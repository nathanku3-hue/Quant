"""
Terminal Zero — JIT (Just-In-Time) Single Ticker Patcher [D-28]

Architecture: "Bedrock + Fresh Snow"
  Bedrock (2000-2024): WRDS, high-quality, static.
  Fresh Snow (2025-Now): Yahoo, on-demand, per-ticker.

When a user drills into a non-watchlist ticker, this module
fetches fresh data from Yahoo and patches it into the system.
"""
import os
import datetime

import streamlit as st
import numpy as np
import pandas as pd

from data import updater

PROCESSED_DIR = "./data/processed"
PATCH_PATH = os.path.join(PROCESSED_DIR, "yahoo_patch.parquet")
TICKERS_PATH = os.path.join(PROCESSED_DIR, "tickers.parquet")


def is_ticker_stale(prices_wide, permno) -> bool:
    """Check if a specific ticker's data is stale (older than 1 business day)."""
    if permno not in prices_wide.columns:
        return True
    series = prices_wide[permno].dropna()
    if series.empty:
        return True
    last = series.index.max()
    today = datetime.date.today()
    last_d = last.date() if hasattr(last, "date") else last
    gap = (today - last_d).days
    # Allow 3-day gap for weekends (Fri→Mon)
    return gap > 3


def jit_patch_ticker(ticker_name, permno, prices_wide):
    """
    JIT micro-update for a single ticker.
    Downloads fresh Yahoo data, merges into patch file, returns updated prices.
    """
    # Determine start date from existing data
    if permno in prices_wide.columns:
        series = prices_wide[permno].dropna()
        if not series.empty:
            last_date = series.index.max()
            start = (last_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            start = "2025-01-01"
    else:
        start = "2025-01-01"

    with st.spinner(f"⚡ Fetching live data for {ticker_name}..."):
        try:
            new_data = updater.batch_download_yahoo([ticker_name], start)
        except Exception as e:
            st.warning(f"Failed to fetch {ticker_name}: {e}")
            return prices_wide

    if new_data.empty:
        st.caption(f"ℹ️ No new data available for {ticker_name}.")
        return prices_wide

    # Map ticker → permno
    new_data["permno"] = np.uint32(permno)
    patch_rows = new_data[["date", "permno", "adj_close", "total_ret", "volume"]].copy()
    if "raw_close" in new_data.columns:
        patch_rows["raw_close"] = new_data["raw_close"]

    # Ensure required columns for patch schema
    for col in ["raw_close", "adj_close", "total_ret", "volume"]:
        if col not in patch_rows.columns:
            patch_rows[col] = 0.0

    patch_rows = patch_rows[["date", "permno", "raw_close", "adj_close", "total_ret", "volume"]]

    # Publish through updater facade (lock + atomic write).
    try:
        updater.publish_patch_rows(patch_rows)
    except TimeoutError:
        st.warning("Patch writer is busy. Please retry in a moment.")
        return prices_wide
    except OSError as e:
        st.warning(f"Failed to publish patch rows for {ticker_name}: {e}")
        return prices_wide

    # Patch in-memory prices_wide
    new_prices = patch_rows.set_index("date")[["adj_close"]].rename(columns={"adj_close": permno})
    if permno in prices_wide.columns:
        base_slice = prices_wide[[permno]]
    else:
        base_slice = pd.DataFrame(columns=[permno])
    updated = pd.concat([base_slice, new_prices])
    updated = updated[~updated.index.duplicated(keep="last")].sort_index()
    prices_wide[permno] = updated[permno]

    n_new = len(patch_rows)
    last_dt = patch_rows["date"].max().date()
    st.success(f"✅ Patched {ticker_name}: +{n_new} days → {last_dt}")

    return prices_wide
