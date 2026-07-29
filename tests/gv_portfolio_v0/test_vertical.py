from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
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
        "hard_falsifier_fired": False,
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

    with pytest.raises(PortfolioV0Error, match="FILL_QUANTITY_MUST_BE_POSITIVE"):
        certify_workspace(workspace)


def test_identity_or_snapshot_tampering_is_rejected() -> None:
    draft = build_draft_workspace()
    tampered = deepcopy(draft)
    tampered["decision_snapshot"]["selected_quantity"] = "999"
    with pytest.raises(PortfolioV0Error, match="IDENTITY_MISMATCH:decision_snapshot_id"):
        confirm_draft_workspace(tampered)


def test_watch_admission_requires_certified_state() -> None:
    with pytest.raises(PortfolioV0Error, match="UNCERTIFIED_WORKSPACE"):
        admit_watch_observation(build_draft_workspace())
