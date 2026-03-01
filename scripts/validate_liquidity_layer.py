"""
Validate liquidity_features layer integrity for FR-040.
"""

from __future__ import annotations

import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from data import liquidity_loader  # noqa: E402

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
LIQUIDITY_PATH = os.path.join(PROCESSED_DIR, "liquidity_features.parquet")

REQUIRED_COLUMNS = {
    "date",
    "us_net_liquidity_mm",
    "liquidity_impulse",
    "repo_spread_bps",
    "repo_stress",
    "lrp_index",
    "dollar_stress_corr",
    "global_dollar_stress",
    "smart_money_flow",
    "realized_vol_21d",
    "vrp",
}


def _print(msg: str):
    print(msg)


def _fail(msg: str) -> int:
    _print(f"❌ {msg}")
    return 1


def validate() -> int:
    _print("🧪 Liquidity Layer Validation (FR-040)")
    _print("=" * 62)

    if not os.path.exists(LIQUIDITY_PATH):
        return _fail(f"Missing file: {LIQUIDITY_PATH}")

    df = pd.read_parquet(LIQUIDITY_PATH)
    if df.empty:
        return _fail("liquidity_features.parquet is empty.")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return _fail(f"Missing required columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if df["date"].duplicated().any():
        return _fail("Duplicate dates detected.")
    if not df["date"].is_monotonic_increasing:
        return _fail("Date sequence is not monotonic increasing.")

    try:
        cal = liquidity_loader._load_trading_calendar(
            start_date=df["date"].min(),
            end_date=df["date"].max(),
        )
    except Exception as e:
        return _fail(f"Failed to load trading calendar from price layers: {e}")
    expected = pd.DatetimeIndex(cal)
    expected = expected[expected <= df["date"].max()]
    actual = pd.DatetimeIndex(df["date"])
    missing_days = expected.difference(actual)
    extra_days = actual.difference(expected)
    _print(f"✅ Calendar rows expected/actual: {len(expected):,} / {len(actual):,}")
    if len(missing_days) > 0:
        sample = ", ".join([d.strftime("%Y-%m-%d") for d in missing_days[:5]])
        return _fail(f"Missing trading days: {len(missing_days):,} (e.g., {sample})")
    if len(extra_days) > 0:
        sample = ", ".join([d.strftime("%Y-%m-%d") for d in extra_days[:5]])
        return _fail(f"Non-trading days present: {len(extra_days):,} (e.g., {sample})")

    post_2020 = df[df["date"] >= pd.Timestamp("2020-01-01")]
    crit = [
        "us_net_liquidity_mm",
        "repo_spread_bps",
        "lrp_index",
        "dollar_stress_corr",
        "smart_money_flow",
        "realized_vol_21d",
        "vrp",
    ]
    null_rates = post_2020[crit].isna().mean() if not post_2020.empty else df[crit].isna().mean()
    _print("✅ Post-2020 null rates:")
    for c, v in null_rates.items():
        _print(f"   - {c}: {v:.2%}")
    if (null_rates > 0.10).any():
        bad = ", ".join([c for c in crit if null_rates[c] > 0.10])
        return _fail(f"Critical null rate above 10%: {bad}")

    # Sept 2019 repo stress sanity.
    sep2019 = df[(df["date"] >= "2019-09-01") & (df["date"] <= "2019-09-30")]
    if sep2019.empty:
        return _fail("No Sept 2019 rows to validate repo stress.")
    repo_peak = float(sep2019["repo_spread_bps"].max())
    _print(f"✅ Sept 2019 repo spread peak (bps): {repo_peak:.2f}")
    if repo_peak <= 10.0:
        return _fail("Expected Sept 2019 repo spread > 10 bps not found.")

    # 2022 liquidity impulse sanity: should show negative regime periods.
    yr2022 = df[(df["date"] >= "2022-01-01") & (df["date"] <= "2022-12-31")]
    if yr2022.empty:
        return _fail("No 2022 rows for liquidity impulse check.")
    impulse_2022 = yr2022["liquidity_impulse"].dropna()
    if impulse_2022.empty:
        return _fail("2022 liquidity impulse series is fully NaN.")
    neg_days = int((impulse_2022 < 0).sum())
    neg_ratio = float(neg_days / len(impulse_2022))
    impulse_min = float(impulse_2022.min())
    _print(
        "✅ 2022 liquidity impulse stats: "
        f"negative_days={neg_days}, negative_ratio={neg_ratio:.1%}, min={impulse_min:.2f}"
    )
    if neg_ratio < 0.40:
        return _fail("2022 negative liquidity impulse ratio is too low (<40%).")
    if impulse_min > -2.0:
        return _fail("2022 liquidity impulse lacks expected deep stress event (min > -2.0).")

    _print("\n✅ LIQUIDITY LAYER: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
