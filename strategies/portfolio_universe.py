"""Portfolio construction universe policy and diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


DEFAULT_MIN_HISTORY_OBS = 3


@dataclass(frozen=True)
class OptimizerUniversePolicy:
    """Policy that separates scan display state from optimizer eligibility."""

    eligible_rating_tokens: tuple[str, ...] = ("ENTER STRONG BUY", "ENTER BUY")
    research_only_rating_tokens: tuple[str, ...] = ("WATCH",)
    excluded_rating_tokens: tuple[str, ...] = ("EXIT", "KILL", "AVOID", "IGNORE")
    min_history_obs: int = DEFAULT_MIN_HISTORY_OBS

    def summary(self) -> dict[str, object]:
        return {
            "eligible_ratings": list(self.eligible_rating_tokens),
            "research_only_ratings": list(self.research_only_rating_tokens),
            "excluded_ratings": list(self.excluded_rating_tokens),
            "min_history_obs": int(self.min_history_obs),
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

    @property
    def included(self) -> bool:
        return self.status == "included"

    def as_dict(self) -> dict[str, object]:
        return {
            "ticker": self.ticker,
            "permno": self.permno,
            "rating": self.rating,
            "action": self.action,
            "status": self.status,
            "reason": self.reason,
            "history_obs": int(self.history_obs),
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

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([record.as_dict() for record in self.records])


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


def build_optimizer_universe(
    df_scan: pd.DataFrame,
    ticker_map: dict,
    prices_wide: pd.DataFrame,
    policy: OptimizerUniversePolicy | None = None,
) -> OptimizerUniverseResult:
    """Build an investable optimizer universe from raw scanner output.

    The function intentionally ignores dashboard display ordering as a source of
    portfolio eligibility. Scanner rows can be shown to the user without being
    allowed into capital allocation.
    """

    policy = policy or DEFAULT_OPTIMIZER_UNIVERSE_POLICY
    included: list[UniverseRecord] = []
    excluded: list[UniverseRecord] = []
    missing_mappings: list[UniverseRecord] = []
    insufficient_history: list[UniverseRecord] = []

    if not isinstance(df_scan, pd.DataFrame) or df_scan.empty or "Ticker" not in df_scan.columns:
        return OptimizerUniverseResult(
            included=tuple(),
            excluded=tuple(),
            missing_mappings=tuple(),
            insufficient_history=tuple(),
            policy_summary=policy.summary(),
        )

    ticker_to_permno_all, ticker_to_permno_with_prices = _build_ticker_to_permno(ticker_map, prices_wide)
    seen: set[str] = set()

    for _, row in df_scan.iterrows():
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
            )
            excluded.append(record)
            insufficient_history.append(record)
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
