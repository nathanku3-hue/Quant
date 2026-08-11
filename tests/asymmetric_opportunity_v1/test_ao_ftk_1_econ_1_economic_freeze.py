"""AO-FTK-1-ECON-1 economic freeze + Trial 2 long-session tests.

After ACCEPT_DRAFT Trial 2: L5 complete, waiting owner L7.
No FTK-2, no capital, no alpha claim, no second eval.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.asymmetric_opportunity_v1.ao_ftk_1_econ_1_contract import (
    ECONOMIC_CLOCK_CLASS,
    EFFECTIVE_DECISION_DOF,
    FORBIDDEN_E_AUTHORITY_KEYS,
    FREEZE_ID,
    KERNEL_ID,
    LABEL_HASH_PROCEDURE_REL,
    LABEL_IDENTITY_REL,
    L7_ROUTE,
    MACHINE_FREEZE_REL,
    MD_FREEZE_REL,
    OWNER_BIND_RECEIPT_REL,
    PARENT_L4_FREEZE_REL,
    PARENT_L5_WORK_COMMIT,
    PARENT_PROGRAM,
    PLAN_ID,
    POST_TRIAL2_STATUSES,
    RECEIPT_REL,
    REQUIRED_E_KEYS,
    REQUIRED_OPERATOR_IDS,
    SENSING_LABEL_CUSTODY_DIR_REL,
    Econ1FailClosedError,
    EconomicEvaluator,
    assert_no_qm_terms_in_econ_surface,
    assert_surface_pins_match_parent,
    assert_valid_econ_freeze,
    economic_label_join,
    evaluate_l5_readiness,
    load_label_hash_procedure,
    load_label_identity,
    load_machine_freeze,
    load_owner_bind_receipt,
    load_parent_l4_freeze,
    load_receipt,
    pin_operator_identity,
    refuse_invented_bind,
    trial_debit,
    validate_econ_freeze,
)
from research.asymmetric_opportunity_v1 import ao_ftk_1_econ_1_trial2 as t2


REPO = Path(__file__).resolve().parents[2]


def test_authority_artifacts_landed() -> None:
    paths = [
        REPO / MACHINE_FREEZE_REL,
        REPO / RECEIPT_REL,
        REPO / OWNER_BIND_RECEIPT_REL,
        REPO / LABEL_IDENTITY_REL,
        REPO / LABEL_HASH_PROCEDURE_REL,
        REPO / t2.L5_READY_REL,
        REPO / t2.L5_AUTH_REL,
        REPO / t2.L5_DEBIT_REL,
        REPO / t2.L5_JOIN_REL,
        REPO / t2.L5_RUN_REL,
        REPO / t2.L6_REL,
        REPO / t2.L7_REL,
        REPO / "docs/context/e2e_evidence/ao_ftk_1_econ_1_l7_route_select.json",
    ]
    for path in paths:
        assert path.is_file(), path


def test_econ_freeze_schema_validates_post_trial2() -> None:
    doc = load_machine_freeze(REPO)
    errors = validate_econ_freeze(doc)
    assert errors == [], errors
    assert_valid_econ_freeze(doc)

    assert doc["freeze_id"] == FREEZE_ID
    assert doc["parent_program"] == PARENT_PROGRAM
    assert doc["l7_route"] == L7_ROUTE
    assert doc["status"] in POST_TRIAL2_STATUSES
    assert doc["next_phase"] == "L7_ROADMAP_DECISION"
    assert doc["parent_l5_work_commit"] == PARENT_L5_WORK_COMMIT
    assert doc["owner_bind"]["verdict"] == "PASS_L5_READY"
    assert doc["owner_bind"]["l5_ready"] is True
    assert doc["l5_ready"] is True


def test_effective_dof_frozen_at_two_matches_parent() -> None:
    doc = load_machine_freeze(REPO)
    parent = load_parent_l4_freeze(REPO)
    assert doc["surface_inheritance"]["effective_decision_dof"] == EFFECTIVE_DECISION_DOF
    assert parent["effective_decision_dof"] == 2
    assert_surface_pins_match_parent(doc, parent)

    ops = doc["surface_inheritance"]["operators"]
    assert len(ops) == 2
    assert {op["operator_id"] for op in ops} == set(REQUIRED_OPERATOR_IDS)
    assert doc["surface_inheritance"]["kernel_id"] == KERNEL_ID
    assert doc["surface_inheritance"]["routing"] == "DOMAIN_LIMITED_EX_ANTE"
    for op in ops:
        assert op["operator_bytes"] == "FROZEN"
        assert pin_operator_identity(op) == op["immutability_pin"]


def test_e1_through_e12_owner_bound_accept_draft() -> None:
    doc = load_machine_freeze(REPO)
    estimand = doc["estimand"]
    for key in REQUIRED_E_KEYS:
        assert key in estimand, key
        assert "form" in estimand[key]
        assert "value" in estimand[key]
        assert "value_owner" in estimand[key]
    for bad in FORBIDDEN_E_AUTHORITY_KEYS:
        assert bad not in estimand

    assert estimand["E1"]["value"]["H_VALUE"] == 63
    assert estimand["E1"]["value_owner"] == "OWNER_BOUND"
    assert estimand["E2"]["value_owner"] == "OWNER_BOUND"
    assert estimand["E2"]["value"]["same_return_convention_ftk_and_w3"] is True
    assert estimand["E3"]["value_owner"] == "OWNER_BOUND"
    assert estimand["E3"]["value"]["execution_lag"] == 1
    assert estimand["E3"]["value"]["cost_bps_round_trip"] == 20
    assert estimand["E3"]["value"]["free_fit"] is False
    assert estimand["E4"]["value"]["RIGHT_TAIL_PERCENTILE"] == 0.90
    assert estimand["E5"]["value"]["CATASTROPHE_PERCENTILE"] == 0.10
    assert estimand["E6"]["value"]["delta_J_required"] == 0.0
    assert estimand["E6"]["value"]["INTERPRETATION"] == "POSITIVE_NET_EDGE_SCREEN"
    assert estimand["E6"]["value"]["CAPITAL_MATERIALITY_FLOOR"] == "NOT_YET_GRANTED"
    assert estimand["E7"]["value"]["K"] == 20
    assert "DUAL_NODE_EQUAL_WEIGHT_RANK_THEN_TOP_K" in estimand["E7"]["value"]["score_map"]


def test_e11_economic_pack_joined_distinct_from_sensing() -> None:
    doc = load_machine_freeze(REPO)
    e11 = doc["estimand"]["E11"]["value"]
    identity_path = e11["identity_path"]
    assert "ao_ftk_1_econ_1_label_custody" in identity_path
    assert "ao_ftk_1_20260812_label_custody" not in identity_path
    assert e11["bytes_joined"] is True
    assert e11["join_authorized"] is True

    identity = load_label_identity(REPO)
    proc = load_label_hash_procedure(REPO)
    assert identity["LABEL_IDENTITY_FROZEN"] is True
    assert identity["LABEL_BYTES_JOINED"] is True
    assert identity["join_performed"] is True
    assert identity["label_pack_type"] == "ECONOMIC"
    assert proc["LABEL_HASH_PROCEDURE_FROZEN"] is True
    assert proc["LABEL_BYTES_JOINED"] is True

    jsonl = REPO / t2.JOINED_LABELS_JSONL_REL
    assert jsonl.is_file()
    sensing_identity = REPO / (
        "data/prebreakout/compiled/ao_ftk_1_20260812_label_custody/"
        "development_label_pack.identity.json"
    )
    assert sensing_identity.is_file()
    assert sensing_identity.resolve() != (REPO / LABEL_IDENTITY_REL).resolve()


def test_material_trial_debited_exactly_one() -> None:
    doc = load_machine_freeze(REPO)
    plan = doc["material_trial_debit_plan"]
    assert plan["plan_id"] == PLAN_ID
    assert plan["material_trials_total_remaining_before_trial2"] == 2
    assert plan["next_debit"] == 1
    assert plan["remaining_after_trial2"] == 1
    assert plan["debit_this_turn"] is True
    assert plan["debit_trigger"] == "ECONOMIC_L5_AUTHORIZATION_RECEIPT"

    debit = json.loads((REPO / t2.L5_DEBIT_REL).read_text(encoding="utf-8"))
    assert debit["debit_units"] == 1
    assert debit["before"] == {"charged": 1, "remaining": 2}
    assert debit["after"] == {"charged": 2, "remaining": 1}
    assert debit["multi_debit"] is False


def test_d7_out_of_scope_not_invented() -> None:
    doc = load_machine_freeze(REPO)
    d7 = doc["d6_d9_mapping"]["D7_CONFIRMATION_TIMING"]
    assert d7["rule_status"] == "EXPLICITLY_OUT_OF_SCOPE_THIS_TRIAL"
    assert d7["invented_this_freeze"] is False
    assert d7["L6_treatment"] == "NOT_IN_SCOPE"
    assert (
        doc["estimand"]["E10"]["value"]["D7_CONFIRMATION_TIMING"]
        == "EXPLICITLY_OUT_OF_SCOPE_THIS_TRIAL"
    )

    l6 = json.loads((REPO / t2.L6_REL).read_text(encoding="utf-8"))
    d7_layer = next(x for x in l6["layers"] if x["layer"] == "D7_CONFIRMATION")
    assert d7_layer["status"] == "NOT_IN_SCOPE"


def test_qm_terms_absent_alpha_zero() -> None:
    doc = load_machine_freeze(REPO)
    assert_no_qm_terms_in_econ_surface(doc)
    assert doc["qm_terms_forbidden"] is True
    assert doc["financial_alpha_evidence"] == 0
    assert doc["capital_authority"] is False
    assert doc["q_source_status"] == "Q_SOURCE_BLOCKED_TERMINAL"
    assert doc["ok_sbi_s2"] == "NOT_AUTHORIZED"
    assert doc["qm_revival_in_ftk"] == "FORBIDDEN"
    assert doc["ao_ftk_2"] == "NOT_AUTHORIZED"
    assert doc["l8_bounded_refinement"] == "DEFER"


def test_l5_one_shot_spent() -> None:
    doc = load_machine_freeze(REPO)
    assert doc["l5_authorized"] is True
    assert doc["economic_l5_authorized"] is True
    assert doc["l5_auto_open"] is False
    assert doc["runnable_evaluation"] is False  # spent
    assert doc["label_bytes_joined"] is True
    assert doc["second_l5"] == "NOT_AUTHORIZED"

    auth = json.loads((REPO / t2.L5_AUTH_REL).read_text(encoding="utf-8"))
    assert auth["owner_decision"] == "L5_AUTHORIZE_ECONOMIC"
    assert auth["one_shot"] is True
    assert auth["debit_allowed"] == 1
    assert auth["joins_allowed"] == 1
    assert auth["evals_allowed"] == 1
    assert auth["d7"] == "OUT_OF_SCOPE"
    assert auth["d9_floor"] == 0.0
    assert auth["financial_alpha_evidence"] == 0


def test_fail_closed_without_auth_still() -> None:
    with pytest.raises(Econ1FailClosedError, match="economic_label_join"):
        economic_label_join(economic_l5_authorized=False)
    with pytest.raises(Econ1FailClosedError, match="trial_debit"):
        trial_debit(economic_l5_authorized=False)
    with pytest.raises(Econ1FailClosedError, match="economic_evaluator.run"):
        EconomicEvaluator().run(economic_l5_authorized=False)


def test_transition_position_clock_and_accept_draft_bind() -> None:
    doc = load_machine_freeze(REPO)
    clock = doc["economic_clock"]
    assert clock["economic_clock_class"] == ECONOMIC_CLOCK_CLASS
    assert clock["not_fast_trading"] is True
    assert clock["not_great_enterprise_hodl"] is True
    assert clock["great_enterprise_kernel"] == "OUT_OF_SCOPE"
    assert doc["estimand"]["E1"]["economic_clock_class"] == ECONOMIC_CLOCK_CLASS

    bind = load_owner_bind_receipt(REPO)
    assert bind["economic_clock_class"] == ECONOMIC_CLOCK_CLASS
    assert bind["owner_attachment_present"] is True
    assert bind["ACCEPT_DRAFT"] is True
    assert bind["verdict"] == "PASS_L5_READY"
    assert bind["l5_ready"] is True
    assert bind["outcome_blind"] is True
    assert bind["residual_peek"] is False
    assert bind["binds"]["E1"]["H_VALUE"] == 63
    assert bind["binds"]["E7"]["K"] == 20
    assert bind["binds"]["E10_D7"]["D7_MODE"] == "OUT_OF_SCOPE"


def test_l5_ready_checklist_green() -> None:
    checklist = json.loads((REPO / t2.L5_READY_REL).read_text(encoding="utf-8"))
    assert checklist["l5_ready"] is True
    assert checklist["verdict"] == "PASS_L5_READY"
    assert checklist["blockers_remaining"] == []

    doc = load_machine_freeze(REPO)
    readiness = evaluate_l5_readiness(doc)
    assert readiness["l5_ready"] is True
    assert readiness["blockers_remaining"] == []


def test_trial2_run_and_l6_first_fail_d2() -> None:
    run = json.loads((REPO / t2.L5_RUN_REL).read_text(encoding="utf-8"))
    assert run["run_id"] == t2.RUN_ID
    assert run["evaluation_count"] == 1
    assert run["second_run"] is False
    assert run["effective_decision_dof"] == 2
    assert run["financial_alpha_evidence"] == 0
    assert run["binds"]["H"] == 63
    assert run["binds"]["K"] == 20
    assert run["binds"]["delta_J_required"] == 0.0
    assert run["payoff"]["d9_interpretation"] == "POSITIVE_NET_EDGE_SCREEN"
    assert run["market_probe"]["full_w3_market_total_return_admitted"] is False
    assert run["evaluation_status"] == "COMPLETED_BLOCKED_FULL_W3_MARKET_CUSTODY_MISSING"
    assert run["forbidden_checks"]["asymmetric_return_ftk_vs_w3"] is False
    assert run["forbidden_checks"]["threshold_grid"] is False

    l6 = json.loads((REPO / t2.L6_REL).read_text(encoding="utf-8"))
    assert l6["first_fail_layer"] == "D2_DATA_OBSERVABLE"
    assert "HOLD_OR_ADMIT_FULL_W3" in l6["failure_route"]
    assert l6["financial_alpha_evidence"] == 0
    assert l6["information_gain"]
    d1 = next(x for x in l6["layers"] if x["layer"] == "D1_CUSTODY_PIT")
    assert d1["status"] == "PASS"
    d2 = next(x for x in l6["layers"] if x["layer"] == "D2_DATA_OBSERVABLE")
    assert d2["status"] == "FAIL"
    assert d2["stop_here"] is True


def test_l7_owner_packet_hard_stop() -> None:
    l7 = json.loads((REPO / t2.L7_REL).read_text(encoding="utf-8"))
    assert l7["worker_did_not_select_next_slice"] is True
    assert l7["AO_FTK_2"] == "NOT_OPENED"
    assert l7["L8"] == "not executed"
    assert l7["financial_alpha_evidence"] == 0
    assert l7["trials_remaining"] == 1
    assert l7["session_path"] == "C_TRIAL2_COMPLETE"
    assert l7["loop_phase"] == "L7_ROADMAP_DECISION"
    assert l7["next_owner_action"] == "L7 route only"
    routes = {r["route"] for r in l7["recommended_routes"]}
    assert "HOLD_EVIDENCE" in routes
    assert "STOP_TRACK" in routes
    assert "AO-FTK-2" not in routes


def test_sot_post_trial2() -> None:
    sot = json.loads(
        (REPO / "docs/context/research_loop_state_current.json").read_text(encoding="utf-8")
    )
    assert sot["process"]["loop_phase"] == "L7_ROADMAP_DECISION"
    assert sot["product"]["financial_alpha_evidence"] == 0
    econ = next(t for t in sot["active_tracks"] if t["track_id"] == "AO-FTK-1-ECON-1")
    assert econ["material_trials_remaining"] == 1
    assert econ["label_bytes_joined"] is True
    assert econ["session_path"] == "C_TRIAL2_COMPLETE"
    assert econ["first_fail_layer"] == "D2_DATA_OBSERVABLE"
    assert econ["worker_status"] == "CLOSED / NO_WORKER"
    parent = next(t for t in sot["active_tracks"] if t["track_id"] == "AO-FTK-1")
    assert parent["material_trials_charged_this_slice"] == 2
    assert parent["material_trials_remaining"] == 1


def test_cannot_invent_e2_e3_d7_helpers() -> None:
    with pytest.raises(Econ1FailClosedError, match="refuse_invent"):
        refuse_invented_bind("E2")
    with pytest.raises(Econ1FailClosedError, match="refuse_invent"):
        refuse_invented_bind("D7")


def test_attachment_concrete_and_no_placeholders() -> None:
    t2.assert_attachment_concrete()
    att = t2.OWNER_ATTACHMENT
    assert att["H_VALUE"] == 63
    assert att["K"] == 20
    assert att["L5_AUTHORIZE_ECONOMIC"] is True
    assert att["ACCEPT_DRAFT"] is True
    assert att["D7_MODE"] == "OUT_OF_SCOPE"


def test_dof_two_pins_stable_after_trial2() -> None:
    doc = load_machine_freeze(REPO)
    parent = load_parent_l4_freeze(REPO)
    assert_surface_pins_match_parent(doc, parent)
    assert doc["surface_inheritance"]["effective_decision_dof"] == 2
    assert doc["surface_inheritance"]["silent_one_dof_collapse"] == "FORBIDDEN"
    assert doc["surface_inheritance"]["third_decision_dof"] == "FORBIDDEN"
    score_map = doc["estimand"]["E7"]["value"]["score_map"]
    assert "DUAL_NODE_EQUAL_WEIGHT_RANK_THEN_TOP_K" in score_map


def test_receipt_matches_post_trial_firewall() -> None:
    receipt = load_receipt(REPO)
    assert receipt["freeze_id"] == FREEZE_ID
    assert receipt["session_path"] == "C_TRIAL2_COMPLETE"
    assert receipt["economic_l5_authorized"] is True
    assert receipt["material_trials_remaining"] == 1
    assert receipt["label_bytes_joined"] is True
    assert receipt["financial_alpha_evidence"] == 0
    assert receipt["first_fail_layer"] == "D2_DATA_OBSERVABLE"
    assert receipt["next_phase"] == "L7_ROADMAP_DECISION"


def test_md_freeze_optional_but_machine_required() -> None:
    assert (REPO / MACHINE_FREEZE_REL).is_file()
    # md freeze may lag; do not hard-fail session if only machine freeze updated
    _ = MD_FREEZE_REL
