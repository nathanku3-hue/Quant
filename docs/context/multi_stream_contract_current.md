# Multi-Stream Contract — Current

Date: 2026-07-30
Active product phase: `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` only
Canonical authority: `docs/context/gv_endgame_authority_current.md`

## Execution topology

| Stream | Ownership | Independent output | Hard handoff |
|---|---|---|---|
| Instrument/thesis | ten permanent identities, two clusters, unique evidence, Living Thesis Lite, dispositions | complete heterogeneous review set | ten validated instrument records and reviews |
| Allocation | competition across all ten, funded set, changed target quantities, residual cash | deterministic initial and transition decisions | content-addressed decision snapshots |
| Execution/accounting | BUY, SELL/REDUCE, orders, fills, costs, positions, cash, NAV | one reconciled portfolio event stream | exact book with zero unexplained residual |
| Persistence/replay | atomic envelope, restart/reopen, replay, idempotence, correction lineage | verified persisted workspace and replay proof | byte-stable certification chain |
| Product | review, confirm, no-change, transition, changed-why | black-box Streamlit operator flow | fresh-checkout AppTest result |
| Integrator | one acceptance fixture, focused tests, terminal failset, evidence | one immutable terminal candidate | candidate SHA for A/B/C |

## Coordination law

- One active product phase; no parallel product phases.
- Streams may work in parallel only on disjoint ownership with an executable handoff.
- Every stream inherits the exact product result and quantitative bounds from the active brief.
- Sessions, cells, runs, and slots cannot satisfy instrument-count acceptance.
- Reviewer A may reject product acceptance even when accounting and custody reviewers pass.
- Focused checks run during implementation; full regression/failset and independent A/B/C run once at the frozen terminal candidate.
- Existing Scale, Universe, and Challenger APIs are validation harnesses, not compatibility contracts.
- Limited Live remains closed.

## Frozen seams

`InstrumentId`, `EvidenceReferenceId`, `DecisionSnapshotId`, `PortfolioAimId`, `PortfolioBookEvent`, `OrderId`, `FillId`, `CertificationId`, classified cash buckets, declared decimal precision, and content-addressed workspace envelopes.

## Current bottleneck

The implementation candidate executes under system `python3`, but terminal progress is blocked by the absent pinned Python 3.12 pytest/Streamlit environment. Restore that environment, run focused tests, and repair this slice before freezing the candidate.
