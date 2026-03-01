from __future__ import annotations

import argparse
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from core import engine  # noqa: E402
from scripts.day5_ablation_report import _atomic_csv_write  # noqa: E402
from scripts.day5_ablation_report import _atomic_json_write  # noqa: E402
from scripts.day5_ablation_report import _build_target_weights  # noqa: E402
from scripts.day5_ablation_report import _load_features_subset  # noqa: E402
from scripts.day5_ablation_report import _load_returns_subset  # noqa: E402
from scripts.day5_ablation_report import _resolve_path  # noqa: E402
from scripts.day5_ablation_report import _to_ts  # noqa: E402
from scripts.day6_walkforward_validation import _build_c3_specs  # noqa: E402
from scripts.day6_walkforward_validation import _load_spy_returns  # noqa: E402
from scripts.day6_walkforward_validation import evaluate_checks  # noqa: E402
from scripts.day6_walkforward_validation import run_walk_forward_validation  # noqa: E402
from scripts.day6_walkforward_validation import validate_crisis_turnover  # noqa: E402
from scripts.scorecard_validation import build_validation_table  # noqa: E402
from strategies.company_scorecard import CompanyScorecard  # noqa: E402
from strategies.factor_specs import FactorSpec  # noqa: E402
from strategies.factor_specs import build_phase19_5_candidate_factor_sets  # noqa: E402
from strategies.factor_specs import correlation_audit  # noqa: E402
from strategies.factor_specs import per_regime_audit  # noqa: E402
from strategies.factor_specs import validate_factor_specs  # noqa: E402
from utils.metrics import compute_cagr  # noqa: E402
from utils.metrics import compute_max_drawdown  # noqa: E402
from utils.metrics import compute_sharpe  # noqa: E402
from utils.metrics import compute_ulcer_index  # noqa: E402


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_FEATURES_PATH = PROCESSED_DIR / "features.parquet"
DEFAULT_PRICES_TRI_PATH = PROCESSED_DIR / "prices_tri.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_OUTPUT_ABLATION = PROCESSED_DIR / "phase19_7_ablation_metrics.csv"
DEFAULT_OUTPUT_DELTA = PROCESSED_DIR / "phase19_7_delta_vs_c3.csv"
DEFAULT_OUTPUT_REGIME_AUDIT = PROCESSED_DIR / "phase19_7_regime_audit.csv"
DEFAULT_OUTPUT_WALKFORWARD = PROCESSED_DIR / "phase19_7_walkforward.csv"
DEFAULT_OUTPUT_DECAY = PROCESSED_DIR / "phase19_7_decay_sensitivity.csv"
DEFAULT_OUTPUT_CRISIS = PROCESSED_DIR / "phase19_7_crisis_turnover.csv"
DEFAULT_OUTPUT_CHECKS = PROCESSED_DIR / "phase19_7_checks.csv"
DEFAULT_OUTPUT_SUMMARY = PROCESSED_DIR / "phase19_7_summary.json"


@dataclass(frozen=True)
class FidelityConfig:
    config_id: str
    scoring_method: str
    factor_specs: tuple[FactorSpec, ...]
    description: str
    strict_red_veto: bool = False
    short_veto_in_stress: bool = False
    freeze_rebalance_in_red: bool = False


def _to_regime_adaptive(specs: list[FactorSpec]) -> list[FactorSpec]:
    out = [replace(spec, normalization="regime_adaptive") for spec in specs]
    validate_factor_specs(out)
    return out


def _build_market_regime(spy_returns: pd.Series, dates: pd.DatetimeIndex) -> pd.Series:
    s = pd.to_numeric(spy_returns, errors="coerce").fillna(0.0).astype(float).sort_index()
    vol21 = s.rolling(21, min_periods=21).std() * np.sqrt(252.0)
    mom63 = (1.0 + s).rolling(63, min_periods=63).apply(np.prod, raw=True) - 1.0
    regime = pd.Series("AMBER", index=s.index, dtype="object")
    regime[(vol21 > 0.30) | (mom63 < -0.03)] = "RED"
    regime[(vol21 < 0.18) & (mom63 > 0.02)] = "GREEN"
    out = regime.reindex(pd.DatetimeIndex(dates)).ffill().fillna("AMBER")
    out.index = pd.DatetimeIndex(dates)
    return out.astype(str).str.upper()


