"""Rule100 replay adapter for research-runner target weights.

This module translates existing Strategy Replay daily portfolio rows into the
canonical runner's risky-asset target-weight matrix. Cash remains implicit and
Rule100 remains diagnostic-only by default.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_STRATEGY_ROLE = "diagnostic_lifecycle_policy"
DEFAULT_PROMOTION_STATUS = "diagnostic_only"
DAILY_PORTFOLIO_ROLE = "daily_portfolio"
CASH_ASSET_LABEL = "CASH"
IGNORED_REPLAY_PERFORMANCE_COLUMNS = (
    "portfolio_equity",
    "portfolio_return",
    "asset_return",
    "weight_for_return",
    "return_contribution",
)


@dataclass(frozen=True)
class Rule100ReplayAdapterResult:
    """Runner-ready risky weights plus diagnostic replay metadata."""

    target_weights: pd.DataFrame
    cash_residual: pd.Series
    metadata: dict[str, Any]

    @property
    def promotion_status(self) -> str:
        return str(self.metadata.get("promotion_status", DEFAULT_PROMOTION_STATUS))

    @property
    def strategy_role(self) -> str:
        return str(self.metadata.get("strategy_role", DEFAULT_STRATEGY_ROLE))

    @property
    def diagnostic_only(self) -> bool:
        return self.promotion_status == DEFAULT_PROMOTION_STATUS


def rule100_replay_to_target_weights(
    replay_or_bundle: Any,
    *,
    asset_column: str = "permno",
    duplicate_tolerance: float = 1e-12,
) -> pd.DataFrame:
    """Return only the runner target-weight matrix for a Rule100 replay."""

    return adapt_rule100_replay_to_target_weights(
        replay_or_bundle,
        asset_column=asset_column,
        duplicate_tolerance=duplicate_tolerance,
    ).target_weights


def adapt_rule100_replay_to_target_weights(
    replay_or_bundle: Any,
    *,
    asset_column: str = "permno",
    duplicate_tolerance: float = 1e-12,
) -> Rule100ReplayAdapterResult:
    """Pivot Rule100 daily replay rows into risky-asset target weights.

    Accepted inputs are raw replay frames, bundle-like objects exposing
    ``.replay`` / ``.frame`` / ``.daily_portfolio``, or selected-result-like
    objects exposing ``.bundle``. The adapter intentionally ignores replay
    performance/equity columns; canonical PnL must come from the runner.
    """

    replay, source_metadata = _extract_replay_frame_and_metadata(replay_or_bundle)
    if replay.empty:
        raise ValueError("Rule100 replay adapter received an empty replay frame.")

    required = {"date", "target_weight"}
    missing = sorted(required - set(replay.columns))
    if missing:
        raise ValueError(f"Rule100 replay frame missing required column(s): {missing}")

    resolved_asset_column = _resolve_asset_column(replay, asset_column)
    working = replay.copy()
    working["_date"] = _coerce_daily_dates(working["date"])

    daily, role_filter = _filter_daily_portfolio_rows(working)
    if daily.empty:
        raise ValueError("Rule100 replay frame contains no daily_portfolio rows.")

    daily["_target_weight"] = pd.to_numeric(daily["target_weight"], errors="coerce")
    if daily["_target_weight"].isna().any() or not np.isfinite(daily["_target_weight"].to_numpy(dtype=float)).all():
        raise ValueError("Rule100 daily replay target_weight values must be finite numeric values.")
    if (daily["_target_weight"] < -duplicate_tolerance).any():
        raise ValueError("Rule100 daily replay target_weight values must be non-negative for long-only v0.")

    cash_mask = _cash_row_mask(daily, resolved_asset_column)
    risky = daily.loc[~cash_mask].copy()

    if not risky.empty:
        risky["_asset"] = _asset_ids(risky[resolved_asset_column], resolved_asset_column)
        if risky["_asset"].isna().any() or risky["_asset"].astype(str).str.strip().eq("").any():
            raise ValueError(f"Rule100 daily replay contains missing {resolved_asset_column} asset identifiers.")

    duplicate_notes: list[str] = []
    if not risky.empty:
        risky, duplicate_notes = _collapse_exact_duplicate_targets(
            risky,
            duplicate_tolerance=duplicate_tolerance,
        )

    target_weights = _pivot_target_weights(risky, daily["_date"], resolved_asset_column)
    row_sums = target_weights.sum(axis=1) if not target_weights.empty else pd.Series(0.0, index=target_weights.index)
    if (row_sums > 1.0 + duplicate_tolerance).any():
        offenders = [idx.date().isoformat() for idx in row_sums[row_sums > 1.0 + duplicate_tolerance].index[:5]]
        raise ValueError(f"Rule100 target weights exceed long-only gross exposure of 1.0 on date(s): {offenders}")

    cash_residual, cash_residual_source = _cash_residual_by_date(
        daily=daily,
        target_weights=target_weights,
    )

    ignored_columns = [col for col in IGNORED_REPLAY_PERFORMANCE_COLUMNS if col in replay.columns]
    metadata = {
        **source_metadata,
        "adapter": "rule100_replay_adapter",
        "strategy_role": DEFAULT_STRATEGY_ROLE,
        "promotion_status": DEFAULT_PROMOTION_STATUS,
        "diagnostic_only": True,
        "no_strategy_promotion": True,
        "role_filter": role_filter,
        "asset_column": resolved_asset_column,
        "target_weight_shape": tuple(target_weights.shape),
        "target_weight_dates": [idx.date().isoformat() for idx in target_weights.index],
        "target_weight_assets": [str(col) for col in target_weights.columns],
        "source_row_count": int(len(replay)),
        "daily_portfolio_row_count": int(len(daily)),
        "excluded_cash_row_count": int(cash_mask.sum()),
        "risky_row_count": int(len(risky)),
        "cash_residual_source": cash_residual_source,
        "cash_residual_by_date": {
            idx.date().isoformat(): float(value)
            for idx, value in cash_residual.items()
            if pd.notna(value) and np.isfinite(float(value))
        },
        "ignored_replay_performance_columns": ignored_columns,
        "duplicate_handling": duplicate_notes,
        "engine_cash_policy": "implicit_residual_cash_no_cash_column",
    }
    if "method" in daily.columns:
        metadata["method_values"] = _sorted_non_empty_strings(daily["method"])
    if "source" in daily.columns:
        metadata["source_values"] = _sorted_non_empty_strings(daily["source"])
    if target_weights.index.size:
        metadata["target_weight_date_window"] = {
            "start": target_weights.index.min().date().isoformat(),
            "end": target_weights.index.max().date().isoformat(),
        }

    return Rule100ReplayAdapterResult(
        target_weights=target_weights,
        cash_residual=cash_residual,
        metadata=metadata,
    )


def _extract_replay_frame_and_metadata(value: Any) -> tuple[pd.DataFrame, dict[str, Any]]:
    metadata: dict[str, Any] = {"source_object_type": type(value).__name__}

    bundle = getattr(value, "bundle", None)
    if bundle is not None:
        metadata.update(_selected_result_metadata(value))
        frame, bundle_metadata = _extract_replay_frame_and_metadata(bundle)
        metadata.update(bundle_metadata)
        metadata["source_object_type"] = f"{type(value).__name__}->{type(bundle).__name__}"
        return frame, metadata

    if isinstance(value, pd.DataFrame):
        metadata.update(_frame_identity_metadata(value))
        return value.copy(), metadata

    for attr in ("replay", "daily_portfolio", "frame"):
        frame = getattr(value, attr, None)
        if isinstance(frame, pd.DataFrame):
            metadata.update(_bundle_identity_metadata(value))
            metadata["source_frame_attr"] = attr
            return frame.copy(), metadata

    raise TypeError(
        "Rule100 replay adapter expects a pandas DataFrame or a replay bundle/result exposing "
        ".replay, .daily_portfolio, .frame, or .bundle."
    )


def _selected_result_metadata(value: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for attr in ("status", "reason", "available", "elapsed_ms"):
        if hasattr(value, attr):
            out[f"selected_result_{attr}"] = _jsonable(getattr(value, attr))
    for attr in ("artifact_path", "manifest_path"):
        raw = getattr(value, attr, None)
        if raw is not None:
            out[attr] = str(Path(raw))
    manifest = getattr(value, "manifest", None)
    if isinstance(manifest, dict):
        for key in ("run_id", "source_id", "method_id", "artifact_type"):
            if key in manifest:
                out[f"manifest_{key}"] = _jsonable(manifest[key])
    return out


def _bundle_identity_metadata(value: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    run_metadata = getattr(value, "run_metadata", None)
    for attr in ("run_id", "source_id", "method_id"):
        if hasattr(value, attr):
            out[attr] = _jsonable(getattr(value, attr))
        elif run_metadata is not None and hasattr(run_metadata, attr):
            out[attr] = _jsonable(getattr(run_metadata, attr))

    if run_metadata is not None:
        for attr in (
            "input_signatures",
            "date_window",
            "row_counts",
            "status_counts",
            "timing",
            "controls_signature",
            "input_coverage_start",
            "effective_start",
            "coverage_warnings",
        ):
            if hasattr(run_metadata, attr):
                out[attr] = _jsonable(getattr(run_metadata, attr))
    return out


def _frame_identity_metadata(frame: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for column in ("run_id", "source_id", "method_id", "artifact_scope"):
        if column in frame.columns:
            values = _sorted_non_empty_strings(frame[column])
            if len(values) == 1:
                out[column] = values[0]
            elif values:
                out[f"{column}s"] = values
    return out


def _resolve_asset_column(frame: pd.DataFrame, requested: str) -> str:
    if requested in frame.columns:
        return requested
    for fallback in ("asset", "ticker"):
        if fallback in frame.columns:
            return fallback
    raise ValueError(
        f"Rule100 replay frame missing asset column {requested!r}; no fallback 'asset' or 'ticker' column found."
    )


def _coerce_daily_dates(values: pd.Series) -> pd.Series:
    dates = pd.to_datetime(values, errors="coerce")
    if dates.isna().any():
        raise ValueError("Rule100 replay date values must be date-like and non-null.")
    try:
        dates = dates.dt.tz_localize(None)
    except (AttributeError, TypeError):
        pass
    return dates.dt.normalize()


def _filter_daily_portfolio_rows(frame: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    for column in ("row_role", "row_type"):
        if column in frame.columns:
            values = frame[column].astype(str).str.strip()
            mask = values.eq(DAILY_PORTFOLIO_ROLE)
            if mask.any():
                return frame.loc[mask].copy(), f"{column}=daily_portfolio"
    return frame.copy(), "assumed_all_rows_daily_portfolio"


def _cash_row_mask(frame: pd.DataFrame, asset_column: str) -> pd.Series:
    mask = pd.Series(False, index=frame.index)
    for column in dict.fromkeys(("ticker", "permno", asset_column)):
        if column in frame.columns:
            mask = mask | frame[column].astype(str).str.strip().str.upper().eq(CASH_ASSET_LABEL)
    return mask


def _asset_ids(values: pd.Series, asset_column: str) -> pd.Series:
    if asset_column == "permno" and pd.api.types.is_numeric_dtype(values):
        numeric = pd.to_numeric(values, errors="coerce")
        if numeric.notna().all() and np.allclose(numeric.to_numpy(dtype=float), np.round(numeric.to_numpy(dtype=float))):
            return numeric.astype("int64")
    return values


def _collapse_exact_duplicate_targets(
    risky: pd.DataFrame,
    *,
    duplicate_tolerance: float,
) -> tuple[pd.DataFrame, list[str]]:
    duplicates = risky.duplicated(["_date", "_asset"], keep=False)
    if not duplicates.any():
        return risky, []

    conflicts: list[str] = []
    for (date_value, asset), group in risky.loc[duplicates].groupby(["_date", "_asset"], sort=False):
        weights = group["_target_weight"].to_numpy(dtype=float)
        if not np.allclose(weights, weights[-1], rtol=0.0, atol=duplicate_tolerance):
            date_label = pd.Timestamp(date_value).date().isoformat()
            conflicts.append(f"{date_label}:{asset}")
    if conflicts:
        raise ValueError(f"Rule100 replay has conflicting duplicate date/asset rows: {conflicts[:5]}")

    collapsed = risky.drop_duplicates(["_date", "_asset"], keep="last")
    return collapsed, ["exact_duplicate_date_asset_rows_collapsed_last_value"]


def _pivot_target_weights(
    risky: pd.DataFrame,
    all_dates: pd.Series,
    asset_column: str,
) -> pd.DataFrame:
    dates = pd.DatetimeIndex(sorted(pd.unique(all_dates)), name="date")
    if risky.empty:
        return pd.DataFrame(index=dates)

    target = (
        risky.pivot(index="_date", columns="_asset", values="_target_weight")
        .reindex(index=dates)
        .fillna(0.0)
        .sort_index()
        .astype(float)
    )
    target.index.name = "date"
    target.columns.name = asset_column
    return target


def _cash_residual_by_date(
    *,
    daily: pd.DataFrame,
    target_weights: pd.DataFrame,
) -> tuple[pd.Series, str]:
    computed = 1.0 - target_weights.sum(axis=1)
    computed = computed.astype(float)
    computed.name = "cash_residual"

    if "cash_residual" not in daily.columns:
        return computed, "computed_from_risky_weight_sum"

    values = daily[["_date", "cash_residual"]].copy()
    values["cash_residual"] = pd.to_numeric(values["cash_residual"], errors="coerce")
    replay_residual = values.groupby("_date")["cash_residual"].agg(_last_valid).reindex(target_weights.index)
    replay_residual = replay_residual.astype(float)
    replay_residual.name = "cash_residual"
    if replay_residual.isna().any():
        replay_residual = replay_residual.fillna(computed)
        return replay_residual, "replay_cash_residual_with_computed_missing_dates"
    return replay_residual, "replay_cash_residual"


def _last_valid(values: pd.Series) -> float:
    clean = values.dropna()
    if clean.empty:
        return float("nan")
    return float(clean.iloc[-1])


def _sorted_non_empty_strings(values: pd.Series) -> list[str]:
    clean = values.dropna().astype(str).str.strip()
    return sorted(value for value in clean.unique().tolist() if value)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            return value
    return value
