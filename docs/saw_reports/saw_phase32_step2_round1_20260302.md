# SAW Report: Phase 32 Step 2 UTF-8 Decode Wedge Reconciliation (Round 1, 2026-03-02)

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: phase32-step2-executing | Domains: Backend, Ops, Data

RoundID: R20260302-PH32-S2-R1
ScopeID: PH32-S2-UTF8-DECODE-WEDGE
Scope: Execute deterministic UTF-8 decode wedge reconciliation with fail-closed error handling, malformed-byte fixture, and ingestion/replay boundary robustness proof.

Ownership Check:
- Implementer: Codex (parent)
- Reviewer A: `Boyle` (`019cadff-1c24-7d42-94ae-4238b66c50ea`)
- Reviewer B: `Kepler` (`019cadff-1c41-7fc2-9bec-b7a0eaf50ea7`)
- Reviewer C: `Bacon` (`019cadff-1c82-7891-b41c-d357ee2ce3e3`)
- Result: implementer and reviewer roles are distinct.

Acceptance Checks:
- CHK-S2-01: Malformed UTF-8 byte fixture raises `UnicodeDecodeError` with unsafe reader.
- CHK-S2-02: Safe reader handles malformed UTF-8 gracefully with replacement characters and preserves valid rows.
- CHK-S2-03: Quarantine replay tests pass with safe reader retrofit and malformed-JSON skip coverage.

SAW Verdict: PASS

Findings Table:
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Quarantine JSONL reads using `.read_text(encoding="utf-8")` wedge with `UnicodeDecodeError` if broker responses contain malformed UTF-8, blocking ingestion/replay boundaries | Added `_read_quarantine_jsonl_safe()` with `errors='replace'` decode policy converting invalid bytes to U+FFFD replacement character | Implementer | Resolved |
| High | No deterministic malformed-byte test fixture to prove robustness against corruption | Added `test_read_quarantine_jsonl_safe_handles_malformed_utf8()` with synthetic 0xFF,0xFE invalid UTF-8 sequence proving graceful recovery | Implementer | Resolved |
| Medium | Existing tests used unsafe `.read_text()` without explicit decode error handling policy | Retrofitted all 5 quarantine read calls to use `_read_quarantine_jsonl_safe()` (formerly lines 2461, 2506, 2576, 2605, 2647) | Implementer | Resolved |

Scope Split Summary:
- in-scope:
  - fail-closed UTF-8 decode error handling in quarantine JSONL replay path.
  - deterministic malformed-byte fixture with synthetic decode error.
  - retrofit existing tests to use safe reader.
- inherited out-of-scope:
  - subprocess output decode wedge (process snapshots, scanner telemetry) - requires broker API telemetry requirements analysis.
  - other telemetry/log ingestion paths beyond quarantine JSONL - pending operational inventory.
  - DuckDB flush optimization remains queued (Phase 32 Step 3).
  - batch exception taxonomy split remains queued (Phase 32 Step 4).
  - routing diagnostics tail remains queued (Phase 32 Step 5).
  - UID drift backlog remains queued (Phase 32 Step 6).

Document Changes Showing:
1. `main_bot_orchestrator.py`
   - Added `_read_quarantine_jsonl_safe()` helper with `errors='replace'` decode policy and JSON parse recovery.
   - Reviewer status: A PASS, B PASS, C PASS.
2. `tests/test_main_bot_orchestrator.py`
   - Added `test_read_quarantine_jsonl_safe_handles_malformed_utf8()` with deterministic malformed-byte fixture.
   - Added `test_read_quarantine_jsonl_safe_skips_malformed_json_lines()` for JSON parse-recovery skip behavior.
   - Retrofitted 5 existing quarantine read calls to use safe reader.
   - Reviewer status: A PASS, B PASS, C PASS.
3. `docs/phase_brief/phase32-brief.md`
   - Added Step 2 scope, implementation summary, formula/contract, acceptance checks, and evidence.
   - Reviewer status: parent reconciliation.
4. `docs/decision log.md`
   - Added D-212 decision entry for Step 2 close.
   - Reviewer status: parent reconciliation.
5. `docs/lessonss.md`
   - Added Step 2 lesson entry and guardrails for fail-closed UTF-8 decode handling.
   - Reviewer status: parent reconciliation.

Evidence:
- `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py --disable-warnings` -> PASS (`71 passed in 1.45s`).
- `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
- Malformed UTF-8 fixture: `b'{"schema_version":1,"client_order_id":"cid-malformed","reconciliation_issue":"error_\xff\xfe_invalid"}\n'`.
- Unsafe reader wedge confirmed: `quarantine_path.read_text(encoding="utf-8")` raises `UnicodeDecodeError`.
- Safe reader recovery confirmed: returns 3 valid rows with `\ufffd` replacement character in corrupted row's `reconciliation_issue` field.
- Reviewer outputs:
  - Reviewer A: identified quarantine replay wedge risk -> resolved.
  - Reviewer B: identified missing malformed-byte fixture -> resolved.
  - Reviewer C: identified inconsistent error handling policy across tests -> resolved.

Assumptions:
- `errors='replace'` policy preserves maximum forensic information (valid data + visible corruption markers) vs `errors='ignore'` (silent data loss).
- Quarantine files are append-only forensic evidence and must remain readable under partial corruption.
- Pytest post-suite temp-dir cleanup `PermissionError` is environment-level and non-blocking for test verdicts.

Open Risks:
- Subprocess output decode wedge (process snapshots, scanner telemetry) remains out-of-scope pending broker API telemetry requirements.
- Other telemetry/log ingestion paths beyond quarantine JSONL may have unprotected `.read_text()` calls requiring similar fail-closed handling.
- Remaining Phase 32 queue remains open (Step 3+): DuckDB flush optimization, exception taxonomy split, routing diagnostics tail, UID drift closure.

Rollback Note:
- Revert `main_bot_orchestrator.py` (`_read_quarantine_jsonl_safe`), `tests/test_main_bot_orchestrator.py` (test addition + retrofits), `docs/phase_brief/phase32-brief.md` (Step 2 section), `docs/decision log.md` (D-212), and this SAW report if Step 2 contract is rejected.

Next action:
- Add Step 2 lesson entry to `docs/lessonss.md` and commit Phase 32 Step 2 artifacts.
- Await CEO authorization for Phase 32 Step 3 (DuckDB flush optimization) or pivot to alternative backlog priorities.

ClosurePacket: RoundID=R20260302-PH32-S2-R1; ScopeID=PH32-S2-UTF8-DECODE-WEDGE; ChecksTotal=3; ChecksPassed=3; ChecksFailed=0; Verdict=PASS; OpenRisks=subprocess_decode_wedge_and_other_telemetry_paths_and_phase32_step3plus_backlog; NextAction=add_step2_lesson_and_commit_or_await_step3_authorization
ClosureValidation: PASS
SAWBlockValidation: PASS
