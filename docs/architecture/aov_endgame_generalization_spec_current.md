# AOV Endgame Generalization Roadmap & Execution Specification

**Repository:** `E:\code\quant`
**Status:** `PRE_SEAL_REAL_CIQ_ADMISSION`
**Roadmap re-audit:** `APPROVED_WITH_WINNER_AND_AUTHORITY_RECUT`
**Strategic reorder:** `APPROVED_AND_RETAINED`
**Sim-to-real recut:** `APPROVED_AND_RETAINED`
**Winner / authority recut:** `APPROVED; TOP_LEVEL_DESIGN_EFFECTIVELY_CLOSED`
**Documentation sync:** `PATCHED`
**Authority type:** Approved roadmap/change authority with the prior capital-path / evidence-clock and sim-to-real recuts retained, plus the 2026-08-08 Winner/Core-Alpha, Minimum-Viable-Atlas, system-wide destructive-authority, and six-constitution owner recut; destructive v3 temporal semantics + pre-Seal adversarial authority tests remain closed locally, leaving real CIQ inputs as the sole pre-clock dependency
**Implementation authority:** **NOT `AUTHORITY_FROZEN`; the Winner/authority recut preregisters post-Clock research and future contract semantics only and does not authorize any additional implementation before Clock #1**
**Date:** 2026-08-08
**Target mandate:** Multi-hour → multi-week systematic evidence engine, initially AOV / long-cash; true Long-Short only after PIT borrow/locate authority exists.

---

# 0. Executive Verdict

## Agreement rating — Winner / authority recut

| Dimension | Rating | Verdict |
|---|---:|---|
| Endgame aggressiveness | **9.9 / 10** | Right-tail / sustainable-compounding destination is correct |
| Prospective-time aggression | **10 / 10** | Future evidence time remains scarcer than historical completeness |
| Right-tail mandate alignment | **9.95 / 10** | Capital-weighted right-tail capture is first-class CIO economics |
| Ship-fast topology | **9.9 / 10** | Minimum Viable Atlas first; seal; expand history underneath running clocks |
| Destructive / no-compat law | **9.9 / 10** | New authority removes old active compatibility in the same slice |
| Research methodology | **9.9 / 10** | Risk-set, rare-event, search, dependence and hazard methods are sufficient |
| Sim-to-real authority | **9.5 / 10** | Capitalization contracts are clear; implementation/drills remain post-Clock work |
| Architecture parsimony | **9.95 / 10** | One incumbent per fork; shared abstractions only after real reuse |
| CEO / PM capital efficiency | **9.9 / 10** | Six constitutions replace owner-menu governance |

**Latest alignment rating:** **~99 / 100 after recuts.**
**Roadmap verdict:** **`APPROVED_WITH_WINNER_AND_AUTHORITY_RECUT`**.
**Top-level design:** **effectively closed; the next meaningful disagreement should come from real PIT data and experiments, not another broad architecture meeting.**
**Current execution gate:** **`PRE_SEAL_REAL_CIQ_ADMISSION` unchanged.**

The prior architecture/scientific-bar, strategic-reorder, and sim-to-real conclusions remain valid on their scopes. The latest recut removes the remaining waterfall/governance risks: the Right-Tail Atlas is minimum-viable-family-first rather than a historical megaproject; `CYCLE_RESONANCE_v1` is preregistered now but not implemented; future authority transitions are destructive rather than compatibility-preserving; owner decisions collapse into six constitutions; and each implementation fork starts from one simplest valid incumbent rather than a menu of parallel designs.

The deeper economic objective is not raw `RIGHT_TAIL_PRECISION` alone. The CIO optimizes **capital-weighted right-tail capture per unit of capital-time**, subject to false-winner cost, catastrophic false-winner risk, opportunity frequency, liquidity, capacity, and the fund survival constitution.

### One-line reasoning

> Freeze truth and the first alpha family now; after Clock #1 seal the first honest Challenger as soon as a Minimum Viable Atlas supports it, while historical depth, replication, and PAPER capitalization continue underneath running evidence clocks.

---

# 1. Authority Precedence — Destructive, No Compatibility Merge

This document exists because `upgrade.md` is a conversation transcript, not a single coherent specification.

## 1.1 Authority model after owner re-audit

Two authorities SHALL remain separate:

### ROADMAP / CHANGE AUTHORITY

`docs/architecture/aov_endgame_generalization_spec_current.md` defines approved direction, sequencing, forbidden scope, and future contract changes.

### CURRENT EXECUTION AUTHORITY

The frozen executable AOV contract + exact code bytes + admitted source receipts + decision cuts + seals define what the currently running organism actually means.

A roadmap sentence SHALL NOT silently change an already-running prospective organism. A roadmap decision becomes runtime authority only after:

```text
implementation
→ tests
→ executable contract/hash update
→ evidence receipt
→ context synchronization
```

`upgrade.md` is historical reasoning only, except that its Final Owner Handover remains the philosophical north star for the multi-hour → multi-week mandate. Earlier/later HFT branches have no current runtime or roadmap authority.

## 1.2 Destructive Authority Replacement Law — system-wide

Every future authority transition is **destructive for current runtime meaning**. When a new schema/contract/semantic hash becomes current authority, the same implementation slice SHALL remove the superseded active path:

```text
NEW AUTHORITY
→ new schema / contract / semantic hash

SAME SLICE MUST REMOVE
→ old active writer
→ old active reader
→ fallback
→ alias
→ dual-write
→ feature flag selecting old authority
→ compatibility adapter
→ stale current-truth wording
→ and update ZERO-COMPAT / negative tests
```

Old artifacts are **not deleted** merely because current authority changes. They remain immutable historical evidence and may be replayed only with their pinned historical code/contract when needed. They SHALL NOT re-enter current runtime authority through a fallback or compatibility reader.

This law applies to Alpha ontology, winner labels, Prediction/Trial custody, execution identity, broker/live book authority, persistent risk state, PAPER/LIVE execution interfaces, and any promoted optimizer/allocation contract.

### One-incumbent law

At every unresolved implementation fork, select the simplest valid incumbent and ship/test that path first. Alternatives are challengers, not parallel architecture:

```text
first Alpha Family       = CYCLE_RESONANCE_v1
first source pipeline    = narrow CIQ + source-bound original public/company disclosures as the family demands
allocation               = existing simple deterministic incumbent
PAPER broker             = existing Alpaca PAPER path
close execution          = MOC_CLOSE_AUCTION_V1 (market + cls) initial incumbent
shared abstraction       = only after a second real consumer
```

`LOC`, explicit close-window, or separate actual-fill execution families may challenge `MOC_CLOSE_AUCTION_V1` only if evidence shows the incumbent is unavailable or economically inadequate. Do not implement all alternatives in parallel.

## 1.3 Explicitly revoked from current critical-path authority

The following are **NOT current implementation authority**:

```text
Execution Toxicity Engine
P(fill)
100ms / 1s markout
queue_ahead
cancel_hazard
LOB queue racing
millisecond CANCEL/FILL race as primary architecture
```

They may remain as historical discussion or a future specialized execution research branch. They SHALL NOT:

- block AOV prospective sealing;
- define P0 platform priority;
- force L2/L3 data acquisition;
- create a second execution spine;
- override the mid/low-frequency Owner Handover.

### Decision reason

> Sub-second microstructure is not the primary economic bottleneck for positions held hours to weeks; Parent-order IS, capacity, borrow/carry, structural break, and forecast decay dominate the current mandate.

---

# 2. Frozen Mid/Low-Frequency Philosophy

## 2.1 Core mandate

The system is designed to answer, at each legitimate decision cut:

```text
What was knowable now?
→ what evidence/state existed?
→ what target/policy was frozen?
→ what happened later?
→ did the challenger improve a capital-relevant decision?
```

The system is **not** primarily designed to win queue priority.

## 2.2 Prospective evidence > architecture completion

**Prospective clock priority is frozen:**

```text
If a minimal honest AOV organism can be sealed,
SEAL FIRST.
Then continue architecture/research under the running clock.
```

No work may delay the first prospective seal unless the missing item makes the seal itself epistemically invalid.

Valid blockers to Seal #1 are narrow:

- identity is ambiguous;
- source/current-cut authority cannot be hashed;
- target vectors are mutable or unreopenable;
- P&L authority is undefined;
- same-cut arms cannot be proven same-cut;
- decision cut cannot be frozen;
- exact reopen fails.

Invalid blockers to Seal #1 include:

- universal historical PIT reconstruction;
- full Forecast Layer;
- global optimizer;
- borrow/locate history;
- options proxy;
- L2/L3 data;
- OMS;
- 100-checkpoint robustness suite.

## 2.3 Fresh reforecast is the endgame decision philosophy

Longer-term target architecture is:

```text
current PIT state
→ fresh features
→ fresh forward forecast
→ portfolio optimizer
→ target weights
```

Not:

```text
entry thesis
→ mechanical decay
→ rule-based hold/exit
```

## 2.4 Score / probability / return / weight are separate objects

Frozen separation:

```text
score ≠ probability ≠ expected return ≠ target weight
```

Rule100 / `factor_positive_count` remains valid as current deterministic policy/control evidence. It SHALL NOT be falsely relabeled as a calibrated forward-return model.

## 2.5 Entry / hold / add / reduce / exit converge to target-weight changes

Endgame semantics:

```text
Δw = w_target - w_current
```

Examples:

```text
0%   → +5% = ENTER LONG
+5%  → +5% = HOLD
+5%  → +7% = ADD
+5%  → +2% = REDUCE
+5%  →  0% = EXIT
+5%  → -2% = EXIT + possible FLIP (only when true short authority exists)
```

No unrealized P&L threshold may be an alpha input.

---

# 3. Current Repo Truth — Reuse, Do Not Rebuild

This roadmap assumes the audited current AOV repo already contains substantial primitives, including or equivalent to:

- frozen current-cut fundamentals (`run_4` current-cut authority);
- current security/market admission/identity work (CIQ Primary Security / Trading Item identity in the audited path);
- Rule100 state and sizing machinery;
- `factor_positive_count` / technical quality controls;
- PIT lifecycle replay machinery;
- current Parent / Child / control concepts;
- five-arm experiment design;
- `decision_cut` / receipts / input hashes / target-vector hashes;
- immutable sealing and exact-reopen concepts;
- total-return reconciliation concepts;
- macro/rate intake including SOFR-related source work.

Concrete existing code examples visible in the current root include:

```text
scripts/pit_lifecycle_replay.py
strategies/rule100_adapter.py
strategies/rule100_softmax.py
scripts/ingest_frb_macro.py
```

## 3.1 Destructive reuse rule

Do **not** build a second research spine.

Required transformation:

```text
existing AOV receipts / hashes / seals / decision cuts
→ generalized immutable contracts
```

Not:

```text
existing AOV spine
+
new parallel P0 platform
+
compatibility adapters forever
```

### Decision reason

> The repo has already paid for research custody primitives; the fastest endgame is to generalize them after the clock starts, not replace them before evidence begins.

---

# 4. Critical Path Overview — Parallel Clocks, Two Capital Paths

The pre-Seal critical path remains singular and unchanged. After Clock #1, execution is managed as **parallel clocks with explicit dependencies**, not one milestone waterfall.

