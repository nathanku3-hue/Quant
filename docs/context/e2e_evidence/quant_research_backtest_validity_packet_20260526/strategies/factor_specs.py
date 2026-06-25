"""
Phase 18 Day 4 — Factor specifications for company scorecard.

Control-theory upgrades are wired as toggles and default to OFF.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Literal
import numpy as np
import pandas as pd


Direction = Literal["positive", "negative"]
Normalization = Literal["zscore", "rank", "raw", "regime_adaptive"]


@dataclass(frozen=True)
class FactorSpec:
    """
    Declarative spec for a single scorecard factor.
    """

    name: str
    candidate_columns: tuple[str, ...]
    direction: Direction
    weight: float
    normalization: Normalization = "zscore"
    use_sigmoid_blend: bool = False
    use_dirty_derivative: bool = False
    use_leaky_integrator: bool = False
    sigmoid_k: float = 0.5
    derivative_weight: float = 0.25
    leaky_alpha: float = 0.20

    def __post_init__(self):
        if not self.name:
            raise ValueError("FactorSpec.name must be non-empty")
        if not self.candidate_columns:
            raise ValueError(f"{self.name}: candidate_columns must be non-empty")
        if self.direction not in ("positive", "negative"):
            raise ValueError(f"{self.name}: invalid direction={self.direction}")
        if self.normalization not in ("zscore", "rank", "raw", "regime_adaptive"):
            raise ValueError(f"{self.name}: invalid normalization={self.normalization}")
        if not 0.0 <= float(self.weight) <= 1.0:
            raise ValueError(f"{self.name}: weight must be in [0,1], got {self.weight}")
        if float(self.sigmoid_k) <= 0.0:
            raise ValueError(f"{self.name}: sigmoid_k must be > 0")
        if float(self.leaky_alpha) <= 0.0 or float(self.leaky_alpha) > 1.0:
            raise ValueError(f"{self.name}: leaky_alpha must be in (0,1], got {self.leaky_alpha}")

    def resolve_feature_column(self, available_columns: set[str]) -> str | None:
        for col in self.candidate_columns:
            if col in available_columns:
                return col
        return None


def validate_factor_specs(specs: list[FactorSpec]) -> None:
    if not specs:
        raise ValueError("factor_specs must be non-empty")

    total_weight = float(sum(spec.weight for spec in specs))
    if abs(total_weight - 1.0) > 1e-6:
        raise ValueError(f"factor weights must sum to 1.0, got {total_weight}")

    names = [spec.name for spec in specs]
    if len(names) != len(set(names)):
        raise ValueError("duplicate factor names detected")


def build_default_factor_specs() -> list[FactorSpec]:
    """
    Day 4 default: equal-weight 4-factor baseline.
    """

    return [
        FactorSpec(
            name="momentum",
            candidate_columns=("resid_mom_60d", "mom_12m"),
            direction="positive",
            weight=0.25,
            normalization="zscore",
        ),
        FactorSpec(
            name="quality",
            candidate_columns=("quality_composite", "capital_cycle_score", "z_moat"),
            direction="positive",
            weight=0.25,
            normalization="zscore",
        ),
        FactorSpec(
            name="volatility",
            candidate_columns=("realized_vol_21d", "yz_vol_20d"),
            direction="negative",
            weight=0.25,
            normalization="zscore",
        ),
        FactorSpec(
            name="illiquidity",
            candidate_columns=("illiq_21d", "amihud_20d"),
            direction="negative",
            weight=0.25,
            normalization="zscore",
        ),
    ]


def build_phase19_5_candidate_factor_sets() -> dict[str, list[FactorSpec]]:
    """
    Phase 19.5 candidate sets focused on signal-strengthening from existing
    Phase 16 inventory-quality features.
    """

    base_4f = [
        FactorSpec(
            name="momentum",
            candidate_columns=("composite_score", "rsi_14d", "rel_strength_60d", "resid_mom_60d"),
            direction="positive",
            weight=0.25,
            normalization="zscore",
            use_leaky_integrator=True,
            leaky_alpha=0.05,
        ),
        FactorSpec(
            name="quality",
            candidate_columns=("z_inventory_quality_proxy", "capital_cycle_score", "z_moat"),
            direction="positive",
            weight=0.25,
            normalization="zscore",
            use_leaky_integrator=True,
            leaky_alpha=0.05,
        ),
        FactorSpec(
            name="volatility",
            candidate_columns=("atr_14d", "yz_vol_20d"),
            direction="negative",
            weight=0.25,
            normalization="zscore",
            use_leaky_integrator=True,
            leaky_alpha=0.05,
        ),
        FactorSpec(
            name="illiquidity",
            candidate_columns=("z_flow_proxy", "amihud_20d"),
            direction="negative",
            weight=0.25,
            normalization="zscore",
            use_leaky_integrator=True,
            leaky_alpha=0.05,
        ),
    ]
    validate_factor_specs(base_4f)

    base_5f = [
        replace(base_4f[0], weight=0.20),
        replace(base_4f[1], weight=0.20),
        replace(base_4f[2], weight=0.20),
        replace(base_4f[3], weight=0.20),
        FactorSpec(
            name="discipline",
            candidate_columns=("z_discipline_cond", "z_demand"),
            direction="positive",
            weight=0.20,
            normalization="zscore",
            use_leaky_integrator=True,
            leaky_alpha=0.05,
        ),
    ]
    validate_factor_specs(base_5f)

    rank_4f = [replace(spec, normalization="rank") for spec in base_4f]
    validate_factor_specs(rank_4f)

    return {
        "P195_SIGNAL_STRENGTH_4F": base_4f,
        "P195_SIGNAL_STRENGTH_5F": base_5f,
        "P195_SIGNAL_STRENGTH_4F_RANK": rank_4f,
    }


def build_phase35_wave1_candidate_specs() -> list[FactorSpec]:
    """
    Phase 35 Wave 1: Pure candidate column improvement.

    NO aggregate signals (composite_score removed for clean ablation).
    NO other changes: equal weights (0.25), zscore norm, no leaky integrators.
    """
    return [
        FactorSpec(
            name="momentum",
            candidate_columns=("resid_mom_60d", "rel_strength_60d", "rsi_14d"),
            direction="positive",
            weight=0.25,
            normalization="zscore",
        ),
        FactorSpec(
            name="quality",
            candidate_columns=("capital_cycle_score", "z_inventory_quality_proxy", "z_moat"),
            direction="positive",
            weight=0.25,
            normalization="zscore",
        ),
        FactorSpec(
            name="volatility",
            candidate_columns=("yz_vol_20d", "atr_14d"),
            direction="negative",
            weight=0.25,
            normalization="zscore",
        ),
        FactorSpec(
            name="illiquidity",
            candidate_columns=("amihud_20d", "z_flow_proxy"),
            direction="negative",
            weight=0.25,
            normalization="zscore",
        ),
    ]


def regime_adaptive_norm(
    values: pd.Series,
    date_index: pd.Series,
    regime_by_date: pd.Series | None,
) -> pd.Series:
    """
    Regime-adaptive cross-sectional normalization.

    Policy:
      - GREEN: zscore
      - AMBER/RED: rank percentile mapped to [-1, 1]
    """

    v = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan)
    d = pd.to_datetime(date_index, errors="coerce")
    out = pd.Series(np.nan, index=v.index, dtype=float)
    if v.empty:
        return out

    if regime_by_date is None or len(regime_by_date) == 0:
        mu = v.groupby(d).transform("mean")
        sigma = v.groupby(d).transform("std").replace(0.0, np.nan)
        return (v - mu) / sigma

    regime_map = pd.Series(regime_by_date).copy()
    regime_map.index = pd.to_datetime(regime_map.index, errors="coerce")
    regime_map = regime_map[~regime_map.index.isna()]
    regime = d.map(regime_map).fillna("AMBER").astype(str).str.upper()

    green_mask = regime.eq("GREEN")
    stress_mask = ~green_mask

    if bool(green_mask.any()):
        vg = v[green_mask]
        dg = d[green_mask]
        mu = vg.groupby(dg).transform("mean")
        sigma = vg.groupby(dg).transform("std").replace(0.0, np.nan)
        out.loc[green_mask] = (vg - mu) / sigma

    if bool(stress_mask.any()):
        vs = v[stress_mask]
        ds = d[stress_mask]
        rank_pct = vs.groupby(ds).rank(pct=True, method="average")
        out.loc[stress_mask] = (rank_pct - 0.5) * 2.0

    return out


def correlation_audit(
    frame: pd.DataFrame,
    factor_columns: list[str],
    date_col: str = "date",
    regime_by_date: pd.Series | None = None,
) -> pd.DataFrame:
    """
    Pairwise orthogonality audit for factor columns.
    Returns one row per pair and regime slice.
    """

    if not factor_columns:
        return pd.DataFrame(
            columns=[
                "regime",
                "factor_a",
                "factor_b",
                "n_obs",
                "pearson_corr",
                "abs_corr",
                "orthogonal_pass",
            ]
        )
    work = frame.copy()
    if date_col in work.columns:
        work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    else:
        work[date_col] = pd.NaT

    for c in factor_columns:
        if c not in work.columns:
            work[c] = np.nan
        work[c] = pd.to_numeric(work[c], errors="coerce")

    regime = pd.Series("ALL", index=work.index, dtype="object")
    if regime_by_date is not None and len(regime_by_date) > 0:
        regime_map = pd.Series(regime_by_date).copy()
        regime_map.index = pd.to_datetime(regime_map.index, errors="coerce")
        regime_map = regime_map[~regime_map.index.isna()]
        regime = work[date_col].map(regime_map).fillna("AMBER").astype(str).str.upper()
    work["__regime__"] = regime

    rows: list[dict[str, object]] = []
    for reg_name, reg_df in [("ALL", work)] + [
        (name, grp) for name, grp in work.groupby("__regime__", sort=True)
    ]:
        for i in range(len(factor_columns)):
            for j in range(i + 1, len(factor_columns)):
                a = factor_columns[i]
                b = factor_columns[j]
                pair = reg_df[[a, b]].dropna()
                n = int(len(pair))
                if n < 3:
                    corr = np.nan
                else:
                    corr = float(pair[a].corr(pair[b]))
                abs_corr = float(abs(corr)) if np.isfinite(corr) else np.nan
                rows.append(
                    {
                        "regime": str(reg_name),
                        "factor_a": a,
                        "factor_b": b,
                        "n_obs": n,
                        "pearson_corr": corr,
                        "abs_corr": abs_corr,
                        "orthogonal_pass": bool(np.isfinite(abs_corr) and abs_corr <= 0.65),
                    }
                )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["regime", "abs_corr"], ascending=[True, False]).reset_index(drop=True)


def regime_veto(
    date_index: pd.Series,
    regime_by_date: pd.Series | None,
    *,
    blocked_regimes: tuple[str, ...] = ("RED",),
) -> pd.Series:
    """
    Return True for rows that should be vetoed by regime.
    """

    d = pd.to_datetime(date_index, errors="coerce")
    if regime_by_date is None or len(regime_by_date) == 0:
        return pd.Series(False, index=d.index, dtype=bool)
    regime_map = pd.Series(regime_by_date).copy()
    regime_map.index = pd.to_datetime(regime_map.index, errors="coerce")
    regime_map = regime_map[~regime_map.index.isna()]
    regime = d.map(regime_map).fillna("AMBER").astype(str).str.upper()
    blocked = {str(x).upper() for x in blocked_regimes}
    return regime.isin(blocked)


def per_regime_audit(
    scores: pd.DataFrame,
    *,
    factor_names: list[str],
    regime_by_date: pd.Series | None,
    date_col: str = "date",
    score_col: str = "score",
) -> pd.DataFrame:
    """
    Per-regime diagnostics:
      - coverage
      - quartile_spread_sigma
      - mean absolute factor contribution
    """

    if scores.empty:
        return pd.DataFrame(
            columns=["regime", "metric", "value", "n_rows", "n_dates"]
        )
    work = scores.copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    work = work.dropna(subset=[date_col])
    if work.empty:
        return pd.DataFrame(
            columns=["regime", "metric", "value", "n_rows", "n_dates"]
        )

    regime_map = pd.Series(regime_by_date).copy() if regime_by_date is not None else pd.Series(dtype="object")
    if len(regime_map):
        regime_map.index = pd.to_datetime(regime_map.index, errors="coerce")
        regime_map = regime_map[~regime_map.index.isna()]
        regime = work[date_col].map(regime_map).fillna("AMBER").astype(str).str.upper()
    else:
        regime = pd.Series("AMBER", index=work.index, dtype="object")
    work["__regime__"] = regime

    rows: list[dict[str, object]] = []
    for name, grp in [("ALL", work)] + [(k, g) for k, g in work.groupby("__regime__", sort=True)]:
        n_rows = int(len(grp))
        n_dates = int(grp[date_col].nunique())
        score_valid = pd.to_numeric(grp.get("score_valid"), errors="coerce").fillna(False).astype(bool)
        coverage = float(score_valid.mean()) if n_rows else 0.0
        rows.append(
            {
                "regime": str(name),
                "metric": "coverage",
                "value": coverage,
                "n_rows": n_rows,
                "n_dates": n_dates,
            }
        )

        # Per-date quartile spread in score space.
        spreads: list[float] = []
        valid_grp = grp.loc[score_valid].copy()
        valid_grp[score_col] = pd.to_numeric(valid_grp[score_col], errors="coerce")
        valid_grp = valid_grp.dropna(subset=[score_col])
        for _, dgrp in valid_grp.groupby(date_col, sort=True):
            s = pd.to_numeric(dgrp[score_col], errors="coerce").dropna()
            if len(s) < 8:
                continue
            q1 = s.quantile(0.75)
            q4 = s.quantile(0.25)
            top = s[s >= q1].mean()
            bot = s[s <= q4].mean()
            sigma = s.std(ddof=0)
            if np.isfinite(sigma) and sigma > 0:
                spreads.append(float((top - bot) / sigma))
        rows.append(
            {
                "regime": str(name),
                "metric": "quartile_spread_sigma",
                "value": float(np.mean(spreads)) if spreads else np.nan,
                "n_rows": n_rows,
                "n_dates": n_dates,
            }
        )

        # Mean abs contribution by factor.
        for fname in factor_names:
            c = f"{fname}_contrib"
            if c not in grp.columns:
                continue
            val = float(pd.to_numeric(grp[c], errors="coerce").abs().mean())
            rows.append(
                {
                    "regime": str(name),
                    "metric": f"mean_abs_contrib_{fname}",
                    "value": val,
                    "n_rows": n_rows,
                    "n_dates": n_dates,
                }
            )
    return pd.DataFrame(rows)
