# SAW Report - Replay Coverage Contract Audit Fix - 2026-05-14

SAW Verdict: PASS

RoundID: 20260514-replay-coverage-contract-audit-fix  
ScopeID: replay-coverage-contract-audit-fix  
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-execution | Domains: Backend, Data, Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/phase65-brief.md`

## Scope

Work round scope: fix SAW audit BLOCK findings for v6 selected-method replay coverage/performance.

Owned files changed in this round:

- `strategies/strategy_replay.py`
- `strategies/optimizer.py`
- `tests/test_strategy_replay.py`
- `tests/test_strategy_replay_coverage.py`
- `tests/test_optimizer_core_policy.py`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/notes.md`
- `docs/lessonss.md`
- `docs/decision log.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/observability_pack_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/current_context.json`
- `docs/context/current_context.md`
- `scripts/build_context_packet.py`
- `tests/test_build_context_packet.py`

Acceptance checks:

- CHK-01: Replay metadata keeps `coverage_segments`.
- CHK-02: Unavailable rows preserve `input_unavailable:<coverage_reason>`.
- CHK-03: Uncovered unavailable dates batch row emission and avoid per-date DataFrame/performance/concat overhead.
- CHK-04: Row-heavy `no_priced_members` unavailable windows preserve explicit per-member rows under the daily-scale budget.
- CHK-05: Replay performance avoids same-date lookahead and recomputes loader equity once at run level.
- CHK-06: Duplicate shadowed coverage/perf tests are removed.
- CHK-07: Bound-feasible inverse-volatility targets skip SLSQP with diagnostics.
- CHK-08: Focused, affected, exact reviewer-line, full-regression, and context bootstrap checks pass.
- CHK-09: SAW reviewer C recheck passes.
- CHK-10: Final Implementer, Reviewer A, and Reviewer B rechecks pass.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Initial daily-scale path only proved CASH-only `membership_gap_exceeded`; row-heavy `no_priced_members` windows could exceed 10s. | Added `_cash_closed_rows_fast(...)` and row-heavy daily-scale regression. | Backend/Data | Fixed |
| High | Replay performance could credit date `t` weights with same-date returns. | Added next-tradable-return alignment via `_returns_for_allocation_dates(...)` and regression coverage. | Backend/Data | Fixed |
| Medium | Loader-based replay attached performance per chunk, resetting `portfolio_equity` inside a run. | Build raw rows first and attach performance once after combined loader output. | Backend/Data | Fixed |
| Medium | Small-frame return lookup treated real `0.0` permno returns as missing and could fall through to ticker lookup. | Switched small-frame and vectorized paths to presence/NA sentinels, with regression coverage. | Backend/Data | Fixed |
| Medium | Duplicate test definitions hid intent under pytest collection. | Removed older shadowed duplicate coverage/perf blocks. | Tests | Fixed |
| Medium | Context bootstrap could validate while pointing at the older Rule100/YTD handover instead of replay-audit truth. | Current truth surfaces with complete New Context Packets now outrank older same-phase handovers; heading extraction and drift validation regressions were added; `current_context.*` was rebuilt. | Docs/Ops | Fixed |
| Process High | Final Implementer, Reviewer A, and Reviewer B rechecks were previously unavailable because the account hit the subagent usage limit. | Reissued formal Implementer plus Reviewer A/B/C passes after resume; all returned PASS. | Parent/Ops | Fixed |

## Scope Split Summary

In-scope fixed:

- coverage segment metadata,
- specific unavailable reasons,
- uncovered-date batch emission,
- row-heavy unavailable performance,
- next-return performance alignment,
- run-level loader equity continuity,
- duplicate test cleanup,
- inverse-volatility deterministic fast path,
- replay-audit current-context bootstrap selection.

Inherited / out-of-scope:

- dashboard backend-bundle end-to-end consumption remains the next integration step;
- runtime smoke remains phase-close work;
- broad inherited dirty/untracked worktree state was not reverted or normalized in this narrow audit fix.

## Document Changes Showing

- `docs/prd.md`, `docs/spec.md`, `PRD.md`, `PRODUCT_SPEC.md`: replay audit notice, PIT return alignment, and boundary updates. Reviewer status: parent-reviewed.
- `docs/phase_brief/phase65-brief.md`: audit fix addendum with current evidence. Reviewer status: parent-reviewed.
- `docs/notes.md`: formula and behavior registry for next-return alignment, fast unavailable rows, and inverse-vol fast path. Reviewer status: parent-reviewed.
- `docs/lessonss.md`: self-learning entry for profiling before threshold relaxation and same-date lookahead. Reviewer status: parent-reviewed.
- `docs/decision log.md`: decision and evidence record. Reviewer status: parent-reviewed.
- `docs/context/*.md`: bridge/planner/done/impact/multistream/alignment/observability refreshed. Reviewer status: parent-reviewed.
- `docs/context/current_context.json`, `docs/context/current_context.md`: regenerated by context packet builder. Reviewer status: validated.
- `scripts/build_context_packet.py`, `tests/test_build_context_packet.py`: current-truth packet source selection, heading extraction, and drift-validation regressions. Reviewer status: Implementer + Reviewer A/B/C PASS.

