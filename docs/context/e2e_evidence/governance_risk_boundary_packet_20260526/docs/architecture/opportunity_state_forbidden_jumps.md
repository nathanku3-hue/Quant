# Opportunity State Forbidden Jumps

Status: Phase 65 G7.2 forbidden-jump register
Date: 2026-05-09
Authority: machine-checkable transition guardrail

## Hard Forbidden Jumps

| From | To | Reason |
| --- | --- | --- |
| `THESIS_CANDIDATE` | `BUYING_RANGE` | plausible thesis is not entry discipline |
| `LEFT_SIDE_RISK` | `BUYING_RANGE` | left-side risk must pass absorption or confirmation |
| `LET_WINNER_RUN` | `EXIT_RISK` | requires deterioration evidence |
| `CROWDED_FROTHY` | `ADD_ON_SETUP` | blocked unless risk approval exists |
| any non-broken state | action/order/alert metadata | states do not create orders or alerts |
| estimated-only evidence | `BUYING_RANGE` | estimated signals may modify confidence only |
| inferred-only evidence | `LET_WINNER_RUN` | inferred signals cannot alone support hold discipline |

## Override Rule

`THESIS_BROKEN` is not a normal jump. It is an override state:

```text
if thesis_broken == true:
    resulting_state = THESIS_BROKEN
```

This prevents strong price/volume, options, rotation, or macro behavior from preserving a state after the core thesis is invalidated.

## Explicit Non-Action Policy

The following fields are forbidden in transition metadata:

```text
alert
alert_emitted
broker_action
broker_call
buy_order
sell_order
order
order_action
score
rank
ranking
candidate_rank
signal_score
```

Their presence causes transition validation to fail closed.

## G7.2 Boundary

G7.2 may define states, transitions, schemas, and validator tests.

G7.2 may not generate candidates, run search, compute scores, rank tickers, emit alerts, call providers, ingest live data, touch broker paths, or change dashboard runtime behavior.
