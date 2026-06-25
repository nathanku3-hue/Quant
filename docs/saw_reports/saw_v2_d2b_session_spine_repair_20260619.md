# SAW Report - V2 PEAD D2B Authoritative Market-Session Spine Repair

Mode: `EXECUTION_PACKET`

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-user-approval | Domains: quantitative-research,data-engineering,PEAD-event-study,docs-ops

RoundID: `ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR`
ScopeID: `V2_D2B_AUTHORITATIVE_MARKET_SESSION_SPINE`

Ship-Fast Decision Gate: the single decision was whether the repaired D2B
authoritative market-session spine can be treated as terminally closed. It
cannot: code, artifact, tests, active-scale smoke, and local reconciliation
passed, but final independent Reviewer A/B/C could not run after the last
High-finding fixes because the reviewer pool hit a usage limit.

## Scope and Ownership

In-scope: repair the D2B market-session spine so D2B offsets are based on the
exact official Ken French daily source dates within the D2A sample range;
preserve D2A evidence and D2B fixed-security selection semantics; rebuild the
bounded D2B sample artifact; make D3 reconstruct and verify the source-backed
session spine before any benchmark publication.

Forbidden scope: patching benchmark dates inside D3, benchmark-date fill/drop,
interpolation, zero substitution, fallback benchmark, source splice, D2B
security-selection semantic changes, D3 artifact publication, CAR/BHAR or
quintile interpretation, dashboard work, ranking/scoring, alerts, broker/order
paths, full build, staging, and commit.

Owned files changed or produced:

- `scripts/pead_d2b_event_window_contract.py`
- `scripts/pead_d3_benchmark_artifact.py`
- `tests/test_pead_d2b_event_window_contract.py`
- `tests/test_pead_d3_benchmark_artifact.py`
- `data/processed/pead_d2b_event_windows_sample.c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1.parquet`
- `data/processed/pead_d2b_event_windows_sample.parquet.manifest.json`
- `docs/phase_brief/v2-pead-d2b-session-spine-repair-brief.md`
- `docs/phase_brief/v2-pead-d2b-event-iid-window-brief.md`
- `docs/phase_brief/v2-pead-d3-benchmark-artifact-implementation.md`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/*_current.md`
- `docs/context/current_context.md`
- `docs/context/current_context.json`

## Acceptance Checks

| Check | Acceptance condition | Result |
|---|---|---|
| CHK-01 | Official Ken French source release, SHA256, ZIP member, and source URLs are captured in the D2B manifest. | PASS |
| CHK-02 | D2B session spine uses source-backed authoritative market sessions, not raw D2A distinct dates. | PASS |
| CHK-03 | The 52 D2A-only market-closed dates are excluded from offsets without deleting D2A evidence. | PASS |
| CHK-04 | D2B fixed-security selection semantics remain unchanged. | PASS |
| CHK-05 | Corrected immutable D2B artifact is published atomically and prior immutable artifact remains available for rollback. | PASS |
| CHK-06 | D3 reconstructs the source-backed required session spine and verifies the D2B session hash before publication. | PASS |
| CHK-07 | D3 benchmark coverage validates in memory at 2,810 / 2,810 with zero missing and no D3 artifact published. | PASS |
| CHK-08 | Focused D2A/D2B/D3/strategy validation passes. | PASS |
| CHK-09 | Active-scale strategy handoff completes without the prior full-frame D2A normalization memory failure. | PASS |
| CHK-10 | Cross-row event metadata/timing drift fails closed. | PASS |
| CHK-11 | Normalization-colliding D2A duplicate keys fail closed globally. | PASS |
| CHK-12 | Final independent Reviewer A/B/C rerun after all fixes is available. | FAIL |

ChecksTotal: 12
ChecksPassed: 11
ChecksFailed: 1

## SE Evidence

Scope line: stream=Data+Docs/Ops; stage=execution/reconciliation; owner=Codex; round_exec_utc=2026-06-20T03:57:26Z

| TaskID | Task | Artifact | Check | Status | EvidenceID |
|---|---|---|---|---|---|
| TSK-01 | Replace raw D2A-date session inference with source-backed authoritative sessions. | `scripts/pead_d2b_event_window_contract.py` | CHK-01, CHK-02, CHK-03 | PASS | EVD-01 |
| TSK-02 | Preserve D2B selection/window semantics while rebuilding the bounded artifact. | D2B manifest and immutable Parquet | CHK-04, CHK-05 | PASS | EVD-02 |
| TSK-03 | Bind D3 required sessions to the recorded source-backed spine and hash. | `scripts/pead_d3_benchmark_artifact.py` | CHK-06, CHK-07 | PASS | EVD-03 |
| TSK-04 | Repair active-scale handoff memory and fail-closed validation gaps. | `scripts/pead_d2b_event_window_contract.py`, focused tests | CHK-08, CHK-09, CHK-10, CHK-11 | PASS | EVD-04 |
| TSK-05 | Complete terminal independent Reviewer A/B/C gate. | Reviewer A/B/C rerun | CHK-12 | BLOCK | EVD-05 |

| EvidenceID | Command or evidence | Result | Notes | EvidenceUTC | RunID |
|---|---|---|---|---|---|
| EVD-01 | D2B manifest/source audit | PASS | Official release `This file was created by using the 202604 CRSP database.`; SHA256 `4b384ddeed3ba5541c433071272aece0734129ff5a016790333632eee8eac518`; sessions `2,862 -> 2,810`; 52 excluded dates. | 2026-06-20T03:57:26Z | ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR |
| EVD-02 | `.venv\Scripts\python scripts\pead_d2b_event_window_contract.py --sample` | PASS | Active D2B artifact SHA256 `c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1`; prior SHA256 `8e2f39c2cb12bd0b50c9a134b280b5ecb8cd438f8a2249c6842c226250228b99` retained. | 2026-06-20T03:57:26Z | ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR |
| EVD-03 | D3 in-memory coverage check | PASS | Required benchmark rows validate at 2,810 / 2,810 with zero missing; zero `pead_d3_ken_french_daily_benchmark*` artifacts exist. | 2026-06-20T03:57:26Z | ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR |
| EVD-04 | `.venv\Scripts\python -m pytest tests\test_pead_d2_returns.py tests\test_pead_d2b_event_window_contract.py tests\test_pead_d3_benchmark_artifact.py tests\test_pead_event_study.py -q` | PASS | 70 passed; active-scale smoke: 11,450 events, 911,707 canonical returns, 687,000 complete rows, zero duplicate keys, peak RSS 1,756.7 MiB. | 2026-06-20T03:57:26Z | ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR |
| EVD-05 | Final Reviewer A/B/C rerun | BLOCK | Fresh reviewers hit usage limit before producing usable independent verdicts after final code changes. | 2026-06-20T03:57:26Z | ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05
EvidenceRows: EVD-01|ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR|2026-06-20T03:57:26Z;EVD-02|ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR|2026-06-20T03:57:26Z;EVD-03|ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR|2026-06-20T03:57:26Z;EVD-04|ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR|2026-06-20T03:57:26Z;EVD-05|ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR|2026-06-20T03:57:26Z
EvidenceValidation: PASS

Rollback note: restore the prior immutable D2B artifact/manifest pointer to SHA256
`8e2f39c2cb12bd0b50c9a134b280b5ecb8cd438f8a2249c6842c226250228b99`
as a bundle. Do not mix old/new Parquet and manifest files.

## Reviewer Reconciliation

- Pre-repair D3 Reviewer B/C rerun: PASS; no Critical/High D3 issue before
  the D2B/D2A session-spine repair.
- Reviewer C active-scale D2B repair finding: High memory failure from
  full-frame D2A normalization. Resolved with chunked validation and
  selected-security projection.
- Reviewer A post-memory finding: High event metadata/timing drift. Resolved
  with cross-row metadata consistency and strictly post-event return checks.
- Reviewer A post-memory finding: Medium normalized duplicate detection gap.
  Resolved with a global normalized `(security_id, date)` primary-key check.
- Final Reviewer A/B/C after all fixes: BLOCKED, not because a new technical
  finding was reported, but because independent reviewers could not run after
  the usage limit was reached.

Ownership check: BLOCK for terminal closure. Implementer/local reconciliation
and reviewer roles were distinct where reviewer results exist, but no usable
final A/B/C verdict exists for the final code state.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Full-frame D2A normalization could fail at active sample scale before strategy handoff. | Validate D2A globally in chunks and project selected-security rows before categorical normalization. | Data | RESOLVED |
| High | Cross-row event metadata drift could allow internally inconsistent event windows or pre-event observed returns. | Validate issuer/date/SUE/primary metadata consistency and require all observed returns to be strictly post-event. | Data | RESOLVED |
| Medium | Raw pre-normalization duplicate checks could miss normalized duplicate keys, including unselected securities. | Enforce exact normalized global `(security_id, date)` uniqueness through DuckDB. | Data | RESOLVED |
| Medium | Future D3 publication still validates the configured download host more strongly than the final redirect host. | Validate final response URL host before accepting future D3 publication input. | D3 Data/Ops | OPEN, NON-BLOCKING FOR THIS REPAIR |
| Medium | D2B records source release/hash/provenance but does not retain the full source ZIP as a local artifact. | Consider retained source ZIP evidence in a future provenance-hardening round. | Data/Ops | OPEN, NON-BLOCKING FOR THIS REPAIR |
| Medium | D3 publication interruption coverage is narrower than D2B coverage. | Add partial-write, `BaseException`, and post-commit interruption tests before D3 phase-end promotion. | D3 Data/Ops | OPEN, NON-BLOCKING FOR THIS REPAIR |
| High / Process | Final Reviewer A/B/C could not run after the last code fixes, so terminal milestone review evidence is missing. | Rerun final independent Reviewer A/B/C after usage limit resets. | Docs/Ops | OPEN, BLOCKING |

## Scope Split Summary

In-scope resolved actions: source-backed D2B sessions, 52 closed-date
exclusions, corrected D2B artifact, D3 session reconstruction/hash gate,
active-scale memory repair, metadata/timing fail-closed checks, and normalized
duplicate-key fail-closed checks.

Inherited or out-of-scope actions: D3 final redirect-host validation, retained
source ZIP policy, expanded D3 interruption tests, D3 artifact publication,
CAR/BHAR interpretation, dashboard, ranking/scoring, alerts, broker/order
paths, full build, staging, and commit.

## Validation Evidence

- Focused matrix:
  `.venv\Scripts\python -m pytest tests\test_pead_d2_returns.py tests\test_pead_d2b_event_window_contract.py tests\test_pead_d3_benchmark_artifact.py tests\test_pead_event_study.py -q`
  -> PASS, 70 passed.
- Context hygiene:
  `.venv\Scripts\python -m pytest tests\test_phase61_context_hygiene.py tests\test_build_context_packet.py -q`
  -> PASS, 24 passed.
- Context packet build and validation:
  `.venv\Scripts\python scripts\build_context_packet.py` and
  `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- D2B artifact:
  `data/processed/pead_d2b_event_windows_sample.c3da606af340ba5b531d3d0382e1f2c83469e29a42dd7c0cc9c356cba82594a1.parquet`.
- Active D2B manifest:
  `data/processed/pead_d2b_event_windows_sample.parquet.manifest.json`.
- D2B rows/events/sessions: 754,920 rows; 12,582 events; 2,810 sessions;
  11,450 eligible handoffs.
- D3 coverage: 2,810 / 2,810 in memory with zero missing; no
  `pead_d3_ken_french_daily_benchmark*` artifact exists.
- D3 reviewer-rerun evidence:
  `docs/saw_reports/saw_v2_d3_benchmark_artifact_reviewer_rerun_20260619.md`
  -> PASS.

## Harness Feedback

- Friction: Final SAW closure repeatedly depends on reviewer availability after local reconciliation fixes.
- Root Cause: Reviewer capacity can fail after technical fixes, leaving machine evidence complete but terminal A/B/C evidence absent.
- Guardrail: Preflight reviewer capacity before the final code-fix loop and publish BLOCK immediately if final A/B/C cannot run.
- Evidence: `docs/saw_reports/saw_v2_d2b_session_spine_repair_20260619.md`

HarnessFeedbackPacketValidatedSeparately: RoundID=ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR; ScopeID=HARNESS_FEEDBACK_REVIEWER_CAPACITY_FRICTION; ChecksTotal=3; ChecksPassed=3; ChecksFailed=0; Verdict=PASS; OpenRisks=none; NextAction=carry_reviewer_capacity_preflight_guardrail_into_next_review_round

HarnessFeedbackClosureValidation: PASS

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `scripts/pead_d2b_event_window_contract.py` | Added authoritative source-backed session spine, manifest provenance, chunked D2A validation, selected-security projection, and stricter output validation. | Local reconciliation PASS; final A/B/C unavailable |
| `scripts/pead_d3_benchmark_artifact.py` | Reconstructs D2B required sessions from source-backed manifest metadata and validates the session hash. | Local reconciliation PASS; final A/B/C unavailable |
| `tests/test_pead_d2b_event_window_contract.py` | Added authoritative-session, chunked handoff, metadata drift, and normalized duplicate regressions. | 70-test focused matrix PASS |
| `tests/test_pead_d3_benchmark_artifact.py` | Added source-backed required-session hash-drift regression. | 70-test focused matrix PASS |
| `data/processed/pead_d2b_event_windows_sample.parquet.manifest.json` | Points to corrected immutable D2B artifact with source/session provenance and excluded dates. | Artifact/hash evidence PASS |
| `docs/phase_brief/v2-pead-d2b-session-spine-repair-brief.md` | Records implementation/artifact/memory status and terminal SAW blocker. | Docs/Ops updated |
| `docs/context/*_current.md` | Current truth surfaces updated to block terminal closure on reviewer unavailability. | Context validation PASS |
| `docs/saw_reports/saw_v2_d2b_session_spine_repair_20260619.md` | Publishes the terminal BLOCK evidence for the repaired D2B session-spine round. | SAW validators PASS |

## Open Risks

Open Risks: terminal_reviewer_A_B_C_unavailable_after_final_code_due_usage_limit;
D3_redirect_host_validation_followup; D3_atomic_interruption_test_followup;
source_zip_retention_policy_followup.

Next action: rerun_final_reviewer_A_B_C_after_usage_limit_then_decide_D3_publication

ClosurePacket: RoundID=ROUND-20260619-V2-D2B-SESSION-SPINE-REPAIR; ScopeID=V2_D2B_AUTHORITATIVE_MARKET_SESSION_SPINE; ChecksTotal=12; ChecksPassed=11; ChecksFailed=1; Verdict=BLOCK; OpenRisks=terminal_reviewer_A_B_C_unavailable_after_final_code_due_usage_limit; NextAction=rerun_final_reviewer_A_B_C_after_usage_limit_then_decide_D3_publication

ClosureValidation: PASS

SAWBlockValidation: PASS
