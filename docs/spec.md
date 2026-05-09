Technical Specification: Terminal Zero (Ironclad Architecture)
Author: Atomic Mesh | Date: 2026-02-19 | Status: Active Blueprint | Version: 14.1 (PM Hierarchy + Stage Loop Governance Sync)
Guiding Principle: "Signals from Price, PnL from Returns."

0. Project Hierarchy and Stage Loop (PM Governance)
  Purpose:
    Keep planning MECE and execution-focused by using a project-based hierarchy, not a technical-layer checklist.

  Canonical hierarchy (initialize at project start):
    - L1 (Project Pillar): e.g., "Backtest Engine (Signal System)"
    - L2 (Streams): Backend | Frontend/UI | Data | Ops
    - L3 (Stage Flow): Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD

  Snapshot reporting contract:
    - Header must include:
      - L1
      - L2 Active Streams
      - L2 Deferred Streams
      - L3 Stage Flow
      - Active Stream
      - Active Stage Level (L2/L3/L4)
    - Main table shows only stage rows under the active level for the selected active stream.
    - Stage set must be MECE under the same parent scope.
    - Stage rows are stream-specific and include current scope, rating, and next scope.
    - Planning stage is a confirmation gate: scope boundary, ownership/handoff, and acceptance checks.
    - Planning row must explicitly carry `Boundary`, `Owner/Handoff`, and `Acceptance Checks`.
    - ASCII table schema is fixed: `Stage | Current Scope | Rating | Next Scope`.
    - Rows must be single-line; truncate text to avoid wrapped-cell leakage.
    - Secondary next suggestion is outside table as `Remark:` and appears only when:
      - `next_step_certainty < 75`
      - `rating_diff_between_top_next_steps < 20`
    - If all rows share the same scope, keep `L1` as header only and do not repeat `L1` in table rows/columns.

  Scoring rubric:
    - `Rating`: `0-100` progress/readiness for the current stage row.
    - `next_step_certainty`: `0-100` confidence for the next-step recommendation.
    - `rating_diff_between_top_next_steps`: absolute delta between primary and secondary next-step ratings.

  Minimal iteration loop (anti-sprawl):
    - Keep main table at active level.
    - Expand only one stage into next depth (L4) when required.
    - Expand only if:
      - two or more plausible sub-steps block start, or
      - next-step certainty < 75, or
      - high-payoff ambiguity exists, or
      - handoff risk exists.
    - Expanded stage contains 3-5 MECE children, each tied to an artifact and "done when" stop condition.
    - Collapse back after action when certainty >= 75.

  Document placement:
    - Canonical policy: `docs/spec.md` (this section).
    - Reusable rendering snippet: `docs/templates/plan_snapshot.txt`.
    - Live loop status: active `docs/phase*-brief.md`.

  Regime contract precedence note (cross-phase consistency):
    - FR-041 matrix entries are historical freeze documentation.
    - Current runtime budget contract is FR-050/FR-070 (`GREEN=1.0`, `AMBER=0.5`, `RED=0.0`).

  R64.1 dependency hygiene note:
    - Alpaca operational/paper quote infrastructure uses `alpaca-py==0.43.4` as the main SDK boundary.
    - The legacy `alpaca-trade-api` package is excluded from the main research environment.
    - This SDK migration does not authorize live orders, broker automation, or any scope beyond paper operational quote metadata.

1. System Architecture Diagram
The system is composed of six strictly isolated layers:
  Data Layer (The Lake): Hybrid Parquet lake (WRDS base + Yahoo patch).
  Compute Layer (The Console): A stateless, vectorized simulation kernel.
  Strategy Layer (The Cartridge): Pluggable signal generators.
  Optimizer Layer (The Grid): Automated parameter sweep engine.
  Updater Layer (The Bridge): Yahoo Finance live data feed. ← NEW
  Application Layer (The Cockpit): A Streamlit dashboard for interaction.

2. Data Layer Specification

2.1 Storage Format
  Format: Apache Parquet (Snappy Compression).
  Location: ./data/processed/
  Partitioning: None (Single file for MVP efficiency).

2.2 Schema Definitions

A. prices.parquet (The Asset Universe)
  Sort Order: permno, date
  Fill Policy: ffill() on price columns (handling holidays/suspensions).
  | Column    | Type          | Origin / Formula                        | Critical Usage           |
  |-----------|---------------|-----------------------------------------|--------------------------|
  | date      | datetime64[ns]| CRSP date                               | Index Alignment          |
  | permno    | int64         | CRSP permno                             | Unique Asset ID          |
  | raw_close | float32       | abs(prc)                                | Liquidity Filters        |
  | adj_close | float32       | abs(prc) [no cfacpr available]           | Signals ONLY (RSI, MA)   |
  | total_ret | float32       | ret (filled with dlret on death)         | Execution / PnL          |
  | volume    | float32       | vol                                     | Liquidity Filters        |

  DATA CONSTRAINT: No ASKHI/BIDLO columns available.
  All High/Low logic uses Adj Close approximations.
  ATR = abs(Close_t - Close_{t-1}). k raised to 3.5 to compensate.

D. yahoo_patch.parquet (The Yahoo Bridge) ← NEW
  Same schema as prices.parquet.
  Contains Yahoo Finance data from 2025-01-01 onwards.
  Generated by data/updater.py via batch yf.download().
  app.py reads prices.parquet UNION ALL yahoo_patch.parquet via DuckDB.
  The base prices.parquet is NEVER modified (append-only architecture, D-21).

E. tickers.parquet (The Ticker Map)
  | Column | Type     | Description |
  |--------|----------|-------------|
  | permno | uint32   | CRSP asset ID |
  | ticker | varchar  | Human-readable symbol (AAPL, NVDA, ...) |
  Source: Latest ticker per permno from raw CRSP CSV.
  Auto-expanded with synthetic permnos (900000+) for new Yahoo tickers.

B. fundamentals.parquet (The Quality Bedrock) [FR-027]
  Quarterly sparse fundamentals keyed by `release_date` for PIT safety.
  Core columns:
  | Column             | Type          | Description |
  |--------------------|---------------|-------------|
  | permno             | int64         | Asset ID |
  | ticker             | varchar       | Symbol alias |
  | release_date       | datetime64[ns]| First date fundamentals become tradable |
  | roic               | float32       | Return on invested capital proxy |
  | revenue_growth_yoy | float32       | YoY growth proxy |
  | quality_pass       | int8          | MVQ gate (1 pass, 0 fail) |

F. fundamentals_snapshot.parquet (Scanner-Ready Snapshot) [FR-027]
  Write-time compressed latest fundamentals state per symbol.
  Purpose: O(1)-style scanner quality lookup without loading full sparse history.
  Current observed size (2026-02-14): 1,680 symbols.

G. sector_map.parquet (Static Context Map) [FR-028]
  Location: `./data/static/sector_map.parquet`
  Columns: `ticker`, `permno` (optional), `sector`, `industry`, `updated_at`.
  Purpose: Attach contextual risk buckets to scanner and optimizer outputs.

H. Compustat Loader Artifacts [FR-031]
  Loader: `data/fundamentals_compustat_loader.py`
  Inputs:
    - Local quarterly CSV (`data/e1o8zgcrz4nwbyif.csv`)
    - `tickers.parquet` + Top3000 liquid ranking
  Outputs:
    - Canonical merge into `fundamentals.parquet` (source precedence applied)
    - Rebuilt `fundamentals_snapshot.parquet`
    - `compustat_ticker_match_top3000.parquet` (mapping audit)
    - `compustat_unmatched_top3000.csv` (coverage gap audit)
  Safety controls:
    - updater lock reuse (`.update.lock`)
    - Atomic writes (`os.replace`) through updater helper
    - Timestamped backups under `data/processed/backups/`

I. R3000 PIT Membership Artifacts [FR-032]
  Loader: `data/r3000_membership_loader.py`
  Input gate:
    - Required columns: `gvkey`, `from`, `thru`
    - Minimum usable rows: default `>= 1000`
    - Fails fast on metadata-only index-label exports
  Outputs:
    - `data/processed/r3000_membership.parquet`
    - `data/processed/universe_r3000_daily.parquet`
    - `data/processed/r3000_unmatched.csv`
  PIT membership expansion:
    - daily universe row exists only if `from_date <= date <= thru_date`

J. earnings_calendar.parquet (Catalyst Event Layer) [FR-034]
  Location: `./data/processed/earnings_calendar.parquet`
  Columns:
  | Column             | Type          | Description |
  |--------------------|---------------|-------------|
  | permno             | uint32        | Asset ID |
  | ticker             | varchar       | Symbol |
  | next_earnings_date | datetime64[ns]| Upcoming earnings date (if known) |
  | last_earnings_date | datetime64[ns]| Most recent earnings date (if known) |
  | fetched_at         | datetime64[ns]| Calendar ingestion timestamp |
  | source             | varchar       | Data source tag (`yfinance`) |
  Loader: `data/calendar_updater.py` (lock-safe + atomic write)

