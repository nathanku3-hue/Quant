from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from core import engine  # noqa: E402
from scripts.scorecard_validation import build_validation_table  # noqa: E402
from strategies.company_scorecard import CompanyScorecard  # noqa: E402
from strategies.factor_specs import FactorSpec  # noqa: E402
from strategies.factor_specs import build_default_factor_specs  # noqa: E402
from strategies.factor_specs import validate_factor_specs  # noqa: E402
from utils.metrics import compute_cagr  # noqa: E402
from utils.metrics import compute_max_drawdown  # noqa: E402
from utils.metrics import compute_sharpe  # noqa: E402
from utils.metrics import compute_ulcer_index  # noqa: E402


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_FEATURES_PATH = PROCESSED_DIR / "features.parquet"
DEFAULT_PRICES_TRI_PATH = PROCESSED_DIR / "prices_tri.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_OUTPUT_METRICS = PROCESSED_DIR / "phase18_day5_ablation_metrics.csv"
DEFAULT_OUTPUT_DELTAS = PROCESSED_DIR / "phase18_day5_ablation_deltas.csv"
DEFAULT_OUTPUT_SUMMARY = PROCESSED_DIR / "phase18_day5_ablation_summary.json"


@dataclass(frozen=True)
class AblationConfig:
    config_id: str
    scoring_method: str
    factor_specs: tuple[FactorSpec, ...]
    description: str


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


