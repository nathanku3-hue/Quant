"""Method-aware PIT strategy allocation replay helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Callable

import numpy as np
import pandas as pd

from core.data_orchestrator import StrategyReplayInputs
from strategies.optimizer import OPTIMIZATION_METHOD_OPTIONS, OptimizationMethod, PortfolioOptimizer
from strategies.rule100_softmax import rule100_config_from_max_weight, softmax_v1_weights


DEFAULT_REPLAY_MAX_WEIGHT = 0.35
REPLAY_SOURCE = "strategy_replay"
RULE100_REPLAY_SOURCE = "rule100_softmax_v1_replay"
CAP_SOURCE_CONTROLS = "controls.max_weight"
REPLAY_COLUMNS = [
    "date",
    "method",
    "ticker",
    "permno",
    "target_weight",
    "cash_residual",
    "asset_return",
    "weight_for_return",
    "return_contribution",
    "portfolio_return",
    "portfolio_equity",
    "cap_used",
    "cap_source",
    "source",
    "row_role",
    "context_role",
    "status",
    "reason",
]
REPLAY_CONTEXT_COLUMNS = [
    "date",
    "method",
    "ticker",
    "context_type",
    "row_role",
    "context_role",
    "action",
    "buy_sell",
    "target_weight",
    "weight",
    "reason",
    "source",
    "status",
]
SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS = [
    "row_type",
    "row_role",
    "run_id",
    "source_id",
    "date",
    "method",
    "ticker",
    "permno",
    "target_weight",
    "cash_residual",
    "asset_return",
    "weight_for_return",
    "return_contribution",
    "portfolio_return",
    "portfolio_equity",
    "cap_used",
    "cap_source",
    "context_type",
    "action",
    "buy_sell",
    "weight",
    "reason",
    "source",
    "context_role",
    "status",
    "artifact_scope",
]
ROLE_COLUMNS = ("context_role", "row_role")
LEGACY_SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS = [
    col for col in SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS if col not in ROLE_COLUMNS
]
SELECTED_METHOD_REPLAY_ARTIFACT_TYPE = "selected_method_replay_output"
SELECTED_METHOD_REPLAY_CACHE_DIR = Path("data/runtime_cache/strategy_replay")


@dataclass(frozen=True)
class StrategyReplayContext:
    """Typed PIT-safe event or decision context attached to replay output."""

    context_type: str
    frame: pd.DataFrame
    status: str
    reason: str
    source: str


@dataclass(frozen=True)
class StrategyReplayRunMetadata:
    """Run-level evidence for one selected-method replay source."""

    run_id: str
    method_id: str
    source_id: str
    input_signatures: tuple[dict[str, Any], ...]
    date_window: dict[str, str | None]
    row_counts: dict[str, int]
    status_counts: dict[str, dict[str, int]]
    timing: dict[str, Any]
    controls_signature: dict[str, Any] = field(default_factory=dict)
    input_coverage_start: str | None = None
    effective_start: str | None = None
    coverage_warnings: tuple[str, ...] = ()


def _empty_run_metadata() -> StrategyReplayRunMetadata:
    return StrategyReplayRunMetadata(
        run_id="uninitialized",
        method_id="",
        source_id="selected_method_replay:uninitialized",
        input_signatures=(),
        date_window={
            "requested_start": None,
            "requested_end": None,
            "replay_start": None,
            "replay_end": None,
        },
        row_counts={
            "daily_portfolio": 0,
            "event_annotations": 0,
            "buy_sell_decisions": 0,
            "total": 0,
        },
        status_counts={
            "daily_portfolio": {},
            "event_annotations": {},
            "buy_sell_decisions": {},
        },
        timing={
            "started_at_utc": None,
            "completed_at_utc": None,
            "elapsed_ms": 0.0,
        },
        controls_signature={},
    )


@dataclass(frozen=True)
class StrategyReplayBundle:
    """Selected-method replay bundle with one shared target-weight source."""

    replay: pd.DataFrame
    event_context: StrategyReplayContext
    decision_context: StrategyReplayContext
    run_metadata: StrategyReplayRunMetadata = field(default_factory=_empty_run_metadata)

    @property
    def frame(self) -> pd.DataFrame:
        return self.replay

    @property
    def daily_portfolio(self) -> pd.DataFrame:
        return self.replay

    @property
    def event_rows(self) -> pd.DataFrame:
        return self.event_context.frame

    @property
    def decision_rows(self) -> pd.DataFrame:
        return self.decision_context.frame

    @property
    def run_id(self) -> str:
        return self.run_metadata.run_id

    @property
    def input_signatures(self) -> tuple[dict[str, Any], ...]:
        return self.run_metadata.input_signatures

    @property
    def date_window(self) -> dict[str, str | None]:
        return self.run_metadata.date_window

    @property
    def status_counts(self) -> dict[str, dict[str, int]]:
        return self.run_metadata.status_counts

    @property
    def timing(self) -> dict[str, Any]:
        return self.run_metadata.timing


@dataclass(frozen=True)
class ReplayBudgetPolicy:
    """Explicit replay performance budget for cold builds and cache reads."""

    cold_start_max_seconds: float = 30.0
    rerun_cache_max_seconds: float = 2.0
    max_rows: int = 500_000
    max_dates: int = 2_000
    max_elapsed_ms: float = 300_000.0


@dataclass(frozen=True)
class SelectedMethodReplayResult:
    """Typed outcome for saved selected-method replay artifact reads/builds."""

    status: str
    reason: str
    bundle: StrategyReplayBundle | None = None
    manifest: dict[str, Any] = field(default_factory=dict)
    artifact_path: Path | None = None
    manifest_path: Path | None = None
    elapsed_ms: float = 0.0
    budget_policy: ReplayBudgetPolicy = field(default_factory=ReplayBudgetPolicy)

    @property
    def available(self) -> bool:
        return self.status == "ok" and self.bundle is not None

    @property
    def replay(self) -> pd.DataFrame:
        if self.bundle is None:
            return pd.DataFrame(columns=REPLAY_COLUMNS)
        return self.bundle.replay


@dataclass(frozen=True)
class ReplayDateCoverage:
    """Per-date coverage classification from linear scan."""

    date: pd.Timestamp
    covered: bool
    reason: str
    membership_date: str | None
    priced_member_count: int
    expected_members: list[int]


def _rule100_candidate_coverage(controls: Any) -> pd.Timestamp | None:
    """Return earliest candidate observation date from controls, or None."""
    raw = _rule100_candidates_from_controls_raw(controls)
    if not isinstance(raw, pd.DataFrame) or raw.empty:
        return None
    if "date" not in raw.columns:
        return None
    dates = pd.to_datetime(raw["date"], errors="coerce").dropna()
    if dates.empty:
        return None
    return pd.Timestamp(dates.min()).normalize()


def _rule100_candidates_from_controls_raw(controls: Any) -> pd.DataFrame:
    """Extract rule100 candidate frame from controls without copy."""
    for name in ("rule100_candidate_frame", "rule100_candidates", "candidate_frame"):
        value = _control_value_raw(controls, name, None)
        if isinstance(value, pd.DataFrame):
            return value
    return pd.DataFrame()


def _control_value_raw(controls: Any, name: str, default: Any) -> Any:
    """Same as _control_value but avoids circular dependency at module load."""
    if controls is None:
        return default
    if isinstance(controls, dict):
        return controls.get(name, default)
    return getattr(controls, name, default)


def _compute_coverage_plan(
    method: "OptimizationMethod",
    controls: Any,
    replay_dates: list[pd.Timestamp],
    *,
    batched: Any = None,
    max_membership_gap_days: int = 30,
) -> list[ReplayDateCoverage]:
    """Linear scan: classify each replay date as covered or uncovered with reason."""
    from core.data_orchestrator import BatchedPITReplayData, pit_members_for_date

    # Rule100 candidate coverage boundary
    candidate_start: pd.Timestamp | None = None
    if method == OptimizationMethod.RULE_OF_100:
        candidate_start = _rule100_candidate_coverage(controls)

    # Precompute first valid price date per column to avoid O(n²) slicing
    first_valid: dict[Any, pd.Timestamp] = {}
    if isinstance(batched, BatchedPITReplayData) and not batched.raw_prices.empty:
        for col in batched.raw_prices.columns:
            valid_idx = batched.raw_prices.index[batched.raw_prices[col].notna()]
            if len(valid_idx):
                first_valid[col] = pd.Timestamp(valid_idx[0]).normalize()

    plan: list[ReplayDateCoverage] = []
    for date_value in replay_dates:
        # If no batched data, assume covered (non-batched path)
        if not isinstance(batched, BatchedPITReplayData):
            plan.append(ReplayDateCoverage(
                date=date_value, covered=True, reason="ok",
                membership_date=None, priced_member_count=0, expected_members=[],
            ))
            continue

        members = pit_members_for_date(batched, date_value, max_gap_days=max_membership_gap_days)
        if members is None:
            plan.append(ReplayDateCoverage(
                date=date_value, covered=False, reason="membership_gap_exceeded",
                membership_date=None, priced_member_count=0, expected_members=[],
            ))
            continue

        # Find membership date used
        import bisect
        date_iso = date_value.normalize().date().isoformat()
        idx = bisect.bisect_right(batched.membership_dates, date_iso) - 1
        mem_date = batched.membership_dates[idx] if idx >= 0 else None

        # Check priced members using precomputed first_valid (O(1) per column)
        valid_cols = [p for p in members if p in batched.raw_prices.columns]
        priced_members = [c for c in valid_cols if first_valid.get(c, pd.Timestamp.max) <= date_value]

        if not priced_members:
            plan.append(ReplayDateCoverage(
                date=date_value, covered=False, reason="no_priced_members",
                membership_date=mem_date, priced_member_count=0,
                expected_members=sorted(members),
            ))
            continue

        # Rule100: check candidate coverage
        if candidate_start is not None and date_value < candidate_start:
            plan.append(ReplayDateCoverage(
                date=date_value, covered=False, reason="candidate_coverage_not_started",
                membership_date=mem_date, priced_member_count=len(priced_members),
                expected_members=sorted(members),
            ))
            continue

        plan.append(ReplayDateCoverage(
            date=date_value, covered=True, reason="ok",
            membership_date=mem_date, priced_member_count=len(priced_members),
            expected_members=sorted(members),
        ))

    return plan


def _control_value(controls: Any, name: str, default: Any) -> Any:
    if controls is None:
        return default
    if isinstance(controls, dict):
        return controls.get(name, default)
    return getattr(controls, name, default)


def _finite_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except Exception:
        return float(default)
    if not np.isfinite(parsed):
        return float(default)
    return parsed


def _control_max_weight(controls: Any) -> float:
    value = _finite_float(_control_value(controls, "max_weight", DEFAULT_REPLAY_MAX_WEIGHT), DEFAULT_REPLAY_MAX_WEIGHT)
    if value <= 0.0 or value > 1.0:
        return DEFAULT_REPLAY_MAX_WEIGHT
    return float(value)


def _control_risk_free_rate(controls: Any) -> float:
    return _finite_float(_control_value(controls, "risk_free_rate", 0.0), 0.0)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _metadata_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _metadata_json_safe(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_metadata_json_safe(item) for item in value]
    if isinstance(value, pd.DataFrame):
        frame = value.copy()
        normalized = pd.DataFrame(index=frame.index)
        for col in sorted(frame.columns, key=lambda item: str(item)):
            series = frame[col]
            if pd.api.types.is_datetime64_any_dtype(series):
                normalized[str(col)] = pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S.%f")
            else:
                normalized[str(col)] = series.astype("object").where(pd.notna(series), None).map(
                    lambda item: _metadata_json_safe(item)
                )
        normalized = normalized.sort_index(axis=0, kind="mergesort").reset_index(drop=True)
        row_payload = normalized.to_dict("records")
        dates = pd.to_datetime(value["date"], errors="coerce") if "date" in value.columns else pd.Series(dtype="datetime64[ns]")
        return {
            "type": "DataFrame",
            "rows": int(len(value)),
            "columns": [str(col) for col in value.columns],
            "date_min": None if dates.empty or dates.isna().all() else str(dates.min().date()),
            "date_max": None if dates.empty or dates.isna().all() else str(dates.max().date()),
            "content_hash": _json_fingerprint(row_payload, length=24),
        }
    if isinstance(value, pd.Index):
        return [str(item) for item in value.tolist()]
    if isinstance(value, (pd.Timestamp,)):
        return pd.Timestamp(value).date().isoformat()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        parsed = float(value)
        if not np.isfinite(parsed):
            return str(parsed)
        return parsed
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not np.isfinite(value):
        return str(value)
    return value


def _json_fingerprint(payload: Any, *, length: int = 16) -> str:
    text = json.dumps(_metadata_json_safe(payload), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def _canonical_metadata(value: Any) -> Any:
    return json.loads(json.dumps(_metadata_json_safe(value), sort_keys=True, separators=(",", ":"), allow_nan=False))


def _controls_signature_payload(controls: Any) -> dict[str, Any]:
    if isinstance(controls, dict):
        return {
            str(key): _metadata_json_safe(value)
            for key, value in sorted(controls.items(), key=lambda item: str(item[0]))
            if not callable(value)
        }
    payload: dict[str, Any] = {}
    for name in ("max_weight", "risk_free_rate", "rebalance", "timeframe"):
        value = getattr(controls, name, None)
        if value is not None:
            payload[name] = _metadata_json_safe(value)
    return payload


def _iso_or_none(value: Any) -> str | None:
    if value is None:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return pd.Timestamp(ts).normalize().date().isoformat()


def _status_counts(frame: pd.DataFrame, *, empty_status: str = "empty") -> dict[str, int]:
    if not isinstance(frame, pd.DataFrame) or frame.empty or "status" not in frame.columns:
        return {empty_status: 0}
    counts = frame["status"].fillna("unknown").astype(str).value_counts(dropna=False).sort_index()
    return {str(status): int(count) for status, count in counts.items()}


def _replay_context_roles(frame: pd.DataFrame) -> pd.Series:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.Series(dtype=object)
    index = frame.index
    ticker = (
        frame["ticker"].astype(str).str.upper().str.strip()
        if "ticker" in frame.columns
        else pd.Series("", index=index, dtype=object)
    )
    status = (
        frame["status"].astype(str).str.lower().str.strip()
        if "status" in frame.columns
        else pd.Series("", index=index, dtype=object)
    )
    target = (
        pd.to_numeric(frame["target_weight"], errors="coerce").fillna(0.0).clip(lower=0.0)
        if "target_weight" in frame.columns
        else pd.Series(0.0, index=index, dtype="float64")
    )
    role = pd.Series("flat_in_replay", index=index, dtype=object)
    role.loc[target > 0.0] = "current_holding"
    role.loc[ticker == "CASH"] = "cash"
    role.loc[status == "context_only"] = "historical_context"
    role.loc[status.str.contains("unavailable", na=False)] = "unavailable"
    role.loc[status.str.contains("missing", na=False)] = "unavailable"
    role.loc[status == "cash_closed"] = role.loc[status == "cash_closed"].where(ticker == "CASH", "unavailable")
    return role


def _coerce_replay_roles(frame: pd.DataFrame, *, row_role: str = "daily_portfolio") -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        return pd.DataFrame(columns=REPLAY_COLUMNS)
    out = frame.copy()
    if "row_role" not in out.columns:
        out["row_role"] = row_role
    else:
        out["row_role"] = out["row_role"].where(out["row_role"].notna(), row_role).astype(str)
        out.loc[out["row_role"].str.strip() == "", "row_role"] = row_role
    out["context_role"] = _replay_context_roles(out)
    return out


def _context_role_from_aux_rows(work: pd.DataFrame, replay_weights: pd.DataFrame) -> pd.Series:
    if not isinstance(work, pd.DataFrame) or work.empty:
        return pd.Series(dtype=object)
    target = pd.to_numeric(work.get("replay_target_weight", pd.Series(np.nan, index=work.index)), errors="coerce")
    role = pd.Series("flat_in_replay", index=work.index, dtype=object)
    role.loc[target > 0.0] = "current_holding"
    missing = target.isna()
    if isinstance(replay_weights, pd.DataFrame) and replay_weights.empty:
        missing = pd.Series(True, index=work.index)
    role.loc[missing] = "unavailable"
    return role


def _hydrate_legacy_artifact_roles(artifact: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(artifact, pd.DataFrame):
        return pd.DataFrame(columns=SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS)
    out = artifact.copy()
    if "row_role" not in out.columns:
        out["row_role"] = out["row_type"] if "row_type" in out.columns else ""
    else:
        fallback = out["row_type"] if "row_type" in out.columns else ""
        out["row_role"] = out["row_role"].where(out["row_role"].notna(), fallback)
    if "context_role" not in out.columns:
        out["context_role"] = ""
    daily_mask = out["row_type"].astype(str).eq("daily_portfolio") if "row_type" in out.columns else pd.Series(False, index=out.index)
    if daily_mask.any():
        out.loc[daily_mask, "context_role"] = _replay_context_roles(out.loc[daily_mask])
    aux_mask = ~daily_mask
    if aux_mask.any():
        aux_target = pd.to_numeric(out.loc[aux_mask].get("target_weight", pd.Series(np.nan, index=out.loc[aux_mask].index)), errors="coerce")
        aux_role = pd.Series("flat_in_replay", index=out.loc[aux_mask].index, dtype=object)
        aux_role.loc[aux_target > 0.0] = "current_holding"
        aux_role.loc[aux_target.isna()] = "unavailable"
        out.loc[aux_mask, "context_role"] = out.loc[aux_mask, "context_role"].where(
            out.loc[aux_mask, "context_role"].astype(str).str.strip() != "",
            aux_role,
        )
    return out.reindex(columns=SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS)


def _date_window_from_replay(
    replay: pd.DataFrame,
    *,
    requested_start: Any = None,
    requested_end: Any = None,
) -> dict[str, str | None]:
    replay_dates = pd.to_datetime(
        replay.get("date", pd.Series(dtype=object)) if isinstance(replay, pd.DataFrame) else pd.Series(dtype=object),
        errors="coerce",
    ).dropna()
    return {
        "requested_start": _iso_or_none(requested_start),
        "requested_end": _iso_or_none(requested_end),
        "replay_start": None if replay_dates.empty else pd.Timestamp(replay_dates.min()).date().isoformat(),
        "replay_end": None if replay_dates.empty else pd.Timestamp(replay_dates.max()).date().isoformat(),
    }


def _price_frame_signature(prices: pd.DataFrame, *, label: str) -> dict[str, Any]:
    frame = _as_price_frame(prices)
    return {
        "type": label,
        "rows": int(frame.shape[0]),
        "columns": int(frame.shape[1]),
        "date_start": None if frame.empty else pd.Timestamp(frame.index.min()).date().isoformat(),
        "date_end": None if frame.empty else pd.Timestamp(frame.index.max()).date().isoformat(),
        "columns_hash": _json_fingerprint([str(col) for col in frame.columns]),
    }


def _strategy_inputs_signature(inputs: StrategyReplayInputs) -> dict[str, Any]:
    price_frame = inputs.prices
    price_date_start = None
    price_date_end = None
    if isinstance(price_frame, pd.DataFrame) and not price_frame.empty:
        idx = pd.to_datetime(price_frame.index, errors="coerce").dropna()
        if not idx.empty:
            price_date_start = pd.Timestamp(idx.min()).date().isoformat()
            price_date_end = pd.Timestamp(idx.max()).date().isoformat()
    return {
        "type": "StrategyReplayInputs",
        "as_of_date": pd.Timestamp(inputs.as_of_date).date().isoformat(),
        "cache_key": str(inputs.cache_key),
        "cache_signature": _metadata_json_safe(inputs.cache_signature),
        "price_shape": [int(inputs.prices.shape[0]), int(inputs.prices.shape[1])],
        "return_shape": [int(inputs.returns.shape[0]), int(inputs.returns.shape[1])],
        "price_date_start": price_date_start,
        "price_date_end": price_date_end,
        "priced_member_count": int(inputs.prices.shape[1]),
        "membership_date": inputs.metadata.get("membership_date") if isinstance(inputs.metadata, dict) else None,
    }


def _coerce_method(method: OptimizationMethod | str) -> OptimizationMethod:
    if isinstance(method, OptimizationMethod):
        return method
    return OptimizationMethod(method)


def _as_price_frame(prices: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(prices, pd.DataFrame) or prices.empty:
        return pd.DataFrame()
    out = prices.copy()
    out.index = pd.to_datetime(out.index, errors="coerce")
    out = out[out.index.notna()].sort_index(kind="mergesort")
    out = out.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    return out


def _as_return_frame(returns: pd.DataFrame | None, prices: pd.DataFrame) -> pd.DataFrame:
    if isinstance(returns, pd.DataFrame) and not returns.empty:
        out = returns.copy()
        out.index = pd.to_datetime(out.index, errors="coerce")
        out = out[out.index.notna()].sort_index(kind="mergesort")
        out = out.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
        return out
    if prices.empty:
        return pd.DataFrame()
    return prices.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)


def _coerce_as_of_dates(as_of_range: Iterable[Any] | tuple[Any, Any] | None, prices: pd.DataFrame) -> list[pd.Timestamp]:
    if as_of_range is None:
        raw_dates = pd.Index(prices.index)
    elif isinstance(as_of_range, tuple) and len(as_of_range) == 2:
        start = pd.to_datetime(as_of_range[0], errors="coerce")
        end = pd.to_datetime(as_of_range[1], errors="coerce")
        if pd.isna(start) or pd.isna(end):
            return []
        raw_dates = pd.date_range(pd.Timestamp(start), pd.Timestamp(end), freq="D")
    elif isinstance(as_of_range, str):
        raw_dates = pd.Index([as_of_range])
    else:
        try:
            raw_dates = pd.Index(list(as_of_range))
        except TypeError:
            raw_dates = pd.Index([as_of_range])

    dates = pd.to_datetime(raw_dates, errors="coerce")
    dates = pd.DatetimeIndex(dates).dropna().normalize().unique().sort_values()
    return [pd.Timestamp(value) for value in dates]


def _ticker_for_asset(asset: Any, ticker_map: dict | None) -> str:
    mapping = ticker_map or {}
    for key in (asset, str(asset)):
        if key in mapping and pd.notna(mapping[key]):
            return str(mapping[key]).upper().strip()
    return str(asset).upper().strip()


def _asset_lookup(prices: pd.DataFrame, ticker_map: dict | None) -> dict[str, Any]:
    lookup: dict[str, Any] = {}
    for asset in prices.columns:
        lookup[str(asset).upper().strip()] = asset
        ticker = _ticker_for_asset(asset, ticker_map)
        lookup[ticker] = asset
    return lookup


def _lookup_column(frame: pd.DataFrame, key: Any) -> Any | None:
    if key in frame.columns:
        return key
    key_text = str(key)
    for col in frame.columns:
        if str(col) == key_text:
            return col
    return None


def _returns_for_allocation_dates(returns_frame: pd.DataFrame) -> pd.DataFrame:
    """Align realized returns to the allocation date that preceded them."""
    if returns_frame.empty:
        return returns_frame
    aligned = returns_frame.copy()
    aligned.index = pd.to_datetime(aligned.index, errors="coerce").normalize()
    aligned = aligned[aligned.index.notna()].sort_index()
    if aligned.empty:
        return aligned
    aligned = aligned.groupby(level=0, sort=True).last()
    if len(aligned.index) <= 1:
        return aligned.iloc[0:0].copy()
    realized = aligned.iloc[1:].copy()
    realized.index = aligned.index[:-1]
    return realized


def _attach_replay_performance(replay: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    out = replay.copy()
    if out.empty:
        for col in ("asset_return", "weight_for_return", "return_contribution", "portfolio_return", "portfolio_equity"):
            out[col] = pd.Series(dtype=float)
        return _coerce_replay_roles(out).reindex(columns=REPLAY_COLUMNS)

    date_index = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    returns_frame = _as_return_frame(returns, pd.DataFrame())
    if not returns_frame.empty:
        returns_frame.index = pd.to_datetime(returns_frame.index, errors="coerce").normalize()
        returns_frame = returns_frame[returns_frame.index.notna()]
        returns_frame = _returns_for_allocation_dates(returns_frame)

    if returns_frame.empty:
        out["asset_return"] = 0.0
        out["weight_for_return"] = pd.to_numeric(out["target_weight"], errors="coerce").fillna(0.0).clip(lower=0.0)
        out["return_contribution"] = 0.0
        out["portfolio_return"] = 0.0
        out["portfolio_equity"] = 1.0
        return _coerce_replay_roles(out).reindex(columns=REPLAY_COLUMNS)
    elif len(out) <= 512 and returns_frame.size <= 4096:
        return_lookup: dict[tuple[pd.Timestamp, str], float] = {}
        for idx, row in returns_frame.iterrows():
            date_key = pd.Timestamp(idx).normalize()
            for col, raw_value in row.items():
                value = pd.to_numeric(raw_value, errors="coerce")
                value = float(value) if np.isfinite(value) else 0.0
                col_key = str(col)
                return_lookup[(date_key, col_key)] = value
                return_lookup[(date_key, col_key.upper().strip())] = value

        asset_returns: list[float] = []
        for date_value, permno, ticker in zip(date_index, out["permno"], out["ticker"]):
            ticker_key = str(ticker).upper().strip()
            if pd.isna(date_value) or ticker_key == "CASH":
                asset_returns.append(0.0)
                continue
            date_key = pd.Timestamp(date_value).normalize()
            permno_key = (date_key, str(permno))
            ticker_lookup_key = (date_key, ticker_key)
            if permno_key in return_lookup:
                value = return_lookup[permno_key]
            else:
                value = return_lookup.get(ticker_lookup_key, 0.0)
            asset_returns.append(float(value) if np.isfinite(value) else 0.0)
        out["asset_return"] = asset_returns
    else:
        # Vectorized: stack returns to long form, join on (date, col)
        ret_long = (
            returns_frame.stack(future_stack=True)
            .reset_index()
        )
        ret_long.columns = ["_date", "_col", "_ret"]
        ret_long["_date"] = pd.to_datetime(ret_long["_date"], errors="coerce").dt.normalize()
        ret_long["_col_str"] = ret_long["_col"].astype(str)

        work = out.copy()
        work["_date"] = date_index
        work["_permno_str"] = work["permno"].astype(str)
        work["_ticker_str"] = work["ticker"].astype(str).str.upper().str.strip()

        # Join by permno first, then fill misses by ticker
        by_permno_raw = work.merge(
            ret_long[["_date", "_col_str", "_ret"]],
            left_on=["_date", "_permno_str"],
            right_on=["_date", "_col_str"],
            how="left",
        )["_ret"]

        miss_mask = by_permno_raw.isna() & (work["_ticker_str"] != "CASH")
        by_permno = by_permno_raw.fillna(0.0)
        if miss_mask.any():
            by_ticker = work[miss_mask].merge(
                ret_long[["_date", "_col_str", "_ret"]],
                left_on=["_date", "_ticker_str"],
                right_on=["_date", "_col_str"],
                how="left",
            )["_ret"].fillna(0.0)
            by_permno = by_permno.copy()
            by_permno.iloc[miss_mask.to_numpy().nonzero()[0]] = by_ticker.to_numpy()

        cash_mask = work["_ticker_str"] == "CASH"
        by_permno = by_permno.where(~cash_mask, 0.0)
        out["asset_return"] = (
            pd.to_numeric(by_permno, errors="coerce")
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0.0)
            .to_numpy()
        )
    out["weight_for_return"] = pd.to_numeric(out["target_weight"], errors="coerce").fillna(0.0).clip(lower=0.0)
    out["return_contribution"] = out["weight_for_return"] * out["asset_return"]
    daily = (
        out.assign(_date=date_index)
        .groupby("_date", dropna=True, sort=True)["return_contribution"]
        .sum()
    )
    equity = (1.0 + daily.fillna(0.0)).cumprod()
    out["portfolio_return"] = date_index.map(daily).fillna(0.0).to_numpy()
    out["portfolio_equity"] = date_index.map(equity).fillna(1.0).to_numpy()
    return _coerce_replay_roles(out).reindex(columns=REPLAY_COLUMNS)


def _resolve_replay_method(method: OptimizationMethod) -> tuple[OptimizationMethod, str]:
    if method == OptimizationMethod.HISTORICAL_BEST_CAGR:
        return OptimizationMethod.INVERSE_VOLATILITY, "historical_best_cagr_resolved_to_inverse_volatility"
    if method == OptimizationMethod.HISTORICAL_MAX_SHARPE:
        return OptimizationMethod.THESIS_NEUTRAL_MAX_SHARPE, "historical_max_sharpe_resolved_to_thesis_neutral_max_sharpe"
    return method, "method_replayed_directly"


def _source_for_method(method: OptimizationMethod) -> str:
    if method == OptimizationMethod.RULE_OF_100:
        return RULE100_REPLAY_SOURCE
    runtime_method, _reason = _resolve_replay_method(method)
    return f"{REPLAY_SOURCE}:{runtime_method.value}"


def _run_optimizer_for_method(
    *,
    optimizer: PortfolioOptimizer,
    method: OptimizationMethod,
    prices: pd.DataFrame,
    max_weight: float,
    risk_free_rate: float,
):
    runtime_method, _reason = _resolve_replay_method(method)
    if runtime_method == OptimizationMethod.INVERSE_VOLATILITY:
        return optimizer.optimize_inverse_volatility_with_diagnostics(
            prices,
            max_weight=max_weight,
        )
    if runtime_method == OptimizationMethod.MEAN_VARIANCE_MIN_VOLATILITY:
        return optimizer.optimize_mean_variance_with_diagnostics(
            prices,
            objective="min_volatility",
            max_weight=max_weight,
            risk_free_rate=risk_free_rate,
        )
    if runtime_method == OptimizationMethod.MEAN_VARIANCE_MAX_RETURN:
        return optimizer.optimize_mean_variance_with_diagnostics(
            prices,
            objective="max_return",
            max_weight=max_weight,
            risk_free_rate=risk_free_rate,
        )
    return optimizer.optimize_mean_variance_with_diagnostics(
        prices,
        objective="max_sharpe",
        max_weight=max_weight,
        risk_free_rate=risk_free_rate,
    )


def _optimizer_result_reason(result: Any) -> str:
    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is not None:
        if getattr(diagnostics, "fallback_used", False):
            return str(getattr(diagnostics, "fallback_reason", "") or "optimizer_fallback")
        message = str(getattr(diagnostics, "solver_message", "") or "")
        if message:
            return message
        messages = getattr(diagnostics, "messages", None)
        if messages:
            return str(messages[0])
    return "optimizer_failure"


def _usable_optimizer_weights(result: Any, assets: pd.Index, max_weight: float) -> tuple[pd.Series, bool, str]:
    weights = getattr(result, "weights", None)
    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is not None and not bool(getattr(diagnostics, "result_is_optimized", False)):
        return pd.Series(dtype=float), False, _optimizer_result_reason(result)
    if not isinstance(weights, pd.Series) or weights.empty:
        return pd.Series(dtype=float), False, _optimizer_result_reason(result)

    series = (
        pd.to_numeric(weights.reindex(assets), errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .clip(lower=0.0)
        .astype(float)
    )
    total = float(series.sum())
    if not np.isfinite(total) or total <= 0.0:
        return pd.Series(dtype=float), False, "optimizer_returned_zero_or_nonfinite_weight"
    if total > 1.0 + 1e-6:
        return pd.Series(dtype=float), False, "optimizer_returned_overallocated_weight"
    if float(series.max()) > max_weight + 1e-5:
        return pd.Series(dtype=float), False, "optimizer_returned_weight_above_cap"
    return series, True, "optimized"


def _rows_for_date(
    *,
    date_value: pd.Timestamp,
    method: OptimizationMethod,
    assets: pd.Index,
    ticker_map: dict | None,
    weights: pd.Series,
    cap_used: float,
    cap_source: str,
    source: str,
    status: str,
    reason: str,
    row_reasons: dict[Any, str] | None = None,
    row_statuses: dict[Any, str] | None = None,
) -> list[dict[str, Any]]:
    clean = (
        pd.to_numeric(weights.reindex(assets), errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .clip(lower=0.0)
        .astype(float)
    )
    gross = float(clean.sum())
    if not np.isfinite(gross) or gross < 0.0 or gross > 1.0 + 1e-6:
        clean = pd.Series(0.0, index=assets, dtype=float)
        gross = 0.0
        status = "cash_closed"
        reason = "invalid_weight_vector"

    if gross > 1.0 and gross <= 1.0 + 1e-6:
        clean = clean / gross
        gross = 1.0

    cash_residual = max(0.0, float(1.0 - gross))
    if abs(cash_residual) <= 1e-9:
        cash_residual = 0.0

    rows: list[dict[str, Any]] = []
    date_label = pd.Timestamp(date_value).date().isoformat()
    row_reasons = row_reasons or {}
    row_statuses = row_statuses or {}
    for asset in assets:
        ticker = _ticker_for_asset(asset, ticker_map)
        weight = float(clean.get(asset, 0.0))
        asset_status = row_statuses.get(asset, status)
        context_role = "current_holding" if weight > 0.0 else "flat_in_replay"
        if asset_status in {"cash_closed", "input_unavailable"} or str(asset_status).startswith("input_unavailable"):
            context_role = "unavailable"
        rows.append(
            {
                "date": date_label,
                "method": method.value,
                "ticker": ticker,
                "permno": asset,
                "target_weight": weight,
                "cash_residual": cash_residual,
                "cap_used": cap_used,
                "cap_source": cap_source,
                "source": source,
                "row_role": "daily_portfolio",
                "context_role": context_role,
                "status": asset_status,
                "reason": row_reasons.get(asset, reason),
            }
        )

    rows.append(
        {
            "date": date_label,
            "method": method.value,
            "ticker": "CASH",
            "permno": "CASH",
            "target_weight": cash_residual,
            "cash_residual": cash_residual,
            "cap_used": cap_used,
            "cap_source": cap_source,
            "source": source,
            "row_role": "daily_portfolio",
            "context_role": "cash",
            "status": status,
            "reason": reason if status == "cash_closed" else ("cash_residual" if cash_residual > 0.0 else reason),
        }
    )
    return rows


def _cash_closed_rows(
    *,
    date_value: pd.Timestamp,
    method: OptimizationMethod,
    assets: pd.Index,
    ticker_map: dict | None,
    cap_used: float,
    source: str,
    reason: str,
) -> list[dict[str, Any]]:
    return _rows_for_date(
        date_value=date_value,
        method=method,
        assets=assets,
        ticker_map=ticker_map,
        weights=pd.Series(0.0, index=assets, dtype=float),
        cap_used=cap_used,
        cap_source=CAP_SOURCE_CONTROLS,
        source=source,
        status="cash_closed",
        reason=reason,
    )


def _cash_closed_rows_fast(
    *,
    date_value: pd.Timestamp,
    method: OptimizationMethod,
    assets: Iterable[Any],
    ticker_map: dict | None,
    cap_used: float,
    source: str,
    reason: str,
) -> list[dict[str, Any]]:
    """Build cash-closed rows without pandas Series overhead for unavailable batches."""
    mapping = ticker_map or {}
    date_label = pd.Timestamp(date_value).date().isoformat()
    rows: list[dict[str, Any]] = []
    for asset in assets:
        ticker_value = None
        for key in (asset, str(asset)):
            if key in mapping:
                ticker_value = mapping[key]
                break
        if ticker_value is None:
            ticker = str(asset).upper().strip()
        else:
            ticker = str(ticker_value).upper().strip()
        rows.append(
            {
                "date": date_label,
                "method": method.value,
                "ticker": ticker,
                "permno": asset,
                "target_weight": 0.0,
                "cash_residual": 1.0,
                "cap_used": cap_used,
                "cap_source": CAP_SOURCE_CONTROLS,
                "source": source,
                "row_role": "daily_portfolio",
                "context_role": "unavailable",
                "status": "cash_closed",
                "reason": reason,
            }
        )

    rows.append(
        {
            "date": date_label,
            "method": method.value,
            "ticker": "CASH",
            "permno": "CASH",
            "target_weight": 1.0,
            "cash_residual": 1.0,
            "cap_used": cap_used,
            "cap_source": CAP_SOURCE_CONTROLS,
            "source": source,
            "row_role": "daily_portfolio",
            "context_role": "cash",
            "status": "cash_closed",
            "reason": reason,
        }
    )
    return rows


def _rule100_candidates_from_controls(controls: Any) -> pd.DataFrame:
    for name in ("rule100_candidate_frame", "rule100_candidates", "candidate_frame"):
        value = _control_value(controls, name, None)
        if isinstance(value, pd.DataFrame):
            return value.copy()
    return pd.DataFrame()


def _prepare_rule100_candidates(candidates: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(candidates, pd.DataFrame) or candidates.empty:
        return pd.DataFrame()
    out = candidates.copy()
    if "ticker" in out.columns:
        out["ticker"] = out["ticker"].astype(str).str.upper().str.strip()
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
        out = out[out["date"].notna()].copy()
    return out.sort_values([col for col in ("ticker", "permno", "date") if col in out.columns], kind="mergesort")


def _latest_rule100_candidates_for_date(candidates: pd.DataFrame, date_value: pd.Timestamp) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame()
    work = candidates
    if "date" in work.columns:
        work = work[work["date"] <= pd.Timestamp(date_value)].copy()
    if work.empty:
        return pd.DataFrame()
    subset = [col for col in ("ticker", "permno") if col in work.columns]
    if subset and "date" in work.columns:
        return work.sort_values(subset + ["date"], kind="mergesort").drop_duplicates(subset=subset, keep="last")
    return work.copy()


def _build_rule100_weights_for_date(
    *,
    candidates: pd.DataFrame,
    date_value: pd.Timestamp,
    prices: pd.DataFrame,
    ticker_map: dict | None,
    max_weight: float,
) -> tuple[pd.Series, str, str, dict[Any, str], dict[Any, str]]:
    assets = pd.Index(prices.columns)

    # Resolve adapter — fail closed if registry is broken
    from strategies.adapter_registry import get_adapter
    adapter = get_adapter(OptimizationMethod.RULE_OF_100)

    price_slice = prices.loc[prices.index <= pd.Timestamp(date_value), :]
    available_assets = pd.Index([])
    if not price_slice.empty:
        available_assets = pd.Index(price_slice.columns[price_slice.notna().any()])
    available_prices = prices.loc[:, available_assets] if len(available_assets) else prices.iloc[:, 0:0]
    lookup = _asset_lookup(available_prices, ticker_map)
    row_reasons = {
        asset: "no_rule100_candidate_as_of_date" if asset in available_assets else "no_price_available_as_of_date"
        for asset in assets
    }
    row_statuses = {asset: "cash_only" for asset in assets}

    required = {"date", "ticker", "factor_positive_count", "technical_quality"}
    if candidates.empty:
        return (
            pd.Series(0.0, index=assets, dtype=float),
            "cash_only",
            "no_rule100_candidate_frame",
            row_reasons,
            row_statuses,
        )
    if not required.issubset(candidates.columns):
        reason = "rule100_candidate_frame_missing_required_columns"
        return (
            pd.Series(0.0, index=assets, dtype=float),
            "cash_closed",
            reason,
            {asset: reason for asset in assets},
            {asset: "cash_closed" for asset in assets},
        )

    latest = _latest_rule100_candidates_for_date(candidates, date_value)
    if latest.empty:
        return (
            pd.Series(0.0, index=assets, dtype=float),
            "cash_only",
            "no_rule100_candidates_available_as_of_date",
            row_reasons,
            row_statuses,
        )

    # Adapter validation on PIT-sliced frame — fail closed
    if adapter is not None:
        result = adapter.validate_inputs(str(date_value.date()), latest)
        if not result.ok:
            reason = f"adapter_validation_failed:{result.reason}"
            return (
                pd.Series(0.0, index=assets, dtype=float),
                "cash_closed",
                reason,
                {asset: reason for asset in assets},
                {asset: "cash_closed" for asset in assets},
            )

    target_rows: list[pd.Series] = []
    target_assets: list[Any] = []
    for _, row in latest.iterrows():
        keys = []
        if "ticker" in latest.columns:
            keys.append(str(row.get("ticker", "")).upper().strip())
        if "permno" in latest.columns and pd.notna(row.get("permno")):
            keys.append(str(row.get("permno")).upper().strip())
        asset = next((lookup[key] for key in keys if key in lookup), None)
        if asset is None:
            continue
        target_rows.append(row)
        target_assets.append(asset)
        eligible = bool(row.get("sizing_eligible", False))
        row_reasons[asset] = str(row.get("eligibility_reason", "eligible_buy_or_hold" if eligible else "not_sizing_eligible"))
        row_statuses[asset] = "ok" if eligible else "cash_only"

    if not target_rows:
        return (
            pd.Series(0.0, index=assets, dtype=float),
            "cash_only",
            "no_rule100_candidates_matched_price_universe",
            row_reasons,
            row_statuses,
        )

    selected = pd.DataFrame(target_rows).reset_index(drop=True)
    selected["_target_asset"] = target_assets
    eligible_mask = selected.get(
        "sizing_eligible",
        pd.Series(False, index=selected.index, dtype=bool),
    ).astype(bool)
    eligible = selected.loc[eligible_mask].copy()
    if eligible.empty:
        return (
            pd.Series(0.0, index=assets, dtype=float),
            "cash_only",
            "no_rule100_sizing_eligible_candidates_as_of_date",
            row_reasons,
            row_statuses,
        )

    # Use adapter.allocation_fn if available; otherwise fall back to direct call
    if adapter is not None:
        controls_for_adapter = {"max_weight": max_weight}
        weights_by_row = adapter.allocation_fn(str(date_value.date()), eligible, controls_for_adapter)
    else:
        weights_by_row = softmax_v1_weights(
            eligible,
            rule100_config_from_max_weight(max_weight),
        )

    weights = pd.Series(0.0, index=assets, dtype=float)
    for idx, weight in weights_by_row.items():
        asset = eligible.loc[idx, "_target_asset"]
        weights.loc[asset] = float(weights.loc[asset]) + float(weight)
        row_reasons[asset] = str(eligible.loc[idx].get("eligibility_reason", "eligible_buy_or_hold"))
        row_statuses[asset] = "ok"

    status = "ok" if float(weights.sum()) > 0.0 else "cash_only"
    return weights, status, "rule100_softmax_v1_replay", row_reasons, row_statuses


def _build_rule100_replay(
    *,
    method: OptimizationMethod,
    controls: Any,
    prices: pd.DataFrame,
    ticker_map: dict | None,
    as_of_dates: list[pd.Timestamp],
    max_weight: float,
) -> pd.DataFrame:
    candidates = _prepare_rule100_candidates(_rule100_candidates_from_controls(controls))
    assets = pd.Index(prices.columns)
    rows: list[dict[str, Any]] = []
    for date_value in as_of_dates:
        weights, status, reason, row_reasons, row_statuses = _build_rule100_weights_for_date(
            candidates=candidates,
            date_value=date_value,
            prices=prices,
            ticker_map=ticker_map,
            max_weight=max_weight,
        )
        rows.extend(
            _rows_for_date(
                date_value=date_value,
                method=method,
                assets=assets,
                ticker_map=ticker_map,
                weights=weights,
                cap_used=max_weight,
                cap_source=CAP_SOURCE_CONTROLS,
                source=RULE100_REPLAY_SOURCE,
                status=status,
                reason=reason,
                row_reasons=row_reasons,
                row_statuses=row_statuses,
            )
        )
    return pd.DataFrame(rows, columns=REPLAY_COLUMNS)


def build_strategy_replay(
    method: OptimizationMethod | str,
    controls: Any,
    prices: pd.DataFrame | StrategyReplayInputs,
    ticker_map: dict | None = None,
    sector_map: dict | None = None,
    as_of_range: Iterable[Any] | tuple[Any, Any] | None = None,
    _attach_performance_path: bool = True,
) -> pd.DataFrame:
    """Build a method-aware point-in-time target-weight replay.

    Each replay date slices price history at ``<= date`` and emits one row for
    every asset in ``prices`` plus one CASH row. Optimizer failures and fallback
    allocations fail closed to cash for that date.
    """

    del sector_map  # Reserved for future diagnostics; no sector policy is added here.
    selected_method = _coerce_method(method)
    if selected_method not in OPTIMIZATION_METHOD_OPTIONS:
        raise ValueError(f"Unsupported optimization method: {method!r}")

    replay_inputs = prices if isinstance(prices, StrategyReplayInputs) else None
    if replay_inputs is not None:
        price_frame = _as_price_frame(replay_inputs.prices)
        return_frame = _as_return_frame(replay_inputs.returns, price_frame)
        ticker_map = replay_inputs.ticker_map if ticker_map is None else ticker_map
        if as_of_range is None:
            as_of_range = [replay_inputs.as_of_date]
    else:
        price_frame = _as_price_frame(prices)
        return_frame = _as_return_frame(None, price_frame)
    max_weight = _control_max_weight(controls)
    risk_free_rate = _control_risk_free_rate(controls)
    if price_frame.empty:
        if replay_inputs is None:
            return pd.DataFrame(columns=REPLAY_COLUMNS)
        date_frame = pd.DataFrame(index=pd.DatetimeIndex([replay_inputs.as_of_date]))
        as_of_dates = _coerce_as_of_dates(as_of_range, date_frame)
        if not as_of_dates:
            as_of_dates = [pd.Timestamp(replay_inputs.as_of_date)]
        if selected_method == OptimizationMethod.RULE_OF_100:
            source = RULE100_REPLAY_SOURCE
        else:
            runtime_method, _resolution_reason = _resolve_replay_method(selected_method)
            source = f"{REPLAY_SOURCE}:{runtime_method.value}"
        rows: list[dict[str, Any]] = []
        for date_value in as_of_dates:
            rows.extend(
                _cash_closed_rows(
                    date_value=date_value,
                    method=selected_method,
                    assets=pd.Index([]),
                    ticker_map=ticker_map,
                    cap_used=max_weight,
                    source=source,
                    reason="no_selected_assets_in_pit_universe_as_of_date",
                )
            )
        replay = pd.DataFrame(rows)
        if not _attach_performance_path:
            return replay.reindex(columns=REPLAY_COLUMNS)
        return _attach_replay_performance(replay, return_frame)

    as_of_dates = _coerce_as_of_dates(as_of_range, price_frame)

    if selected_method == OptimizationMethod.RULE_OF_100:
        replay = _build_rule100_replay(
            method=selected_method,
            controls=controls,
            prices=price_frame,
            ticker_map=ticker_map,
            as_of_dates=as_of_dates,
            max_weight=max_weight,
        )
        if not _attach_performance_path:
            return replay.reindex(columns=REPLAY_COLUMNS)
        return _attach_replay_performance(replay, return_frame)

    assets = pd.Index(price_frame.columns)
    optimizer = PortfolioOptimizer()
    runtime_method, resolution_reason = _resolve_replay_method(selected_method)
    source = f"{REPLAY_SOURCE}:{runtime_method.value}"
    rows: list[dict[str, Any]] = []

    for date_value in as_of_dates:
        price_slice = price_frame.loc[price_frame.index <= pd.Timestamp(date_value), :]
        if price_slice.empty or not bool(price_slice.notna().any().any()):
            rows.extend(
                _cash_closed_rows(
                    date_value=date_value,
                    method=selected_method,
                    assets=assets,
                    ticker_map=ticker_map,
                    cap_used=max_weight,
                    source=source,
                    reason="no_price_history_available_as_of_date",
                )
            )
            continue

        try:
            result = _run_optimizer_for_method(
                optimizer=optimizer,
                method=selected_method,
                prices=price_slice,
                max_weight=max_weight,
                risk_free_rate=risk_free_rate,
            )
        except Exception as exc:
            rows.extend(
                _cash_closed_rows(
                    date_value=date_value,
                    method=selected_method,
                    assets=assets,
                    ticker_map=ticker_map,
                    cap_used=max_weight,
                    source=source,
                    reason=f"optimizer_exception:{type(exc).__name__}",
                )
            )
            continue

        weights, ok, reason = _usable_optimizer_weights(result, assets, max_weight)
        if not ok:
            rows.extend(
                _cash_closed_rows(
                    date_value=date_value,
                    method=selected_method,
                    assets=assets,
                    ticker_map=ticker_map,
                    cap_used=max_weight,
                    source=source,
                    reason=reason,
                )
            )
            continue

        rows.extend(
            _rows_for_date(
                date_value=date_value,
                method=selected_method,
                assets=assets,
                ticker_map=ticker_map,
                weights=weights,
                cap_used=max_weight,
                cap_source=CAP_SOURCE_CONTROLS,
                source=source,
                status="ok",
                reason=resolution_reason,
            )
        )

    replay = pd.DataFrame(rows)
    if not _attach_performance_path:
        return replay.reindex(columns=REPLAY_COLUMNS)
    return _attach_replay_performance(replay, return_frame)


def _is_strategy_input_sequence(value: Any) -> bool:
    return isinstance(value, (list, tuple)) and all(isinstance(item, StrategyReplayInputs) for item in value)


def _coerce_forward_walk_dates(
    *,
    as_of_range: Iterable[Any] | tuple[Any, Any] | None,
    start_date: Any,
    end_date: Any,
    prices: Any,
) -> list[pd.Timestamp]:
    if as_of_range is not None:
        return _coerce_as_of_dates(as_of_range, _as_price_frame(prices) if isinstance(prices, pd.DataFrame) else pd.DataFrame())
    start_ts = pd.to_datetime(start_date, errors="coerce") if start_date is not None else pd.NaT
    end_ts = pd.to_datetime(end_date, errors="coerce") if end_date is not None else pd.NaT
    if not pd.isna(start_ts) and not pd.isna(end_ts):
        return [pd.Timestamp(value) for value in pd.date_range(pd.Timestamp(start_ts).normalize(), pd.Timestamp(end_ts).normalize(), freq="D")]
    if not pd.isna(end_ts):
        return [pd.Timestamp(end_ts).normalize()]
    if not pd.isna(start_ts):
        return [pd.Timestamp(start_ts).normalize()]
    if isinstance(prices, StrategyReplayInputs):
        return [pd.Timestamp(prices.as_of_date).normalize()]
    if _is_strategy_input_sequence(prices):
        return [pd.Timestamp(item.as_of_date).normalize() for item in prices]
    if isinstance(prices, pd.DataFrame):
        return _coerce_as_of_dates(None, _as_price_frame(prices))
    return []


def _input_loader_kwargs(
    *,
    date_value: pd.Timestamp,
    selected_method: OptimizationMethod,
    controls: Any,
    max_weight: float,
    replay_start: Any,
) -> dict[str, Any]:
    date_label = pd.Timestamp(date_value).date().isoformat()
    return {
        "as_of_date": date_label,
        "start_date": _iso_or_none(replay_start) or date_label,
        "end_date": date_label,
        "method": selected_method.value,
        "controls": _controls_signature_payload(controls),
        "max_weight": max_weight,
    }


def _cash_closed_frame_for_date(
    *,
    date_value: pd.Timestamp,
    method: OptimizationMethod,
    ticker_map: dict | None,
    max_weight: float,
    reason: str,
) -> pd.DataFrame:
    source = _source_for_method(method)
    rows = _cash_closed_rows(
        date_value=pd.Timestamp(date_value),
        method=method,
        assets=pd.Index([]),
        ticker_map=ticker_map,
        cap_used=max_weight,
        source=source,
        reason=reason,
    )
    return _attach_replay_performance(pd.DataFrame(rows), pd.DataFrame())


def _build_replay_from_pit_inputs(
    *,
    selected_method: OptimizationMethod,
    controls: Any,
    pit_inputs: Iterable[StrategyReplayInputs],
    ticker_map: dict | None,
    sector_map: dict | None,
    max_weight: float,
    attach_performance_path: bool = True,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    return_frames: list[pd.DataFrame] = []
    input_signatures: list[dict[str, Any]] = []
    for inputs in pit_inputs:
        input_signatures.append(_strategy_inputs_signature(inputs))
        date_value = pd.Timestamp(inputs.as_of_date).normalize()
        input_returns = _as_return_frame(inputs.returns, _as_price_frame(inputs.prices))
        if not input_returns.empty:
            return_frames.append(input_returns)
        try:
            frames.append(
                build_strategy_replay(
                    method=selected_method,
                    controls=controls,
                    prices=inputs,
                    ticker_map=ticker_map,
                    sector_map=sector_map,
                    as_of_range=None,
                    _attach_performance_path=False,
                )
            )
        except Exception as exc:
            frames.append(
                _cash_closed_frame_for_date(
                    date_value=date_value,
                    method=selected_method,
                    ticker_map=ticker_map,
                    max_weight=max_weight,
                    reason=f"pit_replay_exception:{type(exc).__name__}",
                )
            )
    if not frames:
        return pd.DataFrame(columns=REPLAY_COLUMNS), input_signatures
    replay = pd.concat(frames, ignore_index=True, sort=False).reindex(columns=REPLAY_COLUMNS)
    if not attach_performance_path:
        return replay, input_signatures
    returns = pd.concat(return_frames, axis=0, sort=False) if return_frames else pd.DataFrame()
    return _attach_replay_performance(replay, returns), input_signatures


def _build_replay_from_input_loader(
    *,
    selected_method: OptimizationMethod,
    controls: Any,
    input_loader: Callable[..., StrategyReplayInputs],
    replay_dates: list[pd.Timestamp],
    replay_start: Any,
    ticker_map: dict | None,
    sector_map: dict | None,
    max_weight: float,
    coverage_plan: list[ReplayDateCoverage] | None = None,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    unavailable_rows: list[dict[str, Any]] = []
    return_frames: list[pd.DataFrame] = []
    input_signatures: list[dict[str, Any]] = []
    source = _source_for_method(selected_method)

    def _flush_unavailable_rows() -> None:
        nonlocal unavailable_rows
        if unavailable_rows:
            frames.append(pd.DataFrame(unavailable_rows))
            unavailable_rows = []

    # Build coverage lookup if provided
    coverage_by_date: dict[str, ReplayDateCoverage] = {}
    if coverage_plan:
        for entry in coverage_plan:
            coverage_by_date[entry.date.normalize().date().isoformat()] = entry

    for date_value in replay_dates:
        date_iso = pd.Timestamp(date_value).normalize().date().isoformat()
        cov = coverage_by_date.get(date_iso)

        # Pre-replay gate: emit input_unavailable for uncovered dates
        if cov is not None and not cov.covered:
            assets = pd.Index(cov.expected_members) if cov.expected_members else pd.Index([])
            effective_ticker_map = ticker_map
            if cov.expected_members and not ticker_map:
                # Try to build ticker map from input_loader metadata
                effective_ticker_map = None
            unavailable_rows.extend(
                _cash_closed_rows_fast(
                    date_value=pd.Timestamp(date_value),
                    method=selected_method,
                    assets=assets,
                    ticker_map=effective_ticker_map,
                    cap_used=max_weight,
                    source=source,
                    reason=f"input_unavailable:{cov.reason}",
                )
            )
            input_signatures.append({
                "type": "InputUnavailable",
                "as_of_date": date_iso,
                "reason": cov.reason,
                "expected_member_count": len(cov.expected_members),
                "membership_date": cov.membership_date,
            })
            continue

        _flush_unavailable_rows()
        kwargs = _input_loader_kwargs(
            date_value=date_value,
            selected_method=selected_method,
            controls=controls,
            max_weight=max_weight,
            replay_start=replay_start,
        )
        try:
            inputs = input_loader(**kwargs)
            if not isinstance(inputs, StrategyReplayInputs):
                raise TypeError("input_loader_must_return_StrategyReplayInputs")
            input_signatures.append(_strategy_inputs_signature(inputs))
            input_returns = _as_return_frame(inputs.returns, _as_price_frame(inputs.prices))
            if not input_returns.empty:
                return_frames.append(input_returns)
            replay_for_date, _signatures = _build_replay_from_pit_inputs(
                selected_method=selected_method,
                controls=controls,
                pit_inputs=[inputs],
                ticker_map=ticker_map,
                sector_map=sector_map,
                max_weight=max_weight,
                attach_performance_path=False,
            )
            frames.append(replay_for_date)
        except Exception as exc:
            date_label = pd.Timestamp(date_value).date().isoformat()
            input_signatures.append(
                {
                    "type": "StrategyReplayInputsLoaderFailure",
                    "as_of_date": date_label,
                    "start_date": kwargs["start_date"],
                    "end_date": kwargs["end_date"],
                    "reason": type(exc).__name__,
                }
            )
            frames.append(
                _cash_closed_frame_for_date(
                    date_value=date_value,
                    method=selected_method,
                    ticker_map=ticker_map,
                    max_weight=max_weight,
                    reason=f"pit_input_exception:{type(exc).__name__}",
                )
            )
    _flush_unavailable_rows()
    if not frames:
        return pd.DataFrame(columns=REPLAY_COLUMNS), input_signatures
    replay = pd.concat(frames, ignore_index=True, sort=False).reindex(columns=REPLAY_COLUMNS)
    returns = pd.concat(return_frames, axis=0, sort=False) if return_frames else pd.DataFrame()
    return _attach_replay_performance(replay, returns), input_signatures


def _control_context_frame(controls: Any, names: tuple[str, ...]) -> pd.DataFrame | None:
    for name in names:
        value = _control_value(controls, name, None)
        if isinstance(value, pd.DataFrame):
            return value.copy()
    return None


def _empty_context(context_type: str, method: OptimizationMethod, *, reason: str) -> StrategyReplayContext:
    frame = pd.DataFrame(columns=REPLAY_CONTEXT_COLUMNS)
    frame["method"] = pd.Series(dtype=object)
    return StrategyReplayContext(
        context_type=context_type,
        frame=frame,
        status="empty",
        reason=reason,
        source=f"strategy_replay_context:{context_type}:{method.value}",
    )


def _replay_context_weight_lookup(replay: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(replay, pd.DataFrame) or replay.empty:
        return pd.DataFrame(columns=["date", "ticker", "replay_target_weight"])
    if "date" not in replay.columns or "ticker" not in replay.columns or "target_weight" not in replay.columns:
        return pd.DataFrame(columns=["date", "ticker", "replay_target_weight"])
    lookup = replay[["date", "ticker", "target_weight"]].copy()
    lookup["date"] = pd.to_datetime(lookup["date"], errors="coerce").dt.normalize()
    lookup["ticker"] = lookup["ticker"].astype(str).str.upper().str.strip()
    lookup["replay_target_weight"] = pd.to_numeric(lookup["target_weight"], errors="coerce").fillna(0.0).clip(lower=0.0)
    lookup = lookup[(lookup["date"].notna()) & (lookup["ticker"] != "") & (lookup["ticker"] != "CASH")]
    if lookup.empty:
        return pd.DataFrame(columns=["date", "ticker", "replay_target_weight"])
    lookup = lookup.sort_values(["date", "ticker"], kind="mergesort")
    return lookup.drop_duplicates(["date", "ticker"], keep="last")[["date", "ticker", "replay_target_weight"]]


def _normalize_context_frame(
    frame: pd.DataFrame | None,
    *,
    context_type: str,
    method: OptimizationMethod,
    replay: pd.DataFrame,
) -> StrategyReplayContext:
    if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
        return _empty_context(context_type, method, reason=f"no_{context_type}_context_provided")

    dates = pd.to_datetime(replay.get("date", pd.Series(dtype=object)), errors="coerce").dropna().dt.normalize()
    if dates.empty:
        return _empty_context(context_type, method, reason="replay_has_no_valid_dates")
    start_date = dates.min()
    end_date = dates.max()
    tickers = {
        str(value).upper().strip()
        for value in replay.get("ticker", pd.Series(dtype=object)).dropna().unique()
        if str(value).upper().strip() != "CASH"
    }

    work = frame.copy()
    if "date" not in work.columns:
        return _empty_context(context_type, method, reason=f"{context_type}_context_missing_date")
    if "ticker" not in work.columns:
        return _empty_context(context_type, method, reason=f"{context_type}_context_missing_ticker")

    work["date"] = pd.to_datetime(work["date"], errors="coerce").dt.normalize()
    work["ticker"] = work["ticker"].astype(str).str.upper().str.strip()
    work = work[work["date"].notna()].copy()
    work = work[(work["date"] >= start_date) & (work["date"] <= end_date)]
    if tickers:
        work = work[work["ticker"].isin(tickers)]
    if "method" in work.columns:
        method_text = method.value
        method_values = work["method"].astype(str)
        work = work[(method_values == method_text) | (method_values.str.lower().isin(["", "all", "nan", "none"]))]

    if work.empty:
        return _empty_context(context_type, method, reason=f"no_{context_type}_context_in_replay_window")

    replay_weights = _replay_context_weight_lookup(replay)
    if not replay_weights.empty:
        work = work.merge(replay_weights, on=["date", "ticker"], how="left")
    else:
        work["replay_target_weight"] = 0.0

    normalized = pd.DataFrame(index=work.index)
    normalized["date"] = work["date"].dt.date.astype(str)
    normalized["method"] = method.value
    normalized["ticker"] = work["ticker"]
    normalized["context_type"] = context_type
    normalized["row_role"] = context_type
    normalized["context_role"] = _context_role_from_aux_rows(work, replay_weights)
    normalized["action"] = work["action"] if "action" in work.columns else ""
    normalized["buy_sell"] = work["buy_sell"] if "buy_sell" in work.columns else ""
    normalized["target_weight"] = pd.to_numeric(
        work["replay_target_weight"],
        errors="coerce",
    ).fillna(0.0).clip(lower=0.0)
    if "weight" in work.columns:
        weight_source = work["weight"]
    elif "target_weight" in work.columns:
        weight_source = work["target_weight"]
    else:
        weight_source = normalized["target_weight"]
    normalized["weight"] = pd.to_numeric(weight_source, errors="coerce").fillna(0.0).clip(lower=0.0)
    if "primary_reason" in work.columns:
        normalized["reason"] = work["primary_reason"].astype(str)
    elif "reason" in work.columns:
        normalized["reason"] = work["reason"].astype(str)
    else:
        normalized["reason"] = ""
    normalized["source"] = work["source"].astype(str) if "source" in work.columns else f"controls.{context_type}_context"
    normalized["status"] = "ok"
    normalized = normalized.reindex(columns=REPLAY_CONTEXT_COLUMNS).sort_values(["date", "ticker"], kind="mergesort")

    return StrategyReplayContext(
        context_type=context_type,
        frame=normalized.reset_index(drop=True),
        status="ok",
        reason=f"{context_type}_context_attached",
        source=f"strategy_replay_context:{context_type}:{method.value}",
    )


def normalize_context_frame_for_replay(
    frame: pd.DataFrame | None,
    *,
    context_type: str,
    method: OptimizationMethod | str,
    replay: pd.DataFrame,
) -> pd.DataFrame:
    """Public replay-context normalization contract for dashboard adapters."""

    return _normalize_context_frame(
        frame,
        context_type=context_type,
        method=_coerce_method(method),
        replay=replay,
    ).frame


def _build_run_metadata(
    *,
    method: OptimizationMethod,
    controls: Any,
    replay: pd.DataFrame,
    event_context: StrategyReplayContext,
    decision_context: StrategyReplayContext,
    input_signatures: list[dict[str, Any]],
    requested_start: Any,
    requested_end: Any,
    started_at_utc: str,
    completed_at_utc: str,
    elapsed_ms: float,
    run_id: str | None,
    source_id: str | None,
    coverage_plan: list[ReplayDateCoverage] | None = None,
) -> StrategyReplayRunMetadata:
    date_window = _date_window_from_replay(
        replay,
        requested_start=requested_start,
        requested_end=requested_end,
    )
    row_counts = {
        "daily_portfolio": int(len(replay)) if isinstance(replay, pd.DataFrame) else 0,
        "event_annotations": int(len(event_context.frame)),
        "buy_sell_decisions": int(len(decision_context.frame)),
    }
    row_counts["total"] = int(sum(row_counts.values()))
    status_counts = {
        "daily_portfolio": _status_counts(replay),
        "event_annotations": _status_counts(event_context.frame, empty_status=event_context.status),
        "buy_sell_decisions": _status_counts(decision_context.frame, empty_status=decision_context.status),
    }
    safe_signatures = tuple(_metadata_json_safe(item) for item in input_signatures)
    controls_signature = _controls_signature_payload(controls)
    seed = {
        "method_id": method.value,
        "date_window": date_window,
        "input_signatures": safe_signatures,
        "controls": controls_signature,
    }
    resolved_run_id = str(run_id or f"strategy_replay_{_json_fingerprint(seed, length=18)}")
    resolved_source_id = str(source_id or f"selected_method_replay:{method.value}:{resolved_run_id}")

    # Derive coverage metadata from coverage_plan (linear scan results)
    coverage_start_value: str | None = None
    coverage_end_value: str | None = None
    coverage_warnings_list: list[str] = []
    uncovered_reasons: dict[str, int] = {}

    coverage_segments: list[dict[str, Any]] = []

    if coverage_plan:
        covered_dates = [e for e in coverage_plan if e.covered]
        uncovered_dates = [e for e in coverage_plan if not e.covered]
        if covered_dates:
            coverage_start_value = covered_dates[0].date.date().isoformat()
            coverage_end_value = covered_dates[-1].date.date().isoformat()
        for e in uncovered_dates:
            uncovered_reasons[e.reason] = uncovered_reasons.get(e.reason, 0) + 1
        if uncovered_dates:
            coverage_warnings_list.append(
                f"uncovered_dates={len(uncovered_dates)};reasons={uncovered_reasons}"
            )
        # Derive contiguous coverage segments (covered/uncovered runs)
        if coverage_plan:
            seg_start = coverage_plan[0]
            seg_covered = coverage_plan[0].covered
            prev = coverage_plan[0]
            for entry in coverage_plan[1:]:
                if entry.covered != seg_covered:
                    coverage_segments.append({
                        "start": seg_start.date.date().isoformat(),
                        "end": prev.date.date().isoformat(),
                        "covered": seg_covered,
                    })
                    seg_start = entry
                    seg_covered = entry.covered
                prev = entry
            coverage_segments.append({
                "start": seg_start.date.date().isoformat(),
                "end": coverage_plan[-1].date.date().isoformat(),
                "covered": seg_covered,
            })
    else:
        # Fallback: try adapter registry (legacy path)
        try:
            from strategies.adapter_registry import get_adapter
            adapter = get_adapter(method)
            if adapter is not None:
                coverage_start_value = adapter.input_coverage_start
        except Exception:
            pass
        # Emit warning for replay rows before coverage start
        if coverage_start_value and isinstance(replay, pd.DataFrame) and not replay.empty and "date" in replay.columns:
            replay_dates_series = pd.to_datetime(replay["date"], errors="coerce").dropna()
            pre_coverage = replay_dates_series[replay_dates_series < pd.Timestamp(coverage_start_value)]
            if not pre_coverage.empty:
                req_start = _iso_or_none(requested_start) or pre_coverage.min().date().isoformat()
                statuses = replay.loc[pre_coverage.index, "status"].value_counts().to_dict() if "status" in replay.columns else {}
                coverage_warnings_list.append(
                    f"pre_coverage_dates={len(pre_coverage)};requested_start={req_start};coverage_start={coverage_start_value};"
                    + ";".join(f"{k}={v}" for k, v in sorted(statuses.items()))
                )

    # Enrich date_window with coverage fields
    date_window["input_coverage_start"] = coverage_start_value
    date_window["input_coverage_end"] = coverage_end_value
    date_window["uncovered_reasons"] = uncovered_reasons if uncovered_reasons else None
    date_window["coverage_segments"] = coverage_segments if coverage_segments else None

    return StrategyReplayRunMetadata(
        run_id=resolved_run_id,
        method_id=method.value,
        source_id=resolved_source_id,
        input_signatures=safe_signatures,
        date_window=date_window,
        row_counts=row_counts,
        status_counts=status_counts,
        timing={
            "started_at_utc": started_at_utc,
            "completed_at_utc": completed_at_utc,
            "elapsed_ms": round(float(elapsed_ms), 3),
        },
        controls_signature=controls_signature,
        input_coverage_start=coverage_start_value,
        effective_start=coverage_start_value or date_window.get("replay_start"),
        coverage_warnings=tuple(coverage_warnings_list),
    )


def build_selected_method_replay(
    method: OptimizationMethod | str,
    controls: Any,
    prices: pd.DataFrame | StrategyReplayInputs | Iterable[StrategyReplayInputs] | None,
    ticker_map: dict | None = None,
    sector_map: dict | None = None,
    as_of_range: Iterable[Any] | tuple[Any, Any] | None = None,
    *,
    event_context: pd.DataFrame | None = None,
    decision_context: pd.DataFrame | None = None,
    input_loader: Callable[..., StrategyReplayInputs] | None = None,
    start_date: Any = None,
    end_date: Any = None,
    run_id: str | None = None,
    source_id: str | None = None,
    coverage_plan: list[ReplayDateCoverage] | None = None,
) -> StrategyReplayBundle:
    """Build the shared selected-method replay bundle for backend consumers.

    The replay frame is the single source for target weights, latest allocation,
    and performance. Event and buy/sell decision context is attached through
    typed optional frames and filtered to the replay window to preserve PIT
    boundaries.
    """

    started_at_utc = _utc_now_iso()
    perf_start = time.perf_counter()
    selected_method = _coerce_method(method)
    max_weight = _control_max_weight(controls)
    input_signatures: list[dict[str, Any]] = []
    requested_start = start_date
    requested_end = end_date

    if input_loader is not None:
        replay_dates = _coerce_forward_walk_dates(
            as_of_range=as_of_range,
            start_date=start_date,
            end_date=end_date,
            prices=prices,
        )
        if replay_dates:
            requested_start = start_date if start_date is not None else replay_dates[0]
            requested_end = end_date if end_date is not None else replay_dates[-1]
        replay, input_signatures = _build_replay_from_input_loader(
            selected_method=selected_method,
            controls=controls,
            input_loader=input_loader,
            replay_dates=replay_dates,
            replay_start=requested_start,
            ticker_map=ticker_map,
            sector_map=sector_map,
            max_weight=max_weight,
            coverage_plan=coverage_plan,
        )
    elif _is_strategy_input_sequence(prices):
        pit_inputs = list(prices)  # type: ignore[arg-type]
        if pit_inputs:
            requested_start = start_date if start_date is not None else pit_inputs[0].as_of_date
            requested_end = end_date if end_date is not None else pit_inputs[-1].as_of_date
        replay, input_signatures = _build_replay_from_pit_inputs(
            selected_method=selected_method,
            controls=controls,
            pit_inputs=pit_inputs,
            ticker_map=ticker_map,
            sector_map=sector_map,
            max_weight=max_weight,
        )
    else:
        replay_prices = prices if prices is not None else pd.DataFrame()
        if isinstance(replay_prices, StrategyReplayInputs):
            input_signatures.append(_strategy_inputs_signature(replay_prices))
            requested_start = start_date if start_date is not None else replay_prices.metadata.get("effective_date_range", {}).get("start")
            requested_end = end_date if end_date is not None else replay_prices.as_of_date
        elif isinstance(replay_prices, pd.DataFrame):
            input_signatures.append(_price_frame_signature(replay_prices, label="price_frame"))
        effective_as_of_range = as_of_range
        if effective_as_of_range is None and start_date is not None and end_date is not None:
            effective_as_of_range = (start_date, end_date)
        replay = build_strategy_replay(
            method=selected_method,
            controls=controls,
            prices=replay_prices,
            ticker_map=ticker_map,
            sector_map=sector_map,
            as_of_range=effective_as_of_range,
        )
    event_frame = event_context
    if event_frame is None:
        event_frame = _control_context_frame(controls, ("event_context_frame", "event_annotations", "annotation_context_frame"))
    decision_frame = decision_context
    if decision_frame is None:
        decision_frame = _control_context_frame(controls, ("decision_context_frame", "buy_sell_context_frame", "decision_log_context"))

    event_ctx = _normalize_context_frame(
        event_frame,
        context_type="event_annotations",
        method=selected_method,
        replay=replay,
    )
    decision_ctx = _normalize_context_frame(
        decision_frame,
        context_type="decision_context",
        method=selected_method,
        replay=replay,
    )
    completed_at_utc = _utc_now_iso()
    metadata = _build_run_metadata(
        method=selected_method,
        controls=controls,
        replay=replay,
        event_context=event_ctx,
        decision_context=decision_ctx,
        input_signatures=input_signatures,
        requested_start=requested_start,
        requested_end=requested_end,
        started_at_utc=started_at_utc,
        completed_at_utc=completed_at_utc,
        elapsed_ms=(time.perf_counter() - perf_start) * 1000.0,
        run_id=run_id,
        source_id=source_id,
        coverage_plan=coverage_plan,
    )
    return StrategyReplayBundle(
        replay=replay,
        event_context=event_ctx,
        decision_context=decision_ctx,
        run_metadata=metadata,
    )


def selected_method_replay_bundle_to_frame(bundle: StrategyReplayBundle) -> pd.DataFrame:
    """Pack daily portfolio, annotation, and decision rows into one artifact frame."""

    parts: list[pd.DataFrame] = []
    row_specs = (
        ("daily_portfolio", bundle.daily_portfolio),
        ("event_annotation", bundle.event_rows),
        ("buy_sell_decision", bundle.decision_rows),
    )
    for row_type, frame in row_specs:
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            continue
        out = frame.copy()
        out["row_type"] = row_type
        out["row_role"] = row_type
        out["run_id"] = bundle.run_id
        out["source_id"] = bundle.run_metadata.source_id
        out["artifact_scope"] = SELECTED_METHOD_REPLAY_ARTIFACT_TYPE
        if row_type != "daily_portfolio" and "target_weight" not in out.columns and "weight" in out.columns:
            out["target_weight"] = out["weight"]
        if row_type == "daily_portfolio" and "weight" not in out.columns and "target_weight" in out.columns:
            out["weight"] = out["target_weight"]
        if row_type == "daily_portfolio":
            out = _coerce_replay_roles(out)
            out["row_type"] = row_type
            out["row_role"] = row_type
        elif "context_role" not in out.columns:
            target = pd.to_numeric(out.get("target_weight", pd.Series(np.nan, index=out.index)), errors="coerce")
            out["context_role"] = "flat_in_replay"
            out.loc[target > 0.0, "context_role"] = "current_holding"
            out.loc[target.isna(), "context_role"] = "unavailable"
        for col in SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS:
            if col not in out.columns:
                out[col] = "" if col in {
                    "context_type",
                    "row_role",
                    "context_role",
                    "action",
                    "buy_sell",
                    "reason",
                    "source",
                    "status",
                    "permno",
                } else np.nan
        parts.append(out.reindex(columns=SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS))

    if not parts:
        return pd.DataFrame(columns=SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS)
    artifact = pd.concat(parts, ignore_index=True, sort=False).reset_index(drop=True)
    text_columns = {
        "row_type",
        "run_id",
        "source_id",
        "date",
        "method",
        "ticker",
        "permno",
        "cap_source",
        "context_type",
        "row_role",
        "context_role",
        "action",
        "buy_sell",
        "reason",
        "source",
        "status",
        "artifact_scope",
    }
    for col in text_columns.intersection(artifact.columns):
        artifact[col] = artifact[col].where(artifact[col].notna(), "").astype(str)
    return artifact.reindex(columns=SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS)


def _resolve_project_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path(__file__).resolve().parents[1] / candidate
    return candidate.resolve(strict=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_selected_method_replay_artifact_path(
    output_path: Path,
    *,
    cache_dir: str | Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_root = (repo_root / "data").resolve(strict=False)
    canonical_runtime_cache = (repo_root / SELECTED_METHOD_REPLAY_CACHE_DIR).resolve(strict=False)
    resolved_output = _resolve_project_path(output_path)
    resolved_cache = _resolve_project_path(cache_dir)
    if _is_relative_to(resolved_cache, data_root) and not _is_relative_to(resolved_cache, canonical_runtime_cache):
        raise ValueError(
            "Selected-method replay cache_dir must stay under data/runtime_cache/strategy_replay for repo data writes."
        )
    if _is_relative_to(resolved_output, data_root) and not _is_relative_to(resolved_output, canonical_runtime_cache):
        raise ValueError(
            "Selected-method replay output artifacts may not be written under data/ outside data/runtime_cache/strategy_replay."
        )


def _temp_path_for(path: Path, suffix: str) -> Path:
    return path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.{suffix}.tmp")


def _stage_parquet(path: Path, frame: pd.DataFrame, *, index: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _temp_path_for(path, "stage")
    try:
        frame.to_parquet(tmp_path, index=index)
        return tmp_path
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def _stage_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _temp_path_for(path, "stage")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        return tmp_path
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def _atomic_write_parquet(path: Path, frame: pd.DataFrame, *, index: bool = False) -> None:
    tmp_path = _stage_parquet(path, frame, index=index)
    try:
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _atomic_write_text(path: Path, text: str) -> None:
    tmp_path = _stage_text(path, text)
    try:
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _remove_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink(missing_ok=True)


def _restore_or_remove(
    path: Path,
    backup_path: Path,
    *,
    had_original: bool,
) -> None:
    if had_original and backup_path.exists():
        os.replace(backup_path, path)
    else:
        _remove_if_exists(path)


def _promote_selected_method_replay_bundle(
    *,
    artifact_tmp_path: Path,
    artifact_path: Path,
    manifest_tmp_path: Path,
    manifest_path: Path,
) -> None:
    """Promote replay parquet and manifest as one rollback-safe bundle."""

    artifact_backup_path = _temp_path_for(artifact_path, "backup")
    manifest_backup_path = _temp_path_for(manifest_path, "backup")
    artifact_had_original = artifact_path.exists()
    manifest_had_original = manifest_path.exists()
    artifact_promoted = False
    manifest_promoted = False

    try:
        if artifact_had_original:
            os.replace(artifact_path, artifact_backup_path)
        if manifest_had_original:
            os.replace(manifest_path, manifest_backup_path)

        os.replace(artifact_tmp_path, artifact_path)
        artifact_promoted = True
        os.replace(manifest_tmp_path, manifest_path)
        manifest_promoted = True

        _remove_if_exists(artifact_backup_path)
        _remove_if_exists(manifest_backup_path)
    except Exception:
        if artifact_promoted or artifact_path.exists():
            _restore_or_remove(
                artifact_path,
                artifact_backup_path,
                had_original=artifact_had_original,
            )
        elif artifact_had_original and artifact_backup_path.exists():
            os.replace(artifact_backup_path, artifact_path)

        if manifest_promoted or manifest_path.exists():
            _restore_or_remove(
                manifest_path,
                manifest_backup_path,
                had_original=manifest_had_original,
            )
        elif manifest_had_original and manifest_backup_path.exists():
            os.replace(manifest_backup_path, manifest_path)
        raise
    finally:
        _remove_if_exists(artifact_tmp_path)
        _remove_if_exists(manifest_tmp_path)
        _remove_if_exists(artifact_backup_path)
        _remove_if_exists(manifest_backup_path)


def _selected_method_replay_artifact_path(
    bundle: StrategyReplayBundle,
    *,
    cache_dir: str | Path,
) -> Path:
    safe_run = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in bundle.run_id)
    return Path(cache_dir) / f"{safe_run}.selected_method_replay.parquet"


def write_selected_method_replay_artifact_atomic(
    bundle: StrategyReplayBundle,
    *,
    artifact_path: str | Path | None = None,
    cache_dir: str | Path = SELECTED_METHOD_REPLAY_CACHE_DIR,
) -> dict[str, Path | str]:
    """Persist the selected-method replay output bundle with temp-file replacement."""

    output_path = Path(artifact_path) if artifact_path is not None else _selected_method_replay_artifact_path(bundle, cache_dir=cache_dir)
    _validate_selected_method_replay_artifact_path(output_path, cache_dir=cache_dir)
    artifact = selected_method_replay_bundle_to_frame(bundle)
    manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")
    manifest = {
        "artifact_type": SELECTED_METHOD_REPLAY_ARTIFACT_TYPE,
        "display_only": True,
        "canonical_market_data_write": False,
        "broker_order": False,
        "run_id": bundle.run_id,
        "source_id": bundle.run_metadata.source_id,
        "method_id": bundle.run_metadata.method_id,
        "run_metadata": _metadata_json_safe(bundle.run_metadata.__dict__),
        "row_count": int(len(artifact)),
        "row_counts": bundle.run_metadata.row_counts,
        "status_counts": bundle.run_metadata.status_counts,
        "date_window": bundle.run_metadata.date_window,
        "input_signatures": bundle.run_metadata.input_signatures,
        "controls_signature": bundle.run_metadata.controls_signature,
        "timing": bundle.run_metadata.timing,
    }
    manifest_text = json.dumps(_metadata_json_safe(manifest), indent=2, sort_keys=True, allow_nan=False) + "\n"
    artifact_tmp_path = _stage_parquet(output_path, artifact, index=False)
    manifest_tmp_path = _stage_text(manifest_path, manifest_text)
    _promote_selected_method_replay_bundle(
        artifact_tmp_path=artifact_tmp_path,
        artifact_path=output_path,
        manifest_tmp_path=manifest_tmp_path,
        manifest_path=manifest_path,
    )
    return {
        "artifact_path": output_path,
        "manifest_path": manifest_path,
        "run_id": bundle.run_id,
        "source_id": bundle.run_metadata.source_id,
    }


def _selected_replay_result_unavailable(
    reason: str,
    *,
    manifest: dict[str, Any] | None = None,
    artifact_path: Path | None = None,
    manifest_path: Path | None = None,
    elapsed_ms: float = 0.0,
    budget_policy: ReplayBudgetPolicy | None = None,
) -> SelectedMethodReplayResult:
    return SelectedMethodReplayResult(
        status="unavailable",
        reason=reason,
        bundle=None,
        manifest=manifest or {},
        artifact_path=artifact_path,
        manifest_path=manifest_path,
        elapsed_ms=round(float(elapsed_ms), 3),
        budget_policy=budget_policy or ReplayBudgetPolicy(),
    )


def _selected_replay_result_ok(
    bundle: StrategyReplayBundle,
    *,
    reason: str,
    manifest: dict[str, Any] | None = None,
    artifact_path: Path | None = None,
    manifest_path: Path | None = None,
    elapsed_ms: float = 0.0,
    budget_policy: ReplayBudgetPolicy | None = None,
) -> SelectedMethodReplayResult:
    return SelectedMethodReplayResult(
        status="ok",
        reason=reason,
        bundle=bundle,
        manifest=manifest or {},
        artifact_path=artifact_path,
        manifest_path=manifest_path,
        elapsed_ms=round(float(elapsed_ms), 3),
        budget_policy=budget_policy or ReplayBudgetPolicy(),
    )


def _required_manifest_field(manifest: dict[str, Any], field_name: str) -> tuple[bool, Any]:
    if field_name not in manifest:
        return False, None
    return True, manifest[field_name]


def _non_empty_manifest_identity(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _coerce_count_dict(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, int] = {}
    for key, raw in value.items():
        try:
            out[str(key)] = int(raw)
        except Exception:
            out[str(key)] = 0
    return out


def _coerce_nested_count_dict(value: Any) -> dict[str, dict[str, int]]:
    if not isinstance(value, dict):
        return {}
    return {str(key): _coerce_count_dict(raw) for key, raw in value.items()}


def _manifest_timing_elapsed_ms(manifest: dict[str, Any]) -> float:
    timing = manifest.get("timing")
    if not isinstance(timing, dict):
        timing = manifest.get("run_metadata", {}).get("timing") if isinstance(manifest.get("run_metadata"), dict) else {}
    try:
        elapsed = float(timing.get("elapsed_ms", 0.0)) if isinstance(timing, dict) else 0.0
    except Exception:
        return 0.0
    return elapsed if np.isfinite(elapsed) else float("inf")


def _validate_timing_payload(timing: Any) -> bool:
    if not isinstance(timing, dict):
        return False
    if "elapsed_ms" not in timing:
        return False
    try:
        elapsed = float(timing.get("elapsed_ms"))
    except Exception:
        return False
    return bool(np.isfinite(elapsed) and elapsed >= 0.0)


def _source_file_signatures_from_input_signatures(signatures: Any) -> list[Any]:
    out: list[Any] = []
    if not isinstance(signatures, (list, tuple)):
        return out
    for signature in signatures:
        if not isinstance(signature, dict):
            continue
        cache_signature = signature.get("cache_signature")
        if isinstance(cache_signature, dict) and "source_files" in cache_signature:
            source_files = cache_signature.get("source_files")
            if isinstance(source_files, (list, tuple)):
                out.extend(source_files)
    return _canonical_metadata(out)


def _expected_replay_date_window(
    *,
    start_date: Any = None,
    end_date: Any = None,
    as_of_range: Iterable[Any] | tuple[Any, Any] | None = None,
) -> dict[str, str | None]:
    replay_dates = _coerce_forward_walk_dates(
        as_of_range=as_of_range,
        start_date=start_date,
        end_date=end_date,
        prices=pd.DataFrame(),
    )
    return {
        "requested_start": _iso_or_none(start_date),
        "requested_end": _iso_or_none(end_date),
        "replay_start": None if not replay_dates else replay_dates[0].date().isoformat(),
        "replay_end": None if not replay_dates else replay_dates[-1].date().isoformat(),
    }


def _artifact_row_counts(frame: pd.DataFrame) -> dict[str, int]:
    if frame.empty or "row_type" not in frame.columns:
        return {
            "daily_portfolio": 0,
            "event_annotations": 0,
            "buy_sell_decisions": 0,
            "total": int(len(frame)),
        }
    row_type = frame["row_type"].astype(str)
    counts = {
        "daily_portfolio": int((row_type == "daily_portfolio").sum()),
        "event_annotations": int((row_type == "event_annotation").sum()),
        "buy_sell_decisions": int((row_type == "buy_sell_decision").sum()),
    }
    counts["total"] = int(sum(counts.values()))
    return counts


def _artifact_status_counts(frame: pd.DataFrame) -> dict[str, dict[str, int]]:
    row_type_map = {
        "daily_portfolio": "daily_portfolio",
        "event_annotation": "event_annotations",
        "buy_sell_decision": "buy_sell_decisions",
    }
    out: dict[str, dict[str, int]] = {
        "daily_portfolio": {"empty": 0},
        "event_annotations": {"empty": 0},
        "buy_sell_decisions": {"empty": 0},
    }
    if frame.empty or "row_type" not in frame.columns:
        return out
    for row_type, key in row_type_map.items():
        section = frame[frame["row_type"].astype(str) == row_type]
        out[key] = _status_counts(section)
    return out


def _metadata_from_manifest(manifest: dict[str, Any]) -> StrategyReplayRunMetadata:
    run_metadata = manifest.get("run_metadata") if isinstance(manifest.get("run_metadata"), dict) else {}
    date_window = manifest.get("date_window") if isinstance(manifest.get("date_window"), dict) else {}
    return StrategyReplayRunMetadata(
        run_id=str(manifest.get("run_id", "")),
        method_id=str(manifest.get("method_id", "")),
        source_id=str(manifest.get("source_id", "")),
        input_signatures=tuple(_canonical_metadata(manifest.get("input_signatures", ()))),
        date_window=_canonical_metadata(date_window),
        row_counts=_coerce_count_dict(manifest.get("row_counts")),
        status_counts=_coerce_nested_count_dict(manifest.get("status_counts")),
        timing=_canonical_metadata(manifest.get("timing", run_metadata.get("timing", {}))),
        controls_signature=_canonical_metadata(manifest.get("controls_signature", run_metadata.get("controls_signature", {}))),
        input_coverage_start=run_metadata.get("input_coverage_start") or date_window.get("input_coverage_start"),
        effective_start=run_metadata.get("effective_start") or date_window.get("replay_start"),
        coverage_warnings=tuple(run_metadata.get("coverage_warnings") or ()),
    )


def _bundle_from_selected_method_artifact(
    artifact: pd.DataFrame,
    manifest: dict[str, Any],
) -> StrategyReplayBundle:
    artifact = _hydrate_legacy_artifact_roles(artifact)
    row_type = artifact["row_type"].astype(str) if "row_type" in artifact.columns else pd.Series(dtype=object)
    replay = (
        artifact[row_type == "daily_portfolio"]
        .copy()
        .reindex(columns=REPLAY_COLUMNS)
        .reset_index(drop=True)
    )
    event_frame = (
        artifact[row_type == "event_annotation"]
        .copy()
        .reindex(columns=REPLAY_CONTEXT_COLUMNS)
        .reset_index(drop=True)
    )
    decision_frame = (
        artifact[row_type == "buy_sell_decision"]
        .copy()
        .reindex(columns=REPLAY_CONTEXT_COLUMNS)
        .reset_index(drop=True)
    )
    source_id = str(manifest.get("source_id", "selected_method_replay:unknown"))
    method_id = str(manifest.get("method_id", ""))
    event_context = StrategyReplayContext(
        context_type="event_annotations",
        frame=event_frame,
        status="empty" if event_frame.empty else "ok",
        reason="loaded_from_selected_method_replay_artifact",
        source=source_id,
    )
    decision_context = StrategyReplayContext(
        context_type="decision_context",
        frame=decision_frame,
        status="empty" if decision_frame.empty else "ok",
        reason="loaded_from_selected_method_replay_artifact",
        source=source_id,
    )
    metadata = _metadata_from_manifest(manifest)
    if not metadata.method_id and method_id:
        metadata = StrategyReplayRunMetadata(
            run_id=metadata.run_id,
            method_id=method_id,
            source_id=metadata.source_id,
            input_signatures=metadata.input_signatures,
            date_window=metadata.date_window,
            row_counts=metadata.row_counts,
            status_counts=metadata.status_counts,
            timing=metadata.timing,
            controls_signature=metadata.controls_signature,
            input_coverage_start=metadata.input_coverage_start,
            effective_start=metadata.effective_start,
            coverage_warnings=metadata.coverage_warnings,
        )
    return StrategyReplayBundle(
        replay=replay,
        event_context=event_context,
        decision_context=decision_context,
        run_metadata=metadata,
    )


def _validate_manifest_bundle_fields(manifest: dict[str, Any]) -> str | None:
    required_fields = (
        "artifact_type",
        "run_id",
        "source_id",
        "method_id",
        "run_metadata",
        "row_count",
        "row_counts",
        "status_counts",
        "date_window",
        "input_signatures",
        "controls_signature",
        "timing",
    )
    for field_name in required_fields:
        present, _value = _required_manifest_field(manifest, field_name)
        if not present:
            return f"manifest_field_missing:{field_name}"
    for field_name in ("run_id", "source_id", "method_id"):
        if not _non_empty_manifest_identity(manifest.get(field_name)):
            return f"manifest_identity_blank:{field_name}"
    if manifest.get("artifact_type") != SELECTED_METHOD_REPLAY_ARTIFACT_TYPE:
        return "artifact_type_mismatch"
    if manifest.get("display_only") is not True:
        return "manifest_display_only_mismatch"
    if manifest.get("canonical_market_data_write") is not False:
        return "manifest_canonical_write_mismatch"
    if manifest.get("broker_order") is not False:
        return "manifest_broker_order_mismatch"
    run_metadata = manifest.get("run_metadata")
    if not isinstance(run_metadata, dict):
        return "manifest_run_metadata_invalid"
    if not _validate_timing_payload(manifest.get("timing")):
        return "manifest_timing_invalid"
    if not _validate_timing_payload(run_metadata.get("timing")):
        return "manifest_run_metadata_mismatch:timing"
    for field_name in ("run_id", "source_id", "method_id", "row_counts", "status_counts", "date_window", "timing"):
        if _canonical_metadata(run_metadata.get(field_name)) != _canonical_metadata(manifest.get(field_name)):
            return f"manifest_run_metadata_mismatch:{field_name}"
    if _canonical_metadata(run_metadata.get("input_signatures")) != _canonical_metadata(manifest.get("input_signatures")):
        return "manifest_run_metadata_mismatch:input_signatures"
    if _canonical_metadata(run_metadata.get("controls_signature", {})) != _canonical_metadata(manifest.get("controls_signature")):
        return "manifest_run_metadata_mismatch:controls_signature"
    return None


def _validate_artifact_against_manifest(
    artifact: pd.DataFrame,
    manifest: dict[str, Any],
) -> str | None:
    columns = list(artifact.columns)
    if columns == LEGACY_SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS:
        artifact = _hydrate_legacy_artifact_roles(artifact)
    elif columns != SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS:
        return "schema_mismatch"
    try:
        manifest_row_count = int(manifest.get("row_count"))
    except Exception:
        return "manifest_row_count_invalid"
    if len(artifact) != manifest_row_count:
        return "manifest_parquet_mismatch:row_count"
    if not artifact.empty:
        expected_run_id = str(manifest.get("run_id"))
        expected_source_id = str(manifest.get("source_id"))
        expected_method_id = str(manifest.get("method_id"))
        if artifact["artifact_scope"].isna().any() or not artifact["artifact_scope"].astype(str).eq(SELECTED_METHOD_REPLAY_ARTIFACT_TYPE).all():
            return "manifest_parquet_mismatch:artifact_scope"
        if artifact["run_id"].isna().any() or not artifact["run_id"].astype(str).eq(expected_run_id).all():
            return "manifest_parquet_mismatch:run_id"
        if artifact["source_id"].isna().any() or not artifact["source_id"].astype(str).eq(expected_source_id).all():
            return "manifest_parquet_mismatch:source_id"
        if artifact["method"].isna().any() or not artifact["method"].astype(str).eq(expected_method_id).all():
            return "manifest_parquet_mismatch:method_id"
        allowed_row_types = {"daily_portfolio", "event_annotation", "buy_sell_decision"}
        if artifact["row_type"].isna().any() or not artifact["row_type"].astype(str).isin(allowed_row_types).all():
            return "manifest_parquet_mismatch:row_type"
    observed_row_counts = _artifact_row_counts(artifact)
    if _canonical_metadata(observed_row_counts) != _canonical_metadata(manifest.get("row_counts")):
        return "manifest_parquet_mismatch:row_counts"
    observed_status_counts = _artifact_status_counts(artifact)
    if _canonical_metadata(observed_status_counts) != _canonical_metadata(manifest.get("status_counts")):
        return "manifest_parquet_mismatch:status_counts"

    daily = artifact[artifact["row_type"].astype(str) == "daily_portfolio"] if not artifact.empty else artifact
    observed_window = _date_window_from_replay(daily)
    date_window = manifest.get("date_window") if isinstance(manifest.get("date_window"), dict) else {}
    for key in ("replay_start", "replay_end"):
        if observed_window.get(key) != date_window.get(key):
            return f"manifest_parquet_mismatch:date_window.{key}"
    return None


def _validate_replay_context_match(
    manifest: dict[str, Any],
    *,
    method: OptimizationMethod | str,
    controls: Any = None,
    start_date: Any = None,
    end_date: Any = None,
    as_of_range: Iterable[Any] | tuple[Any, Any] | None = None,
    expected_date_window: dict[str, Any] | None = None,
    input_signatures: Iterable[dict[str, Any]] | None = None,
    source_file_signatures: Iterable[Any] | None = None,
    run_id: str | None = None,
    source_id: str | None = None,
) -> str | None:
    try:
        selected_method = _coerce_method(method)
        accepted_method_ids = {selected_method.value, selected_method.name.lower(), str(method)}
    except Exception:
        accepted_method_ids = {str(method)}
    if str(manifest.get("method_id")) not in accepted_method_ids:
        return "method_mismatch"
    if run_id is not None and str(manifest.get("run_id")) != str(run_id):
        return "run_id_mismatch"
    if source_id is not None and str(manifest.get("source_id")) != str(source_id):
        return "source_id_mismatch"

    expected_controls = _canonical_metadata(_controls_signature_payload(controls))
    if _canonical_metadata(manifest.get("controls_signature")) != expected_controls:
        return "controls_signature_mismatch"

    if expected_date_window is None:
        expected_date_window = {
            "requested_start": _iso_or_none(start_date),
            "requested_end": _iso_or_none(end_date),
            "replay_start": None,
            "replay_end": None,
        }
        if as_of_range is not None:
            expected_date_window.update(
                _expected_replay_date_window(
                    start_date=start_date,
                    end_date=end_date,
                    as_of_range=as_of_range,
                )
            )
    manifest_window = manifest.get("date_window") if isinstance(manifest.get("date_window"), dict) else {}
    for key, expected_value in expected_date_window.items():
        if expected_value is not None and manifest_window.get(key) != expected_value:
            return f"date_window_mismatch:{key}"

    if input_signatures is not None:
        expected_signatures = _canonical_metadata(tuple(input_signatures))
        manifest_signatures = _canonical_metadata(tuple(manifest.get("input_signatures", ())))
        if manifest_signatures != expected_signatures:
            return "input_signature_mismatch"
    if source_file_signatures is not None:
        expected_sources = _canonical_metadata(list(source_file_signatures))
        manifest_sources = _source_file_signatures_from_input_signatures(manifest.get("input_signatures"))
        if manifest_sources != expected_sources:
            return "source_file_signature_mismatch"
    return None


def _validate_replay_budget(
    *,
    row_count: int,
    date_count: int,
    elapsed_ms: float,
    cache_read_elapsed_seconds: float | None,
    budget_policy: ReplayBudgetPolicy,
    mode: str,
) -> str | None:
    if int(row_count) > int(budget_policy.max_rows):
        return "budget_exceeded:max_rows"
    if int(date_count) > int(budget_policy.max_dates):
        return "budget_exceeded:max_dates"
    if float(elapsed_ms) > float(budget_policy.max_elapsed_ms):
        return "budget_exceeded:max_elapsed_ms"
    if cache_read_elapsed_seconds is not None and mode == "read":
        if float(cache_read_elapsed_seconds) > float(budget_policy.rerun_cache_max_seconds):
            return "budget_exceeded:rerun_cache_seconds"
    if cache_read_elapsed_seconds is not None and mode == "build":
        if float(cache_read_elapsed_seconds) > float(budget_policy.cold_start_max_seconds):
            return "budget_exceeded:cold_start_seconds"
    return None


def read_selected_method_replay_artifact(
    artifact_path: str | Path,
    *,
    method: OptimizationMethod | str,
    controls: Any = None,
    start_date: Any = None,
    end_date: Any = None,
    as_of_range: Iterable[Any] | tuple[Any, Any] | None = None,
    expected_date_window: dict[str, Any] | None = None,
    input_signatures: Iterable[dict[str, Any]] | None = None,
    source_file_signatures: Iterable[Any] | None = None,
    run_id: str | None = None,
    source_id: str | None = None,
    budget_policy: ReplayBudgetPolicy | None = None,
    cache_dir: str | Path = SELECTED_METHOD_REPLAY_CACHE_DIR,
) -> SelectedMethodReplayResult:
    """Read a saved selected-method replay artifact and validate freshness.

    Invalid, stale, or over-budget bundles fail closed by returning
    ``available == False``. Callers must not reuse a prior replay bundle when
    this result is unavailable.
    """

    policy = budget_policy or ReplayBudgetPolicy()
    perf_start = time.perf_counter()
    output_path = Path(artifact_path)
    manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")

    def _fail(reason: str, manifest: dict[str, Any] | None = None) -> SelectedMethodReplayResult:
        return _selected_replay_result_unavailable(
            reason,
            manifest=manifest,
            artifact_path=output_path,
            manifest_path=manifest_path,
            elapsed_ms=(time.perf_counter() - perf_start) * 1000.0,
            budget_policy=policy,
        )

    try:
        _validate_selected_method_replay_artifact_path(output_path, cache_dir=cache_dir)
    except Exception as exc:
        return _fail(f"artifact_path_invalid:{type(exc).__name__}")
    if not output_path.exists():
        return _fail("artifact_missing")
    if not manifest_path.exists():
        return _fail("manifest_missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return _fail(f"manifest_read_error:{type(exc).__name__}")
    if not isinstance(manifest, dict):
        return _fail("manifest_invalid", {})

    reason = _validate_manifest_bundle_fields(manifest)
    if reason is not None:
        return _fail(reason, manifest)

    try:
        row_count = int(manifest.get("row_count"))
    except Exception:
        return _fail("manifest_row_count_invalid", manifest)
    reason = _validate_replay_budget(
        row_count=row_count,
        date_count=0,
        elapsed_ms=_manifest_timing_elapsed_ms(manifest),
        cache_read_elapsed_seconds=None,
        budget_policy=policy,
        mode="read",
    )
    if reason is not None and reason != "budget_exceeded:max_dates":
        return _fail(reason, manifest)

    reason = _validate_replay_context_match(
        manifest,
        method=method,
        controls=controls,
        start_date=start_date,
        end_date=end_date,
        as_of_range=as_of_range,
        expected_date_window=expected_date_window,
        input_signatures=input_signatures,
        source_file_signatures=source_file_signatures,
        run_id=run_id,
        source_id=source_id,
    )
    if reason is not None:
        return _fail(reason, manifest)

    try:
        artifact = pd.read_parquet(output_path)
    except Exception as exc:
        return _fail(f"parquet_read_error:{type(exc).__name__}", manifest)

    reason = _validate_artifact_against_manifest(artifact, manifest)
    if reason is not None:
        return _fail(reason, manifest)
    artifact = _hydrate_legacy_artifact_roles(artifact)

    if artifact.empty:
        date_count = 0
    else:
        daily = artifact[artifact["row_type"].astype(str) == "daily_portfolio"]
        date_count = int(pd.to_datetime(daily.get("date", pd.Series(dtype=object)), errors="coerce").dropna().nunique())
    reason = _validate_replay_budget(
        row_count=len(artifact),
        date_count=date_count,
        elapsed_ms=_manifest_timing_elapsed_ms(manifest),
        cache_read_elapsed_seconds=time.perf_counter() - perf_start,
        budget_policy=policy,
        mode="read",
    )
    if reason is not None:
        return _fail(reason, manifest)

    bundle = _bundle_from_selected_method_artifact(artifact, manifest)
    return _selected_replay_result_ok(
        bundle,
        reason="loaded_from_selected_method_replay_artifact",
        manifest=manifest,
        artifact_path=output_path,
        manifest_path=manifest_path,
        elapsed_ms=(time.perf_counter() - perf_start) * 1000.0,
        budget_policy=policy,
    )


def build_selected_method_replay_with_budget(
    method: OptimizationMethod | str,
    controls: Any,
    prices: pd.DataFrame | StrategyReplayInputs | Iterable[StrategyReplayInputs] | None,
    ticker_map: dict | None = None,
    sector_map: dict | None = None,
    as_of_range: Iterable[Any] | tuple[Any, Any] | None = None,
    *,
    event_context: pd.DataFrame | None = None,
    decision_context: pd.DataFrame | None = None,
    input_loader: Callable[..., StrategyReplayInputs] | None = None,
    start_date: Any = None,
    end_date: Any = None,
    run_id: str | None = None,
    source_id: str | None = None,
    coverage_plan: list[ReplayDateCoverage] | None = None,
    budget_policy: ReplayBudgetPolicy | None = None,
) -> SelectedMethodReplayResult:
    """Build selected-method replay with explicit fail-closed budget checks."""

    policy = budget_policy or ReplayBudgetPolicy()
    perf_start = time.perf_counter()

    def _fail(reason: str) -> SelectedMethodReplayResult:
        return _selected_replay_result_unavailable(
            reason,
            elapsed_ms=(time.perf_counter() - perf_start) * 1000.0,
            budget_policy=policy,
        )

    replay_dates = _coerce_forward_walk_dates(
        as_of_range=as_of_range,
        start_date=start_date,
        end_date=end_date,
        prices=prices,
    )
    if replay_dates and len(replay_dates) > int(policy.max_dates):
        return _fail("budget_exceeded:max_dates")

    try:
        bundle = build_selected_method_replay(
            method=method,
            controls=controls,
            prices=prices,
            ticker_map=ticker_map,
            sector_map=sector_map,
            as_of_range=as_of_range,
            event_context=event_context,
            decision_context=decision_context,
            input_loader=input_loader,
            start_date=start_date,
            end_date=end_date,
            run_id=run_id,
            source_id=source_id,
            coverage_plan=coverage_plan,
        )
    except Exception as exc:
        return _fail(f"build_exception:{type(exc).__name__}")

    build_elapsed_seconds = time.perf_counter() - perf_start
    replay_frame = bundle.replay if isinstance(bundle.replay, pd.DataFrame) else pd.DataFrame()
    if replay_frame.empty:
        date_count = 0
    else:
        date_count = int(pd.to_datetime(replay_frame.get("date", pd.Series(dtype=object)), errors="coerce").dropna().nunique())
    reason = _validate_replay_budget(
        row_count=len(replay_frame) + len(bundle.event_rows) + len(bundle.decision_rows),
        date_count=date_count,
        elapsed_ms=float(bundle.run_metadata.timing.get("elapsed_ms", 0.0)),
        cache_read_elapsed_seconds=build_elapsed_seconds,
        budget_policy=policy,
        mode="build",
    )
    if reason is not None:
        return _fail(reason)
    return _selected_replay_result_ok(
        bundle,
        reason="built_selected_method_replay",
        elapsed_ms=build_elapsed_seconds * 1000.0,
        budget_policy=policy,
    )
