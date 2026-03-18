from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from core.engine import run_simulation  # noqa: E402
from scripts.day5_ablation_report import _atomic_csv_write  # noqa: E402
from scripts.day5_ablation_report import _atomic_json_write  # noqa: E402
from scripts.day5_ablation_report import _load_returns_subset  # noqa: E402
from utils.metrics import compute_cagr  # noqa: E402
from utils.metrics import compute_max_drawdown  # noqa: E402
from utils.metrics import compute_sharpe  # noqa: E402
from utils.metrics import compute_ulcer_index  # noqa: E402


RESEARCH_MAX_DATE = pd.Timestamp("2022-12-31")
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_FEATURES_PATH = PROCESSED_DIR / "features.parquet"
DEFAULT_PANEL_PATH = PROCESSED_DIR / "daily_fundamentals_panel.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_SUMMARY_PATH = PROCESSED_DIR / "phase56_pead_summary.json"
DEFAULT_EVIDENCE_PATH = PROCESSED_DIR / "phase56_pead_evidence.csv"


@dataclass(frozen=True)
class PeadConfig:
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    max_date: pd.Timestamp
    cost_bps: float
    adv_window_days: int
    adv_usd_min: float
    max_days_since_earnings: int
    value_rank_threshold: float
    summary_path: Path
    evidence_path: Path
    features_path: Path = DEFAULT_FEATURES_PATH
    panel_path: Path = DEFAULT_PANEL_PATH
    prices_path: Path = DEFAULT_PRICES_PATH


def validate_config(cfg: PeadConfig) -> None:
    if cfg.max_date > RESEARCH_MAX_DATE:
        raise ValueError(
            f"max_date must be <= {RESEARCH_MAX_DATE.date()}, got {cfg.max_date.date()}"
        )
    if cfg.end_date > cfg.max_date:
        raise ValueError(
            f"end_date must be <= max_date ({cfg.max_date.date()}), got {cfg.end_date.date()}"
        )
    if cfg.start_date > cfg.end_date:
        raise ValueError("start_date must be <= end_date")
    if cfg.adv_window_days <= 0:
        raise ValueError("adv_window_days must be > 0")
    if cfg.adv_usd_min < 0:
        raise ValueError("adv_usd_min must be >= 0")
    if cfg.max_days_since_earnings < 0:
        raise ValueError("max_days_since_earnings must be >= 0")
    if not 0.0 < cfg.value_rank_threshold <= 1.0:
        raise ValueError("value_rank_threshold must be in (0, 1]")


