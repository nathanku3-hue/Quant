# GodView Signal Freshness Policy

Status: Phase 65 G7.1B policy draft
Date: 2026-05-09
Authority: architecture policy only, not runtime implementation

## Purpose

GodView cannot mix daily prices, twice-monthly short interest, weekly CFTC positioning, filing-lagged ownership, intraday options, and manual research notes without visible freshness labels.

This policy defines future freshness buckets. It does not implement a freshness engine.

## Required Time Fields

Every future signal needs:

```text
asof_ts
captured_at_utc
freshness
latency
provider
provider_feed
manifest_uri
```

`asof_ts` means the time/date the source observation describes.

`captured_at_utc` means when Terminal Zero captured or wrote the observation.

`latency` means the gap between source observation and user-visible availability.

## Freshness Buckets

| Bucket | Intended use | Example families | Dashboard wording |
| --- | --- | --- | --- |
| Intraday | Behavior changes within the trading day. | options tape, options whales, microstructure | `intraday` |
| Daily | End-of-day or daily refreshed context. | price/volume, OI/volume, sector/regime proxies, ETF flows | `daily` |
| Weekly | Weekly official reporting. | CFTC COT/TFF | `weekly` |
| Twice monthly | Official semi-monthly reporting. | FINRA short interest | `twice_monthly` |
| Filing-lagged | Public filings with statutory or practical delay. | 13F/13D/13G/Form 4 | `filing_lagged` |
| Manual | Human/Codex/Chrome capture; freshness depends on source note. | thesis docs, narrative notes | `manual` |
| Delayed vendor/public | Reported with explicit delay. | ATS/OTC, some options/public feeds | `delayed` |
| Unknown/stale | Missing, unmanifested, or beyond policy threshold. | any family | `stale_or_unknown` |

## Family Freshness Defaults

| Signal family | Default freshness | Required label before dashboard use |
| --- | --- | --- |
| Canonical price/volume | Daily | `observed_daily` |
| Supercycle thesis docs | Manual/daily | `manual_research_asof_<date>` |
| IV / options tape | Intraday/daily | `licensed_options_asof_<ts>` |
| Options OI / volume | Daily | `options_oi_daily` |
| Options whales | Intraday/daily | `options_trade_observed_intent_estimated` |
| Gamma / dealer map | Daily/intraday | `estimated_gamma_asof_<ts>` |
| Short interest | Twice monthly | `finra_short_interest_lagged` |
| CTA / systematic pressure | Weekly/daily | `cot_weekly_proxy_daily` |
| Ownership whales | Filing-lagged | `filing_lagged` |
| ETF/passive flows | Daily/weekly | `vendor_flow_daily_or_weekly` |
| Dark pool / block | Delayed/intraday vendor | `ats_block_delayed_or_vendor_intraday` |
| Microstructure | Intraday | `licensed_microstructure_intraday` |
| News/narrative | Real-time/manual | `manual_or_vendor_news_asof_<ts>` |

## Staleness Guardrail

Future dashboard behavior must never silently promote stale context into a fresh signal.

Minimum future rule:

```text
freshness_state = fresh | delayed | stale | unknown
```

If `freshness_state` is `stale` or `unknown`, allowed use should degrade to research context only unless a later source policy explicitly permits another use.

## G7.1B Boundary

This file does not create `signals/freshness_policy.py`, dashboard badges, provider adapters, alert logic, or state-machine transitions.
