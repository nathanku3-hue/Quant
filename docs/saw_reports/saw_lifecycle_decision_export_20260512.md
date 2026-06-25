# SAW Report - Lifecycle Decision Export

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend/Strategy, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: PH65_LIFECYCLE_DECISION_EXPORT_20260512
ScopeID: PH65_LIFECYCLE_DECISION_EXPORT

## Scope

Export an enriched PIT-safe lifecycle decision tape with buy/sell labels and reasons before implementing the true Rule-of-100 lifecycle policy.

## Acceptance Checks

| Check | Result | Evidence |
|---|---|---|
| CHK-01 Export-only mode does not append duplicate lifecycle ENTER/EXIT events | PASS | `scripts/pit_lifecycle_replay.py --export-only` |
| CHK-02 Full decision tape includes BUY/SELL/HOLD/NO_ACTION, reasons, gates, streaks, hold days, cooldown, and Rule-of-100 proxy fields | PASS | `data/portfolio_lifecycle_decision_log.jsonl` |
| CHK-03 Compact buy/sell tape exports emitted replay trades with reasons | PASS | `data/portfolio_lifecycle_buy_sell_log.jsonl` |
| CHK-04 Audit summary reports action counts, open holds, round trips, and audit flags | PASS | `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json` |
| CHK-05 Exported BUY/SELL rows match `run_pit_replay(...)` ENTER/EXIT rows | PASS | `tests/test_pinned_universe.py` |
| CHK-06 Independent SAW Implementer and Reviewer A/B/C ownership | FAIL | Not run because current tool policy requires explicit user authorization to spawn subagents |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Governance closure cannot claim independent SAW review ownership. | Keep SAW verdict BLOCK until user explicitly authorizes independent reviewer/subagent rerun. | Docs/Ops | Open |
| Medium | First export attempt created false AMZN/MSFT/VRT buys by coercing missing `dist_sma20` to `0.0`. | Preserved NaN gate semantics, added `technical_entry_zone_missing`, regenerated artifacts, and added export-vs-replay regression. | Strategy/Data | Resolved |
| Low | Supply/pricing/margin are proxy-mapped, not literal Rule-of-100 columns. | Export records `rule100_proxy_sources`; carry as input to the optimal policy design. | Strategy | Carried |

## Scope Split Summary

In-scope findings/actions:

- Added side-effect-safe export-only decision tape generation.
- Published full decision JSONL, compact buy/sell JSONL, and audit summary.
- Added regression coverage tying BUY/SELL export rows to replay ENTER/EXIT events.
- Documented proxy factor mapping and audit-only boundaries.

Inherited out-of-scope findings/actions:

- Full execution ledger with fills, quantities, cost basis, realized P&L, slippage, and tax lots remains future work.
- Literal Rule-of-100 demand/supply/pricing/margin columns remain future feature-store work.
- Independent SAW subagent review is pending.

Open Risks:

- Independent SAW subagent Implementer and Reviewer A/B/C passes are pending.
- Decision export is not a full execution ledger.
- Rule-of-100 factor fields are proxy mappings until the feature store exposes literal columns.

Next action:

- Audit the decision tape, then design the true Rule-of-100 lifecycle policy.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `scripts/pit_lifecycle_replay.py` | Added export-only decision tape, buy/sell tape, audit summary, and CLI flags. | Local reviewed |
| `tests/test_pinned_universe.py` | Added export write/reason test and export-vs-replay event equivalence test. | Local reviewed |
| `data/portfolio_lifecycle_decision_log.jsonl` | Published full PIT daily decision tape. | Local reviewed |
| `data/portfolio_lifecycle_buy_sell_log.jsonl` | Published compact BUY/SELL tape. | Local reviewed |
| `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json` | Published audit summary. | Local reviewed |
| `docs/notes.md`, `docs/decision log.md`, `docs/phase_brief/phase65-brief.md`, `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md` | Documented export formulas, boundaries, evidence, and product/spec behavior. | Local reviewed |
| `docs/context/*_current.md` | Refreshed planner/bridge/impact/done/multistream/alignment/observability surfaces. | Local reviewed |
| `docs/lessonss.md` | Added export-vs-replay NaN guardrail lesson. | Local reviewed |

## Document Sorting

Document-change visibility is kept in current-context order: implementation, tests, data artifacts, evidence artifacts, notes, decision log, phase brief, product/spec surfaces, context truth surfaces, lessons, SAW report.

## Closure Packet

ChecksTotal: 6
ChecksPassed: 5
ChecksFailed: 1

ClosurePacket: RoundID=PH65_LIFECYCLE_DECISION_EXPORT_20260512; ScopeID=PH65_LIFECYCLE_DECISION_EXPORT; ChecksTotal=6; ChecksPassed=5; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent_saw_subagent_review_pending_execution_ledger_absent_rule100_literal_columns_absent; NextAction=audit_decision_tape_then_design_true_rule100_lifecycle_policy

ClosureValidation: PASS
SAWBlockValidation: PASS