C. macro.parquet (The Regime)
  Sort Order: date
  | Column    | Type    | Origin                 | Critical Usage                    |
  |-----------|---------|------------------------|-----------------------------------|
  | spy_close | float32 | SPY (permno 84398)     | Market Trend Filter               |
  | vix_proxy | float32 | Rolling StdDev of SPY  | Adaptive Stops (k), Vol Sizing    |

K. macro_features.parquet (FR-035 Canonical Macro Layer)
  Location: `./data/processed/macro_features.parquet`
  PIT policy:
    - Fast market series: T+0.
    - Slow FRED series: shifted by +1 trading day.
  Core columns:
  | Column | Type | Rule |
  |---|---|---|
  | date | datetime64[ns] | trading calendar index |
  | spy_close | float32 | Yahoo SPY close (legacy-compatible) |
  | vix_proxy | float32 | 20d realized vol proxy from SPY returns |
  | qqq_close | float32 | Yahoo QQQ close |
  | vix_level / vix3m_level / vvix_level | float32 | Yahoo volatility surface |
  | vix_vix3m_spread | float32 | `vix_level - vix3m_level` |
  | vix_term_ratio | float32 | `vix_level / vix3m_level` |
  | vix_backwardation | bool | `vix_term_ratio > 1.0` |
  | liquidity_air_pocket | bool | `(spread > 0) & (vvix > 110)` |
  | qqq_peak_252d | float32 | rolling 252d max of QQQ close |
  | qqq_drawdown_252d | float32 | `qqq_close / qqq_peak_252d - 1` |
  | qqq_drawdown_252d_z_adapt | float32 | rolling z-score(252d) of `qqq_drawdown_252d` |
  | qqq_ma200 | float32 | rolling 200d average of QQQ close |
  | qqq_ma200_trend_gate | bool | `qqq_close >= qqq_ma200` |
  | qqq_ret_5d_z_adapt | float32 | adaptive z-score of 5d QQQ return |
  | qqq_ret_21d_z_adapt | float32 | rolling z-score(252d) of 21d QQQ return |
  | qqq_drawdown_5d_delta_z_adapt | float32 | adaptive z-score of 5d change in `qqq_drawdown_252d` |
  | slow_bleed_label | bool | `qqq_ret_21d_z_adapt <= -1.0` and `qqq_drawdown_252d_z_adapt <= -0.5` |
  | sharp_shock_label | bool | `qqq_ret_5d_z_adapt <= -2.5` or `qqq_drawdown_5d_delta_z_adapt <= -2.5` |
  | dxy_spx_corr_20d | float32 | rolling 20d corr of returns |
  | dollar_squeeze | bool | `corr > 0.50` |
  | sofr_effr_spread | float32 | `SOFR - DFF` (pre-2018 missing -> 0.0) |
  | collateral_crisis | bool | `sofr_effr_spread > 0.10` |
  | hyg_lqd_ratio | float32 | `HYG / LQD` |
  | hyg_lqd_ratio_z63 | float32 | rolling z-score(63d) |
  | credit_freeze | bool | `hyg_lqd_ratio_z63 < -2.0` |
  | mtum_spy_corr_60d | float32 | rolling 60d corr of returns |
  | momentum_crowding | bool | `mtum_spy_corr_60d > 0.85` |
  | month_end_rebalance_flag | bool | last 3 trading days of month |
  | month_end_rebalance_direction | float32 | sign(MTD SPY - MTD BND) |
  | stress_count | int8 | sum of boolean stress flags |
  | regime_scalar | float32 | stress map: 1.0 / 0.7 / 0.5 / 0.0 |
  Builder: `data/macro_loader.py`
  Validator: `scripts/validate_macro_layer.py`
  Performance notes (Phase 9.2):
    - Rolling percentile uses vectorized `rolling().rank(pct=True)` path (fallback retained).
    - FRED ingestion fetches series in parallel and bounds payload to requested date window (`cosd`, `coed`).

K.1 macro_gates.parquet (FR-035 Hard-Gate Daily Overlay)
  Location: `./data/processed/macro_gates.parquet`
  Build source: `data/macro_loader.py::build_macro_gates` (derived strictly from `macro_features.parquet` dates).
  Strategy consumption policy:
    - `state`, `scalar`, `cash_buffer`, `momentum_entry` are consumed with strict `t signal -> t+1 execution`.
    - Warmup defaults after shift: `state=AMBER`, `scalar=0.5`, `cash_buffer=0.25`, `momentum_entry=False`.
  Columns:
  | Column | Type | Rule |
  |---|---|---|
  | date | datetime64[ns] | trading calendar index |
  | state | string | `RED/AMBER/GREEN` hard-gate state |
  | scalar | float32 | exposure scalar map (`RED=0.0`, `AMBER=0.5`, `GREEN=1.0`) |
  | cash_buffer | float32 | cash reserve map (`RED=0.50`, `AMBER=0.25`, `GREEN=0.0`) |
  | momentum_entry | bool | only true in `GREEN` with trend support and no stress labels |
  | reasons | string | pipe-delimited gate reasons (`sharp_shock`, `vix_backwardation`, etc.) |
  | qqq_drawdown_252d | float32 | pass-through from macro features |
  | qqq_ma200_trend_gate | bool | pass-through from macro features |
  | slow_bleed / sharp_shock | bool | pass-through labels for strategy consumption |
  | qqq_ret_5d_z_adapt / qqq_ret_21d_z_adapt | float32 | adaptive return stress diagnostics |
  | qqq_drawdown_252d_z_adapt | float32 | adaptive drawdown stress diagnostic |
  | vix_term_ratio / vix_backwardation | float32/bool | term-structure stress diagnostics |

L. liquidity_features.parquet (FR-040 Canonical Liquidity Layer)
  Location: `./data/processed/liquidity_features.parquet`
  Columns:
  | Column | Type | Unit | Description |
  |---|---|---|---|
  | date | datetime64[ns] | date | Trading-day index |
  | us_net_liquidity_mm | float32 | USD millions | `WALCL - WDTGAL - (RRPONTSYD*1000)` |
  | liquidity_impulse | float32 | z-score | Normalized 20-day ROC of net liquidity |
  | repo_spread_bps | float32 | basis points | `(SOFR - DFF) * 100` |
  | repo_stress | bool | flag | `repo_spread_bps > 5` |
  | lrp_index | float32 | index | `Z(DTB3) - Z(VIX)` |
  | dollar_stress_corr | float32 | corr | rolling 20d corr(DXY, SPX returns) |
  | global_dollar_stress | bool | flag | `dollar_stress_corr > 0.5` |
  | smart_money_flow | float32 | index | cumulative `(SPY close - SPY open)` |
  | realized_vol_21d | float32 | pct annualized | 21d realized SPY volatility (`std(ret)*sqrt(252)*100`) |
  | vrp | float32 | pct points | volatility risk premium proxy: `vix_level - realized_vol_21d` |
  Engineering guardrails:
    - H.4.1 PIT lag rule: shift `WALCL/WDTGAL` by +2 calendar days.
    - Weekly series forward-fill capped at 14 days; daily series capped at 3 days.
    - Loader aborts if critical FRED series are unavailable.
  Builder: `data/liquidity_loader.py`
  Validator: `scripts/validate_liquidity_layer.py`


M. orbis_daily_aligned.parquet (L2 Macro Alternative Data Stream)
  Location: `./data/processed/orbis_daily_aligned.parquet`
  Source: Moody's Orbis Americas via WRDS Postgres Pipeline
  Note: Currently querying `bvd_orbis_trial` tables. Must update table queries to full volume schema (`bvd_orbis` and `orbis_qvards`) upon unlocking full tier.
  Columns:
  | Column | Type | Description |
  |---|---|---|
  | fiscal_date | datetime64[ns] | Daily interpolated business calendar |
  | median_inventory_turnover | float32 | Median `opre / stok` |
  | median_acquisition_yield | float32 | Median `ibaq / toas` |
  Pipeline (3-Script Flow):
    1. `data/orbis_loader.py` (SQL Extraction & Aggregation): Pulls `ibaq`, `toas`, `opre`, `stok` filtered by NAICS (`334%`) and private limit (`sd_ticker`).
    2. `scripts/align_orbis_macro.py` (Bitemporal Lag & Z-Score): Enforces a strict 90-day reporting delay via `merge_asof(backward)`.
    3. `scripts/orbis_signal_generator.py` (IC Validation): Calculates 252-day rolling z-scores against QQQ forward returns.

3. Compute Layer (The Engine)

