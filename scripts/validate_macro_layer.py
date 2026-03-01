"""
Validate macro_features layer integrity for FR-035.
"""

from __future__ import annotations

import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from data import macro_loader  # noqa: E402

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
MACRO_FEATURES_PATH = os.path.join(PROCESSED_DIR, "macro_features.parquet")
MACRO_GATES_PATH = os.path.join(PROCESSED_DIR, "macro_gates.parquet")

REQUIRED_COLUMNS = {
    "date",
    "spy_close",
    "qqq_close",
    "vix_proxy",
    "vix_level",
    "vix3m_level",
    "vvix_level",
    "vix_vix3m_spread",
    "vix_term_ratio",
    "vix_backwardation",
    "liquidity_air_pocket",
    "qqq_peak_252d",
    "qqq_drawdown_252d",
    "qqq_drawdown_252d_z_adapt",
    "qqq_sma50",
    "qqq_ma200",
    "qqq_ma200_trend_gate",
    "qqq_ret_5d_z_adapt",
    "qqq_ret_21d_z_adapt",
    "slow_bleed_label",
    "sharp_shock_label",
    "dxy_spx_corr_20d",
    "dollar_squeeze",
    "sofr_effr_spread",
    "collateral_crisis",
    "hyg_lqd_ratio",
    "hyg_lqd_ratio_z63",
    "credit_freeze",
    "mtum_spy_corr_60d",
    "momentum_crowding",
    "month_end_rebalance_flag",
    "month_end_rebalance_direction",
    "stress_count",
    "regime_scalar",
}

REQUIRED_GATE_COLUMNS = {
    "date",
    "state",
    "scalar",
    "cash_buffer",
    "momentum_entry",
    "reasons",
    "qqq_drawdown_252d",
    "qqq_sma50",
    "qqq_ma200_trend_gate",
    "slow_bleed",
    "sharp_shock",
    "qqq_ret_5d_z_adapt",
    "qqq_ret_21d_z_adapt",
    "qqq_drawdown_252d_z_adapt",
    "vix_term_ratio",
    "vix_backwardation",
}


def _print(msg: str):
    print(msg)


def _fail(msg: str) -> int:
    _print(f"❌ {msg}")
    return 1


