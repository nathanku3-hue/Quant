# AOV Winner Capture Diagnostic v0 — Frozen Historical Diagnostic Law

**Date:** 2026-08-10  
**Status:** `FROZEN_RETAINED_BYTE_DIAGNOSTIC / IMPLEMENTED`  
**Authority:** historical discovery/forensic evidence only  
**Financial Alpha evidence:** `0`  
**A2 re-query:** forbidden  
**Rule100 / Parent / Child mutation:** forbidden

---

## 0. Purpose

Explain where extreme future winners are lost by the frozen AOV support path without changing the strategy or consuming a second A2 evaluation.

The diagnostic reads only already-retained A1/A2 report bytes, their already-created Rule100/Parent/Child weight matrices, and the exact market source files whose SHA-256 hashes are bound in those reports.

It does **not**:

```text
call Capital IQ or another provider
invoke the A2 evaluator
rebuild or mutate Rule100/Parent/Child
change Clock #1
create financial Alpha evidence
use SNDK/MU as a pass/fail target
```

---

## 1. Structural premise

Frozen code proves the support bottleneck:

```text
Rule100 target support ⊆ sizing_eligible
Parent target support ⊆ Rule100 target support
Child target <= Parent target, security by security
```

`research/aov0/ciq_market.py` creates positive Rule100 target weight only for current-cut `sizing_eligible` names. `research/aov0/policy.py` zeros Parent outside base support and explicitly prevents Child from exceeding Parent.

Therefore this diagnostic attacks **winner access first**. Parent and Child can change allocation/capture conditional on access; they cannot create access to a winner excluded by Rule100 support.

---

## 2. Retained evidence boundary

Accepted stages:

```text
A1 evidence_classification = A1_ADMITTED_HISTORICAL_PIT
A2 evidence_classification = A2_UNTOUCHED_HISTORICAL_PIT
financial_alpha_evidence = 0 for both
A2 evaluation_query_count = 1
A2 second_evaluation_forbidden = true
```

Every report-listed market file is re-hashed before use. Arm `target_weights.csv` and `executed_weights.csv` are also hashed into the diagnostic custody block.

The diagnostic verifies:

```text
executed_weights_t = target_weights_{t-1}
```

with the first executed row equal to zero, matching `core/engine.py` one-bar execution lag.

No network/provider path is imported by the diagnostic module or CLI.

---

## 3. Anchor law

AOV target weights are forward-filled daily between actual state changes. Counting every repeated daily copy would overweight one weekly decision.

The frozen diagnostic anchor set is therefore:

```text
anchor_t = first target row
        OR any date where any Rule100 target weight differs from t-1 by > 1e-12
```

This is implemented by `state_change_anchors(...)` in `research/aov0/winner_capture.py`.

It includes ordinary weekly target changes and deterministic lifecycle/terminal-event support changes. It does not infer or tune hidden rebalance dates from future returns.

---

## 4. Winner labels

For each anchor date `t` and horizon `H ∈ {10,20}`:

```text
F_H(i,t)
= product_{s=t+1 ... next H observed replay sessions}(1 + r(i,s)) - 1
```

The anchor-date return is excluded. A label is emitted only when all `H` future replay sessions are already present in retained custody.

Winner set:

```text
K_t = ceil(0.05 * N_t)
W_H(t) = top K_t securities by F_H(i,t)
```

Tie break is deterministic:

```text
forward_total_return DESC
security_id ASC
```

Primary label = 10 sessions. Secondary label = 20 sessions.

For retained A1/A2, `N_t = 94`, hence `K_t = 5`.

---

## 5. Risk-set boundary

The label universe is the frozen 94-security Lane-2 replay cohort. Therefore:

```text
risk_set_access recall within the diagnostic label universe = 100%
```

This does **not** mean the original research process accessed all market winners. It means the retained A1/A2 bytes can only measure winner access **conditional on the frozen Lane-2 cohort**.

No out-of-cohort winner-recall claim is authorized from this diagnostic. That limitation is one reason Fast Family #2 uses an independent broader objective risk set.

---

## 6. Funnel definitions

For each winner episode `(t, i, H)`:

### 6.1 Risk-set access

```text
security i belongs to the frozen diagnostic denominator
```

By label construction this is true for all labelled winners; the count is retained explicitly so the out-of-cohort limitation is visible.

### 6.2 Sizing eligibility

Proxy is exact for the frozen current-cut replay:

```text
Rule100 target_weight(i,t) > 1e-12
```

because positive Rule100 support exists only for `sizing_eligible` names.

### 6.3 Nonzero forecast/support

```text
Parent target_weight(i,t) > 1e-12
```

Parent cannot create support outside Rule100; this stage is expected to equal or shrink the prior stage and is retained explicitly as an invariant check.

### 6.4 Entry lead

```text
Parent executed_weight(i, first outcome session after t) > 1e-12
```

The report also records consecutive support age before the anchor:

```text
entry_lead_sessions_before_anchor
= consecutive positive Parent target sessions ending at t - 1
```

where a newly admitted winner has zero prior lead.

### 6.5 Capital allocated

Binary funnel count:

