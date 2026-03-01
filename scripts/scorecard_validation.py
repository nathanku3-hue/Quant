from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from strategies.company_scorecard import CompanyScorecard  # noqa: E402
from strategies.factor_specs import build_default_factor_specs  # noqa: E402


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_FEATURES_PATH = PROCESSED_DIR / "features.parquet"
DEFAULT_OUTPUT_VALIDATION_CSV = PROCESSED_DIR / "phase18_day4_scorecard_validation.csv"
DEFAULT_OUTPUT_SCORES_CSV = PROCESSED_DIR / "phase18_day4_company_scores.csv"


def _to_ts(value: str | None) -> pd.Timestamp | None:
    if value is None:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Invalid date value: {value}")
    return pd.Timestamp(ts).normalize()


def _resolve_path(value: str | None, default_path: Path) -> Path:
    if value is None:
        return default_path
    p = Path(value)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


def _sql_escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def _atomic_csv_write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    tries = 8
    try:
        df.to_csv(tmp, index=False)
        for i in range(tries):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if i >= tries - 1:
                    raise
                time.sleep(0.15 * (i + 1))
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _load_features_subset(
    features_path: Path,
    factor_columns: list[str],
    start_date: pd.Timestamp | None,
    end_date: pd.Timestamp | None,
) -> pd.DataFrame:
    if not features_path.exists():
        raise FileNotFoundError(f"Missing features parquet: {features_path}")

    con = duckdb.connect()
    try:
        desc = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{_sql_escape_path(features_path)}')").df()
        available = set(desc["column_name"].astype(str).tolist())
        select_cols = ["date", "permno"] + [c for c in factor_columns if c in available]
        select_sql = ", ".join([f'"{c}"' for c in select_cols])

        where = []
        if start_date is not None:
            where.append(f"CAST(date AS DATE) >= DATE '{start_date.strftime('%Y-%m-%d')}'")
        if end_date is not None:
            where.append(f"CAST(date AS DATE) <= DATE '{end_date.strftime('%Y-%m-%d')}'")
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        query = f"""
        SELECT {select_sql}
        FROM read_parquet('{_sql_escape_path(features_path)}')
        {where_sql}
        ORDER BY date, permno
        """
        df = con.execute(query).df()
    finally:
        con.close()

    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "permno"]).sort_values(["date", "permno"]).reset_index(drop=True)
    return df


def _adjacent_rank_corr(scores: pd.DataFrame) -> float:
    rows: list[float] = []
    for dt, grp in scores.groupby("date", sort=True):
        _ = dt
        grp = grp.copy()
        grp["rank"] = grp["score"].rank(method="average")
    dates = sorted(scores["date"].dropna().unique())
    for i in range(1, len(dates)):
        d0 = dates[i - 1]
        d1 = dates[i]
        g0 = scores[scores["date"] == d0][["permno", "score"]].copy()
        g1 = scores[scores["date"] == d1][["permno", "score"]].copy()
        if g0.empty or g1.empty:
            continue
        g0["r0"] = g0["score"].rank(method="average")
        g1["r1"] = g1["score"].rank(method="average")
        merged = g0[["permno", "r0"]].merge(g1[["permno", "r1"]], on="permno", how="inner")
        if len(merged) < 5:
            continue
        corr = merged["r0"].corr(merged["r1"], method="spearman")
        if np.isfinite(corr):
            rows.append(float(corr))
    return float(np.mean(rows)) if rows else np.nan


def _quartile_sigma_spread(scores: pd.DataFrame) -> float:
    vals: list[float] = []
    for _, grp in scores.groupby("date", sort=True):
        s = pd.to_numeric(grp["score"], errors="coerce")
        s = s.dropna()
        if len(s) < 8:
            continue
        q1 = s.quantile(0.75)
        q4 = s.quantile(0.25)
        top = s[s >= q1].mean()
        bot = s[s <= q4].mean()
        sigma = s.std(ddof=0)
        if np.isfinite(sigma) and sigma > 0:
            vals.append(float((top - bot) / sigma))
    return float(np.mean(vals)) if vals else np.nan


def _factor_balance(scores: pd.DataFrame, factor_names: list[str]) -> tuple[float, float]:
    contrib_cols = [f"{name}_contrib" for name in factor_names if f"{name}_contrib" in scores.columns]
    if not contrib_cols:
        return np.nan, np.nan
    abs_contrib = scores[contrib_cols].abs()
    denom = abs_contrib.sum(axis=1).replace(0.0, np.nan)
    shares = abs_contrib.div(denom, axis=0)
    max_share = float(shares.mean(skipna=True).max(skipna=True))
    min_share = float(shares.mean(skipna=True).min(skipna=True))
    return max_share, min_share


