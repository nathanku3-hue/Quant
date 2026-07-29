# GodView v2 Roadmap Custody Repair Handover

Date: 2026-07-29
Mode: `CLOSURE_REPORT`
Status: `R0_BANKED; INDEPENDENT_AUDIT_PENDING`
Branch: `codex/gv-alpha0-ship`
Released ancestry: `93e7a55`
Roadmap authority: exact branch tip containing this repair, designated `ROADMAP_FREEZE_COMMIT`

## Executive Summary

The prior roadmap was directionally strong but not repository authority. It existed as 26 uncommitted paths, contained a stale direct-base instruction, used a numeric Phase 66 workaround, and put a contract catalogue ahead of the missing portfolio product loop.

R0 repairs those defects and stops. No portfolio implementation, provider access, data artifact, model, score uplift, broker behavior, or live-capital path is opened in this round.

## What changed

1. Removed standalone `GV-CANON-RESET-0` from the product sequence.
2. Made `GV-MICRO-PORTFOLIO-VERTICAL-0` the first product slice.
3. Kept `GV-DETERMINISTIC-REPLAY-0` immediately before bounded portfolio expansion.
4. Preserved released `gv_fs0_v1` unchanged and required a new portfolio namespace.
5. Added `docs/context/ACTIVE_BRIEF` as explicit authority.
6. Changed context generation to fail closed by default and allow numeric discovery only with `--allow-legacy-discovery`.
7. Moved the Phase 66 bridge to archive.
8. Explicitly superseded contradictory historical SAW instructions.
9. Replaced seven automatic branches with three mergeable work packages.
10. Defined minimum cross-layer identity/event seams before parallel work.
11. Reconciled root product, architecture, context, queue, decision, lesson, SAW, and handover surfaces.
12. Left the dirty root checkout untouched.

## Binding sequence

```text
R0 ROADMAP-CUSTODY-REPAIR
→ independent audit
→ GV-MICRO-PORTFOLIO-VERTICAL-0
→ GV-DETERMINISTIC-REPLAY-0
→ evidence-gated later slices
```

Later sequence:

```text
GV-BOUNDED-PORTFOLIO-1
→ GV-PORTFOLIO-SCALE-1
→ GV-UNIVERSE-SCALE-1
→ GV-CHALLENGER-PROMOTION-1
→ GV-LIMITED-LIVE-1
```

## First product acceptance

```text
launch
→ review 3–5 securities, benchmark, and classified cash
→ inspect principal thesis, substitute, competitor, and rejection
→ confirm portfolio aim
→ deterministic paper order and fill
→ certify book
→ persist and reopen
→ admit one later observation
→ explain what changed and why
```

## Work packages

### Package A — Truth core

Permanent IDs, aliases, content-addressed evidence, immutable events, book reducer, classified cash, NAV reconciliation, and replay skeleton.

### Package B — Decision vertical

Living Thesis Lite, Bull/Base/Bear ranges, admit/reject/abstain/cash outcomes, deterministic capital competition, portfolio aim, transition, order, and fill.

### Package C — Product closure

Launch/review/confirm/persist/reopen, read models, fixture orchestration, later-observation explanation, and authority synchronization.

Minimum seams:

`InstrumentId`, `EventId`, `EvidenceReference`, `PortfolioBookEvent`, `DecisionSnapshotId`, `PortfolioAimId`, `OrderId`, `FillId`, `CertificationId`.

## Score

Canonical shipped score remains `39/100`. Observed comparisons remain `0`. No alpha claim.

| Dimension | Current | After first vertical | After exact replay |
|---|---:|---:|---:|
| Product capability | 28 | 60–65 | 65–70 |
| User flow | 42 | 70–75 | 72–78 |
| Portfolio completeness | 18 | 65–70 | 70–75 |
| Integrity and replay | 64 | 70–75 | 90–95 |
| Prospective evidence | 10 | 20–30 | 30–40 |
| Shipping and custody | 78 | 85–90 | 90–95 |
| Weighted audit maturity | ≈39 | 62–66 | 70–74 |

Forecasts are nonbinding. Operational evidence is binary:

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      0/1
Prospective later observation      0/1
Exact deterministic replay         0/1
Bounded repeated portfolio         0/1
```

## Audit reconciliation

| Prior claim | R0 disposition |
|---|---|
| Roadmap PASS/frozen | repaired and banked; independent audit still required |
| Slices 0–7 frozen | corrected to seven product slices plus internal R0 |
| Slices 0–2 authorized | corrected to first vertical and replay after audit |
| 24 changed paths | original candidate had 26 paths |
| isolated worktree | retained |
| root untouched | retained |
| B0–B6 parallel | conceptual ownership retained; execution grouped into three packages |
| replay before scale | retained |
| Phase 66 active bridge | removed from active authority |
| authority synchronized | repaired across all active surfaces |
| Thin SAW PASS | retained as historical structural evidence and explicitly superseded |
| context validation | must pass with explicit active brief |
| create next worktree from `93e7a55` | rejected |
| correct base | exact audited `ROADMAP_FREEZE_COMMIT` |
| score uplift | none |
| decision needed | none for R0; independent audit gates implementation |

## Validation boundary

The isolated worktree has no repository `.venv`. Local validation uses the available system Python 3.12 and must be reproduced independently in a canonical environment before implementation begins.

## Root checkout

`E:\Code\Quant` remains massively dirty and is not execution or publication authority. Do not clean, revert, or use it for implementation in this programme without separate authorization.

## Next action

```text
independently reproduce commit, remote, tests, context validation, and clean status
→ after PASS, create clean isolated worktree from ROADMAP_FREEZE_COMMIT
→ ship GV-MICRO-PORTFOLIO-VERTICAL-0
```
