# Phase 33B Slice 4: Escalation Runtime Runbook

## Enabling Escalation in Production

### Environment Variables

Set these environment variables before starting the application:

```bash
# Master switch (required)
export ENABLE_ESCALATION=true

# Escalation timing (optional, defaults shown)
export ESCALATION_YELLOW_TTL_MINUTES=5
export ESCALATION_RED_TTL_MINUTES=2
export ESCALATION_MAX_COUNT=3
export ESCALATION_COOLDOWN_MINUTES=30
export ESCALATION_CHECK_INTERVAL=60
```

### Starting the Application

```bash
# Set environment variables
export ENABLE_ESCALATION=true

# Launch dashboard
.\.venv\Scripts\python launch.py
```

The escalation manager will automatically start when the dashboard initializes if `ENABLE_ESCALATION=true`.

## Disabling Escalation

To disable escalation immediately:

```bash
# Set flag to false
export ENABLE_ESCALATION=false

# Restart application
.\.venv\Scripts\python launch.py
```

The escalation manager will not start, and no escalations will occur.

## Monitoring Escalation

### Check Escalation Status

Query the database to see escalation activity:

```sql
-- Check escalated alerts
SELECT alert_id, taxonomy, alert_level, escalation_count, last_escalation_at
FROM alerts
WHERE escalation_count > 0
ORDER BY last_escalation_at DESC;

-- Check escalation history
SELECT alert_id, escalation_count, escalated_at, escalation_reason, channel, channel_status
FROM escalation_history
ORDER BY escalated_at DESC
LIMIT 20;
```

### Check Telemetry Events

```python
from core.telemetry_spool import TelemetrySpool

spool = TelemetrySpool(spool_path="data/telemetry/drift_events.jsonl")
events = spool.read_events()
escalation_events = [e for e in events if e["event_type"] == "escalation_triggered"]

for event in escalation_events:
    print(f"Alert: {event['data']['alert_id']}, Count: {event['data']['escalation_count']}")
```

## Smoke Testing

Run the smoke test script to verify escalation works end-to-end:

```bash
# Set fast escalation for testing
export ENABLE_ESCALATION=true
export ESCALATION_RED_TTL_MINUTES=1
export ESCALATION_YELLOW_TTL_MINUTES=1
export ESCALATION_CHECK_INTERVAL=5

# Run smoke test (as module)
.\.venv\Scripts\python -m scripts.escalation_smoke_test
```

**PowerShell equivalent:**
```powershell
$env:ENABLE_ESCALATION="true"
$env:ESCALATION_RED_TTL_MINUTES="1"
$env:ESCALATION_YELLOW_TTL_MINUTES="1"
$env:ESCALATION_CHECK_INTERVAL="5"
.\.venv\Scripts\python -m scripts.escalation_smoke_test
```

Expected output:
- ✅ Escalation count incremented
- ✅ Escalation history entry created
- ✅ Telemetry event emitted
- ✅ No escalation after acknowledgement

## Troubleshooting

### Escalation Not Working

1. Check environment variable:
   ```bash
   echo $ENABLE_ESCALATION
   ```

2. Check dashboard logs for escalation manager startup:
   ```
   EscalationManager initialized: yellow_ttl=5m, red_ttl=2m, max=3, cooldown=30m, interval=60s
   EscalationManager started
   ```

3. Check database schema:
   ```sql
   PRAGMA table_info(alerts);  -- Should have escalation_count, last_escalation_at
   SELECT * FROM escalation_history LIMIT 1;  -- Should exist
   ```

### Too Many Escalations

If alerts are escalating too frequently:

1. Increase TTL values:
   ```bash
   export ESCALATION_YELLOW_TTL_MINUTES=10
   export ESCALATION_RED_TTL_MINUTES=5
   ```

2. Increase cooldown:
   ```bash
   export ESCALATION_COOLDOWN_MINUTES=60
   ```

3. Restart application for changes to take effect.

### Escalation Manager Not Stopping

The escalation manager runs as a daemon thread and will stop automatically when the application exits. For manual control:

```python
# In dashboard.py or custom script
if "escalation_manager" in st.session_state:
    st.session_state.escalation_manager.stop(timeout=5.0)
```

## Rollback Procedure

If escalation causes issues in production:

1. **Immediate disable** (no restart required if using config reload):
   ```bash
   export ENABLE_ESCALATION=false
   ```

2. **Restart application**:
   ```bash
   # Stop current process
   # Restart with ENABLE_ESCALATION=false
   .\.venv\Scripts\python launch.py
   ```

3. **Verify escalation stopped**:
   - Check logs for "EscalationManager stopped"
   - Verify no new escalation_history entries

4. **Investigate**:
   - Review escalation_history for patterns
   - Check telemetry events for errors
   - Review alert timing and thresholds

## Production Checklist

Before enabling escalation in production:

- [ ] Environment variables configured
- [ ] Smoke test passed
- [ ] Database schema migrated (automatic on first run)
- [ ] Telemetry spool directory exists (`data/telemetry/`)
- [ ] Monitoring alerts configured for escalation events
- [ ] Rollback procedure documented and tested
- [ ] Team trained on acknowledging alerts to stop escalation

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_ESCALATION` | `false` | Master switch for escalation |
| `ESCALATION_YELLOW_TTL_MINUTES` | `5` | Minutes before YELLOW alert escalates |
| `ESCALATION_RED_TTL_MINUTES` | `2` | Minutes before RED alert escalates |
| `ESCALATION_MAX_COUNT` | `3` | Max escalations per alert |
| `ESCALATION_COOLDOWN_MINUTES` | `30` | Minutes between escalations |
| `ESCALATION_CHECK_INTERVAL` | `60` | Seconds between escalation checks |
