# PREBREAKOUT Untouched Evaluator v1 — W6 Contract

**Date:** 2026-08-10
**Workstream:** W6 — **PREBREAKOUT untouched evaluator only**
**Status:** `CLOSED_DORMANT / BYTES_FROZEN / MECHANICS_IMPLEMENTED / FIXTURE_TESTED / NO_REAL_LOCKBOX_OPENED`
**Authority:** evaluation mechanics only; no discovery, model-fit, promotion, Parent/Child, PAPER, broker, or capital authority
**financial_alpha_evidence:** `0`
**Canonical methodology parent:** `docs/architecture/prebreakout_methodology_freeze_20260810.md`

---

## 0. Purpose

W6 is the **PREBREAKOUT_DISCOVERY_v1 untouched evaluator only**. It sits **after** W2/W3/W4/W5 have frozen the PREBREAKOUT research question, PIT authority, Atlas episode ontology, and development/walk-forward implementation. It is not the VSB confirmation evaluator and must not be used as upstream evaluation authority for W7 / `VSB_CONFIRMATION_v1`.

It answers one narrow question without allowing outcome-driven rescue:

```text
Were immutable PREBREAKOUT predictions written and frozen before an untouched
lockbox label surface opened, and what do those predictions score on the frozen
right-tail / lead-time / incremental metrics?
```

W6 does not create predictions and does not expose discovery labels. It consumes only normalized immutable rows plus explicit custody records.

Implementation:

```text
research/prebreakout_untouched_evaluator_v1/
  contracts.py
  evaluator.py
```

Tests:

```text
tests/prebreakout_untouched_evaluator_v1/test_evaluator.py
```

---

## 1. Hard custody sequence

Every lockbox is two-stage:

```text
frozen W2/W5 implementation
→ normalized prediction rows
→ PredictionFreezeRecordV1
→ external/independent custody holds labels closed
→ label surface opened once
→ LabelOpenRecordV1
→ W6 deterministic evaluation
```

The evaluator requires **at least one preregistered lockbox**.

For every lockbox it mechanically verifies:

```text
exact contract identity
exact prediction snapshot hash
all prediction rows recorded <= prediction freeze time
prediction freeze time < label open time
exact label + I-vs-I+X utility snapshot hash
exact lockbox set
exact prediction/label denominator join
```

The code can verify the cryptographic/content closure supplied to it. Independent custody remains responsible for the real-world truth of the recorded timestamps and lockbox secrecy; W6 does not pretend a local timestamp is an external attestation.

---

## 2. Evaluation contract

`build_evaluation_contract(...)` freezes:

```text
family_id
implementation_id
primary_label_spec_id
>= 1 lockbox_id
K values for Precision/Recall/Lift@K
minimum legitimate pre-breakout lead sessions (must be >= 1)
score direction = HIGHER_IS_BETTER
preregistered zero-statistical-weight listing identities
prediction ledger hash
implementation manifest hash
search ledger hash
evaluator code hash
```

The contract itself is content-addressed.

Changing these after label open is not a rerun. It is a new charged contract/version.

---

## 3. Exact identity / denominator law

The join key is:

```text
(lockbox_id,
 decision_session_date,
 CIQSEC security_id,
 trading_item_id)
```

No ticker, company/entity, PERMNO, alternate listing, survivor mapping, or other fallback exists in W6.

Prediction rows and label rows must form an **exact set equality** on that join key. One missing label or one missing prediction hard-fails; W6 never silently shrinks the denominator.

Upstream W3 remains responsible for proving the date-local risk set, availability, corporate actions, and no-survivor source authority. W6 consumes that exact listing identity and refuses to weaken it.

---

## 4. MU / SNDK smoke law

W6 contains **no ticker literals and no special-case branches**.

Zero statistical weight is possible only when the exact `CIQSEC|trading_item_id` identity was frozen inside `zero_weight_identity_keys` before label open.

For every such row:

```text
statistical_weight = 0
zero_weight_reason = ENGINEERING_SMOKE_ZERO_STATISTICAL_WEIGHT
```

All other identities must have weight `1`.

Therefore MU/SNDK can be traced end to end by W4/W5/W6 while contributing exactly zero to:

```text
Precision / Recall / Lift
PR-AUC / Average Precision
TTFLD promotion statistics
false/catastrophic-winner denominators
right-tail wealth capture
independent-episode counts
```

Their diagnostics remain visible in `zero_weight_episode_diagnostics`.

No post-result decision can reclassify an inconvenient security to zero weight under the same contract.

---

## 5. Prediction-before-label law

Each normalized prediction row binds:

```text
prediction_id
family_id
implementation_id
lockbox_id
decision_context_id
decision_session_date
decision_session_ordinal
CIQSEC security_id
trading_item_id
score
flagged
eligibility_status = ELIGIBLE | EXCLUDED
exclusion_reason
knowledge_cutoff
prediction_made_at
prediction_recorded_at
statistical_weight
zero_weight_reason
```

Mechanically required:

```text
knowledge_cutoff <= prediction_made_at <= prediction_recorded_at
prediction_recorded_at <= prediction-freeze sealed_at
prediction-freeze sealed_at < label-open opened_at
```

`EXCLUDED` rows cannot be flagged and must carry an explicit exclusion reason. `ELIGIBLE` rows cannot carry an exclusion reason.

For a true winner episode with algorithmic breakout session `B`, any decision row at `B` or later is rejected from W6 entirely. A legitimate TTFLD detection must be at least the preregistered minimum lead, which for PREBREAKOUT v1 is expected to preserve the methodology law of **B-1 or earlier**.

This blocks post-breakout rescue even if a caller rebuilds all downstream hashes consistently.

---

## 6. Label / episode surface

Every untouched label row binds:

```text
primary label spec
same lockbox/date/listing join key
winner_label
catastrophic_outcome_label
realized_total_return
right_tail_wealth
effective_episode_id
breakout_session_date / breakout_session_ordinal for winners
statistical_weight / zero-weight reason
```

For one `effective_episode_id`, W6 requires invariant:

```text
listing identity
winner status
catastrophic status
right-tail wealth
breakout session
statistical weight
```

This prevents repeated date rows from silently changing the identity/economics of one episode after labels open.

`effective_episode_id` is supplied by the frozen upstream W4/W5 dependence/clustering law. W6 **counts** effective episodes and reports raw/effective ratios; it does not recluster after seeing lockbox outcomes.

---

## 7. Metrics implemented

### 7.1 Precision / Recall / Lift @ K

W6 computes date-local rankings for each preregistered K.

Ranking law:

```text
eligible rows only
descending score
deterministic tie-break:
security_id → trading_item_id → prediction_id
```

The winner/base-rate denominator remains the full statistical date-local risk set, including deterministic exclusions, so a missing feature cannot disappear from recall/base-rate accounting.

The report exposes macro and micro:

```text
Precision@K
Recall@K
Lift@K
selected count
true-positive count
winner count
risk-set row count
```

### 7.2 PR-AUC / Average Precision

W6 reports deterministic **Average Precision** under the field:

```text
pr_auc_average_precision
```

Eligible observations rank first by frozen score; deterministic exclusions sit below scored observations so excluded winners remain a penalty rather than disappearing.

### 7.3 TTFLD / missed winners

For each statistical winner episode:

```text
first legitimate flagged decision session <= B - minimum_lead
TTFLD = B_ordinal - first_detection_ordinal
```

W6 reports:

```text
winner effective episodes
detected winner effective episodes
missed winner effective episodes
pre-breakout detection recall by effective episode
TTFLD mean / median / min / max
explicit exclusion reasons for missed/excluded episodes
```

### 7.4 False / catastrophic winners

A false-winner episode is a non-winner effective episode with at least one eligible threshold flag.

A catastrophic false winner additionally carries the frozen catastrophic outcome label.

W6 reports both effective-episode counts/rates and raw false-flag counts.

### 7.5 Right-tail wealth capture

W6 reports signal-level right-tail wealth capture across unique statistical winner episodes:

```text
total right-tail wealth
wealth captured by legitimate pre-breakout threshold flag
capture ratio
Top-K pre-breakout wealth capture for every preregistered K
```

This is not the capital-weighted shadow metric. Capital weighting/capacity/wrong-winner stress remains the later fixed-policy shadow-economics layer.

