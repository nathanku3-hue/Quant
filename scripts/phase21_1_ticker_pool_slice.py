from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.day5_ablation_report import _atomic_csv_write  # noqa: E402
from scripts.day5_ablation_report import _atomic_json_write  # noqa: E402
from scripts.day5_ablation_report import _resolve_path  # noqa: E402
from scripts.day5_ablation_report import _to_ts  # noqa: E402
from scripts.phase20_full_backtest import DEFAULT_FEATURES_PATH  # noqa: E402
from scripts.phase20_full_backtest import DEFAULT_LIQUIDITY_PATH  # noqa: E402
from scripts.phase20_full_backtest import DEFAULT_MACRO_FALLBACK_PATH  # noqa: E402
from scripts.phase20_full_backtest import DEFAULT_MACRO_FEATURES_PATH  # noqa: E402
from scripts.phase20_full_backtest import _load_features_window  # noqa: E402
from scripts.phase20_full_backtest import _load_regime_states  # noqa: E402
from strategies.company_scorecard import CompanyScorecard  # noqa: E402
from strategies.company_scorecard import build_phase20_conviction_frame  # noqa: E402
from strategies.production_config import PRODUCTION_CONFIG_V1  # noqa: E402

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_FUNDAMENTALS_PATH = PROCESSED_DIR / "daily_fundamentals_panel.parquet"
DEFAULT_OUTPUT_PATH = PROCESSED_DIR / "phase21_1_ticker_pool_sample.csv"
DEFAULT_SUMMARY_JSON = PROCESSED_DIR / "phase21_1_ticker_pool_summary.json"
DICTATORSHIP_MODE = "PATH1_STRICT"
DICTATORSHIP_MODE_OFF = "PATH1_DEPRECATED"
PATH1_DIRECTIVE_ID = "PATH1_SECTOR_CONTEXT_PRE_RANK"
SEED_TICKERS = ("MU", "CIEN", "COHR", "TER")
DEFENSIVE_TICKERS = {
    "PG",
    "KO",
    "PEP",
    "WMT",
    "COST",
    "CL",
    "KMB",
    "MO",
    "PM",
    "ABT",
    "ABBV",
    "BMY",
    "JNJ",
    "MRK",
    "PFE",
    "DUK",
    "SO",
    "NEE",
    "EXC",
    "XEL",
    "ED",
    "AEP",
    "T",
    "VZ",
    "KHC",
    "GIS",
}


def _known_context_mask(values: pd.Series) -> pd.Series:
    text = values.astype("string").str.strip()
    return text.notna() & (~text.str.upper().isin({"", "UNKNOWN", "NAN", "NONE", "<NA>"}))


def _mu_style_flags(df: pd.DataFrame) -> pd.Series:
    ticker_u = df["ticker"].astype(str).str.upper()
    capital_cycle = pd.to_numeric(df.get("capital_cycle_lag"), errors="coerce").fillna(0.0)
    resid_mom = pd.to_numeric(df.get("resid_mom_lag"), errors="coerce").fillna(0.0)
    revenue = pd.to_numeric(df.get("revenue_growth_lag"), errors="coerce").fillna(0.0)
    return ticker_u.isin(set(SEED_TICKERS)) | (
        (capital_cycle > 0.0) & (resid_mom > 0.0) & (revenue > 0.0)
    )


