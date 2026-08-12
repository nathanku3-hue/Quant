from __future__ import annotations

from copy import deepcopy
from datetime import UTC, date, datetime, timedelta
import json
from pathlib import Path

import pytest

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import ResearchMode
from research.sector_rotation_alpha_v1.acquisition import (
    build_frozen_acquisition_request,
    require_capture_reopen,
    verify_frozen_acquisition_request,
)
from research.sector_rotation_alpha_v1.contracts import (
    EXPECTED_SECTOR_KEYS,
    FAMILY_ID,
    IMPLEMENTATION_ID,
    PRIMARY_HORIZON_SESSIONS,
    SECONDARY_HORIZON_SESSIONS,
)
from research.sector_rotation_alpha_v1.features import compute_m0_features
from research.sector_rotation_alpha_v1.ledger import append_prediction_batch, load_prediction_tape
from research.sector_rotation_alpha_v1.model import score_m0_features
from research.sector_rotation_alpha_v1.runner import seal_m0_predictions
from research.sector_rotation_alpha_v1.source import (
    BENCHMARK_FAMILY_ID,
    MARKET_SOURCE_ROW_SCHEMA,
    PROSPECTIVE_CAPTURE_MODE,
    RISK_SET_SOURCE_AUTHORITY_SCHEMA,
    RISK_SET_SOURCE_ROW_SCHEMA,
    build_sector_rotation_source_production,
)
from research.sector_rotation_alpha_v1.trial_ledger import (
    append_trial_receipt,
    build_code_manifest,
    build_trial_receipt,
    load_trial_ledger,
)


def _business_days(end: str, periods: int) -> list[date]:
    current = date.fromisoformat(end)
    output: list[date] = []
    while len(output) < periods:
        if current.weekday() < 5:
            output.append(current)
        current -= timedelta(days=1)
    return list(reversed(output))


def _receipt(*, source_id: str, kind: str, day: str, retrieved_at: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "provider": "DETERMINISTIC_FIXTURE_ONLY",
        "retrieved_at": retrieved_at,
        "observed_range_start": day if kind == "risk" else _business_days(day, 60)[0].isoformat(),
        "observed_range_end": day,
        "raw_receipt_path": f"fixture://sra/{kind}/{day}",
        "raw_receipt_sha256": domain_hash("SRA:SOURCE:RECEIPT", {"kind": kind, "day": day}),
        "parser_id": f"sra_{kind}_source_parser_v1",
        "parser_sha256": domain_hash("SRA:SOURCE:PARSER", {"kind": kind, "version": 1}),
        "license_scope": "TEST_SOURCE_BOUND",
        "retention_class": "TEST_FIXTURE",
    }


