# CYCLE_RESONANCE_v1 — Thin Build Specification

**Date:** 2026-08-09
**Status:** `BUILD_SPEC / PREREGISTERED / CLOCK_1_RELEASED / MECHANICS_PARTIAL`
**Family ID:** `CYCLE_RESONANCE_v1`
**First implementation authority:** **RELEASED AFTER CLOCK #1; INPUT-PACKET + IMPLEMENTATION-MANIFEST MECHANICS IMPLEMENTED**
**Current execution effect:** **NO EMPIRICAL MODEL AUTHORITY YET** — provider-blind PIT packet closure and the explicit no-scientific-defaults implementation-manifest contract are implemented; clock/claim/resonance/model/runner mechanics and the legitimate broad CRV1 risk-set join remain open
**Data dependency:** `docs/architecture/alpha_pit_data_api_v1.md` only
**Strategic role after 2026-08-09 lock:** `SLOW_BUSINESS_CYCLE_FAMILY / 252D_PRIMARY_UNCHANGED / NOT_SOLE_PROGRAMME_CLOCK`
**Programme lock:** `docs/architecture/aov_strategic_direction_lock_20260809.md`

---

# 0. Purpose

Define the exact module seams, inputs, outputs, state transitions, and failure tests for the first post-Clock Alpha Discovery Lane without creating a generic Alpha platform.

The family hypothesis is already preregistered:

```text
supply / capacity discipline
→ inventory normalization
→ pricing inflection
→ utilization / margin inflection
→ earnings revisions
→ expectation gap closes
→ exceptional equity payoff
```

This is a **causal-hypothesis graph**, not a claim of proven causality.

The implementation objective is not to maximize average classification accuracy. It is to determine whether observable, time-correct cycle resonance materially improves **capital-relevant right-tail selection** relative to the incumbent information set.

---

# 1. Frozen family semantics

```text
family_id = CYCLE_RESONANCE_v1
status = PREREGISTERED / MECHANICS_PARTIAL / EMPIRICAL_CANDIDATE_NOT_FROZEN
primary_horizon = 252 trading days from legitimate execution boundary
primary_outcome = top 5% date-local cross-sectional primary-security total return
primary_label_spec = CRV1_RIGHT_TAIL_252D_TOP5_V1
primary_risk_set_spec = CRV1_US_PRIMARY_COMMON_V1
financial_alpha_evidence = 0
```

Changing any of the following after outcome inspection requires a new family/version and search-budget charge:

- primary horizon;
- primary winner definition;
- risk-set semantics;
- economic mechanism family;
- material clock ordering/meaning;
- outcome measure.

Sensitivity outcomes are diagnostic only and do not replace the primary outcome under the same version.

## 1.1 Strategic role — slow hypothesis, not slow programme

The final strategic re-audit explicitly retains CRV1's `252`-trading-day primary horizon. CRV1 is the slow business/company-cycle family and **does not monopolize programme evidence velocity**. A separate genuinely multi-week Alpha Family is authorized for preregistration and may run an independent confirmatory/prospective prediction clock beside CRV1 under the active family WIP law.

Do not shorten CRV1 in place to manufacture faster evidence. Do not inject sector-rotation, tactical price/volume, market-transition or microstructure mechanisms into CRV1 v1 merely to make it multi-scale. Those are separate families/components and require their own identity/search budget/evidence.

CRV1's clock/resonance states are intermediate evidence. Predictive authority belongs to immutable ex-ante `WinnerPredictionV1` artifacts frozen before outcome access.

---

# 2. Non-goals

This build SHALL NOT create:

```text
generic Right-Tail platform
generic Alpha Factory framework
generic provider framework
feature store
scraping platform
news platform
vector/RAG platform
universal AI agent system
portfolio optimizer
broker integration
capital sizing authority
backward compatibility to old data-readiness/API contracts
```

`CYCLE_RESONANCE_v1` consumes the Alpha PIT API. It never imports provider adapters directly.

---

# 3. Target package seam

After Clock #1, implementation should remain narrow:

