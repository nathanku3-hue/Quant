# Research Validity Contract

Date: 2026-05-26
Scope: Terminal Zero / Quant research, replay, backtest, optimizer, candidate-card, and dashboard promotion boundaries.
Status: `CANONICAL RESEARCH SPINE HARDENED LOCALLY; AOV CIQ AUTHORITY RECUT GREEN; REAL SEAL DATA ADMISSION OPEN`

## 2026-08-07 AOV-0 Capital IQ Authority Addendum

This addendum supersedes the **active AOV identity/source clauses only** in the 2026-08-06 addendum below. The available WRDS account lacks CRSP entitlement, and the owner explicitly authorized a destructive source-family recut rather than a compatibility bridge.

Current AOV research-validity law therefore requires:

- permanent active AOV security identity = `CIQSEC:<Capital IQ Security ID>`; company `SP_ENTITY_ID`, ticker, legacy PERMNO, and unnamespaced IDs are invalid active aliases;
- candidate universe source = `SPCIQPRO:COMPANIES_SCREENER_RESULT`;
- Rule100 PIT fundamental source = `SPCIQPRO:QUARTERLY_FUNDAMENTALS`;
- risky-asset return authority = `SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA` under one primary-security identity map;
- canonical Rule100 V1 scores remain derived, not hand-entered: runtime requires `factor_positive_count` and `technical_quality`; the three-year revenue screen alone is not a Rule100 score source;
- direct New York Fed SOFR remains the economic-cash source, with the existing after-15:00 America/New_York retrieval gate;
- `aov0_ciq_decision_cut_v1` must bind screen-result, quarterly-fundamental, security-master, market-data, and NY Fed raw-source receipts plus the four derived Parquet hashes, contract hash, CIQ-security universe hash, and cut chronology.

The historical PERMNO-specific Rule100 replay adapter may remain for audit/component history but is not active AOV first-seal authority. No dual CRSP/CIQ compatibility path is permitted.

## 2026-08-06 AOV-0 Hard-Cut Research Validity Addendum

Local hardening through executable tip `dca69fc` makes these current non-negotiable validity rules:

- evidence/frame signatures hash actual cell content;
- evidence run identity is immutable and final `evidence_manifest.json` binds exact component bytes;
- costs must be finite;
- benchmark contracts are named/closed and require implicit cash, PIT equal-weight eligible universe, and economic cash;
- primary benchmark selection is explicit, never list/dict-order dependent;
- PIT equal weight uses the same decision/rebalance schedule as the strategy;
- AOV Rule100 input requires permanent `permno`, exact `daily_portfolio` semantics, and reconciled residual cash; ticker/asset aliases are invalid;
- economic cash is official SOFR minus 25 bp, ACT/360, post-publication only, no proxy substitution;
- production insurance materiality/premium values remain owner-open, so prospective seal/review classification fails closed until supplied;
- historical/synthetic/equal-weight artifacts cannot be relabeled as admitted current Rule100/PIT inputs.

The local mechanical AOV path passes its tests, but no admitted real A1 result or real prospective A3 evidence exists. The first real seal remains the active validity boundary.

## 2026-08-06 AOV-0 Research Validity Addendum

The existing `research/` runner, strategy cartridge, benchmarks, evidence schema, metrics, status vocabulary, and Rule100 replay adapter are the canonical substrate for `ALPHA-ORGANISM-VERTICAL-0`. AOV-0 must extend this spine rather than create another backtester or evidence authority.

AOV-0 validity law:

```text
one PIT cube/version
+ one eligible-universe identity
+ one total-return matrix authority
+ one execution lag and cost contract
+ Rule100 / Parent / Child / PIT-EW / Economic-Cash arms
+ one experiment identity
+ one prospective seal/opening contract
= one comparable evidence family
```

Required corrections before implementation is research-valid:

- `F_proxy` and `C_proxy` must be dimensionally coherent;
- Parent must inherit the existing Rule100 budget/cap/lifecycle/cash semantics rather than force full investment through an independent softmax;
- dynamic terms disabled must reproduce Rule100 target weights within the frozen tolerance;
- Reversal Hazard is a bounded insurance overlay and is evaluated by a preregistered safety endpoint subject to an insurance-premium ceiling, not by a contradictory positive-return requirement;
- PIT total-return data is the sole P&L authority; corporate-action records are reconciliation-only;
- engine cash, economic cash, and future broker cash remain distinct;
- sleeve overlap and formal inference use one preregistered dependence-aware policy derived from the actual decision frequency and holding horizon;
- development success may nominate a prospective candidate but cannot promote a champion;
- seals are not alpha evidence; A3 begins only when outcomes mature and open.

`docs/checklists/aov0_working_alpha_system_checklist.md` controls the unresolved decisions and evidence gates.

