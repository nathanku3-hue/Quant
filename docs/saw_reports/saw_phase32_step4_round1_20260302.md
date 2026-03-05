# SAW Report: Phase 32 Step 4 Exception Taxonomy Split (Round 1, 2026-03-02)

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: phase32-step4-executing | Domains: Backend, Ops, Data

RoundID: R20260302-PH32-S4-R1
ScopeID: PH32-S4-EXCEPTION-TAXONOMY
Scope: Execute binary exception taxonomy split (`TRANSIENT` vs `TERMINAL`) with deterministic routing and canonical output contracts for execution failure paths.

Ownership Check:
- Implementer: Codex (parent)
- Reviewer A: `Darwin` (`019caebe-e916-73a2-a413-8a58caeca6de`)
- Reviewer B: `Arendt` (`019caead-ac88-7e60-9372-b41db88d9ce7`)
- Reviewer C: `Curie` (`019caeb4-a416-7c12-9cab-b240de618146`)
- Result: implementer and reviewer roles are distinct.

Acceptance Checks:
- CHK-S4-01: Binary classification maps broker failures into canonical classes `TRANSIENT` or `TERMINAL`.
- CHK-S4-02: Deterministic routing applies class semantics (`TERMINAL` immediate `FAILED_REJECTED`, `TRANSIENT` bounded retry then `retry_exhausted`).
- CHK-S4-03: Test matrix validates both classes and bounded execution behavior without orchestrator crash/stall.

SAW Verdict: PASS

Findings Table:
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | `timeout<=0` reconciliation lookup path could execute synchronously and stall on hanging broker lookup | Added `EXECUTION_RECONCILIATION_LOOKUP_MIN_TIMEOUT_SECONDS=0.01`, removed synchronous branch, and added zero-timeout bounded regression | Implementer | Resolved |
| High | Taxonomy schema drift: `retry_exhausted` fields differed across branches and non-retryable row errors bypassed canonical terminal mapping | Added `_build_retry_exhausted_result(...)` and `_build_failed_rejected_result(...)`, routed all terminal/transient end states through canonical builders, and mapped row-level non-retryable terminal errors to `FAILED_REJECTED` | Implementer | Resolved |
| High | Mixed-token broker errors could still route through retry gate before terminal mapping (`401 unauthorized connection reset`) | Reordered row-level routing so `TERMINAL` classification is evaluated before retry-token checks; added mixed-token terminal precedence regression | Implementer | Resolved |
| Medium | Missing regression coverage for edge timeout config and canonical field consistency across all Step 4 branches | Added zero-timeout bounded test and expanded Step 4 assertions for canonical fields (`canonical_reason`, `exception_class`) | Implementer | Resolved |

Scope Split Summary:
- in-scope:
  - broker exception taxonomy split and routing semantics in `execute_orders_with_idempotent_retry`.
  - canonical output schema enforcement for terminal/transient terminal states.
  - bounded runtime behavior for zero/non-positive lookup timeout config.
- inherited out-of-scope:
  - Step 5 routing diagnostics tail.
  - Step 6 UID drift closure.
  - long-run bounded worker pool for uncooperative lookup threads (future hardening).

Document Changes Showing:
1. `main_bot_orchestrator.py`
   - Added canonical terminal/transient result builders.
   - Applied deterministic terminal/transient routing across batch and row-level branches.
   - Added bounded minimum lookup timeout to remove synchronous stall seam.
   - Enforced terminal-classification precedence before retry-token evaluation for row-level failures.
   - Reviewer status: A PASS, B PASS (after reconciliation), C PASS (after reconciliation).
2. `tests/test_main_bot_orchestrator.py`
   - Added `test_execute_orders_with_idempotent_retry_zero_lookup_timeout_remains_bounded`.
   - Added `test_execute_orders_terminal_exception_logs_canonical_reason`.
   - Added `test_execute_orders_with_idempotent_retry_terminal_classification_precedes_retry_tokens`.
   - Expanded existing Step 4 assertions for canonical taxonomy fields.
   - Reviewer status: A PASS, B PASS, C PASS after reconciliation.
3. `docs/phase_brief/phase32-brief.md`
   - Added Step 4 section (scope, contract, checks, evidence, risks).
   - Reviewer status: parent reconciliation.
4. `docs/decision log.md`
   - Added D-214 decision entry with implementation/evidence and contract lock.
   - Reviewer status: parent reconciliation.
5. `docs/notes.md`
   - Added Step 4 contract addendum (taxonomy, deterministic routing, canonical schema).
   - Reviewer status: parent reconciliation.
6. `docs/lessonss.md`
   - Added Step 4 lesson entry, root cause, and guardrail.
   - Reviewer status: parent reconciliation.

Evidence:
- `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py --disable-warnings` -> PASS (`74 passed in 1.50s`).
- `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
- Focused Step 4 slice:
  - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py -k "terminal_exception_bypasses_retry_immediately or transient_exception_retries_with_backoff or classify_broker_exception_terminal_cases or classify_broker_exception_transient_cases or zero_lookup_timeout_remains_bounded or terminal_exception_logs_canonical_reason" --disable-warnings`
  - -> PASS (`6 passed, 68 deselected`).
- Reviewer progression:
  - Reviewer A initial BLOCK on terminal-precedence leakage -> resolved -> PASS.
  - Reviewer B initial BLOCK on timeout stall seam -> resolved -> PASS.
  - Reviewer C initial BLOCK on schema consistency -> resolved -> PASS.

Assumptions:
- Unknown exception phrasing defaults to `TRANSIENT` to preserve bounded retry behavior rather than silent drop.
- Canonical output fields (`error`, `canonical_reason`, `exception_class`, `attempt`, `client_order_id`) are required for terminal/transient terminal-state telemetry.
- Pytest atexit temp-dir cleanup `PermissionError` is environment-level and non-blocking for command exit status.

Open Risks:
- Taxonomy indicators are string-based; unseen broker phrasing may classify unexpectedly until indicator set is expanded.
- Uncooperative lookup implementations may keep daemon worker threads alive until internal return despite timeout/cancel signaling.
- Pytest atexit cleanup noise can obscure logs in CI output (non-failing).

Rollback Note:
- Revert `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, and Step 4 docs (`docs/phase_brief/phase32-brief.md`, `docs/decision log.md`, `docs/notes.md`, `docs/lessonss.md`) if D-214 is rejected.

Next action:
- Start Phase 32 Step 5 routing diagnostics tail with deterministic route-cause taxonomy and bounded diagnostic payload controls.

ClosurePacket: RoundID=R20260302-PH32-S4-R1; ScopeID=PH32-S4-EXCEPTION-TAXONOMY; ChecksTotal=3; ChecksPassed=3; ChecksFailed=0; Verdict=PASS; OpenRisks=string_indicator_taxonomy_drift_and_uncooperative_lookup_threads_and_pytest_atexit_permissionerror_noise; NextAction=start_phase32_step5_routing_diagnostics_tail
ClosureValidation: PASS
SAWBlockValidation: PASS
