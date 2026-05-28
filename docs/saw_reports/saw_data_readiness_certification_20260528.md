# SAW Report - Data Readiness Durable Certification and Replay Scope Repair

RoundID: `ROUND-20260527-DATA-READINESS-CERTIFICATION`
ScopeID: `SCOPE-DURABLE-SELECTED-ENDPOINT-AND-REPLAY-SELECTION-CERTS`
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-user-requested-subagents | Domains: Backend, Data, Docs/Ops, Frontend/UI
SAW Verdict: PASS
Commit Anchor: `pending-commit`
GitHub Status: pending commit/push at report publication time.
Dirty Worktree Status: current-round files dirty before commit; pre-commit `--require-github` boot preflight correctly blocked status writing.

## Scope

Add durable, hash-bound, read-only certification artifacts and checks so `data_readiness_gate` can move selected endpoint and replay-selection readiness from WARN to PASS truthfully, including explicit no-patch certification for missing `yahoo_patch`. The replay-selection certificate must not imply replay output artifact certification.

## Owned Files

- `core/data_readiness_gate.py`
- `tests/test_data_readiness_gate.py`
- `data/registry/portfolio_selected_endpoint_certification_v0.json`
- `data/registry/portfolio_replay_selection_certification_v0.json`
- `docs/architecture/data_readiness_gate_v0.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/saw_reports/saw_data_readiness_certification_20260528.md`

## Acceptance Checks

- CHK-01: Missing selected endpoint cert is strict WARN.
- CHK-02: Valid selected endpoint cert makes selected endpoint check PASS.
- CHK-03: Stale selected endpoint cert is strict WARN.
- CHK-04: Selected endpoint cert bad hash is strict FAIL.
- CHK-05: Missing replay cert is strict WARN.
- CHK-06: Valid replay cert makes replay-selection readiness PASS and `portfolio_replay_selection_status=CERTIFIED`.
- CHK-07: Replay cert sourced from Streamlit/session state is strict FAIL.
- CHK-08: Missing `yahoo_patch` without no-patch cert is strict WARN.
- CHK-09: Missing `yahoo_patch` with valid no-patch cert produces no yahoo_patch WARN.
- CHK-10: Certification validation is read-only and leaves no boot/data/cert tmp residue.
- CHK-11: Direct strict data-readiness gate returns PASS against the local safe-boot worktree.
- CHK-12: Governance, boot-control, context, AppTest smoke, and focused replay/dashboard preflight gates pass before commit; GitHub gate blocks only because worktree is dirty.
- CHK-13: Replay output remains `UNCERTIFIED_OUTPUT_NOT_CLAIMED` unless an actual replay output artifact is separately certified.

## Subagent Pass Summary

- Implementer pass: PASS. Implemented certificate validators, tests, registry certs, and docs-as-code updates without provider calls, repairs, replay rebuilds, runtime status writes, or large data staging.
- Reviewer A: PASS. Strategy correctness boundary preserved: replay cert binds durable selection/evidence only and does not claim replay output artifact certification, alpha, recommendation, or strategy promotion.
- Reviewer B: PASS. Runtime/ops resilience preserved: validation is read-only, provider/live imports remain forbidden, write-status was not invoked, and pre-commit GitHub gate blocked dirty worktree as expected.
- Reviewer C: PASS. Data integrity path validates repo-relative paths, SHA-256, optional size, expiry, non-session-state origin, no-patch policy, and tmp-residue absence.
- Ownership check: PASS. Implementer and Reviewer A/B/C roles are recorded as distinct SAW roles.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Replay and selected endpoint checks could not truthfully PASS because no durable non-session-state proof existed. | Added hash-bound registry certificates and strict validator checks. | Implementer | Closed |
| High | Replay selection certification was surfaced as `portfolio_replay_output_status=CERTIFIED`, overclaiming replay output certification. | Added `portfolio_replay_selection_status` for the durable proof and kept legacy `portfolio_replay_output_status=UNCERTIFIED_OUTPUT_NOT_CLAIMED`. | Repair Worker + Reviewer A | Closed |
| High | Missing `yahoo_patch` could be overread as harmless if the WARN were simply suppressed. | Required explicit selected-endpoint `no_patch_certified` policy before removing WARN. | Implementer + Reviewer C | Closed |
| Medium | Historical `.tmp` evidence files under `docs/context/e2e_evidence` could falsely block data-readiness tmp-residue checks. | Scoped certification tmp-residue check to `runtime`, `data/processed`, `data/runtime_cache`, and `data/registry`. | Implementer + Reviewer B | Closed |
| Medium | Pre-commit safe boot cannot pass while current-round files are dirty. | Confirmed boot preflight blocks `--require-github` until commit/push; no status file was generated. | Reviewer B | Closed |

## Scope Split Summary

In-scope findings/actions:

- Data-readiness selected endpoint, replay selection, and `yahoo_patch` no-patch certification are implemented and tested.
- Replay-selection readiness is separated from replay output artifact certification.
- Registry certification JSONs are tracked/unignored proof files; large `data/processed` parquet artifacts remain ignored local data.
- Docs-as-code records the formula, policy, decision, and lesson.

Inherited out-of-scope findings/actions:

