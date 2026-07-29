"""Custody-owned immutable event stream for GV Portfolio V0.

The event envelope is frozen; event payloads remain owned by their producing
streams except for the exercised corporate-action fields validated here. A
CanonicalEventStream stores canonical bytes, returns defensive copies, and can
only advance by returning a new stream whose prefix is byte-identical.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

from contracts.gv_portfolio.v0.identity import (
    CustodyContractError,
    identifier,
    verify_record_id,
)
from core.gv_fs0_canonical import (
    CanonicalizationError,
    canonical_decimal,
    canonical_document_bytes,
    canonical_timestamp,
    parse_canonical_document_bytes,
    prepare_identity_string,
)

EVENT_STREAM_SCHEMA_VERSION = "gv_portfolio_event_stream_v0"
EVENT_ENVELOPE_FIELDS = frozenset(
    {
        "event_id",
        "sequence",
        "event_type",
        "effective_at",
        "source_identity",
        "instrument_id",
        "cash_bucket",
        "payload",
    }
)
EXERCISED_EVENT_TYPES = frozenset(
    {
        "CASH_OPENING",
        "POSITION_OPENING",
        "CORPORATE_ACTION_SPLIT",
        "PORTFOLIO_AIM_CONFIRMED",
        "ORDER_CREATED",
        "FILL_COMPLETED",
        "LATER_OBSERVATION_ADMITTED",
        "CERTIFICATION_RECORDED",
    }
)


class CustodyEventError(CustodyContractError):
    """Raised when canonical event custody validation fails closed."""


def _identity_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise CustodyEventError(f"{field.upper()}_REQUIRED")
    try:
        return prepare_identity_string(value)
    except CanonicalizationError as exc:
        raise CustodyEventError(f"{field.upper()}_INVALID:{exc}") from exc


def _optional_identity_text(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    return _identity_text(value, field=field)


def _effective_at(value: Any) -> str:
    if not isinstance(value, str):
        raise CustodyEventError("EFFECTIVE_AT_REQUIRED")
    try:
        normalized = canonical_timestamp(value)
    except CanonicalizationError as exc:
        raise CustodyEventError(f"EFFECTIVE_AT_INVALID:{exc}") from exc
    if normalized != value:
        raise CustodyEventError("EFFECTIVE_AT_NOT_CANONICAL")
    return normalized


def _canonical_mapping(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise CustodyEventError(f"{field.upper()}_MAPPING_REQUIRED")
    try:
        parsed = parse_canonical_document_bytes(canonical_document_bytes(dict(value)))
    except CanonicalizationError as exc:
        raise CustodyEventError(f"{field.upper()}_NOT_CANONICAL:{exc}") from exc
    if not isinstance(parsed, dict):
        raise CustodyEventError(f"{field.upper()}_MAPPING_REQUIRED")
    return parsed


def _positive_decimal(value: Any, *, field: str) -> Decimal:
    if not isinstance(value, str):
        raise CustodyEventError(f"{field.upper()}_DECIMAL_TEXT_REQUIRED")
    try:
        normalized = canonical_decimal(value, quantum_places=6)
        parsed = Decimal(normalized)
    except (CanonicalizationError, InvalidOperation) as exc:
        raise CustodyEventError(f"{field.upper()}_DECIMAL_INVALID:{exc}") from exc
    if normalized != value:
        raise CustodyEventError(f"{field.upper()}_DECIMAL_NOT_CANONICAL")
    if not parsed.is_finite() or parsed <= 0:
        raise CustodyEventError(f"{field.upper()}_POSITIVE_REQUIRED")
    return parsed


def _verify_split_payload(payload: Mapping[str, Any]) -> None:
    required = {
        "numerator",
        "denominator",
        "pre_quantity",
        "pre_reference_price",
    }
    if not required.issubset(payload):
        raise CustodyEventError("SPLIT_PAYLOAD_FIELDS_MISSING")
    _positive_decimal(payload["numerator"], field="split_numerator")
    _positive_decimal(payload["denominator"], field="split_denominator")
    _positive_decimal(payload["pre_quantity"], field="split_pre_quantity")
    _positive_decimal(payload["pre_reference_price"], field="split_pre_reference_price")


def portfolio_book_event(
    sequence: int,
    event_type: str,
    effective_at: str,
    source_identity: str,
    *,
    instrument_id: str | None = None,
    cash_bucket: str | None = None,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create one content-derived event using the frozen PortfolioBookEvent envelope."""

    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        raise CustodyEventError("EVENT_SEQUENCE_NONNEGATIVE_INTEGER_REQUIRED")
    canonical_event_type = _identity_text(event_type, field="event_type")
    if canonical_event_type not in EXERCISED_EVENT_TYPES:
        raise CustodyEventError(f"EVENT_TYPE_NOT_EXERCISED:{canonical_event_type}")
    body = {
        "sequence": sequence,
        "event_type": canonical_event_type,
        "effective_at": _effective_at(effective_at),
        "source_identity": _identity_text(source_identity, field="source_identity"),
        "instrument_id": _optional_identity_text(
            instrument_id, field="instrument_id"
        ),
        "cash_bucket": _optional_identity_text(cash_bucket, field="cash_bucket"),
        "payload": _canonical_mapping(payload or {}, field="event_payload"),
    }
    if canonical_event_type == "CORPORATE_ACTION_SPLIT":
        if body["instrument_id"] is None:
            raise CustodyEventError("SPLIT_INSTRUMENT_REQUIRED")
        _verify_split_payload(body["payload"])
    return {"event_id": identifier("EVT", body), **body}


