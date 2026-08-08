"""Construct the exact current AOV-0 CIQ decision-cut envelope.

This script does not acquire data and does not run the seal. It binds the four
admitted Parquet inputs, frozen executable contract, mechanically recomputed
CIQ security universe, four raw-source receipts, knowledge cutoff, target date,
cut-build time, and explicitly supplied next eligible close evaluation start. The real
prospective seal stamps its own later write time. The single
hash-bound ``run_4.xlsx`` receipt is the active authority for both the frozen
109-company universe and current-cut quarterly fundamentals; ``run_2`` is not an
active dependency.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gv_fs0_canonical import domain_hash
from research.aov0.contracts import DEFAULT_CONTRACT, normalize_security_id
from scripts.aov0_first_seal import (
    BOUND_PARQUET_INPUTS,
    DECISION_CUT_SCHEMA,
    EXECUTION_CALENDAR_ID,
    REQUIRED_SOURCE_RECEIPTS,
    _load_decision_cut,
    _universe_hash_from_primitives,
    _validate_evaluation_start,
)


DEFAULT_INPUT_ROOT = ROOT / "data/aov0/current"
DEFAULT_RECEIPT_ROOT = ROOT / "data/aov0/source_receipts"
NY_TZ = ZoneInfo("America/New_York")
US_DAILY_BAR_COMPLETE_HOUR = 16


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"aov0_decision_cut_duplicate_json_key:{key}")
        output[key] = value
    return output


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError(f"aov0_decision_cut_receipt_json_invalid:{path.name}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"aov0_decision_cut_receipt_object_required:{path.name}")
    return payload


def _timestamp(value: object, *, field: str) -> pd.Timestamp:
    try:
        parsed = pd.Timestamp(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"aov0_decision_cut_{field}_invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"aov0_decision_cut_{field}_timezone_required")
    return parsed.tz_convert("UTC")


def _utc_text(value: pd.Timestamp | datetime) -> str:
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize("UTC")
    else:
        parsed = parsed.tz_convert("UTC")
    return parsed.isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_receipt(
    path: Path,
    *,
    expected_source_id: str,
    retrieved_at_override: str | None = None,
) -> dict[str, str]:
    payload = _load_json(path)
    source_id = str(payload.get("source_id") or "")
    if source_id != expected_source_id:
        raise ValueError(f"aov0_decision_cut_source_id_mismatch:{path.name}")
    raw_hash = str(payload.get("raw_object_sha256") or "")
    if len(raw_hash) != 64 or any(char not in "0123456789abcdef" for char in raw_hash):
        raise ValueError(f"aov0_decision_cut_raw_hash_invalid:{path.name}")
    retrieved = retrieved_at_override or payload.get("retrieved_at")
    if not retrieved:
        raise ValueError(f"aov0_decision_cut_retrieved_at_required:{path.name}")
    retrieved_ts = _timestamp(retrieved, field=f"retrieved_at_{path.name}")
    return {
        "source_id": source_id,
        "retrieved_at": _utc_text(retrieved_ts),
        "raw_object_sha256": raw_hash,
    }


def _wide_target_date(path: Path, *, name: str) -> tuple[pd.Timestamp, pd.DataFrame]:
    frame = pd.read_parquet(path)
    if "date" not in frame.columns or frame.empty:
        raise ValueError(f"aov0_decision_cut_{name}_date_column_required")
    dates = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    if dates.duplicated().any():
        raise ValueError(f"aov0_decision_cut_{name}_duplicate_date")
    return dates.max(), frame


def _derive_target_date(
    *,
    rule100_path: Path,
    returns_path: Path,
    primitives_path: Path,
) -> tuple[pd.Timestamp, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rule_date, rule = _wide_target_date(rule100_path, name="rule100")
    return_date, returns = _wide_target_date(returns_path, name="returns")
    primitives = pd.read_parquet(primitives_path)
    if primitives.empty or "date" not in primitives.columns:
        raise ValueError("aov0_decision_cut_primitives_date_column_required")
    primitive_dates = pd.to_datetime(primitives["date"], errors="raise").dt.normalize()
    primitive_date = primitive_dates.max()
    if not (rule_date == return_date == primitive_date):
        raise ValueError("aov0_decision_cut_target_date_mismatch")
    return rule_date, rule, returns, primitives


def _validate_target_market_alignment(
    *,
    target_date: pd.Timestamp,
    rule100: pd.DataFrame,
    returns: pd.DataFrame,
    primitives: pd.DataFrame,
) -> None:
    rule_assets = [str(column) for column in rule100.columns if column != "date"]
    return_assets = [str(column) for column in returns.columns if column != "date"]
    try:
        rule_ids = [normalize_security_id(column) for column in rule_assets]
        return_ids = [normalize_security_id(column) for column in return_assets]
    except ValueError as exc:
        raise ValueError("aov0_decision_cut_ciq_security_id_columns_required") from exc
    if len(set(rule_ids)) != len(rule_ids) or len(set(return_ids)) != len(return_ids):
        raise ValueError("aov0_decision_cut_duplicate_security_id_columns")
    if set(rule_ids) != set(return_ids):
        raise ValueError("aov0_decision_cut_rule100_return_asset_set_mismatch")

    required = {"date", "security_id", "total_return"}
    if not required.issubset(primitives.columns):
        raise ValueError("aov0_decision_cut_target_return_alignment_columns_required")
    primitive_dates = pd.to_datetime(primitives["date"], errors="raise").dt.normalize()
    target = primitives.loc[primitive_dates.eq(target_date), ["security_id", "total_return"]].copy()
    if target.empty:
        raise ValueError("aov0_decision_cut_target_primitives_missing")
    try:
        target["security_id"] = target["security_id"].map(normalize_security_id)
    except ValueError as exc:
        raise ValueError("aov0_decision_cut_target_primitive_ciq_id_invalid") from exc
    if target["security_id"].duplicated().any():
        raise ValueError("aov0_decision_cut_target_primitive_duplicate_security")
    if set(target["security_id"].astype(str)) != set(return_ids):
        raise ValueError("aov0_decision_cut_target_primitive_asset_set_mismatch")

    return_row = returns.loc[pd.to_datetime(returns["date"], errors="raise").dt.normalize().eq(target_date)]
    if len(return_row) != 1:
        raise ValueError("aov0_decision_cut_target_return_row_invalid")
    return_vector = pd.Series(
        {
            normalize_security_id(column): pd.to_numeric(return_row.iloc[0][column], errors="coerce")
            for column in return_assets
        },
        dtype=float,
    ).sort_index()
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
        raise ValueError("aov0_decision_cut_target_total_return_non_finite")
    if not np.allclose(
        return_vector.to_numpy(dtype=float),
        primitive_vector.to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-15,
    ):
        raise ValueError("aov0_decision_cut_target_total_return_mismatch")


def _knowledge_cutoff(
    *,
    source_receipts: dict[str, dict[str, str]],
    primitives: pd.DataFrame,
    sofr_path: Path,
) -> pd.Timestamp:
    times = [
        _timestamp(receipt["retrieved_at"], field=f"source_receipt_{name}")
        for name, receipt in source_receipts.items()
    ]
    if "known_at" not in primitives.columns:
        raise ValueError("aov0_decision_cut_primitives_known_at_required")
    primitive_known = pd.to_datetime(primitives["known_at"], utc=True, errors="raise", format="mixed")
    if primitive_known.empty:
        raise ValueError("aov0_decision_cut_primitives_empty")
    times.append(primitive_known.max())

    sofr = pd.read_parquet(sofr_path)
    if sofr.empty or "published_at" not in sofr.columns:
        raise ValueError("aov0_decision_cut_sofr_published_at_required")
    published = pd.to_datetime(sofr["published_at"], utc=True, errors="raise", format="mixed")
    times.append(published.max())
    return max(times)


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def build_decision_cut(
    *,
    rule100_path: Path,
    primitives_path: Path,
    returns_path: Path,
    sofr_path: Path,
    fundamentals_receipt_path: Path,
    security_receipt_path: Path,
    market_receipt_path: Path,
    sofr_receipt_path: Path,
    evaluation_start: str,
    output_path: Path,
    cut_built_at: datetime | pd.Timestamp | None = None,
) -> dict[str, Any]:
    paths = {
        "rule100_targets": Path(rule100_path),
        "vertical_primitives": Path(primitives_path),
        "total_returns": Path(returns_path),
        "official_sofr": Path(sofr_path),
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    receipt_paths = {
        "ciq_quarterly_fundamentals": Path(fundamentals_receipt_path),
        "ciq_security_master": Path(security_receipt_path),
        "ciq_market_data": Path(market_receipt_path),
        "nyfed_sofr": Path(sofr_receipt_path),
    }
    missing_receipts = [name for name, path in receipt_paths.items() if not path.is_file()]
    if missing or missing_receipts:
        raise FileNotFoundError(
            "aov0_decision_cut_missing_inputs:"
            f"parquets={','.join(missing)};receipts={','.join(missing_receipts)}"
        )

    source_receipts = {
        "ciq_quarterly_fundamentals": _extract_receipt(
            receipt_paths["ciq_quarterly_fundamentals"],
            expected_source_id=REQUIRED_SOURCE_RECEIPTS["ciq_quarterly_fundamentals"],
        ),
        "ciq_security_master": _extract_receipt(
            receipt_paths["ciq_security_master"],
            expected_source_id=REQUIRED_SOURCE_RECEIPTS["ciq_security_master"],
        ),
        "ciq_market_data": _extract_receipt(
            receipt_paths["ciq_market_data"],
            expected_source_id=REQUIRED_SOURCE_RECEIPTS["ciq_market_data"],
        ),
        "nyfed_sofr": _extract_receipt(
            receipt_paths["nyfed_sofr"],
            expected_source_id=REQUIRED_SOURCE_RECEIPTS["nyfed_sofr"],
        ),
    }

    target_date, rule100, returns, primitives = _derive_target_date(
        rule100_path=paths["rule100_targets"],
        returns_path=paths["total_returns"],
        primitives_path=paths["vertical_primitives"],
    )
    _validate_target_market_alignment(
        target_date=target_date,
        rule100=rule100,
        returns=returns,
        primitives=primitives,
    )
    market_retrieved_et = _timestamp(
        source_receipts["ciq_market_data"]["retrieved_at"],
        field="ciq_market_data_retrieved_at",
    ).tz_convert(NY_TZ)
    if target_date.date() > market_retrieved_et.date():
        raise ValueError("aov0_decision_cut_market_target_after_retrieval_date")
    if (
        target_date.date() == market_retrieved_et.date()
        and market_retrieved_et.hour < US_DAILY_BAR_COMPLETE_HOUR
    ):
        raise ValueError("aov0_decision_cut_current_daily_bar_not_complete_before_1600_et")

    knowledge_cutoff = _knowledge_cutoff(
        source_receipts=source_receipts,
        primitives=primitives,
        sofr_path=paths["official_sofr"],
    )
    evaluation = _timestamp(evaluation_start, field="evaluation_start")
    _validate_evaluation_start(target_date, evaluation)
    built = pd.Timestamp(cut_built_at or datetime.now(UTC))
    built = built.tz_localize("UTC") if built.tzinfo is None else built.tz_convert("UTC")
    if built < knowledge_cutoff:
        raise ValueError("aov0_decision_cut_built_before_knowledge_cutoff")
    if evaluation <= built:
        raise ValueError("aov0_decision_cut_evaluation_not_after_cut")

    input_sha256 = {name: _sha256(path) for name, path in paths.items()}
    universe_hash = _universe_hash_from_primitives(primitives)
    identity = {
        "schema_version": DECISION_CUT_SCHEMA,
        "decision_target_date": target_date.date().isoformat(),
        "knowledge_cutoff": _utc_text(knowledge_cutoff),
        "cut_built_at": _utc_text(built),
        "evaluation_start": _utc_text(evaluation),
        "execution_calendar_id": EXECUTION_CALENDAR_ID,
        "input_sha256": input_sha256,
        "contract_hash": DEFAULT_CONTRACT.contract_hash,
        "universe_hash": universe_hash,
        "source_receipts": source_receipts,
    }
    cut_hash = domain_hash("AOV0:CIQ_DECISION_CUT:V3", identity)
    payload = {
        "schema_version": DECISION_CUT_SCHEMA,
        "decision_cut_id": f"AOV0_CIQ_{target_date.strftime('%Y%m%d')}_{cut_hash[:16]}",
        "knowledge_cutoff": _utc_text(knowledge_cutoff),
        "cut_built_at": _utc_text(built),
        "decision_target_date": target_date.date().isoformat(),
        "evaluation_start": _utc_text(evaluation),
        "execution_calendar_id": EXECUTION_CALENDAR_ID,
        "input_sha256": input_sha256,
        "contract_hash": DEFAULT_CONTRACT.contract_hash,
        "universe_hash": universe_hash,
        "source_receipts": source_receipts,
    }
    _atomic_json(payload, output_path)
    # Re-read through the actual first-seal parser before returning authority.
    validated = _load_decision_cut(output_path)
    return {
        "status": "AOV0_CIQ_DECISION_CUT_READY",
        "decision_cut_id": validated["decision_cut_id"],
        "knowledge_cutoff": validated["knowledge_cutoff"],
        "cut_built_at": validated["cut_built_at"],
        "decision_target_date": validated["decision_target_date"],
        "evaluation_start": validated["evaluation_start"],
        "output": output_path.as_posix(),
        "sha256": _sha256(output_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--receipt-root", type=Path, default=DEFAULT_RECEIPT_ROOT)
    parser.add_argument("--evaluation-start", required=True, help="Next eligible NYSE core close, timezone required")
    parser.add_argument("--out", type=Path, default=DEFAULT_INPUT_ROOT / "decision_cut.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = build_decision_cut(
            rule100_path=args.input_root / "rule100_targets.parquet",
            primitives_path=args.input_root / "vertical_primitives.parquet",
            returns_path=args.input_root / "total_returns.parquet",
            sofr_path=args.input_root / "official_sofr.parquet",
            fundamentals_receipt_path=args.receipt_root / "ciq_quarterly_fundamentals_run_4_20260807.json",
            security_receipt_path=args.receipt_root / "ciq_primary_security_master_current.json",
            market_receipt_path=args.receipt_root / "ciq_primary_security_market_data_current.json",
            sofr_receipt_path=args.receipt_root / "nyfed_sofr_current.json",
            evaluation_start=args.evaluation_start,
            output_path=args.out,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED_DECISION_CUT_INPUT_INTEGRITY", "reason": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
