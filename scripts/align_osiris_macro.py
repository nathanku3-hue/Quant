from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr

INPUT_PATH = Path("data/processed/osiris_global_hardware_daily.parquet")
OUTPUT_PATH = Path("data/processed/osiris_aligned_macro.parquet")


def _atomic_write_parquet(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=".parquet",
        prefix=f".{output_path.stem}.",
        dir=output_path.parent,
        delete=False,
    ) as tmp:
        temp_path = Path(tmp.name)
    try:
        df.to_parquet(temp_path, index=False)
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def align_osiris_macro(input_path: Path = INPUT_PATH, output_path: Path = OUTPUT_PATH) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    src = pd.read_parquet(input_path).copy()
    if src.empty:
        raise ValueError(f"Input is empty: {input_path}")

    src["closdate"] = pd.to_datetime(src["closdate"], errors="coerce")
    src["median_inv_turnover"] = pd.to_numeric(src["median_inv_turnover"], errors="coerce")
    src = src.dropna(subset=["closdate", "median_inv_turnover"]).copy()

    # Public reporting lag assumption for signal availability.
    src["knowledge_date"] = src["closdate"] + pd.Timedelta(days=60)

    # Keep one signal value per knowledge_date for stable asof join.
    src = src.sort_values(["knowledge_date", "closdate"]).drop_duplicates(
        subset=["knowledge_date"], keep="last"
    )

    start_date = pd.Timestamp("2015-01-01")
    end_date = pd.Timestamp.today().normalize()
    calendar = pd.DataFrame({"date": pd.date_range(start=start_date, end=end_date, freq="B")})

    aligned = pd.merge_asof(
        calendar.sort_values("date"),
        src[["knowledge_date", "closdate", "median_inv_turnover", "n_companies"]].sort_values("knowledge_date"),
        left_on="date",
        right_on="knowledge_date",
        direction="backward",
    )
    aligned["median_inv_turnover"] = aligned["median_inv_turnover"].ffill()
    aligned["n_companies"] = aligned["n_companies"].ffill()

    rolling_mean = aligned["median_inv_turnover"].rolling(window=252, min_periods=252).mean()
    rolling_std = aligned["median_inv_turnover"].rolling(window=252, min_periods=252).std()
    aligned["median_inv_turnover_z252"] = (
        (aligned["median_inv_turnover"] - rolling_mean) / rolling_std.replace(0.0, np.nan)
    )

    aligned = aligned.rename(columns={"date": "fiscal_date"})
    _atomic_write_parquet(aligned, output_path)
    return aligned


def compute_ic(aligned: pd.DataFrame) -> tuple[float, float, int]:
    qqq = yf.download("QQQ", start="2015-01-01", progress=False, auto_adjust=False)
    if qqq is None or qqq.empty:
        raise RuntimeError("QQQ download returned no data.")

    if isinstance(qqq.columns, pd.MultiIndex):
        qqq.columns = qqq.columns.get_level_values(0)

    qqq.index = pd.to_datetime(qqq.index).tz_localize(None)
    qqq = qqq.sort_index()
    if "Close" not in qqq.columns:
        raise RuntimeError("QQQ data missing Close column.")

    qqq["qqq_fwd_ret_60d"] = qqq["Close"].shift(-60) / qqq["Close"] - 1.0
    qqq_signal = qqq[["qqq_fwd_ret_60d"]].copy()
    qqq_signal["fiscal_date"] = qqq_signal.index

    merged = aligned.merge(qqq_signal, on="fiscal_date", how="inner")
    merged = merged.dropna(subset=["median_inv_turnover_z252", "qqq_fwd_ret_60d"])
    if merged.empty:
        raise RuntimeError("No overlapping rows for IC computation.")

    ic, pval = spearmanr(merged["median_inv_turnover_z252"], merged["qqq_fwd_ret_60d"])
    return float(ic), float(pval), int(len(merged))


def main() -> None:
    print("Aligning Osiris macro signal to daily calendar...")
    aligned = align_osiris_macro()
    print(f"Saved aligned macro: {OUTPUT_PATH}")
    print(f"Aligned rows: {len(aligned)}")
    print(f"Aligned date range: {aligned['fiscal_date'].min().date()} -> {aligned['fiscal_date'].max().date()}")

    print("\nRunning QQQ 60D forward-return IC test (Spearman)...")
    try:
        ic, pval, n = compute_ic(aligned)
        print(f"Spearman Correlation (IC): {ic:.6f}")
        print(f"P-Value: {pval:.6g}")
        print(f"N (aligned observations): {n}")
    except Exception as exc:
        print(f"IC computation failed: {exc}")


if __name__ == "__main__":
    main()
