# Unified Opportunity State Machine

Status: Phase 65 G7.2 definition-only state machine
Date: 2026-05-09
Authority: G7.2 state definition, transition schema, and validator only

## Purpose

Define how supercycle thesis quality, GodView market behavior, and risk discipline become one opportunity state without starting alpha search.

This file does not authorize candidate generation, search, scoring, ranking, alerts, broker calls, provider ingestion, live API calls, dashboard runtime behavior, paper trading, or buy/sell orders.

## Product Formula

```text
opportunity_state =
  primary_alpha_thesis_quality
  + secondary_alpha_market_behavior
  + risk_discipline_layer
  + source_quality_controls
```

This is a state-classification formula only. It is not a score, weight, threshold, rank, signal, prompt, or order rule.

SR 26-2 model-risk alignment: the state machine is defined before it becomes executable decision support. Federal Reserve SR 26-2, issued April 17, 2026, emphasizes a risk-based model-risk approach and sound principles for model development/use, validation/monitoring, governance, and controls. Source: https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm

## State List

| State | Meaning | Entry Discipline |
| --- | --- | --- |
| `IGNORE` | Not relevant or outside product scope | no monitoring obligation |
| `THEME_WATCH` | Theme exists, but no company-level thesis yet | watch theme only |
| `THESIS_CANDIDATE` | Candidate has a plausible supercycle thesis | no entry state |
| `EVIDENCE_BUILDING` | Evidence is forming but not enough for action | keep building thesis and source record |
| `LEFT_SIDE_RISK` | Thesis may be attractive, but price/behavior says too early | block buying-range classification |
| `ACCUMULATION_WATCH` | Weakness may be absorbed, but confirmation incomplete | monitor absorption and source quality |
| `CONFIRMATION_WATCH` | Market behavior is starting to confirm | monitor for entry discipline, no order |
| `BUYING_RANGE` | Entry conditions are becoming acceptable | state only; no buy order |
| `ADD_ON_SETUP` | Existing thesis can support controlled add | requires risk/crowding checks; no order |
| `LET_WINNER_RUN` | Thesis and behavior both support holding | no sell order or alert |
| `TRIM_OPTIONAL` | Not broken, but risk/crowding/froth supports reducing | no sell order |
| `CROWDED_FROTHY` | Upside may continue, but chase risk is high | blocks add-on without risk approval |
| `EXIT_RISK` | Behavior or thesis deterioration is material | no sell order |
| `THESIS_BROKEN` | Core thesis invalidated | overrides behavior strength |

## Required Reason Codes

```text
THESIS_EVIDENCE
PRICE_VOLUME_BEHAVIOR
IV_VOL_BEHAVIOR
OPTIONS_WHALE_BEHAVIOR
SHORT_SQUEEZE_BASE
CTA_SYSTEMATIC_CONTEXT
ROTATION_CONTEXT
MACRO_LIQUIDITY_CONTEXT
FACTOR_REGIME_CONTEXT
OWNERSHIP_WHALE_CONTEXT
RISK_INVALIDATION
```

## Required Source Classes

G7.2 transition evidence uses only observation class labels:

```text
observed
estimated
inferred
```

Each transition requires at least one reason code and one source class. Missing evidence fails closed.

## Invariants

1. A name cannot jump directly from `THESIS_CANDIDATE` to `BUYING_RANGE`.
2. `LEFT_SIDE_RISK` must pass through `ACCUMULATION_WATCH` or `CONFIRMATION_WATCH` before `BUYING_RANGE`.
3. `LET_WINNER_RUN` cannot move to `EXIT_RISK` without deterioration evidence.
4. `THESIS_BROKEN` overrides market-behavior strength.
5. `CROWDED_FROTHY` blocks `ADD_ON_SETUP` unless risk approval exists.
6. Estimated signals cannot alone create `BUYING_RANGE`.
7. Inferred signals cannot alone create `LET_WINNER_RUN`.
8. No state creates buy/sell orders.
9. No state emits alerts in this phase.
10. Every transition must include reason codes and source classes.

## Implementation Boundary

Implemented in G7.2:

- `opportunity_engine/states.py`
- `opportunity_engine/schemas.py`
- `opportunity_engine/transitions.py`
- `tests/test_g7_2_opportunity_state_machine.py`

Not implemented in G7.2:

- no candidate generation;
- no search;
- no backtest, replay, or proxy run;
- no signal score or ranking;
- no live provider or API call;
- no dashboard runtime behavior;
- no alert emission;
- no broker or Alpaca/OpenClaw path.

## Machine Formula

```text
g7_2_transition_valid =
  state_enum_complete
  and reason_codes_present
  and source_classes_present
  and forbidden_jump_not_requested
  and thesis_broken_override_applied
  and estimated_only_buying_range == false
  and inferred_only_let_winner_run == false
  and score_rank_alert_broker_fields_absent
```

Source paths:

- `opportunity_engine/states.py`
- `opportunity_engine/schemas.py`
- `opportunity_engine/transitions.py`
- `tests/test_g7_2_opportunity_state_machine.py`
