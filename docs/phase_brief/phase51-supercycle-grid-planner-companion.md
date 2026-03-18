# Phase 51 Week 2 - Grid Search Planner (Companion Note - Docs-Only)

**Status**: COMPANION PLANNING NOTE (historical planning reference; runtime now enabled in bounded scope)
**Runtime Authorization**: SUPERSEDED IN BOUNDED SCOPE BY `D-274` FOR THE SUPERCYCLE SCORER + GRID HARNESS
**Current Governed State**: Phase 50 is complete and shipped; use `docs/phase_brief/phase50-brief.md` as the historical closeout record and `docs/phase_brief/phase51-supercycle-signal-brief.md` / `docs/phase_brief/phase51-factor-algebra-design.md` as the active Phase 51 sources of truth
**Owner**: Codex -> User handoff
**Boundaries**: `docs/` only. No code, no tests, no execution, no data outputs.
**Authority**: Historical `D-267` planning hold, superseded in bounded runtime scope by `D-274`

---

## Cross-Reference

This companion note extends the planning surface defined in:
- `docs/phase_brief/phase51-factor-algebra-design.md:6` - canonical Phase 51 design doc
- `docs/decision log.md:5024` - existing `D-267` docs-only planning hold

This note does not supersede the canonical Phase 51 planning draft. It records the bounded optimizer-planning surface that later informed the `D-274` runtime slice.

---

## GridConfig Specification

**Parameter Space** (`5 x 5 x 3 x 3 = 225` combinations):

GridConfig:
- `power_law_exponents`: `[2.0, 2.5, 3.0, 3.5, 4.0]`
- `gravity_multipliers`: `[10.0, 12.0, 15.0, 18.0, 20.0]`
- `r2_thresholds`: `[0.85, 0.90, 0.95]`
- `convexity_thresholds`: `[1.3, 1.5, 1.7]`

**Rationale**: Bailey et al. (2015) bounded grid plus strict validation reduces overfitting and keeps trial count controlled.

---

## Training Windows

**Cycles** (keep `2008` and `2020` reserved for future validation):

1. **euro_crisis**: `2011-01-01` to `2012-12-31` - Euro crisis recovery
2. **china_devaluation**: `2015-01-01` to `2016-12-31` - China devaluation plus oil crash
3. **trade_war**: `2018-01-01` to `2019-12-31` - Fed tightening plus trade war

**Tickers** (8 semiconductors):
- `10107`: `MU` (Micron)
- `11703`: `LRCX` (Lam Research)
- `10795`: `AMAT` (Applied Materials)
- `14593`: `NVDA` (NVIDIA)
- `10730`: `AMD` (AMD)
- `11081`: `KLAC` (KLA Corp)
- `12490`: `TER` (Teradyne)
- `11850`: `MRVL` (Marvell)

---

## High-Level Pseudocode

### `run_single_backtest`

Input: `permno`, `ticker`, `window`, `SupercycleConfig`

Process:
1. Load PIT-safe fundamentals (`sales_accel_q`, `delta_revenue_inventory`, `gm_accel_q`, `operating_margin_delta_q`)
2. Load historical prices (`adj_close`)
3. Merge as-of (`fundamentals -> prices`, backward direction)
4. For each date:
   - build snapshot dict
   - call `calculate_alpha_quad_score(snapshot, config)`
   - extract `score_100` signal
5. Generate strategy returns (`signal.shift(1) * price_returns`)
6. Calculate metrics:
   - Sharpe ratio (annualized)
   - Max drawdown
   - Total return
   - Num trades
   - Avg hold days
   - Win rate

Output: `Dict[str, float]` with metrics

### `run_grid_search`

Input: `GridConfig`, `max_workers`

Process:
1. Generate all 225 parameter combinations (`itertools.product`)
2. For each combination:
   - create `SupercycleConfig(power, gravity, r2, convex)`
   - for each training window:
     - for each ticker:
       - call `run_single_backtest(permno, ticker, window, config)`
     - append result to list
3. Convert results to DataFrame (`5,400` rows)

Output: DataFrame with columns:
`power_law_exponent`, `gravity_multiplier`, `r2_threshold`, `convexity_threshold`, `ticker`, `window_name`, `sharpe_ratio`, `max_drawdown`, `total_return`, `num_trades`, `avg_hold_days`, `win_rate`

### `aggregate_grid_results`

Input: `results_df` (`5,400` rows)

