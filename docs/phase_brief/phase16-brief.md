# Phase 16 Brief: Walk-Forward Optimization & Honing (FR-080)
Date: 2026-02-15

## 1. Objective
Hone Phase 15 adaptive parameters with deterministic walk-forward optimization
while preserving structural execution rules.

## 2. Governance: FIX vs FINETUNE
### FIX (Non-Tunable)
- Trend eligibility gate remains fixed: `price > SMA200`.
- Regime budgets remain fixed: `GREEN=1.0`, `AMBER=0.5`, `RED=0.0`.
- Portfolio safety remains fixed: `sum(weights_t) <= regime_budget_t` and long-only weights.
- OOS leakage remains prohibited: OOS data cannot be used for parameter search.

### FINETUNE (WFO-Tunable Only)
- `entry_logic` (`dip`, `breakout`, `combined`).
- `alpha_top_n` (selection depth).
- `hysteresis_exit_rank` with invariant `hysteresis_exit_rank >= alpha_top_n`.
- `rsi_entry_percentile`.
- `atr_multiplier`.

## 3. WFO Policy
- Split protocol is fixed and leak-free:
  - Train: `2015-01-01` to `2021-12-31`.
  - OOS/Test: `2022-01-01` to `2024-12-31`.
- Candidate ranking and parameter selection use train metrics only.
- Promotion policy (FR-080 mismatch fix, "Greed patch"):
  - Build a promotable pool first: candidates with valid train metrics and
    `stability_pass AND activity_guard_pass`.
  - If promotable pool is non-empty, rank only that pool by:
    - `objective_score` (desc)
    - `train_cagr` (desc)
    - `train_robust_score` (desc)
    - `train_ulcer` (asc)
    - deterministic parameter tie-breakers (`entry_logic`, `alpha_top_n`,
      `hysteresis_exit_rank`, `adaptive_rsi_percentile`, `atr_preset`).
  - If promotable pool is empty, keep train-only ranking for diagnostics and
    do not promote.
- OOS/Test window is read-only for stability and governance checks.
- OOS fields are never used for ranking or tie-breaks.
- Phase 16.2 activity guardrails:
  - `trades_per_year > min_trades_per_year` (default `10.0`)
  - `exposure_time > min_exposure_time` (default `0.30`)
  - Promotion gate is `stability_pass AND activity_guard_pass`.

## 4. Promotion Gate and Status
- Required pass path:
  - Promotable-first train ranking
  - OOS stability checks
  - Phase 16.2 activity checks from generated OOS weights only
- Selection pool labels:
  - `promotable_train_ranked`: promoted from promotable-first pool.
  - `train_only_rejected_guardrails`: no promotable row; train-only fallback
    kept for diagnostics, no promotion.
  - `no_valid_candidates`: no candidate with valid train metrics.
- Deterministic activity metrics per candidate:
  - `exposure_time`: fraction of OOS rows with non-zero gross exposure.
  - `trades_per_year`: annualized count of OOS positive turnover-change events.
- Candidate promoted defaults (research-only; not runtime defaults):
  - `alpha_top_n=10`
  - `hysteresis_exit_rank=20`
  - `adaptive_rsi_percentile=0.05`
  - `atr_preset=3.0` mapped to ATR multipliers `3.0/4.0/5.0` (`low/mid/high` volatility).
- Rollback note:
  - Promoted defaults were blocked by the Phase 15 verifier and moved to research-only status.
  - Runtime default keeps Alpha Engine disabled in UI until Phase 16.2 logic expansion validates pass criteria.

## 5. Search Space (Initial Contract)
- `entry_logic`: `dip`, `breakout`, `combined`.
- `alpha_top_n`: `10`, `20`.
- `hysteresis_exit_rank`: `20`, `30` with
  `hysteresis_exit_rank >= alpha_top_n`.
- `rsi_entry_percentile`: `0.05`, `0.10`, `0.15`.
- `atr_preset`: `2.0`, `3.0`, `4.0`, `5.0`.

## 6. Acceptance Criteria
- No OOS leakage evidence in optimizer protocol and outputs.
- Structural rules from FR-070 remain unchanged.
- Hard constraints pass for all promoted parameter sets.
- Phase 16.2 guardrails are reflected in artifacts:
  - thresholds (`min_trades_per_year_guard`, `min_exposure_time_guard`)
  - selected candidate activity metrics (`exposure_time`, `trades_per_year`, `activity_guard_pass`)
