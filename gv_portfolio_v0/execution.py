"""Deterministic execution-event authority for GV Portfolio V0.

Execution consumes an immutable decision snapshot and confirmed portfolio aim,
then emits transition, order, and fill events. It never mutates the portfolio
book, persists workspace state, renders UI, or produces certification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.allocation import (
    AllocationError,
    plan_transition,
    validate_execution_handoff,
)
from gv_portfolio_v0.decimal_utils import decimal_text

ID_DOMAIN = "GV-PORTFOLIO-V0"
EXECUTION_MODE = "DETERMINISTIC_PAPER"
MAX_TRADE_DECIMAL_INTEGER_DIGITS = 64
MAX_TRADE_DECIMAL_FRACTION_DIGITS = 64


class ExecutionError(ValueError):
    """Raised when any execution-authority edge fails closed."""


def _identifier(kind: str, payload: Mapping[str, Any]) -> str:
    return f"{kind}_" + domain_hash(f"{ID_DOMAIN}:{kind}:V1", dict(payload))


def _record_with_id(
    kind: str, id_key: str, payload: Mapping[str, Any]
) -> dict[str, Any]:
    body = dict(payload)
    return {id_key: _identifier(kind, body), **body}


def _verify_record_id(
    record: Mapping[str, Any], *, kind: str, id_key: str
) -> None:
    if not isinstance(record, Mapping):
        raise ExecutionError(f"{id_key.upper()}_RECORD_REQUIRED")
    body = {key: value for key, value in record.items() if key != id_key}
    if record.get(id_key) != _identifier(kind, body):
        raise ExecutionError(f"IDENTITY_MISMATCH:{id_key}")


def _timestamp(value: Any, *, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ExecutionError(f"{field.upper()}_UTC_TIMESTAMP_REQUIRED")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ExecutionError(f"{field.upper()}_TIMESTAMP_INVALID") from exc
    if parsed.tzinfo != timezone.utc:
        raise ExecutionError(f"{field.upper()}_UTC_TIMESTAMP_REQUIRED")
    return parsed


def _require_not_before(
    later: Any, earlier: Any, *, later_field: str, earlier_field: str
) -> None:
    if _timestamp(later, field=later_field) < _timestamp(
        earlier, field=earlier_field
    ):
        raise ExecutionError(
            f"{later_field.upper()}_BEFORE_{earlier_field.upper()}"
        )


def _handoff(
    decision_snapshot: Mapping[str, Any], portfolio_aim: Mapping[str, Any]
) -> dict[str, Any]:
    try:
        return validate_execution_handoff(decision_snapshot, portfolio_aim)
    except AllocationError as exc:
        raise ExecutionError(str(exc)) from exc


def _transition(
    decision_snapshot: Mapping[str, Any],
    portfolio_aim: Mapping[str, Any],
    *,
    current_quantity: Any,
    cash_bucket: str,
) -> dict[str, Any]:
    try:
        return plan_transition(
            decision_snapshot,
            portfolio_aim,
            current_quantity=current_quantity,
            cash_bucket=cash_bucket,
        )
    except AllocationError as exc:
        raise ExecutionError(str(exc)) from exc


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
    """Create the frozen PortfolioBookEvent envelope used by Stream 4."""

    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        raise ExecutionError("EVENT_SEQUENCE_INVALID")
    if not isinstance(event_type, str) or not event_type:
        raise ExecutionError("EVENT_TYPE_REQUIRED")
    _timestamp(effective_at, field="effective_at")
    if not isinstance(source_identity, str) or not source_identity:
        raise ExecutionError("EVENT_SOURCE_IDENTITY_REQUIRED")
    preimage = {
        "sequence": sequence,
        "event_type": event_type,
        "effective_at": effective_at,
        "source_identity": source_identity,
        "instrument_id": instrument_id,
        "cash_bucket": cash_bucket,
        "payload": dict(payload or {}),
    }
    return {"event_id": _identifier("EVT", preimage), **preimage}


def _verify_event(event: Mapping[str, Any]) -> None:
    _verify_record_id(event, kind="EVT", id_key="event_id")
    if not isinstance(event.get("sequence"), int) or isinstance(
        event.get("sequence"), bool
    ):
        raise ExecutionError("EVENT_SEQUENCE_INVALID")
    if event["sequence"] < 0:
        raise ExecutionError("EVENT_SEQUENCE_INVALID")
    _timestamp(event.get("effective_at"), field="effective_at")


def create_aim_confirmation_event(
    decision_snapshot: Mapping[str, Any],
    portfolio_aim: Mapping[str, Any],
    *,
    sequence: int,
    effective_at: str,
) -> dict[str, Any]:
    selection = _handoff(decision_snapshot, portfolio_aim)
    _require_not_before(
        effective_at,
        portfolio_aim.get("effective_at"),
        later_field="aim_confirmed_at",
        earlier_field="aim_effective_at",
    )
    return portfolio_book_event(
        sequence,
        "PORTFOLIO_AIM_CONFIRMED",
        effective_at,
        portfolio_aim["portfolio_aim_id"],
        payload={
            "decision_snapshot_id": selection["decision_snapshot_id"],
            "portfolio_aim_id": selection["portfolio_aim_id"],
        },
    )


def create_transition_event(
    decision_snapshot: Mapping[str, Any],
    portfolio_aim: Mapping[str, Any],
    *,
    current_quantity: Any,
    cash_bucket: str,
    sequence: int,
    effective_at: str,
) -> dict[str, Any]:
    transition = _transition(
        decision_snapshot,
        portfolio_aim,
        current_quantity=current_quantity,
        cash_bucket=cash_bucket,
    )
    _require_not_before(
        effective_at,
        decision_snapshot.get("created_at"),
        later_field="transition_effective_at",
        earlier_field="decision_created_at",
    )
    return portfolio_book_event(
        sequence,
        "PORTFOLIO_TRANSITION_PLANNED",
        effective_at,
        decision_snapshot["decision_snapshot_id"],
        instrument_id=transition["instrument_id"],
        cash_bucket=transition["cash_bucket"],
        payload={"transition": transition},
    )


def _verify_transition_event(
    decision_snapshot: Mapping[str, Any],
    portfolio_aim: Mapping[str, Any],
    transition_event: Mapping[str, Any],
) -> dict[str, Any]:
    _verify_event(transition_event)
    if transition_event.get("event_type") != "PORTFOLIO_TRANSITION_PLANNED":
        raise ExecutionError("TRANSITION_EVENT_TYPE_INVALID")
    transition = transition_event.get("payload", {}).get("transition")
    if not isinstance(transition, Mapping):
        raise ExecutionError("TRANSITION_PAYLOAD_REQUIRED")
    expected = _transition(
        decision_snapshot,
        portfolio_aim,
        current_quantity=transition.get("current_quantity"),
        cash_bucket=transition.get("cash_bucket"),
    )
    if canonical_document_bytes(dict(transition)) != canonical_document_bytes(
        expected
    ):
        raise ExecutionError("TRANSITION_PROJECTION_MISMATCH")
    if transition_event.get("source_identity") != decision_snapshot.get(
        "decision_snapshot_id"
    ):
        raise ExecutionError("TRANSITION_SNAPSHOT_BINDING_MISMATCH")
    if transition_event.get("instrument_id") != transition.get("instrument_id"):
        raise ExecutionError("TRANSITION_EVENT_INSTRUMENT_MISMATCH")
    if transition_event.get("cash_bucket") != transition.get("cash_bucket"):
        raise ExecutionError("TRANSITION_EVENT_CASH_BUCKET_MISMATCH")
    return dict(transition)


def create_order(
    decision_snapshot: Mapping[str, Any],
    portfolio_aim: Mapping[str, Any],
    transition_event: Mapping[str, Any],
    *,
    created_at: str,
) -> dict[str, Any]:
    selection = _handoff(decision_snapshot, portfolio_aim)
    transition = _verify_transition_event(
        decision_snapshot, portfolio_aim, transition_event
    )
    if selection["action"] != "BUY":
        raise ExecutionError("CASH_TRANSITION_CANNOT_CREATE_ORDER")
    _require_not_before(
        created_at,
        transition_event.get("effective_at"),
        later_field="order_created_at",
        earlier_field="transition_effective_at",
    )
    payload = {
        "decision_snapshot_id": selection["decision_snapshot_id"],
        "portfolio_aim_id": selection["portfolio_aim_id"],
        "transition_event_id": transition_event["event_id"],
        "instrument_id": transition["instrument_id"],
        "side": "BUY",
        "quantity": transition["quantity_delta"],
        "reference_price": transition["reference_price"],
        "expected_fee": transition["expected_fee"],
        "cash_bucket": transition["cash_bucket"],
        "created_at": created_at,
        "execution_mode": EXECUTION_MODE,
    }
    return _record_with_id("ORD", "order_id", payload)


def create_order_event(
    order: Mapping[str, Any], *, sequence: int
) -> dict[str, Any]:
    _verify_record_id(order, kind="ORD", id_key="order_id")
    return portfolio_book_event(
        sequence,
        "ORDER_CREATED",
        order["created_at"],
        order["order_id"],
        instrument_id=order["instrument_id"],
        cash_bucket=order["cash_bucket"],
        payload={"order": dict(order)},
    )


def _verify_order_event(
    order: Mapping[str, Any], order_event: Mapping[str, Any]
) -> None:
    _verify_record_id(order, kind="ORD", id_key="order_id")
    _verify_event(order_event)
    if order_event.get("event_type") != "ORDER_CREATED":
        raise ExecutionError("ORDER_EVENT_TYPE_INVALID")
    if order_event.get("source_identity") != order.get("order_id"):
        raise ExecutionError("ORDER_EVENT_SOURCE_MISMATCH")
    if order_event.get("effective_at") != order.get("created_at"):
        raise ExecutionError("ORDER_EVENT_TIMESTAMP_MISMATCH")
    if order_event.get("instrument_id") != order.get("instrument_id"):
        raise ExecutionError("ORDER_EVENT_INSTRUMENT_MISMATCH")
    if order_event.get("cash_bucket") != order.get("cash_bucket"):
        raise ExecutionError("ORDER_EVENT_CASH_BUCKET_MISMATCH")
    payload_order = order_event.get("payload", {}).get("order")
    if not isinstance(payload_order, Mapping) or canonical_document_bytes(
        dict(payload_order)
    ) != canonical_document_bytes(dict(order)):
        raise ExecutionError("ORDER_EVENT_PAYLOAD_MISMATCH")


def create_fill(
    order: Mapping[str, Any],
    order_event: Mapping[str, Any],
    *,
    filled_at: str,
) -> dict[str, Any]:
    _verify_order_event(order, order_event)
    _require_not_before(
        filled_at,
        order.get("created_at"),
        later_field="filled_at",
        earlier_field="order_created_at",
    )
    payload = {
        "order_id": order["order_id"],
        "order_created_event_id": order_event["event_id"],
        "instrument_id": order["instrument_id"],
        "side": order["side"],
        "quantity": order["quantity"],
        "price": order["reference_price"],
        "fee": order["expected_fee"],
        "cash_bucket": order["cash_bucket"],
        "filled_at": filled_at,
        "fill_mode": "COMPLETE",
    }
    return _record_with_id("FIL", "fill_id", payload)


def create_fill_event(fill: Mapping[str, Any], *, sequence: int) -> dict[str, Any]:
    _verify_record_id(fill, kind="FIL", id_key="fill_id")
    return portfolio_book_event(
        sequence,
        "FILL_COMPLETED",
        fill["filled_at"],
        fill["fill_id"],
        instrument_id=fill["instrument_id"],
        cash_bucket=fill["cash_bucket"],
        payload={"fill": dict(fill)},
    )


def _trade_decimal_text(
    value: Any,
    *,
    field: str,
    positive: bool = False,
    money: bool = False,
) -> str:
    if isinstance(value, bool) or isinstance(value, float):
        raise ExecutionError(f"{field.upper()}_DECIMAL_TYPE_INVALID")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ExecutionError(f"{field.upper()}_DECIMAL_INVALID") from exc
    if not parsed.is_finite():
        raise ExecutionError(f"{field.upper()}_DECIMAL_FINITE_REQUIRED")
    if positive and parsed <= 0:
        raise ExecutionError(f"{field.upper()}_MUST_BE_POSITIVE")
    if not positive and parsed < 0:
        raise ExecutionError(f"{field.upper()}_MUST_BE_NONNEGATIVE")
    _, digits, exponent = parsed.as_tuple()
    effective_digits = list(digits)
    while len(effective_digits) > 1 and effective_digits[-1] == 0:
        effective_digits.pop()
        exponent += 1
    integer_digits = len(effective_digits) + max(exponent, 0)
    fraction_digits = max(-exponent, 0)
    if (
        integer_digits > MAX_TRADE_DECIMAL_INTEGER_DIGITS
        or fraction_digits > MAX_TRADE_DECIMAL_FRACTION_DIGITS
    ):
        raise ExecutionError(f"{field.upper()}_DECIMAL_OUT_OF_BOUNDS")
    if money and exponent < -2:
        raise ExecutionError(f"{field.upper()}_PRECISION_EXCEEDED")
    return decimal_text(parsed)


def create_trade_order(
    *,
    decision_snapshot_id: str,
    portfolio_aim_id: str,
    transition_event_id: str,
    instrument_id: str,
    side: str,
    quantity: Any,
    reference_price: Any,
    expected_fee: Any,
    cash_bucket: str,
    created_at: str,
) -> dict[str, Any]:
    """Create a deterministic BUY or SELL paper order for an operated portfolio."""

    for field, value in {
        "decision_snapshot_id": decision_snapshot_id,
        "portfolio_aim_id": portfolio_aim_id,
        "transition_event_id": transition_event_id,
        "instrument_id": instrument_id,
        "cash_bucket": cash_bucket,
    }.items():
        if not isinstance(value, str) or not value:
            raise ExecutionError(f"{field.upper()}_REQUIRED")
    if side not in {"BUY", "SELL"}:
        raise ExecutionError("TRADE_SIDE_INVALID")
    _timestamp(created_at, field="created_at")
    payload = {
        "decision_snapshot_id": decision_snapshot_id,
        "portfolio_aim_id": portfolio_aim_id,
        "transition_event_id": transition_event_id,
        "instrument_id": instrument_id,
        "side": side,
        "quantity": _trade_decimal_text(quantity, field="quantity", positive=True),
        "reference_price": _trade_decimal_text(
            reference_price, field="reference_price", positive=True, money=True
        ),
        "expected_fee": _trade_decimal_text(
            expected_fee, field="expected_fee", money=True
        ),
        "cash_bucket": cash_bucket,
        "created_at": created_at,
        "execution_mode": EXECUTION_MODE,
    }
    return _record_with_id("ORD", "order_id", payload)


def validate_trade_chain(
    order: Mapping[str, Any],
    order_event: Mapping[str, Any],
    fill: Mapping[str, Any],
    fill_event: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one generic BUY/SELL order and complete-fill event chain."""

    if order.get("side") not in {"BUY", "SELL"}:
        raise ExecutionError("TRADE_SIDE_INVALID")
    _verify_order_event(order, order_event)
    expected_fill = create_fill(order, order_event, filled_at=fill.get("filled_at"))
    if canonical_document_bytes(dict(fill)) != canonical_document_bytes(expected_fill):
        raise ExecutionError("TRADE_FILL_PROJECTION_MISMATCH")
    _verify_fill_event(fill, fill_event)
    if fill_event["sequence"] <= order_event["sequence"]:
        raise ExecutionError("TRADE_FILL_NOT_AFTER_ORDER")
    return {
        "order_id": order["order_id"],
        "order_created_event_id": order_event["event_id"],
        "fill_id": fill["fill_id"],
        "fill_completed_event_id": fill_event["event_id"],
        "side": order["side"],
        "instrument_id": order["instrument_id"],
    }


