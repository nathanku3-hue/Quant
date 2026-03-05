"""
Telemetry Event Schema - Phase 33B Slice 2

Defines structured events for drift monitoring telemetry.
Events are emitted to append-only JSONL spool for observability.

Event Types:
- drift_check_started: Poll cycle initiated
- drift_check_completed: Drift detection completed successfully
- drift_check_failed: Drift detection failed with error
- drift_alert_created: Alert created by alert manager
- drift_alert_suppressed: Alert suppressed by lifecycle rules
- escalation_triggered: Alert escalated due to unacknowledged TTL expiry

Schema Design:
- All events have: event_type, timestamp, worker_id
- Event-specific fields in 'data' dict for extensibility
- Timestamps in ISO 8601 UTC format
- Baseline context included when available
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TelemetryEvent:
    """
    Structured telemetry event for drift monitoring.

    Phase 33B Slice 2: Observability foundation for async drift pipeline.

    Fields:
        event_type: Event classification (drift_check_started, etc.)
        timestamp: Event occurrence time (UTC)
        worker_id: Worker instance identifier (for multi-worker scenarios)
        data: Event-specific payload (extensible dict)
    """
    event_type: str
    timestamp: datetime
    worker_id: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize event to JSON-compatible dict.

        Returns:
            Dict with ISO 8601 timestamp and all fields
        """
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "worker_id": self.worker_id,
            "data": self.data,
        }


# Event type constants
EVENT_CHECK_STARTED = "drift_check_started"
EVENT_CHECK_COMPLETED = "drift_check_completed"
EVENT_CHECK_FAILED = "drift_check_failed"
EVENT_ALERT_CREATED = "drift_alert_created"
EVENT_ALERT_SUPPRESSED = "drift_alert_suppressed"
EVENT_ESCALATION_TRIGGERED = "escalation_triggered"


def create_check_started_event(
    worker_id: str,
    baseline_id: str | None = None,
    baseline_strategy: str | None = None,
) -> TelemetryEvent:
    """
    Create drift_check_started event.

    Args:
        worker_id: Worker instance identifier
        baseline_id: Baseline identifier (if available)
        baseline_strategy: Strategy name (if available)

    Returns:
        TelemetryEvent with check start context
    """
    data = {}
    if baseline_id:
        data["baseline_id"] = baseline_id
    if baseline_strategy:
        data["baseline_strategy"] = baseline_strategy

    return TelemetryEvent(
        event_type=EVENT_CHECK_STARTED,
        timestamp=datetime.now(timezone.utc),
        worker_id=worker_id,
        data=data,
    )


def create_check_completed_event(
    worker_id: str,
    duration_ms: float,
    drift_score: float,
    normalized_score: float,
    alert_created: bool,
    alert_level: str | None = None,
    baseline_id: str | None = None,
) -> TelemetryEvent:
    """
    Create drift_check_completed event.

    Args:
        worker_id: Worker instance identifier
        duration_ms: Check duration in milliseconds
        drift_score: Raw drift score from detector
        normalized_score: Normalized score [0, 10]
        alert_created: Whether alert was created (not suppressed)
        alert_level: Alert level if created (GREEN/YELLOW/RED)
        baseline_id: Baseline identifier (if available)

    Returns:
        TelemetryEvent with check completion metrics
    """
    data = {
        "duration_ms": duration_ms,
        "drift_score": drift_score,
        "normalized_score": normalized_score,
        "alert_created": alert_created,
    }

    if alert_level:
        data["alert_level"] = alert_level
    if baseline_id:
        data["baseline_id"] = baseline_id

    return TelemetryEvent(
        event_type=EVENT_CHECK_COMPLETED,
        timestamp=datetime.now(timezone.utc),
        worker_id=worker_id,
        data=data,
    )


