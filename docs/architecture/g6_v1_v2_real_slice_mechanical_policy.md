# G6 V1/V2 Real-Slice Mechanical Comparison Policy

Status: Phase 65 G6 policy
Authority: D-363 Phase G6 V1/V2 real-slice mechanical comparison, no alpha

## Purpose

G6 proves that the official V1 replay path and the V2 proxy mechanics can produce equivalent mechanical accounting on one tiny real Tier 0 canonical price slice. It is an implementation-equivalence validation only. It is not strategy research, alpha discovery, candidate ranking, alerting, broker automation, paper trading, or promotion authority.

## Allowed Scope

- Input: the G4 `prices_tri` canonical slice with manifest-backed Tier 0 evidence.
- Weights: predeclared neutral fixture weights only, currently equal weight per available `permno` per date.
- V1 path: `core.engine.run_simulation`, invoked through the G5 canonical replay path.
- V2 path: the existing V2 proxy ledger mechanics on the same prices and weights.
- Comparison fields: positions, cash, turnover, transaction cost, gross exposure, net exposure, row count, date range, source quality, manifest URI, engine name, and engine version.
- Artifact writes: explicit only through `report_path`; default execution uses `report_path=None`.

## Required Gates

- `source_quality = canonical`.
- `extra.source_tier = tier0`.
- Manifest must exist and reconcile SHA-256, row count, schema, and date range before either replay path runs.
- Numeric inputs must be finite before replay.
- Prices must be positive.
- V1 and V2 must use the same predeclared neutral weights and cost model.
- V2 must remain `promotion_ready = false` even when all mechanical fields match.
- Report must keep `promotion_ready = false`, `v2_promotion_ready = false`, `alerts_emitted = false`, and `broker_calls = false`.

## Blocked Scope

- No strategy search, signal function, ranker, factor logic, PEAD, momentum, value, ML, or parameter sweep.
- No Sharpe, CAGR, alpha, drawdown, score, rank, signal strength, buy/sell decision, promotion verdict, paper alert, broker call, Alpaca call, OpenClaw message, notifier call, MLflow, DVC, vectorbt, qlib, or external engine.
- No promotion packet, even on exact V1/V2 match.

## Formula Register

- `target_weight_{t,s} = 1 / count_symbols_t` for each `permno` available on date `t`.
- `engine_returns_{t,s} = total_ret_{t,s}` from the canonical slice for the V1 engine call.
- `cost_rate = total_cost_bps / 10000`.
- `turnover_t = sum_s(abs(target_weight_{t,s} - current_weight_{t,s}))`.
- `transaction_cost_t = equity_before_cost_t * turnover_t * cost_rate`.
- `target_value_{t,s} = target_weight_{t,s} * equity_after_cost_t`.
- `cash_t = equity_after_cost_t - sum_s(target_value_{t,s})`.
- `gross_exposure_t = sum_s(abs(target_value_{t,s})) / equity_after_cost_t`.
- `net_exposure_t = sum_s(target_value_{t,s}) / equity_after_cost_t`.
- `mismatch_count = count(field where V1_field != V2_field)` over the approved mechanical equality fields.

Source paths:
- `v2_discovery/replay/real_slice_v1_v2_comparison.py`
- `v2_discovery/replay/mechanical_comparison_report.py`

## Evidence

- `tests/test_g6_v1_v2_real_slice_mechanical_comparison.py`
- `data/registry/g6_v1_v2_real_slice_mechanical_report.json`
- `data/registry/g6_v1_v2_real_slice_mechanical_report.json.manifest.json`
