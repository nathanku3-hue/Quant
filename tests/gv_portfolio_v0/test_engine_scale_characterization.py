from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
from gv_portfolio_v0.operated import (
    admit_no_change_observation,
    append_non_economic_correction,
    authorize_portfolio_transition,
    build_draft_workspace,
    confirm_initial_portfolio,
    validate_workspace,
)
from gv_portfolio_v0.operated_scenarios import (
    ENGINE_SCALE_100_SCENARIO_ID,
    ENGINE_SCALE_50_SCENARIO_ID,
    get_scenario,
)
from gv_portfolio_v0.operated_storage import ensure_workspace

SCENARIOS = (
    (ENGINE_SCALE_50_SCENARIO_ID, 50),
    (ENGINE_SCALE_100_SCENARIO_ID, 100),
)


def _full_flow(scenario_id: str) -> dict[str, object]:
    workspace = build_draft_workspace(scenario_id)
    workspace = confirm_initial_portfolio(workspace)
    workspace = admit_no_change_observation(workspace)
    workspace = authorize_portfolio_transition(workspace)
    workspace = append_non_economic_correction(workspace)
    validate_workspace(workspace)
    return workspace


@pytest.mark.parametrize(("scenario_id", "size"), SCENARIOS)
def test_characterization_scenarios_are_declarative_and_unique(
    scenario_id: str, size: int
) -> None:
    scenario = get_scenario(scenario_id)
    assert len(scenario["instruments"]) == size
    assert len({row["permanent_key"] for row in scenario["instruments"]}) == size
    assert len({row["symbol"] for row in scenario["instruments"]}) == size
    assert "Synthetic" in scenario["claim_boundary"]
    assert "not Universe acceptance" in scenario["claim_boundary"]


@pytest.mark.parametrize(("scenario_id", "size"), SCENARIOS)
def test_existing_engine_completes_characterization_in_memory(
    scenario_id: str, size: int
) -> None:
    workspace = _full_flow(scenario_id)
    assert workspace["status"] == "CORRECTED_CERTIFIED"
    assert len(workspace["instruments"]) == size
    assert workspace["book"]["unexplained_residual"] == "0"
    assert [row["side"] for row in workspace["orders"][-2:]] == ["SELL", "BUY"]
    assert len(workspace["certification_history"]) == 3

    repeated = _full_flow(scenario_id)
    assert canonical_document_bytes(repeated) == canonical_document_bytes(workspace)


@pytest.mark.parametrize(("scenario_id", "size"), SCENARIOS)
def test_existing_storage_boundary_stops_characterization_before_reopen(
    tmp_path: Path, scenario_id: str, size: int
) -> None:
    with pytest.raises(
        ValueError, match=f"UNKNOWN_OPERATED_SCENARIO:{scenario_id}"
    ):
        ensure_workspace(root=tmp_path / f"scale-{size}", scenario_id=scenario_id)


def test_100_security_characterization_exposes_timestamp_scaling_limit() -> None:
    workspace = build_draft_workspace(ENGINE_SCALE_100_SCENARIO_ID)
    invalid = []
    for row in workspace["evidence_references"]:
        observed_at = row["observed_at"]
        try:
            datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        except ValueError:
            invalid.append(observed_at)
    assert len(invalid) == 40
    assert invalid[0] == "2026-09-01T12:60:00.000000Z"
    assert invalid[-1] == "2026-09-01T12:99:00.000000Z"


def test_characterization_does_not_mutate_accepted_25_scenario() -> None:
    from gv_portfolio_v0.operated_scenarios import (
        PORTFOLIO_25_SCENARIO_ID,
        SCENARIO_25,
    )

    accepted = deepcopy(SCENARIO_25)
    get_scenario(ENGINE_SCALE_50_SCENARIO_ID)
    get_scenario(ENGINE_SCALE_100_SCENARIO_ID)
    assert get_scenario(PORTFOLIO_25_SCENARIO_ID) == accepted
