# FRED / Ken French Public Provider Fixture Plan

Status: Phase 65 G7.1G fixture materialized; provider work held
Date: 2026-05-09
Authority: static fixture validation plan only; no live provider

## Purpose

Define and record the tiny FRED / Ken French public-source fixture proof created in G7.1G.

The fixture proves governance mechanics and macro/factor labels, not market edge. It is deliberately too small to act as a data lake, factor model, macro regime model, signal scorer, or state-machine input.

## Fixture Artifacts

| Artifact | Rows | Dates | Source | Manifest |
| --- | ---: | --- | --- | --- |
| `data/fixtures/fred/fred_macro_tiny.csv` | 9 | `2024-01-01` to `2024-03-01` | FRED graph CSV static capture | `data/fixtures/fred/fred_macro_tiny.manifest.json` |
| `data/fixtures/ken_french/ken_french_factor_tiny.csv` | 12 | `1926-07-31` to `1926-10-31` | Kenneth French F-F Research Data Factors CSV static capture | `data/fixtures/ken_french/ken_french_factor_tiny.manifest.json` |

## FRED Data Shape

Columns:

```text
series_id
date
value
realtime_start
realtime_end
asof_ts
official_source_row_locator
```

Series:

- `M2SL`: liquidity / money supply;
- `DGS10`: rates / yields;
- `BAA10Y`: credit spread.

Primary key:

```text
(series_id, date, realtime_start, realtime_end)
```

## Ken French Data Shape

Columns:

```text
dataset_id
date
factor_name
factor_return
frequency
asof_ts
official_source_row_locator
```

Dataset:

```text
fama_french_3_factors_monthly
```

Factors:

- `Mkt-RF`;
- `SMB`;
- `HML`.

Primary key:

```text
(dataset_id, date, factor_name)
```

## Validation Plan

Implemented static checks:

- manifest exists;
- `sha256` matches artifact bytes;
- manifest `row_count` matches physical rows;
- manifest `date_range` matches physical rows;
- date fields parse;
- `series_id` / `dataset_id` are present;
- numeric values are finite;
- duplicate primary keys are rejected;
- `source_quality` is present;
- `observed_estimated_or_inferred` equals `observed`;
- `allowed_use` and `forbidden_use` are present;
- FRED live API-key requirement is labeled `true_for_live_api` without using a key;
- no macro or factor score field is emitted.

Test artifact:

```text
tests/test_g7_1g_fred_ken_french_tiny_fixture.py
```

## What This Unlocks

If G7.1G passes, the repo has four public-source proof pillars:

```text
SEC: thesis / filings / ownership evidence
FINRA: short-interest / squeeze-base evidence
CFTC: futures positioning / systematic-regime context
FRED + Ken French: macro liquidity / rates / credit / factor-regime context
```

Recommended next sequence:

```text
G7.2 - Unified Opportunity State Machine
```

State-machine work should remain held until G7.2 is separately approved.

## Explicit Holds

Held after G7.1G:

- G7.2 state machine;
- FRED provider;
- Ken French provider;
- live API calls;
- API key handling;
- bulk downloads;
- macro regime score;
- factor regime score;
- signal ranking;
- candidate generation;
- search;
- backtest;
- replay;
- dashboard runtime behavior;
- alerts;
- broker calls.