```text
research/cycle_resonance_v1/
  contracts.py
  pit_packet.py
  clock_features.py
  claim_features.py
  resonance.py
  model.py
  runner.py
```

No provider code belongs in this package.

### Module responsibilities

| Module | Owns | Must not own |
| --- | --- | --- |
| `contracts.py` | family IDs, schemas, implementation manifest, state enums | provider calls, fitting |
| `pit_packet.py` | Alpha PIT API calls + packet closure | provider adapters, outcomes in confirmatory/prospective mode |
| `clock_features.py` | deterministic structured clock transforms | raw provider parsing |
| `claim_features.py` | source-bound claim interpretation/features | source acquisition, evidence authority |
| `resonance.py` | ordered-sequence / resonance representation | model search orchestration |
| `model.py` | one frozen implementation's fit/score/calibration | outcome access in confirmatory/prospective runs |
| `runner.py` | research-mode state machine, Trial/Prediction Ledger handoff | provider access, portfolio capital |

---

# 4. Sole data interface

The family consumes only:

```text
AlphaPITReadAPIv1.risk_set(as_of)
AlphaPITReadAPIv1.observations(ids, fields, as_of)
AlphaPITReadAPIv1.source_claims(ids, as_of)
AlphaPITReadAPIv1.expectations(ids, as_of)
```

In `DISCOVERY` only:

```text
AlphaPITDiscoveryAPIv1.outcomes(risk_set_id, CRV1_RIGHT_TAIL_252D_TOP5_V1)
```

No direct CIQ, SEC, yfinance, old dashboard loader, `permno`, ticker, or old data-readiness access is allowed in this package.

---

# 5. Canonical input packet

## `CycleResonanceInputPacketV1`

```text
schema_version                  cycle_resonance_input_packet_v1
family_id                       CYCLE_RESONANCE_v1
implementation_id               str
research_mode                   DISCOVERY|CONFIRMATORY|PROSPECTIVE
decision_context_id             str
as_of                           timestamp
risk_set_id                     str
risk_set_manifest_sha256        sha256
observations_manifest_sha256    sha256
claims_manifest_sha256          sha256
expectations_manifest_sha256    sha256
source_manifest_sha256s         sorted sha256[]
coverage_policy_id              str
input_packet_sha256             sha256
```

The packet is immutable after construction.

`input_packet_sha256` binds all canonical API manifest hashes, decision context, family, implementation, mode, and `as_of`.

Changing any underlying source byte or canonical artifact changes the packet hash.

---

# 6. Family information request

## 6.1 Structured observations

The initial implementation may request only the `alpha_pit_data_api_v1` closed field set.

Market baseline:

```text
market.close
market.total_return_1d
market.volume
market.adv20
market.realized_vol20
market.sma20
market.sma200
```

Company cycle state:

```text
fund.revenue_q
fund.inventory_q
fund.capex_q
fund.gross_margin_q
fund.operating_margin_q
fund.cash_from_ops_q
```

## 6.2 Expectations

Initial supported expectation measures:

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

## 6.3 Qualitative/source claims

Initial claim topics:

```text
SUPPLY_CAPACITY
INVENTORY_CHANNEL
PRICING
DEMAND
UTILIZATION
MARGIN
GUIDANCE
COMPETITION
OTHER_RELEVANT_CYCLE
```

Source claims are observed/source-bound objects. Interpretation of those claims is a separate inferred feature layer.

---

# 7. Cycle clocks

The family defines these canonical clock identities:

```text
SUPPLY_CAPACITY_CLOCK
INVENTORY_CLOCK
PRICING_CLOCK
DEMAND_CLOCK
UTILIZATION_MARGIN_CLOCK
EARNINGS_REVISIONS_CLOCK
EXPECTATION_GAP_CLOCK
MARKET_CONFIRMATION_CLOCK
```

The family hypothesis does **not** require every security to have every clock observable. Missingness/coverage is explicit and governed by the frozen `CoveragePolicyV1` in the implementation manifest.

There is no hidden default coverage threshold in code.

---

# 8. Clock representation contract

Every clock may expose four preregistered representations:

```text
LEVEL
DELTA
INFLECTION
ORDERED_SEQUENCE
```