Document Sorting: maintained in GitHub-optimized order from `docs/checklist_milestone_review.md`.

## Verification Evidence

| EvidenceID | Command | Result | Notes |
|---|---|---|---|
| EVD-01 | `.venv\Scripts\python -m py_compile strategies\strategy_replay.py strategies\optimizer.py scripts\build_context_packet.py tests\test_strategy_replay.py tests\test_strategy_replay_coverage.py tests\test_optimizer_core_policy.py tests\test_build_context_packet.py` | PASS | Scoped compile. |
| EVD-02 | `.venv\Scripts\python -m pytest tests\test_strategy_replay_coverage.py -q --durations=12` | PASS, 11 passed | Latest slowest: row-heavy no-priced-members 1.21s, 4-asset 5Y 1.20s, CASH-only daily-scale 0.30s. |
| EVD-03 | `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_replay_non_cash_closed.py tests\test_strategy_replay_coverage.py tests\test_optimizer_core_policy.py -q` | PASS, 68 passed | Affected replay/optimizer suite. |
| EVD-04 | `.venv\Scripts\python -m pytest tests\test_execution_microstructure.py::test_shutdown_execution_microstructure_spoolers_fails_closed_when_sink_error_present -q` | PASS | Rechecked reviewer-reported full-suite failure line. |
| EVD-05 | `.venv\Scripts\python -m pytest -q` | PASS | Full regression passed after bootstrap reconciliation. |
| EVD-06 | `.venv\Scripts\python scripts\build_context_packet.py` | PASS | Context packet regenerated. |
| EVD-07 | `.venv\Scripts\python scripts\build_context_packet.py --validate` | PASS | Context packet validation passed. |
| EVD-08 | `.venv\Scripts\python -m pytest tests\test_build_context_packet.py tests\test_phase61_context_hygiene.py -q` | PASS, 24 passed | Current-truth selection plus closed-baseline token preserved. |
| EVD-09 | SAW Implementer recheck | PASS | Implementation complete; `current_context.*` starts with replay-audit content. |
| EVD-10 | SAW Reviewer A/B/C rechecks | PASS | Strategy correctness, operational resilience, data integrity/performance all passed. |

## Ownership Check

Implementer and reviewers were separate agents:

- Parent implementer: Codex main agent.
- SAW Implementer: independent subagent, PASS after reconciliation.
- Reviewer A: independent subagent, PASS.
- Reviewer B: independent subagent, PASS.
- Reviewer C: independent subagent, PASS.

Ownership check status: PASS.

## Top-Down Snapshot

L1: Selected-Method Replay Coverage Contract
L2 Active Streams: Backend, Data, Docs/Ops
L2 Deferred Streams: Frontend/UI runtime smoke
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Backend/Data
Active Stage Level: L3

+--------------------+----------------------+--------+--------------------------------------------------------------+
| Stage              | Current Scope        | Rating | Next Scope                                                   |
+--------------------+----------------------+--------+--------------------------------------------------------------+
| Planning           | B=Replay/OH=Parent/AC=Audit | 100/100 | 1) Dashboard backend bundle smoke [86/100]: next integration |
| Executing          | Audit fixes          | 100/100 | 1) Hold or integrate backend bundle [82/100]: code clean |
| Iterate Loop       | A/B/C fixes          | 100/100 | 1) Preserve bootstrap/replay regressions [90/100]: locked |
| Final Verification | Tests/context/SAW pass | 100/100 | 1) Runtime smoke at phase close [80/100]: out-of-scope now |
+--------------------+----------------------+--------+--------------------------------------------------------------+

## Open Risks

Open Risks:

- Runtime smoke and dashboard backend-bundle end-to-end consumption remain separate phase-close work.

Next action: proceed to dashboard backend-bundle end-to-end integration plus full regression/runtime smoke, or hold.

ClosurePacket: RoundID=20260514-replay-coverage-contract-audit-fix; ScopeID=replay-coverage-contract-audit-fix; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS; OpenRisks=dashboard_backend_bundle_runtime_smoke_phase_close_work; NextAction=dashboard_backend_bundle_integration_full_regression_runtime_smoke_or_hold

ClosureValidation: PASS
SAWBlockValidation: PASS
EvidenceValidation: PASS

Evidence:

- EVD-01 through EVD-10 passed.

Assumptions:

- The latest full pytest run supersedes the earlier stale microstructure failure.
- Dashboard backend-bundle integration remains intentionally out of this replay coverage audit fix scope.

Rollback Note:

- Revert this round's changes in `strategies/strategy_replay.py`, `strategies/optimizer.py`, `tests/test_strategy_replay.py`, `tests/test_strategy_replay_coverage.py`, and `tests/test_optimizer_core_policy.py` to return to the prior replay behavior; do not alter canonical market data, lifecycle logs, or replay artifacts.
