from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts import phase20_full_backtest as phase20  # noqa: E402
from strategies.company_scorecard import CompanyScorecard  # noqa: E402
from strategies.company_scorecard import build_phase20_conviction_frame  # noqa: E402
from strategies.production_config import PRODUCTION_CONFIG_V1  # noqa: E402


IS_START = "2020-01-01"
IS_END = "2022-12-31"
TARGET_DAY = pd.Timestamp("2021-06-01")
MIN_ELIGIBLE_NAMES = 4
MAX_SINGLE_POSITION = 0.25


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True)


def _stable_softmax(values: np.ndarray, temperature: float) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    if x.size == 0:
        return np.asarray([], dtype=float)
    scaled = x / float(temperature)
    finite_scaled = scaled[np.isfinite(scaled)]
    if finite_scaled.size == 0:
        return np.full(x.shape, 1.0 / float(x.size), dtype=float)
    max_v = float(np.max(finite_scaled))
    exp_v = np.exp(np.clip(scaled - max_v, -60.0, 60.0))
    exp_v = np.where(np.isfinite(exp_v), exp_v, 0.0)
    denom = float(exp_v.sum())
    if not np.isfinite(denom) or denom <= 0.0:
        return np.full(x.shape, 1.0 / float(x.size), dtype=float)
    return exp_v / denom


def _cap_and_redistribute(weights: np.ndarray, cap: float) -> np.ndarray:
    w = np.asarray(weights, dtype=float)
    if w.size == 0:
        return np.asarray([], dtype=float)
    total = float(np.nansum(w))
    if not np.isfinite(total) or total <= 0.0:
        return np.zeros_like(w, dtype=float)
    cap_v = float(max(cap, 0.0))
    if cap_v <= 0.0:
        return np.zeros_like(w, dtype=float)

    out = np.zeros_like(w, dtype=float)
    free_mask = np.ones(w.shape[0], dtype=bool)
    remaining = total
    base = np.where(np.isfinite(w) & (w > 0.0), w, 0.0)

    for _ in range(int(w.size) + 2):
        if remaining <= 1e-12 or not free_mask.any():
            break
        free_base = base[free_mask]
        free_sum = float(np.sum(free_base))
        if not np.isfinite(free_sum) or free_sum <= 0.0:
            candidate = np.full(int(free_mask.sum()), remaining / float(max(1, int(free_mask.sum()))), dtype=float)
        else:
            candidate = remaining * (free_base / free_sum)

        over = candidate > (cap_v + 1e-12)
        free_idx = np.where(free_mask)[0]
        if not over.any():
            out[free_idx] = candidate
            remaining = 0.0
            break

        over_idx = free_idx[over]
        out[over_idx] = cap_v
        remaining -= cap_v * float(over_idx.size)
        free_mask[over_idx] = False
        base[over_idx] = 0.0

    if remaining > 1e-10:
        under_idx = np.where(out < (cap_v - 1e-12))[0]
        if under_idx.size > 0:
            room = cap_v - out[under_idx]
            room_sum = float(np.sum(room))
            if room_sum > 0.0 and np.isfinite(room_sum):
                out[under_idx] += remaining * (room / room_sum)

    out = np.clip(out, 0.0, cap_v)
    total_after = float(np.sum(out))
    if total_after > 0.0:
        scale = min(1.0, total / total_after)
        out = out * scale
    return out


def _softmax_with_guards(
    scores: np.ndarray,
    *,
    temperature: float,
    risk_budget: float,
) -> np.ndarray:
    if int(scores.size) < int(MIN_ELIGIBLE_NAMES):
        return np.zeros_like(scores, dtype=float)
    probs = _stable_softmax(scores, temperature=float(temperature))
    raw_w = float(risk_budget) * probs
    return _cap_and_redistribute(raw_w, cap=float(MAX_SINGLE_POSITION))


