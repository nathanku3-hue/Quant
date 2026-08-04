"""Pure deterministic read projections for PIT Slice 1 governance facts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.gv_pit.contracts import (
    CashBucketAmount,
    EvidenceReference,
    PointInTimeIdentity,
    canonical_contract_bytes,
    validate_capital_proposal,
)
from core.gv_pit.governance import (
    DecisionEpisodeOpened,
    GovernanceEventEnvelope,
    ProposalAccepted,
    ProposalIdentityRejected,
    ProposalSubmitted,
    expected_proposal_record_id,
    validate_decision_episode_opened,
    validate_governance_event_stream,
    validate_proposal_under_no_market,
)


class PitProjectionError(ValueError):
    """Fail-closed projector error."""


@dataclass(frozen=True, slots=True)
class GovernanceEventReadModel:
    sequence_number: int
    event_id: str
    event_type: str
    timestamp_utc: str
    correlation_id: str
    causation_id: str
    previous_event_digest: str
    event_digest: str
    record_id: str | None
    proposal_id: str | None


@dataclass(frozen=True, slots=True)
class ProposalRecordReadModel:
    record_id: str
    proposal_id: str
    module_id: str
    module_version: str
    sleeve_id: str
    outcome: str
    status: str
    target_summary: tuple[str, ...]
    principal_claim: str
    supporting_evidence: tuple[EvidenceReference, ...]
    contradicting_evidence: tuple[EvidenceReference, ...]
    supporting_evidence_ids: tuple[str, ...]
    contradicting_evidence_ids: tuple[str, ...]
    missing_discriminator: str
    reason_not_to_act: str
    extension_schema_id: str
    disposition_event_sequence: int


@dataclass(frozen=True, slots=True)
class DecisionEpisodeReadModel:
    episode_id: str
    pit_identity: PointInTimeIdentity
    status: str
    proposal_records: tuple[ProposalRecordReadModel, ...]
    selected_record_ids: tuple[str, ...]
    certified_nav: Decimal
    classified_cash: tuple[CashBucketAmount, ...]
    disagreement_summary: str
    evidence_gap_summary: tuple[str, ...]
    stream_id: str
    event_count: int
    head_sequence_number: int
    terminal_event_digest: str
    governance_events: tuple[GovernanceEventReadModel, ...]
    replay_status: str


def _target_summary(proposal: object) -> tuple[str, ...]:
    targets = getattr(proposal, "targets", ())
    return tuple(
        " ".join(
            (
                target.symbol,
                target.intent.value,
                target.unit.value,
                format(target.target_value, "f"),
                f"quantum={format(target.normalization.unit_quantum, 'f')}",
                f"rounding={target.normalization.rounding_mode.value}",
                f"currency={target.normalization.currency}",
                f"price={target.normalization.price_identity or 'UNAVAILABLE'}",
                f"multiplier={format(target.normalization.contract_multiplier, 'f') if target.normalization.contract_multiplier is not None else 'UNAVAILABLE'}",
                f"lot={target.normalization.lot_size_policy.value}",
            )
        )
        for target in targets
    )


def _proposal_row(
    event: GovernanceEventEnvelope,
    *,
    status: str,
) -> ProposalRecordReadModel:
    payload = event.payload
    proposal = payload.proposal
    return ProposalRecordReadModel(
        record_id=payload.record_id,
        proposal_id=proposal.proposal_id,
        module_id=proposal.module_id,
        module_version=proposal.module_version,
        sleeve_id=proposal.sleeve_id,
        outcome=proposal.outcome.value,
        status=status,
        target_summary=_target_summary(proposal),
        principal_claim=proposal.principal_claim,
        supporting_evidence=proposal.supporting_evidence,
        contradicting_evidence=proposal.contradicting_evidence,
        supporting_evidence_ids=tuple(
            row.evidence_id for row in proposal.supporting_evidence
        ),
        contradicting_evidence_ids=tuple(
            row.evidence_id for row in proposal.contradicting_evidence
        ),
        missing_discriminator=proposal.missing_discriminator,
        reason_not_to_act=proposal.reason_not_to_act,
        extension_schema_id=proposal.extension.schema_id,
        disposition_event_sequence=event.sequence_number,
    )


def _event_read_model(event: GovernanceEventEnvelope) -> GovernanceEventReadModel:
    payload = event.payload
    proposal = getattr(payload, "proposal", None)
    return GovernanceEventReadModel(
        sequence_number=event.sequence_number,
        event_id=event.event_id,
        event_type=event.event_type,
        timestamp_utc=event.timestamp_utc,
        correlation_id=event.correlation_id,
        causation_id=event.causation_id,
        previous_event_digest=event.previous_event_digest,
        event_digest=event.event_digest,
        record_id=getattr(payload, "record_id", None),
        proposal_id=getattr(proposal, "proposal_id", None),
    )


def _require_same_proposal(left: object, right: object) -> None:
    if canonical_contract_bytes(left) != canonical_contract_bytes(right):
        raise PitProjectionError("PIT_DISPOSITION_PROPOSAL_MISMATCH")


def _validate_semantic_event_grammar(
    events: tuple[GovernanceEventEnvelope, ...],
) -> DecisionEpisodeOpened:
    try:
        validate_governance_event_stream(events)
    except ValueError as exc:
        raise PitProjectionError(str(exc)) from exc

    if not isinstance(events[0].payload, DecisionEpisodeOpened):
        raise PitProjectionError("PIT_EPISODE_OPEN_MUST_BE_FIRST")
    opening_event = events[0]
    opening = opening_event.payload
    try:
        validate_decision_episode_opened(opening)
    except ValueError as exc:
        raise PitProjectionError(str(exc)) from exc
    if opening_event.correlation_id != opening.episode_id:
        raise PitProjectionError("PIT_OPEN_CORRELATION_MISMATCH")
    if opening_event.causation_id != opening.pit_identity.certified_book_head_event_id:
        raise PitProjectionError("PIT_OPEN_CAUSATION_MISMATCH")

    opening_proposals_by_id = {
        proposal.proposal_id: proposal for proposal in opening.proposal_set
    }
    submissions: dict[str, GovernanceEventEnvelope] = {}
    submitted_proposal_ids: set[str] = set()
    disposed_records: set[str] = set()

    for event in events[1:]:
        payload = event.payload
        if isinstance(payload, DecisionEpisodeOpened):
            raise PitProjectionError("PIT_MULTIPLE_EPISODE_OPEN_FACTS")
        if payload.episode_id != opening.episode_id:
            raise PitProjectionError("PIT_EVENT_EPISODE_ID_MISMATCH")
        if event.correlation_id != opening.episode_id:
            raise PitProjectionError("PIT_EVENT_CORRELATION_MISMATCH")

        if isinstance(payload, ProposalSubmitted):
            try:
                validate_capital_proposal(payload.proposal)
            except (TypeError, ValueError) as exc:
                raise PitProjectionError(str(exc)) from exc
            expected_record_id = expected_proposal_record_id(
                episode_id=opening.episode_id,
                proposal_id=payload.proposal.proposal_id,
            )
            if payload.record_id != expected_record_id:
                raise PitProjectionError("PIT_PROPOSAL_RECORD_ID_MISMATCH")
            if event.causation_id != opening_event.event_id:
                raise PitProjectionError("PIT_SUBMISSION_CAUSATION_MISMATCH")
            if payload.proposal.pit_identity == opening.pit_identity:
                try:
                    validate_proposal_under_no_market(payload.proposal)
                except ValueError as exc:
                    raise PitProjectionError(str(exc)) from exc
                admitted = opening_proposals_by_id.get(payload.proposal.proposal_id)
                if admitted is None:
                    raise PitProjectionError("PIT_PROPOSAL_NOT_IN_OPENING_SET")
                if canonical_contract_bytes(admitted) != canonical_contract_bytes(
                    payload.proposal
                ):
                    raise PitProjectionError("PIT_OPENING_PROPOSAL_BYTES_MISMATCH")
            if payload.record_id in submissions:
                raise PitProjectionError("PIT_DUPLICATE_PROPOSAL_RECORD_SUBMISSION")
            if payload.proposal.proposal_id in submitted_proposal_ids:
                raise PitProjectionError("PIT_DUPLICATE_PROPOSAL_SUBMISSION")
            submissions[payload.record_id] = event
            submitted_proposal_ids.add(payload.proposal.proposal_id)
            continue

        if isinstance(payload, (ProposalAccepted, ProposalIdentityRejected)):
            submitted = submissions.get(payload.record_id)
            if submitted is None:
                raise PitProjectionError("PIT_ORPHAN_PROPOSAL_DISPOSITION")
            if payload.record_id in disposed_records:
                raise PitProjectionError("PIT_DUPLICATE_PROPOSAL_DISPOSITION")
            if event.sequence_number != submitted.sequence_number + 1:
                raise PitProjectionError("PIT_DISPOSITION_NOT_ADJACENT_TO_SUBMISSION")
            if event.causation_id != submitted.event_id:
                raise PitProjectionError("PIT_DISPOSITION_CAUSATION_MISMATCH")
            _require_same_proposal(payload.proposal, submitted.payload.proposal)

            if isinstance(payload, ProposalAccepted):
                if payload.proposal.pit_identity != opening.pit_identity:
                    raise PitProjectionError("PIT_ACCEPTED_IDENTITY_MISMATCH")
                try:
                    validate_proposal_under_no_market(payload.proposal)
                except ValueError as exc:
                    raise PitProjectionError(str(exc)) from exc
            else:
                if payload.proposal.pit_identity == opening.pit_identity:
                    raise PitProjectionError("PIT_REJECTED_IDENTITY_MATCHED")
                if payload.expected_identity != opening.pit_identity:
                    raise PitProjectionError("PIT_REJECTION_EXPECTED_IDENTITY_MISMATCH")
                if payload.received_identity != payload.proposal.pit_identity:
                    raise PitProjectionError("PIT_REJECTION_RECEIVED_IDENTITY_MISMATCH")
            disposed_records.add(payload.record_id)
            continue

        raise PitProjectionError("PIT_UNSUPPORTED_GOVERNANCE_FACT")

    if set(submissions) != disposed_records:
        raise PitProjectionError("PIT_UNDISPOSED_PROPOSAL_SUBMISSION")
    return opening


def project_decision_episode(
    events: tuple[GovernanceEventEnvelope, ...],
) -> DecisionEpisodeReadModel:
    """Fold one valid ordered stream into a byte-stable read model."""

    opening = _validate_semantic_event_grammar(events)

    rows: list[ProposalRecordReadModel] = []
    for event in events:
        if isinstance(event.payload, ProposalAccepted):
            rows.append(_proposal_row(event, status="ELIGIBLE"))
        elif isinstance(event.payload, ProposalIdentityRejected):
            rows.append(
                _proposal_row(event, status="REJECTED_IDENTITY_MISMATCH")
            )
    rows.sort(key=lambda row: (row.disposition_event_sequence, row.record_id))

    eligible_by_sleeve: dict[str, set[str]] = {}
    for row in rows:
        if row.status == "ELIGIBLE":
            eligible_by_sleeve.setdefault(row.sleeve_id, set()).add(row.outcome)
    conflicting_sleeves = {
        sleeve: outcomes
        for sleeve, outcomes in eligible_by_sleeve.items()
        if len(outcomes) > 1
    }
    if not rows:
        disagreement = "No proposal dispositions have been projected."
    elif not conflicting_sleeves:
        disagreement = "No material outcome disagreement across comparable sleeves."
    else:
        disagreement = "Eligible modules disagree within sleeves: " + "; ".join(
            f"{sleeve}={','.join(sorted(outcomes))}"
            for sleeve, outcomes in sorted(conflicting_sleeves.items())
        )

    evidence_gaps = tuple(
        sorted(
            {
                row.missing_discriminator
                for row in rows
                if row.missing_discriminator.strip()
            }
        )
    )
    model = DecisionEpisodeReadModel(
        episode_id=opening.episode_id,
        pit_identity=opening.pit_identity,
        status="OPEN",
        proposal_records=tuple(rows),
        selected_record_ids=(),
        certified_nav=opening.certified_nav,
        classified_cash=opening.classified_cash,
        disagreement_summary=disagreement,
        evidence_gap_summary=evidence_gaps,
        stream_id=events[0].stream_id,
        event_count=len(events),
        head_sequence_number=events[-1].sequence_number,
        terminal_event_digest=events[-1].event_digest,
        governance_events=tuple(_event_read_model(event) for event in events),
        replay_status="DETERMINISTIC_IN_MEMORY_VERIFIED",
    )
    canonical_contract_bytes(model)
    return model
