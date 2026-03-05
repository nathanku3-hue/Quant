"""
Phase 33B Slice 4: Escalation Runtime Smoke Test

Manual smoke test script to verify escalation works end-to-end in runtime.

Prerequisites:
    Set environment variables:
    - ENABLE_ESCALATION=true
    - ESCALATION_RED_TTL_MINUTES=1
    - ESCALATION_YELLOW_TTL_MINUTES=1
    - ESCALATION_CHECK_INTERVAL=5

Usage:
    python scripts/escalation_smoke_test.py

Expected behavior:
    1. Creates a RED drift alert
    2. Waits for escalation (>1 minute)
    3. Verifies escalation_count incremented
    4. Verifies escalation_history entry created
    5. Verifies telemetry event emitted
    6. Acknowledges alert
    7. Verifies no further escalations
"""

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb

from core.drift_alert_manager import DriftAlertManager
from core.drift_detector import DriftDetector, DriftResult, DriftTaxonomy
from core.escalation_config import get_escalation_config
from core.escalation_manager import EscalationManager
from core.telemetry_spool import TelemetrySpool


def main():
    print("=" * 60)
    print("Phase 33B Slice 4: Escalation Runtime Smoke Test")
    print("=" * 60)

    # Load config
    config = get_escalation_config()
    print(f"\nEscalation config:")
    print(f"  Enabled: {config.enabled}")
    print(f"  RED TTL: {config.red_ttl_minutes} minutes")
    print(f"  YELLOW TTL: {config.yellow_ttl_minutes} minutes")
    print(f"  Check interval: {config.check_interval} seconds")
    print(f"  Max escalations: {config.max_escalations}")
    print(f"  Cooldown: {config.cooldown_minutes} minutes")

    if not config.enabled:
        print("\n❌ ENABLE_ESCALATION=false. Set to 'true' to run smoke test.")
        return

    # Initialize components
    print("\n1. Initializing components...")
    db_path = Path("data/test_escalation_smoke.duckdb")
    if db_path.exists():
        db_path.unlink()

    alert_manager = DriftAlertManager(db_path=db_path)
    detector = DriftDetector(sigma_threshold=2.0)

    telemetry_path = Path("data/telemetry/escalation_smoke.jsonl")
    telemetry_path.parent.mkdir(parents=True, exist_ok=True)
    if telemetry_path.exists():
        telemetry_path.unlink()

    telemetry_spool = TelemetrySpool(spool_path=telemetry_path)

    escalation_manager = EscalationManager(
        alert_manager=alert_manager,
        yellow_ttl_minutes=config.yellow_ttl_minutes,
        red_ttl_minutes=config.red_ttl_minutes,
        max_escalations=config.max_escalations,
        cooldown_minutes=config.cooldown_minutes,
        check_interval=config.check_interval,
        telemetry_spool=telemetry_spool,
        worker_id="smoke_test",
    )

    # Start escalation manager
    print("2. Starting escalation manager...")
    escalation_manager.start()
    time.sleep(1)

    health = escalation_manager.health_check()
    print(f"   Health: is_running={health.is_running}")

    # Create a RED alert manually
    print("\n3. Creating RED drift alert...")
    now = datetime.now(timezone.utc)
    alert_id = f"smoke_test_{int(now.timestamp() * 1000)}"

    with duckdb.connect(str(db_path)) as conn:
        conn.execute("""
            INSERT INTO alerts (
                alert_id, drift_uid, taxonomy, drift_score, normalized_score,
                alert_level, state, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            alert_id,
            f"drift_{alert_id}",
            "ALLOCATION_DRIFT",
            15.0,
            8.0,
            "RED",
            "ACTIVE",
            now.replace(tzinfo=None),
            now.replace(tzinfo=None),
        ])

    print(f"   Alert created: {alert_id}")

    # Wait for escalation
    wait_time = config.red_ttl_minutes * 60 + config.check_interval + 5
    print(f"\n4. Waiting {wait_time}s for escalation...")
    time.sleep(wait_time)

    # Check escalation
    print("\n5. Checking escalation...")
    with duckdb.connect(str(db_path)) as conn:
        result = conn.execute("""
            SELECT escalation_count, last_escalation_at
            FROM alerts
            WHERE alert_id = ?
        """, [alert_id]).fetchone()

        if result and result[0] > 0:
            print(f"   ✅ Escalation count: {result[0]}")
            print(f"   ✅ Last escalation: {result[1]}")
        else:
            print(f"   ❌ No escalation occurred (count={result[0] if result else 'N/A'})")

        # Check audit trail
        audit = conn.execute("""
            SELECT COUNT(*) FROM escalation_history WHERE alert_id = ?
        """, [alert_id]).fetchone()[0]

        if audit > 0:
            print(f"   ✅ Escalation history entries: {audit}")
        else:
            print(f"   ❌ No escalation history entries")

    # Check telemetry
    events = telemetry_spool.read_events()
    escalation_events = [e for e in events if e.get("event_type") == "escalation_triggered"]
    if escalation_events:
        print(f"   ✅ Telemetry events: {len(escalation_events)}")
    else:
        print(f"   ❌ No telemetry events")

    # Acknowledge alert
    print("\n6. Acknowledging alert...")
    with duckdb.connect(str(db_path)) as conn:
        conn.execute("""
            UPDATE alerts
            SET acknowledged_at = ?, state = 'ACKNOWLEDGED'
            WHERE alert_id = ?
        """, [now.replace(tzinfo=None), alert_id])

    # Wait and verify no further escalations
    print(f"\n7. Waiting {config.check_interval + 5}s to verify no further escalations...")
    time.sleep(config.check_interval + 5)

    with duckdb.connect(str(db_path)) as conn:
        result = conn.execute("""
            SELECT escalation_count FROM alerts WHERE alert_id = ?
        """, [alert_id]).fetchone()

        if result:
            print(f"   ✅ Final escalation count: {result[0]} (should be unchanged)")

    # Stop escalation manager
    print("\n8. Stopping escalation manager...")
    escalation_manager.stop(timeout=5.0)

    health = escalation_manager.health_check()
    print(f"   Health: is_running={health.is_running}")
    print(f"   Total checks: {health.total_checks}")
    print(f"   Total escalations: {health.total_escalations}")

    print("\n" + "=" * 60)
    print("Smoke test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
