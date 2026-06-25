# Product Requirements Document: Unified Opportunity Engine

Status: Canonical product PRD for Phase 65 Portfolio Universe Construction Fix
Date: 2026-05-10
Owner: PM / Architecture Office
Scope: docs and architecture only

## Current Phase 65 Notices

Portfolio Replay Role Contract (2026-05-15):

- Portfolio replay rows must carry durable roles so users and future readers can distinguish current holdings, historical context, flat replay exposure, cash, and unavailable evidence.
- Selected-method replay exposure must be labeled as replay/current weight, not generic lifecycle weight.
- Lifecycle/event/decision weights may appear only as audit metadata.
- Saved replay artifacts must remain backward compatible for missing role fields and fail closed for unrelated schema drift.
- Diagnostics must use the same rendered replay context and identity as the Portfolio page.
- This does not authorize canonical provider ingestion, market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Dashboard Replay Aux Weight Semantics + Stacked Timeline (2026-05-15):

- Portfolio & Allocation replay-facing aux surfaces must display replay-derived `target_weight`, not independent lifecycle/event/decision weight fields.
- Original aux weights may remain visible only as audit metadata (`audit_weight`) when useful.
- Strategy Replay Timeline should visualize allocation composition as a stacked step-area chart over replay `target_weight`.
- Partial saved/transitional replay schemas must render unavailable/empty states instead of crashing the Portfolio page.
- This does not authorize provider ingestion, canonical market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Replay Selected Price Loading + MU/SNDK Eligibility Trace (2026-05-15):

- Dashboard replay optimization must preserve full PIT membership proof and only shrink selected asset price/return loading after that proof is built.
- MU/SNDK disappearance analysis is a separate strategy/data eligibility diagnostic, not a replay performance shortcut.
- Current diagnostic through 2026-05-11 shows MU and SNDK are pinned, mapped, PIT-present on the latest replay date, and locally priced; MU latest fails technical quality, SNDK latest fails factor threshold.
- This does not authorize watchlist-only replay, canonical provider ingestion, market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Max Replay Timeline Sampling Fix (2026-05-15):

- Strategy Replay Timeline max-window sampling must normalize grouped weekly keep-dates through the pandas Series `.dt` accessor.
- Timeline weekly sampling remains display-only over daily replay rows and does not authorize a sampled replay source for Portfolio Performance.
- This does not authorize canonical provider ingestion, market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Portfolio Single-Source Replay Page (2026-05-14):

- Portfolio & Allocation replay-facing evidence now comes from one daily forward-walk replay context.
- The visible allocation display is the latest daily replay snapshot for the selected method/window.
- Portfolio Performance refuses sampled replay and optimizer fallback; missing daily replay renders unavailable.
- Strategy Replay Timeline may sample only from daily replay rows after the run exists.
- Latest Buys/Sells is a filtered view of the Buy/Sell Decision Log / `bundle.decision_rows`.
- This does not authorize canonical provider ingestion, market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Saved Artifact Single-Source Aux Surface Fix (2026-05-14):

- Portfolio & Allocation saved-artifact mode must preserve artifact event and decision rows exactly, including valid empty frames.
- A saved artifact with daily portfolio rows but no event/decision rows must not render separately loaded ENTER/EXIT or Buy/Sell rows while labeled `source_mode="saved_artifact"`.
- The focused frontend suite passes with 106 tests after the regression was added.
- This does not authorize canonical provider ingestion, market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Backend Replay Reader Identity Hardening (2026-05-14):

- Saved selected-method replay artifacts must carry non-empty manifest `run_id`, `source_id`, and `method_id`.
- Blank manifest identity fails closed before optional caller expected IDs or parquet/manifest equality can validate a bundle.
- The hardening keeps replay artifacts display-only and does not change dashboard runtime wiring.
- This does not authorize canonical provider ingestion, market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Portfolio Market-Data Freshness Endpoint Cache (2026-05-14):

- Portfolio & Allocation must compute endpoint freshness once per loaded local price matrix signature, then reuse per-column endpoints downstream.
- The endpoint cache preserves the fail-closed freshness contract; it is a performance fix, not a relaxation of stale-data handling.
- Dashboard YTD, optimizer selected-price prep/default ordering, and optimizer universe eligibility should consume the shared endpoint snapshot instead of rescanning the full `prices_wide` matrix.
- Actual local measurement on `(2857, 2000)` prices: snapshot `0.2966s`, legacy loop `0.9555s`, endpoint maps matched, downstream lookups were near-zero.
- This does not authorize canonical provider ingestion, market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Portfolio Market-Data Freshness Fail-Closed Fix (2026-05-14):

