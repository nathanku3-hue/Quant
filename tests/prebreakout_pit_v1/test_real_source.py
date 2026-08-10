from __future__ import annotations

from datetime import date, timedelta

from research.prebreakout_pit_v1.authority import ACTION_CLEAR, ACTION_EFFECTIVE_TERMINAL, ACTION_UNRESOLVED
from research.prebreakout_pit_v1.real_source import (
    LifecycleState,
    apply_lifecycle_transition,
    classify_delisting_event,
    classify_lifecycle_transition,
    freeze_session_partition,
    resolve_mna_role,
)


def _sessions(count: int = 346) -> list[str]:
    start = date(2025, 1, 1)
    return [(start + timedelta(days=index)).isoformat() for index in range(count)]


def test_freeze_session_partition_is_exact_nonoverlapping_60_226_20_20_20() -> None:
    sessions = _sessions()
    frozen = freeze_session_partition(sessions)

    assert len(frozen["feature_warmup"]) == 60
    assert len(frozen["w5_development"]) == 226
    assert len(frozen["post_development_embargo"]) == 20
    assert len(frozen["w6_lockbox_decisions"]) == 20
    assert len(frozen["lockbox_label_maturity_tail"]) == 20
    flattened = (
        frozen["feature_warmup"]
        + frozen["w5_development"]
        + frozen["post_development_embargo"]
        + frozen["w6_lockbox_decisions"]
        + frozen["lockbox_label_maturity_tail"]
    )
    assert flattened == sessions
    assert frozen["development_labels_overlap_w6_lockbox"] is False
    assert frozen["w6_labels_opened"] is False


def test_mna_role_resolution_separates_global_blue_target_from_shift4_acquirer() -> None:
    headline = (
        "Shift4 Payments, Inc. (NYSE:FOUR) completed the acquisition of "
        "Global Blue Group Holding AG (NYSE:GB) from group of shareholders."
    )
    assert resolve_mna_role(headline, ["GB"]) == "WHOLE_COMPANY_TARGET"
    assert resolve_mna_role(headline, ["FOUR"]) == "NONTERMINAL_COUNTERPARTY_OR_PARTIAL"


def test_mna_role_resolution_keeps_micron_acquisition_and_asset_sale_nonterminal() -> None:
    acquirer = (
        "Micron Technology, Inc. (NasdaqGS:MU) completed the acquisition of P5 Fabrication Site "
        "and Facilities from Powerchip Semiconductor Manufacturing Corp. (TWSE:6770)."
    )
    seller = (
        "Texas Instruments Incorporated (NasdaqGS:TXN) completed the acquisition of 300-mm "
        "semiconductor factory in Lehi, Utah from Micron Technology, Inc. (NasdaqGS:MU)."
    )
    assert resolve_mna_role(acquirer, ["MU"]) == "NONTERMINAL_COUNTERPARTY_OR_PARTIAL"
    assert resolve_mna_role(seller, ["MU"]) == "NONTERMINAL_COUNTERPARTY_OR_PARTIAL"


def test_delisting_classifier_does_not_treat_compliance_notice_as_terminal() -> None:
    assert (
        classify_delisting_event(
            "Tilray Brands Receives Non-Compliance Letter from Nasdaq Regarding Minimum Bid Price Requirement"
        )
        == "NONTERMINAL_LISTING_ADMIN"
    )
    assert (
        classify_delisting_event("Shares of Global Blue to Delist from Exchange After Completion of Acquisition")
        == "POTENTIAL_TERMINAL_UNRESOLVED"
    )
    assert classify_delisting_event("Pactiv Evergreen's Stock Delists from Nasdaq") == "TERMINAL_EFFECTIVE"


def test_lifecycle_transition_activates_only_on_first_captured_session_strictly_after_event_date() -> None:
    sessions = ["2025-07-01", "2025-07-02", "2025-07-03", "2025-07-07"] + _sessions()[4:346]
    sessions = sorted(set(sessions))[:346]
    row = {
        "SP_ENTITY_ID": "10976234",
        "EVENT_DATE": "2025-07-02",
        "EVENT_OID": "38575088",
        "EVENT_TYPE": "M&A: Transaction Closing",
        "HEADLINE": (
            "Shift4 Payments, Inc. (NYSE:FOUR) completed the acquisition of "
            "Global Blue Group Holding AG (NYSE:GB) from group of shareholders."
        ),
        "DESCRIPTION": "",
    }
    transition = classify_lifecycle_transition(row, entity_tickers=["GB"], session_spine=sessions)
    assert transition is not None
    assert transition.activation_session == "2025-07-03"
    assert transition.transition_kind == "SET_EFFECTIVE"
    assert transition.state_event_type == "CIQ_MNA_TARGET_CLOSING"


def test_lifecycle_state_machine_is_fail_closed_but_admin_clear_cannot_resurrect_effective_terminal() -> None:
    sessions = _sessions()
    unresolved = classify_lifecycle_transition(
        {
            "SP_ENTITY_ID": "1",
            "EVENT_DATE": sessions[1],
            "EVENT_OID": "10",
            "EVENT_TYPE": "Delisting",
            "HEADLINE": "Example Corp Common Stock to Delist from Nasdaq",
            "DESCRIPTION": "",
        },
        entity_tickers=["EXM"],
        session_spine=sessions,
    )
    effective = classify_lifecycle_transition(
        {
            "SP_ENTITY_ID": "1",
            "EVENT_DATE": sessions[3],
            "EVENT_OID": "11",
            "EVENT_TYPE": "Delisting",
            "HEADLINE": "Example Corp Stock Delists from Nasdaq",
            "DESCRIPTION": "",
        },
        entity_tickers=["EXM"],
        session_spine=sessions,
    )
    admin = classify_lifecycle_transition(
        {
            "SP_ENTITY_ID": "1",
            "EVENT_DATE": sessions[5],
            "EVENT_OID": "12",
            "EVENT_TYPE": "Delisting",
            "HEADLINE": "Example Corp Regains Compliance with Nasdaq Minimum Bid Price Requirement",
            "DESCRIPTION": "",
        },
        entity_tickers=["EXM"],
        session_spine=sessions,
    )
    assert unresolved is not None and effective is not None and admin is not None

    state = apply_lifecycle_transition(LifecycleState(), unresolved)
    assert state.action_state == ACTION_UNRESOLVED
    state = apply_lifecycle_transition(state, effective)
    assert state.action_state == ACTION_EFFECTIVE_TERMINAL
    final = apply_lifecycle_transition(state, admin)
    assert final.action_state == ACTION_EFFECTIVE_TERMINAL
    assert final != LifecycleState(action_state=ACTION_CLEAR)