3.1 The Vectorized Kernel (core/engine.py)
  Implements the Invisible Walls:
    D-04: shift(1) — no look-ahead bias.
    D-05: Turnover Tax — transaction cost deduction.
    D-08: Matrix Alignment — Engine accepts pre-pivoted Returns Matrix (T x N).

  ```python
  def run_simulation(target_weights, returns_df, cost_bps=0.0010):
      executed_weights = target_weights.shift(1).fillna(0.0)
      aligned_returns = returns_df.reindex(
          index=executed_weights.index,
          columns=executed_weights.columns
      ).fillna(0.0)
      gross_ret = (executed_weights * aligned_returns).sum(axis=1)
      turnover = executed_weights.diff().abs().sum(axis=1).fillna(0.0)
      costs = turnover * cost_bps
      net_ret = gross_ret - costs
      return pd.DataFrame({
          'gross_ret': gross_ret, 'net_ret': net_ret,
          'turnover': turnover, 'cost': costs
      })
  ```

4. Strategy Layer (The Cartridge API)

4.1 Base Class (strategies/base.py)
  All strategies return a triple: (weights, regime_signal, debug_details).

  ```python
  class BaseStrategy(ABC):
      @abstractmethod
      def generate_weights(self, prices, fundamentals, macro)
          -> tuple[pd.DataFrame, pd.DataFrame, dict]:
          pass
  ```

4.2 Adaptive Trend Strategy (strategies/adaptive_trend.py)
  3-Regime Logic:
    Attack (1.0): SPY > MA200 & VIX < 20.
    Caution (0.7): SPY > MA200 & VIX >= 20.
    Defense (0.5): SPY < MA200.

4.3 Investor Cockpit Strategy (strategies/investor_cockpit.py)
  Signal-Oriented logic for daily monitoring:
    Chandelier Stop: HighestClose(22d) - k * ATR(22d).
    Dip Hunter: Log-Price Z-Score < z_entry.
    Exposes `get_signals()` public API for Dashboard.

  4.3.1 Five-State Classifier [FR-023] ← NEW
    Hardcoded state machine computed per-stock:
    | State | Condition                                | Support Level      |
    |-------|------------------------------------------|--------------------|
    | HOLD  | Price > Stop, Price > Buy                | Stop (floor)       |
    | BUY   | Price > Stop, Price < Buy, GreenCandle   | Stop (floor)       |
    | WATCH | Price > Stop, Price < Buy, RedCandle     | Stop (floor)       |
    | AVOID | Price < Stop, Price > Buy                | Buy Zone           |
    | WAIT  | Price < Stop, Price < Buy                | z_deep = z - 1.5σ  |
    Design: Deterministic (no LLM). Microsecond-speed. Fully transparent.

  4.3.2 Conviction Scorecard [FR-024v2 — L5 Alpha] ← UPGRADED
    Vectorized per-stock scoring (0-10):
      A. Trend  (3pts): Price > MA200 (unchanged)
      B. Value  (3pts): Robust Z (MAD) < -3.0=3, < -2.0=1
      C. Macro  (2pts): VIX<20+falling=2, mixed=1, panic=0
      D. Momentum (2pts): Price>MA20 + ER>0.4=2, choppy=1
    New methods: _calculate_efficiency_ratio(), _calculate_robust_z()
    Output: conviction dict + metrics dict {rz_score, er_score} in details.

  4.3.3 Smart Watchlist + Auto-Update [FR-025] ← NEW
    Files:
      data/watchlist.json — {defaults: [...], user_added: [...]}
      data/auto_update.py — CLI: reads watchlist → updater.run_update()
    App Integration:
      - Signal Monitor saves user selections → watchlist.json
      - main() checks _is_data_stale() → auto-triggers update on startup
      - Business-day aware: skips weekends (Fri data valid on Mon)

  4.3.5 Catalyst Radar Overlays [FR-034] ← NEW
    `scan_universe()` accepts:
      - `mode`: `default` or `fresh_catalysts`
      - `earnings_blackout_days` (default 5)
      - `catalyst_lookback_days` (default 7)
    Additional outputs:
      - `days_to_earnings`
      - `days_since_earnings`
      - `earnings_risk` (bool, earnings inside blackout window)
    Behavior:
      - Default mode keeps ranking logic intact and annotates event risk.
      - Fresh catalysts mode filters to names with earnings in the last 7 days
        after trend+quality gates.

  4.3.6 Historical Baseline v1 (Frozen Pre FR-041)
    Historical reference only (not the active runtime budget contract).
    Weight pipeline (historical):
      - Dynamic params (if enabled): `k = 2.5 + 1.5*vol_rank`, `z = -3.0 + 2.0*vol_rank`.
      - Stop: `highest_close(22) - k*ATR(22)` where ATR is close-to-close absolute diff mean.
      - Dip signal: `price < buy_zone`, with optional green-candle confirmation.
      - Raw hold signal: `(price > stop) OR dip_signal`.
      - Equal-weight normalization across active signals, then macro scaling applied.
    Regime scaling (historical fallback):
      - Legacy VIX fallback scalar:
        - `1.0` when `vix_proxy < 20`
        - `0.7` when `20 <= vix_proxy <= 30`
        - `0.5` when `vix_proxy > 30`
      - If `regime_scalar` is present, strategy uses clipped scalar `[0.0, 1.0]` and falls back to VIX mapping only on NaNs.
    Macro conviction score (current `_macro_score`, 0..2):
      - Priority 1: `regime_scalar` mapping
        - `<= 0.5 -> 0`, `<= 0.7 -> 1`, `> 0.7 -> 2`.
      - Priority 2: liquidity fallback (`liquidity_impulse`, `repo_stress`, `global_dollar_stress`, `lrp_index`)
        - `stress_hits = repo_stress + global_dollar_stress + (liquidity_impulse < -1.0) + (lrp_index > 1.0)`
        - `stress_hits >= 2 -> 0`; `stress_hits == 1 or liquidity_impulse < 0 -> 1`; else `2`.
      - Priority 3: VIX heuristic fallback
        - If `vix_proxy < 20`: `2` when below its 20d MA, else `1`.
        - If `vix_proxy >= 20`: `1` when below its 20d MA, else `0`.
    Liquidity threshold note (current):
      - `repo_stress` flag currently comes from `repo_spread_bps > 5` bps in the liquidity layer config.

4.4 FR-041 Contract: Regime Governor + Throttle (Historical Freeze; runtime precedence is FR-050/FR-070)
  Purpose:
    Freeze v1 behavior above, then introduce a deterministic two-layer controller
    with explicit veto (Governor) and sizing context (Throttle).

  4.4.1 RegimeManager Interface (Contract)
  ```python
  class RegimeManager(Protocol):
      def bocpd_probability(self, net_liquidity: pd.Series) -> pd.Series: ...
      def matrix_exposure(self, governor_state: str, market_state: str) -> float: ...
      def evaluate(self, macro: pd.DataFrame, idx: pd.Index) -> RegimeManagerResult: ...
  ```
  Expected outputs (per date):
    - `governor_state`: `GREEN|AMBER|RED`
    - `market_state`: `NEG|NEUT|POS`
    - `throttle_score`: continuous score in `[-2, 2]`
    - `matrix_exposure`: matrix-selected exposure
    - `target_exposure`: final enforced exposure after long-only safety clamps
    - `reason`: explainability string

  4.4.2 Governor Rules (Explicit Thresholds)
    - RED if any:
      - `repo_spread_bps > 10.0` (basis points, explicit unit)
      - `credit_freeze == True` AND `vix_level > 15`
      - `liquidity_impulse < -1.90` AND `vix_level > 20`
      - `vix_level > 40`
    - AMBER if not RED and any:
      - `us_net_liquidity_mm < 0.997 * MA20(us_net_liquidity_mm)` AND `liquidity_impulse < 0`
      - `vix_level > 25`
      - `bocpd_prob > 0.80`
    - GREEN otherwise.

  4.4.3 BOCPD Field Contract
    - Field name: `bocpd_prob` (posterior changepoint probability, 0..1).
    - Usage in Governor:
      - `bocpd_prob > 0.80` contributes to AMBER (when not already RED).

  4.4.4 Throttle Score and Binning
    - Score definition:
      - `S = mean(Z(liquidity_impulse), Z(vrp), -Z(vix_level), Z(momentum_proxy))`
      - clip `S` to `[-2, 2]`
    - Bins:
      - POS: `S > 0.5`
      - NEUT: `-0.5 <= S <= 0.5`
      - NEG: `S < -0.5`

  4.4.5 3x3 Mapping Matrix (Governor x Throttle -> Exposure)
    | Governor \ Throttle | NEG | NEUT | POS |
    |---|---:|---:|---:|
    | GREEN | 0.70 | 1.00 | 1.30 |
    | AMBER | 0.25 | 0.50 | 0.75 |
    | RED | 0.00 | 0.00 | 0.20 |

  4.4.6 Long-Only Safety Rule (FR-041)
    - No shorting in V1.
    - Hard enforcement:
      - RED + NEG -> `0.00`
      - RED + NEUT -> `0.00`
      - RED + POS -> `<= 0.20`
    - `target_exposure` is the matrix output after these clamps.

