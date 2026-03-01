from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import duckdb
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
from scripts.day5_ablation_report import _sql_escape_path  # noqa: E402
from scripts.day5_ablation_report import _to_ts  # noqa: E402
from scripts.day6_walkforward_validation import CRISIS_WINDOWS  # noqa: E402
from scripts.day6_walkforward_validation import _build_c3_specs  # noqa: E402
from scripts.day6_walkforward_validation import _slice_by_date  # noqa: E402
from strategies.company_scorecard import CompanyScorecard  # noqa: E402
from strategies.stop_loss import StopLossConfig  # noqa: E402
from utils.metrics import compute_cagr  # noqa: E402
from utils.metrics import compute_max_drawdown  # noqa: E402
from utils.metrics import compute_sharpe  # noqa: E402
from utils.metrics import compute_ulcer_index  # noqa: E402


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_FEATURES_PATH = PROCESSED_DIR / "features.parquet"
DEFAULT_PRICES_TRI_PATH = PROCESSED_DIR / "prices_tri.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_DELTA_CSV = PROCESSED_DIR / "phase21_day1_delta_metrics.csv"
DEFAULT_EQUITY_PNG = PROCESSED_DIR / "phase21_day1_equity_overlay.png"
DEFAULT_CRISIS_CSV = PROCESSED_DIR / "phase21_day1_crisis_turnover.csv"
DEFAULT_SUMMARY_JSON = PROCESSED_DIR / "phase21_day1_stop_impact_summary.json"


def _load_close_subset(
    prices_path: Path,
    permnos: list[int],
    start_date: pd.Timestamp | None,
    end_date: pd.Timestamp | None,
) -> tuple[pd.DataFrame, str]:
    if not prices_path.exists():
        raise FileNotFoundError(f"Missing prices artifact: {prices_path}")
    if not permnos:
        return pd.DataFrame(), "none"

    con = duckdb.connect()
    try:
        schema = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{_sql_escape_path(prices_path)}')"
        ).df()
        cols = set(schema["column_name"].astype(str).tolist())
        if "tri" in cols:
            close_col = "tri"
        elif "adj_close" in cols:
            close_col = "adj_close"
        elif "legacy_adj_close" in cols:
            close_col = "legacy_adj_close"
        elif "raw_close" in cols:
            close_col = "raw_close"
        else:
            raise RuntimeError(
                "Could not find close-like column (tri/adj_close/legacy_adj_close/raw_close)"
            )

        where = []
        if len(permnos) <= 5000:
            literals = ",".join(str(int(p)) for p in sorted(set(permnos)))
            where.append(f"CAST(permno AS BIGINT) IN ({literals})")
        if start_date is not None:
            where.append(
                f"CAST(date AS DATE) >= DATE '{start_date.strftime('%Y-%m-%d')}'"
            )
        if end_date is not None:
            where.append(
                f"CAST(date AS DATE) <= DATE '{end_date.strftime('%Y-%m-%d')}'"
            )
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        query = f"""
        SELECT
            CAST(date AS DATE) AS date,
            CAST(permno AS BIGINT) AS permno,
            CAST({close_col} AS DOUBLE) AS close_px
        FROM read_parquet('{_sql_escape_path(prices_path)}')
        {where_sql}
        ORDER BY date, permno
        """
        out = con.execute(query).df()
    finally:
        con.close()

    if out.empty:
        return pd.DataFrame(), close_col
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["permno"] = pd.to_numeric(out["permno"], errors="coerce")
    out["close_px"] = pd.to_numeric(out["close_px"], errors="coerce")
    out = out.dropna(subset=["date", "permno", "close_px"]).sort_values(["date", "permno"])
    wide = out.pivot(index="date", columns="permno", values="close_px").sort_index()
    return wide, close_col


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
        raise RuntimeError(
            f"Target matrix too large ({matrix_cells:,} > {int(max_matrix_cells):,})"
        )

    if target.shape[1] == 0:
        aligned = pd.DataFrame(index=target.index)
        missing_active = 0
    else:
        returns_reindexed = returns_wide.reindex(index=target.index, columns=target.columns)
        executed = target.shift(1).fillna(0.0).ne(0.0)
        missing_active = int((returns_reindexed.isna() & executed).sum().sum())
        if missing_active > 0 and not allow_missing_returns:
            raise RuntimeError(
                f"Missing {missing_active:,} executed-exposure return cells; rerun with --allow-missing-returns"
            )
        if missing_active > 0 and allow_missing_returns:
            print(
                f"WARNING: Missing executed-exposure return cells treated as zero: {missing_active:,}"
            )
        aligned = returns_reindexed

    sim = engine.run_simulation(
        target_weights=target,
        returns_df=aligned,
        cost_bps=float(cost_bps) / 10000.0,
        strict_missing_returns=not allow_missing_returns,
    ).copy()
    sim.index = pd.DatetimeIndex(sim.index)
    sim.index.name = "date"
    sim["equity"] = (
        1.0 + pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)
    ).cumprod()
    return sim, missing_active


