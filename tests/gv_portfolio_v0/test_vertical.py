from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.storage import (
    admit_later_watch_observation,
    confirm_and_certify,
    ensure_workspace,
    load_workspace,
    workspace_path,
)
from gv_portfolio_v0.vertical import (
    PortfolioV0Error,
    admit_watch_observation,
    build_draft_workspace,
    certify_workspace,
    confirm_draft_workspace,
    reduce_events,
)


def test_draft_exercises_review_outcomes_benchmark_cash_and_split() -> None:
    workspace = build_draft_workspace()
    assert workspace["schema_version"] == "gv_portfolio_v0_workspace_v2"
    assert workspace["status"] == "DRAFT_REVIEW"
    assert len(workspace["instruments"]) == 4
    assert workspace["benchmark"]["role"] == "BENCHMARK"
    assert {row["outcome"] for row in workspace["reviews"]} == {
        "ADMIT",
        "REJECT",
        "ABSTAIN",
    }
    assert workspace["cash_outcome"]["outcome"] == "CASH"
    assert workspace["decision_snapshot"]["capital_competition"][
        "selected_candidate"
    ] == "HARBOR"
    assert workspace["book"]["nav"] == "1500"
    assert workspace["book"]["split_value_residual"] == "0"
    principal = workspace["book"]["positions"][0]
    assert principal["quantity"] == "20"
    assert principal["valuation_price"] == "25"


def test_confirm_certify_persist_and_reopen_complete_operator_loop(tmp_path: Path) -> None:
    draft = ensure_workspace(root=tmp_path)
    snapshot_bytes = canonical_document_bytes(draft["decision_snapshot"])
    certified = confirm_and_certify(root=tmp_path)
    reopened = load_workspace(root=tmp_path)

    assert certified == reopened
    assert reopened["status"] == "CERTIFIED"
    assert canonical_document_bytes(reopened["decision_snapshot"]) == snapshot_bytes
    assert reopened["order"]["execution_mode"] == "DETERMINISTIC_PAPER"
    assert reopened["transition_event"]["event_type"] == "PORTFOLIO_TRANSITION_PLANNED"
    assert reopened["order"]["transition_event_id"] == reopened["transition_event"][
        "event_id"
    ]
    assert reopened["execution_authority_chain"]["order_id"] == reopened["order"][
        "order_id"
    ]
    assert reopened["execution_authority_chain"]["fill_id"] == reopened["fill"][
        "fill_id"
    ]
    assert reopened["fill"]["quantity"] == "5"
    assert reopened["fill"]["price"] == "40"
    assert reopened["fill"]["fee"] == "1"
    assert len(reopened["book"]["positions"]) == 2
    assert reopened["book"]["classified_cash"] == [
        {"bucket": "AVAILABLE", "amount": "774"},
        {"bucket": "RESEARCH_RESERVE", "amount": "25"},
    ]
    assert reopened["book"]["position_value"] == "700"
    assert reopened["book"]["total_cash"] == "799"
    assert reopened["book"]["nav"] == "1499"
    assert reopened["book"]["opening_nav"] == "1500"
    assert reopened["book"]["total_costs"] == "1"
    assert reopened["book"]["unexplained_residual"] == "0"
    assert reopened["book"]["reconciliation_status"] == "RECONCILED"
    assert reopened["certification"]["terminal_book_hash"] == reopened["book"][
        "book_hash"
    ]
    assert all(reopened["certification"]["checks"].values())
    assert workspace_path(tmp_path).is_file()


def test_later_watch_observation_preserves_aim_and_original_snapshot(tmp_path: Path) -> None:
    certified = confirm_and_certify(root=tmp_path)
    aim_id = certified["portfolio_aim"]["portfolio_aim_id"]
    snapshot_bytes = canonical_document_bytes(certified["decision_snapshot"])
    prior_cert_bytes = canonical_document_bytes(certified["certification"])

    observed = admit_later_watch_observation(root=tmp_path)
    reopened = load_workspace(root=tmp_path)

    assert observed == reopened
    assert observed["status"] == "OBSERVED_WATCH_AIM_UNCHANGED"
    assert observed["portfolio_aim"]["portfolio_aim_id"] == aim_id
    assert canonical_document_bytes(observed["decision_snapshot"]) == snapshot_bytes
    assert observed["later_observation"] == {
        "evidence_reference_id": observed["later_observation"][
            "evidence_reference_id"
        ],
        "classification": "WATCH",
        "watch_condition_matches": [
            "order_intake_softens_without_covenant_breach"
        ],
        "hard_falsifier_matches": [],
        "hard_falsifier_fired": False,
        "portfolio_aim_id_before": aim_id,
        "portfolio_aim_id_after": aim_id,
        "aim_changed": False,
    }
    assert canonical_document_bytes(observed["certification_history"][0]) == prior_cert_bytes
    assert observed["certification"]["prior_certification_id"] == certified[
        "certification"
    ]["certification_id"]
    assert observed["book"]["nav"] == "1499"
    assert "no hard falsifier fired" in observed["explanation"]


