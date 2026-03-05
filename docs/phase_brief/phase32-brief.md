# Phase 32: SRE Backlog - Timeout Soak, UTF-8 Wedge, DuckDB Flush, and Exception Taxonomy Split

Status: In Progress (Steps 1-4 Complete; Step 5/M1 queued for approval)
Owner: Backend/Ops/Data
Date: 2026-03-02

## 0) Live Loop State
- L1 (Project Pillar): Backtest Engine (Signal System)
- L2 Active Streams: Backend, Ops, Data
- L2 Deferred Streams: Frontend/UI
- L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- Active Stream: Backend/Ops/Data
- Active Stage Level: L3
- Current Stage: Executing
- Planning Gate Boundary: Steps 1-4 (reconciliation timeout soak + UTF-8 decode wedge + DuckDB flush optimization + exception taxonomy split)
- Owner/Handoff: Implementer (Codex parent) -> Reviewer A/B/C SAW pass
- Acceptance Checks: CHK-S1-01..CHK-S1-05 (Step 1), CHK-S2-01..CHK-S2-03 (Step 2), CHK-S3-01..CHK-S3-03 (Step 3), CHK-S4-01..CHK-S4-03 (Step 4)
- Primary Next Scope: Step 5/M1 scheduled-maintenance blackout circuit (queued)

## 1) Scope
- Implement deterministic synthetic-chaos reconciliation soak coverage.
- Enforce cooperative cancellation token semantics in reconciliation lookup timeout flow.
- Quarantine timeout/cancel/lookup exception ambiguity records to dedicated JSONL sink with durable append semantics.
- Prove blocked reconciliation lookup does not wedge telemetry heartbeat spool flush.

## 2) Implementation Summary
- `main_bot_orchestrator.py`
  - Added cooperative cancellation path in `_poll_lookup_with_timeout(...)` with optional `cancel_event` injection when broker lookup supports it.
  - Added canonical cancellation taxonomy: `lookup_cancelled`.
  - Added uncooperative timeout taxonomy suffix: `lookup_timeout:<seconds>:uncooperative`.
  - Added sticky lookup issue precedence so `lookup_*` taxonomy is preserved across multi-poll reconciliation attempts.
  - Added deterministic reconciliation quarantine sink:
    - path constant `EXECUTION_RECONCILIATION_QUARANTINE_PATH`,
    - durable low-level append (`os.open + O_APPEND + os.write + fsync`),
    - lock file serialization for concurrent writers,
    - schema-stable payload with `schema_version=1`.
  - Added early return for uncooperative timeout issue so subsequent polls do not spawn additional hanging lookup workers.
- `tests/test_main_bot_orchestrator.py`
  - Added synthetic-chaos broker adapter with cooperative cancellation behavior.
  - Added cancellation regression with quarantine assertion.
  - Added mixed-poll taxonomy preservation regression (`cancelled -> unavailable` sequence).
  - Added thread-isolation soak proving reconciliation block does not wedge telemetry spool flush.
  - Added concurrent quarantine-writer integrity regression.
  - Upgraded timeout regression to assert uncooperative timeout classification and quarantine schema contract.

## 3) Formula / Contract Lock
- `lookup_result := get_order_by_client_order_id(client_order_id, cancel_event=token?)`.
- `if lookup exceeds timeout and worker still alive after cancel grace: issue=lookup_timeout:<t>s:uncooperative`.
- `if lookup raises asyncio.CancelledError: issue=lookup_cancelled`.
- `if any poll emits lookup_* issue: final reconciliation issue preserves highest-severity lookup_* taxonomy (sticky precedence)`.
- `if reconciliation unresolved AND issue family in {lookup_timeout, lookup_cancelled, lookup_exception}: append quarantine row before AmbiguousExecutionError is raised`.
- `quarantine_row := durable_append(JSONL, schema_version=1, fsync, serialized writer lock)`.

## 4) Acceptance Checks
- CHK-S1-01 Cooperative cancellation token path is exercised and `lookup_cancelled` is surfaced -> PASS.
- CHK-S1-02 Cancellation taxonomy is propagated into `AmbiguousExecutionError` and quarantine rows -> PASS.
- CHK-S1-03 Blocked reconciliation lookup does not block heartbeat/telemetry spool flush -> PASS.
- CHK-S1-04 Reconciliation quarantine sink writes deterministic JSONL rows with schema contract under concurrent writers -> PASS.
- CHK-S1-05 Mixed poll issue precedence and uncooperative timeout bounded behavior are fail-loud and deterministic -> PASS.

