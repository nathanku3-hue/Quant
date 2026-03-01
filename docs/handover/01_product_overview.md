TERMINAL ZERO — PM HANDOVER DOCUMENT
Part 1 of 4: Product Overview and System Architecture
Date: 2026-02-20 | Status: Active | Current Phase: 21 (Stop-Loss Module)
Author: Atomic Mesh

================================================================================
1. WHAT THIS PRODUCT IS
================================================================================

Terminal Zero is a local-first quantitative research platform that turns raw
market data into daily, actionable buy/sell/hold decisions for a stock portfolio.
It is NOT a trading bot. It is a research cockpit that tells a human operator
what to do, why, and with what confidence.

Core philosophy: "The Pilot's Checklist." Every signal is derived from
observable, verifiable data. Nothing is a black box. Every number is traceable
to a formula in the codebase.

Current maturity: Research-grade. The system runs daily on a local Windows
machine, processes up to 3,000 stocks, and outputs a ranked action report. Live
trading integration is explicitly deferred to Phase 22.

================================================================================
2. WHAT PROBLEMS IT SOLVES
================================================================================

Problem A — Data quality: Raw CRSP/WRDS data ends in 2024. Yahoo Finance is
live but unreliable. Solution: Hybrid "Bedrock + Fresh Snow" architecture. The
47-million-row WRDS base is never modified. Yahoo data is appended as a patch
file and merged at query time via DuckDB UNION ALL.

Problem B — Look-ahead bias: Any backtest that uses today's signal to trade
today is lying. Solution: The simulation engine enforces a mandatory one-day
execution lag (shift-1). This is hard-coded and cannot be disabled.

Problem C — Overfitting: A strategy that looks great in-sample is worthless.
Solution: Walk-forward optimization with strict train/test isolation. Out-of-
sample data cannot participate in parameter selection, only in pass/fail gates.

Problem D — Regime blindness: A strategy that treats a 2008 crash the same as
a 2017 bull run is dangerous. Solution: A two-layer Regime Governor (veto) plus
Throttle (sizing) system that adjusts portfolio exposure to 0%, 50%, or 100%
of capital based on macro stress signals.

Problem E — Signal noise: Dip-buying without quality filters catches falling
knives. Solution: A Point-in-Time (PIT) fundamentals quality gate. A stock only
qualifies if its most recently PUBLISHED financials show ROIC > 0 and Revenue
growth > 0. Stale or missing data defaults to disqualified.

================================================================================
3. SYSTEM LAYERS (STRICT TOP-DOWN)
================================================================================

The system is composed of six strictly isolated layers. Each layer can only
consume outputs from the layer below it, never the reverse.

Layer 1 — DATA LAKE (The Bedrock)
  Input:  3.7 GB CRSP CSV, Yahoo Finance API, FRED API, Compustat CSV
  Output: Parquet files in data/processed/
  Key files:
    prices.parquet          — 47M rows, 2000-2024, WRDS base, never modified
    yahoo_patch.parquet     — Live extension from 2025 onward
    fundamentals.parquet    — 215K rows, PIT-safe quarterly financials
    macro_features.parquet  — Daily macro regime signals (VIX, SOFR, credit)
    liquidity_features.parquet — Fed balance sheet + repo market signals
    features.parquet        — 2.5M rows, stock-level alpha feature vectors

Layer 2 — COMPUTE ENGINE (engine.py)
  Input:  Target weight matrix (dates x stocks), returns matrix
  Output: Gross return, net return, turnover, cost per day
  Key rule: Weights on day T are executed on day T+1. 10 basis points
  transaction cost is deducted on every portfolio change.

Layer 3 — STRATEGY LAYER (The Cartridges)
  Three pluggable strategy modules, each returning (weights, regime, details):
    adaptive_trend.py     — Legacy 3-state regime strategy
    investor_cockpit.py   — Primary production strategy (see Part 2)
    alpha_engine.py       — FR-070 stock selector + sizer (see Part 2)

