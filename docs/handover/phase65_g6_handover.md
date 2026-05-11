# Phase 65 G6 Handover - V1/V2 Real-Slice Mechanical Comparison

Status: CLOSED - V1/V2 MECHANICAL COMPARISON ONLY
Date: 2026-05-09
Authority: D-363 Phase G6 V1/V2 real-slice mechanical comparison, no alpha

## Executive Summary

G6 proved that Terminal Zero can compare the official V1 replay path against V2 proxy mechanics on one tiny real Tier 0 canonical price slice with the same predeclared neutral weights. The V1 and V2 mechanical accounting tables match, and V2 remains quarantined with `v2_promotion_ready = false`. No strategy search, alpha metric, ranking, alert, broker call, or promotion packet was introduced.

## Delivered Scope

- Added `v2_discovery/replay/real_slice_v1_v2_comparison.py` for real-slice V1/V2 mechanical comparison.
- Added `v2_discovery/replay/mechanical_comparison_report.py` for comparison report validation and explicit artifact writing.
- Added focused G6 tests covering canonical gates, manifest drift, finite data, predeclared weights, V1 call proof, V2 proxy proof, allowed field set, mismatch detection, non-promotion, no alerts/broker calls, and no default artifact refresh.
- Published `data/registry/g6_v1_v2_real_slice_mechanical_report.json` and its manifest through an explicit report path.
- Published `docs/architecture/g6_v1_v2_real_slice_mechanical_policy.md`.

## Deferred Scope

- No strategy search.
- No candidate family definition beyond the already approved fixture mechanics.
- No alpha, Sharpe, CAGR, drawdown, score, rank, signal strength, buy/sell decision, paper alert, broker call, Alpaca, OpenClaw, notifier, promotion packet, MLflow, DVC, vectorbt, qlib, or external engine.
- No paper-alert execution or trading permission.

## Derivation and Formula Register

```text
target_weight_{t,s} = 1 / count_symbols_t
engine_returns_{t,s} = total_ret_{t,s}
cost_rate = total_cost_bps / 10000
turnover_t = sum_s(abs(target_weight_{t,s} - current_weight_{t,s}))
transaction_cost_t = equity_before_cost_t * turnover_t * cost_rate
target_value_{t,s} = target_weight_{t,s} * equity_after_cost_t
cash_t = equity_after_cost_t - sum_s(target_value_{t,s})
gross_exposure_t = sum_s(abs(target_value_{t,s})) / equity_after_cost_t
net_exposure_t = sum_s(target_value_{t,s}) / equity_after_cost_t
mismatch_count = count(field where V1_field != V2_field)
```

Source paths:
- `v2_discovery/replay/real_slice_v1_v2_comparison.py`
- `v2_discovery/replay/mechanical_comparison_report.py`

## Logic Chain

```text
G4 canonical slice + manifest -> G5 V1 replay -> V2 proxy ledger on same weights -> strict mechanical comparison -> V2 still non-promotable
```

## Evidence Matrix

```text
G6 focused tests: .venv\Scripts\python -m pytest tests\test_g6_v1_v2_real_slice_mechanical_comparison.py -q -> PASS (20 passed)
G6/G5/G4/G3/G2/G1/G0/F matrix: .venv\Scripts\python -m pytest tests\test_g6_v1_v2_real_slice_mechanical_comparison.py tests\test_g5_single_canonical_replay_no_alpha.py tests\test_g4_real_canonical_readiness_fixture.py tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q -> PASS (147 passed)
Full regression: .venv\Scripts\python -m pytest -q -> PASS
pip check: .venv\Scripts\python -m pip check -> PASS
Data readiness: .venv\Scripts\python scripts\audit_data_readiness.py -> PASS (ready_for_paper_alerts=true; warning stale_sidecars_max_date_2023-11-27)
Minimal validation lab: .venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent -> PASS
Compileall: .venv\Scripts\python -m compileall v2_discovery\replay\real_slice_v1_v2_comparison.py v2_discovery\replay\mechanical_comparison_report.py tests\test_g6_v1_v2_real_slice_mechanical_comparison.py -> PASS
Runtime smoke: .venv\Scripts\python launch.py --server.headless true --server.port 8622 -> PASS; listener alive after 20 seconds and stopped
G6 artifact audit: data/registry/g6_v1_v2_real_slice_mechanical_report.json* -> PASS
G6 forbidden-path scan: v2_discovery/replay/real_slice_v1_v2_comparison.py and mechanical_comparison_report.py -> PASS
G6 secret scan: G6 code/test/doc/report surfaces -> PASS
Context packet: .venv\Scripts\python scripts\build_context_packet.py --validate -> PASS
SAW validation: .venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_phase65_g6_v1_v2_real_slice_mechanical_20260509.md -> PASS
Closure packet validation: .venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py --packet "<G6 ClosurePacket>" --require-open-risks-when-block --require-next-action-when-block -> PASS
Policy: docs/architecture/g6_v1_v2_real_slice_mechanical_policy.md
```

## Open Risks / Assumptions / Rollback

- Open risks: yfinance migration remains future debt; primary S&P sidecar freshness remains stale through `2023-11-27`.
- Assumptions: G7, if approved, is first controlled candidate-family definition only and still no search.
- Rollback: revert only G6 replay package additions, focused test, G6 report artifacts, policy, handover, SAW report, and G6 documentation/context updates; do not revert G5/G4/G3/G2/G1/G0/F/D-353/R64.1.

## New Context Packet

## What Was Done

- Preserved D-353 provenance gates, R64.1 dependency hygiene, Candidate Registry, G0/G1/G2/G3, G4 readiness, and G5 V1 replay as closed prerequisites.
- Closed Phase G6 V1/V2 real-slice mechanical comparison, no alpha.
- Reused the G4 Tier 0 `prices_tri` tiny canonical slice and the G5 predeclared equal weights.
- Ran V1 through `core.engine.run_simulation` and V2 through existing proxy ledger mechanics on the same real canonical slice.
- Compared only positions, cash, turnover, transaction cost, gross exposure, net exposure, row count, date range, source quality, manifest URI, engine name, and engine version.
- Emitted `data/registry/g6_v1_v2_real_slice_mechanical_report.json` with mechanical comparison fields only.
- Kept `promotion_ready = false`, `v2_promotion_ready = false`, `alerts_emitted = false`, and `broker_calls = false`.

## What Is Locked

- G6 is mechanical equivalence validation only and not strategy evidence.
- V2 remains quarantined and non-promotable even when V1/V2 mechanical accounting matches.
- No strategy search, alpha, ranking, alerts, broker calls, promotion packets, paper trading, or trading permission is authorized.
- G6 default execution must keep `report_path=None`; report artifacts refresh only when explicitly requested.

## What Is Next

- Decide whether to hold or approve Phase G7: first controlled candidate-family definition, no search.
- Carry yfinance migration and stale S&P sidecar freshness as open risks.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_g6_v1_v2_real_slice_mechanical_comparison.py tests\test_g5_single_canonical_replay_no_alpha.py tests\test_g4_real_canonical_readiness_fixture.py tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q
```

## Next Todos

- Prepare only the G7-or-hold decision: first controlled candidate-family definition, no search, or hold.
- Keep strategy search, rankings, alerts, broker calls, V2 promotion, paper trading, and promotion packets blocked until explicitly approved.
- Preserve G6 default execution with `report_path=None` unless artifact refresh is explicitly intended.
