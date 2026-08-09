from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd

from research.aov0.ciq_historical_market import admit_historical_market_parts


SOURCE_ID = "SPCIQPRO:HISTORICAL_PRIMARY_SECURITY_MARKET_DATA"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_csv(frame: pd.DataFrame, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(suffix=".csv.tmp", dir=path.parent, delete=False) as tmp:
        temp = Path(tmp.name)
    try:
        frame.to_csv(temp, index=False, encoding="utf-8", lineterminator="\n")
        digest = _sha256(temp)
        if path.exists():
            if _sha256(path) != digest:
                raise RuntimeError(f"historical_market_output_conflict:{path}")
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
            raise RuntimeError(f"historical_market_output_conflict:{path}")
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


def _load_part(raw_path: Path, receipt_path: Path, *, master_sha256: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw_sha = _sha256(raw_path)
    receipt_sha = _sha256(receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    if receipt.get("source_id") != SOURCE_ID:
        raise ValueError("historical_market_part_source_invalid")
    if receipt.get("raw_object_sha256") != raw_sha:
        raise ValueError("historical_market_part_raw_hash_mismatch")
    if receipt.get("master_sha256") != master_sha256:
        raise ValueError("historical_market_part_master_hash_mismatch")
    if receipt.get("exact_primary_spt_query") is not True:
        raise ValueError("historical_market_part_exact_primary_required")
    if receipt.get("alternate_listing_backfill_used") is not False:
        raise ValueError("historical_market_part_alternate_listing_forbidden")
    if int(receipt.get("provider_weekday_chunk_width", -1)) != 7:
        raise ValueError("historical_market_part_provider_chunk_width_invalid")
    if receipt.get("financial_alpha_evidence") != 0:
        raise ValueError("historical_market_part_financial_alpha_evidence_invalid")
    if receipt.get("prospective_clock_authority") != "NONE":
        raise ValueError("historical_market_part_prospective_authority_invalid")
    if receipt.get("parent_child_mutation_authority") != "NONE":
        raise ValueError("historical_market_part_mutation_authority_invalid")
    frame = pd.read_csv(raw_path, dtype=str, encoding="utf-8-sig")
    return frame, {
        "raw_path": raw_path.as_posix(),
        "raw_sha256": raw_sha,
        "receipt_path": receipt_path.as_posix(),
        "receipt_sha256": receipt_sha,
        "start_date": receipt.get("start_date"),
        "end_date": receipt.get("end_date"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge restartable 7-weekday CIQ historical market captures.")
    parser.add_argument("--part", nargs=2, action="append", metavar=("RAW", "RECEIPT"), required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--decision-target-date", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("data/aov0/historical_market"))
    args = parser.parse_args()

    master_sha = _sha256(args.master)
    master = pd.read_csv(args.master, dtype=str, encoding="utf-8-sig")
    if len(master) != 109 or master["SP_ENTITY_ID"].astype(str).str.strip().nunique() != 109:
        raise ValueError("historical_market_master_frozen_109_invalid")
    frozen = set(master["SP_ENTITY_ID"].astype(str).str.strip())

    frames: list[pd.DataFrame] = []
    part_bindings: list[dict[str, Any]] = []
    for raw_text, receipt_text in args.part:
        frame, binding = _load_part(Path(raw_text), Path(receipt_text), master_sha256=master_sha)
        frames.append(frame)
        part_bindings.append(binding)

    admitted = admit_historical_market_parts(
        frames,
        frozen_entity_ids=frozen,
        expected_start_date=args.start_date,
        expected_end_date=args.end_date,
        decision_target_date=args.decision_target_date,
    )
    part_digest_body = {
        "parts": sorted(
            ({"raw_sha256": binding["raw_sha256"], "receipt_sha256": binding["receipt_sha256"]} for binding in part_bindings),
            key=lambda item: (item["raw_sha256"], item["receipt_sha256"]),
        )
    }
    merged_id = hashlib.sha256(
        json.dumps(part_digest_body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    output_dir = args.output_root / args.decision_target_date.replace("-", "") / merged_id
    raw_path = output_dir / "market_raw_merged.csv"
    counts_path = output_dir / "market_counts.csv"
    raw_hash = _atomic_csv(admitted.raw, raw_path)
    counts_hash = _atomic_csv(admitted.counts, counts_path)

    receipt = {
        "schema_version": "aov0_ciq_historical_market_merged_receipt_v1",
        "source_id": SOURCE_ID,
        "master_path": args.master.as_posix(),
        "master_sha256": master_sha,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "decision_target_date": args.decision_target_date,
        "frozen_entity_count": 109,
        "provider_weekday_chunk_width": 7,
        # Compatibility spelling: exact SPT means exact input-master SPT, not
        # provider-primary-at-historical-date identity authority.
        "exact_primary_spt_query": True,
        "query_identity_key": "SPT_INSTRUMENT_ITEM_ID_FROM_INPUT_SECURITY_MASTER",
        "identity_columns_source": "EXTERNAL_INPUT_SECURITY_MASTER",
        "historical_primary_identity_reconstructed": False,
        "historical_primary_identity_authority": "NONE_REQUIRES_SEPARATE_HISTORICAL_PRIMARY_RECEIPT",
        "alternate_listing_backfill_used": False,
        "parts": part_bindings,
        "raw_object_path": raw_path.as_posix(),
        "raw_object_sha256": raw_hash,
        "counts_path": counts_path.as_posix(),
        "counts_sha256": counts_hash,
        "admission_metadata": admitted.metadata,
        "financial_alpha_evidence": 0,
        "evidence_authority": "HISTORICAL_MARKET_ONLY_NOT_PROSPECTIVE_CLOCK_AUTHORITY",
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
    receipt_path = output_dir / "market_merged_receipt.json"
    receipt_hash = _atomic_json(receipt, receipt_path)
    print(
        "HISTORICAL_MARKET_MERGE_OK"
        f"\tROWS={len(admitted.raw)}"
        f"\tGE200_WITH_TARGET={admitted.metadata['ge200_with_target_count']}"
        f"\tRAW_SHA256={raw_hash}"
        f"\tCOUNTS_SHA256={counts_hash}"
        f"\tRECEIPT_SHA256={receipt_hash}"
        f"\tPATH={receipt_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
