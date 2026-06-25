"""Rule-of-100 softmax v1.1 sizing — approved expert contract.

Formula:
    base_score = 0.50*factor_strength + 0.35*technical_quality + 0.15*hold_intact - 0.10*staleness
    raw_weight = budget * softmax(base_score / tau)
    target_weight = min(0.15, raw_weight) * lifecycle_state_multiplier

Lifecycle multipliers:
    BUY/HOLD = 1.00, TRIM = 0.75, TIGHTEN = 0.50, EXIT = 0.00

Trimmed/tightened capital becomes cash (no redistribution).
Research-only — does NOT replace v1 runtime.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from strategies.rule100_softmax import (
    cap_and_redistribute,
    gross_budget_for_count,
    stable_softmax,
    summarize_weights,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

LIFECYCLE_MULTIPLIERS: dict[str, float] = {
    "BUY": 1.00,
    "HOLD": 1.00,
    "TRIM": 0.75,
    "TIGHTEN": 0.50,
    "EXIT": 0.00,
}

# Approved factor groups
V1_1_FACTOR_GROUPS: dict[str, list[str]] = {
    "demand": ["z_demand"],
    "inventory_supply": ["z_inventory_quality_proxy"],
    "moat_pricing": ["z_moat"],
    "capital_discipline": ["capital_cycle_score", "quality_composite"],
}

# Approved technical sub-groups (each produces a [0,1] quality score)
V1_1_TECHNICAL_GROUPS: dict[str, list[str]] = {
    "momentum": ["resid_mom_60d", "rel_strength_60d"],
    "trend": ["dist_sma20", "trend_veto"],
    "stretch": ["rsi_14d"],
    "vol_liquidity": ["yz_vol_20d", "realized_vol_21d"],
}


@dataclass(frozen=True)
class Rule100SoftmaxV1_1Config:
    """v1.1 scoring weights and harness parameters."""

    factor_strength_weight: float = 0.50
    technical_quality_weight: float = 0.35
    hold_intact_weight: float = 0.15
    staleness_penalty_weight: float = 0.10

    temperature: float = 1.0
    max_single_name_weight: float = 0.15
    gross_budget_per_name: float = 0.10
    gross_budget_cap: float = 1.0

    # Staleness: penalty saturates at this many days
    staleness_saturation_days: float = 120.0


# ---------------------------------------------------------------------------
# Factor strength: mean of per-group cross-sectional percentile ranks
# ---------------------------------------------------------------------------

NEUTRAL_FACTOR_STRENGTH = 0.50


def compute_factor_group_values(
    features: pd.DataFrame,
    factor_groups: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    """Return one numeric signal per approved factor group.

    Groups can list fallback columns, but each group contributes at most one
    value per row so alternate columns cannot double-count the same factor.
    """
    groups = factor_groups or V1_1_FACTOR_GROUPS
    if not isinstance(features, pd.DataFrame) or len(features.index) == 0:
        return pd.DataFrame(index=getattr(features, "index", None))

    grouped: dict[str, pd.Series] = {}
    for name, cols in groups.items():
        combined = pd.Series(np.nan, index=features.index, dtype=float)
        for col in cols:
            if col not in features.columns:
                continue
            vals = pd.to_numeric(features[col], errors="coerce")
            combined = combined.where(combined.notna(), vals)
        grouped[name] = combined
    return pd.DataFrame(grouped, index=features.index)


def compute_factor_group_counts(
    features: pd.DataFrame,
    factor_groups: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    """Count present/positive approved factor groups, not raw columns."""
    group_values = compute_factor_group_values(features, factor_groups)
    if group_values.empty:
        return pd.DataFrame(
            {
                "factor_present_count": pd.Series(0, index=features.index, dtype=int),
                "factor_positive_count": pd.Series(0, index=features.index, dtype=int),
            },
            index=features.index,
        )
    return pd.DataFrame(
        {
            "factor_present_count": group_values.notna().sum(axis=1).astype(int),
            "factor_positive_count": (group_values > 0).sum(axis=1).astype(int),
        },
        index=features.index,
    )

def compute_factor_strength_continuous(
    features: pd.DataFrame,
    factor_groups: dict[str, list[str]] | None = None,
) -> pd.Series:
    """Mean of per-group cross-sectional percentile ranks.

    For each group, take the best available column, rank it within the
    non-null cross-section, then average across groups.
    """
    if len(features.index) == 0:
        return pd.Series(dtype=float)

    group_values = compute_factor_group_values(features, factor_groups)
    if group_values.empty or len(group_values.columns) == 0:
        return pd.Series(NEUTRAL_FACTOR_STRENGTH, index=features.index, dtype=float)

    ranks = group_values.rank(pct=True, na_option="keep")
    present_count = ranks.notna().sum(axis=1)
    missing_count = len(ranks.columns) - present_count
    present_sum = ranks.fillna(0.0).sum(axis=1)
    shrunk = (present_sum + missing_count * NEUTRAL_FACTOR_STRENGTH) / len(ranks.columns)
    return shrunk.fillna(NEUTRAL_FACTOR_STRENGTH).clip(0.0, 1.0)


# ---------------------------------------------------------------------------
# Technical quality: mean of 4 sub-group quality scores
# ---------------------------------------------------------------------------

def _momentum_quality(features: pd.DataFrame) -> pd.Series:
    """Cross-sectional percentile of momentum signals (higher = better)."""
    mom = pd.to_numeric(features.get("resid_mom_60d"), errors="coerce")
    rs = pd.to_numeric(features.get("rel_strength_60d"), errors="coerce")
    # Average of available percentile ranks
    ranks = []
    if mom.notna().any():
        ranks.append(mom.rank(pct=True, na_option="keep"))
    if rs.notna().any():
        ranks.append(rs.rank(pct=True, na_option="keep"))
    if not ranks:
        return pd.Series(0.0, index=features.index, dtype=float)
    return pd.concat(ranks, axis=1).mean(axis=1).fillna(0.0)


def _trend_quality(features: pd.DataFrame) -> pd.Series:
    """Trend health: proximity to SMA20 (closer = better), penalized by trend_veto."""
    dist = pd.to_numeric(features.get("dist_sma20"), errors="coerce").fillna(0.0)
    # Proximity: 1.0 at SMA20, 0.0 at 10%+ above
    proximity = (1.0 - dist.clip(lower=0.0) / 0.10).clip(0.0, 1.0)
    veto = features.get("trend_veto", pd.Series(False, index=features.index))
    veto = veto.astype(bool).fillna(False)
    return proximity.where(~veto, 0.0)


def _stretch_quality(features: pd.DataFrame) -> pd.Series:
    """Stretch quality: RSI in healthy range (40-70) scores highest."""
    rsi = pd.to_numeric(features.get("rsi_14d"), errors="coerce").fillna(50.0)
    # Score: 1.0 at RSI 55, linear decay to 0 at RSI 20 or RSI 85
    score = 1.0 - ((rsi - 55.0).abs() / 35.0)
    return score.clip(0.0, 1.0)


def _vol_liquidity_quality(features: pd.DataFrame) -> pd.Series:
    """Vol/liquidity quality: lower vol = better (inverted percentile rank)."""
    vol = pd.to_numeric(features.get("yz_vol_20d"), errors="coerce")
    if vol.notna().sum() < 2:
        return pd.Series(0.5, index=features.index, dtype=float)
    # Invert: low vol gets high rank
    return (1.0 - vol.rank(pct=True, na_option="keep")).fillna(0.5)


def compute_technical_quality_continuous(features: pd.DataFrame) -> pd.Series:
    """Mean of 4 technical sub-group quality scores, each in [0, 1]."""
    if features.empty:
        return pd.Series(dtype=float)
    sub_scores = pd.DataFrame({
        "momentum": _momentum_quality(features),
        "trend": _trend_quality(features),
        "stretch": _stretch_quality(features),
        "vol_liquidity": _vol_liquidity_quality(features),
    }, index=features.index)
    return sub_scores.mean(axis=1).clip(0.0, 1.0)


# ---------------------------------------------------------------------------
# Staleness penalty
# ---------------------------------------------------------------------------

def compute_staleness_penalty(
    days_since_factor_change: pd.Series,
    saturation_days: float = 120.0,
) -> pd.Series:
    """Stale-refresh age penalty: min(days / saturation, 1.0)."""
    days = pd.to_numeric(days_since_factor_change, errors="coerce").fillna(0.0).clip(lower=0.0)
    return (days / max(saturation_days, 1.0)).clip(upper=1.0)


# ---------------------------------------------------------------------------
# Lifecycle multiplier
# ---------------------------------------------------------------------------

def lifecycle_state_multiplier(lifecycle_action: pd.Series) -> pd.Series:
    """Map lifecycle_action to post-softmax multiplier."""
    actions = lifecycle_action.astype(str).str.upper().str.strip()
    return actions.map(LIFECYCLE_MULTIPLIERS).fillna(0.0).astype(float)


# ---------------------------------------------------------------------------
# Scoring and sizing
# ---------------------------------------------------------------------------

def score_v1_1_candidates(
    candidates: pd.DataFrame,
    config: Rule100SoftmaxV1_1Config | None = None,
) -> pd.DataFrame:
    """Compute v1.1 base_score. Expects pre-computed continuous columns."""
    cfg = config or Rule100SoftmaxV1_1Config()
    if not isinstance(candidates, pd.DataFrame) or candidates.empty:
        return pd.DataFrame(columns=list(getattr(candidates, "columns", [])) + ["score_v1_1"])

    out = candidates.copy()
    fs = pd.to_numeric(out.get("factor_strength_continuous", 0.0), errors="coerce").fillna(0.0).clip(0.0, 1.0)
    tq = pd.to_numeric(out.get("technical_quality_continuous", 0.0), errors="coerce").fillna(0.0).clip(0.0, 1.0)
    hi = pd.to_numeric(out.get("hold_intact", 0.0), errors="coerce").fillna(0.0).clip(0.0, 1.0)
    sp = pd.to_numeric(out.get("staleness_penalty", 0.0), errors="coerce").fillna(0.0).clip(0.0, 1.0)

    out["factor_strength_component"] = cfg.factor_strength_weight * fs
    out["technical_quality_component"] = cfg.technical_quality_weight * tq
    out["hold_intact_component"] = cfg.hold_intact_weight * hi
    out["staleness_penalty_component"] = cfg.staleness_penalty_weight * sp

    out["score_v1_1"] = (
        out["factor_strength_component"]
        + out["technical_quality_component"]
        + out["hold_intact_component"]
        - out["staleness_penalty_component"]
    )
    return out


def softmax_v1_1_weights(
    candidates: pd.DataFrame,
    config: Rule100SoftmaxV1_1Config | None = None,
) -> pd.Series:
    """Build v1.1 target weights with lifecycle multiplier applied post-softmax.

    Flow: score -> softmax -> budget scale -> cap -> lifecycle multiplier.
    Trimmed/tightened capital becomes cash (no redistribution).
    """
    cfg = config or Rule100SoftmaxV1_1Config()
    scored = score_v1_1_candidates(candidates, cfg)
    if scored.empty:
        return pd.Series(dtype=float)

    budget = gross_budget_for_count(
        len(scored),
        gross_budget_per_name=cfg.gross_budget_per_name,
        gross_budget_cap=cfg.gross_budget_cap,
    )
    probs = stable_softmax(scored["score_v1_1"].to_numpy(dtype=float), temperature=cfg.temperature)
    raw = pd.Series(budget * probs, index=scored.index, dtype=float)
    capped = cap_and_redistribute(raw, cap=cfg.max_single_name_weight)

    # Apply lifecycle multiplier post-cap (no redistribution of freed capital)
    if "lifecycle_state" in scored.columns:
        multiplier = lifecycle_state_multiplier(scored["lifecycle_state"])
        capped = capped * multiplier

    return capped.clip(lower=0.0)
