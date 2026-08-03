# Impact Packet — Current

Date: 2026-08-03
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Status: `BASELINE BANKED; DOCS CUSTODY PENDING; IMPLEMENTATION NOT STARTED`

## Product impact

The active unit changes from one MU approval flow to one portfolio-wide PIT decision episode. MU operated, MU shadow, book-derived cash, and future modules become peer proposals against one certified book.

## User-flow impact

Slice 1 default experience:

```text
Command Center
→ inspect one exact five-field PIT identity
→ inspect real MU-operated, MU-shadow, and cash proposal rows
→ inspect identity acceptance/rejection, disagreement, evidence gaps, and current capital
→ navigate to evidence, portfolio history, strategy research, or operational replay
```

Selection, preview, confirmation, and certification remain visibly unavailable until later slices.

## Architecture impact

- `dashboard.py` remains the sole future app.
- Six pages replace the current three-page endgame.
- Strategy output becomes immutable proposal evidence.
- Verified adapters translate active repository objects without new serialization paths.
- Identity acceptance occurs in a typed command handler.
- Governance facts use one bounded ordered digest-chained in-memory stream; Slice 1 adds no durable persistence.
- Proposal/episode state is projected deterministically from events.
- Portfolio calculation and mutation remain outside dashboard and Slice 1.
- Standalone paths are deleted only after repository-grounded proof.

## Repository-grounded findings

- `views/command_center.py` does not exist and is a new file.
- The operated source is the active prospective workspace/proposal path.
- The shadow source is `core/gv_v2_mu_nvda_shadow_decision.py`.
- Cash is present in the certified workspace/book; a standalone cash artifact is not assumed.
- The five-file same-evidence baseline is banked at `a520f475bfa4fca42a68a22165ab3ad8960c0bc9` after 9 focused tests passed.
- No production `market_snapshot_id` exists; Slice 1 must use the approved proof-carrying cash-only no-market identity or fail closed.
- Certified head must resolve to the final authoritative event in the exact certified prefix, not merely the last event array element.
- The verified standalone application path is `operated_portfolio_app.py`.

## Touched interfaces expected next

- current operated workspace/proposal schema;
- independent shadow decision schema;
- certified book/head/cash identity;
- decision-free evidence identity and proof-carrying cash-only no-market identity;
- bounded in-memory event ordering/digest conventions;
- dashboard registry and Streamlit composition root.

## Exact Slice 1 files

```text
core/gv_pit/__init__.py
core/gv_pit/contracts.py
core/gv_pit/adapters.py
core/gv_pit/governance.py
core/gv_pit/read_models.py
views/command_center.py
views/page_registry.py
dashboard.py
tests/test_dash_1_page_registry_shell.py
tests/test_gv_pit_transaction.py
```

## Score impact

Accepted score remains `62/100`. Documentation, contracts, and read-only shell work do not earn uplift. Repeated real operation and independent evidence remain required.
