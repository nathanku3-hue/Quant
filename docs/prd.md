G7.1A Canonical Notice (2026-05-09)

The current product canon is the root-level `PRD.md` and `PRODUCT_SPEC.md`.

This historical PRD remains for continuity, but G7.1A supersedes the old product framing:

- Product: Unified Opportunity Engine.
- Primary user: discretionary supercycle investor/operator.
- Primary job: find MU/SNDK-style de-risked asymmetric upside.
- Secondary job: read market behavior through GodView signals: IV, options whales, gamma, short squeeze, CTA/systematic pressure, sector rotation, ETF/passive flows, dark-pool/block activity, ownership whales, microstructure, catalysts, and regime.
- Output layer: dashboard states and paper-only prompts: wait, watch, accumulation, confirmation, buying range, let winner run, trim optional, exit risk, thesis broken.
- Boundary: the system is not a trading bot and G7.1A adds no search, candidate generation, backtest, replay, proxy run, options ingestion, ranking, alert, broker, provider, or dashboard-runtime implementation.
- Immediate next action: `approve_g7_1b_data_infra_gap_or_g7_2_state_machine`.

G8 Candidate-Card Notice (2026-05-10)

- G8 creates exactly one human-nominated Supercycle Gem Candidate Card for `MU`.
- The card is a structured research object, not an investment recommendation.
- It records thesis placeholder, source-quality labels, missing evidence, thesis breakers, provider gaps, and forbidden state transitions.
- It does not produce an alpha score, ranking, buying range, alert, trade, promotion packet, backtest, replay, provider ingestion, dashboard runtime behavior, or broker action.
- Immediate next action: `approve_g9_one_market_behavior_signal_card_or_hold`.

G8.1 Discovery-Intake Notice (2026-05-10)

- G8.1 creates a controlled supercycle discovery intake layer.
- It seeds exactly six intake names: `MU`, `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB`.
- `MU` remains the only full candidate card; all other seed names are intake-only.
- Intake items record themes, why they might belong, evidence needed, source leads, official sources needed, relevant market-behavior modules, thesis breakers, and provider gaps.
- G8.1 does not produce alpha search, ranking, scoring, validated thesis status, buying range, alert, broker behavior, provider ingestion, dashboard runtime behavior, or investment recommendations.
- Immediate next action: `approve_g8_2_one_additional_candidate_card_or_g9_one_market_behavior_signal_card_or_hold`.

G8.1A Discovery-Drift Correction Notice (2026-05-10)

- G8.1A corrects the origin label for the six-name queue.
- The queue is user-seeded and theme/supply-chain-adjacent, not pure system-scouted output.
- Required fields now include `discovery_origin`, `origin_evidence`, `scout_path`, `is_user_seeded`, `is_system_scouted`, `is_validated`, and `is_actionable`.
- `LOCAL_FACTOR_SCOUT` is defined for G8.1B but is not used in G8.1A.
- G8.1A does not produce alpha search, ranking, scoring, factor-scout output, validated thesis status, buying range, alert, broker behavior, provider ingestion, dashboard runtime behavior, or investment recommendations.
- Immediate next action: `approve_g8_1b_pipeline_first_discovery_scout_or_hold`.

DASH-0 Dashboard IA Notice (2026-05-10)

- DASH-0 approves a planning-only GodView dashboard information architecture.
- Target pages are Command Center, Opportunities, Thesis Card, Market Behavior, Entry & Hold Discipline, Portfolio & Allocation, Research Lab, and Settings & Ops.
- DASH-0 does not edit `dashboard.py`, `views/`, `optimizer_view.py`, Streamlit runtime navigation, providers, alerts, broker code, factor scout code, discovery intake output, candidate cards, or backtests.
- Immediate next action: `approve_dash_1_page_registry_shell_or_hold`.

DASH-1 Page Registry Shell Notice (2026-05-10)

- DASH-1 implements the approved GodView page registry/sidebar shell.
- Top-level pages are Command Center, Opportunities, Thesis Card, Market Behavior, Entry & Hold Discipline, Portfolio & Allocation, Research Lab, and Settings & Ops.
- Legacy runtime content is only relocated: Ticker Pool & Proxies -> Opportunities; Data Health and Drift Monitor -> Settings & Ops; Daily Scan, Backtest Lab, Modular Strategies, and Hedge Harvester -> Research Lab; Portfolio Builder and Shadow Portfolio -> Portfolio & Allocation.
- DASH-1 adds no new data, metrics, product claims, provider calls, alerts, broker behavior, factor-scout integration, candidate generation, ranking, scoring, or buy/sell/hold output.
- Immediate next action: `approve_dash_2_command_center_placeholder_or_hold`.

G8.2 System-Scouted Candidate-Card Notice (2026-05-10)

- G8.2 creates exactly one additional Supercycle Gem Candidate Card for `MSFT`.
- `MSFT` is eligible only because G8.1B emitted it as the sole governed `LOCAL_FACTOR_SCOUT` output.
- The MSFT card is a structured research object, not a thesis validation, score, rank, buying range, alert, trade, promotion packet, or recommendation.
- `MU` and `MSFT` are the only candidate cards after G8.2.
- Existing dashboard rows that show `MSFT`, tactical labels, entry prices, or `IGNORE` are legacy runtime output, not the G8.2 card.
- G8.2 adds no new scout output, provider call, dashboard runtime behavior, candidate ranking, candidate scoring, buy/sell/hold output, alert, or broker behavior.
- Immediate next action: `approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold`.

Portfolio Universe Construction Notice (2026-05-10)

- Portfolio Optimizer defaults now come from an explicit optimizer universe builder, not from dashboard display order or `selected_tickers[:20]`.
- `EXIT`, `KILL`, `AVOID`, and `IGNORE` are excluded by default; generic `WATCH` is research-only by default.
- Ticker-map readiness, local price-history readiness, and max-weight feasibility must be visible before allocation.
- The current optimizer is thesis-neutral and does not encode MU conviction, MU hard floors, Black-Litterman views, thesis anchors, or manual overrides.
- Immediate next action: `approve_thesis_anchor_policy_or_hold`.

Optimizer Core Structured Diagnostics Notice (2026-05-11)

- Portfolio Optimizer now has structured diagnostics for feasibility, SLSQP status, active bounds, constraint residuals, equal-weight boundary pressure, and labeled fallback allocations.
- Fallback allocations must be visible as fallback and must state that they are not optimized results.
- This notice does not approve MU conviction, WATCH investability expansion, Black-Litterman, simple tilt / conviction optimizer, new objectives, scanner rules, manual overrides, provider ingestion, alerts, broker behavior, or replay behavior.
- Immediate next action: `approve_portfolio_thesis_anchor_policy_planning_or_hold`.

Portfolio Optimizer View Test and Performance Notice (2026-05-11)

- `/portfolio-and-allocation` optimizer rendering is covered by dedicated Streamlit `AppTest` integration tests.
- Recent selected-stock display refresh loads from a non-canonical Parquet cache and schedules background refresh on cold/stale cache misses.
- Optimizer math execution is cached by selected price frame and user parameters to avoid repeated SLSQP work on equivalent rerenders.
- This notice does not approve canonical provider ingestion, new optimizer objectives, lower-bound policy, MU conviction, WATCH investability expansion, alerts, broker behavior, rankings, scores, or candidate-card dashboard integration.
- Immediate next action: `hold_or_measure_next_dashboard_runtime_bottleneck`.