```text
NOW
│
├─ S0A: destructive temporal authority recut
│      v2 → v3 cut/seal + clock-start receipt
├─ S0B: pre-Seal adversarial authority tests
│      mutation / identity / cash / calendar / maturity / fresh-process gates
├─ S0C: real CIQ identity + completed market admission
└─ S1: FIVE-ARM SEAL CANDIDATE
       ↓
   FRESH-PROCESS FULL-CHAIN VERIFY
       ↓
   IMMUTABLE CLOCK-START RECEIPT
       ↓
       ├─────────────────────────────────────────────────────────────┐
       │ CLOCK A — EVIDENCE                                         │
       │ weekly frozen-109 AOV tape never stops                     │
       │ → matured deterministic ReviewPackets                      │
       │                                                             │
       │ CLOCK B — ALPHA DISCOVERY                                  │
       │ ONE ACTIVE BUILD LANE                                      │
       │ Challenger A build → seal ───────────────┐                 │
       │ Challenger B build → seal ────────────┐  │                 │
       │ Challenger C build → seal ────────┐   │  │                 │
       │                                    ↓   ↓  ↓                 │
       │                         MULTIPLE IMMUTABLE RUNNING TAPES    │
       │                                                             │
       │ CLOCK C — EXTERNAL LEAD TIME                               │
       │ first Challenger seal → independent-replication data prep  │
       │ Clock #1 → borrow/locate entitlement feasibility           │
       │                                                             │
       │ CLOCK D — OPERATIONAL PARITY                               │
       │ current frozen AOV targets                                 │
       │ → paper execution intent → fills/positions/cash/P&L        │
       │ → reconciliation/restart/kill-path learning                │
       └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    FIRST CAPITAL-RELEVANT EDGE
                              │
                              ▼
                    simple allocation incumbent
                    OR optimizer challenger that
                    proves incremental net utility
                              │
                              ▼
                    long-side IS / capacity
                              │
                              ▼
                    independent replication
                              │
                              ▼
                    Long/Cash Shadow
                              │
                              ▼
                    minimal OMS / accounting /
                    reconciliation / recovery / kill
                              │
                              ▼
                    BOUNDED LONG/CASH CAPITAL
                              │
                              └─ optional economic extension only:
                                 PIT borrow/locate authority
                                 → borrow-adjusted allocation
                                 → Full L/S Shadow B
                                 → independent L/S replication
                                 → BOUNDED L/S CAPITAL
```

**Strategic law:** true Long-Short is a capability extension, not the license for the company to begin bounded long/cash capital deployment.

---

# 5. Slice S0/S1 — Start the Irrecoverable Prospective Clock

## 5.1 Objective

Bank the **first real same-cut five-arm seal** before any broad upgrade project.

## 5.2 Seal #1 minimal authority inputs

Use only authority already available or required for the current AOV experiment:

```text
current frozen fundamentals cut (`run_4` authority)
+ current security/listing identity authority
+ post-close market bytes required by current experiment
  (total return / price / volume as defined by current AOV authority)
+ current macro/cash benchmark authority
+ Rule100 / Parent / Child policies
→ decision_cut
→ five-arm targets
→ immutable seal
→ exact reopen
```

## 5.3 Five-arm policy

Retain the current AOV same-cut experiment family. The exact arm names/parameters SHALL come from current executable AOV authority. Conceptually:

1. Rule100 control.
2. Parent.
3. Child / bounded sibling challenger.
4. PIT equal-weight / negative or structural comparator.
5. Cash/economic benchmark.

All arms SHALL:

- share the same decision cut;
- share the same admitted universe where applicable;
- have separate accounting sleeves;
- record target vectors and hashes;
- use one explicit P&L authority;
- be reopenable from sealed bytes.

## 5.4 Arm-5 economic cash — CLOSED FROM EXECUTABLE TRUTH

The re-audit closes this decision from current executable authority:

```text
Arm 5
= ECONOMIC_CASH
= official SOFR - 25 bp
= ACT/360 simple accrual
= no proxy substitution
```

Separate concept:

```text
primary risky-asset performance benchmark
= PIT equal-weight eligible universe
```

SOFR itself is the raw rate authority; **SOFR−25bp economic cash is Arm 5**. This is frozen for the current AOV contract and SHALL NOT be redesigned before Seal #1.

## 5.5 Seal contents

Minimum Seal Manifest:

```text
seal_id
seal_schema_version
knowledge_cutoff
decision_cut_created_at
actual_seal_created_at
evaluation_start
universe identity/hash
source receipt IDs + hashes
current-cut fundamentals identity/hash
market-data identity/hash
benchmark identity/hash
policy/model IDs + contract/formula/mutation hashes
executable_manifest_v1 hash
arm IDs
arm target vectors
arm target-vector hashes
notional convention
holding/evaluation horizon
P&L authority ID
seal semantic hash
```

## 5.6 Seal Candidate → Verification → Clock-Start Authority

The four prior custody fixes are **already implemented locally** and are no longer open architecture items:

```text
cut_built_at != actual sealed_at
NYSE-session execution-bar validation
exact executable-byte manifest
fresh-process full cryptographic reopen
```

The remaining defect is **promotion atomicity**. Writing an immutable prospective seal is not itself permission to claim that the prospective clock started.

Freeze the two-phase authority model:

```text
PHASE 1 — IMMUTABLE SEAL CANDIDATE
knowledge_cutoff
<= decision_cut_created_at
<= actual_seal_created_at
< execution/evaluation_start
→ write immutable Seal Candidate
→ prospective_clock_authority = FALSE

PHASE 2 — FRESH-PROCESS VERIFICATION
Seal Candidate
→ full cryptographic closure verifier
→ VERIFIED
→ write separate immutable PROSPECTIVE_CLOCK_START_RECEIPT
→ prospective_clock_authority = TRUE
```

The original seal SHALL NOT be mutated after verification. `prospective_clock_started` is authoritative only when a valid `PROSPECTIVE_CLOCK_START_RECEIPT` exists and binds the verified seal ID/hash + verifier result + verification timestamp.

A failed verifier leaves the Seal Candidate on disk as non-authoritative custody evidence but creates **no clock-start receipt**.

S1 still does **not** require full raw-data recomputation; the stronger raw/current-authority → recompute → identical outputs proof belongs to S2.

## 5.7 Execution / Return-Interval / Maturity Contract — BLOCKING QUANT FIX

The current executable v2 contract declares next-session 09:30 execution, while the canonical engine applies the prior target to the next dated daily total-return row. The daily return observation's economic left/right endpoints are not yet bound to the 09:30 execution instant, so first-period P&L could include price movement that occurred before the modeled execution.

This semantic change SHALL be a **destructive v3 authority recut**, not an in-place reinterpretation of v2:

```text
active decision cut schema
= aov0_ciq_decision_cut_v3

active seal schema
= aov0_prospective_seal_v3

clock authority schema
= aov0_prospective_clock_start_receipt_v1

execution_calendar_id
= NYSE_2026_CORE_CLOSE_1600_ET
```

No active v2 compatibility reader/writer SHALL remain. Existing v2 artifacts remain immutable historical/mechanical evidence only and may not execute under v3 authority.

Fastest honest v3 contract with the existing daily return source:

```text
execution/evaluation_start
= next eligible market CLOSE boundary supported by the authoritative daily-return series

eligible attributed return interval
= only intervals whose left endpoint >= execution/evaluation_start

outcome_open_not_before
= execution/evaluation_start + sleeve_horizon_calendar_days
```

Do **not** keep `09:30 execution + unspecified daily-return interval + sealed_at+30d maturity`.

If a future contract wants true next-open execution, it must add authoritative open/fill pricing and construct the first open→close (or equivalent) P&L interval explicitly; that is a different contract family and is not required for the fastest first seal.

No later weekly seal may overwrite an earlier sleeve's fixed policy or its frozen execution/evaluation boundary.

## 5.8 Acceptance gate S1

`S1_PASS` requires:

- [ ] Real CIQ risky-asset inputs + decision cut admitted.
- [x] All five arms same-cut under current contract.
- [x] Actual seal time is system-stamped and hash-bound.
- [x] Eligible-market-session validation exists.
- [x] Exact executable-byte manifest exists.
- [x] Fresh-process full-chain verification exists.
- [ ] Seal construction returns a **non-authoritative Seal Candidate**, not `prospective_clock_started=true`.
- [ ] Successful fresh-process verification writes a separate immutable `PROSPECTIVE_CLOCK_START_RECEIPT`.
- [ ] No code path may claim clock start without that receipt.
- [ ] Active schemas are destructively recut to `aov0_ciq_decision_cut_v3`, `aov0_prospective_seal_v3`, and `aov0_prospective_clock_start_receipt_v1`; active v2 execution compatibility is absent.
- [ ] `execution_calendar_id = NYSE_2026_CORE_CLOSE_1600_ET` for the v3 daily-return contract.
- [ ] Execution/evaluation start is bound to a return-series-supported boundary; initial contract uses next eligible close unless authoritative open/fill interval data is explicitly added.
- [ ] Every attributed return interval begins at/after execution/evaluation start.
- [ ] `outcome_open_not_before` is derived from execution/evaluation start + the frozen sleeve horizon, not from seal-write time.
- [ ] No hidden fallback values.

**No requirement:** 100 historical checkpoints.

---

# 6. Prospective Cadence & Evidence Accounting

## 6.1 Cadence

Default current AOV cadence:

```text
weekly prospective seal
→ fixed evaluation sleeve
→ overlapping calendar cohorts allowed operationally
```

## 6.1A Weekly fresh-data / staleness contract — freeze laboratory, refresh measurements

Seal #1 is not enough; Seal #2/#3/#4 must remain genuinely fresh without changing the experiment's candidate selection rule.

For AOV-0, freeze:

```text
candidate universe membership
= original frozen 109 entities
```

Do **not** rerun the 30%-growth/high-growth screener weekly. That would change the laboratory and create selection drift across cohorts.

At each weekly decision cut, refresh measurements for the same frozen candidate set:

```text
frozen 109 candidate entities
→ fresh current fundamental observation
→ fresh primary-security identity / trading-status validation
→ fresh completed market cut
→ fresh benchmark/rate observation as required
→ staleness / missingness validation
→ new v3 decision cut
→ new Seal Candidate
→ verify
→ new Clock-Start Receipt
```

This explicitly separates:

```text
candidate-universe membership
from
current feature state / tradeability state
```

A stale or missing REQUIRED weekly measurement fails closed according to its dependency contract; it must not silently reuse the prior week's state unless the field's PIT contract explicitly defines that prior observation as still current/valid.

### One-line reason

> Freeze the laboratory, refresh its measurements; otherwise weekly prospective cohorts become different strategy definitions rather than repeated observations of one organism.

## 6.2 Overlap does not create independence

Weekly overlapping 30-day sleeves SHALL NOT be counted as independent samples merely because they have distinct seal IDs.

Formal inference must account for overlap/dependence using the current AOV inference contract (e.g. HAC/dependence-aware inference where applicable).

## 6.3 Review levels

### Episode review

After one seal matures:

- exact accounting;
- zero-residual reconciliation;
- no causal story required;
- no promotion based on one episode.

### Cohort review

After sufficient matured prospective outcomes:

- paired Parent/Child or Challenger/Control statistics;
- cost attribution;
- realized contribution partitions;
- dependence-aware inference.

### Regime review

After relevant state transitions mature:

- evaluate whether the effect survives/changes by regime;
- do not backfit the regime definition after observing result.

---

# 7. Slice S2 — Generalize the Existing AOV Evidence Spine, Do Not Replace It

This work begins **after Seal #1 is banked** and runs while prospective time accumulates.

## 7.1 Objective — demand-pulled generalization

Generalization is no longer an independent product milestone. Use the **Rule of Two**:

```text
AOV only
→ keep the concrete AOV implementation

AOV + first real Forecast Challenger need the same primitive
→ extract the shared contract

third real consumer
→ harden the interface
```

Two research-integrity contracts are worth establishing early because they directly protect evidence across challenger families:

```text
1. append-only Prediction Ledger
2. append-only Trial Definition / Execution / Outcome Ledger
```

`UniverseSnapshot` and `FrozenFeatureSnapshot` remain valid target contracts, but their shared abstractions SHALL be pulled out by the second real consumer rather than built as a standalone M3 platform deliverable. The existing AOV-specific representation remains authoritative until that demand exists.

### One-line reason

> No abstraction before the second real consumer: extract shared machinery when reuse is real, not when architecture vocabulary predicts it might become useful.

## 7.2 P0 engineering acceptance recut

Old broad gate rejected:

```text
100 historical checkpoints × 3 years
before P0 acceptance
```

New P0 gate:

```text
ONE REAL EXACT DECISION VERTICAL
raw/current authority
→ admitted universe
→ frozen features/state
→ prediction/policy decision
→ targets
→ outcome input contract
→ exact identical semantic hashes on replay
```

This is the minimum proof that the generalized spine works.

## 7.3 Robustness gate moved later

The following belongs to P1/PIT-history hardening, **not Seal #1/P0**:

```text
100 historical decision checkpoints
+ multiple calendar years
+ revisions
+ corporate actions
+ identifier changes
+ stale/missing proxy cases
```

