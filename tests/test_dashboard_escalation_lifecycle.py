"""
Phase 33B Slice 4.2: Dashboard Lifecycle Tests

Tests escalation manager lifecycle in dashboard context:
- Singleton pattern (reuse on rerun)
- Config change detection and restart
- Graceful stop on disable
- Session-end cleanup
"""

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.drift_alert_manager import DriftAlertManager
from core.escalation_config import EscalationConfig
from core.escalation_manager import EscalationManager
from core.telemetry_spool import TelemetrySpool


class MockSessionState(dict):
    """Mock Streamlit session state."""
    def get(self, key, default=None):
        return super().get(key, default)


def test_escalation_manager_singleton_reuse(tmp_path):
    """Test escalation manager is reused on dashboard rerun (singleton pattern)."""
    db_path = tmp_path / "test.duckdb"
    alert_manager = DriftAlertManager(db_path=db_path)

    telemetry_spool = TelemetrySpool(spool_path=tmp_path / "telemetry.jsonl")

    config = EscalationConfig(
        enabled=True,
        yellow_ttl_minutes=5,
        red_ttl_minutes=2,
        max_escalations=3,
        cooldown_minutes=30,
        check_interval=60,
    )

    session_state = MockSessionState()

    # First run: create manager
    prev_enabled = session_state.get("escalation_enabled", False)
    config_hash = hash((config.yellow_ttl_minutes, config.red_ttl_minutes, config.max_escalations, config.cooldown_minutes, config.check_interval))
    config_changed = (
        prev_enabled != config.enabled
        or session_state.get("escalation_config_hash") != config_hash
    )

    assert config_changed  # First run, should create

    if "escalation_manager" not in session_state:
        manager = EscalationManager(
            alert_manager=alert_manager,
            yellow_ttl_minutes=config.yellow_ttl_minutes,
            red_ttl_minutes=config.red_ttl_minutes,
            max_escalations=config.max_escalations,
            cooldown_minutes=config.cooldown_minutes,
            check_interval=config.check_interval,
            telemetry_spool=telemetry_spool,
            worker_id="test",
        )
        manager.start()
        session_state["escalation_manager"] = manager
        session_state["escalation_enabled"] = True
        session_state["escalation_config_hash"] = config_hash

    first_manager = session_state["escalation_manager"]
    assert first_manager.health_check().is_running

    # Second run: reuse manager (simulate rerun)
    prev_enabled = session_state.get("escalation_enabled", False)
    config_changed = (
        prev_enabled != config.enabled
        or session_state.get("escalation_config_hash") != config_hash
    )

    assert not config_changed  # Config unchanged, should reuse

    if "escalation_manager" not in session_state:
        pytest.fail("Manager should exist in session state")

    second_manager = session_state["escalation_manager"]
    assert second_manager is first_manager  # Same instance
    assert second_manager.health_check().is_running

    # Cleanup
    first_manager.stop(timeout=2.0)


def test_escalation_manager_stop_on_disable(tmp_path):
    """Test escalation manager stops when disabled."""
    db_path = tmp_path / "test.duckdb"
    alert_manager = DriftAlertManager(db_path=db_path)

    telemetry_spool = TelemetrySpool(spool_path=tmp_path / "telemetry.jsonl")

    session_state = MockSessionState()

    # Start with enabled
    config_enabled = EscalationConfig(
        enabled=True,
        yellow_ttl_minutes=5,
        red_ttl_minutes=2,
        max_escalations=3,
        cooldown_minutes=30,
        check_interval=60,
    )

    manager = EscalationManager(
        alert_manager=alert_manager,
        yellow_ttl_minutes=config_enabled.yellow_ttl_minutes,
        red_ttl_minutes=config_enabled.red_ttl_minutes,
        max_escalations=config_enabled.max_escalations,
        cooldown_minutes=config_enabled.cooldown_minutes,
        check_interval=config_enabled.check_interval,
        telemetry_spool=telemetry_spool,
        worker_id="test",
    )
    manager.start()
    session_state["escalation_manager"] = manager
    session_state["escalation_enabled"] = True

    assert manager.health_check().is_running

    # Disable escalation
    config_disabled = EscalationConfig(
        enabled=False,
        yellow_ttl_minutes=5,
        red_ttl_minutes=2,
        max_escalations=3,
        cooldown_minutes=30,
        check_interval=60,
    )

    prev_enabled = session_state.get("escalation_enabled", False)
    config_changed = prev_enabled != config_disabled.enabled

    assert config_changed  # Enabled -> disabled

    # Stop existing manager
    if config_changed and "escalation_manager" in session_state:
        old_manager = session_state["escalation_manager"]
        if old_manager is not None:
            old_manager.stop(timeout=2.0)
        del session_state["escalation_manager"]
        session_state["escalation_enabled"] = False

    assert "escalation_manager" not in session_state
    assert not manager.health_check().is_running