Product Requirements Document: Terminal Zero
Author: Atomic Mesh | Date: 2026-02-15 | Status: Active | Version: 15.0 (FR-080 Walk-Forward Optimization In Progress)

1. Executive Summary
Terminal Zero is a local-first quantitative research platform that has evolved through twelve phases:
  Phase 1: ETL + Engine (Data Plumbing & Vectorized PnL).
  Phase 2: Adaptive Trend Strategy (3-Regime Logic: Attack/Caution/Defense).
  Phase 3: Investor Cockpit (Daily Signal Monitor: Stops, Dips, Macro).
  Phase 4: Parameter Optimizer (Automated Grid Search & Adaptive Parameters).
  Phase 5: Quantamental Integration (PIT quality gate: ROIC + Revenue Growth).
  Phase 6: Portfolio Optimizer (Inverse Volatility + Mean-Variance with fallback).
  Phase 7: Context-Aware Intelligence (Sector/Industry map integration).
  Phase 8: Catalyst Radar (Top 3000 expansion + event-driven overlays). ✅
  Phase 9: Macro-Regime Awareness Layer (institutional stress state map). ✅
  Phase 10: Global Liquidity & Flow Layer (money supply + plumbing). ✅
  Phase 11: Regime Governor + Throttle Contract (deterministic risk matrix). ✅
  Phase 12: Regime Historical Verification (truth-table + stress validation). ✅
  Phase 13: Regime Walk-Forward Backtest (signal-to-PnL validation). ✅
  Phase 14: Feature Engineering & Micro-Alpha (selector data layer). ← CURRENT

Core Philosophy: "The Pilot's Checklist." Do not guess. Check the instruments. Then let the math optimize the instruments.

Current governance overlay (Phase 65, 2026-05-09):
  - Provenance and validation gates are executable before paper-alert expansion.
  - Alpaca operational/paper infrastructure uses `alpaca-py==0.43.4`; live orders remain blocked.
  - Phase F Candidate Registry is complete as registry-only work before strategy search or promotion packets.
  - Candidate intent must be recorded before results with `trial_count`, `parameters_searched`, `manifest_uri`, `source_quality`, and `code_ref`.
  - Candidate Registry snapshots are not promotion authority; strategy search, simulation, alerts, and broker behavior remain blocked until separately approved.
  - Phase G0 V2 Proxy Boundary is complete as boundary-only work; proxy outputs are advisory, `promotion_ready = false`, registry-note-proven, and future promotion requires `core.engine.run_simulation`.
  - Phase G2/G3 fixture lineage and canonical replay are complete: one registered fixture candidate can replay through V2 proxy lineage and the V1 canonical path, with V2 still blocked from promotion.
  - Phase G4/G5 real canonical control steps are complete: one tiny Tier 0 `prices_tri` slice passed readiness gates, then replayed once through the official V1 path with neutral weights and no alpha, ranking, alert, broker, V2 real-data proxy, or promotion behavior.
  - Phase G7 preregistered `PEAD_DAILY_V0` as a tactical signal family only; it is not the core roadmap center.
  - Phase G7.1 realigned the product around discretionary augmentation for de-risked asymmetric upside: 90% supercycle gem discovery and 10% buying-range / hold-discipline prompting.
  - `SUPERCYCLE_GEM_DAILY_V0` is the primary product family target for the next definition-only phase; no candidate generation, search, ranking, alert, broker, or promotion behavior is authorized by G7.1.

2. System Architecture
Layer 1: Data Lake (ETL → Parquet files)
Layer 2: Compute Engine (Vectorized PnL with Shift(1), Turnover Tax)
Layer 3: Strategy Layer (Pluggable "Cartridge" API)
Layer 4: Optimizer (Grid Search over Strategy Parameters) ← NEW
Layer 5: Application (Streamlit Dashboard)

3. Features (Cumulative)

3.1 The Macro Advisor (Cash Management) [Phase 3]
[FR-011] Regime Gauge:
    - Input: VIX Proxy (Rolling Vol of SPY).
    - If VIX > 25: "🔴 DEFENSE (50% Cash)"
    - If VIX > 18: "⚠️ CAUTION (20-30% Cash)"
    - Else: "🟢 BULLISH (Full Port)"

3.2 The Position Monitor (Exit & Risk) [Phase 3]
[FR-012] Chandelier Exit Calculator:
    - Logic: Stop Price = HighestClose(22d) - (k * ATR(22d)).
    - Data Constraint: Close-Only (no High/Low). k raised to 3.5 to compensate.
    - Action: If Price < Stop Price → "SELL IMMEDIATELY".

3.3 The Dip Hunter (Entry Zones) [Phase 3]
[FR-013] Reversion Bands:
    - Logic: Buy Zone = MA(20d) + (z * StdDev(20d)), where z is negative (e.g., -2.5).
    - Uses Log-Price Z-Score for volatility symmetry.
    - Action: Place Limit Orders at this level.

3.4 The Parameter Optimizer [Phase 4] ← NEW
[FR-015] 2D Grid Search (Heatmap):
    - Sweep k (Exit Multiplier): 2.0 to 4.5, step 0.1.
    - Sweep z (Entry Threshold): -1.5 to -4.0, step -0.1.
    - Metric: Ulcer-Adjusted Sharpe Ratio (balances Return vs Drawdown Pain).
    - Output: Interactive Heatmap showing optimal (k, z) coordinate.
    - Goal: Replace manual slider-nudging with mathematical optimization.

[FR-016] Adaptive Regime Parameters:
    - Instead of fixed k and z, parameters auto-adjust based on VIX Proxy:
        - VIX < 15 (Low Vol):  k=2.5 (Tight stops), z=-1.5 (Buy mild dips).
        - VIX 15-25 (Normal):  k=3.5 (Standard),    z=-2.5 (Standard dips).
        - VIX > 25 (High Vol): k=4.5 (Loose stops),  z=-3.5 (Only deep crashes).
    - Goal: Solve the FOMO vs Left-Side Pain trade-off automatically.

[FR-017] Wait-for-Confirmation ("Green Candle" Check):
    - Dip signal triggers when Z < z_entry.
    - But entry only CONFIRMS if Price(T) > Price(T-1) (first green candle).
    - Goal: Reduce premature "Left-Side" entries.

3.5 Dynamic Volatility Mapping [Phase 4.1] ← NEW
[FR-019] Per-Stock Adaptive Parameters:
    - Instead of one global k/z, each stock gets its OWN parameters based on
      its cross-sectional volatility rank (60-day window).
    - Formula:
        k_i = 2.5 + (1.5 × Rank(Vol_i))   # Low Vol → 2.5, High Vol → 4.0
        z_i = -3.0 + (2.0 × Rank(Vol_i))   # Low Vol → -3.0, High Vol → -1.0
    - Goal: NVDA (high vol) gets loose stops; KO (low vol) gets tight stops.
    - Eliminates the contradiction of a single global parameter.

4. User Interface
[FR-014] The "Daily Action Report":
    - Watchlist-based table: Current Price, Stop Price, Risk Buffer %, Buy Zone, Action.
    - Signal Visualizer: Plotly chart with Stop Line (Red) and Buy Zone (Green).
    - Per-stock k/z values displayed with volatility rank badge.

[FR-018] The "Optimizer Lab" (New Tab):
    - 2D Heatmap (Plotly) showing Return/Drawdown for each (k, z) pair.
    - Fixed vs Adaptive comparison card.

