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
    - close Stream 1 reconciliation findings by enforcing consistent PiT constraints across primary and fallback fundamentals paths and by converting active yearly-union selection to strict t-1 daily-liquidity ranking.
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

Phase 31 Closeout Protocol (2026-03-02): Final Governance Promotion with Immutable Matrix Proof (D-210) ✅
  - Decision:
    - promote Phase 31 governance state to PASS after detached full-matrix execution returned immutable status `0` with full green matrix summary.
  - Implementation:
    - historical pre-promotion matrix retained for traceability:
      - `.venv\Scripts\python -m pytest --maxfail=1` -> `472 passed, 1 failed, 2 warnings in 50.94s`.
      - artifact: `docs/context/e2e_evidence/phase31_chk_ph_01_pytest.log`.
    - authoritative promotion matrix executed through detached wrapper:
      - `.venv\Scripts\python docs\context\e2e_evidence\phase31_full_matrix_wrapper.py` -> `597 passed, 5 warnings in 102.74s (0:01:42)`.
      - artifacts: `docs/context/e2e_evidence/phase31_full_matrix_final.status` (`0`), `docs/context/e2e_evidence/phase31_full_matrix_final.log`.
      - immutable hashes:
        - status sha256: `13BF7B3039C63BF5A50491FA3CFD8EB4E699D1BA1436315AEF9CBE5711530354`,
        - log sha256: `30D4C70C36E3DB0168A957C54290168E750E87BD02B03890C2A6526572B3C609`.
    - runtime smoke proof:
      - controlled one-loop dry-run of `main_bot_orchestrator.main()` -> `SMOKE_OK run_scanners=1 run_pending=1`.
      - artifact: `docs/context/e2e_evidence/phase31_chk_ph_02_smoke.log`.
    - Stream 1/5 isolation matrix:
      - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_main_console.py --maxfail=1` -> `198 passed in 7.37s`.
      - artifact: `docs/context/e2e_evidence/phase31_chk_ph_04_stream_matrix.log`.
    - context packet refresh/validation:
      - updated `docs/handover/phase31_handover.md`,
      - refreshed `docs/context/current_context.json` and `docs/context/current_context.md` via `scripts/build_context_packet.py --repo-root .` + `--validate`.
  - Formula/contract lock:
    - `Phase31_Governance := PASS iff (FullRepoMatrix == GREEN) AND (RuntimeSmoke == PASS) AND (ContextPacket == REFRESHED)`.
    - Current state:
      - `FullRepoMatrix == GREEN (597/597)`,
      - `RuntimeSmoke == PASS`,
      - `ContextPacket == REFRESHED`,
      - therefore `Phase31_Governance == PASS`.
  - Rationale:
    - preserves release-traceability while promoting only on immutable artifact-backed evidence.
  - Open risks:
    - promotion is complete; next work is Phase 32 canonical backlog execution:
      - reconciliation-timeout soaks + cancellation hardening,
      - UTF-8 decode wedge reconciliation,
      - DuckDB flush optimization,
      - exception taxonomy split (transient vs non-transient),
      - routing diagnostics tail,
      - UID drift closure.
  - Rollback note:
    - revert `docs/handover/phase31_handover.md`, `docs/context/current_context.json`, `docs/context/current_context.md`, and this decision entry if promotion framing is rejected.

Phase 32 Step 1 (2026-03-02): Reconciliation Timeout Soak + Cooperative Cancellation + Quarantine Durability (D-211) ✅
  - Decision:
    - close Phase 32 Step 1 SRE acceptance checks by moving reconciliation timeout behavior from best-effort daemon timeout to deterministic cooperative-cancel semantics, sticky lookup taxonomy, and durable quarantine evidence writes.
  - Implementation:
    - `main_bot_orchestrator.py`:
      - `_poll_lookup_with_timeout(...)` now:
        - injects `cancel_event` when broker lookup supports it,
        - catches `asyncio.CancelledError` and emits `lookup_cancelled`,
        - emits `lookup_timeout:<seconds>:uncooperative` when worker remains alive beyond timeout/cancel-grace boundary.
      - `_poll_reconciliation_receipt(...)` now:
        - preserves highest-severity lookup issue taxonomy across polls (sticky precedence),
        - returns early on `:uncooperative` timeout to avoid spawning additional hanging lookup workers in the same reconciliation attempt.
      - Added quarantine sink helpers:
        - `_append_reconciliation_quarantine_entry(...)`,
        - `_augment_reconciliation_issue_with_quarantine(...)`,
        - lock-based serialized append (`.lock` sidecar + low-level `O_APPEND` write),
        - durable `fsync` and schema contract `schema_version=1`.
      - Quarantine trigger policy:
        - timeout/cancel/lookup-exception issue families only.
    - `tests/test_main_bot_orchestrator.py`:
      - synthetic chaos adapter for cooperative cancellation,
      - cancellation regression + quarantine verification,
      - mixed-poll precedence regression (`lookup_cancelled` preserved even after later generic unavailability),
      - thread-isolation soak proving blocked reconciliation path does not wedge telemetry spool flush,
      - concurrent quarantine writer integrity regression (lossless/valid JSONL under multi-thread append),
      - timeout regression upgraded for `:uncooperative` taxonomy and schema assertions.
  - Formula/contract lock:
    - `if lookup supports cancel_event and timeout breached -> set(cancel_event) and classify CancelledError as lookup_cancelled`.
    - `if lookup worker remains alive after timeout path -> lookup_timeout:<t>s:uncooperative`.
    - `if any poll emits lookup_* issue -> final issue preserves lookup_* precedence (sticky)`.
    - `if unresolved ambiguity AND issue family in {lookup_timeout, lookup_cancelled, lookup_exception} -> quarantine_append(issue) BEFORE raise AmbiguousExecutionError`.
    - `quarantine_append := lock_serialized + fsync + schema_versioned_jsonl`.
  - Evidence:
    - `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py` -> PASS (`65 passed`).
    - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
    - SAW reviewer reconciliation:
      - Reviewer A found and closed lookup-issue precedence downgrade risk.
      - Reviewer B found and closed uncooperative timeout poll-spawn risk.
      - Reviewer C found and closed concurrent quarantine append integrity risk.
  - Rationale:
    - Phase 32 Step 1 requires deterministic failure handling under synthetic chaos without sacrificing async heartbeat/telemetry forward progress or evidence integrity.
  - Open risks:
    - inter-process lock stress beyond in-process concurrency coverage remains an operational follow-up.
    - pytest atexit temp cleanup emits environment-level `PermissionError` after successful suite completion.
  - Rollback note:
    - revert `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, `docs/phase_brief/phase32-brief.md`, and this decision entry if D-211 is rejected.

Phase 32 Step 2 (2026-03-02): UTF-8 Decode Wedge Reconciliation in Quarantine Ingestion/Replay Path (D-212) ✅

  - Decision record:
    - close Phase 32 Step 2 SRE acceptance checks by adding fail-closed UTF-8 decode error handling in quarantine JSONL replay path with deterministic malformed-byte fixture proving graceful recovery instead of ingestion wedge.
  - The Friction Point:
    - quarantine JSONL reads using `.read_text(encoding="utf-8")` will wedge with `UnicodeDecodeError` if broker responses or external error messages contain malformed UTF-8 bytes.
    - ingestion/replay boundaries (e.g., monitoring scripts, forensic analysis, reconciliation audit) cannot operate if quarantine file becomes unreadable.
    - no deterministic malformed-byte test fixture existed to prove robustness against corruption.
  - The Decision (Hardcoded):
    - Add `_read_quarantine_jsonl_safe()` helper with `errors='replace'` decode policy.
    - Convert malformed UTF-8 bytes to U+FFFD replacement character instead of raising exception.
    - Add deterministic malformed-byte test fixture (`0xFF`,`0xFE` invalid UTF-8 sequence).
    - Retrofit all 5 existing quarantine read calls in test suite to use safe reader.
    - Schema contract preserved: safe reader returns valid `list[dict[str, Any]]` even with corrupted input.
  - Rationale:
    - External sources (broker APIs, process snapshots, third-party integrations) may emit non-UTF-8 or corrupted data.
    - Quarantine files are forensic evidence and must remain readable under partial corruption.
    - `errors='replace'` preserves maximum information (valid bytes + visible corruption markers) vs `errors='ignore'` (silent data loss).
    - Fail-closed design: always returns list (possibly empty), never wedges the caller.
  - Implementation:
    - Added:
      - `_read_quarantine_jsonl_safe(path: Path) -> list[dict[str, Any]]` with `errors='replace'` and JSON parse recovery.
      - `test_read_quarantine_jsonl_safe_handles_malformed_utf8()` with deterministic malformed-byte fixture proving graceful handling.
      - `test_read_quarantine_jsonl_safe_skips_malformed_json_lines()` proving malformed JSON lines are skipped without wedging replay.
      - Test retrofit: 5 existing quarantine read calls now use safe reader (formerly lines 2461, 2506, 2576, 2605, 2647).
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py --disable-warnings` -> PASS (71 passed in 1.45s).
    - malformed UTF-8 fixture: `b'{"schema_version":1,"client_order_id":"cid-malformed","reconciliation_issue":"error_\xff\xfe_invalid"}\n'`.
    - unsafe reader: `quarantine_path.read_text(encoding="utf-8")` raises `UnicodeDecodeError`.
    - safe reader: returns 3 valid rows with replacement character `\ufffd` in corrupted row's `reconciliation_issue` field.
  - Contract lock:
    - `quarantine_rows := _read_quarantine_jsonl_safe(path)`.
    - `if file contains malformed UTF-8: replace invalid bytes with U+FFFD and continue`.
    - `if line contains invalid JSON: log warning, skip line, continue`.
    - `quarantine schema contract always preserved: {schema_version, client_order_id, reconciliation_issue, ...}`.
  - Open risks:
    - current scope addresses quarantine JSONL only; other telemetry/log ingestion paths may still have unprotected `.read_text()` calls.
    - subprocess output decode wedge (process snapshots, scanner telemetry) remains out-of-scope pending broker API telemetry requirements.
  - Rollback note:
    - revert `main_bot_orchestrator.py` (`_read_quarantine_jsonl_safe`), `tests/test_main_bot_orchestrator.py` (test addition + retrofits), `docs/phase_brief/phase32-brief.md` (Step 2 section), and this decision entry if D-212 is rejected.

Phase 32 Step 3 (2026-03-02): DuckDB Flush Optimization - Eradicate O(N) Scaling in Telemetry Spool (D-213) ✅

  - Decision record:
    - close Phase 32 Step 3 SRE acceptance checks by removing O(N) COUNT(*) table scans from flush path and replacing with indexed deduplication lookups and batch-size-based end-of-table detection.
  - The Friction Point:
    - flush path in `execution/microstructure.py:772` executed two full-table COUNT(*) scans (before_count + after_count) on every flush, creating O(2N) cost that grew linearly with table size throughout the trading day.
    - export path in `execution/microstructure.py:859` executed COUNT(*) to determine total_rows for batching, adding additional O(N) scan on critical async flush path.
    - as telemetry spool accumulated thousands of rows, flush operations degraded from O(1) to O(N), threatening to block async event loop and delay heartbeat generation.
  - The Decision (Hardcoded):
    - Eradicate O(N) scaling by removing all COUNT(*) FROM table scans from critical write path.
    - Add CREATE INDEX on `_spool_record_uid` for O(log N) deduplication lookups instead of O(N) sequential scans.
    - Pre-compute inserted row count by executing SELECT ... WHERE NOT EXISTS query before INSERT (O(M log N) where M=batch size).
    - Shift bottleneck from "table size" (unbounded growth) to "batch size" (constant per flush).
    - Remove export path COUNT(*) and detect end-of-table via actual rows fetched vs batch_size (no pre-counting).
    - Keep export cursor pinned at EOF on empty fetch (no automatic rewind) so next tail append exports in the immediate next flush cycle.
    - Use PRAGMA table_info() (O(1) metadata check) for table existence validation instead of COUNT(*).
    - Tighten shutdown fail-closed gate: raise `MicrostructureFlushError` on any terminal `pending_bytes > 0`, `buffer_drop_count > 0`, or non-empty `last_flush_error`.
  - Rationale:
    - COUNT(*) scans entire table sequentially, O(N) cost grows linearly with spool accumulation.
    - Indexed NOT EXISTS lookups are O(log N), bounded by tree height not table size.
    - Counting SELECT result before INSERT avoids double-scan (before/after pattern) while preserving exact inserted row count contract.
    - Export end-of-table detection via batch size eliminates need to pre-count total rows (LIMIT/OFFSET already fetches exact batch).
    - Optimization maintains fail-closed durability guarantee (disk/sink failures now propagate through shutdown even when pending bytes drain to zero).
  - Implementation:
    - Modified:
      - `execution/microstructure.py` (`_append_duckdb_table_rows` lines 769-786): removed before_count/after_count COUNT(*), added CREATE INDEX, pre-compute inserted rows via SELECT COUNT(*) FROM (insert_query).
      - `execution/microstructure.py` (`_export_duckdb_table_to_parquet` lines 856-897): removed total_rows COUNT(*), added PRAGMA table_info(), detect end-of-table via len(export_df) < batch_size, keep cursor at EOF (no rewind).
      - `execution/microstructure.py` (`_TelemetrySpooler.stop` / `_shutdown_execution_microstructure_spoolers`): enforce fail-closed raise on pending bytes, drop evidence, or sink error evidence.
      - `tests/test_execution_microstructure.py`: added EOF-tail export regression and synthetic disk-full shutdown propagation regression.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_execution_microstructure.py --disable-warnings` -> PASS (44 passed in 21.05s).
    - `.venv\Scripts\python -m py_compile execution/microstructure.py tests/test_execution_microstructure.py` -> PASS.
    - Before: 3 full table scans per flush cycle (lines 772, 785, 859) = O(2N) + O(N) = O(3N).
    - After: 0 full table scans, indexed lookups only = O(M log N) where M=batch size (constant).
    - Bottleneck shifted: table size (grows all day) → batch size (constant per flush).
  - Contract lock:
    - `inserted_rows := SELECT COUNT(*) FROM (SELECT ... WHERE NOT EXISTS ...)` ← count query result, not entire table.
    - `CREATE INDEX IF NOT EXISTS idx_{table}_spool_uid ON {table}(_spool_record_uid)` ← O(log N) deduplication.
    - `NOT EXISTS (SELECT 1 FROM {table} WHERE uid = new_uid)` ← O(log N) with index.
    - `export_df := LIMIT {batch_size} OFFSET {start_row}` ← fetch batch without pre-counting total.
    - `if len(export_df) < batch_size: reached end-of-table` ← detect end via result size.
    - `cursor := start_row + len(export_df)` ← track via actual rows, not pre-computed total.
  - Open risks:
    - index maintenance overhead: CREATE INDEX IF NOT EXISTS adds one-time cost on first flush, amortized across subsequent flushes.
    - cursor drift self-heal: if external process truncates/rebuilds table out-of-band, EOF-pinned cursor may require explicit reset to recover.
  - Rollback note:
    - revert `execution/microstructure.py` (`_append_duckdb_table_rows` and `_export_duckdb_table_to_parquet` optimizations), `docs/phase_brief/phase32-brief.md` (Step 3 section), and this decision entry if D-213 is rejected.

Phase 32 Step 4 (2026-03-02): Exception Taxonomy Split - TRANSIENT vs TERMINAL Routing for Execution Failures (D-214) ✅

  - Decision record:
    - close Phase 32 Step 4 SRE acceptance checks by enforcing deterministic binary exception taxonomy and canonical routing for broker failures:
      - `TERMINAL` -> immediate fail-closed `FAILED_REJECTED`,
      - `TRANSIENT` -> bounded retry then canonical `retry_exhausted`.
  - The Friction Point:
    - broad exception handling risked conflating hard broker rejects with transient infrastructure failures.
    - retrying hard rejects (for example buying-power failures) can freeze allocation loops.
    - dropping transient infrastructure failures as terminal can under-fill portfolios.
  - The Decision (Hardcoded):
    - add `_classify_broker_exception(exc)` with binary classes: `TERMINAL` or `TRANSIENT`.
    - route batch exceptions deterministically:
      - terminal bypasses retry loop immediately and emits `FAILED_REJECTED`,
      - transient uses bounded retry loop and emits `retry_exhausted` on exhaustion.
    - add canonical result builders:
      - `_build_failed_rejected_result(...)`,
      - `_build_retry_exhausted_result(...)`.
    - apply canonical taxonomy fields across batch-level and row-level paths (no schema drift between retry_exhausted branches).
    - map row-level non-retryable terminal broker errors to canonical `FAILED_REJECTED` instead of raw free-form pass-through.
    - enforce terminal precedence before retry-token gate in row-level routing so mixed-token errors (`401 unauthorized connection reset`) fail closed as terminal.
    - enforce bounded lookup timeout behavior with minimum async timeout (`EXECUTION_RECONCILIATION_LOOKUP_MIN_TIMEOUT_SECONDS=0.01`) to eliminate synchronous stall risk for `timeout<=0`.
    - emit terminal exception log entries with canonical reason token.
  - Rationale:
    - exception taxonomy split is required for safe production routing semantics:
      - terminal failures must fail fast and release orchestration flow,
      - transient failures must retry within bounded limits.
    - canonical output contracts prevent downstream telemetry/parsing drift.
  - Implementation:
    - `main_bot_orchestrator.py`:
      - added `_build_retry_exhausted_result(...)`, `_build_failed_rejected_result(...)`,
      - integrated canonical builders into all transient exhausted and terminal rejected branches,
      - added row-level terminal classification path for non-retryable broker errors,
      - reordered row-level routing so `TERMINAL` classification is evaluated before retry-token checks,
      - added `EXECUTION_RECONCILIATION_LOOKUP_MIN_TIMEOUT_SECONDS`,
      - replaced synchronous `timeout<=0` lookup path with bounded async timeout clamp.
    - `tests/test_main_bot_orchestrator.py`:
      - added `test_execute_orders_with_idempotent_retry_zero_lookup_timeout_remains_bounded`,
      - added `test_execute_orders_terminal_exception_logs_canonical_reason`,
      - tightened existing Step 4 assertions for canonical taxonomy fields in terminal/transient outcomes.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py --disable-warnings` -> PASS (`74 passed in 1.50s`).
    - `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
    - focused Step 4 slice:
      - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py -k "terminal_exception_bypasses_retry_immediately or transient_exception_retries_with_backoff or classify_broker_exception_terminal_cases or classify_broker_exception_transient_cases or zero_lookup_timeout_remains_bounded or terminal_exception_logs_canonical_reason" --disable-warnings`
      - -> PASS (`6 passed, 68 deselected`).
    - SAW reviewer reconciliation:
      - Reviewer A PASS,
      - Reviewer B initially BLOCK on non-positive timeout stall path -> closed,
      - Reviewer C initially BLOCK on taxonomy schema consistency -> closed.
  - Contract lock:
    - `exception_class := _classify_broker_exception(exc)` where `exception_class in {TERMINAL, TRANSIENT}`.
    - `if exception_class == TERMINAL -> error=FAILED_REJECTED AND retry_loop_bypassed`.
    - `if exception_class == TRANSIENT -> bounded_retry; on exhaust error=retry_exhausted`.
    - `effective_lookup_timeout := max(configured_timeout, 0.01)` (no synchronous indefinite lookup path).
  - Open risks:
    - taxonomy indicators are string-based; novel broker phrasing can still map to fallback `TRANSIENT`.
    - uncooperative broker lookup workers can remain alive until their own return even after timeout cancellation signal.
    - pytest atexit temp cleanup emits environment-level `PermissionError` noise.
  - Rollback note:
    - revert `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, `docs/phase_brief/phase32-brief.md`, and this decision entry if D-214 is rejected.

Phase 55 (2026-03-17): First Bounded Evidence Packet - Gate Miss, No Promotion (D-311) 🟡

  - Decision record:
    - recompute the canonical allocator gate from `data/processed/phase55_allocator_cpcv_summary.json` and treat any miss as a hard no-promotion outcome; do not reinterpret the first packet into discretionary promotion or implicit retry authority.
  - The Decision (Hardcoded):
    - `allocator_gate_pass = 0` on the first bounded Phase 55 evidence packet.
    - no lattice promotion is authorized.
    - Rule-of-100 remains inactive under `D-309`.
    - the Phase 53 research kernel remains immutable under `D-292`.
    - Phase 55 evidence artifacts remain staged only on `data/processed/phase55_*` via atomic write/replace semantics; no write-back into `research_data` is authorized.
  - Evidence:
    - `data/processed/phase55_allocator_cpcv_summary.json` -> `PBO=0.6596408867190602`, `DSR=2.2263075720581107e-45`, `positive_outer_fold_share=0.15`, `SPA_p=1.0`, `WRC_p=1.0`, `allocator_gate_pass=false`.
    - `data/processed/phase55_allocator_cpcv_evidence.json` published on the same processed surface.
    - `scripts/phase55_allocator_governance.py::_atomic_write_json` publishes the summary/evidence packet via temp -> `os.replace(...)`.
  - Contract lock:
    - `allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and (positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]`.
    - `if allocator_gate_pass == 0 -> no promotion`.
  - Open risks:
    - any follow-up Phase 55 execution requires explicit approval; `D-311` is not a retry grant.
  - Rollback note:
    - revert only Phase 55 docs/evidence artifacts if `D-311` wording is amended; do not alter the `D-292` research kernel.

Phase 55 (2026-03-17): Clean Governance Closeout - No-Retry / No-Promotion (D-312) 🟢

  - Decision record:
    - close Phase 55 Opportunity-Set Controller with `D-311` gate-miss evidence as permanent SSOT; treat any further Phase 55 activity as requiring a new explicit approval packet; block all Phase 56 work until a separate planning-only token is issued.
  - The Decision (Hardcoded):
    - Phase 55 governance surface is now closed and immutable.
    - `allocator_gate_pass = 0` remains authoritative; no reinterpretation or retry authority is granted.
    - Rule-of-100 remains inactive under `D-309`.
    - the Phase 53 research kernel remains read-only and immutable under `D-292`.
    - `data/processed/phase55_allocator_cpcv_summary.json` and `data/processed/phase55_allocator_cpcv_evidence.json` are the sole canonical Phase 55 evidence artifacts.
    - `active_phase = 55` remains the repo SSOT label until a separate explicit Phase 56 planning-only token is recorded.
    - Phase 56 planning-only kickoff is authorized only after explicit follow-up approval; no implementation or execution is permitted yet.
  - Evidence:
    - `data/processed/phase55_allocator_cpcv_summary.json` -> `PBO=0.6596408867190602`, `DSR=2.2263075720581107e-45`, `positive_outer_fold_share=0.15`, `SPA_p=1.0`, `WRC_p=1.0`, `allocator_gate_pass=false`.
    - `data/processed/phase55_allocator_cpcv_evidence.json` remains the co-published fold-level evidence packet on the same processed surface.
    - `docs/saw_reports/saw_phase55_d311_gate_miss_20260317.md` and `docs/saw_reports/saw_phase55_d310_kickoff_20260317.md` preserve the governance trail.
    - `docs/phase_brief/phase55-brief.md` is updated to `CLOSED` and `docs/context/current_context.md` / `docs/context/current_context.json` are refreshed from that SSOT.
  - Contract lock:
    - `Phase55 := CLOSED iff (D-312 published) and (context packet refreshed) and (phase55_summary_evidence remains the only SSOT input surface)`.
    - `if future Phase 55 work is proposed -> require a new explicit approval packet; D-311 does not grant retry authority`.
  - Open risks:
    - none.
  - Rollback note:
    - revert only this `D-312` entry plus the synchronized Phase 55 docs/context closeout edits if leadership amends wording; do not alter the `D-311` evidence artifacts or the `D-292` research kernel.

Phase 56 (2026-03-18): Planning-Only Kickoff - Event Sleeve 1 (PEAD) (D-313) 🔵

  - Decision record:
    - open Phase 56 as a docs-only planning surface for PEAD Event Sleeve 1; execution remains blocked until a separate explicit token is issued.
  - The Decision (Hardcoded):
    - Phase 56 is now active for planning only.
    - `active_phase = 56` becomes the repo SSOT label only after this kickoff packet is published and the context packet is refreshed.
    - Phase 55 remains closed and immutable under `D-312`; `D-311` evidence remains permanent SSOT.
    - the Phase 53 research kernel remains read-only and immutable under `D-292`.
    - no Phase 56 implementation, evidence generation, or production promotion is authorized in this round.
    - Phase 56 execution requires a future explicit approval packet and token.
  - Evidence:
    - `docs/phase_brief/phase53-brief.md` roadmap bullet -> `Phase 56 - Event Sleeve 1 (PEAD)`.
    - `docs/phase_brief/phase53-brief.md` missing-hook table row -> `PEAD sleeve runner + cost-aware report`.
    - `docs/phase_brief/phase56-brief.md` publishes the planning-only boundary and hook inventory.
    - `docs/handover/phase56_kickoff_memo_20260318.md` publishes the PM-facing kickoff memo.
  - Contract lock:
    - `Phase56 := PLANNING_ONLY iff (D-313 published) and (context packet refreshed) and (NextPhaseApproval == PENDING)`.
    - `if future Phase 56 work is proposed -> require a separate explicit execution approval packet; D-313 is not an execution grant`.
  - Open risks:
    - none.
  - Rollback note:
    - revert only this `D-313` entry plus the synchronized Phase 56 planning docs/context/SAW edits if leadership amends wording; do not alter `D-312`, `D-311` evidence, or the `D-292` research kernel.

Phase 56 (2026-03-18): Bounded Execution Authorization - Event Sleeve 1 (PEAD) (D-314) 🟢

  - Decision record:
    - consume the exact in-thread token `approve next phase` and authorize the bounded Phase 56 PEAD Event Sleeve 1 first evidence packet on the locked Phase 53 surface only.
  - The Decision (Hardcoded):
    - Phase 56 execution is now active for the bounded PEAD surface only.
    - `NextPhaseApproval = APPROVED` for the first bounded PEAD execution packet.
    - any Phase 56 work must stay on the same-window / same-cost / same-`core.engine.run_simulation` path and respect `RESEARCH_MAX_DATE = 2022-12-31`.
    - the Phase 53 research kernel remains read-only and immutable under `D-292`.
    - Rule-of-100 remains inactive under `D-309`.
    - Phase 55 remains closed and immutable under `D-312`; `D-311` evidence remains historical SSOT and is not reopened here.
    - no production promotion, loader reopen, post-2022 expansion, or non-PEAD execution is authorized in `D-314`.
  - Evidence:
    - exact approval token consumed in-thread on 2026-03-18: `approve next phase`.
    - `docs/phase_brief/phase56-brief.md` updated to `Executing` with bounded PEAD scope.
    - `docs/phase_brief/phase53-brief.md` roadmap and missing-hook evidence continue to anchor the PEAD phase scope.
  - Contract lock:
    - `phase56_execution_authorized = 1[(reply contains exact 'approve next phase') and (NextPhaseApproval == APPROVED)]`.
    - `Phase56 := EXECUTING iff (D-314 published) and (context packet refreshed) and (scope remains PEAD-only on the locked surface)`.
  - Open risks:
    - none.
  - Rollback note:
    - revert only this `D-314` entry plus the synchronized Phase 56 execution-authorization docs/context/SAW edits if leadership amends wording; do not alter `D-312`, `D-311` evidence, or the `D-292` research kernel.

Phase 56 (2026-03-18): First Bounded PEAD Runner + Evidence Packet (D-315) 🟢

  - Decision record:
    - implement the smallest bounded PEAD sleeve/report slice on the locked surface using `capital_cycle_score` plus the existing `quality_pass` gate, publish the first cost-aware evidence packet, and keep promotion blocked.
  - The Decision (Hardcoded):
    - `scripts/phase56_pead_runner.py` is the bounded Phase 56 runner for this packet.
    - governed PEAD weights are equal-weight across names that satisfy `quality_pass = 1`, `adv_usd >= 5_000_000`, `0 <= days_since_earnings <= 63`, and `value_rank_pct >= 0.60` on `capital_cycle_score`.
    - governed return, turnover, and cost series for this packet are produced by `core.engine.run_simulation` at `cost_bps = 5.0` with `end_date <= 2022-12-31`.
    - no loader reopen, no post-2022 expansion, no Rule-of-100 reopen, and no production promotion is authorized here.
  - Evidence:
    - `.venv\Scripts\python scripts/phase56_pead_runner.py --start-date 2000-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0`.
    - `data/processed/phase56_pead_summary.json` -> `Sharpe = 0.4557`, `CAGR = 0.0795`, `MaxDD = -0.5054`, `Ulcer = 15.1873`, `turnover_annual = 78.7201`, `avg_positions = 32.9191`.
    - `data/processed/phase56_pead_evidence.csv` publishes the daily governed PEAD return/turnover/equity series for the bounded packet.
    - `tests/test_phase56_pead_runner.py` passes.
  - Contract lock:
    - `phase56_pead_gate_{i,t} = 1[(quality_pass_{i,t} = 1) and (adv_usd_{i,t} >= 5_000_000) and (0 <= days_since_earnings_{i,t} <= 63) and (value_rank_pct_{i,t} >= 0.60)]`.
    - `Phase56_PEAD_Packet1 := VALID iff (summary artifact exists) and (evidence artifact exists) and (end_date <= 2022-12-31) and (series are produced by core.engine.run_simulation)`.
  - Open risks:
    - the broader baseline/delta comparator path is not widened in `D-315`; this packet is bounded evidence only.
  - Rollback note:
    - revert only the synchronized Phase 56 runner/test/docs/context/SAW edits from this round; do not alter `D-314`, `D-312`, `D-311` evidence, or the `D-292` research kernel.

