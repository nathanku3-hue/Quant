"""Frozen 20/60/20 M0 transforms for VOL_SQUEEZE_BREAKOUT_v1."""

from __future__ import annotations

from collections import defaultdict
from math import log
from statistics import median, stdev
from typing import Any, Mapping

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.manifests import canonical_value
from research.vol_squeeze_breakout_v1.contracts import (
    BREAKOUT_WINDOW,
    FAMILY_ID,
    FEATURE_PACKET_SCHEMA,
    RV_LONG_WINDOW,
    RV_SHORT_WINDOW,
    VOLUME_WINDOW,
)
from research.vol_squeeze_breakout_v1.pit_packet import verify_vsb_input_packet


def compute_m0_features(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Compute the preregistered M0 feature vector at the sealed decision session."""

    verify_vsb_input_packet(packet)
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in packet["market_rows"]:
        grouped[str(row["security_id"])].append(row)

    feature_rows: list[dict[str, Any]] = []
    for security_id in sorted(packet["risk_set_security_ids"]):
        rows = sorted(grouped[security_id], key=lambda row: str(row["session_date"]))
        feature_rows.append(_feature_row(security_id, rows))

    body = {
        "schema_version": FEATURE_PACKET_SCHEMA,
        "family_id": FAMILY_ID,
        "implementation_id": packet["implementation_id"],
        "decision_session_date": packet["decision_session_date"],
        "input_packet_sha256": packet["input_packet_sha256"],
        "rows": feature_rows,
        "row_count": len(feature_rows),
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    feature_packet_sha256 = domain_hash(
        "VOL_SQUEEZE_BREAKOUT_V1:M0_FEATURES",
        canonical_value(body),
    )
    return {**body, "feature_packet_sha256": feature_packet_sha256}


def verify_m0_features(features: Mapping[str, Any]) -> None:
    if not isinstance(features, Mapping):
        raise ValueError("vsb_feature_packet_mapping_required")
    if features.get("schema_version") != FEATURE_PACKET_SCHEMA or features.get("family_id") != FAMILY_ID:
        raise ValueError("vsb_feature_packet_identity_invalid")
    if features.get("financial_alpha_evidence") != 0 or features.get("capital_authority") != "NONE":
        raise ValueError("vsb_feature_packet_authority_invalid")
    sealed = str(features.get("feature_packet_sha256") or "")
    body = {key: value for key, value in features.items() if key != "feature_packet_sha256"}
    expected = domain_hash("VOL_SQUEEZE_BREAKOUT_V1:M0_FEATURES", canonical_value(body))
    if sealed != expected:
        raise ValueError("vsb_feature_packet_hash_mismatch")


def _feature_row(security_id: str, rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    returns = [float(row["total_return_1d"]) for row in rows]
    closes = [float(row["close"]) for row in rows]
    volumes = [float(row["volume"]) for row in rows]

    rv20 = stdev(returns[-RV_SHORT_WINDOW:])
    rv60 = stdev(returns[-RV_LONG_WINDOW:])
    prior_high20 = max(closes[-(BREAKOUT_WINDOW + 1) : -1])
    prior_volume_median20 = median(volumes[-(VOLUME_WINDOW + 1) : -1])
    close_t = closes[-1]
    volume_t = volumes[-1]

    invalid: list[str] = []
    if rv20 <= 0:
        invalid.append("NONPOSITIVE_RV20")
    if rv60 <= 0:
        invalid.append("NONPOSITIVE_RV60")
    if prior_high20 <= 0:
        invalid.append("NONPOSITIVE_PRIOR_HIGH20")
    if close_t <= 0:
        invalid.append("NONPOSITIVE_CLOSE_T")
    if prior_volume_median20 <= 0:
        invalid.append("NONPOSITIVE_PRIOR_VOLUME_MEDIAN20")
    if volume_t <= 0:
        invalid.append("NONPOSITIVE_VOLUME_T")

    if invalid:
        return {
            "security_id": security_id,
            "feature_status": "INSUFFICIENT_OR_INVALID_M0_HISTORY",
            "invalid_reasons": invalid,
            "compression": None,
            "breakout": None,
            "volume_expansion": None,
        }

    compression = log(rv60 / rv20)
    breakout = log(close_t / prior_high20)
    volume_expansion = log(volume_t / prior_volume_median20)
    return {
        "security_id": security_id,
        "feature_status": "READY",
        "invalid_reasons": [],
        "compression": format(compression, ".17g"),
        "breakout": format(breakout, ".17g"),
        "volume_expansion": format(volume_expansion, ".17g"),
    }
