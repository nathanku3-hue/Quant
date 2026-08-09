from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd

from research.aov0.historical_checkpoint import (
    build_historical_aov_decision_checkpoint,
    verify_historical_aov_decision_checkpoint,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(suffix=".parquet.tmp", dir=path.parent, delete=False) as tmp:
        temp = Path(tmp.name)
    try:
        frame.to_parquet(temp, index=True)
        digest = _sha256(temp)
        if path.exists():
            if _sha256(path) != digest:
                raise RuntimeError(f"historical_checkpoint_output_conflict:{path}")
            return digest
        os.replace(temp, path)
        return digest
    finally:
        if temp.exists():
            temp.unlink()


def _atomic_json(payload: dict[str, Any], path: Path) -> str:
    raw = (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise RuntimeError(f"historical_checkpoint_output_conflict:{path}")
        return digest
    with NamedTemporaryFile(suffix=".json.tmp", dir=path.parent, delete=False) as tmp:
        temp = Path(tmp.name)
        tmp.write(raw)
        tmp.flush()
        os.fsync(tmp.fileno())
    try:
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
    return digest


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"historical_checkpoint_json_object_required:{path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Build one exact frozen-AOV historical PIT decision checkpoint.")
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--fundamental-admission-receipt", type=Path, required=True)
    parser.add_argument("--decision-partition-receipt", type=Path, required=True)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--decision-cut-time", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("data/aov0/historical_checkpoints"))
    args = parser.parse_args()

    master_sha = _sha256(args.master)
    master = pd.read_csv(args.master, dtype=str, encoding="utf-8-sig")
    if len(master) != 109 or master["SP_ENTITY_ID"].astype(str).str.strip().nunique() != 109:
        raise ValueError("historical_checkpoint_master_frozen_109_invalid")
    frozen = set(master["SP_ENTITY_ID"].astype(str).str.strip())

    fundamental_receipt = _load_json(args.fundamental_admission_receipt)
    if fundamental_receipt.get("financial_alpha_evidence") != 0:
        raise ValueError("historical_checkpoint_fundamental_financial_alpha_evidence_invalid")
    if fundamental_receipt.get("prospective_clock_authority") != "NONE":
        raise ValueError("historical_checkpoint_fundamental_prospective_authority_invalid")
    if fundamental_receipt.get("parent_child_mutation_authority") != "NONE":
        raise ValueError("historical_checkpoint_fundamental_mutation_authority_invalid")
    if fundamental_receipt.get("master_sha256") != master_sha:
        raise ValueError("historical_checkpoint_fundamental_master_hash_mismatch")
    fundamental_state_path = Path(str(fundamental_receipt["fundamental_state_path"]))
    fundamental_state_sha = _sha256(fundamental_state_path)
    if fundamental_state_sha != fundamental_receipt.get("fundamental_state_sha256"):
        raise ValueError("historical_checkpoint_fundamental_state_hash_mismatch")
    fundamental_state = pd.read_parquet(fundamental_state_path)

    decision_receipt = _load_json(args.decision_partition_receipt)
    if decision_receipt.get("decision_target_date") != args.target_date:
        raise ValueError("historical_checkpoint_decision_partition_target_mismatch")
    if decision_receipt.get("outcome_data_loaded_by_decision_consumer") is not False:
        raise ValueError("historical_checkpoint_decision_partition_outcome_flag_invalid")
    if decision_receipt.get("outcome_authority") != "NONE":
        raise ValueError("historical_checkpoint_decision_partition_outcome_authority_invalid")
    if decision_receipt.get("prospective_clock_authority") != "NONE":
        raise ValueError("historical_checkpoint_decision_partition_prospective_authority_invalid")
    if decision_receipt.get("parent_child_mutation_authority") != "NONE":
        raise ValueError("historical_checkpoint_decision_partition_mutation_authority_invalid")
    decision_market_path = Path(str(decision_receipt["decision_market_path"]))
    decision_market_sha = _sha256(decision_market_path)
    if decision_market_sha != decision_receipt.get("decision_market_sha256"):
        raise ValueError("historical_checkpoint_decision_market_hash_mismatch")
    decision_market = pd.read_parquet(decision_market_path)

    checkpoint = build_historical_aov_decision_checkpoint(
        security_master_raw=master,
        decision_market_raw=decision_market,
        fundamental_state=fundamental_state,
        frozen_entity_ids=frozen,
        target_date=args.target_date,
        decision_cut_time=args.decision_cut_time,
        source_bindings={
            "historical_fundamentals": fundamental_state_sha,
            "primary_security_master": master_sha,
            "decision_market": decision_market_sha,
        },
    )
    verify_historical_aov_decision_checkpoint(checkpoint)

    output_dir = args.output_root / args.target_date.replace("-", "") / checkpoint.checkpoint_id
    rule100_path = output_dir / "rule100_targets.parquet"
    parent_path = output_dir / "parent_targets.parquet"
    child_path = output_dir / "child_targets.parquet"
    security_map_path = output_dir / "security_map.parquet"
    exclusions_path = output_dir / "exclusions.parquet"
    manifest_path = output_dir / "checkpoint_manifest.json"
    artifacts = {
        "rule100_targets": {"path": rule100_path.as_posix(), "sha256": _atomic_parquet(checkpoint.dag.rule100, rule100_path)},
        "parent_targets": {"path": parent_path.as_posix(), "sha256": _atomic_parquet(checkpoint.dag.parent, parent_path)},
        "child_targets": {"path": child_path.as_posix(), "sha256": _atomic_parquet(checkpoint.dag.child, child_path)},
        "security_map": {"path": security_map_path.as_posix(), "sha256": _atomic_parquet(checkpoint.market_slice.security_map, security_map_path)},
        "exclusions": {"path": exclusions_path.as_posix(), "sha256": _atomic_parquet(checkpoint.market_slice.exclusions, exclusions_path)},
    }
    manifest_sha = _atomic_json(dict(checkpoint.manifest), manifest_path)
    receipt = {
        "schema_version": "aov0_historical_pit_decision_checkpoint_receipt_v1",
        "checkpoint_id": checkpoint.checkpoint_id,
        "target_date": args.target_date,
        "decision_cut_time": args.decision_cut_time,
        "checkpoint_manifest_path": manifest_path.as_posix(),
        "checkpoint_manifest_sha256": manifest_sha,
        "master_path": args.master.as_posix(),
        "master_sha256": master_sha,
        "fundamental_admission_receipt_path": args.fundamental_admission_receipt.as_posix(),
        "fundamental_admission_receipt_sha256": _sha256(args.fundamental_admission_receipt),
        "decision_partition_receipt_path": args.decision_partition_receipt.as_posix(),
        "decision_partition_receipt_sha256": _sha256(args.decision_partition_receipt),
        "artifacts": artifacts,
        "outcome_data_loaded": False,
        "outcome_authority": "NONE",
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
        "financial_alpha_evidence": 0,
        "evidence_authority": "HISTORICAL_PIT_DECISION_ONLY_NO_OUTCOME_AUTHORITY",
    }
    receipt_path = output_dir / "checkpoint_receipt.json"
    receipt_sha = _atomic_json(receipt, receipt_path)
    print(
        "HISTORICAL_CHECKPOINT_OK"
        f"\tCHECKPOINT_ID={checkpoint.checkpoint_id}"
        f"\tADMITTED={checkpoint.manifest['admitted_security_count']}"
        f"\tEXCLUDED={checkpoint.manifest['mechanical_exclusion_count']}"
        f"\tSIZING_ELIGIBLE={checkpoint.manifest['rule100_sizing_eligible_count']}"
        f"\tMANIFEST_SHA256={manifest_sha}"
        f"\tRECEIPT_SHA256={receipt_sha}"
        f"\tPATH={receipt_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
