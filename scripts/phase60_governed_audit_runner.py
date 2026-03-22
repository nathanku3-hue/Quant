from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from core.engine import run_simulation  # noqa: E402
from scripts.day5_ablation_report import _atomic_csv_write  # noqa: E402
from scripts.day5_ablation_report import _atomic_json_write  # noqa: E402
from scripts.day5_ablation_report import _load_returns_subset  # noqa: E402
from scripts.phase56_pead_runner import PeadConfig  # noqa: E402
from scripts.phase56_pead_runner import build_pead_target_weights  # noqa: E402
from scripts.phase56_pead_runner import load_pead_feature_frame  # noqa: E402
from scripts.phase56_pead_runner import select_pead_candidates  # noqa: E402
from scripts.phase57_corporate_actions_runner import CorporateActionsConfig  # noqa: E402
from scripts.phase57_corporate_actions_runner import build_corporate_action_target_weights  # noqa: E402
from scripts.phase57_corporate_actions_runner import load_corporate_action_frame  # noqa: E402
from scripts.phase57_corporate_actions_runner import load_trading_dates  # noqa: E402
from scripts.phase57_corporate_actions_runner import select_corporate_action_candidates  # noqa: E402
from scripts.phase20_full_backtest import DEFAULT_FEATURES_PATH as C3_FEATURES_PATH  # noqa: E402
from scripts.phase20_full_backtest import DEFAULT_SDM_FEATURES_PATH as C3_SDM_FEATURES_PATH  # noqa: E402
from scripts.phase20_full_backtest import PRODUCTION_CONFIG_V1  # noqa: E402
from scripts.phase20_full_backtest import _load_features_window as _load_c3_features_window  # noqa: E402
from utils.metrics import compute_cagr  # noqa: E402
from utils.metrics import compute_max_drawdown  # noqa: E402
from utils.metrics import compute_ulcer_index  # noqa: E402
from utils.spa import spa_wrc_pvalues  # noqa: E402
from utils.statistics import safe_sharpe  # noqa: E402
from scripts.day5_ablation_report import _build_target_weights  # noqa: E402
from strategies.company_scorecard import CompanyScorecard  # noqa: E402


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_SUMMARY_PATH = PROCESSED_DIR / "phase60_governed_audit_summary.json"
DEFAULT_EVIDENCE_PATH = PROCESSED_DIR / "phase60_governed_audit_evidence.csv"
DEFAULT_DELTA_PATH = PROCESSED_DIR / "phase60_governed_audit_delta.csv"
DEFAULT_SIDECAR_PATH = PROCESSED_DIR / "sidecar_sp500_pro_2023_2024.parquet"
DEFAULT_PREFLIGHT_PATH = (
    PROJECT_ROOT / "docs" / "context" / "e2e_evidence" / "phase60_d340_preflight_20260319_summary.json"
)
DEFAULT_PHASE54_SUMMARY_PATH = PROCESSED_DIR / "phase54_core_sleeve_summary.json"
DEFAULT_PHASE55_SUMMARY_PATH = PROCESSED_DIR / "phase55_allocator_cpcv_summary.json"
DEFAULT_PHASE60_CUBE_SUMMARY_PATH = PROCESSED_DIR / "phase60_governed_cube_summary.json"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_APPROVED_END_DATE = pd.Timestamp("2024-12-31")
BOOK_ID = "PHASE60_GOVERNED_BOOK_V1"


@dataclass(frozen=True)
class AuditConfig:
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    cost_bps: float
    sensitivity_bps: float
    summary_path: Path = DEFAULT_SUMMARY_PATH
    evidence_path: Path = DEFAULT_EVIDENCE_PATH
    delta_path: Path = DEFAULT_DELTA_PATH
    preflight_path: Path = DEFAULT_PREFLIGHT_PATH
    phase54_summary_path: Path = DEFAULT_PHASE54_SUMMARY_PATH
    phase55_summary_path: Path = DEFAULT_PHASE55_SUMMARY_PATH
    cube_summary_path: Path = DEFAULT_PHASE60_CUBE_SUMMARY_PATH
    prices_path: Path = DEFAULT_PRICES_PATH
    sidecar_path: Path = DEFAULT_SIDECAR_PATH


