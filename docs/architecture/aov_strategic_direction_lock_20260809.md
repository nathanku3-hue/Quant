# GodView Strategic Direction Lock — Multi-Clock Alpha / PAPER-0 / Historical Authority

**Date:** 2026-08-09
**Meeting verdict:** `PASS — STRATEGIC_DIRECTION_LOCKED`
**Strategic state:** `APPROVED_AND_LOCKED`
**Mandatory recuts:** `AUTHORIZED_FOR_EXECUTION`
**Broad architecture reopen:** `NO`
**Current runtime effect:** **NONE BY THIS DOCUMENT ALONE** — every recut still requires implementation, tests, deterministic receipts, and the applicable evidence/risk gate
**Clock #1:** `UNCHANGED / RUNNING / OUTCOME_SEALED`
**financial_alpha_evidence:** `0`
**Strategy live capital:** `CLOSED`

---

## 0. Executive lock

The strategic direction is approved and broad architecture design is closed. Mandatory recuts are execution gates, not reasons to reopen strategy.

The programme optimizes:

```text
EVIDENCE_VELOCITY × ECONOMIC_RELEVANCE
```

The operating law is now:

```text
PARALLELIZE
- independent prediction clocks
- evidence production / qualification
- historical A1/A2 acquisition
- provider acquisition
- replication readiness
- PAPER operational learning

SERIALIZE
- current portfolio/capital-policy commits
- production risk authority
- financial capital authority
```

**Evidence qualification itself is not serialized.** Multiple Alpha Families may independently become evidence-qualified. What remains singular is the current portfolio/capital-policy authority that composes or promotes qualified components.

Initial active Alpha-family WIP is `2`; ceiling `3` until an explicit ownership/search-budget/risk-capacity WIP review. The ceiling is an operating limit, not a permanent constitution.

---

## 1. Ex-ante Prediction Constitution

GodView remains an ex-ante prediction system, not a state-classification or post-hoc explanation system.

Every Alpha Family that claims predictive authority must eventually emit an immutable artifact containing at minimum:

```text
prediction_id
family_id
implementation_id
prediction_made_at
knowledge_cutoff / as_of
target_variable
forecast_horizon
execution_boundary
forecast / probability / distribution
input_packet_hash
model_or_rule_hash
comparator
abstention semantics
prediction_hash
```

Permanent separation:

```text
STATE != FORECAST != TARGET WEIGHT != EXECUTION
```

Cycle/regime labels, GMM/HMM states, anomaly scores, Hurst estimates, breadth/volatility states and resonance states are context/features until they contribute to a future-directed falsifiable prediction frozen before outcome access.

---

## 2. Multi-scale cycle philosophy

GodView recognizes simultaneous overlapping cycles:

```text
STRUCTURAL / SECULAR      years
BUSINESS / EARNINGS       quarters → years
SECTOR / MARKET           weeks → months
TACTICAL / EVENT          days → weeks
```

The portfolio crosses cycles by composing independently validated forecasts, not by routing all capital through one universal regime classifier.

Every composition seam requires a marginal test:

```text
I vs I + X
```

`X` earns inclusion only when it adds marginal information, shortens evidence latency, improves capturability, or improves net risk-adjusted compounding after cost/capacity/winner-clipping effects.

---

## 3. CRV1 role and evidence-duration recut

`CYCLE_RESONANCE_v1` remains the slow business-cycle family with its frozen primary endpoint:

```text
primary_horizon = 252 trading days
primary_outcome = top 5% date-local cross-sectional primary-security total return
```

Do **not** shorten CRV1 in place merely to accelerate learning. A material horizon change creates a new family/version.

The programme must not be hostage to CRV1 maturity. A separate genuinely multi-week Alpha Family is authorized for immediate preregistration, with an economically justified primary horizon in the approximate `5–20d` or `20–60d` range.

Current leading candidates are:

```text
SECTOR_ROTATION_ALPHA_v1
VOL_SQUEEZE_BREAKOUT_v1
```

This strategic meeting does not choose between them. The local preregistration decision must use PIT-data availability, event frequency, capacity, orthogonality, falsifiability, expected evidence latency and economic relevance.

---

## 4. Alpha-family concurrency

Default active confirmatory/prediction clocks:

```text
Clock A = CYCLE_RESONANCE_v1
Clock B = one fast multi-week family
```

A third clock may be admitted up to the initial WIP ceiling only when ownership, mutable writer surfaces, search budget and risk capacity are explicit.

Each concurrent family requires:

```text
independent family_id
independent owner / writer custody
independent implementation manifest
independent search budget / Trial Ledger scope
independent Prediction Ledger identity
independent artifact namespace
explicit risk-set / label contract
immutable prediction custody
no shared mutable outcome authority
no cross-family hidden-label access
```

Parallel evidence qualification is allowed. Capital-policy commits remain atomic and singular.

---

## 5. Event-family-first / model escalation / demand-pulled data

The scientific unit is an economic Alpha/Event Family; models are replaceable implementations.

Do not organize the programme around `Hawkes`, `GMM`, `TFT`, `DeepLOB`, `XGBoost` or a foundation model. A family freezes mechanism, PIT inputs, detector/state representation, future target, horizon, falsifier, costs/capacity, search budget and A1/A2/A3 contract.

Model escalation:

```text
M0 deterministic
→ M1 linear/logistic/statistical
→ M2 tree boosting
→ M3 sequence/deep
→ M4 foundation/ensemble
```

Higher complexity must prove incremental untouched/OOS economic utility.

Data acquisition is demand-pulled:

```text
economic hypothesis
→ test with legitimate current data
→ measure residual information gap
→ prove missing data is binding
→ acquire richer source
```

Daily CIQ price/volume can support sector-rotation, volatility-squeeze/breakout and low-frequency exhaustion-proxy research. True forced-liquidation/LOB absorption and DeepLOB/L2/L3 remain deferred until microstructure data is economically justified.

---

## 6. Lane 1 — Future Truth

Lane 1 never stops:

```text
Clock #1 frozen-109 weekly tape
+
Alpha PIT
+
CRV1 slow clock
+
fast-family clock
→ matured outcomes
→ deterministic ReviewPackets
→ bounded mutation
→ hidden/OOS where legitimate
→ prospective Challengers
→ independent replication
→ bounded capital only after owner/risk gates
```

Clock #1 Parent/Child, identity, source authority, execution/evaluation boundary and outcome seal remain unchanged.

---

## 7. Lane 2 — Historical Compression and hard A1/A2 block

Target sequence:

```text
legitimate historical PIT CIQ
→ exact frozen-AOV replay
→ A1
→ freeze A2 split/query/metrics/executable/source contract
→ one query-metered untouched historical PIT OOS
→ A2
→ Parent/Child economics + loss/missed-winner/winner-clipping diagnosis
```

A1/A2 do not increment `financial_alpha_evidence` under the current prospective-evidence law.

### Historical-vintage truth gate

The current working tree contains a material contradiction:

```text
research/aov0/historical_pit.py
→ requires FilingVer=Original

historical CIQ fundamental capture scripts
→ request / emit FilingVer=Current/Restated

scripts/aov0_historical_pit_replay.py
→ currently reports historical_spg_asof_original = true
```

Therefore:

```text
HISTORICAL_A1_A2 = BLOCKED UNTIL VINTAGE + PARITY CLOSE
```

Quant/Data must prove provider semantics and freeze exactly one economically legitimate historical-vintage authority. The winning authority destructively replaces the competing current path; misleading labels/fallbacks/compatibility bridges are removed. Current/Restated bytes may never be relabeled as Original.

### Exact-replay parity gate

