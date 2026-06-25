# G5 Single Canonical Replay, No Alpha Policy

Status: Phase 65 G5 policy
Authority: D-362 Phase G5 single canonical replay, no alpha

## Purpose

G5 proves that the official V1 canonical replay path can mechanically replay one tiny real Tier 0 canonical price slice after G4 readiness. It is a control-plane and accounting proof only. It is not strategy research, alpha discovery, candidate ranking, alerting, broker automation, or promotion authority.

## Allowed Scope

- Input: the G4-style `prices_tri` canonical slice with manifest-backed Tier 0 evidence.
- Weights: predeclared neutral fixture weights only, currently equal weight per available `permno` per date.
- Engine: `core.engine.run_simulation` only.
- Output: mechanical positions, cash, turnover, transaction cost, gross exposure, net exposure, manifest identity, source quality, and blocked promotion/alert/broker booleans.
- Artifact writes: explicit only through `report_path`; default execution uses `report_path=None`.

## Required Gates

- `source_quality = canonical`.
- `extra.source_tier = tier0`.
- Manifest must exist and reconcile SHA-256, row count, schema, and date range.
- Numeric inputs must be finite before replay.
- Prices must be positive.
- Return matrix must be complete for executed exposures.
- Report must keep `promotion_ready = false`, `alerts_emitted = false`, and `broker_calls = false`.

## Blocked Scope

- No V2 proxy run on real canonical data.
- No strategy search, signal function, ranker, factor logic, PEAD, momentum, value, ML, or parameter sweep.
- No Sharpe, CAGR, alpha, drawdown, score, rank, buy/sell decision, promotion verdict, paper alert, broker call, Alpaca call, OpenClaw message, notifier call, MLflow, DVC, vectorbt, qlib, or external engine.

## Formula Register

- `target_weight_{t,s} = 1 / count_symbols_t` for each `permno` available on date `t`.
- `engine_returns_{t,s} = total_ret_{t,s}` from the canonical slice.
- `cost_rate = total_cost_bps / 10000`.
- `turnover_t = sum_s(abs(target_weight_{t,s} - current_weight_{t,s}))`.
- `transaction_cost_t = equity_before_cost_t * turnover_t * cost_rate`.
- `target_value_{t,s} = target_weight_{t,s} * equity_after_cost_t`.
- `cash_t = equity_after_cost_t - sum_s(target_value_{t,s})`.
- `gross_exposure_t = sum_s(abs(target_value_{t,s})) / equity_after_cost_t`.
- `net_exposure_t = sum_s(target_value_{t,s}) / equity_after_cost_t`.

Source path: `v2_discovery/replay/canonical_real_replay.py`.

## Evidence

- `tests/test_g5_single_canonical_replay_no_alpha.py`
- `data/registry/g5_single_canonical_replay_report.json`
- `data/registry/g5_single_canonical_replay_report.json.manifest.json`
