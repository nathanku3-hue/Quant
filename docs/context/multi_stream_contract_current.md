# Multi-Stream Contract — Current

## Active — External audit handoff for safe pushed candidate (2026-07-29)

Audit target: commit `f64cadcb2a9aaf0708744099ddc03ea2c41617eb`; tree `8c6dc88543847a06268b83db0dd68ea7f5fb12c1`.

| Stream | Ownership | Current state | Hard handoff |
|---|---|---|---|
| Truth core | IDs, exact-byte evidence, immutable events, book, classified cash, NAV | implemented and pushed | canonical event ledger and reconciled book |
| Decision vertical | thesis/scenarios, outcomes, competition, aim, order/fill | implemented and pushed | immutable decision snapshot and execution records |
| Product closure | launch/review/confirm/certify/persist/reopen/WATCH explanation | implemented and pushed | operator-complete workspace |
| Replay shadow | exact reconstruction, corrections, partial fills, certification-chain verification | implemented and pushed | independent reports before terminal certification |
| Provider preflight | origin repository, commit/tree, account identity, exact report bytes | implemented, non-authorizing | external authority decides terminal certification |
| Independent audit | Reviewer A strategy, B runtime, C data integrity | external and pending | exact receipt-bound reports |

## Frozen seams

`InstrumentId`, `EventId`, `EvidenceReference`, `PortfolioBookEvent`, `DecisionSnapshotId`, `PortfolioAimId`, `OrderId`, `FillId`, and `CertificationId`.

## Coordination laws

- `contracts/gv_portfolio/v0` and `core/gv_portfolio_v0` are the single low-level custody authority.
- `gv_portfolio_v0.vertical` orchestrates the bounded product and may not create competing custody semantics.
- Structural receipts and provider preflight cannot mint terminal certification locally.
- Three reviewer accounts must differ from the implementer and from each other. Natural personhood is not claimed.
- Released FS0 remains substrate and cannot reclaim active product queue authority.
- Bounded portfolio remains blocked by external replay certification.

## Current bottleneck

Obtain independent Reviewer A/B/C reports against the exact pushed candidate. No additional product implementation stream is needed before that evidence arrives.
