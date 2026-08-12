"""Frozen ETF-relative M0 transforms for SECTOR_ROTATION_ALPHA_v1."""

from __future__ import annotations

from collections import defaultdict
from math import isfinite, log
from statistics import fmean, median
from typing import Any, Mapping

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.manifests import canonical_value
from research.sector_rotation_alpha_v1.contracts import (
    FAMILY_ID,
    FEATURE_PACKET_SCHEMA,
    MIN_HISTORY_SESSIONS,
    PARTICIPATION_LONG_WINDOW,
    PARTICIPATION_SHORT_WINDOW,
    RELATIVE_LONG_WINDOW,
    RELATIVE_SHORT_WINDOW,
)
from research.sector_rotation_alpha_v1.pit_packet import verify_sector_rotation_input_packet


def compute_m0_features(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Compute frozen ETF-only relative-strength and participation features."""

    verify_sector_rotation_input_packet(packet)
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in packet["market_rows"]:
        grouped[str(row["security_id"])].append(row)

    raw_rows: list[dict[str, Any]] = []
    sector_map = dict(packet["sector_key_by_security"])
    for security_id in packet["risk_set_security_ids"]:
        rows = sorted(grouped[str(security_id)], key=lambda row: str(row["session_date"]))
        raw_rows.append(_raw_feature_row(str(security_id), str(sector_map[str(security_id)]), rows))

    ready = [row for row in raw_rows if row["feature_status"] == "READY"]
    median_ret20 = median(float(row["return_20"]) for row in ready) if ready else None
    median_ret60 = median(float(row["return_60"]) for row in ready) if ready else None

    feature_rows: list[dict[str, Any]] = []
    for row in sorted(raw_rows, key=lambda item: str(item["sector_key"])):
        if row["feature_status"] != "READY":
            feature_rows.append(row)
            continue
        rel20 = float(row["return_20"]) - float(median_ret20)
        rel60 = float(row["return_60"]) - float(median_ret60)
        feature_rows.append(
            {
                **row,
                "relative_strength_20": format(rel20, ".17g"),
                "relative_strength_60": format(rel60, ".17g"),
            }
        )

    body = {
        "schema_version": FEATURE_PACKET_SCHEMA,
        "family_id": FAMILY_ID,
        "implementation_id": packet["implementation_id"],
        "decision_session_date": packet["decision_session_date"],
        "input_packet_sha256": packet["input_packet_sha256"],
        "cross_section_median_return_20": None if median_ret20 is None else format(float(median_ret20), ".17g"),
        "cross_section_median_return_60": None if median_ret60 is None else format(float(median_ret60), ".17g"),
        "rows": feature_rows,
        "row_count": len(feature_rows),
        "stock_sector_map_used": False,
        "stock_breadth_used": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    feature_packet_sha256 = domain_hash(
        "SECTOR_ROTATION_ALPHA_V1:M0_FEATURES",
        canonical_value(body),
    )
    return {**body, "feature_packet_sha256": feature_packet_sha256}


def verify_m0_features(features: Mapping[str, Any]) -> None:
    if not isinstance(features, Mapping):
        raise ValueError("sra_feature_packet_mapping_required")
    if features.get("schema_version") != FEATURE_PACKET_SCHEMA or features.get("family_id") != FAMILY_ID:
        raise ValueError("sra_feature_packet_identity_invalid")
    if features.get("financial_alpha_evidence") != 0 or features.get("capital_authority") != "NONE":
        raise ValueError("sra_feature_packet_authority_invalid")
    if features.get("stock_sector_map_used") is not False or features.get("stock_breadth_used") is not False:
        raise ValueError("sra_feature_packet_stock_dependency_forbidden")
    rows = features.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("sra_feature_rows_required")
    if len(rows) != int(features.get("row_count", -1)):
        raise ValueError("sra_feature_row_count_invalid")
    sealed = str(features.get("feature_packet_sha256") or "")
    body = {key: value for key, value in features.items() if key != "feature_packet_sha256"}
    expected = domain_hash("SECTOR_ROTATION_ALPHA_V1:M0_FEATURES", canonical_value(body))
    if sealed != expected:
        raise ValueError("sra_feature_packet_hash_mismatch")


def _raw_feature_row(security_id: str, sector_key: str, rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    invalid: list[str] = []
    if len(rows) < MIN_HISTORY_SESSIONS:
        invalid.append("INSUFFICIENT_60_SESSION_HISTORY")
    if invalid:
        return _invalid_row(security_id, sector_key, invalid)

    selected = rows[-MIN_HISTORY_SESSIONS:]
    returns = [float(row["total_return_1d"]) for row in selected]
    closes = [float(row["close"]) for row in selected]
    volumes = [float(row["volume"]) for row in selected]
    if any((not isfinite(value)) or value <= -1.0 for value in returns):
        invalid.append("INVALID_TOTAL_RETURN_DOMAIN")
    dollar_volumes = [close * volume for close, volume in zip(closes, volumes, strict=True)]
    if any((not isfinite(value)) or value <= 0.0 for value in dollar_volumes):
        invalid.append("NONPOSITIVE_ETF_DOLLAR_VOLUME")
    if invalid:
        return _invalid_row(security_id, sector_key, invalid)

    ret20 = _compound(returns[-RELATIVE_SHORT_WINDOW:])
    ret60 = _compound(returns[-RELATIVE_LONG_WINDOW:])
    dv5 = fmean(dollar_volumes[-PARTICIPATION_SHORT_WINDOW:])
    dv20 = fmean(dollar_volumes[-PARTICIPATION_LONG_WINDOW:])
    if dv5 <= 0 or dv20 <= 0:
        return _invalid_row(security_id, sector_key, ["NONPOSITIVE_ETF_DOLLAR_VOLUME_MEAN"])
    participation = log(dv5 / dv20)
    if not all(isfinite(value) for value in (ret20, ret60, participation)):
        return _invalid_row(security_id, sector_key, ["NONFINITE_M0_FEATURE"])

    return {
        "security_id": security_id,
        "sector_key": sector_key,
        "feature_status": "READY",
        "invalid_reasons": [],
        "return_20": format(ret20, ".17g"),
        "return_60": format(ret60, ".17g"),
        "relative_strength_20": None,
        "relative_strength_60": None,
        "dollar_volume_participation": format(participation, ".17g"),
    }


def _invalid_row(security_id: str, sector_key: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "security_id": security_id,
        "sector_key": sector_key,
        "feature_status": "INSUFFICIENT_OR_INVALID_M0_HISTORY",
        "invalid_reasons": list(reasons),
        "return_20": None,
        "return_60": None,
        "relative_strength_20": None,
        "relative_strength_60": None,
        "dollar_volume_participation": None,
    }


def _compound(values: list[float]) -> float:
    result = 1.0
    for value in values:
        result *= 1.0 + value
    return result - 1.0