Phase 56 (2026-03-18): First Bounded PEAD Evidence Review - Evidence Only / No Widening (D-316) 🔵

  - Decision record:
    - review the first bounded PEAD evidence packet against the actual on-disk summary schema, publish an evidence-only disposition, and keep comparator widening or promotion blocked absent a separate explicit approval packet.
  - The Decision (Hardcoded):
    - `data/processed/phase56_pead_summary.json` is the authoritative summary artifact for this packet.
    - `strategy_id = PHASE56_PEAD_CAPITAL_CYCLE_V1`, `same_engine = true`, `start_date = 2000-01-01`, `end_date = 2022-12-31`, and `max_date = 2022-12-31` remain the repo-truth identifiers for the first bounded packet.
    - the bounded summary metrics currently under review are `sharpe = 0.4556995567986322`, `cagr = 0.07950885309583589`, `max_dd = -0.505398622797651`, `ulcer = 15.187284696866094`, `turnover_annual = 78.72013729610197`, and `avg_positions = 32.91907094901107`.
    - no invented summary fields, inferred gate verdict, comparator delta, or promotion language are authorized in `D-316` because the on-disk summary artifact does not publish them.
    - `D-314` remains the only execution authorization consumed in this phase so far; `D-316` is a review/hold packet only and does not widen the Phase 56 surface.
  - Evidence:
    - `data/processed/phase56_pead_summary.json` -> `strategy_id = PHASE56_PEAD_CAPITAL_CYCLE_V1`, `same_engine = true`, `candidate_rows = 181417`, `candidate_permnos = 219`, `candidate_dates = 5511`, `turnover_total = 1721.5344311064205`, `net_return_total = 4.328752294275915`.
    - `data/processed/phase56_pead_evidence.csv` remains the co-published daily evidence surface referenced by the summary artifact.
    - `docs/phase_brief/phase56-brief.md` is updated to the review/hold state and `docs/context/current_context.md` / `docs/context/current_context.json` are refreshed from that SSOT.
  - Contract lock:
    - `Phase56_D316_Review := VALID iff (review wording cites only keys present in data/processed/phase56_pead_summary.json) and (same_engine = true) and (end_date = max_date = 2022-12-31) and (no comparator or promotion widening language is introduced)`.
    - `if future comparator or additional Phase 56 execution is proposed -> require a new explicit approval packet; D-316 is not that approval`.
  - Open risks:
    - the broader baseline/delta comparator path remains unpublished in this packet and still requires a separately approved scope if leadership wants it.
  - Rollback note:
    - revert only this `D-316` entry plus the synchronized Phase 56 brief/context/lesson/SAW edits if leadership amends the review wording; do not alter the `D-315` evidence artifacts, `D-314`, Phase 55 evidence, or the `D-292` research kernel.

Phase 56 (2026-03-18): Closeout - No Promotion / No Comparator (D-317) 🟢

  - Decision record:
    - close Phase 56 as evidence-only / no promotion / no comparator widening while preserving the bounded PEAD surface and Phase 55 locks.
  - The Decision (Hardcoded):
    - Phase 56 is closed; no promotion or comparator widening is authorized.
    - `data/processed/phase56_pead_summary.json` and `data/processed/phase56_pead_evidence.csv` remain the SSOT artifacts for Phase 56.
    - any follow-up Phase 56 work requires a new explicit approval packet.
  - Evidence:
    - full regression: `.venv\Scripts\python -m pytest -q` -> PASS (see `docs/context/e2e_evidence/phase56_closeout_full_pytest_20260318.*`).
    - runtime smoke: `.venv\Scripts\python launch.py --help` -> PASS (see `docs/context/e2e_evidence/phase56_launch_smoke_20260318.*`).
    - bounded replay: `.venv\Scripts\python scripts/phase56_pead_runner.py --start-date 2000-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0 --summary-path docs\context\e2e_evidence\phase56_pead_replay_summary_20260318.json --evidence-path docs\context\e2e_evidence\phase56_pead_replay_evidence_20260318.csv`.
  - Contract lock:
    - `Phase56 := CLOSED iff (D-317 published) and (context packet refreshed) and (SSOT artifacts unchanged)`.
    - `if future Phase 56 work is proposed -> require a new explicit approval packet; D-317 is not an execution grant`.
  - Open risks:
    - comparator hardening remains blocked until an explicit approval packet.
  - Rollback note:
    - revert only this `D-317` entry plus the synchronized Phase 56 closeout docs/context/SAW edits; do not alter the `D-315` evidence artifacts, `D-314`, Phase 55 evidence, or the `D-292` research kernel.

Phase 57 (2026-03-18): Planning-Only Kickoff - Event Sleeve 2 (Corporate Actions) (D-318) 🔵

  - Decision record:
    - open Phase 57 as a docs-only planning surface for Corporate Actions; execution and any optional Phase 56 comparator follow-up remain blocked until separate explicit approval packets are issued.
  - The Decision (Hardcoded):
    - Phase 57 is now active for planning only.
    - `active_phase = 57` becomes the repo SSOT label only after this kickoff packet is published and the context packet is refreshed.
    - Phase 56 remains closed and immutable under `D-317`; `data/processed/phase56_pead_summary.json` and `data/processed/phase56_pead_evidence.csv` remain permanent SSOT.
    - Phase 55 remains closed and immutable under `D-312`; `D-311` evidence remains historical SSOT.
    - the Phase 53 research kernel remains read-only and immutable under `D-292`.
    - no Phase 57 implementation, evidence generation, or production promotion is authorized in this round.
    - Phase 57 execution requires a future explicit approval packet and the exact token `approve next phase`.
  - Evidence:
    - `docs/phase_brief/phase53-brief.md` roadmap bullet -> `Phase 57 - Event Sleeve 2 (Corporate Actions)`.
    - `docs/phase_brief/phase53-brief.md` missing-hook table row -> `corporate-actions taxonomy`.
    - `docs/phase_brief/phase57-brief.md` publishes the planning-only boundary and hook inventory.
    - `docs/handover/phase57_kickoff_memo_20260318.md` publishes the PM-facing kickoff memo.
  - Contract lock:
    - `Phase57 := PLANNING_ONLY iff (D-318 published) and (context packet refreshed) and (NextPhaseApproval == PENDING)`.
    - `if future Phase 57 work is proposed -> require a separate explicit execution approval packet; D-318 is not an execution grant`.
  - Open risks:
    - none.
  - Rollback note:
    - revert only this `D-318` entry plus the synchronized Phase 57 planning docs/context/SAW edits if leadership amends wording; do not alter `D-317`, the `D-315` evidence artifacts, `D-312`, or the `D-292` research kernel.

Phase 57 (2026-03-18): Bounded Execution Authorization - Event Sleeve 2 (Corporate Actions) (D-319) 🟢

  - Decision record:
    - consume the exact in-thread token `approve next phase` and authorize the bounded Phase 57 Corporate Actions first evidence packet on the locked Phase 53 surface only.
  - The Decision (Hardcoded):
    - Phase 57 execution is now active for the first bounded Corporate Actions packet only.
    - `NextPhaseApproval = APPROVED` for the first bounded Phase 57 packet only.
    - the bounded packet must stay on the same `2015-01-01 -> 2022-12-31`, `5.0` bps, same-`core.engine.run_simulation` path as the latest governed C3 baseline in `data/processed/phase54_core_sleeve_summary.json`.
    - the Phase 53 research kernel remains read-only and immutable under `D-292`.
    - Rule-of-100 remains inactive under `D-309`.
    - no production promotion, loader reopen, post-2022 expansion, or non-Phase-57 execution is authorized in `D-319`.
  - Evidence:
    - exact approval token consumed in-thread on 2026-03-18: `approve next phase`.
    - `docs/phase_brief/phase53-brief.md` roadmap bullet -> `Phase 57 - Event Sleeve 2 (Corporate Actions)`.
    - `data/processed/phase54_core_sleeve_summary.json` -> `baseline_config_id = C3_LEAKY_INTEGRATOR_V1`, `window = 2015-01-01 -> 2022-12-31`, `cost_bps = 5.0`.
  - Contract lock:
    - `Phase57_D319_Exec := APPROVED iff (exact token consumed) and (window = 2015-01-01 -> 2022-12-31) and (cost_bps = 5.0) and (same engine path = core.engine.run_simulation)`.
    - `if future Phase 57 work is proposed -> require a new explicit approval packet; D-319 is not open-ended execution authority`.
  - Open risks:
    - none.
  - Rollback note:
    - revert only this `D-319` entry plus the synchronized Phase 57 execution-authorization docs/context/SAW edits if leadership amends wording; do not alter `D-317`, `D-312`, or the `D-292` research kernel.

Phase 57 (2026-03-18): First Bounded Corporate Actions Runner + Evidence Packet (D-320) 🟢

  - Decision record:
    - implement the smallest bounded Corporate Actions taxonomy / runner slice on the locked surface, publish the first same-window / same-cost / same-engine summary + evidence + delta-vs-C3 artifacts, and keep promotion blocked pending review.
  - The Decision (Hardcoded):
    - `scripts/phase57_corporate_actions_runner.py` is the bounded Phase 57 runner for this packet.
    - governed Corporate Actions event yield is `corp_action_yield_t = total_ret_t - ((raw_close_t / raw_close_{t-1}) - 1)`.
    - governed candidates satisfy `quality_pass = 1`, `adv_usd >= 5_000_000`, `0.005 <= corp_action_yield <= 0.25`, and `value_rank_pct >= 0.60` on `capital_cycle_score`.
    - target weights are equal-weight across confirmed event names on event day and explicitly reindexed to the full trading calendar so `core.engine.run_simulation` executes the packet as a bounded next-day / one-day hold surface under `shift(1)`.
    - governed return, turnover, and cost series for this packet are produced by `core.engine.run_simulation` at `cost_bps = 5.0` with `start_date = 2015-01-01`, `end_date = 2022-12-31`, and `max_date = 2022-12-31`.
    - no loader reopen, no post-2022 expansion, no Rule-of-100 reopen, and no production promotion are authorized here.
  - Evidence:
    - `.venv\Scripts\python scripts/phase57_corporate_actions_runner.py --start-date 2015-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0`.
    - `data/processed/phase57_corporate_actions_summary.json` -> `strategy_id = PHASE57_CORP_ACTIONS_CASH_YIELD_V1`, `candidate_rows = 972`, `candidate_permnos = 113`, `candidate_dates = 866`, `active_days = 866`, `sharpe = 0.2392571448595545`, `cagr = 0.029013082955127834`, `max_dd = -0.3943086015317727`, `ulcer = 22.757006739516832`, `turnover_annual = 215.59030183077684`, `net_return_total = 0.2578058722905625`.
    - `data/processed/phase57_corporate_actions_delta_vs_c3.csv` -> `sharpe_delta = -0.240802877903895`, `cagr_delta = -0.06114407302135216`, `turnover_ratio_phase57_vs_c3 = 0.7061967047220717`, `max_dd_delta = 0.013356997284943994`, `ulcer_delta = 7.955780751115013`.
  - Contract lock:
    - `Phase57_D320_Packet := VALID iff (same_window_same_cost_same_engine = 1) and (summary/evidence/delta artifacts are co-published) and (end_date = max_date = 2022-12-31)`.
    - `if future comparator or additional Phase 57 execution is proposed -> require a new explicit approval packet; D-320 is the first bounded packet only`.
  - Open risks:
    - the first bounded packet remains below C3 on Sharpe and CAGR and therefore cannot be treated as promotion-ready evidence.
  - Rollback note:
    - revert only the synchronized Phase 57 runner / test / docs / context / SAW edits from this round; do not alter `D-319`, `D-317`, `D-312`, or the `D-292` research kernel.

Phase 57 (2026-03-18): First Bounded Corporate Actions Evidence Review - Evidence Only / No Promotion (D-321) 🔵

  - Decision record:
    - review the first bounded Corporate Actions packet from the actual on-disk summary / delta artifacts, publish an evidence-only disposition, and keep promotion or widening blocked absent a separate explicit approval packet.
  - The Decision (Hardcoded):
    - `data/processed/phase57_corporate_actions_summary.json` and `data/processed/phase57_corporate_actions_delta_vs_c3.csv` are the authoritative artifacts for this review.
    - `strategy_id = PHASE57_CORP_ACTIONS_CASH_YIELD_V1`, `same_engine = true`, `start_date = 2015-01-01`, `end_date = 2022-12-31`, and `max_date = 2022-12-31` remain the repo-truth identifiers for the first bounded packet.
    - the reviewed strategic deltas are `sharpe_delta = -0.240802877903895`, `cagr_delta = -0.06114407302135216`, `turnover_ratio_phase57_vs_c3 = 0.7061967047220717`, `max_dd_delta = 0.013356997284943994`, and `ulcer_delta = 7.955780751115013`.
    - `D-319` remains the only execution authorization consumed in this phase so far; `D-321` is a review / hold packet only and does not widen the Phase 57 surface.
    - no promotion language, inferred comparator verdict, or additional execution authority is authorized in `D-321`.
  - Evidence:
    - `data/processed/phase57_corporate_actions_summary.json` remains the authoritative summary surface for the first bounded packet.
    - `data/processed/phase57_corporate_actions_evidence.csv` remains the co-published daily evidence surface referenced by the summary artifact.
    - `data/processed/phase57_corporate_actions_delta_vs_c3.csv` remains the authoritative same-window / same-cost comparator surface versus `C3_LEAKY_INTEGRATOR_V1`.
    - `docs/phase_brief/phase57-brief.md` is updated to the review / hold state and `docs/context/current_context.md` / `docs/context/current_context.json` are refreshed from that SSOT.
  - Contract lock:
    - `Phase57_D321_Review := VALID iff (review wording cites only fields present in phase57_corporate_actions_summary.json or phase57_corporate_actions_delta_vs_c3.csv) and (no promotion or widening language is introduced)`.
    - `if future comparator or additional Phase 57 execution is proposed -> require a new explicit approval packet; D-321 is not that approval`.
  - Open risks:
    - the first bounded Corporate Actions packet remains below C3 on Sharpe and CAGR, so follow-up work is not automatically authorized from this review.
  - Rollback note:
    - revert only this `D-321` entry plus the synchronized Phase 57 brief / context / lesson / SAW edits if leadership amends the review wording; do not alter the `D-320` evidence artifacts, `D-319`, `D-317`, `D-312`, or the `D-292` research kernel.

Phase 57 (2026-03-18): Closeout - Evidence Only / No Promotion / No Widening (D-322) 🟢

  - Decision record:
    - close Phase 57 as evidence-only / no promotion / no widening while preserving the bounded Corporate Actions surface and all prior locks.
  - The Decision (Hardcoded):
    - Phase 57 is closed; no promotion, widening, or new Corporate Actions execution is authorized.
    - `data/processed/phase57_corporate_actions_summary.json`, `data/processed/phase57_corporate_actions_evidence.csv`, and `data/processed/phase57_corporate_actions_delta_vs_c3.csv` remain the SSOT artifacts for Phase 57.
    - any follow-up Phase 57 work requires a new explicit approval packet.
  - Evidence:
    - full regression: `.venv\Scripts\python -m pytest -q` -> PASS (see `docs/context/e2e_evidence/phase57_closeout_full_pytest_20260318.*`).
    - runtime smoke: `.venv\Scripts\python launch.py --help` -> PASS (see `docs/context/e2e_evidence/phase57_launch_smoke_20260318.*`).
    - bounded replay: `.venv\Scripts\python scripts/phase57_corporate_actions_runner.py --start-date 2015-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0 --summary-path docs\context\e2e_evidence\phase57_corporate_actions_replay_summary_20260318.json --evidence-path docs\context\e2e_evidence\phase57_corporate_actions_replay_evidence_20260318.csv --delta-path docs\context\e2e_evidence\phase57_corporate_actions_replay_delta_vs_c3_20260318.csv`.
    - reviewer-B bounded replay: `.venv\Scripts\python scripts/phase57_corporate_actions_runner.py --start-date 2015-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0 --summary-path docs\context\e2e_evidence\phase57_corporate_actions_replay_revb_summary_20260318.json --evidence-path docs\context\e2e_evidence\phase57_corporate_actions_replay_revb_evidence_20260318.csv --delta-path docs\context\e2e_evidence\phase57_corporate_actions_replay_revb_delta_vs_c3_20260318.csv`.
  - Contract lock:
    - `Phase57 := CLOSED iff (D-322 published) and (context packet refreshed) and (SSOT artifacts unchanged)`.
    - `if future Phase 57 work is proposed -> require a new explicit approval packet; D-322 is not an execution grant`.
  - Open risks:
    - the bounded packet remains below C3 on Sharpe and CAGR; therefore Phase 57 closes as no-promotion evidence only.
  - Rollback note:
    - revert only this `D-322` entry plus the synchronized Phase 57 closeout docs/context/SAW edits; do not alter the `D-320` evidence artifacts, `D-319`, `D-317`, `D-312`, or the `D-292` research kernel.

Phase 58 (2026-03-18): Planning-Only Kickoff - Governance Layer (D-323) 🔵

  - Decision record:
    - open Phase 58 as a docs-only planning surface for Governance Layer work; execution and any optional prior-phase follow-up remain blocked until separate explicit approval packets are issued.
  - The Decision (Hardcoded):
    - Phase 58 is now active for planning only.
    - `active_phase = 58` becomes the repo SSOT label only after this kickoff packet is published and the context packet is refreshed.
    - Phase 57 remains closed and immutable under `D-322`; `data/processed/phase57_corporate_actions_summary.json`, `data/processed/phase57_corporate_actions_evidence.csv`, and `data/processed/phase57_corporate_actions_delta_vs_c3.csv` remain permanent SSOT.
    - Phase 56 remains closed and immutable under `D-317`; Phase 55 remains closed and immutable under `D-312`; the Phase 53 research kernel remains read-only and immutable under `D-292`.
    - no Phase 58 implementation, evidence generation, or production promotion is authorized in this round.
    - Phase 58 execution requires a future explicit approval packet and the exact token `approve next phase`.
  - Evidence:
    - `docs/phase_brief/phase53-brief.md` roadmap bullet -> `Phase 58 - Governance Layer`.
    - `docs/phase_brief/phase58-brief.md` publishes the planning-only boundary and governance-hook inventory.
    - `docs/handover/phase58_kickoff_memo_20260318.md` publishes the PM-facing kickoff memo.
  - Contract lock:
    - `Phase58 := PLANNING_ONLY iff (D-323 published) and (context packet refreshed) and (NextPhaseApproval == PENDING)`.
    - `if future Phase 58 work is proposed -> require a separate explicit execution approval packet; D-323 is not an execution grant`.
  - Open risks:
    - none.
  - Rollback note:
    - revert only this `D-323` entry plus the synchronized Phase 58 planning docs/context/SAW edits if leadership amends wording; do not alter `D-322`, the bounded Phase 57 artifacts, `D-317`, `D-312`, or the `D-292` research kernel.

Confirmation (2026-03-18): Clean D-322 / D-323 SSOT Revalidation

  - Confirmation record:
    - confirm the cleaned Phase 57 `D-322` closeout and Phase 58 `D-323` planning-only kickoff packet after removal of the unauthorized helper artifact and scrubbing of unrelated warning references from the current-round closeout surface.
  - The Confirmation (Hardcoded):
    - `D-322` remains authoritative and unchanged in substance: Phase 57 is `CLOSED` as evidence-only / no promotion / no widening.
    - `D-323` remains authoritative and unchanged in substance: Phase 58 is `PLANNING_ONLY`, `active_phase = 58`, and `NextPhaseApproval = PENDING`.
    - `D-284` through `D-323` plus `RESEARCH_MAX_DATE = 2022-12-31` remain immutable SSOT.
    - no new execution authority is created by this confirmation entry.
  - Evidence:
    - cleaned closeout brief: `docs/phase_brief/phase57-brief.md`.
    - cleaned kickoff brief: `docs/phase_brief/phase58-brief.md`.
    - cleaned closeout handover: `docs/handover/phase57_handover.md`.
    - cleaned kickoff memo: `docs/handover/phase58_kickoff_memo_20260318.md`.
    - cleaned SAW packet: `docs/saw_reports/saw_phase57_d322_closeout_phase58_d323_kickoff_20260318.md`.
    - full regression rerun: `docs/context/e2e_evidence/phase57_closeout_full_pytest_20260318.status.txt`.
    - terminal context validation: `docs/context/e2e_evidence/phase58_context_validate_20260318.status.txt`.
  - Contract lock:
    - `Phase57_D322_Confirmed := 1[(phase57_status = CLOSED) and (phase57_artifacts_unchanged = 1)]`.
    - `Phase58_D323_Confirmed := 1[(active_phase = 58) and (phase58_status = PLANNING_ONLY) and (NextPhaseApproval = PENDING)]`.
  - Open risks:
    - none.
  - Rollback note:
    - revert only this clean confirmation entry plus synchronized context refresh if leadership amends wording; do not alter `D-322`, `D-323`, the bounded Phase 57 artifacts, `D-317`, `D-312`, or the `D-292` research kernel.

Phase 58 (2026-03-18): Bounded Execution Authorization - Governance Layer (D-324) 🟢

  - Decision record:
    - consume the exact in-thread token `approve next phase` and authorize the bounded Phase 58 Governance Layer first evidence packet on the locked Phase 53 surface only.
  - The Decision (Hardcoded):
    - Phase 58 execution is now active for the first bounded Governance Layer packet only.
    - `NextPhaseApproval = APPROVED` for the first bounded Phase 58 packet only.
    - the bounded packet must stay on the same `2015-01-01 -> 2022-12-31`, `5.0` bps, same-`core.engine.run_simulation` path as the locked Phase 54 C3 baseline where comparator evidence applies.
    - the bounded packet may normalize the comparable event-sleeve family only and may carry Phase 55 allocator governance as `reference_only`; it may not invent cross-family comparability or a post-2022 audit surface.
    - the Phase 53 research kernel remains read-only and immutable under `D-292`.
    - no production promotion, loader reopen, post-2022 expansion, or non-Phase-58 execution is authorized in `D-324`.
  - Evidence:
    - exact approval token consumed in-thread on 2026-03-18: `approve next phase`.
    - `docs/phase_brief/phase53-brief.md` roadmap bullet -> `Phase 58 - Governance Layer`.
    - `data/processed/phase54_core_sleeve_summary.json` -> `baseline_config_id = C3_LEAKY_INTEGRATOR_V1`, `window = 2015-01-01 -> 2022-12-31`, `cost_bps = 5.0`.
  - Contract lock:
    - `Phase58_D324_Exec := APPROVED iff (exact token consumed) and (window = 2015-01-01 -> 2022-12-31) and (cost_bps = 5.0) and (same engine path = core.engine.run_simulation)`.
    - `if future Phase 58 work is proposed -> require a new explicit review packet; D-324 is not open-ended execution authority`.
  - Open risks:
    - none.
  - Rollback note:
    - revert only this `D-324` entry plus the synchronized Phase 58 execution-authorization docs/context/SAW edits if leadership amends wording; do not alter `D-322`, `D-317`, `D-312`, or the `D-292` research kernel.

Phase 58 (2026-03-18): First Bounded Governance Evidence Review - Evidence Only / No Promotion / No Widening (D-325) 🔵

  - Decision record:
    - review the first bounded Governance Layer packet from the on-disk summary / evidence / delta artifacts, publish an evidence-only disposition, and keep promotion or widening blocked absent a separate explicit review packet.
  - The Decision (Hardcoded):
    - `data/processed/phase58_governance_summary.json`, `data/processed/phase58_governance_evidence.csv`, and `data/processed/phase58_governance_delta_vs_c3.csv` are the authoritative artifacts for this review.
    - `packet_id = PHASE58_GOVERNANCE_EVENT_LAYER_V1`, `same_window_same_cost_same_engine = true`, `start_date = 2015-01-01`, `end_date = 2022-12-31`, and `max_date = 2022-12-31` remain the repo-truth identifiers for the first bounded packet.
    - the bounded packet covers the comparable event-sleeve family only (`phase56_event_pead`, `phase57_event_corporate_actions`) and carries `phase55_allocator_reference` as `reference_only`.
    - the reviewed family-level governance metrics are `event_family_effective_n_trials = 2.0`, `event_family_spa_p = 0.066`, and `event_family_wrc_p = 0.086`.
    - the reviewed sleeve-level strategic deltas are:
      - `phase56_event_pead`: `sharpe_delta = 0.14556879675273404`, `cagr_delta = 0.01916021094987319`, `dsr = 0.9307882752239804`.
      - `phase57_event_corporate_actions`: `sharpe_delta = -0.240802877903895`, `cagr_delta = -0.06114407302135216`, `dsr = 1.2775341238946346e-41`.
    - `D-324` remains the only execution authorization consumed in this phase so far; `D-325` is a review / hold packet only and does not widen the Phase 58 surface.
    - no promotion language, inferred post-2022 audit completion, or additional execution authority is authorized in `D-325`.
  - Evidence:
    - `data/processed/phase58_governance_summary.json` remains the authoritative summary surface for the first bounded packet.
    - `data/processed/phase58_governance_evidence.csv` remains the authoritative normalized evidence surface for the comparable sleeves plus the allocator reference row.
    - `data/processed/phase58_governance_delta_vs_c3.csv` remains the authoritative same-window / same-cost comparator surface versus `C3_LEAKY_INTEGRATOR_V1`.
    - `docs/phase_brief/phase58-brief.md` is updated to the review / hold state and `docs/context/current_context.md` / `docs/context/current_context.json` are refreshed from that SSOT.
  - Contract lock:
    - `Phase58_D325_Review := VALID iff (review wording cites only fields present in phase58_governance_summary.json, phase58_governance_evidence.csv, or phase58_governance_delta_vs_c3.csv) and (no promotion or widening language is introduced)`.
    - `if future promotion, widening, or additional Phase 58 execution is proposed -> require a new explicit review packet; D-325 is not that approval`.
  - Open risks:
    - the family-level `SPA/WRC` remain above `0.05`, and the Phase 57 sleeve remains below the locked C3 baseline on Sharpe / CAGR, so the first bounded packet remains evidence-only.
  - Rollback note:
    - revert only this `D-325` entry plus the synchronized Phase 58 brief / context / lesson / SAW edits if leadership amends the review wording; do not alter the `D-324` evidence artifacts, `D-322`, `D-317`, `D-312`, or the `D-292` research kernel.

Phase 58 (2026-03-18): Closeout - Evidence Only / No Promotion / No Widening (D-326) 🟢

  - Decision record:
    - close Phase 58 as evidence-only / no promotion / no widening while preserving the bounded Governance Layer surface and all prior locks.
  - The Decision (Hardcoded):
    - Phase 58 is closed; no promotion, widening, or new Governance Layer execution is authorized.
    - `data/processed/phase58_governance_summary.json`, `data/processed/phase58_governance_evidence.csv`, and `data/processed/phase58_governance_delta_vs_c3.csv` remain the SSOT artifacts for Phase 58.
    - any follow-up Phase 58 work requires a new explicit review packet.
  - Evidence:
    - full regression: `.venv\Scripts\python -m pytest -q` -> PASS (see `docs/context/e2e_evidence/phase58_full_pytest_20260318.*`).
    - runtime smoke: `.venv\Scripts\python launch.py --help` -> PASS (see `docs/context/e2e_evidence/phase58_launch_smoke_20260318.*`).
    - bounded replay: `.venv\Scripts\python scripts/phase58_governance_runner.py --start-date 2015-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0 --summary-path docs\context\e2e_evidence\phase58_governance_replay_summary_20260318.json --evidence-path docs\context\e2e_evidence\phase58_governance_replay_evidence_20260318.csv --delta-path docs\context\e2e_evidence\phase58_governance_replay_delta_vs_c3_20260318.csv`.
    - reviewer-B bounded replay: `.venv\Scripts\python scripts/phase58_governance_runner.py --start-date 2015-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0 --summary-path docs\context\e2e_evidence\phase58_governance_replay_revb_summary_20260318.json --evidence-path docs\context\e2e_evidence\phase58_governance_replay_revb_evidence_20260318.csv --delta-path docs\context\e2e_evidence\phase58_governance_replay_revb_delta_vs_c3_20260318.csv`.
  - Contract lock:
    - `Phase58 := CLOSED iff (D-326 published) and (context packet refreshed) and (SSOT artifacts unchanged)`.
    - `if future Phase 58 work is proposed -> require a new explicit review packet; D-326 is not an execution grant`.
  - Open risks:
    - the bounded packet remains mixed (`event_family_spa_p = 0.066`, `event_family_wrc_p = 0.086`; Phase 57 remains below C3 on Sharpe / CAGR), so Phase 58 closes as no-promotion evidence only.
  - Rollback note:
    - revert only this `D-326` entry plus the synchronized Phase 58 closeout docs/context/SAW edits; do not alter the `D-324` evidence artifacts, `D-322`, `D-317`, `D-312`, or the `D-292` research kernel.

Phase 59 (2026-03-18): Planning-Only Kickoff - Shadow Portfolio (D-327) 🔵

  - Decision record:
    - open Phase 59 as a docs-only planning surface for Shadow Portfolio work; execution and any optional prior-phase follow-up remain blocked until separate explicit approval packets are issued.
  - The Decision (Hardcoded):
    - Phase 59 is now active for planning only.
    - `active_phase = 59` becomes the repo SSOT label only after this kickoff packet is published and the context packet is refreshed.
    - Phase 58 remains closed and immutable under `D-326`; `data/processed/phase58_governance_summary.json`, `data/processed/phase58_governance_evidence.csv`, and `data/processed/phase58_governance_delta_vs_c3.csv` remain permanent SSOT.
    - Phase 57 remains closed and immutable under `D-322`; Phase 56 remains closed and immutable under `D-317`; Phase 55 remains closed and immutable under `D-312`; the Phase 53 research kernel remains read-only and immutable under `D-292`.
    - no Phase 59 implementation, evidence generation, or production promotion is authorized in this round.
    - Phase 59 execution requires a future explicit approval packet and the exact token `approve next phase`.
  - Evidence:
    - `docs/phase_brief/phase53-brief.md` roadmap bullet -> `Phase 59 - Shadow Portfolio`.
    - `docs/phase_brief/phase59-brief.md` publishes the planning-only boundary and hook inventory.
    - `docs/handover/phase59_kickoff_memo_20260318.md` publishes the PM-facing kickoff memo.
  - Contract lock:
    - `Phase59 := PLANNING_ONLY iff (D-327 published) and (context packet refreshed) and (NextPhaseApproval == PENDING)`.
    - `if future Phase 59 work is proposed -> require a separate explicit execution approval packet; D-327 is not an execution grant`.
  - Open risks:
    - none.
  - Rollback note:
    - revert only this `D-327` entry plus the synchronized Phase 59 planning docs/context/SAW edits if leadership amends wording; do not alter `D-326`, the bounded Phase 58 artifacts, `D-322`, `D-317`, `D-312`, or the `D-292` research kernel.

