from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import pytest

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.allocation import (
    AllocationError,
    plan_transition,
    validate_execution_handoff,
)
from gv_portfolio_v0.vertical import build_draft_workspace

ID_DOMAIN = "GV-PORTFOLIO-V0"


def _rehash(kind: str, id_key: str, record: Mapping[str, Any]) -> dict[str, Any]:
    body = {key: value for key, value in record.items() if key != id_key}
    return {
        id_key: f"{kind}_" + domain_hash(f"{ID_DOMAIN}:{kind}:V1", body),
        **body,
    }


def test_execution_handoff_and_transition_are_deterministic() -> None:
    workspace = build_draft_workspace()
    snapshot = workspace["decision_snapshot"]
    aim = workspace["portfolio_aim"]
    snapshot_before = canonical_document_bytes(snapshot)
    aim_before = canonical_document_bytes(aim)

    selection = validate_execution_handoff(snapshot, aim)
    first = plan_transition(
        snapshot, aim, current_quantity="0", cash_bucket="AVAILABLE"
    )
    second = plan_transition(
        snapshot, aim, current_quantity="0", cash_bucket="AVAILABLE"
    )

    assert selection == {
        "decision_snapshot_id": snapshot["decision_snapshot_id"],
        "portfolio_aim_id": aim["portfolio_aim_id"],
        "selected_candidate": "HARBOR",
        "outcome": "ADMIT",
        "action": "BUY",
        "instrument_id": snapshot["selected_instrument_id"],
        "quantity": "5",
        "reference_price": "40",
        "fee": "1",
    }
    assert first == second
    assert first["current_quantity"] == "0"
    assert first["target_quantity"] == "5"
    assert first["quantity_delta"] == "5"
    assert canonical_document_bytes(snapshot) == snapshot_before
    assert canonical_document_bytes(aim) == aim_before


def test_validly_rehashed_snapshot_cannot_bind_another_aim() -> None:
    workspace = build_draft_workspace()
    forged = deepcopy(workspace["decision_snapshot"])
    forged["portfolio_aim_id"] = "AIM_OTHER_VALID_ID"
    forged = _rehash("DSN", "decision_snapshot_id", forged)

    with pytest.raises(AllocationError, match="SNAPSHOT_AIM_BINDING_MISMATCH"):
        validate_execution_handoff(forged, workspace["portfolio_aim"])


def test_abstain_winner_cannot_enter_execution() -> None:
    workspace = build_draft_workspace()
    forged = deepcopy(workspace["decision_snapshot"])
    competition = forged["capital_competition"]
    orbit = next(
        row for row in competition["candidates"] if row["candidate"] == "ORBIT"
    )
    competition["selected_candidate"] = "ORBIT"
    competition["selected_instrument_id"] = orbit["instrument_id"]
    competition["selected_net_score_bps"] = orbit["net_score_bps"]
    forged["selected_instrument_id"] = orbit["instrument_id"]
    forged = _rehash("DSN", "decision_snapshot_id", forged)

    with pytest.raises(AllocationError, match="EXECUTION_WINNER_INELIGIBLE"):
        validate_execution_handoff(forged, workspace["portfolio_aim"])


def test_cash_transition_has_zero_execution_economics() -> None:
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

    transition = plan_transition(
        snapshot,
        workspace["portfolio_aim"],
        current_quantity="20",
        cash_bucket="AVAILABLE",
    )

    assert transition["action"] == "CASH"
    assert transition["instrument_id"] is None
    assert transition["current_quantity"] == "20"
    assert transition["target_quantity"] == "20"
    assert transition["quantity_delta"] == "0"
    assert transition["reference_price"] == "0"
    assert transition["expected_fee"] == "0"


@pytest.mark.parametrize("current_quantity", ["-1", "NaN", "Infinity"])
def test_transition_rejects_invalid_current_quantity(current_quantity: str) -> None:
    workspace = build_draft_workspace()
    with pytest.raises(AllocationError):
        plan_transition(
            workspace["decision_snapshot"],
            workspace["portfolio_aim"],
            current_quantity=current_quantity,
            cash_bucket="AVAILABLE",
        )