def _sql_escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def load_pead_feature_frame(cfg: PeadConfig) -> pd.DataFrame:
    for path in (cfg.features_path, cfg.panel_path, cfg.prices_path):
        if not path.exists():
            raise FileNotFoundError(f"Missing required artifact: {path}")

    adv_rows = max(int(cfg.adv_window_days) - 1, 0)
    con = duckdb.connect()
    try:
        query = f"""
        WITH feature_base AS (
            SELECT
                CAST(f.date AS DATE) AS date,
                CAST(f.permno AS BIGINT) AS permno,
                CAST(f.ticker AS VARCHAR) AS ticker,
                CAST(f.capital_cycle_score AS DOUBLE) AS capital_cycle_score,
                CAST(f.z_inventory_quality_proxy AS DOUBLE) AS z_inventory_quality_proxy,
                CAST(f.adj_close AS DOUBLE) AS adj_close,
                CAST(f.volume AS DOUBLE) AS volume
            FROM read_parquet('{_sql_escape_path(cfg.features_path)}') AS f
            WHERE CAST(f.date AS DATE) BETWEEN DATE '{cfg.start_date:%Y-%m-%d}'
              AND DATE '{cfg.end_date:%Y-%m-%d}'
              AND CAST(f.date AS DATE) <= DATE '{cfg.max_date:%Y-%m-%d}'
              AND f.capital_cycle_score IS NOT NULL
        ),
        enriched AS (
            SELECT
                fb.date,
                fb.permno,
                fb.ticker,
                fb.capital_cycle_score,
                fb.z_inventory_quality_proxy,
                AVG(fb.adj_close * fb.volume) OVER (
                    PARTITION BY fb.permno
                    ORDER BY fb.date
                    ROWS BETWEEN {adv_rows} PRECEDING AND CURRENT ROW
                ) AS adv_usd,
                DATE_DIFF('day', CAST(p.release_date AS DATE), fb.date) AS days_since_earnings,
                CAST(p.quality_pass AS INTEGER) AS quality_pass,
                CAST(p.release_date AS DATE) AS release_date
            FROM feature_base AS fb
            LEFT JOIN read_parquet('{_sql_escape_path(cfg.panel_path)}') AS p
              ON CAST(p.date AS DATE) = fb.date
             AND CAST(p.permno AS BIGINT) = fb.permno
        )
        SELECT
            date,
            permno,
            ticker,
            capital_cycle_score,
            z_inventory_quality_proxy,
            adv_usd,
            days_since_earnings,
            quality_pass,
            release_date
        FROM enriched
        ORDER BY date, permno
        """
        frame = con.execute(query).df()
    finally:
        con.close()

    if frame.empty:
        return frame

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["release_date"] = pd.to_datetime(frame["release_date"], errors="coerce")
    frame["permno"] = pd.to_numeric(frame["permno"], errors="coerce").astype("Int64")
    frame["capital_cycle_score"] = pd.to_numeric(frame["capital_cycle_score"], errors="coerce")
    frame["z_inventory_quality_proxy"] = pd.to_numeric(
        frame["z_inventory_quality_proxy"], errors="coerce"
    )
    frame["adv_usd"] = pd.to_numeric(frame["adv_usd"], errors="coerce")
    frame["days_since_earnings"] = pd.to_numeric(frame["days_since_earnings"], errors="coerce")
    frame["quality_pass"] = pd.to_numeric(frame["quality_pass"], errors="coerce").fillna(0).astype(int)
    frame["ticker"] = frame["ticker"].astype(str).str.upper().str.strip()
    frame = frame.dropna(subset=["date", "permno", "capital_cycle_score"]).copy()
    frame["permno"] = frame["permno"].astype(int)
    return frame


def select_pead_candidates(frame: pd.DataFrame, cfg: PeadConfig) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    work = frame.copy()
    gate_mask = (
        work["adv_usd"].ge(float(cfg.adv_usd_min))
        & work["days_since_earnings"].between(0, int(cfg.max_days_since_earnings), inclusive="both")
        & work["quality_pass"].eq(1)
    )
    work = work.loc[gate_mask].copy()
    if work.empty:
        return work

    work["value_rank_pct"] = work.groupby("date")["capital_cycle_score"].rank(
        method="first",
        pct=True,
        ascending=True,
    )
    work = work.loc[work["value_rank_pct"] >= float(cfg.value_rank_threshold)].copy()
    work["score"] = pd.to_numeric(work["capital_cycle_score"], errors="coerce")
    work["score_valid"] = work["score"].notna()
    return work.sort_values(["date", "permno"]).reset_index(drop=True)


def build_pead_target_weights(selected: pd.DataFrame) -> pd.DataFrame:
    if selected.empty:
        return pd.DataFrame(index=pd.DatetimeIndex([], name="date"))

    work = selected.loc[
        pd.to_numeric(selected["score_valid"], errors="coerce").fillna(False).astype(bool),
        ["date", "permno"],
    ].copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work["permno"] = pd.to_numeric(work["permno"], errors="coerce")
    work = work.dropna(subset=["date", "permno"]).sort_values(["date", "permno"])
    if work.empty:
        return pd.DataFrame(index=pd.DatetimeIndex([], name="date"))

    all_dates = pd.DatetimeIndex(sorted(work["date"].unique()), name="date")
    work["target_weight"] = 1.0 / work.groupby("date")["permno"].transform("size")
    target = (
        work.pivot(index="date", columns="permno", values="target_weight")
        .sort_index()
        .fillna(0.0)
    )
    target = target.reindex(all_dates).fillna(0.0)
    target.columns = pd.Index(pd.to_numeric(target.columns, errors="coerce").astype(int))
    return target


