"""
Phase 33B Slice 3: Escalation Atomicity Tests

Tests race conditions and idempotency of atomic escalation gate.

Test Coverage:
- Concurrent escalation attempts (only one succeeds)
- Idempotent escalation (no double-escalation)
- Race-safe cooldown enforcement
- Race-safe max escalation limit
"""

import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.drift_alert_manager import DriftAlertManager
from core.escalation_manager import EscalationManager
from core.telemetry_spool import TelemetrySpool


@pytest.fixture
def temp_db(tmp_path):
    """Temporary database for testing."""
    return tmp_path / "test_atomicity.duckdb"


@pytest.fixture
def alert_manager(temp_db):
    """Alert manager with test database."""
    return DriftAlertManager(db_path=temp_db)


@pytest.fixture
def telemetry_spool(tmp_path):
    """Telemetry spool for testing."""
    spool_path = tmp_path / "telemetry.jsonl"
    return TelemetrySpool(spool_path=spool_path)


@pytest.fixture
def escalation_manager(alert_manager, telemetry_spool):
    """Escalation manager for testing."""
    return EscalationManager(
        alert_manager=alert_manager,
        yellow_ttl_minutes=5,
        red_ttl_minutes=2,
        max_escalations=3,
        cooldown_minutes=30,
        check_interval=1,
        telemetry_spool=telemetry_spool,
        worker_id="test_atomicity",
    )


def create_test_alert(
    alert_manager: DriftAlertManager,
    alert_level: str = "RED",
    created_at: datetime | None = None,
) -> str:
    """Helper to create test alert."""
    if created_at is None:
        created_at = datetime.now(timezone.utc)

    # DuckDB stores timestamps as naive, so convert to naive for insertion
    created_at_naive = created_at.replace(tzinfo=None) if created_at.tzinfo else created_at

    import duckdb
    alert_id = f"test_alert_{int(time.time() * 1000000)}"

    with duckdb.connect(str(alert_manager.db_path)) as conn:
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
            alert_level,
            "ACTIVE",
            created_at_naive,
            created_at_naive,
        ])

    return alert_id


def test_concurrent_escalation_only_one_succeeds(alert_manager, escalation_manager):
    """Test concurrent escalation attempts - only one succeeds."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)

    alert_id = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=old_time,
    )

    # Simulate concurrent escalation attempts
    results = []
    errors = []

    def escalate_worker():
        try:
            escalations = escalation_manager._check_escalations()
            results.append(escalations)
        except Exception as e:
            # DuckDB transaction conflicts are expected in concurrent scenarios
            errors.append(e)

    # Launch 5 concurrent threads
    threads = []
    for _ in range(5):
        t = threading.Thread(target=escalate_worker)
        threads.append(t)
        t.start()

    # Wait for all threads
    for t in threads:
        t.join()

    # Either one thread succeeded, or some got transaction conflicts
    # The key is that only ONE escalation actually happened
    successful_escalations = [r for r in results if len(r) > 0]
    assert len(successful_escalations) <= 1  # At most one succeeded

    # Verify DB state - only escalated once
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        result = conn.execute("""
            SELECT escalation_count, last_escalation_at
            FROM alerts
            WHERE alert_id = ?
        """, [alert_id]).fetchone()

    assert result[0] == 1  # Only escalated once
    assert result[1] is not None


def test_idempotent_escalation_no_double_escalation(alert_manager, escalation_manager):
    """Test escalation is idempotent - no double escalation."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)

    alert_id = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=old_time,
    )

    # First escalation
    escalations1 = escalation_manager._check_escalations()
    assert len(escalations1) == 1
    assert escalations1[0].escalation_count == 1

    # Immediate second attempt (within cooldown)
    escalations2 = escalation_manager._check_escalations()
    assert len(escalations2) == 0  # Blocked by cooldown

    # Verify DB state
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        result = conn.execute("""
            SELECT escalation_count
            FROM alerts
            WHERE alert_id = ?
        """, [alert_id]).fetchone()

    assert result[0] == 1  # Still only 1


