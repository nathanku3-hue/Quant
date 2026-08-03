"""Typed identity admission and bounded in-memory governance for PIT Slice 1."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import TypeAlias

from core.gv_fs0_canonical import domain_hash
from core.gv_pit.contracts import (
    CapitalProposal,
    CashBucketAmount,
    InstrumentUnit,
    NoMarketValidationFacts,
    PointInTimeIdentity,
    build_no_market_identity,
    canonical_contract_bytes,
    canonical_value,
    validate_capital_proposal,
)


EVENT_ID_DOMAIN = "GV-PIT:GOVERNANCE-EVENT-ID:V1"
EVENT_DIGEST_DOMAIN = "GV-PIT:GOVERNANCE-EVENT-DIGEST:V1"
EPISODE_ID_DOMAIN = "GV-PIT:DECISION-EPISODE:V1"
RECORD_ID_DOMAIN = "GV-PIT:PROPOSAL-RECORD:V1"
GENESIS_DIGEST = "GENESIS"


class PitGovernanceError(ValueError):
    """Fail-closed governance error."""


@dataclass(frozen=True, slots=True)
class OpenDecisionEpisodeCommand:
    episode_id: str
    pit_identity: PointInTimeIdentity
    no_market_facts: NoMarketValidationFacts
    certified_nav: Decimal
    classified_cash: tuple[CashBucketAmount, ...]


@dataclass(frozen=True, slots=True)
class SubmitProposalCommand:
    episode_id: str
    proposal: CapitalProposal


@dataclass(frozen=True, slots=True)
class DecisionEpisodeOpened:
    episode_id: str
    pit_identity: PointInTimeIdentity
    no_market_facts: NoMarketValidationFacts
    certified_nav: Decimal
    classified_cash: tuple[CashBucketAmount, ...]


@dataclass(frozen=True, slots=True)
class ProposalSubmitted:
    episode_id: str
    record_id: str
    proposal: CapitalProposal


@dataclass(frozen=True, slots=True)
class ProposalAccepted:
    episode_id: str
    record_id: str
    proposal: CapitalProposal


@dataclass(frozen=True, slots=True)
class ProposalIdentityRejected:
    episode_id: str
    record_id: str
    proposal: CapitalProposal
    expected_identity: PointInTimeIdentity
    received_identity: PointInTimeIdentity


GovernancePayload: TypeAlias = (
    DecisionEpisodeOpened
    | ProposalSubmitted
    | ProposalAccepted
    | ProposalIdentityRejected
)


@dataclass(frozen=True, slots=True)
class GovernanceEventEnvelope:
    stream_id: str
    sequence_number: int
    event_id: str
    event_type: str
    event_schema_version: str
    timestamp_utc: str
    correlation_id: str
    causation_id: str
    previous_event_digest: str
    event_digest: str
    payload: GovernancePayload


def _payload_event_type(payload: GovernancePayload) -> str:
    if isinstance(payload, DecisionEpisodeOpened):
        return "DECISION_EPISODE_OPENED"
    if isinstance(payload, ProposalSubmitted):
        return "PROPOSAL_SUBMITTED"
    if isinstance(payload, ProposalAccepted):
        return "PROPOSAL_ACCEPTED"
    if isinstance(payload, ProposalIdentityRejected):
        return "PROPOSAL_IDENTITY_REJECTED"
    raise PitGovernanceError("GOVERNANCE_PAYLOAD_TYPE_INVALID")


def _event_id_body(event: GovernanceEventEnvelope) -> dict[str, object]:
    return {
        "stream_id": event.stream_id,
        "sequence_number": event.sequence_number,
        "event_type": event.event_type,
        "event_schema_version": event.event_schema_version,
        "timestamp_utc": event.timestamp_utc,
        "correlation_id": event.correlation_id,
        "causation_id": event.causation_id,
        "previous_event_digest": event.previous_event_digest,
        "payload": canonical_value(event.payload),
    }


def _event_digest_body(event: GovernanceEventEnvelope) -> dict[str, object]:
    return {**_event_id_body(event), "event_id": event.event_id}


def _expected_event_id(event: GovernanceEventEnvelope) -> str:
    return "GEV_" + domain_hash(EVENT_ID_DOMAIN, _event_id_body(event))


def _expected_event_digest(event: GovernanceEventEnvelope) -> str:
    return domain_hash(EVENT_DIGEST_DOMAIN, _event_digest_body(event))


class InMemoryGovernanceStream:
    """Bounded append/read stream with no durable persistence side effects."""

    def __init__(self, stream_id: str) -> None:
        if not stream_id:
            raise PitGovernanceError("GOVERNANCE_STREAM_ID_REQUIRED")
        self._stream_id = stream_id
        self._events: list[GovernanceEventEnvelope] = []

    @property
    def stream_id(self) -> str:
        return self._stream_id

    def build_event(
        self,
        payload: GovernancePayload,
        *,
        timestamp_utc: str,
        correlation_id: str,
        causation_id: str,
        sequence_number: int | None = None,
        previous_event_digest: str | None = None,
    ) -> GovernanceEventEnvelope:
        sequence = len(self._events) if sequence_number is None else sequence_number
        previous = (
            self._events[-1].event_digest
            if self._events and previous_event_digest is None
            else GENESIS_DIGEST
            if not self._events and previous_event_digest is None
            else str(previous_event_digest)
        )
        draft = GovernanceEventEnvelope(
            stream_id=self._stream_id,
            sequence_number=sequence,
            event_id="",
            event_type=_payload_event_type(payload),
            event_schema_version="1.0.0",
            timestamp_utc=timestamp_utc,
            correlation_id=correlation_id,
            causation_id=causation_id,
            previous_event_digest=previous,
            event_digest="",
            payload=payload,
        )
        identified = replace(draft, event_id=_expected_event_id(draft))
        return replace(identified, event_digest=_expected_event_digest(identified))

    def append(self, event: GovernanceEventEnvelope) -> GovernanceEventEnvelope:
        if event.stream_id != self._stream_id:
            raise PitGovernanceError("GOVERNANCE_STREAM_ID_MISMATCH")

        existing_by_id = next(
            (row for row in self._events if row.event_id == event.event_id), None
        )
        if existing_by_id is not None:
            if canonical_contract_bytes(existing_by_id) == canonical_contract_bytes(event):
                raise PitGovernanceError("GOVERNANCE_DUPLICATE_EVENT_ID")
            raise PitGovernanceError("GOVERNANCE_CONFLICTING_IDEMPOTENT_REPLAY")

        expected_sequence = len(self._events)
        if event.sequence_number < expected_sequence:
            raise PitGovernanceError("GOVERNANCE_DUPLICATE_SEQUENCE_POSITION")
        if event.sequence_number > expected_sequence:
            raise PitGovernanceError("GOVERNANCE_SEQUENCE_GAP")

        expected_previous = (
            self._events[-1].event_digest if self._events else GENESIS_DIGEST
        )
        if event.previous_event_digest != expected_previous:
            raise PitGovernanceError("GOVERNANCE_PREVIOUS_DIGEST_MISMATCH")
        if event.event_type != _payload_event_type(event.payload):
            raise PitGovernanceError("GOVERNANCE_EVENT_TYPE_MISMATCH")
        if event.event_id != _expected_event_id(event):
            raise PitGovernanceError("GOVERNANCE_EVENT_ID_MISMATCH")
        if event.event_digest != _expected_event_digest(event):
            raise PitGovernanceError("GOVERNANCE_EVENT_DIGEST_MISMATCH")

        self._events.append(event)
        return event

    def append_payload(
        self,
        payload: GovernancePayload,
        *,
        timestamp_utc: str,
        correlation_id: str,
        causation_id: str,
    ) -> GovernanceEventEnvelope:
        return self.append(
            self.build_event(
                payload,
                timestamp_utc=timestamp_utc,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
        )

    def read(self) -> tuple[GovernanceEventEnvelope, ...]:
        expected_previous = GENESIS_DIGEST
        seen_ids: set[str] = set()
        for expected_sequence, event in enumerate(self._events):
            if event.sequence_number != expected_sequence:
                raise PitGovernanceError("GOVERNANCE_READ_SEQUENCE_INVALID")
            if event.event_id in seen_ids:
                raise PitGovernanceError("GOVERNANCE_READ_DUPLICATE_EVENT_ID")
            if event.previous_event_digest != expected_previous:
                raise PitGovernanceError("GOVERNANCE_READ_DIGEST_CHAIN_INVALID")
            if event.event_id != _expected_event_id(event):
                raise PitGovernanceError("GOVERNANCE_READ_EVENT_ID_INVALID")
            if event.event_digest != _expected_event_digest(event):
                raise PitGovernanceError("GOVERNANCE_READ_EVENT_DIGEST_INVALID")
            seen_ids.add(event.event_id)
            expected_previous = event.event_digest
        return tuple(self._events)


def validate_no_market_identity(
    identity: PointInTimeIdentity,
    facts: NoMarketValidationFacts,
) -> None:
    candidate = identity.market_snapshot_id
    expected = build_no_market_identity(facts)
    if candidate != expected:
        raise PitGovernanceError("NO_MARKET_VALIDATION_DIGEST_MISMATCH")
    if candidate.kind != "NO_MARKET_DEPENDENCY_CASH_ONLY_V1":
        raise PitGovernanceError("NO_MARKET_KIND_INVALID")
    if (
        identity.certified_book_id != facts.certified_book_id
        or identity.certified_book_head_event_id
        != facts.certified_book_head_event_id
        or candidate.certified_book_id != facts.certified_book_id
        or candidate.certified_book_head_event_id
        != facts.certified_book_head_event_id
        or candidate.certified_book_hash != facts.certified_book_hash
    ):
        raise PitGovernanceError("NO_MARKET_CERTIFIED_BOOK_BINDING_MISMATCH")
    if facts.positions_count != 0:
        raise PitGovernanceError("NO_MARKET_POSITIONS_NOT_EMPTY")
    if facts.orders_count != 0:
        raise PitGovernanceError("NO_MARKET_ORDERS_NOT_EMPTY")
    if facts.fills_count != 0:
        raise PitGovernanceError("NO_MARKET_FILLS_NOT_EMPTY")
    if facts.unexplained_residual != Decimal("0"):
        raise PitGovernanceError("NO_MARKET_RESIDUAL_NONZERO")
    if any(quantity != Decimal("0") for quantity in facts.proposal_target_quantities):
        raise PitGovernanceError("NO_MARKET_TARGET_QUANTITY_NONZERO")
    if facts.consumes_notional_conversion:
        raise PitGovernanceError("NO_MARKET_NOTIONAL_CONVERSION_PROHIBITED")
    if facts.consumes_weight_conversion:
        raise PitGovernanceError("NO_MARKET_WEIGHT_CONVERSION_PROHIBITED")
    if facts.consumes_price_data:
        raise PitGovernanceError("NO_MARKET_PRICE_CONSUMPTION_PROHIBITED")
    if facts.claims_yield:
        raise PitGovernanceError("NO_MARKET_YIELD_CLAIM_PROHIBITED")
    if facts.claims_market_return:
        raise PitGovernanceError("NO_MARKET_RETURN_CLAIM_PROHIBITED")


def _validate_proposal_under_no_market(proposal: CapitalProposal) -> None:
    for target in proposal.targets:
        if target.unit is not InstrumentUnit.QUANTITY:
            raise PitGovernanceError("NO_MARKET_REAL_SNAPSHOT_REQUIRED_FOR_CONVERSION")
        if target.target_value != Decimal("0"):
            raise PitGovernanceError("NO_MARKET_REAL_SNAPSHOT_REQUIRED_FOR_TARGET")
        if target.normalization.price_identity is not None:
            raise PitGovernanceError("NO_MARKET_PRICE_IDENTITY_PROHIBITED")


def open_decision_episode(
    stream: InMemoryGovernanceStream,
    command: OpenDecisionEpisodeCommand,
    *,
    timestamp_utc: str,
) -> GovernanceEventEnvelope:
    if stream.read():
        raise PitGovernanceError("DECISION_EPISODE_ALREADY_OPEN")
    validate_no_market_identity(command.pit_identity, command.no_market_facts)
    return stream.append_payload(
        DecisionEpisodeOpened(
            episode_id=command.episode_id,
            pit_identity=command.pit_identity,
            no_market_facts=command.no_market_facts,
            certified_nav=command.certified_nav,
            classified_cash=command.classified_cash,
        ),
        timestamp_utc=timestamp_utc,
        correlation_id=command.episode_id,
        causation_id=command.pit_identity.certified_book_head_event_id,
    )


def submit_proposal(
    stream: InMemoryGovernanceStream,
    command: SubmitProposalCommand,
    *,
    submitted_at_utc: str,
    decided_at_utc: str,
) -> GovernanceEventEnvelope:
    events = stream.read()
    opened = [row for row in events if isinstance(row.payload, DecisionEpisodeOpened)]
    if len(opened) != 1:
        raise PitGovernanceError("DECISION_EPISODE_OPEN_REQUIRED")
    episode = opened[0].payload
    if command.episode_id != episode.episode_id:
        raise PitGovernanceError("DECISION_EPISODE_ID_MISMATCH")
    validate_capital_proposal(command.proposal)
    _validate_proposal_under_no_market(command.proposal)

    record_id = "REC_" + domain_hash(
        RECORD_ID_DOMAIN,
        {
            "episode_id": command.episode_id,
            "proposal_id": command.proposal.proposal_id,
        },
    )
    submitted = stream.append_payload(
        ProposalSubmitted(
            episode_id=command.episode_id,
            record_id=record_id,
            proposal=command.proposal,
        ),
        timestamp_utc=submitted_at_utc,
        correlation_id=command.episode_id,
        causation_id=opened[0].event_id,
    )
    if command.proposal.pit_identity == episode.pit_identity:
        payload: GovernancePayload = ProposalAccepted(
            episode_id=command.episode_id,
            record_id=record_id,
            proposal=command.proposal,
        )
    else:
        payload = ProposalIdentityRejected(
            episode_id=command.episode_id,
            record_id=record_id,
            proposal=command.proposal,
            expected_identity=episode.pit_identity,
            received_identity=command.proposal.pit_identity,
        )
    return stream.append_payload(
        payload,
        timestamp_utc=decided_at_utc,
        correlation_id=command.episode_id,
        causation_id=submitted.event_id,
    )


def _timestamp_offset(value: str, seconds: int) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PitGovernanceError("PIT_TIMESTAMP_INVALID") from exc
    if parsed.tzinfo is None:
        raise PitGovernanceError("PIT_TIMESTAMP_UTC_REQUIRED")
    return (parsed.astimezone(timezone.utc) + timedelta(seconds=seconds)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


def govern_real_pit_bundle(bundle: object) -> InMemoryGovernanceStream:
    """Run the deterministic read-only governance transaction for one real bundle."""

    from core.gv_pit.adapters import RealPitSourceBundle

    if not isinstance(bundle, RealPitSourceBundle):
        raise PitGovernanceError("REAL_PIT_SOURCE_BUNDLE_REQUIRED")
    episode_id = "DEP_" + domain_hash(
        EPISODE_ID_DOMAIN, canonical_value(bundle.pit_identity)
    )
    stream = InMemoryGovernanceStream(stream_id=f"PIT-{episode_id}")
    open_decision_episode(
        stream,
        OpenDecisionEpisodeCommand(
            episode_id=episode_id,
            pit_identity=bundle.pit_identity,
            no_market_facts=bundle.no_market_facts,
            certified_nav=bundle.certified_nav,
            classified_cash=bundle.classified_cash,
        ),
        timestamp_utc=_timestamp_offset(bundle.pit_identity.as_of_utc, 1),
    )
    for index, proposal in enumerate(bundle.proposals):
        submit_proposal(
            stream,
            SubmitProposalCommand(episode_id=episode_id, proposal=proposal),
            submitted_at_utc=_timestamp_offset(
                bundle.pit_identity.as_of_utc, 2 + (index * 2)
            ),
            decided_at_utc=_timestamp_offset(
                bundle.pit_identity.as_of_utc, 3 + (index * 2)
            ),
        )
    return stream