def emit_trade_chain(
    *,
    decision_snapshot_id: str,
    portfolio_aim_id: str,
    transition_event_id: str,
    instrument_id: str,
    side: str,
    quantity: Any,
    reference_price: Any,
    expected_fee: Any,
    cash_bucket: str,
    start_sequence: int,
    order_created_at: str,
    filled_at: str,
) -> dict[str, Any]:
    """Emit a complete deterministic BUY or SELL paper trade chain."""

    if not isinstance(start_sequence, int) or isinstance(start_sequence, bool):
        raise ExecutionError("START_SEQUENCE_INVALID")
    if start_sequence < 0:
        raise ExecutionError("START_SEQUENCE_INVALID")
    order = create_trade_order(
        decision_snapshot_id=decision_snapshot_id,
        portfolio_aim_id=portfolio_aim_id,
        transition_event_id=transition_event_id,
        instrument_id=instrument_id,
        side=side,
        quantity=quantity,
        reference_price=reference_price,
        expected_fee=expected_fee,
        cash_bucket=cash_bucket,
        created_at=order_created_at,
    )
    order_event = create_order_event(order, sequence=start_sequence)
    fill = create_fill(order, order_event, filled_at=filled_at)
    fill_event = create_fill_event(fill, sequence=start_sequence + 1)
    authority_chain = validate_trade_chain(order, order_event, fill, fill_event)
    return {
        "order": order,
        "order_created_event": order_event,
        "fill": fill,
        "fill_completed_event": fill_event,
        "events": [order_event, fill_event],
        "authority_chain": authority_chain,
    }