def validate() -> int:
    _print("🧪 Macro Layer Validation (FR-035)")
    _print("=" * 62)

    if not os.path.exists(MACRO_FEATURES_PATH):
        return _fail(f"Missing file: {MACRO_FEATURES_PATH}")

    df = pd.read_parquet(MACRO_FEATURES_PATH)
    if df.empty:
        return _fail("macro_features.parquet is empty.")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return _fail(f"Missing required columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if df["date"].duplicated().any():
        return _fail("Duplicate dates detected.")
    if not df["date"].is_monotonic_increasing:
        return _fail("Date sequence is not monotonic increasing.")

    # Trading-calendar coverage check.
    cal = macro_loader._load_trading_calendar(start_date=df["date"].min())
    expected = pd.DatetimeIndex(cal)
    # Compare on the validated artifact's own horizon.
    expected = expected[expected <= df["date"].max()]
    actual = pd.DatetimeIndex(df["date"])
    missing_days = expected.difference(actual)
    extra_days = actual.difference(expected)
    _print(f"✅ Calendar rows expected/actual: {len(expected):,} / {len(actual):,}")
    if len(missing_days) > 0:
        sample = ", ".join([d.strftime("%Y-%m-%d") for d in missing_days[:5]])
        return _fail(f"Missing trading days in macro layer: {len(missing_days):,} (e.g., {sample})")
    if len(extra_days) > 0:
        sample = ", ".join([d.strftime("%Y-%m-%d") for d in extra_days[:5]])
        return _fail(f"Non-trading dates present in macro layer: {len(extra_days):,} (e.g., {sample})")

    post_2020 = df[df["date"] >= pd.Timestamp("2020-01-01")]
    crit_cols = ["spy_close", "vix_proxy", "vix_level", "sofr_effr_spread", "hyg_lqd_ratio", "mtum_spy_corr_60d"]
    null_rates = post_2020[crit_cols].isna().mean() if not post_2020.empty else df[crit_cols].isna().mean()

    _print(f"✅ Rows: {len(df):,}")
    _print(f"✅ Date range: {df['date'].min().date()} -> {df['date'].max().date()}")
    _print("✅ Post-2020 null rates:")
    for k, v in null_rates.items():
        _print(f"   - {k}: {v:.2%}")

    mar2020 = df[(df["date"] >= "2020-03-01") & (df["date"] <= "2020-03-31")]
    if mar2020.empty:
        return _fail("No March 2020 rows available.")
    liq_hits = int(mar2020["liquidity_air_pocket"].fillna(False).sum())
    _print(f"✅ March 2020 liquidity_air_pocket hits: {liq_hits}")

    yr2022 = df[(df["date"] >= "2022-01-01") & (df["date"] <= "2022-12-31")]
    if yr2022.empty:
        return _fail("No 2022 rows available.")
    crowd_state = yr2022["momentum_crowding"].fillna(False).astype(int)
    crowd_flips = int(crowd_state.diff().abs().fillna(0).sum())
    _print(f"✅ 2022 momentum_crowding state flips: {crowd_flips}")

    if liq_hits <= 0:
        return _fail("Expected March 2020 liquidity_air_pocket triggers not found.")
    if crowd_flips <= 0:
        return _fail("Expected 2022 momentum_crowding regime changes not found.")

    high_null = null_rates[null_rates > 0.20]
    if not high_null.empty:
        return _fail("Critical post-2020 null rates exceed 20%: " + ", ".join(high_null.index.tolist()))

    if not os.path.exists(MACRO_GATES_PATH):
        return _fail(f"Missing file: {MACRO_GATES_PATH}")
    gates = pd.read_parquet(MACRO_GATES_PATH)
    if gates.empty:
        return _fail("macro_gates.parquet is empty.")

    gate_missing = REQUIRED_GATE_COLUMNS - set(gates.columns)
    if gate_missing:
        return _fail(f"Missing macro_gates required columns: {sorted(gate_missing)}")

    gates["date"] = pd.to_datetime(gates["date"], errors="coerce")
    gates = gates.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    gate_dates = pd.DatetimeIndex(gates["date"])
    if gate_dates.duplicated().any():
        return _fail("Duplicate dates detected in macro_gates.")

    missing_gate_days = actual.difference(gate_dates)
    extra_gate_days = gate_dates.difference(actual)
    if len(missing_gate_days) > 0:
        sample = ", ".join([d.strftime("%Y-%m-%d") for d in missing_gate_days[:5]])
        return _fail(f"Missing trading days in macro_gates: {len(missing_gate_days):,} (e.g., {sample})")
    if len(extra_gate_days) > 0:
        sample = ", ".join([d.strftime("%Y-%m-%d") for d in extra_gate_days[:5]])
        return _fail(f"Non-trading dates present in macro_gates: {len(extra_gate_days):,} (e.g., {sample})")

    valid_states = {"GREEN", "AMBER", "RED"}
    bad_states = sorted(set(gates["state"].dropna().astype(str).str.upper()) - valid_states)
    if bad_states:
        return _fail(f"Invalid macro_gates state values: {bad_states}")
    if not pd.to_numeric(gates["scalar"], errors="coerce").between(0.0, 1.0).fillna(False).all():
        return _fail("macro_gates.scalar must be within [0, 1].")
    if pd.to_numeric(gates["cash_buffer"], errors="coerce").isna().all():
        return _fail("macro_gates.cash_buffer is entirely null.")
    _print(f"✅ macro_gates rows: {len(gates):,}")

    _print("\n✅ MACRO LAYER: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
