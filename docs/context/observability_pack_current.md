# Observability Pack — Current

Date: 2026-08-01
Active phase: `GV-OPERATED-PORTFOLIO-25-1`
Status: `IMPLEMENTATION_CHECKPOINT; NOT_FROZEN; NOT_TERMINAL`

## Product sentinels

- **Authority:** `ACTIVE_BRIEF` selects the authorized 25-security phase; accepted score remains `62/100`.
- **Shared path:** retained 10 and new 25 scenarios import the same operated engine and storage implementation and render through the same app/view stack.
- **Identity:** exactly 25 unique permanent IDs and keys in the active scenario.
- **Ownership:** every review retains its instrument-owned evidence; cross-instrument rebinding fails closed.
- **Breadth:** exactly one book; no session/cell/run/slot or copied portfolio counts as a security.
- **Competition:** one candidate row per identity, exactly once.
- **Funding:** multiple positive positions and classified residual cash.
- **No-change:** orders, fills, holdings, cash, NAV, and book hash remain unchanged.
- **Transition:** at least one SELL/REDUCE and one BUY/FUND derived from target deltas.
- **Accounting:** cash and positions nonnegative; unexplained residual `0`.
- **Replay/correction:** exact reconstruction, certification history replay, and append-only non-economic correction.
- **Persistence:** scenario-bound atomic envelope rejects linked-ancestor escape and reloads equivalent state.
- **Product UI:** summary-first and exceptions-first confirm → no-change → transition → correction → fresh-process reopen within four actions.
- **Regression:** retained ten-security behavior remains green.

## Evidence sentinels

Current local checkpoint:

- focused shared 10/25 domain and AppTest: `23/23 PASS`;
- complete operated package: PASS in bounded groups;
- complete FS0 package: PASS in bounded groups;
- context/authority set: PASS before regenerated context validation.

Required before candidate freeze:

- changed-path/test ownership receipt;
- complete CI path-trigger review;
- exact-head checkout review;
- dependency and `pip check` receipt;
- base/candidate failset method;
- evidence destination outside checkout.

Required after freeze:

- exact-head hosted Windows and Linux;
- one controlled base/candidate full-suite comparison;
- independent Reviewer A/B/C;
- documentation-only closure preserving the tested executable tree.

## Current signal

- **GREEN:** shared-path architecture, 10/25 focused behavior, bounded actions, accounting, replay, correction, persistence, and local AppTests.
- **AMBER:** branch/candidate identity, regenerated current context, pre-freeze receipts, hosted parity, full failset, and independent review remain open.
- **RED:** none currently demonstrated.
- **STOP:** any parallel engine/storage/view path, weakened ten-security behavior, ownership drift, accounting/replay/restart failure, candidate-only regression, or scope widening.