Process:
1. Group by `power_law_exponent`, `gravity_multiplier`, `r2_threshold`, `convexity_threshold`
2. Aggregate:
   - `mean_sharpe = mean(sharpe_ratio)`
   - `std_sharpe = std(sharpe_ratio)`
   - `mean_max_dd = mean(max_drawdown)`
   - `mean_total_return = mean(total_return)`
   - `total_trades = sum(num_trades)`
   - `mean_win_rate = mean(win_rate)`
3. Calculate success rates:
   - `ticker_success_rate = % of tickers with Sharpe > 0.5`
   - `window_success_rate = % of windows with Sharpe > 0.5`
4. Sort by `mean_sharpe` descending

Output: DataFrame with `225` rows (one row per parameter combination)

### `generate_survivor_report`

Input: `aggregated_results` (`225` rows), `top_n = 3`

Process:
1. Apply filters:
   - `mean_sharpe > 0.8`
   - `ticker_success_rate > 0.75` (`6/8` tickers)
   - `window_success_rate > 0.66` (`2/3` windows)
   - `mean_max_dd > -0.25`
2. Sort by `mean_sharpe` descending
3. Take top `N` rows
4. Add `rank` column

Output: DataFrame with top-3 survivors

---

## Week 2 Acceptance Gates (W2-01 to W2-05)

**Originally deferred under `D-267`; now executable in bounded scope under `D-274`**

- **W2-01**: Grid harness exists at `backtests/optimize_supercycle_grid.py`
- **W2-02**: Test coverage at `tests/test_optimize_supercycle_grid.py` passes
- **W2-03**: Training run completes on `2011/2015/2018` cycles (`8` tickers)
- **W2-04**: Survivor report emits top-3 parameter sets with metrics
- **W2-05**: Evidence note plus lesson entry in `docs/lessonss.md`

---

## Evidence Note Template (Future)

Week 2 Evidence (`YYYY-MM-DD`)

Training Execution: `225`-combo grid search completed on `2011/2015/2018` cycles across `8` semiconductor tickers.

Raw Results: `5,400` backtest runs (`225 combos x 3 windows x 8 tickers`)

Survivor Report: Top-3 parameter sets identified

```text
Rank  Power  Gravity  R      Convexity  MeanSharpe  MeanMaxDD  TickerSuccess  WindowSuccess
1     [TBD]  [TBD]    [TBD]  [TBD]      [TBD]       [TBD]      [TBD]%         [TBD]%
2     [TBD]  [TBD]    [TBD]  [TBD]      [TBD]       [TBD]      [TBD]%         [TBD]%
3     [TBD]  [TBD]    [TBD]  [TBD]      [TBD]       [TBD]      [TBD]%         [TBD]%
```

Acceptance Criteria:
- Mean Sharpe `> 0.8` across all survivors
- Ticker success rate `> 75%` (`6/8` tickers minimum)
- Window success rate `> 66%` (`2/3` windows minimum)
- Mean max drawdown `> -25%`

Next Phase: Week 3 validation on `2008/2020` crisis periods

Artifacts (future only):
- `data/processed/phase51_grid/grid_search_raw_results.csv`
- `data/processed/phase51_grid/grid_search_aggregated.csv`
- `data/processed/phase51_grid/survivor_report_top3.csv`

---

## Lesson Entry Placeholder (Future)

| Date | Scope | Mistake/Miss | Root Cause | Fix Applied | Guardrail | Evidence |
|---|---|---|---|---|---|---|
| YYYY-MM-DD | Phase 51 Week 2 | Grid search on 225 combos completed | Bounded to 2011/2015/2018 training only | Top-3 survivors identified via multi-metric filter | Always separate training from validation to avoid overfitting | `grid_search_aggregated.csv`, `survivor_report_top3.csv` |

---

## Historical Runtime Block

**CRITICAL NOTICE**

Under the original `D-267` governance state, all runtime implementation (`code`, `tests`, `execution`, `data outputs`) was blocked until final CEO sign-off closed the active Phase 50 runway.

**Current Governed State**: Phase 50 runway remains active; consult `docs/phase_brief/phase50-brief.md` for the current approved runway day and stage.

**Superseding Authorization**: `D-274` now authorizes the bounded scorer/grid runtime slice in parallel with Phase 50

**Originally Blocked Artifacts**:
- `backtests/optimize_supercycle_grid.py` - deferred / out-of-boundary
- `tests/test_optimize_supercycle_grid.py` - deferred / out-of-boundary
- `data/processed/phase51_grid/*.csv` - deferred / out-of-boundary
- Phase 51 SAW runtime closeout report - deferred / out-of-boundary

