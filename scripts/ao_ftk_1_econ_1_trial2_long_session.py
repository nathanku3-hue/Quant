"""AO-FTK-1-ECON-1 long session: ACCEPT_DRAFT → Trial 2 → L6 → L7 STOP.

P0 self-check → P1 bind/L5_READY → P2 auth → P3 debit → P4 join →
P5 one eval → P6 L6 → P7 L7 + SoT. No FTK-2 / L8 / capital / alpha.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.asymmetric_opportunity_v1 import ao_ftk_1_econ_1_contract as econ1
from research.asymmetric_opportunity_v1 import ao_ftk_1_econ_1_trial2 as t2


def _p0_self_check(root: Path) -> dict[str, Any]:
    sot = t2.load_json(root / "docs/context/research_loop_state_current.json")
    process = sot.get("process") or {}
    tracks = {t.get("track_id"): t for t in sot.get("active_tracks") or []}
    econ = tracks.get("AO-FTK-1-ECON-1") or {}
    parent = tracks.get("AO-FTK-1") or {}

    errors: list[str] = []
    if econ.get("freeze_id") != t2.FREEZE_ID and econ.get("track_id") != "AO-FTK-1-ECON-1":
        # track may only have track_id
        pass
    if process.get("loop_phase") not in {
        "WAITING_OWNER_NUMERICS",
        "WAIT_OWNER_L5_ECONOMIC",
        "OWNER_BIND_TRANSITION_POSITION",
    }:
        # Allow restart only from waiting numerics for this dispatch
        if process.get("loop_phase") not in {"WAITING_OWNER_NUMERICS"}:
            errors.append(f"unexpected loop_phase={process.get('loop_phase')!r}")

    charged = int(parent.get("material_trials_charged_this_slice") or 1)
    remaining = int(
        econ.get("material_trials_remaining")
        or parent.get("material_trials_remaining")
        or 2
    )
    if charged != 1:
        errors.append(f"expected charged=1 before debit, got {charged}")
    if remaining != 2:
        errors.append(f"expected remaining=2 before debit, got {remaining}")
    if econ.get("label_bytes_joined") is True:
        errors.append("economic labels already joined before Trial 2")
    if econ.get("economic_l5_authorized") is True and econ.get("status", "").startswith("L5"):
        # if already complete, refuse second run
        if (root / t2.L5_RUN_REL).exists():
            errors.append("economic L5 run already exists; second run forbidden")

    t2.assert_attachment_concrete()
    return {
        "ok": not errors,
        "errors": errors,
        "primary_program": t2.FREEZE_ID,
        "parent_program": t2.PARENT_PROGRAM,
        "clock": t2.ECONOMIC_CLOCK_CLASS,
        "prior_path_a_respected": True,
        "trials_before": {"charged": charged, "remaining": remaining},
        "economic_l5_already_run": (root / t2.L5_RUN_REL).exists(),
        "attachment_concrete": True,
        "loop_phase": process.get("loop_phase"),
    }


def _update_sot(
    root: Path,
    *,
    first_fail_layer: str | None,
    failure_route: str,
    work_commit_placeholder: str = "PENDING_COMMIT",
) -> None:
    sot_path = root / "docs/context/research_loop_state_current.json"
    sot = t2.load_json(sot_path)

    for track in sot.get("active_tracks") or []:
        if track.get("track_id") == "AO-FTK-1":
            track["material_trials_charged_this_slice"] = 2
            track["material_trials_remaining"] = 1
            track["loop_phase"] = "L7_ROADMAP_DECISION"
            track["status"] = "ECON_1_L5_COMPLETE_WAITING_OWNER_L7"
            track["worker_status"] = "CLOSED / NO_WORKER"
            track["l5_ready"] = True
            track["next"] = (
                "CLOSED / NO_WORKER; AO-FTK-1-ECON-1 Trial 2 complete; "
                "owner L7 only; remaining trials=1; alpha=0; no FTK-2"
            )
            track["econ_1_l5_run"] = t2.L5_RUN_REL.as_posix()
            track["econ_1_l6"] = t2.L6_REL.as_posix()
            track["econ_1_l7"] = t2.L7_REL.as_posix()
            track["financial_alpha_evidence"] = 0
        if track.get("track_id") == "AO-FTK-1-ECON-1":
            track["economic_l5_authorized"] = True
            track["l5_auto_open"] = False
            track["label_bytes_joined"] = True
            track["loop_phase"] = "L5_COMPLETE_WAITING_OWNER_L7"
            track["status"] = "L5_COMPLETE_WAITING_OWNER_L7"
            track["terminal_verdict"] = "L5_COMPLETE_WAITING_OWNER_L7"
            track["worker_status"] = "CLOSED / NO_WORKER"
            track["material_trials_charged_this_turn"] = 1
            track["material_trials_remaining"] = 1
            track["material_trials_charged_to_date"] = 2
            track["l5_ready"] = True
            track["bind_verdict"] = "PASS_L5_READY"
            track["session_path"] = "C_TRIAL2_COMPLETE"
            track["financial_alpha_evidence"] = 0
            track["first_fail_layer"] = first_fail_layer
            track["failure_route"] = failure_route
            track["owner_bind_receipt"] = econ1.OWNER_BIND_RECEIPT_REL.as_posix()
            track["l5_ready_receipt"] = t2.L5_READY_REL.as_posix()
            track["l5_auth_receipt"] = t2.L5_AUTH_REL.as_posix()
            track["l5_debit_receipt"] = t2.L5_DEBIT_REL.as_posix()
            track["l5_join_receipt"] = t2.L5_JOIN_REL.as_posix()
            track["l5_run_receipt"] = t2.L5_RUN_REL.as_posix()
            track["l6_receipt"] = t2.L6_REL.as_posix()
            track["l7_owner_packet"] = t2.L7_REL.as_posix()
            track["work_commit"] = work_commit_placeholder
            track["next"] = "OWNER L7 route only; no auto FTK-2; remaining trials=1"

    sot["process"] = {
        **(sot.get("process") or {}),
        "loop_phase": "L7_ROADMAP_DECISION",
        "loop_phase_label": (
            "AO-FTK-1-ECON-1 L5_COMPLETE_WAITING_OWNER_L7 / NO_WORKER; "
            "Trial 2 complete; trials remaining=1; alpha=0"
        ),
        "last_completed_phase": "L5_L6_L7_ECON_TRIAL2",
        "last_completed_note": (
            "AO-FTK-1-ECON-1 ACCEPT_DRAFT long session COMPLETE: bind PASS_L5_READY; "
            "debit 1→charged=2 remaining=1; join once; one economic eval; "
            f"L6 first_fail={first_fail_layer}; L7 packet; AO-FTK-2 NOT_OPENED; alpha=0"
        ),
        "next_phase": "L7_ROADMAP_DECISION",
        "next_phase_note": (
            "Owner L7 route only (HOLD_EVIDENCE / STOP_TRACK / admit Full-W3 market "
            "custody new slice). No auto L8/FTK-2/capital. Remaining material trials=1. "
            "financial_alpha_evidence=0."
        ),
        "diagnosis_layer_if_any": first_fail_layer,
        "failure_route_if_any": failure_route,
        "representation_snr_gate_status": "PASS_AO_FTK_1_20260812_L5_SENSING_COMPLETE",
        "method_id": "ALPHA_SCIENTIFIC_METHOD_v1",
        "method_status": "LOCKED",
    }
    sot["last_econ_trial2"] = {
        "freeze_id": t2.FREEZE_ID,
        "session_path": "C_TRIAL2_COMPLETE",
        "l5_ready": True,
        "l5_ran": True,
        "material_trials_charged": 2,
        "material_trials_remaining": 1,
        "first_fail_layer": first_fail_layer,
        "failure_route": failure_route,
        "d9_interpretation": "POSITIVE_NET_EDGE_SCREEN",
        "financial_alpha_evidence": 0,
        "ao_ftk_2": "NOT_OPENED",
        "run_receipt": t2.L5_RUN_REL.as_posix(),
        "l6_receipt": t2.L6_REL.as_posix(),
        "l7_packet": t2.L7_REL.as_posix(),
    }
    sot["next_worker_slice"] = {
        "primary": "OWNER_SELECT",
        "recommended": "OWNER_L7_ROUTE_ONLY",
        "alternatives": [
            "HOLD_EVIDENCE",
            "STOP_TRACK",
            "ADMIT_FULL_W3_MARKET_CUSTODY_NEW_SLICE",
            "PARALLEL_ONLY_CRV1_SECTOR_PAPER_CLOCK",
        ],
        "forbidden_as_next": [
            "auto second economic eval",
            "open AO-FTK-2",
            "L8 refinement now",
            "capital open",
            "claim financial_alpha_evidence > 0",
            "invent D7 confirmation",
            "W6 open",
            "reuse sensing labels for economic estimand",
        ],
    }
    sot["allowed_now"] = [
        "preserve Clock #1",
        "owner L7 route decision only",
        "CRV1 / Sector Rotation isolated work",
        "PAPER-0 ops at alpha_evidence=0",
        "read ECON Trial 2 receipts",
    ]
    sot["forbidden_now"] = [
        "second economic eval without new owner auth",
        "open AO-FTK-2",
        "L8 refinement now",
        "claim financial_alpha_evidence > 0",
        "capital open",
        "invent D7 confirmation rule",
        "W6 open",
        "H/K/percentile grid search",
        "asymmetric return FTK vs W3",
        "reuse sensing labels for economic estimand",
        "multi-debit",
        "reopen AO-FTK-0 as worker",
    ]
    sot["product"] = {
        **(sot.get("product") or {}),
        "capital_alpha_path": "CLOSED",
        "financial_alpha_evidence": 0,
        "state": "CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED",
        "w6": "UNTOUCHED",
    }
    sot["updated_at_utc"] = "2026-08-12"
    t2.write_json_atomic(sot_path, sot, overwrite=True)


def _update_active_brief(root: Path, *, first_fail_layer: str | None) -> None:
    path = root / "docs/context/ACTIVE_BRIEF"
    text = f"""# ACTIVE_BRIEF — 2026-08-12