def test_escalation_manager_restart_on_config_change(tmp_path):
    """Test escalation manager restarts when config changes."""
    db_path = tmp_path / "test.duckdb"
    alert_manager = DriftAlertManager(db_path=db_path)

    telemetry_spool = TelemetrySpool(spool_path=tmp_path / "telemetry.jsonl")

    session_state = MockSessionState()

    # Start with config 1
    config1 = EscalationConfig(
        enabled=True,
        yellow_ttl_minutes=5,
        red_ttl_minutes=2,
        max_escalations=3,
        cooldown_minutes=30,
        check_interval=60,
    )

    manager1 = EscalationManager(
        alert_manager=alert_manager,
        yellow_ttl_minutes=config1.yellow_ttl_minutes,
        red_ttl_minutes=config1.red_ttl_minutes,
        max_escalations=config1.max_escalations,
        cooldown_minutes=config1.cooldown_minutes,
        check_interval=config1.check_interval,
        telemetry_spool=telemetry_spool,
        worker_id="test",
    )
    manager1.start()
    session_state["escalation_manager"] = manager1
    session_state["escalation_enabled"] = True
    session_state["escalation_config_hash"] = hash((config1.yellow_ttl_minutes, config1.red_ttl_minutes, config1.max_escalations, config1.cooldown_minutes, config1.check_interval))

    assert manager1.health_check().is_running

    # Change config (different check interval)
    config2 = EscalationConfig(
        enabled=True,
        yellow_ttl_minutes=5,
        red_ttl_minutes=2,
        max_escalations=3,
        cooldown_minutes=30,
        check_interval=30,  # Changed from 60
    )

    prev_enabled = session_state.get("escalation_enabled", False)
    config_hash2 = hash((config2.yellow_ttl_minutes, config2.red_ttl_minutes, config2.max_escalations, config2.cooldown_minutes, config2.check_interval))
    config_changed = (
        prev_enabled != config2.enabled
        or session_state.get("escalation_config_hash") != config_hash2
    )

    assert config_changed  # Config hash changed

    # Stop old manager
    if config_changed and "escalation_manager" in session_state:
        old_manager = session_state["escalation_manager"]
        if old_manager is not None:
            old_manager.stop(timeout=2.0)
        del session_state["escalation_manager"]
        session_state["escalation_enabled"] = False

    assert not manager1.health_check().is_running

    # Create new manager with new config
    if "escalation_manager" not in session_state:
        manager2 = EscalationManager(
            alert_manager=alert_manager,
            yellow_ttl_minutes=config2.yellow_ttl_minutes,
            red_ttl_minutes=config2.red_ttl_minutes,
            max_escalations=config2.max_escalations,
            cooldown_minutes=config2.cooldown_minutes,
            check_interval=config2.check_interval,
            telemetry_spool=telemetry_spool,
            worker_id="test",
        )
        manager2.start()
        session_state["escalation_manager"] = manager2
        session_state["escalation_enabled"] = True
        session_state["escalation_config_hash"] = config_hash2

    manager2 = session_state["escalation_manager"]
    assert manager2 is not manager1  # Different instance
    assert manager2.health_check().is_running
    assert manager2.check_interval == 30  # New config applied

    # Cleanup
    manager2.stop(timeout=2.0)


def test_session_end_cleanup(tmp_path):
    """Test atexit cleanup handler stops manager."""
    import atexit

    db_path = tmp_path / "test.duckdb"
    alert_manager = DriftAlertManager(db_path=db_path)
    telemetry_spool = TelemetrySpool(spool_path=tmp_path / "telemetry.jsonl")

    manager = EscalationManager(
        alert_manager=alert_manager,
        yellow_ttl_minutes=5,
        red_ttl_minutes=2,
        max_escalations=3,
        cooldown_minutes=30,
        check_interval=60,
        telemetry_spool=telemetry_spool,
        worker_id="test",
    )
    manager.start()

    # Create cleanup function
    def cleanup():
        manager.stop(timeout=2.0)

    # Register cleanup
    atexit.register(cleanup)

    # Verify manager is running
    assert manager.health_check().is_running

    # Manually call cleanup (simulates atexit)
    cleanup()

    # Verify manager stopped
    assert not manager.health_check().is_running

    # Cleanup
    atexit.unregister(cleanup)


def test_multiple_reruns_no_duplicate_managers(tmp_path):
    """Test multiple reruns don't create duplicate managers."""
    db_path = tmp_path / "test.duckdb"
    alert_manager = DriftAlertManager(db_path=db_path)

    telemetry_spool = TelemetrySpool(spool_path=tmp_path / "telemetry.jsonl")

    config = EscalationConfig(
        enabled=True,
        yellow_ttl_minutes=5,
        red_ttl_minutes=2,
        max_escalations=3,
        cooldown_minutes=30,
        check_interval=60,
    )

    session_state = MockSessionState()
    config_hash = hash((config.yellow_ttl_minutes, config.red_ttl_minutes, config.max_escalations, config.cooldown_minutes, config.check_interval))

    # Simulate 5 reruns
    managers = []
    for i in range(5):
        prev_enabled = session_state.get("escalation_enabled", False)
        config_changed = (
            prev_enabled != config.enabled
            or session_state.get("escalation_config_hash") != config_hash
        )

        if config.enabled and "escalation_manager" not in session_state:
            manager = EscalationManager(
                alert_manager=alert_manager,
                yellow_ttl_minutes=config.yellow_ttl_minutes,
                red_ttl_minutes=config.red_ttl_minutes,
                max_escalations=config.max_escalations,
                cooldown_minutes=config.cooldown_minutes,
                check_interval=config.check_interval,
                telemetry_spool=telemetry_spool,
                worker_id="test",
            )
            manager.start()
            session_state["escalation_manager"] = manager
            session_state["escalation_enabled"] = True
            session_state["escalation_config_hash"] = config_hash

        managers.append(session_state.get("escalation_manager"))

    # All should be the same instance
    assert len(set(id(m) for m in managers if m is not None)) == 1
    assert all(m is managers[0] for m in managers if m is not None)

    # Only one manager running
    manager = session_state["escalation_manager"]
    assert manager.health_check().is_running

    # Cleanup
    manager.stop(timeout=2.0)
