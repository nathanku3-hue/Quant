"""
Tests for AsyncDriftWorker - Phase 33B Slice 1

Validates:
1. Worker lifecycle (start/stop/health check)
2. Single poll cycle execution
3. Error recovery with exponential backoff
4. Clean shutdown without thread leaks
5. Drift detection → alert persistence pipeline
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call

import pandas as pd
import pytest

from core.async_drift_worker import AsyncDriftWorker, WorkerHealth
from core.drift_alert_manager import DriftAlertManager
from core.drift_detector import DriftDetector, DriftResult, DriftTaxonomy


@pytest.fixture
def mock_alert_manager():
    """Mock DriftAlertManager for testing."""
    manager = MagicMock(spec=DriftAlertManager)
    return manager


@pytest.fixture
def mock_drift_detector():
    """Mock DriftDetector for testing."""
    detector = MagicMock(spec=DriftDetector)
    return detector


@pytest.fixture
def mock_baseline_loader():
    """Mock baseline loader that returns sample weights."""
    def loader():
        weights = pd.Series({"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.2})
        metadata = {"baseline_id": "test123", "strategy_name": "test"}
        return weights, metadata
    return loader


@pytest.fixture
def mock_live_loader():
    """Mock live loader that returns sample weights."""
    def loader():
        return pd.Series({"AAPL": 0.6, "MSFT": 0.25, "GOOGL": 0.15})
    return loader


def test_worker_start_and_stop(mock_alert_manager, mock_drift_detector, mock_baseline_loader, mock_live_loader):
    """
    Contract: Worker starts background thread and stops cleanly on shutdown.
    """
    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=mock_baseline_loader,
        live_loader=mock_live_loader,
        poll_interval=1,
    )

    # Start worker
    worker.start()
    assert worker._thread is not None
    assert worker._thread.is_alive()

    health = worker.health_check()
    assert health.is_running is True

    # Stop worker
    worker.stop(timeout=2.0)
    assert not worker._thread.is_alive()

    health = worker.health_check()
    assert health.is_running is False


def test_worker_executes_drift_check(mock_alert_manager, mock_drift_detector, mock_baseline_loader, mock_live_loader):
    """
    Contract: Worker executes drift check and persists alerts.
    """
    # Mock drift detection result
    drift_result = DriftResult(
        drift_score=3.5,  # High z-score
        taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
        timestamp=datetime.now(),
        alert_level="RED",
        details={"method": "chi2", "p_value": 0.001},
    )
    mock_drift_detector.detect_allocation_drift.return_value = drift_result

    # Mock alert manager to return alert record (use MagicMock)
    mock_alert_record = MagicMock()
    mock_alert_record.alert_level = "RED"
    mock_alert_manager.process_drift_result.return_value = mock_alert_record

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=mock_baseline_loader,
        live_loader=mock_live_loader,
        poll_interval=1,
    )

    worker.start()
    time.sleep(2.5)  # Wait for at least 2 poll cycles
    worker.stop(timeout=2.0)

    # Verify drift detection was called
    assert mock_drift_detector.detect_allocation_drift.call_count >= 2

    # Verify alert was processed
    assert mock_alert_manager.process_drift_result.call_count >= 2


def test_worker_skips_check_when_weights_unavailable(mock_alert_manager, mock_drift_detector):
    """
    Contract: Worker skips drift check when baseline or live weights are None.
    """
    def baseline_loader():
        return None, None

    def live_loader():
        return None

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=baseline_loader,
        live_loader=live_loader,
        poll_interval=1,
    )

    worker.start()
    time.sleep(1.5)
    worker.stop(timeout=2.0)

    # Verify drift detection was NOT called
    mock_drift_detector.detect_allocation_drift.assert_not_called()


def test_worker_handles_errors_with_backoff(mock_alert_manager, mock_drift_detector, mock_baseline_loader, mock_live_loader):
    """
    Contract: Worker handles errors gracefully with exponential backoff.
    """
    # Make drift detector raise error
    mock_drift_detector.detect_allocation_drift.side_effect = RuntimeError("Test error")

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=mock_baseline_loader,
        live_loader=mock_live_loader,
        poll_interval=1,
        max_consecutive_errors=3,
    )

    worker.start()
    time.sleep(2.0)  # Let it hit a few errors

    health = worker.health_check()
    assert health.consecutive_errors > 0

    worker.stop(timeout=2.0)


def test_worker_stops_after_max_consecutive_errors(mock_alert_manager, mock_drift_detector, mock_baseline_loader, mock_live_loader):
    """
    Contract: Worker stops itself after max_consecutive_errors threshold.
    """
    # Make drift detector always raise error
    mock_drift_detector.detect_allocation_drift.side_effect = RuntimeError("Persistent error")

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=mock_baseline_loader,
        live_loader=mock_live_loader,
        poll_interval=1,
        max_consecutive_errors=2,
    )

    worker.start()
    time.sleep(5.0)  # Wait for worker to hit error threshold and stop

    health = worker.health_check()
    assert health.is_running is False
    assert health.consecutive_errors >= 2


def test_worker_resets_error_count_on_success(mock_alert_manager, mock_drift_detector, mock_baseline_loader, mock_live_loader):
    """
    Contract: Worker resets consecutive_errors counter after successful check.
    """
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("First call fails")
        # Subsequent calls succeed
        return DriftResult(
            drift_score=1.0,  # Low drift
            taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
            timestamp=datetime.now(),
            alert_level="GREEN",
            details={},
        )

    mock_drift_detector.detect_allocation_drift.side_effect = side_effect

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=mock_baseline_loader,
        live_loader=mock_live_loader,
        poll_interval=1,
    )

    worker.start()
    time.sleep(3.0)  # Wait for error + recovery
    worker.stop(timeout=2.0)

    health = worker.health_check()
    assert health.consecutive_errors == 0  # Reset after success


def test_worker_health_check_tracks_metrics(mock_alert_manager, mock_drift_detector, mock_baseline_loader, mock_live_loader):
    """
    Contract: health_check() returns accurate metrics (checks, alerts, last_check_time).
    """
    drift_result = DriftResult(
        drift_score=3.5,
        taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
        timestamp=datetime.now(),
        alert_level="RED",
        details={},
    )
    mock_drift_detector.detect_allocation_drift.return_value = drift_result

    # Mock alert manager to return alert record
    mock_alert_record = MagicMock()
    mock_alert_record.alert_level = "RED"
    mock_alert_manager.process_drift_result.return_value = mock_alert_record

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=mock_baseline_loader,
        live_loader=mock_live_loader,
        poll_interval=1,
    )

    worker.start()
    time.sleep(2.5)  # Wait for at least 2 checks
    worker.stop(timeout=2.0)

    health = worker.health_check()
    assert health.total_checks >= 2
    assert health.total_alerts >= 2
    assert health.last_check_time is not None
    assert isinstance(health.last_check_time, datetime)


def test_worker_ignores_duplicate_start(mock_alert_manager, mock_drift_detector, mock_baseline_loader, mock_live_loader):
    """
    Contract: Calling start() on running worker is a no-op.
    """
    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=mock_baseline_loader,
        live_loader=mock_live_loader,
        poll_interval=1,
    )

    worker.start()
    first_thread = worker._thread

    worker.start()  # Should be ignored
    assert worker._thread is first_thread  # Same thread

    worker.stop(timeout=2.0)


def test_worker_stop_on_non_running_worker_is_safe(mock_alert_manager, mock_drift_detector, mock_baseline_loader, mock_live_loader):
    """
    Contract: Calling stop() on non-running worker is safe (no-op).
    """
    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=mock_baseline_loader,
        live_loader=mock_live_loader,
        poll_interval=1,
    )

    # Stop without starting (should not crash)
    worker.stop(timeout=1.0)

    health = worker.health_check()
    assert health.is_running is False


def test_worker_classifies_severity_correctly(mock_alert_manager, mock_drift_detector, mock_baseline_loader, mock_live_loader):
    """
    Contract: Worker processes high drift and alert manager creates RED alert.
    """
    # Mock high drift (normalized score ~10.0)
    drift_result = DriftResult(
        drift_score=4.0,  # Very high z-score
        taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
        timestamp=datetime.now(),
        alert_level="RED",
        details={},
    )
    mock_drift_detector.detect_allocation_drift.return_value = drift_result

    # Mock alert manager to return RED alert
    mock_alert_record = MagicMock()
    mock_alert_record.alert_level = "RED"
    mock_alert_manager.process_drift_result.return_value = mock_alert_record

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=mock_baseline_loader,
        live_loader=mock_live_loader,
        poll_interval=1,
    )

    worker.start()
    time.sleep(1.5)
    worker.stop(timeout=2.0)

    # Verify alert was processed
    assert mock_alert_manager.process_drift_result.called


def test_worker_does_not_persist_low_severity_drift(mock_alert_manager, mock_drift_detector, mock_baseline_loader, mock_live_loader):
    """
    Contract: Worker processes low drift but alert manager suppresses (returns None).
    """
    # Mock low drift (normalized score ~3.75, below threshold)
    drift_result = DriftResult(
        drift_score=1.5,  # Low z-score
        taxonomy=DriftTaxonomy.ALLOCATION_DRIFT,
        timestamp=datetime.now(),
        alert_level="GREEN",
        details={},
    )
    mock_drift_detector.detect_allocation_drift.return_value = drift_result

    # Mock alert manager to suppress (return None for GREEN)
    mock_alert_manager.process_drift_result.return_value = None

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=mock_baseline_loader,
        live_loader=mock_live_loader,
        poll_interval=1,
    )

    worker.start()
    time.sleep(1.5)
    worker.stop(timeout=2.0)

    # Verify process_drift_result was called but returned None (suppressed)
    assert mock_alert_manager.process_drift_result.called

    # Verify no alerts were counted
    health = worker.health_check()
    assert health.total_alerts == 0


def test_worker_integration_with_real_detector(mock_alert_manager):
    """
    Phase 33B Slice 1: Integration test with real DriftDetector.

    Contract: Worker correctly calls DriftDetector with expected_weights/actual_weights kwargs.
    This test catches signature mismatches that MagicMock(spec=...) misses.
    """
    # Use REAL DriftDetector (not mock) to enforce signature
    real_detector = DriftDetector(sigma_threshold=2.0)

    def baseline_loader():
        weights = pd.Series({"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.2})
        metadata = {"baseline_id": "test123", "strategy_name": "test"}
        return weights, metadata

    def live_loader():
        # Slight drift from baseline
        return pd.Series({"AAPL": 0.55, "MSFT": 0.28, "GOOGL": 0.17})

    # Mock alert manager to suppress all alerts
    mock_alert_manager.process_drift_result.return_value = None

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=real_detector,  # REAL detector
        baseline_loader=baseline_loader,
        live_loader=live_loader,
        poll_interval=1,
    )

    worker.start()
    time.sleep(1.5)  # Wait for at least 1 poll cycle
    worker.stop(timeout=2.0)

    # Verify drift detection executed without TypeError
    health = worker.health_check()
    assert health.total_checks >= 1
    assert health.consecutive_errors == 0  # No signature errors

    # Verify alert manager was called with DriftResult
    assert mock_alert_manager.process_drift_result.called
    call_args = mock_alert_manager.process_drift_result.call_args_list[0]
    # Extract drift_result from kwargs (called with drift_result=..., normalized_score=...)
    drift_result = call_args[1]["drift_result"]  # Keyword arg
    assert isinstance(drift_result, DriftResult)
    assert drift_result.taxonomy == DriftTaxonomy.ALLOCATION_DRIFT
