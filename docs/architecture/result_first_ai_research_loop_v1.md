# Result-First AI Research Loop v1 — Forward-Gate Method Lock

**Date:** 2026-08-12
**Status:** `LOCKED / FORWARD_ONLY / NO_RETROACTIVE_EVIDENCE_REWRITE`
**Authority:** scientific research-process amendment under `ALPHA_SCIENTIFIC_METHOD_v1`
**Product effect:** none by itself
**Capital effect:** none
**financial_alpha_evidence:** `0`

---

## 0. One-line lock

> **Ordinal RDV + multi-margin feasibility vector + policy-conditioned capturability + reuse default with safety exception.**

The research system is **result-first**, where "result" means the next scientific or operating decision, not PnL. Every gate moves only forward. Finishing a phase never creates entitlement to run the next expensive phase.

---

## 1. Result-first law

Every material research or engineering slice MUST declare before implementation:

```text
DECISION_TO_CHANGE
CURRENT_BELIEF
CHEAPEST_DISCRIMINATING_TEST
WHY_NO_CHEAPER_TEST_EXISTS
PASS_ROUTE
FAIL_ROUTE
UNRESOLVED_ROUTE
ENGINEERING_COST
UNTOUCHED_EVIDENCE_COST
SEARCH_DEBT
```

### Killer rule

```text
IF PASS_ROUTE == FAIL_ROUTE == UNRESOLVED_ROUTE
THEN DECISION_VALUE = ZERO
AND DO_NOT_RUN
```

Routes must name a concrete legal next state/action, not prose synonyms. Examples include:

```text
HOLD_SOURCE
PARK
STOP
SIMPLIFY
REVISE_WITHIN_FREEZE
READY_FOR_L5_CANDIDATE
READY_BUT_NOT_PRIORITY
L5_AUTHORIZE
```

A completed test that cannot change a route is not progress.

### Receipt-first engineering

Define the terminal receipt and legal routes before building substantial machinery. Engineering exists to produce an honest decision receipt, not to complete a horizontal platform.

---

## 2. Forward-gate-only law

Canonical loop enums remain unchanged. This amendment changes the **authorization semantics** between them:

```text
L0 → L1 → L2 → L3 → L4
```

is not an automatic conveyor belt.

Each boundary is a forward decision gate:

```text
current gate PASS/READY
+ no earlier fatal blocker
+ next test has non-zero decision value
→ next gate may be considered
```

No gate may self-authorize a later result-bearing phase.

Especially:

```text
L4_EMPIRICAL_FREEZE
→ READY_FOR_L5_CANDIDATE
≠ L5_AUTHORIZED
```

Before any scarce L5 outcome read, compare all lawful READY candidates across families. `READY_BUT_NOT_PRIORITY` is a legal terminal state.

Historical freezes/runs/diagnoses retain the rules under which they were created. This amendment is forward-only.

---

## 3. E0–E8 decision-production path

```text
E0  QUESTION VALUE
    Is this decision worth asking now?

E1  SOURCE SEMANTICS
    Can indispensable observables exist lawfully?

E2  CUSTODY / PIT
    Can the exact observables be admitted without leakage?

E3  CLOCK / STATE COORDINATE
    What is the data-availability, economic-state, and action clock?

E4  REPRESENTATION SNR
    Can the hypothesized weak state be sensed?

E5  FABRICATION TOLERANCE
    Does lawful numeric/temporal/threshold/missingness perturbation destroy topology?

E6  OBSERVABILITY-SELECTION DIAGNOSIS
    Does fail-closed missingness systematically censor the economically central state?

E6.5 EX-ANTE FEASIBILITY / CAPTURABILITY
    Only when an action-bearing economic freeze, D9, promotion, capital-policy preflight,
    or PAPER action is proposed. Not mandatory for pure source/sensing slices.

E7  SMALLEST SURVIVING FREEZE
    Freeze the minimum representation/action contract that survived prior gates.

E7.5 CROSS-FAMILY RESEARCH CAPITAL ALLOCATION
    Rank READY candidates by ordinal Research Decision Value; do not auto-open L5.

E8  SCARCE OUTCOME READ
    One authorized result-bearing read, then D1→D9 first-fail diagnosis.
```

The objective is to minimize `TIME_SPENT_AFTER_FIRST_KNOWN_FATAL_BLOCKER` and avoid unnecessary outcome reads.

---

## 4. Research Decision Value (RDV) — ordinal only

RDV is a **research-priority aid**, never Alpha evidence, promotion evidence, or capital authority.

Initial machine scale is deliberately ordinal:

```text
route_change_plausibility = LOW | MED | HIGH
decision_materiality      = LOW | MED | HIGH
information_independence  = LOW | MED | HIGH
engineering_cost          = LOW | MED | HIGH
untouched_evidence_cost   = LOW | MED | HIGH
search_debt               = LOW | MED | HIGH
```

Do not invent a universal calibrated `P(route_changes)` and do not assign pseudo-precise mutual-information values without a legitimate probability model.

The killer rule dominates any RDV score. If terminal routes are identical, RDV is zero regardless of narrative importance.

No future return, IC, RankIC, Sharpe, MaxDD, or other outcome-bearing quantity may enter RDV during L0–L4.

---

## 5. Clock / state-coordinate declaration

L2 owns the declaration; L3→L4 enforces it.

Minimum object:

```text
clock_type
role = DATA_AVAILABILITY | ECONOMIC_STATE | ACTION_EXECUTION
why_this_clock
aliasing_risk
invariance_claim
falsifier
```

A family may use multiple roles, but it must not conflate them. A data-availability clock does not become a free economic horizon parameter.

Outcome-driven multi-clock bake-offs or H/K/horizon grids under one version are forbidden.

---

## 6. L3 R9 fabrication-tolerance gate

R9 is additive after R1–R8. Historical L3 receipts remain valid under their pinned contract version.

```text
R9A NUMERIC
  perturb only within source-bound measurement/quantization tolerance

R9B TEMPORAL
  source-bound availability uncertainty; default delay-only
  never move information across an unproven publication boundary into the past
  crossing decision cut → UNOBSERVED → ABSTAIN

R9C THRESHOLD
  local frozen-cut perturbation only; no grid and no outcome selection

R9D MISSINGNESS
  PRESENT → UNOBSERVED under source-shaped stress
  immutable denominator; no imputation or renormalization
```

First global implementation is report/route oriented, not a universal numeric PASS wall. Family-specific hard cuts, if any, must be preregistered without outcome tuning.

Outcome-blind diagnostics may include:

```text
state_flip_rate
direction_flip_rate
rank_displacement
far_from_boundary_flip_rate
baseline_abstention
direct_loss
propagation_tax
abstention_delta
```

---

## 7. Observability-selection bias

Full-denominator accounting does not by itself prove that the surviving decision surface is unbiased.

`OBSERVABILITY_SELECTION_BIAS` is a report-only diagnosis using decision-time ex-ante variables. It may test whether `UNRESOLVED` probability rises materially with stress/shock severity or systematically removes a relevant state manifold.

A Stress-Censoring Gradient may be reported diagnostically, but it MUST NOT:

```text
become a selector
reweight candidates
propensity-fill missing names
shrink the denominator
consume future returns
```

If systematic censoring is material, legal routes are `SIMPLIFY`, `REVISE_WITHIN_FREEZE`, or `BLOCK`.

---

## 8. OpportunityKernel pre-run declarations

Every future result-bearing kernel freezes short machine declarations for:

```text
clock_state_coordinate
activation_contract
invariance_contract
falsifier_contract
```

### Activation

```text
activation_requirement = NONE | REQUIRED | CONDITIONAL
activation_role = CAUSAL_PRECONDITION | ENTRY_CONFIRMATION
```

`CAUSAL_PRECONDITION` must exist before L4. `ENTRY_CONFIRMATION` belongs to D7 only after the D6 path is honest. It may not rescue a D6 failure after results.

### Falsifier

When thesis integrity is causal, use:

```text
F0 SYNCHRONOUS_ELIGIBILITY
  INTACT | DAMAGED | UNRESOLVED
  UNRESOLVED → ABSTAIN

F1 DELAYED_THESIS_INVALIDATION
  post-entry monitoring / de-risk / exit
  never rewrites what was knowable at entry
```

For families where thesis-integrity gating is not applicable, declare `F0=NOT_APPLICABLE` with reason.

---

## 9. Ex-ante capturability and execution feasibility

Capturability moves earlier **without becoming Alpha evidence**.

### Trigger

`ExecutionFeasibilityV1` is required for:

```text
action-bearing economic freeze
D9 economics/cost/capacity
promotion / capital-policy preflight
PAPER action proposal
```

It is optional / `NOT_APPLICABLE` for pure source, custody, representation, or sensing work with no proposed exposure.

### Hard risk stays hard

```text
G(s,a) = ALLOW | BLOCK | UNRESOLVED
```

`BLOCK` is infeasible. No learned objective, expected return, or lambda penalty may compensate for a hard-risk violation.

### Risk margins stay a vector

Never compress heterogeneous hard-risk distance into one universal margin scalar.

Minimum vector may include:

```text
var_margin
sector_margin
single_name_margin
vix_margin
other_reason_code_specific_margins
```

