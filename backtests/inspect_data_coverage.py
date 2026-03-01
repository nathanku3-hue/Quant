"""
Phase 16.3 data-forensics coverage audit for features parquet.

Inputs:
  - data/processed/features.parquet

Outputs (atomic write):
  - data/processed/feature_coverage_daily.csv
  - data/processed/feature_coverage_yearly.csv
  - data/processed/feature_coverage_first_seen.csv
  - data/processed/feature_coverage_summary.csv
  - data/processed/feature_coverage_curve.png (optional; requires matplotlib)
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DEFAULT_FEATURES_PATH = PROCESSED_DIR / "features.parquet"
DEFAULT_DAILY_OUTPUT = PROCESSED_DIR / "feature_coverage_daily.csv"
DEFAULT_YEARLY_OUTPUT = PROCESSED_DIR / "feature_coverage_yearly.csv"
DEFAULT_FIRST_SEEN_OUTPUT = PROCESSED_DIR / "feature_coverage_first_seen.csv"
DEFAULT_SUMMARY_OUTPUT = PROCESSED_DIR / "feature_coverage_summary.csv"
DEFAULT_PLOT_OUTPUT = PROCESSED_DIR / "feature_coverage_curve.png"

IDENTIFIER_COLUMNS = {"date", "permno", "ticker"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit features.parquet historical coverage.")
    parser.add_argument("--features-path", default=str(DEFAULT_FEATURES_PATH))
    parser.add_argument("--start-date", default=None, help="Optional inclusive lower bound (YYYY-MM-DD).")
    parser.add_argument("--end-date", default=None, help="Optional inclusive upper bound (YYYY-MM-DD).")
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="Top-k rows for earliest coverage table in console output.",
    )
    return parser.parse_args()


def _resolve_path(value: str | None, default_path: Path | None = None) -> Path | None:
    if value is None:
        return default_path
    text = str(value).strip()
    if text == "" or text.lower() in {"none", "null"}:
        return None
    path = Path(text)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _parse_optional_date(raw: str | None, label: str) -> pd.Timestamp | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if text == "" or text.lower() in {"none", "null"}:
        return None
    ts = pd.to_datetime(text, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Invalid {label}: {raw}")
    return pd.Timestamp(ts).normalize()


def _normalize_date_series(raw: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(raw, errors="coerce", utc=True)
    return parsed.dt.tz_convert(None).dt.normalize()


def _format_date_series(raw: pd.Series) -> pd.Series:
    return pd.to_datetime(raw, errors="coerce").dt.strftime("%Y-%m-%d").fillna("")


def _atomic_csv_write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        df.to_csv(temp_path, index=False)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def infer_feature_columns(columns: list[str]) -> list[str]:
    return [col for col in columns if str(col) not in IDENTIFIER_COLUMNS]


def compute_valid_mask(features: pd.DataFrame, feature_columns: list[str]) -> pd.Series:
    if not feature_columns:
        return pd.Series(True, index=features.index, dtype=bool)
    return features[feature_columns].notna().any(axis=1)


def build_daily_coverage(valid_rows: pd.DataFrame) -> pd.DataFrame:
    columns = ["date", "valid_tickers", "valid_rows"]
    if valid_rows.empty:
        return pd.DataFrame(columns=columns)
    out = (
        valid_rows.groupby("date", sort=True)
        .agg(valid_tickers=("permno", "nunique"), valid_rows=("permno", "size"))
        .reset_index()
        .sort_values("date")
        .reset_index(drop=True)
    )
    return out[columns]


def build_yearly_coverage(daily: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "year",
        "min_valid_tickers",
        "median_valid_tickers",
        "max_valid_tickers",
        "first_date",
        "last_date",
    ]
    if daily.empty:
        return pd.DataFrame(columns=columns)

    work = daily.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.dropna(subset=["date"])
    if work.empty:
        return pd.DataFrame(columns=columns)

    work["year"] = work["date"].dt.year.astype(int)
    out = (
        work.groupby("year", sort=True)
        .agg(
            min_valid_tickers=("valid_tickers", "min"),
            median_valid_tickers=("valid_tickers", "median"),
            max_valid_tickers=("valid_tickers", "max"),
            first_date=("date", "min"),
            last_date=("date", "max"),
        )
        .reset_index()
        .sort_values("year")
        .reset_index(drop=True)
    )
    return out[columns]


def _first_non_null(raw: pd.Series) -> str:
    non_null = raw.dropna()
    if non_null.empty:
        return ""
    return str(non_null.iloc[0])


def build_first_seen(valid_rows: pd.DataFrame) -> pd.DataFrame:
    has_ticker = "ticker" in valid_rows.columns
    base_columns = ["permno", "first_date", "last_date", "active_days"]
    ordered_columns = ["permno", "ticker", "first_date", "last_date", "active_days"] if has_ticker else base_columns
    if valid_rows.empty:
        return pd.DataFrame(columns=ordered_columns)

    work = valid_rows.copy()
    work = work.sort_values(["permno", "date"]).reset_index(drop=True)
    out = (
        work.groupby("permno", sort=True)
        .agg(first_date=("date", "min"), last_date=("date", "max"), active_days=("date", "nunique"))
        .reset_index()
    )

    if has_ticker:
        ticker_df = work.groupby("permno", sort=True).agg(ticker=("ticker", _first_non_null)).reset_index()
        out = out.merge(ticker_df, on="permno", how="left")
        out = out[["permno", "ticker", "first_date", "last_date", "active_days"]]
    else:
        out = out[base_columns]

    out = out.sort_values(["first_date", "permno"]).reset_index(drop=True)
    return out


def build_summary(daily: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "date_start",
        "date_end",
        "total_days",
        "min_valid_tickers",
        "min_valid_tickers_date",
        "median_valid_tickers",
        "max_valid_tickers",
        "max_valid_tickers_date",
        "pct_days_valid_tickers_gt_0",
    ]
    if daily.empty:
        return pd.DataFrame(
            [
                {
                    "date_start": "",
                    "date_end": "",
                    "total_days": 0,
                    "min_valid_tickers": np.nan,
                    "min_valid_tickers_date": "",
                    "median_valid_tickers": np.nan,
                    "max_valid_tickers": np.nan,
                    "max_valid_tickers_date": "",
                    "pct_days_valid_tickers_gt_0": np.nan,
                }
            ],
            columns=columns,
        )

    work = daily.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if work.empty:
        return pd.DataFrame(
            [
                {
                    "date_start": "",
                    "date_end": "",
                    "total_days": 0,
                    "min_valid_tickers": np.nan,
                    "min_valid_tickers_date": "",
                    "median_valid_tickers": np.nan,
                    "max_valid_tickers": np.nan,
                    "max_valid_tickers_date": "",
                    "pct_days_valid_tickers_gt_0": np.nan,
                }
            ],
            columns=columns,
        )

    min_idx = int(work["valid_tickers"].idxmin())
    max_idx = int(work["valid_tickers"].idxmax())
    row = {
        "date_start": work["date"].min(),
        "date_end": work["date"].max(),
        "total_days": int(len(work)),
        "min_valid_tickers": float(work.loc[min_idx, "valid_tickers"]),
        "min_valid_tickers_date": work.loc[min_idx, "date"],
        "median_valid_tickers": float(work["valid_tickers"].median()),
        "max_valid_tickers": float(work.loc[max_idx, "valid_tickers"]),
        "max_valid_tickers_date": work.loc[max_idx, "date"],
        "pct_days_valid_tickers_gt_0": float((work["valid_tickers"] > 0).mean() * 100.0),
    }
    return pd.DataFrame([row], columns=columns)


def compute_hockey_stick_ratio(daily: pd.DataFrame) -> float | None:
    if daily.empty:
        return None
    work = daily.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if work.empty:
        return None

    min_date = work["date"].min()
    max_date = work["date"].max()
    first_window_end = min_date + pd.DateOffset(years=2) - pd.Timedelta(days=1)
    last_window_start = max_date - pd.DateOffset(years=2) + pd.Timedelta(days=1)

    first_window = work[(work["date"] >= min_date) & (work["date"] <= first_window_end)]
    last_window = work[(work["date"] >= last_window_start) & (work["date"] <= max_date)]
    if first_window.empty or last_window.empty:
        return None

    first_median = float(first_window["valid_tickers"].median())
    last_median = float(last_window["valid_tickers"].median())
    if not np.isfinite(first_median) or not np.isfinite(last_median):
        return None
    if first_median == 0.0:
        return float("inf") if last_median > 0.0 else float("nan")
    return float(last_median / first_median)


def _build_plot(daily: pd.DataFrame, path: Path) -> bool:
    if daily.empty:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f"WARNING: matplotlib unavailable; skipping plot ({exc})")
        return False

    temp_path = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    fig = None
    try:
        plot_df = daily.copy()
        plot_df["date"] = pd.to_datetime(plot_df["date"], errors="coerce")
        plot_df = plot_df.dropna(subset=["date"]).sort_values("date")
        if plot_df.empty:
            return False

        path.parent.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(11, 4))
        ax.plot(plot_df["date"], plot_df["valid_tickers"], color="#1f77b4", linewidth=1.8)
        ax.set_title("Feature Coverage Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Valid Tickers")
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(temp_path, dpi=140)
        os.replace(temp_path, path)
        return True
    except Exception as exc:
        print(f"WARNING: plot write failed; continuing without plot ({exc})")
        return False
    finally:
        if fig is not None:
            try:
                import matplotlib.pyplot as plt

                plt.close(fig)
            except Exception:
                pass
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def _to_output_frames(
    daily: pd.DataFrame,
    yearly: pd.DataFrame,
    first_seen: pd.DataFrame,
    summary: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    daily_out = daily.copy()
    if "date" in daily_out.columns:
        daily_out["date"] = _format_date_series(daily_out["date"])

    yearly_out = yearly.copy()
    for col in ("first_date", "last_date"):
        if col in yearly_out.columns:
            yearly_out[col] = _format_date_series(yearly_out[col])

    first_seen_out = first_seen.copy()
    for col in ("first_date", "last_date"):
        if col in first_seen_out.columns:
            first_seen_out[col] = _format_date_series(first_seen_out[col])

    summary_out = summary.copy()
    for col in ("date_start", "date_end", "min_valid_tickers_date", "max_valid_tickers_date"):
        if col in summary_out.columns:
            summary_out[col] = _format_date_series(summary_out[col])
    return daily_out, yearly_out, first_seen_out, summary_out


def _print_console_summary(
    daily: pd.DataFrame,
    first_seen: pd.DataFrame,
    summary: pd.DataFrame,
    top_k: int,
) -> None:
    if daily.empty:
        print("Coverage rows after filters: 0")
        print("No valid rows detected; outputs contain empty tables.")
        print("Hockey-stick ratio (last2y/first2y median valid_tickers): n/a")
        return

    date_start = pd.to_datetime(daily["date"], errors="coerce").min()
    date_end = pd.to_datetime(daily["date"], errors="coerce").max()
    min_coverage = float(daily["valid_tickers"].min())
    median_coverage = float(daily["valid_tickers"].median())
    max_coverage = float(daily["valid_tickers"].max())
    pct_positive = float((daily["valid_tickers"] > 0).mean() * 100.0)
    ratio = compute_hockey_stick_ratio(daily)

    print("Feature coverage audit")
    print(
        "Date span: "
        f"{date_start.strftime('%Y-%m-%d') if pd.notna(date_start) else 'n/a'} -> "
        f"{date_end.strftime('%Y-%m-%d') if pd.notna(date_end) else 'n/a'} "
        f"({len(daily)} trading days)"
    )
    print(
        "valid_tickers min/median/max: "
        f"{int(min_coverage)} / {median_coverage:.1f} / {int(max_coverage)}"
    )
    print(f"Pct days with valid_tickers > 0: {pct_positive:.2f}%")
    if ratio is None or not np.isfinite(ratio):
        if ratio is not None and np.isinf(ratio):
            print("Hockey-stick ratio (last2y/first2y median valid_tickers): inf")
        else:
            print("Hockey-stick ratio (last2y/first2y median valid_tickers): n/a")
    else:
        print(f"Hockey-stick ratio (last2y/first2y median valid_tickers): {ratio:.3f}")

    if top_k > 0 and not first_seen.empty:
        top = first_seen.sort_values(["first_date", "permno"]).head(top_k).copy()
        for col in ("first_date", "last_date"):
            if col in top.columns:
                top[col] = _format_date_series(top[col])
        print("")
        print(f"Earliest coverage entities (top {len(top)}):")
        print(top.to_string(index=False))

    if not summary.empty:
        row = summary.iloc[0].to_dict()
        print("")
        print(
            "Summary row: "
            f"min={row.get('min_valid_tickers', np.nan)}, "
            f"median={row.get('median_valid_tickers', np.nan)}, "
            f"max={row.get('max_valid_tickers', np.nan)}"
        )


def main() -> int:
    args = parse_args()
    if int(args.top_k) < 0:
        raise ValueError("--top-k must be >= 0.")

    features_path = _resolve_path(args.features_path, default_path=DEFAULT_FEATURES_PATH)
    if features_path is None:
        raise RuntimeError("Failed to resolve --features-path.")
    if not features_path.exists() or not features_path.is_file():
        raise FileNotFoundError(f"Missing feature parquet: {features_path}")

    start_date = _parse_optional_date(args.start_date, "--start-date")
    end_date = _parse_optional_date(args.end_date, "--end-date")
    if start_date is not None and end_date is not None and start_date > end_date:
        raise ValueError("--start-date must be <= --end-date.")

    features = pd.read_parquet(features_path)
    required_cols = {"date", "permno"}
    missing = required_cols.difference(set(features.columns))
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    features = features.copy()
    features["date"] = _normalize_date_series(features["date"])
    features["permno"] = pd.to_numeric(features["permno"], errors="coerce").astype("Int64")
    features = features.dropna(subset=["date", "permno"]).reset_index(drop=True)
    features["permno"] = features["permno"].astype(int)

    if start_date is not None:
        features = features[features["date"] >= start_date]
    if end_date is not None:
        features = features[features["date"] <= end_date]
    features = features.sort_values(["date", "permno"]).reset_index(drop=True)

    feature_columns = infer_feature_columns(list(features.columns))
    valid_mask = compute_valid_mask(features, feature_columns)
    valid_rows = features.loc[valid_mask].copy().reset_index(drop=True)

    daily = build_daily_coverage(valid_rows)
    yearly = build_yearly_coverage(daily)
    first_seen = build_first_seen(valid_rows)
    summary = build_summary(daily)

    daily_out, yearly_out, first_seen_out, summary_out = _to_output_frames(daily, yearly, first_seen, summary)
    _atomic_csv_write(daily_out, DEFAULT_DAILY_OUTPUT)
    _atomic_csv_write(yearly_out, DEFAULT_YEARLY_OUTPUT)
    _atomic_csv_write(first_seen_out, DEFAULT_FIRST_SEEN_OUTPUT)
    _atomic_csv_write(summary_out, DEFAULT_SUMMARY_OUTPUT)

    plot_written = _build_plot(daily, DEFAULT_PLOT_OUTPUT)
    _print_console_summary(daily=daily, first_seen=first_seen, summary=summary, top_k=int(args.top_k))

    print("")
    print(f"Wrote daily coverage: {DEFAULT_DAILY_OUTPUT}")
    print(f"Wrote yearly coverage: {DEFAULT_YEARLY_OUTPUT}")
    print(f"Wrote first-seen coverage: {DEFAULT_FIRST_SEEN_OUTPUT}")
    print(f"Wrote summary coverage: {DEFAULT_SUMMARY_OUTPUT}")
    if plot_written:
        print(f"Wrote coverage curve: {DEFAULT_PLOT_OUTPUT}")
    else:
        print("Coverage curve skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
