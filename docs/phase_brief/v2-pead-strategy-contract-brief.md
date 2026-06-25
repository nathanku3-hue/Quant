# V2 PEAD Strategy Contract Brief

Status: Strategy skeleton handoff-ready after Reviewer A/B/C rerun; real research evidence blocked
Date: 2026-06-18
RoundID: `ROUND-20260618-V2-PEAD-STRATEGY-CONTRACT`
ScopeID: `V2_PEAD_STRATEGY_SCHEMA_EVENT_WINDOW_STATS`
PromotionGateRoundID: `ROUND-20260618-V2-PEAD-STRATEGY-CONTRACT-SAW-RERUN`
PromotionGateScopeID: `V2_PEAD_STRATEGY_SAW_RERUN_PROMOTION_GATE`
Owner: Quant Strategy

## Objective

Ship the data-source-agnostic PEAD strategy contract so the Data stream can later hand off corrected D1/D2 rows without requiring strategy rework.

## Delivered scope

- Required event schema: `event_id, issuer_id, security_id, event_date, sue, is_primary_security`.
- Required return schema: `security_id, date, total_return`; an explicit benchmark column is optional.
- Strict event timing: day `+1` is the first explicit market session strictly after `event_date`; the default horizon is `+1..+60`.
- Complete-window gating: missing sessions, asset returns, or configured benchmark returns make the event ineligible.
- Separate outcome semantics: compounded total return is always available for complete raw windows; `CAR` and `BHAR` exist only when a benchmark column is explicitly configured.
- Cohort-local SUE quantiles, cohort high-minus-low spreads, and HAC/Newey-West inference.
- Pure in-memory fixture coverage; no provider, Parquet, manifest, builder, UI, or research-result write.
- Independent Reviewer A/B/C rerun PASS with no in-scope Critical/High findings; strategy is handoff-ready for corrected D1/D2 inputs only.

## Acceptance criteria

- [x] Event date is excluded from the return window.
- [x] Default complete horizon requires exactly 60 future trading observations.
- [x] Duplicate event IDs, duplicate security-date returns, infinite returns, and returns below `-100%` fail closed.
- [x] Incomplete windows remain visible and are excluded from analysis.
- [x] Raw cumulative return cannot be mislabeled as benchmark-adjusted CAR.
- [x] Quantiles are assigned only inside sufficiently large event-date cohorts.
- [x] High-minus-low inference uses cohort-level spreads with HAC covariance.
- [x] Focused synthetic tests pass.
- [x] Independent Reviewer A/B/C rerun passes after reconciliation.
- [ ] Corrected D1 SUE handoff accepted from Data stream.
- [ ] Corrected D2 total-return/primary-security handoff accepted from Data stream.
- [ ] Real benchmark, delisting policy, and full `+60` coverage accepted.
- [ ] Real quintile/CAR/backtest interpreted. BLOCKED.

## Boundary

This round does not modify or approve `data/`, `scripts/pead_d1_sue_builder.py`, `scripts/pead_d2_iid_primary_contract.py`, `scripts/pead_d2_return_contract.py`, any Parquet/manifest, provider access, candidate ranking, promotion, alerts, broker paths, or UI. Passing synthetic strategy tests is not evidence of alpha.

## Rollback

Remove `strategies/pead_event_study.py`, `tests/test_pead_event_study.py`, and this strategy-contract documentation. No data artifact rollback is required because this round performs no data writes.