## `CycleClockEvidenceV1`

```text
schema_version                cycle_clock_evidence_v1
security_id                   str
clock_id                      enum
as_of                         timestamp
level_value                   float|null
delta_value                   float|null
inflection_state              NEGATIVE_TURN|NO_TURN|POSITIVE_TURN|UNKNOWN
inflection_at                 timestamp|null
state_score                   float|null
state_direction               NEGATIVE|NEUTRAL|POSITIVE|UNKNOWN
coverage_status               PRESENT|PARTIAL|MISSING|NOT_APPLICABLE
observed_evidence_refs        sorted artifact-row-hash[]
inferred_feature_refs         sorted inferred-feature-hash[]
max_available_at              timestamp|null
transform_id                  str
transform_sha256              sha256
clock_evidence_sha256         sha256
```

`state_score`, thresholds, and transform semantics are implementation parameters. They must be frozen in the implementation manifest before confirmatory use.

No transform may use a datum with `available_at > as_of`.

---

# 9. Qualitative / AI claim feature seam

Qualitative evidence is not secondary, but AI interpretation is not evidence authority.

`source_claims()` provides observed/source-bound claims.

`claim_features.py` may transform those claims into family-specific inferred features.

## `CycleClaimFeatureV1`

```text
schema_version                 cycle_claim_feature_v1
security_id                    str
source_claim_id                str
claim_topic                    enum
interpreted_direction          NEGATIVE|NEUTRAL|POSITIVE|MIXED|UNKNOWN
interpreted_strength           float|null
interpreted_horizon            CURRENT|NEXT_QUARTER|NEXT_YEAR|MULTIYEAR|UNKNOWN
clock_id                       enum|null
model_or_rule_id               str
procedure_sha256               sha256
source_claim_row_hash          sha256
epistemic_class                INFERRED_FEATURE
feature_sha256                 sha256
```

Rules:

- the source claim reference is mandatory;
- the interpreter cannot invent a new observed fact;
- AI model/prompt/procedure identity is hash-bound;
- changing model/prompt/procedure consumes Trial/Search budget;
- confirmatory/prospective runs use the exact frozen interpreter bytes/config;
- LLM confidence is not a prediction probability and is not capital authority.

---

# 10. Resonance representation — how the system encodes “clean logic”

`resonance.py` does not attempt to prove causality. It encodes whether the preregistered hypothesis graph is supported by time-correct evidence.

## `CycleResonanceStateV1`

```text
schema_version                 cycle_resonance_state_v1
security_id                    str
as_of                          timestamp
implementation_id              str
clock_evidence_hashes          sorted sha256[]
active_clock_count             int
positive_clock_count           int
negative_clock_count           int
ordered_sequence_state         NOT_ESTABLISHED|PARTIAL|ESTABLISHED|CONTRADICTED
sequence_progress              float|null
expectation_gap_state          NEGATIVE|NONE|POSITIVE|UNKNOWN
market_confirmation_state      NEGATIVE|NONE|POSITIVE|UNKNOWN
falsifier_state                CLEAR|WATCH|TRIGGERED|UNKNOWN
coverage_policy_id             str
coverage_status                ELIGIBLE|INSUFFICIENT|CONTRADICTORY
resonance_feature_vector_hash  sha256
resonance_state_sha256         sha256
```

“Clean logic” means the output is traceable to:

```text
observed source rows
→ source-bound claim rows
→ versioned inferred claim features
→ versioned clock transforms
→ declared ordered-sequence test
→ declared expectation-gap test
```

A high score without this lineage is not `CYCLE_RESONANCE_v1` authority.

---

# 11. Ordered-sequence semantics

The default hypothesis ordering is:

```text
SUPPLY_CAPACITY
→ INVENTORY
→ PRICING
→ UTILIZATION_MARGIN
→ EARNINGS_REVISIONS
→ EXPECTATION_GAP resolution
```

`DEMAND_CLOCK` and `MARKET_CONFIRMATION_CLOCK` are corroborating/state clocks and may be included in the frozen implementation without changing the family identity.

The implementation manifest must define:

