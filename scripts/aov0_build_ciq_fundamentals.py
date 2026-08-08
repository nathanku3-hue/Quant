"""Build the bounded AOV-0 Capital IQ company-fundamental intermediate artifacts."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import tempfile
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.aov0.ciq_fundamentals import (
    IDENTITY_STATUS,
    PIT_MODE,
    SOURCE_ID,
    build_run4_slice,
    sha256_file,
)


def _repo_root() -> Path:
    return ROOT


def _default_external_file(name: str) -> Path:
    root = _repo_root()
    candidates = [root / name]
    if root.parent.name == ".worktrees":
        candidates.append(root.parent.parent / name)
    candidates.append(Path.cwd() / name)
    return next((path for path in candidates if path.exists()), candidates[0])


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        frame.to_parquet(temp, index=False)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _artifact_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _atomic_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def build_artifacts(
    *,
    run4_path: Path,
    panel_path: Path,
    state_path: Path,
    receipt_path: Path,
    admission_time: datetime | None = None,
) -> dict:
    admitted = (admission_time or datetime.now(UTC)).astimezone(UTC)
    panel, state, metadata = build_run4_slice(
        run4_path,
        admission_time=admitted,
    )
    _atomic_parquet(panel, panel_path)
    _atomic_parquet(state, state_path)

    source_mtime = datetime.fromtimestamp(run4_path.stat().st_mtime, tz=UTC)
    receipt = {
        "schema_version": "aov0_ciq_company_universe_fundamentals_receipt_v1",
        "source_id": SOURCE_ID,
        "authority_roles": metadata["authority_roles"],
        "company_universe_entity_count": metadata["company_universe_entity_count"],
        "company_universe_raw_object_sha256": metadata["company_universe_raw_object_sha256"],
        "raw_object_name": run4_path.name,
        "raw_object_sha256": metadata["raw_object_sha256"],
        "raw_object_bytes": metadata["raw_object_bytes"],
        "raw_object_file_mtime_utc": source_mtime.isoformat().replace("+00:00", "Z"),
        "retrieved_at": metadata["admission_time_utc"],
        "retrieved_at_semantics": "CONSERVATIVE_LOCAL_ADMISSION_TIME_NOT_VENDOR_QUERY_TIMESTAMP",
        "capture_mode": "LOCAL_CAPITAL_IQ_EXPORT_ADMISSION_CURRENT_CUT",
        "identity_status": IDENTITY_STATUS,
        "pit_mode": PIT_MODE,
        "quarter_reference_mode": metadata["quarter_reference_mode"],
        "historical_publication_timestamps_embedded": False,
        "source_entity_count": metadata["source_entity_count"],
        "absolute_history_entity_count": metadata["absolute_history_entity_count"],
        "no_absolute_history_entity_ids": metadata["no_absolute_history_entity_ids"],
        "quarter_row_count": metadata["quarter_row_count"],
        "quarter_min": metadata["quarter_min"],
        "quarter_max": metadata["quarter_max"],
        "fundamental_spec_registry_hash": metadata["fundamental_spec_registry_hash"],
        "rule100_factor_group_contract_hash": metadata["rule100_factor_group_contract_hash"],
        "factor_coverage": metadata["factor_coverage"],
        "raw_factor_input_coverage": metadata["raw_factor_input_coverage"],
        "factor_state_status_counts": metadata["factor_state_status_counts"],
        "outputs": {
            "quarterly_panel": {
                "path": _artifact_path(panel_path),
                "rows": int(len(panel)),
                "sha256": sha256_file(panel_path),
            },
            "current_fundamental_state": {
                "path": _artifact_path(state_path),
                "rows": int(len(state)),
                "sha256": sha256_file(state_path),
            },
        },
        "admission_status": "FUNDAMENTAL_STATE_READY_SECURITY_AND_MARKET_DATA_STILL_REQUIRED",
        "remaining_first_seal_gates": [
            "Capital IQ Security ID primary-security mapping",
            "Capital IQ primary-security daily market/total-return history",
            "technical_quality and market-derived vertical primitives",
            "Rule100 target weights on canonical CIQSEC identity",
            "total_returns.parquet",
            "official_sofr.parquet after publication gate",
            "aov0_ciq_decision_cut_v1",
        ],
        "notes": [
            "SP_ENTITY_ID is retained only as a temporary company-level source key and is not a permanent security identifier.",
            "Ticker is not used as permanent identity.",
            "No yfinance/local substitute returns are generated or admitted by this slice.",
            "Relative FQ0 columns are excluded from the historical panel; only absolute FQqYYYY references are normalized.",
            "The workbook lacks complete per-quarter historical publication timestamps; known_at is therefore the conservative local admission time for all rows.",
            "The same hash-bound run_4 workbook is the sole frozen 109-company universe receipt and current-cut quarterly-fundamentals receipt; run_2 is not an active dependency.",
            "This artifact supports the current-cut fundamental factor state only and does not authorize historical PIT replay.",
        ],
    }
    _atomic_json(receipt, receipt_path)
    return receipt


def parse_args() -> argparse.Namespace:
    root = _repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run4", type=Path, default=_default_external_file("run_4.xlsx"))
    parser.add_argument(
        "--panel-out",
        type=Path,
        default=root / "data/aov0/intermediate/ciq_entity_quarterly_panel.parquet",
    )
    parser.add_argument(
        "--state-out",
        type=Path,
        default=root / "data/aov0/intermediate/ciq_entity_fundamental_state.parquet",
    )
    parser.add_argument(
        "--receipt-out",
        type=Path,
        default=root / "data/aov0/source_receipts/ciq_quarterly_fundamentals_run_4_20260807.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = build_artifacts(
        run4_path=args.run4,
        panel_path=args.panel_out,
        state_path=args.state_out,
        receipt_path=args.receipt_out,
    )
    summary = {
        "status": receipt["admission_status"],
        "source_entity_count": receipt["source_entity_count"],
        "absolute_history_entity_count": receipt["absolute_history_entity_count"],
        "quarter_row_count": receipt["quarter_row_count"],
        "state_rows": receipt["outputs"]["current_fundamental_state"]["rows"],
        "no_absolute_history_entity_ids": receipt["no_absolute_history_entity_ids"],
        "receipt": str(args.receipt_out),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
