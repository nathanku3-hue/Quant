# GodView Signal-to-State Map

Status: Phase 65 G7.3 policy-only source eligibility map
Date: 2026-05-09
Authority: signal-to-state policy only

## Purpose

Map GodView signal families to observed/estimated/inferred labels, source eligibility, allowed state influence, forbidden state influence, freshness requirement, and confidence label.

This file does not authorize provider code, live API calls, ingestion, source registry implementation, fixture expansion, scoring, ranking, alerts, broker calls, candidate generation, search, replay, proxy runs, or dashboard runtime behavior.

## Source Classes

```text
OBSERVED_OFFICIAL
OBSERVED_CANONICAL
OBSERVED_LICENSED
ESTIMATED_MODEL
INFERRED_RESEARCH
TIER2_DISCOVERY
REJECTED
```

## Signal Map

| Signal Family | Observed/Estimated/Inferred | Source Class | Allowed State Influence | Forbidden State Influence | Freshness Requirement | Confidence Label |
| --- | --- | --- | --- | --- | --- | --- |
| `SUPERCYCLE_THESIS` | inferred | `INFERRED_RESEARCH` | theme/thesis/evidence building | buying range, add-on, let-winner-run alone | manual research as-of date | `INFERRED_RESEARCH_ONLY` |
| `SEC_FILINGS_OWNERSHIP` | observed | `OBSERVED_OFFICIAL` | thesis evidence, ownership context, confirmation/hold/risk | ranking, alerts, action states alone | filing date/accession/as-of | `OBSERVED_CONTEXT` |
| `FINRA_SHORT_INTEREST` | observed | `OBSERVED_OFFICIAL` | squeeze-base context, evidence building, crowded/frothy | real-time squeeze ignition, buying range, add-on, let-winner-run | twice-monthly settlement/publication date | `OBSERVED_CONTEXT` |
| `CFTC_TFF_POSITIONING` | observed | `OBSERVED_OFFICIAL` | broad systematic/regime context | single-name CTA buying, buying range, add-on, let-winner-run | weekly report date and Tuesday position date | `OBSERVED_CONTEXT` |
| `FRED_MACRO_LIQUIDITY` | observed | `OBSERVED_OFFICIAL` | macro liquidity context | macro score, alpha evidence, buying range, add-on, let-winner-run | series date, vintage/realtime semantics | `OBSERVED_CONTEXT` |
| `KEN_FRENCH_FACTOR_CONTEXT` | observed | `OBSERVED_OFFICIAL` | factor regime context | factor score, alpha evidence, candidate ranking, action states | dataset date and citation | `OBSERVED_CONTEXT` |
| `PRICE_VOLUME_BEHAVIOR` | observed | `OBSERVED_CANONICAL` | left-side, accumulation, confirmation, buying range, hold, risk states | thesis-broken override bypass | canonical daily as-of + manifest | `CANONICAL_BEHAVIOR` |
| `IV_VOL_INTELLIGENCE` | estimated | `OBSERVED_LICENSED` provider-gap | evidence building only until provider decision | action states | licensed provider and as-of timestamp required | `LICENSED_REQUIRED` |
| `OPTIONS_WHALE_RADAR` | estimated | `ESTIMATED_MODEL` provider-gap | evidence building only until provider decision | action states, whale intent as fact | licensed tape + classifier policy required | `LICENSED_REQUIRED` |
| `GAMMA_DEALER_MAP` | estimated | `ESTIMATED_MODEL` provider-gap | evidence building only until provider decision | observed dealer-positioning claims, action states | options chain/OI + model manifest required | `LICENSED_REQUIRED` |
| `ROTATION_SCORE` | estimated | `ESTIMATED_MODEL` | rotation context, confirmation/crowding context | buying range, add-on, let-winner-run alone | model as-of + input manifest | `ESTIMATED_CONTEXT` |
| `ETF_PASSIVE_FLOW` | observed/estimated | `OBSERVED_LICENSED` provider-gap | evidence building only until provider decision | unlicensed flow evidence, action states | licensed/vendor flow as-of | `LICENSED_REQUIRED` |
| `DARK_POOL_BLOCK_RADAR` | estimated | `ESTIMATED_MODEL` provider-gap | evidence building only until provider decision | accumulation fact claims, action states | ATS/vendor delay and source policy required | `LICENSED_REQUIRED` |
| `MICROSTRUCTURE_LIQUIDITY` | observed | `OBSERVED_LICENSED` provider-gap | evidence building only until provider decision | thesis approval, action states | licensed intraday feed as-of | `LICENSED_REQUIRED` |
| `NEWS_NARRATIVE_VELOCITY` | inferred | `INFERRED_RESEARCH` provider-gap | evidence building / thesis contradiction context | alpha evidence, ranking, alerts | sourced note or vendor news as-of | `LICENSED_REQUIRED` |
| `RISK_INVALIDATION` | inferred | `INFERRED_RESEARCH` | exit risk, thesis broken | bullish action states | contradiction evidence as-of | `INFERRED_RESEARCH_ONLY` |

## G7.3 Rules

1. SEC/FINRA/CFTC/FRED/KF fixtures may support context and reason codes.
2. They may not generate rankings or alerts.
3. Estimated signals may modify confidence, but cannot alone move to `BUYING_RANGE`.
4. Tier 2/yfinance cannot move any state toward `BUYING_RANGE` or `LET_WINNER_RUN`.
5. Options/IV/gamma/whales remain provider-gap signals until licensed provider decision.
6. Short interest supports squeeze-base context only, not real-time squeeze ignition.
7. CFTC supports broad regime/positioning context only, not single-name CTA buying.
8. FRED/KF support macro/factor context only, not alpha evidence.

## Machine Paths

Policy is mirrored in:

- `opportunity_engine/source_classes.py`
- `opportunity_engine/signal_policy.py`
- `tests/test_g7_3_signal_to_state_source_map.py`