Only execute this historical robustness program if legitimate historical PIT authority exists or is worth acquiring.

Never fabricate historical `observed_at` / `available_at` to satisfy a checklist.

## 7.4 S2 exact-recompute environment custody

The current executable manifest is sufficient for **source custody** at Seal #1 because final artifacts/targets are themselves hash-bound. It is not a claim of complete binary environment reconstruction.

Before S2 claims:

```text
raw authority
→ recompute
→ identical output hashes
```

bind at minimum:

```text
Python version/interpreter identity
package lock / package manifest hash
numpy/pandas/pyarrow versions + build identities where practical
platform/runtime identity
relevant deterministic runtime settings
```

Do **not** expand this into environment-container perfection before Seal #1.

## 7.5 Post-Seal code-quality debt queue — behavior preserving only

Current code quality is safe enough for the first real clock. No refactor may precede the v3 temporal fix + Clock-Start Receipt merely for cleanliness.

After Seal #1, retain this maintenance order:

```text
CQ1 — central authority contract module
      research/aov0/authority.py
      shared validation for cut timing / execution boundary /
      bound inputs / target vectors / reopen closure

CQ2 — split ciq_market.py by invariant boundary
      ciq_identity.py
      ciq_market_ingest.py
      ciq_market_features.py
      ciq_admission.py
      ciq_market.py = orchestration only

CQ3 — schema/status centralization
      typed enums / schema registry
      no scattered vN string branching

CQ4 — structured authority exception taxonomy
      stable error code + severity + artifact/entity context

CQ5 — policy-history comment cleanup
      code comments stay mechanical;
      governance rationale lives in ADR/decision docs
```

These are **post-Seal refactors**, not a second platform phase. Under the WIP cap, CQ1 may enter the review/custody closure lane because it directly reduces authority divergence. CQ2–CQ5 remain queued unless independently owned or they become the nearest reliability blocker.

No compatibility wrappers are created for the refactor; old artifacts remain interpretable through their frozen historical schema only.

---

# 8. Module Spec — Authority / Custody Layer

## 8.1 `SealRepository`

### Input

- decision cut;
- source receipts;
- universe snapshot;
- target vectors;
- policy artifacts.

### Output

- immutable seal manifest;
- semantic hash;
- audit event.

### Invariants

```text
new ID → INSERT
same ID + same immutable bytes → IDEMPOTENT OK
same ID + different immutable bytes → HARD FAIL
```

### Failure semantics

Fail closed.

### One-line reason

> If the original prospective decision can be mutated, it is not prospective evidence.

---

# 9. Module Spec — Universe Layer

## 9.1 Funnel

```text
MASTER
→ DATA_ELIGIBLE
→ TRADEABLE_LONG / TRADEABLE_SHORT
→ FORECAST_ELIGIBLE
→ FROZEN FORECAST
→ OPTIMIZER_CANDIDATE
```

Do not place a pre-forecast `is_optimizable` boolean in a way that creates a circular dependency with prediction creation.

## 9.2 `UniverseSnapshot`

Minimum fields:

```text
universe_snapshot_id
decision_cut
listing/security identity
universe_policy_version
security-master/input hashes
master_eligible
data_eligible
tradeable_long
tradeable_short
forecast_eligible
rejection codes by layer/direction
semantic hash
```

### Directionality

A security may be long-eligible and short-ineligible.

### Current-stage rule

Until real PIT borrow/locate exists:

```text
production/research authority for genuine short = FALSE
```

Do not fake `borrow_cost = 0`.

The current frozen **109-company universe is an AOV-0 laboratory**, not proof of general-market alpha. Interpret evidence as:

```text
Child vs Parent inside same frozen universe
→ paired policy evidence

absolute AOV return
→ includes universe-selection effect

general-market alpha
→ NOT established
```

Independent replication SHALL separate universe-selection edge, policy edge, forecast edge, and portfolio-construction edge. A second universe / untouched cross-sectional block is higher priority than adding dozens of new features to the same 109 names.

The **replication lead-time clock starts after the first Forecast Challenger seal**, not after the entire research stack matures. Data entitlement, permanent identity, PIT availability, and retention feasibility may have external lead time; prepare that independent surface early while keeping it untouched by iterative research. Before first bounded long/cash capital, require the conjunction of prospective edge evidence, one genuinely independent replication, and operational parity.

---

# 10. Module Spec — Frozen FeatureSnapshot

## 10.1 Objective

Capture exactly what upstream state the decision/forecast saw.

Minimum contract:

```text
feature_snapshot_id
created_at
data_cutoff_at
feature_schema_version
feature_spec_hash
feature_builder_artifact_hash
input manifest / receipt IDs
feature_artifact_uri/hash
max_input_available_at
semantic_hash
```

## 10.2 Required implementation rule

`max_input_available_at` and the input-manifest hash must be derived from authoritative repository records, not trusted from caller input.

## 10.3 Atomicity

Feature snapshot header + membership/input rows must commit in one transaction.

### One-line reason

> A feature matrix with incomplete or caller-asserted lineage cannot support a defensible prediction ledger.

---

# 11. Slice S3 — Forecast Layer as Challenger, Not Safety-Parent Replacement

## 11.1 Current truth

Current AOV Rule100 / factor-positive / deterministic policy machinery is useful but is not yet the Endgame forecast contract.

## 11.2 Forecast Layer objective

While AOV prospective tape runs, build a challenger that outputs forward distributions rather than only policy scores.

Required conceptual output:

```text
asset_id / listing_id
decision cut
horizon
raw_score
expected_asset_return
calibrated probability
uncertainty / variance
scenario-conditioned expectations (later)
model artifact hash
feature snapshot hash
```

## 11.3 Initial horizons

Horizons are versioned, not universal constants.

For the current mid/low-frequency mandate, an initial challenger may use a small set such as:

```text
1d
5d
20d
```

or whatever the research hypothesis genuinely supports.

Do not force 4h/1d/3d/5d/20d simply because an architecture document listed them.

## 11.4 Challenger status

The Forecast Layer SHALL initially be:

```text
CHALLENGER_ONLY
```

It may generate forecasts and prospective seals, but it does not replace the Safety Parent until evidence gates pass.

Two challenger paths are explicitly separated:

```text
A. outcome-informed mutation
   matured ReviewPacket → MutationManifest → child

B. independently pre-registered Forecast Challenger
   hypothesis frozen after Seal #1 but before AOV outcomes are observed
   → build / OOS where legitimate / prospective seal
```

Path B does **not** need to wait for AOV maturity because it did not adapt to AOV outcomes. This may save a full outcome cycle without contaminating mutation governance.

### One active build lane is not one running experiment

The WIP cap applies to engineering construction, not to sealed prospective clocks. Once a Challenger's hypothesis is frozen, its implementation is complete, and its prospective seal is issued, that Challenger leaves the active build lane and continues as an immutable running tape. The build lane may then move to the next independently preregistered Challenger without waiting for the prior tape to mature.

```text
Week 1: build A → seal A → A collecting future evidence
Week 2: build B → seal B → A + B collecting future evidence
Week 3: build C → seal C → A + B + C collecting future evidence
```

Trial Ledger / search-family accounting remains mandatory so calendar parallelism does not hide multiple-testing or search-budget inflation.

> Engineering WIP can be serial; future time cannot.

## 11.5 AOV organism evidence is not automatically alpha evidence

The current AOV Child is primarily a bounded insurance/risk-reduction mutation. That is a strong test of the evidence machine, but it is not automatically the highest-EV alpha research direction.

The first Forecast Challenger SHALL preregister a capital-relevant endpoint such as:

```text
incremental expected net return
OR incremental risk-adjusted net utility
OR forecast calibration improvement that changes capital allocation
```

and also freeze mechanism, falsifier, horizon, search budget, and cost assumption before result inspection.

### One-line reason

> The existing deterministic Parent has current prospective authority; a new forecast model must earn authority prospectively rather than inherit it from backtest quality.

---

# 12. Trial / Prediction Custody

## 12.1 Prediction Ledger

Append-only frozen OOS/shadow/prospective predictions.

Minimum fields:

```text
prediction_id
decision_cut
data_cutoff
feature_snapshot_id/hash
universe_snapshot_id
model artifact hash
target definition version
calibration version
horizon spec
forecast outputs
semantic hash
audit timestamps
```

## 12.2 Trial Ledger

Event-sourced:

```text
TrialDefinition
→ TrialExecutionAttempt
→ TrialOutcomeEvent
```

### `TrialDefinition`

```text
trial_id
parent_trial_id
registered_at
hypothesis_family
search_family_id
dataset/input hashes
universe policy
feature spec
target spec
model spec
parameter hash
split spec
lockbox id
code SHA
preregistered_search_budget
preregistered_data_query_budget
preregistered_compute_budget
```

### Attempt vs result separation

`FAILED_INFRA` is not `FAILED_OOS`.

No historical status UPDATE.

## 12.3 Research-search accounting — economic degrees of freedom are part of evidence

Prospective custody of the winning model does **not** repair an unrecorded model-selection search.

Each alpha/search family must eventually expose at least:

```text
search_family_id
hypothesis family
trial count
preregistered search budget
actual search-budget consumption
feature-family count explored
target/horizon count explored
parameter/model-spec variants
OOS failures
prospective failures
compute/data cost
researcher time / operator time where practical
```

All failed/rejected trials remain in the Trial Ledger. Promotion review must interpret a model in the context of the search process that produced it, not as an isolated winner.

A model discovered in a small, preregistered search may carry stronger evidential credibility than a higher-Sharpe model selected from thousands of undocumented variants.

### One-line reason

> Invisible failed trials and invisible search degrees of freedom both turn research history into a survivor pool and corrupt later significance/credibility claims.

---

# 13. Historical Backtest / OOS Policy — Destructive Recut

## 13.1 P0

**Required:** one exact real replay.

**Not required:** 100 checkpoints / 3 years.

## 13.2 P1 robustness default

If legitimate PIT history becomes available, target:

```text
100 historical decision checkpoints
across ≥ 3 calendar years
including:
- revisions
- corporate actions
- identifier changes
- missing optional proxy
- missing required data
- stress regimes
```

This is a robustness target, not a prerequisite to prospective evidence.

## 13.3 Forecast challenger backtest/OOS default

Evidence adequacy must be versioned by horizon and overlap structure.

Default research policy for a new mid/low-frequency forecast family, when sufficient legitimate PIT history exists:

```text
Development/training windows: multiple rolling/expanding windows
Temporal OOS folds: target 4 as an initial engineering default
Untouched lockbox: at least 1
Cross-sectional holdout: preferred when feasible
```

These numbers are recommendations, not natural laws.

If legitimate historical PIT does not exist:

```text
DO NOT invent it.
Seal the Challenger prospectively and let forward evidence mature.
```

## 13.4 Effective sample size > raw fold count

Promotion evidence SHALL consider:

- holding horizon;
- overlapping labels;
- serial correlation;
- cross-sectional dependence;
- regime coverage;
- number of genuinely independent outcomes.

---

# 13A. Winner / Core-Alpha Constitution — Minimum Viable Atlas First

## 13A.1 Fund-level research objective

The Alpha Factory does not optimize the count of signals/models or raw `RIGHT_TAIL_PRECISION` in isolation. The owner mandate is:

```text
maximize sustainable net compounding
through capital-weighted capture of repeatable right-tail opportunities
per unit of capital-time

subject to:
false-winner cost
catastrophic false-winner risk
opportunity frequency
liquidity / capacity
CRO / fund-survival constraints
```

Right-tail Precision@K, Recall@K, Lift@K, PR-AUC, wealth capture, false-winner rate, and conviction monotonicity remain first-class diagnostics. The deeper CIO metric is `CAPITAL_WEIGHTED_RIGHT_TAIL_CAPTURE_EFFICIENCY`.

## 13A.2 Canonical Alpha ontology

The following are separate objects and SHALL NOT collapse into one generic `model_id`:

```text
ALPHA_FAMILY
→ economic information / inefficiency family

ALPHA_COMPONENT
→ distinct horizon / channel / sub-mechanism inside one family

IMPLEMENTATION
→ model / feature / prompt / estimator / transformation

TRIAL
→ one preregistered evaluation

PORTFOLIO_ROLE
→ incremental / complementary / redundant / regime-bound / capacity-limited

CAPITAL_POLICY
→ desired and authorized portfolio use
```

