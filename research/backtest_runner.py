"""Canonical Research Backtest Runner v0."""

from __future__ import annotations

import hashlib
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

import numpy as np
import pandas as pd

from core import engine
from research.benchmarks import PITEligibilityProvider, build_required_benchmark_weights
from research.evidence_schema import EvidencePacket, write_evidence_packet
from research.metrics import build_equity_curve, compute_metrics
from research.status import ResearchStatus
from research.strategy_cartridge import StrategyCartridge, cartridge_from_mapping, validate_cartridge


CASH_COLUMN = "CASH"
ROW_SUM_TOLERANCE = 1e-9


@dataclass(frozen=True)
class ResearchBacktestResult:
    """Return object for a canonical research backtest attempt."""

    status: ResearchStatus
    run_id: str
    evidence_packet: dict[str, Any]
    artifacts: dict[str, str]
    gate_results: dict[str, Any]
    metrics: dict[str, Any]
    benchmark_metrics: dict[str, Any]
    simulation_result: pd.DataFrame
    executed_weights: pd.DataFrame

    @property
    def verdict(self) -> dict[str, Any]:
        return dict(self.evidence_packet.get("verdict", {}))


def run_research_backtest(
    *,
    cartridge: StrategyCartridge | Mapping[str, Any],
    target_weights: pd.DataFrame,
    returns_df: pd.DataFrame,
    input_signatures: Mapping[str, Any] | None = None,
    pit_membership_proof: Mapping[str, Any] | None = None,
    leakage_checks: Mapping[str, Any] | None = None,
    pit_eligibility_provider: PITEligibilityProvider | None = None,
    run_id: str | None = None,
    emit_artifacts: bool = True,
) -> ResearchBacktestResult:
    """Run strategy and required benchmarks through the canonical engine."""

    normalized_cartridge = _normalize_cartridge(cartridge)
    run_identifier = _normalize_run_identifier(run_id, normalized_cartridge.strategy_id)
    evidence_output_dir = _resolve_evidence_output_dir(normalized_cartridge.output_dir, run_identifier)
    cartridge_failures = validate_cartridge(normalized_cartridge)
    input_signatures = dict(input_signatures or {})
    pit_membership_proof = dict(pit_membership_proof or {})
    leakage_checks = dict(leakage_checks or {})
    gate_failures = list(cartridge_failures)

    weight_validation = validate_target_weights(target_weights)
    gate_failures.extend(weight_validation)

    returns_validation = _validate_returns(returns_df)
    gate_failures.extend(returns_validation)
    calendar_validation = _validate_full_calendar(target_weights, returns_df)
    gate_failures.extend(calendar_validation)

    if normalized_cartridge.source_signatures_required and not input_signatures:
        gate_failures.append("missing_input_signatures")
    if not pit_membership_proof:
        gate_failures.append("missing_pit_membership_proof")
    elif _is_placeholder_pit_proof(pit_membership_proof):
        gate_failures.append("placeholder_pit_membership_proof")
    if not leakage_checks:
        gate_failures.append("missing_leakage_checks")
    elif any(value is not True for value in leakage_checks.values()):
        gate_failures.append("leakage_check_failed")

    simulation_result = pd.DataFrame()
    executed_weights = _build_executed_weights(target_weights) if not target_weights.empty else pd.DataFrame()
    if not executed_weights.empty and isinstance(returns_df, pd.DataFrame) and not returns_df.empty:
        gate_failures.extend(_validate_executed_returns_finite(executed_weights, returns_df))
    metrics: dict[str, Any] = {}
    benchmark_metrics: dict[str, Any] = {}
    benchmark_curves: dict[str, pd.Series] = {}
    equity_curve = pd.Series(dtype=float)

    if gate_failures:
        status = ResearchStatus.BLOCKED
    else:
        try:
            simulation_result = engine.run_simulation(
                target_weights=target_weights,
                returns_df=returns_df,
                cost_bps=float(normalized_cartridge.turnover_cost_rate),
                strict_missing_returns=True,
            )
        except RuntimeError as exc:
            gate_failures.append(_engine_gate_from_exception(exc))
            status = ResearchStatus.BLOCKED
        else:
            equity_curve = build_equity_curve(simulation_result["net_ret"])
            benchmark_results, benchmark_weights, benchmark_gate_failures = _run_required_benchmarks(
                cartridge=normalized_cartridge,
                target_weights=target_weights,
                returns_df=returns_df,
                pit_eligibility_provider=pit_eligibility_provider,
            )
            gate_failures.extend(benchmark_gate_failures)
            if gate_failures:
                status = ResearchStatus.BLOCKED
            else:
                first_benchmark_result = next(iter(benchmark_results.values()), None)
                metrics = compute_metrics(
                    simulation_result,
                    executed_weights,
                    target_weights,
                    benchmark_result=first_benchmark_result,
                )
                for benchmark_name, benchmark_result in benchmark_results.items():
                    weights = benchmark_weights[benchmark_name]
                    benchmark_metrics[benchmark_name] = compute_metrics(
                        benchmark_result,
                        _build_executed_weights(weights),
                        weights,
                    )
                    benchmark_curves[benchmark_name] = build_equity_curve(benchmark_result["net_ret"])
                status = _status_from_completed_run(normalized_cartridge, metrics)

    data_quality_report = _build_data_quality_report(target_weights, returns_df, executed_weights)
    if gate_failures:
        data_quality_report["blocking_failures"] = list(gate_failures)
    gate_results = {
        "passed": not gate_failures,
        "failures": list(dict.fromkeys(gate_failures)),
        "strict_missing_returns": True,
        "canonical_engine": "core.engine.run_simulation",
        "cash_policy": "implicit_residual_cash",
    }
    verdict = {
        "status": status.value,
        "research_valid": status == ResearchStatus.RESEARCH_VALID,
        "promotion_status": status.value,
        "blocking_failures": gate_results["failures"],
    }
    run_metadata = _build_run_metadata(
        run_identifier,
        normalized_cartridge,
        target_weights,
        returns_df,
    )

    if status == ResearchStatus.BLOCKED and not metrics:
        metrics = _empty_metrics()

    packet = EvidencePacket(
        run_id=run_identifier,
        status=status,
        output_dir=evidence_output_dir,
        cartridge=normalized_cartridge.to_dict(),
        run_metadata=run_metadata,
        gate_results=gate_results,
        input_signatures=input_signatures,
        pit_membership_proof=pit_membership_proof,
        leakage_checks=leakage_checks,
        data_quality_report=data_quality_report,
        metrics=metrics,
        benchmark_metrics=benchmark_metrics,
        verdict=verdict,
    )
    artifacts: dict[str, str] = {}
    if emit_artifacts:
        artifacts = write_evidence_packet(
            packet,
            target_weights=target_weights if not target_weights.empty else None,
            executed_weights=executed_weights if not executed_weights.empty else None,
            equity_curve=equity_curve if not equity_curve.empty else None,
            benchmark_curves=benchmark_curves,
            simulation_result=simulation_result if not simulation_result.empty else None,
        )

    return ResearchBacktestResult(
        status=status,
        run_id=run_identifier,
        evidence_packet=packet.to_dict(),
        artifacts=artifacts,
        gate_results=gate_results,
        metrics=metrics,
        benchmark_metrics=benchmark_metrics,
        simulation_result=simulation_result,
        executed_weights=executed_weights,
    )