```text
required edges
allowed skipped edges
maximum temporal lag between edges
clock-specific inflection definition
how contradictions are scored
how missing clocks affect eligibility
```

There are no code defaults for these scientific choices. Missing values in the manifest are a hard error.

A future material reordering of the mechanism creates a new family/version.

---

# 12. Implementation manifest

## `CycleResonanceImplementationManifestV1`

Before a confirmatory run, freeze:

```text
family_id
implementation_id
family_contract_sha256
risk_set_spec_id
primary_label_spec_id
requested_observation_fields
requested_expectation_measures
claim_topics
coverage_policy
clock_transform_ids + hashes
claim_interpreter_id + hash
ordered_sequence_spec
falsifier_spec
model_class / algorithm
model hyperparameters
training window rule
calibration method or NONE
ranking rule
search_family_id
preregistered search budget
actual trials consumed at freeze time
cost assumptions for economic diagnostics
code-byte manifest
manifest_sha256
```

No runtime default may fill an omitted scientific parameter.

---

# 13. Model seam

`model.py` maps immutable resonance/input state to a prediction. It does not access outcomes in confirmatory/prospective mode.

Recommended interface:

```python
def fit(
    *,
    training_packets: Sequence[CycleResonanceInputPacketV1],
    discovery_labels: Sequence[DiscoveryLabelRef],
    manifest: CycleResonanceImplementationManifestV1,
) -> FrozenCycleResonanceModelV1: ...


def predict(
    *,
    model: FrozenCycleResonanceModelV1,
    packet: CycleResonanceInputPacketV1,
) -> Sequence[WinnerPredictionV1]: ...
```

`fit()` is allowed only in discovery/development surfaces.

Confirmatory/prospective runner receives a frozen model artifact; it cannot refit.

---

# 14. Prediction output

## `WinnerPredictionV1`

```text
schema_version                 winner_prediction_v1
prediction_id                  content-addressed id
family_id                      CYCLE_RESONANCE_v1
implementation_id              str
security_id                    str
as_of                          timestamp
risk_set_id                    str
input_packet_sha256            sha256
resonance_state_sha256         sha256
raw_score                      float
calibrated_winner_probability  float|null
calibration_id                 str|null
rank_within_risk_set           int
conviction_bucket              str|null
coverage_status                ELIGIBLE
falsifier_state                CLEAR|WATCH|UNKNOWN
model_sha256                   sha256
prediction_sha256              sha256
```

Rules:

- raw score is not automatically a probability;
- probability requires a frozen calibration artifact;
- no portfolio weight or order quantity is emitted;
- no `BUY/SELL` action is emitted;
- ranking is research output, not capital authority;
- prediction is written to Prediction Ledger before outcomes can be evaluated.

---

# 15. Research state machine

```text
PREREGISTERED                [current]
↓ Clock #1 + data/API build authority
DISCOVERY_READY
↓
DISCOVERY_OPEN
↓ mechanism / implementation search under Trial Ledger
IMPLEMENTATION_FROZEN
↓
HISTORICAL_CONFIRMATORY_RUN
↓ predictions sealed before evaluator opens labels
HISTORICAL_EVALUATED
↓ if evidence supports / or untouched history unavailable but honest prospective test is justified
PROSPECTIVE_SEALED
↓
PROSPECTIVE_RUNNING
↓ maturity
PROSPECTIVE_REVIEWABLE
```

Failure/hold states:

```text
VERSION_CLOSED_INVALID
VERSION_CLOSED_SEARCH_CONTAMINATED
HOLD_REDUNDANT
HOLD_NONMONETIZABLE
HOLD_REGIME_BOUND
HOLD_INSUFFICIENT_EVIDENCE
RETIRED_DECAYED
```

A failed version cannot silently return to `DISCOVERY_OPEN` with altered horizon/universe/label/mechanism and retain the same identity.

---

# 16. Discovery mode

Discovery may inspect:

```text
right-tail outcomes
near-winners
ordinary controls
plausible-story controls
catastrophic losers
within-company non-resonance periods
```

Discovery output is hypothesis-generation evidence only.

