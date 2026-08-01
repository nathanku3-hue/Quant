# Multi-Stream Contract — Current

Date: 2026-08-01
Active phase: `GV-OPERATED-PORTFOLIO-25-1`
Canonical authority: `docs/context/gv_endgame_authority_current.md`
Status: `AUTHORIZED; IMPLEMENTATION_ACTIVE; NOT_FROZEN`

## Ownership boundaries

| Logical stream | Owned result | Current state |
|---|---|---|
| Scenario and thesis | declarative retained 10- and new 25-security identities, evidence, reviews, observations | implemented; focused tests green |
| Allocation | dynamic competition over all scenario identities and selected-funded authority | implemented; 10/25 tests green |
| Execution/accounting | exact target-delta BUY/SELL execution and reconciled book | reused shared primitives; green |
| Persistence/replay | one scenario-bound envelope, restart, certification, correction | implemented through shared storage; green |
| Product/UI | dynamic summary-first and exceptions-first four-action flow | implemented through one app/view; AppTests green |
| Integrator | path ownership, CI, context, pre-freeze evidence, candidate freeze | active; terminal gates open |

These are logical boundaries, not a requirement for six workers. Default execution is one implementer. Parallel work is permitted only for genuinely disjoint tasks after shared interfaces are fixed.

## Coordination law

- Checkpoint genericization has no independent acceptance status.
- The first admissible proof is the 25-security scenario running through the same path while the retained ten-security regression remains green.
- One engine, persistence implementation, schema family, app, and view stack only.
- Sessions, cells, runs, slots, and copied portfolios do not satisfy security breadth.
- Focused tests run during implementation; terminal full comparison and independent A/B/C run once against one frozen candidate.
- Limited Live remains closed.

## Current bottleneck

Pre-freeze completeness: reconcile current authority, retain ownership/CI/dependency/evidence receipts, run broad local validation, and freeze exactly one candidate. Hosted exact-head and independent terminal review have not started.
