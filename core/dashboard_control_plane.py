from __future__ import annotations

import datetime as dt
import json
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_WATCHLIST_FILE = "./data/watchlist.json"
DEFAULT_WATCHLIST = {"defaults": ["AAPL", "MSFT", "SPY"], "user_added": []}
PLAN_STATUS_READY = "ready"
PLAN_STATUS_INVALID_STATE = "invalid_state"
INVALID_STATE_DATE_KEY = "INVALID_STATE"
DATA_HEALTH_HEALTHY = "HEALTHY"
DATA_HEALTH_DEGRADED = "DEGRADED"


def load_watchlist(watchlist_file: str = DEFAULT_WATCHLIST_FILE) -> dict[str, list[str]]:
    if os.path.exists(watchlist_file):
        try:
            with open(watchlist_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                defaults = data.get("defaults", [])
                user_added = data.get("user_added", [])
                if isinstance(defaults, list) and isinstance(user_added, list):
                    return {
                        "defaults": [str(x) for x in defaults],
                        "user_added": [str(x) for x in user_added],
                    }
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "defaults": list(DEFAULT_WATCHLIST["defaults"]),
        "user_added": list(DEFAULT_WATCHLIST["user_added"]),
    }


def get_watchlist_tickers(watchlist_file: str = DEFAULT_WATCHLIST_FILE) -> list[str]:
    data = load_watchlist(watchlist_file)
    return sorted(set(data.get("defaults", []) + data.get("user_added", [])))


def save_user_selections(
    selected_ticker_names: list[str],
    watchlist_file: str = DEFAULT_WATCHLIST_FILE,
) -> None:
    data = load_watchlist(watchlist_file)
    defaults = set(data.get("defaults", []))
    new_user = sorted(set(selected_ticker_names) - defaults)
    data["user_added"] = new_user

    target = Path(watchlist_file)
    target.parent.mkdir(parents=True, exist_ok=True)

    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(target.parent),
            delete=False,
        ) as tmp:
            tmp_path = Path(tmp.name)
            json.dump(data, tmp, indent=4)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(str(tmp_path), str(target))
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def is_data_stale(last_date_pd: Any, *, today: dt.date | None = None) -> bool:
    now = today or dt.date.today()
    last, reason = _coerce_calendar_date(last_date_pd)
    if reason is not None or last is None:
        raise ValueError(f"invalid last_date_pd ({reason or 'unknown_reason'})")
    if last > now:
        raise ValueError("invalid last_date_pd (future_date)")
    _threshold_days, cutoff = _compute_tn_staleness_cutoff(now)
    return bool(last < cutoff)


@dataclass(frozen=True)
class AutoUpdatePlan:
    update_attempted: bool
    update_attempted_for_date: str
    is_stale: bool
    should_attempt_update: bool
    show_already_attempted_caption: bool
    status: str
    is_invalid_state: bool
    reason: str
    message: str
    stale_threshold_label: str
    stale_cutoff_date: str


def _compute_tn_staleness_cutoff(today: dt.date) -> tuple[int, dt.date]:
    weekday = int(today.weekday())
    if weekday == 6:
        threshold_days = 2
    elif weekday == 0:
        threshold_days = 3
    else:
        threshold_days = 1
    return threshold_days, today - dt.timedelta(days=threshold_days)


def _coerce_calendar_date(value: Any) -> tuple[dt.date | None, str | None]:
    candidate = value.date() if hasattr(value, "date") else value
    if isinstance(candidate, dt.datetime):
        candidate = candidate.date()
    if candidate is None:
        return None, "null"

    text = str(candidate).strip()
    lowered = text.lower()
    if lowered in {"none", "null", "nan", "nat"}:
        return None, "null_like"
    if isinstance(candidate, dt.date):
        return candidate, None
    if not text:
        return None, "empty"

    normalized = text
    if "T" in normalized:
        normalized = normalized.split("T", 1)[0]
    if " " in normalized:
        normalized = normalized.split(" ", 1)[0]

    try:
        parsed = dt.date.fromisoformat(normalized)
    except ValueError:
        return None, "invalid_format"
    return parsed, None