def validate_target_weights(target_weights: pd.DataFrame) -> list[str]:
    """Validate risky-asset-only long-only target weights for v0."""

    failures: list[str] = []
    if not isinstance(target_weights, pd.DataFrame) or target_weights.empty:
        return ["missing_target_weights"]

    try:
        date_index = _coerce_datetime_index(target_weights.index)
    except (TypeError, ValueError):
        failures.append("target_weight_index_not_date_like")
    else:
        if date_index.hasnans:
            failures.append("target_weight_index_not_date_like")
        if not date_index.is_monotonic_increasing:
            failures.append("target_weight_index_not_sorted")
        if not date_index.is_unique:
            failures.append("target_weight_index_not_unique")

    if any(str(col).upper() == CASH_COLUMN for col in target_weights.columns):
        failures.append("cash_column_forbidden_v0")

    non_numeric_columns = [
        str(column)
        for column in target_weights.columns
        if not pd.api.types.is_numeric_dtype(target_weights[column])
    ]
    if non_numeric_columns:
        failures.append("target_weights_non_numeric")
        return failures

    numeric = target_weights.astype(float)
    finite_mask = np.isfinite(numeric.to_numpy(dtype=float))
    if not bool(finite_mask.all()):
        failures.append("target_weights_non_finite")
    if (numeric < -ROW_SUM_TOLERANCE).any().any():
        failures.append("target_weights_negative_long_only")
    row_sums = numeric.sum(axis=1)
    if (row_sums > 1.0 + ROW_SUM_TOLERANCE).any():
        failures.append("target_weight_row_sum_gt_one")

    return failures


def _normalize_cartridge(cartridge: StrategyCartridge | Mapping[str, Any]) -> StrategyCartridge:
    if isinstance(cartridge, StrategyCartridge):
        return cartridge
    return cartridge_from_mapping(cartridge)


def _build_executed_weights(target_weights: pd.DataFrame) -> pd.DataFrame:
    return target_weights.shift(1).fillna(0.0)