The canonical forensic unit is a **right-tail episode**, not a famous winner company. When legitimate coverage permits, discovery should enumerate all qualifying episodes under the frozen `CRV1_RIGHT_TAIL_252D_TOP5_V1` label inside the covered date-local risk set; one company may contribute multiple episodes, and incomplete reconstruction coverage must remain explicit rather than silently dropping difficult cases.

For every candidate resonance precursor / mechanism, discovery should deliberately retain four contrast populations:

```text
TRUE_RIGHT_TAIL
precursor present + frozen right-tail outcome

FALSE_WINNER
precursor present + no frozen right-tail outcome

MISSED_RIGHT_TAIL
frozen right-tail outcome + precursor absent / model miss

MATCHED_ORDINARY_OR_LEFT_CONTROL
PIT ex-ante lookalike + no right-tail outcome
```

Matching variables may include declared PIT-available sector/industry, size, valuation, regime, and other preregistered controls. Matched reconstruction is an analyst-efficiency device; final evaluation still uses the full risk set and frozen base rates.

Discovery may compare LEVEL/DELTA/INFLECTION/ORDERED_SEQUENCE implementations, but every material variant is a Trial Ledger entry.

The system SHOULD actively prioritize informative controls, especially cases that looked like a clean cycle resonance ex ante but failed, plus missed winners that expose incumbent/candidate blind spots.

Discovery also produces a diagnostic **winner-blindness audit** for the frozen incumbent organism without tuning it from outcomes:

```text
universe admitted in time?
Rule100 / Parent / Child detected before most payoff?
frozen cap/sizing owned meaningful exposure?
missingness / identity / staleness rules excluded it?
time-to-first-legitimate-detection
premature exit / insurance clipping of an intact winner?
```

This audit has no authority to mutate Rule100/Parent/Child and cannot be cited as financial-alpha evidence.

Finally, treat winner capture as three separable research objects:

```text
DISCOVERY_ENTRY
CONTINUATION_HOLD
EXIT_FALSIFIER
```

A model that discovers an episode does not automatically own hold/exit skill. Any continuation component must consume only PIT thesis-continuation evidence and frozen falsifier state; unrealized P&L is not an alpha input.

---

# 17. Confirmatory mode

Confirmatory mode receives only PIT packets and a frozen implementation.

It MUST NOT:

```text
call outcomes()
import discovery_outcomes.py
refit model
change coverage policy
change winner threshold
change horizon
change clock definitions
change prompt/model interpreter
change risk-set definition
```

Predictions are persisted immutably first.

A separate evaluator later joins prediction IDs to hidden outcome labels and computes evaluation metrics.

---

# 18. Prospective mode

Prospective mode is stricter than historical confirmatory mode:

```text
current decision cut
→ Alpha PIT read packet
→ frozen transforms/model
→ immutable prediction artifact
→ Prediction Ledger
→ no outcome access until maturity
```

No historical rescue is permitted after the prospective tape starts.

A later family version can be registered, but the running tape remains immutable.

---

# 19. Evaluation contract

Primary evaluation is right-tail and incremental, not standalone CAGR/Sharpe. CRV1 may independently become evidence-qualified while other families are also qualifying; this does not itself create portfolio capital authority. Portfolio composition remains an `I` versus `I+X` marginal economic decision under one current capital-policy authority.

Required comparison:

```text
INCUMBENT information system = I
CANDIDATE system = I + CYCLE_RESONANCE_v1
```

Hold constant:

```text
PIT cut
risk set
cost assumptions
portfolio objective
risk constraints
execution assumptions
```

Required scientific/economic metrics include:

```text
Precision@5 / @10 / @20
Lift@K
Recall@K
PR-AUC / Average Precision
Brier score / calibration diagnostics when probability exists
Conviction Monotonicity
False-Winner Rate
Missed-Right-Tail Rate / Recall@K
Catastrophic-False-Winner Rate
Time-to-First-Legitimate-Detection
Premature-Exit / Continuation-Capture diagnostics
Right-Tail Wealth Capture
Capital-Weighted Wealth Capture [shadow diagnostic only]
Right-Tail Capture Efficiency [shadow diagnostic only]
I vs I+X incremental net utility
```

