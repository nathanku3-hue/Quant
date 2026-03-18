from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
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
DEFAULT_BASELINE_SUMMARY_PATH = PROCESSED_DIR / "phase54_core_sleeve_summary.json"
DEFAULT_SUMMARY_PATH = PROCESSED_DIR / "phase57_corporate_actions_summary.json"
DEFAULT_EVIDENCE_PATH = PROCESSED_DIR / "phase57_corporate_actions_evidence.csv"
DEFAULT_DELTA_PATH = PROCESSED_DIR / "phase57_corporate_actions_delta_vs_c3.csv"


@dataclass(frozen=True)
class CorporateActionsConfig:
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    max_date: pd.Timestamp
    cost_bps: float
    adv_window_days: int
    adv_usd_min: float
    event_yield_min: float
    event_yield_max: float
    value_rank_threshold: float
    summary_path: Path
    evidence_path: Path
    delta_path: Path
    baseline_summary_path: Path
    features_path: Path = DEFAULT_FEATURES_PATH
    panel_path: Path = DEFAULT_PANEL_PATH
    prices_path: Path = DEFAULT_PRICES_PATH


def validate_config(cfg: CorporateActionsConfig) -> None:
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
    if cfg.event_yield_min < 0:
        raise ValueError("event_yield_min must be >= 0")
    if cfg.event_yield_max <= cfg.event_yield_min:
        raise ValueError("event_yield_max must be > event_yield_min")
    if not 0.0 < cfg.value_rank_threshold <= 1.0:
        raise ValueError("value_rank_threshold must be in (0, 1]")


def _sql_escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def load_trading_dates(cfg: CorporateActionsConfig) -> pd.DatetimeIndex:
    if not cfg.prices_path.exists():
        raise FileNotFoundError(f"Missing required artifact: {cfg.prices_path}")

    con = duckdb.connect()
    try:
        query = f"""
        SELECT DISTINCT CAST(date AS DATE) AS date
        FROM read_parquet('{_sql_escape_path(cfg.prices_path)}')
        WHERE CAST(date AS DATE) BETWEEN DATE '{cfg.start_date:%Y-%m-%d}'
          AND DATE '{cfg.end_date:%Y-%m-%d}'
          AND CAST(date AS DATE) <= DATE '{cfg.max_date:%Y-%m-%d}'
        ORDER BY date
        """
        out = con.execute(query).df()
    finally:
        con.close()

    idx = pd.DatetimeIndex(pd.to_datetime(out["date"], errors="coerce").dropna().unique(), name="date")
    if len(idx) == 0:
        raise RuntimeError("No trading dates found for the bounded Phase 57 window.")
    return idx