def _validate_returns(returns_df: pd.DataFrame) -> list[str]:
    if not isinstance(returns_df, pd.DataFrame) or returns_df.empty:
        return ["missing_returns"]
    try:
        date_index = _coerce_datetime_index(returns_df.index)
    except (TypeError, ValueError):
        return ["returns_index_not_date_like"]
    failures: list[str] = []
    if date_index.hasnans:
        failures.append("returns_index_not_date_like")
    if not date_index.is_monotonic_increasing:
        failures.append("returns_index_not_sorted")
    if not date_index.is_unique:
        failures.append("returns_index_not_unique")
    non_numeric = [str(column) for column in returns_df.columns if not pd.api.types.is_numeric_dtype(returns_df[column])]
    if non_numeric:
        failures.append("returns_non_numeric")
    numeric = returns_df.select_dtypes(include="number")
    if numeric.shape == returns_df.shape and not np.isfinite(numeric.fillna(0.0).to_numpy(dtype=float)).all():
        failures.append("returns_non_finite")
    return failures


def _validate_full_calendar(target_weights: pd.DataFrame, returns_df: pd.DataFrame) -> list[str]:
    """Require v0 target rows to match the trading calendar supplied by returns."""

    if not isinstance(target_weights, pd.DataFrame) or target_weights.empty:
        return []
    if not isinstance(returns_df, pd.DataFrame) or returns_df.empty:
        return []
    try:
        target_index = _coerce_datetime_index(target_weights.index).normalize()
        returns_index = _coerce_datetime_index(returns_df.index).normalize()
    except (TypeError, ValueError):
        return []
    if target_index.hasnans or returns_index.hasnans:
        return []
    if not target_index.equals(returns_index):
        return ["target_weights_must_match_returns_calendar_v0"]
    return []


def _validate_executed_returns_finite(
    executed_weights: pd.DataFrame,
    returns_df: pd.DataFrame,
) -> list[str]:
    aligned_returns = returns_df.reindex(index=executed_weights.index, columns=executed_weights.columns)
    executed_exposure = executed_weights.ne(0.0)
    executed_values = aligned_returns.where(executed_exposure)
    non_finite_executed = executed_values.notna() & ~np.isfinite(executed_values.fillna(0.0).to_numpy(dtype=float))
    if bool(non_finite_executed.any().any()):
        return ["non_finite_executed_returns"]
    return []


def _is_placeholder_pit_proof(pit_membership_proof: Mapping[str, Any]) -> bool:
    placeholder_values = {"placeholder", "stub", "todo", "missing", "unknown"}
    for key in ("proof_type", "status", "source", "mode"):
        value = pit_membership_proof.get(key)
        if isinstance(value, str) and value.strip().lower() in placeholder_values:
            return True
    return bool(pit_membership_proof.get("placeholder"))


def _run_required_benchmarks(
    *,
    cartridge: StrategyCartridge,
    target_weights: pd.DataFrame,
    returns_df: pd.DataFrame,
    pit_eligibility_provider: PITEligibilityProvider | None,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame], list[str]]:
    failures: list[str] = []
    results: dict[str, pd.DataFrame] = {}
    try:
        benchmark_weights = build_required_benchmark_weights(
            target_weights,
            cartridge.benchmark_policy or {},
            pit_eligibility_provider=pit_eligibility_provider,
        )
    except ValueError as exc:
        failures.append(str(exc))
        return results, {}, failures

    for benchmark_name, weights in benchmark_weights.items():
        try:
            results[benchmark_name] = engine.run_simulation(
                target_weights=weights,
                returns_df=returns_df,
                cost_bps=float(cartridge.turnover_cost_rate),
                strict_missing_returns=True,
            )
        except RuntimeError as exc:
            failures.append(f"benchmark_{benchmark_name}_{_engine_gate_from_exception(exc)}")
    return results, benchmark_weights, failures


def _status_from_completed_run(cartridge: StrategyCartridge, metrics: Mapping[str, Any]) -> ResearchStatus:
    if str(cartridge.strategy_role).strip() == "diagnostic_lifecycle_policy":
        return ResearchStatus.DIAGNOSTIC_ONLY
    trading_days = int(metrics.get("trading_days") or 0)
    if trading_days < int(cartridge.min_required_trading_days):
        return ResearchStatus.EXPLORATORY
    return ResearchStatus.RESEARCH_VALID


def _engine_gate_from_exception(exc: RuntimeError) -> str:
    message = str(exc)
    if "Missing" in message and "return cells" in message:
        return "missing_executed_returns"
    return f"engine_runtime_error:{message}"