- Portfolio & Allocation must treat price freshness as per-asset, not as one shared matrix date.
- Endpoint freshness semantics are centralized in `core.data_orchestrator`; callers may choose strict or tolerated freshness only through an explicit policy parameter.
- Benchmark YTD, portfolio YTD, optimizer selected-price prep, optimizer default ordering, and optimizer universe eligibility must not present stale ragged columns as current evidence.
- If a weighted portfolio leg is stale at the required endpoint, the portfolio YTD fallback fails closed rather than compounding a partial portfolio.
- Optimizer overlays and universe eligibility may use display-only live refresh, but stale assets that cannot be refreshed are dropped/excluded with explicit diagnostics; selected overlay refresh requires same-column local/live overlap before live rows can become allocation evidence.
- This does not authorize canonical provider ingestion, market-data writes, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Dashboard Backend Bundle Integration Verification (2026-05-14):

- Portfolio & Allocation Strategy Replay now consumes the backend selected-method replay bundle through `build_selected_method_replay(...)`.
- The verified dashboard path remains PIT-safe through per-date `r3000_pit` input loading.
- Runtime smoke and full pytest passed for this verification.
- Saved replay artifact-reader consumption and explicit cold-start/rerun performance-budget enforcement remain future work.
- This does not authorize provider ingestion, live trading, broker behavior, alerts, ranking, scoring, recommendations, autonomous allocation, or strategy promotion.

Replay Coverage Contract Audit Fix (2026-05-14):

- Selected-method replay coverage remains auditable through `coverage_segments` metadata and specific `input_unavailable:*` replay reasons.
- Daily all-uncovered replay routing, including row-heavy explicit-member unavailable windows, must stay within the tested budget without optimizer or input-loader calls.
- Replay performance must avoid same-date lookahead by applying generated weights to next tradable returns.
- Context bootstrap must prefer the latest complete current-truth New Context Packet over older same-phase handovers.
- This fix improves replay reliability and audit performance only; it does not authorize provider ingestion, market-data writes, broker behavior, alerts, ranking, scoring, recommendations, live trading, or strategy promotion.

Data/PIT Strategy Replay Hardening (2026-05-13):

- Strategy Replay must be PIT-safe at both row and universe boundaries.
- Replay cache signatures default to and require `r3000_pit`; full-history `top_liquid` membership is not valid for replay input caching.
- Display-only replay input artifacts may be stored only under `data/runtime_cache/strategy_replay` for repo-local data writes.
- Portfolio & Allocation Strategy Replay must generate target weights from per-date local PIT input slices, not from a raw global price matrix.
- This does not authorize provider ingestion, canonical market-data writes, broker behavior, alerts, ranking, scoring, or live trading.

Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay (2026-05-13):

- Rule of 100 visible allocation uses `controls.max_weight` as both the per-name budget and single-name cap in direct UI and Strategy Replay.
- Frozen Rule100 audit/history defaults stay at 10% gross budget per eligible name and 15% cap unless a separate labeled artifact is approved.
- Benchmark YTD keeps local TRI history first but live-overlays stale or missing benchmark tickers per ticker, so stale QQQ is not silently forward-filled flat while SPY is fresh.
- This does not authorize canonical provider ingestion, market-data writes, broker behavior, alerts, ranking, scoring, recommendations, or live trading.

G8.1A Discovery Drift Correction (2026-05-10):

- The current six-name discovery queue is user-seeded and theme/supply-chain-adjacent, not pure system-scouted output.
- Required intake provenance fields are `discovery_origin`, `origin_evidence`, `scout_path`, `is_user_seeded`, `is_system_scouted`, `is_validated`, and `is_actionable`.
- `MU` remains the only candidate card; `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB` remain intake-only.
- All six names remain not system-scouted, not validated, and not actionable.
- `LOCAL_FACTOR_SCOUT` is reserved for G8.1B and is not used in G8.1A.
- No alpha search, ranking, scoring, buying range, alert, broker behavior, provider ingestion, dashboard runtime behavior, or recommendation is authorized.