5. Implementation Roadmap
  Phase 1: ETL + Engine ✅
  Phase 2: 3-Regime Strategy ✅
  Phase 3: Investor Cockpit ✅
  Phase 4: Parameter Optimizer ✅
    - [x] Create `core/optimizer.py` (Grid Search engine).
    - [x] Update `strategies/investor_cockpit.py` with Adaptive Regime logic (FR-016).
    - [x] Add "Green Candle" confirmation (FR-017).
    - [x] Add Optimizer tab to `app.py` (FR-018).
  Phase 4.1: Dynamic Volatility Mapping ✅
    - [x] Per-stock k/z via cross-sectional vol rank (FR-019).
    - [x] Adaptive toggle in Cockpit UI.
    - [x] Fixed vs Adaptive comparison in Optimizer.
  Phase 4.2: Live Data + UX ✅
    - [x] Searchable Ticker Dropdown (FR-020).
    - [x] Yahoo Bridge — Live Data Updater (FR-021).
    - [x] Data Manager Tab (FR-022).
  Phase 5: Quantamental Integration ✅
    - [x] PIT fundamentals ingestion + snapshot context.
    - [x] Scanner Pass 1.5 hard quality gate (ROIC > 0 and Revenue YoY > 0).
    - [x] Watchlist penalty mode with quality warning/cap behavior.
  Phase 6: Portfolio Optimizer ✅
    - [x] `strategies/optimizer.py` with inverse-volatility and mean-variance (SLSQP + fallback).
    - [x] `views/optimizer_view.py` allocation UI and shares table.
  Phase 7: Sector Context ✅
    - [x] Sector map builder (`data/build_sector_map.py`).
    - [x] Scanner + optimizer sector context wiring.
  Phase 8: Catalyst Radar Foundation (Steps 1-6) ✅
    - [x] Added Top 3000 scope support (`data/updater.py`, `data/fundamentals_updater.py`, `data/build_sector_map.py`, `app.py`).
    - [x] Hydrated fundamentals snapshot for expanded universe.
    - [x] Rebuilt sector map for 3000 symbols.
    - [x] Validated scanner path at Top 3000 scale with timing + gate metrics.
    - [x] Ingested local Compustat bedrock into canonical fundamentals store (FR-031).
    - [x] Added institutional valuation/cashflow factor layer with decumulation + EV/EBITDA validation (FR-033).
  Phase 8: Catalyst Radar (Steps 7-11) ✅
    - [x] Added Yahoo earnings calendar updater (`data/calendar_updater.py`) with lock + atomic writes.
    - [x] Integrated calendar context in `app.load_data()` and Data Manager refresh controls.
    - [x] Extended scanner strategy with `days_to_earnings`, `earnings_risk`, and `fresh_catalysts` mode.
    - [x] Added scanner UI earnings warning column and risk-hide toggle.
    - [x] Added validation script for calendar layer (`scripts/validate_calendar_layer.py`).
  Phase 11: FR-041 Regime Governor + Throttle (Docs-as-Code) 🟡
    - [x] Freeze Current Algorithm v1 behavior in `spec.md` before contract changes.
    - [x] Define `RegimeManager` contract, 3x3 mapping matrix, and explicit thresholds.
    - [x] Document long-only red safety clamps.
    - [x] Add phase brief and decision log entries for FR-041.
  Phase 12: FR-042 Regime Historical Verification 🟡
    - [x] Define strict truth-table windows in docs (`docs/phase12-brief.md`).
    - [x] Create verifier script (`backtests/verify_regime_history.py`).
    - [x] Emit `regime_history.csv` and overlay artifact contract.
    - [x] Run reviewer gate and close milestone.
  Phase 13: FR-050 Regime Walk-Forward Backtest 🟡
    - [x] Define FR-050 brief and artifacts (`docs/phase13-brief.md`).
    - [x] Implement walk-forward verifier (`backtests/verify_phase13_walkforward.py`).
    - [x] Add tests for T+1 execution and cash fallback behavior.
    - [x] Run verification + reviewer gate (milestone closed: software PASS, strategy BLOCK).
  Phase 14: FR-060 Feature Engineering & Micro-Alpha 🟡
    - [x] Define FR-060 brief and feature contract (`docs/phase14-brief.md`).
    - [x] Implement feature builder (`data/feature_store.py`).
    - [x] Add tests for PIT safety and close-only fallback behavior.
    - [x] Run verification + reviewer gate (current verdict: PASS).

3.6 Searchable Ticker Dropdown [Phase 4.2] ← NEW
[FR-020] Replace raw PERMNO text input with searchable multiselect:
    - Type "NV" → dropdown filters to "NVDA (86580)".
    - Backed by tickers.parquet (23K permno→ticker mappings).
    - Chart title and Action Report show human-readable ticker names.

3.7 Yahoo Finance Bridge [Phase 4.2] ← NEW
[FR-021] Live Data Updater (data/updater.py):
    - Architecture: "Append-Only Hybrid Lake"
      - Base: prices.parquet (47M rows, WRDS 2000-2024, NEVER modified)
      - Patch: yahoo_patch.parquet (Yahoo 2025+, overwritten on update)
      - app.py reads BOTH via DuckDB UNION ALL.
    - Batch download via yf.download([...]) — 50x faster than looping.
    - Macro (SPY + VIX Proxy) rebuilt on each update.
    - Scope options: Top 50 / Top 100 / Top 200 / Custom watchlist.
    - Synthetic permnos (900000+) for new tickers not in WRDS.

3.8 Data Manager Tab [Phase 4.2] ← NEW
[FR-022] Dashboard tab for data operations:
    - System Status: Last date, universe size, SPY, VIX, freshness badge.
    - Update Controls: Scope selector + "Run Update Now" button.
    - Auto-clears st.cache_data after update and refreshes dashboard.
    - Architecture diagram showing Hybrid Lake design.

3.9 Five-State Signal Model [Phase 4.2] ← NEW
[FR-023] Replace binary SELL/BUY with 5 actionable states:
    | State | Condition | Action |
    |-------|-----------|--------|
    | HOLD  | Price > Stop, above buy zone | Trend intact. Stop = protective floor. |
    | BUY   | Price > Stop, in buy zone + green candle | Dip confirmed. Safe entry. |
    | WATCH | Price > Stop, in buy zone + red candle | Dip detected. Wait for green candle. |
    | AVOID | Price < Stop, above buy zone | Trend broken. Wait for buy zone support. |
    | WAIT  | Price < Stop, below buy zone | Capitulation. Deep support = z - 1.5σ. |
    - Key insight: "SELL" when stop is already broken is stale advice.
    - Forward-looking: shows NEXT level to watch, not past triggers.
    - Support price: Buy Zone (AVOID) or z_deep (WAIT) for re-entry guidance.

3.10 Conviction Scorecard [Phase 4.2 — L5 Alpha Upgrade]
[FR-024v2] Institutional-grade conviction scoring (0-10):
    | Dimension | Points | Logic (v2) |
    |-----------|--------|------------|
    | A. Trend  | 0-3 | Price > MA200 → 3pts (unchanged) |
    | B. Value  | 0-3 | Robust Z (MAD) < -3.0 → 3pts, < -2.0 → 1pt |
    | C. Macro  | 0-2 | VIX < 20 + falling → 2pts, mixed → 1pt, panic → 0 |
    | D. Momentum | 0-2 | Price > MA20 + ER > 0.4 → 2pts, choppy → 1pt |
    
    Advanced Methods:
    - Robust Z: Median + MAD (1.4826 scaling). Crash-resistant.
    - Efficiency Ratio: |Direction|/TotalPath. Filters noise from signal.
    - VIX Trend: Absolute level + 20d MA direction.
    
    Score Interpretation:
    | Score | Label | Meaning |
    |-------|-------|---------|
    | 8-10 | 🔥 HIGH | Perfect storm — all factors aligned |
    | 5-7 | ✅ MODERATE | Good setup, 1-2 factors missing |
    | 1-4 | ⚠️ SPECULATIVE | Counter-trend or hostile environment |