Evidence maturity, portfolio usefulness, and capital authority are separate axes. A real predictor may be `PROSPECTIVELY_SUPPORTED + REDUNDANT + ZERO_CAPITAL` without contradiction.

## 13A.3 `CORE_ALPHA` and `WINNER`

`CORE_ALPHA` is decision-time information that adds conditional predictive value beyond the incumbent information set and survives honest evidence. `WINNER` is an ex-ante classification produced by a frozen Alpha Family/Component; it is never an ex-post label assigned because a stock later rose dramatically.

Keep attribution separate:

```text
universe-selection edge
forecast / Core Alpha
portfolio-construction alpha
actionable execution effect / execution alpha
insurance / survival effect
market / factor exposure
```

A forecast-valid but currently too-costly signal is `NONMONETIZABLE`, not statistical noise. A PIT-observable preregistered regime-specific edge may be `REGIME_BOUND`, not invalid.

## 13A.4 First Alpha Discovery Lane — preregister now, do not implement pre-Clock

```text
FIRST_ALPHA_DISCOVERY_LANE = CYCLE_RESONANCE_v1
STATUS = PREREGISTERED / NOT IMPLEMENTED
PRE_CLOCK_IMPLEMENTATION_AUTHORITY = FALSE
financial_alpha_evidence = 0
```

### Primary economic hypothesis

Multiple partially independent cycle clocks turn in the correct temporal order before consensus/price fully incorporates the future earnings state:

```text
supply / capacity discipline
→ inventory normalization
→ pricing inflection
→ utilization / margin inflection
→ earnings revisions
→ expectation reset
→ exceptional equity payoff
```

This is a **causal-hypothesis graph**, not proven causality.

### Initial information surface

Use the narrowest family-specific sources when the lane becomes active:

```text
structured PIT market/fundamental/estimate state
+ source-bound original company / competitor public disclosures
+ exact availability / receipt metadata
```

No generic document-intelligence, scraping, alternative-data, or provider platform is authorized by this preregistration.

### Primary outcome / horizon

Freeze one primary discovery/evaluation definition before clean PIT results:

```text
primary horizon = 252 trading days from the legitimate execution boundary
primary right-tail outcome = top 5% date-local cross-sectional total return
among the eligible risk set at the decision cut
```

Also retain continuous return, residual-return, earnings-revision, downside, and alternative tail thresholds for **diagnosis/sensitivity only**. They SHALL NOT replace the primary label after results without creating a new family/version/search-budget charge.

### Representation family

Predeclared representations are:

```text
LEVEL
DELTA
INFLECTION
ORDERED_SEQUENCE
```

Search may compare implementations inside these representations, but a new horizon, winner definition, universe rule, or material mechanism change creates a new preregistered version.

### Initial falsifiers

`CYCLE_RESONANCE_v1` fails/holds if valid evidence shows, as applicable:

```text
no incremental I vs I+X value
no right-tail enrichment / conviction monotonicity
mechanism sequence not distinguishable from controls / near-winners
search contamination prevents attribution
independent replication fails
prospective effect fails
edge exists but is nonmonetizable after realistic costs/capacity
```

Failure does not authorize post-result rescue under the same version.

## 13A.5 Minimum Viable Atlas — do not wait for historical perfection

The Atlas is a research method, not a prerequisite megaproject.

Fastest approved sequence:

```text
CYCLE_RESONANCE_v1
→ family-specific winner definition [FROZEN]
→ enough legitimate PIT history for honest discovery / contemporaneous controls
→ discover candidate mechanism / sequence
→ freeze implementation + falsifiers + search budget
→ untouched PIT evaluation where legitimate untouched coverage exists
→ SEAL PROSPECTIVELY AS SOON AS HONESTLY POSSIBLE

while the tape runs:
→ expand historical risk-set coverage
→ deepen near-winner / plausible-story-control / catastrophic-control library
→ build independent replication surface
→ improve reconstruction coverage
```

**Future prospective time is scarcer than historical completeness.** Ten years of perfect historical inventory/capacity/text reconstruction SHALL NOT become a prerequisite for the first honest prospective Challenger.

The canonical historical truth remains the full date-local eligible risk set. Nested case/control reconstruction may reduce expensive qualitative work, but final evaluation returns to full-universe base rates.

## 13A.6 Discovery / confirmation firewall

Three stages remain separate:

```text
DISCOVERY ATLAS
→ outcomes may be visible; no confirmatory authority

FROZEN HISTORICAL VALIDATION
→ mechanism/horizon/variables/falsifiers fixed before untouched inspection

PROSPECTIVE TAPE
→ only future observations; no historical rescue
```

AI role firewalls are explicit:

```text
DISCOVERY AI       may see outcomes
CONTROL-FINDER AI  finds contemporaneous lookalikes / failures
CONFIRMATORY AI    sees only PIT packet at the decision cut
RED-TEAM AI        sees thesis + PIT contradicting evidence
EVALUATOR           may not mutate the hypothesis
```

AI-generated hypotheses/prompts/models count against Trial/Search Ledger budget.

## 13A.7 Incrementality standard

The canonical test is nested system value, not standalone Sharpe:

```text
incumbent information = I
candidate information = X

compare:
I
vs
I + X
```

Hold constant PIT cuts, universe, costs, portfolio objective, risk constraints, and execution assumptions. Sequential residualization is diagnostic/attribution tooling, not a mandatory destructive signal transformation.

## 13A.8 Rare-event / temporal methodology — approved toolkit, not a platform prerequisite

Methods may be selected as the family requires:

```text
Precision@K / Lift@K / PR-AUC / proper probability scoring
learning-to-rank
multi-horizon / competing-risk analysis
discrete-time hazard / survival timing
hierarchical / Bayesian shrinkage
change-point / state-space / hidden-state models
sequence / temporal motif analysis
event studies
conditional predictive ability
HAC / clustered inference / block bootstrap
effective independent episode count
PBO / Deflated Sharpe / Reality Check / SPA / FDR diagnostics
negative controls / placebo dates
```

One memory upcycle producing many semiconductor winners is not many independent macro cycles. Report raw observations **and** effective independent episodes.

## 13A.9 Fundamental / qualitative discipline

Every family/thesis should answer:

```text
WHAT IS CHANGING?
WHY?
WHO / WHAT EXPECTATION IS WRONG?
WHY NOW?
WHAT SHOULD HAPPEN NEXT?
WHAT WOULD FALSIFY IT?
WHY CAN THE PAYOFF BE LARGE?
```

Use base-rate analysis, pre-mortem/inversion, and customer/supplier/competitor/company mosaic corroboration. Qualitative and quantitative evidence are both valid hypothesis inputs; neither bypasses PIT/evidence authority.

Every family also preregisters:

```text
INVARIANCE ASSUMPTIONS
ACTIVATION STATE
CONFIRMATION STATE
FALSIFIER STATE
RE-ENTRY STATE
```

A live capital state may de-risk when a preregistered falsifier fires without rewriting the immutable research tape.

## 13A.10 Alpha redundancy / portfolio contribution

Do not use raw return correlation alone. Maintain an `Alpha Redundancy Matrix` covering:

```text
conditional forecast dependence
conditional position overlap
tail-state payoff overlap
factor exposure overlap
liquidity / capacity overlap
crowding channel overlap
```

Portfolio promotion asks whether `Incumbent Portfolio + Right-Tail Family` adds marginal net utility.

## 13A.11 Conviction / sizing / wrong-winner risk

```text
Alpha / PM → DESIRED capital
CRO        → ALLOWABLE capital
portfolio  → ACTUAL capital
```

Sizing should be fractional-growth-optimal in spirit and aggressively shrunk for model/probability/correlation/tail uncertainty. Track how quickly recommended capital collapses under plausible estimation error.

Winner hunting requires explicit **wrong-winner stress**:

```text
top position -30 / -50 / -80%
two correlated winner theses fail together
industry mechanism breaks
gap-down before exit
liquidity disappears
fraud / accounting event
thesis correct but timing wrong for an extended period
hedge basis fails
```

VaR remains secondary to hard limits, reverse stress, liquidity, concentration, gap, and correlated-thesis-failure controls.

## 13A.12 Research Option Value / PM speed metrics

Prioritize research by expected decision-changing information, not activity volume. For major programs record:

```text
decision the experiment can change
economic value if it changes
probability it changes the decision
independence / contrast of information learned
calendar time
data / analyst / AI / engineering cost
untouched evidence consumed
```

Program KPIs:

```text
TIME_TO_FIRST_SEALED_ALPHA_FAMILY
AVOIDABLE_PROSPECTIVE_CLOCK_IDLE
DISCOVERY_TO_FROZEN_HYPOTHESIS_TIME
```

Do not optimize number of Atlas companies, AI analyses, features, or models.

## 13A.13 Reconstruction coverage and Alpha Half-Life

Every reconstructed observation should expose coverage, e.g.:

```text
PIT_STRUCTURED_COVERAGE
PIT_TEXT_COVERAGE
PIT_INDUSTRY_COVERAGE
EXPECTATION_DATA_COVERAGE
```

Distinguish economically meaningful missingness from historical-reconstruction limitation.

Every promoted family also measures `ALPHA_HALF_LIFE`: how quickly the expected edge decays after the observable signal becomes available. `CAPTURABLE_WINNER` therefore depends on capital × time-to-fill × alpha decay × impact, not ADV alone.

## 13A.14 Second family and platform extraction

`DURABLE_COMPOUNDER_v1` remains a **queued candidate family, not an active lane**. It may become the second real consumer after evidence justifies it. Only then should common primitives such as PIT Claim Ledger, Outcome Census, Risk Set, Logic Graph, Winner Thesis, Control Match, or shared document tooling be extracted into reusable infrastructure.

---

# 14. Prospective / Forward-Test Requirements

## 14.1 AOV current-policy forward clock

- First seal: immediate after S1 gate.
- Subsequent seals: weekly under current AOV cadence.
- Each fixed sleeve: follow current authorized holding horizon (currently expected to be 30 calendar days if that remains executable authority).

## 14.2 First review

One matured seal unlocks deterministic accounting review only.

It does **not** prove alpha.

## 14.3 Preliminary challenger evidence

Default minimum before a forecast challenger is considered more than anecdotal:

```text
≥ 3 non-overlapping matured cohorts
OR an explicitly dependence-adjusted equivalent evidence set
```

This is an initial policy default and SHALL be versioned, not hard-coded into all future strategies.

## 14.4 Stronger promotion evidence

Before a forecast Challenger may displace the Safety Parent, require a combination of:

- multiple prospective cohorts;
- dependence-aware statistics;
- at least one untouched OOS/hidden evidence source where feasible;
- no unresolved reconciliation/cost defect;
- operational replication.

## 14.5 Capitalization Vertical — start operational lead time at Clock #1

After Clock #1, independent Ops/Engineering ownership SHOULD start one thin **Capitalization Vertical** without waiting for alpha maturity, a Forecast Challenger, optimizer, or borrow authority. It may use current frozen AOV targets for operational learning while `financial_alpha_evidence=0`.

Operational-learning mode:

```text
current frozen AOV target
→ non-capital research policy selection
→ paper rebalance intent
→ broker lifecycle observation
→ canonical live-book projection
→ broker positions / cash / open-orders reconciliation
→ restart / recovery / kill-path drills
→ implementation-shortfall bridge
```

Its purpose is **not** to prove alpha. It burns down account, instrument-map, order-lifecycle, reconciliation, restart, calendar, and actual-P&L defects before financial evidence matures.

### 14.5A Research sleeves do not become capital sleeves automatically

Five AOV arms, overlapping cohorts, and multiple Challenger tapes are research/evidence objects. They SHALL NOT be submitted directly to broker capital.

Before any strategy capital intent exists:

```text
multiple immutable research sleeves / tapes
→ deterministic promotion decision
→ exactly one promoted capital policy for the rebalance cycle
→ promoted_policy_id + promoted_seal_id
→ live_rebalance_id
→ account-bound execution intents
```

