from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

import pytest

from research.prebreakout_pit_v1.authority import (
    ACTION_CLEAR,
    ACTION_EFFECTIVE_TERMINAL,
    ACTION_UNRESOLVED,
    AMBIGUOUS_DATE_LOCAL,
    B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE,
    CANDIDATE_ROW_SCHEMA,
    CORPORATE_ACTION_ROW_SCHEMA,
    EXCLUSION_AMBIGUOUS_PRIMARY,
    EXCLUSION_CA_EFFECTIVE,
    EXCLUSION_NOT_IN_SOURCE,
    FAMILY_ID,
    HISTORICAL_CAPTURE_MODE,
    PRIMARY_DATE_LOCAL,
    PRIMARY_PROOF_AMBIGUOUS,
    PRIMARY_PROOF_UNIQUE,
    PROSPECTIVE_CAPTURE_MODE,
    RISK_SET_SPEC_ID,
    SOURCE_AUTHORITY_SCHEMA,
    W2_CONTRACT_SHA256,
    PrebreakoutPITAuthorityError,
    build_b_minus_one_eligibility_proof,
    build_prebreakout_pit_authority,
    verify_prebreakout_pit_authority,
)


AS_OF = datetime(2025, 8, 15, 20, 0, tzinfo=UTC)
DECISION_DAY = "2025-08-15"
BREAKOUT_DAY = "2025-08-18"
BREAKOUT_HASH = W2_CONTRACT_SHA256
RISK_RECEIPT_HASH = "a" * 64
IDENTITY_RECEIPT_HASH = "c" * 64
ACTION_RECEIPT_HASH = "d" * 64


def _receipt(digest: str, *, role: str) -> dict[str, object]:
    return {
        "source_id": f"FIXTURE:{role}",
        "provider": "DETERMINISTIC_FIXTURE_ONLY",
        "retrieved_at": "2026-08-10T12:00:00Z",
        "observed_range_start": DECISION_DAY,
        "observed_range_end": DECISION_DAY,
        "raw_receipt_path": f"fixture://{role}/{digest}",
        "raw_receipt_sha256": digest,
        "parser_id": f"fixture-{role}-parser-v1",
        "parser_sha256": "e" * 64,
        "license_scope": "FIXTURE_ONLY",
        "retention_class": "TEST_FIXTURE",
    }


def _receipts() -> list[dict[str, object]]:
    return [
        _receipt(RISK_RECEIPT_HASH, role="risk"),
        _receipt(IDENTITY_RECEIPT_HASH, role="identity"),
        _receipt(ACTION_RECEIPT_HASH, role="corp-action"),
    ]


def _source_authority() -> dict[str, object]:
    return {
        "schema_version": SOURCE_AUTHORITY_SCHEMA,
        "family_id": FAMILY_ID,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "capture_mode": HISTORICAL_CAPTURE_MODE,
        "decision_session_date": DECISION_DAY,
        "provider": "DETERMINISTIC_FIXTURE_ONLY",
        "date_local_membership_query": True,
        "source_population_complete": True,
        "historical_as_of_mechanically_bound": True,
        "corporate_action_coverage_complete": True,
        "current_survivor_back_projection_used": False,
        "current_primary_back_projection_used": False,
        "alternate_listing_backfill_used": False,
        "ticker_fallback_used": False,
        "company_entity_fallback_used": False,
        "permno_fallback_used": False,
        "primary_listing_resolution": "DATE_LOCAL_PROVIDER_OR_UNIQUE_QUALIFYING_LISTING",
        "ambiguous_listing_policy": "DETERMINISTIC_EXCLUDE_NO_FALLBACK",
        "source_receipt_sha256s": sorted(
            [RISK_RECEIPT_HASH, IDENTITY_RECEIPT_HASH, ACTION_RECEIPT_HASH]
        ),
    }


def _candidate(
    *,
    security_id: str,
    company_id: str,
    trading_item_id: str,
    primary_listing_state: str = PRIMARY_DATE_LOCAL,
    primary_listing_proof_kind: str = PRIMARY_PROOF_UNIQUE,
    active_tradable: bool = True,
    listing_country: str = "US",
    security_class: str = "COMMON_EQUITY",
) -> dict[str, object]:
    return {
        "schema_version": CANDIDATE_ROW_SCHEMA,
        "security_id": security_id,
        "company_id": company_id,
        "trading_item_id": trading_item_id,
        "spt_instrument_item_id": f"SPT{trading_item_id}",
        "membership_as_of_date": DECISION_DAY,
        "listing_country": listing_country,
        "security_class": security_class,
        "primary_listing_state": primary_listing_state,
        "primary_listing_proof_kind": primary_listing_proof_kind,
        "active_tradable": active_tradable,
        "observed_at": "2025-08-15T19:58:00Z",
        "available_at": "2025-08-15T19:59:00Z",
        "source_id": "FIXTURE:RISK",
        "source_receipt_sha256": RISK_RECEIPT_HASH,
        "identity_receipt_sha256": IDENTITY_RECEIPT_HASH,
    }


