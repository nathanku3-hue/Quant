"""Plan, run, freeze, and query-meter the historical PIT AOV evidence lane.

The implementation deliberately reuses the frozen Rule100/Parent/Child/five-arm
engine. Historical evidence is kept separate from prospective authority and
always reports ``financial_alpha_evidence = 0``.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import engine  # noqa: E402
from research.aov0.contracts import DEFAULT_CONTRACT  # noqa: E402
from research.aov0.experiment import run_five_arm_experiment  # noqa: E402
from research.aov0.historical_pit import (  # noqa: E402
    HISTORICAL_PIT_MODE,
    build_factor_transition_plan,
    build_historical_factor_states,
    build_historical_market_panel,
    build_historical_replay_inputs,
    completed_week_decision_dates,
    expand_transition_fundamentals,
    historical_cash_from_official_sofr_rows,
    utc_now_text,
    validate_historical_session_continuity,
)
from research.aov0.historical_risk_set import (  # noqa: E402
    HISTORICAL_SCREEN_FREEZE_MODE,
    HistoricalRiskSet,
    load_historical_start_risk_set,
)
from research.aov0.historical_security_master import (  # noqa: E402
    HistoricalSecurityMaster,
    load_historical_start_security_master,
)
from research.aov0.policy import DEFAULT_MUTATION  # noqa: E402
from research.aov0.review import expected_shortfall_loss  # noqa: E402
from research.benchmarks import (  # noqa: E402
    build_economic_cash_frames,
    build_pit_equal_weight_benchmark,
    strategy_rebalance_dates,
)
from research.metrics import build_equity_curve, compute_metrics  # noqa: E402


TURNOVER_COST_RATE = 0.001
FREEZE_SCHEMA = "aov0_historical_pit_a1_to_a2_freeze_v1"
REPORT_SCHEMA = "aov0_historical_pit_evidence_report_v1"
QUERY_LOCK_SCHEMA = "aov0_historical_pit_a2_query_lock_v1"
QUERY_RECEIPT_SCHEMA = "aov0_historical_pit_a2_query_receipt_v1"
A1_ADMITTED_CLASSIFICATION = "A1_ADMITTED_HISTORICAL_PIT"
A1_GATE_FAILED_CLASSIFICATION = "A1_HISTORICAL_PIT_GATE_FAILED"
A2_UNTOUCHED_CLASSIFICATION = "A2_UNTOUCHED_HISTORICAL_PIT"
CURRENT_SCREEN_DIAGNOSTIC_CLASSIFICATION = "CURRENT_SCREEN_CONDITIONED_DIAGNOSTIC"
FROZEN_IMPLEMENTATION_PATHS = (
    "core/engine.py",
    "data/feature_specs.py",
    "data/feature_store.py",
    "research/aov0/ciq_fundamentals.py",
    "research/aov0/ciq_market.py",
    "research/aov0/contracts.py",
    "research/aov0/cube.py",
    "research/aov0/dag.py",
    "research/aov0/experiment.py",
    "research/aov0/historical_pit.py",
    "research/aov0/historical_risk_set.py",
    "research/aov0/historical_security_master.py",
    "research/aov0/policy.py",
    "research/aov0/review.py",
    "research/backtest_runner.py",
    "research/benchmarks.py",
    "research/metrics.py",
    "research/strategy_cartridge.py",
    "strategies/rule100_softmax.py",
    "strategies/rule100_softmax_v1_1.py",
    "scripts/aov0_capture_ciq_historical_market_chunk.ps1",
    "scripts/aov0_capture_ciq_historical_pit_period_matrix_chunk.ps1",
    "scripts/aov0_capture_ciq_historical_pit_transition_batch.ps1",
    "scripts/aov0_historical_pit_replay.py",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _atomic_json(payload: dict[str, Any], path: Path, *, refuse_existing: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if refuse_existing and path.exists():
        raise FileExistsError(f"historical_evidence_artifact_exists:{path}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
        if refuse_existing and path.exists():
            raise FileExistsError(f"historical_evidence_artifact_exists:{path}")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _atomic_csv(frame: pd.DataFrame, path: Path, *, refuse_existing: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if refuse_existing and path.exists():
        raise FileExistsError(f"historical_evidence_artifact_exists:{path}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        frame.to_csv(temp, index=False)
        if refuse_existing and path.exists():
            raise FileExistsError(f"historical_evidence_artifact_exists:{path}")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _read_csvs(paths: Iterable[Path]) -> pd.DataFrame:
    files = [Path(path) for path in paths]
    if not files:
        raise ValueError("historical_input_file_list_empty")
    frames: list[pd.DataFrame] = []
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
        frames.append(pd.read_csv(path))
    return pd.concat(frames, ignore_index=True, sort=False)


def _entity_ids_from_master(
    master: pd.DataFrame,
    *,
    expected_entity_ids: Iterable[str] | None = None,
    require_current_109: bool = False,
) -> tuple[str, ...]:
    if "SP_ENTITY_ID" not in master.columns:
        raise ValueError("historical_security_master_missing_sp_entity_id")
    entity = master["SP_ENTITY_ID"].fillna("").astype(str).str.strip()
    if entity.eq("").any():
        raise ValueError("historical_security_master_blank_sp_entity_id")
    if entity.duplicated().any():
        raise ValueError("historical_security_master_duplicate_sp_entity_id")
    values = tuple(sorted(entity.tolist()))
    if require_current_109 and len(values) != 109:
        raise ValueError(f"historical_frozen_entity_count_invalid:{len(values)}")
    if expected_entity_ids is not None:
        expected = tuple(sorted(str(value).strip() for value in expected_entity_ids))
        if values != expected:
            raise ValueError("historical_security_master_risk_set_membership_mismatch")
    return values


def _load_optional_risk_set(
    membership_path: Path | None,
    receipt_path: Path | None,
    *,
    expected_as_of_date: str,
) -> HistoricalRiskSet | None:
    if (membership_path is None) != (receipt_path is None):
        raise ValueError("historical_risk_set_membership_and_receipt_required_together")
    if membership_path is None or receipt_path is None:
        return None
    return load_historical_start_risk_set(
        membership_path,
        receipt_path,
        expected_as_of_date=expected_as_of_date,
    )


def _load_optional_historical_security_master(
    master_path: Path,
    receipt_path: Path | None,
    *,
    risk_set: HistoricalRiskSet | None,
    expected_as_of_date: str,
) -> HistoricalSecurityMaster | None:
    if risk_set is None:
        if receipt_path is not None:
            raise ValueError("historical_security_master_receipt_requires_historical_risk_set")
        return None
    if receipt_path is None:
        raise ValueError("historical_security_master_receipt_required_for_admitted_a1")
    return load_historical_start_security_master(
        master_path,
        receipt_path,
        expected_as_of_date=expected_as_of_date,
        expected_entity_ids=risk_set.entity_ids,
    )


def _assert_file_manifest(path: Path, manifest: dict[str, Any], *, label: str) -> None:
    if path.resolve().as_posix() != str(manifest.get("path") or ""):
        raise ValueError(f"{label}_path_drift")
    if _sha256_file(path) != str(manifest.get("sha256") or ""):
        raise ValueError(f"{label}_hash_drift")
    if path.stat().st_size != int(manifest.get("bytes", -1)):
        raise ValueError(f"{label}_size_drift")


def _source_manifest(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted({Path(value) for value in paths}, key=lambda item: item.as_posix()):
        rows.append(
            {
                "path": path.resolve().as_posix(),
                "sha256": _sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return rows


def _load_nyfed_rows(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("refRates") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("historical_nyfed_ref_rates_missing")
    return pd.DataFrame(rows)


def _validate_historical_pit_source_semantics(
    period_matrix: pd.DataFrame,
    transition_raw: pd.DataFrame,
) -> dict[str, Any]:
    period_required = {
        "retrieved_at_utc",
        "provider_function",
        "provider_metric",
        "relative_period",
        "filing_version",
    }
    transition_required = {"retrieved_at_utc", "provider_function", "filing_version"}
    missing_period = sorted(period_required - set(period_matrix.columns))
    if missing_period:
        raise ValueError(f"historical_period_source_metadata_missing:{','.join(missing_period)}")
    missing_transition = sorted(transition_required - set(transition_raw.columns))
    if missing_transition:
        raise ValueError(
            f"historical_transition_source_metadata_missing:{','.join(missing_transition)}"
        )

    period_provider = period_matrix["provider_function"].fillna("").astype(str).str.upper().str.strip()
    period_metric = period_matrix["provider_metric"].fillna("").astype(str).str.upper().str.strip()
    period_relative = period_matrix["relative_period"].fillna("").astype(str).str.upper().str.strip()
    period_filing = period_matrix["filing_version"].fillna("").astype(str).str.upper().str.strip()
    transition_provider = transition_raw["provider_function"].fillna("").astype(str).str.upper().str.strip()
    transition_filing = transition_raw["filing_version"].fillna("").astype(str).str.upper().str.strip()

    if not period_provider.eq("SPG").all() or not transition_provider.eq("SPG").all():
        raise ValueError("historical_pit_provider_function_not_spg")
    if not period_metric.eq("IQ_PERIOD_END").all():
        raise ValueError("historical_period_probe_metric_invalid")
    if not period_relative.eq("FQ0").all():
        raise ValueError("historical_period_probe_relative_period_invalid")
    if not period_filing.eq("ORIGINAL").all() or not transition_filing.eq("ORIGINAL").all():
        raise ValueError("historical_pit_filing_version_not_original")

    period_retrieved = pd.to_datetime(period_matrix["retrieved_at_utc"], utc=True, errors="raise")
    transition_retrieved = pd.to_datetime(transition_raw["retrieved_at_utc"], utc=True, errors="raise")
    if period_retrieved.isna().any() or transition_retrieved.isna().any():
        raise ValueError("historical_pit_retrieval_timestamp_missing")
    return {
        "provider_function": "SPG",
        "filing_version": "Original",
        "period_probe_metric": "IQ_PERIOD_END",
        "period_probe_relative_period": "FQ0",
        "retrieval_timestamp_bound": True,
    }


def _verify_report_content_hash(payload: dict[str, Any]) -> None:
    supplied = str(payload.get("report_content_hash") or "")
    body = dict(payload)
    body.pop("report_content_hash", None)
    if not supplied or supplied != _canonical_json_hash(body):
        raise ValueError("historical_report_content_hash_invalid")


def _expected_shortfall_from_simulation(simulation: pd.DataFrame, level: float) -> float:
    values = pd.to_numeric(simulation["net_ret"], errors="coerce").dropna()
    return float(expected_shortfall_loss(values, level=level))


def _benchmark_simulations(replay, cash: pd.Series) -> dict[str, pd.DataFrame]:
    pit_targets = build_pit_equal_weight_benchmark(
        replay.rule100_weights.index,
        replay.rule100_weights.columns,
        lambda date: replay.eligible_by_date[pd.Timestamp(date).normalize()],
        rebalance_dates=strategy_rebalance_dates(replay.rule100_weights),
    )
    pit = engine.run_simulation(
        target_weights=pit_targets,
        returns_df=replay.total_returns,
        cost_bps=TURNOVER_COST_RATE,
        strict_missing_returns=True,
    )
    cash_weights, cash_returns = build_economic_cash_frames(replay.rule100_weights.index, cash)
    economic = engine.run_simulation(
        target_weights=cash_weights,
        returns_df=cash_returns,
        cost_bps=TURNOVER_COST_RATE,
        strict_missing_returns=True,
    )
    return {"pit_equal_weight": pit, "economic_cash": economic}


def _metrics_for_benchmark(simulation: pd.DataFrame, target_weights: pd.DataFrame) -> dict[str, Any]:
    executed = target_weights.shift(1).fillna(0.0)
    return compute_metrics(simulation, executed, target_weights)


def plan_fundamentals(args: argparse.Namespace) -> dict[str, Any]:
    risk_set = _load_optional_risk_set(
        getattr(args, "risk_set_membership", None),
        getattr(args, "risk_set_receipt", None),
        expected_as_of_date=args.start,
    )
    historical_security_master = _load_optional_historical_security_master(
        args.security_master,
        getattr(args, "historical_security_master_receipt", None),
        risk_set=risk_set,
        expected_as_of_date=args.start,
    )
    master = pd.read_csv(args.security_master)
    frozen = _entity_ids_from_master(
        master,
        expected_entity_ids=None if risk_set is None else risk_set.entity_ids,
        require_current_109=risk_set is None,
    )
    market_parts = [pd.read_csv(path) for path in args.market_part]
    market = build_historical_market_panel(
        security_master_raw=master,
        market_parts=market_parts,
        frozen_entity_ids=frozen,
    )
    start = pd.Timestamp(args.start).normalize()
    end = pd.Timestamp(args.end).normalize()
    calendar = pd.DatetimeIndex(
        sorted(market.frame.loc[market.frame["date"].between(start, end), "date"].unique())
    )
    calendar = validate_historical_session_continuity(calendar)
    decisions = completed_week_decision_dates(calendar)
    decisions = decisions[(decisions >= start) & (decisions <= end)]
    if len(decisions) == 0 or decisions[0] != start:
        raise ValueError("historical_plan_start_must_be_completed_week_decision")
    out = pd.DataFrame({"as_of_date": [date.date().isoformat() for date in decisions]})
    _atomic_csv(out, args.out, refuse_existing=args.refuse_existing)
    metadata = {
        "status": "HISTORICAL_PIT_WEEKLY_ASOF_PLAN_CREATED",
        "start": start.date().isoformat(),
        "end": end.date().isoformat(),
        "weekly_asof_dates": int(len(out)),
        "frozen_entity_count": len(frozen),
        "historical_risk_set_admitted": risk_set is not None,
        "historical_primary_security_identity_admitted": historical_security_master is not None,
        "risk_set_mode": None if risk_set is None else HISTORICAL_SCREEN_FREEZE_MODE,
        "market_part_count": len(args.market_part),
        "out": args.out.resolve().as_posix(),
        "out_sha256": _sha256_file(args.out),
        "financial_alpha_evidence": 0,
    }
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return metadata


def plan_transitions(args: argparse.Namespace) -> dict[str, Any]:
    matrix = _read_csvs(args.period_part)
    # One authoritative planner owns transition semantics.  In particular,
    # missing FQ0 is not a speculative transition signal: the replay engine
    # fails it closed before any expensive full-fundamental provider capture.
    out = build_factor_transition_plan(matrix)
    _atomic_csv(out, args.out, refuse_existing=args.refuse_existing)
    metadata = {
        "status": "HISTORICAL_PIT_TRANSITION_PLAN_CREATED",
        "transition_queries": int(len(out)),
        "entities": int(matrix["source_entity_id"].nunique()),
        "weekly_dates": int(matrix["as_of_date"].nunique()),
        "out": args.out.resolve().as_posix(),
        "out_sha256": _sha256_file(args.out),
        "financial_alpha_evidence": 0,
    }
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return metadata


def _run_window(
    *,
    stage: str,
    security_master: Path,
    market_paths: list[Path],
    period_paths: list[Path],
    transition_paths: list[Path],
    sofr_raw: Path,
    start: str,
    end: str,
    evidence_root: Path,
    risk_set: HistoricalRiskSet | None = None,
    historical_security_master: HistoricalSecurityMaster | None = None,
    inherited_source_cohort: dict[str, Any] | None = None,
    inherited_risk_set_sources: dict[str, Any] | None = None,
    inherited_historical_security_master_receipt_sources: list[dict[str, Any]] | None = None,
    expected_source_entity_ids: list[str] | None = None,
    required_security_ids: list[str] | None = None,
) -> dict[str, Any]:
    master = pd.read_csv(security_master)
    if stage == "A1":
        frozen = _entity_ids_from_master(
            master,
            expected_entity_ids=None if risk_set is None else risk_set.entity_ids,
            require_current_109=risk_set is None,
        )
    else:
        if not expected_source_entity_ids:
            raise ValueError("a2_frozen_source_entity_ids_missing")
        frozen = _entity_ids_from_master(master, expected_entity_ids=expected_source_entity_ids)
    market = build_historical_market_panel(
        security_master_raw=master,
        market_parts=[pd.read_csv(path) for path in market_paths],
        frozen_entity_ids=frozen,
    )
    period_matrix = _read_csvs(period_paths)
    transition_raw = _read_csvs(transition_paths)
    source_semantics = _validate_historical_pit_source_semantics(period_matrix, transition_raw)
    expanded = expand_transition_fundamentals(period_matrix, transition_raw)
    factor_states = build_historical_factor_states(expanded, frozen_entity_ids=frozen)
    replay = build_historical_replay_inputs(
        market_panel=market,
        factor_states=factor_states,
        evaluation_start=start,
        evaluation_end=end,
        contract=DEFAULT_CONTRACT,
        required_security_ids=required_security_ids,
    )
    sofr_rows = _load_nyfed_rows(sofr_raw)
    cash = historical_cash_from_official_sofr_rows(replay.rule100_weights.index, sofr_rows)
    cube = replay.cube
    experiment = run_five_arm_experiment(
        rule100_weights=replay.rule100_weights,
        returns_df=replay.total_returns,
        economic_cash_returns=cash,
        cube=cube,
        pit_eligibility_provider=lambda date: replay.eligible_by_date[pd.Timestamp(date).normalize()],
        output_root=evidence_root / "canonical_five_arm",
        turnover_cost_rate=TURNOVER_COST_RATE,
        contract=DEFAULT_CONTRACT,
        mutation=DEFAULT_MUTATION,
    )
    benchmark_sims = _benchmark_simulations(replay, cash)
    pit_targets = build_pit_equal_weight_benchmark(
        replay.rule100_weights.index,
        replay.rule100_weights.columns,
        lambda date: replay.eligible_by_date[pd.Timestamp(date).normalize()],
        rebalance_dates=strategy_rebalance_dates(replay.rule100_weights),
    )
    cash_targets, _cash_returns = build_economic_cash_frames(replay.rule100_weights.index, cash)
    benchmark_targets = {"pit_equal_weight": pit_targets, "economic_cash": cash_targets}

    metrics: dict[str, dict[str, Any]] = {
        arm: dict(result.metrics) for arm, result in experiment.runs.items()
    }
    for arm, simulation in benchmark_sims.items():
        metrics[arm] = _metrics_for_benchmark(simulation, benchmark_targets[arm])

    cvar = {
        arm: _expected_shortfall_from_simulation(result.simulation_result, DEFAULT_CONTRACT.cvar_level)
        for arm, result in experiment.runs.items()
    }
    cvar.update(
        {
            arm: _expected_shortfall_from_simulation(simulation, DEFAULT_CONTRACT.cvar_level)
            for arm, simulation in benchmark_sims.items()
        }
    )
    parent = metrics["parent"]
    child = metrics["child"]
    delta = {
        "child_minus_parent_cumulative_return": float(child["cumulative_return"] - parent["cumulative_return"]),
        "child_minus_parent_CAGR": (
            None if child.get("CAGR") is None or parent.get("CAGR") is None else float(child["CAGR"] - parent["CAGR"])
        ),
        "child_minus_parent_Sharpe": (
            None if child.get("Sharpe") is None or parent.get("Sharpe") is None else float(child["Sharpe"] - parent["Sharpe"])
        ),
        "child_minus_parent_max_drawdown": float(child["max_drawdown"] - parent["max_drawdown"]),
        "child_minus_parent_total_turnover": float(child["total_turnover"] - parent["total_turnover"]),
        "child_minus_parent_CVaR_loss": float(cvar["child"] - cvar["parent"]),
        "child_CVaR_improvement_vs_parent": float(cvar["parent"] - cvar["child"]),
    }
    trading_days = int(len(replay.rule100_weights))
    canonical_arm_gates_pass = all(run.gate_results["passed"] for run in experiment.runs.values())
    real_ciq_identity = all(str(value).startswith("CIQSEC:") for value in replay.security_ids)
    if stage == "A1" and risk_set is not None:
        if historical_security_master is None:
            raise ValueError("historical_primary_security_identity_required_for_admitted_a1")
        source_cohort = {
            "frozen_company_count": len(frozen),
            "historical_screen_membership_reconstructed": True,
            "historical_primary_security_identity_reconstructed": True,
            "risk_set_mode": HISTORICAL_SCREEN_FREEZE_MODE,
            "as_of_date": risk_set.as_of_date.date().isoformat(),
            "historical_primary_security_as_of_date": historical_security_master.as_of_date.date().isoformat(),
            "current_screen_conditioned": False,
            "current_primary_security_conditioned": False,
            "screen_law_hash": risk_set.metadata["screen_law_hash"],
            "limitation": None,
        }
    elif stage == "A2":
        if (
            not inherited_source_cohort
            or inherited_source_cohort.get("historical_screen_membership_reconstructed") is not True
            or inherited_source_cohort.get("historical_primary_security_identity_reconstructed") is not True
        ):
            raise ValueError("a2_inherited_historical_source_cohort_invalid")
        source_cohort = dict(inherited_source_cohort)
        source_cohort["frozen_company_count"] = len(frozen)
    else:
        source_cohort = {
            "frozen_company_count": len(frozen),
            "historical_screen_membership_reconstructed": False,
            "historical_primary_security_identity_reconstructed": False,
            "risk_set_mode": None,
            "as_of_date": None,
            "historical_primary_security_as_of_date": None,
            "current_screen_conditioned": True,
            "current_primary_security_conditioned": True,
            "screen_law_hash": None,
            "limitation": "CURRENT_FROZEN_109_COMPANY_SOURCE_COHORT_AND_CURRENT_PRIMARY_SECURITY_MAP; DATE_LOCAL PIT FACTORS/TECHNICAL ELIGIBILITY ONLY",
        }
    historical_screen_membership_reconstructed = bool(
        source_cohort["historical_screen_membership_reconstructed"]
    )
    historical_primary_security_identity_reconstructed = bool(
        source_cohort["historical_primary_security_identity_reconstructed"]
    )
    replay_metadata = dict(replay.metadata)
    replay_metadata["source_cohort_mode"] = source_cohort.get("risk_set_mode")
    replay_metadata["historical_screen_membership_reconstructed"] = historical_screen_membership_reconstructed
    replay_metadata["historical_primary_security_identity_reconstructed"] = historical_primary_security_identity_reconstructed
    replay_metadata["current_screen_conditioned"] = bool(source_cohort.get("current_screen_conditioned"))
    replay_metadata["current_primary_security_conditioned"] = bool(
        source_cohort.get("current_primary_security_conditioned")
    )
    replay_metadata["fixed_source_cohort_limitation"] = source_cohort.get("limitation")
    a1_gate = bool(
        stage == "A1"
        and trading_days >= 252
        and canonical_arm_gates_pass
        and real_ciq_identity
        and historical_screen_membership_reconstructed
        and historical_primary_security_identity_reconstructed
    )
    if stage == "A2":
        evidence_classification = A2_UNTOUCHED_CLASSIFICATION
    elif a1_gate:
        evidence_classification = A1_ADMITTED_CLASSIFICATION
    elif historical_screen_membership_reconstructed and historical_primary_security_identity_reconstructed:
        evidence_classification = A1_GATE_FAILED_CLASSIFICATION
    else:
        evidence_classification = CURRENT_SCREEN_DIAGNOSTIC_CLASSIFICATION
    report = {
        "schema_version": REPORT_SCHEMA,
        "stage": stage,
        "created_at_utc": utc_now_text(),
        "contract_hash": DEFAULT_CONTRACT.contract_hash,
        "mutation_hash": DEFAULT_MUTATION.manifest_hash,
        "turnover_cost_rate": TURNOVER_COST_RATE,
        "cube_computed_at": deterministic_computed_at.isoformat(),
        "evidence_authority": "HISTORICAL_ONLY",
        "evidence_classification": evidence_classification,
        "financial_alpha_evidence": 0,
        "prospective_authority_changed": False,
        "factor_pit_mode": HISTORICAL_PIT_MODE,
        "source_cohort": source_cohort,
        "source_semantics": source_semantics,
        "window": {
            "start": replay.rule100_weights.index.min().date().isoformat(),
            "end": replay.rule100_weights.index.max().date().isoformat(),
            "trading_days": trading_days,
            "weekly_decisions": int(len(replay.decision_dates)),
        },
        "source_entity_ids": list(frozen),
        "security_ids": list(replay.security_ids),
        "security_count": len(replay.security_ids),
        "metrics": metrics,
        "cvar_level": DEFAULT_CONTRACT.cvar_level,
        "cvar_loss": cvar,
        "parent_vs_child": delta,
        "canonical_experiment_id": experiment.experiment_id,
        "canonical_experiment_manifest": experiment.experiment_manifest.resolve().as_posix(),
        "canonical_experiment_manifest_sha256": _sha256_file(experiment.experiment_manifest),
        "a1_minimum_gate": {
            "requires_252_trading_days": True,
            "trading_days_pass": trading_days >= 252,
            "canonical_arm_gates_pass": canonical_arm_gates_pass,
            "real_ciq_primary_security_identity": real_ciq_identity,
            "historical_spg_asof_original": True,
            "source_semantics_pass": True,
            "historical_universe_risk_set_pass": historical_screen_membership_reconstructed,
            "historical_primary_security_identity_pass": historical_primary_security_identity_reconstructed,
            "diagnostic_only": not (
                historical_screen_membership_reconstructed
                and historical_primary_security_identity_reconstructed
            ),
            "no_parameter_tuning": True,
            "candidate_pass": a1_gate,
        },
        "input_sources": {
            "security_master": _source_manifest([security_master]),
            "market": _source_manifest(market_paths),
            "period_matrix": _source_manifest(period_paths),
            "transition_fundamentals": _source_manifest(transition_paths),
            "official_nyfed_sofr": _source_manifest([sofr_raw]),
            "historical_risk_set": (
                inherited_risk_set_sources
                if stage == "A2"
                else (
                    None
                    if risk_set is None
                    else {
                        "membership": _source_manifest([risk_set.membership_path]),
                        "receipt": _source_manifest([risk_set.receipt_path]),
                    }
                )
            ),
            "historical_security_master_receipt": (
                inherited_historical_security_master_receipt_sources
                if stage == "A2"
                else (
                    None
                    if historical_security_master is None
                    else _source_manifest([historical_security_master.receipt_path])
                )
            ),
        },
        "replay_metadata": replay_metadata,
    }
    report["report_content_hash"] = _canonical_json_hash(report)
    return report


def run_stage(args: argparse.Namespace) -> dict[str, Any]:
    risk_set: HistoricalRiskSet | None = None
    historical_security_master: HistoricalSecurityMaster | None = None
    inherited_source_cohort: dict[str, Any] | None = None
    inherited_risk_set_sources: dict[str, Any] | None = None
    inherited_historical_security_master_receipt_sources: list[dict[str, Any]] | None = None
    expected_source_entity_ids: list[str] | None = None
    required: list[str] | None = None
    freeze_payload: dict[str, Any] | None = None
    query_lock_path: Path | None = None
    query_receipt_path: Path | None = None
    if args.stage == "A1":
        risk_set = _load_optional_risk_set(
            getattr(args, "risk_set_membership", None),
            getattr(args, "risk_set_receipt", None),
            expected_as_of_date=args.start,
        )
        historical_security_master = _load_optional_historical_security_master(
            args.security_master,
            getattr(args, "historical_security_master_receipt", None),
            risk_set=risk_set,
            expected_as_of_date=args.start,
        )
    else:
        if getattr(args, "risk_set_membership", None) is not None or getattr(args, "risk_set_receipt", None) is not None:
            raise ValueError("a2_risk_set_must_be_inherited_from_freeze")
        if getattr(args, "historical_security_master_receipt", None) is not None:
            raise ValueError("a2_historical_security_master_receipt_must_be_inherited_from_freeze")
    if args.stage == "A2":
        if args.freeze is None:
            raise ValueError("a2_freeze_required")
        freeze_payload = verify_freeze(args.freeze)
        expected_source_entity_ids = [str(value) for value in freeze_payload["frozen_source_entity_ids"]]
        required = [str(value) for value in freeze_payload.get("frozen_security_ids") or []]
        if not required or len(required) != len(set(required)):
            raise ValueError("a2_frozen_security_ids_invalid")
        inherited_source_cohort = dict(freeze_payload["source_cohort"])
        inherited_risk_set_sources = dict(freeze_payload["historical_risk_set_sources"])
        inherited_historical_security_master_receipt_sources = list(
            freeze_payload["historical_security_master_receipt_sources"]
        )
        _assert_file_manifest(
            args.security_master,
            freeze_payload["frozen_security_master"],
            label="a2_frozen_security_master",
        )
        expected_window = freeze_payload["a2_window"]
        if expected_window != {"start": args.start, "end": args.end}:
            raise ValueError("a2_window_does_not_match_freeze")
        bound_paths = freeze_payload.get("a2_paths") or {}
        expected_result = Path(str(bound_paths.get("result") or ""))
        expected_evidence_root = Path(str(bound_paths.get("evidence_root") or ""))
        query_lock_path = Path(str(bound_paths.get("query_lock") or ""))
        query_receipt_path = Path(str(bound_paths.get("query_receipt") or ""))
        if not all(str(path) for path in (expected_result, expected_evidence_root, query_lock_path, query_receipt_path)):
            raise ValueError("a2_freeze_paths_missing")
        if args.out.resolve() != expected_result.resolve():
            raise ValueError("a2_result_path_does_not_match_freeze")
        if args.evidence_root.resolve() != expected_evidence_root.resolve():
            raise ValueError("a2_evidence_root_does_not_match_freeze")
        _assert_a2_capture_after_freeze(args.period_part, args.transition_part, freeze_payload["created_at_utc"])
        if args.out.exists() or query_lock_path.exists() or query_receipt_path.exists():
            raise FileExistsError("a2_query_already_consumed")
        if args.evidence_root.exists() and any(args.evidence_root.iterdir()):
            raise FileExistsError("a2_evidence_root_not_empty")
        query_lock = {
            "schema_version": QUERY_LOCK_SCHEMA,
            "created_at_utc": utc_now_text(),
            "freeze_path": args.freeze.resolve().as_posix(),
            "freeze_sha256": _sha256_file(args.freeze),
            "a2_window": expected_window,
            "result_path": args.out.resolve().as_posix(),
            "evidence_root": args.evidence_root.resolve().as_posix(),
            "source_cohort": inherited_source_cohort,
            "frozen_source_entity_count": len(expected_source_entity_ids),
            "frozen_active_security_count": len(required),
            "frozen_security_ids": required,
            "input_sources": {
                "security_master": _source_manifest([args.security_master]),
                "market": _source_manifest(args.market_part),
                "period_matrix": _source_manifest(args.period_part),
                "transition_fundamentals": _source_manifest(args.transition_part),
                "official_nyfed_sofr": _source_manifest([args.sofr_raw]),
                "historical_risk_set": freeze_payload["historical_risk_set_sources"],
                "historical_security_master_receipt": freeze_payload[
                    "historical_security_master_receipt_sources"
                ],
            },
            "evaluation_query_count_committed": 1,
            "second_evaluation_forbidden": True,
            "financial_alpha_evidence": 0,
        }
        _atomic_json(query_lock, query_lock_path, refuse_existing=True)

    report = _run_window(
        stage=args.stage,
        security_master=args.security_master,
        market_paths=args.market_part,
        period_paths=args.period_part,
        transition_paths=args.transition_part,
        sofr_raw=args.sofr_raw,
        start=args.start,
        end=args.end,
        evidence_root=args.evidence_root,
        risk_set=risk_set,
        historical_security_master=historical_security_master,
        inherited_source_cohort=inherited_source_cohort,
        inherited_risk_set_sources=inherited_risk_set_sources,
        inherited_historical_security_master_receipt_sources=(
            inherited_historical_security_master_receipt_sources
        ),
        expected_source_entity_ids=expected_source_entity_ids,
        required_security_ids=required,
    )
    if args.stage == "A2" and freeze_payload is not None and query_lock_path is not None:
        report["a2_query_meter"] = {
            "evaluation_query_count": 1,
            "implementation_freeze_sha256": _sha256_file(args.freeze),
            "implementation_freeze_created_at_utc": freeze_payload["created_at_utc"],
            "query_lock_path": query_lock_path.resolve().as_posix(),
            "query_lock_sha256": _sha256_file(query_lock_path),
            "heldout_pit_capture_after_freeze": True,
            "second_evaluation_forbidden": True,
        }
        report.pop("report_content_hash", None)
        report["report_content_hash"] = _canonical_json_hash(report)
    _atomic_json(report, args.out, refuse_existing=(args.stage == "A2" or args.refuse_existing))
    if args.stage == "A2" and query_lock_path is not None and query_receipt_path is not None:
        receipt = {
            "schema_version": QUERY_RECEIPT_SCHEMA,
            "created_at_utc": utc_now_text(),
            "evaluation_query_count": 1,
            "query_lock_path": query_lock_path.resolve().as_posix(),
            "query_lock_sha256": _sha256_file(query_lock_path),
            "result_path": args.out.resolve().as_posix(),
            "result_sha256": _sha256_file(args.out),
            "freeze_path": args.freeze.resolve().as_posix(),
            "freeze_sha256": _sha256_file(args.freeze),
            "financial_alpha_evidence": 0,
        }
        _atomic_json(receipt, query_receipt_path, refuse_existing=True)
    print(json.dumps({
        "status": f"{args.stage}_HISTORICAL_PIT_RUN_COMPLETE",
        "out": args.out.resolve().as_posix(),
        "sha256": _sha256_file(args.out),
        "trading_days": report["window"]["trading_days"],
        "security_count": report["security_count"],
        "financial_alpha_evidence": 0,
    }, indent=2, sort_keys=True))
    return report


def create_freeze(args: argparse.Namespace) -> dict[str, Any]:
    if not args.a1_report.is_file():
        raise FileNotFoundError(args.a1_report)
    a1 = json.loads(args.a1_report.read_text(encoding="utf-8"))
    _verify_report_content_hash(a1)
    gate = a1.get("a1_minimum_gate") or {}
    source_cohort = a1.get("source_cohort") or {}
    if a1.get("schema_version") != REPORT_SCHEMA or a1.get("stage") != "A1":
        raise ValueError("a1_report_identity_invalid_cannot_freeze_a2")
    if a1.get("financial_alpha_evidence") != 0:
        raise ValueError("a1_report_financial_alpha_evidence_invalid")
    if a1.get("evidence_classification") != A1_ADMITTED_CLASSIFICATION:
        raise ValueError("a1_not_admitted_historical_pit_cannot_freeze_a2")
    if source_cohort.get("historical_screen_membership_reconstructed") is not True:
        raise ValueError("a1_historical_universe_not_reconstructed_cannot_freeze_a2")
    if source_cohort.get("historical_primary_security_identity_reconstructed") is not True:
        raise ValueError("a1_historical_primary_security_not_reconstructed_cannot_freeze_a2")
    if gate.get("historical_universe_risk_set_pass") is not True:
        raise ValueError("a1_historical_universe_gate_not_passed_cannot_freeze_a2")
    if gate.get("historical_primary_security_identity_pass") is not True:
        raise ValueError("a1_historical_primary_security_gate_not_passed_cannot_freeze_a2")
    if gate.get("source_semantics_pass") is not True:
        raise ValueError("a1_source_semantics_gate_not_passed_cannot_freeze_a2")
    if gate.get("candidate_pass") is not True:
        raise ValueError("a1_candidate_gate_not_passed_cannot_freeze_a2")
    source_entity_ids = [str(value) for value in a1.get("source_entity_ids") or []]
    if not source_entity_ids or len(source_entity_ids) != len(set(source_entity_ids)):
        raise ValueError("a1_source_entity_ids_invalid_cannot_freeze_a2")
    input_sources = a1.get("input_sources") or {}
    security_master_sources = input_sources.get("security_master") or []
    if len(security_master_sources) != 1:
        raise ValueError("a1_security_master_source_invalid_cannot_freeze_a2")
    historical_risk_set_sources = input_sources.get("historical_risk_set")
    if not isinstance(historical_risk_set_sources, dict):
        raise ValueError("a1_historical_risk_set_sources_missing_cannot_freeze_a2")
    if not historical_risk_set_sources.get("membership") or not historical_risk_set_sources.get("receipt"):
        raise ValueError("a1_historical_risk_set_sources_missing_cannot_freeze_a2")
    historical_security_master_receipt_sources = input_sources.get("historical_security_master_receipt") or []
    if len(historical_security_master_receipt_sources) != 1:
        raise ValueError("a1_historical_security_master_receipt_missing_cannot_freeze_a2")
    implementation = []
    for relative in FROZEN_IMPLEMENTATION_PATHS:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        implementation.append({"path": relative, "sha256": _sha256_file(path), "bytes": path.stat().st_size})
    a2_root = args.out.parent.resolve()
    a2_paths = {
        "result": (a2_root / "a2_result.json").as_posix(),
        "evidence_root": (a2_root / "evidence").as_posix(),
        "query_lock": (a2_root / "a2_query_lock.json").as_posix(),
        "query_receipt": (a2_root / "a2_query_receipt.json").as_posix(),
    }
    payload = {
        "schema_version": FREEZE_SCHEMA,
        "created_at_utc": utc_now_text(),
        "financial_alpha_evidence": 0,
        "prospective_authority_changed": False,
        "contract_hash": DEFAULT_CONTRACT.contract_hash,
        "mutation_hash": DEFAULT_MUTATION.manifest_hash,
        "a1_report": {
            "path": args.a1_report.resolve().as_posix(),
            "sha256": _sha256_file(args.a1_report),
            "content_hash": a1.get("report_content_hash"),
        },
        "source_cohort": source_cohort,
        "frozen_source_entity_ids": source_entity_ids,
        "frozen_security_master": security_master_sources[0],
        "historical_risk_set_sources": historical_risk_set_sources,
        "historical_security_master_receipt_sources": historical_security_master_receipt_sources,
        "a1_active_security_ids": list(a1["security_ids"]),
        "frozen_security_ids": list(a1["security_ids"]),
        "a2_window": {"start": args.a2_start, "end": args.a2_end},
        "a2_paths": a2_paths,
        "implementation": implementation,
        "query_law": {
            "heldout_pit_fundamental_capture_must_occur_after_freeze": True,
            "one_controlled_a2_evaluation": True,
            "query_lock_written_before_outcome_evaluation": True,
            "second_a2_evaluation_forbidden": True,
            "preexisting_market_custody_allowed": True,
            "historical_results_cannot_change_financial_alpha_evidence": True,
        },
    }
    payload["freeze_content_hash"] = _canonical_json_hash(payload)
    _atomic_json(payload, args.out, refuse_existing=True)
    print(json.dumps({
        "status": "A1_IMPLEMENTATION_FROZEN_FOR_A2",
        "out": args.out.resolve().as_posix(),
        "sha256": _sha256_file(args.out),
        "frozen_source_entity_count": len(payload["frozen_source_entity_ids"]),
        "a1_active_security_count": len(payload["a1_active_security_ids"]),
        "financial_alpha_evidence": 0,
    }, indent=2, sort_keys=True))
    return payload


def verify_freeze(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    supplied_freeze_hash = str(payload.get("freeze_content_hash") or "")
    freeze_body = dict(payload)
    freeze_body.pop("freeze_content_hash", None)
    if not supplied_freeze_hash or supplied_freeze_hash != _canonical_json_hash(freeze_body):
        raise ValueError("a2_freeze_content_hash_invalid")
    if payload.get("schema_version") != FREEZE_SCHEMA:
        raise ValueError("a2_freeze_schema_invalid")
    if payload.get("contract_hash") != DEFAULT_CONTRACT.contract_hash:
        raise ValueError("a2_freeze_contract_drift")
    if payload.get("mutation_hash") != DEFAULT_MUTATION.manifest_hash:
        raise ValueError("a2_freeze_mutation_drift")
    source_cohort = payload.get("source_cohort") or {}
    if source_cohort.get("historical_screen_membership_reconstructed") is not True:
        raise ValueError("a2_freeze_source_cohort_invalid")
    if source_cohort.get("historical_primary_security_identity_reconstructed") is not True:
        raise ValueError("a2_freeze_historical_primary_security_invalid")
    if source_cohort.get("current_screen_conditioned") is not False:
        raise ValueError("a2_freeze_source_cohort_current_conditioning_invalid")
    if source_cohort.get("current_primary_security_conditioned") is not False:
        raise ValueError("a2_freeze_primary_security_current_conditioning_invalid")
    if source_cohort.get("risk_set_mode") != HISTORICAL_SCREEN_FREEZE_MODE:
        raise ValueError("a2_freeze_risk_set_mode_invalid")
    source_entity_ids = [str(value) for value in payload.get("frozen_source_entity_ids") or []]
    if not source_entity_ids or len(source_entity_ids) != len(set(source_entity_ids)):
        raise ValueError("a2_freeze_source_entity_ids_invalid")
    frozen_security_master = payload.get("frozen_security_master")
    if not isinstance(frozen_security_master, dict):
        raise ValueError("a2_freeze_security_master_invalid")
    historical_risk_set_sources = payload.get("historical_risk_set_sources")
    if not isinstance(historical_risk_set_sources, dict):
        raise ValueError("a2_freeze_historical_risk_set_sources_invalid")
    if not historical_risk_set_sources.get("membership") or not historical_risk_set_sources.get("receipt"):
        raise ValueError("a2_freeze_historical_risk_set_sources_invalid")
    historical_security_master_receipt_sources = payload.get("historical_security_master_receipt_sources") or []
    if len(historical_security_master_receipt_sources) != 1:
        raise ValueError("a2_freeze_historical_security_master_receipt_sources_invalid")
    paths = payload.get("a2_paths") or {}
    if set(paths) != {"result", "evidence_root", "query_lock", "query_receipt"}:
        raise ValueError("a2_freeze_paths_invalid")
    if any(not str(value).strip() for value in paths.values()):
        raise ValueError("a2_freeze_paths_invalid")
    for entry in payload.get("implementation", []):
        candidate = ROOT / str(entry["path"])
        if _sha256_file(candidate) != str(entry["sha256"]):
            raise ValueError(f"a2_frozen_implementation_drift:{entry['path']}")
    a1_path = Path(payload["a1_report"]["path"])
    if _sha256_file(a1_path) != str(payload["a1_report"]["sha256"]):
        raise ValueError("a2_frozen_a1_report_drift")
    a1 = json.loads(a1_path.read_text(encoding="utf-8"))
    _verify_report_content_hash(a1)
    if a1.get("evidence_classification") != A1_ADMITTED_CLASSIFICATION:
        raise ValueError("a2_frozen_a1_not_admitted")
    if str(a1.get("report_content_hash") or "") != str(payload["a1_report"].get("content_hash") or ""):
        raise ValueError("a2_frozen_a1_content_hash_drift")
    if [str(value) for value in a1.get("source_entity_ids") or []] != source_entity_ids:
        raise ValueError("a2_frozen_source_entity_ids_drift")
    a1_sources = a1.get("input_sources") or {}
    a1_security_master = a1_sources.get("security_master") or []
    if len(a1_security_master) != 1 or a1_security_master[0] != frozen_security_master:
        raise ValueError("a2_frozen_security_master_manifest_drift")
    if a1_sources.get("historical_risk_set") != historical_risk_set_sources:
        raise ValueError("a2_frozen_historical_risk_set_manifest_drift")
    if a1_sources.get("historical_security_master_receipt") != historical_security_master_receipt_sources:
        raise ValueError("a2_frozen_historical_security_master_receipt_manifest_drift")
    primary_receipt_manifest = historical_security_master_receipt_sources[0]
    _assert_file_manifest(
        Path(primary_receipt_manifest["path"]),
        primary_receipt_manifest,
        label="a2_frozen_historical_security_master_receipt",
    )
    if a1.get("source_cohort") != source_cohort:
        raise ValueError("a2_frozen_source_cohort_drift")
    a1_security_ids = [str(value) for value in a1.get("security_ids") or []]
    active_security_ids = [str(value) for value in payload.get("a1_active_security_ids") or []]
    frozen_security_ids = [str(value) for value in payload.get("frozen_security_ids") or []]
    if not a1_security_ids or len(a1_security_ids) != len(set(a1_security_ids)):
        raise ValueError("a2_frozen_a1_security_ids_invalid")
    if active_security_ids != a1_security_ids or frozen_security_ids != a1_security_ids:
        raise ValueError("a2_frozen_security_ids_drift")
    return payload


def _assert_a2_capture_after_freeze(period_paths: list[Path], transition_paths: list[Path], freeze_time: str) -> None:
    freeze_ts = pd.Timestamp(freeze_time)
    for frame in (_read_csvs(period_paths), _read_csvs(transition_paths)):
        if "retrieved_at_utc" not in frame.columns:
            raise ValueError("a2_capture_retrieval_timestamp_missing")
        retrieved = pd.to_datetime(frame["retrieved_at_utc"], utc=True, errors="raise")
        if (retrieved <= freeze_ts).any():
            raise ValueError("a2_heldout_pit_capture_not_after_freeze")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan-fundamentals")
    plan.add_argument("--security-master", type=Path, required=True)
    plan.add_argument("--market-part", action="append", type=Path, required=True)
    plan.add_argument("--start", required=True)
    plan.add_argument("--end", required=True)
    plan.add_argument("--risk-set-membership", type=Path)
    plan.add_argument("--risk-set-receipt", type=Path)
    plan.add_argument("--historical-security-master-receipt", type=Path)
    plan.add_argument("--out", type=Path, required=True)
    plan.add_argument("--refuse-existing", action="store_true")

    transitions = sub.add_parser("plan-transitions")
    transitions.add_argument("--period-part", action="append", type=Path, required=True)
    transitions.add_argument("--out", type=Path, required=True)
    transitions.add_argument("--refuse-existing", action="store_true")

    run = sub.add_parser("run")
    run.add_argument("--stage", choices=("A1", "A2"), required=True)
    run.add_argument("--security-master", type=Path, required=True)
    run.add_argument("--market-part", action="append", type=Path, required=True)
    run.add_argument("--period-part", action="append", type=Path, required=True)
    run.add_argument("--transition-part", action="append", type=Path, required=True)
    run.add_argument("--sofr-raw", type=Path, required=True)
    run.add_argument("--start", required=True)
    run.add_argument("--end", required=True)
    run.add_argument("--evidence-root", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--freeze", type=Path)
    run.add_argument("--risk-set-membership", type=Path)
    run.add_argument("--risk-set-receipt", type=Path)
    run.add_argument("--historical-security-master-receipt", type=Path)
    run.add_argument("--refuse-existing", action="store_true")

    freeze = sub.add_parser("freeze-a2")
    freeze.add_argument("--a1-report", type=Path, required=True)
    freeze.add_argument("--a2-start", required=True)
    freeze.add_argument("--a2-end", required=True)
    freeze.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "plan-fundamentals":
        plan_fundamentals(args)
    elif args.command == "plan-transitions":
        plan_transitions(args)
    elif args.command == "run":
        run_stage(args)
    elif args.command == "freeze-a2":
        create_freeze(args)
    else:  # pragma: no cover
        raise AssertionError(args.command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