A `live_rebalance_id` is the root identity for one capital transition. Every child order/fill/cancel/reject event must bind back to it. No implicit averaging, merging, voting, or netting across research sleeves is allowed at the broker boundary.

### 14.5B Sim-to-real instrument/account map

`CIQSEC:<Capital IQ Security ID>` remains research/security authority. Broker execution needs a separate PIT, hash-bound map:

```text
CIQSEC:<id>
→ broker / venue instrument symbol or asset id
→ broker account identity
→ effective / observed / available timestamps
→ tradability / fractional / order-capability state
→ raw broker/security-master receipt hash
→ map semantic hash
```

Missing, stale, ambiguous, or many-to-one execution mapping fails closed. Ticker text alone is not permanent identity authority.

### 14.5C Close-execution contract — bind, do not rebuild

Current v3 research economics use a next-close evaluation boundary. That does **not** automatically prove that a live broker order executed at that boundary.

The existing broker layer already accepts `time_in_force`, and current Alpaca equity semantics support `cls` with market/limit orders for closing-auction MOC/LOC. Freeze one incumbent rather than implement a menu:

```text
INITIAL EXECUTION INCUMBENT
= MOC_CLOSE_AUCTION_V1
= market order + cls TIF
= actual broker fill remains the broker P&L authority
```

`LOC`, explicit close-window, or separate actual-fill execution families are **challengers only**. They may be activated only if `MOC_CLOSE_AUCTION_V1` is unavailable, fails operational parity, or produces materially inferior net execution economics.

The current rebalancer/orchestrator route must explicitly propagate and verify `MOC_CLOSE_AUCTION_V1`; its default ordinary submission path must not be treated as mechanically equivalent to the v3 research close.

### 14.5D Broker lifecycle → canonical live authority

Broker ACK, PARTIAL_FILL, FILL, CANCEL/CANCELED, REJECT, EXPIRED, and open-order state must project into one canonical account-bound event ledger and live book. Broker responses are source events; they do not bypass deterministic projection.

For live authority:

```text
submitted intent
→ broker acknowledgement
→ zero or more partial fills
→ terminal fill / cancel / reject / expire
→ open-order residual state
→ positions / cash / fees
→ canonical live book hash
```

The historical `gv_portfolio_v0` convention that excludes `partial_fill_residuals` from the certification-stable book hash is **not sufficient for live authority**. Live open-order/residual state must be hash-bound or equivalently covered by the canonical live-state commitment.

### 14.5E Restart barrier — broker truth first

Every process restart or uncertain execution recovery starts from broker authority:

```text
broker account identity
+ broker positions
+ broker cash/equity
+ broker open orders
+ locally pending live_rebalance_id / client_order_ids
→ reconcile
```

Any unresolved mismatch or unknown in-flight order sets:

```text
FREEZE_NEW_RISK = TRUE
```

Reducing/closing risk may remain separately authorized by owner/risk policy; new risk may not proceed on ambiguous account state.

### 14.5F Dual ledgers — research economics and actual broker economics

The research CIQ total-return ledger and broker fill/account ledger remain separate authorities:

```text
research counterfactual P&L
≠
actual broker/account P&L
```

Bridge them explicitly through:

```text
implementation shortfall
+ fees
+ fill timing
+ unfilled / partial quantity
+ cash drag
+ financing / borrow where applicable
+ corporate actions / broker adjustments
```

Neither ledger may overwrite or stand in for the other.

### 14.5G Intent identity and signed authority

Production `client_order_id` and signed execution payloads must bind at least:

```text
broker account id
live_rebalance_id
promoted_policy_id / promoted_seal_id
execution-map hash
instrument identity
side / quantity
execution policy / TIF
rebalance_epoch / fencing token
```

The current day+symbol+side+qty identity is adequate only as historical/legacy retry idempotency. When the new capital identity becomes current authority, the Destructive Authority Replacement Law removes the legacy identity path from current execution authority rather than retaining it as fallback.

### 14.5H Paper first; micro-live is an explicit exception

The same thin adapter should serve PAPER and later LIVE authority; mode/account/risk authority changes, not execution architecture.

Broker PAPER is the default first real broker surface. PAPER proves **operational authority**, not real execution economics. It must exercise policy/rebalance identity, account/instrument mapping, signed intent, lifecycle/open-orders, accounting, restart/fencing, hard-risk controls, `FREEZE_NEW_RISK`, and operator procedures. PAPER does **not** prove real market impact, queue position, latency slippage, displayed liquidity, real fill probability, price improvement, or capacity.

PAPER graduation is scenario/fault coverage, not simply elapsed days. Required drill classes include normal/partial/open fills, cancel/replace and rejection paths, expiry, ambiguous submit/duplicate retry, crashes before/after ACK and after partial fill, network/data staleness, broker/local mismatch, unexpected cash/positions, early close, restart with open orders, manual freeze/flatten, and trade bust/correction. A calendar-duration target may remain a secondary coverage aid but cannot substitute for these failure states.

A very small operational micro-live canary is **optional only under explicit owner/risk approval** and must remain:

```text
OPERATIONAL_CANARY_ONLY
financial_alpha_evidence = 0
strategy_promotion = FALSE
```

It may validate real broker/fill/accounting/auction/fee mechanics absent from PAPER; it cannot be cited as alpha or strategy-capital approval.

### Shadow B — True Long-Short

Starts only after PIT borrow/locate authority exists:

```text
true Long-Short
+ PIT locate/borrow economics
+ short fail-closed semantics
+ borrow-adjusted optimizer
```

A promoted shadow may still target roughly `40–60 trading days` as an initial coverage window, but calendar duration is never the authority gate. Adequacy is based on effective independent outcomes, overlap/regime coverage, strategy horizon, lifecycle/fault coverage, reconciliation/restart drills, and capturability/IS evidence.

---

# 15. Slice S4 — Global Optimizer as Portfolio-Construction Challenger, Not a Capital Gate

## 15.1 Incumbent vs challenger

The current/simple deterministic allocation policy is the **incumbent**. The global optimizer is a **portfolio-construction challenger** and must earn authority on incremental capital utility.

Before genuine short authority exists, any optimizer candidate operates only as:

```text
long / cash / risk-controlled allocation
```

Do not call it production Long-Short, and do not make optimizer availability a prerequisite for bounded long/cash capital.

The optimizer must demonstrate incremental net utility after:

```text
costs
+ turnover
+ concentration / risk
+ capacity
+ estimation error
```

If simple deterministic sizing produces economically equivalent outcomes, keep the simpler incumbent and capitalize without waiting for architecture completeness.

## 15.2 Forecast/portfolio separation

Forecast Layer returns asset-level forward values.

Optimizer converts them into NAV-dollar economics.

```text
forecast return units
→ NAV-dollar expected P&L
→ costs / risk / constraints
→ target weights
```

## 15.3 Initial objective

Use deterministic convex formulation first:

```text
Expected return / value
- convex turnover / IS surrogate
- covariance risk
- carry where authoritative
```

Subject to:

```text
gross/net limits
market beta band
sector/industry bands
single-name cap
ADV participation
cash floor
later: borrow / cluster capacity
```

## 15.4 Nonlinear impact

Do not put an unvalidated concave power-law impact directly into a QP and pretend it remains convex.

Architecture:

```text
Convex optimizer
→ proposed targets
→ nonlinear empirical stress
→ if fail: tighten cost/capacity constraints
→ re-solve
```

No arbitrary global `0.7 × Δw` compatibility hack.

## 15.5 Authority rule while evidence matures

Optimizer work may proceed after Seal #1 only when it is the active build lane, the nearest capital blocker, or has genuinely independent ownership. It remains **non-authoritative** until its forecast/risk/cost inputs and promotion gates are valid.

Promotion question:

```text
Does optimizer challenger
produce material incremental net capital utility
versus the simple incumbent
under the same evidence / cost / risk assumptions?
```

If not, reject or hold it. Optimizer sophistication is not an Endgame objective by itself.

---

# 16. Slice S5 — Borrow / Locate: Hard Blocker for True Long-Short

## 16.1 Decision

True production Long-Short **does not exist** until PIT short authority exists.

Before that:

```text
long side = valid
long/cash optimizer = valid
research-only synthetic short = may be studied, clearly labeled
production short = INVALID
```

## 16.2 Minimum borrow/locate data contract

Required or equivalent:

```text
listing/security identity
observed_at
available_at
borrow rate
rebate
locate available flag
locate quantity
HTB state
utilization (if available)
recall event/risk source
buy-in event/risk source
provider/account/feed identity
raw receipt/hash
```

## 16.3 Fail semantics

Missing/stale locate for a short candidate:

```text
TRADEABLE_SHORT = FALSE
```

Never:

```text
borrow cost = 0
```

## 16.4 Historical depth

Ideal historical research target:

```text
3–5+ years
```

but do not delay initial current-forward borrow capture if deep history is not immediately feasible.

A 2–3 year legitimate history can support an initial borrow-adjusted research program; forward collection should start as soon as entitlement is available.

## 16.5 Entitlement decision

This is the first major Endgame area where external vendor/broker entitlement may be the actual hard cost/feasibility constraint.

**Feasibility/vendor/broker investigation starts immediately after Seal #1** because external entitlement lead time may dominate the schedule. It must not block Seal #1, but it also must not wait until optimizer or challenger evidence matures.

The feasibility pass must identify:

- current broker API availability;
- current data-vendor entitlement;
- historical locate availability;
- legal/license retention rules;
- cost.

---

# 17. Slice S6 — Parent-Order IS / Capacity

## 17.1 Primary execution object

For this mandate, execution economics center on the Parent Order.

Required lifecycle:

```text
decision_at
→ arrival_at
→ parent order
→ child executions
→ completion / unfilled
→ realized IS
```

## 17.2 Signed IS

Use one consistent side convention so positive cost always means worse execution.

Attribution should decompose, where data permits:

```text
decision delay
arrival slippage
spread
execution impact
market move
fees
opportunity cost
unfilled quantity
```

## 17.3 Alpha decay vs execution horizon

A real forecast may still be untradeable if execution completion consumes most of the forecast horizon.

Use forward-return term structure + expected completion time, not a universal one-number half-life rule.

## 17.4 Capacity

Name-level capacity:

- ADV participation;
- volatility/liquidity;
- trade size;
- expected execution horizon.

Portfolio-level capacity later adds:

- sector/cluster flow;
- common-factor crowding;
- borrow capacity;
- cross-impact.

## 17.5 Build timing and current-contract freeze

Parent-order IS / capacity baseline SHALL begin after Seal #1 on **long-side evidence**; it does not require short authority.

Do **not** alter the current AOV-0 frozen turnover-cost baseline or `0.35` max-weight/cap semantics before Seal #1 merely to make them more realistic. Future empirical IS/capacity is a **new contract family** and should be compared prospectively rather than retroactively rewriting the first organism.

---

# 18. Slice S7 — Review / Mutation / Challenger Flywheel

## 18.1 Deterministic review before narrative review

Matured prospective outcomes first pass deterministic reconciliation.

Required:

```text
observed net delta
calculated gross delta
cost delta
residual
```

If reconciliation fails, stop. No ontology/story generation.

## 18.2 MutationManifest

A mutation must be bounded and explicit:

```text
hypothesis
parent model/policy
changed genes/parameters/features
unchanged components
search-family identity
expected failure mode resolved
data/query budget
accept/reject criteria
```

## 18.3 Forecast Challenger progression

```text
Development
→ hidden/untouched OOS where legitimate
→ prospective seal
→ repeated prospective cohorts
→ candidate promotion
```

No retrospective champion replacement based on one attractive backtest.

---

# 19. Endgame Research Capital Operating System

The final system is not one ever-mutating champion.

Target model portfolio:

```text
Safety Parent
Production Champion
1–3 Prospective Challengers
Negative Control
Sentinel Models
Retired Models
```

AI/research automation eventually allocates:

```text
research capital
compute budget
data-acquisition budget
prospective-time budget
hidden-query budget
```

Deterministic risk/portfolio governance allocates financial capital.

### One-line reason

> The highest-value research question is not “what feature can I add?” but “which unresolved uncertainty is most likely to change a capital decision per unit of scarce evidence budget?”

---

# 20. Data Infrastructure — Fastest Honest Version

## 20.1 No universal platform rebuild before the clock

