from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from research.prebreakout_discovery_v1.breakout import (
    algorithmic_breakout_events,
    enforce_b_minus_one_pit_proof,
    measure_ttfld,
    verify_b_minus_one_smoke_obligation,
)
from research.prebreakout_discovery_v1.preregistration import (
    BREAKOUT_EPISODE_COOLDOWN_SESSIONS,
    BREAKOUT_LOOKBACK_SESSIONS,
    CONTRACT_SHA256,
    FAMILY_ID,
    FALSIFIER_SPECS,
    RISK_SET_SPEC_ID,
    LEAD_LOOKBACK_SESSIONS,
    MIN_LEGITIMATE_LEAD_SESSIONS,
    PRIMARY_HORIZON_SESSIONS,
    SEARCH_FAMILY_ID,
    SECONDARY_HORIZON_SESSIONS,
    SMOKE_ACCEPTANCE_WEIGHT,
    TRIAL_BUDGET_MAX,
    TRIAL_LEDGER_SCOPE,
    WINNER_FRACTION,
    contract_snapshot,
    validate_contract,
)


def _sessions(count: int) -> list[str]:
    start = date(2026, 1, 1)
    return [(start + timedelta(days=index)).isoformat() for index in range(count)]


def _rows(
    closes: list[float],
    security_id: str = "CIQSEC:IQ101",
    trading_item_id: str = "101",
) -> list[dict[str, object]]:
    sessions = _sessions(len(closes))
    return [
        {
            "security_id": security_id,
            "trading_item_id": trading_item_id,
            "session_date": session,
            "close": close,
        }
        for session, close in zip(sessions, closes, strict=True)
    ]


def test_w2_contract_is_exactly_frozen_and_outcome_blind() -> None:
    validate_contract()
    snap = contract_snapshot()
    assert FAMILY_ID == "PREBREAKOUT_DISCOVERY_v1"
    assert RISK_SET_SPEC_ID == "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1"
    assert PRIMARY_HORIZON_SESSIONS == 20
    assert SECONDARY_HORIZON_SESSIONS == 10
    assert WINNER_FRACTION == 0.05
    assert BREAKOUT_LOOKBACK_SESSIONS == 20
    assert BREAKOUT_EPISODE_COOLDOWN_SESSIONS == 20
    assert LEAD_LOOKBACK_SESSIONS == 20
    assert MIN_LEGITIMATE_LEAD_SESSIONS == 1
    assert SEARCH_FAMILY_ID == "PREBREAKOUT_SEARCH_v1"
    assert TRIAL_LEDGER_SCOPE == "PREBREAKOUT_V1_TRIAL_LEDGER"
    assert TRIAL_BUDGET_MAX == 8
    assert SMOKE_ACCEPTANCE_WEIGHT == 0
    assert len(FALSIFIER_SPECS) == 8
    assert len(CONTRACT_SHA256) == 64
    assert snap["authority"] == {
        "provider_capture": "NOT_AUTHORIZED_BY_W2",
        "outcome_open": "FORBIDDEN",
        "prospective_clock_start": "FORBIDDEN_UNTIL_W3_W4_W5_W6_GATES",
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }


def test_algorithmic_breakout_B_is_strict_prior_20_high_with_20_full_session_cooldown() -> None:
    closes = [100.0] * 20 + [101.0] + [100.0] * 20 + [102.0]
    events = algorithmic_breakout_events(_rows(closes))
    assert [event.session_index for event in events] == [20, 41]
    assert events[0].security_id == "CIQSEC:IQ101"
    assert events[0].trading_item_id == "101"
    assert events[0].prior_high_20 == 100.0
    assert events[0].close == 101.0

    equality = [100.0] * 20 + [100.0]
    assert algorithmic_breakout_events(_rows(equality)) == []

    too_soon = [100.0] * 20 + [101.0, 102.0] + [100.0] * 19
    events = algorithmic_breakout_events(_rows(too_soon))
    assert [event.session_index for event in events] == [20]


def test_breakout_input_fails_closed_on_duplicate_invalid_or_mixed_listing_rows() -> None:
    rows = _rows([100.0] * 21)
    rows[1]["session_date"] = rows[0]["session_date"]
    with pytest.raises(ValueError, match="duplicate_close_session"):
        algorithmic_breakout_events(rows)

    rows = _rows([100.0] * 21)
    rows[2]["close"] = 0.0
    with pytest.raises(ValueError, match="finite_positive"):
        algorithmic_breakout_events(rows)

    rows = _rows([100.0] * 21)
    rows[-1]["security_id"] = "CIQSEC:IQ202"
    rows[-1]["trading_item_id"] = "202"
    with pytest.raises(ValueError, match="one_exact_listing"):
        algorithmic_breakout_events(rows)

    rows = _rows([100.0] * 21)
    rows[0].pop("trading_item_id")
    with pytest.raises(ValueError, match="trading_item_id_required"):
        algorithmic_breakout_events(rows)


