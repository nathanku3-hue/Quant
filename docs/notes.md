# Feature Engineering Notes

## Phase 53-61 Planning Formula Notes

**Date**: 2026-03-15

### Governance Reuse Anchors (Already Implemented)
- `N_eff ~= N * (1 - rho_avg) + 1`
- `lambda_logit_rank = log(r / (1 - r))`
- `PBO = mean(lambda_logit_rank <= 0)`
- `DSR = PSR(sr_hat, sr_benchmark, n_obs, skewness, kurtosis)`
- Existing implementation files:
  - `utils/statistics.py`
  - `scripts/parameter_sweep.py`
  - `tests/test_statistics.py`
  - `tests/test_parameter_sweep.py`

### Phase 53-61 Contracts (Execution Status Noted)
- `trial_budget_outer_fold in [9, 18]`
- `global_active_variants <= 18` is the default governance ceiling; only an explicit execution packet may narrow or override it.
- `phase53_execution_authorized = 1[(reply contains exact 'approve next phase') and (NextPhaseApproval == APPROVED)]`
- `research_catalog_path = "research_data/catalog.duckdb"` (read-only research contract)
- `allocator_state_view = read_parquet("research_data/allocator_state_cube/variant_id=*/*.parquet", hive_partitioning=true)` (registered in read-only catalog)
- `research_guard = snapshot_date <= 2022-12-31` (required SQL wrapper predicate for research queries; enforced in `scripts/run_allocator_cpcv.py`, which hard-rejects any `max_date > 2022-12-31`)
- `phase53_memory_gate = peak_process_memory_mb < 2048` (recorded by `scripts/benchmark_phase53_data_kernel.py` for allocator_state and CPCV shard scans)
- Phase 53 research-v0 data-kernel contracts are runtime-enabled and evidenced in:
  - `data/processed/phase53_source_manifest.json`
  - `research_data/allocator_state_cube/allocator_state_manifest.json`
  - `research_data/alloc_cpcv_splits/cpcv_splits_manifest.json`
  - `docs/context/e2e_evidence/phase53_allocator_cpcv_run.json`
  - `docs/context/e2e_evidence/phase53_data_kernel_benchmark.json`
- `allocator_state_source_{i,t} = melt(phase17_3_parameter_sweep_return_streams)[variant_id=i, snapshot_date=t, period_return_{i,t}]` for `snapshot_date_t <= 2022-12-31` (implemented in `scripts/derive_phase53_sources_from_phase17.py`)
- `fold_t = build_cscv_block_series(unique(snapshot_date), n_blocks=6)` and `cpcv_source_{i,t} = (fold_t, snapshot_date_t, variant_id_i, period_return_{i,t})` (implemented in `scripts/derive_phase53_sources_from_phase17.py` via `utils/statistics.py`)
- `research_quarantine_windows = deny_root(WriteData/AddFile, AppendData/AddSubdirectory) + allow_tree(ReadAndExecute)` for `research_data/` so `connect_research()` temp-write probe fails closed while the DuckDB catalog stays readable
- `f(margin, supply, demand, pricing_power) := score_100` for Phase 54 (authoritative mapping for Rule-of-100 pass flag)
- `rule100_pass_t = score_100` (authoritative Rule-of-100 pass flag for Phase 54)
- `score_100` is computed in `strategies/supercycle_signal.py::calculate_supercycle_score`
- `rule100_pass_lag = shift(rule100_pass_t, 1) by permno` and `rule100_boost = 0.5 * rule100_pass_lag` (Phase 54 core sleeve booster in `strategies/company_scorecard.py::build_phase20_conviction_frame`)
- `conviction_score = clip(raw_conviction + rule100_boost, 0, 10)` (Phase 54 core sleeve lattice path in `strategies/company_scorecard.py::build_phase20_conviction_frame`)
- `rule100_pass_rate = mean(rule100_pass_t)` and `rule100_pass_controller = 1[0.15 <= rule100_pass_rate <= 0.20]` (controller uses raw pass rate)
- `rule100_input_complete = 1[inputs_complete]` and `rule100_pass_rate_eligible = mean(rule100_pass_t | rule100_input_complete = 1)` (diagnostic only)
- `rule100_input_complete_share = mean(rule100_input_complete)` (diagnostic coverage of Rule-of-100 inputs)
- Rule-of-100 input sourcing: when `delta_revenue_inventory`, `gm_accel_q`, or `operating_margin_delta_q` are missing from features/SDM, they may be sourced from `data/processed/daily_fundamentals_panel.parquet`; `sales_accel_q` is optional and falls back to `delta_revenue_inventory` inside `strategies/supercycle_signal.py::calculate_supercycle_score`
- Phase 54 returns coverage filter: features are restricted to permnos with price rows in the evidence window; runner outputs `permnos_total`, `permnos_with_returns`, `permnos_dropped`
- Phase 54 returns merge: when using `prices_tri.parquet`, missing return rows/values are backfilled from `prices.parquet` with primary precedence
- Phase 54 returns repair artifact: `data/processed/phase54_core_sleeve_returns_repaired.parquet` persists the TRI+prices union with `pct_change` fallback and keep-last dedupe on `date/permno`
- Phase 54 raw overlap diagnostics in `scripts/phase20_full_backtest.py`: `overlap_pairs_total = |{(date, permno) in features} ∩ {(date, permno) in repaired_returns}|`, `feature_overlap_rate = overlap_pairs_total / feature_pairs_total`, and `returns_overlap_rate = overlap_pairs_total / returns_pairs_total`
- Phase 54 executed-exposure diagnostics in `scripts/phase20_full_backtest.py`: `executed_exposure_total_cells = sum(shift(weights_ex_cash, 1) != 0)`, `executed_exposure_missing_cells = sum(1[shift(weights_ex_cash, 1) != 0 and isna(aligned_returns_ex_cash)])`, and `executed_exposure_missing_rate = executed_exposure_missing_cells / executed_exposure_total_cells`
- Phase 54 overlap sidecar artifact: `data/processed/phase54_core_sleeve_overlap_diagnostics.json` persists both raw pair overlap and executed-exposure overlap ahead of the strict evidence gate
- Target Rule-of-100 breadth: `15%-20%` pass rate measured on `rule100_pass_t`, pending the final `mu_c / delta_c` lattice check
- Phase 54 evidence guard: `end_date <= 2022-12-31` enforced by `_validate_end_date_guard` in `scripts/phase20_full_backtest.py` via `RESEARCH_MAX_DATE`
- Phase 54 C3 loader current-price guard in `scripts/phase20_full_backtest.py::_apply_c3_current_price_guard`: `c3_current_price_ok_t = 1[notna(adj_close_t)]`
- Phase 54 baseline validity guard: `c3_score_valid_t = score_valid_t * c3_current_price_ok_t` and `c3_score_t = score_t if c3_score_valid_t = 1 else NaN` (applies to C3 baseline rows only; Phase 20 scoring path unchanged)
- Phase 54 C3 loader diagnostics: `c3_loader_price_guard_rows = sum(1[score_valid_t = 1 and isna(adj_close_t)])`, `c3_loader_price_guard_permnos = nunique(permno | invalidated)`, and `c3_loader_price_guard_applied = 1[c3_loader_price_guard_rows > 0]`
- Phase 54 evidence-clear predicate (technical gate only): `phase54_evidence_clear = 1[(missing_active_return_cells.c3 = 0) and (missing_active_return_cells.phase20 = 0) and (same_window_same_cost_same_engine = 1) and (SAW Verdict = PASS)]`
- Phase 54 D-304 strategic follow-up uses the published `phase54_core_sleeve_summary.json` and `phase54_core_sleeve_overlap_diagnostics.json` as SSOT baseline; `ABORT_PIVOT`, `rule100_pass_rate`, and `rule100_pass_controller` affect strategic evaluation only and do not negate `phase54_evidence_clear`
- Phase 54 D-305 strategic rejection predicate: `phase54_baseline_accept = 1[(decision != "ABORT_PIVOT") and (rule100_pass_controller = 1)]`
- Phase 54 D-305 targeted-tuning trigger: `phase54_tuning_trigger = 1[(decision = "ABORT_PIVOT") or (rule100_pass_controller = 0)]` with the live packet currently evaluating `1`
- Phase 54 D-306 movable tuning knobs only: `{demand_floor, margin_floor, r2_threshold, convexity_threshold, ramp_exception_threshold, ramp_margin_floor}` from `strategies/supercycle_signal.py::SupercycleConfig`
- Phase 54 D-306 bounds: `demand_floor in [-0.02, 0.02]`, `margin_floor in [-0.02, 0.02]`, `r2_threshold in [0.80, 0.95]`, `convexity_threshold in [1.25, 2.00]`, `ramp_exception_threshold in [0.12, 0.24]`, `ramp_margin_floor in [-0.05, 0.00]`
- Phase 54 D-306 frozen surfaces: `rule100_pass_t = score_100`, `rule100_boost = 0.5 * shift(rule100_pass_t, 1)`, `power_law_exponent`, `gravity_multiplier`, `demand_power_scale`, `margin_power_scale`, `gravity_denominator`, `support_sma_window`, `momentum_lookback`, `softmax_temperature`, `top_n_green`, `top_n_amber`, `max_gross_exposure`, loader/evidence semantics, and all Phase 53/kernel paths
- Phase 54 D-306 success predicate: `phase54_tuning_success = 1[(phase54_evidence_clear = 1) and (rule100_pass_controller = 1) and (fresh_artifacts = 1) and (SAW Verdict = PASS)]`
- Phase 54 D-307 tuned artifact fields in `scripts/phase20_full_backtest.py`: `{rule100_demand_floor, rule100_margin_floor, rule100_r2_threshold, rule100_convexity_threshold, rule100_ramp_exception_threshold, rule100_ramp_margin_floor}` emitted by `_rule100_tuning_summary_fields`
- Phase 54 D-307 ceiling config: `phase54_d307_ceiling_config = 1[(rule100_demand_floor = -0.02) and (rule100_margin_floor = -0.02) and (rule100_r2_threshold = 0.80) and (rule100_convexity_threshold = 1.25) and (rule100_ramp_exception_threshold = 0.12) and (rule100_ramp_margin_floor = -0.05)]`
- Phase 54 D-307 controller gap: `phase54_controller_gap = max(0, 0.15 - rule100_pass_rate)`; the fresh tuned packet in `data/processed/phase54_d306_tuned_summary.json` evaluates to `0.02357808340727594`
- Phase 54 D-307 hard-stop predicate: `phase54_d307_hard_stop = 1[(phase54_evidence_clear = 1) and (phase54_d307_ceiling_config = 1) and (rule100_pass_controller = 0)]`
- Phase 54 D-308 SSOT baseline for strategic disposition: `{data/processed/phase54_core_sleeve_summary.json, data/processed/phase54_core_sleeve_overlap_diagnostics.json}`
- Phase 54 D-308 option set is closed: `phase54_d308_option in {A_accept_current_baseline, B_final_bounded_widening}`
- Phase 54 D-308 option A predicate: `phase54_d308_accept_current_baseline = 1[(phase54_evidence_clear = 1) and (rule100_pass_controller = 0)]`
- Phase 54 D-308 option B predicate: `phase54_d308_final_bounded_widening = 1[(phase54_evidence_clear = 1) and (phase54_d307_hard_stop = 1) and (surface = six SupercycleConfig thresholds inside D-301 only)]`
- Phase 54 D-308 option B bounds: `demand_floor in [-0.05, 0.05]`, `margin_floor in [-0.05, 0.05]`, `r2_threshold in [0.65, 0.98]`, `convexity_threshold in [1.00, 2.75]`, `ramp_exception_threshold in [0.05, 0.35]`, `ramp_margin_floor in [-0.15, 0.15]`
- Phase 54 D-308 selected option: `phase54_d308_option = B_final_bounded_widening`
- Phase 54 D-308 option A rejected: `phase54_d308_option_a_rejected = 1[(phase54_d308_option = B_final_bounded_widening)]`
- Phase 54 D-308 option B authorized: `phase54_d308_option_b_authorized = 1[(phase54_d308_option = B_final_bounded_widening)]`
- Phase 54 closeout predicate: `phase54_complete = 1[(phase54_evidence_clear = 1) and (phase54_rule100_rejected = 1) and (SAW Verdict = PASS)]`
- Phase 54 D-309 rejection: `phase54_rule100_rejected = 1[(phase54_evidence_clear = 1) and (rule100_pass_controller = 0) and (d308b_max_bound_executed = 1)]`
- Phase 55 baseline: Rule-of-100 sleeve inactive (`rule100_pass_t` forced to 0 or removed from lattice path) unless a new governance packet explicitly reopens it
- `allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]`
- Phase 55 Expert-Locked Definitions (verbatim):
  - Canonical evidence input surface = read-only Phase 53 research kernel only: (i) allocator_state via research_data/catalog.duckdb / research_data/allocator_state_cube, and (ii) CPCV shard reads via allocator_cpcv.sql + scripts/run_allocator_cpcv.py over research_data/alloc_cpcv_splits, both hard-clamped to snapshot_date <= 2022-12-31. Phase 54 SSOT artifacts may be cited as comparator/governance references only
  - Nested CPCV = each outer CPCV split is the sole source of final allocator evidence, while allocator ranking/selection is performed only inside an inner CPCV loop built from that outer-train partition. The selected allocator is then executed exactly once on the untouched outer-test fold
  - WRC = WRC_p is a co-reported diagnostic and governance corroborator, not a new hard unlock clause in Phase 55. Publish WRC_p beside SPA_p in the evidence pack, but keep the hard gate unchanged as allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]
  - Same-engine = same_window_same_cost_same_engine = 1[(all compared runs share identical start_date/end_date and end_date <= 2022-12-31) and (all compared runs share one fixed cost_bps) and (all governed return/equity series are produced by core.engine.run_simulation under D-04 shift(1) and D-05 turnover-tax semantics)]. Any result computed outside that path is diagnostic-only and non-gating.
- Phase 55 Evidence (verbatim):
  - `rule100_pass_rate = 0.024419920141969833`
  - `- **Phase 55 - Opportunity-Set Controller**: apply nested CPCV + DSR/PBO/SPA to allocator rules; reuse Phase 17 math; new allocator wrapper and SPA helper required.`
  - `allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]`
  - `guard = f"snapshot_date <= DATE '{max_date}'"`
- Phase 55 Allocator Gate:
  - Phase 55 SPA/WRC helpers: `utils/spa.py::spa_p_value`, `utils/spa.py::wrc_p_value`
  - Nested CPCV wrapper: `scripts/phase55_allocator_governance.py::compute_nested_cpcv`
  - Gate formula (unchanged): `allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]`
  - Scalar reducers: `pbo=mean`, `dsr=median`, `spa_p=median`, `wrc_p=median`
  - Inner selection reducer: `selected_variant = argmax(selection_count, median_test_sharpe, median_train_sharpe, variant_id_ascending)`
  - `WRC_p = diagnostic only`
- `pead_window_return_{i,e} = prod_{d=1..5}(1 + r_{i,e+d}) - 1`
- Initial PEAD gates:
  - `value_rank_pct >= 0.60`
  - `adv_usd >= 5_000_000`
  - `days_since_earnings <= 63`
- Phase 56 bounded PEAD runner (`scripts/phase56_pead_runner.py`):
  - `pead_score_{i,t} = capital_cycle_score_{i,t}`
  - `adv_usd_{i,t} = mean_{k=0..19}(adj_close_{i,t-k} * volume_{i,t-k})`
  - `days_since_earnings_{i,t} = date_t - release_date_{i,t}`
  - `pead_gate_{i,t} = 1[(quality_pass_{i,t} = 1) and (adv_usd_{i,t} >= 5_000_000) and (0 <= days_since_earnings_{i,t} <= 63) and (value_rank_pct_{i,t} >= 0.60)]`
  - `value_rank_pct_{i,t} = pct_rank(capital_cycle_score_{i,t} within date t, ascending)`
  - `target_weight_{i,t} = 1 / n_selected_t if pead_gate_{i,t} = 1 else 0`
  - governed return, turnover, and cost series are produced by `core.engine.run_simulation` under D-04 shift(1) and D-05 turnover-tax semantics
  - bounded source paths: `data/processed/features.parquet`, `data/processed/daily_fundamentals_panel.parquet`, `data/processed/prices.parquet`, `scripts/phase56_pead_runner.py`, `core/engine.py`
- `shadow_nav_t = sum_s w_{s,t-1} * (1 + r_{s,t}) - costs_t`
- `w_{t+1} = Pi_Delta(w_0 + B x_t)` for the planned Phase 61 BPPP meta-layer

### Planned Implementation Anchors / Gaps
- Reuse candidates:
  - `utils/statistics.py`
  - `scripts/parameter_sweep.py`
  - `strategies/supercycle_signal.py`
  - `data/calendar_updater.py`
  - `scripts/build_shadow_monthly.py`
  - `scripts/phase37_portfolio_construction_runner.py`
- New implementation still required:
  - allocator CPCV / SPA wrapper
  - BPPP meta-layer runner
  - Shadow-v1 monitoring/alert surface built on allocator_state

### Hook Verification Ledger (Planning Round Evidence)
| Claim | checked_at | command | result |
| --- | --- | --- | --- |
| Governance math exists | 2026-03-15 Asia/Macau | `rg -n "effective_number_of_trials|cscv_analysis|deflated_sharpe_ratio" utils/statistics.py` | Matched the three reusable governance functions in `utils/statistics.py`. |
| Sweep checkpoint/governance runner exists | 2026-03-15 Asia/Macau | `rg -n "effective_number_of_trials|cscv_analysis|deflated_sharpe_ratio|checkpoint" scripts/parameter_sweep.py` | Matched the imported governance functions plus checkpoint/resume flow in `scripts/parameter_sweep.py`. |
| Rule-of-100 score anchor exists | 2026-03-15 Asia/Macau | `rg -n "score_100" strategies/supercycle_signal.py scripts/rule_100_backtest_decades.py dashboard.py docs/phase36_rule100_registry.md` | Matched `score_100` in `strategies/supercycle_signal.py`; no competing Phase 53 bridge exists yet. |
| Earnings calendar reuse surface exists | 2026-03-15 Asia/Macau | `rg -n "earnings_calendar" data/calendar_updater.py data/dashboard_data_loader.py strategies/investor_cockpit.py` | Matched current calendar write/read/consume surfaces for future PEAD work. |
| Event-study scaffold exists | 2026-03-15 Asia/Macau | `rg -n "event study|event_study|earnings" backtests/event_study_csco.py` | Matched the bounded event-study scaffold in `backtests/event_study_csco.py`. |
| Shadow/risk primitive reuse exists | 2026-03-15 Asia/Macau | `rg -n "phase37|shadow|atomic|replace" strategies/phase37_portfolio_registry.py scripts/phase37_risk_diagnostics.py scripts/phase37_portfolio_construction_runner.py scripts/build_shadow_monthly.py views/elite_sovereign_view.py` | Matched Phase 37 registry, atomic write helpers, shadow builder, and dashboard reader surfaces. |
| Allocator kernel hooks now present; meta hooks remain missing | 2026-03-15 Asia/Macau | `rg -n "allocator_cpcv\\.sql|allocator_state|connect_research|BPPP|White Reality Check|Hansen SPA|Reality Check" . -g "!docs/context/**" -g "!docs/handover/phase53_kickoff_memo_20260314.md" -g "!docs/phase_brief/phase53-brief.md" -g "!docs/notes.md" -g "!docs/decision log.md"` | Matches `allocator_cpcv.sql`, `allocator_state`, and `connect_research()` in Phase 53 data-kernel files; SPA/Reality Check/BPPP remain absent. |
| No direct repo-local Phase 53 source-contract parquet existed; explicit transform required | 2026-03-15 Asia/Macau | `python duckdb schema scan across data/processed/**/*.parquet for {variant_id,snapshot_date} and {fold,snapshot_date}` | No direct local parquet exposed both required source contracts; fixed by adding `scripts/derive_phase53_sources_from_phase17.py` over Phase 17.3 sweep artifacts. |
| Phase 53 source contracts derived from Phase 17.3 sweep artifacts | 2026-03-15 Asia/Macau | `.venv\Scripts\python scripts\derive_phase53_sources_from_phase17.py` | Produced `data/processed/phase53_allocator_state_source.parquet` and `data/processed/phase53_cpcv_source.parquet` with `105081` rows, `165` variants, `6` folds, and max `snapshot_date = 2022-12-21`. |
| Phase 53 guarded SQL evidence captured | 2026-03-15 Asia/Macau | `.venv\Scripts\python scripts\run_allocator_cpcv.py` | Wrote `docs/context/e2e_evidence/phase53_allocator_cpcv_run.json` with `row_count = 105081` and `guard_predicate = snapshot_date <= DATE '2022-12-31'`. |
| Phase 53 8-thread benchmark evidence captured | 2026-03-15 Asia/Macau | `.venv\Scripts\python scripts\benchmark_phase53_data_kernel.py` | Wrote `docs/context/e2e_evidence/phase53_data_kernel_benchmark.json` with `overall_peak_memory_mb = 44.363281`, `memory_source = winapi_working_set`, and `within_memory_limit = true`. |

## Phase 52 Week 3 SMA200 Trend Filter

**Date**: 2026-03-13

### Orthogonal Exposure Formula
```python
# Two independent dimensions
trend_multiplier = 1.0 if SPY_price >= SPY_SMA200 else 0.5
regime_exposure = 0.4 if realized_vol > 0.25 else 1.0

# Final exposure (multiplicative, not additive)
final_exposure = trend_multiplier × regime_exposure
```

### Four Market States
| State | RV Condition | SPY Condition | Regime Exp | Trend Mult | Final Exp |
|-------|-------------|---------------|------------|------------|-----------|
| 1. Normal + Uptrend | RV ≤25% | SPY ≥ SMA200 | 1.0 | 1.0 | 1.0 |
| 2. Crisis + Uptrend | RV >25% | SPY ≥ SMA200 | 0.4 | 1.0 | 0.4 |
| 3. Normal + Downtrend | RV ≤25% | SPY < SMA200 | 1.0 | 0.5 | 0.5 |
| 4. Crisis + Downtrend | RV >25% | SPY < SMA200 | 0.4 | 0.5 | 0.2 |

### Data Sources
- **SPY**: permno=84398 from prices.parquet
- **SMA200**: 200-day simple moving average of SPY adj_close
- **Coverage**: 2000-01-03 to 2024-12-31 (full backtest coverage)
- **Warmup**: First 200 days for SMA200 initialization

### Trial 14 Baseline (Locked)
- RV threshold: 25% (annualized)
- Defensive exposure: 0.4 (40% in high-vol regime)
- Defensive top_n: 5 stocks
- Sharpe: 0.644 (target: >0.65)
- Max DD 2008: -39.32% (+22.68% vs Week 1 baseline)

### Dual Acceptance Criteria
**Absolute Thresholds** (3/4 required):
- Max DD 2008 < 45%
- Max DD 2020 < 25%
- Sharpe 2007-2024 > 0.65
- Recovery < 240 days

**Delta Guardrails** (2/3 required):
- Sharpe ≥ +0.05 vs Trial 14
- Max DD ≥ -3% vs Trial 14
- Recovery ≥ -30 days vs Week 1

**Pass**: 3/4 absolute OR 2/3 delta

### Execution Parity and Exact RV Aggregation
```python
# Keep Week 3 on the shared engine path so turnover/costs match Weeks 1/2
results = run_simulation(target_weights=target_weights, returns_df=returns_matrix, cost_bps=10)

# Aggregate chunked market RV exactly per date
rv_t = sum(chunk_return_sq_t) / sum(chunk_obs_t)
```

- Shared engine path source: `backtests/phase52_week3_sma200.py` (`run_sma200_trial`)
- Exact RV aggregation source: `backtests/phase52_week3_sma200.py` (`compute_market_realized_vol_efficient`)
- Why it matters: preserves apples-to-apples turnover/cost semantics and avoids mean-of-means drift in the market-state series that drives the Week 3 overlay

### Implementation Status
- ✓ Code complete: `backtests/phase52_week3_sma200.py`
- ✓ Tests pass: 17/17 in `tests/test_phase52_week3_sma200.py`
- ✓ Backtest execution complete: exact-RV artifact published in `data/processed/phase52_week3/week3_sma200_results.json`
- ✓ Shared-engine parity restored: Week 3 now uses `core.engine.run_simulation` for turnover/cost accounting
- ✓ Closeout lock: Week 3 accepted as the final Phase 52 endpoint under `D-284`
- ✓ Local Reviewer C verification passed on the final artifact set; the earlier block was reviewer-lane artifact access, not a data-integrity defect

