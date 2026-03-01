Decision Log: Terminal Zero
Author: Atomic Mesh | Last Updated: 2026-03-01 (Stream 1 fail-loud bootstrap + Stream 4 strict container draft)

Part 1: Master Decision Log

| ID   | Component  | The Friction Point          | The Decision (Hardcoded)       | Rationale                                                |
|------|------------|-----------------------------|--------------------------------|----------------------------------------------------------|
| D-01 | etl.py     | Delisting Bias              | Merge dlret into ret           | Captures -100% bankruptcies in total_ret.                |
| D-02 | etl.py     | Split/Div Confusion         | Dual Schema                    | adj_close for Signals, total_ret for PnL.                |
| D-03 | etl.py     | Macro Availability          | macro.parquet                  | Global regime awareness (SPY/VIX Proxy).                 |
| D-04 | engine     | Look-Ahead Bias             | Shift(1) Enforcement           | Trade T+1 based on Signal T.                             |
| D-05 | engine     | Cost Blindness              | Turnover Tax (10bps)           | Deduct cost on every portfolio change.                   |
| D-06 | infra      | NaN Explosions              | Forward Fill                   | Prevent simulation crashes from missing data.            |
| D-07 | strategy   | API Rigidity                | Abstract Weights               | Decouple Strategy from Engine via BaseStrategy.          |
| D-08 | integration| Wide-Format Mismatch        | Matrix Injection               | Engine accepts pre-pivoted Returns Matrix (T x N).       |
| D-09 | data       | No cfacpr column            | adj_close = abs(PRC)           | Split Trap acknowledged. MVP only. No live trading.      |
| D-10 | data       | No High/Low prices          | Close-Only ATR                 | ATR ≈ abs(Close-PrevClose). k raised to 3.5.             |
| D-11 | data       | No VIX index                | VIX Proxy                      | Rolling StdDev of SPY * sqrt(252) * 100.                 |
| D-12 | data       | No Compustat fundamentals   | Quality Gate stubbed           | Historical MVP decision; superseded by D-29 PIT quality gate. |
| D-13 | strategy   | Binary On/Off regime        | 3-State Regime (0.5/0.7/1.0)  | Attack/Caution/Defense dimmer switch (historical baseline; superseded by later FR-041/FR-050/FR-070 regime contracts). |
| D-14 | strategy   | Black Box feeling           | Reason Codes                   | Strategy returns (weights, regime, details) for UI.      |
| D-15 | data       | Memory crash (23K permnos)  | Top 2000 Liquid Universe       | Filter by total dollar volume in DuckDB before loading.  |
| D-16 | optimizer  | Manual parameter nudging    | 2D Grid Search                 | Automated sweep of k and z. Output: Heatmap. ← NEW      |
| D-17 | optimizer  | Fixed k/z in all regimes    | VIX-Adaptive Parameters        | k, z = f(VIX). Tight in calm; loose in panic. ← NEW     |
| D-18 | optimizer  | Left-Side entry too early   | Wait-for-Confirmation          | Green Candle check: P(T) > P(T-1) before entry. ← NEW   |
| D-19 | strategy   | One k/z for all stocks      | Quantile Mapping               | k_i = 2.5 + 1.5×VolRank, z_i = -3.0 + 2.0×VolRank. Per-stock adaptive params. |
| D-20 | UX         | Raw PERMNO input            | Searchable Ticker Dropdown     | st.multiselect with tickers.parquet (23K mappings). Type "NV" → NVDA. |
| D-21 | data       | Static data (ends 2024)     | Append-Only Hybrid Lake        | Base (WRDS) + Patch (Yahoo) via DuckDB UNION ALL. Never rewrite 47M base. |
| D-22 | data       | Sequential ticker download  | Batch yf.download()            | Multi-ticker request 50x faster. Top 50/100/200 scope. Dashboard trigger. |
| D-23 | UX         | Binary SELL/BUY signals     | 5-State Classifier (FR-023)    | HOLD/BUY/WATCH/AVOID/WAIT. Forward-looking support levels, not stale "SELL". |
| D-24 | strategy   | All BUYs equal              | Conviction Scorecard (FR-024)  | 0-10 score: Trend(3)+Value(3)+Macro(2)+Momentum(2). Hardcoded, no LLM. |
| D-25 | data/UX    | Manual "Run Update Now"     | Smart Watchlist + Auto-Update  | watchlist.json persists selections. Auto-update on stale data. CLI script. |
| D-26 | strategy   | Naive conviction (StdDev/coin-flip) | L5 Alpha (Robust Z + ER) | MAD-based z-score resists crashes. Kaufman ER filters noise from trend. VIX trend. |
| D-27 | UX         | Multiselect + stacked cards  | Scanner + Detail Views (FR-026v2) | Radio toggle (scan/watchlist), always top-5, ticker search bar, drill-down. No permnos shown. |
| D-28 | data       | Stale prices for non-watchlist | JIT Single Ticker Patch (D-28) | "Bedrock + Fresh Snow" architecture. Auto-fetch Yahoo on drill-down if data > 3 days stale. |
| D-29 | data/strategy | Value Traps from price-only dips | PIT Quality Gate (FR-027) | Fundamentals keyed by release_date, daily broadcast via ffill, MVQ filter: ROIC>0 and Revenue YoY>0; stale/missing fundamentals fail-safe. |
| D-30 | data       | Universe too narrow vs institutional coverage | Top 3000 Optional Expansion (FR-030) | Expand investable set without forcing slower default runtime for all sessions. |
| D-31 | app/runtime| Top 3000 load pressure during pivot/concat | Dynamic Batch Sizing in `load_data()` | Use smaller batches when universe > 2500 (`200` vs `250`) to reduce memory spikes and improve stability. |
| D-32 | data/ops   | Missing context for risk concentration | Sector Map as Static Bedrock (FR-028) | Build once, merge at runtime; keeps scanner context-rich without API calls in hot path. |
| D-33 | data       | Sparse Yahoo fundamentals coverage | Compustat CSV Bedrock Ingestion (FR-031) | Load quarterly WRDS/Compustat file for materially higher PIT coverage in investable universe. |
| D-34 | data       | Mixed-source collisions on same release date | Source Precedence: Compustat > Yahoo | `rdq`-driven Compustat rows are preferred over yfinance restatements at `(permno, release_date)` key. |
| D-35 | data/quality | Symbol format drift between vendors | Deterministic ticker normalization + audit | Use exact + suffix/dot normalization and persist unmatched audit file for explicit gap tracking. |
| D-36 | data       | Metadata-only index exports masquerade as constituents | Hard Input Gate for R3000 PIT Loader (FR-032) | Fail fast unless WRDS file has required columns and sufficient rows; prevents hallucinated universe builds. |
| D-37 | app/data   | Need PIT membership universe for forward testing without breaking current runtime | Optional `universe_mode='r3000_pit'` in `load_data()` | Keeps default Top2000/Top3000 flow stable while enabling future date-aware universe selection. |
| D-38 | data/factors | YTD cashflow misread as quarterly flow | OANCFY Decumulation by (permno,fyearq,fqtr) | Prevents Q4 overstatement and restores quarter-true cashflow signals. |
| D-39 | data/factors | Valuation factor mismatch across debt/cash fields | Vectorized EV/EBITDA + Leverage Matrix (FR-033) | Standardized enterprise-value construction with safe denominator handling. |
| D-40 | infra      | Phase churn risk before catalyst layer | Infrastructure Frozen milestone | Lock PIT universe + fundamentals bedrock before adding event-driven alpha logic. |
| D-41 | strategy/UI | High-score picks can hide event risk near earnings | Catalyst Radar event overlay (FR-034) | Keep best candidates visible while flagging `earnings_risk` for <5-day blackout window. |
| D-42 | data/macro | Dual macro artifacts drift and hidden look-ahead risk | Single SSOT macro layer (`macro_features.parquet`) + conservative FRED lag policy | Prevents schema drift and enforces PIT safety by design (`T+1` for slow macro). |
| D-43 | data/perf | Macro rebuild risked >10s as history grows | Vectorized rolling percentile + parallel/date-bounded FRED pulls | Preserves PIT correctness while reducing runtime bottlenecks in FR-035 build path. |
| D-44 | app/strategy | Missing macro artifact could imply false “calm” regime | Defensive fallback (`regime_scalar=0.5`) + scalar-priority regime mapping | Fails safe (reduced risk) when macro layer is unavailable, avoiding full-risk exposure on data outage. |
| D-45 | data/liquidity | Need causal liquidity features with strict PIT discipline | Dedicated `liquidity_features.parquet` + H.4.1 lag rule (Wed→Fri) | Prevents look-ahead in Fed weekly series while adding flow/plumbing signals for FR-040. |
| D-46 | data/runtime | Liquidity build could silently degrade on partial inputs or stale locks | Fail-fast Yahoo critical checks + calendar end-date bounding + stale-lock recovery | Prevents writing misleading stress signals, respects requested build windows, and avoids deadlocks after crashed writers. |
| D-47 | strategy/runtime | Single scalar regime path mixes structural stress and sizing pace | Two-layer RegimeManager (`Governor` + `Throttle`) with fixed 3x3 scalar matrix | Makes exposure logic explicit, testable, and stable across data-source fallback paths for FR-041. |
| D-48 | strategy/risk | Need strict long-only safety in crisis while avoiding blind chase | Red matrix clamps (`RED+NEG=0.0`, `RED+NEUT=0.0`, `RED+POS<=0.20`) [FR-041 historical freeze] | Historical contract snapshot; current runtime precedence is FR-050/FR-070 budget map (`RED=0.0`). |
| D-49 | strategy/validation | Regime tuning can drift without anchored historical behavior checks | FR-042 strict truth table + 2017 GREEN guardrail | Enforces crisis defensiveness (2008 Q4, 2020 Mar, 2022 H1) while preventing chronic risk-off behavior during calm regimes. |
| D-50 | strategy/validation | FR-042 strict run blocked by low-vol false RED triggers and short-window recovery NaNs | Add volatility gates to credit/liquidity RED triggers and allow recovery fallback to full-sample metric when crisis-window recoveries are undefined | Preserves crisis capture while preventing mathematically impossible failures in fixed short windows. |
| D-51 | strategy/backtest | Cash ETF history is incomplete across full sample | FR-050 cash hierarchy (`BIL -> EFFR/252 -> flat 2%/252`) | Preserves realistic cash carry in pre-/post-ETF gaps and avoids biased zero-cash assumptions. |
| D-52 | strategy/backtest | Regime signal can leak if applied same-day to returns | Enforce deterministic `t signal -> t+1 executed weight` in FR-050 | Keeps walk-forward PnL strictly point-in-time and execution-realistic. |
| D-53 | data/features | Selector layer lacks stock-level alpha vectors | Create FR-060 `feature_store` with ranking/sizing/execution features | Separates capital-preservation governor from asset-selection alpha engine. |
| D-54 | data/features | Historical lake is close-only, but YZ/ATR are OHLC-native | Add explicit close-only fallback modes (`yz_mode`, `atr_mode`) | Keeps pipeline operational without hidden assumptions while preserving future OHLC upgrade path. |
| D-55 | strategy/alpha | Need robust tuning without curve-fit drift | FR-070 fixed-vs-adaptive governance + walk-forward-only tuning | Preserve structural philosophy while allowing regime-aware sensitivity changes. |
| D-56 | strategy/execution | Daily rank jitter can overtrade and kill alpha net of costs | Hysteresis rank buffer (`enter<=5`, `hold<=20`, `exit>20`) | Reduces churn while preserving strong-signal entries. |
| D-57 | strategy/risk | Stop logic can drift downward and re-open left-tail risk | Ratchet-only stop (`stop_t=max(stop_{t-1}, new_stop_t)`) | Locks gains and prevents stop widening after entry. |
| D-58 | strategy/optimizer | Parameter hunts can silently mutate structural behavior | FR-080 FIX vs FINETUNE governance split | Keeps structural rules frozen while allowing bounded adaptive honing only where intended. |
| D-59 | strategy/validation | Optimizer loops can overfit by peeking into OOS outcomes | FR-080 WFO-only promotion gate with strict OOS isolation | Preserves causal validation by forbidding OOS data in search objective, ranking, and tie-breaks. |
| D-60 | strategy/perf | FR-080 grid search underutilized CPU despite cached data | Optional multi-process candidate evaluation + sequential fallback | Preserves deterministic behavior while scaling candidate throughput using available cores. |
| D-61 | strategy/optimizer | Multiple FR-080 candidate outputs required a single promoted baseline | Promote strict-pass defaults (`alpha_top_n=10`, `hysteresis_exit_rank=20`, `adaptive_rsi_percentile=0.05`, `atr_preset=3.0 -> 3.0/4.0/5.0`) | Establishes one production SSOT default after WFO strict pass and prevents runtime/backtest config drift. |
| D-62 | strategy/runtime | Tuned FR-080 promotion failed FR-070 verifier gate | Hard-stop rollback: demote promoted params to research-only and restore guarded runtime defaults (`alpha disabled`, `adaptive_rsi_percentile=0.15`) | Prevents shipping unstable tuning and enforces verifier-first runtime promotion policy. |
| D-63 | strategy/optimizer | Train-winner could pass stability but still be operationally inactive | Phase 16.2 activity guardrails (`trades_per_year > 10`, `exposure_time > 0.30`) in promotion gate, computed on OOS window only | Prevents starvation/under-trading profiles from promotion while preserving train-only ranking and OOS isolation. |
| D-64 | strategy/alpha | Dip-only entry gate can starve valid trend/liquidity candidates | Phase 16.2 Step 3 Dip OR Breakout entry (`dip_entry OR breakout_entry_green`) with PIT-safe prior-50d-high | Restores GREEN-regime trade flow while preserving AMBER/RED restraint and no-look-ahead discipline. |
| D-65 | strategy/safety | Malformed regime tokens can bypass intended RED/AMBER/GREEN contracts | Canonical regime normalization (`strip().upper()`) with unknown-state fail-safe to RED budget | Enforces deterministic exposure safety and prevents accidental risk escalation from token formatting or invalid states. |
| D-66 | data/features | Global top-N liquidity universe can over-concentrate selector coverage across long windows | Add feature-store `universe_mode` with default `yearly_union` (`yearly_top_n=100`) and keep `global` legacy flag path | Expands PIT coverage by unioning per-year liquid leaders while preserving operational safety with memory-envelope guards. |
| D-67 | strategy/optimizer | Train-ranked winner selection could ignore promotability and leak policy intent | Promotable-first, train-only deterministic ranking (`objective`, `train_cagr`, `train_robust`, `train_ulcer`, parameter tie-breakers) with no OOS ranking fields | Aligns FR-080 selection behavior with governance by promoting only candidates that pass stability and activity guardrails. |
| D-68 | infra/program | Parallel infra refactor can conflict with active optimizer reader runs | Phase 17 gated execution policy with explicit run guard (`phase16_optimizer.lock` + process check + artifact-bundle completion) before writer milestones | Prevents reader/writer conflicts and preserves a clean attribution boundary between strategy outcomes and infrastructure changes. |
| D-69 | data/updater | Large Yahoo scopes stall or partially fail under single-call batching | Chunked parallel Yahoo downloads with ordered merge and key dedupe (`ticker`,`date`) before atomic patch publish | Improves throughput/resilience for Top500/Top3000 updates while preserving lock-safe, append-only patch semantics. |
| D-70 | data/features | Full-window feature rebuilds are too costly for daily refresh cadence | Incremental feature rebuild with warmup replay, atomic upsert merge, and duplicate-key override (`date`,`permno`) | Converts daily builds from full recompute toward bounded append cost while protecting rolling-window correctness. |
| D-71 | data/ops | Feature artifact failures were not explicitly audited in integrity gate | Extend `scripts/validate_data_layer.py` with feature-store checks (row count, null keys, duplicate keys, freshness gap) | Adds enforceable data-layer acceptance evidence before downstream strategy/optimizer runs. |
| D-72 | strategy/optimizer | Dip-only vs breakout-style entries were not testable as first-class optimizer dimensions | Add FR-080 tournament `entry_logic` grid (`dip`,`breakout`,`combined`) with deterministic train-only tie-break integration and artifact fielding | Enables regime-sensitive entry discovery without violating OOS-isolation governance or promotion guardrails. |
| D-73 | strategy/ops | Long FR-080 tournament runs lacked visible progress and live leaderboard telemetry | Add real-time optimizer heartbeat (`phase16_optimizer_progress.json`) and interim leaderboard (`phase16_optimizer_live_results.csv`) with periodic console ETA updates | Enables operator monitoring/polling without waiting for end-of-run artifacts. |
| D-74 | data/fundamentals | Price-only and partial-fundamental snapshots could not support first-principles moat/demand ranking | Expand PIT fundamentals schema with conservative EPS/equity policy (`net_income_q`, `equity_q`, `eps_basic_q`, `eps_diluted_q`, `eps_q`, `eps_ttm`, `eps_growth_yoy`, `roe_q`) across Yahoo + Compustat loaders and snapshot broadcaster | Enables robust fundamental scoring with explicit diluted-EPS priority, equity fallback, and release-date-safe propagation into runtime selector contexts. |
| D-75 | data/feature-architecture | Parallel script hardening alone could not support agent-driven factor evolution or restatement-safe backtests | Merge Stream A+B into a declarative-engine foundation and bitemporal fundamentals contract: explicit capital-cycle raw fields, `published_at` as-of filtering (`published_at <= trade_date`), conservative fallback (`filing_date` else `fiscal_period_end + 90d`) | Preserves PIT integrity under restatements while preparing feature computation for spec-driven extension instead of hardcoded script edits. |
| D-76 | data/features | Hardcoded feature blocks were not agent-extensible and repeated expensive recompute on identical spec/input states | Refactor `feature_store` into a declarative `FeatureSpec` executor with registry-driven compute and add hash-addressed build cache (`features_<cache_key>.parquet`) | Enables safe feature extension without editing core compute flow and skips redundant rebuilds via deterministic cache reuse. |
| D-77 | data/fundamentals | Sparse bitemporal fundamentals were correct but too slow for repeated runtime joins | Build a dense daily vintage panel with interval-based PIT expansion (`published_at` to `next_published_at`) plus manifest-driven source-signature cache (`daily_fundamentals_panel.parquet` + manifest) | Preserves strict as-of correctness under restatements while making feature/optimizer joins fast and reproducible for each input vintage. |
| D-78 | strategy/validation | Capital-cycle logic needed a deterministic bubble-era sanity check independent of Yahoo coverage gaps | Add CSCO 2000 event-study harness with Compustat fallback and inventory-commitment-sensitive discipline stress (`backtests/event_study_csco.py`) | Verifies that score can de-rate names under rising inventory commitments even when moat remains positive, and prevents silent logic regressions in future refactors. |
| D-79 | strategy/validation | CSCO-style inventory penalty may over-fire on cyclical semis during trough-to-recovery transitions | Add MU 2016 paradox stress run (rally-positive gate) and mark cyclical-exception requirement when score remains negative during confirmed price supercycle | Prevents shipping a discipline term that systematically false-sells cyclical leaders and defines the next research patch target. |
| D-80 | strategy/factor | Discipline penalty needed explicit efficiency override during inventory-led ramps | Implement Turnover Gate (`delta(revenue/inventory) > 0.05 => waive discipline penalty`) in FeatureSpec discipline logic and event-study scorer, then re-run CSCO/MU twin checks | Preserves Cisco de-rating behavior while testing whether turnover-only override can unban cyclical recoveries; establishes whether additional cyclical exception features are required. |
| D-81 | strategy/factor | Turnover-only override remained insufficient for cyclical recoveries and lacked leading inventory-quality signals | Implement Inventory Quality Gate with weighted soft-vote (`book_to_bill`, `gm_accel`, `delta_dso`) across fundamentals schema, FeatureSpec discipline logic, and event-study scorer, with missing-signal fallbacks | Preserves Cisco de-rating while introducing leading quality classification for inventory builds; creates a measurable bridge from “inventory level” to “inventory quality” and isolates remaining MU strict-positivity gap for next patch. |
| D-82 | strategy/factor | Discrete inventory-quality gates remained brittle in cyclical transitions and overfit edge conditions | Pivot to continuous proxy gate (`z_inventory_quality_proxy`) using quarterly acceleration/bloat terms with waiver rule `z_inventory_quality_proxy > 0` and no-new-fetch policy | Reduces binary gate brittleness, preserves PIT semantics, and improves cyclical recovery handling without adding new external data dependencies. |
| D-83 | governance/docs | Plan/report structure drift and missing institutional memory | Add mandatory planning contract (high confidence, low certainty, boundary), self-learning feedback loop (`docs/lessonss.md`), SAW reporting format, and skill hooks (`.codex/skills/saw`, `.codex/skills/research-analysis`) in `AGENTS.md` | Standardizes decision quality visibility, enforces post-round review discipline, and creates repeatable research-backed planning behavior. |
| D-84 | data/runtime | Strict fail-fast external checks can stall refresh workflows during provider outages | On critical upstream data failure, keep last-successful artifact in service, skip unsafe publish, emit stale-data alert, and require explicit resume note before next publish | Preserves data integrity while maintaining operational continuity during transient provider failures. |
| D-85 | governance/review | Review output style varied by session and missed explicit option tradeoffs | Add a mandatory interactive review protocol in `AGENTS.md` (Big/Small mode gate, section cadence, numbered issues with lettered options, file:line evidence, recommended-first options, explicit user confirmation before implementation) | Improves review consistency, keeps decisions auditable, and aligns recommendations with user engineering preferences without over-expanding process overhead. |
| D-86 | governance/pm | Snapshot hierarchy remained generic and produced cluttered planning views | Adopt project-based hierarchy (`L1` pillar, `L2` streams, `L3` stages), stage-specific active-stream reporting, one-stage expansion loop, and trigger-based optional skills (`se-executor`, `architect-review`) with `>=2`-round escalation-by-approval | Improves PM traceability, keeps planning MECE, reduces formatting leakage, and adds rigor only when risk/complexity warrants it. |
| D-87 | governance/saw | Inherited out-of-scope High findings could block unrelated docs-only rounds indefinitely | Scope SAW blocking to in-scope Critical/High findings, while carrying inherited out-of-scope High findings in Open Risks with owner/target milestone and requiring explicit acceptance before milestone close | Preserves review rigor without deadlocking governance updates on pre-existing external debt. |
| D-88 | strategy/research | Event-study-first flow could not answer cross-sectional efficacy question for proxy gate | Promote cross-sectional double-sort evaluator with HAC/Newey-West and optional Fama-MacBeth as the primary Phase 17.1 validation harness | Makes proxy-gate validation reproducible at cross-sectional scale and aligns acceptance to spread/t-stat evidence instead of anecdotal event windows. |
| D-89 | data/features | Incremental feature updates still risked full-table rewrite cost | Convert `features.parquet` from single file to Hive-style partitioned dataset (`year=YYYY/month=MM`) with one-time migration and partition-only upsert rewrites | Restores practical iteration speed for repeated research loops while preserving atomic publish guarantees and PIT-safe storage semantics. |
| D-90 | strategy/statistics | Dense parameter search can overfit and overstate Sharpe under multiple testing | Standardize Phase 17.2 sweep on full combinatorial CSCV (`S` even blocks) + PBO + correlation-adjusted `N_eff` and DSR non-normality adjustment | Adds formal data-snooping controls and promotes variants using deflated risk-adjusted evidence rather than raw in-sample Sharpe. |
| D-91 | strategy/ops | Long-running sweeps could lose progress and misalign fine-search focus after interruptions | Add deterministic parameter-hash variant IDs, checkpoint/resume cadence, and DSR-first coarse anchor (`DSR -> t_stat_nw -> period_mean`) in sweep engine | Prevents wasted recompute, preserves stable identity across grid mutations, and keeps refinement centered on robust (deflated) candidates. |
| D-92 | data/perf | Partitioned upsert still paid avoidable per-partition DuckDB session/read overhead | Batch touched partition reads with a single DuckDB connection inside `_atomic_upsert_features` before per-partition atomic rewrites | Reduces connection churn and repeated scan overhead while preserving partition-scoped atomic write semantics. |
| D-94 | strategy/ticker-pool | Quarterly centroid drift and circular fallback risk degraded anchor intent in Mahalanobis scoring | Replace cyc centroid with per-slice anchor-injected mean in z-space (`MU`,`LRCX`,`AMAT`,`KLAC`,`STX`,`WDC`) and enforce `score_col` as pre-pool metric only; when anchors are missing, fallback to top-k by pre-pool score with critical logging | Removes centroid drift, blocks chicken-and-egg score recursion, and preserves deterministic fallback behavior with explicit telemetry. |
| D-103 | strategy/ticker-pool | Pre-pool ranking lacked deterministic sector context visibility and no explicit Path1 directive telemetry contract | Attach `sector/industry` from static `sector_map.parquet` into conviction frame before `rank_ticker_pool` using permno-first/ticker-fallback deterministic mapping; emit `DICTATORSHIP_MODE` and Path1 telemetry into sample/summary artifacts | Keeps ranking inputs context-aware without runtime API calls and creates auditable Path1 directive evidence for each slice run. |
| D-104 | strategy/ticker-pool | Path1 geometry/runtime gates could silently degrade when projection failed, sparse slices were skipped, or unknown-sector rows collapsed balanced resampling | Fail fast on non-finite sector-projection residualization, add explicit slice-skip logging, exclude `UNKNOWN` from sector-balance depth checks, and expose `--dictatorship-mode on/off` toggle in slice runner with model telemetry parity | Prevents silent geometry corruption, improves operational observability, preserves deterministic balanced-resample behavior under partial context coverage, and enables controlled de-anchor experiments. |
| D-105 | data/macro | Macro stress signals were mixed with regime features and lacked a standalone daily hard-gate artifact for strategy consumption | Add `macro_gates.parquet` built from PIT-safe QQQ drawdown/trend and VIX term-structure adaptive labels (`slow_bleed`, `sharp_shock`, backwardation) with explicit state/scalar/cash/momentum outputs | Separates signal generation from execution controls, keeps gate logic auditable, and enables deterministic strategy consumption without re-computing overlays at runtime. |
| D-106 | strategy/regime | Macro hard-gate outputs could leak same-day information into execution sizing/entry decisions | Enforce strict `t -> t+1` gate consumption in Phase 20 path (`state`, `scalar`, `cash_buffer`, `momentum_entry`) and route baseline run through centralized `macro_gates.parquet` | Preserves point-in-time discipline for the strategy execution layer and cleanly decouples L2 signal generation from portfolio decision timing. |
| D-107 | data/macro | Manual M&A CSV exports block automated Sector Distress indexing | Built WRDS Postgres pipeline for Moody's Orbis Americas (`data/orbis_loader.py`) | WRDS API allows automated SQL filtering, prevents local memory bloat, and enables broader NAICS sector screening. |
| D-108 | strategy/macro | Zephyr M&A deal counts lag actual deployed capital | Substituted Zephyr deal counts with Cashflow Proxies (`ibaq` / `toas`) | Captures actual deployed capital for consolidation (Acquisition Yield) rather than uncompleted deal/announcement volume. |
| D-109 | strategy/macro | Private company reporting latency introduces look-ahead bias in daily signals | Implemented strict 90-day Bitemporal Lag via `merge_asof` | Prevents look-ahead bias by intentionally delaying private quarterly signals before interpolating them onto a daily timeline. |
| D-124 | governance/environment | Dependency manifests and execution commands drifted, causing false-negative test failures outside `.venv` | Lock `requirements.txt` to mirror `pyproject.toml`, enforce `.venv\Scripts\python` in runbook/governance docs, and set pytest cache to writable `.venv/.pytest_cache` | Establishes deterministic install/runtime behavior across local shells and CI/CD while removing cache-path ACL noise from validation runs. |
| D-125 | control-plane/testing | Execution orchestrators lacked direct regression coverage on safety/scheduling branches | Add focused test suites for `main_console.py` and `main_bot_orchestrator.py` with monkeypatched control-plane seams (TTY/non-TTY confirmation, payload guardrails, subprocess scheduling loop) | Protects operator-critical orchestration behavior from drift and establishes deterministic coverage for P1 completion before P2 decoupling. |
| D-126 | architecture/app | `app.py` mixed Streamlit rendering with heavy data-access and control-plane state logic | Extract data loading and auto-update/watchlist control decisions into service modules (`data/dashboard_data_loader.py`, `core/dashboard_control_plane.py`) and keep `app.py` as thin wrappers + UI routing | Reduces coupling, creates direct unit-test boundaries for non-UI logic, and de-risks subsequent P2 app-layer decoupling work. |
| D-131 | strategy | Buy & Hold Underperformance | Infinity Governor | Expanded stops to 5.0x+ for high R-squared, low convexity assets. 20-day lookback, NaN failsafe to 3.0x ATR. |
| D-132 | execution | Catching Falling Knives | Waterfall Support | If 21-EMA breaks, target 50-SMA. If 50 breaks, target 200. Never buy resistance. Day Limit Orders only. |
| D-133 | execution | Retail Stop-Run Wicks | Empirical Stink Bid | Bid below support based on cluster physics (Heavies -5%, Sprinters -11%, Scouts -16%). Zero FOMO on missing fills. |
| D-134 | derivatives | IV Crush on Manias | The Trinity Protocol | 80-Delta LEAPs for Linear Compounders only. De-lever to Spot Stock when Convexity > 1.5. Strict EOD Macro polling at 4 PM EST. |
| D-135 | strategy | Fundamental Kills momentum | Permissive Gates | Momentum Override for NVDA (ignores P/S > 20). Channel Stuffing downgraded to Warning (Bans LEAPs). |
| D-136 | execution/control-plane | Exposed secrets + weak fail-open execution paths | P0 fail-closed control pack | Removed hardcoded broker secrets, enforced paper-default with explicit live break-glass (`TZ_ALPACA_ALLOW_LIVE=YES`), added orchestrator timeout/non-zero hard-stops, and centralized patch writes through lock+atomic facade. |
| D-137 | P1/verification | P1 closeout risk paths were implemented across multiple modules but lacked one consolidated validation artifact | Publish an implementer validation evidence pack covering strict missing returns on executed exposures, strict `client_order_id` idempotency wiring, and fundamentals ingest checkpoint/resume state-machine behavior | Makes P1 closure auditable with explicit file/line proof + deterministic test evidence before milestone sign-off. |
| D-138 | P1/reconciliation | Reviewer re-check exposed remaining in-scope integrity edges (CID recovery mismatch and semantic checkpoint corruption paths) | Apply fail-closed reconciliation patch set: enforce CID uniqueness+mandatory CID+recovery-intent match, validate checkpoint metadata semantics and checkpoint-row integrity, and add wrapper strict/permissive regression coverage | Eliminates residual false-accept and checkpoint-corruption risks before SAW close, while carrying inherited scalability debt as explicit open risk. |
| D-139 | execution/risk-controls | Order submit path needed a deterministic pre-submit risk gate with auditable hard blocks | Add immutable `RiskInterceptor` in the rebalancer path with hard checks for `max_single_asset_weight`, `max_sector_weight`, `VIX > 45` buy kill-switch, and parametric VaR proxy; enforce fail-closed behavior and atomic `logs/risk/` breach audit writes | Creates a reproducible risk boundary between validation and broker submission, preserves sell-side exit capability during volatility shocks, and provides block-level forensic evidence with optional batch-halt semantics. |
| D-140 | data/fundamentals | Legacy `release_date` forward-fill broadcaster could leak post-restatement values into earlier simulation dates | Unify daily fundamentals consumption on published-time interval semantics via `daily_fundamentals_panel` (`published_at <= date < next_published_at`) and route feature-store daily fundamentals through panel-backed path | Removes the highest-probability look-ahead vector and aligns runtime feature generation to the bitemporal publish-time truth contract. |
| D-141 | data/features | Standard deviation z-scaling can explode under sparse/outlier-heavy cross-sections and hide data sparsity incidents | Add robust cross-sectional scaling with hard formula `robust_sigma = max(1.4826 * MAD, epsilon_floor)` and percentile fallback when `window_size < min_window_size`; publish fallback telemetry (`fallback_rows`, `fallback_rate`) | Stabilizes feature normalization under fat tails/sparse windows while making data-quality fallback behavior observable in build logs/artifacts. |
| D-142 | data/updater | Monolithic patch read-concat-rewrite would grow linearly in memory/I/O with universe size | Move Yahoo patch writes to partitioned year/month incremental upsert with touched-partition atomic swap and legacy single-file migration at same `PATCH_PATH` | Converts patch refresh cost from full-file rewrite to touched-partition updates and preserves lock-safe publish semantics as coverage grows. |
| D-143 | data/feature-store | Incremental multi-partition upsert could partially commit on mid-loop failure | Add dataset-level single-visible commit: stage full dataset root update, write commit manifest with cache/tombstone policy, then atomic root swap; enforce read-side policy check (`stale_while_revalidate_sec=0`, `tombstone_priority=enforced`) | Eliminates partial-commit corruption risk and establishes explicit read-consistency policy for commit/tombstone propagation in the truth layer. |
| D-148 | data/storage-locking | Crash interruptions between backup swap operations could strand live paths and tokenless lock release could remove locks without ownership proof | Add backup-swap recovery preflight for updater/feature-store (`*.bak.*` restore), allow self-owner recovery under active lock, and enforce token-owned lock release (`no token => no delete`) across feature-store build and updater lock lifecycle | Closes crash-window data-loss paths, preserves single-writer safety, and ensures lock release operations remain ownership-authenticated under failure/restart conditions. |
| D-149 | data/updater | Truth-layer refresh could partially succeed or false-pass when Yahoo chunk failures were under-counted | Enforce fail-closed updater contract: abort before writes on `failed_chunks > 0`, classify batch transport exceptions as chunk failures, and treat full chunk failure as update failure (`success=False`) | Prevents silent partial refreshes and ensures update success semantics reflect complete, verifiable chunk coverage for the requested window. |
| D-150 | data/observability | Panel-load failures in fundamentals daily build were silently swallowed, obscuring degraded PiT mode operation | Emit explicit warning telemetry on panel-load exception and fallback activation (`mode=quarterly_published_at`, row/date/permno coverage) and lock with regression tests | Improves degraded-mode observability so operators can detect and investigate panel-service failures without silent behavior drift. |
| D-151 | data/feature-store | Full-root staging (`copytree`) for incremental upserts creates O(total_dataset_size) write amplification and slows commit windows as universe/history scales | Replace incremental commit path with manifest-pointer MVCC (`CURRENT` -> immutable v2 manifest), touched-partition-only writes, and deterministic pointer swap | Converts incremental write cost to touched partitions, preserves atomic commit semantics, and aligns truth-layer storage with lakehouse-style commit control. |
| D-152 | data/feature-store integrity | Manifest pointers without cryptographic seals can silently accept corrupted/partial parquet files | Add per-partition SHA-256 seals in manifest v2 and enforce hash verification before reader scan acceptance | Makes read acceptance fail-closed against bit-rot/partial-write corruption and ensures backtests consume cryptographically validated artifacts only. |
| D-153 | data/feature-store concurrency | Aggressive garbage collection can delete files still needed by long-running readers under MVCC | Introduce explicit GC grace policy in manifest contract (`retention_hours_min >= 24`) and retain tombstoned files by default (no aggressive delete in commit path) | Prevents mid-run `FileNotFound` failures for active readers and establishes a safe baseline for future GC/compaction automation. |
| D-154 | data/feature-store publish control | Manifest-v2 publish primitives could be invoked without proving lock ownership token when a lock file existed | Enforce token-validated publish authorization (`missing/mismatch token => block`) in feature-store publish paths and propagate updater lock token through run-build write/upsert calls | Eliminates tokenless concurrent publish race windows and preserves single-writer ownership semantics at commit/pointer boundaries. |
| D-155 | data/feature-store read integrity | Partitioned read path accepted downgraded manifest versions and did not verify manifest partition-key/file-path congruence | Require `manifest.version == v2` for partitioned scans and assert `derived_partition(file_path) == manifest_partition_key` before accepting reads | Closes fail-open metadata drift vectors so reader acceptance remains fail-closed under manifest tampering or key/path divergence. |
| D-156 | data/feature-store bootstrap safety | Manifest bootstrap relied on partition file mtime ranking when pointer lineage was missing, creating non-deterministic state reconstruction risk | Remove mtime winner heuristic and raise `AmbiguousFeatureStoreStateError` for existing partitioned stores without verifiable v2 lineage; allow unsealed bootstrap only for same-process full-rebuild handoff | Enforces Jidoka fail-loud semantics and prevents silent state drift from filesystem timestamp inference. |
| D-157 | data/feature-store tombstone governance | Tombstone retention/prioritization contracts were declared but not fully enforced on read acceptance | Enforce tombstone schema (`retained_until_utc` required) and block scans when active files overlap tombstoned files (`tombstone_priority` hard gate), with adversarial tests | Physically blocks zombie-read windows and aligns reader behavior to strict tombstone-over-cache invariants. |
| D-158 | release/mlops container determinism | Existing runtime image lock was present but lacked a strict orchestrator-focused draft with deterministic snapshot apt policy and explicit OS package pins | Add `Dockerfile.orchestrator.strict` draft using digest-pinned base, fixed Debian snapshot source, version-pinned runtime libs, and SHA-256 lock-artifact verification before dependency install | Establishes an immutable artifact baseline for orchestrator deployment hardening and prepares Stream 4 deterministic release promotion path. |

