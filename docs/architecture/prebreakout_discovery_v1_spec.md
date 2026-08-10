# PREBREAKOUT_DISCOVERY_v1 — W2 Scientific Preregistration

**Date:** 2026-08-10
**Owner lane:** W2
**Status:** `SCIENTIFIC_CONTRACT_FROZEN / OUTCOME_BLIND / NO_REAL_TRIAL_CHARGED / NO_CLOCK_START`
**Family:** `PREBREAKOUT_DISCOVERY_v1`
**Canonical Python authority:** `research/prebreakout_discovery_v1/preregistration.py`
**Mechanical breakout/lead law:** `research/prebreakout_discovery_v1/breakout.py`
**Persistent Trial/Search Ledger mechanics:** `research/prebreakout_discovery_v1/ledger.py`
**financial_alpha_evidence:** `0`
**capital authority:** `NONE`

**Immutable W2 authority version:** `PREBREAKOUT_W2_CONTRACT_v1`
**methodology_contract_sha256:** `94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71`
**breakout_contract_sha256:** `94c8756e11d4e31cbf4d6ca4953b63c83306f4b357a42f0b70c94ae3fd261e71`
**Canonical downstream handoff:** `docs/context/prebreakout_w2_binding_current.md`

The methodology and breakout fields intentionally use the same v1 seal: breakout B/B-1 is part of one immutable W2 scientific contract, not a separately mutable scientific authority. This record operationalizes the methodology freeze in `prebreakout_methodology_freeze_20260810.md`. It does not perform provider acquisition, open historical/untouched labels, append a prospective prediction, mutate VSB, or start a third running Alpha clock.

---

## 1. Ownership boundary

W2 owns exactly:

```text
algorithmic breakout reference B
B episode de-duplication law
primary/secondary winner horizons and top-5% label identity
TTFLD law
B-1 smoke obligation
family/version falsifiers
small material-search budget
persistent append-only Trial/Search Ledger law
```

W2 does **not** own:

```text
W1 Clock #1 custody/outcome authority
W3 CIQSEC + Trading Item PIT/source authority
W4 Atlas label opening/census mechanics
W5 rolling/expanding walk-forward implementation
W6 untouched lockbox evaluation
W7 VSB confirmation retuning (forbidden)
W8 Sector Rotation
W9 CRV1
W10 replication outcomes/PAPER orders
```

A result cannot be promoted by claiming that W2's contract freeze is itself evidence.

---

## 2. Frozen family / risk-set / label identity

```text
family_id                  = PREBREAKOUT_DISCOVERY_v1
risk_set_spec_id           = PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1
primary_label_spec_id      = PREBREAKOUT_RIGHT_TAIL_20D_TOP5_V1
secondary_label_spec_id    = PREBREAKOUT_RIGHT_TAIL_10D_TOP5_V1
primary_horizon            = 20 observed sessions
secondary_horizon          = 10 observed sessions
winner_fraction            = 0.05
```

The risk-set ID is intentionally identical to W3's date-local PIT authority. W2 does not permit a current-survivor, AOV-109, ticker, entity, PERMNO, alternate-listing, or current-primary substitute.

For horizon `H` and a date-local risk set at decision session `t`:

```text
F_H(i,t) = product(1 + r(i,s)) - 1
           over the next H observed primary-listing sessions after t

winner_count_t = ceil(0.05 * date_local_risk_set_count_t)
```

Tie-break:

```text
forward_total_return DESC
security_id ASC
trading_item_id ASC
```

An incomplete horizon is `INCOMPLETE_HORIZON`; it is not imputed and cannot receive matured-denominator credit.

W2 freezes label semantics but does not open any label surface. W4/W5 may use discovery labels only under their own authority; W6 owns untouched label-open custody.

---

## 3. Frozen algorithmic breakout B

### 3.1 Input authority

`B` is computed for one exact W3-authorized primary listing using PIT corporate-action-normalized close observations. The input identity is the exact `CIQSEC + Trading Item` listing. W2 never resolves identity from a display ticker.

### 3.2 Raw breakout law

For observed session index `t`, after at least 20 prior observed listing sessions:

```text
prior_high_20(i,t) = max(close(i,t-20), ..., close(i,t-1))

RAW_BREAKOUT(i,t) = close(i,t) > prior_high_20(i,t)
```

The comparator is **strict**. Equality with the prior high is not a breakout. Missing, non-finite, non-positive, duplicate-session, or mixed-listing input fails closed rather than being repaired.

### 3.3 Episode de-duplication

After accepting a breakout session `B_j`, another raw breakout becomes a new episode only when:

```text
B_{j+1}_index - B_j_index > 20
```

Therefore at least 20 full observed sessions must lie between accepted breakout episodes. This prevents a multi-day continuation through fresh highs from being counted as many separate pre-breakout opportunities.

### 3.4 What B is not

`B` is a reference event used to measure whether PREBREAKOUT was genuinely early. It is **not** the predictive trigger. It has no volume, volatility-compression, VSB score, fundamental, sector, news, or ticker-specific condition.

This is deliberate: VSB remains the separate frozen confirmation component. Adding a VSB-style condition to `B`, changing the 20-session lookback, changing strict `>`, or changing the episode cooldown is a new W2 version, not an in-place repair.

---

## 4. TTFLD law

`TTFLD` means **Time-to-First-Legitimate-Detection**, measured in observed listing sessions before algorithmic breakout `B`.

Frozen legitimate detection window:

```text
[B-20, B-1]
```

For one winner/breakout episode:

```text
first_legitimate_detection = earliest immutable PREBREAKOUT flag
                             inside [B-20, B-1]

TTFLD = B_session_ordinal - first_detection_session_ordinal
```

Therefore:

```text
1 <= TTFLD <= 20  => legitimate pre-breakout detection
flag at B         => too late / no pre-breakout credit
flag after B      => too late / no pre-breakout credit
flag before B-20  => stale for PREBREAKOUT_v1 / no TTFLD credit
no legitimate flag=> MISSED_PREBREAKOUT
```

For aggregate falsifier/evaluator statistics, a miss has:

```text
effective_TTFLD = 0
```

This prevents conditioning lead-time statistics only on successful detections.

---

## 5. MU / SNDK smoke obligation

MU and SNDK are named **engineering smoke traces only** outside the core algorithm:

```text
statistical_weight             = 0
promotion_denominator_weight   = 0
special_case_scoring           = FORBIDDEN
special_case_universe_admission= FORBIDDEN
ticker-literal model branch    = FORBIDDEN
```

The generic W2/W3 handshake is:

```text
IF W3 proof = PIT_ELIGIBLE_B_MINUS_1:
    exact B-1 must equal the immediately prior observed session to B
    PREBREAKOUT must have a legitimate flag at or before B-1
    (and within the frozen B-20 ... B-1 TTFLD window)
    ELSE W2 fails the smoke obligation

IF W3 proof = DETERMINISTIC_EXCLUSION:
    accept only W3's frozen deterministic exclusion vocabulary
    log the exact reason
    give the case zero statistical weight

IF W3 proof = DETERMINISTIC_UNAVAILABLE:
    DO NOT count it as an exclusion/pass
    hold the case/clock until upstream authority is available
```

Accepted W3 deterministic exclusion reasons:

```text
NON_US_LISTING
NON_COMMON_EQUITY
NON_PRIMARY_LISTING
AMBIGUOUS_PRIMARY_LISTING
NOT_ACTIVE_TRADABLE
CORPORATE_ACTION_UNRESOLVED
CORPORATE_ACTION_TERMINAL_EFFECTIVE
NOT_IN_DATE_LOCAL_SOURCE_POPULATION
```

Upstream-unavailable reasons that **block** rather than satisfy the W2 obligation:

```text
BREAKOUT_CONTRACT_UNBOUND
B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE
IDENTITY_UNBOUND
```

`enforce_b_minus_one_pit_proof(...)` also requires the W3-style proof to bind the current W2 contract hash, carry zero statistical/promotion weight, declare `display_symbol_used_for_logic=false`, and prove no outcome/capital authority.