### 7.6 Effective episodes

W6 reports:

```text
raw statistical security-observation count
effective independent episode count
effective/raw ratio
decision-date count
exact listing count
```

Sector/industry/macro clustering semantics are not reinvented here; the upstream frozen episode ID is the authority.

### 7.7 I vs I+X incremental net utility

A separate label-open-bound utility surface contains period-level:

```text
incumbent_net_utility                    = I
incumbent_plus_candidate_net_utility     = I + X
```

W6 reports:

```text
period count
sum(I)
sum(I+X)
sum incremental net utility
mean incremental net utility
fraction of periods with positive incremental utility
per-lockbox breakdown
```

The implementation/search/cost-policy identity is indirectly frozen through the evaluation contract's implementation-manifest/search-ledger hashes. W6 does not retune the policy after seeing utility.

---

## 8. Fail-closed attacks covered by tests

Fixture tests currently cover:

```text
no lockbox preregistered
prediction statistical weight changed after preregistration
prediction recorded after prediction-freeze time
label opened before prediction freeze
exact denominator/label row dropped
label bytes changed after label-open receipt
ticker identity substituted for CIQSEC
post-breakout winner row injected as a rescue
same effective episode changes wealth/identity semantics across dates
report bytes/authority tampered after evaluation
W6 imports discovery/provider/model-fit/broker dependencies
```

The W6 fixture suite has no empirical authority and opens no real lockbox.

---

## 9. Upstream / downstream integration

**Scope boundary:** W6 has no VSB/W7 evaluator authority. Any future VSB matured-date receipt consumed by W7 must come from a separately authorized VSB-specific outcome evaluator/custody path, not from `prebreakout_untouched_evaluator_v1`.

### Required from W2/W3/W4/W5 before a real W6 run

```text
W2 frozen PREBREAKOUT family/implementation/label/K/lead/falsifier contract
W2 search ledger hash and implementation manifest hash
W3 exact date-local CIQSEC + trading-item PIT authority
W4 full census episode IDs and frozen zero-weight smoke identities
W5 immutable untouched prediction rows for >= 1 lockbox
W5/external custody prediction-ledger hash
frozen I-vs-I+X utility policy surface
independent evidence that labels remained closed until LabelOpenRecord
```

### W6 emits

```text
content-addressed untouched evaluation report
right-tail / lead-time / false-winner / effective-episode / I-vs-I+X metrics
zero-weight smoke diagnostics
zero promotion/capital authority
```

### W6 explicitly does not emit

```text
new model
new threshold
new horizon
new risk set
new search trial
rescued version
financial_alpha_evidence increment
promotion decision
PAPER order
broker order
Parent/Child mutation
```

---

## 10. Current W6 state

```text
W6_SCOPE                             = PREBREAKOUT_UNTOUCHED_EVALUATOR_ONLY
W6_STATUS                            = CLOSED_DORMANT
W6_BYTES                             = FROZEN
W6_MECHANICS                         = IMPLEMENTED
W6_FIXTURE_TESTS                     = PASS
REAL_UNTOUCHED_LOCKBOX_CONSUMED      = FALSE
REAL_LABEL_SURFACE_OPENED_BY_W6      = FALSE
PREBREAKOUT_EMPIRICAL_RESULT         = NONE
W7_VSB_EVALUATOR_AUTHORITY           = NONE
financial_alpha_evidence             = 0
promotion_authority                  = NONE
capital_authority                    = NONE
```

**No real lockbox means no more W6 work.** Reopen W6 only after all of the following are true:

```text
W2/W5 PREBREAKOUT implementation is frozen
>= 1 PREBREAKOUT lockbox is preregistered
immutable PREBREAKOUT predictions are sealed
external custody authorizes the one-time label opening
```

When eventually run, the frozen acceptance remains exactly: prediction/label denominator equality; prediction freeze before label open; no post-B rescue; Precision/Recall/Lift, AP/PR-AUC, TTFLD, false/catastrophic winners, effective episodes, right-tail wealth and I vs I+X; MU/SNDK zero statistical weight. No additional W6 feature or metric work is authorized while dormant.