def _action(
    *,
    security_id: str,
    trading_item_id: str,
    action_state: str = ACTION_CLEAR,
    effective_session_date: str | None = None,
    event_type: str = "NONE",
) -> dict[str, object]:
    return {
        "schema_version": CORPORATE_ACTION_ROW_SCHEMA,
        "security_id": security_id,
        "trading_item_id": trading_item_id,
        "action_state": action_state,
        "effective_session_date": effective_session_date,
        "event_type": event_type,
        "observed_at": "2025-08-15T19:57:00Z",
        "available_at": "2025-08-15T19:59:00Z",
        "source_id": "FIXTURE:CORP_ACTION",
        "source_receipt_sha256": ACTION_RECEIPT_HASH,
    }


def _valid_inputs():
    candidates = [
        _candidate(security_id="CIQSEC:IQ101", company_id="1001", trading_item_id="501"),
        _candidate(
            security_id="CIQSEC:IQ202",
            company_id="1002",
            trading_item_id="502",
            primary_listing_state=AMBIGUOUS_DATE_LOCAL,
            primary_listing_proof_kind=PRIMARY_PROOF_AMBIGUOUS,
        ),
        _candidate(security_id="CIQSEC:IQ303", company_id="1003", trading_item_id="503"),
    ]
    actions = [
        _action(security_id="CIQSEC:IQ101", trading_item_id="501"),
        _action(security_id="CIQSEC:IQ202", trading_item_id="502"),
        _action(
            security_id="CIQSEC:IQ303",
            trading_item_id="503",
            action_state=ACTION_EFFECTIVE_TERMINAL,
            effective_session_date=DECISION_DAY,
            event_type="CASH_MERGER_PREOPEN_TRADING_SUSPENSION",
        ),
    ]
    return _source_authority(), candidates, actions, _receipts()


def _build():
    source, candidates, actions, receipts = _valid_inputs()
    return build_prebreakout_pit_authority(
        as_of=AS_OF,
        decision_session_date=DECISION_DAY,
        source_authority=source,
        candidate_rows=candidates,
        corporate_action_rows=actions,
        source_receipts=receipts,
        fixture=True,
    )


def test_compiles_exact_date_local_identity_availability_and_corporate_action_authority() -> None:
    packet = _build()
    verify_prebreakout_pit_authority(packet)

    assert packet.body["candidate_count"] == 3
    assert packet.body["eligible_count"] == 1
    assert packet.body["exclusion_count"] == 2
    assert packet.body["outcome_access_performed"] is False
    assert packet.body["financial_alpha_evidence"] == 0
    assert packet.body["statistical_evidence_weight"] == 0
    assert packet.body["current_survivor_fallback_used"] is False
    assert packet.body["ticker_entity_permno_fallback_used"] is False
    assert packet.eligible_rows[0]["security_id"] == "CIQSEC:IQ101"
    reasons = {row["security_id"]: row["exclusion_reason"] for row in packet.exclusion_rows}
    assert reasons == {
        "CIQSEC:IQ202": EXCLUSION_AMBIGUOUS_PRIMARY,
        "CIQSEC:IQ303": EXCLUSION_CA_EFFECTIVE,
    }


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "current_survivor_back_projection_used",
        "current_primary_back_projection_used",
        "alternate_listing_backfill_used",
        "ticker_fallback_used",
        "company_entity_fallback_used",
        "permno_fallback_used",
    ],
)
def test_forbidden_identity_or_survivor_fallback_flags_fail_closed(forbidden_field: str) -> None:
    source, candidates, actions, receipts = _valid_inputs()
    source[forbidden_field] = True
    with pytest.raises(PrebreakoutPITAuthorityError, match="forbidden_source_flag"):
        build_prebreakout_pit_authority(
            as_of=AS_OF,
            decision_session_date=DECISION_DAY,
            source_authority=source,
            candidate_rows=candidates,
            corporate_action_rows=actions,
            source_receipts=receipts,
            fixture=True,
        )


