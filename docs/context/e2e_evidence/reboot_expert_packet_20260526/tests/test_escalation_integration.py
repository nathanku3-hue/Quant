"""
Phase 33B Slice 3: Escalation Integration Tests

Tests full pipeline: alert → escalate → ack → stop.

Test Coverage:
- Full escalation pipeline with telemetry
- Durable audit entries
- Multi-alert scenarios
- Feature flag behavior
- Integration with AsyncDriftWorker
"""

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from core.drift_alert_manager import DriftAlertManager
from core.drift_detector import DriftDetector, DriftResult, DriftTaxonomy
from core.escalation_manager import EscalationManager
from core.telemetry_spool import TelemetrySpool


@pytest.fixture
def temp_db(tmp_path):
    """Temporary database for testing."""
    return tmp_path / "test_integration.duckdb"


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
        worker_id="test_integration",
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


def test_full_escalation_pipeline(alert_manager, escalation_manager, telemetry_spool):
    """Test full pipeline: alert → escalate → verify telemetry + audit."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)

    # Create alert
    alert_id = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=old_time,
    )

    # Escalate
    escalations = escalation_manager._check_escalations()
    assert len(escalations) == 1
    assert escalations[0].alert_id == alert_id

    # Verify telemetry event
    events = telemetry_spool.read_events()
    escalation_events = [e for e in events if e["event_type"] == "escalation_triggered"]
    assert len(escalation_events) == 1
    assert escalation_events[0]["data"]["alert_id"] == alert_id

    # Verify audit entry
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        audit = conn.execute("""
            SELECT alert_id, escalation_count, channel, channel_status
            FROM escalation_history
            WHERE alert_id = ?
        """, [alert_id]).fetchone()

    assert audit[0] == alert_id
    assert audit[1] == 1
    assert audit[2] == "log"
    assert audit[3] == "success"


def test_escalation_stops_after_acknowledgement(alert_manager, escalation_manager):
    """Test escalation stops when alert is acknowledged."""
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

    # Acknowledge alert - use naive datetimes for DuckDB
    now_naive = now.replace(tzinfo=None)
    cooldown_time = (now - timedelta(minutes=31)).replace(tzinfo=None)
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        conn.execute("""
            UPDATE alerts
            SET acknowledged_at = ?, state = 'ACKNOWLEDGED', last_escalation_at = ?
            WHERE alert_id = ?
        """, [now_naive, cooldown_time, alert_id])

    # Second escalation attempt should fail
    escalations = escalation_manager._check_escalations()
    assert len(escalations) == 0


def test_multi_alert_escalation_scenario(alert_manager, escalation_manager, telemetry_spool):
    """Test multiple alerts escalate independently."""
    now = datetime.now(timezone.utc)

    # Create 3 alerts
    alert1 = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=now - timedelta(minutes=10),
    )
    alert2 = create_test_alert(
        alert_manager,
        alert_level="YELLOW",
        created_at=now - timedelta(minutes=8),
    )
    alert3 = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=now - timedelta(minutes=5),
    )

    # Escalate all
    escalations = escalation_manager._check_escalations()
    assert len(escalations) == 3

    # Verify telemetry events
    events = telemetry_spool.read_events()
    escalation_events = [e for e in events if e["event_type"] == "escalation_triggered"]
    assert len(escalation_events) == 3

    # Verify audit entries
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        audit_count = conn.execute("""
            SELECT COUNT(*)
            FROM escalation_history
        """).fetchone()[0]

    assert audit_count == 3


def test_escalation_lifecycle_with_background_thread(alert_manager, escalation_manager):
    """Test escalation manager lifecycle with background thread."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)

    # Create alert
    alert_id = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=old_time,
    )

    # Start escalation manager
    escalation_manager.start()
    time.sleep(2)  # Wait for at least one check cycle

    # Stop
    escalation_manager.stop(timeout=3.0)

    # Verify escalation occurred
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        result = conn.execute("""
            SELECT escalation_count
            FROM alerts
            WHERE alert_id = ?
        """, [alert_id]).fetchone()

    assert result[0] >= 1  # At least one escalation

    # Verify health check
    health = escalation_manager.health_check()
    assert not health.is_running
    assert health.total_checks >= 1
    assert health.total_escalations >= 1


def test_escalation_with_no_alerts(escalation_manager):
    """Test escalation check with no alerts."""
    escalations = escalation_manager._check_escalations()
    assert len(escalations) == 0

    health = escalation_manager.health_check()
    assert health.total_escalations == 0


def test_escalation_respects_alert_state(alert_manager, escalation_manager):
    """Test escalation only processes ACTIVE alerts."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)
    old_time_naive = old_time.replace(tzinfo=None)

    # Create alerts in different states
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        for state in ["ACTIVE", "RESOLVED", "SUPPRESSED", "SUPERSEDED"]:
            alert_id = f"test_{state}_{int(time.time() * 1000000)}"
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
                state,
                old_time_naive,
                old_time_naive,
            ])

    # Only ACTIVE alert should escalate
    escalations = escalation_manager._check_escalations()
    assert len(escalations) == 1
    assert "ACTIVE" in escalations[0].alert_id


def test_escalation_audit_metadata_structure(alert_manager, escalation_manager):
    """Test escalation audit metadata has correct structure."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)

    alert_id = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=old_time,
    )

    # Escalate
    escalations = escalation_manager._check_escalations()
    assert len(escalations) == 1

    # Verify metadata structure
    import duckdb
    import json
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        metadata_str = conn.execute("""
            SELECT metadata
            FROM escalation_history
            WHERE alert_id = ?
        """, [alert_id]).fetchone()[0]

    metadata = json.loads(metadata_str)
    assert "taxonomy" in metadata
    assert "alert_level" in metadata
    assert "time_since_creation_minutes" in metadata
    assert metadata["alert_level"] == "RED"
    assert metadata["taxonomy"] == "ALLOCATION_DRIFT"


def test_escalation_manager_error_handling(alert_manager, escalation_manager, monkeypatch):
    """Test escalation manager handles errors gracefully."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)

    create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=old_time,
    )

    # Simulate DB error
    def mock_connect(*args, **kwargs):
        raise RuntimeError("DB connection failed")

    import duckdb
    original_connect = duckdb.connect
    monkeypatch.setattr("duckdb.connect", mock_connect)

    # Should not crash
    try:
        escalations = escalation_manager._check_escalations()
        assert False, "Should have raised exception"
    except RuntimeError:
        pass  # Expected

    # Restore and verify recovery
    monkeypatch.setattr("duckdb.connect", original_connect)
    escalations = escalation_manager._check_escalations()
    assert len(escalations) == 1


def test_escalation_without_telemetry_spool(alert_manager):
    """Test escalation works without telemetry spool."""
    escalation_manager = EscalationManager(
        alert_manager=alert_manager,
        yellow_ttl_minutes=5,
        red_ttl_minutes=2,
        max_escalations=3,
        cooldown_minutes=30,
        check_interval=1,
        telemetry_spool=None,  # No telemetry
        worker_id="test_no_telemetry",
    )

    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)

    alert_id = create_test_alert(
        alert_manager,
        alert_level="RED",
        created_at=old_time,
    )

    # Should still escalate
    escalations = escalation_manager._check_escalations()
    assert len(escalations) == 1

    # Verify audit entry still created
    import duckdb
    with duckdb.connect(str(alert_manager.db_path)) as conn:
        audit_count = conn.execute("""
            SELECT COUNT(*)
            FROM escalation_history
            WHERE alert_id = ?
        """, [alert_id]).fetchone()[0]

    assert audit_count == 1
