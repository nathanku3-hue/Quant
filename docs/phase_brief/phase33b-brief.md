# Phase 33B: Async Drift Pipeline

**Status**: Complete
**Started**: 2026-03-04
**Completed**: 2026-03-05
**Owner**: System
**Phase**: 33B (Drift Monitoring - Async Automation)

## Objective

Transform manual drift monitoring into a reliable, non-blocking async pipeline that continuously monitors allocation drift and escalates unacknowledged alerts.

## Context

Phase 33A delivered:
- Baseline registry with immutable identity (Step 1-2)
- Drift detection with statistical normalization (Step 3-4)
- Alert persistence with DuckDB (Step 5-6)
- Baseline pointer system for UI integration (Step 7)

Current gap: Drift checks are manual (button-triggered). Operators must remember to check. No automatic escalation for critical drift.

## Acceptance Criteria

### Slice 3: Escalation Policy
- [x] Escalate unacknowledged YELLOW alerts after 5 minutes
- [x] Escalate unacknowledged RED alerts after 2 minutes
- [x] Escalation actions: log warning, increment counter, emit telemetry
- [x] Tests: escalation timing, ack suppression, multi-alert scenarios
- [x] Atomic race-safe escalation with UPDATE...WHERE...RETURNING
- [x] DuckDB lock resilience with exponential backoff + jitter
- [x] Max 3 escalations per alert (prevent spam)
- [x] 30-minute cooldown between escalations
- [x] Durable audit trail in escalation_history table

### Slice 4: Feature Flag & Dashboard Integration
- [x] Add `ENABLE_ESCALATION` feature flag (default: False)
- [x] Configuration module with environment variable loading
- [x] Dashboard integration with shared initialization function
- [x] Streamlit singleton lifecycle with config change detection
- [x] Session-end cleanup via atexit handler
- [x] Tests: flag toggle behavior, lifecycle, integration

## Technical Design

### Worker Architecture
```
AsyncDriftWorker (core/async_drift_worker.py)
  ├─ start() → spawns background thread
  ├─ stop() → sets shutdown event, joins thread
  ├─ _poll_loop() → while not shutdown:
  │    ├─ load baseline + live weights
  │    ├─ detect drift (DriftDetector)
  │    ├─ normalize scores (DriftScoreNormalizer)
  │    ├─ persist alerts (DriftAlertManager)
  │    ├─ check escalation policy
  │    ├─ emit telemetry
  │    └─ sleep(poll_interval)
  └─ health_check() → returns last_check_time, error_count
```

### Concurrency Safety
- DuckDB writes are atomic (alert manager handles locking)
- Baseline/live weight reads are read-only (no lock needed)
- Worker uses threading.Event for clean shutdown
- No shared mutable state between worker and UI thread

### Error Handling
- Catch all exceptions in poll loop (log + continue)
- Track consecutive error count (stop after 10 consecutive failures)
- Exponential backoff on repeated errors (60s → 120s → 240s)
- Health check exposes error state to dashboard

## Rollback Plan

If async worker causes runtime instability:
1. Set `ENABLE_ASYNC_DRIFT_MONITOR=False` in config
2. Restart dashboard (worker won't start)
3. Manual drift checks remain functional (Phase 33A Step 7)
4. Investigate worker logs for root cause
5. Fix + re-enable behind feature flag

## Dependencies

- Phase 33A Step 1-7 (baseline registry, drift detection, alert persistence)
- DuckDB for alert storage (already integrated)
- threading module (Python stdlib)
- Optional: telemetry system integration (can stub initially)

## Testing Strategy

### Unit Tests
- `test_async_drift_worker.py`: lifecycle, poll cycle, error handling
- `test_escalation_policy.py`: timing, ack suppression, multi-alert

### Integration Tests
- `test_async_drift_integration.py`: full pipeline (baseline → detect → alert → escalate)
- Mock time.sleep() for fast test execution
- Verify DuckDB alert persistence in background thread

### Smoke Tests
- Start dashboard with worker enabled
- Verify worker status indicator shows "Running"
- Trigger drift condition (modify live weights)
- Verify alert appears within 60 seconds
- Acknowledge alert, verify no escalation
- Stop dashboard, verify worker shuts down cleanly

## Risks

1. **Lock Contention**: DuckDB writes from worker + UI thread
   - Mitigation: Alert manager uses connection pooling + retry logic

2. **Thread Leaks**: Worker not stopping on dashboard shutdown
   - Mitigation: Use daemon=False + explicit join() with timeout

3. **False Positive Escalations**: Noisy alerts trigger spam
   - Mitigation: Escalation policy requires sustained drift (2+ consecutive checks)

4. **Performance Impact**: 60s polling adds CPU/memory overhead
   - Mitigation: Profile worker loop, optimize if >5% CPU usage

## Success Metrics

- Worker uptime >99.9% (no crashes in 7-day test)
- Alert latency <90 seconds (from drift occurrence to alert creation)
- Zero thread leaks (clean shutdown in 100 consecutive restarts)
- Escalation accuracy >95% (no false escalations, no missed critical alerts)

## Implementation Status

✅ **Phase 33B Complete** (2026-03-05)

**Delivered**:
- Escalation manager with atomic race-safe logic
- DuckDB lock resilience (exponential backoff + jitter)
- Streamlit singleton lifecycle with config change detection
- Session-end cleanup via atexit handler
- Shared dashboard initialization function (test fidelity)
- 43 tests passing (0 warnings)
- 30-minute operational soak test validation

**Test Coverage**:
- `tests/test_escalation_manager.py` (13 tests)
- `tests/test_escalation_atomicity.py` (7 tests)
- `tests/test_escalation_integration.py` (9 tests)
- `tests/test_escalation_config.py` (6 tests)
- `tests/test_dashboard_escalation_lifecycle.py` (5 tests)
- `tests/test_dashboard_integration.py` (3 tests)

**Documentation**:
- SAW Report: `docs/saw_reports/saw_phase33b_closeout_round1_20260305.md`
- Soak Test Evidence: `data/processed/phase33b_soak_evidence.json`
- Lessons Learned: `docs/lessonss.md` (Phase 33B entry)

**Next Phase**: Phase 34 - Factor Attribution Analysis (`docs/phase_brief/phase34-brief.md`)

## Next Steps

Phase 33B is complete. Proceed to Phase 34 (Factor Attribution Analysis) to build causal clarity on alpha drivers and inform subsequent optimization phases (sizing, risk budget, rebalancing).
