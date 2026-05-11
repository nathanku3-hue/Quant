# FINRA Short Interest Tiny Fixture Policy

Status: Phase 65 G7.1E approved tiny fixture proof
Date: 2026-05-10
Authority: one static FINRA short-interest fixture proof only; no live provider
RoundID: PH65_G7_1E_FINRA_TINY_FIXTURE_20260509
ScopeID: PH65_G7_1E_FIXTURE_ONLY

## Purpose

G7.1E proves that Terminal Zero can carry one official public FINRA short-interest source into the governance model as a tiny static fixture with manifest identity, row checks, delayed-data labels, and no uncontrolled provider expansion.

This is not a full FINRA ingestion layer. It is not a live FINRA provider, Reg SHO provider, OTC/ATS provider, squeeze score, ranking signal, state-machine input, dashboard runtime feature, alert input, broker input, paper-trading input, or promotion authority.

## Approved Source

Approved source:

```text
FINRA Equity Short Interest
```

Why FINRA short interest next:

- official observed short-interest positioning source;
- high value for GodView market-behavior context;
- natural next proof after SEC because it grounds the slow short-crowding / squeeze-base layer;
- interpretation risk can be controlled by explicit delayed-data and non-signal labels.

Official FINRA pages state that FINRA publishes short-interest reports collected from broker-dealers for exchange-listed and OTC equity securities. FINRA Rule 4560 requires members to report short positions in OTC equity securities to FINRA. FINRA short interest is available by settlement date and downloadable files are available for the public catalog.

## Fixture Boundary

Approved:

- one source: FINRA Equity Short Interest;
- one settlement date: `2026-04-15`;
- three tickers: `AAPL`, `TSLA`, `GME`;
- one static CSV fixture;
- one sidecar manifest;
- fixture validation tests only.

Forbidden:

- FINRA provider class;
- live FINRA API call;
- bulk download;
- Reg SHO ingestion;
- OTC / ATS ingestion;
- squeeze score;
- short-squeeze ranking;
- dashboard runtime behavior;
- alerts;
- broker calls;
- candidate generation;
- G7.2 state machine.

## Source-Use Rule

FINRA short interest is a delayed positioning signal:

```text
Short interest = slow squeeze base.
Reg SHO short-sale volume = daily trading context.
Neither one alone = squeeze signal.
```

Required interpretation:

```text
FINRA short interest may say "short base exists."
It may not say "forced covering is happening now."
```

## Allowed Use

Allowed use:

- squeeze base context;
- positioning context;
- GodView market behavior input;
- delayed short-crowding evidence.

## Forbidden Use

Forbidden use:

- real-time squeeze trigger;
- buy/sell signal;
- standalone ranking factor;
- alert emission;
- canonical alpha evidence without additional validation.

## Manifest Contract

The FINRA short-interest fixture manifest must include:

```text
source_name = FINRA Equity Short Interest
source_quality = public_official_observed
provider = finra
provider_feed = equity_short_interest
dataset_type = short_interest
observed_estimated_or_inferred = observed
settlement_date
publication_or_retrieved_at
asof_ts
ticker
issue_name
short_interest
average_daily_volume
days_to_cover
row_count
date_range
sha256
schema_version
official_source_url
license_or_terms_note
freshness_policy = twice_monthly / delayed
allowed_use
forbidden_use
```

Policy invariant:

```text
g7_1e_finra_fixture_valid = static_fixture
  and dataset_type == short_interest
  and manifest_hash_matches
  and row_count_reconciles
  and settlement_date_parses
  and ticker_present
  and short_interest_is_finite_non_negative
  and average_daily_volume_is_finite_non_negative
  and days_to_cover_is_finite_non_negative_when_present
  and duplicate_primary_keys == 0
  and observed_estimated_or_inferred == observed
  and reg_sho_fields_present == false
  and provider_code_added == false
  and squeeze_score_added == false
  and state_machine_added == false
```

## Source Evidence

- FINRA Equity Short Interest data: `https://www.finra.org/finra-data/browse-catalog/equity-short-interest/data`
- FINRA Equity Short Interest files: `https://www.finra.org/finra-data/browse-catalog/equity-short-interest/files`
- FINRA Daily Short Sale Volume Files: `https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files`
- FINRA Short Sale Volume notes: `https://www.finra.org/finra-data/browse-catalog/short-sale-volume`
- FINRA terms of use: `https://www.finra.org/terms-of-use`
- FINRA developer Query API docs: `https://developer.finra.org/products/query-api`

## Verdict

G7.1E FINRA short-interest fixture policy is approved for one static fixture proof and blocks all provider/runtime expansion.
