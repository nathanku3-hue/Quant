"""
Phase 33B Slice 3: Escalation Configuration

Environment-based configuration for escalation policy feature flag and parameters.

Usage:
    from core.escalation_config import get_escalation_config

    config = get_escalation_config()
    if config.enabled:
        escalation_manager = EscalationManager(
            alert_manager=alert_manager,
            yellow_ttl_minutes=config.yellow_ttl_minutes,
            red_ttl_minutes=config.red_ttl_minutes,
            max_escalations=config.max_escalations,
            cooldown_minutes=config.cooldown_minutes,
            check_interval=config.check_interval,
            telemetry_spool=telemetry_spool,
        )
        worker = AsyncDriftWorker(
            ...,
            escalation_manager=escalation_manager,
        )
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EscalationConfig:
    """Escalation policy configuration."""
    enabled: bool
    yellow_ttl_minutes: int
    red_ttl_minutes: int
    max_escalations: int
    cooldown_minutes: int
    check_interval: int

    # Future: channel configuration
    enable_webhook: bool = False
    webhook_url: str = ""
    enable_email: bool = False
    email_to: str = ""


def get_escalation_config() -> EscalationConfig:
    """
    Load escalation configuration from environment variables.

    Environment Variables:
        ENABLE_ESCALATION: Master switch (default: False)
        ESCALATION_YELLOW_TTL_MINUTES: YELLOW alert TTL (default: 5)
        ESCALATION_RED_TTL_MINUTES: RED alert TTL (default: 2)
        ESCALATION_MAX_COUNT: Max escalations per alert (default: 3)
        ESCALATION_COOLDOWN_MINUTES: Cooldown between escalations (default: 30)
        ESCALATION_CHECK_INTERVAL: Check interval in seconds (default: 60)

        # Future Slice 4:
        ESCALATION_ENABLE_WEBHOOK: Enable webhook notifications (default: False)
        ESCALATION_WEBHOOK_URL: Webhook URL
        ESCALATION_ENABLE_EMAIL: Enable email notifications (default: False)
        ESCALATION_EMAIL_TO: Email recipient

    Returns:
        EscalationConfig with loaded settings
    """
    return EscalationConfig(
        enabled=os.getenv("ENABLE_ESCALATION", "false").lower() in ("true", "1", "yes"),
        yellow_ttl_minutes=int(os.getenv("ESCALATION_YELLOW_TTL_MINUTES", "5")),
        red_ttl_minutes=int(os.getenv("ESCALATION_RED_TTL_MINUTES", "2")),
        max_escalations=int(os.getenv("ESCALATION_MAX_COUNT", "3")),
        cooldown_minutes=int(os.getenv("ESCALATION_COOLDOWN_MINUTES", "30")),
        check_interval=int(os.getenv("ESCALATION_CHECK_INTERVAL", "60")),
        enable_webhook=os.getenv("ESCALATION_ENABLE_WEBHOOK", "false").lower() in ("true", "1", "yes"),
        webhook_url=os.getenv("ESCALATION_WEBHOOK_URL", ""),
        enable_email=os.getenv("ESCALATION_ENABLE_EMAIL", "false").lower() in ("true", "1", "yes"),
        email_to=os.getenv("ESCALATION_EMAIL_TO", ""),
    )