def verify_portfolio_book_event(event: Mapping[str, Any]) -> None:
    """Verify exact envelope shape, semantic primitives, and event identity."""

    if not isinstance(event, Mapping):
        raise CustodyEventError("EVENT_MAPPING_REQUIRED")
    actual_fields = frozenset(event)
    if actual_fields != EVENT_ENVELOPE_FIELDS:
        missing = sorted(EVENT_ENVELOPE_FIELDS - actual_fields)
        extra = sorted(actual_fields - EVENT_ENVELOPE_FIELDS)
        raise CustodyEventError(f"EVENT_ENVELOPE_FIELDS_INVALID:missing={missing}:extra={extra}")
    rebuilt = portfolio_book_event(
        event["sequence"],
        event["event_type"],
        event["effective_at"],
        event["source_identity"],
        instrument_id=event["instrument_id"],
        cash_bucket=event["cash_bucket"],
        payload=event["payload"],
    )
    verify_record_id(event, kind="EVT", id_key="event_id")
    if canonical_document_bytes(rebuilt) != canonical_document_bytes(dict(event)):
        raise CustodyEventError("EVENT_CANONICAL_REBUILD_MISMATCH")


class CanonicalEventStream:
    """Immutable canonical stream whose only mutation operation returns a new value."""

    __slots__ = ("_event_bytes", "_event_stream_id")

    def __init__(self, events: Iterable[Mapping[str, Any]] = ()) -> None:
        event_bytes: list[bytes] = []
        rows: list[dict[str, Any]] = []
        for event in events:
            try:
                raw = canonical_document_bytes(dict(event))
                normalized = parse_canonical_document_bytes(raw)
            except (CanonicalizationError, TypeError, ValueError) as exc:
                raise CustodyEventError(f"EVENT_NOT_CANONICAL:{exc}") from exc
            if not isinstance(normalized, dict):
                raise CustodyEventError("EVENT_MAPPING_REQUIRED")
            verify_portfolio_book_event(normalized)
            event_bytes.append(raw)
            rows.append(normalized)

        sequences = [row["sequence"] for row in rows]
        if sequences != list(range(len(rows))):
            raise CustodyEventError("EVENT_SEQUENCE_NOT_CONTIGUOUS")
        event_ids = [row["event_id"] for row in rows]
        if len(event_ids) != len(set(event_ids)):
            raise CustodyEventError("DUPLICATE_EVENT_ID")

        self._event_bytes = tuple(event_bytes)
        self._event_stream_id = identifier(
            "PES",
            {
                "schema_version": EVENT_STREAM_SCHEMA_VERSION,
                "events": rows,
            },
        )

    @property
    def event_stream_id(self) -> str:
        return self._event_stream_id

    @property
    def event_count(self) -> int:
        return len(self._event_bytes)

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            parse_canonical_document_bytes(raw) for raw in self._event_bytes
        )

    def snapshot(self) -> dict[str, Any]:
        rows = list(self.events)
        return {
            "schema_version": EVENT_STREAM_SCHEMA_VERSION,
            "event_stream_id": self.event_stream_id,
            "event_count": self.event_count,
            "first_event_id": rows[0]["event_id"] if rows else None,
            "last_event_id": rows[-1]["event_id"] if rows else None,
            "events": rows,
        }

    def canonical_bytes(self) -> bytes:
        return canonical_document_bytes(self.snapshot())

    def append(
        self,
        event_type: str,
        effective_at: str,
        source_identity: str,
        *,
        instrument_id: str | None = None,
        cash_bucket: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> "CanonicalEventStream":
        event = portfolio_book_event(
            self.event_count,
            event_type,
            effective_at,
            source_identity,
            instrument_id=instrument_id,
            cash_bucket=cash_bucket,
            payload=payload,
        )
        return self.append_event(event)

    def append_event(self, event: Mapping[str, Any]) -> "CanonicalEventStream":
        verify_portfolio_book_event(event)
        if event["sequence"] != self.event_count:
            raise CustodyEventError("APPEND_SEQUENCE_MISMATCH")
        return CanonicalEventStream((*self.events, dict(event)))

    def assert_extends(self, prior: "CanonicalEventStream") -> None:
        """Fail unless this stream contains the prior stream as an exact byte prefix."""

        if not isinstance(prior, CanonicalEventStream):
            raise CustodyEventError("PRIOR_EVENT_STREAM_REQUIRED")
        if self.event_count < prior.event_count:
            raise CustodyEventError("EVENT_STREAM_TRUNCATED")
        if self._event_bytes[: prior.event_count] != prior._event_bytes:
            raise CustodyEventError("EVENT_STREAM_HISTORY_REWRITTEN")

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "CanonicalEventStream":
        if not isinstance(snapshot, Mapping):
            raise CustodyEventError("EVENT_STREAM_SNAPSHOT_MAPPING_REQUIRED")
        expected_fields = {
            "schema_version",
            "event_stream_id",
            "event_count",
            "first_event_id",
            "last_event_id",
            "events",
        }
        if set(snapshot) != expected_fields:
            raise CustodyEventError("EVENT_STREAM_SNAPSHOT_FIELDS_INVALID")
        if snapshot["schema_version"] != EVENT_STREAM_SCHEMA_VERSION:
            raise CustodyEventError("EVENT_STREAM_SCHEMA_INVALID")
        events = snapshot["events"]
        if not isinstance(events, list):
            raise CustodyEventError("EVENT_STREAM_EVENTS_LIST_REQUIRED")
        stream = cls(events)
        if snapshot["event_count"] != stream.event_count:
            raise CustodyEventError("EVENT_STREAM_COUNT_MISMATCH")
        rebuilt = stream.snapshot()
        if canonical_document_bytes(rebuilt) != canonical_document_bytes(dict(snapshot)):
            raise CustodyEventError("EVENT_STREAM_SNAPSHOT_MISMATCH")
        return stream


def build_exercised_opening_stream(instrument_id: str) -> CanonicalEventStream:
    """Build the Slice 0 custody fixture through the exercised 2:1 split."""

    stream = CanonicalEventStream()
    stream = stream.append(
        "CASH_OPENING",
        "2026-07-20T08:55:00.000000Z",
        "FIXTURE:CASH:AVAILABLE",
        cash_bucket="AVAILABLE",
        payload={"amount": "975"},
    )
    stream = stream.append(
        "CASH_OPENING",
        "2026-07-20T08:55:00.000000Z",
        "FIXTURE:CASH:RESEARCH_RESERVE",
        cash_bucket="RESEARCH_RESERVE",
        payload={"amount": "25"},
    )
    stream = stream.append(
        "POSITION_OPENING",
        "2026-07-20T08:56:00.000000Z",
        "FIXTURE:POSITION:NSTAR",
        instrument_id=instrument_id,
        payload={"quantity": "10", "valuation_price": "50"},
    )
    return stream.append(
        "CORPORATE_ACTION_SPLIT",
        "2026-07-20T08:57:00.000000Z",
        "FIXTURE:SPLIT:NSTAR:2FOR1",
        instrument_id=instrument_id,
        payload={
            "numerator": "2",
            "denominator": "1",
            "pre_quantity": "10",
            "pre_reference_price": "50",
        },
    )
