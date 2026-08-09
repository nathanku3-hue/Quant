# AI Research Pipeline v0 — Bounded Post-Clock Research Acceleration

**Date:** 2026-08-08
**Status:** `BUILD_SPEC / CLOCK_1_RELEASED / NOT_IMPLEMENTED`
**Authority:** research-workflow and provenance design; bounded tooling may start only under genuinely independent ownership and may not slow Future Truth, Historical Compression, the authorized fast-family clock, or PAPER-0 minimum closure
**Current execution effect:** **SUPPORTING TOOLING LANE / NO FINANCIAL AUTHORITY** — Clock #1 is running; AI is not a critical-path substitute for measuring incumbent AOV economics
**Financial-alpha evidence:** `0`

---

# 0. Purpose

Define the smallest AI research layer that can accelerate discovery, source interpretation, control finding, review translation and bounded mutation without making an LLM the source of financial truth.

North star:

> **AI allocates research attention and drafts scientific actions; deterministic systems own evidence, accounting, promotion, risk and capital.**

Canonical endgame:

```text
immutable PIT evidence
→ deterministic state / portfolio organism
→ immutable prospective prediction / policy
→ prospective outcome
→ deterministic ReviewPacket
→ bounded AI interpretation / hypothesis / mutation proposal
→ deterministic validation and compile
→ Trial Ledger
→ development / untouched OOS where legitimate
→ prospective Challenger seal
→ repeated prospective evidence
→ independent replication
→ deterministic promotion decision
→ bounded capital authority
```

---

# 1. Authority firewall

AI is never source of truth for:

```text
permanent identity
provider timestamps
known_at / available_at
PIT eligibility
returns
target weights
cash
portfolio accounting
broker fills
transaction costs
CVaR / hard risk limits
kill switches
promotion evidence
Clock-Start Receipts
prospective maturity
financial-alpha evidence
```

AI may propose:

```text
hypotheses
candidate mechanisms
source requests
control populations
feature specifications
experiment definitions
bounded mutations
failure interpretations
next research priorities
```

AI may support several independently owned family clocks, but it cannot merge their evidence into capital authority. Evidence qualification remains deterministic/family-bound; current portfolio/capital-policy authority remains singular.

All AI outputs are `NON_AUTHORITATIVE` until a deterministic admission boundary accepts them.

---

# 2. Role separation

## 2.1 `DISCOVERY_AI`

May inspect declared historical outcomes and the Right-Tail / Crisis discovery atlases. May generate mechanisms, representations, features and falsifiers. Has zero confirmatory, OOS, prospective or capital authority. Every evaluated material variant consumes search budget.

## 2.2 `CONTROL_FINDER_AI`

May inspect outcomes to find false-positive precursors, near winners, plausible-story failures, ordinary/left-tail controls, catastrophic controls and missed-right-tail episodes. Matching dimensions and reconstruction missingness remain explicit. Matched sets are discovery aids only; confirmation returns to the full risk set/base rate.

## 2.3 `CONFIRMATORY_AI`

Receives only the admissible PIT packet at the decision cut. It receives no future returns, eventual-winner labels, hidden-OOS results or later thesis outcomes. Prompt/template/model/procedure are frozen before evaluation. A material prompt/model/procedure change creates a new Trial or implementation version.

## 2.4 `RED_TEAM_AI`

Receives the current thesis plus admissible contradicting PIT evidence and drafts falsifiers, missing-evidence findings, alternative mechanisms, evidence dependencies, hidden assumptions and overclaiming risks. Deterministic rules decide whether a hard falsifier fired.

## 2.5 `REVIEW_TRANSLATOR_AI`

Activates only on an immutable validated ReviewPacket. It cannot change gross/cost/net deltas, accounting residuals or deterministic classifications. It may draft explanations, ontology candidates and next experiments. Accounting failure blocks invocation.

## 2.6 `MUTATION_AI`

A real outcome-informed mutation requires a matured valid ReviewPacket. It creates one bounded `MutationManifestDraft` per authorized iteration and cannot directly edit strategy code, production config, Parent, frozen V0 parameters, hidden OOS or future prospective outcomes. Deterministic validation/compile converts a valid draft into executable development work.

## 2.7 `RESEARCH_CAPITAL_ALLOCATOR_AI`

