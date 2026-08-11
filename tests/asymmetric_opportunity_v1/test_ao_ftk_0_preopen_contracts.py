from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.asymmetric_opportunity_v1.ao_ftk_0_contract import (
    ALLOWED_API_SURFACE,
    CONSTITUTION,
    FORBIDDEN_QM_API_TOKENS,
    KERNEL_ID,
    MACHINE_FREEZE_REL,
    MD_FREEZE_REL,
    PREOPEN_EVIDENCE_REL,
    QM_PARK_REL,
    REQUIRED_OPERATOR_IDS,
    REQUIRED_PRIMITIVE_IDS,
    SLICE_ID,
    assert_no_qm_terms_in_ftk_api,
    assert_valid_machine_freeze,
    bound_primitives,
    build_preopen_evidence,
    decision_operators,
    ftk_api_surface_tokens,
    load_machine_freeze,
    load_qm_park_receipt,
    refuse_ok_sbi_s2,
    refuse_outcome_open,
    refuse_q_amendment_spend,
    refuse_qm_revival,
    validate_machine_freeze,
)


REPO = Path(__file__).resolve().parents[2]


def test_authority_artifacts_landed() -> None:
    paths = [
        REPO / MACHINE_FREEZE_REL,
        REPO / MD_FREEZE_REL,
        REPO / QM_PARK_REL,
        REPO / PREOPEN_EVIDENCE_REL,
    ]
    for path in paths:
        assert path.is_file(), path


def test_machine_freeze_preopen_firewall() -> None:
    freeze = load_machine_freeze(REPO)
    errors = validate_machine_freeze(freeze)
    assert errors == [], errors
    assert_valid_machine_freeze(freeze)

    assert freeze["slice_id"] == SLICE_ID
    assert freeze["kernel_id"] == KERNEL_ID
    assert freeze["financial_alpha_evidence"] == 0
    assert freeze["outcome_open_authorized"] is False
    assert freeze["runnable_evaluation"] is False
    assert freeze["qm_terms_forbidden"] is True
    assert freeze["charged_development_read"] == "FORBIDDEN_THIS_TURN"
    assert freeze["terminal_preopen_verdict"] == "READY_FOR_LATER_CHARGED_DEVELOPMENT_READ"
    assert freeze["constitution"]
    assert "Q/M is terminal" in freeze["constitution"]
    assert CONSTITUTION.split(".")[0] in freeze["constitution"]


def test_primitives_bound_no_invention() -> None:
    freeze = load_machine_freeze(REPO)
    prims = {p["primitive_id"]: p for p in bound_primitives(freeze)}
    for pid in REQUIRED_PRIMITIVE_IDS:
        assert pid in prims
        assert prims[pid]["bind_status"] == "BOUND"
        assert prims[pid]["identity_keys"]["ticker_entity_permno_fallback"] == "FORBIDDEN"
        assert "no_bridge_proof" in prims[pid]

    # Revenue is denominator only, not a decision node.
    assert prims["FTK_PRIM_IQ_TOTAL_REV"]["role"].startswith("RATIO_DENOMINATOR")

    parked = {u["primitive_id"]: u for u in freeze["unbound_or_parked_inputs"]}
    assert parked["ROIC"]["status"] == "UNBOUND_FORBIDDEN_INVENTION"
    assert parked["REVENUE_DIRECTION_NODE"]["status"] == "PARKED"


def test_operator_family_is_one_to_two_dof() -> None:
    freeze = load_machine_freeze(REPO)
    ops = decision_operators(freeze)
    assert len(ops) == 2
    assert freeze["complexity_ledger"]["effective_decision_dof_frozen"] == 2
    assert freeze["complexity_ledger"]["max_effective_decision_dof"] == 2
    assert {op["operator_id"] for op in ops} == set(REQUIRED_OPERATOR_IDS)
    assert freeze["operator_routing"]["mode"] == "DOMAIN_LIMITED_EX_ANTE"
    assert freeze["search_budget"]["material_trials_charged_this_slice"] == 0
    assert freeze["search_budget"]["material_trials_remaining"] == 3


