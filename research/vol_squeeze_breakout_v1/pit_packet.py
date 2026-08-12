"""Provider-blind source-bound PIT packet for VOL_SQUEEZE_BREAKOUT_v1."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from math import isfinite
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import (
    ArtifactRef,
    ResearchMode,
    utc_datetime,
    validate_security_ids,
)
from research.alpha_pit_v1.manifests import canonical_value, verify_artifact_ref
from research.alpha_pit_v1.session import AlphaPITReadAPIv1
from research.vol_squeeze_breakout_v1.contracts import (
    FAMILY_DATA_CONTRACT,
    FAMILY_DATA_CONTRACT_SHA256,
    FAMILY_ID,
    INPUT_PACKET_SCHEMA,
    MARKET_HISTORY_ARTIFACT_TYPE,
    MARKET_HISTORY_SCHEMA,
    MIN_HISTORY_SESSIONS,
    PRIMARY_LABEL_SPEC_ID,
    RISK_SET_SPEC_ID,
    validate_vsb_contract,
)


_MARKET_ROW_FIELDS = {
    "security_id",
    "session_date",
    "close",
    "total_return_1d",
    "volume",
    "observed_at",
    "available_at",
    "coverage_status",
}


def build_vsb_input_packet(
    *,
    api: AlphaPITReadAPIv1,
    market_history: ArtifactRef,
    implementation_id: str,
    as_of: datetime,
) -> dict[str, Any]:
    """Bind one VSB risk-set snapshot to one source-bound daily market-history artifact."""

    validate_vsb_contract()
    cutoff = utc_datetime(as_of)
    implementation = str(implementation_id).strip()
    if not implementation:
        raise ValueError("vsb_implementation_id_required")
    if api.family_id != FAMILY_ID or api.family_contract != FAMILY_DATA_CONTRACT:
        raise ValueError("vsb_alpha_pit_family_contract_mismatch")
    if api.research_mode is ResearchMode.DISCOVERY:
        raise ValueError("vsb_prediction_packet_discovery_mode_forbidden")

    risk_set = api.risk_set(as_of=cutoff)
    risk_payload = _mapping(risk_set.payload, "risk_set")
    risk_set_id = str(risk_payload.get("risk_set_id") or "")
    if not risk_set_id:
        raise ValueError("vsb_risk_set_id_required")
    risk_rows = _rows(risk_payload, "risk_set")
    risk_ids = tuple(
        sorted(validate_security_ids([str(row.get("security_id") or "") for row in risk_rows]))
    )
    if not risk_ids:
        raise ValueError("vsb_empty_risk_set")

    verify_artifact_ref(market_history, family_contract=FAMILY_DATA_CONTRACT)
    if market_history.artifact_type != MARKET_HISTORY_ARTIFACT_TYPE:
        raise ValueError("vsb_market_history_artifact_type_invalid")
    manifest = market_history.manifest
    if manifest.get("research_mode") != api.research_mode.value:
        raise ValueError("vsb_market_history_research_mode_invalid")
    if manifest.get("financial_alpha_evidence") != 0:
        raise ValueError("vsb_financial_alpha_evidence_must_be_zero")

    market_payload = _mapping(market_history.payload, "market_history")
    if market_payload.get("schema_version") != MARKET_HISTORY_SCHEMA:
        raise ValueError("vsb_market_history_schema_invalid")
    if market_payload.get("family_id") != FAMILY_ID:
        raise ValueError("vsb_market_history_family_invalid")
    if market_payload.get("risk_set_id") != risk_set_id:
        raise ValueError("vsb_market_history_risk_set_binding_invalid")
    decision_session_date = _date_text(
        market_payload.get("decision_session_date"),
        "decision_session_date",
    )
    rows = _rows(market_payload, "market_history")
    if int(market_payload.get("row_count", -1)) != len(rows):
        raise ValueError("vsb_market_history_row_count_invalid")

    history_counts, canonical_rows = _validate_market_rows(
        rows,
        risk_ids=risk_ids,
        decision_session_date=decision_session_date,
        as_of=cutoff,
    )
    authority_classes = {
        str(risk_set.manifest.get("authority_class") or ""),
        str(market_history.manifest.get("authority_class") or ""),
    }
    if len(authority_classes) != 1:
        raise ValueError("vsb_mixed_input_authority_forbidden")

    body = {
        "schema_version": INPUT_PACKET_SCHEMA,
        "family_id": FAMILY_ID,
        "family_data_contract_sha256": FAMILY_DATA_CONTRACT_SHA256,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "primary_label_spec_id": PRIMARY_LABEL_SPEC_ID,
        "implementation_id": implementation,
        "research_mode": api.research_mode.value,
        "decision_context_id": api.decision_context_id,
        "as_of": cutoff.isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "decision_session_date": decision_session_date,
        "risk_set_id": risk_set_id,
        "risk_set_manifest_sha256": risk_set.manifest_sha256,
        "market_history_manifest_sha256": market_history.manifest_sha256,
        "market_history_payload_sha256": market_history.payload_sha256,
        "source_receipt_sha256s": sorted(_source_receipt_hashes((risk_set, market_history))),
        "risk_set_security_ids": list(risk_ids),
        "history_session_counts": history_counts,
        "market_rows": canonical_rows,
        "authority_class": next(iter(authority_classes)),
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    packet_sha256 = domain_hash(
        "VOL_SQUEEZE_BREAKOUT_V1:INPUT_PACKET",
        canonical_value(body),
    )
    return {**body, "input_packet_sha256": packet_sha256}


def verify_vsb_input_packet(packet: Mapping[str, Any]) -> None:
    if not isinstance(packet, Mapping):
        raise ValueError("vsb_input_packet_mapping_required")
    if packet.get("schema_version") != INPUT_PACKET_SCHEMA:
        raise ValueError("vsb_input_packet_schema_invalid")
    if packet.get("family_id") != FAMILY_ID:
        raise ValueError("vsb_input_packet_family_invalid")
    if packet.get("family_data_contract_sha256") != FAMILY_DATA_CONTRACT_SHA256:
        raise ValueError("vsb_input_packet_family_contract_hash_invalid")
    if packet.get("risk_set_spec_id") != RISK_SET_SPEC_ID:
        raise ValueError("vsb_input_packet_risk_set_invalid")
    if packet.get("primary_label_spec_id") != PRIMARY_LABEL_SPEC_ID:
        raise ValueError("vsb_input_packet_primary_label_invalid")
    if packet.get("financial_alpha_evidence") != 0 or packet.get("capital_authority") != "NONE":
        raise ValueError("vsb_input_packet_authority_invalid")
    sealed_hash = str(packet.get("input_packet_sha256") or "")
    body = {key: value for key, value in packet.items() if key != "input_packet_sha256"}
    expected = domain_hash(
        "VOL_SQUEEZE_BREAKOUT_V1:INPUT_PACKET",
        canonical_value(body),
    )
    if sealed_hash != expected:
        raise ValueError("vsb_input_packet_hash_mismatch")


def _validate_market_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    risk_ids: Sequence[str],
    decision_session_date: str,
    as_of: datetime,
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    expected_ids = set(risk_ids)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    canonical_rows: list[dict[str, Any]] = []

    for raw in rows:
        if set(raw) != _MARKET_ROW_FIELDS:
            raise ValueError("vsb_market_history_row_fields_invalid")
        security_id = validate_security_ids([str(raw.get("security_id") or "")])[0]
        if security_id not in expected_ids:
            raise ValueError("vsb_market_history_unrequested_security")
        session_date = _date_text(raw.get("session_date"), "session_date")
        key = (security_id, session_date)
        if key in seen:
            raise ValueError("vsb_market_history_duplicate_security_session")
        seen.add(key)
        if session_date > decision_session_date:
            raise ValueError("vsb_market_history_after_decision_session")
        available_at = _timestamp(raw.get("available_at"), "available_at")
        observed_at = _timestamp(raw.get("observed_at"), "observed_at")
        if available_at > as_of:
            raise ValueError("vsb_market_history_available_after_as_of")
        if observed_at > available_at:
            raise ValueError("vsb_market_history_observed_after_available")
        if str(raw.get("coverage_status") or "") != "PRESENT":
            raise ValueError("vsb_market_history_nonpresent_row_forbidden")
        close = _finite(raw.get("close"), "close")
        total_return = _finite(raw.get("total_return_1d"), "total_return_1d")
        volume = _finite(raw.get("volume"), "volume")
        if close <= 0:
            raise ValueError("vsb_market_history_close_must_be_positive")
        if volume < 0:
            raise ValueError("vsb_market_history_volume_must_be_nonnegative")
        row = {
            "security_id": security_id,
            "session_date": session_date,
            "close": format(close, ".17g"),
            "total_return_1d": format(total_return, ".17g"),
            "volume": format(volume, ".17g"),
            "observed_at": observed_at.astimezone(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z"),
            "available_at": available_at.astimezone(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z"),
            "coverage_status": "PRESENT",
        }
        grouped[security_id].append(row)
        canonical_rows.append(row)

    if set(grouped) != expected_ids:
        raise ValueError("vsb_market_history_security_set_not_exact")
    counts: dict[str, int] = {}
    for security_id in sorted(grouped):
        security_rows = sorted(grouped[security_id], key=lambda row: row["session_date"])
        if len(security_rows) < MIN_HISTORY_SESSIONS:
            raise ValueError("vsb_market_history_insufficient_60_session_history")
        if security_rows[-1]["session_date"] != decision_session_date:
            raise ValueError("vsb_market_history_decision_session_missing")
        counts[security_id] = len(security_rows)

    canonical_rows.sort(key=lambda row: (row["security_id"], row["session_date"]))
    return counts, canonical_rows


def _source_receipt_hashes(refs: Sequence[ArtifactRef]) -> set[str]:
    hashes: set[str] = set()
    for ref in refs:
        receipts = ref.manifest.get("source_receipts")
        if not isinstance(receipts, list) or not receipts:
            raise ValueError("vsb_source_receipts_required")
        for receipt in receipts:
            if not isinstance(receipt, Mapping):
                raise ValueError("vsb_source_receipt_mapping_required")
            digest = str(receipt.get("raw_receipt_sha256") or "")
            if len(digest) != 64:
                raise ValueError("vsb_source_receipt_hash_invalid")
            hashes.add(digest)
    return hashes


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"vsb_{field}_mapping_required")
    return value


def _rows(payload: Mapping[str, Any], field: str) -> list[Mapping[str, Any]]:
    rows = payload.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError(f"vsb_{field}_rows_required")
    return rows


def _date_text(value: Any, field: str) -> str:
    text = str(value or "")
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ValueError(f"vsb_{field}_invalid") from exc


def _timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"vsb_market_history_{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"vsb_market_history_{field}_timezone_required")
    return parsed.astimezone(timezone.utc)


def _finite(value: Any, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"vsb_market_history_{field}_finite_required") from exc
    if not isfinite(parsed):
        raise ValueError(f"vsb_market_history_{field}_finite_required")
    return parsed
