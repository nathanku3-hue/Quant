from __future__ import annotations

import os
from datetime import datetime
from datetime import timezone
from typing import Any
from urllib.parse import parse_qsl
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse

_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_SECRET_QUERY_KEYS = {
    "apikey",
    "api_key",
    "token",
    "access_token",
    "password",
    "secret",
    "key",
    "signature",
}

ALLOWED_EGRESS_HOSTS_ENV = "TZ_ALLOWED_EGRESS_HOST_SUFFIXES"
ALLOWED_EGRESS_HOSTS_MODE_ENV = "TZ_ALLOWED_EGRESS_HOST_SUFFIXES_MODE"
ALLOWED_EGRESS_HOSTS_MODE_OVERRIDE = "override"
DEFAULT_ALLOWED_EGRESS_HOST_SUFFIXES = (
    "alpaca.markets",
    "wrds-pgdata.wharton.upenn.edu",
    "financialmodelingprep.com",
)
ALLOW_HTTP_LOCALHOST_ENV = "TZ_ALLOW_HTTP_EGRESS_LOCALHOST"

HMAC_KEY_VERSION_ENV = "TZ_HMAC_KEY_VERSION"
HMAC_KEY_ACTIVATED_AT_ENV = "TZ_HMAC_KEY_ACTIVATED_AT_UTC"
HMAC_KEY_LEGAL_HOLD_ENV = "TZ_HMAC_KEY_LEGAL_HOLD"
HMAC_ROTATION_DAYS_ENV = "TZ_HMAC_ROTATION_DAYS"
HMAC_MAX_FUTURE_SKEW_SECONDS_ENV = "TZ_HMAC_MAX_FUTURE_SKEW_SECONDS"


def env_flag(name: str, *, default: bool = False) -> bool:
    raw = str(os.environ.get(name, "")).strip()
    if raw == "":
        return bool(default)
    return raw.lower() in _TRUE_VALUES


def get_required_env(name: str) -> str:
    value = str(os.environ.get(name, "")).strip()
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value


def get_allowed_egress_host_suffixes() -> tuple[str, ...]:
    raw = str(os.environ.get(ALLOWED_EGRESS_HOSTS_ENV, "")).strip()
    if raw == "":
        return DEFAULT_ALLOWED_EGRESS_HOST_SUFFIXES
    parts = tuple(x.strip().lower() for x in raw.split(",") if x.strip())
    if not parts:
        return DEFAULT_ALLOWED_EGRESS_HOST_SUFFIXES
    mode = str(os.environ.get(ALLOWED_EGRESS_HOSTS_MODE_ENV, "")).strip().lower()
    if mode == ALLOWED_EGRESS_HOSTS_MODE_OVERRIDE:
        return parts
    merged = list(DEFAULT_ALLOWED_EGRESS_HOST_SUFFIXES)
    for suffix in parts:
        if suffix not in merged:
            merged.append(suffix)
    return tuple(merged)


def _host_matches_suffix(host: str, suffix: str) -> bool:
    host_l = host.lower().strip().rstrip(".")
    suffix_l = suffix.lower().strip().lstrip(".").rstrip(".")
    return host_l == suffix_l or host_l.endswith("." + suffix_l)


def is_host_allowed(host: str) -> bool:
    host_s = str(host).strip().lower().rstrip(".")
    if not host_s:
        return False
    suffixes = get_allowed_egress_host_suffixes()
    return any(_host_matches_suffix(host_s, suffix) for suffix in suffixes)


def assert_egress_host_allowed(host: str, *, context: str) -> None:
    host_s = str(host).strip()
    if not is_host_allowed(host_s):
        raise PermissionError(
            f"Deny-by-default egress policy blocked host '{host_s}' for {context}. "
            f"Allowed suffixes: {get_allowed_egress_host_suffixes()}"
        )


def assert_egress_url_allowed(url: str, *, context: str) -> None:
    parsed = urlparse(str(url).strip())
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").strip().lower()
    local_http_allowed = False
    if scheme != "https":
        allow_http_localhost = env_flag(ALLOW_HTTP_LOCALHOST_ENV, default=False)
        local_http_allowed = (
            scheme == "http"
            and allow_http_localhost
            and host in {"localhost", "127.0.0.1", "::1"}
        )
        if not local_http_allowed:
            raise PermissionError(
                f"Deny-by-default egress policy blocked non-https URL for {context}: {url}"
            )
    if local_http_allowed:
        return
    assert_egress_host_allowed(host, context=context)


def redact_url_secrets(url: str) -> str:
    parsed = urlparse(str(url).strip())
    if parsed.query == "":
        return urlunparse(parsed)
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    clean_pairs = [(k, v) for (k, v) in pairs if k.lower() not in _SECRET_QUERY_KEYS]
    clean_query = urlencode(clean_pairs, doseq=True)
    return urlunparse(parsed._replace(query=clean_query))


def _parse_rotation_anchor(raw: str) -> datetime:
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def get_hmac_rotation_status(now_utc: datetime | None = None) -> dict[str, Any]:
    now_val = now_utc.astimezone(timezone.utc) if isinstance(now_utc, datetime) else datetime.now(timezone.utc)
    key_version = get_required_env(HMAC_KEY_VERSION_ENV)
    activated_raw = get_required_env(HMAC_KEY_ACTIVATED_AT_ENV)
    activated_at = _parse_rotation_anchor(activated_raw)
    legal_hold = env_flag(HMAC_KEY_LEGAL_HOLD_ENV, default=False)
    rotation_days = max(1, int(str(os.environ.get(HMAC_ROTATION_DAYS_ENV, "1")).strip() or "1"))
    max_future_skew_seconds = max(
        0,
        int(str(os.environ.get(HMAC_MAX_FUTURE_SKEW_SECONDS_ENV, "300")).strip() or "300"),
    )
    age_seconds = (now_val - activated_at).total_seconds()
    if age_seconds < -float(max_future_skew_seconds):
        raise EnvironmentError(
            "HMAC activation timestamp is in the future beyond allowed skew. "
            f"activated_at={activated_at.isoformat().replace('+00:00', 'Z')} "
            f"now={now_val.isoformat().replace('+00:00', 'Z')} "
            f"max_future_skew_seconds={max_future_skew_seconds}"
        )
    age_days = max(0.0, age_seconds / 86400.0)
    rotation_due = (age_days >= float(rotation_days)) and (not legal_hold)
    return {
        "hmac_key_version": key_version,
        "hmac_key_activated_at_utc": activated_at.isoformat().replace("+00:00", "Z"),
        "hmac_legal_hold": bool(legal_hold),
        "hmac_rotation_days": int(rotation_days),
        "hmac_key_age_days": float(age_days),
        "hmac_rotation_due": bool(rotation_due),
    }


def require_hmac_rotation_compliance(now_utc: datetime | None = None) -> dict[str, Any]:
    status = get_hmac_rotation_status(now_utc=now_utc)
    if status["hmac_rotation_due"]:
        raise EnvironmentError(
            "HMAC signing key rotation overdue. "
            f"Active key_version={status['hmac_key_version']} age_days={status['hmac_key_age_days']:.2f} "
            f"rotation_days={status['hmac_rotation_days']} "
            f"(set {HMAC_KEY_LEGAL_HOLD_ENV}=YES for legal-hold exception)."
        )
    return status
