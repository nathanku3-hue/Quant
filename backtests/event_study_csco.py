from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

TICKERS_PATH = os.path.join(PROCESSED_DIR, "tickers.parquet")
PRICES_PATH = os.path.join(PROCESSED_DIR, "prices.parquet")
PANEL_PATH = os.path.join(PROCESSED_DIR, "daily_fundamentals_panel.parquet")
COMPUSTAT_CSV_PATH = os.path.join(DATA_DIR, "e1o8zgcrz4nwbyif.csv")

EVAL_MODE_CSCO_DROP = "csco_drop"
EVAL_MODE_RALLY_POSITIVE = "rally_positive"
EVAL_MODES = {EVAL_MODE_CSCO_DROP, EVAL_MODE_RALLY_POSITIVE}


@dataclass(frozen=True)
class EventConfig:
    ticker: str = "CSCO"
    start: str = "1999-01-01"
    end: str = "2001-12-31"
    smooth_factor: float = 0.02
    proxy_gate_threshold: float = 0.0
    sales_accel_weight: float = 1.0
    op_margin_accel_weight: float = 1.0
    bloat_weight: float = -1.0
    net_investment_weight: float = -0.5
    eval_mode: str = EVAL_MODE_CSCO_DROP
    rally_start: str | None = None
    rally_end: str | None = None


def _sql_escape(path: str) -> str:
    return path.replace("\\", "/").replace("'", "''")


