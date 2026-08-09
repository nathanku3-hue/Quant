from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd

from research.aov0.historical_checkpoint import split_historical_market_custody


SOURCE_ID = "SPCIQPRO:HISTORICAL_PRIMARY_SECURITY_MARKET_DATA"


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
        frame.to_parquet(temp, index=False)
        digest = _sha256(temp)
        if path.exists():
            if _sha256(path) != digest:
                raise RuntimeError(f"historical_market_partition_conflict:{path}")
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
            raise RuntimeError(f"historical_market_partition_conflict:{path}")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Physically partition historical market custody into decision/outcome sides.")
    parser.add_argument("--merged-receipt", required=True, type=Path)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("data/aov0/historical_market_partitions"))
    args = parser.parse_args()

    merged_receipt_sha = _sha256(args.merged_receipt)
    merged = json.loads(args.merged_receipt.read_text(encoding="utf-8-sig"))
    if merged.get("source_id") != SOURCE_ID:
        raise ValueError("historical_market_partition_source_invalid")
    if merged.get("decision_target_date") != args.target_date:
        raise ValueError("historical_market_partition_target_mismatch")
    if merged.get("exact_primary_spt_query") is not True or merged.get("alternate_listing_backfill_used") is not False:
        raise ValueError("historical_market_partition_query_identity_contract_invalid")
    # Market custody is never allowed to self-promote into historical-primary
    # identity authority. That authority is a separate hash-bound A1 receipt.
    if merged.get("identity_columns_source") not in {None, "EXTERNAL_INPUT_SECURITY_MASTER"}:
        raise ValueError("historical_market_partition_identity_source_invalid")
    if merged.get("historical_primary_identity_reconstructed") not in {None, False}:
        raise ValueError("historical_market_partition_historical_primary_claim_forbidden")
    if int(merged.get("provider_weekday_chunk_width", -1)) != 7:
        raise ValueError("historical_market_partition_provider_chunk_width_invalid")
    if merged.get("financial_alpha_evidence") != 0:
        raise ValueError("historical_market_partition_financial_alpha_evidence_invalid")
    if merged.get("prospective_clock_authority") != "NONE" or merged.get("parent_child_mutation_authority") != "NONE":
        raise ValueError("historical_market_partition_authority_invalid")

    raw_path = Path(str(merged["raw_object_path"]))
    raw_sha = _sha256(raw_path)
    if raw_sha != merged.get("raw_object_sha256"):
        raise ValueError("historical_market_partition_raw_hash_mismatch")
    raw = pd.read_csv(raw_path, dtype=str, encoding="utf-8-sig")
    decision, outcome = split_historical_market_custody(raw, target_date=args.target_date)

    output_dir = args.output_root / args.target_date.replace("-", "") / raw_sha
    decision_path = output_dir / "decision_market.parquet"
    outcome_path = output_dir / "outcome_market.parquet"
    decision_sha = _atomic_parquet(decision, decision_path)
    outcome_sha = _atomic_parquet(outcome, outcome_path)

    decision_receipt = {
        "schema_version": "aov0_historical_decision_market_partition_receipt_v1",
        "source_id": SOURCE_ID,
        "decision_target_date": args.target_date,
        "source_merged_market_receipt_sha256": merged_receipt_sha,
        "source_raw_object_sha256": raw_sha,
        "decision_market_path": decision_path.as_posix(),
        "decision_market_sha256": decision_sha,
        "decision_row_count": int(len(decision)),
        "outcome_data_loaded_by_decision_consumer": False,
        "identity_columns_source": "EXTERNAL_INPUT_SECURITY_MASTER",
        "historical_primary_identity_reconstructed": False,
        "historical_primary_identity_authority": "NONE_REQUIRES_SEPARATE_HISTORICAL_PRIMARY_RECEIPT",
        "outcome_authority": "NONE",
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
        "financial_alpha_evidence": 0,
    }
    decision_receipt_path = output_dir / "decision_partition_receipt.json"
    decision_receipt_sha = _atomic_json(decision_receipt, decision_receipt_path)

    outcome_receipt = {
        "schema_version": "aov0_historical_outcome_market_partition_receipt_v1",
        "source_id": SOURCE_ID,
        "decision_target_date": args.target_date,
        "source_merged_market_receipt_sha256": merged_receipt_sha,
        "source_raw_object_sha256": raw_sha,
        "outcome_market_path": outcome_path.as_posix(),
        "outcome_market_sha256": outcome_sha,
        "outcome_row_count": int(len(outcome)),
        "identity_columns_source": "EXTERNAL_INPUT_SECURITY_MASTER",
        "historical_primary_identity_reconstructed": False,
        "historical_primary_identity_authority": "NONE_REQUIRES_SEPARATE_HISTORICAL_PRIMARY_RECEIPT",
        "decision_authority": "NONE",
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
        "financial_alpha_evidence": 0,
    }
    outcome_receipt_path = output_dir / "outcome_partition_receipt.json"
    outcome_receipt_sha = _atomic_json(outcome_receipt, outcome_receipt_path)

    print(
        "HISTORICAL_MARKET_PARTITION_OK"
        f"\tDECISION_ROWS={len(decision)}"
        f"\tDECISION_SHA256={decision_sha}"
        f"\tDECISION_RECEIPT_SHA256={decision_receipt_sha}"
        f"\tOUTCOME_ROWS={len(outcome)}"
        f"\tOUTCOME_SHA256={outcome_sha}"
        f"\tOUTCOME_RECEIPT_SHA256={outcome_receipt_sha}"
        f"\tDIR={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
