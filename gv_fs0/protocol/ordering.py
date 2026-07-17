"""Pure identity, duplicate, and ordering primitives for GV-FS0 Protocol V1.

These functions construct and order protocol records only. They do not apply a
portfolio transition or calculate any economic balance.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from .canonical import canonical_document_bytes, domain_hash


class OrderingError(ValueError):
    """Fail-closed event identity or ordering error."""


def assign_intra_rank_sequences(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Assign contiguous intra-rank ordinals under the frozen grouping rules."""

    rows = [deepcopy(candidate) for candidate in candidates]
    groups: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["effective_timestamp"], row["session"], row["event_type_rank"])
        groups.setdefault(key, []).append(row)
    result: list[dict[str, Any]] = []
    for group_key in sorted(groups):
        group = groups[group_key]
        group.sort(
            key=lambda row: (
                row["source_sequence"],
                row["source_intent_id"].encode("ascii"),
                row["generated_event_slot"],
            )
        )
        origin_keys = [
            (row["source_sequence"], row["source_intent_id"], row["generated_event_slot"])
            for row in group
        ]
        if len(origin_keys) != len(set(origin_keys)):
            raise OrderingError("DUPLICATE_ORIGIN_ORDER_KEY")
        for index, row in enumerate(group):
            if "intra_rank_sequence" in row and row["intra_rank_sequence"] != index:
                raise OrderingError("PERSISTED_INTRA_RANK_SEQUENCE_INVALID")
            row["intra_rank_sequence"] = index
            result.append(row)
    return result


def event_identity_preimage(event: dict[str, Any]) -> dict[str, Any]:
    """Return the provenance-sensitive event-ID preimage."""

    if "intra_rank_sequence" not in event:
        raise OrderingError("INTRA_RANK_SEQUENCE_REQUIRED_BEFORE_EVENT_ID")
    required = (
        "schema_version",
        "book_id",
        "decision_id",
        "source_sequence",
        "source_intent_id",
        "generated_event_slot",
        "event_type",
        "effective_timestamp",
        "session",
        "event_type_rank",
        "intra_rank_sequence",
        "semantic_payload",
    )
    missing = [field for field in required if field not in event]
    if missing:
        raise OrderingError(f"EVENT_IDENTITY_FIELDS_MISSING:{','.join(missing)}")
    return {field: deepcopy(event[field]) for field in required}


def calculate_event_id(event: dict[str, Any]) -> str:
    """Calculate an event ID only after intra-rank assignment."""

    return "EVT_" + domain_hash("GV-FS0:PORTFOLIO_EVENT_ID:V1", event_identity_preimage(event))


def certification_reference_identity_preimage(event: dict[str, Any]) -> dict[str, Any]:
    """Return the rank-90 reference preimage with no semantic sequence."""

    if event.get("event_type") != "CERTIFICATION_REFERENCE" or event.get("event_type_rank") != 90:
        raise OrderingError("CERTIFICATION_REFERENCE_TYPE_OR_RANK_INVALID")
    required = (
        "schema_version",
        "book_id",
        "decision_id",
        "terminal_snapshot_id",
        "certification_id",
        "event_type",
        "event_type_rank",
        "effective_timestamp",
        "session",
        "source_sequence",
        "source_intent_id",
        "generated_event_slot",
        "intra_rank_sequence",
    )
    missing = [field for field in required if field not in event]
    if missing:
        raise OrderingError(f"CERTIFICATION_REFERENCE_FIELDS_MISSING:{','.join(missing)}")
    return {field: event[field] for field in required}


def calculate_certification_reference_event_id(event: dict[str, Any]) -> str:
    return "EVT_" + domain_hash(
        "GV-FS0:CERTIFICATION_REFERENCE_EVENT_ID:V1",
        certification_reference_identity_preimage(event),
    )


def collapse_and_order_events(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse exact idempotent duplicates, reject conflicts, then globally order."""

    by_event_id: dict[str, tuple[bytes, dict[str, Any]]] = {}
    economic_keys: dict[bytes, str] = {}
    for supplied in events:
        event = deepcopy(supplied)
        expected_id = (
            calculate_certification_reference_event_id(event)
            if event.get("event_type") == "CERTIFICATION_REFERENCE"
            else calculate_event_id(event)
        )
        event_id = event.get("event_id")
        if event_id is None:
            event["event_id"] = expected_id
            event_id = expected_id
        elif event_id != expected_id:
            raise OrderingError("SUPPLIED_EVENT_ID_INVALID")
        identity_bytes = canonical_document_bytes(
            certification_reference_identity_preimage(event)
            if event.get("event_type") == "CERTIFICATION_REFERENCE"
            else event_identity_preimage(event)
        )
        if event_id in by_event_id:
            prior_bytes, _ = by_event_id[event_id]
            if prior_bytes != identity_bytes:
                raise OrderingError("CONFLICTING_EVENT_ID")
            continue
        effect = event.get("economic_effect_key")
        if effect is not None:
            effect_bytes = canonical_document_bytes(effect)
            prior_event_id = economic_keys.get(effect_bytes)
            if prior_event_id is not None and prior_event_id != event_id:
                raise OrderingError("DUPLICATE_SEMANTIC_EVENT")
            economic_keys[effect_bytes] = event_id
        by_event_id[event_id] = (identity_bytes, event)

    ordered = [record for _, record in by_event_id.values()]
    ordered.sort(
        key=lambda event: (
            event["effective_timestamp"],
            event["session"],
            event["event_type_rank"],
            event["intra_rank_sequence"],
            event["event_id"],
        )
    )
    for index, event in enumerate(ordered):
        if "semantic_sequence" in event and event["semantic_sequence"] != index:
            raise OrderingError("PERSISTED_SEMANTIC_SEQUENCE_INVALID")
        event["semantic_sequence"] = index
    return ordered
