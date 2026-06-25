# GodView Provider Selection Policy

Status: Phase 65 G7.1C audit-wait policy
Date: 2026-05-09
Authority: planning only; no provider approval

## Purpose

Define the gate a future GodView provider must pass before implementation. This is the policy bridge between the G7.1B data/infra gap and any future no-cost/public source work.

## Non-Negotiable Source Gates

A source is not eligible for provider implementation until all gates are answered:

| Gate | Required answer |
| --- | --- |
| Rights and terms | Source license/terms permit the intended local research use. |
| Cost | No-cost, free tier, paid, or licensed status is explicit. |
| Authentication | Key/account/credential needs are isolated from core logic. |
| As-of semantics | The date/time the source observation describes is explicit. |
| Capture time | The date/time Terminal Zero captured the data is explicit. |
| Freshness | Expected lag and stale thresholds are defined. |
| Raw locator | A reproducible source URL, accession, report id, or vendor locator exists. |
| Manifest fit | Records can be sealed with manifest/provenance metadata. |
| Source label | Output can be labeled observed, estimated, or inferred. |
| Allowed use | Permitted downstream uses are explicit. |
| Forbidden use | Blocked downstream uses are explicit. |
| Rollback | Bad source or bad ingest can be removed without mutating canonical history. |

## Source Preference Order

Use this order when multiple sources can support the same signal:

1. Official public source with clear terms, stable identifiers, and as-of semantics.
2. Licensed exchange or regulatory source when public data is not sufficient.
3. Vendor source with contractual coverage, history, and documented fields.
4. Research convenience source for discovery only.
5. Manual research capture for notes only unless source policy approves a structured workflow.

Rejected by default:

- unmanifested scraped data;
- unlabeled social/news snippets;
- yfinance as canonical evidence;
- paid/licensed data without explicit approval;
- any source that cannot preserve as-of time and raw locator.

## Provider Port Rules

Every future provider port must emit records with:

```text
provider
provider_feed
source_quality
license_scope
asof_ts
captured_at_utc
freshness
latency
observed_vs_estimated
manifest_uri
raw_locator
allowed_use
forbidden_use
```

Provider ports must not emit:

- dashboard state;
- signal rank;
- buy/sell prompt;
- alert;
- broker call;
- promotion verdict;
- candidate generation.

## Audit-To-Implementation Sequence

No-cost/public implementation may start only after this sequence:

1. Audit source URLs and current terms.
2. Write a provider-specific source policy.
3. Define minimal record schema and raw locator rules.
4. Define manifest/provenance requirements.
5. Create a tiny fixture plan with row-count, key, and date-range expectations.
6. Run source-quality review before any adapter writes canonical or governed data.
7. Receive explicit phase approval.

## Immediate Audit Targets

The first audit pass should cover:

- SEC submissions/companyfacts/13F/13D/G/Form 4;
- FINRA short interest, Reg SHO short-sale volume, ATS/OTC/block datasets;
- CFTC COT/TFF datasets;
- public macro/context sources such as FRED/Ken French.

Options/IV/gamma sources are audit targets too, but not no-cost implementation candidates unless a later provider decision says otherwise.

## Explicit Hold

G7.1C does not approve G7.2, G7.3 provider work, SEC ingestion, FINRA ingestion, CFTC ingestion, options ingestion, source registry implementation, dashboard runtime behavior, alerts, broker calls, or candidate generation.