5. Optimizer Layer (NEW)

5.1 The Grid Search Engine (core/optimizer.py)
  Purpose: Automate parameter tuning for the InvestorCockpit strategy.

  ```python
  def run_grid_search(
      prices: pd.DataFrame,
      returns: pd.DataFrame,
      macro: pd.DataFrame,
      k_range: tuple = (2.0, 4.5, 0.25),  # (start, stop, step)
      z_range: tuple = (-4.0, -1.5, 0.25), # (start, stop, step)
      cost_bps: float = 0.001,
      metric: str = "ulcer_sharpe"
  ) -> pd.DataFrame:
      """
      Returns a DataFrame with columns: k, z, cagr, max_dd, sharpe, ulcer_index, ulcer_sharpe.
      Each row is one (k, z) combination.
      """
  ```

  Optimization Metric: Ulcer-Adjusted Sharpe
    Ulcer Index = sqrt(mean(drawdown^2))  — measures BOTH depth AND duration of pain.
    Ulcer Sharpe = CAGR / Ulcer Index
    Higher is better.

5.2 Adaptive Regime Parameters (FR-016)
  Instead of fixed k/z values, parameters are functions of VIX:
    | VIX Level    | k (Stop) | z (Entry) | Behavior                         |
    |-------------|----------|-----------|----------------------------------|
    | < 15        | 2.5      | -1.5      | Tight stops, buy mild pullbacks  |
    | 15 – 25     | 3.5      | -2.5      | Standard                         |
    | > 25        | 4.5      | -3.5      | Wide stops, only buy deep crashes|

5.3 Wait-for-Confirmation (FR-017)
  Signal triggers when Z < z_entry.
  Confirmation: Entry only executes if Price(T) > Price(T-1) (Green Candle).

6. Application Layer (The Dashboard)

6.1 Console Modes
  Mode 1: "✈️ Investor Cockpit" — Daily Signal Monitor + Searchable Ticker Dropdown.
  Mode 2: "🔬 Lab / Backtest" — Full backtest with equity curve.
  Mode 3: "🎯 Optimizer" — 2D Heatmap parameter sweep.
  Mode 4: "🔄 Data Manager" — System status + Yahoo update trigger. ← NEW

6.2 Implementation Roadmap
  Phase 1: Data Plumbing (ETL) ✅
  Phase 2: Vectorized Engine ✅
  Phase 3: Investor Cockpit ✅
  Phase 4: Parameter Optimizer ✅
  Phase 4.1: Dynamic Volatility Mapping ✅
  Phase 4.2: Live Data + UX ✅
    - Searchable Ticker Dropdown (FR-020)
    - Yahoo Finance Bridge (FR-021, data/updater.py)
    - Data Manager Tab (FR-022)
    - Batch download: Top 50/100/200 scope
  Phase 5: Quantamental Integration ✅
    - PIT quality gate with `release_date` alignment (FR-027)
    - Hybrid behavior: scanner hard filter + watchlist penalty cap
  Phase 6: Portfolio Optimizer ✅
    - Inverse Volatility + Mean-Variance (SLSQP) + deterministic fallback
  Phase 7: Context-Aware Intelligence ✅
    - Sector/industry static map and runtime merge
  Phase 8: Catalyst Radar Foundation (Steps 1-6) ✅
    - Top 3000 scope added to updater, fundamentals updater, sector map builder, and Data Manager UI
    - Dynamic loading batch size (`200` if universe > 2500 else `250`)
    - Top 3000 hydration completed and validated
    - Compustat bedrock ingestion merged with precedence (`compustat_csv > yfinance`) for Top3000 scope
    - Institutional factor layer added (cashflow decumulation + EV/EBITDA matrix, FR-033)
  Phase 8: Catalyst Radar (Steps 7-11) ✅
    - Added earnings calendar updater and data contract (`earnings_calendar.parquet`).
    - Wired calendar context into `load_data()` and Data Manager refresh flow.
    - Scanner now renders earnings risk labels + catalyst mode/filter controls.
    - Added calendar integrity validator (`scripts/validate_calendar_layer.py`).
  Phase 9: Macro-Regime Awareness (FR-035) 🟡
    - Added `data/macro_loader.py` to build canonical `macro_features.parquet`.
    - Added daily hard-gate artifact `macro_gates.parquet` (QQQ drawdown/MA200 + VIX term structure).
    - Added `scripts/validate_macro_layer.py` with crisis-window sanity checks.
    - Strategy consumes `regime_scalar` when available; falls back to legacy VIX logic.
    - Data Manager includes macro rebuild control and live regime metrics.
  Phase 10: Global Liquidity & Flow Layer (FR-040) 🟡
    - Add `data/liquidity_loader.py` to build `liquidity_features.parquet`.
    - Add `scripts/validate_liquidity_layer.py` for schema/PIT/event checks.
    - Enforce H.4.1 release lag in liquidity construction.
  Current phase status is tracked in active `docs/phase*-brief.md` (not in this historical roadmap block).

  4.3.4 Scanner Cockpit Architecture [FR-026] ← NEW
    Session State: cockpit_view ("scanner"|"detail"), selected_ticker (permno|None)
    Scanner View (views/scanner_view.py):
      - Calls scan_universe() on full prices_wide (2-pass, memory-safe)
      - Calls generate_weights() on watchlist permnos only (5-15 tickers)
      - Renders two styled tables with drill-down buttons
    Detail View (views/detail_view.py):
      - Receives single permno from session state
      - Runs strategy on 1 ticker only (fast)
      - Renders chart (Price+Stop+BuyZone) + action report card
    Router in render_investor_cockpit(): dispatches to scanner or detail view

6.3 Phase 8 Step 1-6 Validation (2026-02-14)
  Data Hydration Outcomes:
    - `data/processed/fundamentals.parquet`: 10,219 rows
    - `data/processed/fundamentals_snapshot.parquet`: 1,680 rows
    - `data/static/sector_map.parquet`: 3,000 rows
    - Max `release_date`: 2026-03-17

  Runtime Metrics (local smoke checks):
    - Top 2000: `prices_shape=(6574, 2000)`, load=15.356s, scan=0.227s
    - Top 3000: `prices_shape=(6576, 3000)`, load=21.307s, scan=0.307s
    - Gate metrics at Top 3000: trend=6, quality=432, survivors=2, shown=2

  Rollout Decision:
    - Keep default app load at Top 2000 for responsiveness.
    - Provide Top 3000 as explicit operator-selected expansion mode.

6.4 FR-031 Execution Results (2026-02-14)
  Compustat Ingestion Outcomes:
    - Match coverage vs Top3000: `2781/3000` (`92.70%`)
    - `fundamentals.parquet`: `10,219 -> 225,640` rows (initial merge)
    - `fundamentals_snapshot.parquet`: `1,680 -> 2,819` rows (initial merge)
    - Latest release date retained: `2026-03-17`

  Post-merge Runtime Smoke:
    - Top 3000 load: 9.384s
    - Top 3000 scan: 0.078s
    - Gate metrics: trend=6, quality=428, survivors=2, shown=2

  Notes:
    - `revenue_growth_yoy` is computed with DuckDB window `LAG(revenue, 4)` per permno.
    - Missing lag4 or zero lag denominator is set to `NaN` (fail-safe quality behavior).

6.5 FR-032 Current Status (2026-02-15)
  Implemented:
    - PIT membership loader and daily-universe generator scaffold.
    - `app.load_data()` optional `universe_mode='r3000_pit'` with as-of date support.
  Blocker:
    - Input file `data/t1nd1jyzkjc3hsmq.csv` contains only index metadata (1 row).
    - Loader correctly fails input gate until a full WRDS constituent-history export is supplied.

6.6 FR-033 Institutional Factor Layer (2026-02-15)
  Implemented:
    - Expanded canonical fundamentals schema with institutional fields:
      - raw: `oibdpq`, `atq`, `ltq`, `xrdq`, `oancfy`, `dlttq`, `dlcq`, `cheq`, `cshoq`, `prcraq`, `fyearq`, `fqtr`
      - derived: `oancf_q`, `oancf_ttm`, `ebitda_ttm`, `revenue_ttm`, `xrd_ttm`, `mv_q`, `total_debt`, `net_debt`, `ev`, `ev_ebitda`, `leverage_ratio`, `rd_intensity`
    - Cashflow decumulation and valuation ratio matrix integrated in
      `data/fundamentals_compustat_loader.py::compute_institutional_factors()`.
    - Snapshot now carries factor subset:
      `ev_ebitda`, `leverage_ratio`, `rd_intensity`, `oancf_ttm`, `ebitda_ttm`.

  Validation (`scripts/validate_factor_layer.py`):
    - PIT violations: `0`
    - Decumulation mismatch: `0.0698%` (`126,066` comparable rows)
    - Q4 spike rate (>10x median Q1-Q3): `1.69%` (`n=41,065`, p95=`5.429`)
    - Debt fallback zero-rate (dlttq/dlcq missing): `99.1482%`
    - EV/EBITDA arithmetic bad-rate (>1% rel err): `0.00%` (`n=84,014`)
    - Snapshot non-null coverage:
      - `ev_ebitda`: `48.45%`
      - `leverage_ratio`: `73.94%`
      - `rd_intensity`: `47.87%`
      - `oancf_ttm`: `85.35%`
      - `ebitda_ttm`: `80.90%`

  Post-remediation runtime:
    - `fundamentals.parquet`: `215,876` rows
    - `fundamentals_snapshot.parquet`: `1,550` rows
    - Top 3000 load: `10.105s`
    - Top 3000 scan: `0.087s`