G8.2 System-Scouted Candidate Card (2026-05-10):

- `MSFT` is the only approved G8.2 card because it is the sole governed `LOCAL_FACTOR_SCOUT` output from G8.1B.
- The MSFT card is `candidate_card_only`; it is not validated, actionable, ranked, scored, or recommended.
- `MU` and `MSFT` are the only candidate cards after G8.2.
- Existing dashboard rows that show `MSFT`, tactical prices, trend labels, `COILED SPRING`, or `IGNORE` remain legacy runtime output, not the G8.2 card.
- G8.2 adds no dashboard merge, provider ingestion, alert, broker behavior, buying range, score, rank, buy/sell/hold output, or new scout output.

Portfolio Universe Construction Fix (2026-05-10):

- Portfolio Optimizer defaults now come from an explicit universe builder, not from dashboard display order or `selected_tickers[:20]`.
- `ENTER STRONG BUY` and `ENTER BUY` are eligible by default; `WATCH` is research-only; `EXIT`, `KILL`, `AVOID`, and `IGNORE` are excluded.
- The UI must report missing ticker mappings, insufficient local price history, and max-weight feasibility before allocation.
- The current optimizer is thesis-neutral and must not infer MU conviction, thesis anchors, or endgame allocation from historical price/covariance alone.
- No MU floor, Black-Litterman, conviction mode, thesis-anchor sizing, manual override, scanner rewrite, provider ingestion, alert, broker behavior, or new objective is authorized.

Optimizer Core Structured Diagnostics (2026-05-11):

- The optimizer may now report structured diagnostics for feasibility, SLSQP status, active bounds, constraint residuals, equal-weight boundary pressure, and labeled fallback allocations.
- Fallback allocations must be labeled as fallback and not optimized.
- This does not approve MU conviction, WATCH investability expansion, Black-Litterman, a simple tilt optimizer, new objectives, scanner rules, manual overrides, provider ingestion, alerts, broker behavior, or replay behavior.

Portfolio Data Boundary Refactor (2026-05-11):

- `core/data_orchestrator.py` owns selected-stock live display overlay fetching, adjusted-close extraction, local TRI scaling, stitching, and `data/backtest_results.json` strategy-metrics parsing.
- `views/optimizer_view.py` must render optimizer UI only; it must not import yfinance or read `data/backtest_results.json` directly.
- The freshness overlay remains in-memory display-only and does not authorize canonical provider ingestion, alerts, broker behavior, ranking, scoring, or candidate-card integration.

Portfolio Optimizer View Test and Performance Hardening (2026-05-11):

- `/portfolio-and-allocation` optimizer rendering now has dedicated Streamlit `AppTest` coverage for view rendering, mean-variance control selection, and sector-cap UI paths.
- Recent close-price display refresh uses a non-canonical Parquet cache owned by `core/data_orchestrator.py`; cold cache misses schedule background refresh and fall back to local TRI data for immediate render.
- Optimizer math execution is cached by selected price frame, method, max-weight, and risk-free-rate parameters inside `views/optimizer_view.py`.
- This does not approve canonical provider ingestion, new optimizer objectives, lower-bound policy, MU conviction, WATCH investability expansion, alerts, broker behavior, rankings, scores, or candidate-card dashboard integration.

Portfolio Lifecycle Replay Churn + Weight Policy (2026-05-12):

- Position Lifecycle Replay current holds must not collapse to 100% cash unless lifecycle events are truly sell-all as of the PIT-safe cutoff.
- ENTER replay weights use a max-10 position budget (`0.10`) rather than `1 / replay_universe`.
- Entries require the raw PIT entry gate, a 3-day confirmation streak, and at least 3 positive present PIT vectors across demand, moat, inventory/quality, and discipline.
- Exits require a hard 20% SMA20 stretch or a confirmed raw exit after a 20-day minimum hold; re-entry waits 10 calendar days.
- This does not approve the rejected Phase 54 Rule-of-100 sleeve, ranking, scoring, optimizer objective changes, alerts, broker behavior, provider ingestion, or live trading.

Rule of 100 Method Label (2026-05-12):

