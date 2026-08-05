"""Proposal-bound post-entry SELL+BUY paper rotation acceptance."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import textwrap

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
from core.gv_pit.adapters import build_real_pit_source_bundle
from core.gv_pit.contracts import canonical_value
from core.gv_pit.governance import govern_real_pit_bundle
from core.gv_pit.read_models import project_decision_episode
from gv_portfolio_v0.operated_scenarios import OPERATED_PAPER_CAPITAL_SCENARIO_ID
from gv_portfolio_v0.operated_storage import (
    confirm_prospective_observation_and_persist,
    ensure_prospective_workspace,
    load_prospective_workspace,
    reject_prospective_observation_and_persist,
)
from gv_portfolio_v0.prospective import (
    ProspectiveOperationError,
    operated_rotation_companion,
    preview_runtime_observation,
    reconstruct_prospective_workspace,
)

ROOT = Path(__file__).resolve().parents[1]


def _app_blob(app: object) -> str:
    parts: list[str] = []
    for collection_name in (
        "header",
        "subheader",
        "caption",
        "info",
        "warning",
        "success",
        "error",
        "table",
    ):
        for element in getattr(app, collection_name):
            parts.append(str(getattr(element, "value", element)))
    return "\n".join(parts)


def _element_by_key(collection: object, key: str) -> object:
    return next(
        element for element in collection if getattr(element, "key", None) == key
    )


_FRESH_PROCESS_SCRIPT = textwrap.dedent(
    """
    import hashlib
    import json
    from pathlib import Path
    import sys

    from core.gv_fs0_canonical import canonical_document_bytes
    from gv_portfolio_v0.operated_scenarios import OPERATED_PAPER_CAPITAL_SCENARIO_ID
    from gv_portfolio_v0.operated_storage import load_prospective_workspace
    from gv_portfolio_v0.prospective import reconstruct_prospective_workspace

    root = Path(sys.argv[1])
    workspace = load_prospective_workspace(
        root=root,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    reconstructed = reconstruct_prospective_workspace(
        workspace["events"],
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    print(json.dumps({
        "workspace_hash": hashlib.sha256(canonical_document_bytes(workspace)).hexdigest(),
        "reconstructed_hash": hashlib.sha256(canonical_document_bytes(reconstructed)).hexdigest(),
        "book_hash": workspace["book"]["book_hash"],
        "positions": workspace["book"]["positions"],
        "orders": workspace["orders"],
        "fills": workspace["fills"],
        "cash": workspace["book"]["classified_cash"],
        "costs": workspace["book"]["classified_costs"],
        "residual": workspace["book"]["unexplained_residual"],
        "episode_count": workspace["prospective_episode_count"],
        "lineage_depth": len(workspace["certification_history"]),
    }, sort_keys=True))
    """
)


def _pit_identity() -> dict[str, object]:
    return canonical_value(build_real_pit_source_bundle().pit_identity)  # type: ignore[return-value]


def _displayed_binding(workspace: dict[str, object]) -> dict[str, object]:
    model = project_decision_episode(
        govern_real_pit_bundle(build_real_pit_source_bundle()).read()
    )
    row = next(
        proposal
        for proposal in model.proposal_records
        if proposal.module_id == "GV_REAL_MU_OPERATED"
        and proposal.status == "ELIGIBLE"
    )
    return {
        "episode_id": model.episode_id,
        "record_id": row.record_id,
        "proposal_id": row.proposal_id,
        "module_id": row.module_id,
        "module_version": row.module_version,
        "sleeve_id": row.sleeve_id,
        "status": row.status,
        "pit_identity": _pit_identity(),
        "active_book_hash": workspace["book"]["book_hash"],
        "active_certification_id": workspace["certification"]["certification_id"],
        "active_event_count": len(workspace["events"]),
    }


def _entry_request(workspace: dict[str, object]) -> dict[str, object]:
    review = workspace["reviews"][0]
    return {
        "content": "Owner-reviewed evidence supports one bounded MU paper entry.",
        "locator": "operator://2026-08-04/mu/entry",
        "observed_at": "2026-08-04T12:01:00.000000Z",
        "pit_identity": _pit_identity(),
        "market_instrument_id": review["instrument_id"],
        "market_price": "101.25",
        "market_observed_at": "2026-08-04T12:00:00.000000Z",
        "market_source_identity": "operator://2026-08-04/mu/market",
        "review_updates": [
            {
                "instrument_id": review["instrument_id"],
                "outcome": "ADMIT",
                "net_score_bps": 500,
                "target_quantity": "7",
                "principal_claim": "The bounded owner assertion supports seven MU paper units.",
            }
        ],
        "operator_rationale": "Operate the first bounded MU paper-capital entry.",
    }


def _episode_one(root: Path) -> dict[str, object]:
    workspace = ensure_prospective_workspace(
        root=root,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    return confirm_prospective_observation_and_persist(
        preview_runtime_observation(workspace, _entry_request(workspace)),
        root=root,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )


def _rotation_request(workspace: dict[str, object]) -> dict[str, object]:
    source_review = workspace["reviews"][0]
    companion = operated_rotation_companion(workspace)
    companion_review = companion["review"]
    return {
        "content": (
            "Owner-reviewed evidence reduces the bounded MU target and admits one "
            "governed Meridian companion target for repeatability proof."
        ),
        "locator": "operator://2026-08-04/mu-merid/rotation",
        "observed_at": "2026-08-04T13:01:00.000000Z",
        "pit_identity": _pit_identity(),
        "displayed_proposal_binding": _displayed_binding(workspace),
        "forward_operated_market_packets": [
            {
                "instrument_id": source_review["instrument_id"],
                "market_price": "101.25",
                "market_observed_at": "2026-08-04T13:00:00.000000Z",
                "market_source_identity": "operator://2026-08-04/mu/rotation-market",
            },
            {
                "instrument_id": companion_review["instrument_id"],
                "market_price": "30",
                "market_observed_at": "2026-08-04T13:00:00.000000Z",
                "market_source_identity": "operator://2026-08-04/merid/rotation-market",
            },
        ],
        "review_updates": [
            {
                "instrument_id": source_review["instrument_id"],
                "outcome": "ADMIT",
                "net_score_bps": 420,
                "target_quantity": "4",
                "principal_claim": "Retain four MU units after the bounded reduction.",
            },
            {
                "instrument_id": companion_review["instrument_id"],
                "outcome": "ADMIT",
                "net_score_bps": 470,
                "target_quantity": "5",
                "principal_claim": "Fund five Meridian units from the accepted companion substrate.",
            },
        ],
        "operator_rationale": (
            "Reduce MU and fund Meridian to prove the displayed-proposal-to-capital "
            "rotation loop; this is not an alpha claim."
        ),
    }


def test_rotation_preview_binds_displayed_proposal_and_is_mutation_free(
    tmp_path: Path,
) -> None:
    workspace = _episode_one(tmp_path)
    before = canonical_document_bytes(workspace)
    proposal = preview_runtime_observation(workspace, _rotation_request(workspace))

    assert canonical_document_bytes(workspace) == before
    assert proposal["request"]["displayed_proposal_binding"]["module_id"] == (
        "GV_REAL_MU_OPERATED"
    )
    assert proposal["request"]["displayed_proposal_binding"]["active_book_hash"] == (
        workspace["book"]["book_hash"]
    )
    assert proposal["request"]["pit_identity"] == _pit_identity()
    assert len(proposal["request"]["forward_operated_market_packets"]) == 2
    assert proposal["request"]["forward_operated_market_packets"][0]["market_price"] == "101.25"
    assert proposal["transition"]["transition_kind"] == "PROSPECTIVE_REBALANCE"
    assert [row["side"] for row in proposal["transition"]["legs"]] == ["SELL", "BUY"]
    assert [row["quantity"] for row in proposal["transition"]["legs"]] == ["3", "5"]
    assert proposal["transition"]["unexplained_residual"] == "0"
    assert proposal["transition"]["order_count"] == 2
    quantities = {
        row["instrument_id"]: row["quantity"]
        for row in proposal["transition"]["positions_after"]
    }
    source_id = workspace["reviews"][0]["instrument_id"]
    companion_id = operated_rotation_companion(workspace)["review"]["instrument_id"]
    assert quantities == {source_id: "4", companion_id: "5"}


def test_rotation_confirm_persists_certifies_and_reopens_exactly(tmp_path: Path) -> None:
    workspace = _episode_one(tmp_path)
    proposal = preview_runtime_observation(workspace, _rotation_request(workspace))
    confirmed = confirm_prospective_observation_and_persist(
        proposal,
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )

    assert confirmed["prospective_episode_count"] == 2
    assert confirmed["operator_action_count"] == 4
    assert len(confirmed["orders"]) == 3
    assert len(confirmed["fills"]) == 3
    assert [row["side"] for row in confirmed["orders"]] == ["BUY", "SELL", "BUY"]
    assert len(confirmed["book"]["positions"]) == 2
    assert confirmed["book"]["unexplained_residual"] == "0"
    assert confirmed["book"]["book_hash"] == proposal["transition"]["book_hash_after"]
    assert len(confirmed["certification_history"]) == 2

    reopened = load_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    reconstructed = reconstruct_prospective_workspace(
        reopened["events"],
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    assert canonical_document_bytes(reopened) == canonical_document_bytes(reconstructed)
    expected_hash = hashlib.sha256(canonical_document_bytes(confirmed)).hexdigest()
    completed = subprocess.run(
        [sys.executable, "-c", _FRESH_PROCESS_SCRIPT, str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout)
    assert receipt["workspace_hash"] == receipt["reconstructed_hash"] == expected_hash
    assert receipt["episode_count"] == 2
    assert receipt["lineage_depth"] == 2
    assert [row["side"] for row in receipt["orders"]] == ["BUY", "SELL", "BUY"]
    assert receipt["residual"] == "0"


def test_rotation_reject_all_preserves_book_and_does_not_add_companion(
    tmp_path: Path,
) -> None:
    workspace = _episode_one(tmp_path)
    proposal = preview_runtime_observation(workspace, _rotation_request(workspace))
    rejected = reject_prospective_observation_and_persist(
        proposal,
        "The bounded rotation is valid but the operator rejects capital authority.",
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )

    assert canonical_document_bytes(rejected["book"]) == canonical_document_bytes(
        workspace["book"]
    )
    assert rejected["prospective_episode_count"] == 2
    assert rejected["prospective_episode_history"][-1]["disposition"] == "REJECTED"
    assert len(rejected["instruments"]) == len(workspace["instruments"]) == 1
    assert len(rejected["orders"]) == 1
    assert rejected["orders"][0]["side"] == "BUY"


def test_command_center_operates_displayed_proposal_rotation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    def _denied(*_args: object, **_kwargs: object) -> None:
        raise OSError("GV_COMMAND_CENTER_NETWORK_DENIED")

    workspace_root = tmp_path / "workspace"
    episode_one = _episode_one(workspace_root)
    assert episode_one["prospective_episode_count"] == 1
    monkeypatch.setattr(socket, "create_connection", _denied)
    monkeypatch.setenv("GV_OPERATED_PORTFOLIO_HOME", str(workspace_root))
    monkeypatch.chdir(ROOT)

    app = AppTest.from_file(str(ROOT / "dashboard.py")).run(timeout=120)
    assert not app.exception, app.exception
    initial = _app_blob(app)
    assert "Operate one proposal-bound SELL+BUY rotation" in initial
    assert "GV_REAL_MU_OPERATED" in initial
    assert "MERID" in initial

    _element_by_key(
        app.text_area, "gv_command_center_rotation_evidence_content"
    ).set_value(
        "Owner-reviewed evidence reduces the bounded MU target and admits one governed Meridian companion target."
    )
    _element_by_key(
        app.text_input, "gv_command_center_rotation_source_locator"
    ).set_value("operator://2026-08-04/mu-merid/rotation")
    _element_by_key(
        app.text_input, "gv_command_center_rotation_evidence_observed_at"
    ).set_value("2026-08-04T13:01:00.000000Z")
    _element_by_key(
        app.text_input, "gv_command_center_rotation_source_market_observed_at"
    ).set_value("2026-08-04T13:00:00.000000Z")
    _element_by_key(
        app.text_input, "gv_command_center_rotation_source_market_source_identity"
    ).set_value("operator://2026-08-04/mu/rotation-market")
    _element_by_key(
        app.number_input, "gv_command_center_rotation_source_target_quantity"
    ).set_value(4)
    _element_by_key(
        app.number_input, "gv_command_center_rotation_source_net_score_bps"
    ).set_value(420)
    _element_by_key(
        app.text_area, "gv_command_center_rotation_source_principal_claim"
    ).set_value("Retain four MU units after the bounded reduction.")
    _element_by_key(
        app.text_input, "gv_command_center_rotation_companion_market_observed_at"
    ).set_value("2026-08-04T13:00:00.000000Z")
    _element_by_key(
        app.text_input, "gv_command_center_rotation_companion_market_source_identity"
    ).set_value("operator://2026-08-04/merid/rotation-market")
    _element_by_key(
        app.number_input, "gv_command_center_rotation_companion_target_quantity"
    ).set_value(5)
    _element_by_key(
        app.number_input, "gv_command_center_rotation_companion_net_score_bps"
    ).set_value(470)
    _element_by_key(
        app.text_area, "gv_command_center_rotation_companion_principal_claim"
    ).set_value("Fund five Meridian units from the accepted companion substrate.")
    _element_by_key(
        app.text_area, "gv_command_center_rotation_operator_rationale"
    ).set_value(
        "Reduce MU and fund Meridian to prove the displayed-proposal-to-capital rotation loop; this is not an alpha claim."
    )
    _element_by_key(app.button, "gv_command_center_preview").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    preview = _app_blob(app)
    assert "Mutation-free paper-capital preview" in preview
    assert "GV_REAL_MU_OPERATED" in preview
    assert "SELL" in preview and "BUY" in preview
    assert "residual=0" in preview
    preview_tables = [element.value for element in app.table]
    preview_summary = next(
        table
        for table in preview_tables
        if "displayed_module" in table.columns
    )
    assert preview_summary.loc[0, "displayed_module"] == "GV_REAL_MU_OPERATED"
    assert bool(preview_summary.loc[0, "authoritative"]) is False

    _element_by_key(app.button, "gv_command_center_confirm").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    confirmed = _app_blob(app)
    assert "proposal-bound SELL+BUY rotation has been operated" in confirmed
    assert "Certified paper fills" in confirmed
    assert "SELL" in confirmed and "BUY" in confirmed
    assert "MERID" in confirmed
    confirmed_tables = [element.value for element in app.table]
    authority = next(
        table
        for table in confirmed_tables
        if "prospective_episode_count" in table.columns
    )
    assert int(authority.loc[0, "prospective_episode_count"]) == 2
    assert int(authority.loc[0, "certification_lineage_depth"]) == 2
    active_book = next(
        table
        for table in confirmed_tables
        if "symbol" in table.columns and "quantity" in table.columns
    )
    quantities = dict(zip(active_book["symbol"], active_book["quantity"].astype(str)))
    assert quantities["MU"] == "4"
    assert quantities["MERID"] == "5"


def test_rotation_rejects_stale_binding_and_buy_only_top_up(tmp_path: Path) -> None:
    workspace = _episode_one(tmp_path)
    stale = _rotation_request(workspace)
    stale["displayed_proposal_binding"]["active_book_hash"] = "0" * 64
    with pytest.raises(
        ProspectiveOperationError,
        match="DISPLAYED_PROPOSAL_ACTIVE_BOOK_MISMATCH",
    ):
        preview_runtime_observation(workspace, stale)

    buy_only = _rotation_request(workspace)
    buy_only["review_updates"][0]["target_quantity"] = "8"
    with pytest.raises(
        ProspectiveOperationError,
        match="OPERATED_ROTATION_SOURCE_REDUCTION_REQUIRED",
    ):
        preview_runtime_observation(workspace, buy_only)

    proposal = preview_runtime_observation(workspace, _rotation_request(workspace))
    tampered = deepcopy(proposal)
    tampered["request"]["displayed_proposal_binding"]["proposal_id"] = "PRP_TAMPERED"
    with pytest.raises(
        ProspectiveOperationError,
        match="DISPLAYED_PROPOSAL_BINDING_MISMATCH",
    ):
        confirm_prospective_observation_and_persist(
            tampered,
            root=tmp_path,
            scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
        )
