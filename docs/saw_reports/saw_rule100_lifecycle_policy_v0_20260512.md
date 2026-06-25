# SAW Report - Rule100 Lifecycle Policy v0

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend/Strategy, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: PH65_RULE100_LIFECYCLE_POLICY_V0_20260512
ScopeID: PH65_RULE100_LIFECYCLE_POLICY_V0

## Scope

Promote the concrete lifecycle replay strategy to Rule100 Lifecycle Policy v0 without introducing a generic strategy replay framework.

## Acceptance Checks

| Check | Result | Evidence |
|---|---|---|
| CHK-01 Rule100State adapter exposes demand/supply/pricing/margin with proxy provenance | PASS | `scripts/pit_lifecycle_replay.py`; `tests/test_pinned_universe.py` |
| CHK-02 BUY requires 3/4 factors, technical entry zone, 3-day confirmation, and no cooldown | PASS | focused replay tests and v0 replay artifact |
| CHK-03 HOLD tolerates 2/4 factors while TIGHTEN logs <2/4 factor deterioration | PASS | v0 decision audit: HOLD=739, TIGHTEN=257 |
| CHK-04 TRIM logs 12%-20% stretch without changing v0 weights | PASS | v0 decision audit: TRIM=55 |
| CHK-05 EXIT requires hard stop >20% or confirmed trend veto | PASS | focused exit-guard tests and v0 buy/sell tape |
| CHK-06 Entry sizing uses conviction formula capped at 15% | PASS | `rule100_target_weight(...)`; tests cover 3/4=10% and 4/4=12.5% |
| CHK-07 Delta comparison vs 33-event baseline is published | PASS | `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json` |
| CHK-08 Full regression and runtime HTTP smoke pass | PASS | `.venv\Scripts\python -m pytest -q`; `http://127.0.0.1:8509/portfolio-and-allocation` HTTP 200 |
| CHK-09 Independent SAW Implementer and Reviewer A/B/C ownership | FAIL | Not run because current tool policy requires explicit user authorization to spawn subagents |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Governance closure cannot claim independent SAW review ownership. | Keep SAW verdict BLOCK until explicit subagent/reviewer authorization exists. | Docs/Ops | Open |
| Medium | No 4/4 entry rows appear in the current data window, so conviction sizing does not yet change promoted weights. | Formula and tests are in place; carry as data-observed limitation, not implementation defect. | Strategy | Carried |
| Low | TRIM/TIGHTEN are audit-only and do not yet affect allocation weights. | Carry to next decision after v0 audit. | Strategy/Product | Carried |

## Scope Split Summary

In-scope findings/actions:

- Implemented Rule100State proxy adapter.
- Promoted v0 runtime replay to `data/portfolio_lifecycle_log.jsonl`.
- Regenerated decision and buy/sell tapes.
- Published delta vs the 33-event baseline.
- Kept generic replay framework out of scope.

Inherited out-of-scope findings/actions:

- Literal Rule-of-100 feature-store columns remain future work.
- TRIM/TIGHTEN weight application remains future v1 policy.
- Full execution ledger with fills, quantities, cost basis, realized P&L, slippage, and tax lots remains future work.

Open Risks:

- Independent SAW subagent Implementer and Reviewer A/B/C passes are pending.
- Literal Rule-of-100 columns are absent; v0 uses explicit proxy provenance.
- TRIM/TIGHTEN are audit-only and may need v1 allocation semantics after review.

Next action:

- Audit the Rule100 v0 delta and decide whether TRIM/TIGHTEN should stay audit-only or become weight-changing v1 actions.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `scripts/pit_lifecycle_replay.py` | Added Rule100State, conviction sizing, v0 lifecycle actions, hard-stop/confirmed-veto exits, and baseline comparison. | Local reviewed |
| `tests/test_pinned_universe.py` | Added Rule100 provenance, sizing, exit-guard, and export/replay equivalence coverage. | Local reviewed |
| `data/portfolio_lifecycle_log.jsonl` | Promoted v0 runtime replay: 29 events, open AMAT/LRCX/TSM. | Local reviewed |
| `data/portfolio_lifecycle_decision_log.jsonl`, `data/portfolio_lifecycle_buy_sell_log.jsonl` | Regenerated v0 decision and buy/sell tapes. | Local reviewed |
| `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json` | Published v0 delta audit. | Local reviewed |
| `docs/notes.md`, `docs/decision log.md`, `docs/phase_brief/phase65-brief.md`, `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md` | Documented v0 formulas, boundaries, and evidence. | Local reviewed |
| `docs/context/*_current.md` | Refreshed current truth surfaces for v0. | Local reviewed |
| `docs/lessonss.md` | Added abstraction-timing guardrail. | Local reviewed |

## Document Sorting

Document-change visibility is kept in current-context order: implementation, tests, data artifacts, evidence artifacts, notes, decision log, phase brief, product/spec surfaces, context truth surfaces, lessons, SAW report.

## Closure Packet

ChecksTotal: 9
ChecksPassed: 8
ChecksFailed: 1

ClosurePacket: RoundID=PH65_RULE100_LIFECYCLE_POLICY_V0_20260512; ScopeID=PH65_RULE100_LIFECYCLE_POLICY_V0; ChecksTotal=9; ChecksPassed=8; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent_saw_subagent_review_pending_literal_rule100_columns_absent_trim_tighten_audit_only; NextAction=audit_rule100_v0_delta_then_decide_trim_tighten_weight_policy

ClosureValidation: PASS
SAWBlockValidation: PASS
