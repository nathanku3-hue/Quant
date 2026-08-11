"""AO-FTK-0 Fundamental Transition Kernel pre-open contract helpers.

Research-only freeze support. No outcome join, no capital, no Q/M revival.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SLICE_ID = "AO-FTK-0"
KERNEL_ID = "AO_FTK_0_TRANSITION_SPARSE_BASIS_V1"
CONTRACT_ID = "FundamentalTransitionKernelContractV1"
MACHINE_FREEZE_REL = Path("docs/architecture/ao_ftk_0_transition_sparse_basis_v1.json")
MD_FREEZE_REL = Path("docs/architecture/ao_ftk_0_transition_sparse_basis_v1.md")
QM_PARK_REL = Path("docs/context/e2e_evidence/qm_track_parked_terminal_20260812.json")
PREOPEN_EVIDENCE_REL = Path("docs/context/e2e_evidence/ao_ftk_0_preopen_freeze_20260812.json")

CONSTITUTION = (
    "Q/M is terminal under current admitted custody. AO-FTK-0 freezes a sparse "
    "inventory/margin transition basis only. Full W3 and abstention remain law. "
    "No outcomes, no capital, no Q/M composites, no invented fundamentals. "
    "Success is a preregistered pre-open contract — not alpha, not a leaderboard, "
    "not gate-filling theater."
)

FORBIDDEN_QM_API_TOKENS = (
    "Q",
    "M",
    "M_perp",
    "M⊥",
    "Q+M",
    "Q×M",
    "Q*M",
    "residual-M",
    "residual_M",
    "ROIC",
    "Q_GF",
    "Rule100",
)

ALLOWED_API_SURFACE = frozenset(
    {
        "kernel_id",
        "node_id",
        "operator_id",
        "applicability_status",
        "abstention",
        "prediction_direction",
        "primitive_id",
        "missingness_reason",
    }
)

REQUIRED_OPERATOR_IDS = (
    "INV_DELTA_MEAN_REVERSION",
    "MARGIN_M1_STATE_MEAN_REVERSION",
)

REQUIRED_PRIMITIVE_IDS = (
    "FTK_PRIM_IQ_PERIOD_END",
    "FTK_PRIM_IQ_TOTAL_REV",
    "FTK_PRIM_IQ_INVENTORY",
    "FTK_PRIM_IQ_OPER_INC",
)

APPLICABILITY_STATUSES = (
    "W3_INELIGIBLE",
    "NOT_APPLICABLE",
    "APPLICABLE_OBSERVED",
    "APPLICABLE_UNOBSERVED",
)


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_machine_freeze(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or default_repo_root()
    path = root / MACHINE_FREEZE_REL
    return json.loads(path.read_text(encoding="utf-8"))


def load_qm_park_receipt(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or default_repo_root()
    path = root / QM_PARK_REL
    return json.loads(path.read_text(encoding="utf-8"))


def decision_operators(freeze: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        op
        for op in freeze.get("operators", [])
        if op.get("status") == "FROZEN_DECISION_SURFACE"
    ]


def bound_primitives(freeze: dict[str, Any]) -> list[dict[str, Any]]:
    return [p for p in freeze.get("primitives", []) if p.get("bind_status") == "BOUND"]


def validate_machine_freeze(freeze: dict[str, Any]) -> list[str]:
    """Return a list of validation errors (empty means PASS)."""
    errors: list[str] = []

    if freeze.get("slice_id") != SLICE_ID:
        errors.append(f"slice_id_mismatch:{freeze.get('slice_id')}")
    if freeze.get("kernel_id") != KERNEL_ID:
        errors.append(f"kernel_id_mismatch:{freeze.get('kernel_id')}")
    if freeze.get("contract_id") != CONTRACT_ID:
        errors.append(f"contract_id_mismatch:{freeze.get('contract_id')}")
    if freeze.get("financial_alpha_evidence") != 0:
        errors.append("financial_alpha_evidence_nonzero")
    if freeze.get("outcome_open_authorized") is not False:
        errors.append("outcome_open_authorized_not_false")
    if freeze.get("runnable_evaluation") is not False:
        errors.append("runnable_evaluation_not_false")
    if freeze.get("qm_terms_forbidden") is not True:
        errors.append("qm_terms_forbidden_not_true")
    if freeze.get("qm_revival_in_ftk") != "FORBIDDEN":
        errors.append("qm_revival_not_forbidden")
    if freeze.get("q_amendment_cycles_used") != 0:
        errors.append("q_amendment_cycles_used_nonzero")
    if freeze.get("ok_sbi_s2") != "NOT_AUTHORIZED":
        errors.append("ok_sbi_s2_not_parked")
    if freeze.get("ok_sbi_gates_filled") is not False:
        errors.append("ok_sbi_gates_filled_true")
    if freeze.get("capital_authority") != "NONE":
        errors.append("capital_authority_not_none")

    complexity = freeze.get("complexity_ledger") or {}
    dof = complexity.get("effective_decision_dof_frozen")
    max_dof = complexity.get("max_effective_decision_dof")
    if not isinstance(dof, int) or dof < 1 or dof > 2:
        errors.append(f"effective_decision_dof_out_of_range:{dof}")
    if max_dof != 2:
        errors.append(f"max_effective_decision_dof_not_2:{max_dof}")

    ops = decision_operators(freeze)
    op_ids = [op.get("operator_id") for op in ops]
    if sorted(op_ids) != sorted(REQUIRED_OPERATOR_IDS):
        errors.append(f"decision_operator_set_mismatch:{op_ids}")
    if len(ops) != dof:
        errors.append(f"operator_count_dof_mismatch:{len(ops)}!={dof}")

    prim_ids = [p.get("primitive_id") for p in bound_primitives(freeze)]
    for required in REQUIRED_PRIMITIVE_IDS:
        if required not in prim_ids:
            errors.append(f"missing_bound_primitive:{required}")

    statuses = (freeze.get("applicability_taxonomy") or {}).get("statuses") or []
    for status in APPLICABILITY_STATUSES:
        if status not in statuses:
            errors.append(f"missing_applicability_status:{status}")

    budget = freeze.get("search_budget") or {}
    if budget.get("material_trials_charged_this_slice") != 0:
        errors.append("search_budget_charged_this_slice_nonzero")
    if not isinstance(budget.get("material_trials_remaining"), int):
        errors.append("search_budget_remaining_not_int")
    if budget.get("rescue_redesign_without_new_slice_id") != "FORBIDDEN":
        errors.append("rescue_redesign_not_forbidden")

    labels = freeze.get("label_custody_plan") or {}
    if labels.get("join_authorized") is not False:
        errors.append("label_join_authorized")
    if labels.get("join_performed") is not False:
        errors.append("label_join_performed")
    if labels.get("outcome_inspected") is not False:
        errors.append("label_outcome_inspected")

    denom = freeze.get("denominator_and_abstention") or {}
    if denom.get("denominator") != "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1":
        errors.append("denominator_not_full_w3")
    if denom.get("complete_case_denominator") != "FORBIDDEN":
        errors.append("complete_case_not_forbidden")
    if denom.get("coverage_pass_fail_gate") != "FORBIDDEN":
        errors.append("coverage_pass_fail_not_forbidden")

    if freeze.get("terminal_preopen_verdict") != "READY_FOR_LATER_CHARGED_DEVELOPMENT_READ":
        errors.append(f"unexpected_verdict:{freeze.get('terminal_preopen_verdict')}")

    return errors


def assert_valid_machine_freeze(freeze: dict[str, Any]) -> None:
    errors = validate_machine_freeze(freeze)
    if errors:
        raise ValueError(f"ao_ftk_0_freeze_invalid:{','.join(errors)}")


def ftk_api_surface_tokens(freeze: dict[str, Any] | None = None) -> set[str]:
    """Tokens that constitute the FTK public decision/API surface.

    Intentionally excludes descriptive/prohibition text so forbidden Q/M terms
    may appear in quarantine lists without becoming API members.
    """
    freeze = freeze or {}
    tokens = set(ALLOWED_API_SURFACE)
    tokens.add(str(freeze.get("kernel_id") or KERNEL_ID))
    for op in decision_operators(freeze):
        if op.get("operator_id"):
            tokens.add(str(op["operator_id"]))
        if op.get("node_id"):
            tokens.add(str(op["node_id"]))
    for prim in bound_primitives(freeze):
        if prim.get("primitive_id"):
            tokens.add(str(prim["primitive_id"]))
    return tokens


def assert_no_qm_terms_in_ftk_api(freeze: dict[str, Any] | None = None) -> None:
    surface = ftk_api_surface_tokens(freeze)
    offenders = sorted(t for t in surface if t in FORBIDDEN_QM_API_TOKENS)
    if offenders:
        raise ValueError(f"ao_ftk_0_qm_terms_in_api:{','.join(offenders)}")


def refuse_outcome_open(*, outcome_open_authorized: bool = False) -> None:
    if outcome_open_authorized:
        # Even an explicit true is illegal for this slice contract.
        raise ValueError("ao_ftk_0_outcome_open_forbidden")
    raise ValueError("ao_ftk_0_outcome_open_forbidden")


def refuse_qm_revival() -> None:
    raise ValueError("ao_ftk_0_qm_revival_forbidden")


def refuse_ok_sbi_s2() -> None:
    raise ValueError("ao_ftk_0_ok_sbi_s2_not_authorized")


def refuse_q_amendment_spend() -> None:
    raise ValueError("ao_ftk_0_q_amendment_spend_forbidden")


_QM_TOKEN_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])(M_perp|M⊥|Q\+M|Q×M|Q\*M|residual[-_]M|ROIC|Q_GF|Rule100)(?![A-Za-z0-9_])"
)


def scan_text_for_forbidden_api_usage(text: str) -> list[str]:
    """Scan free text for forbidden Q/M tokens used as bare API identifiers.

    Does not flag prose that only documents the ban (caller should restrict
    scan scope to API/schema fields when needed).
    """
    return sorted({m.group(1) for m in _QM_TOKEN_PATTERN.finditer(text)})


def build_preopen_evidence(
    *,
    repo_root: Path | None = None,
    machine_freeze_sha256: str | None = None,
    md_freeze_sha256: str | None = None,
    qm_park_sha256: str | None = None,
    test_module: str = "tests/asymmetric_opportunity_v1/test_ao_ftk_0_preopen_contracts.py",
) -> dict[str, Any]:
    root = repo_root or default_repo_root()
    freeze = load_machine_freeze(root)
    park = load_qm_park_receipt(root)
    assert_valid_machine_freeze(freeze)
    assert_no_qm_terms_in_ftk_api(freeze)

    return {
        "schema_version": "ao_ftk_0_preopen_freeze_v1",
        "slice_id": SLICE_ID,
        "date": "2026-08-12",
        "terminal_preopen_verdict": freeze["terminal_preopen_verdict"],
        "outcome_open_authorized": False,
        "runnable_evaluation": False,
        "financial_alpha_evidence": 0,
        "qm_revival_attempted": False,
        "q_amendment_cycles_used": 0,
        "ok_sbi_s2": "NOT_AUTHORIZED",
        "ok_sbi_gates_filled": False,
        "capital_authority": "NONE",
        "artifacts": {
            "machine_freeze": str(MACHINE_FREEZE_REL).replace("\\", "/"),
            "md_freeze": str(MD_FREEZE_REL).replace("\\", "/"),
            "qm_park_receipt": str(QM_PARK_REL).replace("\\", "/"),
            "test_module": test_module,
            "machine_freeze_sha256": machine_freeze_sha256,
            "md_freeze_sha256": md_freeze_sha256,
            "qm_park_sha256": qm_park_sha256,
        },
        "primitive_bind_summary": [
            {
                "primitive_id": p["primitive_id"],
                "exact_field_identifier": p["exact_field_identifier"],
                "bind_status": p["bind_status"],
            }
            for p in bound_primitives(freeze)
        ],
        "operator_freeze": [
            {
                "operator_id": op["operator_id"],
                "node_id": op["node_id"],
                "decision_dof_slot": op["decision_dof_slot"],
                "status": op["status"],
            }
            for op in decision_operators(freeze)
        ],
        "complexity": freeze["complexity_ledger"],
        "search_budget": freeze["search_budget"],
        "label_custody_plan_join_authorized": freeze["label_custody_plan"]["join_authorized"],
        "qm_park_status": park.get("Q_SOURCE_STATUS"),
        "constitution": CONSTITUTION,
    }
