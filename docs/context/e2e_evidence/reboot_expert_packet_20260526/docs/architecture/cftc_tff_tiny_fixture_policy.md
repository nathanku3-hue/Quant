# CFTC TFF Tiny Fixture Policy

Status: Phase 65 G7.1F approved tiny fixture proof
Date: 2026-05-10
Authority: one static CFTC COT/TFF fixture proof only; no live provider
RoundID: PH65_G7_1F_CFTC_TFF_TINY_FIXTURE_20260509
ScopeID: PH65_G7_1F_FIXTURE_ONLY

## Purpose

G7.1F proves that Terminal Zero can carry one official public CFTC Commitments of Traders / Traders in Financial Futures source into the governance model as a tiny static fixture with manifest identity, row checks, weekly-positioning labels, and no uncontrolled provider expansion.

This is not a full CFTC ingestion layer. It is not a live CFTC provider, CTA score, single-name CTA inference, state-machine input, ranking signal, dashboard runtime feature, alert input, broker input, paper-trading input, or promotion authority.

## Approved Source

Approved source:

```text
CFTC Commitments of Traders / Traders in Financial Futures
```

Why CFTC TFF next:

- official observed futures-positioning source;
- high value for GodView broad market-behavior and macro/regime context;
- natural next proof after SEC filings/facts and FINRA short-interest governance;
- interpretation risk can be controlled by explicit broad-regime and non-single-name labels.

CFTC COT reports publish weekly open-interest breakdowns for markets where 20 or more traders meet CFTC reporting levels. CFTC states that futures-only and futures-and-options-combined reports are usually released on Friday at 3:30 p.m. Eastern Time and cover Tuesday positions. The Traders in Financial Futures report breaks financial futures positions into categories including Dealer/Intermediary, Asset Manager/Institutional, Leveraged Funds, and Other Reportables.

## Fixture Boundary

Approved:

- one source: CFTC COT/TFF;
- one report date: `2026-05-08`;
- one as-of position date: `2026-05-05`;
- two broad financial futures markets: `E-Mini S&P 500`, `UST 10Y Note`;
- four TFF trader categories;
- one static CSV fixture;
- one sidecar manifest;
- fixture validation tests only.

Forbidden:

- CFTC provider class;
- live CFTC API call;
- bulk download;
- CTA score;
- single-name CTA inference;
- G7.2 state machine;
- signal ranking;
- dashboard runtime behavior;
- alerts;
- broker calls;
- candidate generation.

## Source-Use Rule

CFTC TFF is a broad futures-positioning and regime context source:

```text
CFTC TFF = broad regime / systematic-positioning context.
CFTC TFF != single-name CTA buying evidence.
CFTC TFF alone != buy/sell/hold state.
```

Required interpretation:

```text
CFTC TFF may say "systematic/regime positioning context is supportive or hostile."
It may not say "CTAs are buying this stock today."
```

## Allowed Use

Allowed use:

- broad futures-positioning context;
- macro/regime support;
- CTA/systematic-pressure proxy;
- GodView market-behavior context.

## Forbidden Use

Forbidden use:

- direct single-name CTA buying evidence;
- buy/sell signal;
- standalone ranking factor;
- alert emission;
- alpha evidence without validation.

## Manifest Contract

The CFTC TFF fixture manifest must include:

```text
source_name = CFTC Commitments of Traders / TFF
source_quality = public_official_observed
provider = cftc
provider_feed = cot_tff
dataset_type = futures_positioning
observed_estimated_or_inferred = observed
report_date
asof_position_date
publication_or_retrieved_at
market_name
contract_market_code
trader_category
long_positions
short_positions
spreading_positions
open_interest
row_count
date_range
sha256
schema_version
official_source_url
license_or_terms_note
freshness_policy = weekly / Friday release / Tuesday positions
allowed_use
forbidden_use
```

Policy invariant:

```text
g7_1f_cftc_fixture_valid = static_fixture
  and dataset_type == futures_positioning
  and manifest_hash_matches
  and row_count_reconciles
  and report_date_parses
  and asof_position_date_parses
  and market_name_present
  and contract_market_code_present
  and trader_category_in_allowed_categories
  and long_positions_is_finite_non_negative
  and short_positions_is_finite_non_negative
  and spreading_positions_is_finite_non_negative_when_present
  and open_interest_is_finite_non_negative
  and duplicate_primary_keys == 0
  and observed_estimated_or_inferred == observed
  and single_name_inference_forbidden == true
  and provider_code_added == false
  and cta_score_added == false
  and state_machine_added == false
```

## Source Evidence

- CFTC Commitments of Traders landing page: `https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm`
- CFTC TFF current futures-only report: `https://www.cftc.gov/dea/futures/financial_lf.htm`
- CFTC TFF explanatory notes: `https://www.cftc.gov/idc/groups/public/@commitmentsoftraders/documents/file/tfmexplanatorynotes.pdf`
- OFR TFF dataset notes: `https://www.financialresearch.gov/hedge-fund-monitor/datasets/tff/`

## Verdict

G7.1F CFTC TFF fixture policy is approved for one static fixture proof and blocks all provider/runtime/scoring/state-machine expansion.