Phase 59 (2026-03-18): Bounded Execution Authorization - Shadow Portfolio (D-328) 🟢

  - Decision record:
    - consume the exact in-thread token `approve next phase` and authorize the bounded Phase 59 Shadow Portfolio first evidence packet on the locked read-only research + historical shadow surface only.
  - The Decision (Hardcoded):
    - Phase 59 execution is now active for the first bounded Shadow Portfolio packet only.
    - `NextPhaseApproval = APPROVED` for the first bounded Phase 59 packet only.
    - the research-side packet must stay on the locked `2015-01-01 -> 2022-12-31`, `5.0` bps, same-window / same-cost / same-engine comparator discipline where comparator evidence applies.
    - `research_data/catalog.duckdb` and the `allocator_state` cube remain read-only and immutable under `D-292`.
    - historical `phase50_shadow_ship` artifacts may be cited as explicit reference-only context and must not be rewritten here.
    - no production promotion, no stable shadow stack execution, no post-2022 expansion, no loader/kernel reopen, and no non-Phase-59 execution are authorized in `D-328`.
  - Evidence:
    - exact approval token consumed in-thread on 2026-03-18: `approve next phase`.
    - `docs/phase_brief/phase59-brief.md` updated to `EXECUTING` with the bounded Shadow Portfolio scope.
    - `docs/phase_brief/phase53-brief.md` roadmap bullet -> `Phase 59 - Shadow Portfolio`.
  - Contract lock:
    - `phase59_execution_authorized = 1[(reply contains exact 'approve next phase') and (NextPhaseApproval == APPROVED)]`.
    - `Phase59 := EXECUTING iff (D-328 published) and (context packet refreshed) and (scope remains read-only Shadow NAV / alert only)`.
  - Open risks:
    - none.
  - Rollback note:
    - revert only this `D-328` entry plus the synchronized Phase 59 execution-authorization docs/context/SAW edits if leadership amends wording; do not alter `D-327`, `D-326`, prior-sleeve SSOT artifacts, or the `D-292` research kernel.

Phase 59 (2026-03-18): First Bounded Shadow NAV / Alert Evidence Review - Evidence Only / No Promotion / No Widening (D-329) 🔵

  - Decision record:
    - review the first bounded Phase 59 Shadow Portfolio packet against the actual on-disk summary / evidence / delta schema, publish an evidence-only disposition, and keep promotion or widening blocked absent a separate explicit review packet.
  - The Decision (Hardcoded):
    - `data/processed/phase59_shadow_summary.json` is the authoritative summary artifact for this packet.
    - the authoritative review fields currently under assessment are `packet_id = PHASE59_SHADOW_MONITOR_V1`, `same_window_same_cost_same_engine = true`, `selected_variant.variant_id = v_3516a4bd6b65`, `selected_variant.sharpe = -0.8036313887871052`, `selected_variant.cagr = -0.05889864053976657`, `selected_variant.max_dd = -0.4151519743100388`, `selected_variant.ulcer = 31.866947767982605`, `shadow_reference.alert_level = RED`, `shadow_reference.holdings_overlap = 0.0`, `shadow_reference.gross_exposure_delta = 0.9999999999999998`, and `shadow_reference.turnover_delta_rel = 0.0019000000000000006`.
    - `data/processed/phase59_shadow_evidence.csv` remains the authoritative daily evidence surface for the research lane plus the reference-only Phase 50 curve lane.
    - `data/processed/phase59_shadow_delta_vs_c3.csv` remains the authoritative structural comparator / alert surface for this bounded packet.
    - no invented unified holdings surface, promotion language, or widening language is authorized in `D-329` because the on-disk artifacts do not publish such a disposition.
    - `D-328` remains the only execution authorization consumed in this phase so far; `D-329` is a review / hold packet only and does not widen the Phase 59 surface.
  - Evidence:
    - `data/processed/phase59_shadow_summary.json` -> `review_hold = true`, `review_hold_reasons = [phase59_shadow_research_sharpe_delta < 0, phase59_shadow_research_cagr_delta < 0, phase50_shadow_reference_alert_level = RED]`.
    - `data/processed/phase59_shadow_evidence.csv` publishes `phase59_shadow_research` and `phase50_shadow_reference` rows as separate lanes.
    - `data/processed/phase59_shadow_delta_vs_c3.csv` -> `phase59_shadow_research.sharpe_delta = -1.2836914115505547`, `phase59_shadow_research.cagr_delta = -0.14905579651624656`, `phase50_shadow_reference_alerts.alert_level = RED`.
    - `docs/phase_brief/phase59-brief.md` is updated to the review / hold state and `docs/context/current_context.md` / `docs/context/current_context.json` are refreshed from that SSOT.
  - Contract lock:
    - `Phase59_D329_Review := VALID iff (review wording cites only fields present in phase59_shadow_summary.json, phase59_shadow_evidence.csv, or phase59_shadow_delta_vs_c3.csv) and (no promotion or widening language is introduced)`.
    - `if future promotion, widening, stable shadow execution, or post-2022 work is proposed -> require a new explicit review packet; D-329 is not that approval`.
  - Open risks:
    - the research lane remains below the locked C3 baseline on Sharpe / CAGR and the reference-only alert lane is `RED`, so the first bounded packet remains evidence-only.
  - Rollback note:
    - revert only this `D-329` entry plus the synchronized Phase 59 brief/context/lesson/SAW edits if leadership amends the review wording; do not alter `D-328`, `D-327`, `D-326`, prior-sleeve SSOT artifacts, or the `D-292` research kernel.

Phase 59 (2026-03-18): Closeout - Evidence Only / No Promotion / No Widening (D-330) 🟢

  - Decision record:
    - close Phase 59 as evidence-only / no promotion / no widening while preserving the bounded Shadow Portfolio surface and all prior locks.
  - The Decision (Hardcoded):
    - Phase 59 is closed; no promotion, widening, stable shadow execution, or new Shadow Portfolio work is authorized.
    - `data/processed/phase59_shadow_summary.json`, `data/processed/phase59_shadow_evidence.csv`, and `data/processed/phase59_shadow_delta_vs_c3.csv` remain the SSOT artifacts for Phase 59.
    - any follow-up Phase 59 work or any Phase 60 work requires a new explicit approval packet.
  - Evidence:
    - focused tests: `.venv\Scripts\python -m pytest tests\test_phase59_shadow_portfolio.py tests\test_shadow_portfolio_view.py tests\test_release_controller.py -q` -> PASS (see `docs/context/e2e_evidence/phase59_targeted_tests_20260318.*`).
    - full regression: `.venv\Scripts\python -m pytest -q` -> PASS (see `docs/context/e2e_evidence/phase59_full_pytest_20260318.*`).
    - runtime smoke: `.venv\Scripts\python launch.py --help` -> PASS (see `docs/context/e2e_evidence/phase59_launch_smoke_20260318.*`).
    - bounded replay: `.venv\Scripts\python scripts/phase59_shadow_portfolio_runner.py --start-date 2015-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0 --summary-path docs\context\e2e_evidence\phase59_shadow_replay_summary_20260318.json --evidence-path docs\context\e2e_evidence\phase59_shadow_replay_evidence_20260318.csv --delta-path docs\context\e2e_evidence\phase59_shadow_replay_delta_vs_c3_20260318.csv` -> PASS.
    - reviewer-B bounded replay: `.venv\Scripts\python scripts/phase59_shadow_portfolio_runner.py --start-date 2015-01-01 --end-date 2022-12-31 --max-date 2022-12-31 --cost-bps 5.0 --summary-path docs\context\e2e_evidence\phase59_shadow_replay_revb_summary_20260318.json --evidence-path docs\context\e2e_evidence\phase59_shadow_replay_revb_evidence_20260318.csv --delta-path docs\context\e2e_evidence\phase59_shadow_replay_revb_delta_vs_c3_20260318.csv` -> PASS.
    - PM handover: `docs/handover/phase59_handover.md`.
    - context refresh: `.venv\Scripts\python scripts/build_context_packet.py` and `.venv\Scripts\python scripts/build_context_packet.py --validate` -> PASS.
  - Contract lock:
    - `Phase59 := CLOSED iff (D-330 published) and (context packet refreshed) and (SSOT artifacts unchanged)`.
    - `if future Phase 59 or Phase 60 work is proposed -> require a new explicit approval packet; D-330 is not an execution grant`.
  - Open risks:
    - the bounded packet remains mixed (`selected_variant.sharpe < sharpe_c3`, `selected_variant.cagr < cagr_c3`; `shadow_reference.alert_level = RED`), so Phase 59 closes as no-promotion evidence only.
  - Rollback note:
    - revert only this `D-330` entry plus the synchronized Phase 59 closeout docs/context/SAW edits; do not alter `D-329`, `D-328`, `D-327`, prior-sleeve SSOT artifacts, or the `D-292` research kernel.

Phase 60 (2026-03-18): Planning-Only Kickoff - Stable Shadow Portfolio (D-331) 🔵

  - Decision record:
    - open Phase 60 as a docs-only planning surface for the Stable Shadow Portfolio roadmap item, lock the four planning contracts, and keep all implementation, post-2022 audit execution, and production promotion blocked pending a separate explicit approval token.
  - The Decision (Hardcoded):
    - Phase 60 is now active for planning only.
    - `active_phase = 60` becomes the repo SSOT label only after this kickoff packet is published and the context packet is refreshed.
    - Phase 59 remains closed and immutable under `D-330`; `data/processed/phase59_shadow_summary.json`, `data/processed/phase59_shadow_evidence.csv`, and `data/processed/phase59_shadow_delta_vs_c3.csv` remain permanent SSOT.
    - Phase 58 remains closed and immutable under `D-326`; Phase 57 remains closed and immutable under `D-322`; Phase 56 remains closed and immutable under `D-317`; Phase 55 remains closed and immutable under `D-312`; the Phase 53 research kernel remains read-only and immutable under `D-292`.
    - no Phase 60 implementation, no post-2022 audit execution, no code/evidence mutation, no `research_data/` mutation, no kernel reopen, and no production promotion are authorized in this round.
    - the Phase 60 planning brief must lock these four planning contracts exactly:
      - unified comparator surface = `Option B`: a governed daily holdings / weights cube built from sleeves plus allocator surfaces, with legacy `phase50_shadow_ship` artifacts remaining `reference_only` and excluded from governed comparator metrics.
      - governed cost policy = `Option C`: `5.0` bps is the only gating comparator basis for same-window / same-cost evidence continuity; `10.0` bps is mandatory sensitivity-only evidence and is non-gating unless a later decision re-locks the basis.
      - post-2022 audit spec = `Option A`: one integrated audit only, with mandatory preflight checks and kill switches defined before any holdout run is authorized.
      - allocator carry-forward = `Option C`: allocator rows may exist in the planning cube, but allocator carry-forward is excluded from the governed book until research eligibility clears on the locked gate family.
    - Phase 60 implementation requires a future explicit approval packet and the exact token `approve next phase`.
  - Evidence:
    - `docs/phase_brief/phase53-brief.md` roadmap bullet -> `Phase 60 - Stable Shadow Portfolio`.
    - `docs/phase_brief/phase60-brief.md` publishes the planning-only boundary and locks the four planning contracts.
    - `docs/handover/phase60_kickoff_memo_20260318.md` publishes the PM-facing kickoff memo.
    - `docs/context/bridge_contract_current.md` is refreshed to the Phase 60 planning-only state.
  - Contract lock:
    - `Phase60 := PLANNING_ONLY iff (D-331 published) and (context packet refreshed) and (NextPhaseApproval == PENDING)`.
    - `if future Phase 60 work is proposed -> require a separate explicit implementation approval packet; D-331 is not an execution grant`.
  - Open risks:
    - the family-level `SPA/WRC` remain above `0.05`, the Phase 54 core sleeve remains below promotion readiness (`gates_passed = 4/6`, `rule100_pass_rate = 0.10132320319432121`), the current allocator-selected variant remains negative on Sharpe / CAGR, and the post-2022 holdout seal has not yet been opened.
  - Rollback note:
    - revert only this `D-331` entry plus the synchronized Phase 60 planning docs/context/lesson/SAW edits if leadership amends wording; do not alter `D-330`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 60 (2026-03-18): Complete Institutional Pivot Planning Snapshot (D-332) 🔵

  - Decision record:
    - incorporate the Complete Institutional Pivot snapshot into Phase 60 planning as the first deliverable, lock validator fix as Priority #1, confirm Method B as the planning default for S&P 500 Pro / Moody's B&D sidecars, and tie this snapshot explicitly to the unified governed surface contract already approved in D-331.
  - The Decision (Hardcoded):
    - the next data milestone is "Complete Institutional Pivot" on the already-in-place PIT-clean CRSP/Compustat 2000-2024 bedrock with zero from-scratch replacement required.
    - operational validator failures (14-day feature freshness gap + 2 zombie snapshot rows) must be cleared immediately per industry standard before any reliable pipeline testing.
    - S&P 500 Pro / Moody's B&D designation is resolved at 92/100 confidence by preferred Method B: isolated Parquet sidecars joined only at view level (exactly like Osiris) to protect the governed core updater schema and enable parallel deep-credit/factor testing.
    - no expert delegation is required; Method B is the right planning default with no low-certainty gaps remaining.
    - the hybrid institutional lake distinguishes CRSP/Compustat (PIT-clean 2000-2024 bedrock, governed core) from Osiris (isolated Parquet sidecar, view-layer join only) and S&P/Moody's (Method B preferred: isolated Parquet sidecars, view-layer join) without opening any false-premise milestone.
    - Yahoo sidecars remain separate from the institutional lake.
    - out-of-boundary ingestion keys/schema mappings that violate the governed core updater schema are flagged and blocked from any execution at 100/100 confidence.
    - Phase 60 planning deliverables are locked: (1) validator fix (14-day freshness gap + 2 zombie snapshot rows) as Priority #1, (2) Method B preference locked for S&P/Moody's sidecars, (3) out-of-boundary ingestion block enforced.
    - D-284 through D-331 remain immutable; RESEARCH_MAX_DATE = 2022-12-31 remains in force; no code/evidence/execution surface changes during planning; prior SSOT artifacts remain unchanged.
  - Evidence:
    - `docs/phase_brief/phase60-brief.md` section 0.5 publishes the Complete Institutional Pivot planning snapshot verbatim.
    - `docs/context/current_context.md` and `docs/context/current_context.json` are refreshed to reflect planning-only state with validator fix as deliverable #1.
    - `docs/context/bridge_contract_current.md` is refreshed to the Phase 60 planning-only state with D-332 authority.
  - Contract lock:
    - `Phase60_Institutional_Pivot := PLANNING_ONLY iff (D-332 published) and (validator fix Priority #1) and (Method B locked) and (out-of-boundary block enforced) and (context packet refreshed)`.
    - `if future Phase 60 implementation is proposed -> validator PASS is mandatory before any sidecar testing or data-milestone execution path opens`.
  - Open risks:
    - the 14-day feature freshness gap and 2 zombie snapshot rows remain uncleared; validator PASS is the critical blocker for any reliable pipeline testing.
  - Rollback note:
    - revert only this `D-332` entry plus the synchronized Phase 60 planning docs/context edits if leadership amends wording; do not alter `D-331`, `D-330`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 59 (2026-03-18): Reopened Monitoring Refresh - Evidence Only / No Promotion / No Widening (D-333) 🟢

  - Decision record:
    - reopen Phase 59 narrowly for a monitoring-only refresh over the existing bounded Shadow Portfolio surface, using the existing read-only `phase59_*` packet plus Catalyst Radar-style runtime filtering on `holdings_overlap`, `gross_exposure_delta`, and `turnover_delta_rel` through the already-present D-328 sidecar joins, while preserving all prior locks and keeping the disposition evidence-only / no-promotion / no-widening.
  - The Decision (Hardcoded):
    - `D-330` remains authoritative for the first bounded packet closeout, but this `D-333` packet reopens Phase 59 for a narrow monitoring-only refresh scope only.
    - no new loaders, no kernel reopen, no `research_data/` mutation, no post-2022 expansion, no production promotion, no stable shadow / multi-sleeve execution, and no widening beyond the existing `phase59_*` packet are authorized.
    - the active bounded monitoring surface remains the existing read-only `data/processed/phase59_shadow_summary.json`, `data/processed/phase59_shadow_evidence.csv`, and `data/processed/phase59_shadow_delta_vs_c3.csv` artifacts plus replay evidence emitted under `docs/context/e2e_evidence/`.
    - Catalyst Radar overlay in this packet means runtime filtering / presentation only on the already-published `holdings_overlap`, `gross_exposure_delta`, and `turnover_delta_rel` metrics; it does not create a new governed holdings surface and does not mutate the Phase 59 SSOT artifacts.
    - `dashboard.py` and `views/shadow_portfolio_view.py` remain minimal read-only enrichment surfaces only.
    - `data/processed/phase55_allocator_cpcv_evidence.json` may be cited only as a reference-only prior comparator lane; no new governed delta-vs-prior SSOT is authorized.
    - all prior locks `D-284`..`D-332`, `RESEARCH_MAX_DATE = 2022-12-31`, and same-window / same-cost / same-`core.engine.run_simulation` discipline remain preserved verbatim.
  - Evidence:
    - `docs/phase_brief/phase59-brief.md` is updated to show the reopened monitoring-only scope under `D-333` with active_phase remaining `59`.
    - `docs/handover/phase59_handover.md` and the SAW report are refreshed to document the reopened bounded monitoring refresh packet.
    - targeted pytest, launch smoke, dual replays, and context build/validate are rerun only for the bounded Phase 59 monitoring scope.
  - Contract lock:
    - `Phase59 := REOPENED_MONITORING_ONLY iff (D-333 published) and (scope remains read-only Catalyst Radar style runtime filtering on existing Phase 59 metrics) and (no new Phase 59 SSOT artifact family is introduced)`.
    - `if future Phase 59 widening, Phase 60 execution, or governed surface expansion is proposed -> require a separate explicit approval packet; D-333 is not that authority`.
  - Open risks:
    - none in the bounded reopened scope; the packet remains evidence-only / no-promotion / no-widening by construction.
  - Rollback note:
    - revert only this `D-333` entry plus the synchronized reopened Phase 59 docs/context/SAW edits if leadership amends wording; do not alter `D-332`, `D-331`, `D-330`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 59 (2026-03-18): Closeout After Reopened Monitoring Refresh - Evidence Only / No Promotion / No Widening (D-334) 🟢

  - Decision record:
    - close the narrow `D-333` reopened monitoring-only packet as complete, preserve the bounded Catalyst Radar sidecar overlay as runtime filtering / presentation only, and return Phase 59 to a closed evidence-only / no-promotion / no-widening state.
  - The Decision (Hardcoded):
    - Phase 59 is closed again under `D-334`; the reopened `D-333` monitoring packet is complete and no further Phase 59 work is authorized absent a separate explicit approval packet.
    - the bounded Catalyst Radar sidecar overlay is complete via read-only runtime filtering on the already-published `holdings_overlap`, `gross_exposure_delta`, and `turnover_delta_rel` metrics only.
    - no new loaders, no kernel reopen, no `research_data/` mutation, no post-2022 expansion, no production promotion, no stable shadow / multi-sleeve execution, and no new governed artifact family were introduced in the reopened packet.
    - the canonical Phase 59 SSOT remains `data/processed/phase59_shadow_summary.json`, `data/processed/phase59_shadow_evidence.csv`, and `data/processed/phase59_shadow_delta_vs_c3.csv`; the D-333 replay outputs under `docs/context/e2e_evidence/` are evidence-only replay artifacts and do not replace SSOT.
    - all prior locks `D-284`..`D-333`, `RESEARCH_MAX_DATE = 2022-12-31`, and same-window / same-cost / same-`core.engine.run_simulation` discipline remain preserved verbatim.
  - Evidence:
    - `docs/phase_brief/phase59-brief.md` is returned to `CLOSED` with `D-334` authority and active_phase remaining `59`.
    - `docs/handover/phase59_handover.md` and the D-334 SAW report record the reopened monitoring refresh as complete and closed.
    - the D-333 targeted pytest, launch smoke, dual replays, and context build/validate all passed before closeout.
  - Contract lock:
    - `Phase59 := CLOSED_AGAIN iff (D-334 published) and (D-333 bounded monitoring verification passed) and (no new Phase 59 governed artifact family introduced)`.
    - `if future Phase 59 widening or any Phase 60 execution is proposed -> require a separate explicit approval packet; D-334 is not that authority`.
  - Open risks:
    - none in the bounded closeout scope; the packet remains evidence-only / no-promotion / no-widening by construction.
  - Rollback note:
    - revert only this `D-334` entry plus the synchronized closeout docs/context/SAW edits if leadership amends wording; do not alter `D-333`, `D-332`, `D-331`, `D-330`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 60 (2026-03-18): Planning-Only Kickoff Refresh - Execution Blocked (D-335) 🟢

  - Decision record:
    - formally approve the `D-334` Phase 59 closeout, reactivate the active repo context at Phase 60 in planning-only mode, and preserve the previously locked Stable Shadow planning contracts without granting any implementation or evidence-generation authority.
  - The Decision (Hardcoded):
    - `D-335` makes Phase 60 the active planning context only; it does not authorize code changes, tests, replay runners, sidecar writes, holdout execution, or production promotion.
    - the Phase 60 planning boundary remains the D-331/D-332 contract set: unified governed comparator surface, governed `5.0` bps gating cost basis with `10.0` bps sensitivity lane, one-shot post-2022 audit preflight/kill-switch design, allocator carry-forward exclusion, and the Complete Institutional Pivot planning snapshot.
    - `NextPhaseApproval = PENDING` remains mandatory, and any Phase 60 implementation or evidence generation requires a later explicit approval packet containing the exact token `approve next phase`.
    - Phase 59 stays closed under `D-334`; no widening, no reopen, no new loader files, and no mutation of prior SSOT artifacts are authorized by this packet.
    - all prior locks `D-284`..`D-334`, `RESEARCH_MAX_DATE = 2022-12-31`, and same-window / same-cost / same-`core.engine.run_simulation` discipline remain preserved verbatim.
  - Evidence:
    - `docs/phase_brief/phase60-brief.md` is refreshed to `D-335` authority with execution explicitly blocked and `active_phase = 60` as the planning SSOT label.
    - `docs/handover/phase60_kickoff_memo_20260318.md`, `docs/context/bridge_contract_current.md`, and the D-335 SAW report are refreshed in the same docs-only round.
    - `docs/context/current_context.md` and `docs/context/current_context.json` are rebuilt from the Phase 60 planning source and validated without running any Phase 60 implementation or evidence command.
  - Contract lock:
    - `Phase60 := PLANNING_ONLY iff (D-335 published) and (NextPhaseApproval == PENDING) and (no execution/evidence generation authority granted)`.
    - `if future Phase 60 implementation, evidence generation, or post-2022 execution is proposed -> require a separate explicit approval packet containing exact 'approve next phase'; D-335 is not that authority`.
  - Open risks:
    - the governed daily holdings / weights cube remains a planning contract only; no implementation or holdout evidence exists yet.
  - Rollback note:
    - revert only this `D-335` entry plus the synchronized Phase 60 planning docs/context/SAW edits if leadership amends wording; do not alter `D-334`, `D-333`, `D-332`, `D-331`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 60 (2026-03-18): First Bounded Execution Authorization (D-337) 🟢

  - Decision record:
    - Consume the exact approval token to authorize only the first bounded Phase 60 implementation packet. Transition active_phase := 60 after this packet publishes and the context packet is refreshed.
  - The Decision (Hardcoded):
    - approve next phase exactly consumed.
    - Keep the four D-331 contracts locked verbatim (unified daily holdings/weight cube = Option B, governed cost = 5.0 bps gate + 10.0 bps sensitivity-only, one-shot integrated post-2022 audit = Option A with all preflight checks + kill switches, allocator carry-forward excluded until eligibility clears).
    - Validator fix (14-day freshness gap + 2 zombie snapshot rows) remains absolute Priority #1 before any deeper testing or post-2022 run.
    - Method B sidecars (isolated Parquet, view-layer join only) locked for S&P/Moody’s.
    - All prior locks (D-284…D-336, RESEARCH_MAX_DATE=2022-12-31, same-engine discipline, out-of-boundary ingestion block) preserved verbatim.
    - No promotion of Phase 54 core sleeve, no carry-forward of negative-Sharpe allocator variant, no kernel mutation, no research_data/ mutation, no post-2022 data exposure until full gates + preflights pass.
  - Evidence:
    - Run only bounded verification: `pytest -q`, launch smoke, context rebuild/validate.
    - Capture outputs under `docs/context/e2e_evidence/phase60_d337_first_packet_20260318.*`.
    - Publish updated `docs/handover/phase60_execution_handover_20260318.md`, refreshed `current_context.json` (must show active_phase=60), and new SAW report.
  - Contract lock:
    - `Phase60 := EXECUTING_BOUNDED iff (D-337 published) and (exact token consumed) and (context packet refreshed) and (validator fix flagged Priority #1) and (scope remains first bounded cube + preflight checks only)`.
    - `Any attempt to widen, run post-2022 data, or promote blocked sleeves before kill-switch preflights -> immediate rollback + governance violation`.
  - Open risks:
    - Validator fix first condition means no testing or sidecar use until the gap and zombie rows are fixed.
  - Rollback note:
    - Immediate rollback + governance violation if any attempt to widen, run post-2022 data, or promote blocked sleeves before kill-switch preflights occurs.

