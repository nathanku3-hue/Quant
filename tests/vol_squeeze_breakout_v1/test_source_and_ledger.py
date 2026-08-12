from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import json
from pathlib import Path

import pandas as pd
import pytest

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import ResearchMode
from research.vol_squeeze_breakout_v1.ledger import (
    append_prediction_batch,
    load_prediction_tape,
)
from research.vol_squeeze_breakout_v1.runner import seal_m0_predictions
from research.vol_squeeze_breakout_v1.source import (
    MARKET_SOURCE_ROW_SCHEMA,
    PROSPECTIVE_CAPTURE_MODE,
    RISK_SET_SOURCE_AUTHORITY_SCHEMA,
    RISK_SET_SOURCE_ROW_SCHEMA,
    build_vsb_source_production,
)


def _receipt(*, source_id: str, kind: str, day: str, retrieved_at: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "provider": "S&P Capital IQ Pro",
        "retrieved_at": retrieved_at,
        "observed_range_start": day if kind == "risk" else "2026-05-01",
        "observed_range_end": day,
        "raw_receipt_path": f"fixture://vsb/{kind}/{day}",
        "raw_receipt_sha256": domain_hash("VSB:SOURCE:RECEIPT", {"kind": kind, "day": day}),
        "parser_id": f"vsb_{kind}_source_parser_v1",
        "parser_sha256": domain_hash("VSB:SOURCE:PARSER", {"kind": kind, "version": 1}),
        "license_scope": "TEST_SOURCE_BOUND",
        "retention_class": "TEST_FIXTURE",
    }


def _source_inputs(day: str = "2026-08-10") -> dict[str, object]:
    risk_receipt = _receipt(
        source_id="SPCIQPRO:VSB:RISK_SET",
        kind="risk",
        day=day,
        retrieved_at=f"{day}T20:15:00.000000Z",
    )
    market_receipt = _receipt(
        source_id="SPCIQPRO:VSB:MARKET",
        kind="market",
        day=day,
        retrieved_at=f"{day}T20:30:00.000000Z",
    )
    risk_rows = []
    for security_id, company_id, trading_item_id in (
        ("CIQSEC:IQ101", "COMPANY:101", "SPT101"),
        ("CIQSEC:IQ202", "COMPANY:202", "SPT202"),
    ):
        risk_rows.append(
            {
                "schema_version": RISK_SET_SOURCE_ROW_SCHEMA,
                "security_id": security_id,
                "company_id": company_id,
                "trading_item_id": trading_item_id,
                "primary_listing_id": "PRIMARY:" + security_id,
                "listing_country": "US",
                "security_class": "COMMON_EQUITY",
                "primary_listing": True,
                "active_tradable": True,
                "unique_security_mapping": True,
                "membership_effective_at": f"{day}T20:00:00.000000Z",
                "observed_at": f"{day}T20:00:00.000000Z",
                "available_at": f"{day}T20:10:00.000000Z",
                "source_id": risk_receipt["source_id"],
                "source_receipt_sha256": risk_receipt["raw_receipt_sha256"],
                "identity_receipt_sha256": risk_receipt["raw_receipt_sha256"],
            }
        )
    authority = {
        "schema_version": RISK_SET_SOURCE_AUTHORITY_SCHEMA,
        "family_id": "VOL_SQUEEZE_BREAKOUT_v1",
        "risk_set_spec_id": "VSB_US_PRIMARY_COMMON_DAILY_V1",
        "capture_mode": PROSPECTIVE_CAPTURE_MODE,
        "decision_date": day,
        "growth_filter_applied": False,
        "rule100_filter_applied": False,
        "current_survivor_back_projection_used": False,
        "alternate_listing_backfill_used": False,
        "legacy_identity_fallback_used": False,
        "liquidity_threshold_applied": False,
        "source_receipt_sha256s": [risk_receipt["raw_receipt_sha256"]],
    }

    dates = pd.bdate_range(end=day, periods=60)
    returns = [0.02 if index % 2 == 0 else -0.02 for index in range(40)] + [
        0.005 if index % 2 == 0 else -0.005 for index in range(20)
    ]
    market_rows = []
    for security_id, trading_item_id, base, breakout in (
        ("CIQSEC:IQ101", "SPT101", 100.0, True),
        ("CIQSEC:IQ202", "SPT202", 80.0, False),
    ):
        closes = [base + index * 0.1 for index in range(59)]
        prior_high = max(closes[-20:])
        closes.append(prior_high * (1.05 if breakout else 0.99))
        volumes = [100_000.0] * 59 + [200_000.0]
        for index, stamp in enumerate(dates):
            session = stamp.date().isoformat()
            market_rows.append(
                {
                    "schema_version": MARKET_SOURCE_ROW_SCHEMA,
                    "security_id": security_id,
                    "trading_item_id": trading_item_id,
                    "session_date": session,
                    "close": closes[index],
                    "total_return_1d": returns[index],
                    "volume": volumes[index],
                    "observed_at": f"{session}T20:00:00.000000Z",
                    "available_at": f"{session}T20:05:00.000000Z",
                    "source_id": market_receipt["source_id"],
                    "source_receipt_sha256": market_receipt["raw_receipt_sha256"],
                }
            )
    return {
        "risk_receipt": risk_receipt,
        "market_receipt": market_receipt,
        "risk_rows": risk_rows,
        "authority": authority,
        "market_rows": market_rows,
    }


