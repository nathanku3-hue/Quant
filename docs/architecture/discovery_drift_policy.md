# Discovery Drift Policy

Status: G8.1A governance contract
Authority: Phase 65 G8.1A Discovery Drift Correction
Date: 2026-05-10

## Purpose

G8.1 created a six-name discovery intake queue, but the queue was user-seeded. G8.1A prevents future conceptual drift by separating origin labels from later evidence, ranking, validation, and action states.

## Drift Being Corrected

The current queue contains:

```text
MU, DELL, INTC, AMD, LRCX, ALB
```

These names are not pure system-discovered output. They must not be described as `SYSTEM_SCOUTED`.

## Required Origin Fields

Every discovery intake item must carry:

- `discovery_origin`
- `origin_evidence`
- `scout_path`
- `is_user_seeded`
- `is_system_scouted`
- `is_validated`
- `is_actionable`

## Current Six-Name Relabeling

```text
MU   = USER_SEEDED, candidate_card_exists
DELL = USER_SEEDED + THEME_ADJACENT, intake_only
INTC = USER_SEEDED + THEME_ADJACENT, intake_only
AMD  = USER_SEEDED + THEME_ADJACENT, intake_only
LRCX = USER_SEEDED + SUPPLY_CHAIN_ADJACENT, intake_only
ALB  = USER_SEEDED + THEME_ADJACENT, intake_only
```

All six names must remain:

```text
is_system_scouted = false
is_validated = false
is_actionable = false
```

`MU` may remain `candidate_card_exists = true` through `current_status = candidate_card_exists`, but this does not make MU validated or actionable.

## Forbidden Drift

G8.1A does not allow:

- alpha search;
- candidate ranking;
- candidate scoring;
- buy/sell/hold labels;
- validated-thesis labels;
- actionable labels;
- dashboard runtime behavior;
- alerts;
- broker calls;
- factor-scout consumption.

## Implementation Anchors

- `opportunity_engine/discovery_intake_schema.py`
- `opportunity_engine/discovery_intake.py`
- `data/discovery/supercycle_candidate_intake_queue_v0.json`
- `tests/test_g8_1a_discovery_drift_policy.py`
