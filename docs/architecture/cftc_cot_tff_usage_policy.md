# CFTC COT/TFF Usage Policy

Status: Phase 65 G7.1F usage policy
Date: 2026-05-10
Authority: interpretation boundary for static fixture proof only

## Purpose

Define how Terminal Zero may interpret CFTC Commitments of Traders / Traders in Financial Futures data after the G7.1F tiny fixture proof.

CFTC TFF is useful because it gives official observed positioning categories for broad financial futures. It is dangerous if overread as direct single-stock flow, because the report is market-level, weekly, delayed, and organized by futures contract and trader category rather than by equity ticker.

## Use Boundary

Allowed:

- broad futures-positioning context;
- macro/regime support;
- CTA/systematic-pressure proxy;
- GodView market-behavior context.

Forbidden:

- direct single-name CTA buying evidence;
- buy/sell signal;
- standalone ranking factor;
- alert emission;
- alpha evidence without validation.

Hard language:

```text
CFTC TFF may say "systematic/regime positioning context is supportive or hostile."
It may not say "CTAs are buying this stock today."
```

## Trader Category Boundary

G7.1F allows only these TFF categories in the tiny fixture:

```text
Dealer/Intermediary
Asset Manager/Institutional
Leveraged Funds
Other Reportables
```

Interpretation notes:

- `Leveraged Funds` can be a useful proxy bucket for hedge-fund / systematic / CTA-like pressure at the futures-market level.
- `Leveraged Funds` is not equivalent to a named CTA and does not prove single-name equity demand.
- `Asset Manager/Institutional` and `Dealer/Intermediary` are context labels, not decision labels.
- `Other Reportables` is a residual reported bucket and must not be turned into a signal.

## Timing Boundary

CFTC COT/TFF is weekly and delayed:

```text
publication cadence = normally Friday 3:30 p.m. ET
position as-of date = Tuesday
freshness_policy = weekly / Friday release / Tuesday positions
```

Allowed phrasing:

```text
Broad futures positioning was supportive/hostile as of the Tuesday report date.
```

Forbidden phrasing:

```text
CTAs are buying this stock today.
```

## State-Machine Boundary

G7.1F does not approve G7.2.

The CFTC TFF fixture can be referenced later as a candidate source label for broad market-behavior context only after a separate G7.2 approval. It cannot trigger a buy/sell/hold state by itself.

## Formula Register

```text
cftc_tff_allowed_context = observed_futures_positioning
  and broad_market_contract
  and weekly_delayed
  and source_quality == public_official_observed
  and single_name_inference == false
```

```text
cftc_tff_forbidden_signal = single_name_cta_claim
  or standalone_buy_sell_signal
  or ranking_factor
  or alert_emission
  or alpha_evidence_without_validation
```

## Verdict

CFTC COT/TFF is approved in G7.1F only as broad futures-positioning context and a systematic/regime proxy. It is not single-stock CTA evidence and cannot act as a standalone state-machine, ranking, or alert input.
