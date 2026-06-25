# GodView Data and Infrastructure Gap Assessment

Status: Phase 65 G7.1B architecture assessment
Date: 2026-05-09
Authority: G7.1B docs + architecture + source mapping only

## Executive Answer

The current repo/data layer can support the GodView Opportunity Engine's governance foundation, but it cannot yet support full GodView market-behavior intelligence.

Ready now:

- canonical daily price/volume governance through existing Tier 0-style Parquet lake and manifests;
- provider-port conventions for quote snapshots;
- provenance, source-quality, manifest, and readiness checks;
- Candidate Registry and family-definition governance;
- V1/V2 mechanical replay discipline;
- dashboard smoke and validation-lab discipline.

Not ready now:

- listed-options tape, IV surface, OI/volume, unusual-options, and gamma/dealer maps;
- FINRA short-interest ingestion;
- CFTC COT/TFF ingestion;
- SEC 13F/13D/Form 4 ownership ingestion;
- ETF/passive holdings and flows;
- ATS/dark-pool/block feeds;
- TAQ/order-book/microstructure feeds for GodView behavior;
- governed news/narrative capture as an evidence layer.

G7.1B therefore approves architecture mapping only. It does not approve provider code, ingestion, state-machine design, candidate generation, signal ranking, backtests, replay, alerts, broker calls, or dashboard runtime behavior.

## Core Assessment Matrix

| Signal family | Purpose | Current readiness | Needed data/provider | Freshness | Trust level | Build priority |
| --- | --- | --- | --- | --- | --- | --- |
| Canonical price/volume | Trend, entry, hold discipline | Ready | Existing Tier 0 lake, manifests, readiness audit | Daily | High | P0 |
| Supercycle thesis docs | Thesis evidence | Partial | Research memo / thesis-card schema, contradiction log, source registry | Manual/daily | Medium-high when sourced | P0 |
| Sector/regime price proxies | Rotation/regime context | Ready with existing canonical data | Existing prices, sector map, regime artifacts | Daily | Medium-high | P0 |
| IV / options tape | Vol confirmation, event risk, IV crush/froth | Not ready | OPRA/options provider or licensed options vendor | Intraday/daily | High if licensed | P1 |
| Options OI / volume | Whale/gamma support | Not ready | OCC/vendor OI and volume data | Daily | High if licensed | P1 |
| Options whales | Large trade context, crowding/hedging read | Not ready | Options tape plus trade classification vendor/policy | Intraday/daily | Medium-high if licensed; estimated intent | P1 |
| Gamma / dealer map | Amplification/dampening context | Not ready | Options chain, OI, model layer | Daily/intraday | Medium; estimated | P1 |
| Short interest | Squeeze base | Not ready | FINRA short-interest provider | Twice monthly | Medium | P1 |
| Borrow / stock loan | Squeeze cost and availability context | Not ready | Stock-loan/borrow-rate provider | Daily/intraday vendor | Medium-high if licensed | P2 |
| CTA / systematic pressure | Trend-following context | Not ready | CFTC COT/TFF plus trend proxies | Weekly/daily | Medium | P1 |
| Ownership whales | Institutional, activist, insider support | Not ready | SEC 13F/13D/13G/Form 4 provider | Filing-lagged | Medium-high | P1 |
| ETF/passive flows | Rotation/passive support | Not ready | ETF holdings/flow provider | Daily/weekly | Medium | P2 |
| Dark pool / block | Accumulation/distribution context | Not ready | FINRA ATS/OTC reports or licensed vendor | Delayed/intraday vendor | Medium | P2 |
| Microstructure | Execution quality, liquidity, order-book context | Not ready | TAQ/TotalView/exchange/vendor feed | Intraday | High if licensed | P3 |
| News/narrative | Theme velocity, catalyst tracking | Not ready | Chrome/Codex research capture plus source policy or news vendor | Real-time/manual | Variable | P2 |

## Readiness Classification

| Signal family | Classification | Why |
| --- | --- | --- |
| Canonical price/volume | `ready_now` | Existing Parquet lake, provenance manifests, data readiness audit, G4/G5/G6 canonical-slice proof. |
| Sector/regime price proxies | `ready_with_existing_canonical_data` | Existing price, sector, and regime surfaces can support broad context if source freshness is labeled. |
| Supercycle thesis docs | `requires_manual_research_capture` | Product truth exists, but thesis-card schema and source registry are future docs/policy work. |
| IV / options tape | `requires_vendor_license` | No OPRA/options provider exists; full tape/quote data requires licensed feed. |
| Options OI / volume | `requires_new_provider` | No OI/volume provider exists; future OCC/vendor source decision needed. |
| Options whales | `requires_vendor_license` | Large-trade classification needs licensed tape and interpretation policy. |
| Gamma / dealer map | `requires_new_provider` | Needs options chain/OI plus model estimates; no current model or provider. |
| Short interest | `requires_new_provider` | FINRA source/provider not implemented; lag must be modeled. |
| Borrow / stock loan | `requires_vendor_license` | No borrow-rate/stock-loan feed exists. |
| CTA / systematic pressure | `requires_new_provider` | CFTC reports and trend proxies are absent from current GodView path. |
| Ownership whales | `requires_new_provider` | SEC filing ingestion and entity mapping are absent. |
| ETF/passive flows | `requires_vendor_license` | ETF holdings/flow source is absent and usually vendor-mediated for clean daily flow. |
| Dark pool / block | `requires_vendor_license` | FINRA public ATS/OTC can support delayed context; intraday/block classification needs vendor source. |
| Microstructure | `defer` | Existing execution telemetry is not GodView market microstructure; full TAQ/order-book feed is expensive and later. |
| News/narrative | `requires_manual_research_capture` | Codex/Chrome may capture research notes, but this is not approved alpha evidence. |
| Broker/live execution signals | `reject_current_scope` | G7.1B forbids alerts, broker calls, live orders, and execution behavior. |