- The Portfolio Optimizer `Method` dropdown may expose `Rule of 100` as a user-facing lifecycle allocation mode.
- Selecting `Rule of 100` shows Rule100 softmax v1 target weights for eligible lifecycle holds plus residual cash; if no holds are softmax-eligible, it shows cash.
- `Rule of 100` in the dropdown is not a mean-variance optimizer objective, ranked alpha model, broker instruction, alert, or recommendation label.

Rule100 Softmax v1 Audit (2026-05-12):
- `strategies/rule100_softmax.py` owns the pure softmax v1 sizing helpers and the thin Kelly comparator.
- `scripts/rule100_softmax_v1_audit.py` owns the shared PIT replay/audit harness.
- `views/optimizer_view.py` routes the explicit `Rule of 100` method to softmax v1 target weights and stores `source=rule100_softmax_v1`.
- Softmax v1 is the primary sizing path in the audit set: 10% gross budget per eligible name, 15% per-name cap, explicit cash residual.
- Current target state is AMAT 10%, LRCX 10%, TSM 0%, CASH 80%.
- Kelly remains comparator-only on the same candidate frame and does not become a second full stack.
- Artifact set: `data/processed/rule100_softmax_v1_summary.json`, `data/processed/rule100_softmax_v1_comparison.csv`, `data/processed/rule100_softmax_v1_sample_output.csv`, `data/processed/rule100_softmax_v1_cash_allocation.csv`, and `data/processed/rule100_softmax_v1_history.csv`.
- Position Lifecycle Replay history must preserve original event weights while showing softmax v1 target weights as a separate PIT audit overlay.

Rule100 Softmax v1.1 Research Contract (2026-05-12):

- v1.1 remains research-only; it does not replace v1 runtime routing, mutate the lifecycle log, mutate position memory, or add broker/alert/ranking/scoring behavior.
- The active v1.1 artifact contract is only `data/processed/rule100_softmax_v1_1_comparison.csv` plus `data/processed/rule100_softmax_v1_1_summary.json`; stale `rule100_softmax_v1_1_history.csv` is retired and must not be treated as current.
- Factor coverage counts the four approved factor groups, not raw columns; `capital_cycle_score` and `quality_composite` are alternate inputs to one capital-discipline group.
- Missing factor strength shrinks toward neutral `0.50` by group coverage.
- A real `AppTest.from_file("dashboard.py")` regression must prove the Portfolio & Allocation Policy Target Timeline renders TSM 2026-05-11 with target 0%, event weight 10%, cash 80%, and `tighten_below_hold_threshold`.

Dashboard Architecture Safety Slice (2026-05-11):

- PID liveness checks now route through `utils.process.pid_is_running`, including dashboard backtest PID status and lock-owner probes in updater, parameter sweep, release controller, and phase16 optimizer code.
- Direct runtime `os.kill(pid, 0)` liveness probes are prohibited outside the shared utility because Windows can treat them as real process signals.
- Dashboard backtest launch now refuses to spawn a second job when a live PID file exists rather than terminating an unverified PID.
- The dashboard modular strategy matrix now has one initialization path, and dashboard portfolio price cleanup delegates to `core.data_orchestrator.clean_price_frame`.
- This is safety and architecture hygiene only; it adds no provider ingestion, canonical data write, strategy search, ranking, scoring, alert, broker behavior, or dashboard content redesign.

DASH-0 Dashboard IA Plan (2026-05-10):

- Approved the future dashboard page map: Command Center, Opportunities, Thesis Card, Market Behavior, Entry & Hold Discipline, Portfolio & Allocation, Research Lab, Settings & Ops.
- Planning-only: no runtime dashboard files, views, providers, alerts, broker behavior, factor scout, candidate cards, discovery intake, or backtests are changed.
- Next action is `approve_dash_1_page_registry_shell_or_hold`.

## 1. Product Definition

**Product:** Unified Opportunity Engine

Terminal Zero is not a trading bot. It is a discretionary augmentation cockpit for finding de-risked asymmetric upside and reading market behavior so the user avoids:

1. buying too early on the left side;
2. selling too early while momentum, flows, positioning, and thesis evidence remain supportive.

The engine combines:

```text
Primary alpha:   Supercycle Gem Discovery
Secondary alpha: GodView Market Behavior Intelligence
Output layer:    Decision Augmentation
```

## 2. Primary User

Discretionary supercycle investor/operator.

The user is not asking the system to place trades. The user is asking the system to compress research, expose market-behavior context, and maintain entry/hold discipline.