Phase 60 (2026-03-19): D-337 Governance Hygiene & Internal Consistency (D-338) 🟢

  - Decision record:
    - repair the internal governance artifacts for the bounded D-337 packet only: refresh the stale bridge, rewrite the D-337 SAW report into validator-clean schema, refresh the context packet, and hold any validator/code/cube start until the next explicit packet.
  - The Decision (Hardcoded):
    - `D-337` remains the sole bounded execution authorization consumed so far for Phase 60.
    - `D-338` is docs-only hygiene. It does not widen scope, it does not mutate code or evidence surfaces, and it does not start the validator fix or the unified cube build.
    - `docs/context/bridge_contract_current.md` must align to the D-337 bounded execution truth, not the stale D-335 planning-only posture.
    - `docs/saw_reports/saw_phase60_d337_first_packet_20260318.md` must be re-authored into the repo-standard SAW schema and pass `validate_saw_report_blocks.py`.
    - `docs/context/current_context.md` and `docs/context/current_context.json` must be refreshed so they preserve D-337 history while showing the D-338 hold: await the next explicit packet before any validator/code/cube work begins.
    - all prior locks `D-284`..`D-337`, `RESEARCH_MAX_DATE = 2022-12-31`, the four D-331 planning contracts, the D-332 institutional-pivot snapshot, the D-335 planning refresh, and all prior SSOT artifacts remain preserved verbatim.
  - Evidence:
    - `docs/context/bridge_contract_current.md` refreshed from stale D-335 planning-only language to D-337 bounded execution truth with D-338 hold language.
    - `docs/saw_reports/saw_phase60_d337_first_packet_20260318.md` re-authored into validator-clean schema.
    - `docs/context/e2e_evidence/phase60_d338_d337_saw_validate_20260319.txt` -> PASS.
    - `docs/context/e2e_evidence/phase60_d338_context_build_20260319.*` and `phase60_d338_context_validate_20260319.*` -> PASS.
  - Contract lock:
    - `Phase60_D338_Hygiene := VALID iff (bridge reflects D-337 truth) and (D-337 SAW validator passes) and (context packet refreshed) and (no validator/code/cube work started in this round)`.
    - `if future validator fix or bounded cube work is proposed -> require the next explicit packet after D-338; D-338 is not the release command`.
  - Open risks:
    - the validator fix (14-day freshness gap + 2 zombie snapshot rows) remains unresolved, and all code/cube work is intentionally held pending the next explicit packet.
  - Rollback note:
    - revert only this `D-338` entry plus the synchronized bridge/context/SAW/brief/lesson edits if leadership amends wording; do not alter `D-337`, `D-335`, `D-332`, `D-331`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 60 (2026-03-19): Validator Fix Priority Enforcement + Bounded Governed Cube Build (D-339) 🟢

  - Decision record:
    - execute only the bounded D-339 slice inside the already-authorized D-337 packet: inspect the exact validator failure paths, verify the validator gate to green, and publish the first governed daily holdings / weight cube on the existing read-only sleeve surfaces with allocator overlay explicitly forced to zero.
  - The Decision (Hardcoded):
    - the validator gate is now measured against the same governed price surface the feature builder actually consumes.
    - the live validator status is green: no feature-store freshness failure on the governed surface, zero zombie snapshot rows, and zero PIT violations.
    - the bounded governed cube is built only from:
      - `phase56_event_pead` reconstructed on the locked `2015-01-01 -> 2022-12-31`, `5.0` bps, read-only governed sleeve logic,
      - `phase57_event_corporate_actions` reconstructed on the locked `2015-01-01 -> 2022-12-31`, `5.0` bps, read-only governed sleeve logic.
    - allocator overlay remains `0.0` on every cube row because allocator carry-forward remains excluded until eligibility clears.
    - the blocked Phase 54 core sleeve remains excluded from the cube.
    - no post-2022 data, no kernel mutation, no `research_data/` mutation, no promotion path, and no widening beyond the bounded D-339 slice are authorized here.
    - all prior locks `D-284`..`D-338`, `RESEARCH_MAX_DATE = 2022-12-31`, same-window / same-cost / same-`core.engine.run_simulation` discipline, Contract A/B/C/D from `D-331`, and the institutional-pivot framing from `D-332` remain preserved verbatim.
  - Evidence:
    - targeted pytest for validator + cube slice: `docs/context/e2e_evidence/phase60_validator_fix_20260319_targeted_pytest.*` -> PASS.
    - full regression: `docs/context/e2e_evidence/phase60_validator_fix_20260319_full_pytest.*` -> PASS.
    - validator: `docs/context/e2e_evidence/phase60_validator_fix_20260319_validate_data_layer.txt` -> PASS.
    - bounded cube runner: `docs/context/e2e_evidence/phase60_governed_cube_20260319.*` -> PASS.
    - launch smoke: `docs/context/e2e_evidence/phase60_governed_cube_20260319_smoke.*` -> PASS.
    - governed cube artifacts:
      - `data/processed/phase60_governed_cube_summary.json`
      - `data/processed/phase60_governed_cube.csv`
      - `data/processed/phase60_governed_cube_daily.csv`
    - updated PM handover: `docs/handover/phase60_execution_handover_20260318.md`
    - refreshed context packet and D-339 SAW report published in the same round.
  - Contract lock:
    - `Phase60_D339 := VALID iff (validator = PASS) and (zombie_rows = 0) and (cube uses only phase56_event_pead + phase57_event_corporate_actions with allocator_overlay_weight = 0) and (max_date <= 2022-12-31) and (cost_bps_gate = 5.0)`.
    - `if future post-2022 work, promotion path, sidecar expansion, or widened cube execution is proposed -> require a separate explicit approval packet; D-339 is not that authority`.
  - Open risks:
    - the governed cube is still pre-audit and pre-promotion: no post-2022 evidence exists, allocator carry-forward remains blocked, and the core sleeve remains excluded.
  - Rollback note:
    - revert only this `D-339` entry plus the synchronized Phase 60 validator/cube docs/context/SAW edits if leadership amends wording; do not alter `D-338`, `D-337`, `D-335`, `D-332`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 60 (2026-03-19): Mandatory Preflight Checks + Bounded One-Shot Post-2022 Audit (D-340) 🟢

  - Decision record:
    - execute PF-01..PF-06 on the published governed cube, then run the bounded integrated post-2022 audit slice only if the preflights pass, while preserving all promotion, carry-forward, core-inclusion, and widening blocks.
  - The Decision (Hardcoded):
    - PF-01..PF-06 passed on the published `phase60_governed_cube*` artifacts.
    - the bounded audit window is `2023-01-01 -> 2024-12-31`.
    - the governed audit gate remains `5.0` bps and the separate sensitivity lane remains `10.0` bps.
    - allocator overlay remains `0.0`, allocator carry-forward remains blocked, and the core sleeve remains excluded.
    - no `phase50_shadow_ship` reference fill, no post-2022 promotion claim, no `research_data/` mutation, no kernel mutation, and no widening beyond the bounded D-340 audit slice are authorized here.
    - the audit result is `blocked` by kill switch `KS-03_same_period_c3_unavailable` because the same-period C3 comparator hit `274` missing executed-exposure return cells under strict rules.
  - Evidence:
    - preflight evidence: `docs/context/e2e_evidence/phase60_d340_preflight_20260319.*` -> PASS.
    - bounded audit evidence:
      - `data/processed/phase60_governed_audit_summary.json`
      - `data/processed/phase60_governed_audit_evidence.csv`
      - `data/processed/phase60_governed_audit_delta.csv`
      - `docs/context/e2e_evidence/phase60_d340_audit_20260319.*`
    - full regression: `docs/context/e2e_evidence/phase60_d340_full_pytest_20260319.*` -> PASS.
    - launch smoke: `docs/context/e2e_evidence/phase60_d340_audit_20260319_smoke.*` -> PASS.
  - Contract lock:
    - `Phase60_D340 := VALID iff (PF-01..PF-06 = PASS) and (audit artifacts published) and (allocator_overlay_weight = 0) and (core_sleeve_included = 0) and (audit verdict carries no promotion claim)`.
    - `if future comparator remediation, post-2022 widening, promotion path, or any further Phase 60 expansion is proposed -> require a separate explicit approval packet; D-340 is not that authority`.
  - Open risks:
    - the same-period C3 comparator is unavailable under strict missing-return rules (`274` missing executed-exposure return cells), so GATE-02 cannot clear and the audit remains blocked evidence only.
  - Rollback note:
    - revert only this `D-340` entry plus the synchronized preflight/audit docs/context/SAW edits if leadership amends wording; do not alter `D-339`, `D-338`, `D-337`, `D-335`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 60 (2026-03-19): Blocked Audit Formal Review + Evidence-Only Hold Packet (D-341) 🟢

  - Decision record:
    - formally review the immutable D-340 blocked audit packet against the four SSOT artifacts only, extract the exact `274` executed-exposure missing-return-cell root cause, and publish an evidence-only hold packet with no remediation, no widening, and no promotion authority.
  - The Decision (Hardcoded):
    - D-341 validates only:
      - `docs/context/e2e_evidence/phase60_d340_preflight_20260319_summary.json`
      - `data/processed/phase60_governed_audit_summary.json`
      - `data/processed/phase60_governed_audit_evidence.csv`
      - `data/processed/phase60_governed_audit_delta.csv`
    - the D-340 packet remains `blocked` with `kill_switches_triggered = [KS-03_same_period_c3_unavailable]`.
    - the same-period comparator remains unavailable under strict missing-return rules because it hit exactly `274` missing executed-exposure return cells.
    - the D-341 review packet publishes only evidence-only hold artifacts:
      - `docs/context/e2e_evidence/phase60_d341_review_20260319_summary.json`
      - `docs/context/e2e_evidence/phase60_d341_review_20260319_findings.csv`
      - `docs/context/e2e_evidence/phase60_d341_review_20260319.status.txt`
    - `active_phase = 60` remains unchanged, and remediation, promotion, widening, allocator carry-forward, core inclusion, `research_data/` mutation, and kernel mutation remain unauthorized.
  - Evidence:
    - D-341 review evidence:
      - `docs/context/e2e_evidence/phase60_d341_review_20260319_summary.json`
      - `docs/context/e2e_evidence/phase60_d341_review_20260319_findings.csv`
      - `docs/context/e2e_evidence/phase60_d341_review_20260319.status.txt`
    - focused regression: `docs/context/e2e_evidence/phase60_d341_review_20260319_targeted_pytest.status.txt` -> PASS.
    - full regression: `docs/context/e2e_evidence/phase60_d341_review_20260319_full_pytest.status.txt` -> PASS.
    - context refresh: `docs/context/e2e_evidence/phase60_d341_review_20260319_context_build.status.txt` -> PASS.
    - context validate: `docs/context/e2e_evidence/phase60_d341_review_20260319_context_validate.status.txt` -> PASS.
    - SAW validate: `docs/context/e2e_evidence/phase60_d341_review_20260319_saw_validate.txt` -> PASS.
    - closure validate: `docs/context/e2e_evidence/phase60_d341_review_20260319_closure_validate.txt` -> PASS.
  - Contract lock:
    - `Phase60_D341 := VALID iff (D340_preflight_passed = 1) and (D340_audit_status = blocked) and (KS-03_same_period_c3_unavailable in kill_switches_triggered) and (missing_executed_exposure_return_cells = 274) and (D341 outputs publish evidence_only_hold with all authorization flags = 0)`.
    - `if future comparator remediation, promotion path, post-2022 widening, allocator carry-forward, core inclusion, or any further Phase 60 expansion is proposed -> require a separate explicit approval packet; D-341 is not that authority`.
  - Open risks:
    - the same-period C3 comparator remains unavailable under strict missing-return rules (`274` missing executed-exposure return cells), so the audit remains evidence-only and blocked from promotion.
  - Rollback note:
    - revert only this `D-341` entry plus the synchronized review/docs/context/SAW edits if leadership amends wording; do not alter `D-340`, `D-339`, `D-338`, `D-337`, `D-335`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 60 (2026-03-19): Documentation Hygiene & Stale Language Cleanup (D-343) 🟢

  - Decision record:
    - remove the stale active-state validator-failure language from the active Phase 60 brief, refresh the bridge evidence attribution to the current execution-era handover, and preserve the bounded D-341 evidence-only hold state without changing any execution authority.
  - The Decision (Hardcoded):
    - `D-343` is docs-only hygiene. It does not authorize remediation, promotion, widening, allocator carry-forward, core inclusion, `research_data/` mutation, kernel mutation, or any further Phase 60 execution.
    - the stale Phase 60 brief block `Operational Validator Failures (Must Clear Immediately)` is removed from the active brief because the validator gate was already cleared under `D-339`.
    - the bridge `Evidence Used` reference is refreshed from the historical kickoff memo to the current execution-era handover `docs/handover/phase60_execution_handover_20260318.md`.
    - `D-341` remains the authoritative evidence-only hold packet for the blocked D-340 audit result.
  - Evidence:
    - `docs/phase_brief/phase60-brief.md` no longer presents the resolved validator issue as an active blocker.
    - `docs/context/bridge_contract_current.md` cites the current execution handover under `Evidence Used`.
    - targeted pytest, context build/validate, and SAW validation are captured under `docs/context/e2e_evidence/phase60_d343_hygiene_20260319.*`.
  - Contract lock:
    - `Phase60_D343 := VALID iff (active brief no longer contains stale resolved-validator blocker language) and (bridge evidence attribution points to current execution handover) and (D-341 hold state is otherwise unchanged)`.
    - `if future remediation, widening, promotion path, allocator carry-forward, core inclusion, or any further Phase 60 expansion is proposed -> require a separate explicit approval packet; D-343 is not that authority`.
  - Open risks:
    - none new in-scope; `D-341` remains the authoritative blocked-audit hold packet.
  - Rollback note:
    - revert only this `D-343` entry plus the synchronized brief/bridge/context/SAW/lesson edits if leadership amends wording; do not alter `D-341`, `D-340`, `D-339`, `D-338`, `D-337`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 60 (2026-03-19): Closure Path Decision + Blocked Hold Formalization (D-344) 🟢

  - Decision record:
    - formally confirm that Phase 60 is not yet on a closeout path because the D-340 same-period comparator block remains unresolved, preserve the D-341 evidence-only hold as the current active state, and publish a documentation-hygiene formalization packet with no new execution authority.
  - The Decision (Hardcoded):
    - Phase 60 is now explicitly stamped as `BLOCKED_EVIDENCE_ONLY_HOLD` in the active brief.
    - `D-344` is docs-only formalization. It does not authorize remediation, widening, promotion, allocator carry-forward, core inclusion, `research_data/` mutation, kernel mutation, or any further Phase 60 execution.
    - `D-341` remains the authoritative evidence-only hold packet over the immutable `D-340` blocked audit result.
    - the exact root cause remains unchanged: the same-period C3 comparator failed under strict missing-return rules with `274` missing executed-exposure return cells.
    - the stale resolved-validator language remains absent from the active brief, and the bridge evidence attribution remains locked to the execution-era handover.
  - Evidence:
    - `docs/phase_brief/phase60-brief.md` status is now `BLOCKED_EVIDENCE_ONLY_HOLD`.
    - `docs/context/bridge_contract_current.md` still cites `docs/handover/phase60_execution_handover_20260318.md` under `Evidence Used`.
    - targeted pytest, context build/validate, and SAW validation are captured under `docs/context/e2e_evidence/phase60_d344_hygiene_20260319.*`.
  - Contract lock:
    - `Phase60_D344 := VALID iff (phase60_brief_status = BLOCKED_EVIDENCE_ONLY_HOLD) and (stale resolved-validator language absent) and (bridge evidence attribution points to execution handover) and (D341 hold state unchanged)`.
    - `if future remediation, widening, promotion path, allocator carry-forward, core inclusion, or any further Phase 60 expansion is proposed -> require a separate explicit approval packet; D-344 is not that authority`.
  - Open risks:
    - none new in-scope; the D-341 blocked-audit hold remains the authoritative Phase 60 state.
  - Rollback note:
    - revert only this `D-344` entry plus the synchronized brief/bridge/context/SAW/lesson edits if leadership amends wording; do not alter `D-343`, `D-341`, `D-340`, `D-339`, `D-338`, `D-337`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 60 (2026-03-19): Formal Evidence-Only Closeout as Blocked Hold Packet (D-345) 🟢

  - Decision record:
    - formally close Phase 60 as a blocked evidence-only hold, preserving the immutable D-340 blocked audit result and the D-341 review root cause, while granting no remediation, no widening, no promotion, and no Phase 61+ authority.
  - The Decision (Hardcoded):
    - Phase 60 is formally closed as `CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD`.
    - the exact blocked root cause remains unchanged and must be preserved verbatim:
      - same-period C3 comparator unavailable under strict missing-return rules,
      - `274` missing executed-exposure return cells,
      - `kill_switches_triggered = [KS-03_same_period_c3_unavailable]`.
    - `D-345` is docs-only closeout. It does not authorize remediation, widening, promotion, allocator carry-forward, core inclusion, `research_data/` mutation, kernel mutation, or any Phase 61+ scope.
    - all prior locks `D-284`..`D-344`, `RESEARCH_MAX_DATE = 2022-12-31`, same-window / same-cost / same-`core.engine.run_simulation` discipline, and the four D-331 planning contracts remain preserved verbatim.
  - Evidence:
    - `docs/phase_brief/phase60-brief.md` status is `CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD`.
    - `docs/context/bridge_contract_current.md` reflects D-345 closeout state.
    - `docs/handover/phase60_execution_handover_20260318.md` reflects D-345 blocked-hold closeout.
    - targeted pytest, context build/validate, and SAW/closure validation are captured under `docs/context/e2e_evidence/phase60_d345_closeout_20260319.*`.
  - Contract lock:
    - `Phase60_D345 := CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD iff (phase60_brief_status = CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD) and (D341_root_cause_preserved = 274_missing_cells + KS03) and (no new execution authority granted)`.
    - `if future remediation, widening, promotion path, allocator carry-forward, core inclusion, kernel mutation, or any Phase 61+ scope is proposed -> require a separate explicit approval packet containing exact 'approve next phase'; D-345 is not that authority`.
  - Open risks:
    - none new in-scope; the blocked same-period comparator root cause is now the preserved formal closeout basis for Phase 60.
  - Rollback note:
    - revert only this `D-345` entry plus the synchronized closeout docs/context/SAW/lesson edits if leadership amends wording; do not alter `D-344`, `D-343`, `D-341`, `D-340`, `D-339`, `D-338`, `D-337`, prior-sleeve SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 60 (2026-03-19): Post-Phase-60 Kernel Mutation Hold Packet (D-347) 🟢

  - Decision record:
    - explicitly reject Option A for core/engine.py:34 (strict_missing_returns) and the data snapshot hash function; declare both changes blocked under the D-346/D-345 closeout, preserve the 274 missing executed-exposure return cells verbatim without remediation, and require a formal `approve next phase` token for any Phase 61+ work.
  - The Decision (Hardcoded):
    - `core/engine.py` remains immutable.
    - changing `strict_missing_returns` to True or changing the hash function constitutes a kernel mutation and direct remediation of the 274-cell gap, which is explicitly blocked at 100/100 confidence.
    - the 274-cell gap is preserved verbatim; no fix or comparator repair is authorized in this round.
    - any future kernel hardening or Phase 61 work requires a completely new explicit packet containing the literal token `approve next phase` before any code change.
  - Evidence:
    - Phase 60 `docs/context/e2e_evidence/phase60_d347_hold_20260319.*` outputs.
    - refreshed context packets affirming `CLOSED_BLOCKED_EVIDENCE_ONLY_HOLD`.
    - new SAW report `docs/saw_reports/saw_phase60_d347_kernel_hold_20260319.md`.
  - Contract lock:
    - `Phase60_D347 := MUTATION_BLOCKED iff (core/engine.py unchanged) and (gap preserved verbatim) and (Phase 61/kernel widening strictly requires approve next phase)`.
    - `if future kernel hardening or Phase 61 work is proposed -> require a separate explicit approval packet containing exact 'approve next phase'`.
  - Open risks:
    - none new; the blocked 274-cell C3 comparator gap remains unresolved and unremediated per governance rules.
  - Rollback note:
    - revert only this `D-347` entry plus the synchronized brief/context/SAW/lesson edits; do not alter prior SSOT artifacts, `RESEARCH_MAX_DATE = 2022-12-31`, or the `D-292` research kernel.

Phase 61 (2026-03-19): CEO “approve next phase” Token Consumed + Bounded Phase 61 Comparator Remediation Packet (Data-Only) (D-348) 🟢

  - Decision record:
    - Publish and execute only the D-348 bounded packet exactly as defined in the CEO Handover.
    - Data-level completeness patch for the 2023-2024 executed-exposure returns (sidecar refresh or targeted append to C3 comparator surface).
    - Preserve `strict_missing_returns=True` and snapshot hash function verbatim — no kernel mutation.
    - Re-run the exact D-340 bounded integrated audit (governed cube from PEAD + Corporate Actions sleeves, `allocator_overlay=0.0`, core sleeve excluded, `5.0` bps gate + separate `10.0` bps sensitivity lane, window `2023-01-01 -> 2024-12-31`).
    - Integrate S&P 500 Pro / Moody’s B&D via locked Method B (isolated Parquet sidecars joined only at view layer).
    - Immediately after successful re-audit, publish new evidence bundle and transition docs.
    - No other work authorized (no promotion, no allocator carry-forward, no core inclusion, no `RESEARCH_MAX_DATE` lift, no widening beyond this slice).
  - The Decision (Hardcoded):
    - Phase 60 is officially closed. Phase 61 is executing under EXECUTING_BOUNDED.
    - `core/engine.py` remains untouched (D-347 lock enforced).
    - The 274-cell history stays in lessons as accepted evidence-only root cause.
    - All prior locks (D-284–D-347, `RESEARCH_MAX_DATE=2022-12-31`, same-window/same-cost/same-engine, `5.0` bps gate, allocator/core exclusions) preserved verbatim.
  - Evidence:
    - Docs updated across `decision log.md`, `phase60-brief.md`, `current_context.md`, `current_context.json`, `bridge_contract_current.md`, `phase60_execution_handover_20260318.md`, `lessonss.md`.
  - Contract lock:
    - Bounded execution slice logic applies solely to data patch for 274 return cells (C3 only), followed by Method B sidecar integration. Null core/engine.py mutations permitted.
  - Rollback note:
    - Kernel mutation, widening, promotion, or any change beyond the bounded data patch → revert all D-348 edits and return to D-347 hold state.

Phase 61 (2026-03-20): Raw Tape Ingest Path Prepared, Local Tape Extraction Still Blocked (D-350) 🟡

  - Decision record:
    - prepare the exact raw-tape ingest path for `data/raw/sp500_pro_avantax_tape.csv`, harden the builder to fail closed on malformed tape input, and report the current local blocker truthfully because the Capital IQ plug-in extraction path is not available on this workstation.
  - The Decision (Hardcoded):
    - `scripts/build_sp500_pro_sidecar.py` now prefers the literal daily tape CSV and only allows metadata fallback when explicitly requested.
    - raw tape contract:
      - required normalized columns: `date`, `price`, `total_return`,
      - reject duplicate trading dates,
      - reject all-NaN `price`,
      - reject all-NaN `total_return`,
      - parse accounting-style negatives like `(3.25%)` and `(1.23)`.
    - the normal builder invocation is now intentionally blocked until `data/raw/sp500_pro_avantax_tape.csv` exists.
    - current local extraction remains blocked because:
      - Excel `16.0` is available,
      - the Capital IQ COM add-in is not present / connected,
      - the raw tape CSV is absent.
    - therefore the literal D-350 daily-tape remediation is not yet complete on this machine, even though the downstream ingest path is ready.
  - Evidence:
    - `scripts/build_sp500_pro_sidecar.py`
    - `tests/test_build_sp500_pro_sidecar.py`
    - `.venv\Scripts\python -m pytest tests/test_build_sp500_pro_sidecar.py -q` -> PASS (`8 passed`)
    - `.venv\Scripts\python scripts/build_sp500_pro_sidecar.py` -> BLOCK (`Raw tape CSV is missing ...`)
    - `docs/context/e2e_evidence/phase61_sp500_pro_tape_block_20260320.json`
  - Contract lock:
    - `Phase61_D350 := BLOCKED iff (raw_tape_csv_present = 0) or (capital_iq_addin_present = 0)`.
    - `if literal daily tape appears -> rerun build_sp500_pro_sidecar.py without --allow-metadata-fallback and overwrite sidecar_sp500_pro_2023_2024.parquet from the real tape`.
  - Open risks:
    - the current sidecar remains metadata fallback only and does not satisfy the literal-daily-tape repair objective.
    - C3 view-layer patching for the 274 missing cells remains blocked until the raw tape CSV is actually produced.
  - Rollback note:
    - revert only the D-350 builder/test/docs changes if leadership rejects the prepared ingest path; do not alter D-348 authority, the D-350 PERMNO/CUSIP map, or bedrock price artifacts.

Phase 61 (2026-03-20): Audit Gap Closure + Sidecar Coverage Mask Validation (D-351) 🟡

  - Decision record:
    - close the two execution gaps left open by the original D-350 tape plan:
      - the governed audit must actually consume the sidecar return rows;
      - the C3 comparator must stop selecting AVTA on and after its last available return date under strict `t -> t+1` execution.
    - add a standalone WRDS CRSP extractor for the bounded sidecar path, attempt the live run, and report the live auth blocker truthfully if WRDS rejects the supplied login.
    - validate the repaired audit path with the real on-disk CRSP boundary return row already present in `data/processed/prices.parquet` (`PERMNO 86544`, `2023-11-28`, `total_ret = 0.0`) without mutating bedrock artifacts.
  - The Decision (Hardcoded):
    - `scripts/phase60_governed_audit_runner.py` now overlays sidecar `total_return` rows onto the comparator return surface before strict-missing-return validation.
    - the same comparator path now masks sidecar permnos from C3 feature rows on and after the last available sidecar return date, so stale post-delist feature rows cannot create impossible next-day executions.
    - `scripts/ingest_d350_wrds_sidecar.py` is the canonical env-only WRDS extractor for publishing the bounded D-350 sidecar into `data/processed/sidecar_sp500_pro_2023_2024.parquet`.
    - focused validation proves the repaired path clears KS-03 when supplied the missing boundary return row, but the live repo sidecar remains metadata-only because the 2026-03-20 WRDS login attempt failed with PAM authentication.
    - no mutation of `core/engine.py`, `research_data/`, or bedrock price artifacts is authorized or required by this packet.
  - Evidence:
    - `scripts/phase60_governed_audit_runner.py`
    - `scripts/ingest_d350_wrds_sidecar.py`
    - `tests/test_phase60_governed_audit_runner.py`
    - `tests/test_ingest_d350_wrds_sidecar.py`
    - `.venv\Scripts\python -m pytest tests/test_phase60_governed_audit_runner.py tests/test_ingest_d350_wrds_sidecar.py -q` -> PASS (`9 passed`)
    - temporary bounded validation using a one-row sidecar built from `data/processed/prices.parquet` (`date=2023-11-28`, `total_ret=0.0`) -> comparator PASS, governed audit `status = ok`
    - `docs/phase_brief/phase61-brief.md`
    - `docs/context/e2e_evidence/phase61_d350_wrds_pivot_20260319_summary.json`
    - `docs/saw_reports/saw_phase61_d350_wrds_tape_20260319.md`
  - Contract lock:
    - `Phase61_D351 := VALID iff (audit_runner_consumes_sidecar = 1) and (feature_mask_blocks_post_coverage_selection = 1) and (focused_tests = PASS) and (temp_boundary_sidecar_validation = PASS)`.
    - `if live WRDS extraction is required -> run scripts/ingest_d350_wrds_sidecar.py only with env-supplied credentials and keep all writes isolated to the bounded sidecar/evidence paths; if WRDS rejects auth, leave the sidecar unchanged and keep the audit blocked`.
  - Open risks:
    - live WRDS execution is blocked because WRDS rejected the supplied login with PAM authentication failure;
    - the repo sidecar remains metadata-only until the live bounded sidecar is written;
    - the local bedrock boundary row has `adj_close = NaN`, so direct CRSP price republishing still depends on the live WRDS extractor.
  - Rollback note:
    - revert only the D-351 code/docs/report changes if leadership rejects the view-layer remediation path; do not alter D-350 raw-tape prep, D-348 authority, bedrock price artifacts, or `core/engine.py`.

Phase 61 (2026-03-23): Terminal Zero v2.6 Roadmap Lock + Nautilus Deferral + V1/V2 Boundary (D-352) 🟢

  - Decision record:
    - lock the Terminal Zero v2.6 roadmap as the official forward plan for Phases 62–80+.
    - establish the V1 Core / V2 Discovery architecture boundary with strict directory isolation, promotion contract schema, and candidate lifecycle governance.
    - defer the Nautilus Trader adapter spike to Phases 69–70; the BrokerPort interface is defined in Phase 63 (execution boundary hardening) as the prerequisite adapter seam.
    - ML integration follows an 80/20 split in Phases 62–65 (80% platform hardening, 20% MLOps skeleton), with no distributed compute until Phase 72.
    - the non-ML V2 discovery pipeline (registry, proxy sim, promotion contract) must process at least one candidate family end-to-end before ML augmentation targets apply.
  - The Decision (Hardcoded):
    - `docs/roadmap/terminal_zero_v2.6.md` is the locked roadmap document.
    - `docs/architecture/v1_v2_boundary.md` is the V1/V2 split contract with directory boundaries, promotion packet schema, and candidate lifecycle.
    - `PHASE_QUEUE.md` (repo root) is the worker pickup list for Phases 62–80+.
    - BrokerPort interface: defined in Phase 63. No direct Alpaca imports outside `execution/broker_api.py` after Phase 63.
    - Nautilus: deferred to Phases 69–70. No Nautilus work before V2 pipeline baseline proves structural integrity.
    - ML promotion metric: ≥40% ML-augmented promotions with N ≥ 5 floor, evaluated at Phase 74.
    - ML allocator failure path: BLOCKED status + 30-day cooldown + D-log retirement if 6-month shadow test fails (Phases 78–79).
    - DRL: bounded research spike at Phase 73, prove-or-kill, not approved for standard promotion pipeline.
    - Data isolation: ML experiment artifacts in `v2_discovery/mlops/`; V1 canonical paths (`data/processed/`, `research_data/`) strictly excluded from V2/ML writes.
    - Online models: subject to same drift escalation and KS-03 kill-switch governance as static models.
  - Evidence:
    - `docs/roadmap/terminal_zero_v2.6.md`
    - `docs/architecture/v1_v2_boundary.md`
    - `PHASE_QUEUE.md`
    - `Alpha Rating Discussion_2026-03-20 23_44_29.md` (reconciliation debate trail)
    - `docs/saw_reports/saw_phase61_context_reconciliation_20260322.md` (baseline SAW)
  - Contract lock:
    - `Phase62_READY := VALID iff (phase61_committed = 1) and (roadmap_v2.6_locked = 1) and (v1_v2_boundary_published = 1) and (phase_queue_published = 1)`.
    - `Nautilus_DEFERRED := VALID iff (BrokerPort_defined_in_phase63 = 1) and (v2_pipeline_baseline_proven = 1) before any Nautilus adapter work`.
    - `ML_PROMOTION_GATE := VALID iff (ml_augmented_pct >= 0.40) and (total_promotions_attempted >= 5) evaluated by automated script at Phase 74`.
  - Open risks:
    - Phase 61 committed as b266870 and pushed to origin/main. Phase 62 is READY.
    - WRDS PAM auth remains unresolved; provenance hardening (Phase 64) will address this.
    - Streamlit long-term viability is an open question deferred past Phase 62 (modularize first, migrate later if needed).
  - Rollback note:
    - revert only the D-352 roadmap/architecture/queue files if leadership rejects the v2.6 plan; do not alter D-348 through D-351 authority, Phase 61 reconciliation artifacts, or any V1 canonical data.

Phase 64 (2026-05-09): Accelerated Provenance + Validation + Paper-Alert Gate Milestone A-E (D-353) 🟢

  - Decision record:
    - consume the user-approved "full go" for provenance + validation + paper-alert gate work only, not live trading.
    - execute Phases A-E from `docs/research/laptop_quant_implementation_plan_20260509.md`: source policy, provenance manifest enforcement, provider ports, data health audit, and minimal validation lab.
    - keep yfinance quarantined as Tier 2 discovery/convenience data rather than deleting it.
    - use Alpaca only as operational/paper market data in this milestone; no live Alpaca order path or broker automation is authorized.
  - The Decision (Hardcoded):
    - `docs/architecture/data_source_policy.md` is active.
    - validation reports require manifests.
    - V1 promotion-intent validation requires `source_quality = "canonical"`.
    - `source_quality = "non_canonical"` blocks yfinance/Tier 2 promotion packets.
    - Alpaca IEX quotes must carry `quote_quality = "iex_only"` and cannot be represented as SIP-quality market truth.
    - non-paper Alpaca endpoint initialization requires both break-glass and `TZ_SIGNED_LIVE_TRADING_DECISION=YES`; no such live decision is granted by D-353.
    - credentials must never be committed, logged, embedded in docs, or emitted in artifacts.
  - Evidence:
    - `data/provenance.py`
    - `data/providers/`
    - `execution/broker_api.py`
    - `scripts/audit_data_readiness.py`
    - `validation/`
    - `scripts/run_minimal_validation_lab.py`
    - `tests/test_provenance_policy.py`
    - `tests/test_provider_ports.py`
    - `tests/test_data_readiness_audit.py`
    - `tests/test_minimal_validation_lab.py`
    - `.venv\Scripts\python -m pytest tests/test_provenance_policy.py tests/test_provider_ports.py tests/test_data_readiness_audit.py tests/test_minimal_validation_lab.py tests/test_execution_controls.py -q` -> PASS (`75 passed`)
    - `.venv\Scripts\python scripts\audit_data_readiness.py` -> PASS (`ready_for_paper_alerts = true`, warning `stale_sidecars_max_date_2023-11-27`)
    - `.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent` -> PASS
    - `data/processed/data_readiness_report.json`
    - `data/processed/data_readiness_report.json.manifest.json`
    - `data/processed/minimal_validation_report.json`
    - `data/processed/minimal_validation_report.json.manifest.json`
    - `data/processed/phase56_pead_evidence.csv.manifest.json`
  - Contract lock:
    - `D353_VALIDATION_GATE := VALID iff (validation_report_manifest_present = 1) and (promotion_intent_source_quality = canonical) and (tier2_promotion_block = 1)`.
    - `D353_PROVIDER_GATE := VALID iff (new provider use routes through data/providers/*) and (direct_yfinance_uses subset of data.providers.legacy_allowlist.YFINANCE_DIRECT_USE_ALLOWLIST)`.
    - `D353_ALPACA_BOUNDARY := PAPER_ONLY iff (non_paper_endpoint_requires_break_glass = 1) and (non_paper_endpoint_requires_signed_decision = 1) and (no D-log live-trading approval exists)`.
  - Open risks:
    - yfinance quarantine surface is larger than the original plan list and includes many legacy scripts; the allowlist now records current reality and fails closed on new spread.
    - `pip check` reports inherited dependency conflicts: `alpaca-trade-api 3.2.0` requires `urllib3<2` and `websockets<11`, while the environment has newer versions.
    - primary S&P sidecar is stale through `2023-11-27`; readiness still passes for daily paper-alert gating but provenance refresh remains recommended.
  - Rollback note:
    - revert only D-353 code/docs/report artifacts if leadership rejects the accelerated provenance milestone; do not alter Phase 61 SSOT artifacts, `core/engine.py`, `research_data/`, or bedrock price artifacts.

