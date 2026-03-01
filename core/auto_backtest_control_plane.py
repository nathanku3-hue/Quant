from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import time
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Mapping


DEFAULT_CACHE_PATH = "./data/auto_backtest_cache.json"
CACHE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AutoBacktestConfig:
    ma_lookback: int
    stop_lookback: int
    atr_period: int
    vol_target: float
    max_positions: int
    cost_bps: float
    min_price: float


DEFAULT_CONFIG = AutoBacktestConfig(
    ma_lookback=200,
    stop_lookback=22,
    atr_period=20,
    vol_target=0.15,
    max_positions=50,
    cost_bps=10 / 10_000,
    min_price=5.0,
)


@dataclass(frozen=True)
class AutoBacktestCacheState:
    config: AutoBacktestConfig
    config_fingerprint: str
    last_run_key: str | None
    run_attempted: bool
    run_attempted_for_key: str | None
    status: str
    last_started_at: str | None
    last_finished_at: str | None


@dataclass(frozen=True)
class AutoBacktestCacheLoadResult:
    ok: bool
    reason: str | None
    state: AutoBacktestCacheState | None


@dataclass(frozen=True)
class AutoBacktestPlan:
    run_key: str
    config_fingerprint: str
    is_stale: bool
    run_attempted: bool
    run_attempted_for_key: str
    should_run: bool
    show_already_attempted_caption: bool


def _default_state() -> AutoBacktestCacheState:
    fingerprint = compute_config_fingerprint(DEFAULT_CONFIG)
    return AutoBacktestCacheState(
        config=DEFAULT_CONFIG,
        config_fingerprint=fingerprint,
        last_run_key=None,
        run_attempted=False,
        run_attempted_for_key=None,
        status="idle",
        last_started_at=None,
        last_finished_at=None,
    )


def create_default_state() -> AutoBacktestCacheState:
    return _default_state()


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _clamp_int(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, int(value)))


