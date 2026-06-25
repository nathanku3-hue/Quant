# GodView Provider Roadmap

Status: Phase 65 G7.1B provider roadmap
Date: 2026-05-09
Authority: future architecture targets only

## Purpose

This document names future provider ports and sequencing for GodView. It intentionally does not add provider files, ingestion jobs, credentials, schemas, runtime behavior, or dashboard changes.

## Existing Provider Foundation

Current repo surfaces:

- `data/providers/base.py`: quote snapshot metadata and `MarketDataPort` protocol.
- `data/providers/registry.py`: provider factory for Yahoo and Alpaca.
- `data/providers/yahoo_provider.py`: non-canonical convenience market-data source.
- `data/providers/alpaca_provider.py`: operational quote source through the existing broker API.
- `data/provenance.py`: source-quality, manifest, atomic JSON write, quote/alert validation.

These are useful patterns. They do not cover GodView provider needs.

## Future Provider Ports

Do not implement these in G7.1B:

```text
data/providers/options_provider.py
data/providers/short_interest_provider.py
data/providers/cftc_provider.py
data/providers/sec_filings_provider.py
data/providers/etf_flow_provider.py
data/providers/ats_block_provider.py
data/providers/news_research_provider.py
```

## Provider Responsibilities

| Future provider | Signal families | Minimum responsibility | License/source risk | Priority |
| --- | --- | --- | --- | --- |
| `options_provider.py` | IV, options tape, OI/volume, options whales, gamma prerequisites | Normalize options quotes/trades/chains/OI with as-of, feed, and license metadata | High; OPRA/vendor licensing | P1 |
| `short_interest_provider.py` | Short interest, squeeze base | Capture FINRA short-interest observations with reporting-period lag | Medium; official but lagged | P1 |
| `cftc_provider.py` | CTA/systematic pressure | Capture COT/TFF positioning with report date and as-of Tuesday date | Medium; broad futures context only | P1 |
| `sec_filings_provider.py` | Ownership whales | Capture 13F/13D/13G/Form 4 with filing date, period date, entity mapping | Medium; lag/entity mapping | P1 |
| `etf_flow_provider.py` | ETF/passive flows, sector rotation | Capture holdings/flow/creation-redemption context | Medium-high; vendor likely | P2 |
| `ats_block_provider.py` | Dark-pool/block | Capture ATS/OTC/block context with venue and delay labels | Medium-high; interpretation risk | P2 |
| `news_research_provider.py` | News/narrative, thesis evidence | Convert approved manual/vendor research captures into manifests/notes | Variable; must be policy-bound | P2 |

## Future Port Contract

Each future provider should emit records that can be wrapped with:

```text
provider
provider_feed
source_quality
license_scope
asof_ts
captured_at_utc
freshness
latency
observed_vs_estimated
manifest_uri
raw_locator
```

Provider records must not emit dashboard states, ranks, alerts, broker actions, or promotion verdicts.

## Sequencing

Step 1 - Source policy before code:

- define source_quality eligibility;
- define allowed and forbidden use per provider;
- define freshness thresholds and as-of semantics;
- define manifest/retention requirements;
- define license constraints.

Step 2 - Provider selection:

- choose official/public source when sufficient;
- choose licensed vendor only where official data is delayed, fragmented, or unusable for the product job;
- reject sources that cannot provide as-of, license, or manifest evidence.

Step 3 - Narrow adapter proof:

- one provider;
- one family;
- one tiny fixture;
- no signal ranking;
- no candidate generation;
- no dashboard runtime behavior.

Step 4 - Source-quality review:

- validate freshness, row counts, null keys, duplicates, license metadata, and observed-vs-estimated labels;
- record rollback path and out-of-scope risks.

## Current Non-Implementation Lock

G7.1B creates no files under `data/providers/` and no `signals/` package. Future provider paths remain planning targets only.

## Open Upgrade Debt

- yfinance migration remains separate from G7.1B.
- stale S&P sidecar freshness remains separate from G7.1B.
- broad workspace `compileall .` null-byte / ACL traversal debt remains workspace hygiene, not GodView provider work.
