from __future__ import annotations

import gc
import os
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from data import fundamentals as fundamentals_data


PROCESSED_DIR = "./data/processed"
STATIC_DIR = "./data/static"
SECTOR_MAP_PATH = f"{STATIC_DIR}/sector_map.parquet"
CALENDAR_PATH = f"{PROCESSED_DIR}/earnings_calendar.parquet"
MACRO_FEATURES_PATH = f"{PROCESSED_DIR}/macro_features.parquet"
MACRO_FEATURES_TRI_PATH = f"{PROCESSED_DIR}/macro_features_tri.parquet"
LIQUIDITY_FEATURES_PATH = f"{PROCESSED_DIR}/liquidity_features.parquet"
UNIVERSE_R3000_DAILY_PATH = f"{PROCESSED_DIR}/universe_r3000_daily.parquet"
PRICES_TRI_PATH = f"{PROCESSED_DIR}/prices_tri.parquet"


def _build_paths(*, processed_dir: str, static_dir: str) -> dict[str, str]:
    return {
        "sector_map_path": f"{static_dir}/sector_map.parquet",
        "calendar_path": f"{processed_dir}/earnings_calendar.parquet",
        "macro_features_path": f"{processed_dir}/macro_features.parquet",
        "macro_features_tri_path": f"{processed_dir}/macro_features_tri.parquet",
        "liquidity_features_path": f"{processed_dir}/liquidity_features.parquet",
        "universe_r3000_daily_path": f"{processed_dir}/universe_r3000_daily.parquet",
        "prices_tri_path": f"{processed_dir}/prices_tri.parquet",
        "prices_path": f"{processed_dir}/prices.parquet",
        "tickers_path": f"{processed_dir}/tickers.parquet",
        "patch_path": f"{processed_dir}/yahoo_patch.parquet",
        "legacy_macro_path": f"{processed_dir}/macro.parquet",
    }


