# Dashboard Information Architecture

Status: DASH-0 approved planning-only IA
Authority: Phase 65 DASH-0
Date: 2026-05-10

## Purpose

DASH-0 approves the target information architecture for the GodView dashboard redesign. It does not rewrite `dashboard.py`, `views/`, navigation shell code, Streamlit callbacks, data flows, backtests, alerts, broker code, provider code, factor-scout code, candidate cards, or discovery intake output.

## Current Problem

The live dashboard is still the older Sovereign Cockpit. Its top-level tabs are crowded and tool-oriented:

```text
Ticker Pool & Proxies
Data Health
Drift Monitor
Daily Scan
Backtest Lab
Modular Strategies
Portfolio Builder
Shadow Portfolio
```

The newer product specs require a state-first operator cockpit that answers:

```text
What state is this opportunity in?
Why?
What changed?
What is blocked?
What should the operator monitor next?
```

## Target Page Map

| New Page | Contains | Legacy Movement |
| --- | --- | --- |
| Command Center | State distribution, freshness, risks, next monitoring focus | New top page |
| Opportunities | Intake/candidate cards with origin/status labels | Ticker Pool partially maps here |
| Thesis Card | MU/current candidate thesis, evidence, contradictions, blockers | New |
| Market Behavior | GodView signal families, observed/estimated/inferred labels | New |
| Entry & Hold Discipline | Why not buy yet / why not sell yet | New |
| Portfolio & Allocation | Risk limits, allocation, shadow portfolio | Portfolio Builder + Shadow Portfolio |
| Research Lab | Backtests, modular strategies, daily scan, experiments | Backtest Lab + Modular Strategies + Daily Scan |
| Settings & Ops | Data health, drift monitor, diagnostics, refresh | Data Health + Drift Monitor |

## Page Semantics

### Command Center

Default landing page. Shows state distribution, source-quality/freshness summary, open risks, blocked actions, and next monitoring focus. It may show small ops badges, but not full ops workflows.

### Opportunities

Shows watched opportunities and intake/candidate-card status. It must expose `discovery_origin`, source-quality, freshness, and blocked-action labels. It must not rank opportunities.

### Thesis Card

Shows the current candidate thesis, evidence present/missing, contradiction log, and thesis breakers. `MU` may be shown as the only current candidate card, but not as validated or actionable.

### Market Behavior

Shows GodView signal families with observed/estimated/inferred labels, source class, freshness, provider/feed or provider gap, allowed influence, and forbidden influence.

### Entry & Hold Discipline

Combines "why not buy yet" and "why not sell yet" so the operator sees entry blockers and hold discipline in one review surface. State labels remain paper-only prompts.

### Portfolio & Allocation

Contains allocation review, risk limits, optimizer output, and shadow portfolio comparison. Future runtime redesign should align `Max weight` and `Max sector weight` together as a single "Risk limits" control group.

### Research Lab

Contains backtests, modular strategies, daily scan, and experiments. This is where legacy score/rank-like research tooling can be quarantined from the main state-first cockpit.

### Settings & Ops

Contains Data Health, Drift Monitor, diagnostics, refresh controls, and operational status. Drift Monitor should have a small status badge outside this page, but the full workflow belongs here.

## Non-Goals

DASH-0 does not authorize:

- `dashboard.py` edits;
- `views/` edits;
- `optimizer_view.py` edits;
- Streamlit runtime navigation shell;
- new data or metrics;
- factor-scout code or use of `phase34_factor_scores.parquet`;
- discovery-intake output changes;
- candidate-card changes;
- provider ingestion;
- backtest implementation;
- alerts;
- broker calls;
- buy/sell/hold labels;
- candidate ranking or scoring.

## Streamlit Basis

Official Streamlit docs describe `st.Page` and `st.navigation` as the flexible way to define multipage apps. The entrypoint acts as a shared router/frame around pages, while the older `pages/` directory method is simpler and automatic. DASH-0 therefore plans a future page registry/sidebar shell instead of continuing the crowded flat-tab design.

Sources:

- `https://docs.streamlit.io/develop/concepts/multipage-apps/overview`
- `https://docs.streamlit.io/develop/api-reference/navigation/st.navigation`
- `https://docs.streamlit.io/develop/api-reference/navigation/st.page`

## Locked Decision

Target IA is approved as:

```text
Command Center
Opportunities
Thesis Card
Market Behavior
Entry & Hold Discipline
Portfolio & Allocation
Research Lab
Settings & Ops
```

Next action:

```text
approve_dash_1_page_registry_shell_or_hold
```