Part 2: Decision Rationale (Phase 4 — Optimizer)

D-16: 2D Grid Search
  Problem: User manually nudges k (stop) and z (entry) sliders, relying on intuition.
  Solution: Run all 600+ (k, z) combinations in a vectorized batch.
  Metric: Ulcer-Adjusted Sharpe = CAGR / Ulcer Index.
    Ulcer Index = sqrt(mean(drawdown^2)) — captures both depth AND duration of pain.
  Output: 2D Heatmap where color = metric value. User picks the "Golden (k, z)".
  Risk: Overfitting to historical data. Mitigated by:
    1. Using rolling 5-year windows (Walk-Forward validation).
    2. Preferring "plateaus" over "peaks" in the heatmap (robustness).

D-17: VIX-Adaptive Parameters
  Problem: A fixed k=3.5 may be too tight during panics and too loose during calm.
  Solution: Make parameters slaves to the Regime:
    | VIX < 15  | k=2.5, z=-1.5 | Tight stops, buy mild dips    |
    | VIX 15-25 | k=3.5, z=-2.5 | Standard                      |
    | VIX > 25  | k=4.5, z=-3.5 | Loose stops, deep dips only   |
  Confidence: 9/10. This directly solves the FOMO-vs-Pain tension.

D-18: Wait-for-Confirmation ("Green Candle")
  Problem: Dip entries at z=-2.5 sometimes trigger while the stock is still falling.
  Solution: Z-Score triggers the "Ready" state. Entry only CONFIRMS when:
    Price(T) > Price(T-1) (first "green candle" after the dip).
  Confidence: 10/10. Dramatically reduces Left-Side entries.
  Statistical Basis: Mean-reversion signals have higher win rates when
    the reversal has objectively begun (price turns up).

Part 3: Historical Build Log

Phase 1 (2026-02-12): ETL + Engine
  - Wrote etl.py (DuckDB pipeline for 3.7GB CRSP CSV).
  - Wrote engine.py (Vectorized kernel with Shift/Cost walls).
  - Initial backtest: -82% due to Split Trap (D-09).

Phase 2 (2026-02-13): 3-Regime Strategy
  - Added Attack/Caution/Defense logic (D-13).
  - Strategy returns (weights, regime, details) tuple (D-14).
  - Marginal DD improvement (-82.3% → -81.4%). Split Trap dominates.

Phase 3 (2026-02-13): Investor Cockpit
  - Created InvestorCockpitStrategy with parameterized k and z.
  - Dashboard: Signal Monitor with Macro Advisor.
  - Visualization: Stop Level (Red) + Buy Zone (Green) overlay.
  - Close-Only data constraint acknowledged (D-10).

Phase 4 (2026-02-13): Parameter Optimizer ← PLANNED
  - Grid Search over (k, z) parameter space.
  - Adaptive Regime Parameters (D-17).
  - Wait-for-Confirmation logic (D-18).

Phase 4.2 (2026-02-13): Live Data + UX
  - Searchable Ticker Dropdown (D-20). Replaced PERMNO text input.
  - Yahoo Bridge: Append-Only Hybrid Lake (D-21).
  - Batch download via yf.download (D-22). Top 50/100/200 scopes.
  - Data Manager tab in dashboard for one-click updates.
  - Memory-safe: base parquet never loaded into pandas.
    OOM at 47M rows → solved by DuckDB-only queries + separate patch file.

Phase 4.3 (2026-02-14): Scanner Cockpit Redesign (D-27) ← NEW
  - Replaced st.multiselect + stacked cards with scanner+detail views.
  - scan_universe(): 2-pass filter (MA200 gate → L5 Alpha scoring).
  - views/scanner_view.py: High Conviction Scans + My Watchlist tables.
  - views/detail_view.py: Single-ticker chart + action report card.
  - Router in render_investor_cockpit() dispatches via session state.
  - [D-28] JIT Patch: views/jit_patch.py auto-fetches Yahoo data for stale tickers on drill-down.
    "Bedrock + Fresh Snow" — WRDS static base (2000-2024) + Yahoo on-demand (2025-now).

Phase 5 (2026-02-14): Quantamental Integration (D-29)
  - Added PIT quality layer with release-date discipline.
  - Scanner now enforces Pass 1.5 Quality Gate (hard filter).
  - Watchlist/details keep symbols visible but apply quality penalty behavior.

Phase 6 (2026-02-14): Portfolio Optimizer
  - Added optimizer module (inverse-volatility + mean-variance SLSQP + fallback).
  - Added optimizer view with allocation chart and shares-to-buy table.

Phase 7 (2026-02-14): Sector Context Upgrade (D-32)
  - Implemented static sector/industry map builder.
  - Merged sector context into scanner and fundamentals latest view.

Phase 8 (2026-02-14): Catalyst Radar Foundation — Steps 1-6 (D-30, D-31) ✅
  - Expanded scope support to Top 3000:
    - `data/updater.py`
    - `data/fundamentals_updater.py`
    - `data/build_sector_map.py`
    - Data Manager scope in `app.py`
  - Hydrated data foundation:
    - `fundamentals.parquet`: 10,219 rows
    - `fundamentals_snapshot.parquet`: 1,680 rows
    - `sector_map.parquet`: 3,000 rows
    - max `release_date`: 2026-03-17
  - Runtime validation:
    - Top 2000: load 15.356s, scan 0.227s, gate trend=6 quality=310 survivors=2
    - Top 3000: load 21.307s, scan 0.307s, gate trend=6 quality=432 survivors=2
  - Rollout stance: keep default at Top 2000; Top 3000 remains operator-selected until Catalyst layer (Steps 7-11) is shipped.

Phase 8 (2026-02-14): Compustat Bedrock Expansion (FR-031, D-33..D-35) ✅
  - Added loader: `data/fundamentals_compustat_loader.py`
    - Input: `data/e1o8zgcrz4nwbyif.csv`
    - Scope guardrail: Top 3000 liquid symbols only
    - PIT release date: `rdq`, fallback `datadate + 45d`
    - Revenue YoY formula: `(revenue_q - lag4(revenue_q)) / lag4(revenue_q)` via DuckDB window
  - Merge behavior:
    - Canonical key: `(permno, release_date)`
    - Precedence: `compustat_csv > yfinance`
    - Safety: lock + atomic writes + timestamped backups
  - Results:
    - Match coverage vs Top3000: 2781/3000 (92.70%)
    - fundamentals rows: 10,219 -> 225,640
    - snapshot rows: 1,680 -> 2,819
    - Scanner gate (Top3000): trend=6 quality=428 survivors=2

Phase 8 (2026-02-15): R3000 PIT Universe Scaffold (FR-032, D-36..D-37) 🟡
  - Added `data/r3000_membership_loader.py`:
    - Normalizes WRDS membership rows and maps ticker -> permno with audit trail.
    - Builds `universe_r3000_daily.parquet` via PIT date-window expansion.
  - Added optional `universe_mode='r3000_pit'` to `app.load_data()`.
  - Current blocker:
    - `data/t1nd1jyzkjc3hsmq.csv` failed input gate (metadata-only, 0 usable constituent rows).
    - Awaiting full WRDS constituent-history export for production run.

Entry 2026-02-14: Status: Infrastructure Frozen.
  Action:
    - Implemented PIT index-universe framework via Russell 3000 membership loader scaffold.
    - Hardened Top3000 fundamentals bedrock with PIT clamp and snapshot hygiene.
  Significance:
    - Backtests now maintain point-in-time visibility constraints and prevent survivorship-bias inflation.
    - System is ready to layer forward catalyst logic on top of stable data contracts.

Phase 8 (2026-02-15): Institutional Factor Layer (FR-033, D-38..D-39) ✅
  - Expanded schema in fundamentals pipeline:
    - Added quarterly raw fields (`oibdpq`, `atq`, `ltq`, `xrdq`, `oancfy`, debt/cash/market-cap components, fiscal keys).
    - Added derived institutional factors (`oancf_q`, `oancf_ttm`, `ebitda_ttm`, `ev_ebitda`, `leverage_ratio`, `rd_intensity`).
  - Implemented vectorized decumulation and valuation math in
    `data/fundamentals_compustat_loader.py::compute_institutional_factors`.
  - Validation results (`scripts/validate_factor_layer.py`):
    - PIT violations: 0
    - Decumulation mismatch: 0.0698%
    - Q4 spike rate (>10x): 1.69%
    - Debt fallback zero-rate: 99.15%
    - EV/EBITDA arithmetic bad-rate: 0.00%
  - Snapshot factor coverage:
    - EV/EBITDA 48.45%, Leverage 73.94%, RD Intensity 47.87%, OANCF_TTM 85.35%, EBITDA_TTM 80.90%.

Phase 8 (2026-02-15): Catalyst Radar Integration (FR-034, D-41) ✅
  - Added `data/calendar_updater.py`:
    - Yahoo earnings-date fetch by scope (Top 20/50/100/200/500/3000 or Custom).
    - Uses updater lock and atomic writes to `earnings_calendar.parquet`.
  - `app.load_data()` now merges calendar context into fundamentals payload.
  - `scan_universe()` now emits:
    - `days_to_earnings`, `days_since_earnings`, `earnings_risk`.
    - Optional `fresh_catalysts` mode (last earnings within 7 days).
  - Scanner UI adds:
    - Earnings warning column (`⚠️` when within blackout window).
    - "Hide earnings risk" toggle and blackout-days control.
  - Added `scripts/validate_calendar_layer.py` for data integrity checks.

Phase 9 (2026-02-15): Macro-Regime Layer (FR-035, D-42) 🟡
  - Added `data/macro_loader.py`:
    - Builds canonical `data/processed/macro_features.parquet`.
    - Ingests Yahoo market series + FRED rates.
    - Applies PIT-safe lag policy: fast series T+0, slow series T+1.
    - Computes stress features and `regime_scalar`.
  - Added `scripts/validate_macro_layer.py`:
    - Schema/null checks.
    - Crisis-window sanity checks for March 2020 and 2022.
  - Integration:
    - `app.py` now prefers `macro_features.parquet` with fallback to legacy `macro.parquet`.
    - Data Manager adds macro rebuild control and live regime metrics.
    - `InvestorCockpitStrategy` consumes `regime_scalar` when present, else falls back to legacy VIX scoring.

Phase 9.2 (2026-02-15): Macro Build Optimization Patch (D-43) ✅
  - Performance refactor in `data/macro_loader.py`:
    - Replaced rolling percentile `.apply()` path with vectorized `rolling().rank(pct=True)` (with fallback).
    - Parallelized FRED fetches and bounded requests to build window (`cosd/coed`) while preserving full in-window refetch for revision safety.
  - Added explicit stage timing logs in macro build status.
  - Validation hardening:
    - `scripts/validate_macro_layer.py` now enforces full trading-calendar coverage (no missing/extra dates).
  - Reliability hardening:
    - FRED fetch now uses retry/backoff + timeout and explicit critical-series failure signaling (no silent NaN holes).
    - Trading calendar query applies date filter at SQL level to avoid full-history scans.
    - App fallback macro state is explicitly defensive (`regime_scalar=0.5`, elevated proxy VIX) and strategy macro defense now prioritizes scalar regime when available.
  - Timing results (same machine/session):
    - Baseline: `16.073s`
    - After Step 2 (vectorized percentile): `8.201s`
    - After Step 3 (parallel/date-bounded FRED): `7.927s`

Phase 10 (2026-02-15): Liquidity Layer Foundation + Hardening (FR-040, D-45..D-46) ✅
  - Added `data/liquidity_loader.py`:
    - Builds `data/processed/liquidity_features.parquet` from FRED + Yahoo.
    - Enforces H.4.1 PIT lag for weekly Fed balance-sheet series (Wed -> Fri availability).
    - Computes net-liquidity, repo stress, LRP, dollar stress, and smart-money flow features.
  - Added `scripts/validate_liquidity_layer.py`:
    - Schema/calendar/null checks + Sept-2019 repo spike and 2022 impulse sanity checks.
    - Uses ratio-based 2022 impulse gate to reduce brittleness under normal data revisions.
  - Hardening updates:
    - `data/liquidity_loader.py` now fails fast when critical Yahoo inputs are missing/empty.
    - `data/liquidity_loader.py` now honors `--end-date` in trading-calendar assembly.
    - `data/updater.py` now recovers stale update locks left by crashed jobs.
  - Runtime integration:
    - `app.py` merges `liquidity_features.parquet` into the macro context and exposes FR-040 rebuild controls in Data Manager.
    - `strategies/investor_cockpit.py` consumes FR-040 stress fields as macro-score fallback when `regime_scalar` is unavailable.

Phase 11 (2026-02-15): Regime Governor + Throttle Documentation Freeze (FR-041, D-47..D-48) 🟡
  - Documentation scope (docs-as-code):
    - Added `docs/phase11-brief.md` with objective, thresholds, architecture, and acceptance criteria.
    - `spec.md` now freezes "Current Algorithm v1" before FR-041 contract changes.
    - `spec.md` defines FR-041 RegimeManager interface, BOCPD threshold contract, repo stress units, and 3x3 matrix.
    - `prd.md` now includes FR-041 feature description and delivery criteria.
  - Safety stance:
    - Long-only red safety uses matrix clamps:
      - `RED+NEG=0.00`, `RED+NEUT=0.00`, `RED+POS<=0.20` (D-48).

Phase 12 (2026-02-15): FR-042 Truth-Table Verification Contract (D-49) 🟡
  - Added `docs/phase12-brief.md` with:
    - Objective and methodology for regime verification.
    - Strict acceptance windows:
      - 2008 Q4 RED
      - 2020 Mar RED
      - 2022 H1 AMBER/RED
      - 2017 mostly GREEN (guardrail)
      - Nov 2023 transition to GREEN
    - Performance metrics: drawdown reduction + recovery speed.
  - Calibration patch:
    - Tightened RED trigger context (`credit_freeze` and liquidity shock now volatility-gated).
    - Added FR-042 recovery fallback rule for windows without in-window full recovery.
  - Added `spec.md` FR-042 verification artifacts contract for:
    - `data/processed/regime_history.csv`
    - `data/processed/regime_overlay.png`

Phase 13 (2026-02-15): FR-050 Walk-Forward Contract (D-51..D-52) 🟡
  - Added `docs/phase13-brief.md`:
    - Governor-only deterministic routing (`GREEN=1.0`, `AMBER=0.5`, `RED=0.0`).
    - Strict T+1 execution and turnover cost model.
    - Cash hierarchy and acceptance checks.
  - Added FR-050 sections in `prd.md` and `spec.md`:
    - Artifact schema and metric contract for walk-forward validation.
  - Implemented `backtests/verify_phase13_walkforward.py` + unit tests:
    - `tests/test_verify_phase13_walkforward.py`
    - Artifacts generated:
      - `data/processed/phase13_walkforward.csv`
      - `data/processed/phase13_equity_curve.png`
  - Current FR-050 run snapshot:
    - Sharpe: strategy `0.516` vs buy-and-hold `0.494` (improved)
    - Ulcer: strategy `15.668` vs buy-and-hold `16.255` (improved)
    - MaxDD: strategy `-46.885%` vs buy-and-hold `-55.189%` (improved but not 50% compression)
    - Overall FR-050 strict verdict: `BLOCK`
  - Milestone review gate:
    - Reviewer A: PASS
    - Reviewer B: PASS (after strict-output + optional-PNG resiliency patch)
    - Reviewer C: PASS (fallback coverage telemetry confirmed)

Phase 14 (2026-02-15): FR-060 Feature Store Contract (D-53..D-54) 🟡
  - Added `docs/phase14-brief.md`:
    - Ranking/sizing/execution feature definitions and acceptance checks.
    - Explicit close-only fallback rule for OHLC-dependent features.
  - Added FR-060 sections in `prd.md` and `spec.md`:
    - Feature schema contract and output artifact path.
  - Implemented feature builder + tests:
    - `data/feature_store.py`
    - `tests/test_feature_store.py`
  - Smoke verification:
    - `pytest`: 20 passed
    - `python data/feature_store.py --start-year 2020 --top-n 200`:
      - rows written: 296,834
      - total runtime: 9.522s
  - Hardening patch:
    - Added memory-envelope estimation + safety abort threshold in build path.
    - Added SPY market coverage checks before feature computation.
  - Milestone review gate:
    - Reviewer A: PASS
    - Reviewer B: PASS
    - Reviewer C: PASS

Phase 15 (2026-02-15): FR-070 Alpha Engine Contract (D-55) 🟡
  - Fixed (structural, non-tunable):
    - `SMA200` long eligibility gate remains fixed.
    - Regime budget map remains fixed (`GREEN=1.0`, `AMBER=0.5`, `RED=0.0`).
    - Signal-sign invariants remain fixed (momentum positive, volatility penalty).
  - Adaptive (tunable via WFO only):
    - RSI entry sensitivity via rolling percentile over trailing history.
    - ATR stop multiplier via volatility regime schedule.
    - Selection depth via top-N/percentile controls.
  - Governance rule:
    - Parameter updates require walk-forward protocol.
    - If out-of-sample degradation breaches tolerance, simplify rules instead of adding knobs.

Phase 15 (2026-02-15): FR-070 Integration + Truth Test (D-56..D-57) 🟡
  - Implemented integration in `strategies/investor_cockpit.py`:
    - Alpha path wiring with deterministic selector/sizer/executor loop.
    - Hysteresis hold-buffer enforcement (`Top5` entry, `Top20` hold).
    - Ratchet-only stop persistence per active position.
    - Telemetry emission (`alpha_score`, `entry_trigger`, `stop_loss_level`, `turnover`).
  - Added verifier:
    - `backtests/verify_phase15_alpha_walkforward.py`
    - Compares `SPY` vs `Phase13_Governor` vs `Phase15_Alpha`.
  - UI exposure:
    - Cockpit now renders Top Alpha Candidates and Active Stop-Loss panels when FR-070 is enabled.

Phase 16 (2026-02-15): FR-080 Walk-Forward Optimization & Honing (D-58..D-59) 🟡
  - Documentation scope (FR-080 docs-only milestone):
    - Added `docs/phase16-brief.md` with objective, WFO policy, search-space contract, and acceptance criteria.
    - Added FR-080 section in `prd.md` with objective, governance policy, search space, acceptance, and artifacts.
    - Added FR-080 contract in `spec.md` with artifact schema and hard constraints.
  - FIX vs FINETUNE governance (explicit):
    - FIX (non-tunable): structural FR-070 rules, regime budgets, long-only + hard-cap invariants.
    - FINETUNE (WFO-tunable): `alpha_top_n`, hysteresis ranks, RSI percentile gate, ATR multiplier.
  - WFO-only governance:
    - Parameter selection uses train window metrics only (`2015-01-01..2021-12-31`).
    - OOS/Test window (`2022-01-01..2024-12-31`) is strictly read-only for stability and pass/fail governance.
    - Any detected OOS leakage blocks parameter promotion.

Phase 16.1 (2026-02-15): FR-080 Low-Cost Runtime Optimization Patch (D-60) ✅
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Added optional multi-process candidate evaluation (`ProcessPoolExecutor`).
    - Added worker controls: `--max-workers`, `--chunk-size`, `--disable-parallel`.
    - Added lock controls: `--lock-stale-seconds`, `--lock-wait-seconds`.
    - Added deterministic fallback to sequential execution if parallel execution fails.
    - Added staged artifact bundle commit with rollback on promotion failure.
  - Data reuse stance:
    - Shared datasets are loaded once per run and reused across all candidate evaluations.
  - Safety:
    - Parallel patch preserves existing train-only selection + OOS promotion gate semantics.

Phase 16.2a (2026-02-15): FR-080 Promoted Production Defaults (D-61) ✅
  - Promoted defaults after WFO strict pass:
    - `alpha_top_n=10`
    - `hysteresis_exit_rank=20`
    - `adaptive_rsi_percentile=0.05`
    - `atr_preset=3.0` mapped to ATR multipliers `3.0/4.0/5.0` (`low/mid/high` volatility).
  - Rationale:
    - Locks one strict-pass profile as the FR-080 production default across docs and runtime references.
    - Preserves FR-070 FIX invariants while minimizing operator-side parameter drift.

Phase 16.3 (2026-02-15): FR-080 Hard-Stop Rollback + Diagnostic Pivot (D-62) 🟡
  - Hard-stop rollback:
    - Tuned promotion was blocked after FR-070 tuned verification returned `BLOCK`.
    - Promoted parameter bundle was moved to research-only status (not a runtime default).
    - Runtime default keeps Alpha Engine disabled in UI, with safer RSI fallback `adaptive_rsi_percentile=0.15`.
  - Diagnostic pivot:
    - Next validation focus is starvation analysis on selection/hold behavior under current gates.
    - Phase 16.2 logic expansion is now the required pass path before any re-promotion attempt.

Phase 16.2 (2026-02-15): FR-080 Optimizer Activity Guardrails (D-63) ✅
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Added CLI guard thresholds:
      - `--min-trades-per-year` (default `10.0`)
      - `--min-exposure-time` (default `0.30`)
    - Added deterministic per-candidate activity metrics from generated OOS weights:
      - `exposure_time` (fraction of active OOS exposure days)
      - `trades_per_year` (annualized OOS positive turnover-change events)
    - Promotion gate now requires both:
      - `stability_pass`
      - `activity_guard_pass`
    - Added guard thresholds and activity metrics into summary CSV and best-params payload.
  - Rationale:
    - Stabilizes Phase 16 promotion by blocking low-activity/starved profiles.
    - Preserves strict no-leakage policy and train-only ranking semantics.