def test_ttfld_is_earliest_flag_in_B_minus_20_through_B_minus_1_and_misses_are_zero_effective_lead() -> None:
    sessions = _sessions(40)
    breakout = sessions[30]
    result = measure_ttfld(
        ordered_sessions=sessions,
        breakout_session=breakout,
        flag_sessions=[sessions[9], sessions[10], sessions[23], sessions[29], sessions[30]],
    )
    assert result.status == "DETECTED_PREBREAKOUT"
    assert result.first_legitimate_detection_session == sessions[10]
    assert result.b_minus_one_session == sessions[29]
    assert result.ttfld_sessions == 20
    assert result.effective_ttfld_sessions == 20

    missed = measure_ttfld(
        ordered_sessions=sessions,
        breakout_session=breakout,
        flag_sessions=[sessions[9], sessions[30], sessions[31]],
    )
    assert missed.status == "MISSED_PREBREAKOUT"
    assert missed.first_legitimate_detection_session is None
    assert missed.ttfld_sessions is None
    assert missed.effective_ttfld_sessions == 0


def test_B_minus_one_smoke_obligation_requires_flag_or_deterministic_exclusion() -> None:
    sessions = _sessions(35)
    breakout = sessions[30]

    flagged = verify_b_minus_one_smoke_obligation(
        security_id="CIQSEC:SMOKE1",
        ordered_sessions=sessions,
        breakout_session=breakout,
        b_minus_one_eligible=True,
        deterministic_exclusion_reason=None,
        flag_sessions=[sessions[29]],
    )
    assert flagged.status == "FLAGGED_PREBREAKOUT"
    assert flagged.ttfld_sessions == 1
    assert flagged.acceptance_weight == 0

    with pytest.raises(ValueError, match="eligible_without_prebreakout_flag"):
        verify_b_minus_one_smoke_obligation(
            security_id="CIQSEC:SMOKE2",
            ordered_sessions=sessions,
            breakout_session=breakout,
            b_minus_one_eligible=True,
            deterministic_exclusion_reason=None,
            flag_sessions=[breakout],
        )

    excluded = verify_b_minus_one_smoke_obligation(
        security_id="CIQSEC:SMOKE3",
        ordered_sessions=sessions,
        breakout_session=breakout,
        b_minus_one_eligible=False,
        deterministic_exclusion_reason="CORPORATE_ACTION_UNRESOLVED",
        flag_sessions=[],
    )
    assert excluded.status == "DETERMINISTIC_EXCLUSION"
    assert excluded.acceptance_weight == 0

    with pytest.raises(ValueError, match="deterministic_exclusion_reason_required"):
        verify_b_minus_one_smoke_obligation(
            security_id="CIQSEC:SMOKE4",
            ordered_sessions=sessions,
            breakout_session=breakout,
            b_minus_one_eligible=False,
            deterministic_exclusion_reason="OTHER",
            flag_sessions=[],
        )


def test_w3_style_pit_proof_is_bound_to_w2_and_unavailable_never_satisfies_smoke_obligation() -> None:
    sessions = _sessions(35)
    breakout = sessions[30]
    b_minus_one = sessions[29]
    base = {
        "family_id": FAMILY_ID,
        "display_symbol": "TRACE_ONLY",
        "display_symbol_used_for_logic": False,
        "breakout_contract_sha256": CONTRACT_SHA256,
        "breakout_session": breakout,
        "b_minus_1_session": b_minus_one,
        "security_id": "CIQSEC:IQ101",
        "trading_item_id": "101",
        "statistical_weight": 0,
        "promotion_denominator_weight": 0,
        "outcome_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }

    eligible = {**base, "status": "PIT_ELIGIBLE_B_MINUS_1", "reason": None}
    result = enforce_b_minus_one_pit_proof(
        pit_proof=eligible,
        ordered_sessions=sessions,
        flag_sessions=[sessions[27]],
    )
    assert result.status == "FLAGGED_PREBREAKOUT"
    assert result.ttfld_sessions == 3

    with pytest.raises(ValueError, match="eligible_without_prebreakout_flag"):
        enforce_b_minus_one_pit_proof(
            pit_proof=eligible,
            ordered_sessions=sessions,
            flag_sessions=[breakout],
        )

    excluded = {
        **base,
        "status": "DETERMINISTIC_EXCLUSION",
        "reason": "NOT_IN_DATE_LOCAL_SOURCE_POPULATION",
    }
    result = enforce_b_minus_one_pit_proof(
        pit_proof=excluded,
        ordered_sessions=sessions,
        flag_sessions=[],
    )
    assert result.status == "DETERMINISTIC_EXCLUSION"

    unavailable = {
        **base,
        "status": "DETERMINISTIC_UNAVAILABLE",
        "reason": "B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE",
    }
    with pytest.raises(ValueError, match="upstream_authority_unavailable"):
        enforce_b_minus_one_pit_proof(
            pit_proof=unavailable,
            ordered_sessions=sessions,
            flag_sessions=[],
        )

    wrong_b1 = {**eligible, "b_minus_1_session": sessions[28]}
    with pytest.raises(ValueError, match="b_minus_one_not_exact"):
        enforce_b_minus_one_pit_proof(
            pit_proof=wrong_b1,
            ordered_sessions=sessions,
            flag_sessions=[sessions[27]],
        )


def test_core_has_no_named_smoke_ticker_branch_provider_or_outcome_evaluator() -> None:
    root = Path("research/prebreakout_discovery_v1")
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    forbidden = (
        '"MU"',
        '"SNDK"',
        "yfinance",
        "CiqCycleV1Adapter",
        "discovery_outcomes",
        "aov0_historical_pit_replay",
        "submit_order",
    )
    assert not any(token in text for token in forbidden)