def _verify_fill_event(fill: Mapping[str, Any], fill_event: Mapping[str, Any]) -> None:
    _verify_record_id(fill, kind="FIL", id_key="fill_id")
    _verify_event(fill_event)
    if fill_event.get("event_type") != "FILL_COMPLETED":
        raise ExecutionError("FILL_EVENT_TYPE_INVALID")
    if fill_event.get("source_identity") != fill.get("fill_id"):
        raise ExecutionError("FILL_EVENT_SOURCE_MISMATCH")
    if fill_event.get("effective_at") != fill.get("filled_at"):
        raise ExecutionError("FILL_EVENT_TIMESTAMP_MISMATCH")
    if fill_event.get("instrument_id") != fill.get("instrument_id"):
        raise ExecutionError("FILL_EVENT_INSTRUMENT_MISMATCH")
    if fill_event.get("cash_bucket") != fill.get("cash_bucket"):
        raise ExecutionError("FILL_EVENT_CASH_BUCKET_MISMATCH")
    payload_fill = fill_event.get("payload", {}).get("fill")
    if not isinstance(payload_fill, Mapping) or canonical_document_bytes(
        dict(payload_fill)
    ) != canonical_document_bytes(dict(fill)):
        raise ExecutionError("FILL_EVENT_PAYLOAD_MISMATCH")


