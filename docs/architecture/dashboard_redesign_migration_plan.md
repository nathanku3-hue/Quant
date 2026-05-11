# Dashboard Redesign Migration Plan

Status: DASH-0 planning-only migration plan
Authority: Phase 65 DASH-0
Date: 2026-05-10

## Purpose

Define the migration sequence from the crowded Sovereign Cockpit tabs to the state-first GodView IA. This is a plan only.

## Migration Principles

1. Sort information before changing visuals.
2. Preserve existing runtime behavior until DASH-1 or later approval.
3. Move operational diagnostics out of the main cockpit.
4. Quarantine research/lab tooling away from operator state pages.
5. Keep all product claims state-first, source-labeled, and non-actionable.

## Legacy-To-New Mapping

| Legacy Tab / Area | New Page | Migration Notes |
| --- | --- | --- |
| Ticker Pool & Proxies | Opportunities | Split watchlist/intake status from proxy mechanics. |
| Data Health | Settings & Ops | Keep summary badge on Command Center. |
| Drift Monitor | Settings & Ops | Keep small drift badge on Command Center. |
| Daily Scan | Research Lab | Treat as research workflow, not main cockpit state. |
| Backtest Lab | Research Lab | Keep behind research boundary. |
| Modular Strategies | Research Lab | Keep behind research boundary. |
| Portfolio Builder | Portfolio & Allocation | Move allocation/risk controls here. |
| Shadow Portfolio | Portfolio & Allocation | Combine with allocation review. |
| Hedge Harvester sidebar | Research Lab or Settings & Ops | Remove from persistent sidebar in future runtime work. |
| FR-041 Governor banner | Command Center | Keep as top-level context, not per-tool ornament. |

## DASH-0

Planning-only deliverables:

- approve target IA;
- document page registry plan;
- document migration map;
- document ops relocation policy;
- update handover and SAW.

No runtime files are touched.

## DASH-1 Preview

DASH-1 can implement the page registry/sidebar shell.

Allowed in DASH-1:

- create shell/page registry;
- relocate legacy page blocks;
- keep existing calculations and data unchanged;
- add no new metrics;
- add no new product claims.

Forbidden in DASH-1:

- provider ingestion;
- factor-scout output;
- discovery-intake changes;
- candidate-card changes;
- backtest logic changes;
- alerts;
- broker calls;
- rankings;
- scores;
- buy/sell/hold signals.

## Future Redesign Sequence

1. DASH-1: page registry/sidebar shell.
2. DASH-2: Command Center layout.
3. DASH-3: Opportunities + Thesis Card layouts.
4. DASH-4: Market Behavior + Entry/Hold pages.
5. DASH-5: Portfolio & Allocation page, including Risk limits control-group alignment.
6. DASH-6: Research Lab containment.
7. DASH-7: Settings & Ops consolidation.
8. DASH-8: visual QA, smoke, and user review pass.

## Acceptance Criteria For DASH-0

- IA page map is documented.
- Legacy movement is documented.
- `st.Page` / `st.navigation` rationale is documented.
- Ops relocation policy is documented.
- Runtime implementation is explicitly held.
