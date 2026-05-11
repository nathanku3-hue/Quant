# Data and Infrastructure Gap Assessment for GodView

Status: Phase 65 G7.1A gap assessment
Date: 2026-05-09
Authority: G7.1A starter docs / product-spec rewrite

## Summary

Current infrastructure is enough for the governance path. It is not yet enough for full GodView.

This is expected. G7.1A documents the gap; it does not implement provider layers.

## Current Readiness

Ready now:

- canonical daily price governance;
- manifest/provenance checks;
- Candidate Registry;
- V1/V2 mechanical replay discipline;
- dashboard smoke discipline;
- minimal validation lab;
- paper-alert readiness foundations.

Not ready for full GodView:

- options/IV data;
- options open interest and volume;
- whale options flow;
- gamma/dealer estimates;
- short interest and borrow/stock-loan;
- CFTC COT/TFF positioning;
- SEC 13F/13D/Form 4 ownership intelligence;
- ETF holdings and flows;
- dark-pool / ATS / block activity;
- microstructure / order book;
- news and narrative velocity.

## Readiness Table

| Signal family | Current readiness | Upgrade needed |
| --- | --- | --- |
| Daily canonical price/volume | Ready | Continue manifest governance |
| Supercycle thesis docs | Partially ready | Add research memo / thesis-card schema |
| IV / options tape | Not ready | OPRA/options provider port |
| Options open interest / volume | Not ready | OCC or vendor-backed ingestion |
| Options whales | Not ready | Options tape + classification provider |
| Gamma/dealer map | Not ready | Options chain + OI + model-estimated layer |
| Short interest | Not ready | FINRA short-interest provider |
| Borrow / stock loan | Not ready | Stock-loan or borrow-rate provider |
| CTA / futures positioning | Not ready | CFTC COT/TFF ingestion |
| Whale ownership | Not ready | SEC 13F/13D/Form 4 ingestion |
| ETF/passive flows | Not ready | ETF holdings/flow provider |
| Dark pool/block | Not ready | FINRA ATS/OTC or vendor feed |
| Microstructure/order book | Not ready | TAQ/TotalView/vendor feed |
| News/narrative | Not ready | Browser/research capture + source-quality tagging |

## Future Provider Files

Do not build these in G7.1A. They are future placeholders for planning:

```text
data/providers/options_provider.py
data/providers/short_interest_provider.py
data/providers/cftc_provider.py
data/providers/sec_filings_provider.py
data/providers/etf_flow_provider.py
data/providers/news_research_provider.py
```

## Future Signal Policy Files

Do not build these in G7.1A. They are future placeholders for planning:

```text
signals/source_registry.py
signals/freshness_policy.py
signals/confidence_policy.py
signals/godview_state_machine.py
```

## Source Notes

For later provider design:

- OPRA is the relevant official consolidated source for listed-options last-sale and quotation information. This matters for IV, options whales, and gamma inputs.
- OCC publishes options volume and open-interest reports. These are useful for the options behavior layer.
- FINRA short interest is useful for squeeze context.
- CFTC COT/TFF reports provide futures-positioning context for CTA/systematic-flow proxies.
- SEC 13F/13D/Form 4 filings are useful for ownership-whale context, with filing-lag disclosure.

These notes are architecture anchors only. They do not authorize ingestion.

## Observed Facts vs Vendor/Model Estimates

Future GodView data must separate:

- observed facts: official reports, exchange prints, filings, published price/volume/OI fields;
- vendor transforms: unusual-options flags, ETF flow fields, venue classifications;
- model estimates: IV, dealer gamma, CTA pressure, squeeze probability, narrative velocity.

The product must show this distinction to the operator.

## Required Future Signal Metadata

Every future signal must carry:

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

## G7.1A Boundary

No provider files, ingestion jobs, data artifacts, runtime dashboard behavior, alerts, broker calls, backtests, replay runs, proxy runs, search, ranking, or candidate generation are added by this assessment.
