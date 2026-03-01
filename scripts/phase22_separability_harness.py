from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

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
from scripts.phase21_1_ticker_pool_slice import DICTATORSHIP_MODE  # noqa: E402
from scripts.phase21_1_ticker_pool_slice import DICTATORSHIP_MODE_OFF  # noqa: E402
from scripts.phase21_1_ticker_pool_slice import _load_fundamentals_window  # noqa: E402
from strategies.company_scorecard import CompanyScorecard  # noqa: E402
from strategies.company_scorecard import build_phase20_conviction_frame  # noqa: E402
from strategies.production_config import PRODUCTION_CONFIG_V1  # noqa: E402
from strategies.ticker_pool import TickerPoolConfig  # noqa: E402
from strategies.ticker_pool import _build_weighted_zmat_with_imputation  # noqa: E402
from strategies.ticker_pool import _path1_sector_projection_residualize  # noqa: E402
from strategies.ticker_pool import _resolve_path1_feature_partition  # noqa: E402

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_FUNDAMENTALS_PATH = PROCESSED_DIR / "daily_fundamentals_panel.parquet"
DEFAULT_OUTPUT_CSV = PROCESSED_DIR / "phase22_separability_daily.csv"
DEFAULT_OUTPUT_SUMMARY_JSON = PROCESSED_DIR / "phase22_separability_summary.json"
POSTERIOR_COLS: tuple[str, ...] = (
    "posterior_cyclical",
    "posterior_defensive",
    "posterior_junk",
)
POSTERIOR_LABELS: tuple[str, ...] = ("cyclical", "defensive", "junk")
ARCHETYPE_TICKERS: tuple[str, ...] = ("MU", "LRCX", "AMAT", "KLAC")


def _clean_member_ids(df: pd.DataFrame) -> pd.Series:
    ticker_u = (
        pd.Series(df.get("ticker", pd.Series(index=df.index, dtype="object")), index=df.index)
        .astype("string")
        .str.strip()
        .str.upper()
    )
    valid_ticker = ticker_u.notna() & (~ticker_u.isin({"", "NAN", "NONE", "<NA>"}))
    permno = pd.to_numeric(df.get("permno", pd.Series(index=df.index, dtype=float)), errors="coerce")
    permno_str = permno.round().astype("Int64").astype("string")
    fallback = "PERMNO_" + permno_str.fillna("-1")
    return ticker_u.where(valid_ticker, fallback).astype(str)


def _jaccard_index(lhs: set[str], rhs: set[str]) -> float:
    union = lhs.union(rhs)
    if not union:
        return float("nan")
    inter = lhs.intersection(rhs)
    return float(len(inter) / len(union))


def _build_geometry_residuals(
    block: pd.DataFrame,
    cfg: TickerPoolConfig,
) -> tuple[pd.DataFrame, str, dict[str, int]]:
    allow_features, _ = _resolve_path1_feature_partition(cfg)
    zmat, impute_stats = _build_weighted_zmat_with_imputation(
        block,
        cfg,
        industry_col="industry",
        sector_col="sector",
    )

    valid = zmat.loc[:, allow_features].notna().all(axis=1)
    zgeom = zmat.loc[valid, allow_features]
    if zgeom.empty:
        return (
            pd.DataFrame(index=pd.Index([], dtype=object), columns=allow_features),
            "geometry_empty",
            impute_stats,
        )

    sectors = block.loc[valid, "sector"] if "sector" in block.columns else pd.Series("UNKNOWN", index=zgeom.index)
    resid, mode, _ = _path1_sector_projection_residualize(zgeom, sectors=sectors)
    return resid, str(mode), impute_stats