def _source_inputs(day: str = "2026-08-10") -> dict[str, object]:
    risk_receipt = _receipt(
        source_id="SPCIQPRO:SRA:RISK_SET",
        kind="risk",
        day=day,
        retrieved_at=f"{day}T20:15:00.000000Z",
    )
    market_receipt = _receipt(
        source_id="SPCIQPRO:SRA:MARKET",
        kind="market",
        day=day,
        retrieved_at=f"{day}T20:30:00.000000Z",
    )
    risk_rows = []
    identity: list[tuple[str, str, str]] = []
    for index, sector_key in enumerate(EXPECTED_SECTOR_KEYS, start=1):
        security_id = f"CIQSEC:IQSRA{index:02d}"
        trading_item_id = f"SPTSRA{index:02d}"
        identity.append((security_id, trading_item_id, sector_key))
        risk_rows.append(
            {
                "schema_version": RISK_SET_SOURCE_ROW_SCHEMA,
                "security_id": security_id,
                "trading_item_id": trading_item_id,
                "primary_listing_id": f"PRIMARY:{security_id}",
                "sector_key": sector_key,
                "benchmark_family_id": BENCHMARK_FAMILY_ID,
                "benchmark_membership_receipt_sha256": risk_receipt["raw_receipt_sha256"],
                "instrument_type": "ETF",
                "listing_country": "US",
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
        "family_id": FAMILY_ID,
        "risk_set_spec_id": "SRA_US_SELECT_SECTOR_ETF_11_V1",
        "capture_mode": PROSPECTIVE_CAPTURE_MODE,
        "decision_date": day,
        "benchmark_family_id": BENCHMARK_FAMILY_ID,
        "expected_sector_keys": list(EXPECTED_SECTOR_KEYS),
        "stock_sector_map_used": False,
        "stock_breadth_used": False,
        "underlying_stock_membership_used": False,
        "current_survivor_back_projection_used": False,
        "alternate_listing_backfill_used": False,
        "legacy_identity_fallback_used": False,
        "etf_flow_vendor_used": False,
        "corporate_action_total_return_authority_bound": True,
        "source_receipt_sha256s": [risk_receipt["raw_receipt_sha256"]],
    }

    dates = _business_days(day, 60)
    market_rows = []
    for sector_index, (security_id, trading_item_id, sector_key) in enumerate(identity):
        trend = (sector_index - 5) * 0.00055
        for session_index, stamp in enumerate(dates):
            session = stamp.isoformat()
            cycle = 0.0007 if session_index % 2 == 0 else -0.0005
            total_return = trend + cycle
            close = 80.0 + sector_index * 4.0 + session_index * (0.03 + max(trend, -0.001) * 8.0)
            base_volume = 500_000.0 + sector_index * 25_000.0
            if session_index >= 55:
                volume = base_volume * (1.55 if sector_index >= 8 else 0.65 if sector_index <= 7 else 1.0)
            else:
                volume = base_volume
            market_rows.append(
                {
                    "schema_version": MARKET_SOURCE_ROW_SCHEMA,
                    "security_id": security_id,
                    "trading_item_id": trading_item_id,
                    "sector_key": sector_key,
                    "session_date": session,
                    "close": close,
                    "total_return_1d": total_return,
                    "volume": volume,
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
    return build_sector_rotation_source_production(
        as_of=datetime.fromisoformat(day + "T21:00:00+00:00"),
        decision_date=day,
        decision_context_id="SRA_PROSPECTIVE_" + day,
        research_mode=ResearchMode.PROSPECTIVE,
        risk_set_source_authority=source["authority"],
        risk_set_source_rows=source["risk_rows"],
        risk_set_source_receipts=[source["risk_receipt"]],
        market_source_rows=source["market_rows"],
        market_source_receipts=[source["market_receipt"]],
        fixture=True,
    )


def _trial() -> dict[str, object]:
    return build_trial_receipt(
        code_manifest=build_code_manifest(Path(".")),
        created_at=datetime(2026, 8, 10, 18, 0, tzinfo=UTC),
    )


def _prediction_batch(day: str = "2026-08-10") -> dict[str, object]:
    production = _production(day)
    return seal_m0_predictions(
        input_packet=production.input_packet,
        trial_receipt=_trial(),
        prediction_made_at=datetime.fromisoformat(day + "T21:00:01+00:00"),
    )


def test_source_is_exact_11_etf_sector_risk_set_without_stock_dependencies() -> None:
    production = _production()
    payload = production.risk_set.payload
    assert payload["family_id"] == FAMILY_ID
    assert payload["risk_set_spec_id"] == "SRA_US_SELECT_SECTOR_ETF_11_V1"
    assert len(payload["rows"]) == 11
    assert {row["sector_key"] for row in payload["rows"]} == set(EXPECTED_SECTOR_KEYS)
    assert all(row["sra_source_proof"]["instrument_type"] == "ETF" for row in payload["rows"])
    assert production.input_packet["stock_sector_map_used"] is False
    assert production.input_packet["stock_breadth_used"] is False
    assert production.input_packet["underlying_stock_membership_used"] is False
    assert production.input_packet["financial_alpha_evidence"] == 0
    assert production.input_packet["capital_authority"] == "NONE"


def test_source_rejects_old_sector_map_breadth_survivor_and_etf_flow_shortcuts() -> None:
    source = _source_inputs()
    for flag in (
        "stock_sector_map_used",
        "stock_breadth_used",
        "underlying_stock_membership_used",
        "current_survivor_back_projection_used",
        "alternate_listing_backfill_used",
        "legacy_identity_fallback_used",
        "etf_flow_vendor_used",
    ):
        mutated = deepcopy(source)
        mutated["authority"][flag] = True
        with pytest.raises(ValueError, match="source_forbidden_flag"):
            build_sector_rotation_source_production(
                as_of=datetime(2026, 8, 10, 21, 0, tzinfo=UTC),
                decision_date="2026-08-10",
                decision_context_id="bad-" + flag,
                research_mode=ResearchMode.PROSPECTIVE,
                risk_set_source_authority=mutated["authority"],
                risk_set_source_rows=mutated["risk_rows"],
                risk_set_source_receipts=[mutated["risk_receipt"]],
                market_source_rows=mutated["market_rows"],
                market_source_receipts=[mutated["market_receipt"]],
                fixture=True,
            )


def test_source_requires_exact_ci_security_trading_item_availability_and_total_return_authority() -> None:
    source = _source_inputs()
    as_of = datetime(2026, 8, 10, 21, 0, tzinfo=UTC)

    mutated = deepcopy(source)
    mutated["risk_rows"][0]["instrument_type"] = "COMMON_EQUITY"
    with pytest.raises(ValueError, match="instrument_type_invalid"):
        build_sector_rotation_source_production(
            as_of=as_of,
            decision_date="2026-08-10",
            decision_context_id="not-etf",
            research_mode=ResearchMode.PROSPECTIVE,
            risk_set_source_authority=mutated["authority"],
            risk_set_source_rows=mutated["risk_rows"],
            risk_set_source_receipts=[mutated["risk_receipt"]],
            market_source_rows=mutated["market_rows"],
            market_source_receipts=[mutated["market_receipt"]],
            fixture=True,
        )

    mutated = deepcopy(source)
    mutated["market_rows"][0]["trading_item_id"] = "WRONG_LISTING"
    with pytest.raises(ValueError, match="trading_item_mismatch"):
        build_sector_rotation_source_production(
            as_of=as_of,
            decision_date="2026-08-10",
            decision_context_id="wrong-listing",
            research_mode=ResearchMode.PROSPECTIVE,
            risk_set_source_authority=mutated["authority"],
            risk_set_source_rows=mutated["risk_rows"],
            risk_set_source_receipts=[mutated["risk_receipt"]],
            market_source_rows=mutated["market_rows"],
            market_source_receipts=[mutated["market_receipt"]],
            fixture=True,
        )

    mutated = deepcopy(source)
    mutated["authority"]["corporate_action_total_return_authority_bound"] = False
    with pytest.raises(ValueError, match="total_return_authority_required"):
        build_sector_rotation_source_production(
            as_of=as_of,
            decision_date="2026-08-10",
            decision_context_id="no-ca-authority",
            research_mode=ResearchMode.PROSPECTIVE,
            risk_set_source_authority=mutated["authority"],
            risk_set_source_rows=mutated["risk_rows"],
            risk_set_source_receipts=[mutated["risk_receipt"]],
            market_source_rows=mutated["market_rows"],
            market_source_receipts=[mutated["market_receipt"]],
            fixture=True,
        )


def test_source_requires_completed_close_and_no_future_availability() -> None:
    source = _source_inputs()
    with pytest.raises(ValueError, match="primary_close_not_completed"):
        build_sector_rotation_source_production(
            as_of=datetime(2026, 8, 10, 19, 59, tzinfo=UTC),
            decision_date="2026-08-10",
            decision_context_id="pre-close",
            research_mode=ResearchMode.PROSPECTIVE,
            risk_set_source_authority=source["authority"],
            risk_set_source_rows=source["risk_rows"],
            risk_set_source_receipts=[source["risk_receipt"]],
            market_source_rows=source["market_rows"],
            market_source_receipts=[source["market_receipt"]],
            fixture=True,
        )

    mutated = deepcopy(source)
    mutated["risk_rows"][0]["available_at"] = "2026-08-10T21:00:01.000000Z"
    with pytest.raises(ValueError, match="time_order_invalid"):
        build_sector_rotation_source_production(
            as_of=datetime(2026, 8, 10, 21, 0, tzinfo=UTC),
            decision_date="2026-08-10",
            decision_context_id="future-availability",
            research_mode=ResearchMode.PROSPECTIVE,
            risk_set_source_authority=mutated["authority"],
            risk_set_source_rows=mutated["risk_rows"],
            risk_set_source_receipts=[mutated["risk_receipt"]],
            market_source_rows=mutated["market_rows"],
            market_source_receipts=[mutated["market_receipt"]],
            fixture=True,
        )


def test_m0_features_and_model_preserve_explicit_i_vs_i_plus_x() -> None:
    production = _production()
    features = compute_m0_features(production.input_packet)
    assert features["row_count"] == 11
    assert all(row["feature_status"] == "READY" for row in features["rows"])
    assert all(row["relative_strength_20"] is not None for row in features["rows"])
    assert all(row["relative_strength_60"] is not None for row in features["rows"])

    model = score_m0_features(features)
    assert model["risk_set_count"] == 11
    assert 0 < model["support_count"] < model["incumbent_support_count"] < 11
    assert model["overlay_definition"].startswith("I_PLUS_X")
    assert model["incumbent_definition"].startswith("I_EQUALS")
    assert all("incumbent_score" in row and "forecast_score" in row for row in model["rows"])
    assert model["stock_sector_map_used"] is False
    assert model["stock_breadth_used"] is False


def test_trial_search_budget_is_one_and_second_material_trial_fails_closed(tmp_path: Path) -> None:
    ledger = tmp_path / "sra_trials.jsonl"
    receipt = _trial()
    appended = append_trial_receipt(ledger, receipt)
    assert load_trial_ledger(ledger) == [appended]
    assert appended["trial_budget_max"] == 1
    assert appended["outcome_accessed"] is False
    assert appended["financial_alpha_evidence"] == 0

    with pytest.raises(RuntimeError, match="material_trial_budget_exhausted"):
        append_trial_receipt(ledger, receipt)
    assert len(load_trial_ledger(ledger)) == 1


def test_prediction_seal_binds_trial_horizons_incumbent_and_zero_authority() -> None:
    production = _production()
    with pytest.raises(ValueError, match="must_be_after_knowledge_cutoff"):
        seal_m0_predictions(
            input_packet=production.input_packet,
            trial_receipt=_trial(),
            prediction_made_at=datetime(2026, 8, 10, 21, 0, tzinfo=UTC),
        )

    batch = _prediction_batch()
    assert batch["primary_horizon_sessions"] == PRIMARY_HORIZON_SESSIONS == 20
    assert batch["secondary_horizon_sessions"] == SECONDARY_HORIZON_SESSIONS == 40
    assert batch["outcome_status"] == "UNMATURED_NOT_EVALUATED"
    assert batch["financial_alpha_evidence"] == 0
    assert batch["capital_authority"] == "NONE"
    assert batch["broker_orders"] == "FORBIDDEN"
    assert batch["parent_child_mutation"] == "FORBIDDEN"
    assert all("incumbent_support" in row and "incumbent_score" in row for row in batch["rows"])


def test_prediction_tape_is_append_only_hash_chained_and_one_batch_per_date(tmp_path: Path) -> None:
    ledger = tmp_path / "sra_predictions.jsonl"
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

    with pytest.raises(FileExistsError, match="batch_already_in_ledger"):
        append_prediction_batch(
            ledger,
            first,
            recorded_at=datetime(2026, 8, 11, 21, 0, 3, tzinfo=UTC),
        )
    assert len(load_prediction_tape(ledger)) == 2


def test_prediction_tape_fails_closed_on_tamper_partial_line_and_existing_writer_lock(tmp_path: Path) -> None:
    ledger = tmp_path / "sra_predictions.jsonl"
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


def test_frozen_acquisition_request_is_exact_11_etf_no_capture_and_source_bound() -> None:
    request = build_frozen_acquisition_request()
    verify_frozen_acquisition_request(request)
    assert request["request_sha256"] == "7d4a46c0fa2e0292ab42d0f88f90dc800bb25c5edebcd00bdd1a209a73915c0c"
    assert request["capture_state"] == "PARKED_CAPTURE_HOLD"
    assert request["provider_acquisition_allowed"] is False
    assert request["sector_count"] == 11
    assert [row["sector_key"] for row in request["sector_requests"]] == list(EXPECTED_SECTOR_KEYS)
    assert all(row["identity_provider_fields"] == ["SP_CIQ_ID", "SP_TRADING_ITEM_ID"] for row in request["sector_requests"])
    assert all(row["benchmark_membership_receipt_required"] is True for row in request["sector_requests"])
    assert all(row["unresolved_identity_action"] == "BLOCK" for row in request["sector_requests"])
    market = request["market_history_request"]
    assert market["provider_fields"] == ["SP_TOTAL_RETURN", "SP_PRICE_CLOSE", "SP_VOLUME"]
    assert market["minimum_observed_sessions_per_security"] == 60
    assert market["total_return_is_corporate_action_authority"] is True
    assert request["frozen_model_summary"] == {
        "relative_strength_windows": [20, 60],
        "dollar_volume_participation_windows": [5, 20],
        "material_trials": 1,
        "comparator": "I_RELATIVE_STRENGTH_ONLY_VS_I_PLUS_X_DVP_PRE_LABEL",
        "retune_allowed": False,
    }
    assert all(value is False for value in request["forbidden_inputs_or_methods"].values())

    frozen_path = Path("docs/context/e2e_evidence/sector_rotation_alpha_v1_acquisition_request_20260810.json")
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    assert frozen == request

    with pytest.raises(RuntimeError, match="independent_provider_capacity_required"):
        require_capture_reopen(independent_provider_capacity_available=False)
    with pytest.raises(RuntimeError, match="capture_hold_active"):
        require_capture_reopen(independent_provider_capacity_available=True)


def test_sector_rotation_package_has_no_legacy_rotation_vsb_or_broker_dependency() -> None:
    root = Path("research/sector_rotation_alpha_v1")
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    forbidden = (
        "scripts.osiris_rotation_backtest",
        "research.vol_squeeze_breakout_v1",
        "winner_capture",
        "submit_order",
        "A2_UNTOUCHED_HISTORICAL_PIT",
    )
    assert not any(token in text for token in forbidden)
    for ticker_literal in ("XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"):
        assert ticker_literal not in text
