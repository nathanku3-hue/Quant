"""Same-engine shadow evaluation for the Leningrad cascade challenger."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from typing import Any, Iterable

import numpy as np
import pandas as pd

from core.engine import run_simulation
from research.metrics import build_equity_curve, max_drawdown
from strategies.financial_cascade import (
    CLAIM_BOUNDARY,
    FinancialCascadeObservation,
    FinancialCascadePolicy,
    apply_financial_cascade_cap,
    build_financial_cascade_overlay,
)


@dataclass(frozen=True, slots=True)
class StressWindow:
    window_id: str
    start_date: str
    end_date: str

    def __post_init__(self) -> None:
        if not self.window_id.strip():
            raise ValueError("CASCADE_WINDOW_ID_REQUIRED")
        start = pd.Timestamp(self.start_date)
        end = pd.Timestamp(self.end_date)
        if start.tzinfo is not None or end.tzinfo is not None:
            raise ValueError("CASCADE_WINDOW_DATES_MUST_BE_NAIVE")
        if start != start.normalize() or end != end.normalize() or end < start:
            raise ValueError("CASCADE_WINDOW_RANGE_INVALID")
        if self.start_date != start.date().isoformat() or self.end_date != end.date().isoformat():
            raise ValueError("CASCADE_WINDOW_DATE_NOT_CANONICAL")


@dataclass(frozen=True, slots=True)
class CascadePromotionThresholds:
    min_independent_windows: int = 2
    min_window_observations: int = 5
    min_relative_max_drawdown_improvement: float = 0.15
    min_expected_shortfall_improvement: float = 0.10
    max_annualized_net_alpha_drag: float = 0.01
    max_relative_turnover_increase: float = 0.20
    expected_shortfall_confidence: float = 0.95

    def __post_init__(self) -> None:
        if self.min_independent_windows < 2:
            raise ValueError("CASCADE_MIN_WINDOWS_MUST_BE_AT_LEAST_TWO")
        if self.min_window_observations < 2:
            raise ValueError("CASCADE_MIN_WINDOW_OBSERVATIONS_INVALID")
        for field_name in (
            "min_relative_max_drawdown_improvement",
            "min_expected_shortfall_improvement",
            "max_annualized_net_alpha_drag",
            "max_relative_turnover_increase",
        ):
            value = float(getattr(self, field_name))
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"CASCADE_{field_name.upper()}_INVALID")
        if not 0.5 < self.expected_shortfall_confidence < 1.0:
            raise ValueError("CASCADE_EXPECTED_SHORTFALL_CONFIDENCE_INVALID")


def expected_shortfall(
    net_returns: pd.Series,
    *,
    confidence: float = 0.95,
) -> float:
    """Return positive mean loss in the worst ``1-confidence`` tail."""

    if not 0.5 < confidence < 1.0:
        raise ValueError("CASCADE_EXPECTED_SHORTFALL_CONFIDENCE_INVALID")
    returns = pd.to_numeric(net_returns, errors="coerce").dropna()
    if returns.empty:
        return 0.0
    losses = -returns.astype(float)
    threshold = float(losses.quantile(confidence, interpolation="higher"))
    tail = losses[losses >= threshold]
    return max(0.0, float(tail.mean())) if not tail.empty else 0.0


def _relative_improvement(baseline: float, challenger: float) -> float | None:
    if not np.isfinite(baseline) or not np.isfinite(challenger) or baseline <= 0.0:
        return None
    return float((baseline - challenger) / baseline)


def _canonical_digest(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(raw).hexdigest()


def _frame_digest(frame: pd.DataFrame) -> str:
    normalized = frame.copy()
    normalized.index = [pd.Timestamp(value).isoformat() for value in normalized.index]
    value = {
        "index": list(normalized.index),
        "columns": [str(column) for column in normalized.columns],
        "data": [
            [format(float(item), ".17g") for item in row]
            for row in normalized.to_numpy(dtype=float)
        ],
    }
    return _canonical_digest(value)


def _validate_inputs(target_weights: pd.DataFrame, returns_df: pd.DataFrame) -> None:
    if not isinstance(target_weights, pd.DataFrame) or not isinstance(returns_df, pd.DataFrame):
        raise TypeError("CASCADE_WEIGHTS_AND_RETURNS_DATAFRAMES_REQUIRED")
    if target_weights.empty or returns_df.empty:
        raise ValueError("CASCADE_WEIGHTS_AND_RETURNS_REQUIRED")
    if not target_weights.index.equals(returns_df.index):
        raise ValueError("CASCADE_WEIGHT_RETURN_INDEX_MISMATCH")
    if not target_weights.columns.equals(returns_df.columns):
        raise ValueError("CASCADE_WEIGHT_RETURN_COLUMN_MISMATCH")
    dates = pd.DatetimeIndex(target_weights.index)
    if dates.tz is not None or dates.hasnans or not dates.is_monotonic_increasing or dates.has_duplicates:
        raise ValueError("CASCADE_BACKTEST_INDEX_MUST_BE_SORTED_UNIQUE_NAIVE_DATES")
    for frame, code in (
        (target_weights, "CASCADE_TARGET_WEIGHTS_NON_FINITE"),
        (returns_df, "CASCADE_RETURNS_NON_FINITE"),
    ):
        numeric = frame.apply(pd.to_numeric, errors="coerce")
        if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy()).all():
            raise ValueError(code)


def _validate_windows(
    windows: Iterable[StressWindow],
    index: pd.DatetimeIndex,
    *,
    min_count: int,
) -> tuple[StressWindow, ...]:
    values = tuple(windows)
    if len({window.window_id for window in values}) != len(values):
        raise ValueError("CASCADE_DUPLICATE_WINDOW_ID")
    ordered = sorted(values, key=lambda row: (row.start_date, row.end_date, row.window_id))
    prior_end: pd.Timestamp | None = None
    for window in ordered:
        start = pd.Timestamp(window.start_date)
        end = pd.Timestamp(window.end_date)
        if start < index.min() or end > index.max():
            raise ValueError("CASCADE_WINDOW_OUTSIDE_BACKTEST")
        if prior_end is not None and start <= prior_end:
            raise ValueError("CASCADE_STRESS_WINDOWS_MUST_NOT_OVERLAP")
        prior_end = end
    return tuple(ordered)


def _window_row(
    *,
    window: StressWindow,
    baseline: pd.DataFrame,
    challenger: pd.DataFrame,
    overlay: pd.DataFrame,
    thresholds: CascadePromotionThresholds,
) -> dict[str, Any]:
    start = pd.Timestamp(window.start_date)
    end = pd.Timestamp(window.end_date)
    mask = (baseline.index >= start) & (baseline.index <= end)
    baseline_slice = baseline.loc[mask]
    challenger_slice = challenger.loc[mask]
    overlay_slice = overlay.loc[mask]
    observation_count = int(mask.sum())

    baseline_mdd = abs(max_drawdown(build_equity_curve(baseline_slice["net_ret"])))
    challenger_mdd = abs(max_drawdown(build_equity_curve(challenger_slice["net_ret"])))
    mdd_improvement = _relative_improvement(baseline_mdd, challenger_mdd)

    baseline_es = expected_shortfall(
        baseline_slice["net_ret"], confidence=thresholds.expected_shortfall_confidence
    )
    challenger_es = expected_shortfall(
        challenger_slice["net_ret"], confidence=thresholds.expected_shortfall_confidence
    )
    es_improvement = _relative_improvement(baseline_es, challenger_es)

    bundle_ids = tuple(
        sorted(
            {
                str(value)
                for value in overlay_slice["bundle_identity"].dropna().tolist()
                if str(value)
            }
        )
    )
    state_counts = {
        str(key): int(value)
        for key, value in overlay_slice["cascade_state"].value_counts().sort_index().items()
    }
    enough_rows = observation_count >= thresholds.min_window_observations
    has_cascade_evidence = bool(bundle_ids)
    mdd_pass = (
        mdd_improvement is not None
        and mdd_improvement >= thresholds.min_relative_max_drawdown_improvement
    )
    es_pass = (
        es_improvement is not None
        and es_improvement >= thresholds.min_expected_shortfall_improvement
    )
    return {
        "window_id": window.window_id,
        "start_date": window.start_date,
        "end_date": window.end_date,
        "observation_count": observation_count,
        "bundle_identities": list(bundle_ids),
        "cascade_state_counts": state_counts,
        "baseline_max_drawdown_abs": baseline_mdd,
        "challenger_max_drawdown_abs": challenger_mdd,
        "relative_max_drawdown_improvement": mdd_improvement,
        "baseline_expected_shortfall": baseline_es,
        "challenger_expected_shortfall": challenger_es,
        "relative_expected_shortfall_improvement": es_improvement,
        "enough_rows": enough_rows,
        "has_cascade_evidence": has_cascade_evidence,
        "max_drawdown_gate_pass": bool(mdd_pass),
        "expected_shortfall_gate_pass": bool(es_pass),
        "window_pass": bool(enough_rows and has_cascade_evidence and mdd_pass and es_pass),
    }


def run_financial_cascade_shadow(
    *,
    target_weights: pd.DataFrame,
    returns_df: pd.DataFrame,
    observations: Iterable[FinancialCascadeObservation],
    stress_windows: Iterable[StressWindow],
    cost_rate: float = 0.0010,
    policy: FinancialCascadePolicy | None = None,
    thresholds: CascadePromotionThresholds | None = None,
) -> dict[str, Any]:
    """Compare baseline and cascade-cap weights through the same Quant engine."""

    _validate_inputs(target_weights, returns_df)
    if not np.isfinite(cost_rate) or cost_rate < 0.0:
        raise ValueError("CASCADE_COST_RATE_INVALID")
    active_policy = policy or FinancialCascadePolicy()
    active_thresholds = thresholds or CascadePromotionThresholds()
    observation_values = tuple(observations)
    windows = _validate_windows(
        stress_windows,
        pd.DatetimeIndex(target_weights.index),
        min_count=active_thresholds.min_independent_windows,
    )

    overlay = build_financial_cascade_overlay(
        observation_values,
        target_weights.index,
        policy=active_policy,
    )
    capped = apply_financial_cascade_cap(target_weights, overlay)

    baseline_sim = run_simulation(
        target_weights=target_weights,
        returns_df=returns_df,
        cost_bps=float(cost_rate),
        strict_missing_returns=True,
    )
    challenger_sim = run_simulation(
        target_weights=capped.target_weights,
        returns_df=returns_df,
        cost_bps=float(cost_rate),
        strict_missing_returns=True,
    )
    replay_sim = run_simulation(
        target_weights=capped.target_weights.copy(),
        returns_df=returns_df.copy(),
        cost_bps=float(cost_rate),
        strict_missing_returns=True,
    )
    exact_replay_pass = bool(
        challenger_sim.equals(replay_sim)
        and _frame_digest(challenger_sim) == _frame_digest(replay_sim)
        and _frame_digest(capped.target_weights)
        == _frame_digest(apply_financial_cascade_cap(target_weights, overlay).target_weights)
    )

    window_rows = [
        _window_row(
            window=window,
            baseline=baseline_sim,
            challenger=challenger_sim,
            overlay=overlay,
            thresholds=active_thresholds,
        )
        for window in windows
    ]
    distinct_window_bundle_ids = {
        bundle_id
        for row in window_rows
        for bundle_id in row["bundle_identities"]
    }
    independent_window_gate = bool(
        len(window_rows) >= active_thresholds.min_independent_windows
        and len(distinct_window_bundle_ids) >= active_thresholds.min_independent_windows
        and all(bool(row["enough_rows"] and row["has_cascade_evidence"]) for row in window_rows)
    )

    baseline_ann = float(pd.to_numeric(baseline_sim["net_ret"]).mean() * 252.0)
    challenger_ann = float(pd.to_numeric(challenger_sim["net_ret"]).mean() * 252.0)
    annualized_net_alpha_drag = max(0.0, baseline_ann - challenger_ann)
    alpha_drag_gate = bool(
        annualized_net_alpha_drag <= active_thresholds.max_annualized_net_alpha_drag
    )

    baseline_turnover = float(pd.to_numeric(baseline_sim["turnover"]).sum())
    challenger_turnover = float(pd.to_numeric(challenger_sim["turnover"]).sum())
    if baseline_turnover > 0.0:
        relative_turnover_increase = max(
            0.0, (challenger_turnover - baseline_turnover) / baseline_turnover
        )
    elif challenger_turnover == 0.0:
        relative_turnover_increase = 0.0
    else:
        relative_turnover_increase = math.inf
    turnover_gate = bool(
        np.isfinite(relative_turnover_increase)
        and relative_turnover_increase
        <= active_thresholds.max_relative_turnover_increase
    )

    pit_lineage_gate = bool(
        observation_values
        and all(
            observation.bundle.bundle_identity
            and observation.bundle.scenario_identity
            and observation.effective_date
            and observation.source_as_of_utc
            and observation.available_at_utc
            for observation in observation_values
        )
    )
    performance_gates = bool(window_rows and all(row["window_pass"] for row in window_rows))

    if not independent_window_gate or not pit_lineage_gate:
        decision = "DEFER_INSUFFICIENT_EVIDENCE"
    elif (
        performance_gates
        and alpha_drag_gate
        and turnover_gate
        and exact_replay_pass
    ):
        decision = "PROMOTE_TO_LATER_PORTFOLIO_PREVIEW_CHALLENGER"
    else:
        decision = "KILL_CHALLENGER"

    report_body: dict[str, Any] = {
        "schema_version": "quant-financial-cascade-shadow-report-v1",
        "module_id": "GV_FINANCIAL_CASCADE_SHADOW",
        "claim_boundary": CLAIM_BOUNDARY,
        "decision": decision,
        "capital_authority": False,
        "security_selection_changed": False,
        "entry_exit_logic_changed": False,
        "intervention_ranking_used_for_trades": False,
        "same_engine": "core.engine.run_simulation",
        "cost_rate": float(cost_rate),
        "policy": {
            "severe_default_fraction": str(active_policy.severe_default_fraction),
            "severe_unpaid_fraction": str(active_policy.severe_unpaid_fraction),
            "watch_gross_cap": active_policy.watch_gross_cap,
            "severe_gross_cap": active_policy.severe_gross_cap,
        },
        "thresholds": {
            "min_independent_windows": active_thresholds.min_independent_windows,
            "min_window_observations": active_thresholds.min_window_observations,
            "min_relative_max_drawdown_improvement": active_thresholds.min_relative_max_drawdown_improvement,
            "min_expected_shortfall_improvement": active_thresholds.min_expected_shortfall_improvement,
            "max_annualized_net_alpha_drag": active_thresholds.max_annualized_net_alpha_drag,
            "max_relative_turnover_increase": active_thresholds.max_relative_turnover_increase,
            "expected_shortfall_confidence": active_thresholds.expected_shortfall_confidence,
        },
        "window_results": window_rows,
        "aggregate": {
            "distinct_window_bundle_count": len(distinct_window_bundle_ids),
            "baseline_annualized_mean_net_return": baseline_ann,
            "challenger_annualized_mean_net_return": challenger_ann,
            "annualized_net_alpha_drag": annualized_net_alpha_drag,
            "baseline_total_turnover": baseline_turnover,
            "challenger_total_turnover": challenger_turnover,
            "relative_turnover_increase": (
                relative_turnover_increase
                if np.isfinite(relative_turnover_increase)
                else None
            ),
        },
        "gates": {
            "independent_windows": independent_window_gate,
            "pit_lineage": pit_lineage_gate,
            "all_window_drawdown_and_expected_shortfall": performance_gates,
            "annualized_net_alpha_drag": alpha_drag_gate,
            "bounded_turnover_increase": turnover_gate,
            "exact_replay": exact_replay_pass,
        },
        "replay": {
            "challenger_weights_digest": _frame_digest(capped.target_weights),
            "challenger_simulation_digest": _frame_digest(challenger_sim),
            "exact_replay": exact_replay_pass,
        },
    }
    report_body["report_identity"] = _canonical_digest(report_body)
    return report_body
