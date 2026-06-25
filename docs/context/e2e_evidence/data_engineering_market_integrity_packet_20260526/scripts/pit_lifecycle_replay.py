"""Point-in-time forward replay of portfolio lifecycle events.

Walks forward through historical features.parquet data and detects
eligibility transitions using PIT-equivalent logic aligned with the live scanner:
- ENTER: z_demand > 0 AND capital_cycle_score > 0 AND dist_sma20 <= 5% AND no trend_veto
- EXIT: confirmed dist_sma20 > 12% OR trend_veto on a held ticker, with churn guards

Ticker universe: SCANNER_TICKERS ∪ pinned_thesis_universe.yml (fail-closed).
This is a reconstruction from available data, not synthetic seeding.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.portfolio_lifecycle_log import append_lifecycle_event

FEATURES_PATH = Path("data/processed/features.parquet")
PRICES_TRI_PATH = Path("data/processed/prices_tri.parquet")

# Scanner-equivalent thresholds — aligned with live scanner logic:
#   Live Score == 100: demand > 0, supply >= 0, pricing > 0, margin > 0
#   PIT equivalent: z_demand > 0 AND capital_cycle_score > 0 (fundamental gate)
#   ENTER: fundamental gate AND four-factor lifecycle confirmation AND dist_sma20 in entry zone AND no trend_veto
#   EXIT: confirmed dist_sma20 > parabolic threshold OR trend_veto on held position
PARABOLIC_DIST_SMA20 = 0.12   # 12% above SMA20 triggers EXIT
ACCUMULATION_DIST_MAX = 0.05  # within 5% of SMA20 is entry zone
HARD_EXIT_DIST_SMA20 = 0.20   # hard stretch can override min-hold/confirmation
DEFAULT_MAX_POSITIONS = 10
DEFAULT_ENTRY_WEIGHT = round(1.0 / DEFAULT_MAX_POSITIONS, 4)
MIN_HOLD_DAYS = 20
REENTRY_COOLDOWN_DAYS = 10
EXIT_CONFIRM_DAYS = 2
ENTRY_CONFIRM_DAYS = 3
LIFECYCLE_FACTOR_COLUMNS = (
    "z_demand",
    "z_moat",
    "z_inventory_quality_proxy",
    "z_discipline_cond",
)
RULE_OF_100_FACTOR_SOURCES = {
    "demand": "z_demand",
    "supply": "z_inventory_quality_proxy",
    "pricing": "z_moat",
    "margin": "z_discipline_cond",
}
MIN_FACTOR_COVERAGE = 3
MIN_FACTOR_POSITIVES = 3
MIN_HOLD_FACTOR_POSITIVES = 2
BASE_RULE100_WEIGHT = 0.10
RULE100_BONUS_PER_EXTRA_FACTOR = 0.025
MAX_SINGLE_NAME_WEIGHT = 0.15
TRIM_SUGGESTED_WEIGHT_DELTA = -0.025
TIGHTEN_SUGGESTED_WEIGHT_DELTA = 0.0
BASELINE_DECISION_ACTIONS = {
    "BUY": 18,
    "SELL": 15,
    "HOLD": 993,
    "NO_ACTION": 4398,
}
BASELINE_OPEN_HOLDS = ["AMAT", "LRCX", "TSM"]
DECISION_LOG_COLUMNS = [
    "date",
    "ticker",
    "permno",
    "position_state_before",
    "position_state_after",
    "lifecycle_action",
    "buy_sell",
    "decision_action",
    "primary_reason",
    "reason_codes",
    "weight",
    "target_weight",
    "suggested_weight_delta",
    "price",
    "hold_days",
    "entry_streak",
    "exit_streak",
    "cooldown_until",
    "reentry_blocked",
    "demand",
    "supply",
    "pricing",
    "margin",
    "factor_strength",
    "factor_present_count",
    "factor_positive_count",
    "rule100_confirmed",
    "rule100_hold_intact",
    "rule100_provenance",
    "z_demand",
    "capital_cycle_score",
    "dist_sma20",
    "trend_veto",
    "raw_entry_gate",
    "entry_confirmed",
    "raw_exit_gate",
    "hard_exit_signal",
    "trim_signal",
    "exit_confirmed",
]


def is_pit_eligible(z_demand: float, capital_cycle_score: float, dist_sma20: float, trend_veto: bool) -> bool:
    """Shared eligibility gate for PIT replay. Matches live scanner fundamental logic."""
    fundamental_pass = z_demand > 0 and capital_cycle_score > 0
    return fundamental_pass and dist_sma20 <= ACCUMULATION_DIST_MAX and not trend_veto


def is_pit_exit(dist_sma20: float, trend_veto: bool) -> bool:
    """Shared full-exit candidate trigger for PIT replay."""
    return dist_sma20 > HARD_EXIT_DIST_SMA20 or trend_veto


def is_pit_trim(dist_sma20: float) -> bool:
    """Return True for audit-only v0 trim zone."""
    return PARABOLIC_DIST_SMA20 < dist_sma20 <= HARD_EXIT_DIST_SMA20


def replay_entry_weight(max_positions: int = DEFAULT_MAX_POSITIONS) -> float:
    """Drop-in target weight for a new lifecycle replay position."""
    positions = max(1, int(max_positions))
    return round(1.0 / positions, 4)


@dataclass(frozen=True)
class Rule100State:
    """PIT-safe Rule-of-100 proxy state for the current lifecycle policy."""

    demand: float | None
    supply: float | None
    pricing: float | None
    margin: float | None
    provenance: dict[str, str]

    @property
    def values(self) -> dict[str, float | None]:
        return {
            "demand": self.demand,
            "supply": self.supply,
            "pricing": self.pricing,
            "margin": self.margin,
        }

    @property
    def present_count(self) -> int:
        return sum(value is not None for value in self.values.values())

    @property
    def positive_count(self) -> int:
        return sum(float(value) > 0 for value in self.values.values() if value is not None)

    @property
    def confirmed(self) -> bool:
        return self.present_count >= MIN_FACTOR_COVERAGE and self.positive_count >= MIN_FACTOR_POSITIVES

    @property
    def hold_intact(self) -> bool:
        return self.present_count >= MIN_FACTOR_COVERAGE and self.positive_count >= MIN_HOLD_FACTOR_POSITIVES

    @property
    def factor_strength(self) -> float:
        if self.present_count <= 0:
            return 0.0
        return round(self.positive_count / self.present_count, 6)

    def to_record(self) -> dict[str, object]:
        return {
            **self.values,
            "factor_strength": self.factor_strength,
            "factor_present_count": self.present_count,
            "factor_positive_count": self.positive_count,
            "rule100_confirmed": self.confirmed,
            "rule100_hold_intact": self.hold_intact,
            "rule100_provenance": self.provenance,
        }


def build_rule100_state(row: pd.Series) -> Rule100State:
    """Build the current Rule-of-100 adapter from explicit proxy columns."""
    return Rule100State(
        demand=_nullable_float(row.get(RULE_OF_100_FACTOR_SOURCES["demand"])),
        supply=_nullable_float(row.get(RULE_OF_100_FACTOR_SOURCES["supply"])),
        pricing=_nullable_float(row.get(RULE_OF_100_FACTOR_SOURCES["pricing"])),
        margin=_nullable_float(row.get(RULE_OF_100_FACTOR_SOURCES["margin"])),
        provenance=dict(RULE_OF_100_FACTOR_SOURCES),
    )


def rule100_target_weight(state: Rule100State) -> float:
    """Conviction-based entry target weight for Rule-of-100 lifecycle v0."""
    bonus = max(0, state.positive_count - MIN_FACTOR_POSITIVES) * RULE100_BONUS_PER_EXTRA_FACTOR
    return round(min(BASE_RULE100_WEIGHT + bonus, MAX_SINGLE_NAME_WEIGHT), 4)


def lifecycle_factor_confirmation(row: pd.Series) -> tuple[bool, int, int]:
    """Return Rule-of-100-style PIT factor confirmation from available feature columns.

    This is a lifecycle state filter, not a resurrected Rule-of-100 ranking sleeve.
    The current feature store exposes demand, moat, inventory/quality, and discipline
    vectors; at least three must be present and positive.
    """
    state = build_rule100_state(row)
    return state.confirmed, state.present_count, state.positive_count


def _coerce_float(value: object, default: float = 0.0) -> float:
    coerced = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(coerced):
        if value is None:
            return default
        if pd.isna(value):
            return float("nan")
        return default
    return float(coerced)


def _nullable_float(value: object, ndigits: int = 6) -> float | None:
    coerced = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(coerced):
        return None
    return round(float(coerced), ndigits)


def rule_of_100_factor_state(row: pd.Series) -> dict[str, object]:
    """Expose the current PIT-safe Rule-of-100 proxy state for audit exports.

    The feature store does not yet contain literal supply/pricing/margin columns.
    This audit adapter makes the current proxy mapping explicit so the next
    optimal-policy round can replace it without touching the replay mechanics.
    """
    return build_rule100_state(row).to_record()


def _entry_rejection_reasons(
    *,
    z_demand: float,
    capital_cycle_score: float,
    dist_sma20: float,
    trend_veto: bool,
    factor_confirmed: bool,
    factor_coverage: int,
    factor_positives: int,
) -> list[str]:
    reasons: list[str] = []
    if pd.isna(z_demand) or z_demand <= 0:
        reasons.append("demand_gate_failed")
    if pd.isna(capital_cycle_score) or capital_cycle_score <= 0:
        reasons.append("capital_cycle_gate_failed")
    if pd.isna(dist_sma20):
        reasons.append("technical_entry_zone_missing")
    elif dist_sma20 > ACCUMULATION_DIST_MAX:
        reasons.append("technical_entry_zone_failed")
    if trend_veto:
        reasons.append("trend_veto")
    if factor_coverage < MIN_FACTOR_COVERAGE:
        reasons.append("factor_coverage_missing")
    elif not factor_confirmed:
        reasons.append(f"factor_confirmation_failed_{factor_positives}_of_{factor_coverage}")
    return reasons or ["not_in_entry_state"]


def _write_jsonl_frame(df: pd.DataFrame, path: Path | str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(output_path.parent), suffix=".tmp")
    os.close(fd)
    try:
        df.to_json(tmp, orient="records", lines=True, date_format="iso")
        os.replace(tmp, output_path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _write_json_atomic(payload: dict[str, object], path: Path | str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(output_path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, default=str, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, output_path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _json_scalar(value: object) -> object:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            return value
    return value


def is_reentry_blocked(
    dt: pd.Timestamp,
    cooldown_until: pd.Timestamp | None,
) -> bool:
    """Return True when a ticker is still inside its post-exit cooldown."""
    return cooldown_until is not None and pd.Timestamp(dt) < pd.Timestamp(cooldown_until)


def should_emit_exit(
    *,
    entry_date: pd.Timestamp,
    dt: pd.Timestamp,
    dist_sma20: float,
    trend_veto: bool,
    exit_streak: int,
) -> bool:
    """Return True for a full Rule-of-100 lifecycle exit."""
    if dist_sma20 > HARD_EXIT_DIST_SMA20:
        return True
    if not trend_veto:
        return False
    hold_days = (pd.Timestamp(dt) - pd.Timestamp(entry_date)).days
    return hold_days >= MIN_HOLD_DAYS and exit_streak >= EXIT_CONFIRM_DAYS


SCANNER_TICKERS = [
    "NVDA", "MU", "AMD", "TSM", "AVGO", "INTC", "TSLA", "MSFT", "META",
    "AMZN", "GOOGL", "SMCI", "VRT", "CEG", "ETN", "CLS", "TER", "LRCX",
    "AMAT", "SNDK", "WDC", "CIEN", "COHR", "RBRK", "NBIS",
]


def _default_replay_tickers() -> list[str]:
    """SCANNER_TICKERS ∪ pinned manifest tickers. Raises if loader fails."""
    from data.universe.loader import get_pinned_tickers
    pinned = get_pinned_tickers()
    return sorted(set(SCANNER_TICKERS) | set(pinned))


def run_pit_replay(
    start_date: str = "2025-01-02",
    end_date: str | None = None,
    log_path: Path | str | None = None,
    tickers: list[str] | None = None,
) -> pd.DataFrame:
    """Run point-in-time forward replay and emit lifecycle events.

    Returns DataFrame of emitted events.
    """
    tickers = tickers or _default_replay_tickers()

    features = pd.read_parquet(FEATURES_PATH)
    features = features[features["ticker"].isin(tickers)].copy()
    features["date"] = pd.to_datetime(features["date"])
    features = features[features["date"] >= pd.Timestamp(start_date)]
    if end_date:
        features = features[features["date"] <= pd.Timestamp(end_date)]
    features = features.sort_values(["date", "ticker"]).reset_index(drop=True)

    # Load prices for event price lookup
    prices = pd.read_parquet(PRICES_TRI_PATH)
    prices = prices[prices["ticker"].isin(tickers)].copy()
    prices["date"] = pd.to_datetime(prices["date"])
    price_lookup = prices.set_index(["date", "ticker"])["raw_close"]

    # State: track which tickers are currently "in portfolio"
    held: dict[str, dict] = {}  # ticker -> {entry_date, weight, exit_streak}
    cooldown_until: dict[str, pd.Timestamp] = {}
    entry_streak: dict[str, int] = {}
    events: list[dict] = []

    dates = sorted(features["date"].unique())

    for dt in dates:
        day_data = features[features["date"] == dt]

        for _, row in day_data.iterrows():
            ticker = row["ticker"]
            dist = float(row.get("dist_sma20", 0) or 0)
            veto = bool(row.get("trend_veto", False))
            permno = int(row["permno"]) if pd.notna(row.get("permno")) else None

            # Fundamental gate (maps to live scanner Score >= 90)
            z_demand = float(row.get("z_demand", 0) or 0)
            cap_cycle = float(row.get("capital_cycle_score", 0) or 0)

            # Get price
            try:
                price = float(price_lookup.get((dt, ticker), 0))
            except (KeyError, TypeError):
                price = float(row.get("adj_close", 0) or 0)

            rule100_state = build_rule100_state(row)
            factor_confirmed = rule100_state.confirmed
            factor_coverage = rule100_state.present_count
            factor_positives = rule100_state.positive_count
            is_eligible = is_pit_eligible(z_demand, cap_cycle, dist, veto) and factor_confirmed
            hard_exit_signal = dist > HARD_EXIT_DIST_SMA20
            raw_exit = (hard_exit_signal or veto) and ticker in held

            if ticker in held and veto:
                held[ticker]["exit_streak"] = int(held[ticker].get("exit_streak", 0)) + 1
            elif ticker in held:
                held[ticker]["exit_streak"] = 0

            if raw_exit and should_emit_exit(
                entry_date=pd.Timestamp(held[ticker]["entry_date"]),
                dt=dt,
                dist_sma20=dist,
                trend_veto=veto,
                exit_streak=int(held[ticker].get("exit_streak", 0)),
            ):
                reason = "hard_stop" if hard_exit_signal else "confirmed_trend_veto"
                rating = (
                    f"EXIT (Hard Stop dist_sma20={dist*100:.1f}%)"
                    if hard_exit_signal
                    else "EXIT (Confirmed Trend Veto)"
                )
                event = {
                    "ticker": ticker,
                    "action": "EXIT",
                    "date": str(dt.date()),
                    "weight": 0.0,
                    "rating": rating,
                    "reason": reason,
                    "price": price,
                    "permno": permno,
                }
                append_lifecycle_event(**event, path=log_path)
                events.append(event)
                del held[ticker]
                cooldown_until[ticker] = pd.Timestamp(dt) + pd.Timedelta(days=REENTRY_COOLDOWN_DAYS)
                entry_streak[ticker] = 0

            elif is_eligible and ticker not in held:
                entry_streak[ticker] = int(entry_streak.get(ticker, 0)) + 1
                if entry_streak[ticker] < ENTRY_CONFIRM_DAYS:
                    continue
                if is_reentry_blocked(pd.Timestamp(dt), cooldown_until.get(ticker)):
                    continue
                weight = rule100_target_weight(rule100_state)
                event = {
                    "ticker": ticker,
                    "action": "ENTER",
                    "date": str(dt.date()),
                    "weight": weight,
                    "rating": (
                        f"ENTER (demand={z_demand:.2f}, cycle={cap_cycle:.2f}, "
                        f"factors={factor_positives}/{factor_coverage}, dist={dist*100:.1f}%)"
                    ),
                    "reason": "rule100_lifecycle_confirmed",
                    "price": price,
                    "permno": permno,
                }
                append_lifecycle_event(**event, path=log_path)
                events.append(event)
                held[ticker] = {"entry_date": str(dt.date()), "weight": weight, "exit_streak": 0}
                entry_streak[ticker] = 0
            elif ticker not in held:
                entry_streak[ticker] = 0

    return pd.DataFrame(events) if events else pd.DataFrame(
        columns=["ticker", "action", "date", "weight", "rating", "reason", "price", "permno"]
    )


def export_lifecycle_decision_log(
    start_date: str = "2025-01-02",
    end_date: str | None = None,
    output_path: Path | str | None = None,
    buy_sell_path: Path | str | None = None,
    audit_summary_path: Path | str | None = None,
    tickers: list[str] | None = None,
) -> pd.DataFrame:
    """Export a PIT-safe daily decision tape without mutating the event log.

    The full tape records BUY/SELL/HOLD/NO_ACTION analysis states and reason
    codes for every ticker-date row. BUY/SELL here means replay analysis only;
    it does not create a broker instruction or dashboard recommendation.
    """
    tickers = tickers or _default_replay_tickers()

    features = pd.read_parquet(FEATURES_PATH)
    features = features[features["ticker"].isin(tickers)].copy()
    features["date"] = pd.to_datetime(features["date"])
    features = features[features["date"] >= pd.Timestamp(start_date)]
    if end_date:
        features = features[features["date"] <= pd.Timestamp(end_date)]
    features = features.sort_values(["date", "ticker"]).reset_index(drop=True)

    prices = pd.read_parquet(PRICES_TRI_PATH)
    prices = prices[prices["ticker"].isin(tickers)].copy()
    prices["date"] = pd.to_datetime(prices["date"])
    price_lookup = prices.set_index(["date", "ticker"])["raw_close"]

    held: dict[str, dict] = {}
    cooldown_until: dict[str, pd.Timestamp] = {}
    entry_streak: dict[str, int] = {}
    records: list[dict[str, object]] = []

    for dt in sorted(features["date"].unique()):
        trade_date = pd.Timestamp(dt)
        day_data = features[features["date"] == dt]

        for _, row in day_data.iterrows():
            ticker = str(row["ticker"]).upper()
            permno = int(row["permno"]) if pd.notna(row.get("permno")) else None
            position_before = "HELD" if ticker in held else "FLAT"

            dist = _coerce_float(row.get("dist_sma20"))
            veto = bool(row.get("trend_veto", False))
            z_demand = _coerce_float(row.get("z_demand"))
            cap_cycle = _coerce_float(row.get("capital_cycle_score"))

            try:
                price = _nullable_float(price_lookup.get((trade_date, ticker)), ndigits=4)
            except (KeyError, TypeError):
                price = _nullable_float(row.get("adj_close"), ndigits=4)

            rule100 = build_rule100_state(row)
            factor_confirmed = rule100.confirmed
            factor_coverage = rule100.present_count
            factor_positives = rule100.positive_count
            rule100_state = rule100.to_record()
            raw_entry_gate = is_pit_eligible(z_demand, cap_cycle, dist, veto)
            is_eligible = raw_entry_gate and factor_confirmed
            hard_exit_signal = dist > HARD_EXIT_DIST_SMA20
            trim_signal = is_pit_trim(dist) and ticker in held
            raw_exit_gate = (hard_exit_signal or veto) and ticker in held

            if ticker in held and veto:
                held[ticker]["exit_streak"] = int(held[ticker].get("exit_streak", 0)) + 1
            elif ticker in held:
                held[ticker]["exit_streak"] = 0

            hold_days = None
            if ticker in held:
                hold_days = (trade_date - pd.Timestamp(held[ticker]["entry_date"])).days

            exit_streak_value = int(held.get(ticker, {}).get("exit_streak", 0))
            entry_confirmed = False
            exit_confirmed = False
            lifecycle_action = "NO_ACTION"
            buy_sell = None
            decision_action = "NO_ACTION"
            weight = 0.0
            target_weight = rule100_target_weight(rule100) if is_eligible else 0.0
            suggested_weight_delta = 0.0
            reason_codes: list[str]

            if raw_exit_gate:
                exit_confirmed = should_emit_exit(
                    entry_date=pd.Timestamp(held[ticker]["entry_date"]),
                    dt=trade_date,
                    dist_sma20=dist,
                    trend_veto=veto,
                    exit_streak=exit_streak_value,
                )
                if exit_confirmed:
                    lifecycle_action = "EXIT"
                    buy_sell = "SELL"
                    decision_action = "EXIT"
                    weight = 0.0
                    target_weight = 0.0
                    reason_codes = ["hard_stop"] if hard_exit_signal else ["confirmed_trend_veto"]
                    del held[ticker]
                    cooldown_until[ticker] = trade_date + pd.Timedelta(days=REENTRY_COOLDOWN_DAYS)
                    entry_streak[ticker] = 0
                else:
                    lifecycle_action = "HOLD"
                    decision_action = "HOLD"
                    weight = float(held[ticker].get("weight", 0.0))
                    target_weight = weight
                    if hold_days is not None and hold_days < MIN_HOLD_DAYS:
                        reason_codes = ["exit_pending_min_hold"]
                    elif exit_streak_value < EXIT_CONFIRM_DAYS:
                        reason_codes = ["exit_pending_confirmation"]
                    else:
                        reason_codes = ["exit_guard_blocked"]
            elif is_eligible and ticker not in held:
                entry_streak[ticker] = int(entry_streak.get(ticker, 0)) + 1
                entry_confirmed = entry_streak[ticker] >= ENTRY_CONFIRM_DAYS
                cooldown_blocked = is_reentry_blocked(trade_date, cooldown_until.get(ticker))
                if not entry_confirmed:
                    reason_codes = ["entry_confirmation_pending"]
                elif cooldown_blocked:
                    reason_codes = ["cooldown_blocked"]
                else:
                    lifecycle_action = "BUY"
                    buy_sell = "BUY"
                    decision_action = "BUY"
                    weight = target_weight
                    reason_codes = ["rule100_lifecycle_confirmed"]
                    held[ticker] = {"entry_date": str(trade_date.date()), "weight": weight, "exit_streak": 0}
                    entry_streak[ticker] = 0
            elif ticker in held:
                weight = float(held[ticker].get("weight", 0.0))
                target_weight = weight
                if trim_signal:
                    lifecycle_action = "TRIM"
                    decision_action = "TRIM"
                    suggested_weight_delta = TRIM_SUGGESTED_WEIGHT_DELTA
                    reason_codes = ["parabolic_trim_signal"]
                elif not rule100.hold_intact:
                    lifecycle_action = "TIGHTEN"
                    decision_action = "TIGHTEN"
                    suggested_weight_delta = TIGHTEN_SUGGESTED_WEIGHT_DELTA
                    reason_codes = ["rule100_factor_deterioration_tighten"]
                elif factor_positives >= MIN_FACTOR_POSITIVES:
                    lifecycle_action = "HOLD"
                    decision_action = "HOLD"
                    reason_codes = ["hold_factors_intact"]
                else:
                    lifecycle_action = "HOLD"
                    decision_action = "HOLD"
                    reason_codes = ["hold_one_factor_weak_tolerated"]
            else:
                entry_streak[ticker] = 0
                reason_codes = _entry_rejection_reasons(
                    z_demand=z_demand,
                    capital_cycle_score=cap_cycle,
                    dist_sma20=dist,
                    trend_veto=veto,
                    factor_confirmed=factor_confirmed,
                    factor_coverage=factor_coverage,
                    factor_positives=factor_positives,
                )

            cooldown_value = cooldown_until.get(ticker)
            record = {
                "date": str(trade_date.date()),
                "ticker": ticker,
                "permno": permno,
                "position_state_before": position_before,
                "position_state_after": "HELD" if ticker in held else "FLAT",
                "lifecycle_action": lifecycle_action,
                "buy_sell": buy_sell,
                "decision_action": decision_action,
                "primary_reason": reason_codes[0],
                "reason_codes": reason_codes,
                "weight": round(float(weight), 6),
                "target_weight": round(float(target_weight), 6),
                "suggested_weight_delta": round(float(suggested_weight_delta), 6),
                "price": price,
                "hold_days": int(hold_days) if hold_days is not None else None,
                "entry_streak": int(entry_streak.get(ticker, 0)),
                "exit_streak": exit_streak_value,
                "cooldown_until": str(cooldown_value.date()) if cooldown_value is not None else None,
                "reentry_blocked": is_reentry_blocked(trade_date, cooldown_value),
                "z_demand": _nullable_float(row.get("z_demand")),
                "capital_cycle_score": _nullable_float(row.get("capital_cycle_score")),
                "dist_sma20": _nullable_float(row.get("dist_sma20")),
                "trend_veto": veto,
                "raw_entry_gate": raw_entry_gate,
                "entry_confirmed": bool(entry_confirmed),
                "raw_exit_gate": raw_exit_gate,
                "hard_exit_signal": hard_exit_signal,
                "trim_signal": trim_signal,
                "exit_confirmed": bool(exit_confirmed),
            }
            record.update(rule100_state)
            records.append(record)

    decision_df = pd.DataFrame(records, columns=DECISION_LOG_COLUMNS)
    if output_path:
        _write_jsonl_frame(decision_df, output_path)
    if buy_sell_path:
        trades = decision_df[decision_df["buy_sell"].isin(["BUY", "SELL"])].copy()
        _write_jsonl_frame(trades, buy_sell_path)
    if audit_summary_path:
        _write_json_atomic(build_lifecycle_decision_audit(decision_df), audit_summary_path)
    return decision_df


def build_lifecycle_decision_audit(decision_df: pd.DataFrame) -> dict[str, object]:
    """Summarize good/bad replay behavior from an exported decision tape."""
    if decision_df.empty:
        return {
            "decision_rows": 0,
            "buy_sell_rows": 0,
            "date_range": None,
            "actions": {},
            "reason_counts": {},
            "current_open_holds": [],
            "does_well": [],
            "needs_audit": ["decision_tape_empty"],
        }

    df = decision_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    action_counts = {str(k): int(v) for k, v in df["decision_action"].value_counts().items()}
    buy_sell_counts = {
        str(k): int(v)
        for k, v in df["buy_sell"].dropna().value_counts().items()
    }

    reason_counts: dict[str, int] = {}
    for codes in df["reason_codes"]:
        if isinstance(codes, list):
            items = codes
        elif pd.isna(codes):
            items = []
        else:
            items = [str(codes)]
        for code in items:
            reason_counts[str(code)] = reason_counts.get(str(code), 0) + 1

    trades = df[df["buy_sell"].isin(["BUY", "SELL"])].sort_values(["date", "ticker"]).copy()
    open_positions: dict[str, dict[str, object]] = {}
    round_trips: list[dict[str, object]] = []
    unmatched_sells = 0
    for _, row in trades.iterrows():
        ticker = str(row["ticker"])
        if row["buy_sell"] == "BUY":
            open_positions[ticker] = {
                "ticker": ticker,
                "entry_date": str(pd.Timestamp(row["date"]).date()),
                "entry_price": _json_scalar(row.get("price")),
                "weight": _json_scalar(row.get("weight")),
                "primary_reason": _json_scalar(row.get("primary_reason")),
            }
            continue
        if row["buy_sell"] == "SELL":
            entry = open_positions.pop(ticker, None)
            if entry is None:
                unmatched_sells += 1
                continue
            hold_days = (pd.Timestamp(row["date"]) - pd.Timestamp(entry["entry_date"])).days
            round_trips.append(
                {
                    "ticker": ticker,
                    "entry_date": entry["entry_date"],
                    "exit_date": str(pd.Timestamp(row["date"]).date()),
                    "hold_days": int(hold_days),
                    "exit_reason": _json_scalar(row.get("primary_reason")),
                }
            )

    short_round_trips = [trip for trip in round_trips if int(trip["hold_days"]) <= 5]
    tighten_count = int(action_counts.get("TIGHTEN", 0))
    trim_count = int(action_counts.get("TRIM", 0))
    exit_pending = int(reason_counts.get("exit_pending_min_hold", 0)) + int(
        reason_counts.get("exit_pending_confirmation", 0)
    )
    entry_pending = int(reason_counts.get("entry_confirmation_pending", 0))

    does_well: list[str] = []
    needs_audit: list[str] = []
    if not short_round_trips:
        does_well.append("No <=5-day round trips in the exported buy/sell tape.")
    if open_positions:
        does_well.append("Replay is not sell-all; open holds remain after the latest exported date.")
    if buy_sell_counts.get("BUY", 0) and buy_sell_counts.get("SELL", 0):
        does_well.append("Both buy and sell decisions are explainable with explicit reason codes.")
    if tighten_count:
        needs_audit.append(f"{tighten_count} held ticker-days emit TIGHTEN for Rule-of-100 deterioration.")
    if trim_count:
        needs_audit.append(f"{trim_count} held ticker-days emit TRIM for stretch without changing v0 weight.")
    if exit_pending:
        needs_audit.append(f"{exit_pending} raw exit ticker-days were suppressed by min-hold/confirmation guards.")
    if entry_pending:
        needs_audit.append(f"{entry_pending} entry ticker-days were delayed by multi-day confirmation.")
    if unmatched_sells:
        needs_audit.append(f"{unmatched_sells} sell rows had no matching prior buy in the export window.")
    needs_audit.append(
        "Supply/pricing/margin are currently proxy-mapped from feature-store columns; literal Rule-of-100 columns are not yet present."
    )

    current_legacy_actions = {
        "BUY": int(buy_sell_counts.get("BUY", 0)),
        "SELL": int(buy_sell_counts.get("SELL", 0)),
        "HOLD": int(action_counts.get("HOLD", 0)),
        "NO_ACTION": int(action_counts.get("NO_ACTION", 0)),
        "TRIM": int(action_counts.get("TRIM", 0)),
        "TIGHTEN": int(action_counts.get("TIGHTEN", 0)),
        "EXIT": int(action_counts.get("EXIT", 0)),
    }
    baseline_deltas = {
        key: int(current_legacy_actions.get(key, 0) - BASELINE_DECISION_ACTIONS.get(key, 0))
        for key in BASELINE_DECISION_ACTIONS
    }

    return {
        "decision_rows": int(len(df)),
        "buy_sell_rows": int(len(trades)),
        "date_range": {
            "start": str(df["date"].min().date()),
            "end": str(df["date"].max().date()),
        },
        "tickers": sorted(str(ticker) for ticker in df["ticker"].dropna().unique()),
        "actions": action_counts,
        "buy_sell_actions": buy_sell_counts,
        "reason_counts": dict(sorted(reason_counts.items())),
        "current_open_holds": sorted(open_positions.values(), key=lambda item: str(item["ticker"])),
        "round_trips": round_trips,
        "short_round_trip_count": int(len(short_round_trips)),
        "unmatched_sell_count": int(unmatched_sells),
        "does_well": does_well,
        "needs_audit": needs_audit,
        "rule100_proxy_sources": RULE_OF_100_FACTOR_SOURCES,
        "baseline_comparison": {
            "baseline_name": "pre_rule100_v0_lifecycle_decision_audit_20260512",
            "baseline_actions": BASELINE_DECISION_ACTIONS,
            "current_legacy_actions": current_legacy_actions,
            "delta_vs_baseline": baseline_deltas,
            "baseline_open_holds": BASELINE_OPEN_HOLDS,
            "current_open_holds": sorted(open_positions),
            "trade_event_delta": int(len(trades) - (BASELINE_DECISION_ACTIONS["BUY"] + BASELINE_DECISION_ACTIONS["SELL"])),
            "short_round_trip_delta": int(len(short_round_trips)),
        },
    }


def diagnose_pinned_exclusions(
    start_date: str = "2025-01-02",
    end_date: str | None = None,
) -> pd.DataFrame:
    """Diagnose why pinned tickers were excluded from the replay.

    Returns DataFrame with columns: ticker, status, reason, detail
    Possible reasons: missing_price, insufficient_lookback, no_fundamentals, failed_gate
    """
    from data.universe.loader import resolve_pinned_universe

    pinned = resolve_pinned_universe()
    if not pinned:
        return pd.DataFrame(columns=["ticker", "status", "reason", "detail"])

    features = pd.read_parquet(FEATURES_PATH)
    features["date"] = pd.to_datetime(features["date"])
    features = features[features["date"] >= pd.Timestamp(start_date)]
    if end_date:
        features = features[features["date"] <= pd.Timestamp(end_date)]

    results = []
    for entry in pinned:
        ticker = entry.ticker
        if entry.status == "MISSING_MAP":
            results.append({"ticker": ticker, "status": "DATA_BLOCKED", "reason": "missing_map", "detail": "No permno in tickers.parquet"})
            continue

        sub = features[features["ticker"] == ticker]
        if sub.empty:
            results.append({"ticker": ticker, "status": "DATA_BLOCKED", "reason": "missing_price", "detail": "Not in features.parquet universe"})
            continue

        price_null = sub["adj_close"].isna().all()
        if price_null:
            results.append({"ticker": ticker, "status": "DATA_BLOCKED", "reason": "missing_price", "detail": "adj_close all NaN"})
            continue

        dist_null = sub["dist_sma20"].isna().all()
        if dist_null:
            results.append({"ticker": ticker, "status": "DATA_BLOCKED", "reason": "insufficient_lookback", "detail": "dist_sma20 all NaN (needs SMA20 warmup)"})
            continue

        fund_null = sub["z_demand"].isna().all() or sub["capital_cycle_score"].isna().all()
        if fund_null:
            results.append({"ticker": ticker, "status": "DATA_BLOCKED", "reason": "no_fundamentals", "detail": "z_demand or capital_cycle_score all NaN"})
            continue

        # Check if it ever passed the full replay gate.
        factor_stats = sub.apply(lifecycle_factor_confirmation, axis=1)
        factor_confirmed = factor_stats.apply(lambda value: bool(value[0]))
        factor_positives = factor_stats.apply(lambda value: int(value[2]))
        eligible_days = sub[
            sub.apply(
                lambda r: is_pit_eligible(
                    float(r.get("z_demand", 0) or 0),
                    float(r.get("capital_cycle_score", 0) or 0),
                    float(r.get("dist_sma20", 0) or 0),
                    bool(r.get("trend_veto", False)),
                ),
                axis=1,
            )
            & factor_confirmed
        ]
        if eligible_days.empty:
            z_dem_max = sub["z_demand"].max()
            cap_max = sub["capital_cycle_score"].max()
            dist_at_fund = sub[(sub["z_demand"] > 0) & (sub["capital_cycle_score"] > 0)]["dist_sma20"].min()
            factor_detail = f"factor_confirmed_days={int(factor_confirmed.sum())}, max_factor_positives={int(factor_positives.max()) if len(factor_positives) else 0}"
            detail = (
                f"z_demand_max={z_dem_max:.2f}, cap_cycle_max={cap_max:.2f}, "
                f"min_dist_when_fund_pass={dist_at_fund*100:.1f}%, {factor_detail}"
                if pd.notna(dist_at_fund)
                else f"z_demand_max={z_dem_max:.2f}, cap_cycle_max={cap_max:.2f}, fundamental gate never passed, {factor_detail}"
            )
            results.append({"ticker": ticker, "status": "FAILED_GATE", "reason": "failed_gate", "detail": detail})
        else:
            results.append({"ticker": ticker, "status": "OK", "reason": "eligible", "detail": f"{len(eligible_days)} eligible days"})

    return pd.DataFrame(results)


ELIGIBILITY_TRACE_COLUMNS = [
    "ticker",
    "pinned_thesis_universe",
    "permno",
    "ticker_map_status",
    "replay_dates",
    "pit_member_dates",
    "local_price_return_dates",
    "feature_dates",
    "rule100_history_dates",
    "eligible_feature_dates",
    "latest_replay_date",
    "latest_pit_member",
    "latest_local_price_return",
    "latest_rule100_history_present",
    "latest_sizing_eligible",
    "latest_current_hold_state",
    "latest_exclusion_gate",
    "latest_exclusion_detail",
]


def _read_trace_frame(path: Path | str | None, *, default_path: Path, kind: str | None = None) -> pd.DataFrame:
    trace_path = Path(path) if path is not None else default_path
    if not trace_path.exists():
        return pd.DataFrame()
    suffix = kind or trace_path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(trace_path)
    if suffix == ".jsonl":
        return pd.read_json(trace_path, lines=True)
    return pd.read_csv(trace_path)


def _date_filtered(frame: pd.DataFrame, *, start_date: str, end_date: str | None) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty or "date" not in frame.columns:
        return pd.DataFrame(columns=list(frame.columns) if isinstance(frame, pd.DataFrame) else [])
    out = frame.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    out = out[out["date"].notna()]
    out = out[out["date"] >= pd.Timestamp(start_date).normalize()]
    if end_date:
        out = out[out["date"] <= pd.Timestamp(end_date).normalize()]
    return out


def _valid_price_return_rows(prices: pd.DataFrame, permno: int | None) -> pd.DataFrame:
    if permno is None or prices.empty or "permno" not in prices.columns:
        return pd.DataFrame(columns=list(prices.columns) if isinstance(prices, pd.DataFrame) else [])
    out = prices[pd.to_numeric(prices["permno"], errors="coerce") == int(permno)].copy()
    if out.empty:
        return out
    price_col = "tri" if "tri" in out.columns else "adj_close" if "adj_close" in out.columns else "raw_close"
    price_valid = pd.to_numeric(out.get(price_col), errors="coerce").replace([float("inf"), float("-inf")], pd.NA)
    return_valid = (
        pd.to_numeric(out.get("total_ret"), errors="coerce").replace([float("inf"), float("-inf")], pd.NA)
        if "total_ret" in out.columns
        else pd.Series(0.0, index=out.index)
    )
    return out[(price_valid.notna()) & (price_valid > 0) & return_valid.notna()].copy()


def _trace_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _gate_from_entry_reasons(reasons: list[str]) -> tuple[str, str]:
    factor_reasons = {
        "demand_gate_failed",
        "capital_cycle_gate_failed",
        "factor_coverage_missing",
    }
    if any(reason in factor_reasons or reason.startswith("factor_confirmation_failed") for reason in reasons):
        return "factor threshold", ",".join(reasons)
    technical_reasons = {
        "technical_entry_zone_missing",
        "technical_entry_zone_failed",
        "trend_veto",
    }
    if any(reason in technical_reasons for reason in reasons):
        return "technical quality", ",".join(reasons)
    return "factor threshold", ",".join(reasons)


def trace_thesis_ticker_eligibility(
    tickers: list[str] | tuple[str, ...] = ("MU", "SNDK"),
    *,
    start_date: str = "2025-01-02",
    end_date: str | None = None,
    replay_dates: list[str] | tuple[str, ...] | None = None,
    manifest_path: Path | str | None = None,
    tickers_path: Path | str | None = None,
    universe_path: Path | str | None = None,
    prices_path: Path | str | None = None,
    features_path: Path | str | None = None,
    rule100_history_path: Path | str | None = None,
    decision_log_path: Path | str | None = None,
) -> pd.DataFrame:
    """Trace pinned thesis tickers through data, PIT, Rule100, and sizing gates.

    This diagnostic is intentionally separate from dashboard replay performance.
    It explains why named thesis tickers are or are not eligible without changing
    replay asset selection or using a watchlist-only replay universe.
    """
    from data.universe.loader import resolve_pinned_universe

    normalized_tickers = [str(ticker).upper().strip() for ticker in tickers if str(ticker).strip()]
    pinned = {
        entry.ticker: entry
        for entry in resolve_pinned_universe(manifest_path=manifest_path, tickers_path=tickers_path)
    }

    tickers_file = Path(tickers_path) if tickers_path is not None else Path("data/processed/tickers.parquet")
    ticker_map_frame = _read_trace_frame(tickers_file, default_path=tickers_file, kind=".parquet")
    ticker_to_permno = {}
    if not ticker_map_frame.empty and {"ticker", "permno"}.issubset(ticker_map_frame.columns):
        ticker_to_permno = {
            str(row["ticker"]).upper().strip(): int(row["permno"])
            for _, row in ticker_map_frame.dropna(subset=["ticker", "permno"]).iterrows()
        }

    universe = _date_filtered(
        _read_trace_frame(universe_path, default_path=Path("data/processed/universe_r3000_daily.parquet"), kind=".parquet"),
        start_date=start_date,
        end_date=end_date,
    )
    prices = _date_filtered(
        _read_trace_frame(prices_path, default_path=PRICES_TRI_PATH, kind=".parquet"),
        start_date=start_date,
        end_date=end_date,
    )
    features = _date_filtered(
        _read_trace_frame(features_path, default_path=FEATURES_PATH, kind=".parquet"),
        start_date=start_date,
        end_date=end_date,
    )
    history = _date_filtered(
        _read_trace_frame(rule100_history_path, default_path=Path("data/processed/rule100_softmax_v1_history.csv")),
        start_date=start_date,
        end_date=end_date,
    )
    decisions = _date_filtered(
        _read_trace_frame(decision_log_path, default_path=Path("data/portfolio_lifecycle_decision_log.jsonl"), kind=".jsonl"),
        start_date=start_date,
        end_date=end_date,
    )

    if replay_dates is not None:
        replay_index = pd.DatetimeIndex(pd.to_datetime(list(replay_dates), errors="coerce")).dropna().normalize().unique().sort_values()
    elif not features.empty:
        replay_index = pd.DatetimeIndex(features["date"].dropna()).normalize().unique().sort_values()
    elif not prices.empty:
        replay_index = pd.DatetimeIndex(prices["date"].dropna()).normalize().unique().sort_values()
    else:
        replay_index = pd.DatetimeIndex([])
    replay_date_set = {pd.Timestamp(value).normalize() for value in replay_index}
    latest_replay_date = pd.Timestamp(replay_index[-1]).normalize() if len(replay_index) else None

    records: list[dict[str, object]] = []
    for ticker in normalized_tickers:
        pinned_entry = pinned.get(ticker)
        permno = pinned_entry.permno if pinned_entry is not None and pinned_entry.permno is not None else ticker_to_permno.get(ticker)
        ticker_status = "OK" if permno is not None else "MISSING_MAP"

        ticker_features = features[features.get("ticker", pd.Series(dtype=object)).astype(str).str.upper().eq(ticker)].copy() if not features.empty else pd.DataFrame()
        ticker_history = history[history.get("ticker", pd.Series(dtype=object)).astype(str).str.upper().eq(ticker)].copy() if not history.empty else pd.DataFrame()
        ticker_decisions = decisions[decisions.get("ticker", pd.Series(dtype=object)).astype(str).str.upper().eq(ticker)].copy() if not decisions.empty else pd.DataFrame()
        ticker_prices = _valid_price_return_rows(prices, permno)

        pit_dates = pd.DatetimeIndex([])
        if permno is not None and not universe.empty and {"date", "permno"}.issubset(universe.columns):
            pit_rows = universe[pd.to_numeric(universe["permno"], errors="coerce") == int(permno)].copy()
            pit_dates = pd.DatetimeIndex(pit_rows["date"].dropna()).normalize().unique().sort_values()
        price_dates = pd.DatetimeIndex(ticker_prices["date"].dropna()).normalize().unique().sort_values() if not ticker_prices.empty else pd.DatetimeIndex([])
        feature_dates = pd.DatetimeIndex(ticker_features["date"].dropna()).normalize().unique().sort_values() if not ticker_features.empty else pd.DatetimeIndex([])
        history_dates = pd.DatetimeIndex(ticker_history["date"].dropna()).normalize().unique().sort_values() if not ticker_history.empty else pd.DatetimeIndex([])

        eligible_dates: list[pd.Timestamp] = []
        if not ticker_features.empty:
            for _, row in ticker_features.iterrows():
                state = build_rule100_state(row)
                z_demand = _coerce_float(row.get("z_demand"))
                cap_cycle = _coerce_float(row.get("capital_cycle_score"))
                dist = _coerce_float(row.get("dist_sma20"))
                trend_veto = _trace_bool(row.get("trend_veto"))
                if is_pit_eligible(z_demand, cap_cycle, dist, trend_veto) and state.confirmed:
                    eligible_dates.append(pd.Timestamp(row["date"]).normalize())

        latest_gate = "included"
        latest_detail = "ticker has eligible Rule100 history on latest replay date"
        latest_pit = latest_replay_date in set(pit_dates) if latest_replay_date is not None else False
        latest_price = latest_replay_date in set(price_dates) if latest_replay_date is not None else False
        latest_history = latest_replay_date in set(history_dates) if latest_replay_date is not None else False
        latest_sizing_eligible = False
        latest_hold_state = "UNKNOWN"

        if pinned_entry is None:
            latest_gate = "data unavailable"
            latest_detail = "ticker not present in pinned thesis universe"
        elif permno is None:
            latest_gate = "data unavailable"
            latest_detail = "ticker_map has no valid permno"
        elif latest_replay_date is None:
            latest_gate = "data unavailable"
            latest_detail = "no replay dates available in diagnostic window"
        elif not latest_pit:
            latest_gate = "PIT membership"
            latest_detail = "permno absent from r3000_pit on latest replay date"
        elif not latest_price:
            latest_gate = "data unavailable"
            latest_detail = "no local price/return row on latest replay date"
        else:
            latest_feature = ticker_features[ticker_features["date"] == latest_replay_date] if not ticker_features.empty else pd.DataFrame()
            latest_history_rows = ticker_history[ticker_history["date"] == latest_replay_date] if not ticker_history.empty else pd.DataFrame()
            latest_decision_rows = ticker_decisions[ticker_decisions["date"] == latest_replay_date] if not ticker_decisions.empty else pd.DataFrame()
            if not latest_decision_rows.empty and "position_state_after" in latest_decision_rows.columns:
                latest_hold_state = str(latest_decision_rows.iloc[-1].get("position_state_after", "UNKNOWN")).upper()
            elif latest_history:
                latest_hold_state = "HELD_OR_HISTORY_PRESENT"
            else:
                latest_hold_state = "FLAT_OR_NOT_IN_HISTORY"

            if latest_feature.empty:
                latest_gate = "data unavailable"
                latest_detail = "no feature row on latest replay date"
            else:
                feature_row = latest_feature.iloc[-1]
                state = build_rule100_state(feature_row)
                z_demand = _coerce_float(feature_row.get("z_demand"))
                cap_cycle = _coerce_float(feature_row.get("capital_cycle_score"))
                dist = _coerce_float(feature_row.get("dist_sma20"))
                trend_veto = _trace_bool(feature_row.get("trend_veto"))
                reasons = _entry_rejection_reasons(
                    z_demand=z_demand,
                    capital_cycle_score=cap_cycle,
                    dist_sma20=dist,
                    trend_veto=trend_veto,
                    factor_confirmed=state.confirmed,
                    factor_coverage=state.present_count,
                    factor_positives=state.positive_count,
                )
                if not (is_pit_eligible(z_demand, cap_cycle, dist, trend_veto) and state.confirmed):
                    latest_gate, latest_detail = _gate_from_entry_reasons(reasons)
                elif latest_history_rows.empty:
                    latest_gate = "current-hold state"
                    latest_detail = "entry gates pass but ticker is not present in Rule100 history/current-hold frame"
                else:
                    sizing_series = latest_history_rows.get("sizing_eligible", pd.Series(False, index=latest_history_rows.index))
                    latest_sizing_eligible = bool(sizing_series.astype(bool).any())
                    if not latest_sizing_eligible:
                        reason = str(latest_history_rows.iloc[-1].get("eligibility_reason", "not_sizing_eligible"))
                        latest_gate = "sizing eligibility"
                        latest_detail = reason

        records.append(
            {
                "ticker": ticker,
                "pinned_thesis_universe": pinned_entry is not None,
                "permno": permno,
                "ticker_map_status": ticker_status,
                "replay_dates": len(replay_date_set),
                "pit_member_dates": int(len(pit_dates)),
                "local_price_return_dates": int(len(price_dates)),
                "feature_dates": int(len(feature_dates)),
                "rule100_history_dates": int(len(history_dates)),
                "eligible_feature_dates": int(len(set(eligible_dates))),
                "latest_replay_date": None if latest_replay_date is None else latest_replay_date.date().isoformat(),
                "latest_pit_member": bool(latest_pit),
                "latest_local_price_return": bool(latest_price),
                "latest_rule100_history_present": bool(latest_history),
                "latest_sizing_eligible": bool(latest_sizing_eligible),
                "latest_current_hold_state": latest_hold_state,
                "latest_exclusion_gate": latest_gate,
                "latest_exclusion_detail": latest_detail,
            }
        )

    return pd.DataFrame(records, columns=ELIGIBILITY_TRACE_COLUMNS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PIT portfolio lifecycle replay.")
    parser.add_argument("--start-date", default="2025-01-02")
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--log-path", default=None)
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Export decision/audit logs without appending lifecycle ENTER/EXIT events.",
    )
    parser.add_argument("--decision-log-path", default=None)
    parser.add_argument("--buy-sell-log-path", default=None)
    parser.add_argument("--audit-summary-path", default=None)
    args = parser.parse_args()

    if args.export_only:
        stamp = pd.Timestamp.utcnow().strftime("%Y%m%d")
        decision_log_path = Path(args.decision_log_path or "data/portfolio_lifecycle_decision_log.jsonl")
        buy_sell_log_path = Path(args.buy_sell_log_path or "data/portfolio_lifecycle_buy_sell_log.jsonl")
        audit_summary_path = Path(
            args.audit_summary_path or f"docs/context/e2e_evidence/lifecycle_decision_audit_{stamp}.json"
        )
        decision_df = export_lifecycle_decision_log(
            start_date=args.start_date,
            end_date=args.end_date,
            output_path=decision_log_path,
            buy_sell_path=buy_sell_log_path,
            audit_summary_path=audit_summary_path,
        )
        audit = build_lifecycle_decision_audit(decision_df)
        print("Exported PIT lifecycle decision tape:")
        print(f"  Decision rows: {audit['decision_rows']}")
        print(f"  BUY/SELL rows: {audit['buy_sell_rows']}")
        print(f"  Open holds: {[row['ticker'] for row in audit['current_open_holds']]}")
        print(f"  Decision log: {decision_log_path}")
        print(f"  Buy/sell log: {buy_sell_log_path}")
        print(f"  Audit summary: {audit_summary_path}")
        return 0

    log_path = Path(args.log_path) if args.log_path else None
    print("Running point-in-time lifecycle replay...")
    df = run_pit_replay(start_date=args.start_date, end_date=args.end_date, log_path=log_path)
    print(f"Emitted {len(df)} events:")
    if not df.empty:
        print(f"  ENTER: {(df['action'] == 'ENTER').sum()}")
        print(f"  EXIT:  {(df['action'] == 'EXIT').sum()}")
        print(f"  Tickers: {sorted(df['ticker'].unique())}")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    output = log_path or Path("data/portfolio_lifecycle_log.jsonl")
    print(f"Done. Events written to {output}")

    if args.decision_log_path or args.buy_sell_log_path or args.audit_summary_path:
        decision_df = export_lifecycle_decision_log(
            start_date=args.start_date,
            end_date=args.end_date,
            output_path=Path(args.decision_log_path) if args.decision_log_path else None,
            buy_sell_path=Path(args.buy_sell_log_path) if args.buy_sell_log_path else None,
            audit_summary_path=Path(args.audit_summary_path) if args.audit_summary_path else None,
        )
        audit = build_lifecycle_decision_audit(decision_df)
        print(f"Decision tape rows: {audit['decision_rows']}; BUY/SELL rows: {audit['buy_sell_rows']}")

    print("\n--- Pinned Universe Diagnostics ---")
    diag = diagnose_pinned_exclusions()
    if not diag.empty:
        for _, row in diag.iterrows():
            status = "OK" if row["status"] == "OK" else "DATA_BLOCKED" if row["status"] == "DATA_BLOCKED" else "FAILED_GATE"
            print(f"  {status:12s} {row['ticker']:6s} | {row['reason']:20s} | {row['detail']}")
    else:
        print("  No pinned universe manifest found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