def test_no_qm_terms_in_ftk_api_surface() -> None:
    freeze = load_machine_freeze(REPO)
    assert_no_qm_terms_in_ftk_api(freeze)
    surface = ftk_api_surface_tokens(freeze)
    for token in FORBIDDEN_QM_API_TOKENS:
        assert token not in surface
    # Allowed surface keys remain present as conceptual members.
    assert ALLOWED_API_SURFACE.issubset(surface)


def test_qm_park_receipt_terminal() -> None:
    park = load_qm_park_receipt(REPO)
    assert park["Q_SOURCE_STATUS"] == "Q_SOURCE_BLOCKED_TERMINAL"
    assert park["OK_SBI_S2"] == "NOT_AUTHORIZED"
    assert park["QM_REVIVAL_IN_FTK"] == "FORBIDDEN"
    assert park["Q_AMENDMENT_STATUS"] == "AVAILABLE_UNSPENT"
    assert park["q_amendment_cycles_used"] == 0
    assert park["financial_alpha_evidence"] == 0
    assert park["ftk_relationship"]["ao_ftk_0_uses_qm_geometry"] is False


def test_label_custody_plan_only_no_join() -> None:
    freeze = load_machine_freeze(REPO)
    plan = freeze["label_custody_plan"]
    assert plan["join_authorized"] is False
    assert plan["join_performed"] is False
    assert plan["outcome_inspected"] is False
    assert plan["right_tail_definition"] == "BLOCKED_UNSET"
    assert plan["catastrophe_definition"] == "BLOCKED_UNSET"
    assert plan["seal_status"] == "PLAN_ONLY_UNSEALED"


def test_full_w3_abstention_preserved() -> None:
    freeze = load_machine_freeze(REPO)
    d = freeze["denominator_and_abstention"]
    assert d["denominator"] == "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1"
    assert d["complete_case_denominator"] == "FORBIDDEN"
    assert d["coverage_pass_fail_gate"] == "FORBIDDEN"
    assert d["security_level_return_imputation"] == "FORBIDDEN"
    assert d["abstention"]["selected"] is False
    assert d["abstention"]["risky_weight"] == 0.0
    assert d["abstention"]["removed_from_denominator"] is False
    statuses = freeze["applicability_taxonomy"]["statuses"]
    for required in (
        "W3_INELIGIBLE",
        "NOT_APPLICABLE",
        "APPLICABLE_OBSERVED",
        "APPLICABLE_UNOBSERVED",
    ):
        assert required in statuses


def test_refuse_firewalls() -> None:
    with pytest.raises(ValueError, match="ao_ftk_0_outcome_open_forbidden"):
        refuse_outcome_open()
    with pytest.raises(ValueError, match="ao_ftk_0_outcome_open_forbidden"):
        refuse_outcome_open(outcome_open_authorized=True)
    with pytest.raises(ValueError, match="ao_ftk_0_qm_revival_forbidden"):
        refuse_qm_revival()
    with pytest.raises(ValueError, match="ao_ftk_0_ok_sbi_s2_not_authorized"):
        refuse_ok_sbi_s2()
    with pytest.raises(ValueError, match="ao_ftk_0_q_amendment_spend_forbidden"):
        refuse_q_amendment_spend()


def test_preopen_evidence_receipt_matches_contract() -> None:
    evidence_path = REPO / PREOPEN_EVIDENCE_REL
    assert evidence_path.is_file()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["slice_id"] == SLICE_ID
    assert evidence["terminal_preopen_verdict"] == "READY_FOR_LATER_CHARGED_DEVELOPMENT_READ"
    assert evidence["outcome_open_authorized"] is False
    assert evidence["runnable_evaluation"] is False
    assert evidence["financial_alpha_evidence"] == 0
    assert evidence["qm_revival_attempted"] is False
    assert evidence["q_amendment_cycles_used"] == 0
    assert evidence["ok_sbi_gates_filled"] is False
    assert evidence["label_custody_plan_join_authorized"] is False
    assert len(evidence["operator_freeze"]) == 2
    assert len(evidence["primitive_bind_summary"]) == 4

    # Regenerated body (without SHA pins) must still validate.
    live = build_preopen_evidence(repo_root=REPO)
    assert live["terminal_preopen_verdict"] == evidence["terminal_preopen_verdict"]
    assert live["operator_freeze"] == evidence["operator_freeze"]
