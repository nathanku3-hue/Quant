# GodView Signal Confidence Policy

Status: Phase 65 G7.3 policy-only
Date: 2026-05-09
Authority: confidence labels for state influence only

## Confidence Labels

```text
OBSERVED_CONTEXT
CANONICAL_BEHAVIOR
LICENSED_REQUIRED
ESTIMATED_CONTEXT
INFERRED_RESEARCH_ONLY
REJECTED_FOR_STATE_ADVANCE
```

## Confidence Rules

| Label | Meaning | Allowed Use | Forbidden Use |
| --- | --- | --- | --- |
| `OBSERVED_CONTEXT` | official/public observed context with manifest | reason codes, context panels, state explanation | rankings, alerts, orders |
| `CANONICAL_BEHAVIOR` | canonical price/volume behavior | behavior-state influence after validator gates | thesis-broken override bypass |
| `LICENSED_REQUIRED` | source family is provider/license gated | planning and policy only | state advancement, dashboard runtime, alerts |
| `ESTIMATED_CONTEXT` | model-derived context | confidence modifier after source policy | sole action-state evidence |
| `INFERRED_RESEARCH_ONLY` | human/research inference | thesis/risk narrative context | sole action-state evidence |
| `REJECTED_FOR_STATE_ADVANCE` | stale/unlicensed/unmanifested/rejected | no state influence | all state advancement |

## Freshness Degradation

If freshness is stale or unknown:

```text
state_influence = research_context_only
```

unless a future source policy explicitly allows a different treatment.

## Dashboard Wording Boundary

Future dashboard copy must show whether a signal is observed, estimated, or inferred. It must not label:

- estimated gamma as observed dealer positioning;
- options whale intent as fact;
- dark-pool accumulation as fact from prints alone;
- short interest as real-time squeeze timing;
- FRED/Ken French context as macro/factor score;
- any state as a buy/sell order.
