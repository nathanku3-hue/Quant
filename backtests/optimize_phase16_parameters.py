"""
Phase 16 optimizer: FR-080 strict walk-forward tuning for Phase 15 alpha strategy.

Outputs:
  - data/processed/phase16_optimizer_results.csv
  - data/processed/phase16_best_params.json
  - data/processed/phase16_oos_summary.csv
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
import importlib.util
import json
import os
import sys
import time
import uuid
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from core import engine
from strategies.alpha_engine import AlphaEngine, AlphaEngineConfig
from strategies.investor_cockpit import InvestorCockpitStrategy


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DEFAULT_FEATURES_PATH = PROCESSED_DIR / "features.parquet"
DEFAULT_LIQUIDITY_PATH = PROCESSED_DIR / "liquidity_features.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_PATCH_PATH = PROCESSED_DIR / "yahoo_patch.parquet"

DEFAULT_RESULTS_PATH = PROCESSED_DIR / "phase16_optimizer_results.csv"
DEFAULT_BEST_PARAMS_PATH = PROCESSED_DIR / "phase16_best_params.json"
DEFAULT_OOS_SUMMARY_PATH = PROCESSED_DIR / "phase16_oos_summary.csv"
DEFAULT_PROGRESS_PATH = PROCESSED_DIR / "phase16_optimizer_progress.json"
DEFAULT_LIVE_RESULTS_PATH = PROCESSED_DIR / "phase16_optimizer_live_results.csv"

DEFAULT_TRAIN_START = "2015-01-01"
DEFAULT_TRAIN_END = "2021-12-31"
DEFAULT_TEST_START = "2022-01-01"
DEFAULT_TEST_END = "2024-12-31"

DEFAULT_ALPHA_TOP_N_GRID = "10,20"
DEFAULT_HYSTERESIS_EXIT_GRID = "20,30"
DEFAULT_ADAPTIVE_RSI_GRID = "0.05,0.10,0.15"
DEFAULT_ATR_PRESET_GRID = "2.0,3.0,4.0,5.0"
DEFAULT_ENTRY_LOGIC_GRID = "dip,breakout,combined"
DEFAULT_MIN_TRADES_PER_YEAR = 10.0
DEFAULT_MIN_EXPOSURE_TIME = 0.30

TRADING_DAYS_PER_YEAR = 252.0
ACTIVITY_EPSILON = 1e-12

_WORKER_STATE: dict[str, object] = {}

REQUIRED_SUMMARY_FIELDS = [
    "train_start",
    "train_end",
    "test_start",
    "test_end",
    "entry_logic",
    "alpha_top_n",
    "hysteresis_exit_rank",
    "adaptive_rsi_percentile",
    "atr_preset",
    "atr_mult_low_vol",
    "atr_mult_mid_vol",
    "atr_mult_high_vol",
    "train_cagr",
    "train_sharpe",
    "train_max_dd",
    "train_ulcer",
    "test_cagr",
    "test_sharpe",
    "test_max_dd",
    "test_ulcer",
    "train_robust_score",
    "test_robust_score",
    "sharpe_degradation",
    "stability_pass",
    "exposure_time",
    "trades_per_year",
    "activity_guard_pass",
    "objective_score",
]


def _resolve_output_path(raw: str | None, default_path: Path) -> Path:
    if raw is None:
        return default_path
    token = str(raw).strip()
    if not token:
        return default_path
    out = Path(token)
    if out.is_absolute():
        return out
    return PROJECT_ROOT / out


def _fmt_duration(seconds: float) -> str:
    if not np.isfinite(seconds) or seconds < 0:
        return "n/a"
    total = int(seconds)
    hh = total // 3600
    mm = (total % 3600) // 60
    ss = total % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def _load_phase15_module():
    path = PROJECT_ROOT / "backtests" / "verify_phase15_alpha_walkforward.py"
    spec = importlib.util.spec_from_file_location("verify_phase15_alpha_walkforward", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _parse_int_grid(raw: str) -> list[int]:
    out: list[int] = []
    seen: set[int] = set()
    for token in str(raw).split(","):
        tok = token.strip()
        if not tok:
            continue
        value = int(float(tok))
        if value not in seen:
            seen.add(value)
            out.append(value)
    if not out:
        raise ValueError(f"Grid is empty: {raw}")
    return out


def _parse_float_grid(raw: str) -> list[float]:
    out: list[float] = []
    seen: set[float] = set()
    for token in str(raw).split(","):
        tok = token.strip()
        if not tok:
            continue
        value = float(tok)
        if value not in seen:
            seen.add(value)
            out.append(value)
    if not out:
        raise ValueError(f"Grid is empty: {raw}")
    return out


def _parse_str_grid(raw: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for token in str(raw).split(","):
        tok = token.strip().lower()
        if not tok:
            continue
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
    if not out:
        raise ValueError(f"Grid is empty: {raw}")
    return out


def atr_schedule_from_preset(preset: float) -> tuple[float, float, float]:
    """
    ATR schedule preset where each base value maps to low/mid/high multipliers.
    Defaults (2.0, 3.0, 4.0) reproduce the current Phase 15 baseline schedule.
    """
    base = float(preset)
    return (base, base + 1.0, base + 2.0)


def build_parameter_grid(
    alpha_top_n_values: list[int],
    hysteresis_exit_values: list[int],
    adaptive_rsi_values: list[float],
    atr_presets: list[float],
    entry_logic_values: list[str] | None = None,
) -> list[dict]:
    allowed_entry_logic = set(AlphaEngine.ENTRY_LOGIC_SET)
    entry_logic_grid = entry_logic_values or [AlphaEngine.ENTRY_LOGIC_COMBINED]
    normalized_entry_logic: list[str] = []
    seen_entry_logic: set[str] = set()
    for raw_logic in entry_logic_grid:
        logic = str(raw_logic).strip().lower()
        if logic not in allowed_entry_logic:
            raise ValueError(f"Unsupported entry_logic in grid: {raw_logic}")
        if logic not in seen_entry_logic:
            seen_entry_logic.add(logic)
            normalized_entry_logic.append(logic)

    grid: list[dict] = []
    for entry_logic in normalized_entry_logic:
        for top_n in alpha_top_n_values:
            for hysteresis in hysteresis_exit_values:
                if int(hysteresis) < int(top_n):
                    continue
                for rsi_pct in adaptive_rsi_values:
                    for atr_preset in atr_presets:
                        low, mid, high = atr_schedule_from_preset(float(atr_preset))
                        grid.append(
                            {
                                "entry_logic": str(entry_logic),
                                "alpha_top_n": int(top_n),
                                "hysteresis_exit_rank": int(hysteresis),
                                "adaptive_rsi_percentile": float(rsi_pct),
                                "atr_preset": float(atr_preset),
                                "atr_mult_low_vol": float(low),
                                "atr_mult_mid_vol": float(mid),
                                "atr_mult_high_vol": float(high),
                            }
                        )
    return grid


def resolve_worker_count(max_workers: int, total_tasks: int) -> int:
    if int(total_tasks) <= 1:
        return 1
    cpu = int(os.cpu_count() or 1)
    if int(max_workers) <= 0:
        return max(1, min(cpu, int(total_tasks)))
    return max(1, min(int(max_workers), int(total_tasks)))


def should_use_parallel(disable_parallel: bool, worker_count: int, total_tasks: int) -> bool:
    if bool(disable_parallel):
        return False
    return int(worker_count) > 1 and int(total_tasks) > 1


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


def ulcer_adjusted_sharpe(sharpe: float, ulcer: float) -> float:
    if not np.isfinite(sharpe):
        return float("nan")
    ulcer_val = float(ulcer) if np.isfinite(ulcer) and ulcer > 0 else 0.0
    return float(sharpe / (1.0 + (ulcer_val / 10.0)))


def evaluate_stability(
    train_sharpe: float,
    test_sharpe: float,
    max_sharpe_degradation: float,
    min_test_sharpe: float,
) -> tuple[bool, float]:
    if not np.isfinite(train_sharpe) or not np.isfinite(test_sharpe):
        return False, float("inf")
    degradation = float(train_sharpe - test_sharpe)
    stable = bool(degradation <= float(max_sharpe_degradation) and test_sharpe >= float(min_test_sharpe))
    return stable, degradation


def compute_activity_metrics(weights: pd.DataFrame) -> dict[str, float]:
    if not isinstance(weights, pd.DataFrame) or weights.empty:
        return {"exposure_time": float("nan"), "trades_per_year": float("nan")}
    aligned = weights.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    gross_exposure = aligned.abs().sum(axis=1)
    exposure_time = float((gross_exposure > ACTIVITY_EPSILON).mean()) if len(gross_exposure) else float("nan")
    turnover = aligned.diff().abs().sum(axis=1).fillna(0.0)
    change_events = float((turnover > ACTIVITY_EPSILON).sum())
    years = float(len(aligned.index)) / float(TRADING_DAYS_PER_YEAR)
    trades_per_year = float(change_events / years) if years > 0 else float("nan")
    return {"exposure_time": float(exposure_time), "trades_per_year": float(trades_per_year)}


def compute_window_activity_metrics(
    weights: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, float]:
    if not isinstance(weights, pd.DataFrame) or weights.empty:
        return {"exposure_time": float("nan"), "trades_per_year": float("nan")}
    idx = pd.DatetimeIndex(pd.to_datetime(weights.index, errors="coerce"))
    frame = weights.copy()
    frame.index = idx
    frame = frame[~frame.index.isna()]
    if frame.empty:
        return {"exposure_time": float("nan"), "trades_per_year": float("nan")}
    window = frame[(frame.index >= pd.Timestamp(start)) & (frame.index <= pd.Timestamp(end))]
    if window.empty:
        return {"exposure_time": float("nan"), "trades_per_year": float("nan")}

    gross_exposure = window.abs().sum(axis=1)
    exposure_time = float((gross_exposure > ACTIVITY_EPSILON).mean()) if len(window) else float("nan")

    first_dt = window.index[0]
    prior_mask = frame.index < first_dt
    if prior_mask.any():
        prior_dt = frame.index[prior_mask][-1]
        turnover_source = frame[(frame.index >= prior_dt) & (frame.index <= window.index[-1])]
    else:
        turnover_source = window
    turnover = turnover_source.diff().abs().sum(axis=1).fillna(0.0)
    turnover = turnover.reindex(window.index).fillna(0.0)

    change_events = float((turnover > ACTIVITY_EPSILON).sum())
    years = float(len(window.index)) / float(TRADING_DAYS_PER_YEAR)
    trades_per_year = float(change_events / years) if years > 0 else float("nan")
    return {"exposure_time": float(exposure_time), "trades_per_year": float(trades_per_year)}


def evaluate_activity_guards(
    exposure_time: float,
    trades_per_year: float,
    min_exposure_time: float,
    min_trades_per_year: float,
) -> bool:
    if not np.isfinite(exposure_time) or not np.isfinite(trades_per_year):
        return False
    return bool(
        float(exposure_time) > float(min_exposure_time)
        and float(trades_per_year) > float(min_trades_per_year)
    )


def is_candidate_promotable(record: pd.Series | dict | None) -> bool:
    if record is None:
        return False
    if isinstance(record, pd.Series):
        stability_pass = record.get("stability_pass", False)
        activity_guard_pass = record.get("activity_guard_pass", False)
    elif isinstance(record, dict):
        stability_pass = record.get("stability_pass", False)
        activity_guard_pass = record.get("activity_guard_pass", False)
    else:
        return False
    return bool(coerce_bool(stability_pass) and coerce_bool(activity_guard_pass))


def _compute_metrics(mod15, mod13, ret: pd.Series) -> dict[str, float]:
    if ret is None or len(ret) == 0:
        return {"cagr": float("nan"), "sharpe": float("nan"), "max_dd": float("nan"), "ulcer": float("nan")}
    returns = pd.to_numeric(ret, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    curve = (1.0 + returns).cumprod()
    return mod15._metrics(mod13, returns, curve)


def evaluate_candidate(
    params: dict,
    prices_wide: pd.DataFrame,
    returns_wide: pd.DataFrame,
    features: pd.DataFrame,
    context: pd.DataFrame,
    idx: pd.DatetimeIndex,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    cost_bps: float,
    max_sharpe_degradation: float,
    min_test_sharpe: float,
    min_trades_per_year: float,
    min_exposure_time: float,
    mod15,
    mod13,
) -> dict:
    out = dict(params)
    out["error"] = ""
    out["train_start"] = str(train_start.date())
    out["train_end"] = str(train_end.date())
    out["test_start"] = str(test_start.date())
    out["test_end"] = str(test_end.date())
    out["selected_flag"] = False
    out["promoted_flag"] = False

    try:
        entry_logic = str(params.get("entry_logic", AlphaEngine.ENTRY_LOGIC_COMBINED)).strip().lower()
        entry_top_n = int(params["alpha_top_n"])
        hysteresis_exit_rank = int(params["hysteresis_exit_rank"])
        if hysteresis_exit_rank < entry_top_n:
            raise ValueError("hysteresis_exit_rank must be >= alpha_top_n")
        strat = InvestorCockpitStrategy(
            use_alpha_engine=True,
            alpha_top_n=entry_top_n,
            hysteresis_exit_rank=hysteresis_exit_rank,
            alpha_entry_logic=entry_logic,
            ratchet_stops=True,
        )
        # Keep rank pool depth at hysteresis_exit_rank so hold-buffer exits
        # can evaluate names outside entry_top_n.
        strat.alpha_engine = AlphaEngine(
            AlphaEngineConfig(
                top_n=hysteresis_exit_rank,
                use_adaptive_rsi=True,
                adaptive_rsi_percentile=float(params["adaptive_rsi_percentile"]),
                entry_logic=entry_logic,
                atr_mult_low_vol=float(params["atr_mult_low_vol"]),
                atr_mult_mid_vol=float(params["atr_mult_mid_vol"]),
                atr_mult_high_vol=float(params["atr_mult_high_vol"]),
            )
        )

        weights, _, _ = strat.generate_weights(
            prices=prices_wide,
            fundamentals={"feature_history": features},
            macro=context,
        )
        activity_metrics = compute_window_activity_metrics(
            weights=weights,
            start=test_start,
            end=test_end,
        )
        activity_guard_pass = evaluate_activity_guards(
            exposure_time=float(activity_metrics["exposure_time"]),
            trades_per_year=float(activity_metrics["trades_per_year"]),
            min_exposure_time=float(min_exposure_time),
            min_trades_per_year=float(min_trades_per_year),
        )
        sim = engine.run_simulation(
            target_weights=weights,
            returns_df=returns_wide,
            cost_bps=float(cost_bps) / 10000.0,
        )
        net_ret = pd.to_numeric(sim["net_ret"], errors="coerce").reindex(idx).fillna(0.0)

        train_ret = net_ret[(net_ret.index >= train_start) & (net_ret.index <= train_end)]
        test_ret = net_ret[(net_ret.index >= test_start) & (net_ret.index <= test_end)]

        train_metrics = _compute_metrics(mod15=mod15, mod13=mod13, ret=train_ret)
        test_metrics = _compute_metrics(mod15=mod15, mod13=mod13, ret=test_ret)

        train_robust = ulcer_adjusted_sharpe(train_metrics["sharpe"], train_metrics["ulcer"])
        test_robust = ulcer_adjusted_sharpe(test_metrics["sharpe"], test_metrics["ulcer"])
        stability_pass, degradation = evaluate_stability(
            train_sharpe=float(train_metrics["sharpe"]),
            test_sharpe=float(test_metrics["sharpe"]),
            max_sharpe_degradation=float(max_sharpe_degradation),
            min_test_sharpe=float(min_test_sharpe),
        )

        out.update(
            {
                "train_cagr": float(train_metrics["cagr"]),
                "train_sharpe": float(train_metrics["sharpe"]),
                "train_max_dd": float(train_metrics["max_dd"]),
                "train_ulcer": float(train_metrics["ulcer"]),
                "test_cagr": float(test_metrics["cagr"]),
                "test_sharpe": float(test_metrics["sharpe"]),
                "test_max_dd": float(test_metrics["max_dd"]),
                "test_ulcer": float(test_metrics["ulcer"]),
                "train_robust_score": float(train_robust),
                "test_robust_score": float(test_robust),
                "objective_score": float(train_robust),
                "sharpe_degradation": float(degradation),
                "stability_pass": bool(stability_pass),
                "exposure_time": float(activity_metrics["exposure_time"]),
                "trades_per_year": float(activity_metrics["trades_per_year"]),
                "activity_guard_pass": bool(activity_guard_pass),
                "min_trades_per_year_guard": float(min_trades_per_year),
                "min_exposure_time_guard": float(min_exposure_time),
                "rsi_entry_percentile": float(params["adaptive_rsi_percentile"]),
                "atr_multiplier": float(params["atr_preset"]),
            }
        )
    except Exception as exc:
        out.update(
            {
                "train_cagr": float("nan"),
                "train_sharpe": float("nan"),
                "train_max_dd": float("nan"),
                "train_ulcer": float("nan"),
                "test_cagr": float("nan"),
                "test_sharpe": float("nan"),
                "test_max_dd": float("nan"),
                "test_ulcer": float("nan"),
                "train_robust_score": float("nan"),
                "test_robust_score": float("nan"),
                "objective_score": float("nan"),
                "sharpe_degradation": float("inf"),
                "stability_pass": False,
                "exposure_time": float("nan"),
                "trades_per_year": float("nan"),
                "activity_guard_pass": False,
                "min_trades_per_year_guard": float(min_trades_per_year),
                "min_exposure_time_guard": float(min_exposure_time),
                "error": str(exc),
                "rsi_entry_percentile": float(params["adaptive_rsi_percentile"]),
                "atr_multiplier": float(params["atr_preset"]),
            }
        )
    return out


def _init_optimizer_worker(state: dict[str, object]):
    """
    Worker initializer for parallel candidate evaluation.
    Loads module helpers once per process and keeps shared data in process-local state.
    """
    global _WORKER_STATE
    _WORKER_STATE = dict(state)
    mod15 = _load_phase15_module()
    _WORKER_STATE["mod15"] = mod15
    _WORKER_STATE["mod13"] = mod15._load_phase13_module()


def _evaluate_candidate_worker(task: tuple[int, int, dict]) -> dict:
    i, total, params = task
    st = _WORKER_STATE
    row = evaluate_candidate(
        params=params,
        prices_wide=st["prices_wide"],
        returns_wide=st["returns_wide"],
        features=st["features"],
        context=st["context"],
        idx=st["idx"],
        train_start=st["train_start"],
        train_end=st["train_end"],
        test_start=st["test_start"],
        test_end=st["test_end"],
        cost_bps=st["cost_bps"],
        max_sharpe_degradation=st["max_sharpe_degradation"],
        min_test_sharpe=st["min_test_sharpe"],
        min_trades_per_year=st["min_trades_per_year"],
        min_exposure_time=st["min_exposure_time"],
        mod15=st["mod15"],
        mod13=st["mod13"],
    )
    row["candidate_id"] = int(i)
    row["total_candidates"] = int(total)
    return row


def select_best_candidate(results: pd.DataFrame) -> tuple[pd.Series | None, bool]:
    if results.empty:
        return None, False

    work = results.copy()
    if "error" not in work.columns:
        work["error"] = ""
    if "objective_score" not in work.columns:
        work["objective_score"] = pd.to_numeric(work.get("train_robust_score", np.nan), errors="coerce")
    if "train_cagr" not in work.columns:
        work["train_cagr"] = np.nan
    if "train_robust_score" not in work.columns:
        work["train_robust_score"] = pd.to_numeric(work.get("objective_score", np.nan), errors="coerce")
    if "train_ulcer" not in work.columns:
        work["train_ulcer"] = np.nan

    objective = pd.to_numeric(work["objective_score"], errors="coerce")
    train_cagr = pd.to_numeric(work["train_cagr"], errors="coerce")
    train_robust = pd.to_numeric(work["train_robust_score"], errors="coerce")
    train_ulcer = pd.to_numeric(work["train_ulcer"], errors="coerce")
    valid_mask = (
        work["error"].fillna("").astype(str).eq("")
        & objective.notna()
        & train_cagr.notna()
        & train_robust.notna()
        & train_ulcer.notna()
        & np.isfinite(objective)
        & np.isfinite(train_cagr)
        & np.isfinite(train_robust)
        & np.isfinite(train_ulcer)
    )

    pool = work[valid_mask].copy()
    if pool.empty:
        return None, False

    if "stability_pass" in pool.columns:
        stable_mask = pool["stability_pass"].map(coerce_bool)
    else:
        stable_mask = pd.Series(False, index=pool.index, dtype=bool)
    if "activity_guard_pass" in pool.columns:
        activity_guard_mask = pool["activity_guard_pass"].map(coerce_bool)
    else:
        activity_guard_mask = pd.Series(False, index=pool.index, dtype=bool)

    promotable_pool = pool[stable_mask & activity_guard_mask].copy()
    used_promotable_pool = not promotable_pool.empty
    rank_pool = promotable_pool if used_promotable_pool else pool

    rank_pool["_objective"] = pd.to_numeric(rank_pool["objective_score"], errors="coerce").fillna(-np.inf)
    rank_pool["_train_cagr"] = pd.to_numeric(rank_pool["train_cagr"], errors="coerce").fillna(-np.inf)
    rank_pool["_train_robust"] = pd.to_numeric(rank_pool["train_robust_score"], errors="coerce").fillna(-np.inf)
    rank_pool["_train_ulcer"] = pd.to_numeric(rank_pool["train_ulcer"], errors="coerce").fillna(np.inf)
    for col in ("entry_logic", "alpha_top_n", "hysteresis_exit_rank", "adaptive_rsi_percentile", "atr_preset"):
        if col not in rank_pool.columns:
            rank_pool[col] = "" if col == "entry_logic" else np.nan
    rank_pool["entry_logic"] = rank_pool["entry_logic"].fillna("").astype(str)

    rank_pool = rank_pool.sort_values(
        by=[
            "_objective",
            "_train_cagr",
            "_train_robust",
            "_train_ulcer",
            "entry_logic",
            "alpha_top_n",
            "hysteresis_exit_rank",
            "adaptive_rsi_percentile",
            "atr_preset",
        ],
        ascending=[False, False, False, True, True, True, True, True, True],
        kind="mergesort",
    )
    best = rank_pool.iloc[0].copy()
    return best.drop(labels=["_objective", "_train_cagr", "_train_robust", "_train_ulcer"], errors="ignore"), used_promotable_pool


def build_oos_summary(
    best_row: pd.Series | None,
    args: argparse.Namespace,
    total_candidates: int,
    stable_candidates: int,
    activity_guard_candidates: int,
    promotable_candidates: int,
    selection_pool: str,
) -> dict:
    summary = {
        "train_start": str(args.train_start),
        "train_end": str(args.train_end),
        "test_start": str(args.test_start),
        "test_end": str(args.test_end),
        "entry_logic": "",
        "alpha_top_n": np.nan,
        "hysteresis_exit_rank": np.nan,
        "adaptive_rsi_percentile": np.nan,
        "atr_preset": np.nan,
        "atr_mult_low_vol": np.nan,
        "atr_mult_mid_vol": np.nan,
        "atr_mult_high_vol": np.nan,
        "train_cagr": np.nan,
        "train_sharpe": np.nan,
        "train_max_dd": np.nan,
        "train_ulcer": np.nan,
        "test_cagr": np.nan,
        "test_sharpe": np.nan,
        "test_max_dd": np.nan,
        "test_ulcer": np.nan,
        "train_robust_score": np.nan,
        "test_robust_score": np.nan,
        "sharpe_degradation": np.nan,
        "stability_pass": False,
        "exposure_time": np.nan,
        "trades_per_year": np.nan,
        "activity_guard_pass": False,
        "objective_score": np.nan,
        "total_candidates": int(total_candidates),
        "stable_candidates": int(stable_candidates),
        "activity_guard_candidates": int(activity_guard_candidates),
        "promotable_candidates": int(promotable_candidates),
        "selection_pool": str(selection_pool),
        "strict_mode": bool(args.strict),
        "max_sharpe_degradation": float(args.max_sharpe_degradation),
        "min_test_sharpe": float(args.min_test_sharpe),
        "min_trades_per_year_guard": float(args.min_trades_per_year),
        "min_exposure_time_guard": float(args.min_exposure_time),
    }
    if best_row is not None:
        for key in REQUIRED_SUMMARY_FIELDS:
            if key in {"train_start", "train_end", "test_start", "test_end"}:
                continue
            if key in best_row.index:
                summary[key] = best_row[key]
    return summary


def _atomic_json_write(payload: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def _atomic_csv_write(mod15, df: pd.DataFrame, path: Path):
    if hasattr(mod15, "_atomic_csv_write"):
        mod15._atomic_csv_write(df, path)
        return
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


def _is_pid_alive(pid: int) -> bool:
    if int(pid) <= 0:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _read_lock_meta(lock_path: Path) -> dict | None:
    try:
        raw = lock_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not raw:
        return None
    try:
        meta = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return meta if isinstance(meta, dict) else None


@contextmanager
def _exclusive_lock(
    lock_path: Path,
    stale_seconds: int = 3 * 3600,
    wait_seconds: int = 0,
    poll_seconds: float = 0.5,
):
    """
    Process-level lock to keep multi-file FR-080 outputs consistent.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = None
    lock_token = f"{os.getpid()}:{uuid.uuid4().hex}:{int(time.time())}"
    deadline = time.time() + max(0, int(wait_seconds))
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            lock_meta = json.dumps({"pid": os.getpid(), "ts": int(time.time()), "token": lock_token})
            os.write(fd, lock_meta.encode("utf-8", errors="ignore"))
            break
        except FileExistsError:
            stale = False
            try:
                age = time.time() - float(lock_path.stat().st_mtime)
                stale = age > float(max(0, int(stale_seconds)))
            except OSError:
                stale = False
            meta = _read_lock_meta(lock_path)
            holder_pid = int(meta.get("pid")) if isinstance(meta, dict) and meta.get("pid") is not None else -1
            holder_alive = _is_pid_alive(holder_pid) if holder_pid > 0 else False
            can_reclaim = stale and (not holder_alive)
            if can_reclaim:
                try:
                    lock_path.unlink()
                    continue
                except OSError:
                    pass
            if int(wait_seconds) > 0 and time.time() < deadline:
                time.sleep(max(0.05, float(poll_seconds)))
                continue
            raise RuntimeError(f"Optimizer lock exists: {lock_path}. Another FR-080 run may be active.")
    try:
        yield
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
            if lock_path.exists():
                meta = _read_lock_meta(lock_path)
                token = meta.get("token") if isinstance(meta, dict) else None
                if token == lock_token:
                    try:
                        lock_path.unlink()
                    except OSError:
                        pass


