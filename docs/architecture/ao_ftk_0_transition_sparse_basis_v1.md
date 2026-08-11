# AO-FTK-0 — Transition Sparse Basis Freeze v1

**Slice:** `AO-FTK-0`  
**Name:** `BOTTLENECK_OR_TRANSITION_SPARSE_BASIS`  
**Contract:** `FundamentalTransitionKernelContractV1`  
**Kernel:** `AO_FTK_0_TRANSITION_SPARSE_BASIS_V1`  
**Date:** 2026-08-12  
**Spec:** `v1.0`  
**Status:** `PREOPEN_FREEZE_READY_FOR_LATER_CHARGED_DEVELOPMENT_READ`  
**Science mode:** `PRE-RESULT / PRE-OPEN`  
**Role:** `SHADOW_RESEARCH / RESEARCH_ONLY`  
**financial_alpha_evidence:** `0`  
**capital authority:** `NONE`  
**outcome_open_authorized:** `false`  
**runnable_evaluation:** `false`  
**qm_terms_forbidden:** `true`

Machine freeze: `docs/architecture/ao_ftk_0_transition_sparse_basis_v1.json`

---

## Constitution

> **Q/M is terminal under current admitted custody. AO-FTK-0 freezes a sparse inventory/margin transition basis only.**  
> Full W3 and abstention remain law. No outcomes, no capital, no Q/M composites, no invented fundamentals.  
> Success is a preregistered pre-open contract — not alpha, not a leaderboard, not gate-filling theater.

---

## 0. Why this freeze exists

Under admitted S0 + W3 custody, numeric Q failed to bind (`Q_SOURCE_BLOCKED_TERMINAL` at commit `9dfe9e9`). ROIC is unavailable; inventing Q / Rule100 bridges is forbidden.

**Superseded (do not resume as next work):**

- ordinary OK-SBI-0 S0 “continue Q bind”
- fill 20 OK-SBI evaluation gates for optics
- Q / M⊥ / Q+M⊥ leaderboard or S2 open

**This freeze** preregisters a non-Q/M sparse Reality/transition kernel using already admitted inventory / operating-margin dynamics under `OpportunityKernelV1` and full-W3 law.

---

## 1. Hypothesis

```text
H0: A 1–2 effective-DOF Reality/transition kernel can identify a reproducible
    conditional state transition from inventory and/or operating-margin dynamics
    that is decision-relevant for sparse opportunity discovery.
```

**Not the hypothesis:**

- “good company = growth + ROIC”
- “momentum residual after quality”
- “high-dimensional feature soup”
- Q/M residual geometry revival

### Estimand (sensing vs payoff vs policy)

| Layer | Content | This slice |
|---|---|---|
| Sensing | `P(S_{t+1} \| S_t, C_t)` on frozen inventory/margin transition states | Frozen |
| Payoff | Forward net-payoff distribution functionals | Deferred |
| Policy | Sizing / capital | Deferred |

Later evaluation intent (record only; **no run**): good wager / asymmetric opportunity; recall diagnostic only; catastrophe gates required later; full-W3 vs common-support ledgers when authorized.

---

## 2. Explicit non-identity to Q/M

AO-FTK-0 is **not**:

- a Q basis
- a residual-M basis
- a Q/M composite

**Forbidden in FTK kernel API:** `Q`, `M`, `M_perp`, `M⊥`, `Q+M`, `Q×M`, `residual-M`, `ROIC`, `Q_GF`, `Rule100`.

**Allowed surface:** `kernel_id`, `node_id`, `operator_id`, `applicability_status`, `abstention`, `prediction_direction`, `primitive_id`, `missingness_reason`.

Q track remains:

```text
Q_SOURCE_STATUS      = Q_SOURCE_BLOCKED_TERMINAL
Q_SOURCE_RECEIPT     = 9dfe9e9 / docs/context/e2e_evidence/ok_sbi_0_q_source_bind_attempt_20260812.json
OK_SBI_S2            = NOT_AUTHORIZED
QM_REVIVAL_IN_FTK    = FORBIDDEN
Q_AMENDMENT_STATUS   = AVAILABLE_UNSPENT (future OK-SBI-0-Q-CUSTODY-ADMIT-1 only)
```

Park receipt: `docs/context/e2e_evidence/qm_track_parked_terminal_20260812.json`

---

## 3. Primitive map (admitted S0 only)

| primitive_id | Field | Bind | Role |
|---|---|---|---|
| `FTK_PRIM_IQ_PERIOD_END` | `IQ_PERIOD_END` | BOUND | FQ0 period-change detector / period identity |
| `FTK_PRIM_IQ_TOTAL_REV` | `IQ_TOTAL_REV` (field key `329288`) | BOUND | Ratio denominator only; **not** a decision node |
| `FTK_PRIM_IQ_INVENTORY` | `IQ_INVENTORY` | BOUND | Inventory node numerator |
| `FTK_PRIM_IQ_OPER_INC` | `IQ_OPER_INC` | BOUND | Margin node numerator |

