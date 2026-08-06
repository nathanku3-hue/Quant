"""Immutable bitemporal market packet identity and fail-closed rules."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gv_portfolio_v0.market_packet import (
    MarketPacketError,
    build_immutable_market_packet,
    content_sha256_for_market_packet,
    normalize_immutable_market_packet,
)


def _utc(value: str, field: str = "ts") -> datetime:
    del field
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)


def test_build_and_normalize_round_trip_preserves_sha256() -> None:
    packet = build_immutable_market_packet(
        source_permission_identity="owner-local/permission/manual-v1",
        raw_bytes_or_receipt="RECEIPT value=100",
        valid_effective_at="2026-08-04T12:00:00.000000Z",
        retrieval_knowledge_at="2026-08-04T12:00:30.000000Z",
        permanent_instrument_identity="SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK",
        instrument_id="INS_test",
        value="100.00",
    )
    assert packet["value"] == "100"
    assert packet["schema_version"] == "gv_immutable_market_packet_v1"
    assert packet["content_sha256"] == content_sha256_for_market_packet(packet)

    normalized = normalize_immutable_market_packet(
        packet,
        expected_instrument_id="INS_test",
        expected_permanent_key="SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK",
        latest_time=_utc("2026-08-04T11:00:00.000000Z"),
        observed_time=_utc("2026-08-04T12:01:00.000000Z"),
        utc_datetime=_utc,
    )
    assert normalized["content_sha256"] == packet["content_sha256"]


def test_operator_uri_source_permission_is_rejected() -> None:
    packet = build_immutable_market_packet(
        source_permission_identity="operator://2026-08-04/mu/market",
        raw_bytes_or_receipt="RECEIPT",
        valid_effective_at="2026-08-04T12:00:00.000000Z",
        retrieval_knowledge_at="2026-08-04T12:00:00.000000Z",
        permanent_instrument_identity="SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK",
        instrument_id="INS_test",
        value="100",
    )
    with pytest.raises(MarketPacketError, match="OPERATOR_URI_PROHIBITED"):
        normalize_immutable_market_packet(
            packet,
            expected_instrument_id="INS_test",
            expected_permanent_key="SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK",
            latest_time=_utc("2026-08-04T11:00:00.000000Z"),
            observed_time=_utc("2026-08-04T12:01:00.000000Z"),
            utc_datetime=_utc,
        )


def test_legacy_operator_market_fields_without_packet_are_rejected() -> None:
    with pytest.raises(MarketPacketError, match="OPERATOR_AUTHORITY_PROHIBITED"):
        normalize_immutable_market_packet(
            {
                "market_price": "100",
                "market_observed_at": "2026-08-04T12:00:00.000000Z",
                "market_source_identity": "operator://legacy",
                "instrument_id": "INS_test",
            },
            expected_instrument_id="INS_test",
            expected_permanent_key="SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK",
            latest_time=_utc("2026-08-04T11:00:00.000000Z"),
            observed_time=_utc("2026-08-04T12:01:00.000000Z"),
            utc_datetime=_utc,
        )


def test_tampered_sha256_fails_closed() -> None:
    packet = build_immutable_market_packet(
        source_permission_identity="owner-local/permission/manual-v1",
        raw_bytes_or_receipt="RECEIPT",
        valid_effective_at="2026-08-04T12:00:00.000000Z",
        retrieval_knowledge_at="2026-08-04T12:00:00.000000Z",
        permanent_instrument_identity="SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK",
        instrument_id="INS_test",
        value="100",
    )
    tampered = dict(packet)
    tampered["content_sha256"] = "0" * 64
    with pytest.raises(MarketPacketError, match="SHA256_MISMATCH"):
        normalize_immutable_market_packet(
            tampered,
            expected_instrument_id="INS_test",
            expected_permanent_key="SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK",
            latest_time=_utc("2026-08-04T11:00:00.000000Z"),
            observed_time=_utc("2026-08-04T12:01:00.000000Z"),
            utc_datetime=_utc,
        )
