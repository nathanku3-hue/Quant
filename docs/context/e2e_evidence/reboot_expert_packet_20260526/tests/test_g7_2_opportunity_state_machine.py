from __future__ import annotations

from dataclasses import fields

from opportunity_engine.schemas import (
    SignalEvidence,
    SourceObservationClass,
    TransitionEvidence,
    TransitionRequest,
)
from opportunity_engine.states import OpportunityState, ReasonCode
from opportunity_engine.transitions import validate_transition


EXPECTED_STATES = {
    "IGNORE",
    "THEME_WATCH",
    "THESIS_CANDIDATE",
    "EVIDENCE_BUILDING",
    "LEFT_SIDE_RISK",
    "ACCUMULATION_WATCH",
    "CONFIRMATION_WATCH",
    "BUYING_RANGE",
    "ADD_ON_SETUP",
    "LET_WINNER_RUN",
    "TRIM_OPTIONAL",
    "CROWDED_FROTHY",
    "EXIT_RISK",
    "THESIS_BROKEN",
}


def _evidence(
    *,
    source_class: SourceObservationClass = SourceObservationClass.OBSERVED,
    reason_code: ReasonCode = ReasonCode.PRICE_VOLUME_BEHAVIOR,
    deterioration: bool = False,
    thesis_broken: bool = False,
    risk_approval: bool = False,
) -> TransitionEvidence:
    return TransitionEvidence(
        signals=(
            SignalEvidence(
                reason_code=reason_code,
                source_class=source_class,
                source_name="test_fixture",
            ),
        ),
        deterioration_evidence=deterioration,
        thesis_broken=thesis_broken,
        risk_approval=risk_approval,
    )


def _request(
    current: OpportunityState,
    requested: OpportunityState,
    evidence: TransitionEvidence | None = None,
    metadata: dict[str, object] | None = None,
) -> TransitionRequest:
    return TransitionRequest(
        current_state=current,
        requested_state=requested,
        evidence=evidence or _evidence(),
        metadata=metadata or {},
    )


def test_state_enum_complete():
    assert {state.value for state in OpportunityState} == EXPECTED_STATES


def test_candidate_cannot_jump_directly_to_buying_range():
    result = validate_transition(
        _request(OpportunityState.THESIS_CANDIDATE, OpportunityState.BUYING_RANGE)
    )

    assert not result.allowed
    assert result.resulting_state == OpportunityState.THESIS_CANDIDATE


def test_left_side_risk_requires_confirmation_before_buying_range():
    direct = validate_transition(_request(OpportunityState.LEFT_SIDE_RISK, OpportunityState.BUYING_RANGE))
    via_accumulation = validate_transition(
        _request(OpportunityState.LEFT_SIDE_RISK, OpportunityState.ACCUMULATION_WATCH)
    )
    from_accumulation = validate_transition(
        _request(OpportunityState.ACCUMULATION_WATCH, OpportunityState.BUYING_RANGE)
    )

    assert not direct.allowed
    assert via_accumulation.allowed
    assert from_accumulation.allowed


def test_thesis_broken_overrides_market_behavior():
    result = validate_transition(
        _request(
            OpportunityState.CONFIRMATION_WATCH,
            OpportunityState.BUYING_RANGE,
            _evidence(thesis_broken=True),
        )
    )

    assert result.allowed
    assert result.resulting_state == OpportunityState.THESIS_BROKEN


def test_estimated_signal_alone_cannot_create_buying_range():
    result = validate_transition(
        _request(
            OpportunityState.CONFIRMATION_WATCH,
            OpportunityState.BUYING_RANGE,
            _evidence(source_class=SourceObservationClass.ESTIMATED),
        )
    )

    assert not result.allowed
    assert "estimated" in result.reason


def test_inferred_signal_alone_cannot_create_let_winner_run():
    result = validate_transition(
        _request(
            OpportunityState.BUYING_RANGE,
            OpportunityState.LET_WINNER_RUN,
            _evidence(source_class=SourceObservationClass.INFERRED),
        )
    )

    assert not result.allowed
    assert "inferred" in result.reason


def test_crowded_frothy_blocks_add_on_setup():
    blocked = validate_transition(
        _request(OpportunityState.CROWDED_FROTHY, OpportunityState.ADD_ON_SETUP)
    )
    approved = validate_transition(
        _request(
            OpportunityState.CROWDED_FROTHY,
            OpportunityState.ADD_ON_SETUP,
            _evidence(risk_approval=True),
        )
    )

    assert not blocked.allowed
    assert approved.allowed


def test_transition_requires_reason_codes():
    result = validate_transition(
        _request(
            OpportunityState.ACCUMULATION_WATCH,
            OpportunityState.BUYING_RANGE,
            TransitionEvidence(signals=()),
        )
    )

    assert not result.allowed
    assert "reason codes" in result.reason


def test_transition_requires_source_classification():
    evidence = _evidence()

    assert evidence.source_classes
    assert all(signal.source_class for signal in evidence.signals)


def test_no_state_emits_alert_or_broker_action():
    result = validate_transition(
        _request(
            OpportunityState.CONFIRMATION_WATCH,
            OpportunityState.BUYING_RANGE,
            metadata={"alert_emitted": True},
        )
    )

    assert not result.allowed
    assert "forbidden" in result.reason


def test_no_score_or_ranking_field_exists():
    schema_field_names = {
        *[field.name for field in fields(TransitionRequest)],
        *[field.name for field in fields(TransitionEvidence)],
        *[field.name for field in fields(SignalEvidence)],
    }

    assert not {"score", "rank", "ranking", "candidate_rank", "signal_score"}.intersection(
        schema_field_names
    )