def load_dashboard_data(
    top_n: int = 2000,
    start_year: int = 2000,
    universe_mode: str = "top_liquid",
    asof_date: Any = None,
    *,
    processed_dir: str = PROCESSED_DIR,
    static_dir: str = STATIC_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[int, str], dict[str, Any]]:
    """
    Load dashboard data with memory-safe batching and deterministic fallback behavior.
    """
    paths = _build_paths(processed_dir=processed_dir, static_dir=static_dir)
    con = duckdb.connect()
    temp_dir = os.path.join(processed_dir, "duckdb_tmp")
    os.makedirs(temp_dir, exist_ok=True)
    con.execute(f"PRAGMA temp_directory='{temp_dir.replace('\\', '/')}'")

    has_tri_prices = os.path.exists(paths["prices_tri_path"])
    signal_price_col = "tri" if has_tri_prices else "adj_close"

    # Legacy patch path only applies when tri prices are unavailable.
    has_patch = (not has_tri_prices) and os.path.exists(paths["patch_path"])

    if has_tri_prices:
        src = f"""(
            SELECT date, permno, total_ret, {signal_price_col} AS signal_price, volume
            FROM '{paths["prices_tri_path"]}'
        )"""
    elif has_patch:
        src = f"""(
            SELECT date, permno, total_ret, {signal_price_col} AS signal_price, volume
            FROM '{paths["prices_path"]}'
            UNION ALL
            SELECT date, permno, total_ret, {signal_price_col} AS signal_price, volume
            FROM '{paths["patch_path"]}'
        )"""
    else:
        src = f"""(
            SELECT date, permno, total_ret, {signal_price_col} AS signal_price, volume
            FROM '{paths["prices_path"]}'
        )"""

    if universe_mode == "r3000_pit":
        if not os.path.exists(paths["universe_r3000_daily_path"]):
            con.close()
            raise RuntimeError(
                "universe_mode='r3000_pit' requested but universe_r3000_daily.parquet is missing."
            )

        if asof_date is None:
            target_date = con.execute(
                f"SELECT MAX(CAST(date AS DATE)) AS d FROM '{paths['universe_r3000_daily_path']}'"
            ).df()["d"].iloc[0]
        else:
            asof = pd.to_datetime(asof_date, errors="coerce")
            if pd.isna(asof):
                con.close()
                raise ValueError(f"Invalid asof_date: {asof_date}")
            asof_str = asof.strftime("%Y-%m-%d")
            target_date = con.execute(
                f"""
                SELECT MAX(CAST(date AS DATE)) AS d
                FROM '{paths["universe_r3000_daily_path"]}'
                WHERE CAST(date AS DATE) <= DATE '{asof_str}'
                """
            ).df()["d"].iloc[0]

        if pd.isna(target_date):
            con.close()
            raise RuntimeError("No PIT universe date available for requested as-of date.")

        top_permnos = con.execute(
            f"""
            SELECT DISTINCT CAST(permno AS BIGINT) AS permno
            FROM '{paths["universe_r3000_daily_path"]}'
            WHERE CAST(date AS DATE) = DATE '{pd.Timestamp(target_date).strftime("%Y-%m-%d")}'
            """
        ).df()["permno"].tolist()
    else:
        universe_query = f"""
            SELECT permno
            FROM (
                SELECT permno, SUM(volume * signal_price) as total_dollar_vol
                FROM {src}
                WHERE date >= '{start_year}-01-01'
                GROUP BY permno
            )
            ORDER BY total_dollar_vol DESC
            LIMIT {int(top_n)}
        """
        top_permnos = con.execute(universe_query).df()["permno"].tolist()

    if has_patch:
        patch_permnos = con.execute(
            f"SELECT DISTINCT permno FROM '{paths['patch_path']}'"
        ).df()["permno"].tolist()
        all_permnos = sorted(set(top_permnos) | set(patch_permnos))
    else:
        all_permnos = sorted(set(top_permnos))

    if not all_permnos:
        con.close()
        raise RuntimeError("No assets found for selected universe.")

    batch_size = 200 if len(all_permnos) > 2500 else 250
    returns_parts: list[pd.DataFrame] = []
    prices_parts: list[pd.DataFrame] = []

    for i in range(0, len(all_permnos), batch_size):
        batch = all_permnos[i : i + batch_size]
        batch_list = ",".join([str(int(p)) for p in batch])

        if has_tri_prices:
            batch_query = f"""
                SELECT
                    CAST(date AS DATE) AS date,
                    CAST(permno AS BIGINT) AS permno,
                    CAST(total_ret AS DOUBLE) AS total_ret,
                    CAST({signal_price_col} AS DOUBLE) AS signal_price
                FROM '{paths["prices_tri_path"]}'
                WHERE permno IN ({batch_list})
                  AND date >= '{start_year}-01-01'
            """
        else:
            batch_query = f"""
                SELECT
                    CAST(date AS DATE) AS date,
                    CAST(permno AS BIGINT) AS permno,
                    arg_max(CAST(total_ret AS DOUBLE), priority) AS total_ret,
                    arg_max(CAST({signal_price_col} AS DOUBLE), priority) AS signal_price
                FROM (
                    SELECT date, permno, total_ret, {signal_price_col}, 0 AS priority
                    FROM '{paths["prices_path"]}'
                    WHERE permno IN ({batch_list})
                      AND date >= '{start_year}-01-01'
                    {"UNION ALL" if has_patch else ""}
                    {"SELECT date, permno, total_ret, " + signal_price_col + ", 1 AS priority" if has_patch else ""}
                    {"FROM '" + paths["patch_path"] + "'" if has_patch else ""}
                    {"WHERE permno IN (" + batch_list + ")" if has_patch else ""}
                    {"AND date >= '" + str(start_year) + "-01-01'" if has_patch else ""}
                )
                GROUP BY date, permno
            """
        batch_df = con.execute(batch_query).df()
        if batch_df.empty:
            continue

        batch_df["date"] = pd.to_datetime(batch_df["date"])
        ret_batch = batch_df.pivot(index="date", columns="permno", values="total_ret")
        px_batch = batch_df.pivot(index="date", columns="permno", values="signal_price")
        ret_batch.columns = pd.Index([int(c) for c in ret_batch.columns])
        px_batch.columns = pd.Index([int(c) for c in px_batch.columns])

        returns_parts.append(ret_batch.astype("float32", copy=False))
        prices_parts.append(px_batch.astype("float32", copy=False))

        del batch_df, ret_batch, px_batch
        gc.collect()

    if not returns_parts or not prices_parts:
        con.close()
        raise RuntimeError("No price data loaded for selected universe/date range.")

    returns_wide = pd.concat(returns_parts, axis=1).sort_index()
    prices_wide = pd.concat(prices_parts, axis=1).sort_index()
    returns_wide = returns_wide.reindex(columns=all_permnos).astype("float32", copy=False)
    prices_wide = prices_wide.reindex(columns=all_permnos).astype("float32", copy=False)
    del returns_parts, prices_parts
    gc.collect()

    if os.path.exists(paths["macro_features_tri_path"]):
        macro_path = paths["macro_features_tri_path"]
    elif os.path.exists(paths["macro_features_path"]):
        macro_path = paths["macro_features_path"]
    else:
        macro_path = paths["legacy_macro_path"]

    try:
        macro = pd.read_parquet(macro_path)
        macro["date"] = pd.to_datetime(macro["date"], errors="coerce")
        macro = macro.dropna(subset=["date"]).set_index("date").sort_index()
        macro = macro[macro.index >= pd.Timestamp(f"{start_year}-01-01")]
        if "spy_close" not in macro.columns and "spy_tri" in macro.columns:
            macro["spy_close"] = pd.to_numeric(macro["spy_tri"], errors="coerce")
    except Exception:
        macro = pd.DataFrame(index=prices_wide.index)

    try:
        if os.path.exists(paths["liquidity_features_path"]):
            liquidity = pd.read_parquet(paths["liquidity_features_path"])
            liquidity["date"] = pd.to_datetime(liquidity["date"], errors="coerce")
            liquidity = liquidity.dropna(subset=["date"]).set_index("date").sort_index()
            liquidity = liquidity[liquidity.index >= pd.Timestamp(f"{start_year}-01-01")]
            if not liquidity.empty:
                macro = macro.join(liquidity, how="outer").sort_index() if not macro.empty else liquidity
    except Exception:
        pass

    if macro.empty:
        proxy_spy = (
            prices_wide[84398].reindex(prices_wide.index).ffill()
            if 84398 in prices_wide.columns
            else prices_wide.ffill().iloc[:, 0]
        )
        macro = pd.DataFrame(
            {
                "spy_close": pd.to_numeric(proxy_spy, errors="coerce"),
                "vix_proxy": np.float32(30.0),
                "regime_scalar": np.float32(0.5),
            },
            index=prices_wide.index,
        )

    for col in ("spy_close", "vix_proxy", "regime_scalar"):
        if col in macro.columns:
            macro[col] = pd.to_numeric(macro[col], errors="coerce").astype("float32")
        else:
            macro[col] = np.nan

    for col in (
        "us_net_liquidity_mm",
        "liquidity_impulse",
        "repo_spread_bps",
        "lrp_index",
        "dollar_stress_corr",
        "smart_money_flow",
    ):
        if col in macro.columns:
            macro[col] = pd.to_numeric(macro[col], errors="coerce").astype("float32")

    for col in ("repo_stress", "global_dollar_stress"):
        if col in macro.columns:
            macro[col] = macro[col].fillna(False).astype(bool)

    ticker_df = con.execute(
        f"SELECT permno, ticker FROM '{paths['tickers_path']}'"
    ).df()
    ticker_map = {
        int(p): str(t)
        for p, t in zip(ticker_df["permno"], ticker_df["ticker"])
        if pd.notna(p)
    }

    fundamentals_wide = fundamentals_data.build_fundamentals_snapshot_context(
        prices_index=prices_wide.index,
        permnos=prices_wide.columns,
    )
    fundamentals_wide["ticker_map"] = {
        int(p): ticker_map.get(int(p), str(int(p))) for p in prices_wide.columns
    }

    sector_map_permno = {int(p): "Unknown" for p in prices_wide.columns}
    industry_map_permno = {int(p): "Unknown" for p in prices_wide.columns}
    if os.path.exists(paths["sector_map_path"]):
        try:
            sector_df = pd.read_parquet(paths["sector_map_path"])
            if not sector_df.empty:
                sector_df = sector_df.copy()
                for col in ("ticker", "sector", "industry"):
                    if col not in sector_df.columns:
                        sector_df[col] = "Unknown"
                sector_df["ticker"] = sector_df["ticker"].astype(str).str.upper().str.strip()
                sector_df["sector"] = sector_df["sector"].fillna("Unknown").astype(str)
                sector_df["industry"] = sector_df["industry"].fillna("Unknown").astype(str)
                if "permno" in sector_df.columns:
                    sector_df["permno"] = pd.to_numeric(
                        sector_df["permno"], errors="coerce"
                    ).astype("Int64")
                else:
                    sector_df["permno"] = pd.Series(pd.NA, index=sector_df.index, dtype="Int64")

                sort_cols = ["ticker"]
                if "updated_at" in sector_df.columns:
                    sector_df["updated_at"] = pd.to_datetime(
                        sector_df["updated_at"], errors="coerce"
                    )
                    sort_cols = ["ticker", "updated_at"]
                sector_df = sector_df.sort_values(sort_cols).drop_duplicates(
                    subset=["ticker"], keep="last"
                )

                sector_by_ticker = dict(zip(sector_df["ticker"], sector_df["sector"]))
                industry_by_ticker = dict(zip(sector_df["ticker"], sector_df["industry"]))
                sector_by_permno = {
                    int(p): s
                    for p, s in zip(sector_df["permno"], sector_df["sector"])
                    if pd.notna(p)
                }
                industry_by_permno = {
                    int(p): s
                    for p, s in zip(sector_df["permno"], sector_df["industry"])
                    if pd.notna(p)
                }

                for p in prices_wide.columns:
                    p_int = int(p)
                    ticker = str(ticker_map.get(p_int, "")).upper().strip()
                    sector = (
                        sector_by_ticker.get(ticker)
                        or sector_by_permno.get(p_int)
                        or "Unknown"
                    )
                    industry = (
                        industry_by_ticker.get(ticker)
                        or industry_by_permno.get(p_int)
                        or "Unknown"
                    )
                    if not str(sector).strip() or str(sector).lower() == "nan":
                        sector = "Unknown"
                    if not str(industry).strip() or str(industry).lower() == "nan":
                        industry = "Unknown"
                    sector_map_permno[p_int] = sector
                    industry_map_permno[p_int] = industry
        except Exception:
            pass

    fundamentals_wide["sector_map"] = sector_map_permno
    fundamentals_wide["industry_map"] = industry_map_permno
    latest_df = fundamentals_wide.get("latest")
    if isinstance(latest_df, pd.DataFrame) and not latest_df.empty:
        latest_df = latest_df.copy()
        latest_df["sector"] = [sector_map_permno.get(int(p), "Unknown") for p in latest_df.index]
        latest_df["industry"] = [industry_map_permno.get(int(p), "Unknown") for p in latest_df.index]
        fundamentals_wide["latest"] = latest_df

    cal_cols = ["ticker", "next_earnings_date", "last_earnings_date", "fetched_at", "source"]
    calendar_ctx = pd.DataFrame(
        index=pd.Index(prices_wide.columns, name="permno"),
        columns=cal_cols,
    )
    if os.path.exists(paths["calendar_path"]):
        try:
            cal = pd.read_parquet(paths["calendar_path"])
            if not cal.empty:
                for col in (
                    "permno",
                    "ticker",
                    "next_earnings_date",
                    "last_earnings_date",
                    "fetched_at",
                    "source",
                ):
                    if col not in cal.columns:
                        cal[col] = pd.NA
                cal["permno"] = pd.to_numeric(cal["permno"], errors="coerce").astype("Int64")
                cal = cal.dropna(subset=["permno"])
                cal["permno"] = cal["permno"].astype(int)
                cal["ticker"] = cal["ticker"].astype(str).str.upper().str.strip()
                cal["next_earnings_date"] = pd.to_datetime(cal["next_earnings_date"], errors="coerce")
                cal["last_earnings_date"] = pd.to_datetime(cal["last_earnings_date"], errors="coerce")
                cal["fetched_at"] = pd.to_datetime(cal["fetched_at"], errors="coerce")
                cal["source"] = cal["source"].fillna("yfinance").astype(str)
                cal = cal.sort_values(["permno", "fetched_at"]).drop_duplicates(
                    subset=["permno"], keep="last"
                )
                calendar_ctx = cal.set_index("permno")[cal_cols].reindex(prices_wide.columns)
        except Exception:
            pass

    fundamentals_wide["earnings_calendar"] = calendar_ctx

    con.close()
    return returns_wide, prices_wide, macro, ticker_map, fundamentals_wide
