"""Deterministic accounting reducer for GV Portfolio V0.

Accounting consumes the declared canonical PortfolioBookEvent order. Custody
owns event identity; this module owns economic validation and book projection.
It applies economic validation and book projection for the declared order.
Replay 0 owns reconstruction orchestration, correction lineage reports, and
idempotence proofs. Partial fills are economically legal here when cumulative
fill quantity never exceeds the order; residual state is projected for Replay.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, DecimalException, InvalidOperation
from typing import Any, Iterable, Mapping

from core.gv_fs0_canonical import domain_hash
from gv_portfolio_v0.decimal_utils import (
    MAX_DECIMAL_FRACTION_DIGITS,
    MAX_DECIMAL_INTEGER_DIGITS,
    decimal_text,
    deterministic_decimal_context,
)

ID_DOMAIN = "GV-PORTFOLIO-V0"
DECLARED_PRECISION = "0.01"


class PortfolioBookError(ValueError):
    """Raised when an event would create invalid or unreconciled economics."""


@dataclass(frozen=True)
class _Reduction:
    positions: list[dict[str, Any]]
    classified_cash: list[dict[str, str]]
    classified_costs: list[dict[str, str]]
    total_cash: Decimal
    position_value: Decimal | None
    total_costs: Decimal
    opening_nav: Decimal | None
    terminal_nav: Decimal | None
    split_value_residual: Decimal
    unexplained_residual: Decimal | None
    valuation_pending: bool
    partial_fill_residuals: list[dict[str, str]]


def _decimal(value: Any, *, field: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise PortfolioBookError(f"BINARY_FLOAT_OR_BOOL_FORBIDDEN:{field}")
    if not isinstance(value, (str, int, Decimal)):
        raise PortfolioBookError(f"DECIMAL_TYPE_INVALID:{field}")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PortfolioBookError(f"DECIMAL_INVALID:{field}") from exc
    if not parsed.is_finite():
        raise PortfolioBookError(f"DECIMAL_FINITE_REQUIRED:{field}")
    _, digits, exponent = parsed.as_tuple()
    effective_digits = list(digits)
    while len(effective_digits) > 1 and effective_digits[-1] == 0:
        effective_digits.pop()
        exponent += 1
    integer_digits = len(effective_digits) + max(exponent, 0)
    fraction_digits = max(-exponent, 0)
    if (
        integer_digits > MAX_DECIMAL_INTEGER_DIGITS
        or fraction_digits > MAX_DECIMAL_FRACTION_DIGITS
    ):
        raise PortfolioBookError(f"DECIMAL_OUT_OF_BOUNDS:{field}")
    return parsed


def _money(value: Any, *, field: str, nonnegative: bool = True) -> Decimal:
    parsed = _decimal(value, field=field)
    _, digits, exponent = parsed.as_tuple()
    effective_digits = list(digits)
    while len(effective_digits) > 1 and effective_digits[-1] == 0:
        effective_digits.pop()
        exponent += 1
    if exponent < -2:
        raise PortfolioBookError(f"DECLARED_PRECISION_EXCEEDED:{field}")
    if nonnegative and parsed < 0:
        raise PortfolioBookError(f"NONNEGATIVE_REQUIRED:{field}")
    return parsed


def _whole_quantity(
    value: Any,
    *,
    field: str,
    positive: bool = False,
    nonnegative: bool = True,
) -> Decimal:
    parsed = _decimal(value, field=field)
    if parsed != parsed.to_integral_value():
        raise PortfolioBookError(f"WHOLE_SHARE_REQUIRED:{field}")
    if positive and parsed <= 0:
        raise PortfolioBookError(f"POSITIVE_QUANTITY_REQUIRED:{field}")
    if nonnegative and parsed < 0:
        raise PortfolioBookError(f"NONNEGATIVE_QUANTITY_REQUIRED:{field}")
    return parsed


def _positive_ratio(value: Any, *, field: str) -> Decimal:
    parsed = _decimal(value, field=field)
    if parsed <= 0:
        raise PortfolioBookError(f"POSITIVE_RATIO_REQUIRED:{field}")
    return parsed


def _decimal_text(value: Decimal | str | int) -> str:
    parsed = _decimal(value, field="canonical_decimal")
    return decimal_text(parsed)


def _required_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PortfolioBookError(f"TEXT_REQUIRED:{field}")
    return value


def _ordered_events(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(row) for row in events]
    if not rows:
        raise PortfolioBookError("EVENT_STREAM_REQUIRED")

    sequences: list[int] = []
    event_ids: list[str] = []
    for row in rows:
        sequence = row.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise PortfolioBookError("EVENT_SEQUENCE_INVALID")
        sequences.append(sequence)
        event_ids.append(_required_text(row.get("event_id"), field="event_id"))
        if not isinstance(row.get("payload"), Mapping):
            raise PortfolioBookError("EVENT_PAYLOAD_MAPPING_REQUIRED")

    if len(sequences) != len(set(sequences)):
        raise PortfolioBookError("DUPLICATE_EVENT_SEQUENCE")
    if sequences != list(range(len(rows))):
        raise PortfolioBookError("DECLARED_EVENT_ORDER_INVALID")
    if len(event_ids) != len(set(event_ids)):
        raise PortfolioBookError("DUPLICATE_EVENT_ID")
    return rows


def _reduce_with_context(events: Iterable[Mapping[str, Any]]) -> _Reduction:
    rows = _ordered_events(events)
    cash: dict[str, Decimal] = {}
    positions: dict[str, dict[str, Decimal | None]] = {}
    orders: dict[str, dict[str, Any]] = {}
    order_filled: dict[str, Decimal] = {}
    seen_fill_ids: set[str] = set()
    completely_filled_order_ids: set[str] = set()
    split_residuals: list[Decimal] = []
    costs: list[dict[str, str]] = []
    opening_cash = Decimal("0")
    opening_position_value = Decimal("0")
    opening_valuation_pending = False
    execution_started = False

    for row in rows:
        event_type = _required_text(row.get("event_type"), field="event_type")
        payload = row["payload"]
        instrument_id = row.get("instrument_id")
        cash_bucket = row.get("cash_bucket")

        if event_type == "CASH_OPENING":
            if execution_started:
                raise PortfolioBookError("OPENING_EVENT_AFTER_EXECUTION")
            bucket = _required_text(cash_bucket, field="cash_bucket")
            amount = _money(payload.get("amount"), field="cash_opening.amount")
            cash[bucket] = cash.get(bucket, Decimal("0")) + amount
            opening_cash += amount

        elif event_type == "POSITION_OPENING":
            if execution_started:
                raise PortfolioBookError("OPENING_EVENT_AFTER_EXECUTION")
            instrument = _required_text(instrument_id, field="instrument_id")
            if instrument in positions:
                raise PortfolioBookError("DUPLICATE_OPENING_POSITION")
            quantity = _whole_quantity(
                payload.get("quantity"), field="position_opening.quantity"
            )
            raw_price = payload.get("valuation_price")
            price = (
                None
                if raw_price is None
                else _money(raw_price, field="position_opening.valuation_price")
            )
            positions[instrument] = {"quantity": quantity, "valuation_price": price}
            if price is None:
                opening_valuation_pending = True
            else:
                opening_position_value += quantity * price

        elif event_type == "CORPORATE_ACTION_SPLIT":
            instrument = _required_text(instrument_id, field="instrument_id")
            if instrument not in positions:
                raise PortfolioBookError("SPLIT_POSITION_MISSING")
            position = positions[instrument]
            before_quantity = _whole_quantity(
                payload.get("pre_quantity"), field="split.pre_quantity"
            )
            before_price = _money(
                payload.get("pre_reference_price"), field="split.pre_reference_price"
            )
            if position["quantity"] != before_quantity:
                raise PortfolioBookError("SPLIT_PRE_QUANTITY_MISMATCH")
            if position["valuation_price"] != before_price:
                raise PortfolioBookError("SPLIT_PRE_PRICE_MISMATCH")
            numerator = _positive_ratio(payload.get("numerator"), field="split.numerator")
            denominator = _positive_ratio(
                payload.get("denominator"), field="split.denominator"
            )
            after_quantity = before_quantity * numerator / denominator
            if after_quantity != after_quantity.to_integral_value():
                raise PortfolioBookError("SPLIT_FRACTIONAL_SHARE_UNSUPPORTED")
            after_price = before_price * denominator / numerator
            _, split_digits, split_exponent = after_price.as_tuple()
            effective_split_digits = list(split_digits)
            while (
                len(effective_split_digits) > 1
                and effective_split_digits[-1] == 0
            ):
                effective_split_digits.pop()
                split_exponent += 1
            if split_exponent < -2:
                raise PortfolioBookError("SPLIT_PRICE_PRECISION_EXCEEDED")
            residual = after_quantity * after_price - before_quantity * before_price
            if residual != 0:
                raise PortfolioBookError("SPLIT_VALUE_NOT_PRESERVED")
            split_residuals.append(residual)
            position["quantity"] = after_quantity
            position["valuation_price"] = after_price

        elif event_type == "ORDER_CREATED":
            order = payload.get("order")
            if not isinstance(order, Mapping):
                raise PortfolioBookError("ORDER_MAPPING_REQUIRED")
            order_id = _required_text(order.get("order_id"), field="order_id")
            if order_id in orders:
                raise PortfolioBookError("DUPLICATE_ORDER_ID")
            order_instrument = _required_text(
                order.get("instrument_id"), field="order.instrument_id"
            )
            if instrument_id != order_instrument:
                raise PortfolioBookError("ORDER_EVENT_INSTRUMENT_MISMATCH")
            side = order.get("side")
            if side not in {"BUY", "SELL"}:
                raise PortfolioBookError("UNSUPPORTED_ORDER_SIDE")
            order_quantity = _whole_quantity(
                order.get("quantity"), field="order.quantity", positive=True
            )
            _money(order.get("reference_price"), field="order.reference_price")
            if side == "SELL":
                position = positions.get(order_instrument)
                if position is None:
                    raise PortfolioBookError("SELL_POSITION_MISSING")
                current_quantity = _whole_quantity(
                    position["quantity"], field="position.quantity"
                )
                if order_quantity > current_quantity:
                    raise PortfolioBookError("SELL_ORDER_EXCEEDS_POSITION")
            orders[order_id] = dict(order)

        elif event_type == "FILL_COMPLETED":
            execution_started = True
            fill = payload.get("fill")
            if not isinstance(fill, Mapping):
                raise PortfolioBookError("FILL_MAPPING_REQUIRED")
            fill_id = _required_text(fill.get("fill_id"), field="fill_id")
            if fill_id in seen_fill_ids:
                raise PortfolioBookError("DUPLICATE_FILL_ID")
            seen_fill_ids.add(fill_id)
            order_id = _required_text(fill.get("order_id"), field="fill.order_id")
            order = orders.get(order_id)
            if order is None:
                raise PortfolioBookError("FILL_ORDER_MISSING")
            if order_id in completely_filled_order_ids:
                raise PortfolioBookError("ORDER_ALREADY_COMPLETELY_FILLED")
            fill_instrument = _required_text(
                fill.get("instrument_id"), field="fill.instrument_id"
            )
            bucket = _required_text(fill.get("cash_bucket"), field="fill.cash_bucket")
            if instrument_id != fill_instrument:
                raise PortfolioBookError("FILL_EVENT_INSTRUMENT_MISMATCH")
            if cash_bucket != bucket:
                raise PortfolioBookError("FILL_EVENT_CASH_BUCKET_MISMATCH")
            if fill_instrument != order.get("instrument_id"):
                raise PortfolioBookError("FILL_ORDER_INSTRUMENT_MISMATCH")
            if fill.get("side") != order.get("side"):
                raise PortfolioBookError("FILL_ORDER_SIDE_MISMATCH")
            side = fill.get("side")
            if side not in {"BUY", "SELL"}:
                raise PortfolioBookError("UNSUPPORTED_FILL_SIDE")
            quantity = _whole_quantity(
                fill.get("quantity"), field="fill.quantity", positive=True
            )
            order_quantity = _whole_quantity(
                order.get("quantity"), field="order.quantity", positive=True
            )
            filled_so_far = order_filled.get(order_id, Decimal("0"))
            remaining = order_quantity - filled_so_far
            if quantity > remaining:
                raise PortfolioBookError("FILL_QUANTITY_EXCEEDS_REMAINING")
            new_filled = filled_so_far + quantity
            order_filled[order_id] = new_filled
            if new_filled == order_quantity:
                completely_filled_order_ids.add(order_id)
            price = _money(fill.get("price"), field="fill.price")
            fee = _money(fill.get("fee"), field="fill.fee")
            available = cash.get(bucket, Decimal("0"))
            position = positions.setdefault(
                fill_instrument,
                {"quantity": Decimal("0"), "valuation_price": None},
            )
            current_quantity = _whole_quantity(
                position["quantity"], field="position.quantity"
            )
            if side == "BUY":
                required_cash = quantity * price + fee
                if available < required_cash:
                    raise PortfolioBookError("INSUFFICIENT_CLASSIFIED_CASH")
                cash[bucket] = available - required_cash
                resulting_quantity = current_quantity + quantity
            else:
                if quantity > current_quantity:
                    raise PortfolioBookError("SELL_FILL_EXCEEDS_POSITION")
                proceeds_after_fee = quantity * price - fee
                resulting_cash = available + proceeds_after_fee
                if resulting_cash < 0:
                    raise PortfolioBookError("NEGATIVE_CLASSIFIED_CASH_FORBIDDEN")
                cash[bucket] = resulting_cash
                resulting_quantity = current_quantity - quantity
            if resulting_quantity < 0:
                raise PortfolioBookError("NEGATIVE_POSITION_FORBIDDEN")
            position["quantity"] = resulting_quantity
            position["valuation_price"] = price
            costs.append(
                {
                    "classification": "EXECUTION_FEE",
                    "fill_id": fill_id,
                    "order_id": order_id,
                    "cash_bucket": bucket,
                    "amount": _decimal_text(fee),
                }
            )

        elif event_type in {
            "PORTFOLIO_AIM_CONFIRMED",
            "PORTFOLIO_TRANSITION_PLANNED",
            "LATER_OBSERVATION_ADMITTED",
            "PROSPECTIVE_PROPOSAL_REJECTED",
            "CERTIFICATION_RECORDED",
            "CORRECTION_RECORDED",
        }:
            continue
        else:
            raise PortfolioBookError(f"UNSUPPORTED_EVENT_TYPE:{event_type}")

    cash_rows = [
        {"bucket": bucket, "amount": _decimal_text(amount)}
        for bucket, amount in sorted(cash.items())
    ]
    total_cash = sum(cash.values(), Decimal("0"))
    if any(amount < 0 for amount in cash.values()):
        raise PortfolioBookError("NEGATIVE_CLASSIFIED_CASH_FORBIDDEN")

    position_rows: list[dict[str, Any]] = []
    valuation_pending = False
    terminal_position_value = Decimal("0")
    for instrument, position in sorted(positions.items()):
        quantity = _whole_quantity(position["quantity"], field="position.quantity")
        if quantity < 0:
            raise PortfolioBookError("NEGATIVE_POSITION_FORBIDDEN")
        price = position["valuation_price"]
        if price is None:
            market_value = None
            valuation_pending = True
        else:
            canonical_price = _money(price, field="position.valuation_price")
            market_value = quantity * canonical_price
            terminal_position_value += market_value
        position_rows.append(
            {
                "instrument_id": instrument,
                "quantity": _decimal_text(quantity),
                "valuation_price": (
                    None if price is None else _decimal_text(_decimal(price, field="price"))
                ),
                "market_value": (
                    None if market_value is None else _decimal_text(market_value)
                ),
            }
        )

    total_costs = sum(
        (_decimal(row["amount"], field="classified_cost.amount") for row in costs),
        Decimal("0"),
    )
    opening_nav = (
        None
        if opening_valuation_pending
        else opening_cash + opening_position_value
    )
    terminal_nav = (
        None
        if valuation_pending
        else total_cash + terminal_position_value
    )
    unexplained_residual = (
        None
        if opening_nav is None or terminal_nav is None
        else terminal_nav - (opening_nav - total_costs)
    )

    partial_fill_residuals: list[dict[str, str]] = []
    for order_id, order in sorted(orders.items()):
        order_quantity = _whole_quantity(
            order.get("quantity"), field="order.quantity", positive=True
        )
        filled = order_filled.get(order_id, Decimal("0"))
        residual = order_quantity - filled
        if residual > 0:
            partial_fill_residuals.append(
                {
                    "order_id": order_id,
                    "instrument_id": _required_text(
                        order.get("instrument_id"), field="order.instrument_id"
                    ),
                    "ordered_quantity": _decimal_text(order_quantity),
                    "filled_quantity": _decimal_text(filled),
                    "residual_quantity": _decimal_text(residual),
                }
            )

    return _Reduction(
        positions=position_rows,
        classified_cash=cash_rows,
        classified_costs=costs,
        total_cash=total_cash,
        position_value=None if valuation_pending else terminal_position_value,
        total_costs=total_costs,
        opening_nav=opening_nav,
        terminal_nav=terminal_nav,
        split_value_residual=sum(split_residuals, Decimal("0")),
        unexplained_residual=unexplained_residual,
        valuation_pending=valuation_pending,
        partial_fill_residuals=partial_fill_residuals,
    )


def _reduce(events: Iterable[Mapping[str, Any]]) -> _Reduction:
    """Reduce with enough precision that ambient caller context cannot alter it."""

    try:
        with deterministic_decimal_context():
            return _reduce_with_context(events)
    except DecimalException as exc:
        raise PortfolioBookError("DECIMAL_ARITHMETIC_INVALID") from exc


def build_portfolio_book(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return the reconciled deterministic PortfolioBook projection."""

    reduced = _reduce(events)
    if reduced.valuation_pending:
        reconciliation_status = "VALUATION_PENDING"
    elif reduced.unexplained_residual == 0 and reduced.split_value_residual == 0:
        reconciliation_status = "RECONCILED"
    else:
        reconciliation_status = "UNRECONCILED"

    book = {
        "positions": reduced.positions,
        "classified_cash": reduced.classified_cash,
        "classified_costs": reduced.classified_costs,
        "total_cash": _decimal_text(reduced.total_cash),
        "total_costs": _decimal_text(reduced.total_costs),
        "opening_nav": (
            None if reduced.opening_nav is None else _decimal_text(reduced.opening_nav)
        ),
        "position_value": (
            None
            if reduced.position_value is None
            else _decimal_text(reduced.position_value)
        ),
        "terminal_nav": (
            None if reduced.terminal_nav is None else _decimal_text(reduced.terminal_nav)
        ),
        "nav": (
            None if reduced.terminal_nav is None else _decimal_text(reduced.terminal_nav)
        ),
        "valuation_status": (
            "VALUATION_PENDING" if reduced.valuation_pending else "COMPLETE"
        ),
        "split_value_residual": _decimal_text(reduced.split_value_residual),
        "unexplained_residual": (
            None
            if reduced.unexplained_residual is None
            else _decimal_text(reduced.unexplained_residual)
        ),
        "reconciliation_status": reconciliation_status,
        "all_positions_nonnegative": all(
            _decimal(row["quantity"], field="position.quantity") >= 0
            for row in reduced.positions
        ),
        "classified_cash_nonnegative": all(
            _decimal(row["amount"], field="classified_cash.amount") >= 0
            for row in reduced.classified_cash
        ),
        "execution_relationships_valid": True,
        "declared_precision": DECLARED_PRECISION,
        "partial_fill_residuals": reduced.partial_fill_residuals,
    }
    # Hash excludes partial residuals so Slice 0 complete-fill certs stay stable;
    # residuals are authoritative for Replay reports via explicit field access.
    hash_body = {key: value for key, value in book.items() if key != "partial_fill_residuals"}
    book["book_hash"] = domain_hash(f"{ID_DOMAIN}:BOOK:V2", hash_body)
    return book


def certification_eligible(book: Mapping[str, Any]) -> bool:
    """Return whether the reconciled book satisfies Slice 0 accounting gates."""

    return bool(
        book.get("valuation_status") == "COMPLETE"
        and book.get("reconciliation_status") == "RECONCILED"
        and book.get("unexplained_residual") == "0"
        and book.get("split_value_residual") == "0"
        and book.get("all_positions_nonnegative") is True
        and book.get("classified_cash_nonnegative") is True
        and book.get("execution_relationships_valid") is True
        and book.get("terminal_nav") is not None
    )