Layer 4 — REGIME MANAGER (regime_manager.py)
  Input:  macro_features.parquet, liquidity_features.parquet
  Output: Governor state (GREEN/AMBER/RED), Throttle state (POS/NEUT/NEG),
          target exposure scalar 0.0 to 1.3
  This layer vetoes the entire strategy. If it says RED, no positions are held
  regardless of how good the stock signals look.

Layer 5 — OPTIMIZER (optimizer.py, backtests/)
  Input:  Historical price and return data
  Output: Validated parameter sets for strategy knobs
  Key rule: ONLY train-window data is used for selection. Test-window is
  read-only for promotion gates.

Layer 6 — APPLICATION (app.py, Streamlit dashboard)
  Input:  All of the above
  Output: Web dashboard with four tabs:
    Investor Cockpit  — Daily action report, stop levels, buy zones
    Lab / Backtest    — Historical equity curve
    Optimizer         — 2D heatmap parameter sweep
    Data Manager      — Data freshness and update controls

================================================================================
4. DATA CONTRACTS (NON-NEGOTIABLE RULES)
================================================================================

Rule D-01: Delisting bias is corrected. When a stock is delisted, its
delisting return (often -100%) is merged into the total_ret column.
Without this, backtests overstate performance by ignoring bankruptcies.

Rule D-02: Two separate price columns exist for different purposes.
adj_close is used ONLY for signal generation (MA crossovers, RSI, Z-scores).
total_ret is used ONLY for PnL computation. Mixing these causes the Split Trap
where corporate actions create false signals.

Rule D-04: Execution lag is mandatory. Signal on day T, execution on day T+1.
This is enforced in engine.py and cannot be bypassed.

Rule D-05: Transaction costs are always charged. 10 basis points per unit of
portfolio turnover. This prevents strategies that look great but churn
constantly.

Rule D-21: The WRDS base file is never modified. Yahoo Finance data is
always stored in a separate patch file and merged at query time.

================================================================================
5. WHAT IS COMPLETE vs. IN PROGRESS vs. DEFERRED
================================================================================

COMPLETE (production-locked):
  Phases 1-18: ETL, engine, strategy, optimizer, feature store, regime manager,
  walk-forward backtests, TRI migration, company scorecard (C3 configuration).
  The C3 integrator config is locked in strategies/production_config.py.

IN PROGRESS (Phase 19-21, current sprint):
  Phase 19: Alignment and evidence discipline sprint. Scorecard signal quality
  is being strengthened. Three sub-sprints have run (19.5, 19.6, 19.7). All
  three were aborted because improving coverage regressed spread or destroyed
  crisis-period turnover protection. Current status: BLOCKED pending diagnostics.
  Phase 21: Stop-loss module (strategies/stop_loss.py) is built and tested.
  It is NOT yet wired into the live execution path. Delta gate test showed
  the fixed ATR stops (2.0/1.5) destroyed Sharpe and exploded turnover 4.3x
  with the current weak signal. Stop-loss wiring is BLOCKED until signal
  quality improves.

DEFERRED (future phases):
  Phase 20: Adaptive stop-loss with regime and conviction weighting.
  Phase 21 (full): Stop-loss wiring into production execution path.
  Phase 22: Live cockpit, auto-SAW stub, 30-day live simulation.
  Phase 23+: New factor families, ensemble models, alternative data.

================================================================================
END OF PART 1
================================================================================


================================================================================
PART 2 — ALGORITHMS AND METHODOLOGY
================================================================================

A. SIMULATION ENGINE (engine.py — single function, ~50 lines)
--------------------------------------------------------------------------------
This is the only place PnL is calculated. The formula is:

  executed_weights = target_weights.shift(1).fillna(0)    # lag by 1 day
  gross_ret = (executed_weights * aligned_returns).sum(axis=1)
  turnover  = executed_weights.diff().abs().sum(axis=1)
  net_ret   = gross_ret - (turnover * cost_bps)

Three invariants enforced here and nowhere else:
  1. shift(1)        — no look-ahead. Signal dated T executes at open T+1.
  2. matrix align    — returns matrix reindexed to weights shape, missing = 0.
  3. turnover tax    — cost_bps (default 10 bps) charged on absolute weight change.

