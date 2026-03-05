# SAW Report: Phase 32 Step 3 DuckDB Flush Optimization (Round 1, 2026-03-02)

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: phase32-step3-executing | Domains: Backend, Ops, Data

RoundID: R20260302-PH32-S3-R1
ScopeID: PH32-S3-DUCKDB-FLUSH
Scope: Execute DuckDB flush optimization closure with O(N) scan eradication, tail-export continuity, and fail-closed durability propagation.

Ownership Check:
- Implementer: Codex (parent)
- Reviewer A: `Locke` (`019cae74-9dca-78c2-aa9e-76bbac3aec02`)
- Reviewer B: `McClintock` (`019cae86-5297-7392-af1c-5261ba0c729c`)
- Reviewer C: `Sartre` (`019cae8a-8166-71e3-a569-feb8d244e388`)
- Result: implementer and reviewer roles are distinct.

Acceptance Checks:
- CHK-S3-01: Flush path removes O(N) table COUNT scans and uses indexed dedup lookups.
- CHK-S3-02: Export path removes pre-count scan and preserves deterministic tail export continuity at EOF.
- CHK-S3-03: Fail-closed durability remains enforced with `MicrostructureFlushError` propagation on shutdown sink failures.

SAW Verdict: PASS

Findings Table:
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | EOF export cursor rewind (`start_row > 0` + empty batch) delayed new-tail export by one cycle after appends | Removed EOF cursor rewind in `_export_duckdb_table_to_parquet`; keep cursor pinned at EOF and added `test_export_duckdb_table_to_parquet_exports_new_tail_after_eof_without_extra_cycle` | Implementer | Resolved |
| High | Shutdown fail-closed gate only enforced on `pending_bytes`, allowing sink errors to pass when buffers had drained | Hardened `_TelemetrySpooler.stop` to raise `MicrostructureFlushError` on any of `{pending_bytes > 0, buffer_drop_count > 0, last_flush_error != none}` and preserved propagation via `_shutdown_execution_microstructure_spoolers` | Implementer | Resolved |
| Medium | Overflow-path test teardown relied on implicit shutdown behavior and leaked new fail-closed exception to autouse fixture | Updated overflow regression to assert explicit shutdown fail-closed raise in-test, preventing teardown leakage | Implementer | Resolved |

Scope Split Summary:
- in-scope:
  - DuckDB flush-path O(N) scan removal and indexed dedup write-path enforcement.
  - export-path EOF cursor continuity and deterministic append-tail behavior.
  - shutdown fail-closed durability propagation for sink failure classes.
- inherited out-of-scope:
  - Step 4 backlog: batch exception taxonomy split.
  - Step 5 backlog: routing diagnostics tail.
  - Step 6 backlog: UID drift closure.

Document Changes Showing:
1. `execution/microstructure.py`
   - EOF cursor no-rewind behavior in `_export_duckdb_table_to_parquet`.
   - Shutdown fail-closed hardening in `_TelemetrySpooler.stop`.
   - Reviewer status: A PASS, B PASS, C PASS after reconciliation.
2. `tests/test_execution_microstructure.py`
   - Added EOF-tail continuity regression after explicit EOF drain.
   - Added synthetic disk-full sink error shutdown propagation regression.
   - Updated overflow fail-closed test to assert explicit shutdown exception.
   - Reviewer status: A PASS, B PASS, C PASS after reconciliation.
3. `docs/phase_brief/phase32-brief.md`
   - Updated Step 3 evidence (`44 passed`), contract notes, and open-risk text to match reconciled behavior.
   - Reviewer status: parent reconciliation.
4. `docs/decision log.md`
   - Updated D-213 implementation/evidence details to include EOF continuity and shutdown fail-closed propagation hardening.
   - Reviewer status: parent reconciliation.
5. `docs/notes.md`
   - Updated shutdown durability formula to `MicrostructureFlushError` and expanded fail condition set.
   - Reviewer status: parent reconciliation.
6. `docs/lessonss.md`
   - Added Phase 32 Step 3 lesson entry with root cause and guardrail.
   - Reviewer status: parent reconciliation.

Evidence:
- `.venv\Scripts\python -m pytest tests/test_execution_microstructure.py --disable-warnings` -> PASS (`44 passed in 21.05s`).
- `.venv\Scripts\python -m py_compile execution/microstructure.py tests/test_execution_microstructure.py` -> PASS.
- Reviewer A: initial BLOCK on EOF cursor rewind + missing EOF-tail regression; both resolved.
- Reviewer B: initial BLOCK on shutdown sink-error propagation; resolved with stop-gate hardening + regression.
- Reviewer C: PASS on data/performance integrity after reconciliation.

Assumptions:
- Telemetry DuckDB tables are append-only under normal runtime ownership; out-of-band truncation is treated as an operational anomaly.
- `MicrostructureFlushError` is the canonical fail-closed exception type for spool shutdown integrity violations.
- Pytest atexit temp-dir cleanup `PermissionError` remains an environment artifact and non-blocking for verdicts.

Open Risks:
- Export path still uses `LIMIT/OFFSET`; very large offsets can degrade throughput despite removal of full-table COUNT scans.
- EOF cursor is intentionally pinned; out-of-band table truncation/rebuild may require explicit cursor reset to recover.
- Windows pytest temp cleanup `PermissionError` noise can obscure logs, though it does not fail command exit status.

Rollback Note:
- Revert `execution/microstructure.py`, `tests/test_execution_microstructure.py`, and the Step 3 doc updates (`docs/phase_brief/phase32-brief.md`, `docs/decision log.md`, `docs/notes.md`, `docs/lessonss.md`) if D-213 reconciliation is rejected.

Next action:
- Start Phase 32 Step 4 (batch exception taxonomy split) with deterministic retry-exhaustion taxonomy assertions.

ClosurePacket: RoundID=R20260302-PH32-S3-R1; ScopeID=PH32-S3-DUCKDB-FLUSH; ChecksTotal=3; ChecksPassed=3; ChecksFailed=0; Verdict=PASS; OpenRisks=offset_pagination_scaling_and_eof_cursor_manual_reset_and_pytest_atexit_permissionerror_noise; NextAction=start_phase32_step4_batch_exception_taxonomy_split
ClosureValidation: PASS
SAWBlockValidation: PASS