Phase 16.2 Step 3 (2026-02-15): FR-080 Dip OR Breakout Entry Logic (D-64) ✅
  - Updated `strategies/alpha_engine.py`:
    - Added PIT-safe breakout feature `prior_50d_high`:
      - Rolling 50-day `adj_close` high per `permno`, shifted by one bar.
    - Entry logic expanded to:
      - `tradable & trend_ok & (dip_entry OR breakout_entry_green)`.
    - Breakout path is GREEN-only:
      - `breakout_entry_green = (regime_state == "GREEN") & (adj_close > prior_50d_high)`.
    - Reason-code precedence:
      - Dip path wins when both are true.
      - Breakout path uses `MOM_BREAKOUT_GREEN_<ADAPT|FIXED>`.
  - Updated tests in `tests/test_alpha_engine.py`:
    - Breakout can trigger when dip path is blocked.
    - Breakout does not trigger in AMBER/RED.
  - Updated docs:
    - `docs/phase16-brief.md` and `spec.md` now document Dip OR Breakout and starvation rationale.

Phase 16.2 Guardrail Hardening (2026-02-15): Regime Normalization + OOS Activity Window (D-65) ✅
  - Updated `strategies/alpha_engine.py`:
    - Added strict regime-state normalization (`strip().upper()`).
    - Unknown states now fail-safe to `RED` budget behavior.
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Activity guard metrics now computed on OOS/Test rows only.
    - Turnover activity includes OOS boundary transitions for accurate trade-rate accounting.
  - Updated tests:
    - `tests/test_alpha_engine.py` validates normalization and unknown-state fail-safe behavior.
    - `tests/test_optimize_phase16_parameters.py` validates OOS-window activity metric computation.

Phase 16.3 (2026-02-15): FR-060 PIT Yearly Universe Expander Remediation (D-66) ✅
  - Updated `data/feature_store.py`:
    - Added configurable `universe_mode` (`yearly_union` default, `global` legacy).
    - Added `yearly_top_n` control with default `100`.
    - Added PIT yearly union selector:
      - Per calendar-year top-N liquidity inside `[start_date, end_date]`.
      - Distinct-permno union across years.
    - Added mode-aware status logs and selected-permno reporting.
    - Added pre-load yearly-union memory envelope guard and abort path.
    - Hardened timestamp handling by normalizing market-series datetimes to tz-naive before window alignment.
    - Preserved existing update lock + atomic write flow.
  - Updated tests:
    - `tests/test_feature_store.py` now validates yearly-union and global helper behavior with synthetic annual-liquidity frames.
  - Updated docs:
    - `docs/phase16-brief.md` and `spec.md` now include the remediation contract and default settings.

Phase 16.2 (2026-02-15): FR-080 Promotion Policy Mismatch Fix "Greed patch" (D-67) ✅
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Selection now uses promotable-first ranking:
      - promotable rows are `stability_pass AND activity_guard_pass` with valid
        train metrics.
    - If promotable pool is non-empty, ranking is train-only and deterministic:
      - `objective_score` (desc)
      - `train_cagr` (desc)
      - `train_robust_score` (desc)
      - `train_ulcer` (asc)
      - parameter tie-breakers:
        `alpha_top_n`, `hysteresis_exit_rank`, `adaptive_rsi_percentile`,
        `atr_preset` (ascending).
    - If promotable pool is empty, train-only ranking is retained for
      diagnostics and promotion is blocked.
    - Added explicit `selection_pool` states:
      - `promotable_train_ranked`
      - `train_only_rejected_guardrails`
      - `no_valid_candidates`
    - OOS fields are excluded from ranking and tie-break decisions.
  - Updated tests:
    - `tests/test_optimize_phase16_parameters.py` now validates promotable-first
      behavior and non-promotable skip despite higher train objective.
  - Updated docs:
    - `docs/phase16-brief.md` and `spec.md` now describe the corrected
      promotion policy and ranking order.

Phase 17.0 (2026-02-15): FR-090 Infrastructure Hardening Baseline + Conflict Gate (D-68) ✅
  - Added `docs/phase17-brief.md`:
    - Defines the Phase 17 architecture direction: "Qlib Storage, RD-Agent Evolution."
    - Establishes reader/writer conflict policy for optimizer vs data-layer work.
    - Defines concrete KPI capture methods and target thresholds for Milestones 1-4.
    - Locks approved execution order:
      1) FR-080 functional baseline run,
      2) docs-only Milestone 0 in parallel,
      3) data-layer refactors only after optimizer completion.
  - Runtime safety decision:
    - Active Phase 16.4 optimizer run is treated as a protected reader workload.
    - Milestone 1 write-path refactors remain blocked until:
      - no optimizer process is active,
      - `data/processed/phase16_optimizer.lock` is absent,
      - FR-080 artifact bundle is fully committed.

Phase 17.1 (2026-02-16): FR-090 Data Layer Hardening Slice A (D-69..D-71) ✅
  - Added `utils/parallel.py`:
    - Unified parallel wrapper with ordered result semantics.
    - Backends: threading + multiprocessing.
    - Optional joblib acceleration (`threading`/`loky`) with safe fallback.
  - Updated `data/updater.py`:
    - Added chunked parallel Yahoo download orchestrator:
      - `parallel_batch_download_yahoo()`
      - chunk worker `_download_chunk()`
    - Preserved existing update lock + atomic parquet publish path.
    - Added deterministic ticker normalization and `(ticker,date)` dedupe on merged Yahoo payload.
  - Updated `data/feature_store.py`:
    - Added incremental build mode (default enabled when window semantics allow):
      - Detect existing feature max date.
      - Recompute from warmup replay window.
      - Append only new rows.
    - Added atomic upsert merge helper for `features.parquet`:
      - Source precedence: new rows override old on `(date, permno)`.
    - Added CLI controls:
      - `--full-rebuild`
      - `--incremental-warmup-bdays`
    - Added parallelized stack stage via `utils.parallel.parallel_execute`.
  - Updated `scripts/validate_data_layer.py`:
    - Added feature-store integrity check:
      - non-empty rows,
      - null-key guard,
      - duplicate-key guard,
      - freshness gap vs latest prices/patch.
  - Added tests:
    - `tests/test_parallel_utils.py`
    - `tests/test_updater_parallel.py`
    - Extended `tests/test_feature_store.py` for incremental/upsert helpers.
  - Verification:
    - `pytest`: PASS (all tests).
    - `scripts/validate_data_layer.py`: FAIL due pre-existing snapshot zombie row (not introduced by this slice).

Phase 16.5 (2026-02-16): FR-080 Alpha Discovery Tournament Expansion (D-72) ✅
  - Updated `strategies/alpha_engine.py`:
    - Added `entry_logic` contract in `AlphaEngineConfig` with allowed values:
      - `dip`
      - `breakout`
      - `combined`
    - Added strict validation (`ValueError` on unsupported logic).
    - Entry and reason-code routing now respect selected logic mode.
  - Updated `strategies/investor_cockpit.py`:
    - Added `alpha_entry_logic` passthrough into internal `AlphaEngineConfig`.
    - Exposed selected entry logic in strategy details payload.
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Added `--entry-logic-grid`.
    - Expanded default tournament grid:
      - `entry_logic=dip,breakout,combined`
      - `alpha_top_n=10,20`
      - `atr_preset=2.0,3.0,4.0,5.0`
    - Added `entry_logic` into summary fields and deterministic tie-break ranking.
    - Preserved FR-080 governance:
      - train-only ranking
      - OOS only for stability/activity promotion gates.
  - Updated tests:
    - `tests/test_alpha_engine.py`: entry-logic mode routing + validation coverage.
    - `tests/test_optimize_phase16_parameters.py`: grid validation for entry-logic dimension.
  - Verification:
    - `pytest tests/test_alpha_engine.py tests/test_optimize_phase16_parameters.py -q`: PASS.
    - `pytest -q`: PASS.

Phase 16.5b (2026-02-16): FR-080 Real-Time Tournament Telemetry (D-73) ✅
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Added periodic progress heartbeat controls:
      - `--progress-interval-seconds`
      - `--progress-path`
    - Added interim leaderboard controls:
      - `--live-results-path`
      - `--live-results-every`
      - `--disable-live-results`
    - Parallel evaluator now consumes futures via `as_completed` for immediate completion visibility.
    - Emits periodic console status with elapsed/ETA/promotable count/best-so-far.
    - Publishes atomic heartbeat JSON and interim results CSV during execution.
  - Updated docs:
    - `docs/phase16-brief.md` and `spec.md` now include telemetry contract.

Phase 16.7 (2026-02-16): Fundamental Data-Layer Expansion (D-74) ✅
  - Updated `data/fundamentals_updater.py`:
    - Extended canonical schema and snapshot fields with:
      - `net_income_q`, `equity_q`, `eps_basic_q`, `eps_diluted_q`,
        `eps_q`, `eps_ttm`, `eps_growth_yoy`, `roe_q`.
    - Added net-income mapping preference for common-share earnings labels.
    - Added equity fallback:
      - `equity_q = Total Assets - Total Liabilities` when stockholders equity is missing.
    - Added EPS policy:
      - store both basic/diluted when available,
      - derive EPS from net income and shares when needed,
      - prioritize diluted for selector-facing `eps_q`.
    - Hardened runtime safety:
      - acquire shared update lock before mutating shared artifacts,
      - atomic writes for `fundamentals.parquet`, `fundamentals_snapshot.parquet`, and `tickers.parquet`.
    - Added compatibility guard to backfill missing schema columns before final column selection.
  - Updated `data/fundamentals_compustat_loader.py`:
    - Added resilient optional-column extraction (`niq`, `ceqq`, `epspxq`, `epsfxq`, `atq`, `ltq`).
    - Applied same equity fallback and diluted-priority EPS policy in institutional factor computation.
    - Added graceful lock-contention handling (`TimeoutError` -> status/log return, no uncaught crash).
  - Updated `data/fundamentals.py`:
    - Extended required schema validation, numeric casting, snapshot load path, and runtime context matrices for:
      - `roe_q`
      - `eps_growth_yoy`
    - Extended latest snapshot payload used by scanner/runtime selection.
  - Updated `scripts/validate_factor_layer.py`:
    - Added new fundamentals and snapshot required columns to integrity checks.
    - Core valuation coverage gate now evaluates investable rows (`quality_pass==1`) while reporting full-snapshot coverage for observability.
  - Updated docs:
    - `docs/phase16-brief.md` adds Section 12 for Phase 16.7 scope and data policy.

Phase 17.2 (2026-02-16): Capital-Cycle + Bitemporal Foundation (D-75) ✅
  - Updated docs contract:
    - `docs/phase16-brief.md` adds Phase 16.7b Capital-Cycle Pivot section:
      - score contract (`0.4/0.4/0.2`),
      - conditional discipline logic,
      - bitemporal acceptance criteria.
  - Updated data schema and ingestion:
    - `data/fundamentals_updater.py` adds explicit raw fields:
      - `capex_q`, `depreciation_q`, `inventory_q`, `total_assets_q`, `operating_income_q`
      - plus capital-cycle derivatives:
        `delta_capex_sales`, `operating_margin_delta_q`, `delta_revenue_inventory`, `asset_growth_yoy`.
    - Added bitemporal columns:
      - `filing_date`
      - `published_at`
    - `data/updater.py` now exposes shared quarterly-statement fetch helper for the fundamentals layer.
  - Updated Compustat merge path:
    - `data/fundamentals_compustat_loader.py` now maps the same explicit raw fields when available.
    - Merge dedupe key now preserves published-time versions:
      - `(permno, release_date, published_at)` with source precedence.
  - Updated bitemporal query layer:
    - `data/fundamentals.py` now enforces as-of filtering:
      - `published_at <= as_of_date`.
    - Legacy row fallback for missing `published_at`:
      - `filing_date`,
      - else `fiscal_period_end + 90 days`.
    - Snapshot context now requests as-of-safe fundamentals snapshot.
  - Verification:
    - `py_compile`: PASS (`data/updater.py`, `data/fundamentals_updater.py`, `data/fundamentals.py`, `data/fundamentals_compustat_loader.py`).
    - As-of sanity check: PASS (`published_at`-bounded loads + snapshot path).
    - `pytest -q`: PASS.

Phase 17.2b (2026-02-16): Declarative FeatureSpec Engine + Hash Cache (D-76) ✅
  - Added `data/feature_specs.py`:
    - Introduced `FeatureSpec` dataclass contract:
      - `name`, `func`, `category`, `inputs`, `params`, `smooth_factor`.
    - Added default registry with technical + capital-cycle specs:
      - `z_resid_mom`, `z_flow_proxy`, `z_vol_penalty`, `composite_score`
      - `z_moat`, `z_discipline_cond`, `z_demand`, `capital_cycle_score`.
  - Refactored `data/feature_store.py`:
    - Added declarative spec executor loop with dependency checks for fundamental inputs.
    - Replaced hardcoded score assembly with registry outputs.
    - Added capital-cycle feature outputs to artifact schema:
      - `z_moat`, `z_discipline_cond`, `z_demand`, `capital_cycle_score`.
    - Added deterministic cache key + artifact cache path:
      - `data/processed/features_<cache_key>.parquet`.
    - Cache key includes:
      - spec signature hash,
      - config + universe parameters,
      - permno hash,
      - input artifact fingerprints.
    - On cache hit, build skips feature compute and publishes from cached artifact.
  - Updated tests:
    - `tests/test_feature_specs.py` for conditional discipline behavior.
    - `tests/test_feature_store.py` schema assertions now include capital-cycle outputs.
    - `tests/test_feature_store.py` validates deterministic feature-spec hash.
  - Verification:
    - `py_compile`: PASS (`data/feature_specs.py`, `data/feature_store.py`).
    - `pytest -q`: PASS.
    - Runtime smoke:
      - first run writes cache artifact,
      - second identical run logs cache hit and skips compute stage.

Phase 17.3 (2026-02-16): Daily Vintage Fundamentals Panel + Bitemporal Audit (D-77) ✅
  - Added `data/fundamentals_panel.py`:
    - New dense panel artifact builder:
      - `data/processed/daily_fundamentals_panel.parquet`.
    - Interval-based PIT expansion:
      - each sparse row is active on `[published_at, next_published_at)`.
    - Atomic publish path and manifest cache:
      - `daily_fundamentals_panel.manifest.json` stores source signature + panel metadata.
    - Runtime helper:
      - `join_prices_with_daily_fundamentals()` for fast `(date, permno|ticker)` joins.
  - Feature-engine hash contract hardening:
    - `data/feature_specs.py` now exports:
      - `compute_spec_hash(spec)`
      - `compute_registry_hash(specs)`.
    - `data/feature_store.py` now consumes the shared registry hash helper.
  - Added tests:
    - `tests/test_bitemporal_integrity.py`:
      - fake restatement scenario with strict as-of assertions,
      - pre-restatement panel check (must show old value),
      - post-restatement panel check (must show new value),
      - manifest cache-hit assertion.
    - `tests/test_feature_specs.py`:
      - deterministic hash API assertions.
  - Validation target:
    - Fail build if pre-restatement as-of query resolves to restated value (look-ahead breach).

Phase 16.9 (2026-02-16): CSCO 2000 Event Study Smoke Test (D-78) ✅
  - Added event-study runner:
    - `backtests/event_study_csco.py`
  - Scope:
    - Builds CSCO (1999-2001) daily study frame from `prices.parquet`.
    - Attempts panel path first; auto-falls back to local Compustat CSV when
      panel fields are insufficient in early history.
    - Computes and stores:
      - `z_moat`
      - `z_discipline_cond` (inventory-commitment stress + operating-leverage relief)
      - `z_demand`
      - `capital_cycle_score`
  - Output artifacts:
    - `data/processed/csco_event_study_1999_2001.csv`
    - `data/processed/csco_event_study_1999_2001.html`
  - Result:
    - Source: `compustat_fallback`
    - `Q2 2000 score = 0.4344`
    - `Q3 2000 score = 0.3966`
    - `Q4 2000 score = 0.0328`
    - `Q4 z_moat = 1.0828`
    - Verdict: `PASS`

Phase 16.10 (2026-02-16): MU 2016 Micron Paradox Stress Test (D-79) 🟡
  - Extended event-study harness:
    - `backtests/event_study_csco.py` now supports:
      - dynamic ticker/year artifacts,
      - `--eval-mode rally_positive`,
      - PIT-safe panel projection via publication-time snapshots.
    - Added operational hardening:
      - atomic CSV/HTML writes,
      - resilient output-directory creation,
      - DuckDB-filtered Compustat fallback path for non-zipped CSV.
  - MU run:
    - Command:
      - `python backtests/event_study_csco.py --ticker MU --start 2014-01-01 --end 2018-12-31 --eval-mode rally_positive --rally-start 2016-04-01 --rally-end 2017-03-31`
    - Artifacts:
      - `data/processed/mu_event_study_2014_2018.csv`
      - `data/processed/mu_event_study_2014_2018.html`
    - Outcome:
      - source=`compustat_fallback`
      - rally score mean=`-1.1809`
      - rally score min=`-2.4056`
      - positive-share=`24.51%`
      - verdict=`FAIL` (score does not stay positive through 2016 rally)
  - Decision impact:
    - Cyclical exception is now a required next patch to avoid false-sell behavior in semiconductor supercycle transitions.

Phase 16.11 (2026-02-16): Turnover Gate Patch + Twin Verification (D-80) 🟡
  - Implemented turnover gate:
    - `delta(revenue_inventory_q) > 0.05` waives discipline penalty.
  - Updated shared factor logic:
    - `data/feature_specs.py`:
      - `spec_discipline_conditional` now accepts turnover input and threshold parameter.
      - default spec input for `z_discipline_cond` includes `delta_revenue_inventory`.
  - Updated event-study scorer:
    - `backtests/event_study_csco.py` applies the same turnover-gate logic in:
      - panel path
      - Compustat fallback path
    - Added CLI parameter `--turnover-gate-threshold`.
  - Test updates:
    - `tests/test_feature_specs.py` now covers turnover-gate open/closed behavior.
  - Twin verification:
    - Cisco 2000:
      - verdict `PASS`
      - `Q2=0.4344`, `Q3=0.3966`, `Q4=0.0328`
    - Micron 2016 rally-positive:
      - verdict `FAIL`
      - mean `-1.2894`, min `-2.4056`, max `-0.0603`, positive-share `0.0000`
  - Decision impact:
    - Turnover-only override is insufficient; next patch needs additional cyclical exception features.

Phase 16.12 (2026-02-16): Inventory Quality Gate (D-81) 🟡
  - Implemented leading-signal inventory quality layer:
    - Data schema additions in fundamentals artifacts:
      - `cogs_q`, `receivables_q`, `deferred_revenue_q`, `delta_deferred_revenue_q`
      - `book_to_bill_proxy_q`, `dso_q`, `delta_dso_q`, `gm_accel_q`
    - Updated modules:
      - `data/fundamentals_updater.py`
      - `data/fundamentals_compustat_loader.py`
      - `data/fundamentals.py`
      - `data/fundamentals_panel.py`
  - Updated discipline gate logic:
    - `data/feature_specs.py::spec_discipline_conditional`
      - weighted soft vote:
        - book-to-bill demand vote weight `2`
        - GM acceleration vote weight `1`
        - DSO trend vote weight `1`
      - thresholds:
        - `book_to_bill_proxy_q > 1.0`
        - `gm_accel_q >= 0`
        - `delta_dso_q <= 0`
      - fallback policy:
        - with book-to-bill present: gate opens at `>= 2` weighted votes
        - without book-to-bill: requires GM + DSO path (`>= 2`)
      - missing-signal resilience:
        - `gm_accel_q` falls back to `operating_margin_delta_q`
        - `delta_dso_q` falls back to `-delta_revenue_inventory`
  - Event-study scorer parity:
    - `backtests/event_study_csco.py` now applies Inventory Quality Gate in:
      - panel path
      - Compustat fallback path
    - Added CLI controls for gate thresholds and vote weights.
  - Validation:
    - `pytest -q`: PASS
    - CSCO 2000 (`csco_drop`): PASS (`Q2=0.4344`, `Q3=0.3966`, `Q4=0.0328`)
    - MU 2016 (`rally_positive`): FAIL (strict all-days-positive condition still not met)
  - Decision impact:
    - Infrastructure and gate logic are upgraded end-to-end.
    - Twin verification remains partially blocked by MU strict-positivity; next patch needs moat/demand normalization refinement for cyclical trough regimes without regressing CSCO de-rating.

Phase 16.13 (2026-02-17): Proxy Gate Pivot (D-82) 🟡
  - Decision:
    - Replace discrete inventory-quality soft-vote gate with a continuous
      cross-sectional proxy gate driven by quarterly acceleration/bloat terms.
    - Keep no-new-fetch policy; compute all inputs from existing quarterly fields.
  - New derived fields:
    - `sales_growth_q = pct_change(total_revenue_q, 1)`
    - `sales_accel_q = delta(sales_growth_q)`
    - `op_margin_accel_q = delta(operating_margin_delta_q)`
    - `bloat_q = delta(ln(total_assets_q - inventory_q)) - delta(ln(total_revenue_q))`
    - `net_investment_q = (abs(capex_q) - depreciation_q) / lag(total_assets_q, 1)`
  - Gate score:
    - `z_inventory_quality_proxy = z(sales_accel_q) + z(op_margin_accel_q) - z(bloat_q) - 0.5*z(net_investment_q)`
    - Discipline waiver rule: if `z_inventory_quality_proxy > 0`, set discipline penalty to zero.
  - Rationale:
    - Avoid binary gate brittleness and better separate strategic inventory build
      from inefficient asset bloat in cyclical recoveries.
  - Safety:
    - PIT semantics unchanged (`published_at <= as_of_date`).
    - Backward compatibility preserved by nullable derived columns.

Governance Update (2026-02-18): Planning/SAW Contract Upgrade (D-83) ✅
  - Added mandatory plan response contract and SAW report format in `AGENTS.md`.
  - Added self-learning source of truth: `docs/lessonss.md`.
  - Added skill hooks for SAW and research-backed planning.

Governance Update (2026-02-18): Runtime Fail-Safe Continuity (D-84) ✅
  - Defined fail-safe continuity policy for critical upstream data failures:
    keep last-successful artifact, skip unsafe publish, emit stale-data alert, and require resume note.

Governance Update (2026-02-19): Interactive Review Protocol (D-85) ✅
  - Added structured review mode gate (`BIG CHANGE`/`SMALL CHANGE`) and per-issue optioned responses.
  - Added explicit confirmation checkpoint before implementation during review-mode workflows.

Governance Update (2026-02-19): PM Hierarchy + Stage Loop (D-86) ✅
  - Standardized project-based hierarchy (`L1` pillar, `L2` streams, `L3` stages).
  - Added one-stage expansion/anti-sprawl loop and stage-specific snapshot contract.
  - Added trigger-based optional skills (`se-executor`, `architect-review`) with `>=2`-round escalation by approval.

Governance Update (2026-02-19): SAW In-Scope Blocking Rule (D-87) ✅
  - Updated SAW reconciliation semantics to block on in-scope Critical/High findings.
  - Added inherited out-of-scope High finding carry-forward rule (`Open Risks` + owner + target milestone).

Phase 17.1 (2026-02-19): Cross-Sectional Backtester Transition (D-88) 🟡
  - Decision:
    - Pause event-study-first validation path for this milestone.
    - Stand up cross-sectional double-sort evaluator with econometric inference as primary validation harness.
  - Data foundation:
    - Added `statsmodels==0.14.5` to project dependencies.
    - Hardened `data/feature_store.py` persistence contract:
      - enforced required output columns in `features.parquet`:
        - `z_inventory_quality_proxy`
        - `z_discipline_cond`
      - added incremental schema-drift guard:
        - stale destination schema forces full atomic rewrite instead of unsafe upsert.
      - added cache-schema guard:
        - stale cache artifact without required columns is recomputed.
      - added proxy-input fallback derivation inside feature pipeline:
        - `sales_accel_q <- delta_revenue_inventory`
        - `op_margin_accel_q <- diff(operating_margin_delta_q)`
        - `bloat_q <- diff(1/revenue_inventory_q)`
        - `net_investment_q <- asset_growth_yoy`
    - Rebuilt feature artifact:
      - `python data/feature_store.py --full-rebuild`
      - wrote `2,555,730` rows to `data/processed/features.parquet`.
  - Evaluator delivery:
    - Added `scripts/evaluate_cross_section.py`:
      - DuckDB joins over `prices`, `daily_fundamentals_panel`, `features`, `sector_map`.
      - strict equity filter: `quote_type='EQUITY'` and `industry!='Unknown'`.
      - deterministic sector classification:
        - rank `sector_map` rows by `updated_at` and keep row-1 per `permno`/`ticker` (no `ANY_VALUE` nondeterminism).
      - date-window pushdown:
        - applies `--start-date/--end-date` filters to `prices`, `panel`, and `features` CTEs.
      - double-sort:
        1) top 30% asset growth by `date, industry`
        2) proxy deciles within high-growth buckets
        3) spread = `Decile10 - Decile1`.
      - inference:
        - mean/vol/sharpe of spread
        - Newey-West t-stat with auto lag:
          - `floor(4 * (T / 100)^(2/9))`
        - Fama-MacBeth date-wise OLS + HAC/Newey-West beta significance.
    - Added tests:
      - `tests/test_evaluate_cross_section.py`
  - Produced artifacts:
    - `data/processed/phase17_1_cross_section_spread_timeseries.csv`
    - `data/processed/phase17_1_cross_section_summary.json`
    - `data/processed/phase17_1_cross_section_fama_macbeth_betas.csv`
    - `data/processed/phase17_1_cross_section_fama_macbeth_summary.csv`
  - Result snapshot:
    - spread mean > 0 (`0.002089`) but Newey-West t-stat below gate (`0.766 < 3.0`)
    - FM interaction beta not positive/significant on this sample (`p=0.406005`)
  - Decision impact:
    - Infrastructure for cross-sectional validation is now in place and reproducible.
    - Phase 17.1 remains open for signal iteration because acceptance gates are not yet met.

Phase 17.2A (2026-02-19): Feature Store Partitioned Upsert Unblocker (D-89) ✅
  - Decision:
    - Replace monolithic `features.parquet` writes with partitioned storage and partition-scoped upserts.
  - Implementation:
    - `data/feature_store.py` now treats `data/processed/features.parquet` as a dataset root:
      - partition scheme: `year=YYYY/month=MM`.
    - Added one-time migration:
      - legacy single file is auto-converted to partitioned dataset on first touch.
    - Added partition-aware upsert path:
      - only touched `(year, month)` partitions are reloaded, merged on (`date`,`permno`), and atomically replaced.
    - Reader/update compatibility:
      - bounds, row counts, schema reads, and permno reads now scan both legacy and partitioned layouts.
  - Validation:
    - `tests/test_feature_store.py` expanded with migration + touched-partition rewrite contract.
    - `python data/feature_store.py`: PASS.
    - Post-migration parity check:
      - rows=`2,555,730`, dates=`6,570`, permnos=`389`.
  - Decision impact:
    - Phase 17 research loops are no longer blocked by full-table feature rewrites on each incremental run.

Phase 17.2B (2026-02-19): CSCV + DSR Parameter Sweep Engine (D-90) 🟡
  - Decision:
    - Sweep proxy weight variants with coarse-to-fine search, then score with CSCV/PBO and DSR-adjusted evidence.
  - Implementation:
    - Added `utils/statistics.py`:
      - CSCV split generation (`C(S, S/2)`), block mapping, and PBO computation.
      - correlation-adjusted effective trials:
        - `N_eff ~= N * (1 - rho_avg) + 1` (bounded to `[1, N]`).
      - DSR helpers:
        - expected max Sharpe benchmark and non-normality-adjusted PSR/DSR.
    - Added `scripts/parameter_sweep.py`:
      - coarse-to-fine grid generation with local runtime caps.
      - return-stream export per variant.
      - DSR merge and CSCV summary export.
  - Tests and verification:
    - Added:
      - `tests/test_statistics.py`
      - `tests/test_parameter_sweep.py`
    - Full suite:
      - `.venv\Scripts\python -m pytest -q`: PASS.
    - Smoke sweep:
      - `.venv\Scripts\python scripts/parameter_sweep.py --start-date 2023-01-01 --end-date 2024-12-31 --max-coarse-combos 24 --max-fine-combos 24 --cscv-blocks 6 --output-prefix phase17_2_parameter_sweep_smoke`: PASS.
    - Full sweep:
      - `.venv\Scripts\python scripts/parameter_sweep.py --cscv-blocks 6 --output-prefix phase17_2_parameter_sweep`: PASS.
      - key outputs:
        - variants=`168`
        - avg correlation=`0.4619`
        - effective trials=`91.39`
        - PBO=`0.9412`
        - best variant=`coarse_0006`
        - best metrics: `annualized_sharpe=1.9820`, `t_stat_nw=1.4943`, `dsr=0.8847`.
  - Decision impact:
    - Search/inference infrastructure is production-ready for ongoing proxy-gate research.
    - Current run remains below strict `t_stat > 3.0` acceptance, so signal promotion stays blocked.