B. REGIME MANAGER (regime_manager.py — FR-041)
--------------------------------------------------------------------------------
The governor decides how much capital the strategy is ALLOWED to deploy.
It runs BEFORE stock selection and its veto is absolute.

Inputs (from macro_features.parquet):
  vix_level, vix_trend_5d, net_liquidity (Fed balance sheet delta), sofr_rate,
  credit_spread, market_momentum (SPY vs SMA200)

Step 1 — Governor state (3-way veto):
  GREEN  = trend positive AND VIX < stress threshold AND liquidity not contracting
  AMBER  = trend weakening OR VIX elevated OR liquidity borderline
  RED    = trend negative OR VIX > crisis threshold OR liquidity crisis signal

Step 2 — Throttle state (market momentum):
  POS / NEUT / NEG based on rolling Z-score of SPY momentum

Step 3 — BOCPD changepoint detection (lightweight Bayesian surprise):
  Estimates probability of a structural break in net liquidity.
  Formula: one-step prediction error standardized vs. rolling 63-day window.
  Hazard rate = 1/126 (~6-month average regime duration assumed).
  Output blended at weight 0.25 into throttle score.

Step 4 — Matrix exposure lookup:
  (Governor x Throttle) -> scalar in [0.0, 1.3]
  RED+any = 0.0, AMBER+NEG = 0.25, AMBER+NEUT = 0.50, GREEN+POS = 1.0-1.3

C. STOCK SIGNAL GENERATION (investor_cockpit.py)
--------------------------------------------------------------------------------
Per-stock signals run daily on a rolling window of price + fundamentals.

C1. Dynamic parameter mapping (FR-019):
  Each stock gets its own k (stop width) and z (entry threshold) based on
  where its 20-day volatility ranks cross-sectionally that day.
  High-vol stocks get wider stops and stricter entry thresholds.
  Low-vol stocks get tighter stops and looser entry thresholds.

C2. Entry signals — two modes:
  DIP mode: robust Z-score < -z_entry threshold (price below recent median-MAD band)
  BREAKOUT mode: Kaufman Efficiency Ratio > 0.6 AND price making new highs
  COMBINED mode (default): stock qualifies if either signal fires

  Robust Z-score formula (resists fat-tail crashes):
    z = (price - rolling_median) / (1.4826 * rolling_MAD)
  The 1.4826 factor makes MAD equivalent to std under normality.

  Kaufman Efficiency Ratio (trend quality filter):
    ER = |net_price_change_over_window| / sum(|daily_price_changes|)
    ER near 1.0 = clean trend. ER near 0.0 = random walk / choppy.

C3. Quality gate (Point-in-Time fundamentals):
  A stock FAILS the gate if its latest PUBLISHED quarterly report shows:
    ROIC <= 0, OR Revenue growth <= 0, OR data is missing
  Gate uses published_at <= as_of_date to prevent future data leakage.
  Missing data defaults to FAIL (conservative).

C4. Earnings blackout:
  Stocks within 5 days before or after an earnings date are excluded.
  Prevents entering positions into binary event risk.

C5. Macro defense scaling:
  macro_score in [0.0, 2.0] maps to position weight scalar.
  If regime says AMBER, max position weight is halved.
  If regime says RED, all weights go to 0 regardless of signal.

D. ALPHA ENGINE (alpha_engine.py — FR-070)
--------------------------------------------------------------------------------
The Alpha Engine is an alternative selector that uses the pre-computed
feature store instead of computing signals inline. It runs on top of the
regime manager output.

Selection pipeline (daily, deterministic):
  1. Trend gate: stock must have close > SMA200 (or trend_veto=False)
  2. Liquidity gate: 20-day avg dollar volume >= 10M USD
  3. Conviction score: cross-sectional Z-score of composite alpha features
  4. Top-N selection: pick top 5 stocks by conviction (configurable)
  5. Conviction boost: stocks with score > 2.0 get weight scaled up by 1.2x
  6. ATR-based position sizing:
       ATR multiplier adapts to market volatility regime:
         low_vol  (<20 VIX): 3.0x ATR
         mid_vol  (20-30):   4.0x ATR
         high_vol (>30 VIX): 5.0x ATR
       Wider stops in high-vol environments = smaller position sizes.
  7. Max position cap: 35% of portfolio in any single stock.
  8. Budget scaling: all weights multiplied by regime exposure scalar (0.0-1.3).