- Required artifacts are generated:
  - `data/processed/phase16_optimizer_results.csv`
  - `data/processed/phase16_best_params.json`
  - `data/processed/phase16_oos_summary.csv`

## 7. Artifacts
- `data/processed/phase16_optimizer_results.csv`
- `data/processed/phase16_best_params.json`
- `data/processed/phase16_oos_summary.csv`

## 8. Runtime Optimization Patch
- Low-cost acceleration is enabled for FR-080 candidate search:
  - Single-pass data hydration (shared in-memory data across all candidates).
  - Optional multi-process evaluation controls:
    - `--max-workers` (0 = auto)
    - `--chunk-size`
    - `--disable-parallel`
    - `--progress-interval-seconds`
    - `--progress-path`
    - `--live-results-path`
    - `--live-results-every`
    - `--disable-live-results`
    - `--lock-stale-seconds`
    - `--lock-wait-seconds`
- Safety fallback:
  - If parallel execution fails, the optimizer retries sequentially without changing governance rules.
  - Artifact outputs are staged then promoted as a bundle with rollback on commit failure.
- Real-time observability:
  - Heartbeat JSON is updated throughout evaluation:
    - `data/processed/phase16_optimizer_progress.json`
  - Interim candidate leaderboard is atomically refreshed:
    - `data/processed/phase16_optimizer_live_results.csv`

## 9. Phase 16.2 Step 3: Dip OR Breakout Entry Expansion
- Starvation diagnosis identified a failure mode where names passed trend/liquidity gates but were blocked by dip-only entry.
- Entry logic is expanded to:
  - `entry = tradable & trend_ok & (dip_entry OR breakout_entry_green)`.
- Dip path remains unchanged:
  - `dip_entry = rsi_gate & (pullback_gate | rsi_cross)`.
- Breakout path is PIT-safe and GREEN-only:
  - `breakout_entry_green = (regime_state == "GREEN") & (adj_close > prior_50d_high)`.
  - `prior_50d_high` is computed per `permno` as rolling 50-day high shifted by one bar.
- Reason-code contract:
  - Dip reason has precedence when both paths are true.
  - Dip: `MOM_DIP_<REGIME>_<ADAPT|FIXED>`
  - Breakout: `MOM_BREAKOUT_GREEN_<ADAPT|FIXED>`
- Structural invariants remain unchanged:
  - Regime budgets and hard exposure caps are unchanged.
  - No look-ahead is introduced.

## 10. Phase 16.3 Long-Term Remediation: PIT Yearly Universe Expander (FR-060)
- Objective:
  - Reduce feature-builder survivorship concentration from one global liquidity ranking by expanding selection to a point-in-time yearly union universe.
- Scope:
  - Module: `data/feature_store.py`.
  - Universe modes:
    - `global` (legacy behavior): one global top-N ranking.
    - `yearly_union` (new default): select top-N by liquidity inside each calendar year, constrained to `[start_date, end_date]`, then union distinct `permno`.
- New controls:
  - Config fields:
    - `universe_mode` (default `yearly_union`)
    - `yearly_top_n` (default `100`)
  - CLI:
    - `--universe-mode {global,yearly_union}`
    - `--yearly-top-n <int>`
    - `--top-n` retained for `global` compatibility.
- Safety and operations:
  - Existing lock + atomic parquet write path remains unchanged.
  - Status logs now emit selected universe mode and final permno count.
  - Added pre-load guard for `yearly_union` size using existing memory-envelope policy to abort unsafe runs.
- Backward compatibility:
  - `run_build(start_year, top_n, end_date)` remains valid; new params are optional.

## 11. Phase 16.5 Alpha Discovery Tournament (Entry Logic Dimension)
- Objective:
  - Resolve dip-starvation by evaluating entry modes directly in FR-080 search.
- Implementation:
  - `AlphaEngineConfig` adds `entry_logic` with strict validation:
    - `dip`, `breakout`, `combined`.
  - `InvestorCockpitStrategy` forwards `alpha_entry_logic` into `AlphaEngine`.
  - `backtests/optimize_phase16_parameters.py` adds:
    - CLI flag `--entry-logic-grid`.
    - Grid construction + validation against `AlphaEngine.ENTRY_LOGIC_SET`.
    - Deterministic tie-break inclusion of `entry_logic`.
  - Required summary/result fields now include `entry_logic`.