def _production(day: str = "2026-08-10"):
    source = _source_inputs(day)
    as_of = datetime.fromisoformat(day + "T21:00:00+00:00")
    return build_vsb_source_production(
        as_of=as_of,
        decision_date=day,
        decision_context_id="VSB_PROSPECTIVE_" + day,
        research_mode=ResearchMode.PROSPECTIVE,
        risk_set_source_authority=source["authority"],
        risk_set_source_rows=source["risk_rows"],
        risk_set_source_receipts=[source["risk_receipt"]],
        market_source_rows=source["market_rows"],
        market_source_receipts=[source["market_receipt"]],
    )


def _prediction_batch(day: str = "2026-08-10") -> dict[str, object]:
    production = _production(day)
    return seal_m0_predictions(
        input_packet=production.input_packet,
        prediction_made_at=datetime.fromisoformat(day + "T21:00:01+00:00"),
    )


def test_source_producer_closes_broad_prospective_risk_set_and_market_packet() -> None:
    production = _production()
    payload = production.risk_set.payload
    assert payload["family_id"] == "VOL_SQUEEZE_BREAKOUT_v1"
    assert payload["risk_set_spec_id"] == "VSB_US_PRIMARY_COMMON_DAILY_V1"
    assert payload["source_authority"]["capture_mode"] == PROSPECTIVE_CAPTURE_MODE
    assert payload["source_authority"]["growth_filter_applied"] is False
    assert payload["source_authority"]["rule100_filter_applied"] is False
    assert payload["source_authority"]["liquidity_threshold_applied"] is False
    assert production.input_packet["authority_class"] == "PIT_ARTIFACT"
    assert production.input_packet["financial_alpha_evidence"] == 0
    assert production.source_production_sha256


