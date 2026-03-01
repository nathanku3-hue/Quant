from __future__ import annotations

import pandas as pd


RESULTS_PATH = "data/processed/phase16_optimizer_results.csv"


def analyze_results() -> int:
    try:
        df = pd.read_csv(RESULTS_PATH)
    except FileNotFoundError:
        print(f"Error: Results file not found: {RESULTS_PATH}")
        return 1

    if df.empty:
        print("Error: Results file is empty.")
        return 1

    if "error" in df.columns:
        df = df[df["error"].fillna("").astype(str).eq("")].copy()
        if df.empty:
            print("Error: No successful candidate rows after filtering runtime errors.")
            return 1

    required = ["entry_logic", "test_sharpe", "test_cagr", "test_max_dd", "train_sharpe", "objective_score"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"Error: Missing required columns: {missing}")
        return 1

    numeric_cols = ["test_sharpe", "test_cagr", "test_max_dd", "train_sharpe", "objective_score"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    print("\n=== Tournament Standings (By Logic) ===")
    summary = (
        df.groupby("entry_logic", dropna=False)
        .agg(
            count=("test_sharpe", "count"),
            mean_test_sharpe=("test_sharpe", "mean"),
            max_test_sharpe=("test_sharpe", "max"),
            mean_test_cagr=("test_cagr", "mean"),
            max_test_cagr=("test_cagr", "max"),
            mean_test_max_dd=("test_max_dd", "mean"),
        )
        .round(4)
        .sort_values(["mean_test_sharpe", "max_test_sharpe"], ascending=False)
    )
    print(summary.to_string())

    print("\n=== Top 5 Configurations (By Test Sharpe) ===")
    top_5 = (
        df.sort_values("test_sharpe", ascending=False)
        .head(5)[
            [
                "entry_logic",
                "atr_preset",
                "alpha_top_n",
                "hysteresis_exit_rank",
                "test_sharpe",
                "test_cagr",
                "test_max_dd",
            ]
        ]
        .copy()
    )
    print(top_5.to_string(index=False))

    print("\n=== The 'Dip' vs 'Breakout' Check ===")
    for logic in sorted(df["entry_logic"].dropna().astype(str).unique().tolist()):
        subset = df[df["entry_logic"].astype(str) == logic]
        total = len(subset)
        pos = int((subset["test_cagr"] > 0.0).sum())
        win_rate = (100.0 * pos / total) if total > 0 else 0.0
        best_cagr = subset["test_cagr"].max()
        print(f"{logic.ljust(10)} | % Sets with Positive Return: {win_rate:5.1f}% | Best CAGR: {best_cagr:7.2%}")

    return 0


if __name__ == "__main__":
    raise SystemExit(analyze_results())
