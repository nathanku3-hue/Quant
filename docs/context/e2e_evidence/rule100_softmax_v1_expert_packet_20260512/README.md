# Rule100 Softmax v1 Expert Review Packet

Date: 2026-05-12
Project: Terminal Zero (T0), local-first quantitative research console
Scope: Rule of 100 lifecycle replay sizing, softmax v1 audit baseline, and v1.1 strategy decision prep

## Packet Contents

```text
portfolio_lifecycle_buy_sell_log.jsonl
portfolio_lifecycle_decision_log.jsonl
rule100_softmax_v1_history.csv
rule100_softmax_v1_comparison.csv
rule100_softmax_v1_summary.json
README.md
EXPERT_PROMPT.md
```

## Key Context

The lifecycle event ledgers are intentionally immutable audit records. They show the weight attached to BUY/ENTER and SELL/EXIT events under the current Rule100 lifecycle replay policy. Those event weights are not the same thing as the active target-weight history for a sizing policy.

The softmax v1 artifacts are derived replay/audit outputs. They preserve event weights while adding daily target weights, cash residuals, score inputs, and eligibility reasons.

Current finding:

```text
On 2026-05-11:
AMAT event_weight = 10%, softmax_v1_target_weight = 10%
LRCX event_weight = 10%, softmax_v1_target_weight = 10%
TSM  event_weight = 10%, softmax_v1_target_weight = 0%
CASH under softmax v1 = 80%
```

BUY rows still show 10% because v1 is an ordinal formula and all eligible BUY rows currently tie:

```text
factor_positive_count = 3
technical_quality = 1.0
score = 0.25
budget = 0.10 * eligible_count
```

## Data Dictionary

```text
event_weight
  Immutable lifecycle event/fill weight from the v0/v1 event ledger.

event_target_weight
  Target weight recorded by the lifecycle decision tape at event time.

softmax_v1_target_weight
  Derived daily Rule100 softmax v1 policy target weight.

softmax_v1_cash_residual
  Residual cash after applying v1 target weights.

softmax_v1_gross_weight
  Sum of non-cash v1 target weights for that date.

sizing_eligible
  Whether the name is eligible for v1 target sizing on that PIT date.

eligibility_reason
  Human-readable reason such as eligible_buy_or_hold, tighten_below_hold_threshold, flat_after_sell, or exit_or_trend_veto_block.

score
  Rule100 softmax v1 score used by the sizing helper.
```

## Current Decision State

```text
v1 = frozen ordinal softmax audit baseline.
v1.1 = proposed continuous-input differentiated sizing path.
Kelly = thin comparator only, not a primary sizing stack.
```

The main question for expert review is not whether softmax math is broken. The current v1 output is equal for eligible BUY rows because the inputs are tied. The question is whether v1.1 should introduce PIT-safe continuous factor and technical inputs, and what promotion evidence should be required.