3.11 Smart Watchlist + Auto-Update [Phase 4.2] ← NEW
[FR-025] Self-healing data pipeline with persistent state:
    - data/watchlist.json: Stores {defaults: [...], user_added: [...]}
    - Signal Monitor persists user's ticker selections automatically.
    - On app startup: business-day-aware freshness check → auto-update if stale.
    - data/auto_update.py: Standalone CLI script for Task Scheduler / cron.
    - Default watchlist: AAPL, MSFT, SPY, AMZN, GOOG, META, NVDA, TSLA, QQQ, IWM.

3.12 Scanner Cockpit Redesign [Phase 4.3] ← NEW
[FR-026v2] Replace multiselect+stacked-cards with scanner+detail architecture:
    - Scanner View: Radio toggle between High Conviction / My Watchlist (same position)
        - High Conviction: scan_universe() 2-pass filter on full 2000-stock universe
        - Always shows top 5 by score (no hard cutoff)
        - Score tiers: 🔥 9+ (PERFECT STORM), ✅ 7-8 (STRONG), ⚠️ 5-6, 💤 <5
        - Watchlist: generate_weights() on watchlist tickers only (fast)
        - Each row has 🔍 drill-down button
    - Smart Dropdown: Searchable selectbox sorted by latest price (popularity proxy)
        - Uses native UI (no layout shift)
        - Sorted high-to-low price so popular stocks appear first
        - Selection triggers instant drill-down
    - Detail View: Single-ticker chart + action report card
        - Reuses all existing chart + card rendering logic
        - "← Back to Scanner" navigation
    - Removed: st.multiselect dropdown, stacked cards view
    - Kept: Sidebar controls, Macro Advisor, Conviction scoring, Watchlist persistence
    - [D-28] JIT Patch: Auto-fetch Yahoo data when user drills into stale ticker.
      Architecture: "Bedrock (WRDS 2000-2024) + Fresh Snow (Yahoo 2025-now)".

3.13 Quantamental Quality Gate [Phase 5] ← NEW
[FR-027] Add a PIT-correct quality filter to eliminate value traps:
    - Fundamentals keyed by `release_date` (not quarter-end).
    - Scanner hard filter: Trend pass AND Quality pass.
    - Minimum Viable Quality (MVQ): `ROIC > 0` and `Revenue Growth YoY > 0`.
    - Missing or stale fundamentals default to fail-safe exclusion.
    - ETF bypass list for non-operating instruments (SPY/QQQ/IWM/DIA/GLD/TLT).

3.14 Portfolio Optimizer [Phase 6] ← NEW
[FR-029] Convert "good ideas" into allocation weights:
    - Inverse-Volatility baseline allocator.
    - Mean-Variance (max Sharpe) with long-only, fully-invested constraints.
    - Failure fallback to equal-weight / inverse-vol mode for resilience.
    - UI tab with allocation chart and shares-to-buy output.

3.15 Context-Aware Sector Map [Phase 7] ← NEW
[FR-028] Add static sector/industry metadata to scanner + optimizer:
    - One-off map builder persists `data/static/sector_map.parquet`.
    - Mapped into fundamentals snapshot context for UI explainability.
    - Scanner rows now include sector classification.

3.16 Phase 8 Data Expansion Foundation [Phase 8] ← NEW
[FR-030 Step Set: 1-6] Scale universe safely from Top 2000 baseline to Top 3000 optional scope:
    - Added Top 3000 controls in Data Manager and updater CLIs.
    - Dynamic load batching in `app.load_data()`:
      - `batch_size = 200` when universe > 2500.
      - `batch_size = 250` otherwise.
    - Data hydration status (2026-02-14):
      - `fundamentals.parquet`: 10,219 rows.
      - `fundamentals_snapshot.parquet`: 1,680 rows.
      - `sector_map.parquet`: 3,000 rows.
      - Latest observed release date: 2026-03-17.
    - Validation snapshot (2026-02-14 local run):
      - Top 2000: load 15.356s, scan 0.227s, gate `trend=6`, `quality=310`, survivors=2.
      - Top 3000: load 21.307s, scan 0.307s, gate `trend=6`, `quality=432`, survivors=2.
    - Operational rollout decision:
      - Keep default runtime at Top 2000 for responsiveness.
      - Expose Top 3000 as explicit scale-up mode for controlled expansion.

3.17 Compustat Bedrock Ingestion [Phase 8] ← NEW
[FR-031 Step Set: Data Layer Expansion Before Catalyst Logic]
    - Source: `data/e1o8zgcrz4nwbyif.csv` (local WRDS/Compustat quarterly file).
    - Scope guardrail: Top 3000 liquid universe only (no 28k full-universe pivot risk).
    - PIT alignment:
      - Primary release date: `rdq`.
      - Fallback when missing: `datadate + 45 days`.
    - Metric computation:
      - `revenue_growth_yoy = (revenue_q - lag4(revenue_q)) / lag4(revenue_q)` (per permno, ordered by quarter).
      - `roic = op_income_ttm / invested_capital_avg` with fail-safe null handling.
    - Merge precedence:
      - On `(permno, release_date)` collisions, `compustat_csv` overrides `yfinance`.
    - Safety:
      - `.update.lock` coordination.
      - Atomic parquet writes + timestamped backups.
      - Match/unmatched audit outputs for traceability.
    - Execution results (2026-02-14):
      - Top3000 match coverage: `2781/3000` (`92.70%`).
      - `fundamentals.parquet`: `10,219 -> 225,640` rows (initial merge).
      - `fundamentals_snapshot.parquet`: `1,680 -> 2,819` rows (initial merge).
      - Scanner gate (Top 3000): `trend=6`, `quality=428`, `survivors=2` (initial merge).
    - Post-remediation state (2026-02-15):
      - `fundamentals.parquet`: `215,876` rows (dedup + PIT clamp applied).
      - `fundamentals_snapshot.parquet`: `1,550` rows (active + complete metrics).
      - Data layer validator: PASS.

3.18 Russell 3000 PIT Universe Scaffold [Phase 8] ← NEW
[FR-032 Step Set: Forward-Test Universe Layer]
    - Added loader: `data/r3000_membership_loader.py`.
    - Input Gate (institutional hard stop):
      - Requires WRDS constituent-history columns: `gvkey`, `from`, `thru`.
      - Requires minimum constituent rows (default `>= 1000` with usable `gvkey`).
      - Rejects metadata-only exports.
    - Artifacts:
      - `data/processed/r3000_membership.parquet`
      - `data/processed/universe_r3000_daily.parquet`
      - `data/processed/r3000_unmatched.csv`
    - Dynamic PIT logic for forward testing:
      - Daily universe uses `from <= T <= thru` at each trade date `T`.
    - Current status (2026-02-15):
      - Provided file `data/t1nd1jyzkjc3hsmq.csv` failed input gate (metadata-only, no usable constituents).
      - Awaiting full WRDS index constituent history export to complete FR-032 execution.