## Phase 51 Supercycle Formula Notes

**Date**: 2026-03-13

### Scorer Contract
- `sales_accel_eff = sales_accel_q if finite else delta_revenue_inventory`
- `gm_accel_eff = gm_accel_q if finite else operating_margin_delta_q`
- `demand_pass = (sales_accel_eff > demand_floor) and (delta_revenue_inventory > demand_floor)`
- `margin_pass = (gm_accel_eff > margin_floor) and (operating_margin_delta_q > margin_floor)`
- `demand_strength = max(sales_accel_eff, 0) + max(delta_revenue_inventory, 0)`
- `margin_strength = max(gm_accel_eff, 0) + max(operating_margin_delta_q, 0)`
- `alpha_quad_raw = sum((1 + scale_i * max(component_i, 0)) ^ power_law_exponent - 1)`
- Demand scales: `2.0` for `sales_accel_eff` and `delta_revenue_inventory`
- Margin scales: `8.0` for `gm_accel_eff` and `operating_margin_delta_q`
- `gravity_haircut = (delta_us10y_3m / 0.50) * gravity_multiplier`
- `alpha_quad_adjusted = alpha_quad_raw - gravity_haircut`
- `r2_proxy = clip(cosine(demand_vector, margin_vector), 0, 1) ^ 2`
- `convexity_proxy = 1 + 10 * min(demand_strength, margin_strength)`
- `ramp_exception = demand_pass and demand_strength >= 0.18 and gm_accel_eff >= -0.02 and operating_margin_delta_q >= -0.02`
- `score_100 = 1` iff:
  - `demand_pass`
  - `alpha_quad_adjusted > 0`
  - and either:
    - `margin_pass and r2_proxy >= r2_threshold and convexity_proxy >= convexity_threshold`
    - or `ramp_exception`

### Grid Harness Contract
- Grid size: `5 x 5 x 3 x 3 = 225`
- Training rows: `225 x 3 x 8 = 5,400`
- `strategy_returns_t = signal_{t-1} * asset_return_t`
- `total_return = prod(1 + strategy_returns) - 1`
- `sharpe_ratio = mean(strategy_returns) / std(strategy_returns) * sqrt(252)`
- `max_drawdown = min(equity / cummax(equity) - 1)`
- `information_coefficient = corr(signal_t, strategy_returns_{t+1})`
- Strict survivor filter:
  - `mean_sharpe > 0.8`
  - `ticker_success_rate > 0.75`
  - `window_success_rate > 0.66`
  - `mean_max_dd > -0.25`
- Fallback survivor rule:
  - if no row passes the strict filter, emit the top-ranked `top_n` rows with `passes_filters = False` and `selection_basis = "top_ranked_fallback"`

### Implementation Files
- `strategies/supercycle_signal.py`
- `backtests/optimize_supercycle_grid.py`
- `tests/test_supercycle_signal.py`
- `tests/test_optimize_supercycle_grid.py`

---

## Quality Composite Formula

**Formula**: `quality_composite = 0.4 * ROIC + 0.3 * ROE + 0.3 * Revenue_Growth_YoY`

**Components**:

1. **ROIC (Return on Invested Capital)**: 40% weight
   - `ROIC = operating_income_ttm / invested_capital_avg`
   - `operating_income_ttm` = trailing 4-quarter sum of `oibdpq`
   - `invested_capital` = `ceqq` (equity) + `dlttq` (long-term debt) + `dlcq` (short-term debt)
   - `invested_capital_avg` = 4-quarter rolling average

2. **ROE (Return on Equity)**: 30% weight
   - `ROE = niq / ceqq`
   - `niq` = net income quarterly
   - `ceqq` = common equity quarterly

3. **Revenue Growth YoY**: 30% weight
   - `Revenue_Growth_YoY = (revtq - revtq_lag4) / revtq_lag4`
   - Year-over-year quarterly revenue growth

**Rationale**:
- Simple, auditable 3-term blend
- Temporary explicit formula for Phase 35 pilot
- Future: Replace with research-backed quality basket after pilot validation

**Source**: Phase 1.1 closure report, Phase 2 implementation

---

# Phase 16.13 Formula Notes (Proxy Gate)

Date: 2026-02-17

## 1) Derived Quarterly Metrics
- `sales_growth_q = pct_change(total_revenue_q, 1)`
- `sales_accel_q = delta(sales_growth_q)`
- `op_margin_accel_q = delta(operating_margin_delta_q)`
- `bloat_q = delta(ln(total_assets_q - inventory_q)) - delta(ln(total_revenue_q))`
- `net_investment_q = (abs(capex_q) - depreciation_q) / lag(total_assets_q, 1)`

## 2) Inventory Quality Proxy
- `z_inventory_quality_proxy = z(sales_accel_q) + z(op_margin_accel_q) - z(bloat_q) - 0.5*z(net_investment_q)`

## 3) Discipline Conditional Gate
- Base penalty: `penalty = asset_growth_yoy * (1 - sigmoid(operating_margin_delta_q / smooth_factor))`
- Proxy gate waiver: if `z_inventory_quality_proxy > 0`, then `penalty = 0`
- Output term: `z_discipline_cond = z(-penalty)` (cross-sectional per date)

## 4) Capital Cycle Score
- `capital_cycle_score = 0.4*z_moat + 0.4*z_discipline_cond + 0.2*z_demand`

## 5) Implementation Files
- `data/fundamentals_updater.py` (raw + derived quarterly fields)
- `data/fundamentals_compustat_loader.py` (Compustat parity for derived fields)
- `data/fundamentals.py` (snapshot/daily broadcast propagation)
- `data/fundamentals_panel.py` (daily panel schema + SQL projection)
- `data/feature_specs.py` (proxy score + discipline waiver logic)

---

## Phase 36 Survivor/Bundle Formula Notes

**Date**: 2026-03-08

### Frozen Survivor -> Feature Mapping
- `quality_composite_raw -> quality_composite`
- `vol_beta_63d -> rolling_beta_63d`
- `composite_score_baseline -> composite_score`

### Bundle Execution Contract
- Bundle registry lives in: `strategies/phase36_bundle_registry.py`
- Bundle execution path lives in: `scripts/signal_sweep_runner.py` (`--mode bundle`)
- Each bundle input column is first cross-sectionally z-scored by `date`
- Equal-weight bundle formulas are then evaluated on the normalized feature columns

### Explicit Bundle Formulas
- `bundle_quality_vol = (zscore(quality_composite) + zscore(rolling_beta_63d)) / 2`
- `bundle_quality_composite = (zscore(quality_composite) + zscore(composite_score)) / 2`
- `bundle_vol_composite = (zscore(rolling_beta_63d) + zscore(composite_score)) / 2`
- `bundle_all_three = (zscore(quality_composite) + zscore(rolling_beta_63d) + zscore(composite_score)) / 3`

### Baseline Delta Gate
- Validation gate: `delta_ic_val = bundle_ic_validation - baseline_ic_validation`
- Holdout gate: `delta_ic_hold = bundle_ic_holdout - baseline_ic_holdout`
- Promotion contract: validation and holdout delta IC must both be populated and `> 0`
- Calibration delta IC is recorded as a diagnostic, not a gating requirement

### Robustness Round Stress Contract
- `friction_drag = turnover_monthly * 12 * (cost_bps / 10000)`
- `ic_net_estimated = ic_gross - friction_drag`
- `kill_triggered = (window == "holdout") and (cost_bps == 20) and (ic_net_estimated <= 0)`
- `bundle_decision = Pause if kill_triggered; Continue if delta_ic_val > 0 and delta_ic_hold > 0; otherwise Pivot`
- `portfolio_decision = Continue if continue_votes >= 3; Pause if pause_votes >= 3; otherwise Pivot`
- Implementation file: `scripts/phase36_bundle_robustness_round.py`

### Implementation Files
- `strategies/phase36_bundle_registry.py` (bundle definitions and survivor mapping)
- `scripts/signal_sweep_runner.py` (cross-sectional normalization, baseline loading, delta computation, fail-closed bundle gate)
- `scripts/phase36_bundle_robustness_round.py` (robustness stress grid, 20bps holdout floor, majority rubric, artifact emission)

---

## Phase 37 Portfolio Construction Formula Notes

**Date**: 2026-03-09

### Frozen Sleeve Contract
- Active sleeves: `bundle_quality_vol`, `bundle_vol_composite`, `bundle_all_three`
- Paused sleeve: `bundle_quality_composite`
- Registry file: `strategies/phase37_portfolio_registry.py`
- Comparator path: `data/processed/features_phase35_repaired.parquet`
- PnL path: `core/engine.py` via `run_simulation(...)`

### Sleeve Return and Risk-Primitive Contract
- `sleeve_return_t = equity_t / equity_{t-1} - 1`
- `vol_63d_i(t) = std(sleeve_return_{i,t-62:t}) * sqrt(252)`
- `cov_126d_{i,j}(t) = cov(sleeve_return_{i,t-125:t}, sleeve_return_{j,t-125:t})`
- `corr_126d_{i,j}(t) = cov_126d_{i,j}(t) / (vol_63d_i(t) * vol_63d_j(t))`
- Risk primitives are persisted in `data/processed/phase37_portfolio/portfolio_risk_primitives.parquet`
- Implementation file: `scripts/phase37_risk_diagnostics.py`

### Portfolio Method Formulas
- `equal_weight_i = 1 / 3`
- `inverse_vol_raw_i = 1 / vol_63d_i`
- `inverse_vol_weight_i = normalize(clamp(inverse_vol_raw_i, 15%, 50%))`
- `capped_risk_budget = argmin_w Σ_i (risk_share_i - 1/3)^2`
- Subject to: `Σ_i w_i = 1`, `0.15 <= w_i <= 0.50`, `w_i >= 0`, `gross_exposure = 1.0`
- Implementation file: `scripts/phase37_portfolio_construction_runner.py`

### Ex-Ante Risk and Guardrail Formulas
- `portfolio_var = w' Σ w`
- `marginal_risk_i = (Σ w)_i`
- `risk_contribution_i = w_i * marginal_risk_i`
- `risk_share_i = risk_contribution_i / portfolio_var`
- `gross_turnover_t = 0 if first valid rebalance else 0.5 * Σ_i |w_{i,t} - w_{i,t-1}|`
- `HHI_t = Σ_i w_{i,t}^2`
- Hard guards:
  - optimized methods require `15% <= w_i <= 50%`
  - optimized methods require `risk_share_i <= 40%`
  - all methods require `gross_turnover_t <= 25%` after the first valid rebalance
  - optimized methods require `HHI_t <= 0.375`
  - infeasible or unstable optimized methods are fail-closed, never silently relaxed

### Performance and Delta Contract
- `equity_t = Π_{k<=t} (1 + net_ret_k)` from `run_simulation(...)`
- `CAGR = equity_T^(252 / N_days) - 1`
- `realized_vol = std(net_ret) * sqrt(252)`
- `Sharpe = mean(net_ret) / std(net_ret) * sqrt(252)` when `std(net_ret) > 0`, else `0`
- `max_drawdown = min(equity / cummax(equity) - 1)`
- `delta_cagr_window = portfolio_cagr_window - baseline_cagr_window`
- `delta_sharpe_window = portfolio_sharpe_window - baseline_sharpe_window`
- Baseline files: `data/processed/phase35_reruns/phase35_baseline_corrected_*_target_weights.parquet`

### Recommendation Contract
- `method_decision = Pause` if any hard block occurs
- `method_decision = Continue` if `delta_cagr_validation > 0`, `delta_cagr_holdout > 0`, `delta_sharpe_validation > 0`, and `delta_sharpe_holdout > 0`
- `method_decision = Pivot` otherwise
- `portfolio_decision = Continue` if `continue_votes >= 2`; `Pause` if `pause_votes >= 2`; otherwise `Pivot`
- Validator file: `scripts/validate_phase37_portfolio_outputs.py`

### Implementation Files
- `strategies/phase37_portfolio_registry.py` (sleeve/method registry and locked constraint surface)
- `scripts/phase37_risk_diagnostics.py` (sleeve inputs, risk primitives, regime diagnostics, manifest)
- `scripts/phase37_portfolio_construction_runner.py` (monthly weights, engine path evaluation, guardrails, recommendation)
- `scripts/validate_phase37_portfolio_outputs.py` (fail-closed schema and decision validation)

# Phase 17.1 Formula Notes (Cross-Sectional Backtester)

Date: 2026-02-19

## 1) Forward Return
- `fwd_return_{t,h} = adj_close_{t+h} / adj_close_t - 1`
- Implementation:
  - `scripts/evaluate_cross_section.py` (`load_eval_frame`, DuckDB `LEAD(adj_close, h)` window).

## 2) Double Sort
- Sort 1 (high growth bucket, by date/industry):
  - `High_Asset_Growth = top 30% of asset_growth_yoy within (date, industry)`
- Sort 2 (inside Sort 1 bucket):
  - assign proxy deciles from ordered `z_inventory_quality_proxy` within `(date, industry)`:
    - `decile = floor((rank_position * 9) / (n-1)) + 1`, clipped to `[1, 10]`
- Spread:
  - `spread_t = mean(fwd_return_t | decile=10) - mean(fwd_return_t | decile=1)`
- Implementation:
  - `scripts/evaluate_cross_section.py` (`compute_double_sort`).

## 3) Inference Metrics
- Period mean:
  - `mean = E[spread_t]`
- Period volatility:
  - `vol = std(spread_t)`
- Sharpe:
  - `period_sharpe = mean / vol`
  - `annualized_sharpe = period_sharpe * sqrt(252 / horizon_days)`
- Newey-West lag (auto):
  - `lag = floor(4 * (T/100)^(2/9))`
- Newey-West t-stat for spread mean:
  - OLS on constant with HAC covariance.
- Implementation:
  - `scripts/evaluate_cross_section.py` (`auto_newey_west_lags`, `newey_west_mean_test`, `summarize_spread`).

## 4) Fama-MacBeth Specification
- Cross-sectional regression per date:
  - `fwd_return_{i,t+h} = alpha_t + beta1_t*asset_growth_{i,t} + beta2_t*z_proxy_{i,t} + beta3_t*(asset_growth_{i,t}*z_proxy_{i,t}) + eps_{i,t}`
- Time-series stage:
  - report mean beta and Newey-West t-stat for each beta series (`beta1_t`, `beta2_t`, `beta3_t`).
- Interaction acceptance diagnostic:
  - `beta3_mean > 0` and statistically significant (`p < 0.05`).
- Implementation:
  - `scripts/evaluate_cross_section.py` (`run_fama_macbeth`).

---

# Phase 17.2 Formula Notes (Parameter Sweep, CSCV, DSR)

Date: 2026-02-19

## 1) Correlation-Adjusted Effective Trials
- Let `N` be the number of tested variants and `rho_avg` the average off-diagonal correlation of variant return streams.
- Effective trial count:
  - `N_eff ~= N * (1 - rho_avg) + 1`
  - bounded in implementation to `[1, N]`.
- Implementation:
  - `utils/statistics.py` (`average_pairwise_correlation`, `effective_number_of_trials`).
  - Used by `scripts/parameter_sweep.py`.

## 2) CSCV Split Geometry and PBO
- Split time index into `S` contiguous even blocks (`S in {6, 8, 10}`).
- Enumerate all train/test splits:
  - `splits = C(S, S/2)` where train uses `S/2` blocks and test is the complement.
- Per split:
  - pick train-best variant by Sharpe.
  - evaluate that variant rank in test cross-section.
  - transform relative rank `r` to:
    - `lambda = log(r / (1 - r))`.
- Probability of Backtest Overfitting:
  - `PBO = mean(lambda <= 0)`.
- Implementation:
  - `utils/statistics.py` (`build_cscv_splits`, `build_cscv_block_series`, `cscv_analysis`).
  - Called in `scripts/parameter_sweep.py`.

## 3) Deflated Sharpe Ratio (Bailey & Lopez de Prado Convention)
- Estimated Sharpe of each variant stream:
  - `SR_hat = mean(R) / std(R) * sqrt(periods_per_year)`.
- Expected max Sharpe benchmark under multiple testing:
  - `SR* = E[max(SR)]` approximation from estimated Sharpe distribution and `N_eff`.
- Non-normality-adjusted probabilistic Sharpe:
  - `PSR = Phi( (SR_hat - SR*) * sqrt(n-1) / sqrt(1 - skew*SR_hat + ((kurt-1)/4)*SR_hat^2) )`
  - where `Phi` is the standard normal CDF.
- Deflated Sharpe Ratio:
  - `DSR = PSR`.
- Implementation:
  - `utils/statistics.py` (`safe_sharpe`, `expected_max_sharpe`, `probabilistic_sharpe_ratio`, `deflated_sharpe_ratio`).
  - Applied per variant in `scripts/parameter_sweep.py`.

## 4) Coarse-to-Fine Sweep Topology
- Stage 1 (coarse):
  - evaluate bounded coarse grid (local cap <= 200 combos).
- Stage 2 (fine):
  - center around coarse winner and test neighborhood steps.
- Ranking contract:
  - sort by `DSR` first, then `t_stat_nw`, then spread mean.
- Implementation:
  - `scripts/parameter_sweep.py` (`_build_coarse_grid`, `_build_fine_grid`, `_evaluate_grid`, ranking block in `main`).

---

# Phase 17.3 Prep Notes (Execution Hardening)

Date: 2026-02-19

## 1) Deterministic Variant Identity
- Variant key generation:
  - `variant_id = md5(json(sorted(params)))`
- Contract:
  - stable under key-order changes and robust to grid-order reshuffles.
  - hash payload is restricted to canonical sweep parameter keys (non-parameter metadata ignored).
- Implementation:
  - `scripts/parameter_sweep.py` (`_variant_id_from_params`).

## 2) Fine-Grid Anchor Rule
- Coarse winner selection for fine search:
  - primary: `DSR`
  - tie-break 1: `t_stat_nw`
  - tie-break 2: `period_mean`
  - tie-break 3: deterministic `variant_id` lexical order (stable sort).
- Rationale:
  - refines around the most robust candidate instead of highest raw in-sample signal.
- Implementation:
  - `scripts/parameter_sweep.py` (`_best_row(..., primary_metric='dsr')` in `main`).

## 3) Checkpoint / Resume Policy
- Checkpoint artifacts:
  - `.checkpoint_<prefix>.json`
  - `.checkpoint_<prefix>_results.csv`
  - `.checkpoint_<prefix>_streams.csv`
- Auto checkpoint cadence (`--checkpoint-every=0`):
  - `<=80 variants -> 10`
  - `<=250 variants -> 20`
  - `>250 variants -> 50`
- Resume behavior:
  - default ON, disable with `--no-resume`
  - stage skips use completed `(result + stream)` variant IDs.
- Implementation:
  - `scripts/parameter_sweep.py` (`_checkpoint_paths`, `_save_checkpoint`, `_load_checkpoint`, `_resolve_checkpoint_every`, `_evaluate_grid`).

## 4) Partition-Read Batching for Feature Upsert
- Upsert read optimization:
  - load all touched `(year, month)` partitions in one DuckDB query.
  - reuse one DuckDB connection per `_atomic_upsert_features` execution.
- Implementation:
  - `data/feature_store.py` (`_load_feature_partition_slices`, `_atomic_upsert_features`).

---

# Phase 17 Closeout Notes (Windows Lock Safety)

Date: 2026-02-19

## 1) Windows PID Liveness Contract
- Windows path avoids `os.kill(pid, 0)` and uses WinAPI:
  - `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, ...)`
  - `GetExitCodeProcess(handle, ...)`
  - liveness condition: `exit_code == STILL_ACTIVE (259)`.
- Non-Windows path keeps:
  - `os.kill(pid, 0)` probe semantics.
- Implementation:
  - `scripts/parameter_sweep.py` (`_pid_is_running`).

## 2) Corrupt Lock TTL Recovery Fallback
- Primary lock age:
  - `age_seconds = now_utc - created_at_utc` (from lock payload).
- Fallback lock age when payload is unreadable/missing:
  - `age_seconds = now_utc - file_mtime(lock_path)`.
- Recovery rule:
  - if `age_seconds >= stale_lock_seconds`, attempt stale-lock removal with bounded retries.
- Implementation:
  - `scripts/parameter_sweep.py` (`_lock_age_seconds`, `_lock_file_age_seconds`, `_acquire_sweep_lock`, `_recover_stale_lock`).

## 3) Regression Coverage
- Lock regression tests:
  - `tests/test_parameter_sweep.py::test_sweep_lock_rejects_live_pid`
  - `tests/test_parameter_sweep.py::test_sweep_lock_recovers_dead_pid`
  - `tests/test_parameter_sweep.py::test_sweep_lock_ttl_fallback_recovers_invalid_pid_lock`
  - `tests/test_parameter_sweep.py::test_sweep_lock_ttl_fallback_recovers_corrupt_lock_by_file_mtime`
  - `tests/test_parameter_sweep.py::test_sweep_lock_recovery_is_bounded_when_remove_fails`
  - `tests/test_parameter_sweep.py::test_evaluate_grid_resume_only_path_keeps_existing_state_and_triggers_checkpoint`

---

# Phase 18 Day 1 Formula Notes (Baseline Benchmarking)

Date: 2026-02-19

## 1) SPY Return and Cash Return
- SPY daily return:
  - `spy_ret_t = spy_close_t / spy_close_{t-1} - 1`
- Cash daily return hierarchy:
  - `cash_ret_t = bil_ret_t` when available
  - else `cash_ret_t = effr_rate_t / 100 / 252`
  - else `cash_ret_t = 0.02 / 252`
- Implementation:
  - `scripts/baseline_report.py` (`load_market_inputs`)
  - FR-050 helper: `backtests/verify_phase13_walkforward.py` (`build_cash_return`)

## 2) Baseline Target Weights
- Buy & Hold:
  - `w_target_t = 1.0`
- Static 50/50:
  - `w_target_t = 0.5`
- Trend SMA200:
  - `sma200_t = mean(spy_close_{t-199..t})`
  - `w_target_t = 1.0 if spy_close_t > sma200_t else w_risk_off`
  - default `w_risk_off = 0.5` (CLI override via `--trend-risk-off-weight`)
- Implementation:
  - `scripts/baseline_report.py` (`build_trend_target_weight`, `run_baselines`)

## 3) Engine-Parity Execution and Costs
- Executed weight (D-04):
  - `w_exec_t = w_target_{t-1}`
- Excess-return sleeve passed to engine:
  - `r_excess_t = spy_ret_t - cash_ret_t`
- Engine net excess return:
  - `r_net_excess_t = w_exec_t * r_excess_t - cost_t`
