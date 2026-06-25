# GodView Tiny Fixture Schema Plan

Status: Phase 65 G7.1C schema plan only
Date: 2026-05-09
Authority: schema design only; no data download, fixture materialization, provider implementation, or ingestion

## Purpose

Define tiny future fixture schemas for official/public GodView sources after source audit. This document is intentionally a plan only.

No datasets were downloaded. No fixture files were created. No provider code was added. No canonical data writes were performed.

## Shared Manifest Fields

Every future tiny fixture, if separately approved, must include a sidecar manifest with:

```text
fixture_id
source_name
provider
provider_feed
source_quality
license_scope
official_url_or_doc
raw_locator
retrieved_at_utc
asof_timestamp_field
date_range_min
date_range_max
row_count
column_count
schema_columns
primary_key
duplicate_key_count
null_key_count
sha256
created_by
created_for_round
allowed_use
forbidden_use
observed_estimated_or_inferred
notes
```

Manifest checks:

- `sha256` equals the computed file hash.
- `row_count` equals the physical row count.
- `schema_columns` equals the physical column order.
- `duplicate_key_count = 0`.
- `null_key_count = 0`.
- date fields parse as dates/timestamps.
- raw locator points to an official source path, not a vendor mirror.
- no credential-bearing URL is stored.

## SEC Fixture Schema

Planned columns:

```text
CIK
ticker
accession_number
form_type
filed_at
period_end
fact_name
value
unit
source_url
```

Primary key:

```text
(CIK, accession_number, form_type, fact_name, period_end, unit)
```

Date fields:

- `filed_at`
- `period_end`

Duplicate checks:

- reject duplicate primary keys;
- reject duplicate `(CIK, accession_number, source_url)` rows when `fact_name` is blank;
- require one and only one raw `source_url` per accession/fact row.

Row-count checks:

- tiny fixture target: 1-3 issuers, 1-2 filings each, <= 50 fact rows;
- `row_count > 0`;
- row count must match manifest.

Special policy:

- `CIK` is the stable entity key.
- `ticker` is convenience context and cannot replace CIK.
- Ownership filings such as 13F, Form 4, and 13D/G may require separate parser schemas later; this first schema is only a shared minimum row contract.

## FINRA Short Interest Fixture Schema

Planned columns:

```text
settlement_date
ticker
issue_name
short_interest
avg_daily_volume
days_to_cover
source_file
```

Primary key:

```text
(settlement_date, ticker)
```

Date fields:

- `settlement_date`

Duplicate checks:

- reject duplicate `(settlement_date, ticker)`;
- reject rows where `ticker` or `settlement_date` is missing;
- flag `days_to_cover` values that are placeholders or sentinel-like values for explicit review.

Row-count checks:

- tiny fixture target: 1 settlement date, 3-10 tickers;
- `row_count > 0`;
- manifest row count must match physical rows.

Special policy:

- This fixture is observed short interest only.
- It cannot include daily Reg SHO volume under a short-interest name.

## FINRA Reg SHO Fixture Schema

Planned columns:

```text
date
ticker
short_volume
short_exempt_volume
total_volume
market_center
```

Primary key:

```text
(date, ticker, market_center)
```

Date fields:

- `date`

Duplicate checks:

- reject duplicate `(date, ticker, market_center)`;
- reject rows where `short_volume + short_exempt_volume > total_volume` unless source guide explains the exception;
- require `market_center` to preserve TRF/ADF/ORF/consolidated context.

Row-count checks:

- tiny fixture target: 1 trade date, 3-10 tickers, one market-center source;
- `row_count > 0`;
- manifest row count must match physical rows.

Special policy:

- This fixture is observed short-sale-volume context only.
- It must not be labeled short interest.

## CFTC COT / TFF Fixture Schema

Planned columns:

```text
report_date
market_name
contract_market_code
trader_category
long
short
spreading
open_interest
```

Primary key:

```text
(report_date, contract_market_code, trader_category)
```

Date fields:

- `report_date`

Duplicate checks:

- reject duplicate `(report_date, contract_market_code, trader_category)`;
- reject missing `contract_market_code`;
- require non-negative numeric `long`, `short`, `spreading`, and `open_interest`.

Row-count checks:

- tiny fixture target: 1 report date, 1-3 markets, all required trader categories for those markets;
- `row_count > 0`;
- manifest row count must match physical rows.

Special policy:

```text
CFTC data may support broad regime / futures positioning.
It must not be used as direct single-name CTA buying evidence.
```

## FRED Fixture Schema

Planned columns:

```text
series_id
date
value
realtime_start
realtime_end
```

Primary key:

```text
(series_id, date, realtime_start, realtime_end)
```

Date fields:

- `date`
- `realtime_start`
- `realtime_end`

Duplicate checks:

- reject duplicate `(series_id, date, realtime_start, realtime_end)`;
- reject missing `series_id`;
- preserve missing values exactly as source null/missing tokens until a later normalization policy is approved.

Row-count checks:

- tiny fixture target: 1-3 series, 3-12 observations each;
- `row_count > 0`;
- manifest row count must match physical rows.

Special policy:

- Future FRED work requires API-key handling through environment variables only.
- No credential-bearing URL may appear in fixtures, manifests, logs, docs, or reports.
- Series-level third-party terms must be recorded before any fixture is materialized.

## Ken French Fixture Schema

Planned columns:

```text
dataset_id
date
factor_name
value
```

Primary key:

```text
(dataset_id, date, factor_name)
```

Date fields:

- `date`

Duplicate checks:

- reject duplicate `(dataset_id, date, factor_name)`;
- reject missing `dataset_id`, `date`, or `factor_name`;
- require numeric `value` after source missing-token policy is defined.

Row-count checks:

- tiny fixture target: 1 factor dataset, 3-12 dates, 3-6 factors;
- `row_count > 0`;
- manifest row count must match physical rows.

Special policy:

- Cite the Ken French Data Library in manifest notes.
- Record whether the dataset uses pre-2025 FIZ history, 2025+ CIZ methodology, or crosses that boundary.

## Cross-Fixture Validation Plan

Future approved tiny fixture validation must run:

```text
schema column equality
primary-key duplicate check
null-key check
date parse check
row-count equality against manifest
hash equality against manifest
raw-locator presence check
allowed/forbidden-use presence check
observed/estimated/inferred label check
secret-pattern scan
```

No validation command is implemented in G7.1C. This is a design contract for a later approved fixture/provider proof.

