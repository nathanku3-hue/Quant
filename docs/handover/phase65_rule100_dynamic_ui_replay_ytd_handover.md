# Phase 65 Rule100 Dynamic UI/Replay YTD Handover

RoundID: `20260513-rule100-ytd-visible-correctness`
ScopeID: `rule100-dynamic-ui-replay-sizing-benchmark-stale-overlay`
Date: 2026-05-13
Audience: PM / Planner

## Executive Summary

The visible Rule of 100 and YTD benchmark correctness round is SAW PASS. Direct Rule100 allocation and Strategy Replay now use the same `controls.max_weight` dynamic config, while frozen Rule100 audit/history defaults remain unchanged. Benchmark YTD freshness is now evaluated per ticker so stale QQQ can be overlaid without forcing fresh SPY off local data.

## Delivered Scope vs Deferred Scope

Delivered:

- `rule100_config_from_max_weight(max_weight)` for UI/replay sizing;
- direct Rule100 UI path passes `controls.max_weight` to softmax sizing;
- Strategy Replay Rule100 path uses the same dynamic config;
- per-ticker benchmark stale detection and stale-only live overlay;
- deterministic AppTest replay cap for route coverage;
- behavior tests and SAW closure.

Deferred:

- versioned/labeled 35% Rule100 UI-policy history artifact;
- canonical benchmark/provider ingestion or QQQ backfill;
- replay cold-start optimization for long production horizons;
- broker behavior, alerts, ranking/scoring, live trading, or new optimizer objective.

## Derivation and Formula Register

```text
Rule100 audit default:
  Rule100SoftmaxConfig().gross_budget_per_name = 0.10
  Rule100SoftmaxConfig().max_single_name_weight = 0.15

Rule100 UI/replay config:
  cfg = rule100_config_from_max_weight(controls.max_weight)
  cfg.gross_budget_per_name = controls.max_weight
  cfg.max_single_name_weight = controls.max_weight
  cfg.gross_budget_cap = 1.0

Visible two-name example:
  max_weight = 0.35
  eligible names = 2 equal-score names
  gross budget = min(1.0, 0.35 * 2) = 0.70
  target weights = 0.35 / 0.35 / 0.30 cash

Benchmark freshness:
  stale_tickers = tickers whose local latest valid date is behind the fresh cutoff or missing
  live_overlay_scope = stale_tickers only
  visible_curve_i requires local_fresh_i or live_overlay_i
```

Source paths:

- `strategies/rule100_softmax.py`
- `strategies/strategy_replay.py`
- `views/optimizer_view.py`
- `core/data_orchestrator.py`
- `dashboard.py`
- `tests/test_rule100_softmax.py`
- `tests/test_strategy_replay.py`
- `tests/test_optimizer_view.py`
- `tests/test_dash_2_portfolio_ytd.py`

## Logic Chain

```text
UI max-weight control -> dynamic Rule100 config -> direct UI/replay target weights -> allocation/YTD display
local benchmark TRI -> per-ticker stale check -> stale-only live overlay -> benchmark YTD curves
```

## Evidence Matrix

| Check | Result | Evidence |
| --- | --- | --- |
| Focused Rule100/replay/YTD/AppTest suite | PASS | `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py -q` -> 89 passed |
| Broader affected suite | PASS | `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py tests\test_rule100_softmax_v1_1.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> 151 passed |
| Full pytest | PASS | `.venv\Scripts\python -m pytest -q` |
| Context validation | PASS | `.venv\Scripts\python scripts\build_context_packet.py --validate` |
| Runtime readiness | PASS | Streamlit readiness on `http://127.0.0.1:8514/portfolio-and-allocation`, HTTP 200 |
| SAW | PASS | `docs/saw_reports/saw_rule100_dynamic_ui_replay_ytd_20260513.md` |

## Open Risks / Assumptions / Rollback

Open risks:

- production Strategy Replay over long YTD horizons can still be cold-start expensive;
- frozen Rule100 history intentionally remains 10% audit semantics;
- live benchmark overlay remains display-only and provider-dependent.

Assumptions:

- UI/replay sizing policy can differ from frozen audit history as long as it is explicit and tested;
- canonical benchmark backfill requires a separate ingestion decision.

Rollback:

- revert `strategies/rule100_softmax.py`, `strategies/strategy_replay.py`, `views/optimizer_view.py`, `core/data_orchestrator.py`, `dashboard.py`, affected tests, and this round's docs/context updates. No frozen Rule100 history or canonical market data rollback is required.

## Next Phase Roadmap

- manually audit visible Rule100 weights and QQQ YTD;
- hold if the visible behavior is accepted;
- separately approve a versioned/labeled Rule100 UI-policy history artifact only if historical 35% traces are needed;
- separately approve canonical benchmark ingestion/backfill only if display overlay is not enough.

## New Context Packet

## What Was Done

- Fixed visible Rule100 sizing without rewriting frozen audit history.
- Added `rule100_config_from_max_weight(max_weight)` and used it only for direct UI and Strategy Replay.
- Preserved `Rule100SoftmaxConfig()` defaults at 10% per-name budget and 15% cap.
- Proved one eligible Rule100 name at 35% can target 35%, and two equal names target 35%/35%/30% cash.
- Made direct Rule100 UI state and Strategy Replay agree for the same candidate frame and cap.
- Added per-ticker stale benchmark overlay so stale/missing QQQ can refresh while fresh SPY remains local.
- Prevented stale benchmark columns from rendering fresh-looking forward-filled curves when live overlay fails.
- Published SAW PASS for `20260513-rule100-ytd-visible-correctness`.
- Preserved D-353 provenance gates and R64.1 dependency hygiene as closed baseline truth.

## What Is Locked

- Frozen Rule100 audit/history defaults remain unchanged unless a separate versioned artifact is explicitly approved.
- UI/replay Rule100 sizing derives from `controls.max_weight` through `rule100_config_from_max_weight(...)`.
- Benchmark live overlay is display-only and stale-ticker scoped; it does not promote provider data to canonical market data.
- No provider ingestion, broker behavior, alerts, ranking/scoring, live trading, or new optimizer objective is authorized.

## What Is Next

- Manually audit visible Rule100 weights and QQQ YTD, then hold if accepted.
- Separately approve a versioned/labeled 35% Rule100 UI-policy history artifact only if historical 35% traces are needed.
- Separately approve canonical benchmark ingestion/backfill only if display-only overlay is insufficient.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_rule100_softmax.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py -q
```

## Next Todos

- Keep frozen audit history separate from live UI/replay policy.
- Carry production replay cold-start cost as a future performance follow-up.
- Keep benchmark overlay display-only until a canonical ingestion decision is approved.
