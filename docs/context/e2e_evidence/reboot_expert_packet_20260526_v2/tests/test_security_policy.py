from __future__ import annotations

from datetime import datetime
from datetime import timezone

import pytest

from core.security_policy import assert_egress_url_allowed
from core.security_policy import get_allowed_egress_host_suffixes
from core.security_policy import redact_url_secrets
from core.security_policy import require_hmac_rotation_compliance


def test_redact_url_secrets_removes_api_key_query_param():
    raw = "https://financialmodelingprep.com/stable/analyst-estimates?symbol=NVDA&period=annual&apikey=SECRET123"
    clean = redact_url_secrets(raw)
    assert "SECRET123" not in clean
    assert "apikey=" not in clean
    assert clean.endswith("symbol=NVDA&period=annual")


def test_assert_egress_url_allowed_blocks_unlisted_host():
    with pytest.raises(PermissionError, match="Deny-by-default egress policy blocked host"):
        assert_egress_url_allowed("https://example.com/api", context="unit_test")


def test_assert_egress_url_allowed_blocks_http_even_for_allowlisted_host():
    with pytest.raises(PermissionError, match="non-https URL"):
        assert_egress_url_allowed("http://api.alpaca.markets/v2/account", context="unit_test")


def test_assert_egress_url_allowed_allows_http_localhost_with_break_glass(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TZ_ALLOW_HTTP_EGRESS_LOCALHOST", "YES")
    assert_egress_url_allowed("http://127.0.0.1:8000/health", context="unit_test")


def test_get_allowed_egress_host_suffixes_extends_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TZ_ALLOWED_EGRESS_HOST_SUFFIXES", "discord.com")
    monkeypatch.delenv("TZ_ALLOWED_EGRESS_HOST_SUFFIXES_MODE", raising=False)
    suffixes = get_allowed_egress_host_suffixes()
    assert "alpaca.markets" in suffixes
    assert "discord.com" in suffixes


def test_get_allowed_egress_host_suffixes_override_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TZ_ALLOWED_EGRESS_HOST_SUFFIXES", "discord.com")
    monkeypatch.setenv("TZ_ALLOWED_EGRESS_HOST_SUFFIXES_MODE", "override")
    suffixes = get_allowed_egress_host_suffixes()
    assert suffixes == ("discord.com",)


def test_require_hmac_rotation_compliance_allows_legal_hold(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TZ_HMAC_KEY_VERSION", "hmac-v2")
    monkeypatch.setenv("TZ_HMAC_KEY_ACTIVATED_AT_UTC", "2026-01-01T00:00:00Z")
    monkeypatch.setenv("TZ_HMAC_ROTATION_DAYS", "1")
    monkeypatch.setenv("TZ_HMAC_KEY_LEGAL_HOLD", "YES")
    status = require_hmac_rotation_compliance(now_utc=datetime(2026, 3, 1, tzinfo=timezone.utc))
    assert status["hmac_key_version"] == "hmac-v2"
    assert status["hmac_legal_hold"] is True
    assert status["hmac_rotation_due"] is False


def test_require_hmac_rotation_compliance_blocks_overdue_without_legal_hold(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("TZ_HMAC_KEY_VERSION", "hmac-v3")
    monkeypatch.setenv("TZ_HMAC_KEY_ACTIVATED_AT_UTC", "2026-01-01T00:00:00Z")
    monkeypatch.setenv("TZ_HMAC_ROTATION_DAYS", "1")
    monkeypatch.delenv("TZ_HMAC_KEY_LEGAL_HOLD", raising=False)
    with pytest.raises(EnvironmentError, match="HMAC signing key rotation overdue"):
        require_hmac_rotation_compliance(now_utc=datetime(2026, 3, 1, tzinfo=timezone.utc))


def test_require_hmac_rotation_compliance_blocks_future_activation_beyond_skew(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("TZ_HMAC_KEY_VERSION", "hmac-v4")
    monkeypatch.setenv("TZ_HMAC_KEY_ACTIVATED_AT_UTC", "2026-03-03T00:00:00Z")
    monkeypatch.setenv("TZ_HMAC_ROTATION_DAYS", "1")
    monkeypatch.setenv("TZ_HMAC_MAX_FUTURE_SKEW_SECONDS", "60")
    monkeypatch.delenv("TZ_HMAC_KEY_LEGAL_HOLD", raising=False)
    with pytest.raises(EnvironmentError, match="future beyond allowed skew"):
        require_hmac_rotation_compliance(now_utc=datetime(2026, 3, 1, tzinfo=timezone.utc))