3.19 Institutional Valuation Factor Layer [Phase 8] ← NEW
[FR-033 Step Set: Cashflow Decumulation + EV/EBITDA Matrix]
    - Added institutional factor schema to canonical fundamentals:
      - Raw fields: `oibdpq`, `atq`, `ltq`, `xrdq`, `oancfy`, `dlttq`, `dlcq`, `cheq`, `cshoq`, `prcraq`, `fyearq`, `fqtr`.
      - Derived fields: `oancf_q`, `oancf_ttm`, `ebitda_ttm`, `revenue_ttm`, `xrd_ttm`, `mv_q`, `total_debt`, `net_debt`, `ev`, `ev_ebitda`, `leverage_ratio`, `rd_intensity`.
    - Core logic:
      - Cashflow de-YTD: `oancf_q = oancfy - lag(oancfy)` for Q2-Q4 within `(permno, fyearq)`.
      - EV/EBITDA + leverage computed vectorized with safe denominators.
    - Validation outcomes (2026-02-15):
      - PIT violations: `0`.
      - Decumulation mismatch: `0.0698%`.
      - Q4 spike rate (>10x Q1-Q3 median): `1.69%`.
      - EV/EBITDA arithmetic bad-rate (>1% error): `0.00%`.
      - Snapshot factor coverage: EV/EBITDA `48.45%`, Leverage `73.94%`, RD Intensity `47.87%`, OANCF_TTM `85.35%`, EBITDA_TTM `80.90%`.
    - Runtime smoke (Top 3000):
      - Load `10.105s`, Scan `0.087s`.
    - Gate: `trend=6`, `quality=945`, `survivors=4`.

3.20 Catalyst Radar [Phase 8] ← NEW
[FR-034 Step Set: Event Risk + Fresh Catalysts]
    - New data artifact: `data/processed/earnings_calendar.parquet`.
    - Ingestion:
      - `data/calendar_updater.py` fetches earnings dates from Yahoo Finance.
      - Scope options: Top 20/50/100/200/500/3000 or custom watchlist.
      - Runtime safety: updater lock + atomic parquet writes.
    - Strategy integration (`strategies/investor_cockpit.py`):
      - Adds `days_to_earnings`, `days_since_earnings`, and `earnings_risk`.
      - Risk rule: `earnings_risk = 1` when earnings are within blackout window (default `<5 days`).
      - New scanner mode: `fresh_catalysts` (reported earnings in last 7 days + existing quality/trend gates).
    - UI integration:
      - Scanner table now includes an `Earnings` column with warning badge.
      - Controls include blackout-days selector and "Hide earnings risk" toggle.
      - Data Manager includes calendar coverage/freshness metrics and refresh trigger.

3.21 Macro-Regime Awareness Layer [Phase 9] ← NEW
[FR-035 Step Set: Institutional State Space]
    - Objective:
      - Convert market stress into explicit, PIT-safe features and regime flags.
      - Enable strategy behavior shifts via a deterministic macro scalar.
    - Canonical artifact:
      - `data/processed/macro_features.parquet` (single source of truth; no dual macro files).
    - Data sources (Phase 9):
      - Yahoo: `^VIX`, `^VIX3M`, `^VVIX`, `DX-Y.NYB`, `^GSPC`, `HYG`, `LQD`, `MTUM`, `SPY`, `BND`, `BTC-USD`.
      - FRED: `SOFR`, `DFF` (EFFR proxy), `T10Y2Y`, `DFII10`.
      - DIX/GEX explicitly deferred to Phase 10.
    - PIT alignment policy:
      - Fast market series: T+0 at market close.
      - Slow FRED series: conservative T+1 shift.
      - Weekend/holiday continuity: forward-fill max 3 trading days.
    - Regime checks:
      - `liquidity_air_pocket`: `(VIX - VIX3M > 0) & (VVIX > 110)`.
      - `collateral_crisis`: `(SOFR - EFFR) > 0.10` (10 bps).
      - `credit_freeze`: `zscore(HYG/LQD, 63d) < -2.0`.
      - `momentum_crowding`: `corr(MTUM, SPY, 60d) > 0.85`.
    - Acceptance criteria:
      - March 2020 triggers liquidity stress events.
      - 2022 shows momentum crowding state transitions.
      - Loader and validator pass (`macro_loader.py`, `validate_macro_layer.py`).

3.22 Global Liquidity & Flow Layer [Phase 10] ← NEW
[FR-040 Step Set: Money Supply + Plumbing]
    - Objective:
      - Measure macro liquidity causes (not just volatility symptoms).
      - Add a daily, PIT-safe liquidity feature layer for strategy conditioning.
    - Canonical artifact:
      - `data/processed/liquidity_features.parquet`
    - Core signals:
      - `us_net_liquidity_mm = WALCL - WDTGAL - (RRPONTSYD * 1000)`
      - `liquidity_impulse` (normalized 20-day ROC of net liquidity)
      - `repo_spread_bps = (SOFR - DFF) * 100`
      - `lrp_index = Z(DTB3) - Z(VIX)`
      - `dollar_stress_corr = Corr20(DXY, SPX returns)`
      - `smart_money_flow = CumSum(SPY Close - SPY Open)`
    - PIT guardrail:
      - Fed H.4.1 weekly series (`WALCL`, `WDTGAL`) availability is shifted +2 days (Wed -> Fri).
    - Exclusions for MVP:
      - DIX/GEX, FTD, and COT feeds deferred to later phase.

3.23 Regime Governor + Throttle Contract [Phase 11] ← NEW
[FR-041 Step Set: Deterministic Exposure Control]
    - Objective:
      - Separate "state safety" (Governor) from "opportunity context" (Throttle).
      - Replace implicit fallback behavior with an explicit 3x3 exposure matrix.
    - Inputs and thresholds (explicit):
      - RED if any:
        - `repo_spread_bps > 10.0` (basis points)
        - `credit_freeze == True` AND `vix_level > 15`
        - `liquidity_impulse < -1.90` AND `vix_level > 20`
        - `vix_level > 40`
      - AMBER if not RED and any:
        - `us_net_liquidity_mm < 0.997 * MA20(us_net_liquidity_mm)` AND `liquidity_impulse < 0`
        - `vix_level > 25`
        - `bocpd_prob > 0.80`
      - GREEN otherwise.
      - Throttle score:
        - `S = mean(Z(liquidity_impulse), Z(vrp), -Z(vix_level), Z(momentum_proxy))` in `[-2, 2]`.
        - POS if `S > 0.5`, NEUT if `-0.5 <= S <= 0.5`, NEG if `S < -0.5`.
      - Data contract:
        - `realized_vol_21d` and `vrp = vix_level - realized_vol_21d` are produced in `data/liquidity_loader.py`.
    - Regime matrix (`Governor x Throttle`):
      - GREEN: `NEG=0.70`, `NEUT=1.00`, `POS=1.30`
      - AMBER: `NEG=0.25`, `NEUT=0.50`, `POS=0.75`
      - RED: `NEG=0.00`, `NEUT=0.00`, `POS=0.20`
    - Long-only safety rule:
      - `RED+NEG` and `RED+NEUT` force `0.00` exposure (cash).
      - `RED+POS` is capped at `0.20` (tactical, no shorting).
      - Strategy remains long-only (`weights >= 0.0`).
    - Delivery criteria:
      - `spec.md` includes frozen "Current Algorithm v1" and FR-041 interface/matrix contract.
      - `docs/phase11-brief.md` captures objective, thresholds, matrix, and acceptance criteria.
      - `decision log.md` records FR-041 architecture and red-regime long-only safety decisions.