### Bind law (all primitives)

- **Provider:** `SPCIQPRO:SPG_PRODUCTQUERY_EXISTING_WEB_SESSION` (existing admitted S0 corpus; **no new provider**)
- **Identity:** `CIQSEC` only; trading_item joint key **not required** for fundamental transition nodes; ticker/entity/PERMNO fallback **FORBIDDEN**
- **Periods:** `FQ0..FQ-4` Original filing; first FQ0 baseline-only; no bridge across missing probes
- **PIT:** `CONSERVATIVE_END_OF_REQUESTED_AS_OF_DATE_UTC`
- **Units:** `USD_THOUSANDS` for financial metrics
- **Restatement:** `FilingVer=Original`; never overwrite prior PIT vintage
- **Source receipt:** `structured_transitions.receipt.json` SHA-256 `2d0400e2d1a4cd6f90b1982c9159fc9f128c56950843f43599dd71c54a0a1f4f`
- **Raw object:** `structured_transitions.csv` SHA-256 `a5b873826c9598d33c71cc1e28f44f4ce26512a9c89aa6685f2a1606e9be0b87`
- **No-bridge proof:** admitted S0 metrics only; no Rule100; no invented ROIC/Q; no outcome join

### Lawful derived levels

```text
inventory_to_revenue     = IQ_INVENTORY / IQ_TOTAL_REV
inventory_economic_level = -(inventory_to_revenue)   # +delta = normalization
operating_margin         = IQ_OPER_INC / IQ_TOTAL_REV
```

Ratio law (from S0 structured request):

```text
SAME_RELATIVE_PERIOD_AND_PERIOD_END
SAME_USD_THOUSANDS_UNIT
REVENUE_MUST_BE_POSITIVE
else UNOBSERVED; NO_IMPUTATION
```

### Parked / unbound (not decision surface)

| Object | Status | Reason |
|---|---|---|
| `IQ_CAPEX_BNK` | PARKED_NON_DECISION | Cycle evidence only, not capacity-state truth |
| Revenue direction node | PARKED | Diagnostic: no low-freedom dynamics survivor |
| `ROIC` | UNBOUND_FORBIDDEN_INVENTION | Q terminal block |

---

## 4. Operator family (1–2 effective DOF)

### Frozen decision surface

| Slot | operator_id | Node | Formula |
|---|---|---|---|
| DOF 1 | `INV_DELTA_MEAN_REVERSION` | `INVENTORY_CHANNEL_STATE` | `-sign(e0 − e1)` on inventory economic level → next-PIT inventory economic delta sign |
| DOF 2 | `MARGIN_M1_STATE_MEAN_REVERSION` | `MARGIN_CASH_STATE` | `-frozen_M1_continuous_state_prediction(margin)` → next-PIT operating-margin direction; **M1 bytes unchanged** |

```text
effective_decision_dof_frozen = 2
max_effective_decision_dof    = 2
```

### Routing (domain-limited ex ante)

```text
Inventory node → INV_DELTA_MEAN_REVERSION only
Margin node    → MARGIN_M1_STATE_MEAN_REVERSION only
No post-hoc operator search
No free composite trophy across nodes without new slice_id
No fit / threshold grid without search-budget charge
```

### Parked alternates (not decision surface)

`INV_M0_STATE_MEAN_REVERSION`, `INV_M1_STATE_MEAN_REVERSION` remain historical-diagnostic alternates. Promoting either adds DOF / search debt and requires a **new slice_id**.

### Historical diagnostic role (not alpha)

S0 dynamics diagnostic v2 (`data/prebreakout/analysis/econphysics_s0_economic_dynamics_diagnostic_v2.json`) reported node-specific survivors on inventory and margin. That corpus is **HISTORICAL DIAGNOSTIC ONLY** — not re-tuned confirmation and not financial alpha evidence.

---

## 5. Applicability / missingness / NOT_APPLICABLE

| Status | Meaning |
|---|---|
| `W3_INELIGIBLE` | Not in full-W3 date-local eligible set |
| `NOT_APPLICABLE` | Economic non-claim for the node (not missingness; not cash-drag story) |
| `APPLICABLE_OBSERVED` | Node applies and lawful PIT inputs exist |
| `APPLICABLE_UNOBSERVED` | Node applies but unobserved → **ABSTAIN** |

Abstention payload:

```text
forecast        = ABSTAIN
selected        = false
risky_weight    = 0
removed_from_denominator = false
```

Coverage is status-stratified when later evaluated. Coverage PASS/FAIL as eligibility rewrite is **FORBIDDEN**. Complete-case denominator is **FORBIDDEN**. Security/peer return imputation is **FORBIDDEN**.

---

## 6. Full-W3 / abstention law (reuse AO-K0A; do not rewrite)

```text
denominator = PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1
missingness = persistent ABSTENTION (never eligibility rewrite)
residual capital semantics (later) = ECONOMIC_CASH
opportunity comparator (later)    = PIT-EW full W3
```

Authority references:

- `docs/architecture/orthogonalization_contract_v1.md`
- `docs/architecture/ao_k0a_orthogonal_basis_preflight_v1.json`
- `docs/architecture/asymmetric_opportunity_constitution_v1.md` (`OpportunityKernelV1`)

---

## 7. Falsifiers

1. **F1** — Inventory operator unstable under later preregistered fold law  
2. **F2** — Margin operator unstable under full-W3 abstention burden  
3. **F3** — Kernel “works” only after outcome-driven threshold/operator rescue  
4. **F4** — Denominator rewrite / coverage PASS-FAIL eligibility  
5. **F5** — Q/M / ROIC / Rule100 smuggling into FTK API  
6. **F6** — Later asymmetry evaluation shows unacceptable catastrophe burden  

---

## 8. Search budget + complexity ledger

```text
complexity_unit                 = effective_DOF + charged_search_debt
effective_decision_dof_frozen   = 2
hard_material_trials_total      = 3
material_trials_charged_here    = 0
material_trials_remaining       = 3
one_standard_error_preference   = true
simplicity_preference_on_tie    = LOWER_EFFECTIVE_DOF
free_threshold_grid             = FORBIDDEN
rescue_redesign_w/o new slice   = FORBIDDEN
```

This freeze charges **zero** material trials.

---

## 9. Development-label custody plan (plan only — NO join)

```text
join_authorized      = false
join_performed       = false
outcome_inspected    = false
sensing_horizon      = NEXT_PIT_STRUCTURED_TRANSITION
payoff_horizon_*     = BLOCKED_UNSET
right_tail_definition= BLOCKED_UNSET
catastrophe_definition = BLOCKED_UNSET
seal_status          = PLAN_ONLY_UNSEALED
```

Planned pack path roots (not created/joined this turn):

```text
data/prebreakout/compiled/ao_ftk_0_label_custody/development_label_pack.plan.json
data/prebreakout/compiled/ao_ftk_0_label_custody/prospective_label_pack.plan.json
```

Hash procedure: content-address planned schema + row-key set + decision-date list + label-source receipt; seal as `SEALED_UNJOINED` only after owner binds numeric cuts. **Never open or join in AO-FTK-0.**

---

## 10. OpportunityKernelV1 field freeze

| Field | Value |
|---|---|
| kernel_id | `AO_FTK_0_TRANSITION_SPARSE_BASIS_V1` |
| entry_mode | `CONTINUATION` |
| observable_representation | inventory economic-level lag-1 delta + operating-margin M1 continuous state |
| target | next-PIT inventory normalization and/or operating-margin direction (sensing); payoff deferred |
| horizon | sensing = next-PIT; payoff = `BLOCKED_UNSET` |
| rationale_class | `MECHANISTIC` |
| simple_comparator | PIT-EW full W3 (later) |
| upside_channel | conditional improved inventory/margin regime prior to market recognition |
| downside_failure_mode | false transition; noise; catastrophe left-tail |
| hard_falsifier | F1–F6 |
| applicability_abstention | four-status taxonomy above |
| pit_source_contract | admitted S0 + immutable W3 date-local authority |
| search_cost_trial_identity | one material trial debit against remaining budget |

---

## 11. Stop-lines

```text
NEW_WINNER_OR_FUTURE_OUTCOME_OPEN
W6_LOCKBOX_OR_PROSPECTIVE_OUTCOME_JOIN
OK_SBI_S2_OR_QM_TROPHY
INVENT_ROIC_OR_Q_GF
RULE100_FEATURE_STORE_BRIDGE
TICKER_ENTITY_PERMNO_FALLBACK
SPEND_Q_AMENDMENT_INSIDE_AO_FTK_0
FILL_OK_SBI_20_GATES_FOR_OPTICS
SECOND_MATERIAL_REDESIGN_WITHOUT_NEW_SLICE_ID
K_TUNING_PORTFOLIO_OPTIMIZATION_CAPITAL_PAPER
PARENT_CHILD_MUTATION_A2_REQUERY
VSB_UNPARK
TREAT_DIAGNOSTIC_SURVIVORS_AS_ALPHA
FULL_ENDGAME_REWRITE
FOURTH_EVIDENCE_CLOCK
```

If asked to “just run the backtest”:

```text
STATE = PRE-OPEN FREEZE ONLY
runnable_evaluation = false
outcome_open_authorized = false
```

---

## 12. Exit criteria for later charged development read

Owner must issue a **new slice_id** that:

1. Authorizes charged development read explicitly  
2. Binds or retains `BLOCKED_UNSET` for label cuts  
3. Debits search budget before first material trial  
4. Preserves full-W3 abstention law  
5. Keeps Q/M revival forbidden unless separately authorized  
6. Leaves `outcome_open_authorized=false` until explicit carve-out  

---

## 13. Terminal pre-open verdict

```text
READY_FOR_LATER_CHARGED_DEVELOPMENT_READ
```

Primitives bound; operators frozen at 2 DOF; falsifiers + search budget frozen; label custody plan-only; no outcome open; financial_alpha_evidence=0.
