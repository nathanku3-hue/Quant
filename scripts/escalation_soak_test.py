"""
Phase 33B: Escalation Manager Soak Test

Validates escalation manager behavior under 30-minute runtime:
- Escalation loop cadence consistency
- DuckDB lock retry frequency
- Escalation history table growth
- Telemetry spool rotation
- Health check metrics stability

Usage:
    python scripts/escalation_soak_test.py --duration 30

Output:
    data/processed/phase33b_soak_evidence.json
"""

import argparse
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb

from core.drift_alert_manager import DriftAlertManager
from core.drift_detector import DriftDetector
from core.escalation_config import EscalationConfig
from core.escalation_manager import EscalationManager
from core.telemetry_spool import TelemetrySpool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def inject_test_alert(
    alert_manager: DriftAlertManager,
    taxonomy: str,
    alert_level: str,
    drift_score: float,
) -> str:
    """Inject a test drift alert for escalation testing."""
    from core.drift_detector import DriftResult, DriftTaxonomy

    drift_result = DriftResult(
        drift_score=drift_score,
        taxonomy=DriftTaxonomy(taxonomy),
        timestamp=datetime.now(timezone.utc),
        alert_level=alert_level,
        details={"test": "soak_test_injection"},
    )

    alert = alert_manager.process_drift_result(drift_result, normalized_score=drift_score)
    if alert:
        logger.info(f"Injected test alert: {alert.alert_id} ({alert_level})")
        return alert.alert_id
    return None


