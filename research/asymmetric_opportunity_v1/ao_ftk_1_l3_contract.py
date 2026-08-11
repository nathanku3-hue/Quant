"""AO-FTK-1 L0–L3 Representation/SNR disposition helpers.

Research-only. No outcome join, no material trial debit, no Q/M revival, no L5.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SLICE_ID = "AO-FTK-1-20260812"
PARENT_FREEZE_COMMIT = "6832066"
KERNEL_ID = "AO_FTK_0_TRANSITION_SPARSE_BASIS_V1"
DISPOSITION_JSON_REL = Path(
    "docs/context/e2e_evidence/ao_ftk_1_20260812_l3_representation_snr_disposition.json"
)
DISPOSITION_MD_REL = Path(
    "docs/context/e2e_evidence/ao_ftk_1_20260812_l3_representation_snr_disposition.md"
)
PREFLIGHT_JSON_REL = Path("docs/architecture/ao_ftk_1_20260812_l0_l3_preflight.json")
PREFLIGHT_MD_REL = Path("docs/architecture/ao_ftk_1_20260812_l0_l3_preflight.md")
PARENT_FREEZE_REL = Path("docs/architecture/ao_ftk_0_transition_sparse_basis_v1.json")

ALLOWED_DISPOSITIONS = frozenset(
    {"PASS", "SIMPLIFY", "REVISE_WITHIN_FREEZE", "BLOCK"}
)
R_KEYS = (
    "R1_magnitude_monotonicity",
    "R2_weak_signal_sensitivity",
    "R3_peer_common_mode_rejection",
    "R4_async_causal_sequence_retention",
    "R5_staleness_degradation",
    "R6_missingness_confidence_monotonicity",
    "R7_conflicting_evidence_retention",
    "R8_abstention_vs_deletion",
)
ALLOWED_R_STATUS = frozenset({"PASS", "FAIL", "NOT_EVALUABLE_THIS_TURN"})

# Forbidden API tokens must not appear as FTK-1 decision surface tokens.
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

# Paths / helpers that would imply outcome join — must not be referenced as invoked.
FORBIDDEN_OUTCOME_JOIN_HELPER_TOKENS = (
    "join_labels",
    "open_outcomes",
    "outcome_join",
    "winner_label_join",
    "w6_lockbox_join",
)


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object JSON at {path}")
    return data


def load_disposition(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    return load_json(root / DISPOSITION_JSON_REL)


def load_preflight(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    return load_json(root / PREFLIGHT_JSON_REL)


def validate_l3_disposition(doc: dict[str, Any]) -> list[str]:
    """Return list of schema / firewall errors (empty = valid)."""
    errors: list[str] = []

    if doc.get("slice_id") != SLICE_ID:
        errors.append(f"slice_id must be {SLICE_ID}")
    if doc.get("parent_freeze_commit") != PARENT_FREEZE_COMMIT:
        errors.append(f"parent_freeze_commit must be {PARENT_FREEZE_COMMIT}")
    if doc.get("kernel_id") != KERNEL_ID:
        errors.append(f"kernel_id must remain {KERNEL_ID}")

    phases = doc.get("phases_completed")
    if phases != ["L0", "L1", "L2", "L3"]:
        errors.append("phases_completed must be [L0, L1, L2, L3]")

    rblock = doc.get("r1_r8")
    if not isinstance(rblock, dict):
        errors.append("r1_r8 must be an object")
    else:
        for key in R_KEYS:
            if key not in rblock:
                errors.append(f"missing r1_r8.{key}")
                continue
            entry = rblock[key]
            if not isinstance(entry, dict):
                errors.append(f"r1_r8.{key} must be object")
                continue
            status = entry.get("status")
            if status not in ALLOWED_R_STATUS:
                errors.append(f"r1_r8.{key}.status invalid: {status!r}")
            if "evidence" not in entry:
                errors.append(f"r1_r8.{key}.evidence required")
            if "notes" not in entry:
                errors.append(f"r1_r8.{key}.notes required")

    disposition = doc.get("disposition")
    if disposition not in ALLOWED_DISPOSITIONS:
        errors.append(f"disposition invalid: {disposition!r}")

    if disposition == "PASS" and doc.get("first_fail_R_if_any") not in (None, "null"):
        # allow null only
        if doc.get("first_fail_R_if_any") is not None:
            errors.append("PASS requires first_fail_R_if_any null")

    if doc.get("material_trials_charged_this_slice") != 0:
        errors.append("material_trials_charged_this_slice must be 0")
    if doc.get("material_trials_remaining") != 3:
        errors.append("material_trials_remaining must remain 3")
    if doc.get("outcome_open_authorized") is not False:
        errors.append("outcome_open_authorized must be false")
    if doc.get("l5_authorized") is not False:
        errors.append("l5_authorized must be false")
    if doc.get("l5_auto_open") is not False:
        errors.append("l5_auto_open must be false")
    if doc.get("financial_alpha_evidence") != 0:
        errors.append("financial_alpha_evidence must be 0")
    if doc.get("qm_terms_used") is not False:
        errors.append("qm_terms_used must be false")
    if doc.get("label_join_performed") is not False:
        errors.append("label_join_performed must be false")
    if doc.get("stop_lines_honored") is not True:
        errors.append("stop_lines_honored must be true")
    if doc.get("runnable_evaluation") is not False:
        errors.append("runnable_evaluation must be false")

    next_phase = doc.get("next_phase_recommendation")
    if disposition in {"PASS", "SIMPLIFY"}:
        if next_phase != "L4_CHARGED_SLICE_FREEZE":
            errors.append(
                "PASS/SIMPLIFY must recommend L4_CHARGED_SLICE_FREEZE (not auto L5)"
            )
    if disposition == "BLOCK" and next_phase != "L7_STOP_OR_NEW_SURFACE":
        errors.append("BLOCK must recommend L7_STOP_OR_NEW_SURFACE")

    dof = doc.get("effective_dof_recommendation")
    if disposition == "PASS" and dof != 2:
        errors.append("PASS on inherited 2-DOF surface should recommend effective_dof=2")
    if disposition == "SIMPLIFY" and dof != 1:
        errors.append("SIMPLIFY must recommend effective_dof=1")

    # Firewall: disposition body must not authorize L5 via next_phase string.
    if isinstance(next_phase, str) and "L5" in next_phase and "NOT" not in next_phase:
        if next_phase not in {
            # allow explicit denial phrases only if ever used
        }:
            if next_phase.startswith("L5"):
                errors.append("next_phase_recommendation must not open L5")

    return errors


def assert_valid_l3_disposition(doc: dict[str, Any]) -> None:
    errors = validate_l3_disposition(doc)
    if errors:
        raise AssertionError("L3 disposition invalid:\n- " + "\n- ".join(errors))


def ftk1_surface_blob(doc: dict[str, Any]) -> str:
    """Flatten API-relevant strings for forbidden-token scan (not path evidence)."""
    parts: list[str] = []
    for key in (
        "kernel_id",
        "disposition",
        "next_phase_recommendation",
        "representation_under_test",
        "L1_confirmation",
    ):
        if key in doc:
            parts.append(json.dumps(doc[key], ensure_ascii=False))
    # Allowed sensing names may mention inventory/margin only.
    return "\n".join(parts)


def assert_no_qm_tokens_in_ftk1_api_surface(doc: dict[str, Any]) -> None:
    """Ensure disposition does not introduce Q/M decision tokens as used terms."""
    if doc.get("qm_terms_used") is not False:
        raise AssertionError("qm_terms_used must be false")
    # Explicit park fields must remain terminal.
    if doc.get("q_source_status") != "Q_SOURCE_BLOCKED_TERMINAL":
        raise AssertionError("q_source_status must remain Q_SOURCE_BLOCKED_TERMINAL")
    if doc.get("ok_sbi_s2") != "NOT_AUTHORIZED":
        raise AssertionError("ok_sbi_s2 must remain NOT_AUTHORIZED")
    if doc.get("qm_revival_in_ftk") != "FORBIDDEN":
        raise AssertionError("qm_revival_in_ftk must remain FORBIDDEN")

    # Scan decision-ish free text for bare forbidden tokens as word-like uses
    # (exclude evidence path strings which may mention historical q_source receipts).
    blob = ftk1_surface_blob(doc)
    for token in FORBIDDEN_QM_API_TOKENS:
        # Whole-token style match; allow substrings inside longer words only if not exact.
        if token in {"Q", "M"}:
            # Single-letter tokens: require non-identifier boundaries.
            if re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", blob):
                # Allowed in explicit denial contexts only — reject if present at all on surface.
                raise AssertionError(f"Forbidden QM token {token!r} in FTK-1 API surface")
        else:
            if token in blob:
                raise AssertionError(f"Forbidden QM token {token!r} in FTK-1 API surface")


def assert_no_outcome_join_helpers_invoked(doc: dict[str, Any]) -> None:
    if doc.get("label_join_performed") is not False:
        raise AssertionError("label_join_performed must be false")
    if doc.get("outcome_open_authorized") is not False:
        raise AssertionError("outcome_open_authorized must be false")
    # Receipt must not claim join helpers were invoked.
    text = json.dumps(doc, ensure_ascii=False).lower()
    for token in FORBIDDEN_OUTCOME_JOIN_HELPER_TOKENS:
        # Presence in stop_lines_checked is OK; presence as true action is not.
        if f'"{token}": true' in text or f"{token}=true" in text:
            raise AssertionError(f"Outcome join helper appears invoked: {token}")


def assert_material_trial_counter_unchanged(doc: dict[str, Any]) -> None:
    if doc.get("material_trials_charged_this_slice") != 0:
        raise AssertionError("material trial was charged")
    if doc.get("material_trials_remaining") != 3:
        raise AssertionError("material_trials_remaining must remain 3")
