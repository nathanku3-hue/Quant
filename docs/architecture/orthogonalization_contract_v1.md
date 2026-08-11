# OrthogonalizationContractV1 — AO-K0A Denominator Alignment / Orthogonal Basis Preflight

**Date:** 2026-08-11
**Status:** `FROZEN_SOURCE_PREFLIGHT / NO_EMPIRICAL_RESULT`
**Supersedes for the active AO basis:** complete-case coverage gates, `AO_BASIS_US_PRIMARY_COMMON_DATE_LOCAL_V1` as a separate denominator identity, and the prior raw `Q × M` composition geometry.
**Does not supersede:** historical AO-K0 receipts, W3 PIT authority, S0 custody, W6 lockbox, trial debt, or capital authority.

## 1. Constitutional rule

> **ABSTENTION is not missing data to be repaired; it is an economically costly action: zero risky exposure, full-universe missed-winner accountability, residual capital in economic cash, and no denominator relief.**

Missingness is therefore a persistent state inside the full W3 opportunity space. It is not a coverage `PASS/FAIL` gate and it never rewrites eligibility.

## 2. Immutable denominator

The only denominator authority is:

```text
PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1
```

The basis preflight must left-preserve every date-local W3 eligible `(security_id, trading_item_id)` row. No feature availability, missing history, cohort size, or observed-subset convenience may delete a W3 row.

The immutable W3 authority manifest contains 346 sessions with mean eligible count `4822.994219653179` (min `4561`, max `5260`). This reproduces the approximately 4,823-name W3 universe directly from W3 authority, not from feature/test artifacts.

## 3. Allowed observability sources

AO-K0A may derive observability boundaries only from:

1. immutable W3 date-local authority;
2. the admitted ECONPHYSICS S0 source corpus and its exact admission/quarantine law;
3. exact W3 market custody for the same date-local security/listing identity.

Forbidden boundary sources include historical test outputs, transient feature stores, `test_assemble_features_*`, execution-microstructure test fragments, assembled factor parquet files, current-survivor projections, alternate-listing bridges, ticker/entity/PERMNO fallbacks, and any outcome-bearing surface.

### Q source observability / no-bridge law

AO-K0A does **not** borrow the old Rule100 assembled `z_demand`, `z_inventory_quality_proxy`, `z_moat`, or `capital_cycle_score` artifacts to determine coverage. The admitted S0 corpus contains a different primitive set and cannot reproduce those old features exactly without inventing missing inputs.

For the source preflight only, Q source observability is therefore defined mechanically:

- find the latest **planned** S0 fundamental transition at or before the decision date;
- it is Q-source-observed only if that transition was admitted by the existing S0 admission law;
- a quarantined/missing planned transition flips the source state to unobserved;
- the prior state may not bridge across that missing transition;
- a later admitted transition may restore source observability.

This is a source-availability state, **not a newly invented numeric Q kernel**. AO-K0A does not rederive a numeric Q score and does not read legacy feature artifacts to do so.

### M observability / no-bridge law

`M` requires the exact current W3 `(security_id, trading_item_id)` to have 60 continuous observed W3 sessions with finite `SP_TOTAL_RETURN` in exact W3 market custody.

- fewer than 60 global W3 sessions available: `M_WARMUP`;
- 60 sessions exist but exact-listing history is incomplete: `M_MISSING_HISTORY`;
- no alternate listing, identity fallback, missing-return fill, or observed-subset bridge is allowed.

## 4. Immutable `basis_status`

Every W3 row maps to exactly one status:

```text
ELIGIBLE_COMPLETE
Q_UNOBSERVED
M_WARMUP
M_MISSING_HISTORY
Q_AND_M_MISSING
```

Precedence is deterministic:

```text
Q missing AND M not observed -> Q_AND_M_MISSING
Q missing AND M observed     -> Q_UNOBSERVED
Q observed AND M warmup      -> M_WARMUP
Q observed AND M missing     -> M_MISSING_HISTORY
Q observed AND M observed    -> ELIGIBLE_COMPLETE
```

For every status other than `ELIGIBLE_COMPLETE` in the joint arms:

```text
forecast     = ABSTAIN
selected     = FALSE
risky_weight = 0
```

There is no coverage threshold and no status maps to `PASS` or `FAIL`.

## 5. Rank denominator law

### Q arm

For each decision date, standard percentile rank is computed over **all Q-observed W3 names**:

```text
rank_Q_arm = average-tie rank(Q) / N_Q_observed
```

The Q arm is not artificially intersected down to Q∩M. Q observability is part of deployable system economics.

### Joint residualization sample

For `M_perp` and `Q + M_perp`, first take the exact Q∩M-observed W3 sample and recompute both ranks on that same sample:

```text
rank_Q_joint = rank(Q | Q&M observed)
rank_M_joint = rank(M | Q&M observed)
```

It is forbidden to regress an all-Q percentile rank against an intersection-only M rank.

## 6. Orthogonal projection

Within each decision date only:

```text
rank_M_joint = a_t + b_t * rank_Q_joint + epsilon_t
M_perp       = epsilon_t
```

OLS contains an intercept, has no temporal fit, consumes no outcome, and exports no learned parameter across dates. Numerical residual orthogonality to the intercept and `rank_Q_joint` is a projection invariant, not a coverage admission tolerance.

## 7. Arm observability

```text
Q arm:
  Q observed -> selectable
  otherwise  -> ABSTENTION

M_perp arm:
  Q AND M observed -> selectable
  otherwise        -> ABSTENTION

Q + M_perp arm:
  Q AND M observed -> selectable
  otherwise        -> ABSTENTION
```

