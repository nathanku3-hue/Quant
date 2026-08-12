# ALPHA_SCIENTIFIC_METHOD_v1

**Status:** `LOCKED / RESULT_FIRST_FORWARD_GATE_AMENDED_20260812`
**Date:** 2026-08-12
**Type:** Process constitution (not a model freeze)
**Machine state:** `docs/context/research_loop_state_current.json`
**Human pointer:** `docs/context/RESEARCH_LOOP.md`

Models, kernels, and formulas may die. **This process does not.**

---

## 1. Purpose

Lock how any Alpha / OpportunityKernel experiment earns the right to spend trial budget and how every RUN is diagnosed — so agents can self-identify **phase** and **next** without rereading chat history.

This constitution absorbs:

- S0 M0/M1 `NO_EXTRACTION_LIFT` lesson (representation under-sensing)
- Layered failure routing (custody → … → economics)
- Anti-overfit **and** anti-under-sensing
- External patterns: experiment recording (Qlib-like), research/live parity (LEAN-like), temporal leakage control (mlfinlab-like), multiple-testing discipline (PBO/DSR-like)
- **Plus** Representation Sufficiency Gate (this repo’s missing fifth)
- **Plus** the locked result-first / forward-gate amendment in `docs/architecture/result_first_ai_research_loop_v1.md`

### 1.1 Result-first forward-gate amendment — 2026-08-12

This method is now explicitly **result-first**, where result means a decision-changing scientific/operating terminal, not PnL. The canonical L0–L11/P1–P4 enums remain unchanged, but no phase completion automatically authorizes the next expensive phase.

Hard law:

```text
DECISION_TO_CHANGE before implementation
+ PASS_ROUTE / FAIL_ROUTE / UNRESOLVED_ROUTE preregistered
+ CHEAPEST_DISCRIMINATING_TEST
+ WHY_NO_CHEAPER_TEST_EXISTS

if all terminal routes are the same
→ DECISION_VALUE = 0
→ DO_NOT_RUN
```

`L4_EMPIRICAL_FREEZE → READY_FOR_L5_CANDIDATE`, never automatic `L5_RUN`. Before a scarce L5 read, lawful READY candidates compete across families for research capital; `READY_BUT_NOT_PRIORITY` is legal.

Canonical machine preflight=`docs/architecture/opportunity_kernel_scientific_preflight_v2.json`. Ex-ante action feasibility, when applicable, is separately governed by `docs/architecture/execution_feasibility_v1.json`.

This amendment is forward-only. Historical freezes/runs/diagnoses remain immutable under their pinned contract versions.

### 1.2 Constitution vs runtime (do not conflate)

```text
AI_NATIVE_RESEARCH_CONSTITUTION     = LOCKED
AI_NATIVE_DECISION_SEMANTICS        = LOCKED
FAMILY_LEVEL_FIRST_FAIL (FTK)       = IMPLEMENTED
UNIVERSAL_PREFLIGHT_ENFORCEMENT     = NOT_IMPLEMENTED
CROSS_FAMILY_RDV_ALLOCATOR          = NOT_IMPLEMENTED
AI_NATIVE_QUANT_RESEARCH_RUNTIME    = PARTIAL
```

Machine status + ranked post-lock Golden Questions:

```text
docs/architecture/ai_native_runtime_status_v1.json
docs/architecture/ai_native_runtime_closure_audit_20260812.md
```

Scientific phase IDs remain the L0–L11 / P1–P4 namespace below. **Do not rename** scientific `L5_RUN` to `SCIENCE_S5`.

D1→D9 status split:

```text
D1_D9_CONSTITUTION        = LOCKED
D1_D9_FTK_IMPLEMENTATION  = IMPLEMENTED
D1_D9_UNIVERSAL_RUNNER    = NOT_IMPLEMENTED
```

---

## 2. Canonical loop (enum names)

Agents **must** use these phase IDs:

```text
L0_QUESTION
L1_CAUSAL_MODEL
L2_OBSERVATION_CONTRACT
L3_REPRESENTATION_SNR          # mandatory before expensive RUN
L4_EMPIRICAL_FREEZE
L5_RUN
L6_LAYERED_DIAGNOSIS
L7_ROADMAP_DECISION
L8_BOUNDED_REFINEMENT
L9_REQUALIFY_IF_REP_TOUCHED   # if L3 inputs changed → back through L3
L10_REFREEZE
L11_RUN_AGAIN                 # returns to L5 under new freeze

# After lockbox / prospective only (one-way):
P1_PROSPECTIVE_RUN
P2_MATURE
P3_EVALUATE
P4_PROMOTE_OR_KILL
```

### Flow

```text
L0 → L1 → L2 → L3 → L4 → [E7.5 RDV / OWNER L5 GATE] → L5 → L6 → L7
                              ↓
                    (if redesign allowed)
                         L8 → L9? → L10 → L4 → [E7.5 GATE] → L5 …

After W6 / prospective seal:
  P1 → P2 → P3 → P4   (no adaptive redesign back into same version)
```