def plan_auto_update(
    *,
    last_db_date: Any,
    update_attempted: bool,
    update_attempted_for_date: str | None,
    today: dt.date | None = None,
) -> AutoUpdatePlan:
    now = today or dt.date.today()
    threshold_days, cutoff = _compute_tn_staleness_cutoff(now)
    threshold_label = f"T-{threshold_days}"
    cutoff_key = cutoff.isoformat()

    last_date, invalid_reason = _coerce_calendar_date(last_db_date)
    if invalid_reason is not None or last_date is None:
        reason = f"invalid_last_db_date:{invalid_reason or 'unknown'}"
        message = (
            "Auto-update planner INVALID STATE: last_db_date is missing or malformed. "
            f"Expected ISO date <= {now.isoformat()} for threshold {threshold_label} (cutoff {cutoff_key})."
        )
        return AutoUpdatePlan(
            update_attempted=False,
            update_attempted_for_date=INVALID_STATE_DATE_KEY,
            is_stale=False,
            should_attempt_update=False,
            show_already_attempted_caption=False,
            status=PLAN_STATUS_INVALID_STATE,
            is_invalid_state=True,
            reason=reason,
            message=message,
            stale_threshold_label=threshold_label,
            stale_cutoff_date=cutoff_key,
        )

    if last_date > now:
        reason = "invalid_last_db_date:future_date"
        message = (
            "Auto-update planner INVALID STATE: last_db_date is in the future. "
            f"Received {last_date.isoformat()}, today is {now.isoformat()}."
        )
        return AutoUpdatePlan(
            update_attempted=False,
            update_attempted_for_date=INVALID_STATE_DATE_KEY,
            is_stale=False,
            should_attempt_update=False,
            show_already_attempted_caption=False,
            status=PLAN_STATUS_INVALID_STATE,
            is_invalid_state=True,
            reason=reason,
            message=message,
            stale_threshold_label=threshold_label,
            stale_cutoff_date=cutoff_key,
        )

    last_key = last_date.isoformat()
    attempted = bool(update_attempted and update_attempted_for_date == last_key)
    stale = bool(last_date < cutoff)
    should_attempt = bool(stale and (not attempted))
    show_caption = bool(stale and attempted)

    if stale:
        if attempted:
            reason = "stale_threshold_exceeded:already_attempted"
            message = (
                f"Data date {last_key} is older than {threshold_label} cutoff {cutoff_key}; "
                "auto-update already attempted for this date."
            )
        else:
            reason = "stale_threshold_exceeded:update_required"
            message = (
                f"Data date {last_key} is older than {threshold_label} cutoff {cutoff_key}; "
                "auto-update should run."
            )
    else:
        reason = "fresh_within_threshold"
        message = (
            f"Data date {last_key} satisfies {threshold_label} cutoff {cutoff_key}; "
            "no auto-update required."
        )

    return AutoUpdatePlan(
        update_attempted=attempted,
        update_attempted_for_date=last_key,
        is_stale=stale,
        should_attempt_update=should_attempt,
        show_already_attempted_caption=show_caption,
        status=PLAN_STATUS_READY,
        is_invalid_state=False,
        reason=reason,
        message=message,
        stale_threshold_label=threshold_label,
        stale_cutoff_date=cutoff_key,
    )


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def coerce_proxy_numeric(value: Any, *, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(parsed):
        return float(default)
    return float(parsed)


def derive_hf_proxy_data_health(proxy_data: Any) -> dict[str, Any]:
    signals: list[dict[str, Any]] = []

    if not isinstance(proxy_data, dict):
        signals.append(
            {
                "signal": "__payload__",
                "status": DATA_HEALTH_DEGRADED,
                "reason": "invalid proxy payload",
                "value": None,
                "span": "",
            }
        )
    elif len(proxy_data) == 0:
        signals.append(
            {
                "signal": "__payload__",
                "status": DATA_HEALTH_DEGRADED,
                "reason": "no signals",
                "value": None,
                "span": "",
            }
        )
    else:
        for signal_name in sorted(proxy_data.keys()):
            raw_value = proxy_data.get(signal_name)
            signal_value = raw_value
            signal_span = ""
            status = DATA_HEALTH_HEALTHY
            reason = ""

            if isinstance(raw_value, dict):
                signal_value = raw_value.get("val")
                raw_span = raw_value.get("span")
                signal_span = "" if raw_span is None else str(raw_span)

            if signal_value is None:
                status = DATA_HEALTH_DEGRADED
                reason = "missing value"
            elif not _is_finite_number(signal_value):
                if isinstance(signal_value, (int, float)):
                    reason = "non-finite value"
                else:
                    reason = "non-numeric value"
                status = DATA_HEALTH_DEGRADED

            signals.append(
                {
                    "signal": str(signal_name),
                    "status": status,
                    "reason": reason,
                    "value": float(signal_value) if _is_finite_number(signal_value) else None,
                    "span": signal_span,
                }
            )

    total_signals = len(signals)
    degraded_count = sum(1 for x in signals if x["status"] == DATA_HEALTH_DEGRADED)
    degraded_ratio = (degraded_count / total_signals) if total_signals > 0 else 1.0
    status = DATA_HEALTH_DEGRADED if degraded_count > 0 else DATA_HEALTH_HEALTHY

    return {
        "status": status,
        "degraded_ratio": degraded_ratio,
        "degraded_count": degraded_count,
        "total_signals": total_signals,
        "signals": signals,
    }


def ensure_payload_data_health(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return derive_hf_proxy_data_health({})

    cached_data_health = payload.get("data_health")
    if isinstance(cached_data_health, dict):
        cached_status = str(cached_data_health.get("status", "")).upper()
        cached_signals = cached_data_health.get("signals")
        if cached_status in (DATA_HEALTH_HEALTHY, DATA_HEALTH_DEGRADED) and isinstance(cached_signals, list):
            return cached_data_health

    derived = derive_hf_proxy_data_health(payload.get("proxy", {}))
    payload["data_health"] = derived
    return derived
