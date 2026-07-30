from __future__ import annotations

from copy import deepcopy

import pytest

from core.gv_fs0_canonical import domain_hash
from gv_portfolio_v0.admission import (
    StrategyAdmissionError,
    build_capital_competition,
    build_decision_snapshot,
    cash_decision_record,
    decision_projections,
    instrument_decision_record,
    validate_capital_competition,
    validate_decision_projections,
    validate_decision_records,
    validate_decision_snapshot,
)
from gv_portfolio_v0.thesis import (
    StrategyThesisError,
    living_thesis_lite,
    scenario_range,
    unchanged_aim_watch_observation,
)


def _thesis(
    evidence_id: str,
    *,
    claim: str,
    bear: str,
    base: str,
    bull: str,
    hard_falsifiers: tuple[str, ...] = (),
    watch_conditions: tuple[str, ...] = (),
) -> dict[str, object]:
    return living_thesis_lite(
        principal_claim=claim,
        scenario=scenario_range(
            bear_value=bear, base_value=base, bull_value=bull
        ),
        evidence_reference_ids=[evidence_id],
        hard_falsifiers=hard_falsifiers,
        watch_conditions=watch_conditions,
    )


def _fixture() -> dict[str, object]:
    evidence_ids = [
        "EVD_NSTAR",
        "EVD_HARBOR",
        "EVD_RIVAL",
        "EVD_ORBIT",
        "EVD_LATER",
    ]
    reviews = [
        instrument_decision_record(
            instrument_id="INS_NSTAR",
            symbol="NSTAR",
            relationship="PRINCIPAL_THESIS",
            outcome="ADMIT",
            living_thesis=_thesis(
                evidence_ids[0],
                claim="Recurring revenue durability remains intact.",
                bear="20",
                base="30",
                bull="42",
                hard_falsifiers=("renewal_rate_below_70_percent",),
                watch_conditions=(
                    "order_intake_softens_without_covenant_breach",
                ),
            ),
        ),
        instrument_decision_record(
            instrument_id="INS_HARBOR",
            symbol="HARBOR",
            relationship="SUBSTITUTE",
            outcome="ADMIT",
            living_thesis=_thesis(
                evidence_ids[1],
                claim="Harbor is the best incremental use of available cash.",
                bear="30",
                base="48",
                bull="70",
                hard_falsifiers=("net_debt_to_ebitda_above_4",),
                watch_conditions=("margin_compression_below_base_band",),
            ),
        ),
        instrument_decision_record(
            instrument_id="INS_RIVAL",
            symbol="RIVAL",
            relationship="COMPETITOR",
            outcome="REJECT",
            living_thesis=_thesis(
                evidence_ids[2],
                claim="Rival breaches the mandate leverage screen.",
                bear="10",
                base="28",
                bull="55",
                hard_falsifiers=("mandate_leverage_screen_failed",),
            ),
        ),
        instrument_decision_record(
            instrument_id="INS_ORBIT",
            symbol="ORBIT",
            relationship="ALTERNATIVE",
            outcome="ABSTAIN",
            living_thesis=_thesis(
                evidence_ids[3],
                claim="Orbit evidence is insufficient for commitment.",
                bear="18",
                base="44",
                bull="80",
                watch_conditions=("obtain_customer_concentration_evidence",),
            ),
        ),
    ]
    cash = cash_decision_record(
        classifications=["AVAILABLE", "RESEARCH_RESERVE"],
        role="explicit_competing_allocation",
    )
    candidates = [
        {
            "candidate": "HARBOR",
            "instrument_id": "INS_HARBOR",
            "outcome": "ADMIT",
            "expected_value_bps": 700,
            "risk_penalty_bps": 200,
            "cost_penalty_bps": 25,
        },
        {
            "candidate": "RIVAL",
            "instrument_id": "INS_RIVAL",
            "outcome": "REJECT",
            "expected_value_bps": 900,
            "risk_penalty_bps": 100,
            "cost_penalty_bps": 25,
        },
        {
            "candidate": "ORBIT",
            "instrument_id": "INS_ORBIT",
            "outcome": "ABSTAIN",
            "expected_value_bps": 600,
            "risk_penalty_bps": 500,
            "cost_penalty_bps": 25,
        },
        {
            "candidate": "CASH",
            "instrument_id": None,
            "outcome": "CASH",
            "expected_value_bps": 150,
            "risk_penalty_bps": 0,
            "cost_penalty_bps": 0,
        },
    ]
    snapshot = build_decision_snapshot(
        created_at="2026-07-20T09:05:00.000000Z",
        portfolio_aim_id="AIM_TEST",
        reviews=reviews,
        cash_outcome=cash,
        competition_candidates=candidates,
        available_evidence_reference_ids=evidence_ids,
        selected_quantity="5",
        reference_price="40",
        fee="1",
    )
    return {
        "evidence_ids": evidence_ids,
        "reviews": reviews,
        "cash": cash,
        "candidates": candidates,
        "snapshot": snapshot,
    }


