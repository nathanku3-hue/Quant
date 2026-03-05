"""
Async Drift Worker - Phase 33B Slice 1

Background polling worker that continuously monitors allocation drift
and persists alerts without blocking the UI thread.

Architecture:
- Runs in separate daemon thread with clean shutdown
- 60-second polling interval (configurable)
- Safe error handling with exponential backoff
- Health check endpoint for monitoring

Concurrency Safety:
- DuckDB writes are atomic (alert manager handles locking)
- Read-only access to baseline/live weights (no locks needed)
- threading.Event for clean shutdown signaling
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import pandas as pd

from core.drift_alert_manager import DriftAlertManager
from core.drift_detector import DriftDetector
from core.drift_score_normalizer import normalize_allocation_drift
from core.telemetry_events import (
    TelemetryEvent,
    create_check_started_event,
    create_check_completed_event,
    create_check_failed_event,
)
from core.telemetry_spool import TelemetrySpool

logger = logging.getLogger(__name__)


@dataclass
class WorkerHealth:
    """Health status for async drift worker."""
    is_running: bool
    last_check_time: datetime | None
    consecutive_errors: int
    total_checks: int
    total_alerts: int


class AsyncDriftWorker:
    """
    Background worker for continuous drift monitoring.

    Phase 33B Slice 1: Minimal vertical slice with lifecycle management.

    Usage:
        worker = AsyncDriftWorker(
            alert_manager=alert_manager,
            drift_detector=drift_detector,
            baseline_loader=load_baseline_fn,
            live_loader=load_live_fn,
            poll_interval=60,
        )
        worker.start()
        # ... worker runs in background ...
        worker.stop()  # Clean shutdown
    """

    def __init__(
        self,
        alert_manager: DriftAlertManager,
        drift_detector: DriftDetector,
        baseline_loader: Callable[[], tuple[pd.Series | None, dict | None]],
        live_loader: Callable[[], pd.Series | None],
        *,
        poll_interval: int = 60,
        max_consecutive_errors: int = 10,
        telemetry_spool: TelemetrySpool | None = None,
        worker_id: str = "async_drift_worker",
        escalation_manager: "EscalationManager | None" = None,
    ):
        """
        Initialize async drift worker.

        Args:
            alert_manager: DriftAlertManager for persisting alerts
            drift_detector: DriftDetector for detecting allocation drift
            baseline_loader: Callable that returns (baseline_weights, metadata)
            live_loader: Callable that returns live_weights
            poll_interval: Seconds between drift checks (default: 60)
            max_consecutive_errors: Stop worker after N consecutive errors (default: 10)
            telemetry_spool: Optional TelemetrySpool for event logging (Phase 33B Slice 2)
            worker_id: Worker instance identifier for telemetry (default: "async_drift_worker")
            escalation_manager: Optional EscalationManager for alert escalation (Phase 33B Slice 3)
        """
        self.alert_manager = alert_manager
        self.drift_detector = drift_detector
        self.baseline_loader = baseline_loader
        self.live_loader = live_loader
        self.poll_interval = poll_interval
        self.max_consecutive_errors = max_consecutive_errors
        self.telemetry_spool = telemetry_spool
        self.worker_id = worker_id
        self.escalation_manager = escalation_manager

        # Worker state
        self._thread: threading.Thread | None = None
        self._shutdown_event = threading.Event()
        self._health = WorkerHealth(
            is_running=False,
            last_check_time=None,
            consecutive_errors=0,
            total_checks=0,
            total_alerts=0,
        )
        self._health_lock = threading.Lock()

    def start(self) -> None:
        """
        Start background drift monitoring worker.

        Spawns daemon thread that polls for drift every poll_interval seconds.
        Thread will stop when stop() is called or on unrecoverable error.

        Phase 33B Slice 3: Also starts escalation manager if configured.
        """
        if self._thread is not None and self._thread.is_alive():
            logger.warning("AsyncDriftWorker already running, ignoring start()")
            return

        self._shutdown_event.clear()
        self._thread = threading.Thread(
            target=self._poll_loop,
            name="AsyncDriftWorker",
            daemon=True,  # Ensure clean shutdown on process exit
        )

        with self._health_lock:
            self._health.is_running = True
            self._health.consecutive_errors = 0

        self._thread.start()
        logger.info(f"AsyncDriftWorker started (poll_interval={self.poll_interval}s)")

        # Start escalation manager if configured
        if self.escalation_manager is not None:
            self.escalation_manager.start()
            logger.info("EscalationManager started with AsyncDriftWorker")

    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop background drift monitoring worker.

        Signals shutdown and waits for worker thread to exit cleanly.

        Phase 33B Slice 3: Also stops escalation manager if configured.

        Args:
            timeout: Max seconds to wait for thread to stop (default: 5.0)
        """
        # Stop escalation manager first
        if self.escalation_manager is not None:
            self.escalation_manager.stop(timeout=timeout)
            logger.info("EscalationManager stopped")

        if self._thread is None or not self._thread.is_alive():
            logger.info("AsyncDriftWorker not running, nothing to stop")
            return

        logger.info("Stopping AsyncDriftWorker...")
        self._shutdown_event.set()
        self._thread.join(timeout=timeout)

        if self._thread.is_alive():
            logger.warning(f"AsyncDriftWorker did not stop within {timeout}s timeout")
        else:
            logger.info("AsyncDriftWorker stopped cleanly")

        with self._health_lock:
            self._health.is_running = False

    def health_check(self) -> WorkerHealth:
        """
        Get current health status of worker.

        Returns:
            WorkerHealth with is_running, last_check_time, error counts, etc.
        """
        with self._health_lock:
            return WorkerHealth(
                is_running=self._health.is_running,
                last_check_time=self._health.last_check_time,
                consecutive_errors=self._health.consecutive_errors,
                total_checks=self._health.total_checks,
                total_alerts=self._health.total_alerts,
            )

    def _poll_loop(self) -> None:
        """
        Main polling loop (runs in background thread).

        Continuously checks for drift until shutdown signal received.
        Handles errors with exponential backoff and stops on repeated failures.
        """
        logger.info("AsyncDriftWorker poll loop started")

        while not self._shutdown_event.is_set():
            try:
                self._execute_drift_check()

                # Reset error count on successful check
                with self._health_lock:
                    self._health.consecutive_errors = 0

                # Sleep with interruptible wait (check shutdown every 1s)
                for _ in range(self.poll_interval):
                    if self._shutdown_event.is_set():
                        break
                    time.sleep(1)

            except Exception as e:
                with self._health_lock:
                    self._health.consecutive_errors += 1
                    error_count = self._health.consecutive_errors

                logger.error(
                    f"AsyncDriftWorker poll error ({error_count}/{self.max_consecutive_errors}): {e}",
                    exc_info=True,
                )

                # Emit check_failed event
                if self.telemetry_spool:
                    try:
                        backoff_seconds = min(self.poll_interval * (2 ** (error_count - 1)), 300)
                        event = create_check_failed_event(
                            worker_id=self.worker_id,
                            error_type=type(e).__name__,
                            error_message=str(e),
                            consecutive_errors=error_count,
                            backoff_seconds=backoff_seconds if error_count < self.max_consecutive_errors else None,
                        )
                        self.telemetry_spool.write_event(event)
                    except Exception as telemetry_error:
                        logger.warning(f"Failed to emit check_failed event: {telemetry_error}")

                # Stop worker on repeated failures
                if error_count >= self.max_consecutive_errors:
                    logger.critical(
                        f"AsyncDriftWorker stopping after {error_count} consecutive errors"
                    )
                    with self._health_lock:
                        self._health.is_running = False
                    break

                # Exponential backoff on errors (60s → 120s → 240s, max 300s)
                backoff_seconds = min(self.poll_interval * (2 ** (error_count - 1)), 300)
                logger.info(f"AsyncDriftWorker backing off for {backoff_seconds}s")

                # Interruptible backoff wait (check shutdown every 1s)
                for _ in range(int(backoff_seconds)):
                    if self._shutdown_event.is_set():
                        break
                    time.sleep(1)

        logger.info("AsyncDriftWorker poll loop exited")

    def _execute_drift_check(self) -> None:
        """
        Execute single drift check cycle.

        Phase 33B Slice 1: Wire detector → normalizer → alert manager.
        Phase 33B Slice 2: Add telemetry emission.

        Steps:
        1. Load baseline + live weights
        2. Emit check_started event
        3. Detect drift (DriftDetector)
        4. Normalize scores (DriftScoreNormalizer)
        5. Persist alerts (DriftAlertManager)
        6. Emit check_completed event
        7. Update health metrics
        """
        check_start = time.time()

        # Load weights
        baseline_weights, baseline_metadata = self.baseline_loader()
        live_weights = self.live_loader()

        # Extract baseline context for telemetry
        baseline_id = baseline_metadata.get("baseline_id") if baseline_metadata else None
        baseline_strategy = baseline_metadata.get("strategy_name") if baseline_metadata else None

        # Emit check_started event
        if self.telemetry_spool:
            try:
                event = create_check_started_event(
                    worker_id=self.worker_id,
                    baseline_id=baseline_id,
                    baseline_strategy=baseline_strategy,
                )
                self.telemetry_spool.write_event(event)
            except Exception as e:
                logger.warning(f"Failed to emit check_started event: {e}")

        if baseline_weights is None or live_weights is None:
            logger.debug("AsyncDriftWorker: baseline or live weights unavailable, skipping check")
            return

        # Detect drift
        drift_result = self.drift_detector.detect_allocation_drift(
            expected_weights=baseline_weights,
            actual_weights=live_weights,
        )

        # Normalize score
        normalized_score = normalize_allocation_drift(drift_result.drift_score)

        # Process through alert lifecycle (handles severity classification, suppression, etc.)
        alert_record = self.alert_manager.process_drift_result(
            drift_result=drift_result,
            normalized_score=normalized_score,
        )

        check_duration_ms = (time.time() - check_start) * 1000

        # Emit check_completed event
        if self.telemetry_spool:
            try:
                event = create_check_completed_event(
                    worker_id=self.worker_id,
                    duration_ms=check_duration_ms,
                    drift_score=drift_result.drift_score,
                    normalized_score=normalized_score,
                    alert_created=(alert_record is not None),
                    alert_level=alert_record.alert_level if alert_record else None,
                    baseline_id=baseline_id,
                )
                self.telemetry_spool.write_event(event)
                self.telemetry_spool.rotate_if_needed()  # Check rotation after write
            except Exception as e:
                logger.warning(f"Failed to emit check_completed event: {e}")

        # Update health metrics
        with self._health_lock:
            self._health.total_checks += 1
            if alert_record is not None:
                self._health.total_alerts += 1
            self._health.last_check_time = datetime.now()

        if alert_record:
            logger.info(
                f"AsyncDriftWorker: drift alert created "
                f"(level={alert_record.alert_level}, duration={check_duration_ms:.0f}ms)"
            )
        else:
            logger.debug(
                f"AsyncDriftWorker: drift check complete, no alert "
                f"(score={normalized_score:.2f}, duration={check_duration_ms:.0f}ms)"
            )