Current and historical AOV implementations must prove same-input parity for shared economics. The next authority version should extract the smallest pure feature/policy kernel justified by this real Rule-of-Two reuse, without rewriting the already-running Clock #1 organism.

A1 cannot claim `exact frozen-AOV historical replay` until a frozen parity test reconciles identity, ADV20, realized volatility, SMA/trend state, Q/U, technical state, sizing eligibility and Rule100 weights, with only explicitly declared temporal activation differences allowed.

---

## 8. PAPER-0 — immediate operational recut

PAPER engineering is authorized now; strategy live capital is not.

The first executable vertical is deliberately thin:

```text
frozen promoted target
→ live_rebalance_id
→ ExecutionIntentV1
→ CIQSEC ↔ broker map
→ MOC_CLOSE_AUCTION_V1 = market + cls
→ broker submit / acknowledgement / open orders / fills
→ canonical PAPER state
→ positions/cash reconciliation
→ restart reconciliation
→ FREEZE_NEW_RISK on ambiguity
```

Unsupported broker states may fail closed in PAPER-0. Trade bust/correct, rare replacement states, extended implementation-shortfall attribution and other production-hardening tail may land in PAPER-1 before bounded capital.

### First-order calendar condition

PAPER-0 must either resolve the actual market-session close (including early closes) or explicitly restrict the first order to a verified regular full-session day and fail closed otherwise. A perpetual 16:00 assumption is not authorized.

---

## 9. ExecutionIntentV1 and live PAPER state

`ExecutionIntentV1` is the future destructive current broker-intent authority. At minimum it binds:

```text
account_id
live_rebalance_id
promoted_policy_id / promoted_seal_id
execution_map_hash
instrument_id
side
quantity
execution_policy_id
time_in_force
rebalance_epoch
```

The intent hash/signature and deterministic `client_order_id` derive from this exact object. When current, it removes legacy day/symbol/side/qty CID authority, duplicated orchestrator CID construction and silent TIF defaulting.

Actual broker lifecycle is not the same authority model as deterministic simulated fills. PAPER therefore requires a versioned broker→canonical projection whose committed live state includes open orders and partial-fill residual risk.

Restart begins with `FREEZE_NEW_RISK=true`; broker account/positions/cash/open orders/recent execution state must reconcile to local rebalance/intent/event/book state before the freeze can clear. `rebalance_epoch` fences stale/zombie workers.

---

## 10. PAPER performance law

Precompute/reconcile everything possible before the auction window. The latency-critical path should be only:

```text
immutable ExecutionIntentV1
→ small synchronous final risk gate
→ broker submit
→ acknowledgement
```

Order sizing should use one timestamped/hash-bound batch or bounded-batch pricing snapshot rather than serial symbol-by-symbol network discovery inside the final MOC window.

No GPU/distributed programme is authorized; compute is not the current bottleneck.

---

## 11. Replication readiness starts now

Independent-replication readiness no longer waits for a Challenger seal. Begin quarantined preparation now:

```text
entitlement feasibility
source/provider feasibility
permanent identity feasibility
PIT/vintage semantics
license/retention feasibility
expected acquisition latency
immutable quarantine design
```

Replication outcomes remain inaccessible to discovery/confirmatory research. Broad speculative dataset acquisition is not authorized; actual family-specific acquisition remains demand-pulled.

---

## 12. Historical CIQ acquisition throughput

Provider acquisition, not Python simulation, is the present Lane-2 performance bottleneck.

After the historical-vintage semantic is frozen, use restartable immutable chunks with bounded concurrency:

```text
start = 2 independent Excel workers
→ measure COM/provider stability + part integrity + wall-clock throughput
→ increase to 3–4 only if stable
```

Workers own disjoint parts; deterministic merge/conflict checks remain authority. Do not respond to Office latency by building a generic provider platform unless measured bounded parallelism still leaves provider access as the binding constraint.

---

## 13. Alpha PIT second-consumer recut