```text
Parent executed_weight(i, first outcome session) > 1e-12
```

Quantitative episode statistic:

```text
winner_capital_share_first_session
= sum Parent executed weights on winner set
  / Parent risky gross exposure on the first outcome session
```

### 6.6 Contribution captured

The monotone funnel credits only on-time entry:

```text
entry_lead = true
AND
sum_{next H sessions}(Parent executed_weight * security_return) > 0
```

A winner first entered later inside the H-session window is reported separately as `late_entry_captured`; it cannot retroactively receive entry-lead credit.

### 6.7 Child clipping

For each winner episode:

```text
winner_gross_giveup
= Parent winner contribution - Child winner contribution
```

Positive values are clipping/give-up. Overlapping 10d/20d episode sums are explicitly marked `episode_overlap_sensitive=true` and are not treated as realized stage P&L.

### 6.8 False-positive / downside avoided

For Parent-supported nonwinners at anchor `t`:

```text
false_positive = in Parent support AND not in W_H(t)
downside_false_positive = false_positive AND F_H(i,t) < 0
child_avoided_loss = max(Child contribution - Parent contribution, 0)
```

This measures the risk-control benefit of Child on supported names that subsequently lost money while keeping it separate from missed-winner cost.

---

## 7. Winner recall / breadth lift

Across eligible anchors:

```text
winner_recall
= total sizing-eligible winners
  / total labelled winners

selection_breadth
= mean_t (Rule100 supported securities / risk-set securities)

winner_recall_lift_vs_breadth
= winner_recall / selection_breadth
```

This is a descriptive historical diagnostic, not a new acceptance threshold for AOV.

---

## 8. Regime split

Use the exact AOV slow-trend breadth semantics from `research/aov0/ciq_market.py`:

```text
sma200(i,t) = 200-observed-session rolling mean(close)
trend_slow(i,t) = +1 if close >= sma200 else -1
regime(t) = date-local mean(trend_slow)
```

Provider query-grid NA placeholders and holidays are **not** counted as observed sessions. Each security rolls on its own observed close rows, matching the source feature builder.

Terminal securities are removed from the active trend breadth from their source-authorized effective date onward.

Frozen descriptive buckets require no fitted thresholds:

```text
POSITIVE_BREADTH if regime > 0
NEUTRAL_BREADTH  if regime = 0
NEGATIVE_BREADTH if regime < 0
UNAVAILABLE      if no valid regime exists
```

The same funnel aggregation is emitted for each observed bucket.

---

## 9. Whole-stage Parent/Child attribution

Horizon episodes overlap, so they are not used to reconcile the realized Parent/Child stage gap.

The whole-stage attribution is non-overlapping daily P&L:

```text
gap_contribution_i
= sum_t ((Parent_executed_weight_{t,i} - Child_executed_weight_{t,i}) * r_{t,i})

Parent_minus_Child_gross_gap
= sum_i gap_contribution_i
```

This must reconcile to the retained stage report's:

```text
Parent gross_return_sum - Child gross_return_sum
```

within absolute tolerance `1e-12`.

The five largest realized stage winners are selected by full-stage compounded security total return using the same deterministic top-5% law. Their contribution-gap share is reported separately from the generic top gap contributors.

---

## 10. Smoke probes

Smoke symbols are generic CLI inputs. The algorithm contains no `SNDK` or `MU` branch.

For each requested symbol, the report checks exact membership in:

```text
retained Lane-2 source cohort
current checked CIQ primary master
```

and may attach older retained eligibility diagnostics if a matching generic trace exists.

Smoke probes have:

```text
acceptance_weight = 0
special_case_code_authorized = false
```

Their role is to force deterministic explanations, not to redefine the research denominator or family pass/fail law.

---

## 11. Current retained-byte reproduction

The implemented diagnostic reproduces the focused-pivot facts from the retained bytes:

```text
A1 10d winner recall = 26.6667%
A1 10d mean breadth  = 23.5028%
A1 20d winner recall = 28.4615%
A1 20d mean breadth  = 23.7316%

A2 10d winner recall = 26.6667%
A2 10d mean breadth  = 20.3901%
A2 20d winner recall = 20.0000%
A2 20d mean breadth  = 19.1489%
```

For A2:

```text
Parent - Child gross gap = 1.373092 percentage points
Child cost savings vs Parent = 0.048211 percentage points
```

The five largest full-A2 realized winners are:

```text
OPHC
SMTI
CSTL
NTRA
TLSI
```

Parent had exposure to OPHC, SMTI, and NTRA; it never had exposure to CSTL or TLSI. The five winners' Parent-minus-Child contribution deltas explain `92.5781%` of the A2 gross gap.

These are historical diagnostic facts, not financial-Alpha promotion evidence.

---

## 12. Implementation / evidence paths

```text
research/aov0/winner_capture.py
scripts/aov0_winner_capture_diagnostic.py
tests/aov0/test_winner_capture_diagnostic.py
docs/context/e2e_evidence/winner_capture_diagnostic_v0_20260810.json
```

The evidence artifact records source hashes, arm hashes, report hashes, A2 query-count invariants, smoke-probe status, regime splits, and `financial_alpha_evidence=0`.
