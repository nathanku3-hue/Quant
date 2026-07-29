from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import pytest

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.execution import (
    ExecutionError,
    create_aim_confirmation_event,
    create_fill,
    create_fill_event,
    create_order,
    create_order_event,
    create_transition_event,
    emit_execution_chain,
    validate_execution_chain,
)
from gv_portfolio_v0.vertical import build_draft_workspace

ID_DOMAIN = "GV-PORTFOLIO-V0"


def _rehash(kind: str, id_key: str, record: Mapping[str, Any]) -> dict[str, Any]:
    body = {key: value for key, value in record.items() if key != id_key}
    return {
        id_key: f"{kind}_" + domain_hash(f"{ID_DOMAIN}:{kind}:V1", body),
        **body,
    }


def _buy_chain() -> dict[str, Any]:
    workspace = build_draft_workspace()
    snapshot = workspace["decision_snapshot"]
    aim = workspace["portfolio_aim"]
    aim_event = create_aim_confirmation_event(
        snapshot,
        aim,
        sequence=4,
        effective_at="2026-07-20T09:05:30.000000Z",
    )
    transition_event = create_transition_event(
        snapshot,
        aim,
        current_quantity="0",
        cash_bucket="AVAILABLE",
        sequence=5,
        effective_at="2026-07-20T09:05:45.000000Z",
    )
    order = create_order(
        snapshot,
        aim,
        transition_event,
        created_at="2026-07-20T09:06:00.000000Z",
    )
    order_event = create_order_event(order, sequence=6)
    fill = create_fill(
        order, order_event, filled_at="2026-07-20T09:06:01.000000Z"
    )
    fill_event = create_fill_event(fill, sequence=7)
    return {
        "workspace": workspace,
        "snapshot": snapshot,
        "aim": aim,
        "events": [aim_event, transition_event, order_event, fill_event],
        "transition_event": transition_event,
        "order": order,
        "order_event": order_event,
        "fill": fill,
        "fill_event": fill_event,
    }


def test_safe_emitter_returns_only_validated_execution_authority() -> None:
    workspace = build_draft_workspace()
    emitted = emit_execution_chain(
        workspace["decision_snapshot"],
        workspace["portfolio_aim"],
        current_quantity="0",
        cash_bucket="AVAILABLE",
        start_sequence=4,
        aim_confirmed_at="2026-07-20T09:05:30.000000Z",
        transition_effective_at="2026-07-20T09:05:45.000000Z",
        order_created_at="2026-07-20T09:06:00.000000Z",
        filled_at="2026-07-20T09:06:01.000000Z",
    )

    assert [row["event_type"] for row in emitted["events"]] == [
        "PORTFOLIO_AIM_CONFIRMED",
        "PORTFOLIO_TRANSITION_PLANNED",
        "ORDER_CREATED",
        "FILL_COMPLETED",
    ]
    assert emitted["authority_chain"]["order_id"] == emitted["order"]["order_id"]
    assert emitted["authority_chain"]["fill_id"] == emitted["fill"]["fill_id"]
    assert "book" not in emitted
    assert "certification" not in emitted


def test_complete_execution_chain_is_deterministic_and_event_only() -> None:
    first = _buy_chain()
    second = _buy_chain()
    snapshot_before = canonical_document_bytes(first["snapshot"])
    aim_before = canonical_document_bytes(first["aim"])

    chain = validate_execution_chain(
        first["snapshot"],
        first["aim"],
        first["events"],
        order=first["order"],
        fill=first["fill"],
    )

    assert canonical_document_bytes(first["events"]) == canonical_document_bytes(
        second["events"]
    )
    assert canonical_document_bytes(first["order"]) == canonical_document_bytes(
        second["order"]
    )
    assert canonical_document_bytes(first["fill"]) == canonical_document_bytes(
        second["fill"]
    )
    assert chain["decision_snapshot_id"] == first["snapshot"][
        "decision_snapshot_id"
    ]
    assert chain["transition_event_id"] == first["transition_event"]["event_id"]
    assert chain["order_id"] == first["order"]["order_id"]
    assert chain["fill_id"] == first["fill"]["fill_id"]
    assert all("book" not in event for event in first["events"])
    assert canonical_document_bytes(first["snapshot"]) == snapshot_before
    assert canonical_document_bytes(first["aim"]) == aim_before


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("decision_snapshot_id", "DSN_FORGED", "ORDER_PROJECTION_MISMATCH"),
        ("portfolio_aim_id", "AIM_FORGED", "ORDER_PROJECTION_MISMATCH"),
        ("transition_event_id", "EVT_FORGED", "ORDER_PROJECTION_MISMATCH"),
        ("instrument_id", "INS_FORGED", "ORDER_PROJECTION_MISMATCH"),
    ],
)
def test_validly_rehashed_forged_order_is_rejected(
    field: str, value: str, error: str
) -> None:
    chain = _buy_chain()
    forged = deepcopy(chain["order"])
    forged[field] = value
    forged = _rehash("ORD", "order_id", forged)

    with pytest.raises(ExecutionError, match=error):
        validate_execution_chain(
            chain["snapshot"],
            chain["aim"],
            chain["events"],
            order=forged,
            fill=chain["fill"],
        )