================================================================================
END OF PART 2 BATCH 1
================================================================================

E. FEATURE STORE (data/feature_store.py — FR-060)
--------------------------------------------------------------------------------
Builds 2.5M-row features.parquet that the Alpha Engine consumes every run.
Uses DuckDB for in-process SQL against parquet files (no server needed).

Universe selection:
  All stocks ranked by annual average dollar volume.
  Top 3,000 by global liquidity, OR top 100 per year (union mode, default).
  This gives survivorship-bias-free coverage across time.

Feature computation pipeline (runs daily, per stock, vectorized):
  Momentum features:
    resid_mom_60d   — 60-day residual return after beta-hedging vs SPY
    rel_strength_60d — stock return minus equal-weight universe return
  Technical features:
    rsi_14          — 14-day Relative Strength Index
    atr_14          — 14-day Average True Range (proxy: |close_t - close_t-1|)
    sma_20, sma_200 — Simple moving averages; trend filter = close > sma_200
  Liquidity features:
    amihud_20       — Amihud illiquidity = |return| / dollar_volume, 20-day avg
  Volatility features:
    yang_zhang_20   — Yang-Zhang volatility estimator (OHLC-based, 20-day)
  Fundamental features (joined from fundamentals.parquet, PIT-safe):
    z_inventory_quality_proxy — continuous proxy gate (see formula below)
    z_discipline_cond         — asset discipline conditional score

  Inventory Quality Proxy formula (D-82):
    sales_accel_q     = delta(pct_change(revenue_q, 1))
    op_margin_accel_q = delta(operating_margin_delta_q)
    bloat_q           = delta(ln(total_assets - inventory)) - delta(ln(revenue))
    net_investment_q  = (|capex_q| - depreciation_q) / lag(total_assets_q)
    z_proxy = z(sales_accel) + z(op_margin_accel) - z(bloat) - 0.5*z(net_invest)
    If z_proxy > 0: discipline penalty is waived (cyclical build is OK).

Storage: partitioned by year/month for fast incremental upsert.
PIT safety: all fundamental joins use published_at <= as_of_date.
Schema drift guard: if required columns go missing, forces full rewrite.

F. COMPANY SCORECARD (strategies/company_scorecard.py — Phase 18 Day 4)
--------------------------------------------------------------------------------
The scorecard is a linear multi-factor model. It runs on the feature store
and produces a daily cross-sectional score per stock.

Formula: score = sum(weight_k * sign_k * normalize(factor_k))
  where sign_k = +1 if factor direction is "positive", -1 if "negative"
  and normalize() is cross-sectional z-score (or rank percentile in stress)

Locked production configuration (C3 — ABLATION_C3_INTEGRATOR):
  Factor 1: z_inventory_quality_proxy  weight=1.0  direction=positive
  Factor 2: z_discipline_cond          weight=1.0  direction=positive
  Factor 3: resid_mom_60d              weight=1.0  direction=positive
  Factor 4: amihud_20                  weight=1.0  direction=negative
  Scoring method: complete_case (stock excluded if ANY factor is missing)
  Decay: 0.95 (scores exponentially weighted toward recent)

Regime-adaptive normalization (Phase 19.6):
  GREEN regime: z-score normalization (assumes returns are approximately normal)
  AMBER/RED regime: rank percentile mapped to [-1, 1] (non-parametric, robust)

RED veto (strict_red_veto=True):
  In RED regime, ALL scores are forced to 0. No stock scores positively.
  This is a hard rule, not a soft penalty.

Phase 18 Day 5 result that locked C3:
  Baseline (Day 4 equal-weight all factors): Sharpe 0.764, turnover 64.9/yr
  C3 integrator (ablated to 4 factors + decay): Sharpe 1.007, turnover 19.8/yr
  C3 is 31% higher Sharpe and 70% lower turnover. Locked as production baseline.

