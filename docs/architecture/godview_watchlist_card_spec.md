# GodView Watchlist Card Spec

Status: Phase 65 G7.4 product-state spec only
Date: 2026-05-09
Authority: watchlist card schema/spec only

## Purpose

Define the watchlist card fields for state-first GodView dashboard planning.

No dashboard runtime code is added.

## Required Fields

```text
ticker
theme
current_state
previous_state
state_change_reason
thesis_state
entry_discipline
hold_discipline
market_behavior_summary
risk_state
freshness_summary
observed_estimated_inferred_breakdown
blocked_actions
next_monitoring_questions
```

## Field Semantics

| Field | Meaning | Boundary |
| --- | --- | --- |
| `ticker` | security identifier or placeholder theme ticker | does not create candidate |
| `theme` | supercycle or product theme | does not create thesis approval |
| `current_state` | one `OpportunityState` value | state label only |
| `previous_state` | prior `OpportunityState` value | no ranking |
| `state_change_reason` | reason codes and source classes behind change | requires source labels |
| `thesis_state` | thesis evidence health and contradiction status | inferred, not alpha score |
| `entry_discipline` | left-side/accumulation/confirmation/buying-range status | no buy order |
| `hold_discipline` | let-run/trim/exit-risk status | no sell order |
| `market_behavior_summary` | source-labeled GodView behavior context | no signal ranking |
| `risk_state` | invalidation and crowding/froth state | review state only |
| `freshness_summary` | fresh/delayed/stale/unknown by family | no silent promotion |
| `observed_estimated_inferred_breakdown` | source label counts and caveats | estimates do not become facts |
| `blocked_actions` | why buying/selling/ranking/alerting is blocked | no runtime action |
| `next_monitoring_questions` | human review questions | no alert emission |

## Required Blocked Actions

Every card must be able to show these blocked actions:

```text
buy_order_blocked
sell_order_blocked
alert_blocked
ranking_blocked
provider_call_blocked
candidate_generation_blocked
dashboard_runtime_change_blocked
```

## Example Card Shape

```json
{
  "ticker": "EXAMPLE",
  "theme": "supercycle theme placeholder",
  "current_state": "CONFIRMATION_WATCH",
  "previous_state": "ACCUMULATION_WATCH",
  "state_change_reason": ["PRICE_VOLUME_BEHAVIOR", "THESIS_EVIDENCE"],
  "thesis_state": "evidence building; no thesis-broken flag",
  "entry_discipline": "confirmation improving; no order",
  "hold_discipline": "not applicable before position",
  "market_behavior_summary": "observed canonical behavior plus context-only public fixtures",
  "risk_state": "no risk approval; no crowded add-on",
  "freshness_summary": "daily canonical fresh; fixture context static",
  "observed_estimated_inferred_breakdown": {
    "observed": 2,
    "estimated": 0,
    "inferred": 1
  },
  "blocked_actions": [
    "buy_order_blocked",
    "alert_blocked",
    "ranking_blocked"
  ],
  "next_monitoring_questions": [
    "Has observed behavior confirmed without stale source gaps?",
    "Has thesis evidence changed?"
  ]
}
```

The example is schema-only. It is not a candidate card and not an actual ticker recommendation.