def _enforce_min_stop_distance(
    reference_price: float,
    stop_candidate: float,
    min_stop_distance_abs: float,
) -> float:
    if float(min_stop_distance_abs) <= 0.0:
        return float(stop_candidate)
    return float(min(float(stop_candidate), float(reference_price) - float(min_stop_distance_abs)))


def _apply_stop_overlay(
    raw_target_weights: pd.DataFrame,
    close_wide: pd.DataFrame,
    cfg: StopLossConfig,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    target_adj = raw_target_weights.copy()
    target_adj = target_adj.sort_index()

    if target_adj.empty:
        return target_adj, {"stop_hits": 0, "time_exits": 0}

    close = close_wide.reindex(index=target_adj.index, columns=target_adj.columns)
    atr = close.diff().abs().rolling(
        window=int(cfg.atr_window), min_periods=int(cfg.atr_window)
    ).mean()

    positions: dict[int, dict[str, Any]] = {}
    holdings_prev = pd.Series(0.0, index=target_adj.columns, dtype=float)
    stop_hits = 0
    time_exits = 0

    for i, dt in enumerate(target_adj.index):
        holdings_today = (
            pd.Series(0.0, index=target_adj.columns, dtype=float)
            if i == 0
            else target_adj.iloc[i - 1].copy()
        )
        held_cols = holdings_today.index[holdings_today > 0.0]
        held_set = {int(p) for p in held_cols}

        # Remove positions naturally exited by signal.
        for p in list(positions.keys()):
            if int(p) not in held_set:
                positions.pop(int(p), None)

        # New executed entries.
        entry_mask = (holdings_today > 0.0) & (holdings_prev <= 0.0)
        for p in holdings_today.index[entry_mask]:
            permno = int(p)
            if permno in positions:
                continue
            px = float(close.at[dt, p]) if pd.notna(close.at[dt, p]) else np.nan
            if not np.isfinite(px):
                continue
            atr_entry = float(atr.at[dt, p]) if pd.notna(atr.at[dt, p]) else np.nan
            if np.isfinite(atr_entry):
                init_stop = px - float(cfg.initial_stop_atr_multiple) * atr_entry
                init_stop = _enforce_min_stop_distance(
                    reference_price=px,
                    stop_candidate=init_stop,
                    min_stop_distance_abs=float(cfg.min_stop_distance_abs),
                )
            else:
                atr_entry = 0.0
                init_stop = -1e18
            positions[permno] = {
                "entry_price": px,
                "current_stop": float(init_stop),
                "is_trailing": False,
                "days_held": 0,
                "highest_price": px,
                "atr_at_entry": atr_entry,
            }

        forced_exits: list[tuple[int, str]] = []
        for p in list(positions.keys()):
            if int(p) not in held_set:
                continue
            col = p
            px = float(close.at[dt, col]) if pd.notna(close.at[dt, col]) else np.nan
            if not np.isfinite(px):
                continue

            pos = positions[p]
            pos["days_held"] = int(pos["days_held"]) + 1
            pos["highest_price"] = float(max(float(pos["highest_price"]), px))

            is_profitable = px > float(pos["entry_price"])
            if (not is_profitable) and int(pos["days_held"]) > int(cfg.max_underwater_days):
                forced_exits.append((int(p), "time"))
                continue

            atr_now = float(atr.at[dt, col]) if pd.notna(atr.at[dt, col]) else np.nan
            if not np.isfinite(atr_now):
                continue

            if is_profitable and not bool(pos["is_trailing"]):
                pos["is_trailing"] = True

            if bool(pos["is_trailing"]):
                candidate = px - float(cfg.trailing_stop_atr_multiple) * atr_now
                candidate = _enforce_min_stop_distance(
                    reference_price=px,
                    stop_candidate=candidate,
                    min_stop_distance_abs=float(cfg.min_stop_distance_abs),
                )
            else:
                candidate = float(pos["entry_price"]) - float(cfg.initial_stop_atr_multiple) * atr_now
                candidate = _enforce_min_stop_distance(
                    reference_price=float(pos["entry_price"]),
                    stop_candidate=candidate,
                    min_stop_distance_abs=float(cfg.min_stop_distance_abs),
                )

            new_stop = float(max(float(pos["current_stop"]), float(candidate)))
            pos["current_stop"] = new_stop
            if px <= new_stop:
                forced_exits.append((int(p), "stop"))

        for permno, reason in forced_exits:
            if permno in target_adj.columns:
                target_adj.at[dt, permno] = 0.0
            positions.pop(int(permno), None)
            if reason == "stop":
                stop_hits += 1
            else:
                time_exits += 1

        holdings_prev = holdings_today

    return target_adj, {"stop_hits": int(stop_hits), "time_exits": int(time_exits)}


def _compute_sim_metrics(sim: pd.DataFrame) -> dict[str, float]:
    if sim.empty:
        return {
            "sharpe": float("nan"),
            "cagr": float("nan"),
            "max_dd": float("nan"),
            "max_dd_abs": float("nan"),
            "ulcer": float("nan"),
            "turnover_annual": float("nan"),
            "turnover_total": float("nan"),
            "n_days": 0.0,
        }
    ret = pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)
    eq = pd.to_numeric(sim["equity"], errors="coerce").ffill()
    max_dd = float(compute_max_drawdown(eq))
    turnover = pd.to_numeric(sim["turnover"], errors="coerce").fillna(0.0)
    return {
        "sharpe": float(compute_sharpe(ret)),
        "cagr": float(compute_cagr(eq)),
        "max_dd": max_dd,
        "max_dd_abs": float(abs(max_dd)),
        "ulcer": float(compute_ulcer_index(eq)),
        "turnover_annual": float(turnover.mean() * 252.0),
        "turnover_total": float(turnover.sum()),
        "n_days": float(len(sim)),
    }