**Planning Artifacts Still Relevant**:
- this companion planning note
- cross-reference to `docs/phase_brief/phase51-factor-algebra-design.md:6`
- research notes and future placeholders inside docs

**Rationale**: This historical block preserved governance while Phase 50 was still the only authorized runtime. `D-274` now reopens only the bounded scorer/grid slice, not the entire Phase 51 surface.

**Rollback Note**: The prior supercycle runtime surface was rolled back per `docs/saw_reports/saw_phase50_day13_runtime_closeout_20260324.md:69` and `docs/saw_reports/saw_phase50_day13_runtime_closeout_20260324.md:76`.

---

## Dependencies (Conceptual Only - Mapped to Current Repo Interfaces)

**Future data/interface candidates when runtime is authorized**:
- `data/fundamentals.py:351` - `load_quarterly_fundamentals(...)`
- `data/fundamentals.py:451` - `load_fundamentals_snapshot(...)`
- `data/fundamentals.py:985` - `build_fundamentals_daily(...)`
- `data/feature_store.py:1578` - `_load_prices_long(...)`
- `backtests/verify_phase15_alpha_walkforward.py:125` - `_load_price_series(...)`
- `backtests/verify_phase15_alpha_walkforward.py:221` - `_load_prices_matrix(...)`

**Deferred / out-of-boundary until Phase 50 gate passes**:
- any supercycle-specific strategy module such as `strategies/supercycle_signal.py`
- any `calculate_alpha_quad_score(...)` runtime surface
- any new optimizer harness, tests, or result artifacts

Actual implementation, if later authorized, must bind to the current repo interfaces that exist at that time rather than assuming deleted Week 1 artifacts.

---

## Next Actions (Post Final Phase 50 Gate)

1. Implement `backtests/optimize_supercycle_grid.py` per this pseudocode
2. Add test coverage at `tests/test_optimize_supercycle_grid.py`
3. Execute `225`-combo grid search (`5,400` backtests)
4. Generate survivor report (top-3 parameter sets)
5. Document evidence plus lesson entry
6. Run SAW closure review for the authorized implementation round

**Estimated Duration**: `5` days after explicit runtime authorization

---

**Status**: COMPANION PLANNING NOTE COMPLETE; historical block superseded by bounded `D-274` runtime authorization
**Authority**: Historical `D-267` plus bounded `D-274` unlock
**Next Gate**: complete the bounded scorer/grid implementation and publish evidence
**Confidence**: `10/10` on planning continuity, `9/10` on runtime authorization clarity

---

## Week 1 Docs-Only Extension (D-267 Hold Preserved)

**Scope**: planning clarification and research-index cleanup only. No runtime surface touched.
**Owner**: Codex -> CEO handoff
**Boundaries**: this companion note plus `docs/research/researches.md` only

### Locked Design Decisions (Resolved Low-Certainty Items)

1. `Pardo (2011)` remains a bibliographic note only; no local PDF is required under the current docs-only hold.
2. Week 1 documentation remains an extension of this existing companion note; no separate Phase 51 brief is opened.

### No-Touch Boundaries (D-267 Enforced)

- `strategies/`, `tests/`, `backtests/`, `data/processed/`, and any Phase 51 SAW/runtime surface
- lithium / `ALB` / `SQM` expansion
- SanDisk symbol-lineage work
- any code, tests, optimizer, or macro-gravity implementation
- any Phase 50, paper-runtime, live-runtime, or broker-surface integration

### Week 1 Acceptance Gates (Docs-Only Form)

- `W1-01`: `docs/research/researches.md` records the three cited sources with novelty notes
- `W1-02`: this companion note records the locked decisions and no-touch boundaries
- `W1-03` to `W1-05`: deferred until a new authorization explicitly replaces the current `D-267` hold

### Research Pack Summary

`Bailey et al. (2015)`, `Erten & Ocampo (2012)`, and `Pardo (2011)` are documented as the bounded research basis for a future grid-search and validation design. This preserves the planning rationale without opening a runtime surface.

### Rollback

If this docs-only extension is rejected, rollback is limited to this appended section and the corresponding research-index update in `docs/research/researches.md`.

### Week 1 Evidence Note (Docs-Only)

Docs-only cleanup complete inside the approved planning surface. Local research PDFs already on disk remain the source of truth for Bailey and Erten, `Pardo (2011)` remains bibliographic only, and runtime stays blocked under `D-267`.