Phase 64.1 (2026-05-09): Dependency Hygiene + Phase F Candidate Registry Approval (D-354) 🟢

  - Decision record:
    - close the dependency hygiene wedge before Candidate Registry so experiment multiplication does not start on a red `pip check`.
    - migrate the main Alpaca SDK boundary from `alpaca-trade-api` to `alpaca-py==0.43.4`.
    - keep Alpaca functionality bounded to operational/paper quote and existing paper/live safety gates; no live orders or broker automation are authorized.
    - approve Phase F Candidate Registry only after R64.1 checks pass, with registry-only scope and no strategy factory, V2 fast simulator, promotion packet, alert packet, or live execution path.
  - The Decision (Hardcoded):
    - `requirements.txt`, `requirements.lock`, and `pyproject.toml` use `alpaca-py==0.43.4` in the main environment.
    - `alpaca-trade-api` is excluded from the main dependency set and `execution/broker_api.py` no longer imports `alpaca_trade_api`.
    - the existing broker boundary keeps the same credential, paper-default, non-paper break-glass, and signed-decision gates.
    - Phase F Candidate Registry is approved as append-only metadata/lifecycle work: candidate metadata before results, required `trial_count`, required manifest pointer, and immutable audit trail.
  - Evidence:
    - `execution/broker_api.py`
    - `requirements.txt`
    - `requirements.lock`
    - `pyproject.toml`
    - `tests/test_dependency_hygiene.py`
    - `docs/phase_brief/phase65-brief.md`
    - `.venv\Scripts\python -m pip check` -> PASS (`No broken requirements found.`)
    - `.venv\Scripts\python -m pytest tests/test_dependency_hygiene.py tests/test_execution_controls.py tests/test_provider_ports.py tests/test_provenance_policy.py -q` -> PASS
  - Contract lock:
    - `R64_1_DEPENDENCY_GATE := VALID iff (pip_check = PASS) and (main_dependency = alpaca-py==0.43.4) and (legacy_alpaca_trade_api_not_in_main_deps = 1)`.
    - `PHASE_F_APPROVED := VALID iff (R64_1_DEPENDENCY_GATE = VALID) and (scope = registry_only) and (strategy_factory = blocked) and (promotion_packets = blocked) and (live_execution = blocked)`.
  - Open risks:
    - yfinance legacy migration remains future debt but is not a Candidate Registry blocker while quarantine tests pass.
    - primary S&P sidecar freshness remains a warning for paper-alert readiness and should be refreshed when canonical vendor access is available.
    - unrelated pre-existing dirty files remain excluded from the R64/R65 surgical commits.
  - Rollback note:
    - revert only the R64.1 dependency files, broker SDK shim, dependency tests, and docs if the `alpaca-py` boundary is rejected; do not revert D-353 provenance/validation gates or Phase 61 SSOT artifacts.

Phase 65 (2026-05-09): Candidate Registry - Registry-Only Closeout (D-355) 🟢

  - Decision record:
    - implement Phase F as a registry-only candidate intent ledger before strategy search, simulation, alerts, promotion packets, or broker behavior.
    - record candidate metadata, trial family intent, code reference, data snapshot, source quality, and manifest pointer before any result payload exists.
    - use a simple JSONL append-only event log first; do not add MLflow, DVC, vectorbt, Qlib, a strategy factory, or V2 fast simulator in this phase.
    - keep the next decision explicit: Phase G V2 Proxy Boundary versus advanced registry accounting for trial families and multiple-testing metadata.
  - The Decision (Hardcoded):
    - `v2_discovery/schemas.py` defines frozen `CandidateSpec`, `CandidateEvent`, and `CandidateSnapshot` dataclasses.
    - `v2_discovery/registry.py` writes `data/registry/candidate_events.jsonl` as the source of truth and derives `data/registry/candidate_snapshot.json`.
    - every candidate requires `manifest_uri`, `source_quality`, `trial_count`, and `parameters_searched`; the manifest must exist and source quality must match.
    - event hashes chain with `previous_event_hash` and `event_hash`, with the first event anchored to `GENESIS`.
    - allowed Phase F transitions are `generated -> incubating`, `incubating -> rejected`, `generated -> rejected`, `generated -> retired`, and `generated -> quarantined`.
    - `promoted`, `alerted`, and `executed` statuses are forbidden in Phase F; registry snapshots are never promotion-ready.
  - Evidence:
    - `docs/architecture/candidate_registry_policy.md`
    - `v2_discovery/schemas.py`
    - `v2_discovery/registry.py`
    - `scripts/run_candidate_registry_demo.py`
    - `tests/test_candidate_registry.py`
    - `data/registry/candidate_events.jsonl`
    - `data/registry/candidate_snapshot.json`
    - `data/registry/candidate_registry_rebuild_report.json`
    - `.venv\Scripts\python -m pytest tests/test_candidate_registry.py -q` -> PASS (`12 passed`)
    - `.venv\Scripts\python scripts\run_candidate_registry_demo.py` -> PASS (`event_count = 3`, `demo_status = rejected`, `hash_chain_valid = true`)
    - `.venv\Scripts\python -m pytest tests/test_dependency_hygiene.py tests/test_provider_ports.py tests/test_provenance_policy.py tests/test_data_readiness_audit.py tests/test_minimal_validation_lab.py tests/test_candidate_registry.py -q` -> PASS
    - `.venv\Scripts\python -m pytest -q` -> PASS with existing skips/warnings
    - `.venv\Scripts\python -m pip check` -> PASS (`No broken requirements found.`)
    - `.venv\Scripts\python scripts\audit_data_readiness.py` -> PASS (`ready_for_paper_alerts = true`, warning `stale_sidecars_max_date_2023-11-27`)
    - `.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent` -> PASS
    - `.venv\Scripts\python launch.py --server.headless true --server.port 8599` -> PASS (headless smoke reached local URL; smoke process stopped)
  - Contract lock:
    - `PH65_REGISTRY_ONLY := VALID iff (append_only_event_log = 1) and (snapshot_rebuilds_from_events = 1) and (candidate_manifest_uri_required = 1) and (candidate_source_quality_required = 1) and (trial_count_required = 1) and (strategy_search = 0) and (promotion_packets = 0) and (alerts = 0) and (execution = 0)`.
    - `PH65_HASH_CHAIN := VALID iff event_hash_i == SHA256(canonical_json(event_i without event_hash)) and previous_event_hash_i == event_hash_{i-1}`.
  - Open risks:
    - yfinance legacy migration remains future debt but is not a Candidate Registry blocker while quarantine tests pass.
    - primary S&P sidecar freshness remains a paper-alert warning through `2023-11-27`.
    - unrelated pre-existing dirty files remain excluded from the Phase 65 surgical commit.
  - Rollback note:
    - revert only Phase 65 registry code, tests, policy/brief/handover/context docs, and `data/registry/*` artifacts if the registry kernel is rejected; do not revert D-353/R64.1 provenance, validation, provider, dependency, or broker-boundary work.

Phase 65 G0 (2026-05-09): V2 Proxy Boundary Harness (D-356) 🟢

  - Decision record:
    - create a boundary-only V2 proxy airlock after Candidate Registry and before any useful fast simulation.
    - keep `core.engine.run_simulation` as the only official V1 truth path.
    - keep V2 proxy outputs advisory only with `promotion_ready = false` and `canonical_engine_required = true`.
    - do not add strategy search, parameter sweeps, candidate ranking, alerts, broker calls, promotion packets, external engines, MLflow, DVC, vectorbt, Qlib, LEAN, or Nautilus.
  - The Decision (Hardcoded):
    - `v2_discovery/fast_sim/schemas.py` defines frozen `ProxyRunSpec`, `ProxyRunResult`, `PromotionPacketDraft`, `ProxyBoundaryVerdict`, and `ProxyRunStatus`.
    - `v2_discovery/fast_sim/boundary.py` validates registered candidates, registry event IDs, manifests, source quality, proxy verdicts, and registry note proofs.
    - `v2_discovery/fast_sim/noop_proxy.py` computes no alpha and only appends a registry note.
    - proxy results cannot be promotion-ready, cannot use forged registry note IDs, and cannot bypass the future V1 canonical rerun requirement.
  - Evidence:
    - `docs/architecture/v2_proxy_boundary_policy.md`
    - `v2_discovery/fast_sim/schemas.py`
    - `v2_discovery/fast_sim/boundary.py`
    - `v2_discovery/fast_sim/noop_proxy.py`
    - `tests/test_v2_proxy_boundary.py`
    - `.venv\Scripts\python -m pytest tests/test_v2_proxy_boundary.py -q` -> PASS (`11 passed`)
    - `.venv\Scripts\python -m compileall v2_discovery\fast_sim tests\test_v2_proxy_boundary.py` -> PASS
  - Contract lock:
    - `PH65_G0_BOUNDARY_ONLY := VALID iff (proxy_result_promotion_ready = 0) and (canonical_engine_required = 1) and (registered_candidate_required = 1) and (manifest_required = 1) and (source_quality_required = 1) and (registry_note_event_valid = 1) and (strategy_search = 0) and (broker_calls = 0) and (alerts = 0)`.
    - `PH65_G0_CANONICAL_TRUTH := VALID iff official_truth_path = core.engine.run_simulation`.
  - Open risks:
    - yfinance legacy migration remains future debt.
    - primary S&P sidecar freshness remains a paper-alert warning through `2023-11-27`.
  - Rollback note:
    - revert only Phase G0 fast-sim boundary files, tests, policy/brief/context docs, and SAW report if the boundary harness is rejected; do not revert Phase F Candidate Registry, D-353 provenance gates, or R64.1 dependency hygiene.

Phase 65 G1 (2026-05-09): Deterministic Synthetic Fast-Proxy Simulator (D-357) 🟢

  - Decision record:
    - approve G1 as synthetic mechanics only after G0 proved proxy output containment.
    - prove deterministic replay, manifest-backed fixture loading, hash validation, cost accounting, ledger output, and registry/boundary references.
    - keep proxy outputs separate from official truth; V1 `core.engine.run_simulation` evidence remains required for any future promotion.
    - do not add strategy search, real market data, PEAD variants, alpha/Sharpe/CAGR/max-drawdown/ranking metrics, alerts, broker calls, promotion packets, MLflow, or DVC.
  - The Decision (Hardcoded):
    - `v2_discovery/fast_sim/fixtures.py` accepts only `data/fixtures/v2_proxy/*` with provider `synthetic_fixture`, feed `prebaked_target_weights`, license `synthetic_fixture_only`, and fixture hash checks.
    - `v2_discovery/fast_sim/cost_model.py` computes deterministic transaction costs from configured bps, initial cash, and turnover.
    - `v2_discovery/fast_sim/ledger.py` computes positions, cash, turnover, transaction costs, gross exposure, and net exposure from prebaked target weights.
    - `v2_discovery/fast_sim/simulator.py` routes every run through `V2ProxyBoundary`, appends only a registry note, and returns `promotion_ready = false` plus `canonical_engine_required = true`.
    - golden fixtures live under `data/fixtures/v2_proxy/` and are validated with strict table comparisons in tests.
  - Evidence:
    - `data/fixtures/v2_proxy/synthetic_manifest.json`
    - `data/fixtures/v2_proxy/expected_ledger.csv`
    - `data/fixtures/v2_proxy/expected_positions.csv`
    - `data/fixtures/v2_proxy/expected_result.json`
    - `v2_discovery/fast_sim/cost_model.py`
    - `v2_discovery/fast_sim/fixtures.py`
    - `v2_discovery/fast_sim/ledger.py`
    - `v2_discovery/fast_sim/simulator.py`
    - `tests/test_v2_fast_proxy_synthetic.py`
    - `tests/test_v2_fast_proxy_invariants.py`
    - `.venv\Scripts\python -m pytest tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py -q` -> PASS (`16 passed`)
    - `.venv\Scripts\python -m pytest tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q` -> PASS (`39 passed`)
    - `.venv\Scripts\python -m compileall v2_discovery\fast_sim tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py` -> PASS
    - `.venv\Scripts\python -m pip check` -> PASS (`No broken requirements found.`)
  - Contract lock:
    - `PH65_G1_SYNTHETIC_ONLY := VALID iff (fixture_manifest_required = 1) and (fixture_hashes_match = 1) and (real_market_data_paths = 0) and (prebaked_weights_only = 1) and (strategy_search = 0) and (alerts = 0) and (broker_calls = 0)`.
    - `PH65_G1_QUARANTINE := VALID iff (promotion_ready = 0) and (canonical_engine_required = 1) and (boundary_verdict in {tier2_blocked, blocked_from_promotion}) and (official_truth_path_required = core.engine.run_simulation)`.
  - Open risks:
    - yfinance legacy migration remains future debt.
    - primary S&P sidecar freshness remains a paper-alert warning through `2023-11-27`.
    - G2 must not convert synthetic mechanics into strategy discovery without explicit approval.
  - Rollback note:
    - revert only Phase G1 simulator files, G1 tests, `data/fixtures/v2_proxy/*`, policy/brief/context docs, and SAW report if the synthetic simulator is rejected; do not revert Phase G0 boundary, Phase F Candidate Registry, D-353 provenance gates, or R64.1 dependency hygiene.

Phase 65 G1.1 (2026-05-09): Synthetic Fast Proxy Data-Integrity Reconciliation (D-358) 🟢

  - Decision record:
    - close the Reviewer C data-integrity block before any G2 decision.
    - treat `nan`, `+inf`, and `-inf` as invalid evidence at fixture load, pre-ledger, post-ledger, result-summary, and proxy metadata boundaries.
    - reconcile fixture/golden manifest row counts, date ranges, schema columns, and SHA-256 hashes against loaded artifacts.
    - fail closed on missing symbols and sparse target weights; do not use `nan_to_num`, `fillna(0)`, or imputation to repair bad evidence.
    - keep G1 synthetic mechanics only; no G2, real market data, strategy search, alert, broker, or promotion authority is introduced.
  - The Decision (Hardcoded):
    - `v2_discovery/fast_sim/validation.py` centralizes required-column, null, finite-numeric, positive-numeric, and manifest reconciliation checks.
    - `v2_discovery/fast_sim/fixtures.py` validates symbols before string cleanup, rejects non-finite prices/weights, and reconciles prices, weights, and top-level manifest metadata.
    - `v2_discovery/fast_sim/ledger.py` validates pre-ledger inputs/cost assumptions, rejects sparse target weights after pivot, and validates positions/ledger outputs.
    - `v2_discovery/fast_sim/schemas.py` requires strict JSON-serializable finite proxy mappings.
    - `data/fixtures/v2_proxy/synthetic_manifest.json` now declares row count, date range, schema, and hash metadata for prices, weights, expected ledger, expected positions, and expected result.
  - Evidence:
    - `v2_discovery/fast_sim/validation.py`
    - `v2_discovery/fast_sim/fixtures.py`
    - `v2_discovery/fast_sim/ledger.py`
    - `v2_discovery/fast_sim/schemas.py`
    - `tests/test_v2_fast_proxy_synthetic.py`
    - `tests/test_v2_fast_proxy_invariants.py`
    - `data/fixtures/v2_proxy/synthetic_manifest.json`
    - `.venv\Scripts\python -m pytest tests/test_v2_fast_proxy_synthetic.py -q` -> PASS (`25 passed`)
    - `.venv\Scripts\python -m pytest tests/test_v2_fast_proxy_invariants.py -q` -> PASS (`9 passed`)
    - `.venv\Scripts\python -m pytest tests/test_v2_proxy_boundary.py -q` -> PASS (`11 passed`)
    - `.venv\Scripts\python -m pytest tests/test_v2_fast_proxy_synthetic.py tests/test_v2_fast_proxy_invariants.py tests/test_v2_proxy_boundary.py tests/test_candidate_registry.py -q` -> PASS (`57 passed`)
    - `.venv\Scripts\python -m pytest -q` -> PASS with existing skips/warnings
    - `.venv\Scripts\python -m pip check` -> PASS
    - `.venv\Scripts\python scripts\audit_data_readiness.py` -> PASS (`ready_for_paper_alerts = true`, warning `stale_sidecars_max_date_2023-11-27`)
    - `.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent` -> PASS
    - `.venv\Scripts\python launch.py --server.headless true --server.port 8604` -> PASS (stayed alive for 20s)
    - Reviewer B recheck -> PASS
    - Reviewer C final recheck -> PASS
  - Contract lock:
    - `PH65_G1_FINITE_GATE := VALID iff all numeric fixture inputs, cost assumptions, ledger outputs, positions, result series, and proxy metadata are finite and strict-JSON serializable`.
    - `PH65_G1_MANIFEST_RECONCILIATION := VALID iff manifest row_count/date_range/schema/sha256 metadata equals loaded fixture or golden artifact truth`.
    - `PH65_G1_NO_REPAIR := VALID iff missing symbols, sparse weights, non-finite values, and manifest drift fail closed before simulation output is accepted`.
  - Open risks:
    - yfinance legacy migration remains future debt.
    - primary S&P sidecar freshness remains a paper-alert warning through `2023-11-27`.
    - G2 must remain a separate explicit decision and must stay synthetic/no-search unless approved.
  - Rollback note:
    - revert only Phase G1.1 validation/schema/fixture/test/doc/report changes if the reconciliation is rejected; do not revert Phase G0 boundary, Phase F Candidate Registry, D-353 provenance gates, or R64.1 dependency hygiene.

Phase 65 G2 (2026-05-09): Single Registered Fixture Candidate (D-359) 🟢

  - Decision record:
    - approve exactly one registered synthetic fixture candidate through the quarantined V2 proxy.
    - prove registry -> G1 fixture -> deterministic proxy -> real hash-linked registry note -> lineage report once.
    - keep the proxy result blocked from promotion with `promotion_ready = false` and `canonical_engine_required = true`.
    - do not add strategy search, real market data, candidate ranking, alerts, broker calls, promotion packets, MLflow, or DVC.
  - The Decision (Hardcoded):
    - `v2_discovery/fast_sim/run_candidate_proxy.py` registers or loads one G2 fixture candidate and reuses the fixed proxy note if repeated.
    - `v2_discovery/fast_sim/lineage.py` rebuilds lineage from the append-only registry event log and validates hash-linked note proof.
    - `data/registry/g2_single_fixture_candidate_report.json*` records the optional lineage report and manifest.
  - Evidence:
    - `tests/test_v2_proxy_registered_candidate_flow.py`
    - `docs/architecture/g2_registered_fixture_candidate_policy.md`
    - `docs/saw_reports/saw_phase65_g2_registered_fixture_candidate_20260509.md`
    - `.venv\Scripts\python -m pytest tests\test_v2_proxy_registered_candidate_flow.py -q` -> PASS (`19 passed`)
    - `.venv\Scripts\python -m pytest tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q` -> PASS (`76 passed`)
  - Contract lock:
    - `PH65_G2_LINEAGE_ONLY := VALID iff (registered_fixture_candidates = 1) and (registry_note_hash_linked = 1) and (promotion_ready = 0) and (canonical_engine_required = 1) and (strategy_search = 0) and (broker_calls = 0) and (alerts = 0)`.
  - Open risks:
    - yfinance legacy migration remains future debt.
    - primary S&P sidecar freshness remains a paper-alert warning through `2023-11-27`.
  - Rollback note:
    - revert only the G2 runner, lineage helper, test, policy, SAW report, and G2 registry report artifacts if rejected; do not revert G0, G1, Candidate Registry, D-353, or R64.1.

Phase 65 G3 (2026-05-09): First Canonical Replay Fixture (D-360) 🟢

  - Decision record:
    - approve the first canonical replay fixture as truth-alignment work, not strategy search.
    - replay exactly one registered fixture candidate through `core.engine.run_simulation`.
    - compare V1 and V2 only on mechanical accounting fields.
    - keep V2 subordinate even when the mechanical comparison matches.
    - treat SR 26-2 model-risk guidance as governance framing for inventory, documentation, and validation discipline, not as a new dependency.
  - The Decision (Hardcoded):
    - `v2_discovery/replay/canonical_replay.py` requires one registered G2 fixture candidate, validates manifest/source-quality/hash evidence, calls `core.engine.run_simulation`, and writes the optional replay report.
    - `v2_discovery/replay/comparison.py` compares only positions, cash, turnover, transaction cost, gross exposure, net exposure, row count, date range, manifest URI, source quality, and candidate ID.
    - `v2_discovery/replay/schemas.py` locks `promotion_ready = false`, `canonical_engine_required = true`, and `boundary_verdict = "v2_blocked_from_promotion"`.
  - Evidence:
    - `tests/test_v2_canonical_replay_fixture.py`
    - `docs/architecture/g3_canonical_replay_fixture_policy.md`
    - `data/registry/g3_canonical_replay_report.json*`
    - `.venv\Scripts\python -m pytest tests\test_v2_canonical_replay_fixture.py -q` -> PASS (`15 passed`)
  - Contract lock:
    - `PH65_G3_CANONICAL_REPLAY_ONLY := VALID iff (registered_fixture_candidates = 1) and (v1_engine = core.engine.run_simulation) and (comparison_fields = mechanical_allowed_set) and (promotion_ready = 0) and (promotion_packet_created = 0) and (strategy_search = 0) and (broker_calls = 0) and (alerts = 0)`.
  - Open risks:
    - yfinance legacy migration remains future debt.
    - primary S&P sidecar freshness remains a paper-alert warning through `2023-11-27`.
  - Rollback note:
    - revert only the G3 replay package, focused test, policy, SAW report, G3 registry report artifacts, and G3 documentation/context updates if rejected; do not revert G2, G1, G0, Candidate Registry, D-353, or R64.1.

Phase 65 G4 (2026-05-09): First Real Canonical Dataset Readiness Fixture (D-361) 🟢

  - Decision record:
    - approve the first real canonical dataset readiness fixture.
    - use one tiny Tier 0 `prices_tri` daily-bar slice only.
    - require a manifest and reconcile manifest SHA-256, row count, schema, and date range.
    - validate finite numeric values, duplicate primary keys, monotonic dates per `permno`, price domain, return domain, and freshness.
    - keep sidecars optional for the passing price slice; stale sidecars block only when explicitly required.
    - do not run strategy search, V2 real-data discovery, alpha logic, candidate ranking, alerts, broker calls, or promotion packets.
  - The Decision (Hardcoded):
    - `v2_discovery/readiness/canonical_slice.py` loads only the G4 canonical slice and rejects Tier 2, public-web, operational-market-data, stale, ambiguous, non-finite, duplicate-key, non-monotonic, or impossible-domain artifacts.
    - `v2_discovery/readiness/canonical_readiness.py` emits readiness-only reports with `ready_for_g5 = true` after all gates pass and defaults `report_path = None` so test/dry runs do not refresh artifacts.
    - `data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet*` is the first tiny real canonical dataset fixture.
  - Evidence:
    - `tests/test_g4_real_canonical_readiness_fixture.py`
    - `docs/architecture/g4_real_canonical_readiness_policy.md`
    - `data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet*`
    - `data/registry/g4_real_canonical_readiness_report.json*`
    - `.venv\Scripts\python -m pytest tests\test_g4_real_canonical_readiness_fixture.py -q` -> PASS (`18 passed`)
  - Contract lock:
    - `PH65_G4_READINESS_ONLY := VALID iff (source_quality = canonical) and (source_tier = tier0) and (manifest_reconciles = 1) and (finite_numeric_check = pass) and (duplicate_key_check = pass) and (date_monotonicity_check = pass) and (price_domain_check = pass) and (return_domain_check = pass) and (strategy_search = 0) and (performance_metrics = 0) and (broker_calls = 0) and (alerts = 0)`.
  - Open risks:
    - yfinance legacy migration remains future debt.
    - primary S&P sidecar freshness remains a paper-alert warning through `2023-11-27`.
  - Rollback note:
    - revert only G4 readiness package, focused test, fixture/report artifacts, policy, handover, SAW report, and G4 documentation/context updates if rejected; do not revert G3, G2, G1, G0, Candidate Registry, D-353, or R64.1.

Phase 65 G5 (2026-05-09): Single Canonical Replay, No Alpha (D-362) 🟢

  - Decision record:
    - approve one official V1 canonical replay on the G4 tiny real Tier 0 canonical slice.
    - use predeclared neutral equal weights only.
    - call `core.engine.run_simulation` once and publish mechanical accounting only.
    - do not call V2 proxy on real data.
    - do not run strategy search, alpha logic, ranking, alerts, broker calls, or promotion packets.
  - The Decision (Hardcoded):
    - `v2_discovery/replay/canonical_real_replay.py` loads the G4 canonical slice through readiness gates, builds neutral weights, calls `core.engine.run_simulation`, and builds deterministic positions/ledger evidence.
    - `v2_discovery/replay/canonical_replay_report.py` emits a manifest-backed report with positions, cash, turnover, transaction cost, gross exposure, net exposure, and blocked promotion/alert/broker booleans only.
    - `data/registry/g5_single_canonical_replay_report.json*` records the optional mechanical replay report and manifest.
  - Evidence:
    - `tests/test_g5_single_canonical_replay_no_alpha.py`
    - `docs/architecture/g5_single_canonical_replay_no_alpha_policy.md`
    - `data/registry/g5_single_canonical_replay_report.json*`
    - `.venv\Scripts\python -m pytest tests\test_g5_single_canonical_replay_no_alpha.py -q` -> PASS (`18 passed`)
    - `.venv\Scripts\python -m pytest tests\test_g5_single_canonical_replay_no_alpha.py tests\test_g4_real_canonical_readiness_fixture.py -q` -> PASS (`36 passed`)
    - G5 artifact hash audit -> PASS
  - Contract lock:
    - `PH65_G5_CANONICAL_REPLAY_ONLY := VALID iff (source_quality = canonical) and (source_tier = tier0) and (manifest_reconciles = 1) and (weights = predeclared_equal_weight) and (v1_engine = core.engine.run_simulation) and (v2_proxy_real_data_run = 0) and (performance_metrics = 0) and (promotion_ready = 0) and (broker_calls = 0) and (alerts = 0)`.
  - Open risks:
    - yfinance legacy migration remains future debt.
    - primary S&P sidecar freshness remains a paper-alert warning through `2023-11-27`.
  - Rollback note:
    - revert only G5 replay modules, focused test, report artifacts, policy, handover, SAW report, and G5 documentation/context updates if rejected; do not revert G4, G3, G2, G1, G0, Candidate Registry, D-353, or R64.1.

Phase 65 G6 (2026-05-09): V1/V2 Real-Slice Mechanical Comparison (D-363) 🟢

  - Decision record:
    - approve one V1/V2 mechanical comparison on the G4 tiny real Tier 0 canonical slice.
    - use predeclared neutral equal weights only.
    - call V1 official replay and V2 proxy mechanics separately.
    - compare only mechanical accounting and source identity fields.
    - keep V2 subordinate and non-promotable even when V1/V2 match.
    - do not run strategy search, alpha logic, ranking, alerts, broker calls, or promotion packets.
  - The Decision (Hardcoded):
    - `v2_discovery/replay/real_slice_v1_v2_comparison.py` loads the G4 canonical slice through readiness gates, reuses the G5 V1 replay path, runs V2 proxy ledger mechanics on the same predeclared weights, and compares approved fields only.
    - `v2_discovery/replay/mechanical_comparison_report.py` emits a manifest-backed report with V1/V2 positions, cash, turnover, transaction cost, gross exposure, net exposure, source identity, engine identity, mismatch fields, and blocked promotion/alert/broker booleans only.
    - `data/registry/g6_v1_v2_real_slice_mechanical_report.json*` records the optional mechanical comparison report and manifest.
  - Evidence:
    - `tests/test_g6_v1_v2_real_slice_mechanical_comparison.py`
    - `docs/architecture/g6_v1_v2_real_slice_mechanical_policy.md`
    - `data/registry/g6_v1_v2_real_slice_mechanical_report.json*`
    - `.venv\Scripts\python -m pytest tests\test_g6_v1_v2_real_slice_mechanical_comparison.py -q` -> PASS (`20 passed`)
    - G6 artifact hash audit -> PASS
  - Contract lock:
    - `PH65_G6_MECHANICAL_COMPARISON_ONLY := VALID iff (source_quality = canonical) and (source_tier = tier0) and (manifest_reconciles = 1) and (weights = predeclared_equal_weight) and (v1_engine = core.engine.run_simulation) and (v2_engine = proxy_mechanics) and (comparison_fields = approved_mechanical_set) and (mismatch_count = 0) and (v2_promotion_ready = 0) and (performance_metrics = 0) and (promotion_packet = 0) and (broker_calls = 0) and (alerts = 0)`.
  - Open risks:
    - yfinance legacy migration remains future debt.
    - primary S&P sidecar freshness remains a paper-alert warning through `2023-11-27`.
  - Rollback note:
    - revert only G6 comparison modules, focused test, report artifacts, policy, handover, SAW report, and G6 documentation/context updates if rejected; do not revert G5, G4, G3, G2, G1, G0, Candidate Registry, D-353, or R64.1.