def build_validation_table(scores: pd.DataFrame, factor_names: list[str]) -> pd.DataFrame:
    if "score_valid" in scores.columns:
        coverage = float(pd.to_numeric(scores["score_valid"], errors="coerce").fillna(0).astype(bool).mean()) if len(scores) else 0.0
    else:
        coverage = float(scores["score"].notna().mean()) if len(scores) else 0.0
    max_share, min_share = _factor_balance(scores=scores, factor_names=factor_names)
    rank_corr = _adjacent_rank_corr(scores=scores[["date", "permno", "score"]])
    quartile_sigma = _quartile_sigma_spread(scores=scores[["date", "permno", "score"]])

    checks = [
        {
            "check": "score_coverage",
            "target": ">=0.95",
            "value": coverage,
            "pass": bool(np.isfinite(coverage) and coverage >= 0.95),
        },
        {
            "check": "factor_balance_max_share",
            "target": "<=0.60",
            "value": max_share,
            "pass": bool(np.isfinite(max_share) and max_share <= 0.60),
        },
        {
            "check": "factor_balance_min_share",
            "target": ">=0.10",
            "value": min_share,
            "pass": bool(np.isfinite(min_share) and min_share >= 0.10),
        },
        {
            "check": "adjacent_rank_correlation",
            "target": ">0.70",
            "value": rank_corr,
            "pass": bool(np.isfinite(rank_corr) and rank_corr > 0.70),
        },
        {
            "check": "quartile_spread_sigma",
            "target": ">2.0",
            "value": quartile_sigma,
            "pass": bool(np.isfinite(quartile_sigma) and quartile_sigma > 2.0),
        },
    ]
    return pd.DataFrame(checks)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 18 Day 4 scorecard validation")
    p.add_argument("--input-features", default=str(DEFAULT_FEATURES_PATH))
    p.add_argument("--start-date", default="2015-01-01")
    p.add_argument("--end-date", default="2024-12-31")
    p.add_argument(
        "--scoring-method",
        default="complete_case",
        choices=["complete_case", "partial", "impute_neutral"],
        help="Score validity/aggregation mode.",
    )
    p.add_argument("--output-validation-csv", default=str(DEFAULT_OUTPUT_VALIDATION_CSV))
    p.add_argument("--output-scores-csv", default=str(DEFAULT_OUTPUT_SCORES_CSV))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    start = _to_ts(args.start_date)
    end = _to_ts(args.end_date)
    if start is not None and end is not None and end < start:
        raise ValueError(f"end-date {end.date()} is earlier than start-date {start.date()}")

    features_path = _resolve_path(args.input_features, DEFAULT_FEATURES_PATH)
    output_validation_csv = _resolve_path(args.output_validation_csv, DEFAULT_OUTPUT_VALIDATION_CSV)
    output_scores_csv = _resolve_path(args.output_scores_csv, DEFAULT_OUTPUT_SCORES_CSV)

    specs = build_default_factor_specs()
    all_candidates = sorted({c for spec in specs for c in spec.candidate_columns})

    print("=" * 80)
    print("PHASE 18 DAY 4: COMPANY SCORECARD VALIDATION")
    print("=" * 80)
    print(f"Input: {features_path}")
    print(f"Window: {start.strftime('%Y-%m-%d')} -> {end.strftime('%Y-%m-%d')}")

    features = _load_features_subset(
        features_path=features_path,
        factor_columns=all_candidates,
        start_date=start,
        end_date=end,
    )
    if features.empty:
        raise RuntimeError("No feature rows found in selected window.")

    scorecard = CompanyScorecard(factor_specs=specs, scoring_method=args.scoring_method)
    scores, summary = scorecard.compute_scores(features_df=features)

    factor_names = [s.name for s in specs]
    validation = build_validation_table(scores=scores, factor_names=factor_names)
    _atomic_csv_write(scores, output_scores_csv)
    _atomic_csv_write(validation, output_validation_csv)

    print(
        f"Rows scored: {summary.n_rows:,} | Dates: {summary.n_dates:,} | "
        f"Coverage: {summary.coverage:.2%} | Method: {summary.scoring_method}"
    )
    if summary.missing_factor_columns:
        print("Missing factor families (fallback unresolved): " + ", ".join(summary.missing_factor_columns))
        raise RuntimeError(
            "Scorecard missing factor families: " + ", ".join(summary.missing_factor_columns)
        )

    print("\nValidation checks:")
    print(validation.to_string(index=False))
    print(f"\nScores CSV:      {output_scores_csv}")
    print(f"Validation CSV:  {output_validation_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