def summarize_simulation(
    *,
    sim: pd.DataFrame,
    weights: pd.DataFrame,
    selected: pd.DataFrame,
    cfg: PeadConfig,
) -> dict[str, Any]:
    out = sim.copy()
    out["equity"] = (1.0 + pd.to_numeric(out["net_ret"], errors="coerce").fillna(0.0)).cumprod()
    n_positions = weights.gt(0.0).sum(axis=1).astype(int)

    return {
        "strategy_id": "PHASE56_PEAD_CAPITAL_CYCLE_V1",
        "start_date": cfg.start_date.strftime("%Y-%m-%d"),
        "end_date": cfg.end_date.strftime("%Y-%m-%d"),
        "max_date": cfg.max_date.strftime("%Y-%m-%d"),
        "cost_bps": float(cfg.cost_bps),
        "value_rank_threshold": float(cfg.value_rank_threshold),
        "adv_window_days": int(cfg.adv_window_days),
        "adv_usd_min": float(cfg.adv_usd_min),
        "max_days_since_earnings": int(cfg.max_days_since_earnings),
        "same_engine": True,
        "rows": int(len(out)),
        "candidate_rows": int(len(selected)),
        "candidate_permnos": int(selected["permno"].nunique()) if not selected.empty else 0,
        "candidate_dates": int(selected["date"].nunique()) if not selected.empty else 0,
        "avg_positions": float(n_positions.mean()) if len(n_positions) else 0.0,
        "max_positions": int(n_positions.max()) if len(n_positions) else 0,
        "sharpe": float(compute_sharpe(out["net_ret"])),
        "cagr": float(compute_cagr(out["equity"])),
        "max_dd": float(compute_max_drawdown(out["equity"])),
        "ulcer": float(compute_ulcer_index(out["equity"])),
        "turnover_annual": float(pd.to_numeric(out["turnover"], errors="coerce").mean() * 252.0),
        "turnover_total": float(pd.to_numeric(out["turnover"], errors="coerce").sum()),
        "net_return_total": float(out["equity"].iloc[-1] - 1.0) if not out.empty else 0.0,
        "mean_net_ret": float(pd.to_numeric(out["net_ret"], errors="coerce").mean()),
        "mean_gross_ret": float(pd.to_numeric(out["gross_ret"], errors="coerce").mean()),
    }


