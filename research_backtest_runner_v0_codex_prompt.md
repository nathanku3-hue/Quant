# Codex Task: Research Backtest Runner v0

## Mission

Make research validity mechanical. Implement the promotion rule:

```text
No cartridge + no canonical engine run + no PIT proof + no benchmark + no costs + no evidence packet = not research-valid.
```

Do not approve live trading, broker automation, alerts, rankings, recommendations, or public performance claims.

## Decisions Already Locked

1. Create a top-level `research/` package.
2. Keep `core.engine.run_simulation` as the canonical PnL/cost/turnover primitive.
3. Use `strict_missing_returns=True` for research-valid runs.
4. Treat cash as implicit residual cash; do not pass a `CASH` column to the engine in v0.
5. Expose `turnover_cost_rate`, where `0.0010 = 10 bps per unit one-way risky-asset turnover`.
6. Lock statuses: `diagnostic_only`, `exploratory`, `research_valid`, `candidate_ready`, `blocked`.
7. First repo adapter: Rule100 replay adapter, diagnostic-only.
8. Required benchmark: PIT equal-weight eligible universe using the same PIT loader/dates/data-health gates as the strategy.

## Files to Add

```text
research/__init__.py
research/status.py
research/strategy_cartridge.py
research/evidence_schema.py
research/metrics.py
research/benchmarks.py
research/backtest_runner.py
research/adapters/__init__.py
research/adapters/rule100_replay_adapter.py
docs/architecture/research_validity_contract.md
tests/test_research_status.py
tests/test_research_backtest_runner.py
tests/test_research_benchmarks.py
tests/test_research_rule100_adapter.py
```

## Files to Modify

```text
core/engine.py                    # only docstring/name clarification if needed; avoid behavior changes in v0
strategies/strategy_replay.py     # only add adapter-friendly helper if absolutely needed
docs/architecture/...             # add contract doc
```

## Implementation Requirements

### status.py

Define a closed enum or literal constants:

```text
diagnostic_only
exploratory
research_valid
candidate_ready
blocked
```

Reject unknown status values.

### strategy_cartridge.py

Create a minimal dataclass or pydantic-free validator that requires:

```text
strategy_id
strategy_version
strategy_role
universe_mode
input_loader_name or input_source_id
rebalance_schedule
execution_lag
cost policy
benchmark policy
window
output_dir
```

Avoid new heavy dependencies.

### backtest_runner.py

Implement a runner that:

1. Validates cartridge.
2. Validates target weights:
   - sorted date index;
   - unique dates;
   - numeric values;
   - no non-finite values;
   - long-only v0 weights >= 0;
   - row sum <= 1.0 + tolerance;
   - no `CASH` column in v0.
3. Calls `core.engine.run_simulation(..., strict_missing_returns=True, cost_bps=turnover_cost_rate)`.
4. Builds executed weights using the same `target_weights.shift(1).fillna(0.0)` convention.
5. Builds equity curve from `net_ret`.
6. Runs required benchmarks through the same engine.
7. Emits an evidence packet containing metrics, run metadata, input signatures, PIT proof placeholder/proof object, benchmark metrics, and verdict.
8. Returns `blocked` when a required gate fails.

### benchmarks.py

Implement:

```text
cash benchmark: zero risky weights, zero costs, same dates
pit_equal_weight_eligible_universe benchmark: same dates, same PIT eligibility provider, same strict policy, same cost_rate unless explicitly overridden in cartridge
```

For v0 tests, a fixture PIT eligibility provider is acceptable.

### rule100_replay_adapter.py

Implement a function that receives a replay frame or `StrategyReplayBundle` and returns target weights:

```text
filter row_role == daily_portfolio
exclude ticker == CASH and permno == CASH
pivot date x permno -> target_weight
fill absent risky weights with 0.0
sort dates
validate no duplicate date/permno rows, unless exact duplicates are safely aggregated by last value with explicit reason
```

The adapter must not use `portfolio_equity` from replay as authoritative evidence.

## Tests Required

```text
test_research_status_vocab_is_closed
test_runner_calls_core_engine_with_strict_missing_returns_true
test_runner_blocks_missing_cost_policy
test_runner_blocks_missing_benchmark_policy
test_runner_blocks_cash_column_in_target_weights
test_runner_blocks_missing_executed_returns
test_runner_emits_required_evidence_files
test_pit_equal_weight_benchmark_uses_same_dates
test_rule100_adapter_excludes_cash_rows
test_rule100_adapter_rejects_replay_equity_as_authoritative
```

## Acceptance Criteria

A fixture cartridge can run end-to-end and emit an evidence packet, but no strategy is promoted by default. Rule100 can be routed through the runner as `diagnostic_only` or `exploratory`, not `research_valid`, unless every required gate is present.
