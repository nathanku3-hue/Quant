"""
Phase 15 diagnostic tool for walk-forward failure analysis.

Inputs:
  - data/processed/phase15_walkforward.csv
  - data/processed/phase16_optimizer_results.csv (optional)

Outputs:
  - summary CSV (atomic write)
  - yearly CSV (atomic write)
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DEFAULT_WALKFORWARD_CSV = PROCESSED_DIR / "phase15_walkforward.csv"
DEFAULT_OPTIMIZER_CSV = PROCESSED_DIR / "phase16_optimizer_results.csv"
DEFAULT_OUTPUT_SUMMARY = PROCESSED_DIR / "phase15_failure_diagnostic_summary.csv"
DEFAULT_OUTPUT_YEARLY = PROCESSED_DIR / "phase15_failure_diagnostic_yearly.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose Phase 15 walk-forward failure modes.")
    parser.add_argument("--walkforward-csv", default=str(DEFAULT_WALKFORWARD_CSV))
    parser.add_argument(
        "--optimizer-csv",
        default=str(DEFAULT_OPTIMIZER_CSV),
        help="Optional optimizer results CSV. Diagnostics are skipped if missing.",
    )
    parser.add_argument("--output-summary", default=str(DEFAULT_OUTPUT_SUMMARY))
    parser.add_argument("--output-yearly", default=str(DEFAULT_OUTPUT_YEARLY))
    return parser.parse_args()


def _resolve_path(value: str | None, default_path: Path | None = None) -> Path | None:
    if value is None:
        return default_path
    text = str(value).strip()
    if text == "" or text.lower() in {"none", "null"}:
        return None
    p = Path(text)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


def _atomic_csv_write(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        df.to_csv(temp_path, index=False)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def _numeric_col(df: pd.DataFrame, col: str, fill_value: float | None = None) -> pd.Series:
    if col in df.columns:
        s = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
    else:
        s = pd.Series(np.nan, index=df.index, dtype=float)
    if fill_value is not None:
        s = s.fillna(fill_value)
    return s.astype(float)


def coerce_bool(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if value is None:
        return False
    if isinstance(value, str):
        norm = value.strip().lower()
        if norm in {"", "0", "false", "f", "no", "n", "off"}:
            return False
        if norm in {"1", "true", "t", "yes", "y", "on"}:
            return True
    num = pd.to_numeric(value, errors="coerce")
    if pd.isna(num):
        return False
    return bool(float(num) != 0.0)


def compute_drawdown(equity_curve: pd.Series) -> pd.Series:
    eq = pd.to_numeric(equity_curve, errors="coerce").replace([np.inf, -np.inf], np.nan).ffill()
    if len(eq) == 0:
        return pd.Series(dtype=float)
    peak = eq.cummax().replace(0.0, np.nan)
    dd = (eq / peak) - 1.0
    return dd.astype(float)


def compute_max_drawdown(equity_curve: pd.Series) -> float:
    dd = compute_drawdown(equity_curve)
    return float(dd.min()) if len(dd) else float("nan")


def compute_ulcer_index(equity_curve: pd.Series) -> float:
    dd_pct = compute_drawdown(equity_curve) * 100.0
    dd_sq = (dd_pct.fillna(0.0) ** 2.0).mean()
    return float(np.sqrt(dd_sq))


def compute_sharpe(daily_ret: pd.Series) -> float:
    r = pd.to_numeric(daily_ret, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if len(r) < 2:
        return float("nan")
    sigma = float(r.std())
    if sigma == 0.0:
        return float("nan")
    return float((r.mean() / sigma) * np.sqrt(252.0))


def compute_cagr(equity_curve: pd.Series) -> float:
    eq = pd.to_numeric(equity_curve, errors="coerce").dropna()
    if len(eq) < 2:
        return float("nan")
    start = float(eq.iloc[0])
    end = float(eq.iloc[-1])
    if start <= 0 or end <= 0:
        return float("nan")
    years = max(len(eq) / 252.0, 1e-9)
    return float((end / start) ** (1.0 / years) - 1.0)


def _phase15_series(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    has_ret = "phase15_ret" in df.columns
    has_curve = "phase15_curve" in df.columns
    if not has_ret and not has_curve:
        raise ValueError("Walkforward CSV must include at least one of: phase15_ret, phase15_curve")

    if has_ret:
        ret = _numeric_col(df, "phase15_ret", fill_value=0.0)
    else:
        ret = pd.Series(np.nan, index=df.index, dtype=float)

    if has_curve:
        curve = _numeric_col(df, "phase15_curve", fill_value=None).ffill()
    else:
        curve = pd.Series(np.nan, index=df.index, dtype=float)

    if has_ret and curve.notna().sum() >= 2:
        return ret.astype(float), curve.astype(float)
    if has_ret:
        return ret.astype(float), (1.0 + ret).cumprod().astype(float)
    curve_clean = curve.astype(float)
    ret_from_curve = curve_clean.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return ret_from_curve.astype(float), curve_clean.astype(float)


def _event_count_rate(raw: pd.Series) -> tuple[int, float]:
    s = pd.to_numeric(raw, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    rows = int(len(s))
    count = int((s > 0).sum())
    rate = float(count / rows) if rows > 0 else float("nan")
    return count, rate


def _fmt_pct(value: float) -> str:
    if not np.isfinite(value):
        return "nan"
    return f"{value:.2%}"


def _fmt_num(value: float, digits: int = 4) -> str:
    if not np.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def build_regime_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "governor_state",
                "rows",
                "pct_rows",
                "mean_phase15_ret",
                "sharpe_phase15",
                "mean_num_positions",
                "entry_days",
                "entry_rate",
                "turnover_mean",
                "turnover_median",
            ]
        )

    work = df.copy()
    if "governor_state" in work.columns:
        work["governor_state"] = work["governor_state"].fillna("UNKNOWN").astype(str)
    else:
        work["governor_state"] = "UNKNOWN"

    work["_phase15_ret"] = _numeric_col(work, "phase15_ret", fill_value=0.0)
    work["_num_positions"] = _numeric_col(work, "num_positions", fill_value=0.0)
    work["_entry"] = (_numeric_col(work, "entry_trigger", fill_value=0.0) > 0).astype(int)
    work["_turnover"] = _numeric_col(work, "turnover", fill_value=0.0)

    grouped = work.groupby("governor_state", dropna=False)
    out = grouped.agg(
        rows=("governor_state", "size"),
        mean_phase15_ret=("_phase15_ret", "mean"),
        mean_num_positions=("_num_positions", "mean"),
        entry_days=("_entry", "sum"),
        entry_rate=("_entry", "mean"),
        turnover_mean=("_turnover", "mean"),
        turnover_median=("_turnover", "median"),
    ).reset_index()

    sharpe = grouped["_phase15_ret"].apply(compute_sharpe).reset_index(name="sharpe_phase15")
    out = out.merge(sharpe, on="governor_state", how="left")
    total_rows = max(int(len(work)), 1)
    out["pct_rows"] = pd.to_numeric(out["rows"], errors="coerce").fillna(0.0) / float(total_rows)
    out = out[
        [
            "governor_state",
            "rows",
            "pct_rows",
            "mean_phase15_ret",
            "sharpe_phase15",
            "mean_num_positions",
            "entry_days",
            "entry_rate",
            "turnover_mean",
            "turnover_median",
        ]
    ]
    return out.sort_values("rows", ascending=False).reset_index(drop=True)


def build_yearly_summary(df: pd.DataFrame) -> pd.DataFrame:
    required = {"date"}
    missing = required.difference(set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns for yearly summary: {sorted(missing)}")
    if df.empty:
        return pd.DataFrame(
            columns=[
                "year",
                "rows",
                "cagr",
                "mean_positions",
                "entry_count",
                "entry_rate",
                "turnover_mean",
                "turnover_median",
                "turnover_sum",
            ]
        )

    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if work.empty:
        return pd.DataFrame(
            columns=[
                "year",
                "rows",
                "cagr",
                "mean_positions",
                "entry_count",
                "entry_rate",
                "turnover_mean",
                "turnover_median",
                "turnover_sum",
            ]
        )

    _, phase15_curve = _phase15_series(work)
    work["_phase15_curve"] = phase15_curve
    work["_num_positions"] = _numeric_col(work, "num_positions", fill_value=0.0)
    work["_entry"] = (_numeric_col(work, "entry_trigger", fill_value=0.0) > 0).astype(int)
    work["_turnover"] = _numeric_col(work, "turnover", fill_value=0.0)
    work["year"] = work["date"].dt.year.astype(int)

    rows: list[dict[str, float | int]] = []
    for year, chunk in work.groupby("year", sort=True):
        n = int(len(chunk))
        entry_count = int(chunk["_entry"].sum())
        rows.append(
            {
                "year": int(year),
                "rows": n,
                "cagr": float(compute_cagr(chunk["_phase15_curve"])),
                "mean_positions": float(chunk["_num_positions"].mean()),
                "entry_count": entry_count,
                "entry_rate": float(entry_count / n) if n > 0 else float("nan"),
                "turnover_mean": float(chunk["_turnover"].mean()),
                "turnover_median": float(chunk["_turnover"].median()),
                "turnover_sum": float(chunk["_turnover"].sum()),
            }
        )
    return pd.DataFrame(rows)


def summarize_frontier(optimizer: pd.DataFrame) -> tuple[dict[str, int], pd.DataFrame, pd.DataFrame]:
    if optimizer.empty:
        empty = pd.DataFrame()
        return (
            {
                "optimizer_rows": 0,
                "stable_candidates": 0,
                "stable_candidates_test_cagr_gt_10": 0,
            },
            empty,
            empty,
        )

    work = optimizer.copy()
    if "stability_pass" in work.columns:
        stable_mask = work["stability_pass"].map(coerce_bool)
    else:
        stable_mask = pd.Series(False, index=work.index)

    work["stability_pass_bool"] = stable_mask.astype(bool)
    work["test_cagr"] = pd.to_numeric(work.get("test_cagr", np.nan), errors="coerce")
    work["train_robust_score"] = pd.to_numeric(work.get("train_robust_score", np.nan), errors="coerce")

    stats = {
        "optimizer_rows": int(len(work)),
        "stable_candidates": int(stable_mask.sum()),
        "stable_candidates_test_cagr_gt_10": int((stable_mask & (work["test_cagr"] > 0.10)).sum()),
    }

    keep_cols = [
        "candidate_id",
        "alpha_top_n",
        "hysteresis_exit_rank",
        "adaptive_rsi_percentile",
        "atr_preset",
        "test_cagr",
        "train_robust_score",
        "stability_pass",
        "stability_pass_bool",
        "error",
    ]
    selected_cols = [c for c in keep_cols if c in work.columns]

    top_test = work.sort_values(by=["test_cagr", "train_robust_score"], ascending=[False, False]).head(10)
    top_robust = work.sort_values(by=["train_robust_score", "test_cagr"], ascending=[False, False]).head(10)
    if selected_cols:
        top_test = top_test[selected_cols]
        top_robust = top_robust[selected_cols]

    return stats, top_test.reset_index(drop=True), top_robust.reset_index(drop=True)


def _load_walkforward(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Walkforward CSV not found: {path}")
    df = pd.read_csv(path)
    if "date" not in df.columns:
        raise ValueError(f"Missing `date` column in walkforward CSV: {path}")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    df = df.drop_duplicates(subset=["date"], keep="last")
    return df.reset_index(drop=True)


def main() -> int:
    args = parse_args()
    walkforward_path = _resolve_path(args.walkforward_csv, default_path=DEFAULT_WALKFORWARD_CSV)
    optimizer_path = _resolve_path(args.optimizer_csv, default_path=DEFAULT_OPTIMIZER_CSV)
    output_summary = _resolve_path(args.output_summary, default_path=DEFAULT_OUTPUT_SUMMARY)
    output_yearly = _resolve_path(args.output_yearly, default_path=DEFAULT_OUTPUT_YEARLY)

    if walkforward_path is None or output_summary is None or output_yearly is None:
        raise RuntimeError("Failed to resolve required file paths.")

    walkforward = _load_walkforward(walkforward_path)
    phase15_ret, phase15_curve = _phase15_series(walkforward)

    total_rows = int(len(walkforward))
    date_start = walkforward["date"].min()
    date_end = walkforward["date"].max()

    phase15_cagr = float(compute_cagr(phase15_curve))
    phase15_sharpe = float(compute_sharpe(phase15_ret))
    phase15_max_dd = float(compute_max_drawdown(phase15_curve))
    phase15_ulcer = float(compute_ulcer_index(phase15_curve))

    entry_count, entry_rate = _event_count_rate(walkforward.get("entry_trigger", pd.Series(index=walkforward.index)))
    exit_rank_count, exit_rank_rate = _event_count_rate(walkforward.get("exit_rank", pd.Series(index=walkforward.index)))
    exit_stop_count, exit_stop_rate = _event_count_rate(walkforward.get("exit_stop", pd.Series(index=walkforward.index)))

    num_positions = _numeric_col(walkforward, "num_positions", fill_value=0.0)
    turnover = _numeric_col(walkforward, "turnover", fill_value=0.0)
    avg_num_positions = float(num_positions.mean()) if total_rows > 0 else float("nan")
    pct_days_zero_positions = float((num_positions == 0).mean()) if total_rows > 0 else float("nan")
    pct_days_with_positions = float((num_positions > 0).mean()) if total_rows > 0 else float("nan")
    turnover_mean = float(turnover.mean()) if total_rows > 0 else float("nan")
    turnover_median = float(turnover.median()) if total_rows > 0 else float("nan")
    turnover_p90 = float(turnover.quantile(0.90)) if total_rows > 0 else float("nan")
    turnover_max = float(turnover.max()) if total_rows > 0 else float("nan")
    turnover_positive_days = int((turnover > 0).sum())
    turnover_positive_rate = float(turnover_positive_days / total_rows) if total_rows > 0 else float("nan")
    turnover_sum = float(turnover.sum()) if total_rows > 0 else float("nan")

    enriched = walkforward.copy()
    enriched["phase15_ret"] = phase15_ret
    enriched["phase15_curve"] = phase15_curve
    regime_df = build_regime_summary(enriched)
    yearly_df = build_yearly_summary(enriched)

    summary_rows: list[dict[str, object]] = [
        {
            "section": "overall",
            "total_rows": total_rows,
            "date_start": date_start.strftime("%Y-%m-%d") if pd.notna(date_start) else "",
            "date_end": date_end.strftime("%Y-%m-%d") if pd.notna(date_end) else "",
            "phase15_cagr": phase15_cagr,
            "phase15_sharpe": phase15_sharpe,
            "phase15_max_dd": phase15_max_dd,
            "phase15_ulcer": phase15_ulcer,
            "entry_trigger_count": entry_count,
            "entry_trigger_rate": entry_rate,
            "exit_rank_count": exit_rank_count,
            "exit_rank_rate": exit_rank_rate,
            "exit_stop_count": exit_stop_count,
            "exit_stop_rate": exit_stop_rate,
            "avg_num_positions": avg_num_positions,
            "pct_days_num_positions_eq_0": pct_days_zero_positions,
            "pct_days_num_positions_gt_0": pct_days_with_positions,
            "turnover_mean": turnover_mean,
            "turnover_median": turnover_median,
            "turnover_p90": turnover_p90,
            "turnover_max": turnover_max,
            "turnover_positive_days": turnover_positive_days,
            "turnover_positive_rate": turnover_positive_rate,
            "turnover_sum": turnover_sum,
        }
    ]

    if not regime_df.empty:
        for row in regime_df.to_dict(orient="records"):
            summary_row = {"section": "regime"}
            summary_row.update(row)
            summary_rows.append(summary_row)

    print("\nPhase 15 diagnostic summary")
    print(f"Rows: {total_rows}")
    print(
        "Date span: "
        f"{date_start.strftime('%Y-%m-%d') if pd.notna(date_start) else 'nan'} -> "
        f"{date_end.strftime('%Y-%m-%d') if pd.notna(date_end) else 'nan'}"
    )
    print(
        "Phase15 metrics: "
        f"CAGR={_fmt_pct(phase15_cagr)}, "
        f"Sharpe={_fmt_num(phase15_sharpe, 3)}, "
        f"MaxDD={_fmt_pct(phase15_max_dd)}, "
        f"Ulcer={_fmt_num(phase15_ulcer, 3)}"
    )
    print(
        "Trade proxies: "
        f"entry_trigger={entry_count} ({_fmt_pct(entry_rate)}), "
        f"exit_rank={exit_rank_count} ({_fmt_pct(exit_rank_rate)}), "
        f"exit_stop={exit_stop_count} ({_fmt_pct(exit_stop_rate)})"
    )
    print(
        "Activity/starvation: "
        f"avg_num_positions={_fmt_num(avg_num_positions, 3)}, "
        f"pct_zero={_fmt_pct(pct_days_zero_positions)}, "
        f"pct_with_positions={_fmt_pct(pct_days_with_positions)}"
    )
    print(
        "Turnover: "
        f"mean={_fmt_num(turnover_mean, 4)}, "
        f"median={_fmt_num(turnover_median, 4)}, "
        f"p90={_fmt_num(turnover_p90, 4)}, "
        f"max={_fmt_num(turnover_max, 4)}, "
        f"positive_days={turnover_positive_days} ({_fmt_pct(turnover_positive_rate)})"
    )

    print("\nRegime split stats")
    if regime_df.empty:
        print("No regime rows available.")
    else:
        print(
            regime_df.to_string(
                index=False,
                formatters={
                    "pct_rows": _fmt_pct,
                    "mean_phase15_ret": _fmt_pct,
                    "entry_rate": _fmt_pct,
                    "sharpe_phase15": lambda x: _fmt_num(x, 3),
                    "mean_num_positions": lambda x: _fmt_num(x, 3),
                    "turnover_mean": lambda x: _fmt_num(x, 4),
                    "turnover_median": lambda x: _fmt_num(x, 4),
                },
            )
        )

    print("\nYearly diagnostics")
    if yearly_df.empty:
        print("No yearly rows available.")
    else:
        print(
            yearly_df.to_string(
                index=False,
                formatters={
                    "cagr": _fmt_pct,
                    "mean_positions": lambda x: _fmt_num(x, 3),
                    "entry_rate": _fmt_pct,
                    "turnover_mean": lambda x: _fmt_num(x, 4),
                    "turnover_median": lambda x: _fmt_num(x, 4),
                    "turnover_sum": lambda x: _fmt_num(x, 4),
                },
            )
        )

    if optimizer_path is not None and optimizer_path.exists():
        optimizer_df = pd.read_csv(optimizer_path)
        frontier_stats, top_test, top_robust = summarize_frontier(optimizer_df)
        summary_rows.append({"section": "frontier", **frontier_stats})

        print("\nFrontier diagnostics")
        print(f"Stable candidates: {frontier_stats['stable_candidates']}")
        print(f"Stable candidates with test_cagr > 10%: {frontier_stats['stable_candidates_test_cagr_gt_10']}")

        print("\nTop 10 by test_cagr")
        print(top_test.to_string(index=False) if not top_test.empty else "No rows")

        print("\nTop 10 by train_robust_score")
        print(top_robust.to_string(index=False) if not top_robust.empty else "No rows")
    else:
        print(f"\nFrontier diagnostics skipped (optimizer CSV missing): {optimizer_path}")

    summary_df = pd.DataFrame(summary_rows)
    _atomic_csv_write(summary_df, output_summary)
    _atomic_csv_write(yearly_df, output_yearly)

    print(f"\nSummary CSV written: {output_summary}")
    print(f"Yearly CSV written: {output_yearly}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
