"""AO-FTK-1-ECON-1 final economic trial orchestration.

P0 self-check → P1 D2 re-preflight → (if GREEN) P2 auth → P3 debit →
P4 economic join → P5 one eval → P6 L6 → P7 L7 + SoT → HARD STOP.

Never debit before D2 GREEN. No FTK-2 / L8 / capital / alpha claim.
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

from research.asymmetric_opportunity_v1 import ao_ftk_1_econ_1_final_trial as ft
from research.econphysics_prebreakout_v1.contracts import build_structured_snapshots
from scripts.econphysics_prebreakout_s0_shootout import (
    _admit_rows,
    _master_map,
    _read_csv,
    _sha256,
    _transition_plan_maps,
    _validate_receipt,
)


def _p0_self_check(root: Path) -> dict[str, Any]:
    sot = ft.load_json(root / "docs/context/research_loop_state_current.json")
    process = sot.get("process") or {}
    tracks = {t.get("track_id"): t for t in sot.get("active_tracks") or []}
    econ = tracks.get("AO-FTK-1-ECON-1") or {}
    parent = tracks.get("AO-FTK-1") or {}
    errors: list[str] = []

    if process.get("loop_phase") not in {
        "WAIT_OWNER_L5_ECONOMIC_FINAL",
        "W3_MKT_ADMITTED_D2_GREEN_WAIT_OWNER_L5",
    }:
        # allow if econ track is waiting owner L5 final
        if econ.get("status") not in {
            "W3_MKT_ADMIT_PASS_D2_GREEN",
            "W3_MKT_ADMITTED_D2_GREEN_WAIT_OWNER_L5",
        } and process.get("next_phase") not in {
            "WAIT_OWNER_L5_ECONOMIC_FINAL",
        }:
            errors.append(f"unexpected loop_phase={process.get('loop_phase')!r}")

    remaining = int(
        econ.get("material_trials_remaining")
        or parent.get("material_trials_remaining")
        or 0
    )
    charged = int(
        parent.get("material_trials_charged_this_slice")
        or econ.get("material_trials_charged_to_date")
        or 2
    )
    if remaining != 1:
        errors.append(f"expected remaining=1, got {remaining}")
    if charged != 2:
        errors.append(f"expected charged=2, got {charged}")

    if not (root / ft.W3_ADMIT_REL).is_file():
        errors.append("missing W3 admit receipt")
    if not (root / ft.W3_D2_PRIOR_REL).is_file():
        errors.append("missing prior D2 preflight")
    if (root / ft.RUN_REL).exists():
        errors.append("final economic run already exists; second eval forbidden")

    w3 = tracks.get("AO-FTK-1-ECON-1") or {}
    if w3.get("w3_mkt_work_commit") not in (None, ft.W3_ADMIT_COMMIT) and w3.get(
        "w3_mkt_work_commit"
    ) != ft.W3_ADMIT_COMMIT:
        # soft check — prefer exact
        if str(w3.get("w3_mkt_work_commit")) != ft.W3_ADMIT_COMMIT:
            errors.append(
                f"w3 admit commit mismatch: {w3.get('w3_mkt_work_commit')} != {ft.W3_ADMIT_COMMIT}"
            )

    return {
        "ok": not errors,
        "errors": errors,
        "trials_before": {"charged": charged, "remaining": remaining},
        "loop_phase": process.get("loop_phase"),
        "w3_admit_commit": econ.get("w3_mkt_work_commit") or ft.W3_ADMIT_COMMIT,
        "D2_prior": econ.get("D2_PRECHECK") or "GREEN",
    }


def _load_admitted_corpus(root: Path) -> tuple[list[Any], dict[tuple[str, str, str], str], dict[str, Any]]:
    raw_path = root / ft.DEFAULT_STRUCTURED_TRANSITIONS
    master_path = root / ft.DEFAULT_MASTER
    plan_path = root / ft.DEFAULT_TRANSITION_PLAN
    receipt_path = raw_path.with_suffix(".receipt.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    _validate_receipt(raw_path, master_path, plan_path, receipt)
    master_rows = _read_csv(master_path)
    plan_rows = _read_csv(plan_path)
    raw_rows = _read_csv(raw_path)
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
    return snapshots, predecessor, admission


def _update_sot(
    root: Path,
    *,
    session: str,
    first_fail_layer: str | None,
    failure_route: str,
    debited: bool,
    d9_screen: str | None,
    work_commit: str = "PENDING_COMMIT",
) -> None:
    sot_path = root / "docs/context/research_loop_state_current.json"
    sot = ft.load_json(sot_path)
    charged = 3 if debited else 2
    remaining = 0 if debited else 1

    for track in sot.get("active_tracks") or []:
        if track.get("track_id") == "AO-FTK-1":
            track.update(
                {
                    "status": "ECON_1_FINAL_TRIAL_COMPLETE"
                    if debited
                    else "ECON_1_ABORT_NO_DEBIT_D2_RED",
                    "loop_phase": "L7_ROADMAP_DECISION",
                    "worker_status": "CLOSED / NO_WORKER",
                    "material_trials_charged_this_slice": charged,
                    "material_trials_remaining": remaining,
                    "financial_alpha_evidence": 0,
                    "runnable_evaluation": False,
                    "next": (
                        "CLOSED / NO_WORKER; final economic trial complete; "
                        f"first_fail={first_fail_layer}; remaining={remaining}; alpha=0; no FTK-2"
                        if debited
                        else "CLOSED / NO_WORKER; D2 RED abort no debit; remaining=1; alpha=0"
                    ),
                }
            )
            if debited:
                track["econ_1_l5_final_run"] = ft.RUN_REL.as_posix()
                track["econ_1_l6_final"] = ft.L6_REL.as_posix()
                track["econ_1_l7_final"] = ft.L7_REL.as_posix()
            track["econ_1_d2_repreflight"] = ft.D2_REL.as_posix()

        if track.get("track_id") == "AO-FTK-1-ECON-1":
            track.update(
                {
                    "status": "FINAL_TRIAL_COMPLETE" if debited else "ABORT_NO_DEBIT_D2_RED",
                    "loop_phase": "L7_ROADMAP_DECISION",
                    "worker_status": "CLOSED / NO_WORKER",
                    "session_path": session,
                    "material_trials_charged_to_date": charged,
                    "material_trials_remaining": remaining,
                    "material_trial_debit_this_turn": debited,
                    "economic_l5_authorized": debited,
                    "runnable_evaluation": False,
                    "financial_alpha_evidence": 0,
                    "first_fail_layer": first_fail_layer,
                    "failure_route": failure_route,
                    "d9_screen": d9_screen,
                    "D2_REPREFLIGHT": "GREEN" if debited or session != "ABORT_NO_DEBIT" else "RED",
                    "full_w3_market_admitted": True,
                    "ao_ftk_2": "NOT_OPENED",
                    "worker_did_not_select_next_slice": True,
                    "next": "L7 owner route only; no FTK-2; no second eval",
                    "l5_final_auth_receipt": ft.AUTH_REL.as_posix() if debited else None,
                    "l5_final_debit_receipt": ft.DEBIT_REL.as_posix() if debited else None,
                    "l5_final_join_receipt": ft.JOIN_REL.as_posix() if debited else None,
                    "l5_final_run_receipt": ft.RUN_REL.as_posix() if debited else None,
                    "l6_final_receipt": ft.L6_REL.as_posix() if debited else None,
                    "l7_final_owner_packet": ft.L7_REL.as_posix(),
                    "d2_repreflight_receipt": ft.D2_REL.as_posix(),
                    "work_commit": work_commit,
                    "note": (
                        "Final economic trial complete; trials remaining=0; alpha=0"
                        if debited
                        else "D2 re-preflight RED; abort without debit; remaining=1"
                    ),
                }
            )

    sot["process"] = {
        **sot.get("process", {}),
        "loop_phase": "L7_ROADMAP_DECISION",
        "loop_phase_label": (
            f"AO-FTK-1-ECON-1 final trial {session}; first_fail={first_fail_layer}; "
            f"remaining={remaining}; alpha=0; NO_WORKER"
        ),
        "last_completed_phase": "ECON_1_FINAL_L7_STOP" if debited else "ECON_1_ABORT_D2_RED",
        "last_completed_note": (
            f"WORK_ID={ft.WORK_ID}; session={session}; debited={debited}; "
            f"first_fail={first_fail_layer}; route={failure_route}; "
            f"d9={d9_screen}; trials charged={charged} remaining={remaining}; "
            "AO_FTK_2=NOT_OPENED; alpha=0"
        ),
        "next_phase": "L7_ROADMAP_DECISION",
        "next_phase_note": (
            "Owner L7 route only. No FTK-2. No second eval. No capital. "
            f"Trials remaining={remaining}. financial_alpha_evidence=0."
        ),
        "diagnosis_layer_if_any": first_fail_layer,
        "failure_route_if_any": failure_route,
    }
    sot["next_worker_slice"] = {
        "primary": "OWNER_SELECT",
        "recommended": "L7_ROUTE_ONLY",
        "alternatives": ["HOLD", "STOP", "CANDIDATE_PIPELINE_PREP", "PARALLEL_ONLY"],
        "forbidden_as_next": [
            "open AO-FTK-2",
            "second economic eval",
            "claim financial_alpha_evidence > 0",
            "capital open",
            "L8 without owner earn",
            "AOV-as-W3",
        ],
    }
    sot["allowed_now"] = [
        "preserve Clock #1",
        "owner L7 route only on AO-FTK-1-ECON-1",
        "CRV1 / Sector Rotation isolated work",
        "PAPER-0 ops at alpha_evidence=0",
        "read final trial receipts",
    ]
    sot["forbidden_now"] = [
        "open AO-FTK-2",
        "second economic evaluation",
        "debit more trials (remaining=0)" if debited else "debit without D2 GREEN",
        "claim financial_alpha_evidence > 0",
        "capital open",
        "W6 open",
        "AOV-104 as Full-W3",
        "invent prices/returns",
        "asymmetric return FTK vs W3",
        "L8 this session without owner earn",
        "reopen AO-FTK-0 as worker",
    ]
    sot["last_econ_final_trial"] = {
        "work_id": ft.WORK_ID,
        "session": session,
        "debited": debited,
        "first_fail_layer": first_fail_layer,
        "failure_route": failure_route,
        "d9_screen": d9_screen,
        "material_trials_charged": charged,
        "material_trials_remaining": remaining,
        "financial_alpha_evidence": 0,
        "ao_ftk_2": "NOT_OPENED",
        "receipts": {
            "d2": ft.D2_REL.as_posix(),
            "auth": ft.AUTH_REL.as_posix() if debited else None,
            "debit": ft.DEBIT_REL.as_posix() if debited else None,
            "join": ft.JOIN_REL.as_posix() if debited else None,
            "run": ft.RUN_REL.as_posix() if debited else None,
            "l6": ft.L6_REL.as_posix() if debited else None,
            "l7": ft.L7_REL.as_posix(),
        },
        "work_commit": work_commit,
    }
    sot["product"]["financial_alpha_evidence"] = 0
    sot["product"]["w6"] = "UNTOUCHED"
    sot["updated_at_utc"] = "2026-08-12"
    ft.write_json_atomic(sot_path, sot, overwrite=True)


def _update_active_brief(root: Path, *, session: str, first_fail: str | None, remaining: int) -> None:
    path = root / "docs/context/ACTIVE_BRIEF"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    header = f"""# ACTIVE_BRIEF — 2026-08-12

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
ACTIVE_RESEARCH_SHADOW   = AO-FTK-1-ECON-1 / {session} / first_fail={first_fail} / remaining={remaining} / NO_WORKER
AO_FTK_0_STATUS          = CLOSED / READY_FOR_LATER_CHARGED_DEVELOPMENT_READ / NO_WORKER
AO_FTK_1_STATUS          = ECON_1_FINAL / charged={'3' if remaining == 0 else '2'} remaining={remaining} / NO_WORKER
AO_FTK_1_ECON_1_STATUS   = {session}; first_fail={first_fail}; alpha=0; NO_WORKER
OK_SBI_0_STATUS          = S0_DESIGN_LOCKED_RELEASE_BLOCKED + Q_SOURCE_BLOCKED_TERMINAL (PARKED)
CAPITAL_ALPHA_PATH       = CLOSED
FINANCIAL_ALPHA_EVIDENCE = 0
```

## AO-FTK-1-ECON-1 final trial (2026-08-12)

```text
WORK_ID               = {ft.WORK_ID}
SESSION               = {session}
FIRST_FAIL_LAYER      = {first_fail}
TRIALS                = charged={'3' if remaining == 0 else '2'} remaining={remaining}
ALPHA                 = 0
AO_FTK_2              = NOT_OPENED
NEXT                  = L7 owner route only
```

### Receipts

```text
d2   = {ft.D2_REL.as_posix()}
auth = {ft.AUTH_REL.as_posix()}
debit= {ft.DEBIT_REL.as_posix()}
join = {ft.JOIN_REL.as_posix()}
run  = {ft.RUN_REL.as_posix()}
l6   = {ft.L6_REL.as_posix()}
l7   = {ft.L7_REL.as_posix()}
```

## Do now

1. Preserve Clock #1; outcomes sealed until legitimate maturity.
2. Owner L7 route only on AO-FTK-1-ECON-1.
3. **No FTK-2. No second eval. No capital. alpha=0.**

## Do not

```text
open AO-FTK-2 / second economic eval / claim financial_alpha_evidence > 0
capital open / W6 open / AOV-104 as Full-W3 / invent prices-returns
asymmetric FTK vs W3 returns / L8 without owner earn
```

## One-line constitution

{ft.CONSTITUTION}
"""
    # Keep brief focused on final state
    path.write_text(header, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="AO-FTK-1-ECON-1 final economic trial")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    root = args.repo.resolve()

    print("=== P0 self-check ===")
    p0 = _p0_self_check(root)
    if not p0["ok"]:
        print("P0 FAIL:", p0["errors"])
        return 2
    print("P0 OK", p0["trials_before"])

    print("=== P1 D2 re-preflight ===")
    d2 = ft.build_d2_repreflight(root)
    ft.write_json_atomic(root / ft.D2_REL, d2, overwrite=args.overwrite)
    print("D2_PRECHECK=", d2.get("D2_PRECHECK"), "blockers=", d2.get("blockers"))
    print(
        "coverage_min=",
        (d2.get("coverage") or {}).get("coverage_rate_min"),
        "dates=",
        (d2.get("coverage") or {}).get("decision_dates_h63_calendar_complete"),
        "n_elig_max=",
        (d2.get("coverage") or {}).get("n_w3_eligible_sample_max"),
    )

    if d2.get("D2_PRECHECK") != "GREEN":
        abort = ft.build_abort_no_debit_packet(d2)
        ft.write_json_atomic(root / ft.L7_REL, abort, overwrite=args.overwrite)
        _update_sot(
            root,
            session="ABORT_NO_DEBIT",
            first_fail_layer="D2_DATA_OBSERVABLE",
            failure_route="ABORT_NO_DEBIT_D2_RED",
            debited=False,
            d9_screen="NOT_REACHED",
        )
        _update_active_brief(
            root, session="ABORT_NO_DEBIT", first_fail="D2_DATA_OBSERVABLE", remaining=1
        )
        print("ABORT_NO_DEBIT_D2_RED")
        return 0

    print("=== P2 authorization ===")
    auth = ft.build_l5_final_authorization(d2=d2)
    ft.write_json_atomic(root / ft.AUTH_REL, auth, overwrite=args.overwrite)

    print("=== P3 debit ===")
    debit = ft.build_trial_debit()
    ft.write_json_atomic(root / ft.DEBIT_REL, debit, overwrite=args.overwrite)
    print("debited 1: remaining 1→0")

    print("=== load structured corpus + scores ===")
    snapshots, predecessor, admission = _load_admitted_corpus(root)
    print(
        "snapshots=",
        len(snapshots),
        "admitted_sec=",
        admission.get("admitted_security_count"),
    )
    score_rows = ft.build_continuous_scores(snapshots, predecessor)
    print("score_rows=", len(score_rows))

    print("=== P4 economic label join ===")
    probe = ft.build_final_market_probe(root, d2)
    join_receipt, manifest, label_rows = ft.build_label_join(repo=root, market_probe=probe)
    # write labels
    jsonl_path = root / ft.FINAL_LABELS_JSONL_REL
    if jsonl_path.exists() and not args.overwrite:
        raise FileExistsError(jsonl_path)
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in label_rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
    ft.write_json_atomic(root / ft.FINAL_JOINED_MANIFEST_REL, manifest, overwrite=args.overwrite)
    ft.write_json_atomic(root / ft.JOIN_REL, join_receipt, overwrite=args.overwrite)

    print("=== P5 one frozen economic evaluation ===")
    run = ft.run_economic_evaluation(repo=root, score_rows=score_rows)
    ft.write_json_atomic(root / ft.RUN_REL, run, overwrite=args.overwrite)
    payoff = run.get("payoff") or {}
    print(
        "delta_J=",
        payoff.get("delta_J"),
        "d9=",
        payoff.get("d9_screen"),
        "screens=",
        run.get("layer_screens"),
    )

    print("=== P6 L6 first-fail ===")
    l6 = ft.build_l6_diagnosis(run)
    ft.write_json_atomic(root / ft.L6_REL, l6, overwrite=args.overwrite)
    print("first_fail=", l6.get("first_fail_layer"), "route=", l6.get("failure_route"))

    print("=== P7 L7 owner packet + SoT ===")
    l7 = ft.build_l7_owner_packet(run=run, l6=l6, d2=d2)
    ft.write_json_atomic(root / ft.L7_REL, l7, overwrite=args.overwrite)
    _update_sot(
        root,
        session="C_FINAL_TRIAL_COMPLETE",
        first_fail_layer=l6.get("first_fail_layer"),
        failure_route=str(l6.get("failure_route")),
        debited=True,
        d9_screen=str(l6.get("d9_screen")),
    )
    _update_active_brief(
        root,
        session="C_FINAL_TRIAL_COMPLETE",
        first_fail=l6.get("first_fail_layer"),
        remaining=0,
    )

    print("=== HARD STOP ===")
    print(
        json.dumps(
            {
                "WORK_ID": ft.WORK_ID,
                "D2_REPREFLIGHT": "GREEN",
                "DEBITED": True,
                "SESSION": "C_FINAL_TRIAL_COMPLETE",
                "FIRST_FAIL_LAYER": l6.get("first_fail_layer"),
                "FAILURE_ROUTE": l6.get("failure_route"),
                "D9_SCREEN": l6.get("d9_screen"),
                "DELTA_J": payoff.get("delta_J"),
                "ALPHA": 0,
                "TRIALS_AFTER": {"charged": 3, "remaining": 0},
                "AO_FTK_2": "NOT_OPENED",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