def _sql_escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def _load_fundamentals_window(
    fundamentals_path: Path,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    if not fundamentals_path.exists():
        return pd.DataFrame(columns=["date", "permno", "ebitda_ttm", "roic", "operating_margin_delta_q"])

    con = duckdb.connect()
    try:
        desc = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{_sql_escape_path(fundamentals_path)}')"
        ).df()
        available = set(desc["column_name"].astype(str).tolist())
        keep = ["date", "permno", "ebitda_ttm", "roic", "operating_margin_delta_q"]
        select_cols = [c for c in keep if c in available]
        if "date" not in select_cols or "permno" not in select_cols:
            return pd.DataFrame(columns=keep)

        select_sql = ", ".join([f'"{c}"' for c in select_cols])
        query = f"""
        SELECT {select_sql}
        FROM read_parquet('{_sql_escape_path(fundamentals_path)}')
        WHERE CAST(date AS DATE) >= DATE '{start_date.strftime('%Y-%m-%d')}'
          AND CAST(date AS DATE) <= DATE '{end_date.strftime('%Y-%m-%d')}'
        ORDER BY date, permno
        """
        df = con.execute(query).df()
    finally:
        con.close()

    if df.empty:
        return pd.DataFrame(columns=["date", "permno", "ebitda_ttm", "roic", "operating_margin_delta_q"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["permno"] = pd.to_numeric(df["permno"], errors="coerce")
    for col in ["ebitda_ttm", "roic", "operating_margin_delta_q"]:
        if col not in df.columns:
            df[col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["date", "permno"]).reset_index(drop=True)


def _select_sample_date(
    conviction: pd.DataFrame,
    as_of_date: pd.Timestamp,
    min_longs: int,
) -> pd.Timestamp:
    if "regime" not in conviction.columns:
        raise RuntimeError("Conviction frame missing required 'regime' column")

    eligible = conviction.loc[
        conviction["date"].le(as_of_date),
        ["date", "mahalanobis_distance", "pool_action", "regime"],
    ]
    if eligible.empty:
        raise RuntimeError(
            "No rows available for date <= as_of_date. "
            "Check feature coverage or widen date window."
        )

    valid = eligible.loc[eligible["mahalanobis_distance"].notna()]
    if valid.empty:
        raise RuntimeError(
            "No valid Mahalanobis outputs found up to as-of-date; aborting to avoid misleading sample artifacts."
        )

    stats = (
        valid.groupby("date", sort=True)
        .agg(
            long_n=("pool_action", lambda s: int((pd.Series(s).astype(str) == "LONG").sum())),
            regime=("regime", "first"),
        )
        .reset_index()
    )
    stats["regime"] = stats["regime"].astype(str).str.upper()

    for filt in [
        (stats["regime"].eq("GREEN") & stats["long_n"].ge(int(min_longs))),
        (stats["regime"].eq("GREEN") & stats["long_n"].gt(0)),
        stats["long_n"].gt(0),
    ]:
        sub = stats.loc[filt]
        if not sub.empty:
            return pd.Timestamp(sub["date"].max())
    return pd.Timestamp(stats["date"].max())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 21.1 ticker pool slice (Mahalanobis + shrinkage)"
    )
    parser.add_argument("--start-date", default="2015-01-01")
    parser.add_argument("--as-of-date", required=True)
    parser.add_argument("--input-features", default=str(DEFAULT_FEATURES_PATH))
    parser.add_argument("--input-fundamentals", default=str(DEFAULT_FUNDAMENTALS_PATH))
    parser.add_argument("--macro-path", default=None)
    parser.add_argument("--liquidity-path", default=str(DEFAULT_LIQUIDITY_PATH))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--output-summary-json", default=str(DEFAULT_SUMMARY_JSON))
    parser.add_argument("--top-longs", type=int, default=8)
    parser.add_argument("--short-excerpt", type=int, default=8)
    parser.add_argument("--dictatorship-mode", choices=["on", "off"], default="on")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dictatorship_mode = str(args.dictatorship_mode).strip().lower() == "on"
    dictatorship_mode_label = DICTATORSHIP_MODE if dictatorship_mode else DICTATORSHIP_MODE_OFF

    start = _to_ts(args.start_date)
    as_of = _to_ts(args.as_of_date)
    if start is None or as_of is None:
        raise ValueError("Both --start-date and --as-of-date must be valid dates")
    if as_of < start:
        raise ValueError(f"as-of-date {as_of.date()} is earlier than start-date {start.date()}")

    features_path = _resolve_path(args.input_features, DEFAULT_FEATURES_PATH)
    fundamentals_path = _resolve_path(args.input_fundamentals, DEFAULT_FUNDAMENTALS_PATH)
    macro_path = _resolve_path(
        args.macro_path,
        DEFAULT_MACRO_FEATURES_PATH if DEFAULT_MACRO_FEATURES_PATH.exists() else DEFAULT_MACRO_FALLBACK_PATH,
    )
    liquidity_path = _resolve_path(args.liquidity_path, DEFAULT_LIQUIDITY_PATH)
    output_csv = _resolve_path(args.output_csv, DEFAULT_OUTPUT_PATH)
    output_summary_json = _resolve_path(args.output_summary_json, DEFAULT_SUMMARY_JSON)

    extra_cols = [
        "ticker",
        "adj_close",
        "dist_sma20",
        "sma200",
        "yz_vol_20d",
        "atr_14d",
        "revenue_growth_q",
        "resid_mom_60d",
        "z_inventory_quality_proxy",
        "capital_cycle_score",
        "amihud_20d",
        "z_discipline_cond",
        "z_moat",
        "z_demand",
    ]
    features = _load_features_window(
        features_path=features_path,
        start_date=start,
        end_date=as_of,
        extra_columns=extra_cols,
    )
    if features.empty:
        raise RuntimeError("No features found for the requested date window")

    fundamentals = _load_fundamentals_window(
        fundamentals_path=fundamentals_path,
        start_date=start,
        end_date=as_of,
    )
    if not fundamentals.empty:
        fundamentals = fundamentals.sort_values(["date", "permno"]).drop_duplicates(
            subset=["date", "permno"],
            keep="last",
        )
        features = features.merge(fundamentals, on=["date", "permno"], how="left")
    else:
        features["ebitda_ttm"] = pd.NA
        features["roic"] = pd.NA
        features["operating_margin_delta_q"] = pd.NA

    feature_dates = pd.DatetimeIndex(sorted(features["date"].dropna().unique()))
    regime, _ = _load_regime_states(
        start_date=start,
        end_date=as_of,
        feature_dates=feature_dates,
        macro_path=macro_path,
        liquidity_path=liquidity_path,
    )

    scorecard = CompanyScorecard(
        factor_specs=list(PRODUCTION_CONFIG_V1.factor_specs),
        scoring_method=PRODUCTION_CONFIG_V1.scoring_method,
    )
    scores, _ = scorecard.compute_scores(features)
    conviction = build_phase20_conviction_frame(
        scores_df=scores,
        features_df=features,
        regime_by_date=regime,
        dictatorship_mode=dictatorship_mode,
    )
    if conviction.empty:
        raise RuntimeError("Conviction frame is empty")
    if "sector" not in conviction.columns:
        conviction["sector"] = "Unknown"
    if "industry" not in conviction.columns:
        conviction["industry"] = "Unknown"
    if "sector_context_source" not in conviction.columns:
        conviction["sector_context_source"] = "unknown"
    if "path1_sector_context_attached" not in conviction.columns:
        conviction["path1_sector_context_attached"] = _known_context_mask(
            conviction["sector"]
        ) | _known_context_mask(conviction["industry"])
    conviction["path1_sector_context_attached"] = (
        pd.Series(conviction["path1_sector_context_attached"], index=conviction.index)
        .fillna(False)
        .astype(bool)
    )
    conviction["path1_directive_id"] = PATH1_DIRECTIVE_ID
    conviction["DICTATORSHIP_MODE"] = dictatorship_mode_label

    sample_date = _select_sample_date(conviction, as_of_date=as_of, min_longs=int(args.top_longs))
    block = conviction[conviction["date"] == sample_date].copy()
    if block.empty:
        raise RuntimeError("Selected sample date produced no rows")
    valid_odds_rows = block.loc[
        pd.to_numeric(block.get("odds_score"), errors="coerce").notna()
        & pd.to_numeric(block.get("posterior_cyclical"), errors="coerce").notna()
        & pd.to_numeric(block.get("posterior_defensive"), errors="coerce").notna()
        & pd.to_numeric(block.get("posterior_junk"), errors="coerce").notna()
    ]
    odds_available = not valid_odds_rows.empty

    long_sort_cols = ["compounder_prob", "conviction_score", "score"]
    long_sort_asc = [False, False, False]
    if "odds_score" in block.columns and pd.to_numeric(block["odds_score"], errors="coerce").notna().any():
        long_sort_cols = ["odds_score", "compounder_prob", "conviction_score", "score"]
        long_sort_asc = [False, False, False, False]

    longs = (
        block[block["pool_action"] == "LONG"]
        .sort_values(long_sort_cols, ascending=long_sort_asc)
        .head(int(args.top_longs))
    )
    shorts = (
        block[block["pool_action"] == "SHORT"]
        .sort_values(["mahalanobis_distance", "conviction_score"], ascending=[False, True])
        .head(int(args.short_excerpt))
    )

    sample = pd.concat([longs, shorts], axis=0)
    if sample.empty:
        sample = (
            block.sort_values(["compounder_prob", "conviction_score", "score"], ascending=[False, False, False])
            .head(int(args.top_longs + args.short_excerpt))
            .copy()
        )
    if "odds_ratio" in sample.columns and pd.to_numeric(sample["odds_ratio"], errors="coerce").notna().any():
        sample["odds_ratio"] = pd.to_numeric(sample["odds_ratio"], errors="coerce")
    else:
        sample["odds_ratio"] = np.exp(
            pd.to_numeric(sample.get("odds_score"), errors="coerce").clip(lower=-50.0, upper=50.0)
        )
    if "path1_sector_context_attached" not in sample.columns:
        sample["path1_sector_context_attached"] = _known_context_mask(sample.get("sector", pd.Series(index=sample.index, dtype="object"))) | _known_context_mask(sample.get("industry", pd.Series(index=sample.index, dtype="object")))
    sample["path1_sector_context_attached"] = (
        pd.Series(sample["path1_sector_context_attached"], index=sample.index)
        .fillna(False)
        .astype(bool)
    )
    if "sector_context_source" not in sample.columns:
        sample["sector_context_source"] = "unknown"
    sample["path1_directive_id"] = PATH1_DIRECTIVE_ID
    sample["DICTATORSHIP_MODE"] = dictatorship_mode_label

    keep_cols = [
        "date",
        "ticker",
        "permno",
        "regime",
        "sector",
        "industry",
        "sector_context_source",
        "path1_sector_context_attached",
        "path1_directive_id",
        "DICTATORSHIP_MODE",
        "dictatorship_mode",
        "path1_feature_allow",
        "path1_feature_deny",
        "path1_residualization",
        "path1_sector_count",
        "path1_cov_resample",
        "path1_cov_resample_n",
        "path1_cov_resample_per_sector",
        "path1_cov_resample_seed",
        "score",
        "conviction_score",
        "mahalanobis_distance",
        "mahalanobis_k_cyc",
        "compounder_prob",
        "pool_action",
        "pool_long_candidate",
        "pool_short_candidate",
        "odds_score",
        "odds_ratio",
        "posterior_cyclical",
        "posterior_defensive",
        "posterior_junk",
        "posterior_negative",
        "defensive_cluster_id",
        "junk_cluster_id",
        "style_compounder_gate",
        "weak_quality_liquidity",
        "entry_gate",
        "avoid_or_short_flag",
        "leverage_mult",
        "leverage_multiplier",
        "sigma_continuous",
        "jump_veto_score",
        "asset_beta_lag",
        "portfolio_beta",
        "gross_exposure",
        "net_exposure",
        "short_borrow_balance",
        "borrow_cost_daily",
        "beta_scale_pre",
        "beta_scale_post",
        "position_weight_final",
        "shrinkage_method",
        "shrinkage_coeff",
        "centroid_source",
        "centroid_quarter",
        "centroid_knn_count",
        "centroid_seed_used",
        "centroid_seed_missing",
    ]
    for col in keep_cols:
        if col not in sample.columns:
            sample[col] = pd.NA
    sample = sample[keep_cols].copy()

    _atomic_csv_write(sample, output_csv)

    top_longs = longs.sort_values(
        long_sort_cols,
        ascending=long_sort_asc,
    ).head(int(args.top_longs))
    top_long_tickers = {str(t).upper() for t in top_longs["ticker"].dropna().astype(str)}
    block_tickers = {str(t).upper() for t in block["ticker"].dropna().astype(str)}
    available_seed = sorted(set(SEED_TICKERS).intersection(block_tickers))
    seed_in_top = sorted(set(SEED_TICKERS).intersection(top_long_tickers))
    required_seed_in_top = int(min(3, len(available_seed)))
    plug_tza_names = sorted(top_long_tickers.intersection({"TZA", "PLUG"}))
    plug_tza_count = int(len(plug_tza_names))
    tza_plug_out = not bool(plug_tza_names)
    seed_presence_pass = (len(seed_in_top) >= required_seed_in_top)

    defensive_in_top = sorted(top_long_tickers.intersection(DEFENSIVE_TICKERS))
    defensive_count_top8 = int(len(defensive_in_top))
    defensive_pct_top8 = float(defensive_count_top8 / max(1, len(top_long_tickers)))
    defensive_lt_35 = bool(defensive_pct_top8 < 0.35)

    top12_longs = (
        block[block["pool_action"] == "LONG"]
        .sort_values(long_sort_cols, ascending=long_sort_asc)
        .head(12)
        .copy()
    )
    top12_longs["ticker_u"] = top12_longs["ticker"].astype(str).str.upper()
    top12_longs["mu_style_flag"] = _mu_style_flags(top12_longs)
    mu_style_count_top12 = int(pd.to_numeric(top12_longs["mu_style_flag"], errors="coerce").fillna(False).sum())
    mu_style_pass = bool(mu_style_count_top12 >= 4)

    top8_longs = top_longs.copy()
    top8_longs["ticker_u"] = top8_longs["ticker"].astype(str).str.upper()
    top8_longs["mu_style_flag"] = _mu_style_flags(top8_longs)
    mu_style_count_top8 = int(pd.to_numeric(top8_longs["mu_style_flag"], errors="coerce").fillna(False).sum())
    mu_style_pass_top8 = bool(mu_style_count_top8 >= 4)

    if "odds_ratio" in top8_longs.columns and pd.to_numeric(top8_longs["odds_ratio"], errors="coerce").notna().any():
        top8_odds_ratio = pd.to_numeric(top8_longs["odds_ratio"], errors="coerce")
    else:
        top8_odds_ratio = np.exp(
            pd.to_numeric(top8_longs["odds_score"], errors="coerce").clip(lower=-50.0, upper=50.0)
        )
        top8_odds_ratio = pd.to_numeric(top8_odds_ratio, errors="coerce")
    min_odds_ratio_top8 = float(top8_odds_ratio.min()) if top8_odds_ratio.notna().any() else float("nan")
    min_odds_ratio_ge_3 = bool(np.isfinite(min_odds_ratio_top8) and min_odds_ratio_top8 >= 0.5)

    deep_space_source = "mahalanobis_k_cyc"
    deep_space_series = pd.to_numeric(top8_longs.get("mahalanobis_k_cyc"), errors="coerce")
    if not deep_space_series.notna().any():
        deep_space_source = "mahalanobis_distance_fallback"
        deep_space_series = pd.to_numeric(top8_longs.get("mahalanobis_distance"), errors="coerce")
    deep_space_count_top_longs = int((deep_space_series.fillna(0.0) > 5.0).sum())
    deep_space_gt5_zero_pass = bool(deep_space_count_top_longs == 0)

    leverage_sample = block.copy()
    lev_series = pd.to_numeric(leverage_sample.get("leverage_multiplier", pd.Series(dtype=float)), errors="coerce")
    beta_series = pd.to_numeric(leverage_sample.get("portfolio_beta", pd.Series(dtype=float)), errors="coerce")
    gross_series = pd.to_numeric(leverage_sample.get("gross_exposure", pd.Series(dtype=float)), errors="coerce")
    net_series = pd.to_numeric(leverage_sample.get("net_exposure", pd.Series(dtype=float)), errors="coerce")
    borrow_series = pd.to_numeric(leverage_sample.get("borrow_cost_daily", pd.Series(dtype=float)), errors="coerce")

    lev_min = float(lev_series.min()) if lev_series.notna().any() else float("nan")
    lev_max = float(lev_series.max()) if lev_series.notna().any() else float("nan")
    beta_abs_max = float(beta_series.abs().max()) if beta_series.notna().any() else float("nan")
    gross_min = float(gross_series.min()) if gross_series.notna().any() else float("nan")
    accounting_pass = bool(
        ((gross_series + 1e-12) >= net_series.abs()).dropna().all()
    ) if (gross_series.notna().any() and net_series.notna().any()) else False
    borrow_nonnegative = bool((borrow_series.fillna(0.0) >= -1e-12).all())
    leverage_range_pass = bool(
        np.isfinite(lev_min) and np.isfinite(lev_max) and lev_min >= 1.0 - 1e-9 and lev_max <= 1.5 + 1e-9
    )
    beta_cap_pass = bool(np.isfinite(beta_abs_max) and beta_abs_max <= 1.0 + 1e-9)

    quarter_seed_log: list[dict[str, object]] = []
    if "centroid_quarter" in conviction.columns and "centroid_seed_missing" in conviction.columns:
        seed_log = (
            conviction[["centroid_quarter", "centroid_seed_missing"]]
            .drop_duplicates()
            .sort_values("centroid_quarter")
        )
        for _, row in seed_log.iterrows():
            q = str(row["centroid_quarter"])
            if not q or q.upper() == "<NA>" or q.lower() == "nan":
                continue
            missing_text = str(row["centroid_seed_missing"]) if pd.notna(row["centroid_seed_missing"]) else ""
            missing = [s for s in missing_text.split(",") if s]
            quarter_seed_log.append(
                {
                    "quarter": q,
                    "missing_seed_tickers": missing,
                    "missing_seed_count": int(len(missing)),
                }
            )

    posterior_coverage = float(len(valid_odds_rows) / max(1, len(block)))
    posterior_vals = valid_odds_rows[["posterior_cyclical", "posterior_defensive", "posterior_junk"]].apply(
        pd.to_numeric,
        errors="coerce",
    )
    posterior_bounds_pass = bool(
        ((posterior_vals >= -1e-9) & (posterior_vals <= 1.0 + 1e-9)).all(axis=None)
    ) if odds_available else False
    posterior_sum_pass = bool(
        np.allclose(
            (
                posterior_vals["posterior_cyclical"].fillna(0.0)
                + posterior_vals["posterior_defensive"].fillna(0.0)
                + posterior_vals["posterior_junk"].fillna(0.0)
            ).to_numpy(dtype=float),
            1.0,
            atol=1e-6,
        )
    ) if odds_available else False

    block_sector = block.get("sector", pd.Series(index=block.index, dtype="object"))
    block_industry = block.get("industry", pd.Series(index=block.index, dtype="object"))
    block_context_source = (
        pd.Series(block.get("sector_context_source", "unknown"), index=block.index)
        .fillna("unknown")
        .astype(str)
        .str.strip()
        .replace("", "unknown")
    )
    block_context_attached = (
        pd.Series(block.get("path1_sector_context_attached", False), index=block.index)
        .fillna(False)
        .astype(bool)
    )
    sample_context_attached = (
        pd.Series(sample.get("path1_sector_context_attached", False), index=sample.index)
        .fillna(False)
        .astype(bool)
    )
    model_dictatorship_values = sorted(
        {
            bool(x)
            for x in pd.to_numeric(block.get("dictatorship_mode", False), errors="coerce")
            .fillna(False)
            .astype(bool)
            .tolist()
        }
    )
    path1_cov_resample_modes = sorted(
        {
            str(x)
            for x in pd.Series(block.get("path1_cov_resample", "not_run"), index=block.index)
            .dropna()
            .astype(str)
            .tolist()
        }
    )
    path1_cov_resample_seed_values = sorted(
        {
            int(x)
            for x in pd.to_numeric(block.get("path1_cov_resample_seed", -1), errors="coerce")
            .fillna(-1)
            .astype(int)
            .tolist()
        }
    )
    path1_known_sector_n = int(_known_context_mask(block_sector).sum())
    path1_known_industry_n = int(_known_context_mask(block_industry).sum())
    path1_attached_n = int(block_context_attached.sum())
    path1_attached_ratio = float(path1_attached_n / max(1, len(block)))
    path1_source_counts = {
        str(k): int(v)
        for k, v in block_context_source.value_counts(dropna=False).sort_index().items()
    }
    path1_sample_sector_counts = {
        str(k): int(v)
        for k, v in pd.Series(sample.get("sector", pd.Series(index=sample.index, dtype="object")))
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
        .value_counts(dropna=False)
        .head(10)
        .sort_index()
        .items()
    }
    path1_sample_industry_counts = {
        str(k): int(v)
        for k, v in pd.Series(sample.get("industry", pd.Series(index=sample.index, dtype="object")))
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
        .value_counts(dropna=False)
        .head(10)
        .sort_index()
        .items()
    }

    summary = {
        "status": "ok",
        "window": {"start_date": str(start.date()), "as_of_date": str(as_of.date())},
        "sample_date": str(pd.Timestamp(sample_date).date()),
        "artifacts": {
            "sample_csv": str(output_csv),
            "summary_json": str(output_summary_json),
        },
        "hardening": {
            "dynamic_centroid": False,
            "centroid_frequency": "daily_anchor_injected",
            "seed_tickers": ["MU", "LRCX", "AMAT", "KLAC", "STX", "WDC"],
            "centroid_top_k": 30,
            "centroid_weighting": "anchor_mean_zspace; fallback_topk_by_prepool_score",
            "cyclical_feature_weight": 2.5,
            "ecdf_probability": "daily_average_rank",
            "shrinkage_methods_in_sample": sorted({str(x) for x in sample["shrinkage_method"].dropna().unique().tolist()}),
            "shrinkage_coeff_unique_in_sample": sorted(
                {
                    float(x)
                    for x in pd.to_numeric(sample["shrinkage_coeff"], errors="coerce").dropna().astype(float).tolist()
                }
            ),
        },
        "seed_missing_by_quarter": quarter_seed_log,
        "archetype_checks": {
            "tza_plug_out_top_longs": bool(tza_plug_out),
            "plug_tza_count_top_longs": plug_tza_count,
            "plug_tza_names_top_longs": plug_tza_names,
            "seed_names_available_in_universe": available_seed,
            "seed_names_in_top_longs": seed_in_top,
            "required_seed_names_in_top_longs": required_seed_in_top,
            "seed_presence_pass": bool(seed_presence_pass),
            "defensive_names_in_top_longs": defensive_in_top,
            "defensive_count_top_longs": defensive_count_top8,
            "defensive_pct_top_longs": defensive_pct_top8,
            "defensive_lt_35_pct": defensive_lt_35,
            "defensive_le_25_pct": bool(defensive_pct_top8 <= 0.25),
            "mu_style_count_top8": mu_style_count_top8,
            "mu_style_count_top8_required": 4,
            "mu_style_top8_pass": mu_style_pass_top8,
            "mu_style_count_top12": mu_style_count_top12,
            "mu_style_count_required": 4,
            "mu_style_pass": mu_style_pass,
            "mu_style_tickers_top12": sorted(
                set(top12_longs.loc[top12_longs["mu_style_flag"], "ticker_u"].dropna().astype(str).tolist())
            ),
            "deep_space_count_top_longs_gt5": deep_space_count_top_longs,
            "deep_space_gt5_zero_pass": deep_space_gt5_zero_pass,
            "deep_space_source": deep_space_source,
        },
        "leverage_checks": {
            "leverage_min": lev_min,
            "leverage_max": lev_max,
            "leverage_in_1p0_to_1p5": leverage_range_pass,
            "portfolio_beta_abs_max": beta_abs_max,
            "portfolio_beta_cap_1p0_pass": beta_cap_pass,
            "gross_exposure_min": gross_min,
            "net_gross_accounting_pass": accounting_pass,
            "borrow_cost_nonnegative": borrow_nonnegative,
        },
        "odds_checks": {
            "odds_available": bool(odds_available),
            "valid_odds_rows": int(len(valid_odds_rows)),
            "posterior_coverage": posterior_coverage,
            "posterior_bounds_pass": posterior_bounds_pass,
            "posterior_sum_close_to_one_pass": posterior_sum_pass,
            "min_odds_ratio_top8": min_odds_ratio_top8,
            "min_odds_ratio_top8_ge_3": bool(np.isfinite(min_odds_ratio_top8) and min_odds_ratio_top8 >= 3.0),
            "min_raw_odds_ratio_top8_ge_0p5": min_odds_ratio_ge_3,
        },
        "path1_telemetry": {
            "DICTATORSHIP_MODE": dictatorship_mode_label,
            "dictatorship_mode": dictatorship_mode_label,
            "path1_directive_id": PATH1_DIRECTIVE_ID,
            "model_dictatorship_mode_values": model_dictatorship_values,
            "path1_cov_resample_modes_in_block": path1_cov_resample_modes,
            "path1_cov_resample_seed_values_in_block": path1_cov_resample_seed_values,
            "block_rows": int(len(block)),
            "sample_rows": int(len(sample)),
            "context_attached_rows_in_block": path1_attached_n,
            "context_attached_ratio_in_block": path1_attached_ratio,
            "known_sector_rows_in_block": path1_known_sector_n,
            "known_industry_rows_in_block": path1_known_industry_n,
            "sample_context_attached_rows": int(sample_context_attached.sum()),
            "context_source_counts_in_block": path1_source_counts,
            "sample_sector_counts": path1_sample_sector_counts,
            "sample_industry_counts": path1_sample_industry_counts,
        },
    }
    _atomic_json_write(summary, output_summary_json)

    method = str(block["shrinkage_method"].dropna().iloc[0]) if block["shrinkage_method"].notna().any() else "unknown"
    coeff = float(pd.to_numeric(block["shrinkage_coeff"], errors="coerce").dropna().iloc[0]) if pd.to_numeric(block["shrinkage_coeff"], errors="coerce").notna().any() else float("nan")
    print("Phase 21.1 ticker pool slice complete")
    print(f"Sample date used: {sample_date.date()} (as-of request: {as_of.date()})")
    print(f"Shrinkage path: {method} (coeff={coeff:.4f})")
    print(f"Long rows: {len(longs)} | Short rows: {len(shorts)}")
    print(f"Output: {output_csv}")
    print(f"Summary: {output_summary_json}")
    print(f"Archetype check - TZA/PLUG out of top longs: {tza_plug_out}")
    print(
        "Archetype check - seed presence pass: "
        f"{seed_presence_pass} (available={available_seed}, in_top={seed_in_top}, required={required_seed_in_top})"
    )
    print(
        "Archetype check - defensive share: "
        f"{defensive_pct_top8:.3f} ({defensive_count_top8}/{max(1, len(top_long_tickers))}), <35%={defensive_lt_35}"
    )
    print(
        "Archetype check - MU-style cyclicals in top12: "
        f"{mu_style_count_top12} (required>=4) pass={mu_style_pass}"
    )
    print(
        "Archetype check - MU-style cyclicals in top8: "
        f"{mu_style_count_top8} (required>=4) pass={mu_style_pass_top8}"
    )
    print(
        "Archetype check - PLUG/TZA count in top longs: "
        f"{plug_tza_count} names={plug_tza_names}"
    )
    print(
        "Odds check - min raw odds_ratio in top8 longs: "
        f"{min_odds_ratio_top8:.4f} (>=0.5 pass={min_odds_ratio_ge_3})"
    )
    print(
        "Archetype check - deep-space names (MahDist>5.0) in top longs: "
        f"{deep_space_count_top_longs} (must be 0 pass={deep_space_gt5_zero_pass})"
    )
    print(
        "Leverage check - leverage range [1.0,1.5]: "
        f"min={lev_min:.4f}, max={lev_max:.4f}, pass={leverage_range_pass}"
    )
    print(
        "Leverage check - portfolio beta cap |beta|<=1.0: "
        f"max_abs_beta={beta_abs_max:.4f}, pass={beta_cap_pass}"
    )
    print(
        "Leverage check - accounting gross>=|net| and borrow_cost>=0: "
        f"gross_min={gross_min:.4f}, accounting_pass={accounting_pass}, borrow_nonnegative={borrow_nonnegative}"
    )
    print(
        "Path1 telemetry - mode/directive/context: "
        f"{dictatorship_mode_label} / {PATH1_DIRECTIVE_ID} / {path1_attached_n}/{len(block)} "
        f"(ratio={path1_attached_ratio:.3f})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