- Safety:
  - FR-080 governance is unchanged:
    - train-only ranking,
    - OOS used only for stability/activity promotion gate,
    - no OOS ranking/tie-break leakage.

## 12. Phase 16.7 Fundamental Upgrade (Stream C: Docs + Data Layer)
- Objective:
  - Expand PIT fundamentals to support first-principles moat/demand selection.
- Scope (Step 2 implemented):
  - `data/fundamentals_updater.py`
  - `data/fundamentals_compustat_loader.py`
  - `data/fundamentals.py`
  - `scripts/validate_factor_layer.py`
- New canonical fundamentals fields:
  - `net_income_q`
  - `equity_q`
  - `eps_basic_q`
  - `eps_diluted_q`
  - `eps_q` (diluted-priority fallback to basic)
  - `eps_ttm`
  - `eps_growth_yoy`
  - `roe_q`
- Data policy:
  - Net income maps to common-share earnings when available (`Net Income Common Stockholders` / `niq`).
  - Equity fallback uses `Total Assets - Total Liabilities` when explicit stockholders equity is missing.
  - EPS stores both basic and diluted when available; selector-facing `eps_q` prioritizes diluted EPS.
- Safety:
  - PIT release-date discipline is unchanged.
  - `run_update()` now acquires the shared updater lock and writes
    `fundamentals.parquet`, `fundamentals_snapshot.parquet`, and `tickers.parquet`
    via atomic temp-file swap.
  - Compustat ingestion now returns graceful lock-contention status instead of
    raising an uncaught timeout stack trace.
  - `scripts/validate_factor_layer.py` core coverage gate now evaluates on the
    investable snapshot subset (`quality_pass==1`) while still reporting
    full-snapshot coverage for observability.

## 13. Phase 16.7b Capital-Cycle Pivot (Stream A+B Merge Contract)
- Objective:
  - Move from generic growth screening to a Quality-Gated Capital Cycle model
    that is restatement-safe and agent-ready.
- Model contract:
  - `Score = (0.4 * Z_moat) + (0.4 * Z_discipline_cond) + (0.2 * Z_demand)`
  - `Z_moat`: normalized moat proxy (initially ROIC family).
  - `Z_discipline_cond`:
    - base penalty tracks asset growth discipline.
    - monopoly conditional relief: when operating-margin delta is positive,
      growth penalty is reduced toward zero.
  - `Z_demand`: normalized demand acceleration proxy (revenue/inventory delta).
- Data contract:
  - Explicit raw fields must be present in fundamentals artifacts when available:
    - `capex_q`
    - `depreciation_q`
    - `inventory_q`
    - `total_assets_q`
    - `operating_income_q`
  - Capital-cycle derived fields:
    - `delta_capex_sales`
    - `operating_margin_delta_q`
    - `delta_revenue_inventory`
    - `asset_growth_yoy`
- PIT/Bitemporal contract:
  - Fundamentals rows carry `published_at`.
  - As-of queries must enforce `published_at <= trade_date`.
  - Conservative fallback for legacy rows with missing `published_at`:
    - use `filing_date` when available,
    - else `fiscal_period_end + 90 days`.
- Acceptance criteria:
  - No look-ahead leakage in fundamentals access path under as-of queries.
  - Schema remains backward-compatible (missing new columns are backfilled to `NaN`).
  - Existing scanner/runtime flows continue to run with prior artifacts.

## 14. Phase 17.2 Spec Engine Skeleton + Hash Cache
- Objective:
  - Replace hardcoded feature scoring blocks with a declarative spec executor.
- Implementation:
  - Added `data/feature_specs.py`:
    - `FeatureSpec` dataclass:
      - `name`
      - `func`
      - `category`
      - `inputs`
      - `params`
      - `smooth_factor`
    - default registry includes technical and initial capital-cycle specs:
      - `z_resid_mom`, `z_flow_proxy`, `z_vol_penalty`, `composite_score`
      - `z_moat`, `z_discipline_cond`, `z_demand`, `capital_cycle_score`
  - Refactored `data/feature_store.py`:
    - added spec executor loop over registry.
    - performs dependency checks for fundamental specs using bitemporal snapshot columns.
    - wires bitemporal fundamentals daily matrices into feature context.
    - exposes new output columns:
      - `z_moat`
      - `z_discipline_cond`
      - `z_demand`
      - `capital_cycle_score`
