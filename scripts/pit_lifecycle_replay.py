"""Point-in-time forward replay of portfolio lifecycle events.

Walks forward through historical features.parquet data and detects
eligibility transitions using PIT-equivalent logic aligned with the live scanner:
- ENTER: z_demand > 0 AND capital_cycle_score > 0 AND dist_sma20 <= 5% AND no trend_veto
- EXIT: dist_sma20 > 12% OR trend_veto active on previously-eligible ticker

Ticker universe: SCANNER_TICKERS ∪ pinned_thesis_universe.yml (fail-closed).
This is a reconstruction from available data, not synthetic seeding.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from data.portfolio_lifecycle_log import append_lifecycle_event

FEATURES_PATH = Path("data/processed/features.parquet")
PRICES_TRI_PATH = Path("data/processed/prices_tri.parquet")

# Scanner-equivalent thresholds — aligned with live scanner logic:
#   Live Score == 100: demand > 0, supply >= 0, pricing > 0, margin > 0
#   PIT equivalent: z_demand > 0 AND capital_cycle_score > 0 (fundamental gate)
#   ENTER: fundamental gate AND dist_sma20 in entry zone AND no trend_veto
#   EXIT: dist_sma20 > parabolic threshold OR trend_veto on held position
PARABOLIC_DIST_SMA20 = 0.12   # 12% above SMA20 triggers EXIT
ACCUMULATION_DIST_MAX = 0.05  # within 5% of SMA20 is entry zone


def is_pit_eligible(z_demand: float, capital_cycle_score: float, dist_sma20: float, trend_veto: bool) -> bool:
    """Shared eligibility gate for PIT replay. Matches live scanner fundamental logic."""
    fundamental_pass = z_demand > 0 and capital_cycle_score > 0
    return fundamental_pass and dist_sma20 <= ACCUMULATION_DIST_MAX and not trend_veto


def is_pit_exit(dist_sma20: float, trend_veto: bool) -> bool:
    """Shared exit trigger for PIT replay."""
    return dist_sma20 > PARABOLIC_DIST_SMA20 or trend_veto
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
    held: dict[str, dict] = {}  # ticker -> {entry_date, weight}
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

            is_eligible = is_pit_eligible(z_demand, cap_cycle, dist, veto)
            is_exit = is_pit_exit(dist, veto) and ticker in held

            if is_exit:
                reason = "parabolic_stretch" if dist > PARABOLIC_DIST_SMA20 else "trend_veto"
                rating = f"EXIT / TRAIL TIGHT (dist_sma20={dist*100:.1f}%)" if dist > PARABOLIC_DIST_SMA20 else "EXIT (Trend Veto)"
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

            elif is_eligible and ticker not in held:
                # Equal-weight approximation for replay
                weight = round(1.0 / max(1, len(tickers)), 4)
                event = {
                    "ticker": ticker,
                    "action": "ENTER",
                    "date": str(dt.date()),
                    "weight": weight,
                    "rating": f"ENTER (demand={z_demand:.2f}, cycle={cap_cycle:.2f}, dist={dist*100:.1f}%)",
                    "reason": "pit_replay_eligible",
                    "price": price,
                    "permno": permno,
                }
                append_lifecycle_event(**event, path=log_path)
                events.append(event)
                held[ticker] = {"entry_date": str(dt.date()), "weight": weight}

    return pd.DataFrame(events) if events else pd.DataFrame(
        columns=["ticker", "action", "date", "weight", "rating", "reason", "price", "permno"]
    )


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

        # Check if it ever passed the gate
        eligible_days = sub[
            sub.apply(lambda r: is_pit_eligible(
                float(r.get("z_demand", 0) or 0),
                float(r.get("capital_cycle_score", 0) or 0),
                float(r.get("dist_sma20", 0) or 0),
                bool(r.get("trend_veto", False)),
            ), axis=1)
        ]
        if eligible_days.empty:
            z_dem_max = sub["z_demand"].max()
            cap_max = sub["capital_cycle_score"].max()
            dist_at_fund = sub[(sub["z_demand"] > 0) & (sub["capital_cycle_score"] > 0)]["dist_sma20"].min()
            detail = f"z_demand_max={z_dem_max:.2f}, cap_cycle_max={cap_max:.2f}, min_dist_when_fund_pass={dist_at_fund*100:.1f}%" if pd.notna(dist_at_fund) else f"z_demand_max={z_dem_max:.2f}, cap_cycle_max={cap_max:.2f}, fundamental gate never passed"
            results.append({"ticker": ticker, "status": "FAILED_GATE", "reason": "failed_gate", "detail": detail})
        else:
            results.append({"ticker": ticker, "status": "OK", "reason": "eligible", "detail": f"{len(eligible_days)} eligible days"})

    return pd.DataFrame(results)


if __name__ == "__main__":
    print("Running point-in-time lifecycle replay...")
    df = run_pit_replay()
    print(f"Emitted {len(df)} events:")
    if not df.empty:
        print(f"  ENTER: {(df['action'] == 'ENTER').sum()}")
        print(f"  EXIT:  {(df['action'] == 'EXIT').sum()}")
        print(f"  Tickers: {sorted(df['ticker'].unique())}")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print("Done. Events written to data/portfolio_lifecycle_log.jsonl")

    print("\n--- Pinned Universe Diagnostics ---")
    diag = diagnose_pinned_exclusions()
    if not diag.empty:
        for _, row in diag.iterrows():
            icon = "✅" if row["status"] == "OK" else "❌" if row["status"] == "DATA_BLOCKED" else "⚠️"
            print(f"  {icon} {row['ticker']:6s} | {row['status']:12s} | {row['reason']:20s} | {row['detail']}")
    else:
        print("  No pinned universe manifest found.")
