# PHASE_QUEUE.md — GodView Product Queue

Status: `ONE ACTIVE GATE; FINAL PLANNING FROZEN; LIVE CLOSED`
Last updated: 2026-08-03
Canonical authority: `docs/context/gv_endgame_authority_current.md`
Active brief: `docs/context/ACTIVE_BRIEF` → `docs/phase_brief/gv-dashboard-all-capital-pit-1-brief.md`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`
Planning checklist: `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`

## Queue law

1. One active product gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`.
2. Preserve accepted terminals and hosted-green evidence unchanged.
3. Bank the current same-evidence MU shadow work before dashboard implementation.
4. Build the portfolio-wide PIT pipeline; MU is only the first real case.
5. Work layer-first: contracts → verified adapters → command handler → ordered events → projector → dashboard.
6. Layers 1–6 form one functional Slice 1 transaction and cannot be banked as disconnected frameworks.
7. `dashboard.py` remains the sole future GodView application.
8. Pages are read projections, not business authority.
9. Identity decisions belong to the command handler; the projector is a pure fold.
10. Preview is calculation-only; authorization, application, and certification are separate facts.
11. Multiple absolute targets are not summed; later composition is zero/one base target plus compatible deltas/overlays.
12. Delete legacy paths only after path existence, dependency, behavior, and regression proof.
13. Limited Live remains closed and unauthorized.

## Active execution queue

| Order | Gate | Status | Exit result |
|---:|---|---|---|
| 0 | Bank same-evidence MU shadow baseline | Pending | Focused tests green; exact five code/test paths committed; no tag; no unrelated paths |
| 0D | Bank final planning authority | Pending after Gate 0 | Status/context refreshed; docs-only commit; fully clean worktree |
| 1A | Immutable PIT/proposal contracts | Authorized within Slice 1 | Five-field identity, evidence/digest, normalized targets, strict extension envelopes |
| 1B | Verified real adapters | Authorized within Slice 1 | MU operated/shadow and book-derived cash map without fabricated files/fields |
| 1C | Governance command authority | Authorized within Slice 1 | Handler emits accepted or identity-rejected events with complete proposal |
| 1D | Ordered event authority | Authorized within Slice 1 | Sequence/digest chain, duplicate/gap rejection, canonical reads |
| 1E | Pure projector/read models | Authorized within Slice 1 | Event-backed statuses only; canonical ordering; exact replay |
| 1F | Six-page shell + read-only Command Center | Authorized within Slice 1 | Real three-row PIT episode renders; no raw UI authority or mutation |
| 2 | Selection + intent-aware composition | Planned | Reject all; one base target; compatible delta/overlay legs; replayable selection |
| 3 | Preview + confirmation + certification + replay | Planned | Multi-model risk/cost receipt; stale-preview rejection; separate authority events |
| 4 | Placement, extraction, conditional deletion | Deferred | One dashboard path; displaced paths proven unused and removed |
| 5 | 3–5 real identities and independent modules | Deferred | Repeated operated evidence; no fixture inflation |
| 6 | CTA/macro/cascade modules | Closed until Gate 5 | Neutral seam reused without core/domain leakage |
| 7 | Limited Live | Closed | Separate explicit authorization only after evidence/legal/operational gates |

## Slice 0 exact code/test authority

```text
M  gv_portfolio_v0/prospective.py
M  views/gv_prospective_paper_workspace.py
M  tests/gv_portfolio_v0/test_real_evidence_mu.py
A  core/gv_v2_mu_nvda_shadow_decision.py
A  tests/gv_portfolio_v0/test_same_evidence_shadow.py
```

No documentation file enters the baseline commit. No tag is created.

## Slice 1 capability bill of materials

Expected source areas:

```text
core/gv_pit/ contracts
core/gv_pit/ verified adapters
core/gv_pit/ commands + handler
core/gv_pit/ events + event store/adapter
core/gv_pit/ projector + read models
dashboard.py
views/page_registry.py
views/command_center.py
focused tests and AST authority-state scanner
```

Exact paths are reconciled in the first execution round. No listed component is independently accepted; Slice 1 passes only as the complete real read-only episode.

## Slice 1 hard stop

```text
zero selection
zero target composition
zero optimizer
zero risk math
zero preview
zero authorization
zero book mutation
zero certification change
zero deletion
```

## Immediate next action

Run the two focused MU test modules in the approved Python 3.12 environment. If green, commit exactly the five baseline paths with no tag. Update status/custody fields, regenerate context, and bank the final planning authority separately as docs-only. Verify a fully clean worktree, then inspect exact operated/book/event fields and execute Slice 1 Layers 1–6 without another broad planning round.
