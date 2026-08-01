# Impact Packet — Current

Date: 2026-08-01
Active phase: `GV-OPERATED-PORTFOLIO-25-1`
Base: terminal `main` at `2349e1bd91d9b4036f3956c52ce7bbf66a9c2c1e`
Status: `IMPLEMENTATION_CHECKPOINT; NOT_FROZEN; NOT_TERMINAL`

## Product impact

The active checkpoint evolves the accepted operated product from one hard-coded ten-security fixture into one shared scenario-driven path:

- retained ten-security regression scenario;
- new 25-security product scenario;
- exactly one portfolio book per workspace;
- one capital competition covering every scenario identity exactly once;
- multiple funded positions and classified residual cash;
- explicit no-change, real SELL/REDUCE plus BUY/FUND transition, correction, persistence, replay, and fresh-process reopen;
- summary-first and exceptions-first presentation;
- no more than four required operator actions.

## Architecture impact

Changed shared paths:

- `gv_portfolio_v0/operated.py`: derives identity, review, transition, validation, and changed-why expectations from a declarative scenario;
- `gv_portfolio_v0/operated_storage.py`: uses one scenario-bound envelope and shared persistence implementation;
- `views/gv_operated_portfolio_workspace.py`: renders dynamic counts, cluster summaries, exceptions, and scenario-specific actions;
- `operated_portfolio_app.py`: selects a declarative scenario through environment configuration;
- `gv_portfolio_v0/operated_scenarios.py`: owns retained 10- and new 25-security scenario data;
- `launch_operated_portfolio_25.py`: thin scenario-selecting launcher only.

No second domain engine, persistence implementation, schema family, application, or view stack was created. Shared book, execution, and replay primitives remain reused.

## Test impact

- retained ten-security tests remain the compatibility contract;
- cloned-text rejection was replaced by the approved ownership rule: cross-instrument rebinding fails, while identical content is legal with explicit ownership and independent canonical identity;
- `tests/gv_portfolio_v0/test_operated_25.py` proves 25 identities, ownership, one competition, bounded actions, accounting, replay, persistence isolation, correction, and fresh-process AppTest;
- CI path ownership includes the scenario module, 25-security launcher, new phase brief, and shared changed paths.

## Current evidence

- focused shared 10/25 domain and AppTest: `23/23 PASS`;
- complete operated package: PASS in bounded groups;
- complete FS0 product package: PASS in bounded groups;
- context/authority tests: PASS before regenerated packet validation;
- manual shared-path flow: 25 draft → 8 funded → no-change → SELL+BUY → correction; residual `0`.

These are local checkpoint results only. No candidate SHA, hosted exact-head run, controlled full failset comparison, or independent terminal review exists yet.

## Boundary

Accepted endgame progress remains `62/100`. Providers, optimizer, broker, Universe, Challenger, Limited Live, live capital, historical harness compatibility, and repository-wide dependency repair remain excluded.