def _simulate_from_target_weights(
    target_weights: pd.DataFrame,
    returns_long: pd.DataFrame,
    cost_bps: float,
    allow_missing_returns: bool,
    max_matrix_cells: int,
) -> tuple[pd.DataFrame, int]:
    target = target_weights.sort_index()
    if target.empty and len(target.index) == 0:
        sim = pd.DataFrame(columns=["gross_ret", "net_ret", "turnover", "cost", "equity"])
        return sim, 0

    ret = returns_long.copy()
    ret["date"] = pd.to_datetime(ret["date"], errors="coerce")
    ret["permno"] = pd.to_numeric(ret["permno"], errors="coerce")
    ret["ret"] = pd.to_numeric(ret["ret"], errors="coerce")
    ret = ret.dropna(subset=["date", "permno"]).sort_values(["date", "permno"])
    returns_wide = ret.pivot(index="date", columns="permno", values="ret").sort_index()

    matrix_cells = int(len(target.index) * max(1, target.shape[1]))
    if matrix_cells > int(max_matrix_cells):
        raise RuntimeError(f"Target matrix too large ({matrix_cells:,} > {int(max_matrix_cells):,})")

    if target.shape[1] == 0:
        aligned = pd.DataFrame(index=target.index)
        missing_active = 0
    else:
        returns_reindexed = returns_wide.reindex(index=target.index, columns=target.columns)
        executed = target.shift(1).fillna(0.0).ne(0.0)
        missing_active = int((returns_reindexed.isna() & executed).sum().sum())
        if missing_active > 0 and not allow_missing_returns:
            raise RuntimeError(f"Missing {missing_active:,} executed-exposure return cells; rerun with --allow-missing-returns")
        if missing_active > 0 and allow_missing_returns:
            print(f"WARNING: Missing executed-exposure return cells treated as zero: {missing_active:,}")
        aligned = returns_reindexed

    sim = engine.run_simulation(
        target_weights=target,
        returns_df=aligned,
        cost_bps=float(cost_bps) / 10000.0,
        strict_missing_returns=not allow_missing_returns,
    ).copy()
    sim.index = pd.DatetimeIndex(sim.index)
    sim.index.name = "date"
    sim["equity"] = (1.0 + pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)).cumprod()
    return sim, missing_active


def _simulate_perf(sim: pd.DataFrame) -> dict[str, float]:
    if sim.empty:
        return {
            "sharpe": np.nan,
            "cagr": np.nan,
            "max_dd": np.nan,
            "max_dd_abs": np.nan,
            "ulcer": np.nan,
            "turnover_annual": np.nan,
            "turnover_total": np.nan,
            "n_backtest_days": 0.0,
        }
    ret = pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)
    eq = pd.to_numeric(sim["equity"], errors="coerce").ffill()
    turnover = pd.to_numeric(sim["turnover"], errors="coerce").fillna(0.0)
    max_dd = float(compute_max_drawdown(eq))
    return {
        "sharpe": float(compute_sharpe(ret)),
        "cagr": float(compute_cagr(eq)),
        "max_dd": max_dd,
        "max_dd_abs": float(abs(max_dd)),
        "ulcer": float(compute_ulcer_index(eq)),
        "turnover_annual": float(turnover.mean() * 252.0),
        "turnover_total": float(turnover.sum()),
        "n_backtest_days": float(len(sim)),
    }


def _apply_red_regime_freeze(target_weights: pd.DataFrame, regime_by_date: pd.Series) -> pd.DataFrame:
    out = target_weights.copy().sort_index()
    if out.empty:
        return out
    regime = pd.Series(regime_by_date).copy()
    regime.index = pd.to_datetime(regime.index, errors="coerce")
    regime = regime[~regime.index.isna()].astype(str).str.upper()
    prev = None
    for dt in out.index:
        if str(regime.get(dt, "AMBER")).upper() == "RED" and prev is not None:
            out.loc[dt] = prev.values
        prev = out.loc[dt].copy()
    return out