def load_corporate_action_frame(cfg: CorporateActionsConfig) -> pd.DataFrame:
    for path in (cfg.features_path, cfg.panel_path, cfg.prices_path):
        if not path.exists():
            raise FileNotFoundError(f"Missing required artifact: {path}")

    adv_rows = max(int(cfg.adv_window_days) - 1, 0)
    con = duckdb.connect()
    try:
        query = f"""
        WITH price_base AS (
            SELECT
                CAST(p.date AS DATE) AS date,
                CAST(p.permno AS BIGINT) AS permno,
                CAST(p.raw_close AS DOUBLE) AS raw_close,
                CAST(p.total_ret AS DOUBLE) AS total_ret,
                CAST(p.volume AS DOUBLE) AS volume
            FROM read_parquet('{_sql_escape_path(cfg.prices_path)}') AS p
            WHERE CAST(p.date AS DATE) BETWEEN DATE '{cfg.start_date:%Y-%m-%d}'
              AND DATE '{cfg.end_date:%Y-%m-%d}'
              AND CAST(p.date AS DATE) <= DATE '{cfg.max_date:%Y-%m-%d}'
        ),
        priced AS (
            SELECT
                pb.date,
                pb.permno,
                pb.raw_close,
                pb.total_ret,
                AVG(pb.raw_close * pb.volume) OVER (
                    PARTITION BY pb.permno
                    ORDER BY pb.date
                    ROWS BETWEEN {adv_rows} PRECEDING AND CURRENT ROW
                ) AS adv_usd,
                LAG(pb.raw_close) OVER (PARTITION BY pb.permno ORDER BY pb.date) AS prev_raw_close
            FROM price_base AS pb
        )
        SELECT
            priced.date,
            priced.permno,
            CAST(f.ticker AS VARCHAR) AS ticker,
            CAST(f.capital_cycle_score AS DOUBLE) AS capital_cycle_score,
            CAST(p.quality_pass AS INTEGER) AS quality_pass,
            priced.adv_usd,
            priced.total_ret - ((priced.raw_close / NULLIF(priced.prev_raw_close, 0)) - 1.0) AS corp_action_yield
        FROM priced
        LEFT JOIN read_parquet('{_sql_escape_path(cfg.panel_path)}') AS p
          ON CAST(p.date AS DATE) = priced.date
         AND CAST(p.permno AS BIGINT) = priced.permno
        LEFT JOIN read_parquet('{_sql_escape_path(cfg.features_path)}') AS f
          ON CAST(f.date AS DATE) = priced.date
         AND CAST(f.permno AS BIGINT) = priced.permno
        WHERE priced.prev_raw_close IS NOT NULL
        ORDER BY priced.date, priced.permno
        """
        frame = con.execute(query).df()
    finally:
        con.close()

    if frame.empty:
        return frame

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["permno"] = pd.to_numeric(frame["permno"], errors="coerce").astype("Int64")
    frame["ticker"] = frame["ticker"].astype(str).str.upper().str.strip()
    frame["capital_cycle_score"] = pd.to_numeric(frame["capital_cycle_score"], errors="coerce")
    frame["quality_pass"] = pd.to_numeric(frame["quality_pass"], errors="coerce").fillna(0).astype(int)
    frame["adv_usd"] = pd.to_numeric(frame["adv_usd"], errors="coerce")
    frame["corp_action_yield"] = pd.to_numeric(frame["corp_action_yield"], errors="coerce")
    frame = frame.dropna(subset=["date", "permno", "corp_action_yield"]).copy()
    frame["permno"] = frame["permno"].astype(int)
    return frame.reset_index(drop=True)


