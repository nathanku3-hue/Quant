"""GV-FS0 canonical synthetic decision, book, events, and snapshots.

This module owns primary paper-economic truth for the bounded synthetic OPEN
and NO_POSITION fixtures. Both roles consume the same frozen V1 schemas/tables,
canonical encoder, event builder, reducer, and snapshot path. It performs no
verification subprocess work, certification, publication, provider access, or
UI rendering.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from core.gv_fs0_canonical import canonical_decimal, canonical_document_bytes, domain_hash

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "gv_fs0" / "v1"
SCHEMA_ROOT = CONTRACT_ROOT / "schemas"
TABLE_ROOT = CONTRACT_ROOT / "tables"

PROTOCOL_ID = "GV_FS0_PROTOCOL_V1"
PROTOCOL_VERSION = "V1"

_EVENT_RANKS_PATH = TABLE_ROOT / "gv_fs0_event_ranks_v1.json"
_EVENT_SLOTS_PATH = TABLE_ROOT / "gv_fs0_generated_event_slots_v1.json"
_OWNERSHIP_PATH = TABLE_ROOT / "gv_fs0_transition_ownership_v1.json"

_EVENT_RANKS = {
    row["event_type"]: row["event_type_rank"]
    for row in json.loads(_EVENT_RANKS_PATH.read_text(encoding="utf-8"))["entries"]
}
_EVENT_SLOTS = {
    (row["source_type"], row["event_type"]): row["generated_event_slot"]
    for row in json.loads(_EVENT_SLOTS_PATH.read_text(encoding="utf-8"))["entries"]
}
_TRANSITION_OWNERSHIP = {
    row["event_type"]: row
    for row in json.loads(_OWNERSHIP_PATH.read_text(encoding="utf-8"))["entries"]
}

_PAYLOAD_KEYS = (
    "quantity",
    "execution_price",
    "fee",
    "cash_delta",
    "position_delta",
    "dividend_amount_per_share",
    "entitled_quantity",
    "receivable_amount",
    "payment_amount",
    "referenced_entitlement_id",
    "valuation_price",
    "terminal_snapshot_id",
    "certification_id",
)


class GvFs0BookError(ValueError):
    """Fail-closed primary book error."""


@dataclass(frozen=True)
class DecisionEnvelope:
    schema_version: str
    decision_id: str
    decision_hash: str
    fixture_hash: str
    authority_tier: str
    action: str
    decision_timestamp: str
    effective_timestamp: str
    security_id: str
    requested_quantity: int | None
    rationale_ref: str
    protocol_id: str
    fixture_id: str
    operator_id: str
    supersedes_decision_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "decision_hash": self.decision_hash,
            "fixture_hash": self.fixture_hash,
            "authority_tier": self.authority_tier,
            "action": self.action,
            "decision_timestamp": self.decision_timestamp,
            "effective_timestamp": self.effective_timestamp,
            "security_id": self.security_id,
            "requested_quantity_or_sizing_input": {"quantity": self.requested_quantity},
            "rationale_ref": self.rationale_ref,
            "protocol_id": self.protocol_id,
            "fixture_id": self.fixture_id,
            "operator_id": self.operator_id,
            "supersedes_decision_id": self.supersedes_decision_id,
        }


@dataclass(frozen=True)
class PortfolioBook:
    book_id: str
    events: tuple[dict[str, Any], ...]
    snapshots: tuple[dict[str, Any], ...]
    economic_payload: dict[str, Any]
    economic_payload_hash: str


@dataclass(frozen=True)
class OpenBookBuild:
    source_fixture: dict[str, Any]
    fixture_hash: str
    decision: DecisionEnvelope
    verifier_input: dict[str, Any]
    book: PortfolioBook


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GvFs0BookError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return value


def _schema_registry() -> Registry:
    registry = Registry()
    for path in sorted(SCHEMA_ROOT.glob("*.schema.json")):
        schema = _load_json(path)
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry


def validate_schema(payload: Mapping[str, Any], schema_name: str) -> None:
    schema = _load_json(SCHEMA_ROOT / schema_name)
    Draft202012Validator(schema, registry=_schema_registry()).validate(dict(payload))


def _decimal(value: Decimal | str | int) -> str:
    raw = str(value)
    negative = raw.startswith("-")
    magnitude = raw[1:] if negative else raw
    canonical = canonical_decimal(magnitude)
    return f"-{canonical}" if negative and canonical != "0" else canonical


def _empty_payload(**values: Any) -> dict[str, Any]:
    payload = {key: None for key in _PAYLOAD_KEYS}
    unknown = set(values) - set(payload)
    if unknown:
        raise GvFs0BookError(f"UNKNOWN_EVENT_PAYLOAD_FIELDS:{sorted(unknown)}")
    payload.update(values)
    return payload


def _source_intent(
    intent_type: str,
    sequence: int,
    *,
    session: str,
    security_id: str = "SEC_1",
    quantity: int | None = None,
    execution_price: str | None = None,
    fee: str | None = None,
    dividend_amount_per_share: str | None = None,
    referenced_entitlement_source_intent_id: str | None = None,
    valuation_timestamp: str | None = None,
    effective_timestamp: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "gv_fs0_source_intent_v1",
        "source_intent_id": f"{intent_type}:{sequence}",
        "source_sequence": sequence,
        "intent_type": intent_type,
        "effective_timestamp": effective_timestamp or f"{session}T14:30:00.000000Z",
        "session": session,
        "security_id": security_id,
        "quantity": quantity,
        "execution_price": execution_price,
        "fee": fee,
        "dividend_amount_per_share": dividend_amount_per_share,
        "referenced_entitlement_source_intent_id": referenced_entitlement_source_intent_id,
        "valuation_timestamp": valuation_timestamp,
    }


def _build_source_fixture(*, fixture_id: str, include_open_intents: bool) -> dict[str, Any]:
    sessions = ["2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17"]
    closes = ["10", "11", "12", "13", "14"]
    prices = [
        {
            "security_id": "SEC_1",
            "session": session,
            "price_timestamp": f"{session}T20:00:00.000000Z",
            "close_price": close,
            "source_sequence": index,
        }
        for index, (session, close) in enumerate(zip(sessions, closes, strict=True))
    ]
    intents: list[dict[str, Any]] = []
    if include_open_intents:
        intents.extend(
            [
                _source_intent(
                    "EXECUTION_INTENT",
                    0,
                    session="2026-07-14",
                    quantity=10,
                    execution_price="10",
                ),
                _source_intent("EXPLICIT_FEE", 1, session="2026-07-14", fee="1"),
                _source_intent(
                    "DIVIDEND_DECLARATION",
                    2,
                    session="2026-07-15",
                    dividend_amount_per_share="0.5",
                ),
                _source_intent(
                    "DIVIDEND_PAYMENT_INSTRUCTION",
                    3,
                    session="2026-07-16",
                    referenced_entitlement_source_intent_id="DIVIDEND_DECLARATION:2",
                ),
            ]
        )
    valuation_sequence = len(intents)
    intents.extend(
        _source_intent(
            "VALUATION_INSTRUCTION",
            sequence=valuation_sequence + index,
            session=session,
            valuation_timestamp=f"{session}T20:00:00.000000Z",
            effective_timestamp=f"{session}T20:00:00.000000Z",
        )
        for index, session in enumerate(sessions)
    )
    fixture = {
        "schema_version": "gv_fs0_source_fixture_v1",
        "protocol_id": PROTOCOL_ID,
        "fixture_id": fixture_id,
        "currency": "USD",
        "security_id": "SEC_1",
        "initial_cash": "1000",
        "sessions": sessions,
        "source_prices": prices,
        "source_intents": intents,
    }
    validate_schema(fixture, "gv_fs0_source_fixture_v1.schema.json")
    return fixture


def build_open_source_fixture() -> dict[str, Any]:
    return _build_source_fixture(fixture_id="FIXTURE_OPEN_1", include_open_intents=True)


def build_no_position_source_fixture() -> dict[str, Any]:
    return _build_source_fixture(
        fixture_id="FIXTURE_NO_POSITION_1", include_open_intents=False
    )


def _build_decision(
    *,
    fixture_hash: str,
    fixture_id: str,
    decision_id: str,
    action: str,
    requested_quantity: int | None,
    rationale_ref: str,
) -> DecisionEnvelope:
    base = {
        "schema_version": "gv_fs0_decision_envelope_v1",
        "decision_id": decision_id,
        "fixture_hash": fixture_hash,
        "authority_tier": "MANUAL_OWNER_PAPER",
        "action": action,
        "decision_timestamp": "2026-07-12T00:00:00.000000Z",
        "effective_timestamp": "2026-07-13T00:00:00.000000Z",
        "security_id": "SEC_1",
        "requested_quantity_or_sizing_input": {"quantity": requested_quantity},
        "rationale_ref": rationale_ref,
        "protocol_id": PROTOCOL_ID,
        "fixture_id": fixture_id,
        "operator_id": "OWNER_1",
        "supersedes_decision_id": None,
    }
    decision_hash = domain_hash("GV-FS0:DECISION_ENVELOPE:V1", base)
    decision = DecisionEnvelope(
        schema_version=base["schema_version"],
        decision_id=base["decision_id"],
        decision_hash=decision_hash,
        fixture_hash=fixture_hash,
        authority_tier=base["authority_tier"],
        action=base["action"],
        decision_timestamp=base["decision_timestamp"],
        effective_timestamp=base["effective_timestamp"],
        security_id=base["security_id"],
        requested_quantity=requested_quantity,
        rationale_ref=base["rationale_ref"],
        protocol_id=PROTOCOL_ID,
        fixture_id=fixture_id,
        operator_id=base["operator_id"],
        supersedes_decision_id=None,
    )
    validate_schema(decision.to_dict(), "gv_fs0_decision_envelope_v1.schema.json")
    return decision


def build_open_decision(fixture_hash: str, fixture_id: str) -> DecisionEnvelope:
    return _build_decision(
        fixture_hash=fixture_hash,
        fixture_id=fixture_id,
        decision_id="DECISION_OPEN_1",
        action="OPEN",
        requested_quantity=10,
        rationale_ref="RATIONALE:OPEN_1",
    )


def build_no_position_decision(fixture_hash: str, fixture_id: str) -> DecisionEnvelope:
    return _build_decision(
        fixture_hash=fixture_hash,
        fixture_id=fixture_id,
        decision_id="DECISION_NO_POSITION_1",
        action="NO_POSITION",
        requested_quantity=None,
        rationale_ref="RATIONALE:NO_POSITION_1",
    )


def _book_id(decision: DecisionEnvelope) -> str:
    preimage = {
        "protocol_id": decision.protocol_id,
        "fixture_id": decision.fixture_id,
        "fixture_hash": decision.fixture_hash,
        "decision_id": decision.decision_id,
        "decision_hash": decision.decision_hash,
    }
    return "BOOK_" + domain_hash("GV-FS0:BOOK_ID:V1", preimage)


def build_verifier_input(
    fixture: Mapping[str, Any], decision: DecisionEnvelope
) -> dict[str, Any]:
    payload = {
        "schema_version": "gv_fs0_verifier_input_v1",
        "protocol": {
            "protocol_id": decision.protocol_id,
            "fixture_id": decision.fixture_id,
            "fixture_hash": decision.fixture_hash,
            "currency": fixture["currency"],
            "initial_cash": fixture["initial_cash"],
        },
        "decision": {
            "decision_id": decision.decision_id,
            "decision_hash": decision.decision_hash,
            "authority": decision.authority_tier,
            "action": decision.action,
            "decision_timestamp": decision.decision_timestamp,
            "effective_timestamp": decision.effective_timestamp,
            "security_id": decision.security_id,
            "requested_sizing": {"quantity": decision.requested_quantity},
            "rationale_reference": decision.rationale_ref,
        },
        "source_prices": list(fixture["source_prices"]),
        "source_intents": list(fixture["source_intents"]),
    }
    validate_schema(payload, "gv_fs0_verifier_input_v1.schema.json")
    return payload


def _candidate(
    *,
    book_id: str,
    decision: DecisionEnvelope,
    source_type: str,
    source_sequence: int,
    source_intent_id: str,
    event_type: str,
    effective_timestamp: str,
    session: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "gv_fs0_portfolio_event_v1",
        "book_id": book_id,
        "decision_id": decision.decision_id,
        "source_sequence": source_sequence,
        "source_intent_id": source_intent_id,
        "generated_event_slot": _EVENT_SLOTS[(source_type, event_type)],
        "event_type": event_type,
        "effective_timestamp": effective_timestamp,
        "session": session,
        "event_type_rank": _EVENT_RANKS[event_type],
        "security_id": decision.security_id,
        "payload": payload,
    }


def _event_identity_preimage(candidate: Mapping[str, Any], intra_rank_sequence: int) -> dict[str, Any]:
    return {
        "schema_version": candidate["schema_version"],
        "book_id": candidate["book_id"],
        "decision_id": candidate["decision_id"],
        "source_sequence": candidate["source_sequence"],
        "source_intent_id": candidate["source_intent_id"],
        "generated_event_slot": candidate["generated_event_slot"],
        "event_type": candidate["event_type"],
        "effective_timestamp": candidate["effective_timestamp"],
        "session": candidate["session"],
        "event_type_rank": candidate["event_type_rank"],
        "intra_rank_sequence": intra_rank_sequence,
        "payload": candidate["payload"],
    }


def _assign_intra_rank(candidates: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    unique_candidates: dict[bytes, dict[str, Any]] = {}
    for candidate in candidates:
        unique_candidates.setdefault(canonical_document_bytes(candidate), candidate)
    groups: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    for candidate in unique_candidates.values():
        key = (
            candidate["effective_timestamp"],
            candidate["session"],
            candidate["event_type_rank"],
        )
        groups.setdefault(key, []).append(candidate)
    completed: list[dict[str, Any]] = []
    for group in groups.values():
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
            raise GvFs0BookError("DUPLICATE_ORIGIN_ORDER_KEY")
        for intra_rank_sequence, row in enumerate(group):
            completed.append({**row, "intra_rank_sequence": intra_rank_sequence})
    return completed


def _economic_effect_key(event: Mapping[str, Any]) -> bytes:
    payload = event["payload"]
    return canonical_document_bytes(
        {
            "book_id": event["book_id"],
            "event_type": event["event_type"],
            "effective_timestamp": event["effective_timestamp"],
            "session": event["session"],
            "security_id": event["security_id"],
            **{key: payload[key] for key in _PAYLOAD_KEYS},
        }
    )


def _deduplicate_completed_events(
    events: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    retained_by_id: dict[str, tuple[bytes, dict[str, Any]]] = {}
    economic_effect_ids: dict[bytes, str] = {}
    for event in events:
        identity = canonical_document_bytes(
            _event_identity_preimage(event, event["intra_rank_sequence"])
        )
        event_id = event["event_id"]
        existing = retained_by_id.get(event_id)
        if existing is not None:
            if existing[0] != identity:
                raise GvFs0BookError("CONFLICTING_EVENT_ID")
            continue
        effect_key = _economic_effect_key(event)
        prior_id = economic_effect_ids.get(effect_key)
        if prior_id is not None and prior_id != event_id:
            raise GvFs0BookError("DUPLICATE_SEMANTIC_EVENT")
        retained_by_id[event_id] = (identity, event)
        economic_effect_ids[effect_key] = event_id
    return [entry[1] for entry in retained_by_id.values()]


def _build_economic_events(
    fixture: Mapping[str, Any], decision: DecisionEnvelope, book_id: str
) -> tuple[dict[str, Any], ...]:
    source_intent_types = [intent["intent_type"] for intent in fixture["source_intents"]]
    if decision.action == "NO_POSITION":
        if decision.requested_quantity is not None:
            raise GvFs0BookError("NO_POSITION_QUANTITY_PROHIBITED")
        if any(intent_type != "VALUATION_INSTRUCTION" for intent_type in source_intent_types):
            raise GvFs0BookError("NO_POSITION_NON_VALUATION_INTENT_PROHIBITED")
    elif decision.action != "OPEN":
        raise GvFs0BookError(f"UNSUPPORTED_DECISION_ACTION:{decision.action}")

    price_by_session = {row["session"]: row for row in fixture["source_prices"]}
    candidates: list[dict[str, Any]] = [
        _candidate(
            book_id=book_id,
            decision=decision,
            source_type="DECISION_ENVELOPE",
            source_sequence=0,
            source_intent_id=f"DECISION:{decision.decision_hash}",
            event_type="DECISION_ACCEPTED",
            effective_timestamp=decision.effective_timestamp,
            session=fixture["sessions"][0],
            payload=_empty_payload(quantity=decision.requested_quantity),
        )
    ]
    entitlement_candidate: dict[str, Any] | None = None
    for intent in fixture["source_intents"]:
        intent_type = intent["intent_type"]
        common = dict(
            book_id=book_id,
            decision=decision,
            source_type=intent_type,
            source_sequence=intent["source_sequence"],
            source_intent_id=intent["source_intent_id"],
            effective_timestamp=intent["effective_timestamp"],
            session=intent["session"],
        )
        if intent_type == "EXECUTION_INTENT":
            quantity = intent["quantity"]
            execution_price = Decimal(intent["execution_price"])
            cash_delta = -(Decimal(quantity) * execution_price)
            candidates.extend(
                [
                    _candidate(
                        **common,
                        event_type="EXECUTION",
                        payload=_empty_payload(
                            quantity=quantity,
                            execution_price=_decimal(execution_price),
                        ),
                    ),
                    _candidate(
                        **common,
                        event_type="CASH_MOVEMENT",
                        payload=_empty_payload(cash_delta=_decimal(cash_delta)),
                    ),
                    _candidate(
                        **common,
                        event_type="POSITION_MOVEMENT",
                        payload=_empty_payload(position_delta=str(quantity)),
                    ),
                ]
            )
        elif intent_type == "EXPLICIT_FEE":
            fee = Decimal(intent["fee"])
            candidates.extend(
                [
                    _candidate(
                        **common,
                        event_type="FEE_OR_COST",
                        payload=_empty_payload(fee=_decimal(fee)),
                    ),
                    _candidate(
                        **common,
                        event_type="CASH_MOVEMENT",
                        payload=_empty_payload(cash_delta=_decimal(-fee)),
                    ),
                ]
            )
        elif intent_type == "DIVIDEND_DECLARATION":
            amount_per_share = Decimal(intent["dividend_amount_per_share"])
            entitled_quantity = decision.requested_quantity or 0
            entitlement_candidate = _candidate(
                **common,
                event_type="DIVIDEND_ENTITLEMENT",
                payload=_empty_payload(
                    dividend_amount_per_share=_decimal(amount_per_share),
                    entitled_quantity=entitled_quantity,
                    receivable_amount=_decimal(Decimal(entitled_quantity) * amount_per_share),
                ),
            )
            candidates.append(entitlement_candidate)
        elif intent_type == "DIVIDEND_PAYMENT_INSTRUCTION":
            candidates.append(
                _candidate(
                    **common,
                    event_type="DIVIDEND_PAYMENT",
                    payload=_empty_payload(),
                )
            )
        elif intent_type == "VALUATION_INSTRUCTION":
            price = price_by_session[intent["session"]]
            valuation_common = {
                **common,
                "effective_timestamp": intent["valuation_timestamp"],
            }
            candidates.append(
                _candidate(
                    **valuation_common,
                    event_type="SESSION_VALUATION",
                    payload=_empty_payload(valuation_price=price["close_price"]),
                )
            )
        else:
            raise GvFs0BookError(f"UNSUPPORTED_SOURCE_INTENT:{intent_type}")

    with_intra = _assign_intra_rank(candidates)
    entitlement_rows = [
        row for row in with_intra if row["event_type"] == "DIVIDEND_ENTITLEMENT"
    ]
    if len(entitlement_rows) > 1:
        raise GvFs0BookError("MULTIPLE_DIVIDEND_ENTITLEMENTS_PROHIBITED")
    entitlement_row = entitlement_rows[0] if entitlement_rows else None
    entitlement_id = (
        "EVT_"
        + domain_hash(
            "GV-FS0:PORTFOLIO_EVENT_ID:V1",
            _event_identity_preimage(
                entitlement_row, entitlement_row["intra_rank_sequence"]
            ),
        )
        if entitlement_row is not None
        else None
    )
    completed: list[dict[str, Any]] = []
    for row in with_intra:
        payload = dict(row["payload"])
        if row["event_type"] == "DIVIDEND_PAYMENT":
            if entitlement_row is None or entitlement_id is None:
                raise GvFs0BookError("DIVIDEND_ENTITLEMENT_MISSING")
            payload["payment_amount"] = entitlement_row["payload"]["receivable_amount"]
            payload["referenced_entitlement_id"] = entitlement_id
            row = {**row, "payload": payload}
        preimage = _event_identity_preimage(row, row["intra_rank_sequence"])
        event_id = "EVT_" + domain_hash("GV-FS0:PORTFOLIO_EVENT_ID:V1", preimage)
        completed.append({**row, "event_id": event_id})

    completed = _deduplicate_completed_events(completed)
    completed.sort(
        key=lambda row: (
            row["effective_timestamp"],
            row["session"],
            row["event_type_rank"],
            row["intra_rank_sequence"],
            row["event_id"],
        )
    )
    final_events = [
        {**row, "semantic_sequence": semantic_sequence}
        for semantic_sequence, row in enumerate(completed)
    ]
    for event in final_events:
        validate_schema(event, "gv_fs0_portfolio_event_v1.schema.json")
        if event["event_type"] not in _TRANSITION_OWNERSHIP:
            raise GvFs0BookError("UNSUPPORTED_EVENT_TYPE")
    return tuple(final_events)


def _snapshot_preimage(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: snapshot[key]
        for key in (
            "book_id",
            "decision_id",
            "fixture_hash",
            "session",
            "valuation_timestamp",
            "applied_event_ids",
            "shares",
            "cash",
            "receivables",
            "market_value",
            "nav",
            "session_contribution",
            "cumulative_contribution",
        )
    }


def snapshots_from_session_rows(
    *,
    decision: DecisionEnvelope,
    book_id: str,
    events: Sequence[Mapping[str, Any]],
    session_rows: Sequence[Mapping[str, Any]],
    initial_cash: str,
) -> tuple[dict[str, Any], ...]:
    """Create canonical snapshots from independently supplied session economics."""

    event_ids_by_session: dict[str, list[str]] = {}
    ordered_ids: list[str] = []
    for event in events:
        ordered_ids.append(event["event_id"])
        event_ids_by_session[event["session"]] = list(ordered_ids)
    valuation_timestamp_by_session = {
        event["session"]: event["effective_timestamp"]
        for event in events
        if event["event_type"] == "SESSION_VALUATION"
    }
    previous_nav = Decimal(initial_cash)
    snapshots: list[dict[str, Any]] = []
    for row in session_rows:
        session = row["session"]
        nav = Decimal(row["nav"])
        session_contribution = nav - previous_nav
        previous_nav = nav
        snapshot = {
            "schema_version": "gv_fs0_snapshot_v1",
            "session": session,
            "valuation_timestamp": valuation_timestamp_by_session[session],
            "book_id": book_id,
            "decision_id": decision.decision_id,
            "fixture_hash": decision.fixture_hash,
            "authority_tier": decision.authority_tier,
            "action": decision.action,
            "rationale_ref": decision.rationale_ref,
            "security_id": decision.security_id,
            "shares": row["shares"],
            "cash": _decimal(row["cash"]),
            "receivables": _decimal(row["receivables"]),
            "market_value": _decimal(row["market_value"]),
            "nav": _decimal(row["nav"]),
            "session_contribution": _decimal(session_contribution),
            "cumulative_contribution": _decimal(nav - Decimal(initial_cash)),
            "applied_event_ids": event_ids_by_session[session],
        }
        snapshot_id = "SNAP_" + domain_hash(
            "GV-FS0:SNAPSHOT_ID:V1", _snapshot_preimage(snapshot)
        )
        snapshot["snapshot_id"] = snapshot_id
        validate_schema(snapshot, "gv_fs0_snapshot_v1.schema.json")
        snapshots.append(snapshot)
    return tuple(snapshots)


def _reduce_book(
    fixture: Mapping[str, Any],
    decision: DecisionEnvelope,
    book_id: str,
    events: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    cash = Decimal(fixture["initial_cash"])
    shares = 0
    receivables: dict[str, Decimal] = {}
    paid_entitlements: set[str] = set()
    session_rows: list[dict[str, Any]] = []
    for event in events:
        event_type = event["event_type"]
        payload = event["payload"]
        if event_type == "CASH_MOVEMENT":
            cash += Decimal(payload["cash_delta"])
        elif event_type == "POSITION_MOVEMENT":
            shares += int(payload["position_delta"])
        elif event_type == "DIVIDEND_ENTITLEMENT":
            receivables[event["event_id"]] = Decimal(payload["receivable_amount"])
        elif event_type == "DIVIDEND_PAYMENT":
            entitlement_id = payload["referenced_entitlement_id"]
            if entitlement_id in paid_entitlements or entitlement_id not in receivables:
                raise GvFs0BookError("DIVIDEND_PAYMENT_INVALID")
            amount = receivables.pop(entitlement_id)
            if amount != Decimal(payload["payment_amount"]):
                raise GvFs0BookError("DIVIDEND_PAYMENT_AMOUNT_MISMATCH")
            paid_entitlements.add(entitlement_id)
            cash += amount
        elif event_type == "SESSION_VALUATION":
            receivable_total = sum(receivables.values(), Decimal("0"))
            market_value = Decimal(shares) * Decimal(payload["valuation_price"])
            nav = cash + market_value + receivable_total
            session_rows.append(
                {
                    "session": event["session"],
                    "shares": shares,
                    "cash": _decimal(cash),
                    "receivables": _decimal(receivable_total),
                    "market_value": _decimal(market_value),
                    "nav": _decimal(nav),
                }
            )
        if cash < 0 or shares < 0:
            raise GvFs0BookError("NEGATIVE_BOOK_STATE")
    if receivables:
        raise GvFs0BookError("UNPAID_DIVIDEND_ENTITLEMENT")
    if len(session_rows) != len(fixture["sessions"]):
        raise GvFs0BookError("SNAPSHOT_SESSION_COUNT_MISMATCH")
    return snapshots_from_session_rows(
        decision=decision,
        book_id=book_id,
        events=events,
        session_rows=session_rows,
        initial_cash=fixture["initial_cash"],
    )


def economic_payload(
    *,
    decision: DecisionEnvelope,
    book_id: str,
    events: Sequence[Mapping[str, Any]],
    snapshots: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "protocol_id": decision.protocol_id,
        "fixture_id": decision.fixture_id,
        "fixture_hash": decision.fixture_hash,
        "decision_id": decision.decision_id,
        "decision_hash": decision.decision_hash,
        "book_id": book_id,
        "ordered_economic_event_ids": [event["event_id"] for event in events],
        "snapshots": [dict(snapshot) for snapshot in snapshots],
        "terminal_snapshot_id": snapshots[-1]["snapshot_id"],
    }


def _build_book(
    *,
    fixture: dict[str, Any],
    decision_builder: Callable[[str, str], DecisionEnvelope],
) -> OpenBookBuild:
    fixture_hash = domain_hash("GV-FS0:FIXTURE:V1", fixture)
    decision = decision_builder(fixture_hash, fixture["fixture_id"])
    verifier_input = build_verifier_input(fixture, decision)
    book_id = _book_id(decision)
    events = _build_economic_events(fixture, decision, book_id)
    snapshots = _reduce_book(fixture, decision, book_id, events)
    payload = economic_payload(
        decision=decision,
        book_id=book_id,
        events=events,
        snapshots=snapshots,
    )
    payload_hash = domain_hash("GV-FS0:ECONOMIC_PAYLOAD:V1", payload)
    book = PortfolioBook(
        book_id=book_id,
        events=events,
        snapshots=snapshots,
        economic_payload=payload,
        economic_payload_hash=payload_hash,
    )
    return OpenBookBuild(
        source_fixture=fixture,
        fixture_hash=fixture_hash,
        decision=decision,
        verifier_input=verifier_input,
        book=book,
    )


def build_open_book() -> OpenBookBuild:
    return _build_book(
        fixture=build_open_source_fixture(), decision_builder=build_open_decision
    )


def build_no_position_book() -> OpenBookBuild:
    return _build_book(
        fixture=build_no_position_source_fixture(),
        decision_builder=build_no_position_decision,
    )


def verifier_rows_to_economic_payload(
    build: OpenBookBuild, verifier_rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    snapshots = snapshots_from_session_rows(
        decision=build.decision,
        book_id=build.book.book_id,
        events=build.book.events,
        session_rows=verifier_rows,
        initial_cash=build.source_fixture["initial_cash"],
    )
    return economic_payload(
        decision=build.decision,
        book_id=build.book.book_id,
        events=build.book.events,
        snapshots=snapshots,
    )


__all__ = [
    "DecisionEnvelope",
    "GvFs0BookError",
    "OpenBookBuild",
    "PortfolioBook",
    "PROTOCOL_ID",
    "PROTOCOL_VERSION",
    "build_no_position_book",
    "build_open_book",
    "validate_schema",
    "verifier_rows_to_economic_payload",
]