def _atomic_json_write(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    tries = 8
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
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
    df["permno"] = pd.to_numeric(df["permno"], errors="coerce")
    df = df.dropna(subset=["date", "permno"]).sort_values(["date", "permno"]).reset_index(drop=True)
    return df


def _load_returns_subset(
    prices_path: Path,
    permnos: list[int],
    start_date: pd.Timestamp | None,
    end_date: pd.Timestamp | None,
) -> pd.DataFrame:
    if not prices_path.exists():
        raise FileNotFoundError(f"Missing prices artifact: {prices_path}")
    if not permnos:
        return pd.DataFrame(columns=["date", "permno", "ret"])

    con = duckdb.connect()
    try:
        schema = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{_sql_escape_path(prices_path)}')").df()
        cols = set(schema["column_name"].astype(str).tolist())
        has_total_ret = "total_ret" in cols

        where = []
        if len(permnos) <= 5000:
            permno_literals = ",".join(str(int(p)) for p in sorted(set(permnos)))
            where.append(f"CAST(p.permno AS BIGINT) IN ({permno_literals})")
            join_sql = ""
        else:
            target_permnos = pd.DataFrame({"permno": pd.Series(permnos, dtype="int64")})
            con.register("target_permnos", target_permnos)
            join_sql = """
            INNER JOIN target_permnos AS t
                ON CAST(p.permno AS BIGINT) = t.permno
            """
        if start_date is not None:
            where.append(f"CAST(p.date AS DATE) >= DATE '{start_date.strftime('%Y-%m-%d')}'")
        if end_date is not None:
            where.append(f"CAST(p.date AS DATE) <= DATE '{end_date.strftime('%Y-%m-%d')}'")
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        try:
            if has_total_ret:
                query = f"""
                SELECT
                    CAST(p.date AS DATE) AS date,
                    CAST(p.permno AS BIGINT) AS permno,
                    CAST(p.total_ret AS DOUBLE) AS ret
                FROM read_parquet('{_sql_escape_path(prices_path)}') AS p
                {join_sql}
                {where_sql}
                ORDER BY date, permno
                """
                out = con.execute(query).df()
            else:
                query = f"""
                SELECT
                    CAST(p.date AS DATE) AS date,
                    CAST(p.permno AS BIGINT) AS permno,
                    CAST(p.adj_close AS DOUBLE) AS price
                FROM read_parquet('{_sql_escape_path(prices_path)}') AS p
                {join_sql}
                {where_sql}
                ORDER BY date, permno
                """
                tmp = con.execute(query).df()
                tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")
                tmp["permno"] = pd.to_numeric(tmp["permno"], errors="coerce")
                tmp["price"] = pd.to_numeric(tmp["price"], errors="coerce")
                tmp = tmp.dropna(subset=["date", "permno"]).sort_values(["permno", "date"])
                tmp["ret"] = tmp.groupby("permno", sort=False)["price"].pct_change(fill_method=None)
                out = tmp[["date", "permno", "ret"]].copy()
        finally:
            if len(permnos) > 5000:
                con.unregister("target_permnos")
    finally:
        con.close()

    if out.empty:
        return out
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["permno"] = pd.to_numeric(out["permno"], errors="coerce")
    out["ret"] = pd.to_numeric(out["ret"], errors="coerce")
    out = out.dropna(subset=["date", "permno"]).sort_values(["date", "permno"]).reset_index(drop=True)
    return out


def _apply_updates(
    specs: list[FactorSpec],
    updates: dict[str, dict[str, Any]],
    drop_names: set[str] | None = None,
) -> list[FactorSpec]:
    out: list[FactorSpec] = []
    drop_names = drop_names or set()
    for spec in specs:
        if spec.name in drop_names:
            continue
        kwargs = updates.get(spec.name, {})
        out.append(replace(spec, **kwargs))
    return out


def build_ablation_configs() -> list[AblationConfig]:
    base = build_default_factor_specs()
    validate_factor_specs(base)

    configs: list[AblationConfig] = []
    configs.append(
        AblationConfig(
            config_id="BASELINE_DAY4",
            scoring_method="complete_case",
            factor_specs=tuple(base),
            description="Equal-weight complete-case baseline control.",
        )
    )

    configs.append(
        AblationConfig(
            config_id="ABLATION_A1_PARTIAL",
            scoring_method="partial",
            factor_specs=tuple(base),
            description="Track A: partial scoring with dynamic weight re-normalization.",
        )
    )

    b1_ir = _apply_updates(
        specs=base,
        updates={
            "momentum": {"weight": 0.29},
            "quality": {"weight": 0.20},
            "volatility": {"weight": 0.27},
            "illiquidity": {"weight": 0.24},
        },
    )
    validate_factor_specs(b1_ir)
    configs.append(
        AblationConfig(
            config_id="ABLATION_B1_IR_WEIGHT",
            scoring_method="complete_case",
            factor_specs=tuple(b1_ir),
            description="Track B: IR-style weighting tilt toward stronger discriminators.",
        )
    )

    c3_integrator = _apply_updates(
        specs=base,
        updates={
            s.name: {
                "use_sigmoid_blend": False,
                "use_dirty_derivative": False,
                "use_leaky_integrator": True,
                "leaky_alpha": 0.20,
            }
            for s in base
        },
    )
    validate_factor_specs(c3_integrator)
    configs.append(
        AblationConfig(
            config_id="ABLATION_C3_INTEGRATOR",
            scoring_method="complete_case",
            factor_specs=tuple(c3_integrator),
            description="Track C: leaky-integrator only.",
        )
    )

    c1_sigmoid = _apply_updates(
        specs=base,
        updates={
            s.name: {
                "use_sigmoid_blend": True,
                "use_dirty_derivative": False,
                "use_leaky_integrator": False,
                "sigmoid_k": 0.5,
            }
            for s in base
        },
    )
    validate_factor_specs(c1_sigmoid)
    configs.append(
        AblationConfig(
            config_id="ABLATION_C1_SIGMOID",
            scoring_method="complete_case",
            factor_specs=tuple(c1_sigmoid),
            description="Track C: sigmoid blender only.",
        )
    )

    c4_full = _apply_updates(
        specs=base,
        updates={
            s.name: {
                "use_sigmoid_blend": True,
                "use_dirty_derivative": True,
                "use_leaky_integrator": True,
                "sigmoid_k": 0.5,
                "derivative_weight": 0.25,
                "leaky_alpha": 0.20,
            }
            for s in base
        },
    )
    validate_factor_specs(c4_full)
    configs.append(
        AblationConfig(
            config_id="ABLATION_C4_FULL",
            scoring_method="complete_case",
            factor_specs=tuple(c4_full),
            description="Track C: full control stack.",
        )
    )

    ac_optimal = _apply_updates(
        specs=b1_ir,
        updates={
            s.name: {
                "use_sigmoid_blend": True,
                "use_dirty_derivative": True,
                "use_leaky_integrator": True,
                "sigmoid_k": 0.5,
                "derivative_weight": 0.25,
                "leaky_alpha": 0.20,
            }
            for s in b1_ir
        },
    )
    validate_factor_specs(ac_optimal)
    configs.append(
        AblationConfig(
            config_id="ABLATION_AC_OPTIMAL",
            scoring_method="partial",
            factor_specs=tuple(ac_optimal),
            description="Combined A/C path: partial + IR + full control stack.",
        )
    )

    b3_hier = _apply_updates(
        specs=base,
        updates={
            "momentum": {"weight": 0.40},
            "volatility": {"weight": 0.30},
            "illiquidity": {"weight": 0.20},
            "quality": {"weight": 0.10},
        },
    )
    validate_factor_specs(b3_hier)
    configs.append(
        AblationConfig(
            config_id="ABLATION_B3_HIERARCHICAL",
            scoring_method="complete_case",
            factor_specs=tuple(b3_hier),
            description="Track B: hierarchical weighting by factor tier.",
        )
    )

    a3_fallback = _apply_updates(
        specs=base,
        updates={
            "momentum": {"candidate_columns": ("resid_mom_60d", "rel_strength_60d", "rsi_14d")},
            "quality": {"candidate_columns": ("quality_composite", "capital_cycle_score", "z_moat", "z_inventory_quality_proxy")},
            "volatility": {"candidate_columns": ("realized_vol_21d", "yz_vol_20d", "atr_14d")},
            "illiquidity": {"candidate_columns": ("illiq_21d", "amihud_20d", "z_flow_proxy")},
        },
    )
    validate_factor_specs(a3_fallback)
    configs.append(
        AblationConfig(
            config_id="ABLATION_A3_FALLBACK",
            scoring_method="complete_case",
            factor_specs=tuple(a3_fallback),
            description="Track A: fallback-chain expansion while keeping complete-case semantics.",
        )
    )

    if len(configs) != 9:
        raise RuntimeError(f"Expected 9 configurations, got {len(configs)}")
    for cfg in configs:
        validate_factor_specs(list(cfg.factor_specs))
    return configs


def _build_target_weights(scores: pd.DataFrame, top_quantile: float) -> pd.DataFrame:
    valid = scores.loc[
        pd.to_numeric(scores["score_valid"], errors="coerce").fillna(False).astype(bool)
        & pd.to_numeric(scores["score"], errors="coerce").notna(),
        ["date", "permno", "score"],
    ].copy()
    valid["date"] = pd.to_datetime(valid["date"], errors="coerce")
    valid["permno"] = pd.to_numeric(valid["permno"], errors="coerce")
    valid["score"] = pd.to_numeric(valid["score"], errors="coerce")
    valid = valid.dropna(subset=["date", "permno", "score"]).sort_values(["date", "permno"])

    all_dates = pd.DatetimeIndex(sorted(pd.to_datetime(scores["date"], errors="coerce").dropna().unique()))
    if valid.empty or len(all_dates) == 0:
        return pd.DataFrame(index=all_dates)

    valid["rank_desc"] = valid.groupby("date")["score"].rank(method="first", ascending=False)
    counts = valid.groupby("date")["permno"].transform("size")
    n_select = np.maximum(1, np.ceil(counts * float(top_quantile))).astype(int)
    selected = valid[valid["rank_desc"] <= n_select].copy()
    if selected.empty:
        return pd.DataFrame(index=all_dates)

    selected["target_weight"] = 1.0 / selected.groupby("date")["permno"].transform("size")
    target = (
        selected.pivot(index="date", columns="permno", values="target_weight")
        .sort_index()
        .fillna(0.0)
    )
    target = target.reindex(all_dates).fillna(0.0)
    return target


def _simulate_scores_strategy(
    scores: pd.DataFrame,
    returns_long: pd.DataFrame,
    top_quantile: float,
    cost_bps: float,
    allow_missing_returns: bool,
    max_matrix_cells: int,
) -> tuple[pd.DataFrame, dict[str, float]]:
    target_weights = _build_target_weights(scores=scores, top_quantile=top_quantile)
    if target_weights.empty and len(target_weights.index) == 0:
        empty = pd.DataFrame(columns=["gross_ret", "net_ret", "turnover", "cost", "equity"])
        return empty, {
            "sharpe": np.nan,
            "cagr": np.nan,
            "max_dd": np.nan,
            "ulcer": np.nan,
            "turnover_annual": np.nan,
            "turnover_total": np.nan,
            "n_backtest_days": 0.0,
            "avg_positions": 0.0,
        }

    ret = returns_long.copy()
    ret["date"] = pd.to_datetime(ret["date"], errors="coerce")
    ret["permno"] = pd.to_numeric(ret["permno"], errors="coerce")
    ret["ret"] = pd.to_numeric(ret["ret"], errors="coerce")
    ret = ret.dropna(subset=["date", "permno"]).sort_values(["date", "permno"])
    returns_wide = ret.pivot(index="date", columns="permno", values="ret").sort_index()

    matrix_cells = int(len(target_weights.index) * max(1, target_weights.shape[1]))
    if matrix_cells > int(max_matrix_cells):
        raise RuntimeError(
            f"Target matrix too large ({matrix_cells:,} cells > {int(max_matrix_cells):,}). "
            "Lower universe size or raise --max-matrix-cells explicitly."
        )

    if target_weights.shape[1] == 0:
        returns_aligned = pd.DataFrame(index=target_weights.index)
    else:
        returns_reindexed = (
            returns_wide
            .reindex(index=target_weights.index, columns=target_weights.columns)
        )
        executed_positions = target_weights.shift(1).fillna(0.0).ne(0.0)
        missing_active = int((returns_reindexed.isna() & executed_positions).sum().sum())
        if missing_active > 0 and not allow_missing_returns:
            raise RuntimeError(
                f"Missing {missing_active:,} return cells on executed exposures. "
                "Use --allow-missing-returns to treat them as zero."
            )
        if missing_active > 0 and allow_missing_returns:
            print(f"WARNING: Missing executed-exposure return cells treated as zero: {missing_active:,}")
        returns_aligned = returns_reindexed

    sim = engine.run_simulation(
        target_weights=target_weights,
        returns_df=returns_aligned,
        cost_bps=float(cost_bps) / 10000.0,
        strict_missing_returns=not allow_missing_returns,
    )
    sim = sim.copy()
    sim["equity"] = (1.0 + pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)).cumprod()

    position_counts = (target_weights > 0.0).sum(axis=1)
    metrics = {
        "sharpe": float(compute_sharpe(sim["net_ret"])),
        "cagr": float(compute_cagr(sim["equity"])),
        "max_dd": float(compute_max_drawdown(sim["equity"])),
        "ulcer": float(compute_ulcer_index(sim["equity"])),
        "turnover_annual": float(pd.to_numeric(sim["turnover"], errors="coerce").mean() * 252.0),
        "turnover_total": float(pd.to_numeric(sim["turnover"], errors="coerce").sum()),
        "n_backtest_days": float(len(sim)),
        "avg_positions": float(position_counts.mean()) if len(position_counts) else 0.0,
    }
    return sim, metrics