def test_vertical_is_byte_deterministic_across_independent_roots(tmp_path: Path) -> None:
    confirm_and_certify(root=tmp_path / "a")
    confirm_and_certify(root=tmp_path / "b")
    first = admit_later_watch_observation(root=tmp_path / "a")
    second = admit_later_watch_observation(root=tmp_path / "b")
    assert canonical_document_bytes(first) == canonical_document_bytes(second)
    assert workspace_path(tmp_path / "a").read_bytes() == workspace_path(
        tmp_path / "b"
    ).read_bytes()


def test_reopen_fails_closed_on_persisted_hash_corruption(tmp_path: Path) -> None:
    confirm_and_certify(root=tmp_path)
    path = workspace_path(tmp_path)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["workspace"]["book"]["nav"] = "999999"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    with pytest.raises(PortfolioV0Error, match="WORKSPACE_HASH_MISMATCH"):
        load_workspace(root=tmp_path)


def test_reducer_reports_valuation_pending_without_invented_price() -> None:
    event = {
        "event_id": "EVT_PENDING",
        "sequence": 0,
        "event_type": "POSITION_OPENING",
        "effective_at": "2026-07-20T00:00:00.000000Z",
        "source_identity": "TEST",
        "instrument_id": "INS_PENDING",
        "cash_bucket": None,
        "payload": {"quantity": "3", "valuation_price": None},
    }
    book = reduce_events([event])
    assert book["valuation_status"] == "VALUATION_PENDING"
    assert book["nav"] is None
    assert book["position_value"] is None


def test_certification_rejects_negative_buy_fill_quantity() -> None:
    """A negative BUY must not turn into synthetic classified cash."""
    workspace = confirm_draft_workspace(build_draft_workspace())
    fill_event = next(
        event for event in workspace["events"] if event["event_type"] == "FILL_COMPLETED"
    )
    fill_event["payload"]["fill"]["quantity"] = "-5"

    with pytest.raises(
        PortfolioV0Error, match="POSITIVE_QUANTITY_REQUIRED:fill.quantity"
    ):
        certify_workspace(workspace)


def test_identity_or_snapshot_tampering_is_rejected() -> None:
    draft = build_draft_workspace()
    tampered = deepcopy(draft)
    tampered["decision_snapshot"]["selected_quantity"] = "999"
    with pytest.raises(PortfolioV0Error, match="DECISION_SNAPSHOT_ID_MISMATCH"):
        confirm_draft_workspace(tampered)


def test_ineligible_abstain_candidate_cannot_be_selected_and_certified() -> None:
    tampered = confirm_draft_workspace(build_draft_workspace())
    competition = tampered["decision_snapshot"]["capital_competition"]
    abstain = next(
        row for row in competition["candidates"] if row["candidate"] == "ORBIT"
    )
    competition["selected_candidate"] = abstain["candidate"]
    competition["selected_instrument_id"] = abstain["instrument_id"]
    competition["selected_net_score_bps"] = abstain["net_score_bps"]
    snapshot = tampered["decision_snapshot"]
    snapshot["decision_snapshot_id"] = "DSN_" + domain_hash(
        "GV-PORTFOLIO-V0:DSN:V1",
        {key: value for key, value in snapshot.items() if key != "decision_snapshot_id"},
    )

    with pytest.raises(PortfolioV0Error, match="CAPITAL_COMPETITION_MISMATCH"):
        certify_workspace(tampered)


def test_contradictory_decision_projection_cannot_certify() -> None:
    tampered = build_draft_workspace()
    snapshot = tampered["decision_snapshot"]
    abstain = next(
        review for review in snapshot["reviews"] if review["outcome"] == "ABSTAIN"
    )
    snapshot["selected_instrument_id"] = abstain["instrument_id"]
    snapshot["decision_snapshot_id"] = "DSN_" + domain_hash(
        "GV-PORTFOLIO-V0:DSN:V1",
        {key: value for key, value in snapshot.items() if key != "decision_snapshot_id"},
    )

    with pytest.raises(PortfolioV0Error, match="DECISION_SELECTION_MISMATCH"):
        confirm_draft_workspace(tampered)


def test_watch_admission_requires_certified_state() -> None:
    with pytest.raises(PortfolioV0Error, match="UNCERTIFIED_WORKSPACE"):
        admit_watch_observation(build_draft_workspace())
