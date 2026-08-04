# Phase Brief — GV-OPERATED-PAPER-CAPITAL-1

Date: 2026-08-04
Mode: `EXECUTION_PACKET`
Status: `ISOLATED CLOSURE COMPLETE; OWNER OPERATION COMPLETE; REVIEWER A/B/C PASS; READY TO PUBLISH`
Accepted product score: `62/100` — unchanged
Limited Live: `CLOSED`
Base authority: `2d95cdf9e033f7d8b6f1d9c18aea2e46bed6ec72`
Closed Slice 1 executable: `879cc04d7b79b05e6a8f3643595c1f043f6b89d8`
Frozen cascade research branch: `codex/gv-financial-cascade-shadow-0-r2@a68ba8e621c0c0155fbc41a158e122f346638af6`

## Objective

Operate one genuine non-zero MU paper-capital decision through the default GodView Command Center:

```text
owner-authored evidence + identified market packet
→ mutation-free preview
→ explicit confirm or reject
→ atomic persistence
→ certification
→ fresh-process reopen and exact replay
→ changed active book visible in Command Center
```

This is the sole immediate score-bearing product gate. Code fixtures prove implementation only; they do not complete the product milestone or change the accepted score.

## Locked design

- Preserve historical `GV_REAL_EVIDENCE_MU_PORTFOLIO_1` unchanged.
- Add separate forward scenario `GV_OPERATED_PAPER_CAPITAL_1`.
- Render active persisted paper authority first and the banked no-market Slice 1 comparison second.
- Label the banked comparison as historical; never represent it as the current market-aware active book after a BUY.
- Reuse existing preview, rejection, confirmation, atomic persistence, certification, and replay paths.
- Admit BUY-only only as `PROSPECTIVE_CASH_FUNDED_ENTRY` when the certified book has zero funded positions, all legs are BUY, one exact instrument/price/quantity packet is bound, cash covers notional plus fee, and residual remains zero.
- Keep ordinary and post-entry transitions subject to the existing SELL-plus-BUY rebalance rule.
- Treat owner market-source identity as a content-addressed operator assertion, not provider verification, alpha evidence, advice, broker authority, or live authority.

## Implemented candidate

Production:

```text
M gv_portfolio_v0/operated_scenarios.py
M gv_portfolio_v0/prospective.py
M gv_portfolio_v0/operated_storage.py
M views/command_center.py
M core/gv_fs0_canonical.py
M gv_portfolio_v0/allocation.py
M gv_portfolio_v0/book.py
M gv_portfolio_v0/execution.py
A gv_portfolio_v0/decimal_utils.py
```

Tests:

```text
A tests/test_gv_pit_operated_capital.py
M tests/test_dash_1_page_registry_shell.py
M tests/test_gv_pit_transaction.py
A tests/test_gv_pit_operated_capital.py
```

Implemented behavior:

- typed `ForwardOperatedDecisionPacket`;
- positive canonical decimal price validation;
- evidence and market timestamps bound after current authority;
- market time cannot follow decision admission time;
- exact instrument, market source identity, price, quantity, claim, and rationale included in proposal identity;
- admitted price becomes order/fill price;
- mutation-free preview exposes resulting positions, classified cash, costs, NAV, book hash, and residual;
- confirmation persists through the existing confined atomic envelope and issues a new certification;
- rejection preserves book authority;
- exact reconstruction after reopen;
- typed PIT identity tuple is persisted with the active forward packet and cross-bound to
  the outer request/update;
- per-workspace lock serializes public load/write and compound load/compute/replace paths
  while atomic replacement remains the only write primitive;
- request, text, review, episode, event, and persisted-workspace bounds fail closed;
- canonical persisted bytes, inner/outer scenario identity, envelope shape, Decimal
  exponent/magnitude, money precision, and hostile ambient Decimal contexts fail closed;
- Command Center discards stale previews and stores no workspace/book/certification authority in session state.

## Acceptance checks

