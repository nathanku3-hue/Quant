# GodView Top-Level Roadmap — Layer First

Status: `ACTIVE`
Date: 2026-08-03
Accepted product score: `62/100`
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Canonical architecture: `docs/architecture/dashboard_all_capital_pit_contract.md`
Planning checklist: `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`

## Endgame

GodView is an all-capital point-in-time portfolio operating system:

```text
certified book/evidence/market identity
→ verified proposal adapters
→ immutable proposals
→ governed event acceptance
→ deterministic comparison
→ intent-aware transition selection
→ calculation-only portfolio preview
→ explicit authorization
→ applied and certified book events
→ exact replay and prospective learning
```

The dashboard is the sole operator product. Strategy logic remains inside strategy modules. MU is the first real case, not the system boundary.

## Layer map

| Layer | Authority | Current phase responsibility |
|---:|---|---|
| 0 | Accepted custody and baseline | Preserve accepted book/evidence/replay; bank the current five-file MU shadow baseline |
| 1 | Immutable contracts | Five-field PIT identity, evidence references, normalized targets, strict envelopes, proposal |
| 2 | Verified adapters | Real MU-operated, MU-shadow, and certified-book cash translation; no invented serialization |
| 3 | Governance commands | Identity decision and accepted/rejected event emission |
| 4 | Ordered event authority | Stream order, digest chain, append/read, duplicate/gap rejection |
| 5 | Read projections | Pure deterministic proposal/episode projector and canonical ordering |
| 6 | Dashboard product | Six-page shell and read-only Command Center through `dashboard.py` |
| 7 | Selection/composition | Reject all, select one base, add compatible deltas/overlays |
| 8 | Portfolio authority | Risk/cost preview, stale-bound authorization, application, certification, replay |
| 9 | Consolidation/expansion | Content placement, proven deletion, repeated operation, independent modules, later Live gate |

Layers 1–6 are implemented as one Slice 1 product transaction. They are not separate framework milestones.

## Phase 0 — Bank the current shadow baseline

Verify and commit the current five-path MU operated-versus-shadow slice unchanged. It is a recovery point and real adapter source, not a release, tag, generic pipeline, or score event.

Exit gate:

```text
focused same-evidence and real-MU tests pass
+ exactly five code/test paths committed
+ no documentation or unrelated path in the baseline commit
+ no Git tag
+ planning status/context updated and banked separately as docs-only
+ fully clean worktree before Slice 1 edits
```

## Phase 1 — Real read-only all-proposal PIT transaction

Implement Layers 1–6 in dependency order:

```text
immutable contracts
→ verified real adapters
→ typed submission commands and identity handler
→ ordered append-only event envelope/store protocol
→ pure deterministic projector/read models
→ six-page registry
→ read-only Command Center
```

Required operated result:

- one certified five-field PIT identity;
- real MU-operated proposal row;
- real MU-shadow proposal row;
- cash baseline derived from certified book cash;
- accepted/identity-rejected event-backed status;
- canonical proposal row ordering;
- disagreement/evidence gaps/current capital/compact health visible;
- no fabricated production proposal row;
- no raw session-state governance authority;
- no selection, optimization, risk math, preview, mutation, certification change, or deletion.

Exit gate:

```text
contracts/digests/normalization tests
+ real adapter mapping tests
+ five-field command-handler rejection tests
+ event sequence/digest/duplicate/gap tests
+ deterministic projector/replay tests
+ six-page registry tests
+ Command Center AppTest
+ AST authority-state gate
+ mutation/optimization/deletion absence proof
```

## Phase 2 — Deterministic selection and intent-aware composition

Add:

- reject-all/no-action;
- zero or one base `TARGET_FINAL`;
- zero or more compatible `DELTA`/`OVERLAY` legs;
- explicit per-target acceptance or override;
- deterministic normalization and collision handling;
- command/event vocabulary for selection and abort.

Joint optimization remains a research challenger. Decision consensus still owns no portfolio risk/cost math.

Exit gate: selection is deterministic and replayable; overlapping absolute targets fail closed; no preview or book mutation occurs.

## Phase 3 — Preview, authorization, application, certification, replay

Add:

- portfolio target resolution against the current certified book;
- cost, liquidity, cash, concentration, margin, and multi-model risk receipts;
- immutable calculation-only `TransitionPreview`;
- current-book/head, digest, and expiry binding;
- explicit operator authorization event;
- separate application and certification events;
- exact authority replay.

Exit gate: stale/changed/expired/blocked previews cannot authorize; confirmation cannot bypass portfolio authority; replay reconstructs exact result.

## Phase 4 — Content placement, extraction, and proven deletion

Mount current decisions, certified portfolio, strategy research/replay, and operations under their final pages. Extract only exercised boundaries.

Delete only when:

```text
path exists
+ dependency scan shows zero active callers
+ dashboard behavior owns the displaced journey
+ focused/regression tests pass
+ rollback is recorded
```

`operated_portfolio_app.py` is the verified standalone candidate; no deletion is authorized yet.

Exit gate: one production path through `dashboard.py`, zero duplicate authority, lower state ambiguity, and deletion evidence.

## Phase 5 — Repeated real operation

Run the same PIT loop across 3–5 real identities and at least one genuinely independent module. Measure disagreement, operator disposition, capital consequences, costs, and replay fidelity.

Exit gate: prospective episodes are real rather than fixture-inflated; independent terminal review passes; any score uplift is evidence-gated.

## Phase 6 — New strategy modules

Add CTA, macro, microstructure, or cascade modules only through the frozen proposal and extension seam. Domain data, formulas, diagnostics, and sizing remain inside each module. Neutral core receives resolved targets and risk constraints.

Exit gate: a new module competes at the same PIT identity without changing dashboard, command, event, projection, or portfolio-authority semantics.

## Phase 7 — Separately authorized Limited Live

Consider only after repeated cost-adjusted paper operation, exact replay, custody stability, independent replication, legal review, operational ownership, and explicit owner authorization.

Limited Live remains closed.

## Immediate order

```text
Phase 0: test and bank five-file baseline
→ bank final planning authority separately as docs-only and verify clean tree
→ Phase 1: contracts → adapters → handler → events → projector → dashboard
→ stop at read-only Command Center
```

No broad architecture round precedes Phase 1. Field-level repository reconciliation is allowed; strategy expansion, risk implementation, broker work, and deletion are not.
