SAW Report: Phase 31 Option 1 Medium-Risk Reconciliation Round 2

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init (fallback) | Domains: Execution Trust Boundary, Runtime Ops, Data Integrity | FallbackSource: docs/spec.md + docs/phase_brief/phase31-brief.md
Ownership Check: PASS (Implementer and reviewers are distinct agents)
- Implementer: Codex (parent agent)
- Reviewer A: Lagrange (`019ca952-acf4-7012-8ee5-da759d65f68c`)
- Reviewer B: Zeno (`019ca952-aded-7d10-a947-0595d22e9d67`)
- Reviewer C: Curie (`019ca952-aee2-7872-9f37-905801e83792`)

RoundID: RND-20260301-PH31-OPTION1-MEDIUM-R2
ScopeID: SCOPE-PH31-OPTION1-MEDIUM-RECON

Scope
- In-scope: `execution/microstructure.py`, `execution/signed_envelope.py`, `core/dashboard_control_plane.py`, `app.py`, touched tests, and mandatory docs updates for this reconciliation round.
- Out-of-scope: strategy research changes, broker feature expansion, full phase-end closeout protocol.

Acceptance Checks
- CHK-01: Deterministic spool UID enforces idempotency across retry paths and repeated append calls.
- CHK-02: Immediate append accounting is truthful (`spool_records_appended` durable-only) and prepared-vs-written counters are explicit.
- CHK-03: Retry-buffer overflow is fail-closed (no silent drop).
- CHK-04: Shutdown with pending telemetry is fail-closed (explicit runtime error).
- CHK-05: Replay ledger malformed state is fail-closed with quarantine/rewrite and parent-dir fsync on rewrite.
- CHK-06: Null-like date (`pd.NaT`) planner path is invalid-state safe and UI spinner label uses planner-normalized date key.
- CHK-07: Focused regression suite passes for touched modules.
- CHK-08: Integrated regression matrix passes and SAW reviewer A/B/C report no in-scope Critical/High findings.

Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Duplicate telemetry rows could occur on post-write append errors and repeated logical retries | Deterministic business-key spool UID + UID preservation during decode + retry idempotency tests | Implementer | Resolved |
| High | Telemetry overflow path could silently lose rows under lock contention | Overflow path changed to explicit fail-closed error (no partial enqueue/drop) + regression | Implementer | Resolved |
| High | Buffered telemetry could be lost on shutdown without explicit signal | Bounded drain on stop + explicit fail-closed shutdown error when pending remains | Implementer | Resolved |
| High | Malformed replay ledger could allow acceptance after corruption | Quarantine + valid-line rewrite + fail-closed reject of current submit + tests | Implementer | Resolved |
| High | Missing broker ack could be misclassified as healthy heartbeat latency | Strict ack-anchor fallback policy resulting in `latency_missing` block + regression | Implementer | Resolved |
| Medium | Replay ledger check remains line-scan under lock | Added max-row cap (`TZ_EXECUTION_REPLAY_LEDGER_MAX_ROWS`) to bound worst-case scan cost | Implementer | Mitigated |

Scope Split Summary
- in-scope findings/actions: all in-scope Critical/High findings from this round are resolved and revalidated.
- inherited out-of-scope findings/actions: none carried in this round.

Document Changes Showing
- `execution/microstructure.py`: deterministic retry UID, truthful counters, overflow/shutdown fail-closed, ack-anchor strictness; Reviewer status: Cleared
- `execution/signed_envelope.py`: malformed-ledger fail-closed, parent-dir fsync, ledger row-cap trim gate, updated lock timeout default; Reviewer status: Cleared
- `core/dashboard_control_plane.py`: null-like date coercion ordering fix (`pd.NaT` safe); Reviewer status: Cleared
- `app.py`: planner-normalized spinner date label (no raw `.date()` assumption); Reviewer status: Cleared
- `tests/test_execution_microstructure.py`: new regressions for post-write dedupe, overflow fail-closed, repeated-retry idempotency, missing-ack heartbeat block, shutdown fail-closed; Reviewer status: Cleared
- `tests/test_signed_envelope_replay.py`: malformed-ledger fail-closed and rewrite-fsync regression updates; Reviewer status: Cleared
- `tests/test_dashboard_control_plane.py`: `pd.NaT` invalid-state regression; Reviewer status: Cleared
- `docs/phase_brief/phase31-brief.md`: round update + evidence pack; Reviewer status: Cleared
- `docs/notes.md`: formula/contract addendum for D-201 controls; Reviewer status: Cleared
- `docs/lessonss.md`: new round lesson entry; Reviewer status: Cleared
- `docs/decision log.md`: D-201 decision record; Reviewer status: Cleared

Document Sorting (GitHub-optimized)
1. `docs/phase_brief/phase31-brief.md`
2. `docs/notes.md`
3. `docs/lessonss.md`
4. `docs/decision log.md`
5. `docs/saw_reports/saw_phase31_option1_medium_round2.md`

Checks Summary
- ChecksTotal: 8
- ChecksPassed: 8
- ChecksFailed: 0

SAW Verdict: PASS
ClosurePacket: RoundID=RND-20260301-PH31-OPTION1-MEDIUM-R2; ScopeID=SCOPE-PH31-OPTION1-MEDIUM-RECON; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=Medium_replay_scan_cost_bounded_by_row_cap_and_non_blocking_pytest_windows_cleanup_warning; NextAction=Proceed_with_phase31_option1_medium_merge_and_monitor_new_fail_closed_events
ClosureValidation: PASS
SAWBlockValidation: PASS

Evidence
- `.venv\Scripts\python -m pytest -q tests/test_execution_microstructure.py tests/test_signed_envelope_replay.py tests/test_dashboard_control_plane.py` -> PASS (`58 passed`).
- `.venv\Scripts\python -m pytest -q tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py tests/test_execution_microstructure.py tests/test_auto_backtest_control_plane.py tests/test_dashboard_control_plane.py tests/test_ticker_pool.py tests/test_alpha_engine.py tests/test_engine.py tests/test_statistics.py tests/test_signed_envelope_replay.py` -> PASS (`256 passed`).
- `.venv\Scripts\python -m py_compile execution/microstructure.py execution/signed_envelope.py core/dashboard_control_plane.py app.py tests/test_execution_microstructure.py tests/test_signed_envelope_replay.py tests/test_dashboard_control_plane.py` -> PASS.
- Reviewer A/B/C final verification: no in-scope Critical/High findings.

Assumptions
- Phase-end protocol is not triggered in this round; this is a reconciliation-hardening cycle within active Phase 31.

Open Risks:
- Medium operational debt remains around replay ledger scan path (bounded but still file-scan-based) and known non-fatal Windows pytest temp cleanup warning.
Next action:
- Keep D-201 controls active in runtime monitoring and schedule the next bounded optimization pass for replay ledger indexing if lock contention telemetry trends up.

Rollback Note
- Revert all touched code/tests/docs for this round as one batch if D-201 is rejected.
