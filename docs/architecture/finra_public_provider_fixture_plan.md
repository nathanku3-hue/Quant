# FINRA Public Provider Fixture Plan

Status: Phase 65 G7.1E fixture materialized; provider work held
Date: 2026-05-10
Authority: static fixture validation plan only; no live provider

## Purpose

Define and record the one tiny FINRA short-interest public-source fixture proof created in G7.1E.

The fixture proves governance mechanics and delayed-data labeling, not market edge. It is deliberately too small to act as a data lake or squeeze model.

## Fixture Artifact

| Artifact | Rows | Settlement Date | Tickers | Source | Manifest |
| --- | ---: | --- | --- | --- | --- |
| `data/fixtures/finra/finra_short_interest_tiny.csv` | 3 | `2026-04-15` | `AAPL`, `TSLA`, `GME` | FINRA Equity Short Interest file `shrt20260415.csv` | `data/fixtures/finra/finra_short_interest_tiny.manifest.json` |

## Data Shape

Columns:

```text
settlement_date
ticker
issue_name
short_interest
average_daily_volume
days_to_cover
official_source_row_locator
```

Fixture rows:

- `AAPL`: short interest `134422787`, average daily volume `39674165`, days to cover `3.39`;
- `TSLA`: short interest `71106902`, average daily volume `70796421`, days to cover `1.00`;
- `GME`: short interest `61907606`, average daily volume `6610420`, days to cover `9.37`.

## Validation Plan

Implemented static checks:

- manifest exists;
- `sha256` matches artifact bytes;
- manifest `row_count` matches physical rows;
- `settlement_date` parses;
- ticker is present;
- `short_interest` is finite and non-negative;
- `average_daily_volume` is finite and non-negative;
- `days_to_cover` is finite and non-negative when present;
- duplicate primary key `(settlement_date, ticker)` is rejected;
- `source_quality` is present and equals `public_official_observed`;
- `allowed_use` and `forbidden_use` are present;
- `observed_estimated_or_inferred` equals `observed`;
- Reg SHO fields are not mixed into the short-interest fixture.

Test artifact:

```text
tests/test_g7_1e_finra_short_interest_tiny_fixture.py
```

## What This Unlocks

If G7.1E passes, the repo has a second official public source fixture integrated into governance discipline and the first GodView market-behavior base-layer fixture.

Recommended next sequence:

```text
G7.1F - CFTC COT/TFF tiny fixture
G7.1G - FRED/Ken French macro fixture
G7.2  - Unified Opportunity State Machine
```

State-machine work should remain held until SEC + FINRA are proven, unless PM explicitly accepts speed over data grounding.

## Explicit Holds

Held after G7.1E:

- G7.2 state machine;
- Reg SHO provider or fixture;
- ATS / OTC block provider or fixture;
- CFTC provider proof;
- FRED provider proof;
- options / IV / OPRA;
- signal scoring;
- candidate generation;
- dashboard runtime behavior;
- alerts;
- broker calls.