def test_source_producer_requires_completed_nyse_close_and_uses_nyse_local_date() -> None:
    source = _source_inputs()
    with pytest.raises(ValueError, match="primary_close_not_completed"):
        build_vsb_source_production(
            as_of=datetime(2026, 8, 10, 11, 30, tzinfo=UTC),
            decision_date="2026-08-10",
            decision_context_id="pre-close",
            research_mode=ResearchMode.PROSPECTIVE,
            risk_set_source_authority=source["authority"],
            risk_set_source_rows=source["risk_rows"],
            risk_set_source_receipts=[source["risk_receipt"]],
            market_source_rows=source["market_rows"],
            market_source_receipts=[source["market_receipt"]],
        )

    production = build_vsb_source_production(
        as_of=datetime(2026, 8, 11, 0, 30, tzinfo=UTC),
        decision_date="2026-08-10",
        decision_context_id="after-utc-midnight-still-nyse-date",
        research_mode=ResearchMode.PROSPECTIVE,
        risk_set_source_authority=source["authority"],
        risk_set_source_rows=source["risk_rows"],
        risk_set_source_receipts=[source["risk_receipt"]],
        market_source_rows=source["market_rows"],
        market_source_receipts=[source["market_receipt"]],
    )
    assert production.input_packet["decision_session_date"] == "2026-08-10"


def test_source_producer_requires_receipts_retrieved_after_completed_close() -> None:
    source = _source_inputs()
    source["risk_receipt"]["retrieved_at"] = "2026-08-10T19:59:59.000000Z"
    with pytest.raises(ValueError, match="risk_set_source_retrieved_before_completed_close"):
        build_vsb_source_production(
            as_of=datetime(2026, 8, 10, 21, 0, tzinfo=UTC),
            decision_date="2026-08-10",
            decision_context_id="pre-close-receipt",
            research_mode=ResearchMode.PROSPECTIVE,
            risk_set_source_authority=source["authority"],
            risk_set_source_rows=source["risk_rows"],
            risk_set_source_receipts=[source["risk_receipt"]],
            market_source_rows=source["market_rows"],
            market_source_receipts=[source["market_receipt"]],
        )


def test_source_producer_rejects_historical_discovery_and_forbidden_universe_shortcuts() -> None:
    source = _source_inputs()
    as_of = datetime(2026, 8, 10, 21, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="source_discovery_mode_forbidden"):
        build_vsb_source_production(
            as_of=as_of,
            decision_date="2026-08-10",
            decision_context_id="bad-discovery",
            research_mode=ResearchMode.DISCOVERY,
            risk_set_source_authority=source["authority"],
            risk_set_source_rows=source["risk_rows"],
            risk_set_source_receipts=[source["risk_receipt"]],
            market_source_rows=source["market_rows"],
            market_source_receipts=[source["market_receipt"]],
        )

    for flag in (
        "growth_filter_applied",
        "rule100_filter_applied",
        "current_survivor_back_projection_used",
        "alternate_listing_backfill_used",
        "legacy_identity_fallback_used",
        "liquidity_threshold_applied",
    ):
        mutated = deepcopy(source)
        mutated["authority"][flag] = True
        with pytest.raises(ValueError, match="risk_set_source_forbidden_flag"):
            build_vsb_source_production(
                as_of=as_of,
                decision_date="2026-08-10",
                decision_context_id="bad-" + flag,
                research_mode=ResearchMode.PROSPECTIVE,
                risk_set_source_authority=mutated["authority"],
                risk_set_source_rows=mutated["risk_rows"],
                risk_set_source_receipts=[mutated["risk_receipt"]],
                market_source_rows=mutated["market_rows"],
                market_source_receipts=[mutated["market_receipt"]],
            )


