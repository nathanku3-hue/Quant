"""One canonical five-arm AOV-0 experiment and immutable prospective seal."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from core.gv_fs0_canonical import domain_hash
from research.aov0.contracts import AOV0Contract, DEFAULT_CONTRACT
from research.aov0.cube import VerticalCube
from research.aov0.dag import DagRunResult, HashDagCache, run_policy_dag
from research.aov0.policy import DEFAULT_MUTATION, MutationManifest, assert_rule100_equivalence
from research.backtest_runner import ResearchBacktestResult, run_research_backtest
from research.strategy_cartridge import StrategyCartridge


EXPERIMENT_SCHEMA = "aov0_five_arm_experiment_v1"
SEAL_SCHEMA = "aov0_prospective_seal_v1"


@dataclass(frozen=True)
class FiveArmExperimentResult:
    experiment_id: str
    dag: DagRunResult
    runs: dict[str, ResearchBacktestResult]
    arm_metrics: dict[str, dict[str, Any]]
    experiment_manifest: Path


@dataclass(frozen=True)
class ProspectiveSeal:
    seal_id: str
    path: Path
    payload: dict[str, Any]


def run_five_arm_experiment(
    *,
    rule100_weights: pd.DataFrame,
    returns_df: pd.DataFrame,
    economic_cash_returns: pd.Series,
    cube: VerticalCube,
    pit_eligibility_provider,
    output_root: Path,
    turnover_cost_rate: float = 0.001,
    contract: AOV0Contract = DEFAULT_CONTRACT,
    mutation: MutationManifest = DEFAULT_MUTATION,
    cache: HashDagCache | None = None,
) -> FiveArmExperimentResult:
    assert_rule100_equivalence(rule100_weights, cube, contract=contract)
    dag = run_policy_dag(
        rule100_weights,
        cube,
        contract=contract,
        mutation=mutation,
        cache=cache,
    )
    returns = returns_df.copy()
    returns.index = pd.DatetimeIndex(pd.to_datetime(returns.index)).normalize()
    target_dates = dag.rule100.index
    if not returns.index.equals(target_dates):
        raise ValueError("aov0_experiment_return_calendar_mismatch")

    input_identity = _canonical_hash_value({
        "schema_version": EXPERIMENT_SCHEMA,
        "contract_hash": contract.contract_hash,
        "cube_hash": cube.cube_hash,
        "source_hash": cube.source_hash,
        "formula_hash": cube.formula_hash,
        "mutation_hash": mutation.manifest_hash,
        "rule100_hash": dag.node_hashes["rule100"],
        "parent_hash": dag.node_hashes["parent"],
        "child_hash": dag.node_hashes["child"],
        "returns_hash": _frame_hash(returns),
        "economic_cash_hash": _series_hash(economic_cash_returns),
        "turnover_cost_rate": float(turnover_cost_rate),
        "inference": {
            "primary_endpoint": contract.inference_primary_endpoint,
            "hac_lag_weekly": contract.inference_hac_lag_weekly,
            "block_bootstrap_expected_weeks": contract.inference_block_bootstrap_expected_weeks,
        },
        "insurance": {
            "endpoint": f"CVaR_{contract.cvar_level:.2f}",
            "materiality_floor_ratio": contract.insurance_materiality_floor_ratio,
            "premium_ceiling_annual_return": contract.insurance_premium_ceiling_annual_return,
        },
    })
    experiment_id = domain_hash("AOV0:FIVE_ARM_EXPERIMENT:V1", input_identity)
    benchmark_policy = {
        "primary": "pit_equal_weight_eligible_universe",
        "required": {
            "cash": {"kind": "implicit_zero_return_cash"},
            "pit_equal_weight_eligible_universe": {"kind": "pit_equal_weight_match_strategy_schedule"},
            "economic_cash": {"kind": "economic_cash_total_return"},
        },
    }
    run_root = Path(output_root) / "runs"
    common_kwargs = {
        "returns_df": returns,
        "economic_cash_returns": economic_cash_returns,
        "input_signatures": input_identity,
        "pit_membership_proof": {
            "proof_type": "aov0_date_local_permno_universe",
            "contract_hash": contract.contract_hash,
            "cube_hash": cube.cube_hash,
        },
        "leakage_checks": {
            "pit_inputs_only": True,
            "permanent_ids_only": True,
            "same_return_authority": True,
            "same_decision_schedule": True,
        },
        "pit_eligibility_provider": pit_eligibility_provider,
        "emit_artifacts": True,
    }
    target_by_arm = {
        "rule100": dag.rule100,
        "parent": dag.parent,
        "child": dag.child,
    }
    runs: dict[str, ResearchBacktestResult] = {}
    for arm, weights in target_by_arm.items():
        cartridge = StrategyCartridge(
            strategy_id=f"aov0_{arm}",
            strategy_version="1.0.0",
            strategy_role="diagnostic_lifecycle_policy" if arm == "rule100" else "signal_strategy",
            universe_mode=contract.universe_rule,
            input_loader_name="AOV0_VERTICAL_CUBE_SLICE_V0",
            rebalance_schedule="match_rule100_target_change",
            execution_lag=contract.execution_lag,
            turnover_cost_rate=turnover_cost_rate,
            benchmark_policy=benchmark_policy,
            start_date=target_dates.min().date().isoformat(),
            end_date=target_dates.max().date().isoformat(),
            output_dir=run_root,
            min_required_trading_days=252,
            hypothesis="AOV-0 mechanical organism; historical output remains exploratory.",
            owner="AOV0",
            metadata={"experiment_id": experiment_id, "contract_hash": contract.contract_hash},
        )
        runs[arm] = run_research_backtest(
            cartridge=cartridge,
            target_weights=weights,
            run_id=f"{experiment_id[:16]}_{arm}",
            **common_kwargs,
        )
        if runs[arm].status.value == "blocked":
            raise ValueError(f"aov0_arm_blocked:{arm}:{runs[arm].gate_results['failures']}")

    reference_benchmarks = runs["rule100"].benchmark_metrics
    for arm in ("parent", "child"):
        for benchmark in ("pit_equal_weight_eligible_universe", "economic_cash"):
            if runs[arm].benchmark_metrics[benchmark] != reference_benchmarks[benchmark]:
                raise ValueError(f"aov0_benchmark_semantics_drift:{arm}:{benchmark}")

    arm_metrics = {
        "rule100": runs["rule100"].metrics,
        "parent": runs["parent"].metrics,
        "child": runs["child"].metrics,
        "pit_equal_weight": reference_benchmarks["pit_equal_weight_eligible_universe"],
        "economic_cash": reference_benchmarks["economic_cash"],
    }
    manifest_payload = {
        **input_identity,
        "experiment_id": experiment_id,
        "evidence_level": "A1_EXPLORATORY_MECHANICAL_ONLY",
        "alpha_evidence": 0,
        "arms": arm_metrics,
        "run_evidence_manifests": {
            arm: _artifact_identity(Path(result.artifacts["evidence_manifest.json"]))
            for arm, result in runs.items()
        },
        "dag": {
            "node_hashes": dag.node_hashes,
            "cache_hits": dag.cache_hits,
            "cache_misses": dag.cache_misses,
        },
    }
    experiment_dir = Path(output_root) / "experiments"
    experiment_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = experiment_dir / f"{experiment_id}.json"
    if manifest_path.exists():
        raise FileExistsError(f"aov0_experiment_manifest_exists:{manifest_path}")
    _write_json_atomic(manifest_path, manifest_payload)
    return FiveArmExperimentResult(
        experiment_id=experiment_id,
        dag=dag,
        runs=runs,
        arm_metrics=arm_metrics,
        experiment_manifest=manifest_path,
    )


def seal_prospective_experiment(
    result: FiveArmExperimentResult,
    *,
    cube: VerticalCube,
    decision_cut_id: str,
    sealed_at: str,
    output_dir: Path,
    contract: AOV0Contract = DEFAULT_CONTRACT,
    mutation: MutationManifest = DEFAULT_MUTATION,
) -> ProspectiveSeal:
    sealed_ts = _utc(sealed_at)
    payload = {
        "schema_version": SEAL_SCHEMA,
        "experiment_id": result.experiment_id,
        "decision_cut_id": str(decision_cut_id),
        "sealed_at": sealed_ts.isoformat().replace("+00:00", "Z"),
        "outcome_open_not_before": (
            sealed_ts + timedelta(days=contract.sleeve_horizon_calendar_days)
        ).isoformat().replace("+00:00", "Z"),
        "outcome_status": "SEALED_NOT_OPENED",
        "outcome_data_loaded": False,
        "contract_hash": contract.contract_hash,
        "cube_hash": cube.cube_hash,
        "source_hash": cube.source_hash,
        "formula_hash": cube.formula_hash,
        "mutation_hash": mutation.manifest_hash,
        "arm_target_hashes": result.dag.node_hashes,
        "required_arms": ["rule100", "parent", "child", "pit_equal_weight", "economic_cash"],
        "return_authority": contract.total_return_authority,
        "economic_cash_contract": {
            "source": contract.economic_cash_source,
            "quote_convention": contract.economic_cash_quote_convention,
            "roll_policy": contract.economic_cash_roll_policy,
            "known_at_rule": contract.economic_cash_known_at_rule,
        },
        "evidence_level": "PROSPECTIVE_CLOCK_STARTED_ALPHA_EVIDENCE_0",
        "alpha_evidence": 0,
        "experiment_manifest": _artifact_identity(result.experiment_manifest),
    }
    seal_id = domain_hash("AOV0:PROSPECTIVE_SEAL:V1", payload)
    sealed_payload = {**payload, "seal_id": seal_id}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{seal_id}.json"
    if path.exists():
        raise FileExistsError(f"aov0_prospective_seal_exists:{path}")
    _write_json_atomic(path, sealed_payload)
    reopened = reopen_prospective_seal(path)
    if reopened["seal_id"] != seal_id:
        raise ValueError("aov0_prospective_seal_reopen_mismatch")
    return ProspectiveSeal(seal_id=seal_id, path=path, payload=reopened)


def reopen_prospective_seal(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != SEAL_SCHEMA:
        raise ValueError("aov0_prospective_seal_schema_invalid")
    if payload.get("outcome_data_loaded") is not False or payload.get("outcome_status") != "SEALED_NOT_OPENED":
        raise ValueError("aov0_prospective_outcome_opened_early")
    seal_id = payload.get("seal_id")
    body = {key: value for key, value in payload.items() if key != "seal_id"}
    expected = domain_hash("AOV0:PROSPECTIVE_SEAL:V1", body)
    if seal_id != expected:
        raise ValueError("aov0_prospective_seal_hash_mismatch")
    return payload


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _frame_hash(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(pd.util.hash_pandas_object(frame, index=True).to_numpy(dtype="uint64").tobytes())
    digest.update("|".join(str(column) for column in frame.columns).encode("utf-8"))
    return digest.hexdigest()


def _series_hash(series: pd.Series) -> str:
    frame = pd.DataFrame({str(series.name or "value"): series})
    return _frame_hash(frame)


def _artifact_identity(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"path": path.as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _canonical_hash_value(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, dict):
        return {str(key): _canonical_hash_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_hash_value(item) for item in value]
    return value


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
