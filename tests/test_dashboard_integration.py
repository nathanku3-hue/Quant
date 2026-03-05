"""
Phase 33B Slice 4.3: True Dashboard Integration Test

Tests escalation manager lifecycle by calling the actual dashboard initialization function.
This validates the real runtime code path used by dashboard.py.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest


def test_dashboard_escalation_initialization_enabled(tmp_path, monkeypatch):
    """Test dashboard escalation initialization with ENABLE_ESCALATION=true."""
    # Set environment
    monkeypatch.setenv("ENABLE_ESCALATION", "true")
    monkeypatch.setenv("ESCALATION_CHECK_INTERVAL", "60")

    # Mock streamlit to avoid UI rendering
    mock_st = MagicMock()
    mock_st.session_state = {}
    sys.modules['streamlit'] = mock_st

    # Mock data paths
    test_db_path = tmp_path / "drift_alerts.duckdb"
    test_telemetry_path = tmp_path / "telemetry" / "drift_events.jsonl"
    test_telemetry_path.parent.mkdir(parents=True, exist_ok=True)

    # Import actual dashboard initialization function
    from core.drift_alert_manager import DriftAlertManager
    from core.drift_detector import DriftDetector
    from core.dashboard_escalation import initialize_escalation_manager

    # Execute actual dashboard initialization code
    drift_alert_manager = DriftAlertManager(db_path=test_db_path)
    drift_detector = DriftDetector(sigma_threshold=2.0)

    # Call the actual function used by dashboard.py
    initialize_escalation_manager(
        alert_manager=drift_alert_manager,
        session_state=mock_st.session_state,
        telemetry_path=test_telemetry_path,
    )

    # Verify manager was created and started
    assert "escalation_manager" in mock_st.session_state
    manager = mock_st.session_state["escalation_manager"]
    assert manager is not None
    assert manager.health_check().is_running

    # Cleanup
    manager.stop(timeout=2.0)
    del sys.modules['streamlit']


def test_dashboard_escalation_initialization_disabled(tmp_path, monkeypatch):
    """Test dashboard escalation initialization with ENABLE_ESCALATION=false."""
    # Set environment
    monkeypatch.setenv("ENABLE_ESCALATION", "false")

    # Mock streamlit
    mock_st = MagicMock()
    mock_st.session_state = {}
    sys.modules['streamlit'] = mock_st

    # Mock data paths
    test_db_path = tmp_path / "drift_alerts.duckdb"

    # Import actual dashboard initialization function
    from core.drift_alert_manager import DriftAlertManager
    from core.drift_detector import DriftDetector
    from core.dashboard_escalation import initialize_escalation_manager

    # Execute actual dashboard initialization code
    drift_alert_manager = DriftAlertManager(db_path=test_db_path)
    drift_detector = DriftDetector(sigma_threshold=2.0)

    # Call the actual function used by dashboard.py
    initialize_escalation_manager(
        alert_manager=drift_alert_manager,
        session_state=mock_st.session_state,
    )

    # Verify manager was not created
    assert "escalation_manager" not in mock_st.session_state

    # Cleanup mock
    del sys.modules['streamlit']


def test_dashboard_escalation_singleton_on_rerun(tmp_path, monkeypatch):
    """Test dashboard escalation manager is reused on rerun (singleton)."""
    # Set environment
    monkeypatch.setenv("ENABLE_ESCALATION", "true")

    # Mock streamlit
    mock_st = MagicMock()
    mock_st.session_state = {}
    sys.modules['streamlit'] = mock_st

    # Mock data paths
    test_db_path = tmp_path / "drift_alerts.duckdb"
    test_telemetry_path = tmp_path / "telemetry" / "drift_events.jsonl"
    test_telemetry_path.parent.mkdir(parents=True, exist_ok=True)

    # Import actual dashboard initialization function
    from core.drift_alert_manager import DriftAlertManager
    from core.dashboard_escalation import initialize_escalation_manager

    drift_alert_manager = DriftAlertManager(db_path=test_db_path)

    # First run: create manager
    initialize_escalation_manager(
        alert_manager=drift_alert_manager,
        session_state=mock_st.session_state,
        telemetry_path=test_telemetry_path,
    )

    first_manager = mock_st.session_state["escalation_manager"]

    # Second run: reuse manager (simulate rerun)
    initialize_escalation_manager(
        alert_manager=drift_alert_manager,
        session_state=mock_st.session_state,
        telemetry_path=test_telemetry_path,
    )

    second_manager = mock_st.session_state["escalation_manager"]
    assert second_manager is first_manager  # Same instance (singleton)

    # Cleanup
    first_manager.stop(timeout=2.0)
    del sys.modules['streamlit']
