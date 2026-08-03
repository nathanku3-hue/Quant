"""Real MU evidence-to-portfolio functional slice."""

from __future__ import annotations

from pathlib import Path
import socket

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
from gv_portfolio_v0.operated_scenarios import REAL_MU_PROSPECTIVE_SCENARIO_ID
from gv_portfolio_v0.operated_storage import (
    confirm_prospective_observation_and_persist,
    ensure_prospective_workspace,
    load_prospective_workspace,
    workspace_path,
)
from gv_portfolio_v0.prospective import (
    ProspectiveOperationError,
    preview_runtime_observation,
    reconstruct_prospective_workspace,
)

RECONCILIATION_HASH = (
    "89cc062783ae367c1bf259cfb7b355e0812ca162995b7ce05743a39e99592017"
)
RECONCILIATION_LOCATOR = (
    "repo://data/gv_v2_reconciliation/mu_nvda_supply_1/"
    f"reconciliation_result.json#reconciliation_hash={RECONCILIATION_HASH}"
)
ROOT = Path(__file__).resolve().parents[2]


def _app_blob(app: object) -> str:
    parts: list[str] = []
    for collection_name in (
        "header",
        "subheader",
        "caption",
        "info",
        "warning",
        "success",
        "table",
    ):
        for element in getattr(app, collection_name):
            parts.append(str(getattr(element, "value", element)))
    return "\n".join(parts)


def _request(workspace: dict[str, object]) -> dict[str, object]:
    review = workspace["reviews"][0]
    source_evidence = workspace["evidence_references"][0]
    return {
        "content": source_evidence["content"],
        "locator": source_evidence["locator"],
        "observed_at": "2026-08-02T12:30:00.000000Z",
        "review_updates": [
            {
                "instrument_id": review["instrument_id"],
                "outcome": "ABSTAIN",
                "net_score_bps": 0,
                "target_quantity": "0",
                "principal_claim": (
                    "Micron-specific physical supply persistence remains unestablished; "
                    "retain NO_POSITION pending independent physical supply evidence."
                ),
            }
        ],
        "operator_rationale": (
            "The real source set supports only indirect industry corroboration. Preserve "
            "classified cash and confirm ABSTAIN/NO_POSITION without execution."
        ),
    }


def test_real_mu_source_authority_is_rebuilt_before_bootstrap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import gv_portfolio_v0.prospective as prospective

    original = prospective.load_verified_mu_nvda_reconciliation

    def _drifted_result(*args: object, **kwargs: object) -> dict[str, object]:
        result = dict(original(*args, **kwargs))
        result["portfolio_action"] = "OPEN"
        return result

    monkeypatch.setattr(
        prospective,
        "load_verified_mu_nvda_reconciliation",
        _drifted_result,
    )
    with pytest.raises(
        ProspectiveOperationError,
        match="PROSPECTIVE_SOURCE_AUTHORITY_MISMATCH:portfolio_action",
    ):
        ensure_prospective_workspace(
            root=tmp_path,
            scenario_id=REAL_MU_PROSPECTIVE_SCENARIO_ID,
        )


def test_real_mu_profile_uses_real_identity_and_cash_only_authority(
    tmp_path: Path,
) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=REAL_MU_PROSPECTIVE_SCENARIO_ID,
    )
    assert workspace["scenario_id"] == REAL_MU_PROSPECTIVE_SCENARIO_ID
    assert workspace["source_authority"]["reconciliation_hash"] == RECONCILIATION_HASH
    assert len(workspace["instruments"]) == 1
    instrument = workspace["instruments"][0]
    assert instrument["symbol"] == "MU"
    assert instrument["namespace"] == "SEC_CIK_LISTING_V1"
    assert instrument["permanent_key"] == (
        "SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK"
    )
    evidence = workspace["evidence_references"][0]
    assert evidence["locator"] == RECONCILIATION_LOCATOR
    review = workspace["reviews"][0]
    assert review["outcome"] == "ABSTAIN"
    assert review["target_quantity"] == "0"
    assert workspace["orders"] == []
    assert workspace["fills"] == []
    assert workspace["book"]["positions"] == []
    assert workspace["book"]["nav"] == "11000"
    assert workspace["book"]["unexplained_residual"] == "0"
    assert {row["bucket"] for row in workspace["book"]["classified_cash"]} == {
        "AVAILABLE",
        "RESEARCH_RESERVE",
    }


