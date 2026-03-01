from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.day5_ablation_report import _atomic_csv_write  # noqa: E402
from scripts.day5_ablation_report import _resolve_path  # noqa: E402
from scripts.day5_ablation_report import _to_ts  # noqa: E402
from scripts.phase20_full_backtest import DEFAULT_FEATURES_PATH  # noqa: E402
from scripts.phase20_full_backtest import DEFAULT_LIQUIDITY_PATH  # noqa: E402
from scripts.phase20_full_backtest import DEFAULT_MACRO_FALLBACK_PATH  # noqa: E402
from scripts.phase20_full_backtest import DEFAULT_MACRO_FEATURES_PATH  # noqa: E402
from scripts.phase20_full_backtest import _load_features_window  # noqa: E402
from scripts.phase20_full_backtest import _load_regime_states  # noqa: E402
from scripts.phase21_1_ticker_pool_slice import _load_fundamentals_window  # noqa: E402
from strategies.company_scorecard import CompanyScorecard  # noqa: E402
from strategies.company_scorecard import build_phase20_conviction_frame  # noqa: E402
from strategies.production_config import PRODUCTION_CONFIG_V1  # noqa: E402

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SEED_TICKERS = ("MU", "CIEN", "COHR", "TER")
FOCUS_TICKERS = ("MU", "CIEN", "KLAC", "LRCX")


