"""Focused tests for the independent same-evidence MU shadow comparison."""

from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path

import pytest

import core.gv_v2_mu_nvda_shadow_decision as shadow_module
from core.gv_fs0_canonical import canonical_document_bytes
from core.gv_v2_mu_nvda_reconciliation import load_verified_mu_nvda_reconciliation
from core.gv_v2_mu_nvda_shadow_decision import (
    MU_CLAIM_PATH,
    NVDA_FACT_SET_PATH,
    MuNvdaShadowDecisionError,
    build_mu_nvda_shadow_decision,
    load_mu_nvda_shadow_decision,
    verify_mu_nvda_shadow_decision,
)
from gv_portfolio_v0.operated_scenarios import REAL_MU_PROSPECTIVE_SCENARIO_ID
from gv_portfolio_v0.operated_storage import (
    ensure_prospective_workspace,
    reject_prospective_observation_and_persist,
)
from gv_portfolio_v0.prospective import (
    ProspectiveOperationError,
    preview_runtime_observation,
)
from views.gv_prospective_paper_workspace import (
    _decision_free_evidence_identity,
    _real_mu_comparison_row,
    _real_mu_shadow_context,
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _reject_request(workspace: dict[str, object]) -> dict[str, object]:
    review = workspace["reviews"][0]
    source_evidence = workspace["evidence_references"][0]
    return {
        "content": source_evidence["content"],
        "locator": source_evidence["locator"],
        "observed_at": "2026-08-02T12:30:00.000000Z",
        "review_updates": [
            {
                "instrument_id": review["instrument_id"],
                "outcome": "REJECT",
                "net_score_bps": 0,
                "target_quantity": "0",
                "principal_claim": (
                    "Reject the current MU interpretation because direct physical-supply "
                    "persistence remains unproven."
                ),
            }
        ],
        "operator_rationale": (
            "Treat the missing issuer-specific physical-supply discriminator as a reason "
            "to reject this proposal rather than merely abstain."
        ),
    }


def test_shadow_is_pure_independent_and_abstains_on_current_evidence() -> None:
    mu_claim = _load(MU_CLAIM_PATH)
    nvda_fact_set = _load(NVDA_FACT_SET_PATH)
    mu_before = canonical_document_bytes(mu_claim)
    nvda_before = canonical_document_bytes(nvda_fact_set)

    decision = build_mu_nvda_shadow_decision(
        mu_claim=mu_claim,
        nvda_fact_set=nvda_fact_set,
    )
    verify_mu_nvda_shadow_decision(decision)

    assert decision["outcome"] == "ABSTAIN"
    assert decision["portfolio_mutation_authorized"] is False
    assert decision["reads_existing_portfolio_decision"] is False
    assert "Micron-specific physical supply persistence" in decision["principal_claim"]
    assert "Point-in-time Micron" in decision["missing_discriminator"]
    assert "falsify" in decision["falsifier"]
    assert canonical_document_bytes(mu_claim) == mu_before
    assert canonical_document_bytes(nvda_fact_set) == nvda_before

    parameters = inspect.signature(build_mu_nvda_shadow_decision).parameters
    assert tuple(parameters) == ("mu_claim", "nvda_fact_set")
    source = inspect.getsource(shadow_module)
    assert "from gv_portfolio_v0" not in source
    assert "import gv_portfolio_v0" not in source
    assert "gv_v2_mu_nvda_reconciliation" not in source


def test_shadow_and_operated_decision_use_exact_same_decision_free_evidence() -> None:
    reconciliation = load_verified_mu_nvda_reconciliation()
    shadow = load_mu_nvda_shadow_decision()
    assert canonical_document_bytes(shadow["evidence_identity"]) == (
        canonical_document_bytes(_decision_free_evidence_identity(reconciliation))
    )
    assert shadow["evidence_identity"]["source_bindings"] == {
        "mu_claim_evaluation_hash": reconciliation["source_bindings"][
            "mu_claim_evaluation_hash"
        ],
        "nvda_fact_set_hash": reconciliation["source_bindings"][
            "nvda_fact_set_hash"
        ],
    }


def test_shadow_rejects_tampered_source_evidence() -> None:
    mu_claim = _load(MU_CLAIM_PATH)
    nvda_fact_set = _load(NVDA_FACT_SET_PATH)
    tampered = deepcopy(nvda_fact_set)
    tampered["facts"][0]["exact_excerpt"] = "fabricated"

    with pytest.raises(
        MuNvdaShadowDecisionError,
        match="SHADOW_NVDA_FACT_SET_HASH_MISMATCH",
    ):
        build_mu_nvda_shadow_decision(
            mu_claim=mu_claim,
            nvda_fact_set=tampered,
        )


def test_real_mu_preview_requires_exact_locked_evidence(tmp_path: Path) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=REAL_MU_PROSPECTIVE_SCENARIO_ID,
    )
    request = _reject_request(workspace)
    request["content"] = "operator paraphrase"
    with pytest.raises(
        ProspectiveOperationError,
        match="REAL_MU_EXACT_EVIDENCE_CONTENT_REQUIRED",
    ):
        preview_runtime_observation(workspace, request)


def test_comparison_records_disagreement_and_rejected_final_decision(
    tmp_path: Path,
) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=REAL_MU_PROSPECTIVE_SCENARIO_ID,
    )
    workspace_before = canonical_document_bytes(workspace)
    shadow_context = _real_mu_shadow_context()
    assert canonical_document_bytes(workspace) == workspace_before

    baseline = _real_mu_comparison_row(
        workspace=workspace,
        shadow_context=shadow_context,
    )
    assert baseline["operated_decision"] == "ABSTAIN"
    assert baseline["shadow_decision"] == "ABSTAIN"
    assert baseline["agreement"] is True
    assert baseline["operator_final_decision"] == "NOT_YET_RECORDED"
    assert baseline["same_immutable_evidence"] is True

    proposal = preview_runtime_observation(workspace, _reject_request(workspace))
    preview = _real_mu_comparison_row(
        workspace=workspace,
        shadow_context=shadow_context,
        proposal=proposal,
    )
    assert preview["operated_decision"] == "REJECT"
    assert preview["shadow_decision"] == "ABSTAIN"
    assert preview["agreement"] is False
    assert "disqualifying" in preview["reason_for_disagreement"]
    assert preview["operator_final_decision"] == "PENDING_CONFIRM_OR_REJECT"

    rejected = reject_prospective_observation_and_persist(
        proposal,
        "The operator rejects this interpretation and retains the current ABSTAIN decision.",
        root=tmp_path,
        scenario_id=REAL_MU_PROSPECTIVE_SCENARIO_ID,
    )
    final = _real_mu_comparison_row(
        workspace=rejected,
        shadow_context=shadow_context,
    )
    assert final["operated_decision"] == "REJECT"
    assert final["shadow_decision"] == "ABSTAIN"
    assert final["agreement"] is False
    assert final["operator_final_decision"] == (
        "REJECTED_PROPOSAL_RETAINED_ABSTAIN"
    )
    assert rejected["reviews"][0]["outcome"] == "ABSTAIN"
    assert rejected["book"]["positions"] == []
    assert rejected["orders"] == []
    assert rejected["fills"] == []
