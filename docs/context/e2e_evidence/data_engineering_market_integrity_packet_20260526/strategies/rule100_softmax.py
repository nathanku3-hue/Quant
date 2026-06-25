"""Rule-of-100 softmax v1 sizing helpers.

This module owns the pure sizing math. Runtime/replay scripts are responsible
for building PIT-safe candidate frames and writing artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Rule100SoftmaxConfig:
    """Configuration for the primary Rule100 softmax v1 sizing policy."""

    temperature: float = 1.0
    max_single_name_weight: float = 0.15
    gross_budget_per_name: float = 0.10
    gross_budget_cap: float = 1.0
    factor_weight: float = 0.75
    technical_weight: float = 0.25
    hold_weight: float = 0.0
    age_penalty_weight: float = 0.0
    trim_penalty_weight: float = 0.0


@dataclass(frozen=True)
class KellyAblationConfig:
    """Thin Kelly-style comparator configuration.

    The comparator intentionally uses the same score vector and budget/cap
    harness as softmax. It is not a calibrated per-name Kelly engine.
    """

    odds: float = 1.0
    max_single_name_weight: float = 0.15
    gross_budget_per_name: float = 0.10
    gross_budget_cap: float = 1.0


def _finite_float(value: object, default: float) -> float:
    try:
        parsed = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(parsed):
        return float(default)
    return parsed


def rule100_config_from_max_weight(
    max_weight: object,
    *,
    base: Rule100SoftmaxConfig | None = None,
) -> Rule100SoftmaxConfig:
    """Return the dynamic Rule100 UI/replay config for a user max-weight cap."""

    cfg = base or Rule100SoftmaxConfig()
    cap = _finite_float(max_weight, default=cfg.max_single_name_weight)
    if cap <= 0.0 or cap > 1.0:
        cap = cfg.max_single_name_weight
    return Rule100SoftmaxConfig(
        temperature=cfg.temperature,
        max_single_name_weight=float(cap),
        gross_budget_per_name=float(cap),
        gross_budget_cap=cfg.gross_budget_cap,
        factor_weight=cfg.factor_weight,
        technical_weight=cfg.technical_weight,
        hold_weight=cfg.hold_weight,
        age_penalty_weight=cfg.age_penalty_weight,
        trim_penalty_weight=cfg.trim_penalty_weight,
    )


def stable_softmax(values: Sequence[float] | np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """Return numerically stable softmax probabilities for one score vector."""

    tau = _finite_float(temperature, default=1.0)
    if tau <= 0.0:
        raise ValueError(f"temperature must be > 0, got {temperature!r}")

    x = np.asarray(values, dtype=float).reshape(-1)
    if x.size == 0:
        return np.asarray([], dtype=float)

    scaled = x / tau
    finite_scaled = scaled[np.isfinite(scaled)]
    if finite_scaled.size == 0:
        return np.full(x.shape, 1.0 / float(x.size), dtype=float)

    max_v = float(np.max(finite_scaled))
    exp_v = np.exp(np.clip(scaled - max_v, -60.0, 60.0))
    exp_v = np.where(np.isfinite(exp_v), exp_v, 0.0)
    denom = float(exp_v.sum())
    if not math.isfinite(denom) or denom <= 0.0:
        return np.full(x.shape, 1.0 / float(x.size), dtype=float)
    return exp_v / denom


def _as_weight_series(weights: pd.Series | Sequence[float] | np.ndarray) -> pd.Series:
    if isinstance(weights, pd.Series):
        series = pd.to_numeric(weights, errors="coerce")
        return series.replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(float)
    values = np.asarray(weights, dtype=float).reshape(-1)
    return pd.Series(values, dtype=float).replace([np.inf, -np.inf], np.nan).fillna(0.0)


def cap_and_redistribute(
    weights: pd.Series | Sequence[float] | np.ndarray,
    cap: float,
) -> pd.Series:
    """Cap long-only weights and redistribute remaining budget deterministically."""

    cap_value = _finite_float(cap, default=0.0)
    if cap_value < 0.0:
        raise ValueError(f"cap must be >= 0, got {cap!r}")

    raw = _as_weight_series(weights).clip(lower=0.0)
    if raw.empty or cap_value <= 0.0:
        return pd.Series(0.0, index=raw.index, dtype=float)

    target_total = float(raw.sum())
    if not math.isfinite(target_total) or target_total <= 0.0:
        return pd.Series(0.0, index=raw.index, dtype=float)

    out = pd.Series(0.0, index=raw.index, dtype=float)
    base = raw.copy()
    free = pd.Series(True, index=raw.index, dtype=bool)
    remaining = target_total

    for _ in range(len(raw) + 2):
        free_index = free[free].index
        if remaining <= 1e-12 or len(free_index) == 0:
            break

        free_base = base.loc[free_index].clip(lower=0.0)
        free_total = float(free_base.sum())
        if not math.isfinite(free_total) or free_total <= 0.0:
            candidate = pd.Series(
                remaining / float(len(free_index)),
                index=free_index,
                dtype=float,
            )
        else:
            candidate = remaining * (free_base / free_total)

        over = candidate > (cap_value + 1e-12)
        if not bool(over.any()):
            out.loc[free_index] = candidate
            remaining = 0.0
            break

        capped_index = candidate[over].index
        out.loc[capped_index] = cap_value
        remaining -= cap_value * float(len(capped_index))
        free.loc[capped_index] = False
        base.loc[capped_index] = 0.0

    if remaining > 1e-10:
        room = (cap_value - out).clip(lower=0.0)
        room_total = float(room.sum())
        if room_total > 0.0 and math.isfinite(room_total):
            out = out + remaining * (room / room_total)

    return out.clip(lower=0.0, upper=cap_value)


def gross_budget_for_count(
    n_candidates: int,
    *,
    gross_budget_per_name: float = 0.10,
    gross_budget_cap: float = 1.0,
) -> float:
    """Return `min(gross_budget_cap, gross_budget_per_name * n_candidates)`."""

    try:
        n = int(n_candidates)
    except Exception:
        n = 0
    per_name = max(_finite_float(gross_budget_per_name, default=0.10), 0.0)
    cap = min(max(_finite_float(gross_budget_cap, default=1.0), 0.0), 1.0)
    return float(min(cap, per_name * max(n, 0)))


def _required_column(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        raise ValueError(f"Rule100 sizing candidate frame missing required column: {column}")
    return frame[column]


def _optional_numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return (
        pd.to_numeric(frame[column], errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(default)
        .astype(float)
    )


def score_rule100_candidates(
    candidates: pd.DataFrame,
    config: Rule100SoftmaxConfig | None = None,
) -> pd.DataFrame:
    """Attach the Rule100 softmax v1 score and component columns."""

    cfg = config or Rule100SoftmaxConfig()
    if not isinstance(candidates, pd.DataFrame) or candidates.empty:
        return pd.DataFrame(columns=list(getattr(candidates, "columns", [])) + ["score"])

    out = candidates.copy()
    factor_count = (
        pd.to_numeric(_required_column(out, "factor_positive_count"), errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .clip(lower=0.0)
        .astype(float)
    )
    technical_quality = (
        pd.to_numeric(_required_column(out, "technical_quality"), errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .clip(lower=0.0, upper=1.0)
        .astype(float)
    )
    hold_intact = _optional_numeric(out, "hold_intact", 0.0).clip(lower=0.0, upper=1.0)
    age_penalty = _optional_numeric(out, "age_penalty", 0.0).clip(lower=0.0, upper=1.0)
    trim_penalty = _optional_numeric(out, "trim_penalty", 0.0).clip(lower=0.0, upper=1.0)

    out["factor_component"] = float(cfg.factor_weight) * (factor_count - 3.0).clip(lower=0.0)
    out["technical_component"] = float(cfg.technical_weight) * technical_quality
    out["hold_component"] = float(cfg.hold_weight) * hold_intact
    out["age_penalty_component"] = float(cfg.age_penalty_weight) * age_penalty
    out["trim_penalty_component"] = float(cfg.trim_penalty_weight) * trim_penalty
    out["score"] = (
        out["factor_component"]
        + out["technical_component"]
        + out["hold_component"]
        - out["age_penalty_component"]
        - out["trim_penalty_component"]
    )
    return out


def _stable_order(frame: pd.DataFrame) -> pd.DataFrame:
    sort_cols: list[str] = []
    ascending: list[bool] = []
    if "score" in frame.columns:
        sort_cols.append("score")
        ascending.append(False)
    if "ticker" in frame.columns:
        sort_cols.append("ticker")
        ascending.append(True)
    elif "permno" in frame.columns:
        sort_cols.append("permno")
        ascending.append(True)
    if not sort_cols:
        return frame.copy()
    return frame.sort_values(sort_cols, ascending=ascending, kind="mergesort")


def softmax_v1_weights(
    candidates: pd.DataFrame,
    config: Rule100SoftmaxConfig | None = None,
) -> pd.Series:
    """Build capped softmax v1 weights for one PIT candidate set."""

    cfg = config or Rule100SoftmaxConfig()
    scored = score_rule100_candidates(candidates, cfg)
    if scored.empty:
        return pd.Series(dtype=float)

    ordered = _stable_order(scored)
    budget = gross_budget_for_count(
        len(ordered),
        gross_budget_per_name=cfg.gross_budget_per_name,
        gross_budget_cap=cfg.gross_budget_cap,
    )
    probabilities = stable_softmax(ordered["score"].to_numpy(dtype=float), temperature=cfg.temperature)
    raw = pd.Series(budget * probabilities, index=ordered.index, dtype=float)
    capped = cap_and_redistribute(raw, cap=cfg.max_single_name_weight)
    return capped.reindex(scored.index).fillna(0.0).astype(float)


def kelly_ablation_weights(
    candidates: pd.DataFrame,
    *,
    score_config: Rule100SoftmaxConfig | None = None,
    kelly_config: KellyAblationConfig | None = None,
) -> pd.Series:
    """Build a thin Kelly-style comparator on the same candidate scores."""

    score_cfg = score_config or Rule100SoftmaxConfig()
    kelly_cfg = kelly_config or KellyAblationConfig(
        max_single_name_weight=score_cfg.max_single_name_weight,
        gross_budget_per_name=score_cfg.gross_budget_per_name,
        gross_budget_cap=score_cfg.gross_budget_cap,
    )
    odds = _finite_float(kelly_cfg.odds, default=1.0)
    if odds <= 0.0:
        raise ValueError(f"odds must be > 0, got {kelly_cfg.odds!r}")

    scored = score_rule100_candidates(candidates, score_cfg)
    if scored.empty:
        return pd.Series(dtype=float)

    ordered = _stable_order(scored)
    p = pd.to_numeric(ordered["score"], errors="coerce").fillna(0.0).clip(lower=0.0, upper=1.0)
    raw_fraction = ((odds * p) - (1.0 - p)) / odds
    raw_fraction = raw_fraction.clip(lower=0.0)
    active = raw_fraction > 0.0
    if float(raw_fraction.sum()) <= 0.0 or not bool(active.any()):
        return pd.Series(0.0, index=scored.index, dtype=float)

    budget = gross_budget_for_count(
        len(ordered),
        gross_budget_per_name=kelly_cfg.gross_budget_per_name,
        gross_budget_cap=kelly_cfg.gross_budget_cap,
    )
    active_budget = min(budget, float(kelly_cfg.max_single_name_weight) * float(active.sum()))
    raw = active_budget * raw_fraction.loc[active] / float(raw_fraction.loc[active].sum())
    capped = cap_and_redistribute(raw, cap=kelly_cfg.max_single_name_weight)
    out = pd.Series(0.0, index=ordered.index, dtype=float)
    out.loc[capped.index] = capped
    return out.reindex(scored.index).fillna(0.0).astype(float)


def summarize_weights(weights: pd.Series | Sequence[float] | np.ndarray) -> dict[str, float | int]:
    """Summarize one allocation vector for audit reports."""

    series = _as_weight_series(weights).clip(lower=0.0)
    positive = series[series > 1e-12]
    gross = float(series.sum())
    if gross > 0.0:
        normalized = positive / gross
        herfindahl = float((normalized ** 2.0).sum()) if not normalized.empty else 0.0
    else:
        herfindahl = 0.0
    return {
        "gross_weight": gross,
        "cash_residual": max(0.0, 1.0 - gross),
        "max_weight": float(positive.max()) if not positive.empty else 0.0,
        "nonzero_names": int(len(positive)),
        "herfindahl": herfindahl,
    }


def compare_softmax_and_kelly(
    candidates: pd.DataFrame,
    *,
    softmax_config: Rule100SoftmaxConfig | None = None,
    kelly_config: KellyAblationConfig | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Return a single harness table for softmax v1 and Kelly ablation."""

    softmax_cfg = softmax_config or Rule100SoftmaxConfig()
    kelly_cfg = kelly_config or KellyAblationConfig(
        max_single_name_weight=softmax_cfg.max_single_name_weight,
        gross_budget_per_name=softmax_cfg.gross_budget_per_name,
        gross_budget_cap=softmax_cfg.gross_budget_cap,
    )
    scored = score_rule100_candidates(candidates, softmax_cfg)
    if scored.empty:
        empty = pd.DataFrame(columns=list(scored.columns) + ["softmax_weight", "kelly_weight"])
        return empty, {
            "eligible_count": 0,
            "gross_budget": 0.0,
            "softmax": summarize_weights(pd.Series(dtype=float)),
            "kelly_ablation": summarize_weights(pd.Series(dtype=float)),
            "kelly_comparator_only": True,
        }

    softmax_weights = softmax_v1_weights(scored, softmax_cfg)
    kelly_weights = kelly_ablation_weights(
        scored,
        score_config=softmax_cfg,
        kelly_config=kelly_cfg,
    )
    out = scored.copy()
    out["softmax_weight"] = softmax_weights.reindex(out.index).fillna(0.0)
    out["kelly_weight"] = kelly_weights.reindex(out.index).fillna(0.0)
    out["weight_delta_softmax_minus_kelly"] = out["softmax_weight"] - out["kelly_weight"]
    out = _stable_order(out).reset_index(drop=True)

    budget = gross_budget_for_count(
        len(out),
        gross_budget_per_name=softmax_cfg.gross_budget_per_name,
        gross_budget_cap=softmax_cfg.gross_budget_cap,
    )
    summary = {
        "eligible_count": int(len(out)),
        "gross_budget": float(budget),
        "softmax": summarize_weights(out["softmax_weight"]),
        "kelly_ablation": summarize_weights(out["kelly_weight"]),
        "kelly_comparator_only": True,
        "temperature": float(softmax_cfg.temperature),
        "max_single_name_weight": float(softmax_cfg.max_single_name_weight),
        "kelly_odds": float(kelly_cfg.odds),
    }
    return out, summary