def _commit_artifact_bundle(stage_to_target: list[tuple[Path, Path]], run_tag: str):
    """
    Best-effort bundle commit:
    - Backup existing targets.
    - Promote stage files to canonical targets.
    - Roll back to backups on failure.
    """
    backups: list[tuple[Path, Path]] = []
    promoted: list[Path] = []
    commit_ok = False
    rollback_ok = True
    caught_exc: Exception | None = None
    try:
        for _, target in stage_to_target:
            if target.exists():
                backup = target.with_suffix(target.suffix + f".{run_tag}.bak")
                os.replace(target, backup)
                backups.append((target, backup))
        for stage, target in stage_to_target:
            os.replace(stage, target)
            promoted.append(target)
        commit_ok = True
    except Exception as exc:
        caught_exc = exc
        # Revert newly promoted targets with no prior backup.
        for target in promoted:
            if any(t == target for t, _ in backups):
                continue
            if target.exists():
                try:
                    target.unlink()
                except OSError:
                    rollback_ok = False
        # Restore backed-up targets.
        for target, backup in backups:
            if target.exists():
                try:
                    target.unlink()
                except OSError:
                    rollback_ok = False
            if backup.exists():
                try:
                    os.replace(backup, target)
                except OSError:
                    rollback_ok = False
        # Cleanup stage files where possible.
        for stage, _ in stage_to_target:
            if stage.exists():
                try:
                    stage.unlink()
                except OSError:
                    pass
        if not rollback_ok:
            raise RuntimeError(
                "Artifact bundle commit failed and rollback was incomplete; manual recovery may be required."
            ) from caught_exc
        raise
    finally:
        # Remove backups only if commit succeeded fully.
        if commit_ok:
            for _, backup in backups:
                if backup.exists():
                    try:
                        backup.unlink()
                    except OSError:
                        pass