- Turnover/cost (D-05):
  - `turnover_t = |w_exec_t - w_exec_{t-1}|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
- Portfolio net return:
  - `r_port_t = cash_ret_t + r_net_excess_t`
- Implementation:
  - `scripts/baseline_report.py` (`simulate_single_baseline`)
  - `engine.py` (`run_simulation`)

## 4) Report Metrics
- Equity curve:
  - `equity_t = Π(1 + r_port_i), i=1..t`
- Annualized volatility:
  - `ann_vol = std(r_port) * sqrt(252)`
- Annualized turnover:
  - `turnover_annualized = mean(turnover_t) * 252`
- Total turnover:
  - `turnover_total = Σ turnover_t`
- CAGR / Sharpe / MaxDD / Ulcer:
  - FR-050 helpers reused directly from `backtests/verify_phase13_walkforward.py`
- Implementation:
  - `scripts/baseline_report.py` (`simulate_single_baseline`, `run_baselines`)

---

# Phase 18 Day 1 Addendum (SSOT Metrics + Final Artifact Contract)

Date: 2026-02-19

## 1) Metric SSOT Consolidation
- Metric functions extracted to:
  - `utils/metrics.py`
- Canonical formulas used by code:
  - `CAGR = (equity_T / equity_0)^(1/years) - 1`
  - `Sharpe = mean(excess_ret) / std(excess_ret) * sqrt(periods_per_year)`
  - `MaxDD = min((equity / cummax(equity)) - 1)`
  - `Ulcer = sqrt(mean((100 * drawdown)^2))`
  - `Turnover_t = sum(abs(weights_t - weights_{t-1}))`
- Delegation compatibility:
  - `backtests/verify_phase13_walkforward.py` keeps existing helper names but delegates to `utils/metrics.py`.

## 2) Day 1 Output Contract (Final)
- CSV output (single summary table):
  - `data/processed/phase18_day1_baselines.csv`
- CSV columns:
  - `baseline,cagr,sharpe,max_dd,ulcer,turnover_annual,turnover_total,start_date,end_date,n_days`
- Plot output:
  - `data/processed/phase18_day1_equity_curves.png`
  - log-scale y-axis
  - matplotlib primary path, Pillow fallback when matplotlib is unavailable.

## 3) Baseline Return Equation (Implemented)
- `w_exec_t = shift(w_target_t, 1)` (D-04)
- `r_excess_t = spy_ret_t - cash_ret_t`
- `cost_t = turnover_t * (cost_bps / 10000)` where `turnover_t = |w_exec_t - w_exec_{t-1}|` (D-05)
- `r_port_t = cash_ret_t + w_exec_t * r_excess_t - cost_t`
- File reference:
  - `scripts/baseline_report.py` (`simulate_single_baseline`)

---

# Phase 18 Day 2 Formula Notes (TRI Migration)

Date: 2026-02-19

## 1) Per-Asset TRI Construction
- Core factor:
  - `factor_t = 1 + total_ret_t`
- Guardrail handling:
  - if `total_ret_t` is missing -> `factor_t = 1`
  - if `total_ret_t <= -1` -> `factor_t = 0` (terminal/invalid loss cap)
- TRI path:
  - `TRI_t = base_value * cumprod(factor_t)`
- File reference:
  - `data/build_tri.py` (`build_prices_tri`)

## 2) Schema Guardrail (Split Trap Barrier)
- Legacy signal source renamed:
  - `adj_close -> legacy_adj_close`
- Day 2 contract:
  - signal/indicator layer uses `tri`
  - execution layer keeps `total_ret`
- File references:
  - `data/build_tri.py` (artifact schema projection)
  - `data/feature_store.py` (TRI-first source selection + compatibility output)

## 3) Split Continuity Validation
- For known split dates:
  - `tri_pct_t = TRI_t / TRI_{t-1} - 1`
  - `expected_pct_t = total_ret_t`
  - pass when `abs(tri_pct_t - expected_pct_t) <= tolerance`
- This checks continuity against causal return input (avoids false failure from genuine split-day market moves).
- File reference:
  - `data/build_tri.py` (`build_validation_report`)

## 4) Dividend Capture Sanity Check
- Trailing 1-year delta:
  - `delta_dividend_effect = tri_return_1y - legacy_adj_close_return_1y`
- Expected sign:
  - `delta_dividend_effect >= 0` for high-yield validation tickers.
- File reference:
  - `data/build_tri.py` (`build_validation_report`)

## 5) Macro TRI Extension
- Added TRI columns:
  - `spy_tri`, `vix_tri`, `mtum_tri`, `dxy_tri`
- Recomputed derived fields:
  - `vix_proxy = rolling_std(pct_change(spy_tri), 20) * sqrt(252) * 100`
  - `mtum_spy_corr_60d = rolling_corr(pct_change(mtum_tri), pct_change(spy_tri), 60)`
  - `dxy_spx_corr_20d = rolling_corr(pct_change(dxy_tri), pct_change(spy_tri), 20)`
- File reference:
  - `data/build_macro_tri.py`

## 6) Runtime Integration Notes
- `app.py` prefers `prices_tri.parquet` and `macro_features_tri.parquet` when present.
- `strategies/investor_cockpit.py` carries `tri` in feature history and uses it when available for price-side checks.
- `data/feature_store.py` persists both `adj_close` (compatibility) and `tri` (signal-safe column).

---

# Phase 18 Day 3 Formula Notes (Cash Overlay)

Date: 2026-02-20

## 1) Scenario Set (6 total)
- `Buy & Hold`: `w_target_t = 1.0`
- `Trend SMA200`: `w_target_t = 1.0 if TRI_t > SMA200_t else 0.5`
- `Vol Target 15% (20/60/120d)`: three lookback variants
- `Trend Multi-Horizon`: weighted MA score (`50/100/200`, weights `0.5/0.3/0.2`)
- File reference:
  - `scripts/cash_overlay_report.py` (`run_scenarios`)

## 2) Volatility-Target Overlay Formula
- Realized volatility (lag-safe):
  - `sigma_t = std(spy_ret_{t-lookback..t-1}) * sqrt(252)`
- Target exposure:
  - `w_target_t = clip(0.15 / sigma_t, 0, 1)`
- Warm-up handling:
  - before valid window, fill `w_target_t = 1.0`
- File reference:
  - `strategies/cash_overlay.py` (`VolatilityTargetOverlay.compute_exposure`)

## 3) Trend Multi-Horizon Overlay Formula
- Lagged price:
  - `p_lag_t = TRI_{t-1}`
- For each MA window `i`:
  - `MA_i,t = mean(p_lag_{t-i+1..t})`
  - `signal_i,t = +1 if p_lag_t > MA_i,t else -1`
- Weighted score:
  - `score_t = sum_i(weight_i * signal_i,t)`
- Exposure mapping:
  - `w_target_t = clip(0.5 + 0.5 * score_t, 0, 1)`
- File reference:
  - `strategies/cash_overlay.py` (`TrendFollowingOverlay.compute_exposure`)

## 4) Portfolio Return, Lag, and Cost Path
- Executed exposure (D-04):
  - `w_exec_t = shift(w_target_t, 1)`
- Excess-return sleeve sent to engine:
  - `r_excess_t = spy_ret_t - cash_ret_t`
- Engine net excess:
  - `r_net_excess_t = w_exec_t * r_excess_t - cost_t`
- Turnover/cost (D-05):
  - `turnover_t = |w_exec_t - w_exec_{t-1}|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
- Portfolio net return (FR-050 cash hierarchy applied):
  - `r_port_t = cash_ret_t + r_net_excess_t`
- File references:
  - `scripts/cash_overlay_report.py` (`simulate_overlay_strategy`)
  - `engine.py` (`run_simulation`)

## 5) Stress and Correlation Diagnostics
- Stress-window exposure summary:
  - `exposure_min`, `exposure_mean`, `exposure_max` per scenario/window
  - windows: `covid_crash`, `inflation_shock`, `low_vol_meltup`, `rate_hikes_q4`
- Exposure orthogonality:
  - Pearson correlation matrix on executed exposure series.
- File references:
  - `scripts/cash_overlay_report.py` (`build_stress_checks`, `build_exposure_corr`)

## 6) Day 3 Regression Fix Note
- `_load_inputs` now passes datetime-indexed macro context into FR-050 `_build_context`.
- Prevents mixed-index sort error (`Timestamp` vs `int`) when liquidity context is present.
- File references:
  - `scripts/cash_overlay_report.py` (`_load_inputs`)
  - `tests/test_cash_overlay.py` (`test_load_inputs_uses_datetime_index_for_fr050_context`)

---

# Phase 18 Day 4 Formula Notes (Company Scorecard)

Date: 2026-02-20

## 1) Linear Factor Score
- Core equation:
  - `Score_i,t = Σ_k (w_k * sign_k * N_k(i,t))`
- where:
  - `w_k`: factor weight
  - `sign_k`: `+1` for positive factors, `-1` for negative factors
  - `N_k(i,t)`: normalized factor value for stock `i` on date `t`
- File references:
  - `strategies/company_scorecard.py` (`compute_scores`)
  - `strategies/factor_specs.py` (`build_default_factor_specs`)

## 2) Cross-Sectional Normalization
- Z-score normalization (default):
  - `N_k(i,t) = (x_k(i,t) - μ_k,t) / σ_k,t`
- Rank normalization:
  - `N_k(i,t) = rank_pct(x_k(i,t))`
- Raw normalization:
  - `N_k(i,t) = x_k(i,t)`
- File reference:
  - `strategies/company_scorecard.py` (`_normalize`)

## 3) Day 4 Default Factor Set (Equal Weights)
- Momentum (`+`): `resid_mom_60d`
- Quality (`+`): `quality_composite` (fallback `capital_cycle_score`)
- Volatility (`-`): `realized_vol_21d` (fallback `yz_vol_20d`)
- Illiquidity (`-`): `illiq_21d` (fallback `amihud_20d`)
- Weight vector:
  - `[0.25, 0.25, 0.25, 0.25]`
- File references:
  - `strategies/factor_specs.py`
  - `data/feature_store.py` (Day 4 alias columns)

## 4) Control-Theory Upgrade Toggles (Default OFF)
- Sigmoid blender:
  - `sigmoid(x) = 2 / (1 + exp(-k*x)) - 1`
- Dirty derivative:
  - `x'_t = x_t - x_{t-1}`
- Leaky integrator:
  - `x~_t = EWMA_alpha(x_t)`
- Day 4 baseline policy:
  - all toggles `False`; wiring only, no ablation activation
- File references:
  - `strategies/factor_specs.py` (`FactorSpec` toggles)
  - `strategies/company_scorecard.py` (`_apply_control_toggles`)

## 5) Validation Metrics
- Score coverage:
  - `coverage = non_null(score) / total_rows`
- Factor dominance:
  - per-row share `= |contrib_k| / Σ_j |contrib_j|`
  - evaluate max mean share across factors
- Stability:
  - Spearman rank correlation between adjacent dates
- Quartile separation:
  - `spread_sigma = (mean(Q1) - mean(Q4)) / std(score)`
- File reference:
  - `scripts/scorecard_validation.py` (`build_validation_table`)

---

# Phase 18 Day 5 Formula Notes (Ablation Matrix)

Date: 2026-02-20

## 1) Score Validity Modes
- Complete-case:
  - `valid_i,t = AND_k isfinite(N_k(i,t))`
  - `Score_i,t = Σ_k (w_k * sign_k * N_k(i,t))` only when `valid_i,t = True`
- Partial:
  - `valid_i,t = OR_k isfinite(N_k(i,t))`
  - `Score_i,t = [Σ_k (w_k * sign_k * N_k(i,t))] / [Σ_k (w_k * 1_{k available})]`
- Impute-neutral:
  - `valid_i,t = OR_k isfinite(N_k(i,t))`
  - missing factor contribution treated as `0`:
    - `Score_i,t = Σ_k (w_k * sign_k * N_k(i,t, missing->0))`
- File reference:
  - `strategies/company_scorecard.py` (`compute_scores`)

## 2) Top-Quantile Portfolio Construction
- Per-date descending rank:
  - `rank_desc(i,t) = rank(score_i,t, descending, method=first)`
- Selected names:
  - `n_select_t = ceil(top_quantile * n_valid_t)`
  - `selected_i,t = 1 if rank_desc(i,t) <= n_select_t else 0`
- Target weight:
  - `w_target(i,t) = selected_i,t / n_select_t`
- File reference:
  - `scripts/day5_ablation_report.py` (`_build_target_weights`)

## 3) Backtest Path (D-04/D-05)
- Engine input:
  - target matrix `W_target(t,i)` from Day 5 scores
  - return matrix `R(t,i)` from `prices_tri.total_ret`
- Execution lag:
  - `W_exec(t,i) = W_target(t-1,i)` (inside `engine.run_simulation`)
- Turnover/cost:
  - `turnover_t = Σ_i |W_exec(t,i) - W_exec(t-1,i)|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
- Net return:
  - `r_net_t = Σ_i (W_exec(t,i) * R(t,i)) - cost_t`
- Equity:
  - `equity_t = Π(1 + r_net_j), j=1..t`
- File references:
  - `scripts/day5_ablation_report.py` (`_simulate_scores_strategy`)
  - `engine.py` (`run_simulation`)

## 4) Day 5 Delta Metrics
- Baseline anchor: `BASELINE_DAY4`
- For each metric `m`:
  - `delta_m(config) = m(config) - m(baseline)`
- Turnover reduction:
  - `turnover_reduction = 1 - turnover_annual(config) / turnover_annual(baseline)`
- Optimal selection gates:
  - `coverage >= target_coverage`
  - `quartile_spread_sigma >= target_spread`
  - `turnover_reduction >= target_turnover_reduction`
  - `sharpe >= sharpe_baseline`
- File references:
  - `scripts/day5_ablation_report.py` (`_build_deltas`, `_select_optimal`)

## 5) Runtime Guardrails Added
- Dense matrix cap:
  - fail if `n_dates * max(1, n_permnos) > max_matrix_cells`
- Missing active returns:
  - default fail-fast on active-position missing cells
  - optional override: `--allow-missing-returns` => warn + zero-impute
- Empty input window:
  - writes empty artifacts with `status=no_data` and exits non-zero.
- File reference:
  - `scripts/day5_ablation_report.py` (`main`, `_simulate_scores_strategy`)

---

# Phase 18 Day 6 Formula Notes (Walk-Forward Validation)

Date: 2026-02-20

## 1) Leaky Integrator Parameterization
- Day 6 C3 setting:
  - `decay = 0.95`
  - `alpha = 1 - decay = 0.05`
- Integrator recurrence (per factor series per permno):
  - `I_t = (1 - alpha) * I_{t-1} + alpha * x_t`
  - implemented as EWMA with `alpha=0.05`, `adjust=False`.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`_build_c3_specs`)
  - `strategies/company_scorecard.py` (`_apply_control_toggles`)

## 2) Walk-Forward Window Mechanics
- Train/test windows (`W1..W4`) are evaluated as:
  - train metrics on `[train_start, train_end]`
  - test metrics on `[test_start, test_end]`
- Temporal isolation:
  - scores are generated on chronologically ordered history only,
  - no future rows are used in score computation,
  - execution remains `shift(1)` through engine path.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`run_walk_forward_validation`)

## 3) Portfolio Simulation Path
- Selection:
  - `n_select_t = ceil(top_quantile * n_valid_t)`
  - top-ranked names get equal target weights.
- Execution/cost:
  - `w_exec_t = w_target_{t-1}`
  - `turnover_t = sum_i |w_exec_t(i) - w_exec_{t-1}(i)|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
  - `net_ret_t = sum_i(w_exec_t(i) * ret_t(i)) - cost_t`
- File references:
  - `scripts/day6_walkforward_validation.py` (`_simulate_from_scores`)
  - `engine.py` (`run_simulation`)

## 4) Day 6 Check Computations
- Drawdown duration:
  - longest consecutive run where `equity_t < rolling_peak_t`.
- Recovery speed:
  - index distance from `recovery_start` to first date where equity regains pre-start peak.
- Beta:
  - `beta = cov(port_ret, spy_ret) / var(spy_ret)`.
- Rank stability:
  - mean adjacent-date Spearman rank correlation on cross-sectional scores.
- File references:
  - `scripts/day6_walkforward_validation.py` (`_compute_drawdown_duration`, `_days_to_new_high`, `_compute_beta`, `_adjacent_rank_corr`)

## 5) Decay Plateau Diagnostics (CHK-51..53)
- Gradient smoothness:
  - `max(abs(gradient(sharpe(decay_grid)))) < 0.05`.
- Peak-width:
  - at least 3 decay points within `0.03` Sharpe of the best decay.
- Symmetry:
  - `abs((S_0.95 - S_0.90) - (S_0.95 - S_0.98)) < 0.05`.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`analyze_decay_sensitivity`, `evaluate_checks`)

## 6) Crisis Turnover Gate (CHK-54)
- For each crisis window:
  - `reduction_pct = 100 * (turnover_base - turnover_c3) / turnover_base`
  - pass condition: `reduction_pct >= 15` and `turnover_c3 < turnover_base`
- Global CHK-54 pass:
  - all crisis windows pass simultaneously.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`validate_crisis_turnover`)

---

# Phase 21 Day 1 Formula Notes (Stop-Loss & Drawdown Control)

Date: 2026-02-20

## 1) ATR Proxy (Close-Only, SMA)
- Mode:
  - `atr_mode = proxy_close_only`
- Daily range proxy:
  - `range_t = |close_t - close_{t-1}|`
- ATR:
  - `ATR_t = SMA(range_t, window=20)`
- File reference:
  - `strategies/stop_loss.py` (`ATRCalculator.compute_atr`)

## 2) Initial and Trailing Stop Formulas
- Initial stop at entry:
  - `stop_initial = entry_price - (K_initial * ATR_entry)`
  - `K_initial = 2.0`
- Trailing candidate:
  - `stop_trailing_candidate_t = price_t - (K_trailing * ATR_t)`
  - `K_trailing = 1.5`
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager.enter_position`, `StopLossManager.update_stop`)

## 3) D-57 Ratchet Invariant
- Non-decreasing stop:
  - `stop_t = max(stop_{t-1}, stop_candidate_t)`
- Invariant:
  - `stop_t >= stop_{t-1}` for every update step.
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager.update_stop`)

## 4) Time-Based Underwater Exit
- Underwater condition:
  - `price_t <= entry_price`
- Exit rule:
  - force exit when `days_held > max_underwater_days` while underwater.
- Day 1 default:
  - `max_underwater_days = 60`
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager.update_stop`)

## 5) Drawdown Circuit Breakers
- Drawdown:
  - `dd_t = (equity_t - peak_equity_t) / peak_equity_t`
- Tiers:
  - if `dd_t <= -0.15` => scale `0.00`
  - else if `dd_t <= -0.12` => scale `0.50`
  - else if `dd_t <= -0.08` => scale `0.75`
  - else scale `1.00`
- Recovery:
  - if currently in tier mode and `dd_t > -0.04`, reset to scale `1.00`.
- File reference:
  - `strategies/stop_loss.py` (`PortfolioDrawdownMonitor.update_equity`)

## 6) Zero-Volatility Safety Switch
- Optional microscopic floor:
  - `stop <= reference_price - min_stop_distance_abs`
- Default Day 1 setting:
  - `min_stop_distance_abs = 0.0` (disabled by default)
- Intended use:
  - avoid zero-distance stop placement when ATR is exactly zero.
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager._enforce_min_stop_distance`)

---

# Phase 21.1 Formula Notes (Anchor-Injected Cyclical Centroid)

Date: 2026-02-21

## 1) Anchor-Injected Cyclical Centroid in z-Space
- Anchor set:
  - `A = {MU, LRCX, AMAT, KLAC, STX, WDC}`
- Daily available anchors:
  - `A_t = {i in slice_t | ticker_i in A}`
- Centroid (primary path):
  - `mu_cyc_t = mean_{i in A_t}(z_i_t)`
- File reference:
  - `strategies/ticker_pool.py` (`_compute_cyc_centroid_anchor_injected`)

## 2) No-Anchor Fallback Centroid (Legacy Top-k)
- Trigger:
  - `|A_t| = 0`
- Fallback index set:
  - `K_t = TopK(score_col_prepool, k=centroid_top_k)`
- Fallback centroid:
  - `mu_cyc_t = mean_{i in K_t}(z_i_t)`
- Empty fallback safety:
  - if `K_t` is empty after NaN filtering, return zero vector.
- File reference:
  - `strategies/ticker_pool.py` (`_compute_cyc_centroid_anchor_injected`)

## 3) Pre-Pool Score Guard (Chicken-and-Egg Prevention)
- Rule:
  - `score_col` must not be pool-derived (`mahalanobis_*`, `posterior_*`, `odds_*`, `pool_*`, `compounder_prob`).
- Behavior:
  - raise `ValueError` if forbidden score column is passed.
- File reference:
  - `strategies/ticker_pool.py` (`_assert_pre_pool_score_col`)

## 4) Anchor-Priority Long Ranking Boost
- Base eligibility:
  - `valid_i = (MahDist_k_cyc_i <= 5.0) and (odds_ratio_i > 0.5)`
- Anchor bonus level:
  - `B_t = max_{j notin A}(odds_ratio_j) + 1`, fallback `B_t = 10` when non-anchor set is empty.
- Final score:
  - `odds_score_i = odds_ratio_i + B_t * 1_{i in A}` if `valid_i`, else `-9999`.
- File reference:
  - `strategies/ticker_pool.py` (inside `rank_ticker_pool`)

## 5) Path1 Runtime Gates and Deterministic Resample Rule
- Sector-balanced resample depth is computed on known sector labels only:
  - `counts_known = counts(sector != 'UNKNOWN')`
  - `per_sector = min(counts_known)`
  - if `per_sector < 2`, fallback mode is used.
- Non-finite sector projection residualization is hard-fail for that date slice:
  - `if residual_mode == 'projection_nonfinite_fallback': skip date slice + CRITICAL log`
- Slice runner exposes explicit mode toggle:
  - `--dictatorship-mode on|off`
  - `on -> DICTATORSHIP_MODE='PATH1_STRICT'`
  - `off -> DICTATORSHIP_MODE='PATH1_DEPRECATED'`
- File reference:
  - `strategies/ticker_pool.py` (`_deterministic_sector_balanced_resample`, `rank_ticker_pool`)
  - `scripts/phase21_1_ticker_pool_slice.py` (`parse_args`, `main`)

---

# Phase 21.1 Path1 Formula Notes (Sector Context + Dictatorship Telemetry)

Date: 2026-02-21

## 1) Deterministic Sector/Industry Attach (Before Pool Ranking)
- Source:
  - `data/static/sector_map.parquet`
- Priority order:
  - `context_permno = latest(sector, industry by permno)`
  - `context_ticker = latest(sector, industry by ticker)`
  - `context = coalesce(context_permno, context_ticker, 'Unknown')`
- Deterministic selection:
  - sort rows by `updated_at DESC`, then stable tie-breakers, then keep first key row.
- File reference:
  - `strategies/company_scorecard.py` (`_load_sector_context_maps`, `_attach_sector_industry_context`)

## 2) Path1 Context Attachment Flag
- Source label:
  - `sector_context_source_i = 'permno' if permno-map hit else 'ticker' if ticker-map hit else 'unknown'`
- Attachment flag:
  - `path1_sector_context_attached_i = 1{sector_context_source_i != 'unknown'}`
- File reference:
  - `strategies/company_scorecard.py` (`_attach_sector_industry_context`)

## 3) Path1 Directive and DICTATORSHIP_MODE Output Fields
- Constant fields:
  - `DICTATORSHIP_MODE = 'PATH1_STRICT'`
  - `path1_directive_id = 'PATH1_SECTOR_CONTEXT_PRE_RANK'`
- Emitted to:
  - sample CSV rows and summary JSON telemetry.
- File reference:
  - `scripts/phase21_1_ticker_pool_slice.py` (`main`)

## 4) Path1 Summary Telemetry Formulas
- Block-level attachment coverage:
  - `context_attached_ratio_in_block = context_attached_rows_in_block / max(1, block_rows)`
- Sector/industry known counts:
  - `known_sector_rows_in_block = sum(1{sector not in ['', 'Unknown', NaN]})`
  - `known_industry_rows_in_block = sum(1{industry not in ['', 'Unknown', NaN]})`
- Source mix:
  - `context_source_counts_in_block = frequency(sector_context_source)`
- Sample composition:
  - `sample_sector_counts = frequency(sample.sector)`
  - `sample_industry_counts = frequency(sample.industry)`
- File reference:
  - `scripts/phase21_1_ticker_pool_slice.py` (`main`, `_known_context_mask`)

---

# Phase 22 Formula Notes (Separability Harness)

Date: 2026-02-21

## 1) Cluster Stability (Jaccard Overlap)
- Ranking basis:
  - `odds_score` descending.
- Sets:
  - `S_decile_t = top ceil(0.10 * N_t) tickers by odds_score`
  - `S_30_t = top min(30, N_t) tickers by odds_score`
- Daily stability:
  - `J(S_t, S_{t-1}) = |S_t ∩ S_{t-1}| / |S_t ∪ S_{t-1}|`
- Emitted metrics:
  - `jaccard_top_decile`
  - `jaccard_top_30`
- File reference:
  - `scripts/phase22_separability_harness.py` (`_jaccard_index`, `_build_daily_metrics`)

## 2) Manifold Separation (Silhouette in Path1 Geometry)
- Feature space:
  - post-MAD robust z-scored features
  - then sector-projection residualized geometry (`z_geom_resid`).
- Labels:
  - `label_i = argmax(posterior_cyclical_i, posterior_defensive_i, posterior_junk_i)`.
- Score:
  - silhouette score on `(z_geom_resid, label)` rows.
- One-class policy:
  - if only one effective class on a day, emit `silhouette_score = NaN` with class coverage counters.
- Runtime fallback:
  - when `sklearn.metrics` is unavailable, use deterministic manual Euclidean silhouette implementation.
- File reference:
  - `scripts/phase22_separability_harness.py` (`_build_geometry_residuals`, `_compute_silhouette_metrics`, `_manual_silhouette_score`)

## 3) Invariant Truth Checks (Archetype Recall)
- Archetype set:
  - `{MU, LRCX, AMAT, KLAC}`
- Daily rank:
  - `rank_i_t = 1-based rank of ticker i by odds_score on day t`
- Daily hits:
  - `hit_decile_i_t = 1{rank_i_t <= top_decile_n_t}`
  - `hit_top30_i_t = 1{rank_i_t <= top_30_n_t}`
- Aggregate rates:
  - mean of daily hit indicators across the evaluation window.
