from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "contracts/gv_fs0/v1/tables"


def _rows() -> dict[str, dict[str, str]]:
    value = json.loads((TABLES / "gv_fs0_transition_ownership_v1.json").read_text(encoding="utf-8"))
    return {row["event_type"]: row for row in value["entries"]}


def test_every_v1_event_has_exactly_one_visible_ownership_row() -> None:
    rows = _rows()
    assert set(rows) == {
        "DECISION_ACCEPTED",
        "EXECUTION",
        "FEE_OR_COST",
        "CASH_MOVEMENT",
        "POSITION_MOVEMENT",
        "DIVIDEND_ENTITLEMENT",
        "DIVIDEND_PAYMENT",
        "SESSION_VALUATION",
        "CERTIFICATION_REFERENCE",
    }


def test_execution_and_fee_authority_do_not_directly_mutate_balances() -> None:
    rows = _rows()
    for event_type in ["EXECUTION", "FEE_OR_COST"]:
        row = rows[event_type]
        assert row["cash"] == "NONE"
        assert row["shares"] == "NONE"
        assert row["receivables"] == "NONE"
    assert rows["EXECUTION"]["responsibility"] == "EXECUTION_AUTHORITY_ONLY"
    assert rows["FEE_OR_COST"]["responsibility"] == "FEE_AUTHORITY_ONLY"


def test_generated_cash_and_position_movements_own_effect_once() -> None:
    rows = _rows()
    assert rows["CASH_MOVEMENT"]["cash"] == "MUTATE_ONCE"
    assert rows["CASH_MOVEMENT"]["shares"] == "NONE"
    assert rows["POSITION_MOVEMENT"]["shares"] == "MUTATE_ONCE"
    assert rows["POSITION_MOVEMENT"]["cash"] == "NONE"


def test_dividend_entitlement_and_payment_have_atomic_nonoverlapping_ownership() -> None:
    rows = _rows()
    entitlement = rows["DIVIDEND_ENTITLEMENT"]
    payment = rows["DIVIDEND_PAYMENT"]
    assert entitlement["receivables"] == "INCREASE_ONCE"
    assert entitlement["cash"] == "NONE"
    assert payment["cash"] == "INCREASE_ONCE"
    assert payment["receivables"] == "DECREASE_ONCE"
    assert payment["responsibility"] == "ATOMIC_SETTLEMENT"


def test_valuation_and_certification_reference_are_observation_only() -> None:
    rows = _rows()
    for event_type in ["SESSION_VALUATION", "CERTIFICATION_REFERENCE", "DECISION_ACCEPTED"]:
        row = rows[event_type]
        assert {row["cash"], row["shares"], row["receivables"]} == {"NONE"}


def test_dividend_payment_slot_emits_no_separate_cash_movement() -> None:
    slots = json.loads((TABLES / "gv_fs0_generated_event_slots_v1.json").read_text(encoding="utf-8"))["entries"]
    payment_rows = [row for row in slots if row["source_type"] == "DIVIDEND_PAYMENT_INSTRUCTION"]
    assert payment_rows == [
        {
            "event_type": "DIVIDEND_PAYMENT",
            "generated_event_slot": 10,
            "source_type": "DIVIDEND_PAYMENT_INSTRUCTION",
        }
    ]


def test_payment_rank_precedes_session_valuation_rank() -> None:
    ranks = {
        row["event_type"]: row["event_type_rank"]
        for row in json.loads((TABLES / "gv_fs0_event_ranks_v1.json").read_text(encoding="utf-8"))["entries"]
    }
    assert ranks["DIVIDEND_PAYMENT"] == 70
    assert ranks["SESSION_VALUATION"] == 80
    assert ranks["DIVIDEND_PAYMENT"] < ranks["SESSION_VALUATION"]


def test_no_quantity_is_unowned_or_multiply_owned_within_one_event() -> None:
    rows = _rows()
    mutation_tokens = {"MUTATE_ONCE", "INCREASE_ONCE", "DECREASE_ONCE"}
    cash_owners = {event for event, row in rows.items() if row["cash"] in mutation_tokens}
    share_owners = {event for event, row in rows.items() if row["shares"] in mutation_tokens}
    receivable_owners = {event for event, row in rows.items() if row["receivables"] in mutation_tokens}
    assert cash_owners == {"CASH_MOVEMENT", "DIVIDEND_PAYMENT"}
    assert share_owners == {"POSITION_MOVEMENT"}
    assert receivable_owners == {"DIVIDEND_ENTITLEMENT", "DIVIDEND_PAYMENT"}
