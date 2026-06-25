# FRED / Ken French Tiny Fixture Policy

Status: Phase 65 G7.1G approved tiny fixture proof
Date: 2026-05-09
Authority: static FRED / Ken French fixture proof only; no live provider
RoundID: PH65_G7_1G_FRED_KEN_FRENCH_TINY_FIXTURE_20260509
ScopeID: PH65_G7_1G_FIXTURE_ONLY

## Purpose

G7.1G proves that Terminal Zero can carry tiny public macro and factor context fixtures with manifest identity, row checks, source labels, and explicit no-score boundaries.

This is not a FRED provider, Ken French provider, live API integration, macro regime score, factor regime score, Unified Opportunity State Machine input, ranking signal, dashboard runtime feature, alert input, broker input, paper-trading input, or promotion authority.

## Approved Sources

Approved sources:

```text
FRED / ALFRED
Kenneth French Data Library
```

Why these sources:

- FRED / ALFRED supplies official public macro series and supports historical real-time-vintage concepts that matter for avoiding hindsight leakage in future provider work.
- The Kenneth French Data Library supplies public research factor-return datasets widely used for benchmark and factor context.
- Together they become the fourth public-source fixture pillar after SEC, FINRA, and CFTC.

## Fixture Boundary

Approved:

- one static FRED CSV fixture;
- three FRED macro series: `DGS10`, `M2SL`, `BAA10Y`;
- three dates per FRED series;
- one static Ken French CSV fixture;
- one Ken French dataset: `fama_french_3_factors_monthly`;
- four monthly dates, long-form factor rows for `Mkt-RF`, `SMB`, and `HML`;
- one sidecar manifest for each fixture;
- fixture validation tests only.

Forbidden:

- FRED provider class;
- Ken French provider class;
- live API call;
- API key handling;
- bulk download;
- macro regime score;
- factor regime score;
- G7.2 state machine;
- signal ranking;
- dashboard runtime behavior;
- alerts;
- broker calls;
- candidate generation.

## Source-Use Rule

FRED and Ken French are context sources:

```text
FRED = macro liquidity / rates / credit context.
Ken French = factor-return / benchmark context.
FRED + Ken French != macro score, factor score, alpha proof, ranking signal, or alert.
```

Required interpretation:

```text
FRED fixture may support macro context and future regime panels.
It may not produce a macro regime score in this phase.
It may not use live API keys in this phase.

Ken French fixture may support factor/regime context and later benchmark comparison.
It may not be used to claim alpha or rank candidates in this phase.
```

## Manifest Contract

The FRED fixture manifest must include:

```text
source_name = FRED / ALFRED
source_quality = public_official_observed
provider = fred
provider_feed = fred_or_alfred
dataset_type = macro_series
observed_estimated_or_inferred = observed
series_id
date
value
realtime_start
realtime_end
retrieved_at_or_static_fixture_created_at
asof_ts
row_count
date_range
sha256
schema_version
official_source_url
terms_note
api_key_required = true_for_live_api
allowed_use
forbidden_use
```

The Ken French fixture manifest must include:

```text
source_name = Kenneth French Data Library
source_quality = public_research_observed
provider = ken_french
provider_feed = data_library
dataset_type = factor_returns
observed_estimated_or_inferred = observed
dataset_id
date
factor_name
factor_return
frequency
retrieved_at_or_static_fixture_created_at
asof_ts
row_count
date_range
sha256
schema_version
official_source_url
terms_note
allowed_use
forbidden_use
```

Policy invariant:

```text
g7_1g_macro_factor_fixture_valid = static_fixture
  and fred_manifest_hash_matches
  and ken_french_manifest_hash_matches
  and row_count_reconciles
  and date_range_reconciles
  and date_fields_parse
  and series_id_present
  and dataset_id_present
  and numeric_values_are_finite
  and duplicate_primary_keys == 0
  and observed_estimated_or_inferred == observed
  and allowed_use_present
  and forbidden_use_present
  and live_api_key_used == false
  and macro_score_emitted == false
  and factor_score_emitted == false
  and provider_code_added == false
  and state_machine_added == false
```

## Source Evidence

- FRED API documentation: `https://fred.stlouisfed.org/docs/api/fred/`
- FRED API terms: `https://fred.stlouisfed.org/docs/api/terms_of_use.html`
- FRED series CSV service used manually for fixture capture: `https://fred.stlouisfed.org/graph/fredgraph.csv`
- Kenneth French Data Library: `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html`

## Verdict

G7.1G FRED / Ken French fixture policy is approved for tiny static fixture proof and blocks all provider/runtime/scoring/state-machine expansion.