3.24 Regime Historical Verification [Phase 12] ← NEW
[FR-042 Step Set: Truth-Table Proof of Life]
    - Objective:
      - Validate that FR-041 regime logic matches known crisis/calm windows without curve-fitting.
      - Verify safety behavior (crisis capture) and opportunity behavior (false-positive control).
    - Verifier:
      - `backtests/verify_regime_history.py`
      - Replays `RegimeManager` over full history and emits:
        - `data/processed/regime_history.csv`
        - `data/processed/regime_overlay.png`
    - Mandatory truth windows:
      - `2008Q4`: predominantly RED.
      - `2020-03`: predominantly RED.
      - `2022H1`: predominantly AMBER/RED.
      - `2017`: predominantly GREEN (false-positive guardrail).
      - `2023-11`: transition toward GREEN.
    - Behavioral metrics:
      - Drawdown reduction vs buy-and-hold baseline.
      - Recovery speed vs baseline.

3.25 Regime Walk-Forward Backtest [Phase 13] ← NEW
[FR-050 Step Set: Governor-to-PnL Validation]
    - Objective:
      - Validate whether FR-041 regime routing improves realized risk-adjusted
        outcomes when translated into executable portfolio weights.
    - Deterministic routing:
      - `GREEN -> 1.0 SPY`, `AMBER -> 0.5 SPY`, `RED -> 0.0 SPY` (cash).
      - Signal at `t` is executed at `t+1` (no look-ahead).
    - Cash proxy hierarchy:
      - `BIL` return when available.
      - Else `EFFR / 252` daily accrual.
      - Else flat `2% / 252`.
    - Artifacts:
      - `data/processed/phase13_walkforward.csv`
      - `data/processed/phase13_equity_curve.png`
    - Primary checks:
      - Ulcer index improvement.
      - Max drawdown compression.
      - Sharpe improvement.

3.26 Feature Engineering & Micro-Alpha [Phase 14] ← NEW
[FR-060 Step Set: Selector Data Layer]
    - Objective:
      - Add stock-level feature vectors for ranking, sizing, and execution.
    - Ranking features:
      - `resid_mom_60d`, `amihud_20d`, `rolling_beta_63d`.
    - Sizing feature:
      - `yz_vol_20d` (Yang-Zhang annualized volatility).
    - Execution features:
      - `atr_14d`, `rsi_14d`, `dist_sma20`.
    - Minimal signal scaffold:
      - `composite_score = Z(resid_mom_60d) + Z(flow_proxy) - Z(yz_vol_20d)`.
      - `trend_veto = price < SMA200`.
    - Data-constraint fallback:
      - If `open/high/low` are missing, use documented close-only fallback modes for YZ and ATR.
    - Artifact:
      - `data/processed/features.parquet`.

3.27 Alpha Engine & Tactical Execution [Phase 15] ← NEW
[FR-070 Step Set: Selector + Sizer + Executor]
    - Objective:
      - Connect the Governor (capital preservation) and Feature Store (asset-level alpha)
        into one deterministic execution layer.
    - Structural-fixed rules (not tuned):
      - Trend eligibility gate remains `price > SMA200`.
      - Regime budgets remain fixed: `GREEN=1.0`, `AMBER=0.5`, `RED=0.0`.
      - Score sign discipline remains fixed (momentum positive, volatility negative).
    - Adaptive knobs (walk-forward only):
      - RSI entry threshold via rolling percentile.
      - ATR stop multiplier via volatility regime.
      - Selection breadth via top-N / percentile depth.
    - Hard execution rules:
      - Hysteresis rank buffer: enter `Top 5`, hold until rank drops below `Top 20`.
      - Ratchet-only stop: stop level can only move upward after entry.
      - Regime budget hard cap always enforced at portfolio level.
    - Sizing contract:
      - Base: `target_risk / yz_vol_20d`.
      - Adjust: conviction scalar.
      - Enforce: hard cap to regime budget at portfolio level.
    - Executor contract:
      - Entry around pullback conditions (`SMA20` / RSI signal).
      - Dynamic stop using ATR multiple.
    - Artifacts:
      - Strategy module: `strategies/alpha_engine.py`
      - Strategy integration: `strategies/investor_cockpit.py`
      - Verifier: `backtests/verify_phase15_alpha_walkforward.py`
      - Unit tests: `tests/test_alpha_engine.py`

3.28 Walk-Forward Optimization & Honing [Phase 16] ← NEW
[FR-080 Step Set: Governance-First Parameter Honing]
    - Objective:
      - Hone adaptive execution parameters without changing fixed structural rules.
      - Improve out-of-sample robustness while preventing curve-fit drift.
    - WFO policy:
      - Fixed split protocol:
        - Train: `2015-01-01` to `2021-12-31`
        - OOS/Test: `2022-01-01` to `2024-12-31`
      - Parameter search and ranking use train metrics only.
      - OOS/Test is read-only for stability checks and pass/fail governance.
      - Promotion requires OOS stability acceptance and hard-constraint compliance.
    - Search space:
      - `entry_logic`: `dip`, `breakout`, `combined`.
      - `alpha_top_n` (selection depth).
      - `hysteresis_exit_rank` with mandatory `hysteresis_exit_rank >= alpha_top_n`.
      - `rsi_entry_percentile`.
      - `atr_multiplier`.
      - Phase 16.5 tournament baseline grid:
        - `alpha_top_n`: `10, 20`
        - `hysteresis_exit_rank`: `20, 30`
        - `adaptive_rsi_percentile`: `0.05, 0.10, 0.15`
        - `atr_preset`: `2.0, 3.0, 4.0, 5.0`
    - Runtime optimization patch:
      - Single-pass data loading and reuse across candidate evaluations.
      - Optional multi-core candidate evaluation with deterministic sequential fallback.
    - Acceptance criteria:
      - No OOS leakage in parameter selection path.
      - Structural-fixed rules from FR-070 remain unchanged.
      - Hard constraints pass for promoted parameter sets.
      - Required artifacts are generated and consumable.
    - Artifacts:
      - `data/processed/phase16_optimizer_results.csv`
      - `data/processed/phase16_best_params.json`
      - `data/processed/phase16_oos_summary.csv`

3.29 Position-Level Stop-Loss Control [Phase 21 Day 1] ← NEW
[FR-090 Step Set: Stop-Loss & Drawdown Control]
    - Objective:
      - provide a standalone, testable stop-loss subsystem for close-only environments.
    - ATR policy:
      - `atr_mode = proxy_close_only` (explicit).
      - `ATR_t = SMA(|Close_t - Close_{t-1}|, window=20)`.
    - Stop stages:
      - Initial: `entry - 2.0 * ATR_entry`.
      - Trailing: `price_t - 1.5 * ATR_t`.
      - Time override: exit when underwater for more than `60` days.
    - D-57 invariant:
      - `stop_t = max(stop_{t-1}, stop_candidate_t)` (stop never decreases).
    - Portfolio drawdown tiers:
      - `-8% => 0.75`, `-12% => 0.50`, `-15% => 0.00`; recover to full at `>-4%`.
    - Artifacts:
      - `strategies/stop_loss.py`
      - `tests/test_stop_loss.py`