def test_validly_rehashed_order_event_with_contradictory_payload_is_rejected() -> None:
    chain = _buy_chain()
    forged_order = deepcopy(chain["order"])
    forged_order["quantity"] = "6"
    forged_order = _rehash("ORD", "order_id", forged_order)
    forged_event = deepcopy(chain["order_event"])
    forged_event["payload"] = {"order": forged_order}
    forged_event = _rehash("EVT", "event_id", forged_event)
    events = [chain["events"][0], chain["events"][1], forged_event, chain["events"][3]]

    with pytest.raises(ExecutionError, match="ORDER_EVENT_PAYLOAD_MISMATCH"):
        validate_execution_chain(
            chain["snapshot"],
            chain["aim"],
            events,
            order=chain["order"],
            fill=chain["fill"],
        )


def test_validly_rehashed_aim_event_with_wrong_snapshot_is_rejected() -> None:
    chain = _buy_chain()
    forged_event = deepcopy(chain["events"][0])
    forged_event["payload"]["decision_snapshot_id"] = "DSN_FORGED"
    forged_event = _rehash("EVT", "event_id", forged_event)
    events = [forged_event, *chain["events"][1:]]

    with pytest.raises(ExecutionError, match="AIM_CONFIRMATION_EVENT_MISMATCH"):
        validate_execution_chain(
            chain["snapshot"],
            chain["aim"],
            events,
            order=chain["order"],
            fill=chain["fill"],
        )


def test_validly_rehashed_transition_with_wrong_aim_is_rejected() -> None:
    chain = _buy_chain()
    forged_event = deepcopy(chain["transition_event"])
    forged_event["payload"]["transition"]["portfolio_aim_id"] = "AIM_FORGED"
    forged_event = _rehash("EVT", "event_id", forged_event)
    events = [chain["events"][0], forged_event, *chain["events"][2:]]

    with pytest.raises(ExecutionError, match="TRANSITION_PROJECTION_MISMATCH"):
        validate_execution_chain(
            chain["snapshot"],
            chain["aim"],
            events,
            order=chain["order"],
            fill=chain["fill"],
        )


def test_order_event_timestamp_must_equal_bound_order() -> None:
    chain = _buy_chain()
    forged_event = deepcopy(chain["order_event"])
    forged_event["effective_at"] = "2026-07-20T09:06:00.500000Z"
    forged_event = _rehash("EVT", "event_id", forged_event)
    events = [chain["events"][0], chain["events"][1], forged_event, chain["events"][3]]

    with pytest.raises(ExecutionError, match="ORDER_EVENT_TIMESTAMP_MISMATCH"):
        validate_execution_chain(
            chain["snapshot"],
            chain["aim"],
            events,
            order=chain["order"],
            fill=chain["fill"],
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("order_id", "ORD_FORGED"),
        ("order_created_event_id", "EVT_FORGED"),
        ("instrument_id", "INS_FORGED"),
        ("quantity", "4"),
        ("price", "41"),
        ("fee", "2"),
    ],
)
def test_validly_rehashed_forged_fill_is_rejected(field: str, value: str) -> None:
    chain = _buy_chain()
    forged = deepcopy(chain["fill"])
    forged[field] = value
    forged = _rehash("FIL", "fill_id", forged)

    with pytest.raises(ExecutionError, match="FILL_PROJECTION_MISMATCH"):
        validate_execution_chain(
            chain["snapshot"],
            chain["aim"],
            chain["events"],
            order=chain["order"],
            fill=forged,
        )


