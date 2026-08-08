# AOV Velocity Council — CEO / Quant / PM / Risk / Architecture / Engineering

**Date:** 2026-08-08
**Mode:** `APPROVED_DECISION_RECORD`
**Scope:** post-Clock roadmap aggressiveness, maximum safe parallelism, AI × Pipeline proposal, Market Transition / Resonance Capital proposal, and owner-ratified A1→A2 historical-compression execution recut
**Current execution state:** `CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED` — the council recut does not alter the immutable Clock #1 chain
**Financial-alpha evidence:** `0` — **UNCHANGED**
**Limited Live:** `CLOSED` — **UNCHANGED**

## 0. Council verdict

The current roadmap is directionally correct but **too conservative in one post-Clock dimension**: its global “one active capital-value engineering build lane” can serialize work that belongs to independent authority domains.

The council therefore approves a narrow velocity recut:

> **Parallelize work; serialize authority.**

After Clock #1, independent teams may build against frozen contracts in parallel, but each authority domain has exactly one incumbent writer and every transition into evidence/capital authority crosses a deterministic join gate.

The pre-Clock path remains singular:

```text
complete real CIQ market custody/admission
→ decision_cut_v3
→ Seal Candidate
→ fresh-process full-chain verification
→ immutable Clock-Start Receipt
```

Nothing in this round may enter that chain.

## 1. Council votes

| Seat | AI × Pipeline | Market Transition / Resonance Capital | Velocity recut | Main condition |
| --- | --- | --- | --- | --- |
| CEO | APPROVE_WITH_MODIFICATIONS | APPROVE_WITH_MODIFICATIONS | APPROVE | shorten calendar time without creating platform programmes |
| Quant | APPROVE_WITH_MODIFICATIONS | APPROVE_WITH_MODIFICATIONS | APPROVE | discovery may parallelize; confirmatory authority remains clean |
| PM | APPROVE_WITH_MODIFICATIONS | APPROVE_WITH_MODIFICATIONS | APPROVE | eliminate avoidable dependency idle time and expose lane blockers |
| Risk | APPROVE_WITH_MODIFICATIONS | APPROVE_WITH_MODIFICATIONS | APPROVE | AI, leverage, shorts, options and promotion remain authority-gated |
| Architecture | APPROVE_WITH_MODIFICATIONS | APPROVE_WITH_MODIFICATIONS | APPROVE | one writer per authority domain; deterministic joins; Rule of Two |
| Engineering | APPROVE_WITH_MODIFICATIONS | APPROVE_WITH_MODIFICATIONS | APPROVE | contract-first fixtures permit parallel implementation without shared mutable state |

**Council result:** `6/6 APPROVE_WITH_MODIFICATIONS`.

### Owner ratification / final execution rating

The owner subsequently approved the philosophy and roadmap with one additional execution recut: elevate historical PIT `A1 → freeze → A2` from embedded Atlas work into a **first-class second critical lane** beside future-truth/self-improvement work.

| Dimension | Owner rating | Agreement |
| --- | ---: | --- |
| Roadmap revised aggressively enough | **9.8 / 10** | Very high |
| Ship fast / destructive / no backward compatibility | **9.7 / 10** | Very high |
| Philosophy aligned / maximize real alpha | **9.8 / 10** | Very high |
| **Overall** | **9.77 / 10** | **APPROVE WITH ONE EXECUTION RECUT** |

The project operating objective is now **evidence velocity × economic relevance**, not architecture completeness.

The approved priority stack is:

```text
1. preserve prospective evidence generation
2. measure frozen AOV historically with legitimate PIT data
3. obtain untouched A2
4. identify exactly where incumbent loses money / misses winners
5. build CYCLE_RESONANCE_v1 as one economically motivated challenger
6. use matured prospective ReviewPackets for bounded mutation
7. add another family only when evidence identifies a missing dimension
```

## 2. Audit against owner questions

### 2.1 Is the roadmap correctly aggressive?

