"""
Phase 21.1 ticker-pool ranking.

Implements a PIT-safe Mahalanobis distance ranker with:
  - Ledoit-Wolf covariance shrinkage when sklearn is available.
  - Deterministic manual fixed shrinkage fallback (alpha=0.50) toward
    a constant-correlation covariance target when sklearn is unavailable.
  - Anchor-injected cyclical centroid in z-scored feature space.
  - Critical fallback to legacy top-k centroid by pre-pool score when no anchors exist.
  - Daily empirical CDF probability mapping (average-rank eCDF).
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Anchor basket used for cyclical centroid injection (z-space).
CYCLICAL_ANCHORS: tuple[str, ...] = ("LRCX", "AMAT", "KLAC", "STX", "WDC", "MU")
POST_POOL_SCORE_COLS: tuple[str, ...] = (
    "mahalanobis_distance",
    "mahalanobis_k_cyc",
    "compounder_prob",
    "pool_long_candidate",
    "pool_short_candidate",
    "pool_action",
    "posterior_cyclical",
    "posterior_defensive",
    "posterior_junk",
    "posterior_negative",
    "odds_ratio",
    "odds_score",
)
RISK_FEATURE_BLOCKLIST: tuple[str, ...] = (
    "realized_vol_lag",
    "yz_vol_20d",
    "atr_14d",
    "sigma_continuous",
    "asset_beta_lag",
    "portfolio_beta",
    "rolling_beta_63d",
)
RISK_TOKEN_BLOCKLIST: tuple[str, ...] = ("beta", "vol")
ROBUST_SIGMA_SCALE: float = 1.4826
ROBUST_SIGMA_EPSILON_FLOOR: float = 1e-6
ROBUST_SIGMA_MIN_WINDOW_SIZE: int = 20
BOOLEAN_TRUE_TOKENS = frozenset({"1", "true", "t", "yes", "y", "on"})
BOOLEAN_FALSE_TOKENS = frozenset({"0", "false", "f", "no", "n", "off"})


@dataclass(frozen=True)
class TickerPoolConfig:
    feature_columns: tuple[str, ...] = (
        "rev_accel",
        "inv_vel_traj",
        "op_lev",
        "q_tot",
        "CycleSetup",
    )
    seed_tickers: tuple[str, ...] = ("MU", "CIEN", "COHR", "TER", "LRCX", "AMAT", "KLAC", "STX", "WDC")
    dictatorship_mode: bool = True
    path1_allow_features: tuple[str, ...] = (
        "rev_accel",
        "inv_vel_traj",
        "op_lev",
        "q_tot",
        "CycleSetup",
    )
    path1_deny_features: tuple[str, ...] = ()
    min_universe: int = 15
    min_center_count: int = 4
    centroid_top_k: int = 30
    centroid_lambda: float = 8.0
    cyclical_feature_weight: float = 2.5
    long_prob_threshold: float = 0.70
    short_distance_quantile: float = 0.85
    fallback_long_top_k: int = 8
    odds_epsilon: float = 1e-8
    manual_shrinkage: float = 0.50
    ridge: float = 1e-6
    covariance_type: str = "diag"
    geometry_clip_lower_quantile: float = 0.02
    geometry_clip_upper_quantile: float = 0.98


def _assert_geometry_excludes_risk(features: list[str] | tuple[str, ...], *, context: str) -> None:
    feature_l = [str(c).strip().lower() for c in features]
    exact_hits = sorted(set(feature_l).intersection({c.lower() for c in RISK_FEATURE_BLOCKLIST}))
    token_hits = sorted(
        {
            c
            for c in feature_l
            if any(token in c for token in RISK_TOKEN_BLOCKLIST)
        }
    )
    # Explicit geometry isolation contract: risk features must never enter BGM matrix.
    if exact_hits:
        raise ValueError(f"{context} includes risk columns forbidden in BGM geometry: {exact_hits}")
    if token_hits:
        raise ValueError(f"{context} includes beta/vol tokens forbidden in BGM geometry: {token_hits}")


def _resolve_path1_feature_partition(cfg: TickerPoolConfig) -> tuple[list[str], list[str]]:
    allow = [str(c) for c in cfg.path1_allow_features]
    deny = [str(c) for c in cfg.path1_deny_features]
    allow_set = set(allow)
    deny_set = set(deny)
    overlap = sorted(allow_set.intersection(deny_set))
    if overlap:
        raise ValueError(
            "Path1 feature partition invalid: allow/deny overlap detected: "
            f"{overlap}"
        )

    feature_set = set(str(c) for c in cfg.feature_columns)
    partition_set = allow_set.union(deny_set)
    if partition_set != feature_set:
        missing = sorted(feature_set - partition_set)
        extras = sorted(partition_set - feature_set)
        raise ValueError(
            "Path1 feature partition invalid: allow/deny must exactly partition "
            f"feature_columns. missing={missing}, extras={extras}"
        )
    return allow, deny


def _percentile_fallback_scale(series: pd.Series) -> pd.Series:
    ranked = series.rank(method="average", pct=True, na_option="keep")
    return ((ranked - 0.5) * 2.0).astype(float)


def _robust_zscore(
    series: pd.Series,
    *,
    epsilon_floor: float = ROBUST_SIGMA_EPSILON_FLOOR,
    min_window_size: int = ROBUST_SIGMA_MIN_WINDOW_SIZE,
    return_telemetry: bool = False,
) -> pd.Series | tuple[pd.Series, dict[str, float | int]]:
    s = pd.to_numeric(series, errors="coerce")
    window_size = int(s.notna().sum())
    min_window = max(1, int(min_window_size))
    eps = max(float(epsilon_floor), float(np.finfo(float).eps))
    fallback_rows = 0

    if window_size == 0:
        scaled = pd.Series(np.nan, index=s.index, dtype=float)
    else:
        med = float(s.median(skipna=True))
        mad = float((s - med).abs().median(skipna=True))
        if not np.isfinite(mad):
            mad = 0.0
        robust_sigma = max(ROBUST_SIGMA_SCALE * mad, eps)
        scaled = (s - med) / robust_sigma
        if window_size < min_window:
            scaled = _percentile_fallback_scale(s)
            fallback_rows = 1

    row_total = 1 if window_size > 0 else 0
    telemetry: dict[str, float | int] = {
        "window_size": window_size,
        "min_window_size": min_window,
        "epsilon_floor": eps,
        "row_total": row_total,
        "fallback_rows": fallback_rows,
        "fallback_rate": (float(fallback_rows) / float(row_total)) if row_total > 0 else 0.0,
    }
    if return_telemetry:
        return scaled.astype(float), telemetry
    return scaled.astype(float)


def _clean_context_group(values: pd.Series) -> pd.Series:
    out = values.astype("string").str.strip()
    upper = out.str.upper()
    out = out.mask(
        out.isna()
        | (out == "")
        | upper.isin({"UNKNOWN", "NAN", "NONE", "<NA>"}),
        pd.NA,
    )
    return out


def _normalize_boolean_series(values: pd.Series, *, default: bool = False) -> pd.Series:
    parsed = pd.Series(pd.NA, index=values.index, dtype="boolean")

    bool_mask = values.map(lambda v: isinstance(v, (bool, np.bool_)))
    if bool_mask.any():
        parsed.loc[bool_mask] = values.loc[bool_mask].astype(bool).to_numpy()

    numeric = pd.to_numeric(values, errors="coerce")
    parsed.loc[numeric.eq(1.0)] = True
    parsed.loc[numeric.eq(0.0)] = False

    text = values.astype("string").str.strip().str.lower()
    parsed.loc[text.isin(BOOLEAN_TRUE_TOKENS)] = True
    parsed.loc[text.isin(BOOLEAN_FALSE_TOKENS)] = False

    return parsed.fillna(bool(default)).astype(bool)


def _hierarchical_impute_geometry(
    block: pd.DataFrame,
    feature_columns: list[str] | tuple[str, ...],
    *,
    industry_col: str = "industry",
    sector_col: str = "sector",
) -> tuple[pd.DataFrame, dict[str, int]]:
    """
    Bitemporal NaN handling for SDM geometry features.

    Level 1: same-date industry median (fallback: sector median via grouping key).
    Level 2: neutral zero fill for remaining NaNs.
    """
    idx = block.index
    cols = [str(c) for c in feature_columns]
    raw = pd.DataFrame(index=idx)
    for col in cols:
        raw[col] = pd.to_numeric(block.get(col, pd.Series(np.nan, index=idx, dtype=float)), errors="coerce")

    industry = (
        _clean_context_group(block[industry_col])
        if industry_col in block.columns
        else pd.Series(pd.NA, index=idx, dtype="string")
    )
    sector = (
        _clean_context_group(block[sector_col])
        if sector_col in block.columns
        else pd.Series(pd.NA, index=idx, dtype="string")
    )
    industry_key = industry.fillna("UNKNOWN")
    sector_key = sector.fillna("UNKNOWN")

    out = pd.DataFrame(index=idx)
    industry_fill_cells = 0
    sector_fill_cells = 0
    zero_fill_cells = 0
    for col in cols:
        s = raw[col]
        missing_before = s.isna()
        # Level 1A: industry peer fill (same PIT date slice).
        ind_med = s.groupby(industry_key, sort=False).transform("median")
        s_level1 = s.fillna(ind_med)
        industry_fill_cells += int((missing_before & s_level1.notna()).sum())
        # Level 1B: sector peer fill for remaining gaps.
        missing_after_industry = s_level1.isna()
        sec_med = s.groupby(sector_key, sort=False).transform("median")
        s_level2 = s_level1.fillna(sec_med)
        sector_fill_cells += int((missing_after_industry & s_level2.notna()).sum())
        # Level 2: keep row in universe with neutral value.
        remaining = s_level2.isna()
        zero_fill_cells += int(remaining.sum())
        out[col] = s_level2.fillna(0.0)

    stats = {
        "universe_before_imputation": int(raw.notna().all(axis=1).sum()),
        "universe_after_imputation": int(out.notna().all(axis=1).sum()),
        "industry_fill_cells": int(industry_fill_cells),
        "sector_fill_cells": int(sector_fill_cells),
        "zero_fill_cells": int(zero_fill_cells),
    }
    return out, stats


def _build_weighted_zmat_with_imputation(
    block: pd.DataFrame,
    cfg: TickerPoolConfig,
    *,
    industry_col: str = "industry",
    sector_col: str = "sector",
) -> tuple[pd.DataFrame, dict[str, int | float]]:
    imputed_raw, stats = _hierarchical_impute_geometry(
        block,
        cfg.feature_columns,
        industry_col=industry_col,
        sector_col=sector_col,
    )
    sector_key = (
        _clean_context_group(block[sector_col])
        if sector_col in block.columns
        else pd.Series(pd.NA, index=block.index, dtype="string")
    )
    # Granularity preference for neutralization:
    # industry_group (if present) -> industry -> sector -> market.
    candidate_keys: list[pd.Series] = []
    if "industry_group" in block.columns:
        candidate_keys.append(_clean_context_group(block["industry_group"]))
    if industry_col in block.columns:
        candidate_keys.append(_clean_context_group(block[industry_col]))
    candidate_keys.append(sector_key)
    peer_key = pd.Series(pd.NA, index=block.index, dtype="string")
    for key in candidate_keys:
        peer_key = peer_key.combine_first(key)
    peer_key = peer_key.fillna("MARKET")
    neutralize_cols = {c for c in cfg.feature_columns if c != "CycleSetup"}

    zmat = pd.DataFrame(index=block.index)
    scale_row_total = 0
    scale_fallback_rows = 0
    for col in cfg.feature_columns:
        xcol = pd.to_numeric(imputed_raw[col], errors="coerce")
        lo_q = float(np.clip(cfg.geometry_clip_lower_quantile, 0.0, 1.0))
        hi_q = float(np.clip(cfg.geometry_clip_upper_quantile, 0.0, 1.0))
        if hi_q < lo_q:
            lo_q, hi_q = hi_q, lo_q
        finite = xcol[np.isfinite(xcol)]
        if not finite.empty:
            lo = float(finite.quantile(lo_q))
            hi = float(finite.quantile(hi_q))
            if np.isfinite(lo) and np.isfinite(hi):
                xcol = xcol.clip(lower=min(lo, hi), upper=max(lo, hi))

        if col in neutralize_cols:
            peer_med = xcol.groupby(peer_key, sort=False).transform("median")
            market_med = float(np.nanmedian(xcol.to_numpy(dtype=float)))
            if np.isfinite(market_med):
                peer_med = peer_med.fillna(market_med)
            xcol = xcol - peer_med
        zcol, scale_stats = _robust_zscore(xcol, return_telemetry=True)
        scale_row_total += int(scale_stats.get("row_total", 0))
        scale_fallback_rows += int(scale_stats.get("fallback_rows", 0))

        if bool(zcol.isna().all()):
            zcol = pd.Series(0.0, index=block.index, dtype=float)
        # Neutral zero in robust space for any residual missing values.
        zmat[col] = zcol.fillna(0.0) * _feature_weight(col, cfg)
    stats["scale_row_total"] = int(scale_row_total)
    stats["scale_fallback_rows"] = int(scale_fallback_rows)
    stats["scale_fallback_rate"] = (
        float(scale_fallback_rows) / float(scale_row_total) if scale_row_total > 0 else 0.0
    )
    return zmat, stats


def _constant_correlation_target(sample_cov: np.ndarray) -> np.ndarray:
    cov = np.atleast_2d(np.asarray(sample_cov, dtype=float))
    n_feat = cov.shape[0]
    if n_feat <= 1:
        return cov.copy()

    var = np.clip(np.diag(cov), a_min=0.0, a_max=None)
    std = np.sqrt(var)
    denom = np.outer(std, std)
    with np.errstate(divide="ignore", invalid="ignore"):
        corr = np.divide(cov, denom, out=np.zeros_like(cov), where=denom > 0.0)
    np.fill_diagonal(corr, 1.0)

    off_diag = corr[~np.eye(n_feat, dtype=bool)]
    finite_off = off_diag[np.isfinite(off_diag)]
    mean_corr = float(np.nanmean(finite_off)) if finite_off.size else 0.0
    mean_corr = float(np.clip(mean_corr, -0.99, 0.99))

    target = mean_corr * np.outer(std, std)
    np.fill_diagonal(target, var)
    return target


def _fit_covariance(
    x: np.ndarray,
    manual_shrinkage: float,
    ridge: float,
    covariance_type: str = "diag",
) -> tuple[np.ndarray, str, float]:
    if x.ndim != 2:
        raise ValueError("x must be 2D")
    n_obs, n_feat = x.shape
    cov_mode = str(covariance_type).strip().lower()
    if cov_mode not in {"full", "diag"}:
        cov_mode = "diag"
    if n_obs < 2 or n_feat < 1:
        cov = np.eye(max(1, n_feat), dtype=float) * float(ridge)
        method = "manual_fixed_constant_corr_diag" if cov_mode == "diag" else "manual_fixed_constant_corr"
        return cov, method, float(manual_shrinkage)

    try:
        from sklearn.covariance import LedoitWolf  # type: ignore

        lw = LedoitWolf().fit(x)
        cov = np.asarray(lw.covariance_, dtype=float)
        shrink = float(getattr(lw, "shrinkage_", np.nan))
        method = "ledoit_wolf"
        if cov_mode == "diag":
            cov = np.diag(np.diag(cov))
            method = f"{method}_diag"
        cov = cov + np.eye(cov.shape[0], dtype=float) * float(ridge)
        return cov, method, shrink
    except Exception:
        sample_cov = np.cov(x, rowvar=False, ddof=1)
        sample_cov = np.atleast_2d(np.asarray(sample_cov, dtype=float))
        target = _constant_correlation_target(sample_cov)
        alpha = float(np.clip(manual_shrinkage, 0.0, 1.0))
        cov = ((1.0 - alpha) * sample_cov) + (alpha * target)
        method = "manual_fixed_constant_corr"
        if cov_mode == "diag":
            cov = np.diag(np.diag(cov))
            method = f"{method}_diag"
        cov = cov + np.eye(cov.shape[0], dtype=float) * float(ridge)
        return cov, method, alpha


def _mahalanobis_batch(x: np.ndarray, center: np.ndarray, inv_cov: np.ndarray) -> np.ndarray:
    diff = x - center
    m2 = np.einsum("ij,jk,ik->i", diff, inv_cov, diff)
    m2 = np.clip(m2, a_min=0.0, a_max=None)
    return np.sqrt(m2)


def _ecdf_probability(distance: pd.Series) -> pd.Series:
    finite = pd.to_numeric(distance, errors="coerce")
    finite = finite[np.isfinite(finite)]
    if finite.empty:
        return pd.Series(dtype=float)
    if len(finite) == 1:
        return pd.Series(0.5, index=finite.index, dtype=float)
    ranks = finite.rank(method="average", ascending=True)
    ecdf = ranks / float(len(finite))
    prob = 1.0 - ecdf
    return prob.astype(float)


def _feature_weight(col: str, cfg: TickerPoolConfig) -> float:
    cyclical_cols = {
        "CycleSetup",
    }
    if col in cyclical_cols:
        return float(cfg.cyclical_feature_weight)
    return 1.0


def _conviction_cluster_score(center: np.ndarray, feature_names: list[str] | tuple[str, ...]) -> float:
    """Option A cyclical-trough ranker (locked Phase 20 close state)."""
    vec = np.asarray(center, dtype=float).reshape(-1)
    f = {str(name): float(vec[i]) if i < len(vec) and np.isfinite(vec[i]) else 0.0 for i, name in enumerate(feature_names)}
    return float(
        (2.0 * f.get("CycleSetup", 0.0))
        + f.get("op_lev", 0.0)
        + f.get("rev_accel", 0.0)
        + f.get("inv_vel_traj", 0.0)
        - f.get("q_tot", 0.0)
    )


def _quarter_key(ts: pd.Timestamp) -> pd.Period:
    return pd.Timestamp(ts).to_period("Q")


def _assert_pre_pool_score_col(score_col: str) -> None:
    score_key = str(score_col).strip().lower()
    if score_key == "":
        raise ValueError("score_col must be a non-empty pre-pool metric column name.")
    if score_key in {c.lower() for c in POST_POOL_SCORE_COLS}:
        raise ValueError(
            f"score_col='{score_col}' is a post-pool metric. "
            "Fallback centroid scoring requires a pre-pool metric."
        )
    if score_key.startswith("pool_"):
        raise ValueError(
            f"score_col='{score_col}' appears to be pool-derived. "
            "Fallback centroid scoring requires a pre-pool metric."
        )


def _compute_cyc_centroid_anchor_injected(
    block: pd.DataFrame,
    zmat: pd.DataFrame,
    *,
    ticker_col: str,
    score_col: str,
    centroid_top_k: int,
) -> tuple[np.ndarray, str, int, list[str], list[str]]:
    anchor_set = {t.upper() for t in CYCLICAL_ANCHORS}
    ticker_upper = block[ticker_col].astype(str).str.upper()
    anchors_present = sorted(anchor_set.intersection(set(ticker_upper.tolist())))
    anchors_missing = sorted(anchor_set - set(anchors_present))

    anchor_mask = ticker_upper.isin(anchor_set)
    anchor = zmat.loc[anchor_mask].dropna(how="any")
    if len(anchor) > 0:
        logger.info(
            "mu_cyc anchor-injected: n=%d/%d anchors present",
            len(anchor),
            len(CYCLICAL_ANCHORS),
        )
        center = anchor.mean(axis=0).to_numpy(dtype=np.float64)
        return center, "anchor_injected", int(len(anchor)), anchors_present, anchors_missing

    logger.critical(
        "mu_cyc anchor injection FAILED (no anchors present on this slice). "
        "Falling back to legacy centroid_top_k=%d using score_col='%s'.",
        int(max(1, centroid_top_k)),
        score_col,
    )
    score = pd.to_numeric(block.get(score_col), errors="coerce")
    k = int(max(1, centroid_top_k))
    top_idx = score.nlargest(k).index
    top = zmat.loc[top_idx].dropna(how="any")
    if len(top) == 0:
        logger.critical(
            "Legacy top_k centroid also failed (empty after NaN drop). Returning zero vector mu_cyc."
        )
        return (
            np.zeros(len(zmat.columns), dtype=np.float64),
            "anchor_fallback_zero",
            0,
            anchors_present,
            anchors_missing,
        )

    center = top.mean(axis=0).to_numpy(dtype=np.float64)
    return center, "anchor_fallback_topk", int(len(top)), anchors_present, anchors_missing


def _compute_cyc_centroid_topk_legacy(
    block: pd.DataFrame,
    zmat: pd.DataFrame,
    *,
    score_col: str,
    centroid_top_k: int,
) -> tuple[np.ndarray, str, int, list[str], list[str]]:
    score = pd.to_numeric(block.get(score_col), errors="coerce")
    k = int(max(1, centroid_top_k))
    top_idx = score.nlargest(k).index
    top = zmat.loc[top_idx].dropna(how="any")
    if len(top) == 0:
        logger.critical(
            "Legacy top_k centroid failed (empty after NaN drop). Returning zero vector mu_cyc."
        )
        return (
            np.zeros(len(zmat.columns), dtype=np.float64),
            "legacy_topk_zero",
            0,
            [],
            [],
        )
    center = top.mean(axis=0).to_numpy(dtype=np.float64)
    return center, "legacy_topk", int(len(top)), [], []


def _path1_sector_projection_residualize(
    x: pd.DataFrame,
    sectors: pd.Series,
) -> tuple[pd.DataFrame, str, int]:
    if x.empty:
        return x.copy(), "empty", 0

    s = sectors.reindex(x.index)
    s = s.astype("string").fillna("UNKNOWN")
    sector_count = int(s.nunique(dropna=False))
    if sector_count <= 0:
        return x.copy(), "no_sector_dummies", 0

    # Projection onto sector dummies is algebraically equivalent to subtracting
    # each sector's cross-sectional mean and avoids O(N^2) matrix ops.
    x_num = x.apply(pd.to_numeric, errors="coerce")
    sector_mean = x_num.groupby(s, sort=False).transform("mean")
    resid = x_num - sector_mean
    resid_mat = resid.to_numpy(dtype=float)
    if not bool(np.isfinite(resid_mat).all()):
        return x.copy(), "projection_nonfinite_fallback", sector_count
    return (
        pd.DataFrame(resid_mat, index=x.index, columns=x.columns),
        "sector_projection_residualized",
        sector_count,
    )


def _date_seed(ts: pd.Timestamp) -> int:
    t = pd.Timestamp(ts).normalize()
    return int(t.strftime("%Y%m%d"))


def _stable_identity_key(
    block: pd.DataFrame,
    *,
    permno_col: str,
    ticker_col: str,
) -> pd.Series:
    if permno_col in block.columns:
        permno = pd.to_numeric(block[permno_col], errors="coerce")
    else:
        permno = pd.Series(np.nan, index=block.index, dtype=float)
    if ticker_col in block.columns:
        ticker = block[ticker_col].astype(str)
    else:
        ticker = pd.Series("", index=block.index, dtype="object")
    permno_key = permno.apply(lambda v: "" if not np.isfinite(v) else str(int(v)))
    key = ticker.where(permno.isna(), permno_key)
    return key.astype(str)


def _deterministic_sector_balanced_resample(
    x: pd.DataFrame,
    *,
    sectors: pd.Series,
    stable_key: pd.Series,
    date_seed: int,
) -> tuple[pd.DataFrame, str, int, int]:
    if x.empty:
        return x.copy(), "empty", 0, int(date_seed)

    sec = sectors.reindex(x.index).astype("string").fillna("UNKNOWN")
    known_mask = ~sec.str.upper().eq("UNKNOWN")
    sec_known = sec.loc[known_mask]
    counts = sec_known.value_counts(dropna=False)
    if int(counts.shape[0]) < 2:
        return x.copy(), "unbalanced_single_known_sector", 0, int(date_seed)

    per_sector = int(counts.min())
    if per_sector < 2:
        return x.copy(), "unbalanced_too_shallow", per_sector, int(date_seed)

    rng = np.random.default_rng(int(date_seed))
    picked: list = []
    for sec_name in sorted(counts.index.astype(str).tolist()):
        sec_mask = sec.eq(sec_name)
        sec_idx = x.index[sec_mask]
        key = stable_key.reindex(sec_idx).fillna("").astype(str)
        ordered_idx = pd.Series(sec_idx, index=sec_idx).loc[
            key.sort_values(kind="mergesort").index
        ].to_numpy()
        selected_pos = np.sort(rng.choice(np.arange(len(ordered_idx)), size=per_sector, replace=False))
        picked.extend(ordered_idx[selected_pos].tolist())

    sample_idx = pd.Index(picked)
    return x.loc[sample_idx], "sector_balanced_date_seeded", per_sector, int(date_seed)


def _defensive_cluster_mask_by_realized_vol(
    zvalid: pd.DataFrame,
    *,
    vol_col: str = "realized_vol_lag",
) -> tuple[pd.Series, int]:
    """
    Identify a defensive component as the lowest transformed realized-vol cluster.

    Uses 3 quantile buckets on transformed realized vol and selects the bucket
    with the lowest mean vol as the defensive cluster.
    """
    if vol_col not in zvalid.columns:
        return pd.Series(False, index=zvalid.index, dtype=bool), -1
    vol = pd.to_numeric(zvalid[vol_col], errors="coerce")
    if int(vol.notna().sum()) < 3:
        return pd.Series(False, index=zvalid.index, dtype=bool), -1

    vol_rank = vol.rank(method="average", pct=True)
    bucket = pd.Series(np.nan, index=zvalid.index, dtype=float)
    bucket.loc[vol_rank <= (1.0 / 3.0)] = 0.0
    bucket.loc[(vol_rank > (1.0 / 3.0)) & (vol_rank <= (2.0 / 3.0))] = 1.0
    bucket.loc[vol_rank > (2.0 / 3.0)] = 2.0
    if int(bucket.notna().sum()) < 3:
        return pd.Series(False, index=zvalid.index, dtype=bool), -1

    means = vol.groupby(bucket).mean()
    means = means[np.isfinite(means)]
    if means.empty:
        return pd.Series(False, index=zvalid.index, dtype=bool), -1
    defensive_id = int(float(means.idxmin()))
    mask = bucket.eq(float(defensive_id)).fillna(False)
    return mask.astype(bool), defensive_id


def _junk_cluster_mask_by_quality_growth(
    block: pd.DataFrame,
    *,
    ebitda_roic_col: str = "z_ebitda_roic_accel",
    ebitda_col: str = "ebitda_accel",
    roic_col: str = "roic_accel",
    revenue_col: str = "revenue_growth_q",
) -> tuple[pd.Series, int, pd.Series]:
    """
    Identify a junk component using lowest-median quality/growth diagnostics:
      - ebitda_roic_accel proxy (mean of ebitda_accel and roic_accel z-proxies),
      - gm_accel_q proxy (fallback: operating_margin_delta_q, then ebitda_accel),
      - revenue_growth_q proxy (fallback: revenue_growth_yoy, then revenue_growth_lag).
    Returns:
      - junk cluster membership mask
      - junk cluster id
      - per-row missing-quality mask (any of the three diagnostics unavailable)
    """
    idx = block.index
    nan_series = pd.Series(np.nan, index=idx, dtype=float)

    def _first_nonempty_series(candidates: list[str], fallback: pd.Series) -> pd.Series:
        for col in candidates:
            if col not in block.columns:
                continue
            candidate = pd.to_numeric(block[col], errors="coerce")
            if int(candidate.notna().sum()) > 0:
                return candidate
        return fallback

    ebitda_raw = pd.to_numeric(block.get(ebitda_col, nan_series), errors="coerce")
    roic_raw = pd.to_numeric(block.get(roic_col, nan_series), errors="coerce")
    ebitda_roic_src = _first_nonempty_series([ebitda_roic_col], nan_series)
    if int(pd.to_numeric(ebitda_roic_src, errors="coerce").notna().sum()) > 0:
        ebitda_roic = _robust_zscore(ebitda_roic_src)
    else:
        ebitda_z = _robust_zscore(ebitda_raw)
        roic_z = _robust_zscore(roic_raw)
        ebitda_roic = pd.concat([ebitda_z, roic_z], axis=1).mean(axis=1, skipna=True)

    gm_raw = _first_nonempty_series(
        ["gm_accel_q", "operating_margin_delta_q", ebitda_col],
        nan_series,
    )
    gm_z = _robust_zscore(gm_raw)

    revenue_raw = _first_nonempty_series(
        [revenue_col, "revenue_growth_yoy", "revenue_growth_lag"],
        nan_series,
    )
    revenue_z = _robust_zscore(revenue_raw)

    metric_df = pd.DataFrame(
        {
            "ebitda_roic_accel": ebitda_roic,
            "gm_accel_proxy": gm_z,
            "revenue_growth_proxy": revenue_z,
        },
        index=idx,
    )
    missing_quality = metric_df.isna().any(axis=1)
    composite = metric_df.mean(axis=1, skipna=True)
    if int(composite.notna().sum()) < 3:
        return (
            pd.Series(False, index=idx, dtype=bool),
            -1,
            missing_quality.astype(bool),
        )

    comp_rank = composite.rank(method="average", pct=True)
    bucket = pd.Series(np.nan, index=idx, dtype=float)
    bucket.loc[comp_rank <= (1.0 / 3.0)] = 0.0
    bucket.loc[(comp_rank > (1.0 / 3.0)) & (comp_rank <= (2.0 / 3.0))] = 1.0
    bucket.loc[comp_rank > (2.0 / 3.0)] = 2.0
    if int(bucket.notna().sum()) < 3:
        return (
            pd.Series(False, index=idx, dtype=bool),
            -1,
            missing_quality.astype(bool),
        )

    med = (
        metric_df.assign(_bucket=bucket)
        .dropna(subset=["_bucket"])
        .groupby("_bucket", sort=True)[["ebitda_roic_accel", "gm_accel_proxy", "revenue_growth_proxy"]]
        .median()
    )
    if med.empty:
        return (
            pd.Series(False, index=idx, dtype=bool),
            -1,
            missing_quality.astype(bool),
        )
    junk_score = med.sum(axis=1, skipna=True)
    junk_score = junk_score[np.isfinite(junk_score)]
    if junk_score.empty:
        return (
            pd.Series(False, index=idx, dtype=bool),
            -1,
            missing_quality.astype(bool),
        )
    junk_id = int(float(junk_score.idxmin()))
    mask = bucket.eq(float(junk_id)).fillna(False)
    return mask.astype(bool), junk_id, missing_quality.astype(bool)




def rank_ticker_pool(
    frame: pd.DataFrame,
    *,
    date_col: str = "date",
    permno_col: str = "permno",
    ticker_col: str = "ticker",
    sector_col: str = "sector",
    score_col: str = "score",
    style_gate_col: str = "style_compounder_gate",
    weak_ql_col: str = "weak_quality_liquidity",
    config: TickerPoolConfig | None = None,
) -> pd.DataFrame:
    """
    Golden-Master rollback path:
    use raw geometry cluster scoring only and avoid matrix/z-score rank machinery.
    """

    cfg = config or TickerPoolConfig()
    _assert_pre_pool_score_col(score_col)
    allow_features, deny_features = _resolve_path1_feature_partition(cfg)
    _assert_geometry_excludes_risk(cfg.feature_columns, context="feature_columns")
    _assert_geometry_excludes_risk(allow_features, context="path1_allow_features")

    required = {date_col, permno_col}
    miss = sorted(required - set(frame.columns))
    if miss:
        raise ValueError(f"Missing required columns: {miss}")

    needed_cols = [date_col, permno_col, ticker_col, sector_col, score_col, style_gate_col, weak_ql_col, *cfg.feature_columns]
    present_cols = [c for c in needed_cols if c in frame.columns]
    work = frame.loc[:, present_cols].copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    bad_date_count = int(work[date_col].isna().sum())
    if bad_date_count > 0:
        raise ValueError(
            f"{date_col} contains {bad_date_count} non-coercible rows; "
            "fix malformed date values before calling rank_ticker_pool"
        )
    work[permno_col] = pd.to_numeric(work[permno_col], errors="coerce")
    if ticker_col not in work.columns:
        work[ticker_col] = pd.NA
    if sector_col not in work.columns:
        work[sector_col] = "UNKNOWN"
    if style_gate_col not in work.columns:
        work[style_gate_col] = False
    if weak_ql_col not in work.columns:
        work[weak_ql_col] = False
    if score_col not in work.columns:
        work[score_col] = np.nan

    work[style_gate_col] = _normalize_boolean_series(work[style_gate_col], default=False)
    work[weak_ql_col] = _normalize_boolean_series(work[weak_ql_col], default=False)
    for col in cfg.feature_columns:
        if col not in work.columns:
            work[col] = np.nan
        work[col] = pd.to_numeric(work[col], errors="coerce")

    out = pd.DataFrame(index=work.index)
    out["mahalanobis_distance"] = np.nan
    out["mahalanobis_k_cyc"] = np.nan
    out["compounder_prob"] = np.nan
    out["pool_long_candidate"] = False
    out["pool_short_candidate"] = False
    out["pool_action"] = "WAIT"
    out["posterior_cyclical"] = np.nan
    out["posterior_defensive"] = np.nan
    out["posterior_junk"] = np.nan
    out["posterior_negative"] = np.nan
    out["odds_ratio"] = np.nan
    out["odds_score"] = np.nan
    out["defensive_cluster_id"] = -1
    out["junk_cluster_id"] = -1
    out["shrinkage_method"] = "golden_master_raw_geometry"
    out["shrinkage_coeff"] = 0.0
    out["centroid_source"] = "legacy_topk_raw_geometry"
    out["centroid_quarter"] = pd.NA
    out["centroid_knn_count"] = 0
    out["centroid_seed_used"] = ""
    out["centroid_seed_missing"] = ""
    out["dictatorship_mode"] = False
    out["path1_feature_allow"] = ",".join(allow_features)
    out["path1_feature_deny"] = ",".join(deny_features)
    out["path1_residualization"] = "not_run_raw_geometry"
    out["path1_sector_count"] = 0
    out["path1_cov_resample"] = "not_run_raw_geometry"
    out["path1_cov_resample_n"] = 0
    out["path1_cov_resample_per_sector"] = 0
    out["path1_cov_resample_seed"] = -1
    out["geometry_universe_before_imputation"] = 0
    out["geometry_universe_after_imputation"] = 0
    out["geometry_industry_impute_cells"] = 0
    out["geometry_sector_impute_cells"] = 0
    out["geometry_zero_impute_cells"] = 0

    anchor_set = {t.upper() for t in CYCLICAL_ANCHORS}

    for current_date, block in work.groupby(date_col, sort=True):
        gi = block.index
        if len(block) < int(cfg.min_universe):
            logger.warning(
                "Skipping date slice %s: universe size %d < min_universe %d.",
                str(pd.Timestamp(current_date).date()),
                int(len(block)),
                int(cfg.min_universe),
            )
            continue

        raw = pd.DataFrame(
            {
                "CycleSetup": pd.to_numeric(block.get("CycleSetup"), errors="coerce"),
                "op_lev": pd.to_numeric(block.get("op_lev"), errors="coerce"),
                "rev_accel": pd.to_numeric(block.get("rev_accel"), errors="coerce"),
                "inv_vel_traj": pd.to_numeric(block.get("inv_vel_traj"), errors="coerce"),
                "q_tot": pd.to_numeric(block.get("q_tot"), errors="coerce"),
            },
            index=block.index,
        )
        row_data_count = raw.notna().sum(axis=1)
        filled = raw.copy()
        for col in filled.columns:
            col_s = filled[col]
            if bool(col_s.notna().any()):
                med = float(col_s.median(skipna=True))
                filled[col] = col_s.fillna(med)
            else:
                filled[col] = 0.0
        cluster_score = (
            (2.0 * filled["CycleSetup"])
            + filled["op_lev"]
            + filled["rev_accel"]
            + filled["inv_vel_traj"]
            - filled["q_tot"]
        )
        valid = row_data_count >= 1
        valid_n = int(valid.sum())
        if valid_n < int(cfg.min_universe):
            logger.warning(
                "Skipping date slice %s: valid geometry rows %d < min_universe %d.",
                str(pd.Timestamp(current_date).date()),
                valid_n,
                int(cfg.min_universe),
            )
            continue

        score_valid = cluster_score.loc[valid].astype(float)
        candidate_idx = score_valid.index

        # Golden-Master fallback: avoid sparse top-k starvation by using a broad
        # raw-geometry long candidate set keyed off long_prob_threshold.
        pct_rank_desc = score_valid.rank(method="average", ascending=False, pct=True)
        long_cut = float(np.clip(1.0 - float(cfg.long_prob_threshold), 0.05, 0.95))
        long_candidate = pct_rank_desc <= long_cut

        prob_rank = score_valid.rank(method="average", ascending=True, pct=True)
        prob = prob_rank.clip(lower=0.0, upper=1.0).astype(float)
        distance = (1.0 - prob).clip(lower=0.0, upper=1.0)
        eps = float(max(1e-8, cfg.odds_epsilon))
        odds_ratio = prob / ((1.0 - prob) + eps)

        short_q = float(np.clip(1.0 - float(cfg.short_distance_quantile), 0.0, 1.0))
        short_cut = float(score_valid.quantile(short_q))
        weak_quality = _normalize_boolean_series(block.loc[score_valid.index, weak_ql_col], default=False)
        short_candidate = weak_quality & score_valid.le(short_cut) & (~long_candidate)

        action = pd.Series("WAIT", index=score_valid.index, dtype=object)
        action.loc[score_valid.le(short_cut)] = "AVOID"
        action.loc[short_candidate] = "SHORT"
        action.loc[long_candidate] = "LONG"

        posterior_cyc = prob
        posterior_def = ((1.0 - prob) * 0.5).clip(lower=0.0, upper=1.0)
        posterior_junk = ((1.0 - prob) * 0.5 + short_candidate.astype(float) * 0.5).clip(lower=0.0, upper=1.0)
        posterior_neg = (1.0 - posterior_cyc).clip(lower=0.0, upper=1.0)

        used = (
            block.loc[score_valid.index, ticker_col]
            .astype(str)
            .str.upper()
            .loc[lambda s: s.isin(anchor_set)]
            .drop_duplicates()
            .tolist()
        )
        missing = sorted(anchor_set.difference(set(used)))

        out.loc[score_valid.index, "mahalanobis_distance"] = distance
        out.loc[score_valid.index, "mahalanobis_k_cyc"] = distance
        out.loc[score_valid.index, "compounder_prob"] = prob
        out.loc[score_valid.index, "pool_long_candidate"] = long_candidate.astype(bool)
        out.loc[score_valid.index, "pool_short_candidate"] = short_candidate.astype(bool)
        out.loc[score_valid.index, "pool_action"] = action.astype(str)
        out.loc[score_valid.index, "posterior_cyclical"] = posterior_cyc.astype(float)
        out.loc[score_valid.index, "posterior_defensive"] = posterior_def.astype(float)
        out.loc[score_valid.index, "posterior_junk"] = posterior_junk.astype(float)
        out.loc[score_valid.index, "posterior_negative"] = posterior_neg.astype(float)
        out.loc[score_valid.index, "odds_ratio"] = odds_ratio.astype(float)
        out.loc[score_valid.index, "odds_score"] = score_valid.astype(float)
        out.loc[score_valid.index, "defensive_cluster_id"] = 0
        out.loc[score_valid.index, "junk_cluster_id"] = 0

        out.loc[gi, "centroid_quarter"] = str(_quarter_key(pd.Timestamp(current_date)))
        out.loc[gi, "centroid_knn_count"] = int(len(candidate_idx))
        out.loc[gi, "centroid_seed_used"] = ",".join(used)
        out.loc[gi, "centroid_seed_missing"] = ",".join(missing)
        out.loc[gi, "path1_sector_count"] = int(block[sector_col].astype(str).nunique())
        out.loc[gi, "path1_cov_resample_n"] = int(valid_n)
        out.loc[gi, "path1_cov_resample_seed"] = int(_date_seed(pd.Timestamp(current_date)))
        out.loc[gi, "geometry_universe_before_imputation"] = int(valid_n)
        out.loc[gi, "geometry_universe_after_imputation"] = int(valid_n)

    out["pool_long_candidate"] = pd.to_numeric(out["pool_long_candidate"], errors="coerce").fillna(False).astype(bool)
    out["pool_short_candidate"] = pd.to_numeric(out["pool_short_candidate"], errors="coerce").fillna(False).astype(bool)
    out["pool_action"] = out["pool_action"].astype(str)
    out["mahalanobis_k_cyc"] = pd.to_numeric(out["mahalanobis_k_cyc"], errors="coerce")
    out["posterior_cyclical"] = pd.to_numeric(out["posterior_cyclical"], errors="coerce")
    out["posterior_defensive"] = pd.to_numeric(out["posterior_defensive"], errors="coerce")
    out["posterior_junk"] = pd.to_numeric(out["posterior_junk"], errors="coerce")
    out["posterior_negative"] = pd.to_numeric(out["posterior_negative"], errors="coerce")
    out["odds_ratio"] = pd.to_numeric(out["odds_ratio"], errors="coerce")
    out["odds_score"] = pd.to_numeric(out["odds_score"], errors="coerce")
    out["defensive_cluster_id"] = pd.to_numeric(out["defensive_cluster_id"], errors="coerce").fillna(-1).astype(int)
    out["junk_cluster_id"] = pd.to_numeric(out["junk_cluster_id"], errors="coerce").fillna(-1).astype(int)
    out["centroid_knn_count"] = pd.to_numeric(out["centroid_knn_count"], errors="coerce").fillna(0).astype(int)
    out["dictatorship_mode"] = pd.to_numeric(out["dictatorship_mode"], errors="coerce").fillna(False).astype(bool)
    out["path1_residualization"] = out["path1_residualization"].astype(str)
    out["path1_sector_count"] = pd.to_numeric(out["path1_sector_count"], errors="coerce").fillna(0).astype(int)
    out["path1_cov_resample"] = out["path1_cov_resample"].astype(str)
    out["path1_cov_resample_n"] = pd.to_numeric(out["path1_cov_resample_n"], errors="coerce").fillna(0).astype(int)
    out["path1_cov_resample_per_sector"] = (
        pd.to_numeric(out["path1_cov_resample_per_sector"], errors="coerce").fillna(0).astype(int)
    )
    out["path1_cov_resample_seed"] = (
        pd.to_numeric(out["path1_cov_resample_seed"], errors="coerce").fillna(-1).astype(int)
    )
    out["geometry_universe_before_imputation"] = (
        pd.to_numeric(out["geometry_universe_before_imputation"], errors="coerce").fillna(0).astype(int)
    )
    out["geometry_universe_after_imputation"] = (
        pd.to_numeric(out["geometry_universe_after_imputation"], errors="coerce").fillna(0).astype(int)
    )
    out["geometry_industry_impute_cells"] = (
        pd.to_numeric(out["geometry_industry_impute_cells"], errors="coerce").fillna(0).astype(int)
    )
    out["geometry_sector_impute_cells"] = (
        pd.to_numeric(out["geometry_sector_impute_cells"], errors="coerce").fillna(0).astype(int)
    )
    out["geometry_zero_impute_cells"] = (
        pd.to_numeric(out["geometry_zero_impute_cells"], errors="coerce").fillna(0).astype(int)
    )
    return out