def _posterior_argmax_labels(block: pd.DataFrame) -> pd.Series:
    posterior = block.loc[:, list(POSTERIOR_COLS)].apply(pd.to_numeric, errors="coerce")
    valid = posterior.notna().all(axis=1)
    argmax = pd.Series(pd.NA, index=posterior.index, dtype="object")
    if bool(valid.any()):
        argmax.loc[valid] = posterior.loc[valid].idxmax(axis=1)
    mapping = {
        "posterior_cyclical": "cyclical",
        "posterior_defensive": "defensive",
        "posterior_junk": "junk",
    }
    labels = argmax.map(mapping)
    return pd.Series(labels, index=posterior.index, dtype="object")


def _compute_silhouette_metrics(geometry: pd.DataFrame, labels: pd.Series) -> dict[str, Any]:
    label_index = labels.dropna().index
    idx = geometry.index.intersection(label_index)
    if len(idx) < 3:
        class_counts = labels.loc[idx].value_counts(dropna=False)
        return {
            "silhouette_score": float("nan"),
            "silhouette_reason": "too_few_rows",
            "silhouette_label_rows": int(len(idx)),
            "silhouette_effective_classes": int(class_counts.size),
            "silhouette_cyclical_n": int(class_counts.get("cyclical", 0)),
            "silhouette_defensive_n": int(class_counts.get("defensive", 0)),
            "silhouette_junk_n": int(class_counts.get("junk", 0)),
        }

    y = labels.loc[idx].astype(str)
    class_counts = y.value_counts(dropna=False)
    effective_classes = int(class_counts.size)
    if effective_classes <= 1:
        return {
            "silhouette_score": float("nan"),
            "silhouette_reason": "one_effective_class",
            "silhouette_label_rows": int(len(idx)),
            "silhouette_effective_classes": int(effective_classes),
            "silhouette_cyclical_n": int(class_counts.get("cyclical", 0)),
            "silhouette_defensive_n": int(class_counts.get("defensive", 0)),
            "silhouette_junk_n": int(class_counts.get("junk", 0)),
        }

    x = geometry.loc[idx].to_numpy(dtype=float)
    y_values = y.to_numpy(dtype=str)

    score: float
    reason = "ok"
    try:
        from sklearn.metrics import silhouette_score  # type: ignore

        score = float(silhouette_score(x, y.to_numpy()))
    except Exception:
        score = _manual_silhouette_score(x, y_values)
        reason = "ok_manual" if np.isfinite(score) else "silhouette_error"
    return {
        "silhouette_score": score,
        "silhouette_reason": reason,
        "silhouette_label_rows": int(len(idx)),
        "silhouette_effective_classes": int(effective_classes),
        "silhouette_cyclical_n": int(class_counts.get("cyclical", 0)),
        "silhouette_defensive_n": int(class_counts.get("defensive", 0)),
        "silhouette_junk_n": int(class_counts.get("junk", 0)),
    }


def _manual_silhouette_score(x: np.ndarray, labels: np.ndarray) -> float:
    n_samples = int(x.shape[0])
    if n_samples < 3:
        return float("nan")
    unique_labels = np.unique(labels)
    if unique_labels.size < 2 or unique_labels.size >= n_samples:
        return float("nan")

    diffs = x[:, None, :] - x[None, :, :]
    dist = np.sqrt(np.sum(diffs * diffs, axis=2))

    label_to_idx = {label: np.flatnonzero(labels == label) for label in unique_labels}
    a = np.zeros(n_samples, dtype=float)
    b = np.full(n_samples, np.inf, dtype=float)

    for label, idx in label_to_idx.items():
        if idx.size <= 1:
            a[idx] = 0.0
        else:
            intra = dist[np.ix_(idx, idx)]
            a[idx] = intra.sum(axis=1) / float(idx.size - 1)

        for other_label, other_idx in label_to_idx.items():
            if other_label == label:
                continue
            inter = dist[np.ix_(idx, other_idx)].mean(axis=1)
            b[idx] = np.minimum(b[idx], inter)

    denom = np.maximum(a, b)
    s = np.where(denom > 0.0, (b - a) / denom, 0.0)
    if not bool(np.isfinite(s).all()):
        return float("nan")
    return float(np.mean(s))