def test_ci_q_security_and_trading_item_identity_are_exact_and_not_ticker_compatible() -> None:
    source, candidates, actions, receipts = _valid_inputs()
    candidates[0]["security_id"] = "MU"
    with pytest.raises(PrebreakoutPITAuthorityError, match="ciq_security_id_required"):
        build_prebreakout_pit_authority(
            as_of=AS_OF,
            decision_session_date=DECISION_DAY,
            source_authority=source,
            candidate_rows=candidates,
            corporate_action_rows=actions,
            source_receipts=receipts,
            fixture=True,
        )

    source, candidates, actions, receipts = _valid_inputs()
    candidates[0]["spt_instrument_item_id"] = "SPT999"
    with pytest.raises(PrebreakoutPITAuthorityError, match="trading_item_alias_mismatch"):
        build_prebreakout_pit_authority(
            as_of=AS_OF,
            decision_session_date=DECISION_DAY,
            source_authority=source,
            candidate_rows=candidates,
            corporate_action_rows=actions,
            source_receipts=receipts,
            fixture=True,
        )


def test_candidate_and_corporate_action_future_availability_fail_closed() -> None:
    source, candidates, actions, receipts = _valid_inputs()
    candidates[0]["available_at"] = "2025-08-15T20:00:01Z"
    with pytest.raises(PrebreakoutPITAuthorityError, match="candidate_availability_order_invalid"):
        build_prebreakout_pit_authority(
            as_of=AS_OF,
            decision_session_date=DECISION_DAY,
            source_authority=source,
            candidate_rows=candidates,
            corporate_action_rows=actions,
            source_receipts=receipts,
            fixture=True,
        )

    source, candidates, actions, receipts = _valid_inputs()
    actions[0]["available_at"] = "2025-08-15T20:00:01Z"
    with pytest.raises(PrebreakoutPITAuthorityError, match="corporate_action_availability_order_invalid"):
        build_prebreakout_pit_authority(
            as_of=AS_OF,
            decision_session_date=DECISION_DAY,
            source_authority=source,
            candidate_rows=candidates,
            corporate_action_rows=actions,
            source_receipts=receipts,
            fixture=True,
        )

    source, candidates, actions, receipts = _valid_inputs()
    source["capture_mode"] = PROSPECTIVE_CAPTURE_MODE
    source["historical_as_of_mechanically_bound"] = False
    with pytest.raises(PrebreakoutPITAuthorityError, match="prospective_source_receipt_after_asof"):
        build_prebreakout_pit_authority(
            as_of=AS_OF,
            decision_session_date=DECISION_DAY,
            source_authority=source,
            candidate_rows=candidates,
            corporate_action_rows=actions,
            source_receipts=receipts,
            fixture=True,
        )


def test_corporate_action_coverage_must_be_exact_and_unresolved_is_deterministically_excluded() -> None:
    source, candidates, actions, receipts = _valid_inputs()
    actions.pop()
    with pytest.raises(PrebreakoutPITAuthorityError, match="corporate_action_coverage_not_exact"):
        build_prebreakout_pit_authority(
            as_of=AS_OF,
            decision_session_date=DECISION_DAY,
            source_authority=source,
            candidate_rows=candidates,
            corporate_action_rows=actions,
            source_receipts=receipts,
            fixture=True,
        )

    source, candidates, actions, receipts = _valid_inputs()
    actions[0] = _action(
        security_id="CIQSEC:IQ101",
        trading_item_id="501",
        action_state=ACTION_UNRESOLVED,
        event_type="UNRESOLVED_TERMINAL_EVENT",
    )
    packet = build_prebreakout_pit_authority(
        as_of=AS_OF,
        decision_session_date=DECISION_DAY,
        source_authority=source,
        candidate_rows=candidates,
        corporate_action_rows=actions,
        source_receipts=receipts,
        fixture=True,
    )
    reasons = {row["security_id"]: row["exclusion_reason"] for row in packet.exclusion_rows}
    assert reasons["CIQSEC:IQ101"] == "CORPORATE_ACTION_UNRESOLVED"


def test_bminus1_proof_binds_w2_breakout_hash_and_exact_identity_with_zero_weight() -> None:
    packet = _build()
    proof = build_b_minus_one_eligibility_proof(
        authority=packet,
        case_id="GENERIC_SMOKE_ELIGIBLE",
        display_symbol="DISPLAY_ONLY",
        breakout_contract_sha256=BREAKOUT_HASH,
        breakout_session=BREAKOUT_DAY,
        b_minus_1_session=DECISION_DAY,
        expected_security_id="CIQSEC:IQ101",
        expected_trading_item_id="501",
    )
    body = proof.body
    assert body["status"] == "PIT_ELIGIBLE_B_MINUS_1"
    assert body["reason"] is None
    assert body["breakout_contract_sha256"] == BREAKOUT_HASH
    assert body["display_symbol_used_for_logic"] is False
    assert body["row_available_at"] == "2025-08-15T19:59:00.000000Z"
    assert body["statistical_weight"] == 0
    assert body["promotion_denominator_weight"] == 0
    assert body["outcome_access_performed"] is False