CAGR, Sharpe, drawdown, ROC-AUC, generic hit rate, and feature importance are diagnostics only.

---

# 20. Dependence / episode accounting

The evaluator must report:

```text
raw security-observation count
effective independent episode count
sector/industry clustering
shared macro-cycle grouping
overlapping-horizon dependence
```

A single memory upcycle producing many semiconductor winners is not treated as many independent macro episodes.

HAC/cluster-aware inference/block bootstrap may be used as appropriate; the method is frozen per evaluation version.

---

# 21. Minimum Viable Atlas acceptance

The first prospective seal SHALL NOT wait for exhaustive historical reconstruction.

The programme also has a separate first-class **Lane 2 Historical Compression** for the frozen incumbent: legitimate historical PIT CIQ → exact frozen-AOV replay → A1 → freeze hidden A2 contract → query-metered untouched A2. Lane-2 A1/A2 measures Parent/Child economics and may inform a PM/CEO `CONTINUE / PIVOT / HOLD` decision; it does **not** become untouched CRV1 evidence. If A1/A2 causes a material CRV1 hypothesis/implementation change, create a new CRV1 version/family/search charge rather than rescue v1 in place.

Minimum approved sequence:

```text
1. Alpha PIT API sufficient for declared first-family sources
2. legitimate date-local risk set
3. enough historical PIT observations/claims/expectations for honest discovery
4. contemporaneous controls + near-winner / failure contrasts, including false-winner and missed-right-tail cases
5. diagnostic incumbent winner-blindness review; no Parent/Child tuning authority
6. freeze one implementation manifest
7. untouched historical test where legitimate untouched data exists
8. if no legitimate untouched history exists, record that fact rather than fabricate it
9. seal prospective Challenger as soon as the evidence contract is honest
10. deepen historical risk set / false-winner / missed-winner / matched-control library and replication while tape runs
```

There is no requirement to reconstruct a universal ten-year text/capacity history before the first prospective seal.

---

# 22. Search-budget semantics

Each of these consumes search budget:

```text
clock transform variant
claim interpreter / prompt / model variant
coverage policy variant
ordered-sequence parameter variant
model class
hyperparameter set
training window
calibration method
ranking threshold
control definition
```

These require a new family/version, not merely another trial:

```text
primary horizon
primary outcome label
risk-set semantics
material economic mechanism
material causal-order hypothesis
```

All negative trials remain retained.

---

# 23. Falsifier contract

Family/version-level falsifiers include:

```text
no incremental I vs I+X value
no right-tail enrichment
no conviction monotonicity
mechanism sequence indistinguishable from controls / near-winners
claimed ordered timing fails
false-winner burden makes top-K commercially unusable
search contamination prevents attribution
independent replication fails
prospective effect fails
real edge becomes nonmonetizable after realistic cost/capacity
```

A triggered falsifier does not permit outcome-driven redefinition under the same family/version.

Per-security thesis `WATCH` or `TRIGGERED` states are model inputs/diagnostics only until a separately preregistered capital state machine exists.

---

# 24. Required failure-injection tests

Before the first prospective seal, test at least:

1. direct provider import from `research/cycle_resonance_v1/` → FAIL;
2. old readiness/API/ticker/permno fallback import → FAIL;
3. `available_at > as_of` in any clock evidence → FAIL;
4. source-claim hash mutation → input packet/prediction closure FAIL;
5. AI claim feature without source claim → FAIL;
6. AI claim feature procedure hash drift → FAIL;
7. confirmatory/prospective import of discovery outcome capability → FAIL;
8. confirmatory model refit attempt → FAIL;
9. same frozen packet/model → exact same prediction bytes/hash;
10. changed canonical source manifest → changed packet/prediction hash;
11. missing required implementation-manifest scientific parameter → FAIL, no default;
12. silent missing observation/claim/expectation drop → FAIL;
13. future inflection used in an earlier decision cut → FAIL;
14. primary label/horizon/risk-set change under same family version → FAIL;
15. Trial Ledger count does not increase after material implementation search → FAIL;
16. prediction emitted with portfolio weight/order quantity → FAIL;
17. raw score mislabeled as calibrated probability → FAIL;
18. outcome evaluation performed before prediction artifact is immutable → FAIL;
19. effective independent episode count omitted from mature evaluation → FAIL;
20. search/coverage/source manifests omitted from promotion packet → FAIL.