- `portfolio_allocation.benchmarks` remains route-readiness WARN in the data-readiness payload and is not a blocker for `overall_status=PASS`.
- Runtime `boot_status_current.json` was intentionally not generated pre-commit.
- Full post-push safe-boot/write-status sequence remains required before status artifact generation.

## Verification Evidence

- `EVD-01`: `E:\Code\Quant\.venv\Scripts\python.exe -m pytest tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py -q` -> PASS, 27 passed.
- `EVD-02`: `E:\Code\Quant\.venv\Scripts\python.exe -c "from core.data_readiness_gate import run_data_readiness_gate; import json; payload=run_data_readiness_gate('.', mode='strict'); print(json.dumps(payload, indent=2, sort_keys=True))"` -> PASS; `overall_status=PASS`, `strict_status=PASS`, selected endpoint `CERTIFIED`, replay selection `CERTIFIED`, replay output `UNCERTIFIED_OUTPUT_NOT_CLAIMED`, no warnings/blockers.
- `EVD-03`: `E:\Code\Quant\.venv\Scripts\python.exe scripts\governance_preflight.py --repo-root . --json` -> PASS.
- `EVD-04`: `E:\Code\Quant\.venv\Scripts\python.exe scripts\boot_preflight.py --repo-root . --mode strict --require-github --smoke --run-focused-contract --json` -> expected pre-commit FAIL only because worktree was dirty; boot-control tests, data-readiness, governance, context validation, Portfolio AppTest smoke, and focused replay/dashboard contract all PASS.
- `EVD-05`: No repair command used `--write-status` before commit; any pre-existing ignored `runtime\boot_status_current.json` was not treated as current safe-boot proof.

## SE Executor Closure

Scope line: stream=Data/Ops, stage=Final Verification, owner=Data Readiness Certification Implementer, round_exec_utc=2026-05-28T04:48:30Z

| task_id | task | artifact | check | status | evidence_id |
|---|---|---|---|---|---|
| TSK-01 | Tests-first certification matrix | `tests/test_data_readiness_gate.py` | focused pytest | PASS | EVD-01 |
| TSK-02 | Read-only certificate validation | `core/data_readiness_gate.py` | focused pytest + direct gate | PASS | EVD-01,EVD-02 |
| TSK-03 | Portable registry certificates | `data/registry/*certification_v0.json` | direct gate hash validation | PASS | EVD-02 |
| TSK-04 | Docs/lesson/decision updates | docs files | SAW report review | PASS | EVD-03 |
| TSK-05 | Safe-boot pre-commit guard | boot preflight + status path | expected dirty-block, no status write | PASS | EVD-04,EVD-05 |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05
EvidenceRows: EVD-01|ROUND-20260527-DATA-READINESS-CERTIFICATION|2026-05-28T04:40:00Z;EVD-02|ROUND-20260527-DATA-READINESS-CERTIFICATION|2026-05-28T04:46:22Z;EVD-03|ROUND-20260527-DATA-READINESS-CERTIFICATION|2026-05-28T04:47:00Z;EVD-04|ROUND-20260527-DATA-READINESS-CERTIFICATION|2026-05-28T04:47:26Z;EVD-05|ROUND-20260527-DATA-READINESS-CERTIFICATION|2026-05-28T04:47:00Z
EvidenceValidation: PASS

## Document Changes Showing

| path | change summary | reviewer status |
|---|---|---|
| `docs/architecture/data_readiness_gate_v0.md` | Added durable certification addendum and explicit no-patch policy. | PASS |
| `docs/notes.md` | Added certification validation formula and yahoo_patch policy formula. | PASS |
| `docs/decision log.md` | Added Data Readiness Durable Certification v0 decision and contract lock. | PASS |
| `docs/lessonss.md` | Added lesson on durable non-session-state proof before WARN can become PASS. | PASS |
| `docs/saw_reports/saw_data_readiness_certification_20260528.md` | Published SAW report and validation evidence. | PASS |

## Document Sorting

GitHub-optimized ordering is maintained: architecture contract under `docs/architecture/`, formula/decision/lesson docs under canonical governance files, SAW report under `docs/saw_reports/`, and data certificates under `data/registry/`.

## Open Risks:

- Post-commit/post-push safe-boot must be rerun before any runtime boot-status generation.
- Any pre-existing ignored `runtime/boot_status_current.json` is not current proof and must not be refreshed until the full safe-boot gate passes clean/aligned after push.
- Certificate expiry is `2026-06-11T00:00:00Z`; refresh is required after that date before strict PASS can continue.

## Next action:

Commit and push the narrow certification files, rerun full strict safe-boot gate, and only run `--write-status` if safe_boot=true and Git is clean/aligned.

ClosurePacket: RoundID=ROUND-20260527-DATA-READINESS-CERTIFICATION; ScopeID=SCOPE-DURABLE-SELECTED-ENDPOINT-AND-REPLAY-SELECTION-CERTS; ChecksTotal=13; ChecksPassed=13; ChecksFailed=0; Verdict=PASS; OpenRisks=post-push-safe-boot-write-status-still-required; NextAction=commit-push-rerun-safe-boot-then-write-status-only-if-clean-aligned
ClosureValidation: PASS
SAWBlockValidation: PASS
