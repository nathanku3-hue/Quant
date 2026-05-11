# GodView API Availability Matrix

Status: Phase 65 G7.1C audit-wait matrix
Date: 2026-05-09
Authority: planning only; no source approval

## Purpose

Record the practical availability of GodView source candidates before provider design. This matrix supports audit planning only.

## Current Ready Surface

| Data/signal | Availability | Current classification | Current allowed use | Blocked use |
| --- | --- | --- | --- | --- |
| Canonical daily price/volume | Existing local Tier 0 lake | Canonical observed | Governance context, readiness, mechanical replay | Live execution trigger |
| Manifest/provenance | Existing repo | Governance | Artifact integrity and source tracking | Provider approval by itself |
| V1/V2 mechanical replay | Existing repo | Validation | Mechanical path proof | Alpha evidence |
| Data readiness audit | Existing repo | Governance | Freshness/schema sanity | Source replacement decision |
| yfinance convenience data | Existing repo quarantine | Tier 2 discovery only | Research convenience, examples | Canonical evidence or promotion |

## No-Cost/Public Candidates After Audit

| Candidate | Source type | Expected label | Freshness shape | Primary GodView value | Audit blocker |
| --- | --- | --- | --- | --- | --- |
| SEC submissions/companyfacts | Official public API | Observed | Intraday/daily filing updates | Filing-backed fundamentals and entity state | Terms, fair-access, entity mapping |
| SEC 13F | Official public filing | Observed but delayed | 45-day post-quarter filing lag per supplied study | Ownership whale context | Delay, issuer/security mapping |
| SEC 13D/G | Official public filing | Observed filing | Filing-lagged | Activist/large-holder context | Filing parsing and amendments |
| SEC Form 4 | Official public filing | Observed filing | Fast filing lag per supplied study | Insider confirmation | Issuer/person/security mapping |
| FINRA short interest | Official public dataset | Observed report | Twice monthly | Squeeze base | Delay and symbol mapping |
| FINRA Reg SHO volume | Official public dataset | Observed volume | Daily | Short-sale context | Must not be confused with short interest |
| FINRA ATS/OTC datasets | Official public/delayed datasets | Observed aggregate; accumulation inferred | Delayed/monthly or dataset-specific | Dark-pool/block context | Interpretation and latency |
| CFTC COT/TFF | Official public dataset | Observed futures positioning | Weekly | CTA/systematic proxy | Futures-to-equity mapping is estimated |
| FRED / Ken French / macro | Public/mixed | Observed/context | Daily/monthly/periodic | Regime and factor context | Release timing and PIT alignment |

## Paid Or Licensed Decision Points

| Candidate | Source type | Expected label | GodView value | Decision status |
| --- | --- | --- | --- | --- |
| OPRA | Consolidated options tape | Observed if licensed | Options prints/quotes | Defer for provider/license decision |
| OCC options reports/data | Official reports/data products | Observed daily fields | Options volume/OI | Audit public vs paid scope |
| Tradier + ORATS | Vendor/API | Observed quotes plus vendor/model fields | IV/Greeks/options chains | Defer for account/terms review |
| Massive/Polygon-style API | Vendor/API | Observed plus vendor fields | Options trades, quotes, IV, Greeks, OI | Defer for cost/coverage decision |
| ThetaData | Vendor/API | Observed vendor feed | Historical/real-time options | Defer for cost/coverage decision |
| Nasdaq TotalView | Exchange feed | Observed if licensed | Full order book | Later paid microstructure |
| NYSE TAQ / WRDS | Licensed/academic data | Observed if licensed | Historical trades/quotes | Later paid/academic route |
| ETF/passive-flow vendor | Vendor/API | Observed/vendor-derived | ETF holdings/flows | Source selection required |
| News/narrative vendor | Vendor/API/manual | Inferred from source captures | Thesis/narrative state | Source policy required |

## Availability Verdict

Current repo support:

```text
ready = canonical_daily_price_volume + manifests + readiness_audit + replay_validation + provider_port_pattern
not_ready = options_iv_whales_gamma + short_interest_ingestion + cftc_ingestion + sec_ownership_ingestion + etf_flows + ats_dark_pool + taq_order_book + governed_news
```

No-cost near-term candidates are SEC, FINRA, CFTC, and public macro/factor sources, but only after source audit. Options, IV, whales, gamma, and microstructure are not no-cost implementation candidates.

## Required Labels

Future signals must keep these labels separate:

- `observed`: official/licensed observation with as-of semantics and manifest evidence;
- `estimated`: model output derived from observed inputs, such as gamma exposure or CTA pressure;
- `inferred`: narrative or state interpretation, such as thesis health or market-behavior interpretation.

Estimated signals must never masquerade as observed facts.

