from __future__ import annotations

import math
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts import phase20_full_backtest as phase20  # noqa: E402


IS_START = "2020-01-01"
IS_END = "2022-12-31"
OOS_START = "2023-01-01"
OOS_END = "2024-12-31"
T_VALUES = [0.2, 0.5, 0.8, 1.0, 1.5, 2.0]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
WFO_DIR = PROCESSED_DIR / "phase23_wfo_temperature"
SUMMARY_PATH = PROCESSED_DIR / "phase23_wfo_temperature_summary.json"


@contextmanager
def _patched_argv(argv: list[str]):
    prior = list(sys.argv)
    sys.argv = argv
    try:
        yield
    finally:
        sys.argv = prior


def _temp_token(value: float) -> str:
    return str(value).replace(".", "p")


def _is_finite_number(value: Any) -> bool:
    try:
        x = float(value)
    except Exception:
        return False
    return bool(math.isfinite(x))


def _run_phase20_for_window(
    *,
    temperature: float,
    start_date: str,
    end_date: str,
    label: str,
) -> dict[str, Any]:
    token = _temp_token(temperature)
    run_dir = WFO_DIR / label
    run_dir.mkdir(parents=True, exist_ok=True)

    out_delta = run_dir / f"{label}_t{token}_delta_vs_c3.csv"
    out_equity = run_dir / f"{label}_t{token}_equity.png"
    out_cash = run_dir / f"{label}_t{token}_cash_allocation.csv"
    out_top20 = run_dir / f"{label}_t{token}_top20_exposure.csv"
    out_summary = run_dir / f"{label}_t{token}_summary.json"
    out_sample = run_dir / f"{label}_t{token}_sample_output.csv"
    out_crisis = run_dir / f"{label}_t{token}_crisis_turnover.csv"

    argv = [
        "phase20_full_backtest.py",
        "--start-date",
        str(start_date),
        "--end-date",
        str(end_date),
        "--option-a-sector-specialist",
        "--allow-missing-returns",
        "--softmax-temperature",
        str(float(temperature)),
        "--output-delta-csv",
        str(out_delta),
        "--output-equity-png",
        str(out_equity),
        "--output-cash-csv",
        str(out_cash),
        "--output-top20-csv",
        str(out_top20),
        "--output-summary-json",
        str(out_summary),
        "--output-sample-csv",
        str(out_sample),
        "--output-crisis-csv",
        str(out_crisis),
    ]

    with _patched_argv(argv):
        exit_code = int(phase20.main())

    if not out_summary.exists():
        raise RuntimeError(f"Missing backtest summary artifact: {out_summary}")

    payload = pd.read_json(out_summary, typ="series").to_dict()
    metrics = dict(payload.get("metrics", {}).get("phase20", {}))
    return {
        "temperature": float(temperature),
        "window": {"start_date": str(start_date), "end_date": str(end_date)},
        "exit_code": int(exit_code),
        "decision": str(payload.get("decision", "")),
        "summary_path": str(out_summary),
        "cagr": float(metrics.get("cagr")) if _is_finite_number(metrics.get("cagr")) else float("nan"),
        "sharpe": float(metrics.get("sharpe")) if _is_finite_number(metrics.get("sharpe")) else float("nan"),
        "max_dd": float(metrics.get("max_dd")) if _is_finite_number(metrics.get("max_dd")) else float("nan"),
    }


def _selection_key(row: dict[str, Any]) -> tuple[float, float, float]:
    sharpe = float(row.get("sharpe", float("nan")))
    cagr = float(row.get("cagr", float("nan")))
    temp = float(row.get("temperature", float("nan")))
    sharpe_key = sharpe if math.isfinite(sharpe) else float("-inf")
    cagr_key = cagr if math.isfinite(cagr) else float("-inf")
    temp_key = -temp if math.isfinite(temp) else float("-inf")
    return sharpe_key, cagr_key, temp_key


def main() -> int:
    WFO_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("PHASE 23 WFO: SOFTMAX TEMPERATURE")
    print("=" * 80)
    print(f"IS Window:  {IS_START} -> {IS_END}")
    print(f"OOS Window: {OOS_START} -> {OOS_END}")
    print(f"Search T:   {T_VALUES}")

    is_results: list[dict[str, Any]] = []
    for t_value in T_VALUES:
        print(f"\n[IS] Running temperature={t_value:.2f}")
        result = _run_phase20_for_window(
            temperature=float(t_value),
            start_date=IS_START,
            end_date=IS_END,
            label="is",
        )
        is_results.append(result)
        print(
            f"[IS] t={t_value:.2f} cagr={result['cagr']:.6f} "
            f"sharpe={result['sharpe']:.6f} max_dd={result['max_dd']:.6f}"
        )

    if not is_results:
        raise RuntimeError("IS run produced no results.")

    winner = max(is_results, key=_selection_key)
    winner_t = float(winner["temperature"])

    print(f"\n[OOS] Running winning temperature={winner_t:.2f}")
    oos_result = _run_phase20_for_window(
        temperature=winner_t,
        start_date=OOS_START,
        end_date=OOS_END,
        label="oos",
    )

    summary = {
        "status": "ok",
        "selection_metric": "max_is_sharpe",
        "search_space": {"temperature_values": [float(v) for v in T_VALUES]},
        "windows": {
            "in_sample": {"start_date": IS_START, "end_date": IS_END},
            "out_of_sample": {"start_date": OOS_START, "end_date": OOS_END},
        },
        "in_sample_results": is_results,
        "winner": {
            "temperature": winner_t,
            "in_sample_metrics": {
                "cagr": float(winner["cagr"]),
                "sharpe": float(winner["sharpe"]),
                "max_dd": float(winner["max_dd"]),
            },
        },
        "out_of_sample_result": oos_result,
        "artifacts_root": str(WFO_DIR),
    }
    phase20._atomic_json_write(summary, SUMMARY_PATH)

    print("\nWFO COMPLETE")
    print(f"Winning T (IS): {winner_t:.2f}")
    print(f"IS (2020-2022) for T={winner_t:.2f}: CAGR={winner['cagr']:.6f}, Sharpe={winner['sharpe']:.6f}")
    print(
        f"OOS (2023-2024) for T={winner_t:.2f}: "
        f"CAGR={oos_result['cagr']:.6f}, Sharpe={oos_result['sharpe']:.6f}, Max Drawdown={oos_result['max_dd']:.6f}"
    )
    print(f"Summary Artifact: {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
