"""
pead_d1_sue_builder.py
======================
V2-PEAD-D1: Standardized Unexpected Earnings (SUE) Signal Builder
=================================================================

Builds a price-scaled SUE signal from comp_fundq (Compustat quarterly
fundamentals). This is a Compustat-only, PERMNO-free implementation.

Data contract:
  Input  : data/raw/wrds/comp_fundq.parquet
           Columns: gvkey, datadate, rdq, fyearq, fqtr,
                    epspxq, niq, saleq, atq, ceqq, cshoq, prccq, ajexq
  Output : data/processed/pead_d1_sue_signal.parquet
           Columns: gvkey, rdq, datadate, fyearq, fqtr,
                    adj_eps, adj_eps_t4, surprise,
                    prccq_lag1, cshoq_lag1, liquidity_pass,
                    sue_price_scaled, sue_std_scaled,
                    sue_price_scaled_clipped, n_prior_quarters, valid_sue

Methodology (academic standard for Compustat-only PEAD):
  1. Raw Compustat EPS:
       adj_eps = numeric epspxq
       (legacy column name retained for downstream compatibility; ajexq is
       not applied to EPS in this D1 contract)
  2. t-4 seasonal random-walk:
       surprise = adj_eps_t − adj_eps_{t-4}
       (requires exactly 4-quarter lag within same gvkey, not just any row-4)
  3. Price-scaled SUE (primary):
       sue_price_scaled = surprise / abs(prccq_{t-1})
       prccq_{t-1} = prior quarter's prccq (PIT price before announcement)
  4. Std-scaled SUE (secondary, for quintile robustness):
       rolling 8-quarter std of adj_eps within gvkey
       sue_std_scaled = surprise / rolling_std  (if std > 0)
  5. Clipped SUE:
       sue_price_scaled_clipped = sue_price_scaled capped within each RDQ
       cross-section at +/- 5 * std(sue_price_scaled). Missing/zero group
       std leaves the raw value unchanged.
  6. Liquidity flag:
       liquidity_pass = prccq_lag1 * cshoq_lag1 > 50
       (Compustat cshoq is in millions; flag only, no row drop)
  7. Filters applied:
       - rdq not null, rdq >= 2015-01-01
       - At least 4 prior quarters of adj_eps available for this gvkey
       - prccq_lag1 > 0.50 (penny stock filter)
       - Duplicates on (gvkey, rdq) → keep latest datadate before lag construction

Guardrails:
  - No CRSP, no PERMNO, no IBES — Compustat-only
  - No future data leakage: t-4 lag uses only prior fiscal quarters
  - RDQ is the event date anchor (public announcement date)
  - prccq is quarter-end price, NOT pre-announcement; use lag-1 for PIT
  - Do not use yfinance ^GSPC as benchmark (use Ken French or SPY TRI)

Usage:
    .venv/Scripts/python scripts/pead_d1_sue_builder.py
    .venv/Scripts/python scripts/pead_d1_sue_builder.py --dry-run
    .venv/Scripts/python scripts/pead_d1_sue_builder.py --start-date 2020-01-01
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FUNDQ_PATH = ROOT / "data" / "raw" / "wrds" / "comp_fundq.parquet"
OUT_PATH = ROOT / "data" / "processed" / "pead_d1_sue_signal.parquet"
MANIFEST_PATH = OUT_PATH.with_suffix(".parquet.manifest.json")

START_DATE = "2015-01-01"
MIN_PRICE = 0.50        # penny-stock floor for price denominator
MIN_PRIOR_Q = 4        # minimum prior quarters needed for t-4 lag
ROLLING_STD_WINDOW = 8  # quarters for std-scaled SUE denominator
SUE_CLIP_STD_MULTIPLE = 5.0
LIQUIDITY_MARKET_CAP_MIN_MILLIONS = 50.0
RAW_ABS_SUE_GT_5_MAX_SHARE = 0.005
CURRENT_VINTAGE_LIMITATION = (
    "Input fundamentals are a current-vintage Compustat extract that may include "
    "later restatements; strict point-in-time filing-vintage behavior and freedom "
    "from restatement hindsight are not established."
)


def load_fundq(path: Path, start_date: str) -> pd.DataFrame:
    print(f"[load] Reading {path}")
    df = pd.read_parquet(path)
    print(f"  raw rows: {len(df):,}  columns: {list(df.columns)}")

    required = {"gvkey", "datadate", "rdq", "fyearq", "fqtr",
                "epspxq", "prccq", "cshoq"}
    missing = required - set(df.columns)
    if missing:
        sys.exit(f"[error] Missing columns in comp_fundq: {missing}")

    df["rdq"] = pd.to_datetime(df["rdq"], errors="coerce")
    df["datadate"] = pd.to_datetime(df["datadate"], errors="coerce")

    before = len(df)
    df = df[df["rdq"].notna() & (df["rdq"] >= pd.Timestamp(start_date))]
    print(f"  after rdq filter (>= {start_date}): {len(df):,}  "
          f"(dropped {before - len(df):,})")
    return df


def build_quarter_key(df: pd.DataFrame) -> pd.DataFrame:
    """Encode fiscal year+quarter as a single sortable integer."""
    df = df.copy()
    df["fyearq"] = pd.to_numeric(df["fyearq"], errors="coerce")
    df["fqtr"] = pd.to_numeric(df["fqtr"], errors="coerce")
    df = df[df["fyearq"].notna() & df["fqtr"].notna()].copy()
    df["fy_int"] = df["fyearq"].astype(int)
    df["fq_int"] = df["fqtr"].astype(int)
    # Quarter sequence: year*4 + quarter_index (0-based)
    df["qseq"] = df["fy_int"] * 4 + (df["fq_int"] - 1)
    return df


def compute_adj_eps(df: pd.DataFrame) -> pd.DataFrame:
    """Keep raw numeric epspxq under the legacy adj_eps column name."""
    df = df.copy()
    df["epspxq"] = pd.to_numeric(df["epspxq"], errors="coerce")
    df["prccq"] = pd.to_numeric(df["prccq"], errors="coerce")
    df["cshoq"] = pd.to_numeric(df["cshoq"], errors="coerce")

    df["adj_eps"] = df["epspxq"]
    return df


def deduplicate_fundq(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate (gvkey, fyearq, fqtr) rows.
    Keep the row with the latest datadate (most recent restatement).
    """
    before = len(df)
    df = df.sort_values(["gvkey", "fyearq", "fqtr", "datadate"])
    df = df.drop_duplicates(subset=["gvkey", "fyearq", "fqtr"], keep="last")
    dropped = before - len(df)
    if dropped:
        print(f"  dedup (gvkey, fyearq, fqtr): dropped {dropped:,} rows "
              f"(kept latest datadate)")
    return df


