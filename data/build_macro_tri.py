"""
Phase 18 Day 2 — macro TRI extension builder.

Builds macro_features_tri.parquet by extending macro_features.parquet with
TRI-based price series and recomputed return-derived regime fields.
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
MACRO_FEATURES_PATH = PROCESSED_DIR / "macro_features.parquet"
PRICES_TRI_PATH = PROCESSED_DIR / "prices_tri.parquet"
DEFAULT_OUTPUT_PATH = PROCESSED_DIR / "macro_features_tri.parquet"

DEFAULT_START_DATE = "2015-01-01"
DEFAULT_END_DATE = "2024-12-31"
SPY_PERMNO = 84398


@dataclass(frozen=True)
class MacroTriSummary:
    output_path: Path
    rows: int
    start_date: str
    end_date: str
    max_abs_spy_diff: float


def _to_timestamp(value: str | None) -> pd.Timestamp | None:
    if value is None:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Invalid date: {value}")
    return pd.Timestamp(ts).normalize()


def _tmp_path_for(path: Path, suffix: str = ".tmp") -> Path:
    return path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}{suffix}")


def _atomic_write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = _tmp_path_for(path, suffix=".parquet.tmp")
    try:
        df.to_parquet(tmp, index=False)
        attempts = 8
        for i in range(attempts):
            try:
                os.replace(tmp, path)
                break
            except PermissionError:
                if i >= attempts - 1:
                    raise
                time.sleep(0.15 * (i + 1))
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _tri_from_price(price: pd.Series, base_value: float = 100.0) -> pd.Series:
    px = pd.to_numeric(price, errors="coerce")
    ret = px.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    factor = (1.0 + ret).clip(lower=0.0)
    tri = float(base_value) * factor.cumprod()
    return tri.astype("float64")


def _load_spy_tri_from_prices(
    start_date: pd.Timestamp | None,
    end_date: pd.Timestamp | None,
) -> pd.Series:
    if not PRICES_TRI_PATH.exists():
        return pd.Series(dtype="float64")

    con = duckdb.connect()
    try:
        clauses = [f"CAST(permno AS BIGINT) = {SPY_PERMNO}"]
        if start_date is not None:
            clauses.append(f"CAST(date AS DATE) >= DATE '{start_date.strftime('%Y-%m-%d')}'")
        if end_date is not None:
            clauses.append(f"CAST(date AS DATE) <= DATE '{end_date.strftime('%Y-%m-%d')}'")
        where_sql = " AND ".join(clauses)
        df = con.execute(
            f"""
            SELECT CAST(date AS DATE) AS date, CAST(tri AS DOUBLE) AS tri
            FROM '{str(PRICES_TRI_PATH).replace("\\", "/")}'
            WHERE {where_sql}
            ORDER BY date
            """
        ).df()
    finally:
        con.close()

    if df.empty:
        return pd.Series(dtype="float64")
    idx = pd.to_datetime(df["date"], errors="coerce")
    tri = pd.to_numeric(df["tri"], errors="coerce")
    s = pd.Series(tri.values, index=idx, name="spy_tri")
    s = s[~s.index.isna()].sort_index()
    return s


def build_macro_tri(
    input_path: Path,
    output_path: Path,
    start_date: pd.Timestamp | None,
    end_date: pd.Timestamp | None,
    base_value: float = 100.0,
) -> MacroTriSummary:
    if not input_path.exists():
        raise FileNotFoundError(f"Missing macro features parquet: {input_path}")
    if float(base_value) <= 0.0:
        raise ValueError(f"base_value must be > 0, got {base_value}")

    macro = pd.read_parquet(input_path)
    if macro.empty:
        raise RuntimeError(f"Macro source is empty: {input_path}")
    if "date" not in macro.columns:
        raise RuntimeError(f"Macro source is missing date column: {input_path}")

    macro = macro.copy()
    macro["date"] = pd.to_datetime(macro["date"], errors="coerce")
    macro = macro.dropna(subset=["date"]).sort_values("date").drop_duplicates(subset=["date"], keep="last")

    if start_date is not None:
        macro = macro[macro["date"] >= start_date]
    if end_date is not None:
        macro = macro[macro["date"] <= end_date]
    macro = macro.reset_index(drop=True)
    if macro.empty:
        raise RuntimeError("No macro rows in requested date window.")

    out = macro.copy()
    out = out.sort_values("date").reset_index(drop=True)
    idx = pd.DatetimeIndex(out["date"])

    spy_tri_from_prices = _load_spy_tri_from_prices(start_date=start_date, end_date=end_date)
    if not spy_tri_from_prices.empty:
        out = out.merge(
            spy_tri_from_prices.rename("spy_tri").reset_index().rename(columns={"index": "date"}),
            on="date",
            how="left",
        )
    else:
        if "spy_close" not in out.columns:
            raise RuntimeError("macro_features source is missing spy_close and no prices_tri fallback is available.")
        out["spy_tri"] = _tri_from_price(out["spy_close"], base_value=float(base_value)).values

    tri_sources = {
        "vix_level": "vix_tri",
        "mtum_px": "mtum_tri",
        "dxy_px": "dxy_tri",
    }
    for src_col, dst_col in tri_sources.items():
        if src_col in out.columns:
            out[dst_col] = _tri_from_price(out[src_col], base_value=float(base_value)).values
        else:
            out[dst_col] = np.nan

    spy_tri = pd.to_numeric(out["spy_tri"], errors="coerce")
    spy_ret = spy_tri.pct_change(fill_method=None)
    out["vix_proxy"] = (spy_ret.rolling(20, min_periods=20).std() * np.sqrt(252.0) * 100.0)

    mtum_tri = pd.to_numeric(out["mtum_tri"], errors="coerce")
    mtum_ret = mtum_tri.pct_change(fill_method=None)
    out["mtum_spy_corr_60d"] = mtum_ret.rolling(60, min_periods=60).corr(spy_ret)

    dxy_tri = pd.to_numeric(out["dxy_tri"], errors="coerce")
    dxy_ret = dxy_tri.pct_change(fill_method=None)
    out["dxy_spx_corr_20d"] = dxy_ret.rolling(20, min_periods=20).corr(spy_ret)

    # Keep compatibility with legacy consumers that still read spy_close.
    if "spy_close" not in out.columns:
        out["spy_close"] = np.nan
    out["spy_close"] = out["spy_close"].where(pd.to_numeric(out["spy_close"], errors="coerce").notna(), out["spy_tri"])

    for c in ("spy_tri", "vix_tri", "mtum_tri", "dxy_tri", "vix_proxy", "mtum_spy_corr_60d", "dxy_spx_corr_20d"):
        out[c] = pd.to_numeric(out[c], errors="coerce").astype("float32")

    _atomic_write_parquet(out, output_path)

    max_abs_spy_diff = np.nan
    if PRICES_TRI_PATH.exists():
        con = duckdb.connect()
        try:
            row = con.execute(
                f"""
                WITH px AS (
                    SELECT CAST(date AS DATE) AS date, CAST(tri AS DOUBLE) AS tri
                    FROM '{str(PRICES_TRI_PATH).replace("\\", "/")}'
                    WHERE CAST(permno AS BIGINT) = {SPY_PERMNO}
                ),
                mx AS (
                    SELECT CAST(date AS DATE) AS date, CAST(spy_tri AS DOUBLE) AS spy_tri
                    FROM '{str(output_path).replace("\\", "/")}'
                )
                SELECT MAX(ABS(px.tri - mx.spy_tri)) AS max_abs_diff
                FROM px
                INNER JOIN mx ON px.date = mx.date
                """
            ).fetchone()
            max_abs_spy_diff = float(row[0]) if row and row[0] is not None else np.nan
        finally:
            con.close()

    return MacroTriSummary(
        output_path=output_path,
        rows=int(len(out)),
        start_date=idx.min().strftime("%Y-%m-%d"),
        end_date=idx.max().strftime("%Y-%m-%d"),
        max_abs_spy_diff=max_abs_spy_diff,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build macro_features_tri.parquet from macro_features.parquet.")
    parser.add_argument("--input", default=str(MACRO_FEATURES_PATH), help="Input macro_features parquet path.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Output macro_features_tri parquet path.")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE, help="Date floor (YYYY-MM-DD).")
    parser.add_argument("--end-date", default=DEFAULT_END_DATE, help="Date ceiling (YYYY-MM-DD).")
    parser.add_argument("--base-value", type=float, default=100.0, help="TRI starting value.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    start_date = _to_timestamp(args.start_date)
    end_date = _to_timestamp(args.end_date)
    if start_date is not None and end_date is not None and end_date < start_date:
        raise ValueError("end_date must be >= start_date")

    print("=" * 72)
    print("Phase 18 Day 2: Build macro_features_tri.parquet")
    print("=" * 72)
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Window: {start_date.strftime('%Y-%m-%d') if start_date else 'min'} -> {end_date.strftime('%Y-%m-%d') if end_date else 'max'}")

    summary = build_macro_tri(
        input_path=input_path,
        output_path=output_path,
        start_date=start_date,
        end_date=end_date,
        base_value=float(args.base_value),
    )
    print(f"Rows: {summary.rows:,}")
    print(f"Date range: {summary.start_date} -> {summary.end_date}")
    if np.isfinite(summary.max_abs_spy_diff):
        print(f"SPY TRI max abs diff vs prices_tri: {summary.max_abs_spy_diff:.10f}")
    else:
        print("SPY TRI max abs diff vs prices_tri: n/a")
    print("=" * 72)
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