def test_real_mu_preview_confirm_persist_and_reconstruct_exactly(
    tmp_path: Path,
) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=REAL_MU_PROSPECTIVE_SCENARIO_ID,
    )
    path = workspace_path(tmp_path, scenario_id=REAL_MU_PROSPECTIVE_SCENARIO_ID)
    persisted_before = path.read_bytes()
    request = _request(workspace)
    proposal = preview_runtime_observation(workspace, request)

    assert path.read_bytes() == persisted_before
    assert proposal["economics_changed"] is False
    assert proposal["changed_why"]["change_type"] == "PROSPECTIVE_NO_CHANGE"
    assert proposal["changed_why"]["orders_created"] == 0

    confirmed = confirm_prospective_observation_and_persist(
        proposal,
        root=tmp_path,
        scenario_id=REAL_MU_PROSPECTIVE_SCENARIO_ID,
    )
    assert confirmed["prospective_episode_count"] == 1
    assert confirmed["operator_action_count"] == 2
    assert confirmed["book"]["book_hash"] == workspace["book"]["book_hash"]
    assert confirmed["orders"] == []
    assert confirmed["fills"] == []
    assert confirmed["book"]["positions"] == []
    assert confirmed["reviews"][0]["outcome"] == "ABSTAIN"
    assert confirmed["reviews"][0]["target_quantity"] == "0"
    assert confirmed["prospective_proposals"][-1]["request"]["locator"] == (
        RECONCILIATION_LOCATOR
    )
    assert confirmed["prospective_proposals"][-1]["request"][
        "operator_rationale"
    ] == request["operator_rationale"]

    reopened = load_prospective_workspace(
        root=tmp_path,
        scenario_id=REAL_MU_PROSPECTIVE_SCENARIO_ID,
    )
    reconstructed = reconstruct_prospective_workspace(
        reopened["events"], scenario_id=REAL_MU_PROSPECTIVE_SCENARIO_ID
    )
    assert canonical_document_bytes(reopened) == canonical_document_bytes(reconstructed)


def test_real_mu_app_routes_to_runtime_observation_product(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    def _denied(*_args: object, **_kwargs: object) -> None:
        raise OSError("GV_REAL_MU_NETWORK_DENIED")

    monkeypatch.setattr(socket, "create_connection", _denied)
    monkeypatch.setenv("GV_OPERATED_SCENARIO_ID", REAL_MU_PROSPECTIVE_SCENARIO_ID)
    monkeypatch.setenv("GV_OPERATED_PORTFOLIO_HOME", str(tmp_path / "workspace"))
    monkeypatch.chdir(ROOT)

    app = AppTest.from_file(str(ROOT / "operated_portfolio_app.py")).run(timeout=120)
    assert not app.exception, app.exception
    blob = _app_blob(app)
    assert "GV Real Evidence — MU Paper Decision" in blob
    assert "instruments=1" in blob
    assert "episodes=0" in blob
    assert "operator_actions=0" in blob
    assert "no score, alpha" in blob.lower()
    assert "MU" in blob
    assert "ABSTAIN" in blob
    assert "NO_POSITION" in blob
    assert "Immutable source evidence" in blob
    assert "Instrument identity" in blob
    assert "Same-evidence decision comparison" in blob
    assert "same_immutable_evidence=true" in blob
    assert "shadow_reads_portfolio_decision=false" in blob
    assert "shadow_mutation_authorized=false" in blob
    assert "NOT_YET_RECORDED" in blob
    assert "residual=0" in blob