Phase 17.3 Prep (2026-02-19): Sweep Resume + DSR Anchor Hardening (D-91) ✅
  - Decision:
    - Stabilize sweep execution for longer research rounds and enforce robust tie-breaking for fine-grid anchoring.
  - Implementation:
    - `scripts/parameter_sweep.py`:
      - deterministic variant identity from sorted parameter tuple hash:
        - `variant_id = md5(json(sorted(params)))`.
        - hash input is limited to the five sweep parameter keys (metadata keys ignored).
      - coarse winner for fine grid now uses:
        - `DSR -> t_stat_nw -> period_mean`.
        - tie rows resolve deterministically via `variant_id` stable sort.
      - checkpoint/resume subsystem:
        - hidden checkpoint artifacts:
          - `.checkpoint_<prefix>.json`
          - `.checkpoint_<prefix>_results.csv`
          - `.checkpoint_<prefix>_streams.csv`
        - auto cadence when `--checkpoint-every=0`:
          - `<=80 -> 10`, `<=250 -> 20`, `>250 -> 50`.
        - resume is default; disable with `--no-resume`.
        - cleanup after success unless `--keep-checkpoint`.
      - atomic checkpoint replace retry on transient Windows lock conflicts.
  - Verification:
    - tests:
      - `tests/test_parameter_sweep.py` updated for:
        - hash-ID stability
        - DSR-first ranking
        - checkpoint cadence.
    - resume smoke:
      - first run builds checkpoint + outputs.
      - rerun loads checkpoint and logs:
        - `[coarse] resume hit ...`
        - `[fine] resume hit ...`
      - both runs PASS.
  - Decision impact:
    - Sweep runtime is now restartable and deterministic under grid evolution.
    - Fine-grid compute is aligned with robust (deflated) evidence rather than raw luck.

Phase 17.3 Prep (2026-02-19): Partition Read Batching in Upsert Path (D-92) ✅
  - Decision:
    - Remove remaining per-partition read overhead inside partitioned feature upserts.
  - Implementation:
    - `data/feature_store.py`:
      - added batched partition loader (`_load_feature_partition_slices`) that:
        - registers touched `(year, month)` keys once,
        - reads all relevant partitions in one DuckDB query,
        - returns partition-keyed frames for downstream merge/write.
      - `_atomic_upsert_features` now:
        - opens one DuckDB connection for the read batch,
        - closes connection once,
        - proceeds with partition-scoped atomic rewrite loop.
  - Verification:
    - `tests/test_feature_store.py` adds:
      - `test_atomic_upsert_features_batches_partition_reads_with_single_connection`.
    - full test suite:
      - `.venv\\Scripts\\python -m pytest -q`: PASS.
  - Decision impact:
    - Reduced connection churn and repeated scan overhead for multi-partition incremental writes.

Phase 17 Closeout (2026-02-19): Windows-Safe Sweep Lock Liveness + Corrupt-Lock Recovery (D-93) ✅
  - Decision:
    - Replace Windows `os.kill(pid, 0)` liveness probe in sweep lock path and harden stale-lock recovery when lock metadata is unreadable.
  - Root cause:
    - Windows lock test path could terminate the active runner process when probing PID liveness with `os.kill(pid, 0)`, producing hard `aborted` runs without traceback.
  - Implementation:
    - `scripts/parameter_sweep.py`:
      - `_pid_is_running` now uses WinAPI process query (`OpenProcess` + `GetExitCodeProcess`) on Windows.
      - non-Windows behavior remains `os.kill(pid, 0)` probe.
      - stale-lock TTL recovery now falls back to lock file mtime when JSON payload is missing/corrupt.
      - bounded stale-lock recovery and explicit failure path retained.
    - `tests/test_parameter_sweep.py`:
      - added `test_sweep_lock_ttl_fallback_recovers_corrupt_lock_by_file_mtime`.
  - Verification:
    - `.venv\\Scripts\\python -m pytest tests\\test_parameter_sweep.py -k sweep_lock -vv -s`: PASS.
    - `.venv\\Scripts\\python -m pytest tests\\test_parameter_sweep.py -vv -s`: PASS.
    - `.venv\\Scripts\\python -m pytest -q`: PASS.
  - Decision impact:
    - Eliminates Windows process-termination crash path in lock checks.
    - Improves operational recovery from stale/corrupt lock files without manual intervention.

Phase 18 Day 1 (2026-02-19): Baseline Benchmark Report with Engine-Parity Frictions (D-94) ✅
  - Decision:
    - Add a dedicated baseline report script for SPY control strategies that enforces the same execution constraints as alpha backtests.
  - Implementation:
    - Added `scripts/baseline_report.py`.
    - Baselines implemented:
      - `buy_hold_spy` (target SPY weight `1.0`)
      - `static_50_50` (target SPY weight `0.5`)
      - `trend_sma200` (`spy_close > sma200 => 1.0`, else `--trend-risk-off-weight`, default `0.5`).
    - Execution/cost path:
      - uses `engine.run_simulation` as SSOT for shift(1) and turnover/cost.
      - models the tradable sleeve as SPY allocation with excess return leg `(spy_ret - cash_ret)` and then adds `cash_ret` back to avoid charging synthetic cash-leg turnover.
    - Reused FR-050 helpers from `backtests/verify_phase13_walkforward.py`:
      - `build_cash_return`, `compute_cagr`, `compute_sharpe`, `compute_max_drawdown`, `compute_ulcer_index`.
    - Cash hierarchy:
      - `BIL -> EFFR/252 -> flat 2%/252`.
    - Exports:
      - `data/processed/phase18_day1_baseline_equity.csv`
      - `data/processed/phase18_day1_baseline_metrics.csv`
      - optional PNG overlay (graceful skip if matplotlib unavailable).
    - Added tests:
      - `tests/test_baseline_report.py` for lag/cost/trend/metrics contract.
  - Verification:
    - `.venv\Scripts\python -m pytest tests\test_baseline_report.py -q`: PASS.
    - `.venv\Scripts\python scripts\baseline_report.py`: PASS.
    - Sample outputs (2015-01-02 -> 2024-12-31, rows=2,523):
      - buy_hold_spy: CAGR `12.982%`, Sharpe `0.782`, MaxDD `-33.717%`
      - static_50_50: CAGR `11.104%`, Sharpe `0.653`, MaxDD `-17.907%`
      - trend_sma200: CAGR `11.544%`, Sharpe `0.892`, MaxDD `-25.591%`
  - Decision impact:
    - Phase 18 now has reproducible, friction-aware benchmark controls for Day 1 comparison against later alpha candidates.

Phase 18 Day 1 (2026-02-19): Baseline Protocol Alignment + Metric SSOT Extraction (D-95) ✅
  - Decision:
    - Promote baseline/risk metrics into `utils/metrics.py` as single source of truth and align Day 1 baseline script interface/output contract to institutional operator spec.
  - Implementation:
    - Added `utils/metrics.py` with:
      - `compute_cagr`
      - `compute_sharpe(returns, rf_returns=None, periods_per_year=252)`
      - `compute_max_drawdown`
      - `compute_ulcer_index`
      - `compute_turnover`
    - Refactored `backtests/verify_phase13_walkforward.py` metric helpers to delegate to SSOT while preserving existing function names.
    - Updated `scripts/baseline_report.py`:
      - CLI contract now uses `--output-csv` and `--output-plot` defaults:
        - `data/processed/phase18_day1_baselines.csv`
        - `data/processed/phase18_day1_equity_curves.png`
      - institutional ASCII metrics table in console output
      - log-scale equity overlay plot
      - Pillow fallback path for PNG generation when matplotlib is unavailable
      - CSV schema contract:
        - `baseline,cagr,sharpe,max_dd,ulcer,turnover_annual,turnover_total,start_date,end_date,n_days`
    - Added tests:
      - `tests/test_metrics.py`
      - expanded `tests/test_baseline_report.py`
      - expanded `tests/test_verify_phase13_walkforward.py`
  - Verification:
    - `.venv\Scripts\python -m pytest tests\test_metrics.py tests\test_verify_phase13_walkforward.py tests\test_baseline_report.py tests\test_verify_phase15_alpha_walkforward.py -q`: PASS (`16 passed`).
    - `.venv\Scripts\python scripts\baseline_report.py`: PASS.
    - Artifacts written:
      - `data/processed/phase18_day1_baselines.csv`
      - `data/processed/phase18_day1_equity_curves.png`
  - Decision impact:
    - Day 1 baseline benchmarking now matches operator execution protocol and metric governance with reusable SSOT metric primitives for downstream phases.

Phase 18 Day 2 (2026-02-19): TRI Migration + Schema Guardrail + Macro TRI Extension (D-96) ✅
  - Decision:
    - Replace split-trap signal source with forward-built TRI artifacts while preserving D-02 execution semantics (`total_ret` unchanged for PnL).
  - Root cause:
    - Legacy `adj_close` signal inputs can be retroactively rewritten by corporate actions, creating false technical signals around split windows.
  - Implementation:
    - Added `data/build_tri.py`:
      - builds `data/processed/prices_tri.parquet` from base+patch price data with patch-priority dedupe on `(date, permno)`.
      - computes `tri` from cumulative total-return factors.
      - renames legacy signal column to `legacy_adj_close` (explicit deprecation barrier).
      - emits Day 2 validation artifacts:
        - `data/processed/phase18_day2_tri_validation.csv`
        - `data/processed/phase18_day2_split_events.png`
    - Added `data/build_macro_tri.py`:
      - builds `data/processed/macro_features_tri.parquet`.
      - adds `spy_tri`, `vix_tri`, `mtum_tri`, `dxy_tri`.
      - recomputes TRI-derived macro features (`vix_proxy`, `mtum_spy_corr_60d`, `dxy_spx_corr_20d`).
    - TRI-first compatibility integration:
      - `data/feature_store.py`: prefers `prices_tri.parquet` source, persists `tri`, keeps backward-compatible `adj_close`.
      - `strategies/investor_cockpit.py`: supports/propagates `tri` in alpha feature history and prefers it when available in stop checks.
      - `app.py`: prefers `prices_tri.parquet` and `macro_features_tri.parquet` when present.
    - Added tests:
      - `tests/test_build_tri.py` (schema migration, patch priority, split continuity, dividend capture, macro SPY consistency).
  - Verification:
    - `.venv\Scripts\python data/build_tri.py --start-date 2015-01-01 --end-date 2024-12-31 --output data/processed/prices_tri.parquet --validation-csv data/processed/phase18_day2_tri_validation.csv --split-plot data/processed/phase18_day2_split_events.png`: PASS.
    - `.venv\Scripts\python data/build_macro_tri.py --start-date 2015-01-01 --end-date 2024-12-31 --input data/processed/macro_features.parquet --output data/processed/macro_features_tri.parquet`: PASS.
    - `.venv\Scripts\python -m pytest tests\test_metrics.py tests\test_verify_phase13_walkforward.py tests\test_baseline_report.py tests\test_verify_phase15_alpha_walkforward.py tests\test_build_tri.py tests\test_feature_store.py tests\test_strategy.py tests\test_phase15_integration.py tests\test_alpha_engine.py -q`: PASS (`53 passed`).
    - Day 2 validation CSV: `10/10` checks passed.
  - Decision impact:
    - Signal-layer split-trap risk is removed for Day 2 artifacts while execution and compatibility paths remain stable for existing alpha-engine contracts.

Phase 18 Day 3 (2026-02-20): Cash Allocation Overlay — Discrete Trend > Continuous Vol Target (D-97) ✅
  - Decision:
    - Lock `Trend SMA200` as the reference cash-allocation overlay for Phase 18.
    - Do not adopt continuous volatility targeting for the production Day 4 critical path.
    - Defer continuous-overlay optimization to Phase 19.
  - Rationale:
    - Day 3 stress tests showed continuous vol targeting underperforms discrete binary trend filtering under transaction-cost constraints.
    - Vol-target variants improved drawdown depth but paid material turnover drag:
      - Vol Target 20d turnover: `8.452 annual` (~`42 bps` annual cost drag at `5 bps` costs)
      - Trend SMA200 turnover: `0.123 annual` (~`0.6 bps` annual cost drag)
    - Sharpe penalty in this decision frame: `0.761` vs `0.894` (`-0.133`).
    - This is classified as design-constraint discovery (not execution defect).
    - The outcome empirically validates `FR-041` regime-governor architecture:
      - discrete `GREEN/AMBER/RED` state machine with binary trend filters
      - superior to continuous exposure scaling in this system setting.
  - Evidence:
    - `data/processed/phase18_day3_overlay_metrics.csv`
    - `data/processed/phase18_day3_overlay_exposure_corr.csv` (vol vs trend correlation frame)
    - `data/processed/phase18_day3_overlay_3panel.png`
    - `docs/saw_phase18_day3_round1.md` (`ADVISORY_PASS`)
  - Files:
    - `strategies/cash_overlay.py` (continuous classes retained for future Phase 19 experimentation)
    - `scripts/cash_overlay_report.py`
  - Alternative considered:
    - Add dead-zone bands to reduce vol-target churn.
    - Rejected for Day 3 closeout under FIX vs FINETUNE discipline (avoid parameter salvage / curve-fit loop).

Phase 18 Day 4 (2026-02-20): Company Scorecard Baseline + Control-Toggle Wiring (D-98) ✅
  - Decision:
    - Implement Day 4 linear multi-factor scorecard baseline with equal-weight factors and control-theory toggles wired but defaulted `OFF`.
  - Implementation:
    - Added `strategies/factor_specs.py`:
      - `FactorSpec` with candidate-column fallbacks, direction, weight, normalization, and control toggles:
        - `use_sigmoid_blend`
        - `use_dirty_derivative`
        - `use_leaky_integrator`
      - default factor set:
        - momentum (`resid_mom_60d`)
        - quality (`quality_composite` fallback `capital_cycle_score`)
        - volatility (`realized_vol_21d` fallback `yz_vol_20d`)
        - illiquidity (`illiq_21d` fallback `amihud_20d`)
    - Added `strategies/company_scorecard.py`:
      - vectorized cross-sectional score computation with per-factor contribution columns.
      - normalization modes: `zscore`, `rank`, `raw`.
      - control toggles applied conditionally and PIT-safe over per-permno series.
    - Added `scripts/scorecard_validation.py`:
      - computes Day 4 scores from `features.parquet`.
      - emits validation checks and scored output artifacts.
    - Updated `data/feature_store.py`:
      - scorecard alias columns persisted:
        - `quality_composite`
        - `realized_vol_21d`
        - `illiq_21d`
    - Added tests:
      - `tests/test_company_scorecard.py`
  - Verification:
    - `.venv\Scripts\python -m py_compile strategies/factor_specs.py strategies/company_scorecard.py scripts/scorecard_validation.py tests/test_company_scorecard.py`: PASS.
    - `.venv\Scripts\python -m pytest tests/test_company_scorecard.py tests/test_feature_store.py -q`: PASS.
    - `.venv\Scripts\python -m pytest tests/test_metrics.py tests/test_verify_phase13_walkforward.py tests/test_baseline_report.py tests/test_verify_phase15_alpha_walkforward.py tests/test_build_tri.py tests/test_feature_store.py tests/test_strategy.py tests/test_phase15_integration.py tests/test_alpha_engine.py tests/test_cash_overlay.py tests/test_company_scorecard.py -q`: PASS (`68 passed`).
    - `.venv\Scripts\python scripts/scorecard_validation.py --input-features data/processed/features.parquet --start-date 2015-01-01 --end-date 2024-12-31 --output-validation-csv data/processed/phase18_day4_scorecard_validation.csv --output-scores-csv data/processed/phase18_day4_company_scores.csv`: PASS.
  - Decision impact:
    - Day 4 baseline scoring infrastructure is operational and ablation-ready.
    - Control-theory hooks are integrated without contaminating baseline (all toggles default OFF).
    - Validation objectives still open for tuning loop:
      - score coverage below target (`88.36% < 95%`).
      - quartile spread sigma below target (`1.793 < 2.0`).
      - non-gate watch metric shows factor under-contribution (`min share 0.089 < 0.10`).

Phase 18 Day 5 (2026-02-20): Ablation Matrix Result — Integrator Wins on Sharpe/Turnover, Coverage/Spread Still Binding (D-99) ✅
  - Decision:
    - Accept Day 5 as `ADVISORY_PASS`.
    - Carry forward `ABLATION_C3_INTEGRATOR` as Day 6 starting candidate for robustness checks.
    - Keep Day 5 acceptance gates for coverage/spread open (not forced closed by parameter salvage).
  - Implementation:
    - Added `scripts/day5_ablation_report.py` with 9-config matrix execution and atomic artifacts.
    - Added explicit score validity modes in `strategies/company_scorecard.py`:
      - `complete_case`
      - `partial`
      - `impute_neutral`
    - Added runtime guardrails:
      - active-return missing-data fail-fast + optional override (`--allow-missing-returns`)
      - dense matrix size ceiling (`--max-matrix-cells`)
      - empty-data artifact write path (`status=no_data`)
    - Added tests:
      - `tests/test_day5_ablation_report.py`
      - expanded `tests/test_company_scorecard.py` for scoring-mode validity ordering.
  - Evidence:
    - `data/processed/phase18_day5_ablation_metrics.csv`
    - `data/processed/phase18_day5_ablation_deltas.csv`
    - `data/processed/phase18_day5_ablation_summary.json`
    - `.venv\Scripts\python -m pytest tests\test_metrics.py tests\test_verify_phase13_walkforward.py tests\test_baseline_report.py tests\test_verify_phase15_alpha_walkforward.py tests\test_build_tri.py tests\test_feature_store.py tests\test_strategy.py tests\test_phase15_integration.py tests\test_alpha_engine.py tests\test_cash_overlay.py tests\test_company_scorecard.py tests\test_day5_ablation_report.py` -> PASS (`73 passed`).
  - Result snapshot:
    - Baseline (`BASELINE_DAY4`, complete-case): coverage `47.82%`, spread `1.842`, Sharpe `0.764`, turnover `64.934`.
    - Best config (`ABLATION_C3_INTEGRATOR`): coverage `52.37%`, spread `1.800`, Sharpe `1.007`, turnover `19.794`.
    - Turnover reduction vs baseline: `69.52%` (pass).
    - Coverage (`>=95%`) and spread (`>=2.0`) remain failed.
  - Rationale:
    - Day 5 objective was controlled falsification/selection, not forced target pass-through.
    - Integrator materially reduced churn and improved risk-adjusted performance without overfitting weight topology.
    - Coverage/spread constraints now clearly identified as data-availability + factor-structure limits requiring Day 6 robustness framing, not blind Day 5 retuning.
  - Alternative considered:
    - Force pass by relaxing validity semantics globally to impute-neutral and/or over-tilting hierarchical weights.
    - Rejected for governance integrity (would contaminate the control-group comparison and blur ablation attribution).

Phase 18 Day 6 (2026-02-20): Walk-Forward Validation — C3 Crisis Control Confirmed, Regime Robustness Incomplete (D-100) ✅
  - Decision:
    - Close Day 6 as `ADVISORY_PASS`.
    - Retain C3 integrator (`decay=0.95`) as a defensiveness mechanism, not yet as universal default.
    - Carry failed robustness checks (CHK-39, CHK-41, CHK-48, CHK-50, CHK-51..53) forward to Day 7 cyclical-exception work.
  - Implementation:
    - Added `scripts/day6_walkforward_validation.py` with:
      - walk-forward windows (`W1..W4`),
      - decay sweep (`0.85..0.99`),
      - crisis turnover validation.
    - Added `tests/test_day6_walkforward_validation.py`.
    - Produced Day 6 artifacts:
      - `phase18_day6_walkforward.csv`
      - `phase18_day6_decay_sensitivity.csv`
      - `phase18_day6_crisis_turnover.csv`
      - `phase18_day6_checks.csv`
      - `phase18_day6_summary.json`
  - Evidence:
    - Day 6 checks: `9/16` pass, `7/16` fail.
    - Critical gate CHK-54: PASS (`>=15%` turnover reduction in all crisis windows, minimum observed `80.38%`).
    - Full impacted regression:
      - `.venv\Scripts\python -m pytest tests\test_metrics.py tests\test_verify_phase13_walkforward.py tests\test_baseline_report.py tests\test_verify_phase15_alpha_walkforward.py tests\test_build_tri.py tests\test_feature_store.py tests\test_strategy.py tests\test_phase15_integration.py tests\test_alpha_engine.py tests\test_cash_overlay.py tests\test_company_scorecard.py tests\test_day5_ablation_report.py tests\test_day6_walkforward_validation.py -q` -> PASS (`77 passed`).
  - Rationale:
    - C3 continues to show strong turnover suppression in crisis regimes (primary Day 6 safety concern).
    - Out-of-sample upside-capture and plateau checks failed, indicating parameter/regime brittleness.
    - Treating Day 6 as hard PASS would overstate generalization; advisory framing preserves discipline.
  - Alternative considered:
    - Immediate post-Day 6 parameter salvage to force CHK-51..53 pass.
    - Rejected to avoid mixing robustness diagnostics with tuning in the same gate.

Phase 18 Closure (2026-02-20): Lock C3 Integrator and Close Sprint (D-101) ✅
  - Decision:
    - Close Phase 18 and lock `C3_LEAKY_INTEGRATOR_V1` for production use in this phase context.
    - Accept Day 6 advisory failures as documented design tradeoffs for this closure cycle.
  - Implementation:
    - Added lock module:
      - `strategies/production_config.py`
      - immutable `PRODUCTION_CONFIG_V1` built from `FactorSpec` defaults with integrator-only toggles and `decay=0.95`.
    - Added closure/deployment docs:
      - `docs/saw_phase18_day6_final.md`
      - `docs/production_deployment.md`
      - `docs/phase18_closure_report.md`
    - Updated lifecycle docs:
      - `docs/phase18-brief.md` (Phase Closed)
      - `docs/lessonss.md` (new closure lesson)
  - Evidence:
    - `data/processed/phase18_day5_ablation_metrics.csv`:
      - baseline Sharpe `0.764` -> C3 Sharpe `1.007`
      - baseline turnover `64.934` -> C3 turnover `19.794`
    - `data/processed/phase18_day6_summary.json`:
      - checks `9/16` pass, `7/16` fail
      - critical CHK-54 pass
      - missing active-return cells under override run: baseline `0`, C3 `13704`
    - `data/processed/phase18_day6_crisis_turnover.csv`:
      - minimum crisis turnover reduction `80.38%`.
  - Rationale:
    - C3 keeps the strongest proven crisis-turnover suppression from Day 6.
    - User/operator directive explicitly preferred stability and simplicity over another adaptive tuning cycle.
    - Closure preserves an auditable baseline and defers further complexity to later phases.
  - Open risks accepted at closure:
    - CHK-41, CHK-48, CHK-50 upside/recovery consistency.
    - CHK-51, CHK-52, CHK-53 decay plateau robustness.
  - Rollback path:
    - stop using `PRODUCTION_CONFIG_V1` and restore pre-lock scorecard wiring.
    - keep Phase 18 artifacts/docs for audit traceability.

Phase 21 Day 1 (2026-02-20): Standalone Stop-Loss & Drawdown Control Module (D-102) ✅
  - Decision:
    - Implement a standalone risk-control module at `strategies/stop_loss.py` for position-level stops and portfolio drawdown tiers.
    - Keep ATR mode explicit as close-only proxy with simple moving average.
    - Enforce D-57 ratchet invariant in stop updates.
  - Implementation:
    - Added `strategies/stop_loss.py`:
      - `StopLossConfig` with `atr_mode='proxy_close_only'`.
      - `ATRCalculator` using:
        - `ATR_t = SMA(|close_t - close_{t-1}|, window=20)`.
      - `StopLossManager` with:
        - initial stop (`entry - 2.0*ATR`),
        - trailing stop (`price - 1.5*ATR`),
        - time-based underwater exit (`days_held > max_underwater_days`),
        - ratchet update (`stop_t = max(stop_{t-1}, candidate_t)`).
      - `PortfolioDrawdownMonitor` tiers:
        - drawdown thresholds: `-8% / -12% / -15%`,
        - scales: `0.75 / 0.50 / 0.00`,
        - recovery threshold: `>-4%`.
      - Optional edge-case guard:
        - `min_stop_distance_abs` (default `0.0`) to avoid zero-distance stops under zero volatility.
    - Added `tests/test_stop_loss.py` (18 tests) covering:
      - ATR math and date lookups,
      - stage transitions,
      - D-57 non-decreasing stop path,
      - time-based exits,
      - drawdown tier transitions,
      - zero-volatility and minimum-distance edge case.
  - Evidence:
    - `.venv\Scripts\python -m py_compile strategies/stop_loss.py tests/test_stop_loss.py` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_stop_loss.py -q` -> PASS (`18 passed`).
    - `.venv\Scripts\python -m pytest tests/test_phase15_integration.py -q` -> PASS (`3 passed`).
  - Rationale:
    - Day 1 requires a reusable, testable stop-loss subsystem that is independent of OHLC dependencies.
    - Current data constraints are close-only; explicit ATR mode removes hidden assumptions.
    - Ratchet enforcement preserves D-57 invariants while enabling phased stop behavior.
  - Open risks:
    - Module is not yet wired into live portfolio execution path; integration is deferred to later Phase 21 tasks.
    - `.pytest_cache` ACL warning persists on this environment (non-blocking to test outcomes).
  - Mitigation / next gate:
    - Phase 21 Day 2 must include integration activation gate, runtime observability checks, and rollback procedure updates in `docs/runbook_ops.md` before enabling live usage.
  - Rollback path:
    - remove `strategies/stop_loss.py` and `tests/test_stop_loss.py`.
    - revert Phase 21 Day 1 doc entries in brief/notes/lessons if this decision is revoked.

Phase 21.1 Path1 Directive (2026-02-21): Sector/Industry Context Pre-Rank + Dictatorship Telemetry (D-103) ✅
  - Decision:
    - Enforce Path1 directive context wiring by attaching static sector/industry metadata to the conviction frame before ticker-pool ranking.
    - Add explicit telemetry contract fields in slice artifacts:
      - `DICTATORSHIP_MODE`
      - `path1_directive_id`
      - context coverage/source breakdown fields.
  - Implementation:
    - `strategies/company_scorecard.py`:
      - added deterministic sector-map loader from `data/static/sector_map.parquet`.
      - attach order: `permno` map first, then `ticker` fallback.
      - emits:
        - `sector`
        - `industry`
        - `sector_context_source`
        - `path1_sector_context_attached`
      - runs attachment before `rank_ticker_pool`.
    - `scripts/phase21_1_ticker_pool_slice.py`:
      - emits Path1 fields into sample CSV:
        - `sector`, `industry`, `sector_context_source`,
        - `path1_sector_context_attached`,
        - `path1_directive_id`,
        - `DICTATORSHIP_MODE`.
      - emits summary JSON block `path1_telemetry` with:
        - attached coverage ratio,
        - known sector/industry counts,
        - context source distribution,
        - sample sector/industry composition counts.
  - Evidence:
    - `strategies/company_scorecard.py`
    - `scripts/phase21_1_ticker_pool_slice.py`
    - `docs/notes.md`
    - `docs/lessonss.md`
  - Rationale:
    - Static sector map exists as local bedrock and is safe to inject in hot path without live provider dependencies.
    - Deterministic pre-rank context merge avoids hidden runtime drift and improves traceability of Path1 constraints.
  - Rollback path:
    - remove context-attach helper calls and Path1 telemetry fields from slice outputs.
    - keep previous sample/summary schema for consumers that do not need Path1 directives.

Phase 22 Baseline Harness (2026-02-21): Separability Telemetry Scaffold (D-105) ✅
  - Decision:
    - Add a dedicated separability harness for de-anchor validation with `--dictatorship-mode off` baseline telemetry.
    - Lock Section 2 directives in implementation:
      - Jaccard stability on `odds_score`.
      - Silhouette labels from posterior argmax.
      - one-effective-class days emit `NaN` + coverage counters (no synthetic fill).
    - Emit both stability sets:
      - `top_decile`
      - `top_30`.
  - Implementation:
    - Added `scripts/phase22_separability_harness.py`:
      - loads Phase 20 conviction frame in PIT-safe path,
      - computes day-over-day Jaccard overlap for `top_decile` and `top_30`,
      - computes silhouette in post-neutralized/post-MAD geometry with posterior argmax labels,
      - computes archetype recall ranks/hits for `MU/LRCX/AMAT/KLAC`,
      - emits:
        - `data/processed/phase22_separability_daily.csv`
        - `data/processed/phase22_separability_summary.json`.
    - Added `tests/test_phase22_separability_harness.py`:
      - Jaccard math,
      - one-class silhouette policy,
      - finite two-class silhouette path,
      - fixed top-N archetype hit schema.
    - Added deterministic manual silhouette fallback when `sklearn.metrics` is unavailable.
  - Evidence:
    - `.venv\Scripts\python -m py_compile scripts/phase22_separability_harness.py tests/test_phase22_separability_harness.py` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_phase22_separability_harness.py -q` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_ticker_pool.py tests/test_company_scorecard.py -q` -> PASS.
    - `.venv\Scripts\python scripts/phase22_separability_harness.py --start-date 2024-12-01 --as-of-date 2024-12-24 --dictatorship-mode off` -> PASS.
  - Baseline snapshot (2024-12-01 to 2024-12-24, mode `PATH1_DEPRECATED`):
    - days: `17` (all with valid odds rows).
    - Jaccard mean:
      - `top_decile = 0.3438`
      - `top_30 = 0.3560`.
    - Silhouette:
      - valid days `16`,
      - mean `0.0786`,
      - one-class days `1` (`2024-12-02`).
    - Archetype hit rates:
      - aggregate `top_decile = 0.3382`,
      - aggregate `top_30 = 0.5441`.
  - Rationale:
    - Promotion thresholds must be set from observed unsupervised baseline telemetry, not inferred from target outcomes.
    - Manual silhouette fallback preserves deterministic telemetry in environments where `sklearn.metrics` is unavailable.
  - Rollback path:
    - remove `scripts/phase22_separability_harness.py` and `tests/test_phase22_separability_harness.py`.
    - stop publishing Phase 22 separability artifacts.

Phase 23 Step 1 (2026-02-22): FMP PIT Estimates Ingestion Scaffold (D-106) ✅
  - Decision:
    - Implement Path A scaffold for historical consensus ingestion using Financial Modeling Prep (FMP):
      - endpoint: `/api/v3/historical/analyst-estimates/{ticker}`.
    - Enforce internal PIT schema contract and identifier integrity before downstream SDM feature work.
  - Implementation:
    - Added `scripts/ingest_fmp_estimates.py` with:
      - API auth from `FMP_API_KEY` (graceful fail + explicit warning when missing),
      - ticker→permno crosswalk from `data/static/sector_map.parquet`,
      - strict processed schema: `permno,ticker,published_at,horizon,metric,value`,
      - quarterly/annual normalization into `horizon='NTM'`,
      - PIT period filter: include only `period_end > published_at`,
      - atomic parquet writes,
      - write-safety guard to prevent overwriting existing outputs when fetch/mapping yields empty result.
    - Added tests:
      - `tests/test_ingest_fmp_estimates.py`
      - coverage: NTM quarter sum, FY fallback, PIT period filter, schema/mapping contract.
  - Evidence:
    - `.venv\Scripts\python -m py_compile scripts/ingest_fmp_estimates.py tests/test_ingest_fmp_estimates.py` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_ingest_fmp_estimates.py -q` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_ingest_fmp_estimates.py tests/test_ticker_pool.py tests/test_company_scorecard.py -q` -> PASS.
    - Dry-run command:
      - `.venv\Scripts\python scripts/ingest_fmp_estimates.py --tickers MU,AMAT`
      - observed runtime warning: missing `FMP_API_KEY` (graceful fail path confirmed).
  - Rationale:
    - Step 1 must be complete before SDM revision features can be computed.
    - Preserving last-known-good parquet outputs under transient fetch/crosswalk failures reduces operational blast radius.
  - Open risks:
    - API connectivity and payload mapping are not yet validated end-to-end in this environment due missing `FMP_API_KEY`.
  - Rollback path:
    - remove `scripts/ingest_fmp_estimates.py` and `tests/test_ingest_fmp_estimates.py`.
    - revert Step 1 ingest wiring until credentialed dry-run evidence is available.

Phase 23 Step 1.1 (2026-02-22): Rate-Aware Cache-First FMP Ingestion + Scoped Universe (D-107) ✅
  - Decision:
    - Upgrade ingest engine to operate under API-credit/rate constraints with local cache-first behavior.
    - Keep Phase 23 Path A active while enabling local/offline reuse and deterministic merge into processed estimates.
  - Implementation:
    - `scripts/ingest_fmp_estimates.py`:
      - added per-ticker JSON cache at `data/raw/fmp_cache/{ticker}.json`,
      - checks cache before network request,
      - supports scoped universe via `--tickers` and `--tickers-file` with `--max-tickers` cap,
      - pre-filters requested universe by crosswalk-mapped tickers before API calls,
      - adds exponential backoff for 429 conditions and cache-only continuation after limit exhaustion,
      - adds merge-with-existing mode where new rows deterministically override existing rows on dedupe keys.
    - added scoped starter list:
      - `data/raw/fmp_target_tickers.txt` (20 semicap/cyclical-focused names).
    - expanded tests:
      - `tests/test_ingest_fmp_estimates.py` now covers target resolution cap, cache roundtrip, and deterministic merge override.
  - Evidence:
    - `.venv\Scripts\python -m py_compile scripts/ingest_fmp_estimates.py tests/test_ingest_fmp_estimates.py` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_ingest_fmp_estimates.py tests/test_ticker_pool.py tests/test_company_scorecard.py -q` -> PASS.
    - Runtime attempt:
      - `.venv\Scripts\python scripts/ingest_fmp_estimates.py --tickers-file data/raw/fmp_target_tickers.txt --max-tickers 500`
      - connectivity failed with network socket permission error (`WinError 10013`), no cache/processed writes performed.
  - Rationale:
    - API budgets and rate limits require cache-first behavior and universe scoping to remain operationally viable.
    - deterministic merge semantics prevent stale records from overriding newly fetched PIT rows.
  - Open risks:
    - Current environment still blocks outbound API access (`WinError 10013`), so live cache population remains unverified.
    - No local R3000 membership parquet artifact currently available for auto-scope bootstrap/merge.
  - Rollback path:
    - remove cache-first and merge extensions from `scripts/ingest_fmp_estimates.py`,
    - remove `data/raw/fmp_target_tickers.txt`,
    - revert extended tests in `tests/test_ingest_fmp_estimates.py`.