6.7 FR-042 Verification Artifacts (2026-02-15)
  Required outputs:
    - `data/processed/regime_history.csv`
    - `data/processed/regime_overlay.png`

  `regime_history.csv` key columns:
    - `date`: trading session date
    - `governor_state`: `GREEN|AMBER|RED`
    - `market_state`: `NEG|NEUT|POS`
    - `throttle_score`: continuous score in `[-2, 2]`
    - `matrix_exposure`: exposure selected from 3x3 matrix
    - `target_exposure`: final long-only clamped exposure
    - `reason`: explainability reason string
    - `truth_window`: FR-042 validation bucket label
    - `truth_expected`: allowed/expected state set for the bucket
    - `truth_pass`: window-rule compliance flag (`0|1`)

  `regime_overlay.png` requirements:
    - Plot market proxy (`SPY` close or equivalent) with date index.
    - Overlay Governor states with color bands:
      - GREEN = risk-on
      - AMBER = caution
      - RED = defensive
    - Include legend and title with FR id (`FR-042`).

6.8 FR-050 Walk-Forward Artifacts (2026-02-15)
  Required outputs:
    - `data/processed/phase13_walkforward.csv`
    - `data/processed/phase13_equity_curve.png`

  `phase13_walkforward.csv` key columns:
    - `date`: trading session date
    - `governor_state`: FR-041 Governor at `t`
    - `signal_weight`: deterministic signal weight at `t` (`1.0|0.5|0.0`)
    - `executed_weight`: shifted weight executed at `t` from prior signal
    - `spy_close`: SPY close
    - `spy_ret`: SPY daily return
    - `cash_ret`: chosen cash return for session
    - `cash_source`: `BIL|EFFR|FLAT`
    - `turnover`: `abs(executed_weight_t - executed_weight_{t-1})`
    - `cost`: `turnover * cost_bps`
    - `strategy_ret`: `executed_weight*spy_ret + (1-executed_weight)*cash_ret - cost`
    - `buyhold_ret`: SPY buy-and-hold return
    - `equity_curve`: cumulative strategy equity (start `1.0`)
    - `buyhold_curve`: cumulative SPY equity (start `1.0`)
    - `drawdown`: strategy drawdown from running peak
    - `buyhold_drawdown`: SPY drawdown from running peak

  FR-050 rules:
    - Execution lag: strict `t -> t+1`.
    - Cash hierarchy: `BIL` first, then `EFFR/252`, then flat `0.02/252`.

6.9 FR-060 Feature Store Artifacts (2026-02-15)
  Required outputs:
    - `data/processed/features.parquet`

  `features.parquet` key columns:
    - `date`: trading session date
    - `permno`: asset id
    - `ticker`: symbol (when available from ticker map)
    - `adj_close`: close used for feature construction
    - `volume`: volume used for flow/liquidity features
    - `rolling_beta_63d`: rolling beta vs market return
    - `resid_mom_60d`: rolling residual momentum
    - `amihud_20d`: rolling Amihud illiquidity
    - `yz_vol_20d`: Yang-Zhang annualized volatility
    - `atr_14d`: ATR-14 (or close-proxy ATR when OHLC unavailable)
    - `rsi_14d`: RSI-14
    - `dist_sma20`: `(close - sma20) / sma20`
    - `sma200`: 200-day simple moving average
    - `trend_veto`: `close < sma200`
    - `z_resid_mom`: cross-sectional z-score leg
    - `z_flow_proxy`: cross-sectional z-score leg for flow
    - `z_vol_penalty`: cross-sectional z-score leg for volatility penalty
    - `composite_score`: `z_resid_mom + z_flow_proxy - z_vol_penalty`
    - `yz_mode`: `true_ohlc|proxy_close_only`
    - `atr_mode`: `true_ohlc|proxy_close_only`

  FR-060 rules:
    - PIT-safe rolling computations only (backward-looking windows).
    - Close-only fallback must be explicit through mode flags.
    - Feature universe selection supports:
      - `universe_mode='yearly_union'` (default): as-of anchored yearly union.
        - let `anchor_date := append_start_ts` for incremental builds, else `start_date`.
        - annual liquidity is computed from rows with `date <= anchor_date`.
        - eligible union years are `year < year(anchor_date)` (bootstrap fallback: `year == year(anchor_date)` only when no prior year exists).
        - top `yearly_top_n` permnos are selected per eligible year and unioned.
      - `universe_mode='global'` (legacy): single global top `top_n` liquidity ranking.
    - Default knobs:
      - `yearly_top_n=100`
      - `top_n=3000` retained for legacy/global mode compatibility.
    - Safety guard:
      - Build must abort when selected yearly-union universe breaches the memory-envelope abort threshold.

6.10 FR-070 Alpha Engine Contract (2026-02-15)
  Module:
    - `strategies/alpha_engine.py`

  Primary interface:
  ```python
  class AlphaEngine:
      def build_daily_plan(
          self,
          features: pd.DataFrame,
          regime_state: str,
          asof_date: pd.Timestamp | None = None,
      ) -> AlphaPlanResult: ...
  ```

  Input schema (minimum):
    - `date`, `permno`
    - `adj_close`, `sma200`, `dist_sma20`
    - `rsi_14d`, `atr_14d`, `yz_vol_20d`
    - `composite_score`, `trend_veto`
    - `adj_close` history is used to derive PIT-safe `prior_50d_high` when absent.

  Structural rules (fixed):
    - Long-only universe gate requires `adj_close > sma200`.
    - Regime state normalization is strict (`strip().upper()`), with unknown tokens fail-safe to `RED`.
    - Regime budgets are fixed:
      - `GREEN -> 1.0`
      - `AMBER -> 0.5`
      - `RED -> 0.0`
    - Final exposure must satisfy:
      - `sum(weights) <= regime_budget`
      - `weights_i >= 0` for all assets.

  Adaptive rules (tunable via walk-forward only):
    - RSI entry gate supports:
      - fixed threshold mode (e.g., 30)
      - rolling percentile mode (e.g., bottom 5% over 252 days)
    - Entry trigger composition:
      - `dip_entry = rsi_gate & (pullback_gate | rsi_cross)`
      - `breakout_entry_green = (regime_state == "GREEN") & (adj_close > prior_50d_high)`
      - `entry = tradable & trend_ok & (dip_entry | breakout_entry_green)`
      - `prior_50d_high` is per-asset rolling 50-day high shifted by one bar (prior-only).
      - If both paths are true, dip reason code takes precedence.
    - ATR stop multiplier supports volatility-aware schedule.
    - Selection depth supports top-N or percentile depth.

  Output fields:
    - `weights`: normalized target weights for selected symbols.
    - `entries`: boolean entry mask.
    - `stop_price`: per-asset stop level (`entry - k*ATR`).
    - `reason_code`: deterministic explainability string.
      - Dip path: `MOM_DIP_<REGIME>_<ADAPT|FIXED>`
      - Breakout path: `MOM_BREAKOUT_GREEN_<ADAPT|FIXED>`
    - `regime_budget` and `budget_utilization`.
    - `alpha_telemetry` fields:
      - `alpha_score`
      - `entry_trigger`
      - `stop_loss_level`
      - `turnover`

  Integration hard rules:
    - Hysteresis:
      - Enter when rank `<= 5`.
      - Hold while rank `<= 20`.
      - Exit when rank `> 20`.
    - Ratchet-only stop:
      - `stop_t = max(stop_{t-1}, price_t - K*ATR_t)`.
    - Portfolio hard cap:
      - `sum(weights_t) <= regime_budget_t`.

  Walk-forward verifier:
    - `backtests/verify_phase15_alpha_walkforward.py`
    - Outputs:
      - `data/processed/phase15_walkforward.csv`
      - `data/processed/phase15_equity_curve.png`
    - Benchmark table:
      - `SPY` vs `Phase13_Governor` vs `Phase15_Alpha`

  FR-070 validation checks:
    - Regime hard-cap invariant always passes.
    - RED regime produces zero exposure.
    - Reason codes are non-empty for all selected names.