def select_corporate_action_candidates(
    frame: pd.DataFrame,
    cfg: CorporateActionsConfig,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    work = frame.copy()
    gate_mask = (
        work["adv_usd"].ge(float(cfg.adv_usd_min))
        & work["quality_pass"].eq(1)
        & work["corp_action_yield"].between(
            float(cfg.event_yield_min),
            float(cfg.event_yield_max),
            inclusive="both",
        )
        & work["capital_cycle_score"].notna()
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
    work["score_valid"] = work["capital_cycle_score"].notna()
    return work.sort_values(["date", "permno"]).reset_index(drop=True)


def build_corporate_action_target_weights(
    selected: pd.DataFrame,
    trading_dates: pd.DatetimeIndex,
) -> pd.DataFrame:
    if selected.empty:
        return pd.DataFrame(index=trading_dates)

    work = selected.loc[
        pd.to_numeric(selected["score_valid"], errors="coerce").fillna(False).astype(bool),
        ["date", "permno"],
    ].copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work["permno"] = pd.to_numeric(work["permno"], errors="coerce")
    work = work.dropna(subset=["date", "permno"]).sort_values(["date", "permno"])
    if work.empty:
        return pd.DataFrame(index=trading_dates)

    work["target_weight"] = 1.0 / work.groupby("date")["permno"].transform("size")
    target = (
        work.pivot(index="date", columns="permno", values="target_weight")
        .sort_index()
        .fillna(0.0)
    )
    target = target.reindex(trading_dates, fill_value=0.0)
    target.columns = pd.Index(pd.to_numeric(target.columns, errors="coerce").astype(int))
    target.index.name = "date"
    return target


def load_baseline_summary(cfg: CorporateActionsConfig) -> dict[str, Any]:
    if not cfg.baseline_summary_path.exists():
        raise FileNotFoundError(f"Missing required baseline summary: {cfg.baseline_summary_path}")

    with open(cfg.baseline_summary_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    try:
        window = payload["window"]
        baseline_start = pd.Timestamp(window["start_date"])
        baseline_end = pd.Timestamp(window["end_date"])
        baseline_cost_bps = float(payload["cost_bps"])
        baseline_config_id = str(payload["baseline_config_id"])
        baseline_metrics = payload["metrics"]["c3"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"Baseline summary missing required Phase 54 C3 fields: {cfg.baseline_summary_path}"
        ) from exc

    if baseline_start != cfg.start_date or baseline_end != cfg.end_date:
        raise ValueError(
            "Baseline window mismatch: "
            f"expected {cfg.start_date.date()} -> {cfg.end_date.date()}, "
            f"got {baseline_start.date()} -> {baseline_end.date()}"
        )
    if abs(baseline_cost_bps - float(cfg.cost_bps)) > 1e-9:
        raise ValueError(
            f"Baseline cost_bps mismatch: expected {cfg.cost_bps}, got {baseline_cost_bps}"
        )

    return {
        "baseline_config_id": baseline_config_id,
        "baseline_cost_bps": baseline_cost_bps,
        "baseline_metrics_c3": {
            "sharpe": float(baseline_metrics["sharpe"]),
            "cagr": float(baseline_metrics["cagr"]),
            "max_dd": float(baseline_metrics["max_dd"]),
            "ulcer": float(baseline_metrics["ulcer"]),
            "turnover_annual": float(baseline_metrics["turnover_annual"]),
            "turnover_total": float(baseline_metrics["turnover_total"]),
        },
    }


def summarize_simulation(
    *,
    sim: pd.DataFrame,
    weights: pd.DataFrame,
    selected: pd.DataFrame,
    cfg: CorporateActionsConfig,
    baseline: dict[str, Any],
) -> dict[str, Any]:
    out = sim.copy()
    out["equity"] = (1.0 + pd.to_numeric(out["net_ret"], errors="coerce").fillna(0.0)).cumprod()
    n_positions = weights.gt(0.0).sum(axis=1).astype(int)
    active_days = int(n_positions.gt(0).sum())
    active_positions = n_positions.loc[n_positions.gt(0)]

    return {
        "strategy_id": "PHASE57_CORP_ACTIONS_CASH_YIELD_V1",
        "start_date": cfg.start_date.strftime("%Y-%m-%d"),
        "end_date": cfg.end_date.strftime("%Y-%m-%d"),
        "max_date": cfg.max_date.strftime("%Y-%m-%d"),
        "cost_bps": float(cfg.cost_bps),
        "adv_window_days": int(cfg.adv_window_days),
        "adv_usd_min": float(cfg.adv_usd_min),
        "event_yield_min": float(cfg.event_yield_min),
        "event_yield_max": float(cfg.event_yield_max),
        "value_rank_threshold": float(cfg.value_rank_threshold),
        "same_engine": True,
        "same_window_same_cost_same_engine": True,
        "baseline_config_id": baseline["baseline_config_id"],
        "rows": int(len(out)),
        "candidate_rows": int(len(selected)),
        "candidate_permnos": int(selected["permno"].nunique()) if not selected.empty else 0,
        "candidate_dates": int(selected["date"].nunique()) if not selected.empty else 0,
        "active_days": active_days,
        "active_day_share": float(active_days / len(weights)) if len(weights) else 0.0,
        "avg_positions": float(n_positions.mean()) if len(n_positions) else 0.0,
        "avg_positions_active_days": float(active_positions.mean()) if len(active_positions) else 0.0,
        "max_positions": int(n_positions.max()) if len(n_positions) else 0,
        "mean_event_yield": float(selected["corp_action_yield"].mean()) if not selected.empty else 0.0,
        "max_event_yield": float(selected["corp_action_yield"].max()) if not selected.empty else 0.0,
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


def build_delta_frame(summary: dict[str, Any], baseline: dict[str, Any]) -> pd.DataFrame:
    c3 = baseline["baseline_metrics_c3"]
    turnover_annual_c3 = float(c3["turnover_annual"])
    turnover_annual_phase57 = float(summary["turnover_annual"])
    turnover_ratio = (
        turnover_annual_phase57 / turnover_annual_c3 if abs(turnover_annual_c3) > 1e-12 else 0.0
    )
    row = {
        "window_start": summary["start_date"],
        "window_end": summary["end_date"],
        "cost_bps": float(summary["cost_bps"]),
        "baseline_config_id": baseline["baseline_config_id"],
        "strategy_id": summary["strategy_id"],
        "same_window_same_cost_same_engine": True,
        "candidate_rows": int(summary["candidate_rows"]),
        "candidate_permnos": int(summary["candidate_permnos"]),
        "candidate_dates": int(summary["candidate_dates"]),
        "active_days": int(summary["active_days"]),
        "active_day_share": float(summary["active_day_share"]),
        "sharpe_c3": float(c3["sharpe"]),
        "sharpe_phase57": float(summary["sharpe"]),
        "sharpe_delta": float(summary["sharpe"] - c3["sharpe"]),
        "cagr_c3": float(c3["cagr"]),
        "cagr_phase57": float(summary["cagr"]),
        "cagr_delta": float(summary["cagr"] - c3["cagr"]),
        "turnover_annual_c3": turnover_annual_c3,
        "turnover_annual_phase57": turnover_annual_phase57,
        "turnover_ratio_phase57_vs_c3": float(turnover_ratio),
        "max_dd_c3": float(c3["max_dd"]),
        "max_dd_phase57": float(summary["max_dd"]),
        "max_dd_delta": float(summary["max_dd"] - c3["max_dd"]),
        "ulcer_c3": float(c3["ulcer"]),
        "ulcer_phase57": float(summary["ulcer"]),
        "ulcer_delta": float(summary["ulcer"] - c3["ulcer"]),
        "net_return_total_phase57": float(summary["net_return_total"]),
    }
    return pd.DataFrame([row])


def build_evidence_frame(
    sim: pd.DataFrame,
    weights: pd.DataFrame,
    selected: pd.DataFrame,
) -> pd.DataFrame:
    evidence = sim.copy().rename_axis("date").reset_index()
    evidence["date"] = pd.to_datetime(evidence["date"], errors="coerce")
    evidence["equity"] = (1.0 + pd.to_numeric(evidence["net_ret"], errors="coerce").fillna(0.0)).cumprod()
    n_positions = weights.gt(0.0).sum(axis=1).astype(int)
    gross_exposure = weights.abs().sum(axis=1)
    evidence["n_positions"] = n_positions.reindex(weights.index).astype(int).values
    evidence["gross_exposure"] = gross_exposure.reindex(weights.index).astype(float).values

    event_stats = (
        selected.groupby("date", as_index=True)
        .agg(
            event_count=("permno", "nunique"),
            mean_event_yield=("corp_action_yield", "mean"),
            max_event_yield=("corp_action_yield", "max"),
        )
        .reindex(weights.index)
        .fillna(0.0)
    )
    evidence["event_count"] = event_stats["event_count"].astype(int).values
    evidence["mean_event_yield"] = event_stats["mean_event_yield"].astype(float).values
    evidence["max_event_yield"] = event_stats["max_event_yield"].astype(float).values
    return evidence


def run_corporate_actions(cfg: CorporateActionsConfig) -> dict[str, Any]:
    validate_config(cfg)

    trading_dates = load_trading_dates(cfg)
    action_frame = load_corporate_action_frame(cfg)
    selected = select_corporate_action_candidates(action_frame, cfg)
    if selected.empty:
        raise RuntimeError("No Corporate Actions candidates passed the bounded Phase 57 gates.")

    weights = build_corporate_action_target_weights(selected, trading_dates)
    permnos = sorted(int(c) for c in weights.columns)
    returns_long = _load_returns_subset(
        prices_path=cfg.prices_path,
        permnos=permnos,
        start_date=cfg.start_date,
        end_date=cfg.end_date,
    )
    if returns_long.empty:
        raise RuntimeError("No return rows found for the bounded Phase 57 window.")

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

    baseline = load_baseline_summary(cfg)
    summary = summarize_simulation(
        sim=sim,
        weights=weights,
        selected=selected,
        cfg=cfg,
        baseline=baseline,
    )
    summary["summary_path"] = str(cfg.summary_path)
    summary["evidence_path"] = str(cfg.evidence_path)
    summary["delta_path"] = str(cfg.delta_path)
    summary["baseline_summary_path"] = str(cfg.baseline_summary_path)
    summary["baseline_metrics_c3"] = baseline["baseline_metrics_c3"]
    summary["source_paths"] = {
        "features_path": str(cfg.features_path),
        "panel_path": str(cfg.panel_path),
        "prices_path": str(cfg.prices_path),
        "baseline_summary_path": str(cfg.baseline_summary_path),
        "tri_builder_path": str(PROJECT_ROOT / "data" / "build_tri.py"),
        "engine_path": str(PROJECT_ROOT / "core" / "engine.py"),
    }

    delta = build_delta_frame(summary, baseline)
    evidence = build_evidence_frame(sim=sim, weights=weights, selected=selected)

    cfg.summary_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_write(summary, cfg.summary_path)
    _atomic_csv_write(evidence, cfg.evidence_path)
    _atomic_csv_write(delta, cfg.delta_path)
    return summary


def parse_args() -> CorporateActionsConfig:
    parser = argparse.ArgumentParser(description="Phase 57 bounded Corporate Actions runner.")
    parser.add_argument("--start-date", default="2015-01-01")
    parser.add_argument("--end-date", default="2022-12-31")
    parser.add_argument("--max-date", default="2022-12-31")
    parser.add_argument("--cost-bps", type=float, default=5.0)
    parser.add_argument("--adv-window-days", type=int, default=20)
    parser.add_argument("--adv-usd-min", type=float, default=5_000_000.0)
    parser.add_argument("--event-yield-min", type=float, default=0.005)
    parser.add_argument("--event-yield-max", type=float, default=0.25)
    parser.add_argument("--value-rank-threshold", type=float, default=0.60)
    parser.add_argument("--summary-path", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--evidence-path", default=str(DEFAULT_EVIDENCE_PATH))
    parser.add_argument("--delta-path", default=str(DEFAULT_DELTA_PATH))
    parser.add_argument("--baseline-summary-path", default=str(DEFAULT_BASELINE_SUMMARY_PATH))
    parser.add_argument("--features-path", default=str(DEFAULT_FEATURES_PATH))
    parser.add_argument("--panel-path", default=str(DEFAULT_PANEL_PATH))
    parser.add_argument("--prices-path", default=str(DEFAULT_PRICES_PATH))
    args = parser.parse_args()

    return CorporateActionsConfig(
        start_date=pd.Timestamp(args.start_date),
        end_date=pd.Timestamp(args.end_date),
        max_date=pd.Timestamp(args.max_date),
        cost_bps=float(args.cost_bps),
        adv_window_days=int(args.adv_window_days),
        adv_usd_min=float(args.adv_usd_min),
        event_yield_min=float(args.event_yield_min),
        event_yield_max=float(args.event_yield_max),
        value_rank_threshold=float(args.value_rank_threshold),
        summary_path=Path(args.summary_path),
        evidence_path=Path(args.evidence_path),
        delta_path=Path(args.delta_path),
        baseline_summary_path=Path(args.baseline_summary_path),
        features_path=Path(args.features_path),
        panel_path=Path(args.panel_path),
        prices_path=Path(args.prices_path),
    )


def main() -> None:
    cfg = parse_args()
    summary = run_corporate_actions(cfg)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