Phase 23 Step 2 (2026-02-22): 3-Pillar SDM Ingestion + PIT Assembler Hardening (D-108) ✅
  - Decision:
    - Fix Pillar 1/2 `merge_asof` failure by enforcing global timeline-key sorting before join.
    - Add dynamic `totalq.total_q` schema probe so optional intangible fields are ingested when present without breaking on schema drift.
    - Enforce allow+audit policy for unmapped identifiers (retain rows, write audit file, never silent-drop).
    - Add explicit final assembler script for PIT-safe quarterly-to-daily joins:
      - `scripts/assemble_sdm_features.py`.
  - Implementation:
    - `scripts/ingest_compustat_sdm.py`:
      - added `_assert_merge_asof_sorted` and timeline-first sort contract:
        - left: `published_at_dt, gvkey`
        - right: `pit_date, gvkey`.
      - added dynamic `totalq` probing:
        - `information_schema.columns` lookup,
        - required/stable/optional field selection.
      - added allow+audit crosswalk behavior:
        - unmapped rows retained,
        - audit output `data/processed/fundamentals_sdm_unmapped_permno_audit.csv`.
    - `scripts/assemble_sdm_features.py`:
      - backward `merge_asof` joins from fundamentals `published_at` to macro/factor daily timestamps with configurable tolerance.
      - sector/industry context attach by permno first, then ticker fallback.
      - atomic write for `data/processed/features_sdm.parquet`.
    - tests added:
      - `tests/test_ingest_compustat_sdm.py`
      - `tests/test_assemble_sdm_features.py`.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_ingest_compustat_sdm.py tests/test_assemble_sdm_features.py tests/test_ingest_fmp_estimates.py -q` -> PASS (`13 passed`).
    - dry-runs:
      - `scripts/ingest_compustat_sdm.py --tickers NVDA,MU,AMAT,LRCX,KLAC,COHR,TER,CIEN --start-date 2022-01-01 --end-date 2025-12-31 --dry-run` -> PASS.
      - `scripts/ingest_frb_macro.py --start-date 2022-01-01 --end-date 2025-12-31 --dry-run` -> PASS.
      - `scripts/ingest_ff_factors.py --start-date 2022-01-01 --end-date 2025-12-31 --dry-run` -> PASS.
      - `scripts/assemble_sdm_features.py --dry-run --tolerance-days 7` -> PASS.
    - writes:
      - `data/processed/fundamentals_sdm.parquet` -> written (128 rows, scoped slice).
      - `data/processed/macro_rates.parquet` -> written (1140 rows).
      - `data/processed/ff_factors.parquet` -> written (1003 rows).
      - `data/processed/features_sdm.parquet` -> written (128 rows).
  - Rationale:
    - `merge_asof` correctness is non-negotiable for PIT-safe quarterly/annual joins.
    - dynamic `totalq` probing removes brittle schema assumptions while preserving stable fields.
    - allow+audit keeps complete lineage under mapping gaps and avoids silent data-loss.
  - Open risks:
    - `frb.rates_daily` currently terminates at 2025-02-13 in this runtime, so later fundamentals rows show expected macro nulls under tolerance.
    - `.pytest_cache` ACL warning persists in environment; does not affect test pass/fail.
  - Rollback path:
    - remove `scripts/assemble_sdm_features.py`,
    - revert `scripts/ingest_compustat_sdm.py` to pre-D-108 behavior,
    - remove `tests/test_ingest_compustat_sdm.py` and `tests/test_assemble_sdm_features.py`,
    - regenerate SDM artifacts from prior ingestion scripts.

Phase 23 Step 2.1 (2026-02-22): Strict 14-Day Feed-Horizon Tolerance Gate (D-109) ✅
  - Decision:
    - Enforce fixed `14d` staleness tolerance on SDM assembler `merge_asof` joins for both macro and FF factor pillars.
    - Add explicit warning telemetry counting rows nulled by the tolerance gate (vs no-tolerance baseline).
  - Implementation:
    - `scripts/assemble_sdm_features.py`:
      - replaced configurable tolerance with strict constant:
        - `ASOF_TOLERANCE = Timedelta('14d')`.
      - added `_count_rows_nulled_by_tolerance` helper:
        - computes no-tolerance vs strict-tolerance asof matches,
        - logs count of rows nulled strictly due to staleness.
      - removed CLI `--tolerance-days` override to keep tolerance policy fixed.
    - `tests/test_assemble_sdm_features.py`:
      - updated assembler calls for fixed tolerance path,
      - added regression test for stale-match nulling counter.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_assemble_sdm_features.py -q` -> PASS.
    - `.venv\Scripts\python scripts/assemble_sdm_features.py --dry-run` -> PASS with warning:
      - macro nulled `30` rows,
      - ff nulled `4` rows.
    - `.venv\Scripts\python scripts/assemble_sdm_features.py` -> PASS and wrote `features_sdm.parquet`.
  - Rationale:
    - prevents stale macro/factor data from being forward-carried too far beyond publication anchors.
    - warning telemetry makes feed-horizon degradation explicit at runtime.
  - Open risks:
    - upstream feed endpoints still cap at 2025-02-13 (FRB) and 2025-12-31 (FF), so late rows remain null until source refresh.
  - Rollback path:
    - restore previous configurable tolerance behavior in `scripts/assemble_sdm_features.py`,
    - remove stale-null audit helper and associated tests if policy is reversed.

Phase 23 Step 6 (2026-02-22): BGM Manifold Swap to SDM + Macro Cycle Geometry (D-110) ✅
  - Decision:
    - Switch clustering geometry from Phase 22 price-exhaust mix to SDM/macro manifold only.
    - Enforce strict geometry-risk separation: no beta/volatility feature may enter BGM matrix.
    - Add migration-safe dual-read feature adapter to combine legacy and SDM feature artifacts during transition.
  - Implementation:
    - `scripts/assemble_sdm_features.py`:
      - expanded fundamentals from quarterly releases to daily cadence via per-entity forward fill.
      - precomputed industry medians (`ind_rev_accel`, etc.) and cycle interaction:
        - `CycleSetup = yield_slope_10y2y * rmw * cma`.
    - `scripts/phase20_full_backtest.py`:
      - updated `_load_features_window` to dual-read:
        - base: `features.parquet`,
        - overlay: `features_sdm.parquet`,
        - merge key: `[date, permno]` with UTC-naive normalization.
    - `strategies/company_scorecard.py`:
      - added SDM/macro columns to conviction-frame bridge and lagged routing into ticker-pool input.
    - `strategies/ticker_pool.py`:
      - geometry features now fixed to:
        - `rev_accel, inv_vel_traj, gm_traj, op_lev, intang_intensity, q_tot, rmw, cma, yield_slope_10y2y, CycleSetup`.
      - added explicit assert guards rejecting risk columns/tokens (`beta`, `vol`) in geometry config.
    - tests:
      - added `tests/test_phase20_full_backtest_loader.py`.
      - updated `tests/test_ticker_pool.py` and `tests/test_assemble_sdm_features.py`.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_assemble_sdm_features.py tests/test_phase20_full_backtest_loader.py tests/test_ticker_pool.py tests/test_company_scorecard.py -q` -> PASS (`40 passed`).
    - `.venv\Scripts\python scripts/assemble_sdm_features.py` -> PASS (`11254` rows written).
    - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2024-01-01 --as-of-date 2024-12-24 --top-longs 5 --short-excerpt 5 --dictatorship-mode on --output-csv data/processed/phase23_action2_smoke_sample.csv --output-summary-json data/processed/phase23_action2_smoke_summary.json` -> PASS.
  - Rationale:
    - isolates clustering geometry to causal SDM state and macro-cycle drivers while preserving risk controls in sizing/governor path.
    - migration-safe dual-read avoids breaking existing scripts during artifact transition.
  - Open risks:
    - sparse SDM coverage can reduce valid geometry rows on some dates; ticker-pool min-universe skip warnings are expected until coverage improves.
  - Rollback path:
    - restore old `TickerPoolConfig.feature_columns` set and remove geometry risk-guard asserts.
    - disable dual-read overlay by reverting `_load_features_window` to single-source read.
    - revert daily-expansion/precompute additions in `scripts/assemble_sdm_features.py`.