def _build_data_quality_report(
    target_weights: pd.DataFrame,
    returns_df: pd.DataFrame,
    executed_weights: pd.DataFrame,
) -> dict[str, Any]:
    target_numeric = target_weights.select_dtypes(include="number") if isinstance(target_weights, pd.DataFrame) else pd.DataFrame()
    returns_numeric = returns_df.select_dtypes(include="number") if isinstance(returns_df, pd.DataFrame) else pd.DataFrame()
    executed_nonzero = int(executed_weights.ne(0.0).sum().sum()) if not executed_weights.empty else 0
    aligned_returns = returns_df.reindex(index=executed_weights.index, columns=executed_weights.columns) if not executed_weights.empty else pd.DataFrame()
    missing_executed = (
        int((aligned_returns.isna() & executed_weights.ne(0.0)).sum().sum())
        if not aligned_returns.empty
        else 0
    )
    non_finite_inputs = 0
    if not target_numeric.empty:
        non_finite_inputs += int((~np.isfinite(target_numeric.to_numpy(dtype=float))).sum())
    if not returns_numeric.empty:
        non_finite_inputs += int((~np.isfinite(returns_numeric.fillna(0.0).to_numpy(dtype=float))).sum())
    return {
        "target_weight_rows": int(len(target_weights)) if isinstance(target_weights, pd.DataFrame) else 0,
        "target_weight_assets": int(len(target_weights.columns)) if isinstance(target_weights, pd.DataFrame) else 0,
        "return_rows": int(len(returns_df)) if isinstance(returns_df, pd.DataFrame) else 0,
        "return_assets": int(len(returns_df.columns)) if isinstance(returns_df, pd.DataFrame) else 0,
        "executed_nonzero_cells": executed_nonzero,
        "missing_executed_return_count": missing_executed,
        "non_finite_input_count": non_finite_inputs,
    }


def _build_run_metadata(
    run_id: str,
    cartridge: StrategyCartridge,
    target_weights: pd.DataFrame,
    returns_df: pd.DataFrame,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_engine": "core.engine.run_simulation",
        "strict_missing_returns": True,
        "execution_lag": cartridge.execution_lag,
        "cost_policy": {
            "turnover_cost_rate": float(cartridge.turnover_cost_rate or 0.0),
            "turnover_cost_bps": float(cartridge.turnover_cost_rate or 0.0) * 10_000.0,
            "cost_basis": "per_unit_one_way_risky_asset_turnover",
        },
        "cash_policy": "implicit_residual_cash",
        "target_weight_signature": _frame_signature(target_weights),
        "returns_signature": _frame_signature(returns_df),
    }


def _coerce_datetime_index(index: Any) -> pd.DatetimeIndex:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return pd.DatetimeIndex(pd.to_datetime(index, errors="coerce"))


def _frame_signature(frame: pd.DataFrame) -> dict[str, Any]:
    columns = tuple(str(column) for column in frame.columns)
    index_min = str(frame.index.min()) if len(frame.index) else None
    index_max = str(frame.index.max()) if len(frame.index) else None
    payload = f"{frame.shape}|{columns}|{index_min}|{index_max}"
    return {
        "rows": int(frame.shape[0]),
        "columns": list(columns),
        "index_min": index_min,
        "index_max": index_max,
        "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    }


def _default_run_id(strategy_id: str) -> str:
    safe_strategy_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in strategy_id) or "research"
    return f"{safe_strategy_id}_{uuid4().hex[:12]}"


def _normalize_run_identifier(run_id: str | None, strategy_id: str) -> str:
    if run_id is None:
        return _default_run_id(strategy_id)
    candidate = str(run_id).strip()
    if (
        not candidate
        or candidate in (".", "..")
        or Path(candidate).is_absolute()
        or any(part in ("", ".", "..") for part in Path(candidate).parts)
        or "/" in candidate
        or "\\" in candidate
    ):
        raise ValueError("unsafe_run_id")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if any(char not in allowed for char in candidate):
        raise ValueError("unsafe_run_id")
    return candidate


def _resolve_evidence_output_dir(output_root: str | Path, run_id: str) -> Path:
    root = Path(output_root).expanduser().resolve()
    run_dir = (root / run_id).resolve()
    if root != run_dir and root not in run_dir.parents:
        raise ValueError("evidence_output_dir_escape")
    return run_dir


def _empty_metrics() -> dict[str, Any]:
    return {
        "cumulative_return": None,
        "CAGR": None,
        "annualized_volatility": None,
        "Sharpe": None,
        "Sortino": None,
        "max_drawdown": None,
        "drawdown_duration": None,
        "average_turnover": None,
        "total_turnover": None,
        "total_cost_drag": None,
        "average_gross_exposure": None,
        "average_cash_residual": None,
        "benchmark_excess_return": None,
        "tracking_error": None,
        "information_ratio": None,
        "missing_executed_return_count": None,
        "non_finite_input_count": None,
        "trading_days": 0,
        "rebalance_count": None,
    }
