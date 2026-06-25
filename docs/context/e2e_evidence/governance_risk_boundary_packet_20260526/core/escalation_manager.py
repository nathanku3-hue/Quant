"""
Phase 33B Slice 3: Escalation Manager

Manages escalation policy for unacknowledged drift alerts to ensure
critical drift doesn't go unnoticed.

Escalation Rules:
- YELLOW alerts: escalate after 5 minutes unacknowledged
- RED alerts: escalate after 2 minutes unacknowledged
- Max 3 escalations per alert (prevent spam)
- 30-minute cooldown between escalations
- Acknowledged/resolved alerts never escalated

Architecture:
- Runs in separate daemon thread (independent of drift checks)
- 60-second check interval (configurable)
- Atomic escalation gate (UPDATE...WHERE...RETURNING)
- Durable audit trail in escalation_history table
- Lifecycle mirrors AsyncDriftWorker pattern

CEO Execution Invariants:
- Atomic Operations: Race-safe escalation via single UPDATE with guards
- Durable Audit: All escalations persisted to DB (not just lossy telemetry)
- Fail-Closed: Invalid states raise exceptions, never silent escalation
"""

from __future__ import annotations

import json
import logging
import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import duckdb

from core.drift_alert_manager import AlertRecord, DriftAlertManager
from core.telemetry_spool import TelemetrySpool

logger = logging.getLogger(__name__)


@dataclass
class EscalationHealth:
    """Health status for escalation manager."""
    is_running: bool
    last_check_time: datetime | None
    total_checks: int
    total_escalations: int
    consecutive_errors: int


@dataclass
class EscalationEvent:
    """Escalation event record."""
    alert_id: str
    taxonomy: str
    alert_level: str
    escalation_count: int
    time_since_creation_minutes: float
    escalation_reason: str
    escalated_at: datetime
    channel: str
    channel_status: str


