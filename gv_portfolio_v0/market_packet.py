"""Immutable bitemporal market packets for operated paper authority.

Replaces free-text operator:// market authority with a fail-closed packet that
carries source/permission identity, raw bytes or receipt, valid/effective time,
retrieval/knowledge time, permanent instrument identity, value/unit/currency,
schema version, and SHA-256 content identity.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from core.gv_fs0_canonical import (
    CanonicalizationError,
    assert_sha256,
    canonical_document_bytes,
    domain_hash,
)

MARKET_PACKET_SCHEMA_VERSION = "gv_immutable_market_packet_v1"
MARKET_PACKET_DOMAIN = "GV-IMMUTABLE-MARKET-PACKET:V1"
MAX_MARKET_PACKET_TEXT = 4096
ALLOWED_UNITS = frozenset({"price"})
ALLOWED_CURRENCIES = frozenset({"USD"})


class MarketPacketError(ValueError):
    """Fail-closed market packet construction or verification error."""


def _required_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MarketPacketError(f"MARKET_PACKET_{field.upper()}_REQUIRED")
    text = value.strip()
    if len(text) > MAX_MARKET_PACKET_TEXT:
        raise MarketPacketError(f"MARKET_PACKET_{field.upper()}_TOO_LONG")
    return text


def _positive_decimal_text(value: Any, *, field: str) -> str:
    if isinstance(value, bool) or isinstance(value, float):
        raise MarketPacketError(f"MARKET_PACKET_{field.upper()}_TYPE_INVALID")
    text = _required_text(str(value) if isinstance(value, (int, Decimal)) else value, field=field)
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
        raise MarketPacketError("MARKET_PRICE_OUT_OF_BOUNDS")
    # Canonical decimal text without scientific notation.
    normalized = format(amount, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    if len(normalized) > MAX_MARKET_PACKET_TEXT:
        raise MarketPacketError("MARKET_PRICE_OUT_OF_BOUNDS")
    return normalized


def _utc_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _packet_body_without_hash(fields: Mapping[str, str]) -> dict[str, str]:
    return {
        "schema_version": fields["schema_version"],
        "source_permission_identity": fields["source_permission_identity"],
        "raw_bytes_or_receipt": fields["raw_bytes_or_receipt"],
        "valid_effective_at": fields["valid_effective_at"],
        "retrieval_knowledge_at": fields["retrieval_knowledge_at"],
        "permanent_instrument_identity": fields["permanent_instrument_identity"],
        "instrument_id": fields["instrument_id"],
        "value": fields["value"],
        "unit": fields["unit"],
        "currency": fields["currency"],
    }


def content_sha256_for_market_packet(fields: Mapping[str, str]) -> str:
    """SHA-256 of the canonical packet body excluding content_sha256."""

    body = _packet_body_without_hash(fields)
    try:
        return domain_hash(MARKET_PACKET_DOMAIN, body)
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise MarketPacketError("MARKET_PACKET_HASH_CANONICALIZATION_FAILED") from exc


def build_immutable_market_packet(
    *,
    source_permission_identity: str,
    raw_bytes_or_receipt: str,
    valid_effective_at: str,
    retrieval_knowledge_at: str,
    permanent_instrument_identity: str,
    instrument_id: str,
    value: str,
    unit: str = "price",
    currency: str = "USD",
    schema_version: str = MARKET_PACKET_SCHEMA_VERSION,
) -> dict[str, str]:
    """Build one immutable market packet with recomputed SHA-256 identity."""

    fields = {
        "schema_version": _required_text(schema_version, field="schema_version"),
        "source_permission_identity": _required_text(
            source_permission_identity, field="source_permission_identity"
        ),
        "raw_bytes_or_receipt": _required_text(
            raw_bytes_or_receipt, field="raw_bytes_or_receipt"
        ),
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
    """Validate and re-canonicalize one market packet; reject operator:// market authority."""

    if not isinstance(raw, Mapping):
        raise MarketPacketError("MARKET_PACKET_MAPPING_REQUIRED")
    if any(
        key in raw
        for key in ("market_source_identity", "market_price", "market_observed_at")
    ) and "content_sha256" not in raw:
        raise MarketPacketError("MARKET_PACKET_OPERATOR_AUTHORITY_PROHIBITED")

    packet = build_immutable_market_packet(
        source_permission_identity=str(raw.get("source_permission_identity", "")),
        raw_bytes_or_receipt=str(raw.get("raw_bytes_or_receipt", "")),
        valid_effective_at=str(raw.get("valid_effective_at", "")),
        retrieval_knowledge_at=str(raw.get("retrieval_knowledge_at", "")),
        permanent_instrument_identity=str(
            raw.get("permanent_instrument_identity", "")
        ),
        instrument_id=str(raw.get("instrument_id", "")),
        value=str(raw.get("value", raw.get("market_price", ""))),
        unit=str(raw.get("unit", "price")),
        currency=str(raw.get("currency", "USD")),
        schema_version=str(
            raw.get("schema_version", MARKET_PACKET_SCHEMA_VERSION)
        ),
    )

    if packet["instrument_id"] != expected_instrument_id:
        raise MarketPacketError("MARKET_PACKET_INSTRUMENT_MISMATCH")
    if packet["permanent_instrument_identity"] != expected_permanent_key:
        raise MarketPacketError("MARKET_PACKET_PERMANENT_IDENTITY_MISMATCH")
    if packet["source_permission_identity"].startswith("operator://"):
        raise MarketPacketError("MARKET_PACKET_OPERATOR_URI_PROHIBITED")

    valid_time = utc_datetime(packet["valid_effective_at"], field="valid_effective_at")
    knowledge_time = utc_datetime(
        packet["retrieval_knowledge_at"], field="retrieval_knowledge_at"
    )
    if valid_time <= latest_time:
        raise MarketPacketError("MARKET_PACKET_VALID_NOT_AFTER_AUTHORITY")
    if knowledge_time < valid_time:
        raise MarketPacketError("MARKET_PACKET_KNOWLEDGE_BEFORE_VALID")
    if knowledge_time > observed_time:
        raise MarketPacketError("MARKET_PACKET_KNOWLEDGE_AFTER_EVIDENCE")
    if valid_time > observed_time:
        raise MarketPacketError("MARKET_PACKET_VALID_AFTER_EVIDENCE")

    # Re-stamp canonical UTC forms after datetime validation.
    packet["valid_effective_at"] = _utc_timestamp(valid_time)
    packet["retrieval_knowledge_at"] = _utc_timestamp(knowledge_time)
    packet["content_sha256"] = content_sha256_for_market_packet(packet)

    declared = raw.get("content_sha256")
    if declared is not None:
        declared_text = _required_text(str(declared), field="content_sha256")
        try:
            assert_sha256(declared_text)
        except (CanonicalizationError, ValueError) as exc:
            raise MarketPacketError("MARKET_PACKET_SHA256_INVALID") from exc
        if declared_text != packet["content_sha256"]:
            # Allow hash computed on pre-normalized timestamps if body otherwise matches
            # by requiring exact equality to the recomputed canonical identity only.
            raise MarketPacketError("MARKET_PACKET_SHA256_MISMATCH")

    # Final integrity: hash must verify against canonical body.
    recomputed = content_sha256_for_market_packet(packet)
    if recomputed != packet["content_sha256"]:
        raise MarketPacketError("MARKET_PACKET_SHA256_INVARIANT_BROKEN")
    return packet


def market_packet_price(packet: Mapping[str, str]) -> str:
    return str(packet["value"])