`capturability_state = ROBUST | NEAR_BOUNDARY | FRAGILE | BLOCKED | UNRESOLVED` is summary only. Underlying margin vector remains authority.

### Soft friction stays soft

Within the hard-feasible set, admitted models may estimate:

```text
implementation shortfall
slippage
latency cost
fill probability
market impact / participation cost
```

These are capturability/economic inputs, not D6 selection evidence.

---

## 10. Policy-conditioned execution telemetry

Realized fills and execution telemetry are endogenous to the policy that generated them.

Any calibration of a capturability envelope MUST bind at least:

```text
policy_id
order_type
TIF
participation regime / sizing rule
market regime or declared conditioning state
instrument / venue identity where relevant
telemetry source receipt / period
```

A fill distribution generated by one policy may not silently estimate another policy's fill probability or implementation shortfall.

Execution telemetry may calibrate capturability/D9/capital-policy stress. It is not a universal OpportunityKernel feature surface.

Forbidden:

```text
execution_microstructure_fills → universal Alpha feature
prior policy fills → next Alpha thesis without a separately admitted causal contract
outcome-trained stress_block_rate
```

---

## 11. Three-ledger law

Keep separate authorities:

```text
SCIENTIFIC LEDGER
  L0–L8 science, source/PIT, R9, observability-selection, D1–D8

CAPTURABILITY LEDGER
  action feasibility, policy-conditioned IS/latency/fill/capacity stress, D9

ACTUAL BROKER LEDGER
  realized fills, fees, cash, positions, open orders, account P&L
```

No ledger overwrites another. Actual fills never retroactively rewrite historical Alpha evidence.

---

## 12. AI research-loop law

AI is primarily an **active hypothesis-elimination and research-allocation engine**, not an autonomous Alpha generator.

AI may:

```text
generate hypotheses
find contradictions
locate missing evidence
design discriminating tests
propose the cheapest falsifier
compress bounded search spaces
rank research WIP by ordinal RDV
```

AI may not:

```text
optimize historical Sharpe as the inner-loop objective
self-authorize L5
self-expand search budget
turn RDV into Alpha evidence
turn a hard risk veto into a soft penalty
merge scientific/risk/broker authority
```

Outcome-visible Discovery AI remains separate and charged to search debt; confirmatory L0–L4 work remains outcome-blind under its role firewall.

---

## 13. Vertical engineering and reuse law

Default engineering shape:

```text
one decision question
→ minimum necessary source seams
→ one falsifier path
→ one discriminating test
→ one terminal receipt
```

Generic infrastructure is extracted by default only after at least **two real consumers** prove the same semantic need.

This is a default, not a theorem. Safety/authority primitives may be shared earlier when duplication itself creates authority or safety risk, including examples such as:

```text
immutable receipt/hash primitives
PIT timestamp validation
canonical risk reason codes
fail-closed authority checks
```

Do not use the safety exception to justify a generic research/data/model platform.

---

## 14. Research-velocity KPIs

Prefer:

```text
TIME_TO_TERMINAL_DECISION
ROUTE_CHANGE_RATE_PER_SLICE
OUTCOME_READS_AVOIDED
SOURCE_FAILURES_CAUGHT_PRE_L3
REPRESENTATION_FAILURES_CAUGHT_PRE_L5
DECISION_CHANGING_INFO_PER_ENGINEERING_HOUR
DECISION_CHANGING_INFO_PER_OUTCOME_READ
SEARCH_DEBT_PER_SURVIVING_FAMILY
TIME_SPENT_AFTER_FIRST_KNOWN_FATAL_BLOCKER
```

Do not optimize number of runs, features, models, commits, or completed phases.

---

## 15. Explicit rejections

The following remain rejected:

```text
fills → Alpha as a universal path
lambda-soft hard risk
single blended expert confidence / risk-margin score
E6.5 mandatory on pure sensing/source slices
RDV as Alpha evidence or promotion score
outcome-trained stress_block_rate
automatic DISLOCATION open as a framework showcase
Bayesian optimization on historical Sharpe as an AI-native privilege
automatic L4 → L5 progression
retroactive R9 failure of historical experiments
```

---

## 16. Forward-only applicability

```text
REVISION_EFFECT      = FORWARD_ONLY
HISTORICAL_EVIDENCE = IMMUTABLE
CURRENT_PRODUCT      = UNCHANGED
CLOCK_1              = UNCHANGED
FINANCIAL_ALPHA      = 0
```

Current family/track state is owned by `docs/context/research_loop_state_current.json`. This method lock does not reopen FTK, TR-v0, W6, DISLOCATION, capital, or any stopped/parked family.