## 5) Evidence
- `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py` -> PASS (`65 passed`).
- `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
- Known environment artifact: pytest emits non-failing atexit temp-dir cleanup `PermissionError` (`...pytest-current`) after suite completion.

## 6) Open Risks
- Inter-process lock semantics depend on OS-level file-lock behavior; current regression validates concurrent threads in-process and normal orchestrator operation.
- Long-run daemon lookup thread elimination for completely uncooperative third-party clients is bounded per reconciliation attempt (early return) but still relies on daemon lifecycle for eventual thread teardown.

## 7) Rollback Note
- Revert `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, and this brief if Step 1 contract is rejected.

---

## Step 2: UTF-8 Decode Wedge Reconciliation

### 1) Scope
- Implement fail-closed UTF-8 decode error handling in quarantine JSONL ingestion/replay path.
- Add deterministic malformed-byte fixture with synthetic UTF-8 decode error.
- Prove ingestion/replay boundaries remain operational (no wedge) when external sources introduce corrupted data.
- Ensure quarantine schema contract is preserved under decode errors.

### 2) Implementation Summary
- `main_bot_orchestrator.py`
  - Added `_read_quarantine_jsonl_safe()` helper with `errors='replace'` decode policy.
  - Converts malformed UTF-8 bytes to U+FFFD replacement character (\ufffd) instead of raising `UnicodeDecodeError`.
  - Includes JSON parse error recovery with warning log and graceful skip.
  - Returns list of valid quarantine rows even when file contains corrupted data.
- `tests/test_main_bot_orchestrator.py`
  - Added `test_read_quarantine_jsonl_safe_handles_malformed_utf8()` with deterministic malformed-byte fixture.
  - Added `test_read_quarantine_jsonl_safe_skips_malformed_json_lines()` to exercise JSON parse-recovery skip path.
  - Proves unsafe `.read_text(encoding="utf-8")` wedges with `UnicodeDecodeError`.
  - Proves safe reader handles malformed bytes gracefully with replacement characters.
  - Updated all 5 existing quarantine read calls to use safe reader (lines formerly 2461, 2506, 2576, 2605, 2647).

### 3) Formula / Contract Lock
- `quarantine_rows := _read_quarantine_jsonl_safe(path)`.
- `if file contains malformed UTF-8: replace invalid bytes with U+FFFD (\ufffd) and continue`.
- `if line contains invalid JSON: log warning, skip line, continue with remaining lines`.
- `quarantine schema contract preserved: {schema_version, client_order_id, reconciliation_issue, ...}`.
- `ingestion/replay boundary never wedges: always returns list[dict] (possibly empty on total failure)`.

### 4) Acceptance Checks
- CHK-S2-01 Malformed UTF-8 byte fixture raises `UnicodeDecodeError` with unsafe reader -> PASS.
- CHK-S2-02 Safe reader handles malformed UTF-8 gracefully with replacement characters and preserves valid rows -> PASS.
- CHK-S2-03 Quarantine replay tests pass with safe reader retrofit and malformed-JSON skip coverage -> PASS.