**Before recut:** strong on prospective-clock urgency, weaker on post-Clock construction concurrency.
**Finding:** the one-global-build-lane law correctly prevented architecture sprawl, but it also risked forcing `Alpha PIT API → CYCLE_RESONANCE → AI` into a waterfall even though their interfaces are already specifiable independently.

**Disposition:** `MODIFY`.

Aggression remains constrained by authority, not by an artificial single-team queue.

### 2.2 Does the roadmap ship fast with maximum defensible parallelism?

**Before recut:** multiple evidence/operational clocks were parallel, but core strategy/data/AI construction could still serialize.
**Disposition:** replace the global construction cap with **authority-domain WIP slots**.

Maximum approved post-Clock construction topology:

```text
ALWAYS ON
A. weekly AOV prospective tape
B. deterministic review / custody / replay closure

DOMAIN WIP SLOT 1 — ALPHA PIT PIPELINE
C. alpha_pit_data_api_v1
   one narrow incumbent; only first-family-required fields/sources

DOMAIN WIP SLOT 2 — ALPHA FAMILY
D. CYCLE_RESONANCE_v1
   one primary confirmatory Alpha-family implementation at a time

DOMAIN WIP SLOT 3 — AI RESEARCH TOOLING
E. bounded AI receipt / role-firewall / fixture vertical
   only with independent ownership; no generic agent platform

DOMAIN WIP SLOT 4 — PAPER CAPITALIZATION
F. thin Alpaca PAPER Capitalization Vertical
   existing execution substrate; no second OMS

DISCOVERY INCUBATORS — RESEARCH, NOT CURRENT AUTHORITY
G. registered outcome-visible / hypothesis-generation work may run in parallel
   subject to explicit search budgets and zero confirmatory/capital authority

ASYNC EXTERNAL LEAD TIME
H. borrow/locate feasibility
I. independent-replication preparation after first Challenger seal
```

If independent ownership is not actually available, priority collapses rather than pretending concurrency:

```text
Clock continuity
→ Alpha PIT Pipeline + CYCLE_RESONANCE critical pair
→ AI research tooling
→ other discovery incubators
```

PAPER remains independently owned where that team exists.

### 2.3 Does the complex system produce 1+1>2?

**Finding:** yes only if the lanes converge through shared immutable contracts and marginal-value tests. Four disconnected mini-platforms would be 1+1<2.

Freeze the system synergy chain:

```text
provider/source bytes
→ immutable PIT canonical packet
→ Alpha-family state / prediction
→ Prediction Ledger
→ future outcome
→ deterministic ReviewPacket
→ bounded AI interpretation / hypothesis / mutation draft
→ deterministic validator / compiler
→ Trial Ledger
→ OOS / prospective Challenger
→ deterministic promotion gate
→ PAPER execution identity / broker lifecycle
→ actual broker P&L + implementation-shortfall bridge
→ deterministic ReviewPacket
```

**System law:** parallel lanes exchange immutable, versioned objects. They do not coordinate through shared mutable scientific or capital state.

### 2.4 Owner execution recut — dual critical evidence lanes

The final programme topology is explicitly two-lane:

```text
LANE 1 — FUTURE TRUTH                    LANE 2 — COMPRESSED LEARNING
─────────────────────                    ─────────────────────────────
weekly prospective tape                  historical PIT CIQ reconstruction
        │                                         │
Alpha PIT + CRV1                         exact frozen-AOV replay
        │                                         │
matured ReviewPackets                           A1
        │                                         │
bounded mutation                               FREEZE A2 CONTRACT
        │                                         │
hidden/OOS validation                    untouched historical PIT OOS
        │                                         │
prospective Challenger                          A2
        │                                         │
independent replication                 incumbent loss / missed-winner diagnosis
        │
bounded capital
```

Historical computation/provider work does not wait for future calendar time, and future prospective time does not wait for historical completeness. Lane 2 measures the frozen incumbent; it does not create permission to tune Parent/Child between A1 and A2. A2 remains query-metered and untouched under its frozen contract. If historical universe/PIT authority is insufficient, the result is downgraded to a diagnostic rather than relabeled as A1/A2.

