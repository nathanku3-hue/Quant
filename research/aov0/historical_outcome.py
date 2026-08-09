"""Outcome-side evaluation for one frozen historical AOV checkpoint.

This module is intentionally separate from ``historical_checkpoint``.  A
checkpoint can be built and hash-verified without importing this module or
opening any post-target returns.  When an admitted historical outcome period is
opened, the three frozen risky arms are evaluated through the repository's
canonical ``core.engine.run_simulation`` path.

Clock-v3 timing is preserved: a target selected at decision close is placed on
the historical evaluation-close row, and the engine's mandatory ``shift(1)``
therefore first exposes risk to the following close-to-close return interval.
No return whose left endpoint predates evaluation start is credited.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from core import engine
from core.gv_fs0_canonical import domain_hash
from research.aov0.ciq_market import DATE_ALIASES, _parse_market_raw
from research.aov0.contracts import DEFAULT_CONTRACT
from research.benchmarks import build_economic_cash_frames, build_pit_equal_weight_benchmark
from research.aov0.historical_checkpoint import (
    HistoricalAOVDecisionCheckpoint,
    HistoricalCheckpointError,
    verify_historical_aov_decision_checkpoint,
)


OUTCOME_SCHEMA = "aov0_historical_pit_checkpoint_outcome_v1"
OUTCOME_AUTHORITY = "HISTORICAL_PIT_CHECKPOINT_OUTCOME_ONLY_NOT_PROSPECTIVE_AUTHORITY"
NY_TZ = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class HistoricalAOVOutcome:
    outcome_id: str
    payload: Mapping[str, Any]
    simulations: Mapping[str, pd.DataFrame]


class HistoricalOutcomeError(ValueError):
    """Fail-closed historical outcome-evaluation error."""


def evaluate_historical_aov_outcome(
    *,
    checkpoint: HistoricalAOVDecisionCheckpoint,
    outcome_market_raw: pd.DataFrame,
    evaluation_start: str | pd.Timestamp,
    outcome_open_not_before: str | pd.Timestamp,
    turnover_cost_rate: float,
    outcome_source_sha256: str,
    economic_cash_returns: pd.Series,
    economic_cash_source_sha256: str,
) -> HistoricalAOVOutcome:
    """Evaluate the exact five-arm frozen AOV historical sleeve."""

    verify_historical_aov_decision_checkpoint(checkpoint)
    evaluation = _aware_utc(evaluation_start, field="evaluation_start")
    maturity = _aware_utc(outcome_open_not_before, field="outcome_open_not_before")
    expected_maturity = evaluation + pd.Timedelta(days=DEFAULT_CONTRACT.sleeve_horizon_calendar_days)
    if maturity != expected_maturity:
        raise HistoricalOutcomeError("aov0_historical_outcome_maturity_contract_mismatch")
    if not np.isfinite(float(turnover_cost_rate)) or float(turnover_cost_rate) < 0.0:
        raise HistoricalOutcomeError("aov0_historical_outcome_turnover_cost_invalid")
    _sha256_text(outcome_source_sha256, field="outcome_source")
    _sha256_text(economic_cash_source_sha256, field="economic_cash_source")

    target = pd.Timestamp(str(checkpoint.manifest["target_date"])).normalize()
    evaluation_date = pd.Timestamp(evaluation.tz_convert(NY_TZ).date())
    maturity_date = pd.Timestamp(maturity.tz_convert(NY_TZ).date())
    if evaluation_date <= target:
        raise HistoricalOutcomeError("aov0_historical_outcome_evaluation_not_after_target")
    if not isinstance(outcome_market_raw, pd.DataFrame) or outcome_market_raw.empty:
        raise HistoricalOutcomeError("aov0_historical_outcome_market_required")
    _reject_pre_or_target_rows(outcome_market_raw, target=target)

    normalized = _parse_market_raw(outcome_market_raw, checkpoint.market_slice.security_map)
    normalized = normalized.loc[
        normalized["date"].ge(evaluation_date) & normalized["date"].le(maturity_date)
    ].copy()
    if normalized.empty:
        raise HistoricalOutcomeError("aov0_historical_outcome_horizon_empty")
    calendar = pd.DatetimeIndex(sorted(normalized["date"].drop_duplicates())).normalize()
    if evaluation_date not in calendar:
        raise HistoricalOutcomeError("aov0_historical_outcome_evaluation_close_missing")
    if len(calendar) < 2:
        raise HistoricalOutcomeError("aov0_historical_outcome_no_post_evaluation_interval")

    returns = normalized.pivot(index="date", columns="security_id", values="total_return")
    returns = returns.reindex(index=calendar, columns=checkpoint.dag.rule100.columns)
    returns.index = pd.DatetimeIndex(returns.index).normalize()

    eligible_assets = tuple(str(column) for column in checkpoint.dag.rule100.columns)
    pit_equal_weight = build_pit_equal_weight_benchmark(
        calendar,
        checkpoint.dag.rule100.columns,
        lambda _date: eligible_assets,
        rebalance_dates=pd.DatetimeIndex([calendar[0]]),
    )
    economic_cash_weights, economic_cash_frame = build_economic_cash_frames(
        calendar,
        economic_cash_returns,
    )
    target_vectors = {
        "rule100": checkpoint.dag.rule100.iloc[0].astype(float),
        "parent": checkpoint.dag.parent.iloc[0].astype(float),
        "child": checkpoint.dag.child.iloc[0].astype(float),
        "pit_equal_weight": pit_equal_weight.iloc[0].astype(float),
        "economic_cash": economic_cash_weights.iloc[0].astype(float),
    }

    simulations: dict[str, pd.DataFrame] = {}
    simulation_hashes: dict[str, str] = {}
    arm_metrics: dict[str, dict[str, Any]] = {}
    for arm, vector in target_vectors.items():
        schedule = pd.DataFrame(
            np.repeat(vector.to_numpy(dtype=float)[None, :], len(calendar), axis=0),
            index=calendar,
            columns=vector.index,
            dtype=float,
        )
        arm_returns = economic_cash_frame if arm == "economic_cash" else returns
        simulation = engine.run_simulation(
            target_weights=schedule,
            returns_df=arm_returns,
            cost_bps=float(turnover_cost_rate),
            strict_missing_returns=True,
        )
        if abs(float(simulation.loc[evaluation_date, "gross_ret"])) > 1e-15:
            raise HistoricalOutcomeError("aov0_historical_outcome_pre_execution_return_credited")
        if abs(float(simulation.loc[evaluation_date, "turnover"])) > 1e-15:
            raise HistoricalOutcomeError("aov0_historical_outcome_pre_execution_turnover_credited")
        active_rows = simulation.index[simulation["turnover"].gt(1e-15)]
        if len(active_rows) != 1 or active_rows[0] <= evaluation_date:
            raise HistoricalOutcomeError("aov0_historical_outcome_initial_execution_boundary_invalid")
        simulations[arm] = simulation
        simulation_hashes[arm] = _frame_hash(simulation)
        arm_metrics[arm] = {
            "gross_compound_return": format(float((1.0 + simulation["gross_ret"]).prod() - 1.0), ".17g"),
            "net_compound_return": format(float((1.0 + simulation["net_ret"]).prod() - 1.0), ".17g"),
            "turnover_sum": format(float(simulation["turnover"].sum()), ".17g"),
            "cost_sum": format(float(simulation["cost"].sum()), ".17g"),
            "trading_rows": int(len(simulation)),
            "first_attributed_return_date": active_rows[0].date().isoformat(),
            "last_observed_return_date": simulation.index.max().date().isoformat(),
        }

    parent_net = float(arm_metrics["parent"]["net_compound_return"])
    child_net = float(arm_metrics["child"]["net_compound_return"])
    body: dict[str, Any] = {
        "schema_version": OUTCOME_SCHEMA,
        "outcome_authority": OUTCOME_AUTHORITY,
        "checkpoint_id": checkpoint.checkpoint_id,
        "target_date": target.date().isoformat(),
        "evaluation_start": evaluation.isoformat().replace("+00:00", "Z"),
        "outcome_open_not_before": maturity.isoformat().replace("+00:00", "Z"),
        "return_interval_policy": "ATTRIBUTED_DAILY_TOTAL_RETURN_LEFT_ENDPOINT_GTE_EVALUATION_START",
        "canonical_engine": "core.engine.run_simulation",
        "turnover_cost_rate": format(float(turnover_cost_rate), ".17g"),
        "outcome_source_sha256": str(outcome_source_sha256),
        "outcome_input_frame_sha256": _frame_hash(outcome_market_raw),
        "normalized_return_matrix_sha256": _frame_hash(returns),
        "economic_cash_return_matrix_sha256": _frame_hash(economic_cash_frame),
        "economic_cash_source_sha256": str(economic_cash_source_sha256),
        "required_arms": ["rule100", "parent", "child", "pit_equal_weight", "economic_cash"],
        "simulation_hashes": simulation_hashes,
        "arm_metrics": arm_metrics,
        "paired_child_minus_parent_net_compound_return": format(child_net - parent_net, ".17g"),
        "parent_child_mutation_authority": "NONE",
        "prospective_clock_authority": "NONE",
        "financial_alpha_evidence": 0,
    }
    outcome_id = domain_hash("AOV0:HISTORICAL_PIT_CHECKPOINT_OUTCOME:V1", body)
    payload = {**body, "outcome_id": outcome_id}
    return HistoricalAOVOutcome(outcome_id=outcome_id, payload=payload, simulations=simulations)


def verify_historical_aov_outcome(outcome: HistoricalAOVOutcome) -> None:
    payload = dict(outcome.payload)
    if payload.get("schema_version") != OUTCOME_SCHEMA:
        raise HistoricalOutcomeError("aov0_historical_outcome_schema_invalid")
    if payload.get("outcome_authority") != OUTCOME_AUTHORITY:
        raise HistoricalOutcomeError("aov0_historical_outcome_authority_invalid")
    if payload.get("parent_child_mutation_authority") != "NONE":
        raise HistoricalOutcomeError("aov0_historical_outcome_mutation_authority_forbidden")
    if payload.get("prospective_clock_authority") != "NONE":
        raise HistoricalOutcomeError("aov0_historical_outcome_prospective_authority_forbidden")
    if payload.get("financial_alpha_evidence") != 0:
        raise HistoricalOutcomeError("aov0_historical_outcome_financial_alpha_evidence_invalid")
    supplied = str(payload.pop("outcome_id", ""))
    expected = domain_hash("AOV0:HISTORICAL_PIT_CHECKPOINT_OUTCOME:V1", payload)
    if supplied != expected or outcome.outcome_id != expected:
        raise HistoricalOutcomeError("aov0_historical_outcome_hash_mismatch")
    required_arms = ["rule100", "parent", "child", "pit_equal_weight", "economic_cash"]
    if payload.get("required_arms") != required_arms or set(outcome.simulations) != set(required_arms):
        raise HistoricalOutcomeError("aov0_historical_outcome_required_arms_invalid")
    expected_hashes = payload.get("simulation_hashes") or {}
    actual_hashes = {arm: _frame_hash(frame) for arm, frame in outcome.simulations.items()}
    if expected_hashes != actual_hashes:
        raise HistoricalOutcomeError("aov0_historical_outcome_simulation_hash_mismatch")


def _reject_pre_or_target_rows(frame: pd.DataFrame, *, target: pd.Timestamp) -> None:
    date_column = None
    for column in frame.columns:
        token = "".join(character for character in str(column).upper() if character.isalnum())
        if token in DATE_ALIASES:
            date_column = column
            break
    if date_column is None:
        raise HistoricalOutcomeError("aov0_historical_outcome_date_column_required")
    dates = pd.to_datetime(frame[date_column], errors="raise").dt.normalize()
    if dates.le(target).any():
        raise HistoricalOutcomeError("aov0_historical_outcome_pre_or_target_market_forbidden")


def _aware_utc(value: str | pd.Timestamp, *, field: str) -> pd.Timestamp:
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        raise HistoricalOutcomeError(f"aov0_historical_outcome_{field}_timezone_required")
    return parsed.tz_convert("UTC")


def _sha256_text(value: object, *, field: str) -> str:
    text = str(value or "").strip().lower()
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise HistoricalOutcomeError(f"aov0_historical_outcome_{field}_sha256_invalid")
    return text


def _frame_hash(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(str(frame.shape).encode("utf-8"))
    digest.update("|".join(str(column) for column in frame.columns).encode("utf-8"))
    digest.update("|".join(str(dtype) for dtype in frame.dtypes).encode("utf-8"))
    digest.update(pd.util.hash_pandas_object(frame.index, index=False).to_numpy(dtype="uint64").tobytes())
    digest.update(pd.util.hash_pandas_object(frame, index=False).to_numpy(dtype="uint64").tobytes())
    return digest.hexdigest()
