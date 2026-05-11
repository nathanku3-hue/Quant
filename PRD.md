# Product Requirements Document: Unified Opportunity Engine

Status: Canonical product PRD for Phase 65 Portfolio Universe Construction Fix
Date: 2026-05-10
Owner: PM / Architecture Office
Scope: docs and architecture only

## Current Phase 65 Notices

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
