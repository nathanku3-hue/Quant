# GodView Daily Brief Spec

Status: Phase 65 G7.4 product-state spec only
Date: 2026-05-09
Authority: daily brief content specification only

## Purpose

Define a future daily brief around opportunity-state changes, not scores, rankings, alerts, or orders.

No dashboard runtime code is added.

## Brief Sections

1. State distribution.
2. State changes since prior review.
3. Freshness and source-quality gaps.
4. New thesis evidence or contradiction evidence.
5. Entry-discipline blockers.
6. Hold-discipline blockers.
7. GodView provider-gap reminders.
8. Open monitoring questions.

## Required Language Rules

Use:

```text
state changed because...
source class is...
freshness is...
blocked because...
monitor next...
```

Do not use:

```text
buy now
sell now
top ranked
score improved
alert triggered
broker action
candidate generated
```

## Daily Brief Record Shape

```json
{
  "brief_date": "YYYY-MM-DD",
  "state_distribution": {},
  "state_changes": [],
  "freshness_gaps": [],
  "source_quality_gaps": [],
  "thesis_evidence_updates": [],
  "risk_invalidation_updates": [],
  "why_not_buy_yet": [],
  "why_not_sell_yet": [],
  "provider_gaps": [],
  "next_monitoring_questions": []
}
```

This record shape is product-spec only. It is not a runtime schema, not a data sink, not an alert payload, and not a notification contract.

## Footer Invariant

```text
daily_brief_state_only = true
no buy or sell orders
no alerts
no scores
no rankings
no provider calls
no broker calls
```