## 3. Primary Job

Find MU/SNDK-style de-risked asymmetric upside:

- structural winners with credible supercycle setup;
- thesis evidence that can be reviewed and challenged;
- buying-range discipline that reduces left-side entry pain;
- hold discipline that prevents premature selling when the evidence still supports the winner.

## 4. Secondary Job

Read market behavior around the thesis:

- implied volatility and volatility surface behavior;
- options whales and unusual options activity;
- gamma and dealer-positioning estimates;
- short interest and squeeze context;
- CTA/systematic pressure and futures-positioning proxies;
- sector rotation and factor/risk appetite;
- ETF/passive holdings and flow pressure;
- dark-pool, ATS, and block activity;
- ownership whales through SEC 13F/13D/Form 4 style evidence;
- microstructure and order-book context;
- catalysts, news, and narrative velocity;
- regime.

The GodView layer is not a trigger machine. It is a context layer that tells the operator whether market behavior is confirming, contradicting, crowding, squeezing, or de-risking the thesis.

## 5. Final Output

Dashboard states and paper-only prompts:

```text
wait
watch
accumulation
confirmation
buying range
let winner run
trim optional
exit risk
thesis broken
```

These outputs are not live alerts in G7.1A, not broker instructions, and not promotion packets.

## 6. Product Principles

### 6.1 Discretionary Augmentation

The system supports the operator's judgment. It does not replace it.

### 6.2 Thesis Before Search

The product does not start from generic quant alpha search. It starts from a product job: finding de-risked asymmetric upside and protecting the operator from poor entry/exit timing.

### 6.3 GodView Is Evidence, Not Permission

Market-behavior signals may support, weaken, or contextualize a thesis. They may not approve a signal, bypass source-quality rules, or become automatic trade triggers.

### 6.4 Source Quality Must Be Visible

Every future GodView signal must carry:

```text
source_quality
provider
provider_feed
freshness
latency
confidence
observed_vs_estimated
allowed_use
forbidden_use
manifest_uri
```

### 6.5 Paper-Only Prompts Come Later

G12 may add paper-only buying-range / hold-discipline alerts after source policy, state machine, dashboard prototype, and sealed family definitions exist. G7.1A does not emit prompts.

## 7. In Scope For G7.1A

- rewrite starter docs;
- create root PRD and product spec canon;
- replace PEAD-centered roadmap language;
- document the Unified Opportunity Engine;
- document GodView taxonomy;
- document data and infrastructure gaps;
- document Codex/Chrome research-agent workflow;
- refresh phase brief and current truth surfaces.

## 8. Out Of Scope For G7.1A

- candidate generation;
- alpha search;
- backtests;
- replay runs;
- proxy runs;
- options ingestion;
- short-interest ingestion;
- CFTC ingestion;
- SEC filings ingestion;
- ETF flow ingestion;
- news provider ingestion;
- signal ranking;
- buying/selling alerts;
- broker calls;
- Alpaca live behavior;
- OpenClaw notifications;
- new dashboard runtime behavior.

## 9. Current Readiness

Current infrastructure is sufficient for the governance path:

- canonical daily price governance;
- manifests and provenance checks;
- Candidate Registry;
- V1/V2 mechanical replay discipline;
- dashboard smoke discipline;
- minimal validation lab;
- paper-alert readiness foundations.

Current infrastructure is not sufficient for full GodView without future provider layers:

- options, IV, and OPRA-style data;
- options open interest and volume;
- whale options flow;
- gamma/dealer estimates;
- short interest and borrow/stock-loan context;
- CFTC COT/TFF positioning;
- SEC 13F/13D/Form 4 ownership intelligence;
- ETF holdings and flows;
- dark-pool, ATS, and block activity;
- microstructure and order book;
- news and narrative velocity.

## 10. Roadmap

```text
G7.1A - Starter Docs / PRD / Product Spec Rewrite
G7.1B - Data + Infra Gap Assessment for GodView signals
G7.1C - Codex/Chrome Research Agent SOP
G7.2  - Unified Opportunity Engine State Machine
G7.3  - GodView Signal Source Policy
G7.4  - Supercycle Gem Family Definition, no search
G7.5  - Market Behavior Signal Family Definitions, no search
G8    - One Supercycle Gem Candidate Card, no search
G9    - One Market Behavior Signal Card, no search
G10   - Dashboard Prototype: watchlist state view
G11   - Bounded discovery under sealed families
G12   - Paper-only buying-range / hold-discipline alerts
```