def _apply_short_veto_in_stress(scores: pd.DataFrame, features: pd.DataFrame, regime_by_date: pd.Series) -> pd.DataFrame:
    out = scores.copy()
    needed = [
        c
        for c in ["date", "permno", "z_inventory_quality_proxy", "capital_cycle_score", "z_moat", "z_flow_proxy", "amihud_20d"]
        if c in features.columns
    ]
    if not {"date", "permno"}.issubset(set(needed)):
        return out
    aux = features[needed].drop_duplicates(subset=["date", "permno"], keep="last")
    out = out.merge(aux, on=["date", "permno"], how="left")

    regime = pd.Series(regime_by_date).copy()
    regime.index = pd.to_datetime(regime.index, errors="coerce")
    regime = regime[~regime.index.isna()].astype(str).str.upper()
    out["__regime__"] = pd.to_datetime(out["date"], errors="coerce").map(regime).fillna("AMBER")

    quality = pd.Series(np.nan, index=out.index, dtype=float)
    for c in ["z_inventory_quality_proxy", "capital_cycle_score", "z_moat"]:
        if c in out.columns:
            quality = quality.where(quality.notna(), pd.to_numeric(out[c], errors="coerce"))
    liq = pd.Series(np.nan, index=out.index, dtype=float)
    if "z_flow_proxy" in out.columns:
        liq = liq.where(liq.notna(), pd.to_numeric(out["z_flow_proxy"], errors="coerce"))
    if "amihud_20d" in out.columns:
        liq = liq.where(liq.notna(), -pd.to_numeric(out["amihud_20d"], errors="coerce"))
    out["__quality__"] = quality
    out["__liq__"] = liq

    valid = pd.to_numeric(out.get("score_valid"), errors="coerce").fillna(False).astype(bool)
    stress = out["__regime__"].astype(str).str.upper().isin(["AMBER", "RED"])
    score = pd.to_numeric(out.get("score"), errors="coerce")
    for _, idx in out[stress & valid & score.notna()].groupby(pd.to_datetime(out["date"], errors="coerce")).groups.items():
        block = out.loc[idx].copy()
        q30 = pd.to_numeric(block["__quality__"], errors="coerce").quantile(0.30)
        l30 = pd.to_numeric(block["__liq__"], errors="coerce").quantile(0.30)
        med = pd.to_numeric(block["score"], errors="coerce").median()
        fluff = (
            pd.to_numeric(block["__quality__"], errors="coerce").le(q30)
            & pd.to_numeric(block["__liq__"], errors="coerce").le(l30)
            & pd.to_numeric(block["score"], errors="coerce").notna()
        )
        fluff_idx = block.index[fluff]
        if len(fluff_idx):
            out.loc[fluff_idx, "score"] = np.maximum(pd.to_numeric(out.loc[fluff_idx, "score"], errors="coerce"), med)

    drop_cols = [c for c in ["__regime__", "__quality__", "__liq__", "z_inventory_quality_proxy", "capital_cycle_score", "z_moat", "z_flow_proxy", "amihud_20d"] if c in out.columns]
    return out.drop(columns=drop_cols, errors="ignore")


def _compute_scores(features: pd.DataFrame, cfg: FidelityConfig, regime_by_date: pd.Series) -> tuple[pd.DataFrame, Any]:
    scorecard = CompanyScorecard(
        factor_specs=list(cfg.factor_specs),
        scoring_method=cfg.scoring_method,
        regime_by_date=regime_by_date,
        strict_red_veto=cfg.strict_red_veto,
        veto_regimes=("RED",),
    )
    scores, summary = scorecard.compute_scores(features)
    if cfg.short_veto_in_stress:
        scores = _apply_short_veto_in_stress(scores=scores, features=features, regime_by_date=regime_by_date)
    return scores, summary


def _simulate_config(
    scores: pd.DataFrame,
    returns: pd.DataFrame,
    regime_by_date: pd.Series,
    cfg: FidelityConfig,
    top_quantile: float,
    cost_bps: float,
    allow_missing_returns: bool,
    max_matrix_cells: int,
) -> tuple[pd.DataFrame, int]:
    target = _build_target_weights(scores=scores, top_quantile=top_quantile)
    if cfg.freeze_rebalance_in_red:
        target = _apply_red_regime_freeze(target_weights=target, regime_by_date=regime_by_date)
    return _simulate_from_target_weights(
        target_weights=target,
        returns_long=returns,
        cost_bps=cost_bps,
        allow_missing_returns=allow_missing_returns,
        max_matrix_cells=max_matrix_cells,
    )


