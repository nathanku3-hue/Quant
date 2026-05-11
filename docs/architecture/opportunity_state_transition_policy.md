# Opportunity State Transition Policy

Status: Phase 65 G7.2 transition policy
Date: 2026-05-09
Authority: definition-only transition validation

## Purpose

Define allowed movement between opportunity states while preserving source-quality discipline and forbidding action semantics.

## Allowed Transition Shape

```text
TransitionRequest(
  current_state,
  requested_state,
  evidence.signals[reason_code, source_class, source_name],
  evidence.deterioration_evidence,
  evidence.thesis_broken,
  evidence.risk_approval,
  metadata
)
```

The transition validator returns:

```text
TransitionResult(allowed, resulting_state, reason)
```

It never emits a score, rank, order, alert, notification, provider call, dashboard mutation, or candidate event.

## Core Rules

| Rule | Policy |
| --- | --- |
| Evidence required | every transition must include at least one reason code and source class |
| Thesis override | `thesis_broken = true` produces `THESIS_BROKEN` even if requested state is bullish |
| Direct jump block | `THESIS_CANDIDATE -> BUYING_RANGE` is forbidden |
| Left-side block | `LEFT_SIDE_RISK -> BUYING_RANGE` is forbidden |
| Confirmation path | `LEFT_SIDE_RISK -> ACCUMULATION_WATCH -> BUYING_RANGE` or `LEFT_SIDE_RISK -> CONFIRMATION_WATCH -> BUYING_RANGE` is the minimum path |
| Deterioration gate | `LET_WINNER_RUN -> EXIT_RISK` requires deterioration evidence or `RISK_INVALIDATION` |
| Crowding gate | `CROWDED_FROTHY -> ADD_ON_SETUP` requires explicit risk approval |
| Estimated-only gate | estimated-only evidence cannot create `BUYING_RANGE` |
| Inferred-only gate | inferred-only evidence cannot create `LET_WINNER_RUN` |
| Forbidden metadata | action, alert, broker, score, and ranking fields fail closed |

## Allowed Uses

- state definition;
- schema validation;
- transition policy tests;
- dashboard/product planning language;
- future source-policy mapping.

## Forbidden Uses

- no buy/sell/hold instruction;
- no order construction;
- no alert emission;
- no ranking or score;
- no candidate generation;
- no dashboard runtime event;
- no provider call;
- no broker or notifier side effect.

## Source Pillar Constraints

The four public-source fixture pillars may provide reason-code context only:

- SEC: `THESIS_EVIDENCE`, `OWNERSHIP_WHALE_CONTEXT`;
- FINRA: `SHORT_SQUEEZE_BASE`;
- CFTC: `CTA_SYSTEMATIC_CONTEXT`;
- FRED/Ken French: `MACRO_LIQUIDITY_CONTEXT`, `FACTOR_REGIME_CONTEXT`.

None of these fixture pillars alone creates a buy/sell/order/alert/ranking state.

## Validation

Focused tests:

```text
.venv\Scripts\python -m pytest tests\test_g7_2_opportunity_state_machine.py -q
```

Required test themes:

- state enum completeness;
- forbidden direct jump;
- left-side confirmation path;
- thesis-broken override;
- estimated-only block;
- inferred-only block;
- crowded/frothy add-on block;
- reason-code and source-class requirement;
- no alert/broker/action fields;
- no score/ranking fields.