---

# 25. Build order after Clock #1 — parallel producer / consumer construction

`alpha_pit_data_api_v1` remains the sole real data dependency, but CRV1 engineering does not wait for every concrete adapter to finish. The frozen API contract is the integration seam.

```text
J1 CONTRACT
1. consume deterministic alpha_pit_data_api_v1 contract fixtures
2. build pit_packet.py closure against fixture ArtifactRefs

PARALLEL CRV1 WORK
3. implement structured clock transforms
4. implement narrow source-claim interpretation seam
5. implement resonance state / ordered sequence
6. implement prediction/model/manifest/Trial-Ledger mechanics

PARALLEL ALPHA PIT PRODUCER WORK
alpha_pit_data_api_v1 builds real CIQ/SEC adapters, content-addressed manifests,
coverage/missingness and capability-firewall tests in its own authority domain

J3 REAL PIT INTEGRATION
7. substitute real API artifacts for fixtures without changing CRV1 provider boundaries
8. run discovery under explicit outcomes capability
9. freeze one implementation manifest
10. run confirmatory prediction process with outcome capability absent
11. evaluate separately
12. seal prospectively as soon as honest
```

A fixture cannot count as historical PIT evidence, untouched evidence or prospective evidence. Lane 2 A1/A2 may run concurrently under separate writer/evidence custody because it evaluates the frozen incumbent rather than writing CRV1 authority. The confirmatory Alpha-family WIP slot remains singular: Market Transition may run discovery in parallel but cannot build a second confirmatory family beside CRV1. Historical Atlas breadth beyond the A1/A2 economic question, more providers, a second confirmatory family, and shared platform abstractions remain downstream until evidence demands them.

---

# 26. Exit criteria for this build spec

The first family is implementation-ready when:

```text
Alpha PIT API contracts implemented and failure-tested
+ family input packet closes deterministically
+ clock/claim/resonance outputs are content-addressed
+ implementation manifest has no scientific defaults
+ discovery/confirmatory capability firewall is mechanically enforced
+ Trial/Prediction Ledger hooks are present
+ frozen model predicts without outcome access
+ separate evaluator can compute I vs I+X and right-tail metrics
+ prospective prediction can be sealed without historical rescue
```

This does **not** mean the Alpha Family has proven alpha.

---

# 27. Current authority statement

```text
ACTIVE_PRODUCT_STATE = CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED
CLOCK_1_STARTED = TRUE
CYCLE_RESONANCE_v1 = PREREGISTERED / INPUT_PACKET_AND_IMPLEMENTATION_MANIFEST_MECHANICS_IMPLEMENTED / EMPIRICAL_CANDIDATE_NOT_FROZEN
ALPHA_PIT_DATA_API_V1 = MECHANICS_IMPLEMENTED / CURRENT_CIQ_STRUCTURED_CUSTODY_VERIFIED / CRV1_RISK_SET_BLOCKED
financial_alpha_evidence = 0
LIVE = CLOSED
```

Clock #1 released the first confirmatory Alpha-family build slot. `pit_packet.py` now closes provider-blind Alpha PIT artifacts deterministically, and `implementation_manifest.py` requires every scientific choice explicitly before freeze: family/risk-set/label identity, observation/expectation/claim surfaces, coverage policy, transform hashes, claim interpreter, ordered-sequence law, falsifiers, model/hyperparameters, training/calibration/ranking rules, search-family budget, cost assumptions, and code-byte identity. Missing scientific parameters fail closed; search trials cannot exceed the preregistered budget; sealed manifest tampering fails hash verification. Clock/claim/resonance/model/runner mechanics remain open, discovery/outcome visibility remains quarantined, no empirical or prospective prediction is yet sealed for this family, and financial-alpha evidence remains `0`.