Current `alpha_pit_data_api_v1` is correctly CRV1-first. When Family #2 actually opens, extract only a tiny immutable `FamilyDataContract` containing:

```text
family_id
risk_set_spec_id
primary_label_spec_id
allowed observation surface
allowed expectation surface
allowed claim surface
```

Inject it into session/artifact/outcome binding. Add cross-family rejection and concurrent-session isolation tests. Do not create a registry, plugin system, feature store or generic provider platform.

---

## 14. AI / Market Transition / leverage boundaries

AI may accelerate research attention, source-bound extraction, control finding, red-team review, ReviewPacket explanation and bounded mutation drafting. Deterministic systems continue to own PIT truth, identity, accounting, risk, execution, evidence qualification and capital-policy commits. Real outcome-informed mutation still requires a matured, reconciled, validated ReviewPacket.

`MARKET_TRANSITION_ALPHA_v1` remains a separate family/discovery object unless explicitly admitted into one of the active family WIP slots. Its state classification is not Alpha without ex-ante future targets.

`RESONANCE_LEVERAGE_POLICY_v1` remains downstream capital policy. Multiple evidence-qualified families or multi-scale resonance do not themselves authorize leverage, shorting, options or multiple simultaneous capital-policy authorities.

---

## 15. Management KPIs

Leadership should track:

```text
Evidence velocity
= days preregistration → first seal → maturity
  plus A1/A2 provider wall-clock separately

Economic throughput
= independent legitimate forecasts matured per calendar quarter

PAPER operational quality
= reconciled rebalances / total rebalances
  with zero unresolved open-risk ambiguity
  plus implementation shortfall

Search efficiency
= economic information gained per Trial/Search budget consumed
```

These are management metrics, not new platforms.

---

## 16. Locked authority statement

```text
STRATEGIC_DIRECTION = APPROVED_AND_LOCKED
MANDATORY_RECUTS = AUTHORIZED_FOR_EXECUTION
BROAD_ARCHITECTURE_REOPEN = NO
PARALLEL_EVIDENCE_QUALIFICATION = YES
SINGLE_CURRENT_CAPITAL_POLICY_AUTHORITY = YES
CLOCK_1 = UNCHANGED
CRV1_252D = UNCHANGED
FAST_ALPHA_CLOCK = AUTHORIZE_PREREGISTRATION_NOW
INITIAL_ACTIVE_ALPHA_WIP = 2
INITIAL_ALPHA_WIP_CEILING = 3 UNTIL EXPLICIT WIP REVIEW
PAPER_0 = AUTHORIZE_IMPLEMENTATION; FIRST ORDER REQUIRES MINIMUM GATES
HISTORICAL_A1_A2 = BLOCKED UNTIL VINTAGE + PARITY CLOSE
REPLICATION_READINESS = START NOW
FINANCIAL_ALPHA_EVIDENCE = 0
STRATEGY_LIVE_CAPITAL = CLOSED
```

---

## 17. Explicitly rejected responses

Do not answer these recuts by building:

```text
generic data/provider platform
generic Alpha Factory
generic Cycle/Event Engine
generic Model Factory
generic AI-agent platform
second OMS
broad execution platform
optimizer-first programme
large research UI programme
GPU/distributed platform
L2/L3 because a model can consume it
```

Every new component must directly shorten time to legitimate A1/A2/A3, PAPER capturability, independent replication or bounded capital—or be deferred.

---

## 18. Next strategic meeting trigger

No more broad architecture meetings. The next CEO/CRO/PM-level decision is evidence-triggered by one or more of:

```text
real A1 incumbent economics
real A2 untouched result
first reconciled PAPER-0 rebalance
fast-family implementation freeze / prospective seal
first matured Clock #1 ReviewPacket
material independent-replication readiness blocker
```

The next decision is `CONTINUE / PIVOT / HOLD / STOP / PROMOTE`, based on economics and evidence rather than architecture speculation.