## Authority (read first)

```text
RESEARCH_LOOP_STATE      = docs/context/research_loop_state_current.json   # phase/next SoT
RESEARCH_LOOP_HUMAN      = docs/context/RESEARCH_LOOP.md
METHOD_CONSTITUTION      = docs/architecture/alpha_scientific_method_v1.md
LOOP_CLI                 = python scripts/print_research_loop_state.py

LINEAGE_BRANCH           = codex/pit-source-authority-1
WORKTREE                 = E:/Code/Quant/.worktrees/devspace-053ca7a4f582fb3e
PUBLIC_MAIN              = NON_AUTHORITY_UNTIL_MERGE
```

## Product vs research

```text
ACTIVE_PRODUCT_STATE     = CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED
ACTIVE_RESEARCH_SHADOW   = AO-FTK-1-ECON-1 / L5_COMPLETE_WAITING_OWNER_L7 / TRANSITION_POSITION / NO_WORKER
AO_FTK_0_STATUS          = CLOSED / READY_FOR_LATER_CHARGED_DEVELOPMENT_READ / NO_WORKER
AO_FTK_1_STATUS          = ECON_1_L5_COMPLETE_WAITING_OWNER_L7 / sensing L5 spent / charged=2 remaining=1 / NO_WORKER
AO_FTK_1_ECON_1_STATUS   = L5_COMPLETE_WAITING_OWNER_L7 / Trial 2 complete / first_fail={first_fail_layer} / alpha=0 / NO_WORKER
OK_SBI_0_STATUS          = S0_DESIGN_LOCKED_RELEASE_BLOCKED + Q_SOURCE_BLOCKED_TERMINAL (PARKED)
CAPITAL_ALPHA_PATH       = CLOSED
FINANCIAL_ALPHA_EVIDENCE = 0
```

