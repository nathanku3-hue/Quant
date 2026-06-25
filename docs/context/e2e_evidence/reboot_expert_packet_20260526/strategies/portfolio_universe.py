"""Portfolio construction universe policy and diagnostics."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from core.data_orchestrator import PriceEndpointFreshness
from core.data_orchestrator import build_price_endpoint_freshness
from core.data_orchestrator import price_column_latest_date
from core.data_orchestrator import price_endpoint_is_fresh
from core.data_orchestrator import price_frame_latest_date


DEFAULT_MIN_HISTORY_OBS = 3
DEFAULT_MAX_ENDPOINT_STALENESS_DAYS = 5
DEFAULT_POSITION_MEMORY_PATH = Path("data/portfolio_positions.json")


@dataclass(frozen=True)
class OptimizerUniversePolicy:
    """Policy that separates scan display state from optimizer eligibility."""

    eligible_rating_tokens: tuple[str, ...] = ("ENTER STRONG BUY", "ENTER BUY")
    maintain_rating_tokens: tuple[str, ...] = ("HOLD", "TRAIL TIGHT", "TRAIL")
    research_only_rating_tokens: tuple[str, ...] = ("WATCH",)
    excluded_rating_tokens: tuple[str, ...] = ("EXIT", "KILL", "AVOID", "IGNORE")
    min_history_obs: int = DEFAULT_MIN_HISTORY_OBS
    max_endpoint_staleness_days: int = DEFAULT_MAX_ENDPOINT_STALENESS_DAYS

    def summary(self) -> dict[str, object]:
        return {
            "eligible_ratings": list(self.eligible_rating_tokens),
            "maintain_ratings": list(self.maintain_rating_tokens),
            "research_only_ratings": list(self.research_only_rating_tokens),
            "excluded_ratings": list(self.excluded_rating_tokens),
            "min_history_obs": int(self.min_history_obs),
            "max_endpoint_staleness_days": int(self.max_endpoint_staleness_days),
            "watch_default": "research_only",
            "conviction_mode": "not_approved",
            "manual_override": "not_approved",
        }


DEFAULT_OPTIMIZER_UNIVERSE_POLICY = OptimizerUniversePolicy()


@dataclass(frozen=True)
class UniverseRecord:
    ticker: str
    permno: object | None
    rating: str
    action: str
    status: str
    reason: str
    history_obs: int
    latest_price_date: str = ""

    @property
    def included(self) -> bool:
        return self.status.startswith("included")

    def as_dict(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "permno": self.permno,
            "rating": self.rating,
            "action": self.action,
            "status": self.status,
            "reason": self.reason,
            "history_obs": int(self.history_obs),
            "latest_price_date": self.latest_price_date,
        }


@dataclass(frozen=True)
class OptimizerUniverseResult:
    included: tuple[UniverseRecord, ...]
    excluded: tuple[UniverseRecord, ...]
    missing_mappings: tuple[UniverseRecord, ...]
    insufficient_history: tuple[UniverseRecord, ...]
    policy_summary: dict[str, object]

    @property
    def records(self) -> tuple[UniverseRecord, ...]:
        return self.included + self.excluded

    @property
    def included_tickers(self) -> list[str]:
        return [record.ticker for record in self.included]

    @property
    def included_permnos(self) -> list[object]:
        return [record.permno for record in self.included if record.permno is not None]

    @property
    def missing_history(self) -> tuple[UniverseRecord, ...]:
        return tuple(
            record
            for record in self.insufficient_history
            if record.reason
            in {
                "local_price_history_unavailable",
                "open_position_price_history_unavailable",
            }
        )

    @property
    def stale_endpoints(self) -> tuple[UniverseRecord, ...]:
        return tuple(
            record
            for record in self.insufficient_history
            if record.reason
            in {
                "stale_price_endpoint",
                "open_position_stale_price_endpoint",
            }
        )

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([record.as_dict() for record in self.records])


def split_history_readiness(records: Iterable[UniverseRecord]) -> dict[str, tuple[UniverseRecord, ...]]:
    """Split price-readiness failures without relaxing the underlying gate."""
    missing_history: list[UniverseRecord] = []
    stale_endpoint: list[UniverseRecord] = []
    other: list[UniverseRecord] = []
    for record in records:
        if record.reason in {"local_price_history_unavailable", "open_position_price_history_unavailable"}:
            missing_history.append(record)
        elif record.reason in {"stale_price_endpoint", "open_position_stale_price_endpoint"}:
            stale_endpoint.append(record)
        else:
            other.append(record)
    return {
        "missing_history": tuple(missing_history),
        "stale_endpoint": tuple(stale_endpoint),
        "other": tuple(other),
    }


def optimizer_universe_health_summary(result: OptimizerUniverseResult | None) -> dict[str, object]:
    """Return UI/report-safe universe diagnostics with stale endpoints separated."""
    if result is None:
        return {
            "included": 0,
            "excluded": 0,
            "missing_mappings": 0,
            "insufficient_history": 0,
            "missing_history": 0,
            "stale_endpoint": 0,
            "other_history_fail": 0,
            "stale_endpoint_tickers": [],
            "missing_history_tickers": [],
        }
    split = split_history_readiness(result.insufficient_history)
    return {
        "included": len(result.included),
        "excluded": len(result.excluded),
        "missing_mappings": len(result.missing_mappings),
        "insufficient_history": len(result.insufficient_history),
        "missing_history": len(split["missing_history"]),
        "stale_endpoint": len(split["stale_endpoint"]),
        "other_history_fail": len(split["other"]),
        "stale_endpoint_tickers": [record.ticker for record in split["stale_endpoint"]],
        "missing_history_tickers": [record.ticker for record in split["missing_history"]],
    }


def _normalize_token(value: object) -> str:
    text = str(value or "").upper()
    for char in (":", "/", "-", "_", "(", ")", "[", "]"):
        text = text.replace(char, " ")
    return " ".join(text.split())


def _contains_any(text: str, tokens: Iterable[str]) -> bool:
    normalized_tokens = (_normalize_token(token) for token in tokens)
    return any(token and token in text for token in normalized_tokens)


def classify_optimizer_eligibility(
    rating: object,
    action: object,
    policy: OptimizerUniversePolicy = DEFAULT_OPTIMIZER_UNIVERSE_POLICY,
) -> tuple[str, str]:
    """Classify a scanner row before mapping/price readiness checks."""

    rating_text = _normalize_token(rating)
    action_text = _normalize_token(action)
    combined = f"{rating_text} {action_text}".strip()

    if _contains_any(combined, policy.excluded_rating_tokens):
        if "EXIT" in combined or "KILL" in combined:
            return "excluded", "exit_or_kill"
        if "AVOID" in combined:
            return "excluded", "avoid"
        return "excluded", "ignore"

    if _contains_any(rating_text, policy.research_only_rating_tokens):
        return "research_only", "watch_research_only"

    if _contains_any(rating_text, policy.eligible_rating_tokens):
        return "eligible", "eligible_rating"

    if _contains_any(rating_text, policy.maintain_rating_tokens):
        return "maintain", "maintain_existing_position"

    return "excluded", "not_portfolio_eligible"


def _build_ticker_to_permno(ticker_map: dict, prices_wide: pd.DataFrame) -> tuple[dict[str, object], dict[str, object]]:
    all_mapped: dict[str, object] = {}
    price_ready: dict[str, object] = {}
    available = set(prices_wide.columns) if isinstance(prices_wide, pd.DataFrame) else set()

    for permno, ticker in (ticker_map or {}).items():
        key = str(ticker).upper()
        if not key:
            continue
        all_mapped.setdefault(key, permno)
        if permno in available:
            price_ready.setdefault(key, permno)

    return all_mapped, price_ready


def _history_observation_count(prices_wide: pd.DataFrame, permno: object | None) -> int:
    if permno is None or not isinstance(prices_wide, pd.DataFrame) or permno not in prices_wide.columns:
        return 0
    series = pd.to_numeric(prices_wide[permno], errors="coerce")
    series = series.replace([np.inf, -np.inf], np.nan)
    return int(series.notna().sum())


def _endpoint_date_text(value: pd.Timestamp | None) -> str:
    if value is None or pd.isna(value):
        return ""
    return pd.Timestamp(value).date().isoformat()


def map_permno_weights_to_ticker_weights(weights: pd.Series, ticker_map: dict) -> pd.Series:
    """Map permno-indexed weights to ticker weights while preserving residual cash."""
    if not isinstance(weights, pd.Series) or weights.empty:
        return pd.Series(dtype="float64")

    ticker_lookup = ticker_map if isinstance(ticker_map, dict) else {}
    rows: dict[str, float] = {}
    clean_weights = pd.to_numeric(weights, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    clean_weights = clean_weights[clean_weights > 0]
    for permno, weight in clean_weights.items():
        ticker = ticker_lookup.get(permno)
        if ticker is None:
            try:
                ticker = ticker_lookup.get(int(permno))
            except Exception:
                ticker = None
        if ticker:
            ticker_key = str(ticker).upper()
            rows[ticker_key] = rows.get(ticker_key, 0.0) + float(weight)

    out = pd.Series(rows, dtype="float64")
    out_total = float(out.sum()) if not out.empty else 0.0
    if out.empty or out_total <= 0:
        return pd.Series(dtype="float64")
    if out_total > 1.0:
        return out / out_total
    return out


def _has_open_position(ticker: str, position_memory: dict[str, dict]) -> bool:
    if ticker not in position_memory:
        return False
    try:
        return float(position_memory[ticker].get("last_weight", 0.0)) > 0.0
    except (TypeError, ValueError):
        return False


def _open_position_reason(ticker: str, position_memory: dict[str, dict]) -> str:
    source = str(position_memory.get(ticker, {}).get("source", "")).lower()
    if source == "lifecycle_replay":
        return "open_lifecycle_position"
    return "position_memory_hold"


def build_optimizer_universe(
    df_scan: pd.DataFrame,
    ticker_map: dict,
    prices_wide: pd.DataFrame,
    policy: OptimizerUniversePolicy | None = None,
    position_memory: dict[str, dict] | None = None,
    price_freshness: PriceEndpointFreshness | None = None,
) -> OptimizerUniverseResult:
    """Build an investable optimizer universe from raw scanner output.

    The function intentionally ignores dashboard display ordering as a source of
    portfolio eligibility. Scanner rows can be shown to the user without being
    allowed into capital allocation.

    position_memory: if provided, tickers in maintain-tier ratings that exist in
    this dict are kept in the universe with their last-known weight as upper bound.
    """

    policy = policy or DEFAULT_OPTIMIZER_UNIVERSE_POLICY
    position_memory = position_memory or {}
    included: list[UniverseRecord] = []
    excluded: list[UniverseRecord] = []
    missing_mappings: list[UniverseRecord] = []
    insufficient_history: list[UniverseRecord] = []

    has_scan = isinstance(df_scan, pd.DataFrame) and not df_scan.empty and "Ticker" in df_scan.columns
    if not has_scan and not position_memory:
        return OptimizerUniverseResult(
            included=tuple(),
            excluded=tuple(),
            missing_mappings=tuple(),
            insufficient_history=tuple(),
            policy_summary=policy.summary(),
        )

    ticker_to_permno_all, ticker_to_permno_with_prices = _build_ticker_to_permno(ticker_map, prices_wide)
    if price_freshness is None:
        price_freshness = build_price_endpoint_freshness(prices_wide)
    required_latest = price_frame_latest_date(prices_wide, freshness=price_freshness)
    seen: set[str] = set()

    scan_rows = df_scan.iterrows() if has_scan else []
    for _, row in scan_rows:
        ticker = str(row.get("Ticker", "")).upper().strip()
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)

        rating = str(row.get("Rating", ""))
        action = str(row.get("Action", ""))
        eligibility, reason = classify_optimizer_eligibility(rating, action, policy=policy)

        mapped_permno = ticker_to_permno_all.get(ticker)
        price_permno = ticker_to_permno_with_prices.get(ticker)
        permno = price_permno if price_permno is not None else mapped_permno
        history_obs = _history_observation_count(prices_wide, price_permno)
        latest_price_date = price_column_latest_date(
            prices_wide,
            price_permno,
            freshness=price_freshness,
        )
        endpoint_is_fresh = price_endpoint_is_fresh(
            latest_price_date,
            required_latest,
            max_staleness_days=policy.max_endpoint_staleness_days,
        )

        if mapped_permno is None:
            record = UniverseRecord(
                ticker=ticker,
                permno=None,
                rating=rating,
                action=action,
                status="missing_mapping",
                reason="ticker_not_in_local_ticker_map",
                history_obs=0,
            )
            excluded.append(record)
            missing_mappings.append(record)
            continue

        if price_permno is None or history_obs < int(policy.min_history_obs):
            record = UniverseRecord(
                ticker=ticker,
                permno=permno,
                rating=rating,
                action=action,
                status="insufficient_history",
                reason="local_price_history_unavailable",
                history_obs=history_obs,
                latest_price_date=_endpoint_date_text(latest_price_date),
            )
            excluded.append(record)
            insufficient_history.append(record)
            continue

        if not endpoint_is_fresh:
            record = UniverseRecord(
                ticker=ticker,
                permno=permno,
                rating=rating,
                action=action,
                status="insufficient_history",
                reason="stale_price_endpoint",
                history_obs=history_obs,
                latest_price_date=_endpoint_date_text(latest_price_date),
            )
            excluded.append(record)
            insufficient_history.append(record)
            continue

        if _has_open_position(ticker, position_memory):
            included.append(
                UniverseRecord(
                    ticker=ticker,
                    permno=price_permno,
                    rating=rating,
                    action=action,
                    status="included_current_hold",
                    reason=_open_position_reason(ticker, position_memory),
                    history_obs=history_obs,
                    latest_price_date=_endpoint_date_text(latest_price_date),
                )
            )
            continue

        if eligibility == "eligible":
            included.append(
                UniverseRecord(
                    ticker=ticker,
                    permno=price_permno,
                    rating=rating,
                    action=action,
                    status="included",
                    reason=reason,
                    history_obs=history_obs,
                    latest_price_date=_endpoint_date_text(latest_price_date),
                )
            )
            continue

        if eligibility == "maintain" and _has_open_position(ticker, position_memory):
            included.append(
                UniverseRecord(
                    ticker=ticker,
                    permno=price_permno,
                    rating=rating,
                    action=action,
                    status="included_maintain",
                    reason=reason,
                    history_obs=history_obs,
                    latest_price_date=_endpoint_date_text(latest_price_date),
                )
            )
            continue

        status = "research_only" if eligibility == "research_only" else "excluded"
        excluded.append(
            UniverseRecord(
                ticker=ticker,
                permno=price_permno,
                rating=rating,
                action=action,
                status=status,
                reason=reason,
                history_obs=history_obs,
                latest_price_date=_endpoint_date_text(latest_price_date),
            )
        )

    for ticker in sorted(position_memory):
        if ticker in seen or not _has_open_position(ticker, position_memory):
            continue

        mapped_permno = ticker_to_permno_all.get(ticker)
        price_permno = ticker_to_permno_with_prices.get(ticker)
        permno = price_permno if price_permno is not None else mapped_permno
        history_obs = _history_observation_count(prices_wide, price_permno)
        latest_price_date = price_column_latest_date(
            prices_wide,
            price_permno,
            freshness=price_freshness,
        )
        endpoint_is_fresh = price_endpoint_is_fresh(
            latest_price_date,
            required_latest,
            max_staleness_days=policy.max_endpoint_staleness_days,
        )

        if mapped_permno is None:
            record = UniverseRecord(
                ticker=ticker,
                permno=None,
                rating="",
                action="",
                status="missing_mapping",
                reason="open_position_not_in_local_ticker_map",
                history_obs=0,
            )
            excluded.append(record)
            missing_mappings.append(record)
            continue

        if price_permno is None or history_obs < int(policy.min_history_obs):
            record = UniverseRecord(
                ticker=ticker,
                permno=permno,
                rating="",
                action="",
                status="insufficient_history",
                reason="open_position_price_history_unavailable",
                history_obs=history_obs,
                latest_price_date=_endpoint_date_text(latest_price_date),
            )
            excluded.append(record)
            insufficient_history.append(record)
            continue

        if not endpoint_is_fresh:
            record = UniverseRecord(
                ticker=ticker,
                permno=permno,
                rating="",
                action="",
                status="insufficient_history",
                reason="open_position_stale_price_endpoint",
                history_obs=history_obs,
                latest_price_date=_endpoint_date_text(latest_price_date),
            )
            excluded.append(record)
            insufficient_history.append(record)
            continue

        included.append(
            UniverseRecord(
                ticker=ticker,
                permno=price_permno,
                rating="",
                action="",
                status="included_current_hold",
                reason=_open_position_reason(ticker, position_memory),
                history_obs=history_obs,
                latest_price_date=_endpoint_date_text(latest_price_date),
            )
        )

    return OptimizerUniverseResult(
        included=tuple(included),
        excluded=tuple(excluded),
        missing_mappings=tuple(missing_mappings),
        insufficient_history=tuple(insufficient_history),
        policy_summary=policy.summary(),
    )


def diagnose_max_weight_feasibility(
    n_assets: int,
    max_weight: float,
    tolerance: float = 1e-6,
) -> dict[str, object]:
    """Diagnose whether a max-weight cap leaves optimization freedom."""

    try:
        n = int(n_assets)
    except Exception:
        n = 0
    try:
        cap = float(max_weight)
    except Exception:
        cap = 0.0

    if n <= 0:
        return {
            "n_assets": n,
            "max_weight": cap,
            "min_feasible_max_weight": np.nan,
            "is_feasible": False,
            "is_boundary_forced": False,
            "message": "No assets are available for optimization.",
        }

    min_feasible = 1.0 / n
    capacity = cap * n
    is_feasible = capacity >= (1.0 - tolerance)
    is_boundary_forced = is_feasible and cap <= (min_feasible + tolerance)

    if not is_feasible:
        message = (
            f"{n} assets with max weight {cap:.2%} cannot reach 100% allocation; "
            f"minimum feasible cap is {min_feasible:.2%}."
        )
    elif is_boundary_forced:
        message = (
            f"{n} assets with max weight {cap:.2%} sits at the minimum feasible boundary; "
            "the allocation is effectively forced toward equal weight."
        )
    else:
        message = "Max-weight cap is feasible and leaves allocation room."

    return {
        "n_assets": n,
        "max_weight": cap,
        "min_feasible_max_weight": min_feasible,
        "is_feasible": is_feasible,
        "is_boundary_forced": is_boundary_forced,
        "message": message,
    }



# ---------------------------------------------------------------------------
# Position Memory: tracks owned positions across scanner refreshes
# ---------------------------------------------------------------------------


def load_position_memory(path: Path | str | None = None) -> dict[str, dict]:
    """Load position memory from JSON. Returns {TICKER: {permno, last_weight, ...}}."""
    path = Path(path) if path else DEFAULT_POSITION_MEMORY_PATH
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return {k.upper(): v for k, v in data.items() if isinstance(v, dict)}
    except (json.JSONDecodeError, OSError):
        return {}


def load_current_position_memory(
    as_of: str | pd.Timestamp | None = None,
    position_path: Path | str | None = None,
    lifecycle_path: Path | str | None = None,
) -> dict[str, dict]:
    """Load current holdings, preferring PIT-safe lifecycle replay state.

    If a lifecycle replay exists, it is the authority for whether the current
    portfolio has open holds or has sold all positions. JSON position memory is
    only the fallback when no replay evidence exists yet.
    """
    from data.portfolio_lifecycle_log import get_open_lifecycle_positions, read_lifecycle_log

    lifecycle_events = read_lifecycle_log(lifecycle_path)
    if not lifecycle_events.empty:
        return get_open_lifecycle_positions(as_of=as_of, path=lifecycle_path)
    return load_position_memory(position_path)


def save_position_memory(
    memory: dict[str, dict],
    path: Path | str | None = None,
) -> None:
    """Atomically write position memory to JSON."""
    path = Path(path) if path else DEFAULT_POSITION_MEMORY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(memory, indent=2, default=str)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        os.replace(tmp, str(path))
    except BaseException:
        os.close(fd) if not os.get_inheritable(fd) else None
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def update_position_memory_after_optimization(
    weights: "pd.Series",
    ticker_map: dict,
    universe: OptimizerUniverseResult,
    path: Path | str | None = None,
    lifecycle_path: Path | str | None = None,
) -> dict[str, dict]:
    """Update position memory after a successful optimization run.

    - Adds/updates tickers that received positive weight.
    - Removes tickers that were explicitly excluded (EXIT/KILL).
    - Emits ENTER/EXIT lifecycle events for audit replay.
    """
    import datetime as _dt

    from data.portfolio_lifecycle_log import append_lifecycle_event

    now = _dt.datetime.now().isoformat()
    memory = load_current_position_memory(as_of=now, position_path=path, lifecycle_path=lifecycle_path)

    # Build permno -> ticker reverse map
    permno_to_ticker: dict[object, str] = {}
    for permno, ticker in (ticker_map or {}).items():
        permno_to_ticker[permno] = str(ticker).upper()

    # Update from current weights — emit ENTER for new positions
    for permno, weight in weights.items():
        ticker = permno_to_ticker.get(permno, "")
        if not ticker:
            continue
        w = float(weight)
        if w > 0:
            entry = memory.get(ticker, {})
            is_new = ticker not in memory
            memory[ticker] = {
                "permno": permno,
                "last_weight": w,
                "entry_date": entry.get("entry_date", now),
                "last_updated": now,
            }
            if is_new:
                append_lifecycle_event(
                    ticker=ticker,
                    action="ENTER",
                    date=now,
                    weight=w,
                    rating="",
                    reason="optimizer_allocation",
                    permno=permno,
                    path=lifecycle_path,
                )

    # Remove tickers that were explicitly exited — emit EXIT for removed positions
    for record in universe.excluded:
        if record.reason == "exit_or_kill" and record.ticker in memory:
            mem = memory[record.ticker]
            append_lifecycle_event(
                ticker=record.ticker,
                action="EXIT",
                date=now,
                weight=0.0,
                rating=record.rating,
                reason="exit_or_kill",
                permno=mem.get("permno"),
                path=lifecycle_path,
            )
            memory.pop(record.ticker)

    save_position_memory(memory, path)
    return memory


def get_maintain_weight_caps(
    universe: OptimizerUniverseResult,
    position_memory: dict[str, dict],
    ticker_map: dict,
) -> dict[object, float]:
    """Return {permno: max_weight} for maintain-tier positions.

    These positions keep their last-known weight as an upper bound;
    the optimizer cannot increase them beyond what was previously allocated.
    """
    caps: dict[object, float] = {}
    for record in universe.included:
        if record.status in {"included_maintain", "included_current_hold"} and record.permno is not None:
            mem = position_memory.get(record.ticker, {})
            last_w = float(mem.get("last_weight", 0.0))
            if last_w > 0:
                caps[record.permno] = last_w
    return caps