---

## 3. Layered diagnosis order (every empirical RUN)

Fixed order. **Stop at first true failure layer.** Later layers are undefined if earlier failed.

```text
D1_CUSTODY_PIT
D2_DATA_OBSERVABLE
D3_MEASUREMENT_POWER
D4_REPRESENTATION_SNR
D5_MECHANISM_SELF_TRANSITION
D6_SELECTION_ENRICHMENT
D7_CONFIRMATION_TIMING
D8_HOLD_EXIT_CONVEXITY
D9_ECONOMICS_COST_CAPACITY
```

### Information-gain rule

Every RUN receipt must answer not only PASS/FAIL but:

```text
what information was gained vs prior representation / null
which single layer may be changed next
what is forbidden to change
```

### Failure routing (one layer only)

```text
DATA_FAILURE
REPRESENTATION_FAILURE
MECHANISM_FAILURE
EXPECTATION_GAP_FAILURE
SELECTION_FAILURE
CONFIRMATION_FAILURE
HOLD_EXIT_FAILURE
EXECUTION_FAILURE
STOP_TRACK
NEW_OBSERVABLE_SURFACE
```

---

## 4. Representation Sufficiency Gate (L3) — mandatory checklist

Before expensive capture / trial spend / winner labels:

```text
R1 magnitude_monotonicity
R2 weak_signal_sensitivity
R3 peer_common_mode_rejection
R4 async_causal_sequence_retention
R5 staleness_degradation
R6 missingness_confidence_monotonicity
R7 conflicting_evidence_retention
R8 abstention_vs_deletion
R9 perturbation_fabrication_tolerance
```

R9 is additive and versioned. Historical `R1–R8` receipts remain valid under their original L3 contract version. Future `L3_R1_R9_V2` work uses source-bound, outcome-blind stress only:

```text
R9A numeric       = source measurement / quantization tolerance
R9B temporal      = lawful availability delay; cut crossing → UNOBSERVED → ABSTAIN
R9C threshold     = local frozen-cut stress only; no grid
R9D missingness   = PRESENT → UNOBSERVED; denominator immutable
```

Future result-bearing kernels also declare the clock/state coordinate in L2, with L3→L4 enforcing that availability, economic-state and action clocks are not conflated. Observability-selection bias is diagnostic/report-only and may route `SIMPLIFY / REVISE_WITHIN_FREEZE / BLOCK`; it may never reweight candidates, repair missing names, or shrink the opportunity denominator.

**Gate question:**

> If the hypothesized weak transition were real, would this representation still distinguish it from noise?

Sign-only / premature quantization risk is caught here — not after 310k requests.

---

## 5. Dual invariant (non-negotiable)

```text
         representation power ↑
                        useful science │ dangerous flexibility
                                       │
         ──────────────────────────────┼──────────────→ degrees of freedom
                                       │
                        under-sensing  │ overfit
```

**Bottom-left is not good research.** Anti-overfit without anti-under-sensing is incomplete.

---

## 6. What each phase returns (not CAGR / MU-SNDK by default)

| Phase | Required return |
|---|---|
| L0–L3 pre-open | contract + gate verdict (`READY_*` / `*_BLOCKED`) |
| L4 EMPIRICAL FREEZE | immutable freeze + `READY_FOR_L5_CANDIDATE` or block; **never L5 authorization by itself** |
| E7.5 research allocation | ordinal RDV comparison across lawful READY candidates; may return `READY_BUT_NOT_PRIORITY` |
| L5 RUN | separately authorized immutable run receipt + metrics under freeze |
| L6 | layered diagnosis table + first fail layer + info-gain |
| L7 | single next-dollar route |
| P3 | clock-law evaluation only |
| Smoke (MU/SNDK class) | zero-weight only; never primary success |

CAGR / Sharpe only if explicitly preregistered as secondary functionals after cost law.

---

## 7. Authority split

```text
PROCESS authority     = this method + result_first_ai_research_loop_v1.md + research_loop_state_current.json
MACHINE preflight     = opportunity_kernel_scientific_preflight_v2.json
CAPTURABILITY preflight = execution_feasibility_v1.json (action-bearing trigger only)
PRODUCT authority     = Clock #1 / runtime / capital (separate)
FAMILY contracts      = CRV1, Sector, FTK, OK-SBI, … (die without killing process)
```

---

## 8. Agent self-identification protocol (harness)

When user asks **“which phase / what’s next”**:

1. Read **only** `docs/context/research_loop_state_current.json` first
2. Optionally confirm pointers in `docs/context/RESEARCH_LOOP.md`
3. Answer using fields: `loop_phase`, `next_phase`, `next_worker_slice`, `forbidden_now`, `diagnosis_layer_if_any`
4. Do **not** reconstruct phase from chat alone

Updating state is mandatory at every L4 freeze, L5 run close, L6 diagnosis, L7 decision, and P4 promote/kill.