- File reference:
  - `scripts/phase22_separability_harness.py` (`_archetype_rank_metrics`, `_build_summary`)

---

# Phase 23 Formula Notes (FMP PIT Estimates Ingestion - Step 1)

Date: 2026-02-22

## 1) Internal Schema Contract
- Cleaned output schema:
  - `permno, ticker, published_at, horizon, metric, value`
- Metric names ingested from FMP:
  - `estimatedRevenueAvg`
  - `estimatedEpsAvg`
- Horizon:
  - normalized to `NTM`.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_build_processed_estimates`)

## 2) PIT Publication-Time Rule
- Publication timestamp:
  - `published_at = coalesce(date, publishedDate, published_at, acceptedDate, updatedAt, fetched_at_utc)`
- PIT firewall for NTM aggregation:
  - include forecast periods only when `period_end > published_at`.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_derive_period_fields`, `_normalize_ntm_for_metric`)

## 3) NTM Normalization Rule (Quarterly/Annual)
- For each `(permno, ticker, published_at, metric)` group:
  - if at least 4 future quarterly rows exist:
    - `NTM = sum(first 4 future quarters by period_end ascending)`
  - else if 2-3 future quarterly rows exist:
    - `NTM = sum(quarters) * (4 / n_quarters)` (annualized partial forward set)
  - else if annual (`FY`) row exists:
    - `NTM = FY value`
  - else if exactly 1 future quarter exists:
    - `NTM = quarter_value * 4`
  - else:
    - fallback to first finite metric value.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_normalize_ntm_for_metric`)

## 4) Identifier Integrity Rule
- Mapping source:
  - `data/static/sector_map.parquet`
- Join key:
  - uppercased cleaned ticker (`ticker_u`)
- Integrity behavior:
  - drop unmapped ticker rows from processed output.
  - log unmapped ticker sample for audit.
  - if processed output is empty after mapping/normalization, abort write (preserve existing outputs).
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_load_ticker_permno_crosswalk`, `_build_processed_estimates`, `main`)

## 5) Rate-Aware Cache-First Ingestion Rules
- Per-ticker cache path:
  - `cache_path(ticker) = data/raw/fmp_cache/{ticker}.json`
- Cache priority:
  - if cache exists and `--refresh-cache` is not set:
    - use cache rowset, skip network request.
- 429 handling:
  - exponential backoff:
    - `wait_k = min(backoff_initial_sec * 2^k, 300)` for retry `k`.
  - after retry budget is exhausted:
    - set rate-limited mode,
    - stop new network requests,
    - continue cache-only for remaining scoped tickers,
    - exit cleanly (`code 0`) if no fresh rows can be fetched.
- Scoped universe:
  - target list resolved from `--tickers` and/or `--tickers-file`,
  - capped by `--max-tickers` (default `500`),
  - pre-filtered to tickers with known `permno` in crosswalk before API calls.
- Merge policy:
  - if `--merge-existing` and prior `data/processed/estimates.parquet` exists:
    - `final = dedup(existing ∪ new)` on key
      - `(permno, ticker, published_at, horizon, metric)`
    - source rank enforces **new rows win** on key collisions.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_resolve_target_tickers`, `_load_cached_rows`, `_fetch_with_backoff`, `_merge_existing_processed`, `main`)

---

# Phase 23 Formula Notes (3-Pillar SDM Ingest + Assembler Round 3)

Date: 2026-02-22

## 1) merge_asof Sorting Contract (Pillar 1 + 2)
- Required global order before `merge_asof(..., by='gvkey')`:
  - `left sort = sort_values(['published_at_dt', 'gvkey'])`
  - `right sort = sort_values(['pit_date', 'gvkey'])`
- Hard assertions:
  - `published_at_dt` monotonic increasing globally.
  - `pit_date` monotonic increasing globally.
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_assert_merge_asof_sorted`, `_join_totalq`)

## 2) Peters & Taylor PIT Join + Dynamic Schema
- Filing lag:
  - `pit_date = datadate + 90 days`
- Dynamic probe:
  - `available_cols = information_schema.columns(totalq.total_q)`
  - `selected_cols = required + stable + optional_intersection`
- Required:
  - `gvkey`, `datadate`
- Stable:
  - `k_int`, `k_int_know`, `k_int_org`, `q_tot`
- Optional enrichment:
  - `k_phy`, `invest_int`, `invest_phy`, `ik_tot`
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_probe_totalq_columns`, `_select_totalq_columns`, `_query_totalq`)

## 3) Pillar 2 Derived Features
- Intangible intensity:
  - `intang_intensity = k_int / (k_int + ppentq)` when denominator `> 0`
- Investment discipline:
  - preferred: `invest_disc = ik_tot - lag4(ik_tot)` when `ik_tot` exists
  - fallback: `invest_disc = (k_int - lag4(k_int)) / lag4(k_int)` when `lag4(k_int) > 0`
- Regime flag:
  - `q_regime = 1(q_tot > 1.0)` (NaN-preserving when `q_tot` unavailable)
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_join_totalq`)

## 4) Allow + Audit Identifier Policy
- Mapping:
  - `permno = map(ticker -> permno from sector_map.parquet)`
- Policy:
  - never drop unmapped rows.
  - emit audit CSV for unmapped rows:
    - `data/processed/fundamentals_sdm_unmapped_permno_audit.csv`
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_crosswalk_permno`, `_atomic_write_csv`)

## 5) Assembler PIT Join Rules
- Inputs:
  - `fundamentals_sdm.parquet`
  - `macro_rates.parquet`
  - `ff_factors.parquet`
- Key normalization:
  - `published_at_dt = to_datetime(published_at, utc=True).tz_convert(None)`
  - `macro_at = to_datetime(date, utc=True).tz_convert(None)`
  - `ff_at = to_datetime(date, utc=True).tz_convert(None)`
- Asof joins:
  - `fundamentals ⟵ macro` by backward join on `published_at_dt` to `macro_at`
  - `fundamentals ⟵ ff` by backward join on `published_at_dt` to `ff_at`
  - strict staleness cap: `tolerance = Timedelta('14d')`
- Tolerance-null audit:
  - `baseline_match = merge_asof(..., tolerance=None)`
  - `strict_match = merge_asof(..., tolerance='14d')`
  - `nulled_by_tolerance = count(baseline_match exists AND strict_match is null)`
  - emit warning counts for macro and factor joins.
- Sector attach:
  - `permno` map first, then ticker fallback.
- File reference:
  - `scripts/assemble_sdm_features.py` (`assemble_features`, `_count_rows_nulled_by_tolerance`, `_attach_sector_context`)

---

# Phase 23 Formula Notes (Action 2: BGM Manifold Swap)

Date: 2026-02-22

## 1) Daily SDM Broadcast (Method A)
- Entity-wise daily forward fill from quarterly release timeline:
  - `date = normalize(published_at)`
  - For each `gvkey`: reindex to daily calendar and `ffill` latest released snapshot.
- Calendar:
  - `calendar = date_range(min(fundamentals, macro, ff), max(fundamentals, macro, ff), 'D')`
- File reference:
  - `scripts/assemble_sdm_features.py` (`_build_daily_calendar`, `_expand_fundamentals_daily`, `assemble_features`)

## 2) Industry Median Precompute (Method B)
- Daily industry medians:
  - `ind_rev_accel = median(rev_accel | date, industry)`
  - `ind_inv_vel_traj = median(inv_vel_traj | date, industry)`
  - `ind_gm_traj = median(gm_traj | date, industry)`
  - `ind_op_lev = median(op_lev | date, industry)`
  - `ind_intang_intensity = median(intang_intensity | date, industry)`
  - `ind_q_tot = median(q_tot | date, industry)`
- File reference:
  - `scripts/assemble_sdm_features.py` (`_add_industry_medians`)

## 3) Macro-Cycle Interaction (Method B)
- Cycle setup interaction:
  - `CycleSetup = yield_slope_10y2y * rmw * cma`
  - alias: `cycle_setup = CycleSetup`
- File reference:
  - `scripts/assemble_sdm_features.py` (`_add_cycle_setup`)

## 4) Dual-Read Migration Adapter
- Data loader merge contract:
  - `features_window = left_join(features.parquet, features_sdm.parquet, on=[date, permno])`
  - Date normalization before merge:
    - `date = to_datetime(date, utc=True).tz_convert(None)`
  - Overlap policy:
    - for duplicate column name `x`, use `combine_first(x_left, x_sdm)`.
- File reference:
  - `scripts/phase20_full_backtest.py` (`_read_feature_window`, `_load_features_window`)

## 5) BGM Geometry Isolation Contract (Superseded by Phase 20 Lock on 2026-02-22)
- Current locked Phase 20 geometry set must include only:
  - `rev_accel, inv_vel_traj, op_lev, q_tot, CycleSetup`
- Historical note:
  - prior Phase 23 experimentation used a broader 10-feature geometry set;
    this is retained as historical context only and is not the current lock state.
- Explicit risk exclusion asserts:
  - reject exact risk columns:
    - `realized_vol_lag, yz_vol_20d, atr_14d, sigma_continuous, asset_beta_lag, portfolio_beta, rolling_beta_63d`
  - reject any geometry column containing token:
    - `beta` or `vol`
- File reference:
  - `strategies/ticker_pool.py` (`TickerPoolConfig`, `_assert_geometry_excludes_risk`, `rank_ticker_pool`)

## 6) Risk Routing Separation
- Risk features kept for sizing/governor only:
  - volatility path: `sigma_continuous`, `realized_vol_lag`, `atr_14d`, `yz_vol_20d`
  - beta path: `asset_beta_lag`, `portfolio_beta`, `beta_scale_pre`, `beta_scale_post`
- Geometry path uses lagged SDM/macro fields only.
- File reference:
  - `strategies/company_scorecard.py` (`build_phase20_conviction_frame`)

## 7) Hierarchical Imputation for SDM Geometry (Universe Preservation)
- Scope:
  - Applied in ticker-pool geometry build before robust MAD scaling.
- Level 1 (Industry Fill, PIT cross-section):
  - For each date and feature:
    - `x_i = median(feature | date, industry)` when firm value is NaN
  - Fallback grouping key:
    - `industry` else `sector` else `UNKNOWN`.
- Level 2 (Neutral Fill):
  - Remaining NaN -> `0.0` in robust-scaled geometry space.
  - Interpretation:
    - `0.0` is neutral market-average exposure on that feature.
- Telemetry:
  - `geometry_universe_before_imputation`
  - `geometry_universe_after_imputation`
  - `geometry_industry_impute_cells`
  - `geometry_zero_impute_cells`
- File reference:
  - `strategies/ticker_pool.py` (`_hierarchical_impute_geometry`, `_build_weighted_zmat_with_imputation`, `rank_ticker_pool`)
  - `scripts/phase22_separability_harness.py` (`_build_geometry_residuals`, `_build_daily_metrics`, `_build_summary`)

---

# Phase 20 Closure Formula Notes (Golden Master Lock)

Date: 2026-02-22

## 1) Cluster Ranker (Option A, Cyclical Trough)
- Formula:
  - `cluster_score = (CycleSetup * 2.0) + op_lev + rev_accel + inv_vel_traj - q_tot`
- Interpretation:
  - reward cycle inflection + operating leverage + revenue acceleration + inventory clearing,
  - penalize high `q_tot` to avoid buying supply-heavy/capital-loose profiles.
- Source path:
  - `strategies/ticker_pool.py` (`_conviction_cluster_score`)

## 2) Hard Entry Gate (Trend-Confirmed)
- Formula:
  - `entry_gate = score_valid & (conviction_score >= 7.0) & pool_long_candidate & mom_ok & support_proximity`
- Interpretation:
  - no entry without both momentum confirmation and support confirmation.
- Source path:
  - `strategies/company_scorecard.py` (`build_phase20_conviction_frame`)

## 3) Hard Exit / Selection Rule
- Formula:
  - `selected = entry_gate & (rank <= n_target)`
- Interpretation:
  - positions must still pass hard gate and rank threshold each day (no winner-retention hysteresis in locked state).
- Source path:
  - `scripts/phase20_full_backtest.py` (`_build_phase20_plan`)

## 4) Concentrated Portfolio and Structural Cash
- Defaults:
  - `top_n_green = 8`
  - `top_n_amber = 4`
  - `cash_pct_GREEN = 0.20`
  - `gross_cap_GREEN = 0.80`
- Source path:
  - `scripts/phase20_full_backtest.py` (`parse_args`, `_build_phase20_plan`)

## 5) Fundamental Continuity Repair (PIT-safe Missing Data)
- Rule:
  - grouped ticker-level `ffill(limit=120)` for `q_tot`, `inv_vel_traj`, `op_lev`, `rev_accel`, `CycleSetup`.
  - remaining NaNs filled by same-date sector median, then same-date market median, then `0.0`.
- Source path:
  - `strategies/company_scorecard.py` (`build_phase20_conviction_frame`)

## 6) MU Reverse-Engineer Diagnostic (Boundary Evidence)
- October 2022 means from `data/processed/diagnostic_MU_reverse_engineer.csv`:
  - `q_tot = 3.2634692142857142`
  - `inv_vel_traj = 0.0`
  - `conviction_score = 3.510820467875683`
- Interpretation:
  - backward-looking fundamentals can lag market forward-pricing at cycle bottoms.

---

# Context Bootstrap Formula/Contract Notes

Date: 2026-02-23

## 1) Context Artifact Schema Contract (`current_context.json`)
- Required top-level fields:
  - `schema_version`
  - `generated_at_utc`
  - `source_files`
  - `active_phase`
  - `what_was_done`
  - `what_is_locked`
  - `what_is_next`
  - `first_command`
  - `next_todos`
- Field constraints:
  - `generated_at_utc`: ISO-8601 UTC timestamp.
  - `what_was_done`, `what_is_locked`, `what_is_next`, `next_todos`: non-empty string arrays.
  - `first_command`: non-empty string.
  - key order is fixed to `PACKET_KEYS` in `scripts/build_context_packet.py`.

## 2) Markdown Packet Section Contract (`current_context.md`)
- Required section order:
  - `## What Was Done`
  - `## What Is Locked`
  - `## What Is Next`
  - `## First Command`

## 3) Refresh/Validation Command Contract
- Build command:
  - `.venv\Scripts\python scripts/build_context_packet.py`
- Validation command:
  - `.venv\Scripts\python scripts/build_context_packet.py --validate`
- Phase-end freshness check formula:
  - `artifact_age_hours = (now_utc - generated_at_utc) / 3600`
  - pass condition: `artifact_age_hours <= 24`

## 4) Source Selection + Active Phase Rule
- Candidate order:
  - inspect phase handovers and phase briefs by descending phase number.
  - select first document that satisfies required sections.
- `active_phase` rule:
  - use phase number parsed from selected source document.
  - fallback to max phase brief number only if selected source has no parseable phase token.
- File reference:
  - `scripts/build_context_packet.py` (`_select_context_source`, `_active_phase`, `build_context_packet`)

## 5) Validate Mode Integrity Rule
- Validation command:
  - `.venv\Scripts\python scripts/build_context_packet.py --validate`
- Pass conditions:
  - JSON schema matches `PACKET_KEYS`.
  - `generated_at_utc` parseable + age <= 24h.
  - existing JSON equals expected packet except timestamp field.
  - markdown headers match required contract.
  - markdown body equals canonical render from JSON payload (parity check).
- File reference:
  - `scripts/build_context_packet.py` (`validate_existing_outputs`, `render_context_markdown`)

---

# Phase 23 Macro Gates Formula Notes

Date: 2026-02-23

## 1) QQQ Drawdown and Trend Features
- `qqq_peak_252d_t = max(qqq_close_{t-251..t})`
- `qqq_drawdown_252d_t = qqq_close_t / qqq_peak_252d_t - 1`
- `qqq_ma200_t = mean(qqq_close_{t-199..t})`
- `qqq_ma200_trend_gate_t = 1[qqq_close_t >= qqq_ma200_t]`

## 2) Adaptive Stress Labels (Slow Bleed / Sharp Shock)
- `qqq_ret_5d_t = qqq_close_t / qqq_close_{t-5} - 1`
- `qqq_ret_21d_t = qqq_close_t / qqq_close_{t-21} - 1`
- `qqq_ret_5d_z_adapt_t = z_ewm(qqq_ret_5d_t; mean_span=20, vol_span=126)`
- `qqq_ret_21d_z_adapt_t = z_roll(qqq_ret_21d_t; window=252)`
- `qqq_drawdown_252d_z_adapt_t = z_roll(qqq_drawdown_252d_t; window=252)`
- `qqq_drawdown_5d_delta_t = qqq_drawdown_252d_t - qqq_drawdown_252d_{t-5}`
- `qqq_drawdown_5d_delta_z_adapt_t = z_ewm(qqq_drawdown_5d_delta_t; mean_span=20, vol_span=126)`
- `slow_bleed_label_t = 1[(qqq_ret_21d_z_adapt_t <= -1.0) and (qqq_drawdown_252d_z_adapt_t <= -0.5)]`
- `sharp_shock_label_t = 1[(qqq_ret_5d_z_adapt_t <= -2.5) or (qqq_drawdown_5d_delta_z_adapt_t <= -2.5)]`

## 3) VIX Term Structure Gate
- `vix_term_ratio_t = vix_level_t / vix3m_level_t`
- `vix_backwardation_t = 1[vix_term_ratio_t > 1.0]`

## 4) Hard-Gate State Mapping
- `RED_t = sharp_shock_label_t or vix_backwardation_t`
- `AMBER_t = (not RED_t) and (slow_bleed_label_t or not qqq_ma200_trend_gate_t)`
- `GREEN_t = not (RED_t or AMBER_t)`
- `scalar_t = {RED: 0.0, AMBER: 0.5, GREEN: 1.0}`
- `cash_buffer_t = {RED: 0.50, AMBER: 0.25, GREEN: 0.0}`
- `momentum_entry_t = 1[state_t == GREEN and qqq_ma200_trend_gate_t and not slow_bleed_label_t and not sharp_shock_label_t]`

## 5) Implementation Files
- `data/macro_loader.py`
  - `build_macro_features` (QQQ + VIX term + adaptive labels)
  - `build_macro_gates` (daily hard-gate artifact construction)
  - `run_build` (atomic write of `macro_features.parquet` and `macro_gates.parquet`)
- `scripts/validate_macro_layer.py` (macro_features + macro_gates contract validation)

---

# Phase 23 Macro Gate Consumption Notes

Date: 2026-02-23

## 1) Strategy Consumption Contract (PiT)
- Gate outputs are consumed with strict one-day lag:
  - `state_exec_t = state_signal_{t-1}`
  - `scalar_exec_t = scalar_signal_{t-1}`
  - `cash_buffer_exec_t = cash_buffer_signal_{t-1}`
  - `momentum_entry_exec_t = momentum_entry_signal_{t-1}`
- Warmup defaults after shift:
  - `state = AMBER`
  - `scalar = 0.5`
  - `cash_buffer = 0.25`
  - `momentum_entry = False`

## 2) Phase 20 Plan Wiring
- `selected = entry_gate AND momentum_entry_exec AND (rank <= n_target)`
- `risk_budget = min(1 - cash_buffer_exec, scalar_exec)`
- `base_weight_i = risk_budget / n_selected` for selected names.

## 3) Deferred Risk Scope
- Explicitly deferred to next iteration:
  - integrating `liquidity_air_pocket`, `credit_freeze`, and `momentum_crowding` into hard-gate `RED/AMBER` state transitions.

## 4) Implementation Files
- `scripts/phase20_full_backtest.py`
  - `_load_regime_states(..., macro_gates_path, return_controls=True)`
  - `_build_phase20_plan(..., gate_scalar_by_date, gate_cash_buffer_by_date, gate_momentum_entry_by_date)`
- `strategies/regime_manager.py`
  - Direct hard-gate consumption path when macro context includes gate columns.

---

# Phase 23 Softmax Sizing Notes

Date: 2026-02-23

## 1) GREEN Allocation Rule (Orthogonal Sizing Upgrade)
- For each date `t`, on selected GREEN names only:
  - `p_i,t = exp(conviction_score_i,t / tau) / sum_j exp(conviction_score_j,t / tau)`
  - `tau = softmax_temperature` (default `1.0`)
- GREEN risk budget:
  - `risk_budget_t = 1 - cash_pct_t = 0.80`
- Final GREEN weight:
  - `w_i,t = risk_budget_t * p_i,t`

## 2) Non-GREEN Allocation Rule (Unchanged)
- For AMBER/RED regimes:
  - `w_i,t = risk_budget_t / n_selected_t` on selected names.

## 3) Numerical Stability Rule
- Softmax is computed in stabilized form:
  - `exp((x - max(x))/tau)` with clipping to bounded exponent range.
- Invalid/degenerate denominator fallback:
  - use uniform probabilities over selected GREEN names.

## 4) Implementation Files
- `scripts/phase20_full_backtest.py`
  - `parse_args` (`--softmax-temperature`)
  - `_build_phase20_plan` (GREEN softmax allocation path)

---

# Phase 23 WFO Temperature Notes

Date: 2026-02-23

## 1) Walk-Forward Protocol
- In-Sample (train):
  - `2020-01-01 -> 2022-12-31`
- Out-of-Sample (test):
  - `2023-01-01 -> 2024-12-31`
- Search space:
  - `T_values = [0.2, 0.5, 0.8, 1.0, 1.5, 2.0]`

## 2) Selection Rule
- For each `T` in `T_values`, run Phase 20 backtest on IS window.
- Record `CAGR` and `Sharpe`.
- Winning parameter:
  - `T* = argmax_T Sharpe_IS(T)`
- Tie-break in implementation:
  - higher `CAGR_IS`, then lower `T`.

## 3) OOS Verification Rule
- Execute exactly one OOS backtest using `T*`.
- No additional temperature candidates are evaluated on OOS.

## 4) Implementation Files
- `scripts/optimize_softmax_temperature.py`
  - imports and executes `scripts/phase20_full_backtest.py` logic via `phase20.main()`
  - writes IS grid + OOS result artifact:
    - `data/processed/phase23_wfo_temperature_summary.json`

---

# Phase 23 Institutional Overlay Notes

Date: 2026-02-23

## 1) Bitemporal Continuity Restoration
- Restored bounded core-fundamental continuity in conviction builder:
  - grouped by `permno`, `ffill(limit=120)` for:
    - `q_tot`, `inv_vel_traj`, `op_lev`, `rev_accel`, `CycleSetup`.
- Source path:
  - `strategies/company_scorecard.py` (`build_phase20_conviction_frame`)

## 2) Softmax Concentration Overlays
- Minimum portfolio breadth guard:
  - if `len(eligible_tickers) < 4`, abort stock sizing and force:
    - `cash_pct = 1.0`,
    - stock weights = `0.0`.
- Max single-name cap:
  - `max_weight = 0.25` (absolute portfolio weight).
  - softmax weights are capped and excess is iteratively redistributed to uncapped names.
- Source path:
  - `scripts/phase20_full_backtest.py` (`_build_phase20_plan`)

## 3) Single-Day Diagnostic Contract
- Diagnostic script:
- `scripts/diagnostic_softmax_weights.py`
- Target date:
  - requested `2021-06-01`, using closest valid day in available IS feature coverage.
- Telemetry:
  - hard-gate eligible universe (`mom_ok & support_proximity`),
  - raw conviction scores,
  - softmax allocation under `T=0.2` and `T=2.0`,
  - NaN/Inf checks.

---

# Phase 23 Wrap Notes

Date: 2026-02-23

## 1) Revertibility Lock (No-Git Safe)
- Freeze pack created to preserve code + best result artifacts in a manifest-backed snapshot:
  - `scripts/phase23_freeze_pack.py`
- Restore utility for deterministic rollback:
  - `scripts/phase23_restore_from_freeze.py`

## 2) Snapshot Output
- Latest pointer:
  - `data/processed/phase23_freeze_latest.json`
- Snapshot manifest:
  - `data/processed/phase23_freeze/<snapshot_id>/manifest.json`
- Manifest includes:
  - captured code files,
  - captured artifact files,
  - ranked best-result table (by `CAGR`, tie-break `Sharpe`),
  - per-file SHA256 for integrity verification.

## 3) Pivot Readiness (Orbis)
- Current repository scan shows no staged Orbis ingest artifacts or schema exports under project files.
- Next engineering step before `data/orbis_loader.py` implementation:
  - confirm source format/access mode,
  - confirm target feature extraction scope,
  - confirm initial regional universe filter.

---

# Phase 25B Osiris Macro Notes

Date: 2026-02-24

