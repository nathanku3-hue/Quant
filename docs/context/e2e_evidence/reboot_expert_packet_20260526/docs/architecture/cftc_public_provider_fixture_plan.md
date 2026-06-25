# CFTC Public Provider Fixture Plan

Status: Phase 65 G7.1F fixture materialized; provider work held
Date: 2026-05-10
Authority: static fixture validation plan only; no live provider

## Purpose

Define and record the one tiny CFTC COT/TFF public-source fixture proof created in G7.1F.

The fixture proves governance mechanics and broad-regime labeling, not market edge. It is deliberately too small to act as a data lake, CTA model, signal scorer, or state-machine input.

## Fixture Artifact

| Artifact | Rows | Report Date | As-Of Position Date | Markets | Source | Manifest |
| --- | ---: | --- | --- | --- | --- | --- |
| `data/fixtures/cftc/cftc_tff_tiny.csv` | 8 | `2026-05-08` | `2026-05-05` | `E-Mini S&P 500`, `UST 10Y Note` | CFTC TFF current futures-only report | `data/fixtures/cftc/cftc_tff_tiny.manifest.json` |

## Data Shape

Columns:

```text
report_date
asof_position_date
market_name
contract_market_code
trader_category
long_positions
short_positions
spreading_positions
open_interest
official_source_row_locator
```

Trader categories:

- `Dealer/Intermediary`;
- `Asset Manager/Institutional`;
- `Leveraged Funds`;
- `Other Reportables`.

## Validation Plan

Implemented static checks:

- manifest exists;
- `sha256` matches artifact bytes;
- manifest `row_count` matches physical rows;
- `report_date` parses;
- `asof_position_date` parses;
- `market_name` is present;
- `contract_market_code` is present;
- `trader_category` is in allowed categories;
- `long_positions` is finite and non-negative;
- `short_positions` is finite and non-negative;
- `spreading_positions` is finite and non-negative when present;
- `open_interest` is finite and non-negative;
- duplicate primary key `(report_date, market_name, contract_market_code, trader_category)` is rejected;
- `source_quality` is present and equals `public_official_observed`;
- `allowed_use` and `forbidden_use` are present;
- `observed_estimated_or_inferred` equals `observed`;
- `single_name_inference` is forbidden;
- ticker/single-name fields are rejected when mixed into the broad futures fixture.

Test artifact:

```text
tests/test_g7_1f_cftc_tff_tiny_fixture.py
```

## What This Unlocks

If G7.1F passes, the repo has a third official public source fixture integrated into governance discipline:

```text
SEC: thesis / ownership / filings / facts
FINRA: delayed short-crowding / squeeze-base context
CFTC: broad futures-positioning / systematic-regime context
```

Recommended next sequence:

```text
G7.1G - FRED/Ken French macro fixture
G7.2  - Unified Opportunity State Machine
```

State-machine work should remain held until G7.2 is separately approved.

## Explicit Holds

Held after G7.1F:

- G7.2 state machine;
- CFTC provider class;
- live CFTC API call;
- bulk CFTC download;
- CTA score;
- single-name CTA inference;
- FRED / Ken French fixture;
- Reg SHO fixture;
- ATS / dark-pool fixture;
- options / IV / gamma / whale data;
- provider code;
- live API calls;
- signal scoring;
- candidate generation;
- search;
- backtest;
- replay;
- dashboard runtime behavior;
- alerts;
- broker calls.
