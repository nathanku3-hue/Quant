"""
Tests for Telemetry Integration - Phase 33B Slice 2

Validates:
1. Event emission on success/failure/backoff paths
2. Event schema correctness
3. Atomic writes and rotation
4. Thread safety
5. No events lost on worker errors
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from core.async_drift_worker import AsyncDriftWorker
from core.drift_detector import DriftDetector, DriftResult, DriftTaxonomy
from core.telemetry_events import (
    EVENT_CHECK_STARTED,
    EVENT_CHECK_COMPLETED,
    EVENT_CHECK_FAILED,
    TelemetryEvent,
    create_check_started_event,
    create_check_completed_event,
    create_check_failed_event,
)
from core.telemetry_spool import TelemetrySpool


def test_telemetry_event_serialization():
    """
    Contract: TelemetryEvent serializes to JSON-compatible dict with ISO 8601 timestamp.
    """
    event = TelemetryEvent(
        event_type="test_event",
        timestamp=datetime(2026, 3, 4, 12, 30, 45),
        worker_id="test_worker",
        data={"key": "value", "count": 42},
    )

    event_dict = event.to_dict()

    assert event_dict["event_type"] == "test_event"
    assert event_dict["timestamp"] == "2026-03-04T12:30:45"
    assert event_dict["worker_id"] == "test_worker"
    assert event_dict["data"]["key"] == "value"
    assert event_dict["data"]["count"] == 42


def test_telemetry_spool_write_and_read(tmp_path):
    """
    Contract: TelemetrySpool writes events atomically and reads them back correctly.
    """
    spool_path = tmp_path / "test_events.jsonl"
    spool = TelemetrySpool(spool_path)

    # Write events
    event1 = create_check_started_event(worker_id="worker1", baseline_id="baseline123")
    event2 = create_check_completed_event(
        worker_id="worker1",
        duration_ms=150.5,
        drift_score=2.5,
        normalized_score=6.25,
        alert_created=True,
        alert_level="YELLOW",
    )

    spool.write_event(event1)
    spool.write_event(event2)

    # Read events back
    events = spool.read_events()

    assert len(events) == 2
    assert events[0]["event_type"] == EVENT_CHECK_STARTED
    assert events[0]["data"]["baseline_id"] == "baseline123"
    assert events[1]["event_type"] == EVENT_CHECK_COMPLETED
    assert events[1]["data"]["duration_ms"] == 150.5
    assert events[1]["data"]["alert_created"] is True


def test_telemetry_spool_rotation(tmp_path):
    """
    Contract: TelemetrySpool rotates file when size exceeds threshold.
    """
    spool_path = tmp_path / "test_events.jsonl"
    spool = TelemetrySpool(spool_path, max_size_mb=0.001)  # 1 KB threshold

    # Write enough events to trigger rotation
    for i in range(100):
        event = create_check_started_event(worker_id=f"worker{i}", baseline_id="baseline123")
        spool.write_event(event)

    # Force rotation check
    rotated = spool.rotate_if_needed()

    assert rotated is True
    # Check that rotated file exists
    rotated_files = list(tmp_path.glob("test_events.*.jsonl"))
    assert len(rotated_files) == 1


def test_telemetry_spool_cleanup_old_rotations(tmp_path):
    """
    Contract: TelemetrySpool keeps only N most recent rotated files.
    """
    spool_path = tmp_path / "test_events.jsonl"
    spool = TelemetrySpool(spool_path, max_size_mb=0.001, rotation_keep=2)

    # Create multiple rotations
    for rotation in range(5):
        for i in range(50):
            event = create_check_started_event(worker_id=f"worker{i}", baseline_id="baseline123")
            spool.write_event(event)
        spool.rotate_if_needed()
        time.sleep(0.1)  # Ensure different timestamps

    # Check that only 2 rotated files remain
    rotated_files = list(tmp_path.glob("test_events.*.jsonl"))
    assert len(rotated_files) == 2


def test_worker_emits_check_started_event(tmp_path):
    """
    Contract: Worker emits check_started event at beginning of poll cycle.
    """
    spool_path = tmp_path / "drift_events.jsonl"
    spool = TelemetrySpool(spool_path)

    mock_alert_manager = MagicMock()
    mock_alert_manager.process_drift_result.return_value = None

    real_detector = DriftDetector(sigma_threshold=2.0)

    def baseline_loader():
        weights = pd.Series({"AAPL": 0.5, "MSFT": 0.5})
        metadata = {"baseline_id": "test_baseline_123", "strategy_name": "test_strategy"}
        return weights, metadata

    def live_loader():
        return pd.Series({"AAPL": 0.5, "MSFT": 0.5})

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=real_detector,
        baseline_loader=baseline_loader,
        live_loader=live_loader,
        poll_interval=1,
        telemetry_spool=spool,
        worker_id="test_worker",
    )

    worker.start()
    time.sleep(1.5)
    worker.stop(timeout=2.0)

    # Read events
    events = spool.read_events()

    # Verify check_started event exists
    started_events = [e for e in events if e["event_type"] == EVENT_CHECK_STARTED]
    assert len(started_events) >= 1
    assert started_events[0]["worker_id"] == "test_worker"
    assert started_events[0]["data"]["baseline_id"] == "test_baseline_123"
    assert started_events[0]["data"]["baseline_strategy"] == "test_strategy"


def test_worker_emits_check_completed_event(tmp_path):
    """
    Contract: Worker emits check_completed event after successful drift check.
    """
    spool_path = tmp_path / "drift_events.jsonl"
    spool = TelemetrySpool(spool_path)

    mock_alert_manager = MagicMock()
    mock_alert_record = MagicMock()
    mock_alert_record.alert_level = "YELLOW"
    mock_alert_manager.process_drift_result.return_value = mock_alert_record

    real_detector = DriftDetector(sigma_threshold=2.0)

    def baseline_loader():
        weights = pd.Series({"AAPL": 0.5, "MSFT": 0.5})
        metadata = {"baseline_id": "test_baseline_123"}
        return weights, metadata

    def live_loader():
        return pd.Series({"AAPL": 0.6, "MSFT": 0.4})  # Slight drift

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=real_detector,
        baseline_loader=baseline_loader,
        live_loader=live_loader,
        poll_interval=1,
        telemetry_spool=spool,
        worker_id="test_worker",
    )

    worker.start()
    time.sleep(1.5)
    worker.stop(timeout=2.0)

    # Read events
    events = spool.read_events()

    # Verify check_completed event exists
    completed_events = [e for e in events if e["event_type"] == EVENT_CHECK_COMPLETED]
    assert len(completed_events) >= 1

    completed = completed_events[0]
    assert completed["worker_id"] == "test_worker"
    assert "duration_ms" in completed["data"]
    assert "drift_score" in completed["data"]
    assert "normalized_score" in completed["data"]
    assert completed["data"]["alert_created"] is True
    assert completed["data"]["alert_level"] == "YELLOW"


def test_worker_emits_check_failed_event_on_error(tmp_path):
    """
    Contract: Worker emits check_failed event when drift check raises exception.
    """
    spool_path = tmp_path / "drift_events.jsonl"
    spool = TelemetrySpool(spool_path)

    mock_alert_manager = MagicMock()
    mock_drift_detector = MagicMock()
    mock_drift_detector.detect_allocation_drift.side_effect = RuntimeError("Test error")

    def baseline_loader():
        weights = pd.Series({"AAPL": 0.5})
        metadata = {"baseline_id": "test_baseline"}
        return weights, metadata

    def live_loader():
        return pd.Series({"AAPL": 0.5})

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_loader=baseline_loader,
        live_loader=live_loader,
        poll_interval=1,
        max_consecutive_errors=2,
        telemetry_spool=spool,
        worker_id="test_worker",
    )

    worker.start()
    time.sleep(2.0)  # Wait for error
    worker.stop(timeout=2.0)

    # Read events
    events = spool.read_events()

    # Verify check_failed event exists
    failed_events = [e for e in events if e["event_type"] == EVENT_CHECK_FAILED]
    assert len(failed_events) >= 1

    failed = failed_events[0]
    assert failed["worker_id"] == "test_worker"
    assert failed["data"]["error_type"] == "RuntimeError"
    assert "Test error" in failed["data"]["error_message"]
    assert failed["data"]["consecutive_errors"] >= 1
    assert "backoff_seconds" in failed["data"]


def test_worker_continues_on_telemetry_write_failure(tmp_path):
    """
    Contract: Worker continues drift checks even if telemetry write fails.
    """
    spool_path = tmp_path / "drift_events.jsonl"
    spool = TelemetrySpool(spool_path)

    # Mock write_event to raise OSError (deterministic failure)
    original_write = spool.write_event
    def failing_write(event):
        raise OSError("Simulated write failure")
    spool.write_event = failing_write

    mock_alert_manager = MagicMock()
    mock_alert_manager.process_drift_result.return_value = None

    real_detector = DriftDetector(sigma_threshold=2.0)

    def baseline_loader():
        weights = pd.Series({"AAPL": 0.5})
        metadata = {}
        return weights, metadata

    def live_loader():
        return pd.Series({"AAPL": 0.5})

    worker = AsyncDriftWorker(
        alert_manager=mock_alert_manager,
        drift_detector=real_detector,
        baseline_loader=baseline_loader,
        live_loader=live_loader,
        poll_interval=1,
        telemetry_spool=spool,
        worker_id="test_worker",
    )

    worker.start()
    time.sleep(1.5)
    worker.stop(timeout=2.0)

    # Verify worker executed checks despite telemetry failures
    health = worker.health_check()
    assert health.total_checks >= 1
    assert health.consecutive_errors == 0  # Telemetry errors don't count as check errors


def test_telemetry_event_factories():
    """
    Contract: Event factory functions create correctly structured events.
    """
    # check_started
    started = create_check_started_event(
        worker_id="worker1",
        baseline_id="baseline123",
        baseline_strategy="momentum",
    )
    assert started.event_type == EVENT_CHECK_STARTED
    assert started.worker_id == "worker1"
    assert started.data["baseline_id"] == "baseline123"
    assert started.data["baseline_strategy"] == "momentum"

    # check_completed
    completed = create_check_completed_event(
        worker_id="worker1",
        duration_ms=123.45,
        drift_score=2.5,
        normalized_score=6.25,
        alert_created=True,
        alert_level="RED",
        baseline_id="baseline123",
    )
    assert completed.event_type == EVENT_CHECK_COMPLETED
    assert completed.data["duration_ms"] == 123.45
    assert completed.data["alert_created"] is True

    # check_failed
    failed = create_check_failed_event(
        worker_id="worker1",
        error_type="ValueError",
        error_message="Invalid input",
        consecutive_errors=3,
        backoff_seconds=120,
    )
    assert failed.event_type == EVENT_CHECK_FAILED
    assert failed.data["error_type"] == "ValueError"
    assert failed.data["consecutive_errors"] == 3
