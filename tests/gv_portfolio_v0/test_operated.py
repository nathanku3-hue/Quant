from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess

import pytest

from core.gv_fs0_canonical import domain_hash
from gv_portfolio_v0.book import PortfolioBookError, build_portfolio_book
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


def _position_by_symbol(workspace: dict[str, object], symbol: str) -> dict[str, str]:
    instruments = {
        row["symbol"]: row["instrument_id"] for row in workspace["instruments"]
    }
    return next(
        row
        for row in workspace["book"]["positions"]
        if row["instrument_id"] == instruments[symbol]
    )


def _transitioned_workspace() -> dict[str, object]:
    return authorize_portfolio_transition(
        admit_no_change_observation(confirm_initial_portfolio(build_draft_workspace()))
    )


def _corrected_workspace() -> dict[str, object]:
    return append_non_economic_correction(_transitioned_workspace())


def _rehash_snapshot(snapshot: dict[str, object]) -> None:
    body = {key: value for key, value in snapshot.items() if key != "decision_snapshot_id"}
    snapshot["decision_snapshot_id"] = "DSN_" + domain_hash(
        "GV-OPERATED-PORTFOLIO-10:DSN:V1", body
    )


def _rehash_event(event: dict[str, object]) -> None:
    body = {key: value for key, value in event.items() if key != "event_id"}
    event["event_id"] = "EVT_" + domain_hash("GV-PORTFOLIO-V0:EVT:V1", body)


def _create_directory_link(link: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        completed = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            pytest.skip(f"junction unavailable: {completed.stderr or completed.stdout}")
    else:
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"directory symlink unavailable: {exc}")


def test_draft_has_ten_distinct_instruments_two_clusters_and_unique_theses() -> None:
    workspace = build_draft_workspace()
    assert workspace["status"] == STATUS_DRAFT
    assert workspace["portfolio_count"] == 1
    assert len(workspace["instruments"]) == 10
    assert len({row["instrument_id"] for row in workspace["instruments"]}) == 10
    assert len({row["permanent_key"] for row in workspace["instruments"]}) == 10
    assert {row["economic_cluster"] for row in workspace["instruments"]} == {
        "DIGITAL_INFRASTRUCTURE",
        "REAL_ECONOMY",
    }
    assert len({row["content_sha256"] for row in workspace["evidence_references"]}) == 10
    assert len(
        {
            row["living_thesis_lite"]["principal_claim"]
            for row in workspace["reviews"]
        }
    ) == 10
    candidates = workspace["current_decision_snapshot"]["capital_competition"][
        "candidates"
    ]
    assert len(candidates) == 10
    assert {row["instrument_id"] for row in candidates} == {
        row["instrument_id"] for row in workspace["instruments"]
    }
    assert workspace["book"]["nav"] == "5000"


def test_one_portfolio_full_flow_funds_no_changes_then_rebalances() -> None:
    draft = build_draft_workspace()
    funded = confirm_initial_portfolio(draft)
    assert funded["status"] == STATUS_FUNDED
    assert funded["book"]["nav"] == "4992"
    assert len([row for row in funded["book"]["positions"] if int(row["quantity"])]) == 4
    assert {row["bucket"] for row in funded["book"]["classified_cash"]} == {
        "AVAILABLE",
        "RESEARCH_RESERVE",
    }
    assert [row["side"] for row in funded["orders"]] == ["BUY"] * 4

    observed = admit_no_change_observation(funded)
    assert observed["status"] == STATUS_NO_CHANGE
    assert observed["book"]["book_hash"] == funded["book"]["book_hash"]
    assert len(observed["orders"]) == 4
    assert observed["changed_why"] == {
        "change_type": "NO_CHANGE",
        "reason": "The observation stayed inside the watch band; no hard falsifier or funding threshold fired.",
        "holdings_changed": False,
        "cash_changed": False,
        "orders_created": 0,
    }

    transitioned = authorize_portfolio_transition(observed)
    assert transitioned["status"] == STATUS_TRANSITION
    assert [row["side"] for row in transitioned["orders"][-2:]] == ["SELL", "BUY"]
    assert _position_by_symbol(transitioned, "HARBOR")["quantity"] == "6"
    assert _position_by_symbol(transitioned, "MERID")["quantity"] == "5"
    assert transitioned["book"]["total_costs"] == "12"
    assert transitioned["book"]["nav"] == "4988"
    assert transitioned["book"]["unexplained_residual"] == "0"
    assert transitioned["changed_why"]["reduced"]["symbol"] == "HARBOR"
    assert transitioned["changed_why"]["funded_or_increased"]["symbol"] == "MERID"

    reconstructed = reconstruct_exact(
        transitioned["events"], expected_book=transitioned["book"]
    )
    assert reconstructed["book_hash"] == transitioned["book"]["book_hash"]
    assert replay_idempotent(transitioned["events"])["book_hash"] == reconstructed[
        "book_hash"
    ]