def test_validly_rehashed_fill_event_with_contradictory_payload_is_rejected() -> None:
    chain = _buy_chain()
    forged_fill = deepcopy(chain["fill"])
    forged_fill["quantity"] = "4"
    forged_fill = _rehash("FIL", "fill_id", forged_fill)
    forged_event = deepcopy(chain["fill_event"])
    forged_event["payload"] = {"fill": forged_fill}
    forged_event = _rehash("EVT", "event_id", forged_event)
    events = [*chain["events"][:3], forged_event]

    with pytest.raises(ExecutionError, match="FILL_EVENT_PAYLOAD_MISMATCH"):
        validate_execution_chain(
            chain["snapshot"],
            chain["aim"],
            events,
            order=chain["order"],
            fill=chain["fill"],
        )


def test_fill_event_timestamp_must_equal_bound_fill() -> None:
    chain = _buy_chain()
    forged_event = deepcopy(chain["fill_event"])
    forged_event["effective_at"] = "2026-07-20T09:06:02.000000Z"
    forged_event = _rehash("EVT", "event_id", forged_event)
    events = [*chain["events"][:3], forged_event]

    with pytest.raises(ExecutionError, match="FILL_EVENT_TIMESTAMP_MISMATCH"):
        validate_execution_chain(
            chain["snapshot"],
            chain["aim"],
            events,
            order=chain["order"],
            fill=chain["fill"],
        )


def test_fill_before_order_fails_closed() -> None:
    chain = _buy_chain()
    with pytest.raises(ExecutionError, match="FILLED_AT_BEFORE_ORDER_CREATED_AT"):
        create_fill(
            chain["order"],
            chain["order_event"],
            filled_at="2026-07-20T09:05:59.000000Z",
        )


def test_event_sequence_reordering_fails_closed() -> None:
    chain = _buy_chain()
    reordered = [
        chain["events"][0],
        chain["events"][2],
        chain["events"][1],
        chain["events"][3],
    ]
    with pytest.raises(ExecutionError, match="EXECUTION_EVENT_ORDER_INVALID"):
        validate_execution_chain(
            chain["snapshot"],
            chain["aim"],
            reordered,
            order=chain["order"],
            fill=chain["fill"],
        )


def test_cash_transition_prohibits_order_and_fill() -> None:
    workspace = build_draft_workspace()
    snapshot = deepcopy(workspace["decision_snapshot"])
    competition = snapshot["capital_competition"]
    cash = next(
        row for row in competition["candidates"] if row["candidate"] == "CASH"
    )
    competition["selected_candidate"] = "CASH"
    competition["selected_instrument_id"] = None
    competition["selected_net_score_bps"] = cash["net_score_bps"]
    snapshot["selected_action"] = "CASH"
    snapshot["selected_instrument_id"] = None
    snapshot["selected_quantity"] = "0"
    snapshot["reference_price"] = "0"
    snapshot["fee"] = "0"
    snapshot = _rehash("DSN", "decision_snapshot_id", snapshot)
    aim = workspace["portfolio_aim"]
    aim_event = create_aim_confirmation_event(
        snapshot,
        aim,
        sequence=4,
        effective_at="2026-07-20T09:05:30.000000Z",
    )
    transition_event = create_transition_event(
        snapshot,
        aim,
        current_quantity="0",
        cash_bucket="AVAILABLE",
        sequence=5,
        effective_at="2026-07-20T09:05:45.000000Z",
    )

    result = validate_execution_chain(
        snapshot,
        aim,
        [aim_event, transition_event],
        order=None,
        fill=None,
    )
    assert result["order_id"] is None
    assert result["fill_id"] is None
    with pytest.raises(ExecutionError, match="CASH_TRANSITION_CANNOT_CREATE_ORDER"):
        create_order(
            snapshot,
            aim,
            transition_event,
            created_at="2026-07-20T09:06:00.000000Z",
        )