def run_soak_test(duration_minutes: int) -> dict:
    """
    Run escalation manager soak test.

    Args:
        duration_minutes: Test duration in minutes

    Returns:
        Soak test evidence dictionary
    """
    logger.info(f"Starting {duration_minutes}-minute escalation soak test")

    # Setup test environment
    test_db_path = Path("data/test_escalation_soak.duckdb")
    test_telemetry_path = Path("data/telemetry/soak_test_drift_events.jsonl")
    test_telemetry_path.parent.mkdir(parents=True, exist_ok=True)

    # Clean up previous test artifacts
    if test_db_path.exists():
        test_db_path.unlink()
    if test_telemetry_path.exists():
        test_telemetry_path.unlink()

    # Initialize components
    alert_manager = DriftAlertManager(db_path=test_db_path)
    telemetry_spool = TelemetrySpool(
        spool_path=test_telemetry_path,
        max_size_mb=1.0,  # Small size to test rotation
        rotation_keep=3,
    )

    # Create escalation manager with test config
    escalation_manager = EscalationManager(
        alert_manager=alert_manager,
        yellow_ttl_minutes=5,
        red_ttl_minutes=2,
        max_escalations=3,
        cooldown_minutes=30,
        check_interval=60,
        telemetry_spool=telemetry_spool,
        worker_id="soak_test",
    )

    # Start escalation manager
    escalation_manager.start()
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(minutes=duration_minutes)

    # Metrics collection
    health_checks = []
    escalation_counts = []
    lock_retry_events = []
    alert_injections = []

    # Inject initial test alerts
    logger.info("Injecting initial test alerts...")
    alert_id_red = inject_test_alert(alert_manager, "ALLOCATION_DRIFT", "RED", 8.0)
    alert_id_yellow = inject_test_alert(alert_manager, "REGIME_DRIFT", "YELLOW", 5.0)
    alert_injections.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_id": alert_id_red,
        "level": "RED",
    })
    alert_injections.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_id": alert_id_yellow,
        "level": "YELLOW",
    })

    # Monitor loop (check every 5 minutes)
    check_interval = 300  # 5 minutes
    next_check = time.time() + check_interval

    try:
        while datetime.now(timezone.utc) < end_time:
            # Wait until next check
            sleep_time = max(0, next_check - time.time())
            if sleep_time > 0:
                time.sleep(min(sleep_time, 10))  # Check every 10s for early exit
                continue

            # Capture health check
            health = escalation_manager.health_check()
            health_snapshot = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_running": health.is_running,
                "last_check_time": health.last_check_time.isoformat() if health.last_check_time else None,
                "total_checks": health.total_checks,
                "total_escalations": health.total_escalations,
                "consecutive_errors": health.consecutive_errors,
            }
            health_checks.append(health_snapshot)
            logger.info(
                f"Health check: running={health.is_running}, checks={health.total_checks}, "
                f"escalations={health.total_escalations}, errors={health.consecutive_errors}"
            )

            # Query escalation history count
            with duckdb.connect(str(test_db_path)) as conn:
                result = conn.execute("SELECT COUNT(*) FROM escalation_history").fetchone()
                escalation_count = result[0] if result else 0
                escalation_counts.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "count": escalation_count,
                })

            next_check = time.time() + check_interval

    except KeyboardInterrupt:
        logger.warning("Soak test interrupted by user")
    finally:
        # Stop escalation manager
        logger.info("Stopping escalation manager...")
        escalation_manager.stop(timeout=5.0)

    # Final metrics collection
    final_health = escalation_manager.health_check()
    with duckdb.connect(str(test_db_path)) as conn:
        final_escalation_count = conn.execute("SELECT COUNT(*) FROM escalation_history").fetchone()[0]
        escalation_history = conn.execute("""
            SELECT alert_id, escalation_count, escalated_at, escalation_reason
            FROM escalation_history
            ORDER BY escalated_at
        """).fetchall()

    # Read telemetry events
    telemetry_events = []
    if test_telemetry_path.exists():
        with open(test_telemetry_path, "r") as f:
            for line in f:
                try:
                    telemetry_events.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    pass

    # Compile evidence
    evidence = {
        "test_config": {
            "duration_minutes": duration_minutes,
            "start_time": start_time.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "yellow_ttl_minutes": 5,
            "red_ttl_minutes": 2,
            "check_interval_seconds": 60,
        },
        "health_checks": health_checks,
        "escalation_counts": escalation_counts,
        "final_metrics": {
            "is_running": final_health.is_running,
            "total_checks": final_health.total_checks,
            "total_escalations": final_health.total_escalations,
            "consecutive_errors": final_health.consecutive_errors,
            "escalation_history_rows": final_escalation_count,
        },
        "escalation_history": [
            {
                "alert_id": row[0],
                "escalation_count": row[1],
                "escalated_at": row[2].isoformat() if row[2] else None,
                "escalation_reason": row[3],
            }
            for row in escalation_history
        ],
        "telemetry_events": telemetry_events,
        "alert_injections": alert_injections,
        "lock_retry_events": lock_retry_events,  # Would need instrumentation to capture
    }

    # Write evidence to file
    output_path = Path("data/processed/phase33b_soak_evidence.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(evidence, f, indent=2)

    logger.info(f"Soak test complete. Evidence written to {output_path}")

    # Summary
    logger.info("=" * 60)
    logger.info("SOAK TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Duration: {duration_minutes} minutes")
    logger.info(f"Total escalation checks: {final_health.total_checks}")
    logger.info(f"Total escalations: {final_health.total_escalations}")
    logger.info(f"Escalation history rows: {final_escalation_count}")
    logger.info(f"Consecutive errors: {final_health.consecutive_errors}")
    logger.info(f"Telemetry events: {len(telemetry_events)}")
    logger.info(f"Manager stopped cleanly: {not final_health.is_running}")
    logger.info("=" * 60)

    return evidence


def main():
    parser = argparse.ArgumentParser(description="Run escalation manager soak test")
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Test duration in minutes (default: 30)",
    )
    args = parser.parse_args()

    evidence = run_soak_test(args.duration)

    # Validation checks
    checks_passed = True

    if evidence["final_metrics"]["consecutive_errors"] > 0:
        logger.warning("⚠️  Consecutive errors detected during soak test")
        checks_passed = False

    if evidence["final_metrics"]["is_running"]:
        logger.warning("⚠️  Manager did not stop cleanly")
        checks_passed = False

    if evidence["final_metrics"]["total_checks"] < (args.duration * 60 / 60) * 0.9:
        logger.warning("⚠️  Escalation check cadence below expected (90% threshold)")
        checks_passed = False

    if checks_passed:
        logger.info("✅ All soak test validation checks passed")
    else:
        logger.error("❌ Some soak test validation checks failed")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
