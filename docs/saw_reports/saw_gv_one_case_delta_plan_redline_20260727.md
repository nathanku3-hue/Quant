# SAW Report — GV One-Case Decision Delta Plan Redline

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Decision Value Observation, Docs/Ops, Research Protocol | FallbackSource: docs/spec.md + docs/phase_brief/gv-one-case-decision-delta-brief.md

RoundID: ROUND-20260727-GV-ONE-CASE-DELTA-PLAN-REDLINE
ScopeID: GV_ONE_CASE_EVIDENCE_GAP_TRIAGE_PLAN

## Scope

Planning-only final redline of the next GodView one-case comparison. No runtime, test, data, workflow, current-truth, Git-ref, remote, or human-session implementation was authorized or performed.

The branch base is clean at accepted `origin/main@48a43b9`. The worktree is intentionally not clean and contains exactly three planning changes:

- `docs/phase_brief/gv-one-case-decision-delta-brief.md`
- `docs/lessonss.md`
- `docs/saw_reports/saw_gv_one_case_delta_plan_redline_20260727.md`

An ignored Python 3.12 `.venv` was created only to run mandatory validators. It is not a tracked change or Commit A implementation.

## Ownership Check

Thin SAW applies because this is a low-risk planning/docs-only round. No code or phase closeout occurred.

Ownership check: PASS for thin scope validation; independent implementation reviewers remain required after Commit A exists.

## Acceptance Checks

- CHK-01: Verify the branch base is exactly accepted `origin/main@48a43b9`, zero ahead/behind, with exactly three uncommitted planning changes.
- CHK-02: Remove impossible self-referential candidate binding from `experiment_binding.json`; bind exact hosted-green candidate later through `session_manifest.json`.
- CHK-03: Replace unequal principal strings with two separately verifiable signed identity records linked to distinct verified-human subject commitments.
- CHK-04: Add a positive source-file allowlist, path/hash custody, repository confinement, and forbidden-path access tests for projection generation.
- CHK-05: Retain each blinded arm's current research action and rationale while excluding prior Alpha and portfolio answers.
- CHK-06: Define equal maximum 60-minute budgets, early submission, no latency inference, and pre-exposure versus consumed-run abort semantics.
- CHK-07: Preserve forbidden scope: no Commit A code, truth correction, UI, publication, provider work, push, or human run.
- CHK-08: Run both repository-mandated SAW validators and `git diff --check` with ignored Python 3.12 `.venv`.

## Findings

| Severity | Impact | Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| P0 | `experiment_binding.json` cannot contain the SHA of the commit that contains itself. | Static binding excludes candidate SHA; post-hosted-green `session_manifest.json` binds candidate SHA/tree, experiment binding, instructions, schemas, proof identity, nonce, and one-shot state. | Commit A implementer | Planned |
| P0 | Unequal principal strings plus one replayable attestation do not prove two separate humans. | Require two independently verified signed identity records with distinct verified-human subject commitments, credentials, role challenges, issuer evidence, and session-manifest binding. | Human-run owner | Planned |
| P0 | Forbidden output scanning does not prove projection source custody. | Added exact positive path/hash allowlist, repository-confined canonical resolution, instrumented read-set proof, and direct/alias/symlink/junction forbidden-path tests. | Commit A implementer | Planned |
| P1 | Removing all actions from blinded arms makes `selected_action_defensibility` unscoreable. | Retain each arm's newly authored current research action and rationale; exclude only prior Alpha, portfolio, adjudication, result, and origin metadata. | Commit A implementer | Planned |
| P1 | Equal budget, elapsed time, latency inference, and one-shot abort state were conflated. | Defined equal maximum 60-minute budgets, early submission, differing elapsed times, no latency endpoint, pre-exposure abort, and irrevocable consumption at `BASELINE_OPEN`. | Human-run owner | Planned |
| Medium | Prior plan and SAW incorrectly described the planning worktree as clean. | State branch base clean and worktree containing exactly three planning changes. | Planner | Fixed |
| Medium | Mandatory validators were previously blocked by absent `.venv`. | Created ignored Python 3.12.10 `.venv` and ran both validators plus whitespace validation. | Environment owner | Fixed |

## Scope Split Summary

In-scope actions:

- Corrected the approval-gate brief for all three P0 and two P1 audit defects.
- Updated the lesson entry with non-self-referential custody, signed-human identity, positive source custody, action retention, and one-shot semantics.
- Updated this SAW evidence to reflect the actual dirty planning worktree and validator results.
- Created ignored `.venv` solely for validation.

Inherited out-of-scope items:

- Active current-truth surfaces remain stale about Alpha merge status; correction is reserved for an approved Commit A.
- Root checkout remains stale and massively dirty; it was not touched.
- Commit A implementation, hosted CI, independent implementation reviewers, human run, and Commit B remain blocked pending final plan audit.

## Reviewer Passes

- Thin scope check: PASS. Exactly the three authorized planning files changed; ignored `.venv` is environment-only.
- Forbidden-action scan: PASS. No runtime, tests, data, workflow, truth surfaces, Git refs, remote branches, or human records changed.
- Evidence check: PASS. All five audit defects are explicitly represented in the brief and lesson.
- Candidate-custody check: PASS. Static experiment binding and runtime session binding are separated.
- Human-separation check: PASS. Principal-string inequality is explicitly insufficient.
- Source-custody check: PASS. Positive allowlist and forbidden-path reads are both required.
- Budget/abort check: PASS. Maximum budgets, early completion, no latency claim, and consumption boundary are explicit.
- Next-action check: PASS. Return the plan for final audit; implementation remains blocked.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
| --- | --- | --- |
| `docs/phase_brief/gv-one-case-decision-delta-brief.md` | Corrected local status; candidate/session binding; signed-human identity evidence; source allowlist; current-arm action/rationale; budget and abort semantics. | PASS |
| `docs/lessonss.md` | Replaced the prior partial lesson with the complete custody, identity, blinding, and one-shot guardrail. | PASS |
| `docs/saw_reports/saw_gv_one_case_delta_plan_redline_20260727.md` | Reconciled findings, actual worktree status, scope, and validation evidence. | PASS |

## Document Sorting

Canonical review order:

1. Phase brief.
2. Lesson register.
3. Thin SAW evidence.

## Evidence

- Branch base: `HEAD = origin/main = 48a43b99350465202f8bcd09113a34fa724580af`.
- Branch delta from `origin/main`: `0 / 0`; branch remains unpushed.
- Worktree: exactly three planning changes; no runtime/test/data/workflow/current-truth files changed.
- Python environment: ignored `.venv`, Python `3.12.10`.
- Closure packet validator: PASS.
- SAW report-block validator: PASS.
- `git diff --check`: PASS.
- `.venv` ignored by `.gitignore`; it does not appear in `git status`.

## Open Risks

Open Risks:

- Final independent plan audit has not yet issued implementation approval.
- Current-truth merge-pending drift remains until approved Commit A.
- Human-run execution still depends on two eligible, materially case/outcome-naive, separately verified humans.
- Identity-evidence adapters must meet the core signed-human contract; account inequality alone remains forbidden.

Next action: return the revised planning artifacts for final audit. Do not implement, push, correct truth, or open a human session.

ClosureValidation: PASS
SAWBlockValidation: PASS

ClosurePacket: RoundID=ROUND-20260727-GV-ONE-CASE-DELTA-PLAN-REDLINE; ScopeID=GV_ONE_CASE_EVIDENCE_GAP_TRIAGE_PLAN; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=final_plan_audit_pending_current_truth_drift_two_verified_humans_not_yet_scheduled; NextAction=return_revised_plan_for_final_audit