Phase 23 Step 6.1 (2026-02-22): Hierarchical Imputation to Prevent Universe Collapse (D-111) ✅
  - Decision:
    - Eliminate NaN-driven cross-sectional collapse in unsupervised geometry by introducing strict PIT imputation hierarchy before robust scaling.
    - Do not drop rows from geometry matrix due to sparse SDM fields.
  - Implementation:
    - `strategies/ticker_pool.py`:
      - added hierarchical imputation:
        - Level 1: same-date industry median (fallback key: sector),
        - Level 2: neutral `0.0` fill for remaining missing values.
      - integrated imputed geometry builder before z-score/MAD path.
      - added universe telemetry:
        - `geometry_universe_before_imputation`,
        - `geometry_universe_after_imputation`,
        - `geometry_industry_impute_cells`,
        - `geometry_zero_impute_cells`.
    - `scripts/phase22_separability_harness.py`:
      - aligned geometry reconstruction with ticker-pool imputed z-matrix path.
      - surfaced imputation telemetry in summary aggregates.
    - tests:
      - added regression coverage for universe preservation under sparse SDM features.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_ticker_pool.py tests/test_phase22_separability_harness.py tests/test_company_scorecard.py -q` -> PASS.
    - `.venv\Scripts\python scripts/phase22_separability_harness.py --start-date 2024-12-01 --as-of-date 2024-12-24 --dictatorship-mode off --output-csv data/processed/phase22_separability_daily_action2.jsonfix.csv --output-summary-json data/processed/phase22_separability_summary_action2.jsonfix.json` -> PASS.
    - summary telemetry:
      - `days_with_valid_odds: 17` (was 1),
      - `geometry_universe_before_imputation mean: 2.59`,
      - `geometry_universe_after_imputation mean: 389.0`.
  - Rationale:
    - preserves cross-section breadth required for unsupervised clustering while remaining PIT-safe and neutral on unknown fields.
  - Open risks:
    - silhouette remains invalid in this window (`one_effective_class`) despite recovered universe breadth.
  - Rollback path:
    - revert imputation helpers in `strategies/ticker_pool.py` and harness alignment in `scripts/phase22_separability_harness.py`,
    - restore prior NaN-filter geometry behavior.

Phase 23 Closure (2026-02-22): Median-Neutralized + Diagonal-Covariance Memory-Trough Isolation (D-112) ✅
  - Decision:
    - Formally close Phase 23 and lock clustering manifold state for promotion to historical validation.
    - Lock the following in `strategies/ticker_pool.py`:
      - geometry feature manifold,
      - cluster ranker heuristic,
      - covariance mode/hyperparameters.
    - Adopt robust closeout settings:
      - cross-sectional peer neutralization by median (industry granularity preferred; sector fallback),
      - diagonal covariance mode for clustering-distance stability.
  - Implementation:
    - `strategies/ticker_pool.py`:
      - neutralization baseline switched to median by peer group,
      - covariance mode surfaced and fixed to `diag`,
      - final locked cycle-aware ranker retained.
    - `strategies/company_scorecard.py`:
      - context plumbing extended to pass `industry_group` when available (fallback remains `industry -> sector`).
    - `scripts/phase20_full_backtest.py`:
      - explicit SDM adapter CLI input added:
        - `--input-sdm-features` (default `data/processed/features_sdm.parquet`),
      - runtime print telemetry now confirms SDM overlay path existence.
  - Evidence:
    - `.venv\Scripts\python scripts/phase22_separability_harness.py --start-date 2024-12-01 --as-of-date 2024-12-24 --dictatorship-mode off --output-csv data/processed/phase22_separability_daily_action2_outlierskewfix.csv --output-summary-json data/processed/phase22_separability_summary_action2_outlierskewfix.json` -> PASS.
    - `data/processed/phase22_separability_summary_action2_outlierskewfix.json`:
      - `silhouette_score.mean = 0.009045008492558893` (positive),
      - `silhouette_single_class_days = 0`,
      - `MU` top-30 hit-rate > 0 in closeout run.
    - `.venv\Scripts\python -m py_compile strategies/ticker_pool.py strategies/company_scorecard.py scripts/phase20_full_backtest.py` -> PASS.
  - Rationale:
    - Median baselines prevent mega-cap outlier skew from distorting peer-neutralized geometry.
    - Diagonal covariance reduces cross-feature overlap instability in fat-tailed fundamental spaces.
    - With positive mean silhouette and memory-trough signal recovery in the closeout window, Phase 23 exits feature-engineering and transitions to Phase 20 historical validation.
  - Open risks:
    - Archetype recall remains uneven across semiconductor names in strict top-30 ranking; this is now a validation-phase (not manifold-design) risk.
  - Rollback path:
    - revert D-112 manifold hardening and return to D-111 state if PM rejects Phase 23 closeout evidence.

Phase Governance Update (2026-02-22): SAW Phase-End Closure Package (D-113) ✅
  - Decision:
    - Extend SAW from round-close only to explicit phase-end closure protocol.
    - Require full test matrix, subagent end-to-end replay, PM handover artifact, and `/new` context bootstrap with confirmation gate.
  - Implementation:
    - Updated `.codex/skills/saw/SKILL.md`:
      - added mandatory Section 6 `Phase-End Closeout Protocol` with checks `CHK-PH-01..CHK-PH-05`.
      - added phase-end hard gate and required report blocks (`PhaseEndValidation`, `HandoverDoc`, `ContextPacketReady`, `ConfirmationRequired`).
      - hardened execution contract with runtime smoke timeout (`180s`), reproducible E2E matching criteria, and explicit next-phase approval token handling.
    - Added `.codex/skills/saw/references/phase_end_handover_template.md`:
      - PM-friendly handover template with formula register, explicit logic chain, and required data-integrity evidence slots.
    - Updated `.codex/skills/saw/agents/openai.yaml`:
      - default prompt now enforces phase-end checks, `NextPhaseApproval: PENDING`, and exact `approve next phase` confirmation token.
    - Updated `docs/checklist_milestone_review.md`:
      - added missing phase-end closure tasks (full regression, runtime smoke, data integrity, handover, `/new` packet), plus explicit lessons-loop gate.
  - Rationale:
    - Phase close required consistent governance outputs across testing, documentation, and handoff; these were previously implied but not strictly enforced.
  - Rollback path:
    - revert D-113 files to prior versions and restore prior SAW round-only behavior.

Core Module Refactor Stage 2 (2026-02-22): Root-to-Core Module Relocation (D-114) ✅
  - Decision:
    - Enforce root policy where only entrypoints remain as Python files in root (`app.py`, `launch.py`).
    - Relocate runtime modules `engine.py`, `etl.py`, `optimizer.py` into `core/` package.
    - Use temporary root shims during import migration, then destroy shims after reconciliation.
  - Implementation:
    - Added package scaffold:
      - `core/__init__.py`
    - Moved modules:
      - `engine.py -> core/engine.py`
      - `etl.py -> core/etl.py`
      - `optimizer.py -> core/optimizer.py`
    - Reconciled internal imports to `core` namespace across app/backtests/scripts/tests.
    - Updated `core/optimizer.py` internal dependency from root import to package-relative import (`from . import engine`).
    - Destroyed temporary root shims once import scan showed no internal references.
    - Updated docs path references:
      - `docs/spec.md` (`core/engine.py`, `core/optimizer.py`)
      - `docs/prd.md` (`core/optimizer.py`)
  - Evidence:
    - Import reconciliation scan:
      - `rg -n --glob '*.py' "<engine|optimizer|etl root import patterns>" .` -> only `core.*` imports remain.
    - Root policy check:
      - root files now: `AGENTS.md`, `app.py`, `launch.py`, `pyproject.toml`, `requirements.txt`.
    - Entry-point dry run:
      - `.venv\Scripts\python launch.py --help` -> PASS.
    - Full test run:
      - `.venv\Scripts\python -m pytest -q` -> FAIL (`5` pre-existing/non-import failures in SDM/ticker-pool tests).
  - Rationale:
    - Structural separation improves module hygiene without changing entrypoint ergonomics.
    - Shim lifecycle reduced migration risk while enabling strict root cleanup.
  - Open risks:
    - Full-suite pytest remains red on five non-import tests (`tests/test_assemble_sdm_features.py`, `tests/test_phase20_full_backtest_loader.py`, `tests/test_ticker_pool.py`) that are outside this refactor scope.
  - Rollback path:
    - move `core/engine.py`, `core/etl.py`, `core/optimizer.py` back to root and restore legacy import statements.

Phase 20 Closure Wrap (2026-02-22): Golden Master Lock + PM Handover Packet (D-115) ✅
  - Decision:
    - Formally close Phase 20 as a completed milestone with a locked cyclical-trough operating profile and explicit Phase 24 runway.
    - Lock Phase 20 ranker and gate math for historical-validation handoff:
      - `cluster_score = (CycleSetup * 2.0) + op_lev + rev_accel + inv_vel_traj - q_tot`
      - `entry_gate = score_valid & (conviction_score >= 7.0) & pool_long_candidate & mom_ok & support_proximity`
      - hard exit selection remains `selected = entry_gate & (rank <= n_target)`.
    - Publish phase-end handover context packet for `/new` bootstrap and approval-token gating.
  - Implementation:
    - `strategies/ticker_pool.py`:
      - restored `_conviction_cluster_score` to Option A cyclical-trough formula (`+CycleSetup*2`, `-q_tot`).
    - `docs/phase_brief/phase20-brief.md`:
      - rewritten from stale Round-3 salvage state to formal closure brief with locked formulas, experiment ledger, structural boundary, and CI/CD handoff status.
    - `docs/notes.md`:
      - appended explicit Phase 20 lock formulas and source-path references.
    - `docs/lessonss.md`:
      - appended closure-round lesson for ranker-drift guardrail.
    - `docs/handover/phase20_handover.md`:
      - created PM-facing closure/handoff packet with formula register, logic chain, evidence matrix, and new-context bootstrap block.
    - `docs/saw_reports/saw_phase20_closeout_round4.md`:
      - created SAW closeout report with closure packet and validation lines.
  - Evidence:
    - Phase 20 ledger artifacts:
      - `data/processed/phase20_5y_hardgate_summary.json` (`CAGR=0.12124546831937266`, `Sharpe=0.653639319471661`, `MaxDD=-0.1843785358570833`).
      - `data/processed/phase20_5y_PRODUCTION_FINAL_summary.json` (`CAGR=0.012282190604340881`, `Sharpe=0.3377146011290567`, `MaxDD=-0.032054938043322045`).
    - MU diagnostic evidence:
      - `data/processed/diagnostic_MU_reverse_engineer.csv` (Oct 2022: `q_tot mean=3.2634692142857142`, `inv_vel_traj mean=0.0`, `conviction mean=3.510820467875683`).
    - Validation commands and results are recorded in `docs/saw_reports/saw_phase20_closeout_round4.md`.
  - Rationale:
    - closure package converts fragmented experiment outcomes into a locked and auditable operating baseline,
    - explicit handover packet prevents context loss at `/new` boundary,
    - ranker restore aligns runtime math with approved Option A capital-cycle thesis.
  - Open risks:
    - Full 5-year rerun under the freshly re-locked ranker was not executed in this docs/governance round; existing ledger remains prior run evidence.
  - Rollback path:
    - revert `strategies/ticker_pool.py::_conviction_cluster_score` to prior supercycle expression,
    - restore previous `docs/phase_brief/phase20-brief.md`, remove `docs/handover/phase20_handover.md`, and drop `D-115` entry if PM rejects closure package.

Context Bootstrap Governance Update (2026-02-23): Phase-End Context Artifact Refresh Policy (D-116) ✅
  - Decision:
    - Require explicit phase-end refresh of generated context artifacts before milestone closure:
      - `docs/context/current_context.json`
      - `docs/context/current_context.md`
    - Add a build-script validation gate so phase close fails when context artifacts are stale/missing/invalid.
  - Implementation:
    - Updated `.codex/skills/saw/SKILL.md` Section 6 with `CHK-PH-06` context refresh + validation command contract.
    - Updated `docs/checklist_milestone_review.md` with mandatory context artifact refresh checklist item.
    - Updated `docs/runbook_ops.md` with startup quickstart commands for context bootstrap:
      - `.venv\Scripts\python scripts/build_context_packet.py`
      - `invoke $context-bootstrap`
      - `.venv\Scripts\python scripts/build_context_packet.py --validate`
    - Updated `docs/notes.md` with context artifact schema and markdown packet contracts.
    - Updated `docs/lessonss.md` with a context-drift guardrail lesson entry.
  - Evidence:
    - Docs-only governance round; no test execution required.
    - Commands and artifact path contracts are documented in runbook + SAW phase-end protocol.
  - Rationale:
    - `/new` handoffs degrade when context artifacts are not regenerated and validated at phase boundaries.
  - Open risks:
    - `scripts/build_context_packet.py` and `$context-bootstrap` invocation semantics must stay stable across local environments.
  - Rollback note:
    - Revert `D-116` document edits to return to prior phase-close policy without mandatory context artifact refresh.

Context Bootstrap Implementation (2026-02-23): Deterministic Artifact Generator + Validation Gate (D-117) ✅
  - Decision:
    - Implement and retain script-backed context persistence as the canonical `/new` bootstrap mechanism.
    - Keep subagents for orchestration/review only; do not use subagent memory as persistence.
  - Implementation:
    - Added `scripts/build_context_packet.py`:
      - generates `docs/context/current_context.json` and `docs/context/current_context.md`.
      - enforces stable key contract (`schema_version`, `generated_at_utc`, `source_files`, `active_phase`, `what_was_done`, `what_is_locked`, `what_is_next`, `first_command`, `next_todos`).
      - added `--validate` mode for stale-drift detection against source docs.
      - validates markdown header contract and JSON->markdown parity.
    - Added tests:
      - `tests/test_build_context_packet.py` (8 tests passing).
      - `tests/conftest.py` to stabilize repo-root imports for direct `pytest` invocation.
    - Added skill:
      - `.codex/skills/context-bootstrap/SKILL.md`.
      - updated `.codex/skills/README.md` skill index.
    - Integrated governance docs already wired under `D-116` (`saw`/checklist/runbook).
  - Evidence:
    - `.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q` -> PASS (`8 passed`).
    - `.venv\Scripts\pytest tests\test_build_context_packet.py -q` -> PASS (`8 passed`).
    - `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
    - `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
    - artifacts present:
      - `docs/context/current_context.json`
      - `docs/context/current_context.md`
  - Rationale:
    - provides deterministic cross-session startup context with strict validation and reproducible operator commands.
  - Open risks:
    - two-file output commit is per-file atomic but not transactionally atomic across both files.
  - Rollback note:
    - remove `scripts/build_context_packet.py`, `tests/test_build_context_packet.py`, `tests/conftest.py`, `.codex/skills/context-bootstrap/`, and revert `D-116/D-117` docs wiring if policy is reversed.

Phase 23 Orthogonal Sizing Upgrade (2026-02-23): GREEN Softmax + Raw-Geometry Test Contract (D-118) ✅
  - Decision:
    - Keep Phase 20 raw-geometry ticker-pool production contract and realign tests to that contract.
    - Upgrade GREEN allocation from equal-weight to conviction-score softmax sizing with configurable temperature (`tau`, default `1.0`).
  - Implementation:
    - `tests/test_ticker_pool.py`:
      - removed legacy matrix/z-score/anchor-centroid expectations,
      - replaced with raw-geometry contract assertions (score formula, telemetry constants, deterministic behavior).
    - `scripts/phase20_full_backtest.py`:
      - added `--softmax-temperature`,
      - applied GREEN-only softmax allocation:
        - `w_i = (1 - cash_pct) * softmax(conviction_score_i / tau)`,
      - kept AMBER/RED equal-weight logic unchanged.
    - Documentation updates:
      - appended formula notes in `docs/notes.md`,
      - appended lesson entry in `docs/lessonss.md`.
  - Evidence:
    - `pytest -q tests/test_ticker_pool.py` -> PASS (`15 passed`).
    - `pytest -q tests/test_company_scorecard.py` -> PASS (`20 passed`).
    - `pytest -q` -> BLOCKED at collection by missing optional deps:
      - `yfinance`, `psycopg2`.
    - Backtest run:
      - `python scripts/phase20_full_backtest.py --start-date 2020-01-01 --end-date 2024-12-31 --option-a-sector-specialist --allow-missing-returns --softmax-temperature 1.0 ... --output-summary-json data/processed/phase23_softmax_sizing_summary.json`
      - output generated at `data/processed/phase23_softmax_sizing_summary.json`.
  - Rationale:
    - restores test validity to active production behavior and adds an orthogonal sizing improvement without changing gate logic.
  - Open risks:
    - full-suite health remains environment-dependent until optional dependencies are installed in the active interpreter.
  - Rollback note:
    - revert `tests/test_ticker_pool.py` and `scripts/phase20_full_backtest.py` to prior commit snapshot and remove `--softmax-temperature` if softmax sizing is rejected.

Phase 23 Walk-Forward Temperature Optimization (2026-02-23): IS/OOS Softmax Calibration Wrapper (D-119) ✅
  - Decision:
    - Tune softmax temperature using a strict walk-forward protocol without OOS parameter search:
      - IS train window: `2020-01-01 -> 2022-12-31`,
      - OOS test window: `2023-01-01 -> 2024-12-31`.
    - Search space fixed to:
      - `T_values = [0.2, 0.5, 0.8, 1.0, 1.5, 2.0]`.
    - Selection metric fixed to IS Sharpe only.
  - Implementation:
    - Added `scripts/optimize_softmax_temperature.py`:
      - imports `scripts.phase20_full_backtest` and executes backtest logic via `phase20.main()`,
      - runs IS grid for all candidate `T`,
      - selects winner by max IS Sharpe (tie-break: higher IS CAGR, then lower `T`),
      - executes exactly one OOS run for winning `T`,
      - writes final artifact:
        - `data/processed/phase23_wfo_temperature_summary.json`.
  - Evidence:
    - `.venv\Scripts\python scripts/optimize_softmax_temperature.py` -> PASS.
    - Console result:
      - `Winning T (IS): 0.20`
      - `IS CAGR=-0.021843, IS Sharpe=-0.220303`
      - `OOS CAGR=0.372029, OOS Sharpe=1.362116, OOS MaxDD=-0.138161`
    - artifact:
      - `data/processed/phase23_wfo_temperature_summary.json`.
  - Rationale:
    - preserves PIT and WFO discipline while allowing bounded hyperparameter tuning on the new softmax sizing control.
  - Open risks:
    - IS results were tied across all tested temperatures in this run, indicating low sensitivity in current IS sample under present gates/universe.
  - Rollback note:
    - remove `scripts/optimize_softmax_temperature.py` and associated `phase23_wfo_temperature*` artifacts if PM rejects the WFO wrapper workflow.

Phase 23 Institutional Risk Overlay + Starvation Fix (2026-02-23): Bounded Continuity + Softmax Caps (D-120) ✅
  - Decision:
    - Restore bounded continuity fill for core bitemporal fundamentals to reduce off-cycle starvation.
    - Add institutional concentration controls to softmax sizing:
      - minimum breadth guard (`N < 4 -> all cash`),
      - max single-name position cap (`25%`) with proportional capped-redistribution.
  - Implementation:
    - `strategies/company_scorecard.py`:
      - restored grouped `ffill(limit=120)` for:
        - `q_tot`, `inv_vel_traj`, `op_lev`, `rev_accel`, `CycleSetup`.
    - `scripts/phase20_full_backtest.py`:
      - added min-eligible guard and `cash_pct=1.0` stand-down path when eligible breadth is below `4`,
      - added capped redistribution helper enforcing `max_single_position=0.25` in GREEN softmax path.
    - `scripts/diagnostic_softmax_weights.py`:
      - single-day PM diagnostic output now emits hard-gate universe and capped softmax allocations for `T=0.2` and `T=2.0`.
  - Evidence:
    - `.venv\Scripts\python scripts/diagnostic_softmax_weights.py` -> PASS.
      - closest valid day to requested target reported `Eligible Count = 5`,
      - `T=0.2` max reported weight `= 0.25` (cap respected),
      - NaN/Inf checks `false`.
    - `.venv\Scripts\python -m pytest -q` -> PASS.
  - Rationale:
    - prevents concentrated one-name exposures under sparse eligible sets while keeping continuity fill bounded in time.
  - Open risks:
    - IS feature coverage in this workspace starts at `2022-02-16`, so requested `2021-06-01` diagnostics map to closest available 2022 date.
  - Rollback note:
    - revert edits in `strategies/company_scorecard.py`, `scripts/phase20_full_backtest.py`, and `scripts/diagnostic_softmax_weights.py`.

Phase 23 Wrap Freeze (2026-02-23): Manifest Snapshot + Deterministic Restore (D-121) ✅
  - Decision:
    - Close Phase 23 with a no-git-safe freeze so strategy code and top backtest artifacts are explicitly revertible.
    - Preserve best-result lineage directly in snapshot metadata to avoid losing benchmark references during Orbis pivot.
  - Implementation:
    - Added freeze pack utility:
      - `scripts/phase23_freeze_pack.py`
      - creates snapshot under `data/processed/phase23_freeze/<snapshot_id>/`
      - writes SHA256 manifest + best-result ranking table.
    - Added restore utility:
      - `scripts/phase23_restore_from_freeze.py`
      - restores files from manifest, supports `--dry-run` and `--code-only`.
    - Published latest pointer:
      - `data/processed/phase23_freeze_latest.json`.
  - Evidence:
    - `.venv\Scripts\python scripts/phase23_freeze_pack.py --top-results-limit 12` -> PASS.
    - `.venv\Scripts\python scripts/phase23_restore_from_freeze.py --dry-run --code-only` -> PASS.
    - Snapshot created:
      - `data/processed/phase23_freeze/phase23_freeze_20260223_131534Z/manifest.json`.
    - Top preserved result in manifest:
      - `data/processed/phase23_softmax_sizing_summary.json` (`CAGR=0.205618`, `Sharpe=0.972964`, `MaxDD=-0.146706`).
  - Rationale:
    - phase transition to alternative-data engineering requires immutable rollback anchors for strategy stability.
  - Open risks:
    - restore process is filesystem-based and must be executed intentionally; no automatic rollback trigger exists.
  - Rollback note:
    - remove `scripts/phase23_freeze_pack.py`, `scripts/phase23_restore_from_freeze.py`, and `data/processed/phase23_freeze*` artifacts if freeze workflow is superseded.

Phase 25B Osiris Pivot (2026-02-24): Global Hardware Proxy Validated and Frozen (D-122) ✅
  - Decision:
    - Pivot alternative-data macro source from private `bvd_orbis` to public `bvd_osiris` due schema-access constraints.
    - Lock a production-grade global hardware supply-chain proxy from Osiris with PIT-safe lagging.
    - Treat positive IC on turnover as semantically consistent with the original inventory-bloat hypothesis:
      - high turnover = healthy sell-through = bullish,
      - low turnover = inventory glut = bearish.
  - Implementation:
    - Access probe and schema mapping:
      - `scripts/test_bvd_access.py`
      - `scripts/map_osiris.py`
    - Osiris extraction and aggregation:
      - `data/osiris_loader.py`
      - outputs:
        - `data/processed/osiris_global_hardware_daily.parquet`
        - `data/processed/osiris_regional_hardware_daily.parquet`
    - Daily PIT alignment and IC validation:
      - `scripts/align_osiris_macro.py`
      - output:
        - `data/processed/osiris_aligned_macro.parquet`
  - Evidence:
    - Access probe:
      - `bvd_osiris` OPEN,
      - `bvd_amadeus_trial` OPEN.
    - Extraction:
      - `8022` unique hardware companies.
    - Validation:
      - Spearman IC (Osiris z-score vs QQQ 60d forward returns) = `+0.087636`,
      - p-value = `1.18113e-05`,
      - aligned observations = `2492`.
  - Rationale:
    - preserves Phase 25 objective (global supply-chain leading signal) without waiting on private-dataset entitlement fixes.
  - Open risks:
    - sparse final-period coverage can make tail behavior noisy; monitor company-count floor in ongoing runs.
    - signal currently validated on QQQ only; cross-asset robustness remains to be tested.
  - Rollback note:
    - remove `data/osiris_loader.py`, `scripts/align_osiris_macro.py`, and generated `osiris_*` artifacts if this pivot is superseded by restored private-dataset access.

Execution Guardrails Hardening (2026-02-26): P0-2 Safety Controls for Non-TTY + Payload Integrity (D-123) ✅
  - Decision:
    - Fail closed for non-interactive execution sessions unless explicitly confirmed.
    - Replace assertion-based runtime risk checks in execution payload generation with explicit validation exceptions.
    - Add deterministic batch/idempotency metadata and duplicate-symbol protections in the order path.
  - Implementation:
    - Added execution confirmation guard:
      - `execution/confirmation.py`
      - policy: non-interactive sessions require `TZ_EXECUTION_CONFIRM=YES`.
    - Updated console flow:
      - `main_console.py`
      - removed auto-YES behavior for non-TTY runs.
    - Hardened payload generator:
      - `scripts/execution_bridge.py`
      - required-column validation, deterministic ticker dedupe/sort, max-order guard, explicit leverage checks, atomic payload writes, webhook timeout/status handling.
    - Hardened rebalancer path:
      - `execution/rebalancer.py`
      - non-negative/finite weight validation, max-gross guard, rounded quantity sizing, duplicate-symbol rejection, optional dry-run execution.
    - Hardened broker submit path:
      - `execution/broker_api.py`
      - side/qty/symbol validation and optional `client_order_id` pass-through.
    - Added unit tests:
      - `tests/test_execution_controls.py`.
  - Evidence:
    - `.venv\Scripts\python -m py_compile execution\confirmation.py main_console.py scripts\execution_bridge.py execution\rebalancer.py execution\broker_api.py tests\test_execution_controls.py` -> PASS.
    - `.venv\Scripts\python -m pytest tests\test_execution_controls.py -q` -> PASS (`8 passed`).
  - Rationale:
    - reduces chance of accidental live-order generation in headless/automated contexts and makes risk failures explicit and auditable at runtime.
  - Open risks:
    - legacy orchestrator flows outside `main_console.py` still need explicit harmonization to the same confirmation contract.
    - this round does not yet add integration tests against live broker adapters.
  - Rollback note:
    - revert `execution/confirmation.py`, `main_console.py`, `scripts/execution_bridge.py`, `execution/rebalancer.py`, `execution/broker_api.py`, and `tests/test_execution_controls.py`.

Dependency Unification + Control-Plane Lock (2026-02-26): P1 Environment Determinism (D-124) ✅
  - Decision:
    - Promote `pyproject.toml` dependency set as canonical and mirror it in `requirements.txt` in the same change.
    - Enforce `.venv\Scripts\python` execution path in operational runbooks/governance commands.
    - Redirect pytest cache to writable in-venv path to avoid root cache ACL failures.
  - Implementation:
    - Manifest lock:
      - `pyproject.toml`
      - `requirements.txt` (exact mirror of runtime + `pytest` dev dependency)
      - added/locked `alpaca-trade-api`, harmonized `yfinance`, aligned pinned versions.
    - Python runtime compatibility guard:
      - updated `requires-python` to `>=3.12,<3.15` to match project 3.12+ policy while avoiding single-minor pin brittleness.
    - Pytest cache control-plane hardening:
      - `pyproject.toml` -> `[tool.pytest.ini_options].cache_dir = ".venv/.pytest_cache"`.
    - Runbook/governance command normalization:
      - `docs/runbook_ops.md` (all core data/test commands now `.venv\Scripts\python ...`)
      - `AGENTS.md` verification/validator commands now explicitly `.venv\Scripts\python ...`.
  - Evidence:
    - `.venv\Scripts\python -m py_compile scripts/phase20_full_backtest.py tests/test_phase20_macro_gates_consumption.py` -> PASS.
    - `.venv\Scripts\python -m pytest -q tests/test_phase20_macro_gates_consumption.py tests/test_phase20_full_backtest_loader.py tests/test_regime_manager.py` -> PASS (`7 passed`).
    - `.venv\Scripts\python -m pytest -q tests/test_execution_controls.py` -> PASS (`8 passed`).
    - System-python reproducibility failure remains documented and is intentionally mitigated by venv-only command policy:
      - `python -m pytest -q tests/test_execution_controls.py` -> FAIL (`ModuleNotFoundError: alpaca_trade_api`).
  - Rationale:
    - removes dependency ambiguity between installer entry points and prevents false-negative test failures from shell interpreter drift.
  - Open risks:
    - historical docs/artifacts may still contain legacy bare `python` command examples outside active runbook/governance paths.
    - existing root `.pytest_cache` ACL artifact cannot be removed in this session; pytest now bypasses it via in-venv cache_dir.
  - Rollback note:
    - revert `pyproject.toml`, `requirements.txt`, `docs/runbook_ops.md`, and `AGENTS.md` if this lock policy is rejected.

Control-Plane Test Coverage (2026-02-26): P1 Orchestrator Regression Guardrails (D-125) ✅
  - Decision:
    - Add direct, deterministic tests for both execution orchestrators:
      - `main_console.py` interactive/non-interactive execution control path.
      - `main_bot_orchestrator.py` subprocess and scheduler control path.
  - Implementation:
    - Added `tests/test_main_console.py`:
      - kill-switch `STOP_TRADING` exit behavior.
      - manual-input behavior for TTY/non-TTY branches.
      - main flow coverage:
        - empty scan fail-fast,
        - non-interactive no-override abort path,
        - confirmed payload generation/save/notify path,
        - payload guardrail exception path.
    - Added `tests/test_main_bot_orchestrator.py`:
      - `run_scanners()` subprocess call contract (both scanners invoked with expected args).
      - stderr-to-logger behavior.
      - exception tolerance (first scanner failure does not prevent second scanner attempt).
      - `main()` scheduling contract (`friday 15:55`) + immediate diagnostic call + keyboard-interrupt disarm path.
  - Evidence:
    - `.venv\Scripts\python -m py_compile main_console.py main_bot_orchestrator.py tests/test_main_console.py tests/test_main_bot_orchestrator.py` -> PASS.
    - `.venv\Scripts\python -m pytest -q tests/test_main_console.py tests/test_main_bot_orchestrator.py` -> PASS (`11 passed`).
    - `.venv\Scripts\python -m pytest -q tests/test_execution_controls.py` -> PASS (`8 passed`).
  - Rationale:
    - execution orchestration is a control-plane risk path; direct unit coverage lowers regression risk before structural P2 decoupling.
  - Open risks:
    - tests are unit-level with monkeypatched seams; end-to-end broker integration remains out of scope for this round.
  - Rollback note:
    - remove `tests/test_main_console.py` and `tests/test_main_bot_orchestrator.py` if coverage scope is redefined.

P2 First Slice (2026-02-26): App Thin-Layer Decoupling via Service Boundaries (D-126) ✅
  - Decision:
    - Move heavy data-loading and control-plane decision logic out of `app.py` into dedicated service modules.
    - Keep `app.py` responsible for Streamlit rendering and UI action wiring only.
  - Implementation:
    - Added data service:
      - `data/dashboard_data_loader.py`
      - exported `load_dashboard_data(...)` (formerly inlined in `app.py::load_data`).
      - includes universe resolution, batched DuckDB reads, macro/liquidity merge, fallback macro context, sector/industry enrichment, and earnings-calendar context assembly.
    - Added control-plane service:
      - `core/dashboard_control_plane.py`
      - watchlist I/O (`load_watchlist`, `get_watchlist_tickers`, `save_user_selections`),
      - stale-date policy (`is_data_stale`),
      - auto-update decision contract (`plan_auto_update` + `AutoUpdatePlan`).
    - Refactored `app.py`:
      - `load_data(...)` is now a thin cached wrapper over `load_dashboard_data(...)`,
      - auto-update branch now uses `plan_auto_update(...)` instead of inlined session-state/date logic.
  - Test Coverage Added:
    - `tests/test_dashboard_control_plane.py`:
      - default/invalid watchlist handling,
      - deterministic watchlist save/load behavior,
      - weekday/weekend stale-date policy,
      - auto-update plan transitions (`reset`, `attempt`, `already-attempted`).
    - `tests/test_dashboard_data_loader.py`:
      - minimal TRI-path load contract with temporary parquet fixtures,
      - explicit `r3000_pit` missing-artifact fail-fast behavior.
  - Evidence:
    - `.venv\Scripts\python -m py_compile app.py core/dashboard_control_plane.py data/dashboard_data_loader.py tests/test_dashboard_control_plane.py tests/test_dashboard_data_loader.py` -> PASS.
    - `.venv\Scripts\python -m pytest -q tests/test_dashboard_control_plane.py tests/test_dashboard_data_loader.py tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py` -> PASS (`27 passed`).
  - Rationale:
    - shrinks non-UI blast radius in `app.py` and establishes testable service seams for subsequent P2 decomposition.
  - Open risks:
    - `app.py` still includes substantial non-trivial rendering/orchestration paths beyond this slice (optimizer/backtest tab logic).
    - Streamlit bare-import warnings are expected when importing `app.py` outside `streamlit run`.
  - Rollback note:
    - revert `app.py`, remove `core/dashboard_control_plane.py`, remove `data/dashboard_data_loader.py`, and remove the two new test files if this slice is rejected.

P1 Closeout Implementer Validation (2026-02-28): Evidence Lock for Execution/Data Safety Paths (D-137) ✅
  - Decision:
    - Close P1 verification only after explicit proof of:
      - strict missing-return failure semantics on executed exposure bars,
      - strict `client_order_id` propagation/idempotency wiring through rebalancer -> broker path,
      - fundamentals ingest checkpoint/resume controls and mismatch-policy behavior.
    - Publish docs-as-code evidence links in runbook/notes/lessons/SAW skeleton in the same round.
  - Implementation:
    - Verified strict missing-return semantics in simulation kernel:
      - `core/engine.py` (`strict_missing_returns`, executed-exposure mask and fail-fast runtime error).
      - script wiring preserves same semantics (`allow_missing_returns=False` maps to strict mode).
    - Verified strict idempotency wiring:
      - deterministic fallback `client_order_id` generation in `execution/rebalancer.py`,
      - explicit pass-through and failure-recovery lookup by `client_order_id` in `execution/broker_api.py`.
    - Verified fundamentals checkpoint/resume:
      - stage machine + mismatch policy + checkpoint artifact lifecycle in `data/fundamentals_updater.py`,
      - resume/reset/error-path regression coverage in `tests/test_fundamentals_updater_checkpoint.py`.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_engine.py tests/test_execution_controls.py tests/test_fundamentals_updater_checkpoint.py -q` -> PASS (`31 passed`).
    - Documentation updates:
      - `docs/runbook_ops.md`
      - `docs/notes.md`
      - `docs/lessonss.md`
      - `docs/saw_reports/saw_p1_closeout_impl_validation_skeleton.md`
  - Rationale:
    - converts distributed P1 hardening into a single auditable closure packet with reproducible commands and source-level proof.
  - Open risks:
    - this round is evidence-focused; it does not execute live broker integration or full phase-end runtime smoke.
  - Rollback note:
    - revert the docs-only artifacts above if governance format requires revision; no code-path rollback is needed for this round.

P1 Reconciliation Patch Set (2026-02-28): Fail-Closed Integrity Hardening (D-138) ✅
  - Decision:
    - Resolve all in-scope High findings from independent SAW re-check before closure.
    - Keep unresolved inherited performance debt in `Open Risks` with owner/target milestone.
  - Implementation:
    - Execution idempotency hardening:
      - reject duplicate `client_order_id` in a single submit batch,
      - reject blank `client_order_id` at broker submit boundary,
      - require recovered order to match intended `symbol/side/qty`; otherwise fail closed with `recovery_mismatch`.
    - Fundamentals checkpoint hardening:
      - semantic metadata validation (`version`, `rows_in_partial`, `tickers_with_data`, `stage`) routed through checkpoint mismatch policy,
      - checkpoint-row integrity validation (target ticker scope + positive numeric `permno`) before resume/write,
      - freeze/re-apply `permno_map` on checkpoint resume to prevent ticker-map drift during `final_write`.
    - Regression coverage hardening:
      - added wrapper-level strict/permissive executed-exposure tests across Phase20/RegimeFidelity/Phase21,
      - added Phase20 CLI default guard test (`allow_missing_returns=False` default).
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_execution_controls.py tests/test_fundamentals_updater_checkpoint.py tests/test_missing_returns_cli_defaults.py tests/test_missing_returns_execution_masks.py tests/test_engine.py tests/test_day5_ablation_report.py tests/test_day6_walkforward_validation.py tests/test_updater_parallel.py tests/test_phase20_full_backtest_loader.py tests/test_phase20_macro_gates_consumption.py tests/test_main_console.py tests/test_main_bot_orchestrator.py -q` -> PASS (`87 passed`).
    - Reviewer B re-check: no unresolved in-scope Critical/High in execution scope.
    - Reviewer C re-check: prior in-scope High checkpoint integrity findings closed; inherited performance mediums remain.
  - Rationale:
    - blocks false-positive order recovery and silent checkpoint corruption while preserving strict fail-closed defaults under fault conditions.
  - Open risks:
    - inherited High: orchestrator-level submit/recovery E2E integration proof is pending in next milestone,
    - inherited Medium: checkpoint write cadence and full-history merge scale costs remain.
  - Rollback note:
    - revert `execution/rebalancer.py`, `execution/broker_api.py`, `data/fundamentals_updater.py`, and related new tests if this reconciliation strategy is rejected.

P2 Auto-Backtest Infrastructure UI (2026-02-28): Lab/Backtest Decoupling + JSON Control Plane (D-139) ✅
  - Decision:
    - Extract Lab/Backtest rendering from monolithic `app.py` into a dedicated view module.
    - Add a dedicated control-plane service for Lab/Backtest config normalization and JSON cache state transitions.
    - Keep simulation execution behavior unchanged (manual run trigger, same strategy/engine path).
  - Implementation:
    - Added `core/auto_backtest_control_plane.py`:
      - typed dataclasses for config/cache/plan contracts,
      - deterministic normalization + fingerprint/run-key helpers,
      - fail-closed cache loading (with explicit reset policy),
      - explicit cost-unit contract (`rate` vs `bps`) for unambiguous transaction-cost normalization,
      - strict cache payload validation for schema version and boolean state fields,
      - start/finish state transitions,
      - atomic cache persist (`tmp -> os.replace`) with bounded `PermissionError` retry.
    - Added `views/auto_backtest_view.py`:
      - migrated the Lab/Backtest controls, charts, and metrics from `app.py`,
      - wired cache load + normalization + start/finish/failure state persistence,
      - enforced fail-closed run start (abort simulation when start-state cache write fails),
      - enforced explicit operator reset on corrupted/unreadable cache payloads.
    - Updated `app.py`:
      - Lab/Backtest route now calls `render_auto_backtest_view(...)`,
      - removed no-longer-used local imports tied to inline Lab logic.
    - Added tests:
      - `tests/test_auto_backtest_control_plane.py` for normalization, fail-closed cache load, planner gating, transition semantics, schema/field validation, and atomic persist behavior.
      - `tests/test_auto_backtest_view.py` for view-to-control-plane bps conversion seam coverage.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_auto_backtest_control_plane.py tests/test_auto_backtest_view.py` -> PASS (`8 passed`).
    - `.venv\Scripts\python -m pytest -q tests/test_dashboard_control_plane.py tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py` -> PASS (`38 passed`).
    - `.venv\Scripts\python -m py_compile core/auto_backtest_control_plane.py views/auto_backtest_view.py app.py` -> PASS.
  - Rationale:
    - reduces `app.py` coupling and establishes a testable control seam for future Auto-Backtest orchestration without touching broker/execution safety boundaries.
  - Open risks:
    - runtime observability for cache-state transitions is currently local/UI scoped (no orchestrator E2E telemetry yet),
    - non-blocking dependency warning persists from `pandas_datareader` deprecation path.
  - Rollback note:
    - remove `core/auto_backtest_control_plane.py`, remove `views/auto_backtest_view.py`, revert `app.py` route wiring, and remove `tests/test_auto_backtest_control_plane.py`.

Phase 25 SAW Reconciliation (2026-02-28): Orchestrator E2E Idempotency Hard-Fail Closure (D-140) ✅
  - Decision:
    - Close all in-scope Critical/High findings from SAW reviewer passes before issuing Phase 25 verdict.
    - Keep orchestrator execution state fail-closed under partial/malformed downstream batch responses.
  - Implementation:
    - `main_bot_orchestrator.py` hardening:
      - preflight duplicate-symbol rejection before first submit attempt,
      - authoritative intent anchor uses original `pending_by_cid[cid]` payload (not downstream row echo),
      - per-attempt expected-vs-observed CID reconciliation,
      - unresolved missing CIDs fail closed as `batch_result_missing`,
      - retryable faults at max attempts terminalize as `retry_exhausted`,
      - non-dict `result` rows are ignored and routed through missing-CID reconciliation.
    - `tests/test_main_bot_orchestrator.py` expansion:
      - already-exists mismatch terminal-fail behavior,
      - retry-exhausted and non-retryable terminal paths,
      - partial batch row retry/no-silent-drop proof,
      - persistent missing row fail-closed proof,
      - duplicate-symbol preflight rejection,
      - malformed row (`order=dict + result=non-dict`) fail-closed proof,
      - recovery anchor to original pending intent under downstream row-order drift.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py tests/test_main_console.py tests/test_execution_controls.py` -> PASS (`54 passed`).
    - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py` -> PASS (`16 passed`).
    - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
    - Final SAW reviewer rechecks:
      - Reviewer A: PASS (no in-scope Critical/High),
      - Reviewer B: PASS (no in-scope Critical/High),
      - Reviewer C: PASS (no in-scope Critical/High).
  - Rationale:
    - enforces deterministic execution accounting across network partitions and adapter-shape drift while preserving strict paper-lock boundaries.
  - Open risks:
    - medium: subprocess timeout currently hard-stops direct child but does not yet enforce process-tree termination semantics.
    - medium: CID fallback remains runtime-date dependent when both `trade_day` and explicit `client_order_id` are absent.
  - Rollback note:
    - revert `main_bot_orchestrator.py` and newly added `tests/test_main_bot_orchestrator.py` scenarios if this reconciliation policy is rejected.

Phase 26 Runtime Hardening Debt Burn-Down (2026-02-28): Process Tree + Seed Gate + Entrypoint Wiring (D-141) ✅
  - Decision:
    - close accepted medium debt from the Phase 25 ledger by hardening runtime orchestration behavior and entrypoint contracts.
    - enforce explicit fail-closed handling for malformed batch container/schema responses from downstream execution adapters.
  - Implementation:
    - scanner runtime hardening in `main_bot_orchestrator.py`:
      - process-group/session aware spawn path,
      - explicit process-tree termination on timeout with Windows `taskkill` return-code validation,
      - scheduler loop exception containment (log-and-continue behavior).
    - execution boundary hardening in `main_bot_orchestrator.py`:
      - canonical seed gate requires `client_order_id` or `trade_day`,
      - null-like CID normalization (`None`/`null`/`nan` treated as missing),
      - non-list `batch_results` guarded as empty and reconciled fail-closed,
      - dict-shaped `result` rows missing `ok` treated as malformed/unobserved.
    - outer-loop wiring:
      - `scripts/test_rebalance.py` now routes submission through `execute_orders_with_idempotent_retry(...)`,
      - seeds `trade_day` before submit and exits non-zero if any order fails.
    - regression coverage:
      - expanded `tests/test_main_bot_orchestrator.py`,
      - added `tests/test_test_rebalance_script.py`.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py` -> PASS.
    - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py scripts/test_rebalance.py tests/test_test_rebalance_script.py` -> PASS.
    - Final SAW rechecks:
      - Implementer PASS,
      - Reviewer A PASS (no in-scope Critical/High),
      - Reviewer B PASS (no in-scope Critical/High),
      - Reviewer C PASS (no in-scope Critical/High).
  - Rationale:
    - prevents fail-dead runtime behavior and strengthens deterministic, auditable order lifecycle handling under malformed/downstream fault conditions without relaxing paper-lock controls.
  - Open risks:
    - medium: broader production entrypoint coverage beyond `scripts/test_rebalance.py` remains follow-up integration scope.
  - Rollback note:
    - revert `main_bot_orchestrator.py`, `scripts/test_rebalance.py`, `tests/test_main_bot_orchestrator.py`, and remove `tests/test_test_rebalance_script.py` if this runtime contract bundle is rejected.

Phase 27 Conditional-Block Remediation (2026-02-28): Strict OK Typing + Terminal Kill Confirmation + Universal Success Parity (D-142) ✅
  - Decision:
    - Clear AMBER conditional block by resolving newly surfaced High/Medium fail-closed gaps in orchestrator execution semantics.
    - Preserve paper-trading lock and prohibit feature/UI/strategy scope changes in this round.
  - Implementation:
    - `main_bot_orchestrator.py` hardening:
      - strict boolean gate for downstream `result.ok` (`non-bool => unobserved`),
      - universal parity validation on all `ok=True` rows,
      - sparse success payload parity fallback via `row.order` fields (`symbol/side/qty`),
      - strict qty typing:
        - reject boolean `qty` at request normalization boundary,
        - reject boolean `qty` in recovery parity matcher,
      - terminate-confirmed-or-fail timeout contract preserved with terminal `ScannerTerminationError`,
      - startup diagnostic containment aligned with scheduler behavior for non-terminal exceptions.
    - `scripts/test_rebalance.py`:
      - success accounting tightened to `ok is True` only.
    - `execution/rebalancer.py`:
      - acceptance logging path tightened to `ok is True` only.
    - `tests/test_main_bot_orchestrator.py` expansion:
      - startup/scheduled terminal re-raise checks,
      - duplicate CID / invalid max_attempts / non-dict order / empty-order guards,
      - non-boolean `ok` fail-closed checks,
      - sparse `ok=True` fallback acceptance check,
      - bool-qty input and bool-qty payload rejection checks.
    - `tests/test_test_rebalance_script.py` expansion:
      - non-boolean `ok` treated as failure,
      - pre-seeded `trade_day` preservation check.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py` -> PASS (`78 passed`).
    - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py execution/rebalancer.py scripts/test_rebalance.py tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py` -> PASS.
    - SAW reviewer rechecks after reconciliation:
      - Implementer PASS,
      - Reviewer A PASS (no in-scope Critical/High),
      - Reviewer B PASS (no in-scope Critical/High),
      - Reviewer C PASS (no in-scope Critical/High).
  - Rationale:
    - prevents silent false-positive order acceptance from adapter/schema drift,
    - enforces terminal control-plane behavior when timeout termination cannot be confirmed,
    - preserves deterministic execution state reconciliation under sparse but valid success payloads.
  - Open risks:
    - medium: process-tree confirmation still relies on parent liveness checks (descendant-level enumeration is not directly validated),
    - medium: POSIX kill-path and Windows fallback-after-success branch remain lightly unit-tested,
    - medium (inherited): broader production entrypoint propagation beyond current remediated seams remains follow-up integration scope.
  - Rollback note:
    - revert `main_bot_orchestrator.py`, `execution/rebalancer.py`, `scripts/test_rebalance.py`, `tests/test_main_bot_orchestrator.py`, `tests/test_test_rebalance_script.py`, and associated Phase 27 docs if this remediation strategy is rejected.

