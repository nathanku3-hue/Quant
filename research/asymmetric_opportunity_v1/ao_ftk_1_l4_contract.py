"""AO-FTK-1 L4 charged-slice freeze helpers.

Custody + preregistration only. No L5, no trial debit, no label join, no alpha.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SLICE_ID = "AO-FTK-1-20260812"
KERNEL_ID = "AO_FTK_0_TRANSITION_SPARSE_BASIS_V1"
PARENT_FREEZE_COMMIT = "6832066"
L3_DISPOSITION_COMMIT = "28aa0f1"
PLAN_ID = "FTK1_TRIAL_DEBIT_PLAN_V1"
EFFECTIVE_DECISION_DOF = 2

MACHINE_FREEZE_REL = Path(
    "docs/architecture/ao_ftk_1_20260812_l4_charged_slice_freeze.json"
)
MD_FREEZE_REL = Path("docs/architecture/ao_ftk_1_20260812_l4_charged_slice_freeze.md")
RECEIPT_REL = Path(
    "docs/context/e2e_evidence/ao_ftk_1_20260812_l4_charged_slice_freeze.json"
)
L3_DISPOSITION_REL = Path(
    "docs/context/e2e_evidence/ao_ftk_1_20260812_l3_representation_snr_disposition.json"
)
PARENT_FREEZE_REL = Path("docs/architecture/ao_ftk_0_transition_sparse_basis_v1.json")
PREFLIGHT_REL = Path("docs/architecture/ao_ftk_1_20260812_l0_l3_preflight.json")
LABEL_CUSTODY_DIR_REL = Path(
    "data/prebreakout/compiled/ao_ftk_1_20260812_label_custody"
)
LABEL_IDENTITY_REL = LABEL_CUSTODY_DIR_REL / "development_label_pack.identity.json"
LABEL_HASH_PROCEDURE_REL = (
    LABEL_CUSTODY_DIR_REL / "development_label_pack.hash_procedure.json"
)

REQUIRED_OPERATOR_IDS = (
    "INV_DELTA_MEAN_REVERSION",
    "MARGIN_M1_STATE_MEAN_REVERSION",
)

BLOCKED_UNSET_FIELDS = (
    "payoff_horizon",
    "payoff_horizon_primary",
    "payoff_horizon_secondary",
    "right_tail_cut",
    "right_tail_definition",
    "catastrophe_cut",
    "catastrophe_definition",
)

CONSTITUTION = (
    "L4 freezes the passed 2-DOF candidate and the debit/join locks. "
    "It does not spend the trial, open labels, or claim alpha. "
    "Stop at WAIT_OWNER_L5."
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


class L4FailClosedError(PermissionError):
    """Raised when L5-gated operations are attempted without authorization."""


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


def load_label_identity(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    return load_json(root / LABEL_IDENTITY_REL)


def load_label_hash_procedure(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    return load_json(root / LABEL_HASH_PROCEDURE_REL)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256_text(canonical)


def _require_l5_authorized(*, l5_authorized: bool, action: str) -> None:
    if l5_authorized is not True:
        raise L4FailClosedError(
            f"ao_ftk_1_l4_fail_closed:{action}:l5_authorized=false"
        )


def label_join(
    *,
    l5_authorized: bool = False,
    join_authorized: bool = False,
    **_: Any,
) -> None:
    """Fail closed unless separate owner L5 authorization is present."""
    _require_l5_authorized(l5_authorized=l5_authorized, action="label_join")
    if join_authorized is not True:
        raise L4FailClosedError("ao_ftk_1_l4_fail_closed:label_join:join_authorized=false")
    raise L4FailClosedError(
        "ao_ftk_1_l4_fail_closed:label_join:join_not_implemented_in_l4"
    )


def trial_debit(
    *,
    l5_authorized: bool = False,
    debit_units: int = 1,
    **_: Any,
) -> None:
    """Fail closed unless separate owner L5 authorization is present."""
    _require_l5_authorized(l5_authorized=l5_authorized, action="trial_debit")
    if debit_units != 1:
        raise L4FailClosedError(
            f"ao_ftk_1_l4_fail_closed:trial_debit:debit_units_must_be_1_got_{debit_units}"
        )
    raise L4FailClosedError(
        "ao_ftk_1_l4_fail_closed:trial_debit:debit_not_implemented_in_l4"
    )


def evaluator_run(
    *,
    l5_authorized: bool = False,
    runnable_evaluation: bool = False,
    **_: Any,
) -> None:
    """Fail closed unless separate owner L5 authorization + runnable flag."""
    _require_l5_authorized(l5_authorized=l5_authorized, action="evaluator.run")
    if runnable_evaluation is not True:
        raise L4FailClosedError(
            "ao_ftk_1_l4_fail_closed:evaluator.run:runnable_evaluation=false"
        )
    raise L4FailClosedError(
        "ao_ftk_1_l4_fail_closed:evaluator.run:run_not_implemented_in_l4"
    )


# Aliases matching prompt naming.
label_join_fn = label_join
trial_debit_fn = trial_debit


class Evaluator:
    """Minimal evaluator surface that refuses unless L5-authorized."""

    def run(
        self,
        *,
        l5_authorized: bool = False,
        runnable_evaluation: bool = False,
        **kwargs: Any,
    ) -> None:
        evaluator_run(
            l5_authorized=l5_authorized,
            runnable_evaluation=runnable_evaluation,
            **kwargs,
        )


def validate_l4_freeze(doc: dict[str, Any]) -> list[str]:
    """Return schema / firewall errors (empty = valid L4 freeze)."""
    errors: list[str] = []

    if doc.get("schema_version") != "ao_ftk_1_l4_charged_slice_freeze_v1":
        errors.append("schema_version must be ao_ftk_1_l4_charged_slice_freeze_v1")
    if doc.get("slice_id") != SLICE_ID:
        errors.append(f"slice_id must be {SLICE_ID}")
    if doc.get("status") != "L4_FREEZE_READY_WAITING_OWNER_L5":
        errors.append("status must be L4_FREEZE_READY_WAITING_OWNER_L5")
    if doc.get("parent_freeze_commit") != PARENT_FREEZE_COMMIT:
        errors.append(f"parent_freeze_commit must be {PARENT_FREEZE_COMMIT}")
    if doc.get("l3_disposition_commit") != L3_DISPOSITION_COMMIT:
        errors.append(f"l3_disposition_commit must be {L3_DISPOSITION_COMMIT}")
    if doc.get("l3_disposition") != "PASS":
        errors.append("l3_disposition must be PASS")
    if doc.get("effective_decision_dof") != EFFECTIVE_DECISION_DOF:
        errors.append("effective_decision_dof must be 2 (frozen; no silent 1-DOF collapse)")
    if doc.get("kernel_id") != KERNEL_ID:
        errors.append(f"kernel_id must remain {KERNEL_ID}")

    if doc.get("l5_authorized") is not False:
        errors.append("l5_authorized must be false")
    if doc.get("l5_auto_open") is not False:
        errors.append("l5_auto_open must be false")
    if doc.get("runnable_evaluation") is not False:
        errors.append("runnable_evaluation must be false")
    if doc.get("capital_authority") is not False:
        errors.append("capital_authority must be false")
    if doc.get("financial_alpha_evidence") != 0:
        errors.append("financial_alpha_evidence must be 0")
    if doc.get("qm_terms_forbidden") is not True:
        errors.append("qm_terms_forbidden must be true")

    # Representation
    rep = doc.get("representation")
    if not isinstance(rep, dict):
        errors.append("representation must be object")
    else:
        if rep.get("inventory_state") != (
            "continuous lag-1 inventory economic-level delta"
        ):
            errors.append("representation.inventory_state mismatch")
        if rep.get("margin_state") != "continuous operating-margin M1 state":
            errors.append("representation.margin_state mismatch")
        if rep.get("sensing_preference") != "continuous preferred over sign-only scores":
            errors.append("representation.sensing_preference mismatch")
        if "INV_DELTA_MEAN_REVERSION" not in str(rep.get("inventory_decision_emit", "")):
            errors.append("representation.inventory_decision_emit must pin INV_DELTA")

    # Operators
    ops = doc.get("operators")
    if not isinstance(ops, list) or len(ops) != 2:
        errors.append("operators must be a list of length 2")
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
            if op.get("status") != "FROZEN_DECISION_SURFACE":
                errors.append(f"{op.get('operator_id')}: status must be FROZEN_DECISION_SURFACE")
            if not op.get("immutability_pin"):
                errors.append(f"{op.get('operator_id')}: immutability_pin required")
            if op.get("operator_id") == "MARGIN_M1_STATE_MEAN_REVERSION":
                if op.get("m1_bytes_mutation") != "FORBIDDEN":
                    errors.append("MARGIN_M1: m1_bytes_mutation must be FORBIDDEN")

    routing = doc.get("operator_routing") or doc.get("routing")
    if isinstance(routing, dict):
        mode = routing.get("mode")
    else:
        mode = routing
    if mode != "DOMAIN_LIMITED_EX_ANTE":
        errors.append("routing must be DOMAIN_LIMITED_EX_ANTE")

    # Material trial debit plan
    plan = doc.get("material_trial_debit")
    if not isinstance(plan, dict):
        errors.append("material_trial_debit must be object")
    else:
        if plan.get("plan_id") != PLAN_ID:
            errors.append(f"material_trial_debit.plan_id must be {PLAN_ID}")
        if plan.get("hard_material_trials_total") != 3:
            errors.append("hard_material_trials_total must be 3")
        if plan.get("current_charged") != 0:
            errors.append("current_charged must be 0")
        if plan.get("remaining") != 3:
            errors.append("remaining must be 3")
        if plan.get("next_debit") != 1:
            errors.append("next_debit must be 1")
        if plan.get("debit_trigger") != "L5_AUTHORIZATION_RECEIPT":
            errors.append("debit_trigger must be L5_AUTHORIZATION_RECEIPT")
        if plan.get("free_threshold_grid") != "FORBIDDEN":
            errors.append("free_threshold_grid must be FORBIDDEN")
        if plan.get("uncharged_adaptive_search") != "FORBIDDEN":
            errors.append("uncharged_adaptive_search must be FORBIDDEN")

    # Label pack
    lp = doc.get("label_pack")
    if not isinstance(lp, dict):
        errors.append("label_pack must be object")
    else:
        if lp.get("LABEL_IDENTITY_FROZEN") is not True:
            errors.append("LABEL_IDENTITY_FROZEN must be true")
        if lp.get("LABEL_HASH_PROCEDURE_FROZEN") is not True:
            errors.append("LABEL_HASH_PROCEDURE_FROZEN must be true")
        if lp.get("LABEL_BYTES_JOINED") is not False:
            errors.append("LABEL_BYTES_JOINED must be false")
        if lp.get("label_join") is not False:
            errors.append("label_join must be false")
        if lp.get("outcome_open") is not False:
            errors.append("outcome_open must be false")
        if lp.get("seal_status") != "IDENTITY_AND_HASH_FROZEN_UNJOINED":
            errors.append("seal_status must be IDENTITY_AND_HASH_FROZEN_UNJOINED")
        if lp.get("join_authorized") is not False:
            errors.append("join_authorized must be false")
        if lp.get("join_performed") is not False:
            errors.append("join_performed must be false")
        if lp.get("outcome_inspected") is not False:
            errors.append("outcome_inspected must be false")

    # Economic cuts remain BLOCKED_UNSET
    for field in (
        "payoff_horizon",
        "right_tail_cut",
        "catastrophe_cut",
    ):
        if doc.get(field) != "BLOCKED_UNSET":
            errors.append(f"{field} must be BLOCKED_UNSET")

    econ = doc.get("economic_cuts")
    if isinstance(econ, dict):
        for field in (
            "payoff_horizon_primary",
            "payoff_horizon_secondary",
            "right_tail_definition",
            "catastrophe_definition",
        ):
            if econ.get(field) != "BLOCKED_UNSET":
                errors.append(f"economic_cuts.{field} must be BLOCKED_UNSET")

    if not isinstance(doc.get("stop_lines"), list) or not doc.get("stop_lines"):
        errors.append("stop_lines must be a non-empty list")

    # No third DOF / silent collapse markers
    if doc.get("third_decision_dof") not in (None, False, "FORBIDDEN"):
        if doc.get("third_decision_dof") is True:
            errors.append("third_decision_dof forbidden")
    if doc.get("silent_one_dof_collapse") not in (None, False, "FORBIDDEN"):
        if doc.get("silent_one_dof_collapse") is True:
            errors.append("silent_one_dof_collapse forbidden")

    return errors


def assert_valid_l4_freeze(doc: dict[str, Any]) -> None:
    errors = validate_l4_freeze(doc)
    if errors:
        raise AssertionError("L4 freeze invalid:\n- " + "\n- ".join(errors))


def assert_no_qm_terms_in_l4_surface(doc: dict[str, Any]) -> None:
    if doc.get("qm_terms_forbidden") is not True:
        raise AssertionError("qm_terms_forbidden must be true")
    # Decision surface fields only (not evidence paths that may name q_source receipts).
    surface = json.dumps(
        {
            "kernel_id": doc.get("kernel_id"),
            "representation": doc.get("representation"),
            "operators": doc.get("operators"),
            "operator_routing": doc.get("operator_routing") or doc.get("routing"),
        },
        ensure_ascii=False,
    )
    for token in FORBIDDEN_QM_API_TOKENS:
        if token in {"Q", "M"}:
            # Single-letter: require non-identifier boundaries; L4 surface should not use them.
            import re

            if re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", surface):
                raise AssertionError(f"Forbidden QM token {token!r} in L4 API surface")
        else:
            if token in surface:
                raise AssertionError(f"Forbidden QM token {token!r} in L4 API surface")