def test_decision_selection_is_execution_authority() -> None:
    workspace = build_draft_workspace()
    tampered = deepcopy(workspace)
    snapshot = tampered["decision_snapshots"][0]
    snapshot["capital_competition"]["selected_funded_instrument_ids"] = []
    _rehash_snapshot(snapshot)
    tampered["current_decision_snapshot"] = deepcopy(snapshot)

    with pytest.raises(
        OperatedPortfolioError, match="DECISION_SNAPSHOT_AUTHORITY_MISMATCH"
    ):
        validate_workspace(tampered, allow_draft=True)
    with pytest.raises(
        OperatedPortfolioError, match="DECISION_SNAPSHOT_AUTHORITY_MISMATCH"
    ):
        confirm_initial_portfolio(tampered)


def test_review_requires_instrument_owned_evidence() -> None:
    workspace = build_draft_workspace()
    shared = workspace["reviews"][0]["living_thesis_lite"]["evidence_reference_ids"][0]
    tampered = deepcopy(workspace)
    for review in tampered["reviews"]:
        review["living_thesis_lite"]["evidence_reference_ids"] = [shared]
    with pytest.raises(
        OperatedPortfolioError, match="THESIS_INSTRUMENT_EVIDENCE_OWNER_MISMATCH"
    ):
        validate_workspace(tampered, allow_draft=True)


def test_event_ledger_owns_trade_and_changed_why_projections() -> None:
    transitioned = _transitioned_workspace()

    missing_chain = deepcopy(transitioned)
    missing_chain["trade_authority_chains"] = []
    with pytest.raises(
        OperatedPortfolioError, match="TRADE_AUTHORITY_CHAIN_PROJECTION_MISMATCH"
    ):
        validate_workspace(missing_chain)

    forged_order = deepcopy(transitioned)
    forged_order["orders"][0]["instrument_id"] = forged_order["instruments"][-1][
        "instrument_id"
    ]
    with pytest.raises(OperatedPortfolioError, match="ORDER_PROJECTION_MISMATCH"):
        validate_workspace(forged_order)

    forged_fill = deepcopy(transitioned)
    forged_fill["fills"][0]["price"] = "999"
    with pytest.raises(OperatedPortfolioError, match="FILL_PROJECTION_MISMATCH"):
        validate_workspace(forged_fill)

    false_changed_why = deepcopy(transitioned)
    false_changed_why["changed_why"]["cash_after"] = "999999"
    false_changed_why["changed_why"]["funded_or_increased"]["symbol"] = "FAKE"
    with pytest.raises(
        OperatedPortfolioError, match="CHANGED_WHY_PROJECTION_MISMATCH"
    ):
        validate_workspace(false_changed_why)


def test_transition_legs_match_exact_target_deltas() -> None:
    transitioned = _transitioned_workspace()
    tampered = deepcopy(transitioned)
    transition = next(
        event
        for event in tampered["events"]
        if event["event_type"] == "PORTFOLIO_TRANSITION_PLANNED"
        and event["payload"]["transition_kind"] == "REDUCE_AND_FUND"
    )
    transition["payload"]["legs"][0]["quantity"] = "3"
    _rehash_event(transition)
    with pytest.raises(OperatedPortfolioError, match="TRANSITION_LEGS_MISMATCH"):
        validate_workspace(tampered)


