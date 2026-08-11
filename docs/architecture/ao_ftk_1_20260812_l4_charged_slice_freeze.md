# AO-FTK-1 — L4 Charged-Slice Freeze

**Slice:** `AO-FTK-1-20260812`  
**Name:** `FTK_L4_CHARGED_SLICE_FREEZE`  
**Date:** 2026-08-12  
**Spec:** `v1.0`  
**Role:** `SHADOW_RESEARCH / RESEARCH_ONLY`  
**Science mode:** `CHARGED_SLICE_FREEZE` (custody + preregistration only)  
**Status:** `L4_FREEZE_READY_WAITING_OWNER_L5`  
**Owner decision this turn:** `L4_AUTHORIZE`  
**L5 authorized:** `false`  
**financial_alpha_evidence:** `0`

Machine freeze: `docs/architecture/ao_ftk_1_20260812_l4_charged_slice_freeze.json`

---

## Constitution

> **L4 freezes the passed 2-DOF candidate and the debit/join locks.**  
> It does not spend the trial, open labels, or claim alpha.  
> **Stop at WAIT_OWNER_L5.**

---

## Why this phase exists

| Gate | Meaning |
|---|---|
| L3 PASS | Permits preparation of a charged read |
| **L4 (this)** | Freezes the charged-read candidate (custody + preregistration) |
| L5 | The charged read itself — **separate owner authorization required** |

**Already true (do not re-litigate):**

- L0–L3 complete; L3 disposition = **PASS** at `effective_dof = 2` (commit `28aa0f1`)
- Parent freeze AO-FTK-0 @ `6832066` (CLOSED / NO_WORKER)
- `material_trials_charged = 0` / remaining = 3
- Q/M = `Q_SOURCE_BLOCKED_TERMINAL`; S2 off
- Clock #1 sealed; capital path CLOSED; W6 UNTOUCHED

L4 creates **no** Alpha claim, **no** label access, **no** trial debit, **no** capital authority.

---

## Frozen contract (binding)

### Identity / lineage

```text
slice_id                 = AO-FTK-1-20260812
parent_freeze_commit     = 6832066
l3_disposition_commit    = 28aa0f1
l3_disposition           = PASS
effective_decision_dof   = 2   # FROZEN charged-read candidate
kernel_id                = AO_FTK_0_TRANSITION_SPARSE_BASIS_V1
```

### Representation (2 DOF — no silent collapse, no third DOF)

| Node | Sensing vector | Decision emission |
|---|---|---|
| Inventory | continuous lag-1 inventory economic-level delta | `-sign(delta)` via `INV_DELTA_MEAN_REVERSION` |
| Margin | continuous operating-margin M1 state | frozen M1 continuous prediction via `MARGIN_M1_STATE_MEAN_REVERSION` |

- Continuous preferred over sign-only scores for SNR.
- Sign is inventory **emission only**; continuous magnitude retained for sensing.
- M1 operator bytes = **FROZEN**; mutation **FORBIDDEN**.

### Operators

| Slot | Operator | Bytes | Immutability pin (sha256) |
|---|---|---|---|
| 1 | `INV_DELTA_MEAN_REVERSION` | FROZEN | `9434b495…0fdd85` |
| 2 | `MARGIN_M1_STATE_MEAN_REVERSION` | FROZEN (M1 mutation FORBIDDEN) | `a464058d…b633cd` |

**Routing:** `DOMAIN_LIMITED_EX_ANTE` — no free composite trophy, no post-hoc operator hunt.

### Material-trial debit plan (plan only — **0 charged**)

```text
plan_id                    = FTK1_TRIAL_DEBIT_PLAN_V1
hard_material_trials_total = 3
current_charged            = 0
remaining                  = 3
next_debit                 = 1
debit_trigger              = L5_AUTHORIZATION_RECEIPT only
free_threshold_grid        = FORBIDDEN
uncharged_adaptive_search  = FORBIDDEN
```

### Label custody — three states

| State | L4 requirement |
|---|---|
| `LABEL_IDENTITY_FROZEN` | YES — frozen |
| `LABEL_HASH_PROCEDURE_FROZEN` | YES — frozen |
| `LABEL_BYTES_JOINED` | **NO** — must remain false |

Paths (identity + hash only; **no joined parquet/outcomes**):

- `data/prebreakout/compiled/ao_ftk_1_20260812_label_custody/development_label_pack.identity.json`
- `data/prebreakout/compiled/ao_ftk_1_20260812_label_custody/development_label_pack.hash_procedure.json`

`seal_status` = `IDENTITY_AND_HASH_FROZEN_UNJOINED`

### Economic cuts (sensing-first L4)

```text
payoff_horizon_primary   = BLOCKED_UNSET
payoff_horizon_secondary = BLOCKED_UNSET
right_tail_definition    = BLOCKED_UNSET
catastrophe_definition   = BLOCKED_UNSET
```

Do **not** invent defaults. These must freeze before any asymmetry / economics / deployability claim.

### Authority flags

```text
runnable_evaluation      = false
l5_authorized            = false
l5_auto_open             = false
capital_authority        = false
financial_alpha_evidence = 0
qm_terms_forbidden       = true
```

---

## Fail-closed mechanical guards

When `l5_authorized == false`:

| Call | Result |
|---|---|
| `label_join()` | **FAIL CLOSED** |
| `trial_debit()` | **FAIL CLOSED** |
| `evaluator.run()` | **FAIL CLOSED** |

Implementation: `research/asymmetric_opportunity_v1/ao_ftk_1_l4_contract.py`  
Tests: `tests/asymmetric_opportunity_v1/test_ao_ftk_1_l4_charged_slice_freeze.py`

---

## DOF discipline

- `effective_decision_dof = 2` is the **frozen charged-read candidate**.
- Silent collapse to 1 DOF → invalidates accepted L3 receipt → **FORBIDDEN**.
- Adding a third DOF → exceeds frozen search surface → **FORBIDDEN**.
- 1-vs-2 re-search → uncharged adaptive search → **FORBIDDEN**.
- Later redundancy of one component = **L6 first-fail / info-gain AFTER authorized L5**, not a pre-read rewrite.

---

## What L4 is not

- Not L5 execution
- Not a material trial debit
- Not label byte join / outcome open
- Not alpha evidence
- Not capital / W6 / Q revival
- Not auto L3→L5 or L4→L5

---

## What ends L4

Exactly one of:

1. **L4_FREEZE_PASS** → state = `WAIT_OWNER_L5` (this receipt path)
2. **L4_HOLD / STOP_OR_PARK** → only if owner explicitly overrides
3. **L4_CUSTODY_DEFECT_BLOCK** → honest stop; no evaluator run as escape hatch

L4 must **never** end through an implicit evaluator run.

---

## Before any future L5 (not this freeze)

Requires **all** of:

1. Separate owner L5 authorization receipt  
2. Material trial debit of exactly **1** recorded  
3. Sealed label identity honored + join authorized for that one read  
4. `runnable_evaluation = true` only for that authorized read  
5. L4 freeze PASS still binding (no silent redesign)  
6. Outcome open only under that receipt’s law  

After L5: L6 first-fail (D1→D9) + info-gain → L7 owner next-dollar.  
No unconstrained run → diagnose → refine → run.

---

## Next owner action

```text
authorize L5 | hold | stop
(never silent L5)
```