Phase 65 G7 (2026-05-09): Controlled Candidate-Family Definition (D-364) 🟢

  - Decision record:
    - approve the first controlled candidate-family definition before search.
    - define `PEAD_DAILY_V0` with hypothesis, universe, feature allowlist, finite parameter space, fixed trial budget, Tier 0 canonical data policy, validation gates, and multiple-testing policy.
    - keep G7 definition-only: no candidate generation, backtest, replay, proxy run, alpha/performance metric, ranking, alert, broker call, or promotion packet.
  - The Decision (Hardcoded):
    - `v2_discovery/families/schemas.py` defines a frozen family schema with finite allowed features, finite parameter space, required `trial_budget_max`, Tier 0/canonical policy, and promotion-source rejection.
    - `v2_discovery/families/trial_budget.py` computes and validates the finite trial count.
    - `v2_discovery/families/registry.py` writes append-only/versioned family artifacts, requires manifest-backed family definitions before future candidate creation, and emits a definition-only registry report.
    - `v2_discovery/families/validation.py` reconciles family manifests and blocks outcome/performance/ranking fields in the report.
    - `data/registry/candidate_families/pead_daily_v0.json*` records the first family definition and manifest.
  - Evidence:
    - `tests/test_g7_candidate_family_definition.py`
    - `docs/architecture/g7_candidate_family_definition_policy.md`
    - `data/registry/candidate_families/pead_daily_v0.json*`
    - `data/registry/candidate_family_registry_report.json`
    - `.venv\Scripts\python -m pytest tests\test_g7_candidate_family_definition.py -q` -> PASS (`19 passed`)
    - `.venv\Scripts\python -m pytest tests\test_g7_candidate_family_definition.py tests\test_g6_v1_v2_real_slice_mechanical_comparison.py tests\test_g5_single_canonical_replay_no_alpha.py tests\test_g4_real_canonical_readiness_fixture.py tests\test_v2_canonical_replay_fixture.py tests\test_v2_proxy_registered_candidate_flow.py tests\test_v2_fast_proxy_synthetic.py tests\test_v2_fast_proxy_invariants.py tests\test_v2_proxy_boundary.py tests\test_candidate_registry.py -q` -> PASS (`166 passed`)
  - Contract lock:
    - `PH65_G7_DEFINITION_ONLY := VALID iff (family_id = PEAD_DAILY_V0) and (status = defined) and (manifest_reconciles = 1) and (finite_trial_count = 24) and (trial_budget_max = 24) and (data_tier_required = tier0) and (source_quality_required = canonical) and (candidate_generation = 0) and (result_generation = 0) and (performance_metrics = 0) and (promotion_packet = 0) and (broker_calls = 0) and (alerts = 0)`.
  - Open risks:
    - yfinance legacy migration remains future debt.
    - primary S&P sidecar freshness remains a paper-alert warning through `2023-11-27`.
  - Rollback note:
    - revert only G7 family modules, focused test, family/report artifacts, policy, handover, SAW report, and G7 documentation/context updates if rejected; do not revert G6, G5, G4, G3, G2, G1, G0, Candidate Registry, D-353, or R64.1.

