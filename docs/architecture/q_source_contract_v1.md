# QSourceContractV1

**Date:** 2026-08-12  
**Status:** `BLOCKED_UNSET` / current feasibility path = `Q_SOURCE_BLOCKED`  
**Slice:** `OK-SBI-0` (shadow research only)  
**Machine freeze:** `docs/architecture/q_source_contract_v1.json`  
**Implementation:** `research/asymmetric_opportunity_v1/q_source_contract.py`

## Global authority sentence

> **Q is not a deployable numeric factor until `QSourceContractV1.status ∈ {Q_GF_BOUND, Q_AMENDED_BOUND}`.**  
> RevGrowth + ROIC, Rule100-Q, and similar formulations are **conceptual or historical candidates only** unless their exact PIT primitives, transformations, lags, missingness law, and hashes are bound.

## Separations (do not collapse)

```text
Q_SOURCE_OBSERVED     ≠  Q_NUMERIC_VALUE_AVAILABLE
Q_NUMERIC_AVAILABLE   ≠  Q_VALIDATED
Q_VALIDATED           ≠  Q_CAPITAL_AUTHORIZED
```

AO-K0A freezes **source-availability / basis-status** only. It does **not** invent a numeric Q kernel and does **not** authorize borrowing legacy assembled Rule100-Q feature stores.

## Allowed status values

```text
BLOCKED_UNSET
Q_GF_BOUND
Q_MINIMAL_AMENDMENT_REQUIRED   # intermediate only; max 1 outcome-blind cycle
Q_AMENDED_BOUND
Q_SOURCE_BLOCKED
```

```text
max_outcome_blind_q_amendment_cycles = 1
```

A second redesign requires a **new slice_id**, new search budget, and new hashes — not another OK-SBI-0 loop.

## Required fields per primitive

Every numeric Q primitive must bind all of:

```text
primitive_id
provider_source_object
exact_field_identifier
ciqsec_trading_item_identity
period_perspective_semantics
pit_availability_timestamp
minimum_publication_processing_lag
unit_currency_law
formula_denominator
restatement_carry_law
applicability_rule
missingness_reason
corporate_action_treatment
source_receipt_hash
no_bridge_proof
```

Forbidden:

```text
silent synthetic substitute
unavailable-field bridge
ticker / entity / PERMNO fallback
post-label Q redesign
legacy test/feature-store borrow for Q definition
```

## Current state (2026-08-12)

```text
status                         = Q_SOURCE_BLOCKED
conceptual_candidate           = RevGrowth_12m + ROIC (NOT authority)
q_amendment_cycles_used        = 0
q_source_binding_hash          = BLOCKED_UNSET
runnable_evaluation (OK-SBI-0) = false
```

## Relation to OK-SBI-0 / AO-K0B

- **OK-SBI-0** = active shadow research umbrella (S0 pre-open machinery).  
- **AO-K0A** = frozen prerequisite (denominator / abstention / residual geometry).  
- **AO-K0B** = legacy blocked pointer for a result-bearing basis test; must **not** run as automatic `Q / M⊥ / Q+M⊥` trophy next.  
- **AO-K0B-D** = development/result-bearing stage **inside** OK-SBI-0 only after Q bind + numeric gates + label hashes + one-shot carve-out.

No Alpha, capital, or production authority is created by this contract.