6.11 FR-080 Walk-Forward Optimization & Honing Contract (2026-02-15)
  Required outputs:
    - `data/processed/phase16_optimizer_results.csv`
    - `data/processed/phase16_best_params.json`
    - `data/processed/phase16_oos_summary.csv`

  Governance contract (FIX vs FINETUNE):
    - FIX (non-tunable):
      - FR-070 structural rules remain unchanged.
      - Regime budgets and long-only hard-cap invariants remain unchanged.
    - FINETUNE (WFO-tunable):
      - `entry_logic` (`dip`, `breakout`, `combined`)
      - `alpha_top_n`
      - `hysteresis_exit_rank`
      - `rsi_entry_percentile`
      - `atr_multiplier`

  Hard constraints:
    - `hysteresis_exit_rank >= alpha_top_n`.
    - Structural rules are fixed and may not be tuned in FR-080.
    - No OOS leakage:
      - OOS observations cannot participate in objective scoring, ranking,
        or tie-breaks.
      - OOS may only be used as a post-selection promotion gate (`stability_pass`).
    - Promotion selection policy (FR-080 mismatch fix):
      - Build promotable pool first:
        - `stability_pass AND activity_guard_pass`
        - valid train metrics (`objective_score`, `train_cagr`,
          `train_robust_score`, `train_ulcer`)
      - If promotable pool is non-empty, rank only promotable rows by:
        - `objective_score` (desc)
        - `train_cagr` (desc)
        - `train_robust_score` (desc)
        - `train_ulcer` (asc)
        - deterministic parameter tie-breakers:
          `entry_logic`, `alpha_top_n`, `hysteresis_exit_rank`, `adaptive_rsi_percentile`,
          `atr_preset` (ascending).
      - If promotable pool is empty:
        - keep train-only ranked fallback for diagnostics.
        - do not promote any candidate.
    - Phase 16.2 activity guards (strict `>`):
      - `trades_per_year > min_trades_per_year` (default `10.0`).
      - `exposure_time > min_exposure_time` (default `0.30`).
      - Promotion requires both: `stability_pass AND activity_guard_pass`.
      - Activity metrics are computed on the OOS/Test window only.

  Promoted defaults (candidate profile; runtime default only after Phase15 verifier PASS):
    - `alpha_top_n=10`
    - `hysteresis_exit_rank=20`
    - `adaptive_rsi_percentile=0.05`
    - `atr_preset=3.0` mapped to:
      - `atr_mult_low_vol=3.0`
      - `atr_mult_mid_vol=4.0`
      - `atr_mult_high_vol=5.0`

  Operational guardrail:
    - Promoted parameters are not runtime defaults unless Phase15 verifier status is `PASS`.
    - Current rollback defaults:
      - Alpha Engine is disabled by default in runtime/UI.
      - Safer RSI fallback default is `adaptive_rsi_percentile=0.15`.

  Performance controls:
    - Dataset hydration is single-pass per run (load once, reuse for all candidates).
    - Candidate evaluation supports optional multi-process execution:
      - `--max-workers` (`0` = auto core count cap by task count)
      - `--chunk-size`
      - `--disable-parallel`
      - `--progress-interval-seconds`
      - `--progress-path`
      - `--live-results-path`
      - `--live-results-every`
      - `--disable-live-results`
      - `--lock-stale-seconds`
      - `--lock-wait-seconds`
    - Runtime fallback is deterministic:
      - If parallel execution fails, optimizer retries sequentially in-process.
    - Artifact commit safety:
      - Outputs are staged and promoted as a bundle with rollback on promotion failure.
    - Runtime heartbeat artifacts:
      - `phase16_optimizer_progress.json` (status, completed/total, ETA, promotable-so-far, best candidate snapshot)
      - `phase16_optimizer_live_results.csv` (interim candidate table)

  Tournament baseline grid (Phase 16.5):
    - `entry_logic`: `dip`, `breakout`, `combined`
    - `alpha_top_n`: `10`, `20`
    - `hysteresis_exit_rank`: `20`, `30`
    - `adaptive_rsi_percentile`: `0.05`, `0.10`, `0.15`
    - `atr_preset`: `2.0`, `3.0`, `4.0`, `5.0`

  `phase16_optimizer_results.csv` minimum columns:
    - `candidate_id`
    - `train_start`, `train_end`
    - `test_start`, `test_end`
    - `entry_logic`
    - `alpha_top_n`, `hysteresis_exit_rank`
    - `adaptive_rsi_percentile`, `atr_preset`
    - `atr_mult_low_vol`, `atr_mult_mid_vol`, `atr_mult_high_vol`
    - `train_cagr`, `train_sharpe`, `train_max_dd`, `train_ulcer`
    - `test_cagr`, `test_sharpe`, `test_max_dd`, `test_ulcer`
    - `train_robust_score`, `test_robust_score`
    - `sharpe_degradation`, `stability_pass`, `objective_score`
    - `exposure_time`, `trades_per_year`, `activity_guard_pass`
    - `min_trades_per_year_guard`, `min_exposure_time_guard`
    - `selected_flag`, `promoted_flag`

  `phase16_best_params.json` minimum keys:
    - `train_window`
    - `test_window`
    - `strict_mode`
    - `max_sharpe_degradation`, `min_test_sharpe`
    - `min_trades_per_year_guard`, `min_exposure_time_guard`
    - `total_candidates`, `stable_candidates`, `activity_guard_candidates`, `promotable_candidates`, `selection_pool`
    - `selection_pool` values include:
      - `promotable_train_ranked`
      - `train_only_rejected_guardrails`
      - `no_valid_candidates`
    - `selected_activity`
    - `selected`
    - `train_selected`

  `phase16_oos_summary.csv` minimum columns:
    - `train_start`, `train_end`
    - `test_start`, `test_end`
    - selected parameter fields
    - `test_cagr`, `test_sharpe`, `test_ulcer`, `test_max_dd`
    - `stability_pass`, `selection_pool`
    - `exposure_time`, `trades_per_year`, `activity_guard_pass`
    - `min_trades_per_year_guard`, `min_exposure_time_guard`

## Phase 21 Day 1 Addendum: Stop-Loss Module Contract

Scope:
- Standalone module for position stops and portfolio drawdown scaling without OHLC dependency.

Module:
- `strategies/stop_loss.py`

Config contract (`StopLossConfig`):
- `atr_mode`: must be `proxy_close_only`.
- `atr_window`: default `20`.
- `initial_stop_atr_multiple`: default `2.0`.
- `trailing_stop_atr_multiple`: default `1.5`.
- `max_underwater_days`: default `60`.
- drawdown thresholds/scales:
  - `dd_tier1_threshold=-0.08`, `dd_tier1_scale=0.75`
  - `dd_tier2_threshold=-0.12`, `dd_tier2_scale=0.50`
  - `dd_tier3_threshold=-0.15`, `dd_tier3_scale=0.00`
  - `dd_recovery_threshold=-0.04`
- optional safety:
  - `min_stop_distance_abs` (default `0.0`).

Formula contract:
- ATR proxy:
  - `ATR_t = SMA(|close_t - close_{t-1}|, atr_window)`
- Initial stop:
  - `stop_initial = entry_price - initial_stop_atr_multiple * ATR_entry`
- Trailing stop candidate:
  - `stop_trailing_t = price_t - trailing_stop_atr_multiple * ATR_t`
- Ratchet (D-57):
  - `stop_t = max(stop_{t-1}, stop_candidate_t)`
- Time-based forced exit:
  - if underwater and `days_held > max_underwater_days`, exit.
- Portfolio drawdown:
  - `dd_t = (equity_t - peak_equity_t) / peak_equity_t`
  - tier mapping to scaling via thresholds above.

Test contract:
- `tests/test_stop_loss.py` validates:
  - ATR behavior and insufficient-history handling,
  - stage transitions and ratchet non-decreasing invariant,
  - underwater timeout exits,
  - drawdown tier/recovery logic,
  - zero-volatility edge behavior.

## Post-Phase-18 Alignment

Date: 2026-02-20  
Scope: retro-map current repository state to the ideal roadmap checkpoint before new risk-layer promotion.

Alignment mapping (current -> ideal endpoint):
- Data foundation:
  - TRI lake, macro/liquidity layers, and partition-aware feature contracts are implemented.
  - This maps to the ideal pre-risk endpoint where signal and execution data contracts are already stable.
- Strategy baseline:
  - C3 scorecard baseline is locked and auditable (`strategies/production_config.py`).
  - This is treated as the control group for all subsequent risk/execution deltas.
- Governance baseline:
  - SAW workflow, decision logs, and lessons loop are active and enforced.
  - This maps to the ideal endpoint requiring evidence-first promotion discipline before extra complexity.