def _single_event(
    events: Iterable[Mapping[str, Any]], event_type: str
) -> Mapping[str, Any]:
    matches = [event for event in events if event.get("event_type") == event_type]
    if len(matches) != 1:
        raise ExecutionError(f"EXACTLY_ONE_{event_type}_REQUIRED")
    return matches[0]


def emit_execution_chain(
    decision_snapshot: Mapping[str, Any],
    portfolio_aim: Mapping[str, Any],
    *,
    current_quantity: Any,
    cash_bucket: str,
    start_sequence: int,
    aim_confirmed_at: str,
    transition_effective_at: str,
    order_created_at: str,
    filled_at: str,
) -> dict[str, Any]:
    """Emit one complete, validated Slice 0 execution chain.

    The returned object contains immutable records and events only. Accounting,
    persistence, certification, and product projection remain downstream owners.
    """

    if not isinstance(start_sequence, int) or isinstance(start_sequence, bool):
        raise ExecutionError("START_SEQUENCE_INVALID")
    if start_sequence < 0:
        raise ExecutionError("START_SEQUENCE_INVALID")
    selection = _handoff(decision_snapshot, portfolio_aim)
    aim_event = create_aim_confirmation_event(
        decision_snapshot,
        portfolio_aim,
        sequence=start_sequence,
        effective_at=aim_confirmed_at,
    )
    transition_event = create_transition_event(
        decision_snapshot,
        portfolio_aim,
        current_quantity=current_quantity,
        cash_bucket=cash_bucket,
        sequence=start_sequence + 1,
        effective_at=transition_effective_at,
    )
    events: list[dict[str, Any]] = [aim_event, transition_event]
    order: dict[str, Any] | None = None
    fill: dict[str, Any] | None = None
    order_event: dict[str, Any] | None = None
    fill_event: dict[str, Any] | None = None

    if selection["action"] == "BUY":
        order = create_order(
            decision_snapshot,
            portfolio_aim,
            transition_event,
            created_at=order_created_at,
        )
        order_event = create_order_event(order, sequence=start_sequence + 2)
        fill = create_fill(order, order_event, filled_at=filled_at)
        fill_event = create_fill_event(fill, sequence=start_sequence + 3)
        events.extend([order_event, fill_event])

    authority_chain = validate_execution_chain(
        decision_snapshot,
        portfolio_aim,
        events,
        order=order,
        fill=fill,
    )
    return {
        "aim_confirmation_event": aim_event,
        "transition_event": transition_event,
        "order": order,
        "order_created_event": order_event,
        "fill": fill,
        "fill_completed_event": fill_event,
        "events": events,
        "authority_chain": authority_chain,
    }


