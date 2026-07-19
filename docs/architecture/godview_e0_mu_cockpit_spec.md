# GODVIEW-E0: MU Supply-Gap Contract-Proof Slice

Status: Active Implementation Specification — Synthetic Build Only After P0 Hash Freeze
Date: 2026-07-15
Authority: `docs/architecture/godview_endgame_vision.md` and `docs/architecture/top_level_roadmap.md`

## 1. Purpose

Build the smallest complete evidence-to-decision slice that can honestly accept, reject, block, or suspend its own MU supply-gap analysis.

This is not an MU dashboard project. MU is the first evidence-rich patient used to test whether the architecture survives point-in-time evidence, supply-demand identification, business capture, shareholder capture, valuation non-identifiability, model inadequacy, and a fair cheap baseline.

## 2. E0 Decision and Claim Boundary

Human action set:

```text
ADVANCE_TO_FULL_RESEARCH
HOLD_FOR_EVIDENCE
REJECT_THESIS
```

Research question:

> Does admissible point-in-time physical evidence support a materially slower memory-supply-relief path than the set of operating and valuation scenarios consistent with MU's decision-time price, and do MU's business and shareholder economics preserve enough of that separation to justify advancing the proposition to full research?

Permitted candidate output:

```text
PRICE_INCONSISTENCY_CANDIDATE
```

Mandatory output qualifier:

> Conditional on the registered evidence bundle, model family, bounds, proof rule, and decision timestamp.

Forbidden E0 claims:

- established market mispricing;
- financial alpha;
- investability or tradability;
- a buy, sell, size, or portfolio action;
- calibrated scenario probability;
- general superiority to human research;
- research-latency improvement.

## 3. P0 Inputs

E0 has no implementation authority until these four artifacts are internally consistent and hash-frozen:

```text
docs/architecture/godview_e0/e0_preregistration.yaml
docs/architecture/godview_e0/evidence_authority_matrix.csv
docs/architecture/godview_e0/e0_model_spec.md
docs/architecture/godview_e0/e0_acceptance_tests.md
```

The implementation must consume the machine-readable preregistration directly. It may not duplicate or reinterpret scientific policy in CLI or UI code.

## 4. Canonical End-to-End Flow

```text
immutable bundle directory
→ manifest and SHA-256 verification
→ evidence-authority validation
→ canonical typed facts
→ effective-supply stock-flow representation
→ supply-demand identification gate
→ MU business-capture bridge
→ shareholder-capture bridge
→ control and constrained price envelopes
→ model self-falsification and proof gate
→ forced falsifiers and materiality
→ canonical result.json
→ deterministic decision_packet.md
→ sealed pre/post human decision records
→ append-only evidence-bearing run ledger
```

No network access is permitted during a run.

## 5. Orthogonal State Contract

### Run state

```text
VALID
BLOCKED
```

### Block reasons

```text
INVALID_SCHEMA
INVALID_POINT_IN_TIME
MISSING_INDISPENSABLE_EVIDENCE
STALE_INDISPENSABLE_EVIDENCE
CONTRADICTORY_INDISPENSABLE_EVIDENCE
INACCESSIBLE_OR_UNLICENSED_EVIDENCE
NONDETERMINISTIC_EXECUTION
INVALID_BASELINE_SEAL
```

### Model state

```text
ADEQUACY_GATE_PASSED
NON_IDENTIFIABLE
BOUNDS_UNJUSTIFIED
MODEL_INADEQUATE
INFEASIBILITY_UNCERTIFIED
NOT_EVALUATED
```

### Claim results

Each claim is independently:

```text
SUPPORTED
FALSIFIED
UNKNOWN
NOT_EVALUATED
```

Claims:

```text
C1_PHYSICAL_RELIEF_SLOWER
C2_MU_BUSINESS_CAPTURE
C3_SHAREHOLDER_CAPTURE
C4_PRICE_ENVELOPE_MATERIALLY_SEPARATED
```

### Candidate output

```text
NONE
PRICE_INCONSISTENCY_CANDIDATE
```

### Invariants

