"""Typed identity admission and bounded in-memory governance for PIT Slice 1."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import TypeAlias

from core.gv_fs0_canonical import (
    canonical_document_bytes,
    canonical_timestamp,
    domain_hash,
)
from core.gv_pit.contracts import (
    AUTHORITATIVE_PORTFOLIO_EVENT_TYPES,
    NON_AUTHORITATIVE_PORTFOLIO_EVENT_TYPES,
    CapitalProposal,
    CashBaselineExtensionV1,
    CashBucketAmount,
    InstrumentUnit,
    NoMarketValidationFacts,
    PointInTimeIdentity,
    build_no_market_identity,
    canonical_contract_bytes,
    canonical_value,
    decode_certified_source_prefix_proof,
    validate_capital_proposal,
    validate_no_market_facts,
    validate_portfolio_source_event,
)
from gv_portfolio_v0.prospective import (
    ProspectiveOperationError,
    validate_prospective_workspace,
)
from gv_portfolio_v0.replay import (
    ReplayError,
    certify_replay_prefix,
    reconstruct_book,
)


EVENT_ID_DOMAIN = "GV-PIT:GOVERNANCE-EVENT-ID:V1"
EVENT_DIGEST_DOMAIN = "GV-PIT:GOVERNANCE-EVENT-DIGEST:V1"
EPISODE_ID_DOMAIN = "GV-PIT:DECISION-EPISODE:V1"
RECORD_ID_DOMAIN = "GV-PIT:PROPOSAL-RECORD:V1"
GOVERNANCE_EVENT_SCHEMA_VERSION = "1.0.0"
GENESIS_DIGEST = "GENESIS"
MAX_GOVERNANCE_EVENTS = 1_024
MAX_GOVERNANCE_EVENT_BYTES = 1_000_000


class PitGovernanceError(ValueError):
    """Fail-closed governance error."""


@dataclass(frozen=True, slots=True)
class OpenDecisionEpisodeCommand:
    episode_id: str
    pit_identity: PointInTimeIdentity
    no_market_facts: NoMarketValidationFacts
    proposal_set: tuple[CapitalProposal, ...]
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
    proposal_set: tuple[CapitalProposal, ...]
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


def validate_governance_event_stream(
    events: tuple[GovernanceEventEnvelope, ...],
    *,
    allow_empty: bool = False,
) -> None:
    if not events:
        if allow_empty:
            return
        raise PitGovernanceError("GOVERNANCE_EVENT_STREAM_REQUIRED")
    if len(events) > MAX_GOVERNANCE_EVENTS:
        raise PitGovernanceError("GOVERNANCE_EVENT_COUNT_OUT_OF_BOUNDS")
    stream_id = events[0].stream_id
    if not stream_id:
        raise PitGovernanceError("GOVERNANCE_STREAM_ID_REQUIRED")
    expected_previous = GENESIS_DIGEST
    seen_ids: set[str] = set()
    prior_timestamp: str | None = None
    for expected_sequence, event in enumerate(events):
        if len(canonical_contract_bytes(event)) > MAX_GOVERNANCE_EVENT_BYTES:
            raise PitGovernanceError("GOVERNANCE_EVENT_SIZE_OUT_OF_BOUNDS")
        if event.stream_id != stream_id:
            raise PitGovernanceError("GOVERNANCE_READ_STREAM_ID_MISMATCH")
        if isinstance(event.sequence_number, bool) or not isinstance(
            event.sequence_number, int
        ):
            raise PitGovernanceError("GOVERNANCE_SEQUENCE_TYPE_INVALID")
        if event.sequence_number != expected_sequence:
            raise PitGovernanceError("GOVERNANCE_READ_SEQUENCE_INVALID")
        if event.event_id in seen_ids:
            raise PitGovernanceError("GOVERNANCE_READ_DUPLICATE_EVENT_ID")
        if event.previous_event_digest != expected_previous:
            raise PitGovernanceError("GOVERNANCE_READ_DIGEST_CHAIN_INVALID")
        if event.event_type != _payload_event_type(event.payload):
            raise PitGovernanceError("GOVERNANCE_READ_EVENT_TYPE_INVALID")
        if event.event_schema_version != GOVERNANCE_EVENT_SCHEMA_VERSION:
            raise PitGovernanceError("GOVERNANCE_EVENT_SCHEMA_VERSION_INVALID")
        if not event.correlation_id or not event.causation_id:
            raise PitGovernanceError("GOVERNANCE_EVENT_LINEAGE_REQUIRED")
        try:
            normalized_timestamp = canonical_timestamp(event.timestamp_utc)
        except ValueError as exc:
            raise PitGovernanceError("GOVERNANCE_EVENT_TIMESTAMP_INVALID") from exc
        if normalized_timestamp != event.timestamp_utc:
            raise PitGovernanceError("GOVERNANCE_EVENT_TIMESTAMP_NOT_CANONICAL")
        if prior_timestamp is not None and event.timestamp_utc < prior_timestamp:
            raise PitGovernanceError("GOVERNANCE_EVENT_TIMESTAMP_REGRESSION")
        if event.event_id != _expected_event_id(event):
            raise PitGovernanceError("GOVERNANCE_READ_EVENT_ID_INVALID")
        if event.event_digest != _expected_event_digest(event):
            raise PitGovernanceError("GOVERNANCE_READ_EVENT_DIGEST_INVALID")
        seen_ids.add(event.event_id)
        expected_previous = event.event_digest
        prior_timestamp = event.timestamp_utc


class InMemoryGovernanceStream:
    """Bounded append/read stream with no durable persistence side effects."""

    def __init__(self, stream_id: str) -> None:
        if not stream_id:
            raise PitGovernanceError("GOVERNANCE_STREAM_ID_REQUIRED")
        self._stream_id = stream_id
        self._events: list[GovernanceEventEnvelope] = []
        self._event_bytes_by_id: dict[str, bytes] = {}
        self._last_timestamp_utc: str | None = None

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
            event_schema_version=GOVERNANCE_EVENT_SCHEMA_VERSION,
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
        event_bytes = canonical_contract_bytes(event)
        if len(event_bytes) > MAX_GOVERNANCE_EVENT_BYTES:
            raise PitGovernanceError("GOVERNANCE_EVENT_SIZE_OUT_OF_BOUNDS")

        existing_bytes = self._event_bytes_by_id.get(event.event_id)
        if existing_bytes is not None:
            if existing_bytes == event_bytes:
                raise PitGovernanceError("GOVERNANCE_DUPLICATE_EVENT_ID")
            raise PitGovernanceError("GOVERNANCE_CONFLICTING_IDEMPOTENT_REPLAY")

        expected_sequence = len(self._events)
        if expected_sequence >= MAX_GOVERNANCE_EVENTS:
            raise PitGovernanceError("GOVERNANCE_EVENT_COUNT_OUT_OF_BOUNDS")
        if isinstance(event.sequence_number, bool) or not isinstance(
            event.sequence_number, int
        ):
            raise PitGovernanceError("GOVERNANCE_SEQUENCE_TYPE_INVALID")
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
        if event.event_schema_version != GOVERNANCE_EVENT_SCHEMA_VERSION:
            raise PitGovernanceError("GOVERNANCE_EVENT_SCHEMA_VERSION_INVALID")
        if not isinstance(event.correlation_id, str) or not event.correlation_id:
            raise PitGovernanceError("GOVERNANCE_EVENT_CORRELATION_REQUIRED")
        if not isinstance(event.causation_id, str) or not event.causation_id:
            raise PitGovernanceError("GOVERNANCE_EVENT_CAUSATION_REQUIRED")
        try:
            normalized_timestamp = canonical_timestamp(event.timestamp_utc)
        except (TypeError, ValueError) as exc:
            raise PitGovernanceError("GOVERNANCE_EVENT_TIMESTAMP_INVALID") from exc
        if normalized_timestamp != event.timestamp_utc:
            raise PitGovernanceError("GOVERNANCE_EVENT_TIMESTAMP_NOT_CANONICAL")
        if (
            self._last_timestamp_utc is not None
            and event.timestamp_utc < self._last_timestamp_utc
        ):
            raise PitGovernanceError("GOVERNANCE_EVENT_TIMESTAMP_REGRESSION")
        if event.event_id != _expected_event_id(event):
            raise PitGovernanceError("GOVERNANCE_EVENT_ID_MISMATCH")
        if event.event_digest != _expected_event_digest(event):
            raise PitGovernanceError("GOVERNANCE_EVENT_DIGEST_MISMATCH")

        self._events.append(event)
        self._event_bytes_by_id[event.event_id] = event_bytes
        self._last_timestamp_utc = event.timestamp_utc
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
        return tuple(self._events)


def _validated_source_head(
    certified_prefix: list[dict[str, object]],
) -> dict[str, object]:
    allowed_types = (
        AUTHORITATIVE_PORTFOLIO_EVENT_TYPES
        | NON_AUTHORITATIVE_PORTFOLIO_EVENT_TYPES
    )
    authoritative_head: dict[str, object] | None = None
    for row in certified_prefix:
        event_type = row.get("event_type")
        if event_type not in allowed_types:
            raise PitGovernanceError("NO_MARKET_SOURCE_EVENT_TYPE_UNRECOGNIZED")
        try:
            validate_portfolio_source_event(row)
        except (TypeError, ValueError) as exc:
            raise PitGovernanceError("NO_MARKET_SOURCE_EVENT_INVALID") from exc
        if event_type in AUTHORITATIVE_PORTFOLIO_EVENT_TYPES:
            authoritative_head = row
    if authoritative_head is None:
        raise PitGovernanceError("NO_MARKET_SOURCE_AUTHORITATIVE_HEAD_REQUIRED")
    return authoritative_head


def _verify_no_market_source_proof(
    facts: NoMarketValidationFacts,
) -> dict[str, object]:
    try:
        source_workspace, certified_prefix, certification, prior_certification = (
            decode_certified_source_prefix_proof(facts.source_proof)
        )
        validate_prospective_workspace(source_workspace)
    except (TypeError, ValueError, ProspectiveOperationError) as exc:
        raise PitGovernanceError(f"NO_MARKET_SOURCE_WORKSPACE_INVALID:{exc}") from exc

    workspace_certification = source_workspace.get("certification")
    if not isinstance(workspace_certification, dict) or canonical_document_bytes(
        workspace_certification
    ) != canonical_document_bytes(certification):
        raise PitGovernanceError("NO_MARKET_SOURCE_WORKSPACE_CERTIFICATION_MISMATCH")
    workspace_events = source_workspace.get("events")
    if not isinstance(workspace_events, list):
        raise PitGovernanceError("NO_MARKET_SOURCE_WORKSPACE_EVENTS_REQUIRED")
    active_certification_id = certification.get("certification_id")
    markers = [
        row
        for row in workspace_events
        if isinstance(row, dict)
        and row.get("event_type") == "CERTIFICATION_RECORDED"
        and row.get("source_identity") == active_certification_id
    ]
    if len(markers) != 1:
        raise PitGovernanceError("NO_MARKET_SOURCE_ACTIVE_CERTIFICATION_MARKER_REQUIRED")
    marker_sequence = markers[0].get("sequence")
    if (
        isinstance(marker_sequence, bool)
        or not isinstance(marker_sequence, int)
        or marker_sequence <= 0
        or marker_sequence >= len(workspace_events)
        or workspace_events[marker_sequence] is not markers[0]
    ):
        raise PitGovernanceError("NO_MARKET_SOURCE_CERTIFICATION_MARKER_ORDER_INVALID")
    workspace_prefix = workspace_events[:marker_sequence]
    if canonical_document_bytes(workspace_prefix) != canonical_document_bytes(
        certified_prefix
    ):
        raise PitGovernanceError("NO_MARKET_SOURCE_WORKSPACE_PREFIX_MISMATCH")
    prior_id = certification.get("prior_certification_id")
    if prior_id is None:
        if prior_certification is not None:
            raise PitGovernanceError("NO_MARKET_SOURCE_UNEXPECTED_PRIOR_CERTIFICATION")
    else:
        history = source_workspace.get("certification_history")
        if not isinstance(history, list):
            raise PitGovernanceError("NO_MARKET_SOURCE_CERTIFICATION_HISTORY_REQUIRED")
        matching_prior = [
            row
            for row in history
            if isinstance(row, dict) and row.get("certification_id") == prior_id
        ]
        if len(matching_prior) != 1 or prior_certification is None:
            raise PitGovernanceError("NO_MARKET_SOURCE_PRIOR_CERTIFICATION_REQUIRED")
        if canonical_document_bytes(matching_prior[0]) != canonical_document_bytes(
            prior_certification
        ):
            raise PitGovernanceError("NO_MARKET_SOURCE_PRIOR_CERTIFICATION_MISMATCH")

    source_head = _validated_source_head(certified_prefix)
    if certification.get("decision_snapshot_id") != facts.source_proof.decision_snapshot_id:
        raise PitGovernanceError("NO_MARKET_SOURCE_DECISION_SNAPSHOT_MISMATCH")
    if certification.get("portfolio_aim_id") != facts.source_proof.portfolio_aim_id:
        raise PitGovernanceError("NO_MARKET_SOURCE_PORTFOLIO_AIM_MISMATCH")
    try:
        expected_certification = certify_replay_prefix(
            certified_prefix,
            decision_snapshot_id=facts.source_proof.decision_snapshot_id,
            portfolio_aim_id=facts.source_proof.portfolio_aim_id,
            prior_certification=prior_certification,
        )
        book = reconstruct_book(certified_prefix)
    except ReplayError as exc:
        raise PitGovernanceError(f"NO_MARKET_SOURCE_REPLAY_INVALID:{exc}") from exc
    if canonical_document_bytes(expected_certification) != canonical_document_bytes(
        certification
    ):
        raise PitGovernanceError("NO_MARKET_SOURCE_CERTIFICATION_MISMATCH")
    if certification.get("terminal_book_hash") != book.get("book_hash"):
        raise PitGovernanceError("NO_MARKET_SOURCE_CERTIFIED_BOOK_HASH_MISMATCH")
    workspace_book = source_workspace.get("book")
    if not isinstance(workspace_book, dict) or canonical_document_bytes(
        workspace_book
    ) != canonical_document_bytes(book):
        raise PitGovernanceError("NO_MARKET_SOURCE_WORKSPACE_BOOK_MISMATCH")
    source_orders = source_workspace.get("orders")
    source_fills = source_workspace.get("fills")
    if not isinstance(source_orders, list) or not isinstance(source_fills, list):
        raise PitGovernanceError("NO_MARKET_SOURCE_ORDER_FILL_LISTS_REQUIRED")

    derived = {
        "certified_book_id": str(certification.get("terminal_book_hash") or ""),
        "certified_book_head_event_id": str(source_head.get("event_id") or ""),
        "certified_book_head_timestamp_utc": str(
            source_head.get("effective_at") or ""
        ),
        "certified_book_hash": str(book.get("book_hash") or ""),
        "positions_count": len(book.get("positions") or []),
        "orders_count": len(source_orders),
        "fills_count": len(source_fills),
        "unexplained_residual": Decimal(str(book.get("unexplained_residual"))),
    }
    for field_name, expected_value in derived.items():
        if getattr(facts, field_name) != expected_value:
            raise PitGovernanceError(
                f"NO_MARKET_SOURCE_{field_name.upper()}_MISMATCH"
            )
    return book


def validate_no_market_identity(
    identity: PointInTimeIdentity,
    facts: NoMarketValidationFacts,
) -> dict[str, object]:
    try:
        validate_no_market_facts(facts)
        expected = build_no_market_identity(facts)
    except (TypeError, ValueError) as exc:
        raise PitGovernanceError(str(exc)) from exc
    book = _verify_no_market_source_proof(facts)
    candidate = identity.market_snapshot_id
    if candidate != expected:
        raise PitGovernanceError("NO_MARKET_VALIDATION_DIGEST_MISMATCH")
    if candidate.kind != "NO_MARKET_DEPENDENCY_CASH_ONLY_V1":
        raise PitGovernanceError("NO_MARKET_KIND_INVALID")
    if identity.as_of_utc != facts.certified_book_head_timestamp_utc:
        raise PitGovernanceError("PIT_AS_OF_NOT_CERTIFIED_HEAD_TIMESTAMP")
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
    return book


def _validate_opening_proposal_set(opening: DecisionEpisodeOpened) -> None:
    proposals = opening.proposal_set
    if not isinstance(proposals, tuple) or not proposals:
        raise PitGovernanceError("PIT_OPENING_PROPOSAL_SET_REQUIRED")
    if not all(isinstance(proposal, CapitalProposal) for proposal in proposals):
        raise PitGovernanceError("PIT_OPENING_PROPOSAL_SET_TYPE_INVALID")
    proposal_ids = tuple(proposal.proposal_id for proposal in proposals)
    if len(set(proposal_ids)) != len(proposal_ids):
        raise PitGovernanceError("PIT_OPENING_DUPLICATE_PROPOSAL_ID")

    target_quantities: list[Decimal] = []
    consumes_notional = False
    consumes_weight = False
    consumes_price = False
    claims_yield = False
    claims_market_return = False
    for proposal in proposals:
        try:
            validate_capital_proposal(proposal)
        except (TypeError, ValueError) as exc:
            raise PitGovernanceError(str(exc)) from exc
        if proposal.pit_identity != opening.pit_identity:
            raise PitGovernanceError("PIT_OPENING_PROPOSAL_IDENTITY_MISMATCH")
        validate_proposal_under_no_market(proposal)
        for target in proposal.targets:
            target_quantities.append(target.target_value)
            consumes_notional = consumes_notional or (
                target.unit is InstrumentUnit.NOTIONAL
            )
            consumes_weight = consumes_weight or (
                target.unit is InstrumentUnit.WEIGHT
            )
            consumes_price = consumes_price or (
                target.normalization.price_identity is not None
            )
        if isinstance(proposal.extension, CashBaselineExtensionV1):
            claims_yield = claims_yield or (
                proposal.extension.payload.yield_status
                != "UNAVAILABLE_NO_ADMITTED_SOURCE"
            )
            market_return_declarations = tuple(
                boundary.strip().lower()
                for boundary in proposal.quantitative_boundaries
                if boundary.strip().lower().startswith("market_return_claim=")
            )
            if market_return_declarations != ("market_return_claim=false",):
                raise PitGovernanceError(
                    "NO_MARKET_CASH_RETURN_CLAIM_DECLARATION_INVALID"
                )
            claims_market_return = claims_market_return or any(
                declaration == "market_return_claim=true"
                for declaration in market_return_declarations
            )

    facts = opening.no_market_facts
    derived = {
        "proposal_target_quantities": tuple(target_quantities),
        "consumes_notional_conversion": consumes_notional,
        "consumes_weight_conversion": consumes_weight,
        "consumes_price_data": consumes_price,
        "consumes_reference_price": consumes_price,
        "claims_yield": claims_yield,
        "claims_market_return": claims_market_return,
    }
    for field_name, expected_value in derived.items():
        if getattr(facts, field_name) != expected_value:
            raise PitGovernanceError(
                f"NO_MARKET_PROPOSAL_SET_{field_name.upper()}_MISMATCH"
            )


def validate_decision_episode_opened(opening: DecisionEpisodeOpened) -> None:
    if not opening.episode_id:
        raise PitGovernanceError("DECISION_EPISODE_ID_REQUIRED")
    book = validate_no_market_identity(opening.pit_identity, opening.no_market_facts)
    _validate_opening_proposal_set(opening)
    if not isinstance(opening.certified_nav, Decimal):
        raise PitGovernanceError("PIT_CERTIFIED_NAV_TYPE_INVALID")
    if not opening.certified_nav.is_finite() or opening.certified_nav < Decimal("0"):
        raise PitGovernanceError("PIT_CERTIFIED_NAV_NONNEGATIVE_FINITE_REQUIRED")
    if not isinstance(opening.classified_cash, tuple) or not all(
        isinstance(row, CashBucketAmount) for row in opening.classified_cash
    ):
        raise PitGovernanceError("PIT_CLASSIFIED_CASH_TYPE_INVALID")
    buckets = tuple(row.bucket for row in opening.classified_cash)
    if len(set(buckets)) != len(buckets):
        raise PitGovernanceError("PIT_DUPLICATE_CLASSIFIED_CASH_BUCKET")
    classified_total = sum(
        (row.amount for row in opening.classified_cash), start=Decimal("0")
    )
    if classified_total != opening.certified_nav:
        raise PitGovernanceError("PIT_CLASSIFIED_CASH_NAV_MISMATCH")

    expected_nav = Decimal(str(book.get("nav")))
    expected_cash = tuple(
        CashBucketAmount(
            bucket=str(row.get("bucket") or ""),
            amount=Decimal(str(row.get("amount"))),
        )
        for row in book.get("classified_cash") or []
        if isinstance(row, dict)
    )
    if opening.certified_nav != expected_nav:
        raise PitGovernanceError("PIT_CERTIFIED_NAV_SOURCE_PROOF_MISMATCH")
    if opening.classified_cash != expected_cash:
        raise PitGovernanceError("PIT_CLASSIFIED_CASH_SOURCE_PROOF_MISMATCH")


def validate_proposal_under_no_market(proposal: CapitalProposal) -> None:
    if proposal.risk_targets:
        raise PitGovernanceError("NO_MARKET_RISK_TARGET_REQUIRES_MARKET_CONTEXT")
    for target in proposal.targets:
        if target.unit is not InstrumentUnit.QUANTITY:
            raise PitGovernanceError("NO_MARKET_REAL_SNAPSHOT_REQUIRED_FOR_CONVERSION")
        if target.target_value != Decimal("0"):
            raise PitGovernanceError("NO_MARKET_REAL_SNAPSHOT_REQUIRED_FOR_TARGET")
        if target.normalization.price_identity is not None:
            raise PitGovernanceError("NO_MARKET_PRICE_IDENTITY_PROHIBITED")
        if target.normalization.contract_multiplier is not None:
            raise PitGovernanceError("NO_MARKET_CONTRACT_MULTIPLIER_PROHIBITED")
    if isinstance(proposal.extension, CashBaselineExtensionV1) and (
        proposal.extension.payload.yield_status
        != "UNAVAILABLE_NO_ADMITTED_SOURCE"
    ):
        raise PitGovernanceError("NO_MARKET_CASH_YIELD_STATUS_INVALID")


def expected_proposal_record_id(*, episode_id: str, proposal_id: str) -> str:
    if not episode_id or not proposal_id:
        raise PitGovernanceError("PROPOSAL_RECORD_IDENTITY_REQUIRED")
    return "REC_" + domain_hash(
        RECORD_ID_DOMAIN,
        {"episode_id": episode_id, "proposal_id": proposal_id},
    )


def open_decision_episode(
    stream: InMemoryGovernanceStream,
    command: OpenDecisionEpisodeCommand,
    *,
    timestamp_utc: str,
) -> GovernanceEventEnvelope:
    if stream.read():
        raise PitGovernanceError("DECISION_EPISODE_ALREADY_OPEN")
    opening = DecisionEpisodeOpened(
        episode_id=command.episode_id,
        pit_identity=command.pit_identity,
        no_market_facts=command.no_market_facts,
        proposal_set=command.proposal_set,
        certified_nav=command.certified_nav,
        classified_cash=command.classified_cash,
    )
    validate_decision_episode_opened(opening)
    return stream.append_payload(
        opening,
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
    identity_matches = command.proposal.pit_identity == episode.pit_identity
    if identity_matches:
        validate_proposal_under_no_market(command.proposal)
        admitted = next(
            (
                proposal
                for proposal in episode.proposal_set
                if proposal.proposal_id == command.proposal.proposal_id
            ),
            None,
        )
        if admitted is None:
            raise PitGovernanceError("PIT_PROPOSAL_NOT_IN_OPENING_SET")
        if canonical_contract_bytes(admitted) != canonical_contract_bytes(
            command.proposal
        ):
            raise PitGovernanceError("PIT_OPENING_PROPOSAL_BYTES_MISMATCH")

    record_id = expected_proposal_record_id(
        episode_id=command.episode_id,
        proposal_id=command.proposal.proposal_id,
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
    if identity_matches:
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
            proposal_set=bundle.proposals,
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