def validate_execution_chain(
    decision_snapshot: Mapping[str, Any],
    portfolio_aim: Mapping[str, Any],
    events: Iterable[Mapping[str, Any]],
    *,
    order: Mapping[str, Any] | None,
    fill: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Validate every ownership edge from decision through immutable fill event."""

    selection = _handoff(decision_snapshot, portfolio_aim)
    rows = [dict(event) for event in events]
    if not rows:
        raise ExecutionError("EXECUTION_EVENTS_REQUIRED")
    for event in rows:
        _verify_event(event)
    sequences = [event["sequence"] for event in rows]
    if sequences != sorted(sequences) or len(sequences) != len(set(sequences)):
        raise ExecutionError("EXECUTION_EVENT_ORDER_INVALID")
    event_ids = [event["event_id"] for event in rows]
    if len(event_ids) != len(set(event_ids)):
        raise ExecutionError("DUPLICATE_EXECUTION_EVENT_ID")

    aim_event = _single_event(rows, "PORTFOLIO_AIM_CONFIRMED")
    transition_event = _single_event(rows, "PORTFOLIO_TRANSITION_PLANNED")
    expected_aim_event = create_aim_confirmation_event(
        decision_snapshot,
        portfolio_aim,
        sequence=aim_event["sequence"],
        effective_at=aim_event["effective_at"],
    )
    if canonical_document_bytes(aim_event) != canonical_document_bytes(
        expected_aim_event
    ):
        raise ExecutionError("AIM_CONFIRMATION_EVENT_MISMATCH")
    transition = _verify_transition_event(
        decision_snapshot, portfolio_aim, transition_event
    )
    if aim_event["sequence"] >= transition_event["sequence"]:
        raise ExecutionError("TRANSITION_NOT_AFTER_AIM_CONFIRMATION")
    _require_not_before(
        transition_event["effective_at"],
        aim_event["effective_at"],
        later_field="transition_effective_at",
        earlier_field="aim_confirmed_at",
    )

    order_events = [event for event in rows if event["event_type"] == "ORDER_CREATED"]
    fill_events = [event for event in rows if event["event_type"] == "FILL_COMPLETED"]
    if selection["action"] == "CASH":
        if order is not None or fill is not None or order_events or fill_events:
            raise ExecutionError("CASH_TRANSITION_HAS_EXECUTION")
        return {
            "decision_snapshot_id": selection["decision_snapshot_id"],
            "portfolio_aim_id": selection["portfolio_aim_id"],
            "transition_event_id": transition_event["event_id"],
            "order_id": None,
            "fill_id": None,
        }

    if order is None or fill is None:
        raise ExecutionError("BUY_EXECUTION_RECORDS_REQUIRED")
    order_event = _single_event(rows, "ORDER_CREATED")
    fill_event = _single_event(rows, "FILL_COMPLETED")

    expected_order = create_order(
        decision_snapshot,
        portfolio_aim,
        transition_event,
        created_at=order.get("created_at"),
    )
    if canonical_document_bytes(dict(order)) != canonical_document_bytes(
        expected_order
    ):
        raise ExecutionError("ORDER_PROJECTION_MISMATCH")
    _verify_order_event(order, order_event)
    if order_event["sequence"] <= transition_event["sequence"]:
        raise ExecutionError("ORDER_NOT_AFTER_TRANSITION")
    if order.get("transition_event_id") != transition_event.get("event_id"):
        raise ExecutionError("ORDER_TRANSITION_BINDING_MISMATCH")

    expected_fill = create_fill(
        order, order_event, filled_at=fill.get("filled_at")
    )
    if canonical_document_bytes(dict(fill)) != canonical_document_bytes(expected_fill):
        raise ExecutionError("FILL_PROJECTION_MISMATCH")
    _verify_fill_event(fill, fill_event)
    if fill_event["sequence"] <= order_event["sequence"]:
        raise ExecutionError("FILL_NOT_AFTER_ORDER")
    if fill.get("order_id") != order.get("order_id"):
        raise ExecutionError("FILL_ORDER_BINDING_MISMATCH")
    if fill.get("order_created_event_id") != order_event.get("event_id"):
        raise ExecutionError("FILL_ORDER_EVENT_BINDING_MISMATCH")
    if transition.get("instrument_id") != order.get("instrument_id"):
        raise ExecutionError("ORDER_TRANSITION_INSTRUMENT_MISMATCH")

    return {
        "decision_snapshot_id": selection["decision_snapshot_id"],
        "portfolio_aim_id": selection["portfolio_aim_id"],
        "transition_event_id": transition_event["event_id"],
        "order_id": order["order_id"],
        "order_created_event_id": order_event["event_id"],
        "fill_id": fill["fill_id"],
        "fill_completed_event_id": fill_event["event_id"],
    }
