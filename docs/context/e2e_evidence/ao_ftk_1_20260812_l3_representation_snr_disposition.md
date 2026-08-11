# AO-FTK-1 — L3 Representation / SNR Disposition

**Slice:** `AO-FTK-1-20260812`  
**Date:** 2026-08-12  
**Phases completed:** L0 → L1 → L2 → L3  
**Disposition:** **PASS**  
**Effective DOF recommendation:** **2**  
**Material trials charged:** **0** (remaining **3**)  
**L5 authorized:** **false** (auto-open: **false**)  
**financial_alpha_evidence:** **0**  
**Labels joined:** **false**  
**Outcome open authorized:** **false**

Machine receipt: `docs/context/e2e_evidence/ao_ftk_1_20260812_l3_representation_snr_disposition.json`  
Preflight: `docs/architecture/ao_ftk_1_20260812_l0_l3_preflight.json`

---

## Why this slice

AO-FTK-0 closed at pre-open freeze (`6832066` / close `15613f3`) with:

- 4 primitives BOUND  
- 2 DOF operators FROZEN  
- full-W3 + abstention law  
- search budget 3 remaining, 0 charged  
- **no** outcome open, **no** material trial, **no** alpha evidence  

This slice does **not** reopen AO-FTK-0 as a worker. It answers the L3 Representation Sufficiency Gate on the inherited surface only.

---

## L0 — Question (locked)

> A representation of the frozen 1–2 DOF inventory/margin transition kernel that survives R1–R8 can distinguish a real weak next-PIT transition signal from noise under full-W3 abstention burden.

Not hypothesized: growth+ROIC; Q/M residual geometry; feature soup; diagnostic survivors as alpha; MU/SNDK as success.

---

## L1 — Inheritance confirmation

| Field | Confirmed |
|---|---|
| `kernel_id` | `AO_FTK_0_TRANSITION_SPARSE_BASIS_V1` |
| `rationale_class` | `MECHANISTIC` |
| `entry_mode` | `CONTINUATION` |
| `comparator_later` | `PIT_EQUAL_WEIGHT_FULL_W3` |
| policy / capital | `DEFERRED` |

Primitives and operators **not** redesigned. Q/M remains terminal/parked. Revenue direction and ROIC remain parked/forbidden.

---

## L2 — Preflight summary

Representation under test (continuous preferred):

1. Inventory economic-level lag-1 **continuous** delta  
2. Operating-margin **continuous** M1 state (bytes frozen)

Applicability: W3 / NOT_APPLICABLE / observed / unobserved→ABSTAIN.  
Denominator: full W3, no complete-case rewrite.  
Sensing horizon: next-PIT structured transition.  
Payoff / right-tail / catastrophe: `BLOCKED_UNSET`.  
Material trial not debited; labels not joined.

Main prior concern addressed: S0 shootout flagged **D4 sign-only under-sensing**. FTK-0 retained continuous M1 and continuous inventory delta as observable representation; L3 evaluates that continuous-preferred encoding, not a pure sign soup.

---

## L3 — R1–R8 disposition table

Gate question (method constitution): *If the hypothesized weak transition were real, would this representation still distinguish it from noise?*

| Gate | Status | Evidence (short) | Notes |
|---|---|---|---|
| **R1** magnitude_monotonicity | **PASS** | FTK-0 `observable_representation`; FTK-1 preflight continuous vectors | Continuous inventory Δ + continuous M1 provide magnitude channels; sign is decision emission only |
| **R2** weak_signal_sensitivity | **PASS** | FTK-0 operators; M1 continuous representation | Continuous scores retain weak transitions that pure sign quantization collapses |
| **R3** peer_common_mode_rejection | **PASS** | Preflight peer plan; M1 `pit_peer_residual` | Margin inherits peer residual; inventory XS demean allowed as control only (not 3rd DOF) |
| **R4** async_causal_sequence_retention | **PASS** | Primitive FQ grid + operator lag-1 formulas | Adjacent advancing FQ0 sequence retained; M1 temporal accumulation preserved |
| **R5** staleness_degradation | **PASS** | Primitive PIT / lag law | Conservative EOD as-of; Original filing; no intra-day bridge |
| **R6** missingness_confidence_monotonicity | **PASS** | Applicability + abstention law; admission missingness counts | Missing → ABSTAIN weight 0; no imputation; inventory missingness does not rewrite eligibility |
| **R7** conflicting_evidence_retention | **PASS** | Domain-limited routing; M1 `mixed_evidence_zeroed=false` | Two nodes may disagree without forced zeroing or free composite trophy |
| **R8** abstention_vs_deletion | **PASS** | Denominator + applicability taxonomy | Full W3; abstain without row deletion; NOT_APPLICABLE ≠ deletion |

**first_fail_R_if_any:** `null`

---

## Disposition rationale

**PASS** — Representation is adequate for a later charged development read under the frozen FTK-0 surface.

- Continuous sensing vectors are already part of the inherited freeze’s observable representation.  
- Inventory decision surface uses `−sign(delta)`, but L3 requires (and preflight records) continuous magnitude retention for SNR — preventing pure sign-only under-sensing as the evaluation representation.  
- Margin DOF is continuous M1 by freeze; addresses the prior D4 flag without new primitives.  
- Full-W3 abstention law satisfies R6/R8 structurally.  
- **SIMPLIFY** not selected: no charged-read indistinguishability evidence forces collapse to 1 DOF; simplicity preference applies on later empirical tie.  
- **REVISE_WITHIN_FREEZE** not required: continuous-vs-quantized sensing encoding is already bounded inside freeze authority.  
- **BLOCK** not selected: structural SNR pathway exists without inventing Q/M or a third DOF.

Passing L3 is **not** alpha evidence and **not** L5 authorization.

---

## Recommended next (owner)

```text
next_phase_recommendation = L4_CHARGED_SLICE_FREEZE
effective_dof_recommendation = 2
l5_authorized               = false
l5_auto_open                = false
material_trials_remaining   = 3
```

**Owner action:** authorize a separate L4 charged-slice freeze (then, only with further authorization, L5 RUN with material trial debit + sealed labels).

There is **no** automatic L3/L4 → L5 transition.

---

## Stop-lines honored

No material trial debit; no label join; no outcome open; no Q/M revival; no third DOF; no free threshold grid; no AO-FTK-0 worker reopen; no capital / W6; `financial_alpha_evidence = 0`.

---

## One-line constitution

> Inherit FTK-0. Answer L3. Debit nothing. Join nothing. Passing SNR is not a license to open outcomes — only a license to ask the owner for L4/L5.
