"""Strict Rule100 replay adapter for the AOV research spine.

AOV has no ticker/asset compatibility aliases. Risky rows require permanent
`permno` identity, explicit `daily_portfolio` row role, and explicit context
role. Cash is recognized only through `context_role == "cash"` and remains
implicit in the canonical engine.
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
CASH_CONTEXT_ROLE = "cash"
IGNORED_REPLAY_PERFORMANCE_COLUMNS = (
    "portfolio_equity",
    "portfolio_return",
    "asset_return",
    "weight_for_return",
    "return_contribution",
)


@dataclass(frozen=True)
class Rule100ReplayAdapterResult:
    target_weights: pd.DataFrame
    cash_residual: pd.Series
    metadata: dict[str, Any]

    @property
    def promotion_status(self) -> str:
        return str(self.metadata["promotion_status"])

    @property
    def strategy_role(self) -> str:
        return str(self.metadata["strategy_role"])

    @property
    def diagnostic_only(self) -> bool:
        return self.promotion_status == DEFAULT_PROMOTION_STATUS


def rule100_replay_to_target_weights(
    replay_or_bundle: Any,
    *,
    duplicate_tolerance: float = 1e-12,
) -> pd.DataFrame:
    return adapt_rule100_replay_to_target_weights(
        replay_or_bundle,
        duplicate_tolerance=duplicate_tolerance,
    ).target_weights


def adapt_rule100_replay_to_target_weights(
    replay_or_bundle: Any,
    *,
    duplicate_tolerance: float = 1e-12,
) -> Rule100ReplayAdapterResult:
    replay, source_metadata = _extract_replay_frame_and_metadata(replay_or_bundle)
    if replay.empty:
        raise ValueError("rule100_replay_empty")

    required = {"date", "target_weight", "row_role", "context_role", "permno"}
    missing = sorted(required - set(replay.columns))
    if missing:
        raise ValueError(f"rule100_replay_missing_required_columns:{','.join(missing)}")

    working = replay.copy()
    working["_date"] = _coerce_daily_dates(working["date"])
    roles = working["row_role"].astype(str).str.strip()
    daily = working.loc[roles.eq(DAILY_PORTFOLIO_ROLE)].copy()
    if daily.empty:
        raise ValueError("rule100_replay_no_daily_portfolio_rows")

    daily["_target_weight"] = pd.to_numeric(daily["target_weight"], errors="coerce")
    if daily["_target_weight"].isna().any() or not np.isfinite(daily["_target_weight"].to_numpy(dtype=float)).all():
        raise ValueError("rule100_target_weights_non_finite")
    if (daily["_target_weight"] < -duplicate_tolerance).any():
        raise ValueError("rule100_target_weights_negative")

    context_roles = daily["context_role"].astype(str).str.strip().str.lower()
    cash_mask = context_roles.eq(CASH_CONTEXT_ROLE)
    risky = daily.loc[~cash_mask].copy()
    if not risky.empty:
        numeric_permno = pd.to_numeric(risky["permno"], errors="coerce")
        if numeric_permno.isna().any() or not np.isfinite(numeric_permno.to_numpy(dtype=float)).all():
            raise ValueError("rule100_permanent_id_required")
        if not np.allclose(numeric_permno.to_numpy(dtype=float), np.round(numeric_permno.to_numpy(dtype=float))):
            raise ValueError("rule100_permno_must_be_integer")
        risky["_asset"] = numeric_permno.astype("int64")
        if risky.duplicated(["_date", "_asset"], keep=False).any():
            raise ValueError("rule100_duplicate_date_permno_rows")

    target_weights = _pivot_target_weights(risky, daily["_date"])
    row_sums = target_weights.sum(axis=1) if not target_weights.empty else pd.Series(0.0, index=target_weights.index)
    if (row_sums > 1.0 + duplicate_tolerance).any():
        raise ValueError("rule100_target_weight_row_sum_gt_one")

    computed_cash = (1.0 - row_sums).astype(float)
    computed_cash.name = "cash_residual"
    cash_source = "computed_from_risky_weight_sum"
    if "cash_residual" in daily.columns:
        reported = _reported_cash_residual(daily, target_weights.index)
        if not np.allclose(
            reported.to_numpy(dtype=float),
            computed_cash.to_numpy(dtype=float),
            rtol=0.0,
            atol=duplicate_tolerance,
        ):
            raise ValueError("rule100_cash_residual_mismatch")
        cash_source = "validated_replay_cash_residual"

    ignored_columns = [column for column in IGNORED_REPLAY_PERFORMANCE_COLUMNS if column in replay.columns]
    metadata = {
        **source_metadata,
        "adapter": "rule100_replay_adapter_strict_v1",
        "strategy_role": DEFAULT_STRATEGY_ROLE,
        "promotion_status": DEFAULT_PROMOTION_STATUS,
        "diagnostic_only": True,
        "no_strategy_promotion": True,
        "identity_contract": "PERMNO_REQUIRED_NO_TICKER_ALIAS",
        "row_role_contract": "daily_portfolio_required",
        "cash_context_contract": "context_role=cash",
        "target_weight_shape": tuple(target_weights.shape),
        "target_weight_assets": [int(column) for column in target_weights.columns],
        "source_row_count": int(len(replay)),
        "daily_portfolio_row_count": int(len(daily)),
        "excluded_cash_row_count": int(cash_mask.sum()),
        "risky_row_count": int(len(risky)),
        "cash_residual_source": cash_source,
        "cash_residual_by_date": {
            index.date().isoformat(): float(value)
            for index, value in computed_cash.items()
        },
        "ignored_replay_performance_columns": ignored_columns,
        "engine_cash_policy": "implicit_residual_cash_no_cash_column",
    }
    return Rule100ReplayAdapterResult(
        target_weights=target_weights,
        cash_residual=computed_cash,
        metadata=metadata,
    )


def _extract_replay_frame_and_metadata(value: Any) -> tuple[pd.DataFrame, dict[str, Any]]:
    metadata: dict[str, Any] = {"source_object_type": type(value).__name__}
    bundle = getattr(value, "bundle", None)
    if bundle is not None:
        frame, nested = _extract_replay_frame_and_metadata(bundle)
        metadata.update(nested)
        metadata["source_object_type"] = f"{type(value).__name__}->{type(bundle).__name__}"
        manifest = getattr(value, "manifest", None)
        if isinstance(manifest, dict):
            for key in ("run_id", "source_id", "method_id", "artifact_type"):
                if key in manifest:
                    metadata[f"manifest_{key}"] = _jsonable(manifest[key])
        for attr in ("artifact_path", "manifest_path"):
            raw = getattr(value, attr, None)
            if raw is not None:
                metadata[attr] = str(Path(raw))
        return frame, metadata
    if isinstance(value, pd.DataFrame):
        return value.copy(), metadata
    frame = getattr(value, "replay", None)
    if isinstance(frame, pd.DataFrame):
        run_metadata = getattr(value, "run_metadata", None)
        if run_metadata is not None:
            for attr in ("run_id", "source_id", "method_id", "input_signatures"):
                if hasattr(run_metadata, attr):
                    metadata[attr] = _jsonable(getattr(run_metadata, attr))
        return frame.copy(), metadata
    raise TypeError("rule100_replay_requires_dataframe_or_bundle_replay")


def _coerce_daily_dates(values: pd.Series) -> pd.Series:
    dates = pd.to_datetime(values, errors="coerce")
    if dates.isna().any():
        raise ValueError("rule100_replay_dates_invalid")
    try:
        dates = dates.dt.tz_localize(None)
    except (AttributeError, TypeError):
        pass
    return dates.dt.normalize()


def _pivot_target_weights(risky: pd.DataFrame, all_dates: pd.Series) -> pd.DataFrame:
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
    target.columns.name = "permno"
    return target


def _reported_cash_residual(daily: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.Series:
    values = daily[["_date", "cash_residual"]].copy()
    values["cash_residual"] = pd.to_numeric(values["cash_residual"], errors="coerce")
    if values["cash_residual"].isna().any() or not np.isfinite(values["cash_residual"].to_numpy(dtype=float)).all():
        raise ValueError("rule100_cash_residual_non_finite")
    grouped = values.groupby("_date")["cash_residual"]
    if grouped.nunique(dropna=False).gt(1).any():
        raise ValueError("rule100_cash_residual_inconsistent_within_date")
    return grouped.first().reindex(dates).astype(float)


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
            pass
    return value
