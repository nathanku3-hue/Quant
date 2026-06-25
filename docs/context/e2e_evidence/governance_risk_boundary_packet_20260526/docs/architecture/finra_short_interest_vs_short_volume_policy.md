# FINRA Short Interest vs Short-Sale Volume Policy

Status: Phase 65 G7.1E interpretation policy
Date: 2026-05-10
Authority: labeling and misuse-prevention policy only; no provider approval

## Purpose

Prevent FINRA short-interest data, Reg SHO daily short-sale volume, and OTC/ATS transparency data from being conflated in GodView planning.

This policy exists because all three source families can sound like "short pressure," but they measure different things, arrive on different schedules, and support different claims.

## Core Rule

```text
Short interest = slow squeeze base.
Reg SHO short-sale volume = daily trading context.
OTC / ATS transparency = delayed aggregate venue context.
Neither one alone = squeeze signal.
```

## FINRA Short Interest

Short interest measures reported outstanding short positions as of specific settlement dates. It is delayed position context.

Allowed label:

```text
delayed short-crowding evidence
```

Allowed claim:

```text
short base exists
```

Forbidden claim:

```text
forced covering is happening now
```

## Reg SHO Daily Short-Sale Volume

Reg SHO daily short-sale volume measures aggregated short-sale volume by security for trades reported to FINRA facilities. It is daily activity context, not outstanding position context.

Allowed label:

```text
daily short-sale-volume context
```

Forbidden labels:

```text
short interest
borrow stress
forced covering
real-time squeeze trigger
```

## OTC / ATS Transparency

FINRA OTC/ATS transparency datasets support delayed aggregate trading context. They must not be labeled as real-time dark-pool accumulation or observed whale intent.

Allowed label:

```text
delayed aggregate venue context
```

Forbidden labels:

```text
real-time dark-pool accumulation
observed whale buying
single-name squeeze trigger
```

## G7.1E Fixture Boundary

The G7.1E fixture contains short-interest columns only:

```text
settlement_date
ticker
issue_name
short_interest
average_daily_volume
days_to_cover
official_source_row_locator
```

The fixture must not contain Reg SHO fields such as:

```text
trade_date
short_sale_volume
short_exempt_volume
total_volume
market_center
```

## Future Work

Reg SHO daily short-sale volume may become a later tiny fixture only after explicit approval. It should use a separate fixture, manifest, policy, and test file.

OTC / ATS block or transparency data also remains a later phase and must stay separated from short interest.
