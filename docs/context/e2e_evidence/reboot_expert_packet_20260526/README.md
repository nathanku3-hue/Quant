# Terminal Zero: Unified Opportunity Engine

Status: Phase 65 G7.1A starter docs / product-spec rewrite
Date: 2026-05-09
Authority: G7.1A docs-only product canon

Terminal Zero is a local-first discretionary augmentation cockpit. It is not a trading bot.

The product is the **Unified Opportunity Engine**:

```text
Primary alpha:   supercycle gem discovery / de-risked asymmetric upside
Secondary alpha: GodView market-behavior intelligence
Output layer:    buying-range, hold-discipline, trim-risk, and thesis-break prompts
```

The engine helps a discretionary supercycle investor/operator find MU/SNDK-style structural winners and read market behavior well enough to avoid two expensive mistakes:

- buying too early on the left side;
- selling too early while momentum, flows, positioning, and thesis evidence remain supportive.

All outputs are decision-support states or paper-only prompts. They are not orders, broker instructions, alert authorization, or signal approval.

## Current Canon

Use these starter docs first:

- [PRD.md](PRD.md) - product requirements for the Unified Opportunity Engine
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md) - product and architecture specification
- [docs/architecture/top_level_roadmap.md](docs/architecture/top_level_roadmap.md) - G7.1A through G12 roadmap
- [docs/architecture/unified_opportunity_engine.md](docs/architecture/unified_opportunity_engine.md) - top-level product architecture
- [docs/architecture/godview_signal_taxonomy.md](docs/architecture/godview_signal_taxonomy.md) - GodView signal families and use boundaries
- [docs/architecture/data_infra_gap_assessment.md](docs/architecture/data_infra_gap_assessment.md) - current readiness and future provider gaps
- [docs/architecture/codex_agent_research_workflow.md](docs/architecture/codex_agent_research_workflow.md) - Codex/Chrome research-agent SOP
- [docs/architecture/dashboard_product_spec.md](docs/architecture/dashboard_product_spec.md) - dashboard state model and product surface

Historical lowercase docs remain for continuity:

- [docs/prd.md](docs/prd.md)
- [docs/spec.md](docs/spec.md)

Those files now point back to the root canon above. If a conflict appears, the G7.1A root docs win for product framing.

## Product Model

### 1. Primary Alpha: Supercycle Gem Discovery

Find de-risked asymmetric upside: companies or assets where structural demand, supply constraints, ownership behavior, fundamentals, and market action converge into a possible supercycle winner.

This layer is thesis-first. It does not start from generic alpha search, parameter sweeps, or backtest-driven ranking.

### 2. Secondary Alpha: GodView Market-Behavior Intelligence

Read the market around the thesis:

- implied volatility and volatility surface behavior;
- options whales and unusual options activity;
- gamma and dealer-positioning estimates;
- short interest and short-squeeze context;
- CTA/systematic pressure and CFTC positioning proxies;
- sector rotation and factor/risk appetite;
- ETF/passive holdings and flow pressure;
- dark-pool, ATS, and block activity;
- ownership whales through 13F/13D/Form 4 style evidence;
- microstructure and order-book context;
- catalysts, news, and narrative velocity;
- broad regime.

Some of these are observed facts. Others are vendor fields or model estimates. The product must label that difference before downstream use.

### 3. Output Layer: Decision Augmentation

The dashboard should resolve evidence into states such as:

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

These are operator prompts, not automatic trades.

## Current Phase

**Phase G8.2: System-Scouted Candidate Card**

Scope:

- one MSFT candidate-card-only research object from the governed `LOCAL_FACTOR_SCOUT` output;
- no new scout output;
- no cards for DELL/AMD/LRCX/ALB;
- no search, ranking, scoring, thesis validation, buying range, alert, broker call, provider ingestion, or dashboard runtime merge.

G8.2 proves the system-scouted intake-to-card path. Existing dashboard MSFT rows remain legacy runtime output, not the G8.2 card.

