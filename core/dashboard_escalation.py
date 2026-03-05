"""
Dashboard Escalation Initialization

Shared initialization logic for escalation manager in dashboard runtime.
Extracted to ensure tests validate actual production code path.

Phase 33B Slice 4.3: Operational hardening with test fidelity.
"""

from pathlib import Path
from typing import Any

from core.drift_alert_manager import DriftAlertManager
from core.escalation_config import get_escalation_config
from core.escalation_manager import EscalationManager
from core.telemetry_spool import TelemetrySpool


def initialize_escalation_manager(
    alert_manager: DriftAlertManager,
    session_state: dict[str, Any],
    telemetry_path: Path | None = None,
) -> None:
    """
    Initialize escalation manager with singleton lifecycle.

    This function implements the dashboard escalation initialization logic:
    - Singleton pattern (reuse on rerun)
    - Config change detection and restart
    - Graceful stop on disable
    - Session-end cleanup registration

    Args:
        alert_manager: DriftAlertManager instance
        session_state: Streamlit session state dict
        telemetry_path: Optional telemetry spool path (default: data/telemetry/drift_events.jsonl)

    Side effects:
        - Creates/reuses escalation manager in session_state["escalation_manager"]
        - Updates session_state["escalation_enabled"]
        - Updates session_state["escalation_config_hash"]
        - Registers atexit cleanup handler (once per session)
    """
    import atexit

    # Load configuration
    escalation_config = get_escalation_config()

    # Check if escalation state changed (enabled -> disabled or config changed)
    prev_enabled = session_state.get("escalation_enabled", False)
    config_changed = (
        prev_enabled != escalation_config.enabled
        or session_state.get("escalation_config_hash") != hash(
            (
                escalation_config.yellow_ttl_minutes,
                escalation_config.red_ttl_minutes,
                escalation_config.max_escalations,
                escalation_config.cooldown_minutes,
                escalation_config.check_interval,
            )
        )
    )

    # Stop existing manager if disabled or config changed
    if config_changed and "escalation_manager" in session_state:
        old_manager = session_state["escalation_manager"]
        if old_manager is not None:
            old_manager.stop(timeout=2.0)
        del session_state["escalation_manager"]
        session_state["escalation_enabled"] = False

    # Create/reuse escalation manager if enabled
    if escalation_config.enabled:
        if "escalation_manager" not in session_state:
            # Default telemetry path
            if telemetry_path is None:
                telemetry_path = Path("data/telemetry/drift_events.jsonl")

            # Initialize telemetry spool
            telemetry_spool = TelemetrySpool(
                spool_path=telemetry_path,
                max_size_mb=10.0,
                rotation_keep=5,
            )

            # Create and start escalation manager
            escalation_manager = EscalationManager(
                alert_manager=alert_manager,
                yellow_ttl_minutes=escalation_config.yellow_ttl_minutes,
                red_ttl_minutes=escalation_config.red_ttl_minutes,
                max_escalations=escalation_config.max_escalations,
                cooldown_minutes=escalation_config.cooldown_minutes,
                check_interval=escalation_config.check_interval,
                telemetry_spool=telemetry_spool,
                worker_id="dashboard_escalation",
            )
            escalation_manager.start()

            # Store in session state (singleton)
            session_state["escalation_manager"] = escalation_manager
            session_state["escalation_enabled"] = True
            session_state["escalation_config_hash"] = hash(
                (
                    escalation_config.yellow_ttl_minutes,
                    escalation_config.red_ttl_minutes,
                    escalation_config.max_escalations,
                    escalation_config.cooldown_minutes,
                    escalation_config.check_interval,
                )
            )

            # Register cleanup handler for session end
            def _cleanup_escalation_manager():
                """Stop escalation manager on dashboard shutdown."""
                if "escalation_manager" in session_state:
                    manager = session_state["escalation_manager"]
                    if manager is not None:
                        manager.stop(timeout=3.0)

            # Register cleanup only once
            if not session_state.get("escalation_cleanup_registered", False):
                atexit.register(_cleanup_escalation_manager)
                session_state["escalation_cleanup_registered"] = True