def test_race_safe_cooldown_enforcement(alert_manager, escalation_manager):
    """Test cooldown is enforced atomically at DB level."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)

    alert_id = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=old_time,
    )

    # First escalation
    escalations = escalation_manager._check_escalations()
    assert len(escalations) == 1

    # Manually set last_escalation_at to 29 minutes ago (within 30min cooldown) - use naive datetime
    cooldown_time = (now - timedelta(minutes=29)).replace(tzinfo=None)
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        conn.execute("""
            UPDATE alerts
            SET last_escalation_at = ?
            WHERE alert_id = ?
        """, [cooldown_time, alert_id])

    # Concurrent attempts should all fail (cooldown not expired)
    results = []

    def escalate_worker():
        escalations = escalation_manager._check_escalations()
        results.append(escalations)

    threads = []
    for _ in range(3):
        t = threading.Thread(target=escalate_worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # All should fail
    assert all(len(r) == 0 for r in results)

    # Verify escalation count unchanged
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        result = conn.execute("""
            SELECT escalation_count
            FROM alerts
            WHERE alert_id = ?
        """, [alert_id]).fetchone()

    assert result[0] == 1  # Still only 1


def test_race_safe_max_escalation_limit(alert_manager, escalation_manager):
    """Test max escalation limit enforced atomically."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)

    alert_id = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=old_time,
    )

    # Escalate to max-1 (2 times) - use naive datetime for DuckDB
    cooldown_time = (now - timedelta(minutes=31)).replace(tzinfo=None)
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        conn.execute("""
            UPDATE alerts
            SET escalation_count = 2, last_escalation_at = ?
            WHERE alert_id = ?
        """, [cooldown_time, alert_id])

    # Concurrent attempts to escalate (only 1 should succeed to reach max=3)
    results = []

    def escalate_worker():
        try:
            escalations = escalation_manager._check_escalations()
            results.append(escalations)
        except Exception:
            # DuckDB transaction conflicts expected
            results.append([])

    threads = []
    for _ in range(5):
        t = threading.Thread(target=escalate_worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Only one should succeed (or none if all got conflicts)
    successful = [r for r in results if len(r) > 0]
    assert len(successful) <= 1

    # Verify final count is exactly 3
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        result = conn.execute("""
            SELECT escalation_count
            FROM alerts
            WHERE alert_id = ?
        """, [alert_id]).fetchone()

    assert result[0] == 3


def test_atomic_ttl_check_prevents_premature_escalation(alert_manager, escalation_manager):
    """Test TTL check in atomic gate prevents premature escalation."""
    now = datetime.now(timezone.utc)
    recent_time = now - timedelta(minutes=1)  # 1 minute ago (< 2min RED TTL)

    alert_id = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=recent_time,
    )

    # Concurrent attempts should all fail (TTL not expired)
    results = []

    def escalate_worker():
        escalations = escalation_manager._check_escalations()
        results.append(escalations)

    threads = []
    for _ in range(3):
        t = threading.Thread(target=escalate_worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # All should fail
    assert all(len(r) == 0 for r in results)

    # Verify no escalation occurred
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        result = conn.execute("""
            SELECT escalation_count, last_escalation_at
            FROM alerts
            WHERE alert_id = ?
        """, [alert_id]).fetchone()

    assert result[0] == 0
    assert result[1] is None


def test_atomic_ack_check_prevents_escalation(alert_manager, escalation_manager):
    """Test acknowledgement check in atomic gate prevents escalation."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)

    alert_id = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=old_time,
    )

    # Acknowledge alert
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        conn.execute("""
            UPDATE alerts
            SET acknowledged_at = ?, state = 'ACKNOWLEDGED'
            WHERE alert_id = ?
        """, [now, alert_id])

    # Concurrent attempts should all fail (acknowledged)
    results = []

    def escalate_worker():
        escalations = escalation_manager._check_escalations()
        results.append(escalations)

    threads = []
    for _ in range(3):
        t = threading.Thread(target=escalate_worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # All should fail
    assert all(len(r) == 0 for r in results)

    # Verify no escalation occurred
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        result = conn.execute("""
            SELECT escalation_count, last_escalation_at
            FROM alerts
            WHERE alert_id = ?
        """, [alert_id]).fetchone()

    assert result[0] == 0
    assert result[1] is None


def test_audit_trail_consistency_under_concurrency(alert_manager, escalation_manager):
    """Test escalation_history audit trail remains consistent under concurrency."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)

    alert_id = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=old_time,
    )

    # Concurrent escalation attempts
    results = []

    def escalate_worker():
        escalations = escalation_manager._check_escalations()
        results.append(escalations)

    threads = []
    for _ in range(5):
        t = threading.Thread(target=escalate_worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verify audit trail has exactly 1 entry
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        audit_count = conn.execute("""
            SELECT COUNT(*)
            FROM escalation_history
            WHERE alert_id = ?
        """, [alert_id]).fetchone()[0]

    assert audit_count == 1  # Only one audit entry despite concurrent attempts