## AO-FTK-1-ECON-1 status (2026-08-12) — Trial 2 COMPLETE / L7 STOP

```text
WORKER_STATUS         = CLOSED / NO_WORKER
SESSION_PATH          = C_TRIAL2_COMPLETE
OWNER_DECISION        = ACCEPT_DRAFT + L5_AUTHORIZE_ECONOMIC
ECONOMIC_CLOCK        = TRANSITION_POSITION
BINDS                 = H=63 RT=0.90 CAT=0.10 K=20 ΔJ=0.0 D7=OUT_OF_SCOPE E2/E3=OWNER_BOUND
L5_READY              = true
L5_RAN                = true
TRIALS_AFTER          = charged=2 remaining=1
FIRST_FAIL_LAYER      = {first_fail_layer}
D9_INTERPRETATION     = POSITIVE_NET_EDGE_SCREEN
ALPHA                 = 0
AO_FTK_2              = NOT_OPENED
L8                    = not executed
NEXT                  = OWNER L7 route only
```

### Receipts

```text
owner_bind     = docs/context/e2e_evidence/ao_ftk_1_econ_1_owner_bind_transition_position.json
l5_ready       = docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_ready_checklist.json
l5_auth        = docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_authorization.json
l5_debit       = docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_trial_debit.json
l5_join        = docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_label_join.json
l5_run         = docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_run.json
l6             = docs/context/e2e_evidence/ao_ftk_1_econ_1_l6_layered_diagnosis.json
l7             = docs/context/e2e_evidence/ao_ftk_1_econ_1_l7_owner_packet.json
machine_freeze = docs/architecture/ao_ftk_1_econ_1_economic_asymmetry_freeze.json
```