**Ship-fast law:** destructive change applies to obsolete runtime authority, not scientific custody. When new authority wins, delete the old active reader/writer/fallback/alias/dual-write/old-authority feature flag/compatibility adapter in the same slice; preserve immutable historical evidence under its pinned historical environment/schema.

**Governance critical-path law:** unrelated repository-wide legacy-suite failures block repository phase-close claims, not an owned Alpha PIT/A1/A2 research slice whose deterministic scope gates pass and whose unrelated failures are explicitly recorded.

## 3. Architecture options and scores

Risk profile: `performance_first`
Weights: `impact=1.3`, `maintainability=0.9`, `risk=1.2`, `effort=0.9`
Formula: `OptionScore = impact*1.3 + maintainability*0.9 - risk*1.2 - effort*0.9`.

### Finding A — post-Clock WIP law

| Option | Impact | Risk | Effort | Maintainability | OptionScore | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| A. retain one global engineering build lane | 2 | 2 | 1 | 4 | 2.9 | reject |
| B. one WIP slot per authority domain | 5 | 2 | 3 | 5 | **5.9** | **approve** |
| C. unrestricted maximum parallel engineering | 5 | 5 | 5 | 2 | -2.2 | reject |

Reason: B captures calendar concurrency without allowing multiple writers or competing authority systems.

### Finding B — AI activation

| Option | Impact | Risk | Effort | Maintainability | OptionScore | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| A. do not build any AI tooling until a matured ReviewPacket exists | 2 | 1 | 1 | 4 | 4.1 | too late |
| B. post-Clock fixture/source-claim AI engineering; real outcome-informed use remains maturity-gated | 5 | 2 | 3 | 5 | **5.9** | **approve** |
| C. implement AI before Clock #1 | 3 | 5 | 4 | 2 | -3.9 | reject |

Reason: a real ReviewPacket should gate **outcome-informed authority**, not all harmless engineering of receipts, schemas, fixture flows and discovery-only source-claim tooling.

### Finding C — Market Transition sequencing

| Option | Impact | Risk | Effort | Maintainability | OptionScore | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| A. run a second confirmatory Alpha-family build beside CYCLE_RESONANCE_v1 | 4 | 4 | 4 | 2 | -1.4 | reject |
| B. parallel discovery incubator; confirmatory build enters Alpha slot after CRV1 seal or explicit PIVOT | 5 | 2 | 2 | 5 | **6.8** | **approve** |
| C. defer all Market Transition work until CRV1 matures | 2 | 1 | 1 | 4 | 4.1 | unnecessarily serial |

Reason: historical crisis/regime discovery can reduce future calendar latency without consuming confirmatory authority or a second production model lane.

### Finding D — A1→A2 historical evidence compression

| Option | Impact | Risk | Effort | Maintainability | OptionScore | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| A. leave A1/A2 embedded inside broader Minimum-Viable-Atlas work | 3 | 2 | 2 | 4 | 3.3 | too serial |
| B. first-class Lane 2: legitimate historical PIT → exact frozen-AOV A1 → freeze → query-metered untouched A2 | 5 | 2 | 3 | 5 | **5.9** | **approve** |
| C. unrestricted historical backtesting/discovery before a frozen A2 boundary | 5 | 5 | 5 | 2 | -2.2 | reject |

Reason: B consumes historical provider/compute capacity while future calendar time accrues, but preserves the untouched A2 boundary and prevents incumbent tuning or hidden-OOS fishing.

## 4. AI × Pipeline proposal — approved modifications

### Retain

