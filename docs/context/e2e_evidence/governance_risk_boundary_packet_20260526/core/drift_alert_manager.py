"""
Phase 33A Step 5: Alert Lifecycle Persistence

Manages drift alert lifecycle to prevent alert storms, flapping, and noise through:
- Deduplication: Suppress duplicate alerts within time window
- Hysteresis: Require consecutive breaches before escalation
- Cooldown: Suppress alerts after resolution to prevent storms
- Acknowledgement: Manual suppression with TTL

CEO Execution Invariants:
- DuckDB Backend: NOT SQLite (per AGENTS.md:12) for production reliability
- Fail-Closed: Invalid states raise exceptions, never silent GREEN
- Atomic Operations: All state transitions are transactional
- Audit Trail: All lifecycle events logged for forensic analysis

FR-TBD: Alert lifecycle as institutional standard (Renaissance/Two Sigma/Citadel)
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import duckdb

from core.drift_detector import DriftResult, DriftTaxonomy


class AlertState(str, Enum):
    """Alert lifecycle states."""
    ACTIVE = "ACTIVE"           # Alert currently firing
    ACKNOWLEDGED = "ACKNOWLEDGED"  # Manually acknowledged by user
    RESOLVED = "RESOLVED"       # Drift returned to normal
    SUPERSEDED = "SUPERSEDED"   # Replaced by newer ACTIVE alert for taxonomy
    SUPPRESSED = "SUPPRESSED"   # Suppressed by dedup/cooldown/hysteresis


class AlertLevel(str, Enum):
    """Alert severity levels (aligned with drift_detector.py)."""
    GREEN = "GREEN"     # < 5.0 normalized score
    YELLOW = "YELLOW"   # 5.0 - 9.9 normalized score
    RED = "RED"         # >= 10.0 normalized score


@dataclass
class AlertRecord:
    """
    Immutable alert lifecycle record.

    Fields:
        alert_id: Unique alert identifier (drift_uid + timestamp)
        drift_uid: Drift event UID from DriftResult
        taxonomy: Drift taxonomy (ALLOCATION/REGIME/PARAMETER/SCHEDULE)
        drift_score: Raw drift score from detector
        normalized_score: Normalized score [0, 10] from normalizer
        alert_level: GREEN/YELLOW/RED based on normalized score
        state: Alert lifecycle state (ACTIVE/ACKNOWLEDGED/RESOLVED/SUPPRESSED)
        created_at: Alert creation timestamp (UTC)
        updated_at: Last state transition timestamp (UTC)
        acknowledged_at: Manual acknowledgement timestamp (UTC, optional)
        resolved_at: Resolution timestamp (UTC, optional)
        suppression_reason: Why alert was suppressed (optional)
        details: JSON-serializable forensic context
    """
    alert_id: str
    drift_uid: str
    taxonomy: str
    drift_score: float
    normalized_score: float
    alert_level: str
    state: str
    created_at: datetime
    updated_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    suppression_reason: str | None = None
    details: dict[str, Any] | None = None


class DriftAlertManager:
    """
    Alert lifecycle manager with DuckDB persistence.

    Implements institutional best practices:
    - Deduplication: Same drift_uid within 1 hour → suppress
    - Hysteresis: Require 2 consecutive breaches before RED alert
    - Cooldown: After RED cleared, suppress new alerts for 15 minutes
    - Acknowledgement: Manual "Ack Drift" → suppress for 4 hours
    """

    def __init__(
        self,
        db_path: Path | str = "data/drift_alerts.duckdb",
        dedup_window_minutes: int = 60,
        hysteresis_threshold: int = 2,
        cooldown_minutes: int = 15,
        ack_ttl_hours: int = 4,
    ):
        """
        Initialize alert manager with DuckDB backend.

        Args:
            db_path: Path to DuckDB database file
            dedup_window_minutes: Deduplication window (default: 60 min)
            hysteresis_threshold: Consecutive breaches required (default: 2)
            cooldown_minutes: Cooldown after resolution (default: 15 min)
            ack_ttl_hours: Acknowledgement TTL (default: 4 hours)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.dedup_window = timedelta(minutes=dedup_window_minutes)
        self.hysteresis_threshold = hysteresis_threshold
        self.cooldown_period = timedelta(minutes=cooldown_minutes)
        self.ack_ttl = timedelta(hours=ack_ttl_hours)

        self._init_database()

        logging.info(
            "DriftAlertManager initialized: db=%s, dedup=%dm, hysteresis=%d, cooldown=%dm, ack_ttl=%dh",
            self.db_path,
            dedup_window_minutes,
            hysteresis_threshold,
            cooldown_minutes,
            ack_ttl_hours,
        )

    def _init_database(self) -> None:
        """
        Initialize DuckDB schema for alert persistence.

        Schema:
        - alerts: Main alert records table
        - alert_history: State transition audit trail
        - breach_counter: Hysteresis tracking (consecutive breaches)
        """
        with duckdb.connect(str(self.db_path)) as conn:
            # Main alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id VARCHAR PRIMARY KEY,
                    drift_uid VARCHAR NOT NULL,
                    taxonomy VARCHAR NOT NULL,
                    drift_score DOUBLE NOT NULL,
                    normalized_score DOUBLE NOT NULL,
                    alert_level VARCHAR NOT NULL,
                    state VARCHAR NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    acknowledged_at TIMESTAMP,
                    resolved_at TIMESTAMP,
                    suppression_reason VARCHAR,
                    details JSON
                )
            """)

            # State transition audit trail
            conn.execute("""
                CREATE SEQUENCE IF NOT EXISTS seq_history_id START 1
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    history_id INTEGER PRIMARY KEY DEFAULT nextval('seq_history_id'),
                    alert_id VARCHAR NOT NULL,
                    from_state VARCHAR,
                    to_state VARCHAR NOT NULL,
                    transition_at TIMESTAMP NOT NULL,
                    reason VARCHAR
                )
            """)

            # Hysteresis tracking (consecutive breaches per taxonomy)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS breach_counter (
                    taxonomy VARCHAR PRIMARY KEY,
                    consecutive_breaches INTEGER NOT NULL DEFAULT 0,
                    last_breach_at TIMESTAMP NOT NULL,
                    last_breach_score DOUBLE NOT NULL
                )
            """)

            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_drift_uid ON alerts(drift_uid)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_taxonomy ON alerts(taxonomy)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_state ON alerts(state)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_alert_id ON alert_history(alert_id)")

            # Phase 33B Slice 3: Escalation columns migration
            conn.execute("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS escalation_count INTEGER DEFAULT 0")
            conn.execute("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS last_escalation_at TIMESTAMP")
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_escalation
                ON alerts(state, alert_level, created_at, escalation_count)
            """)

            # Phase 33B Slice 3: Escalation audit table
            conn.execute("CREATE SEQUENCE IF NOT EXISTS escalation_history_seq START 1")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS escalation_history (
                    escalation_id INTEGER PRIMARY KEY DEFAULT nextval('escalation_history_seq'),
                    alert_id VARCHAR NOT NULL,
                    escalation_count INTEGER NOT NULL,
                    escalated_at TIMESTAMP NOT NULL,
                    escalation_reason VARCHAR NOT NULL,
                    channel VARCHAR,
                    channel_status VARCHAR,
                    metadata VARCHAR
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_escalation_alert
                ON escalation_history(alert_id, escalated_at)
            """)

    def process_drift_result(
        self,
        drift_result: DriftResult,
        normalized_score: float,
    ) -> AlertRecord | None:
        """
        Process drift detection result through alert lifecycle.

        Lifecycle Decision Tree:
        1. Compute alert level + reset hysteresis counter on non-RED
        2. GREEN event: suppress immediately (no alert persistence)
        3. Check deduplication: Same drift_uid within window? → SUPPRESSED
        4. Check acknowledgement: Active ack for taxonomy? → SUPPRESSED
        5. Check cooldown: Recent resolution for taxonomy? → SUPPRESSED
        6. Check hysteresis: Consecutive breaches < threshold? → SUPPRESSED
        7. Otherwise: Create ACTIVE alert (superseding prior ACTIVE taxonomy alert)

        Args:
            drift_result: DriftResult from drift detector
            normalized_score: Normalized score [0, 10] from normalizer

        Returns:
            AlertRecord if alert created/updated, None if suppressed

        Raises:
            ValueError: If normalized_score out of bounds [0, 10]
        """
        # Validate normalized score
        if not 0.0 <= normalized_score <= 10.0:
            raise ValueError(
                f"Invalid normalized_score: {normalized_score}. "
                "Must be in [0, 10] range."
            )

        # Determine alert level from normalized score
        alert_level = self._compute_alert_level(normalized_score)

        # Strict hysteresis: any non-RED event breaks consecutive breach chain
        if alert_level != AlertLevel.RED:
            self._reset_hysteresis_counter(drift_result.taxonomy)

        # GREEN is baseline telemetry only; do not create lifecycle alerts
        if alert_level == AlertLevel.GREEN:
            logging.debug(
                "Alert suppressed (GREEN level): drift_uid=%s, taxonomy=%s, score=%.2f",
                drift_result.uid,
                drift_result.taxonomy,
                normalized_score,
            )
            return None

        # Check deduplication
        if self._is_duplicate(drift_result.uid):
            logging.debug(
                "Alert suppressed (deduplication): drift_uid=%s, taxonomy=%s",
                drift_result.uid,
                drift_result.taxonomy,
            )
            return None

        # Check acknowledgement
        if self._is_acknowledged(drift_result.taxonomy):
            logging.debug(
                "Alert suppressed (acknowledged): taxonomy=%s",
                drift_result.taxonomy,
            )
            return None

        # Check cooldown
        if self._is_in_cooldown(drift_result.taxonomy):
            logging.debug(
                "Alert suppressed (cooldown): taxonomy=%s",
                drift_result.taxonomy,
            )
            return None

        # Check hysteresis (only for RED alerts)
        if alert_level == AlertLevel.RED:
            if not self._check_hysteresis(drift_result.taxonomy, normalized_score):
                logging.debug(
                    "Alert suppressed (hysteresis): taxonomy=%s, consecutive_breaches < %d",
                    drift_result.taxonomy,
                    self.hysteresis_threshold,
                )
                return None

        # Create active alert
        alert_record = self._create_alert(
            drift_result=drift_result,
            normalized_score=normalized_score,
            alert_level=alert_level,
        )

        logging.info(
            "Alert created: alert_id=%s, taxonomy=%s, level=%s, score=%.2f",
            alert_record.alert_id,
            alert_record.taxonomy,
            alert_record.alert_level,
            alert_record.normalized_score,
        )

        return alert_record

    def acknowledge_alert(
        self,
        taxonomy: str | DriftTaxonomy,
        reason: str = "Manual acknowledgement",
    ) -> int:
        """
        Acknowledge all active alerts for a taxonomy.

        Acknowledged alerts are suppressed for ack_ttl duration (default: 4 hours).

        Args:
            taxonomy: Drift taxonomy to acknowledge
            reason: Acknowledgement reason for audit trail

        Returns:
            Number of alerts acknowledged
        """
        taxonomy_str = taxonomy.value if isinstance(taxonomy, DriftTaxonomy) else taxonomy
        now = datetime.now(timezone.utc)

        with duckdb.connect(str(self.db_path)) as conn:
            # Update active alerts to acknowledged state
            result = conn.execute("""
                UPDATE alerts
                SET state = ?,
                    acknowledged_at = ?,
                    updated_at = ?
                WHERE taxonomy = ?
                  AND state = ?
                RETURNING alert_id
            """, [
                AlertState.ACKNOWLEDGED.value,
                now,
                now,
                taxonomy_str,
                AlertState.ACTIVE.value,
            ]).fetchall()

            count = len(result)

            # Log state transitions
            for (alert_id,) in result:
                conn.execute("""
                    INSERT INTO alert_history (alert_id, from_state, to_state, transition_at, reason)
                    VALUES (?, ?, ?, ?, ?)
                """, [
                    alert_id,
                    AlertState.ACTIVE.value,
                    AlertState.ACKNOWLEDGED.value,
                    now,
                    reason,
                ])

        logging.info(
            "Alerts acknowledged: taxonomy=%s, count=%d, ttl=%s",
            taxonomy_str,
            count,
            self.ack_ttl,
        )

        return count

    def resolve_alert(
        self,
        alert_id: str,
        reason: str = "Drift returned to normal",
    ) -> bool:
        """
        Resolve an active alert (drift returned to GREEN).

        Resolved alerts trigger cooldown period to prevent alert storms.

        Args:
            alert_id: Alert ID to resolve
            reason: Resolution reason for audit trail

        Returns:
            True if alert resolved, False if not found or already resolved
        """
        now = datetime.now(timezone.utc)

        with duckdb.connect(str(self.db_path)) as conn:
            # Update alert to resolved state
            result = conn.execute("""
                UPDATE alerts
                SET state = ?,
                    resolved_at = ?,
                    updated_at = ?
                WHERE alert_id = ?
                  AND state = ?
                RETURNING alert_id, taxonomy
            """, [
                AlertState.RESOLVED.value,
                now,
                now,
                alert_id,
                AlertState.ACTIVE.value,
            ]).fetchone()

            if not result:
                return False

            alert_id_returned, taxonomy = result

            # Log state transition
            conn.execute("""
                INSERT INTO alert_history (alert_id, from_state, to_state, transition_at, reason)
                VALUES (?, ?, ?, ?, ?)
            """, [
                alert_id_returned,
                AlertState.ACTIVE.value,
                AlertState.RESOLVED.value,
                now,
                reason,
            ])

        logging.info(
            "Alert resolved: alert_id=%s, taxonomy=%s, cooldown=%s",
            alert_id_returned,
            taxonomy,
            self.cooldown_period,
        )

        return True

    def get_active_alerts(self, taxonomy: str | DriftTaxonomy | None = None) -> list[AlertRecord]:
        """
        Get all active alerts, optionally filtered by taxonomy.

        Args:
            taxonomy: Optional taxonomy filter

        Returns:
            List of active AlertRecords
        """
        with duckdb.connect(str(self.db_path)) as conn:
            if taxonomy:
                taxonomy_str = taxonomy.value if isinstance(taxonomy, DriftTaxonomy) else taxonomy
                results = conn.execute("""
                    SELECT * FROM alerts
                    WHERE state = ?
                      AND taxonomy = ?
                    ORDER BY created_at DESC
                """, [AlertState.ACTIVE.value, taxonomy_str]).fetchall()
            else:
                results = conn.execute("""
                    SELECT * FROM alerts
                    WHERE state = ?
                    ORDER BY created_at DESC
                """, [AlertState.ACTIVE.value]).fetchall()

            return [self._row_to_alert_record(row) for row in results]

    def _compute_alert_level(self, normalized_score: float) -> AlertLevel:
        """
        Compute alert level from normalized score.

        Thresholds (aligned with drift_detector.py):
        - GREEN: < 5.0 (in-range)
        - YELLOW: 5.0 - 9.9 (warning)
        - RED: >= 10.0 (critical)
        """
        if normalized_score < 5.0:
            return AlertLevel.GREEN
        elif normalized_score < 10.0:
            return AlertLevel.YELLOW
        else:
            return AlertLevel.RED

    def _is_duplicate(self, drift_uid: str) -> bool:
        """
        Check if drift_uid seen within deduplication window.

        Args:
            drift_uid: Drift event UID

        Returns:
            True if duplicate (suppress), False otherwise
        """
        cutoff = datetime.now(timezone.utc) - self.dedup_window

        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute("""
                SELECT COUNT(*) FROM alerts
                WHERE drift_uid = ?
                  AND created_at > ?
            """, [drift_uid, cutoff]).fetchone()

            return result[0] > 0 if result else False

    def _is_acknowledged(self, taxonomy: str) -> bool:
        """
        Check if taxonomy has active acknowledgement within TTL.

        Args:
            taxonomy: Drift taxonomy

        Returns:
            True if acknowledged (suppress), False otherwise
        """
        cutoff = datetime.now(timezone.utc) - self.ack_ttl

        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute("""
                SELECT COUNT(*) FROM alerts
                WHERE taxonomy = ?
                  AND state = ?
                  AND acknowledged_at > ?
            """, [taxonomy, AlertState.ACKNOWLEDGED.value, cutoff]).fetchone()

            return result[0] > 0 if result else False

    def _is_in_cooldown(self, taxonomy: str) -> bool:
        """
        Check if taxonomy in cooldown period after recent resolution.

        Args:
            taxonomy: Drift taxonomy

        Returns:
            True if in cooldown (suppress), False otherwise
        """
        cutoff = datetime.now(timezone.utc) - self.cooldown_period

        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute("""
                SELECT COUNT(*) FROM alerts
                WHERE taxonomy = ?
                  AND state = ?
                  AND resolved_at > ?
            """, [taxonomy, AlertState.RESOLVED.value, cutoff]).fetchone()

            return result[0] > 0 if result else False

    def _check_hysteresis(self, taxonomy: str, normalized_score: float) -> bool:
        """
        Check hysteresis: require consecutive breaches before RED alert.

        Args:
            taxonomy: Drift taxonomy
            normalized_score: Current normalized score

        Returns:
            True if hysteresis threshold met (allow alert), False otherwise (suppress)
        """
        now = datetime.now(timezone.utc)

        with duckdb.connect(str(self.db_path)) as conn:
            # Get current breach counter
            result = conn.execute("""
                SELECT consecutive_breaches, last_breach_at
                FROM breach_counter
                WHERE taxonomy = ?
            """, [taxonomy]).fetchone()

            if result:
                consecutive_breaches, last_breach_at = result
                logging.debug(
                    "Hysteresis check: taxonomy=%s, existing_counter=%d, last_breach=%s",
                    taxonomy,
                    consecutive_breaches,
                    last_breach_at,
                )

                # Ensure last_breach_at is timezone-aware for comparison
                if last_breach_at.tzinfo is None:
                    last_breach_at = last_breach_at.replace(tzinfo=timezone.utc)

                # Check if breach is consecutive (within reasonable time window, e.g., 5 minutes)
                gap = now - last_breach_at
                if gap < timedelta(minutes=5):
                    consecutive_breaches += 1
                    logging.debug(
                        "Hysteresis: consecutive breach (gap=%s), counter=%d",
                        gap,
                        consecutive_breaches,
                    )
                else:
                    # Reset counter if gap too large
                    consecutive_breaches = 1
                    logging.debug(
                        "Hysteresis: gap too large (gap=%s), counter reset to 1",
                        gap,
                    )
            else:
                consecutive_breaches = 1
                logging.debug("Hysteresis: first breach for taxonomy=%s", taxonomy)

            # Update breach counter
            conn.execute("""
                INSERT INTO breach_counter (taxonomy, consecutive_breaches, last_breach_at, last_breach_score)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (taxonomy) DO UPDATE SET
                    consecutive_breaches = EXCLUDED.consecutive_breaches,
                    last_breach_at = EXCLUDED.last_breach_at,
                    last_breach_score = EXCLUDED.last_breach_score
            """, [taxonomy, consecutive_breaches, now, normalized_score])

            # Check if threshold met
            threshold_met = consecutive_breaches >= self.hysteresis_threshold
            logging.debug(
                "Hysteresis result: counter=%d, threshold=%d, allow_alert=%s",
                consecutive_breaches,
                self.hysteresis_threshold,
                threshold_met,
            )
            return threshold_met

    def _reset_hysteresis_counter(self, taxonomy: str | DriftTaxonomy) -> None:
        """
        Reset hysteresis counter for taxonomy on non-RED events.

        This enforces strict consecutiveness: any non-RED observation breaks the
        RED breach chain and requires a fresh sequence to re-trigger escalation.
        """
        taxonomy_str = taxonomy.value if isinstance(taxonomy, DriftTaxonomy) else taxonomy

        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute("""
                SELECT COUNT(*) FROM breach_counter
                WHERE taxonomy = ?
            """, [taxonomy_str]).fetchone()
            has_counter = result[0] > 0 if result else False

            if has_counter:
                conn.execute("""
                    DELETE FROM breach_counter
                    WHERE taxonomy = ?
                """, [taxonomy_str])
                logging.debug("Hysteresis counter reset: taxonomy=%s", taxonomy_str)
            else:
                logging.debug("Hysteresis counter reset no-op: taxonomy=%s", taxonomy_str)

    def _create_alert(
        self,
        drift_result: DriftResult,
        normalized_score: float,
        alert_level: AlertLevel,
    ) -> AlertRecord:
        """
        Create new alert record in database.

        Args:
            drift_result: DriftResult from detector
            normalized_score: Normalized score [0, 10]
            alert_level: Computed alert level

        Returns:
            Created AlertRecord
        """
        now = datetime.now(timezone.utc)
        alert_id = f"{drift_result.uid}_{int(now.timestamp())}"

        alert_record = AlertRecord(
            alert_id=alert_id,
            drift_uid=drift_result.uid,
            taxonomy=drift_result.taxonomy.value,
            drift_score=drift_result.drift_score,
            normalized_score=normalized_score,
            alert_level=alert_level.value,
            state=AlertState.ACTIVE.value,
            created_at=now,
            updated_at=now,
            details=drift_result.details,
        )

        with duckdb.connect(str(self.db_path)) as conn:
            # Supersede prior ACTIVE alerts for same taxonomy before inserting new one.
            superseded_ids = conn.execute("""
                SELECT alert_id
                FROM alerts
                WHERE taxonomy = ?
                  AND state = ?
            """, [alert_record.taxonomy, AlertState.ACTIVE.value]).fetchall()

            if superseded_ids:
                superseded_reason = f"Superseded by alert {alert_record.alert_id}"
                conn.execute("""
                    UPDATE alerts
                    SET state = ?,
                        updated_at = ?,
                        suppression_reason = ?
                    WHERE taxonomy = ?
                      AND state = ?
                """, [
                    AlertState.SUPERSEDED.value,
                    now,
                    superseded_reason,
                    alert_record.taxonomy,
                    AlertState.ACTIVE.value,
                ])

                for (superseded_id,) in superseded_ids:
                    conn.execute("""
                        INSERT INTO alert_history (alert_id, from_state, to_state, transition_at, reason)
                        VALUES (?, ?, ?, ?, ?)
                    """, [
                        superseded_id,
                        AlertState.ACTIVE.value,
                        AlertState.SUPERSEDED.value,
                        now,
                        superseded_reason,
                    ])

            conn.execute("""
                INSERT INTO alerts (
                    alert_id, drift_uid, taxonomy, drift_score, normalized_score,
                    alert_level, state, created_at, updated_at, details
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                alert_record.alert_id,
                alert_record.drift_uid,
                alert_record.taxonomy,
                alert_record.drift_score,
                alert_record.normalized_score,
                alert_record.alert_level,
                alert_record.state,
                alert_record.created_at,
                alert_record.updated_at,
                json.dumps(alert_record.details) if alert_record.details else None,
            ])

            # Log initial state
            conn.execute("""
                INSERT INTO alert_history (alert_id, from_state, to_state, transition_at, reason)
                VALUES (?, ?, ?, ?, ?)
            """, [
                alert_record.alert_id,
                None,
                AlertState.ACTIVE.value,
                now,
                "Alert created",
            ])

        return alert_record

    def _row_to_alert_record(self, row: tuple) -> AlertRecord:
        """Convert database row to AlertRecord."""
        return AlertRecord(
            alert_id=row[0],
            drift_uid=row[1],
            taxonomy=row[2],
            drift_score=row[3],
            normalized_score=row[4],
            alert_level=row[5],
            state=row[6],
            created_at=row[7],
            updated_at=row[8],
            acknowledged_at=row[9],
            resolved_at=row[10],
            suppression_reason=row[11],
            details=json.loads(row[12]) if row[12] else None,
        )


# Module-level convenience function
def create_alert_manager(**kwargs) -> DriftAlertManager:
    """Factory function for creating DriftAlertManager with custom settings."""
    return DriftAlertManager(**kwargs)
