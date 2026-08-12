"""TR-v0 L2 observation contract loaders and fail-closed invariants."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
L2_CONTRACT_PATH = ROOT / "docs/architecture/transition_recognition_v0_l2_observation_contract.json"
L2_RECEIPT_PATH = ROOT / "docs/context/e2e_evidence/tr_v0_l2_observation_contract_1.json"
L0_L1_PATH = ROOT / "docs/architecture/transition_recognition_v0_l0_l1_freeze.json"
ADMISSION_PATH = ROOT / "docs/context/e2e_evidence/tr_v0_g0_g2_admission_1.json"

PRIMARY_RECOGNITION_MEASURES = (
    "EPS_FY1",
    "EPS_FY1_REVISION_30D",
    "EPS_FY1_REVISION_90D",
)

FORBIDDEN_TRUE_FLAGS = (
    "timing_research",
    "ftk_rescue",
    "returns_join",
    "runnable_evaluation",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_l2_contract() -> dict[str, Any]:
    return load_json(L2_CONTRACT_PATH)


def assert_l2_contract_invariants(contract: dict[str, Any] | None = None) -> None:
    c = contract if contract is not None else load_l2_contract()
    if c.get("slice_id") != "TR-v0-L2-OBSERVATION-CONTRACT-1":
        raise AssertionError("tr_v0_l2_slice_id_mismatch")
    if c.get("family_id") != "TRANSITION_RECOGNITION_v0":
        raise AssertionError("tr_v0_l2_family_mismatch")
    if c.get("debit", 1) != 0 or c.get("evals", 1) != 0 or c.get("label_join", 1) != 0:
        raise AssertionError("tr_v0_l2_nonzero_trial_surface")
    if c.get("financial_alpha_evidence", 1) != 0:
        raise AssertionError("tr_v0_l2_alpha_nonzero")
    if c.get("l5") != "FORBIDDEN":
        raise AssertionError("tr_v0_l2_l5_not_forbidden")
    if c.get("ao_ftk_2") != "FORBIDDEN":
        raise AssertionError("tr_v0_l2_ao_ftk_2_not_forbidden")
    for flag in FORBIDDEN_TRUE_FLAGS:
        if c.get(flag) is True:
            raise AssertionError(f"tr_v0_l2_forbidden_flag_true:{flag}")

    rec = c["recognition_observation_contract"]
    primary = {m["measure"] for m in rec["measures_primary_v0"]}
    if primary != set(PRIMARY_RECOGNITION_MEASURES):
        raise AssertionError("tr_v0_l2_primary_measures_mismatch")
    if rec["source_bind"]["status"] != "MISSING_SOURCE":
        raise AssertionError("tr_v0_l2_source_must_be_missing_until_admit")
    if rec["source_bind"].get("provider_capture_this_slice") != "FORBIDDEN":
        raise AssertionError("tr_v0_l2_provider_capture_not_forbidden")
    if rec["source_bind"].get("crv1_family_artifact_reuse_as_tr_authority") != "FORBIDDEN":
        raise AssertionError("tr_v0_l2_crv1_reuse_not_forbidden")

    reality = c["reality_observation_contract"]
    if reality.get("ftk_policy_reuse_as_reality") != "FORBIDDEN":
        raise AssertionError("tr_v0_l2_ftk_policy_reuse_not_forbidden")
    fields = {p["field"] for p in reality["primitive_binds"]}
    required = {"IQ_PERIOD_END", "IQ_TOTAL_REV", "IQ_INVENTORY", "IQ_OPER_INC"}
    if not required.issubset(fields):
        raise AssertionError("tr_v0_l2_reality_primitives_incomplete")

    gap = c["recognition_gap_contract"]
    op_ids = {o["operator_id"] for o in gap["operator_family_v0"]}
    if "REV_LAG_AFTER_REALITY" not in op_ids:
        raise AssertionError("tr_v0_l2_gap_operator_missing")
    for op in gap["operator_family_v0"]:
        if op.get("materiality_cut") != "BLOCKED_UNSET_UNTIL_L3_L4":
            raise AssertionError("tr_v0_l2_gap_cut_must_be_unset")

    if c["selection_vs_timing"]["out_of_scope"] != "B_TIMING_entry_confirmation_D7":
        raise AssertionError("tr_v0_l2_timing_must_be_out_of_scope")

    # Parent admission must still forbid trial surface.
    admission = load_json(ADMISSION_PATH)
    if admission.get("terminal") != "ALL_PASS_ADMIT_L1_FROZEN":
        raise AssertionError("tr_v0_l2_parent_admission_not_pass")
    if admission.get("debit", 1) != 0 or admission.get("timing_research") is not False:
        raise AssertionError("tr_v0_l2_parent_admission_trial_surface")

    l0l1 = load_json(L0_L1_PATH)
    if l0l1.get("status") != "L0_L1_FROZEN":
        raise AssertionError("tr_v0_l2_parent_l0l1_not_frozen")
