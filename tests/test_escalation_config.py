"""
Phase 33B Slice 3: Escalation Config Tests

Tests environment-based configuration loading.
"""

import os
from unittest.mock import patch

import pytest

from core.escalation_config import get_escalation_config


def test_escalation_config_defaults():
    """Test default configuration values."""
    with patch.dict(os.environ, {}, clear=True):
        config = get_escalation_config()

        assert config.enabled is False
        assert config.yellow_ttl_minutes == 5
        assert config.red_ttl_minutes == 2
        assert config.max_escalations == 3
        assert config.cooldown_minutes == 30
        assert config.check_interval == 60
        assert config.enable_webhook is False
        assert config.enable_email is False


def test_escalation_config_enabled():
    """Test enabling escalation via environment."""
    with patch.dict(os.environ, {"ENABLE_ESCALATION": "true"}):
        config = get_escalation_config()
        assert config.enabled is True

    with patch.dict(os.environ, {"ENABLE_ESCALATION": "1"}):
        config = get_escalation_config()
        assert config.enabled is True

    with patch.dict(os.environ, {"ENABLE_ESCALATION": "yes"}):
        config = get_escalation_config()
        assert config.enabled is True

    with patch.dict(os.environ, {"ENABLE_ESCALATION": "false"}):
        config = get_escalation_config()
        assert config.enabled is False


def test_escalation_config_custom_values():
    """Test custom configuration values."""
    with patch.dict(os.environ, {
        "ENABLE_ESCALATION": "true",
        "ESCALATION_YELLOW_TTL_MINUTES": "10",
        "ESCALATION_RED_TTL_MINUTES": "3",
        "ESCALATION_MAX_COUNT": "5",
        "ESCALATION_COOLDOWN_MINUTES": "45",
        "ESCALATION_CHECK_INTERVAL": "30",
    }):
        config = get_escalation_config()

        assert config.enabled is True
        assert config.yellow_ttl_minutes == 10
        assert config.red_ttl_minutes == 3
        assert config.max_escalations == 5
        assert config.cooldown_minutes == 45
        assert config.check_interval == 30


def test_escalation_config_webhook():
    """Test webhook configuration."""
    with patch.dict(os.environ, {
        "ESCALATION_ENABLE_WEBHOOK": "true",
        "ESCALATION_WEBHOOK_URL": "https://example.com/webhook",
    }):
        config = get_escalation_config()

        assert config.enable_webhook is True
        assert config.webhook_url == "https://example.com/webhook"


def test_escalation_config_email():
    """Test email configuration."""
    with patch.dict(os.environ, {
        "ESCALATION_ENABLE_EMAIL": "true",
        "ESCALATION_EMAIL_TO": "alerts@example.com",
    }):
        config = get_escalation_config()

        assert config.enable_email is True
        assert config.email_to == "alerts@example.com"


def test_escalation_config_immutable():
    """Test configuration is immutable."""
    config = get_escalation_config()

    with pytest.raises(AttributeError):
        config.enabled = True  # type: ignore