def test_source_producer_rejects_non_primary_non_us_or_non_ciq_source() -> None:
    source = _source_inputs()
    as_of = datetime(2026, 8, 10, 21, 0, tzinfo=UTC)
    for field, value, expected in (
        ("primary_listing", False, "required_true:primary_listing"),
        ("listing_country", "CA", "non_us_listing"),
        ("security_class", "ADR", "security_class_invalid"),
    ):
        mutated = deepcopy(source)
        mutated["risk_rows"][0][field] = value
        with pytest.raises(ValueError, match=expected):
            build_vsb_source_production(
                as_of=as_of,
                decision_date="2026-08-10",
                decision_context_id="bad-row",
                research_mode=ResearchMode.PROSPECTIVE,
                risk_set_source_authority=mutated["authority"],
                risk_set_source_rows=mutated["risk_rows"],
                risk_set_source_receipts=[mutated["risk_receipt"]],
                market_source_rows=mutated["market_rows"],
                market_source_receipts=[mutated["market_receipt"]],
            )

    mutated = deepcopy(source)
    mutated["market_receipt"]["provider"] = "OTHER_VENDOR"
    with pytest.raises(ValueError, match="market_provider_not_ciq"):
        build_vsb_source_production(
            as_of=as_of,
            decision_date="2026-08-10",
            decision_context_id="bad-provider",
            research_mode=ResearchMode.PROSPECTIVE,
            risk_set_source_authority=mutated["authority"],
            risk_set_source_rows=mutated["risk_rows"],
            risk_set_source_receipts=[mutated["risk_receipt"]],
            market_source_rows=mutated["market_rows"],
            market_source_receipts=[mutated["market_receipt"]],
        )


def test_prediction_tape_is_append_only_hash_chained_and_one_batch_per_date(tmp_path: Path) -> None:
    ledger = tmp_path / "vsb_predictions.jsonl"
    first = _prediction_batch("2026-08-10")
    second = _prediction_batch("2026-08-11")
    first_entry = append_prediction_batch(
        ledger,
        first,
        recorded_at=datetime(2026, 8, 10, 21, 0, 2, tzinfo=UTC),
    )
    second_entry = append_prediction_batch(
        ledger,
        second,
        recorded_at=datetime(2026, 8, 11, 21, 0, 2, tzinfo=UTC),
    )
    tape = load_prediction_tape(ledger)
    assert tape == [first_entry, second_entry]
    assert first_entry["sequence"] == 0
    assert first_entry["previous_chain_hash"] == "0" * 64
    assert second_entry["sequence"] == 1
    assert second_entry["previous_chain_hash"] == first_entry["chain_hash"]
    assert all(entry["evaluation_status"] == "UNMATURED_NOT_EVALUATED" for entry in tape)
    assert all(entry["batch"]["financial_alpha_evidence"] == 0 for entry in tape)

    with pytest.raises(FileExistsError, match="batch_already_in_ledger"):
        append_prediction_batch(
            ledger,
            first,
            recorded_at=datetime(2026, 8, 11, 21, 0, 3, tzinfo=UTC),
        )
    assert len(load_prediction_tape(ledger)) == 2


def test_prediction_tape_fails_closed_on_tamper_partial_line_and_existing_writer_lock(tmp_path: Path) -> None:
    ledger = tmp_path / "vsb_predictions.jsonl"
    batch = _prediction_batch()
    append_prediction_batch(
        ledger,
        batch,
        recorded_at=datetime(2026, 8, 10, 21, 0, 2, tzinfo=UTC),
    )
    entry = json.loads(ledger.read_text(encoding="utf-8").strip())
    entry["batch"]["rows"][0]["forecast_score"] = "999"
    ledger.write_text(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="chain_hash_mismatch"):
        load_prediction_tape(ledger)

    ledger.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="partial_final_line"):
        load_prediction_tape(ledger)

    ledger.unlink()
    lock = Path(str(ledger) + ".lock")
    lock.write_text("owned-by-other-writer\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="writer_lock_exists"):
        append_prediction_batch(
            ledger,
            batch,
            recorded_at=datetime(2026, 8, 10, 21, 0, 2, tzinfo=UTC),
        )
    assert lock.exists()


def test_landed_vsb_source_and_tape_have_no_historical_or_a2_evaluator_dependency() -> None:
    root = Path("research/vol_squeeze_breakout_v1")
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    forbidden = (
        "aov0_historical_pit_replay",
        "winner_capture",
        "discovery_outcomes",
        "A2_UNTOUCHED_HISTORICAL_PIT",
        "submit_order",
    )
    assert not any(token in text for token in forbidden)