def test_sell_accounting_fails_closed_on_oversell() -> None:
    transitioned = _transitioned_workspace()
    tampered = deepcopy(transitioned["events"])
    sell_order_event = next(
        event
        for event in tampered
        if event["event_type"] == "ORDER_CREATED"
        and event["payload"]["order"]["side"] == "SELL"
    )
    sell_order_event["payload"]["order"]["quantity"] = "1000"
    with pytest.raises(PortfolioBookError, match="SELL_ORDER_EXCEEDS_POSITION"):
        build_portfolio_book(tampered)


def test_append_only_correction_preserves_economics_and_links_certifications() -> None:
    transitioned = _transitioned_workspace()
    prior_certification = deepcopy(transitioned["certification"])
    corrected = append_non_economic_correction(transitioned)
    assert corrected["status"] == STATUS_CORRECTED
    assert corrected["book"]["book_hash"] == transitioned["book"]["book_hash"]
    assert corrected["book"]["nav"] == transitioned["book"]["nav"]
    assert corrected["certification"]["prior_certification_id"] == prior_certification[
        "certification_id"
    ]
    assert corrected["certification_history"][-1] == prior_certification
    assert corrected["correction_history"] == [
        {
            "event_id": corrected["events"][-2]["event_id"],
            "prior_certification_id": prior_certification["certification_id"],
            "certification_id": corrected["certification"]["certification_id"],
            "economic_effect": "NONE",
        }
    ]


def test_complete_certification_history_is_replayed_and_immutable() -> None:
    transitioned = _transitioned_workspace()
    forged_history = deepcopy(transitioned)
    forged_history["certification_history"][0]["terminal_book_hash"] = "FORGED"
    with pytest.raises(
        OperatedPortfolioError, match="CERTIFICATION_HISTORY_OBJECT_MISMATCH"
    ):
        validate_workspace(forged_history)

    corrected = _corrected_workspace()
    self_asserted = deepcopy(corrected)
    self_asserted["correction_history"][0][
        "prior_certification_byte_stable"
    ] = False
    with pytest.raises(
        OperatedPortfolioError, match="CORRECTION_HISTORY_PROJECTION_MISMATCH"
    ):
        validate_workspace(self_asserted)


def test_persist_restart_reopen_each_operator_stage(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    draft = ensure_workspace(root=root)
    assert draft["status"] == STATUS_DRAFT

    funded = confirm_and_persist(root=root)
    assert load_workspace(root=root) == funded
    observed = admit_no_change_and_persist(root=root)
    assert load_workspace(root=root) == observed
    transitioned = authorize_transition_and_persist(root=root)
    assert load_workspace(root=root) == transitioned
    corrected = append_correction_and_persist(root=root)
    assert load_workspace(root=root) == corrected
    assert corrected["status"] == STATUS_CORRECTED


def test_persistence_rejects_linked_ancestor_escape(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    linked = tmp_path / "linked-root"
    _create_directory_link(linked, outside)

    with pytest.raises(
        OperatedPortfolioError, match="WORKSPACE_LINKED_ANCESTOR_PROHIBITED"
    ):
        ensure_workspace(root=linked / "nested")
    assert not (outside / "nested" / workspace_path().name).exists()


def test_persisted_workspace_tamper_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    confirm_and_persist(root=root)
    path = workspace_path(root)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["workspace"]["book"]["nav"] = "999999"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    with pytest.raises(OperatedPortfolioError, match="WORKSPACE_HASH_MISMATCH"):
        load_workspace(root=root)


def test_validation_rejects_duplicate_identity_and_cross_instrument_thesis_rebinding() -> None:
    workspace = build_draft_workspace()
    duplicate = deepcopy(workspace)
    duplicate["instruments"][1] = deepcopy(duplicate["instruments"][0])
    with pytest.raises(OperatedPortfolioError):
        validate_workspace(duplicate, allow_draft=True)

    rebound = deepcopy(workspace)
    rebound["reviews"][1]["living_thesis_lite"] = deepcopy(
        rebound["reviews"][0]["living_thesis_lite"]
    )
    with pytest.raises(
        OperatedPortfolioError, match="THESIS_INSTRUMENT_OWNER_MISMATCH"
    ):
        validate_workspace(rebound, allow_draft=True)