Do not build a universal PIT platform as a prerequisite to Seal #1.

Generalize only data needed by active slices.

## 20.2 Storage pattern

Preferred minimal architecture:

```text
RAW immutable receipts
→ canonical Parquet artifacts
→ DuckDB analytical/replay queries
→ append-only manifests / ledgers for custody
```

Parquet is bulk analytical storage, not the sole source of relational/immutability guarantees.

## 20.3 Data domains by phase

### NOW / S1 — required

- current fundamentals authority;
- current security/listing identity;
- total return/price/volume needed by current AOV P&L and factors;
- exact benchmark source used by the five-arm authority;
- code/policy artifacts and hashes.

### S3 Forecast Challenger — required as hypothesis demands

- legitimate historical price/return panels;
- PIT fundamentals where available;
- factor/sector exposures;
- catalyst/event timestamps only if that family is tested.

### S5 True Short — mandatory

- borrow rate;
- locate quantity/availability;
- HTB / rebate;
- recall/buy-in lineage where feasible.

### Optional later

- options OI / IV / skew;
- dealer-flow proxy;
- supply-chain proxy;
- alternative data.

Optional proxy failure must degrade explicitly; it may not silently impute authority.

---

# 21. API / Provider Contract

Every active external source must expose or be wrapped into:

```text
fetch_id
provider/feed
request timestamp
observed timestamp
provider timestamp if available
raw payload location/hash
parser/canonicalizer version
quality/staleness state
license/retention classification
```

Operational principle:

> **Provider bytes are evidence, not source-code assets.**

Raw vendor files stay out of Git. Retain only what licensing permits, preserve hashes/manifests and retention/redistribution classification, and ensure future replay does not rely on unlawfully retained or redistributable vendor payloads.

## 21.1 Current-cut APIs / feeds

Reuse current CIQ / WRDS / current provider paths already in the repo when they are authoritative for the slice.

Do not replace a working authority merely to satisfy a new architecture name.

## 21.2 Borrow provider

Must prove current feasibility before promising true Long-Short.

## 21.3 Broker/execution API

Needed later for:

```text
orders
fills
cancels
positions
cash
fees
locates/borrow where broker supplies them
```

Not required to start the prospective research clock.

---

# 22. Proxy Scraping Governance

Proxy sources are classified per model/strategy dependency:

```text
REQUIRED
OPTIONAL
ADVISORY
```

### REQUIRED failure

Fail closed.

### OPTIONAL failure

Use an explicitly trained degraded/fallback path and missingness indicator.

### ADVISORY failure

Audit/UI only; does not alter trade authority.

Do not store inference as observed fact.

Good:

```text
dealer_hedging_pressure_proxy
```

Bad:

```text
dealer_is_short_gamma = true
```

---

# 23. Validation & Test Matrix

## 23.1 S1 Pre-Seal adversarial authority tests — mandatory

Normal unit coverage is already strong. Before the first real Clock-Start Receipt, the test priority is **failure injection**: prove the machine cannot accidentally claim knowledge or authority it does not have.

Mandatory v3 tests:

1. **Fresh-process promotion is mandatory**
   - Seal construction alone produces no authoritative clock-start state.
   - Same-process-only verification cannot issue `PROSPECTIVE_CLOCK_START_RECEIPT`.
   - Fresh-process verification failure leaves the Seal Candidate immutable and creates no receipt.

2. **Artifact byte mutation**
   - Flip one byte in a bound market Parquet after candidate creation.
   - Full-chain verification MUST fail on size/hash identity.

3. **Target-vector mutation**
   - Change one target weight by 1 bp or alter serialized target bytes.
   - Verification MUST fail on target vector/hash closure.

4. **Security-identity mutation**
   - Replace a canonical `CIQSEC:<id>` identity or inject ticker/SP_ENTITY_ID/PERMNO authority.
   - Admission/verification MUST fail closed.

5. **Economic-cash authority mutation**
   - Substitute official SOFR−25bp with any proxy/ETF/zero-return cash authority.
   - Arm-5 contract verification MUST fail.

6. **Calendar/economic-time negative tests**
   - non-session/weekend evaluation boundary → BLOCK;
   - evaluation boundary <= cut/seal chronology → BLOCK;
   - wrong close time/session identity → BLOCK;
   - attributed return interval starts before evaluation start → BLOCK;
   - maturity earlier than evaluation_start + 30 calendar days → BLOCK.

7. **Nothing-happened / information-unavailability tests**
   - before Clock-Start Receipt: prospective clock unavailable;
   - before execution/evaluation boundary: executed sleeve outcome unavailable;
   - before maturity: ReviewPacket/outcome opening unavailable;
   - after one seal but before matured review: outcome-informed mutation unavailable.

Existing required positives remain:

- same-cut arm identity;
- input hash stability;
- P&L authority identity;
- no mutable receipt reuse;
- exact v3 schema/calendar identity.

`S1_PASS` requires these adversarial cases in addition to the temporal-authority implementation.

## 23.1A Post-Seal test investments — do not block Clock #1

After the tape starts, add as evidence requires:

- property-based return-reconciliation invariants;
- property-based identity/fail-closed invariants;
- deterministic same-input/code/contract → same-target/hash properties;
- long-running weekly seal/cut simulation;
- artifact retention/recovery drills;
- Challenger isolation tests;
- forecast calibration tests.

Tests should increasingly protect **economic/custody/identity contracts**, not private function layout.

## 23.2 S2 generalized spine tests

- immutable insert/idempotency;
- time-cut visibility;
- exact universe replay;
- exact feature replay;
- prediction hash replay;
- Trial append-only events;
- rejected/failed trials retained.

## 23.3 S3 Forecast tests

- label horizon correctness;
- no feature `available_at > cutoff`;
- calibration separation;
- negative/zero controls;
- time-shift placebo;
- untouched OOS/forward custody;
- forecast outcome attribution.

## 23.4 S4 optimizer tests

- same forward state, different unrealized P&L → same target;
- fresh negative expected value lowers target;
- higher transition cost lowers turnover;
- higher correlation lowers combined exposure;
- constraints always satisfied;
- nonlinear stress failure triggers re-solve, not arbitrary shrink.

## 23.5 S5 short tests

- missing locate kills short only;
- borrow cost enters Net EV;
- locate quantity caps target;
- stale borrow fails closed;
- long eligibility remains independent.

---

# 24. Explicit Backtest / Forward-Test Counts

These are **versioned engineering defaults**, not universal physical laws.

## P0 engineering

```text
1 exact real decision replay
```

Required before generalized P0 is considered mechanically proven.

## P1 historical robustness, only when legitimate PIT exists

```text
Target: 100 decision checkpoints
Target: ≥3 calendar years
```

Moved out of Seal/P0 critical path.

## New Forecast Challenger historical OOS

When legitimate history supports it:

```text
Initial default: 4 temporal OOS folds
+ 1 untouched lockbox
+ cross-sectional holdout when practical
```

If history cannot support honest PIT:

```text
0 fabricated folds.
Use prospective challenger sealing instead.
```

## AOV prospective

```text
weekly seals
current fixed sleeve horizon
first deterministic review after first maturity
```

## Preliminary challenger evidence default

```text
≥3 non-overlapping matured cohorts
or dependence-adjusted equivalent evidence
```

## Shadow / paper operational gate

A `40–60 trading day` window may be a planning default, not the graduation criterion. Adequacy is judged by independent outcomes, overlap/regimes/holding horizon plus explicit PAPER lifecycle/fault coverage, broker-state reconciliation, restart/fencing/`FREEZE_NEW_RISK`, operator drills, and dual-ledger IS attribution.

## Stronger Long-Short paper gate

Require:

- PIT borrow/locate operating throughout the test;
- no unresolved borrow fallback;
- enough events to observe changing locate/rate state;
- cost/IS attribution working;
- portfolio constraints operating.

---

# 25. What Is NOT Allowed on the Critical Path

Until re-audit or an actual blocker proves necessity, the following SHALL NOT delay first prospective evidence:

```text
universal PIT historical rebuild
100 checkpoints / 3 years before first seal
L2/L3 market data
Execution Toxicity Engine
queue-position models
options dealer inventory reconstruction
Spark / distributed compute / GPU research infrastructure
streaming platform / feature platform / microservice rewrite
pre-Seal authority-module or ciq_market cleanup refactor
full OMS
perfect global optimizer
full borrow history
AOV-2 source-app exploration
broad alternative-data ingestion
new Episode-style governance program
```

---

# 26. Current Short-Side Naming Rule

Until PIT borrow/locate is operational:

Never label the active platform or Step 1 as “production Long-Short.”

Allowed names:

```text
AOV evidence vertical
long/cash portfolio
long-side optimizer
synthetic short research comparator (explicit research-only)
```

After S5 passes:

```text
TRUE LONG-SHORT
```

may be enabled.

---

# 27. Capitalization / Live Modules — Start Thin, Reuse Existing Primitives

These do not block prospective research. They **do** carry external/operational lead time, so their thin PAPER path starts after Clock #1 under independent ownership rather than waiting for mature alpha.

Do **not** build a second OMS. Reuse and adapt the repo's existing execution primitives:

- `execution/broker_api.py` — account/position snapshot, submit, recovery lookup, fill telemetry, paper/live guard;
- `main_bot_orchestrator.py` — idempotent retry, ambiguous-receipt reconciliation polling, quarantine;
- `execution/signed_envelope.py` — signed payload and atomic replay protection;
- `gv_portfolio_v0/execution.py` + `book.py` + `replay.py` — deterministic event/book/replay primitives.

The missing work is a thin sim-to-real binding/projection layer, not a new platform.

## Capital-policy / rebalance authority

Required before broker submission:

- exactly one promoted capital policy per rebalance cycle;
- `promoted_policy_id` and `promoted_seal_id`;
- unique `live_rebalance_id`;
- target-vector hash;
- account identity;
- execution-map hash;
- execution policy / TIF;
- owner/risk authority mode (`PAPER`, later `LIVE`, optional `OPERATIONAL_CANARY_ONLY`).

Research arms/cohorts/challengers never become broker sleeves by implication.

## Broker instrument / account adapter

Required:

- hash-bound `CIQSEC:<id>` ↔ broker instrument/asset mapping;
- broker account binding;
- PIT observed/available/effective timestamps;
- tradability / fractional / order-capability state;
- fail-closed ambiguity/staleness behavior.

## Broker lifecycle projection

Canonical live events must cover at least:

- intent submitted;
- accepted / pending-new / new;
- partial fill(s);
- complete fill;
- pending-cancel / canceled / cancel-rejected;
- pending-replace / replaced / replace-rejected;
- rejected;
- expired / done-for-day;
- trade bust;
- trade correction;
- open-order residual / leaves-quantity state.

Broker event streams are lifecycle history; broker snapshots are current external state. Both reconcile into one immutable local event ledger / canonical live account book. A bust/correction appends a correction event and never rewrites the historical fill backward. Live open-order/residual state is part of authority and may not be omitted merely to preserve a historical certification hash.

## Authoritative portfolio state

- account identity;
- positions;
- cash / buying power / equity as policy requires;
- open orders;
- realized/unrealized P&L;
- fees;
- accrued borrow where applicable;
- corporate-action / broker adjustment processing.

## Restart / reconciliation barrier

On every restart or ambiguous execution path:

```text
FREEZE_NEW_RISK = TRUE
→ query broker account / positions / cash-equity / open orders / recent executions-corrections
→ load canonical live book + pending live_rebalance_id / order identities + rebalance_epoch
→ reconcile every difference
→ only clean reconciliation may clear freeze
```

Every account-level capital transition carries a monotonic `rebalance_epoch` / fencing token. A stale or zombie worker whose epoch is not current may not create new-risk intents even if it still possesses valid credentials or old client-order identities.

Unresolved ambiguity keeps `FREEZE_NEW_RISK = TRUE`.

## Research ↔ broker economics bridge

Keep research CIQ-return economics and actual broker/account economics separate. Attribute their difference through implementation shortfall, fees, timing, partial/unfilled quantity, cash drag, financing/borrow, and broker/corporate-action adjustments.

## Calendar / close authority