Immediate next action:

```text
approve_g7_1b_data_infra_gap_or_g7_2_state_machine
```

## 11. Acceptance Checks

- PRD names the product Unified Opportunity Engine.
- Product spec merges primary alpha and secondary alpha into one state engine.
- Roadmap no longer centers PEAD as the main product.
- GodView explicitly includes IV, options whales, gamma, short squeeze, CTA, rotation, ETF/passive, dark-pool/block, ownership whales, microstructure, and regime.
- Data/infra gap assessment says current infra is enough for governance, not enough for full GodView.
- Codex/Chrome research workflow is documented with allowed and forbidden uses.
- G8 PEAD generation remains held.
- No new search/backtest/replay/alert/broker/provider implementation is added.

## 12. Open Risks

- yfinance migration remains future debt.
- Primary S&P sidecar freshness remains stale through 2023-11-27.
- Full GodView requires future provider policy and ingestion design.
- Some GodView concepts are vendor/model estimates, not directly observed facts; the product must label this before use.

## Portfolio Lifecycle Current Holds Addendum

- Portfolio & Allocation must treat Position Lifecycle Replay as the current-hold authority when replay evidence exists.
- If the latest PIT-safe lifecycle state is not sell-all, current allocation must not render as 100% cash.
- Open lifecycle holdings remain held when there is no fresh PIT ENTER today; future-dated replay rows are ignored.
- Portfolio performance must preserve residual cash for sub-100% lifecycle holdings.
- This does not authorize provider ingestion, alerts, broker behavior, ranking, scoring, or a new optimizer objective.

## Portfolio Replay Selection Identity Addendum

- Portfolio replay identity must be driven by explicit signed replay selection state, not hidden optimizer session mirrors.
- The replay selection signature must bind typed asset identities and selected price content so same-shape edits or numeric-string collisions fail closed.
- If the signed selection is missing, stale, or mismatched, Portfolio replay surfaces must fail closed as unavailable.
- The page must not fall back to the first 10 price columns for replay identity.
- Transitional event/decision aux loading remains a backend artifact producer follow-up and does not authorize provider ingestion, alerts, broker behavior, ranking, scoring, recommendations, or live trading.

## Lifecycle Decision Export Addendum

- The product may export a PIT-safe replay-analysis decision tape before changing lifecycle policy.
- Exported BUY/SELL labels are analysis labels that must match lifecycle ENTER/EXIT events; they are not orders, alerts, recommendations, rankings, or dashboard action labels.
- The full export records reasons and gate state for BUY, SELL, HOLD, and NO_ACTION rows.
- The export exists to audit good/bad replay behavior before implementing the true Rule-of-100 lifecycle policy.
- This does not authorize provider ingestion, canonical writes, broker behavior, alerts, ranking, scoring, or a new optimizer objective.

## Rule100 Lifecycle Policy v0 Addendum

- The product promotes the existing lifecycle replay into a concrete Rule100 lifecycle policy, not a generic multi-strategy framework.
- Rule100 factor state is explicit and proxy-labeled: demand, supply, pricing, and margin are mapped from current PIT feature columns with provenance.
- TRIM and TIGHTEN are audit-only states in v0; they do not change current portfolio weights.
- Entry sizing is conviction-based and capped, but current data still results in 10% entry weights because no promoted entry has 4/4 factors.
- This does not authorize live trading, broker orders, alerts, ranking, scoring, dashboard recommendations, provider ingestion, canonical writes, or a Phase 54 Rule-of-100 sleeve reopen.

## Optimizer History Diagnostics Split Addendum

- Portfolio Optimizer universe diagnostics must distinguish true missing local price history from stale local price endpoints.
- Assets with enough observations but an old endpoint remain fail-closed as optimizer-ineligible, but the UI labels them as `Stale Endpoint`, not generic history failure.
- Assets with no local series or too few observations are labeled `Missing History`.
- The underlying `insufficient_history` gate remains unchanged and must not be relaxed to make stale assets investable.
- This does not authorize provider ingestion, canonical market-data writes, ranking, scoring, recommendations, broker behavior, alerts, or live trading.
