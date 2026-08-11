"""AO-FTK-1-ECON-1 economic / asymmetry estimand freeze helpers.

Outcome-blind form freeze + transition-position owner bind + Trial 2 receipts.
Fail-closed without economic L5 authorization. No AO-FTK-2 / capital / alpha.
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
BIND_NAME = "FTK_ECON1_TRANSITION_POSITION_BIND"
KERNEL_ID = "AO_FTK_0_TRANSITION_SPARSE_BASIS_V1"
PARENT_L5_WORK_COMMIT = "948471c"
PARENT_L4_WORK_COMMIT = "a3350f0"
PRIOR_FREEZE_COMMIT = "febd8e4"
L7_ROUTE = "LATER_ECONOMIC_CUT_FREEZE_PLUS_SECOND_TRIAL"
PLAN_ID = "FTK1_ECON_TRIAL_DEBIT_PLAN_V1"
EFFECTIVE_DECISION_DOF = 2
SCHEMA_VERSION = "ao_ftk_1_econ_1_economic_asymmetry_freeze_v1"
ECONOMIC_CLOCK_CLASS = "TRANSITION_POSITION"
AUTHORIZED_PHASES = frozenset(
    {
        "ECONOMIC_ESTIMAND_FREEZE",
        "OWNER_BIND_TRANSITION_POSITION",
        "OWNER_BIND_TRANSITION_POSITION_PLUS_ECON_FREEZE_FINALIZE",
        "L5_COMPLETE_WAITING_OWNER_L7",
    }
)
RECOGNIZED_STATUSES = frozenset(
    {
        "ECON_FREEZE_PASS_WAITING_OWNER_L5",
        "ECON_FREEZE_PASS_WAITING_OWNER_NUMERICS",
        "ECON_FREEZE_BLOCKED_MISSING_AUTHORITY",
        "HOLD_RECOMMENDED",
        "ECON_FREEZE_PASS_L5_READY",
        "ECON_BIND_WAITING_OWNER_NUMERICS",
        "ECON_L5_COMPLETE_WAITING_OWNER_L7",
        "L5_COMPLETE_WAITING_OWNER_L7",
    }
)
RECOGNIZED_NEXT_PHASES = frozenset(
    {
        "WAIT_OWNER_L5_ECONOMIC",
        "WAITING_OWNER_NUMERICS",
        "HOLD_EVIDENCE",
        "BLOCKED_MISSING_AUTHORITY",
        "L7_ROADMAP_DECISION",
    }
)
POST_TRIAL2_STATUSES = frozenset(
    {
        "ECON_L5_COMPLETE_WAITING_OWNER_L7",
        "L5_COMPLETE_WAITING_OWNER_L7",
    }
)
BIND_VERDICTS = frozenset(
    {
        "PASS_L5_READY",
        "WAITING_NUMERICS",
        "HOLD",
        "BLOCKED",
    }
)

MACHINE_FREEZE_REL = Path(
    "docs/architecture/ao_ftk_1_econ_1_economic_asymmetry_freeze.json"
)
MD_FREEZE_REL = Path("docs/architecture/ao_ftk_1_econ_1_economic_asymmetry_freeze.md")
RECEIPT_REL = Path(
    "docs/context/e2e_evidence/ao_ftk_1_econ_1_economic_asymmetry_freeze.json"
)
OWNER_BIND_RECEIPT_REL = Path(
    "docs/context/e2e_evidence/ao_ftk_1_econ_1_owner_bind_transition_position.json"
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
        "OWNER_BOUND",
        "EXPLICITLY_OUT_OF_SCOPE",
        "OWNER_OR_CRO_BLOCKED_UNSET",
    }
)

D7_RULE_STATUSES = frozenset(
    {
        "INHERITED_AUTHORITY",
        "BLOCKED_UNSET",
        "EXPLICITLY_OUT_OF_SCOPE_THIS_TRIAL",
    }
)

CONSTITUTION = (
    "Stamp FTK as TRANSITION_POSITION. Bind one horizon and the economic laws "
    "without invention or peeking. One economic trial after L5 auth. L6 first-fail. "
    "L7 stop. No FTK-2 / capital / alpha claim."
)

# Sentinel values that mean "not bound" for L5 readiness (must not invent).
UNSET_SENTINELS = frozenset(
    {
        None,
        "OWNER_BLOCKED_UNSET",
        "BLOCKED_UNSET",
        "OWNER_OR_CRO_BLOCKED_UNSET",
        "UNSET",
        "",
    }
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


def load_owner_bind_receipt(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    return load_json(root / OWNER_BIND_RECEIPT_REL)


def load_parent_l4_freeze(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    return load_json(root / PARENT_L4_FREEZE_REL)


def _is_bound_scalar(value: Any) -> bool:
    """True if value is a concrete bound scalar (not an unset/blocked sentinel)."""
    if value in UNSET_SENTINELS:
        return False
    if isinstance(value, str):
        upper = value.upper()
        if "BLOCKED" in upper or upper in {"UNSET", "OWNER_BLOCKED_UNSET"}:
            return False
        # numeric-looking strings or non-empty concrete labels count as bound
        return len(value.strip()) > 0
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    return False


def evaluate_l5_readiness(doc: dict[str, Any]) -> dict[str, Any]:
    """Evaluate L5 readiness checklist outcome-blind from freeze document.

    Does not authorize L5. Returns checklist items + l5_ready flag.
    """
    estimand = doc.get("estimand") or {}
    clock = doc.get("economic_clock") or {}
    e1 = (estimand.get("E1") or {}).get("value") or {}
    e2 = (estimand.get("E2") or {}).get("value") or {}
    e2_owner = (estimand.get("E2") or {}).get("value_owner")
    e3 = (estimand.get("E3") or {}).get("value") or {}
    e3_owner = (estimand.get("E3") or {}).get("value_owner")
    e4 = (estimand.get("E4") or {}).get("value") or {}
    e5 = (estimand.get("E5") or {}).get("value") or {}
    e6 = (estimand.get("E6") or {}).get("value") or {}
    e7 = (estimand.get("E7") or {}).get("value") or {}
    e11 = (estimand.get("E11") or {}).get("value") or {}
    d7 = (doc.get("d6_d9_mapping") or {}).get("D7_CONFIRMATION_TIMING") or {}
    surface = doc.get("surface_inheritance") or {}
    fail_closed = doc.get("fail_closed_guards") or {}

    items: list[dict[str, Any]] = []

    def add(item_id: str, ok: bool, detail: str) -> None:
        items.append({"id": item_id, "pass": ok, "detail": detail})

    clock_ok = clock.get("economic_clock_class") == ECONOMIC_CLOCK_CLASS
    add(
        "economic_clock_class",
        clock_ok,
        f"economic_clock_class={clock.get('economic_clock_class')!r}",
    )

    h_val = e1.get("H_VALUE")
    h_ok = _is_bound_scalar(h_val)
    add("H_VALUE", h_ok, f"H_VALUE={h_val!r}")

    e2_ok = e2_owner in ("INHERITED_AUTHORITY", "OWNER_BOUND") and all(
        _is_bound_scalar(e2.get(k))
        for k in (
            "price_provider_semantics",
            "entry_price_convention",
            "exit_price_convention",
            "corporate_action_adjustment",
        )
    )
    add("E2_price_return", e2_ok, f"value_owner={e2_owner!r}")

    e3_ok = e3_owner in ("INHERITED_AUTHORITY", "OWNER_BOUND") and all(
        _is_bound_scalar(e3.get(k)) for k in ("execution_lag", "cost_formula")
    ) and e3.get("free_fit") is False
    add("E3_lag_cost", e3_ok, f"value_owner={e3_owner!r}")

    rt = e4.get("RIGHT_TAIL_PERCENTILE")
    rt_ok = _is_bound_scalar(rt)
    add("E4_percentile", rt_ok, f"RIGHT_TAIL_PERCENTILE={rt!r}")

    cat = e5.get("CATASTROPHE_PERCENTILE")
    cat_ok = _is_bound_scalar(cat)
    add("E5_percentile", cat_ok, f"CATASTROPHE_PERCENTILE={cat!r}")

    dj = e6.get("delta_J_required")
    dj_ok = _is_bound_scalar(dj)
    add("E6_delta_J", dj_ok, f"delta_J_required={dj!r}")

    k_val = e7.get("K")
    k_ok = isinstance(k_val, int) and k_val >= 1
    if not k_ok and isinstance(k_val, str) and k_val.isdigit() and int(k_val) >= 1:
        k_ok = True
    score_map = str(e7.get("score_map") or "")
    score_ok = "DUAL_NODE_EQUAL_WEIGHT_RANK_THEN_TOP_K" in score_map
    add("E7_K", k_ok and score_ok, f"K={k_val!r}; score_map_ok={score_ok}")

    d7_status = d7.get("rule_status")
    d7_ok = d7_status in (
        "INHERITED_AUTHORITY",
        "EXPLICITLY_OUT_OF_SCOPE_THIS_TRIAL",
    ) and d7.get("invented_this_freeze") is not True
    add("D7", d7_ok, f"rule_status={d7_status!r}")

    post_trial = doc.get("status") in POST_TRIAL2_STATUSES or doc.get(
        "authorized_phase"
    ) == "L5_COMPLETE_WAITING_OWNER_L7"
    if post_trial:
        e11_ok = (
            e11.get("bytes_joined") is True
            and "ao_ftk_1_econ_1_label_custody" in str(e11.get("identity_path") or "")
        )
        add("E11_labels_unjoined", e11_ok, f"post-trial bytes_joined={e11.get('bytes_joined')}")
    else:
        e11_ok = (
            e11.get("bytes_joined") is False
            and e11.get("join_authorized") is False
            and "ao_ftk_1_econ_1_label_custody" in str(e11.get("identity_path") or "")
        )
        add("E11_labels_unjoined", e11_ok, f"bytes_joined={e11.get('bytes_joined')}")

    dof_ok = surface.get("effective_decision_dof") == EFFECTIVE_DECISION_DOF
    add("surface_dof_2", dof_ok, f"dof={surface.get('effective_decision_dof')}")

    # Pre-auth bind checklist requires L5 still false. Post-trial docs flip auth;
    # readiness for bind purposes treats post-trial as already authorized (skip gate).
    if post_trial:
        l5_gate_ok = doc.get("l5_auto_open") is False
        add("l5_authorized_false", l5_gate_ok, "post-trial: auto_open remains false")
    else:
        l5_false = (
            doc.get("l5_authorized") is False
            and doc.get("economic_l5_authorized") is False
            and doc.get("l5_auto_open") is False
        )
        add("l5_authorized_false", l5_false, "l5 remains unauthorized this bind")

    fc_ok = bool(fail_closed) and all(
        fail_closed.get(k) == "FAIL_CLOSED"
        for k in (
            "economic_label_join_when_l5_false",
            "trial_debit_when_l5_false",
            "economic_evaluator_run_when_l5_false",
        )
        if k in fail_closed
    )
    # also accept nested implementation path presence
    if not fc_ok:
        fc_ok = (
            fail_closed.get("economic_label_join_when_l5_false") == "FAIL_CLOSED"
            and fail_closed.get("trial_debit_when_l5_false") == "FAIL_CLOSED"
            and fail_closed.get("economic_evaluator_run_when_l5_false") == "FAIL_CLOSED"
        )
    add("fail_closed_guards", fc_ok, "fail-closed guards present")

    not_fast = clock.get("not_fast_trading") is True
    not_ge = clock.get("not_great_enterprise_hodl") is True
    add(
        "clock_exclusions",
        not_fast and not_ge,
        f"not_fast_trading={not_fast}; not_ge_hodl={not_ge}",
    )

    blockers = [i["id"] for i in items if not i["pass"]]
    l5_ready = len(blockers) == 0
    return {
        "l5_ready": l5_ready,
        "checklist": items,
        "blockers_remaining": blockers,
        "economic_l5_authorized": bool(doc.get("economic_l5_authorized")),
        "post_trial": post_trial,
    }


def refuse_invented_bind(field: str, *, reason: str = "missing_owner_or_authority") -> None:
    """Hard refuse invented E2/E3/D7/H values — outcome-blind bind only."""
    raise Econ1FailClosedError(
        f"ao_ftk_1_econ_1_fail_closed:refuse_invent:{field}:{reason}"
    )


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
    post_trial = (
        doc.get("status") in POST_TRIAL2_STATUSES
        or doc.get("authorized_phase") == "L5_COMPLETE_WAITING_OWNER_L7"
    )

    if doc.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if doc.get("freeze_id") != FREEZE_ID:
        errors.append(f"freeze_id must be {FREEZE_ID}")
    if doc.get("parent_program") != PARENT_PROGRAM:
        errors.append(f"parent_program must be {PARENT_PROGRAM}")
    if doc.get("name") not in (NAME, BIND_NAME):
        errors.append(f"name must be {NAME} or {BIND_NAME}")
    if doc.get("status") not in RECOGNIZED_STATUSES:
        errors.append("status must be a recognized economic freeze terminal")

    if doc.get("authorized_phase") not in AUTHORIZED_PHASES:
        errors.append(
            "authorized_phase must be ECONOMIC_ESTIMAND_FREEZE or OWNER_BIND_TRANSITION_POSITION* "
            "or L5_COMPLETE_WAITING_OWNER_L7"
        )
    if doc.get("l7_route") != L7_ROUTE:
        errors.append(f"l7_route must be {L7_ROUTE}")
    if doc.get("second_l5") != "NOT_AUTHORIZED":
        errors.append("second_l5 must be NOT_AUTHORIZED")
    if doc.get("l5_auto_open") is not False:
        errors.append("l5_auto_open must be false")
    if doc.get("capital_authority") is not False:
        errors.append("capital_authority must be false")
    if doc.get("financial_alpha_evidence") != 0:
        errors.append("financial_alpha_evidence must be 0")

    if post_trial:
        if doc.get("l5_authorized") is not True:
            errors.append("post-trial l5_authorized must be true")
        if doc.get("economic_l5_authorized") is not True:
            errors.append("post-trial economic_l5_authorized must be true")
        if doc.get("runnable_evaluation") is not False:
            errors.append("post-trial runnable_evaluation must be false (one-shot spent)")
        if doc.get("label_bytes_joined") is not True:
            errors.append("post-trial label_bytes_joined must be true")
        if doc.get("material_trials_charged_this_turn") not in (1,):
            errors.append("post-trial material_trials_charged_this_turn must be 1")
        if doc.get("next_phase") != "L7_ROADMAP_DECISION":
            errors.append("post-trial next_phase must be L7_ROADMAP_DECISION")
    else:
        if doc.get("l5_authorized") is not False:
            errors.append("l5_authorized must be false")
        if doc.get("economic_l5_authorized") is not False:
            errors.append("economic_l5_authorized must be false")
        if doc.get("runnable_evaluation") is not False:
            errors.append("runnable_evaluation must be false")
        if doc.get("label_bytes_joined") is not False:
            errors.append("label_bytes_joined must be false")
        if doc.get("material_trials_charged_this_turn") != 0:
            errors.append("material_trials_charged_this_turn must be 0")

    # Transition-position clock (required after bind turn)
    clock = doc.get("economic_clock")
    if isinstance(clock, dict):
        if clock.get("economic_clock_class") != ECONOMIC_CLOCK_CLASS:
            errors.append(
                f"economic_clock.economic_clock_class must be {ECONOMIC_CLOCK_CLASS}"
            )
        if clock.get("not_fast_trading") is not True:
            errors.append("economic_clock.not_fast_trading must be true")
        if clock.get("not_great_enterprise_hodl") is not True:
            errors.append("economic_clock.not_great_enterprise_hodl must be true")
        ge = clock.get("great_enterprise_kernel")
        if ge is not None and ge not in ("OUT_OF_SCOPE", "OUT OF SCOPE"):
            errors.append("economic_clock.great_enterprise_kernel must be OUT_OF_SCOPE")
    elif doc.get("owner_bind") is not None:
        errors.append("economic_clock object required when owner_bind present")

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
        if post_trial:
            if bytes_joined is not True:
                errors.append("post-trial E11.bytes_joined must be true")
            if join_authorized is not True:
                errors.append("post-trial E11.join_authorized must be true")
        else:
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
            if d7.get("rule_status") not in D7_RULE_STATUSES:
                errors.append(
                    "D7.rule_status must be INHERITED_AUTHORITY, "
                    "BLOCKED_UNSET, or EXPLICITLY_OUT_OF_SCOPE_THIS_TRIAL"
                )
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
        if post_trial:
            if plan.get("debit_this_turn") is not True:
                errors.append("post-trial debit_this_turn must be true")
        else:
            if plan.get("debit_this_turn") is not False and plan.get("debit_this_turn") != "FORBIDDEN":
                errors.append("debit_this_turn must be false/FORBIDDEN")
        if plan.get("debit_trigger") != "ECONOMIC_L5_AUTHORIZATION_RECEIPT":
            errors.append("debit_trigger must be ECONOMIC_L5_AUTHORIZATION_RECEIPT")

    if doc.get("next_phase") not in RECOGNIZED_NEXT_PHASES:
        errors.append(
            "next_phase must be WAIT_OWNER_L5_ECONOMIC | WAITING_OWNER_NUMERICS | "
            "HOLD_EVIDENCE | BLOCKED_MISSING_AUTHORITY | L7_ROADMAP_DECISION"
        )

    readiness = evaluate_l5_readiness(doc)
    blockers = doc.get("l5_blockers")
    if post_trial:
        if not readiness["l5_ready"]:
            errors.append("post-trial checklist must remain green on bound fields")
        if not isinstance(blockers, list):
            errors.append("l5_blockers must be a list")
        if doc.get("status") not in POST_TRIAL2_STATUSES:
            errors.append("post-trial status must be ECON_L5_COMPLETE_WAITING_OWNER_L7")
    elif readiness["l5_ready"]:
        # when fully ready, blockers may be empty or only residual L5 auth note
        if not isinstance(blockers, list):
            errors.append("l5_blockers must be a list")
        if doc.get("status") not in (
            "ECON_FREEZE_PASS_L5_READY",
            "ECON_FREEZE_PASS_WAITING_OWNER_L5",
        ):
            errors.append("status must reflect L5_READY when checklist green")
        if doc.get("next_phase") != "WAIT_OWNER_L5_ECONOMIC":
            errors.append("next_phase must be WAIT_OWNER_L5_ECONOMIC when L5_READY")
        if doc.get("l5_authorized") is not False or doc.get("economic_l5_authorized") is not False:
            errors.append("L5_READY never auto-authorizes economic L5")
    else:
        if not isinstance(blockers, list) or not blockers:
            errors.append("l5_blockers must be a non-empty list when not L5_READY")

    # owner_bind section consistency (if present)
    owner_bind = doc.get("owner_bind")
    if isinstance(owner_bind, dict):
        if owner_bind.get("outcome_blind") is not True:
            errors.append("owner_bind.outcome_blind must be true")
        if owner_bind.get("residual_peek") is not False:
            errors.append("owner_bind.residual_peek must be false")
        if owner_bind.get("verdict") not in BIND_VERDICTS:
            errors.append("owner_bind.verdict must be PASS_L5_READY|WAITING_NUMERICS|HOLD|BLOCKED")
        if owner_bind.get("l5_ready") is True and not readiness["l5_ready"]:
            errors.append("owner_bind.l5_ready true but checklist not green")
        if owner_bind.get("l5_ready") is False and readiness["l5_ready"]:
            errors.append("owner_bind.l5_ready false but checklist is green")
        if post_trial:
            if owner_bind.get("material_trials_charged_this_turn") not in (1,):
                errors.append("post-trial owner_bind material_trials_charged_this_turn must be 1")
        else:
            if owner_bind.get("material_trials_charged_this_turn") not in (0, None):
                errors.append("owner_bind must not charge material trials")

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

    # Hard anti-invention: E2/E3 must not claim inheritance without path
    e2 = (doc.get("estimand") or {}).get("E2") or {}
    if e2.get("value_owner") == "INHERITED_AUTHORITY":
        if not (e2.get("authority_path") or (e2.get("value") or {}).get("authority_path")):
            errors.append("E2 INHERITED_AUTHORITY requires authority_path citation")
    e3 = (doc.get("estimand") or {}).get("E3") or {}
    if e3.get("value_owner") == "INHERITED_AUTHORITY":
        if not (e3.get("authority_path") or (e3.get("value") or {}).get("authority_path")):
            errors.append("E3 INHERITED_AUTHORITY requires authority_path citation")

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
