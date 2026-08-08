"""Fail-closed local entrypoint for the first real AOV-0 prospective seal."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
import os
import subprocess
import sys
import tempfile
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gv_fs0_canonical import domain_hash
from research.aov0.cash import build_economic_cash_returns
from research.aov0.contracts import (
    AOV0Contract,
    DEFAULT_CONTRACT,
    OWNER_INSURANCE_DECISION_FIELDS,
    normalize_security_id,
)
from research.aov0.cube import build_vertical_cube
from research.aov0.experiment import (
    reopen_prospective_seal,
    run_five_arm_experiment,
    seal_prospective_experiment,
)


DEFAULT_INPUT_ROOT = Path("data/aov0/current")
DEFAULT_OUTPUT_ROOT = Path("data/aov0")
DECISION_CUT_SCHEMA = "aov0_ciq_decision_cut_v3"
EXECUTION_CALENDAR_ID = "NYSE_2026_CORE_CLOSE_1600_ET"
CLOCK_START_RECEIPT_SCHEMA = "aov0_prospective_clock_start_receipt_v1"
FRESH_VERIFICATION_SCHEMA = "aov0_fresh_process_verification_v1"
NYSE_TZ = ZoneInfo("America/New_York")
NYSE_2026_CLOSED_DATES = frozenset(
    {
        "2026-01-01",
        "2026-01-19",
        "2026-02-16",
        "2026-04-03",
        "2026-05-25",
        "2026-06-19",
        "2026-07-03",
        "2026-09-07",
        "2026-11-26",
        "2026-12-25",
    }
)
REQUIRED_INPUTS = {
    "rule100_targets": "rule100_targets.parquet",
    "vertical_primitives": "vertical_primitives.parquet",
    "total_returns": "total_returns.parquet",
    "official_sofr": "official_sofr.parquet",
    "decision_cut": "decision_cut.json",
}
BOUND_PARQUET_INPUTS = tuple(name for name in REQUIRED_INPUTS if name != "decision_cut")
REQUIRED_SOURCE_RECEIPTS = {
    "ciq_quarterly_fundamentals": "SPCIQPRO:QUARTERLY_FUNDAMENTALS",
    "ciq_security_master": "SPCIQPRO:PRIMARY_SECURITY_MASTER",
    "ciq_market_data": "SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA",
    "nyfed_sofr": "NYFED:SOFR",
}
OPTIONAL_SOURCE_RECEIPTS: dict[str, str] = {}
SOURCE_RECEIPT_FIELDS = {"source_id", "retrieved_at", "raw_object_sha256"}
EXECUTABLE_MANIFEST_SCHEMA = "aov0_executable_byte_manifest_v1"
EXECUTABLE_REQUIRED_PATHS = (
    "scripts/aov0_build_ciq_fundamentals.py",
    "scripts/aov0_build_ciq_market.py",
    "scripts/aov0_fetch_nyfed_sofr.py",
    "scripts/aov0_build_decision_cut.py",
    "scripts/aov0_first_seal.py",
    "scripts/aov0_reopen_seal.py",
    "research/aov0/ciq_fundamentals.py",
    "research/aov0/ciq_market.py",
    "research/aov0/cash.py",
    "research/aov0/contracts.py",
    "research/aov0/cube.py",
    "research/aov0/dag.py",
    "research/aov0/experiment.py",
    "research/aov0/policy.py",
    "research/backtest_runner.py",
    "research/benchmarks.py",
    "research/evidence_schema.py",
    "research/strategy_cartridge.py",
    "core/engine.py",
    "core/gv_fs0_canonical.py",
    "data/feature_specs.py",
    "data/feature_store.py",
    "strategies/rule100_softmax_v1_1.py",
)


def _load_wide(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    if "date" not in frame.columns:
        raise ValueError(f"aov0_first_seal_date_column_required:{path}")
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    frame = frame.set_index("date").sort_index()
    if frame.empty or not frame.index.is_unique:
        raise ValueError(f"aov0_first_seal_date_index_invalid:{path}")
    try:
        frame.columns = pd.Index(
            [normalize_security_id(column) for column in frame.columns],
            dtype="object",
            name="security_id",
        )
    except ValueError as exc:
        raise ValueError(f"aov0_first_seal_ciq_security_id_columns_required:{path}") from exc
    return frame.astype(float)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_path(path: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _artifact_identity(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "path": _artifact_path(path),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"aov0_first_seal_duplicate_json_key:{key}")
        output[key] = value
    return output


def _utc_timestamp(value: object, *, field: str) -> pd.Timestamp:
    try:
        ts = pd.Timestamp(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"aov0_first_seal_{field}_invalid") from exc
    if ts.tzinfo is None:
        raise ValueError(f"aov0_first_seal_{field}_timezone_required")
    return ts.tz_convert("UTC")


def _utc_text(ts: pd.Timestamp) -> str:
    return ts.isoformat().replace("+00:00", "Z")


def _decision_date(value: object) -> pd.Timestamp:
    text = str(value or "").strip()
    try:
        parsed = pd.Timestamp(text)
    except (TypeError, ValueError) as exc:
        raise ValueError("aov0_first_seal_decision_target_date_invalid") from exc
    if parsed.tzinfo is not None:
        parsed = parsed.tz_convert("UTC").tz_localize(None)
    parsed = parsed.normalize()
    if text != parsed.date().isoformat():
        raise ValueError("aov0_first_seal_decision_target_date_must_be_date")
    return parsed


def _expected_evaluation_start(target_date: pd.Timestamp) -> pd.Timestamp:
    target = _decision_date(target_date.date().isoformat() if isinstance(target_date, pd.Timestamp) else target_date)
    if target.year != 2026:
        raise ValueError("aov0_first_seal_execution_calendar_out_of_scope")
    session = target.date() + timedelta(days=1)
    while session.weekday() >= 5 or session.isoformat() in NYSE_2026_CLOSED_DATES:
        session += timedelta(days=1)
    local_close = datetime.combine(session, time(16, 0), tzinfo=NYSE_TZ)
    return pd.Timestamp(local_close).tz_convert("UTC")


def _validate_evaluation_start(target_date: pd.Timestamp, evaluation_start: pd.Timestamp) -> None:
    expected = _expected_evaluation_start(target_date)
    if evaluation_start != expected:
        raise ValueError(
            "aov0_first_seal_evaluation_start_not_expected_nyse_core_close:"
            f"expected={_utc_text(expected)};observed={_utc_text(evaluation_start)}"
        )


def _validate_sha256_text(value: object, *, field: str) -> str:
    digest = str(value or "")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"aov0_first_seal_sha256_invalid:{field}")
    return digest


def _universe_hash_from_primitives(primitives: pd.DataFrame) -> str:
    required = {"date", "security_id"}
    if not required.issubset(primitives.columns) or primitives.empty:
        raise ValueError("aov0_first_seal_universe_columns_required")
    frame = primitives.loc[:, ["date", "security_id"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    try:
        frame["security_id"] = frame["security_id"].map(normalize_security_id)
    except ValueError as exc:
        raise ValueError("aov0_first_seal_universe_ciq_security_id_invalid") from exc
    if frame.duplicated(["date", "security_id"]).any():
        raise ValueError("aov0_first_seal_universe_duplicate_date_security_id")
    by_date = {
        date.date().isoformat(): sorted(group["security_id"].astype(str).tolist())
        for date, group in frame.groupby("date", sort=True)
    }
    return domain_hash("AOV0:DATE_LOCAL_CIQ_SECURITY_UNIVERSE:V1", {"by_date": by_date})


def _load_decision_cut(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("aov0_first_seal_decision_cut_json_invalid") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != DECISION_CUT_SCHEMA:
        raise ValueError("aov0_first_seal_decision_cut_schema_invalid")
    required = {
        "schema_version",
        "decision_cut_id",
        "knowledge_cutoff",
        "cut_built_at",
        "decision_target_date",
        "evaluation_start",
        "execution_calendar_id",
        "input_sha256",
        "contract_hash",
        "universe_hash",
        "source_receipts",
    }
    if set(payload) != required:
        raise ValueError("aov0_first_seal_decision_cut_fields_invalid")
    decision_cut_id = str(payload.get("decision_cut_id") or "").strip()
    if not decision_cut_id:
        raise ValueError("aov0_first_seal_decision_cut_id_invalid")
    if payload.get("execution_calendar_id") != EXECUTION_CALENDAR_ID:
        raise ValueError("aov0_first_seal_execution_calendar_id_invalid")
    hashes = payload.get("input_sha256")
    if not isinstance(hashes, dict) or set(hashes) != set(BOUND_PARQUET_INPUTS):
        raise ValueError("aov0_first_seal_decision_cut_input_bindings_invalid")
    for name, value in hashes.items():
        _validate_sha256_text(value, field=f"input:{name}")
    _validate_sha256_text(payload.get("contract_hash"), field="contract_hash")
    _validate_sha256_text(payload.get("universe_hash"), field="universe_hash")

    receipts = payload.get("source_receipts")
    allowed_receipts = {**REQUIRED_SOURCE_RECEIPTS, **OPTIONAL_SOURCE_RECEIPTS}
    if not isinstance(receipts, dict):
        raise ValueError("aov0_first_seal_source_receipts_invalid")
    if not set(REQUIRED_SOURCE_RECEIPTS).issubset(receipts) or not set(receipts).issubset(allowed_receipts):
        raise ValueError("aov0_first_seal_source_receipts_invalid")
    for name, expected_source in allowed_receipts.items():
        if name not in receipts:
            continue
        receipt = receipts[name]
        if not isinstance(receipt, dict) or set(receipt) != SOURCE_RECEIPT_FIELDS:
            raise ValueError(f"aov0_first_seal_source_receipt_fields_invalid:{name}")
        if str(receipt.get("source_id") or "") != expected_source:
            raise ValueError(f"aov0_first_seal_source_receipt_id_invalid:{name}")
        _utc_timestamp(receipt.get("retrieved_at"), field=f"source_receipt_{name}_retrieved_at")
        _validate_sha256_text(receipt.get("raw_object_sha256"), field=f"source_receipt:{name}")
    return payload


def _assert_bound_input_hashes(paths: dict[str, Path], cut: dict[str, Any]) -> None:
    hashes = cut["input_sha256"]
    for name in BOUND_PARQUET_INPUTS:
        if _sha256(paths[name]) != hashes[name]:
            raise ValueError(f"aov0_first_seal_input_hash_mismatch:{name}")


def _validate_target_return_alignment(
    *,
    target_date: pd.Timestamp,
    rule100: pd.DataFrame,
    returns: pd.DataFrame,
    primitives: pd.DataFrame,
) -> None:
    if set(rule100.columns) != set(returns.columns):
        raise ValueError("aov0_first_seal_rule100_return_asset_set_mismatch")
    required = {"date", "security_id", "total_return"}
    if not required.issubset(primitives.columns):
        raise ValueError("aov0_first_seal_target_return_alignment_columns_required")
    frame = primitives.loc[:, ["date", "security_id", "total_return"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    try:
        frame["security_id"] = frame["security_id"].map(normalize_security_id)
    except ValueError as exc:
        raise ValueError("aov0_first_seal_target_primitive_ciq_id_invalid") from exc
    target = frame.loc[frame["date"].eq(target_date)].copy()
    if target.empty:
        raise ValueError("aov0_first_seal_target_primitives_missing")
    if target["security_id"].duplicated().any():
        raise ValueError("aov0_first_seal_target_primitive_duplicate_security")
    if set(target["security_id"].astype(str)) != set(returns.columns.astype(str)):
        raise ValueError("aov0_first_seal_target_primitive_asset_set_mismatch")

    return_vector = pd.to_numeric(returns.loc[target_date], errors="coerce").astype(float).sort_index()
    primitive_vector = (
        target.assign(total_return=pd.to_numeric(target["total_return"], errors="coerce"))
        .set_index("security_id")["total_return"]
        .astype(float)
        .sort_index()
    )
    if (
        return_vector.isna().any()
        or primitive_vector.isna().any()
        or not np.isfinite(return_vector.to_numpy(dtype=float)).all()
        or not np.isfinite(primitive_vector.to_numpy(dtype=float)).all()
    ):
        raise ValueError("aov0_first_seal_target_total_return_non_finite")
    if not np.allclose(
        return_vector.to_numpy(dtype=float),
        primitive_vector.to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-15,
    ):
        raise ValueError("aov0_first_seal_target_total_return_mismatch")


def _validate_cut_timing_and_history(
    *,
    cut: dict[str, Any],
    rule100: pd.DataFrame,
    returns: pd.DataFrame,
    primitives: pd.DataFrame,
    sofr: pd.DataFrame,
) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    knowledge_cutoff = _utc_timestamp(cut["knowledge_cutoff"], field="knowledge_cutoff")
    cut_built_at = _utc_timestamp(cut["cut_built_at"], field="cut_built_at")
    evaluation_start = _utc_timestamp(cut["evaluation_start"], field="evaluation_start")
    target_date = _decision_date(cut["decision_target_date"])

    if cut_built_at < knowledge_cutoff:
        raise ValueError("aov0_first_seal_cut_built_before_knowledge_cutoff")
    if evaluation_start <= cut_built_at or evaluation_start <= knowledge_cutoff:
        raise ValueError("aov0_first_seal_evaluation_start_not_after_cut")
    _validate_evaluation_start(target_date, evaluation_start)

    for name, frame in (("rule100", rule100), ("returns", returns)):
        if frame.empty:
            raise ValueError(f"aov0_first_seal_{name}_empty")
        if frame.index.max() > target_date:
            raise ValueError(f"aov0_first_seal_{name}_post_cut_history")
        if frame.index.max() != target_date:
            raise ValueError(f"aov0_first_seal_{name}_target_date_mismatch")

    if not rule100.index.equals(returns.index):
        raise ValueError("aov0_first_seal_rule100_return_calendar_mismatch")
    _validate_target_return_alignment(
        target_date=target_date,
        rule100=rule100,
        returns=returns,
        primitives=primitives,
    )

    required_primitive = {"date", "known_at"}
    if not required_primitive.issubset(primitives.columns):
        raise ValueError("aov0_first_seal_primitives_cut_columns_required")
    primitive_dates = pd.to_datetime(primitives["date"], errors="raise").dt.normalize()
    primitive_known = pd.to_datetime(
        primitives["known_at"], utc=True, errors="raise", format="mixed"
    )
    if primitive_dates.empty or primitive_dates.max() > target_date:
        raise ValueError("aov0_first_seal_primitives_post_cut_history")
    if primitive_dates.max() != target_date:
        raise ValueError("aov0_first_seal_primitives_target_date_mismatch")
    if (primitive_known > knowledge_cutoff).any():
        raise ValueError("aov0_first_seal_primitives_future_knowledge")

    required_sofr = {"effective_date", "published_at", "sofr_percent"}
    if not required_sofr.issubset(sofr.columns):
        raise ValueError("aov0_first_seal_sofr_cut_columns_required")
    sofr_effective = pd.to_datetime(sofr["effective_date"], errors="raise").dt.normalize()
    sofr_published = pd.to_datetime(
        sofr["published_at"], utc=True, errors="raise", format="mixed"
    )
    if sofr.empty or (sofr_effective > target_date).any():
        raise ValueError("aov0_first_seal_sofr_post_target_date")
    if (sofr_published > knowledge_cutoff).any():
        raise ValueError("aov0_first_seal_sofr_future_publication")

    receipts = cut["source_receipts"]
    for name, receipt in receipts.items():
        retrieved_at = _utc_timestamp(
            receipt["retrieved_at"], field=f"source_receipt_{name}_retrieved_at"
        )
        if retrieved_at > knowledge_cutoff:
            raise ValueError(f"aov0_first_seal_source_receipt_after_knowledge_cutoff:{name}")
    nyfed_retrieved = _utc_timestamp(
        receipts["nyfed_sofr"]["retrieved_at"], field="source_receipt_nyfed_sofr_retrieved_at"
    ).tz_convert(ZoneInfo("America/New_York"))
    if (nyfed_retrieved.hour, nyfed_retrieved.minute) < (15, 0):
        raise ValueError("aov0_first_seal_nyfed_sofr_retrieved_before_1500_et")

    return knowledge_cutoff, cut_built_at, target_date, evaluation_start


def _decision_cut_binding(
    *,
    paths: dict[str, Path],
    cut: dict[str, Any],
    knowledge_cutoff: pd.Timestamp,
    cut_built_at: pd.Timestamp,
    target_date: pd.Timestamp,
    evaluation_start: pd.Timestamp,
) -> dict[str, Any]:
    return {
        "schema_version": DECISION_CUT_SCHEMA,
        "decision_cut_id": str(cut["decision_cut_id"]),
        "knowledge_cutoff": _utc_text(knowledge_cutoff),
        "cut_built_at": _utc_text(cut_built_at),
        "decision_target_date": target_date.date().isoformat(),
        "evaluation_start": _utc_text(evaluation_start),
        "execution_calendar_id": EXECUTION_CALENDAR_ID,
        "contract_hash": str(cut["contract_hash"]),
        "universe_hash": str(cut["universe_hash"]),
        "source_receipts": cut["source_receipts"],
        "inputs": {
            name: _artifact_identity(paths[name])
            for name in BOUND_PARQUET_INPUTS
        },
        "decision_cut_artifact": _artifact_identity(paths["decision_cut"]),
    }


def _write_executable_manifest(*, output_root: Path) -> Path:
    candidates = {Path(path) for path in EXECUTABLE_REQUIRED_PATHS}
    repo_root = ROOT.resolve()
    for module in tuple(sys.modules.values()):
        module_file = getattr(module, "__file__", None)
        if not module_file:
            continue
        resolved = Path(module_file).resolve()
        try:
            relative = resolved.relative_to(repo_root)
        except ValueError:
            continue
        if relative.suffix == ".py":
            candidates.add(relative)

    files: dict[str, dict[str, object]] = {}
    for relative in sorted(candidates, key=lambda value: value.as_posix()):
        path = repo_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"aov0_executable_manifest_missing_file:{relative.as_posix()}")
        raw = path.read_bytes()
        files[relative.as_posix()] = {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    interpreter = Path(sys.executable).resolve()
    interpreter_raw = interpreter.read_bytes()
    payload = {
        "schema_version": EXECUTABLE_MANIFEST_SCHEMA,
        "python_version": sys.version,
        "interpreter": {
            "path": interpreter.as_posix(),
            "bytes": len(interpreter_raw),
            "sha256": hashlib.sha256(interpreter_raw).hexdigest(),
        },
        "files": files,
    }
    manifest_id = domain_hash("AOV0:EXECUTABLE_BYTE_MANIFEST:V1", payload)
    payload["manifest_id"] = manifest_id
    directory = Path(output_root) / "executable_manifests"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{manifest_id}.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise FileExistsError(f"aov0_executable_manifest_collision:{path}")
        return path
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=directory)
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
    return path


def run_first_seal(
    *,
    input_root: Path = DEFAULT_INPUT_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    contract: AOV0Contract = DEFAULT_CONTRACT,
    sealed_at: datetime | None = None,
) -> dict[str, object]:
    input_root = Path(input_root)
    paths = {name: input_root / filename for name, filename in REQUIRED_INPUTS.items()}
    missing = [name for name, path in paths.items() if not path.is_file()]
    owner_decisions = [
        field
        for field in OWNER_INSURANCE_DECISION_FIELDS
        if getattr(contract, field) is None
    ]
    if owner_decisions or missing:
        if owner_decisions and missing:
            status = "BLOCKED_OWNER_DECISION_AND_ADMITTED_INPUTS"
        elif owner_decisions:
            status = "BLOCKED_OWNER_DECISION"
        else:
            status = "BLOCKED_MISSING_ADMITTED_INPUTS"
        return {
            "status": status,
            "financial_alpha_evidence": 0,
            "prospective_clock_started": False,
            "owner_decisions_required": owner_decisions,
            "missing": missing,
            "required_paths": {name: path.as_posix() for name, path in paths.items()},
        }

    cut = _load_decision_cut(paths["decision_cut"])
    _assert_bound_input_hashes(paths, cut)

    rule100 = _load_wide(paths["rule100_targets"])
    returns = _load_wide(paths["total_returns"])
    primitives = pd.read_parquet(paths["vertical_primitives"])
    sofr = pd.read_parquet(paths["official_sofr"])
    if str(cut["contract_hash"]) != contract.contract_hash:
        raise ValueError("aov0_first_seal_contract_hash_mismatch")
    computed_universe_hash = _universe_hash_from_primitives(primitives)
    if str(cut["universe_hash"]) != computed_universe_hash:
        raise ValueError("aov0_first_seal_universe_hash_mismatch")
    knowledge_cutoff, cut_built_at, target_date, evaluation_start = _validate_cut_timing_and_history(
        cut=cut,
        rule100=rule100,
        returns=returns,
        primitives=primitives,
        sofr=sofr,
    )

    cube = build_vertical_cube(
        primitives,
        computed_at=_utc_text(knowledge_cutoff),
        contract=contract,
    )
    economic_cash = build_economic_cash_returns(rule100.index, sofr)
    eligible_by_date = {
        date: tuple(sorted(group["security_id"].astype(str).unique().tolist()))
        for date, group in cube.frame.groupby("date", sort=False)
    }

    experiment = run_five_arm_experiment(
        rule100_weights=rule100,
        returns_df=returns,
        economic_cash_returns=economic_cash,
        cube=cube,
        pit_eligibility_provider=lambda date: eligible_by_date.get(pd.Timestamp(date).normalize(), ()),
        output_root=Path(output_root) / "evidence",
        contract=contract,
    )
    if experiment.current_target_date != target_date.date().isoformat():
        raise ValueError("aov0_first_seal_experiment_target_date_mismatch")

    # Re-hash after experiment execution so the prospective receipt cannot bind
    # bytes that changed during the run.
    _assert_bound_input_hashes(paths, cut)
    binding = _decision_cut_binding(
        paths=paths,
        cut=cut,
        knowledge_cutoff=knowledge_cutoff,
        cut_built_at=cut_built_at,
        target_date=target_date,
        evaluation_start=evaluation_start,
    )
    executable_manifest = _write_executable_manifest(output_root=Path(output_root))
    seal = seal_prospective_experiment(
        experiment,
        cube=cube,
        decision_cut_binding=binding,
        executable_manifest=executable_manifest,
        output_dir=Path(output_root) / "prospective_seals",
        contract=contract,
        sealed_at=sealed_at,
    )
    return {
        "status": "SEAL_CANDIDATE_WRITTEN",
        "financial_alpha_evidence": 0,
        "prospective_clock_started": False,
        "experiment_id": experiment.experiment_id,
        "seal_id": seal.seal_id,
        "seal_path": seal.path.as_posix(),
        "sealed_at": seal.payload["sealed_at"],
        "executable_manifest": _artifact_identity(executable_manifest),
        "decision_target_date": experiment.current_target_date,
        "evaluation_start": seal.payload["evaluation_start"],
        "current_decision_target_hashes": experiment.current_target_hashes,
        "outcome_open_not_before": seal.payload["outcome_open_not_before"],
    }


def _load_verification_proof(
    path: Path,
    *,
    seal_path: Path,
    expected_parent_pid: int | None,
) -> dict[str, Any]:
    try:
        proof = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("aov0_clock_start_verification_proof_json_invalid") from exc
    required = {
        "schema_version",
        "status",
        "verified_at",
        "parent_pid",
        "verifier_pid",
        "fresh_process",
        "seal_id",
        "seal_artifact",
        "verifier_executable",
        "evaluation_start",
        "outcome_open_not_before",
        "verification_id",
    }
    if not isinstance(proof, dict) or set(proof) != required:
        raise ValueError("aov0_clock_start_verification_proof_fields_invalid")
    if proof["schema_version"] != FRESH_VERIFICATION_SCHEMA or proof["status"] != "FULL_CHAIN_REOPEN_VERIFIED":
        raise ValueError("aov0_clock_start_verification_status_invalid")
    if proof["fresh_process"] is not True or int(proof["verifier_pid"]) == int(proof["parent_pid"]):
        raise ValueError("aov0_clock_start_fresh_process_required")
    if expected_parent_pid is not None and int(proof["parent_pid"]) != int(expected_parent_pid):
        raise ValueError("aov0_clock_start_parent_pid_mismatch")
    seal_identity = _artifact_identity(Path(seal_path))
    if proof["seal_artifact"] != seal_identity:
        raise ValueError("aov0_clock_start_seal_artifact_mismatch")
    verifier_identity = _artifact_identity(ROOT / "scripts/aov0_reopen_seal.py")
    if proof["verifier_executable"] != verifier_identity:
        raise ValueError("aov0_clock_start_verifier_executable_mismatch")
    body = {key: value for key, value in proof.items() if key != "verification_id"}
    expected_id = domain_hash("AOV0:FRESH_PROCESS_VERIFICATION:V1", body)
    if proof["verification_id"] != expected_id:
        raise ValueError("aov0_clock_start_verification_id_mismatch")
    return proof


def _write_new_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"aov0_clock_start_receipt_exists:{path}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def issue_clock_start_receipt(
    *,
    seal_path: Path,
    verification_proof_path: Path,
    output_root: Path,
    expected_parent_pid: int | None = None,
) -> dict[str, Any]:
    seal_path = Path(seal_path).resolve()
    verification_proof_path = Path(verification_proof_path).resolve()
    seal = reopen_prospective_seal(seal_path)
    proof = _load_verification_proof(
        verification_proof_path,
        seal_path=seal_path,
        expected_parent_pid=os.getpid() if expected_parent_pid is None else expected_parent_pid,
    )
    if proof["seal_id"] != seal["seal_id"]:
        raise ValueError("aov0_clock_start_seal_id_mismatch")
    if proof["evaluation_start"] != seal["evaluation_start"]:
        raise ValueError("aov0_clock_start_evaluation_start_mismatch")
    if proof["outcome_open_not_before"] != seal["outcome_open_not_before"]:
        raise ValueError("aov0_clock_start_maturity_mismatch")
    verified_at = _utc_timestamp(proof["verified_at"], field="clock_start_verified_at")
    evaluation_start = _utc_timestamp(seal["evaluation_start"], field="clock_start_evaluation_start")
    if verified_at >= evaluation_start:
        raise ValueError("aov0_clock_start_verification_not_before_evaluation_start")
    body = {
        "schema_version": CLOCK_START_RECEIPT_SCHEMA,
        "seal_id": seal["seal_id"],
        "seal_artifact": _artifact_identity(seal_path),
        "verification_id": proof["verification_id"],
        "verification_proof": _artifact_identity(verification_proof_path),
        "verified_at": _utc_text(verified_at),
        "clock_started_at": _utc_text(verified_at),
        "evaluation_start": seal["evaluation_start"],
        "outcome_open_not_before": seal["outcome_open_not_before"],
        "prospective_clock_started": True,
        "financial_alpha_evidence": 0,
    }
    receipt = {
        **body,
        "clock_start_receipt_id": domain_hash("AOV0:PROSPECTIVE_CLOCK_START_RECEIPT:V1", body),
    }
    path = Path(output_root) / "clock_start_receipts" / f"{seal['seal_id']}.json"
    _write_new_json_atomic(path, receipt)
    validated = load_clock_start_receipt(
        path,
        seal_path=seal_path,
        repo_root=ROOT,
    )
    return {**validated, "path": path.as_posix(), "sha256": _sha256(path)}


def load_clock_start_receipt(
    path: Path,
    *,
    seal_path: Path,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    del repo_root  # Reserved for future relocation-safe custody expansion.
    try:
        receipt = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("aov0_clock_start_receipt_json_invalid") from exc
    required = {
        "schema_version",
        "seal_id",
        "seal_artifact",
        "verification_id",
        "verification_proof",
        "verified_at",
        "clock_started_at",
        "evaluation_start",
        "outcome_open_not_before",
        "prospective_clock_started",
        "financial_alpha_evidence",
        "clock_start_receipt_id",
    }
    if not isinstance(receipt, dict) or set(receipt) != required:
        raise ValueError("aov0_clock_start_receipt_fields_invalid")
    if receipt["schema_version"] != CLOCK_START_RECEIPT_SCHEMA or receipt["prospective_clock_started"] is not True:
        raise ValueError("aov0_clock_start_receipt_schema_invalid")
    if receipt["financial_alpha_evidence"] != 0:
        raise ValueError("aov0_clock_start_financial_evidence_invalid")
    body = {key: value for key, value in receipt.items() if key != "clock_start_receipt_id"}
    expected_id = domain_hash("AOV0:PROSPECTIVE_CLOCK_START_RECEIPT:V1", body)
    if receipt["clock_start_receipt_id"] != expected_id:
        raise ValueError("aov0_clock_start_receipt_id_mismatch")
    seal_path = Path(seal_path).resolve()
    seal = reopen_prospective_seal(seal_path)
    if receipt["seal_id"] != seal["seal_id"] or receipt["seal_artifact"] != _artifact_identity(seal_path):
        raise ValueError("aov0_clock_start_receipt_seal_binding_invalid")
    proof_identity = receipt["verification_proof"]
    if not isinstance(proof_identity, dict) or set(proof_identity) != {"path", "bytes", "sha256"}:
        raise ValueError("aov0_clock_start_verification_proof_identity_invalid")
    proof_path = Path(str(proof_identity["path"]))
    if not proof_path.is_absolute():
        proof_path = (ROOT / proof_path).resolve()
    if _artifact_identity(proof_path) != proof_identity:
        raise ValueError("aov0_clock_start_verification_proof_artifact_mismatch")
    proof = _load_verification_proof(proof_path, seal_path=seal_path, expected_parent_pid=None)
    if receipt["verification_id"] != proof["verification_id"]:
        raise ValueError("aov0_clock_start_receipt_verification_binding_invalid")
    if receipt["verified_at"] != proof["verified_at"] or receipt["clock_started_at"] != proof["verified_at"]:
        raise ValueError("aov0_clock_start_receipt_time_binding_invalid")
    if receipt["evaluation_start"] != seal["evaluation_start"]:
        raise ValueError("aov0_clock_start_receipt_evaluation_binding_invalid")
    if receipt["outcome_open_not_before"] != seal["outcome_open_not_before"]:
        raise ValueError("aov0_clock_start_receipt_maturity_binding_invalid")
    return receipt


def prospective_authority_state(
    *,
    seal_path: Path,
    clock_start_receipt_path: Path | None,
    now: datetime | pd.Timestamp,
) -> dict[str, object]:
    seal = reopen_prospective_seal(Path(seal_path))
    now_ts = pd.Timestamp(now)
    now_ts = now_ts.tz_localize("UTC") if now_ts.tzinfo is None else now_ts.tz_convert("UTC")
    if clock_start_receipt_path is None or not Path(clock_start_receipt_path).is_file():
        return {
            "prospective_clock_started": False,
            "evaluation_started": False,
            "outcome_open_authorized": False,
            "future_outcome_authority_available": False,
        }
    receipt = load_clock_start_receipt(clock_start_receipt_path, seal_path=seal_path)
    clock_started_at = _utc_timestamp(receipt["clock_started_at"], field="clock_started_at")
    evaluation_start = _utc_timestamp(seal["evaluation_start"], field="evaluation_start")
    maturity = _utc_timestamp(seal["outcome_open_not_before"], field="outcome_open_not_before")
    clock_started = now_ts >= clock_started_at
    evaluation_started = clock_started and now_ts >= evaluation_start
    matured = clock_started and now_ts >= maturity
    return {
        "prospective_clock_started": clock_started,
        "evaluation_started": evaluation_started,
        "outcome_open_authorized": matured,
        "future_outcome_authority_available": matured,
    }


def promote_seal_candidate(
    candidate: dict[str, object],
    *,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, object]:
    if candidate.get("status") != "SEAL_CANDIDATE_WRITTEN" or candidate.get("prospective_clock_started") is not False:
        return {
            **candidate,
            "status": "BLOCKED_INVALID_SEAL_CANDIDATE_FOR_PROMOTION",
            "prospective_clock_started": False,
        }
    seal_path = Path(str(candidate["seal_path"]))
    if not seal_path.is_absolute():
        seal_path = (ROOT / seal_path).resolve()
    proof_path = Path(output_root) / "verification_proofs" / f"{candidate['seal_id']}.json"
    reopen = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/aov0_reopen_seal.py"),
            "--seal",
            str(seal_path),
            "--repo-root",
            str(ROOT),
            "--verification-proof",
            str(proof_path.resolve()),
            "--expected-parent-pid",
            str(os.getpid()),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if reopen.returncode != 0:
        return {
            **candidate,
            "status": "BLOCKED_FRESH_PROCESS_REOPEN_FAILED",
            "prospective_clock_started": False,
            "fresh_process_reopen_stderr": reopen.stderr.strip(),
            "fresh_process_reopen_stdout": reopen.stdout.strip(),
        }
    reopened = json.loads(reopen.stdout)
    try:
        receipt = issue_clock_start_receipt(
            seal_path=seal_path,
            verification_proof_path=proof_path,
            output_root=output_root,
            expected_parent_pid=os.getpid(),
        )
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        return {
            **candidate,
            "status": "BLOCKED_CLOCK_START_RECEIPT",
            "prospective_clock_started": False,
            "fresh_process_reopen": reopened,
            "reason": str(exc),
        }
    return {
        **candidate,
        "status": "PROSPECTIVE_CLOCK_STARTED",
        "prospective_clock_started": True,
        "fresh_process_reopen": reopened,
        "clock_start_receipt": receipt,
    }


def main() -> int:
    candidate = run_first_seal()
    if candidate.get("status") != "SEAL_CANDIDATE_WRITTEN":
        print(json.dumps(candidate, indent=2, sort_keys=True))
        return 2
    result = promote_seal_candidate(candidate)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("prospective_clock_started") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
