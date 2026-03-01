"""
Terminal Zero — Fundamentals Updater [FR-027]

Phase 5 backend foundation:
  - Ingest sparse quarterly fundamentals from yfinance.
  - Align observations to release_date (Point-in-Time approximation).
  - Persist append-safe parquet for sparse-to-dense daily broadcasting.

Minimum Viable Quality (MVQ) factors:
  - ROIC > 0
  - Revenue Growth YoY > 0
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from typing import Any
from typing import Iterable

import numpy as np
import pandas as pd
import yfinance as yf

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from data import updater  # noqa: E402

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
TICKERS_PATH = os.path.join(PROCESSED_DIR, "tickers.parquet")
FUNDAMENTALS_PATH = os.path.join(PROCESSED_DIR, "fundamentals.parquet")
FUNDAMENTALS_SNAPSHOT_PATH = os.path.join(PROCESSED_DIR, "fundamentals_snapshot.parquet")
FUNDAMENTALS_INGEST_CHECKPOINT_META_PATH = os.path.join(PROCESSED_DIR, "fundamentals_ingest.checkpoint.json")
FUNDAMENTALS_INGEST_CHECKPOINT_ROWS_PATH = os.path.join(PROCESSED_DIR, "fundamentals_ingest.partial.parquet")
PHASE16_OPTIMIZER_LOCK_PATH = os.path.join(PROCESSED_DIR, "phase16_optimizer.lock")
PHASE16_REQUIRED_ARTIFACTS = [
    os.path.join(PROCESSED_DIR, "phase16_optimizer_results.csv"),
    os.path.join(PROCESSED_DIR, "phase16_best_params.json"),
    os.path.join(PROCESSED_DIR, "phase16_oos_summary.csv"),
]

# FR-027 thresholds
MVQ_ROIC_MIN = 0.0
MVQ_REVENUE_GROWTH_MIN = 0.0
QUALITY_BYPASS_TICKERS = {"SPY", "QQQ", "IWM", "DIA", "GLD", "TLT"}
CHECKPOINT_VERSION = 1
CHECKPOINT_STAGE_FETCH = "fetch"
CHECKPOINT_STAGE_MERGE = "merge"
CHECKPOINT_STAGE_FINAL_WRITE = "final_write"
CHECKPOINT_STAGE_DONE = "done"
CHECKPOINT_MISMATCH_FAIL = "fail"
CHECKPOINT_MISMATCH_RESET = "reset"

SCHEMA_COLUMNS = [
    "permno",
    "ticker",
    "fiscal_period_end",
    "release_date",
    "filing_date",
    "published_at",
    "fyearq",
    "fqtr",
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
    "quality_pass_mvq",
    "source",
    "ingested_at",
]
SNAPSHOT_COLUMNS = [
    "permno",
    "ticker",
    "release_date",
    "published_at",
    "roic",
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
    "roe_q",
    "eps_q",
    "eps_ttm",
    "eps_growth_yoy",
    "revenue_growth_yoy",
    "ev_ebitda",
    "leverage_ratio",
    "rd_intensity",
    "oancf_ttm",
    "ebitda_ttm",
    "quality_pass",
]


def _new_status() -> dict:
    return {
        "log": [],
        "success": False,
        "tickers_requested": 0,
        "tickers_with_data": 0,
        "rows_written": 0,
        "snapshot_rows": 0,
        "new_tickers": 0,
        "last_release_date": None,
    }


def _phase17_writer_gate() -> tuple[bool, str | None]:
    if os.path.exists(PHASE16_OPTIMIZER_LOCK_PATH):
        return (
            False,
            f"Phase 17 writer blocked: optimizer lock present at {PHASE16_OPTIMIZER_LOCK_PATH}.",
        )
    missing = [p for p in PHASE16_REQUIRED_ARTIFACTS if not os.path.exists(p)]
    if missing:
        return (
            False,
            "Phase 17 writer blocked: required Phase 16 artifacts missing: "
            + ", ".join(missing),
        )
    return True, None


def _log(status: dict, msg: str):
    print(msg)
    status["log"].append(msg)


def _normalize_tickers(values: Iterable[str]) -> list[str]:
    out = []
    for t in values:
        if not t:
            continue
        s = str(t).strip().upper()
        if s:
            out.append(s)
    return list(dict.fromkeys(out))


def _get_target_tickers(scope: str, custom_list: str | None) -> list[str]:
    if scope == "Custom" and custom_list:
        return _normalize_tickers(custom_list.split(","))

    n = 50
    if "3000" in scope:
        n = 3000
    elif "500" in scope:
        n = 500
    elif "200" in scope:
        n = 200
    elif "100" in scope:
        n = 100
    return _normalize_tickers(updater.get_top_liquid_tickers(n))


def _empty_series(index: pd.Index) -> pd.Series:
    return pd.Series(np.nan, index=index, dtype=float)


def _get_metric_row(df: pd.DataFrame, candidates: list[str], periods: pd.DatetimeIndex) -> pd.Series:
    if df is None or df.empty:
        return _empty_series(periods)

    for label in candidates:
        if label in df.index:
            s = pd.to_numeric(df.loc[label], errors="coerce")
            s = s.reindex(periods)
            return s.astype(float)
    return _empty_series(periods)


def _normalize_period_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    if df is None or df.empty:
        return pd.DataFrame(), pd.DatetimeIndex([])

    out = df.copy()
    out.columns = pd.to_datetime(out.columns, errors="coerce")
    out = out.loc[:, ~out.columns.isna()]
    if out.empty:
        return pd.DataFrame(), pd.DatetimeIndex([])

    out = out.sort_index(axis=1)
    # If duplicate period columns exist, keep the right-most one.
    out = out.loc[:, ~out.columns.duplicated(keep="last")]
    periods = pd.DatetimeIndex(out.columns)
    if periods.tz is not None:
        periods = periods.tz_convert(None)
        out.columns = periods

    return out, periods


def _infer_release_dates(ticker_obj: yf.Ticker, fiscal_periods: pd.DatetimeIndex) -> pd.Series:
    """
    Infer release_date from earnings calendar.
    Fallback: fiscal_period_end + 45 days.
    """
    if len(fiscal_periods) == 0:
        return pd.Series([], dtype="datetime64[ns]")

    fallback = pd.Series(
        [p + pd.Timedelta(days=45) for p in fiscal_periods],
        index=fiscal_periods,
        dtype="datetime64[ns]",
    )

    try:
        earnings = ticker_obj.get_earnings_dates(limit=max(32, len(fiscal_periods) * 4))
    except Exception:
        earnings = pd.DataFrame()

    if earnings is None or earnings.empty:
        return fallback

    edates = pd.DatetimeIndex(pd.to_datetime(earnings.index, errors="coerce"))
    edates = edates[~edates.isna()]
    if len(edates) == 0:
        return fallback
    if edates.tz is not None:
        edates = edates.tz_convert(None)
    edates = edates.sort_values().normalize().unique()

    chosen: list[pd.Timestamp] = []
    for i, fiscal_end in enumerate(fiscal_periods):
        cands = [d for d in edates if d >= fiscal_end and d <= fiscal_end + pd.Timedelta(days=120)]
        release = cands[0] if cands else fallback.iloc[i]
        if chosen and release <= chosen[-1]:
            release = chosen[-1] + pd.Timedelta(days=1)
        chosen.append(pd.Timestamp(release).normalize())

    return pd.Series(chosen, index=fiscal_periods, dtype="datetime64[ns]")


def _extract_ticker_fundamentals(ticker: str, permno: int) -> pd.DataFrame:
    """
    Fetch one ticker from yfinance and emit sparse PIT quarterly rows.
    """
    tk = yf.Ticker(ticker)
    statements = updater.fetch_quarterly_fundamental_frames(ticker, ticker_obj=tk)
    income, periods = _normalize_period_columns(statements.get("income", pd.DataFrame()))
    if income.empty or len(periods) == 0:
        return pd.DataFrame(columns=SCHEMA_COLUMNS)

    balance, _ = _normalize_period_columns(statements.get("balance", pd.DataFrame()))
    cashflow, _ = _normalize_period_columns(statements.get("cashflow", pd.DataFrame()))

    revenue_q = _get_metric_row(income, ["Total Revenue", "Revenue"], periods)
    oibdpq = _get_metric_row(
        income,
        [
            "EBITDA",
            "Normalized EBITDA",
            "Operating Income",
            "Operating Income Loss",
            "EBIT",
            "Net Income",
            "Net Income Common Stockholders",
        ],
        periods,
    )
    # Prefer common-share earnings when available (exclude preferred impact).
    net_income_q = _get_metric_row(
        income,
        [
            "Net Income Common Stockholders",
            "Net Income Common Stock",
            "Net Income Applicable To Common Shares",
            "Net Income",
        ],
        periods,
    )
    op_income_q = _get_metric_row(
        income,
        [
            "Operating Income",
            "Operating Income Loss",
            "EBIT",
            "Net Income",
            "Net Income Common Stockholders",
        ],
        periods,
    )
    gross_profit_q = _get_metric_row(
        income,
        [
            "Gross Profit",
            "Gross Profit Income",
        ],
        periods,
    )
    cogs_q = _get_metric_row(
        income,
        [
            "Cost Of Revenue",
            "Cost Of Goods Sold",
            "Cost Of Goods And Services Sold",
            "Cost Of Goods Sold Excluding D&A",
        ],
        periods,
    )
    oancfy = _get_metric_row(
        cashflow,
        [
            "Operating Cash Flow",
            "Cash Flow From Continuing Operating Activities",
            "Net Cash Provided By Operating Activities",
        ],
        periods,
    )
    capex_q = _get_metric_row(
        cashflow,
        [
            "Capital Expenditure",
            "Capital Expenditures",
            "Purchase Of PPE",
            "Payments To Acquire Property Plant And Equipment",
        ],
        periods,
    )
    depreciation_q = _get_metric_row(
        cashflow,
        [
            "Depreciation And Amortization",
            "Depreciation",
            "Depreciation Amortization Depletion",
            "DepreciationAndAmortization",
        ],
        periods,
    )

    atq = _get_metric_row(balance, ["Total Assets"], periods)
    inventory_q = _get_metric_row(
        balance,
        [
            "Inventory",
            "Inventories",
            "Finished Goods",
        ],
        periods,
    )
    receivables_q = _get_metric_row(
        balance,
        [
            "Accounts Receivable",
            "Accounts Receivable Trade",
            "Net Receivables",
            "Receivables",
            "Trade And Other Receivables Current",
        ],
        periods,
    )
    deferred_revenue_q = _get_metric_row(
        balance,
        [
            "Deferred Revenue Current",
            "Current Deferred Revenue",
            "Deferred Revenue",
            "Contract With Customer Liability Current",
        ],
        periods,
    )
    ltq = _get_metric_row(
        balance,
        [
            "Total Liabilities Net Minority Interest",
            "Total Liabilities",
        ],
        periods,
    )
    xrdq = _get_metric_row(
        income,
        [
            "Research And Development",
            "Research Development",
        ],
        periods,
    )
    equity_primary_q = _get_metric_row(
        balance,
        [
            "Stockholders Equity",
            "Total Equity Gross Minority Interest",
            "Common Stock Equity",
        ],
        periods,
    )
    cshoq = _get_metric_row(
        balance,
        [
            "Share Issued",
            "Ordinary Shares Number",
        ],
        periods,
    )
    shares_basic_avg = _get_metric_row(
        income,
        [
            "Basic Average Shares",
            "Basic Average Shares And Assumed Conversions",
            "Basic Shares",
        ],
        periods,
    )
    shares_diluted_avg = _get_metric_row(
        income,
        [
            "Diluted Average Shares",
            "Diluted Average Shares And Assumed Conversions",
            "Diluted Shares",
        ],
        periods,
    )
    eps_basic_q = _get_metric_row(
        income,
        [
            "Basic EPS",
            "Basic EPS Continuing Operations",
            "EPS Basic",
        ],
        periods,
    )
    eps_diluted_q = _get_metric_row(
        income,
        [
            "Diluted EPS",
            "Diluted EPS Continuing Operations",
            "EPS Diluted",
        ],
        periods,
    )
    prcraq = pd.Series(np.nan, index=periods, dtype=float)
    debt_q = _get_metric_row(
        balance,
        [
            "Total Debt",
            "Long Term Debt",
            "Current Debt And Capital Lease Obligation",
        ],
        periods,
    ).fillna(0.0)
    dlttq = _get_metric_row(
        balance,
        [
            "Long Term Debt",
        ],
        periods,
    )
    dlcq = _get_metric_row(
        balance,
        [
            "Current Debt And Capital Lease Obligation",
            "Current Debt",
        ],
        periods,
    )
    cash_q = _get_metric_row(
        balance,
        [
            "Cash Cash Equivalents And Short Term Investments",
            "Cash And Cash Equivalents",
            "Cash And Cash Equivalents, At Carrying Value",
        ],
        periods,
    ).fillna(0.0)
    cheq = cash_q.copy()

    # Equity fallback: assets - liabilities when stockholders equity is missing.
    equity_fallback_q = atq - ltq
    equity_q = equity_primary_q.where(equity_primary_q.notna(), equity_fallback_q)

    shares_basic_for_eps = shares_basic_avg.where(shares_basic_avg.notna(), cshoq)
    shares_diluted_for_eps = (
        shares_diluted_avg.where(shares_diluted_avg.notna(), shares_basic_for_eps).where(lambda s: s.notna(), cshoq)
    )
    derived_eps_basic_q = net_income_q / shares_basic_for_eps.replace(0, np.nan)
    derived_eps_diluted_q = net_income_q / shares_diluted_for_eps.replace(0, np.nan)
    eps_basic_q = eps_basic_q.where(eps_basic_q.notna(), derived_eps_basic_q)
    eps_diluted_q = eps_diluted_q.where(eps_diluted_q.notna(), derived_eps_diluted_q)
    # Conservative priority: diluted EPS first, then basic EPS.
    eps_q = eps_diluted_q.where(eps_diluted_q.notna(), eps_basic_q)

    invested_capital_q = (equity_q + debt_q - cash_q).where(lambda s: s > 0)

    eps_ttm = eps_q.rolling(4, min_periods=4).sum()
    eps_growth_yoy = eps_ttm.pct_change(4, fill_method=None)
    if eps_growth_yoy.notna().sum() == 0:
        eps_growth_yoy = eps_q.pct_change(4, fill_method=None)
    roe_q = net_income_q / equity_q.replace(0, np.nan)

    revenue_ttm = revenue_q.rolling(4, min_periods=4).sum()
    xrd_ttm = xrdq.rolling(4, min_periods=4).sum()
    op_income_ttm = op_income_q.rolling(4, min_periods=4).sum()
    ebitda_ttm = oibdpq.rolling(4, min_periods=4).sum()
    oancf_q = oancfy.copy()
    oancf_ttm = oancf_q.rolling(4, min_periods=4).sum()
    invested_capital_avg = invested_capital_q.rolling(4, min_periods=1).mean()

    roic = op_income_ttm / invested_capital_avg.replace(0, np.nan)
    revenue_growth_yoy = revenue_ttm.pct_change(4, fill_method=None)
    if revenue_growth_yoy.notna().sum() == 0:
        # Fallback when history is too short for TTM YoY.
        revenue_growth_yoy = revenue_q.pct_change(4, fill_method=None)
    # Keep gross profit and COGS internally consistent even when one side is missing.
    cogs_q = cogs_q.where(cogs_q.notna(), revenue_q - gross_profit_q)
    gross_profit_q = gross_profit_q.where(gross_profit_q.notna(), revenue_q - cogs_q)
    total_revenue_q = revenue_q
    operating_income_q = op_income_q
    total_assets_q = atq
    operating_margin_q = pd.Series(
        np.where(revenue_q > 0, operating_income_q / revenue_q, np.nan),
        index=periods,
    )
    operating_margin_delta_q = operating_margin_q.diff()
    gross_margin_q = pd.Series(
        np.where(revenue_q > 0, gross_profit_q / revenue_q, np.nan),
        index=periods,
    )
    gross_margin_delta_q = gross_margin_q.diff()
    gm_accel_q = gross_margin_delta_q.diff()
    capex_sales_q = pd.Series(
        np.where(revenue_q > 0, capex_q.abs() / revenue_q, np.nan),
        index=periods,
    )
    delta_capex_sales = capex_sales_q.diff()
    delta_deferred_revenue_q = deferred_revenue_q.diff()
    book_to_bill_proxy_q = pd.Series(
        np.where(
            (revenue_q > 0) & deferred_revenue_q.notna(),
            (revenue_q + delta_deferred_revenue_q.fillna(0.0)) / revenue_q,
            np.nan,
        ),
        index=periods,
    )
    dso_q = pd.Series(
        np.where(revenue_q > 0, (receivables_q / revenue_q) * 90.0, np.nan),
        index=periods,
    )
    delta_dso_q = dso_q.diff()
    gm_accel_q = gm_accel_q.where(gm_accel_q.notna(), operating_margin_delta_q)
    revenue_inventory_q = pd.Series(
        np.where(inventory_q > 0, revenue_q / inventory_q, np.nan),
        index=periods,
    )
    delta_revenue_inventory = revenue_inventory_q.diff()
    delta_dso_q = delta_dso_q.where(delta_dso_q.notna(), -delta_revenue_inventory)
    sales_growth_q = revenue_q.pct_change(fill_method=None)
    sales_accel_q = sales_growth_q.diff()
    op_margin_accel_q = operating_margin_delta_q.diff()
    asset_ex_inventory_q = total_assets_q - inventory_q
    log_asset_ex_inventory_q = np.log(asset_ex_inventory_q.where(asset_ex_inventory_q > 0, np.nan))
    log_sales_q = np.log(total_revenue_q.where(total_revenue_q > 0, np.nan))
    bloat_q = log_asset_ex_inventory_q.diff() - log_sales_q.diff()
    assets_lag1 = total_assets_q.shift(1)
    net_investment_q = (capex_q.abs() - depreciation_q) / assets_lag1.replace(0.0, np.nan)
    asset_growth_yoy = atq.pct_change(4, fill_method=None)
    mv_q = cshoq * prcraq
    total_debt = dlttq.fillna(0.0) + dlcq.fillna(0.0)
    net_debt = total_debt - cheq.fillna(0.0)
    ev = mv_q + total_debt - cheq.fillna(0.0)
    ev_ebitda = pd.Series(np.where(ebitda_ttm > 0, ev / ebitda_ttm, np.nan), index=periods)
    leverage_ratio = pd.Series(np.where(ebitda_ttm > 0, net_debt / ebitda_ttm, np.nan), index=periods)
    rd_intensity = pd.Series(np.where(revenue_ttm > 0, xrd_ttm / revenue_ttm, np.nan), index=periods)

    roic = roic.replace([np.inf, -np.inf], np.nan)
    revenue_growth_yoy = revenue_growth_yoy.replace([np.inf, -np.inf], np.nan)
    operating_margin_q = operating_margin_q.replace([np.inf, -np.inf], np.nan)
    operating_margin_delta_q = operating_margin_delta_q.replace([np.inf, -np.inf], np.nan)
    gross_margin_q = gross_margin_q.replace([np.inf, -np.inf], np.nan)
    gm_accel_q = gm_accel_q.replace([np.inf, -np.inf], np.nan)
    capex_sales_q = capex_sales_q.replace([np.inf, -np.inf], np.nan)
    delta_capex_sales = delta_capex_sales.replace([np.inf, -np.inf], np.nan)
    delta_deferred_revenue_q = delta_deferred_revenue_q.replace([np.inf, -np.inf], np.nan)
    book_to_bill_proxy_q = book_to_bill_proxy_q.replace([np.inf, -np.inf], np.nan)
    dso_q = dso_q.replace([np.inf, -np.inf], np.nan)
    delta_dso_q = delta_dso_q.replace([np.inf, -np.inf], np.nan)
    revenue_inventory_q = revenue_inventory_q.replace([np.inf, -np.inf], np.nan)
    delta_revenue_inventory = delta_revenue_inventory.replace([np.inf, -np.inf], np.nan)
    sales_growth_q = sales_growth_q.replace([np.inf, -np.inf], np.nan)
    sales_accel_q = sales_accel_q.replace([np.inf, -np.inf], np.nan)
    op_margin_accel_q = op_margin_accel_q.replace([np.inf, -np.inf], np.nan)
    bloat_q = bloat_q.replace([np.inf, -np.inf], np.nan)
    net_investment_q = net_investment_q.replace([np.inf, -np.inf], np.nan)
    asset_growth_yoy = asset_growth_yoy.replace([np.inf, -np.inf], np.nan)
    cogs_q = cogs_q.replace([np.inf, -np.inf], np.nan)
    receivables_q = receivables_q.replace([np.inf, -np.inf], np.nan)
    deferred_revenue_q = deferred_revenue_q.replace([np.inf, -np.inf], np.nan)
    depreciation_q = depreciation_q.replace([np.inf, -np.inf], np.nan)
    eps_basic_q = eps_basic_q.replace([np.inf, -np.inf], np.nan)
    eps_diluted_q = eps_diluted_q.replace([np.inf, -np.inf], np.nan)
    eps_q = eps_q.replace([np.inf, -np.inf], np.nan)
    eps_ttm = eps_ttm.replace([np.inf, -np.inf], np.nan)
    eps_growth_yoy = eps_growth_yoy.replace([np.inf, -np.inf], np.nan)
    roe_q = roe_q.replace([np.inf, -np.inf], np.nan)
    ev_ebitda = ev_ebitda.replace([np.inf, -np.inf], np.nan)
    leverage_ratio = leverage_ratio.replace([np.inf, -np.inf], np.nan)
    rd_intensity = rd_intensity.replace([np.inf, -np.inf], np.nan)

    release_dates = _infer_release_dates(tk, periods)
    filing_dates = pd.to_datetime(release_dates, errors="coerce")
    published_at = filing_dates.where(filing_dates.notna(), periods + pd.Timedelta(days=90))
    ingested_at = pd.Timestamp.utcnow().tz_localize(None)
    fyearq = periods.year
    fqtr = periods.quarter

    out = pd.DataFrame(
        {
            "permno": np.uint32(permno),
            "ticker": ticker,
            "fiscal_period_end": periods,
            "release_date": release_dates.values,
            "filing_date": filing_dates.values,
            "published_at": published_at.values,
            "fyearq": fyearq,
            "fqtr": fqtr,
            "revenue": revenue_q.values,
            "operating_income": op_income_q.values,
            "total_revenue_q": total_revenue_q.values,
            "operating_income_q": operating_income_q.values,
            "total_assets_q": total_assets_q.values,
            "inventory_q": inventory_q.values,
            "capex_q": capex_q.values,
            "depreciation_q": depreciation_q.values,
            "gross_profit_q": gross_profit_q.values,
            "cogs_q": cogs_q.values,
            "receivables_q": receivables_q.values,
            "deferred_revenue_q": deferred_revenue_q.values,
            "delta_deferred_revenue_q": delta_deferred_revenue_q.values,
            "operating_margin_q": operating_margin_q.values,
            "operating_margin_delta_q": operating_margin_delta_q.values,
            "gross_margin_q": gross_margin_q.values,
            "gm_accel_q": gm_accel_q.values,
            "capex_sales_q": capex_sales_q.values,
            "delta_capex_sales": delta_capex_sales.values,
            "book_to_bill_proxy_q": book_to_bill_proxy_q.values,
            "dso_q": dso_q.values,
            "delta_dso_q": delta_dso_q.values,
            "revenue_inventory_q": revenue_inventory_q.values,
            "delta_revenue_inventory": delta_revenue_inventory.values,
            "sales_growth_q": sales_growth_q.values,
            "sales_accel_q": sales_accel_q.values,
            "op_margin_accel_q": op_margin_accel_q.values,
            "bloat_q": bloat_q.values,
            "net_investment_q": net_investment_q.values,
            "asset_growth_yoy": asset_growth_yoy.values,
            "net_income_q": net_income_q.values,
            "equity_q": equity_q.values,
            "eps_basic_q": eps_basic_q.values,
            "eps_diluted_q": eps_diluted_q.values,
            "eps_q": eps_q.values,
            "eps_ttm": eps_ttm.values,
            "eps_growth_yoy": eps_growth_yoy.values,
            "roe_q": roe_q.values,
            "invested_capital": invested_capital_q.values,
            "roic": roic.values,
            "revenue_growth_yoy": revenue_growth_yoy.values,
            "oibdpq": oibdpq.values,
            "atq": atq.values,
            "ltq": ltq.values,
            "xrdq": xrdq.values,
            "oancfy": oancfy.values,
            "oancf_q": oancf_q.values,
            "oancf_ttm": oancf_ttm.values,
            "ebitda_ttm": ebitda_ttm.values,
            "revenue_ttm": revenue_ttm.values,
            "xrd_ttm": xrd_ttm.values,
            "dlttq": dlttq.values,
            "dlcq": dlcq.values,
            "cheq": cheq.values,
            "cshoq": cshoq.values,
            "prcraq": prcraq.values,
            "mv_q": mv_q.values,
            "total_debt": total_debt.values,
            "net_debt": net_debt.values,
            "ev": ev.values,
            "ev_ebitda": ev_ebitda.values,
            "leverage_ratio": leverage_ratio.values,
            "rd_intensity": rd_intensity.values,
            "source": "yfinance",
            "ingested_at": ingested_at,
        }
    )

    out["quality_pass_mvq"] = (
        out["roic"].gt(MVQ_ROIC_MIN) & out["revenue_growth_yoy"].gt(MVQ_REVENUE_GROWTH_MIN)
    )
    out = out[SCHEMA_COLUMNS]
    out = out.dropna(subset=["release_date"])
    return out


def _build_scanner_snapshot(full_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create scanner-ready latest snapshot per permno.
    Snapshot is tiny and intended for fast app startup (schema-on-write).
    """
    if full_df is None or full_df.empty:
        return pd.DataFrame(columns=SNAPSHOT_COLUMNS)

    df = full_df.copy()
    df["permno"] = pd.to_numeric(df["permno"], errors="coerce")
    df = df.dropna(subset=["permno"])
    if df.empty:
        return pd.DataFrame(columns=SNAPSHOT_COLUMNS)
    df["permno"] = df["permno"].astype("uint32")
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    df["fiscal_period_end"] = pd.to_datetime(df["fiscal_period_end"], errors="coerce")
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    if "filing_date" not in df.columns:
        df["filing_date"] = pd.NaT
    df["filing_date"] = pd.to_datetime(df["filing_date"], errors="coerce")
    if "published_at" not in df.columns:
        df["published_at"] = pd.NaT
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    fallback_published = df["filing_date"].where(df["filing_date"].notna(), df["fiscal_period_end"] + pd.Timedelta(days=90))
    df["published_at"] = df["published_at"].where(df["published_at"].notna(), fallback_published)
    df["ingested_at"] = pd.to_datetime(df["ingested_at"], errors="coerce")
    df["roic"] = pd.to_numeric(df["roic"], errors="coerce")
    for c in (
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
    ):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = np.nan
    df["roe_q"] = pd.to_numeric(df["roe_q"], errors="coerce")
    df["eps_q"] = pd.to_numeric(df["eps_q"], errors="coerce")
    df["eps_ttm"] = pd.to_numeric(df["eps_ttm"], errors="coerce")
    df["eps_growth_yoy"] = pd.to_numeric(df["eps_growth_yoy"], errors="coerce")
    df["revenue_growth_yoy"] = pd.to_numeric(df["revenue_growth_yoy"], errors="coerce")
    for c in ("ev_ebitda", "leverage_ratio", "rd_intensity", "oancf_ttm", "ebitda_ttm"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = np.nan

    df = df.dropna(subset=["release_date"])
    pit_cutoff = pd.Timestamp.utcnow().tz_localize(None).normalize()
    known_df = df[df["published_at"] <= pit_cutoff]
    if known_df.empty:
        known_df = df

    known_df = known_df.sort_values(["permno", "release_date", "published_at", "ingested_at"])
    latest = known_df.drop_duplicates(subset=["permno"], keep="last").copy()

    quality = latest["roic"].gt(MVQ_ROIC_MIN) & latest["revenue_growth_yoy"].gt(MVQ_REVENUE_GROWTH_MIN)
    quality = quality.fillna(False).astype("int8")
    bypass_mask = latest["ticker"].isin(QUALITY_BYPASS_TICKERS)
    quality.loc[bypass_mask] = 1
    latest["quality_pass"] = quality

    for c in SNAPSHOT_COLUMNS:
        if c not in latest.columns:
            latest[c] = np.nan

    latest = latest[SNAPSHOT_COLUMNS]
    latest["published_at"] = pd.to_datetime(latest["published_at"], errors="coerce")
    latest["roic"] = latest["roic"].astype("float32")
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
        latest[c] = pd.to_numeric(latest[c], errors="coerce").astype("float32")
    latest["roe_q"] = pd.to_numeric(latest["roe_q"], errors="coerce").astype("float32")
    latest["eps_q"] = pd.to_numeric(latest["eps_q"], errors="coerce").astype("float32")
    latest["eps_ttm"] = pd.to_numeric(latest["eps_ttm"], errors="coerce").astype("float32")
    latest["eps_growth_yoy"] = pd.to_numeric(latest["eps_growth_yoy"], errors="coerce").astype("float32")
    latest["revenue_growth_yoy"] = latest["revenue_growth_yoy"].astype("float32")
    for c in ("ev_ebitda", "leverage_ratio", "rd_intensity", "oancf_ttm", "ebitda_ttm"):
        latest[c] = pd.to_numeric(latest[c], errors="coerce").astype("float32")
    latest = latest.sort_values(["ticker", "permno"]).reset_index(drop=True)
    return latest


def _save_scanner_snapshot(full_df: pd.DataFrame, status: dict) -> int:
    snap = _build_scanner_snapshot(full_df)
    updater.atomic_parquet_write(snap, FUNDAMENTALS_SNAPSHOT_PATH, index=False)
    n = int(len(snap))
    status["snapshot_rows"] = n
    _log(status, f"💾 fundamentals_snapshot.parquet rows: {n:,}")
    return n


def _checkpoint_now_iso() -> str:
    return pd.Timestamp.utcnow().tz_localize(None).isoformat(timespec="seconds")


def _atomic_json_write(payload: dict, filename: str):
    temp_file = f"{filename}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(temp_file, filename)
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass


def _read_checkpoint_metadata(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except OSError as exc:
        raise RuntimeError(f"Unable to read checkpoint metadata: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Checkpoint metadata is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Checkpoint metadata payload must be a JSON object.")
    return payload


def _checkpoint_stage(stage: str | None) -> str:
    s = str(stage or "").strip().lower()
    if s in {CHECKPOINT_STAGE_FETCH, CHECKPOINT_STAGE_MERGE, CHECKPOINT_STAGE_FINAL_WRITE, CHECKPOINT_STAGE_DONE}:
        return s
    return CHECKPOINT_STAGE_FETCH


def _remove_file_if_exists(path: str):
    if not os.path.exists(path):
        return
    try:
        os.remove(path)
    except OSError:
        pass


def _cleanup_checkpoint_files():
    _remove_file_if_exists(FUNDAMENTALS_INGEST_CHECKPOINT_META_PATH)
    _remove_file_if_exists(FUNDAMENTALS_INGEST_CHECKPOINT_ROWS_PATH)


def _normalize_schema_rows(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in SCHEMA_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
    return out[SCHEMA_COLUMNS]


def _normalize_checkpoint_permno_map(raw_map: Any) -> dict[str, int]:
    if not isinstance(raw_map, dict):
        return {}
    out: dict[str, int] = {}
    for ticker, permno in raw_map.items():
        t = str(ticker).upper().strip()
        if not t:
            continue
        permno_n = pd.to_numeric(permno, errors="coerce")
        if pd.isna(permno_n):
            continue
        permno_i = int(permno_n)
        if permno_i <= 0:
            continue
        out[t] = permno_i
    return out


def _derive_checkpoint_permno_map_from_rows(rows: pd.DataFrame, targets: list[str]) -> dict[str, int]:
    if rows.empty or "ticker" not in rows.columns or "permno" not in rows.columns:
        return {}
    target_set = set(_normalize_tickers(targets))
    if not target_set:
        return {}
    pairs = rows[["ticker", "permno"]].copy()
    pairs["ticker"] = pairs["ticker"].astype(str).str.upper().str.strip()
    pairs["permno"] = pd.to_numeric(pairs["permno"], errors="coerce")
    pairs = pairs[pairs["ticker"].isin(target_set)]
    pairs = pairs.dropna(subset=["ticker", "permno"])
    if pairs.empty:
        return {}
    pairs = pairs.drop_duplicates(subset=["ticker"], keep="last")
    return {str(ticker): int(permno) for ticker, permno in zip(pairs["ticker"], pairs["permno"])}


def _parse_nonnegative_int(value: Any, field_name: str) -> int:
    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed):
        raise RuntimeError(f"checkpoint metadata field '{field_name}' must be numeric; got {value!r}")
    parsed_int = int(parsed)
    if parsed_int < 0:
        raise RuntimeError(f"checkpoint metadata field '{field_name}' must be non-negative; got {value!r}")
    return parsed_int


def _normalize_checkpoint_payload(payload: dict) -> dict:
    out = dict(payload)
    out["version"] = _parse_nonnegative_int(out.get("version", CHECKPOINT_VERSION), "version")
    out["targets"] = _normalize_tickers(out.get("targets", []))
    out["processed_tickers"] = _normalize_tickers(out.get("processed_tickers", []))
    out["permno_map"] = _normalize_checkpoint_permno_map(out.get("permno_map", {}))
    raw_stage = str(out.get("stage", "")).strip().lower()
    if raw_stage and raw_stage not in {
        CHECKPOINT_STAGE_FETCH,
        CHECKPOINT_STAGE_MERGE,
        CHECKPOINT_STAGE_FINAL_WRITE,
        CHECKPOINT_STAGE_DONE,
    }:
        raise RuntimeError(f"checkpoint metadata field 'stage' is invalid: {out.get('stage')!r}")
    out["stage"] = _checkpoint_stage(raw_stage)
    out["rows_in_partial"] = _parse_nonnegative_int(out.get("rows_in_partial", 0), "rows_in_partial")
    out["tickers_with_data"] = _parse_nonnegative_int(out.get("tickers_with_data", 0), "tickers_with_data")
    return out


def _validate_checkpoint_partial_rows(rows: pd.DataFrame, targets: list[str]) -> str | None:
    if rows.empty:
        return None
    if "ticker" not in rows.columns or "permno" not in rows.columns:
        return "checkpoint rows missing required columns: ticker/permno"
    tickers_raw = rows["ticker"].astype(str).str.upper().str.strip()
    if tickers_raw.eq("").any() or tickers_raw.eq("NAN").any():
        return "checkpoint rows contain blank ticker values"
    target_set = set(_normalize_tickers(targets))
    row_tickers = set(_normalize_tickers(tickers_raw.tolist()))
    unknown_row_tickers = sorted(row_tickers - target_set)
    if unknown_row_tickers:
        return f"checkpoint rows contain out-of-scope tickers: {unknown_row_tickers[:5]}"
    permno_vals = pd.to_numeric(rows["permno"], errors="coerce")
    if permno_vals.isna().any():
        return "checkpoint rows contain null/non-numeric permno values"
    if (permno_vals <= 0).any():
        return "checkpoint rows contain non-positive permno values"
    return None


def _checkpoint_write_metadata(payload: dict):
    out = dict(payload)
    out["version"] = int(out.get("version", CHECKPOINT_VERSION))
    out["targets"] = _normalize_tickers(out.get("targets", []))
    out["processed_tickers"] = _normalize_tickers(out.get("processed_tickers", []))
    out["permno_map"] = _normalize_checkpoint_permno_map(out.get("permno_map", {}))
    out["stage"] = _checkpoint_stage(out.get("stage"))
    out["rows_in_partial"] = int(out.get("rows_in_partial", 0))
    out["tickers_with_data"] = int(out.get("tickers_with_data", 0))
    out["updated_at"] = _checkpoint_now_iso()
    if not out.get("created_at"):
        out["created_at"] = out["updated_at"]
    _atomic_json_write(out, FUNDAMENTALS_INGEST_CHECKPOINT_META_PATH)


def _new_checkpoint_payload(scope: str, custom_list: str | None, targets: list[str]) -> dict:
    now = _checkpoint_now_iso()
    return {
        "version": CHECKPOINT_VERSION,
        "scope": scope,
        "custom_list": custom_list,
        "targets": list(targets),
        "processed_tickers": [],
        "permno_map": {},
        "tickers_with_data": 0,
        "rows_in_partial": 0,
        "stage": CHECKPOINT_STAGE_FETCH,
        "created_at": now,
        "updated_at": now,
    }


def _checkpoint_mismatch_reset(
    status: dict,
    reason: str,
    mismatch_policy: str,
) -> bool:
    msg = f"Checkpoint mismatch: {reason}"
    if mismatch_policy == CHECKPOINT_MISMATCH_RESET:
        _log(status, f"♻ {msg}. Resetting checkpoint.")
        _cleanup_checkpoint_files()
        return True
    _log(
        status,
        "✗ "
        + msg
        + ". Re-run with checkpoint_mismatch_policy='reset' (or CLI --checkpoint-mismatch reset), "
        + "or pass checkpoint_reset=True (or CLI --checkpoint-reset).",
    )
    return False


def _load_checkpoint_partial_rows() -> pd.DataFrame:
    if not os.path.exists(FUNDAMENTALS_INGEST_CHECKPOINT_ROWS_PATH):
        return pd.DataFrame(columns=SCHEMA_COLUMNS)
    try:
        rows = pd.read_parquet(FUNDAMENTALS_INGEST_CHECKPOINT_ROWS_PATH)
    except Exception as exc:
        raise RuntimeError(f"Unable to read checkpoint partial rows: {exc}") from exc
    return _normalize_schema_rows(rows)


def run_update(
    scope: str = "Top 100",
    custom_list: str | None = None,
    *,
    checkpoint_enabled: bool = False,
    checkpoint_keep: bool = False,
    checkpoint_reset: bool = False,
    checkpoint_mismatch_policy: str = CHECKPOINT_MISMATCH_FAIL,
) -> dict:
    """
    Run fundamentals ingestion and save `fundamentals.parquet`.
    """
    status = _new_status()
    _log(status, "=" * 58)
    _log(status, f"📚 Fundamentals Update (FR-027) — Scope: {scope}")
    _log(status, "=" * 58)

    if checkpoint_enabled:
        checkpoint_mismatch_policy = str(checkpoint_mismatch_policy or CHECKPOINT_MISMATCH_FAIL).strip().lower()
        if checkpoint_mismatch_policy not in {CHECKPOINT_MISMATCH_FAIL, CHECKPOINT_MISMATCH_RESET}:
            _log(
                status,
                f"✗ Invalid checkpoint mismatch policy '{checkpoint_mismatch_policy}'. "
                f"Use '{CHECKPOINT_MISMATCH_FAIL}' or '{CHECKPOINT_MISMATCH_RESET}'.",
            )
            return status

    if not os.path.exists(TICKERS_PATH):
        _log(status, "✗ Missing tickers.parquet. Run ETL/updater first.")
        return status

    gate_ok, gate_msg = _phase17_writer_gate()
    if not gate_ok:
        _log(status, f"✗ {gate_msg}")
        return status

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    try:
        updater._acquire_update_lock()
    except TimeoutError:
        _log(status, "✗ Another update is already running. Try again after it completes.")
        return status

    try:
        ticker_df = pd.read_parquet(TICKERS_PATH)
        ticker_df["ticker"] = ticker_df["ticker"].astype(str).str.upper().str.strip()
        ticker_df["permno"] = pd.to_numeric(ticker_df["permno"], errors="coerce").astype("Int64")
        ticker_df = ticker_df.dropna(subset=["permno"])
        ticker_df["permno"] = ticker_df["permno"].astype("uint32")

        requested_targets = _normalize_tickers(_get_target_tickers(scope, custom_list))
        if not requested_targets:
            _log(status, "✗ No target tickers found.")
            return status

        checkpoint_payload: dict | None = None
        checkpoint_stage = CHECKPOINT_STAGE_FETCH
        processed_tickers: list[str] = []
        processed_set: set[str] = set()
        checkpoint_permno_map: dict[str, int] = {}
        partial_rows = pd.DataFrame(columns=SCHEMA_COLUMNS)
        targets = list(requested_targets)

        if checkpoint_enabled:
            if checkpoint_reset:
                _log(status, "♻ Checkpoint reset requested. Removing prior checkpoint artifacts.")
                _cleanup_checkpoint_files()

            try:
                checkpoint_payload = _read_checkpoint_metadata(FUNDAMENTALS_INGEST_CHECKPOINT_META_PATH)
                if checkpoint_payload is not None:
                    checkpoint_payload = _normalize_checkpoint_payload(checkpoint_payload)
            except RuntimeError as exc:
                can_continue = _checkpoint_mismatch_reset(
                    status,
                    str(exc),
                    checkpoint_mismatch_policy,
                )
                if not can_continue:
                    return status
                checkpoint_payload = None
            if checkpoint_payload is not None:
                frozen_targets = _normalize_tickers(checkpoint_payload.get("targets", []))
                if not frozen_targets:
                    can_continue = _checkpoint_mismatch_reset(
                        status,
                        "existing metadata has empty frozen targets",
                        checkpoint_mismatch_policy,
                    )
                    if not can_continue:
                        return status
                    checkpoint_payload = None
                elif frozen_targets != requested_targets:
                    can_continue = _checkpoint_mismatch_reset(
                        status,
                        "frozen targets differ from requested targets",
                        checkpoint_mismatch_policy,
                    )
                    if not can_continue:
                        return status
                    checkpoint_payload = None
                else:
                    checkpoint_stage = _checkpoint_stage(checkpoint_payload.get("stage"))
                    if checkpoint_stage == CHECKPOINT_STAGE_DONE:
                        _log(status, "ℹ Found completed checkpoint; starting a fresh checkpointed run.")
                        _cleanup_checkpoint_files()
                        checkpoint_payload = None

            if checkpoint_payload is None:
                targets = list(requested_targets)
                checkpoint_stage = CHECKPOINT_STAGE_FETCH
                if os.path.exists(FUNDAMENTALS_INGEST_CHECKPOINT_ROWS_PATH):
                    _log(status, "♻ Removing orphan checkpoint partial rows before initialization.")
                    _remove_file_if_exists(FUNDAMENTALS_INGEST_CHECKPOINT_ROWS_PATH)
                checkpoint_payload = _new_checkpoint_payload(scope, custom_list, targets)
                checkpoint_permno_map = {}
                _checkpoint_write_metadata(checkpoint_payload)
                _log(status, f"🧭 Checkpoint initialized with {len(targets)} frozen targets.")
            else:
                targets = _normalize_tickers(checkpoint_payload.get("targets", []))
                checkpoint_stage = _checkpoint_stage(checkpoint_payload.get("stage"))
                processed_tickers = _normalize_tickers(checkpoint_payload.get("processed_tickers", []))
                checkpoint_permno_map = _normalize_checkpoint_permno_map(checkpoint_payload.get("permno_map", {}))
                try:
                    partial_rows = _load_checkpoint_partial_rows()
                except RuntimeError as exc:
                    can_continue = _checkpoint_mismatch_reset(
                        status,
                        str(exc),
                        checkpoint_mismatch_policy,
                    )
                    if not can_continue:
                        return status
                    targets = list(requested_targets)
                    checkpoint_stage = CHECKPOINT_STAGE_FETCH
                    processed_tickers = []
                    processed_set.clear()
                    partial_rows = pd.DataFrame(columns=SCHEMA_COLUMNS)
                    checkpoint_payload = _new_checkpoint_payload(scope, custom_list, targets)
                    checkpoint_permno_map = {}
                    _checkpoint_write_metadata(checkpoint_payload)
                row_tickers = (
                    _normalize_tickers(partial_rows["ticker"].astype(str).tolist())
                    if not partial_rows.empty
                    else []
                )
                row_validation_error = _validate_checkpoint_partial_rows(partial_rows, targets)
                if row_validation_error:
                    can_continue = _checkpoint_mismatch_reset(
                        status,
                        row_validation_error,
                        checkpoint_mismatch_policy,
                    )
                    if not can_continue:
                        return status
                    targets = list(requested_targets)
                    checkpoint_stage = CHECKPOINT_STAGE_FETCH
                    processed_tickers = []
                    processed_set.clear()
                    partial_rows = pd.DataFrame(columns=SCHEMA_COLUMNS)
                    checkpoint_payload = _new_checkpoint_payload(scope, custom_list, targets)
                    checkpoint_permno_map = {}
                    _checkpoint_write_metadata(checkpoint_payload)
                    row_tickers = []
                if not partial_rows.empty:
                    checkpoint_permno_map.update(_derive_checkpoint_permno_map_from_rows(partial_rows, targets))
                unknown_row_tickers = sorted(set(row_tickers) - set(targets))
                if unknown_row_tickers:
                    can_continue = _checkpoint_mismatch_reset(
                        status,
                        f"checkpoint rows contain out-of-scope tickers: {unknown_row_tickers[:5]}",
                        checkpoint_mismatch_policy,
                    )
                    if not can_continue:
                        return status
                    targets = list(requested_targets)
                    checkpoint_stage = CHECKPOINT_STAGE_FETCH
                    processed_tickers = []
                    processed_set.clear()
                    partial_rows = pd.DataFrame(columns=SCHEMA_COLUMNS)
                    checkpoint_payload = _new_checkpoint_payload(scope, custom_list, targets)
                    checkpoint_permno_map = {}
                    _checkpoint_write_metadata(checkpoint_payload)
                    row_tickers = []

                if checkpoint_stage in {CHECKPOINT_STAGE_MERGE, CHECKPOINT_STAGE_FINAL_WRITE} and partial_rows.empty:
                    can_continue = _checkpoint_mismatch_reset(
                        status,
                        f"stage '{checkpoint_stage}' requires checkpoint rows but rows file is missing/empty",
                        checkpoint_mismatch_policy,
                    )
                    if not can_continue:
                        return status
                    targets = list(requested_targets)
                    checkpoint_stage = CHECKPOINT_STAGE_FETCH
                    processed_tickers = []
                    processed_set.clear()
                    partial_rows = pd.DataFrame(columns=SCHEMA_COLUMNS)
                    checkpoint_payload = _new_checkpoint_payload(scope, custom_list, targets)
                    checkpoint_permno_map = {}
                    _checkpoint_write_metadata(checkpoint_payload)
                    row_tickers = []
                elif checkpoint_stage == CHECKPOINT_STAGE_FETCH and processed_tickers and partial_rows.empty:
                    can_continue = _checkpoint_mismatch_reset(
                        status,
                        "fetch stage has processed_tickers but checkpoint rows are missing/empty",
                        checkpoint_mismatch_policy,
                    )
                    if not can_continue:
                        return status
                    targets = list(requested_targets)
                    checkpoint_stage = CHECKPOINT_STAGE_FETCH
                    processed_tickers = []
                    processed_set.clear()
                    partial_rows = pd.DataFrame(columns=SCHEMA_COLUMNS)
                    checkpoint_payload = _new_checkpoint_payload(scope, custom_list, targets)
                    checkpoint_permno_map = {}
                    _checkpoint_write_metadata(checkpoint_payload)
                    row_tickers = []
                else:
                    processed_tickers = row_tickers
                    processed_set = set(row_tickers)
                    _log(
                        status,
                        f"↩ Resuming checkpoint at stage '{checkpoint_stage}' "
                        f"({len(processed_set)}/{len(targets)} tickers with checkpoint rows).",
                    )

        status["tickers_requested"] = len(targets)
        _log(status, f"🎯 Targets: {len(targets)} tickers")

        t2p = dict(zip(ticker_df["ticker"], ticker_df["permno"].astype(int)))
        max_permno = int(ticker_df["permno"].max()) if not ticker_df.empty else 900000
        next_permno = max(900000, max_permno + 1)
        if checkpoint_enabled:
            # Freeze target ticker->permno identity for checkpointed resumes to avoid map drift.
            for ticker, permno in checkpoint_permno_map.items():
                t2p[ticker] = int(permno)
        new_tickers: list[str] = []
        for t in targets:
            if t not in t2p:
                t2p[t] = next_permno
                next_permno += 1
                new_tickers.append(t)
        if checkpoint_enabled:
            frozen_map = {ticker: int(t2p[ticker]) for ticker in targets if ticker in t2p}
            checkpoint_payload["permno_map"] = frozen_map
            _checkpoint_write_metadata(checkpoint_payload)
        status["new_tickers"] = len(new_tickers)
        if new_tickers:
            _log(status, f"🆕 New symbols assigned synthetic permnos: {len(new_tickers)}")

        rows: list[pd.DataFrame] = []
        if checkpoint_enabled and checkpoint_stage == CHECKPOINT_STAGE_FETCH:
            for i, ticker in enumerate(targets, start=1):
                if ticker in processed_set:
                    _log(status, f"[{i:>3}/{len(targets)}] Skipping {ticker} (checkpoint).")
                    continue
                _log(status, f"[{i:>3}/{len(targets)}] Fetching {ticker} ...")
                try:
                    tdf = _extract_ticker_fundamentals(ticker, t2p[ticker])
                except Exception as e:
                    _log(status, f"      ⚠ Failed: {e}")
                    tdf = pd.DataFrame(columns=SCHEMA_COLUMNS)
                if tdf.empty:
                    _log(status, "      ⚠ No usable quarterly fundamentals")
                else:
                    tdf = _normalize_schema_rows(tdf)
                    if partial_rows.empty:
                        partial_rows = tdf.reset_index(drop=True)
                    else:
                        partial_rows = pd.concat([partial_rows, tdf], ignore_index=True)
                    updater.atomic_parquet_write(partial_rows, FUNDAMENTALS_INGEST_CHECKPOINT_ROWS_PATH, index=False)
                    _log(status, f"      ✓ {len(tdf)} quarterly rows")
                    if ticker not in processed_set:
                        processed_tickers.append(ticker)
                        processed_set.add(ticker)
                checkpoint_payload["processed_tickers"] = list(processed_tickers)
                checkpoint_payload["rows_in_partial"] = int(len(partial_rows))
                checkpoint_payload["tickers_with_data"] = int(partial_rows["ticker"].nunique()) if not partial_rows.empty else 0
                checkpoint_payload["stage"] = CHECKPOINT_STAGE_FETCH
                _checkpoint_write_metadata(checkpoint_payload)
            checkpoint_stage = CHECKPOINT_STAGE_MERGE
        elif checkpoint_enabled:
            _log(status, f"↩ Skipping fetch stage because checkpoint is at '{checkpoint_stage}'.")
        else:
            for i, ticker in enumerate(targets, start=1):
                _log(status, f"[{i:>3}/{len(targets)}] Fetching {ticker} ...")
                try:
                    tdf = _extract_ticker_fundamentals(ticker, t2p[ticker])
                except Exception as e:
                    _log(status, f"      ⚠ Failed: {e}")
                    continue
                if tdf.empty:
                    _log(status, "      ⚠ No usable quarterly fundamentals")
                    continue
                rows.append(tdf)
                _log(status, f"      ✓ {len(tdf)} quarterly rows")

        if checkpoint_enabled:
            if partial_rows.empty:
                _log(status, "✗ No fundamentals were extracted.")
                return status
            checkpoint_payload["stage"] = CHECKPOINT_STAGE_MERGE
            checkpoint_payload["processed_tickers"] = list(processed_tickers)
            checkpoint_payload["rows_in_partial"] = int(len(partial_rows))
            checkpoint_payload["tickers_with_data"] = int(partial_rows["ticker"].nunique()) if not partial_rows.empty else 0
            _checkpoint_write_metadata(checkpoint_payload)
            new_df = partial_rows.copy()
        else:
            if not rows:
                _log(status, "✗ No fundamentals were extracted.")
                return status
            new_df = pd.concat(rows, ignore_index=True)

        status["tickers_with_data"] = int(new_df["ticker"].nunique())

        if os.path.exists(FUNDAMENTALS_PATH):
            old_df = pd.read_parquet(FUNDAMENTALS_PATH)
            combined = pd.concat([old_df, new_df], ignore_index=True)
        else:
            combined = new_df

        combined["release_date"] = pd.to_datetime(combined["release_date"], errors="coerce")
        combined["release_date"] = combined["release_date"].dt.normalize()
        combined["fiscal_period_end"] = pd.to_datetime(combined["fiscal_period_end"], errors="coerce")
        if "filing_date" not in combined.columns:
            combined["filing_date"] = pd.NaT
        combined["filing_date"] = pd.to_datetime(combined["filing_date"], errors="coerce")
        combined["filing_date"] = combined["filing_date"].dt.normalize()
        if "published_at" not in combined.columns:
            combined["published_at"] = pd.NaT
        combined["published_at"] = pd.to_datetime(combined["published_at"], errors="coerce")
        published_fallback = combined["filing_date"].where(
            combined["filing_date"].notna(),
            combined["fiscal_period_end"] + pd.Timedelta(days=90),
        )
        combined["published_at"] = combined["published_at"].where(
            combined["published_at"].notna(),
            published_fallback,
        )
        combined["published_at"] = pd.to_datetime(combined["published_at"], errors="coerce").dt.normalize()
        combined["ingested_at"] = pd.to_datetime(combined["ingested_at"], errors="coerce")

        combined = combined.sort_values(["permno", "release_date", "published_at", "ingested_at"])
        combined = combined.drop_duplicates(subset=["permno", "release_date", "published_at"], keep="last")
        combined = _normalize_schema_rows(combined)

        if checkpoint_enabled:
            checkpoint_payload["stage"] = CHECKPOINT_STAGE_FINAL_WRITE
            checkpoint_payload["rows_in_partial"] = int(len(new_df))
            checkpoint_payload["tickers_with_data"] = int(new_df["ticker"].nunique()) if not new_df.empty else 0
            _checkpoint_write_metadata(checkpoint_payload)

        updater.atomic_parquet_write(combined, FUNDAMENTALS_PATH, index=False)
        status["rows_written"] = len(combined)
        latest_release = combined["release_date"].max()
        if pd.notna(latest_release):
            status["last_release_date"] = str(pd.Timestamp(latest_release).date())

        # Persist ticker map in case new symbols were assigned synthetic permnos.
        map_df = pd.DataFrame(
            [{"permno": np.uint32(v), "ticker": k} for k, v in t2p.items()]
        ).sort_values("ticker")
        updater.atomic_parquet_write(map_df, TICKERS_PATH, index=False)

        _save_scanner_snapshot(combined, status)

        status["success"] = True
        _log(status, f"💾 fundamentals.parquet rows: {status['rows_written']:,}")
        _log(status, f"📅 Latest release date: {status['last_release_date']}")
        _log(status, f"✅ Complete. Data for {status['tickers_with_data']} tickers.")
        _log(status, "=" * 58)

        if checkpoint_enabled:
            if checkpoint_keep:
                checkpoint_payload["stage"] = CHECKPOINT_STAGE_DONE
                checkpoint_payload["processed_tickers"] = list(targets)
                checkpoint_payload["rows_in_partial"] = int(len(new_df))
                checkpoint_payload["tickers_with_data"] = int(new_df["ticker"].nunique()) if not new_df.empty else 0
                checkpoint_payload["completed_at"] = _checkpoint_now_iso()
                _checkpoint_write_metadata(checkpoint_payload)
                _log(status, "🧷 Checkpoint artifacts kept (--checkpoint-keep).")
            else:
                _cleanup_checkpoint_files()
                _log(status, "🧹 Checkpoint artifacts removed after successful completion.")

        return status
    finally:
        updater._release_update_lock()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Terminal Zero Fundamentals Updater")
    parser.add_argument(
        "--scope",
        default="Top 100",
        help="'Top 50', 'Top 100', 'Top 200', 'Top 500', 'Top 3000', or 'Custom'",
    )
    parser.add_argument(
        "--tickers",
        default=None,
        help="Comma-separated tickers when --scope=Custom",
    )
    parser.add_argument(
        "--checkpoint",
        action="store_true",
        help="Enable ingest checkpoint/resume for heavy fundamentals merges.",
    )
    parser.add_argument(
        "--checkpoint-keep",
        action="store_true",
        help="Keep checkpoint metadata and partial rows after a successful run.",
    )
    parser.add_argument(
        "--checkpoint-reset",
        action="store_true",
        help="Delete existing checkpoint artifacts before starting this run.",
    )
    parser.add_argument(
        "--checkpoint-mismatch",
        choices=[CHECKPOINT_MISMATCH_FAIL, CHECKPOINT_MISMATCH_RESET],
        default=CHECKPOINT_MISMATCH_FAIL,
        help="Behavior when requested targets differ from frozen checkpoint targets.",
    )
    args = parser.parse_args()

    result = run_update(
        scope=args.scope,
        custom_list=args.tickers,
        checkpoint_enabled=args.checkpoint,
        checkpoint_keep=args.checkpoint_keep,
        checkpoint_reset=args.checkpoint_reset,
        checkpoint_mismatch_policy=args.checkpoint_mismatch,
    )
    if not result["success"]:
        sys.exit(1)