G. STOP-LOSS MODULE (strategies/stop_loss.py — Phase 21 Day 1)
--------------------------------------------------------------------------------
Built and tested. NOT yet wired into live execution. Blocked by signal quality.

ATR proxy (close-only, no OHLC needed):
  ATR_t = SMA(|close_t - close_t-1|, window=20)

Two-stage stop with ratchet (D-57):
  Stage 1 — Initial stop:
    stop_initial = entry_price - 2.0 * ATR_at_entry
  Stage 2 — Trailing stop (activates after position is profitable):
    stop_trailing_t = price_t - 1.5 * ATR_t
  Ratchet invariant: stop_t = max(stop_t-1, stop_trailing_t)
  The stop can ONLY move up, never down. Locks in gains.

Time-based forced exit:
  If position is underwater for more than 60 consecutive days, exit.
  Prevents "bagholding" on broken thesis stocks.

Portfolio drawdown circuit breaker (3 tiers):
  Tier 1: portfolio DD <= -8%  -> scale all positions to 75%
  Tier 2: portfolio DD <= -12% -> scale all positions to 50%
  Tier 3: portfolio DD <= -15% -> scale all positions to 0% (full cash)
  Recovery: DD recovers above -4% -> restore 1 tier at a time

Phase 21 Day 1 gate result (why stop-loss is blocked):
  C3 Sharpe: 1.007  ->  C3+Stops Sharpe: 0.382  (delta = -0.625, FAIL)
  Turnover annual: 19.8  ->  84.9  (4.3x increase, FAIL)
  Root cause: fixed ATR stops thrash positions when signal is weak.
  Decision: stops only help when signal conviction is high. Fix signal first.

================================================================================
PART 3 — VALIDATION GATES AND EVIDENCE DISCIPLINE
================================================================================

Every feature/change must pass a quantitative gate before it is promoted.
These gates are non-negotiable. Advisory passes are documented but do not
override the gate decision for risk-layer changes.

ACCEPTANCE GATES (Phase 18 locked C3 baseline as control):
  Sharpe delta:    new_Sharpe >= C3_Sharpe - 0.03       (C3 = 1.007)
  Turnover delta:  new_Turnover <= C3_Turnover * 1.15   (C3 = 19.8/yr)
  MaxDD delta:     new_MaxDD <= C3_MaxDD + 0.03         (absolute)
  Crisis gate:     turnover reduction >= 70% in ALL crisis windows:
                     COVID crash, COVID vol, Inflation spike, 2022 bear

DECISION RULE: 3/4 gates pass = PROMOTE. 2+ failures = ABORT and pivot.

CROSS-SECTIONAL ACCEPTANCE GATES (signal quality, from Phase 17):
  Quartile spread sigma >= 2.0  (top quartile beats bottom by 2 sigma)
  Coverage >= 80%               (80% of universe has valid scores)
  Newey-West t-stat >= 3.0      (spread is statistically significant)
  Fama-MacBeth beta positive and significant (p < 0.05)

WALK-FORWARD PROTOCOL (anti-overfitting):
  Train window: e.g. 2015-2021. Parameters selected on this window only.
  Test window: 2022-2024. Read-only. Used only to pass/fail promotion.
  Degredation limit: test_Sharpe >= train_Sharpe * 0.88 (max 12% decay).
  Activity guard: >= 12 trades/year AND >= 30% exposure time in test window.

PARAMETER SWEEP ANTI-GAMING (Phase 17.2B):
  CSCV (Combinatorially Symmetric Cross-Validation): splits data into S=6
  blocks, tests all C(S, S/2) = 10 possible train/test splits. PBO
  (Probability of Backtest Overfitting) must be < 0.5 for promotion.
  DSR (Deflated Sharpe Ratio): adjusts for number of trials tested.
  Effective trials N_eff = N * (1 - avg_correlation) + 1.
  Best variant selected by DSR first, then Newey-West t-stat, then mean.