## Current Repo Source Map

| Repo surface | Current capability | GodView support level |
| --- | --- | --- |
| `data/provenance.py` | Source-quality constants, manifest creation/validation, atomic JSON writes, alert/quote validation. | Strong governance foundation; not a GodView provider layer. |
| `data/providers/base.py` | `QuoteSnapshot` metadata and `MarketDataPort` protocol. | Useful provider-port pattern for future adapters. |
| `data/providers/yahoo_provider.py` | Non-canonical Yahoo quote/daily-bar convenience provider. | Useful only for research/convenience; not canonical GodView evidence. |
| `data/providers/alpaca_provider.py` | Operational Alpaca quote provider via broker API. | Operational quotes only; does not approve broker use or GodView evidence. |
| `data/providers/registry.py` | Provider factory for Yahoo/Alpaca. | Existing registry is narrow; no GodView providers exist. |
| `scripts/audit_data_readiness.py` | Daily paper-alert readiness audit for price/fundamentals/ticker/sector/macro/liquidity/sidecars. | Good readiness model; scope is daily governance, not full GodView. |
| `v2_discovery/readiness/*` | Canonical tiny-slice readiness proof and freshness checks. | Strong pattern for future provider proof. |
| `v2_discovery/replay/*` | Mechanical replay/report discipline. | Governance proof only; no new replay should run for G7.1B design. |
| `docs/architecture/godview_signal_taxonomy.md` | Product taxonomy and metadata contract. | Input taxonomy; needs source matrix and policies added by G7.1B. |
| `execution/microstructure.py` and tests | Execution telemetry and latency/slippage plumbing. | Not a market microstructure provider; must not be treated as TAQ/order-book GodView. |

Missing future surfaces confirmed in G7.1B source mapping:

```text
data/providers/options_provider.py
data/providers/short_interest_provider.py
data/providers/cftc_provider.py
data/providers/sec_filings_provider.py
data/providers/etf_flow_provider.py
data/providers/ats_block_provider.py
data/providers/news_research_provider.py
signals/source_registry.py
signals/freshness_policy.py
signals/confidence_policy.py
signals/godview_state_machine.py
```

These paths are future architecture targets only. G7.1B does not create them.

## External Source Anchors

Use official or primary sources for future source-policy design:

- OPRA/OLPP: official plan for consolidated options last-sale reports and quotation information from U.S. options exchanges; serious anchor for options tape, IV inputs, options-whale context, and gamma prerequisites. Source: `https://www.sec.gov/file/plan-reporting-consolidated-options-last-sale-reports-and-quotation-information`
- FINRA short interest: reported twice monthly; useful for squeeze-base context, not real-time squeeze timing. FINRA distinguishes short interest from daily short-sale volume. Sources: `https://www.finra.org/investors/insights/short-interest`, `https://www.finra.org/finra-data/browse-catalog/short-sale-volume`
- CFTC COT/TFF: weekly positioning reports based on Tuesday open interest and normally released Friday at 3:30 p.m. ET; useful for systematic/CTA context, not single-name real-time flow. Sources: `https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm`, `https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm`
- SEC filings: 13F/13D/13G/Form 4 filings are observed public records with filing lags; useful for ownership-whale context after entity mapping.
- Codex/Chrome: permitted only for research capture and documentation workflows, not alpha evidence, source approval, canonical market-data writes, alerts, or trading actions. Sources: `https://help.openai.com/en/articles/11369540-codex-in-chatgpt-faq`, `https://chromewebstore.google.com/detail/codex/hehggadaopoacecdllhhajmbjkdcmajg`

## Current Infrastructure Verdict

```text
godview_current_infra = governance_ready + price_volume_ready + provider_port_pattern_ready
godview_current_infra != full_market_behavior_ready
```

The repo can govern future GodView signals once they exist. It cannot yet observe or license most GodView inputs.

## Explicitly Not Fixed In G7.1B

- yfinance migration;
- stale S&P sidecar;
- OPRA/options ingestion;
- SEC filing ingestion;
- CFTC ingestion;
- FINRA short-interest ingestion;
- microstructure feed;
- dashboard runtime behavior;
- state machine;
- candidate generation;
- signal ranking;
- broad workspace `compileall .` inherited null-byte / ACL traversal debt.

## Acceptance Lock

G7.1B is complete only if:

- every signal family has readiness, provider need, freshness, trust level, and build priority;
- current infra is labeled sufficient for governance but not full GodView;
- future provider ports are documented, not implemented;
- observed/estimated/inferred distinctions are explicit;
- Codex/Chrome research agents are limited to research capture/docs;
- G7.2 and G8 remain held.