def _robust_zscore(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    if int(s.notna().sum()) == 0:
        return pd.Series(np.nan, index=s.index, dtype=float)
    med = float(s.median(skipna=True))
    mad = float((s - med).abs().median(skipna=True))
    scale = mad * 1.4826
    if (not np.isfinite(scale)) or scale <= 1e-9:
        sigma = float(s.std(skipna=True))
        if np.isfinite(sigma) and sigma > 1e-9:
            scale = sigma
        else:
            out = pd.Series(np.nan, index=s.index, dtype=float)
            out.loc[s.notna()] = 0.0
            return out
    return (s - med) / scale


def _first_nonempty_series(block: pd.DataFrame, candidates: list[str]) -> pd.Series:
    nan_series = pd.Series(np.nan, index=block.index, dtype=float)
    for col in candidates:
        if col not in block.columns:
            continue
        series = pd.to_numeric(block[col], errors="coerce")
        if int(series.notna().sum()) > 0:
            return series
    return nan_series


def _build_conviction(start_date: pd.Timestamp, as_of_date: pd.Timestamp, features_path: Path, fundamentals_path: Path, macro_path: Path, liquidity_path: Path) -> pd.DataFrame:
    extra_cols = [
        "ticker",
        "adj_close",
        "dist_sma20",
        "sma200",
        "yz_vol_20d",
        "atr_14d",
        "revenue_growth_q",
        "revenue_growth_yoy",
        "resid_mom_60d",
        "z_inventory_quality_proxy",
        "capital_cycle_score",
        "amihud_20d",
        "z_discipline_cond",
        "z_moat",
        "z_demand",
        "gm_accel_q",
        "z_ebitda_roic_accel",
    ]
    features = _load_features_window(
        features_path=features_path,
        start_date=start_date,
        end_date=as_of_date,
        extra_columns=extra_cols,
    )
    if features.empty:
        raise RuntimeError("No features found for requested diagnostic window")

    fundamentals = _load_fundamentals_window(
        fundamentals_path=fundamentals_path,
        start_date=start_date,
        end_date=as_of_date,
    )
    if not fundamentals.empty:
        fundamentals = fundamentals.sort_values(["date", "permno"]).drop_duplicates(["date", "permno"], keep="last")
        features = features.merge(fundamentals, on=["date", "permno"], how="left")
    else:
        features["ebitda_ttm"] = pd.NA
        features["roic"] = pd.NA
        features["operating_margin_delta_q"] = pd.NA

    feature_dates = pd.DatetimeIndex(sorted(features["date"].dropna().unique()))
    regime, _ = _load_regime_states(
        start_date=start_date,
        end_date=as_of_date,
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
    )
    if conviction.empty:
        raise RuntimeError("Conviction frame is empty")
    return conviction


def _build_diagnostic_table(block: pd.DataFrame) -> pd.DataFrame:
    diag = block.copy()

    ticker_u = diag["ticker"].astype(str).str.upper()

    if "z_ebitda_roic_accel" in diag.columns and int(pd.to_numeric(diag["z_ebitda_roic_accel"], errors="coerce").notna().sum()) > 0:
        ebitda_roic = pd.to_numeric(diag["z_ebitda_roic_accel"], errors="coerce")
        ebitda_roic_source = "z_ebitda_roic_accel"
    else:
        ebitda_accel_z = _robust_zscore(pd.to_numeric(diag.get("ebitda_accel"), errors="coerce"))
        roic_accel_z = _robust_zscore(pd.to_numeric(diag.get("roic_accel"), errors="coerce"))
        ebitda_roic = pd.concat([ebitda_accel_z, roic_accel_z], axis=1).mean(axis=1, skipna=True)
        ebitda_roic_source = "robust_z_avg(ebitda_accel,roic_accel)"

    gm_raw = _first_nonempty_series(diag, ["gm_accel_q", "operating_margin_delta_q", "ebitda_accel"])
    rev_raw = _first_nonempty_series(diag, ["revenue_growth_q", "revenue_growth_yoy", "revenue_growth_lag"])
    realized_vol = pd.to_numeric(diag.get("realized_vol_lag"), errors="coerce")
    if int(realized_vol.notna().sum()) == 0:
        realized_vol = _first_nonempty_series(diag, ["yz_vol_20d", "atr_14d"])

    diag_out = pd.DataFrame(index=diag.index)
    diag_out["date"] = pd.to_datetime(diag["date"], errors="coerce")
    diag_out["ticker"] = diag["ticker"].astype(str)
    diag_out["permno"] = pd.to_numeric(diag["permno"], errors="coerce")
    diag_out["pool_action"] = diag["pool_action"].astype(str)
    diag_out["resid_mom_60d"] = pd.to_numeric(diag.get("resid_mom_60d"), errors="coerce")
    diag_out["ebitda_roic_accel"] = pd.to_numeric(ebitda_roic, errors="coerce")
    diag_out["ebitda_roic_accel_source"] = ebitda_roic_source
    diag_out["gm_accel_q"] = pd.to_numeric(diag.get("gm_accel_q"), errors="coerce")
    diag_out["gm_accel_q_eff"] = pd.to_numeric(gm_raw, errors="coerce")
    diag_out["revenue_growth_q"] = pd.to_numeric(diag.get("revenue_growth_q"), errors="coerce")
    diag_out["revenue_growth_q_eff"] = pd.to_numeric(rev_raw, errors="coerce")
    diag_out["realized_vol"] = pd.to_numeric(realized_vol, errors="coerce")
    diag_out["mahalanobis_to_centroid"] = pd.to_numeric(diag.get("mahalanobis_distance"), errors="coerce")
    diag_out["r_cyc"] = pd.to_numeric(diag.get("posterior_cyclical"), errors="coerce")
    diag_out["r_def"] = pd.to_numeric(diag.get("posterior_defensive"), errors="coerce")
    diag_out["r_junk"] = pd.to_numeric(diag.get("posterior_junk"), errors="coerce")
    diag_out["odds_score"] = pd.to_numeric(diag.get("odds_score"), errors="coerce")
    diag_out["compounder_prob"] = pd.to_numeric(diag.get("compounder_prob"), errors="coerce")
    diag_out["conviction_score"] = pd.to_numeric(diag.get("conviction_score"), errors="coerce")
    diag_out["score"] = pd.to_numeric(diag.get("score"), errors="coerce")

    z_cols = {
        "resid_mom_60d": _robust_zscore(diag_out["resid_mom_60d"]),
        "ebitda_roic_accel": _robust_zscore(diag_out["ebitda_roic_accel"]),
        "gm_accel_q": _robust_zscore(diag_out["gm_accel_q_eff"]),
        "revenue_growth_q": _robust_zscore(diag_out["revenue_growth_q_eff"]),
        "realized_vol": _robust_zscore(diag_out["realized_vol"]),
    }
    anchor_mask = ticker_u.isin(set(SEED_TICKERS))
    anchor_count = int(anchor_mask.sum())
    diag_out["anchor_seed_count"] = anchor_count

    delta_cols: list[str] = []
    for name, zser in z_cols.items():
        diag_out[f"z_{name}"] = zser
        anchor_mean = float(zser.loc[anchor_mask].mean()) if anchor_count > 0 else np.nan
        diag_out[f"anchor_z_{name}"] = anchor_mean
        delta_col = f"z_delta_{name}"
        diag_out[delta_col] = zser - anchor_mean
        delta_cols.append(delta_col)

    delta_matrix = diag_out[delta_cols].to_numpy(dtype=float)
    diag_out["z_delta_l2"] = np.sqrt(np.nansum(np.square(delta_matrix), axis=1))

    diag_out["is_seed_anchor"] = ticker_u.isin(set(SEED_TICKERS))
    diag_out["is_focus_ticker"] = ticker_u.isin(set(FOCUS_TICKERS))

    return diag_out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 21 odds diagnostic table")
    parser.add_argument("--start-date", default="2015-01-01")
    parser.add_argument("--as-of-date", required=True)
    parser.add_argument("--input-features", default=str(DEFAULT_FEATURES_PATH))
    parser.add_argument("--input-fundamentals", default=str(PROCESSED_DIR / "daily_fundamentals_panel.parquet"))
    parser.add_argument("--macro-path", default=None)
    parser.add_argument("--liquidity-path", default=str(DEFAULT_LIQUIDITY_PATH))
    parser.add_argument("--output-csv", default=None)
    parser.add_argument("--top-longs", type=int, default=8)
    parser.add_argument("--top-shorts", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    start = _to_ts(args.start_date)
    as_of = _to_ts(args.as_of_date)
    if start is None or as_of is None:
        raise ValueError("Both --start-date and --as-of-date must be valid dates")
    if as_of < start:
        raise ValueError(f"as-of-date {as_of.date()} is earlier than start-date {start.date()}")

    output_default = PROCESSED_DIR / f"phase21_1_diagnostic_odds_{as_of.strftime('%Y-%m-%d')}.csv"

    features_path = _resolve_path(args.input_features, DEFAULT_FEATURES_PATH)
    fundamentals_path = _resolve_path(args.input_fundamentals, PROCESSED_DIR / "daily_fundamentals_panel.parquet")
    macro_path = _resolve_path(
        args.macro_path,
        DEFAULT_MACRO_FEATURES_PATH if DEFAULT_MACRO_FEATURES_PATH.exists() else DEFAULT_MACRO_FALLBACK_PATH,
    )
    liquidity_path = _resolve_path(args.liquidity_path, DEFAULT_LIQUIDITY_PATH)
    output_csv = _resolve_path(args.output_csv, output_default)

    conviction = _build_conviction(
        start_date=start,
        as_of_date=as_of,
        features_path=features_path,
        fundamentals_path=fundamentals_path,
        macro_path=macro_path,
        liquidity_path=liquidity_path,
    )

    block = conviction.loc[conviction["date"].eq(as_of)].copy()
    if block.empty:
        raise RuntimeError(f"No rows found for exact as-of date {as_of.date()}")

    diag = _build_diagnostic_table(block)
    diag = diag.sort_values(["odds_score", "compounder_prob", "conviction_score"], ascending=[False, False, False])

    _atomic_csv_write(diag, output_csv)

    print("Phase 21 odds diagnostic complete")
    print(f"As-of date: {as_of.date()} | Rows: {len(diag)}")
    print(f"Full diagnostic CSV: {output_csv}")

    cols_excerpt = [
        "ticker",
        "resid_mom_60d",
        "ebitda_roic_accel",
        "gm_accel_q_eff",
        "revenue_growth_q_eff",
        "realized_vol",
        "mahalanobis_to_centroid",
        "r_cyc",
        "r_def",
        "r_junk",
        "odds_score",
        "z_delta_resid_mom_60d",
        "z_delta_ebitda_roic_accel",
        "z_delta_gm_accel_q",
        "z_delta_revenue_growth_q",
        "z_delta_realized_vol",
    ]

    top_longs = diag.loc[diag["pool_action"].eq("LONG")].head(int(args.top_longs))
    top_shorts = (
        diag.loc[diag["pool_action"].eq("SHORT")]
        .sort_values(["odds_score", "mahalanobis_to_centroid"], ascending=[True, False])
        .head(int(args.top_shorts))
    )
    focus = diag.loc[diag["ticker"].astype(str).str.upper().isin(set(FOCUS_TICKERS))]

    print("\nTop 8 LONGS (side-by-side)")
    if top_longs.empty:
        print("NONE")
    else:
        print(top_longs[cols_excerpt].to_string(index=False))

    print("\nTop 8 SHORTS (side-by-side)")
    if top_shorts.empty:
        print("NONE")
    else:
        print(top_shorts[cols_excerpt].to_string(index=False))

    print("\nFocus tickers (MU, CIEN, KLAC, LRCX)")
    if focus.empty:
        print("NONE")
    else:
        print(focus[cols_excerpt + ["pool_action"]].sort_values("ticker").to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