## 1) Core Signal Formula
- Source fields in `bvd_osiris.os_fin_ind`:
  - `inventory = data20010` (Net Stated Inventory),
  - `revenue = COALESCE(data13004, data13002, data13000)`.
- Per-company metric:
  - `inv_turnover = revenue / inventory`.
- Implementation path:
  - `data/osiris_loader.py`.

## 2) Dedup and PIT Controls
- SQL-level dedup:
  - `SELECT DISTINCT`.
- Dataframe-level dedup:
  - `drop_duplicates(subset=['os_id_number', 'closdate'])`.
- Public reporting lag:
  - `knowledge_date = closdate + 60 days`.
- Daily alignment:
  - business-day calendar + `merge_asof(direction='backward')`.
- Implementation path:
  - `data/osiris_loader.py`,
  - `scripts/align_osiris_macro.py`.

## 3) Daily Z-Score Formula
- Rolling normalization on aligned daily signal:
  - `z252_t = (x_t - mean_252_t) / std_252_t`,
  - where `x_t = median_inv_turnover_t`.
- Implementation path:
  - `scripts/align_osiris_macro.py`.

## 4) Validation Formula
- Forward return target:
  - `qqq_fwd_ret_60d_t = Close_{t+60} / Close_t - 1`.
- IC test:
  - `Spearman( median_inv_turnover_z252_t, qqq_fwd_ret_60d_t )`.
- Latest run evidence:
  - `IC = +0.087636`, `p = 1.18113e-05`, `N = 2492`.
- Implementation path:
  - `scripts/align_osiris_macro.py`.

---

# P1 Closeout Validation Formula Notes

Date: 2026-02-28

## 1) Strict Missing Returns on Executed Exposure
- Executed weight (D-04 timing contract):
  - `w_exec[t, i] = w_target[t-1, i]`
- Strict missing-return cell count:
  - `missing_executed = sum_{t,i} 1[ isna(ret_aligned[t, i]) and (w_exec[t, i] != 0) ]`
- Fail-fast rule:
  - if `strict_missing_returns=True` and `missing_executed > 0`, raise runtime error.
- Implementation path:
  - `core/engine.py` (`run_simulation`: executed-exposure mask + strict fail path).
  - Script parity:
    - `scripts/day5_ablation_report.py` (`strict_missing_returns = not allow_missing_returns`)
    - `scripts/day6_walkforward_validation.py` (`strict_missing_returns = not allow_missing_returns`)

## 2) Strict Idempotency Wiring with `client_order_id`
- Deterministic fallback ID (when order omits explicit ID):
  - `digest = UPPER(SHA256(symbol + "|" + side + "|" + qty))[0:12]`
  - `client_order_id = trade_day + "-" + symbol + "-" + UPPER(side) + "-" + qty + "-" + digest`
- Pass-through rule:
  - `submit_order(..., client_order_id)` must carry the same ID in broker payload and result payload.
- Recovery rule on submit exception:
  - if `client_order_id` exists, call `get_order_by_client_order_id(client_order_id)` and return recovered order if found.
- Recovery intent predicate (fail-closed if false):
  - `match = (recovered_symbol == intended_symbol) and (recovered_side == intended_side) and (abs(recovered_qty - intended_qty) <= 1e-9)`
  - if `match == False`: return `error='recovery_mismatch'` and do not mark order accepted.
- Implementation path:
  - `execution/rebalancer.py` (`_generate_client_order_id`, `execute_orders`)
  - `execution/broker_api.py` (`submit_order`, `get_order_by_client_order_id`)

## 3) Fundamentals Ingest Checkpoint/Resume State Machine
- Stage set:
  - `stage in {fetch, merge, final_write, done}`
- Resume gate:
  - continue only when `frozen_targets == requested_targets`;
  - else follow mismatch policy (`fail` or `reset`).
- Identity freeze:
  - `permno_map[ticker] = frozen permno` is persisted in checkpoint metadata and re-applied before resume writes.
- Semantic corruption gate:
  - metadata fields (`version`, `rows_in_partial`, `tickers_with_data`, `stage`) must pass semantic validation;
  - invalid checkpoint rows (`permno <= 0` or non-numeric/null) are routed through mismatch policy and fail closed by default.
- Checkpoint artifacts:
  - metadata JSON: `fundamentals_ingest.checkpoint.json`
  - partial rows parquet: `fundamentals_ingest.partial.parquet`
- Completion policy:
  - success + `checkpoint_keep=False` => cleanup checkpoint artifacts;
  - success + `checkpoint_keep=True` => persist with `stage=done`.
- Implementation path:
  - `data/fundamentals_updater.py` (`run_update`, checkpoint helpers, CLI flags)
  - regression coverage: `tests/test_fundamentals_updater_checkpoint.py`

---

# P2 Auto-Backtest UI Control-Plane Notes

Date: 2026-02-28

## 1) Lab/Backtest Config Normalization
- Control config tuple:
  - `(ma_lookback, stop_lookback, atr_period, vol_target, max_positions, cost_bps, min_price)`
- Normalization rules:
  - `ma_lookback_norm = clamp(round(ma_lookback / 10) * 10, 50, 300)`
  - `stop_lookback_norm = clamp(stop_lookback, 10, 60)`
  - `atr_period_norm = clamp(atr_period, 10, 40)`
  - `vol_target_norm = clamp(vol_target, 0.05, 0.30)` (percent inputs >1 are converted by `/100`)
  - `max_positions_norm = clamp(max_positions, 10, 100)`
  - `cost_bps_norm = max(0, cost_bps)`
    - when `cost_bps_unit = "bps"`: convert by `/10000`,
    - when `cost_bps_unit = "rate"`: use as-is (decimal rate).
  - `min_price_norm = max(1.0, min_price)`
- Implementation path:
  - `core/auto_backtest_control_plane.py` (`normalize_config`)

## 2) Run-Key and Staleness Contract
- Config fingerprint:
  - `fp = SHA256(JSON(normalized_config, sort_keys=True))`
- Run key:
  - `run_key = normalize_date(latest_prices_date) + ":" + fp`
- Planner staleness:
  - `is_stale = (last_run_key != run_key)`
- Attempted-state gate:
  - `attempted = run_attempted and (run_attempted_for_key == run_key)`
  - `should_run = is_stale and not attempted`
- Implementation path:
  - `core/auto_backtest_control_plane.py` (`compute_config_fingerprint`, `compute_run_key`, `build_auto_backtest_plan`)

## 3) Cache State Machine
- Start transition:
  - `status = "running"`
  - `run_attempted = True`
  - `run_attempted_for_key = run_key`
  - `last_started_at = utc_now`
- Finish transition:
  - `status in {"finished","failed"}`
  - `last_run_key = run_key`
  - `last_finished_at = utc_now`
- Implementation path:
  - `core/auto_backtest_control_plane.py` (`mark_started`, `mark_finished`)
  - `views/auto_backtest_view.py` (start/finish/failure writes around simulation)

## 4) Atomic JSON Persist Contract
- Temp path:
  - `tmp = target + "." + pid + "." + epoch_ms + ".tmp"`
- Commit:
  - `write(tmp) -> os.replace(tmp, target)`
- Retry policy:
  - bounded retries on `PermissionError` with short sleep backoff.
- Cleanup:
  - always remove temp file in `finally`.
- Implementation path:
  - `core/auto_backtest_control_plane.py` (`persist_cache_atomic`)

## 5) Cache Integrity Recovery Contract
- Default load policy:
  - `error_policy = "fail"` for normal runtime.
- Bootstrap policy:
  - auto-bootstrap defaults only when cache file is missing.
- Corruption policy:
  - `invalid_json` / `invalid_payload` must block execution path and require explicit operator reset action.
- Start-state durability policy:
  - if start-state write fails, simulation is aborted (fail closed).

---

# Phase 25 Orchestrator E2E Reconciliation Notes

Date: 2026-02-28

## 1) Authoritative Intent Anchor by CID
- Let `O0[cid]` be the normalized original pending order map before submit.
- Let `Rk` be one downstream row on attempt `k`.
- CID extraction:
  - `cid = first_non_empty(Rk.result.client_order_id, Rk.order.client_order_id)`
- Authoritative order for all parity/retry decisions:
  - `O[cid] = O0[cid]` (never trust downstream echoed `Rk.order` fields as intent source).
- Implementation path:
  - `main_bot_orchestrator.py` (`execute_orders_with_idempotent_retry`)

## 2) Batch Completeness and Fail-Closed Rule
- Per attempt `k`:
  - `Expected_k = set(pending_by_cid.keys())`
  - `Observed_k = set(cids accepted from well-formed rows)`
  - `Missing_k = Expected_k - Observed_k`
- Reconciliation:
  - if `k < max_attempts`: `next_pending <- Missing_k`
  - else: emit terminal result per missing CID with:
    - `ok=False`
    - `error='batch_result_missing'`
    - `attempt=k`
- Implementation path:
  - `main_bot_orchestrator.py` (`execute_orders_with_idempotent_retry`)

## 3) Recovery Match Predicate (Already Exists)
- Strict match on original intent:
  - `match = (symbol_rec == symbol_intent) and (side_rec == side_intent) and (abs(qty_rec - qty_intent) <= 1e-9)`
- Decision:
  - if `error contains 'already exists'` and `match=True`: accept as recovered success.
  - else if `error contains 'already exists'` and `match=False`: fail closed as `recovery_mismatch` (no retry).
- Implementation path:
  - `main_bot_orchestrator.py`

## 4) Retry Terminalization Rule
- For retryable transport faults:
  - if `attempt < max_attempts`: retry with same CID.
  - else: terminalize as:
    - `ok=False`
    - `error='retry_exhausted'`
    - `last_error=<normalized error text>`
- Implementation path:
  - `main_bot_orchestrator.py`

## 5) Malformed Row Handling Rule
- Row is considered malformed when:
  - `row` is not a dict, or
  - `row.result` is not a dict.
- Malformed rows are ignored for observation accounting (treated as unobserved), so missing-CID reconciliation applies.
- Implementation path:
  - `main_bot_orchestrator.py`
  - regression coverage in `tests/test_main_bot_orchestrator.py`

---

# Phase 26 Runtime Hardening Notes

Date: 2026-02-28

## 1) Process-Tree Timeout Termination Contract
- Spawn semantics:
  - Windows: create new process group (`CREATE_NEW_PROCESS_GROUP`).
  - POSIX: create new session (`start_new_session=True`).
- Timeout semantics:
  - on scanner timeout, terminate process tree first, then re-raise timeout.
- Windows kill contract:
  - execute `taskkill /PID <pid> /T /F`,
  - require `returncode == 0`, else log hard error.
- POSIX kill contract:
  - send `SIGTERM` to process group,
  - wait bounded grace window,
  - escalate to `SIGKILL` if still alive.
- Implementation path:
  - `main_bot_orchestrator.py` (`_spawn_scanner_process`, `_terminate_process_tree`, `_run_scanner_step`)

## 2) Scheduler Resilience Contract
- Runtime loop behavior:
  - scanner run failure logs error and loop continues,
  - only explicit `KeyboardInterrupt` disarms orchestrator loop.
- Implementation path:
  - `main_bot_orchestrator.py` (`main`)

## 3) Canonical Seed Boundary Contract
- Entry seed rule:
  - every order must provide at least one canonical seed:
    - explicit `client_order_id`, or
    - canonical `trade_day`.
- Null-like normalization:
  - `None`, `null`, `nan` textual forms are treated as missing.
- Enforcement path:
  - pre-normalization gate in `execute_orders_with_idempotent_retry`.
- Implementation path:
  - `main_bot_orchestrator.py` (`_clean_optional_str`, `execute_orders_with_idempotent_retry`)

## 4) Malformed Batch Schema Contract
- Non-list `batch_results` from downstream are treated as empty.
- Dict-shaped rows missing `result.ok` are treated as malformed/unobserved.
- Unobserved CIDs are reconciled through:
  - retry when attempts remain,
  - terminal fail-closed `batch_result_missing` when retries are exhausted.
- Implementation path:
  - `main_bot_orchestrator.py`
  - `tests/test_main_bot_orchestrator.py`

## 5) Rebalance Entrypoint Contract
- Script-level wiring:
  - `scripts/test_rebalance.py` seeds `trade_day`,
  - submits via `execute_orders_with_idempotent_retry(...)`,
  - exits with non-zero code when any submission fails.
- Regression coverage:
  - `tests/test_test_rebalance_script.py`.

---

# Phase 27 Conditional-Block Remediation Notes

Date: 2026-02-28

## 1) Strict Boolean `ok` Gate (Fail-Closed)
- Row admissibility predicate:
  - `admissible_row = isinstance(row, dict) and isinstance(row.result, dict) and isinstance(row.result.ok, bool)`
- Non-admissible rows are treated as unobserved:
  - `Observed_k` excludes these rows.
  - Missing CID reconciliation then applies:
    - retry while attempts remain,
    - terminal `batch_result_missing` at exhaustion.
- Entrypoint success accounting:
  - `ok_count = sum(1 for row in execute_results if row.result.ok is True)`
  - any non-boolean `ok` value is counted as failed.

## 2) Universal Success Parity with Sparse-Payload Fallback
- Acceptance predicate for all `ok=True` rows:
  - `match = (symbol_rec == symbol_intent) and (side_rec == side_intent) and (abs(qty_rec - qty_intent) <= 1e-9)`
- Fallback resolution when success payload omits fields:
  - `symbol_rec = first_non_empty(result.symbol, row.order.symbol)`
  - `side_rec = first_non_empty(result.side, row.order.side)`
  - `qty_rec = first_non_null(result.qty, row.order.qty)`
- Decision:
  - if `match=False`: fail closed with `intent_mismatch` (or `recovery_mismatch` for recovered payloads).
  - if `match=True`: accept terminal success.

## 3) Strict `qty` Type Guardrails
- Input normalization guard:
  - reject boolean quantities:
    - `if isinstance(order.qty, bool): raise ValueError`
  - parse numeric quantity:
    - `qty = int(order.qty)` else fail closed.
- Recovery matcher guard:
  - reject boolean recovered quantity:
    - `if isinstance(result.qty, bool): return False`
  - parse numeric recovered quantity:
    - `qty_rec = float(result.qty)` else fail closed.

## 4) Terminate-Confirmed-or-Fail Contract
- Timeout sequence:
  1. scanner process times out,
  2. invoke process-tree termination,
  3. require liveness confirmation (`proc.poll() is not None`) within grace windows,
  4. if not confirmed, raise terminal `ScannerTerminationError`.
- Terminal propagation:
  - startup diagnostic path and scheduler loop re-raise `ScannerTerminationError` after critical logging.

## 5) Startup Containment Parity
- Startup diagnostic follows scheduler-style containment for non-terminal exceptions:
  - `except Exception -> log error -> continue to armed scheduler mode`
- Terminal scanner-kill failures are not contained:
  - `except ScannerTerminationError -> critical log -> raise`

---

# Phase 28 Entrypoint Contract Remediation Notes

Date: 2026-02-28

## 1) Atomic Payload Entry Gate (Local Submit)
- Payload row admissibility:
  - `admissible_row = is_dict(row) AND has_required_fields(row) AND all_field_validators_pass`
- Batch policy:
  - if any row is non-admissible, abort entire batch:
    - `raise ValueError(...)`
  - no partial-row skipping is allowed.
- Required row fields:
  - `ticker|symbol`, `target_weight`, `action|side`, `order_type`, `limit_price`, `client_order_id`, `trade_day`.
- Validation highlights:
  - `target_weight > 0` and finite,
  - `order_type in {MARKET, LIMIT}`,
  - `trade_day` must be `YYYYMMDD` and a valid calendar date,
  - duplicate `ticker` or duplicate `client_order_id` is rejected.
- Implementation path:
  - `main_console.py` (`_validate_payload_execution_rows`)

## 2) Local Intent Parity Contract
- After target-weight -> order calculation, enforce exact symbol-set parity:
  - `set(payload_symbols) == set(calculated_symbols)`
- For each symbol, seed order intent and assert parity:
  - `symbol`, `side`, `qty`, `order_type`, `limit_price`, `client_order_id` must match expected intent.
- Limit-price policy:
  - `MARKET` -> `limit_price = None`,
  - `LIMIT + fixed numeric` -> use fixed numeric,
  - `LIMIT + Bid_Ask_Mid token` -> resolve from calculated price.
- Implementation path:
  - `main_console.py` (`_resolve_seeded_limit_price`, `_assert_seeded_order_parity`, `_execute_payload_via_idempotent_helper`)

## 3) CID Reconciliation Contract (Helper Output)
- Expected set:
  - `ExpectedCID = {payload_row.client_order_id}`
- Observed set:
  - `ObservedCID = {row.order.client_order_id from helper results}`
- Acceptance:
  - `ObservedCID == ExpectedCID` and no duplicates/unknown CIDs.
- Else fail closed:
  - unknown CID, duplicate CID, or missing CID rows -> `ValueError`.
- Implementation path:
  - `main_console.py` (`_execute_payload_via_idempotent_helper`)

## 4) Broker Submit/Recovery Intent Contract
- Submit boundary:
  - reject bool qty:
    - `if isinstance(qty, bool): invalid_qty`
  - enforce `order_type`/`limit_price` consistency:
    - market: no valid non-null limit semantics,
    - limit: finite positive `limit_price` required.
- Recovery parity:
  - strict match on:
    - `symbol`, `side`, `qty`, `order_type`, `client_order_id`
  - market-order recovery accepts only null-like `limit_price`:
    - `{None, "", "none", "null"}`
  - non-null numeric market `limit_price` fails closed as `recovery_mismatch`.
- Implementation path:
  - `execution/broker_api.py` (`submit_order`, `_recovery_matches_intent`, `get_order_by_client_order_id`)

## 5) Orchestrator Recovery Parity Extension
- Retry normalization now carries:
  - `order_type`, `limit_price` in addition to `symbol/side/qty/client_order_id`.
- Recovery acceptance predicate extends to:
  - `symbol/side/qty/order_type/limit_price` parity (plus CID anchoring).
- Implementation path:
  - `main_bot_orchestrator.py` (`_normalize_order_for_retry`, `_recovery_result_matches_intent`)

## DevSecOps Stream Controls (2026-03-01)
- Scope:
  - secret scrub for WRDS/FMP credentials,
  - cache-level API-key redaction,
  - deny-by-default egress policy,
  - HMAC key lifecycle contract with legal-hold exception.
- Explicit formulas and code loci:
  - key-age (days) with future-skew guard:
    - `age_seconds = (now_utc - hmac_key_activated_at_utc).total_seconds()`
    - `if age_seconds < -max_future_skew_seconds: fail_closed`
    - `age_days = max(0, age_seconds / 86400)`
    - implemented in `core/security_policy.py` (`get_hmac_rotation_status`).
  - rotation due:
    - `rotation_due = (age_days >= rotation_days) and (not legal_hold)`
    - implemented in `core/security_policy.py` (`get_hmac_rotation_status` / `require_hmac_rotation_compliance`).
- Runtime contracts:
  - required env:
    - `TZ_HMAC_KEY_VERSION`, `TZ_HMAC_KEY_ACTIVATED_AT_UTC`,
    - `WRDS_USER`, `WRDS_PASS`, `FMP_API_KEY`,
    - Alpaca key pair (`APCA_API_KEY_ID` + `APCA_API_SECRET_KEY` or aliases).
  - legal-hold exception:
    - `TZ_HMAC_KEY_LEGAL_HOLD=YES`.
  - egress allowlist extension:
    - `TZ_ALLOWED_EGRESS_HOST_SUFFIXES=host1,host2,...` (extends defaults).
  - egress allowlist override mode:
    - `TZ_ALLOWED_EGRESS_HOST_SUFFIXES_MODE=override`.
  - transport and notification controls:
    - HTTPS required for egress by default,
    - optional localhost-only HTTP break-glass: `TZ_ALLOW_HTTP_EGRESS_LOCALHOST=YES`,
    - post-submit webhook failures degrade with warning while payload-only notification remains fail-closed.
- Follow-through controls (Track 3 approved):
  - Data Health derivation is sourced from in-memory HF proxy input payload (same object passed as `manual_inputs` to the scanner).
  - Explicit formulas:
    - `degraded_count = count(signal.status == "DEGRADED")`
    - `degraded_ratio = degraded_count / total_signals`
    - `status = "DEGRADED" if degraded_count > 0 else "HEALTHY"`
  - Implementation path:
    - `core/dashboard_control_plane.py`:
      - `derive_hf_proxy_data_health`
      - `ensure_payload_data_health`
    - `dashboard.py`:
      - payload persistence: `payload["data_health"]`
      - operator surface: compact badge + expandable details panel.
  - Malformed FMP payload hardening expansion:
    - added regression classes for non-rate-limit dict, unexpected scalar payload, and invalid JSON decode paths in `tests/test_ingest_fmp_estimates.py`.

---

# Phase 29 Microstructure Telemetry Notes

Date: 2026-03-01

## 1) Arrival Midpoint Anchor (Sovereign_Command Time)
- At command generation, each seeded order captures:
  - `arrival_ts` (UTC, ms precision),
  - `arrival_quote_ts`,
  - `arrival_bid_price`, `arrival_ask_price`,
  - `arrival_price`.
- Formula:
  - `arrival_price = (arrival_bid_price + arrival_ask_price) / 2`.
- Implementation path:
  - `main_console.py` (`_execute_payload_via_idempotent_helper`)
  - `execution/broker_api.py` (`get_latest_quote_snapshot`)

## 2) Partial-Fill Aggregation by `client_order_id`
- Fill rows are captured from broker activity feed when available.
- Fallback is snapshot-level fill (`filled_qty`, `filled_avg_price`) when activity rows are unavailable.
- Fill VWAP formula:
  - `VWAP_fill = sum(fill_price_i * fill_qty_i) / sum(fill_qty_i)`.
- Implementation path:
  - `execution/broker_api.py` (`_list_fill_activities`, `_summarize_partial_fills`, `_extract_fill_telemetry`)

## 3) Deterministic Slippage / Implementation Shortfall
- Buy shortfall:
  - `IS_buy = (VWAP_fill - arrival_price) * fill_qty`.
- Sell shortfall (cost-positive):
  - `IS_sell = (arrival_price - VWAP_fill) * fill_qty`.
- Slippage standardization:
  - `slippage_bps = (signed_delta / arrival_price) * 10,000`.
  - `signed_delta = VWAP_fill - arrival_price` for buys.
  - `signed_delta = arrival_price - VWAP_fill` for sells.
- Implementation path:
  - `execution/microstructure.py` (`_calc_execution_cost_metrics`)

## 4) Latency Decomposition
- `latency_ms_command_to_submit = submit_sent_ts - arrival_ts`.
- `latency_ms_submit_to_ack = broker_ack_ts - submit_sent_ts`.
- `latency_ms_ack_to_first_fill = first_fill_ts - broker_ack_ts`.
- `latency_ms_command_to_first_fill = first_fill_ts - arrival_ts`.
- Implementation path:
  - `execution/microstructure.py` (`_ms_diff`, `build_execution_telemetry_rows`)

## 5) Post-Trade Telemetry Sink
- Order rows:
  - `data/processed/execution_microstructure.parquet`
  - DuckDB: `data/processed/execution_microstructure.duckdb` table `execution_microstructure`.
- Fill rows:
  - `data/processed/execution_microstructure_fills.parquet`
  - DuckDB table `execution_microstructure_fills`.
- Local-submit integration path:
  - `main_console.py` (`_persist_execution_microstructure`, `main` local-submit branch)
- Persistence behavior:
  - telemetry sink write failure is fail-closed for local submit.

---

# Phase 30 Release Engineering Notes

Date: 2026-03-01

## 1) Digest-Locked Release Identity
- Canonical release reference formula:
  - `release_ref = "<repo>:<tag>@sha256:<64-hex>"`
- Validation path:
  - `core/release_metadata.py` (`is_digest_locked_release_ref`, `require_digest_locked_release_ref`)

## 2) UI Cache Fingerprint Bound To Artifact Identity
- Explicit formula:
  - `cache_fingerprint = "<version>@sha256:<release_digest|local-dev>"`
- Implementation path:
  - `core/release_metadata.py` (`build_release_cache_fingerprint`)
  - `dashboard.py` (`_release_bound_cache_version`)

## 3) Promotion and Rollback State Machine
- State transition (high level):
  - `idle/active -> pending_probe -> active|rolled_back|rollback_failed`
- Rollback target contract:
  - on failed startup probe:
    - restore `N-1` (`current_release` before candidate stage),
    - fallback to `previous_release` only when `current_release` is absent.
  - `status=rolled_back` is valid only when rollback verification succeeds (`rollback_ok=True`).
  - `status=rollback_failed` records unresolved runtime rollback outcome.