def _analyze_decay(
    features: pd.DataFrame,
    returns: pd.DataFrame,
    regime_by_date: pd.Series,
    cfg: FidelityConfig,
    top_quantile: float,
    cost_bps: float,
    allow_missing_returns: bool,
    max_matrix_cells: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for decay in [0.85, 0.90, 0.95, 0.98, 0.99]:
        alpha = 1.0 - float(decay)
        specs = [replace(s, leaky_alpha=alpha) if s.use_leaky_integrator else s for s in cfg.factor_specs]
        tmp_cfg = replace(cfg, factor_specs=tuple(specs))
        scores, summary = _compute_scores(features=features, cfg=tmp_cfg, regime_by_date=regime_by_date)
        sim, missing = _simulate_config(
            scores=scores,
            returns=returns,
            regime_by_date=regime_by_date,
            cfg=tmp_cfg,
            top_quantile=top_quantile,
            cost_bps=cost_bps,
            allow_missing_returns=allow_missing_returns,
            max_matrix_cells=max_matrix_cells,
        )
        perf = _simulate_perf(sim)
        rows.append(
            {
                "decay": float(decay),
                "alpha": alpha,
                "coverage": float(summary.coverage),
                "sharpe": float(perf["sharpe"]),
                "turnover_annual": float(perf["turnover_annual"]),
                "max_dd": float(perf["max_dd"]),
                "missing_active_return_cells": int(missing),
            }
        )
    out = pd.DataFrame(rows).sort_values("decay").reset_index(drop=True)
    base = out[np.isclose(out["decay"], 0.95)]
    base_sh = float(base["sharpe"].iloc[0]) if not base.empty else np.nan
    base_to = float(base["turnover_annual"].iloc[0]) if not base.empty else np.nan
    out["sharpe_delta_vs_0_95"] = pd.to_numeric(out["sharpe"], errors="coerce") - base_sh
    out["turnover_delta_vs_0_95"] = pd.to_numeric(out["turnover_annual"], errors="coerce") - base_to
    return out


def _build_configs(c3_decay: float) -> list[FidelityConfig]:
    c3 = _build_c3_specs(c3_decay)
    p195 = build_phase19_5_candidate_factor_sets()
    c3_regime = _to_regime_adaptive(c3)
    p4_regime = _to_regime_adaptive(p195["P195_SIGNAL_STRENGTH_4F"])
    p5_regime = _to_regime_adaptive(p195["P195_SIGNAL_STRENGTH_5F"])

    configs = [
        FidelityConfig("C3_LOCKED", "complete_case", tuple(c3), "Locked C3 baseline.", False, False, False),
        FidelityConfig("P197_C3_STRICT_RED_PARTIAL", "partial", tuple(c3_regime), "C3 regime-adaptive with strict RED-veto.", True, True, True),
        FidelityConfig("P197_4F_STRICT_RED_PARTIAL", "partial", tuple(p4_regime), "4F regime-adaptive with strict RED-veto.", True, True, True),
        FidelityConfig("P197_5F_STRICT_RED_PARTIAL", "partial", tuple(p5_regime), "5F regime-adaptive with strict RED-veto.", True, True, True),
        FidelityConfig("P197_RANK_4F_STRICT_RED", "partial", tuple(p195["P195_SIGNAL_STRENGTH_4F_RANK"]), "Rank-4F with strict RED-veto.", True, True, True),
    ]
    for cfg in configs:
        validate_factor_specs(list(cfg.factor_specs))
    return configs


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 19.7 regime-fidelity forensics sprint")
    p.add_argument("--input-features", default=str(DEFAULT_FEATURES_PATH))
    p.add_argument("--input-prices", default=None)
    p.add_argument("--start-date", default="2015-01-01")
    p.add_argument("--end-date", default="2024-12-31")
    p.add_argument("--cost-bps", type=float, default=5.0)
    p.add_argument("--top-quantile", type=float, default=0.10)
    p.add_argument("--c3-decay", type=float, default=0.95)
    p.add_argument("--allow-missing-returns", action="store_true")
    p.add_argument("--max-matrix-cells", type=int, default=25_000_000)
    p.add_argument("--output-ablation-csv", default=str(DEFAULT_OUTPUT_ABLATION))
    p.add_argument("--output-delta-csv", default=str(DEFAULT_OUTPUT_DELTA))
    p.add_argument("--output-regime-audit-csv", default=str(DEFAULT_OUTPUT_REGIME_AUDIT))
    p.add_argument("--output-walkforward-csv", default=str(DEFAULT_OUTPUT_WALKFORWARD))
    p.add_argument("--output-decay-csv", default=str(DEFAULT_OUTPUT_DECAY))
    p.add_argument("--output-crisis-csv", default=str(DEFAULT_OUTPUT_CRISIS))
    p.add_argument("--output-checks-csv", default=str(DEFAULT_OUTPUT_CHECKS))
    p.add_argument("--output-summary-json", default=str(DEFAULT_OUTPUT_SUMMARY))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    start = _to_ts(args.start_date)
    end = _to_ts(args.end_date)
    if start is not None and end is not None and end < start:
        raise ValueError(f"end-date {end.date()} is earlier than start-date {start.date()}")
    if not (0.0 < float(args.top_quantile) < 1.0):
        raise ValueError("--top-quantile must be in (0,1)")

    features_path = _resolve_path(args.input_features, DEFAULT_FEATURES_PATH)
    default_prices = DEFAULT_PRICES_TRI_PATH if DEFAULT_PRICES_TRI_PATH.exists() else DEFAULT_PRICES_PATH
    prices_path = _resolve_path(args.input_prices, default_prices)
    if not prices_path.exists():
        raise FileNotFoundError(f"Returns artifact not found: {prices_path}")

    output_ablation = _resolve_path(args.output_ablation_csv, DEFAULT_OUTPUT_ABLATION)
    output_delta = _resolve_path(args.output_delta_csv, DEFAULT_OUTPUT_DELTA)
    output_regime_audit = _resolve_path(args.output_regime_audit_csv, DEFAULT_OUTPUT_REGIME_AUDIT)
    output_walkforward = _resolve_path(args.output_walkforward_csv, DEFAULT_OUTPUT_WALKFORWARD)
    output_decay = _resolve_path(args.output_decay_csv, DEFAULT_OUTPUT_DECAY)
    output_crisis = _resolve_path(args.output_crisis_csv, DEFAULT_OUTPUT_CRISIS)
    output_checks = _resolve_path(args.output_checks_csv, DEFAULT_OUTPUT_CHECKS)
    output_summary = _resolve_path(args.output_summary_json, DEFAULT_OUTPUT_SUMMARY)

    configs = _build_configs(c3_decay=float(args.c3_decay))
    all_candidates = sorted({c for cfg in configs for spec in cfg.factor_specs for c in spec.candidate_columns})
    all_candidates = sorted(set(all_candidates + ["z_inventory_quality_proxy", "z_flow_proxy", "amihud_20d", "capital_cycle_score", "z_moat"]))

    features = _load_features_subset(features_path=features_path, factor_columns=all_candidates, start_date=start, end_date=end)
    if features.empty:
        raise RuntimeError("No feature rows found for requested window.")
    permnos = sorted(pd.to_numeric(features["permno"], errors="coerce").dropna().astype(int).unique().tolist())
    returns = _load_returns_subset(prices_path=prices_path, permnos=permnos, start_date=start, end_date=end)
    if returns.empty:
        raise RuntimeError("No return rows found for selected universe/window.")

    all_dates = pd.DatetimeIndex(sorted(pd.to_datetime(features["date"], errors="coerce").dropna().unique()))
    spy_returns = _load_spy_returns(prices_path=prices_path, start_date=start, end_date=end)
    regime_by_date = _build_market_regime(spy_returns=spy_returns, dates=all_dates)

    print("=" * 80)
    print("PHASE 19.7 REGIME FIDELITY SPRINT")
    print("=" * 80)
    print(f"Window: {start.strftime('%Y-%m-%d')} -> {end.strftime('%Y-%m-%d')} | Configs={len(configs)}")

    rows: list[dict[str, Any]] = []
    regime_audit_frames: list[pd.DataFrame] = []
    scores_by_cfg: dict[str, pd.DataFrame] = {}
    sims_by_cfg: dict[str, pd.DataFrame] = {}

    for i, cfg in enumerate(configs, start=1):
        print(f"[{i}/{len(configs)}] {cfg.config_id}")
        scores, summary = _compute_scores(features=features, cfg=cfg, regime_by_date=regime_by_date)
        scores_by_cfg[cfg.config_id] = scores
        checks = build_validation_table(scores=scores, factor_names=[s.name for s in cfg.factor_specs])
        vmap = {str(r["check"]): float(r["value"]) if pd.notna(r["value"]) else np.nan for _, r in checks.iterrows()}
        sim, missing = _simulate_config(
            scores=scores,
            returns=returns,
            regime_by_date=regime_by_date,
            cfg=cfg,
            top_quantile=float(args.top_quantile),
            cost_bps=float(args.cost_bps),
            allow_missing_returns=bool(args.allow_missing_returns),
            max_matrix_cells=int(args.max_matrix_cells),
        )
        sims_by_cfg[cfg.config_id] = sim
        perf = _simulate_perf(sim)

        factor_names = [s.name for s in cfg.factor_specs]
        regime_diag = per_regime_audit(scores=scores, factor_names=factor_names, regime_by_date=regime_by_date)
        if not regime_diag.empty:
            regime_diag["config_id"] = cfg.config_id
            regime_audit_frames.append(regime_diag)

        spread_by_regime = (
            regime_diag[
                (regime_diag["metric"] == "quartile_spread_sigma")
                & (regime_diag["regime"].isin(["GREEN", "AMBER", "RED"]))
            ][["regime", "value", "n_rows"]]
            if not regime_diag.empty
            else pd.DataFrame(columns=["regime", "value", "n_rows"])
        )
        if spread_by_regime.empty:
            spread_min = np.nan
            spread_weighted = np.nan
        else:
            spread_min = float(pd.to_numeric(spread_by_regime["value"], errors="coerce").min())
            w = pd.to_numeric(spread_by_regime["n_rows"], errors="coerce").fillna(0.0)
            s = pd.to_numeric(spread_by_regime["value"], errors="coerce")
            spread_weighted = float((s * w).sum() / w.sum()) if float(w.sum()) > 0 else np.nan

        norm_cols = [f"{s.name}_normalized" for s in cfg.factor_specs if f"{s.name}_normalized" in scores.columns]
        corr = correlation_audit(frame=scores[["date"] + norm_cols], factor_columns=norm_cols, date_col="date", regime_by_date=regime_by_date)
        max_abs_corr = (
            float(pd.to_numeric(corr[corr["regime"] == "ALL"]["abs_corr"], errors="coerce").max())
            if not corr.empty
            else np.nan
        )

        rows.append(
            {
                "config_id": cfg.config_id,
                "description": cfg.description,
                "scoring_method": cfg.scoring_method,
                "strict_red_veto": bool(cfg.strict_red_veto),
                "short_veto_in_stress": bool(cfg.short_veto_in_stress),
                "freeze_rebalance_in_red": bool(cfg.freeze_rebalance_in_red),
                "coverage": float(vmap.get("score_coverage", np.nan)),
                "quartile_spread_sigma": float(vmap.get("quartile_spread_sigma", np.nan)),
                "regime_spread_sigma_min": spread_min,
                "regime_weighted_spread_sigma": spread_weighted,
                "adjacent_rank_correlation": float(vmap.get("adjacent_rank_correlation", np.nan)),
                "orthogonality_max_abs_corr": max_abs_corr,
                "sharpe": float(perf["sharpe"]),
                "turnover_annual": float(perf["turnover_annual"]),
                "max_dd": float(perf["max_dd"]),
                "max_dd_abs": float(perf["max_dd_abs"]),
                "score_rows": int(summary.n_rows),
                "score_dates": int(summary.n_dates),
                "missing_factor_families": ",".join(summary.missing_factor_columns),
                "missing_active_return_cells": int(missing),
            }
        )

    ablation = pd.DataFrame(rows).reset_index(drop=True)
    baseline_row = ablation[ablation["config_id"] == "C3_LOCKED"].iloc[0]
    baseline_sim = sims_by_cfg["C3_LOCKED"]

    crisis_map: dict[str, tuple[float, bool]] = {}
    for cfg in configs:
        if cfg.config_id == "C3_LOCKED":
            crisis_map[cfg.config_id] = (np.nan, False)
            continue
        crisis_i = validate_crisis_turnover(baseline_sim=baseline_sim, c3_sim=sims_by_cfg[cfg.config_id])
        red_i = pd.to_numeric(crisis_i["reduction_pct"], errors="coerce")
        crisis_map[cfg.config_id] = (
            float(red_i.min()) if len(red_i) else np.nan,
            bool(len(crisis_i) > 0 and red_i.notna().all() and red_i.ge(80.0).all()),
        )
    ablation["crisis_min_reduction_pct"] = ablation["config_id"].map(lambda c: crisis_map.get(c, (np.nan, False))[0])
    ablation["gate_crisis_ge_80_all"] = ablation["config_id"].map(lambda c: crisis_map.get(c, (np.nan, False))[1]).astype(bool)

    candidates = ablation[ablation["config_id"] != "C3_LOCKED"].copy()
    candidates["gate_coverage"] = pd.to_numeric(candidates["coverage"], errors="coerce") >= 0.90
    candidates["gate_spread_all_regimes"] = pd.to_numeric(candidates["regime_spread_sigma_min"], errors="coerce") >= 2.30
    candidates["gate_sharpe"] = pd.to_numeric(candidates["sharpe"], errors="coerce") >= 0.95
    candidates["gate_count"] = (
        candidates[["gate_coverage", "gate_spread_all_regimes", "gate_sharpe", "gate_crisis_ge_80_all"]]
        .sum(axis=1)
        .astype(int)
    )
    candidates = candidates.sort_values(["gate_count", "regime_spread_sigma_min", "sharpe"], ascending=[False, False, False])
    selected_id = str(candidates.iloc[0]["config_id"]) if not candidates.empty else "C3_LOCKED"
    selected_row = ablation[ablation["config_id"] == selected_id].iloc[0]
    selected_sim = sims_by_cfg[selected_id]
    selected_scores = scores_by_cfg[selected_id]
    baseline_scores = scores_by_cfg["C3_LOCKED"]

    delta = pd.DataFrame(
        [
            {
                "baseline_config_id": "C3_LOCKED",
                "selected_config_id": selected_id,
                "coverage_baseline": float(baseline_row["coverage"]),
                "coverage_selected": float(selected_row["coverage"]),
                "coverage_delta": float(selected_row["coverage"] - baseline_row["coverage"]),
                "spread_baseline": float(baseline_row["quartile_spread_sigma"]),
                "spread_selected": float(selected_row["quartile_spread_sigma"]),
                "spread_delta": float(selected_row["quartile_spread_sigma"] - baseline_row["quartile_spread_sigma"]),
                "regime_spread_min_selected": float(selected_row["regime_spread_sigma_min"]),
                "regime_weighted_spread_selected": float(selected_row["regime_weighted_spread_sigma"]),
                "sharpe_baseline": float(baseline_row["sharpe"]),
                "sharpe_selected": float(selected_row["sharpe"]),
                "sharpe_delta": float(selected_row["sharpe"] - baseline_row["sharpe"]),
                "turnover_baseline": float(baseline_row["turnover_annual"]),
                "turnover_selected": float(selected_row["turnover_annual"]),
                "turnover_ratio_selected_vs_baseline": (
                    float(selected_row["turnover_annual"] / baseline_row["turnover_annual"])
                    if abs(float(baseline_row["turnover_annual"])) > 1e-12
                    else np.nan
                ),
            }
        ]
    )

    walkforward = run_walk_forward_validation(
        baseline_sim=baseline_sim,
        c3_sim=selected_sim,
        baseline_scores=baseline_scores,
        c3_scores=selected_scores,
        spy_returns=spy_returns,
    )
    selected_cfg = next(cfg for cfg in configs if cfg.config_id == selected_id)
    decay = _analyze_decay(
        features=features,
        returns=returns,
        regime_by_date=regime_by_date,
        cfg=selected_cfg,
        top_quantile=float(args.top_quantile),
        cost_bps=float(args.cost_bps),
        allow_missing_returns=bool(args.allow_missing_returns),
        max_matrix_cells=int(args.max_matrix_cells),
    )
    crisis = validate_crisis_turnover(baseline_sim=baseline_sim, c3_sim=selected_sim)
    checks = evaluate_checks(walkforward_df=walkforward, decay_df=decay, crisis_df=crisis)
    checks["evidence_file"] = (
        checks["evidence_file"]
        .astype(str)
        .str.replace("phase18_day6_walkforward.csv", "phase19_7_walkforward.csv", regex=False)
        .str.replace("phase18_day6_decay_sensitivity.csv", "phase19_7_decay_sensitivity.csv", regex=False)
        .str.replace("phase18_day6_crisis_turnover.csv", "phase19_7_crisis_turnover.csv", regex=False)
    )

    gate_coverage = bool(float(selected_row["coverage"]) >= 0.90)
    gate_spread = bool(float(selected_row["regime_spread_sigma_min"]) >= 2.30)
    gate_sharpe = bool(float(selected_row["sharpe"]) >= 0.95)
    crisis_reductions = pd.to_numeric(crisis["reduction_pct"], errors="coerce")
    gate_crisis = bool(len(crisis) > 0 and crisis_reductions.notna().all() and crisis_reductions.ge(80.0).all())

    check_map = {str(r["check_id"]): bool(r["pass"]) for _, r in checks.iterrows()}
    bundle_ids = ["CHK-41", "CHK-48", "CHK-50", "CHK-51", "CHK-53"]
    bundle_passes = int(sum(check_map.get(cid, False) for cid in bundle_ids))
    gate_chk_bundle = bool(bundle_passes >= 4)

    gates = {
        "gate_coverage_ge_90": gate_coverage,
        "gate_spread_sigma_ge_2_30_all_regimes": gate_spread,
        "gate_sharpe_ge_0_95": gate_sharpe,
        "gate_crisis_turnover_reduction_ge_80_all_windows": gate_crisis,
    }
    gates_passed = int(sum(bool(v) for v in gates.values()))
    gates_total = int(len(gates))
    decision = "PROMOTE" if (gates_passed == gates_total and gate_chk_bundle) else "ABORT_PIVOT"
    saw_target_verdict = "PASS" if decision == "PROMOTE" else "BLOCK"

    regime_audit = pd.concat(regime_audit_frames, axis=0, ignore_index=True) if regime_audit_frames else pd.DataFrame()
    _atomic_csv_write(ablation, output_ablation)
    _atomic_csv_write(delta, output_delta)
    _atomic_csv_write(regime_audit, output_regime_audit)
    _atomic_csv_write(walkforward, output_walkforward)
    _atomic_csv_write(decay, output_decay)
    _atomic_csv_write(crisis, output_crisis)
    _atomic_csv_write(checks, output_checks)

    summary = {
        "status": "ok",
        "window": {"start_date": start.strftime("%Y-%m-%d"), "end_date": end.strftime("%Y-%m-%d")},
        "cost_bps": float(args.cost_bps),
        "top_quantile": float(args.top_quantile),
        "baseline_config_id": "C3_LOCKED",
        "selected_config_id": selected_id,
        "selected_scoring_method": str(selected_row["scoring_method"]),
        "gate_chk_bundle": {"bundle_ids": bundle_ids, "bundle_passes": bundle_passes, "bundle_required": 4},
        "gates": gates,
        "gates_passed": gates_passed,
        "gates_total": gates_total,
        "decision": decision,
        "saw_target_verdict": saw_target_verdict,
        "artifacts": {
            "ablation_csv": str(output_ablation),
            "delta_csv": str(output_delta),
            "regime_audit_csv": str(output_regime_audit),
            "walkforward_csv": str(output_walkforward),
            "decay_csv": str(output_decay),
            "crisis_csv": str(output_crisis),
            "checks_csv": str(output_checks),
        },
    }
    _atomic_json_write(summary, output_summary)

    print(f"selected_id={selected_id}")
    print(
        f"coverage={float(selected_row['coverage']):.4f} "
        f"spread_min={float(selected_row['regime_spread_sigma_min']):.4f} "
        f"sharpe={float(selected_row['sharpe']):.4f}"
    )
    print(f"gate_passes={gates_passed}/{gates_total} bundle_passes={bundle_passes}/5")
    print(f"decision={decision} saw_target_verdict={saw_target_verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