def _zscore(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    mu = s.mean(skipna=True)
    sigma = s.std(skipna=True)
    if not np.isfinite(sigma) or sigma == 0:
        return pd.Series(0.0, index=s.index, dtype=float)
    return (s - mu) / sigma


def _sigmoid(series: pd.Series, smooth_factor: float) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce") / max(float(smooth_factor), 1e-6)
    x = np.clip(x, -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(-x))


def _inventory_quality_proxy(
    sales_accel: pd.Series,
    op_margin_accel: pd.Series,
    bloat: pd.Series,
    net_investment: pd.Series,
    sales_accel_weight: float = 1.0,
    op_margin_accel_weight: float = 1.0,
    bloat_weight: float = -1.0,
    net_investment_weight: float = -0.5,
) -> pd.Series:
    return (
        float(sales_accel_weight) * _zscore(sales_accel).fillna(0.0)
        + float(op_margin_accel_weight) * _zscore(op_margin_accel).fillna(0.0)
        + float(bloat_weight) * _zscore(bloat).fillna(0.0)
        + float(net_investment_weight) * _zscore(net_investment).fillna(0.0)
    )


def _apply_proxy_gate(
    discipline_penalty: pd.Series,
    proxy_score: pd.Series,
    proxy_gate_threshold: float,
) -> pd.Series:
    gate_open = pd.to_numeric(proxy_score, errors="coerce").gt(float(proxy_gate_threshold))
    return discipline_penalty.where(~gate_open, 0.0)


def _atomic_write_csv(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.{pd.Timestamp.utcnow().value}.tmp"
    try:
        df.to_csv(tmp, index=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _output_paths(cfg: EventConfig) -> dict[str, str]:
    start_year = pd.Timestamp(cfg.start).year
    end_year = pd.Timestamp(cfg.end).year
    base = f"{cfg.ticker.lower()}_event_study_{start_year}_{end_year}"
    return {
        "csv": os.path.join(PROCESSED_DIR, f"{base}.csv"),
        "png": os.path.join(PROCESSED_DIR, f"{base}.png"),
        "html": os.path.join(PROCESSED_DIR, f"{base}.html"),
    }


def _load_permno_for_ticker(ticker: str) -> int:
    con = duckdb.connect()
    try:
        row = con.execute(
            f"""
            SELECT CAST(permno AS BIGINT) AS permno
            FROM read_parquet('{_sql_escape(TICKERS_PATH)}')
            WHERE UPPER(TRIM(CAST(ticker AS VARCHAR))) = ?
            ORDER BY permno
            LIMIT 1
            """,
            [ticker.upper().strip()],
        ).fetchone()
    finally:
        con.close()
    if row is None:
        raise ValueError(f"Ticker {ticker} not found in {TICKERS_PATH}")
    return int(row[0])


def _load_prices(permno: int, start: str, end: str) -> pd.DataFrame:
    if not os.path.exists(PRICES_PATH):
        raise RuntimeError(
            f"Missing prices artifact: {PRICES_PATH}. Run data ingestion before event study."
        )
    con = duckdb.connect()
    try:
        q = f"""
        SELECT
          CAST(date AS DATE) AS date,
          CAST(adj_close AS DOUBLE) AS adj_close
        FROM read_parquet('{_sql_escape(PRICES_PATH)}')
        WHERE CAST(permno AS BIGINT) = {int(permno)}
          AND CAST(date AS DATE) BETWEEN DATE '{start}' AND DATE '{end}'
        ORDER BY date
        """
        out = con.execute(q).df()
    finally:
        con.close()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return out


def _load_panel(permno: int, start: str, end: str) -> pd.DataFrame:
    if not os.path.exists(PANEL_PATH):
        return pd.DataFrame()
    con = duckdb.connect()
    try:
        info = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{_sql_escape(PANEL_PATH)}')"
        ).df()
        available_cols = {str(c).strip().lower() for c in info["column_name"].tolist()}

        def _sel(col: str, cast_type: str, alias: str | None = None) -> str:
            alias_name = alias or col
            if col.lower() in available_cols:
                return f"CAST({col} AS {cast_type}) AS {alias_name}"
            return f"CAST(NULL AS {cast_type}) AS {alias_name}"

        q = f"""
        SELECT
          {_sel("date", "DATE")},
          {_sel("release_date", "DATE")},
          {_sel("published_at", "DATE")},
          {_sel("roic", "DOUBLE")},
          {_sel("operating_margin_delta_q", "DOUBLE")},
          {_sel("asset_growth_yoy", "DOUBLE")},
          {_sel("sales_growth_q", "DOUBLE")},
          {_sel("sales_accel_q", "DOUBLE")},
          {_sel("op_margin_accel_q", "DOUBLE")},
          {_sel("bloat_q", "DOUBLE")},
          {_sel("net_investment_q", "DOUBLE")},
          {_sel("revenue_inventory_q", "DOUBLE")},
          {_sel("delta_revenue_inventory", "DOUBLE")},
          {_sel("quality_pass", "INTEGER")}
        FROM read_parquet('{_sql_escape(PANEL_PATH)}')
        WHERE CAST(permno AS BIGINT) = {int(permno)}
          AND CAST(date AS DATE) BETWEEN DATE '{start}' AND DATE '{end}'
        ORDER BY date
        """
        try:
            out = con.execute(q).df()
        except Exception as exc:
            # Backward-compatible fallback for older panel schemas.
            print(f"[event_study] panel load fallback ({type(exc).__name__}): {exc}")
            return pd.DataFrame()
    finally:
        con.close()
    if out.empty:
        return out
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["release_date"] = pd.to_datetime(out["release_date"], errors="coerce")
    out["published_at"] = pd.to_datetime(out["published_at"], errors="coerce")
    return out


def _find_compustat_path() -> str:
    if os.path.exists(COMPUSTAT_CSV_PATH):
        return COMPUSTAT_CSV_PATH
    zipped = f"{COMPUSTAT_CSV_PATH}.zip"
    if os.path.exists(zipped):
        return zipped
    raise FileNotFoundError(
        "Compustat fallback source not found at "
        f"{COMPUSTAT_CSV_PATH} or {zipped}"
    )


def _load_compustat_quarterly(
    ticker: str,
    start: str,
    end: str,
    smooth_factor: float,
    proxy_gate_threshold: float,
    sales_accel_weight: float,
    op_margin_accel_weight: float,
    bloat_weight: float,
    net_investment_weight: float,
) -> pd.DataFrame:
    csv_path = _find_compustat_path()
    ticker_key = ticker.upper().strip()
    compression = "zip" if csv_path.endswith(".zip") else None
    header = pd.read_csv(csv_path, nrows=0, compression=compression)
    available_cols = {str(c).strip().lower() for c in header.columns}
    candidate_cols = [
        "tic",
        "datadate",
        "rdq",
        "fyearq",
        "fqtr",
        "revtq",
        "invtq",
        "atq",
        "oibdpq",
        "capxq",
        "capxy",
        "dpq",
        "dpy",
        "cogsq",
        "rectq",
        "drcq",
        "drltq",
    ]
    usecols = [c for c in candidate_cols if c.lower() in available_cols]
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(csv_path, usecols=usecols, compression=compression, chunksize=250_000):
        chunk["tic"] = chunk["tic"].astype(str).str.upper().str.strip()
        sub = chunk[chunk["tic"] == ticker_key].copy()
        if not sub.empty:
            chunks.append(sub)
    if chunks:
        q = pd.concat(chunks, ignore_index=True)
    else:
        q = pd.DataFrame(columns=usecols)

    q["fiscal_period_end"] = pd.to_datetime(q["datadate"], errors="coerce")
    q["published_at"] = pd.to_datetime(q["rdq"], errors="coerce")
    q["published_at"] = q["published_at"].where(
        q["published_at"].notna(),
        q["fiscal_period_end"] + pd.Timedelta(days=90),
    )
    q = q.dropna(subset=["fiscal_period_end", "published_at"])
    q = q.sort_values("fiscal_period_end").reset_index(drop=True)
    q = q[
        (q["fiscal_period_end"] >= pd.Timestamp(start))
        & (q["fiscal_period_end"] <= pd.Timestamp(end))
    ].copy()
    if q.empty:
        return q

    q["revtq"] = pd.to_numeric(q["revtq"], errors="coerce")
    q["invtq"] = pd.to_numeric(q["invtq"], errors="coerce")
    q["atq"] = pd.to_numeric(q["atq"], errors="coerce")
    q["oibdpq"] = pd.to_numeric(q["oibdpq"], errors="coerce")
    q["capxq"] = pd.to_numeric(q.get("capxq"), errors="coerce")
    q["capxy"] = pd.to_numeric(q.get("capxy"), errors="coerce")
    q["dpq"] = pd.to_numeric(q.get("dpq"), errors="coerce")
    q["dpy"] = pd.to_numeric(q.get("dpy"), errors="coerce")
    q["cogsq"] = pd.to_numeric(q.get("cogsq"), errors="coerce")
    q["rectq"] = pd.to_numeric(q.get("rectq"), errors="coerce")
    q["drcq"] = pd.to_numeric(q.get("drcq"), errors="coerce")
    q["drltq"] = pd.to_numeric(q.get("drltq"), errors="coerce")
    q["deferred_revenue_q"] = q["drcq"].where(q["drcq"].notna(), q["drltq"])
    q["capex_q"] = q["capxq"].where(q["capxq"].notna(), q["capxy"])
    q["depreciation_q"] = q["dpq"].where(q["dpq"].notna(), q["dpy"])

    q["operating_margin_q"] = q["oibdpq"] / q["revtq"].replace(0.0, np.nan)
    q["operating_margin_delta_q"] = q["operating_margin_q"].diff()
    q["asset_growth_yoy"] = q["atq"].pct_change(4, fill_method=None)
    q["asset_growth_qoq"] = q["atq"].pct_change(1, fill_method=None)
    q["asset_growth_effective"] = q["asset_growth_yoy"].where(
        q["asset_growth_yoy"].notna(),
        q["asset_growth_qoq"],
    )

    q["inventory_to_revenue"] = q["invtq"] / q["revtq"].replace(0.0, np.nan)
    q["delta_inventory_to_revenue"] = q["inventory_to_revenue"].diff()
    q["revenue_inventory_q"] = q["revtq"] / q["invtq"].replace(0.0, np.nan)
    q["delta_revenue_inventory"] = q["revenue_inventory_q"].diff()
    q["gross_profit_q"] = q["revtq"] - q["cogsq"]
    q["gross_margin_q"] = q["gross_profit_q"] / q["revtq"].replace(0.0, np.nan)
    q["gross_margin_delta_q"] = q["gross_margin_q"].diff()
    q["gm_accel_q"] = q["gross_margin_delta_q"].diff()
    q["delta_deferred_revenue_q"] = q["deferred_revenue_q"].diff()
    q["book_to_bill_proxy_q"] = np.where(
        (q["revtq"] > 0) & q["deferred_revenue_q"].notna(),
        (q["revtq"] + q["delta_deferred_revenue_q"].fillna(0.0)) / q["revtq"],
        np.nan,
    )
    q["dso_q"] = np.where(
        q["revtq"] > 0,
        (q["rectq"] / q["revtq"]) * 90.0,
        np.nan,
    )
    q["delta_dso_q"] = q["dso_q"].diff()
    q["gm_accel_q"] = q["gm_accel_q"].where(q["gm_accel_q"].notna(), q["operating_margin_delta_q"])
    # Fallback proxy when receivables are unavailable: improving turnover implies cleaner collections.
    q["delta_dso_q"] = q["delta_dso_q"].where(q["delta_dso_q"].notna(), -q["delta_revenue_inventory"])
    q["sales_growth_q"] = q["revtq"].pct_change(fill_method=None)
    q["sales_accel_q"] = q["sales_growth_q"].diff()
    q["op_margin_accel_q"] = q["operating_margin_delta_q"].diff()
    q["asset_ex_inventory_q"] = q["atq"] - q["invtq"]
    q["bloat_q"] = (
        np.log(q["asset_ex_inventory_q"].where(q["asset_ex_inventory_q"] > 0, np.nan)).diff()
        - np.log(q["revtq"].where(q["revtq"] > 0, np.nan)).diff()
    )
    q["net_investment_q"] = (
        q["capex_q"].abs() - q["depreciation_q"]
    ) / q["atq"].shift(1).replace(0.0, np.nan)

    q["roic_proxy"] = (
        q["oibdpq"].rolling(4, min_periods=1).sum()
        / q["atq"].rolling(4, min_periods=1).mean().replace(0.0, np.nan)
    )

    q["z_moat"] = _zscore(q["roic_proxy"])
    q["z_inventory_quality_proxy"] = _inventory_quality_proxy(
        sales_accel=q["sales_accel_q"],
        op_margin_accel=q["op_margin_accel_q"],
        bloat=q["bloat_q"],
        net_investment=q["net_investment_q"],
        sales_accel_weight=sales_accel_weight,
        op_margin_accel_weight=op_margin_accel_weight,
        bloat_weight=bloat_weight,
        net_investment_weight=net_investment_weight,
    )
    operating_leverage_score = _sigmoid(q["operating_margin_delta_q"].fillna(0.0), smooth_factor=smooth_factor)
    discipline_penalty = q["asset_growth_effective"] * (1.0 - operating_leverage_score)
    discipline_penalty = _apply_proxy_gate(
        discipline_penalty=discipline_penalty,
        proxy_score=q["z_inventory_quality_proxy"],
        proxy_gate_threshold=proxy_gate_threshold,
    )
    q["z_discipline_cond"] = _zscore(-discipline_penalty)
    q["z_demand"] = _zscore(q["delta_revenue_inventory"])
    q["capital_cycle_score"] = (
        0.4 * q["z_moat"].fillna(0.0)
        + 0.4 * q["z_discipline_cond"].fillna(0.0)
        + 0.2 * q["z_demand"].fillna(0.0)
    )
    q["source"] = "compustat_fallback"
    return q


def _quarterly_to_daily(prices: pd.DataFrame, quarterly: pd.DataFrame) -> pd.DataFrame:
    if prices.empty:
        return prices.copy()
    base = prices[["date", "adj_close"]].copy().sort_values("date")
    base["date"] = pd.to_datetime(base["date"], errors="coerce").astype("datetime64[ns]")
    if quarterly.empty:
        for c in [
            "z_moat",
            "z_discipline_cond",
            "z_demand",
            "capital_cycle_score",
            "asset_growth_effective",
            "delta_inventory_to_revenue",
            "delta_revenue_inventory",
            "operating_margin_delta_q",
            "sales_growth_q",
            "sales_accel_q",
            "op_margin_accel_q",
            "bloat_q",
            "net_investment_q",
            "z_inventory_quality_proxy",
            "book_to_bill_proxy_q",
            "gm_accel_q",
            "delta_dso_q",
            "source",
            "published_at",
            "fiscal_period_end",
        ]:
            base[c] = np.nan
        return base

    required_cols = [
        "published_at",
        "fiscal_period_end",
        "z_moat",
        "z_discipline_cond",
        "z_demand",
        "capital_cycle_score",
        "asset_growth_effective",
        "delta_inventory_to_revenue",
        "delta_revenue_inventory",
        "operating_margin_delta_q",
        "sales_growth_q",
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
        "z_inventory_quality_proxy",
        "book_to_bill_proxy_q",
        "gm_accel_q",
        "delta_dso_q",
        "source",
    ]
    q0 = quarterly.copy()
    for c in required_cols:
        if c not in q0.columns:
            q0[c] = np.nan

    q = q0[
        [
            "published_at",
            "fiscal_period_end",
            "z_moat",
            "z_discipline_cond",
            "z_demand",
            "capital_cycle_score",
            "asset_growth_effective",
            "delta_inventory_to_revenue",
            "delta_revenue_inventory",
            "operating_margin_delta_q",
            "sales_growth_q",
            "sales_accel_q",
            "op_margin_accel_q",
            "bloat_q",
            "net_investment_q",
            "z_inventory_quality_proxy",
            "book_to_bill_proxy_q",
            "gm_accel_q",
            "delta_dso_q",
            "source",
        ]
    ].copy()
    q["published_at"] = pd.to_datetime(q["published_at"], errors="coerce").astype("datetime64[ns]")
    q["fiscal_period_end"] = pd.to_datetime(q["fiscal_period_end"], errors="coerce").astype("datetime64[ns]")
    q = q.sort_values("published_at")
    out = pd.merge_asof(
        base.sort_values("date"),
        q,
        left_on="date",
        right_on="published_at",
        direction="backward",
    )
    return out


def _panel_coverage_ok(panel: pd.DataFrame) -> bool:
    if panel is None or panel.empty:
        return False
    required = [
        "roic",
        "operating_margin_delta_q",
        "asset_growth_yoy",
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
        "delta_revenue_inventory",
    ]
    avail = 0
    for c in required:
        if c in panel.columns and panel[c].notna().sum() > 0:
            avail += 1
    published_ok = (
        ("published_at" in panel.columns and panel["published_at"].notna().sum() > 0)
        or ("release_date" in panel.columns and panel["release_date"].notna().sum() > 0)
    )
    return bool(avail >= 5 and published_ok)


def _build_from_panel(
    panel: pd.DataFrame,
    prices: pd.DataFrame,
    smooth_factor: float,
    proxy_gate_threshold: float,
    sales_accel_weight: float,
    op_margin_accel_weight: float,
    bloat_weight: float,
    net_investment_weight: float,
) -> pd.DataFrame:
    sort_cols = ["date"]
    if "published_at" in panel.columns:
        sort_cols.append("published_at")
    elif "release_date" in panel.columns:
        sort_cols.append("release_date")
    p = panel.copy().sort_values(sort_cols)
    p["effective_published_at"] = pd.to_datetime(p.get("published_at"), errors="coerce")
    if "release_date" in p.columns:
        release_fallback = pd.to_datetime(p["release_date"], errors="coerce")
        p["effective_published_at"] = p["effective_published_at"].where(
            p["effective_published_at"].notna(),
            release_fallback,
        )
    p = p.dropna(subset=["effective_published_at"]).copy()
    if p.empty:
        return _quarterly_to_daily(prices=prices, quarterly=pd.DataFrame())

    # Collapse panel to publication snapshots and project to daily with as-of merge.
    snap = (
        p.sort_values(["effective_published_at", "date"])
        .drop_duplicates(subset=["effective_published_at"], keep="last")
        .copy()
    )
    snap["published_at"] = pd.to_datetime(snap["effective_published_at"], errors="coerce")
    if "release_date" in snap.columns:
        snap["fiscal_period_end"] = pd.to_datetime(snap["release_date"], errors="coerce")
    elif "fiscal_period_end" in snap.columns:
        snap["fiscal_period_end"] = pd.to_datetime(snap["fiscal_period_end"], errors="coerce")
    else:
        snap["fiscal_period_end"] = pd.NaT
    for col in (
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
        "asset_growth_yoy",
        "operating_margin_delta_q",
        "delta_revenue_inventory",
        "revenue_inventory_q",
    ):
        if col not in snap.columns:
            snap[col] = np.nan
        snap[col] = pd.to_numeric(snap[col], errors="coerce")

    # Build missing proxy terms from base panel fields when necessary.
    if snap["sales_accel_q"].isna().all():
        sales_growth_q = snap["delta_revenue_inventory"].copy()
        snap["sales_accel_q"] = sales_growth_q
    if snap["op_margin_accel_q"].isna().all():
        snap["op_margin_accel_q"] = snap["operating_margin_delta_q"].diff()
    if snap["bloat_q"].isna().all():
        inv_to_rev = 1.0 / snap["revenue_inventory_q"].replace(0.0, np.nan)
        snap["bloat_q"] = inv_to_rev.diff()
    if snap["net_investment_q"].isna().all():
        snap["net_investment_q"] = snap["asset_growth_yoy"]

    snap["z_moat"] = _zscore(snap["roic"])
    snap["z_inventory_quality_proxy"] = _inventory_quality_proxy(
        sales_accel=snap["sales_accel_q"],
        op_margin_accel=snap["op_margin_accel_q"],
        bloat=snap["bloat_q"],
        net_investment=snap["net_investment_q"],
        sales_accel_weight=sales_accel_weight,
        op_margin_accel_weight=op_margin_accel_weight,
        bloat_weight=bloat_weight,
        net_investment_weight=net_investment_weight,
    )
    operating_leverage_score = _sigmoid(snap["operating_margin_delta_q"].fillna(0.0), smooth_factor=smooth_factor)
    snap["asset_growth_effective"] = snap["asset_growth_yoy"].where(
        snap["asset_growth_yoy"].notna(),
        snap["sales_growth_q"],
    )
    discipline_penalty = snap["asset_growth_effective"] * (1.0 - operating_leverage_score)
    discipline_penalty = _apply_proxy_gate(
        discipline_penalty=discipline_penalty,
        proxy_score=snap["z_inventory_quality_proxy"],
        proxy_gate_threshold=proxy_gate_threshold,
    )
    snap["z_discipline_cond"] = _zscore(-discipline_penalty)
    snap["z_demand"] = _zscore(snap["delta_revenue_inventory"])
    snap["capital_cycle_score"] = (
        0.4 * snap["z_moat"].fillna(0.0)
        + 0.4 * snap["z_discipline_cond"].fillna(0.0)
        + 0.2 * snap["z_demand"].fillna(0.0)
    )
    snap["delta_inventory_to_revenue"] = (1.0 / snap["revenue_inventory_q"].replace(0.0, np.nan)).diff()
    snap["source"] = "daily_panel"
    return _quarterly_to_daily(prices=prices, quarterly=snap)


def _save_plot(df: pd.DataFrame, output_png: str, output_html: str, ticker: str) -> dict[str, str | None]:
    png_path: str | None = None
    html_path: str | None = None
    errors: list[str] = []

    try:
        import matplotlib.pyplot as plt  # type: ignore

        fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True, gridspec_kw={"height_ratios": [2, 2]})

        ax0 = axes[0]
        ax0.plot(df["date"], df["adj_close"], color="#1f77b4", linewidth=1.5, label=f"{ticker} Close")
        ax0.set_ylabel("Price")
        ax0.set_title(f"{ticker} Event Study (1999-2001): Price vs Capital Cycle Score")
        ax0.grid(alpha=0.2)
        ax0.legend(loc="upper left")

        ax1 = axes[1]
        ax1.plot(df["date"], df["capital_cycle_score"], color="#d62728", linewidth=1.5, label="capital_cycle_score")
        ax1.plot(df["date"], df["z_moat"], color="#2ca02c", linewidth=1.0, alpha=0.9, label="z_moat")
        ax1.plot(df["date"], df["z_discipline_cond"], color="#9467bd", linewidth=1.0, alpha=0.9, label="z_discipline_cond")
        ax1.plot(df["date"], df["z_demand"], color="#ff7f0e", linewidth=1.0, alpha=0.9, label="z_demand")
        ax1.axhline(0.0, color="black", linewidth=0.8, alpha=0.4)
        ax1.set_ylabel("Z / Score")
        ax1.grid(alpha=0.2)
        ax1.legend(loc="upper left", ncol=2)

        plt.tight_layout()
        os.makedirs(os.path.dirname(output_png), exist_ok=True)
        tmp_png = f"{output_png}.{os.getpid()}.{pd.Timestamp.utcnow().value}.tmp.png"
        try:
            fig.savefig(tmp_png, dpi=140)
            os.replace(tmp_png, output_png)
            png_path = output_png
        finally:
            plt.close(fig)
            if os.path.exists(tmp_png):
                try:
                    os.remove(tmp_png)
                except OSError:
                    pass
    except Exception:
        png_path = None
        errors.append("matplotlib_plot_failed")

    try:
        import plotly.graph_objects as go  # type: ignore
        from plotly.subplots import make_subplots  # type: ignore

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.5, 0.5],
            subplot_titles=(f"{ticker} Close", "Capital Cycle Components"),
        )
        fig.add_trace(go.Scatter(x=df["date"], y=df["adj_close"], name="adj_close", line=dict(color="#1f77b4")), row=1, col=1)
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["capital_cycle_score"], name="capital_cycle_score", line=dict(color="#d62728")),
            row=2,
            col=1,
        )
        fig.add_trace(go.Scatter(x=df["date"], y=df["z_moat"], name="z_moat", line=dict(color="#2ca02c")), row=2, col=1)
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["z_discipline_cond"], name="z_discipline_cond", line=dict(color="#9467bd")),
            row=2,
            col=1,
        )
        fig.add_trace(go.Scatter(x=df["date"], y=df["z_demand"], name="z_demand", line=dict(color="#ff7f0e")), row=2, col=1)
        fig.update_layout(
            title=f"{ticker} Event Study (1999-2001)",
            template="plotly_white",
            height=760,
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0.0),
        )
        os.makedirs(os.path.dirname(output_html), exist_ok=True)
        tmp_html = f"{output_html}.{os.getpid()}.{pd.Timestamp.utcnow().value}.tmp.html"
        try:
            fig.write_html(tmp_html, include_plotlyjs="cdn")
            os.replace(tmp_html, output_html)
            html_path = output_html
        finally:
            if os.path.exists(tmp_html):
                try:
                    os.remove(tmp_html)
                except OSError:
                    pass
    except Exception:
        html_path = None
        errors.append("plotly_plot_failed")

    return {
        "png": png_path,
        "html": html_path,
        "plot_error": ";".join(errors) if errors else None,
    }


