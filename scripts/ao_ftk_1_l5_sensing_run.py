"""AO-FTK-1 L5 sensing-first one-shot orchestration.

Strict ladder:
  auth self-check → L5 auth receipt → debit 1 → hash verify →
  join labels once → one frozen eval → L6 → L7 packet → SoT update → STOP

No second eval, no redesign, no capital, no alpha claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.asymmetric_opportunity_v1 import ao_ftk_1_l4_contract as l4
from research.asymmetric_opportunity_v1 import ao_ftk_1_l5_contract as l5
from research.econphysics_prebreakout_v1.contracts import build_structured_snapshots
from scripts.econphysics_prebreakout_s0_shootout import (
    _admit_rows,
    _master_map,
    _read_csv,
    _sha256,
    _transition_plan_maps,
    _validate_receipt,
)


def _load_admitted_corpus(
    root: Path,
    *,
    structured_transitions: Path,
    master: Path,
    transition_plan: Path,
) -> tuple[list[Any], dict[str, Any], dict[tuple[str, str, str], str], dict[str, Any]]:
    raw_path = structured_transitions if structured_transitions.is_absolute() else root / structured_transitions
    master_path = master if master.is_absolute() else root / master
    plan_path = transition_plan if transition_plan.is_absolute() else root / transition_plan
    receipt_path = raw_path.with_suffix(".receipt.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    _validate_receipt(raw_path, master_path, plan_path, receipt)
    master_rows = _read_csv(master_path)
    plan_rows = _read_csv(plan_path)
    raw_rows = _read_csv(raw_path)
    if len(raw_rows) != int(receipt.get("raw_grid_rows") or -1):
        raise ValueError("ao_ftk_1_l5_raw_row_count_receipt_mismatch")
    entity_to_security = _master_map(master_rows)
    expected_fq0, predecessor = _transition_plan_maps(
        plan_rows, entity_to_security=entity_to_security
    )
    receipt_sha = _sha256(receipt_path)
    admitted_rows, admission = _admit_rows(
        raw_rows,
        entity_to_security=entity_to_security,
        receipt_sha256=receipt_sha,
        expected_fq0_by_snapshot=expected_fq0,
    )
    snapshots = build_structured_snapshots(admitted_rows)
    corpus = {
        "raw_path": raw_path.as_posix(),
        "raw_sha256": _sha256(raw_path),
        "receipt_path": receipt_path.as_posix(),
        "receipt_sha256": receipt_sha,
        "master_path": master_path.as_posix(),
        "master_sha256": _sha256(master_path),
        "transition_plan_path": plan_path.as_posix(),
        "transition_plan_sha256": _sha256(plan_path),
    }
    return snapshots, admission, predecessor, corpus


def _write_joined_labels(
    root: Path,
    *,
    label_rows: list[dict[str, Any]],
    identity_sha256: str,
    hash_procedure_sha256: str,
    label_content_address: str,
    auth_receipt_id: str,
    debit_receipt_id: str,
) -> tuple[dict[str, Any], str, str]:
    custody_dir = root / l5.LABEL_CUSTODY_DIR_REL
    custody_dir.mkdir(parents=True, exist_ok=True)

    # JSONL always (hashable without parquet deps issues); parquet preferred.
    jsonl_path = root / l5.JOINED_LABELS_JSONL_REL
    if jsonl_path.exists():
        raise FileExistsError(f"ao_ftk_1_l5_output_exists:{jsonl_path}")
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in label_rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
    jsonl_sha = l5.sha256_file(jsonl_path)

    parquet_path = root / l5.JOINED_LABELS_REL
    if parquet_path.exists():
        raise FileExistsError(f"ao_ftk_1_l5_output_exists:{parquet_path}")
    frame = pd.DataFrame(label_rows)
    frame.to_parquet(parquet_path, index=False)
    parquet_sha = l5.sha256_file(parquet_path)

    manifest = {
        "schema_version": "ao_ftk_1_label_pack_joined_manifest_v1",
        "slice_id": l5.SLICE_ID,
        "LABEL_BYTES_JOINED": True,
        "join_authorized": True,
        "join_performed": True,
        "outcome_inspected": True,
        "outcome_scope": "SENSING_TARGETS_ONLY",
        "auth_receipt_id": auth_receipt_id,
        "debit_receipt_id": debit_receipt_id,
        "identity_path": l4.LABEL_IDENTITY_REL.as_posix(),
        "identity_sha256_pre_join": identity_sha256,
        "hash_procedure_path": l4.LABEL_HASH_PROCEDURE_REL.as_posix(),
        "hash_procedure_sha256_pre_join": hash_procedure_sha256,
        "label_identity_content_address_sha256": label_content_address,
        "joined_labels_parquet": l5.JOINED_LABELS_REL.as_posix(),
        "joined_labels_parquet_sha256": parquet_sha,
        "joined_labels_jsonl": l5.JOINED_LABELS_JSONL_REL.as_posix(),
        "joined_labels_jsonl_sha256": jsonl_sha,
        "joined_row_count": len(label_rows),
        "sensing_targets": [t["target_id"] for t in l5.SENSING_TARGETS],
        "economic_cuts": {
            "payoff_horizon": "BLOCKED_UNSET",
            "right_tail_cut": "BLOCKED_UNSET",
            "catastrophe_cut": "BLOCKED_UNSET",
        },
        "seal_status": "JOINED_UNDER_L5_AUTH",
    }
    manifest_sha = l5.write_json_atomic(root / l5.JOINED_MANIFEST_REL, manifest, overwrite=False)
    return manifest, manifest_sha, parquet_sha


def _patch_identity_after_join(root: Path, *, parquet_sha: str, manifest_sha: str) -> None:
    identity_path = root / l4.LABEL_IDENTITY_REL
    identity = l5.load_json(identity_path)
    identity["LABEL_BYTES_JOINED"] = True
    identity["join_authorized"] = True
    identity["join_performed"] = True
    identity["outcome_inspected"] = True
    identity["seal_status"] = "JOINED_UNDER_L5_AUTH"
    identity["joined_artifact_paths"] = {
        "development_labels_parquet": l5.JOINED_LABELS_REL.as_posix(),
        "joined_manifest": l5.JOINED_MANIFEST_REL.as_posix(),
        "development_labels_parquet_sha256": parquet_sha,
        "joined_manifest_sha256": manifest_sha,
        "note": "Joined under L5_AUTHORIZE sensing-first one-shot only.",
    }
    identity["notes"] = (
        "Identity frozen at L4. Bytes joined once under L5 auth (sensing targets only)."
    )
    l5.write_json_atomic(identity_path, identity, overwrite=True)

    proc_path = root / l4.LABEL_HASH_PROCEDURE_REL
    proc = l5.load_json(proc_path)
    proc["LABEL_BYTES_JOINED"] = True
    proc["join_authorized"] = True
    proc["join_performed"] = True
    proc["outcome_inspected"] = True
    proc["seal_name"] = "JOINED_UNDER_L5_AUTH"
    proc["seal_status"] = "JOINED_UNDER_L5_AUTH"
    proc["notes"] = (
        "Hash procedure frozen at L4. One authorized join performed at L5; second join FORBIDDEN."
    )
    l5.write_json_atomic(proc_path, proc, overwrite=True)


def _update_loop_sot(
    root: Path,
    *,
    l6: dict[str, Any],
    l7: dict[str, Any],
) -> None:
    path = root / "docs/context/research_loop_state_current.json"
    sot = l5.load_json(path)
    sot["updated_at_utc"] = "2026-08-12"
    sot["product"]["financial_alpha_evidence"] = 0
    sot["process"] = {
        **sot.get("process", {}),
        "loop_phase": "L7_ROADMAP_DECISION",
        "loop_phase_label": (
            "AO-FTK-1 L5 sensing-first complete + L6 diagnosis; waiting owner L7 decision"
        ),
        "last_completed_phase": "L6_LAYERED_DIAGNOSIS",
        "last_completed_note": (
            "AO-FTK-1-20260812 L5 one-shot: debit=1 remaining=2 labels joined; "
            f"surface={l7.get('surface_status')} first_fail={l6.get('first_fail_layer')} "
            f"route={l6.get('failure_route')}; alpha_evidence=0; L7 WAITING_OWNER"
        ),
        "next_phase": "OWNER_L7_DECISION",
        "next_phase_note": (
            "Owner selects L7 route only. No auto L5 re-run. No AO-FTK-2. "
            "Trials remaining=2. financial_alpha_evidence=0."
        ),
        "diagnosis_layer_if_any": l6.get("first_fail_layer"),
        "failure_route_if_any": l6.get("failure_route"),
        "representation_snr_gate_status": "PASS_AO_FTK_1_20260812_L5_SENSING_COMPLETE",
    }

    tracks = sot.get("active_tracks") or []
    for track in tracks:
        if track.get("track_id") == "AO-FTK-1":
            track.update(
                {
                    "status": "L5_COMPLETE_WAITING_OWNER_L7",
                    "loop_phase": "L7_ROADMAP_DECISION",
                    "worker_status": "L5_COMPLETE / WAITING_OWNER_L7",
                    "material_trials_charged_this_slice": 1,
                    "material_trials_remaining": 2,
                    "l5_authorized": True,
                    "l5_auth_spent": True,
                    "l5_auto_open": False,
                    "label_bytes_joined": True,
                    "runnable_evaluation": False,
                    "financial_alpha_evidence": 0,
                    "effective_decision_dof": 2,
                    "l5_auth_receipt": l5.AUTH_REL.as_posix(),
                    "l5_debit_receipt": l5.DEBIT_REL.as_posix(),
                    "l5_join_receipt": l5.JOIN_REL.as_posix(),
                    "l5_run_receipt": l5.RUN_REL.as_posix(),
                    "l6_receipt": l5.L6_REL.as_posix(),
                    "l7_owner_packet": l5.L7_REL.as_posix(),
                    "next": "OWNER L7 decision; no autonomous next slice; no second L5",
                }
            )
        if track.get("track_id") == "AO-FTK-0":
            track["worker_status"] = "CLOSED / NO_WORKER"
            track["next"] = (
                "CLOSED / NO_WORKER; do not reopen as worker; L3/L4/L5 successor is AO-FTK-1"
            )

    sot["next_worker_slice"] = {
        "primary": "OWNER_SELECT",
        "recommended": "L7_ROUTE_FROM_OWNER_PACKET",
        "alternatives": [
            "HOLD_EVIDENCE",
            "L8_BOUNDED_REFINEMENT",
            "SIMPLIFY_TO_1_DOF",
            "STOP_TRACK",
            "NEW_OBSERVABLE_SURFACE",
            "LATER_ECONOMIC_CUT_FREEZE_PLUS_SECOND_TRIAL",
            "PARALLEL_ONLY_CRV1_SECTOR_PAPER_CLOCK",
        ],
        "forbidden_as_next": [
            "silent second L5 without new owner authorization",
            "open AO-FTK-2 before owner L7",
            "OK-SBI-0 S2 evaluation",
            "Q/M_perp/Q+M_perp leaderboard",
            "invent Q / Rule100 bridge",
            "AO-FTK-0 outcome open / reopen as worker",
            "material trial debit without new L5 authorization",
            "claim financial_alpha_evidence > 0",
            "post-hoc economic cut binding",
            "capital open",
            "W6 open",
        ],
    }
    sot["allowed_now"] = [
        "preserve Clock #1",
        "owner select L7 route from owner packet",
        "CRV1 / Sector Rotation isolated work",
        "PAPER-0 ops at alpha_evidence=0",
        "update this state file when owner decides",
        "read L5/L6/L7 receipts",
    ]
    sot["forbidden_now"] = [
        "second L5 evaluation without new owner authorization",
        "threshold/parameter grid or DOF rewrite",
        "post-hoc economic cut binding after peeking",
        "open AO-FTK-2 before L7 owner decision",
        "OK-SBI S2 / composite trophy",
        "invent ROIC / Q_GF without admit slice",
        "W6 open",
        "claim financial_alpha_evidence > 0",
        "reopen AO-FTK-0 as worker",
        "treat L3/L4/L5 sensing as Alpha",
        "capital open",
    ]
    sot["last_l5_run"] = {
        "slice_id": l5.SLICE_ID,
        "mode": l5.MODE,
        "run_id": l5.RUN_ID,
        "material_trials_charged_this_slice": 1,
        "material_trials_remaining": 2,
        "label_bytes_joined": True,
        "evals": 1,
        "effective_decision_dof": 2,
        "financial_alpha_evidence": 0,
        "surface_status": l7.get("surface_status"),
        "receipt": l5.RUN_REL.as_posix(),
    }
    sot["last_l6_diagnosis"] = {
        "slice_id": l5.SLICE_ID,
        "first_fail_layer": l6.get("first_fail_layer"),
        "failure_route": l6.get("failure_route"),
        "financial_alpha_evidence": 0,
        "receipt": l5.L6_REL.as_posix(),
    }
    sot["last_l7_owner_packet"] = {
        "slice_id": l5.SLICE_ID,
        "l7_status": "WAITING_OWNER",
        "trials_remaining": 2,
        "l5_auth_spent": True,
        "worker_did_not_select_next_slice": True,
        "packet": l5.L7_REL.as_posix(),
    }
    # Keep last_l4_freeze historical; note L5 spent separately.
    if "last_l4_freeze" in sot:
        sot["last_l4_freeze"]["note"] = (
            "L4 freeze remains historical binding; L5 one-shot spent under separate auth receipt"
        )
    l5.write_json_atomic(path, sot, overwrite=True)


def _update_active_brief(root: Path, *, l6: dict[str, Any], l7: dict[str, Any]) -> None:
    path = root / "docs/context/ACTIVE_BRIEF"
    text = path.read_text(encoding="utf-8")
    # Replace key status lines if present; else append L5 block.
    replacements = {
        "ACTIVE_RESEARCH_SHADOW   = AO-FTK-1-20260812 / L4_FREEZE_PASS (WAIT_OWNER_L5)": (
            "ACTIVE_RESEARCH_SHADOW   = AO-FTK-1-20260812 / L5_COMPLETE_WAITING_OWNER_L7"
        ),
        "AO_FTK_1_STATUS          = L4_FREEZE_PASS / effective_dof=2 / material_trials_charged=0 / labels_unjoined / L5=false": (
            "AO_FTK_1_STATUS          = L5_COMPLETE_WAITING_OWNER_L7 / effective_dof=2 / material_trials_charged=1 remaining=2 / labels_joined / L5_auth_spent=true"
        ),
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)

    marker = "## Do now"
    l5_block = f"""## AO-FTK-1 L5/L6 status (2026-08-12)

