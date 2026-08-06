# AOV-2 / Identification Candidate Source Pool

Date: 2026-08-06
Status: `DISCOVERY_ONLY; AUTHENTICATION/PIT/TERMS UNVERIFIED; NOT AOV-0 AUTHORITY`
Owners: AOV-2 Event-State Integration / `IDENTIFICATION-READINESS-PROBE-0`
Critical-path effect: `NONE`

## Purpose

Retain a bounded inventory of ChatGPT-accessible or publicly described finance-data applications for two later uses:

1. **AOV-2 event-state exploration** — company events, filings, earnings material, market context, and derived research views.
2. **Identification Readiness Probe** — discovery of candidate sources that might support institutional-flow, holdings, mapping, or related feasibility work.

This inventory is not a production provider stack, not a data-entitlement statement, and not evidence that any source is point-in-time, exportable, stable, or usable without a separate external login.

## Authentication assumption and caveat

For this registry, “no login” means **no separately supplied broker/data-vendor account or API key**. A user still needs a ChatGPT account and may need to press **Connect**. A listed app may still present a second OAuth, subscription, entitlement, regional, workspace-admin, or provider-login requirement.

Therefore every entry begins as:

```text
AUTHENTICATION_UNVERIFIED
PIT_UNVERIFIED
EXPORT_UNVERIFIED
TERMS_UNVERIFIED
```

Public listing language or a visible Connect button does not establish anonymous access or research-data authority.

## Preferred exploration shortlist

The first bounded discovery set is:

```text
Massive
+ Fiscal.ai
+ MetricDuck
+ Quartr
+ FactorWeave
+ CoinGecko
```

Intended exploratory coverage:

| Candidate | Intended discovery role |
|---|---|
| Massive | broad stock and market-data discovery |
| Fiscal.ai | public fundamentals, source filings, and market-quote discovery |
| MetricDuck | SEC filings and financial-statement discovery |
| Quartr | earnings calls, presentations, and company-event research |
| FactorWeave | quantitative/factor research discovery |
| CoinGecko | public crypto-market discovery |

No member of this shortlist is preferred production infrastructure until it passes the readiness contract below.

## Candidate inventory — likely lower external-credential friction

These names are retained exactly as a candidate pool, not as verified access claims.

### Stocks, ETFs, and market data

- Financial Datasets
- TickerSage
- AlphaStocks
- Fiscal.ai
- ForInvest
- Next Stock – Market Insights
- TradingCursor
- FactorWeave
- Longbridge
- FinancialReports
- MetricDuck
- Massive
- Co-Invest
- Murali Growth Screener Mobile
- Public Equity Investing

### Research, filings, and investment analysis

- Quartr
- Financial Summarizer Pro
- PortfolioIQ
- Theia Insights
- Economic Mind
- Stocktwits
- CredCore – Tusk Liquid
- The Fly Market Intelligence
- WikiFx
- Learn to invest with AJ Bell
- Investment Banking

### Crypto market data

- Binance
- Kraken
- OKX
- CryptoAudit
- CoinMarketCap
- CoinGecko
- Exum: ExoScope Crypto
- Paribu
- TickerSage

### Options and strategy tools

- OptionsCalc
- Options Analysis Suite
- Vega Options
- Unusual Whales — premium/login risk must be assumed until disproved

### FX, metals, and calculators

- Any Exchange Rate
- XE Currency Converter
- Xflow
- U.S. Gold Bureau Metal Spots
- Mamble Calculators
- PortfolioIQ

## Candidate inventory — entitlement or login risk

These may provide high-value professional data, but they are not candidates for a strict zero-external-auth path without explicit proof:

- PitchBook
- FactSet AI-Ready Data
- Daloopa
- S&P Global
- LSEG
- Bigdata.com
- Morningstar
- Third Bridge
- Guidepoint
- MSCI Connector
- Token Terminal
- Aiera
- CB Insights
- Moody’s
- D&B Finance Analytics
- Interactive Brokers
- TipRanks
- Moody’s Credit MCP
- Zacks Financial Data
- Octus
- Clarity AI
- Unusual Whales
- MT Newswires
- The Fly Market Intelligence