def _evaluate_drop(df: pd.DataFrame) -> tuple[bool, dict[str, float]]:
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    q2 = d[(d["date"] >= pd.Timestamp("2000-04-01")) & (d["date"] < pd.Timestamp("2000-07-01"))]["capital_cycle_score"].mean()
    q3 = d[(d["date"] >= pd.Timestamp("2000-07-01")) & (d["date"] < pd.Timestamp("2000-10-01"))]["capital_cycle_score"].mean()
    q4 = d[(d["date"] >= pd.Timestamp("2000-10-01")) & (d["date"] < pd.Timestamp("2001-01-01"))]["capital_cycle_score"].mean()
    moat_q4 = d[(d["date"] >= pd.Timestamp("2000-10-01")) & (d["date"] < pd.Timestamp("2001-01-01"))]["z_moat"].mean()

    metrics = {
        "q2_score": float(q2) if np.isfinite(q2) else float("nan"),
        "q3_score": float(q3) if np.isfinite(q3) else float("nan"),
        "q4_score": float(q4) if np.isfinite(q4) else float("nan"),
        "q4_moat": float(moat_q4) if np.isfinite(moat_q4) else float("nan"),
    }
    if not (np.isfinite(q2) and np.isfinite(q3) and np.isfinite(q4)):
        return False, metrics

    # Event-study success:
    # 1) score decays through Q3 and Q4,
    # 2) Q4 score is materially below Q2,
    # 3) moat remains positive in Q4.
    is_pass = bool((q3 < q2) and (q4 < q3) and ((q2 - q4) >= 0.25) and (moat_q4 > 0))
    return is_pass, metrics


