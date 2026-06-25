# SAW Report - Portfolio Lifecycle Current Holds Fix

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-reviewer-rerun | Domains: Backend, Frontend/UI, Data, Docs/Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase65-brief.md`

RoundID: `20260512_portfolio_lifecycle_current_holds_saw`
ScopeID: `portfolio_lifecycle_current_holds_fix`

## Scope And Ownership

Scope: make Position Lifecycle Replay authoritative for current open holdings on Portfolio & Allocation, preserving residual cash and PIT safety without changing optimizer objective, ranking, scoring, alerts, brokers, or provider ingestion.

Owned runtime files:
- `data/portfolio_lifecycle_log.py`
- `strategies/portfolio_universe.py`
- `views/optimizer_view.py`
- `dashboard.py`

Owned test files:
- `tests/test_position_lifecycle.py`
- `tests/test_portfolio_universe.py`
- `tests/test_optimizer_view.py`
- `tests/test_dash_2_portfolio_ytd.py`

Owned docs/context files:
- `docs/notes.md`
- `docs/decision log.md`
- `docs/prd.md`
- `docs/spec.md`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/lessonss.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/observability_pack_current.md`

## Acceptance Checks

- CHK-01: lifecycle open-position reconstruction uses latest ENTER/EXIT event at or before `as_of`.
- CHK-02: future-dated lifecycle rows do not enter current holdings.
- CHK-03: lifecycle sell-all overrides stale JSON position memory.
- CHK-04: open lifecycle holds enter the universe as `included_current_hold` even if the current scanner row is EXIT/KILL.
- CHK-05: no-fresh-PIT-ENTER with open lifecycle holds renders lifecycle holds plus residual cash, not 100% cash.
- CHK-06: residual cash is preserved across session weights, live ticker mapping, and aligned performance weights unless weights exceed 100%.
- CHK-07: lifecycle JSONL appends use lock + temp + fsync + `os.replace`, and malformed JSONL rows fail closed.
- CHK-08: focused compile, focused pytest, full pytest, context validation, and browser smoke pass.
- CHK-09: independent Implementer and Reviewer A/B/C passes complete with no unresolved in-scope Critical/High findings.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High, prior | Live ticker YTD path could lose residual cash by normalizing sub-100% lifecycle holdings to 100%. | Added `map_permno_weights_to_ticker_weights(...)`, delegated `_weights_by_ticker(...)` to it, and added numeric residual-cash regressions. | Parent Implementer | RESOLVED |
| Medium, prior | Lifecycle JSONL append was not true temp-to-replace, and malformed JSONL rows could be silently skipped. | Reworked append to lock + temp + fsync + `os.replace`; malformed rows now raise `ValueError`; focused tests cover cleanup and fail-closed parsing. | Parent Implementer | RESOLVED |
| Low | Hard-crash stale lifecycle `.lock` recovery is not implemented. | Current behavior fails closed by timeout; carry as future Ops hardening. | Future Ops | CARRIED |
| Low | Lifecycle replay is not a full execution ledger with fills, quantities, realized P&L, or slippage. | Carry as separate lifecycle accounting policy decision. | Future Data/Ops | CARRIED |

## Subagent Results

Ownership check: PASS. Parent implementer and independent Reviewer A/B/C reruns were separate agents. Reviewers performed read-only inspection and did not edit files.

- Implementer pass: PASS after residual-cash finding was reconciled.
- Reviewer A, strategy correctness/regression: PASS after `_weights_by_ticker(...)` reconciliation.
- Reviewer B, runtime/operational resilience: PASS; Low stale-lock recovery carried.
- Reviewer C, data integrity/performance: PASS; inherited execution-ledger limitation carried.

## Scope Split Summary

In-scope resolved:
- Current holdings are reconstructed from lifecycle replay before declaring sell-all cash.
- Scanner EXIT/KILL labels do not close open lifecycle holds without a lifecycle EXIT.
- Residual cash is preserved in allocation and live YTD performance paths.
- Lifecycle JSONL writes and malformed-row handling are fail-closed enough for this focused bug round.

Inherited out-of-scope:
- Broader dirty dashboard/navigation worktree remains outside this focused fix.
- Full lifecycle transaction-accounting policy, stale-lock cleanup, fills, quantities, realized P&L, and slippage remain future work.
- Provider ingestion, canonical market-data writes, alerts, brokers, ranking, scoring, conviction mode, Black-Litterman, and new optimizer objectives remain blocked.

