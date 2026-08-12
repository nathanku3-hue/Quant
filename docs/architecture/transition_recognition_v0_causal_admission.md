# TRANSITION_RECOGNITION_v0 — Causal Admission (L0/L1 Frozen)

**Status:** `ADMITTED_L1_FROZEN / NO_TRIAL`  
**Slice:** `TR-v0-G0-G2-ADMISSION-1`  
**Date:** `2026-08-12`  
**Next phase:** `L2_OBSERVATION_CONTRACT`  
**Financial alpha evidence:** `0`  
**Capital authority:** `NONE`

Machine admission receipt: `docs/context/e2e_evidence/tr_v0_g0_g2_admission_1.json`  
Machine L0/L1 freeze: `docs/architecture/transition_recognition_v0_l0_l1_freeze.json`

---

## 1. Family boundary

`TRANSITION_RECOGNITION_v0` is admitted only as a **conditional selection bridge**.

```text
CYCLE_RESONANCE_v1
= broad ordered-cycle mechanism
= supply/capacity -> inventory -> pricing -> margin -> revisions -> expectation gap
= 252-trading-day right-tail family

TRANSITION_RECOGNITION_v0
= GIVEN a real operating transition already exists,
  ask whether recognition lag distinguishes selectable not-yet-recognized
  transitions from already-recognized transitions.
```

TR-v0 does not inherit CRV1's 252-trading-day primary horizon, primary label, broad resonance score, or ordered-clock family contract. A later economic horizon and wager law must be frozen separately before any result-bearing evaluation.

If TR-v0 cannot remain distinct on this basis, falsifier F3 routes it into CRV1 rather than allowing a duplicate family.

---

## 2. L0 — Golden question

> Conditional on a real PIT-observable operating transition, does an independently observable recognition/consensus gap identify which transitions are economically selectable (not-yet-recognized) versus already-recognized?

This is a **selection** question (D6). It is not an entry/confirmation/timing question (D7).

---

## 3. L1 — Causal model

```text
REALITY
  business transition actually occurring, observed PIT-correctly
    |
    v
RECOGNITION STATE
  contemporaneous consensus/expectation state at decision_as_of
    |
    v
RECOGNITION GAP
  Reality has moved farther than contemporaneous recognition
    |
    v
SUBSEQUENT RECOGNITION
  later state transition; not a timing rule here
    |
    v
POTENTIAL SELECTION EDGE
  later D6 economic selection enrichment; not evaluated here
```

The model is intentionally narrow. It does not claim that recognition lag causes every subsequent payoff, and it does not authorize a trading rule.

---

## 4. Node semantics

### REALITY

A PIT-observable operating-transition state established independently of recognition. Lawful transition primitives may be reused to establish Reality, but Reality is **not**:

- FTK K=20 selected-set membership;
- H=63 hold policy;
- a failed FTK payoff or residual state;
- a post-hoc return-conditioned event date.

### RECOGNITION STATE

The latest lawful consensus/expectation state available at `decision_as_of` for permanent security identity.

Candidate measure family, to be bound at L2 only:

```text
EPS_FY1
EPS_FY2
REVENUE_FY1
REVENUE_FY2
EPS_FY1_REVISION_30D
EPS_FY1_REVISION_90D
REVENUE_FY1_REVISION_30D
REVENUE_FY1_REVISION_90D
FORWARD_PE
```

Required PIT law:

```text
security_id = CIQSEC:<Capital IQ Security ID>
available_at <= decision_as_of
latest lawful vintage only
source receipt bound
observed consensus and inferred market-implied state labeled separately
missing required state -> ABSTAIN
```

The existing Alpha PIT expectations schema proves this class of state is definable without returns. L2 must create a TR-v0-specific family/source binding; CRV1 artifacts do not become TR-v0 authority merely because they share the same logical expectation vocabulary.

### RECOGNITION GAP

A relational state: Reality is positive while contemporaneous recognition has not moved commensurately.

The exact normalization, scale alignment, materiality rule, and any required consensus-history window are **not defined here**. They are L2/L3 contract work and must remain outcome-blind.

---

## 5. Frozen hypothesis

**H1** — Among firms exhibiting a real operating transition, future economic selection enrichment under a later preregistered wager law is higher when contemporaneous consensus recognition materially lags the observed transition, versus transitions already recognized.

This is hypothesis text only. No returns, labels, timing rule, threshold, H, K, or economic evaluation is opened by this freeze.

---

## 6. Falsifiers

| ID | Falsifier | Route |
|---|---|---|
| F1 | Recognition cannot be defined independently of future returns | KILL |
| F2 | Recognition is merely another encoding of the same Reality/FTK transition | KILL / not incremental |
| F3 | TR-v0 is materially identical to CRV1 | MERGE / ROUTE CRV1 |
| F4 | Useful recognition state exists only after inspecting failed FTK dates/payoffs | KILL |
| F5 | Mechanism requires H/K/threshold chosen from prior economic residuals | KILL |

These falsifiers are frozen before L2.

---

## 7. Admission contract

```text
G0 = PASS   distinct conditional selector vs broad CRV1
G1 = PASS   recognition state PIT-definable without returns
G2 = PASS   recognition semantically incremental to Reality

TERMINAL = ALL_PASS_ADMIT_L1_FROZEN
NEXT     = L2_OBSERVATION_CONTRACT
DEBIT    = 0
ALPHA    = 0
```

L2 is permitted to bind identity, source, as-of/lag, missingness, consensus-history construction, and the operator that compares Reality with RecognitionState. L2 is **not** permitted to fit from returns, choose economic thresholds, open D7 timing, debit a material trial, or run L5.

---

## 8. Explicit non-goals

```text
no returns / labels / payoff joins
no H/K/threshold search
no feature leaderboard
no D7 timing / "when to buy"
no FTK rescue / failed-date residual fitting
no AO-FTK-2
no capital / alpha claim
no full strategy scaffold
```

**One-line constitution:** Free-kill first: distinct from CRV1, PIT recognition without returns, incremental to Reality. Selection only—not timing, not FTK rescue, not a trial.