def _archetype_rank_metrics(
    ranked_block: pd.DataFrame,
    top_decile_n: int,
    top_n_label: int,
    top_n_eff: int,
) -> dict[str, Any]:
    rank_series = pd.Series(np.arange(1, len(ranked_block) + 1), index=ranked_block["ticker_u"], dtype=float)
    universe = set(ranked_block["ticker_u"].dropna().astype(str))

    out: dict[str, Any] = {}
    top_decile_hits = 0
    top_n_hits = 0
    present_n = 0
    ranked_n = 0

    for ticker in ARCHETYPE_TICKERS:
        prefix = ticker.lower()
        present = ticker in universe
        rank_val = float(rank_series.get(ticker, np.nan))
        ranked = bool(np.isfinite(rank_val))
        top_decile_hit = bool(ranked and rank_val <= float(top_decile_n))
        top_n_hit = bool(ranked and rank_val <= float(top_n_eff))

        out[f"{prefix}_present"] = bool(present)
        out[f"{prefix}_rank"] = rank_val
        out[f"{prefix}_top_decile_hit"] = bool(top_decile_hit)
        out[f"{prefix}_top_{int(top_n_label)}_hit"] = bool(top_n_hit)

        present_n += int(present)
        ranked_n += int(ranked)
        top_decile_hits += int(top_decile_hit)
        top_n_hits += int(top_n_hit)

    out["archetype_present_n"] = int(present_n)
    out["archetype_ranked_n"] = int(ranked_n)
    out["archetype_top_decile_hits"] = int(top_decile_hits)
    out[f"archetype_top_{int(top_n_label)}_hits"] = int(top_n_hits)
    return out


def _safe_mean(series: pd.Series) -> float:
    vals = pd.to_numeric(series, errors="coerce")
    vals = vals[np.isfinite(vals)]
    if vals.empty:
        return float("nan")
    return float(vals.mean())


def _metric_summary(series: pd.Series) -> dict[str, Any]:
    vals = pd.to_numeric(series, errors="coerce")
    vals = vals[np.isfinite(vals)]
    if vals.empty:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
        }
    return {
        "count": int(len(vals)),
        "mean": float(vals.mean()),
        "median": float(vals.median()),
        "min": float(vals.min()),
        "max": float(vals.max()),
    }