The earlier W3 receipt `prebreakout_pit_w3_mu_sndk_20260810.json` was correctly created while W2 was still unbound. Its `BREAKOUT_CONTRACT_UNBOUND` MU/SNDK records remain historical custody evidence but **do not satisfy the now-frozen W2 smoke obligation**. W3 must regenerate the proof against this W2 hash once exact B/B-1 sessions and source-complete date-local CIQ authority exist. W2 does not acquire or fabricate those missing source bytes.

---

## 6. Frozen falsifier constitution

### 6.1 Invalidation falsifiers

These make the result scientifically unusable rather than merely negative:

```text
PIT_OR_CUSTODY_BREACH
  any future leakage, survivor back-projection, identity fallback,
  unresolved corporate-action substitution, prediction-after-label,
  or shared mutable outcome authority

SEARCH_CONTAMINATION_OR_BUDGET_BREACH
  any material variant inspected without a charged Trial-Ledger open,
  or cumulative material trials > 8
```

An invalidated result cannot be repaired under the same version.

### 6.2 Economic falsifiers

These are frozen before untouched/prospective evaluation:

```text
NO_RIGHT_TAIL_ENRICHMENT
  untouched primary-20d prebreakout Recall/Lift <= breadth-matched baseline

NO_POSITIVE_PREBREAKOUT_LEAD
  eligible true-winner episodes have median effective TTFLD <= 0

CATASTROPHIC_FALSE_WINNER_NOT_IMPROVED
  bottom-5%-return false-winner rate >= preregistered matched-control rate

NO_INCREMENTAL_I_PLUS_X
  preregistered I+X net utility <= incumbent I

PROSPECTIVE_EFFECT_FAILS
  prospective eligible winner episodes fail to retain positive ex-ante
  lead/right-tail enrichment under the frozen evaluator

INDEPENDENT_REPLICATION_FAILS
  quarantined identity/PIT/license replication fails to reproduce the
  frozen-direction prebreakout effect
```

A triggered falsifier is evidence about the frozen version. It is never permission to change a threshold/horizon/window and rerun the same identity.

---

## 7. Search budget — hard maximum 8

```text
search_family_id              = PREBREAKOUT_SEARCH_v1
trial_ledger_scope            = PREBREAKOUT_V1_TRIAL_LEDGER
prediction_ledger_scope       = PREBREAKOUT_V1_PREDICTION_LEDGER
artifact_namespace            = prebreakout_discovery_v1/
material_trial_budget_max     = 8
cost_per_material_variant     = 1
```

The budget is intentionally small. Four temporal OOS folds are evidence partitions, **not four free searches**. One implementation evaluated across all frozen folds is one material trial; changing a charged scientific choice creates another material trial.

Each of these consumes one material trial before result inspection:

```text
feature family / representation
transform or window variant
model class
hyperparameter set
training window
calibration method
ranking threshold / Top-K choice
control definition
cross-sectional holdout definition
```

A failed, null, aborted, rejected, or negative trial remains charged. There is no refund.

These require a **new family/version**, not another trial under the eight-count budget:

```text
risk-set semantics
primary horizon
primary outcome label
breakout-B definition
TTFLD law
winner fraction
material economic mechanism
falsifier constitution
search budget itself
```

Synthetic unit tests of fixed mechanics do not consume search budget because they do not inspect discovery/untouched/prospective outcomes.

---

## 8. Persistent Trial/Search Ledger

`research/prebreakout_discovery_v1/ledger.py` implements the W2 persistent ledger as hash-chained append-only JSONL under an exclusive writer lock.

### `TRIAL_OPEN`

A material trial is charged **before** its result is inspected. **Real `TRIAL_OPEN #1` is forbidden until both the exact Trial-1 data/source manifest and the exact Trial-1 implementation manifest are frozen first.** The open record must then bind their corresponding source/code identities plus explicit scientific identity including:

```text
trial_id
implementation_id
feature_spec_id
transform_spec_id
model_spec_id
training_window_spec_id
calibration_spec_id
ranking_spec_id
control_spec_id
cross_sectional_holdout_spec_id
temporal_fold_plan_id
source_manifest_sha256
code_sha256
```

It seals:

```text
outcome_access_class       = DISCOVERY_DEVELOPMENT_ONLY
untouched_lockbox_access   = FORBIDDEN
prospective_outcome_access = FORBIDDEN
material_trial_cost        = 1
```

