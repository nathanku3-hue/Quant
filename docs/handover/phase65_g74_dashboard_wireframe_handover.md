# Phase 65 G7.4 Handover - Dashboard Wireframe / Product-State Spec

Date: 2026-05-09
Status: COMPLETE
Owner: Codex / Frontend/UI + Docs/Ops

## 1) Executive Summary

- Objective completed: defined the first GodView dashboard product spec around opportunity states, watchlist cards, and daily brief structure.
- Business/user impact: the dashboard concept now explains states and blockers without score/rank/alert/order behavior.
- Current readiness: product-state spec is ready; G8 candidate card remains held unless G7.4 is accepted.

## 2) Delivered Scope vs Deferred Scope

Delivered:

- `docs/architecture/godview_dashboard_wireframe.md`
- `docs/architecture/godview_watchlist_card_spec.md`
- `docs/architecture/godview_daily_brief_spec.md`
- `tests/test_g7_4_dashboard_state_spec.py`

Deferred:

- dashboard runtime code;
- Streamlit implementation;
- candidate cards;
- alerts;
- provider calls;
- scoring/ranking;
- broker calls.

## 3) Derivation and Formula Register

| Formula ID | Formula | Variables | Why it matters | Source |
| --- | --- | --- | --- | --- |
| F-G74-01 | `dashboard_card = state + prior_state + reason_codes + source_breakdown + blockers + monitoring_questions` | card fields | Keeps dashboard state-first and non-executing | `docs/architecture/godview_watchlist_card_spec.md` |
| F-G74-02 | `brief_state_only = state_changes + freshness_gaps + blockers + questions` | daily brief sections | Prevents rankings/alerts/orders in daily brief | `docs/architecture/godview_daily_brief_spec.md` |
| F-G74-03 | `runtime_added = false` | G7.4 owned files | Keeps G7.4 as product spec only | `docs/architecture/godview_dashboard_wireframe.md` |

## 4) Logic Chain

| Chain ID | Input | Transform | Decision Rule | Output |
| --- | --- | --- | --- | --- |
| L-G74-01 | opportunity state | watchlist card fields | show state, reasons, freshness, blockers | product-state card |
| L-G74-02 | state changes | daily brief sections | summarize changes without alerts or ranks | future brief spec |
| L-G74-03 | source gaps | blocker copy | show why not buy/sell yet | discipline view |

## 5) Evidence Matrix

| Check ID | Command | Result | Artifact |
| --- | --- | --- | --- |
| CHK-G74-01 | `.venv\Scripts\python -m pytest tests\test_g7_4_dashboard_state_spec.py -q` | PASS | focused spec tests |
| CHK-G74-02 | forbidden-scope scan | PASS | owned G7.4 files |
| CHK-G74-03 | closure packet validation | PASS | G7.4 closure packet |
| CHK-G74-04 | SAW block validation | PASS | G7.4 SAW report |

## 6) Open Risks / Assumptions / Rollback

Open Risks:

- inherited yfinance migration, stale sidecar, Reg SHO policy gap, GodView provider gap, options/license gap, and broad compileall workspace hygiene remain open.
- Runtime dashboard implementation still needs later UI phase and screenshot/runtime validation.

Assumptions:

- G7.4 is product-state spec only and intentionally does not edit `dashboard.py` or `views/*`.

Rollback Note:

- Revert only G7.4 dashboard spec docs, focused test, context/governance updates, handover, and SAW report.

## 7) Next Phase Roadmap

| Step | Scope | Acceptance Check | Owner |
| --- | --- | --- | --- |
| 1 | G8 one Supercycle Gem candidate card or hold | only after G7.4 PASS and explicit approval | PM / Architecture |
| 2 | Hold dashboard runtime | no runtime UI until later approved phase | Frontend/UI |

## 8) New Context Packet

## What Was Done
- Preserved D-353, R64.1, Candidate Registry, G0-G7, G7.1, G7.1A, G7.1B, G7.1C, G7.1D, G7.1E, G7.1F, G7.1G as inherited baseline truth.
- Completed G7.4 as dashboard wireframe / product-state spec only.
- Added state-first dashboard sections, watchlist card fields, blocked actions, daily brief structure, and no-runtime/no-alert/no-order boundaries.
- Added focused docs tests for dashboard spec completeness and forbidden score/ranking/action wording.

## What Is Locked
- Dashboard spec is state-first, not score-first.
- No dashboard runtime code was added.
- No buy or sell orders.
- No alerts.
- No scores.
- No rankings.
- No provider calls.
- No broker calls.
- G8 remains held unless G7.4 passes and the next decision explicitly approves candidate-card work.

## What Is Next
- Recommended next action: `approve_g8_one_supercycle_gem_candidate_card_or_hold`.
- G8 is the first place to create an actual candidate card, and it remains held until approved.

## First Command
```text
.venv\Scripts\python -m pytest tests\test_g7_4_dashboard_state_spec.py -q
```

## Next Todos
- Hold G8 until explicit approval.
- Keep provider/search/ranking/alert/broker/dashboard-runtime work held.