Phase 28 Entrypoint Contract Remediation (2026-02-28): Atomic Local-Submit Gate + CID Lineage + Strict Parity (D-143) ✅
  - Decision:
    - Execute approved Step 1 remediation bundle for broader production entrypoint wiring.
    - Enforce fail-closed, all-or-nothing local-submit payload handling and strict contract lineage from payload generation through broker submit/recovery.
  - Implementation:
    - `main_console.py`:
      - added strict atomic payload row validator (`execution_orders` must fully conform or batch aborts),
      - required per-row contract fields:
        - `ticker/symbol`, `target_weight`, `action|side`, `order_type`, `limit_price`, `client_order_id`, `trade_day`,
      - added semantic `trade_day` validation (`YYYYMMDD` + calendar-valid date),
      - enforced batch-size cap at helper entry and symbol-set parity against calculated orders,
      - seeded and validated strict parity on `symbol/side/qty/order_type/limit_price/client_order_id`,
      - hardened helper result reconciliation (unknown/duplicate/missing CID rows fail closed),
      - tightened integer guard to reject non-integral quantities (no truncation).
    - `execution/rebalancer.py`:
      - extended submit path to pass limit intent (`order_type`, `limit_price`) for limit orders,
      - validated limit-price numeric positivity and preserved backward-compatible market submission semantics.
    - `execution/broker_api.py`:
      - extended submit validation for market/limit intent with strict limit-price checks,
      - rejected boolean `qty` at submit boundary,
      - upgraded recovery intent match to enforce `symbol/side/qty/order_type/client_order_id`,
      - enforced strict market recovery null-limit semantics and preserved raw recovered `limit_price` for consistent matching.
    - `main_bot_orchestrator.py`:
      - normalized and matched recovery parity with `order_type/limit_price` checks in addition to existing idempotency controls.
    - test expansion:
      - `tests/test_main_console.py`, `tests/test_execution_controls.py`, `tests/test_main_bot_orchestrator.py` updated with negative matrix and recovery-semantics regressions.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_main_console.py tests/test_execution_controls.py tests/test_main_bot_orchestrator.py -q` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py` -> PASS (`109 passed in 5.03s`).
    - `.venv\Scripts\python -m py_compile main_console.py main_bot_orchestrator.py execution/broker_api.py execution/rebalancer.py tests/test_main_console.py tests/test_execution_controls.py tests/test_main_bot_orchestrator.py` -> PASS.
    - Final SAW reviewer clearance:
      - Reviewer A: PASS,
      - Reviewer B: PASS (prior null-semantics BLOCK cleared),
      - Reviewer C: PASS.
  - Rationale:
    - eliminates partial-execution corruption risk from malformed payload rows,
    - restores deterministic CID traceability at production entrypoint seam,
    - enforces strict payload intent parity before accepting execution/recovery outcomes.
  - Open risks:
    - low: unknown broker null sentinels for market `limit_price` beyond `{None, "", "none", "null"}` intentionally fail closed as `recovery_mismatch`.
    - low: recovery-mismatch permutation matrix can be expanded for side/qty/type/limit variants.
  - Rollback note:
    - revert `main_console.py`, `execution/rebalancer.py`, `execution/broker_api.py`, `main_bot_orchestrator.py`, `tests/test_main_console.py`, `tests/test_execution_controls.py`, `tests/test_main_bot_orchestrator.py`, and associated Phase 28 docs if this remediation strategy is rejected.

DevSecOps Stream Remediation (2026-03-01): Secret Scrub + Runtime Egress Gate + HMAC Rotation Contract (D-144) ✅
  - Decision:
    - execute a fail-closed DevSecOps hardening bundle for credential handling and outbound boundary control.
  - Implementation:
    - hardcoded credential purge:
      - removed WRDS default credentials from:
        - `scripts/ingest_compustat_sdm.py`
        - `scripts/ingest_ff_factors.py`
        - `scripts/ingest_frb_macro.py`
      - removed hardcoded FMP key literals from legacy diagnostics:
        - `logs/diagnostics/root_legacy/_diag_fmp_api.py`
        - `logs/diagnostics/root_legacy/_diag_fmp_stable.py`
      - also scrubbed legacy WRDS diagnostic helpers to env-only auth:
        - `logs/diagnostics/root_legacy/_probe_wrds_schema.py`
        - `logs/diagnostics/root_legacy/_diag_wrds.py`
        - `logs/diagnostics/root_legacy/_probe_step0.py`
        - `logs/diagnostics/root_legacy/_probe_step0b.py`
        - `logs/diagnostics/root_legacy/_probe_3pillar_schema.py`
    - cache/artifact secret redaction:
      - added URL-secret redaction for FMP cache load/save path in `scripts/ingest_fmp_estimates.py`,
      - prevented `apikey` persistence in new cache writes,
      - sanitized existing cached artifacts:
        - `data/raw/fmp_cache/AMD.json`
        - `data/raw/fmp_cache/INTC.json`
        - `data/raw/fmp_cache/NVDA.json`
    - secret ingress hardening:
      - removed broker `.env` auto-load path in `execution/broker_api.py` (env-injected secrets only).
    - deny-by-default egress:
      - introduced centralized policy in `core/security_policy.py`,
      - enforced allowlisted egress URL check in:
        - `execution/broker_api.py` (broker base URL),
        - `scripts/execution_bridge.py` (webhook path),
      - guarded `scripts/high_freq_data.py` with policy checks to block non-allowlisted public endpoints.
    - HMAC signing-key lifecycle controls:
      - added key-version and activation timestamp contract with legal-hold exception in `core/security_policy.py`,
      - enforced on payload generation via `scripts/execution_bridge.py`.
  - Evidence:
    - targeted tests:
      - `.venv\Scripts\python -m pytest tests/test_security_policy.py tests/test_ingest_fmp_estimates.py tests/test_execution_controls.py -q`
    - secret scrub verification:
      - regex scans show no remaining hardcoded WRDS/FMP literals in active scripts.
  - Rationale:
    - removes embedded credentials from code and cached artifacts,
    - preserves forensic traceability through explicit `hmac_key_version`,
    - enforces legal-hold exception path for rotation governance,
    - reduces exfiltration risk by default-deny outbound controls.
  - Open risks:
    - legacy scripts that depend on non-allowlisted public data endpoints now degrade to guarded fallback behavior unless allowlist policy is expanded intentionally.
    - credential provider-side rotation remains an operator action outside code scope.
  - Rollback note:
    - revert modified files in this decision block and re-run targeted tests if this policy hardening is rejected.

DevSecOps SAW Reconciliation (2026-03-01): TLS Lock + HMAC Future-Skew Guard + Post-Submit Notify Degrade (D-146) ✅
  - Decision:
    - close SAW High findings by tightening egress transport semantics, hardening HMAC timestamp validation, and separating pre-submit vs post-submit webhook failure handling.
  - Implementation:
    - `core/security_policy.py`:
      - enforced HTTPS-only egress by default (`http` blocked even for allowlisted hosts),
      - added localhost-only HTTP break-glass (`TZ_ALLOW_HTTP_EGRESS_LOCALHOST=YES`),
      - changed `TZ_ALLOWED_EGRESS_HOST_SUFFIXES` behavior to extend defaults unless explicit `TZ_ALLOWED_EGRESS_HOST_SUFFIXES_MODE=override`,
      - added fail-closed future timestamp guard for HMAC activation (`TZ_HMAC_MAX_FUTURE_SKEW_SECONDS`, default `300`).
    - `scripts/high_freq_data.py`:
      - replaced directional fallback constants with neutral degraded metrics (`val=0.0`, `degraded=true`) when egress is blocked or fetch fails.
    - `scripts/execution_bridge.py` + `main_console.py`:
      - kept payload-only webhook behavior fail-closed,
      - added post-submit degraded notify path (`[WATCHTOWER-DEGRADED]`) for transport failures after successful local submit.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_security_policy.py tests/test_high_freq_data.py tests/test_execution_controls.py tests/test_main_console.py`
    - added/updated regression cases:
      - HTTP egress block + localhost break-glass tests,
      - allowlist extension/override behavior tests,
      - HMAC future-skew fail-closed test,
      - post-submit webhook degrade vs payload-only fail-closed tests,
      - high-frequency neutral degraded fallback tests.
  - Rationale:
    - removes policy bypass paths (plaintext transport + future timestamp masking),
    - avoids operator-footgun outage from accidental allowlist replacement,
    - preserves post-trade execution continuity while still fail-closing pre-submit notification path.
  - Open risks:
    - degraded high-frequency metrics still require explicit UI/operator visibility follow-up to avoid silent quality drift.
    - provider-side credential rotation remains operator action outside code scope.
  - Rollback note:
    - revert `core/security_policy.py`, `scripts/high_freq_data.py`, `scripts/execution_bridge.py`, `main_console.py`, and associated tests/docs if reconciliation strategy is rejected.

DevSecOps Track 3 Follow-Through (2026-03-01): Data Health Badge + Malformed Payload Test Expansion (D-147) ✅
  - Decision:
    - close approved Track 3 follow-through items with binary in-memory Data Health UI signaling and expanded malformed FMP payload regression coverage.
  - Implementation:
    - `core/dashboard_control_plane.py`:
      - added `derive_hf_proxy_data_health` (binary health contract with per-signal detail),
      - added `ensure_payload_data_health` (legacy payload fallback derivation).
    - `dashboard.py`:
      - derives `data_health` from in-memory `proxy_data` at scan runtime and persists it in cache payload,
      - renders compact `Data Health` badge and expandable detail panel (`signal/status/reason/span`),
      - keeps legacy cache compatibility by deriving missing `data_health` on load.
    - `tests/test_ingest_fmp_estimates.py`:
      - added malformed payload negative-path tests for:
        - non-rate-limit dict payload (`ValueError`),
        - unexpected scalar payload (`ValueError`),
        - invalid JSON decode path (`JSONDecodeError`).
    - Reconciliation addendum (reviewer BLOCK -> PASS):
      - added `coerce_proxy_numeric` guards in dashboard proxy rendering paths to avoid non-finite/type drift,
      - forced empty-proxy health to fail closed (`DEGRADED`) for contract coherence,
      - hardened cache lifecycle with atomic JSON writes and guarded cache-load fallback,
      - guarded sparse signal detail rendering (`span` lookup fallback) to avoid dashboard runtime faults.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_dashboard_control_plane.py tests/test_ingest_fmp_estimates.py`
    - `.venv\Scripts\python -m py_compile dashboard.py core/dashboard_control_plane.py tests/test_dashboard_control_plane.py tests/test_ingest_fmp_estimates.py`
  - Rationale:
    - gives operators immediate binary visibility when any HF proxy signal is degraded,
    - prevents silent malformed-payload drift by locking non-rate-limit failure classes into regression gates.
  - Open risks:
    - low/medium: dashboard badge currently reports degraded ratio by signal count; downstream quantitative impact weighting by signal criticality remains future work.
  - Rollback note:
    - revert `dashboard.py`, `core/dashboard_control_plane.py`, `tests/test_dashboard_control_plane.py`, `tests/test_ingest_fmp_estimates.py` and rerun the evidence commands above.

Microstructure / Execution Quant Stream Activation (2026-03-01): Arrival Midpoint + Partial-Fill VWAP + Slippage/Latency Sink (D-145) ✅
  - Decision:
    - activate stream-5 execution-quant telemetry instrumentation without expanding into RiskOps/System/DevSec/Data ownership domains.
  - Implementation:
    - `execution/broker_api.py`:
      - added quote snapshot API (`get_latest_quote_snapshot`) with strict bid/ask midpoint extraction,
      - added submit-time telemetry (`submit_sent_ts`, `broker_ack_ts`) and order lifecycle enrichment,
      - added partial-fill extraction from broker `FILL` activities,
      - added deterministic fill summary (`fill_count`, `fill_qty`, `fill_notional`, `fill_vwap`, `first_fill_ts`, `last_fill_ts`).
    - `main_console.py`:
      - stamped `arrival_ts` at Sovereign_Command generation,
      - attached `arrival_bid_price`, `arrival_ask_price`, `arrival_price`, `arrival_quote_ts` per order,
      - integrated post-trade telemetry persistence after local submit,
      - fail-closed behavior when telemetry sink write fails.
    - `execution/microstructure.py`:
      - added deterministic execution-cost math and latency decomposition,
      - wrote order-level and fill-level telemetry to Parquet + DuckDB.
    - tests:
      - added `tests/test_execution_microstructure.py` for IS/slippage/latency math and sink persistence,
      - expanded `tests/test_execution_controls.py` for midpoint snapshot and partial-fill VWAP aggregation,
      - updated `tests/test_main_console.py` local-submit seam checks for telemetry integration.
  - Formula lock:
    - `arrival_price = (bid + ask) / 2`
    - `VWAP_fill = sum(price_i * qty_i) / sum(qty_i)`
    - `IS_buy = (VWAP_fill - arrival_price) * qty`
    - `IS_sell = (arrival_price - VWAP_fill) * qty`
    - `slippage_bps = (signed_delta / arrival_price) * 10,000`
  - Artifacts:
    - `data/processed/execution_microstructure.parquet`
    - `data/processed/execution_microstructure_fills.parquet`
    - `data/processed/execution_microstructure.duckdb`
  - Open risks:
    - broker activity feed availability can vary; fallback uses order snapshot fill fields when per-fill activity rows are unavailable.
    - venue metadata depends on upstream broker activity payload richness.
  - Rollback note:
    - revert `execution/broker_api.py`, `main_console.py`, `execution/microstructure.py`, and related stream-5 tests/docs if this telemetry model is rejected.

Release Engineering / MLOps Stream Activation (2026-03-01): Digest-Locked Artifacts + Deterministic Promotion/Rollback (D-146) ✅
  - Decision:
    - enforce digest-locked container artifact identity for releases and wire automatic N-1 rollback to startup diagnostics.
  - Implementation:
    - immutable artifact packaging:
      - added `Dockerfile` with pinned base image digest and deterministic runtime venv.
      - added `.dockerignore` to reduce mutable/non-runtime payload.
    - release metadata schema + governance:
      - added `core/release_metadata.py`:
        - digest-lock validators,
        - normalized release record/state schema,
        - release-bound UI cache fingerprint builder.
    - deterministic promotion/rollback controller:
      - added `scripts/release_controller.py`:
        - atomic metadata writes (`tmp -> fsync -> os.replace`),
        - candidate stage + probe + finalize state machine,
        - docker mode deployment with startup watch and automatic rollback to N-1 on startup failure,
        - metadata-only and external-probe modes for controlled operations.
    - UI cache binding to artifact hash:
      - updated `dashboard.py` to bind matrix-cache invalidation to:
        - schema version + `TZ_RELEASE_DIGEST` via `build_release_cache_fingerprint(...)`.
    - tests:
      - added `tests/test_release_controller.py` coverage for:
        - digest-lock validation,
        - promotion success path,
        - rollback path,
        - atomic write safety,
        - docker startup-probe rollback behavior,
        - release-cache fingerprint contract.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_release_controller.py -q` -> PASS.
    - `.venv\Scripts\python -m py_compile scripts/release_controller.py core/release_metadata.py dashboard.py` -> PASS.
  - Rationale:
    - removes mutable-tag ambiguity from release control,
    - links runtime UI cache state to deployed artifact identity,
    - enforces deterministic rollback path without human intervention for startup-fault deployments.
  - Open risks:
    - docker-mode rollback currently restores service container, not full external traffic-router semantics.
    - digest resolution in operator workflows depends on registry/push policies outside repository code.
  - 2026-03-01 hardening reconciliation (Area 4 in-scope):
    - added truthful rollback terminal state `rollback_failed` when rollback is not verified.
    - added lock owner-token semantics to prevent non-owner unlock races and unsafe stale-lock takeover.
    - added `--allow-external-probe-promote` acknowledgement gate to avoid accidental metadata promotion in external runtime mode.
    - updated release-controller tests for lock ownership, stale-lock behavior, rollback verification status, and distinct rollback-failed exit code.
  - Rollback note:
    - revert `Dockerfile`, `.dockerignore`, `scripts/release_controller.py`, `core/release_metadata.py`, `tests/test_release_controller.py`, and docs touched by D-146 if this stream is rejected.

RiskOps Stream 2 Reconciliation (2026-03-01): Authoritative Interceptor + Fail-Closed Context + Long-Only + Audit Fail-Stop (D-147) ✅
  - Decision:
    - lock Stream 2 risk controls as immutable fail-closed gates between `rebalancer` and broker submit, with authoritative risk inputs and deterministic block semantics.
  - Implementation:
    - `execution/risk_interceptor.py`:
      - added strict long-only projection guard (`reason_code=invalid_order_projection`),
      - changed context precedence to trusted-first:
        - prices: broker `get_latest_price` only,
        - sectors: broker -> portfolio -> order fallback,
        - VIX: broker -> portfolio -> order fallback,
        - volatility: broker -> portfolio -> order fallback,
      - made projection violations return explicit deterministic `BLOCK` decisions.
    - `execution/rebalancer.py` (already in Stream 2 scope):
      - preserves fail-closed default when broker risk context is unavailable,
      - removes executable bypass path for missing risk context (no runtime opt-out),
      - validates/normalizes the full batch before any submit side effects,
      - sequences sell orders before buys in `calculate_orders` output for rebalance runs,
      - normalizes/validates broker position symbols and rejects non-finite position quantities in `calculate_orders`,
      - commits projected risk state only after successful broker acceptance (`result["ok"] is True`),
      - applies conservative pending-order projection (buy-only pre-fill; do not credit pending sells),
      - enforces audit-write failure semantics via `risk_blocked_audit_failed` and batch fail-stop.
    - `tests/test_execution_controls.py`:
      - added regressions for:
        - missing-risk-context fail-closed default,
        - post-submit-only risk-state commit,
        - authoritative source anti-spoof checks (sector/VIX/volatility),
        - long-only oversell block,
        - audit persistence failure fail-stop behavior.
    - `tests/test_main_bot_orchestrator.py`:
      - upgraded minimal broker doubles to provide required risk context (`get_portfolio_state`, `get_latest_price`) so idempotent tests do not rely on bypasses.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_execution_controls.py tests/test_main_console.py tests/test_main_bot_orchestrator.py` -> PASS.
  - Rationale:
    - removes trust in upstream order-metadata for risk-critical inputs,
    - closes fail-open seams for missing context by default,
    - prevents partial batch side effects from late-row validation errors,
    - prevents inadvertent short drift in long-only mode,
    - hardens forensic reliability by failing closed on audit persistence errors.
  - Open risks:
    - test doubles without risk-context methods now fail closed by design and must be updated to include required context methods.
    - broker-side data quality (price/sector/vix/vol) remains a dependency outside repository control.
  - Rollback note:
    - revert `execution/risk_interceptor.py`, `execution/rebalancer.py`, `tests/test_execution_controls.py`, and `tests/test_main_bot_orchestrator.py` if this Stream 2 reconciliation is rejected.

Stream 5 Option 2 Production Patch (2026-03-01): Terminal-Unfilled Fail-Closed + Recovery Anchor Backfill + Drift-Safe Latency (D-148) ✅
  - Decision:
    - treat terminal unfilled submit outcomes as non-accepted, fail closed without retry thrash, and backfill latency anchors for recovered client-order-id payloads.
  - Implementation:
    - `execution/broker_api.py`:
      - added terminal-unfilled classifier (`canceled/cancelled/rejected/expired` + `fill_qty<=0`) and acceptance normalization to `ok=False` with `error=terminal_unfilled:<status>`,
      - added recovery/submit latency anchor backfill:
        - `submit_sent_ts := submitted_at || created_at || updated_at`,
        - `broker_ack_ts := updated_at || submitted_at || created_at`.
    - `main_bot_orchestrator.py`:
      - added terminal-unfilled fail-closed guard in retry loop before retry-token evaluation,
      - prevents retry thrash even when row error text includes retryable tokens.
    - `execution/microstructure.py`:
      - added latency-anchor resolver fallback from broker lifecycle timestamps when explicit submit/ack fields are absent,
      - clamped latency decomposition to non-negative values (`max(0, computed_ms)`).
    - tests:
      - `tests/test_execution_controls.py`:
        - added terminal-unfilled submit and terminal-unfilled recovery fail-closed tests,
        - added recovery anchor-backfill assertions.
      - `tests/test_main_bot_orchestrator.py`:
        - added non-thrashing terminal-unfilled retry guard regression.
      - `tests/test_execution_microstructure.py`:
        - added signed slippage assertions (negative favorable, zero neutral),
        - added recovery-anchor backfill + clock-drift latency clamp assertions.
  - Formula lock:
    - `terminal_unfilled := status in {canceled,cancelled,rejected,expired} AND fill_qty <= 0`
    - `latency_ms = max(0, (t_end - t_start) * 1000)`
    - `slippage_bps = (signed_delta / arrival_price) * 10,000`
  - Open risks:
    - broker status vocabulary outside known terminal set may require mapping expansion if new upstream enums are introduced.
  - Rollback note:
    - revert `execution/broker_api.py`, `main_bot_orchestrator.py`, `execution/microstructure.py`, and related test/doc updates if this patch is rejected.

Phase 31 Sovereign Execution Hardening (2026-03-01): Trust Boundary + Telemetry Durability + Semantic Contract Reconciliation (D-149) ✅
  - Decision:
    - lock fail-closed defaults for signed replay boundaries, local-submit telemetry durability, and semantic coercion paths.
  - Implementation:
    - `execution/signed_envelope.py`:
      - atomic cross-process replay check+append under file lock,
      - malformed ledger quarantine (`.malformed.jsonl`) and valid-line rewrite,
      - append durability (`flush + fsync`).
    - `execution/microstructure.py`:
      - deterministic spool UID and DuckDB idempotent insert anti-dup,
      - schema-invalid JSON quarantine and stale trailing-partial-line quarantine,
      - stale offset reset + bounded spool compaction,
      - parquet export cursor model and legacy single-file dedupe fallback,
      - spool/cursor atomic writes hardened with `fsync` semantics.
    - `main_console.py`:
      - bounded durability gate for local-submit telemetry flush before success/notify,
      - terminal-unfilled local acceptance check aligned with fail-closed contract.
    - `strategies/alpha_engine.py`:
      - snapshot contract validation + multi-day derived-field recompute,
      - safe boolean normalization for `trend_veto`,
      - numeric-stable candidate ranking.
    - `strategies/ticker_pool.py`:
      - runtime invariant checks (`ValueError`) replacing strip-able asserts,
      - malformed-date fail-fast,
      - deterministic string/boolean token normalization for weak-quality/style gates.
    - `core/dashboard_control_plane.py`:
      - atomic watchlist persistence (`tmp -> flush -> fsync -> os.replace`).
    - tests:
      - added `tests/test_signed_envelope_replay.py`,
      - expanded `tests/test_execution_microstructure.py`, `tests/test_main_console.py`,
      - expanded `tests/test_alpha_engine.py`, `tests/test_ticker_pool.py`, `tests/test_dashboard_control_plane.py`.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_auto_backtest_control_plane.py tests/test_dashboard_control_plane.py tests/test_ticker_pool.py tests/test_alpha_engine.py tests/test_engine.py tests/test_statistics.py tests/test_signed_envelope_replay.py` -> PASS.
    - `.venv\Scripts\python -m py_compile execution/signed_envelope.py execution/microstructure.py main_console.py strategies/alpha_engine.py strategies/ticker_pool.py core/dashboard_control_plane.py tests/test_signed_envelope_replay.py tests/test_execution_microstructure.py tests/test_alpha_engine.py tests/test_ticker_pool.py tests/test_dashboard_control_plane.py` -> PASS.
  - Rationale:
    - closes newly surfaced in-scope SAW Critical/High reliability gaps while preserving asynchronous execution-path performance.
  - Open risks:
    - cross-process spool lock discipline is still thread-level (medium),
    - replay lock wait path has no timeout budget (medium),
    - long-horizon DuckDB anti-join/count path can degrade flush throughput (medium),
    - `score_col` semantic no-op in current ticker ranking path (medium),
    - `plan_auto_update` null-date handling remains medium hardening follow-up.
  - Rollback note:
    - revert all D-149 touched code/docs/tests as one batch if this stream is rejected.

Stream 5 Option 2 SAW Reconciliation Round 2 (2026-03-01): Terminal-Partial Fail-Closed + Telemetry Fill-Row Consistency + Legacy Null-Key Dedupe Safety (D-150) ✅
  - Decision:
    - close remaining in-scope SAW Critical/High findings for Stream 5 Option 2 by hardening terminal partial-fill retry behavior, summary-only fill-row consistency, and legacy parquet null-key dedupe safety.
  - Implementation:
    - `main_bot_orchestrator.py`:
      - added terminal-status classifier and fail-closed branch for terminal partial-fill rows (`terminal_partial_fill:<status>`) to prevent retry thrash.
    - `execution/microstructure.py`:
      - added synthesized `summary_fallback` fill row when `fill_summary` is present but `partial_fills` is empty,
      - replaced legacy single-file parquet dedupe with null-safe per-key dedupe preserving rows where `_spool_record_uid`, `record_id`, or `uid` are null.
    - tests:
      - `tests/test_execution_controls.py`: added Alpaca v2 quote-field coverage (`bid_price`/`ask_price`),
      - `tests/test_main_bot_orchestrator.py`: added terminal partial-fill no-retry regression,
      - `tests/test_execution_microstructure.py`: added summary-only fill-row synthesis regression and null-key parquet dedupe regressions for `_spool_record_uid`, `record_id`, and `uid`.
  - Formula lock:
    - `terminal_partial_fail_closed := status in TERMINAL_STATUSES AND fill_qty > 0 => final(ok=False), non-retry`
    - `summary_fill_fallback_row := (partial_fills == []) AND (fill_count > 0) AND (fill_qty > 0) AND (fill_vwap > 0)`
    - `legacy_dedupe_keyed_only := dedupe(key) over rows with non-empty key; preserve rows with empty/null key`
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_controls.py tests/test_main_console.py tests/test_main_bot_orchestrator.py` -> PASS.
    - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py execution/microstructure.py tests/test_main_bot_orchestrator.py tests/test_execution_microstructure.py tests/test_execution_controls.py` -> PASS.
    - `docs/saw_reports/saw_stream5_option2_round2.md` -> `ClosureValidation: PASS`, `SAWBlockValidation: PASS`.
  - Open risks:
    - inherited out-of-scope contract risk remains in orchestrator sparse `ok=True` success fallback semantics (row-order fallback); requires separate policy decision before changing behavior.
  - Rollback note:
    - revert `main_bot_orchestrator.py`, `execution/microstructure.py`, `tests/test_main_bot_orchestrator.py`, `tests/test_execution_microstructure.py`, `tests/test_execution_controls.py`, and SAW/docs updates for D-150 if rejected.

Stream 5 Execution Quant Round 3 (2026-03-01): Adaptive Heartbeat Freshness + Baseline Runner Pack (D-200) ✅
  - Decision:
    - add deterministic adaptive heartbeat freshness telemetry from submit-to-ack latencies (rolling MAD + hard ceiling), plus dedicated backfill and slippage baseline runners.
  - Implementation:
    - `execution/microstructure.py`:
      - added heartbeat policy constants and evaluator:
        - `evaluate_heartbeat_freshness(...)`,
        - rolling robust stats (`median`, `MAD`, `robust_sigma`),
        - adaptive limit + bootstrap fallback + hard-ceiling block classification.
      - integrated heartbeat annotation into `build_execution_telemetry_rows(...)` with strict no-lookahead rolling history.
      - added cross-batch history bootstrap from sink:
        - `_load_recent_submit_to_ack_history_ms(...)`.
      - added reusable dataframe annotation helper:
        - `annotate_heartbeat_freshness_frame(...)`.
      - hardened atomic replace under transient Windows locks with bounded retry:
        - `_atomic_replace_with_retry(...)`.
      - reconciled runtime durability gate to fail closed when flush reports:
        - `last_flush_error != None`, or
        - `buffer_drop_count > 0`
        - in `wait_for_execution_microstructure_flush(...)`.
      - hardened sink schema drift path:
        - dynamic `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` from registered batch schema,
        - explicit insert-column projection to avoid `SELECT n.*` binder drift failures.
      - changed parquet export pagination ordering to append-stable query priority:
        - `ORDER BY rowid` (with deterministic fallbacks), preventing offset-skip under inter-batch appends.
    - `scripts/backfill_execution_latency.py`:
      - deterministic historical backfill runner for heartbeat fields,
      - outputs:
        - `data/processed/execution_microstructure_latency_backfill.parquet`,
        - `data/processed/execution_microstructure_latency_backfill_summary.json`.
    - `scripts/evaluate_execution_slippage_baseline.py`:
      - baseline signed slippage evaluator (summary + side/symbol tables),
      - outputs:
        - `data/processed/execution_slippage_baseline_summary.json`,
        - `data/processed/execution_slippage_baseline_by_side.csv`,
        - `data/processed/execution_slippage_baseline_by_symbol.csv`.
    - tests:
      - `tests/test_execution_microstructure.py`:
        - hard-ceiling block regression,
        - adaptive-threshold regime expansion regression,
        - row-level heartbeat column emission regression,
        - fail-closed wait regression for `last_flush_error`/`buffer_drop_count`,
        - schema-drift append regression,
        - append-between-batch export no-skip regression.
      - `tests/test_execution_stream5_scripts.py`:
        - backfill runner annotation/summary regression,
        - baseline slippage signed-asymmetry regression.
  - Formula lock:
    - `median_t = median(history_t)`, `MAD_t = median(|history_t - median_t|)`,
    - `robust_sigma_t = max(1.4826 * MAD_t, 5.0)`,
    - `adaptive_limit_t = median_t + 4.0 * robust_sigma_t` when history length `>= 12`,
    - bootstrap fallback `adaptive_limit_t = 150.0`,
    - `adaptive_limit_t = clip(adaptive_limit_t, 25.0, hard_ceiling_ms)`,
    - `hard_ceiling_ms = env(TZ_EXEC_HEARTBEAT_HARD_CEILING_MS, default=500.0)`,
    - `decision_t = BLOCK` if latency missing, hard-ceiling breach, or adaptive breach; else `PASS`.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py tests/test_execution_controls.py tests/test_main_console.py` -> PASS.
    - `.venv\Scripts\python -m py_compile execution/microstructure.py scripts/backfill_execution_latency.py scripts/evaluate_execution_slippage_baseline.py tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py` -> PASS.
  - Open risks:
    - heartbeat verdict is currently telemetry-stage classification; pre-trade broker-heartbeat hard-stop wiring remains a separate runtime governance task.
    - adaptive policy assumes submit-to-ack latency is a stable proxy for heartbeat freshness; broker-native heartbeat channels may require separate calibration.
  - Rollback note:
    - revert `execution/microstructure.py`, `scripts/backfill_execution_latency.py`, `scripts/evaluate_execution_slippage_baseline.py`, `tests/test_execution_microstructure.py`, `tests/test_execution_stream5_scripts.py`, and corresponding docs if D-200 is rejected.