def _validation_to_map(df: pd.DataFrame) -> dict[str, float]:
    out: dict[str, float] = {}
    for _, row in df.iterrows():
        out[str(row["check"])] = float(row["value"]) if pd.notna(row["value"]) else np.nan
    return out


def _build_deltas(metrics: pd.DataFrame, baseline_id: str) -> pd.DataFrame:
    if metrics.empty:
        return metrics.copy()
    if baseline_id not in set(metrics["config_id"]):
        raise ValueError(f"Baseline id {baseline_id} missing from metrics table")

    baseline = metrics[metrics["config_id"] == baseline_id].iloc[0]
    out = metrics.copy()
    delta_cols = [
        "coverage",
        "quartile_spread_sigma",
        "adjacent_rank_correlation",
        "factor_balance_max_share",
        "sharpe",
        "cagr",
        "max_dd",
        "ulcer",
        "turnover_annual",
    ]
    for c in delta_cols:
        out[f"delta_{c}"] = pd.to_numeric(out[c], errors="coerce") - float(baseline[c])

    base_turnover = float(baseline["turnover_annual"])
    if np.isfinite(base_turnover) and abs(base_turnover) > 1e-12:
        out["turnover_reduction_vs_baseline"] = 1.0 - (pd.to_numeric(out["turnover_annual"], errors="coerce") / base_turnover)
    else:
        out["turnover_reduction_vs_baseline"] = np.nan
    return out


