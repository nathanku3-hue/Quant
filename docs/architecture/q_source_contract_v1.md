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

## Current state (2026-08-12) — OK-SBI-0-S0-Q-SOURCE-BIND

```text
status                         = Q_SOURCE_BLOCKED
conceptual_candidate           = RevGrowth_12m + ROIC (NOT authority)
q_amendment_cycles_used        = 0
q_source_binding_hash          = BLOCKED_UNSET
runnable_evaluation (OK-SBI-0) = false
outcome_open_authorized        = false
financial_alpha_evidence       = 0
```

### Admitted-custody audit (outcome-blind)

Bound attempt used only AO-K0A admitted boundary sources:

```text
IMMUTABLE_W3_DATE_LOCAL_AUTHORITY
ADMITTED_ECONPHYSICS_S0
EXACT_W3_MARKET_CUSTODY
```

Findings:

| Primitive | Candidate input in custody? | Bind status |
|---|---|---|
| `RevGrowth_12m` | `IQ_TOTAL_REV` on admitted S0 structured transitions (level only) | **UNBOUND** — formula, PIT lag, applicability, joint CIQSEC+trading_item on S0 rows not frozen as Q authority |
| `ROIC` | **none** (no `IQ_ROIC` / NOPAT / invested-capital metric in admitted S0 receipt metrics) | **UNBOUND** — inventing ROIC from `IQ_OPER_INC`/`IQ_CAPEX_BNK` is forbidden |

Identity gap:

```text
W3 eligible rows carry (security_id=CIQSEC, trading_item_id)
S0 master maps SP_ENTITY_ID → security_id
S0 fundamental rows lack trading_item_id
→ CIQSEC+trading_item joint identity for Q primitives remains unbound
```

Amendment budget:

```text
max_outcome_blind_q_amendment_cycles = 1
q_amendment_cycles_used              = 0
amendment_consumed                   = false
reason: a single field tweak cannot lawfully invent ROIC or complete joint
        identity without new admitted custody; second redesign requires new slice_id
```

Evidence:

```text
docs/context/e2e_evidence/ok_sbi_0_q_source_bind_attempt_20260812.json
research/asymmetric_opportunity_v1/q_source_contract.py  (audit_admitted_custody_for_q)
```

## Relation to OK-SBI-0 / AO-K0B

- **OK-SBI-0** = active shadow research umbrella (S0 pre-open machinery).  
- **AO-K0A** = frozen prerequisite (denominator / abstention / residual geometry).  
- **AO-K0B** = legacy blocked pointer for a result-bearing basis test; must **not** run as automatic `Q / M⊥ / Q+M⊥` trophy next.  
- **AO-K0B-D** = development/result-bearing stage **inside** OK-SBI-0 only after Q bind + numeric gates + label hashes + one-shot carve-out.

No Alpha, capital, or production authority is created by this contract.