class EscalationManager:
    """
    Manages escalation policy for unacknowledged alerts.

    Lifecycle mirrors AsyncDriftWorker pattern:
    - start() spawns background thread
    - stop() signals shutdown and waits
    - health_check() returns status

    Phase 33B Slice 3: Minimal vertical slice with atomic escalation.
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
        """
        Initialize escalation manager.

        Args:
            alert_manager: DriftAlertManager for alert state access
            yellow_ttl_minutes: YELLOW alert escalation TTL (default: 5)
            red_ttl_minutes: RED alert escalation TTL (default: 2)
            max_escalations: Max escalations per alert (default: 3)
            cooldown_minutes: Cooldown between escalations (default: 30)
            check_interval: Check interval in seconds (default: 60)
            telemetry_spool: Optional telemetry spool for events
            worker_id: Worker identifier for telemetry
        """
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
        self._health = EscalationHealth(
            is_running=False,
            last_check_time=None,
            total_checks=0,
            total_escalations=0,
            consecutive_errors=0,
        )
        self._health_lock = threading.Lock()

        logger.info(
            "EscalationManager initialized: yellow_ttl=%dm, red_ttl=%dm, max=%d, cooldown=%dm, interval=%ds",
            yellow_ttl_minutes,
            red_ttl_minutes,
            max_escalations,
            cooldown_minutes,
            check_interval,
        )

    def start(self) -> None:
        """Start background escalation checker thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("EscalationManager already running")
            return

        self._shutdown_event.clear()
        self._thread = threading.Thread(
            target=self._escalation_loop,
            name="escalation-manager",
            daemon=True,
        )
        self._thread.start()

        with self._health_lock:
            self._health.is_running = True

        logger.info("EscalationManager started")

    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop escalation checker and wait for clean shutdown.

        Args:
            timeout: Max wait time in seconds (default: 5.0)
        """
        if self._thread is None or not self._thread.is_alive():
            logger.warning("EscalationManager not running")
            return

        logger.info("Stopping EscalationManager...")
        self._shutdown_event.set()
        self._thread.join(timeout=timeout)

        if self._thread.is_alive():
            logger.warning("EscalationManager did not stop within timeout")
        else:
            logger.info("EscalationManager stopped cleanly")

        with self._health_lock:
            self._health.is_running = False

    def health_check(self) -> EscalationHealth:
        """Get current health status."""
        with self._health_lock:
            return EscalationHealth(
                is_running=self._health.is_running,
                last_check_time=self._health.last_check_time,
                total_checks=self._health.total_checks,
                total_escalations=self._health.total_escalations,
                consecutive_errors=self._health.consecutive_errors,
            )

    def _escalation_loop(self) -> None:
        """Main loop: check alerts every check_interval seconds."""
        logger.info("Escalation loop started")

        while not self._shutdown_event.is_set():
            try:
                escalations = self._check_escalations()

                with self._health_lock:
                    self._health.last_check_time = datetime.now(timezone.utc)
                    self._health.total_checks += 1
                    self._health.total_escalations += len(escalations)
                    self._health.consecutive_errors = 0

                if escalations:
                    logger.info("Escalated %d alerts", len(escalations))

            except Exception as e:
                logger.exception("Escalation check failed: %s", e)
                with self._health_lock:
                    self._health.consecutive_errors += 1

            # Sleep with shutdown check
            self._shutdown_event.wait(timeout=self.check_interval)

        logger.info("Escalation loop stopped")

    def _check_escalations(self) -> list[EscalationEvent]:
        """
        Check all active alerts and escalate if needed (atomic).

        Handles DuckDB lock contention with retry logic.

        Returns:
            List of escalation events
        """
        now = datetime.now(timezone.utc)
        escalations: list[EscalationEvent] = []

        # Query active unacknowledged alerts with lock retry
        max_retries = 3
        retry_delay_ms = 50  # Start with 50ms

        for attempt in range(max_retries):
            try:
                with duckdb.connect(str(self.alert_manager.db_path)) as conn:
                    result = conn.execute("""
                        SELECT
                            alert_id,
                            taxonomy,
                            alert_level,
                            created_at,
                            escalation_count,
                            last_escalation_at
                        FROM alerts
                        WHERE state = 'ACTIVE'
                          AND acknowledged_at IS NULL
                        ORDER BY created_at ASC
                    """).fetchall()
                break  # Success, exit retry loop

            except duckdb.IOException as e:
                # File lock contention (common on Windows)
                if attempt < max_retries - 1:
                    # Retry with exponential backoff + jitter
                    import random
                    jitter = random.uniform(0, retry_delay_ms / 1000.0)
                    time.sleep(retry_delay_ms / 1000.0 + jitter)
                    retry_delay_ms *= 2  # Exponential backoff
                    logger.debug(
                        "DuckDB lock contention on escalation check (attempt %d/%d), retrying...",
                        attempt + 1,
                        max_retries,
                    )
                else:
                    # Max retries exceeded, skip this cycle
                    logger.warning(
                        "DuckDB lock contention persists after %d retries, skipping escalation check cycle",
                        max_retries,
                    )
                    return []  # Return empty, will retry next cycle

            except Exception as e:
                # Unexpected error, propagate
                logger.error("Escalation check query failed: %s", e)
                raise

        for row in result:
            alert_id, taxonomy, alert_level, created_at, escalation_count, last_escalation_at = row

            # Ensure timezone-aware datetimes (DuckDB returns naive)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if last_escalation_at is not None and last_escalation_at.tzinfo is None:
                last_escalation_at = last_escalation_at.replace(tzinfo=timezone.utc)

            # Determine TTL based on alert level
            if alert_level == "RED":
                ttl_minutes = self.red_ttl_minutes
            elif alert_level == "YELLOW":
                ttl_minutes = self.yellow_ttl_minutes
            else:
                continue  # GREEN alerts never escalate

            # Check if TTL expired
            ttl_cutoff = now - timedelta(minutes=ttl_minutes)
            if created_at > ttl_cutoff:
                continue  # Not yet expired

            # Check cooldown
            if last_escalation_at is not None:
                cooldown_cutoff = now - timedelta(minutes=self.cooldown_minutes)
                if last_escalation_at > cooldown_cutoff:
                    continue  # Still in cooldown

            # Check max escalations
            if escalation_count >= self.max_escalations:
                continue  # Max escalations reached

            # Attempt atomic escalation
            event = self._escalate_alert(alert_id, taxonomy, alert_level, created_at, now, ttl_cutoff)
            if event is not None:
                escalations.append(event)

        return escalations

    def _escalate_alert(
        self,
        alert_id: str,
        taxonomy: str,
        alert_level: str,
        created_at: datetime,
        now: datetime,
        ttl_cutoff: datetime,
    ) -> EscalationEvent | None:
        """
        Escalate single alert atomically.

        Returns None if escalation conditions not met (race lost, already ack'd, etc.)
        Handles DuckDB transaction conflicts gracefully (concurrent escalation attempts).
        """
        cooldown_cutoff = now - timedelta(minutes=self.cooldown_minutes)

        try:
            # Atomic escalation gate
            with duckdb.connect(str(self.alert_manager.db_path)) as conn:
                result = conn.execute("""
                    UPDATE alerts
                    SET
                        escalation_count = escalation_count + 1,
                        last_escalation_at = ?
                    WHERE
                        alert_id = ?
                        AND state = 'ACTIVE'
                        AND acknowledged_at IS NULL
                        AND created_at <= ?
                        AND (last_escalation_at IS NULL OR last_escalation_at < ?)
                        AND escalation_count < ?
                    RETURNING alert_id, escalation_count
                """, [now, alert_id, ttl_cutoff, cooldown_cutoff, self.max_escalations]).fetchall()

                if not result:
                    # Race lost or conditions not met
                    return None

                _, new_escalation_count = result[0]

                # Durable audit entry
                time_since_creation = (now - created_at).total_seconds() / 60.0
                escalation_reason = f"unacknowledged_{alert_level.lower()}_alert_ttl_exceeded"

                conn.execute("""
                    INSERT INTO escalation_history (
                        alert_id,
                        escalation_count,
                        escalated_at,
                        escalation_reason,
                        channel,
                        channel_status,
                        metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [
                    alert_id,
                    new_escalation_count,
                    now,
                    escalation_reason,
                    "log",
                    "success",
                    json.dumps({
                        "taxonomy": taxonomy,
                        "alert_level": alert_level,
                        "time_since_creation_minutes": time_since_creation,
                    }),
                ])

        except duckdb.TransactionException as e:
            # Concurrent escalation attempt - race lost, treat as no-op
            logger.debug(
                "Escalation race lost for alert_id=%s (concurrent modification): %s",
                alert_id,
                str(e),
            )
            return None
        except duckdb.IOException as e:
            # File lock contention - treat as race lost
            logger.debug(
                "DuckDB lock contention during escalation for alert_id=%s: %s",
                alert_id,
                str(e),
            )
            return None
        except Exception as e:
            # Unexpected error - log and propagate
            logger.error(
                "Escalation failed for alert_id=%s: %s",
                alert_id,
                str(e),
            )
            raise

        # Log escalation
        logger.warning(
            "ESCALATION: alert_id=%s, taxonomy=%s, level=%s, count=%d, age=%.1fm",
            alert_id,
            taxonomy,
            alert_level,
            new_escalation_count,
            time_since_creation,
        )

        # Emit telemetry event
        if self.telemetry_spool is not None:
            from core.telemetry_events import create_escalation_triggered_event
            telemetry_event = create_escalation_triggered_event(
                worker_id=self.worker_id,
                alert_id=alert_id,
                taxonomy=taxonomy,
                alert_level=alert_level,
                escalation_count=new_escalation_count,
                time_since_creation_minutes=time_since_creation,
                escalation_reason=escalation_reason,
            )
            self.telemetry_spool.write_event(telemetry_event)

        return EscalationEvent(
            alert_id=alert_id,
            taxonomy=taxonomy,
            alert_level=alert_level,
            escalation_count=new_escalation_count,
            time_since_creation_minutes=time_since_creation,
            escalation_reason=escalation_reason,
            escalated_at=now,
            channel="log",
            channel_status="success",
        )