## Evidence

- `.venv\Scripts\python -m py_compile data\portfolio_lifecycle_log.py strategies\portfolio_universe.py dashboard.py tests\test_position_lifecycle.py tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_position_lifecycle.py tests\test_portfolio_universe.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 58 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Browser smoke at `http://127.0.0.1:8509/portfolio-and-allocation` -> PASS; Portfolio Optimizer renders, lifecycle-hold message renders, no `100% Cash` title, no import error, and current-hold tickers are visible.
- `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.

## SE Executor Evidence

Task table:
- TSK-01: lifecycle state reconstruction and fail-closed JSONL handling | artifacts: `data/portfolio_lifecycle_log.py`, `tests/test_position_lifecycle.py` | check: focused tests | status: PASS | evidence: EVD-01.
- TSK-02: universe current-hold inclusion and residual-cash weight mapping | artifacts: `strategies/portfolio_universe.py`, `tests/test_portfolio_universe.py` | check: focused tests | status: PASS | evidence: EVD-02.
- TSK-03: optimizer/UI lifecycle-hold allocation behavior | artifacts: `views/optimizer_view.py`, `tests/test_optimizer_view.py` | check: AppTest/focused tests | status: PASS | evidence: EVD-03.
- TSK-04: YTD/live performance residual-cash preservation | artifacts: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py` | check: focused tests/browser smoke | status: PASS | evidence: EVD-04.
- TSK-05: docs/context/SAW closeout | artifacts: docs/context, notes, decision log, PRD/spec, this SAW report | check: context validation + SAW validators | status: PASS | evidence: EVD-05.

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05
EvidenceRows: EVD-01|20260512_portfolio_lifecycle_current_holds_saw|2026-05-11T16:31:04Z;EVD-02|20260512_portfolio_lifecycle_current_holds_saw|2026-05-11T16:31:04Z;EVD-03|20260512_portfolio_lifecycle_current_holds_saw|2026-05-11T16:31:04Z;EVD-04|20260512_portfolio_lifecycle_current_holds_saw|2026-05-11T16:31:04Z;EVD-05|20260512_portfolio_lifecycle_current_holds_saw|2026-05-11T16:31:04Z
EvidenceValidation: PASS

## Document Changes Showing

- `data/portfolio_lifecycle_log.py`: added PIT-safe open-position reconstruction, temp-replace append, lock handling, and malformed-row fail-closed behavior. Reviewer status: PASS.
- `strategies/portfolio_universe.py`: added lifecycle-first current memory, current-hold universe inclusion, and ticker-weight mapping preserving residual cash. Reviewer status: PASS.
- `views/optimizer_view.py`: renders lifecycle holds plus residual cash when no fresh PIT ENTER candidates exist. Reviewer status: PASS.
- `dashboard.py`: reads lifecycle current memory and preserves residual cash in session/ticker/aligned YTD paths. Reviewer status: PASS.
- Focused tests: added PIT, sell-all, residual-cash, malformed-log, and lifecycle-hold UI regressions. Reviewer status: PASS.
- Governance/current-context docs: updated behavior, formula notes, boundaries, evidence, and lesson guardrail. Reviewer status: PASS.

## Document Sorting

Canonical sorting order follows `docs/checklist_milestone_review.md`: runtime/test artifacts first, docs-as-code surfaces next, current truth surfaces last, SAW report terminal.

## Open Risks

Open Risks:
- Low stale-lock recovery follow-up remains for future Ops.
- Lifecycle replay is still not a full execution ledger; broader accounting policy remains future Data/Ops work.
- Inherited dirty worktree outside this focused fix remains out-of-scope.

## Next action

Next action:
Hold, or separately review lifecycle position-accounting policy if full execution-ledger semantics are desired.

ClosurePacket: RoundID=20260512_portfolio_lifecycle_current_holds_saw; ScopeID=portfolio_lifecycle_current_holds_fix; ChecksTotal=9; ChecksPassed=9; ChecksFailed=0; Verdict=PASS; OpenRisks=Low_stale_lock_recovery_and_inherited_lifecycle_replay_not_full_execution_ledger; NextAction=Hold_or_review_lifecycle_position_accounting_policy

ClosureValidation: PASS
SAWBlockValidation: PASS