- External probe safety gate:
  - `--mode external-probe` requires explicit `--allow-external-probe-promote`.
- Implementation path:
  - `scripts/release_controller.py` (`execute_release_controller`, `build_docker_startup_probe`)

---

# Phase 31 Stream 2 Risk Interceptor Notes

Date: 2026-03-01

## 1) Post-Trade Exposure and Weight Checks
- Portfolio-state ingest contract:
  - malformed or non-finite broker position quantities are fail-closed (`risk_check_error`), not silently dropped.
- Post-trade quantity projection:
  - `qty_post_i = qty_current_i + qty_order_i` for buy orders.
  - `qty_post_i = qty_current_i - qty_order_i` for sell orders.
- Long-only invariant:
  - if `long_only=True`, enforce `qty_post_i >= 0` for every symbol projection.
  - if violated, return deterministic block with `reason_code=invalid_order_projection`.
- Notional exposure:
  - `exposure_i = abs(qty_post_i) * price_i`.
- Weight:
  - `weight_i = exposure_i / equity`.
- Single-asset hard limit:
  - `max_i(weight_i) <= max_single_asset_weight`.
- Implementation path:
  - `execution/risk_interceptor.py` (`project_state`, `evaluate`)

## 2) Sector Concentration Hard Limit
- Sector exposure aggregation:
  - `sector_exposure_s = sum(exposure_i for i in sector s)`.
- Sector weight:
  - `sector_weight_s = sector_exposure_s / equity`.
- Hard limit:
  - `max_s(sector_weight_s) <= max_sector_weight`.
- Sector source resolution order:
  - broker `get_sector_map/get_sector_for_symbol` -> portfolio state `sector_map/sectors` -> order row `sector` fallback -> `UNKNOWN`.
- Implementation path:
  - `execution/risk_interceptor.py` (`_resolve_sector_map`, `evaluate`)

## 3) VIX Kill-Switch Gate
- Decision rule:
  - if `side == buy` and `vix > 45`, then `BLOCK`.
  - sell orders remain eligible (gate does not block exits).
- VIX source resolution order:
  - broker (`get_vix_level/get_vix`) -> portfolio state (`vix`/`vix_level`) -> order row (`vix`/`vix_level`) fallback.
- Implementation path:
  - `execution/risk_interceptor.py` (`_resolve_vix`, `evaluate`)

## 4) VaR Proxy Hard Limit
- Per-symbol volatility input:
  - broker `get_symbol_volatility` -> portfolio-state map -> order row `volatility`/`volatility_1d`/`vol` fallback -> default.
- Portfolio VaR proxy:
  - `var_proxy = z * sqrt(sum((weight_i * sigma_i)^2))`
  - where `z = var_confidence_z`.
- Hard limit:
  - `var_proxy <= max_var_proxy`.
- Implementation path:
  - `execution/risk_interceptor.py` (`_resolve_symbol_volatility`, `_compute_var_proxy`, `evaluate`)

## 5) Fail-Closed Execution and Block Audit Trail
- Rebalancer integration point:
  - Risk check executes after order-shape validation and before `broker.submit_order(...)`.
- Batch preflight contract:
  - normalize/validate the entire order batch before first submit side effect.
- Rebalance ordering contract:
  - sell orders are sequenced before buys to reduce avoidable cash-constraint rejects.
- Fail-closed contract:
  - any interceptor/bootstrap/state-update exception returns a `BLOCK` result and skips broker submit.
- State-commit ordering:
  - projected risk state is committed only when `result["ok"] is True` after submit.
  - conservative pending-order policy: only buy legs are projected pre-fill; sells are not credited until downstream fill telemetry confirms execution.
- Batch halt contract (optional):
  - when `halt_on_risk_block=True` (or order flag `halt_batch_on_block=True`), the first block halts remaining batch rows as `risk_batch_halt`.
- Atomic audit persistence:
  - write JSON to `logs/risk/<unique>.tmp`, then `os.replace(tmp, final)` to `logs/risk/risk_block_*.json`.
- Audit-write failure semantics:
  - if audit persistence fails, return `reason_code=risk_blocked_audit_failed` and force batch halt fail-stop.
- Implementation path:
  - `execution/rebalancer.py` (`execute_orders`)
  - `execution/risk_interceptor.py` (`persist_block_decision`)

---

# Phase 30 Truth Layer Formula Notes (PiT + Scaling + Atomic Commit)

Date: 2026-03-01

## 1) PiT Fundamentals Availability Contract
- Daily availability interval:
  - `active(date) := published_at <= date < next_published_at`
- Join discipline:
  - features must consume fundamentals values on panel date rows only, not `release_date` forward-fill.
- Implementation path:
  - `data/fundamentals_panel.py` (`build_daily_fundamentals_panel`, interval SQL join)
  - `data/fundamentals.py` (`build_fundamentals_daily`, panel-first path)

## 2) Robust Cross-Sectional Scaling Contract
- For each date cross-section:
  - `median_t = median(x_{i,t})`
  - `MAD_t = median(|x_{i,t} - median_t|)`
  - `robust_sigma_t = max(1.4826 * MAD_t, epsilon_floor)`
  - `z_{i,t}^{robust} = (x_{i,t} - median_t) / robust_sigma_t`
- Sparse cross-section fallback:
  - if `window_size_t < min_window_size`, use percentile fallback:
  - `z_{i,t}^{pct} = (rank_pct_{i,t} - 0.5) * 2`
- Observability:
  - `fallback_rate = fallback_rows / total_rows`
- Implementation path:
  - `data/feature_store.py` (`_cross_sectional_scale`, `_cross_sectional_percentile_fallback`, `run_build` telemetry)

## 3) Incremental Patch Upsert Contract (Yahoo Bridge)
- Partitioning:
  - `partition_key = (year(date), month(date))`
- Upsert dedupe key:
  - `(permno, date)`, keep latest row in merge order.
- Write path:
  - touched-partition-only rewrite under updater lock.
- Implementation path:
  - `data/updater.py` (`_upsert_partitioned_patch_rows`, `_atomic_partition_swap`, `publish_patch_rows`)

## 4) Feature Store Atomic Commit Contract
- Single-visible-commit protocol:
  - apply partition merges in stage dataset root
  - write commit manifest and tombstone metadata
  - atomically swap stage root into `features.parquet`
- Read-side policy gate:
  - `stale_while_revalidate_sec = 0`
  - `tombstone_priority = enforced`
- Implementation path:
  - `data/feature_store.py` (`_atomic_upsert_features`, `_write_feature_commit_manifest`, `_validate_feature_manifest_policy`)

## 5) Crash-Recovery + Lock Ownership Contract
- Backup-swap recovery:
  - if `target_path` is missing and `target_path.bak.*` exists, restore newest backup before any read/write merge path.
  - if live `target_path` exists, stale backups are pruned.
- Lock-owner rule:
  - backup recovery is blocked only for a live external owner lock.
  - self-owned lock (`lock_pid == current_pid`) is recovery-eligible.
- Lock-release rule:
  - `release` is token-owned only.
  - if no token exists, lock file is not removed (`no token => no delete`).
- Implementation path:
  - `data/updater.py` (`_recover_backup_swap`, `_update_lock_owner_live`, `_release_update_lock`)
  - `data/feature_store.py` (`_recover_atomic_replace_backups`, `_update_lock_owner_live`, `run_build`)

## 6) Yahoo Chunk Failure Fail-Closed Contract
- Chunk accounting:
  - treat transport exceptions as explicit `chunk_failed=True`.
  - `failed_chunks = count(None results + chunk_failed frames)`.
- Update gate:
  - if `failed_chunks > 0`, abort update before ticker-map or patch writes.
  - if all chunks fail (`all_chunks_failed=True`), return hard failure (`success=False`).
- Implementation path:
  - `data/updater.py` (`batch_download_yahoo`, `parallel_batch_download_yahoo`, `run_update`)

## 7) Feature Manifest V2 (Pointer + Cryptographic Seal)
- Commit pointer:
  - `CURRENT -> <commit_id>` (atomic pointer swap via `os.replace`).
- Manifest identity:
  - `commit_id = sha256(seed|time_ns|pid)[:16]`.
- Partition seal:
  - each active partition entry includes:
  - `file` (immutable parquet path)
  - `sha256 = SHA256(file_bytes)`
  - `size_bytes`
- Read acceptance gate:
  - before scan, verify:
  - cache policy contract (`stale_while_revalidate_sec=0`, `tombstone_priority=enforced`)
  - GC grace contract (`retention_hours_min >= 24`)
  - physical file existence and `sha256(file_bytes) == manifest.sha256`.
- Implementation path:
  - `data/feature_store.py` (`_build_feature_manifest_v2`, `_set_feature_current_commit`, `_validate_feature_manifest_hashes`, `_feature_store_scan_sql`)

## 8) Touched-Partition Commit Assembly (No Full Root Clone)
- Incremental commit path:
  - read current active slice by partition
  - merge `(date, permno)` with new rows (new wins)
  - write immutable parquet only for touched partitions
  - write v2 manifest
  - atomically swap `CURRENT` pointer
  - refresh root current-view cache (`part-000.parquet`) only for touched partitions
- Filesystem atomicity invariant:
  - every replace path asserts same-filesystem requirement before `os.replace`.
- Complexity shift:
  - old: `O(total_dataset_size)` (`copytree`)
  - new: `O(touched_partitions + metadata)`
- Implementation path:
  - `data/feature_store.py` (`_atomic_upsert_features`, `_write_partition_file_atomic`, `_refresh_current_partition_cache`, `_assert_same_filesystem_for_replace`)

## 9) MVCC Retention Safety Baseline
- Tombstone retention model:
  - replaced/removed partition files are recorded in manifest tombstones with:
  - `retained_until_utc = now + retention_hours_min`.
- Current safety posture:
  - commit path performs no aggressive physical deletion of immutable version files.
  - this is intentional to avoid invalidating long-running readers.
- Implementation path:
  - `data/feature_store.py` (`_atomic_upsert_features`, manifest `gc_policy` + `tombstones`)

## 10) Publish Lock Ownership Gate (Token-Validated)
- Publish authorization contract:
  - if update lock file exists, feature-store publish is allowed only when:
  - `expected_lock_token != ""`
  - `expected_lock_token == live_lock_token`.
- Fail-closed rules:
  - missing token -> block publish.
  - mismatched token -> block publish.
  - lock file without token metadata -> block publish.
- Enforcement path:
  - `data/feature_store.py` (`_assert_feature_write_lock`, `_set_feature_current_commit`, `_atomic_upsert_features`)
  - `run_build` now threads acquired updater lock token into partitioned write/upsert paths.

## 11) Manifest Read Strictness (Version + Partition-Key/File Consistency)
- Version gate:
  - partitioned read path requires `manifest.version == "v2"`.
  - downgraded/non-v2 pointed manifests are rejected fail-closed.
- Partition identity gate:
  - for each manifest partition entry:
  - `derived_partition(file_path) == manifest_partition_key`.
  - mismatch is rejected before scan.
- Enforcement path:
  - `data/feature_store.py` (`_feature_store_scan_sql`, `_partition_relpath_from_file_path`, `_validate_feature_manifest_hashes`)
  - tests:
    - `tests/test_feature_store.py::test_feature_store_scan_fails_closed_on_manifest_version_downgrade`
    - `tests/test_feature_store.py::test_feature_store_scan_fails_closed_on_manifest_partition_mismatch`

## 12) Fail-Loud Bootstrap Invariant (No mtime Guessing)
- Bootstrap policy:
  - for existing partitioned datasets, missing `CURRENT`/manifest lineage is treated as ambiguous state.
  - system raises `AmbiguousFeatureStoreStateError` and refuses implicit state reconstruction.
- Deterministic exception:
  - unsealed bootstrap is allowed only during the same-process `full_rebuild` handoff where dataset state is freshly materialized.
- Removed behavior:
  - no "latest mtime wins" partition inference.
- Implementation path:
  - `data/feature_store.py` (`AmbiguousFeatureStoreStateError`, `_scan_current_partition_files`, `_bootstrap_feature_manifest_v2`, `_ensure_partitioned_feature_store`)
  - tests:
    - `tests/test_feature_store.py::test_ensure_partitioned_feature_store_fails_closed_when_manifest_missing`
    - `tests/test_feature_store.py::test_bootstrap_feature_manifest_v2_fails_on_ambiguous_partition_files`

## 13) EXDEV / Cross-Filesystem Fail-Closed Contract
- Atomic replace requirement:
  - all replace paths require same-filesystem check before `os.replace`.
- Adversarial validation:
  - simulated cross-device st_dev mismatch raises fail-closed runtime error.
  - simulated pointer-swap `EXDEV` leaves previous `CURRENT` pointer unchanged.
- Implementation path:
  - `data/feature_store.py` (`_assert_same_filesystem_for_replace`, `_set_feature_current_commit`)
  - tests:
    - `tests/test_feature_store.py::test_assert_same_filesystem_for_replace_fails_closed_on_cross_device`
    - `tests/test_feature_store.py::test_set_feature_current_commit_fails_closed_on_exdev_and_preserves_pointer`

## 14) Tombstone Retention + Priority Enforcement
- Retention gate:
  - every manifest v2 tombstone requires `retained_until_utc`.
- Priority gate:
  - active partition files must not overlap with tombstoned file paths.
  - overlap triggers fail-closed read rejection (`tombstone_priority='enforced'`).
- Implementation path:
  - `data/feature_store.py` (`_validate_feature_manifest_tombstones`, `_feature_store_scan_sql`)
  - tests:
    - `tests/test_feature_store.py::test_manifest_tombstones_include_retention_window`
    - `tests/test_feature_store.py::test_feature_store_scan_fails_closed_on_missing_tombstone_retention`
    - `tests/test_feature_store.py::test_feature_store_scan_blocks_tombstoned_active_file`

## 15) Strict Orchestrator Docker Draft Contract (Stream 4 Track B)
- Draft artifact:
  - `Dockerfile.orchestrator.strict`
- Immutable base:
  - `PYTHON_BASE_REF` must be digest-pinned (`@sha256:...`).
- OS dependency determinism:
  - apt resolution pinned to `snapshot.debian.org` with fixed `DEBIAN_SNAPSHOT`.
  - runtime shared libraries are version-pinned (`ca-certificates`, `libgcc-s1`, `libstdc++6`, `libgomp1`).
- Lock artifact integrity gate:
  - dependency install source is `requirements.lock`.
  - `REQUIREMENTS_LOCK_SHA256` must match `SHA256(requirements.lock)` before install.
- Runtime scope:
  - orchestrator-focused copy set (`main_bot_orchestrator.py`, `core/`, `execution/`, `scripts/`) and deterministic entrypoint.
- Implementation path:
  - `Dockerfile.orchestrator.strict`
  - `docs/production_deployment.md` (strict draft subsection)

---

# Stream 5 Option 2 Formula Notes (Terminal-Unfilled Semantics + Recovery Anchor Backfill)

Date: 2026-03-01

## 1) Terminal unfilled local-submit contract
- Terminal unfilled predicate:
  - `terminal_unfilled := status in {canceled, cancelled, rejected, expired} AND fill_qty <= 0`
- Local-submit acceptance rule:
  - `accepted_local_submit := (ok == True) AND (terminal_unfilled == False)`
- Fail-closed output normalization:
  - `ok = False`
  - `error = "terminal_unfilled:<status>"` (unless an explicit row error already exists in orchestrator reconciliation)
- Implementation path:
  - `execution/broker_api.py` (`_is_terminal_unfilled_result`, `_normalize_submit_acceptance`)
  - `main_bot_orchestrator.py` (`_is_terminal_unfilled_execution_result`, fail-closed non-retry branch)

## 2) Recovery latency-anchor backfill formulas
- Recovery payload anchor assignment (first non-empty field wins):
  - `submit_sent_ts := submit_sent_ts || submitted_at || created_at || updated_at`
  - `broker_ack_ts := broker_ack_ts || updated_at || submitted_at || created_at`
- Implementation path:
  - `execution/broker_api.py` (`_backfill_latency_anchors`)
  - `execution/microstructure.py` (`_resolve_latency_anchors`)

## 3) Clock-drift-safe latency decomposition
- Drift-safe latency formula:
  - `latency_ms = max(0, (t_end - t_start) * 1000)`
- Applied in telemetry decomposition:
  - `command_to_submit`, `submit_to_ack`, `ack_to_first_fill`, `command_to_first_fill`.
- Implementation path:
  - `execution/microstructure.py` (`_ms_diff`)

## 4) Signed slippage invariants (no abs coercion)
- Buy delta:
  - `delta_buy = fill_vwap - arrival_price`
- Sell delta:
  - `delta_sell = arrival_price - fill_vwap`
- Slippage:
  - `slippage_bps = (delta / arrival_price) * 10,000`
- Test invariants:
  - favorable buy => `slippage_bps < 0`
  - neutral fill => `slippage_bps = 0`
- Validation path:
  - `tests/test_execution_microstructure.py`

## 5) Adaptive heartbeat freshness (rolling MAD + hard ceiling)
- Objective:
  - convert submit-to-ack latency telemetry into deterministic `PASS/BLOCK` freshness decisions without look-ahead.
- Rolling context (strictly point-in-time):
  - for row `t`, baseline uses only historical rows:
  - `history_t = {latency_{t-k}, ..., latency_{t-1}}`, `N=64`.
  - cross-batch history bootstrap is event-time ordered from sink rows:
  - `event_time_t = coalesce(arrival_ts, submit_sent_ts, broker_ack_ts, filled_at, execution_ts, captured_at_utc, created_at, updated_at)`
  - sort invariant before baseline extraction: `ORDER BY event_time_t DESC NULLS LAST`.
- Robust statistics:
  - `median_t = median(history_t)`
  - `MAD_t = median(|history_t - median_t|)`
  - `robust_sigma_t = max(1.4826 * MAD_t, 5.0)`
- Adaptive threshold:
  - when `len(history_t) >= 12`:
  - `adaptive_limit_t = median_t + 4.0 * robust_sigma_t`
  - bootstrap fallback otherwise:
  - `adaptive_limit_t = 150.0`
  - clamp:
  - `adaptive_limit_t = clip(adaptive_limit_t, 25.0, hard_ceiling_ms)`
- Hard ceiling:
  - `hard_ceiling_ms = env(TZ_EXEC_HEARTBEAT_HARD_CEILING_MS, default=500.0)`
- Deterministic decision:
  - `BLOCK(latency_missing)` if `latency_ms_submit_to_ack` is missing/non-finite
  - `BLOCK(hard_ceiling_exceeded)` if `latency_ms_submit_to_ack > hard_ceiling_ms`
  - `BLOCK(adaptive_limit_exceeded)` if `latency_ms_submit_to_ack > adaptive_limit_t`
  - else `PASS(within_limit)`
- Implementation path:
  - `execution/microstructure.py`
  - functions:
    - `evaluate_heartbeat_freshness`
    - `annotate_heartbeat_freshness_frame`
    - `build_execution_telemetry_rows` (row-level persistence fields)
    - `_load_recent_submit_to_ack_history_ms` (cross-batch history bootstrap)
- Backfill/eval runners:
  - `scripts/backfill_execution_latency.py`
  - `scripts/evaluate_execution_slippage_baseline.py`
  - source loader mode contract:
  - default: `source_mode = duckdb_strict` (fail-loud on missing/unreadable/query-failing DuckDB).
  - explicit override only: `source_mode = parquet_override` via `--source-mode parquet_override` or `TZ_EXEC_TELEMETRY_SOURCE_MODE=parquet_override`.
  - no implicit DuckDB->Parquet fallback.
  - cohort-aligned baseline formulas in `compute_slippage_baseline(...)`:
  - `sanitize(x) = x if isfinite(x) else null`
  - `cohort_slippage_bps_i = slippage_bps_i if observed else 0.0`
  - `mean_slippage_bps = mean(cohort_slippage_bps)`
  - `median_slippage_bps = median(cohort_slippage_bps)`
  - report transparency fields:
  - `cohort_rows`, `observed_rows`, `zero_imputed_rows`.

## Phase 31 Addendum: Trust-Boundary + Telemetry Durability Contracts

Date: 2026-03-01

### 1) Signed replay atomicity (`execution/signed_envelope.py`)
- Replay key:
  - `replay_key = intent_id + ":" + nonce`
- Atomic replay gate:
  - under exclusive ledger lock, apply:
  - `reject if replay_key in seen`
  - else append replay row and fsync.
- Malformed ledger handling:
  - malformed rows are quarantined to `<ledger>.malformed.jsonl`,
  - ledger is rewritten with valid lines only.

### 2) Spool UID + idempotent sink replay (`execution/microstructure.py`)
- Deterministic spool UID per consumed line:
  - `_spool_record_uid = sha1(f"{generation}:{line_start}:{payload}")`
- DuckDB idempotent insert contract:
  - insert only rows where `_spool_record_uid` is not present in target table.
- Legacy single-file parquet idempotent fallback:
  - merge and `drop_duplicates(subset in {record_id, uid, _spool_record_uid}, keep="first")` before atomic rewrite.

### 3) Corruption quarantine + stale partial-line self-heal (`execution/microstructure.py`)
- Schema-invalid JSON record quarantine reasons:
  - `schema_invalid_record_type`, `schema_row_not_object`.
- JSON parse corruption quarantine reason:
  - `json_decode_error`.
- Trailing partial-line stale policy:
  - `quarantine_trailing_partial := (line has no '\n') AND (now - spool_mtime >= 2.0s)`.

### 4) Local-submit telemetry durability gate (`main_console.py`)
- Durability acceptance rule:
  - `durability_pass := drained == True AND pending_bytes == 0 AND last_flush_error == ""`.
- Local-submit success/notify is blocked unless `durability_pass` is true.

### 5) Snapshot/semantic coercion contracts
- Alpha candidate ranking:
  - `rank_key = (-numeric(composite_score), +numeric(permno))` (stable sort; NaN last).
  - file: `strategies/alpha_engine.py`.
- Trend veto parser:
  - `True tokens = {true,1,yes,on,t,y}`,
  - `False tokens = {false,0,no,off,f,n}`,
  - unknown -> default policy.
  - file: `strategies/alpha_engine.py`.
- Ticker-pool boolean parser uses deterministic token sets for `style_compounder_gate` and `weak_quality_liquidity`.
  - file: `strategies/ticker_pool.py`.

### 6) Stream 5 Option 2 reconciliation addendum (`main_bot_orchestrator.py`, `execution/microstructure.py`)
- Terminal partial-fill fail-closed rule (retry loop):
  - `terminal_partial := status in {canceled,cancelled,rejected,expired,done_for_day,stopped,suspended} AND fill_qty > 0`
  - action: finalize row with `ok=False` and no retry enqueue.
- Summary-only fill consistency rule:
  - if `partial_fills == []` and order-level summary is present (`fill_count>0`, `fill_qty>0`, `fill_vwap>0`), synthesize one fill row:
  - `fill_source = summary_fallback`, `fill_qty = fill_summary.fill_qty`, `fill_price = fill_summary.fill_vwap`.
- Legacy parquet null-key dedupe rule:
- for each dedupe key in `{record_id, uid, _spool_record_uid}`:
- dedupe only rows with non-empty key;
- preserve all rows where key is null/empty token (`'', none, null, nan`).

## Phase 31 Option 1 Medium-Risk Reconciliation Addendum (2026-03-01)

### 1) Deterministic spool record identity (retry-idempotent across append calls)
- Record UID payload (capture-time excluded):
  - `uid_payload := {"record_type": record_type, "row": row_without(captured_at_utc)}`
- UID formula:
  - `_spool_record_uid := sha1(json.dumps(uid_payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True))`
- Implementation path:
  - `execution/microstructure.py` (`_build_spool_records`)

### 2) Immediate-write vs prepared counters
- Prepared counters:
  - `orders_prepared := len(order_rows)`
  - `fills_prepared := len(fill_rows)`
- Immediate durable counters:
  - `fully_appended := (spool_records_appended == spool_records_total)`
  - `orders_written := orders_prepared if fully_appended else 0`
  - `fills_written := fills_prepared if fully_appended else 0`
- Intent:
  - prevent reporting immediate writes when append was buffered/contended/failed.
- Implementation path:
  - `execution/microstructure.py` (`append_execution_microstructure`)

### 3) Retry-buffer overflow contract (fail-closed)
- Overflow predicate:
  - `overflow := (projected_records > SPOOL_BUFFER_MAX_RECORDS) OR (projected_bytes > SPOOL_BUFFER_MAX_BYTES)`