def _load_feature_history_frozen_universe(
    mod15,
    features_path: Path,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    full_start: pd.Timestamp,
    full_end: pd.Timestamp,
    top_n_universe: int,
) -> tuple[pd.DataFrame, list[int]]:
    """
    Freeze universe from train window only, then load full-window feature rows
    for that fixed membership (prevents train/test leakage in universe selection).
    """
    train_hist = mod15._load_feature_history(
        features_path=features_path,
        start=train_start,
        end=train_end,
        top_n=int(top_n_universe),
    )
    if train_hist.empty:
        raise RuntimeError("Train-window feature history is empty; cannot freeze optimization universe.")

    permnos = sorted(set(int(p) for p in train_hist["permno"].tolist()))
    p_list = ",".join(str(int(p)) for p in permnos)
    path_esc = mod15._sql_escape_path(features_path)
    feature_cols = list(InvestorCockpitStrategy.ALPHA_FEATURE_COLUMNS)
    col_expr = ", ".join(feature_cols)
    q = f"""
    SELECT {col_expr}
    FROM '{path_esc}'
    WHERE CAST(date AS DATE) >= DATE '{full_start.strftime('%Y-%m-%d')}'
      AND CAST(date AS DATE) <= DATE '{full_end.strftime('%Y-%m-%d')}'
      AND CAST(permno AS BIGINT) IN ({p_list})
    ORDER BY date, permno
    """
    con = duckdb.connect()
    try:
        out = con.execute(q).df()
    finally:
        con.close()

    if out.empty:
        raise RuntimeError("Frozen-universe feature history is empty for requested optimization window.")
    out["date"] = pd.to_datetime(out["date"], errors="coerce", utc=True).dt.tz_convert(None).dt.normalize()
    out["permno"] = pd.to_numeric(out["permno"], errors="coerce").astype("Int64")
    out = out.dropna(subset=["date", "permno"])
    out["permno"] = out["permno"].astype(int)
    return out.sort_values(["date", "permno"]), permnos


