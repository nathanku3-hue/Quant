# Dashboard IA Handover - DASH-0 GodView Redesign Plan

Status: Complete
Authority: Phase 65 DASH-0 planning-only work
Date: 2026-05-10
Owner: PM / Architecture Office

## Executive Summary (PM-friendly)

DASH-0 approves the dashboard information architecture before any code rewrite. The current live dashboard is still the older Sovereign Cockpit with crowded top-level tabs. The future design should become a state-first GodView cockpit organized around operator decisions, not tools.

Approved page order:

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

No runtime code is changed in DASH-0.

## Delivered Scope vs Deferred Scope

Delivered:

- dashboard IA spec;
- page registry plan;
- migration plan;
- ops relocation policy;
- optional wireframe/product-spec updates;
- handover and SAW closeout.

Deferred:

- DASH-1 page registry/sidebar shell;
- Streamlit runtime work;
- `dashboard.py` edits;
- `views/` edits;
- `optimizer_view.py` risk-limit control alignment;
- new data, metrics, provider calls, alerts, broker calls, rankings, scores, buy/sell/hold outputs.

## Derivation and Formula Register

DASH-0 validity formula:

```text
dash_0_valid =
  page_map_approved
  and legacy_movement_mapped
  and streamlit_navigation_basis_documented
  and ops_relocation_policy_defined
  and runtime_code_touched == false
  and factor_scout_touched == false
  and provider_alert_broker_touched == false
```

Source paths:

- `docs/architecture/dashboard_information_architecture.md`
- `docs/architecture/dashboard_page_registry_plan.md`
- `docs/architecture/dashboard_redesign_migration_plan.md`
- `docs/architecture/dashboard_ops_relocation_policy.md`

## Logic Chain

```text
Current crowded tabs -> state-first IA -> page registry plan -> migration boundary -> DASH-1 approval gate
```

## Evidence Matrix

| Check | Result | Artifact |
| --- | --- | --- |
| IA spec | PASS | `docs/architecture/dashboard_information_architecture.md` |
| Page registry plan | PASS | `docs/architecture/dashboard_page_registry_plan.md` |
| Migration plan | PASS | `docs/architecture/dashboard_redesign_migration_plan.md` |
| Ops relocation policy | PASS | `docs/architecture/dashboard_ops_relocation_policy.md` |
| Runtime files untouched by DASH-0 | PASS | no DASH-0 edits to `dashboard.py` or `views/` |
| Streamlit docs basis | PASS | official Streamlit docs for `st.Page` and `st.navigation` |

## Open Risks / Assumptions / Rollback

Open risks:

- inherited dirty dashboard runtime worktree remains outside DASH-0;
- DASH-1 still needs visual QA and Streamlit smoke if approved;
- legacy score/rank-like research tooling must remain quarantined in Research Lab;
- optimizer risk-limit alignment remains a future runtime task.

Assumptions:

- the target IA is approved before runtime implementation;
- DASH-1 will relocate legacy content only and add no new metrics or product claims;
- Streamlit runtime version supports the planned navigation mechanism before DASH-1 implementation.

Rollback:

- revert only DASH-0 docs, handover, context surfaces, governance logs, and SAW report.
- do not revert G8.1A or prior Phase 65 work.

## Next Phase Roadmap

1. `DASH-1`: page registry/sidebar shell, no new data, no new metrics, legacy pages only relocated.
2. `DASH-2`: Command Center page design.
3. `DASH-3`: Opportunities and Thesis Card.
4. `DASH-4`: Market Behavior and Entry/Hold Discipline.
5. `DASH-5`: Portfolio & Allocation, including future Risk limits control-group alignment.
6. Hold.

## New Context Packet

## What Was Done

- Completed DASH-0 as dashboard information-architecture planning only.
- Preserved the R64.1/D-353 provenance anchor while creating a separate dashboard IA planning lane.
- Approved the target page map: Command Center, Opportunities, Thesis Card, Market Behavior, Entry & Hold Discipline, Portfolio & Allocation, Research Lab, Settings & Ops.
- Mapped legacy Sovereign Cockpit tabs into the future state-first pages.
- Documented the future `st.Page` / `st.navigation` registry-shell direction using official Streamlit docs.
- Moved Data Health and Drift Monitor into the future Settings & Ops page by policy.
- Preserved DASH-1 as a separate future approval gate.
- Added no runtime code, no provider code, no alerts, no broker behavior, no factor-scout code, no candidate-card changes, and no discovery-intake changes.

## What Is Locked

- DASH-0 is planning-only.
- `dashboard.py`, `views/`, and `optimizer_view.py` are not touched by DASH-0.
- Drift Monitor and Data Health belong in future Settings & Ops, with only compact badges outside it.
- Portfolio & Allocation should eventually group `Max weight` and `Max sector weight` as one Risk limits UX task, but not in DASH-0.
- Research Lab contains Backtest Lab, Modular Strategies, Daily Scan, and experiments.
- No buy/sell/hold, score, rank, provider, alert, broker, or new-data behavior is authorized.

## What Is Next

- Recommended next action: `approve_dash_1_page_registry_shell_or_hold`.
- DASH-1 should create the page registry/sidebar shell only.
- DASH-1 should add no new data, metrics, product claims, providers, alerts, broker calls, rankings, or scores.
- Alternative: hold.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_build_context_packet.py tests\test_phase61_context_hygiene.py -q
```

## Next Todos

- Wait for explicit DASH-1 approval or hold.

## Confirmation

ConfirmationRequired: YES
Prompt: Reply "approve DASH-1 page registry shell" or "hold".
NextPhaseApproval: PENDING