- [x] Historical real-MU scenario remains unchanged.
- [x] Forward scenario starts from certified classified cash and zero positions.
- [x] Non-zero BUY-only preview is admitted only under the bounded empty-book rule.
- [x] Insufficient cash fails closed.
- [x] Preview does not mutate memory or persistence.
- [x] Rejection leaves book authority unchanged.
- [x] Confirmation creates one BUY order/fill/position, reduced cash, classified fee, and zero residual.
- [x] Fresh-process load and exact reconstruction reproduce the confirmed workspace.
- [x] Post-entry single-sided top-up remains rejected.
- [x] Default Command Center renders active authority before the immutable historical comparison.
- [x] Focused engine, UI, PIT, dashboard, and legacy prospective regressions pass locally.
- [x] Exact candidate is moved to `codex/gv-operated-paper-capital-1-custody` from base `2d95cdf` without advancing the closed Slice 1 branch.
- [x] Full terminal Reviewer A/B/C closure passes against the final changed bytes.
- [x] Context packet build and validation pass after documentation reconciliation.
- [x] One fresh owner-authored packet is previewed and explicitly confirmed through the production Command Center interaction surface.
- [x] After confirmation, a separate process displays and reconstructs the changed certified book.
- [ ] Candidate is committed and pushed only after terminal review.

## Parallel cascade feasibility disposition

Read-only inspection found no governed PIT bilateral or institutional-network artifact in current Quant authority. The existing cascade branch contains synthetic/engineering-only evidence and explicit promotion blockers.

```text
DATA FAIL
→ preserve branch a68ba8e… unchanged
→ classify as inactive research evidence
→ remove cascade from the active alpha roadmap
→ no extension, integration, RegimeManager change, or capital authority
```

A later DATA PASS may extend the existing provider minimally only after exact source derivations are established. The provisional required core is source/availability identity, coverage/missingness, baseline/shock default and unpaid fractions, non-unique clearing, scenario/bundle identities, and staleness. Additional inferred fields are not mandatory.

## P0 risks

- Advancing the already-closed Slice 1 branch with new product bytes.
- Confirming a stale or mutated market packet.
- Treating operator-asserted price identity as independently verified market data.
- Representing the banked no-market comparison as the active post-BUY book.
- Treating the AppTest fallback as equivalent to manual browser control; the runtime limitation and fresh packet are recorded in the owner evidence.

## Forbidden scope

No generic proposal selection or composition, neutral PIT market-governance expansion, optimizer/risk model, provider acquisition, new event store, new persistence engine, cascade integration, cascade extension, RegimeManager modification, CTA/macro implementation, broker route, live capital, legacy deletion, or score uplift.

## What Was Done

- Implemented the bounded forward-operated cash-funded BUY vertical.
- Added focused and regression tests; all executed groups passed.
- Reran the expanded focused gate at `73/73` under Python 3.12.10 / pytest 9.1.0.
- Operated and separately reopened a fresh seven-unit MU owner packet at price `101.25`,
  with available cash `9289.25`, costs `2`, and residual `0`.
- Completed independent terminal Reviewer A/B/C closure with three PASS verdicts after
  canonical-byte, scenario-binding, Decimal-context, money-precision, and bounds fixes.
- Verified cascade custody and completed the read-only governed-data feasibility check as DATA FAIL.
- Preserved the accepted score at 62/100.

## What Is Locked

- Closed Slice 1 authority and historical real-MU semantics remain immutable.
- Cascade remains frozen at `a68ba8e621c…` and inactive.
- The new BUY-only rule applies only to the empty-book forward-operated scenario.
- Code readiness does not equal product completion.
- Limited Live remains closed.

## What Is Next

- Publish a new PASS closure report while preserving the historical SAW BLOCK report.
- Commit and push only the reviewed exact candidate on the isolated custody branch.

## First Command

```text
git status --short --branch
```

## Next Todos

- Close the independent A/B/C rerun (PASS/PASS/PASS).
- Retain the validated historical SAW BLOCK and add the isolated PASS closure.
- Publish only after review; keep score at 62/100.