Baseline history remains active underneath this product rewrite: D-353 / Phase 64 provenance and validation gates are complete, and R64.1 dependency hygiene is closed with `pip check` passing.

## Roadmap

```text
G7.1A - Starter Docs / PRD / Product Spec Rewrite
G7.1B - Data + Infra Gap Assessment for GodView signals
G7.1C - Codex/Chrome Research Agent SOP
G7.2  - Unified Opportunity Engine State Machine
G7.3  - GodView Signal Source Policy
G7.4  - Supercycle Gem Family Definition, no search
G7.5  - Market Behavior Signal Family Definitions, no search
G8    - One Supercycle Gem Candidate Card, no search
G8.1  - Discovery intake and origin governance
G8.2  - One system-scouted MSFT candidate card, no validation
G9    - One Market Behavior Signal Card, no search
G10   - Dashboard Prototype: watchlist state view
G11   - Bounded discovery under sealed families
G12   - Paper-only buying-range / hold-discipline alerts
```

Immediate next action:

```text
approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold
```

## Current Infrastructure Readiness

Ready for governance foundations:

- canonical daily price governance;
- manifests and provenance checks;
- Candidate Registry;
- V1/V2 mechanical replay discipline;
- dashboard smoke discipline;
- minimal validation lab;
- paper-alert readiness foundations.

Not ready for full GodView without future provider layers:

- options, IV, and OPRA-style data;
- options open interest and volume;
- whale options flow;
- gamma/dealer estimates;
- short interest and borrow/stock-loan context;
- CFTC COT/TFF positioning;
- SEC 13F/13D/Form 4 ownership intelligence;
- ETF holdings and flows;
- dark-pool, ATS, and block activity;
- microstructure and order-book feeds;
- news and narrative velocity capture.

These gaps are expected. G7.1A documents them; it does not build them.

## Development Environment

Hard constraints:

- Python 3.12+ through `.venv`;
- Streamlit UI;
- DuckDB SQL engine;
- Pandas/Polars dataframes;
- Parquet storage;
- Plotly and Streamlit native components;
- pytest and `streamlit.testing` where applicable.

Common commands:

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m pip check
.\.venv\Scripts\python scripts\build_context_packet.py
.\.venv\Scripts\python scripts\build_context_packet.py --validate
.\.venv\Scripts\streamlit run app.py
```

## Current Truth Surfaces

Start from:

- [docs/context/planner_packet_current.md](docs/context/planner_packet_current.md)
- [docs/context/impact_packet_current.md](docs/context/impact_packet_current.md)
- [docs/context/bridge_contract_current.md](docs/context/bridge_contract_current.md)
- [docs/context/done_checklist_current.md](docs/context/done_checklist_current.md)
- [docs/context/multi_stream_contract_current.md](docs/context/multi_stream_contract_current.md)
- [docs/context/post_phase_alignment_current.md](docs/context/post_phase_alignment_current.md)
- [docs/context/observability_pack_current.md](docs/context/observability_pack_current.md)

These surfaces are advisory. They do not authorize trading, alerts, broker automation, candidate generation, search, replay, proxy runs, promotion packets, or scope widening by themselves.

## Non-Negotiable Boundaries

- Terminal Zero is not a trading bot.
- G8.2 candidate cards are not scores, ranks, alerts, recommendations, buying ranges, or broker actions.
- G8 PEAD candidate generation remains held.
- `PEAD_DAILY_V0` remains a valid tactical family, not the product center.
- GodView signals must carry source quality, freshness, latency, confidence, observed-vs-estimated status, allowed use, forbidden use, and manifest identity before downstream use.
- No signal becomes alpha evidence because a research agent captured a source page.
- No credentials, live broker paths, or canonical market-data writes may be handled by Codex/Chrome research workflows.

## Last Updated

2026-05-10 - Phase 65 G8.2 system-scouted candidate-card proof.