- Hash cache:
  - Build cache key derives from:
    - spec signatures
    - config parameters
    - universe/permno hash
    - input artifact fingerprints
  - Cache artifact path:
    - `data/processed/features_<cache_key>.parquet`
  - On cache hit:
    - skips compute and publishes from cached artifact.
- Safety:
  - Existing updater lock + atomic write semantics remain intact.
  - Fundamental spec failures degrade to NaN matrices and log warnings instead of crashing the build.

## 15. Phase 16.9 Smoke Test: CSCO 2000 Event Study
- Objective:
  - Validate that capital-cycle logic can de-rate a bubble-era winner when
    inventory commitments accelerate.
- Study artifact:
  - `backtests/event_study_csco.py`
  - Outputs:
    - `data/processed/csco_event_study_1999_2001.csv`
    - `data/processed/csco_event_study_1999_2001.html`
- Data path:
  - Primary: `daily_fundamentals_panel.parquet`.
  - Fallback (when panel lacks required fields in 1999-2001):
    - local Compustat CSV (`data/e1o8zgcrz4nwbyif.csv`).
- Scoring contract used in the event study:
  - `score = 0.4*z_moat + 0.4*z_discipline_cond + 0.2*z_demand`
  - `z_discipline_cond` in the smoke test adds explicit inventory-commitment
    pressure (`inventory_to_revenue` level + acceleration) and partial
    operating-leverage relief.
- PASS criteria:
  - `Q3 2000 score < Q2 2000 score`
  - `Q4 2000 score < Q3 2000 score`
  - `Q2-Q4 drop >= 0.25`
  - `Q4 z_moat > 0` (monopoly signal still present)
- Run result (latest):
  - Source used: `compustat_fallback`
  - `Q2 2000 score = 0.4344`
  - `Q3 2000 score = 0.3966`
  - `Q4 2000 score = 0.0328`
  - `Q4 z_moat = 1.0828`
  - Verdict: `PASS`

## 16. Phase 16.10 Stress Test: Micron Paradox (MU 2016)
- Objective:
  - Test whether the current capital-cycle discipline term falsely de-rates a
    cyclical inventory build ahead of a demand supercycle.
- Study artifact:
  - Reused event-study harness with rally-positive evaluation mode:
    - `backtests/event_study_csco.py --eval-mode rally_positive`
  - Outputs:
    - `data/processed/mu_event_study_2014_2018.csv`
    - `data/processed/mu_event_study_2014_2018.html`
- Window:
  - Full context: `2014-01-01 .. 2018-12-31`
  - Rally check: `2016-04-01 .. 2017-03-31`
- Result:
  - Source used: `compustat_fallback`
  - Price return during rally window: `+162.0%` (`11.03 -> 28.90`)
  - Rally score stats:
    - mean: `-1.1809`
    - min: `-2.4056`
    - max: `0.6947`
    - positive-share: `24.51%`
  - Verdict: `FAIL` (score does not stay positive through the rally).
- Interpretation:
  - Current discipline term over-penalizes inventory/asset build in cyclical
    semis and can trigger false-sell behavior near trough-to-recovery regime shifts.
- Next patch target:
  - Add a cyclical exception modifier (e.g., book-to-bill / shipment proxy) to
    reduce discipline penalty when demand-leading evidence is improving.

## 17. Phase 16.11 Turnover Gate Patch + Twin Verification
- Objective:
  - Implement conditional override:
    - if `delta(revenue_inventory_q) > 0.05`, waive discipline penalty.
- Code updates:
  - `data/feature_specs.py`
    - `spec_discipline_conditional` now accepts turnover input and applies
      `turnover_gate_threshold` (`0.05` default).
    - Default `z_discipline_cond` spec now depends on:
      - `asset_growth_yoy`
      - `operating_margin_delta_q`
      - `delta_revenue_inventory`
  - `backtests/event_study_csco.py`
    - Added shared turnover-gate application for both panel and Compustat
      fallback paths.
    - Added CLI control `--turnover-gate-threshold`.
- Verification A (Cisco 2000):
  - Verdict: `PASS` (de-rating still preserved).
  - `Q2=0.4344`, `Q3=0.3966`, `Q4=0.0328`.
