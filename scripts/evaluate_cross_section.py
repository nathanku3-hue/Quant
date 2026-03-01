from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from typing import Any

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
STATIC_DIR = os.path.join(PROJECT_ROOT, "data", "static")

DEFAULT_PANEL_PATH = os.path.join(PROCESSED_DIR, "daily_fundamentals_panel.parquet")
DEFAULT_PRICES_PATH = os.path.join(PROCESSED_DIR, "prices.parquet")
DEFAULT_FEATURES_PATH = os.path.join(PROCESSED_DIR, "features.parquet")
DEFAULT_SECTOR_MAP_PATH = os.path.join(STATIC_DIR, "sector_map.parquet")


@dataclass(frozen=True)
class EvalConfig:
    panel_path: str = DEFAULT_PANEL_PATH
    prices_path: str = DEFAULT_PRICES_PATH
    features_path: str = DEFAULT_FEATURES_PATH
    sector_map_path: str = DEFAULT_SECTOR_MAP_PATH
    start_date: str | None = None
    end_date: str | None = None
    horizon_days: int = 21
    high_asset_growth_pct: float = 0.30
    min_high_group_size: int = 2
    nw_lags: int | None = None
    run_fama_macbeth: bool = True
    fm_min_obs: int = 30
    output_dir: str = PROCESSED_DIR
    output_prefix: str = "phase17_1_cross_section"


def _sql_escape_path(path: str) -> str:
    return path.replace("\\", "/").replace("'", "''")


