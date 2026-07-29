# Observability Pack — Current

## Active — Safe pushed candidate and external-audit sentinels (2026-07-29)

- **Authority sentinel:** `docs/context/ACTIVE_BRIEF` selects the Slice 0 brief explicitly.
- **Audit-target sentinel:** commit `f64cadcb2a9aaf0708744099ddc03ea2c41617eb`; tree `8c6dc88543847a06268b83db0dd68ea7f5fb12c1`; origin equality PASS.
- **Ancestry sentinel:** candidate descends from audited R0 commit `1db2501`.
- **Custody sentinel:** permanent IDs, evidence, and events have one low-level authority; duplicate semantics are prohibited.
- **Product sentinel:** four-security operator loop is complete under `gv_portfolio_v0`.
- **Accounting sentinel:** split residual `0`; terminal NAV `1499`; valuation-pending never invents NAV.
- **Environment sentinel:** Python 3.12.10, pytest 9.0.2, Streamlit 1.54.0, jsonschema 4.26.0.
- **Regression sentinel:** focused matrix 282/282 PASS.
- **Replay sentinel:** exact shadow replay, correction/partial-fill/valuation cases pass.
- **Independence sentinel:** self-asserted receipts are rejected; three distinct reviewer accounts are required.
- **Provider sentinel:** repository, candidate commit/tree, GitHub identities, and exact report bytes are preflight checks only; local terminal promotion is absent.
- **Claim sentinel:** score 39, real prospective evidence 0, no alpha/live claim.
- **Sequence sentinel:** independent Slice 0 audit → external acceptance → terminal replay certification → bounded portfolio.
- **Root sentinel:** dirty source checkout remains at `accef5c6` with 5,600 entries and was untouched.
- **Drift sentinel:** do not reopen providers, PEAD, legacy queues, optimizer/copula/graph/adaptive execution, tax/FX/derivatives/shorting, broker, score uplift, alpha, or live capital.

## Rating

- GREEN: candidate custody, product loop, accounting, persistence, operator UX, pinned environment, replay shadow, safe provider preflight, regression matrix.
- AMBER: independent Reviewer A/B/C reports.
- RED: terminal replay certification, real prospective evidence, bounded portfolio, alpha evidence, and live capital remain unproven or unauthorized.
