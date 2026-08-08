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
from research.aov0.contracts import (
    AOV0Contract,
    DEFAULT_CONTRACT,
    validate_prospective_contract,
)
from research.aov0.cube import VerticalCube
from research.aov0.dag import DagRunResult, HashDagCache, run_policy_dag
from research.benchmarks import build_pit_equal_weight_benchmark, strategy_rebalance_dates
from research.aov0.policy import DEFAULT_MUTATION, MutationManifest, assert_rule100_equivalence
from research.backtest_runner import ResearchBacktestResult, run_research_backtest
from research.strategy_cartridge import StrategyCartridge


EXPERIMENT_SCHEMA = "aov0_five_arm_experiment_v1"
SEAL_SCHEMA = "aov0_prospective_seal_v3"
EXECUTABLE_MANIFEST_SCHEMA = "aov0_executable_byte_manifest_v1"
RETURN_INTERVAL_POLICY = "ATTRIBUTED_DAILY_TOTAL_RETURN_LEFT_ENDPOINT_GTE_EVALUATION_START"


@dataclass(frozen=True)
class FiveArmExperimentResult:
    experiment_id: str
    dag: DagRunResult
    runs: dict[str, ResearchBacktestResult]
    arm_metrics: dict[str, dict[str, Any]]
    current_target_date: str
    current_target_hashes: dict[str, str]
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
            "proof_type": "aov0_date_local_ciq_security_universe",
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
    current_date = pd.Timestamp(target_dates.max()).normalize()
    pit_equal_weight_targets = build_pit_equal_weight_benchmark(
        target_dates,
        dag.rule100.columns,
        pit_eligibility_provider,
        rebalance_dates=strategy_rebalance_dates(dag.rule100),
    )
    current_target_frames = {
        "rule100": dag.rule100.loc[[current_date]],
        "parent": dag.parent.loc[[current_date]],
        "child": dag.child.loc[[current_date]],
        "pit_equal_weight": pit_equal_weight_targets.loc[[current_date]],
        "economic_cash": pd.DataFrame(
            {"ECONOMIC_CASH": [1.0]}, index=pd.DatetimeIndex([current_date])
        ),
    }
    current_target_hashes = {
        arm: _frame_hash(frame)
        for arm, frame in current_target_frames.items()
    }
    current_target_vectors = {
        arm: _target_vector_payload(frame)
        for arm, frame in current_target_frames.items()
    }
    manifest_payload = {
        **input_identity,
        "experiment_id": experiment_id,
        "evidence_level": "A1_EXPLORATORY_MECHANICAL_ONLY",
        "financial_alpha_evidence": 0,
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
        "current_decision_targets": {
            "decision_target_date": current_date.date().isoformat(),
            "arm_target_hashes": current_target_hashes,
            "arm_target_vectors": current_target_vectors,
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
        current_target_date=current_date.date().isoformat(),
        current_target_hashes=current_target_hashes,
        experiment_manifest=manifest_path,
    )


def seal_prospective_experiment(
    result: FiveArmExperimentResult,
    *,
    cube: VerticalCube,
    decision_cut_binding: dict[str, Any],
    executable_manifest: Path,
    output_dir: Path,
    contract: AOV0Contract = DEFAULT_CONTRACT,
    mutation: MutationManifest = DEFAULT_MUTATION,
    sealed_at: datetime | None = None,
) -> ProspectiveSeal:
    validate_prospective_contract(contract)
    decision_cut_id = str(decision_cut_binding.get("decision_cut_id") or "").strip()
    cut_built_at = str(decision_cut_binding.get("cut_built_at") or "").strip()
    knowledge_cutoff = str(decision_cut_binding.get("knowledge_cutoff") or "").strip()
    evaluation_start = str(decision_cut_binding.get("evaluation_start") or "").strip()
    decision_target_date = str(decision_cut_binding.get("decision_target_date") or "").strip()
    if (
        not decision_cut_id
        or not cut_built_at
        or not knowledge_cutoff
        or not evaluation_start
        or decision_target_date != result.current_target_date
    ):
        raise ValueError("aov0_prospective_decision_cut_binding_invalid")
    knowledge_ts = _utc(knowledge_cutoff)
    cut_built_ts = _utc(cut_built_at)
    evaluation_start_ts = _utc(evaluation_start)
    sealed_ts = (sealed_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if not (knowledge_ts <= cut_built_ts <= sealed_ts < evaluation_start_ts):
        raise ValueError("aov0_prospective_seal_timing_invalid")
    executable_manifest = Path(executable_manifest)
    if not executable_manifest.is_file():
        raise FileNotFoundError(f"aov0_executable_manifest_missing:{executable_manifest}")
    payload = {
        "schema_version": SEAL_SCHEMA,
        "experiment_id": result.experiment_id,
        "decision_cut_id": decision_cut_id,
        "decision_cut_binding": decision_cut_binding,
        "sealed_at": sealed_ts.isoformat().replace("+00:00", "Z"),
        "evaluation_start": evaluation_start_ts.isoformat().replace("+00:00", "Z"),
        "sleeve_horizon_calendar_days": contract.sleeve_horizon_calendar_days,
        "return_interval_policy": RETURN_INTERVAL_POLICY,
        "outcome_open_not_before": (
            evaluation_start_ts + timedelta(days=contract.sleeve_horizon_calendar_days)
        ).isoformat().replace("+00:00", "Z"),
        "outcome_status": "SEALED_NOT_OPENED",
        "outcome_data_loaded": False,
        "contract_hash": contract.contract_hash,
        "cube_hash": cube.cube_hash,
        "source_hash": cube.source_hash,
        "formula_hash": cube.formula_hash,
        "mutation_hash": mutation.manifest_hash,
        "arm_history_node_hashes": result.dag.node_hashes,
        "current_decision_target_hashes": result.current_target_hashes,
        "required_arms": ["rule100", "parent", "child", "pit_equal_weight", "economic_cash"],
        "return_authority": contract.total_return_authority,
        "economic_cash_contract": {
            "source": contract.economic_cash_source,
            "quote_convention": contract.economic_cash_quote_convention,
            "roll_policy": contract.economic_cash_roll_policy,
            "known_at_rule": contract.economic_cash_known_at_rule,
        },
        "evidence_level": "PROSPECTIVE_SEAL_CANDIDATE_FINANCIAL_ALPHA_EVIDENCE_0",
        "financial_alpha_evidence": 0,
        "experiment_manifest": _artifact_identity(result.experiment_manifest),
        "executable_manifest": _artifact_identity(executable_manifest),
    }
    seal_id = domain_hash("AOV0:PROSPECTIVE_SEAL:V3", payload)
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
    if "prospective_clock_started" in payload:
        raise ValueError("aov0_prospective_seal_cannot_claim_clock_start")
    if payload.get("evidence_level") != "PROSPECTIVE_SEAL_CANDIDATE_FINANCIAL_ALPHA_EVIDENCE_0":
        raise ValueError("aov0_prospective_seal_evidence_level_invalid")
    if payload.get("return_interval_policy") != RETURN_INTERVAL_POLICY:
        raise ValueError("aov0_prospective_return_interval_policy_invalid")
    if payload.get("sleeve_horizon_calendar_days") != DEFAULT_CONTRACT.sleeve_horizon_calendar_days:
        raise ValueError("aov0_prospective_horizon_invalid")
    sealed_ts = _utc(str(payload.get("sealed_at") or ""))
    evaluation_start_ts = _utc(str(payload.get("evaluation_start") or ""))
    maturity_ts = _utc(str(payload.get("outcome_open_not_before") or ""))
    expected_maturity = evaluation_start_ts + timedelta(days=DEFAULT_CONTRACT.sleeve_horizon_calendar_days)
    if sealed_ts >= evaluation_start_ts:
        raise ValueError("aov0_prospective_seal_not_before_evaluation_start")
    if maturity_ts != expected_maturity:
        raise ValueError("aov0_prospective_outcome_maturity_invalid")
    seal_id = payload.get("seal_id")
    body = {key: value for key, value in payload.items() if key != "seal_id"}
    expected = domain_hash("AOV0:PROSPECTIVE_SEAL:V3", body)
    if seal_id != expected:
        raise ValueError("aov0_prospective_seal_hash_mismatch")
    return payload


def validate_attributed_return_intervals(
    intervals: pd.DataFrame,
    *,
    evaluation_start: str | datetime,
) -> None:
    required = {"interval_start", "interval_end"}
    if not isinstance(intervals, pd.DataFrame) or not required.issubset(intervals.columns):
        raise ValueError("aov0_attributed_return_interval_columns_required")
    if intervals.empty:
        return
    starts = pd.to_datetime(intervals["interval_start"], utc=True, errors="raise", format="mixed")
    ends = pd.to_datetime(intervals["interval_end"], utc=True, errors="raise", format="mixed")
    boundary = pd.Timestamp(evaluation_start)
    boundary = boundary.tz_localize("UTC") if boundary.tzinfo is None else boundary.tz_convert("UTC")
    if (starts < boundary).any():
        raise ValueError("aov0_attributed_return_interval_begins_before_evaluation_start")
    if (ends <= starts).any():
        raise ValueError("aov0_attributed_return_interval_order_invalid")


def _resolve_artifact_path(identity: dict[str, Any], *, repo_root: Path) -> Path:
    raw_path = identity.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("aov0_full_reopen_artifact_path_invalid")
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path(repo_root) / path
    return path.resolve()


def _verify_artifact_identity(identity: dict[str, Any], *, repo_root: Path) -> Path:
    if not isinstance(identity, dict) or set(identity) != {"path", "bytes", "sha256"}:
        raise ValueError("aov0_full_reopen_artifact_identity_invalid")
    path = _resolve_artifact_path(identity, repo_root=repo_root)
    if not path.is_file():
        raise FileNotFoundError(f"aov0_full_reopen_artifact_missing:{path}")
    raw = path.read_bytes()
    if len(raw) != int(identity["bytes"]):
        raise ValueError(f"aov0_full_reopen_artifact_size_mismatch:{path}")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != str(identity["sha256"]):
        raise ValueError(f"aov0_full_reopen_artifact_hash_mismatch:{path}")
    return path


def _verify_executable_manifest(identity: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    manifest_path = _verify_artifact_identity(identity, repo_root=repo_root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != EXECUTABLE_MANIFEST_SCHEMA:
        raise ValueError("aov0_full_reopen_executable_manifest_schema_invalid")
    manifest_id = str(manifest.get("manifest_id") or "")
    body = {key: value for key, value in manifest.items() if key != "manifest_id"}
    files = body.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("aov0_full_reopen_executable_manifest_files_invalid")
    for relative, expected in files.items():
        if not isinstance(expected, dict) or set(expected) != {"bytes", "sha256"}:
            raise ValueError("aov0_full_reopen_executable_file_identity_invalid")
        path = (Path(repo_root) / str(relative)).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"aov0_full_reopen_executable_file_missing:{relative}")
        raw = path.read_bytes()
        if len(raw) != int(expected["bytes"]) or hashlib.sha256(raw).hexdigest() != str(expected["sha256"]):
            raise ValueError(f"aov0_full_reopen_executable_file_mismatch:{relative}")
    interpreter = body.get("interpreter")
    if not isinstance(interpreter, dict) or set(interpreter) != {"path", "bytes", "sha256"}:
        raise ValueError("aov0_full_reopen_interpreter_identity_invalid")
    interpreter_path = Path(str(interpreter["path"]))
    if not interpreter_path.is_file():
        raise FileNotFoundError(f"aov0_full_reopen_interpreter_missing:{interpreter_path}")
    interpreter_raw = interpreter_path.read_bytes()
    if (
        len(interpreter_raw) != int(interpreter["bytes"])
        or hashlib.sha256(interpreter_raw).hexdigest() != str(interpreter["sha256"])
    ):
        raise ValueError("aov0_full_reopen_interpreter_mismatch")
    expected_manifest_id = domain_hash("AOV0:EXECUTABLE_BYTE_MANIFEST:V1", body)
    if manifest_id != expected_manifest_id:
        raise ValueError("aov0_full_reopen_executable_manifest_id_mismatch")
    return manifest


def _verify_evidence_manifest(identity: dict[str, Any], *, repo_root: Path) -> None:
    manifest_path = _verify_artifact_identity(identity, repo_root=repo_root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "research_evidence_manifest_v1":
        raise ValueError("aov0_full_reopen_evidence_manifest_schema_invalid")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("aov0_full_reopen_evidence_manifest_files_invalid")
    for filename, expected in files.items():
        if not isinstance(expected, dict) or set(expected) != {"bytes", "sha256"}:
            raise ValueError("aov0_full_reopen_evidence_file_identity_invalid")
        artifact = manifest_path.parent / str(filename)
        if not artifact.is_file():
            raise FileNotFoundError(f"aov0_full_reopen_evidence_file_missing:{artifact}")
        raw = artifact.read_bytes()
        if len(raw) != int(expected["bytes"]) or hashlib.sha256(raw).hexdigest() != str(expected["sha256"]):
            raise ValueError(f"aov0_full_reopen_evidence_file_mismatch:{artifact}")


def reopen_prospective_seal_full_chain(path: Path, *, repo_root: Path) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    raw_payload = json.loads(Path(path).read_text(encoding="utf-8"))
    _verify_executable_manifest(raw_payload.get("executable_manifest"), repo_root=repo_root)
    payload = reopen_prospective_seal(path)

    binding = payload.get("decision_cut_binding")
    if not isinstance(binding, dict):
        raise ValueError("aov0_full_reopen_decision_cut_binding_invalid")
    cut_path = _verify_artifact_identity(binding.get("decision_cut_artifact"), repo_root=repo_root)
    cut = json.loads(cut_path.read_text(encoding="utf-8"))
    bound_fields = (
        "schema_version",
        "decision_cut_id",
        "knowledge_cutoff",
        "cut_built_at",
        "decision_target_date",
        "evaluation_start",
        "execution_calendar_id",
        "contract_hash",
        "universe_hash",
        "source_receipts",
    )
    for field in bound_fields:
        if cut.get(field) != binding.get(field):
            raise ValueError(f"aov0_full_reopen_decision_cut_binding_mismatch:{field}")
    cut_hashes = cut.get("input_sha256")
    inputs = binding.get("inputs")
    if not isinstance(cut_hashes, dict) or not isinstance(inputs, dict) or set(cut_hashes) != set(inputs):
        raise ValueError("aov0_full_reopen_input_binding_set_invalid")
    for name, identity in inputs.items():
        _verify_artifact_identity(identity, repo_root=repo_root)
        if str(identity["sha256"]) != str(cut_hashes[name]):
            raise ValueError(f"aov0_full_reopen_decision_cut_input_hash_mismatch:{name}")

    experiment_path = _verify_artifact_identity(payload.get("experiment_manifest"), repo_root=repo_root)
    experiment = json.loads(experiment_path.read_text(encoding="utf-8"))
    if experiment.get("experiment_id") != payload.get("experiment_id"):
        raise ValueError("aov0_full_reopen_experiment_id_mismatch")
    for field in ("contract_hash", "cube_hash", "source_hash", "formula_hash", "mutation_hash"):
        if experiment.get(field) != payload.get(field):
            raise ValueError(f"aov0_full_reopen_experiment_binding_mismatch:{field}")
    current = experiment.get("current_decision_targets")
    if not isinstance(current, dict):
        raise ValueError("aov0_full_reopen_current_targets_invalid")
    if current.get("decision_target_date") != binding.get("decision_target_date"):
        raise ValueError("aov0_full_reopen_target_date_mismatch")
    hashes = current.get("arm_target_hashes")
    vectors = current.get("arm_target_vectors")
    if hashes != payload.get("current_decision_target_hashes"):
        raise ValueError("aov0_full_reopen_target_hash_binding_mismatch")
    if not isinstance(vectors, dict) or set(vectors) != set(payload.get("required_arms") or []):
        raise ValueError("aov0_full_reopen_target_vector_set_invalid")
    for arm, vector_payload in vectors.items():
        frame = _target_frame_from_payload(vector_payload)
        if _frame_hash(frame) != str(hashes[arm]):
            raise ValueError(f"aov0_full_reopen_target_vector_hash_mismatch:{arm}")

    run_manifests = experiment.get("run_evidence_manifests")
    if not isinstance(run_manifests, dict) or set(run_manifests) != {"rule100", "parent", "child"}:
        raise ValueError("aov0_full_reopen_run_evidence_manifest_set_invalid")
    for identity in run_manifests.values():
        _verify_evidence_manifest(identity, repo_root=repo_root)

    return {
        "status": "FULL_CHAIN_REOPEN_VERIFIED",
        "seal_id": payload["seal_id"],
        "sealed_at": payload["sealed_at"],
        "decision_cut_id": payload["decision_cut_id"],
        "decision_target_date": binding["decision_target_date"],
        "evaluation_start": binding["evaluation_start"],
        "outcome_open_not_before": payload["outcome_open_not_before"],
        "outcome_status": payload["outcome_status"],
        "financial_alpha_evidence": payload["financial_alpha_evidence"],
    }


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _target_vector_payload(frame: pd.DataFrame) -> dict[str, Any]:
    if len(frame) != 1:
        raise ValueError("aov0_target_vector_single_row_required")
    date = pd.Timestamp(frame.index[0]).normalize().date().isoformat()
    columns = [str(column) for column in frame.columns]
    values = [format(float(frame.iloc[0][column]), ".17g") for column in frame.columns]
    return {"date": date, "columns": columns, "values": values}


def _target_frame_from_payload(payload: dict[str, Any]) -> pd.DataFrame:
    if set(payload) != {"date", "columns", "values"}:
        raise ValueError("aov0_target_vector_payload_fields_invalid")
    columns = payload["columns"]
    values = payload["values"]
    if not isinstance(columns, list) or not isinstance(values, list) or len(columns) != len(values):
        raise ValueError("aov0_target_vector_payload_shape_invalid")
    if len(set(str(column) for column in columns)) != len(columns):
        raise ValueError("aov0_target_vector_payload_duplicate_columns")
    date = pd.Timestamp(str(payload["date"])).normalize()
    return pd.DataFrame(
        [[float(value) for value in values]],
        index=pd.DatetimeIndex([date]),
        columns=[str(column) for column in columns],
    )


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