================================================================================
PART 4 — CURRENT STATUS, BLOCKERS, AND FORWARD ROADMAP
================================================================================

CURRENT STATUS (as of 2026-02-20):
  Production baseline: C3 integrator locked (strategies/production_config.py)
  Signal quality: BELOW target. Coverage ~52%, quartile spread < 2.0 sigma.
  Stop-loss: Built, tested, NOT wired. Blocked by signal weakness.
  Phase 19 sprints 19.5, 19.6, 19.7 all ABORTED due to regressions.

ACTIVE BLOCKERS:
  Blocker 1 — Signal spread insufficient:
    Current quartile spread < 2.0 sigma. Target 2.0+.
    Three sprint attempts (19.5, 19.6, 19.7) all improved one metric while
    regressing another. Root cause: factors are partially correlated. Adding
    a new factor steals weight from existing factors instead of adding info.
    Next action: orthogonality audit to find non-redundant factor candidates.

  Blocker 2 — RED regime veto fidelity:
    Backtests show positions held in RED regime windows. Strict RED veto
    is coded but not consistently enforced in all code paths.
    Next action: audit all weight generation paths for RED bypass.

  Blocker 3 — Stop-loss wiring dependency:
    Stop-loss module is ready but wiring it with weak signal produces turnover
    explosion (19.8 -> 84.9/yr). Must fix signal first. Stop-loss wiring is
    formally deferred until signal gates pass.

FORWARD ROADMAP:
  Phase 19 (current): Fix signal quality. Gate: coverage >= 85%, spread >= 2.1.
  Phase 20 (next):    Adaptive stop-loss (regime/conviction weighted K values).
  Phase 21 (full):    Wire stops into production execution path.
  Phase 22:           Live cockpit, 30-day live simulation, end-to-end < 50s.
  Phase 23+:          New factor families, alternative data, ensemble models.

KEY LESSONS LEARNED:
  L1: Never add risk layers before signal quality is proven.
      Adding stops to a weak signal creates whipsaw and turnover explosion.

  L2: Complete-case scoring beats imputation for factor models.
      Stocks with missing factors should be excluded, not zero-filled.
      Zero-fill dilutes the signal from stocks that do have data.

  L3: PIT (Point-in-Time) semantics are non-negotiable.
      Any fundamental data joined without published_at <= as_of_date
      is future data leakage and makes backtests meaningless.

  L4: Turnover and Sharpe must be evaluated together.
      A strategy with Sharpe 1.5 but 200/yr turnover is worse than
      Sharpe 1.0 with 20/yr turnover at 10 bps cost assumption.

  L5: Crisis turnover reduction is the key risk metric, not just MaxDD.
      The regime system's value is that it STOPS TRADING in crashes.
      If crisis turnover reduction < 70%, the regime system is not working.

  L6: Overfitting is silent. Always use out-of-sample gates.
      PBO > 0.5 on any parameter sweep means the best result is luck.

  L7: Windows-specific issues require Windows-specific fixes.
      os.kill(pid, 0) silently kills the process on Windows. Use
      OpenProcess + GetExitCodeProcess for PID liveness checks.

KEY FILES FOR HANDOVER:
  strategies/production_config.py   — locked C3 production configuration
  strategies/stop_loss.py           — stop-loss module (built, not wired)
  strategies/company_scorecard.py   — scorecard engine
  strategies/regime_manager.py      — regime governor (FR-041)
  strategies/alpha_engine.py        — stock selector (FR-070)
  strategies/investor_cockpit.py    — primary strategy
  data/feature_store.py             — feature pipeline (FR-060)
  data/feature_specs.py             — declarative feature registry
  engine.py                         — simulation kernel (SSOT for PnL)
  docs/decision log.md              — full decision history (D-01 to D-101)
  docs/lessonss.md                  — lessons and guardrails log
  docs/phase21-brief.md             — active sprint state
  AGENTS.md                         — governance rules for all AI agents

================================================================================
END OF HANDOVER DOCUMENT
File: docs/handover/01_product_overview.md
Date: 2026-02-20 | Author: Atomic Mesh | Status: Complete
================================================================================