def test_bminus1_proof_records_deterministic_source_exclusion_without_rescue() -> None:
    packet = _build()
    excluded = build_b_minus_one_eligibility_proof(
        authority=packet,
        case_id="GENERIC_SMOKE_EXCLUDED",
        display_symbol="DISPLAY_ONLY",
        breakout_contract_sha256=BREAKOUT_HASH,
        breakout_session=BREAKOUT_DAY,
        b_minus_1_session=DECISION_DAY,
        expected_security_id="CIQSEC:IQ202",
        expected_trading_item_id="502",
    )
    assert excluded.body["status"] == "DETERMINISTIC_EXCLUSION"
    assert excluded.body["reason"] == EXCLUSION_AMBIGUOUS_PRIMARY

    absent = build_b_minus_one_eligibility_proof(
        authority=packet,
        case_id="GENERIC_SMOKE_ABSENT",
        display_symbol="DISPLAY_ONLY",
        breakout_contract_sha256=BREAKOUT_HASH,
        breakout_session=BREAKOUT_DAY,
        b_minus_1_session=DECISION_DAY,
        expected_security_id="CIQSEC:IQ999",
        expected_trading_item_id="999",
    )
    assert absent.body["status"] == "DETERMINISTIC_EXCLUSION"
    assert absent.body["reason"] == EXCLUSION_NOT_IN_SOURCE


def test_active_w3_rejects_missing_w2_hash_old_unbound_receipt_is_historical_bytes_only() -> None:
    with pytest.raises(PrebreakoutPITAuthorityError, match="w2_contract_hash_required"):
        build_b_minus_one_eligibility_proof(
            authority=None,
            case_id="MU_SMOKE",
            display_symbol="MU",
            breakout_contract_sha256=None,
            breakout_session=None,
            b_minus_1_session=None,
            expected_security_id=None,
            expected_trading_item_id=None,
        )


def test_current_w2_bound_smoke_state_is_bminus1_authority_unavailable_not_pass() -> None:
    for case_id, symbol in (("MU_SMOKE", "MU"), ("SNDK_SMOKE", "SNDK")):
        proof = build_b_minus_one_eligibility_proof(
            authority=None,
            case_id=case_id,
            display_symbol=symbol,
            breakout_contract_sha256=W2_CONTRACT_SHA256,
            breakout_session=BREAKOUT_DAY,
            b_minus_1_session=DECISION_DAY,
            expected_security_id=None,
            expected_trading_item_id=None,
        )
        assert proof.body["status"] == "DETERMINISTIC_UNAVAILABLE"
        assert proof.body["reason"] == B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE
        assert proof.body["breakout_contract_sha256"] == W2_CONTRACT_SHA256
        assert proof.body["display_symbol_used_for_logic"] is False
        assert proof.body["statistical_weight"] == 0
        assert proof.body["promotion_denominator_weight"] == 0
        assert proof.body["financial_alpha_evidence"] == 0


def test_current_w3_rejects_any_breakout_hash_other_than_frozen_w2() -> None:
    with pytest.raises(PrebreakoutPITAuthorityError, match="w2_contract_hash_mismatch"):
        build_b_minus_one_eligibility_proof(
            authority=None,
            case_id="HASH_DRIFT",
            display_symbol="DISPLAY_ONLY",
            breakout_contract_sha256="b" * 64,
            breakout_session=BREAKOUT_DAY,
            b_minus_1_session=DECISION_DAY,
        )


def test_authority_packet_tamper_fails_closed() -> None:
    packet = _build().as_dict()
    tampered = deepcopy(packet)
    tampered["eligible_rows"][0]["active_tradable"] = False
    with pytest.raises(PrebreakoutPITAuthorityError, match="authority_hash_mismatch"):
        verify_prebreakout_pit_authority(tampered)


def test_wrong_authority_date_cannot_be_relabelled_as_bminus1() -> None:
    packet = _build()
    with pytest.raises(PrebreakoutPITAuthorityError, match="authority_not_bminus1_session"):
        build_b_minus_one_eligibility_proof(
            authority=packet,
            case_id="DATE_MISMATCH",
            display_symbol="DISPLAY_ONLY",
            breakout_contract_sha256=BREAKOUT_HASH,
            breakout_session="2025-08-19",
            b_minus_1_session="2025-08-18",
            expected_security_id="CIQSEC:IQ101",
            expected_trading_item_id="501",
        )