def _json_safe(value):
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if pd.isna(value):
        return None
    return value


def _extract_activity_snapshot(row: pd.Series | None) -> dict | None:
    if row is None:
        return None
    return {
        "exposure_time": _json_safe(row.get("exposure_time", np.nan)),
        "trades_per_year": _json_safe(row.get("trades_per_year", np.nan)),
        "activity_guard_pass": _json_safe(row.get("activity_guard_pass", False)),
        "stability_pass": _json_safe(row.get("stability_pass", False)),
    }


def build_best_params_payload(
    args: argparse.Namespace,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    total_candidates: int,
    stable_candidates: int,
    activity_guard_candidates: int,
    promotable_candidates: int,
    selection_pool: str,
    promoted_row: pd.Series | None,
    train_best_row: pd.Series | None,
) -> dict:
    payload = {
        "train_window": {"start": str(train_start.date()), "end": str(train_end.date())},
        "test_window": {"start": str(test_start.date()), "end": str(test_end.date())},
        "strict_mode": bool(args.strict),
        "max_sharpe_degradation": float(args.max_sharpe_degradation),
        "min_test_sharpe": float(args.min_test_sharpe),
        "min_trades_per_year_guard": float(args.min_trades_per_year),
        "min_exposure_time_guard": float(args.min_exposure_time),
        "total_candidates": int(total_candidates),
        "stable_candidates": int(stable_candidates),
        "activity_guard_candidates": int(activity_guard_candidates),
        "promotable_candidates": int(promotable_candidates),
        "selection_pool": str(selection_pool),
        "selected_activity": None,
        "train_selected_activity": None,
        "selected": None,
        "train_selected": None,
    }
    if promoted_row is not None:
        payload["selected"] = {k: _json_safe(v) for k, v in promoted_row.to_dict().items()}
        payload["selected_activity"] = _extract_activity_snapshot(promoted_row)
    if train_best_row is not None:
        payload["train_selected"] = {k: _json_safe(v) for k, v in train_best_row.to_dict().items()}
        payload["train_selected_activity"] = _extract_activity_snapshot(train_best_row)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 16 FR-080 strict WFO optimizer for Phase 15 alpha strategy")
    parser.add_argument("--train-start", default=DEFAULT_TRAIN_START)
    parser.add_argument("--train-end", default=DEFAULT_TRAIN_END)
    parser.add_argument("--test-start", default=DEFAULT_TEST_START)
    parser.add_argument("--test-end", default=DEFAULT_TEST_END)
    parser.add_argument("--cost-bps", type=float, default=5.0)
    parser.add_argument("--top-n-universe", type=int, default=300)
    parser.add_argument("--alpha-top-n-grid", default=DEFAULT_ALPHA_TOP_N_GRID)
    parser.add_argument("--hysteresis-exit-grid", default=DEFAULT_HYSTERESIS_EXIT_GRID)
    parser.add_argument("--entry-logic-grid", default=DEFAULT_ENTRY_LOGIC_GRID)
    parser.add_argument("--adaptive-rsi-grid", default=DEFAULT_ADAPTIVE_RSI_GRID)
    parser.add_argument("--atr-preset-grid", default=DEFAULT_ATR_PRESET_GRID)
    parser.add_argument("--max-workers", type=int, default=0, help="0=auto (use available cores)")
    parser.add_argument("--chunk-size", type=int, default=1, help="ProcessPool map chunk size")
    parser.add_argument("--disable-parallel", action="store_true", help="Force sequential candidate evaluation")
    parser.add_argument(
        "--progress-interval-seconds",
        type=float,
        default=15.0,
        help="Progress heartbeat interval for console and JSON status file",
    )
    parser.add_argument(
        "--progress-path",
        default=str(DEFAULT_PROGRESS_PATH),
        help="Live progress heartbeat JSON path",
    )
    parser.add_argument(
        "--live-results-path",
        default=str(DEFAULT_LIVE_RESULTS_PATH),
        help="Interim candidate leaderboard CSV path",
    )
    parser.add_argument(
        "--live-results-every",
        type=int,
        default=4,
        help="Write interim results CSV every N completed candidates",
    )
    parser.add_argument(
        "--disable-live-results",
        action="store_true",
        help="Disable interim live-results CSV writes during evaluation",
    )
    parser.add_argument("--lock-stale-seconds", type=int, default=3 * 3600, help="Consider lock stale after this age")
    parser.add_argument("--lock-wait-seconds", type=int, default=0, help="Optional wait for active lock before fail")
    parser.add_argument("--max-sharpe-degradation", type=float, default=0.75)
    parser.add_argument("--min-test-sharpe", type=float, default=0.0)
    parser.add_argument("--min-trades-per-year", type=float, default=DEFAULT_MIN_TRADES_PER_YEAR)
    parser.add_argument("--min-exposure-time", type=float, default=DEFAULT_MIN_EXPOSURE_TIME)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--features-path", default=str(DEFAULT_FEATURES_PATH))
    parser.add_argument("--macro-path", default=None)
    parser.add_argument("--liquidity-path", default=str(DEFAULT_LIQUIDITY_PATH))
    parser.add_argument("--prices-path", default=str(DEFAULT_PRICES_PATH))
    parser.add_argument("--patch-path", default=str(DEFAULT_PATCH_PATH))
    parser.add_argument("--results-path", default=str(DEFAULT_RESULTS_PATH))
    parser.add_argument("--best-params-path", default=str(DEFAULT_BEST_PARAMS_PATH))
    parser.add_argument("--oos-summary-path", default=str(DEFAULT_OOS_SUMMARY_PATH))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mod15 = _load_phase15_module()
    mod13 = mod15._load_phase13_module()

    train_start = mod15._to_ts(args.train_start)
    train_end = mod15._to_ts(args.train_end)
    test_start = mod15._to_ts(args.test_start)
    test_end = mod15._to_ts(args.test_end)
    if any(x is None for x in (train_start, train_end, test_start, test_end)):
        raise ValueError("Invalid split bounds.")
    if train_end < train_start:
        raise ValueError("train-end must be >= train-start.")
    if test_end < test_start:
        raise ValueError("test-end must be >= test-start.")
    if train_end >= test_start:
        raise ValueError("test-start must be strictly after train-end.")
    if float(args.min_trades_per_year) < 0:
        raise ValueError("min-trades-per-year must be >= 0.")
    if float(args.min_exposure_time) < 0.0 or float(args.min_exposure_time) > 1.0:
        raise ValueError("min-exposure-time must be within [0, 1].")

    full_start = min(train_start, test_start)
    full_end = max(train_end, test_end)

    features_path = mod15._resolve_path(args.features_path, default_path=DEFAULT_FEATURES_PATH)
    macro_path = mod15._resolve_path(args.macro_path, default_path=mod15._default_macro_path())
    liquidity_path = mod15._resolve_path(args.liquidity_path, default_path=DEFAULT_LIQUIDITY_PATH)
    prices_path = mod15._resolve_path(args.prices_path, default_path=DEFAULT_PRICES_PATH)
    patch_path = mod15._resolve_path(args.patch_path, default_path=DEFAULT_PATCH_PATH)

    results_path = mod15._resolve_path(args.results_path, default_path=DEFAULT_RESULTS_PATH)
    best_params_path = mod15._resolve_path(args.best_params_path, default_path=DEFAULT_BEST_PARAMS_PATH)
    oos_summary_path = mod15._resolve_path(args.oos_summary_path, default_path=DEFAULT_OOS_SUMMARY_PATH)

    if features_path is None or macro_path is None:
        raise RuntimeError("Failed to resolve required input paths.")
    if results_path is None or best_params_path is None or oos_summary_path is None:
        raise RuntimeError("Failed to resolve output paths.")
    if not features_path.exists() or not features_path.is_file():
        raise FileNotFoundError(f"Missing feature store: {features_path}")
    if not macro_path.exists() or not macro_path.is_file():
        raise FileNotFoundError(f"Missing macro context file: {macro_path}")
    if (prices_path is None or (not prices_path.exists())) and (patch_path is None or (not patch_path.exists())):
        raise FileNotFoundError("At least one of prices-path or patch-path must exist.")
    output_paths = [results_path.resolve(), best_params_path.resolve(), oos_summary_path.resolve()]
    if len(set(output_paths)) != 3:
        raise ValueError("results-path, best-params-path, and oos-summary-path must be distinct.")
    output_dirs = {p.parent for p in output_paths}
    if len(output_dirs) != 1:
        raise ValueError("All FR-080 outputs must share the same directory for bundle-level consistency.")
    if any(p.exists() and p.is_dir() for p in output_paths):
        raise ValueError("FR-080 output paths must be files, not directories.")
    input_candidates = [features_path.resolve(), macro_path.resolve()]
    for maybe_path in (liquidity_path, prices_path, patch_path):
        if maybe_path is not None:
            input_candidates.append(maybe_path.resolve())
    if any(out in set(input_candidates) for out in output_paths):
        raise ValueError("FR-080 outputs must not overwrite input artifacts.")

    macro = mod15._load_frame(macro_path, start=full_start, end=full_end)
    liquidity = mod15._load_frame(liquidity_path, start=full_start, end=full_end) if liquidity_path is not None and liquidity_path.exists() else None
    context = mod15._build_context(macro=macro, liquidity=liquidity)
    if context.empty:
        raise RuntimeError("No macro/liquidity context rows found for selected window.")

    features, permnos = _load_feature_history_frozen_universe(
        mod15=mod15,
        features_path=features_path,
        train_start=train_start,
        train_end=train_end,
        full_start=full_start,
        full_end=full_end,
        top_n_universe=int(args.top_n_universe),
    )
    prices_wide, returns_wide = mod15._load_prices_matrix(
        permnos=permnos,
        prices_path=prices_path,
        patch_path=patch_path,
        start=full_start,
        end=full_end,
    )
    if prices_wide.empty or returns_wide.empty:
        raise RuntimeError("Unable to load alpha universe prices/returns.")

    idx = prices_wide.index.intersection(context.index)
    idx = pd.DatetimeIndex(pd.to_datetime(idx, errors="coerce", utc=True)).tz_convert(None).normalize()
    idx = pd.DatetimeIndex(idx[~idx.isna()].unique()).sort_values()
    if len(idx) == 0:
        raise RuntimeError("No common dates available after aligning features, prices, and context.")

    prices_wide = prices_wide.reindex(idx).sort_index()
    returns_wide = returns_wide.reindex(idx).sort_index().fillna(0.0)
    context = context.reindex(idx).ffill()

    features = features.copy()
    features["date"] = pd.to_datetime(features["date"], errors="coerce", utc=True).dt.tz_convert(None).dt.normalize()
    features["permno"] = pd.to_numeric(features["permno"], errors="coerce").astype("Int64")
    features = features.dropna(subset=["date", "permno"])
    features["permno"] = features["permno"].astype(int)
    features = features[features["date"].isin(idx)].sort_values(["date", "permno"])
    if features.empty:
        raise RuntimeError("Feature history became empty after alignment.")

    train_rows = int(((idx >= train_start) & (idx <= train_end)).sum())
    test_rows = int(((idx >= test_start) & (idx <= test_end)).sum())
    if train_rows == 0:
        raise RuntimeError("Train split has no aligned rows.")
    if test_rows == 0:
        raise RuntimeError("Test split has no aligned rows.")

    alpha_top_n_values = _parse_int_grid(args.alpha_top_n_grid)
    hysteresis_exit_values = _parse_int_grid(args.hysteresis_exit_grid)
    entry_logic_values = _parse_str_grid(args.entry_logic_grid)
    adaptive_rsi_values = _parse_float_grid(args.adaptive_rsi_grid)
    atr_presets = _parse_float_grid(args.atr_preset_grid)
    grid = build_parameter_grid(
        alpha_top_n_values=alpha_top_n_values,
        hysteresis_exit_values=hysteresis_exit_values,
        adaptive_rsi_values=adaptive_rsi_values,
        atr_presets=atr_presets,
        entry_logic_values=entry_logic_values,
    )
    if not grid:
        raise RuntimeError("No parameter combinations after constraint filtering.")

    results: list[dict] = []
    total = len(grid)
    worker_count = resolve_worker_count(max_workers=int(args.max_workers), total_tasks=total)
    use_parallel = should_use_parallel(
        disable_parallel=bool(args.disable_parallel),
        worker_count=worker_count,
        total_tasks=total,
    )
    progress_interval_seconds = max(1.0, float(args.progress_interval_seconds))
    live_results_every = max(1, int(args.live_results_every))
    progress_path = _resolve_output_path(args.progress_path, DEFAULT_PROGRESS_PATH)
    live_results_path = _resolve_output_path(args.live_results_path, DEFAULT_LIVE_RESULTS_PATH)
    print(f"Candidate eval mode: {'parallel' if use_parallel else 'sequential'} (workers={worker_count}, tasks={total})")
    print(f"Live progress JSON: {progress_path}")
    if not bool(args.disable_live_results):
        print(f"Live results CSV: {live_results_path}")
    tasks = [(int(i), int(total), params) for i, params in enumerate(grid, start=1)]
    eval_started_at = time.time()
    next_report_deadline = eval_started_at

    def _progress_stats(rows: list[dict]) -> dict[str, object]:
        stable = 0
        activity = 0
        promotable = 0
        best_obj = float("-inf")
        best_candidate_id = None
        best_entry_logic = ""
        for rec in rows:
            stable_flag = coerce_bool(rec.get("stability_pass", False))
            activity_flag = coerce_bool(rec.get("activity_guard_pass", False))
            if stable_flag:
                stable += 1
            if activity_flag:
                activity += 1
            if stable_flag and activity_flag:
                promotable += 1
            err = str(rec.get("error", "")).strip()
            obj = pd.to_numeric(rec.get("objective_score", np.nan), errors="coerce")
            if err == "" and np.isfinite(obj):
                score = float(obj)
                if score > best_obj:
                    best_obj = score
                    best_candidate_id = int(rec.get("candidate_id")) if rec.get("candidate_id") is not None else None
                    best_entry_logic = str(rec.get("entry_logic", ""))
        return {
            "stable": int(stable),
            "activity": int(activity),
            "promotable": int(promotable),
            "best_objective": float(best_obj) if np.isfinite(best_obj) else float("nan"),
            "best_candidate_id": best_candidate_id,
            "best_entry_logic": best_entry_logic,
        }

    def _write_progress_heartbeat(completed: int, *, force: bool = False, status: str = "running"):
        nonlocal next_report_deadline
        now = time.time()
        if not force and now < next_report_deadline:
            return
        elapsed = max(0.0, now - eval_started_at)
        rate = (float(completed) / elapsed) if elapsed > 0 else 0.0
        remaining = max(0, int(total) - int(completed))
        eta = (remaining / rate) if rate > 0 else float("nan")
        stats = _progress_stats(results)
        pct = (100.0 * float(completed) / float(total)) if total > 0 else 100.0
        heartbeat = {
            "status": str(status),
            "timestamp_utc": pd.Timestamp.utcnow().isoformat(),
            "mode": "parallel" if use_parallel else "sequential",
            "workers": int(worker_count),
            "total_candidates": int(total),
            "completed_candidates": int(completed),
            "percent_complete": float(pct),
            "elapsed_seconds": float(elapsed),
            "eta_seconds": float(eta) if np.isfinite(eta) else None,
            "stable_candidates_so_far": int(stats["stable"]),
            "activity_guard_candidates_so_far": int(stats["activity"]),
            "promotable_candidates_so_far": int(stats["promotable"]),
            "best_objective_so_far": (
                float(stats["best_objective"]) if np.isfinite(pd.to_numeric(stats["best_objective"], errors="coerce")) else None
            ),
            "best_candidate_id_so_far": stats["best_candidate_id"],
            "best_entry_logic_so_far": str(stats["best_entry_logic"]),
            "results_path_target": str(results_path),
            "best_params_path_target": str(best_params_path),
            "oos_summary_path_target": str(oos_summary_path),
        }
        _atomic_json_write(heartbeat, progress_path)
        if results and not bool(args.disable_live_results):
            if force or (int(completed) % int(live_results_every) == 0) or int(completed) == int(total):
                interim_df = pd.DataFrame(results)
                if "candidate_id" in interim_df.columns:
                    interim_df = interim_df.sort_values("candidate_id").reset_index(drop=True)
                _atomic_csv_write(mod15=mod15, df=interim_df, path=live_results_path)
        best_obj = heartbeat["best_objective_so_far"]
        best_obj_str = "n/a" if best_obj is None else f"{float(best_obj):.4f}"
        print(
            "[progress] "
            f"{int(completed)}/{int(total)} ({pct:.1f}%) "
            f"elapsed={_fmt_duration(elapsed)} "
            f"eta={_fmt_duration(float(eta) if np.isfinite(eta) else float('nan'))} "
            f"promotable={int(stats['promotable'])} "
            f"best_obj={best_obj_str} "
            f"best_logic={str(stats['best_entry_logic']) or 'n/a'}",
            flush=True,
        )
        next_report_deadline = now + progress_interval_seconds

    _write_progress_heartbeat(0, force=True, status="running")

    if use_parallel:
        shared_state = {
            "prices_wide": prices_wide,
            "returns_wide": returns_wide,
            "features": features,
            "context": context,
            "idx": idx,
            "train_start": train_start,
            "train_end": train_end,
            "test_start": test_start,
            "test_end": test_end,
            "cost_bps": float(args.cost_bps),
            "max_sharpe_degradation": float(args.max_sharpe_degradation),
            "min_test_sharpe": float(args.min_test_sharpe),
            "min_trades_per_year": float(args.min_trades_per_year),
            "min_exposure_time": float(args.min_exposure_time),
        }
        try:
            with ProcessPoolExecutor(
                max_workers=int(worker_count),
                initializer=_init_optimizer_worker,
                initargs=(shared_state,),
            ) as ex:
                futures = [ex.submit(_evaluate_candidate_worker, t) for t in tasks]
                for future in as_completed(futures):
                    row = future.result()
                    results.append(row)
                    _write_progress_heartbeat(len(results))
        except Exception as exc:
            print(f"WARNING: parallel evaluation failed ({exc}); retrying sequentially.")
            results = []
            use_parallel = False
            _write_progress_heartbeat(0, force=True, status="retry_sequential")
            for i, params in enumerate(grid, start=1):
                row = evaluate_candidate(
                    params=params,
                    prices_wide=prices_wide,
                    returns_wide=returns_wide,
                    features=features,
                    context=context,
                    idx=idx,
                    train_start=train_start,
                    train_end=train_end,
                    test_start=test_start,
                    test_end=test_end,
                    cost_bps=float(args.cost_bps),
                    max_sharpe_degradation=float(args.max_sharpe_degradation),
                    min_test_sharpe=float(args.min_test_sharpe),
                    min_trades_per_year=float(args.min_trades_per_year),
                    min_exposure_time=float(args.min_exposure_time),
                    mod15=mod15,
                    mod13=mod13,
                )
                row["candidate_id"] = int(i)
                row["total_candidates"] = int(total)
                results.append(row)
                _write_progress_heartbeat(len(results))
    else:
        for i, params in enumerate(grid, start=1):
            row = evaluate_candidate(
                params=params,
                prices_wide=prices_wide,
                returns_wide=returns_wide,
                features=features,
                context=context,
                idx=idx,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                cost_bps=float(args.cost_bps),
                max_sharpe_degradation=float(args.max_sharpe_degradation),
                min_test_sharpe=float(args.min_test_sharpe),
                min_trades_per_year=float(args.min_trades_per_year),
                min_exposure_time=float(args.min_exposure_time),
                mod15=mod15,
                mod13=mod13,
            )
            row["candidate_id"] = int(i)
            row["total_candidates"] = int(total)
            results.append(row)
            _write_progress_heartbeat(len(results))

    _write_progress_heartbeat(len(results), force=True, status="evaluated")

    results_df = pd.DataFrame(results)
    if not results_df.empty and "candidate_id" in results_df.columns:
        results_df = results_df.sort_values("candidate_id").reset_index(drop=True)
    if not results_df.empty and "stability_pass" in results_df.columns:
        stable_mask = results_df["stability_pass"].map(coerce_bool)
        stable_candidates = int(stable_mask.sum())
    else:
        stable_mask = pd.Series(False, index=results_df.index, dtype=bool)
        stable_candidates = 0
    if not results_df.empty and "activity_guard_pass" in results_df.columns:
        activity_guard_mask = results_df["activity_guard_pass"].map(coerce_bool)
        activity_guard_candidates = int(activity_guard_mask.sum())
    else:
        activity_guard_mask = pd.Series(False, index=results_df.index, dtype=bool)
        activity_guard_candidates = 0
    promotable_candidates = int((stable_mask & activity_guard_mask).sum()) if not results_df.empty else 0
    selected_row, used_promotable_pool = select_best_candidate(results_df)
    has_train_candidate = selected_row is not None
    train_best_row = selected_row
    promoted_row = None
    selection_pool = "no_valid_candidates"
    if selected_row is not None and not results_df.empty:
        selection_pool = "promotable_train_ranked" if used_promotable_pool else "train_only_rejected_guardrails"
        mask = (
            (results_df["entry_logic"].fillna("").astype(str) == str(selected_row.get("entry_logic", "")))
            &
            (pd.to_numeric(results_df["alpha_top_n"], errors="coerce") == pd.to_numeric(selected_row.get("alpha_top_n"), errors="coerce"))
            & (
                pd.to_numeric(results_df["hysteresis_exit_rank"], errors="coerce")
                == pd.to_numeric(selected_row.get("hysteresis_exit_rank"), errors="coerce")
            )
            & (
                pd.to_numeric(results_df["adaptive_rsi_percentile"], errors="coerce")
                == pd.to_numeric(selected_row.get("adaptive_rsi_percentile"), errors="coerce")
            )
            & (pd.to_numeric(results_df["atr_preset"], errors="coerce") == pd.to_numeric(selected_row.get("atr_preset"), errors="coerce"))
        )
        if mask.any():
            first_idx = results_df.index[mask][0]
            results_df.loc[first_idx, "selected_flag"] = True
            if used_promotable_pool and is_candidate_promotable(results_df.loc[first_idx]):
                results_df.loc[first_idx, "promoted_flag"] = True
                promoted_row = results_df.loc[first_idx].copy()
    summary_row = build_oos_summary(
        best_row=promoted_row,
        args=args,
        total_candidates=len(results_df),
        stable_candidates=stable_candidates,
        activity_guard_candidates=activity_guard_candidates,
        promotable_candidates=promotable_candidates,
        selection_pool=selection_pool,
    )
    payload = build_best_params_payload(
        args=args,
        train_start=train_start,
        train_end=train_end,
        test_start=test_start,
        test_end=test_end,
        total_candidates=len(results_df),
        stable_candidates=stable_candidates,
        activity_guard_candidates=activity_guard_candidates,
        promotable_candidates=promotable_candidates,
        selection_pool=selection_pool,
        promoted_row=promoted_row,
        train_best_row=train_best_row,
    )

    run_tag = str(int(time.time() * 1000))
    stage_results = results_path.with_suffix(results_path.suffix + f".{run_tag}.stage")
    stage_summary = oos_summary_path.with_suffix(oos_summary_path.suffix + f".{run_tag}.stage")
    stage_best = best_params_path.with_suffix(best_params_path.suffix + f".{run_tag}.stage")
    with _exclusive_lock(
        results_path.parent / "phase16_optimizer.lock",
        stale_seconds=int(args.lock_stale_seconds),
        wait_seconds=int(args.lock_wait_seconds),
    ):
        _atomic_csv_write(mod15=mod15, df=results_df, path=stage_results)
        _atomic_csv_write(mod15=mod15, df=pd.DataFrame([summary_row]), path=stage_summary)
        _atomic_json_write(payload=payload, path=stage_best)
        _commit_artifact_bundle(
            stage_to_target=[
                (stage_results, results_path),
                (stage_summary, oos_summary_path),
                (stage_best, best_params_path),
            ],
            run_tag=run_tag,
        )

    if not bool(args.disable_live_results):
        _atomic_csv_write(mod15=mod15, df=results_df, path=live_results_path)

    if args.strict and promoted_row is None:
        print("No candidate passed promotion guardrails (stability + activity).")
        _write_progress_heartbeat(len(results), force=True, status="complete_blocked")
        return 2

    if promoted_row is not None:
        print(
            "Best params: "
            f"entry_logic={str(promoted_row.get('entry_logic', AlphaEngine.ENTRY_LOGIC_COMBINED))}, "
            f"alpha_top_n={int(promoted_row['alpha_top_n'])}, "
            f"hysteresis_exit_rank={int(promoted_row['hysteresis_exit_rank'])}, "
            f"adaptive_rsi_percentile={float(promoted_row['adaptive_rsi_percentile']):.2f}, "
            f"atr_preset={float(promoted_row['atr_preset']):.1f}"
        )
    else:
        if has_train_candidate:
            print("Train-selected candidate failed promotion guardrails; no params promoted.")
        else:
            print("No valid candidate could be selected from train metrics.")
    _write_progress_heartbeat(len(results), force=True, status="complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