## 2026-06-02 V2-D0.1 Follow-Up Validity Addendum

Source: `docs/handover/V2_D0_1_EXPERT_1_6_FOLLOWUP_RECONCILIATION_20260602.md`

PEAD is not `research_valid` unless `C3_LOCK_PEAD_V2_001_v1` exists and the run passes all fail-closed gates below:

- HAC one-sided 95% lower confidence bound on annualized daily net alpha delta vs locked C3 is greater than zero.
- Annualized daily net alpha delta point estimate is at least +2.00% per year vs locked C3.
- Family-level FDR adjusted q is at most 0.05.
- Deflated Sharpe Ratio confidence is at least 0.95 after effective-trial adjustment.
- PBO is at most 0.10 for `research_valid`.
- Base turnover cost `0.0010` and 2x cost stress `0.0020` both pass.
- PEAD-specific one-way adverse slippage stress of at least +5 bps passes unless a larger model-based stress applies.
- OOS/walk-forward evidence, PIT event timestamp leakage audit, negative controls, robustness windows, concentration checks, and reproducibility rerun pass.

For PEAD, default `hac_lag = min(63, max(5, primary_holding_window_trading_days))`. For a 20-trading-day primary holding window, `hac_lag = 20`.

Without a PIT event ledger or canonical `core.engine.run_simulation(..., strict_missing_returns=True)` run, PEAD status is `blocked`, not exploratory. Without the locked C3 comparator, PEAD can be exploratory at most.

## 1. Promotion Rule

The repo-level quant promotion rule is:

```text
No cartridge + no canonical engine run + no PIT proof + no benchmark + no costs + no evidence packet = not research-valid.
```

This rule separates four concepts that must not be collapsed:

```text
dashboard-visible        != research-valid
diagnostic replay        != research-valid
candidate hypothesis     != research-valid
optimizer allocation     != research-valid strategy evidence
```

A strategy, signal, replay, optimizer output, candidate card, or dashboard surface may only claim `research_valid` after it has passed the mechanical gates in this contract.

This contract does not approve live trading, broker automation, public performance claims, buy/sell/hold recommendations, autonomous allocation, or alerting.

## 2. Locked Decisions

### 2.1 Canonical runner location

Approve a new top-level package:

```text
research/
  __init__.py
  backtest_runner.py
  strategy_cartridge.py
  evidence_schema.py
  metrics.py
  benchmarks.py
  status.py
  adapters/
    __init__.py
    rule100_replay_adapter.py
```

Rationale:

- `core/` should remain the low-level simulation/data primitive layer.
- `strategies/` should remain strategy and replay construction logic.
- `research/` should orchestrate cartridges, canonical engine calls, PIT proof, benchmarks, costs, metrics, evidence artifacts, and promotion verdicts.

Do not place the canonical evidence runner inside `strategies/`, because that makes strategy code responsible for judging itself. Do not place the evidence runner inside `core/`, because research policy is broader than the simulation kernel.

### 2.2 Canonical PnL path

Every research-valid run must use:

```text
strategy cartridge
  -> PIT input loader / dated strategy adapter
  -> target weights, risky assets only
  -> core.engine.run_simulation(..., strict_missing_returns=True)
  -> same engine for required benchmarks
  -> metrics + PIT proof + input signatures + evidence packet
  -> mechanical verdict
```

The official PnL/cost/turnover primitive is:

```python
core.engine.run_simulation
```

Replay-attached equity curves, dashboard YTD curves, optimizer diagnostics, historical scripts, and candidate-card status fields are not authoritative research evidence.

### 2.3 Engine interface precheck

`core.engine.run_simulation` already supports the intended primitive shape:

```text
target_weights: Date index x asset columns
returns_df:     Date index x asset columns
execution lag:  target weights are shifted by one bar
turnover:       absolute change in executed risky-asset weights
costs:          turnover * cost_rate
strict mode:    fails if an executed nonzero exposure has missing return
```

Important hidden assumptions to lock in the runner:

1. Cash is implicit. Do not pass a `CASH` column to the engine unless the runner also defines a deliberate zero-return cash series and a turnover policy for cash. V0 should not pass `CASH` at all.
2. Row sums must be validated before the engine call. For long-only V0, `0 <= row_sum <= 1`.
3. The target-weight index must be sorted, unique, and date-like.
4. Asset columns should be stable identifiers, preferably `permno`, not ticker labels.
5. Benchmark target weights must be passed through the same engine, same date index, same missing-return policy, and declared cost policy.
6. The engine does not emit all evidence artifacts by itself. The runner must derive executed weights, equity curve, exposure, benchmark curves, cost breakdown, and metrics.

### 2.4 First strategy target

The first real repo adapter should be:

```text
Rule100 replay adapter, diagnostic-only
```