Retro-enforced gate policy from this point forward:
- No new risk/execution layer may ship without quantified deltas vs latest C3 baseline under:
  - same date window,
  - same `cost_bps`,
  - same `engine.run_simulation` path.
- If promotion gates fail, the layer is blocked/aborted and work pivots to upstream signal quality.

Forward reference:
- Active alignment execution state and roadmap are tracked in `docs/phase19-brief.md`.

## Phase 23 Addendum: SDM Ingestion/Assembly Contract

Date: 2026-02-22  
Scope: lock PIT-safe 3-pillar SDM ingestion path and final feature assembly contract.

Pipelines:
- `scripts/ingest_compustat_sdm.py`:
  - pulls `comp.fundq` + `totalq.total_q`,
  - computes trajectory/intangible features,
  - writes `data/processed/fundamentals_sdm.parquet`.
- `scripts/ingest_frb_macro.py`:
  - pulls `frb.rates_daily`,
  - computes macro cycle derivatives,
  - writes `data/processed/macro_rates.parquet`.
- `scripts/ingest_ff_factors.py`:
  - pulls `ff.fivefactors_daily` (+ momentum),
  - writes `data/processed/ff_factors.parquet`.
- `scripts/assemble_sdm_features.py`:
  - backward `merge_asof` joins fundamentals to macro/factors on `published_at`,
  - writes `data/processed/features_sdm.parquet`.

Critical safety rules:
- PIT anchors:
  - fundamentals availability = `rdq`,
  - Peters & Taylor availability = `datadate + 90 days`.
- `merge_asof` key ordering:
  - must be globally monotonic on timeline key before join.
- Atomic writes:
  - all SDM parquet writes are `tmp -> os.replace`.
- Identifier traceability:
  - allow+audit unmapped `permno` rows via:
    - `data/processed/fundamentals_sdm_unmapped_permno_audit.csv`.

## Phase 25B Addendum: Global Hardware Supply Chain (Osiris)

Date: 2026-02-24  
Scope: lock the public-data fallback macro signal path derived from global non-US hardware fundamentals in `bvd_osiris`.

Data source contract:
- WRDS library and tables:
  - `bvd_osiris.os_fin_ind` (financial statement fields),
  - `bvd_osiris.os_activ_naics12cde` (secondary NAICS),
  - `bvd_osiris.os_gen` (country and core NAICS context).
- Hardware filter:
  - include rows where either core or secondary NAICS starts with `334`:
    - `caics12cod LIKE '334%' OR naics12cde LIKE '334%'`.
- Geography filter:
  - non-US only:
    - `cntrycde <> 'US'`.

Extraction and dedup contract (`data/osiris_loader.py`):
- SQL-level duplication guard:
  - `SELECT DISTINCT` over joined records.
- pandas-level duplication guard:
  - `drop_duplicates(subset=['os_id_number', 'closdate'])`.
- Financial fields:
  - `revenue = COALESCE(data13004, data13002, data13000)`,
  - `inventory = data20010`.
- Base signal formula:
  - `inv_turnover = revenue / inventory`.
- Global daily aggregation:
  - `median_inv_turnover = median(inv_turnover) by closdate`.
- Regional daily aggregation:
  - same metric by `closdate, iso_country` for `TW, KR, DE, JP, CN`.

Alignment and PIT lag contract (`scripts/align_osiris_macro.py`):
- Public reporting lag:
  - `knowledge_date = closdate + 60 days`.
- Daily calendar:
  - business days from `2015-01-01` through run-date `today`.
- Alignment method:
  - `merge_asof(direction='backward')` from daily calendar to `knowledge_date`.
- Daily continuation:
  - forward-fill aligned `median_inv_turnover`.
- 252-day normalization:
  - `z252_t = (x_t - mean_252_t) / std_252_t`,
  - where `x_t = median_inv_turnover_t`.

Validation contract:
- Market target:
  - QQQ 60-trading-day forward return:
    - `fwd_ret_60d_t = Close_{t+60} / Close_t - 1`.
- IC metric:
  - Spearman correlation between `median_inv_turnover_z252` and `fwd_ret_60d`.
- Latest observed evidence (2026-02-24 run):
  - `IC = +0.087636`, `p = 1.18113e-05`, `N = 2492`.

Artifacts:
- `data/processed/osiris_global_hardware_daily.parquet`
- `data/processed/osiris_regional_hardware_daily.parquet`
- `data/processed/osiris_aligned_macro.parquet`

## Phase 29 Addendum: Microstructure Telemetry Contract

Date: 2026-03-01  
Scope: execution-quant instrumentation at broker/orchestrator seam for arrival anchoring, partial-fill VWAP, deterministic slippage, and latency decomposition.

### Command-time arrival anchor (`main_console.py`)
- For each seeded `Sovereign_Command` row, capture:
  - `arrival_ts`: UTC timestamp at command generation (`ms` precision).
  - `arrival_quote_ts`: broker quote timestamp when available.
  - `arrival_bid_price`, `arrival_ask_price`.
  - `arrival_price`: midpoint at command-time quote snapshot.
- Midpoint formula:
  - `arrival_price = (arrival_bid_price + arrival_ask_price) / 2`.

### Broker execution telemetry (`execution/broker_api.py`)
- Submit path captures:
  - `submit_sent_ts`, `broker_ack_ts`.
  - order lifecycle fields (`created_at`, `submitted_at`, `updated_at`, `filled_at`, `filled_qty`, `filled_avg_price`).
- Partial-fill extraction:
  - primary: broker activity feed rows (`FILL`) filtered to the same `order_id`.
  - fallback: snapshot-level synthetic fill from `filled_qty` + `filled_avg_price` when activity rows are unavailable.
- Fill summary fields:
  - `fill_count`, `fill_qty`, `fill_notional`, `fill_vwap`, `first_fill_ts`, `last_fill_ts`.

### Deterministic execution-cost formulas (`execution/microstructure.py`)
- Partial-fill VWAP per `client_order_id`:
  - `VWAP_fill = sum(fill_price_i * fill_qty_i) / sum(fill_qty_i)`.
- Buy implementation shortfall:
  - `IS_buy = (VWAP_fill - arrival_price) * fill_qty`.
- Sell implementation shortfall (sign-normalized to cost):
  - `IS_sell = (arrival_price - VWAP_fill) * fill_qty`.
- Slippage in basis points (cost-positive convention):
  - `slippage_bps = ((signed_delta) / arrival_price) * 10,000`,
  - where `signed_delta = VWAP_fill - arrival_price` for buys,
  - and `signed_delta = arrival_price - VWAP_fill` for sells.
- Baseline cohort alignment (`scripts/evaluate_execution_slippage_baseline.py`):
  - intended-cohort denominator is total rows, not observed-only rows.
  - `cohort_slippage_bps_i = slippage_bps_i` when observed, else `0.0` for no-fill/uncaptured rows.
  - non-finite numeric inputs are sanitized before aggregation:
    - `sanitize(x) = x if isfinite(x) else null`.
  - aggregate baseline uses `cohort_slippage_bps`:
    - `mean_slippage_bps = mean(cohort_slippage_bps)`,
    - `median_slippage_bps = median(cohort_slippage_bps)`.
  - observability counters are still emitted:
    - `observed_rows`, `zero_imputed_rows`.

### Latency decomposition (`execution/microstructure.py`)
- `latency_ms_command_to_submit = submit_sent_ts - arrival_ts`.
- `latency_ms_submit_to_ack = broker_ack_ts - submit_sent_ts`.
- `latency_ms_ack_to_first_fill = first_fill_ts - broker_ack_ts`.
- `latency_ms_command_to_first_fill = first_fill_ts - arrival_ts`.

### Adaptive heartbeat freshness (`execution/microstructure.py`)
- Scope:
  - execution heartbeat freshness is evaluated from rolling `latency_ms_submit_to_ack` observations without look-ahead.
- Rolling baseline:
  - `history_t = {latency_{t-k}, ..., latency_{t-1}}` with window size `N=64`.
  - cross-batch bootstrap history must be ordered by explicit event-time (coalesced timestamp columns), not append order / row id.
  - `median_t = median(history_t)`.
  - `MAD_t = median(|history_t - median_t|)`.
  - `robust_sigma_t = max(1.4826 * MAD_t, 5.0 ms)`.
- Adaptive limit:
  - when `len(history_t) >= 12`:
    - `adaptive_limit_t = median_t + 4.0 * robust_sigma_t`.
  - bootstrap fallback (insufficient history):
    - `adaptive_limit_t = 150.0 ms`.
  - clamp:
    - `adaptive_limit_t = clip(adaptive_limit_t, 25.0 ms, hard_ceiling_ms)`.
- Hard ceiling:
  - `hard_ceiling_ms = env(TZ_EXEC_HEARTBEAT_HARD_CEILING_MS, default=500.0)`.
