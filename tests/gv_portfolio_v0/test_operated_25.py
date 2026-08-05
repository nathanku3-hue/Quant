from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
from gv_portfolio_v0.operated import (
    OperatedPortfolioError,
    STATUS_CORRECTED,
    STATUS_DRAFT,
    STATUS_FUNDED,
    STATUS_NO_CHANGE,
    STATUS_TRANSITION,
    admit_no_change_observation,
    append_non_economic_correction,
    authorize_portfolio_transition,
    build_draft_workspace,
    confirm_initial_portfolio,
    validate_workspace,
)
from gv_portfolio_v0.operated_scenarios import (
    DEFAULT_SCENARIO_ID,
    PORTFOLIO_25_SCENARIO_ID,
)
from gv_portfolio_v0.operated_storage import (
    admit_no_change_and_persist,
    append_correction_and_persist,
    authorize_transition_and_persist,
    confirm_and_persist,
    ensure_workspace,
    load_workspace,
    workspace_path,
)
from gv_portfolio_v0.replay import reconstruct_exact, replay_idempotent

ROOT = Path(__file__).resolve().parents[2]


def _full_25_flow() -> dict[str, object]:
    workspace = build_draft_workspace(PORTFOLIO_25_SCENARIO_ID)
    workspace = confirm_initial_portfolio(workspace)
    workspace = admit_no_change_observation(workspace)
    workspace = authorize_portfolio_transition(workspace)
    return append_non_economic_correction(workspace)


def test_25_scenario_is_one_real_portfolio_with_exact_breadth_and_ownership() -> None:
    workspace = build_draft_workspace(PORTFOLIO_25_SCENARIO_ID)
    assert workspace["status"] == STATUS_DRAFT
    assert workspace["portfolio_count"] == 1
    assert len(workspace["instruments"]) == 25
    assert len({row["instrument_id"] for row in workspace["instruments"]}) == 25
    assert len({row["permanent_key"] for row in workspace["instruments"]}) == 25
    assert len({row["economic_cluster"] for row in workspace["instruments"]}) >= 2

    instrument_ids = {row["instrument_id"] for row in workspace["instruments"]}
    initial_evidence = workspace["evidence_references"][:25]
    assert len(initial_evidence) == 25
    assert len({row["evidence_reference_id"] for row in initial_evidence}) == 25
    assert {
        row["owned_instrument_ids"][0] for row in initial_evidence
    } == instrument_ids
    assert all(len(row["owned_instrument_ids"]) == 1 for row in initial_evidence)

    reviews = workspace["reviews"]
    assert len(reviews) == 25
    assert {row["instrument_id"] for row in reviews} == instrument_ids
    assert all(
        row["living_thesis_lite"]["instrument_id"] == row["instrument_id"]
        for row in reviews
    )
    assert len(
        {row["living_thesis_lite"]["thesis_id"] for row in reviews}
    ) == 25

    candidates = workspace["current_decision_snapshot"]["capital_competition"][
        "candidates"
    ]
    candidate_ids = [row["instrument_id"] for row in candidates]
    assert len(candidate_ids) == 25
    assert len(set(candidate_ids)) == 25
    assert set(candidate_ids) == instrument_ids


def test_identical_thesis_content_keeps_independent_ownership_and_identity() -> None:
    workspace = build_draft_workspace(PORTFOLIO_25_SCENARIO_ID)
    duplicated_claim = "Leverage violates the mandate screen."
    matches = [
        row
        for row in workspace["reviews"]
        if row["living_thesis_lite"]["principal_claim"] == duplicated_claim
    ]
    assert len(matches) == 2
    assert len({row["instrument_id"] for row in matches}) == 2
    assert len(
        {row["living_thesis_lite"]["thesis_id"] for row in matches}
    ) == 2


