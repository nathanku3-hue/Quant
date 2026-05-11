# DASH-1 Page Registry Shell Handover

Status: Complete
Authority: Phase 65 DASH-1 runtime shell-only work
Date: 2026-05-10
Owner: PM / Architecture Office

## Executive Summary (PM-friendly)

DASH-1 replaces the old crowded top-level dashboard tabs with the approved GodView page registry/sidebar shell.

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

This is not a visual redesign and not a semantic expansion. Existing legacy dashboard content is only relocated behind the approved page buckets.

## Delivered Scope vs Deferred Scope

Delivered:

- Streamlit page registry/sidebar shell;
- approved page groups;
- legacy content relocation;
- placeholders for pages without approved runtime content;
- focused shell tests;
- context selector support for the DASH-1 handover.

Deferred:

- DASH-2 Command Center content design;
- page-by-page visual redesign;
- optimizer risk-limit control alignment;
- new data, metrics, signals, providers, alerts, broker calls, rankings, scores, candidate generation, factor-scout integration, or buy/sell/hold output.

## Derivation and Formula Register

DASH-1 shell validity:

```text
dash_1_shell_valid =
  approved_page_order_present
  and streamlit_page_registry_present
  and selected_page_run_called
  and old_flat_tabs_absent
  and legacy_content_reachable
  and forbidden_scope_absent
```

Source paths:

- `dashboard.py`
- `views/page_registry.py`
- `tests/test_dash_1_page_registry_shell.py`

## Logic Chain

```text
DASH-0 IA approval -> Streamlit page registry -> sidebar shell -> legacy relocation -> DASH-2 content gate
```

## Evidence Matrix

| Check | Result | Artifact |
| --- | --- | --- |
| Focused DASH-1 tests | PASS | `tests/test_dash_1_page_registry_shell.py` |
| Dashboard drift regression | PASS | `tests/test_dashboard_drift_monitor_integration.py` |
| Runtime smoke | PASS | `docs/context/e2e_evidence/dash1_streamlit_8502_status.txt` |
| Context selector | PASS | `tests/test_build_context_packet.py` |
| G8.1B-R parallel closeout | PASS | `docs/saw_reports/saw_phase65_g8_1b_r_reviewer_rerun_20260510.md` |

## Open Risks / Assumptions / Rollback

Open risks:

- inherited dirty dashboard runtime worktree;
- separate G8.1B factor-scout lane artifacts remain outside DASH-1 ownership;
- visual QA remains pending beyond boot smoke;
- DASH-2 must avoid introducing metrics or claims without explicit approval.

Assumptions:

- Streamlit `1.54.0` supports `st.Page` and `st.navigation`;
- legacy page internals remain acceptable until later page-specific redesign phases;
- DASH-1 should preserve behavior rather than improve content.

Rollback:

- revert DASH-1 edits to `dashboard.py`, `views/page_registry.py`, focused tests, handover, context surfaces, and SAW report.
- do not revert G8.1A, G8.1B, G8.1B-R, DASH-0, or inherited artifacts.

## Next Phase Roadmap

1. `DASH-2`: Command Center placeholder + status badges only.
2. `DASH-3`: Opportunities / Thesis Card content pass.
3. `DASH-4`: Market Behavior / Entry & Hold Discipline content pass.
4. `DASH-5`: Portfolio & Allocation risk-limits control grouping.
5. Hold.

## New Context Packet

## What Was Done

- Completed DASH-1 as runtime shell-only page registry work.
- Preserved the R64.1/D-353 provenance anchor while implementing the dashboard shell lane.
- Replaced the old flat top-level tab shell with Streamlit `st.Page` / `st.navigation`.
- Preserved the approved page map: Command Center, Opportunities, Thesis Card, Market Behavior, Entry & Hold Discipline, Portfolio & Allocation, Research Lab, Settings & Ops.
- Relocated legacy content only: Ticker Pool & Proxies -> Opportunities; Data Health and Drift Monitor -> Settings & Ops; Daily Scan, Backtest Lab, Modular Strategies, and Hedge Harvester -> Research Lab; Portfolio Builder and Shadow Portfolio -> Portfolio & Allocation.
- Added placeholder-only shell pages where no approved runtime content exists yet.
- Added no new data, metrics, product claims, providers, alerts, broker behavior, factor-scout integration, candidate generation, ranking, scoring, or buy/sell/hold output.
- Parallel G8.1B-R reviewer-evidence closeout is PASS and did not touch dashboard files.

## What Is Locked

- DASH-1 is shell-only and relocation-only.
- `views/page_registry.py` owns the approved page order, page groups, and legacy movement map.
- Data Health and Drift Monitor are not top-level product tabs; they live under Settings & Ops.
- Backtest Lab, Daily Scan, Modular Strategies, and Hedge Harvester are not top-level product tabs; they live under Research Lab.
- Portfolio Builder and Shadow Portfolio live under Portfolio & Allocation.
- Command Center, Thesis Card, Market Behavior, and Entry & Hold Discipline remain placeholders until separately approved.
- No new score, rank, buy/sell/hold, provider, alert, broker, factor-scout, candidate-generation, or ingestion behavior is authorized.

## What Is Next

- Recommended next action: `approve_dash_2_command_center_placeholder_or_hold`.
- DASH-2 should add Command Center placeholder/status badges only.
- DASH-2 should add no new metrics, product claims, providers, alerts, broker calls, rankings, scores, factor-scout integration, or candidate generation.
- Alternative: hold.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py tests\test_dashboard_drift_monitor_integration.py -q
```

## Next Todos

- Wait for explicit DASH-2 approval or hold.

## Confirmation

ConfirmationRequired: YES
Prompt: Reply "approve DASH-2 command center placeholder" or "hold".
NextPhaseApproval: PENDING