- Overflow action:
  - do not partially enqueue retry batch,
  - emit `last_flush_error`,
  - raise `RuntimeError("telemetry spool retry buffer overflow: ...")`.
- Implementation path:
  - `execution/microstructure.py` (`_buffer_records_for_retry`, `_TelemetrySpooler.append`)

### 4) Shutdown durability gate (fail-closed if pending telemetry remains)
- Shutdown sequence:
  - set stop signal,
  - best-effort synchronous flush attempts until deadline,
  - if any of `{pending_bytes > 0, buffer_drop_count > 0, last_flush_error != none}` after deadline
    => raise `MicrostructureFlushError("telemetry spool shutdown fail-closed: ...")`.
- Intent:
  - remove silent buffered-data loss and sink-error suppression on shutdown.
- Implementation path:
  - `execution/microstructure.py` (`_TelemetrySpooler.stop`, `_shutdown_execution_microstructure_spoolers`)

### 5) Recovery anchor strictness for heartbeat classification
- Submit anchor:
  - `submit_sent_ts := submit_sent_ts || submitted_at || created_at || updated_at`
- Ack anchor (no submit/created fallback):
  - `broker_ack_ts := broker_ack_ts || ack_ts || updated_at`
- Result:
  - if ack anchor missing then `latency_ms_submit_to_ack = None` and heartbeat classification is `BLOCK(latency_missing)`.
- Implementation path:
  - `execution/microstructure.py` (`_resolve_latency_anchors`, `evaluate_heartbeat_freshness`)

### 6) Replay-ledger malformed-state contract + growth cap
- Malformed-line detection contract:
  - if malformed rows detected in replay ledger under lock:
  - `quarantine(malformed)` + `rewrite(valid_lines)` + reject current submit (`fail-closed`).
- Ledger growth cap:
  - `max_rows := env(TZ_EXECUTION_REPLAY_LEDGER_MAX_ROWS, default=50000)`
  - `valid_lines := tail(valid_lines, max_rows)` + rewrite + trim telemetry event.
- Replay lock budget:
  - `DEFAULT_EXECUTION_REPLAY_LOCK_TIMEOUT_MS := 25`
- Implementation path:
  - `execution/signed_envelope.py` (`assert_not_replayed_and_append_atomic`, `_resolve_replay_ledger_max_rows`)

## Stream 1 PiT Sprint Addendum (2026-03-01)

### 1) Dual-time PiT gate (`data/fundamentals.py`)
- Time axes:
  - `T_valid := release_date`
  - `T_knowledge := published_at`
  - `T_simulation := as_of_date` (timestamp precision retained)
- Gate invariant:
  - record is visible iff:
  - `T_knowledge <= T_simulation` and `T_valid <= T_simulation`
- Loader application:
  - `load_quarterly_fundamentals(...)`
  - `load_fundamentals_snapshot(...)`

### 2) Timestamp binding contract (`data/fundamentals.py`, `data/feature_store.py`)
- Binding token:
  - `token := HMAC_SHA256(secret, iso8601(T_simulation))`
- Validation:
  - `compare_digest(token, HMAC_SHA256(secret, iso8601(T_simulation)))`
- Strict mode:
  - `T0_STRICT_SIMULATION_TS_BINDING=1` => token required when `as_of_date` is supplied.
  - secret source:
  - `T0_SIMULATION_TS_BINDING_SECRET` or explicit arg.
- Feature-store integration:
  - strict-mode token is generated once at `close_wide.index[-1]`
  - token/secret are plumbed to:
  - `build_fundamentals_daily(...)`
  - `load_fundamentals_snapshot(...)`

### 3) Fallback valid-time masking (`data/fundamentals.py`)
- Fallback path builds matrices from `published_at` broadcasts.
- Reconciliation guard:
  - `valid_time_mask(date, permno) := release_date(date, permno) <= date`
  - all fallback matrices are masked by `valid_time_mask`.
- Quality gate:
  - `quality_pass := (roic > 0) AND (revenue_growth_yoy > 0) AND (0 <= age_days <= max_age_days)`.

### 4) Deterministic dedupe tie-break (`data/fundamentals.py`)
- Dedupe key remains:
  - `(permno, release_date, published_at)` keep latest.
- Deterministic tie-break for equal `ingested_at`:
  - `_row_hash := hash_pandas_object(sorted_row_columns)`
  - sort order:
  - `(permno, release_date, published_at, ingested_at, _row_hash)`
  - dedupe then drop `_row_hash`.

### 5) Yearly-union eradication to t-1 daily selector (`data/feature_store.py`)
- Universe anchor:
  - `anchor := normalize(start_date)` (or clamped `end_date`).
- Eligibility:
  - `date < anchor` (strict t-1, no same-day usage).
- Selector:
  - compute last tradable date `< anchor`,
  - rank by `dollar_volume = signal_price * volume` on that date,
  - choose `top yearly_top_n` by `(dollar_volume desc, permno asc)`.
- Result:
  - active selector path no longer uses full-year pre-calculated blocks.

## Stream 1 Option 1 Isolated High Backlog Reconciliation (2026-03-01)

### 1) Yearly-union as-of anchor contract (`data/feature_store.py`)
- Selector anchor:
  - `anchor_date := append_start_ts` when incremental universe refresh is active.
  - `anchor_date := start_date` otherwise.
- Liquidity cutoff:
  - annual-liquidity source rows must satisfy `date <= anchor_date`.
- Eligible union years:
  - primary set: `eligible_years = {y | y < year(anchor_date)}`
  - bootstrap fallback: `eligible_years = {year(anchor_date)}` only when no prior year is available.
- Selection:
  - for each `y in eligible_years`, choose top `yearly_top_n` by annual dollar volume, then union.
- Implementation path:
  - `data/feature_store.py` (`_top_liquid_permnos_yearly_union`, `run_build`)
  - tests:
    - `tests/test_feature_store.py::test_top_liquid_permnos_yearly_union_is_asof_anchored`
    - `tests/test_feature_store.py::test_top_liquid_permnos_yearly_union_excludes_same_day_spike`
    - `tests/test_feature_store.py::test_top_liquid_permnos_yearly_union_uses_patch_precedence_before_anchor`

### 2) Feature-spec fail-closed execution contract (`data/feature_store.py`)
- Missing context inputs:
  - `missing_inputs(spec) != empty => raise FeatureSpecExecutionError`.
- Missing fundamental dependencies:
  - for fundamental specs, let `generated = prior_spec_outputs`.
  - `missing_dep = {i in spec.inputs | i not in dependency_columns and i not in generated}`.
  - `missing_dep != empty => raise FeatureSpecExecutionError`.
- Runtime and post-processing failures:
  - `spec.func` exceptions must be wrapped as `FeatureSpecExecutionError`.
  - `result` type must satisfy `isinstance(result, pandas.DataFrame)`.
  - non-DataFrame or reindex failures must raise `FeatureSpecExecutionError`.
- Implementation path:
  - `data/feature_store.py` (`_execute_feature_specs`)
  - tests:
    - `tests/test_feature_store.py::test_execute_feature_specs_fails_closed_on_spec_exception`
    - `tests/test_feature_store.py::test_execute_feature_specs_fails_closed_on_non_dataframe_result`
    - `tests/test_feature_store.py::test_execute_feature_specs_fails_closed_on_missing_inputs`
    - `tests/test_feature_store.py::test_execute_feature_specs_fails_closed_on_missing_fundamental_dependencies`
    - `tests/test_feature_store.py::test_execute_feature_specs_allows_fundamental_inputs_from_prior_spec_outputs`

## Stream 5 Telemetry Constraint Reconciliation (2026-03-01)

### 1) Authoritative execution-receipt gate (`main_bot_orchestrator.py`)
- For any success-path receipt (`ok == True`), required authoritative fields are:
  - `filled_qty > 0`
  - `filled_avg_price > 0`
  - `execution_ts != ""`
- Acceptance formula:
  - `authoritative_ok := ok AND has(symbol, side, qty) AND has(filled_qty, filled_avg_price, execution_ts)`
- Fail-closed contract:
  - if `ok == True` but authoritative fields are missing:
  - trigger reconciliation polling via `get_order_by_client_order_id(client_order_id)`.
  - if reconciliation still lacks authoritative fields after poll budget:
  - raise `AmbiguousExecutionError` and abort acceptance.
- Applies to:
  - direct `ok=True` submit payloads,
  - `already exists` recovery path promoted to success.
- Implementation path:
  - `main_bot_orchestrator.py`:
    - `_normalize_execution_receipt_fields`
    - `_ok_true_result_missing_required_broker_fields`
    - `_poll_reconciliation_receipt`
    - `execute_orders_with_idempotent_retry`

### 2) Canonical execution timestamp resolution (`execution/broker_api.py`)
- Canonical resolver:
  - `execution_ts := execution_ts || fill_summary.first_fill_ts || min(partial_fills.fill_ts) || filled_at`
- Normalization rule:
  - `_normalize_submit_acceptance(...)` now injects `execution_ts` when resolvable from broker snapshot/fill telemetry.
- Implementation path:
  - `execution/broker_api.py`:
    - `_resolve_execution_ts`
    - `_normalize_submit_acceptance`

### 3) Regression coverage
- `tests/test_main_bot_orchestrator.py`:
  - sparse `ok=True` payload with symbol/side/qty but missing authoritative execution fields now raises `AmbiguousExecutionError` and polls reconciliation,
  - sparse `ok=True` payload reconciles to success when lookup returns definitive receipt,
  - sparse `already exists` recovery now also raises `AmbiguousExecutionError` when reconciliation is unavailable,
  - existing success-path doubles upgraded with `filled_qty`, `filled_avg_price`, `execution_ts`.
- `tests/test_execution_controls.py`:
  - broker submit result now asserts `execution_ts` derivation for:
    - activity-derived fill summary path,
    - snapshot fallback fill path.

## Stream 5 Sprint+1 Follow-Through (2026-03-01)

### 1) Strict success invariant (`main_bot_orchestrator.py`)
- Authoritative success formula:
  - `success := (ok == True)`
  - `AND (filled_qty > 0)`
  - `AND (filled_avg_price > 0)`
  - `AND (execution_ts parses as ISO-8601 with timezone)`
  - `AND (filled_qty <= order_qty)`
- Implementation path:
  - `_to_utc_execution_ts_or_none`
  - `_normalize_execution_receipt_fields`
  - `_execution_fill_qty_within_order_bounds`
  - `_ok_true_result_missing_required_broker_fields`

### 2) Ambiguity trap hardening (`main_bot_orchestrator.py`)
- Reconciliation lookup contract:
  - `lookup_result := timeout_guard(get_order_by_client_order_id, per_poll_timeout)`
  - `if timeout/exception: record issue tag and continue within poll budget`
  - `if budget exhausted without authoritative receipt: raise AmbiguousExecutionError(issue_tag)`
- Duplicate row deterministic fail-closed contract:
  - `dup_cid := {cid | count(batch_rows[cid]) > 1}`
  - `if cid in dup_cid: result.ok = False; result.error = duplicate_batch_result_cid`
- Implementation path:
  - `_poll_lookup_with_timeout`
  - `_poll_reconciliation_receipt`
  - `execute_orders_with_idempotent_retry` (duplicate CID pre-scan + fail-closed output)

### 3) Regression coverage
- `tests/test_main_bot_orchestrator.py`:
  - malformed `execution_ts` fail-closed ambiguity,
  - overfilled-qty bound fail-closed ambiguity,
  - duplicate-output-CID fail-closed determinism (both row orders),
  - reconciliation lookup timeout issue surfacing,
  - zero-poll-budget ambiguity.

## Round Update (2026-03-01) - Stream 5 Authoritative Receipt SAW Reconciliation (CID + Terminal Taxonomy)
- Status: Completed (SAW reviewer recheck PASS; no unresolved in-scope Critical/High).
- Added in this round:
  - `main_bot_orchestrator.py`:
    - success receipt gate now requires broker-origin `client_order_id` for all `ok=True` acceptance paths,
    - reconciliation remains mandatory for sparse success payloads and now also covers missing broker CID in direct `ok=True` paths,
    - terminal outcomes are now canonicalized with deterministic taxonomy:
      - normalized terminal `status`,
      - `terminal_reason` (`terminal_unfilled` or `terminal_partial_fill`),
      - canonical `error = <terminal_reason>:<status>`,
      - preserved passthrough diagnostics in `broker_error_raw`,
    - batch submit exceptions from `rebalancer.execute_orders(...)` are now fail-closed/retry-aware:
      - retry until `max_attempts`,
      - emit deterministic `retry_exhausted` with `last_error=batch_exception:<ExceptionType>` on exhaustion.
  - `tests/test_main_bot_orchestrator.py`:
    - added non-recovery sparse `ok=True` missing broker CID ambiguity regression,
    - added terminal status normalization + broker error preservation regression,
    - updated terminal fail-closed expectations to canonical terminal taxonomy fields,
    - added batch-exception retry recovery and retry-exhaustion regressions.
- Formula/contract lock:
  - `authoritative_ok := (ok == True) AND has(client_order_id, symbol, side, qty) AND (filled_qty > 0) AND (filled_avg_price > 0) AND (execution_ts is valid_iso8601_tz) AND (filled_qty <= order_qty)`.
  - `if authoritative_ok == False: poll_reconciliation(client_order_id)`.
  - `if reconciliation unavailable after budget: raise AmbiguousExecutionError(reconciliation_issue)`.
  - `terminal_reason := terminal_unfilled if effective_fill_qty <= 0 or invalid else terminal_partial_fill`.
  - `terminal_error := terminal_reason + ":" + normalized_terminal_status`.
  - `if execute_orders batch raises and attempt < max_attempts: retry; else fail_closed(error=retry_exhausted, last_error=batch_exception:<ExceptionType>)`.
- Verification:
  - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
  - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py` -> PASS (`196 passed`).
  - SAW reviewer final confirmations:
    - Reviewer A PASS,
    - Reviewer B PASS,
    - Reviewer C PASS.

## Phase 32 Step 4 Exception Taxonomy Split Addendum (2026-03-02)

### 1) Binary broker-exception taxonomy (`main_bot_orchestrator.py`)
- Canonical classes:
  - `TERMINAL`: hard business/validation/auth rejects (fail-closed now).
  - `TRANSIENT`: network/timeout/service/rate-limit errors (bounded retry).
- Classifier contract:
  - `exception_class := _classify_broker_exception(exc)` where `exception_class in {"TERMINAL","TRANSIENT"}`.
  - unknown exception patterns default to `TRANSIENT` (bounded retry safety).

### 2) Deterministic routing contract (`execute_orders_with_idempotent_retry`)
- Batch exception path:
  - `if TERMINAL -> error=FAILED_REJECTED, exception_class=TERMINAL, bypass retry loop`.
  - `if TRANSIENT -> bounded retry; on exhaustion error=retry_exhausted, exception_class=TRANSIENT`.
- Row-level broker-result path:
  - classify terminal/transient before retry token evaluation.
  - terminal precedence rule:
    - if classifier returns `TERMINAL`, fail closed immediately even when error text also contains retryable tokens.
  - `if non-retryable error text and terminal classification -> FAILED_REJECTED` (no raw free-form pass-through).
  - `retry_exhausted` outputs are emitted via one shared builder so canonical fields are stable across all transient exhaustion branches.

### 3) Canonical output schema
- Terminal fail-closed:
  - `{"ok":false,"error":"FAILED_REJECTED","exception_class":"TERMINAL","canonical_reason":...,"rejection_reason":...,"client_order_id":...,"attempt":...}`
- Transient exhausted:
  - `{"ok":false,"error":"retry_exhausted","exception_class":"TRANSIENT","canonical_reason":...,"last_error":...,"client_order_id":...,"attempt":...}`

### 4) Bounded zero-timeout lookup safety
- Reconciliation timeout guard:
  - `effective_timeout := max(timeout_seconds, 0.01)`
- Intent:
  - remove synchronous `timeout<=0` lookup execution path that could stall on hanging broker lookups.

## Phase 32 Step 1 (2026-03-02) - Reconciliation Timeout Soak and Thread Isolation

### 1) Cooperative cancellation semantics (`main_bot_orchestrator.py`)
- Lookup timeout wrapper now attempts cooperative cancellation when broker adapter exposes `cancel_event`.
- Canonical taxonomy:
  - `lookup_cancelled` when lookup raises `asyncio.CancelledError`,
  - `lookup_timeout:<seconds>s` when timed-out worker exits but does not emit explicit cancel/exception,
  - `lookup_timeout:<seconds>s:uncooperative` when worker remains alive beyond timeout path.

### 2) Sticky lookup issue precedence (`main_bot_orchestrator.py`)
- Reconciliation polling now preserves the highest-priority lookup issue across poll cycles.
- Contract:
  - once a `lookup_*` issue appears, later generic states (`reconciliation_receipt_unavailable`, `non_authoritative_reconciliation_receipt`) cannot overwrite forensic taxonomy.
  - `:uncooperative` timeout is terminal for the current reconciliation attempt to avoid spawning additional stuck lookup workers.

### 3) Dedicated reconciliation quarantine sink (`main_bot_orchestrator.py`)
- Added durable JSONL quarantine writer for lookup timeout/cancel/exception families only.
- Writer contract:
  - lock-serialized append via sidecar `.lock`,
  - low-level append write (`O_APPEND`) + `fsync`,
  - parent-dir fsync on first create where supported,
  - schema-stable payload with `schema_version=1`.

### 4) Synthetic chaos + isolation coverage (`tests/test_main_bot_orchestrator.py`)
- Added synthetic chaos broker with deterministic cancel-aware hanging lookup.
- Added regressions:
  - timeout path quarantines with `:uncooperative`,
  - cooperative cancellation path surfaces `lookup_cancelled` and quarantines deterministically,
  - mixed-poll precedence keeps `lookup_cancelled`,
  - blocked reconciliation lookup does not block telemetry spool append/flush,
  - concurrent quarantine writers remain lossless and parseable.

## Phase 35 Repaired `permno` Overlay Notes (2026-03-08)

### 1) Canonical repaired feature formulas
- `mom_12m`:
  - formula: `(adj_close_t / adj_close_t-252) - 1`
  - implemented in: `data/feature_derivation.py` (`derive_mom_12m`)
  - materialized by: `scripts/build_phase35_repaired_features.py`
- `realized_vol_21d`:
  - formula: `std(pct_change(adj_close), 21d) * sqrt(252)`
  - implemented in: `data/feature_derivation.py` (`derive_realized_vol_21d`)
  - materialized by: `scripts/build_phase35_repaired_features.py`
- `illiq_21d`:
  - formula: `mean(abs(daily_return) / dollar_volume, 21d) * 1e6`
  - where `dollar_volume = adj_close * volume`
  - implemented in: `data/feature_derivation.py` (`derive_illiq_21d`)
  - materialized by: `scripts/build_phase35_repaired_features.py`
- `quality_composite`:
  - explicit formula: `0.4 * roic + 0.3 * roe_q + 0.3 * revenue_growth_yoy`
  - implemented in: `data/feature_derivation.py` (`derive_quality_composite_from_panel`)
  - materialized by: `scripts/build_phase35_repaired_features.py`

### 2) Repaired validation contract
- Provenance nulls are treated as `missing`, not skipped.
- Price-derived factors are validated only on rows with the required raw inputs:
  - `mom_12m`: `adj_close`
  - `realized_vol_21d`: `adj_close`
  - `illiq_21d`: `adj_close` and non-zero `volume`
- Implemented in: `data/validation.py` (`summarize_derived_feature_missingness`, `validate_phase35_repaired_window`)

### 3) Attribution numeric-column contract
- `scripts/attribution_report.py` must exclude `*_source` and `score_valid` from numeric IC and attribution math.
- Only numeric factor columns should be pivoted into factor IC / attribution calculations.

### 4) Governed evidence windows
- Calibration: `2022-01-01` → `2023-06-30`
- Validation: `2023-07-01` → `2024-03-31`
- Holdout: `2024-04-01` → `2024-12-31`
- `2020-2021` are warmup only for the repaired Phase 35 rerun path.



## Phase 36 Robustness Contract Notes (2026-03-08)

### 1) Locked friction-stress formula
- explicit formula: `ic_net_estimated = ic_gross - ((cost_bps / 10000) * turnover_monthly * 12.0)`
- implemented in: `scripts/phase36_bundle_robustness_round.py` (`compute_friction_stress`)
- validated by: `scripts/validate_phase36_bundle_robustness_outputs.py`

### 2) Locked 20bps holdout fail-closed floor
- explicit rule: `kill_triggered = holdout_net_ic_at_20bps <= 0`
- implemented in: `scripts/phase36_bundle_robustness_round.py` (`compute_friction_stress`, `apply_majority_rubric`)
- validated by: `scripts/validate_phase36_bundle_robustness_outputs.py`, `tests/test_phase36_bundle_robustness_round.py`, `tests/test_validate_phase36_bundle_robustness_outputs.py`

### 3) Locked portfolio rubric
- explicit rule:
  - `Continue` if `continue_votes >= 3`
  - `Pause` if `pause_votes >= 3`
  - otherwise `Pivot`
- implemented in: `scripts/phase36_bundle_robustness_round.py` (`apply_majority_rubric`)
- evidence artifact: `data/processed/phase36_rule100/robustness/bundle_robustness_recommendation.json`

## Phase 38 Bounded Gate Contract Notes (2026-03-09)

### 1) Locked dual-gate formulas
- `active_days = count(governed trading days in the window where the latest in-window frozen method status is 'ready' or 'valid')`
- `eligible_days = count(governed trading days in the target window recovered from frozen equal_weight diagnostics)`
- `coverage_ratio = active_days / eligible_days`
- `method_gate_pass = (validation_active_days >= 252) and (validation_coverage_ratio >= 0.80) and (holdout_active_days >= 252) and (holdout_coverage_ratio >= 0.80)`
- `portfolio_gate_decision = Continue if continue_votes >= 2; Pause if pause_votes >= 2; otherwise Pivot`

### 2) Frozen execution reconstruction
- Daily governed calendar source: `data/processed/phase37_portfolio/portfolio_guardrail_diagnostics.csv` rows for `equal_weight`.
- Optimized-method state expansion: forward-fill each month's frozen `status` within the same governed window to the recovered daily calendar; do not cross window boundaries.
- Consistency check: `reconstructed_warmup_days == portfolio_method_comparison.warmup_days` for `inverse_vol_63d` and `capped_risk_budget`.

### 3) Evidence surface
- Bounded execution path: one-off `.venv` inline Python execution from the terminal using frozen artifacts only; no persisted Phase 38 execution script was added by contract.
- Evidence artifacts: `data/processed/phase38_gate/gate_diagnostics_delta.csv`, `data/processed/phase38_gate/gate_recommendation.json`.

## Phase 39 Reachability Policy Notes (2026-03-09)

### 1) Locked policy formulas
- `active_days_window = count(governed trading days in the window where the method is in a valid investable state)`
- `eligible_days_window = count(governed trading days available inside the governed window)`
- `coverage_ratio_window = active_days_window / eligible_days_window`
- `threshold_reachable = MIN_ACTIVE_DAYS_THRESHOLD <= min(eligible_days_validation, eligible_days_holdout)`
- `dual_gate_window_pass = (active_days_window >= MIN_ACTIVE_DAYS_THRESHOLD) and (coverage_ratio_window >= MIN_COVERAGE_RATIO_THRESHOLD)`
- `future_gate_proposal_allowed = threshold_reachable`
- `future_execution_authorized = threshold_reachable and explicit_future_governance_instruction`

### 2) Locked governance interpretation
- If `threshold_reachable = false`, the disposition is governance `Hold` before any threshold approval, worker guide, or execution proposal can advance.
- Impossible geometry is a policy/window-design issue, not a method-quality failure and not a reason to mutate frozen Phase 37/38 evidence.
- The dual gate family is preserved; Phase 39 does not rewrite the frozen `252 / 0.80` constants.

### 3) Evidence and implementation boundary
- Docs-only evidence surface: `docs/phase_brief/phase39-brief.md`, `docs/notes.md`, `docs/context/current_context.json`, `docs/context/current_context.md`, `docs/decision log.md`, `docs/lessonss.md`, `docs/saw_reports/saw_phase39_reachability_policy_20260309.md`.
- No `.py` implementation file is authorized in Phase 39; the pre-execution reachability screen is a governance policy contract only in this round.

## Phase 40 Geometry Remedy Notes

1. Reachability formula: threshold_reachable = MIN_ACTIVE_DAYS_THRESHOLD <= min(eligible_days_validation, eligible_days_holdout)
2. Remedy options: Method A (lower threshold - PRIMARY), Method B (redesign windows), Method C (redesign metric)
3. Planning anchor: Method A, no threshold value activated in Phase 40
4. Product targets: shadow_ship_target_phase = 48, capital_decision_target_phase >= 50
5. Boundaries: Docs-only, no execution token, no remedy execution

## Phase 41 Threshold Trade-Off Notes

1. Candidate set: `T = {180, 150, 126}` days under Method A only
2. Fixed dimension weights:
   - `w_auditability = 25`
   - `w_geometry = 30`
   - `w_dual_gate = 15`
   - `w_governance = 15`
   - `w_shadow_path = 15`
3. Ordinal scoring scale: `s_i(t) ∈ {1,2,3,4,5}` where `5` is strongest governance fit and `1` is unacceptable for current objectives
4. Weighted score formula:
   - `score(t) = (25*s_auditability(t) + 30*s_geometry(t) + 15*s_dual_gate(t) + 15*s_governance(t) + 15*s_shadow_path(t)) / 100`
5. Locked Phase 41 ordinal scores:
   - `score_components(180) = {auditability:5, geometry:2, dual_gate:5, governance:5, shadow_path:4}`
   - `score_components(150) = {auditability:4, geometry:4, dual_gate:5, governance:4, shadow_path:4}`
   - `score_components(126) = {auditability:3, geometry:5, dual_gate:5, governance:3, shadow_path:3}`
6. Ranked output:
   - `score(150) = 4.15`
   - `score(180) = 3.95`
   - `score(126) = 3.90`
   - ranked order = `150 > 180 > 126`
7. Governance interpretation:
   - ranked order is a CEO decision surface only
   - no threshold is enacted in Phase 41
   - threshold selection remains deferred to Phase 42 governance review
8. Implementation boundary:
   - no `.py` implementation file is authorized in Phase 41
   - no rerun or recomputation of frozen Phase 37/38 evidence is authorized in Phase 41

## Phase 42 Threshold Governance Notes

1. Governance-selected implementation target:
   - `MIN_ACTIVE_DAYS_THRESHOLD_target = 150`
   - `MIN_COVERAGE_RATIO_THRESHOLD = 0.80` (unchanged)
2. Selection interpretation:
   - `150` is selected as the balanced option under the sealed Phase 41 scorecard
   - `180` remains conservative fallback
   - `126` remains aggressive reserve option
3. Governance rationale:
   - `150` preserves the dual-gate family with materially stronger reachability margin than `180`
   - `150` avoids the higher governance and shadow-validation burden associated with `126`
4. Implementation boundary:
   - selected threshold is governance-locked for future planning only
   - code/constants remain unchanged until a later explicitly authorized implementation round
   - no rerun or recomputation of frozen Phase 37/38 evidence is authorized in Phase 42
   - no gate re-execution or execution token is authorized in Phase 42
5. Next-phase boundary:
   - Phase 43 is opened for implementation planning only
   - research quarantine and inherited hard blocks remain unchanged

## Phase 43 Implementation Planning Notes

1. Future authoritative constant owner:
   - `strategies/phase37_portfolio_registry.py`
   - planned registry constants:
     - `MIN_ACTIVE_DAYS_THRESHOLD = 150`
     - `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
