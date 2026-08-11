# AO-FTK-1 — L0–L2 Representation / SNR Preflight

**Slice:** `AO-FTK-1-20260812`  
**Name:** `FTK_CHARGED_DEV_PREP_L0_L3`  
**Date:** 2026-08-12  
**Role:** `SHADOW_RESEARCH / RESEARCH_ONLY`  
**Science mode:** `CHARGED_DEVELOPMENT_PREP` (not product; not capital)  
**Authorized phases this turn:** L0 → L1 → L2 → L3 only  

Machine: `docs/architecture/ao_ftk_1_20260812_l0_l3_preflight.json`

---

## Inheritance

| Item | Value |
|---|---|
| Parent freeze | AO-FTK-0 @ `6832066` |
| Parent close | `15613f3` CLOSED / NO_WORKER |
| Parent verdict | `READY_FOR_LATER_CHARGED_DEVELOPMENT_READ` |
| Kernel | `AO_FTK_0_TRANSITION_SPARSE_BASIS_V1` |
| Material trials remaining | 3 (unchanged; **0 charged this slice**) |
| Labels joined | **false** |
| Outcome open | **false** |
| Alpha evidence | **0** |

AO-FTK-0 is **not** reopened as a worker. Outcomes remain sealed.

---

## L0 — Question (locked)

> A representation of the frozen 1–2 DOF inventory/margin transition kernel that survives R1–R8 can distinguish a real weak next-PIT transition signal from noise under full-W3 abstention burden.

**Not** the hypothesis: growth+ROIC quality; Q/M residual geometry; high-dimensional feature soup; diagnostic survivors = alpha; MU/SNDK smoke = success.

---

## L1 — Causal / authority model (confirm only)

```text
kernel_id          = AO_FTK_0_TRANSITION_SPARSE_BASIS_V1
rationale_class    = MECHANISTIC
entry_mode         = CONTINUATION
comparator_later   = PIT_EQUAL_WEIGHT_FULL_W3
policy / capital   = DEFERRED
```

No primitive search reopen. No replacement of inventory/margin with a “more promising” basis.

| Slot | Operator | Node |
|---|---|---|
| DOF1 | `INV_DELTA_MEAN_REVERSION` | `INVENTORY_CHANNEL_STATE` |
| DOF2 | `MARGIN_M1_STATE_MEAN_REVERSION` | `MARGIN_CASH_STATE` |

---

## L2 — Observation contract / SNR preflight

### Representation vectors under test

1. **Inventory continuous lag-1 delta**  
   `inventory_economic_level[FQ0] − inventory_economic_level[FQ-1]`  
   with `inventory_economic_level = −(IQ_INVENTORY / IQ_TOTAL_REV)`.  
   Decision prediction remains `−sign(delta)`; **continuous magnitude is retained for SNR** (anti D4 under-sensing).

2. **Margin M1 continuous state**  
   Frozen M1 continuous state on `operating_margin = IQ_OPER_INC / IQ_TOTAL_REV`.  
   M1 implementation bytes mutation **FORBIDDEN**. Continuous encoding retained deliberately from FTK-0.

### Sensing targets

| Target | Node | Horizon |
|---|---|---|
| Next-PIT inventory normalization direction | inventory | `NEXT_PIT_STRUCTURED_TRANSITION` |
| Next-PIT operating-margin direction | margin | `NEXT_PIT_STRUCTURED_TRANSITION` |

Payoff / right-tail / catastrophe remain `BLOCKED_UNSET`.

### Applicability stratification

`W3_INELIGIBLE` | `NOT_APPLICABLE` | `APPLICABLE_OBSERVED` | `APPLICABLE_UNOBSERVED→ABSTAIN`

Services / non-inventory firms: **NOT_APPLICABLE or abstain** — never rewrite denominator.

### Missingness → abstention

Unobserved / nonpositive revenue / unit-period incompatibility → `selected=false`, `risky_weight=0`, **not** removed from W3 denominator.

### Peer / common-mode (R3 plan)

- Margin: inherit frozen M1 `pit_peer_residual` continuous state (no re-fit).  
- Inventory: continuous economic-level delta primary; optional XS demean of continuous inventory/revenue is **common-mode control only**, not a third DOF.  
- No security/peer return imputation.

### Explicit non-actions this turn

- Material trial **not** debited  
- Labels **not** joined  
- No Q/M tokens  
- No free threshold grid  
- No charged RUN

### Historical diagnostic context only

S0 dynamics + M0/M1 shootout are **HISTORICAL DIAGNOSTIC ONLY** (not retune confirmation; not alpha). They motivate continuous M1 retention and full-W3 abstention burden awareness; they do **not** establish financial_alpha_evidence.

---

## Next in this slice

L3 Representation Sufficiency Gate (R1–R8) → disposition receipt.  
Passing L3 does **not** authorize L5.