Phase 65 G7.1 (2026-05-09): Roadmap Realignment / Product Charter (D-365) 🟢

  - Decision record:
    - approve roadmap realignment before G8 candidate generation.
    - hold G8 PEAD candidate generation until a separate approval.
    - frame Terminal Zero as discretionary augmentation for de-risked asymmetric upside, not generic alpha search and not a trading bot.
    - document the planning allocation model: 90% supercycle gem discovery and 10% buying-range / hold-discipline prompting.
    - keep `PEAD_DAILY_V0` valid but classify it as a tactical signal family.
    - name `SUPERCYCLE_GEM_DAILY_V0` as the primary product family target for the next definition-only phase.
    - define dashboard taxonomy around thesis health, entry discipline, hold discipline, flow/positioning, and regime.
    - treat short-squeeze and CTA-type inputs as dashboard context, not automatic triggers.
    - do not generate candidates, run backtests, replay/proxy runs, search, rankings, alerts, broker calls, live orders, paper trades, or promotion packets.
  - The Decision (Hardcoded):
    - `docs/architecture/product_roadmap_discretionary_augmentation.md` is the product charter for the discretionary augmentation roadmap.
    - `docs/architecture/dashboard_signal_taxonomy.md` is the dashboard state taxonomy and source-quality boundary.
    - `docs/architecture/supercycle_gem_family_policy.md` names the primary product family target for G7.2.
    - `docs/handover/phase65_g71_handover.md` is the PM handover and current-context source for the roadmap realignment.
    - `dashboard.py` now passes the already-created drift monitor dependencies into the promoted drift tab after runtime smoke exposed a missing-argument Streamlit page error.
  - Evidence:
    - `docs/architecture/product_roadmap_discretionary_augmentation.md`
    - `docs/architecture/dashboard_signal_taxonomy.md`
    - `docs/architecture/supercycle_gem_family_policy.md`
    - `docs/handover/phase65_g71_handover.md`
    - `.venv\Scripts\python -m pytest tests\test_g7_candidate_family_definition.py -q` -> PASS
    - `.venv\Scripts\python -m pytest tests\test_dashboard_drift_monitor_integration.py tests\test_drift_monitor_view.py -q` -> PASS
    - `.venv\Scripts\python launch.py --server.headless true --server.port 8631` -> PASS (alive after 30s; no uncaught app execution in stderr)
    - `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS
  - Contract lock:
    - `PH65_G7_1_PRODUCT_CHARTER_ONLY := VALID iff (roadmap = discretionary_augmentation) and (supercycle_focus = 0.90) and (buying_range_hold_prompt_focus = 0.10) and (pead_role = tactical_signal_family) and (primary_family_target = SUPERCYCLE_GEM_DAILY_V0) and (g8_pead_generation = held) and (candidate_generation = 0) and (backtest = 0) and (replay = 0) and (proxy_run = 0) and (strategy_search = 0) and (ranking = 0) and (broker_calls = 0) and (alerts = 0) and (promotion_packet = 0)`.
  - Open risks:
    - yfinance legacy migration remains future debt.
    - primary S&P sidecar freshness remains a paper-alert warning through `2023-11-27`.
  - Rollback note:
    - revert only G7.1 docs/context/SAW/handover updates if rejected; do not revert G7 family code, G7 artifacts, G6, G5, G4, G3, G2, G1, G0, Candidate Registry, D-353, or R64.1.

Phase 65 G7.1A (2026-05-09): Starter Docs / PRD / Product Spec Rewrite (D-366) 🟡

  - Decision record:
    - approve a docs-only starter-docs and product-spec rewrite before G7.2, G7.4, G7.5, G8, or any search/candidate work.
    - name the product `Unified Opportunity Engine`.
    - define the product as:
      - Primary Alpha: Supercycle Gem Discovery / de-risked asymmetric upside.
      - Secondary Alpha: GodView Market Behavior Intelligence.
      - Output Layer: Decision Augmentation through dashboard states and paper-only prompts.
    - state plainly that Terminal Zero is not a trading bot.
    - make root `PRD.md` and `PRODUCT_SPEC.md` the product canon.
    - keep lowercase `docs/prd.md` and `docs/spec.md` aligned with canon notices to prevent stale-entry drift.
    - move Supercycle Gem Family Definition downstream to G7.4; G7.2 is now Unified Opportunity Engine State Machine.
    - set immediate next action to `approve_g7_1b_data_infra_gap_or_g7_2_state_machine`.
    - keep G7.2, G7.4, G7.5, G8, search, candidate generation, backtest, replay, proxy run, provider ingestion, ranking, alerts, broker calls, Alpaca live behavior, OpenClaw notification, and dashboard-runtime implementation held.
  - The Decision (Hardcoded):
    - `README.md`, `PRD.md`, and `PRODUCT_SPEC.md` are the starter product canon for the Unified Opportunity Engine.
    - `docs/architecture/top_level_roadmap.md` records the G7.1A-G12 roadmap.
    - `docs/architecture/unified_opportunity_engine.md` defines the three product layers and future state-engine concept.
    - `docs/architecture/godview_signal_taxonomy.md` defines GodView signal families and use boundaries.
    - `docs/architecture/data_infra_gap_assessment.md` documents current governance readiness and future GodView provider gaps.
    - `docs/architecture/codex_agent_research_workflow.md` defines allowed and forbidden Codex/Chrome research-agent uses.
    - `docs/architecture/dashboard_product_spec.md` defines future dashboard states without runtime behavior.
  - Evidence:
    - `README.md`
    - `PRD.md`
    - `PRODUCT_SPEC.md`
    - `docs/architecture/top_level_roadmap.md`
    - `docs/architecture/unified_opportunity_engine.md`
    - `docs/architecture/godview_signal_taxonomy.md`
    - `docs/architecture/data_infra_gap_assessment.md`
    - `docs/architecture/codex_agent_research_workflow.md`
    - `docs/architecture/dashboard_product_spec.md`
    - validation evidence pending final G7.1A SAW closeout.
  - Contract lock:
    - `PH65_G7_1A_DOCS_ONLY := VALID iff (product = Unified Opportunity Engine) and (primary_alpha = Supercycle Gem Discovery) and (secondary_alpha = GodView Market Behavior Intelligence) and (output_layer = Decision Augmentation) and (root_prd_spec_canon = 1) and (immediate_next_action = approve_g7_1b_data_infra_gap_or_g7_2_state_machine) and (g7_2_approved = 0) and (g7_4_family_definition = 0) and (g8_generation = held) and (candidate_generation = 0) and (search = 0) and (backtest = 0) and (replay = 0) and (proxy_run = 0) and (provider_ingestion = 0) and (ranking = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.
  - Open risks:
    - yfinance legacy migration remains future debt.
    - primary S&P sidecar freshness remains stale through `2023-11-27`.
    - full GodView requires future source policy and provider design.
  - Rollback note:
    - revert only G7.1A starter-docs/product-spec/context/SAW/handover updates if rejected; do not revert G7.1, G7 family artifacts, dashboard drift-monitor fix, or prior G phases.

Phase 65 G7.1B (2026-05-09): Data + Infra Gap Assessment (D-367) 🟡

  - Decision record:
    - approve G7.1B before G7.2 state-machine work.
    - keep scope to docs, architecture, and source mapping only.
    - answer whether the current repo/data layer can support the GodView Opportunity Engine.
    - classify each GodView signal family by readiness, provider need, freshness, trust level, and build priority.
    - document future provider ports only; do not implement them.
    - require future GodView signals to carry signal id, family, ticker/theme, source quality, provider/feed, observed-vs-estimated label, freshness, latency, as-of timestamp, confidence, allowed use, forbidden use, and manifest URI.
    - define observed, estimated, and inferred labels.
    - allow Codex/Chrome research agents only for research capture and docs; forbid alpha evidence, source approval, canonical market-data writes, scraping without policy, alerts, and trading actions.
    - hold G7.2 and G8 until a separate downstream decision.
  - The Decision (Hardcoded):
    - `docs/architecture/godview_data_infra_gap_assessment.md` records the answer: current infra is governance-ready and daily-price-ready, not full-GodView-ready.
    - `docs/architecture/godview_signal_source_matrix.md` records source/readiness/freshness/trust/build-priority mapping.
    - `docs/architecture/godview_provider_roadmap.md` names future provider ports without creating provider files.
    - `docs/architecture/godview_signal_freshness_policy.md` defines future freshness buckets and required time fields.
    - `docs/architecture/godview_observed_vs_estimated_policy.md` defines observed, estimated, and inferred labels.
    - `docs/architecture/codex_chrome_research_sop.md` defines research-agent allowed/forbidden uses.
  - Evidence:
    - `docs/architecture/godview_data_infra_gap_assessment.md`
    - `docs/architecture/godview_signal_source_matrix.md`
    - `docs/architecture/godview_provider_roadmap.md`
    - `docs/architecture/godview_signal_freshness_policy.md`
    - `docs/architecture/godview_observed_vs_estimated_policy.md`
    - `docs/architecture/codex_chrome_research_sop.md`
    - `docs/handover/phase65_g71b_handover.md`
    - validation evidence pending final G7.1B SAW closeout.
  - Contract lock:
    - `PH65_G7_1B_DATA_INFRA_GAP_ONLY := VALID iff (source_matrix = published) and (provider_roadmap = documented_only) and (current_infra = governance_ready_not_full_godview_ready) and (observed_estimated_inferred_policy = published) and (freshness_policy = published) and (codex_chrome_research_only = 1) and (g7_2_approved = 0) and (g8_generation = held) and (provider_code = 0) and (ingestion = 0) and (candidate_generation = 0) and (search = 0) and (backtest = 0) and (replay = 0) and (proxy_run = 0) and (ranking = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.
  - Open risks:
    - yfinance migration remains future debt.
    - primary S&P sidecar freshness remains stale through `2023-11-27`.
    - full GodView requires future source policy, licensing decisions, and provider implementation.
    - broad compileall workspace hygiene remains inherited debt.
  - Rollback note:
    - revert only G7.1B architecture docs/context/SAW/handover/governance-log updates if rejected; do not revert G7.1A product canon, G7.1 roadmap realignment, G7 family artifacts, dashboard drift-monitor fix, or prior G phases.

Phase 65 G7.1C (2026-05-09): Open-Source Repo + Data/API Availability Survey (D-368) 🟡

  - Decision record:
    - approve G7.1C as docs/research and architecture planning only.
    - capture the supplied open-source repo and data/API availability survey as a `docs/research` artifact with source audit pending.
    - treat OpenBB, LEAN, Qlib, vectorbt, FinRL, pandas-datareader, Freqtrade, Hummingbot, and CCXT as architecture references, not canonical GodView source approval.
    - plan the immediate no-cost public-source path as SEC + FINRA + CFTC + public macro after audit only.
    - keep yfinance quarantined as Tier 2 discovery only.
    - keep OPRA/options, IV, options whales, gamma/dealer maps, dark-pool/block, microstructure, ETF/passive flows, and governed news/narrative behind future provider/source decisions.
    - hold G7.2 and provider implementation until source audit is completed or explicitly waived.
    - do not add provider code, ingestion, state machine, candidate generation, search, backtests, replays, proxy runs, ranking, alerts, broker calls, paper trades, promotion packets, or dashboard runtime behavior.
  - The Decision (Hardcoded):
    - `docs/research/g7_1c_open_source_repo_data_api_availability_survey_20260509.md` is the audit-pending research capture.
    - `docs/architecture/open_source_data_source_survey.md` records open-source architecture lessons.
    - `docs/architecture/godview_api_availability_matrix.md` separates ready, no-cost/public, paid/licensed, operational, and delayed/context sources.
    - `docs/architecture/godview_provider_selection_policy.md` defines source audit gates before provider implementation.
    - `docs/architecture/godview_build_vs_borrow_decision.md` records build-vs-borrow and the held no-cost implementation plan.
  - Evidence:
    - `docs/research/g7_1c_open_source_repo_data_api_availability_survey_20260509.md`
    - `docs/architecture/open_source_data_source_survey.md`
    - `docs/architecture/godview_api_availability_matrix.md`
    - `docs/architecture/godview_provider_selection_policy.md`
    - `docs/architecture/godview_build_vs_borrow_decision.md`
    - validation evidence pending final G7.1C SAW closeout.
  - Contract lock:
    - `PH65_G7_1C_OPEN_SOURCE_API_SURVEY_ONLY := VALID iff (research_capture = audit_pending) and (open_source_repos = architecture_reference_only) and (no_cost_path = sec_finra_cftc_public_macro_after_audit) and (options_iv_gamma_microstructure = provider_decision_gap) and (g7_2_approved = 0) and (provider_code = 0) and (ingestion = 0) and (candidate_generation = 0) and (search = 0) and (backtest = 0) and (replay = 0) and (proxy_run = 0) and (ranking = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.
  - Open risks:
    - source claims are audit-pending and must not be treated as independently verified.
    - yfinance migration remains future debt.
    - primary S&P sidecar freshness remains stale through `2023-11-27`.
    - full GodView requires future source policy, licensing decisions, and provider implementation.
    - broad compileall workspace hygiene remains inherited debt.
  - Rollback note:
    - revert only G7.1C research/architecture/context/SAW/handover/governance-log updates if rejected; do not revert G7.1B source matrix, G7.1A product canon, G7.1 roadmap realignment, G7 family artifacts, dashboard drift-monitor fix, or prior G phases.

Phase 65 G7.1C (2026-05-09): Official Public Source Audit (D-369) 🟡

  - Decision record:
    - approve G7.1C official public source audit as audit-only documentation.
    - verify SEC EDGAR / data.sec.gov, FINRA short interest, FINRA Reg SHO daily short-sale volume, FINRA OTC/ATS transparency, CFTC COT/TFF, FRED/ALFRED, and Ken French Data Library against official/public docs.
    - record source rights, auth, API key, cost, freshness, history depth, usage constraints, entity keys, raw locators, as-of timestamp availability, observed/estimated/inferred label, allowed use, forbidden use, fixture feasibility, implementation priority, and open questions.
    - define tiny fixture schemas for later only; do not download data or create fixture files.
    - hold provider implementation until explicit approval.
    - state clearly that SEC / FINRA / CFTC / FRED / Ken French can support future GodView public-source modules, but audit approval does not authorize ingestion.
    - keep CFTC COT/TFF as broad regime/futures positioning only, not direct single-name CTA buying evidence.
    - keep Reg SHO daily short-sale volume separate from short interest.
    - do not add provider code, ingestion, state machine, candidate generation, search, backtests, replays, proxy runs, ranking, alerts, broker calls, paper trades, promotion packets, physical fixtures, or dashboard runtime behavior.
  - The Decision (Hardcoded):
    - `docs/architecture/godview_public_source_audit.md` records the official/public source audit.
    - `docs/architecture/godview_source_terms_matrix.md` records the required-column terms matrix.
    - `docs/architecture/godview_tiny_fixture_schema_plan.md` records future fixture schemas only.
    - `docs/architecture/godview_public_provider_priority.md` records the one-tiny-fixture-or-hold priority.
    - `docs/handover/phase65_g71c_source_audit_handover.md` is the canonical PM handover.
    - `docs/handover/phase65_g71-0c_handover.md` is the current context selector alias.
  - Evidence:
    - `docs/architecture/godview_public_source_audit.md`
    - `docs/architecture/godview_source_terms_matrix.md`
    - `docs/architecture/godview_tiny_fixture_schema_plan.md`
    - `docs/architecture/godview_public_provider_priority.md`
    - `docs/handover/phase65_g71c_source_audit_handover.md`
    - `docs/saw_reports/saw_phase65_g7_1c_public_source_audit_20260509.md`
  - Contract lock:
    - `PH65_G7_1C_PUBLIC_SOURCE_AUDIT_ONLY := VALID iff (official_source_audit = complete) and (source_terms_matrix = published) and (tiny_fixture_schema_plan = plan_only) and (provider_priority = published) and (physical_fixture = 0) and (provider_code = 0) and (ingestion = 0) and (state_machine = 0) and (candidate_generation = 0) and (search = 0) and (backtest = 0) and (replay = 0) and (proxy_run = 0) and (ranking = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.
  - Open risks:
    - yfinance migration remains future debt.
    - primary S&P sidecar freshness remains stale through `2023-11-27`.
    - GodView provider gap remains open until a future provider/fixture proof is explicitly approved.
    - options/OPRA/IV/gamma/whale-flow license gap remains out of scope.
    - broad compileall workspace hygiene remains inherited debt.
  - Rollback note:
    - revert only G7.1C audit docs, matrices, context, handover, and SAW report; do not revert G7.1A, G7.1, G7 family artifacts, dashboard drift-monitor fix, or prior G phases.

Phase 65 G7.1D (2026-05-09): SEC Tiny Public Fixture Proof (D-370) 🟡

  - Decision record:
    - approve G7.1D as one tiny SEC data.sec.gov public-provider fixture proof.
    - choose SEC first, not FINRA, because SEC is official, public, no-key, lower interpretation risk, and maps well to Supercycle thesis/ownership/fundamentals evidence.
    - use exactly one stable large-cap entity: Apple Inc. / AAPL / CIK `0000320193`.
    - create one static companyfacts fixture and one static submissions fixture with sidecar manifests.
    - validate manifest presence, SHA-256, row counts, date parsing, CIK format, duplicate primary-key rejection, non-finite numeric rejection, source quality, allowed/forbidden use, and observed label.
    - do not build a live SEC provider, broad downloader, scheduled ingestion, canonical lake write, ticker universe expansion, Form 4/13F strategy logic, GodView score, candidate generator, state machine, dashboard runtime behavior, alert, or broker path.
    - keep FINRA, CFTC, FRED, Ken French, and G7.2 held until separate approval.
  - The Decision (Hardcoded):
    - `docs/architecture/sec_tiny_fixture_policy.md` records G7.1D SEC source policy and forbidden scope.
    - `docs/architecture/sec_public_provider_fixture_plan.md` records the static fixture shape and validation plan.
    - `data/fixtures/sec/sec_companyfacts_tiny.json` stores two observed Apple Inc. companyfacts rows.
    - `data/fixtures/sec/sec_companyfacts_tiny.json.manifest.json` stores the companyfacts manifest.
    - `data/fixtures/sec/sec_submissions_tiny.json` stores five observed Apple Inc. submission metadata rows.
    - `data/fixtures/sec/sec_submissions_tiny.json.manifest.json` stores the submissions manifest.
    - `tests/test_g7_1d_sec_tiny_fixture.py` validates the static fixture proof and negative paths.
    - `docs/handover/phase65_g71d_sec_tiny_fixture_handover.md` is the canonical PM handover.
  - Evidence:
    - `docs/architecture/sec_tiny_fixture_policy.md`
    - `docs/architecture/sec_public_provider_fixture_plan.md`
    - `data/fixtures/sec/sec_companyfacts_tiny.json`
    - `data/fixtures/sec/sec_companyfacts_tiny.json.manifest.json`
    - `data/fixtures/sec/sec_submissions_tiny.json`
    - `data/fixtures/sec/sec_submissions_tiny.json.manifest.json`
    - `tests/test_g7_1d_sec_tiny_fixture.py`
    - validation evidence PASS: focused fixture tests, focused fixture + context-builder tests, full pytest, pip check, scoped compile, dashboard drift regression, launch smoke, data readiness, minimal validation lab, forbidden implementation scan, secret scan, artifact hash audit, context rebuild/validation, SAW report validation, and closure packet validation.
  - Contract lock:
    - `PH65_G7_1D_SEC_TINY_FIXTURE_ONLY := VALID iff (sec_static_fixture = 1) and (sec_companyfacts_rows = 2) and (sec_submissions_rows = 5) and (manifest_hash_match = 1) and (row_count_match = 1) and (cik_format_valid = 1) and (date_fields_parse = 1) and (duplicate_primary_key_rejected = 1) and (non_finite_numeric_rejected = 1) and (source_quality = public_official_observed) and (observed_label = observed) and (provider_code = 0) and (broad_downloader = 0) and (ingestion = 0) and (canonical_lake_write = 0) and (state_machine = 0) and (candidate_generation = 0) and (ranking = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.
  - Open risks:
    - yfinance migration remains future debt.
    - primary S&P sidecar freshness remains stale through `2023-11-27`.
    - FINRA short-interest policy details remain future work.
    - GodView provider gap remains open after this static proof.
    - broad compileall workspace hygiene remains inherited debt.
  - Rollback note:
    - revert only G7.1D SEC fixture docs, fixture files, test file, context, handover, and SAW report; do not revert G7.1C audit docs or prior Phase 65 artifacts.

Phase 65 G7.1E (2026-05-10): FINRA Short Interest Tiny Fixture Proof (D-371)

  - Decision record:
    - approve G7.1E as one tiny FINRA Equity Short Interest public fixture proof.
    - use short interest first, not Reg SHO short-sale volume, because short interest maps to delayed squeeze-base / positioning context while Reg SHO daily volume is a separate daily trading-activity dataset.
    - use exactly one settlement date, `2026-04-15`, and exactly three tickers: `AAPL`, `TSLA`, and `GME`.
    - create one static CSV fixture with one sidecar manifest; do not build a live FINRA provider or broad downloader.
    - validate manifest presence, SHA-256, row count, settlement-date parsing, ticker presence, finite/non-negative numeric fields, duplicate primary-key rejection, source quality, allowed/forbidden use, observed label, and Reg SHO field exclusion.
    - lock the interpretation rule: short interest may say "short base exists"; it may not say "forced covering is happening now."
    - do not add FINRA provider code, live FINRA API calls, bulk downloads, Reg SHO ingestion, OTC/ATS ingestion, squeeze scoring, short-squeeze ranking, candidate generation, G7.2 state machine, dashboard runtime behavior, alerts, broker calls, paper trades, or promotion packets.
    - keep CFTC, FRED, Ken French, options/IV/OPRA, and G7.2 held until separate approval.
  - The Decision (Hardcoded):
    - `docs/architecture/finra_short_interest_tiny_fixture_policy.md` records G7.1E FINRA source policy and forbidden scope.
    - `docs/architecture/finra_short_interest_vs_short_volume_policy.md` records the short-interest-vs-Reg-SHO interpretation boundary.
    - `docs/architecture/finra_public_provider_fixture_plan.md` records the static fixture shape and validation plan.
    - `data/fixtures/finra/finra_short_interest_tiny.csv` stores three observed FINRA short-interest rows for settlement date `2026-04-15`.
    - `data/fixtures/finra/finra_short_interest_tiny.manifest.json` stores the source-rights/provenance/hash manifest.
    - `tests/test_g7_1e_finra_short_interest_tiny_fixture.py` validates the static fixture proof and negative paths.
    - `docs/handover/phase65_g71e_finra_tiny_fixture_handover.md` is the canonical PM handover.
    - `docs/handover/phase65_g71-00e_handover.md` is the current context selector alias.
    - `docs/handover/phase65_g71-0e_handover.md` is the compatibility selector alias.
    - `docs/saw_reports/saw_phase65_g7_1e_finra_tiny_fixture_20260509.md` records the SAW closeout.
  - Evidence:
    - `docs/architecture/finra_short_interest_tiny_fixture_policy.md`
    - `docs/architecture/finra_short_interest_vs_short_volume_policy.md`
    - `docs/architecture/finra_public_provider_fixture_plan.md`
    - `data/fixtures/finra/finra_short_interest_tiny.csv`
    - `data/fixtures/finra/finra_short_interest_tiny.manifest.json`
    - `tests/test_g7_1e_finra_short_interest_tiny_fixture.py`
    - validation evidence PASS: focused fixture tests, focused fixture + context-builder tests, full pytest, pip check, scoped compile, dashboard drift regression, launch smoke, data readiness, minimal validation lab, forbidden implementation scan, secret scan, artifact hash audit, context rebuild/validation, SAW report validation, evidence-map validation, and closure packet validation.
  - Contract lock:
    - `PH65_G7_1E_FINRA_TINY_FIXTURE_ONLY := VALID iff (finra_static_fixture = 1) and (dataset_type = short_interest) and (settlement_dates = 1) and (tickers = 3) and (row_count = 3) and (manifest_hash_match = 1) and (row_count_match = 1) and (settlement_date_parses = 1) and (ticker_present = 1) and (duplicate_primary_key_rejected = 1) and (non_finite_numeric_rejected = 1) and (non_negative_numeric_fields = 1) and (source_quality = public_official_observed) and (observed_label = observed) and (reg_sho_fields_present = 0) and (provider_code = 0) and (live_api_call = 0) and (bulk_downloader = 0) and (reg_sho_ingestion = 0) and (otc_ats_ingestion = 0) and (state_machine = 0) and (candidate_generation = 0) and (squeeze_score = 0) and (ranking = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.
  - Open risks:
    - yfinance migration remains future debt.
    - primary S&P sidecar freshness remains stale through `2023-11-27`.
    - Reg SHO policy and fixture remain future work and must not be conflated with short interest.
    - GodView provider gap remains open after this static proof.
    - broad compileall workspace hygiene remains inherited debt.
  - Rollback note:
    - revert only G7.1E FINRA fixture docs, fixture files, test file, context, handover, provider-priority update, governance-log updates, and SAW report; do not revert G7.1D SEC fixture docs or prior Phase 65 artifacts.

Phase 65 G7.1F (2026-05-10): CFTC COT/TFF Tiny Fixture Proof (D-372)

  - Decision record:
    - approve G7.1F as one tiny CFTC Commitments of Traders / Traders in Financial Futures public fixture proof.
    - use CFTC TFF next because it supports broad futures-positioning / systematic-regime context for GodView, while remaining explicitly unable to prove single-name CTA buying.
    - use exactly one report date, `2026-05-08`, and exactly one as-of position date, `2026-05-05`.
    - use exactly two broad financial futures markets: `E-Mini S&P 500` and `UST 10Y Note`.
    - use exactly four TFF trader categories: `Dealer/Intermediary`, `Asset Manager/Institutional`, `Leveraged Funds`, and `Other Reportables`.
    - create one static CSV fixture with one sidecar manifest; do not build a live CFTC provider or broad downloader.
    - validate manifest presence, SHA-256, row count, report-date parsing, as-of-position-date parsing, market/code/category presence, finite/non-negative numeric fields, duplicate primary-key rejection, source quality, allowed/forbidden use, observed label, and single-name field exclusion.
    - lock the interpretation rule: CFTC TFF may say "systematic/regime positioning context is supportive or hostile"; it may not say "CTAs are buying this stock today."
    - do not add CFTC provider code, live CFTC API calls, bulk downloads, CTA scoring, single-name CTA inference, buy/sell/hold state-machine input, standalone ranking factor, dashboard runtime behavior, alerts, broker calls, paper trades, or promotion packets.
    - keep FRED/Ken French, Reg SHO, ATS/dark-pool, options/IV/gamma/whale data, and G7.2 held until separate approval.
  - The Decision (Hardcoded):
    - `docs/architecture/cftc_tff_tiny_fixture_policy.md` records G7.1F CFTC source policy and forbidden scope.
    - `docs/architecture/cftc_cot_tff_usage_policy.md` records the broad-regime-vs-single-name-CTA interpretation boundary.
    - `docs/architecture/cftc_public_provider_fixture_plan.md` records the static fixture shape and validation plan.
    - `data/fixtures/cftc/cftc_tff_tiny.csv` stores eight observed CFTC TFF rows for report date `2026-05-08`.
    - `data/fixtures/cftc/cftc_tff_tiny.manifest.json` stores the source-rights/provenance/hash manifest.
    - `tests/test_g7_1f_cftc_tff_tiny_fixture.py` validates the static fixture proof and negative paths.
    - `docs/handover/phase65_g71f_cftc_tiny_fixture_handover.md` is the canonical PM handover.
    - `docs/handover/phase65_g71-000f_handover.md` is the current context selector alias.
    - `docs/handover/phase65_g71-0f_handover.md` is the compatibility selector alias.
    - `docs/saw_reports/saw_phase65_g7_1f_cftc_tiny_fixture_20260509.md` records the SAW closeout.
  - Evidence:
    - `docs/architecture/cftc_tff_tiny_fixture_policy.md`
    - `docs/architecture/cftc_cot_tff_usage_policy.md`
    - `docs/architecture/cftc_public_provider_fixture_plan.md`
    - `data/fixtures/cftc/cftc_tff_tiny.csv`
    - `data/fixtures/cftc/cftc_tff_tiny.manifest.json`
    - `tests/test_g7_1f_cftc_tff_tiny_fixture.py`
    - validation evidence PASS: focused fixture tests, focused fixture + context-builder tests, full pytest, pip check, scoped compile, dashboard drift regression, launch smoke, data readiness, minimal validation lab, forbidden implementation scan, secret scan, artifact hash audit, context rebuild/validation, SAW report validation, evidence-map validation, and closure packet validation.
  - Contract lock:
    - `PH65_G7_1F_CFTC_TFF_TINY_FIXTURE_ONLY := VALID iff (cftc_static_fixture = 1) and (dataset_type = futures_positioning) and (report_dates = 1) and (asof_position_dates = 1) and (markets = 2) and (trader_categories = 4) and (row_count = 8) and (manifest_hash_match = 1) and (row_count_match = 1) and (report_date_parses = 1) and (asof_position_date_parses = 1) and (market_name_present = 1) and (contract_market_code_present = 1) and (trader_category_allowed = 1) and (duplicate_primary_key_rejected = 1) and (non_finite_numeric_rejected = 1) and (non_negative_numeric_fields = 1) and (source_quality = public_official_observed) and (observed_label = observed) and (single_name_inference_forbidden = 1) and (provider_code = 0) and (live_api_call = 0) and (bulk_downloader = 0) and (cta_score = 0) and (single_name_inference = 0) and (state_machine = 0) and (candidate_generation = 0) and (ranking = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.
  - Open risks:
    - yfinance migration remains future debt.
    - primary S&P sidecar freshness remains stale through `2023-11-27`.
    - Reg SHO policy and fixture remain future work and must not be conflated with short interest.
    - GodView provider gap remains open after this static proof.
    - broad compileall workspace hygiene remains inherited debt.
  - Rollback note:
    - revert only G7.1F CFTC fixture docs, fixture files, test file, context, handover, provider-priority update, governance-log updates, and SAW report; do not revert G7.1E FINRA fixture docs or prior Phase 65 artifacts.

Phase 65 G7.1G (2026-05-09): FRED / Ken French Tiny Fixture Proof (D-373)

  - Decision record:
    - approve G7.1G as one tiny FRED macro fixture and one tiny Ken French factor fixture proof.
    - use FRED / ALFRED next because official macro series and real-time-period semantics matter for future macro/regime context without hindsight leakage.
    - use the Kenneth French Data Library because public research factor returns are a standard benchmark/factor context source.
    - use exactly three FRED macro series: `DGS10`, `M2SL`, and `BAA10Y`, with three dates per series.
    - use exactly one Ken French dataset: `fama_french_3_factors_monthly`, with four monthly dates and long-form `Mkt-RF`, `SMB`, and `HML` factor rows.
    - create static CSV fixtures with sidecar manifests; do not build a live FRED provider, Ken French provider, downloader, or API client.
    - validate manifest presence, SHA-256, row count, date range, date parsing, finite numeric values, duplicate primary-key rejection, source quality, allowed/forbidden use, observed label, FRED API-key-required label, and score/runtime field exclusion.
    - lock the interpretation rule: FRED may support macro context and future regime panels, but not a macro regime score in this phase; Ken French may support factor context and later benchmark comparison, but not alpha claims or candidate ranking in this phase.
    - do not add live API calls, API key handling, bulk downloads, macro regime score, factor regime score, signal ranking, candidate generation, G7.2 state machine, dashboard runtime behavior, alerts, broker calls, paper trades, or promotion packets.
    - hold G7.2 until separate approval.
  - The Decision (Hardcoded):
    - `docs/architecture/fred_ken_french_tiny_fixture_policy.md` records G7.1G source policy and forbidden scope.
    - `docs/architecture/macro_factor_context_usage_policy.md` records macro/factor context-only interpretation policy.
    - `docs/architecture/fred_ken_french_public_provider_fixture_plan.md` records the static fixture shapes and validation plan.
    - `data/fixtures/fred/fred_macro_tiny.csv` stores nine observed FRED macro rows.
    - `data/fixtures/fred/fred_macro_tiny.manifest.json` stores the FRED source-rights/provenance/hash manifest.
    - `data/fixtures/ken_french/ken_french_factor_tiny.csv` stores twelve observed Ken French factor-return rows.
    - `data/fixtures/ken_french/ken_french_factor_tiny.manifest.json` stores the Ken French source-rights/provenance/hash manifest.
    - `tests/test_g7_1g_fred_ken_french_tiny_fixture.py` validates the static fixture proof and negative paths.
    - `docs/handover/phase65_g71g_fred_ken_french_tiny_fixture_handover.md` is the canonical PM handover.
    - `docs/handover/phase65_g71-0000g_handover.md` is the current context selector alias.
    - `docs/handover/phase65_g71-0g_handover.md` is the compatibility selector alias.
    - `docs/saw_reports/saw_phase65_g7_1g_fred_ken_french_tiny_fixture_20260509.md` records the SAW closeout.
  - Evidence:
    - `docs/architecture/fred_ken_french_tiny_fixture_policy.md`
    - `docs/architecture/macro_factor_context_usage_policy.md`
    - `docs/architecture/fred_ken_french_public_provider_fixture_plan.md`
    - `data/fixtures/fred/fred_macro_tiny.csv`
    - `data/fixtures/fred/fred_macro_tiny.manifest.json`
    - `data/fixtures/ken_french/ken_french_factor_tiny.csv`
    - `data/fixtures/ken_french/ken_french_factor_tiny.manifest.json`
    - `tests/test_g7_1g_fred_ken_french_tiny_fixture.py`
    - validation evidence PASS: focused fixture tests, focused fixture + context-builder tests, full pytest, pip check, scoped compile, dashboard drift regression, launch smoke, data readiness, minimal validation lab, forbidden implementation scan, secret scan, artifact hash audit, context rebuild/validation, SAW report validation, evidence-map validation, and closure packet validation.
  - Contract lock:
    - `PH65_G7_1G_FRED_KEN_FRENCH_TINY_FIXTURE_ONLY := VALID iff (fred_static_fixture = 1) and (ken_french_static_fixture = 1) and (fred_series = 3) and (fred_rows = 9) and (ken_french_datasets = 1) and (ken_french_rows = 12) and (manifest_hash_match = 1) and (row_count_match = 1) and (date_range_match = 1) and (date_fields_parse = 1) and (series_id_present = 1) and (dataset_id_present = 1) and (numeric_values_finite = 1) and (duplicate_primary_key_rejected = 1) and (source_quality_present = 1) and (observed_label = observed) and (allowed_forbidden_use_present = 1) and (fred_api_key_required_label = true_for_live_api) and (provider_code = 0) and (live_api_call = 0) and (api_key_handling = 0) and (bulk_downloader = 0) and (macro_regime_score = 0) and (factor_regime_score = 0) and (state_machine = 0) and (candidate_generation = 0) and (ranking = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.
  - Open risks:
    - yfinance migration remains future debt.
    - primary S&P sidecar freshness remains stale through `2023-11-27`.
    - Reg SHO policy and fixture remain future work and must not be conflated with short interest.
    - GodView provider gap remains open after this static proof.
    - FRED live API key handling and series rights remain future provider-policy work.
    - broad compileall workspace hygiene remains inherited debt.
  - Rollback note:
    - revert only G7.1G FRED / Ken French fixture docs, fixture files, test file, context, handover, provider-priority update, governance-log updates, and SAW report; do not revert G7.1F CFTC fixture docs or prior Phase 65 artifacts.

Phase 65 G7.2 (2026-05-10): Unified Opportunity State Machine (D-374)

  - Decision record:
    - approve G7.2 as definition-only Unified Opportunity State Machine work.
    - define finite opportunity states, reason codes, transition evidence schemas, forbidden jumps, and validator tests.
    - keep all score, rank, alert, broker, provider, ingestion, search, backtest, replay, proxy, and dashboard-runtime behavior blocked.
    - require `THESIS_BROKEN` to override bullish market behavior.
    - block direct `THESIS_CANDIDATE -> BUYING_RANGE` jumps.
    - require `LEFT_SIDE_RISK` to pass through `ACCUMULATION_WATCH` or `CONFIRMATION_WATCH` before `BUYING_RANGE`.
    - block estimated-only evidence from creating `BUYING_RANGE`.
    - block inferred-only evidence from creating `LET_WINNER_RUN`.
  - The Decision (Hardcoded):
    - `docs/architecture/unified_opportunity_state_machine.md` records the state-machine definition.
    - `docs/architecture/opportunity_state_transition_policy.md` records the transition policy.
    - `docs/architecture/opportunity_state_forbidden_jumps.md` records the hard forbidden-jump register.
    - `opportunity_engine/states.py` stores the finite state and reason-code enums.
    - `opportunity_engine/schemas.py` stores the transition evidence schemas.
    - `opportunity_engine/transitions.py` stores the transition validator.
    - `tests/test_g7_2_opportunity_state_machine.py` validates the state-machine invariants.
    - `docs/handover/phase65_g72_state_machine_handover.md` is the canonical PM handover.
    - `docs/saw_reports/saw_phase65_g7_2_state_machine_20260509.md` records the SAW closeout.
  - Evidence:
    - focused G7.2 tests PASS.
    - scoped compile PASS.
    - closure packet validation PASS.
    - SAW report validation PASS.
    - evidence validation PASS.
  - Contract lock:
    - `PH65_G7_2_STATE_DEFINITION_ONLY := VALID iff (state_enum_complete = 1) and (reason_codes_present = 1) and (source_classes_present = 1) and (forbidden_jump_not_requested = 1) and (thesis_broken_override_applied = 1) and (estimated_only_buying_range = 0) and (inferred_only_let_winner_run = 0) and (score_rank_alert_broker_fields_absent = 1) and (candidate_generation = 0) and (search = 0) and (backtest = 0) and (replay = 0) and (proxy_run = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.

Phase 65 G7.3 (2026-05-10): Signal-to-State Source Eligibility Map (D-375)

  - Decision record:
    - approve G7.3 as policy-only Signal-to-State Source Eligibility Map work.
    - map every GodView signal family to source class, observed/estimated/inferred label, allowed state influence, forbidden state influence, freshness requirement, and confidence label.
    - keep provider classes, live API calls, source registry implementation, scoring, ranking, alerts, broker, and dashboard runtime behavior blocked.
    - preserve SEC/FINRA/CFTC/FRED/Ken French fixture pillars as context/reason-code sources only.
    - keep Tier 2/yfinance from moving any state toward `BUYING_RANGE` or `LET_WINNER_RUN`.
    - keep options/IV/gamma/whales as provider-gap signals.
  - The Decision (Hardcoded):
    - `docs/architecture/godview_signal_to_state_map.md` records the full source-to-state map.
    - `docs/architecture/godview_source_eligibility_policy.md` records source-class eligibility.
    - `docs/architecture/godview_signal_confidence_policy.md` records confidence labels and freshness degradation.
    - `opportunity_engine/source_classes.py` stores source class, signal family, and confidence enums.
    - `opportunity_engine/signal_policy.py` stores the signal-family policy map.
    - `tests/test_g7_3_signal_to_state_source_map.py` validates the policy boundaries.
    - `docs/handover/phase65_g73_signal_to_state_handover.md` is the canonical PM handover.
    - `docs/saw_reports/saw_phase65_g7_3_signal_to_state_map_20260509.md` records the SAW closeout.
  - Evidence:
    - focused G7.3 tests PASS.
    - scoped compile PASS.
    - closure packet validation PASS.
    - SAW report validation PASS.
    - evidence validation PASS.
  - Contract lock:
    - `PH65_G7_3_POLICY_ONLY := VALID iff (source_class_enum_complete = 1) and (signal_family_map_complete = 1) and (public_fixtures_context_only = 1) and (estimated_only_buying_range = 0) and (tier2_yfinance_action_state = 0) and (provider_gap_signals = 1) and (short_interest_context_only = 1) and (cftc_broad_regime_only = 1) and (fred_ken_french_context_only = 1) and (provider_code = 0) and (live_api_call = 0) and (source_registry = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.

Phase 65 G7.4 (2026-05-10): Dashboard Wireframe / Product-State Spec (D-376)

  - Decision record:
    - approve G7.4 as product-spec-only dashboard wireframe work.
    - define state-first dashboard sections, watchlist card fields, and daily brief structure.
    - keep dashboard runtime code, Streamlit edits, candidate cards, alerts, provider calls, broker calls, score, ranking, and candidate generation blocked.
    - ensure the dashboard answers what state an opportunity is in, why, what changed, and what is blocked.
    - keep buy/sell/order language out of the runtime boundary.
  - The Decision (Hardcoded):
    - `docs/architecture/godview_dashboard_wireframe.md` records the dashboard wireframe.
    - `docs/architecture/godview_watchlist_card_spec.md` records the watchlist card fields.
    - `docs/architecture/godview_daily_brief_spec.md` records the daily brief structure.
    - `tests/test_g7_4_dashboard_state_spec.py` validates the spec boundaries.
    - `docs/handover/phase65_g74_dashboard_wireframe_handover.md` is the canonical PM handover.
    - `docs/saw_reports/saw_phase65_g7_4_dashboard_wireframe_20260509.md` records the SAW closeout.
  - Evidence:
    - focused G7.4 tests PASS.
    - scoped compile PASS.
    - closure packet validation PASS.
    - SAW report validation PASS.
    - evidence validation PASS.
  - Contract lock:
    - `PH65_G7_4_PRODUCT_SPEC_ONLY := VALID iff (dashboard_sections_complete = 1) and (watchlist_card_fields_complete = 1) and (daily_brief_spec_complete = 1) and (no_buy_sell_alert_score_rank = 1) and (no_runtime_streamlit = 1) and (no_dashboard_runtime_change = 1) and (candidate_card = 0) and (provider_code = 0) and (live_api_call = 0) and (broker_calls = 0)`.

Phase 65 G8.1 (2026-05-10): Supercycle Discovery Intake (D-378)

  - Decision record:
    - approve G8.1 as discovery-intake-only work.
    - create a small supercycle theme taxonomy.
    - create one static candidate intake queue seeded exactly with `MU`, `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB`.
    - preserve `MU` as the only existing full candidate card.
    - mark `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB` as intake-only.
    - require evidence-needed fields, thesis breakers, provider gaps, and source-lead caveats before any future card work.
    - keep alpha search, ranking, scoring, thesis validation, buying range, backtest, replay, provider ingestion, dashboard runtime, alerts, broker behavior, and recommendations blocked.
  - The Decision (Hardcoded):
    - `opportunity_engine/discovery_intake_schema.py` stores the G8.1 schema constants and validator.
    - `opportunity_engine/discovery_intake.py` loads taxonomy/queue/manifest JSON and validates bundles.
    - `data/discovery/supercycle_discovery_themes_v0.json` stores the approved theme taxonomy.
    - `data/discovery/supercycle_candidate_intake_queue_v0.json` stores the six-name intake queue.
    - `data/discovery/supercycle_candidate_intake_queue_v0.manifest.json` stores the queue manifest and source-policy boundary.
    - `tests/test_g8_1_supercycle_discovery_intake.py` validates the G8.1 invariants.
    - `docs/architecture/g8_1_supercycle_discovery_intake_policy.md` records the intake-only policy.
    - `docs/architecture/supercycle_discovery_theme_taxonomy.md` records the theme contract.
    - `docs/architecture/supercycle_candidate_intake_schema.md` records the queue schema.
    - `docs/handover/phase65_g81_supercycle_discovery_intake_handover.md` is the canonical PM handover.
    - `docs/saw_reports/saw_phase65_g8_1_supercycle_discovery_intake_20260510.md` records the SAW closeout.
  - Evidence:
    - focused G8.1 tests PASS.
    - final validation matrix recorded in the G8.1 SAW report.
  - Contract lock:
    - `PH65_G8_1_INTAKE_ONLY := VALID iff (seed_tickers = [MU,DELL,INTC,AMD,LRCX,ALB]) and (candidate_card_exists = {MU}) and (intake_only = {DELL,INTC,AMD,LRCX,ALB}) and (ticker_required = 1) and (theme_candidates_required = 1) and (evidence_needed_required = 1) and (thesis_breakers_required = 1) and (provider_gaps_required = 1) and (score_fields = 0) and (rank_fields = 0) and (buy_sell_hold_calls = 0) and (validated_status = 0) and (action_state_promotion = 0) and (yfinance_canonical = 0) and (manifest_hash_match = 1) and (alpha_search = 0) and (backtest = 0) and (replay = 0) and (provider_ingestion = 0) and (dashboard_runtime = 0) and (broker_behavior = 0)`.

Phase 65 G8.1A (2026-05-10): Discovery Drift Correction (D-379)

  - Decision record:
    - approve G8.1A as product-governance and schema-only drift correction.
    - mark the current six-name queue as user-seeded, with theme or supply-chain adjacency where applicable.
    - prevent `MU`, `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB` from being described as pure system-scouted output.
    - require `discovery_origin`, `origin_evidence`, `scout_path`, `is_user_seeded`, `is_system_scouted`, `is_validated`, and `is_actionable`.
    - define `LOCAL_FACTOR_SCOUT` for a later G8.1B scout baseline but keep it unused in G8.1A.
    - keep factor scout, alpha search, ranking, scoring, thesis validation, buying range, dashboard runtime, alerts, broker behavior, and recommendations blocked.
  - The Decision (Hardcoded):
    - `opportunity_engine/discovery_intake_schema.py` stores the origin enum and validator rules.
    - `data/discovery/supercycle_candidate_intake_queue_v0.json` stores the relabeled six-name queue.
    - `data/discovery/supercycle_candidate_intake_queue_v0.manifest.json` records the origin policy and refreshed queue hash.
    - `tests/test_g8_1a_discovery_drift_policy.py` validates the G8.1A invariants.
    - `docs/architecture/discovery_drift_policy.md` records the drift correction.
    - `docs/architecture/discovery_origin_taxonomy.md` records the origin taxonomy.
    - `docs/architecture/supercycle_scout_protocol.md` records the G8.1A scout boundary and G8.1B preview.
    - `docs/architecture/discovery_intake_vs_candidate_card.md` records the object boundary.
    - `docs/handover/phase65_g81a_discovery_drift_handover.md` is the canonical PM handover.
    - `docs/saw_reports/saw_phase65_g8_1a_discovery_drift_20260510.md` records the SAW closeout.
  - Evidence:
    - focused G8.1/G8.1A tests PASS.
    - scoped compile PASS.
  - Contract lock:
    - `PH65_G8_1A_DISCOVERY_DRIFT := VALID iff (origin_required = 1) and (origin_evidence_required = 1) and (scout_path_required = 1) and (seed_tickers = [MU,DELL,INTC,AMD,LRCX,ALB]) and (MU_origin = USER_SEEDED) and (DELL_INTC_AMD_ALB_origin = USER_SEEDED+THEME_ADJACENT) and (LRCX_origin = USER_SEEDED+SUPPLY_CHAIN_ADJACENT) and (system_scouted_current_six = 0) and (validated_current_six = 0) and (actionable_current_six = 0) and (local_factor_scout_used = 0) and (rank = 0) and (score = 0) and (buy_sell_hold = 0)`.

Phase 65 DASH-0 (2026-05-10): GodView Dashboard IA Redesign Plan (D-380)

  - Decision record:
    - approve DASH-0 as planning-only dashboard information architecture.
    - approve target page map: Command Center, Opportunities, Thesis Card, Market Behavior, Entry & Hold Discipline, Portfolio & Allocation, Research Lab, Settings & Ops.
    - plan future Streamlit page registry/sidebar shell using `st.Page` and `st.navigation` after DASH-1 approval.
    - move Data Health and Drift Monitor to future Settings & Ops.
    - move Backtest Lab, Modular Strategies, Daily Scan, and experiments to future Research Lab.
    - move Portfolio Builder and Shadow Portfolio to future Portfolio & Allocation.
    - record future optimizer UX task to align `Max weight` and `Max sector weight` in one Risk limits group.
    - keep runtime dashboard code, Streamlit navigation shell, providers, factor scout, discovery intake output, candidate cards, backtests, alerts, broker behavior, rankings, and scores blocked.
  - The Decision (Hardcoded):
    - `docs/architecture/dashboard_information_architecture.md` records the approved page map.
    - `docs/architecture/dashboard_page_registry_plan.md` records the future registry/sidebar plan.
    - `docs/architecture/dashboard_redesign_migration_plan.md` records the legacy-to-new mapping.
    - `docs/architecture/dashboard_ops_relocation_policy.md` records Data Health / Drift Monitor relocation.
    - `docs/handover/dashboard_ia_handover_20260510.md` is the canonical PM handover.
    - `docs/saw_reports/saw_dashboard_ia_redesign_plan_20260510.md` records the SAW closeout.
  - Evidence:
    - official Streamlit docs confirm `st.Page` / `st.navigation` are the flexible multipage mechanism and the entrypoint acts as router/frame.
    - context validation PASS.
  - Contract lock:
    - `PH65_DASH_0_IA_SPEC_ONLY := VALID iff (page_map = [Command Center,Opportunities,Thesis Card,Market Behavior,Entry & Hold Discipline,Portfolio & Allocation,Research Lab,Settings & Ops]) and (legacy_movement_mapped = 1) and (ops_relocation_policy = 1) and (streamlit_registry_basis = 1) and (dashboard_py_touched = 0) and (views_touched = 0) and (optimizer_view_touched = 0) and (factor_scout_touched = 0) and (discovery_intake_output_touched = 0) and (candidate_cards_touched = 0) and (provider_code = 0) and (backtest_code = 0) and (alerts = 0) and (broker_calls = 0)`.

Phase 65 G8 (2026-05-10): One Supercycle Gem Candidate Card (D-377)

  - Decision record:
    - approve G8 as candidate-card-only work for one human-nominated ticker.
    - use `MU` as the default ticker.
    - create a structured research object with source-quality labels, evidence-present/missing lists, thesis breakers, data dependencies, state mapping, provider-gap labels, and forbidden outputs.
    - keep alpha search, candidate screening, ranking, scoring, upside calculation, buy range, backtest, replay, provider ingestion, dashboard runtime, buy/sell alerts, and broker calls blocked.
    - require initial state to be only `THESIS_CANDIDATE` or `EVIDENCE_BUILDING`.
    - require `BUYING_RANGE`, `ADD_ON_SETUP`, `LET_WINNER_RUN`, and `TRIM_OPTIONAL` to remain forbidden for G8.
  - The Decision (Hardcoded):
    - `opportunity_engine/candidate_card_schema.py` stores the G8 schema constants and validator.
    - `opportunity_engine/candidate_card.py` loads card/manifest JSON and validates card bundles.
    - `data/candidate_cards/MU_supercycle_candidate_card_v0.json` stores the one MU card.
    - `data/candidate_cards/MU_supercycle_candidate_card_v0.manifest.json` stores the card manifest and source-policy boundary.
    - `tests/test_g8_supercycle_candidate_card.py` validates the G8 invariants.
    - `docs/architecture/g8_supercycle_candidate_card_policy.md` records the candidate-card-only policy.
    - `docs/architecture/supercycle_candidate_card_schema.md` records the schema contract.
    - `docs/handover/phase65_g8_supercycle_candidate_card_handover.md` is the canonical PM handover.
    - `docs/saw_reports/saw_phase65_g8_supercycle_candidate_card_20260510.md` records the SAW closeout.
  - Evidence:
    - focused G8 tests PASS.
    - G7.2/G7.3/G7.4 regression tests PASS.
    - full validation matrix recorded in the G8 SAW report.
  - Contract lock:
    - `PH65_G8_CANDIDATE_CARD_ONLY := VALID iff (one_card = MU) and (candidate_status = candidate_card_only) and (ticker_required = 1) and (theme_required = 1) and (manifest_required = 1) and (source_quality_summary_required = 1) and (initial_state in {THESIS_CANDIDATE,EVIDENCE_BUILDING}) and (action_states_absent = 1) and (score_rank_signal_alert_broker_fields_absent = 1) and (yfinance_canonical = 0) and (estimated_as_observed = 0) and (options_iv_gamma_whales_provider_gap = 1) and (alpha_search = 0) and (screening = 0) and (ranking = 0) and (backtest = 0) and (replay = 0) and (provider_ingestion = 0) and (dashboard_runtime = 0) and (broker_calls = 0)`.
Phase 65 G7.2 (2026-05-10): Unified Opportunity State Machine (D-374)

  - Decision record:
    - approve G7.2 as definition-only Unified Opportunity State Machine work.
    - define finite opportunity states, reason codes, transition evidence schemas, forbidden jumps, and validator tests.
    - keep all score, rank, alert, broker, provider, ingestion, search, backtest, replay, proxy, and dashboard-runtime behavior blocked.
    - require `THESIS_BROKEN` to override bullish market behavior.
    - block direct `THESIS_CANDIDATE -> BUYING_RANGE` jumps.
    - require `LEFT_SIDE_RISK` to pass through `ACCUMULATION_WATCH` or `CONFIRMATION_WATCH` before `BUYING_RANGE`.
    - block estimated-only evidence from creating `BUYING_RANGE`.
    - block inferred-only evidence from creating `LET_WINNER_RUN`.
  - The Decision (Hardcoded):
    - `docs/architecture/unified_opportunity_state_machine.md` records the state-machine definition.
    - `docs/architecture/opportunity_state_transition_policy.md` records the transition policy.
    - `docs/architecture/opportunity_state_forbidden_jumps.md` records the hard forbidden-jump register.
    - `opportunity_engine/states.py` stores the finite state and reason-code enums.
    - `opportunity_engine/schemas.py` stores the transition evidence schemas.
    - `opportunity_engine/transitions.py` stores the transition validator.
    - `tests/test_g7_2_opportunity_state_machine.py` validates the state-machine invariants.
    - `docs/handover/phase65_g72_state_machine_handover.md` is the canonical PM handover.
    - `docs/saw_reports/saw_phase65_g7_2_state_machine_20260509.md` records the SAW closeout.
  - Evidence:
    - focused G7.2 tests PASS.
    - scoped compile PASS.
    - closure packet validation PASS.
    - SAW report validation PASS.
    - evidence validation PASS.
  - Contract lock:
    - `PH65_G7_2_STATE_DEFINITION_ONLY := VALID iff (state_enum_complete = 1) and (reason_codes_present = 1) and (source_classes_present = 1) and (forbidden_jump_not_requested = 1) and (thesis_broken_override_applied = 1) and (estimated_only_buying_range = 0) and (inferred_only_let_winner_run = 0) and (score_rank_alert_broker_fields_absent = 1) and (candidate_generation = 0) and (search = 0) and (backtest = 0) and (replay = 0) and (proxy_run = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.

Phase 65 G7.3 (2026-05-10): Signal-to-State Source Eligibility Map (D-375)

  - Decision record:
    - approve G7.3 as policy-only Signal-to-State Source Eligibility Map work.
    - map every GodView signal family to source class, observed/estimated/inferred label, allowed state influence, forbidden state influence, freshness requirement, and confidence label.
    - keep provider classes, live API calls, source registry implementation, scoring, ranking, alerts, broker, and dashboard runtime behavior blocked.
    - preserve SEC/FINRA/CFTC/FRED/Ken French fixture pillars as context/reason-code sources only.
    - keep Tier 2/yfinance from moving any state toward `BUYING_RANGE` or `LET_WINNER_RUN`.
    - keep options/IV/gamma/whales as provider-gap signals.
  - The Decision (Hardcoded):
    - `docs/architecture/godview_signal_to_state_map.md` records the full source-to-state map.
    - `docs/architecture/godview_source_eligibility_policy.md` records source-class eligibility.
    - `docs/architecture/godview_signal_confidence_policy.md` records confidence labels and freshness degradation.
    - `opportunity_engine/source_classes.py` stores source class, signal family, and confidence enums.
    - `opportunity_engine/signal_policy.py` stores the signal-family policy map.
    - `tests/test_g7_3_signal_to_state_source_map.py` validates the policy boundaries.
    - `docs/handover/phase65_g73_signal_to_state_handover.md` is the canonical PM handover.
    - `docs/saw_reports/saw_phase65_g7_3_signal_to_state_map_20260509.md` records the SAW closeout.
  - Evidence:
    - focused G7.3 tests PASS.
    - scoped compile PASS.
    - closure packet validation PASS.
    - SAW report validation PASS.
    - evidence validation PASS.
  - Contract lock:
    - `PH65_G7_3_POLICY_ONLY := VALID iff (source_class_enum_complete = 1) and (signal_family_map_complete = 1) and (public_fixtures_context_only = 1) and (estimated_only_buying_range = 0) and (tier2_yfinance_action_state = 0) and (provider_gap_signals = 1) and (short_interest_context_only = 1) and (cftc_broad_regime_only = 1) and (fred_ken_french_context_only = 1) and (provider_code = 0) and (live_api_call = 0) and (source_registry = 0) and (alerts = 0) and (broker_calls = 0) and (dashboard_runtime_change = 0)`.

Phase 65 G7.4 (2026-05-10): Dashboard Wireframe / Product-State Spec (D-376)

  - Decision record:
    - approve G7.4 as product-spec-only dashboard wireframe work.
    - define state-first dashboard sections, watchlist card fields, and daily brief structure.
    - keep dashboard runtime code, Streamlit edits, candidate cards, alerts, provider calls, broker calls, score, ranking, and candidate generation blocked.
    - ensure the dashboard answers what state an opportunity is in, why, what changed, and what is blocked.
    - keep buy/sell/order language out of the runtime boundary.
  - The Decision (Hardcoded):
    - `docs/architecture/godview_dashboard_wireframe.md` records the dashboard wireframe.
    - `docs/architecture/godview_watchlist_card_spec.md` records the watchlist card fields.
    - `docs/architecture/godview_daily_brief_spec.md` records the daily brief structure.
    - `tests/test_g7_4_dashboard_state_spec.py` validates the spec boundaries.
    - `docs/handover/phase65_g74_dashboard_wireframe_handover.md` is the canonical PM handover.
    - `docs/saw_reports/saw_phase65_g7_4_dashboard_wireframe_20260509.md` records the SAW closeout.
  - Evidence:
    - focused G7.4 tests PASS.
    - scoped compile PASS.
    - closure packet validation PASS.
    - SAW report validation PASS.
    - evidence validation PASS.
  - Contract lock:
    - `PH65_G7_4_PRODUCT_SPEC_ONLY := VALID iff (dashboard_sections_complete = 1) and (watchlist_card_fields_complete = 1) and (daily_brief_spec_complete = 1) and (no_buy_sell_alert_score_rank = 1) and (no_runtime_streamlit = 1) and (no_dashboard_runtime_change = 1) and (candidate_card = 0) and (provider_code = 0) and (live_api_call = 0) and (broker_calls = 0)`.
Phase 65 G8.1B (2026-05-10): Pipeline-First Discovery Scout Baseline (D-381)

  - Decision record:
    - approve G8.1B as backend/governance-only work.
    - wrap the existing local Phase 34 factor artifact as `LOCAL_FACTOR_SCOUT`.
    - name the wrapper `4-Factor Equal-Weight Scout Baseline`.
    - use `scout_model_id = LOCAL_FACTOR_EQUAL_WEIGHT_V0`.
    - emit exactly one tiny intake-only scout output item.
    - keep rank, score display, recommendation language, validation claims, candidate-card creation, dashboard runtime behavior, provider calls, alerts, and broker behavior blocked.
  - The Decision (Hardcoded):
    - `opportunity_engine/factor_scout_schema.py` stores the G8.1B schema constants and validator.
    - `opportunity_engine/factor_scout.py` loads/validates scout artifacts and reads local source metadata deterministically.
    - `data/discovery/local_factor_scout_baseline_v0.json` stores the governed baseline metadata.
    - `data/discovery/local_factor_scout_baseline_v0.manifest.json` stores the baseline manifest and source-policy boundary.
    - `data/discovery/local_factor_scout_output_tiny_v0.json` stores one `LOCAL_FACTOR_SCOUT` intake-only item.
    - `data/discovery/local_factor_scout_output_tiny_v0.manifest.json` stores the output manifest.
    - `tests/test_g8_1b_pipeline_first_discovery_scout.py` validates G8.1B invariants.
    - `docs/architecture/pipeline_first_discovery_scout_policy.md`, `docs/architecture/local_factor_scout_baseline_policy.md`, and `docs/architecture/factor_scout_output_contract.md` record the policy and output contracts.
    - `docs/handover/phase65_g81b_pipeline_first_scout_handover.md` is the canonical PM handover.
    - `docs/saw_reports/saw_phase65_g8_1b_pipeline_first_scout_20260510.md` records the SAW closeout.
  - Evidence:
    - focused G8.1B tests PASS.
    - source artifact metadata reconciles to 2555730 rows, 2000-01-03 to 2026-02-13, and 389 permnos.
    - deterministic fixture selection returns `MSFT` by latest-date/local-metadata/ascending-permno rule, not by factor ordering.
  - Contract lock:
    - `PH65_G8_1B_SCOUT_BASELINE_ONLY := VALID iff (model_id = LOCAL_FACTOR_EQUAL_WEIGHT_V0) and (model_name = 4-Factor Equal-Weight Scout Baseline) and (source_artifact = data/processed/phase34_factor_scores.parquet) and (factor_names = [momentum_normalized,quality_normalized,volatility_normalized,illiquidity_normalized]) and (sum(factor_weights) = 1.0) and (output_items = 1) and (discovery_origin = LOCAL_FACTOR_SCOUT) and (status = intake_only) and (system_scouted = 1) and (validated = 0) and (actionable = 0) and (score_display = 0) and (rank = 0) and (buy_sell_signal = 0) and (candidate_card = 0) and (dashboard_runtime = 0) and (provider_call = 0)`.

Phase 65 DASH-1 (2026-05-10): Page Registry Shell (D-382)

  - Decision record:
    - approve DASH-1 as runtime shell-only work.
    - replace the old flat-tab mental model with a Streamlit page registry/sidebar shell.
    - keep legacy page behavior while relocating old pages behind approved IA buckets.
    - keep new GodView pages placeholder/status-only until a later approved phase.
    - keep all new data, metrics, product claims, provider calls, alerts, broker behavior, factor-scout integration, candidate generation, ranking, scoring, and buy/sell/hold output blocked.
  - The Decision (Hardcoded):
    - `dashboard.py` owns the shared Streamlit entrypoint/frame and calls `page.run()`.
    - `views/page_registry.py` owns approved page titles, page groups, and legacy movement map.
    - `tests/test_dash_1_page_registry_shell.py` validates the approved page map, legacy relocation, absence of `st.tabs`, and forbidden-scope boundaries.
    - `docs/handover/dash_1_page_registry_shell_handover_20260510.md` is the canonical PM handover.
    - `docs/saw_reports/saw_dash_1_page_registry_shell_20260510.md` records the SAW closeout.
  - Parallel lane:
    - `docs/saw_reports/saw_phase65_g8_1b_r_reviewer_rerun_20260510.md` closes G8.1B-R reviewer evidence with PASS and no dashboard edits.
  - Contract lock:
    - `PH65_DASH_1_RUNTIME_SHELL_ONLY := VALID iff (approved_page_order = 1) and (st_page_registry = 1) and (selected_page_run = 1) and (legacy_relocation = 1) and (old_flat_tabs = 0) and (new_metrics = 0) and (new_data = 0) and (ranking = 0) and (scoring = 0) and (alerts = 0) and (broker_calls = 0) and (provider_ingestion = 0) and (factor_scout_integration = 0)`.

Phase 65 G8.2 (2026-05-10): System-Scouted Candidate Card (D-383)

  - Decision record:
    - approve G8.2 as Data + Docs/Ops candidate-card-only work.
    - convert exactly one governed `LOCAL_FACTOR_SCOUT` output item into a structured research object.
    - use `MSFT` only because it is the sole G8.1B `LOCAL_FACTOR_SCOUT` output.
    - require `candidate_status = candidate_card_only`, `discovery_origin = LOCAL_FACTOR_SCOUT`, `scout_model_id = LOCAL_FACTOR_EQUAL_WEIGHT_V0`, `source_intake_item_id`, `source_intake_manifest_uri`, and `candidate_card_manifest_uri`.
    - keep DELL/AMD/LRCX/ALB cards, new scout outputs, factor-score display, rank, score, thesis validation, actionability, buy/sell/hold, buying range, alert, broker behavior, provider ingestion, and dashboard runtime merge blocked.
    - treat official/public evidence pointers as research orientation only, not thesis validation.
  - The Decision (Hardcoded):
    - `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json` stores the MSFT system-scouted candidate card.
    - `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json` stores the card manifest, provenance, source policy, and hash.
    - `opportunity_engine/candidate_card_schema.py` rejects factor-score leakage and validates optional governance flags when present.
    - `tests/test_g8_2_system_scouted_candidate_card.py` validates G8.2 invariants.
    - `docs/architecture/g8_2_system_scouted_candidate_card_policy.md` records the policy and dashboard boundary.
    - `docs/handover/phase65_g82_system_scouted_candidate_card_handover.md` is the canonical PM handover.
    - `docs/saw_reports/saw_phase65_g8_2_system_scouted_candidate_card_20260510.md` records the SAW closeout.
  - Evidence:
    - focused G8.2 tests PASS.
    - G8/G8.1B/G8.2 regression PASS.
    - context-builder tests PASS.
    - scoped compile PASS.
    - context rebuild and closure validators PASS after SAW publication.
  - Dashboard boundary:
    - The dashboard can already show `MSFT` through legacy runtime ticker-list logic.
    - That runtime row is not the G8.2 candidate card and must not be interpreted as card-reader integration.
  - Contract lock:
    - `PH65_G8_2_ONE_CARD_ONLY := VALID iff (source_scout_output = data/discovery/local_factor_scout_output_tiny_v0.json) and (source_scout_tickers = [MSFT]) and (candidate_card_ticker = MSFT) and (candidate_status = candidate_card_only) and (discovery_origin = LOCAL_FACTOR_SCOUT) and (scout_model_id = LOCAL_FACTOR_EQUAL_WEIGHT_V0) and (source_intake_manifest_uri_present = 1) and (candidate_manifest_uri_present = 1) and (candidate_cards = [MU,MSFT]) and (new_scout_output = 0) and (user_seeded_cards_created = 0) and (factor_score = 0) and (rank = 0) and (score = 0) and (validated = 0) and (actionable = 0) and (buy_sell_hold = 0) and (buying_range = 0) and (alert = 0) and (broker_call = 0) and (provider_ingestion = 0) and (dashboard_runtime_merge = 0)`.

Phase 65 DASH-2 (2026-05-10): Portfolio Allocation Runtime Slice

  - Decision record:
    - keep Portfolio Optimizer visible at the top of `Portfolio & Allocation`.
    - remove the optimizer expander/toggle introduced in the first DASH-2 pass.
    - render YTD Performance below the optimizer, comparing optimized portfolio return against SPY and QQQ.
    - refresh selected stock and benchmark prices with an in-memory yfinance adjusted-close overlay for display freshness only.
    - keep broker behavior, alerts, candidate ranking/scoring, factor-scout integration, provider ingestion, and canonical evidence changes blocked.
  - The Decision (Hardcoded):
    - `views/optimizer_view.py` refreshes selected optimizer price series and stores current optimizer weights in `st.session_state["optimizer_weights"]`.
    - `dashboard.py` calculates weighted YTD portfolio return from current optimizer weights and displays SPY/QQQ YTD metrics below the optimizer.
    - `tests/test_dash_2_portfolio_ytd.py` validates ordering, return-weight plumbing, freshness helpers, and no forbidden runtime scope.
  - Evidence:
    - focused DASH-2 tests PASS.
    - DASH-1 navigation regression PASS.
    - scoped compile PASS.
    - Browser check shows `Portfolio Optimizer` before `YTD Performance`, SPY/QQQ metrics present, and freshness through 2026-05-08.
  - Contract lock:
    - `PH65_DASH_2_PORTFOLIO_RUNTIME_SLICE := VALID iff (optimizer_top_level = 1) and (optimizer_expander = 0) and (ytd_below_optimizer = 1) and (portfolio_return = weighted_optimizer_return) and (benchmarks = [SPY,QQQ]) and (fresh_price_overlay = in_memory_display_only) and (provider_ingestion = 0) and (broker_call = 0) and (alert = 0) and (candidate_rank_score = 0)`.

Phase 65 Portfolio Universe Construction Fix (2026-05-10)

  - Decision record:
    - approve P0-P3 mechanical correction only: explicit optimizer universe builder, default exclusion of `EXIT`/`KILL`/`AVOID`/`IGNORE`, ticker/price readiness reporting, and max-weight feasibility diagnostics.
    - approve lightweight P4-P6 support: rename misleading Sharpe labels, add regression tests, and document the portfolio construction contract.
    - hold Black-Litterman, MU 20% policy, conviction mode, WATCH investability policy, manual override, thesis-anchor sizing, scanner rewrites, and new portfolio objectives.
  - The Decision (Hardcoded):
    - `strategies/portfolio_universe.py` owns scanner-row eligibility classification, ticker-map readiness, local price-history readiness, and max-weight feasibility diagnostics.
    - `dashboard.py` calls `build_optimizer_universe(...)` and passes `universe.included_permnos` plus `universe_audit` to the optimizer view instead of slicing `df_scan["Ticker"]`.
    - `views/optimizer_view.py` renders the universe audit, uses only audited candidate assets when provided, explains allocation constraints, and labels the max-Sharpe path as thesis-neutral.
    - `docs/architecture/portfolio_construction_contract.md` records the scanner/display/allocation boundary and explicitly blocks conviction work.
  - Evidence:
    - focused portfolio universe and DASH-2 tests PASS.
    - scoped compile PASS for `strategies/portfolio_universe.py`, `views/optimizer_view.py`, and `dashboard.py`.
    - current cached scan audits to zero eligible assets under the conservative policy because current rows are EXIT/KILL/IGNORE/WATCH or local price-history failures.
    - browser smoke at `http://127.0.0.1:8503/portfolio-and-allocation` shows Portfolio Optimizer, Universe Audit, fail-closed no-eligible message, and YTD Performance.
  - Contract lock:
    - `PORTFOLIO_UNIVERSE_CONSTRUCTION_FIX := VALID iff (explicit_universe_builder = 1) and (display_sort_slice = 0) and (exit_kill_avoid_ignore_default_excluded = 1) and (watch_research_only_default = 1) and (ticker_map_readiness_reported = 1) and (price_history_readiness_reported = 1) and (max_weight_feasibility_diagnostic = 1) and (auto_best_sharpe_label = 0) and (mu_hard_floor = 0) and (conviction_mode = 0) and (black_litterman_runtime = 0) and (manual_override = 0)`.

Phase 65 Portfolio Universe Optimizer-Core Quarantine (2026-05-10)

  - Decision record:
    - reject accepting the dirty `strategies/optimizer.py` lower-bound/SLSQP diff into the Portfolio Universe Construction Fix closure.
    - preserve the optimizer-core diff as a quarantine patch, revert `strategies/optimizer.py` to baseline, and close the universe-construction fix only after focused validation passes.
    - open optimizer lower-bound/SLSQP behavior as a separate policy/audit round before any acceptance, revision, or rejection of optimizer-core math changes.
  - The Decision (Hardcoded):
    - `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch` stores the quarantined dirty diff.
    - `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_note_20260510.md` records that the diff is out of scope for universe construction.
    - `docs/saw_reports/saw_portfolio_universe_construction_fix_20260510.md` closes `PORTFOLIO_UNIVERSE_CONSTRUCTION_FIX_20260510` as PASS after quarantine.
  - Evidence:
    - `git diff -- strategies/optimizer.py` is empty.
    - focused portfolio universe/DASH tests PASS.
    - full pytest PASS after context/provenance hygiene and yfinance allowlist repair.
    - scoped compile PASS.
    - context validation PASS.
    - browser smoke PASS at `/portfolio-and-allocation`.
  - Contract lock:
    - `PORTFOLIO_UNIVERSE_QUARANTINE_CLOSE := VALID iff (optimizer_diff_saved = 1) and (strategies_optimizer_diff = 0) and (focused_tests_pass = 1) and (scoped_compile_pass = 1) and (context_validate_pass = 1) and (browser_smoke_pass = 1) and (optimizer_core_lower_bounds_accepted = 0)`.

Phase 65 Optimizer Core Policy Audit (2026-05-10)

  - Decision record:
    - open `OPTIMIZER_CORE_POLICY_AUDIT` as docs/tests-first work only.
    - reject the quarantined lower-bound/SLSQP diff as-is.
    - hold implementation until a future round explicitly approves optimizer-core policy changes and replaces audit xfails with passing implementation tests.
  - The Decision (Hardcoded):
    - `docs/architecture/optimizer_core_policy_audit.md` records audit questions, answer set, source rationale, and reject-as-is disposition.
    - `docs/architecture/optimizer_constraints_policy.md` records current and future feasibility formulas.
    - `docs/architecture/optimizer_lower_bound_slsqp_policy.md` records lower-bound/SLSQP policy and active-bound reporting requirements.
    - `tests/test_optimizer_core_policy.py` locks non-approval and records strict xfail debt for infeasibility/fallback/active-bound behavior.
    - `docs/saw_reports/saw_optimizer_core_policy_audit_20260510.md` records the independent implementer/reviewer SAW closeout.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q` PASS with expected strict xfails.
    - `git diff -- strategies/optimizer.py` remains empty.
  - Contract lock:
    - `OPTIMIZER_CORE_POLICY_AUDIT := VALID iff (policy_docs_present = 1) and (policy_tests_present = 1) and (strategies_optimizer_diff = 0) and (lower_bound_slsqp_diff_accepted = 0) and (mu_conviction = 0) and (watch_investability = 0) and (black_litterman = 0) and (universe_eligibility_change = 0)`.

Phase 65 Dashboard Scanner Testability Hardening (2026-05-11)

  - Decision record:
    - approve `DASHBOARD_SCANNER_TESTABILITY_HARDENING` as behavior-preserving scanner extraction and coverage work.
    - move deterministic dashboard scanner formulas out of inline `dashboard.py` closures into `strategies/scanner.py`.
    - keep dashboard-owned provider calls, Streamlit cache boundaries, and payload persistence in `dashboard.py`.
    - add focused boundary-value tests for macro scoring, breadth status, price technicals, cluster classification, entry price, tactics, proxy signal, rating, leverage, and full scan-frame enrichment.
    - add small direct tests for `InvestorCockpitStrategy`, `AdaptiveTrendStrategy`, `ProductionConfig`, and `core.etl`.
  - The Decision (Hardcoded):
    - `strategies/scanner.py` owns pure scanner math and dataframe enrichment.
    - `dashboard.py` still owns yfinance calls through `fetch_macro_score`, `get_breadth_status`, and `get_prices_and_technicals`, then delegates deterministic enrichment to `enrich_scan_frame(...)`.
    - `tests/test_scanner.py` is the scanner formula guardrail; `tests/test_process_utils.py` remains the process-liveness guardrail.
    - no scanner semantics, provider authority, candidate-card state, ranking/scoring policy, alert, broker behavior, or dashboard redesign is approved by this round.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests\test_scanner.py tests\test_strategy.py tests\test_phase15_integration.py tests\test_adaptive_trend.py tests\test_production_config.py tests\test_core_etl.py tests\test_process_utils.py -q` PASS, 46 passed.
    - `.venv\Scripts\python -m py_compile strategies\scanner.py dashboard.py tests\test_scanner.py tests\test_strategy.py tests\test_adaptive_trend.py tests\test_production_config.py tests\test_core_etl.py tests\conftest.py` PASS.
    - `.venv\Scripts\python -m pytest -q` PASS.
    - `tests/pytest_out.txt` refreshed with the current full-suite PASS summary.
  - Contract lock:
    - `DASHBOARD_SCANNER_TESTABILITY_HARDENING := VALID iff (scanner_math_owner = strategies/scanner.py) and (dashboard_provider_boundary_preserved = 1) and (scanner_boundary_tests = 1) and (process_guardrail_still_passing = 1) and (provider_ingestion = 0) and (canonical_market_data_write = 0) and (ranking_policy_change = 0) and (alert_or_broker = 0)`.

Phase 65 Optimizer Core Structured Diagnostics (2026-05-11)

  - Decision record:
    - approve `OPTIMIZER_CORE_STRUCTURED_DIAGNOSTICS_IMPLEMENTATION` as diagnostics-only optimizer-core work.
    - implement explicit pre-solver feasibility checks, equal-weight boundary warnings, SLSQP status reporting, post-solver active-bound diagnostics, full-investment residual diagnostics, and UI-safe explanation rows.
    - keep the quarantined lower-bound/SLSQP diff rejected as-is; this round does not approve lower-bound allocation policy.
    - keep MU conviction policy, WATCH investability expansion, Black-Litterman, simple tilt / conviction optimizer, new objectives, scanner rules, manual overrides, provider ingestion, alerts, broker behavior, and replay behavior blocked.
  - The Decision (Hardcoded):
    - `strategies/optimizer_diagnostics.py` owns structured diagnostic objects and formulas.
    - `strategies/optimizer.py` exposes diagnostic-returning optimizer methods while preserving legacy weight-returning methods.
    - `views/optimizer_view.py` renders optimization status, feasibility status, active constraints, max-cap assets, lower-bound assets, equal-weight-forced status, solver status, residuals, and fallback labeling.
    - `tests/test_optimizer_core_policy.py` converts prior strict xfail audit debt into passing diagnostics tests.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q` PASS.
    - scoped compile PASS for `strategies/optimizer.py`, `strategies/optimizer_diagnostics.py`, `views/optimizer_view.py`, and `dashboard.py`.
  - Contract lock:
    - `OPTIMIZER_CORE_STRUCTURED_DIAGNOSTICS := VALID iff (diagnostics_module = 1) and (pre_solver_feasibility = 1) and (slsqp_status_report = 1) and (active_bound_report = 1) and (constraint_residual_report = 1) and (fallback_labeled = 1) and (silent_fallback = 0) and (mu_conviction = 0) and (watch_investability = 0) and (black_litterman = 0) and (new_objective = 0) and (scanner_rule_change = 0)`.

Phase 65 Portfolio Data Boundary Refactor (2026-05-11)

  - Decision record:
    - approve `1A/2A/3A` architecture cleanup for `/portfolio-and-allocation`.
    - move selected-stock live display overlay fetching, close extraction, local TRI scaling, and stitching out of `views/optimizer_view.py`.
    - move `data/backtest_results.json` strategy-metrics parsing out of `views/optimizer_view.py`.
    - keep the DASH-2 display freshness behavior and optimizer diagnostics unchanged.
  - The Decision (Hardcoded):
    - `core/data_orchestrator.py` owns `download_recent_close_prices`, `scale_live_overlay_to_local`, `refresh_selected_prices_with_live_overlay`, and `load_strategy_metrics_from_results`.
    - `views/optimizer_view.py` imports these helpers and does not import yfinance or parse `data/backtest_results.json` directly.
    - `data/providers/legacy_allowlist.py` no longer needs `views/optimizer_view.py` because direct yfinance usage is removed from the view.
    - `tests/test_data_orchestrator_portfolio_runtime.py` locks overlay scaling/stitching, duplicate-date anchor handling, partial-live cell preservation, stale-while-revalidate behavior, scheduler submit fail-soft behavior, future-mtime cache invalidation, and metrics parsing behavior.
  - Evidence:
    - `.venv\Scripts\python -m py_compile core\data_orchestrator.py views\optimizer_view.py data\providers\legacy_allowlist.py tests\test_dash_2_portfolio_ytd.py tests\test_dashboard_sprint_a.py tests\test_data_orchestrator_portfolio_runtime.py` PASS.
    - `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py -q` PASS, 8 passed.
    - `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dashboard_sprint_a.py tests\test_dash_2_portfolio_ytd.py tests\test_provider_ports.py tests\test_portfolio_universe.py -q` PASS, 47 passed.
    - `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q` PASS, 17 passed.
    - `.venv\Scripts\python -m pytest -q` PASS.
    - runtime smoke `http://localhost:8505/portfolio-and-allocation` PASS, HTTP 200.
  - Contract lock:
    - `PORTFOLIO_DATA_BOUNDARY_REFACTOR := VALID iff (view_yfinance_import = 0) and (view_backtest_json_parse = 0) and (overlay_fetch_owner = core_data_orchestrator) and (overlay_scale_stitch_owner = core_data_orchestrator) and (partial_live_overlay_preserves_local_cells = 1) and (duplicate_anchor_dates_deduped_before_scaling = 1) and (stale_overlay_cache_is_display_only = 1) and (scheduler_submit_failure_fails_soft = 1) and (strategy_metrics_owner = core_data_orchestrator) and (provider_ingestion = 0) and (canonical_write = 0) and (optimizer_objective_change = 0)`.

Phase 65 Portfolio Optimizer View Test and Performance Hardening (2026-05-11)

  - Decision record:
    - implement the approved tests/performance options for `/portfolio-and-allocation`.
    - add dedicated Streamlit `AppTest` coverage for the optimizer view render path, mean-variance dropdown, and sector-cap controls.
    - add a UI-to-solver handoff test that pipes synthetic max-weight and risk-free-rate controls into the real SLSQP optimizer.
    - cache recent display close overlays through non-canonical Parquet files and schedule background refresh on cold/stale cache misses.
    - cache optimizer runs by selected price frame and user parameters.
  - The Decision (Hardcoded):
    - `tests/test_optimizer_view.py` owns Streamlit view integration coverage and display-cache behavior tests.
    - `tests/test_optimizer_core_policy.py` owns UI-derived bounds through real optimizer coverage.
    - `core/data_orchestrator.py` owns display-only Parquet overlay cache, background refresh scheduling, atomic cache writes, and copy-safe scale cache.
    - `views/optimizer_view.py` uses `_run_optimizer_cached(...)` for equivalent rerenders and keeps sector caps post-solver.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_optimizer_core_policy.py tests\test_dash_2_portfolio_ytd.py -q` PASS, 39 passed.
  - Contract lock:
    - `PORTFOLIO_OPTIMIZER_VIEW_PERF_HARDENING := VALID iff (streamlit_view_test = 1) and (ui_solver_bounds_test = 1) and (overlay_parquet_cache = display_only) and (cache_write_atomic = 1) and (cold_cache_nonblocking = 1) and (optimizer_run_cache = 1) and (sector_cap_post_solver = 1) and (provider_ingestion = 0) and (canonical_write = 0) and (new_optimizer_objective = 0) and (mu_conviction = 0) and (watch_investability = 0)`.

Phase 65 Dashboard Architecture Safety Slice (2026-05-11)

  - Decision record:
    - approve the Architecture Section 1 recommended fixes for process liveness safety and local dashboard duplication cleanup.
    - centralize PID liveness probing in `utils/process.py` and route dashboard, updater, release-controller, parameter-sweep, and phase16 optimizer lock callers through the shared helper.
    - keep compatibility wrappers (`_pid_is_running`, `_pid_is_alive`, `_is_pid_alive`) so existing tests and monkeypatch seams stay stable.
    - collapse duplicated dashboard strategy-matrix initialization behind `_build_strategy_matrix(...)` and `_ensure_modular_strategy_state(...)`.
    - delegate `dashboard.py::_clean_portfolio_price_frame(...)` to `core.data_orchestrator.clean_price_frame(...)`.
  - The Decision (Hardcoded):
    - `utils/process.py::pid_is_running` owns the Windows-safe process probe and is the only allowed place for a process-liveness `os.kill(pid, 0)` style fallback.
    - dashboard backtest PID status no longer calls `os.kill(pid, 0)` directly.
    - strategy-matrix status semantics remain unchanged: `Running...`, `Done`, `Next`, `Pending`, and `Insufficient`.
    - dashboard portfolio YTD cleanup now inherits canonical duplicate-date handling from `core.data_orchestrator.clean_price_frame`.
  - Evidence:
    - `.venv\Scripts\python -m py_compile utils\process.py dashboard.py data\updater.py scripts\parameter_sweep.py scripts\release_controller.py backtests\optimize_phase16_parameters.py tests\test_process_utils.py` PASS.
    - `.venv\Scripts\python -m pytest tests\test_process_utils.py tests\test_parameter_sweep.py tests\test_updater_parallel.py tests\test_release_controller.py tests\test_optimize_phase16_parameters.py tests\test_dash_1_page_registry_shell.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py -q` PASS, 102 passed.
    - `rg -n "os\.kill\(pid,\s*0\)|os\.kill\(int\(pid\),\s*0\)" -g "*.py"` finds no unsafe runtime caller outside the shared utility comment.
    - `.venv\Scripts\python -m pytest -q` was attempted but timed out after 304 seconds; affected focused suite passed.
    - `.venv\Scripts\python launch.py` was attempted as an app boot smoke; the long-running server timed out, then `Invoke-WebRequest http://127.0.0.1:8501` returned HTTP 200 and the smoke process tree was stopped.
  - Contract lock:
    - `DASHBOARD_ARCHITECTURE_SAFETY := VALID iff (shared_pid_probe = utils.process.pid_is_running) and (unsafe_windows_pid_probe_runtime_callers = 0) and (legacy_pid_wrapper_names_preserved = 1) and (strategy_matrix_builder_single = 1) and (dashboard_price_cleaner_delegates_to_core = 1) and (provider_ingestion = 0) and (canonical_market_data_write = 0)`.

Phase 65 Dashboard Unified Data Cache Performance Fix (2026-05-11)

  - Decision record:
    - approve the Performance Part 4 Issue 1 fix for uncached dashboard unified parquet loads.
    - cache `load_unified_data(mode="historical", top_n=2000, start_year=2000, universe_mode="top_liquid")` across Streamlit reruns.
    - invalidate the cache through source-file signatures rather than a blind TTL, so local parquet rewrites are visible on the next rerun.
    - keep provider ingestion, canonical data writes, alpha-engine loop optimization, scanner financial-statement caching, and row-wise scanner enrichment refactors out of this slice.
  - The Decision (Hardcoded):
    - `dashboard.py::_load_unified_data_cached` owns the Streamlit `st.cache_resource` wrapper.
    - `core.data_orchestrator.build_unified_data_cache_signature` owns the cache invalidation fingerprint for relevant processed/static parquet files.
    - `tests/test_data_orchestrator_portfolio_runtime.py` locks file-signature change behavior.
    - `tests/test_dashboard_sprint_a.py` locks that the dashboard load path uses the signature cache.
  - Evidence:
    - pre-fix timing: direct `.venv` load of `load_unified_data(...)` took `8.802s` and `8.393s` for `(2518, 2000)` price/return matrices.
  - Contract lock:
    - `DASHBOARD_UNIFIED_DATA_CACHE := VALID iff (streamlit_cache_resource = 1) and (cache_key_includes_loader_args = 1) and (cache_key_includes_source_parquet_signature = 1) and (source_parquet_rewrite_invalidates = 1) and (provider_ingestion = 0) and (canonical_market_data_write = 0)`.