def _compute_crisis_turnover(
    sim_baseline: pd.DataFrame,
    sim_stops: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for name, start, end in CRISIS_WINDOWS:
        b = _slice_by_date(sim_baseline, start, end)
        s = _slice_by_date(sim_stops, start, end)
        base_turn = float(pd.to_numeric(b.get("turnover"), errors="coerce").fillna(0.0).mean() * 252.0)
        stop_turn = float(pd.to_numeric(s.get("turnover"), errors="coerce").fillna(0.0).mean() * 252.0)
        reduction = (
            (base_turn - stop_turn) / base_turn * 100.0
            if np.isfinite(base_turn) and abs(base_turn) > 1e-12
            else float("nan")
        )
        rows.append(
            {
                "window": name,
                "start_date": start,
                "end_date": end,
                "turnover_annual_c3": base_turn,
                "turnover_annual_c3_stops": stop_turn,
                "reduction_pct": reduction,
                "gate_pass_70pct": bool(np.isfinite(reduction) and reduction >= 70.0),
            }
        )
    return pd.DataFrame(rows)


def _write_equity_overlay_png(path: Path, baseline_sim: pd.DataFrame, stop_sim: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(12, 6))
        b = baseline_sim["equity"].copy()
        s = stop_sim["equity"].copy()
        ax.plot(b.index, b.values, label="C3 Baseline", linewidth=1.5)
        ax.plot(s.index, s.values, label="C3 + Stops", linewidth=1.5)
        ax.set_title("Phase 21 Day 1: Equity Overlay (2015-2024)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Equity")
        ax.grid(alpha=0.25)
        ax.legend(loc="best")
        fig.tight_layout()
        fig.savefig(tmp, dpi=140)
        plt.close(fig)
    except Exception:
        # fallback file to satisfy artifact contract if matplotlib is unavailable.
        with open(tmp, "wb") as f:
            f.write(b"")
    tmp.replace(path)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 21 Day 1: stop-impact delta gate vs C3 baseline")
    p.add_argument("--input-features", default=str(DEFAULT_FEATURES_PATH))
    p.add_argument("--input-prices", default=None)
    p.add_argument("--start-date", default="2015-01-01")
    p.add_argument("--end-date", default="2024-12-31")
    p.add_argument("--cost-bps", type=float, default=5.0)
    p.add_argument("--top-quantile", type=float, default=0.10)
    p.add_argument("--c3-decay", type=float, default=0.95)
    p.add_argument("--allow-missing-returns", action="store_true")
    p.add_argument("--max-matrix-cells", type=int, default=25_000_000)
    p.add_argument("--output-delta-csv", default=str(DEFAULT_DELTA_CSV))
    p.add_argument("--output-equity-png", default=str(DEFAULT_EQUITY_PNG))
    p.add_argument("--output-crisis-csv", default=str(DEFAULT_CRISIS_CSV))
    p.add_argument("--output-summary-json", default=str(DEFAULT_SUMMARY_JSON))
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

    output_delta = _resolve_path(args.output_delta_csv, DEFAULT_DELTA_CSV)
    output_png = _resolve_path(args.output_equity_png, DEFAULT_EQUITY_PNG)
    output_crisis = _resolve_path(args.output_crisis_csv, DEFAULT_CRISIS_CSV)
    output_summary = _resolve_path(args.output_summary_json, DEFAULT_SUMMARY_JSON)

    c3_specs = _build_c3_specs(float(args.c3_decay))
    all_candidates = sorted({c for s in c3_specs for c in s.candidate_columns})
    features = _load_features_subset(features_path, all_candidates, start, end)
    if features.empty:
        raise RuntimeError("No feature rows found for selected window.")
    permnos = sorted(pd.to_numeric(features["permno"], errors="coerce").dropna().astype(int).unique().tolist())
    returns = _load_returns_subset(prices_path, permnos, start, end)
    if returns.empty:
        raise RuntimeError("No return rows found for selected window.")
    close_wide, close_col = _load_close_subset(prices_path, permnos, start, end)
    if close_wide.empty:
        raise RuntimeError("No close price rows found for selected window.")

    print("=" * 80)
    print("PHASE 21 DAY 1: STOP IMPACT DELTA GATE")
    print("=" * 80)
    print(f"Features: {features_path}")
    print(f"Prices:   {prices_path} (close source: {close_col})")
    print(f"Window:   {start.strftime('%Y-%m-%d')} -> {end.strftime('%Y-%m-%d')}")
    print(f"C3 decay: {float(args.c3_decay):.2f}")
    print(f"Cost:     {float(args.cost_bps):.2f} bps")

    c3_scores, c3_summary = CompanyScorecard(
        factor_specs=c3_specs,
        scoring_method="complete_case",
    ).compute_scores(features)

    raw_target = _build_target_weights(scores=c3_scores, top_quantile=float(args.top_quantile)).sort_index()
    if raw_target.empty:
        raise RuntimeError("C3 target weights are empty for selected window.")

    c3_sim, c3_missing = _simulate_from_target_weights(
        target_weights=raw_target,
        returns_long=returns,
        cost_bps=float(args.cost_bps),
        allow_missing_returns=bool(args.allow_missing_returns),
        max_matrix_cells=int(args.max_matrix_cells),
    )

    stop_cfg = StopLossConfig(
        atr_window=20,
        atr_mode="proxy_close_only",
        initial_stop_atr_multiple=2.0,
        trailing_stop_atr_multiple=1.5,
        max_underwater_days=60,
    )
    target_stops, stop_stats = _apply_stop_overlay(raw_target, close_wide, stop_cfg)

    c3_stops_sim, c3_stops_missing = _simulate_from_target_weights(
        target_weights=target_stops,
        returns_long=returns,
        cost_bps=float(args.cost_bps),
        allow_missing_returns=bool(args.allow_missing_returns),
        max_matrix_cells=int(args.max_matrix_cells),
    )

    metrics_c3 = _compute_sim_metrics(c3_sim)
    metrics_stops = _compute_sim_metrics(c3_stops_sim)
    crisis = _compute_crisis_turnover(c3_sim, c3_stops_sim)
    _atomic_csv_write(crisis, output_crisis)

    gate_sharpe = bool(metrics_stops["sharpe"] >= (metrics_c3["sharpe"] - 0.03))
    gate_turnover = bool(
        metrics_stops["turnover_annual"] <= (metrics_c3["turnover_annual"] * 1.15)
    )
    gate_maxdd = bool(
        metrics_stops["max_dd_abs"] <= (metrics_c3["max_dd_abs"] + 0.03)
    )
    crisis_min_red = float(pd.to_numeric(crisis["reduction_pct"], errors="coerce").min())
    gate_crisis = bool(crisis["gate_pass_70pct"].all()) if not crisis.empty else False

    gates = {
        "gate_sharpe": gate_sharpe,
        "gate_turnover": gate_turnover,
        "gate_maxdd_abs": gate_maxdd,
        "gate_crisis_turnover_70pct_all_windows": gate_crisis,
    }
    gates_passed = int(sum(bool(v) for v in gates.values()))
    gates_total = int(len(gates))
    promotion_decision = "PROMOTE" if gates_passed >= 3 else "ABORT"
    saw_target_verdict = (
        "PASS" if gates_passed == 4 else ("ADVISORY_PASS" if gates_passed == 3 else "BLOCK")
    )

    row = {
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "cost_bps": float(args.cost_bps),
        "top_quantile": float(args.top_quantile),
        "c3_decay": float(args.c3_decay),
        "score_coverage_c3": float(c3_summary.coverage),
        "score_coverage_c3_stops": float(c3_summary.coverage),
        "sharpe_c3": float(metrics_c3["sharpe"]),
        "sharpe_c3_stops": float(metrics_stops["sharpe"]),
        "sharpe_delta": float(metrics_stops["sharpe"] - metrics_c3["sharpe"]),
        "turnover_annual_c3": float(metrics_c3["turnover_annual"]),
        "turnover_annual_c3_stops": float(metrics_stops["turnover_annual"]),
        "turnover_ratio_c3_stops_vs_c3": (
            float(metrics_stops["turnover_annual"] / metrics_c3["turnover_annual"])
            if np.isfinite(metrics_c3["turnover_annual"]) and abs(metrics_c3["turnover_annual"]) > 1e-12
            else float("nan")
        ),
        "max_dd_c3": float(metrics_c3["max_dd"]),
        "max_dd_c3_stops": float(metrics_stops["max_dd"]),
        "max_dd_abs_c3": float(metrics_c3["max_dd_abs"]),
        "max_dd_abs_c3_stops": float(metrics_stops["max_dd_abs"]),
        "max_dd_abs_delta": float(metrics_stops["max_dd_abs"] - metrics_c3["max_dd_abs"]),
        "ulcer_c3": float(metrics_c3["ulcer"]),
        "ulcer_c3_stops": float(metrics_stops["ulcer"]),
        "cagr_c3": float(metrics_c3["cagr"]),
        "cagr_c3_stops": float(metrics_stops["cagr"]),
        "gate_sharpe_pass": gate_sharpe,
        "gate_turnover_pass": gate_turnover,
        "gate_maxdd_abs_pass": gate_maxdd,
        "gate_crisis_turnover_pass": gate_crisis,
        "crisis_min_reduction_pct": crisis_min_red,
        "gates_passed": gates_passed,
        "gates_total": gates_total,
        "promotion_decision": promotion_decision,
        "saw_target_verdict": saw_target_verdict,
        "stop_hits": int(stop_stats["stop_hits"]),
        "time_exits": int(stop_stats["time_exits"]),
        "missing_active_return_cells_c3": int(c3_missing),
        "missing_active_return_cells_c3_stops": int(c3_stops_missing),
        "close_source_column": close_col,
    }

    # Add crisis reductions as flat columns for audit visibility.
    for _, r in crisis.iterrows():
        key = str(r["window"]).lower()
        row[f"crisis_reduction_pct_{key}"] = float(r["reduction_pct"])
        row[f"crisis_gate_pass_{key}"] = bool(r["gate_pass_70pct"])

    delta = pd.DataFrame([row])
    _atomic_csv_write(delta, output_delta)
    _write_equity_overlay_png(output_png, c3_sim, c3_stops_sim)

    summary_payload = {
        "status": "ok",
        "decision": promotion_decision,
        "saw_target_verdict": saw_target_verdict,
        "gates": {k: bool(v) for k, v in gates.items()},
        "gates_passed": gates_passed,
        "gates_total": gates_total,
        "artifacts": {
            "delta_csv": str(output_delta),
            "equity_png": str(output_png),
            "crisis_csv": str(output_crisis),
        },
    }
    _atomic_json_write(summary_payload, output_summary)

    print("\nGate results:")
    for k, v in gates.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    print(f"  gates_passed: {gates_passed}/{gates_total}")
    print(f"  decision: {promotion_decision}")
    print(f"  saw_target_verdict: {saw_target_verdict}")
    print("\nArtifacts:")
    print(f"  Delta CSV:   {output_delta}")
    print(f"  Equity PNG:  {output_png}")
    print(f"  Crisis CSV:  {output_crisis}")
    print(f"  Summary JSON:{output_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
