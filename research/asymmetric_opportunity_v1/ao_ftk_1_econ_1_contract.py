"""AO-FTK-1-ECON-1 economic / asymmetry estimand freeze helpers.

Outcome-blind form freeze only. No economic L5, no trial debit, no label join,
no evaluation, no alpha claim.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


FREEZE_ID = "AO-FTK-1-ECON-1"
PARENT_PROGRAM = "AO-FTK-1-20260812"
NAME = "FTK_ECONOMIC_ASYMMETRY_FREEZE"
KERNEL_ID = "AO_FTK_0_TRANSITION_SPARSE_BASIS_V1"
PARENT_L5_WORK_COMMIT = "948471c"
PARENT_L4_WORK_COMMIT = "a3350f0"
L7_ROUTE = "LATER_ECONOMIC_CUT_FREEZE_PLUS_SECOND_TRIAL"
PLAN_ID = "FTK1_ECON_TRIAL_DEBIT_PLAN_V1"
EFFECTIVE_DECISION_DOF = 2
SCHEMA_VERSION = "ao_ftk_1_econ_1_economic_asymmetry_freeze_v1"

MACHINE_FREEZE_REL = Path(
    "docs/architecture/ao_ftk_1_econ_1_economic_asymmetry_freeze.json"
)
MD_FREEZE_REL = Path("docs/architecture/ao_ftk_1_econ_1_economic_asymmetry_freeze.md")
RECEIPT_REL = Path(
    "docs/context/e2e_evidence/ao_ftk_1_econ_1_economic_asymmetry_freeze.json"
)
L7_SELECT_REL = Path(
    "docs/context/e2e_evidence/ao_ftk_1_econ_1_l7_route_select.json"
)
PARENT_L4_FREEZE_REL = Path(
    "docs/architecture/ao_ftk_1_20260812_l4_charged_slice_freeze.json"
)
PARENT_L5_RUN_REL = Path("docs/context/e2e_evidence/ao_ftk_1_20260812_l5_run.json")
PARENT_L7_PACKET_REL = Path(
    "docs/context/e2e_evidence/ao_ftk_1_20260812_l7_owner_packet.json"
)

LABEL_CUSTODY_DIR_REL = Path(
    "data/prebreakout/compiled/ao_ftk_1_econ_1_label_custody"
)
LABEL_IDENTITY_REL = LABEL_CUSTODY_DIR_REL / "economic_label_pack.identity.json"
LABEL_HASH_PROCEDURE_REL = (
    LABEL_CUSTODY_DIR_REL / "economic_label_pack.hash_procedure.json"
)
SENSING_LABEL_CUSTODY_DIR_REL = Path(
    "data/prebreakout/compiled/ao_ftk_1_20260812_label_custody"
)

REQUIRED_OPERATOR_IDS = (
    "INV_DELTA_MEAN_REVERSION",
    "MARGIN_M1_STATE_MEAN_REVERSION",
)

REQUIRED_E_KEYS = tuple(f"E{i}" for i in range(1, 13))
FORBIDDEN_E_AUTHORITY_KEYS = ("E13", "E14")

VALUE_OWNERS = frozenset(
    {
        "FROZEN",
        "OWNER_BLOCKED_UNSET",
        "BLOCKED_UNSET",
        "INHERITED_AUTHORITY",
    }
)

CONSTITUTION = (
    "Freeze the economic estimand outcome-blind on the unchanged 2-DOF sensing law. "
    "Debit nothing. Join nothing. Run nothing. Stop at WAIT_OWNER_L5_ECONOMIC."
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

STOP_LINES = (
    "TRIAL2_DEBIT_THIS_TURN",
    "ECONOMIC_LABEL_JOIN_THIS_TURN",
    "AUTO_L5_AFTER_FREEZE",
    "H_OR_PERCENTILE_GRID_SEARCH",
    "POST_PEEK_CUT_BINDING",
    "DOF_COLLAPSE_OR_THIRD_DOF",
    "OPERATOR_OR_REPRESENTATION_REWRITE",
    "DROP_INVENTORY_PRE_RESULT",
    "FEATURE_ADD",
    "OPEN_AO_FTK_2",
    "INVENT_D7_CONFIRMATION_RULE",
    "INVENT_E13_E14_AS_AUTHORITY",
    "INVENT_PRICE_LAG_COST_LAW",
    "REUSE_SENSING_LABELS_FOR_ECONOMIC_ESTIMAND",
    "Q_INVENT_OR_S2",
    "REOPEN_AO_FTK_0",
    "W6_OPEN",
    "CAPITAL_OR_ALPHA_CLAIM",
    "L8_REFINEMENT_THIS_TURN",
    "CAGR_OR_MU_SNDK_AS_PRIMARY_SUCCESS",
)


class Econ1FailClosedError(PermissionError):
    """Raised when economic L5-gated operations are attempted without authorization."""


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object JSON at {path}")
    return data


def load_machine_freeze(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    return load_json(root / MACHINE_FREEZE_REL)


def load_receipt(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    return load_json(root / RECEIPT_REL)


def load_parent_l4_freeze(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    return load_json(root / PARENT_L4_FREEZE_REL)


def load_label_identity(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    return load_json(root / LABEL_IDENTITY_REL)


def load_label_hash_procedure(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    return load_json(root / LABEL_HASH_PROCEDURE_REL)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def pin_operator_identity(operator: dict[str, Any]) -> str:
    """Content-address operator id + formula + immutability statements."""
    payload = {
        "operator_id": operator.get("operator_id"),
        "node_id": operator.get("node_id"),
        "decision_dof_slot": operator.get("decision_dof_slot"),
        "formula": operator.get("formula"),
        "status": operator.get("status"),
        "operator_bytes": operator.get("operator_bytes"),
        "m1_bytes_mutation": operator.get("m1_bytes_mutation"),
        "fit_or_tuning": operator.get("fit_or_tuning"),
        "threshold_grid": operator.get("threshold_grid"),
    }
    canonical = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return sha256_text(canonical)


def _require_economic_l5_authorized(*, economic_l5_authorized: bool, action: str) -> None:
    if economic_l5_authorized is not True:
        raise Econ1FailClosedError(
            f"ao_ftk_1_econ_1_fail_closed:{action}:economic_l5_authorized=false"
        )


def economic_label_join(
    *,
    economic_l5_authorized: bool = False,
    join_authorized: bool = False,
    **_: Any,
) -> None:
    """Fail closed unless separate economic L5 authorization is present."""
    _require_economic_l5_authorized(
        economic_l5_authorized=economic_l5_authorized, action="economic_label_join"
    )
    if join_authorized is not True:
        raise Econ1FailClosedError(
            "ao_ftk_1_econ_1_fail_closed:economic_label_join:join_authorized=false"
        )
    raise Econ1FailClosedError(
        "ao_ftk_1_econ_1_fail_closed:economic_label_join:join_not_implemented_in_freeze"
    )


def trial_debit(
    *,
    economic_l5_authorized: bool = False,
    debit_units: int = 1,
    **_: Any,
) -> None:
    """Fail closed unless separate economic L5 authorization is present."""
    _require_economic_l5_authorized(
        economic_l5_authorized=economic_l5_authorized, action="trial_debit"
    )
    if debit_units != 1:
        raise Econ1FailClosedError(
            f"ao_ftk_1_econ_1_fail_closed:trial_debit:debit_units_must_be_1_got_{debit_units}"
        )
    raise Econ1FailClosedError(
        "ao_ftk_1_econ_1_fail_closed:trial_debit:debit_not_implemented_in_freeze"
    )


def economic_evaluator_run(
    *,
    economic_l5_authorized: bool = False,
    runnable_evaluation: bool = False,
    **_: Any,
) -> None:
    """Fail closed unless separate economic L5 authorization + runnable flag."""
    _require_economic_l5_authorized(
        economic_l5_authorized=economic_l5_authorized, action="economic_evaluator.run"
    )
    if runnable_evaluation is not True:
        raise Econ1FailClosedError(
            "ao_ftk_1_econ_1_fail_closed:economic_evaluator.run:runnable_evaluation=false"
        )
    raise Econ1FailClosedError(
        "ao_ftk_1_econ_1_fail_closed:economic_evaluator.run:run_not_implemented_in_freeze"
    )


# Prompt-facing aliases
label_join = economic_label_join
evaluator_run = economic_evaluator_run


class EconomicEvaluator:
    """Minimal evaluator surface that refuses unless economic L5-authorized."""

    def run(
        self,
        *,
        economic_l5_authorized: bool = False,
        runnable_evaluation: bool = False,
        **kwargs: Any,
    ) -> None:
        economic_evaluator_run(
            economic_l5_authorized=economic_l5_authorized,
            runnable_evaluation=runnable_evaluation,
            **kwargs,
        )


def _e_block_errors(e_key: str, block: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(block, dict):
        return [f"{e_key} must be object"]
    if "form" not in block:
        errors.append(f"{e_key}.form required")
    owner = block.get("value_owner")
    if owner not in VALUE_OWNERS:
        errors.append(
            f"{e_key}.value_owner must be one of {sorted(VALUE_OWNERS)}; got {owner!r}"
        )
    if "value" not in block:
        errors.append(f"{e_key}.value required")
    return errors


def validate_econ_freeze(doc: dict[str, Any]) -> list[str]:
    """Return schema / firewall errors (empty = valid economic freeze)."""
    errors: list[str] = []

    if doc.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if doc.get("freeze_id") != FREEZE_ID:
        errors.append(f"freeze_id must be {FREEZE_ID}")
    if doc.get("parent_program") != PARENT_PROGRAM:
        errors.append(f"parent_program must be {PARENT_PROGRAM}")
    if doc.get("name") != NAME:
        errors.append(f"name must be {NAME}")
    if doc.get("status") not in (
        "ECON_FREEZE_PASS_WAITING_OWNER_L5",
        "ECON_FREEZE_PASS_WAITING_OWNER_NUMERICS",
        "ECON_FREEZE_BLOCKED_MISSING_AUTHORITY",
        "HOLD_RECOMMENDED",
    ):
        errors.append("status must be a recognized economic freeze terminal")

    if doc.get("authorized_phase") != "ECONOMIC_ESTIMAND_FREEZE":
        errors.append("authorized_phase must be ECONOMIC_ESTIMAND_FREEZE")
    if doc.get("l7_route") != L7_ROUTE:
        errors.append(f"l7_route must be {L7_ROUTE}")
    if doc.get("second_l5") != "NOT_AUTHORIZED":
        errors.append("second_l5 must be NOT_AUTHORIZED")
    if doc.get("l5_authorized") is not False:
        errors.append("l5_authorized must be false")
    if doc.get("l5_auto_open") is not False:
        errors.append("l5_auto_open must be false")
    if doc.get("economic_l5_authorized") is not False:
        errors.append("economic_l5_authorized must be false")
    if doc.get("runnable_evaluation") is not False:
        errors.append("runnable_evaluation must be false")
    if doc.get("capital_authority") is not False:
        errors.append("capital_authority must be false")
    if doc.get("financial_alpha_evidence") != 0:
        errors.append("financial_alpha_evidence must be 0")
    if doc.get("label_bytes_joined") is not False:
        errors.append("label_bytes_joined must be false")
    if doc.get("material_trials_charged_this_turn") != 0:
        errors.append("material_trials_charged_this_turn must be 0")

    surface = doc.get("surface_inheritance")
    if not isinstance(surface, dict):
        errors.append("surface_inheritance must be object")
    else:
        if surface.get("effective_decision_dof") != EFFECTIVE_DECISION_DOF:
            errors.append("surface_inheritance.effective_decision_dof must be 2")
        if surface.get("kernel_id") != KERNEL_ID:
            errors.append(f"surface_inheritance.kernel_id must be {KERNEL_ID}")
        if surface.get("routing") != "DOMAIN_LIMITED_EX_ANTE":
            errors.append("surface_inheritance.routing must be DOMAIN_LIMITED_EX_ANTE")
        if surface.get("silent_one_dof_collapse") != "FORBIDDEN":
            errors.append("silent_one_dof_collapse must be FORBIDDEN")
        if surface.get("third_decision_dof") != "FORBIDDEN":
            errors.append("third_decision_dof must be FORBIDDEN")
        ops = surface.get("operators")
        if not isinstance(ops, list) or len(ops) != 2:
            errors.append("surface_inheritance.operators must be list of length 2")
        else:
            ids = {op.get("operator_id") for op in ops if isinstance(op, dict)}
            if ids != set(REQUIRED_OPERATOR_IDS):
                errors.append(f"operators ids must be {REQUIRED_OPERATOR_IDS}")
            for op in ops:
                if not isinstance(op, dict):
                    errors.append("operator entry must be object")
                    continue
                if op.get("operator_bytes") != "FROZEN":
                    errors.append(f"{op.get('operator_id')}: operator_bytes must be FROZEN")
                if not op.get("immutability_pin"):
                    errors.append(f"{op.get('operator_id')}: immutability_pin required")
                if op.get("operator_id") == "MARGIN_M1_STATE_MEAN_REVERSION":
                    if op.get("m1_bytes_mutation") != "FORBIDDEN":
                        errors.append("MARGIN_M1: m1_bytes_mutation must be FORBIDDEN")

    estimand = doc.get("estimand")
    if not isinstance(estimand, dict):
        errors.append("estimand must be object")
    else:
        for e_key in REQUIRED_E_KEYS:
            if e_key not in estimand:
                errors.append(f"estimand.{e_key} required")
            else:
                errors.extend(_e_block_errors(e_key, estimand[e_key]))
        for bad in FORBIDDEN_E_AUTHORITY_KEYS:
            if bad in estimand:
                errors.append(f"estimand must not define authority key {bad}")

    # E11 label pack distinct from sensing (fields may live on E11 or E11.value)
    e11 = (estimand or {}).get("E11") if isinstance(estimand, dict) else None
    if isinstance(e11, dict):
        e11_value = e11.get("value") if isinstance(e11.get("value"), dict) else e11
        identity_path = str(
            e11_value.get("identity_path")
            or e11.get("identity_path")
            or ""
        )
        if "ao_ftk_1_20260812_label_custody" in identity_path:
            errors.append("E11 must not reuse sensing label custody path")
        if "ao_ftk_1_econ_1_label_custody" not in identity_path:
            errors.append("E11 identity_path must point at econ_1 custody")
        bytes_joined = e11_value.get("bytes_joined", e11.get("bytes_joined"))
        join_authorized = e11_value.get("join_authorized", e11.get("join_authorized"))
        if bytes_joined is not False:
            errors.append("E11.bytes_joined must be false")
        if join_authorized is not False:
            errors.append("E11.join_authorized must be false")

    dmap = doc.get("d6_d9_mapping")
    if not isinstance(dmap, dict):
        errors.append("d6_d9_mapping must be object")
    else:
        for layer in (
            "D6_SELECTION_ENRICHMENT",
            "D7_CONFIRMATION_TIMING",
            "D8_HOLD_EXIT_CONVEXITY",
            "D9_ECONOMICS_COST_CAPACITY",
        ):
            if layer not in dmap:
                errors.append(f"d6_d9_mapping.{layer} required")
        d7 = dmap.get("D7_CONFIRMATION_TIMING")
        if isinstance(d7, dict):
            if d7.get("rule_status") not in ("INHERITED_AUTHORITY", "BLOCKED_UNSET"):
                errors.append("D7.rule_status must be INHERITED_AUTHORITY or BLOCKED_UNSET")
            if d7.get("invented_this_freeze") is True:
                errors.append("D7 must not be invented this freeze")

    plan = doc.get("material_trial_debit_plan")
    if not isinstance(plan, dict):
        errors.append("material_trial_debit_plan must be object")
    else:
        if plan.get("plan_id") != PLAN_ID:
            errors.append(f"material_trial_debit_plan.plan_id must be {PLAN_ID}")
        if plan.get("material_trials_total_remaining_before_trial2") != 2:
            errors.append("material_trials_total_remaining_before_trial2 must be 2")
        if plan.get("next_debit") != 1:
            errors.append("next_debit must be 1")
        if plan.get("remaining_after_trial2") != 1:
            errors.append("remaining_after_trial2 must be 1")
        if plan.get("debit_this_turn") is not False and plan.get("debit_this_turn") != "FORBIDDEN":
            errors.append("debit_this_turn must be false/FORBIDDEN")
        if plan.get("debit_trigger") != "ECONOMIC_L5_AUTHORIZATION_RECEIPT":
            errors.append("debit_trigger must be ECONOMIC_L5_AUTHORIZATION_RECEIPT")

    if doc.get("next_phase") != "WAIT_OWNER_L5_ECONOMIC":
        errors.append("next_phase must be WAIT_OWNER_L5_ECONOMIC")

    blockers = doc.get("l5_blockers")
    if not isinstance(blockers, list) or not blockers:
        errors.append("l5_blockers must be a non-empty list (explicit readiness gaps)")

    if not isinstance(doc.get("stop_lines"), list) or not doc.get("stop_lines"):
        errors.append("stop_lines must be a non-empty list")
    if doc.get("stop_lines_hit") not in ([], None):
        # allow empty list only for PASS terminals
        if doc.get("stop_lines_hit") is None:
            errors.append("stop_lines_hit required")

    if doc.get("qm_terms_forbidden") is not True:
        errors.append("qm_terms_forbidden must be true")
    if doc.get("ao_ftk_2") != "NOT_AUTHORIZED":
        errors.append("ao_ftk_2 must be NOT_AUTHORIZED")
    if doc.get("l8_bounded_refinement") != "DEFER":
        errors.append("l8_bounded_refinement must be DEFER")

    return errors


def assert_valid_econ_freeze(doc: dict[str, Any]) -> None:
    errors = validate_econ_freeze(doc)
    if errors:
        raise AssertionError("ECON freeze invalid:\n- " + "\n- ".join(errors))


def assert_no_qm_terms_in_econ_surface(doc: dict[str, Any]) -> None:
    if doc.get("qm_terms_forbidden") is not True:
        raise AssertionError("qm_terms_forbidden must be true")
    surface = json.dumps(
        {
            "kernel_id": (doc.get("surface_inheritance") or {}).get("kernel_id"),
            "operators": (doc.get("surface_inheritance") or {}).get("operators"),
            "representation": (doc.get("surface_inheritance") or {}).get("representation"),
            "estimand_e7": ((doc.get("estimand") or {}).get("E7")),
        },
        ensure_ascii=False,
    )
    for token in FORBIDDEN_QM_API_TOKENS:
        if token in {"Q", "M"}:
            if re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", surface):
                raise AssertionError(f"Forbidden QM token {token!r} in ECON API surface")
        else:
            if token in surface:
                raise AssertionError(f"Forbidden QM token {token!r} in ECON API surface")


def assert_surface_pins_match_parent(
    doc: dict[str, Any], parent: dict[str, Any]
) -> None:
    """Assert econ freeze surface inherits parent L4 dof + operator pins."""
    if doc.get("surface_inheritance", {}).get("effective_decision_dof") != parent.get(
        "effective_decision_dof"
    ):
        raise AssertionError("effective_decision_dof mismatch vs parent L4")
    parent_ops = {
        op["operator_id"]: op["immutability_pin"]
        for op in parent.get("operators", [])
        if isinstance(op, dict)
    }
    child_ops = {
        op["operator_id"]: op["immutability_pin"]
        for op in (doc.get("surface_inheritance") or {}).get("operators", [])
        if isinstance(op, dict)
    }
    if parent_ops != child_ops:
        raise AssertionError(
            f"operator immutability pins mismatch: parent={parent_ops} child={child_ops}"
        )
    for op in (doc.get("surface_inheritance") or {}).get("operators", []):
        recomputed = pin_operator_identity(op)
        if recomputed != op.get("immutability_pin"):
            raise AssertionError(
                f"operator pin recompute failed for {op.get('operator_id')}"
            )
