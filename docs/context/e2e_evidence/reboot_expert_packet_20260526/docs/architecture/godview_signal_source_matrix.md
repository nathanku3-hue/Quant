# GodView Signal Source Matrix

Status: Phase 65 G7.1B source matrix
Date: 2026-05-09
Authority: G7.1B docs + architecture + source mapping only

## Purpose

This matrix translates GodView signal families into source needs, readiness, trust, and allowed use. It is not a signal registry and does not authorize ingestion.

## Signal Metadata Contract

Every future GodView signal must carry:

```text
signal_id
signal_family
ticker_or_theme
source_quality
provider
provider_feed
observed_vs_estimated
freshness
latency
asof_ts
confidence
allowed_use
forbidden_use
manifest_uri
```

Field rules:

- `signal_id`: stable deterministic identifier for the signal observation.
- `signal_family`: one of the approved GodView families.
- `ticker_or_theme`: security ticker, basket, sector, commodity, or thesis theme.
- `source_quality`: canonical, operational, non_canonical, or rejected until a later source policy expands the enum.
- `provider` and `provider_feed`: named source authority/vendor/feed.
- `observed_vs_estimated`: `observed`, `estimated`, or `inferred`.
- `freshness`: human-readable policy bucket such as daily, weekly, filing-lagged, delayed, intraday, or manual.
- `latency`: expected reporting lag or observed capture lag.
- `asof_ts`: timestamp/date the source observation describes, not just ingestion time.
- `confidence`: source-confidence tier after policy approval.
- `allowed_use`: explicit list of permitted downstream uses.
- `forbidden_use`: explicit list of blocked uses.
- `manifest_uri`: manifest/evidence locator for source artifact or research note.

## Source Matrix

| Signal family | Primary source candidate | Current repo support | Observed / estimated / inferred | Freshness | Allowed use before future approval | Forbidden use |
| --- | --- | --- | --- | --- | --- | --- |
| Canonical price/volume | Existing Tier 0 lake / canonical Parquet manifests | Ready | Observed | Daily | Governance context, trend context, readiness proof | Live order trigger without later approval |
| Supercycle thesis docs | Manual research memo / thesis card | Partial | Inferred from sourced research | Manual/daily | Human review, architecture planning | Alpha evidence without source policy |
| Sector/regime price proxies | Existing canonical prices, sector map, regime artifacts | Ready with existing data | Inferred | Daily | Broad market context | Single-name flow proof |
| IV / volatility surface | OPRA/options vendor | Not ready | Quote/print observed; IV estimated | Intraday/daily | None beyond planning | Dashboard signal until provider/source policy |
| Options tape | OPRA/options vendor | Not ready | Observed if licensed | Intraday/daily | None beyond planning | Whale intent or gamma proof without policy |
| Options OI / volume | OCC/vendor | Not ready | Observed/reporting field if sourced | Daily | None beyond planning | Signal approval without manifest/source policy |
| Options whales | Options tape + classifier | Not ready | Observed print plus estimated intent/classification | Intraday/daily | None beyond planning | Automatic bullish/bearish interpretation |
| Gamma / dealer map | Options chain/OI + model | Not ready | Estimated | Daily/intraday | None beyond planning | Treating model output as observed fact |
| Short interest | FINRA | Not ready | Observed official report | Twice monthly | Future squeeze-base context | Real-time squeeze timing |
| Borrow / stock loan | Licensed borrow/stock-loan provider | Not ready | Observed/vendor field | Daily/intraday vendor | None beyond planning | Canonical evidence without license/manifest |
| CTA / systematic pressure | CFTC COT/TFF + trend proxies | Not ready | Official reports observed; single-name CTA pressure estimated | Weekly/daily | Future broad flow context | Single-name real-time flow proof |
| Ownership whales | SEC 13F/13D/13G/Form 4 | Not ready | Observed filing | Filing-lagged | Future sponsorship context | Real-time accumulation proof |
| ETF/passive flows | ETF holdings/flow provider | Not ready | Vendor observed/derived fields | Daily/weekly | Future passive support/pressure context | Unlicensed canonical flow evidence |
| Dark pool / block | FINRA ATS/OTC or vendor | Not ready | Reported prints observed; accumulation inferred | Delayed/intraday vendor | Future sponsorship/liquidity context | Simple accumulation/distribution proof |
| Microstructure | TAQ/TotalView/exchange/vendor feed | Not ready | Observed if licensed | Intraday | Future execution-quality context | Thesis approval or signal ranking |
| News/narrative | Codex/Chrome research capture or news vendor | Not ready | Inferred | Real-time/manual | Research notes and docs | Alpha evidence, alerts, scraping without policy |

## Trust Levels

| Trust level | Meaning | Examples |
| --- | --- | --- |
| High | Direct official/licensed observation with manifest and clear as-of semantics. | Canonical prices, licensed options prints, SEC filings after manifesting. |
| Medium-high | Official/observed but lagged or entity-mapped. | FINRA short interest, CFTC COT/TFF, 13F/13D/Form 4. |
| Medium | Vendor-derived, delayed, model-assisted, or context-only. | ETF flows, ATS aggregates, sector/regime proxies. |
| Variable | Manual/narrative capture with source-quality spread. | News/narrative, thesis memo evidence. |
| Rejected | No approved source, stale, unlicensed, or unmanifested. | Scraped unapproved feeds, unlabeled web notes, unvetted social posts. |

## Priority Bands

P0:

- canonical price/volume;
- thesis docs and thesis-card source policy;
- source metadata contract;
- freshness and observed-vs-estimated labeling.

P1:

- options/IV/OI/tape foundation;
- FINRA short interest;
- CFTC COT/TFF;
- SEC filings;
- gamma/dealer estimate policy after options foundations.

P2:

- ETF/passive flows;
- dark-pool/block context;
- news/narrative capture;
- borrow/stock-loan if squeeze context becomes product-critical.

P3:

- TAQ/order-book microstructure for execution-quality and liquidity context.

## Current G7.1B Verdict

The matrix supports downstream planning. It does not create source approval, alpha evidence, state-machine transitions, ranking, alerts, provider ingestion, or broker actions.