Long-run role only. It may rank experiments by decision-changing value, economic impact, information independence, power, calendar time, data/compute/human/AI cost, untouched evidence consumed and search debt. It may recommend research budgets; it never allocates portfolio weight, leverage, shorts, broker orders or live limits.

---

# 3. `AIInvocationReceipt`

Every material AI invocation that enters the research process SHALL bind at least:

```text
ai_run_id
role
registered_at
provider
model_family
model_identifier
model_version_if_available
prompt_template_hash
system_instruction_hash
input_packet_ids
input_packet_hashes
tool_authority_manifest_hash
outcome_visibility_class
search_family_id
trial_id
budget_class
token_compute_usage
generated_output_hash
raw_output_retention_locator
parser_version
status
```

Rules:

- record exact model identity when exposed by the provider;
- do not claim generative reproducibility when provider/model state is not reproducible;
- replay retained output bytes rather than pretending identical prose can be regenerated;
- hash exact input evidence, prompt template, tool permissions and output;
- retain rejected outputs/prompts when they affected candidate selection;
- material prompt/model changes count as search degrees of freedom;
- never store API/broker credentials in receipts, Trial Ledger or model context;
- provider outage = `FAILED_INFRA`;
- malformed output = `FAILED_AI_PARSE`;
- authority violation = `REJECTED_AUTHORITY`;
- invalid scientific hypothesis = research rejection, not infrastructure failure.

---

# 4. Non-authoritative object taxonomy

Initial draft objects:

```text
ResearchSourceCandidate
EvidenceExtractionDraft
HypothesisDraft
MechanismGraphDraft
ControlSetDraft
FeatureSpecDraft
TrialDefinitionDraft
MutationManifestDraft
ReviewExplanationDraft
ResearchPriorityDraft
OperatorExplanationDraft
```

Every draft binds:

```text
authority = NON_AUTHORITATIVE
source/input IDs
AIInvocationReceipt ID/hash
search_family_id
outcome_visibility_class
hidden_evidence_visibility
allowed_next_transition
```

No draft directly enters accounting, broker execution, accepted thesis state or promotion authority.

---

# 5. External-source evidence path

Allowed:

```text
ExternalSource
→ RawReceipt
→ Parser / source-bound extraction
→ EvidenceCandidate
→ deterministic evidence validation
→ admitted EvidenceReference
```

Forbidden:

```text
website / repository / filing
→ LLM summary
→ trusted model feature
```

Every admitted fact retains original-source linkage, timestamps, provenance, units, entity/period mapping, revision/vintage state, upstream/duplicate relationship and `OBSERVED / ESTIMATED / INFERRED / UNKNOWN` epistemic class.

LLM extraction confidence is not evidence confidence. Contradictory evidence stays contradictory. Missing/stale evidence stays missing/stale.

---

# 6. Hypothesis admission

Only registered hypotheses enter research authority. A registered hypothesis states:

```text
economic mechanism
target population
PIT inputs
representation
expected direction
horizon
falsifier
cost assumptions
search family
search budget
expected capital relevance
measurable implication
```

“Interesting pattern” or “LLM thinks bullish” is insufficient. Historical outcome-visible observations create hypotheses/search debt only. No historical rescue after prospective failure under the same version.

---

# 7. Trial Ledger integration

Every AI-generated hypothesis/model that receives a real evaluation gets a `TrialDefinition` binding:

```text
parent trial
search family
hypothesis family
feature/model spec
target / horizon / universe
code hash
prompt hash
AI model identity
input hashes
split specification
search budget
```

Trial definitions, attempts and outcomes are append-only. Material changes to hypothesis, prompt, target or horizon create new versioned research objects. Failed/rejected AI hypotheses remain visible. Duplicate hypotheses are linked, not silently erased.

Search-budget consumption includes model, feature, prompt, target, horizon and threshold variants.

---

# 8. Hostile-source / prompt-injection boundary

All external documents and repositories are untrusted data.

Source text cannot:

```text
change AI role
change tool permissions
request secrets
expand network egress
alter search budget
alter target definition
alter hidden-OOS permissions
alter capital authority
become agent authority because it appears in README/source text
```

Future research agents use source-content delimiters, allowlisted network/file/tool scope, sandboxed shell authority, no broker APIs, and no production credentials. Code extracted from sources is never executed or installed automatically. Dependency/security/license review precedes reuse.

---

# 9. Post-Clock activation — modified for velocity

The real ReviewPacket should gate **outcome-informed use**, not all AI engineering.

