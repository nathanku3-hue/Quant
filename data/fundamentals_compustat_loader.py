"""
Terminal Zero — Compustat Fundamentals Loader (Top 3000, PIT-safe)

Purpose
  - Ingest quarterly fundamentals from local WRDS/Compustat CSV.
  - Expand coverage for investable universe (Top 3000 liquid tickers only).
  - Merge with existing fundamentals.parquet using precedence:
      compustat_csv > yfinance on (permno, release_date).
  - Rebuild fundamentals_snapshot.parquet for scanner runtime.

Safety
  - Uses updater lock (.update.lock) to avoid concurrent writes.
  - Writes parquet atomically via temp file + os.replace.
  - Creates timestamped backups before overwrite.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import sys

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from data import updater  # noqa: E402
from data.fundamentals_updater import (  # noqa: E402
    MVQ_REVENUE_GROWTH_MIN,
    MVQ_ROIC_MIN,
    QUALITY_BYPASS_TICKERS,
    SCHEMA_COLUMNS,
    SNAPSHOT_COLUMNS,
)

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
TICKERS_PATH = os.path.join(PROCESSED_DIR, "tickers.parquet")
FUNDAMENTALS_PATH = os.path.join(PROCESSED_DIR, "fundamentals.parquet")
SNAPSHOT_PATH = os.path.join(PROCESSED_DIR, "fundamentals_snapshot.parquet")
BACKUP_DIR = os.path.join(PROCESSED_DIR, "backups")
DEFAULT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "e1o8zgcrz4nwbyif.csv")
MATCH_AUDIT_PATH = os.path.join(PROCESSED_DIR, "compustat_ticker_match_top3000.parquet")
UNMATCHED_AUDIT_PATH = os.path.join(PROCESSED_DIR, "compustat_unmatched_top3000.csv")

SOURCE_COMPUSTAT = "compustat_csv"
SOURCE_YAHOO = "yfinance"


def _log(msg: str):
    print(msg)


def _sql_escape_path(path: str) -> str:
    return path.replace("\\", "/").replace("'", "''")


def compute_institutional_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorized institutional factor construction.

    Requires columns:
      permno, fyearq, fqtr, revenue, oancfy, oibdpq, dlttq, dlcq, cheq, cshoq, prcraq, xrdq,
      net_income_q, equity_q, eps_basic_q, eps_diluted_q
    """
    if df.empty:
        return df

    out = df.copy()
    out = out.sort_values(["permno", "fyearq", "fqtr", "fiscal_period_end"]).reset_index(drop=True)

    for col in ("net_income_q", "equity_q", "eps_basic_q", "eps_diluted_q"):
        if col not in out.columns:
            out[col] = np.nan

    # Equity fallback: assets - liabilities when CEQQ/equity is missing.
    out["equity_q"] = pd.to_numeric(out["equity_q"], errors="coerce")
    out["atq"] = pd.to_numeric(out["atq"], errors="coerce")
    out["ltq"] = pd.to_numeric(out["ltq"], errors="coerce")
    out["equity_q"] = out["equity_q"].where(out["equity_q"].notna(), out["atq"] - out["ltq"])

    # 1) Cash flow de-cumulation (YTD -> quarterly)
    out["oancf_q"] = out["oancfy"]
    out["prev_oancfy"] = out.groupby(["permno", "fyearq"])["oancfy"].shift(1)
    mask_q234 = out["fqtr"].fillna(0) > 1
    out.loc[mask_q234, "oancf_q"] = out.loc[mask_q234, "oancfy"] - out.loc[mask_q234, "prev_oancfy"]
    # If quarter>1 but no previous YTD, mark invalid quarter flow as NaN.
    out.loc[mask_q234 & out["prev_oancfy"].isna(), "oancf_q"] = np.nan

    # 2) TTM constructions
    out["ebitda_ttm"] = (
        out.groupby("permno")["oibdpq"]
        .rolling(window=4, min_periods=4)
        .sum()
        .reset_index(level=0, drop=True)
    )
    out["oancf_ttm"] = (
        out.groupby("permno")["oancf_q"]
        .rolling(window=4, min_periods=4)
        .sum()
        .reset_index(level=0, drop=True)
    )
    out["revenue_ttm"] = (
        out.groupby("permno")["revenue"]
        .rolling(window=4, min_periods=4)
        .sum()
        .reset_index(level=0, drop=True)
    )
    out["xrd_ttm"] = (
        out.groupby("permno")["xrdq"]
        .rolling(window=4, min_periods=4)
        .sum()
        .reset_index(level=0, drop=True)
    )

    # 3) EV components
    out["mv_q"] = out["cshoq"] * out["prcraq"]
    out["total_debt"] = out["dlttq"].fillna(0.0) + out["dlcq"].fillna(0.0)
    out["net_debt"] = out["total_debt"] - out["cheq"].fillna(0.0)
    out["ev"] = out["mv_q"] + out["total_debt"] - out["cheq"].fillna(0.0)

    # 4) Ratios
    out["ev_ebitda"] = np.where(out["ebitda_ttm"] > 0, out["ev"] / out["ebitda_ttm"], np.nan)
    out["leverage_ratio"] = np.where(out["ebitda_ttm"] > 0, out["net_debt"] / out["ebitda_ttm"], np.nan)
    out["rd_intensity"] = np.where(out["revenue_ttm"] > 0, out["xrd_ttm"] / out["revenue_ttm"], np.nan)

    # Revenue YoY: (Revenue_q - Revenue_lag4) / Revenue_lag4
    out["revenue_lag4"] = out.groupby("permno")["revenue"].shift(4)
    out["revenue_growth_yoy"] = np.where(
        out["revenue_lag4"].notna() & (out["revenue_lag4"] != 0) & out["revenue"].notna(),
        (out["revenue"] - out["revenue_lag4"]) / out["revenue_lag4"],
        np.nan,
    )

    # Capital-cycle explicit factors.
    for col in (
        "operating_income_q",
        "total_revenue_q",
        "total_assets_q",
        "inventory_q",
        "capex_q",
        "gross_profit_q",
        "depreciation_q",
        "cogs_q",
        "receivables_q",
        "deferred_revenue_q",
    ):
        if col not in out.columns:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["cogs_q"] = out["cogs_q"].where(out["cogs_q"].notna(), out["total_revenue_q"] - out["gross_profit_q"])
    out["gross_profit_q"] = out["gross_profit_q"].where(out["gross_profit_q"].notna(), out["total_revenue_q"] - out["cogs_q"])
    out["operating_margin_q"] = np.where(
        out["total_revenue_q"] > 0,
        out["operating_income_q"] / out["total_revenue_q"],
        np.nan,
    )
    out["operating_margin_delta_q"] = out.groupby("permno")["operating_margin_q"].diff()
    out["gross_margin_q"] = np.where(
        out["total_revenue_q"] > 0,
        out["gross_profit_q"] / out["total_revenue_q"],
        np.nan,
    )
    out["gross_margin_delta_q"] = out.groupby("permno")["gross_margin_q"].diff()
    out["gm_accel_q"] = out.groupby("permno")["gross_margin_delta_q"].diff()
    out["capex_sales_q"] = np.where(
        out["total_revenue_q"] > 0,
        np.abs(out["capex_q"]) / out["total_revenue_q"],
    np.nan,
    )
    out["delta_capex_sales"] = out.groupby("permno")["capex_sales_q"].diff()
    out["delta_deferred_revenue_q"] = out.groupby("permno")["deferred_revenue_q"].diff()
    out["book_to_bill_proxy_q"] = np.where(
        (out["total_revenue_q"] > 0) & out["deferred_revenue_q"].notna(),
        (out["total_revenue_q"] + out["delta_deferred_revenue_q"].fillna(0.0)) / out["total_revenue_q"],
        np.nan,
    )
    out["dso_q"] = np.where(
        out["total_revenue_q"] > 0,
        (out["receivables_q"] / out["total_revenue_q"]) * 90.0,
        np.nan,
    )
    out["delta_dso_q"] = out.groupby("permno")["dso_q"].diff()
    out["gm_accel_q"] = out["gm_accel_q"].where(out["gm_accel_q"].notna(), out["operating_margin_delta_q"])
    out["revenue_inventory_q"] = np.where(
        out["inventory_q"] > 0,
        out["total_revenue_q"] / out["inventory_q"],
        np.nan,
    )
    out["delta_revenue_inventory"] = out.groupby("permno")["revenue_inventory_q"].diff()
    out["delta_dso_q"] = out["delta_dso_q"].where(out["delta_dso_q"].notna(), -out["delta_revenue_inventory"])
    out["sales_growth_q"] = out.groupby("permno")["total_revenue_q"].pct_change(fill_method=None)
    out["sales_accel_q"] = out.groupby("permno")["sales_growth_q"].diff()
    out["op_margin_accel_q"] = out.groupby("permno")["operating_margin_delta_q"].diff()
    out["asset_ex_inventory_q"] = out["total_assets_q"] - out["inventory_q"]
    out["log_asset_ex_inventory_q"] = np.log(out["asset_ex_inventory_q"].where(out["asset_ex_inventory_q"] > 0, np.nan))
    out["log_sales_q"] = np.log(out["total_revenue_q"].where(out["total_revenue_q"] > 0, np.nan))
    out["bloat_q"] = out.groupby("permno")["log_asset_ex_inventory_q"].diff() - out.groupby("permno")["log_sales_q"].diff()
    out["assets_lag1"] = out.groupby("permno")["total_assets_q"].shift(1)
    out["net_investment_q"] = (
        out["capex_q"].abs() - out["depreciation_q"]
    ) / out["assets_lag1"].replace(0.0, np.nan)
    out["asset_growth_yoy"] = out.groupby("permno")["total_assets_q"].pct_change(4, fill_method=None)

    # EPS/ROE metrics for first-principles selector layer.
    out["net_income_q"] = pd.to_numeric(out["net_income_q"], errors="coerce")
    out["cshoq"] = pd.to_numeric(out["cshoq"], errors="coerce")
    derived_eps = np.where(
        out["net_income_q"].notna() & out["cshoq"].notna() & (out["cshoq"] != 0),
        out["net_income_q"] / out["cshoq"],
        np.nan,
    )
    out["eps_basic_q"] = pd.to_numeric(out["eps_basic_q"], errors="coerce")
    out["eps_diluted_q"] = pd.to_numeric(out["eps_diluted_q"], errors="coerce")
    out["eps_basic_q"] = out["eps_basic_q"].where(out["eps_basic_q"].notna(), derived_eps)
    out["eps_diluted_q"] = out["eps_diluted_q"].where(out["eps_diluted_q"].notna(), out["eps_basic_q"])
    # Conservative priority: diluted EPS first, then basic.
    out["eps_q"] = out["eps_diluted_q"].where(out["eps_diluted_q"].notna(), out["eps_basic_q"])
    out["eps_ttm"] = (
        out.groupby("permno")["eps_q"]
        .rolling(window=4, min_periods=4)
        .sum()
        .reset_index(level=0, drop=True)
    )
    out["eps_lag4"] = out.groupby("permno")["eps_q"].shift(4)
    out["eps_growth_yoy"] = np.where(
        out["eps_lag4"].notna() & (out["eps_lag4"] != 0) & out["eps_q"].notna(),
        (out["eps_q"] - out["eps_lag4"]) / out["eps_lag4"],
        np.nan,
    )
    out["roe_q"] = np.where(
        out["equity_q"].notna() & (out["equity_q"] != 0) & out["net_income_q"].notna(),
        out["net_income_q"] / out["equity_q"],
        np.nan,
    )

    # ROIC proxy using operating income TTM over invested capital average.
    out["op_income_ttm"] = (
        out.groupby("permno")["operating_income"]
        .rolling(window=4, min_periods=4)
        .sum()
        .reset_index(level=0, drop=True)
    )
    out["invested_capital_avg"] = (
        out.groupby("permno")["invested_capital"]
        .rolling(window=4, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )
    out["roic"] = np.where(
        out["invested_capital_avg"] > 0,
        out["op_income_ttm"] / out["invested_capital_avg"],
        np.nan,
    )

    for col in (
        "sales_growth_q",
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
    ):
        out[col] = pd.to_numeric(out[col], errors="coerce").replace([np.inf, -np.inf], np.nan)

    drop_cols = [
        "prev_oancfy",
        "revenue_lag4",
        "eps_lag4",
        "op_income_ttm",
        "invested_capital_avg",
        "gross_margin_delta_q",
        "asset_ex_inventory_q",
        "log_asset_ex_inventory_q",
        "log_sales_q",
        "assets_lag1",
    ]
    out = out.drop(columns=[c for c in drop_cols if c in out.columns])
    return out


def _backup_if_exists(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d_%H%M%S")
    base = os.path.basename(path).replace(".parquet", "")
    backup_path = os.path.join(BACKUP_DIR, f"{base}.{stamp}.bak.parquet")
    shutil.copy2(path, backup_path)
    return backup_path


def _candidate_ticker_forms(raw_ticker: str) -> list[tuple[str, str]]:
    s = str(raw_ticker).upper().strip()
    if not s:
        return []

    candidates: list[tuple[str, str]] = [(s, "exact")]

    # Example: ADCT.1 -> ADCT
    no_numeric_suffix = re.sub(r"\.[0-9]+$", "", s)
    if no_numeric_suffix and no_numeric_suffix != s:
        candidates.append((no_numeric_suffix, "drop_numeric_suffix"))

    # Example: IDAI. -> IDAI
    no_trailing_dot = re.sub(r"\.$", "", s)
    if no_trailing_dot and no_trailing_dot != s:
        candidates.append((no_trailing_dot, "drop_trailing_dot"))

    # Example: BRK.B -> BRK-B
    dot_to_dash = s.replace(".", "-")
    if dot_to_dash != s:
        candidates.append((dot_to_dash, "dot_to_dash"))

    # Preserve order but dedupe values.
    uniq: list[tuple[str, str]] = []
    seen = set()
    for val, tag in candidates:
        if val not in seen:
            uniq.append((val, tag))
            seen.add(val)
    return uniq


def _load_top3000_map() -> pd.DataFrame:
    if not os.path.exists(TICKERS_PATH):
        raise FileNotFoundError(f"Missing ticker map: {TICKERS_PATH}")

    top_tickers = [str(t).upper().strip() for t in updater.get_top_liquid_tickers(3000)]
    top_tickers = list(dict.fromkeys([t for t in top_tickers if t]))

    tmap = pd.read_parquet(TICKERS_PATH)
    tmap["ticker"] = tmap["ticker"].astype(str).str.upper().str.strip()
    tmap["permno"] = pd.to_numeric(tmap["permno"], errors="coerce").astype("Int64")
    tmap = tmap.dropna(subset=["permno"])
    tmap["permno"] = tmap["permno"].astype(np.uint32)

    tmap = tmap[tmap["ticker"].isin(top_tickers)].copy()
    tmap = tmap.drop_duplicates(subset=["ticker"], keep="last")
    tmap = tmap.sort_values("ticker").reset_index(drop=True)

    if tmap.empty:
        raise RuntimeError("Top 3000 ticker map is empty. Ensure prices/tickers parquet are present.")
    return tmap


def _load_distinct_compustat_tickers(csv_path: str) -> list[str]:
    csv_sql = _sql_escape_path(csv_path)
    con = duckdb.connect()
    try:
        q = f"""
            SELECT DISTINCT UPPER(TRIM(tic)) AS raw_ticker
            FROM read_csv_auto('{csv_sql}', header=true, sample_size=-1, ignore_errors=true)
            WHERE tic IS NOT NULL
        """
        df = con.execute(q).df()
    finally:
        con.close()
    vals = [str(x).strip().upper() for x in df["raw_ticker"].tolist() if str(x).strip()]
    return list(dict.fromkeys(vals))


def _detect_csv_columns(csv_path: str) -> set[str]:
    csv_sql = _sql_escape_path(csv_path)
    con = duckdb.connect()
    try:
        q = f"""
            DESCRIBE SELECT * FROM read_csv_auto('{csv_sql}', header=true, sample_size=-1, ignore_errors=true)
        """
        info = con.execute(q).df()
    finally:
        con.close()
    if info.empty or "column_name" not in info.columns:
        return set()
    return {str(c).strip().lower() for c in info["column_name"].tolist() if str(c).strip()}


def _build_ticker_match_audit(csv_tickers: list[str], top_map: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    lookup = dict(zip(top_map["ticker"], top_map["permno"]))

    rows = []
    for raw in csv_tickers:
        for candidate, match_type in _candidate_ticker_forms(raw):
            permno = lookup.get(candidate)
            if permno is not None:
                rows.append(
                    {
                        "raw_ticker": raw,
                        "ticker": candidate,
                        "permno": np.uint32(permno),
                        "match_type": match_type,
                    }
                )
                break

    matched = pd.DataFrame(rows)
    if matched.empty:
        matched = pd.DataFrame(columns=["raw_ticker", "ticker", "permno", "match_type"])
    else:
        matched = matched.drop_duplicates(subset=["raw_ticker"], keep="first")

    matched_tickers = set(matched["ticker"]) if not matched.empty else set()
    unmatched_top = top_map[~top_map["ticker"].isin(matched_tickers)].copy()
    unmatched_top = unmatched_top.sort_values("ticker").reset_index(drop=True)
    unmatched_top["reason"] = "no_compustat_ticker_match"
    return matched, unmatched_top


def _extract_compustat_fundamentals(csv_path: str, ticker_match: pd.DataFrame) -> pd.DataFrame:
    if ticker_match.empty:
        return pd.DataFrame(columns=SCHEMA_COLUMNS)

    csv_sql = _sql_escape_path(csv_path)
    csv_cols = _detect_csv_columns(csv_path)

    def _opt_double(col: str, alias: str) -> str:
        if col.lower() in csv_cols:
            return f"CAST({col} AS DOUBLE) AS {alias}"
        return f"CAST(NULL AS DOUBLE) AS {alias}"

    def _opt_int(col: str, alias: str) -> str:
        if col.lower() in csv_cols:
            return f"CAST({col} AS INTEGER) AS {alias}"
        return f"CAST(NULL AS INTEGER) AS {alias}"

    if "oibdpq" in csv_cols and "niq" in csv_cols:
        operating_income_expr = "CAST(COALESCE(oibdpq, niq) AS DOUBLE) AS operating_income"
    elif "oibdpq" in csv_cols:
        operating_income_expr = "CAST(oibdpq AS DOUBLE) AS operating_income"
    elif "niq" in csv_cols:
        operating_income_expr = "CAST(niq AS DOUBLE) AS operating_income"
    else:
        operating_income_expr = "CAST(NULL AS DOUBLE) AS operating_income"

    ltq_expr = "CAST(ltq AS DOUBLE) AS ltq" if "ltq" in csv_cols else "CAST(lctq AS DOUBLE) AS ltq"
    if "capxy" in csv_cols and "capxq" in csv_cols:
        capex_expr = "CAST(COALESCE(capxq, capxy) AS DOUBLE) AS capex_q"
    elif "capxq" in csv_cols:
        capex_expr = "CAST(capxq AS DOUBLE) AS capex_q"
    elif "capxy" in csv_cols:
        capex_expr = "CAST(capxy AS DOUBLE) AS capex_q"
    else:
        capex_expr = "CAST(NULL AS DOUBLE) AS capex_q"

    if "dpq" in csv_cols and "dpy" in csv_cols:
        depreciation_expr = "CAST(COALESCE(dpq, dpy) AS DOUBLE) AS depreciation_q"
    elif "dpq" in csv_cols:
        depreciation_expr = "CAST(dpq AS DOUBLE) AS depreciation_q"
    elif "dpy" in csv_cols:
        depreciation_expr = "CAST(dpy AS DOUBLE) AS depreciation_q"
    else:
        depreciation_expr = "CAST(NULL AS DOUBLE) AS depreciation_q"

    if "gpq" in csv_cols:
        gross_profit_expr = "CAST(gpq AS DOUBLE) AS gross_profit_q"
    elif "revtq" in csv_cols and "cogsq" in csv_cols:
        gross_profit_expr = "CAST((revtq - cogsq) AS DOUBLE) AS gross_profit_q"
    else:
        gross_profit_expr = "CAST(NULL AS DOUBLE) AS gross_profit_q"
    if "cogsq" in csv_cols:
        cogs_expr = "CAST(cogsq AS DOUBLE) AS cogs_q"
    elif "revtq" in csv_cols and "gpq" in csv_cols:
        cogs_expr = "CAST((revtq - gpq) AS DOUBLE) AS cogs_q"
    else:
        cogs_expr = "CAST(NULL AS DOUBLE) AS cogs_q"
    receivables_expr = _opt_double("rectq", "receivables_q")
    if "drcq" in csv_cols and "drltq" in csv_cols:
        deferred_expr = "CAST(COALESCE(drcq, drltq) AS DOUBLE) AS deferred_revenue_q"
    elif "drcq" in csv_cols:
        deferred_expr = "CAST(drcq AS DOUBLE) AS deferred_revenue_q"
    elif "drltq" in csv_cols:
        deferred_expr = "CAST(drltq AS DOUBLE) AS deferred_revenue_q"
    elif "drq" in csv_cols:
        deferred_expr = "CAST(drq AS DOUBLE) AS deferred_revenue_q"
    else:
        deferred_expr = "CAST(NULL AS DOUBLE) AS deferred_revenue_q"

    con = duckdb.connect()
    try:
        con.register("ticker_match", ticker_match[["raw_ticker", "ticker", "permno"]])
        q = f"""
            WITH src AS (
                SELECT
                    UPPER(TRIM(tic)) AS raw_ticker,
                    CAST(datadate AS DATE) AS fiscal_period_end,
                    TRY_CAST(rdq AS DATE) AS rdq,
                    {_opt_int("fyearq", "fyearq")},
                    {_opt_int("fqtr", "fqtr")},
                    {_opt_double("revtq", "revenue")},
                    {operating_income_expr},
                    {_opt_double("invtq", "inventory_q")},
                    {capex_expr},
                    {depreciation_expr},
                    {gross_profit_expr},
                    {cogs_expr},
                    {receivables_expr},
                    {deferred_expr},
                    {_opt_double("oibdpq", "oibdpq")},
                    {_opt_double("niq", "net_income_q")},
                    {_opt_double("atq", "atq")},
                    -- Some exports do not include ltq; lctq is used as a conservative proxy.
                    {ltq_expr},
                    {_opt_double("ceqq", "equity_q")},
                    {_opt_double("dlcq", "dlcq")},
                    {_opt_double("dlttq", "dlttq")},
                    {_opt_double("cheq", "cheq")},
                    {_opt_double("cshoq", "cshoq")},
                    {_opt_double("prcraq", "prcraq")},
                    {_opt_double("xrdq", "xrdq")},
                    {_opt_double("oancfy", "oancfy")},
                    {_opt_double("epspxq", "eps_basic_q")},
                    {_opt_double("epsfxq", "eps_diluted_q")}
                FROM read_csv_auto('{csv_sql}', header=true, sample_size=-1, ignore_errors=true)
                WHERE tic IS NOT NULL
            ),
            mapped AS (
                SELECT
                    CAST(m.permno AS UBIGINT) AS permno,
                    m.ticker,
                    s.fiscal_period_end,
                    COALESCE(s.rdq, s.fiscal_period_end + INTERVAL 45 DAY) AS filing_date,
                    COALESCE(s.rdq, s.fiscal_period_end + INTERVAL 45 DAY) AS release_date,
                    COALESCE(s.rdq, s.fiscal_period_end + INTERVAL 45 DAY) AS published_at,
                    s.fyearq,
                    s.fqtr,
                    s.revenue,
                    s.operating_income,
                    s.revenue AS total_revenue_q,
                    s.operating_income AS operating_income_q,
                    s.atq AS total_assets_q,
                    s.inventory_q,
                    s.capex_q,
                    s.depreciation_q,
                    s.gross_profit_q,
                    s.cogs_q,
                    s.receivables_q,
                    s.deferred_revenue_q,
                    s.oibdpq,
                    s.net_income_q,
                    s.atq,
                    s.ltq,
                    s.equity_q,
                    s.dlcq,
                    s.dlttq,
                    s.cheq,
                    s.cshoq,
                    s.prcraq,
                    s.xrdq,
                    s.oancfy,
                    s.eps_basic_q,
                    s.eps_diluted_q
                FROM src s
                JOIN ticker_match m
                  ON s.raw_ticker = m.raw_ticker
                WHERE s.fiscal_period_end IS NOT NULL
            )
            SELECT * EXCLUDE (rn)
            FROM (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY permno, fiscal_period_end
                        ORDER BY release_date DESC
                    ) AS rn
                FROM mapped
            ) x
            WHERE rn = 1
        """
        out = con.execute(q).df()
    finally:
        con.close()

    if out.empty:
        return pd.DataFrame(columns=SCHEMA_COLUMNS)

    out["permno"] = pd.to_numeric(out["permno"], errors="coerce").astype("Int64")
    out = out.dropna(subset=["permno"])
    out["permno"] = out["permno"].astype(np.uint32)
    out["ticker"] = out["ticker"].astype(str).str.upper().str.strip()
    out["fiscal_period_end"] = pd.to_datetime(out["fiscal_period_end"], errors="coerce")
    out["filing_date"] = pd.to_datetime(out.get("filing_date"), errors="coerce")
    out["release_date"] = pd.to_datetime(out["release_date"], errors="coerce")
    out["published_at"] = pd.to_datetime(out.get("published_at"), errors="coerce")
    out = out.dropna(subset=["fiscal_period_end", "release_date"])
    # PIT clamp: earnings cannot be known before quarter close.
    # Enforce release_date >= fiscal_period_end + 1 day.
    out["release_date"] = (
        out[["release_date", "fiscal_period_end"]].max(axis=1) + pd.Timedelta(days=1)
    ).dt.normalize()
    out["filing_date"] = out["filing_date"].where(out["filing_date"].notna(), out["release_date"])
    out["published_at"] = out["published_at"].where(out["published_at"].notna(), out["filing_date"])
    out["published_at"] = out["published_at"].where(
        out["published_at"].notna(),
        out["fiscal_period_end"] + pd.Timedelta(days=90),
    )
    out["filing_date"] = pd.to_datetime(out["filing_date"], errors="coerce").dt.normalize()
    out["published_at"] = pd.to_datetime(out["published_at"], errors="coerce").dt.normalize()

    out["fyearq"] = pd.to_numeric(out["fyearq"], errors="coerce")
    out["fqtr"] = pd.to_numeric(out["fqtr"], errors="coerce")

    numeric_raw_cols = [
        "revenue",
        "operating_income",
        "total_revenue_q",
        "operating_income_q",
        "total_assets_q",
        "inventory_q",
        "capex_q",
        "depreciation_q",
        "gross_profit_q",
        "cogs_q",
        "receivables_q",
        "deferred_revenue_q",
        "oibdpq",
        "net_income_q",
        "atq",
        "ltq",
        "equity_q",
        "dlcq",
        "dlttq",
        "cheq",
        "cshoq",
        "prcraq",
        "xrdq",
        "oancfy",
        "eps_basic_q",
        "eps_diluted_q",
    ]
    for col in numeric_raw_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    # Invested capital proxy from quarterly balance sheet.
    out["invested_capital"] = (
        out["equity_q"] + out["dlttq"].fillna(0.0) + out["dlcq"].fillna(0.0) - out["cheq"].fillna(0.0)
    )
    out["invested_capital"] = out["invested_capital"].where(out["invested_capital"] > 0, np.nan)

    out = compute_institutional_factors(out)

    out["source"] = SOURCE_COMPUSTAT
    out["ingested_at"] = pd.Timestamp.utcnow().tz_localize(None)
    out["quality_pass_mvq"] = (
        out["roic"].gt(MVQ_ROIC_MIN) & out["revenue_growth_yoy"].gt(MVQ_REVENUE_GROWTH_MIN)
    )
    out["fyearq"] = pd.to_numeric(out["fyearq"], errors="coerce").astype("Int64")
    out["fqtr"] = pd.to_numeric(out["fqtr"], errors="coerce").astype("Int64")
    for col in [
        "revenue",
        "operating_income",
        "total_revenue_q",
        "operating_income_q",
        "total_assets_q",
        "inventory_q",
        "capex_q",
        "depreciation_q",
        "gross_profit_q",
        "cogs_q",
        "receivables_q",
        "deferred_revenue_q",
        "delta_deferred_revenue_q",
        "operating_margin_q",
        "operating_margin_delta_q",
        "gross_margin_q",
        "gm_accel_q",
        "capex_sales_q",
        "delta_capex_sales",
        "book_to_bill_proxy_q",
        "dso_q",
        "delta_dso_q",
        "revenue_inventory_q",
        "delta_revenue_inventory",
        "sales_growth_q",
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
        "asset_growth_yoy",
        "net_income_q",
        "equity_q",
        "eps_basic_q",
        "eps_diluted_q",
        "eps_q",
        "eps_ttm",
        "eps_growth_yoy",
        "roe_q",
        "invested_capital",
        "roic",
        "revenue_growth_yoy",
        "oibdpq",
        "atq",
        "ltq",
        "xrdq",
        "oancfy",
        "oancf_q",
        "oancf_ttm",
        "ebitda_ttm",
        "revenue_ttm",
        "xrd_ttm",
        "dlttq",
        "dlcq",
        "cheq",
        "cshoq",
        "prcraq",
        "mv_q",
        "total_debt",
        "net_debt",
        "ev",
        "ev_ebitda",
        "leverage_ratio",
        "rd_intensity",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float32")

    out = out[SCHEMA_COLUMNS]
    return out


def _ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in SCHEMA_COLUMNS:
        if c not in out.columns:
            out[c] = np.nan
    out = out[SCHEMA_COLUMNS]
    out["permno"] = pd.to_numeric(out["permno"], errors="coerce").astype("Int64")
    out = out.dropna(subset=["permno"])
    out["permno"] = out["permno"].astype(np.uint32)
    out["ticker"] = out["ticker"].astype(str).str.upper().str.strip()
    out["fiscal_period_end"] = pd.to_datetime(out["fiscal_period_end"], errors="coerce")
    out["filing_date"] = pd.to_datetime(out["filing_date"], errors="coerce")
    out["release_date"] = pd.to_datetime(out["release_date"], errors="coerce")
    out["published_at"] = pd.to_datetime(out["published_at"], errors="coerce")
    fallback_published = out["filing_date"].where(
        out["filing_date"].notna(),
        out["fiscal_period_end"] + pd.Timedelta(days=90),
    )
    out["published_at"] = out["published_at"].where(out["published_at"].notna(), fallback_published)
    out["ingested_at"] = pd.to_datetime(out["ingested_at"], errors="coerce")
    out["fyearq"] = pd.to_numeric(out["fyearq"], errors="coerce").astype("Int64")
    out["fqtr"] = pd.to_numeric(out["fqtr"], errors="coerce").astype("Int64")
    for c in [
        "revenue",
        "operating_income",
        "total_revenue_q",
        "operating_income_q",
        "total_assets_q",
        "inventory_q",
        "capex_q",
        "depreciation_q",
        "gross_profit_q",
        "cogs_q",
        "receivables_q",
        "deferred_revenue_q",
        "delta_deferred_revenue_q",
        "operating_margin_q",
        "operating_margin_delta_q",
        "gross_margin_q",
        "gm_accel_q",
        "capex_sales_q",
        "delta_capex_sales",
        "book_to_bill_proxy_q",
        "dso_q",
        "delta_dso_q",
        "revenue_inventory_q",
        "delta_revenue_inventory",
        "sales_growth_q",
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
        "asset_growth_yoy",
        "net_income_q",
        "equity_q",
        "eps_basic_q",
        "eps_diluted_q",
        "eps_q",
        "eps_ttm",
        "eps_growth_yoy",
        "roe_q",
        "invested_capital",
        "roic",
        "revenue_growth_yoy",
        "oibdpq",
        "atq",
        "ltq",
        "xrdq",
        "oancfy",
        "oancf_q",
        "oancf_ttm",
        "ebitda_ttm",
        "revenue_ttm",
        "xrd_ttm",
        "dlttq",
        "dlcq",
        "cheq",
        "cshoq",
        "prcraq",
        "mv_q",
        "total_debt",
        "net_debt",
        "ev",
        "ev_ebitda",
        "leverage_ratio",
        "rd_intensity",
    ]:
        out[c] = pd.to_numeric(out[c], errors="coerce").astype("float32")
    out["quality_pass_mvq"] = out["quality_pass_mvq"].fillna(False).astype(bool)
    out["source"] = out["source"].fillna(SOURCE_YAHOO).astype(str)
    out = out.dropna(subset=["release_date"])
    out["filing_date"] = pd.to_datetime(out["filing_date"], errors="coerce").dt.normalize()
    out["release_date"] = out["release_date"].dt.normalize()
    out["published_at"] = pd.to_datetime(out["published_at"], errors="coerce").dt.normalize()
    return out


def _merge_fundamentals(compustat_df: pd.DataFrame) -> pd.DataFrame:
    if os.path.exists(FUNDAMENTALS_PATH):
        existing = _ensure_schema(pd.read_parquet(FUNDAMENTALS_PATH))
    else:
        existing = pd.DataFrame(columns=SCHEMA_COLUMNS)

    new_rows = _ensure_schema(compustat_df)

    if existing.empty:
        merged = new_rows
    else:
        merged = pd.concat([existing, new_rows], ignore_index=True)

    source_priority = {SOURCE_YAHOO: 0, SOURCE_COMPUSTAT: 1}
    merged["_source_pri"] = merged["source"].map(source_priority).fillna(0).astype(int)
    merged = merged.sort_values(["permno", "release_date", "published_at", "_source_pri", "ingested_at"])
    merged = merged.drop_duplicates(subset=["permno", "release_date", "published_at"], keep="last")
    merged = merged.drop(columns=["_source_pri"]).sort_values(["permno", "release_date", "published_at"])
    merged = merged.reset_index(drop=True)
    return merged[SCHEMA_COLUMNS]


def _build_snapshot(full_df: pd.DataFrame) -> pd.DataFrame:
    if full_df is None or full_df.empty:
        return pd.DataFrame(columns=SNAPSHOT_COLUMNS)

    df = _ensure_schema(full_df)
    pit_cutoff = pd.Timestamp.utcnow().tz_localize(None).normalize()
    known = df[df["published_at"] <= pit_cutoff]
    if known.empty:
        known = df

    known = known.sort_values(["permno", "release_date", "published_at", "ingested_at"])
    latest = known.drop_duplicates(subset=["permno"], keep="last").copy()

    # Scanner hygiene: active listings only (zombie cull) and complete quality metrics.
    latest_date_threshold = pit_cutoff - pd.DateOffset(months=6)
    latest = latest[latest["release_date"] > latest_date_threshold]
    latest = latest.dropna(subset=["revenue_growth_yoy", "roic"])

    quality = latest["roic"].gt(MVQ_ROIC_MIN) & latest["revenue_growth_yoy"].gt(MVQ_REVENUE_GROWTH_MIN)
    latest["quality_pass"] = quality.fillna(False).astype("int8")
    latest.loc[latest["ticker"].isin(QUALITY_BYPASS_TICKERS), "quality_pass"] = 1

    snap = latest[SNAPSHOT_COLUMNS].copy()
    snap["published_at"] = pd.to_datetime(snap["published_at"], errors="coerce")
    snap["roic"] = pd.to_numeric(snap["roic"], errors="coerce").astype("float32")
    for c in (
        "operating_margin_q",
        "operating_margin_delta_q",
        "gross_margin_q",
        "gm_accel_q",
        "capex_sales_q",
        "delta_capex_sales",
        "book_to_bill_proxy_q",
        "dso_q",
        "delta_dso_q",
        "revenue_inventory_q",
        "delta_revenue_inventory",
        "sales_growth_q",
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
        "asset_growth_yoy",
    ):
        snap[c] = pd.to_numeric(snap[c], errors="coerce").astype("float32")
    snap["roe_q"] = pd.to_numeric(snap["roe_q"], errors="coerce").astype("float32")
    snap["eps_q"] = pd.to_numeric(snap["eps_q"], errors="coerce").astype("float32")
    snap["eps_ttm"] = pd.to_numeric(snap["eps_ttm"], errors="coerce").astype("float32")
    snap["eps_growth_yoy"] = pd.to_numeric(snap["eps_growth_yoy"], errors="coerce").astype("float32")
    snap["revenue_growth_yoy"] = pd.to_numeric(snap["revenue_growth_yoy"], errors="coerce").astype("float32")
    for c in ("ev_ebitda", "leverage_ratio", "rd_intensity", "oancf_ttm", "ebitda_ttm"):
        snap[c] = pd.to_numeric(snap[c], errors="coerce").astype("float32")
    snap["quality_pass"] = pd.to_numeric(snap["quality_pass"], errors="coerce").fillna(0).astype("int8")
    snap = snap.sort_values(["ticker", "permno"]).reset_index(drop=True)
    return snap


def run_ingestion(csv_path: str) -> dict:
    status = {
        "success": False,
        "top3000": 0,
        "matched_top3000": 0,
        "unmatched_top3000": 0,
        "new_rows": 0,
        "fundamentals_rows_before": 0,
        "fundamentals_rows_after": 0,
        "snapshot_rows_before": 0,
        "snapshot_rows_after": 0,
        "latest_release_date": None,
        "backup_fundamentals": None,
        "backup_snapshot": None,
    }

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Compustat CSV not found: {csv_path}")

    _log("=" * 72)
    _log("📚 Compustat Loader (Top 3000, Compustat > Yahoo precedence)")
    _log(f"📄 Source CSV: {csv_path}")
    _log("=" * 72)

    try:
        updater._acquire_update_lock()
    except TimeoutError:
        _log("✗ Another update is already running. Try again after it completes.")
        return status

    try:
        top_map = _load_top3000_map()
        status["top3000"] = int(len(top_map))
        _log(f"🎯 Top universe tickers: {status['top3000']:,}")

        csv_tickers = _load_distinct_compustat_tickers(csv_path)
        _log(f"🧾 Distinct Compustat tickers: {len(csv_tickers):,}")

        match_df, unmatched_top = _build_ticker_match_audit(csv_tickers, top_map)
        status["matched_top3000"] = int(match_df["ticker"].nunique()) if not match_df.empty else 0
        status["unmatched_top3000"] = int(len(unmatched_top))
        _log(
            f"🔗 Top3000 match coverage: {status['matched_top3000']:,}/{status['top3000']:,} "
            f"({(status['matched_top3000'] / max(status['top3000'], 1)) * 100:.2f}%)"
        )

        os.makedirs(PROCESSED_DIR, exist_ok=True)
        match_df.to_parquet(MATCH_AUDIT_PATH, index=False)
        unmatched_top.to_csv(UNMATCHED_AUDIT_PATH, index=False)
        _log(f"🗂️  Match audit: {MATCH_AUDIT_PATH}")
        _log(f"🗂️  Unmatched audit: {UNMATCHED_AUDIT_PATH}")

        comp_df = _extract_compustat_fundamentals(csv_path, match_df)
        status["new_rows"] = int(len(comp_df))
        _log(f"➕ Extracted Compustat rows: {status['new_rows']:,}")
        if comp_df.empty:
            raise RuntimeError("No Compustat fundamentals extracted for Top 3000 mapping.")

        if os.path.exists(FUNDAMENTALS_PATH):
            status["fundamentals_rows_before"] = int(len(pd.read_parquet(FUNDAMENTALS_PATH)))
        if os.path.exists(SNAPSHOT_PATH):
            status["snapshot_rows_before"] = int(len(pd.read_parquet(SNAPSHOT_PATH)))

        merged = _merge_fundamentals(comp_df)
        snapshot = _build_snapshot(merged)

        status["fundamentals_rows_after"] = int(len(merged))
        status["snapshot_rows_after"] = int(len(snapshot))
        latest_release = pd.to_datetime(merged["release_date"], errors="coerce").max()
        if pd.notna(latest_release):
            status["latest_release_date"] = str(pd.Timestamp(latest_release).date())

        status["backup_fundamentals"] = _backup_if_exists(FUNDAMENTALS_PATH)
        status["backup_snapshot"] = _backup_if_exists(SNAPSHOT_PATH)

        updater.atomic_parquet_write(merged, FUNDAMENTALS_PATH, index=False)
        updater.atomic_parquet_write(snapshot, SNAPSHOT_PATH, index=False)

        _log(f"💾 fundamentals.parquet: {status['fundamentals_rows_before']:,} -> {status['fundamentals_rows_after']:,}")
        _log(f"💾 fundamentals_snapshot.parquet: {status['snapshot_rows_before']:,} -> {status['snapshot_rows_after']:,}")
        _log(f"📅 Latest release date: {status['latest_release_date']}")
        if status["backup_fundamentals"]:
            _log(f"🛟 Backup fundamentals: {status['backup_fundamentals']}")
        if status["backup_snapshot"]:
            _log(f"🛟 Backup snapshot: {status['backup_snapshot']}")

        status["success"] = True
        _log("✅ Compustat ingestion complete.")
        return status
    finally:
        updater._release_update_lock()


def main():
    parser = argparse.ArgumentParser(description="Load Compustat CSV into fundamentals parquet (Top 3000)")
    parser.add_argument("--csv-path", default=DEFAULT_CSV_PATH, help="Path to Compustat CSV file")
    args = parser.parse_args()

    result = run_ingestion(csv_path=args.csv_path)
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