def validate_config(cfg: AuditConfig) -> None:
    if cfg.start_date < pd.Timestamp("2023-01-01"):
        raise ValueError("Audit start_date must be >= 2023-01-01")
    if cfg.end_date > DEFAULT_APPROVED_END_DATE:
        raise ValueError(f"Audit end_date must be <= {DEFAULT_APPROVED_END_DATE.date()}")
    if cfg.start_date > cfg.end_date:
        raise ValueError("start_date must be <= end_date")
    if abs(float(cfg.cost_bps) - 5.0) > 1e-9:
        raise ValueError("Governed audit gate is locked to 5.0 bps")
    if abs(float(cfg.sensitivity_bps) - 10.0) > 1e-9:
        raise ValueError("Sensitivity lane is locked to 10.0 bps")


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_sidecar_returns(
    sidecar_path: Path,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    if not sidecar_path.exists():
        return pd.DataFrame(columns=["date", "permno", "ret"])

    sidecar = pd.read_parquet(sidecar_path)
    required = {"date", "permno", "total_return"}
    missing = required - set(sidecar.columns)
    if missing:
        raise ValueError(f"Sidecar parquet missing required columns: {sorted(missing)}")

    out = sidecar.loc[:, ["date", "permno", "total_return"]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["permno"] = pd.to_numeric(out["permno"], errors="coerce")
    out["ret"] = pd.to_numeric(out["total_return"], errors="coerce")
    out = out.drop(columns=["total_return"])
    out = out.dropna(subset=["date", "permno"])
    out["permno"] = out["permno"].astype(int)
    out = out[(out["date"] >= start_date) & (out["date"] <= end_date)].copy()
    if out.empty:
        return out.reset_index(drop=True)
    if out.duplicated(subset=["date", "permno"]).any():
        duplicates = out.loc[out.duplicated(subset=["date", "permno"], keep=False), ["date", "permno"]]
        raise RuntimeError(
            "Sidecar parquet contains duplicate date/permno rows: "
            f"{duplicates.sort_values(['date', 'permno']).head(10).to_dict(orient='records')}"
        )
    return out.sort_values(["date", "permno"]).reset_index(drop=True)


def _merge_returns_long(base_returns: pd.DataFrame, sidecar_returns: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    base = base_returns.copy()
    base["date"] = pd.to_datetime(base["date"], errors="coerce")
    base["permno"] = pd.to_numeric(base["permno"], errors="coerce")
    base["ret"] = pd.to_numeric(base["ret"], errors="coerce")
    base = base.dropna(subset=["date", "permno"]).copy()
    base["permno"] = base["permno"].astype(int)
    base["source"] = "base"

    sidecar = sidecar_returns.copy()
    if sidecar.empty:
        merged = base.drop(columns=["source"]).sort_values(["date", "permno"]).reset_index(drop=True)
        return merged, {
            "sidecar_present": False,
            "sidecar_rows_total": 0,
            "sidecar_rows_used": 0,
            "sidecar_override_rows": 0,
            "sidecar_permnos": [],
        }

    sidecar["date"] = pd.to_datetime(sidecar["date"], errors="coerce")
    sidecar["permno"] = pd.to_numeric(sidecar["permno"], errors="coerce")
    sidecar["ret"] = pd.to_numeric(sidecar["ret"], errors="coerce")
    sidecar = sidecar.dropna(subset=["date", "permno"]).copy()
    sidecar["permno"] = sidecar["permno"].astype(int)
    sidecar["source"] = "sidecar"

    overlap = base.merge(sidecar[["date", "permno"]], on=["date", "permno"], how="inner")
    merged = (
        pd.concat([base, sidecar], ignore_index=True)
        .sort_values(["date", "permno", "source"])
        .drop_duplicates(subset=["date", "permno"], keep="last")
        .drop(columns=["source"])
        .sort_values(["date", "permno"])
        .reset_index(drop=True)
    )
    return merged, {
        "sidecar_present": True,
        "sidecar_rows_total": int(len(sidecar)),
        "sidecar_rows_used": int(len(sidecar)),
        "sidecar_override_rows": int(len(overlap)),
        "sidecar_permnos": sorted(sidecar["permno"].unique().tolist()),
    }


def _apply_sidecar_feature_mask(features: pd.DataFrame, sidecar_returns: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    if features.empty or sidecar_returns.empty:
        return features, {"feature_rows_dropped": 0, "feature_mask_permnos": []}

    coverage = (
        sidecar_returns.dropna(subset=["ret"])
        .groupby("permno", sort=True)["date"]
        .max()
        .rename("last_return_date")
        .reset_index()
    )
    if coverage.empty:
        return features, {"feature_rows_dropped": 0, "feature_mask_permnos": []}

    masked = features.copy()
    masked["date"] = pd.to_datetime(masked["date"], errors="coerce")
    masked["permno"] = pd.to_numeric(masked["permno"], errors="coerce")
    masked = masked.merge(coverage, on="permno", how="left")
    keep_mask = masked["last_return_date"].isna() | (masked["date"] < masked["last_return_date"])
    dropped = masked.loc[~keep_mask, ["date", "permno"]].copy()
    masked = masked.loc[keep_mask].drop(columns=["last_return_date"]).reset_index(drop=True)
    return masked, {
        "feature_rows_dropped": int(len(dropped)),
        "feature_mask_permnos": sorted(coverage["permno"].astype(int).unique().tolist()),
        "feature_mask_date_min": str(dropped["date"].min().date()) if not dropped.empty else None,
        "feature_mask_date_max": str(dropped["date"].max().date()) if not dropped.empty else None,
    }


def _run_phase20_comparator(
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    cost_bps: float,
    sidecar_path: Path,
) -> dict[str, Any]:
    extra_cols = [
        "ticker",
        "adj_close",
        "dist_sma20",
        "sma200",
        "resid_mom_60d",
        "z_inventory_quality_proxy",
        "capital_cycle_score",
        "amihud_20d",
    ]
    features = _load_c3_features_window(
        C3_FEATURES_PATH,
        start_date,
        end_date,
        extra_columns=extra_cols,
        sdm_features_path=C3_SDM_FEATURES_PATH,
    )
    sidecar_returns = _load_sidecar_returns(sidecar_path, start_date, end_date)
    features, feature_mask_info = _apply_sidecar_feature_mask(features, sidecar_returns)
    if features.empty:
        raise RuntimeError("KS-03: same-period C3 comparator has no feature rows in the audit window")

    scorecard = CompanyScorecard(
        factor_specs=list(PRODUCTION_CONFIG_V1.factor_specs),
        scoring_method=PRODUCTION_CONFIG_V1.scoring_method,
    )
    scores, _ = scorecard.compute_scores(features)
    feature_dates = pd.DatetimeIndex(sorted(features["date"].dropna().unique()))
    baseline_weights = _build_target_weights(
        scores=scores,
        top_quantile=float(PRODUCTION_CONFIG_V1.top_quantile),
    ).reindex(feature_dates).fillna(0.0)

    permnos = sorted(pd.to_numeric(features["permno"], errors="coerce").dropna().astype(int).unique().tolist())
    prices_path = DEFAULT_PRICES_PATH
    if (PROJECT_ROOT / "data" / "processed" / "prices_tri.parquet").exists():
        prices_path = PROJECT_ROOT / "data" / "processed" / "prices_tri.parquet"
    returns, sidecar_info = _load_returns(prices_path, permnos, start_date, end_date, sidecar_path=sidecar_path)
    sim = _simulate(baseline_weights, returns, cost_bps)
    return {
        "baseline_config_id": PRODUCTION_CONFIG_V1.config_id,
        "metrics": {"c3": _metrics(sim)},
        "sidecar_info": sidecar_info,
        "feature_mask_info": feature_mask_info,
    }


def _phase56_weights(start_date: pd.Timestamp, end_date: pd.Timestamp, cost_bps: float) -> pd.DataFrame:
    cfg = PeadConfig(
        start_date=start_date,
        end_date=end_date,
        max_date=end_date,
        cost_bps=cost_bps,
        adv_window_days=20,
        adv_usd_min=5_000_000.0,
        max_days_since_earnings=63,
        value_rank_threshold=0.60,
        summary_path=PROCESSED_DIR / "_phase60_audit_phase56_summary.json",
        evidence_path=PROCESSED_DIR / "_phase60_audit_phase56_evidence.csv",
    )
    return build_pead_target_weights(select_pead_candidates(load_pead_feature_frame(cfg), cfg))


def _phase57_weights(start_date: pd.Timestamp, end_date: pd.Timestamp, cost_bps: float) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    cfg = CorporateActionsConfig(
        start_date=start_date,
        end_date=end_date,
        max_date=end_date,
        cost_bps=cost_bps,
        adv_window_days=20,
        adv_usd_min=5_000_000.0,
        event_yield_min=0.005,
        event_yield_max=0.25,
        value_rank_threshold=0.60,
        summary_path=PROCESSED_DIR / "_phase60_audit_phase57_summary.json",
        evidence_path=PROCESSED_DIR / "_phase60_audit_phase57_evidence.csv",
        delta_path=PROCESSED_DIR / "_phase60_audit_phase57_delta.csv",
        baseline_summary_path=DEFAULT_PHASE54_SUMMARY_PATH,
    )
    calendar = load_trading_dates(cfg)
    weights = build_corporate_action_target_weights(
        select_corporate_action_candidates(load_corporate_action_frame(cfg), cfg),
        calendar,
    )
    return weights, calendar


def _normalize(weights: pd.DataFrame, calendar: pd.DatetimeIndex, permnos: list[int]) -> pd.DataFrame:
    if weights.empty:
        out = pd.DataFrame(0.0, index=calendar, columns=permnos)
    else:
        out = weights.reindex(index=calendar, columns=permnos, fill_value=0.0).fillna(0.0).astype(float)
    out.index.name = "date"
    out.columns.name = "permno"
    return out


def _load_returns(
    prices_path: Path,
    permnos: list[int],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    sidecar_path: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    base_returns = _load_returns_subset(
        prices_path=prices_path,
        permnos=permnos,
        start_date=start_date,
        end_date=end_date,
    )
    sidecar_returns = (
        _load_sidecar_returns(sidecar_path, start_date, end_date)
        if sidecar_path is not None
        else pd.DataFrame(columns=["date", "permno", "ret"])
    )
    returns_long, sidecar_info = _merge_returns_long(base_returns, sidecar_returns)
    returns = (
        returns_long.assign(
            date=pd.to_datetime(returns_long["date"], errors="coerce"),
            permno=pd.to_numeric(returns_long["permno"], errors="coerce"),
            ret=pd.to_numeric(returns_long["ret"], errors="coerce"),
        )
        .dropna(subset=["date", "permno"])
        .pivot(index="date", columns="permno", values="ret")
        .sort_index()
    )
    returns.columns = pd.Index(pd.to_numeric(returns.columns, errors="coerce").astype(int), name="permno")
    returns.index.name = "date"
    return returns, sidecar_info


def _simulate(weights: pd.DataFrame, returns: pd.DataFrame, cost_bps: float) -> pd.DataFrame:
    sim = run_simulation(
        target_weights=weights,
        returns_df=returns.reindex(index=weights.index, columns=weights.columns),
        cost_bps=float(cost_bps) / 10000.0,
        strict_missing_returns=True,
    )
    sim.index = pd.to_datetime(sim.index, errors="coerce")
    return sim


def _enforce_kill_switches(*, preflight: dict[str, Any], cube_summary: dict[str, Any], weights: pd.DataFrame, allocator_overlay_applied: bool, core_included: bool) -> None:
    if not preflight.get("passed", False):
        raise RuntimeError("KS-03: preflight did not pass; audit cannot start")
    if not cube_summary.get("phase50_reference_only_excluded", False):
        raise RuntimeError("KS-01: phase50 reference fill detected in governed path")
    if allocator_overlay_applied:
        raise RuntimeError("KS-05: allocator overlay was applied despite governance block")
    if core_included:
        raise RuntimeError("KS-05: core sleeve was included despite governance block")
    if weights.empty or weights.abs().sum().sum() <= 0.0:
        raise RuntimeError("KS-04: unified cube weights are empty")


def _metrics(sim: pd.DataFrame) -> dict[str, float]:
    equity = (1.0 + pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)).cumprod()
    return {
        "sharpe": float(safe_sharpe(sim["net_ret"])),
        "cagr": float(compute_cagr(equity)),
        "max_dd": float(compute_max_drawdown(equity)),
        "ulcer": float(compute_ulcer_index(equity)),
        "turnover_annual": float(pd.to_numeric(sim["turnover"], errors="coerce").mean() * 252.0),
        "turnover_total": float(pd.to_numeric(sim["turnover"], errors="coerce").sum()),
        "net_return_total": float(equity.iloc[-1] - 1.0),
    }


def _build_daily_evidence(weights: pd.DataFrame, sim_5: pd.DataFrame, sim_10: pd.DataFrame) -> pd.DataFrame:
    gross_exposure = weights.abs().sum(axis=1)
    turnover = weights.diff().abs()
    if not turnover.empty:
        turnover.iloc[0] = weights.iloc[0].abs()
    evidence = pd.DataFrame(
        {
            "date": weights.index,
            "book_id": BOOK_ID,
            "gross_exposure": gross_exposure.values,
            "turnover_total": turnover.sum(axis=1).values,
            "n_active_permnos": (weights.abs() > 0.0).sum(axis=1).astype(int).values,
            "net_ret_5bps": pd.to_numeric(sim_5["net_ret"], errors="coerce").values,
            "net_ret_10bps": pd.to_numeric(sim_10["net_ret"], errors="coerce").values,
        }
    )
    return evidence


def run_governed_audit(cfg: AuditConfig) -> dict[str, Any]:
    validate_config(cfg)
    preflight = _load_json(cfg.preflight_path)
    cube_summary = _load_json(cfg.cube_summary_path)
    phase55_summary = _load_json(cfg.phase55_summary_path)

    phase56_weights = _phase56_weights(cfg.start_date, cfg.end_date, cfg.cost_bps)
    phase57_weights, calendar = _phase57_weights(cfg.start_date, cfg.end_date, cfg.cost_bps)
    permnos = sorted(set(map(int, phase56_weights.columns.tolist() + phase57_weights.columns.tolist())))
    pead = _normalize(phase56_weights, calendar, permnos)
    corp = _normalize(phase57_weights, calendar, permnos)
    weights = pead.add(corp, fill_value=0.0)
    _enforce_kill_switches(
        preflight=preflight,
        cube_summary=cube_summary,
        weights=weights,
        allocator_overlay_applied=False,
        core_included=False,
    )

    returns, governed_sidecar_info = _load_returns(
        cfg.prices_path,
        permnos,
        cfg.start_date,
        cfg.end_date,
        sidecar_path=cfg.sidecar_path,
    )
    sim_book_5 = _simulate(weights, returns, cfg.cost_bps)
    sim_book_10 = _simulate(weights, returns, cfg.sensitivity_bps)
    sim_pead_5 = _simulate(pead, returns, cfg.cost_bps)
    sim_corp_5 = _simulate(corp, returns, cfg.cost_bps)

    kill_switches_triggered: list[str] = []
    comparator_error: str | None = None
    c3_5: dict[str, Any] | None = None
    c3_10: dict[str, Any] | None = None
    try:
        c3_5 = _run_phase20_comparator(cfg.start_date, cfg.end_date, cfg.cost_bps, cfg.sidecar_path)
        c3_10 = _run_phase20_comparator(cfg.start_date, cfg.end_date, cfg.sensitivity_bps, cfg.sidecar_path)
    except RuntimeError as exc:
        comparator_error = str(exc)
        kill_switches_triggered.append("KS-03_same_period_c3_unavailable")

    family_matrix = pd.DataFrame(
        {
            "phase56_event_pead": pd.to_numeric(sim_pead_5["net_ret"], errors="coerce").fillna(0.0).values,
            "phase57_event_corporate_actions": pd.to_numeric(sim_corp_5["net_ret"], errors="coerce").fillna(0.0).values,
        },
        index=calendar,
    )
    family_tests = spa_wrc_pvalues(family_matrix)
    book_metrics_5 = _metrics(sim_book_5)
    book_metrics_10 = _metrics(sim_book_10)
    pead_metrics_5 = _metrics(sim_pead_5)

    overlap_counts = ((pead.abs() > 0.0) & (corp.abs() > 0.0)).sum(axis=1)
    overlap_ratio = overlap_counts / np.maximum((weights.abs() > 0.0).sum(axis=1), 1)

    gate_results = {
        "GATE-01_event_family_significance": bool(
            float(family_tests["spa_p"]) < 0.05 and float(family_tests["wrc_p"]) < 0.05
        ),
        "GATE-02_pead_vs_c3_same_period": bool(
            c3_5 is not None
            and pead_metrics_5["sharpe"] >= float(c3_5["metrics"]["c3"]["sharpe"])
            and pead_metrics_5["cagr"] >= float(c3_5["metrics"]["c3"]["cagr"])
        ),
        "GATE-03_core_sleeve_block_enforced": True,
        "GATE-04_allocator_block_enforced": bool(
            not phase55_summary.get("allocator_gate_pass", False)
            and not cube_summary.get("allocator_overlay_applied", True)
        ),
        "GATE-05_nonempty_governed_overlap_exposure_turnover": bool(
            overlap_ratio.notna().any()
            and weights.abs().sum().sum() > 0.0
            and weights.diff().abs().sum().sum() > 0.0
        ),
    }

    daily_evidence = _build_daily_evidence(weights, sim_book_5, sim_book_10)
    delta = pd.DataFrame(
        [
            {
                "lane": "5bps_gate",
                "window_start": cfg.start_date.strftime("%Y-%m-%d"),
                "window_end": cfg.end_date.strftime("%Y-%m-%d"),
                "cost_bps": float(cfg.cost_bps),
                "baseline_config_id": str(c3_5["baseline_config_id"]) if c3_5 is not None else "",
                "book_sharpe": book_metrics_5["sharpe"],
                "c3_sharpe": float(c3_5["metrics"]["c3"]["sharpe"]) if c3_5 is not None else float("nan"),
                "book_sharpe_delta": book_metrics_5["sharpe"] - float(c3_5["metrics"]["c3"]["sharpe"]) if c3_5 is not None else float("nan"),
                "book_cagr": book_metrics_5["cagr"],
                "c3_cagr": float(c3_5["metrics"]["c3"]["cagr"]) if c3_5 is not None else float("nan"),
                "book_cagr_delta": book_metrics_5["cagr"] - float(c3_5["metrics"]["c3"]["cagr"]) if c3_5 is not None else float("nan"),
                "book_turnover_annual": book_metrics_5["turnover_annual"],
                "c3_turnover_annual": float(c3_5["metrics"]["c3"]["turnover_annual"]) if c3_5 is not None else float("nan"),
                "family_spa_p": float(family_tests["spa_p"]),
                "family_wrc_p": float(family_tests["wrc_p"]),
                "comparator_available": c3_5 is not None,
            },
            {
                "lane": "10bps_sensitivity",
                "window_start": cfg.start_date.strftime("%Y-%m-%d"),
                "window_end": cfg.end_date.strftime("%Y-%m-%d"),
                "cost_bps": float(cfg.sensitivity_bps),
                "baseline_config_id": str(c3_10["baseline_config_id"]) if c3_10 is not None else "",
                "book_sharpe": book_metrics_10["sharpe"],
                "c3_sharpe": float(c3_10["metrics"]["c3"]["sharpe"]) if c3_10 is not None else float("nan"),
                "book_sharpe_delta": book_metrics_10["sharpe"] - float(c3_10["metrics"]["c3"]["sharpe"]) if c3_10 is not None else float("nan"),
                "book_cagr": book_metrics_10["cagr"],
                "c3_cagr": float(c3_10["metrics"]["c3"]["cagr"]) if c3_10 is not None else float("nan"),
                "book_cagr_delta": book_metrics_10["cagr"] - float(c3_10["metrics"]["c3"]["cagr"]) if c3_10 is not None else float("nan"),
                "book_turnover_annual": book_metrics_10["turnover_annual"],
                "c3_turnover_annual": float(c3_10["metrics"]["c3"]["turnover_annual"]) if c3_10 is not None else float("nan"),
                "family_spa_p": float(family_tests["spa_p"]),
                "family_wrc_p": float(family_tests["wrc_p"]),
                "comparator_available": c3_10 is not None,
            },
        ]
    )

    status = "blocked" if kill_switches_triggered else "ok"
    summary = {
        "packet_id": "PHASE60_GOVERNED_AUDIT_V1",
        "book_id": BOOK_ID,
        "status": status,
        "start_date": cfg.start_date.strftime("%Y-%m-%d"),
        "end_date": cfg.end_date.strftime("%Y-%m-%d"),
        "cost_bps_gate": float(cfg.cost_bps),
        "sensitivity_bps": float(cfg.sensitivity_bps),
        "preflight_passed": bool(preflight.get("passed", False)),
        "allocator_overlay_applied": False,
        "core_sleeve_included": False,
        "allocator_gate_pass": bool(phase55_summary.get("allocator_gate_pass", False)),
        "family_spa_p": float(family_tests["spa_p"]),
        "family_wrc_p": float(family_tests["wrc_p"]),
        "gate_results": gate_results,
        "kill_switches_triggered": kill_switches_triggered,
        "comparator_error": comparator_error,
        "book_metrics_5bps": book_metrics_5,
        "book_metrics_10bps": book_metrics_10,
        "pead_metrics_5bps": pead_metrics_5,
        "same_period_c3_5bps": {
            "baseline_config_id": str(c3_5["baseline_config_id"]) if c3_5 is not None else "",
            "metrics_c3": c3_5["metrics"]["c3"] if c3_5 is not None else {},
            "sidecar_info": c3_5["sidecar_info"] if c3_5 is not None else {},
            "feature_mask_info": c3_5["feature_mask_info"] if c3_5 is not None else {},
        },
        "same_period_c3_10bps": {
            "baseline_config_id": str(c3_10["baseline_config_id"]) if c3_10 is not None else "",
            "metrics_c3": c3_10["metrics"]["c3"] if c3_10 is not None else {},
            "sidecar_info": c3_10["sidecar_info"] if c3_10 is not None else {},
            "feature_mask_info": c3_10["feature_mask_info"] if c3_10 is not None else {},
        },
        "governed_returns_sidecar": {
            "path": str(cfg.sidecar_path),
            **governed_sidecar_info,
        },
        "overlap_ratio_mean": float(overlap_ratio.mean()),
        "gross_exposure_mean": float(daily_evidence["gross_exposure"].mean()),
        "turnover_total": float(daily_evidence["turnover_total"].sum()),
        "summary_path": str(cfg.summary_path),
        "evidence_path": str(cfg.evidence_path),
        "delta_path": str(cfg.delta_path),
    }

    cfg.summary_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_write(summary, cfg.summary_path)
    _atomic_csv_write(daily_evidence, cfg.evidence_path)
    _atomic_csv_write(delta, cfg.delta_path)
    return summary


def parse_args() -> AuditConfig:
    parser = argparse.ArgumentParser(description="Run the bounded Phase 60 post-2022 governed audit.")
    parser.add_argument("--start-date", default="2023-01-01")
    parser.add_argument("--end-date", default=str(DEFAULT_APPROVED_END_DATE.date()))
    parser.add_argument("--cost-bps", type=float, default=5.0)
    parser.add_argument("--sensitivity-bps", type=float, default=10.0)
    parser.add_argument("--summary-path", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--evidence-path", default=str(DEFAULT_EVIDENCE_PATH))
    parser.add_argument("--delta-path", default=str(DEFAULT_DELTA_PATH))
    parser.add_argument("--preflight-path", default=str(DEFAULT_PREFLIGHT_PATH))
    parser.add_argument("--sidecar-path", default=str(DEFAULT_SIDECAR_PATH))
    args = parser.parse_args()
    return AuditConfig(
        start_date=pd.Timestamp(args.start_date),
        end_date=pd.Timestamp(args.end_date),
        cost_bps=float(args.cost_bps),
        sensitivity_bps=float(args.sensitivity_bps),
        summary_path=Path(args.summary_path),
        evidence_path=Path(args.evidence_path),
        delta_path=Path(args.delta_path),
        preflight_path=Path(args.preflight_path),
        sidecar_path=Path(args.sidecar_path),
    )


def main() -> int:
    cfg = parse_args()
    summary = run_governed_audit(cfg)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