- External repositories are reference material or future bounded consumers, never present financial authority.
- Deterministic systems remain source of truth for identity, timestamps, PIT eligibility, returns, weights, accounting, broker state, costs, risk limits, kill switches and promotion evidence.
- AI outputs are proposals until deterministically admitted.
- Keep explicit roles: `DISCOVERY_AI`, `CONTROL_FINDER_AI`, `CONFIRMATORY_AI`, `RED_TEAM_AI`, `REVIEW_TRANSLATOR_AI`, `MUTATION_AI`, and later `RESEARCH_CAPITAL_ALLOCATOR_AI`.
- Keep `AIInvocationReceipt`, non-authoritative draft-object taxonomy, Trial/Search Ledger charging, hostile-source/prompt-injection boundary, one-provider/one-orchestration incumbent, and external-code adoption gate.
- Keep Qlib/Nautilus/OpenBB/RD-Agent/AlphaEvo/DSA/Minara/NDX concepts quarantined behind GodView contracts; no second canonical runner, OMS, provider platform or autonomous trading agent.

### Modify

The first AI implementation is split into two activation levels:

```text
POST-CLOCK / IMMEDIATE / FIXTURE + DISCOVERY AUTHORITY
AI-DISCOVERY-CLAIM-VERTICAL-0
immutable source-bound claim packet or fixture
→ AIInvocationReceipt
→ one bounded inferred-feature / control / hypothesis draft schema
→ deterministic schema + authority validation
→ Trial/Search Ledger charge where evaluated

POST-CLOCK / MAY BUILD ON FIXTURES, REAL USE MATURITY-GATED
AI-REVIEW-MUTATION-VERTICAL-0
immutable ReviewPacket fixture
→ ReviewExplanationDraft / MutationManifestDraft
→ deterministic validator
→ bounded deterministic compiler fixture

REAL OUTCOME-INFORMED ACTIVATION ONLY AFTER
matured + reconciled + validated ReviewPacket
```

`CYCLE_RESONANCE_v1` may therefore use a frozen AI claim interpreter as an implementation component without waiting for AOV maturity, provided Discovery/Confirmatory/Prospective visibility remains mechanically separated.

The long-run Research Capital Allocator remains downstream. Do not build it before enough real trials exist to allocate.

## 5. Market Transition / Resonance Capital proposal — approved modifications

### Retain as separate objects

```text
MARKET_TRANSITION_ALPHA_v1
= forecast Alpha Family

ENTRY_TIMING_COMPONENT_v1
= separate Alpha Component

RESONANCE_LEVERAGE_POLICY_v1
= Capital Policy, not Core Alpha
```

Also retain:

- `DISCOVERY / ENTRY`, `CONTINUATION / HOLD`, `EXIT / FALSIFIER` attribution separation;
- operational kill vs market-risk de-risk vs emergency flatten;
- crisis-transition Atlas as `DISCOVERY_ONLY`;
- false-crisis controls and effective independent episode accounting;
- left-inflection vs right-confirmation testing;
- explicit hysteresis;
- `DESIRED / ALLOWABLE / FEASIBLE / ACTUAL` capital separation;
- `not long != short`;
- short alpha requires independent negative-return + borrow/cost/capacity evidence;
- puts remain insurance, never Core Alpha;
- options data remains an incremental challenger rather than V1 prerequisite;
- no generic macro/options/regime platform.

### Modify sequencing

Immediately after Clock #1, `MARKET_TRANSITION_ALPHA_v1` may open only as a **registered Discovery Incubator**:

```text
historical Crisis Transition Atlas
+ false-crisis controls
+ PIT source-gap inventory
+ candidate transition mechanisms
+ preregistered labels / falsifiers / search budget
```

It does **not** get a second confirmatory Alpha implementation lane while `CYCLE_RESONANCE_v1` is being built.

Its confirmatory/prospective implementation may enter the `ALPHA_FAMILY_BUILD` slot only after:

```text
CYCLE_RESONANCE_v1 prospective seal
OR
explicit PM/CEO PIVOT decision
```

`RESONANCE_LEVERAGE_POLICY_v1` remains design authority only until upstream stock Alpha + market/timing components have legitimate evidence/calibration and the Capital Constitution identifies state-dependent sizing as the nearest capital-value blocker.

