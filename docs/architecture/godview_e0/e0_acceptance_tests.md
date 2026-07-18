# GodView E0 Acceptance Tests

Status: P0 Freeze Candidate
Date: 2026-07-15
Protocol: `GODVIEW-E0-P0-V1`

## 1. Acceptance Principle

E0 is accepted only when the complete evidence-to-decision chain can produce every positive, negative, blocked, unknown, non-identifiable, bounds-sensitive, model-inadequate, and uncertified result without narrative repair.

Test count alone is not acceptance. Each terminal branch must execute end to end through canonical `result.json` and `decision_packet.md` generation.

## 2. Required Test Layers

### Contract validation

- YAML preregistration parses and rejects unknown or duplicate keys.
- CSV evidence-authority matrix has unique `evidence_id` values and required columns.
- Every claim ID maps to at least one indispensable evidence row.
- Every model parameter maps to an evidence row or registered conservative policy range.
- State enums and invariants are exact.

### Determinism

- Same protocol, code identity, evidence bundle, baseline seal, and run class produce byte-identical canonical machine outputs.
- Input row ordering does not change canonical facts or results.
- Lattice-axis ordering is canonical.
- Expected Cartesian-product count equals evaluated count.
- Hash drift creates a new identity and cannot reuse a prior result.

### Point-in-time authority

- `known_at > decision_timestamp` blocks before model evaluation.
- Current snapshot cannot satisfy a historical point-in-time requirement.
- Revised history without vintage authority blocks.
- Missing permitted-use or licence status blocks an indispensable item.
- Duplicate reports sharing one upstream source do not increase evidence independence.
- Entity, segment, product, currency, unit, or effective-period ambiguity blocks the affected indispensable item.

### Stock-flow and accounting integrity

- Allocation shares cannot exceed one within tolerance.
- HBM and conventional DRAM capacity cannot be double counted.
- Production and qualification lags cannot move output backward in time.
- Producer and channel inventory equations conserve the registered unit.
- Inventory release is not counted both as stock reduction and market shipments.
- Revenue, cost, operating profit, FCFF, capital structure, and diluted-share identities reconcile.
- Repurchases affect both cash and diluted shares and cannot create free value.

### Model adequacy and proof

- Control model accommodates the decision-time price before physical constraints.
- Primary model changes only the registered physical and capture constraints.
- Complete enumeration is proven by exact count equality.
- Partial enumeration produces `INFEASIBILITY_UNCERTIFIED`.
- Local or generic solver failure can never produce a candidate.
- Unsupported bounds produce `BOUNDS_UNJUSTIFIED`.
- Conservative expansion is applied exactly.
- Physical ablation removes or materially reduces candidate separation.
- Frozen challenge model executes before candidate evaluation.
- Economic materiality is applied after proof and challenge checks.

### Baseline fairness

- Baseline and assisted arms bind the same evidence-bundle hash.
- Both bind the same decision timestamp, cutoff, action set, horizon, instructions, and 60-minute human-analysis budget.
- Baseline seal predates packet generation.
- Outside-research attestation is required.
- Baseline record mutation invalidates the seal.
- Machine runtime is recorded separately from human time.
- Rubric item scale, equal weighting, tie handling, and adjudication are exact.
- E0 output cannot label a one-case delta as general improvement.

### Model-search discipline

- A synthetic run touching real MU or market artifacts is rejected or reclassified as evidence-bearing before execution.
- Every evidence-bearing run is appended to the ledger, including null, failed, partial, and unviewed runs.
- Material amendments require a new protocol version.
- Candidate carry-forward after a material amendment is rejected.
- Non-material parser repair requires a prelocked synthetic golden expected output.
- Prior evidence-bearing run count is correct and disclosed.

### LLM boundary

- Critical-path tests require no LLM.
- Rendered text may contain only facts, numbers, states, and causal language present in approved structured fields.
- An uncited or unstructured factual assertion fails rendering validation.
- LLM-created confidence, probability, contradiction resolution, bound change, or thesis promotion is rejected.

## 3. Required End-to-End Golden Cases

### G01 — Valid authority, physical claim supported, price envelope overlaps

Expected:

```text
run_state = VALID
model_state = ADEQUACY_GATE_PASSED
C1 = SUPPORTED
C2 = SUPPORTED
C3 = SUPPORTED
C4 = FALSIFIED
candidate = NONE
```

Purpose: prove thesis-supporting physical evidence does not force a price inconsistency.

### G02 — Physical claim falsified

Expected:

```text
run_state = VALID
C1 = FALSIFIED
candidate = NONE
```

Purpose: prove the system can reject the primary physical proposition.

### G03 — Business capture falsified

Expected:

```text
run_state = VALID
C1 = SUPPORTED
C2 = FALSIFIED
candidate = NONE
```

Purpose: prove industry scarcity does not automatically accrue to MU.

### G04 — Shareholder capture falsified

Expected:

```text
run_state = VALID
C1 = SUPPORTED
C2 = SUPPORTED
C3 = FALSIFIED
candidate = NONE
```

Purpose: prove MU business improvement does not automatically accrue to shareholders.

### G05 — Missing indispensable evidence

Expected:

```text
run_state = BLOCKED
block_reason = MISSING_INDISPENSABLE_EVIDENCE
model_state = NOT_EVALUATED
all claims = NOT_EVALUATED
candidate = NONE
```

### G06 — Stale indispensable evidence

Expected block reason: `STALE_INDISPENSABLE_EVIDENCE`.

### G07 — Invalid point-in-time or revised-history leakage

Expected block reason: `INVALID_POINT_IN_TIME`.

### G08 — Contradictory indispensable evidence