Phase 31 Option 1 Medium-Risk Reconciliation Sprint (2026-03-01): Deterministic Retry Identity + Fail-Closed Overflow/Shutdown + Replay Ledger Strictness (D-201) ✅
  - Decision:
    - close medium-risk operational gaps raised after Phase 31 hardening by enforcing deterministic retry idempotency, truthful immediate-write accounting, and explicit fail-closed behavior on telemetry overflow/shutdown and malformed replay-ledger states.
  - Implementation:
    - `execution/microstructure.py`:
      - replaced append-time random spool UID with deterministic business-key hash (`captured_at_utc` excluded),
      - preserved preassigned `_spool_record_uid` during spool decode (legacy offset UID only as fallback),
      - separated prepared vs immediate durable counters (`orders_prepared`/`fills_prepared` and `orders_written`/`fills_written`),
      - bounded retry buffer with all-or-nothing enqueue; overflow now raises `RuntimeError` (fail-closed),
      - shutdown now performs bounded best-effort drain and raises fail-closed error if pending bytes remain.
    - `execution/signed_envelope.py`:
      - added parent-directory `fsync` after replay-ledger rewrite replace,
      - malformed replay-ledger rows now trigger quarantine + rewrite + fail-closed reject of current submit,
      - added replay-ledger max-row cap (`TZ_EXECUTION_REPLAY_LEDGER_MAX_ROWS`, default `50_000`) with trim event,
      - increased default replay lock timeout from `5ms` to `25ms`.
    - `core/dashboard_control_plane.py` + `app.py`:
      - fixed `pd.NaT` null-like coercion ordering in planner (prevents date-compare type crash),
      - removed direct `.date()` dependency in auto-update spinner message.
    - tests:
      - extended `tests/test_execution_microstructure.py` for post-write error dedupe, overflow fail-closed, retry idempotency across repeated calls, missing-ack heartbeat block, and shutdown fail-closed behavior,
      - extended `tests/test_signed_envelope_replay.py` for malformed-ledger fail-closed semantics and rewrite fsync hook,
      - extended `tests/test_dashboard_control_plane.py` for `pd.NaT` invalid-state handling.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_signed_envelope_replay.py tests/test_dashboard_control_plane.py` -> PASS (`58 passed`).
    - `.venv\Scripts\python -m pytest -q tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_auto_backtest_control_plane.py tests/test_dashboard_control_plane.py tests/test_ticker_pool.py tests/test_alpha_engine.py tests/test_engine.py tests/test_statistics.py tests/test_signed_envelope_replay.py` -> PASS (`256 passed`).
    - `.venv\Scripts\python -m py_compile execution/microstructure.py execution/signed_envelope.py core/dashboard_control_plane.py app.py tests/test_execution_microstructure.py tests/test_signed_envelope_replay.py tests/test_dashboard_control_plane.py` -> PASS.
    - SAW reviewer recheck (A/B/C) -> no in-scope Critical/High findings.
  - Rationale:
    - enforce institutional fail-closed behavior for trust-boundary and telemetry durability edges while keeping hot path non-blocking under normal contention.
  - Open risks:
    - replay-ledger still requires line-scan under lock (now bounded by max-row cap),
    - legacy parquet single-file mode remains heavier than partitioned mode (performance debt, medium),
    - Streamlit runtime smoke was not rerun in this reconciliation-only round.
  - Rollback note:
    - revert `execution/microstructure.py`, `execution/signed_envelope.py`, `core/dashboard_control_plane.py`, `app.py`, touched tests, and this doc entry as one batch if D-201 is rejected.

Stream 1 Option 1 Isolated Inherited-High Round (2026-03-01): As-Of Yearly-Union + Feature-Spec Fail-Closed Enforcement (D-202) ✅
  - Decision:
    - close the inherited Stream 1 high backlog by removing yearly-union forward leakage and replacing feature-spec fail-soft behavior with fail-closed execution semantics.
  - Implementation:
    - `data/feature_store.py`:
      - yearly-union selector now uses an as-of anchor (`anchor_date`) with hard cutoff `date <= anchor_date`,
      - eligible yearly union set is restricted to `year < year(anchor_date)` with controlled bootstrap fallback to `year == year(anchor_date)` only when no prior year exists,
      - incremental builds now anchor selector at `append_start_ts` (full builds use `start_ts`),
      - `_execute_feature_specs` now raises `FeatureSpecExecutionError` on:
        - missing required context inputs,
        - missing fundamental dependencies not present in snapshot columns or prior spec outputs,
        - spec runtime exceptions,
        - non-DataFrame outputs and post-processing failures.
    - `tests/test_feature_store.py`:
      - added PIT regressions for yearly-union anchoring, same-day spike exclusion, and patch-overlay precedence before anchor,
      - added fail-closed regressions for spec runtime exception, missing inputs, missing fundamental dependencies, prior-output dependency allowance, and invalid non-DataFrame return type.
    - `docs/spec.md`:
      - updated FR-060 yearly-union semantics to match as-of anchor contract.
  - Evidence:
    - `.venv\Scripts\python -m py_compile data/feature_store.py tests/test_feature_store.py` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_updater_parallel.py tests/test_fundamentals_updater_checkpoint.py -q` -> PASS (`[100%]`).
    - SAW implementer + Reviewer A/B/C reconciliation for scoped files reported no unresolved in-scope Critical/High findings for Option1 scope.
  - Rationale:
    - enforces institutional PIT discipline for universe membership and removes silent degradation paths in spec execution.
  - Open risks:
    - non-blocking test-depth/observability follow-ups remain:
      - optional `run_build` integration test for explicit spec-failure status taxonomy,
      - optional additional patch-branch PIT stress cases.
    - inherited out-of-scope runtime debts identified by reviewers (schema-drift full-rewrite truncation risk, broader incremental recovery semantics) are tracked separately and were not introduced by this round.
  - Rollback note:
    - revert `data/feature_store.py`, `tests/test_feature_store.py`, `docs/spec.md`, and this decision-log entry if D-202 is rejected.

Stream 1 PiT Look-Ahead Bias Sprint Reconciliation (2026-03-01): Dual-Time Gate + Strict-Binding Plumbing + Fallback Valid-Time Mask + Deterministic Dedupe (D-203) ✅
  - Decision:
    - close Stream 1 reconciliation BLOCK findings by enforcing consistent PiT constraints across primary and fallback fundamentals paths and by converting active yearly-union selection to strict t-1 daily-liquidity ranking.
  - Implementation:
    - `data/fundamentals.py`:
      - timestamp-precision simulation gate retained (no day-normalize coercion),
      - dual-time visibility guard enforced:
        - `published_at <= simulation_ts`,
        - `release_date <= simulation_ts`,
      - added deterministic HMAC timestamp-binding helpers:
        - `create_simulation_ts_binding_token(...)`,
        - `validate_simulation_ts_binding_token(...)`,
      - strict binding mode:
        - `T0_STRICT_SIMULATION_TS_BINDING=1` requires token when `as_of_date` is provided,
      - fallback daily-path reconciliation:
        - release-date valid-time mask applied to all fallback matrices,
        - quality gate now enforces non-negative age (`age_days >= 0`),
      - deterministic dedupe reconciliation:
        - `_row_hash` tie-break key for equal-key/equal-`ingested_at` rows before dropping duplicates.
    - `data/feature_store.py`:
      - active `yearly_union` selector now ranks universe from the last tradable date strictly before anchor (`date < anchor`),
      - full-year pre-calculation removed from active selector flow,
      - strict-binding token/secret plumbing added from feature-store compute path into fundamentals loaders.
    - tests:
      - `tests/test_bitemporal_integrity.py`:
        - exact timestamp restatement crossover assertion,
        - fallback valid-time no-leak regression,
        - deterministic dedupe tie regression,
      - `tests/test_feature_store.py`:
        - same-day spike exclusion and patch precedence under t-1 anchor,
        - strict-binding plumbing regression (`compute_feature_frame` strict env).
      - `tests/test_fundamentals_daily.py`:
        - fallback monkeypatch signature compatibility updated for new optional binding args.
  - Formula lock:
    - `visible := (T_knowledge <= T_simulation) AND (T_valid <= T_simulation)`,
    - `token := HMAC_SHA256(secret, iso8601(T_simulation))`,
    - `valid_time_mask(date, permno) := release_date(date, permno) <= date`,
    - `quality_pass := (roic > 0) AND (revenue_growth_yoy > 0) AND (0 <= age_days <= max_age_days)`,
    - `universe_tminus1 := top_n(dollar_volume) at last_tradable_date where date < anchor`.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_feature_store.py` -> PASS (`45 passed`).
    - `.venv\Scripts\python -m py_compile data/fundamentals.py data/feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py tests/test_feature_store.py` -> PASS.
    - SAW reviewer recheck:
      - Reviewer A PASS,
      - Reviewer B PASS,
      - Reviewer C PASS,
      - no unresolved in-scope Critical/High findings.
  - Rationale:
    - removes remaining fallback and strict-mode operational leak paths while preserving fail-closed invariants and deterministic replay behavior required for institutional PiT correctness.
  - Open risks:
    - legacy `_select_permnos_from_annual_liquidity` helper remains for test/backward-compat surfaces; active runtime path no longer depends on it.
    - strict-binding remains environment-gated by operator policy and secret provisioning.
  - Rollback note:
    - revert `data/fundamentals.py`, `data/feature_store.py`, touched tests, and associated docs for D-203 if this sprint reconciliation is rejected.

Stream 1 Cleanup Slice (2026-03-01): Retire Legacy Annual-Liquidity Helper Surface (D-206) ✅
  - Decision:
    - retire legacy full-year helper surface to remove residual reintroduction risk and keep universe selection tied only to active t-1 anchored runtime selectors.
  - Implementation:
    - `data/feature_store.py`:
      - removed `_select_permnos_from_annual_liquidity` helper (legacy annual block semantics),
      - preserved active selector stack:
        - `_select_universe_permnos -> _top_liquid_permnos_yearly_union`,
        - strict t-1 cutoff (`date < anchor`) and last-tradable-date liquidity ranking unchanged.
    - `tests/test_feature_store.py`:
      - removed obsolete helper-level tests tied to retired function surface,
      - added dispatch/ownership regression:
        - `test_select_universe_permnos_yearly_union_uses_active_anchor_selector`,
      - retained active-path regressions for:
        - as-of anchoring,
        - same-day spike exclusion,
        - patch precedence before anchor.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_feature_store.py tests/test_bitemporal_integrity.py tests/test_fundamentals_daily.py` -> PASS (`43 passed`).
    - `.venv\Scripts\python -m py_compile data/feature_store.py tests/test_feature_store.py` -> PASS.
    - SAW reviewer recheck:
      - Reviewer A PASS,
      - Reviewer B PASS,
      - Reviewer C PASS.
  - Rationale:
    - removes legacy callable semantics that could accidentally bypass active t-1 runtime contract in future refactors.
  - Open risks:
    - none in-scope for this cleanup slice.
  - Rollback note:
    - revert `data/feature_store.py`, `tests/test_feature_store.py`, and associated docs/SAW updates if D-206 is rejected.

Stream 5 Execution Telemetry Constraint Pivot (2026-03-01): Authoritative Success Receipt Gate + Ambiguous Fail-Closed Reconciliation (D-204) ✅
  - Decision:
    - eliminate sparse `ok=True` success acceptance in orchestrator by requiring authoritative execution receipt fields (`filled_qty`, `filled_avg_price`, `execution_ts`) before marking an order successful.
  - Implementation:
    - `main_bot_orchestrator.py`:
      - added execution-receipt normalization and validation helpers:
        - `_to_positive_float_or_none`,
        - `_resolve_execution_ts`,
        - `_normalize_execution_receipt_fields`,
      - hardened `_ok_true_result_missing_required_broker_fields` to require:
        - symbol/side/qty parity fields,
        - `filled_qty > 0`,
        - `filled_avg_price > 0`,
        - non-empty `execution_ts`,
      - hardened reconciliation path:
        - direct `ok=True` sparse payloads now poll `get_order_by_client_order_id` and raise `AmbiguousExecutionError` if authoritative receipt remains unavailable,
        - `already exists` recovery promoted to success now enforces the same authoritative receipt gate and ambiguity failure mode.
    - `execution/broker_api.py`:
      - added `_resolve_execution_ts` and wired into `_normalize_submit_acceptance` so broker results expose canonical `execution_ts` when derivable from fill telemetry.
    - tests:
      - `tests/test_main_bot_orchestrator.py`:
        - sparse-`ok=True` reconciliation success test added,
        - sparse-`already exists` ambiguity fail-closed test added,
        - success-path doubles upgraded to include authoritative execution fields.
      - `tests/test_execution_controls.py`:
        - added `execution_ts` assertions on activity-derived and snapshot-fallback fill telemetry paths.
  - Evidence:
    - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py execution/broker_api.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py` -> PASS.
    - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py` -> PASS (`[100%]`).
  - Rationale:
    - removes orchestrator blindness from sparse success payloads and guarantees that `ok=True` only exists when execution is backed by definitive broker receipt fields.
  - Open risks:
    - remaining non-critical observability enhancement: explicit status taxonomy field for ambiguous-receipt classes can be added in a follow-up.
  - Rollback note:
    - revert `main_bot_orchestrator.py`, `execution/broker_api.py`, touched Stream 5 tests, and this decision-log entry if D-204 is rejected.

Stream 5 Final Cleanup (2026-03-01): Event-Time Heartbeat Ordering + Slippage Cohort Alignment (D-205) ✅
  - Decision:
    - close remaining Stream 5 medium risks by enforcing explicit event-time ordering for heartbeat history bootstrap and cohort-wide slippage denominator alignment (including zero-fill / no-observed-slippage rows).
  - Implementation:
    - `execution/microstructure.py`:
      - `_to_positive_float_or_none(...)` now rejects non-finite values (`inf`, `-inf`, `nan`) to prevent malformed payload propagation.
      - `_load_recent_submit_to_ack_history_ms(...)` now requires explicit event-time sort expressions (`COALESCE(TRY_CAST(...))`) over timestamp columns before extracting rolling latency history.
      - removed unordered fallback history query; when event-time cannot be established, bootstrap history returns empty (fail-safe, no chronology assumption).
    - `scripts/backfill_execution_latency.py`:
      - `_sort_backfill_rows(...)` now builds an event-time key from coalesced timestamp columns and sorts deterministically by event time (not append/capture order alone).
    - `scripts/evaluate_execution_slippage_baseline.py`:
      - baseline metrics now evaluate full intended cohort with:
        - `cohort_slippage_bps_i = slippage_bps_i if observed else 0.0`,
        - `sanitize(x) = x if isfinite(x) else null` before aggregation,
      - summary emits denominator transparency fields:
        - `cohort_rows`, `observed_rows`, `zero_imputed_rows`,
      - side/symbol aggregates now include full cohort rows and per-group `observed_rows`.
    - tests:
      - `tests/test_execution_microstructure.py`:
        - added event-time ordering regression for heartbeat bootstrap history.
      - `tests/test_execution_stream5_scripts.py`:
        - added backfill event-time sort regression,
        - updated slippage baseline assertions for cohort-aligned denominator and zero-imputed rows,
        - added non-finite input sanitization regression.
  - Formula lock:
    - `event_time_t = coalesce(arrival_ts, submit_sent_ts, broker_ack_ts, filled_at, execution_ts, captured_at_utc, created_at, updated_at)`,
    - `history_bootstrap := order_by(event_time_t DESC NULLS LAST)`,
    - `cohort_slippage_bps_i = slippage_bps_i if observed else 0.0`,
    - `sanitize(x) = x if isfinite(x) else null`,
    - `mean_slippage_bps = mean(cohort_slippage_bps)`.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py tests/test_execution_controls.py tests/test_main_console.py` -> PASS.
    - `.venv\Scripts\python -m py_compile execution/microstructure.py scripts/backfill_execution_latency.py scripts/evaluate_execution_slippage_baseline.py tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py` -> PASS.
  - Rationale:
    - prevents out-of-order packet ingestion from contaminating heartbeat baselines and removes slippage survivorship bias from Stream 5 baseline reports.
  - Open risks:
    - upstream feeds that provide invalid/unparseable timestamps can still reduce available bootstrap history length; telemetry quality policy should continue to monitor this rate.
  - Rollback note:
    - revert `execution/microstructure.py`, `scripts/backfill_execution_latency.py`, `scripts/evaluate_execution_slippage_baseline.py`, touched tests, and this decision entry if D-205 is rejected.

Stream 5 Option 2 Closure (2026-03-01): Fail-Loud Source Loader Contract for Runner Scripts (D-207) ✅
  - Decision:
    - eradicate silent DuckDB->Parquet fallback masking by enforcing strict primary-sink semantics in Stream 5 runner scripts.
  - Implementation:
    - `scripts/backfill_execution_latency.py`:
      - added loader source modes:
        - `duckdb_strict` (default),
        - `parquet_override` (explicit operator override only),
      - added `PrimarySinkUnavailableError`,
      - strict mode now fails loud on missing/unreadable/query-failing DuckDB with no implicit fallback,
      - explicit override paths:
        - CLI `--source-mode parquet_override`,
        - env `TZ_EXEC_TELEMETRY_SOURCE_MODE=parquet_override`.
    - `scripts/evaluate_execution_slippage_baseline.py`:
      - mirrored the same mode/exception contract and override controls.
    - tests (`tests/test_execution_stream5_scripts.py`):
      - strict mode fails loud when DuckDB is unavailable even if parquet exists,
      - strict mode fails loud on DuckDB query error without fallback,
      - parquet reads succeed only when explicit override is selected (CLI-mode token or env override).
  - Formula/contract lock:
    - `source_mode = duckdb_strict` (default),
    - `if source_mode == duckdb_strict and duckdb_unavailable: raise PrimarySinkUnavailableError`,
    - `if source_mode == parquet_override: read parquet`,
    - `implicit_fallback(duckdb -> parquet) = forbidden`.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_execution_stream5_scripts.py` -> PASS.
    - `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_execution_stream5_scripts.py tests/test_execution_controls.py tests/test_main_console.py` -> PASS.
    - `.venv\Scripts\python -m py_compile scripts/backfill_execution_latency.py scripts/evaluate_execution_slippage_baseline.py tests/test_execution_stream5_scripts.py` -> PASS.
    - `.venv\Scripts\python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<D-207 packet>" --require-open-risks-when-block --require-next-action-when-block` -> VALID.
    - `.venv\Scripts\python .codex/skills/_shared/scripts/validate_saw_report_blocks.py --report-file docs/saw_reports/saw_stream5_option2_round4.md` -> VALID.
  - Rationale:
    - removes fail-open observability risk where primary-sink outages appear healthy due to implicit secondary-source reads.
  - Open risks:
    - none introduced in this bounded Option 2 scope.
  - Rollback note:
    - revert `scripts/backfill_execution_latency.py`, `scripts/evaluate_execution_slippage_baseline.py`, `tests/test_execution_stream5_scripts.py`, and this decision entry if D-207 is rejected.

Stream 5 Sprint+1 Follow-Through (2026-03-01): Strict Success Invariant + Deterministic Ambiguity Trap (D-208) ✅
  - Decision:
    - harden orchestrator acceptance so `ok=True` cannot transition to success unless authoritative fill telemetry is structurally valid, bounded to order intent, and deterministic under duplicate-broker-row conditions.
  - Implementation:
    - `main_bot_orchestrator.py`:
      - strict authoritative receipt normalization now enforces:
        - parseable timezone-aware `execution_ts` (normalized to UTC `...Z`),
        - `filled_qty > 0`,
        - `filled_avg_price > 0`,
        - `filled_qty <= order.qty`,
      - required-field validator made non-mutating (`candidate = dict(result)`),
      - reconciliation polling hardened with:
        - per-poll lookup timeout (`EXECUTION_RECONCILIATION_LOOKUP_TIMEOUT_SECONDS`),
        - explicit issue tagging (`lookup_timeout`, `lookup_exception`, budget zero, unavailable receipt),
        - issue propagation into `AmbiguousExecutionError`,
      - duplicate output rows for the same `client_order_id` now fail closed deterministically:
        - pre-scan CID counts before row processing,
        - any duplicate CID is assigned `error=duplicate_batch_result_cid` regardless of row order.
    - `tests/test_main_bot_orchestrator.py`:
      - added malformed `execution_ts` ambiguity regression,
      - added overfilled-qty bound ambiguity regression,
      - added duplicate CID fail-closed regression with row-order permutations (sparse-first and authoritative-first),
      - added reconciliation lookup-timeout regression,
      - added zero reconciliation poll-budget regression.
  - Formula/contract lock:
    - `success := (ok == True) AND (filled_qty > 0) AND (filled_avg_price > 0) AND (execution_ts is valid_iso8601_tz) AND (filled_qty <= order_qty)`,
    - `if not success_candidate: poll_reconciliation()`,
    - `if reconciliation unavailable after budget: raise AmbiguousExecutionError(issue_tag)`,
    - `if duplicate_rows_for_same_cid: fail_closed(error=duplicate_batch_result_cid)`.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py` -> PASS (`61 passed`).
    - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py` -> PASS (`[100%]`).
    - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
    - SAW reviewer recheck:
      - Reviewer A PASS (duplicate-CID determinism closed),
      - Reviewer B PASS (bounded lookup timeout + ambiguity issue propagation),
      - Reviewer C PASS (timestamp validity + fill bound + non-mutating validator).
  - Rationale:
    - removes row-order and payload-shape ambiguity at the execution acceptance boundary so telemetry degradation cannot silently promote non-authoritative states into success.
  - Open risks:
    - medium deferred: batch `execute_orders(...)` exception classification is still broad (all exceptions can retry until exhaustion); can be split into transient/non-transient taxonomy in a follow-up.
  - Rollback note:
    - revert `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, and this decision entry if D-208 is rejected.

Stream 5 SAW Reconciliation (2026-03-01): Broker-CID Success Gate + Canonical Terminal Taxonomy + Batch Exception Fail-Closed (D-209) ✅
  - Decision:
    - close remaining Stream 5 in-scope High execution-identity/taxonomy risks by enforcing broker-origin CID for all `ok=True` acceptance paths and canonicalizing terminal receipt outcomes.
  - Implementation:
    - `main_bot_orchestrator.py`:
      - `_ok_true_result_missing_required_broker_fields(...)` now requires broker `client_order_id` in addition to existing authoritative success fields,
      - `ok=True` path now forces reconciliation when broker CID is missing,
      - terminal receipts are normalized through `_normalize_terminal_execution_result(...)` with:
        - `status` normalized to terminal token,
        - `terminal_reason` in `{terminal_unfilled, terminal_partial_fill}`,
        - canonical `error=<terminal_reason>:<status>`,
        - optional preserved `broker_error_raw`,
      - added batch exception boundary around `rebalancer.execute_orders(...)`:
        - retry while attempts remain,
        - deterministic fail-closed exhaustion receipt (`retry_exhausted`, `last_error=batch_exception:<ExceptionType>`).
    - `tests/test_main_bot_orchestrator.py`:
      - added non-recovery `ok=True` missing-broker-CID ambiguity regression,
      - updated terminal unfilled/partial tests to canonical taxonomy expectations,
      - added terminal status normalization/broker-error preservation regression,
      - added batch exception retry-recovery and exhaustion regressions.
  - Formula/contract lock:
    - `authoritative_ok := (ok == True) AND has(client_order_id, symbol, side, qty) AND (filled_qty > 0) AND (filled_avg_price > 0) AND (execution_ts is valid_iso8601_tz) AND (filled_qty <= order_qty)`.
    - `if authoritative_ok == False: reconciliation_required(client_order_id)`.
    - `if reconciliation unavailable after poll budget: raise AmbiguousExecutionError(reconciliation_issue)`.
    - `terminal_reason := terminal_unfilled if effective_fill_qty <= 0 or invalid else terminal_partial_fill`.
    - `terminal_error := terminal_reason + ":" + normalized_terminal_status`.
    - `if batch_submit_exception and attempt == max_attempts: fail_closed(error=retry_exhausted, last_error=batch_exception:<ExceptionType>)`.
  - Evidence:
    - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
    - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py` -> PASS (`198 passed`).
    - SAW reviewer final confirmations: Reviewer A PASS, Reviewer B PASS, Reviewer C PASS.
  - Rationale:
    - removes remaining fail-open acceptance path where local CID backfill could mask missing broker identity, and stabilizes downstream execution telemetry taxonomy.
  - Open risks:
    - medium (deferred): reconciliation timeout path uses daemon-thread timeout wrapper; long-run timeout soak/worker-cancellation hardening remains a follow-up resilience item.
  - Rollback note:
    - revert `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, and this decision entry if D-209 is rejected.

Phase 31 Closeout Protocol (2026-03-01): Artifact Seal with Inherited Full-Matrix Gate Carryover (D-210) ⚠
  - Decision:
    - seal Phase 31 release artifact and context packet now, but keep phase governance in BLOCK state due one inherited full-repo failure outside Stream 1/5 scope.
  - Implementation:
    - full-repo matrix executed:
      - `.venv\Scripts\python -m pytest --maxfail=1` -> `472 passed, 1 failed, 2 warnings in 50.94s`.
      - evidence artifact: `docs/context/e2e_evidence/phase31_chk_ph_01_pytest.log`.
    - failing path isolated for carryover:
      - `tests/test_phase15_integration.py::test_phase15_weights_respect_regime_cap`,
      - failure location `strategies/alpha_engine.py:488`,
      - cause: single-day snapshot missing non-null precomputed fields (`adv20`, `rsi_threshold`, `prev_rsi`, `prior_50d_high`).
    - runtime smoke proof executed:
      - controlled one-loop dry-run of `main_bot_orchestrator.main()` -> `SMOKE_OK run_scanners=1 run_pending=1`.
      - evidence artifact: `docs/context/e2e_evidence/phase31_chk_ph_02_smoke.log`.
    - Stream 1/5 isolation matrix evidence:
      - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py --maxfail=1` -> `198 passed in 7.37s`.
      - evidence artifact: `docs/context/e2e_evidence/phase31_chk_ph_04_stream_matrix.log`.
    - context packet refresh executed:
      - published `docs/handover/phase31_handover.md`,
      - refreshed `docs/context/current_context.json` and `docs/context/current_context.md` via `scripts/build_context_packet.py`.
  - Formula/contract lock:
    - `Phase31_Governance := PASS iff (FullRepoMatrix == GREEN) AND (RuntimeSmoke == PASS) AND (ContextPacket == REFRESHED)`.
    - Current state:
      - `FullRepoMatrix == BLOCK (1 inherited failure)`,
      - `RuntimeSmoke == PASS`,
      - `ContextPacket == REFRESHED`,
      - therefore `Phase31_Governance == BLOCK`.
  - Rationale:
    - preserves release-traceability and handover continuity without masking inherited cross-stream test debt.
  - Open risks:
    - inherited high-priority carryover to Phase 32: unresolved Phase 15 integration regression blocks unconditional governance PASS.
  - Rollback note:
    - revert `docs/handover/phase31_handover.md`, `docs/context/current_context.json`, `docs/context/current_context.md`, and this decision entry if D-210 is rejected.
