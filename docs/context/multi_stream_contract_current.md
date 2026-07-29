# Multi-Stream Contract — Current

## Active — Candidate custody and external audit handoff (2026-07-29)

| Stream | Ownership | Current state | Hard handoff |
|---|---|---|---|
| Truth core | IDs, exact-byte evidence, immutable events, book, classified cash, NAV | implemented and pinned | canonical event ledger and reconciled book |
| Decision vertical | thesis/scenarios, outcomes, competition, aim, order/fill | implemented and pinned | immutable decision snapshot and execution records |
| Product closure | launch/review/confirm/certify/persist/reopen/WATCH explanation | implemented and pinned | operator-complete workspace |
| Replay/certification | exact reconstruction, corrections, partial fills, certification chain | implemented; shadow evidence bankable | verified external receipts before certification |
| Independent audit | Reviewer A strategy, B runtime, C data integrity | external and pending | exact candidate commit/tree/report receipts |

## Frozen seams

`InstrumentId`, `EventId`, `EvidenceReference`, `PortfolioBookEvent`, `DecisionSnapshotId`, `PortfolioAimId`, `OrderId`, `FillId`, and `CertificationId`.

## Coordination laws

- `contracts/gv_portfolio/v0` and `core/gv_portfolio_v0` are the single low-level custody authority.
- `gv_portfolio_v0.vertical` orchestrates the bounded fixture and may not create competing custody semantics.
- Replay may produce shadow evidence before audit, but cannot issue terminal certification without verified receipts.
- Structural receipt validation is insufficient; the certification CLI verifies GitHub account identity and exact report bytes at the submitted commit.
- Three reviewer accounts must differ from the implementer and from each other. Natural personhood is not claimed.
- Detailed fields freeze only when exercised by the operator/replay fixtures.
- Released FS0 remains substrate and cannot reclaim active product queue authority.
- Bounded portfolio remains blocked by replay certification.

## Current bottleneck

Bank and push one exact clean candidate, then obtain independent Reviewer A/B/C receipts. No additional product implementation stream is needed before that evidence arrives.