def _rehash_snapshot(snapshot: dict[str, object]) -> None:
    payload = {
        key: value for key, value in snapshot.items() if key != "decision_snapshot_id"
    }
    snapshot["decision_snapshot_id"] = "DSN_" + domain_hash(
        "GV-PORTFOLIO-V0:DSN:V1", payload
    )


def test_valid_snapshot_is_sole_authority_and_projections_are_copies() -> None:
    fixture = _fixture()
    snapshot = fixture["snapshot"]
    validate_decision_snapshot(
        snapshot,
        available_evidence_reference_ids=fixture["evidence_ids"],
    )
    reviews, cash = decision_projections(snapshot)
    reviews[0]["outcome"] = "REJECT"
    cash["classification"] = ["FORGED"]
    assert snapshot["reviews"][0]["outcome"] == "ADMIT"
    assert snapshot["cash_outcome"]["classification"] == [
        "AVAILABLE",
        "RESEARCH_RESERVE",
    ]


def test_persisted_reviews_cannot_contradict_snapshot() -> None:
    fixture = _fixture()
    reviews = deepcopy(fixture["reviews"])
    reviews[0]["outcome"] = "REJECT"
    with pytest.raises(StrategyAdmissionError, match="REVIEWS_PROJECTION_MISMATCH"):
        validate_decision_projections(
            fixture["snapshot"],
            reviews_projection=reviews,
            cash_projection=fixture["cash"],
            available_evidence_reference_ids=fixture["evidence_ids"],
        )


def test_persisted_cash_cannot_contradict_snapshot() -> None:
    fixture = _fixture()
    cash = deepcopy(fixture["cash"])
    cash["classification"] = ["FORGED"]
    with pytest.raises(StrategyAdmissionError, match="CASH_PROJECTION_MISMATCH"):
        validate_decision_projections(
            fixture["snapshot"],
            reviews_projection=fixture["reviews"],
            cash_projection=cash,
            available_evidence_reference_ids=fixture["evidence_ids"],
        )


@pytest.mark.parametrize("candidate_id", ["ORBIT", "RIVAL"])
def test_validly_rehashed_ineligible_candidate_cannot_be_winner(
    candidate_id: str,
) -> None:
    fixture = _fixture()
    snapshot = deepcopy(fixture["snapshot"])
    competition = snapshot["capital_competition"]
    forged = next(
        row for row in competition["candidates"] if row["candidate"] == candidate_id
    )
    competition["selected_candidate"] = forged["candidate"]
    competition["selected_instrument_id"] = forged["instrument_id"]
    competition["selected_net_score_bps"] = forged["net_score_bps"]
    snapshot["selected_action"] = "BUY"
    snapshot["selected_instrument_id"] = forged["instrument_id"]
    _rehash_snapshot(snapshot)
    with pytest.raises(StrategyAdmissionError, match="CAPITAL_COMPETITION_MISMATCH"):
        validate_decision_snapshot(
            snapshot,
            available_evidence_reference_ids=fixture["evidence_ids"],
        )


def test_stored_net_score_cannot_override_recomputation() -> None:
    fixture = _fixture()
    competition = deepcopy(fixture["snapshot"]["capital_competition"])
    competition["candidates"][0]["net_score_bps"] += 1
    competition["selected_net_score_bps"] += 1
    with pytest.raises(StrategyAdmissionError, match="CAPITAL_COMPETITION_MISMATCH"):
        validate_capital_competition(
            competition,
            reviews=fixture["reviews"],
            cash_outcome=fixture["cash"],
            available_evidence_reference_ids=fixture["evidence_ids"],
        )


def test_negative_penalty_terms_are_rejected() -> None:
    fixture = _fixture()
    candidates = deepcopy(fixture["candidates"])
    candidates[0]["risk_penalty_bps"] = -1
    with pytest.raises(
        StrategyAdmissionError, match="RISK_PENALTY_MUST_BE_NONNEGATIVE"
    ):
        build_capital_competition(
            candidates,
            reviews=fixture["reviews"],
            cash_outcome=fixture["cash"],
            available_evidence_reference_ids=fixture["evidence_ids"],
        )


