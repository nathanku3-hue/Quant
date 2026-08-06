"""Source-derived immutable bitemporal market packets.

Packets bind one verified source capture, permission manifest, parser identity,
instrument-bound row, common decision cut, and point-in-time observation. The
operator cannot author price, source, parser, receipt, or timestamp authority.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from core.gv_fs0_canonical import CanonicalizationError, assert_sha256, domain_hash

MARKET_PACKET_SCHEMA_VERSION = "gv_immutable_market_packet_v2"
MARKET_PACKET_DOMAIN = "GV-IMMUTABLE-MARKET-PACKET:V2"
MAX_MARKET_PACKET_TEXT = 4096
ALLOWED_UNITS = frozenset({"price"})
ALLOWED_CURRENCIES = frozenset({"USD"})
LEGACY_AUTHORITY_FIELDS = frozenset(
    {
        "source_permission_identity",
        "raw_bytes_or_receipt",
        "market_source_identity",
        "market_price",
        "market_observed_at",
    }
)
PACKET_BODY_FIELDS = (
    "schema_version",
    "source_contract_version",
    "source_object_identity",
    "source_object_sha256",
    "permission_manifest_identity",
    "permission_manifest_sha256",
    "parser_identity",
    "parser_version",
    "decision_cut_id",
    "row_locator",
    "row_sha256",
    "valid_effective_at",
    "retrieval_knowledge_at",
    "permanent_instrument_identity",
    "instrument_id",
    "value",
    "unit",
    "currency",
)
PACKET_FIELDS = frozenset((*PACKET_BODY_FIELDS, "content_sha256"))


class MarketPacketError(ValueError):
    """Fail-closed source-derived packet error."""


def _required_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MarketPacketError(f"MARKET_PACKET_{field.upper()}_REQUIRED")
    text = value.strip()
    if len(text) > MAX_MARKET_PACKET_TEXT:
        raise MarketPacketError(f"MARKET_PACKET_{field.upper()}_TOO_LONG")
    return text


def _sha256_text(value: Any, *, field: str) -> str:
    text = _required_text(value, field=field)
    try:
        assert_sha256(text)
    except (CanonicalizationError, ValueError) as exc:
        raise MarketPacketError(f"MARKET_PACKET_{field.upper()}_INVALID") from exc
    return text


def _positive_decimal_text(value: Any, *, field: str) -> str:
    if isinstance(value, bool) or isinstance(value, float):
        raise MarketPacketError(f"MARKET_PACKET_{field.upper()}_TYPE_INVALID")
    text = _required_text(
        str(value) if isinstance(value, (int, Decimal)) else value,
        field=field,
    )
    try:
        amount = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise MarketPacketError(f"MARKET_PACKET_{field.upper()}_INVALID") from exc
    if not amount.is_finite() or amount <= 0:
        raise MarketPacketError(f"MARKET_PACKET_{field.upper()}_NOT_POSITIVE")
    sign, digits, exponent = amount.as_tuple()
    del sign
    digit_list = list(digits)
    while len(digit_list) > 1 and digit_list[-1] == 0:
        digit_list.pop()
        exponent += 1
    integer_digits = len(digit_list) + max(exponent, 0)
    fraction_digits = max(-exponent, 0)
    if integer_digits > 18 or fraction_digits > 18:
        raise MarketPacketError("MARKET_PACKET_VALUE_OUT_OF_BOUNDS")
    normalized = format(amount, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    if len(normalized) > MAX_MARKET_PACKET_TEXT:
        raise MarketPacketError("MARKET_PACKET_VALUE_OUT_OF_BOUNDS")
    return normalized


def _utc_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _packet_body_without_hash(fields: Mapping[str, str]) -> dict[str, str]:
    return {field: fields[field] for field in PACKET_BODY_FIELDS}


def content_sha256_for_market_packet(fields: Mapping[str, str]) -> str:
    try:
        return domain_hash(MARKET_PACKET_DOMAIN, _packet_body_without_hash(fields))
    except (CanonicalizationError, KeyError, TypeError, ValueError) as exc:
        raise MarketPacketError("MARKET_PACKET_HASH_CANONICALIZATION_FAILED") from exc


def build_immutable_market_packet(
    *,
    source_contract_version: str,
    source_object_identity: str,
    source_object_sha256: str,
    permission_manifest_identity: str,
    permission_manifest_sha256: str,
    parser_identity: str,
    parser_version: str,
    decision_cut_id: str,
    row_locator: str,
    row_sha256: str,
    valid_effective_at: str,
    retrieval_knowledge_at: str,
    permanent_instrument_identity: str,
    instrument_id: str,
    value: str,
    unit: str = "price",
    currency: str = "USD",
    schema_version: str = MARKET_PACKET_SCHEMA_VERSION,
) -> dict[str, str]:
    fields = {
        "schema_version": _required_text(schema_version, field="schema_version"),
        "source_contract_version": _required_text(
            source_contract_version, field="source_contract_version"
        ),
        "source_object_identity": _required_text(
            source_object_identity, field="source_object_identity"
        ),
        "source_object_sha256": _sha256_text(
            source_object_sha256, field="source_object_sha256"
        ),
        "permission_manifest_identity": _required_text(
            permission_manifest_identity, field="permission_manifest_identity"
        ),
        "permission_manifest_sha256": _sha256_text(
            permission_manifest_sha256, field="permission_manifest_sha256"
        ),
        "parser_identity": _required_text(parser_identity, field="parser_identity"),
        "parser_version": _required_text(parser_version, field="parser_version"),
        "decision_cut_id": _required_text(decision_cut_id, field="decision_cut_id"),
        "row_locator": _required_text(row_locator, field="row_locator"),
        "row_sha256": _sha256_text(row_sha256, field="row_sha256"),
        "valid_effective_at": _required_text(
            valid_effective_at, field="valid_effective_at"
        ),
        "retrieval_knowledge_at": _required_text(
            retrieval_knowledge_at, field="retrieval_knowledge_at"
        ),
        "permanent_instrument_identity": _required_text(
            permanent_instrument_identity, field="permanent_instrument_identity"
        ),
        "instrument_id": _required_text(instrument_id, field="instrument_id"),
        "value": _positive_decimal_text(value, field="value"),
        "unit": _required_text(unit, field="unit"),
        "currency": _required_text(currency, field="currency"),
    }
    if fields["schema_version"] != MARKET_PACKET_SCHEMA_VERSION:
        raise MarketPacketError("MARKET_PACKET_SCHEMA_VERSION_UNSUPPORTED")
    if fields["unit"] not in ALLOWED_UNITS:
        raise MarketPacketError("MARKET_PACKET_UNIT_UNSUPPORTED")
    if fields["currency"] not in ALLOWED_CURRENCIES:
        raise MarketPacketError("MARKET_PACKET_CURRENCY_UNSUPPORTED")
    packet = dict(fields)
    packet["content_sha256"] = content_sha256_for_market_packet(fields)
    return packet


def normalize_immutable_market_packet(
    raw: Any,
    *,
    expected_instrument_id: str,
    expected_permanent_key: str,
    latest_time: datetime,
    observed_time: datetime,
    utc_datetime,
) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        raise MarketPacketError("MARKET_PACKET_MAPPING_REQUIRED")
    if LEGACY_AUTHORITY_FIELDS.intersection(raw):
        raise MarketPacketError("MARKET_PACKET_MANUAL_AUTHORITY_PROHIBITED")
    if set(raw) != PACKET_FIELDS:
        raise MarketPacketError("MARKET_PACKET_FIELD_SET_INVALID")

    packet = build_immutable_market_packet(
        source_contract_version=str(raw.get("source_contract_version", "")),
        source_object_identity=str(raw.get("source_object_identity", "")),
        source_object_sha256=str(raw.get("source_object_sha256", "")),
        permission_manifest_identity=str(
            raw.get("permission_manifest_identity", "")
        ),
        permission_manifest_sha256=str(raw.get("permission_manifest_sha256", "")),
        parser_identity=str(raw.get("parser_identity", "")),
        parser_version=str(raw.get("parser_version", "")),
        decision_cut_id=str(raw.get("decision_cut_id", "")),
        row_locator=str(raw.get("row_locator", "")),
        row_sha256=str(raw.get("row_sha256", "")),
        valid_effective_at=str(raw.get("valid_effective_at", "")),
        retrieval_knowledge_at=str(raw.get("retrieval_knowledge_at", "")),
        permanent_instrument_identity=str(
            raw.get("permanent_instrument_identity", "")
        ),
        instrument_id=str(raw.get("instrument_id", "")),
        value=str(raw.get("value", "")),
        unit=str(raw.get("unit", "")),
        currency=str(raw.get("currency", "")),
        schema_version=str(raw.get("schema_version", "")),
    )
    if packet["instrument_id"] != expected_instrument_id:
        raise MarketPacketError("MARKET_PACKET_INSTRUMENT_MISMATCH")
    if packet["permanent_instrument_identity"] != expected_permanent_key:
        raise MarketPacketError("MARKET_PACKET_PERMANENT_IDENTITY_MISMATCH")

    valid_time = utc_datetime(packet["valid_effective_at"], field="valid_effective_at")
    knowledge_time = utc_datetime(
        packet["retrieval_knowledge_at"], field="retrieval_knowledge_at"
    )
    if valid_time <= latest_time:
        raise MarketPacketError("MARKET_PACKET_VALID_NOT_AFTER_AUTHORITY")
    if knowledge_time < valid_time:
        raise MarketPacketError("MARKET_PACKET_KNOWLEDGE_BEFORE_VALID")
    if knowledge_time > observed_time:
        raise MarketPacketError("MARKET_PACKET_KNOWLEDGE_AFTER_DECISION")
    if valid_time > observed_time:
        raise MarketPacketError("MARKET_PACKET_VALID_AFTER_DECISION")

    packet["valid_effective_at"] = _utc_timestamp(valid_time)
    packet["retrieval_knowledge_at"] = _utc_timestamp(knowledge_time)
    packet["content_sha256"] = content_sha256_for_market_packet(packet)
    declared = _sha256_text(raw.get("content_sha256"), field="content_sha256")
    if declared != packet["content_sha256"]:
        raise MarketPacketError("MARKET_PACKET_SHA256_MISMATCH")
    return packet


def market_packet_price(packet: Mapping[str, str]) -> str:
    return str(packet["value"])