def build_evidence_frame(sim: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
    evidence = sim.copy().reset_index().rename(columns={"index": "date"})
    evidence["date"] = pd.to_datetime(evidence["date"], errors="coerce")
    evidence["equity"] = (1.0 + pd.to_numeric(evidence["net_ret"], errors="coerce").fillna(0.0)).cumprod()
    evidence["n_positions"] = weights.gt(0.0).sum(axis=1).reindex(weights.index).astype(int).values
    return evidence


def run_pead(cfg: PeadConfig) -> dict[str, Any]:
    validate_config(cfg)

    feature_frame = load_pead_feature_frame(cfg)
    selected = select_pead_candidates(feature_frame, cfg)
    if selected.empty:
        raise RuntimeError("No PEAD candidates passed the bounded Phase 56 gates.")

    weights = build_pead_target_weights(selected)
    permnos = sorted(int(c) for c in weights.columns)
    returns_long = _load_returns_subset(
        prices_path=cfg.prices_path,
        permnos=permnos,
        start_date=cfg.start_date,
        end_date=cfg.end_date,
    )
    if returns_long.empty:
        raise RuntimeError("No return rows found for the bounded Phase 56 PEAD window.")

    returns_wide = (
        returns_long.assign(
            date=pd.to_datetime(returns_long["date"], errors="coerce"),
            permno=pd.to_numeric(returns_long["permno"], errors="coerce"),
            ret=pd.to_numeric(returns_long["ret"], errors="coerce"),
        )
        .dropna(subset=["date", "permno"])
        .pivot(index="date", columns="permno", values="ret")
        .sort_index()
        .reindex(index=weights.index, columns=weights.columns)
    )

    sim = run_simulation(
        target_weights=weights,
        returns_df=returns_wide,
        cost_bps=float(cfg.cost_bps) / 10000.0,
        strict_missing_returns=False,
    )
    sim.index = pd.to_datetime(sim.index, errors="coerce")

    summary = summarize_simulation(sim=sim, weights=weights, selected=selected, cfg=cfg)
    summary["summary_path"] = str(cfg.summary_path)
    summary["evidence_path"] = str(cfg.evidence_path)
    summary["source_paths"] = {
        "features_path": str(cfg.features_path),
        "panel_path": str(cfg.panel_path),
        "prices_path": str(cfg.prices_path),
        "event_study_harness": str(PROJECT_ROOT / "backtests" / "event_study_csco.py"),
        "engine_path": str(PROJECT_ROOT / "core" / "engine.py"),
    }

    evidence = build_evidence_frame(sim=sim, weights=weights)
    cfg.summary_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_write(summary, cfg.summary_path)
    _atomic_csv_write(evidence, cfg.evidence_path)
    return summary


def parse_args() -> PeadConfig:
    parser = argparse.ArgumentParser(description="Phase 56 bounded PEAD runner.")
    parser.add_argument("--start-date", default="2000-01-01")
    parser.add_argument("--end-date", default="2022-12-31")
    parser.add_argument("--max-date", default="2022-12-31")
    parser.add_argument("--cost-bps", type=float, default=5.0)
    parser.add_argument("--adv-window-days", type=int, default=20)
    parser.add_argument("--adv-usd-min", type=float, default=5_000_000.0)
    parser.add_argument("--max-days-since-earnings", type=int, default=63)
    parser.add_argument("--value-rank-threshold", type=float, default=0.60)
    parser.add_argument("--summary-path", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--evidence-path", default=str(DEFAULT_EVIDENCE_PATH))
    args = parser.parse_args()

    return PeadConfig(
        start_date=pd.Timestamp(args.start_date),
        end_date=pd.Timestamp(args.end_date),
        max_date=pd.Timestamp(args.max_date),
        cost_bps=float(args.cost_bps),
        adv_window_days=int(args.adv_window_days),
        adv_usd_min=float(args.adv_usd_min),
        max_days_since_earnings=int(args.max_days_since_earnings),
        value_rank_threshold=float(args.value_rank_threshold),
        summary_path=Path(args.summary_path),
        evidence_path=Path(args.evidence_path),
    )


def main() -> None:
    cfg = parse_args()
    summary = run_pead(cfg)

    print("=" * 72)
    print("Phase 56 PEAD Runner")
    print("=" * 72)
    print(f"Window          : {summary['start_date']} .. {summary['end_date']}")
    print(f"Max Date        : {summary['max_date']}")
    print(f"Cost (bps)      : {summary['cost_bps']:.2f}")
    print(f"Candidate Rows  : {summary['candidate_rows']:,}")
    print(f"Candidate Dates : {summary['candidate_dates']:,}")
    print(f"Candidate Names : {summary['candidate_permnos']:,}")
    print(f"Avg Positions   : {summary['avg_positions']:.2f}")
    print(f"Max Positions   : {summary['max_positions']}")
    print(f"Sharpe          : {summary['sharpe']:.4f}")
    print(f"CAGR            : {summary['cagr']:.4f}")
    print(f"Max Drawdown    : {summary['max_dd']:.4f}")
    print(f"Ulcer           : {summary['ulcer']:.4f}")
    print(f"Turnover Annual : {summary['turnover_annual']:.4f}")
    print(f"Turnover Total  : {summary['turnover_total']:.4f}")
    print(f"Net Return      : {summary['net_return_total']:.4f}")
    print(f"Summary JSON    : {summary['summary_path']}")
    print(f"Evidence CSV    : {summary['evidence_path']}")
    print("=" * 72)


if __name__ == "__main__":
    main()
