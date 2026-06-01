---
name: boundary-gate
description: Classify proposed work against repo boundaries before execution. Use when a request may be blocked, may need explicit approval, or may be irrelevant to the active scope.
---

# Boundary Gate Skill

Use this skill before executing any ambiguous or scope-expanding request.

This repo-local adapter preserves Quant's current truth-surface authority. The generic meta-harness template is installed under `.meta-harness/templates/skills/boundary-gate.md` for reference, but this active skill owns Quant boundary classification.

## Inputs
1. Load:
   - `docs/context/bridge_contract_current.md`
   - `docs/context/impact_packet_current.md`
   - `docs/context/done_checklist_current.md`
2. Extract active scope, owned files, open decisions, forbidden actions, and approval gates.

## Classification Contract
Classify each proposed item as one of:

```text
BLOCKED: <item> | Reason: <violates locked boundary or missing required evidence>
EXPLICIT_APPROVAL: <item> | Reason: <safe only after user/source/policy approval>
NOT_RELEVANT: <item> | Reason: <outside active bottleneck or owned file budget>
ALLOWED: <item> | Reason: <inside owned scope and acceptance checks>
```

## Gate Rules
1. `BLOCKED` for actions forbidden by current `DO_NOT_REDECIDE` or done-checklist blocked criteria.
2. `EXPLICIT_APPROVAL` for governed data intake/regeneration, provider ingestion, runtime boot claims, production-impacting operations, or policy changes not already approved.
3. `NOT_RELEVANT` for work that is technically possible but does not advance the chosen scope.
4. `ALLOWED` only when owned files, acceptance checks, and rollback/stop conditions are clear.

## Output Rules
1. Lead with the classification.
2. Include the exact source boundary when available.
3. If any item is `BLOCKED`, do not implement it in the same round.