def compute_t4_lag(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each gvkey, compute t-4 seasonal lag of adj_eps using qseq.
    Only assigns lag when qseq_{t} - qseq_{t-4} == 4 exactly (no gap).
    """
    df = df.sort_values(["gvkey", "qseq"]).copy()

    # Shift within gvkey by 4 positions
    df["adj_eps_t4_raw"] = df.groupby("gvkey")["adj_eps"].shift(4)
    df["qseq_t4_raw"] = df.groupby("gvkey")["qseq"].shift(4)
    df["prccq_lag1_raw"] = df.groupby("gvkey")["prccq"].shift(1)
    df["cshoq_lag1_raw"] = df.groupby("gvkey")["cshoq"].shift(1)

    # Validate: the lag must be exactly 4 quarters (no missing quarters in between)
    qseq_diff = df["qseq"] - df["qseq_t4_raw"]
    valid_t4 = qseq_diff == 4

    df["adj_eps_t4"] = df["adj_eps_t4_raw"].where(valid_t4)
    df["prccq_lag1"] = df["prccq_lag1_raw"]  # prior quarter price (PIT proxy)
    df["cshoq_lag1"] = df["cshoq_lag1_raw"]  # Compustat shares outstanding, millions

    # Count prior quarters available for each gvkey (cumcount, 0-based)
    df["n_prior_quarters"] = df.groupby("gvkey").cumcount()

    return df


def compute_rolling_std(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute rolling std of adj_eps over the prior ROLLING_STD_WINDOW quarters.
    Excludes current quarter (shift=1) to avoid lookahead.
    """
    df = df.sort_values(["gvkey", "qseq"]).copy()

    def _rolling_std_excl_current(s: pd.Series) -> pd.Series:
        return (
            s.shift(1)
             .rolling(window=ROLLING_STD_WINDOW, min_periods=4)
             .std()
        )

    df["eps_rolling_std"] = (
        df.groupby("gvkey")["adj_eps"]
          .transform(_rolling_std_excl_current)
    )
    return df


def compute_sue(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["surprise"] = df["adj_eps"] - df["adj_eps_t4"]

    # Price-scaled SUE (primary)
    price_denom = df["prccq_lag1"].abs()
    price_denom_ok = price_denom.notna() & (price_denom >= MIN_PRICE)
    df["sue_price_scaled"] = np.where(
        price_denom_ok,
        df["surprise"] / price_denom,
        np.nan,
    )

    # Std-scaled SUE (secondary)
    std_ok = df["eps_rolling_std"].notna() & (df["eps_rolling_std"] > 0)
    df["sue_std_scaled"] = np.where(
        std_ok,
        df["surprise"] / df["eps_rolling_std"],
        np.nan,
    )

    df["liquidity_pass"] = (
        df["prccq_lag1"] * df["cshoq_lag1"]
        > LIQUIDITY_MARKET_CAP_MIN_MILLIONS
    )

    # Validity flag
    df["valid_sue"] = (
        df["adj_eps_t4"].notna()
        & df["surprise"].notna()
        & price_denom_ok
        & (df["n_prior_quarters"] >= MIN_PRIOR_Q)
    )

    return df


def clip_sue_by_rdq(
    df: pd.DataFrame,
    *,
    source_col: str = "sue_price_scaled",
    output_col: str = "sue_price_scaled_clipped",
    rdq_col: str = "rdq",
    std_multiple: float = SUE_CLIP_STD_MULTIPLE,
) -> pd.DataFrame:
    """
    Cap a SUE column within each RDQ cross-section at +/- std_multiple * std.

    Missing or zero cross-sectional std leaves raw values unchanged.
    """
    df = df.copy()
    values = pd.to_numeric(df[source_col], errors="coerce")
    rdq_groups = df[rdq_col]
    group_std = values.groupby(rdq_groups).transform("std")
    threshold = group_std * std_multiple
    can_clip = values.notna() & threshold.notna() & (threshold > 0)
    clipped = values.clip(lower=-threshold, upper=threshold)
    df[output_col] = values.where(~can_clip, clipped)
    return df


def summarize_d1_quality(df: pd.DataFrame) -> dict[str, int | float]:
    """Return vectorized D1 quality metrics over valid SUE rows only."""
    valid_mask = df["valid_sue"].fillna(False).astype(bool)
    valid = df.loc[valid_mask]
    valid_rows = len(valid)

    raw_sue = pd.to_numeric(valid["sue_price_scaled"], errors="coerce")
    clipped_sue = pd.to_numeric(
        valid["sue_price_scaled_clipped"], errors="coerce"
    )
    raw_extreme_count = int(raw_sue.abs().gt(5.0).sum())
    clipped_count = int(
        (
            raw_sue.notna()
            & clipped_sue.notna()
            & raw_sue.ne(clipped_sue)
        ).sum()
    )
    liquidity_pass_count = int(
        valid["liquidity_pass"].fillna(False).astype(bool).sum()
    )

    def _share(count: int) -> float:
        return count / valid_rows if valid_rows else 0.0

    return {
        "valid_rows": valid_rows,
        "raw_abs_sue_gt_5_count": raw_extreme_count,
        "raw_abs_sue_gt_5_share": _share(raw_extreme_count),
        "clipped_count": clipped_count,
        "clipped_share": _share(clipped_count),
        "liquidity_pass_count": liquidity_pass_count,
        "liquidity_pass_share": _share(liquidity_pass_count),
    }


def enforce_d1_quality_gate(quality_metrics: dict[str, int | float]) -> None:
    """Fail closed when the valid-row raw SUE extreme share reaches the limit."""
    extreme_share = float(quality_metrics["raw_abs_sue_gt_5_share"])
    if extreme_share >= RAW_ABS_SUE_GT_5_MAX_SHARE:
        raise RuntimeError(
            "D1 quality gate failed: raw |SUE| > 5 share "
            f"{extreme_share:.8%} is >= "
            f"{RAW_ABS_SUE_GT_5_MAX_SHARE:.8%}"
        )


def deduplicate_rdq(df: pd.DataFrame) -> pd.DataFrame:
    """
    If a gvkey has multiple rows with the same rdq (e.g. amended filings),
    keep the row with the latest datadate.
    """
    before = len(df)
    df = df.sort_values(["gvkey", "rdq", "datadate"])
    df = df.drop_duplicates(subset=["gvkey", "rdq"], keep="last")
    dropped = before - len(df)
    if dropped:
        print(f"  dedup (gvkey, rdq): dropped {dropped:,} rows "
              f"(kept latest datadate per announcement date)")
    return df


def write_output(
    df: pd.DataFrame,
    out_path: Path,
    manifest_path: Path,
    dry_run: bool,
    quality_metrics: dict[str, int | float] | None = None,
) -> None:
    out_cols = [
        "gvkey", "rdq", "datadate", "fyearq", "fqtr",
        "adj_eps", "adj_eps_t4", "surprise",
        "prccq_lag1", "cshoq_lag1", "liquidity_pass",
        "sue_price_scaled", "sue_std_scaled", "sue_price_scaled_clipped",
        "n_prior_quarters", "valid_sue",
    ]
    out = df[out_cols].copy()
    if quality_metrics is None:
        quality_metrics = summarize_d1_quality(out)

    print(f"\n[output] Shape: {out.shape}")
    print(f"  valid_sue rows: {out['valid_sue'].sum():,}")
    print(f"  gvkeys: {out['gvkey'].nunique():,}")
    print(f"  rdq range: {out['rdq'].min().date()} → {out['rdq'].max().date()}")
    print(f"  sue_price_scaled non-null: {out['sue_price_scaled'].notna().sum():,}")

    # Distribution stats
    valid = out[out["valid_sue"]]
    if len(valid):
        q = valid["sue_price_scaled"].quantile([0.05, 0.25, 0.50, 0.75, 0.95])
        print(f"\n  SUE (price-scaled) quantiles [valid rows only]:")
        for pct, val in q.items():
            print(f"    p{int(pct*100):>2d}: {val:+.6f}")

    if dry_run:
        print("\n[dry-run] Skipping parquet write.")
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_out_path = _tmp_path_for(out_path)
    tmp_manifest_path = _tmp_path_for(manifest_path)
    try:
        out.to_parquet(tmp_out_path, index=False)
        os.replace(tmp_out_path, out_path)
    finally:
        tmp_out_path.unlink(missing_ok=True)
    print(f"\n[write] {out_path}  ({out_path.stat().st_size / 1e6:.2f} MB)")

    sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "1.0",
        "builder": "scripts/pead_d1_sue_builder.py",
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "parquet_file": out_path.name,
        "row_count": len(out),
        "valid_sue_count": int(out["valid_sue"].sum()),
        "gvkey_count": int(out["gvkey"].nunique()),
        "rdq_min": str(out["rdq"].min().date()),
        "rdq_max": str(out["rdq"].max().date()),
        "columns": list(out.columns),
        "sha256": sha256,
        "quality_metrics": quality_metrics,
        "limitations": [CURRENT_VINTAGE_LIMITATION],
        "methodology": {
            "eps_basis": "raw numeric epspxq (column name adj_eps retained for compatibility; ajexq not applied)",
            "sue_primary": "surprise / abs(prccq_lag1)",
            "sue_secondary": f"surprise / rolling_std(adj_eps, window={ROLLING_STD_WINDOW}q, shift=1)",
            "sue_clipped": f"sue_price_scaled clipped by rdq cross-section to +/- {SUE_CLIP_STD_MULTIPLE} * std(sue_price_scaled); missing/zero std leaves raw value",
            "liquidity_flag": f"liquidity_pass = prccq_lag1 * cshoq_lag1 > {LIQUIDITY_MARKET_CAP_MIN_MILLIONS}; cshoq is in millions; no row drop",
            "min_prior_quarters": MIN_PRIOR_Q,
            "min_price_denominator": MIN_PRICE,
            "t4_validation": "qseq_t - qseq_{t-4} == 4 exactly (no gap quarters)",
        },
        "data_source": {
            "input": "data/raw/wrds/comp_fundq.parquet",
            "permission_basis": "D0.4D_2026-06-18_accessible_true",
            "no_permno": True,
            "no_ibes": True,
            "benchmark": "NOT_INCLUDED — use Ken French Mkt-RF or local SPY TRI for PEAD D2+",
        },
        "guardrails": [
            "No PERMNO — Compustat GVKEY-only",
            "No IBES — Compustat epspxq random-walk model only",
            "No yfinance ^GSPC — not canonical total-return benchmark",
            "No future data: t-4 lag validated by qseq exact-4-step check",
            "PIT price: prccq_lag1 (prior quarter close, not post-announcement)",
            "Liquidity is a flag only; valid_sue does not require liquidity_pass",
            "Atomic output write: parquet temp file is replaced before manifest is written",
            CURRENT_VINTAGE_LIMITATION,
        ],
    }
    try:
        tmp_manifest_path.write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        os.replace(tmp_manifest_path, manifest_path)
    finally:
        tmp_manifest_path.unlink(missing_ok=True)
    print(f"[write] {manifest_path}")


def _tmp_path_for(path: Path) -> Path:
    return path.with_name(f"{path.stem}.tmp{path.suffix}")


def print_coverage_by_year(df: pd.DataFrame) -> None:
    valid = df[df["valid_sue"]].copy()
    valid["year"] = valid["rdq"].dt.year
    by_year = valid.groupby("year").agg(
        events=("gvkey", "count"),
        gvkeys=("gvkey", "nunique"),
        sue_null=("sue_price_scaled", lambda x: x.isna().sum()),
    ).reset_index()
    print("\n[coverage by year — valid SUE rows]")
    print(by_year.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="PEAD D1 SUE Signal Builder")
    parser.add_argument("--start-date", default=START_DATE,
                        help=f"Min rdq date (default: {START_DATE})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Compute but do not write output files")
    args = parser.parse_args()

    if not FUNDQ_PATH.exists():
        sys.exit(f"[error] comp_fundq not found: {FUNDQ_PATH}\n"
                 f"  Run local_wrds_pead_v2_fetcher.py first.")

    print("=" * 60)
    print("PEAD D1 SUE Signal Builder — V2-PEAD-D1")
    print(f"Input : {FUNDQ_PATH}")
    print(f"Output: {OUT_PATH}")
    print(f"Date filter: rdq >= {args.start_date}")
    print("=" * 60)

    df = load_fundq(FUNDQ_PATH, args.start_date)
    df = build_quarter_key(df)
    df = compute_adj_eps(df)
    df = deduplicate_fundq(df)
    df = deduplicate_rdq(df)
    df = compute_t4_lag(df)
    df = compute_rolling_std(df)
    df = compute_sue(df)
    df = clip_sue_by_rdq(df)

    if df.empty:
        sys.exit(
            "[error] No processed D1 SUE rows remain after filtering for "
            f"start date {args.start_date}; existing outputs were not touched."
        )

    quality_metrics = summarize_d1_quality(df)
    print("\n[D1 quality summary — valid rows]")
    for metric, value in quality_metrics.items():
        print(f"  {metric}: {value}")
    enforce_d1_quality_gate(quality_metrics)

    print_coverage_by_year(df)

    write_output(
        df,
        OUT_PATH,
        MANIFEST_PATH,
        dry_run=args.dry_run,
        quality_metrics=quality_metrics,
    )

    # Summary
    valid_count = int(df["valid_sue"].sum())
    total_count = len(df)
    coverage = valid_count / total_count if total_count else 0.0
    print(f"\n{'=' * 60}")
    print(f"DONE: {valid_count:,} valid SUE events / {total_count:,} total rows")
    print(f"Coverage: {coverage:.1%} of rdq-filtered quarters")
    print(f"\nNext step (D2): merge sue_signal with GVKEY-keyed daily prices")
    print(f"  comp_secd_2015_2019 + prices_daily_compustat → event returns")
    print(f"  Benchmark: Ken French Mkt-RF or local SPY TRI (NOT yfinance ^GSPC)")
    print(f"  Primary IID: resolve via cshoq*prccq selection before D2")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
