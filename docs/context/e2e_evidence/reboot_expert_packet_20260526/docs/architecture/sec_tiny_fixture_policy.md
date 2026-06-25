# SEC Tiny Fixture Policy

Status: Phase 65 G7.1D approved tiny fixture proof
Date: 2026-05-09
Authority: one static SEC data.sec.gov fixture proof only; no live provider
RoundID: PH65_G7_1D_SEC_TINY_FIXTURE_20260509
ScopeID: PH65_G7_1D_FIXTURE_ONLY

## Purpose

G7.1D proves that Terminal Zero can carry one official public source into the governance model as a tiny static fixture with source rights, manifest identity, row checks, date checks, and no uncontrolled provider expansion.

This is not a full SEC ingestion layer. It is not a live provider, downloader, source registry, signal score, state-machine input, candidate-generation input, alert input, or broker input.

## Approved Source

Approved first source:

```text
SEC EDGAR / data.sec.gov
```

Why SEC first:

- official public source;
- no authentication or API key required for the reviewed JSON endpoints;
- strong CIK and accession-number identity;
- direct fit for Supercycle thesis, ownership, and fundamentals evidence later;
- lower interpretation risk than FINRA short interest for the first proof.

SEC public docs describe `data.sec.gov` as RESTful JSON APIs for submissions and XBRL company facts. The reviewed endpoints used here are:

- `https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json`
- `https://data.sec.gov/submissions/CIK0000320193.json`

Automated access must follow SEC fair-access guidance. This proof used two one-company requests and stores only static tiny fixture files.

## Fixture Boundary

Approved:

- one company: Apple Inc. / AAPL / CIK `0000320193`;
- one companyfacts tiny sample with two facts;
- one submissions tiny sample with five filing metadata rows;
- sidecar manifests with source rights, raw locators, as-of timestamps, hashes, row counts, and allowed/forbidden use;
- fixture validation tests only.

Forbidden:

- live SEC provider class;
- broad downloader;
- scheduled ingestion;
- canonical lake writes;
- ticker universe expansion;
- Form 4 / 13F / 13D / 13G strategy logic;
- GodView scoring;
- candidate generation;
- state machine;
- dashboard runtime behavior;
- alerts;
- broker calls.

## Manifest Contract

Each SEC tiny fixture manifest must include:

```text
source_name = SEC EDGAR / data.sec.gov
source_quality = public_official_observed
provider = sec
provider_feed = data.sec.gov
api_endpoint
retrieved_at
asof_ts
entity_key_type = CIK
cik
ticker_if_known
form_types
row_count
date_range
sha256
schema_version
license_or_terms_note
rate_limit_policy
allowed_use
forbidden_use
observed_estimated_or_inferred = observed
```

Policy invariant:

```text
g7_1d_sec_fixture_valid = static_fixture
  and manifest_hash_matches
  and row_count_reconciles
  and cik_is_10_digit_string
  and date_fields_parse
  and duplicate_primary_keys == 0
  and numeric_fact_values_are_finite
  and observed_estimated_or_inferred == observed
  and provider_code_added == false
  and ingestion_added == false
```

## Allowed Use

Allowed use:

```text
Static fixture validation, provenance, schema, row-count, date, and source-rights proof only.
```

Forbidden use:

```text
No live provider, bulk download, ingestion, canonical lake writes, signal scoring,
candidate generation, alerts, broker calls, or state-machine consumption.
```

## Source Evidence

- SEC EDGAR API documentation: `https://www.sec.gov/search-filings/edgar-application-programming-interfaces`
- SEC developer/fair access guidance: `https://www.sec.gov/about/developer-resources`
- SEC EDGAR data access: `https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data`

## Verdict

G7.1D SEC fixture policy is approved for one static fixture proof and blocks all provider/runtime expansion.