3.30 SDM 3-Pillar Data Ingestion [Phase 23] ← NEW
[FR-100 Step Set: SDM Data Foundation]
    - Objective:
      - Build PIT-safe ingestion/assembly for Supply-Demand-Margin feature backbone.
    - Ingestion scripts:
      - `scripts/ingest_compustat_sdm.py` (Pillar 1 + 2)
      - `scripts/ingest_frb_macro.py` (Pillar 3a)
      - `scripts/ingest_ff_factors.py` (Pillar 3b)
      - `scripts/assemble_sdm_features.py` (final PIT assembler)
    - PIT merge contract:
      - Compustat anchor: `published_at = rdq`.
      - Peters & Taylor lag: `pit_date = datadate + 90 days`.
      - `merge_asof` requires global timeline-key sorting before join.
    - Identifier policy:
      - `permno` mapping uses `sector_map.parquet`.
      - unmapped rows are retained and audited (no silent drops).
    - Artifacts:
      - `data/processed/fundamentals_sdm.parquet`
      - `data/processed/macro_rates.parquet`
      - `data/processed/ff_factors.parquet`
      - `data/processed/features_sdm.parquet`

3.31 The Infinity Governor & Derivatives Trinity [Phase 62 & 64] ← NEW
[FR-110 Step Set: Non-Linear Risk & Leverage Abstraction]
    - Objective:
      - Match Buy & Hold on Compounders; Crush Buy & Hold on Manias.
    - Logic:
      - Bi-directional stop multiplier. Reward high $R^2$ with 5.4x stops. Penalize high Convexity with 1.5x stops.
      - Lookback Period strictly locked at 20 trading days to isolate immediate kinetic momentum.
      - Data Gaps (NaN/Null) fail-safe to baseline 3.0x ATR.
    - Leverage Engine:
      - Macro > 80 + Score 100 + Linear Trend = BUY 80-Delta LEAP.
      - If trend goes Parabolic = De-lever to 1.0x Stock.
      - Stop loss on LEAP is strictly tied to the underlying stock's trailing stop.
    - Polling Protocol:
      - Macro Gravity evaluated strictly at EOD (4:00 PM EST). No intraday regime changes.

3.32 Unified Command & Waterfall Entries [Phase 65] ← NEW
[FR-120 Step Set: Single Source of Truth Execution]
    - Objective:
      - Fuse regime, entry, and vehicle into one dashboard command.
    - Entry Logic:
      - Targets the *next* logical floor (21 -> 50 -> 200) instead of broken lines.
      - Applies empirical Wick Buffers based on kinetic cluster (Heavies, Sprinters, Scouts).
      - Applies Quality Premium to ensure fills on "Must Own" Score 100 assets.
    - Execution Mechanism:
      - Day Limit Orders ONLY (calculated EOD for next session). No GTC resting orders.
      - Zero FOMO protocol for fill failures; missing a trade costs nothing.

3.33 Microstructure Telemetry & Execution-Quality Analytics [Phase 29] ← NEW
[FR-130 Step Set: Arrival/Fill Quality Instrumentation]
    - Objective:
      - Upgrade execution assessment from binary `ok=True/False` to measurable microstructure quality.
    - Arrival Anchor:
      - At Sovereign_Command generation time, stamp `arrival_ts` (UTC ms precision).
      - Capture command-time midpoint: `arrival_price = (bid + ask) / 2`.
    - Fill Aggregation:
      - Aggregate partial fills by `client_order_id` and compute:
        - `VWAP_fill = sum(fill_price_i * fill_qty_i) / sum(fill_qty_i)`.
    - Slippage / Shortfall:
      - Buy shortfall: `IS_buy = (VWAP_fill - arrival_price) * qty`.
      - Sell shortfall (cost-positive): `IS_sell = (arrival_price - VWAP_fill) * qty`.
      - Normalize cross-asset costs via `slippage_bps` on arrival reference.
    - Latency Decomposition:
      - `command->submit`, `submit->ack`, `ack->first_fill`, `command->first_fill`.
    - Storage:
      - Persist order-level and fill-level telemetry in Parquet + DuckDB for OLAP analytics.

3.34 Release Engineering / MLOps Deterministic Pipeline [Phase 30] ← NEW
[FR-140 Step Set: Immutable Artifact Promotion + Automatic Rollback]
    - Objective:
      - Eliminate mutable deployment drift and guarantee deterministic startup-fault rollback.
    - Immutable Artifact Contract:
      - Every candidate release is a digest-locked image reference:
        - `release_ref = "<repo>:<tag>@sha256:<64-hex>"`.
      - Tags without digest lock are not promotable.
    - Promotion State Machine:
      - `pending_probe -> active | rolled_back`.
      - Metadata persisted atomically to:
        - `data/processed/release_metadata.json`.
    - Startup-Fault Rollback Contract:
      - Deployment controller watches candidate startup window.
      - If candidate exits during startup diagnostics, controller auto-restores N-1 image with no manual intervention.
    - UI Governance:
      - Cache invalidation is release-bound:
        - `cache_fingerprint = "<version>@sha256:<release_digest|local-dev>"`.

3.35 Sovereign Execution Hardening [Phase 31] <- NEW
[FR-150 Step Set: Trust Boundary + Telemetry Durability]
    - Objective:
      - close fail-open seams in signed replay, async telemetry durability, and semantic coercion boundaries.
    - Trust boundary:
      - local-submit replay gate is atomic across processes.
      - malformed replay ledger rows are quarantined and cannot hard-block valid submits.
    - Telemetry durability:
      - spool replay uses deterministic UID idempotence,
      - schema-invalid and stale-partial spool records are quarantined,
      - local-submit success/notify requires bounded durability gate pass.
    - Semantic contract:
      - snapshot paths validate required columns and date coercion,
      - candidate ranking is numeric-stable for `composite_score`,
      - boolean gates normalize explicit token sets (no unsafe truthiness coercion).
    - Artifacts:
      - `execution/signed_envelope.py`
      - `execution/microstructure.py`
      - `main_console.py`
      - `strategies/alpha_engine.py`
      - `strategies/ticker_pool.py`
      - `tests/test_signed_envelope_replay.py`
      - `tests/test_execution_microstructure.py`