Rule100 is the right first target because it already has replay/context machinery, cash-closed behavior, target weights, and PIT-oriented candidate coverage. It must remain `diagnostic_only` or, at most, `exploratory` until it has a full evidence packet and robustness evidence.

The first adapter should:

1. Build or receive a `StrategyReplayBundle`.
2. Filter to `row_role == "daily_portfolio"`.
3. Exclude the `CASH` row from engine target weights.
4. Pivot `date x permno -> target_weight`.
5. Preserve `cash_residual` as evidence metadata, not as an engine asset column.
6. Feed the resulting risky-asset target matrix into the research runner.
7. Emit an evidence packet with `strategy_role = "diagnostic_lifecycle_policy"` and `promotion_status = "diagnostic_only"` unless all gates pass.

### 2.5 PIT equal-weight eligible-universe benchmark

The primary benchmark policy is:

```text
PIT equal-weight eligible universe, same replay dates, same strategy rebalance schedule,
same PIT input loader, same data-health gates, same return matrix, same strict missing-return policy,
and same declared transaction-cost policy.
```

Implementation definition:

For each strategy rebalance date `t`:

1. Ask the same PIT input loader for the eligible universe as of `t`.
2. Use only members that pass the same signal-date availability and freshness gates used by the strategy.
3. Do not use future `t+1` return availability to decide membership. If an executed benchmark constituent later has a missing return, strict missing-return mode should fail the benchmark just as it would fail the strategy.
4. Assign `1 / N` to each eligible risky asset when `N > 0`; otherwise assign all implicit cash by producing a zero-risky-weight row.
5. Forward-fill target weights between rebalance dates across the same trading calendar used for the strategy.
6. Pass the benchmark target matrix through `core.engine.run_simulation` with `strict_missing_returns=True`.

Required benchmark set for research-valid V0:

```text
cash benchmark
broad market benchmark, if available for the same window
PIT equal-weight eligible-universe benchmark
strategy-family benchmark, when available
```

The PIT equal-weight benchmark is the most important benchmark for signal validity because it answers whether the strategy beat simply owning the same eligible universe without the signal.

### 2.6 Cost naming policy

The engine parameter currently named `cost_bps` should be treated as a decimal cost rate, not an integer basis-point count.

Locked vocabulary:

```text
cost_rate = 0.0010 = 10 bps per 1.0 unit of one-way risky-asset turnover
```

V0 runner API should expose:

```python
turnover_cost_rate: float
```

and pass it into the existing engine parameter until the engine itself is renamed:

```python
run_simulation(..., cost_bps=turnover_cost_rate)
```

Artifacts must report both:

```json
{
  "turnover_cost_rate": 0.001,
  "turnover_cost_bps": 10.0,
  "cost_basis": "per_unit_one_way_risky_asset_turnover"
}
```

### 2.7 Evidence status vocabulary

The repo should lock these exact mechanical statuses:

```text
diagnostic_only
exploratory
research_valid
candidate_ready
blocked
```

Definitions:

| Status | Mechanical meaning |
|---|---|
| `diagnostic_only` | Useful artifact, replay, optimizer output, dashboard state, or internal check, but not a complete canonical evidence run. |
| `exploratory` | Canonical runner completed and artifacts were emitted, but one or more promotion requirements are missing, such as long window, OOS/walk-forward, regime coverage, robustness, or liquidity/capacity checks. |
| `research_valid` | Cartridge, canonical engine run, PIT proof, benchmark set, declared costs, metrics, input signatures, and evidence packet all passed. No live-trading or recommendation claim. |
| `candidate_ready` | `research_valid` plus required robustness evidence, OOS/walk-forward policy, sensitivity checks, regime coverage, and capacity/liquidity checks. Still not live trading. |
| `blocked` | Required gate failed: missing cartridge, no PIT proof, no benchmark, no cost policy, leakage risk, non-finite/missing executed returns, invalid weights, signature mismatch, or forbidden UI/recommendation dependency. |

Statuses must be generated by code from gate results, not hand-written prose.

### 2.8 Legacy script policy

All historical backtest scripts are quarantined as historical or exploratory unless routed through the canonical runner.

Initial quarantine pattern:

```text
scripts/*backtest*.py
scripts/*_replay.py, unless explicitly wrapped by research/backtest_runner.py
legacy result JSON/CSV files without current evidence packet
```

Quarantine means:

- keep the files;
- do not treat their outputs as research-valid;
- do not use them for promotion claims;
- optionally wrap the smallest useful one later through the canonical runner.

## 3. Strategy Cartridge Contract

Minimum V0 cartridge fields:

```yaml
strategy_id:
strategy_version:
strategy_role: diagnostic_lifecycle_policy | signal_strategy | allocation_policy | benchmark
owner:
created_at_utc:
hypothesis:

universe:
  universe_mode: r3000_pit
  membership_source:
  id_type: permno
  membership_date_policy:
  max_membership_gap_days:

inputs:
  input_loader:
  price_source:
  return_source:
  feature_source:
  source_signatures_required: true

signal:
  signal_definition:
  feature_lag_policy:
  rebalance_schedule:
  execution_lag: one_bar

portfolio:
  target_weight_adapter:
  long_only: true
  max_weight:
  gross_exposure_limit:
  cash_policy: implicit_residual_cash
  fallback_policy:

costs:
  turnover_cost_rate:
  spread_slippage_policy:
  commission_policy:
  borrow_cost_policy: not_applicable_for_long_only | required
  cash_drag_policy:

benchmarks:
  required:
    - cash
    - pit_equal_weight_eligible_universe
  optional:
    - broad_market
    - strategy_family

window:
  start_date:
  end_date:
  min_required_trading_days:
  short_window_policy:

outputs:
  evidence_schema_version:
  metric_schema_version:
  output_dir:
```

Fail closed for research-valid status if any of the following are missing:

```text
strategy_id
strategy_version
PIT universe mode / loader
input signatures
rebalance schedule
execution lag
target-weight adapter
valid target-weight matrix
declared cost policy
required benchmark policy
strict missing-return mode
PIT proof artifact
metrics artifact
verdict artifact
```

## 4. Evidence Packet V0

Every canonical run should emit:

```text
evidence/<run_id>/
  cartridge.json
  run_metadata.json
  verdict.json
  gate_results.json
  input_signatures.json
  pit_membership_proof.json
  metrics.json
  benchmark_metrics.json
  equity_curve.csv or parquet
  benchmark_curves.csv or parquet
  target_weights.csv or parquet
  executed_weights.csv or parquet
  turnover.csv or parquet
  costs.csv or parquet
  exposure.csv or parquet
  data_quality_report.json
```

V0 can use CSV when parquet dependencies are unavailable, but the schema should be stable enough to move to parquet.

Mandatory V0 metrics:

```text
cumulative_return
CAGR, when window >= 252 trading days
annualized_volatility
Sharpe
Sortino, if downside observations exist
max_drawdown
drawdown_duration
average_turnover
total_turnover
total_cost_drag
average_gross_exposure
average_cash_residual
benchmark_excess_return
tracking_error, when benchmark variance exists
information_ratio, when benchmark variance exists
missing_executed_return_count
non_finite_input_count
trading_days
rebalance_count
```

## 5. Data-Health and Leakage Gates

Hard-block gates:

```text
current universe membership used for historical rows
future fundamentals or release-date leakage
full-history normalization or ranking used in signal generation
candidate-card/dashboard labels used as alpha input
replay artifact signature mismatch
missing executed returns in strict mode
non-finite executed returns
row gross exposure > 1.0 for long-only V0
negative weights for long-only V0
missing cost policy
missing benchmark policy
missing PIT proof
```

Cash-closed but not necessarily full-run failure:

```text
no eligible PIT members on a date
membership gap exceeds policy on a date
no fresh priced members on a date
optimizer infeasible on a date
strategy adapter returns invalid date-local weights and fallback policy says cash-close
```

## 6. Runner V0 Acceptance Tests

Add tests before strategy expansion:

```text
test_research_runner_calls_core_engine_strict_mode
test_research_runner_rejects_replay_equity_as_authoritative
test_rule100_adapter_excludes_cash_from_engine_weights
test_cash_residual_is_implicit_not_engine_cash_column
test_missing_executed_return_blocks_research_valid
test_missing_cost_policy_blocks_research_valid
test_missing_benchmark_policy_blocks_research_valid
test_pit_equal_weight_uses_same_dates_and_loader
test_short_window_labels_exploratory
test_legacy_backtest_script_output_is_not_research_valid
test_status_vocab_is_closed_enum
test_cost_rate_reports_decimal_and_bps_equivalent
```

## 7. First Implementation Slice

Implement in this order:

1. Add this document.
2. Add `research/status.py` with the closed status enum.
3. Add `research/strategy_cartridge.py` with validation for required fields.
4. Add `research/backtest_runner.py` that accepts fixture target weights and returns an evidence packet.
5. Add `research/benchmarks.py` with cash and PIT equal-weight benchmark constructors.
6. Add `research/adapters/rule100_replay_adapter.py` to pivot Rule100 replay output into risky-asset target weights.
7. Add tests proving strict engine usage, implicit cash, required benchmark/cost policy, and blocked status on missing gates.

The first implementation should not attempt to rescue every legacy script. It should prove one narrow path:

```text
fixture cartridge -> canonical engine -> evidence packet -> mechanical status
Rule100 replay adapter -> canonical engine -> diagnostic evidence packet
```
