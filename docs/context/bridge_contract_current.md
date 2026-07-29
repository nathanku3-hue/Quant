# Bridge Contract — Current

- **ACTIVE_PHASE:** `GV-MICRO-PORTFOLIO-VERTICAL-0` only.
- **IMPLEMENTATION_STATE:** S2/S3/S4 and shared Integrator wiring are banked locally at the terminal branch tip.
- **AUTHORITY:** Strategy owns decisions; Execution owns transition/order/fill events; Accounting owns the deterministic book; Product owns orchestration and presentation only.
- **PRODUCT_DELTA:** the existing confirm → execute → certify → persist/reopen → later WATCH flow now consumes canonical cross-stream records and a reconciled PortfolioBook.
- **SCHEMA:** `gv_portfolio_v0_workspace_v2`; no compatibility adapter for superseded bytes.
- **VERIFICATION:** portfolio 82/82 PASS; frozen protocol 150/150 PASS; legacy product 259/263 PASS with four unrelated frozen-document failures.
- **BLOCKERS:** full repository collection lacks declared dependencies; independent audit has not run against the remote terminal SHA.
- **SCORE:** shipped product score remains **39/100**; observed remains **0**; no alpha or live-capital claim.
- **OPEN_DECISION:** none. The next action is mechanical custody and audit, not feature selection.
- **RECOMMENDED_NEXT_STEP:** repair the declared full-suite environment and audit the exact remote terminal SHA.
- **DO_NOT_START:** Product feature work, Replay implementation, providers, WRDS, broad loaders, optimizer/copula/graph/adaptive execution, broker, score uplift, or live capital.
