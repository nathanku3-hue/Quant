# Dashboard Product Spec — All-Capital PIT Operator Surface

Status: `ACTIVE — FINAL PLANNING ROUND`
Date: 2026-08-03
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`
Planning checklist: `docs/architecture/dashboard_all_capital_pit_planning_checklist.md`

## Purpose

The dashboard is the strategy consumer, comparator, and operator surface for one certified point-in-time capital decision. It does not own strategy logic, proposal identity decisions, event acceptance, portfolio calculation, or mutation.

## Product questions

```text
What exact book/evidence/market state is being evaluated?
Which real proposals entered that same PIT?
Which were accepted or identity rejected, and why?
Where do proposals disagree?
What evidence or discriminator is missing?
What capital and classified cash are currently certified?
Can the governance event stream and read model replay exactly?
What later operator action is unavailable or pending?
```

## Slice 1 product flow

```text
real MU operated object
+ real MU shadow object
+ certified-book cash
→ verified adapters
→ immutable proposals
→ typed submission handler
→ accepted/rejected ordered events
→ deterministic read projection
→ read-only Command Center
```

## Required Slice 1 behaviors

- one exact five-field PIT identity is visible;
- MU-operated, MU-shadow, and cash-baseline rows are real production-adapter outputs;
- identity rejection is event-backed;
- proposal rows are canonically ordered;
- current capital, disagreement, evidence gaps, and compact health are visible;
- full event/projection diagnostics are accessible through Operations & Replay;
- session state is limited to ephemeral UI controls;
- existing research/replay/optimizer surfaces are visibly non-authoritative.

## Explicitly unavailable in Slice 1

```text
proposal selection
composite target resolution
optimizer or risk engine
transition preview
authorization
book mutation
certification change
path deletion
```

The UI must represent these as unavailable future capabilities rather than simulated controls.

## Later product flow

Slice 2 adds intent-aware selection and target conflict handling. Slice 3 adds calculation-only preview, stale-bound authorization, application, certification, and exact authority replay.

## Product quality bar

The slice is not complete when contracts or pages compile independently. It completes only when the real three-proposal episode renders through `dashboard.py`, identity rejection replays from ordered events, and negative-authority checks prove no hidden selection/mutation path.
