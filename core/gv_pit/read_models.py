"""Pure deterministic read projections for PIT Slice 1 governance facts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.gv_pit.contracts import (
    CashBucketAmount,
    PointInTimeIdentity,
    canonical_contract_bytes,
)
from core.gv_pit.governance import (
    DecisionEpisodeOpened,
    GovernanceEventEnvelope,
    ProposalAccepted,
    ProposalIdentityRejected,
)


class PitProjectionError(ValueError):
    """Fail-closed projector error."""


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
    event_count: int
    terminal_event_digest: str
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


def project_decision_episode(
    events: tuple[GovernanceEventEnvelope, ...],
) -> DecisionEpisodeReadModel:
    """Fold one valid ordered stream into a byte-stable read model."""

    if not events:
        raise PitProjectionError("PIT_EVENT_STREAM_EMPTY")
    for expected_sequence, event in enumerate(events):
        if event.sequence_number != expected_sequence:
            raise PitProjectionError("PIT_EVENT_SEQUENCE_INVALID")
        if expected_sequence and (
            event.previous_event_digest != events[expected_sequence - 1].event_digest
        ):
            raise PitProjectionError("PIT_EVENT_DIGEST_LINK_INVALID")

    opened = [event for event in events if isinstance(event.payload, DecisionEpisodeOpened)]
    if len(opened) != 1:
        raise PitProjectionError("PIT_EPISODE_OPEN_FACT_REQUIRED")
    opening = opened[0].payload

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
        event_count=len(events),
        terminal_event_digest=events[-1].event_digest,
        replay_status="DETERMINISTIC_IN_MEMORY_VERIFIED",
    )
    canonical_contract_bytes(model)
    return model
