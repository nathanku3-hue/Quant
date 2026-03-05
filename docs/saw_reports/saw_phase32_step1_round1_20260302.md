# SAW Report: Phase 32 Step 1 Timeout Soak (Round 1, 2026-03-02)

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: phase32-step1-executing | Domains: Backend, Ops, Data

RoundID: R20260302-PH32-S1-R1
ScopeID: PH32-S1-TIMEOUT-SOAK
Scope: Execute deterministic timeout soak with cooperative cancellation, quarantine durability, and heartbeat-thread isolation proof.

Ownership Check:
- Implementer: Codex (parent)
- Reviewer A: `Boyle` (`019cadff-1c24-7d42-94ae-4238b66c50ea`)
- Reviewer B: `Kepler` (`019cadff-1c41-7fc2-9bec-b7a0eaf50ea7`)
- Reviewer C: `Bacon` (`019cadff-1c82-7891-b41c-d357ee2ce3e3`)
- Result: implementer and reviewer roles are distinct.

Acceptance Checks:
- CHK-S1-01: Cooperative cancellation token path surfaces canonical cancellation taxonomy.
- CHK-S1-02: Timeout/cancel/exception ambiguity is quarantined before raise.
- CHK-S1-03: Blocked reconciliation lookup thread does not wedge heartbeat telemetry spool flush.
- CHK-S1-04: Quarantine sink is deterministic and lossless under concurrent writers.
- CHK-S1-05: Mixed-poll lookup issue precedence preserves forensic lookup taxonomy.

SAW Verdict: PASS

Findings Table:
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Lookup timeout/cancel issue could be overwritten by later generic poll labels, weakening taxonomy and suppressing expected quarantine family | Added sticky lookup issue precedence and preserved highest-priority lookup issue across poll loop | Implementer | Resolved |
| High | Non-cooperative timed-out lookup could spawn additional hanging workers across polls | Added `lookup_timeout:<seconds>:uncooperative` terminal classification with early return from reconciliation poll loop | Implementer | Resolved |
| High | Quarantine JSONL append could lose/corrupt rows under concurrent writers | Added lock-serialized append with low-level `O_APPEND` write + `fsync` and regression for concurrent writers | Implementer | Resolved |
| Medium | Quarantine schema drift risk was under-tested | Added explicit schema key assertions and `schema_version=1` contract in tests | Implementer | Resolved |

Scope Split Summary:
- in-scope:
  - cooperative cancellation + timeout taxonomy handling in reconciliation lookup path.
  - deterministic quarantine writer durability/integrity for lookup ambiguity evidence.
  - synthetic chaos thread-isolation soak proof against telemetry spool flush path.
- inherited out-of-scope:
  - UTF-8 decode wedge backlog (Phase 32 Step 2).
  - DuckDB flush optimization backlog (Phase 32 Step 3).

Document Changes Showing:
1. `main_bot_orchestrator.py`
   - Cooperative cancel injection, sticky lookup issue precedence, uncooperative timeout classification, lock-serialized durable quarantine append.
   - Reviewer status: A PASS, B PASS, C PASS after reconciliation.
2. `tests/test_main_bot_orchestrator.py`
   - Synthetic chaos adapter, cancellation + quarantine regressions, mixed-poll precedence regression, heartbeat isolation soak, concurrent quarantine-writer regression.
   - Reviewer status: A PASS, B PASS, C PASS after reconciliation.
3. `docs/phase_brief/phase32-brief.md`
   - Added Phase 32 Step 1 scope, acceptance checks, formula/contract lock, and evidence.
   - Reviewer status: parent reconciliation.
4. `docs/decision log.md`
   - Added D-211 decision entry for Step 1 close.
   - Reviewer status: parent reconciliation.
5. `docs/notes.md`
   - Added Step 1 implementation note block and formulas.
   - Reviewer status: parent reconciliation.
6. `docs/lessonss.md`
   - Added round lesson and guardrail from reviewer-driven reconciliation.
   - Reviewer status: parent reconciliation.

Evidence:
- `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py` -> PASS (`65 passed`).
- `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
- Reviewer outputs:
  - Reviewer A: identified taxonomy precedence downgrade risk -> resolved.
  - Reviewer B: identified uncooperative worker accumulation risk -> resolved.
  - Reviewer C: identified concurrent quarantine append integrity risk -> resolved.

Assumptions:
- Current lock-based quarantine append semantics are sufficient for orchestrator process concurrency envelope.
- Pytest post-suite temp-dir cleanup `PermissionError` is environment-level and non-blocking for test verdicts.

Open Risks:
- Inter-process lock stress across independently spawned orchestrator processes remains an operational soak follow-up.
- Remaining Phase 32 queue remains open (Step 2+): UTF-8 decode wedge reconciliation, DuckDB flush optimization, taxonomy split follow-through.

Rollback Note:
- Revert `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, and docs entries created in this round if Step 1 contract is rejected.

Next action:
- Start Phase 32 Step 2 UTF-8 decode wedge reconciliation using deterministic malformed-byte fixtures and fail-closed quarantine assertions.

ClosurePacket: RoundID=R20260302-PH32-S1-R1; ScopeID=PH32-S1-TIMEOUT-SOAK; ChecksTotal=5; ChecksPassed=5; ChecksFailed=0; Verdict=PASS; OpenRisks=interprocess_lock_stress_and_phase32_step2plus_backlog; NextAction=start_phase32_step2_utf8_decode_wedge_reconciliation
ClosureValidation: PASS
SAWBlockValidation: PASS
