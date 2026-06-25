# Dashboard Page Registry Plan

Status: DASH-0 planning-only registry plan
Authority: Phase 65 DASH-0
Date: 2026-05-10

## Purpose

Plan the future dashboard page registry/sidebar shell. No runtime code is implemented in DASH-0.

## Preferred Future Mechanism

Use Streamlit `st.Page` and `st.navigation` in a later DASH-1 runtime phase.

Rationale:

- It lets the entrypoint become a shared router/frame.
- It supports explicit page labels, icons, URL paths, and grouping.
- It is more flexible than relying on filename ordering in a `pages/` directory.

## Candidate Registry Shape

Future DASH-1 can implement a page registry shaped like:

```text
app shell
  common frame
  shared status badges
  shared governance footer
  st.navigation(page_groups)
```

Planned page groups:

```text
Operate
  Command Center
  Opportunities
  Thesis Card
  Market Behavior
  Entry & Hold Discipline

Portfolio
  Portfolio & Allocation

Research
  Research Lab

System
  Settings & Ops
```

## Future Page Modules

Suggested future module names:

```text
views/dashboard_pages/command_center.py
views/dashboard_pages/opportunities.py
views/dashboard_pages/thesis_card.py
views/dashboard_pages/market_behavior.py
views/dashboard_pages/entry_hold_discipline.py
views/dashboard_pages/portfolio_allocation.py
views/dashboard_pages/research_lab.py
views/dashboard_pages/settings_ops.py
```

These are planning names only. DASH-0 does not create them.

## Shared Frame Contract

Future shell should provide:

- app title and state-only boundary;
- data freshness badge;
- drift status badge only, not full drift workflow;
- source-quality badge;
- disabled footer facts:
  - `orders_enabled = false`
  - `alerts_enabled = false`
  - `rankings_enabled = false`
  - `scores_enabled = false`
  - `providers_enabled = false`

## Migration Guardrails

- DASH-1 may relocate legacy content into the new shell.
- DASH-1 may not add new data, metrics, claims, providers, alerts, broker calls, ranking, scoring, or buy/sell/hold behavior.
- DASH-1 must keep all page labels state-first and operator-readable.
- DASH-1 must run Streamlit smoke and visual QA before closeout.

## Held Runtime Task

The optimizer UX fix is held for a later runtime task:

```text
Align Max weight and Max sector weight as one Risk limits control group in optimizer_view.py.
```

No `optimizer_view.py` change is authorized by DASH-0.
