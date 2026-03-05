# Phase 33B Slice 3: Escalation Policy

**Status**: Complete
**Started**: 2026-03-04
**Completed**: 2026-03-05
**Owner**: System
**Phase**: 33B (Drift Monitoring - Async Automation)

## Objective

Implement escalation policy for unacknowledged drift alerts to ensure critical drift doesn't go unnoticed.

## Context

Phase 33B Slice 1-2 delivered:
- Async drift worker with lifecycle management
- Telemetry integration for observability
- Production-hardened durability semantics

Current gap: Alerts can remain unacknowledged indefinitely. No automatic escalation for critical drift.

## Acceptance Criteria

### Core Escalation Logic
- [ ] Escalate unacknowledged YELLOW alerts after 5 minutes
- [ ] Escalate unacknowledged RED alerts after 2 minutes
- [ ] Escalation checks run every 60 seconds (configurable)
- [ ] Acknowledged alerts are never escalated
- [ ] Resolved alerts are never escalated

### Escalation Actions
- [ ] Log escalation event at WARNING level
- [ ] Increment escalation counter in alert metadata
- [ ] Emit telemetry event (escalation_triggered)
- [ ] Optional: webhook/email notification (behind feature flag)

### Suppression Rules
- [ ] Max 3 escalations per alert (prevent spam)
- [ ] Cooldown period: 30 minutes between escalations for same alert
- [ ] Escalation stops when alert is acknowledged or resolved

### Testing
- [ ] Test escalation timing (YELLOW 5min, RED 2min)
- [ ] Test ack suppression (no escalation after ack)
- [ ] Test max escalation limit (stops at 3)
- [ ] Test cooldown period (30min between escalations)
- [ ] Test multi-alert scenarios (independent escalation)

## Technical Design

### Database Schema Migration

**New Columns in `alerts` table:**
```sql
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS escalation_count INTEGER DEFAULT 0;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS last_escalation_at TIMESTAMP;
CREATE INDEX IF NOT EXISTS idx_alerts_escalation ON alerts(state, alert_level, created_at, escalation_count);
```

**Migration Strategy:**
- Run migration on DriftAlertManager initialization
- Use `IF NOT EXISTS` for safe re-run on existing DBs
- Existing alerts get `escalation_count=0, last_escalation_at=NULL`
- No data loss, backward compatible

**Rollback:**
- Columns remain but unused if escalation disabled
- No DROP COLUMN needed (DuckDB supports it, but not required)

### Escalation Audit Table

**New table for durable escalation history:**
```sql
CREATE SEQUENCE IF NOT EXISTS escalation_history_seq START 1;
CREATE TABLE IF NOT EXISTS escalation_history (
    escalation_id INTEGER PRIMARY KEY DEFAULT nextval('escalation_history_seq'),
    alert_id TEXT NOT NULL,
    escalation_count INTEGER NOT NULL,
    escalated_at TIMESTAMP NOT NULL,
    escalation_reason TEXT NOT NULL,
    channel TEXT,  -- 'log', 'webhook', 'email'
    channel_status TEXT,  -- 'success', 'failed', 'skipped'
    metadata TEXT  -- JSON blob for extensibility
);
CREATE INDEX IF NOT EXISTS idx_escalation_alert ON escalation_history(alert_id, escalated_at);
```

**Purpose:**
- Durable audit trail (survives telemetry rotation/loss)
- Compliance/forensics for escalation actions
- Query: "When was alert X escalated and via what channel?"

### Atomic Escalation Gate (Race-Safe)

**Idempotent escalation update:**
```sql
UPDATE alerts
SET
    escalation_count = escalation_count + 1,
    last_escalation_at = ?
WHERE
    alert_id = ?
    AND state = 'ACTIVE'
    AND acknowledged_at IS NULL
    AND created_at <= ?  -- TTL expiry check (now - TTL)
    AND (last_escalation_at IS NULL OR last_escalation_at < ?)  -- Cooldown check
    AND escalation_count < ?  -- Max escalation check
RETURNING alert_id, escalation_count;
```