def _clamp_float(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def _coerce_config_payload(payload: AutoBacktestConfig | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(payload, AutoBacktestConfig):
        return asdict(payload)
    if isinstance(payload, Mapping):
        return payload
    return {}


def _serialize_config(config: AutoBacktestConfig) -> dict[str, Any]:
    return {
        "ma_lookback": int(config.ma_lookback),
        "stop_lookback": int(config.stop_lookback),
        "atr_period": int(config.atr_period),
        "vol_target": round(float(config.vol_target), 4),
        "max_positions": int(config.max_positions),
        "cost_bps": round(float(config.cost_bps), 8),
        "min_price": round(float(config.min_price), 4),
    }


def _serialize_state(state: AutoBacktestCacheState) -> dict[str, Any]:
    return {
        "version": CACHE_SCHEMA_VERSION,
        "config": _serialize_config(state.config),
        "config_fingerprint": state.config_fingerprint,
        "last_run_key": state.last_run_key,
        "run_attempted": bool(state.run_attempted),
        "run_attempted_for_key": state.run_attempted_for_key,
        "status": state.status,
        "last_started_at": state.last_started_at,
        "last_finished_at": state.last_finished_at,
    }


def _parse_state(payload: Any) -> AutoBacktestCacheState | None:
    if not isinstance(payload, Mapping):
        return None

    version = payload.get("version")
    if not isinstance(version, int) or int(version) != CACHE_SCHEMA_VERSION:
        return None

    config_payload = payload.get("config")
    if not isinstance(config_payload, Mapping):
        return None

    config = normalize_config(config_payload)
    computed_fp = compute_config_fingerprint(config)
    payload_fp = payload.get("config_fingerprint")
    if not isinstance(payload_fp, str) or payload_fp != computed_fp:
        return None

    last_run_key = payload.get("last_run_key")
    if last_run_key is not None and not isinstance(last_run_key, str):
        return None

    run_attempted_for_key = payload.get("run_attempted_for_key")
    if run_attempted_for_key is not None and not isinstance(run_attempted_for_key, str):
        return None

    run_attempted_raw = payload.get("run_attempted", False)
    if not isinstance(run_attempted_raw, bool):
        return None

    status = payload.get("status", "idle")
    if status not in {"idle", "running", "finished", "failed"}:
        return None

    last_started_at = payload.get("last_started_at")
    if last_started_at is not None and not isinstance(last_started_at, str):
        return None

    last_finished_at = payload.get("last_finished_at")
    if last_finished_at is not None and not isinstance(last_finished_at, str):
        return None

    return AutoBacktestCacheState(
        config=config,
        config_fingerprint=computed_fp,
        last_run_key=last_run_key,
        run_attempted=run_attempted_raw,
        run_attempted_for_key=run_attempted_for_key,
        status=status,
        last_started_at=last_started_at,
        last_finished_at=last_finished_at,
    )


def _normalize_date_key(latest_prices_date: Any) -> str:
    if latest_prices_date is None:
        return "unknown"
    value = latest_prices_date.date() if hasattr(latest_prices_date, "date") else latest_prices_date
    if isinstance(value, (dt.date, dt.datetime)):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    return text or "unknown"


def _utc_timestamp(now: dt.datetime | None = None) -> str:
    ts = now or dt.datetime.now(dt.timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt.timezone.utc)
    else:
        ts = ts.astimezone(dt.timezone.utc)
    return ts.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_config(payload: AutoBacktestConfig | Mapping[str, Any]) -> AutoBacktestConfig:
    data = _coerce_config_payload(payload)

    ma_raw = _safe_int(data.get("ma_lookback"), DEFAULT_CONFIG.ma_lookback)
    ma_lookback = _clamp_int(int(round(ma_raw / 10.0) * 10), 50, 300)

    stop_lookback = _clamp_int(
        _safe_int(data.get("stop_lookback"), DEFAULT_CONFIG.stop_lookback),
        10,
        60,
    )
    atr_period = _clamp_int(
        _safe_int(data.get("atr_period"), DEFAULT_CONFIG.atr_period),
        10,
        40,
    )

    vol_target_raw = _safe_float(data.get("vol_target"), DEFAULT_CONFIG.vol_target)
    if vol_target_raw > 1.0:
        vol_target_raw = vol_target_raw / 100.0
    vol_target = _clamp_float(vol_target_raw, 0.05, 0.30)
    vol_target = round(round(vol_target * 100.0) / 100.0, 4)

    max_positions = _clamp_int(
        _safe_int(data.get("max_positions"), DEFAULT_CONFIG.max_positions),
        10,
        100,
    )

    cost_bps_raw = _safe_float(data.get("cost_bps"), DEFAULT_CONFIG.cost_bps)
    cost_unit = str(data.get("cost_bps_unit", "rate")).strip().lower()
    if cost_unit == "bps":
        cost_bps_raw = cost_bps_raw / 10_000.0
    cost_bps = round(max(0.0, cost_bps_raw), 8)

    min_price = round(max(1.0, _safe_float(data.get("min_price"), DEFAULT_CONFIG.min_price)), 4)

    return AutoBacktestConfig(
        ma_lookback=ma_lookback,
        stop_lookback=stop_lookback,
        atr_period=atr_period,
        vol_target=vol_target,
        max_positions=max_positions,
        cost_bps=cost_bps,
        min_price=min_price,
    )


def compute_config_fingerprint(config: AutoBacktestConfig) -> str:
    payload = _serialize_config(config)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def compute_run_key(latest_prices_date: Any, config_fingerprint: str) -> str:
    return f"{_normalize_date_key(latest_prices_date)}:{config_fingerprint}"


def load_cache(path: str, error_policy: str = "fail") -> AutoBacktestCacheLoadResult:
    if error_policy not in {"fail", "reset"}:
        raise ValueError("error_policy must be one of: fail, reset")

    def _on_error(reason: str) -> AutoBacktestCacheLoadResult:
        if error_policy == "reset":
            return AutoBacktestCacheLoadResult(ok=True, reason=reason, state=_default_state())
        return AutoBacktestCacheLoadResult(ok=False, reason=reason, state=None)

    cache_path = Path(path)
    if not cache_path.exists():
        return _on_error("missing_file")

    try:
        with cache_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError:
        return _on_error("invalid_json")
    except OSError:
        return _on_error("io_error")

    state = _parse_state(payload)
    if state is None:
        return _on_error("invalid_payload")

    return AutoBacktestCacheLoadResult(ok=True, reason=None, state=state)


def build_auto_backtest_plan(
    *,
    latest_prices_date: Any,
    config: AutoBacktestConfig | Mapping[str, Any],
    cache_state: AutoBacktestCacheState,
) -> AutoBacktestPlan:
    normalized_config = normalize_config(config)
    config_fingerprint = compute_config_fingerprint(normalized_config)
    run_key = compute_run_key(latest_prices_date, config_fingerprint)

    attempted = bool(cache_state.run_attempted and cache_state.run_attempted_for_key == run_key)
    failed_for_key = bool(cache_state.status == "failed" and cache_state.run_attempted_for_key == run_key)
    stale = bool(cache_state.last_run_key != run_key or failed_for_key)
    if failed_for_key:
        attempted = False
    should_run = bool(stale and (not attempted))

    return AutoBacktestPlan(
        run_key=run_key,
        config_fingerprint=config_fingerprint,
        is_stale=stale,
        run_attempted=attempted,
        run_attempted_for_key=run_key,
        should_run=should_run,
        show_already_attempted_caption=bool(stale and attempted),
    )


def mark_started(
    cache_state: AutoBacktestCacheState,
    *,
    latest_prices_date: Any,
    config: AutoBacktestConfig | Mapping[str, Any],
    now: dt.datetime | None = None,
) -> AutoBacktestCacheState:
    normalized_config = normalize_config(config)
    config_fingerprint = compute_config_fingerprint(normalized_config)
    run_key = compute_run_key(latest_prices_date, config_fingerprint)
    return AutoBacktestCacheState(
        config=normalized_config,
        config_fingerprint=config_fingerprint,
        last_run_key=cache_state.last_run_key,
        run_attempted=True,
        run_attempted_for_key=run_key,
        status="running",
        last_started_at=_utc_timestamp(now),
        last_finished_at=cache_state.last_finished_at,
    )


def mark_finished(
    cache_state: AutoBacktestCacheState,
    *,
    latest_prices_date: Any,
    config: AutoBacktestConfig | Mapping[str, Any] | None = None,
    status: str = "finished",
    now: dt.datetime | None = None,
) -> AutoBacktestCacheState:
    if status not in {"finished", "failed"}:
        raise ValueError("status must be one of: finished, failed")
    normalized_config = normalize_config(config or cache_state.config)
    config_fingerprint = compute_config_fingerprint(normalized_config)
    run_key = compute_run_key(latest_prices_date, config_fingerprint)
    last_run_key = run_key if status == "finished" else cache_state.last_run_key
    return AutoBacktestCacheState(
        config=normalized_config,
        config_fingerprint=config_fingerprint,
        last_run_key=last_run_key,
        run_attempted=True,
        run_attempted_for_key=run_key,
        status=status,
        last_started_at=cache_state.last_started_at,
        last_finished_at=_utc_timestamp(now),
    )


def persist_cache_atomic(
    path: str,
    state: AutoBacktestCacheState,
    *,
    permission_error_retries: int = 8,
    retry_delay_seconds: float = 0.15,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_name(f"{target.name}.{os.getpid()}.{int(time.time() * 1000)}.tmp")
    payload = _serialize_state(state)
    retries = max(1, int(permission_error_retries))

    for attempt in range(1, retries + 1):
        try:
            with tmp_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, target)
            return
        except PermissionError:
            if attempt >= retries:
                raise
            backoff = max(0.0, float(retry_delay_seconds)) * (2 ** (attempt - 1))
            time.sleep(backoff)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
