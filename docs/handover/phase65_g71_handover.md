# Phase 65 G7.1 Handover - Roadmap Realignment / Product Charter

Status: CLOSED - PRODUCT CHARTER ONLY
Date: 2026-05-09
Authority: D-365 Phase G7.1 roadmap realignment / product charter

## Executive Summary

G7.1 realigned Phase 65+ around discretionary augmentation for de-risked asymmetric upside. The roadmap now says Terminal Zero is not a generic alpha-search machine and not a trading bot. The product target is 90% supercycle gem discovery and 10% buying-range / hold-discipline prompting. `PEAD_DAILY_V0` remains valid but is classified as a tactical signal family, while `SUPERCYCLE_GEM_DAILY_V0` becomes the primary product family for the next definition-only step.

No candidate was generated, no backtest/replay/proxy run started, no metric/ranking appeared, and no alert, broker, notifier, OpenClaw, or promotion path was introduced.

## Delivered Scope

- Published `docs/architecture/product_roadmap_discretionary_augmentation.md`.
- Published `docs/architecture/dashboard_signal_taxonomy.md`.
- Published `docs/architecture/supercycle_gem_family_policy.md`.
- Updated `docs/phase_brief/phase65-brief.md`, `docs/prd.md`, `docs/spec.md`, `docs/notes.md`, `docs/decision log.md`, `README.md`, lessons, and current truth surfaces.
- Published G7.1 SAW report.

## Deferred Scope

- No G8 PEAD candidate generation.
- No Supercycle Gem family artifact yet; that is G7.2 if approved.
- No candidate card.
- No dashboard implementation.
- No search, backtest, replay, proxy run, ranking, alert, broker call, paper trade, live trade, or promotion packet.

## Derivation and Formula Register

```text
product_focus = 0.90 * supercycle_gem_discovery + 0.10 * buying_range_hold_discipline_prompting
```

This is a planning allocation model, not a portfolio formula, signal weight, ranking score, or execution rule.

Source paths:
- `docs/architecture/product_roadmap_discretionary_augmentation.md`
- `docs/architecture/dashboard_signal_taxonomy.md`
- `docs/architecture/supercycle_gem_family_policy.md`

## Logic Chain

```text
G7 family-definition governance -> product framing changed -> roadmap realigned before candidate generation -> G7.2 Supercycle Gem family definition or hold
```

## Evidence Matrix

```text
Roadmap charter: docs/architecture/product_roadmap_discretionary_augmentation.md
Dashboard taxonomy: docs/architecture/dashboard_signal_taxonomy.md
Supercycle family policy: docs/architecture/supercycle_gem_family_policy.md
G7 focused regression: .venv\Scripts\python -m pytest tests\test_g7_candidate_family_definition.py -q -> PASS
Dashboard drift-tab regression: .venv\Scripts\python -m pytest tests\test_dashboard_drift_monitor_integration.py tests\test_drift_monitor_view.py -q -> PASS
Runtime smoke: .venv\Scripts\python launch.py --server.headless true --server.port 8631 -> PASS (alive after 30s, no uncaught app execution)
Context packet: .venv\Scripts\python scripts\build_context_packet.py --validate -> PASS
SAW report: docs/saw_reports/saw_phase65_g7_1_roadmap_realignment_20260509.md
```

## Open Risks / Assumptions / Rollback

- Open risks: yfinance migration remains future debt; primary S&P sidecar freshness remains stale through `2023-11-27`.
- Assumptions: G7.2, if approved, is definition-only Supercycle Gem family work and still no candidate generation.
- Rollback: revert only G7.1 docs/context/SAW/handover updates and the narrow dashboard drift-tab call-site regression fix if rejected. Do not revert G7 family code, G7 artifacts, G6/G5/G4/G3/G2/G1/G0/F, D-353, or R64.1.

## New Context Packet

## What Was Done

- Preserved D-353 provenance gates, R64.1 dependency hygiene, Candidate Registry, G0/G1/G2/G3/G4/G5/G6, and G7 `PEAD_DAILY_V0` family-definition artifacts as valid and unchanged.
- Closed G7.1 as roadmap/product-charter-only work.
- Reframed Terminal Zero as discretionary augmentation for de-risked asymmetric upside, not a trading bot and not generic alpha search.
- Documented the 90/10 product model: 90% supercycle gem discovery and 10% buying-range / hold-discipline prompting.
- Classified `PEAD_DAILY_V0` as a tactical signal family.
- Named `SUPERCYCLE_GEM_DAILY_V0` as the primary product family for the next definition-only step.
- Published dashboard taxonomy for thesis health, entry discipline, hold discipline, flow/positioning, and regime.
- Kept search, backtests, replays, rankings, alerts, broker calls, candidate cards, and promotion packets blocked.

## What Is Locked

- G8 PEAD candidate generation is held until a new approval.
- `PEAD_DAILY_V0` remains valid but is not the core roadmap center.
- `SUPERCYCLE_GEM_DAILY_V0` is a planned primary product family label only; no family artifact exists yet.
- Future short-squeeze and CTA-type signals are dashboard context, not automatic triggers.
- No strategy search, backtest, replay, proxy run, metric, ranking, alert, broker call, paper trading, or promotion packet is authorized by G7.1.

## What Is Next

- Decide whether to hold or approve Phase G7.2: define `SUPERCYCLE_GEM_DAILY_V0`, no search.
- Carry yfinance migration and stale S&P sidecar freshness as open risks.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_g7_candidate_family_definition.py -q
```

## Next Todos

- Prepare only the G7.2-or-hold decision: define `SUPERCYCLE_GEM_DAILY_V0`, no search, or hold.
- Keep G8 PEAD candidate generation held until explicitly reapproved.
- Keep strategy search, rankings, alerts, broker calls, V2 promotion, paper trading, and promotion packets blocked.

ConfirmationRequired: YES
Prompt: Reply "approve next phase" to start execution.
NextPhaseApproval: PENDING