**Race Safety:**
- Single atomic UPDATE with WHERE guards
- TTL expiry enforced at DB level (created_at <= cutoff)
- Returns empty if conditions not met (already escalated, ack'd, max reached, TTL not expired)
- Multiple escalation loops won't double-escalate same alert
- Cooldown enforced at DB level

### Escalation Manager Architecture

```python
class EscalationManager:
    """
    Manages escalation policy for unacknowledged alerts.

    Lifecycle mirrors AsyncDriftWorker pattern:
    - start() spawns background thread
    - stop() signals shutdown and waits
    - health_check() returns status
    """

    def __init__(
        self,
        alert_manager: DriftAlertManager,
        yellow_ttl_minutes: int = 5,
        red_ttl_minutes: int = 2,
        max_escalations: int = 3,
        cooldown_minutes: int = 30,
        check_interval: int = 60,
        telemetry_spool: TelemetrySpool | None = None,
        worker_id: str = "escalation_manager",
    ):
        self.alert_manager = alert_manager
        self.yellow_ttl_minutes = yellow_ttl_minutes
        self.red_ttl_minutes = red_ttl_minutes
        self.max_escalations = max_escalations
        self.cooldown_minutes = cooldown_minutes
        self.check_interval = check_interval
        self.telemetry_spool = telemetry_spool
        self.worker_id = worker_id

        self._thread: threading.Thread | None = None
        self._shutdown_event = threading.Event()
        self._health = EscalationHealth(...)
        self._health_lock = threading.Lock()

    def start(self) -> None:
        """Start background escalation checker thread."""
        ...

    def stop(self, timeout: float = 5.0) -> None:
        """Stop escalation checker and wait for clean shutdown."""
        ...

    def health_check(self) -> EscalationHealth:
        """Get current health status."""
        ...

    def _escalation_loop(self) -> None:
        """Main loop: check alerts every check_interval seconds."""
        ...

    def _check_escalations(self) -> list[EscalationEvent]:
        """Check all active alerts and escalate if needed (atomic)."""
        ...

    def _escalate_alert(self, alert: AlertRecord) -> EscalationEvent | None:
        """
        Escalate single alert atomically.

        Returns None if escalation conditions not met (race lost, already ack'd, etc.)
        """
        ...
```

**Health Status:**
```python
@dataclass
class EscalationHealth:
    is_running: bool
    last_check_time: datetime | None
    total_checks: int
    total_escalations: int
    consecutive_errors: int
```

### Feature Flag Contract

**Configuration (environment variables or config file):**
```python
ENABLE_ESCALATION: bool = False  # Master switch (default: disabled)
ESCALATION_YELLOW_TTL_MINUTES: int = 5
ESCALATION_RED_TTL_MINUTES: int = 2
ESCALATION_MAX_COUNT: int = 3
ESCALATION_COOLDOWN_MINUTES: int = 30
ESCALATION_CHECK_INTERVAL: int = 60

# Channel flags (future Slice 4)
ESCALATION_ENABLE_WEBHOOK: bool = False
ESCALATION_WEBHOOK_URL: str = ""
ESCALATION_ENABLE_EMAIL: bool = False
ESCALATION_EMAIL_TO: str = ""
```

**Runtime Behavior:**
- `ENABLE_ESCALATION=False`: EscalationManager not started, no overhead
- `ENABLE_ESCALATION=True`: Manager starts with configured TTLs
- Channel flags checked at escalation time (log always enabled)
- Config changes require worker restart (no hot reload in Slice 3)

### Integration with AsyncDriftWorker
- Escalation manager runs in separate thread (independent of drift checks)
- Shares DriftAlertManager for alert state access
- Emits telemetry events to same spool
- Optional: webhook/email via pluggable escalation channels

### Escalation Event Schema
```python
{
    "event_type": "escalation_triggered",
    "timestamp": "2026-03-04T12:30:00Z",
    "worker_id": "escalation_manager",
    "data": {
        "alert_id": "abc123",
        "taxonomy": "ALLOCATION_DRIFT",
        "alert_level": "RED",
        "escalation_count": 1,
        "time_since_creation_minutes": 3.5,
        "escalation_reason": "unacknowledged_red_alert_ttl_exceeded"
    }
}
```

## Implementation Tasks

1. **Database Schema Migration**
   - Add escalation columns to `alerts` table
   - Create `escalation_history` audit table with sequence-backed PK
   - Add indexes for escalation queries
   - Run migration in DriftAlertManager.__init__()

2. **Implement EscalationManager class**
   - Lifecycle methods (start/stop/health_check)
   - Background thread with 60s check interval
   - Atomic escalation gate (UPDATE ... WHERE ... RETURNING with TTL check)
   - Durable audit logging to escalation_history table

3. **Add escalation telemetry events**
   - `escalation_triggered` event type
   - Factory function in telemetry_events.py
   - Emit alongside durable DB audit

4. **Wire into async worker lifecycle**
   - Optional escalation_manager parameter
   - Start/stop with worker
   - Share telemetry spool
   - Feature flag: ENABLE_ESCALATION

5. **Comprehensive test suite**
   - Mock time for fast execution
   - Test atomic escalation (race conditions)
   - Test all timing/suppression rules
   - Test durable audit persistence
   - Integration test with full pipeline

## Testing Strategy

### Unit Tests
- `test_escalation_manager.py`: timing, suppression, cooldown, lifecycle
- `test_escalation_atomicity.py`: race conditions, idempotency
- Mock time.time() for fast test execution
- Verify escalation count increments correctly
- Verify audit table entries created

### Integration Tests
- `test_escalation_integration.py`: full pipeline (alert → escalate → ack → stop)
- Verify telemetry events emitted
- Verify durable audit entries
- Test multi-alert scenarios
- Test feature flag behavior

### Race Condition Tests
- Simulate concurrent escalation loops
- Verify only one escalation succeeds per cooldown window
- Verify max escalation limit enforced atomically

## Rollback Plan

If escalation causes issues:
1. Set `ENABLE_ESCALATION=False` in config
2. Restart worker (escalation manager won't start)
3. Alerts remain functional (no escalation, but still visible)
4. Investigate escalation logs for root cause
5. Fix + re-enable behind feature flag

## Dependencies

- Phase 33B Slice 1-2 (async worker, telemetry)
- DriftAlertManager for alert state access
- TelemetrySpool for escalation event logging

## Risks

1. **Escalation Spam**: Too many escalations overwhelm operators
   - Mitigation: Max 3 escalations + 30min cooldown

2. **False Escalations**: Transient drift triggers unnecessary escalations
   - Mitigation: Hysteresis in alert creation (already implemented)

3. **Missed Escalations**: Escalation manager crashes/stops
   - Mitigation: Health check endpoint, telemetry monitoring

## Success Metrics

- Escalation latency <90 seconds (from TTL expiry to escalation event)
- Zero false escalations (ack'd/resolved alerts never escalated)
- Escalation spam rate <1% (max 3 per alert enforced)

## Next Steps

1. ✅ Implement EscalationManager class
2. ✅ Add escalation event schema to telemetry
3. ✅ Wire escalation manager into worker lifecycle
4. ✅ Add comprehensive tests
5. ✅ Add feature flag configuration module
6. ✅ Harden concurrency exception handling

## Runtime Integration Example

```python
from core.escalation_config import get_escalation_config
from core.escalation_manager import EscalationManager
from core.async_drift_worker import AsyncDriftWorker

# Load configuration
escalation_config = get_escalation_config()

# Create escalation manager if enabled
escalation_manager = None
if escalation_config.enabled:
    escalation_manager = EscalationManager(
        alert_manager=alert_manager,
        yellow_ttl_minutes=escalation_config.yellow_ttl_minutes,
        red_ttl_minutes=escalation_config.red_ttl_minutes,
        max_escalations=escalation_config.max_escalations,
        cooldown_minutes=escalation_config.cooldown_minutes,
        check_interval=escalation_config.check_interval,
        telemetry_spool=telemetry_spool,
        worker_id="escalation_manager",
    )

# Create worker with optional escalation manager
worker = AsyncDriftWorker(
    alert_manager=alert_manager,
    drift_detector=drift_detector,
    baseline_loader=baseline_loader,
    live_loader=live_loader,
    poll_interval=60,
    telemetry_spool=telemetry_spool,
    escalation_manager=escalation_manager,  # None if disabled
)

worker.start()
```

## Production Deployment

To enable escalation in production:

```bash
export ENABLE_ESCALATION=true
export ESCALATION_YELLOW_TTL_MINUTES=5
export ESCALATION_RED_TTL_MINUTES=2
export ESCALATION_MAX_COUNT=3
export ESCALATION_COOLDOWN_MINUTES=30
export ESCALATION_CHECK_INTERVAL=60
```

## Implementation Status

✅ **Complete** - All components implemented and tested:
- Schema migration with escalation columns and audit table
- EscalationManager with atomic race-safe escalation
- Telemetry integration with escalation_triggered events
- Worker lifecycle integration
- Feature flag configuration module (core/escalation_config.py)
- Dashboard integration with shared initialization function (core/dashboard_escalation.py)
- Comprehensive test suite (43 tests passing, 0 warnings)
- DuckDB lock resilience with exponential backoff + jitter
- Streamlit singleton lifecycle with config change detection
- Session-end cleanup via atexit handler
- 30-minute operational soak test validation

**SAW Report**: `docs/saw_reports/saw_phase33b_closeout_round1_20260305.md`

**Next Phase**: Phase 34 - Factor Attribution Analysis (`docs/phase_brief/phase34-brief.md`)