def test_shared_engine_has_no_fixture_symbol_authority_or_parallel_stack() -> None:
    for relative in (
        "gv_portfolio_v0/operated.py",
        "gv_portfolio_v0/operated_storage.py",
        "views/gv_operated_portfolio_workspace.py",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert '"HARBOR"' not in text
        assert '"MERID"' not in text
        assert "EXACTLY_TEN" not in text
    for relative in (
        "gv_portfolio_v0/operated25.py",
        "gv_portfolio_v0/operated25_storage.py",
        "views/gv_operated_portfolio_25_workspace.py",
        "operated_portfolio_25_app.py",
    ):
        assert not (ROOT / relative).exists()


def test_scenario_definition_and_persisted_binding_fail_closed(
    tmp_path: Path,
) -> None:
    workspace = build_draft_workspace(PORTFOLIO_25_SCENARIO_ID)
    forged_workspace = deepcopy(workspace)
    forged_workspace["scenario_hash"] = "FORGED"
    with pytest.raises(
        OperatedPortfolioError, match="WORKSPACE_SCENARIO_HASH_MISMATCH"
    ):
        validate_workspace(forged_workspace, allow_draft=True)

    root = tmp_path / "scenario-bound"
    ensure_workspace(root=root, scenario_id=PORTFOLIO_25_SCENARIO_ID)
    path = workspace_path(root, scenario_id=PORTFOLIO_25_SCENARIO_ID)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["scenario_hash"] = "FORGED"
    path.write_bytes(canonical_document_bytes(envelope))
    with pytest.raises(
        OperatedPortfolioError, match="PERSISTED_SCENARIO_HASH_MISMATCH"
    ):
        load_workspace(root=root, scenario_id=PORTFOLIO_25_SCENARIO_ID)


def test_25_scenario_executes_no_change_transition_replay_and_correction() -> None:
    draft = build_draft_workspace(PORTFOLIO_25_SCENARIO_ID)
    assert draft["book"]["nav"] == "11000"

    funded = confirm_initial_portfolio(draft)
    assert funded["status"] == STATUS_FUNDED
    assert len(funded["orders"]) == 8
    assert len([row for row in funded["book"]["positions"] if int(row["quantity"])]) == 8
    assert funded["book"]["nav"] == "10984"
    assert funded["book"]["unexplained_residual"] == "0"

    observed = admit_no_change_observation(funded)
    assert observed["status"] == STATUS_NO_CHANGE
    assert observed["book"]["book_hash"] == funded["book"]["book_hash"]
    assert len(observed["orders"]) == 8

    transitioned = authorize_portfolio_transition(observed)
    assert transitioned["status"] == STATUS_TRANSITION
    assert [row["side"] for row in transitioned["orders"][-2:]] == [
        "SELL",
        "BUY",
    ]
    assert transitioned["changed_why"]["reduced"]["symbol"] == "HARBOR"
    assert transitioned["changed_why"]["funded_or_increased"]["symbol"] == "MERID"
    assert transitioned["book"]["nav"] == "10980"
    assert transitioned["book"]["unexplained_residual"] == "0"

    reconstructed = reconstruct_exact(
        transitioned["events"], expected_book=transitioned["book"]
    )
    assert reconstructed["book_hash"] == transitioned["book"]["book_hash"]
    assert replay_idempotent(transitioned["events"])["book_hash"] == reconstructed[
        "book_hash"
    ]

    corrected = append_non_economic_correction(transitioned)
    assert corrected["status"] == STATUS_CORRECTED
    assert corrected["book"]["book_hash"] == transitioned["book"]["book_hash"]
    assert corrected["book"]["nav"] == transitioned["book"]["nav"]
    assert len(corrected["certification_history"]) == 3
    validate_workspace(corrected)


def test_cross_instrument_evidence_and_thesis_rebinding_fails_closed() -> None:
    workspace = build_draft_workspace(PORTFOLIO_25_SCENARIO_ID)

    evidence_rebound = deepcopy(workspace)
    first_owner = evidence_rebound["evidence_references"][0][
        "owned_instrument_ids"
    ][0]
    second_owner = evidence_rebound["evidence_references"][1][
        "owned_instrument_ids"
    ][0]
    assert first_owner != second_owner
    evidence_rebound["reviews"][1]["living_thesis_lite"][
        "evidence_reference_ids"
    ] = [evidence_rebound["evidence_references"][0]["evidence_reference_id"]]
    with pytest.raises(
        OperatedPortfolioError, match="THESIS_INSTRUMENT_EVIDENCE_OWNER_MISMATCH"
    ):
        validate_workspace(evidence_rebound, allow_draft=True)

    thesis_rebound = deepcopy(workspace)
    thesis_rebound["reviews"][1]["living_thesis_lite"] = deepcopy(
        thesis_rebound["reviews"][0]["living_thesis_lite"]
    )
    with pytest.raises(
        OperatedPortfolioError, match="THESIS_INSTRUMENT_OWNER_MISMATCH"
    ):
        validate_workspace(thesis_rebound, allow_draft=True)


def test_shared_storage_is_scenario_isolated_and_restartable(tmp_path: Path) -> None:
    root = tmp_path / "shared-operated-root"
    ten = ensure_workspace(root=root, scenario_id=DEFAULT_SCENARIO_ID)
    twenty_five = ensure_workspace(
        root=root, scenario_id=PORTFOLIO_25_SCENARIO_ID
    )
    assert len(ten["instruments"]) == 10
    assert len(twenty_five["instruments"]) == 25
    assert workspace_path(root, scenario_id=DEFAULT_SCENARIO_ID).is_file()
    assert workspace_path(root, scenario_id=PORTFOLIO_25_SCENARIO_ID).is_file()
    assert workspace_path(
        root, scenario_id=DEFAULT_SCENARIO_ID
    ) != workspace_path(root, scenario_id=PORTFOLIO_25_SCENARIO_ID)

    funded = confirm_and_persist(
        root=root, scenario_id=PORTFOLIO_25_SCENARIO_ID
    )
    assert load_workspace(
        root=root, scenario_id=PORTFOLIO_25_SCENARIO_ID
    ) == funded
    observed = admit_no_change_and_persist(
        root=root, scenario_id=PORTFOLIO_25_SCENARIO_ID
    )
    transitioned = authorize_transition_and_persist(
        root=root, scenario_id=PORTFOLIO_25_SCENARIO_ID
    )
    corrected = append_correction_and_persist(
        root=root, scenario_id=PORTFOLIO_25_SCENARIO_ID
    )
    assert observed["status"] == STATUS_NO_CHANGE
    assert transitioned["status"] == STATUS_TRANSITION
    assert corrected["status"] == STATUS_CORRECTED
    assert load_workspace(
        root=root, scenario_id=PORTFOLIO_25_SCENARIO_ID
    ) == corrected
    assert load_workspace(root=root, scenario_id=DEFAULT_SCENARIO_ID) == ten