The catalog presence of these products does not imply anonymous access, redistribution rights, historical PIT access, or stable export capability.

## Avoid under a strict zero-external-auth constraint

Account-linked portfolio, broker, banking, or personal-finance connectors are not the default research-source path:

- Parqet
- Kubera
- Fugle-Stock
- Revolut X
- Webull
- Gainium
- Cryptoworth
- Interactive Brokers / IBKR
- YNAB
- Mercury
- other portfolio/banking connectors requiring personal account linkage

They may be evaluated only under a separately authorized operational-integration phase, never as a shortcut around the Truth Plane.

## Readiness probe contract

Each candidate must be evaluated independently. A bundle-level claim is forbidden.

| Gate | Required evidence |
|---|---|
| Authentication | Exact Connect flow; whether second OAuth/login, subscription, geography, plan, or workspace-admin approval is required |
| Provenance | Original source names, URLs or identifiers, source timestamps, and citation/locator support |
| PIT semantics | `valid_at`, first-public/accepted time, revision history, and whether historical answers can be reconstructed as known then |
| Permanent identity | CIK, PERMNO, ISIN, FIGI, exchange identity, or another stable cross-time identifier; ticker-only is insufficient |
| Export and custody | Ability to retain raw response/object bytes, schema, timestamp, request identity, and exact replay evidence |
| Coverage | Asset classes, markets, fields, date history, corporate actions, delistings, and missingness behavior |
| Reliability | Rate limits, latency, stale responses, failure modes, correction policy, and deterministic repeatability |
| Terms | Research storage, derived data, redistribution, commercial use, attribution, and retention rights |
| Cost | Free/public boundary, paid tier, query limits, engineering cost, and expected information value |
| Security | No credential exposure, personal account linkage, broker authority, or unintended write capability |

## Admission ladder

```text
CANDIDATE_LISTED
→ CONNECTIVITY_CONFIRMED
→ SOURCE_READINESS_PROBED
→ DISCOVERY_SOURCE or INTERPRETATION_SOURCE
→ PIT_CANDIDATE
→ separately reviewed PIT_TRUTH_AUTHORITY
```

Definitions:

- `DISCOVERY_SOURCE`: useful for finding documents, entities, or candidate questions; cannot populate tradable state.
- `INTERPRETATION_SOURCE`: may support bounded event/research interpretation with citations; cannot own market/accounting truth.
- `PIT_CANDIDATE`: exact time, identity, source, retention, and export evidence exists, but canonical admission has not occurred.
- `PIT_TRUTH_AUTHORITY`: requires a separate executable contract, independent review, versioned ingestion, and fail-closed replay. No app receives this status from catalog text or a successful chat response.

## AOV-2 usage boundary

AOV-2 may use approved discovery/interpretation sources to test one event family at a time:

```text
no-event state update
vs event-as-measurement
vs event-as-intervention candidate
```

Event-derived outputs must carry source references, `known_at`, uncertainty, and alternative interpretations. They do not directly issue target weights.

## Identification Probe usage boundary

`IDENTIFICATION-READINESS-PROBE-0` may use this pool to discover candidate holdings, filings, entity maps, or flow-related sources. The probe must still establish:

- actual publication latency;
- historical identity mapping;
- usable coverage;
- concentration and first-stage plausibility;
- export/custody rights;
- bounded acquisition and engineering cost.

Catalog breadth or convenient access is not identification.

## Critical-path prohibition

This source pool must not:

- block Episode-2 custody closeout;
- block AOV-0 implementation or prospective sealing;
- populate `VERTICAL-CUBE-SLICE-V0` without a separate data-authority gate;
- trigger a broad provider-acquisition programme;
- create a second research engine, dashboard, or manual-copy truth path;
- support alpha, PIT, entitlement, or no-login claims before direct verification.

## First future action

When AOV-2 or the Identification Readiness Probe is explicitly opened, run one small source-readiness batch against the six-name preferred shortlist and return only per-source gate evidence. Do not connect or test the full inventory at once.
