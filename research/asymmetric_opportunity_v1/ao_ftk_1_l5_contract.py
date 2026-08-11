"""AO-FTK-1 L5 sensing-first one-shot contract.

Exactly one owner-authorized charged sensing evaluation under the L4 freeze:
one trial debit, one label join, one frozen 2-DOF eval, L6 first-fail, stop at L7.

No redesign, no second run, no capital, no financial alpha claim.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from research.asymmetric_opportunity_v1 import ao_ftk_1_l4_contract as l4
from research.econphysics_prebreakout_v1.contracts import (
    TEMPORAL_FOLD_COUNT,
    StructuredSnapshot,
    build_structured_snapshots,
    deterministic_xs_holdout,
)
from research.econphysics_prebreakout_v1.dynamics_diagnostic import (
    DELTA_MEAN_REVERSION,
    M1_STATE_MEAN_REVERSION,
    _economic_levels,
    _negate_prediction,
    _sign,
    _difference,
)
from research.econphysics_prebreakout_v1.low_snr_m1 import build_low_snr_states
from research.econphysics_prebreakout_v1.shootout_evaluator import (
    DEFAULT_MINIMUM_FOLD_COVERAGE,
    DEFAULT_MINIMUM_FOLD_N,
    MINIMUM_INFORMATIVE_TEMPORAL_FOLDS,
    _evaluate_model_target,
)
from research.econphysics_prebreakout_v1.transition_evaluator import (
    INVENTORY_TARGET_ID,
    MARGIN_TARGET_ID,
    TransitionObservation,
    _adjacent_pairs,
    _inventory_normalization_target,
    _operating_margin_target,
    _temporal_fold_map,
)


SLICE_ID = "AO-FTK-1-20260812"
MODE = "SENSING_FIRST"
PLAN_ID = "FTK1_TRIAL_DEBIT_PLAN_V1"
EFFECTIVE_DECISION_DOF = 2
RUN_ID = "AO_FTK_1_20260812_L5_SENSING_RUN_1"
AUTH_RECEIPT_ID = "AO_FTK_1_20260812_L5_AUTHORIZATION"
DEBIT_RECEIPT_ID = "AO_FTK_1_20260812_L5_TRIAL_DEBIT"
JOIN_RECEIPT_ID = "AO_FTK_1_20260812_L5_LABEL_JOIN"
L6_RECEIPT_ID = "AO_FTK_1_20260812_L6_LAYERED_DIAGNOSIS"
L7_PACKET_ID = "AO_FTK_1_20260812_L7_OWNER_PACKET"

INV_OPERATOR_ID = "INV_DELTA_MEAN_REVERSION"
MARGIN_OPERATOR_ID = "MARGIN_M1_STATE_MEAN_REVERSION"

SENSING_TARGETS = (
    {
        "target_id": INVENTORY_TARGET_ID,
        "node_id": "INVENTORY_CHANNEL_STATE",
        "operator_id": INV_OPERATOR_ID,
        "family_alias": DELTA_MEAN_REVERSION,
        "horizon": "NEXT_PIT_STRUCTURED_TRANSITION",
    },
    {
        "target_id": MARGIN_TARGET_ID,
        "node_id": "MARGIN_CASH_STATE",
        "operator_id": MARGIN_OPERATOR_ID,
        "family_alias": M1_STATE_MEAN_REVERSION,
        "horizon": "NEXT_PIT_STRUCTURED_TRANSITION",
    },
)

AUTH_REL = Path("docs/context/e2e_evidence/ao_ftk_1_20260812_l5_authorization.json")
DEBIT_REL = Path("docs/context/e2e_evidence/ao_ftk_1_20260812_l5_trial_debit.json")
JOIN_REL = Path("docs/context/e2e_evidence/ao_ftk_1_20260812_l5_label_join.json")
RUN_REL = Path("docs/context/e2e_evidence/ao_ftk_1_20260812_l5_run.json")
L6_REL = Path("docs/context/e2e_evidence/ao_ftk_1_20260812_l6_layered_diagnosis.json")
L6_MD_REL = Path("docs/context/e2e_evidence/ao_ftk_1_20260812_l6_layered_diagnosis.md")
L7_REL = Path("docs/context/e2e_evidence/ao_ftk_1_20260812_l7_owner_packet.json")
RUN_MD_REL = Path("docs/context/e2e_evidence/ao_ftk_1_20260812_l5_run.md")

LABEL_CUSTODY_DIR_REL = Path("data/prebreakout/compiled/ao_ftk_1_20260812_label_custody")
JOINED_MANIFEST_REL = LABEL_CUSTODY_DIR_REL / "development_label_pack.joined.manifest.json"
JOINED_LABELS_REL = LABEL_CUSTODY_DIR_REL / "development_labels.parquet"
JOINED_LABELS_JSONL_REL = LABEL_CUSTODY_DIR_REL / "development_labels.jsonl"

DEFAULT_STRUCTURED_TRANSITIONS = Path(
    "data/prebreakout/raw/econphysics_s0_structured_v1/structured_transitions.csv"
)
DEFAULT_MASTER = Path(
    "data/prebreakout/compiled/econphysics_s0_request_20260810/s0_ciqsec_company_master.csv"
)
DEFAULT_TRANSITION_PLAN = Path(
    "data/prebreakout/compiled/econphysics_s0_request_20260810/s0_period_change_plan.csv"
)

CONSTITUTION = (
    "One auth · one debit · one join · one frozen sensing eval · "
    "L6 first-fail + info-gain · stop at L7. "
    "No redesign, no second run, no capital, no alpha claim."
)


class L5FailClosedError(PermissionError):
    """Raised when L5 one-shot gates are violated."""


class L5CustodyError(RuntimeError):
    """Raised when freeze / hash / authority custody fails."""


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object JSON at {path}")
    return data


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_text(blob)


def write_json_atomic(path: Path, payload: Mapping[str, Any], *, overwrite: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"ao_ftk_1_l5_output_exists:{path}")
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return sha256_file(path)


def write_text_atomic(path: Path, text: str, *, overwrite: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"ao_ftk_1_l5_output_exists:{path}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            if not text.endswith("\n"):
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return sha256_file(path)


# ---------------------------------------------------------------------------
# Step 0 — authority self-check
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuthoritySelfCheck:
    ok: bool
    errors: tuple[str, ...]
    slice_id: str
    l3_disposition: str
    l4_terminal_verdict: str
    material_trials_remaining: int
    effective_decision_dof: int


def authority_self_check(repo: Path | None = None) -> AuthoritySelfCheck:
    root = repo or default_repo_root()
    errors: list[str] = []

    sot = load_json(root / "docs/context/research_loop_state_current.json")
    freeze = l4.load_machine_freeze(root)
    receipt = l4.load_receipt(root)
    l3 = load_json(root / l4.L3_DISPOSITION_REL)

    nws = sot.get("next_worker_slice") or {}
    primary = nws.get("primary")
    recommended = nws.get("recommended")
    track = next(
        (t for t in sot.get("active_tracks", []) if t.get("track_id") == "AO-FTK-1"),
        {},
    )
    track_slice = track.get("slice_id")
    # Accept either active primary = FTK-1 or post-L4-close OWNER_SELECT with
    # recommended L5 authorize and track slice still AO-FTK-1-20260812.
    primary_ok = primary == SLICE_ID or (
        primary == "OWNER_SELECT"
        and track_slice == SLICE_ID
        and recommended in {
            "L5_AUTHORIZE_SEPARATE",
            "L5_AUTHORIZE",
            "L5_SENSING_FIRST",
        }
    )
    if not primary_ok:
        errors.append(
            f"primary/track slice not ready for L5: primary={primary!r} "
            f"recommended={recommended!r} track_slice={track_slice!r}"
        )

    if freeze.get("slice_id") != SLICE_ID or receipt.get("slice_id") != SLICE_ID:
        errors.append("L4 freeze/receipt slice_id mismatch")

    l3_disp = l3.get("disposition") or freeze.get("l3_disposition")
    if l3_disp != "PASS":
        errors.append(f"L3 disposition not PASS: {l3_disp!r}")
    if track.get("l3_disposition") not in (None, "PASS"):
        errors.append(f"track L3 disposition not PASS: {track.get('l3_disposition')!r}")

    l4_verdict = receipt.get("terminal_verdict")
    if l4_verdict != "L4_FREEZE_PASS":
        errors.append(f"L4 terminal_verdict not L4_FREEZE_PASS: {l4_verdict!r}")

    freeze_errors = l4.validate_l4_freeze(freeze)
    if freeze_errors:
        errors.append("L4 freeze no longer binding: " + "; ".join(freeze_errors[:5]))

    next_phase = (sot.get("process") or {}).get("next_phase")
    if next_phase not in {
        "WAIT_OWNER_L5",
        "L5_RUN",
        "OWNER_L5",
        None,
    } and not str(next_phase or "").startswith("WAIT_OWNER_L5"):
        # Allow only L5-entry phases; refuse if already past L7 without new auth.
        if next_phase in {"OWNER_L7_DECISION", "L7_ROADMAP_DECISION"} and track.get(
            "l5_auth_spent"
        ):
            errors.append(f"L5 one-shot already spent; next_phase={next_phase!r}")

    remaining = int((freeze.get("material_trial_debit") or {}).get("remaining") or 0)
    # Remaining is L4-plan baseline (3). Live SoT may already show charged.
    sot_remaining = int(track.get("material_trials_remaining", remaining))
    if sot_remaining < 1:
        errors.append(f"material_trials remaining < 1: {sot_remaining}")
    if track.get("l5_auth_spent") is True:
        errors.append("l5_auth_spent=true; second L5 forbidden under this receipt")
    if track.get("label_bytes_joined") is True and track.get("l5_authorized") is not True:
        errors.append("labels already joined without L5 auth track flag")

    dof = int(freeze.get("effective_decision_dof") or track.get("effective_decision_dof") or 0)
    if dof != EFFECTIVE_DECISION_DOF:
        errors.append(f"effective_decision_dof not 2: {dof}")

    # L4 freeze must still forbid silent L5 in its own document.
    if freeze.get("l5_auto_open") is not False:
        errors.append("l5_auto_open must remain false on L4 freeze")
    if track.get("l5_auto_open") is not False and track.get("l5_auto_open") is not None:
        errors.append("track l5_auto_open must be false")

    return AuthoritySelfCheck(
        ok=not errors,
        errors=tuple(errors),
        slice_id=SLICE_ID,
        l3_disposition=str(l3_disp),
        l4_terminal_verdict=str(l4_verdict),
        material_trials_remaining=sot_remaining,
        effective_decision_dof=dof,
    )


def require_authority_pass(repo: Path | None = None) -> AuthoritySelfCheck:
    check = authority_self_check(repo)
    if not check.ok:
        raise L5CustodyError(
            "ao_ftk_1_l5_authority_self_check_failed:" + "|".join(check.errors)
        )
    return check


# ---------------------------------------------------------------------------
# Step 1 — L5 authorization receipt
# ---------------------------------------------------------------------------


def build_l5_authorization_receipt(
    *,
    repo: Path | None = None,
    authorized_at_utc: str | None = None,
) -> dict[str, Any]:
    root = repo or default_repo_root()
    freeze = l4.load_machine_freeze(root)
    freeze_path = root / l4.MACHINE_FREEZE_REL
    identity_path = root / l4.LABEL_IDENTITY_REL
    hash_proc_path = root / l4.LABEL_HASH_PROCEDURE_REL

    return {
        "schema_version": "ao_ftk_1_l5_authorization_receipt_v1",
        "receipt_id": AUTH_RECEIPT_ID,
        "slice_id": SLICE_ID,
        "name": "FTK_L5_SENSING_FIRST_ONE_SHOT",
        "date": "2026-08-12",
        "role": "SHADOW_RESEARCH / RESEARCH_ONLY",
        "owner_decision": "L5_AUTHORIZE",
        "mode": MODE,
        "l5_authorized": True,
        "l5_auto_open": False,
        "runnable_evaluation": True,
        "science_mode": "ONE_AUTHORIZED_CHARGED_SENSING_EVALUATION",
        "authorized_phases": [
            "L5_RUN",
            "L6_LAYERED_DIAGNOSIS",
            "L7_ROADMAP_DECISION",
        ],
        "entry_phase": "L5_RUN",
        "debit_allowed": 1,
        "joins_allowed": 1,
        "evals_allowed": 1,
        "material_trial_debit": {
            "plan_id": PLAN_ID,
            "debit_units": 1,
            "before_charged": 0,
            "before_remaining": 3,
            "after_charged": 1,
            "after_remaining": 2,
        },
        "label_join": {
            "allowed": 1,
            "scope": "SENSING_TARGETS_ONLY",
            "sensing_targets": [t["target_id"] for t in SENSING_TARGETS],
            "product_clock_join": "FORBIDDEN",
            "w6_join": "FORBIDDEN",
        },
        "evaluation": {
            "allowed": 1,
            "effective_decision_dof": EFFECTIVE_DECISION_DOF,
            "operators": [INV_OPERATOR_ID, MARGIN_OPERATOR_ID],
            "routing": "DOMAIN_LIMITED_EX_ANTE",
            "threshold_grid": "FORBIDDEN",
            "operator_fit": "FORBIDDEN",
            "dof_rewrite": "FORBIDDEN",
            "feature_add": "FORBIDDEN",
            "qm_terms": "FORBIDDEN",
        },
        "outcome_open_scope": "SENSING_LABEL_JOIN_ONLY",
        "payoff_horizon": "BLOCKED_UNSET",
        "right_tail_cut": "BLOCKED_UNSET",
        "catastrophe_cut": "BLOCKED_UNSET",
        "capital_authority": False,
        "financial_alpha_evidence": 0,
        "l4_freeze": {
            "path": l4.MACHINE_FREEZE_REL.as_posix(),
            "sha256": sha256_file(freeze_path),
            "terminal_verdict": "L4_FREEZE_PASS",
            "effective_decision_dof": freeze.get("effective_decision_dof"),
            "parent_freeze_commit": freeze.get("parent_freeze_commit"),
            "l3_disposition_commit": freeze.get("l3_disposition_commit"),
        },
        "label_custody": {
            "identity_path": l4.LABEL_IDENTITY_REL.as_posix(),
            "identity_sha256": sha256_file(identity_path),
            "hash_procedure_path": l4.LABEL_HASH_PROCEDURE_REL.as_posix(),
            "hash_procedure_sha256": sha256_file(hash_proc_path),
            "LABEL_IDENTITY_FROZEN": True,
            "LABEL_HASH_PROCEDURE_FROZEN": True,
            "LABEL_BYTES_JOINED_before": False,
        },
        "prior": {
            "l3_disposition": "PASS",
            "l3_commit": "28aa0f1",
            "l4_verdict": "L4_FREEZE_PASS",
            "l4_commit": "a3350f0",
            "parent_freeze": "AO-FTK-0 @ 6832066",
        },
        "product_state": "CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED",
        "w6": "UNTOUCHED",
        "q_source_status": "Q_SOURCE_BLOCKED_TERMINAL",
        "ok_sbi_s2": "NOT_AUTHORIZED",
        "q_amendment": "AVAILABLE_UNSPENT",
        "qm_revival_in_ftk": "FORBIDDEN",
        "authorized_at_utc": authorized_at_utc or utc_now_iso(),
        "constitution": CONSTITUTION,
        "one_shot": True,
        "second_run": "FORBIDDEN",
        "redesign": "FORBIDDEN",
        "new_slice": "FORBIDDEN",
    }


# ---------------------------------------------------------------------------
# Step 2 — trial debit
# ---------------------------------------------------------------------------


def build_trial_debit_receipt(
    *,
    auth_receipt_id: str = AUTH_RECEIPT_ID,
    debited_at_utc: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "ao_ftk_1_l5_trial_debit_receipt_v1",
        "receipt_id": DEBIT_RECEIPT_ID,
        "slice_id": SLICE_ID,
        "plan_id": PLAN_ID,
        "auth_receipt_id": auth_receipt_id,
        "debit": 1,
        "debit_units": 1,
        "charged_before": 0,
        "remaining_before": 3,
        "charged_after": 1,
        "remaining_after": 2,
        "material_trials_charged_this_slice": 1,
        "material_trials_remaining": 2,
        "multi_debit": "FORBIDDEN",
        "free_threshold_grid": "FORBIDDEN",
        "uncharged_adaptive_search": "FORBIDDEN",
        "debited_at_utc": debited_at_utc or utc_now_iso(),
        "financial_alpha_evidence": 0,
        "capital_authority": False,
    }


def assert_debit_exactly_one(debit_receipt: Mapping[str, Any]) -> None:
    if int(debit_receipt.get("debit") or 0) != 1:
        raise L5FailClosedError("ao_ftk_1_l5_fail_closed:debit_must_be_exactly_1")
    if int(debit_receipt.get("charged_after") or -1) != 1:
        raise L5FailClosedError("ao_ftk_1_l5_fail_closed:charged_after_must_be_1")
    if int(debit_receipt.get("remaining_after") or -1) != 2:
        raise L5FailClosedError("ao_ftk_1_l5_fail_closed:remaining_after_must_be_2")


# ---------------------------------------------------------------------------
# Step 3 — freeze / operator hash verification
# ---------------------------------------------------------------------------


def verify_frozen_hashes(repo: Path | None = None) -> dict[str, Any]:
    root = repo or default_repo_root()
    freeze = l4.load_machine_freeze(root)
    errors: list[str] = []

    if freeze.get("effective_decision_dof") != EFFECTIVE_DECISION_DOF:
        errors.append("effective_decision_dof != 2")
    if freeze.get("silent_one_dof_collapse") != "FORBIDDEN":
        errors.append("silent_one_dof_collapse not FORBIDDEN")
    if freeze.get("third_decision_dof") != "FORBIDDEN":
        errors.append("third_decision_dof not FORBIDDEN")

    ops = freeze.get("operators") or []
    if not isinstance(ops, list) or len(ops) != 2:
        errors.append("operators length != 2")
    pin_report: list[dict[str, Any]] = []
    for op in ops:
        if not isinstance(op, dict):
            errors.append("operator not object")
            continue
        recomputed = l4.pin_operator_identity(op)
        recorded = op.get("immutability_pin")
        match = recomputed == recorded
        pin_report.append(
            {
                "operator_id": op.get("operator_id"),
                "recorded_pin": recorded,
                "recomputed_pin": recomputed,
                "match": match,
            }
        )
        if not match:
            errors.append(f"immutability_pin mismatch:{op.get('operator_id')}")
        if op.get("operator_bytes") != "FROZEN":
            errors.append(f"operator_bytes not FROZEN:{op.get('operator_id')}")

    op_ids = {op.get("operator_id") for op in ops if isinstance(op, dict)}
    if op_ids != {INV_OPERATOR_ID, MARGIN_OPERATOR_ID}:
        errors.append(f"operator_ids mismatch:{sorted(op_ids)}")

    identity = l4.load_label_identity(root)
    hash_proc = l4.load_label_hash_procedure(root)
    if identity.get("LABEL_IDENTITY_FROZEN") is not True:
        errors.append("LABEL_IDENTITY_FROZEN not true")
    if hash_proc.get("LABEL_HASH_PROCEDURE_FROZEN") is not True:
        errors.append("LABEL_HASH_PROCEDURE_FROZEN not true")
    if identity.get("slice_id") != SLICE_ID or hash_proc.get("slice_id") != SLICE_ID:
        errors.append("label custody slice_id mismatch")

    # Economic cuts must remain BLOCKED_UNSET (no post-hoc bind).
    for field in ("payoff_horizon", "right_tail_cut", "catastrophe_cut"):
        if freeze.get(field) != "BLOCKED_UNSET":
            errors.append(f"{field} not BLOCKED_UNSET")

    if freeze.get("qm_terms_forbidden") is not True:
        errors.append("qm_terms_forbidden not true")

    freeze_path = root / l4.MACHINE_FREEZE_REL
    identity_path = root / l4.LABEL_IDENTITY_REL
    hash_proc_path = root / l4.LABEL_HASH_PROCEDURE_REL

    report = {
        "ok": not errors,
        "errors": errors,
        "effective_decision_dof": freeze.get("effective_decision_dof"),
        "operator_pins": pin_report,
        "freeze_sha256": sha256_file(freeze_path),
        "label_identity_sha256": sha256_file(identity_path),
        "label_hash_procedure_sha256": sha256_file(hash_proc_path),
        "payoff_horizon": freeze.get("payoff_horizon"),
        "right_tail_cut": freeze.get("right_tail_cut"),
        "catastrophe_cut": freeze.get("catastrophe_cut"),
        "qm_terms_forbidden": freeze.get("qm_terms_forbidden"),
    }
    if errors:
        raise L5CustodyError("ao_ftk_1_l5_custody_hash_fail:" + "|".join(errors))
    return report


# ---------------------------------------------------------------------------
# Step 4 — label join (exactly once)
# ---------------------------------------------------------------------------


def _identity_content_address_payload(identity: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "pack_schema_id": identity.get("pack_schema_id"),
        "row_key_set_definition": identity.get("row_key_set_definition"),
        "sensing_target_keys": identity.get("sensing_target_keys"),
        "source_receipt_lineage": identity.get("source_receipt_lineage"),
        "slice_id": identity.get("slice_id"),
    }


def build_label_join_receipt(
    *,
    auth_receipt_id: str,
    debit_receipt_id: str,
    identity_sha256: str,
    hash_procedure_sha256: str,
    joined_manifest_sha256: str,
    joined_labels_sha256: str,
    joined_row_count: int,
    label_content_address: str,
    joined_at_utc: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "ao_ftk_1_l5_label_join_receipt_v1",
        "receipt_id": JOIN_RECEIPT_ID,
        "slice_id": SLICE_ID,
        "auth_receipt_id": auth_receipt_id,
        "debit_receipt_id": debit_receipt_id,
        "join_authorized": True,
        "join_performed": True,
        "join_count": 1,
        "LABEL_BYTES_JOINED": True,
        "outcome_inspected": True,
        "outcome_scope": "SENSING_TARGETS_ONLY",
        "sensing_targets": [t["target_id"] for t in SENSING_TARGETS],
        "horizon": "NEXT_PIT_STRUCTURED_TRANSITION",
        "product_clock_join": False,
        "w6_join": False,
        "identity_path": l4.LABEL_IDENTITY_REL.as_posix(),
        "identity_sha256_pre_join": identity_sha256,
        "hash_procedure_path": l4.LABEL_HASH_PROCEDURE_REL.as_posix(),
        "hash_procedure_sha256_pre_join": hash_procedure_sha256,
        "label_identity_content_address_sha256": label_content_address,
        "joined_manifest_path": JOINED_MANIFEST_REL.as_posix(),
        "joined_manifest_sha256": joined_manifest_sha256,
        "joined_labels_path": JOINED_LABELS_REL.as_posix(),
        "joined_labels_sha256": joined_labels_sha256,
        "joined_row_count": joined_row_count,
        "second_join": "FORBIDDEN",
        "joined_at_utc": joined_at_utc or utc_now_iso(),
        "financial_alpha_evidence": 0,
        "economic_cuts": {
            "payoff_horizon": "BLOCKED_UNSET",
            "right_tail_cut": "BLOCKED_UNSET",
            "catastrophe_cut": "BLOCKED_UNSET",
        },
    }


def assert_join_exactly_once(join_receipt: Mapping[str, Any]) -> None:
    if join_receipt.get("join_performed") is not True:
        raise L5FailClosedError("ao_ftk_1_l5_fail_closed:join_not_performed")
    if int(join_receipt.get("join_count") or 0) != 1:
        raise L5FailClosedError("ao_ftk_1_l5_fail_closed:join_count_must_be_1")
    if join_receipt.get("LABEL_BYTES_JOINED") is not True:
        raise L5FailClosedError("ao_ftk_1_l5_fail_closed:LABEL_BYTES_JOINED_not_true")


# ---------------------------------------------------------------------------
# Step 5 — one frozen sensing evaluation
# ---------------------------------------------------------------------------


def _inventory_feature_applicability(snapshot: StructuredSnapshot) -> str:
    """Classify inventory domain applicability without erasing rows."""
    rows = snapshot.by_period()
    inv_values = [row.inventory for row in rows.values()]
    rev_values = [row.total_revenue for row in rows.values()]
    inv_any = any(v is not None for v in inv_values)
    rev_any = any(v is not None and v > 0 for v in rev_values)
    if rev_any and not inv_any:
        # Services-like / non-inventory business: domain NOT_APPLICABLE, measured.
        return "NOT_APPLICABLE"
    if not rev_any and not inv_any:
        return "APPLICABLE_UNOBSERVED"
    fq0 = rows.get("FQ0")
    fq1 = rows.get("FQ-1")
    if (
        fq0 is not None
        and fq1 is not None
        and fq0.inventory is not None
        and fq1.inventory is not None
        and fq0.total_revenue is not None
        and fq0.total_revenue > 0
        and fq1.total_revenue is not None
        and fq1.total_revenue > 0
    ):
        return "APPLICABLE_OBSERVED"
    return "APPLICABLE_UNOBSERVED"


def _margin_feature_applicability(snapshot: StructuredSnapshot) -> str:
    rows = snapshot.by_period()
    fq0 = rows.get("FQ0")
    if fq0 is None:
        return "APPLICABLE_UNOBSERVED"
    if fq0.operating_income is None or fq0.total_revenue is None or fq0.total_revenue <= 0:
        return "APPLICABLE_UNOBSERVED"
    return "APPLICABLE_OBSERVED"


def _inv_delta_mean_reversion_prediction(snapshot: StructuredSnapshot) -> int | None:
    levels = _economic_levels(snapshot, INVENTORY_TARGET_ID)
    current_delta = _difference(levels.get("FQ0"), levels.get("FQ-1"))
    signed = _sign(current_delta)
    return _negate_prediction(signed)


def _margin_m1_prediction(
    m1_state: Any,
) -> int | None:
    raw = m1_state.margin_cash.prediction_direction
    return _negate_prediction(raw)


def evaluate_frozen_sensing(
    snapshots: Sequence[StructuredSnapshot],
    *,
    predecessor_period_end_by_snapshot: Mapping[tuple[str, str, str], str] | None = None,
    minimum_fold_n: int = DEFAULT_MINIMUM_FOLD_N,
    minimum_fold_coverage: float = DEFAULT_MINIMUM_FOLD_COVERAGE,
) -> dict[str, Any]:
    """Exactly one frozen 2-DOF sensing evaluation. No operator search."""

    if not snapshots:
        raise ValueError("ao_ftk_1_l5_snapshots_required")

    candidate_pairs = _adjacent_pairs(snapshots)
    if predecessor_period_end_by_snapshot is None:
        pairs = candidate_pairs
    else:
        pairs = [
            (left, right)
            for left, right in candidate_pairs
            if predecessor_period_end_by_snapshot.get(_snapshot_key(right))
            == left.fq0_period_end.isoformat()
        ]
    if not pairs:
        raise ValueError("ao_ftk_1_l5_adjacent_pairs_required")

    feature_dates = sorted({left.as_of_date.isoformat() for left, _ in pairs})
    fold_map = _temporal_fold_map(feature_dates)
    m1_states = build_low_snr_states(snapshots)

    observations: dict[str, list[TransitionObservation]] = {
        INVENTORY_TARGET_ID: [],
        MARGIN_TARGET_ID: [],
    }
    strata: dict[str, Counter[str]] = {
        INVENTORY_TARGET_ID: Counter(),
        MARGIN_TARGET_ID: Counter(),
    }
    label_rows: list[dict[str, Any]] = []

    for left, right in pairs:
        fold = fold_map[left.as_of_date.isoformat()]
        holdout = deterministic_xs_holdout(left.security_id)
        m1 = m1_states[_snapshot_key(left)]

        inv_pred = _inv_delta_mean_reversion_prediction(left)
        inv_actual = _inventory_normalization_target(left, right)
        inv_app = _inventory_feature_applicability(left)
        if inv_app == "NOT_APPLICABLE":
            inv_pred = None  # domain abstain; measured not erased
        strata[INVENTORY_TARGET_ID][inv_app] += 1
        if inv_actual is None:
            strata[INVENTORY_TARGET_ID]["TARGET_UNOBSERVED"] += 1
        if inv_pred is None and inv_app == "APPLICABLE_OBSERVED":
            strata[INVENTORY_TARGET_ID]["PREDICTION_ABSTAIN"] += 1
        if inv_pred is not None and inv_actual is not None:
            strata[INVENTORY_TARGET_ID]["EVALUABLE"] += 1

        observations[INVENTORY_TARGET_ID].append(
            TransitionObservation(
                target_id=INVENTORY_TARGET_ID,
                node_id="INVENTORY_CHANNEL_STATE",
                security_id=left.security_id,
                source_entity_id=left.source_entity_id,
                feature_as_of_date=left.as_of_date.isoformat(),
                feature_period_end=left.fq0_period_end.isoformat(),
                target_as_of_date=right.as_of_date.isoformat(),
                target_period_end=right.fq0_period_end.isoformat(),
                prediction_direction=inv_pred,
                actual_direction=inv_actual,
                xs_holdout=holdout,
                temporal_fold=fold,
            )
        )
        label_rows.append(
            {
                "security_id": left.security_id,
                "source_entity_id": left.source_entity_id,
                "decision_as_of_date": left.as_of_date.isoformat(),
                "feature_period_end": left.fq0_period_end.isoformat(),
                "target_as_of_date": right.as_of_date.isoformat(),
                "target_period_end": right.fq0_period_end.isoformat(),
                "target_id": INVENTORY_TARGET_ID,
                "operator_id": INV_OPERATOR_ID,
                "applicability_status": inv_app,
                "prediction_direction": inv_pred,
                "label_direction": inv_actual,
                "selected": inv_pred is not None and inv_app == "APPLICABLE_OBSERVED",
                "risky_weight": 1.0
                if inv_pred is not None and inv_app == "APPLICABLE_OBSERVED"
                else 0.0,
                "xs_holdout": holdout,
                "temporal_fold": fold + 1,
                "horizon": "NEXT_PIT_STRUCTURED_TRANSITION",
            }
        )

        mar_pred = _margin_m1_prediction(m1)
        mar_actual = _operating_margin_target(left, right)
        mar_app = _margin_feature_applicability(left)
        strata[MARGIN_TARGET_ID][mar_app] += 1
        if mar_actual is None:
            strata[MARGIN_TARGET_ID]["TARGET_UNOBSERVED"] += 1
        if mar_pred is None and mar_app == "APPLICABLE_OBSERVED":
            strata[MARGIN_TARGET_ID]["PREDICTION_ABSTAIN"] += 1
        if mar_pred is not None and mar_actual is not None:
            strata[MARGIN_TARGET_ID]["EVALUABLE"] += 1

        observations[MARGIN_TARGET_ID].append(
            TransitionObservation(
                target_id=MARGIN_TARGET_ID,
                node_id="MARGIN_CASH_STATE",
                security_id=left.security_id,
                source_entity_id=left.source_entity_id,
                feature_as_of_date=left.as_of_date.isoformat(),
                feature_period_end=left.fq0_period_end.isoformat(),
                target_as_of_date=right.as_of_date.isoformat(),
                target_period_end=right.fq0_period_end.isoformat(),
                prediction_direction=mar_pred,
                actual_direction=mar_actual,
                xs_holdout=holdout,
                temporal_fold=fold,
            )
        )
        label_rows.append(
            {
                "security_id": left.security_id,
                "source_entity_id": left.source_entity_id,
                "decision_as_of_date": left.as_of_date.isoformat(),
                "feature_period_end": left.fq0_period_end.isoformat(),
                "target_as_of_date": right.as_of_date.isoformat(),
                "target_period_end": right.fq0_period_end.isoformat(),
                "target_id": MARGIN_TARGET_ID,
                "operator_id": MARGIN_OPERATOR_ID,
                "applicability_status": mar_app,
                "prediction_direction": mar_pred,
                "label_direction": mar_actual,
                "selected": mar_pred is not None and mar_app == "APPLICABLE_OBSERVED",
                "risky_weight": 1.0
                if mar_pred is not None and mar_app == "APPLICABLE_OBSERVED"
                else 0.0,
                "xs_holdout": holdout,
                "temporal_fold": fold + 1,
                "horizon": "NEXT_PIT_STRUCTURED_TRANSITION",
            }
        )

    targets: dict[str, Any] = {}
    for target_meta in SENSING_TARGETS:
        tid = target_meta["target_id"]
        report = _evaluate_model_target(
            observations[tid],
            minimum_fold_n=minimum_fold_n,
            minimum_fold_coverage=minimum_fold_coverage,
        )
        targets[tid] = {
            "target_id": tid,
            "node_id": target_meta["node_id"],
            "operator_id": target_meta["operator_id"],
            "family_alias": target_meta["family_alias"],
            "horizon": target_meta["horizon"],
            "operator_report": report,
            "applicability_strata": dict(sorted(strata[tid].items())),
            "pair_count": len(observations[tid]),
            "abstention_rate": _ratio(
                sum(1 for r in observations[tid] if r.prediction_direction is None),
                len(observations[tid]),
            ),
            "missing_label_rate": _ratio(
                sum(1 for r in observations[tid] if r.actual_direction is None),
                len(observations[tid]),
            ),
        }

    inv_status = targets[INVENTORY_TARGET_ID]["operator_report"]["mechanism_status"]
    mar_status = targets[MARGIN_TARGET_ID]["operator_report"]["mechanism_status"]
    inv_pass = inv_status == "PASS"
    mar_pass = mar_status == "PASS"
    if inv_pass and mar_pass:
        surface_status = "BOTH_NODES_MEASURABLE_SIGNAL"
    elif inv_pass or mar_pass:
        surface_status = "PARTIAL_NODE_SIGNAL"
    elif inv_status == "UNOBSERVED" or mar_status == "UNOBSERVED":
        surface_status = "INSUFFICIENT_MEASUREMENT"
    else:
        surface_status = "NO_MEASURABLE_SIGNAL"

    return {
        "schema_version": "ao_ftk_1_l5_sensing_evaluation_v1",
        "run_id": RUN_ID,
        "mode": MODE,
        "slice_id": SLICE_ID,
        "evaluation_count": 1,
        "effective_decision_dof": EFFECTIVE_DECISION_DOF,
        "operators_frozen": [INV_OPERATOR_ID, MARGIN_OPERATOR_ID],
        "routing": "DOMAIN_LIMITED_EX_ANTE",
        "comparator": {
            "name": "NO_INFORMATION_BASELINE_MAJORITY_CLASS",
            "description": (
                "Directional hit-rate lift vs majority-class no-information baseline "
                "on evaluable (prediction×label) rows; fold-stable association > 0 "
                "required for mechanism PASS."
            ),
            "minimum_supporting_temporal_folds": MINIMUM_INFORMATIVE_TEMPORAL_FOLDS,
            "minimum_fold_n": minimum_fold_n,
            "minimum_fold_coverage": minimum_fold_coverage,
            "temporal_fold_count": TEMPORAL_FOLD_COUNT,
        },
        "snapshot_count": len(snapshots),
        "candidate_adjacent_transition_pair_count": len(candidate_pairs),
        "adjacent_transition_pair_count": len(pairs),
        "predecessor_period_end_gate_used": predecessor_period_end_by_snapshot is not None,
        "predecessor_gate_dropped_pair_count": len(candidate_pairs) - len(pairs),
        "security_count": len({s.security_id for s in snapshots}),
        "xs_holdout_rule": "sha256(ECONPHYSICS_S0_XS_HOLDOUT_V1|CIQSEC) mod 5 == 0",
        "xs_holdout_role": "CORROBORATION_NOT_TUNING",
        "targets": targets,
        "surface_status": surface_status,
        "inventory_mechanism_status": inv_status,
        "margin_mechanism_status": mar_status,
        "threshold_grid_performed": False,
        "operator_fit_performed": False,
        "dof_rewrite_performed": False,
        "feature_add_performed": False,
        "qm_terms_present": False,
        "economic_cuts_bound": False,
        "payoff_horizon": "BLOCKED_UNSET",
        "right_tail_cut": "BLOCKED_UNSET",
        "catastrophe_cut": "BLOCKED_UNSET",
        "market_data_access_performed": False,
        "equity_outcome_access_performed": False,
        "w6_access_performed": False,
        "selection_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": False,
        "promotion_authority": "NONE",
        "label_rows": label_rows,
    }


def _snapshot_key(snapshot: StructuredSnapshot) -> tuple[str, str, str]:
    return snapshot.security_id, snapshot.source_entity_id, snapshot.as_of_date.isoformat()


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


# ---------------------------------------------------------------------------
# Step 6 — L6 layered diagnosis
# ---------------------------------------------------------------------------


D_LAYERS = (
    "D1_CUSTODY_PIT",
    "D2_DATA_OBSERVABLE",
    "D3_MEASUREMENT_POWER",
    "D4_REPRESENTATION_SNR",
    "D5_MECHANISM_SELF_TRANSITION",
    "D6_SELECTION_ENRICHMENT",
    "D7_CONFIRMATION_TIMING",
    "D8_HOLD_EXIT_CONVEXITY",
    "D9_ECONOMICS_COST_CAPACITY",
)


def build_l6_diagnosis(
    *,
    custody_report: Mapping[str, Any],
    eval_report: Mapping[str, Any],
    auth_receipt_id: str = AUTH_RECEIPT_ID,
    debit_receipt_id: str = DEBIT_RECEIPT_ID,
    join_receipt_id: str = JOIN_RECEIPT_ID,
    run_id: str = RUN_ID,
) -> dict[str, Any]:
    table: list[dict[str, Any]] = []
    first_fail: str | None = None

    def _add(
        layer: str,
        status: str,
        *,
        notes: str,
        in_scope: bool = True,
    ) -> None:
        nonlocal first_fail
        failed = status == "FAIL"
        if failed and first_fail is None and in_scope:
            first_fail = layer
        table.append(
            {
                "layer": layer,
                "status": status,
                "in_scope_sensing_first": in_scope,
                "notes": notes,
                "stop_here": failed and first_fail == layer,
            }
        )

    # D1 custody / PIT
    if custody_report.get("ok") is True:
        _add(
            "D1_CUSTODY_PIT",
            "PASS",
            notes="Operator immutability pins match; dof=2; economic cuts BLOCKED_UNSET; no PIT rewrite.",
        )
    else:
        _add(
            "D1_CUSTODY_PIT",
            "FAIL",
            notes="Custody/hash verification failed: "
            + "; ".join(custody_report.get("errors") or []),
        )

    # D2 data observable
    pairs = int(eval_report.get("adjacent_transition_pair_count") or 0)
    snaps = int(eval_report.get("snapshot_count") or 0)
    if snaps > 0 and pairs > 0:
        _add(
            "D2_DATA_OBSERVABLE",
            "PASS",
            notes=(
                f"Admitted snapshots={snaps}, adjacent pairs={pairs}; "
                "predecessor gate enforced; missingness abstains (no row deletion)."
            ),
        )
    else:
        _add(
            "D2_DATA_OBSERVABLE",
            "FAIL",
            notes="No admitted snapshots or adjacent pairs under freeze law.",
        )

    # D3 measurement power
    inv = eval_report["targets"][INVENTORY_TARGET_ID]
    mar = eval_report["targets"][MARGIN_TARGET_ID]
    inv_od = inv["operator_report"]["overall_development"]
    mar_od = mar["operator_report"]["overall_development"]
    inv_qual = inv["operator_report"]["qualifying_temporal_fold_count"]
    mar_qual = mar["operator_report"]["qualifying_temporal_fold_count"]
    if inv_qual >= MINIMUM_INFORMATIVE_TEMPORAL_FOLDS or mar_qual >= MINIMUM_INFORMATIVE_TEMPORAL_FOLDS:
        _add(
            "D3_MEASUREMENT_POWER",
            "PASS",
            notes=(
                f"Inventory evaluable N={inv_od.get('N')} qualifying_folds={inv_qual}; "
                f"margin evaluable N={mar_od.get('N')} qualifying_folds={mar_qual}."
            ),
        )
    else:
        _add(
            "D3_MEASUREMENT_POWER",
            "FAIL",
            notes="Neither node reached minimum fold N/coverage for mechanism adjudication.",
        )

    # D4 representation SNR — continuous retained; check abstention not total
    inv_cover = inv_od.get("coverage_rate")
    mar_cover = mar_od.get("coverage_rate")
    inv_abs = inv.get("abstention_rate")
    if (inv_cover is not None and inv_cover > 0) or (mar_cover is not None and mar_cover > 0):
        _add(
            "D4_REPRESENTATION_SNR",
            "PASS",
            notes=(
                "Continuous inventory lag-1 + continuous M1 surface retained; "
                f"inventory coverage={inv_cover}, abstention={inv_abs}; "
                f"margin coverage={mar_cover}; services inventory NOT_APPLICABLE "
                f"count={inv['applicability_strata'].get('NOT_APPLICABLE', 0)} measured."
            ),
        )
    else:
        _add(
            "D4_REPRESENTATION_SNR",
            "FAIL",
            notes="Zero coverage under continuous sensing representation.",
        )

    # D5 mechanism self-transition (primary sensing question)
    inv_status = inv["operator_report"]["mechanism_status"]
    mar_status = mar["operator_report"]["mechanism_status"]
    inv_lift = inv_od.get("lift_vs_no_information_baseline")
    mar_lift = mar_od.get("lift_vs_no_information_baseline")
    inv_assoc = inv_od.get("directional_association")
    mar_assoc = mar_od.get("directional_association")
    if inv_status == "PASS" or mar_status == "PASS":
        _add(
            "D5_MECHANISM_SELF_TRANSITION",
            "PASS",
            notes=(
                f"Inventory {INV_OPERATOR_ID} status={inv_status} "
                f"lift={inv_lift} assoc={inv_assoc} "
                f"supporting_folds={inv['operator_report']['supporting_temporal_fold_count']}; "
                f"margin {MARGIN_OPERATOR_ID} status={mar_status} "
                f"lift={mar_lift} assoc={mar_assoc} "
                f"supporting_folds={mar['operator_report']['supporting_temporal_fold_count']}."
            ),
        )
    elif inv_status == "UNOBSERVED" and mar_status == "UNOBSERVED":
        _add(
            "D5_MECHANISM_SELF_TRANSITION",
            "FAIL",
            notes="Both nodes UNOBSERVED for mechanism adjudication.",
        )
    else:
        _add(
            "D5_MECHANISM_SELF_TRANSITION",
            "FAIL",
            notes=(
                f"No fold-stable next-PIT sensing signal under frozen operators "
                f"(inventory={inv_status}, margin={mar_status})."
            ),
        )

    # D6–D9 out of scope for sensing-first (no selection/hold/economics estimand)
    for layer, note in (
        (
            "D6_SELECTION_ENRICHMENT",
            "No selection estimand preregistered this turn; sensing-only.",
        ),
        (
            "D7_CONFIRMATION_TIMING",
            "No confirmation/timing estimand preregistered this turn.",
        ),
        (
            "D8_HOLD_EXIT_CONVEXITY",
            "No hold/exit estimand preregistered this turn.",
        ),
        (
            "D9_ECONOMICS_COST_CAPACITY",
            "Economic cuts remain BLOCKED_UNSET; do not bind payoff/catastrophe after peeking. F6 asymmetry catastrophe NOT_IN_SCOPE_SENSING_FIRST.",
        ),
    ):
        _add(layer, "NOT_IN_SCOPE_SENSING_FIRST", notes=note, in_scope=False)

    # Information gain
    surface = eval_report.get("surface_status")
    if first_fail is None and (inv_status == "PASS" or mar_status == "PASS"):
        failure_route = "NONE_IN_SCOPE_PASS"
        info = (
            "Relative to the prior L3/L4 representation freeze (unjoined, uncharged), "
            "this one-shot join+eval measured fold-stable next-PIT transition association "
            f"on the frozen 2-DOF surface (surface_status={surface}). "
            f"Inventory operator {INV_OPERATOR_ID}: {inv_status} "
            f"(lift={inv_lift}, assoc={inv_assoc}). "
            f"Margin operator {MARGIN_OPERATOR_ID}: {mar_status} "
            f"(lift={mar_lift}, assoc={mar_assoc}). "
            "No economic cuts were bound; financial_alpha_evidence remains 0."
        )
        next_layer_may_change = (
            "Owner may later authorize economic-cut freeze + second trial, "
            "bounded refinement, or STOP — not auto-dispatched."
        )
    elif first_fail == "D5_MECHANISM_SELF_TRANSITION":
        failure_route = "MECHANISM_FAILURE"
        info = (
            "Joined sensing labels under freeze showed no fold-stable next-PIT "
            f"association for either frozen operator (inventory={inv_status}, "
            f"margin={mar_status}). Representation was evaluable; mechanism self-transition "
            "did not survive majority temporal folds."
        )
        next_layer_may_change = (
            "Owner may STOP_TRACK, SIMPLIFY_TO_1_DOF under new freeze, or "
            "NEW_OBSERVABLE_SURFACE — not auto-dispatched."
        )
    elif first_fail in {"D1_CUSTODY_PIT"}:
        failure_route = "DATA_FAILURE"
        info = "Custody/hash failure aborted scientific interpretation."
        next_layer_may_change = "Repair custody only; do not redesign operators silently."
    elif first_fail in {"D2_DATA_OBSERVABLE", "D3_MEASUREMENT_POWER"}:
        failure_route = "INCONCLUSIVE_MEASUREMENT" if first_fail == "D3_MEASUREMENT_POWER" else "DATA_FAILURE"
        info = f"First-fail at {first_fail}; sensing question not adjudicated."
        next_layer_may_change = "Owner: repair data/power or stop."
    elif first_fail == "D4_REPRESENTATION_SNR":
        failure_route = "REPRESENTATION_FAILURE"
        info = "Continuous sensing representation produced zero coverage."
        next_layer_may_change = "Owner: representation revise under new freeze rules only."
    else:
        failure_route = "INCONCLUSIVE_MEASUREMENT"
        info = f"first_fail={first_fail}; surface_status={surface}."
        next_layer_may_change = "Owner decision required."

    return {
        "schema_version": "ao_ftk_1_l6_layered_diagnosis_v1",
        "receipt_id": L6_RECEIPT_ID,
        "slice_id": SLICE_ID,
        "mode": MODE,
        "auth_receipt_id": auth_receipt_id,
        "debit_receipt_id": debit_receipt_id,
        "join_receipt_id": join_receipt_id,
        "run_id": run_id,
        "layers": table,
        "first_fail_layer": first_fail,
        "failure_route": failure_route,
        "information_gain": {
            "summary": info,
            "surface_status": surface,
            "inventory_mechanism_status": inv_status,
            "margin_mechanism_status": mar_status,
            "inventory_lift_vs_null": inv_lift,
            "margin_lift_vs_null": mar_lift,
            "inventory_directional_association": inv_assoc,
            "margin_directional_association": mar_assoc,
            "comparator": eval_report.get("comparator"),
            "which_single_layer_may_change_next": next_layer_may_change,
            "forbidden_to_change": [
                "second evaluation without new owner auth",
                "threshold/parameter grid",
                "DOF collapse or third DOF",
                "operator/feature rewrite under same freeze",
                "post-hoc economic cut binding",
                "W6 open",
                "capital / alpha claim",
                "AO-FTK-2 autonomous open",
                "Q invention / QM revival in FTK",
            ],
        },
        "falsifiers": {
            "F1_INVENTORY_OPERATOR_UNSTABLE": "TRIGGERED"
            if inv_status in {"FAILED", "PARTIAL_SUPPORT"} and inv_status != "PASS"
            else ("NOT_TRIGGERED" if inv_status == "PASS" else inv_status),
            "F2_MARGIN_OPERATOR_UNSTABLE": "TRIGGERED"
            if mar_status in {"FAILED", "PARTIAL_SUPPORT"} and mar_status != "PASS"
            else ("NOT_TRIGGERED" if mar_status == "PASS" else mar_status),
            "F3_THRESHOLD_RESCUE_REQUIRED": "NOT_TRIGGERED_NO_GRID",
            "F4_DENOMINATOR_REWRITE": "NOT_TRIGGERED",
            "F5_QM_SMUGGLING": "NOT_TRIGGERED",
            "F6_ASYMMETRY_CATASTROPHE": "NOT_IN_SCOPE_SENSING_FIRST",
        },
        "financial_alpha_evidence": 0,
        "capital_authority": False,
        "diagnosed_at_utc": utc_now_iso(),
        "constitution": CONSTITUTION,
    }


def l6_markdown(diag: Mapping[str, Any]) -> str:
    lines = [
        "# AO-FTK-1 L6 Layered Diagnosis (Sensing-First)",
        "",
        f"**Slice:** `{diag.get('slice_id')}`  ",
        f"**Mode:** `{diag.get('mode')}`  ",
        f"**First fail:** `{diag.get('first_fail_layer')}`  ",
        f"**Failure route:** `{diag.get('failure_route')}`  ",
        f"**financial_alpha_evidence:** `{diag.get('financial_alpha_evidence')}`",
        "",
        "## D1→D9",
        "",
        "| Layer | Status | In-scope | Notes |",
        "|---|---|---|---|",
    ]
    for row in diag.get("layers") or []:
        notes = str(row.get("notes") or "").replace("|", "\\|")
        lines.append(
            f"| `{row.get('layer')}` | `{row.get('status')}` | "
            f"{row.get('in_scope_sensing_first')} | {notes} |"
        )
    ig = diag.get("information_gain") or {}
    lines.extend(
        [
            "",
            "## Information gain",
            "",
            str(ig.get("summary") or ""),
            "",
            f"**May change next (owner only):** {ig.get('which_single_layer_may_change_next')}",
            "",
            "**Forbidden to change:**",
            "",
        ]
    )
    for item in ig.get("forbidden_to_change") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Step 7 — L7 owner packet
# ---------------------------------------------------------------------------


def build_l7_owner_packet(
    *,
    l6: Mapping[str, Any],
    eval_report: Mapping[str, Any],
) -> dict[str, Any]:
    first_fail = l6.get("first_fail_layer")
    route = l6.get("failure_route")
    inv_status = eval_report.get("inventory_mechanism_status")
    mar_status = eval_report.get("margin_mechanism_status")

    if route == "NONE_IN_SCOPE_PASS":
        recommended = [
            {
                "route_id": "HOLD_EVIDENCE",
                "description": "Record sensing PASS; keep alpha_evidence=0; do not promote.",
            },
            {
                "route_id": "LATER_ECONOMIC_CUT_FREEZE_PLUS_SECOND_TRIAL",
                "description": (
                    "Owner may later freeze payoff/right-tail/catastrophe cuts and "
                    "authorize a second material trial under new binding — not this worker."
                ),
            },
            {
                "route_id": "L8_BOUNDED_REFINEMENT",
                "description": "Requires new freeze rules + remaining budget; owner only.",
            },
            {
                "route_id": "STOP_TRACK",
                "description": "Park FTK-1 with sensing evidence on record.",
            },
        ]
    elif first_fail == "D5_MECHANISM_SELF_TRANSITION":
        recommended = [
            {
                "route_id": "STOP_TRACK",
                "description": "No fold-stable sensing mechanism under freeze.",
            },
            {
                "route_id": "SIMPLIFY_TO_1_DOF",
                "description": "Owner may authorize 1-DOF refine under new freeze (not silent collapse).",
            },
            {
                "route_id": "NEW_OBSERVABLE_SURFACE",
                "description": "Owner may open a new observable surface slice.",
            },
        ]
    else:
        recommended = [
            {
                "route_id": "HOLD_EVIDENCE",
                "description": "Record diagnosis; owner selects repair or stop.",
            },
            {
                "route_id": "STOP_TRACK",
                "description": "Stop without further trial spend.",
            },
        ]

    return {
        "schema_version": "ao_ftk_1_l7_owner_packet_v1",
        "packet_id": L7_PACKET_ID,
        "slice_id": SLICE_ID,
        "mode": MODE,
        "l7_status": "WAITING_OWNER",
        "worker_selected_next_slice": False,
        "worker_did_not_select_next_slice": True,
        "l5_auth_spent": True,
        "l5_auto_open": False,
        "material_trials_charged": 1,
        "material_trials_remaining": 2,
        "label_bytes_joined": True,
        "evals_performed": 1,
        "effective_decision_dof": EFFECTIVE_DECISION_DOF,
        "first_fail_layer": first_fail,
        "failure_route": route,
        "inventory_mechanism_status": inv_status,
        "margin_mechanism_status": mar_status,
        "surface_status": eval_report.get("surface_status"),
        "financial_alpha_evidence": 0,
        "capital_authority": False,
        "payoff_horizon": "BLOCKED_UNSET",
        "right_tail_cut": "BLOCKED_UNSET",
        "catastrophe_cut": "BLOCKED_UNSET",
        "recommended_routes": recommended,
        "forbidden_autonomous": [
            "open AO-FTK-2",
            "second L5 without new owner auth",
            "promote candidate / SAW",
            "move capital",
            "bind economic cuts after peeking",
            "W6 open",
            "claim financial_alpha_evidence > 0",
        ],
        "receipts": {
            "l5_authorization": AUTH_REL.as_posix(),
            "trial_debit": DEBIT_REL.as_posix(),
            "label_join": JOIN_REL.as_posix(),
            "l5_run": RUN_REL.as_posix(),
            "l6_diagnosis": L6_REL.as_posix(),
            "l7_owner_packet": L7_REL.as_posix(),
        },
        "constitution": CONSTITUTION,
        "issued_at_utc": utc_now_iso(),
    }


# ---------------------------------------------------------------------------
# Fail-closed API for second-run / multi-debit / multi-join
# ---------------------------------------------------------------------------


_SPENT_RUN_IDS: set[str] = set()


def assert_eval_not_spent(run_id: str = RUN_ID) -> None:
    if run_id in _SPENT_RUN_IDS:
        raise L5FailClosedError(f"ao_ftk_1_l5_fail_closed:second_evaluation:{run_id}")


def mark_eval_spent(run_id: str = RUN_ID) -> None:
    if run_id in _SPENT_RUN_IDS:
        raise L5FailClosedError(f"ao_ftk_1_l5_fail_closed:second_evaluation:{run_id}")
    _SPENT_RUN_IDS.add(run_id)


def require_l5_auth(*, l5_authorized: bool, action: str) -> None:
    if l5_authorized is not True:
        raise L5FailClosedError(f"ao_ftk_1_l5_fail_closed:{action}:l5_authorized=false")


def trial_debit(
    *,
    l5_authorized: bool = False,
    debit_units: int = 1,
    already_debited: bool = False,
) -> dict[str, Any]:
    require_l5_auth(l5_authorized=l5_authorized, action="trial_debit")
    if already_debited:
        raise L5FailClosedError("ao_ftk_1_l5_fail_closed:trial_debit:already_debited")
    if debit_units != 1:
        raise L5FailClosedError(
            f"ao_ftk_1_l5_fail_closed:trial_debit:debit_units_must_be_1_got_{debit_units}"
        )
    receipt = build_trial_debit_receipt()
    assert_debit_exactly_one(receipt)
    return receipt


def label_join(
    *,
    l5_authorized: bool = False,
    join_authorized: bool = False,
    already_joined: bool = False,
) -> None:
    require_l5_auth(l5_authorized=l5_authorized, action="label_join")
    if join_authorized is not True:
        raise L5FailClosedError("ao_ftk_1_l5_fail_closed:label_join:join_authorized=false")
    if already_joined:
        raise L5FailClosedError("ao_ftk_1_l5_fail_closed:label_join:second_join_forbidden")


def evaluator_run(
    *,
    l5_authorized: bool = False,
    runnable_evaluation: bool = False,
    run_id: str = RUN_ID,
    already_run: bool = False,
) -> None:
    require_l5_auth(l5_authorized=l5_authorized, action="evaluator.run")
    if runnable_evaluation is not True:
        raise L5FailClosedError(
            "ao_ftk_1_l5_fail_closed:evaluator.run:runnable_evaluation=false"
        )
    if already_run:
        raise L5FailClosedError(
            f"ao_ftk_1_l5_fail_closed:evaluator.run:second_evaluation:{run_id}"
        )
    assert_eval_not_spent(run_id)


def run_md(run_receipt: Mapping[str, Any]) -> str:
    targets = (run_receipt.get("evaluation") or {}).get("targets") or {}
    lines = [
        "# AO-FTK-1 L5 Sensing-First Run",
        "",
        f"**Run ID:** `{run_receipt.get('run_id')}`  ",
        f"**Mode:** `{run_receipt.get('mode')}`  ",
        f"**DOF:** `{run_receipt.get('effective_decision_dof')}`  ",
        f"**Surface status:** `{(run_receipt.get('evaluation') or {}).get('surface_status')}`  ",
        f"**financial_alpha_evidence:** `{run_receipt.get('financial_alpha_evidence')}`",
        "",
        "## Targets",
        "",
    ]
    for tid, trep in targets.items():
        od = (trep.get("operator_report") or {}).get("overall_development") or {}
        lines.extend(
            [
                f"### {tid}",
                "",
                f"- operator: `{trep.get('operator_id')}`",
                f"- mechanism_status: `{(trep.get('operator_report') or {}).get('mechanism_status')}`",
                f"- N: `{od.get('N')}`",
                f"- lift_vs_null: `{od.get('lift_vs_no_information_baseline')}`",
                f"- directional_association: `{od.get('directional_association')}`",
                f"- coverage_rate: `{od.get('coverage_rate')}`",
                f"- abstention_rate: `{trep.get('abstention_rate')}`",
                f"- strata: `{trep.get('applicability_strata')}`",
                "",
            ]
        )
    lines.append("Economic cuts remain **BLOCKED_UNSET**. No capital. No alpha claim.")
    lines.append("")
    return "\n".join(lines)