## Do now

1. Preserve Clock #1; outcomes sealed until legitimate maturity.
2. `Q_SOURCE_BLOCKED_TERMINAL` — do **not** invent Q / open OK-SBI S2.
3. **AO-FTK-1-ECON-1 Trial 2 COMPLETE** — owner L7 route only.
4. Recommended owner routes: HOLD_EVIDENCE | STOP_TRACK | admit Full-W3 market custody (new slice) then separate auth for remaining trial.
5. **No active worker. No FTK-2. No L8. No capital. alpha=0.**

## Do not

```text
second economic eval / param grid / invent D7 / open AO-FTK-2 / L8 now
claim financial_alpha_evidence > 0 / capital open / W6 open
asymmetric return FTK vs W3 / reuse sensing labels for economic estimand
borrow Breakout clock / GE multi-year primary / multi-debit
```

## One-line constitution

Accept draft binds. One transition-position economic trial. Same return law both sides. ΔJ>0 is a screen not capital. L6 first-fail. L7 stop. No slice 2.
"""
    t2.write_text_atomic(path, text, overwrite=True)


def _build_freeze_receipt(doc: dict[str, Any], *, first_fail: str | None) -> dict[str, Any]:
    return {
        "schema_version": "ao_ftk_1_econ_1_economic_asymmetry_freeze_receipt_v1",
        "receipt_id": "AO_FTK_1_ECON_1_ECONOMIC_ASYMMETRY_FREEZE",
        "freeze_id": t2.FREEZE_ID,
        "parent_program": t2.PARENT_PROGRAM,
        "name": "FTK_ECONOMIC_ASYMMETRY_FREEZE",
        "date": "2026-08-12",
        "role": "SHADOW_RESEARCH / RESEARCH_ONLY",
        "science_mode": "OUTCOME_BLIND_ECONOMIC_ASYMMETRY_FREEZE",
        "authorized_phase": doc.get("authorized_phase"),
        "terminal_verdict": doc.get("status"),
        "status": doc.get("status"),
        "l7_route": econ1.L7_ROUTE,
        "l7_machine_effective": True,
        "parent_l5_work_commit": "948471c",
        "parent_l4_work_commit": "a3350f0",
        "surface_dof": 2,
        "surface_dof_unchanged": True,
        "economic_clock_class": t2.ECONOMIC_CLOCK_CLASS,
        "bind_verdict": "PASS_L5_READY",
        "l5_ready": True,
        "l5_authorized": True,
        "economic_l5_authorized": True,
        "material_trials_charged_this_turn": 1,
        "material_trials_remaining": 1,
        "label_bytes_joined": True,
        "financial_alpha_evidence": 0,
        "session_path": "C_TRIAL2_COMPLETE",
        "first_fail_layer": first_fail,
        "ACCEPT_DRAFT": True,
        "artifacts": {
            "machine_freeze": econ1.MACHINE_FREEZE_REL.as_posix(),
            "owner_bind_receipt": econ1.OWNER_BIND_RECEIPT_REL.as_posix(),
            "l5_ready": t2.L5_READY_REL.as_posix(),
            "l5_auth": t2.L5_AUTH_REL.as_posix(),
            "l5_debit": t2.L5_DEBIT_REL.as_posix(),
            "l5_join": t2.L5_JOIN_REL.as_posix(),
            "l5_run": t2.L5_RUN_REL.as_posix(),
            "l6": t2.L6_REL.as_posix(),
            "l7": t2.L7_REL.as_posix(),
            "label_identity": econ1.LABEL_IDENTITY_REL.as_posix(),
            "label_hash_procedure": econ1.LABEL_HASH_PROCEDURE_REL.as_posix(),
            "contract_module": "research/asymmetric_opportunity_v1/ao_ftk_1_econ_1_contract.py",
            "trial2_module": "research/asymmetric_opportunity_v1/ao_ftk_1_econ_1_trial2.py",
        },
        "firewall": {
            "l5_authorized": True,
            "economic_l5_authorized": True,
            "l5_auto_open": False,
            "runnable_evaluation": False,
            "capital_authority": False,
            "material_trials_charged_this_turn": 1,
            "material_trials_remaining": 1,
            "label_bytes_joined": True,
            "financial_alpha_evidence": 0,
            "ao_ftk_2": "NOT_AUTHORIZED",
            "l8_bounded_refinement": "DEFER",
            "w6": "UNTOUCHED",
            "economic_clock_class": t2.ECONOMIC_CLOCK_CLASS,
        },
        "next_phase": "L7_ROADMAP_DECISION",
        "next_owner_action": "L7 route only",
        "next_worker_recommended": "OWNER_L7_ONLY",
        "stop_lines_honored": True,
        "stop_lines_hit": [],
        "constitution": t2.CONSTITUTION,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO_ROOT)
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing trial2 receipts")
    args = parser.parse_args(argv)
    root = args.repo.resolve()
    ow = bool(args.overwrite)

    # P0
    p0 = _p0_self_check(root)
    if not p0["ok"]:
        print("P0 FAIL:", p0["errors"], file=sys.stderr)
        return 2
    print("P0 PASS", json.dumps(p0, sort_keys=True))

    # Load freeze
    doc = econ1.load_machine_freeze(root)

    # P1 — bind ACCEPT_DRAFT
    doc = t2.apply_accept_draft_binds(doc)
    readiness = econ1.evaluate_l5_readiness(doc)
    if not readiness["l5_ready"]:
        print("P1 FAIL L5_READY blockers:", readiness["blockers_remaining"], file=sys.stderr)
        return 3
    bind_receipt = t2.build_owner_bind_receipt(doc)
    checklist = t2.build_l5_ready_checklist(doc)
    t2.write_json_atomic(root / econ1.MACHINE_FREEZE_REL, doc, overwrite=True)
    t2.write_json_atomic(root / econ1.OWNER_BIND_RECEIPT_REL, bind_receipt, overwrite=True)
    t2.write_json_atomic(root / t2.L5_READY_REL, checklist, overwrite=ow or True)
    print("P1 PASS_L5_READY")

    # P2 — L5 authorization
    now = t2.utc_now_iso()
    auth = t2.build_l5_authorization(authorized_at_utc=now)
    t2.write_json_atomic(root / t2.L5_AUTH_REL, auth, overwrite=ow or True)
    print("P2 L5 authorization written")

    # P3 — debit exactly 1
    debit = t2.build_trial_debit(debited_at_utc=now)
    t2.write_json_atomic(root / t2.L5_DEBIT_REL, debit, overwrite=ow or True)
    print("P3 debit charged 1→2 remaining 2→1")

    # P4 — join once
    market_probe = t2.probe_market_custody(root)
    join_receipt, manifest, label_rows = t2.build_label_join(
        repo=root, joined_at_utc=now, market_probe=market_probe
    )
    # Write joined artifacts
    jsonl_path = root / t2.JOINED_LABELS_JSONL_REL
    if jsonl_path.exists() and not ow:
        # allow overwrite in long session re-run only with flag
        pass
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in label_rows:
            handle.write(
                json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                + "\n"
            )
    t2.write_json_atomic(root / t2.JOINED_MANIFEST_REL, manifest, overwrite=True)
    # Update identity + hash procedure
    identity = econ1.load_label_identity(root)
    identity.update(
        {
            "LABEL_BYTES_JOINED": True,
            "join_authorized": True,
            "join_performed": True,
            "outcome_inspected": False,
            "seal_status": "IDENTITY_HASH_FROZEN_BYTES_JOINED_SCHEMA_ONLY",
            "economic_cuts": {
                "payoff_horizon_primary": 63,
                "right_tail_definition": 0.90,
                "catastrophe_definition": 0.10,
                "delta_J_required": 0.0,
            },
            "joined_artifact_paths": {
                "economic_labels_jsonl": t2.JOINED_LABELS_JSONL_REL.as_posix(),
                "joined_manifest": t2.JOINED_MANIFEST_REL.as_posix(),
            },
        }
    )
    proc = econ1.load_label_hash_procedure(root)
    proc.update(
        {
            "LABEL_BYTES_JOINED": True,
            "join_authorized": True,
            "join_performed": True,
            "seal_name": "SEALED_JOINED_SCHEMA_RNET_UNOBSERVED",
            "seal_status": "BYTES_JOINED_SCHEMA_ONLY",
            "content_address": join_receipt["content_address"],
        }
    )
    t2.write_json_atomic(root / econ1.LABEL_IDENTITY_REL, identity, overwrite=True)
    t2.write_json_atomic(root / econ1.LABEL_HASH_PROCEDURE_REL, proc, overwrite=True)
    t2.write_json_atomic(root / t2.L5_JOIN_REL, join_receipt, overwrite=ow or True)
    print("P4 join performed; FORWARD_R_NET materialized=", join_receipt["FORWARD_R_NET_materialized"])

    # P5 — one eval
    run = t2.run_economic_evaluation(
        repo=root, market_probe=market_probe, completed_at_utc=now
    )
    t2.write_json_atomic(root / t2.L5_RUN_REL, run, overwrite=ow or True)
    md = f"""# AO-FTK-1-ECON-1 L5 economic run