```text
L5_AUTH               = SPENT (SENSING_FIRST one-shot)
MATERIAL_TRIALS       = charged 1 / remaining 2
LABEL_BYTES_JOINED    = true (sensing targets only; one join)
EVALS                 = 1 frozen 2-DOF sensing eval
SURFACE_STATUS        = {l7.get('surface_status')}
FIRST_FAIL_LAYER      = {l6.get('first_fail_layer')}
FAILURE_ROUTE         = {l6.get('failure_route')}
FINANCIAL_ALPHA_EVIDENCE = 0
NEXT                  = OWNER L7 decision (no auto next slice / no second L5)
RECEIPTS              = docs/context/e2e_evidence/ao_ftk_1_20260812_l5_*.json
                        + l6_layered_diagnosis + l7_owner_packet
```

"""
    if "## AO-FTK-1 L5/L6 status" not in text:
        if marker in text:
            text = text.replace(marker, l5_block + marker, 1)
        else:
            text = text + "\n" + l5_block

    # Update do-now item 4/5 if still WAIT_OWNER_L5 language
    text = text.replace(
        "**AO-FTK-1 L4 DONE** (`L4_FREEZE_PASS` → **WAIT_OWNER_L5**). Frozen: 2-DOF continuous inventory lag-1 + continuous M1; label identity + hash procedure; trial-debit plan (0 charged / 3 remaining). **L5 is NOT_AUTHORIZED.** No silent L5. No trial debit. No label join. `financial_alpha_evidence=0`.",
        "**AO-FTK-1 L5 DONE** (`L5_COMPLETE_WAITING_OWNER_L7`). One-shot sensing-first: debit 1 (remaining 2), labels joined once, one frozen 2-DOF eval, L6 first-fail complete. **No second L5.** `financial_alpha_evidence=0`.",
    )
    text = text.replace(
        "5. Owner next: **authorize L5 | hold | stop** (separate receipt required for L5).",
        "5. Owner next: **L7 route** from `ao_ftk_1_20260812_l7_owner_packet.json` (HOLD_EVIDENCE / L8 / STOP / later economic freeze). No auto L5.",
    )
    text = text.replace(
        "L5 RUN / material trial debit / label join without explicit owner L5 authorization",
        "second L5 / multi-debit / multi-join / post-hoc economic cut bind without new owner authorization",
    )
    l5.write_text_atomic(path, text, overwrite=True)


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo).resolve() if args.repo else REPO_ROOT

    # Fail closed if outputs already exist (one-shot).
    for rel in (l5.AUTH_REL, l5.DEBIT_REL, l5.JOIN_REL, l5.RUN_REL, l5.L6_REL, l5.L7_REL):
        if (root / rel).exists() and not args.allow_overwrite:
            raise FileExistsError(f"ao_ftk_1_l5_already_spent:{rel}")

    # Step 0
    check = l5.require_authority_pass(root)
    print(f"STEP0_AUTHORITY_PASS remaining={check.material_trials_remaining} dof={check.effective_decision_dof}")

    # Step 1
    auth = l5.build_l5_authorization_receipt(repo=root)
    auth_sha = l5.write_json_atomic(root / l5.AUTH_REL, auth, overwrite=args.allow_overwrite)
    print(f"STEP1_AUTH_RECEIPT sha={auth_sha[:16]}")

    # Step 2
    debit = l5.trial_debit(l5_authorized=True, debit_units=1, already_debited=False)
    debit_sha = l5.write_json_atomic(root / l5.DEBIT_REL, debit, overwrite=args.allow_overwrite)
    print(f"STEP2_DEBIT charged={debit['charged_after']} remaining={debit['remaining_after']} sha={debit_sha[:16]}")

    # Step 3
    custody = l5.verify_frozen_hashes(root)
    print(f"STEP3_CUSTODY_PASS freeze={custody['freeze_sha256'][:16]}")

    # Load corpus + evaluate (labels derived from same adjacent pairs as eval)
    snapshots, admission, predecessor, corpus = _load_admitted_corpus(
        root,
        structured_transitions=Path(args.structured_transitions),
        master=Path(args.master),
        transition_plan=Path(args.transition_plan),
    )
    print(
        f"CORPUS snapshots={len(snapshots)} admitted_sec={admission.get('admitted_security_count', 'n/a')}"
    )

    l5.evaluator_run(
        l5_authorized=True,
        runnable_evaluation=True,
        run_id=l5.RUN_ID,
        already_run=False,
    )

    eval_full = l5.evaluate_frozen_sensing(
        snapshots,
        predecessor_period_end_by_snapshot=predecessor,
        minimum_fold_n=args.minimum_fold_n,
        minimum_fold_coverage=args.minimum_fold_coverage,
    )
    label_rows = eval_full.pop("label_rows")
    l5.mark_eval_spent(l5.RUN_ID)

    # Step 4 — join once (materialize labels under frozen identity/hash)
    identity = l4.load_label_identity(root)
    identity_sha = l5.sha256_file(root / l4.LABEL_IDENTITY_REL)
    hash_proc_sha = l5.sha256_file(root / l4.LABEL_HASH_PROCEDURE_REL)
    content_addr = l5.canonical_json_sha256(l5._identity_content_address_payload(identity))

    l5.label_join(l5_authorized=True, join_authorized=True, already_joined=False)
    _manifest, manifest_sha, parquet_sha = _write_joined_labels(
        root,
        label_rows=label_rows,
        identity_sha256=identity_sha,
        hash_procedure_sha256=hash_proc_sha,
        label_content_address=content_addr,
        auth_receipt_id=l5.AUTH_RECEIPT_ID,
        debit_receipt_id=l5.DEBIT_RECEIPT_ID,
    )
    join = l5.build_label_join_receipt(
        auth_receipt_id=l5.AUTH_RECEIPT_ID,
        debit_receipt_id=l5.DEBIT_RECEIPT_ID,
        identity_sha256=identity_sha,
        hash_procedure_sha256=hash_proc_sha,
        joined_manifest_sha256=manifest_sha,
        joined_labels_sha256=parquet_sha,
        joined_row_count=len(label_rows),
        label_content_address=content_addr,
    )
    l5.assert_join_exactly_once(join)
    join_sha = l5.write_json_atomic(root / l5.JOIN_REL, join, overwrite=args.allow_overwrite)
    _patch_identity_after_join(root, parquet_sha=parquet_sha, manifest_sha=manifest_sha)
    print(f"STEP4_JOIN rows={len(label_rows)} sha={join_sha[:16]}")

    # Step 5 — immutable run receipt (metrics without label row dump)
    run_receipt = {
        "schema_version": "ao_ftk_1_l5_run_receipt_v1",
        "run_id": l5.RUN_ID,
        "slice_id": l5.SLICE_ID,
        "mode": l5.MODE,
        "name": "FTK_L5_SENSING_FIRST_ONE_SHOT",
        "auth_receipt_id": l5.AUTH_RECEIPT_ID,
        "debit_receipt_id": l5.DEBIT_RECEIPT_ID,
        "join_receipt_id": l5.JOIN_RECEIPT_ID,
        "effective_decision_dof": l5.EFFECTIVE_DECISION_DOF,
        "material_trials_charged": 1,
        "material_trials_remaining": 2,
        "label_bytes_joined": True,
        "evaluation_count": 1,
        "freeze_hashes": {
            "l4_freeze_sha256": custody["freeze_sha256"],
            "label_identity_sha256_pre_join": identity_sha,
            "label_hash_procedure_sha256_pre_join": hash_proc_sha,
            "operator_pins": custody["operator_pins"],
        },
        "join_hashes": {
            "joined_manifest_sha256": manifest_sha,
            "joined_labels_sha256": parquet_sha,
            "label_identity_content_address_sha256": content_addr,
        },
        "source_corpus": corpus,
        "admission": {
            **admission,
            "admitted_snapshot_count": len(snapshots),
            "admitted_security_count": len({s.security_id for s in snapshots}),
            "imputation_performed": False,
            "row_deletion_performed": False,
            "market_data_access_performed": False,
            "w6_access_performed": False,
            "equity_outcome_access_performed": False,
        },
        "evaluation": eval_full,
        "payoff_horizon": "BLOCKED_UNSET",
        "right_tail_cut": "BLOCKED_UNSET",
        "catastrophe_cut": "BLOCKED_UNSET",
        "financial_alpha_evidence": 0,
        "capital_authority": False,
        "promotion_authority": "NONE",
        "second_run": "FORBIDDEN",
        "constitution": l5.CONSTITUTION,
        "completed_at_utc": l5.utc_now_iso(),
    }
    run_sha = l5.write_json_atomic(root / l5.RUN_REL, run_receipt, overwrite=args.allow_overwrite)
    l5.write_text_atomic(
        root / l5.RUN_MD_REL, l5.run_md(run_receipt), overwrite=args.allow_overwrite
    )
    print(
        f"STEP5_RUN surface={eval_full['surface_status']} "
        f"inv={eval_full['inventory_mechanism_status']} "
        f"mar={eval_full['margin_mechanism_status']} sha={run_sha[:16]}"
    )

    # Step 6
    l6 = l5.build_l6_diagnosis(custody_report=custody, eval_report=eval_full)
    l6_sha = l5.write_json_atomic(root / l5.L6_REL, l6, overwrite=args.allow_overwrite)
    l5.write_text_atomic(
        root / l5.L6_MD_REL, l5.l6_markdown(l6), overwrite=args.allow_overwrite
    )
    print(
        f"STEP6_L6 first_fail={l6['first_fail_layer']} route={l6['failure_route']} sha={l6_sha[:16]}"
    )

    # Step 7
    l7 = l5.build_l7_owner_packet(l6=l6, eval_report=eval_full)
    l7_sha = l5.write_json_atomic(root / l5.L7_REL, l7, overwrite=args.allow_overwrite)
    print(f"STEP7_L7 WAITING_OWNER routes={len(l7['recommended_routes'])} sha={l7_sha[:16]}")

    # Step 8
    _update_loop_sot(root, l6=l6, l7=l7)
    _update_active_brief(root, l6=l6, l7=l7)
    print("STEP8_SOT_UPDATED loop_phase=L7_ROADMAP_DECISION")

    return {
        "auth": auth,
        "debit": debit,
        "join": join,
        "run": run_receipt,
        "l6": l6,
        "l7": l7,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(REPO_ROOT))
    parser.add_argument(
        "--structured-transitions",
        default=str(l5.DEFAULT_STRUCTURED_TRANSITIONS),
    )
    parser.add_argument("--master", default=str(l5.DEFAULT_MASTER))
    parser.add_argument("--transition-plan", default=str(l5.DEFAULT_TRANSITION_PLAN))
    parser.add_argument("--minimum-fold-n", type=int, default=30)
    parser.add_argument("--minimum-fold-coverage", type=float, default=0.20)
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Dangerous: allow overwrite of one-shot receipts (tests only).",
    )
    args = parser.parse_args()
    payload = run(args)
    l6 = payload["l6"]
    l7 = payload["l7"]
    print(
        "AO_FTK_1_L5_COMPLETE"
        f"\tCHARGED=1"
        f"\tREMAINING=2"
        f"\tFIRST_FAIL={l6.get('first_fail_layer')}"
        f"\tROUTE={l6.get('failure_route')}"
        f"\tSURFACE={l7.get('surface_status')}"
        f"\tALPHA=0"
        f"\tL7=WAITING_OWNER"
    )


if __name__ == "__main__":
    main()