def _select_optimal(
    deltas: pd.DataFrame,
    baseline_id: str,
    target_coverage: float,
    target_spread: float,
    target_turnover_reduction: float,
) -> tuple[str, dict[str, bool]]:
    if deltas.empty:
        return baseline_id, {
            "coverage_met": False,
            "spread_met": False,
            "turnover_reduction_met": False,
            "sharpe_preservation_met": False,
            "all_met": False,
        }

    baseline_row = deltas[deltas["config_id"] == baseline_id]
    if baseline_row.empty:
        raise ValueError(f"Missing baseline row: {baseline_id}")
    baseline_sharpe = float(baseline_row["sharpe"].iloc[0])

    candidates = deltas[deltas["config_id"] != baseline_id].copy()
    if candidates.empty:
        return baseline_id, {
            "coverage_met": False,
            "spread_met": False,
            "turnover_reduction_met": False,
            "sharpe_preservation_met": False,
            "all_met": False,
        }

    candidates["coverage_met"] = pd.to_numeric(candidates["coverage"], errors="coerce") >= float(target_coverage)
    candidates["spread_met"] = pd.to_numeric(candidates["quartile_spread_sigma"], errors="coerce") >= float(target_spread)
    candidates["turnover_reduction_met"] = (
        pd.to_numeric(candidates["turnover_reduction_vs_baseline"], errors="coerce") >= float(target_turnover_reduction)
    )
    candidates["sharpe_preservation_met"] = pd.to_numeric(candidates["sharpe"], errors="coerce") >= baseline_sharpe
    candidates["all_met"] = (
        candidates["coverage_met"]
        & candidates["spread_met"]
        & candidates["turnover_reduction_met"]
        & candidates["sharpe_preservation_met"]
    )

    feasible = candidates[candidates["all_met"]].copy()
    if feasible.empty:
        # Fallback: highest Sharpe among ablations if no configuration meets all gates.
        best = candidates.sort_values("sharpe", ascending=False, na_position="last").iloc[0]
    else:
        best = feasible.sort_values("sharpe", ascending=False, na_position="last").iloc[0]

    checks = {
        "coverage_met": bool(best["coverage_met"]),
        "spread_met": bool(best["spread_met"]),
        "turnover_reduction_met": bool(best["turnover_reduction_met"]),
        "sharpe_preservation_met": bool(best["sharpe_preservation_met"]),
        "all_met": bool(best["all_met"]),
    }
    return str(best["config_id"]), checks


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 18 Day 5: Scorecard ablation matrix report")
    p.add_argument("--input-features", default=str(DEFAULT_FEATURES_PATH))
    p.add_argument("--input-prices", default=None, help="Optional prices parquet override. Defaults to prices_tri if present.")
    p.add_argument("--start-date", default="2015-01-01")
    p.add_argument("--end-date", default="2024-12-31")
    p.add_argument("--cost-bps", type=float, default=5.0)
    p.add_argument("--top-quantile", type=float, default=0.10, help="Top score quantile used for long-only simulation.")
    p.add_argument(
        "--max-matrix-cells",
        type=int,
        default=25_000_000,
        help="Safety limit for dense date x permno matrices used by simulation.",
    )
    p.add_argument(
        "--allow-missing-returns",
        action="store_true",
        help="If set, missing active return cells are imputed to zero instead of failing fast.",
    )
    p.add_argument("--target-coverage", type=float, default=0.95)
    p.add_argument("--target-spread", type=float, default=2.0)
    p.add_argument("--target-turnover-reduction", type=float, default=0.20)
    p.add_argument("--output-metrics-csv", default=str(DEFAULT_OUTPUT_METRICS))
    p.add_argument("--output-deltas-csv", default=str(DEFAULT_OUTPUT_DELTAS))
    p.add_argument("--output-summary-json", default=str(DEFAULT_OUTPUT_SUMMARY))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    start = _to_ts(args.start_date)
    end = _to_ts(args.end_date)
    if start is not None and end is not None and end < start:
        raise ValueError(f"end-date {end.date()} is earlier than start-date {start.date()}")

    if not (0.0 < float(args.top_quantile) < 1.0):
        raise ValueError("--top-quantile must be in (0, 1)")

    features_path = _resolve_path(args.input_features, DEFAULT_FEATURES_PATH)
    default_prices = DEFAULT_PRICES_TRI_PATH if DEFAULT_PRICES_TRI_PATH.exists() else DEFAULT_PRICES_PATH
    prices_path = _resolve_path(args.input_prices, default_prices)
    if not prices_path.exists():
        raise FileNotFoundError(f"Returns artifact not found: {prices_path}")
    output_metrics = _resolve_path(args.output_metrics_csv, DEFAULT_OUTPUT_METRICS)
    output_deltas = _resolve_path(args.output_deltas_csv, DEFAULT_OUTPUT_DELTAS)
    output_summary = _resolve_path(args.output_summary_json, DEFAULT_OUTPUT_SUMMARY)

    configs = build_ablation_configs()
    all_candidates = sorted({c for cfg in configs for spec in cfg.factor_specs for c in spec.candidate_columns})
    features = _load_features_subset(
        features_path=features_path,
        factor_columns=all_candidates,
        start_date=start,
        end_date=end,
    )
    if features.empty:
        empty = pd.DataFrame(columns=[
            "config_id",
            "description",
            "scoring_method",
            "factor_count",
            "coverage",
            "factor_balance_max_share",
            "factor_balance_min_share",
            "adjacent_rank_correlation",
            "quartile_spread_sigma",
            "sharpe",
            "cagr",
            "max_dd",
            "ulcer",
            "turnover_annual",
            "turnover_total",
            "avg_positions",
            "n_rows",
            "n_dates",
            "missing_factor_families",
        ])
        _atomic_csv_write(empty, output_metrics)
        _atomic_csv_write(empty, output_deltas)
        _atomic_json_write(
            {
                "status": "no_data",
                "reason": "No feature rows found for requested window.",
                "artifacts": {
                    "metrics_csv": str(output_metrics),
                    "deltas_csv": str(output_deltas),
                },
            },
            output_summary,
        )
        print("No feature rows found; wrote empty Day 5 artifacts.")
        return 2

    permnos = sorted(pd.to_numeric(features["permno"], errors="coerce").dropna().astype(int).unique().tolist())
    returns = _load_returns_subset(prices_path=prices_path, permnos=permnos, start_date=start, end_date=end)
    if returns.empty:
        empty = pd.DataFrame(columns=[
            "config_id",
            "description",
            "scoring_method",
            "factor_count",
            "coverage",
            "factor_balance_max_share",
            "factor_balance_min_share",
            "adjacent_rank_correlation",
            "quartile_spread_sigma",
            "sharpe",
            "cagr",
            "max_dd",
            "ulcer",
            "turnover_annual",
            "turnover_total",
            "avg_positions",
            "n_rows",
            "n_dates",
            "missing_factor_families",
        ])
        _atomic_csv_write(empty, output_metrics)
        _atomic_csv_write(empty, output_deltas)
        _atomic_json_write(
            {
                "status": "no_data",
                "reason": "No return rows found for selected universe/window.",
                "artifacts": {
                    "metrics_csv": str(output_metrics),
                    "deltas_csv": str(output_deltas),
                },
            },
            output_summary,
        )
        print("No return rows found; wrote empty Day 5 artifacts.")
        return 2

    print("=" * 80)
    print("PHASE 18 DAY 5: ABLATION MATRIX")
    print("=" * 80)
    print(f"Features: {features_path}")
    print(f"Returns:  {prices_path}")
    print(f"Window:   {start.strftime('%Y-%m-%d')} -> {end.strftime('%Y-%m-%d')}")
    print(f"Configs:  {len(configs)}")

    rows: list[dict[str, Any]] = []
    for i, cfg in enumerate(configs, start=1):
        print(f"[{i}/{len(configs)}] {cfg.config_id} ({cfg.scoring_method})")
        scorecard = CompanyScorecard(
            factor_specs=list(cfg.factor_specs),
            scoring_method=cfg.scoring_method,
        )
        scores, summary = scorecard.compute_scores(features)
        validation = build_validation_table(scores=scores, factor_names=[s.name for s in cfg.factor_specs])
        vmap = _validation_to_map(validation)
        _, perf = _simulate_scores_strategy(
            scores=scores,
            returns_long=returns,
            top_quantile=float(args.top_quantile),
            cost_bps=float(args.cost_bps),
            allow_missing_returns=bool(args.allow_missing_returns),
            max_matrix_cells=int(args.max_matrix_cells),
        )
        rows.append(
            {
                "config_id": cfg.config_id,
                "description": cfg.description,
                "scoring_method": cfg.scoring_method,
                "factor_count": int(len(cfg.factor_specs)),
                "coverage": float(vmap.get("score_coverage", np.nan)),
                "factor_balance_max_share": float(vmap.get("factor_balance_max_share", np.nan)),
                "factor_balance_min_share": float(vmap.get("factor_balance_min_share", np.nan)),
                "adjacent_rank_correlation": float(vmap.get("adjacent_rank_correlation", np.nan)),
                "quartile_spread_sigma": float(vmap.get("quartile_spread_sigma", np.nan)),
                "sharpe": float(perf["sharpe"]),
                "cagr": float(perf["cagr"]),
                "max_dd": float(perf["max_dd"]),
                "ulcer": float(perf["ulcer"]),
                "turnover_annual": float(perf["turnover_annual"]),
                "turnover_total": float(perf["turnover_total"]),
                "avg_positions": float(perf["avg_positions"]),
                "n_rows": int(summary.n_rows),
                "n_dates": int(summary.n_dates),
                "missing_factor_families": ",".join(summary.missing_factor_columns),
            }
        )

    metrics = pd.DataFrame(rows).reset_index(drop=True)
    deltas = _build_deltas(metrics=metrics, baseline_id="BASELINE_DAY4")
    optimal_id, acceptance = _select_optimal(
        deltas=deltas,
        baseline_id="BASELINE_DAY4",
        target_coverage=float(args.target_coverage),
        target_spread=float(args.target_spread),
        target_turnover_reduction=float(args.target_turnover_reduction),
    )

    _atomic_csv_write(metrics, output_metrics)
    _atomic_csv_write(deltas, output_deltas)

    summary_payload = {
        "status": "ok",
        "baseline_id": "BASELINE_DAY4",
        "optimal_id": optimal_id,
        "targets": {
            "coverage": float(args.target_coverage),
            "spread_sigma": float(args.target_spread),
            "turnover_reduction": float(args.target_turnover_reduction),
        },
        "acceptance": acceptance,
        "artifacts": {
            "metrics_csv": str(output_metrics),
            "deltas_csv": str(output_deltas),
        },
    }
    _atomic_json_write(summary_payload, output_summary)

    print("\nAblation metrics:")
    print(metrics[[
        "config_id",
        "coverage",
        "quartile_spread_sigma",
        "sharpe",
        "turnover_annual",
    ]].to_string(index=False))
    print(f"\nOptimal config: {optimal_id}")
    print(f"Acceptance gates: {acceptance}")
    print(f"Metrics CSV: {output_metrics}")
    print(f"Deltas CSV:  {output_deltas}")
    print(f"Summary:     {output_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
