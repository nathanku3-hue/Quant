# SAW Report — GV Operated Portfolio Acceptance-Kernel Repair — 2026-07-31

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: change-scope | Domains: product strategy, execution/accounting, persistence/custody, Streamlit product | Source: explicit user-fixed repair scope

RoundID: `GV-OPERATED-10-KERNEL-REPAIR-20260731`
ScopeID: `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R`
Base: `3e4dc957f475945169ddf33ed359254bd98dc64d`
Branch: `codex/gv-challenger-promotion-1`

## Verdict

SAW Verdict: BLOCK

The acceptance-kernel repair and narrow pinned Windows environment are locally green, but this is not terminal acceptance. A pushed immutable candidate SHA, hosted Windows/Linux parity, fresh-checkout proof, full failset comparison, and genuinely independent Reviewer A/B/C remain open.

## Acceptance checks

| Check | Result | Evidence |
|---|---|---|
| CHK-01 Decision selection and instrument-owned evidence are authoritative | PASS | empty selection and shared-evidence adversarial regressions fail closed |
| CHK-02 Event-derived projections, transition deltas, certification history, and correction links are exact | PASS | forged chain/order/fill/changed-why/transition/certification regressions fail closed |
| CHK-03 Persistence rejects linked ancestors and Windows junctions | PASS | junction-ancestor regression; no escaped workspace write |
| CHK-04 Black-box operator loop includes correction and fresh-process corrected reopen | PASS | AppTest with network denied |
| CHK-05 Focused product, shared semantics, and context/authority regressions pass | PASS | operated/AppTest 15/15; focused 70/70; context 33/33; combined 178/178 |
| CHK-06 Hosted parity and immutable terminal review | BLOCK | narrow Windows environment PASS and CI added; no pushed candidate SHA, hosted Linux/Windows result, or independent review |

## Local role-separated review

These passes were performed in one assistant session and are not independent reviewers.

### Reviewer A — product and strategy

- PASS locally: deterministic selected IDs control funding.
- PASS locally: each review retains its instrument-owned initial evidence.
- PASS locally: no frozen quantity or product phase was weakened.

### Reviewer B — runtime and operator flow

- PASS locally: confirm → no-change → transition → correction → fresh-process reopen.
- PASS locally: explicit captions expose clusters, funded symbols, trade sides, and changed-why under pinned Streamlit 1.54.0.
- PASS locally: no provider or broker path was introduced.

### Reviewer C — accounting, replay, and custody

- PASS locally: orders, fills, authority chains, transition legs, book, certification history, and correction links are event-derived or byte-equal.
- PASS locally: Harbor and Meridian accounting remains NAV 4988, costs 12, residual 0.
- PASS locally: symlink and Windows-junction ancestors are rejected before create/write/replace/load.
- PASS locally: `requirements-alpha.txt` provisions Python 3.12.10, pytest 9.0.2, and Streamlit 1.54.0 with `pip check` green.
- BLOCK terminal: hosted Windows/Linux exact-SHA parity and independent review are not yet available.

## Findings

| Severity | Finding | Impact | Fix | Owner | Status |
|---|---|---|---|---|---|
| Critical | Decision selection was descriptive rather than executable authority | Unauthorized funding could pass | Execute exact deterministic selected IDs | Current slice | RESOLVED |
| Critical | UI/history projections could contradict canonical events | Operator and certification truth could diverge | Reconstruct or require byte equality | Current slice | RESOLVED |
| High | Persistence followed linked ancestors | Workspace writes could escape lexical root | Canonical ancestor and junction confinement | Current slice | RESOLVED |
| High | Black-box flow stopped before correction | No complete operator/reopen proof | Extend AppTest through corrected reopen | Current slice | RESOLVED |
| High | Existing CI did not trigger on operated files or run operated tests | A known-invalid or untested candidate could be pushed without hosted proof | Add narrow Windows/Linux operated-product workflow using `requirements-alpha.txt` | Current slice | RESOLVED LOCALLY; HOSTED RUN PENDING |

## Scope split

### In-scope

Acceptance-kernel semantics, evidence ownership, event-derived projections, certification/correction lineage, linked-ancestor persistence confinement, black-box correction/reopen, tests, and current authority surfaces.

### Inherited out-of-scope

Repository-wide failset comparison, independent reviewer execution, candidate push, main fast-forward, and terminal tagging. The monorepo root lock is outside this product slice. Scale, Universe, Challenger, providers, optimizer, broker, and Live remain closed.

## Document Changes Showing

- `gv_portfolio_v0/operated.py`: decision/event/certification authority and exact projections.
- `gv_portfolio_v0/operated_storage.py`: v2 confined atomic persistence.
- `views/gv_operated_portfolio_workspace.py`: AppTest-visible operator truth.
- `tests/gv_portfolio_v0/test_operated.py`: adversarial acceptance-kernel regressions.
- `tests/gv_portfolio_v0/test_operated_app.py`: correction and fresh-process reopen.
- current context, phase brief, notes, decision log, and lessons: local-green/terminal-blocked truth.

## Validation / evidence

- Changed modules compile: PASS.
- Operated domain + AppTest: 15/15 PASS.
- Book/execution/replay/operated focused set: 70/70 PASS.
- Context/authority set: 33/33 PASS.
- Complete `tests/gv_portfolio_v0`: 145/145 PASS.
- Combined package + context/authority: 178/178 PASS under pinned `requirements-alpha.txt` environment.
- Narrow environment: Python 3.12.10, pytest 9.0.2, Streamlit 1.54.0; `pip check` PASS.
- `.github/workflows/gv-operated-portfolio.yml`: operated-file triggers plus Windows/Linux Python 3.12 matrix.
- Context packet build and validation: PASS.
- `git diff --check`: PASS.
- One locally frozen candidate commit exists at current branch HEAD; no push, hosted parity, main fast-forward, or tag.

Open Risks: pushed immutable candidate, hosted Windows/Linux parity, exact-SHA fresh-checkout proof, full failset comparison, and independent Reviewer A/B/C are missing.

Next action: push the locally frozen current-HEAD candidate, then run hosted parity, fresh-checkout proof, full failset comparison, and A/B/C concurrently.

ClosurePacket: RoundID=GV-OPERATED-10-KERNEL-REPAIR-20260731; ScopeID=GV-OPERATED-PORTFOLIO-10-TRANSITION-1R; ChecksTotal=6; ChecksPassed=5; ChecksFailed=1; Verdict=BLOCK; OpenRisks=hosted_exact_sha_parity_and_independent_terminal_review_missing; NextAction=push_frozen_candidate_then_run_terminal_gates_concurrently

ClosureValidation: PASS
SAWBlockValidation: PASS