def _atomic_write_csv(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    try:
        df.to_csv(tmp, index=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _atomic_write_json(payload: dict[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def auto_newey_west_lags(n_obs: int) -> int:
    if n_obs <= 1:
        return 0
    lag = int(np.floor(4.0 * ((float(n_obs) / 100.0) ** (2.0 / 9.0))))
    return max(0, min(lag, int(n_obs - 1)))


def newey_west_mean_test(series: pd.Series, maxlags: int | None = None) -> dict[str, float | int]:
    y = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    n_obs = int(len(y))
    if n_obs < 3:
        return {
            "mean": float("nan"),
            "se": float("nan"),
            "t_stat": float("nan"),
            "p_value": float("nan"),
            "n_obs": n_obs,
            "nw_lag": 0,
        }
    lag = auto_newey_west_lags(n_obs) if maxlags is None else max(int(maxlags), 0)
    lag = min(lag, n_obs - 1)
    x = np.ones((n_obs, 1), dtype=float)
    fit = sm.OLS(y.to_numpy(dtype=float), x).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    return {
        "mean": float(fit.params[0]),
        "se": float(fit.bse[0]),
        "t_stat": float(fit.tvalues[0]),
        "p_value": float(fit.pvalues[0]),
        "n_obs": n_obs,
        "nw_lag": int(lag),
    }


def _rank_to_decile(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    out = pd.Series(np.nan, index=series.index, dtype="float64")
    valid = s.dropna().sort_values(kind="mergesort")
    n = len(valid)
    if n == 0:
        return out
    if n == 1:
        out.loc[valid.index] = 10.0
        return out
    positions = np.arange(n, dtype=float)
    deciles = np.floor(positions * 9.0 / float(n - 1)) + 1.0
    out.loc[valid.index] = deciles
    return out


def load_eval_frame(cfg: EvalConfig) -> pd.DataFrame:
    for path in [cfg.panel_path, cfg.prices_path, cfg.features_path, cfg.sector_map_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required artifact: {path}")

    filters: list[str] = []
    if cfg.start_date:
        filters.append(f"CAST(date AS DATE) >= DATE '{cfg.start_date}'")
    if cfg.end_date:
        filters.append(f"CAST(date AS DATE) <= DATE '{cfg.end_date}'")
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    q = f"""
    WITH prices_base AS (
        SELECT
            CAST(date AS DATE) AS date,
            CAST(permno AS BIGINT) AS permno,
            CAST(adj_close AS DOUBLE) AS adj_close
        FROM read_parquet('{_sql_escape_path(cfg.prices_path)}')
        {where_clause}
    ),
    forward_ret AS (
        SELECT
            date,
            permno,
            LEAD(adj_close, {int(cfg.horizon_days)}) OVER (
                PARTITION BY permno
                ORDER BY date
            ) / NULLIF(adj_close, 0.0) - 1.0 AS fwd_return
        FROM prices_base
    ),
    panel AS (
        SELECT
            CAST(date AS DATE) AS date,
            CAST(permno AS BIGINT) AS permno,
            UPPER(TRIM(CAST(ticker AS VARCHAR))) AS ticker,
            CAST(asset_growth_yoy AS DOUBLE) AS asset_growth_yoy,
            CAST(operating_margin_delta_q AS DOUBLE) AS operating_margin_delta_q,
            CAST(delta_revenue_inventory AS DOUBLE) AS delta_revenue_inventory,
            CAST(revenue_inventory_q AS DOUBLE) AS revenue_inventory_q
        FROM read_parquet('{_sql_escape_path(cfg.panel_path)}')
        {where_clause}
    ),
    features AS (
        SELECT
            CAST(date AS DATE) AS date,
            CAST(permno AS BIGINT) AS permno,
            CAST(z_inventory_quality_proxy AS DOUBLE) AS z_inventory_quality_proxy,
            CAST(z_discipline_cond AS DOUBLE) AS z_discipline_cond
        FROM read_parquet('{_sql_escape_path(cfg.features_path)}')
        {where_clause}
    ),
    sector_map AS (
        SELECT
            CAST(permno AS BIGINT) AS permno,
            UPPER(TRIM(CAST(ticker AS VARCHAR))) AS ticker,
            TRIM(CAST(industry AS VARCHAR)) AS industry,
            UPPER(TRIM(CAST(quote_type AS VARCHAR))) AS quote_type,
            TRY_CAST(updated_at AS TIMESTAMP) AS updated_at
        FROM read_parquet('{_sql_escape_path(cfg.sector_map_path)}')
    ),
    sector_ranked AS (
        SELECT
            permno,
            ticker,
            industry,
            quote_type,
            ROW_NUMBER() OVER (
                PARTITION BY permno
                ORDER BY updated_at DESC NULLS LAST, industry, ticker
            ) AS rn_permno,
            ROW_NUMBER() OVER (
                PARTITION BY ticker
                ORDER BY updated_at DESC NULLS LAST, industry, permno
            ) AS rn_ticker
        FROM sector_map
    ),
    sector_by_permno AS (
        SELECT
            permno,
            industry,
            quote_type
        FROM sector_ranked
        WHERE rn_permno = 1
    ),
    sector_by_ticker AS (
        SELECT
            ticker,
            industry,
            quote_type
        FROM sector_ranked
        WHERE rn_ticker = 1
    )
    SELECT
        fr.date,
        fr.permno,
        p.asset_growth_yoy,
        p.operating_margin_delta_q,
        p.delta_revenue_inventory,
        p.revenue_inventory_q,
        f.z_inventory_quality_proxy,
        f.z_discipline_cond,
        fr.fwd_return,
        COALESCE(sp.industry, st.industry, 'Unknown') AS industry,
        UPPER(COALESCE(sp.quote_type, st.quote_type, 'UNKNOWN')) AS quote_type
    FROM forward_ret fr
    INNER JOIN panel p
        ON fr.date = p.date
       AND fr.permno = p.permno
    INNER JOIN features f
        ON fr.date = f.date
       AND fr.permno = f.permno
    LEFT JOIN sector_by_permno sp
        ON p.permno = sp.permno
    LEFT JOIN sector_by_ticker st
        ON p.ticker = st.ticker
    WHERE fr.fwd_return IS NOT NULL
      AND p.asset_growth_yoy IS NOT NULL
      AND f.z_inventory_quality_proxy IS NOT NULL
      AND UPPER(COALESCE(sp.quote_type, st.quote_type, 'UNKNOWN')) = 'EQUITY'
      AND COALESCE(sp.industry, st.industry, 'Unknown') <> 'Unknown'
    ORDER BY fr.date, fr.permno
    """

    con = duckdb.connect()
    try:
        out = con.execute(q).df()
    finally:
        con.close()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    return out.dropna(subset=["date"]).sort_values(["date", "permno"]).reset_index(drop=True)


def compute_double_sort(
    frame: pd.DataFrame,
    high_asset_growth_pct: float = 0.30,
    min_high_group_size: int = 2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {
        "date",
        "permno",
        "industry",
        "asset_growth_yoy",
        "z_inventory_quality_proxy",
        "fwd_return",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns for double sort: {missing}")

    work = frame.copy()
    work = work.dropna(subset=["date", "permno", "industry", "asset_growth_yoy", "z_inventory_quality_proxy", "fwd_return"])
    if work.empty:
        return pd.DataFrame(columns=["date", "decile_1", "decile_10", "spread", "n_short", "n_long"]), work

    high_threshold = 1.0 - float(high_asset_growth_pct)
    work["ag_rank_pct"] = work.groupby(["date", "industry"])["asset_growth_yoy"].rank(method="first", pct=True)
    work["is_high_asset_growth"] = work["ag_rank_pct"] >= high_threshold
    high = work[work["is_high_asset_growth"]].copy()
    if high.empty:
        return pd.DataFrame(columns=["date", "decile_1", "decile_10", "spread", "n_short", "n_long"]), high

    high["high_group_size"] = high.groupby(["date", "industry"])["permno"].transform("size")
    if int(min_high_group_size) > 0:
        high = high[high["high_group_size"] >= int(min_high_group_size)].copy()
    if high.empty:
        return pd.DataFrame(columns=["date", "decile_1", "decile_10", "spread", "n_short", "n_long"]), high

    high["proxy_decile"] = (
        high.groupby(["date", "industry"], group_keys=False)["z_inventory_quality_proxy"]
        .transform(_rank_to_decile)
        .astype("Int64")
    )
    high = high.dropna(subset=["proxy_decile"]).copy()
    if high.empty:
        return pd.DataFrame(columns=["date", "decile_1", "decile_10", "spread", "n_short", "n_long"]), high
    high["proxy_decile"] = high["proxy_decile"].astype(int)

    decile_ret = (
        high.groupby(["date", "proxy_decile"])["fwd_return"]
        .mean()
        .unstack("proxy_decile")
        .sort_index()
    )
    for d in range(1, 11):
        if d not in decile_ret.columns:
            decile_ret[d] = np.nan
    decile_ret = decile_ret.reindex(columns=list(range(1, 11)))
    decile_ret = decile_ret.rename(columns={d: f"decile_{d}" for d in range(1, 11)})

    n_short = high[high["proxy_decile"] == 1].groupby("date")["permno"].nunique()
    n_long = high[high["proxy_decile"] == 10].groupby("date")["permno"].nunique()

    spread_df = pd.DataFrame(index=decile_ret.index)
    spread_df["decile_1"] = decile_ret["decile_1"]
    spread_df["decile_10"] = decile_ret["decile_10"]
    spread_df["spread"] = spread_df["decile_10"] - spread_df["decile_1"]
    spread_df["n_short"] = n_short.reindex(spread_df.index).fillna(0).astype(int)
    spread_df["n_long"] = n_long.reindex(spread_df.index).fillna(0).astype(int)
    spread_df = spread_df.reset_index().rename(columns={"index": "date"})
    spread_df["date"] = pd.to_datetime(spread_df["date"], errors="coerce")
    return spread_df.sort_values("date").reset_index(drop=True), high


def summarize_spread(spread_df: pd.DataFrame, horizon_days: int, nw_lags: int | None = None) -> dict[str, float | int | bool]:
    if spread_df.empty or "spread" not in spread_df.columns:
        return {
            "period_mean": float("nan"),
            "period_vol": float("nan"),
            "period_sharpe": float("nan"),
            "annualized_sharpe": float("nan"),
            "t_stat_nw": float("nan"),
            "p_value_nw": float("nan"),
            "nw_lag": 0,
            "n_periods": 0,
            "pass_spread_positive": False,
            "pass_tstat_gt_3": False,
            "pass_all": False,
        }
    s = pd.to_numeric(spread_df["spread"], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    n_periods = int(len(s))
    if n_periods < 2:
        return {
            "period_mean": float("nan"),
            "period_vol": float("nan"),
            "period_sharpe": float("nan"),
            "annualized_sharpe": float("nan"),
            "t_stat_nw": float("nan"),
            "p_value_nw": float("nan"),
            "nw_lag": 0,
            "n_periods": n_periods,
            "pass_spread_positive": False,
            "pass_tstat_gt_3": False,
            "pass_all": False,
        }
    period_mean = float(s.mean())
    period_vol = float(s.std(ddof=1))
    period_sharpe = float(period_mean / period_vol) if np.isfinite(period_vol) and period_vol > 0 else float("nan")
    annualization = np.sqrt(252.0 / max(float(horizon_days), 1.0))
    annualized_sharpe = float(period_sharpe * annualization) if np.isfinite(period_sharpe) else float("nan")
    nw = newey_west_mean_test(s, maxlags=nw_lags)
    pass_spread_positive = bool(np.isfinite(period_mean) and period_mean > 0.0)
    pass_tstat_gt_3 = bool(np.isfinite(nw["t_stat"]) and float(nw["t_stat"]) > 3.0)
    return {
        "period_mean": period_mean,
        "period_vol": period_vol,
        "period_sharpe": period_sharpe,
        "annualized_sharpe": annualized_sharpe,
        "t_stat_nw": float(nw["t_stat"]),
        "p_value_nw": float(nw["p_value"]),
        "nw_lag": int(nw["nw_lag"]),
        "n_periods": int(nw["n_obs"]),
        "pass_spread_positive": pass_spread_positive,
        "pass_tstat_gt_3": pass_tstat_gt_3,
        "pass_all": bool(pass_spread_positive and pass_tstat_gt_3),
    }


def run_fama_macbeth(
    frame: pd.DataFrame,
    nw_lags: int | None = None,
    min_obs: int = 30,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    needed = {"date", "fwd_return", "asset_growth_yoy", "z_inventory_quality_proxy"}
    missing = sorted(needed - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns for Fama-MacBeth: {missing}")

    work = frame[["date", "fwd_return", "asset_growth_yoy", "z_inventory_quality_proxy"]].copy()
    work = work.dropna()
    work["interaction"] = work["asset_growth_yoy"] * work["z_inventory_quality_proxy"]
    work = work.replace([np.inf, -np.inf], np.nan).dropna()

    beta_rows: list[dict[str, Any]] = []
    min_obs = max(int(min_obs), 4)
    for dt, grp in work.groupby("date", sort=True):
        if len(grp) < min_obs:
            continue
        x = grp[["asset_growth_yoy", "z_inventory_quality_proxy", "interaction"]]
        y = grp["fwd_return"]
        x = sm.add_constant(x, has_constant="add")
        fit = sm.OLS(y.to_numpy(dtype=float), x.to_numpy(dtype=float)).fit()
        beta_rows.append(
            {
                "date": pd.Timestamp(dt),
                "n_obs": int(len(grp)),
                "r_squared": float(fit.rsquared),
                "beta_const": float(fit.params[0]),
                "beta_asset_growth": float(fit.params[1]),
                "beta_z_proxy": float(fit.params[2]),
                "beta_interaction": float(fit.params[3]),
            }
        )

    beta_df = pd.DataFrame(beta_rows)
    if beta_df.empty:
        return beta_df, pd.DataFrame(
            columns=[
                "coefficient",
                "mean_beta",
                "nw_t_stat",
                "nw_p_value",
                "nw_lag",
                "n_periods",
            ]
        )
    beta_df = beta_df.sort_values("date").reset_index(drop=True)

    summary_rows: list[dict[str, Any]] = []
    for col in ["beta_const", "beta_asset_growth", "beta_z_proxy", "beta_interaction"]:
        nw = newey_west_mean_test(beta_df[col], maxlags=nw_lags)
        summary_rows.append(
            {
                "coefficient": col,
                "mean_beta": float(nw["mean"]),
                "nw_t_stat": float(nw["t_stat"]),
                "nw_p_value": float(nw["p_value"]),
                "nw_lag": int(nw["nw_lag"]),
                "n_periods": int(nw["n_obs"]),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    return beta_df, summary_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 17.1 cross-sectional double-sort evaluator.")
    parser.add_argument("--panel-path", default=DEFAULT_PANEL_PATH)
    parser.add_argument("--prices-path", default=DEFAULT_PRICES_PATH)
    parser.add_argument("--features-path", default=DEFAULT_FEATURES_PATH)
    parser.add_argument("--sector-map-path", default=DEFAULT_SECTOR_MAP_PATH)
    parser.add_argument("--start-date", default=None, help="Optional lower bound (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=None, help="Optional upper bound (YYYY-MM-DD)")
    parser.add_argument("--horizon-days", type=int, default=21, help="Forward return horizon in trading days (e.g. 21 or 63).")
    parser.add_argument("--high-asset-growth-pct", type=float, default=0.30, help="Top percentile bucket for Sort 1.")
    parser.add_argument("--min-high-group-size", type=int, default=2, help="Minimum names per Date/Industry high-growth group.")
    parser.add_argument("--nw-lags", type=int, default=None, help="Newey-West max lags (default: auto rule).")
    parser.add_argument("--skip-fama-macbeth", action="store_true")
    parser.add_argument("--fm-min-obs", type=int, default=30, help="Minimum cross-sectional rows per date for FM regression.")
    parser.add_argument("--output-dir", default=PROCESSED_DIR)
    parser.add_argument("--output-prefix", default="phase17_1_cross_section")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = EvalConfig(
        panel_path=str(args.panel_path),
        prices_path=str(args.prices_path),
        features_path=str(args.features_path),
        sector_map_path=str(args.sector_map_path),
        start_date=str(args.start_date) if args.start_date else None,
        end_date=str(args.end_date) if args.end_date else None,
        horizon_days=int(args.horizon_days),
        high_asset_growth_pct=float(args.high_asset_growth_pct),
        min_high_group_size=int(args.min_high_group_size),
        nw_lags=int(args.nw_lags) if args.nw_lags is not None else None,
        run_fama_macbeth=(not bool(args.skip_fama_macbeth)),
        fm_min_obs=int(args.fm_min_obs),
        output_dir=str(args.output_dir),
        output_prefix=str(args.output_prefix),
    )

    os.makedirs(cfg.output_dir, exist_ok=True)
    spread_path = os.path.join(cfg.output_dir, f"{cfg.output_prefix}_spread_timeseries.csv")
    summary_path = os.path.join(cfg.output_dir, f"{cfg.output_prefix}_summary.json")
    fm_betas_path = os.path.join(cfg.output_dir, f"{cfg.output_prefix}_fama_macbeth_betas.csv")
    fm_summary_path = os.path.join(cfg.output_dir, f"{cfg.output_prefix}_fama_macbeth_summary.csv")

    frame = load_eval_frame(cfg)
    spread_df, sorted_frame = compute_double_sort(
        frame=frame,
        high_asset_growth_pct=cfg.high_asset_growth_pct,
        min_high_group_size=cfg.min_high_group_size,
    )
    spread_summary = summarize_spread(
        spread_df=spread_df,
        horizon_days=cfg.horizon_days,
        nw_lags=cfg.nw_lags,
    )

    _atomic_write_csv(spread_df, spread_path)

    summary_payload: dict[str, Any] = {
        "config": {
            "panel_path": cfg.panel_path,
            "prices_path": cfg.prices_path,
            "features_path": cfg.features_path,
            "sector_map_path": cfg.sector_map_path,
            "start_date": cfg.start_date,
            "end_date": cfg.end_date,
            "horizon_days": cfg.horizon_days,
            "high_asset_growth_pct": cfg.high_asset_growth_pct,
            "min_high_group_size": cfg.min_high_group_size,
            "nw_lags": cfg.nw_lags,
            "run_fama_macbeth": cfg.run_fama_macbeth,
            "fm_min_obs": cfg.fm_min_obs,
        },
        "sample": {
            "rows_loaded": int(len(frame)),
            "rows_sorted": int(len(sorted_frame)),
            "spread_periods": int(spread_summary["n_periods"]),
        },
        "double_sort": spread_summary,
        "artifacts": {
            "spread_timeseries_csv": spread_path,
            "summary_json": summary_path,
        },
    }

    print("Double-Sort Summary")
    print(
        f"  Spread mean={spread_summary['period_mean']:.6f}, "
        f"vol={spread_summary['period_vol']:.6f}, "
        f"Sharpe(ann)={spread_summary['annualized_sharpe']:.3f}, "
        f"t_NW={spread_summary['t_stat_nw']:.3f}, "
        f"lag={spread_summary['nw_lag']}, "
        f"periods={spread_summary['n_periods']}"
    )
    print(
        f"  Pass criteria: spread>0={spread_summary['pass_spread_positive']}, "
        f"t_stat>3={spread_summary['pass_tstat_gt_3']}, "
        f"overall={spread_summary['pass_all']}"
    )

    if cfg.run_fama_macbeth:
        fm_betas, fm_summary = run_fama_macbeth(
            frame=frame,
            nw_lags=cfg.nw_lags,
            min_obs=cfg.fm_min_obs,
        )
        _atomic_write_csv(fm_betas, fm_betas_path)
        _atomic_write_csv(fm_summary, fm_summary_path)
        interaction = fm_summary[fm_summary["coefficient"] == "beta_interaction"]
        interaction_mean = float(interaction["mean_beta"].iloc[0]) if not interaction.empty else float("nan")
        interaction_t = float(interaction["nw_t_stat"].iloc[0]) if not interaction.empty else float("nan")
        interaction_p = float(interaction["nw_p_value"].iloc[0]) if not interaction.empty else float("nan")
        interaction_pass = bool(np.isfinite(interaction_mean) and np.isfinite(interaction_p) and interaction_mean > 0.0 and interaction_p < 0.05)
        summary_payload["fama_macbeth"] = {
            "coefficients": fm_summary.to_dict(orient="records"),
            "interaction_pass_positive_significant": interaction_pass,
            "interaction_mean_beta": interaction_mean,
            "interaction_nw_t_stat": interaction_t,
            "interaction_nw_p_value": interaction_p,
            "n_periods": int(len(fm_betas)),
            "artifacts": {
                "betas_csv": fm_betas_path,
                "summary_csv": fm_summary_path,
            },
        }
        print("Fama-MacBeth Summary")
        print(
            f"  interaction mean={interaction_mean:.6f}, "
            f"t_NW={interaction_t:.3f}, p={interaction_p:.6f}, "
            f"pass={interaction_pass}"
        )

    _atomic_write_json(summary_payload, summary_path)
    print(f"Wrote: {spread_path}")
    print(f"Wrote: {summary_path}")
    if cfg.run_fama_macbeth:
        print(f"Wrote: {fm_betas_path}")
        print(f"Wrote: {fm_summary_path}")


if __name__ == "__main__":
    main()