## 9.1 `AI-DISCOVERY-CLAIM-VERTICAL-0`

Activation status: **Clock #1 is now running**, so this bounded tooling slice may start only with independent ownership and without delaying Alpha PIT / `CYCLE_RESONANCE_v1`.

```text
immutable source-bound claim packet or contract fixture
→ AIInvocationReceipt
→ one bounded inferred-feature / control / hypothesis schema
→ deterministic schema + authority validator
→ Trial/Search Ledger charge when evaluated
```

Initial constraints:

```text
one AI/provider incumbent
one orchestration approach
one prompt/schema family per role
one output schema per first vertical
zero broker/capital interaction
zero hidden-OOS access
zero autonomous code edits
```

This may supply the already-preregistered `CYCLE_RESONANCE_v1` claim-feature seam, provided confirmatory/prospective runs use the exact frozen interpreter and have no outcome capability.

## 9.2 `AI-REVIEW-MUTATION-VERTICAL-0`

The schema/validator/compiler **may be built and tested on immutable synthetic/fixture ReviewPackets after Clock #1** in parallel.

Real outcome-informed activation remains blocked until:

```text
matured ReviewPacket
+ deterministic reconciliation PASS
+ immutable packet hash verified
```

Then:

```text
validated deterministic ReviewPacket
→ ReviewExplanationDraft / one MutationManifestDraft
→ deterministic authority/schema validator
→ bounded deterministic compiler
→ one development Trial
→ Trial Ledger
→ canonical evaluation
```

A fixture proves engineering mechanics only; it is not financial evidence.

## 9.3 Research Capital Allocator

Deferred until enough real Trials/ReviewPackets exist for resource-allocation ranking to have a real consumer.

---

# 10. External repository quarantine matrix

The classifications below are design intent only. **No license/dependency/security audit or code adoption is claimed by this document.**

| Repository / product | Classification | Reusable pattern | Forbidden authority |
| --- | --- | --- | --- |
| `daily_stock_analysis` | `REFERENCE_RESEARCH_INTAKE_AND_AI_UX` | multi-source intake, jobs, context assembly, reports, modular AI tasks | ratings/BUY-SELL-HOLD/target/stop levels as GodView capital truth |
| `AlphaEvo` | `REFERENCE_BOUNDED_RESEARCH_EVOLUTION` | iterative hypothesis→implementation→evaluation→feedback | unrestricted self-evolution or arbitrary generated Python against canonical state |
| Microsoft RD-Agent | `REFERENCE_RESEARCH_DEVELOPMENT_LOOP` | Research/Development/Evaluation/Feedback separation | autonomous mutation of accepted contracts, sealed hypotheses or production parameters |
| Qlib | `REFERENCE_RESEARCH_SANDBOX_AND_EXPERIMENT_PATTERNS` | dataset/model/factor workflow patterns | second canonical runner or automatic evidence authority |
| Minara | `REFERENCE_PRODUCT_AND_OPERATOR_UX` | copilot/research workspace/strategy studio/inspectable workflow | prompt→strategy→live execution or AI override of deterministic rejection |
| `ndx-momentum-hedge` | `REFERENCE_ADVERSARIAL_STRATEGY_SPECIMEN` | typed external-strategy reconstruction/red-team fixture | published performance as GodView evidence |
| NautilusTrader | `REFERENCE_EVENT_AND_EXECUTION_ARCHITECTURE` | event/order lifecycle, simulation/live parity, replay patterns | second OMS or external broker truth |
| OpenBB | `REFERENCE_PROVIDER_ADAPTER_SURFACE` | source adapter ideas when a real family needs them | universal data layer, CIQ substitution, trusted generic dataframe |

External code adoption requires one exact current consumer, one exact missing capability, evidence that native implementation is materially worse, license/maintenance/dependency/network/telemetry/secret/filesystem/subprocess review, exact version pinning, failure isolation and proof that removing the dependency does not destroy portfolio truth.

---

# 11. One-incumbent policy

Initially:

```text
one LLM/provider incumbent
one orchestration approach
one experiment runner authority
one prompt/schema family per AI role
one AI receipt format
one Trial Ledger
one Prediction Ledger
one canonical portfolio engine
one broker/OMS path
```

Alternatives become Challengers after observed incumbent deficiency. Do not simultaneously integrate multiple general agent frameworks or provider platforms.

---

