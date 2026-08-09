from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd

from research.aov0.ciq_historical_pit import normalize_historical_pit_fundamentals


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(suffix=".parquet.tmp", dir=path.parent, delete=False) as tmp:
        temp_path = Path(tmp.name)
    try:
        frame.to_parquet(temp_path, index=False)
        new_hash = _sha256(temp_path)
        if path.exists():
            if _sha256(path) != new_hash:
                raise RuntimeError(f"historical_pit_output_conflict:{path}")
            return new_hash
        os.replace(temp_path, path)
        return new_hash
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _atomic_json(payload: dict[str, Any], path: Path) -> str:
    raw = (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise RuntimeError(f"historical_pit_output_conflict:{path}")
        return digest
    with NamedTemporaryFile(suffix=".json.tmp", dir=path.parent, delete=False) as tmp:
        temp_path = Path(tmp.name)
        tmp.write(raw)
        tmp.flush()
        os.fsync(tmp.fileno())
    try:
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return digest


def main() -> int:
    parser = argparse.ArgumentParser(description="Admit one real CIQ historical PIT fundamental cut.")
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--output-root", default=Path("data/aov0/historical_pit"), type=Path)
    args = parser.parse_args()

    raw_hash = _sha256(args.raw)
    receipt_hash = _sha256(args.receipt)
    master_hash = _sha256(args.master)
    receipt = json.loads(args.receipt.read_text(encoding="utf-8-sig"))
    if receipt.get("raw_object_sha256") != raw_hash:
        raise ValueError("historical_pit_raw_receipt_hash_mismatch")
    if receipt.get("master_sha256") != master_hash:
        raise ValueError("historical_pit_master_receipt_hash_mismatch")
    if receipt.get("financial_alpha_evidence") != 0:
        raise ValueError("historical_pit_receipt_financial_alpha_evidence_invalid")
    if receipt.get("prospective_clock_authority") != "NONE":
        raise ValueError("historical_pit_receipt_prospective_authority_invalid")
    if receipt.get("parent_child_mutation_authority") != "NONE":
        raise ValueError("historical_pit_receipt_mutation_authority_invalid")

    master = pd.read_csv(args.master, dtype=str)
    frozen_entity_ids = set(master["SP_ENTITY_ID"].astype(str).str.strip())
    if len(master) != 109 or len(frozen_entity_ids) != 109:
        raise ValueError("historical_pit_master_frozen_109_invalid")

    raw = pd.read_csv(args.raw, dtype=str, encoding="utf-8-sig")
    panel, state, metadata = normalize_historical_pit_fundamentals(
        raw,
        frozen_entity_ids=frozen_entity_ids,
        expected_as_of_date=str(receipt["historical_as_of_date"]),
    )
    if _sha256(args.raw) != raw_hash:
        raise RuntimeError("historical_pit_raw_changed_during_admission")
    if _sha256(args.master) != master_hash:
        raise RuntimeError("historical_pit_master_changed_during_admission")

    output_dir = args.output_root / str(receipt["historical_as_of_date"]).replace("-", "") / raw_hash
    panel_path = output_dir / "fundamental_panel.parquet"
    state_path = output_dir / "fundamental_state.parquet"
    panel_hash = _atomic_parquet(panel, panel_path)
    state_hash = _atomic_parquet(state, state_path)

    admission = {
        "schema_version": "aov0_ciq_historical_pit_admission_receipt_v1",
        "historical_as_of_date": receipt["historical_as_of_date"],
        "pit_available_at_utc": receipt["pit_available_at_utc"],
        "retrieved_at_utc": receipt["retrieved_at_utc"],
        "raw_object_path": args.raw.as_posix(),
        "raw_object_sha256": raw_hash,
        "raw_receipt_path": args.receipt.as_posix(),
        "raw_receipt_sha256": receipt_hash,
        "master_path": args.master.as_posix(),
        "master_sha256": master_hash,
        "fundamental_panel_path": panel_path.as_posix(),
        "fundamental_panel_sha256": panel_hash,
        "fundamental_state_path": state_path.as_posix(),
        "fundamental_state_sha256": state_hash,
        "frozen_entity_count": 109,
        "financial_alpha_evidence": 0,
        "evidence_authority": "HISTORICAL_PIT_ONLY_NOT_PROSPECTIVE_CLOCK_AUTHORITY",
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
        "admission_metadata": metadata,
    }
    receipt_path = output_dir / "admission_receipt.json"
    admission_hash = _atomic_json(admission, receipt_path)
    print(
        "HISTORICAL_PIT_ADMISSION_OK"
        f"\tASOF={admission['historical_as_of_date']}"
        f"\tRAW_SHA256={raw_hash}"
        f"\tPANEL_SHA256={panel_hash}"
        f"\tSTATE_SHA256={state_hash}"
        f"\tRECEIPT_SHA256={admission_hash}"
        f"\tPATH={receipt_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
