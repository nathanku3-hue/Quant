# researches.md

Last updated: 2026-02-18

## Existing Research Markdown Cross-Reference
Record all `researches*.md` files used for novelty checks.

| File | Domain | Scope | Last Checked | Notes |
|---|---|---|---|---|
| `docs/research/researches.md` | cross-domain | master index | 2026-02-18 | Initial bootstrap entry |
| `docs/research/README.md` | cross-domain | input/output contract | 2026-02-18 | Defines PDF naming and extraction contract |

## Findings Delta Log
Use one row per PDF reviewed.

| Date | Source PDF | Domain | Core Methodology | Core Findings | Delta vs Existing `researches*.md` | Logic Chain (1 line) | Formula (1 line) |
|---|---|---|---|---|---|---|---|
| YYYY-MM-DD | `<pdf name>` | `<scientific/financial/medical/law>` | `<one line>` | `<one line>` | `<new/conflict/confirm + one line>` | `<if A and B then C>` | `<explicit equation or N/A>` |
| 2026-02-18 | `N/A (no PDF reviewed in governance-only milestone)` | cross-domain | `N/A` | Initialized research cross-reference process | New process baseline only | if research evidence is required and no PDF exists then claim remains low-certainty | N/A |
| 2026-06-21 | `fama_1998_market_efficiency_long_term_returns.pdf` | financial | Reviews long-horizon abnormal-return methodology, cross-event correlation, return metrics, and calendar-time rolling portfolios | Calendar-time portfolio time-series variation captures cross-event correlation missed by the expected-return model; BHAR and ignored cross-correlation can distort inference | New direct support for selecting calendar-time aggregation while retaining strict model/sample caveats | if overlapping event returns are cross-correlated then aggregate active events in calendar time and infer from the portfolio time series, while preserving expected-return-model limits | `R_HL,t = alpha_CT + beta_M * mktrf_t + epsilon_t` is the repo's daily single-factor adaptation, not a formula prescribed by Fama |