# 12. AI budgeting law

Record model/token/compute/data/human-review/calendar cost. Every search family receives a preregistered budget. Prompt fishing, model swapping, feature-generation rounds and target/horizon search consume that budget. AI cannot grant itself more budget. Research Capital Allocator may later recommend changes; PM/governance admits them.

---

# 13. No-narrative-over-accounting law

AI explanation occurs only after deterministic accounting. It cannot invent causal attribution from contribution partitions, excuse losses as “market irrationality”, or relabel inferred narrative as mechanical fact. `MECHANICAL / STATISTICAL / INFERRED / UNRESOLVED` status remains explicit.

---

# 14. Lifecycle attribution

Preserve separate objects:

```text
DISCOVERY_ENTRY
CONTINUATION_HOLD
EXIT_FALSIFIER
```

Different AI/model components may own each only with separate evidence. Unrealized P&L is never proof that a hold remains correct. Hold logic consumes PIT continuation evidence; exit logic consumes PIT falsifier evidence.

---

# 15. Promotion firewall

AI cannot promote itself or convert a development/OOS/prospective result directly into capital authority. Promotion reads Trial/search history, prospective evidence, costs, capacity, redundancy, replication and capturability. Deterministic gates own final state. AI may summarize/recommend only. Safety Parent/demotion remain available without AI approval.

---

# 16. Failure / adversarial tests

Before authoritative use, cover at least:

```text
outcome leakage
hidden-OOS access
wrong-role data visibility
source prompt injection / malicious README / filing instruction
AIInvocationReceipt input/output/prompt/tool-manifest tamper
mutation outside allowed gene set
frozen-parameter edit
unauthorized risk increase
missing Trial Ledger entry
search-budget exhaustion
post-result prompt modification
FAILED_INFRA vs FAILED_OOS separation
external backtest metric into PromotionScore
external BUY/SELL into portfolio action
LLM outage does not block deterministic portfolio operation
LLM cannot issue Clock-Start / maturity / alpha evidence / FREEZE_NEW_RISK clear / broker intent
```

---

# 17. Research-quality metrics

AI process metrics are separate from portfolio-alpha evidence:

```text
TIME_TO_HYPOTHESIS
HYPOTHESIS_TO_FROZEN_EXPERIMENT_TIME
REVIEWPACKET_TO_NEXT_REGISTERED_TRIAL_TIME
HUMAN_RESEARCH_MINUTES_SAVED
CONTRADICTION_DETECTION_RATE
EVIDENCE_GAP_DISCOVERY
AI_HYPOTHESIS_DUPLICATION_RATE
AI_UNSUPPORTED_CLAIM_RATE
AI_RESEARCH_COST_PER_REGISTERED_TRIAL
AI_RESEARCH_COST_PER_DECISION_CHANGED
DECISION_CHANGING_RESEARCH_YIELD
AI_AUTHORITY_VIOLATION_COUNT
```

`AI_AUTHORITY_VIOLATION_COUNT` target = `0`.

“AI saved time”, “AI found a backtest”, and “AI found an eventual historical winner” are not financial-alpha evidence.

---

# 18. Parallelism contract

This lane may run beside `alpha_pit_data_api_v1`, `CYCLE_RESONANCE_v1`, and PAPER Capitalization only when:

- it has independent ownership/capacity;
- it consumes frozen schemas or immutable fixtures;
- it does not write another lane's authority objects;
- integration occurs at deterministic join gates;
- any consumer-visible model/prompt/procedure is versioned and hash-bound;
- generic platform work is forbidden until a second real consumer proves reuse.

**Parallelize engineering; serialize authority promotion.**

---

# 19. Current authority statement

```text
ACTIVE_PRODUCT_STATE = CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED
CLOCK_1_STARTED = TRUE
AI_RESEARCH_PIPELINE_V0 = SPECIFIED / TOOLING_LANE_RELEASED / NOT IMPLEMENTED
REAL_OUTCOME_INFORMED_AI = BLOCKED_UNTIL_MATURE_RECONCILED_REVIEWPACKET
financial_alpha_evidence = 0
LIVE = CLOSED
```

Clock #1 releases only bounded AI receipt/schema/fixture/source-claim engineering under independent ownership. Real outcome-informed mutation remains mechanically blocked until a matured, reconciled, validated ReviewPacket exists. No AI output receives evidence, promotion, risk, broker, or capital authority from this release.
