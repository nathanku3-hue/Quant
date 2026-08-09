from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd

from research.aov0.ciq_historical_pit import REQUIRED_RELATIVE_PERIODS


SOURCE_ID = "SPCIQPRO:HISTORICAL_ASOF_QUARTERLY_FUNDAMENTALS"


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
                raise RuntimeError(f"historical_pit_merge_output_conflict:{path}")
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
            raise RuntimeError(f"historical_pit_merge_output_conflict:{path}")
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


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"historical_pit_part_receipt_object_required:{path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge restartable CIQ historical PIT fundamental chunks.")
    parser.add_argument("--parts-dir", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--as-of-date", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("data/aov0/historical_pit/raw"))
    args = parser.parse_args()

    master_sha = _sha256(args.master)
    master = pd.read_csv(args.master, dtype=str, encoding="utf-8-sig")
    frozen = tuple(master["SP_ENTITY_ID"].fillna("").astype(str).str.strip())
    if len(master) != 109 or len(set(frozen)) != 109 or any(not value for value in frozen):
        raise ValueError("historical_pit_merge_master_frozen_109_invalid")

    receipt_paths = sorted(args.parts_dir.glob("part_*.receipt.json"))
    if not receipt_paths:
        raise FileNotFoundError("historical_pit_merge_parts_missing")
    frames: list[pd.DataFrame] = []
    bindings: list[dict[str, Any]] = []
    seen_chunks: set[int] = set()
    availability_values: set[str] = set()
    expected_chunk_count: int | None = None
    for receipt_path in receipt_paths:
        receipt_sha = _sha256(receipt_path)
        receipt = _json(receipt_path)
        if receipt.get("schema_version") != "aov0_ciq_historical_pit_fundamental_part_receipt_v1":
            raise ValueError("historical_pit_merge_part_schema_invalid")
        if receipt.get("source_id") != SOURCE_ID:
            raise ValueError("historical_pit_merge_part_source_invalid")
        if receipt.get("historical_as_of_date") != args.as_of_date:
            raise ValueError("historical_pit_merge_part_asof_mismatch")
        if receipt.get("master_sha256") != master_sha:
            raise ValueError("historical_pit_merge_part_master_hash_mismatch")
        if receipt.get("financial_alpha_evidence") != 0:
            raise ValueError("historical_pit_merge_part_financial_alpha_evidence_invalid")
        if receipt.get("prospective_clock_authority") != "NONE":
            raise ValueError("historical_pit_merge_part_prospective_authority_invalid")
        if receipt.get("parent_child_mutation_authority") != "NONE":
            raise ValueError("historical_pit_merge_part_mutation_authority_invalid")
        chunk_index = int(receipt["chunk_index"])
        chunk_count = int(receipt["chunk_count"])
        if expected_chunk_count is None:
            expected_chunk_count = chunk_count
        elif chunk_count != expected_chunk_count:
            raise ValueError("historical_pit_merge_chunk_count_drift")
        if chunk_index in seen_chunks:
            raise ValueError("historical_pit_merge_duplicate_chunk_index")
        seen_chunks.add(chunk_index)
        availability_values.add(str(receipt["pit_available_at_utc"]))
        raw_path = Path(str(receipt["raw_object_path"]))
        raw_sha = _sha256(raw_path)
        if raw_sha != receipt.get("raw_object_sha256"):
            raise ValueError("historical_pit_merge_part_raw_hash_mismatch")
        frame = pd.read_csv(raw_path, dtype=str, encoding="utf-8-sig")
        if len(frame) != int(receipt["raw_grid_rows"]):
            raise ValueError("historical_pit_merge_part_row_count_mismatch")
        frames.append(frame)
        bindings.append(
            {
                "chunk_index": chunk_index,
                "raw_object_path": raw_path.as_posix(),
                "raw_object_sha256": raw_sha,
                "receipt_path": receipt_path.as_posix(),
                "receipt_sha256": receipt_sha,
                "retrieved_at_utc": str(receipt["retrieved_at_utc"]),
            }
        )

    if expected_chunk_count is None or seen_chunks != set(range(expected_chunk_count)):
        raise ValueError("historical_pit_merge_chunk_set_incomplete")
    if len(availability_values) != 1:
        raise ValueError("historical_pit_merge_availability_boundary_drift")

    raw = pd.concat(frames, ignore_index=True)
    if len(raw) != 109 * len(REQUIRED_RELATIVE_PERIODS):
        raise ValueError("historical_pit_merge_grid_row_count_invalid")
    raw["SP_ENTITY_ID"] = raw["SP_ENTITY_ID"].fillna("").astype(str).str.strip()
    raw["relative_period"] = raw["relative_period"].fillna("").astype(str).str.strip().str.upper()
    expected_pairs = {(entity_id, period) for entity_id in frozen for period in REQUIRED_RELATIVE_PERIODS}
    actual_pairs = list(zip(raw["SP_ENTITY_ID"], raw["relative_period"], strict=True))
    if len(actual_pairs) != len(set(actual_pairs)) or set(actual_pairs) != expected_pairs:
        raise ValueError("historical_pit_merge_entity_period_grid_invalid")
    if set(raw["as_of_date"].astype(str)) != {args.as_of_date}:
        raise ValueError("historical_pit_merge_raw_asof_invalid")
    raw = raw.sort_values(["SP_ENTITY_ID", "relative_period"], kind="stable").reset_index(drop=True)

    binding_body = {
        "as_of_date": args.as_of_date,
        "master_sha256": master_sha,
        "parts": sorted(
            ({"chunk_index": item["chunk_index"], "raw_sha256": item["raw_object_sha256"], "receipt_sha256": item["receipt_sha256"]} for item in bindings),
            key=lambda item: item["chunk_index"],
        ),
    }
    merge_id = hashlib.sha256(
        json.dumps(binding_body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    output_dir = args.output_root / args.as_of_date.replace("-", "") / merge_id
    raw_path = output_dir / "historical_pit_fundamentals_merged.csv"
    raw_sha = _atomic_csv(raw, raw_path)
    retrieval_times = sorted(str(item["retrieved_at_utc"]) for item in bindings)
    receipt = {
        "schema_version": "aov0_ciq_historical_pit_fundamentals_merged_receipt_v1",
        "source_id": SOURCE_ID,
        "provider": "S&P Capital IQ Pro Office SPG",
        "historical_as_of_date": args.as_of_date,
        "pit_available_at_utc": next(iter(availability_values)),
        "availability_semantics": "CONSERVATIVE_END_OF_ASOF_DATE_ANY_TIMEZONE",
        "retrieved_at_utc": retrieval_times[-1],
        "retrieval_window_start_utc": retrieval_times[0],
        "retrieval_window_end_utc": retrieval_times[-1],
        "master_path": args.master.as_posix(),
        "master_sha256": master_sha,
        "frozen_entity_count": 109,
        "relative_periods": list(REQUIRED_RELATIVE_PERIODS),
        "parts": sorted(bindings, key=lambda item: item["chunk_index"]),
        "raw_object_path": raw_path.as_posix(),
        "raw_object_sha256": raw_sha,
        "raw_grid_rows": int(len(raw)),
        "financial_alpha_evidence": 0,
        "evidence_authority": "HISTORICAL_PIT_ONLY_NOT_PROSPECTIVE_CLOCK_AUTHORITY",
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
    receipt_path = output_dir / "historical_pit_fundamentals_merged.receipt.json"
    receipt_sha = _atomic_json(receipt, receipt_path)
    print(
        "HISTORICAL_PIT_MERGE_OK"
        f"\tROWS={len(raw)}"
        f"\tPARTS={len(bindings)}"
        f"\tRAW_SHA256={raw_sha}"
        f"\tRECEIPT_SHA256={receipt_sha}"
        f"\tPATH={receipt_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