def _evaluate_rally_positive(
    df: pd.DataFrame,
    rally_start: str,
    rally_end: str,
) -> tuple[bool, dict[str, float]]:
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    rs = pd.Timestamp(rally_start)
    re = pd.Timestamp(rally_end)
    win = d[(d["date"] >= rs) & (d["date"] <= re)].copy()
    if win.empty:
        return False, {
            "rally_mean_score": float("nan"),
            "rally_min_score": float("nan"),
            "rally_max_score": float("nan"),
            "rally_positive_share": float("nan"),
            "rally_rows": 0.0,
        }

    score = pd.to_numeric(win["capital_cycle_score"], errors="coerce")
    positive_mask = score > 0
    metrics = {
        "rally_mean_score": float(score.mean(skipna=True)),
        "rally_min_score": float(score.min(skipna=True)),
        "rally_max_score": float(score.max(skipna=True)),
        "rally_positive_share": float(positive_mask.mean(skipna=True)),
        "rally_rows": float(len(win)),
    }
    # Strict interpretation of "stays positive":
    # every scored day in the rally window must be > 0.
    passed = bool(positive_mask.fillna(False).all())
    return passed, metrics


def run_event_study(cfg: EventConfig) -> dict[str, object]:
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    permno = _load_permno_for_ticker(cfg.ticker)
    prices = _load_prices(permno=permno, start=cfg.start, end=cfg.end)
    if prices.empty:
        raise RuntimeError("No price rows found for CSCO in requested window.")

    panel = _load_panel(permno=permno, start=cfg.start, end=cfg.end)
    panel_ok = _panel_coverage_ok(panel)
    if panel_ok:
        study = _build_from_panel(
            panel=panel,
            prices=prices,
            smooth_factor=cfg.smooth_factor,
            proxy_gate_threshold=cfg.proxy_gate_threshold,
            sales_accel_weight=cfg.sales_accel_weight,
            op_margin_accel_weight=cfg.op_margin_accel_weight,
            bloat_weight=cfg.bloat_weight,
            net_investment_weight=cfg.net_investment_weight,
        )
        source_used = "daily_panel"
    else:
        try:
            quarterly = _load_compustat_quarterly(
                ticker=cfg.ticker,
                start=cfg.start,
                end=cfg.end,
                smooth_factor=cfg.smooth_factor,
                proxy_gate_threshold=cfg.proxy_gate_threshold,
                sales_accel_weight=cfg.sales_accel_weight,
                op_margin_accel_weight=cfg.op_margin_accel_weight,
                bloat_weight=cfg.bloat_weight,
                net_investment_weight=cfg.net_investment_weight,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Compustat fallback source is missing. "
                f"Expected {COMPUSTAT_CSV_PATH} or {COMPUSTAT_CSV_PATH}.zip"
            ) from exc
        if quarterly.empty:
            raise RuntimeError("Panel coverage is insufficient and Compustat fallback has no usable rows.")
        study = _quarterly_to_daily(prices=prices, quarterly=quarterly)
        source_used = "compustat_fallback"

    study = study[(study["date"] >= pd.Timestamp(cfg.start)) & (study["date"] <= pd.Timestamp(cfg.end))].copy()
    study = study.sort_values("date").reset_index(drop=True)
    study["ticker"] = cfg.ticker
    study["permno"] = permno
    outputs = _output_paths(cfg)
    _atomic_write_csv(study, outputs["csv"])
    plot_outputs = _save_plot(study, outputs["png"], outputs["html"], cfg.ticker)

    mode = str(cfg.eval_mode or EVAL_MODE_CSCO_DROP).strip().lower()
    if mode not in EVAL_MODES:
        raise ValueError(f"Unsupported eval_mode: {cfg.eval_mode}")
    if mode == EVAL_MODE_RALLY_POSITIVE:
        rally_start = cfg.rally_start or "2016-04-01"
        rally_end = cfg.rally_end or "2017-03-31"
        passed, metrics = _evaluate_rally_positive(study, rally_start=rally_start, rally_end=rally_end)
    else:
        passed, metrics = _evaluate_drop(study)

    return {
        "passed": passed,
        "source_used": source_used,
        "eval_mode": mode,
        "proxy_gate_threshold": float(cfg.proxy_gate_threshold),
        "sales_accel_weight": float(cfg.sales_accel_weight),
        "op_margin_accel_weight": float(cfg.op_margin_accel_weight),
        "bloat_weight": float(cfg.bloat_weight),
        "net_investment_weight": float(cfg.net_investment_weight),
        "permno": permno,
        "rows": int(len(study)),
        "output_csv": outputs["csv"],
        "output_png": plot_outputs.get("png"),
        "output_html": plot_outputs.get("html"),
        "plot_error": plot_outputs.get("plot_error"),
        **metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Ticker capital-cycle event study.")
    parser.add_argument("--ticker", default="CSCO")
    parser.add_argument("--start", default="1999-01-01")
    parser.add_argument("--end", default="2001-12-31")
    parser.add_argument(
        "--eval-mode",
        choices=sorted(EVAL_MODES),
        default=EVAL_MODE_CSCO_DROP,
        help="Evaluation contract: csco_drop or rally_positive.",
    )
    parser.add_argument("--rally-start", default=None, help="Required for rally_positive evaluation.")
    parser.add_argument("--rally-end", default=None, help="Required for rally_positive evaluation.")
    parser.add_argument(
        "--proxy-gate-threshold",
        type=float,
        default=0.0,
        help="Discipline waiver threshold for z_inventory_quality_proxy (> threshold opens gate).",
    )
    parser.add_argument(
        "--sales-accel-weight",
        type=float,
        default=1.0,
        help="Weight for z(sales_accel_q).",
    )
    parser.add_argument(
        "--op-margin-accel-weight",
        type=float,
        default=1.0,
        help="Weight for z(op_margin_accel_q).",
    )
    parser.add_argument(
        "--bloat-weight",
        type=float,
        default=-1.0,
        help="Weight for z(bloat_q).",
    )
    parser.add_argument(
        "--net-investment-weight",
        type=float,
        default=-0.5,
        help="Weight for z(net_investment_q).",
    )
    args = parser.parse_args()

    cfg = EventConfig(
        ticker=args.ticker,
        start=args.start,
        end=args.end,
        eval_mode=args.eval_mode,
        rally_start=args.rally_start,
        rally_end=args.rally_end,
        proxy_gate_threshold=float(args.proxy_gate_threshold),
        sales_accel_weight=float(args.sales_accel_weight),
        op_margin_accel_weight=float(args.op_margin_accel_weight),
        bloat_weight=float(args.bloat_weight),
        net_investment_weight=float(args.net_investment_weight),
    )
    result = run_event_study(cfg)

    print("=" * 72)
    print("Capital-Cycle Event Study")
    print("=" * 72)
    print(f"Ticker          : {cfg.ticker}")
    print(f"Permno          : {result['permno']}")
    print(f"Window          : {cfg.start} .. {cfg.end}")
    print(f"Rows            : {result['rows']:,}")
    print(f"Data Source     : {result['source_used']}")
    print(f"Eval Mode       : {result['eval_mode']}")
    print(
        "Proxy Gate      : "
        f"z_proxy>{result['proxy_gate_threshold']:.2f} | "
        f"w=[{result['sales_accel_weight']:.2f}, "
        f"{result['op_margin_accel_weight']:.2f}, "
        f"{result['bloat_weight']:.2f}, "
        f"{result['net_investment_weight']:.2f}]"
    )
    if result["eval_mode"] == EVAL_MODE_RALLY_POSITIVE:
        rally_start = cfg.rally_start or "2016-04-01"
        rally_end = cfg.rally_end or "2017-03-31"
        print(f"Rally Window    : {rally_start} .. {rally_end}")
        print(f"Rally Mean Score: {result['rally_mean_score']:.4f}")
        print(f"Rally Min Score : {result['rally_min_score']:.4f}")
        print(f"Rally Max Score : {result['rally_max_score']:.4f}")
        print(f"Positive Share  : {result['rally_positive_share']:.4f}")
    else:
        print(f"Q2 2000 Score   : {result['q2_score']:.4f}")
        print(f"Q3 2000 Score   : {result['q3_score']:.4f}")
        print(f"Q4 2000 Score   : {result['q4_score']:.4f}")
        print(f"Q4 2000 z_moat  : {result['q4_moat']:.4f}")
    print(f"CSV             : {result['output_csv']}")
    print(f"PNG             : {result['output_png']}")
    print(f"HTML            : {result['output_html']}")
    print(f"Plot Error      : {result.get('plot_error')}")
    print("=" * 72)
    print("PASS" if result["passed"] else "FAIL")

    if not result["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
