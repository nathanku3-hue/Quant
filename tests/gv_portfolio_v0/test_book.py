from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
from gv_portfolio_v0.book import (
    PortfolioBookError,
    build_portfolio_book,
    certification_eligible,
    reduce_events,
)
from gv_portfolio_v0.vertical import build_draft_workspace, confirm_draft_workspace


def _confirmed_events() -> list[dict[str, Any]]:
    return deepcopy(confirm_draft_workspace(build_draft_workspace())["events"])


def _event_index(events: list[dict[str, Any]], event_type: str) -> int:
    return next(
        index for index, event in enumerate(events) if event["event_type"] == event_type
    )


def _mutated_fill_events(**changes: Any) -> list[dict[str, Any]]:
    events = _confirmed_events()
    index = _event_index(events, "FILL_COMPLETED")
    fill = dict(events[index]["payload"]["fill"])
    fill.update(changes)
    events[index]["payload"] = {"fill": fill}
    events[index]["event_id"] = "EVT_TEST_MUTATED_FILL"
    return events


def test_vertical_uses_reconciled_book_while_legacy_projection_remains_compatible() -> None:
    draft = build_draft_workspace()
    certified = confirm_draft_workspace(draft)
    legacy_keys = {
        "positions",
        "classified_cash",
        "total_cash",
        "position_value",
        "nav",
        "valuation_status",
        "split_value_residual",
        "declared_precision",
    }

    for workspace in (draft, certified):
        rich = build_portfolio_book(workspace["events"])
        legacy = reduce_events(workspace["events"])
        assert canonical_document_bytes(rich) == canonical_document_bytes(
            workspace["book"]
        )
        assert {key: legacy[key] for key in legacy_keys} == {
            key: rich[key] for key in legacy_keys
        }


def test_transition_plan_is_non_economic_for_accounting() -> None:
    events = _confirmed_events()
    without_transition = [
        deepcopy(event)
        for event in events
        if event["event_type"] != "PORTFOLIO_TRANSITION_PLANNED"
    ]
    for sequence, event in enumerate(without_transition):
        event["sequence"] = sequence

    assert build_portfolio_book(events) == build_portfolio_book(without_transition)


def test_reconciled_book_exposes_explicit_costs_and_zero_residual() -> None:
    book = build_portfolio_book(_confirmed_events())

    assert book["opening_nav"] == "1500"
    assert book["classified_cash"] == [
        {"bucket": "AVAILABLE", "amount": "774"},
        {"bucket": "RESEARCH_RESERVE", "amount": "25"},
    ]
    assert book["classified_costs"] == [
        {
            "classification": "EXECUTION_FEE",
            "fill_id": book["classified_costs"][0]["fill_id"],
            "order_id": book["classified_costs"][0]["order_id"],
            "cash_bucket": "AVAILABLE",
            "amount": "1",
        }
    ]
    assert book["total_costs"] == "1"
    assert book["position_value"] == "700"
    assert book["terminal_nav"] == "1499"
    assert book["split_value_residual"] == "0"
    assert book["unexplained_residual"] == "0"
    assert book["reconciliation_status"] == "RECONCILED"
    assert book["all_positions_nonnegative"] is True
    assert book["classified_cash_nonnegative"] is True
    assert book["execution_relationships_valid"] is True
    assert certification_eligible(book) is True


@pytest.mark.parametrize("quantity", ["-2", "0"])
def test_nonpositive_fill_quantity_is_rejected_before_mutation(quantity: str) -> None:
    with pytest.raises(PortfolioBookError, match="POSITIVE_QUANTITY_REQUIRED:fill.quantity"):
        build_portfolio_book(_mutated_fill_events(quantity=quantity))


def test_complete_fill_must_equal_order_quantity() -> None:
    with pytest.raises(PortfolioBookError, match="COMPLETE_FILL_QUANTITY_MISMATCH"):
        build_portfolio_book(_mutated_fill_events(quantity="4"))


def test_complete_order_cannot_be_filled_twice() -> None:
    events = _confirmed_events()
    fill_index = _event_index(events, "FILL_COMPLETED")
    certification_index = _event_index(events, "CERTIFICATION_RECORDED")
    duplicate = deepcopy(events[fill_index])
    duplicate["sequence"] = events[certification_index]["sequence"]
    duplicate["event_id"] = "EVT_TEST_DUPLICATE_COMPLETE_FILL"
    duplicate["payload"]["fill"]["fill_id"] = "FIL_TEST_SECOND_COMPLETE_FILL"
    events[certification_index]["sequence"] += 1
    events.insert(certification_index, duplicate)

    with pytest.raises(PortfolioBookError, match="ORDER_ALREADY_COMPLETELY_FILLED"):
        build_portfolio_book(events)