Current `NYSE_2026_CORE_CLOSE_1600_ET` is a bounded research v3 calendar contract, not a perpetual live-session calendar. Ongoing PAPER/LIVE authority must resolve the actual session close, including early-close sessions, from an authoritative exchange/broker calendar surface.

A hard-coded 16:00 ET close may be used only where the specific session is proven to be a normal close.

## Monitoring / kill

- data freshness;
- forecast/calibration drift;
- execution-map staleness/ambiguity;
- broker/account mismatch;
- open-order ambiguity;
- optimizer infeasibility;
- IS drift;
- borrow shock;
- exposure breach;
- position mismatch;
- strategy/asset/short-side kill controls;
- persistent `FREEZE_NEW_RISK` state across restart until reconciliation clears.

---

# 28. Fastest Endgame Clocks & Capital Paths

The prior M3→M10 list was a dependency inventory but visually encouraged a waterfall. It is superseded by four clocks and two capitalization paths.

## Pre-Seal authority gate

**Current state:** `PRE_SEAL_REAL_CIQ_ADMISSION`.

Deliver:

```text
destructive v3 temporal authority        [CLOSED LOCAL]
+ mandatory adversarial authority tests  [CLOSED LOCAL]
+ real CIQ admission                     [OPEN]
→ first real same-cut five-arm Seal Candidate
→ fresh-process full-chain verification
→ immutable PROSPECTIVE_CLOCK_START_RECEIPT
```

No item below may weaken or bypass that gate.

## CLOCK A — Evidence

```text
Clock-Start Receipt
→ weekly prospective AOV tape
→ frozen original 109 candidate membership
→ fresh weekly measurements / status / market / benchmark-rate state
→ explicit staleness / fail-closed checks
→ matured deterministic ReviewPackets
```

Do not rerun the high-growth screener as the weekly universe selector.

## CLOCK B — Alpha Discovery

Exactly one **active build lane** at a time, but any number of already-sealed immutable tapes may continue collecting future evidence:

```text
Challenger A build → seal A ───────────────┐
Challenger B build → seal B ────────────┐  │
Challenger C build → seal C ────────┐   │  │
                                     ↓   ↓  ↓
                          prospective evidence matures
```

Prediction Ledger + Trial Ledger protect custody and multiple-testing honesty. Shared `UniverseSnapshot` / `FeatureSnapshot` abstractions are extracted only when the second real consumer requires them.

## CLOCK C — External Lead Time

Two externally dominated clocks run without waiting for the serial research chain:

```text
Clock #1
→ borrow / locate entitlement feasibility

first Forecast Challenger seal
→ independent-replication data entitlement / identity / PIT preparation
```

The independent replication surface remains untouched by iterative research until its preregistered use.

## CLOCK D — Capitalization Vertical / Operational Readiness

Immediately after Clock #1, independent ownership starts the thin **Capitalization Vertical** in PAPER mode while research tapes continue:

```text
current frozen AOV target [operational learning only]
→ paper rebalance identity
→ account + CIQSEC↔broker execution map
→ signed account-bound intent
→ broker submit / ACK / partial-fill / terminal lifecycle
→ canonical live book + open orders
→ broker positions/cash/open-orders reconciliation
→ persistent restart / FREEZE_NEW_RISK behavior
→ implementation-shortfall / fees / timing / cash-drag bridge
```

This path remains `financial_alpha_evidence=0` until a promoted capital-relevant research policy exists. When promotion later occurs, exactly one `promoted_policy_id / promoted_seal_id` feeds exactly one `live_rebalance_id`; the adapter is reused rather than replaced.

Close execution is an explicit contract. Initial incumbent=`MOC_CLOSE_AUCTION_V1` (`market + cls`); LOC/close-window/actual-fill variants are challengers only. Research next-close economics must never be silently equated to ordinary DAY-order execution.

## CAPITAL PATH A — Bounded Long/Cash

```text
prospective capital-relevant edge
→ simple deterministic allocation incumbent
   OR optimizer challenger that earns incremental net utility
→ long-side IS / capacity
→ one genuinely independent replication
→ Long/Cash Shadow through the already-running Capitalization Vertical
→ one promoted capital policy → one live_rebalance_id
→ close-execution / actual-fill contract
→ canonical broker lifecycle + positions/cash/open-orders authority
→ restart reconciliation + persistent FREEZE_NEW_RISK
→ research-vs-broker implementation-shortfall bridge
→ explicit owner / risk approval
→ BOUNDED LONG/CASH CAPITAL
```

Required capital gate:

```text
prospective evidence
+ independent replication
+ operational parity
```

True Long-Short is **not** a prerequisite.

## CAPITAL PATH B — Optional Long-Short Extension

Only when economically attractive:

```text
PIT borrow / locate authority
→ short eligibility + borrow economics
→ borrow-adjusted allocation / optimizer challenger
→ Full L/S Shadow B
→ independent L/S replication
→ explicit owner / risk approval
→ BOUNDED L/S CAPITAL
```

True L/S is an economic capability expansion, not a symbolic definition of system completion.

---

# 29. Post-Seal WIP Law — One Build Lane, Multiple Running Tapes

The WIP cap applies to **active engineering construction**, not to immutable experiments already collecting future evidence.

After Seal #1, freeze this law:

```text
ALWAYS-ON
1. weekly AOV prospective tape

CORE CLOSURE
2. deterministic review + custody/replay closure

ONE ACTIVE BUILD LANE
3. one capital-value engineering build at a time
   initial default = independently pre-registered Forecast Challenger
   after seal, that Challenger leaves build WIP and keeps running

ASYNC EXTERNAL LEAD TIME
4. borrow/locate feasibility from Clock #1
5. independent-replication data preparation after first Challenger seal

INDEPENDENT CAPITALIZATION CLOCK AFTER CLOCK #1
6. thin PAPER Capitalization Vertical on current frozen AOV targets
   for account/map/lifecycle/reconciliation/restart/IS learning only
```

Queued work becomes active only when it is the nearest evidence/capital blocker or has genuinely independent ownership:

```text
optimizer challenger
long-side Parent-order IS / capacity
minimal OMS / live operations
post-Seal refactors
```

### Priority under constrained ownership

1. Never miss a legally valid prospective seal.
2. Finish deterministic review/custody before the first outcomes mature.
3. Build and seal Challenger A; then reuse the build lane for B/C while A keeps running.
4. Start independent-replication lead time after the first Challenger seal.
5. Keep borrow entitlement moving asynchronously, without making it a long/cash capital gate.
6. Start the thin PAPER Capitalization Vertical immediately after Clock #1 under independent ownership; do not wait for mature alpha.
7. Bind real close-execution semantics, account/instrument identity, broker lifecycle projection, restart reconciliation, and dual-ledger IS attribution before strategy capital.
8. Activate optimizer only if it is the nearest blocker and require it to beat the simple incumbent on net utility.
9. Capitalize bounded long/cash once evidence + independent replication + Capitalization Vertical authority satisfy the owner/risk gate.
10. Extend to bounded L/S only when borrow-backed economics justify the added complexity.

### One-line reason

> Calendar parallelism is valuable; engineering WIP explosion is not. Future evidence clocks and external lead times should never sit idle merely because one build lane is serial.

---

# 30. CEO / PM Operating KPI After Seal #1

Once Seal #1 succeeds, architecture-completion percentage SHALL stop being the primary operating KPI.

Track separately:

```text
time-to-first-real-seal
weekly seal continuity / missed seals
fresh-process artifact-reopen success
% matured outcomes reconciled exactly
time from maturity → ReviewPacket
active engineering build lane
number of immutable Challenger tapes currently collecting future evidence
number of legally startable evidence clocks left idle
research trials retained, including failures
effective independent prospective cohorts
net effect after frozen cost assumptions
time-to-first-prospective Challenger
independent-replication lead time
time-to-PAPER-Capitalization-Vertical
% broker lifecycle states projected canonically
restart reconciliation / FREEZE_NEW_RISK drill success
research→broker implementation-shortfall reconciliation
borrow-entitlement lead time
time-to-Long/Cash Shadow
time-to-BOUNDED LONG/CASH CAPITAL
time-to-Full-L/S Shadow B
time-to-BOUNDED L/S CAPITAL
```

Keep four score domains separate:

```text
mechanical readiness
prospective-machine readiness
financial-alpha evidence
operational/live readiness
```

A better platform does not automatically increase financial-alpha evidence.

## 30.1 Program-level continue / pivot / stop capital gate

Trial Ledger governs individual research families; CEO/PM governance must also decide whether the **Alpha Program itself** still deserves incremental engineering/data capital.

At every major matured evidence checkpoint, classify the next program action:

```text
CONTINUE
= evidence increased the probability of capital-relevant edge
  or materially improved capital readiness

PIVOT
= the evidence machine works, but the current hypothesis/data/market family does not

STOP / HOLD
= additional engineering does not materially increase
  expected information value or capital readiness
```

The exact thresholds are owner-versioned rather than frozen here, but the direction is mandatory:

> When alpha evidence fails to strengthen, architecture expansion becomes harder to approve, not easier.

Do not respond to absent alpha by automatically adding optimizer sophistication, platform abstraction, alternative data, or true L/S complexity. Each expansion must show how it increases expected information value or net capital utility.

---

# 31. Decision / Evidence Separation

## AOV current control

Rule100 / Parent / Child current policies may continue generating prospective evidence exactly as frozen.

## Forecast challenger

Must not retroactively rewrite current sealed targets.

## Optimizer

Must not rewrite forecast values to satisfy portfolio constraints.

## Research governance

Search-debt / multiple-testing penalties affect promotion evidence, not historical target vectors after the fact.

---

# 32. Important Methodological Anchors

These are intellectual anchors, not code requirements.

- **Markowitz (1952):** portfolio interactions matter; real costs/constraints must be endogenous.
- **Kelly (1956):** sizing logic is useful only under explicit uncertainty/caps; full estimated Kelly is not default production authority.
- **Avellaneda & Lee (2010):** residual/stat-arb is a useful baseline; structural breaks must be modeled explicitly.
- **Almgren & Chriss (2000):** Parent-order execution risk belongs in allocation economics.
- **Bailey / López de Prado, Harvey/Liu:** multiple testing and trial accounting matter; backtest corrections do not substitute for forward evidence.
- **Hansen-Hodrick / Newey-West:** overlapping holding periods require dependence-aware inference.

---

# 33. Re-audit Checklist — Required Owner Decisions

Latest alignment result: **`APPROVED_WITH_WINNER_AND_AUTHORITY_RECUT` at ~99/100 after recuts; prior strategic and sim-to-real recuts are retained; documentation is patched; top-level design is effectively closed; destructive v3 temporal-authority semantics and the pre-Seal adversarial authority suite remain closed locally; execution authority is still blocked only on real CIQ inputs.** The Winner/authority recut changes post-Clock research/capitalization topology and future authority-replacement rules, not the current pre-Seal gate.

## Six owner constitutions — top-level governance surface

Do not create a new owner freeze for every implementation detail. Owner authority is collapsed to six constitutions; implementation beneath them is delegated unless it changes constitutional semantics:

```text
1. FUND MANDATE
   sustainable compounding / capital-weighted right-tail capture;
   long/cash capitalization does not wait for true L/S.

2. RESEARCH CONSTITUTION
   Alpha ontology, Minimum Viable Atlas, search integrity,
   AI boundary, Winner/Core-Alpha gates, first family preregistration.

3. CAPITAL CONSTITUTION
   desired vs allowable vs actual capital;
   portfolio utility, capacity, survival and independent replication gates.

4. EXECUTION CONSTITUTION
   one research→execution benchmark family, capital identity,
   MOC_CLOSE_AUCTION_V1 initial incumbent, dual P&L attribution.

5. LIVE-RISK CONSTITUTION
   hard risk budget, persistent FREEZE_NEW_RISK,
   broker-first restart reconciliation, fencing / zombie-worker prevention.

6. OPERATOR CONSTITUTION
   PAPER/LIVE approval, freeze/unfreeze, manual flatten,
   hard-limit changes and incident authority.
```

The detailed checklist below proves consistency with those constitutions; it is not twenty separate owner meetings.

## Authority

