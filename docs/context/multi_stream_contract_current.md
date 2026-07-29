# Multi-Stream Contract — Current

## Active — Three-package micro-portfolio execution (2026-07-29)

| Package | Ownership | Parallel boundary | Hard handoff |
|---|---|---|---|
| A — Truth core | permanent IDs, evidence, immutable events, book reducer, classified cash, NAV, replay API skeleton | owns disjoint truth/accounting paths after minimum seams freeze | reconciled book and replayable event log |
| B — Decision vertical | Living Thesis Lite, scenarios, admission, capital competition, aim, transition, paper order/fill | consumes Package A IDs/events; cannot invent alternate lineage | certified portfolio aim and fill events |
| C — Product closure | launch/review/confirm/persist/reopen, read models, acceptance fixture, later-observation explanation, docs/ops | consumes A/B read models; cannot mutate certified truth directly | operator-complete vertical and synchronized authority |

## Minimum frozen seams

`InstrumentId`, `EventId`, `EvidenceReference`, `PortfolioBookEvent`, `DecisionSnapshotId`, `PortfolioAimId`, `OrderId`, `FillId`, and `CertificationId`.

## Coordination laws

- One product authority only: `GV-MICRO-PORTFOLIO-VERTICAL-0` after independent R0 audit PASS.
- Maximum parallelism means independent executable work, not maximum worker or branch count.
- A package may run separately only when it owns disjoint files, uses exercised seams, can merge independently, and does not force global redesign on failure.
- Detailed fields freeze only when the operator fixture exercises them.
- Replay builds early from real vertical events; replay certification is the immediate next slice.
- Learn work remains shadow-only and cannot mutate the certified book or create competing authority.
- Cross-package blockers are limited to P0/P1 custody, accounting, mandate, mandatory-action, or replay defects.

## Current bottleneck

Independent audit must confirm the banked R0 authority before any implementation worktree is created.