- `BLOCKED` implies `NOT_EVALUATED` model state, all claims `NOT_EVALUATED`, and candidate `NONE`.
- Candidate output requires `VALID`, `ADEQUACY_GATE_PASSED`, and all four claims `SUPPORTED`.
- `NON_IDENTIFIABLE`, `BOUNDS_UNJUSTIFIED`, `MODEL_INADEQUATE`, or `INFEASIBILITY_UNCERTIFIED` implies candidate `NONE`.
- Missing evidence never becomes `FALSIFIED`.
- An economically immaterial certified separation sets C4 to `FALSIFIED`.
- The human decision remains independent from the candidate output.

## 6. Functional Slices

### E0.1 — Evidence-Authority Kernel

Input: synthetic immutable bundle.

Output:

- canonical manifest;
- typed facts;
- authority findings;
- `VALID` or `BLOCKED` result;
- deterministic hashes.

Required branches:

- valid bundle;
- missing indispensable evidence;
- stale evidence;
- invalid `known_at`;
- revised-history leakage;
- contradictory indispensable evidence;
- duplicate upstream evidence;
- inaccessible or unlicensed evidence;
- non-deterministic serialization.

Endgame role: creates the authority boundary reused by every future module and evidence-bearing run.

### E0.2 — Effective Supply and Identification

Input: accepted typed physical facts.

Output:

- effective-supply feasible set by segment and horizon;
- supply-specific mechanism result;
- demand-alternative challenge;
- C1 result;
- physical falsifier state.

The slice must distinguish theoretical capacity, qualified production, sellable supply, producer inventory, channel inventory, market availability, demand, and price.

Endgame role: proves an independent gap can remain `NON_IDENTIFIABLE` rather than being forced into a directional signal.

### E0.3 — Business and Shareholder Capture

Input: physical outcomes plus accepted MU operational/accounting facts.

Output:

- C2 business-capture result;
- C3 shareholder-capture result;
- reconciled revenue, cost, operating, capex, working-capital, tax, financing, dilution, repurchase, net-debt, and cash-flow bridges;
- forced capture falsifiers.

Endgame role: prevents physical criticality from bypassing company economics or shareholder leakage.

### E0.4 — Price Envelope and Model Self-Falsification

Input: accepted facts and capture outcomes.

Output:

- control-model feasible price set;
- physically constrained feasible set;
- complete-enumeration or certified proof record;
- conservative bound expansion;
- physical-constraint ablation;
- frozen challenge-model result;
- materiality result;
- model state;
- C4 result;
- optional candidate output.

Endgame role: makes model rejection a first-class successful result and prevents local solver failure or narrow bounds from masquerading as market error.

### E0.5 — Decision Packet and Cheap Baseline

Input:

- sealed baseline record;
- canonical machine result;
- evidence and claim lineage.

Output:

- deterministic `decision_packet.md`;
- post-packet human decision;
- six-part rubric item scores and raw delta;
- rationale changes;
- append-only run-ledger entry.

Both baseline and assisted arms receive identical evidence, instructions, horizon, and fixed human-analysis time. Machine runtime is recorded separately.

Endgame role: converts analysis into a fair, auditable decision product without claiming general effectiveness from one case.

### E0.6 — First MU Evidence-Bearing Run

This slice begins only after all synthetic terminal branches pass.

Any run reading MU, market-price, industry, accounting, or decision-time artifacts is an `EVIDENCE_BEARING_RUN` and must be retained, even if partial, null, failed, or not viewed.

Endgame role: tests the full contract against reality and may validly stop the program.

## 7. Model and Proof Boundary

Default E0 model family:

```text
finite bounded scenario lattice + complete deterministic enumeration
```

A solver is not required for the first implementation.

A later solver path requires P0 amendment that freezes:

- mathematical class;
- domain closure;
- global-proof authority;
- accepted termination statuses;
- numerical tolerances;
- retained proof artifact;
- challenge-model compatibility.

Local infeasibility, optimizer failure, time limit, partial enumeration, or numerical restoration failure produces `INFEASIBILITY_UNCERTIFIED`, never a candidate.

## 8. Candidate Predicate

`PRICE_INCONSISTENCY_CANDIDATE` requires all of the following:

1. valid deterministic run;
2. all indispensable evidence passes authority;
3. supply and demand are sufficiently distinguished;
4. stock-flow and accounting identities reconcile;
5. the control model accommodates the decision-time price;
6. the registered physical constraint supports C1;
7. business and shareholder capture support C2 and C3;
8. separation is completely enumerated or globally certified;
9. physical ablation removes or materially reduces the separation;
10. conservative bound expansion does not restore overlap;
11. the frozen challenge model does not eliminate the result;
12. no forced falsifier triggers;
13. the robust price-equivalent separation meets the preregistered materiality threshold;
14. all prior evidence-bearing attempts are disclosed;
15. C4 is supported.

An empty intersection alone is never sufficient.

## 9. Model-Search and Amendment Policy

Run classes:

```text
SYNTHETIC_DEV_RUN
EVIDENCE_BEARING_RUN
```

A synthetic run may use generated fixtures only. Any access to real MU or decision-time evidence makes the run evidence-bearing.

Every evidence-bearing run records immutable protocol, model, code, configuration, evidence, baseline, solver/enumerator, timestamp, result, and prior-run-count identities.

A material change requires a new protocol version and cannot repair or carry forward a prior candidate. Material changes include evidence inclusion, equations, transformations, bounds, tolerances, proof method, branch order, challenge model, materiality, or falsifiers.

Non-material repairs are limited to comments, formatting, logging, deterministic rendering, or parser defects whose expected behavior was locked by a synthetic golden fixture before the evidence-bearing rerun.

## 10. Cheap-Baseline Rubric

The primary E0 endpoint is decision quality under identical fixed human-analysis time.

The rubric contains six equal-weight items scored on a preregistered `0`, `1`, or `2` scale:

1. selected-action defensibility;
2. identification of indispensable missing evidence;
3. recognition of falsifiers and contradictions;
4. separation of supply, demand, business capture, shareholder capture, and valuation;
5. avoidance of claims beyond the evidence;
6. traceability of rationale to admissible evidence.

Scoring must be blind to arm identity where practical. Tie handling, adjudication, and missing-score behavior are frozen before packet exposure.

E0 reports raw item differences and total difference only. It does not infer general improvement.

## 11. Required Outputs

```text
evidence_manifest.json
facts.json
supply_envelope.json
business_capture.json
shareholder_capture.json
price_envelope.json
model_adequacy.json
falsifiers.json
result.json
decision_packet.md
baseline_decision.json
post_decision.json
baseline_comparison.json
run_manifest.json
run_ledger.jsonl
```

Output names describe the contract; exact directory layout may remain implementation-local until E0.1.

## 12. Thin Implementation Boundary

Allowed:

- Python standard library;
- typed validation where it reduces ambiguity;
- deterministic JSON/YAML/CSV parsing;
- complete finite enumeration;
- SHA-256;
- pytest golden and invariant tests;
- one thin local CLI over shared application/domain services.

Deferred until measured need:

- Pyomo or a global solver;
- Frictionless as a runtime dependency;
- DVC;
- provenance graph infrastructure;
- workflow orchestration;
- provider abstraction;
- database or model registry;
- dashboard or web service;
- LLM extraction or narrative generation.

An LLM may later format approved structured fields only. It may not create facts, resolve contradictions, select bounds, infer causal links, assign confidence, or promote a thesis.

## 13. Stop Rules

Stop or hold E0 when:

- an indispensable evidence category lacks point-in-time authority;
- supply and demand remain non-identifiable;
- the control model cannot fit price;
- model or accounting identities fail;
- global separation cannot be certified;
- conservative bounds restore overlap;
- the challenge model removes the result;
- business or shareholder capture fails;
- the robust separation is economically immaterial;
- the cheap baseline cannot be run fairly;
- evidence-bearing search history is incomplete;
- forbidden infrastructure appears necessary before the contract works.

Failure is a valid shipped E0 result.

## 14. Immediate Next Action

```text
P0-FREEZE-01
```

Freeze and hash the four P0 artifacts, then implement E0.1 using synthetic golden bundles only.