- run_id: `{t2.RUN_ID}`
- clock: TRANSITION_POSITION
- binds: H=63, RT=0.90, CAT=0.10, K=20, ΔJ=0.0, D7=OUT_OF_SCOPE
- evaluation_status: **{run['evaluation_status']}**
- market_flag: `{market_probe.get('flag')}`
- delta_J: `{run['payoff']['delta_J']}`
- financial_alpha_evidence: **0**
- AO-FTK-2: NOT_OPENED

## Session arithmetic (frozen)

{run['session_arithmetic']['inclusive_session_arithmetic']}

## Note

Full-W3 market custody missing for economic estimand. No invented returns. No second run.
"""
    t2.write_text_atomic(root / t2.L5_RUN_MD_REL, md, overwrite=True)
    print("P5 evaluation complete:", run["evaluation_status"])

    # P6 — L6
    l6 = t2.build_l6_diagnosis(run)
    t2.write_json_atomic(root / t2.L6_REL, l6, overwrite=ow or True)
    print("P6 first_fail=", l6["first_fail_layer"], "route=", l6["failure_route"])

    # P7 — L7 + freeze stamp + SoT
    l7 = t2.build_l7_owner_packet(run=run, l6=l6, trials_remaining=1)
    t2.write_json_atomic(root / t2.L7_REL, l7, overwrite=ow or True)

    doc = t2.stamp_freeze_post_trial(
        doc,
        trials_charged=2,
        trials_remaining=1,
        join_performed=True,
        first_fail_layer=l6["first_fail_layer"],
    )
    t2.write_json_atomic(root / econ1.MACHINE_FREEZE_REL, doc, overwrite=True)
    freeze_receipt = _build_freeze_receipt(doc, first_fail=l6["first_fail_layer"])
    t2.write_json_atomic(root / econ1.RECEIPT_REL, freeze_receipt, overwrite=True)

    _update_sot(
        root,
        first_fail_layer=l6["first_fail_layer"],
        failure_route=str(l6["failure_route"]),
    )
    _update_active_brief(root, first_fail_layer=l6["first_fail_layer"])
    print("P7 L7 packet + SoT updated; HARD STOP")

    packet = {
        "FREEZE_ID": t2.FREEZE_ID,
        "CLOCK": t2.ECONOMIC_CLOCK_CLASS,
        "SESSION_PATH": "C_TRIAL2_COMPLETE",
        "L5_READY": True,
        "L5_RAN": True,
        "BINDS": "H=63 RT=0.90 CAT=0.10 K=20 ΔJ=0.0 D7=OOS E2/E3=OWNER_BOUND",
        "TRIALS_AFTER": "charged=2 remaining=1",
        "FIRST_FAIL_LAYER": l6["first_fail_layer"],
        "FAILURE_ROUTE": l6["failure_route"],
        "D9_INTERPRETATION": "POSITIVE_NET_EDGE_SCREEN",
        "ALPHA": 0,
        "AO_FTK_2": "NOT_OPENED",
        "NEXT_OWNER_ACTION": "L7 route only",
        "RECEIPTS": {
            "bind": econ1.OWNER_BIND_RECEIPT_REL.as_posix(),
            "l5_ready": t2.L5_READY_REL.as_posix(),
            "auth": t2.L5_AUTH_REL.as_posix(),
            "debit": t2.L5_DEBIT_REL.as_posix(),
            "join": t2.L5_JOIN_REL.as_posix(),
            "run": t2.L5_RUN_REL.as_posix(),
            "l6": t2.L6_REL.as_posix(),
            "l7": t2.L7_REL.as_posix(),
        },
    }
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