### 5) Evidence
- `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py --disable-warnings` -> PASS (`71 passed in 1.45s`).
- `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
- Malformed UTF-8 fixture: `b'{"schema_version":1,"client_order_id":"cid-malformed","reconciliation_issue":"error_\xff\xfe_invalid"}\n'` (0xFF,0xFE are invalid UTF-8).
- Safe reader output includes replacement character: `"\ufffd"` in `reconciliation_issue` field.

### 6) Open Risks
- Current scope addresses quarantine JSONL replay; other telemetry/log ingestion paths may still have unprotected `.read_text()` calls.
- Subprocess output decode wedge (e.g., process snapshot queries) remains out-of-scope pending broker API telemetry requirements.

### 7) Rollback Note
- Revert `main_bot_orchestrator.py` (`_read_quarantine_jsonl_safe` addition), `tests/test_main_bot_orchestrator.py` (test additions and safe reader retrofits), and this brief Step 2 section if contract is rejected.

---

## Step 3: DuckDB Flush Optimization (O(N) → O(1) Telemetry Spool)

### 1) Scope
- Eradicate O(N) scaling in telemetry spool flush path by removing full-table COUNT(*) scans.
- Implement indexed deduplication lookups for O(log N) NOT EXISTS checks instead of O(N) table scans.
- Replace pre-count/post-count pattern with direct row-count calculation from INSERT SELECT result.
- Optimize export path to detect end-of-table via batch size instead of pre-counting total rows.
- Preserve fail-closed durability guarantee with MicrostructureFlushError on disk failures.

### 2) Implementation Summary
- `execution/microstructure.py` (`_append_duckdb_table_rows`):
  - **Removed**: two O(N) COUNT(*) FROM table scans (before_count + after_count at lines 772, 785).
  - **Added**: CREATE INDEX on `_spool_record_uid` for O(log N) deduplication lookups.
  - **Added**: Pre-compute inserted row count by executing SELECT ... WHERE NOT EXISTS query before INSERT.
  - **Result**: Flush cost changes from O(2N) table scans to O(M log N) where M=batch size, N=table size.
  - **Bottleneck shifted**: From "table size" (grows all day) to "batch size" (constant per flush).
- `execution/microstructure.py` (`_export_duckdb_table_to_parquet`):
  - **Removed**: O(N) COUNT(*) FROM table scan for total_rows calculation (line 859).
  - **Added**: PRAGMA table_info() metadata check (O(1)) for table existence validation.
  - **Added**: End-of-table detection via actual rows fetched vs batch_size (no pre-counting).
  - **Added**: EOF cursor retention (no automatic rewind on empty fetch) so tail appends are exported on the next flush cycle without an extra rewind pass.
  - **Result**: Export cost changes from O(N) full scan to O(1) metadata + O(M log N) batch fetch, with deterministic tail-cursor continuity at EOF.
- `execution/microstructure.py` (`_TelemetrySpooler.stop`, `_shutdown_execution_microstructure_spoolers`):
  - **Hardened**: fail-closed shutdown now raises `MicrostructureFlushError` when any of these remain at stop boundary:
    - `pending_bytes > 0`, or
    - `buffer_drop_count > 0`, or
    - `last_flush_error` is non-empty.
  - **Result**: sink-failure classes (for example disk-full export failure) cannot silently pass shutdown when pending bytes happen to be zero.

### 3) Formula / Contract Lock
- `inserted_rows := COUNT(*) FROM (SELECT ... WHERE NOT EXISTS ...)` ← count BEFORE insert, not entire table.
- `CREATE INDEX IF NOT EXISTS idx_{table}_spool_uid ON {table}(_spool_record_uid)` ← O(log N) lookups.
- `NOT EXISTS (SELECT 1 FROM {table} WHERE uid = new_uid)` ← O(log N) with index, not O(N) scan.
- `export_df := LIMIT {batch_size} OFFSET {start_row}` ← fetch batch, check result size for end-of-table.
- `if len(export_df) < batch_size: reached end-of-table` ← no pre-count needed.
- `cursor := start_row + actual_rows_fetched` ← track progress via actual rows, not pre-computed total.

### 4) Acceptance Checks
- CHK-S3-01 Flush path removes O(N) COUNT(*) table scans and uses indexed deduplication -> PASS.
- CHK-S3-02 Export path removes O(N) COUNT(*) and detects end-of-table via batch size -> PASS.
- CHK-S3-03 All microstructure tests pass with optimized implementation and shutdown durability reconciliation -> PASS (`44/44`).

### 5) Evidence
- `.venv\Scripts\python -m pytest tests/test_execution_microstructure.py --disable-warnings` -> PASS (`44 passed in 21.05s`).
- `.venv\Scripts\python -m py_compile execution/microstructure.py tests/test_execution_microstructure.py` -> PASS.
- Before: `COUNT(*) FROM table` (line 772, 785, 859) = 3 full table scans per flush cycle.
- After: `CREATE INDEX + SELECT COUNT(*) FROM (insert_query)` = O(log N) indexed lookups only.
- Bottleneck: **table size** (O(N), unbounded growth) → **batch size** (O(M), constant per flush).

### 6) Open Risks
- Index maintenance overhead: CREATE INDEX IF NOT EXISTS adds one-time index creation cost on first flush; subsequent flushes benefit from indexed lookups.
- Cursor drift self-heal: EOF cursor rewind was removed to prevent tail-export delay; if an external process truncates/rebuilds DuckDB tables out-of-band, manual cursor reset may be required.

### 7) Rollback Note
- Revert `execution/microstructure.py` (both `_append_duckdb_table_rows` and `_export_duckdb_table_to_parquet` optimizations) and this brief Step 3 section if contract is rejected.

---

## Step 4: Exception Taxonomy Split (TRANSIENT vs TERMINAL)

### 1) Scope
- Split broker execution exception handling into strict binary taxonomy classes: `TRANSIENT` and `TERMINAL`.
- Route `TRANSIENT` failures through bounded retry semantics; route `TERMINAL` failures through immediate fail-closed rejection.
- Ensure row-level and batch-level terminal/transient outcomes emit deterministic canonical fields for downstream telemetry.
- Prove non-positive reconciliation timeout remains bounded (no synchronous stall path).

### 2) Implementation Summary
- `main_bot_orchestrator.py`
  - Added `_classify_broker_exception(exc)` binary taxonomy mapping:
    - terminal indicators: validation/business rule failures, broker hard rejects, and 4xx client failures.
    - transient indicators: network/timeout/5xx/rate-limit failures.
    - default unknown -> `TRANSIENT` (bounded retry safety).
  - Added canonical result constructors:
    - `_build_retry_exhausted_result(...)` for all transient exhausted paths.
    - `_build_failed_rejected_result(...)` for terminal fail-closed paths.
  - Enforced deterministic routing:
    - batch exception classified `TERMINAL` -> immediate `FAILED_REJECTED`, no retry loop continuation.
    - batch exception classified `TRANSIENT` -> bounded retries then canonical `retry_exhausted`.
    - row-level non-retryable error classified `TERMINAL` -> canonical `FAILED_REJECTED` (no raw pass-through).
    - terminal precedence hardened: row-level `TERMINAL` classification is evaluated before retry-token gate so mixed-token errors (for example `401 unauthorized connection reset`) fail closed immediately.
  - Added canonical terminal exception log line including reason token.
  - Hardened lookup timeout helper:
    - removed synchronous lookup execution for `timeout<=0`,
    - added minimum bounded async timeout (`EXECUTION_RECONCILIATION_LOOKUP_MIN_TIMEOUT_SECONDS=0.01`).
- `tests/test_main_bot_orchestrator.py`
  - Added zero-timeout bounded regression (`timeout=0.0` still returns bounded timeout ambiguity).
  - Added canonical terminal logging regression.
  - Expanded existing Step 4 assertions to enforce canonical taxonomy fields across terminal/transient branches.

### 3) Formula / Contract Lock
- `exception_class := _classify_broker_exception(exc)` where `exception_class in {TRANSIENT, TERMINAL}`.
- Batch exception routing:
  - `if exception_class == TERMINAL -> result.error=FAILED_REJECTED, exception_class=TERMINAL, bypass retry loop`.
  - `if exception_class == TRANSIENT -> bounded retry; on exhaustion result.error=retry_exhausted, exception_class=TRANSIENT`.
- Row-level non-retryable routing:
  - `if _is_retryable_execution_error(error_text) == False and classifier(error_text) == TERMINAL -> FAILED_REJECTED`.
- Non-positive lookup timeout safety:
  - `effective_timeout := max(timeout_seconds, 0.01)` to prevent synchronous indefinite lookup stall.

### 4) Acceptance Checks
- CHK-S4-01 Binary taxonomy mapping into canonical classes (`TRANSIENT`/`TERMINAL`) is deterministic -> PASS.
- CHK-S4-02 Routing is deterministic: terminal bypasses retry and transient exhausts bounded retry -> PASS.
- CHK-S4-03 Test matrix validates both classes and bounded runtime behavior without main-loop crash -> PASS.

### 5) Evidence
- `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py --disable-warnings` -> PASS (`74 passed in 1.50s`).
- `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py` -> PASS.
- Focused Step 4 slice:
  - `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py -k "terminal_exception_bypasses_retry_immediately or transient_exception_retries_with_backoff or classify_broker_exception_terminal_cases or classify_broker_exception_transient_cases or zero_lookup_timeout_remains_bounded or terminal_exception_logs_canonical_reason" --disable-warnings`
  - -> PASS (`6 passed, 68 deselected`).

### 6) Open Risks
- Taxonomy remains indicator-string based; unseen broker error phrasing can still map to `TRANSIENT` fallback.
- Uncooperative broker lookup implementations can still leave daemon worker threads alive until internal return.
- Pytest atexit temp cleanup `PermissionError` is environment-level log noise (non-failing).

### 7) Rollback Note
- Revert `main_bot_orchestrator.py`, `tests/test_main_bot_orchestrator.py`, and this brief Step 4 section if contract is rejected.

---

## Step 5 (M1): Scheduled Maintenance Blackout Circuit (Approval-Gated)

### 1) Scope
- Add explicit maintenance blackout classification to avoid misrouting planned provider downtime as generic transient infrastructure failure.
- Add env/config-driven blackout window sourcing (no hardcoded temporal constants in execution logic).
- Patch all required control points to avoid retry storms and unhandled exception crashes:
  - `core/data_orchestrator.py`
  - `execution/microstructure.py`
  - `main_bot_orchestrator.py`
- Keep this step strictly operational-hardening scope (no Rank 2 institutional data migration in this sprint).

### 2) Resolved Ambiguities (Locked for M1)
- **Exception taxonomy decision**: Method A adopted.
  - Add explicit class/token: `MAINTENANCE_BLACKOUT`.
  - Do not fold planned maintenance into generic `TRANSIENT`.
- **Blackout window sourcing**: Method B adopted.
  - Source maintenance windows from env/config (Twelve-Factor config discipline).
  - Hardcoded date/time values are forbidden in core runtime routing logic.
- **Patch scope decision**: Method B adopted.
  - Patch data layer + microstructure + orchestrator together.
  - Reason: sensor/controller contract; orchestrator is retry locus and must handle maintenance class explicitly.

### 3) Operational Timing Context (Absolute Time Lock)
- Known provider maintenance trigger context:
  - Saturday, **2026-03-07 09:00 ET**
  - Equivalent UTC: **2026-03-07 14:00 UTC**
- Runtime logic must not hardcode this window; this timestamp is operational context for this sprint and test fixtures.

### 4) Formula / Contract Lock
- `exception_class := classify(error)` where:
  - `MAINTENANCE_BLACKOUT` => park/open-circuit behavior (no retry storm)
  - `TRANSIENT` => bounded retry with backoff
  - `TERMINAL` => immediate fail-closed reject
- `blackout_windows := parse_env_config(TZ_MAINTENANCE_WINDOWS_JSON | equivalent)`
- `if now in blackout_window and provider_error matches maintenance signature -> MAINTENANCE_BLACKOUT`
- `MAINTENANCE_BLACKOUT routing`:
  - orchestrator returns clean parked state (planned pause semantics)
  - no infinite retries
  - bounded/noisy-log suppression
- `resume_condition := now >= blackout_window_end` (or window absent/disabled by config refresh)

### 5) Implementation Plan (No Code Applied Yet)
- `core/data_orchestrator.py`
  - Add maintenance signature detection helper for provider outages (`503`, maintenance phrases, timeout+window context).
  - Emit explicit maintenance-class signal to callers (typed exception or canonical status payload).
- `main_bot_orchestrator.py`
  - Extend exception routing to recognize `MAINTENANCE_BLACKOUT`.
  - Add parked-path behavior: deterministic sleep/backoff strategy and clean terminal semantics for planned blackout.
  - Ensure maintenance class bypasses generic transient retry loop.
- `execution/microstructure.py`
  - Add maintenance-aware flush loop handling to avoid rapid retry churn during blackout windows.
  - Preserve fail-closed durability semantics while preventing log flood/retry storm during planned maintenance.

### 6) Acceptance Checks (Planned)
- CHK-S5-01 `503/maintenance` signatures during active blackout window classify as `MAINTENANCE_BLACKOUT`.
- CHK-S5-02 Out-of-window `503` remains `TRANSIENT` and uses bounded retry semantics.
- CHK-S5-03 Orchestrator handles `MAINTENANCE_BLACKOUT` without unhandled exception and without retry thrash.
- CHK-S5-04 Microstructure path remains bounded (no tight-loop retry storm / no log flood pattern).
- CHK-S5-05 Planned blackout path exits or parks cleanly with deterministic status semantics.
- CHK-S5-06 Regression safety: existing Step 1-4 contracts remain green.

### 7) Test/Artifact Plan (Planned)
- New tests:
  - `tests/test_data_orchestrator_maintenance.py`
  - `tests/test_execution_microstructure_maintenance.py`
- Extended tests:
  - `tests/test_main_bot_orchestrator.py` maintenance taxonomy/routing cases
- Planned verification commands:
  - `.venv\Scripts\python -m py_compile core/data_orchestrator.py execution/microstructure.py main_bot_orchestrator.py`
  - `.venv\Scripts\python -m pytest -q tests/test_data_orchestrator_maintenance.py tests/test_execution_microstructure_maintenance.py tests/test_main_bot_orchestrator.py -k "maintenance or blackout"`

### 8) Open Risks
- Provider may change maintenance signaling text while still returning HTTP 503; signature matching must be resilient and auditable.
- Window-source misconfiguration (bad JSON/invalid timezone) can route incorrectly; parser must fail loudly with safe defaults.
- If only partial patch is applied (for example data layer only), orchestrator crash risk remains.

### 9) Rollback Note
- If Step 5 contract is rejected or fails verification, revert only Step 5/M1 changes and keep Steps 1-4 intact.
- Maintain current fail-closed protections from Steps 1-4 as non-regression baseline.
