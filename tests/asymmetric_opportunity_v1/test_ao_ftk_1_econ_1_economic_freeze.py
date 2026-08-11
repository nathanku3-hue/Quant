"""AO-FTK-1-ECON-1 economic asymmetry freeze — custody + fail-closed tests.

No trial debit, no economic label join, no evaluation, no alpha claim.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.asymmetric_opportunity_v1.ao_ftk_1_econ_1_contract import (
    EFFECTIVE_DECISION_DOF,
    FORBIDDEN_E_AUTHORITY_KEYS,
    FREEZE_ID,
    KERNEL_ID,
    LABEL_HASH_PROCEDURE_REL,
    LABEL_IDENTITY_REL,
    L7_ROUTE,
    MACHINE_FREEZE_REL,
    MD_FREEZE_REL,
    PARENT_L4_FREEZE_REL,
    PARENT_L5_WORK_COMMIT,
    PARENT_PROGRAM,
    PLAN_ID,
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
    load_label_hash_procedure,
    load_label_identity,
    load_machine_freeze,
    load_parent_l4_freeze,
    load_receipt,
    pin_operator_identity,
    trial_debit,
    validate_econ_freeze,
)


REPO = Path(__file__).resolve().parents[2]


def test_authority_artifacts_landed() -> None:
    paths = [
        REPO / MACHINE_FREEZE_REL,
        REPO / MD_FREEZE_REL,
        REPO / RECEIPT_REL,
        REPO / LABEL_IDENTITY_REL,
        REPO / LABEL_HASH_PROCEDURE_REL,
        REPO
        / "docs/context/e2e_evidence/ao_ftk_1_econ_1_l7_route_select.json",
    ]
    for path in paths:
        assert path.is_file(), path


def test_econ_freeze_schema_validates() -> None:
    doc = load_machine_freeze(REPO)
    errors = validate_econ_freeze(doc)
    assert errors == [], errors
    assert_valid_econ_freeze(doc)

    assert doc["freeze_id"] == FREEZE_ID
    assert doc["parent_program"] == PARENT_PROGRAM
    assert doc["l7_route"] == L7_ROUTE
    assert doc["status"] == "ECON_FREEZE_PASS_WAITING_OWNER_NUMERICS"
    assert doc["next_phase"] == "WAIT_OWNER_L5_ECONOMIC"
    assert doc["parent_l5_work_commit"] == PARENT_L5_WORK_COMMIT
    assert doc["authorized_phase"] == "ECONOMIC_ESTIMAND_FREEZE"
    assert doc["second_l5"] == "NOT_AUTHORIZED"


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


def test_e1_through_e12_present_no_e13_e14_authority() -> None:
    doc = load_machine_freeze(REPO)
    estimand = doc["estimand"]
    for key in REQUIRED_E_KEYS:
        assert key in estimand, key
        assert "form" in estimand[key]
        assert "value" in estimand[key]
        assert "value_owner" in estimand[key]
    for bad in FORBIDDEN_E_AUTHORITY_KEYS:
        assert bad not in estimand


def test_e11_economic_pack_distinct_from_sensing() -> None:
    doc = load_machine_freeze(REPO)
    e11 = doc["estimand"]["E11"]["value"]
    identity_path = e11["identity_path"]
    assert "ao_ftk_1_econ_1_label_custody" in identity_path
    assert "ao_ftk_1_20260812_label_custody" not in identity_path
    assert e11["bytes_joined"] is False
    assert e11["join_authorized"] is False
    assert (
        e11["sensing_pack_path_forbidden_reuse"].rstrip("/")
        == str(SENSING_LABEL_CUSTODY_DIR_REL).replace("\\", "/").rstrip("/")
        or "ao_ftk_1_20260812_label_custody" in e11["sensing_pack_path_forbidden_reuse"]
    )

    identity = load_label_identity(REPO)
    proc = load_label_hash_procedure(REPO)
    assert identity["LABEL_IDENTITY_FROZEN"] is True
    assert identity["LABEL_BYTES_JOINED"] is False
    assert identity["join_authorized"] is False
    assert identity["label_pack_type"] == "ECONOMIC"
    assert proc["LABEL_HASH_PROCEDURE_FROZEN"] is True
    assert proc["LABEL_BYTES_JOINED"] is False
    assert proc["seal_name"] == "SEALED_UNJOINED"

    custody_dir = REPO / "data/prebreakout/compiled/ao_ftk_1_econ_1_label_custody"
    for p in custody_dir.iterdir():
        assert p.suffix.lower() != ".parquet", p
        assert "joined" not in p.name.lower() or p.suffix == ".json"

    sensing_identity = REPO / (
        "data/prebreakout/compiled/ao_ftk_1_20260812_label_custody/"
        "development_label_pack.identity.json"
    )
    assert sensing_identity.is_file()
    assert sensing_identity.resolve() != (REPO / LABEL_IDENTITY_REL).resolve()


def test_material_trials_not_debited_this_turn() -> None:
    doc = load_machine_freeze(REPO)
    plan = doc["material_trial_debit_plan"]
    assert plan["plan_id"] == PLAN_ID
    assert plan["material_trials_total_remaining_before_trial2"] == 2
    assert plan["next_debit"] == 1
    assert plan["remaining_after_trial2"] == 1
    assert plan["debit_this_turn"] is False
    assert plan["debit_trigger"] == "ECONOMIC_L5_AUTHORIZATION_RECEIPT"

    receipt = load_receipt(REPO)
    assert receipt["material_trials_charged_this_turn"] == 0
    assert receipt["firewall"]["material_trials_remaining"] == 2


def test_d7_not_invented_blocked_unset() -> None:
    doc = load_machine_freeze(REPO)
    d7 = doc["d6_d9_mapping"]["D7_CONFIRMATION_TIMING"]
    assert d7["rule_status"] == "BLOCKED_UNSET"
    assert d7["invented_this_freeze"] is False
    assert d7["l5_blocker"] is True
    assert doc["estimand"]["E10"]["value"]["D7_CONFIRMATION_TIMING"] == "BLOCKED_UNSET"


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


def test_l5_not_authorized() -> None:
    doc = load_machine_freeze(REPO)
    assert doc["l5_authorized"] is False
    assert doc["economic_l5_authorized"] is False
    assert doc["l5_auto_open"] is False
    assert doc["runnable_evaluation"] is False
    assert doc["label_bytes_joined"] is False
    assert isinstance(doc["l5_blockers"], list) and len(doc["l5_blockers"]) >= 1


def test_fail_closed_label_join_when_l5_false() -> None:
    with pytest.raises(Econ1FailClosedError, match="economic_label_join"):
        economic_label_join(economic_l5_authorized=False)
    with pytest.raises(Econ1FailClosedError, match="economic_label_join"):
        economic_label_join()


def test_fail_closed_trial_debit_when_l5_false() -> None:
    with pytest.raises(Econ1FailClosedError, match="trial_debit"):
        trial_debit(economic_l5_authorized=False)
    with pytest.raises(Econ1FailClosedError, match="trial_debit"):
        trial_debit()


def test_fail_closed_evaluator_run_when_l5_false() -> None:
    ev = EconomicEvaluator()
    with pytest.raises(Econ1FailClosedError, match="economic_evaluator.run"):
        ev.run(economic_l5_authorized=False)
    with pytest.raises(Econ1FailClosedError, match="economic_evaluator.run"):
        ev.run()
    with pytest.raises(Econ1FailClosedError, match="economic_evaluator.run"):
        ev.run(economic_l5_authorized=False, runnable_evaluation=True)


def test_fail_closed_still_blocks_partial_l5_flags() -> None:
    with pytest.raises(Econ1FailClosedError):
        economic_label_join(economic_l5_authorized=False, join_authorized=True)
    with pytest.raises(Econ1FailClosedError):
        trial_debit(economic_l5_authorized=False, debit_units=1)
    with pytest.raises(Econ1FailClosedError, match="not_implemented_in_freeze"):
        economic_label_join(economic_l5_authorized=True, join_authorized=True)
    with pytest.raises(Econ1FailClosedError, match="not_implemented_in_freeze"):
        trial_debit(economic_l5_authorized=True, debit_units=1)
    with pytest.raises(Econ1FailClosedError, match="not_implemented_in_freeze"):
        EconomicEvaluator().run(
            economic_l5_authorized=True, runnable_evaluation=True
        )


def test_receipt_matches_freeze_firewall() -> None:
    receipt = load_receipt(REPO)
    assert receipt["freeze_id"] == FREEZE_ID
    assert receipt["parent_program"] == PARENT_PROGRAM
    assert receipt["terminal_verdict"] == "ECON_FREEZE_PASS_WAITING_OWNER_NUMERICS"
    assert receipt["l5_authorized"] is False
    assert receipt["economic_l5_authorized"] is False
    assert receipt["material_trials_charged_this_turn"] == 0
    assert receipt["label_bytes_joined"] is False
    assert receipt["financial_alpha_evidence"] == 0
    assert receipt["next_phase"] == "WAIT_OWNER_L5_ECONOMIC"
    assert receipt["surface_dof"] == 2
    assert receipt["stop_lines_hit"] == []
    assert "L5_AUTHORIZE_ECONOMIC" in receipt["next_owner_action"]

    freeze = load_machine_freeze(REPO)
    assert freeze["l5_authorized"] is False
    assert freeze["financial_alpha_evidence"] == 0
    assert freeze["material_trial_debit_plan"]["debit_this_turn"] is False


def test_parent_l4_exists_and_parent_path_pinned() -> None:
    assert (REPO / PARENT_L4_FREEZE_REL).is_file()
    doc = load_machine_freeze(REPO)
    assert doc["parent_l4_freeze"] == str(PARENT_L4_FREEZE_REL).replace("\\", "/")


def test_l7_route_select_receipt() -> None:
    path = REPO / "docs/context/e2e_evidence/ao_ftk_1_econ_1_l7_route_select.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["l7_route"] == L7_ROUTE
    assert data["l7_select_effective"] is True
    assert data["second_l5"] == "NOT_AUTHORIZED"
    assert data["material_trial_debit_this_turn"] == "FORBIDDEN"