- [x] This document is approved as ROADMAP / CHANGE AUTHORITY.
- [x] Current executable AOV contract/code/receipts remain CURRENT EXECUTION AUTHORITY until implementation evidence updates them.
- [x] `upgrade.md` remains historical transcript, not active spec.
- [x] HFT/toxicity branch is non-authoritative for current mandate.

## Seal #1

- [x] Current identity authority design is sufficient once the real CIQ primary-security bytes are admitted.
- [x] Current `run_4` fundamentals cut is the single current-cut company/universe authority and is hashable.
- [x] Five-arm semantics are same-cut and fixed-policy by current contract.
- [x] Arm 5 is frozen as `ECONOMIC_CASH = official SOFR - 25 bp, ACT/360`; PIT equal-weight remains the risky-asset performance comparator.
- [ ] Real CIQ primary-security + post-close market/P&L bytes are admitted.
- [x] Actual seal write time is system-stamped, distinct from decision-cut creation time, and hash-bound.
- [x] NYSE-session execution-bar validation exists.
- [x] Fresh-process reopen verifies the full cryptographic closure.
- [x] Exact executable-byte manifest is bound.
- [x] Seal Candidate → fresh-process verification proof → separate immutable `PROSPECTIVE_CLOCK_START_RECEIPT`; no caller receives authoritative clock-start state before the receipt exists.
- [x] Execution/evaluation start, daily return interval, and 30-day maturity use one coherent economic contract: next eligible close boundary, only intervals starting at/after evaluation start, maturity from evaluation start + 30 calendar days.

## Generalization

- [x] No second research spine.
- [x] Existing receipts/seals are the primitives to generalize into ledgers.
- [x] Prediction Ledger + Trial Ledger remain early research-integrity infrastructure.
- [x] `UniverseSnapshot` / `FeatureSnapshot` shared abstractions follow the Rule of Two: extract only when the second real consumer requires them.
- [x] P0 gate = one real exact replay; generalized platform completion is not an independent milestone.
- [x] 100 checkpoints/3 years moved to robustness phase.

## Forecast

- [x] New Forecast Layer is challenger first.
- [x] An independently pre-registered Forecast Challenger may be built after Seal #1 without waiting for AOV outcome maturity; only outcome-informed mutation must wait for a matured ReviewPacket.
- [x] One active build lane does not mean one running experiment: after A is sealed, B may use the build lane while A keeps collecting immutable future evidence.
- [x] Multiple running Challenger tapes remain explicitly accounted in Trial Ledger / search-family governance.
- [x] Raw Rule100 score is not relabeled as probability/expected return.
- [x] OOS count is policy-versioned, not a global constant.

## Portfolio construction

- [x] Simple deterministic allocation is the incumbent; the global optimizer is a portfolio-construction challenger.
- [x] Optimizer authority requires incremental net utility after costs, turnover, concentration/risk, capacity, and estimation error.
- [x] Bounded long/cash capital does not wait for an optimizer when the simple incumbent is economically adequate.

## Independent replication

- [x] AOV-109 remains a laboratory, not external-validity proof.
- [x] Independent-replication data/identity/PIT lead time starts after the first Forecast Challenger seal.
- [x] First bounded long/cash capital requires prospective evidence + one genuinely independent replication + operational parity.

## Long-Short

- [x] No production short before PIT borrow/locate.
- [x] Borrow missing/stale = short fail-closed.
- [x] Borrow entitlement feasibility starts in parallel after Seal #1 because vendor/broker lead time is external; short authority remains closed until PIT data exists.
- [x] True L/S is an optional economic extension and is not a prerequisite for bounded long/cash capital.

## Tests / release confidence

- [x] Historical v2 mechanical/custody baseline remains immutable evidence only.
- [x] Destructive v3 authority + adversarial pre-Seal suite = `75/75 PASS`; ZERO-COMPAT seven-zero; active runtime has no v2/open reader or writer.
- [x] Test emphasis is failure/custody/time authority, not additional factor-calculation breadth.
- [x] Property-based/long-running weekly simulations are post-Seal investments and do not block Clock #1.

## Code quality / maintainability

- [x] `APPROVE_WITH_POST_SEAL_REFACTOR`; do not refactor before Clock #1.
- [x] Highest post-Seal refactor = one shared authority validation module to eliminate builder/seal/reopen policy drift.
- [x] `ciq_market.py` split, typed schema registry, structured errors, and comment-history cleanup are queued maintenance, not current critical path.

## Recurring operation

- [x] AOV-0 laboratory candidate membership = frozen original 109 entities.
- [x] Weekly cuts refresh current measurements/status; no weekly rerun of the high-growth screen.
- [x] Missing/stale REQUIRED weekly data fails closed according to the field's contract.
- [x] Weekly seal continuity becomes an operating SLO once Clock #1 starts.

## Execution

- [x] Parent-order IS/capacity is primary execution research and may start on long-side trades before short authority exists.
- [x] HFT queue model is deferred/non-blocking.
- [x] Post-Seal engineering WIP is capped at one active capital-value build lane, while multiple already-sealed Challenger tapes may keep running.
- [x] Thin PAPER Capitalization Vertical starts after Clock #1 under independent ownership and may use current frozen AOV targets for operational learning with `financial_alpha_evidence=0`.
- [x] Capitalization Vertical binds one promoted policy/seal to one `live_rebalance_id`; research arms/cohorts/tapes never become broker sleeves automatically.
- [x] `CIQSEC:<id>` requires a PIT hash-bound broker instrument/account execution map before submission.
- [x] Research close economics require explicit close-auction/close-window/actual-fill execution authority; ordinary default submission is not mechanically equivalent.
- [x] Broker ACK/partial-fill/fill/cancel/reject/expired/open-order state must project into canonical live event/book authority.
- [x] Live open-order residual state must be hash-bound; historical exclusion of `partial_fill_residuals` from the book hash is not sufficient for live authority.
- [x] Restart begins from broker positions + cash/equity + open orders reconciliation; ambiguity persists `FREEZE_NEW_RISK`.
- [x] Research CIQ-return P&L and actual broker/account P&L remain separate ledgers bridged by implementation shortfall / fees / timing / cash drag.
- [x] Production order identity binds rebalance + promoted seal/policy + account + execution-map hash, not only day/symbol/side/qty.
- [x] Ongoing PAPER/LIVE calendar resolves actual session close including early closes; hard-coded 16:00 is not perpetual live authority.
- [x] Borrow entitlement and independent-replication preparation are external lead-time clocks and may run asynchronously.

## Live

- [x] No second OMS is required; reuse existing broker submit/recovery, signed replay, quarantine, and deterministic event/book/replay primitives through a thin capitalization adapter.
- [x] PAPER is the default first broker authority. Optional micro-live canary requires explicit owner/risk approval and remains `OPERATIONAL_CANARY_ONLY`, `financial_alpha_evidence=0`, and non-promotional.
- [x] Minimal account/instrument binding + lifecycle projection + canonical live book/open orders + reconciliation/recovery/kill authority is required before bounded long/cash capital.
- [x] Long/Cash Shadow may begin before true Long-Short through the already-running Capitalization Vertical once a promoted capital policy exists.
- [x] Full Long-Short Shadow B remains blocked on PIT borrow/locate.
- [x] Bounded long/cash and bounded L/S are separate capital gates.

## Program capital allocation

- [x] Major matured-evidence checkpoints require an explicit `CONTINUE`, `PIVOT`, or `STOP / HOLD` program decision.
- [x] Architecture/data/optimizer/L-S expansion must show incremental expected information value or capital readiness; absent alpha does not automatically authorize more platform complexity.

## Integrated leadership disposition

```text
Quant Strategist
= APPROVE_WITH_ONE_MAJOR_UPGRADE
= forecast discovery is the primary research problem;
  multiple preregistered sealed Challengers may accumulate future evidence concurrently.

PM
= APPROVE_BUT_REPLACE_THE_WATERFALL
= manage evidence / alpha-discovery / external-lead-time / capitalization clocks;
  no legally startable evidence clock should sit idle.

CEO
= APPROVE_WITH_CAPITAL_PATH_SPLIT
= bounded long/cash must not wait for true L/S;
  use program-level CONTINUE / PIVOT / STOP-HOLD gates for incremental capital.

Architecture Lead
= APPROVE_WITH_PULL_BASED_GENERALIZATION
= no abstraction before the second real consumer;
  one build lane is not one running experiment.

Code Quality
= APPROVE_WITH_POST_SEAL_REFACTOR

Test Gate
= APPROVED_WITH_PRE_SEAL_ADVERSARIAL_TESTS

Performance
= NO_ACTION_UNTIL_MEASURED_BOTTLENECK

Roadmap Topology
= APPROVED_WITH_WINNER_AND_AUTHORITY_RECUT
= prior strategic/sim-to-real recuts retained; Minimum Viable Atlas first, `CYCLE_RESONANCE_v1` preregistered, six owner constitutions, one incumbent per fork, system-wide destructive authority replacement.

Research / CIO
= RIGHT_TAIL_WINNER_MANDATE
= optimize capital-weighted right-tail capture per unit capital-time under false-winner, catastrophic-loss, frequency, liquidity, capacity, and survival constraints; raw Precision@K is first-class but not the final utility.

Execution Architecture
= REUSE_NOT_REBUILD
= existing broker/recovery/signed-replay/event-book primitives remain foundations; `MOC_CLOSE_AUCTION_V1` is the initial PAPER execution incumbent and alternatives are challengers only.

Ship Decision — pre-Seal gate
= GO
= destructive v3 temporal/adversarial authority closed locally; subject only to real CIQ admission.
```

---

# 34. Owner Approval State Machine

```text
DRAFT
→ REAUDIT_REQUESTED
→ REAUDIT_APPROVED
→ PRE_SEAL_TEMPORAL_AUTHORITY_FIX
→ V3_TEMPORAL_AND_ADVERSARIAL_EVIDENCED
→ PRE_SEAL_REAL_CIQ_ADMISSION   [current]
→ AUTHORITY_FROZEN
→ IMPLEMENTATION_ACTIVE
```

Current state of this document:

```text
PRE_SEAL_REAL_CIQ_ADMISSION
```

Architecture/scientific-bar authority remains approved and shall not be reopened. Prior strategic and sim-to-real recuts are retained. The 2026-08-08 Winner/authority recut preregisters `CYCLE_RESONANCE_v1`, freezes Minimum-Viable-Atlas-first research, six owner constitutions, one-incumbent execution, and system-wide destructive authority replacement; none changes this pre-Seal execution state machine or authorizes implementation before Clock #1. Destructive v3 temporal authority and mandatory adversarial authority tests are green locally: Seal Candidate → fresh-process verification proof → immutable Clock-Start Receipt; coherent close-based evaluation/return-interval/maturity semantics; and tamper/identity/cash/calendar/maturity/nothing-happened negative tests. `AUTHORITY_FROZEN` remains blocked only on real CIQ risky-asset bytes and the resulting real cut/candidate/receipt.

---

# 35. Final North Star

> **Start prospective evidence as early as an honest seal allows. Discover and capture a few exceptional right-tail opportunities rather than maximize model count. Use minimum viable historical truth to freeze an honest family, then seal prospectively and deepen the Atlas underneath the running clock. Replace current authority destructively rather than preserving executable ambiguity. Never call a short position production-valid without borrow authority. Never trade a backtest result as if it were a forward forecast.**

And the fastest-path rule:

> **Admit real CIQ bytes → real Seal Candidate → fresh-process verify → Clock-Start Receipt → weekly frozen-109 evidence stays alive → release the preregistered `CYCLE_RESONANCE_v1` lane and build only enough family-specific PIT Atlas for honest discovery/controls → freeze and seal the first prospective Challenger as soon as possible while deeper Atlas/false-winner/replication work continues underneath → in parallel start the thin Alpaca PAPER Capitalization Vertical using `MOC_CLOSE_AUCTION_V1`, one promoted policy→one `live_rebalance_id`, PIT account/instrument map, canonical lifecycle/open-order authority, restart reconciliation/fencing/`FREEZE_NEW_RISK`, and dual research↔broker P&L → prove independent replication + right-tail/capturability + long-side IS/capacity → BOUNDED LONG/CASH CAPITAL → only if economically attractive, add PIT borrow → true L/S Shadow B → independent L/S replication → BOUNDED L/S CAPITAL.**