def test_fill_instrument_must_match_event_and_order() -> None:
    with pytest.raises(PortfolioBookError, match="FILL_EVENT_INSTRUMENT_MISMATCH"):
        build_portfolio_book(_mutated_fill_events(instrument_id="INS_FORGED"))


def test_fill_bucket_must_match_event_envelope() -> None:
    with pytest.raises(PortfolioBookError, match="FILL_EVENT_CASH_BUCKET_MISMATCH"):
        build_portfolio_book(_mutated_fill_events(cash_bucket="RESEARCH_RESERVE"))


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("fee", "-1", "NONNEGATIVE_REQUIRED:fill.fee"),
        ("price", "-1", "NONNEGATIVE_REQUIRED:fill.price"),
        ("fee", "NaN", "DECIMAL_FINITE_REQUIRED:fill.fee"),
        ("fee", "0.001", "DECLARED_PRECISION_EXCEEDED:fill.fee"),
    ],
)
def test_invalid_fill_decimal_is_rejected(field: str, value: str, error: str) -> None:
    with pytest.raises(PortfolioBookError, match=error):
        build_portfolio_book(_mutated_fill_events(**{field: value}))


def test_binary_float_is_rejected_from_economic_state() -> None:
    events = deepcopy(build_draft_workspace()["events"])
    events[0]["payload"]["amount"] = 975.0
    events[0]["event_id"] = "EVT_TEST_FLOAT"

    with pytest.raises(
        PortfolioBookError, match="BINARY_FLOAT_OR_BOOL_FORBIDDEN:cash_opening.amount"
    ):
        build_portfolio_book(events)


def test_overprecision_opening_cash_is_rejected() -> None:
    events = deepcopy(build_draft_workspace()["events"])
    events[0]["payload"]["amount"] = "975.001"
    events[0]["event_id"] = "EVT_TEST_OVERPRECISION"

    with pytest.raises(
        PortfolioBookError, match="DECLARED_PRECISION_EXCEEDED:cash_opening.amount"
    ):
        build_portfolio_book(events)


def test_classified_cash_underflow_is_rejected() -> None:
    with pytest.raises(PortfolioBookError, match="INSUFFICIENT_CLASSIFIED_CASH"):
        build_portfolio_book(_mutated_fill_events(price="1000"))


def test_duplicate_opening_position_is_rejected() -> None:
    events = deepcopy(build_draft_workspace()["events"])
    original = deepcopy(events[2])
    duplicate = deepcopy(original)
    duplicate["sequence"] = 3
    duplicate["event_id"] = "EVT_TEST_DUPLICATE_POSITION"
    events[3]["sequence"] = 4
    events.insert(3, duplicate)

    with pytest.raises(PortfolioBookError, match="DUPLICATE_OPENING_POSITION"):
        build_portfolio_book(events)


def test_exact_two_for_one_split_has_zero_value_residual() -> None:
    book = build_portfolio_book(build_draft_workspace()["events"])

    assert book["positions"][0]["quantity"] == "20"
    assert book["positions"][0]["valuation_price"] == "25"
    assert book["split_value_residual"] == "0"
    assert book["unexplained_residual"] == "0"


def test_missing_valuation_is_pending_and_not_certification_eligible() -> None:
    events = [
        {
            "event_id": "EVT_PENDING",
            "sequence": 0,
            "event_type": "POSITION_OPENING",
            "effective_at": "2026-07-20T00:00:00.000000Z",
            "source_identity": "TEST",
            "instrument_id": "INS_PENDING",
            "cash_bucket": None,
            "payload": {"quantity": "3", "valuation_price": None},
        }
    ]

    book = build_portfolio_book(events)

    assert book["valuation_status"] == "VALUATION_PENDING"
    assert book["reconciliation_status"] == "VALUATION_PENDING"
    assert book["position_value"] is None
    assert book["terminal_nav"] is None
    assert book["unexplained_residual"] is None
    assert certification_eligible(book) is False


def test_repeated_canonical_reduction_is_byte_and_hash_identical() -> None:
    events = _confirmed_events()

    first = build_portfolio_book(events)
    second = build_portfolio_book(events)

    assert canonical_document_bytes(first) == canonical_document_bytes(second)
    assert first["book_hash"] == second["book_hash"]


def test_declared_event_order_is_required_not_reconstructed() -> None:
    events = _confirmed_events()
    events[0], events[1] = events[1], events[0]

    with pytest.raises(PortfolioBookError, match="DECLARED_EVENT_ORDER_INVALID"):
        build_portfolio_book(events)