No leverage multiplier, short authority, option trade, hedge budget or live-capital setting is authorized by this round.

## 6. Deterministic join gates

Parallel work is admitted only through these joins:

```text
J0 CLOCK
real Clock-Start Receipt exists

J1 CONTRACT
consumer/producer schema + visibility + authority boundary frozen

J2 LOCAL PROOF
lane passes deterministic fixture/failure tests without relying on another lane's mutable state

J3 REAL PIT INTEGRATION
real canonical input artifacts satisfy the frozen contract

J4 EVIDENCE SEAL
prediction/policy artifact immutable before outcome

J5 MATURE REVIEW
future outcome opens; deterministic accounting/reconciliation/ReviewPacket passes

J6 CAPITAL PROMOTION
prospective edge + independent replication + capturability/PAPER parity + owner/risk gate
```

A lane may build ahead of its next join, but it may not claim the authority on the other side of that join.

## 7. Anti-sprawl rules

Parallelism is denied when any of these is true:

- two lanes would write the same current-authority object or package;
- a lane requires a generic platform before its first concrete consumer;
- an external framework is adopted for conceptual similarity rather than measured time/complexity reduction;
- a discovery lane tries to consume hidden OOS/prospective outcomes;
- AI tries to become data/risk/promotion/broker authority;
- Market Transition tries to smuggle leverage/short/options policy into a forecast family;
- pipeline work expands beyond declared first-consumer fields before a second real consumer;
- PAPER work mutates strategy truth rather than exercising frozen operational targets;
- parallel trial count escapes Trial/Search Ledger budgets.

## 8. Velocity / synergy KPIs

Track at least:

```text
TIME_TO_FIRST_PROSPECTIVE_CHALLENGER
AVOIDABLE_PROSPECTIVE_CLOCK_IDLE
DISCOVERY_TO_FROZEN_HYPOTHESIS_TIME
MATURITY_TO_REVIEWPACKET_TIME
REVIEWPACKET_TO_NEXT_REGISTERED_TRIAL_TIME
PIT_CONTRACT_BLOCKED_DAYS_BY_LANE
AI_RESEARCH_COST_PER_REGISTERED_TRIAL
DECISION_CHANGING_RESEARCH_YIELD
NUMBER_OF_LEGALLY_STARTABLE_LANES_LEFT_IDLE
END_TO_END_HASH_CUSTODY_BREAK_COUNT
AUTHORITY_VIOLATION_COUNT
```

`AUTHORITY_VIOLATION_COUNT` target = `0`.

The `1+1>2` test is not “more components exist.” It is whether the integrated chain reduces time-to-honest-evidence or increases marginal evidence/capturability while preserving authority clarity.

## 9. Final council disposition

```text
PRE-CLOCK [HISTORICAL / NOW CLOSED]
NO CHANGE WAS MADE
→ real CIQ custody/admission → Clock #1 completed independently of this council recut

CURRENT POST-CLOCK
CHANGE
→ LANE 1 FUTURE TRUTH: weekly tape + Alpha PIT + CYCLE_RESONANCE_v1 + later matured ReviewPacket mutation
→ LANE 2 COMPRESSED LEARNING: historical PIT CIQ → exact frozen-AOV replay → A1 → freeze A2 contract → untouched historical PIT OOS → A2
→ one incumbent/writer per authority domain
→ bounded AI fixture/discovery tooling may build under independent ownership without slowing the two critical evidence lanes
→ Market Transition may run as discovery incubator, not a second confirmatory family
→ PAPER Capitalization remains independently parallel
→ evidence/capital authority remains serial at deterministic join gates
→ broad Right-Tail/AI/data/options/leverage/UI/platform work stays suppressed until evidence makes it the nearest economic blocker
```

**Roadmap decision:** `APPROVED_WITH_VELOCITY_PARALLELISM_RECUT`; owner execution recut=`A1_A2_SECOND_CRITICAL_LANE`; overall owner rating=`9.77/10`.