- Verification B (Micron 2016):
  - Verdict: `FAIL` under strict rally-positive gate.
  - Window `2016-04-01 .. 2017-03-31`:
    - mean score `-1.2894`
    - min `-2.4056`
    - max `-0.0603`
    - positive-share `0.0000`
- Conclusion:
  - Turnover Gate is implemented but not sufficient to resolve the Micron
    paradox under strict positivity criteria.
  - Next iteration should add a stronger cyclical exception signal
    (book-to-bill proxy / forward demand indicator) beyond turnover alone.

## 18. Phase 16.12 Inventory Quality Gate (Book-to-Bill / GM / DSO)
- Objective:
  - Classify inventory build quality using leading signals and waive discipline
    penalty only for strategic builds.
- Data-layer expansion:
  - Added new fundamentals fields across Yahoo + Compustat + panel paths:
    - `cogs_q`
    - `receivables_q`
    - `deferred_revenue_q`
    - `delta_deferred_revenue_q`
    - `book_to_bill_proxy_q`
    - `dso_q`
    - `delta_dso_q`
    - `gm_accel_q`
  - Updated PIT loaders/snapshots/broadcasters:
    - `data/fundamentals_updater.py`
    - `data/fundamentals_compustat_loader.py`
    - `data/fundamentals.py`
    - `data/fundamentals_panel.py`
- Feature logic upgrade:
  - `data/feature_specs.py::spec_discipline_conditional` now supports weighted
    soft-vote gate:
    - Demand vote (strongest): `book_to_bill_proxy_q > 1.0` (weight `2`).
    - Pricing vote: `gm_accel_q >= 0`.
    - Collections vote: `delta_dso_q <= 0`.
  - Gate policy:
    - If book-to-bill present: open when weighted votes `>= 2`.
    - If book-to-bill missing: fallback requires GM + DSO votes (`>= 2`).
  - Robust fallbacks:
    - `gm_accel_q` falls back to `operating_margin_delta_q` when absent.
    - `delta_dso_q` falls back to `-delta_revenue_inventory` when receivables are unavailable.
- Validation:
  - Unit/integration tests:
    - `pytest -q` passes.
    - Updated tests:
      - `tests/test_feature_specs.py`
      - `tests/test_bitemporal_integrity.py`
  - Twin event-study verification:
    - Cisco 2000: `PASS` (sell behavior preserved).
    - Micron 2016 rally-positive: `FAIL` (score remains negative under strict
      “all days > 0” criterion).
- Current verdict:
  - Inventory Quality Gate is implemented and wired end-to-end.
  - Twin verification is partially satisfied; Cisco is preserved but Micron
    remains blocked under strict positivity.

## 19. Phase 16.13 Proxy Gate Pivot (No-New-Fetch Regime Upgrade)
- Objective:
  - Replace hard-threshold inventory gate with a smoother proxy score that uses
    only already-fetched quarterly fields.
  - Keep PIT/bitemporal behavior unchanged and quarterly update cadence intact.
- Data policy:
  - No new external fetch fields are required.
  - Derived metrics are computed from existing quarterly columns:
    - `sales_growth_q = pct_change(total_revenue_q, 1)`
    - `sales_accel_q = delta(sales_growth_q)`
    - `op_margin_accel_q = delta(operating_margin_delta_q)`
    - `bloat_q = delta(ln(total_assets_q - inventory_q)) - delta(ln(total_revenue_q))`
    - `net_investment_q = (abs(capex_q) - depreciation_q) / lag(total_assets_q, 1)`
- Score contract:
  - `z_inventory_quality_proxy = z(sales_accel_q) + z(op_margin_accel_q) - z(bloat_q) - 0.5*z(net_investment_q)`
  - Discipline override gate:
    - if `z_inventory_quality_proxy > 0`, waive discipline penalty.
- Capital-cycle composition remains:
  - `capital_cycle_score = 0.4*z_moat + 0.4*z_discipline_cond + 0.2*z_demand`
- Acceptance criteria:
  - CSCO 2000 event study still passes de-rating test.
  - MU 2016 rally window improves relative to Phase 16.12 baseline (mean/positive-share).
  - Schema remains backward-compatible (missing new derived columns backfilled to `NaN`).
  - `pytest -q` passes after wiring updater + panel + feature engine paths.
