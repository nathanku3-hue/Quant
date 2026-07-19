# GodView Endgame Vision

Status: Active Architecture Canon — GV-FS0 First
Date: 2026-07-16
Authority: `godview_portfolio_p0_owner_freeze.md`, `top_level_roadmap.md`, `gv_fs0_certification_and_data_authority_contract.md`, and the frozen research contract

## Product Center

**GodView is a portfolio operating system whose research engine improves the authority and quality of capital-allocation decisions. It must preserve what was known, why an action or abstention occurred, how the position affected cash and risk, and whether the economics survived costs and time.**

The first product is a deterministic paper-portfolio truth layer backed by auditable evidence-to-decision research. It is not a mechanical winner predictor, an autonomous analyst, an optimizer-first product, a broker, or evidence that financial alpha already exists.

MU is the first research patient because memory semiconductors expose hard physical-supply, inventory, qualification, capital-cycle, capture, and valuation questions. MU is not the product.

## Endgame

The endgame is a repeatable closed-loop architecture that can:

1. convert an explicit decision into a deterministic paper action or abstention;
2. preserve cash, positions, costs, exposures, drawdown, and self-financing portfolio truth;
3. bind every action to exact decision, evidence, policy, code, and output identities;
4. preserve exact point-in-time evidence authority;
5. distinguish evidence failure, identification failure, model failure, thesis falsification, sizing error, timing error, and implementation cost;
6. reject its own model before blaming the market;
7. measure selection, sizing, timing, costs, risk, and abstention prospectively;
8. improve research and allocation policies through repeated independent evidence;
9. consider live capital only after cost-adjusted replication.

## Product Law

> **Ship the portfolio truth substrate first, but do not grant automatic allocation or live-capital authority until decisions survive point-in-time evidence, model self-falsification, prospective paper economics, implementation costs, and independent replication.**

Portfolio substrate and portfolio authority are separate:

- early substrate: paper account, cash, positions, receivables, actions, costs, corporate actions, exposures, drawdown, attribution, abstention, lineage, and replay;
- later authority: autonomous selection, optimization-led allocation, leverage, shorting, derivatives, broker routing, live capital, and financial-alpha claims.

The long-run owner mandate is frozen by `godview_portfolio_p0_owner_freeze.md`: point-in-time Russell 1000 common equities, IWB **market-price total return** in USD, IWB NAV reconciliation, SOFR minus 25 bp cash, point-in-time ICB sector state, permanent capped equal weight, explicit concentration/liquidity/turnover limits, maximum 20 issuers, residual cash, and no forced full investment. The first authorized synthetic implementation is the smaller GV-FS0 chain: `DecisionEnvelope → PortfolioBook → Fs0PortfolioSnapshot → Fs0Certification → Streamlit adapter`. Real admission still requires the unchanged owner-freeze gate.

## Staged Delivery Law

The endgame is strict, and implementation authority is deliberately staged.

The first active gate is GV-FS0:

```text
DecisionEnvelope
→ PortfolioBook
→ Fs0PortfolioSnapshot
→ Fs0Certification
→ Streamlit adapter
```

The prior six-stream concurrent-start authority is revoked. Its A–F labels remain later endgame work packages only. GV-FS1 adds benchmark and policy paths; GV-FS2 adds bitemporal and corporate-action hardening; GV-RA0 admits real data; GV-E0 connects the frozen MU research contract; GV-P1 adds challengers and inference.

`PortfolioBook` is the sole active official GodView economic book for FS0. `strategies/strategy_replay.py`, the legacy lifecycle, optimizers, independent reconstruction, and UI cannot own or upgrade official FS0 truth.

Discovery capture may precede full research promotion. Claim promotion may not. Only `RESEARCH_CONTRACT_PASSED_PAPER` enters the later primary structural-policy inference population. Every stage converges through immutable decision, protocol, book, certification, and result identities.

Corollaries:

- Architecture quality is not financial alpha.
- Schema validity is not evidence authority.
- Solver output is not proof authority.
- An empty feasible-set intersection is not market error by itself.
- A physical bottleneck is not an equity opportunity until business and shareholder capture are separately supported.
- A valid run may reject the thesis.
- Missing evidence is not falsification.
- A single MU case may show architecture feasibility and a traceable decision difference; it cannot prove general decision improvement.
- Every evidence-bearing model attempt, null result, negative result, material amendment, policy variant, and outcome-exposed parameter vector must remain visible.
- Repeated or overlapping issuer episodes do not mechanically create independent observations; the complete portfolio time series is primary.
- Evidence-density checkpoints at 12, 36, 48, and 60 months govern interpretation but do not by themselves prove statistical sufficiency or alpha.
- Capped equal weight remains a permanent control, and residual cash must be challenged by an actual IWB-holding `P7_RESEARCH_EW_RESIDUAL_BENCHMARK_FIXED_TIMING_NET`, not pasted benchmark returns.
- Point-in-time membership, permanent identity, sector history, raw prices, benchmark, SOFR, corporate actions, and delistings are bitemporal authority inputs; current snapshots and silent substitution are invalid.
- Independent replication requires new future information, new issuer/context coverage, separate implementation and raw-data reconstruction, an independent reviewer, and pre-unblinding reconciliation.