### `TRIAL_CLOSE`

Close is a zero-cost immutable follow-up with status:

```text
COMPLETE | FAILED | NULL | ABORTED | REJECTED | SELECTED
```

The close does not refund the open charge.

The ledger fails closed on duplicate opens/closes, close-without-open, partial lines, writer-lock collision, non-monotonic timestamps, tampering, scientific-identity/hash gaps, or a ninth material trial.

No real W2 development trial is opened by this preregistration round. Repository closure inspection also finds no non-test PREBREAKOUT Trial-Ledger file and no non-test `TRIAL_OPEN` record. Therefore the current consumed real-search count remains `0/8`.

Fixture/unit-test `TRIAL_OPEN` calls are mechanics checks only and do not consume the real scientific budget. W5's walk-forward contract binds to these W2 identities and limit; W5 does not own a second search budget and may not begin a real charged run before the two Trial-1 manifests above are frozen.

---

## 9. Clock / outcome / capital no-go

This W2 freeze authorizes **contracts and mechanics only**.

```text
provider acquisition by W2       = FORBIDDEN / NOT PERFORMED
historical Atlas label open by W2 = FORBIDDEN / NOT PERFORMED
untouched lockbox label open      = FORBIDDEN / NOT PERFORMED
prospective prediction append     = FORBIDDEN / NOT PERFORMED
new PREBREAKOUT clock start       = NOT AUTHORIZED
VSB retune                         = FORBIDDEN
A2 re-query                        = FORBIDDEN
Clock #1 outcome open              = FORBIDDEN
Parent/Child mutation              = FORBIDDEN
PAPER/broker order                 = FORBIDDEN
financial_alpha_evidence increment = 0
capital authority                  = NONE
```

The first legitimate downstream sequence remains W3 source closure → W4 Atlas census → W5 charged development/freeze → W6 untouched evaluator → prospective time. No stage may use W2's contract hash as a substitute for actual evidence.

---

## 10. W2 acceptance tests

W2 closes only when fixture/mechanical tests prove:

```text
strict prior-20-session B comparator
equality is not B
20-full-session episode cooldown
one-listing/finite/unique-session fail-closed B inputs
TTFLD earliest flag only inside B-20 ... B-1
flag at B is too late
miss effective TTFLD = 0
B-1 eligible smoke requires a legitimate pre-B flag
W3 deterministic exclusion vocabulary is exact
W3 deterministic unavailable blocks
W3 proof binds this W2 hash and exact B-1 session
smoke rows remain zero-weight
no named-ticker/provider/outcome/broker branch in W2 core
Trial Open charges before result inspection
failed/null trials do not refund budget
hard 8-trial cap; ninth open fails
append-only chain/tamper/partial-line/writer-lock checks
explicit scientific identity/hash required per material trial
```

These tests are mechanical evidence only. They are not historical alpha, untouched alpha, prospective alpha, or capital evidence.

---

## 11. Frozen disposition

```text
W2_SCIENTIFIC_CONTRACT          = FROZEN
BREAKOUT_B                      = PRIOR_20_HIGH_STRICT_GT / 20_SESSION_EPISODE_COOLDOWN
PRIMARY_HORIZON                 = 20 SESSIONS / TOP 5%
SECONDARY_HORIZON               = 10 SESSIONS / TOP 5%
TTFLD                           = EARLIEST FLAG IN B-20..B-1 / MISS=0 EFFECTIVE
SEARCH_BUDGET                   = 8 MATERIAL TRIALS HARD MAX
PERSISTENT_TRIAL_LEDGER         = IMPLEMENTED / HASH-CHAINED / EXCLUSIVE WRITER
MU_SNDK_STATISTICAL_WEIGHT      = 0
MU_SNDK_CURRENT_W2_OBLIGATION   = NOT YET SATISFIED; W3 REFRESH REQUIRED
REAL_TRIALS_CHARGED             = 0
OUTCOME_OPEN                    = FALSE
PROSPECTIVE_CLOCK_STARTED       = FALSE
financial_alpha_evidence        = 0
capital_authority               = NONE
```