2. Future consumer rule:
   - `scripts/phase38_gate_execution.py` must import the gate constants from `strategies/phase37_portfolio_registry.py`
   - runtime code may not hardcode `150` or `0.80` outside the registry
3. Future gate formulas (implementation target only; not enacted in Phase 43):
   - `dual_gate_window_pass = (active_days_window >= MIN_ACTIVE_DAYS_THRESHOLD) and (coverage_ratio_window >= MIN_COVERAGE_RATIO_THRESHOLD)`
   - `method_gate_pass = dual_gate_window_pass_validation and dual_gate_window_pass_holdout`
4. Future validation path (post-authorization only):
   - targeted constant propagation:
     - `.venv\Scripts\python -m pytest tests\test_phase37_portfolio_registry.py tests\test_phase38_gate_execution.py -q`
   - bounded rerun:
     - `.venv\Scripts\python scripts\phase38_gate_execution.py`
   - bounded output validator:
     - `.venv\Scripts\python scripts\validate_phase38_gate_outputs.py`
5. Planning boundary:
   - Phase 43 seals the implementation contract only
   - Phase 44 reviews the contract before any later implementation authorization
   - Phase 37 and Phase 38 evidence remain frozen throughout Phase 43

## Phase 45 Implementation Completion Notes

1. Bounded implementation enactment:
   - Registry constants enacted in `strategies/phase37_portfolio_registry.py`:
     - `MIN_ACTIVE_DAYS_THRESHOLD = 150`
     - `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
   - Gate execution script implemented: `scripts/phase38_gate_execution.py`
   - Gate output validator implemented: `scripts/validate_phase38_gate_outputs.py`
   - Targeted tests added for registry ownership and gate propagation
2. Gate execution results (150/0.80 thresholds):
   - Portfolio gate decision: **Pause**
   - Vote counts: Continue=0, Pause=3, Pivot=0
   - All three approved methods (equal_weight, inverse_vol_63d, capped_risk_budget) failed dual-gate thresholds
   - Validation window: 390 active days, 69.5% coverage (passes 150 active days, fails 80% coverage)
   - Holdout window: 378 active days, 66.0% coverage (passes 150 active days, fails 80% coverage)
3. Bounded outputs regenerated:
   - `data/processed/phase38_gate/gate_diagnostics_delta.csv`
   - `data/processed/phase38_gate/gate_recommendation.json`
4. Implementation scope discipline:
   - Write surface limited to authorized files only
   - No production or shadow deployment
   - No rerun outside bounded Phase 38 gate path
   - Frozen Phase 37 evidence preserved
5. Next-phase boundary:
   - Phase 45 implementation complete
   - Phase 46 opens for governance review of gate results
   - Research quarantine and inherited hard blocks remain unchanged

## Phase 47 Coverage-Ratio Remedy Notes

1. Locked planning path:
   - coverage ratio is the sole in-scope problem
   - `Method A` is the only active remedy family in Phase 47
   - future policy shape remains one common coverage floor across validation and holdout
   - any later evidence refresh is limited to one narrow bounded rerun against frozen Phase 37 / Phase 45 evidence
2. Accepted packet constants and evidence:
   - `MIN_ACTIVE_DAYS_THRESHOLD = 150`
   - `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
   - validation coverage = `0.6952`
   - holdout coverage = `0.6597`
   - `min_current_coverage = min(0.6952, 0.6597) = 0.6597`
3. Candidate coverage-floor set carried forward for later governance:
   - `C = {0.65, 0.60, 0.55}`
4. Coverage-margin formula:
   - `coverage_margin(c) = min_current_coverage - c`
5. Candidate margins from the accepted packet:
   - `coverage_margin(0.65) = 0.0097`
   - `coverage_margin(0.60) = 0.0597`
   - `coverage_margin(0.55) = 0.1097`
6. Planning interpretation:
   - `0.65` = conservative near-pass option
   - `0.60` = balanced option
   - `0.55` = aggressive reserve option
7. Boundary:
   - no coverage floor is selected in Phase 47
   - no coverage floor is enacted in Phase 47
   - no `.py` implementation file is authorized in Phase 47

## Phase 47 Coverage-Floor Selection Notes

1. Selected policy constant:
   - `MIN_ACTIVE_DAYS_THRESHOLD = 150`
   - `MIN_COVERAGE_RATIO_THRESHOLD = 0.65`
2. Selection formula:
   - `coverage_margin(c) = min_current_coverage - c`
   - `min_current_coverage = min(0.6952, 0.6597) = 0.6597`
3. Decision rationale:
   - `coverage_margin(0.65) = 0.0097` → selected as the narrow conservative pass floor
   - `coverage_margin(0.60) = 0.0597` → feasible but looser than required
   - `coverage_margin(0.55) = 0.1097` → widest margin with the highest dilution risk
4. Governance interpretation:
   - `0.65` is selected in Phase 47
   - enactment is deferred to the bounded Phase 48 packet
   - active-days remedy remains closed

## Phase 48 Bounded Enactment Notes

1. Authoritative Python ownership:
   - constant owner: `strategies/phase37_portfolio_registry.py`
   - runtime gate consumer: `scripts/phase38_gate_execution.py`
   - bounded output validator: `scripts/validate_phase38_gate_outputs.py`
2. Runtime formulas:
   - `gate_pass(window) = (active_days(window) >= 150) AND (coverage_ratio(window) >= 0.65)`
   - `window_regime_days(window, regime) = max(n_days)` across duplicate sleeve rows for the same `(window, regime)`; if duplicate rows disagree on `n_days`, fail closed
   - `active_days(window) = SUM(window_regime_days(window, regime))` for `regime in {GREEN, AMBER}`
   - `total_days(window) = SUM(window_regime_days(window, regime))` for all regimes
   - `coverage_ratio(window) = active_days(window) / total_days(window)`
   - portfolio disposition remains `Pause` on any governed window miss
3. Bounded output surface:
   - `data/processed/phase38_gate/gate_diagnostics_delta.csv`
   - `data/processed/phase38_gate/gate_recommendation.json`
4. Corrected Phase 48 rerun result:
   - validation = `130` active days, `0.6952` coverage
   - holdout = `126` active days, `0.6597` coverage
   - coverage clears `0.65`, active days fail `150`
   - corrected packet = `Pause`
5. Corrective note:
   - an earlier interim `Continue` was withdrawn after SAW found duplicated sleeve-row day counts were being summed as distinct governed days
6. Hard blocks preserved:
   - no production or shadow deployment
   - no `permno` migration
   - no governed `10` bps rewrite
   - no new sleeves
   - no Sovereign cartridge integration inside the bounded gate packet

## Phase 49 Shadow-Evidence Integrity Notes

1. Readiness formulas:
   - `shadow_capture_day_count = count(distinct artifact_trade_date)`
   - `shadow_capture_window_ok = (min(artifact_trade_date) >= approved_window_start) AND (max(artifact_trade_date) <= approved_window_end)`
   - `shadow_capture_source_ok = scanner_outputs_from_runtime AND c3_deltas_from_day_specific_telemetry AND no_placeholder_synthesis`
   - `shadow_capture_ready = (shadow_capture_day_count >= 5) AND shadow_capture_window_ok AND shadow_capture_source_ok`
2. Current repository state on 2026-03-11:
   - `scripts/collect_shadow_evidence.py` writes all five day files in a single run
   - `collect_daily_scanner_output()` emits synthetic ticker rows rather than runtime-captured scanner output
   - `collect_c3_delta_snapshot()` selects the latest available telemetry event, so day files are relabeled snapshots rather than day-specific captures
3. Phase boundary:
   - Phase 49 is docs-only reconciliation
   - Phase 50 paper-curve remains blocked until `shadow_capture_ready = True` or governance explicitly accepts demo-only evidence
4. Source paths:
   - `scripts/collect_shadow_evidence.py`
   - `data/shadow_evidence/*.json`
   - `data/telemetry/simulated_routing_intents.log`

## Phase 50 Shadow-Ship Readiness Notes

1. Authoritative Python ownership:
   - paper-curve generator: `scripts/run_phase50_paper_curve.py`
   - paper-only dashboard surface: `views/elite_sovereign_view.py`
2. Demo-mode paper formulas:
   - `target_weight_i = sovereign_score_i / sum_j(sovereign_score_j)`
   - `signal_edge_i = demand_i + pricing_i + margin_i - supply_i`
   - `demo_return_i = clip((0.002 * signal_edge_i) + (0.0001 * hf_scalar_i) + regime_bias_i, -0.02, 0.02)`
   - `regime_bias_i = 0.0004 if regime contains "Super Cycle", 0.0001 if regime contains "Turnaround", else 0.0`
   - `day1_slippage_bps = mean(vol_constraint_i) * 50`
   - `active_days_progress_to_threshold = active_days_observed / 150`
3. Engine path:
   - `core.engine.run_simulation` remains the source of truth for `gross_ret`, `net_ret`, `turnover`, and `cost`
   - `equity_t = cumprod(1 + net_ret_t)`
4. Bounded output surface:
   - `data/processed/phase50_shadow_ship/paper_curve_day1.csv`
   - `data/processed/phase50_shadow_ship/paper_curve_positions_day1.csv`
   - `data/processed/phase50_shadow_ship/telemetry_day1.json`
   - `data/processed/phase50_shadow_ship/gate_recommendation.json`
   - compatibility mirrors:
     - `data/shadow_evidence/paper_curve_day1.csv`
     - `data/shadow_evidence/telemetry_day1.json`
     - `data/processed/phase50_gate/gate_recommendation.json`
   - `data/telemetry/phase50_paper_curve_events.jsonl`
   - canonical Phase 50 runtime reads stay on `data/processed/phase50_shadow_ship/`; compatibility mirrors exist only to satisfy CEO memo / handoff path contracts
5. Governance rule:
   - workers may not unilaterally open new phases; each phase opening requires explicit CEO sign-off in `docs/decision log.md`

## Phase 50 Final Gate Aggregation Notes

1. Final gate package artifacts:
   - full curve snapshot: `data/processed/phase50_shadow_ship/phase50_curve_full_20260410.csv`
   - aggregated telemetry: `data/processed/phase50_shadow_ship/phase50_aggregated_telemetry_20260410.json`
   - event-log snapshot: `data/processed/phase50_shadow_ship/phase50_event_log_full_20260410.jsonl`
2. Final gate aggregation formulas used in the accelerated package:
   - `cumulative_equity_factor = equity_day30`
   - `cumulative_return_pct = cumulative_equity_factor - 1`
   - `average_turnover = mean(turnover_days1_30)`
   - `stability_score = 1 - min(std(net_ret_days1_30) / max(abs(mean(net_ret_days1_30)), 1e-12), 1.0)`
3. Runtime source of truth:
   - `scripts/run_phase50_paper_curve.py` remains the only generator for the day-indexed curve and telemetry
   - the accelerated final package reuses those day-indexed outputs; it does not introduce a new simulation model

## Sovereign Shipping State Notes (2026-04-10)

### 1) Selector and routing state formulas
- `production_default_selector = "sovereign"`
- `governed_intent_valid = selector == "sovereign" and intent_payload_complete and audit_fields_present`
- `live_route_allowed = governed_intent_valid and live_break_glass_enabled and risk_interceptor_pass`
- `route_mode = "live" if live_route_allowed else "paper_fallback"`

### 2) Governance state changes
- `docs/handover/sovereign_promotion_package_20260313.md` is now the canonical live artifact rather than a contingent draft.
- Live-routing surfaces are permitted only through the existing governed execution path (`main_bot_orchestrator.py` -> `execution/rebalancer.py` -> `execution/risk_interceptor.py` -> `execution/broker_api.py`).
- Paper fallback remains mandatory whenever any live gate fails.
- Comparator and telemetry lineage remain part of the live audit trail; production unlock does not erase baseline evidence requirements.

### 3) Phase 51 design-state change
- `docs/phase_brief/phase51-factor-algebra-design.md` is now an implementation-authorized design starting point.
- The design brief remains a design artifact, not a source-of-truth runtime spec for executed production behavior.

## Live-Market Validation Round Criteria Notes

### 1) Entry and path lock
- Governed live-routing path remains:
  - `main_bot_orchestrator.py` -> `execution/rebalancer.py` -> `execution/risk_interceptor.py` -> `execution/broker_api.py`
- Validation mode token:
  - `validation_mode = "micro_capital_pilot"`
- Shadow comparator requirement:
  - same-window, same-cost, same `engine.run_simulation` path vs latest governed C3 baseline

### 2) Explicit formulas
- `telemetry_completeness = complete_lineage_orders / total_submitted_orders`
- `cash_drift = abs(local_cash_eod - broker_cash_eod)`
- `position_drift = max_symbol(abs(local_qty_eod - broker_qty_eod))`
- `slippage_deterioration_bps = live_median_adverse_slippage_bps - 7.5`
- `holdings_overlap = |live_symbols ∩ shadow_symbols| / max(1, |shadow_symbols|)`
- `gross_exposure_delta = abs(live_gross_exposure - shadow_gross_exposure)`
- `turnover_delta_abs = abs(live_turnover - shadow_turnover)`
- `turnover_delta_rel = turnover_delta_abs / max(abs(shadow_turnover), 1e-12)`
- `validation_round_pass = all(CHK_LMV_01..CHK_LMV_11) and no_rollback_trigger`

### 3) Runtime code loci
- Intent and authoritative execution result handling:
  - `main_bot_orchestrator.py`
- Batch normalization, routing, and risk-block persistence:
  - `execution/rebalancer.py`
- Projection, VIX kill switch, sector/single-name/VAR checks:
  - `execution/risk_interceptor.py`
- Fill aggregation, slippage, latency, heartbeat, and durable telemetry sinks:
  - `execution/microstructure.py`

### 4) Truthfulness boundary
- The current raw runtime path emits order/fill telemetry and slippage only when `arrival_price` context exists.
- The current raw runtime path does **not** by itself emit:
  - end-of-day cash/position reconciliation summaries
  - live-vs-shadow holdings overlap
  - gross-exposure delta
  - turnover delta
  - same-window C3 delta summaries for a live round
- Those checks therefore require a dedicated validation summarizer/reconciliation layer before a micro-capital live-market validation round can be authorized.

### 5) Artifact contract
- Raw telemetry remains in:
  - `data/processed/execution_microstructure.parquet`
  - `data/processed/execution_microstructure_fills.parquet`
  - `data/processed/execution_microstructure.duckdb`
- Future round summaries should live under:
  - `data/processed/live_market_validation/<round_id>/`

## Phase 57 Corporate Actions Formula Notes

1. Bounded Corporate Actions event proxy:
   - `corp_action_yield_t = total_ret_t - ((raw_close_t / raw_close_{t-1}) - 1)`
   - source path:
     - `scripts/phase57_corporate_actions_runner.py` (`load_corporate_action_frame`)
2. Eligible denominator family:
   - `eligible_t = 1[(quality_pass_t = 1) and (adv_usd_t >= 5_000_000) and (0.005 <= corp_action_yield_t <= 0.25)]`
   - `adv_usd_t = mean(raw_close_t * volume_t over 20 trading days by permno)`
   - source path:
     - `scripts/phase57_corporate_actions_runner.py` (`load_corporate_action_frame`, `select_corporate_action_candidates`)
3. Confirmation family:
   - `value_rank_pct_t = rank_pct(capital_cycle_score_t by date, ascending)`
   - `confirmed_t = 1[value_rank_pct_t >= 0.60]`
   - source path:
     - `scripts/phase57_corporate_actions_runner.py` (`select_corporate_action_candidates`)
4. Portfolio construction:
   - `target_weight_{t,i} = 1 / N_t` for confirmed names on event day `t`
   - non-event dates are explicitly reindexed to `0` target weight across the full trading calendar
   - executed exposure remains next-day because `core.engine.run_simulation` applies `shift(1)`
   - source paths:
     - `scripts/phase57_corporate_actions_runner.py` (`build_corporate_action_target_weights`)
     - `core/engine.py` (`run_simulation`)
5. Same-window / same-cost comparator discipline:
   - bounded Phase 57 packet window = `2015-01-01 -> 2022-12-31`
   - `cost_bps = 5.0`
   - locked comparator baseline = `data/processed/phase54_core_sleeve_summary.json` with `baseline_config_id = C3_LEAKY_INTEGRATOR_V1`
   - delta metrics:
     - `sharpe_delta = sharpe_phase57 - sharpe_c3`
     - `cagr_delta = cagr_phase57 - cagr_c3`
     - `turnover_ratio_phase57_vs_c3 = turnover_annual_phase57 / turnover_annual_c3`
     - `max_dd_delta = max_dd_phase57 - max_dd_c3`
     - `ulcer_delta = ulcer_phase57 - ulcer_c3`
   - source path:
     - `scripts/phase57_corporate_actions_runner.py` (`load_baseline_summary`, `build_delta_frame`)
6. Phase 57 closeout governance predicate:
   - `phase57_promotion_ready = 1[(same_window_same_cost_same_engine = 1) and (sharpe_delta >= 0) and (cagr_delta >= 0)]`
   - `phase57_closeout_no_promotion = 1[phase57_promotion_ready = 0]`
   - source paths:
     - `docs/decision log.md` (`D-321`, `D-322`)
     - `docs/phase_brief/phase57-brief.md`

## Phase 58 Governance Layer Formula Notes

1. Comparable event-family scope:
   - `event_family = {phase56_event_pead, phase57_event_corporate_actions}`
   - `allocator_reference = phase55 summary only` with `reference_only = true`
   - source path:
     - `scripts/phase58_governance_runner.py`
2. Same-window / same-cost / same-engine packet discipline:
   - `window = 2015-01-01 -> 2022-12-31`
   - `cost_bps = 5.0`
   - `same_window_same_cost_same_engine = 1[(all included event sleeves share the window, cost, and core.engine.run_simulation path)]`
   - source path:
     - `scripts/phase58_governance_runner.py`
3. Family trial-pool normalization:
   - `event_return_matrix_t = outer_join(net_ret_phase56_t, net_ret_phase57_t).fillna(0)`
   - `N_eff = effective_number_of_trials(event_return_matrix)`
   - `sr_estimates = {safe_sharpe(sleeve_i)}`
   - `dsr_i = deflated_sharpe_ratio(returns_i, sr_estimates, N_eff)`
   - `family_spa_p, family_wrc_p = spa_wrc_pvalues(event_return_matrix)`
   - source paths:
     - `scripts/phase58_governance_runner.py`
     - `utils/statistics.py`
     - `utils/spa.py`
4. Comparator deltas vs the locked C3 baseline:
   - `sharpe_delta_i = sharpe_i - sharpe_c3`
   - `cagr_delta_i = cagr_i - cagr_c3`
   - `turnover_ratio_i = turnover_annual_i / turnover_annual_c3`
   - `max_dd_delta_i = max_dd_i - max_dd_c3`
   - `ulcer_delta_i = ulcer_i - ulcer_c3`
   - source path:
     - `scripts/phase58_governance_runner.py` (`build_delta_row`)
5. Explicit bounded-packet non-applicability:
   - `pbo_applicable_event_family = 0`
   - reason: `single-packet event sleeves do not expose a CSCV search lattice in this bounded packet`
   - source path:
     - `scripts/phase58_governance_runner.py`
6. Review / hold predicate:
   - `phase58_review_hold = 1[(event_family_spa_p >= 0.05) or (event_family_wrc_p >= 0.05) or any(sharpe_delta_i < 0) or any(cagr_delta_i < 0)]`
   - source path:
     - `scripts/phase58_governance_runner.py` (`build_review_hold_reasons`)

## Phase 59 Shadow Portfolio Formula Notes

1. Phase 55-governed research-variant selector:
   - `selected_variant = argmax(selection_count, median_outer_test_sharpe, variant_id_ascending)`
   - input surface: `data/processed/phase55_allocator_cpcv_evidence.json::fold_results`
   - source path:
     - `data/phase59_shadow_portfolio.py` (`select_phase55_variant`)
2. Research-side Shadow NAV surface:
   - `research_shadow_ret_t = allocator_state(period_return_{selected_variant,t})`
   - `research_shadow_ret_t = 0` on business dates in `2015-01-01 -> 2022-12-31` where the selected variant has no observed row
   - `research_shadow_equity_t = cumprod(1 + research_shadow_ret_t)`
   - source path:
     - `data/phase59_shadow_portfolio.py` (`_build_research_surface`)
3. Research-side comparator deltas vs locked C3 baseline:
   - `sharpe_delta = sharpe_shadow - sharpe_c3`
   - `cagr_delta = cagr_shadow - cagr_c3`
   - `max_dd_delta = max_dd_shadow - max_dd_c3`
   - `ulcer_delta = ulcer_shadow - ulcer_c3`
   - source path:
     - `data/phase59_shadow_portfolio.py` (`_build_research_delta_row`)
4. Reference-only alert contract:
   - `holdings_overlap = |shadow_latest_tickers ∩ core_sample_selected_tickers| / max(1, |shadow_latest_tickers|)`
   - `gross_exposure_delta = abs(core_gross_exposure_latest - shadow_gross_exposure_latest)`
   - `turnover_delta_abs = abs(turnover_delta_vs_c3_phase50)`
   - `turnover_delta_rel = turnover_delta_abs / max(abs(shadow_average_turnover), 1e-12)`
   - source path:
     - `data/phase59_shadow_portfolio.py` (`_build_shadow_reference_surface`)
5. Review / hold predicate:
   - `phase59_review_hold = 1[(research_sharpe_delta < 0) or (research_cagr_delta < 0) or (shadow_reference_alert_level != "GREEN")]`
   - source path:
     - `data/phase59_shadow_portfolio.py` (`build_phase59_packet`)
