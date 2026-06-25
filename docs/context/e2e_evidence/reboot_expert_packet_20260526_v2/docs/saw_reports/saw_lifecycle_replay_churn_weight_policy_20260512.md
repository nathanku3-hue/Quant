# SAW Report - Lifecycle Replay Churn + Weight Policy

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend/Strategy, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: PH65_LIFECYCLE_REPLAY_CHURN_WEIGHT_20260512
ScopeID: PH65_LIFECYCLE_REPLAY_STATE_POLICY

## Scope

Implement the drop-in lifecycle replay fix first, then the optimal PIT lifecycle confirmation/state-machine fix for Portfolio & Allocation.

## Acceptance Checks

| Check | Result | Evidence |
|---|---|---|
| CHK-01 Drop-in ENTER weight uses 10% max-10 sizing | PASS | `scripts/pit_lifecycle_replay.py::replay_entry_weight`; `tests/test_pinned_universe.py` |
| CHK-02 Optimal lifecycle entry requires 3-of-4 PIT factor confirmation | PASS | `lifecycle_factor_confirmation(...)`; `tests/test_pinned_universe.py` |
| CHK-03 Entry/exit churn guards implemented | PASS | 3-day entry, 20-day min hold, 2-day exit, 20% hard exit, 10-day cooldown |
| CHK-04 Runtime lifecycle log regenerated from final policy | PASS | `data/portfolio_lifecycle_log.jsonl`; 33 events, 18 ENTER, 15 EXIT |
| CHK-05 Current portfolio is not sell-all cash | PASS | Port 8509 smoke shows AMAT/LRCX/TSM/CASH and no `100.0% Cash` |
| CHK-06 SPY/QQQ YTD benchmark fallback works when live fetch is rate-limited | PASS | Port 8509 smoke traces include Portfolio/SPY/QQQ |
| CHK-07 Focused tests pass | PASS | `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_pinned_universe.py tests\test_position_lifecycle.py tests\test_portfolio_universe.py tests\test_optimizer_view.py -q` |
| CHK-08 Full pytest passes | PASS | `.venv\Scripts\python -m pytest -q` |
| CHK-09 Context validation passes | PASS | `.venv\Scripts\python scripts\build_context_packet.py --validate` |
| CHK-10 Portfolio YTD uses price/TRI levels, not daily returns-as-prices | PASS | `core/data_orchestrator.py`; `tests/test_data_orchestrator_portfolio_runtime.py` |
| CHK-11 Port 8509 Portfolio YTD metric is sane | PASS | `docs/context/e2e_evidence/portfolio_ytd_return_fix_8509_smoke.json` shows `+14.25%` and no `7645112.18%` |
| CHK-12 Independent SAW Implementer and Reviewer A/B/C ownership | FAIL | Not run because current tool policy requires explicit user authorization to spawn subagents |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Governance closure cannot honestly claim independent SAW review ownership. | Keep verdict BLOCK and request explicit reviewer/subagent rerun authorization for PASS closure. | Docs/Ops | Open |
| Low | Live yfinance rate limits can hide YTD benchmark traces. | Added local TRI benchmark fallback for SPY/QQQ. | Frontend/UI | Resolved |
| High | Portfolio YTD compounded daily returns as prices, producing multi-million-percent returns. | Corrected `UnifiedDataPackage` price/return slots and made YTD local-history-first. | Data/Frontend | Resolved |

## Scope Split Summary

In-scope findings/actions:

- Implemented replay sizing, factor confirmation, churn guards, local benchmark fallback, runtime log, tests, docs, context updates, and live smoke.
- No unresolved in-scope code defect remains from local verification.

Inherited out-of-scope findings/actions:

- Lifecycle replay remains a reconstruction log, not a fill/quantity/cost execution ledger.
- Literal Rule-of-100 margin/supply/pricing columns are not in `features.parquet`; current optimal layer uses available PIT feature vectors.
- Broad dirty worktree contains inherited dashboard/navigation/context changes outside this focused round.

Open Risks:

- Independent SAW subagent Implementer and Reviewer A/B/C passes are pending.
- Lifecycle replay remains a reconstruction log until a future execution-ledger/accounting model is approved.
- The optimal lifecycle layer uses current PIT feature vectors rather than literal Rule-of-100 margin/supply/pricing columns.
- Broad dirty worktree contains inherited changes outside this focused round.

Next action:

- Explicitly authorize independent SAW subagent rerun for PASS governance closure, or accept local-verification status with SAW BLOCK recorded.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `docs/notes.md` | Added formula registry for drop-in and optimal lifecycle policy. | Local reviewed |
| `docs/decision log.md` | Added lifecycle replay churn + weight policy decision record. | Local reviewed |
| `docs/phase_brief/phase65-brief.md` | Added approved scope, held scope, contract, and acceptance checks. | Local reviewed |
| `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md` | Added product/spec notices and boundaries. | Local reviewed |
| `docs/context/*_current.md` | Refreshed bridge, planner, impact, done, multi-stream, alignment, and observability surfaces. | Local reviewed |
| `docs/lessonss.md` | Added lifecycle replay state guardrail lesson. | Local reviewed |
| `docs/context/e2e_evidence/portfolio_ytd_return_fix_8509_smoke.json` | Captured fixed YTD browser-smoke evidence. | Local reviewed |

## Document Sorting

Document-change visibility is kept in current-context order: notes, decision log, phase brief, product/spec surfaces, context truth surfaces, lessons, SAW report.

## Closure Packet

ChecksTotal: 12
ChecksPassed: 11
ChecksFailed: 1

ClosurePacket: RoundID=PH65_LIFECYCLE_REPLAY_CHURN_WEIGHT_20260512; ScopeID=PH65_LIFECYCLE_REPLAY_STATE_POLICY; ChecksTotal=12; ChecksPassed=11; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent_saw_subagent_review_pending_lifecycle_execution_ledger_future_work_rule100_literal_columns_absent_dirty_worktree_inherited; NextAction=explicitly_authorize_independent_saw_rerun_or_accept_local_verification_status

ClosureValidation: PASS
SAWBlockValidation: PASS
