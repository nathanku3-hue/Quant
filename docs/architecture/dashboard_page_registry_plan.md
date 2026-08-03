# Dashboard Page Registry Plan

Status: `ACTIVE SLICE-1 PRODUCT CONTRACT`
Date: 2026-08-03
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`

## Runtime mechanism

Keep Streamlit `st.Page` and `st.navigation`. `dashboard.py` remains the shared frame and sole future application. `views/page_registry.py` owns exactly this order:

```text
Command Center                 default
Discovery & Analysis
Decisions & Thesis
Portfolio & Rotation
Strategy Modules
Operations & Replay
```

Repository grounding: `views/command_center.py` does not currently exist and is a new Slice 1 file.

## Registry law

- Registration fails closed when any required page is missing or duplicated.
- Command Center owns the default URL path.
- Page renderers consume typed read models or bounded existing renderers.
- Navigation creates no proposal, identity, event, portfolio, or certification authority.
- Discovery & Analysis remains functional during the migration.
- Existing research/replay surfaces are labeled non-authoritative.

## Slice 1 composition root

```text
verified source objects
→ adapters
→ proposal submission handler
→ ordered governance events
→ deterministic projector
→ DecisionEpisodeReadModel
→ dashboard.py composition root
→ views.command_center renderer
```

The registry never builds proposals, validates identity, appends events, or reads canonical state from raw session state.

## Expected product-surface files

```text
M  dashboard.py
M  views/page_registry.py
A  views/command_center.py
M  existing page-registry tests
A/M Command Center AppTest and authority-state tests
```

Contract/adapter/event/projector files are required lower layers of the same Slice 1 transaction and are governed by the canonical contract. The earlier exact seven-file shell scope is superseded.

## Acceptance

- six pages render in the frozen order;
- Command Center is default;
- real MU-operated, MU-shadow, and book-cash rows render through projected state;
- no static production proposal rows exist;
- no raw session-state governance authority is read;
- no selection, risk, preview, mutation, certification change, or deletion occurs.