def create_check_failed_event(
    worker_id: str,
    error_type: str,
    error_message: str,
    consecutive_errors: int,
    backoff_seconds: int | None = None,
) -> TelemetryEvent:
    """
    Create drift_check_failed event.

    Args:
        worker_id: Worker instance identifier
        error_type: Exception class name
        error_message: Error message
        consecutive_errors: Count of consecutive failures
        backoff_seconds: Backoff duration if applicable

    Returns:
        TelemetryEvent with error context
    """
    data = {
        "error_type": error_type,
        "error_message": error_message,
        "consecutive_errors": consecutive_errors,
    }

    if backoff_seconds is not None:
        data["backoff_seconds"] = backoff_seconds

    return TelemetryEvent(
        event_type=EVENT_CHECK_FAILED,
        timestamp=datetime.now(timezone.utc),
        worker_id=worker_id,
        data=data,
    )


def create_alert_created_event(
    worker_id: str,
    alert_id: str,
    taxonomy: str,
    alert_level: str,
    drift_score: float,
    normalized_score: float,
) -> TelemetryEvent:
    """
    Create drift_alert_created event.

    Args:
        worker_id: Worker instance identifier
        alert_id: Alert unique identifier
        taxonomy: Drift taxonomy (ALLOCATION_DRIFT, etc.)
        alert_level: Alert severity (GREEN/YELLOW/RED)
        drift_score: Raw drift score
        normalized_score: Normalized score [0, 10]

    Returns:
        TelemetryEvent with alert creation context
    """
    return TelemetryEvent(
        event_type=EVENT_ALERT_CREATED,
        timestamp=datetime.now(timezone.utc),
        worker_id=worker_id,
        data={
            "alert_id": alert_id,
            "taxonomy": taxonomy,
            "alert_level": alert_level,
            "drift_score": drift_score,
            "normalized_score": normalized_score,
        },
    )


def create_alert_suppressed_event(
    worker_id: str,
    taxonomy: str,
    suppression_reason: str,
    drift_score: float,
    normalized_score: float,
) -> TelemetryEvent:
    """
    Create drift_alert_suppressed event.

    Args:
        worker_id: Worker instance identifier
        taxonomy: Drift taxonomy
        suppression_reason: Why alert was suppressed (dedup, ack, cooldown, etc.)
        drift_score: Raw drift score
        normalized_score: Normalized score [0, 10]

    Returns:
        TelemetryEvent with suppression context
    """
    return TelemetryEvent(
        event_type=EVENT_ALERT_SUPPRESSED,
        timestamp=datetime.now(timezone.utc),
        worker_id=worker_id,
        data={
            "taxonomy": taxonomy,
            "suppression_reason": suppression_reason,
            "drift_score": drift_score,
            "normalized_score": normalized_score,
        },
    )


def create_escalation_triggered_event(
    worker_id: str,
    alert_id: str,
    taxonomy: str,
    alert_level: str,
    escalation_count: int,
    time_since_creation_minutes: float,
    escalation_reason: str,
) -> TelemetryEvent:
    """
    Create escalation_triggered event.

    Phase 33B Slice 3: Escalation policy telemetry.

    Args:
        worker_id: Worker instance identifier
        alert_id: Alert unique identifier
        taxonomy: Drift taxonomy (ALLOCATION_DRIFT, etc.)
        alert_level: Alert severity (YELLOW/RED)
        escalation_count: Current escalation count for this alert
        time_since_creation_minutes: Minutes since alert creation
        escalation_reason: Why alert was escalated

    Returns:
        TelemetryEvent with escalation context
    """
    return TelemetryEvent(
        event_type=EVENT_ESCALATION_TRIGGERED,
        timestamp=datetime.now(timezone.utc),
        worker_id=worker_id,
        data={
            "alert_id": alert_id,
            "taxonomy": taxonomy,
            "alert_level": alert_level,
            "escalation_count": escalation_count,
            "time_since_creation_minutes": time_since_creation_minutes,
            "escalation_reason": escalation_reason,
        },
    )
