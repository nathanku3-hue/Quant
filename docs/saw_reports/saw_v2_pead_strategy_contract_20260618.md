# SAW Report — V2 PEAD Strategy Contract

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Quant Strategy, Financial Statistics, Python Testing

RoundID: `ROUND-20260618-V2-PEAD-STRATEGY-CONTRACT`
ScopeID: `V2_PEAD_STRATEGY_SCHEMA_EVENT_WINDOW_STATS`

## Scope and Ownership

Work round scope: implement a strategy-layer-only PEAD schema/event-window/statistics contract without touching Data-stream builders or artifacts.

Owned files changed in this round:

- `strategies/pead_event_study.py`
- `tests/test_pead_event_study.py`
- `docs/phase_brief/v2-pead-strategy-contract-brief.md`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/saw_reports/saw_v2_pead_strategy_contract_20260618.md`
- `docs/context/*_current.md` and `docs/context/current_context.*` after context refresh

Acceptance checks:

- `CHK-01`: Schema requires issuer/security/event/SUE plus upstream primary-security boolean handoff.
- `CHK-02`: Event windows use explicit market sessions, not per-security observation compression.
- `CHK-03`: Raw cumulative return, CAR, and BHAR formulas are separated and benchmark-gated.
- `CHK-04`: Cohort SUE bucketing is separated from outcome eligibility; HAC gaps fail closed.
- `CHK-05`: Synthetic fixture tests cover reviewer counterexamples.
- `CHK-06`: Docs-as-code records formulas, boundaries, and blocked Data-stream handoffs.
- `CHK-07`: Independent Reviewer A/B/C rerun completes after reconciliation.

## Subagent Passes

Implementer pass: parent agent implemented and reconciled Reviewer A/B/C first-pass findings.

Reviewer A pass: initial read-only pass found event-time compression, non-PIT/ex-post cohort risk, malformed boolean truthiness, and HAC gap compression. Parent added market-session grid, strict booleans, daily-default cohorts with ex-post opt-in, separated signal buckets from outcomes, and HAC gap fail-closed tests. Rerun unavailable due tool quota.

Reviewer B pass: initial read-only pass found malformed boolean truthiness, date normalization drift, benchmark-name collision, and config coercion. Parent added strict boolean/date/config validation and reserved-name tests. Rerun unavailable due tool quota.

Reviewer C pass: initial read-only pass found missing session compression, delisting/coverage bias risk, primary-security handoff weakness, malformed external skeleton acceptance, and unbounded large-sample expansion. Parent added explicit market sessions, issuer/primary metadata, exact skeleton validation, coverage reasons, and a bounded summary path. Rerun returned no usable reviewer content.

Ownership check: Implementer and reviewers were different agents in first-pass SAW. Second-pass reviewer rerun did not complete because the multi-agent tool returned usage-limit errors/null output.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Per-security row compression could mislabel event days. | Replaced event-day basis with explicit `market_sessions` and exact session offset joins. | Implementer | Fixed by tests |
| High | Malformed `window_complete` could fail open. | Added strict boolean validation and malformed schema regression. | Implementer | Fixed by tests |
| High | Numeric/timezone dates could silently shift anchors. | Rejected numeric epoch-like dates and timezone-bearing date inputs. | Implementer | Fixed by tests |
| High | Outcome availability could affect SUE bucket membership. | Split `signal_bucket_eligible` from `quantile_eligible`. | Implementer | Fixed by tests |
| High | Primary security handoff was implicit. | Required `issuer_id` and `is_primary_security=True`; uniqueness is issuer-date. | Implementer | Fixed by tests |
| Medium | HAC could compress missing cohort periods. | Reindexed cohort spreads to full PeriodIndex and set HAC t-stat unavailable on gaps. | Implementer | Fixed by tests |
| Medium | Large samples could retain all windows. | Added `summarize_event_outcomes_from_inputs(..., batch_size=...)` summary-first path. | Implementer | Fixed by source review |
| High | Independent reviewer rerun did not complete. | Stop short of PASS; require reviewer rerun after quota resets. | Owner: PM/next worker | Open |

## Scope Split Summary

in-scope findings/actions:

- Strategy schema/window/statistics contract and synthetic tests were implemented.
- Reviewer counterexamples were converted into fixture tests.
- Docs-as-code records formula semantics and Data-stream boundaries.

inherited out-of-scope findings/actions:

- D1 SUE adjustment-basis correction remains Data stream owned.
- D2 total-return level, primary-IID construction, delisting policy, benchmark integration, and real artifact builds remain Data stream owned.
- Real quintile/CAR/backtest interpretation remains blocked until corrected Data-stream handoff passes.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `strategies/pead_event_study.py` | Added strategy-only event schema, market-session windows, outcomes, quantiles, HAC stats, and batch summary path. | First-pass findings reconciled; rerun blocked |
| `tests/test_pead_event_study.py` | Added 13 synthetic tests covering formulas, market-session gaps, strict schema/date/config validation, bucket/outcome separation, and HAC gaps. | First-pass findings reconciled; rerun blocked |
| `docs/phase_brief/v2-pead-strategy-contract-brief.md` | Added live brief and acceptance/boundary state. | Docs check PASS |
| `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md` | Added PEAD strategy-contract product/spec notices. | Docs check PASS |
| `docs/notes.md` | Added formula registry and source paths. | Docs check PASS |
| `docs/decision log.md` | Added strategy-contract decision and boundary lock. | Docs check PASS |
| `docs/lessonss.md` | Added self-learning guardrail entry. | Docs check PASS |

## Validation Evidence

- `.\.venv\Scripts\python -m pytest tests\test_pead_event_study.py -q` -> PASS, 13 passed.
- `.\.venv\Scripts\python -m pytest tests\test_pead_event_study.py tests\test_statistics.py -q` -> PASS, 19 passed.
- `.\.venv\Scripts\python -m pytest tests\test_pead_event_study.py tests\test_statistics.py tests\test_phase56_pead_runner.py -q` -> PASS, 23 passed.
- `.\.venv\Scripts\python -m py_compile strategies\pead_event_study.py tests\test_pead_event_study.py` -> PASS.
- `git diff --check -- <owned files>` -> PASS with CRLF warnings only.

Open Risks: independent_reviewer_rerun_unavailable_due_quota; Data-stream D1/D2 corrections still blocked outside this scope; real alpha interpretation remains blocked.

Next action: rerun_SAW_reviewers_A_B_C_after_quota_then_promote_if_no_high_findings

ClosurePacket: RoundID=ROUND-20260618-V2-PEAD-STRATEGY-CONTRACT; ScopeID=V2_PEAD_STRATEGY_SCHEMA_EVENT_WINDOW_STATS; ChecksTotal=7; ChecksPassed=6; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent_reviewer_rerun_unavailable_due_quota; NextAction=rerun_SAW_reviewers_A_B_C_after_quota_then_promote_if_no_high_findings

ClosureValidation: PASS

SAWBlockValidation: PASS
