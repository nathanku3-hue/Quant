# SEC Public Provider Fixture Plan

Status: Phase 65 G7.1D fixture materialized; provider work held
Date: 2026-05-09
Authority: static fixture validation plan only; no live provider

## Purpose

Define and record the one tiny SEC public-source fixture proof created in G7.1D.

The fixture proves governance mechanics, not market edge. It is deliberately too small to act as a data lake.

## Fixture Artifacts

| Artifact | Rows | Entity | Endpoint | Manifest |
| --- | ---: | --- | --- | --- |
| `data/fixtures/sec/sec_companyfacts_tiny.json` | 2 facts | AAPL / CIK `0000320193` | `companyfacts` | `data/fixtures/sec/sec_companyfacts_tiny.json.manifest.json` |
| `data/fixtures/sec/sec_submissions_tiny.json` | 5 filings | AAPL / CIK `0000320193` | `submissions` | `data/fixtures/sec/sec_submissions_tiny.json.manifest.json` |

## Data Shape

Companyfacts sample:

- `Assets`, USD, FY 2026 Q2, form `10-Q`, end `2026-03-28`, filed `2026-05-01`;
- `NetIncomeLoss`, USD, FY 2026 Q2, form `10-Q`, end `2026-03-28`, filed `2026-05-01`.

Submissions sample:

- five recent filing metadata rows;
- forms: `4`, `144`, `10-Q`, `8-K`;
- filing date range: `2026-04-30` to `2026-05-08`.

## Validation Plan

Implemented static checks:

- manifest exists;
- `sha256` matches artifact bytes;
- manifest `row_count` matches physical rows;
- date fields parse;
- CIK is zero-padded 10 digits;
- duplicate primary key is rejected;
- non-finite numeric company facts are rejected;
- `source_quality` is present and equals `public_official_observed`;
- `allowed_use` and `forbidden_use` are present;
- `observed_estimated_or_inferred` equals `observed`.

Test artifact:

```text
tests/test_g7_1d_sec_tiny_fixture.py
```

## What This Unlocks

If G7.1D passes, the repo has its first official public source fixture integrated into governance discipline.

Recommended next sequence:

```text
G7.1E - FINRA short-interest tiny fixture
G7.1F - CFTC COT/TFF tiny fixture
G7.1G - FRED/Ken French macro fixture
G7.2  - Unified Opportunity State Machine
```

State-machine work should remain held until at least SEC and FINRA are proven, unless PM explicitly accepts speed over data grounding.

## Explicit Holds

Held after G7.1D:

- FINRA provider proof;
- CFTC provider proof;
- FRED provider proof;
- Ken French provider proof;
- SEC live provider code;
- source registry implementation;
- GodView signal scoring;
- candidate generation;
- dashboard runtime behavior;
- alerts or broker calls.