def test_stored_tie_ordering_cannot_override_lexical_winner() -> None:
    fixture = _fixture()
    candidates = deepcopy(fixture["candidates"])
    cash = next(row for row in candidates if row["candidate"] == "CASH")
    cash["expected_value_bps"] = 475
    competition = build_capital_competition(
        candidates,
        reviews=fixture["reviews"],
        cash_outcome=fixture["cash"],
        available_evidence_reference_ids=fixture["evidence_ids"],
    )
    assert competition["selected_candidate"] == "CASH"
    harbor = next(
        row for row in competition["candidates"] if row["candidate"] == "HARBOR"
    )
    competition["selected_candidate"] = "HARBOR"
    competition["selected_instrument_id"] = harbor["instrument_id"]
    competition["selected_net_score_bps"] = harbor["net_score_bps"]
    with pytest.raises(StrategyAdmissionError, match="CAPITAL_COMPETITION_MISMATCH"):
        validate_capital_competition(
            competition,
            reviews=fixture["reviews"],
            cash_outcome=fixture["cash"],
            available_evidence_reference_ids=fixture["evidence_ids"],
        )


def test_validly_rehashed_action_instrument_mismatch_is_rejected() -> None:
    fixture = _fixture()
    snapshot = deepcopy(fixture["snapshot"])
    snapshot["selected_action"] = "CASH"
    snapshot["selected_instrument_id"] = None
    _rehash_snapshot(snapshot)
    with pytest.raises(StrategyAdmissionError, match="DECISION_SELECTION_MISMATCH"):
        validate_decision_snapshot(
            snapshot,
            available_evidence_reference_ids=fixture["evidence_ids"],
        )


def test_validly_rehashed_empty_aim_binding_is_rejected() -> None:
    fixture = _fixture()
    snapshot = deepcopy(fixture["snapshot"])
    snapshot["portfolio_aim_id"] = ""
    _rehash_snapshot(snapshot)
    with pytest.raises(StrategyAdmissionError, match="PORTFOLIO_AIM_ID_REQUIRED"):
        validate_decision_snapshot(
            snapshot,
            available_evidence_reference_ids=fixture["evidence_ids"],
        )


def test_dangling_evidence_reference_is_rejected() -> None:
    fixture = _fixture()
    reviews = deepcopy(fixture["reviews"])
    reviews[0]["living_thesis_lite"]["evidence_reference_ids"] = ["EVD_MISSING"]
    with pytest.raises(StrategyThesisError, match="DANGLING_EVIDENCE_REFERENCE"):
        validate_decision_records(
            reviews,
            fixture["cash"],
            available_evidence_reference_ids=fixture["evidence_ids"],
        )


def test_unknown_outcome_is_rejected() -> None:
    fixture = _fixture()
    reviews = deepcopy(fixture["reviews"])
    reviews[0]["outcome"] = "PROMOTE"
    with pytest.raises(StrategyAdmissionError, match="INSTRUMENT_OUTCOME_INVALID"):
        validate_decision_records(
            reviews,
            fixture["cash"],
            available_evidence_reference_ids=fixture["evidence_ids"],
        )


def test_duplicate_instrument_decision_is_rejected() -> None:
    fixture = _fixture()
    reviews = [*deepcopy(fixture["reviews"]), deepcopy(fixture["reviews"][0])]
    with pytest.raises(StrategyAdmissionError, match="DUPLICATE_INSTRUMENT_DECISION"):
        validate_decision_records(
            reviews,
            fixture["cash"],
            available_evidence_reference_ids=fixture["evidence_ids"],
        )


def test_scenario_values_must_be_finite_and_ordered() -> None:
    with pytest.raises(StrategyThesisError, match="SCENARIO_RANGE_ORDER_INVALID"):
        scenario_range(bear_value="30", base_value="20", bull_value="40")
    with pytest.raises(StrategyThesisError, match="BULL_VALUE_FINITE_REQUIRED"):
        scenario_range(bear_value="10", base_value="20", bull_value="NaN")


def test_principal_claim_must_be_nonempty() -> None:
    with pytest.raises(StrategyThesisError, match="PRINCIPAL_CLAIM_REQUIRED"):
        living_thesis_lite(
            principal_claim="  ",
            scenario=scenario_range(
                bear_value="10", base_value="20", bull_value="30"
            ),
            evidence_reference_ids=["EVD_TEST"],
            hard_falsifiers=[],
            watch_conditions=[],
        )


