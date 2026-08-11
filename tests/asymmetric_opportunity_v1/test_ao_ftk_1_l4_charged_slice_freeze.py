"""AO-FTK-1 L4 charged-slice freeze — custody + fail-closed tests.

No L5, no trial debit, no label join, no alpha claim.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.asymmetric_opportunity_v1.ao_ftk_1_l4_contract import (
    EFFECTIVE_DECISION_DOF,
    KERNEL_ID,
    L3_DISPOSITION_COMMIT,
    LABEL_HASH_PROCEDURE_REL,
    LABEL_IDENTITY_REL,
    L4FailClosedError,
    MACHINE_FREEZE_REL,
    MD_FREEZE_REL,
    PARENT_FREEZE_COMMIT,
    PLAN_ID,
    RECEIPT_REL,
    REQUIRED_OPERATOR_IDS,
    SLICE_ID,
    Evaluator,
    assert_no_qm_terms_in_l4_surface,
    assert_valid_l4_freeze,
    label_join,
    load_label_hash_procedure,
    load_label_identity,
    load_machine_freeze,
    load_receipt,
    pin_operator_identity,
    trial_debit,
    validate_l4_freeze,
)


REPO = Path(__file__).resolve().parents[2]


def test_authority_artifacts_landed() -> None:
    paths = [
        REPO / MACHINE_FREEZE_REL,
        REPO / MD_FREEZE_REL,
        REPO / RECEIPT_REL,
        REPO / LABEL_IDENTITY_REL,
        REPO / LABEL_HASH_PROCEDURE_REL,
    ]
    for path in paths:
        assert path.is_file(), path


def test_l4_freeze_schema_validates() -> None:
    doc = load_machine_freeze(REPO)
    errors = validate_l4_freeze(doc)
    assert errors == [], errors
    assert_valid_l4_freeze(doc)

    assert doc["slice_id"] == SLICE_ID
    assert doc["parent_freeze_commit"] == PARENT_FREEZE_COMMIT
    assert doc["l3_disposition_commit"] == L3_DISPOSITION_COMMIT
    assert doc["l3_disposition"] == "PASS"
    assert doc["kernel_id"] == KERNEL_ID
    assert doc["status"] == "L4_FREEZE_READY_WAITING_OWNER_L5"
    assert doc["effective_decision_dof"] == EFFECTIVE_DECISION_DOF
    assert doc["next_phase"] == "WAIT_OWNER_L5"


def test_effective_dof_frozen_at_two() -> None:
    doc = load_machine_freeze(REPO)
    assert doc["effective_decision_dof"] == 2
    assert doc["max_effective_decision_dof"] == 2
    assert doc["silent_one_dof_collapse"] == "FORBIDDEN"
    assert doc["third_decision_dof"] == "FORBIDDEN"
    ops = doc["operators"]
    assert len(ops) == 2
    assert {op["operator_id"] for op in ops} == set(REQUIRED_OPERATOR_IDS)
    assert doc["operator_routing"]["mode"] == "DOMAIN_LIMITED_EX_ANTE"
    assert doc["routing"] == "DOMAIN_LIMITED_EX_ANTE"


def test_operator_immutability_pins() -> None:
    doc = load_machine_freeze(REPO)
    for op in doc["operators"]:
        assert op["operator_bytes"] == "FROZEN"
        assert op["immutability_pin"]
        # Recompute pin from frozen fields must match recorded pin.
        recomputed = pin_operator_identity(op)
        assert recomputed == op["immutability_pin"], op["operator_id"]
    margin = next(
        op for op in doc["operators"] if op["operator_id"] == "MARGIN_M1_STATE_MEAN_REVERSION"
    )
    assert margin["m1_bytes_mutation"] == "FORBIDDEN"


def test_material_trials_uncharged() -> None:
    doc = load_machine_freeze(REPO)
    plan = doc["material_trial_debit"]
    assert plan["plan_id"] == PLAN_ID
    assert plan["current_charged"] == 0
    assert plan["remaining"] == 3
    assert plan["next_debit"] == 1
    assert plan["debit_trigger"] == "L5_AUTHORIZATION_RECEIPT"
    assert plan["free_threshold_grid"] == "FORBIDDEN"
    assert plan["uncharged_adaptive_search"] == "FORBIDDEN"

    receipt = load_receipt(REPO)
    assert receipt["material_trials_charged_this_slice"] == 0
    assert receipt["firewall"]["material_trials_remaining"] == 3


def test_label_identity_and_hash_frozen_bytes_unjoined() -> None:
    doc = load_machine_freeze(REPO)
    lp = doc["label_pack"]
    assert lp["LABEL_IDENTITY_FROZEN"] is True
    assert lp["LABEL_HASH_PROCEDURE_FROZEN"] is True
    assert lp["LABEL_BYTES_JOINED"] is False
    assert lp["label_join"] is False
    assert lp["outcome_open"] is False
    assert lp["seal_status"] == "IDENTITY_AND_HASH_FROZEN_UNJOINED"
    assert lp["join_authorized"] is False
    assert lp["join_performed"] is False
    assert lp["outcome_inspected"] is False

    identity = load_label_identity(REPO)
    assert identity["LABEL_IDENTITY_FROZEN"] is True
    assert identity["LABEL_BYTES_JOINED"] is False
    assert identity["join_performed"] is False
    assert identity["security_identity"] if False else identity["row_key_set_definition"][
        "security_identity"
    ] == "CIQSEC"
    assert (
        identity["row_key_set_definition"]["ticker_entity_permno_fallback"] == "FORBIDDEN"
    )

    proc = load_label_hash_procedure(REPO)
    assert proc["LABEL_HASH_PROCEDURE_FROZEN"] is True
    assert proc["LABEL_BYTES_JOINED"] is False
    assert proc["join_authorized"] is False
    assert proc["seal_name"] == "SEALED_UNJOINED"

    # No joined outcomes/parquet under label custody dir.
    custody_dir = REPO / "data/prebreakout/compiled/ao_ftk_1_20260812_label_custody"
    for p in custody_dir.iterdir():
        assert p.suffix.lower() != ".parquet", p
        assert "joined" not in p.name.lower() or p.suffix == ".json"


def test_blocked_unset_economic_cuts_retained() -> None:
    doc = load_machine_freeze(REPO)
    assert doc["payoff_horizon"] == "BLOCKED_UNSET"
    assert doc["right_tail_cut"] == "BLOCKED_UNSET"
    assert doc["catastrophe_cut"] == "BLOCKED_UNSET"
    econ = doc["economic_cuts"]
    assert econ["payoff_horizon_primary"] == "BLOCKED_UNSET"
    assert econ["payoff_horizon_secondary"] == "BLOCKED_UNSET"
    assert econ["right_tail_definition"] == "BLOCKED_UNSET"
    assert econ["catastrophe_definition"] == "BLOCKED_UNSET"


def test_qm_terms_absent() -> None:
    doc = load_machine_freeze(REPO)
    assert_no_qm_terms_in_l4_surface(doc)
    assert doc["qm_terms_forbidden"] is True
    assert doc["q_source_status"] == "Q_SOURCE_BLOCKED_TERMINAL"
    assert doc["ok_sbi_s2"] == "NOT_AUTHORIZED"
    assert doc["qm_revival_in_ftk"] == "FORBIDDEN"


def test_l5_not_authorized_and_not_runnable() -> None:
    doc = load_machine_freeze(REPO)
    assert doc["l5_authorized"] is False
    assert doc["l5_auto_open"] is False
    assert doc["runnable_evaluation"] is False
    assert doc["capital_authority"] is False
    assert doc["financial_alpha_evidence"] == 0


def test_fail_closed_label_join_when_l5_false() -> None:
    with pytest.raises(L4FailClosedError, match="label_join"):
        label_join(l5_authorized=False)
    with pytest.raises(L4FailClosedError, match="label_join"):
        label_join()  # default false


def test_fail_closed_trial_debit_when_l5_false() -> None:
    with pytest.raises(L4FailClosedError, match="trial_debit"):
        trial_debit(l5_authorized=False)
    with pytest.raises(L4FailClosedError, match="trial_debit"):
        trial_debit()


def test_fail_closed_evaluator_run_when_l5_false() -> None:
    ev = Evaluator()
    with pytest.raises(L4FailClosedError, match="evaluator.run"):
        ev.run(l5_authorized=False)
    with pytest.raises(L4FailClosedError, match="evaluator.run"):
        ev.run()
    # Even if someone flips runnable without L5, still fail on L5 first.
    with pytest.raises(L4FailClosedError, match="evaluator.run"):
        ev.run(l5_authorized=False, runnable_evaluation=True)


def test_fail_closed_still_blocks_partial_l5_flags() -> None:
    """Worker-ready flags alone must never open L5 paths."""
    with pytest.raises(L4FailClosedError):
        label_join(l5_authorized=False, join_authorized=True)
    with pytest.raises(L4FailClosedError):
        trial_debit(l5_authorized=False, debit_units=1)
    # If L5 flag true but implementation not opened this phase, still refuse.
    with pytest.raises(L4FailClosedError, match="not_implemented_in_l4"):
        label_join(l5_authorized=True, join_authorized=True)
    with pytest.raises(L4FailClosedError, match="not_implemented_in_l4"):
        trial_debit(l5_authorized=True, debit_units=1)
    with pytest.raises(L4FailClosedError, match="not_implemented_in_l4"):
        Evaluator().run(l5_authorized=True, runnable_evaluation=True)


def test_receipt_matches_freeze_firewall() -> None:
    receipt = load_receipt(REPO)
    assert receipt["slice_id"] == SLICE_ID
    assert receipt["terminal_verdict"] == "L4_FREEZE_PASS"
    assert receipt["l5_authorized"] is False
    assert receipt["material_trials_charged_this_slice"] == 0
    assert receipt["label_bytes_joined"] is False
    assert receipt["financial_alpha_evidence"] == 0
    assert receipt["next_phase"] == "WAIT_OWNER_L5"
    assert "authorize L5" in receipt["next_owner_action"]
    assert receipt["stop_lines_hit"] == []
    assert receipt["effective_decision_dof_frozen"] == 2

    freeze = load_machine_freeze(REPO)
    assert freeze["l5_authorized"] is False
    assert freeze["financial_alpha_evidence"] == 0
    assert freeze["material_trial_debit"]["current_charged"] == 0


def test_l3_pass_still_binding_no_dof_rewrite() -> None:
    l3_path = REPO / (
        "docs/context/e2e_evidence/ao_ftk_1_20260812_l3_representation_snr_disposition.json"
    )
    l3 = json.loads(l3_path.read_text(encoding="utf-8"))
    assert l3["disposition"] == "PASS"
    assert l3["effective_dof_recommendation"] == 2
    freeze = load_machine_freeze(REPO)
    assert freeze["effective_decision_dof"] == l3["effective_dof_recommendation"]
    assert freeze["l3_disposition"] == "PASS"