- Deterministic decision:
  - `BLOCK` if `latency_ms_submit_to_ack` is missing.
  - `BLOCK` with `reason=hard_ceiling_exceeded` if `latency > hard_ceiling_ms`.
  - `BLOCK` with `reason=adaptive_limit_exceeded` if `latency > adaptive_limit_t`.
  - otherwise `PASS`.
- Persisted telemetry fields:
  - `heartbeat_decision`, `heartbeat_reason`,
  - `heartbeat_is_blocked`, `heartbeat_is_hard_block`,
  - `heartbeat_mode`, `heartbeat_window_count`,
  - `heartbeat_window_median_ms`, `heartbeat_window_mad_ms`, `heartbeat_robust_sigma_ms`,
  - `heartbeat_adaptive_limit_ms`, `heartbeat_hard_ceiling_ms`,
  - `heartbeat_latency_ms`, `heartbeat_latency_zscore`.

### Post-trade sink
- Order-level sink:
  - `data/processed/execution_microstructure.parquet`
  - `data/processed/execution_microstructure.duckdb` table `execution_microstructure`
- Fill-level sink:
  - `data/processed/execution_microstructure_fills.parquet`
  - DuckDB table `execution_microstructure_fills`
- Persistence wiring:
  - local submit path (`main_console.py`) persists telemetry immediately after helper returns and fails closed if telemetry write fails.
- Backfill + baseline evaluation runners:
  - `scripts/backfill_execution_latency.py`:
    - deterministic historical annotation of heartbeat freshness columns into
    - `data/processed/execution_microstructure_latency_backfill.parquet`,
    - plus summary JSON `data/processed/execution_microstructure_latency_backfill_summary.json`.
  - `scripts/evaluate_execution_slippage_baseline.py`:
    - baseline signed-slippage report outputs:
    - `data/processed/execution_slippage_baseline_summary.json`,
    - `data/processed/execution_slippage_baseline_by_side.csv`,
    - `data/processed/execution_slippage_baseline_by_symbol.csv`.
  - Source-of-truth loader contract (Option 2 fail-loud):
    - default mode is strict DuckDB primary sink:
      - `source_mode = duckdb_strict`.
      - if DuckDB file is missing/unreadable/query-failing, scripts raise `PrimarySinkUnavailableError` (no implicit parquet fallback).
    - explicit parquet override is opt-in only:
      - CLI: `--source-mode parquet_override`
      - env override: `TZ_EXEC_TELEMETRY_SOURCE_MODE=parquet_override`
    - unsupported mode tokens are rejected (`ValueError`).

## Phase 30 Addendum: Release Engineering / MLOps Deterministic Pipeline

Date: 2026-03-01  
Scope: immutable image artifacts, deterministic promotion, and automatic N-1 rollback tied to startup diagnostics.

### Immutable artifact contract
- Deployable unit is a digest-locked container reference:
  - `release_ref = "<repo>:<tag>@sha256:<64-hex>"`
- Runtime release metadata schema:
  - `core/release_metadata.py` (`ReleaseRecord`, `ReleaseMetadata`)
- Canonical state artifact:
  - `data/processed/release_metadata.json`

### Promotion and rollback controller
- Controller:
  - `scripts/release_controller.py`
- Required sequence:
  1. stage candidate (`status=pending_probe`),
  2. run startup probe (docker mode deploy + startup watch),
  3. finalize:
     - `status=active` on success,
     - `status=rolled_back` when restore N-1 is verified on failure,
     - `status=rollback_failed` when restore N-1 cannot be verified.
- External probe safety gate:
  - `--mode external-probe` requires explicit `--allow-external-probe-promote` acknowledgement.
  - This mode is only valid when runtime deploy/rollback is managed outside `scripts/release_controller.py`.
- Atomicity:
  - metadata writes use `tmp -> fsync -> os.replace`.

### Startup containment wiring
- Docker mode deploy probe:
  - starts candidate service container with:
    - `TZ_RELEASE_DIGEST=<candidate_digest>`
  - monitors startup watch window,
  - if candidate exits during watch, controller:
    - removes candidate container,
    - starts previous known-good release image automatically.

### UI cache governance formula
- Cache fingerprint is release-bound:
  - `cache_fingerprint = "<version>@sha256:<release_digest|local-dev>"`
- Implementation path:
  - `core/release_metadata.py` (`build_release_cache_fingerprint`)
  - `dashboard.py` (`_release_bound_cache_version`)

## Phase 29.1 Addendum: Stream 5 Option 2 Production Patch

Date: 2026-03-01  
Scope: execution submit/recovery semantics hardening for terminal unfilled outcomes, latency-anchor recovery backfill, drift-safe latency decomposition, and signed slippage assertions.

### Local-submit acceptance contract
- Terminal unfilled outcomes are non-accepted:
  - `terminal_unfilled := status in {canceled, cancelled, rejected, expired} AND fill_qty <= 0`.
  - `accepted_local_submit := (ok is True) AND NOT terminal_unfilled`.
- Fail-closed behavior:
  - when `terminal_unfilled` is true, emit `ok=False` with deterministic error:
  - `error = "terminal_unfilled:<status>"` (or existing explicit error if present in orchestrator row).
- Implementation path:
  - `execution/broker_api.py` (`_is_terminal_unfilled_result`, `_normalize_submit_acceptance`)
  - `main_bot_orchestrator.py` (`_is_terminal_unfilled_execution_result`, retry loop fail-closed branch)

### Recovery latency-anchor backfill contract
- For recovery payloads (client-order-id lookup), anchor fields are backfilled from broker lifecycle timestamps:
  - `submit_sent_ts := submit_sent_ts || submitted_at || created_at || updated_at`
  - `broker_ack_ts := broker_ack_ts || updated_at || submitted_at || created_at`
  - where `||` means first non-empty value.
- Implementation path:
  - `execution/broker_api.py` (`_backfill_latency_anchors`)
  - `execution/microstructure.py` (`_resolve_latency_anchors`)

### Clock-drift guard contract
- Latency decomposition is fail-closed against negative wall-clock deltas:
  - `latency_ms = max(0, (t_end - t_start) * 1000)`.
- Applies to:
  - command-to-submit,
  - submit-to-ack,
  - ack-to-first-fill,
  - command-to-first-fill.
- Implementation path:
  - `execution/microstructure.py` (`_ms_diff`)

### Slippage sign-preservation contract
- Slippage retains directional sign and must not be absolute-value coerced:
  - buy: `delta = fill_vwap - arrival_price`
  - sell: `delta = arrival_price - fill_vwap`
  - `slippage_bps = (delta / arrival_price) * 10,000`
- Expected behavior:
  - favorable execution => negative slippage,
  - parity execution => zero slippage.
- Validation path:
  - `tests/test_execution_microstructure.py` (negative and zero slippage assertions)

3.35 Sovereign Execution Hardening [Phase 31] <- NEW
[FR-150 Step Set: Trust Boundary + Telemetry Durability]
    - Objective:
      - eliminate replay-race, spool-corruption, and semantic-coercion fail-open pathways.
    - Hard contracts:
      - signed envelope replay check+append executes atomically under lock,
      - malformed replay rows are quarantined (`.malformed.jsonl`) with valid-ledger rewrite,
      - spool replay is idempotent with deterministic UID,
      - schema-invalid and stale trailing-partial spool lines are quarantined (`.bad`) with cursor progress,
      - local-submit path must pass bounded telemetry durability gate before success/notify.
    - Semantic guards:
      - `trend_veto`/quality flags use tokenized boolean normalization,
      - `composite_score` selection is numeric + stable tie-break,
      - malformed dates in ticker ranking are explicit fail-fast errors.
    - Verification matrix:
      - targeted integrated pytest matrix + compile gate required for stream close.

### Stream 5 Option 2 Reconciliation Addendum (2026-03-01)

#### Terminal status fail-closed refinement
- Terminal statuses (execution seam):
  - `{canceled, cancelled, rejected, expired, done_for_day, stopped, suspended}`.
- Unfilled terminal rule:
  - `terminal_unfilled := terminal_status AND fill_qty <= 0` -> final `ok=False`, non-retry.
- Partial-fill terminal rule:
  - `terminal_partial := terminal_status AND fill_qty > 0` -> final `ok=False`, non-retry.

#### Telemetry row consistency refinement
- If `partial_fills` is empty but aggregate fill summary is present (`fill_count>0`, `fill_qty>0`, `fill_vwap>0`), telemetry must emit a synthesized fill row so order/fill tables stay join-consistent.
- Synthesized row contract:
  - `fill_source = summary_fallback`.

#### Legacy parquet replay safety refinement
- Legacy single-file parquet dedupe must preserve historical rows with missing dedupe keys.
- Null-safe key rule:
  - for each key in `{record_id, uid, _spool_record_uid}` dedupe only records with non-empty key values and preserve null/empty-key rows.