def test_watch_and_hard_falsifier_definitions_must_not_overlap() -> None:
    with pytest.raises(
        StrategyThesisError, match="THESIS_RULE_CLASSIFICATION_OVERLAP"
    ):
        living_thesis_lite(
            principal_claim="A valid claim.",
            scenario=scenario_range(
                bear_value="10", base_value="20", bull_value="30"
            ),
            evidence_reference_ids=["EVD_TEST"],
            hard_falsifiers=["same_rule"],
            watch_conditions=["same_rule"],
        )


def test_watch_match_without_hard_falsifier_preserves_aim() -> None:
    fixture = _fixture()
    thesis = fixture["reviews"][0]["living_thesis_lite"]
    observation = unchanged_aim_watch_observation(
        living_thesis=thesis,
        available_evidence_reference_ids=fixture["evidence_ids"],
        evidence_reference_id="EVD_LATER",
        watch_condition_matches=[
            "order_intake_softens_without_covenant_breach"
        ],
        hard_falsifier_matches=[],
        portfolio_aim_id_before="AIM_TEST",
        portfolio_aim_id_after="AIM_TEST",
    )
    assert observation["classification"] == "WATCH"
    assert observation["hard_falsifier_fired"] is False
    assert observation["aim_changed"] is False


def test_dangling_observation_evidence_reference_is_rejected() -> None:
    fixture = _fixture()
    thesis = fixture["reviews"][0]["living_thesis_lite"]
    with pytest.raises(
        StrategyThesisError, match="DANGLING_OBSERVATION_EVIDENCE_REFERENCE"
    ):
        unchanged_aim_watch_observation(
            living_thesis=thesis,
            available_evidence_reference_ids=fixture["evidence_ids"],
            evidence_reference_id="EVD_MISSING",
            watch_condition_matches=[
                "order_intake_softens_without_covenant_breach"
            ],
            hard_falsifier_matches=[],
            portfolio_aim_id_before="AIM_TEST",
            portfolio_aim_id_after="AIM_TEST",
        )


def test_watch_matches_are_canonicalized_independent_of_input_order() -> None:
    fixture = _fixture()
    thesis = deepcopy(fixture["reviews"][0]["living_thesis_lite"])
    thesis["watch_conditions"] = ["watch_b", "watch_a"]
    observation = unchanged_aim_watch_observation(
        living_thesis=thesis,
        available_evidence_reference_ids=fixture["evidence_ids"],
        evidence_reference_id="EVD_LATER",
        watch_condition_matches=["watch_b", "watch_a"],
        hard_falsifier_matches=[],
        portfolio_aim_id_before="AIM_TEST",
        portfolio_aim_id_after="AIM_TEST",
    )
    assert observation["watch_condition_matches"] == ["watch_a", "watch_b"]


def test_undeclared_observation_match_is_rejected() -> None:
    fixture = _fixture()
    thesis = fixture["reviews"][0]["living_thesis_lite"]
    with pytest.raises(
        StrategyThesisError, match="UNDECLARED_WATCH_CONDITION_MATCH"
    ):
        unchanged_aim_watch_observation(
            living_thesis=thesis,
            available_evidence_reference_ids=fixture["evidence_ids"],
            evidence_reference_id="EVD_LATER",
            watch_condition_matches=["invented_watch"],
            hard_falsifier_matches=[],
            portfolio_aim_id_before="AIM_TEST",
            portfolio_aim_id_after="AIM_TEST",
        )


def test_hard_falsifier_cannot_preserve_unchanged_aim() -> None:
    fixture = _fixture()
    thesis = fixture["reviews"][0]["living_thesis_lite"]
    with pytest.raises(
        StrategyThesisError, match="HARD_FALSIFIER_BLOCKS_UNCHANGED_AIM"
    ):
        unchanged_aim_watch_observation(
            living_thesis=thesis,
            available_evidence_reference_ids=fixture["evidence_ids"],
            evidence_reference_id="EVD_LATER",
            watch_condition_matches=[
                "order_intake_softens_without_covenant_breach"
            ],
            hard_falsifier_matches=["renewal_rate_below_70_percent"],
            portfolio_aim_id_before="AIM_TEST",
            portfolio_aim_id_after="AIM_TEST",
        )
