# TR-v0 — G0→G2 Fail-Fast Admission Packet

**Slice:** `TR-v0-G0-G2-ADMISSION-1`  
**Family:** `TRANSITION_RECOGNITION_v0`  
**Role:** `SHADOW_RESEARCH / OUTCOME_BLIND / NO_TRIAL`  
**Date:** `2026-08-12`  
**Terminal:** `ALL_PASS_ADMIT_L1_FROZEN`  
**Next:** `L2_OBSERVATION_CONTRACT`  
**Debit / evals / label join:** `0 / 0 / 0`  
**Timing research:** `false`  
**FTK rescue:** `false`  
**Financial alpha evidence:** `0`

Machine receipt: `docs/context/e2e_evidence/tr_v0_g0_g2_admission_1.json`

---

## Scope

This packet re-lands the already-accepted free-gate science. It does **not** reopen FTK economics and does not perform a trial.

Board context remains:

```text
Reality / 雷達       = PASS
Selection / 擇標的   = FAIL   <- bottleneck
Timing / 擇時        = UNKNOWN / out of scope

Question = Reality -> Selection bridge via Recognition Gap
Not      = FTK rescue / entry timing / full strategy build
```

The single golden question is:

> Among companies with a real operating transition, what independently observable PIT state distinguishes a merely real transition from an economically selectable, not-yet-recognized transition?

Only **Recognition as selection** is admitted here. Recognition as timing remains D7 and is forbidden until a later selection test earns it.

---

## G0 — Distinctness versus CRV1: PASS

`CYCLE_RESONANCE_v1` owns the broad ordered-cycle hypothesis:

```text
supply/capacity
-> inventory
-> pricing
-> utilization/margin
-> earnings revisions
-> expectation-gap resolution
-> 252d right-tail winner
```

TR-v0 is narrower:

```text
GIVEN Reality is already present,
ask whether contemporaneous recognition lag adds selection information:
Reality + RecognitionGap  vs  Reality alone.
```

The later success metric is a separately preregistered D6 selection-enrichment comparison inside the Reality-positive cohort. No metric is evaluated here. TR-v0 does not inherit CRV1's 252-trading-day primary horizon; a later economic horizon must be frozen separately before result access.

**Merge rule:** if TR-v0 later requires CRV1's broad ordered-cycle contract, 252d label, or resonance score to define itself, route/merge it to CRV1 instead of maintaining a duplicate family.

---

## G1 — PIT recognition without returns: PASS

### Recognition state

The latest lawful point-in-time consensus/expectation state known at `decision_as_of` for permanent security identity, using source-bound expectation rows only.

Candidate observation families are definition candidates only, not fitted/scored features:

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

### Recognition gap

Conditional on `Reality=true`, the operating transition has moved farther than contemporaneous consensus recognition. The exact normalization/materiality operator is intentionally deferred to L2. It may not be selected from future returns, future prices, failed FTK dates/payoffs, or residual outcomes.

### PIT / identity law

```text
security_id = CIQSEC:<Capital IQ Security ID>
available_at <= decision_as_of
latest lawful vintage only
observed consensus != inferred market-implied state unless explicitly labeled
missing / stale / not-entitled required state -> ABSTAIN
```

The existing `alpha_pit_data_api_v1` expectations surface demonstrates that this recognition state is definable with permanent identity, `available_at`, source receipts, epistemic class, and explicit missingness. **L2 still must bind a TR-v0-specific family/source contract.** CRV1 family artifacts are not TR-v0 authority.

No return/label join occurred.

---

## G2 — Incremental to Reality: PASS

Reality and recognition are different semantic nodes:

```text
REALITY
= PIT operating-transition observation

RECOGNITION_STATE
= PIT consensus / expectations observation
```

RecognitionGap therefore has independent meaning as:

> the business transition is occurring, but contemporaneous expectations have not yet incorporated it.

It may **not** be another encoding of the same inventory/margin transition surface. Specifically forbidden as recognition inputs:

```text
FTK inventory transition score
FTK margin transition score
FTK composite rank / selected-set membership
K=20 action map
H=63 hold law
failed FTK residual/payoff information
price/return reaction used to define recognition
```

If L2 cannot preserve this separation, F2 kills TR-v0 as non-incremental.

---

## L0/L1 freeze

### L0 question

> Conditional on a real PIT-observable operating transition, does an independently observable recognition/consensus gap identify which transitions are economically selectable (not-yet-recognized) versus already-recognized?

### L1 causal chain

```text
REALITY
  business transition actually occurring (PIT-observable)
    |
    v
RECOGNITION STATE
  consensus/market has not fully incorporated the transition
    |
    v
RECOGNITION GAP
  Reality has moved farther than expectations
    |
    v
SUBSEQUENT RECOGNITION
  later scientific state; NOT timing research in this slice
    |
    v
POTENTIAL SELECTION EDGE
  D6 later; NOT evaluated here
```

### H1

Among firms exhibiting a real operating transition, future economic selection enrichment under a later preregistered wager law is higher when contemporaneous consensus recognition materially lags the observed transition, versus transitions already recognized.

### Falsifiers frozen before L2

- **F1:** Recognition cannot be defined independently of future returns -> `KILL`.
- **F2:** Recognition is merely another encoding of Reality/FTK -> `KILL / not incremental`.
- **F3:** Hypothesis is materially identical to CRV1 -> `MERGE/ROUTE`.
- **F4:** Useful recognition state can be defined only after inspecting failed FTK dates/payoffs -> `KILL`.
- **F5:** Mechanism requires choosing H/K/threshold from prior economic residuals -> `KILL`.

Machine freeze: `docs/architecture/transition_recognition_v0_l0_l1_freeze.json`  
Human causal authority: `docs/architecture/transition_recognition_v0_causal_admission.md`

---

## Hard stop-lines honored

```text
no returns / labels / payoff joins
no H / K / threshold / feature search
no economic trial / debit / L5
no timing / D7
no FTK residual rescue
no AO-FTK-2
no capital / alpha claim
no full strategy scaffold
```

The next lawful science slice is only `TR-v0-L2-OBSERVATION-CONTRACT-1`, after the parallel FTK STOP stamp is on current authority. L2 may bind expectations/revision sources PIT-correctly; it still may not open returns, timing, thresholds, or L5.

---

## Return packet

```text
SLICE_ID:     TR-v0-G0-G2-ADMISSION-1
G0:           PASS
G1:           PASS
G2:           PASS
TERMINAL:     ALL_PASS_ADMIT_L1_FROZEN
L0_L1_FROZEN:true
TIMING_OPENED:false
FTK_RESCUE:   false
DEBIT:        0
ALPHA:        0
NEXT:         L2_OBSERVATION_CONTRACT
RECEIPT:      docs/context/e2e_evidence/tr_v0_g0_g2_admission_1.json
```

**Constitution:** Free-kill first: distinct from CRV1, PIT recognition without returns, incremental to Reality. Selection only—not timing, not FTK rescue, not a trial.