3.36 Candidate Registry and Proxy Quarantine [Phase 65] <- NEW
[FR-160 Step Set: Candidate Intent + Synthetic Proxy Mechanics]
    - Objective:
      - prevent candidate results from outrunning identity, provenance, and official-truth boundaries.
    - Phase F registry:
      - candidate intent is registered before results;
      - append-only JSONL event log is the source of truth;
      - snapshot files are disposable projections;
      - no strategy search, alert, broker, or promotion path is authorized by registry presence.
    - Phase G0 proxy boundary:
      - V2 proxy outputs are advisory only;
      - `promotion_ready = false`;
      - `canonical_engine_required = true`;
      - future promotion still requires `core.engine.run_simulation`.
    - Phase G1 synthetic mechanics:
      - accepts only manifest-backed synthetic fixtures under `data/fixtures/v2_proxy/`;
      - reconciles fixture/golden row counts, date ranges, schema columns, and SHA-256 hashes before accepted output;
      - rejects `nan`, `+inf`, `-inf`, missing symbols, sparse target weights, and non-finite proxy metadata fail-closed;
      - does not repair invalid evidence with `nan_to_num`, sparse-weight `fillna(0)`, interpolation, or stringified nulls;
      - consumes prebaked target weights, not signals;
      - emits only positions, cash, turnover, transaction cost, gross exposure, net exposure, row count, date range, and boundary verdict;
      - blocks real market data, alpha/Sharpe/CAGR/max-drawdown/ranking metrics, alerts, broker calls, and promotion packets.
    - Phase G2/G3 fixture replay:
      - records one registered fixture candidate and one hash-linked proxy note before replay comparison;
      - calls `core.engine.run_simulation` for the V1 canonical replay proof;
      - compares only mechanical accounting fields;
      - emits `boundary_verdict = "v2_blocked_from_promotion"`;
      - keeps `promotion_ready = false` even when V1 and V2 match.
    - Phase G4 real canonical readiness:
      - uses one tiny Tier 0 `prices_tri` daily-bar slice only;
      - requires a dedicated manifest and reconciles SHA-256, row count, schema, and date range;
      - rejects Tier 2, public-web, operational-market-data, stale, ambiguous, duplicate-key, non-monotonic, non-finite, and impossible price/return evidence;
      - emits readiness only with `ready_for_g5`, not strategy performance;
      - keeps sidecars optional for the passing price slice and blocks stale sidecars only when explicitly required.
    - Phase G5/G6 real canonical replay and comparison:
      - G5 calls `core.engine.run_simulation` once on the G4 slice with predeclared neutral weights;
      - G6 runs V1 and V2 mechanics separately on the same real canonical slice and weights;
      - compares only mechanical accounting fields and records engine identity separately;
      - keeps `promotion_ready = false`, `v2_promotion_ready = false`, alerts blocked, broker calls blocked, and promotion packets blocked even when V1/V2 match;
      - does not emit alpha, Sharpe, CAGR, drawdown, rank, score, signal strength, or buy/sell decisions.
    - Phase G7 controlled candidate-family definition:
      - defines `PEAD_DAILY_V0` before any result observation;
      - declares hypothesis, universe, feature allowlist, finite parameter space, trial budget, data policy, validation gates, and multiple-testing policy;
      - uses manifest-backed append-only/versioned family definition artifacts;
      - blocks candidate generation, backtest/replay/proxy runs, alpha/performance metrics, rankings, alerts, broker calls, and promotion packets.
    - Artifacts:
      - `v2_discovery/registry.py`
      - `v2_discovery/fast_sim/boundary.py`
      - `v2_discovery/fast_sim/simulator.py`
      - `v2_discovery/replay/canonical_replay.py`
      - `v2_discovery/replay/comparison.py`
      - `v2_discovery/replay/canonical_real_replay.py`
      - `v2_discovery/replay/real_slice_v1_v2_comparison.py`
      - `v2_discovery/readiness/canonical_readiness.py`
      - `v2_discovery/readiness/canonical_slice.py`
      - `v2_discovery/families/registry.py`
      - `v2_discovery/families/schemas.py`
      - `v2_discovery/families/trial_budget.py`
      - `v2_discovery/families/validation.py`
      - `data/fixtures/v2_proxy/*`
      - `data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet`
      - `data/registry/candidate_families/pead_daily_v0.json`
      - `tests/test_candidate_registry.py`
      - `tests/test_v2_proxy_boundary.py`
      - `tests/test_v2_fast_proxy_synthetic.py`
      - `tests/test_v2_fast_proxy_invariants.py`
      - `tests/test_v2_canonical_replay_fixture.py`
      - `tests/test_g4_real_canonical_readiness_fixture.py`
      - `tests/test_g5_single_canonical_replay_no_alpha.py`
      - `tests/test_g6_v1_v2_real_slice_mechanical_comparison.py`
      - `tests/test_g7_candidate_family_definition.py`

3.37 Discretionary Augmentation Roadmap [Phase 65 G7.1] <- NEW
[FR-161 Step Set: Product Charter + Dashboard Taxonomy]
    - Objective:
      - reframe the roadmap before candidate generation so the system does not drift into generic alpha search by inertia.
    - Product charter:
      - Terminal Zero is a discretionary augmentation cockpit, not a trading bot;
      - roadmap focus is 90% supercycle gem discovery and 10% buying-range / hold-discipline prompting;
      - `SUPERCYCLE_GEM_DAILY_V0` is the primary product-family target;
      - `PEAD_DAILY_V0` remains valid as a tactical signal family and evidence module only.
    - Roadmap vocabulary:
      - "alpha search" becomes "de-risked upside discovery";
      - "strategy candidate" becomes "thesis / signal candidate";
      - "buy/sell signal" becomes "decision-support state";
      - "backtest result" becomes "evidence layer";
      - "alert" becomes "buying-range / hold-discipline prompt";
      - "V2 discovery" becomes "research sandbox";
      - "promotion" becomes "human-reviewed thesis approval".
    - Dashboard taxonomy:
      - thesis health;
      - entry discipline;
      - hold discipline;
      - flow and positioning;
      - regime.
    - Flow and positioning boundary:
      - short-squeeze and CTA-type signals are context, not automatic triggers;
      - lagged source cadence and source quality must be shown before downstream use.
    - Phase sequence:
      - G7.1 roadmap realignment;
      - G7.2 define Supercycle Gem Family, no search;
      - G8 create one thesis candidate card, no search;
      - G9 build dashboard signal map, no alpha search;
      - G10 begin bounded discovery inside one approved family;
      - G11 entry/hold discipline monitor;
      - G12 paper-only buying-range prompts.
    - Blocked scope:
      - no candidate generation, backtest, replay, proxy run, search, ranking, metric output, alert emission, broker call, live order, or promotion packet.
    - Artifacts:
      - `docs/architecture/product_roadmap_discretionary_augmentation.md`
      - `docs/architecture/dashboard_signal_taxonomy.md`
      - `docs/architecture/supercycle_gem_family_policy.md`
      - `docs/handover/phase65_g71_handover.md`

[DASH-2 Product Delta: Portfolio Allocation Runtime Slice]
    - Objective:
      - keep Portfolio Optimizer as the primary Portfolio & Allocation workflow while adding a below-the-fold YTD comparison.
    - Product behavior:
      - Portfolio Optimizer renders top-level, not behind an expander/toggle;
      - YTD Performance renders below optimizer output;
      - portfolio return reflects current optimizer weights when available;
      - SPY and QQQ are displayed as comparison benchmarks.
    - Data boundary:
      - yfinance adjusted-close overlay is used only for runtime display freshness;
      - selected-stock overlay fetching/scaling and strategy-metrics parsing are delegated to `core/data_orchestrator.py`, not the Streamlit view;
      - no canonical provider ingestion, candidate scoring, ranking, alerting, broker behavior, or candidate-card merge is authorized.
    - Artifacts:
      - `core/data_orchestrator.py`
      - `dashboard.py`
      - `views/optimizer_view.py`
      - `tests/test_dash_2_portfolio_ytd.py`
      - `tests/test_data_orchestrator_portfolio_runtime.py`

[Dashboard Architecture Safety Slice - 2026-05-11]
    - Objective:
      - remove Windows-unsafe and duplicated process-liveness behavior from runtime paths without changing product behavior.
    - Runtime safety:
      - `utils/process.py::pid_is_running` is the shared process-liveness helper;
      - direct runtime `os.kill(pid, 0)` probes are blocked outside the shared utility;
      - dashboard backtest spawn refuses a second job when a PID file points to a live process, rather than terminating an unverified PID.
    - Dashboard helper boundary:
      - Modular Strategies and Portfolio Builder fallback use one strategy-matrix initializer path;
      - dashboard portfolio price cleanup delegates to `core.data_orchestrator.clean_price_frame`.
    - Blocked scope:
      - no provider ingestion, canonical data write, strategy search, ranking, scoring, alerting, broker behavior, dashboard content redesign, or candidate-card dashboard merge.
    - Artifacts:
      - `utils/process.py`
      - `dashboard.py`
      - `data/updater.py`
      - `scripts/parameter_sweep.py`
      - `scripts/release_controller.py`
      - `backtests/optimize_phase16_parameters.py`
      - `tests/test_process_utils.py`
