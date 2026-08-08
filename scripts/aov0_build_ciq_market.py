"""Build the current AOV-0 CIQ security/market leg and three risky-asset inputs.

Required raw inputs are one bounded primary-security master export and one
same-cut daily primary-security market-history export. Retrieval timestamps are
explicit CLI inputs because local file mtimes are not accepted as provider
retrieval authority.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import tempfile
import sys
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

NY_TZ = ZoneInfo("America/New_York")
US_DAILY_BAR_COMPLETE = datetime.strptime("16:00", "%H:%M").time()

from research.aov0.ciq_market import (
    MARKET_DATA_SOURCE_ID,
    SECURITY_MASTER_SOURCE_ID,
    build_ciq_market_slice,
    read_tabular_export,
    sha256_file,
)


def _default_external_file(name: str) -> Path:
    candidates = [ROOT / name]
    if ROOT.parent.name == ".worktrees":
        candidates.append(ROOT.parent.parent / name)
    candidates.append(Path.cwd() / name)
    return next((path for path in candidates if path.exists()), candidates[0])


def _utc(value: str | datetime, *, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"aov0_ciq_{field}_invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"aov0_ciq_{field}_timezone_required")
    return parsed.astimezone(UTC)


def _utc_text(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _atomic_parquet(frame: pd.DataFrame, path: Path, *, index: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        frame.to_parquet(temp, index=index)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _atomic_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _artifact_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_artifacts(
    *,
    security_master_path: Path,
    market_history_path: Path,
    fundamental_state_path: Path,
    security_retrieved_at: str | datetime,
    market_retrieved_at: str | datetime,
    target_date: str | None,
    security_map_path: Path,
    exclusions_path: Path,
    rule100_path: Path,
    primitives_path: Path,
    returns_path: Path,
    security_receipt_path: Path,
    market_receipt_path: Path,
    now: datetime | None = None,
) -> dict:
    security_time = _utc(security_retrieved_at, field="security_retrieved_at")
    market_time = _utc(market_retrieved_at, field="market_retrieved_at")
    build_time = _utc(now or datetime.now(UTC), field="build_time")
    if security_time > build_time or market_time > build_time:
        raise ValueError("aov0_ciq_source_retrieval_time_in_future")
    admission_time = build_time

    security_hash_before = sha256_file(security_master_path)
    market_hash_before = sha256_file(market_history_path)
    master_raw = read_tabular_export(security_master_path, kind="security_master")
    market_raw = read_tabular_export(market_history_path, kind="market")
    fundamentals = pd.read_parquet(fundamental_state_path)
    result = build_ciq_market_slice(
        security_master_raw=master_raw,
        market_raw=market_raw,
        fundamental_state=fundamentals,
        admission_time=admission_time,
        target_date=target_date,
    )
    decision_date = pd.Timestamp(result.metadata["decision_target_date"]).date()
    market_time_et = market_time.astimezone(NY_TZ)
    if decision_date > market_time_et.date():
        raise ValueError("aov0_ciq_market_target_date_after_retrieval_date")
    if (
        decision_date == market_time_et.date()
        and market_time_et.time().replace(tzinfo=None) < US_DAILY_BAR_COMPLETE
    ):
        raise ValueError(
            "aov0_ciq_current_daily_bar_not_complete_before_1600_et:"
            f"{market_time_et.isoformat()}"
        )
    if sha256_file(security_master_path) != security_hash_before:
        raise RuntimeError("aov0_ciq_security_master_changed_during_admission")
    if sha256_file(market_history_path) != market_hash_before:
        raise RuntimeError("aov0_ciq_market_history_changed_during_admission")

    _atomic_parquet(result.security_map, security_map_path, index=False)
    _atomic_parquet(result.exclusions, exclusions_path, index=False)
    _atomic_parquet(result.market_features, primitives_path, index=False)
    _atomic_parquet(result.rule100_targets.rename_axis("date").reset_index(), rule100_path, index=False)
    _atomic_parquet(result.total_returns.rename_axis("date").reset_index(), returns_path, index=False)

    common = {
        "decision_target_date": result.metadata["decision_target_date"],
        "frozen_entity_count": result.metadata["frozen_entity_count"],
        "canonical_security_count": result.metadata["canonical_security_count"],
        "excluded_entity_count": result.metadata["excluded_entity_count"],
        "rule100_sizing_eligible_count": result.metadata["rule100_sizing_eligible_count"],
        "formula_contract": result.metadata["formula_contract"],
        "current_cut_only": True,
        "historical_rule100_targets_emitted": False,
    }
    security_receipt = {
        "schema_version": "aov0_ciq_primary_security_master_receipt_v1",
        "source_id": SECURITY_MASTER_SOURCE_ID,
        "retrieved_at": _utc_text(security_time),
        "retrieved_at_semantics": "EXPLICIT_PROVIDER_EXPORT_RETRIEVAL_TIME",
        "raw_object_name": security_master_path.name,
        "raw_object_sha256": security_hash_before,
        "raw_object_bytes": security_master_path.stat().st_size,
        **common,
        "outputs": {
            "security_map": {
                "path": _artifact_path(security_map_path),
                "rows": int(len(result.security_map)),
                "sha256": sha256_file(security_map_path),
            },
            "exclusions": {
                "path": _artifact_path(exclusions_path),
                "rows": int(len(result.exclusions)),
                "sha256": sha256_file(exclusions_path),
            },
        },
        "admission_status": "PRIMARY_SECURITY_IDENTITY_ADMITTED_WITH_MECHANICAL_EXCLUSIONS",
    }
    market_receipt = {
        "schema_version": "aov0_ciq_primary_security_market_data_receipt_v1",
        "source_id": MARKET_DATA_SOURCE_ID,
        "retrieved_at": _utc_text(market_time),
        "retrieved_at_semantics": "EXPLICIT_PROVIDER_EXPORT_RETRIEVAL_TIME",
        "raw_object_name": market_history_path.name,
        "raw_object_sha256": market_hash_before,
        "raw_object_bytes": market_history_path.stat().st_size,
        **common,
        "primitive_rows": result.metadata["primitive_rows"],
        "primitive_min_date": result.metadata["primitive_min_date"],
        "primitive_max_date": result.metadata["primitive_max_date"],
        "rule100_risky_gross": result.metadata["rule100_risky_gross"],
        "rule100_max_weight": result.metadata["rule100_max_weight"],
        "outputs": {
            "rule100_targets": {
                "path": _artifact_path(rule100_path),
                "rows": int(len(result.rule100_targets)),
                "sha256": sha256_file(rule100_path),
            },
            "vertical_primitives": {
                "path": _artifact_path(primitives_path),
                "rows": int(len(result.market_features)),
                "sha256": sha256_file(primitives_path),
            },
            "total_returns": {
                "path": _artifact_path(returns_path),
                "rows": int(len(result.total_returns)),
                "sha256": sha256_file(returns_path),
            },
        },
        "admission_status": "THREE_RISKY_ASSET_FIRST_SEAL_INPUTS_ADMITTED",
    }
    _atomic_json(security_receipt, security_receipt_path)
    _atomic_json(market_receipt, market_receipt_path)
    return {
        "status": "THREE_RISKY_ASSET_FIRST_SEAL_INPUTS_ADMITTED",
        "decision_target_date": result.metadata["decision_target_date"],
        "canonical_security_count": result.metadata["canonical_security_count"],
        "excluded_entity_count": result.metadata["excluded_entity_count"],
        "rule100_sizing_eligible_count": result.metadata["rule100_sizing_eligible_count"],
        "rule100_risky_gross": result.metadata["rule100_risky_gross"],
        "security_receipt": _artifact_path(security_receipt_path),
        "market_receipt": _artifact_path(market_receipt_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--security-master", type=Path, default=_default_external_file("ciq_primary_security_master.xlsx"))
    parser.add_argument("--market-history", type=Path, default=_default_external_file("ciq_primary_security_market_history.xlsx"))
    parser.add_argument(
        "--fundamental-state",
        type=Path,
        default=ROOT / "data/aov0/intermediate/ciq_entity_fundamental_state.parquet",
    )
    parser.add_argument("--security-retrieved-at", required=False)
    parser.add_argument("--market-retrieved-at", required=False)
    parser.add_argument("--target-date")
    parser.add_argument(
        "--security-map-out",
        type=Path,
        default=ROOT / "data/aov0/intermediate/ciq_primary_security_map.parquet",
    )
    parser.add_argument(
        "--exclusions-out",
        type=Path,
        default=ROOT / "data/aov0/intermediate/ciq_security_market_exclusions.parquet",
    )
    parser.add_argument(
        "--rule100-out",
        type=Path,
        default=ROOT / "data/aov0/current/rule100_targets.parquet",
    )
    parser.add_argument(
        "--primitives-out",
        type=Path,
        default=ROOT / "data/aov0/current/vertical_primitives.parquet",
    )
    parser.add_argument(
        "--returns-out",
        type=Path,
        default=ROOT / "data/aov0/current/total_returns.parquet",
    )
    parser.add_argument(
        "--security-receipt-out",
        type=Path,
        default=ROOT / "data/aov0/source_receipts/ciq_primary_security_master_current.json",
    )
    parser.add_argument(
        "--market-receipt-out",
        type=Path,
        default=ROOT / "data/aov0/source_receipts/ciq_primary_security_market_data_current.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    missing = [str(path) for path in (args.security_master, args.market_history) if not path.is_file()]
    missing_timestamps = [
        name
        for name, value in (
            ("security_retrieved_at", args.security_retrieved_at),
            ("market_retrieved_at", args.market_retrieved_at),
        )
        if not value
    ]
    if missing or missing_timestamps:
        print(
            json.dumps(
                {
                    "status": "BLOCKED_MISSING_CIQ_RAW_INPUTS_OR_RETRIEVAL_TIMES",
                    "missing_files": missing,
                    "missing_explicit_timestamps": missing_timestamps,
                    "required_security_fields": [
                        "SP_ENTITY_ID/entity_id",
                        "Capital IQ Security ID",
                        "Trading Item/Instrument Item ID",
                        "primary flag if more than one row per entity",
                    ],
                    "required_market_fields": [
                        "date",
                        "Capital IQ Security ID or exact Trading Item ID",
                        "Trading Item/Instrument Item ID",
                        "Total Return (%) or Total Return Index",
                        "close/adjusted close",
                        "volume",
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    result = build_artifacts(
        security_master_path=args.security_master,
        market_history_path=args.market_history,
        fundamental_state_path=args.fundamental_state,
        security_retrieved_at=args.security_retrieved_at,
        market_retrieved_at=args.market_retrieved_at,
        target_date=args.target_date,
        security_map_path=args.security_map_out,
        exclusions_path=args.exclusions_out,
        rule100_path=args.rule100_out,
        primitives_path=args.primitives_out,
        returns_path=args.returns_out,
        security_receipt_path=args.security_receipt_out,
        market_receipt_path=args.market_receipt_out,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