def main() -> int:
    features_path = phase20.DEFAULT_FEATURES_PATH
    sdm_features_path = phase20.DEFAULT_SDM_FEATURES_PATH
    macro_path = (
        phase20.DEFAULT_MACRO_FEATURES_PATH
        if phase20.DEFAULT_MACRO_FEATURES_PATH.exists()
        else phase20.DEFAULT_MACRO_FALLBACK_PATH
    )
    liquidity_path = phase20.DEFAULT_LIQUIDITY_PATH

    start = pd.Timestamp(IS_START)
    end = pd.Timestamp(IS_END)

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
    features = phase20._load_features_window(
        features_path,
        start,
        end,
        extra_columns=extra_cols,
        sdm_features_path=sdm_features_path,
    )
    features = phase20._apply_option_a_universe_filter(features)
    if features.empty:
        raise RuntimeError("No features loaded for diagnostic window.")

    feature_dates = pd.DatetimeIndex(sorted(features["date"].dropna().unique()))
    regime, _ = phase20._load_regime_states(
        start_date=start,
        end_date=end,
        feature_dates=feature_dates,
        macro_path=macro_path,
        liquidity_path=liquidity_path,
    )

    scorecard = CompanyScorecard(
        factor_specs=list(PRODUCTION_CONFIG_V1.factor_specs),
        scoring_method=PRODUCTION_CONFIG_V1.scoring_method,
    )
    scores, _ = scorecard.compute_scores(features)
    conviction = build_phase20_conviction_frame(
        scores_df=scores,
        features_df=features,
        regime_by_date=regime,
        support_sma_window=200,
        momentum_lookback=60,
    )

    available_dates = pd.DatetimeIndex(sorted(conviction["date"].dropna().unique()))
    if len(available_dates) == 0:
        raise RuntimeError("No conviction dates available for diagnostic.")

    hard_gate_counts = (
        conviction.assign(hard_gate=conviction["mom_ok"].astype(bool) & conviction["support_proximity"].astype(bool))
        .groupby("date", sort=True)["hard_gate"]
        .sum()
    )
    candidate_dates = pd.DatetimeIndex(hard_gate_counts[hard_gate_counts > 4].index)
    if len(candidate_dates) == 0:
        candidate_dates = available_dates

    nearest_idx = int(np.argmin(np.abs(candidate_dates - TARGET_DAY)))
    diag_date = pd.Timestamp(candidate_dates[nearest_idx])

    day = conviction.loc[conviction["date"] == diag_date].copy()
    day = day.sort_values(["conviction_score", "score"], ascending=[False, False])
    day["hard_gate"] = day["mom_ok"].astype(bool) & day["support_proximity"].astype(bool)

    eligible = day.loc[day["hard_gate"], ["ticker", "permno", "conviction_score"]].copy()
    eligible["ticker"] = eligible["ticker"].astype(str)
    eligible = eligible.sort_values(["conviction_score", "ticker"], ascending=[False, True]).reset_index(drop=True)

    tickers = eligible["ticker"].tolist()
    scores_arr = pd.to_numeric(eligible["conviction_score"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    score_pairs = [{"ticker": t, "conviction_score": float(s)} for t, s in zip(tickers, scores_arr, strict=False)]

    regime = str(day["regime"].iloc[0]).upper() if not day.empty else "AMBER"
    cash_map = {"GREEN": 0.20, "AMBER": 0.25, "RED": 0.50}
    cash_pct = float(cash_map.get(regime, 0.25))
    risk_budget = float(np.clip(1.0 - cash_pct, 0.0, 1.0))

    w_t02_arr = _softmax_with_guards(scores_arr, temperature=0.2, risk_budget=risk_budget)
    w_t20_arr = _softmax_with_guards(scores_arr, temperature=2.0, risk_budget=risk_budget)

    w_t02_pairs = [{"ticker": t, "weight": float(w)} for t, w in zip(tickers, w_t02_arr, strict=False)]
    w_t20_pairs = [{"ticker": t, "weight": float(w)} for t, w in zip(tickers, w_t20_arr, strict=False)]

    err_t02 = bool((~np.isfinite(w_t02_arr)).any()) if w_t02_arr.size > 0 else False
    err_t20 = bool((~np.isfinite(w_t20_arr)).any()) if w_t20_arr.size > 0 else False
    err_any = bool(err_t02 or err_t20)

    print("=" * 80)
    print("SOFTMAX SINGLE-DAY DIAGNOSTIC")
    print("=" * 80)
    print(f"Target Date Requested: {TARGET_DAY.date()}")
    print(f"Closest Valid Trading Day: {diag_date.date()}")
    print(f"Day Regime: {regime}")
    print(f"Risk Budget: {risk_budget:.6f}")
    print(f"Eligible Count (mom_ok & support_proximity): {int(len(eligible))}")
    print("")
    print(f"Eligible Universe: {_json(tickers)}")
    print(f"Raw Scores: {_json(score_pairs)}")
    print(f"Softmax T=0.2: {_json(w_t02_pairs)}")
    print(f"Softmax T=2.0: {_json(w_t20_pairs)}")
    print(
        "Error Check (any NaN/Inf): "
        + _json(
            {
                "t_0_2_has_nan_or_inf": err_t02,
                "t_2_0_has_nan_or_inf": err_t20,
                "any_nan_or_inf": err_any,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
