from __future__ import annotations

from opportunity_engine.schemas import (
    ACTION_FIELD_NAMES,
    SourceObservationClass,
    TransitionRequest,
    TransitionResult,
)
from opportunity_engine.states import OpportunityState, ReasonCode


ALLOWED_TRANSITIONS: dict[OpportunityState, frozenset[OpportunityState]] = {
    OpportunityState.IGNORE: frozenset(
        {
            OpportunityState.THEME_WATCH,
            OpportunityState.THESIS_CANDIDATE,
            OpportunityState.IGNORE,
        }
    ),
    OpportunityState.THEME_WATCH: frozenset(
        {
            OpportunityState.THESIS_CANDIDATE,
            OpportunityState.EVIDENCE_BUILDING,
            OpportunityState.IGNORE,
            OpportunityState.THEME_WATCH,
        }
    ),
    OpportunityState.THESIS_CANDIDATE: frozenset(
        {
            OpportunityState.EVIDENCE_BUILDING,
            OpportunityState.LEFT_SIDE_RISK,
            OpportunityState.THESIS_BROKEN,
            OpportunityState.THESIS_CANDIDATE,
        }
    ),
    OpportunityState.EVIDENCE_BUILDING: frozenset(
        {
            OpportunityState.LEFT_SIDE_RISK,
            OpportunityState.ACCUMULATION_WATCH,
            OpportunityState.CONFIRMATION_WATCH,
            OpportunityState.THESIS_BROKEN,
            OpportunityState.EVIDENCE_BUILDING,
        }
    ),
    OpportunityState.LEFT_SIDE_RISK: frozenset(
        {
            OpportunityState.ACCUMULATION_WATCH,
            OpportunityState.CONFIRMATION_WATCH,
            OpportunityState.THESIS_BROKEN,
            OpportunityState.LEFT_SIDE_RISK,
        }
    ),
    OpportunityState.ACCUMULATION_WATCH: frozenset(
        {
            OpportunityState.CONFIRMATION_WATCH,
            OpportunityState.BUYING_RANGE,
            OpportunityState.LEFT_SIDE_RISK,
            OpportunityState.THESIS_BROKEN,
            OpportunityState.ACCUMULATION_WATCH,
        }
    ),
    OpportunityState.CONFIRMATION_WATCH: frozenset(
        {
            OpportunityState.BUYING_RANGE,
            OpportunityState.LEFT_SIDE_RISK,
            OpportunityState.THESIS_BROKEN,
            OpportunityState.CONFIRMATION_WATCH,
        }
    ),
    OpportunityState.BUYING_RANGE: frozenset(
        {
            OpportunityState.ADD_ON_SETUP,
            OpportunityState.LET_WINNER_RUN,
            OpportunityState.TRIM_OPTIONAL,
            OpportunityState.CROWDED_FROTHY,
            OpportunityState.EXIT_RISK,
            OpportunityState.THESIS_BROKEN,
            OpportunityState.BUYING_RANGE,
        }
    ),
    OpportunityState.ADD_ON_SETUP: frozenset(
        {
            OpportunityState.LET_WINNER_RUN,
            OpportunityState.TRIM_OPTIONAL,
            OpportunityState.CROWDED_FROTHY,
            OpportunityState.EXIT_RISK,
            OpportunityState.THESIS_BROKEN,
            OpportunityState.ADD_ON_SETUP,
        }
    ),
    OpportunityState.LET_WINNER_RUN: frozenset(
        {
            OpportunityState.ADD_ON_SETUP,
            OpportunityState.TRIM_OPTIONAL,
            OpportunityState.CROWDED_FROTHY,
            OpportunityState.EXIT_RISK,
            OpportunityState.THESIS_BROKEN,
            OpportunityState.LET_WINNER_RUN,
        }
    ),
    OpportunityState.TRIM_OPTIONAL: frozenset(
        {
            OpportunityState.LET_WINNER_RUN,
            OpportunityState.CROWDED_FROTHY,
            OpportunityState.EXIT_RISK,
            OpportunityState.THESIS_BROKEN,
            OpportunityState.TRIM_OPTIONAL,
        }
    ),
    OpportunityState.CROWDED_FROTHY: frozenset(
        {
            OpportunityState.ADD_ON_SETUP,
            OpportunityState.TRIM_OPTIONAL,
            OpportunityState.EXIT_RISK,
            OpportunityState.THESIS_BROKEN,
            OpportunityState.CROWDED_FROTHY,
        }
    ),
    OpportunityState.EXIT_RISK: frozenset(
        {
            OpportunityState.THESIS_BROKEN,
            OpportunityState.TRIM_OPTIONAL,
            OpportunityState.CONFIRMATION_WATCH,
            OpportunityState.EXIT_RISK,
        }
    ),
    OpportunityState.THESIS_BROKEN: frozenset(
        {
            OpportunityState.IGNORE,
            OpportunityState.THESIS_BROKEN,
        }
    ),
}


def validate_transition(request: TransitionRequest) -> TransitionResult:
    evidence = request.evidence

    if set(request.metadata).intersection(ACTION_FIELD_NAMES):
        return TransitionResult(False, request.current_state, "action, score, and ranking fields are forbidden")

    if not evidence.signals:
        return TransitionResult(False, request.current_state, "transition requires reason codes and source classes")

    if not evidence.reason_codes:
        return TransitionResult(False, request.current_state, "transition requires reason codes")

    if not evidence.source_classes:
        return TransitionResult(False, request.current_state, "transition requires source classification")

    if evidence.thesis_broken:
        return TransitionResult(True, OpportunityState.THESIS_BROKEN, "thesis broken overrides behavior strength")

    if request.requested_state not in ALLOWED_TRANSITIONS[request.current_state]:
        return TransitionResult(False, request.current_state, "requested state jump is forbidden")

    if (
        request.current_state == OpportunityState.THESIS_CANDIDATE
        and request.requested_state == OpportunityState.BUYING_RANGE
    ):
        return TransitionResult(False, request.current_state, "candidate cannot jump directly to buying range")

    if (
        request.current_state == OpportunityState.LEFT_SIDE_RISK
        and request.requested_state == OpportunityState.BUYING_RANGE
    ):
        return TransitionResult(
            False,
            request.current_state,
            "left side risk must pass accumulation or confirmation watch before buying range",
        )

    if (
        request.current_state == OpportunityState.LET_WINNER_RUN
        and request.requested_state == OpportunityState.EXIT_RISK
        and not evidence.deterioration_evidence
        and ReasonCode.RISK_INVALIDATION not in evidence.reason_codes
    ):
        return TransitionResult(False, request.current_state, "exit risk requires deterioration evidence")

    if (
        request.current_state == OpportunityState.CROWDED_FROTHY
        and request.requested_state == OpportunityState.ADD_ON_SETUP
        and not evidence.risk_approval
    ):
        return TransitionResult(False, request.current_state, "crowded frothy blocks add-on setup without risk approval")

    if (
        request.requested_state == OpportunityState.BUYING_RANGE
        and evidence.all_sources_are(SourceObservationClass.ESTIMATED)
    ):
        return TransitionResult(False, request.current_state, "estimated signals cannot alone create buying range")

    if (
        request.requested_state == OpportunityState.LET_WINNER_RUN
        and evidence.all_sources_are(SourceObservationClass.INFERRED)
    ):
        return TransitionResult(False, request.current_state, "inferred signals cannot alone create let winner run")

    return TransitionResult(True, request.requested_state, "transition allowed for definition-only state machine")
