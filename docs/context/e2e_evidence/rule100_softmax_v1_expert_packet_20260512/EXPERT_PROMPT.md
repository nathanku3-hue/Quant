# Expert Review Prompt: Rule100 Softmax v1 / v1.1 Sizing

You are reviewing a local-first quantitative research console called Terminal Zero (T0). The relevant system is a Streamlit + Python + DuckDB/Pandas/Parquet research app. The portfolio lifecycle replay is point-in-time (PIT) and must avoid look-ahead bias. No broker actions, alerts, live trading, provider ingestion, or production promotion are authorized by this review.

## Project Background

T0 has a Portfolio & Allocation workflow that reconstructs lifecycle holdings from a PIT replay. The current lifecycle policy is called Rule100 Lifecycle Policy v0. It uses a state machine over a pinned thesis universe and local feature-store data.

The lifecycle replay currently distinguishes these concepts:

```text
Event/fill ledger:
  Append-only ENTER/EXIT style audit record used by the dashboard lifecycle replay.

Decision tape:
  Daily PIT audit record with BUY, SELL, HOLD, TRIM, TIGHTEN, EXIT, and NO_ACTION states.

Target-weight history:
  Derived sizing-policy output for each PIT date/ticker, separate from the event ledger.
```

Earlier behavior showed every lifecycle BUY/ENTER at 10%. That was not necessarily a softmax failure. The original lifecycle event ledger used a fixed Rule100 v0 entry weight, and the UI chart was still surfacing the event weight as the replay weight. A separate softmax v1 target-weight artifact was then added so reviewers can compare immutable event weights against derived policy targets.

## Current Rule100 Lifecycle Policy

The current replay policy:

```text
BUY/ENTER:
  Requires PIT entry gate, at least 3-of-4 lifecycle factor confirmation, technical entry zone, and multi-day confirmation.

HOLD:
  Allows held names to remain held when thesis state is still intact.

TRIM/TIGHTEN:
  Audit-only in v1. They do not yet execute partial reweights.

EXIT/SELL:
  Full exit only on hard stop or confirmed trend veto.

Sizing:
  v0 event entries are generally 10%, capped at 15% in principle.
```

Current open lifecycle holds are AMAT, LRCX, and TSM in the event ledger, but softmax v1 marks TSM as not sizing-eligible in the current daily target history.

## Softmax v1 Rule Under Review

Softmax v1 is the recommended primary sizing baseline. Kelly remains only a thin ablation/comparator on the same harness.

Current v1 formula:

```text
score_i = 0.75 * (factor_positive_count_i - 3) + 0.25 * technical_quality_i

budget_t = min(1.0, 0.10 * eligible_count_t)

raw_weight_i = budget_t * softmax(score_i / tau)
tau = 1.0
single_name_cap = 15%
cash = 1.0 - sum(final_target_weights)
```

This v1 formula is intentionally ordinal and auditable. It does not pretend that a 3/4 or 4/4 confirmation is a calibrated return probability.

Current observed issue:

```text
All eligible BUY rows currently have:
factor_positive_count = 3
technical_quality = 1.0
score = 0.25

Therefore equal scores plus budget = 0.10 * eligible_count produce 10% per eligible BUY row.
```

Current state on 2026-05-11:

```text
AMAT event_weight = 10%, softmax_v1_target_weight = 10%
LRCX event_weight = 10%, softmax_v1_target_weight = 10%
TSM  event_weight = 10%, softmax_v1_target_weight = 0%
softmax_v1_cash_residual = 80%
```

## Proposed Direction

The project preference is:

```text
Freeze v1 as the ordinal audit baseline.
Create v1.1 for differentiated sizing using richer PIT-safe continuous inputs.
Do not silently mutate v1 behavior.
Keep Kelly comparator-only.
```

Candidate v1.1 score direction:

```text
score_i =
    0.45 * factor_strength_continuous_i
  + 0.25 * technical_quality_continuous_i
  + 0.15 * hold_intact_i
  - 0.10 * age_penalty_i
  - 0.20 * trim_penalty_i
```

The coefficients above are starting priors only, not final approvals.

## Artifacts To Inspect

```text
portfolio_lifecycle_buy_sell_log.jsonl
  Compact event-level BUY/SELL view. Expected to show 10% event weights.

portfolio_lifecycle_decision_log.jsonl
  Full PIT daily decision tape with lifecycle actions and factor/technical state.

rule100_softmax_v1_history.csv
  Derived daily softmax v1 target-weight history. Use this to inspect target weights, cash, and eligibility.

rule100_softmax_v1_comparison.csv
  Current softmax vs thin Kelly comparator output on the shared harness.

rule100_softmax_v1_summary.json
  Summary metadata and artifact paths from the audit run.
```

## Questions For Expert Review

1. Is it correct to keep the event/fill ledger immutable and treat softmax v1 target history as a separate derived audit artifact?

2. Should the dashboard/replay chart display softmax target weight as the primary policy weight while keeping event_weight visible as audit-only context?

3. Is the current v1 ordinal formula acceptable as a frozen audit baseline, even though tied inputs produce 10% per eligible BUY?

4. Should v1.1 introduce continuous PIT-safe factor and technical inputs for visible differentiated sizing?

5. What is the preferred definition of factor_strength_continuous?
   Options may include clipped z-score, percentile/rank, averaged normalized proxy values, or another PIT-safe transform.

6. What is the preferred definition of technical_quality_continuous?
   Options may include normalized moving-average proximity, trend slope strength, drawdown/stretch bands, or another PIT-safe transform.

7. Should age_penalty be included at all?
   Concern: a simple age penalty may wrongly punish durable winners unless it proxies thesis staleness or mean-reversion risk.

8. Should TRIM and TIGHTEN remain audit-only in v1, or become partial target-weight reductions in v1.1?

9. Should the gross budget remain min(1.0, 0.10 * eligible_count), or should v1.1 change only the score while leaving the budget unchanged?

10. What promotion evidence should v1.1 require versus v1?
    Suggested evidence: turnover, concentration, cash drag, max drawdown, YTD/period return, lifecycle hit-rate, and same-window replay metrics.

## Requested Output

Please return:

```text
Recommendation:
  Keep v1 frozen / modify v1 / promote v1.1 / reject v1.1

Rationale:
  Brief explanation grounded in the artifacts.

Data Contract Decision:
  Whether event_weight and target_weight should remain separate.

v1.1 Input Decision:
  Approved continuous inputs and definitions, or what is missing before approval.

Coefficient Guidance:
  Whether the starting coefficients are acceptable, should be changed, or need calibration.

Evidence Gate:
  Required metrics and minimum comparison protocol before v1.1 promotion.

Risks:
  PIT leakage risks, overfitting risks, auditability risks, or UI interpretation risks.
```