## Independent Research Modules — No Composite Promotion Score

GodView preserves four independent reality-versus-expectations modules:

1. **`G_supply` — Physical Supply Inertia**
   Whether admissible physical evidence supports a supply-relief path materially different from the family of operating and valuation scenarios consistent with price.
2. **`G_duration` — Competitive-Advantage Duration**
   Whether admissible evidence supports a materially different persistence or fade path from price-consistent duration assumptions.
3. **`G_customer` — Customer Economics and Stress**
   Whether observable affordability, inventory, qualification, substitution, deferral, or commitment behavior differs materially from price-consistent demand assumptions.
4. **`G_dependency` — Dependency and Economic Capture**
   Whether a critical dependency transmits into company economics and shareholder cash flow differently from what price already discounts.

The modules may inform one thesis but must not be averaged into `G_total`, a winner probability, or an automatic promotion state.

**`P_flow_dislocation` is an event-specific sidecar only.** It may diagnose whether a material price move contains non-fundamental pressure. It is not a fifth valuation module and cannot independently advance a thesis.

## E0 Primary Contract

E0 implements only `G_supply` for MU.

The human decision is:

```text
ADVANCE_TO_FULL_RESEARCH
HOLD_FOR_EVIDENCE
REJECT_THESIS
```

The E0 question is:

> Does admissible point-in-time physical evidence support a materially slower memory-supply-relief path than the set of operating and valuation scenarios consistent with MU's decision-time price, and do MU's business and shareholder economics preserve enough of that separation to justify advancing the proposition to full research?

E0 may emit only a model-class-conditional:

```text
PRICE_INCONSISTENCY_CANDIDATE
```

E0 may not claim established mispricing, financial alpha, investability, tradability, a trade recommendation, calibrated probability, or general decision-system effectiveness.

## Market-Consistent Feasible-Envelope Rule

One market price does not identify one exact belief vector.

E0 therefore produces:

- a deterministic feasible expectations set;
- explicit parameter domains and evidence-derived bounds;
- disconnected feasible regions when they exist;
- complete sensitivity and conservative bound-expansion results;
- explicit `NON_IDENTIFIABLE`, `BOUNDS_UNJUSTIFIED`, `MODEL_INADEQUATE`, or `INFEASIBILITY_UNCERTIFIED` outcomes;
- no probability weights, P10/P50/P90 paths, likelihoods, or scalar confidence scores without a separately preregistered calibration basis.

The default first model family is a finite, bounded scenario lattice with complete enumeration. A solver may replace enumeration only when the model class, global-proof authority, accepted statuses, tolerances, and retained proof artifact are frozen in P0.

## Point-in-Time Evidence Law

Every indispensable evidence item must expose:

- exact artifact and source locator;
- permitted-use or licence status;
- publication time and `known_at` time;
- effective period;
- revision or vintage policy;
- upstream source identity and duplication relationship;
- entity, segment, product, period, currency, and units;
- `OBSERVED`, `ESTIMATED`, `INFERRED`, or `UNKNOWN` status;
- allowed claim influence;
- explicitly forbidden conclusions.

Freshness is computed from the registered policy rather than entered as subjective confidence. Missing, stale, contradictory, duplicated, revised, unknown, negative, and not applicable remain distinct.

Current snapshots, revised histories, retrospective reconstructions, correlated reports from one upstream source, and inaccessible licensed data cannot silently become point-in-time evidence.

## Supply-Demand Identification Rule

Price, margins, lead times, utilization, and inventory can reflect supply restrictions or demand changes.

`G_supply` requires at least one preregistered supply-specific mechanism through direct physical evidence, timing restrictions, cross-segment or cross-producer implications, or a falsifier that separates supply inertia from demand acceleration.

If the two explanations remain observationally interchangeable, the required result is `NON_IDENTIFIABLE`.

## Two-Stage Capture Gate

```text
physical supply condition
→ industry economics
→ MU business capture
→ shareholder cash-flow capture
→ relationship to the decision-time price envelope
```

Business capture and shareholder capture are separate claims. Failure or uncertainty at one arrow cannot be repaired by narrative from another arrow.

## Model Self-Falsification Rule

Before `PRICE_INCONSISTENCY_CANDIDATE`, E0 must prove all of the following under the registered protocol:

1. the control model can accommodate the decision-time price before the physical constraint is imposed;
2. dimensions, segments, stock-flow identities, and accounting bridges reconcile;
3. every material bound has evidence authority and a frozen conservative expansion rule;
4. supply and demand are sufficiently identified;
5. non-overlap is completely enumerated or globally certified;
6. physical-constraint ablation removes or materially reduces the separation;
7. a frozen broader or challenge model does not eliminate the result;
8. business and shareholder capture remain supported;
9. no forced falsifier has triggered;
10. the minimum robust price-equivalent separation exceeds the preregistered materiality threshold;
11. every prior evidence-bearing model attempt is disclosed.

Failure produces the appropriate model or claim state. It never defaults to a market-error conclusion.

## Orthogonal Result Model

### Run state

```text
VALID
BLOCKED
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

Each preregistered claim is independently:

```text
SUPPORTED
FALSIFIED
UNKNOWN
NOT_EVALUATED
```

The minimum claims are:

- `C1_PHYSICAL_RELIEF_SLOWER`;
- `C2_MU_BUSINESS_CAPTURE`;
- `C3_SHAREHOLDER_CAPTURE`;
- `C4_PRICE_ENVELOPE_MATERIALLY_SEPARATED`.

### Candidate output

```text
NONE
PRICE_INCONSISTENCY_CANDIDATE
```

### Human decision

```text
ADVANCE_TO_FULL_RESEARCH
HOLD_FOR_EVIDENCE
REJECT_THESIS
```

A candidate requires `VALID`, `ADEQUACY_GATE_PASSED`, and all four claims `SUPPORTED`. The human decision remains independent.

## Frozen Cheap-Baseline Endpoint

The primary E0 comparison is:

> **Whether GodView produces a higher-quality research-triage decision than the cheap human baseline under an identical, fixed human-analysis time budget.**

Both arms receive the same sealed admissible evidence bundle, timestamp, information cutoff, instructions, action set, horizon, and fixed human-analysis time. Outside research and post-cutoff information are prohibited.

The baseline decision is canonicalized, timestamped, and cryptographically sealed before the GodView packet is exposed.

The preregistered rubric covers:

1. selected action;
2. indispensable missing evidence;
3. falsifiers and contradictions;
4. separation of supply, demand, business capture, shareholder capture, and valuation claims;
5. avoidance of claims beyond the evidence;
6. rationale traceability.

E0 reports only the observed within-case difference and rationale change. Research-latency improvement is a separate prospective endpoint and is not inferred from E0 elapsed time.

## Path to Financial Alpha

```text
PORTFOLIO TRUTH — Ship deterministic paper account, actions, cash, costs, risk, attribution, and replay
RESEARCH FEED — Upgrade or reject portfolio-linked candidates under the frozen evidence contract
POLICY PROOF — Compare cheap deterministic sizing with optimizer proposals on the same replay engine
PROSPECTIVE ECONOMICS — Accumulate cost-, lag-, liquidity-, and drawdown-aware paper evidence
REPLICATION — Repeat across independent companies, modules, reviewers, regimes, and policies
LIVE-CAPITAL GATE — Consider broker and capital authority only when independently earned
FINANCIAL ALPHA — Prospective, cost-adjusted, search-history-aware, independently replicated
```

Every phase must ship a vertical functional slice that exercises the same endgame chain. No phase may be justified only by infrastructure completion.

## Authority and Readiness

- Strategic endgame clarity: **9.7/10**.
- E0 architecture agreement: **9.6/10**.
- E0 implementation readiness after P0 hash freeze: **9.0/10**.
- Current demonstrated financial alpha: **1.5/10**.
- Financial-alpha or trade-authority claim: **denied**.

The phrase `alpha-stage readiness` is retired from product canon because it can be confused with financial alpha. Use `E0 implementation readiness` or `bounded prototype readiness`.

## Current Authority Boundary

Authorized now:

- update and reconcile documentation;
- preserve the four frozen research-contract artifacts;
- build GV-FS0 through one new canonical `PortfolioBook`, without importing or converting legacy replay/lifecycle state;
- accept one synthetic `OPEN` and one synthetic `NO_POSITION` through `DecisionEnvelope`;
- emit immutable `Fs0PortfolioSnapshot` and `Fs0Certification` artifacts;
- render those artifacts through a read-only Streamlit adapter;
- preserve the later path for explicit owner decisions, discovery-only capsules, and research-contract results through the same certified book boundary.

Not authorized by this document alone:

- provider or network access;
- live or historical data acquisition outside separately approved local inputs;
- scanner ratings or performance as allocation authority;
- automatic promotion or autonomous allocation;
- leverage, shorting, derivatives, or hedging;
- broker, orders, or live capital;
- financial-alpha, tradability, or investment claims.

No backward-compatibility obligation applies to superseded signal-first, dashboard-first, provider-first, E0-E8, G7-G12, or M0-M9 roadmap semantics.
