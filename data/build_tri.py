"""
Phase 18 Day 2 — Total Return Index (TRI) builder.

Builds a signal-safe TRI artifact from price/return history while preserving
legacy close values for comparison and rollback.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PRICES_PATH = PROCESSED_DIR / "prices.parquet"
PATCH_PATH = PROCESSED_DIR / "yahoo_patch.parquet"
TICKERS_PATH = PROCESSED_DIR / "tickers.parquet"
MACRO_TRI_PATH = PROCESSED_DIR / "macro_features_tri.parquet"

DEFAULT_START_DATE = "2015-01-01"
DEFAULT_END_DATE = "2024-12-31"
DEFAULT_OUTPUT_PATH = PROCESSED_DIR / "prices_tri.parquet"
DEFAULT_VALIDATION_CSV = PROCESSED_DIR / "phase18_day2_tri_validation.csv"
DEFAULT_SPLIT_PLOT = PROCESSED_DIR / "phase18_day2_split_events.png"

SPY_PERMNO = 84398

KNOWN_SPLITS = [
    ("AAPL", "2020-08-31", 4.0),
    ("TSLA", "2020-08-31", 5.0),
    ("TSLA", "2022-08-25", 3.0),
    ("NVDA", "2024-06-10", 10.0),
]

DIVIDEND_TICKERS = ["XOM", "T", "VZ", "CVX", "MO"]


@dataclass(frozen=True)
class BuildSummary:
    output_path: Path
    rows: int
    start_date: str
    end_date: str
    tri_min: float
    tri_max: float


def _sql_escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def _to_timestamp(value: str | None) -> pd.Timestamp | None:
    if value is None:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Invalid date: {value}")
    return pd.Timestamp(ts).normalize()


def _atomic_replace(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    attempts = 8
    for i in range(attempts):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if i >= attempts - 1:
                raise
            time.sleep(0.15 * (i + 1))


def _tmp_path_for(path: Path, suffix: str = ".tmp") -> Path:
    return path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}{suffix}")


def _date_clause(start_date: pd.Timestamp | None, end_date: pd.Timestamp | None, col_name: str = "date") -> str:
    clauses: list[str] = []
    if start_date is not None:
        clauses.append(f"CAST({col_name} AS DATE) >= DATE '{start_date.strftime('%Y-%m-%d')}'")
    if end_date is not None:
        clauses.append(f"CAST({col_name} AS DATE) <= DATE '{end_date.strftime('%Y-%m-%d')}'")
    if not clauses:
        return ""
    return "WHERE " + " AND ".join(clauses)


def build_prices_tri(
    start_date: pd.Timestamp | None,
    end_date: pd.Timestamp | None,
    output_path: Path,
    base_value: float = 100.0,
) -> BuildSummary:
    if not PRICES_PATH.exists():
        raise FileNotFoundError(f"Missing base prices parquet: {PRICES_PATH}")
    if float(base_value) <= 0.0:
        raise ValueError(f"base_value must be > 0, got {base_value}")

    has_patch = PATCH_PATH.exists()
    has_tickers = TICKERS_PATH.exists()

    base_where = _date_clause(start_date=start_date, end_date=end_date, col_name="date")
    patch_where = _date_clause(start_date=start_date, end_date=end_date, col_name="date")

    ticker_join_sql = (
        f"LEFT JOIN '{_sql_escape_path(TICKERS_PATH)}' t ON CAST(t.permno AS BIGINT) = wr.permno"
        if has_tickers
        else ""
    )
    ticker_select_sql = "t.ticker AS ticker" if has_tickers else "CAST(NULL AS VARCHAR) AS ticker"

    tri_query = f"""
        WITH src AS (
            SELECT
                CAST(date AS DATE) AS date,
                CAST(permno AS BIGINT) AS permno,
                CAST(raw_close AS DOUBLE) AS raw_close,
                CAST(adj_close AS DOUBLE) AS adj_close,
                CAST(total_ret AS DOUBLE) AS total_ret,
                CAST(volume AS DOUBLE) AS volume,
                0 AS priority
            FROM '{_sql_escape_path(PRICES_PATH)}'
            {base_where}
            {"UNION ALL" if has_patch else ""}
            {"SELECT CAST(date AS DATE) AS date, CAST(permno AS BIGINT) AS permno, CAST(raw_close AS DOUBLE) AS raw_close, CAST(adj_close AS DOUBLE) AS adj_close, CAST(total_ret AS DOUBLE) AS total_ret, CAST(volume AS DOUBLE) AS volume, 1 AS priority FROM '" + _sql_escape_path(PATCH_PATH) + "' " + patch_where if has_patch else ""}
        ),
        ranked AS (
            SELECT
                date,
                permno,
                raw_close,
                adj_close,
                total_ret,
                volume,
                ROW_NUMBER() OVER (PARTITION BY date, permno ORDER BY priority DESC) AS rn
            FROM src
        ),
        dedup AS (
            SELECT
                date,
                permno,
                raw_close,
                adj_close AS legacy_adj_close,
                total_ret,
                volume,
                CASE
                    WHEN total_ret IS NULL THEN 1.0
                    WHEN total_ret <= -1.0 THEN 0.0
                    ELSE 1.0 + total_ret
                END AS tri_factor
            FROM ranked
            WHERE rn = 1
        ),
        wr AS (
            SELECT
                date,
                permno,
                raw_close,
                legacy_adj_close,
                total_ret,
                volume,
                tri_factor,
                MAX(CASE WHEN tri_factor <= 0.0 THEN 1 ELSE 0 END) OVER (
                    PARTITION BY permno
                    ORDER BY date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS zero_hit,
                SUM(CASE WHEN tri_factor > 0.0 THEN LN(tri_factor) ELSE 0.0 END) OVER (
                    PARTITION BY permno
                    ORDER BY date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS log_cum
            FROM dedup
        )
        SELECT
            wr.date AS date,
            wr.permno AS permno,
            {ticker_select_sql},
            CAST(CASE
                WHEN wr.zero_hit = 1 THEN 0.0
                ELSE {float(base_value)} * EXP(wr.log_cum)
            END AS FLOAT) AS tri,
            CAST(wr.total_ret AS FLOAT) AS total_ret,
            CAST(wr.legacy_adj_close AS FLOAT) AS legacy_adj_close,
            CAST(wr.raw_close AS FLOAT) AS raw_close,
            CAST(wr.volume AS FLOAT) AS volume
        FROM wr
        {ticker_join_sql}
        ORDER BY wr.date, wr.permno
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = _tmp_path_for(output_path, suffix=".parquet.tmp")

    con = duckdb.connect()
    temp_dir = PROCESSED_DIR / "duckdb_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    con.execute(f"PRAGMA temp_directory='{_sql_escape_path(temp_dir)}'")
    try:
        con.execute(f"COPY ({tri_query}) TO '{_sql_escape_path(tmp_out)}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        _atomic_replace(tmp_out, output_path)

        row = con.execute(
            f"""
            SELECT
                COUNT(*) AS rows,
                MIN(CAST(date AS DATE)) AS min_date,
                MAX(CAST(date AS DATE)) AS max_date,
                MIN(CAST(tri AS DOUBLE)) AS tri_min,
                MAX(CAST(tri AS DOUBLE)) AS tri_max
            FROM '{_sql_escape_path(output_path)}'
            """
        ).fetchone()
    finally:
        con.close()
        if tmp_out.exists():
            try:
                tmp_out.unlink()
            except OSError:
                pass

    rows = int(row[0]) if row and row[0] is not None else 0
    min_date = "" if row is None or row[1] is None else pd.Timestamp(row[1]).strftime("%Y-%m-%d")
    max_date = "" if row is None or row[2] is None else pd.Timestamp(row[2]).strftime("%Y-%m-%d")
    tri_min = float(row[3]) if row and row[3] is not None else np.nan
    tri_max = float(row[4]) if row and row[4] is not None else np.nan

    return BuildSummary(
        output_path=output_path,
        rows=rows,
        start_date=min_date,
        end_date=max_date,
        tri_min=tri_min,
        tri_max=tri_max,
    )


def _load_ticker_window(
    con: duckdb.DuckDBPyConnection,
    tri_path: Path,
    ticker: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    return con.execute(
        f"""
        SELECT
            CAST(date AS DATE) AS date,
            CAST(tri AS DOUBLE) AS tri,
            CAST(legacy_adj_close AS DOUBLE) AS legacy_adj_close,
            CAST(total_ret AS DOUBLE) AS total_ret
        FROM '{_sql_escape_path(tri_path)}'
        WHERE UPPER(CAST(ticker AS VARCHAR)) = ?
          AND CAST(date AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
        ORDER BY date
        """,
        [ticker.upper(), start_date, end_date],
    ).df()


def build_validation_report(
    tri_path: Path,
    output_csv_path: Path,
    split_tolerance: float = 0.02,
) -> pd.DataFrame:
    if not tri_path.exists():
        raise FileNotFoundError(f"Missing TRI artifact: {tri_path}")

    records: list[dict[str, object]] = []
    con = duckdb.connect()
    try:
        for ticker, split_date_str, ratio in KNOWN_SPLITS:
            split_dt = pd.Timestamp(split_date_str)
            window_start = (split_dt - pd.Timedelta(days=5)).strftime("%Y-%m-%d")
            window_end = (split_dt + pd.Timedelta(days=5)).strftime("%Y-%m-%d")
            window = _load_ticker_window(
                con=con,
                tri_path=tri_path,
                ticker=ticker,
                start_date=window_start,
                end_date=window_end,
            )
            if window.empty:
                records.append(
                    {
                        "check_type": "split_continuity",
                        "ticker": ticker,
                        "event_date": split_date_str,
                        "metric": "window_rows",
                        "value": 0.0,
                        "pass": False,
                        "notes": f"missing data for known split ratio {ratio}",
                    }
                )
                continue

            window["date"] = pd.to_datetime(window["date"], errors="coerce")
            pre = window.loc[window["date"] < split_dt]
            post = window.loc[window["date"] >= split_dt]
            if pre.empty or post.empty:
                records.append(
                    {
                        "check_type": "split_continuity",
                        "ticker": ticker,
                        "event_date": split_date_str,
                        "metric": "continuity_pct",
                        "value": np.nan,
                        "pass": False,
                        "notes": "insufficient pre/post rows around split date",
                    }
                )
                continue

            tri_pre = float(pre["tri"].iloc[-1])
            tri_post = float(post["tri"].iloc[0])
            legacy_pre = float(pre["legacy_adj_close"].iloc[-1])
            legacy_post = float(post["legacy_adj_close"].iloc[0])
            expected_pct = float(post["total_ret"].iloc[0]) if "total_ret" in post.columns else np.nan
            tri_pct = (tri_post / tri_pre - 1.0) if np.isfinite(tri_pre) and tri_pre != 0.0 else np.nan
            legacy_pct = (
                (legacy_post / legacy_pre - 1.0) if np.isfinite(legacy_pre) and legacy_pre != 0.0 else np.nan
            )
            if np.isfinite(expected_pct):
                continuity_ok = bool(np.isfinite(tri_pct) and abs(tri_pct - expected_pct) <= max(0.005, float(split_tolerance) * 0.25))
                metric_name = "tri_minus_total_ret"
                metric_value = tri_pct - expected_pct if np.isfinite(tri_pct) else np.nan
            else:
                continuity_ok = bool(np.isfinite(tri_pct) and abs(tri_pct) < float(split_tolerance))
                metric_name = "tri_pct_change"
                metric_value = tri_pct

            records.append(
                {
                    "check_type": "split_continuity",
                    "ticker": ticker,
                    "event_date": split_date_str,
                    "metric": metric_name,
                    "value": metric_value,
                    "pass": continuity_ok,
                    "notes": f"tri_pct_change={tri_pct:.6f}; expected_ret={expected_pct:.6f}; legacy_pct_change={legacy_pct:.6f}; split_ratio={ratio}",
                }
            )

        for ticker in DIVIDEND_TICKERS:
            df = con.execute(
                f"""
                SELECT
                    CAST(date AS DATE) AS date,
                    CAST(tri AS DOUBLE) AS tri,
                    CAST(legacy_adj_close AS DOUBLE) AS legacy_adj_close
                FROM '{_sql_escape_path(tri_path)}'
                WHERE UPPER(CAST(ticker AS VARCHAR)) = ?
                ORDER BY date DESC
                LIMIT 260
                """,
                [ticker.upper()],
            ).df()

            if len(df) < 252:
                records.append(
                    {
                        "check_type": "dividend_capture",
                        "ticker": ticker,
                        "event_date": "",
                        "metric": "rows",
                        "value": float(len(df)),
                        "pass": False,
                        "notes": "insufficient trailing rows (<252)",
                    }
                )
                continue

            df = df.sort_values("date").reset_index(drop=True)
            tri_ret = float(df["tri"].iloc[-1] / df["tri"].iloc[0] - 1.0)
            legacy_ret = float(df["legacy_adj_close"].iloc[-1] / df["legacy_adj_close"].iloc[0] - 1.0)
            records.append(
                {
                    "check_type": "dividend_capture",
                    "ticker": ticker,
                    "event_date": "",
                    "metric": "tri_minus_legacy_1y",
                    "value": tri_ret - legacy_ret,
                    "pass": bool(np.isfinite(tri_ret) and np.isfinite(legacy_ret) and tri_ret >= legacy_ret),
                    "notes": f"tri_1y={tri_ret:.6f}; legacy_1y={legacy_ret:.6f}",
                }
            )

        if MACRO_TRI_PATH.exists():
            diff_row = con.execute(
                f"""
                WITH px AS (
                    SELECT CAST(date AS DATE) AS date, CAST(tri AS DOUBLE) AS tri
                    FROM '{_sql_escape_path(tri_path)}'
                    WHERE CAST(permno AS BIGINT) = {SPY_PERMNO}
                ),
                mx AS (
                    SELECT CAST(date AS DATE) AS date, CAST(spy_tri AS DOUBLE) AS spy_tri
                    FROM '{_sql_escape_path(MACRO_TRI_PATH)}'
                )
                SELECT MAX(ABS(px.tri - mx.spy_tri)) AS max_abs_diff
                FROM px
                INNER JOIN mx ON px.date = mx.date
                """
            ).fetchone()
            max_diff = float(diff_row[0]) if diff_row and diff_row[0] is not None else np.nan
            records.append(
                {
                    "check_type": "macro_consistency",
                    "ticker": "SPY",
                    "event_date": "",
                    "metric": "max_abs_diff_spy_tri",
                    "value": max_diff,
                    "pass": bool(np.isfinite(max_diff) and max_diff < 1e-6),
                    "notes": "comparison vs macro_features_tri.spy_tri",
                }
            )
    finally:
        con.close()

    report = pd.DataFrame(records)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = _tmp_path_for(output_csv_path, suffix=".csv.tmp")
    try:
        report.to_csv(tmp, index=False)
        _atomic_replace(tmp, output_csv_path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    return report


def build_split_plot(
    tri_path: Path,
    output_plot_path: Path,
) -> bool:
    con = duckdb.connect()
    try:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            plt = None

        if plt is not None:
            fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharex=False)
            axes_list = axes.flatten()
            for i, (ticker, split_date_str, ratio) in enumerate(KNOWN_SPLITS):
                ax = axes_list[i]
                split_dt = pd.Timestamp(split_date_str)
                start = (split_dt - pd.Timedelta(days=45)).strftime("%Y-%m-%d")
                end = (split_dt + pd.Timedelta(days=45)).strftime("%Y-%m-%d")
                df = _load_ticker_window(
                    con=con,
                    tri_path=tri_path,
                    ticker=ticker,
                    start_date=start,
                    end_date=end,
                )
                if df.empty:
                    ax.text(0.5, 0.5, f"{ticker}: no data", ha="center", va="center")
                    ax.set_title(f"{ticker} {split_date_str}")
                    continue

                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date"]).sort_values("date")
                tri = pd.to_numeric(df["tri"], errors="coerce")
                legacy = pd.to_numeric(df["legacy_adj_close"], errors="coerce")

                tri0 = float(tri.dropna().iloc[0]) if tri.dropna().size else np.nan
                legacy0 = float(legacy.dropna().iloc[0]) if legacy.dropna().size else np.nan
                tri_norm = tri / tri0 if np.isfinite(tri0) and tri0 != 0.0 else tri
                legacy_norm = legacy / legacy0 if np.isfinite(legacy0) and legacy0 != 0.0 else legacy

                ax.plot(df["date"], tri_norm, label="TRI", color="#1f77b4", linewidth=1.8)
                ax.plot(df["date"], legacy_norm, label="legacy_adj_close", color="#d62728", linewidth=1.2)
                ax.axvline(split_dt, color="#2ca02c", linestyle="--", linewidth=1.1)
                ax.set_title(f"{ticker} split {ratio:.1f}:1 ({split_date_str})")
                ax.grid(alpha=0.2)
                ax.legend(loc="best", fontsize=8)

            fig.suptitle("Phase 18 Day 2 — Split Event Continuity (TRI vs legacy_adj_close)")
            fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.97])

            output_plot_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = _tmp_path_for(output_plot_path, suffix=".png.tmp")
            try:
                fig.savefig(tmp, dpi=150)
                _atomic_replace(tmp, output_plot_path)
            finally:
                plt.close(fig)
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except OSError:
                        pass
            return True

        try:
            from PIL import Image, ImageDraw
        except ImportError:
            return False

        width, height = 1500, 900
        pad = 24
        panel_w = (width - pad * 3) // 2
        panel_h = (height - pad * 3) // 2

        img = Image.new("RGB", (width, height), color=(248, 249, 251))
        draw = ImageDraw.Draw(img)
        draw.text((pad, 6), "Phase 18 Day 2 — Split Event Continuity (TRI vs legacy_adj_close)", fill=(20, 20, 20))

        for i, (ticker, split_date_str, ratio) in enumerate(KNOWN_SPLITS):
            row = i // 2
            col = i % 2
            x0 = pad + col * (panel_w + pad)
            y0 = pad + row * (panel_h + pad) + 22
            x1 = x0 + panel_w
            y1 = y0 + panel_h
            draw.rectangle([x0, y0, x1, y1], outline=(150, 150, 150), width=1)
            draw.text((x0 + 6, y0 + 4), f"{ticker} split {ratio:.1f}:1 ({split_date_str})", fill=(40, 40, 40))

            split_dt = pd.Timestamp(split_date_str)
            start = (split_dt - pd.Timedelta(days=45)).strftime("%Y-%m-%d")
            end = (split_dt + pd.Timedelta(days=45)).strftime("%Y-%m-%d")
            df = _load_ticker_window(
                con=con,
                tri_path=tri_path,
                ticker=ticker,
                start_date=start,
                end_date=end,
            )
            if df.empty:
                draw.text((x0 + 12, y0 + 28), "No data in split window", fill=(120, 40, 40))
                continue

            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
            tri = pd.to_numeric(df["tri"], errors="coerce")
            legacy = pd.to_numeric(df["legacy_adj_close"], errors="coerce")
            tri0 = float(tri.dropna().iloc[0]) if tri.dropna().size else np.nan
            legacy0 = float(legacy.dropna().iloc[0]) if legacy.dropna().size else np.nan
            tri_norm = tri / tri0 if np.isfinite(tri0) and tri0 != 0.0 else tri
            legacy_norm = legacy / legacy0 if np.isfinite(legacy0) and legacy0 != 0.0 else legacy

            vals = pd.concat([tri_norm, legacy_norm], axis=0).replace([np.inf, -np.inf], np.nan).dropna()
            if vals.empty:
                draw.text((x0 + 12, y0 + 28), "Series unavailable", fill=(120, 40, 40))
                continue
            y_min = float(vals.min())
            y_max = float(vals.max())
            if y_max <= y_min:
                y_max = y_min + 1.0
            n = len(df)
            inner_left = x0 + 10
            inner_right = x1 - 10
            inner_top = y0 + 26
            inner_bottom = y1 - 10

            def _x(ii: int) -> int:
                if n <= 1:
                    return inner_left
                return int(inner_left + (ii / (n - 1)) * (inner_right - inner_left))

            def _y(v: float) -> int:
                return int(inner_bottom - ((v - y_min) / (y_max - y_min)) * (inner_bottom - inner_top))

            tri_pts = []
            legacy_pts = []
            for ii in range(n):
                tv = tri_norm.iloc[ii]
                lv = legacy_norm.iloc[ii]
                if np.isfinite(tv):
                    tri_pts.append((_x(ii), _y(float(tv))))
                if np.isfinite(lv):
                    legacy_pts.append((_x(ii), _y(float(lv))))
            if len(tri_pts) >= 2:
                draw.line(tri_pts, fill=(31, 119, 180), width=2)
            if len(legacy_pts) >= 2:
                draw.line(legacy_pts, fill=(214, 39, 40), width=2)

            split_idx = np.searchsorted(df["date"].to_numpy(), np.datetime64(split_dt), side="left")
            split_idx = int(min(max(split_idx, 0), max(n - 1, 0)))
            split_x = _x(split_idx)
            draw.line([(split_x, inner_top), (split_x, inner_bottom)], fill=(44, 160, 44), width=1)

            draw.text((x0 + 10, y1 - 20), "Blue=TRI  Red=legacy  Green=split date", fill=(70, 70, 70))

        output_plot_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = _tmp_path_for(output_plot_path, suffix=".png.tmp")
        try:
            img.save(tmp, format="PNG")
            _atomic_replace(tmp, output_plot_path)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass
    finally:
        con.close()
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build prices_tri.parquet from total_ret.")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE, help="Date floor (YYYY-MM-DD).")
    parser.add_argument("--end-date", default=DEFAULT_END_DATE, help="Date ceiling (YYYY-MM-DD).")
    parser.add_argument("--base-value", type=float, default=100.0, help="TRI starting value.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Output TRI parquet path.")
    parser.add_argument(
        "--validation-csv",
        default=str(DEFAULT_VALIDATION_CSV),
        help="Validation CSV output path.",
    )
    parser.add_argument(
        "--split-plot",
        default=str(DEFAULT_SPLIT_PLOT),
        help="Split continuity PNG output path.",
    )
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation CSV generation.")
    parser.add_argument("--skip-plot", action="store_true", help="Skip split-event plot generation.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start_date = _to_timestamp(args.start_date)
    end_date = _to_timestamp(args.end_date)
    if start_date is not None and end_date is not None and end_date < start_date:
        raise ValueError("end_date must be >= start_date")

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    print("=" * 72)
    print("Phase 18 Day 2: Build prices_tri.parquet")
    print("=" * 72)
    print(f"Window: {start_date.strftime('%Y-%m-%d') if start_date else 'min'} -> {end_date.strftime('%Y-%m-%d') if end_date else 'max'}")
    print(f"Output: {output_path}")

    summary = build_prices_tri(
        start_date=start_date,
        end_date=end_date,
        output_path=output_path,
        base_value=float(args.base_value),
    )
    print(f"Rows: {summary.rows:,}")
    print(f"Date range: {summary.start_date} -> {summary.end_date}")
    print(f"TRI range: min={summary.tri_min:.6f} max={summary.tri_max:.6f}")

    if not args.skip_validation:
        validation_csv = Path(args.validation_csv)
        if not validation_csv.is_absolute():
            validation_csv = PROJECT_ROOT / validation_csv
        report = build_validation_report(
            tri_path=output_path,
            output_csv_path=validation_csv,
        )
        passed = int(pd.to_numeric(report["pass"], errors="coerce").fillna(False).astype(bool).sum()) if not report.empty else 0
        total = int(len(report))
        print(f"Validation CSV: {validation_csv} ({passed}/{total} checks passed)")
    else:
        print("Validation CSV: skipped")

    if not args.skip_plot:
        split_plot = Path(args.split_plot)
        if not split_plot.is_absolute():
            split_plot = PROJECT_ROOT / split_plot
        ok = build_split_plot(tri_path=output_path, output_plot_path=split_plot)
        if ok:
            print(f"Split plot: {split_plot}")
        else:
            print("Split plot: skipped (matplotlib not available)")
    else:
        print("Split plot: skipped")

    print("=" * 72)
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