def _load_conviction_frame(
    *,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    features_path: Path,
    fundamentals_path: Path,
    macro_path: Path,
    liquidity_path: Path,
    dictatorship_mode: bool,
) -> pd.DataFrame:
    warmup_start = pd.Timestamp(start_date) - pd.Timedelta(days=14)
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
        start_date=warmup_start,
        end_date=end_date,
        extra_columns=extra_cols,
    )
    if features.empty:
        return pd.DataFrame()

    fundamentals = _load_fundamentals_window(
        fundamentals_path=fundamentals_path,
        start_date=warmup_start,
        end_date=end_date,
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
        start_date=warmup_start,
        end_date=end_date,
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
    conviction["date"] = pd.to_datetime(conviction["date"], errors="coerce")
    conviction = conviction[
        conviction["date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date), inclusive="both")
    ].copy()
    return conviction


def _build_daily_metrics(
    conviction: pd.DataFrame,
    *,
    top_decile_ratio: float,
    top_n: int,
) -> pd.DataFrame:
    if conviction.empty:
        return pd.DataFrame()

    cfg = TickerPoolConfig()
    rows: list[dict[str, Any]] = []
    prev_top_decile: set[str] | None = None
    prev_top_n: set[str] | None = None

    for current_date, block in conviction.groupby("date", sort=True):
        b = block.copy()
        b["odds_score"] = pd.to_numeric(b.get("odds_score"), errors="coerce")
        b["ticker_u"] = _clean_member_ids(b)

        ranked = (
            b.loc[b["odds_score"].notna(), ["ticker_u", "odds_score"]]
            .sort_values(["odds_score", "ticker_u"], ascending=[False, True], kind="mergesort")
            .reset_index(drop=True)
        )

        top_decile_n = int(max(1, math.ceil(len(ranked) * float(top_decile_ratio)))) if len(ranked) else 0
        top_n_eff = int(min(int(top_n), len(ranked)))
        top_decile_set = set(ranked["ticker_u"].head(top_decile_n).astype(str).tolist()) if top_decile_n > 0 else set()
        top_n_set = set(ranked["ticker_u"].head(top_n_eff).astype(str).tolist()) if top_n_eff > 0 else set()

        jaccard_top_decile = float("nan")
        jaccard_top_n = float("nan")
        if prev_top_decile is not None:
            jaccard_top_decile = _jaccard_index(prev_top_decile, top_decile_set)
        if prev_top_n is not None:
            jaccard_top_n = _jaccard_index(prev_top_n, top_n_set)
        prev_top_decile = top_decile_set
        prev_top_n = top_n_set

        geometry, residual_mode, impute_stats = _build_geometry_residuals(b, cfg=cfg)
        labels = _posterior_argmax_labels(b)
        sil = _compute_silhouette_metrics(geometry, labels)

        row: dict[str, Any] = {
            "date": pd.Timestamp(current_date),
            "window_rows": int(len(b)),
            "valid_odds_rows": int(len(ranked)),
            "top_decile_n": int(top_decile_n),
            f"top_{int(top_n)}_n": int(top_n_eff),
            "jaccard_top_decile": jaccard_top_decile,
            f"jaccard_top_{int(top_n)}": jaccard_top_n,
            "geometry_rows": int(len(geometry)),
            "geometry_residualization_mode": str(residual_mode),
            "geometry_universe_before_imputation": int(impute_stats.get("universe_before_imputation", 0)),
            "geometry_universe_after_imputation": int(impute_stats.get("universe_after_imputation", 0)),
            "geometry_industry_impute_cells": int(impute_stats.get("industry_fill_cells", 0)),
            "geometry_sector_impute_cells": int(impute_stats.get("sector_fill_cells", 0)),
            "geometry_zero_impute_cells": int(impute_stats.get("zero_fill_cells", 0)),
        }
        row.update(sil)
        row.update(
            _archetype_rank_metrics(
                ranked_block=ranked,
                top_decile_n=top_decile_n,
                top_n_label=top_n,
                top_n_eff=top_n_eff,
            )
        )
        rows.append(row)

    out = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date.astype(str)
    return out


def _build_summary(
    daily: pd.DataFrame,
    *,
    start_date: pd.Timestamp,
    as_of_date: pd.Timestamp,
    top_n: int,
    dictatorship_mode: bool,
    output_csv: Path,
    output_summary_json: Path,
) -> dict[str, Any]:
    mode_label = DICTATORSHIP_MODE if dictatorship_mode else DICTATORSHIP_MODE_OFF
    if daily.empty:
        return {
            "status": "no_data",
            "window": {"start_date": str(start_date.date()), "as_of_date": str(as_of_date.date())},
            "artifacts": {
                "daily_csv": str(output_csv),
                "summary_json": str(output_summary_json),
            },
            "directives": {
                "rank_stability_basis": "odds_score",
                "silhouette_label_source": "posterior_argmax",
                "silhouette_single_class_policy": "nan_with_coverage_counters",
                "dictatorship_mode": mode_label,
            },
        }

    aggregate = {
        "days_total": int(len(daily)),
        "days_with_valid_odds": int((pd.to_numeric(daily["valid_odds_rows"], errors="coerce") > 0).sum()),
        "geometry_universe_before_imputation": _metric_summary(daily["geometry_universe_before_imputation"]),
        "geometry_universe_after_imputation": _metric_summary(daily["geometry_universe_after_imputation"]),
        "geometry_industry_impute_cells": _metric_summary(daily["geometry_industry_impute_cells"]),
        "geometry_sector_impute_cells": _metric_summary(daily["geometry_sector_impute_cells"]),
        "geometry_zero_impute_cells": _metric_summary(daily["geometry_zero_impute_cells"]),
        "jaccard_top_decile": _metric_summary(daily["jaccard_top_decile"]),
        f"jaccard_top_{int(top_n)}": _metric_summary(daily[f"jaccard_top_{int(top_n)}"]),
        "silhouette_score": _metric_summary(daily["silhouette_score"]),
        "silhouette_single_class_days": int(
            pd.Series(daily["silhouette_reason"], index=daily.index).eq("one_effective_class").sum()
        ),
        "silhouette_invalid_days": int(pd.to_numeric(daily["silhouette_score"], errors="coerce").isna().sum()),
        "archetype_top_decile_hit_rate": float(
            _safe_mean(
                pd.to_numeric(daily["archetype_top_decile_hits"], errors="coerce")
                / float(len(ARCHETYPE_TICKERS))
            )
        ),
        f"archetype_top_{int(top_n)}_hit_rate": float(
            _safe_mean(
                pd.to_numeric(daily[f"archetype_top_{int(top_n)}_hits"], errors="coerce")
                / float(len(ARCHETYPE_TICKERS))
            )
        ),
    }
    before = pd.to_numeric(daily["geometry_universe_before_imputation"], errors="coerce").replace(0.0, np.nan)
    after = pd.to_numeric(daily["geometry_universe_after_imputation"], errors="coerce")
    aggregate["geometry_recovery_ratio_mean"] = float(_safe_mean(after / before))

    archetype_detail: dict[str, Any] = {}
    for ticker in ARCHETYPE_TICKERS:
        prefix = ticker.lower()
        rank_col = f"{prefix}_rank"
        dec_col = f"{prefix}_top_decile_hit"
        top_n_col = f"{prefix}_top_{int(top_n)}_hit"
        rank_vals = pd.to_numeric(daily[rank_col], errors="coerce")
        archetype_detail[ticker] = {
            "present_days": int(pd.to_numeric(daily[f"{prefix}_present"], errors="coerce").fillna(False).astype(bool).sum()),
            "ranked_days": int(rank_vals.notna().sum()),
            "mean_rank": float(rank_vals.dropna().mean()) if rank_vals.notna().any() else None,
            "median_rank": float(rank_vals.dropna().median()) if rank_vals.notna().any() else None,
            "top_decile_hit_rate": float(_safe_mean(pd.to_numeric(daily[dec_col], errors="coerce"))),
            f"top_{int(top_n)}_hit_rate": float(_safe_mean(pd.to_numeric(daily[top_n_col], errors="coerce"))),
        }

    return {
        "status": "ok",
        "window": {"start_date": str(start_date.date()), "as_of_date": str(as_of_date.date())},
        "artifacts": {
            "daily_csv": str(output_csv),
            "summary_json": str(output_summary_json),
        },
        "directives": {
            "rank_stability_basis": "odds_score",
            "rank_stability_sets": ["top_decile", f"top_{int(top_n)}"],
            "silhouette_label_source": "posterior_argmax",
            "silhouette_space": "post_neutralized_post_mad_scaled",
            "silhouette_single_class_policy": "nan_with_coverage_counters",
            "dictatorship_mode": mode_label,
        },
        "aggregate_metrics": aggregate,
        "archetype_metrics": archetype_detail,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 22 separability harness (Jaccard/Silhouette/Archetype Recall)"
    )
    parser.add_argument("--start-date", default="2024-12-01")
    parser.add_argument("--as-of-date", required=True)
    parser.add_argument("--input-features", default=str(DEFAULT_FEATURES_PATH))
    parser.add_argument("--input-fundamentals", default=str(DEFAULT_FUNDAMENTALS_PATH))
    parser.add_argument("--macro-path", default=None)
    parser.add_argument("--liquidity-path", default=str(DEFAULT_LIQUIDITY_PATH))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-summary-json", default=str(DEFAULT_OUTPUT_SUMMARY_JSON))
    parser.add_argument("--top-decile-ratio", type=float, default=0.10)
    parser.add_argument("--top-n", type=int, default=30)
    parser.add_argument("--dictatorship-mode", choices=["on", "off"], default="off")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = _to_ts(args.start_date)
    as_of = _to_ts(args.as_of_date)
    if start is None or as_of is None:
        raise ValueError("Both --start-date and --as-of-date must be valid dates")
    if as_of < start:
        raise ValueError(f"as-of-date {as_of.date()} is earlier than start-date {start.date()}")

    top_decile_ratio = float(args.top_decile_ratio)
    if not (0.0 < top_decile_ratio <= 1.0):
        raise ValueError("--top-decile-ratio must be in (0, 1].")
    top_n = int(max(1, args.top_n))

    dictatorship_mode = str(args.dictatorship_mode).strip().lower() == "on"
    mode_label = DICTATORSHIP_MODE if dictatorship_mode else DICTATORSHIP_MODE_OFF
    features_path = _resolve_path(args.input_features, DEFAULT_FEATURES_PATH)
    fundamentals_path = _resolve_path(args.input_fundamentals, DEFAULT_FUNDAMENTALS_PATH)
    macro_path = _resolve_path(
        args.macro_path,
        DEFAULT_MACRO_FEATURES_PATH if DEFAULT_MACRO_FEATURES_PATH.exists() else DEFAULT_MACRO_FALLBACK_PATH,
    )
    liquidity_path = _resolve_path(args.liquidity_path, DEFAULT_LIQUIDITY_PATH)
    output_csv = _resolve_path(args.output_csv, DEFAULT_OUTPUT_CSV)
    output_summary_json = _resolve_path(args.output_summary_json, DEFAULT_OUTPUT_SUMMARY_JSON)

    conviction = _load_conviction_frame(
        start_date=start,
        end_date=as_of,
        features_path=features_path,
        fundamentals_path=fundamentals_path,
        macro_path=macro_path,
        liquidity_path=liquidity_path,
        dictatorship_mode=dictatorship_mode,
    )
    if conviction.empty:
        summary = _build_summary(
            pd.DataFrame(),
            start_date=start,
            as_of_date=as_of,
            top_n=top_n,
            dictatorship_mode=dictatorship_mode,
            output_csv=output_csv,
            output_summary_json=output_summary_json,
        )
        _atomic_csv_write(pd.DataFrame(), output_csv)
        _atomic_json_write(summary, output_summary_json)
        print("Phase 22 separability harness complete")
        print("No conviction rows available for the requested window")
        print(f"Mode: {mode_label}")
        print(f"Output: {output_csv}")
        print(f"Summary: {output_summary_json}")
        return 0

    daily = _build_daily_metrics(conviction, top_decile_ratio=top_decile_ratio, top_n=top_n)
    summary = _build_summary(
        daily,
        start_date=start,
        as_of_date=as_of,
        top_n=top_n,
        dictatorship_mode=dictatorship_mode,
        output_csv=output_csv,
        output_summary_json=output_summary_json,
    )

    _atomic_csv_write(daily, output_csv)
    _atomic_json_write(summary, output_summary_json)

    print("Phase 22 separability harness complete")
    print(f"Window: {start.date()} -> {as_of.date()}")
    print(f"Mode: {mode_label}")
    print(
        "Jaccard means: "
        f"top_decile={summary.get('aggregate_metrics', {}).get('jaccard_top_decile', {}).get('mean')} | "
        f"top_{top_n}={summary.get('aggregate_metrics', {}).get(f'jaccard_top_{top_n}', {}).get('mean')}"
    )
    print(
        "Silhouette mean: "
        f"{summary.get('aggregate_metrics', {}).get('silhouette_score', {}).get('mean')}"
    )
    print(
        f"Archetype hit rate (top_{top_n}): "
        f"{summary.get('aggregate_metrics', {}).get(f'archetype_top_{top_n}_hit_rate')}"
    )
    print(f"Output: {output_csv}")
    print(f"Summary: {output_summary_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