Expected block reason: `CONTRADICTORY_INDISPENSABLE_EVIDENCE`.

The engine may not average or majority-vote the contradiction.

### G09 — Supply-demand non-identifiable

Expected:

```text
run_state = VALID
model_state = NON_IDENTIFIABLE
C1 = UNKNOWN
candidate = NONE
```

### G10 — Bounds unjustified

The primary candidate disappears under registered 20 percent conservative expansion.

Expected:

```text
run_state = VALID
model_state = BOUNDS_UNJUSTIFIED
C4 = UNKNOWN
candidate = NONE
```

### G11 — Model inadequate: stock-flow or accounting failure

Expected model state: `MODEL_INADEQUATE`.

Purpose: prove an internally inconsistent model cannot emit a claim.

### G12 — Model inadequate: control model cannot fit price

Expected model state: `MODEL_INADEQUATE` or `BOUNDS_UNJUSTIFIED` according to the frozen cause classification.

Candidate remains `NONE`.

### G13 — Infeasibility uncertified

The primary search is partial or only a local solver failure is available.

Expected:

```text
run_state = VALID
model_state = INFEASIBILITY_UNCERTIFIED
C4 = UNKNOWN
candidate = NONE
```

### G14 — Candidate removed by physical ablation

The separation persists when the physical constraint is removed.

Expected model state: `MODEL_INADEQUATE`.

Purpose: prove the market contradiction must be attributable to `G_supply`.

### G15 — Candidate removed by frozen challenge model

Expected model state: `NON_IDENTIFIABLE` or `BOUNDS_UNJUSTIFIED` according to cause.

Candidate remains `NONE`.

### G16 — Certified but economically immaterial separation

Separation exceeds numerical tolerance but is below 15 percent.

Expected:

```text
model_state = ADEQUACY_GATE_PASSED
C4 = FALSIFIED
candidate = NONE
```

### G17 — Invalid baseline seal or unequal comparison budget

Expected:

```text
run_state = BLOCKED
block_reason = INVALID_BASELINE_SEAL
candidate = NONE
```

The packet may render validation failure only, not a decision comparison.

### G18 — Undeclared prior evidence-bearing run

Expected: current evidence-bearing run fails search-history completeness and cannot emit a candidate.

The exact implementation may use `BLOCKED` or a dedicated validation failure, but the choice must be fixed before code and remain consistent with the preregistration.

### G19 — Fully valid conditional candidate

Expected:

```text
run_state = VALID
model_state = ADEQUACY_GATE_PASSED
C1 = SUPPORTED
C2 = SUPPORTED
C3 = SUPPORTED
C4 = SUPPORTED
candidate = PRICE_INCONSISTENCY_CANDIDATE
```

Mandatory conditions:

- all indispensable evidence passes;
- supply-demand identification passes;
- stock-flow and accounting identities pass;
- control model fits price;
- complete enumeration count matches;
- primary separation is certified;
- ablation removes or materially reduces separation;
- 20 percent bound expansion preserves separation;
- challenge model preserves separation;
- no falsifier triggers;
- robust price-equivalent separation is at least 15 percent;
- prior evidence-bearing run history is complete;
- packet includes the conditional qualifier and all forbidden-claim warnings.

This case validates branch semantics only. It is not evidence about MU.

## 4. Decision-Packet Acceptance

Every packet must show:

- protocol, model, code, bundle, baseline, and result identities;
- run, model, claim, candidate, and human-decision states separately;
- accepted evidence and exact lineage;
- blocked, missing, stale, contradictory, estimated, inferred, and unknown evidence;
- parameter domains and derivation classes;
- control, primary, expansion, ablation, and challenge results;
- falsifiers;
- materiality;
- prior evidence-bearing run count;
- allowed and forbidden conclusions;
- baseline and post-packet decisions;
- raw rubric item differences without a general-effectiveness claim.

Packet generation fails when it encounters an unsupported factual statement or causal verb absent from approved structured output.

## 5. Slice Exit Gates

### E0.1 exit

G05-G08, determinism, hash, schema, duplicate-source, and invalid-baseline preconditions pass through canonical result generation.

### E0.2 exit

G02 and G09 pass; physical stock-flow identities and supply-demand challenge are executable.

### E0.3 exit

G03, G04, and G11 pass; business and shareholder capture remain independent.

### E0.4 exit

G01, G10, G12-G16, and G19 pass; candidate emission is impossible without all proof gates.

### E0.5 exit

G17, rubric, packet, sealing, and run-ledger tests pass for every terminal state.

### E0.6 entry

All nineteen synthetic cases and focused regressions pass from a clean checkout with no network access.

## 6. First MU Run Acceptance

The first evidence-bearing MU run succeeds as an E0 experiment when:

- one immutable bundle is accepted or honestly blocked;
- every real-data attempt is retained;
- the full chain reaches one reproducible terminal state;
- no manual edit changes a derived result in place;
- baseline fairness is preserved;
- output does not exceed E0 claim authority.

A candidate is not required. `BLOCKED`, `NON_IDENTIFIABLE`, `MODEL_INADEQUATE`, `INFEASIBILITY_UNCERTIFIED`, `FALSIFIED`, or no candidate may be the correct shipped result.

## 7. Forbidden Acceptance Shortcuts

The following cannot close a slice:

- passing helper tests without executing the terminal branch;
- schema validation without evidence-authority tests;
- an attractive output without complete run history;
- local solver infeasibility;
- a dashboard screenshot;
- narrative review of a packet not regenerated from canonical output;
- manual repair of a failed evidence-bearing result under the same protocol version;
- test-count growth without new branch coverage;
- one MU baseline delta interpreted as general decision improvement.