AO-K0A freezes the orthogonal basis and arm observability. It does **not** invent an unapproved scalar weighting/combination rule for `Q + M_perp`; any result-bearing composition multi-arm evaluation is gated by **OK-SBI-0** (shadow) after numeric Q source-binding — not by an automatic legacy AO-K0B trophy open.

## 8. Full-W3 evaluation law

### Right-tail recall

After development outcomes are lawfully opened in a separately authorized result-bearing slice:

```text
Recall_t = #(selected ∩ winner) / #(winner in matured full W3)
```

Winners inside `ABSTENTION` remain in the denominator and are missed opportunities.

### Breadth

```text
Breadth_t = N_selected,t / N_W3,t
```

`N_complete,t` is forbidden as the breadth denominator.

### Opportunity-cost diagnostics

Diagnostics are outcome-side accounting only and may not feed Q/M:

```text
ForegoneUpside_t
  = #(ABSTENTION ∩ right-tail) / #(right-tail in full W3)

AvoidedCatastrophe_t
  = #(ABSTENTION ∩ bottom-tail) / #(bottom-tail in full W3)
```

The report must also compare COMPLETE vs ABSTENTION realized-return distributions (median, P10, P5, P1, top-5% incidence, bottom-5% incidence) after outcomes are lawfully opened.

### Downside

Selected-name catastrophic false rate remains selected-name burden:

```text
CatFalseRate
  = #(selected nonwinner ∩ bottom-tail) / #(selected nonwinner)
```

Full-W3 catastrophic capture must also be reported:

```text
CatCapture
  = #(selected ∩ bottom-tail) / #(bottom-tail in full W3)
```

ABSTENTION bottom-tail is `avoided_catastrophe_by_abstention`; ABSTENTION right-tail is `foregone_right_tail_by_abstention`.

## 9. Capital semantics

There is no security-level return imputation for Q/M-missing names.

```text
ABSTENTION risky weight = 0
residual capital         = economic cash
opportunity benchmark    = PIT equal-weight full W3
```

Canonical builders remain:

```text
research.benchmarks.build_economic_cash_frames
research.benchmarks.build_pit_equal_weight_benchmark
```

Economic cash answers where unallocated capital actually sits. PIT equal-weight full W3 answers the opportunity-universe cost of abstention. They are separate comparators and cannot substitute for each other.

## 10. Explicitly forbidden

```text
security_level_return_imputation = FORBIDDEN
peer_return_imputation           = FORBIDDEN
complete_case_denominator        = FORBIDDEN
observed_subset_renormalization  = FORBIDDEN
coverage_pass_fail_gate          = FORBIDDEN
feature_store_boundary_inference = FORBIDDEN
alternate_listing_history_bridge = FORBIDDEN
outcome_input_to_basis           = FORBIDDEN
```

## 11. Source-preflight receipt

The read-only source preflight deterministically generated the pre-W6 weekly matrix in memory and content-addressed it without creating a transient feature store:

```text
pre-W6 W3 sessions              = 306
weekly decision dates           = 64
matrix rows                     = 310,329
matrix SHA-256                  = bd36a6305f38ff68c57f6ccfb9d3481be6fd42d2288128ef9ec3eb3cc12df5cf
rows removed for missingness    = 0
W6 dates consumed               = 0
winner/future outcome reads     = 0
new provider requests           = 0
```

Source-observability status counts:

```text
ELIGIBLE_COMPLETE   223,367
M_MISSING_HISTORY    17,767
M_WARMUP             30,270
Q_AND_M_MISSING      36,068
Q_UNOBSERVED          2,857
```

Post-M-warmup source-complete rate is `0.8973228991748552`. This number is **not an Alpha result** and is **not a coverage gate**.

### Reconciliation of the previously stated ~79.49%

The ~79.49% common-coverage figure is not recertified by AO-K0A because the allowed first-principles source set does not uniquely reproduce the prior numeric-Q observability law. AO-K0A therefore does not tune an observability definition until it reproduces 79.49%, and it does not import old feature artifacts to preserve that number. The figure may remain historical context, but it is not an active denominator authority or PASS/FAIL threshold.

## 12. AO-K0A stop line

AO-K0A stops before:

```text
opening any new winner/future outcome
running empirical Q / M_perp / Q+M_perp results
W6
new provider requests
K tuning
Dislocation experiment
peer valuation acquisition
portfolio optimization
capital promotion
```

### Downstream naming (docs delta 2026-08-12; does not reopen this contract)

```text
AO-K0A (this contract)     = frozen prerequisite; no empirical result
OK-SBI-0                   = active research shadow at S0 (pre-open only)
AO-K0B                     = legacy blocked next-slice pointer; must not run as automatic trophy
AO-K0B-D                   = development stage inside OK-SBI-0 only after QSource + gates + hashes + carve-out
```

**Q is not a deployable numeric factor until `QSourceContractV1.status ∈ {Q_GF_BOUND, Q_AMENDED_BOUND}`** (`docs/architecture/q_source_contract_v1.md`). This contract freezes Q **source-observability / basis-status** only — not a numeric Q kernel and not Rule100 feature-store borrow.

Result-bearing sparse-basis work is **not** authorized by default as a `Q / M_perp / Q+M_perp` leaderboard. Any later evaluation must respect OK-SBI-0 science order (missingness → raw Q×M joint law → Residual-M novelty → deployability), dual clocks, multi-arm probes (including raw additive and conjunction arms), and ledger-tagged claims — and requires an explicit one-shot stop-line carve-out. Until then: `runnable_evaluation=false`, `OUTCOME_OPEN=NO`, `financial_alpha_evidence=0`.
