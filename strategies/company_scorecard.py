"""
Phase 18 Day 4 — Company scorecard engine.

Implements linear multi-factor scores with cross-sectional normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from strategies.factor_specs import FactorSpec
from strategies.factor_specs import build_default_factor_specs
from strategies.factor_specs import build_phase19_5_candidate_factor_sets
from strategies.factor_specs import build_phase35_wave1_candidate_specs
from strategies.factor_specs import regime_adaptive_norm
from strategies.factor_specs import regime_veto
from strategies.factor_specs import validate_factor_specs
from strategies.ticker_pool import TickerPoolConfig
from strategies.ticker_pool import rank_ticker_pool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SECTOR_MAP_PATH = PROJECT_ROOT / "data" / "static" / "sector_map.parquet"
logger = logging.getLogger(__name__)


PHASE35_PRESETS = {
    "PHASE35_W1_CANDIDATES": build_phase35_wave1_candidate_specs(),
    # Wave 2/3 will be added later
}


@dataclass(frozen=True)
class ScorecardRunSummary:
    n_rows: int
    n_dates: int
    coverage: float
    missing_factor_columns: tuple[str, ...]
    scoring_method: str


ScoringMethod = Literal["complete_case", "partial", "impute_neutral"]


def _clean_context_text(values: pd.Series) -> pd.Series:
    out = values.astype("string").str.strip()
    upper = out.str.upper()
    out = out.mask(
        out.isna()
        | (out == "")
        | upper.isin({"UNKNOWN", "NAN", "NONE", "<NA>"}),
        pd.NA,
    )
    return out


def _clean_ticker(values: pd.Series) -> pd.Series:
    out = values.astype("string").str.strip().str.upper()
    out = out.mask(out.isna() | (out == "") | out.isin({"NAN", "NONE", "<NA>"}), pd.NA)
    return out


def _empty_context_maps() -> tuple[pd.DataFrame, pd.DataFrame]:
    by_permno = pd.DataFrame(columns=["permno", "sector", "industry", "industry_group"])
    by_ticker = pd.DataFrame(columns=["ticker_u", "sector", "industry", "industry_group"])
    return by_permno, by_ticker


@lru_cache(maxsize=2)
def _load_sector_context_maps(
    sector_map_path: Path = DEFAULT_SECTOR_MAP_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not sector_map_path.exists():
        return _empty_context_maps()
    try:
        context = pd.read_parquet(sector_map_path)
    except Exception as exc:
        logger.warning("Failed reading sector map at %s: %s", str(sector_map_path), str(exc))
        return _empty_context_maps()
    if context.empty:
        return _empty_context_maps()

    work = context.copy()
    for col in ["ticker", "permno", "sector", "industry", "industry_group", "updated_at"]:
        if col not in work.columns:
            work[col] = pd.NA

    work["ticker_u"] = _clean_ticker(work["ticker"])
    work["permno"] = pd.to_numeric(work["permno"], errors="coerce")
    work["sector"] = _clean_context_text(work["sector"])
    work["industry"] = _clean_context_text(work["industry"])
    work["industry_group"] = _clean_context_text(work["industry_group"])
    work["updated_at"] = pd.to_datetime(work["updated_at"], errors="coerce", utc=True)
    work = work[(work["sector"].notna()) | (work["industry"].notna()) | (work["industry_group"].notna())]
    if work.empty:
        return _empty_context_maps()

    work = work.sort_values(
        ["updated_at", "industry_group", "industry", "ticker_u", "permno"],
        ascending=[False, True, True, True, True],
        na_position="last",
    )

    by_permno = (
        work[work["permno"].notna()][["permno", "sector", "industry", "industry_group"]]
        .drop_duplicates(subset=["permno"], keep="first")
        .reset_index(drop=True)
    )
    by_ticker = (
        work[work["ticker_u"].notna()][["ticker_u", "sector", "industry", "industry_group"]]
        .drop_duplicates(subset=["ticker_u"], keep="first")
        .reset_index(drop=True)
    )
    return by_permno, by_ticker


def _attach_sector_industry_context(
    frame: pd.DataFrame,
    sector_map_path: Path = DEFAULT_SECTOR_MAP_PATH,
) -> pd.DataFrame:
    if frame.empty:
        out = frame.copy()
        out["sector"] = pd.Series(dtype="object")
        out["industry"] = pd.Series(dtype="object")
        out["sector_context_source"] = pd.Series(dtype="object")
        out["path1_sector_context_attached"] = pd.Series(dtype=bool)
        return out

    by_permno, by_ticker = _load_sector_context_maps(sector_map_path=sector_map_path)
    by_permno = by_permno.copy()
    by_ticker = by_ticker.copy()
    out = frame.copy()
    out["ticker_u"] = _clean_ticker(out["ticker"])

    by_permno = by_permno.rename(
        columns={
            "sector": "sector_permno",
            "industry": "industry_permno",
            "industry_group": "industry_group_permno",
        }
    )
    by_ticker = by_ticker.rename(
        columns={
            "sector": "sector_ticker",
            "industry": "industry_ticker",
            "industry_group": "industry_group_ticker",
        }
    )
    out = out.merge(by_permno, on="permno", how="left")
    out = out.merge(by_ticker, on="ticker_u", how="left")

    sector_permno = _clean_context_text(out["sector_permno"])
    sector_ticker = _clean_context_text(out["sector_ticker"])
    industry_permno = _clean_context_text(out["industry_permno"])
    industry_ticker = _clean_context_text(out["industry_ticker"])
    industry_group_permno = _clean_context_text(out["industry_group_permno"])
    industry_group_ticker = _clean_context_text(out["industry_group_ticker"])

    out["sector"] = sector_permno.combine_first(sector_ticker).fillna("Unknown")
    out["industry"] = industry_permno.combine_first(industry_ticker).fillna("Unknown")
    out["industry_group"] = industry_group_permno.combine_first(industry_group_ticker).fillna("Unknown")
    has_permno_context = sector_permno.notna() | industry_permno.notna() | industry_group_permno.notna()
    has_ticker_context = sector_ticker.notna() | industry_ticker.notna() | industry_group_ticker.notna()
    out["sector_context_source"] = np.where(
        has_permno_context,
        "permno",
        np.where(has_ticker_context, "ticker", "unknown"),
    )
    out["path1_sector_context_attached"] = (out["sector_context_source"] != "unknown").astype(bool)

    out.drop(
        columns=[
            "ticker_u",
            "sector_permno",
            "industry_permno",
            "industry_group_permno",
            "sector_ticker",
            "industry_ticker",
            "industry_group_ticker",
        ],
        inplace=True,
        errors="ignore",
    )
    return out


class CompanyScorecard:
    """
    Linear scorecard:
      score = sum(weight_k * sign_k * normalized_factor_k)
    """

    def __init__(
        self,
        factor_specs: list[FactorSpec] | None = None,
        date_col: str = "date",
        permno_col: str = "permno",
        scoring_method: ScoringMethod = "complete_case",
        regime_by_date: pd.Series | None = None,
        strict_red_veto: bool = False,
        veto_regimes: tuple[str, ...] = ("RED",),
    ):
        specs = factor_specs if factor_specs is not None else build_default_factor_specs()
        validate_factor_specs(specs)
        self.factor_specs = specs
        self.date_col = date_col
        self.permno_col = permno_col
        self.scoring_method: ScoringMethod = self._validate_scoring_method(scoring_method)
        if regime_by_date is None:
            self.regime_by_date = None
        else:
            regime_map = pd.Series(regime_by_date).copy()
            regime_map.index = pd.to_datetime(regime_map.index, errors="coerce")
            regime_map = regime_map[~regime_map.index.isna()]
            self.regime_by_date = regime_map
        self.strict_red_veto = bool(strict_red_veto)
        self.veto_regimes = tuple(str(x).upper() for x in veto_regimes)

    @classmethod
    def from_factor_preset(
        cls,
        preset_name: str,
        *,
        scoring_method: ScoringMethod = "complete_case",
        date_col: str = "date",
        permno_col: str = "permno",
    ) -> "CompanyScorecard":
        """
        Build scorecard from named preset.
        Supported presets:
          - DEFAULT_DAY4
          - P195_SIGNAL_STRENGTH_4F
          - P195_SIGNAL_STRENGTH_5F
          - P195_SIGNAL_STRENGTH_4F_RANK
          - PHASE35_W1_CANDIDATES
        """

        key = str(preset_name).strip().upper()
        if key in PHASE35_PRESETS:
            specs = PHASE35_PRESETS[key]
        elif key == "DEFAULT_DAY4":
            specs = build_default_factor_specs()
        else:
            phase19_sets = {
                k.upper(): v for k, v in build_phase19_5_candidate_factor_sets().items()
            }
            if key not in phase19_sets:
                supported = ["DEFAULT_DAY4"] + sorted(phase19_sets.keys()) + sorted(PHASE35_PRESETS.keys())
                raise ValueError(
                    f"Unsupported preset_name={preset_name}. Supported={supported}"
                )
            specs = phase19_sets[key]
        return cls(
            factor_specs=list(specs),
            date_col=date_col,
            permno_col=permno_col,
            scoring_method=scoring_method,
        )

    @staticmethod
    def _as_numeric(series: pd.Series) -> pd.Series:
        out = pd.to_numeric(series, errors="coerce")
        return out.replace([np.inf, -np.inf], np.nan)

    def _normalize(self, values: pd.Series, date_index: pd.Series, method: str) -> pd.Series:
        if method == "raw":
            return values

        grp = values.groupby(date_index)
        if method == "zscore":
            mu = grp.transform("mean")
            sigma = grp.transform("std").replace(0.0, np.nan)
            return (values - mu) / sigma
        if method == "rank":
            return values.groupby(date_index).rank(pct=True, method="average")
        if method == "regime_adaptive":
            return regime_adaptive_norm(
                values=values,
                date_index=date_index,
                regime_by_date=self.regime_by_date,
            )
        raise ValueError(f"Unsupported normalization method: {method}")

    def _apply_control_toggles(self, raw: pd.Series, permno_index: pd.Series, spec: FactorSpec) -> pd.Series:
        out = raw.copy()

        if spec.use_dirty_derivative:
            deriv = out.groupby(permno_index).diff()
            out = out + float(spec.derivative_weight) * deriv.fillna(0.0)

        if spec.use_leaky_integrator:
            out = out.groupby(permno_index).transform(
                lambda s: s.ewm(alpha=float(spec.leaky_alpha), adjust=False, min_periods=1).mean()
            )

        if spec.use_sigmoid_blend:
            z = out.copy()
            sigma = pd.to_numeric(z, errors="coerce").std(skipna=True)
            scale = max(float(sigma), 1e-9)
            z = (z / scale).clip(lower=-50.0, upper=50.0)
            out = 2.0 / (1.0 + np.exp(-float(spec.sigmoid_k) * z)) - 1.0

        return out

    @staticmethod
    def _validate_scoring_method(scoring_method: str) -> ScoringMethod:
        allowed = {"complete_case", "partial", "impute_neutral"}
        method = str(scoring_method).strip().lower()
        if method not in allowed:
            raise ValueError(
                f"Unsupported scoring_method={scoring_method}. "
                f"Expected one of {sorted(allowed)}."
            )
        return method  # type: ignore[return-value]

    def compute_scores(self, features_df: pd.DataFrame) -> tuple[pd.DataFrame, ScorecardRunSummary]:
        if not isinstance(features_df, pd.DataFrame):
            raise TypeError("features_df must be a pandas DataFrame")
        required = {self.date_col, self.permno_col}
        missing_required = sorted(required - set(features_df.columns))
        if missing_required:
            raise ValueError(f"Missing required columns: {missing_required}")

        work = features_df.copy()
        work[self.date_col] = pd.to_datetime(work[self.date_col], errors="coerce")
        work[self.permno_col] = pd.to_numeric(work[self.permno_col], errors="coerce")
        work = work.dropna(subset=[self.date_col, self.permno_col]).sort_values([self.date_col, self.permno_col])
        if work.empty:
            empty = pd.DataFrame(columns=[self.date_col, self.permno_col, "score"])
            summary = ScorecardRunSummary(
                n_rows=0,
                n_dates=0,
                coverage=0.0,
                missing_factor_columns=tuple(),
                scoring_method=self.scoring_method,
            )
            return empty, summary

        available = set(work.columns)
        date_idx = work[self.date_col]
        permno_idx = work[self.permno_col]

        out = work[[self.date_col, self.permno_col]].copy()
        missing_cols: list[str] = []
        contrib_by_factor: dict[str, pd.Series] = {}
        valid_by_factor: dict[str, pd.Series] = {}
        weight_by_factor: dict[str, float] = {}

        for spec in self.factor_specs:
            resolved_col = spec.resolve_feature_column(available)
            if resolved_col is None:
                missing_cols.append(spec.name)
                contrib = pd.Series(np.nan, index=work.index, dtype=float)
                norm = pd.Series(np.nan, index=work.index, dtype=float)
                out[f"{spec.name}_source"] = pd.Series(pd.NA, index=work.index, dtype="object")
                out[f"{spec.name}_normalized"] = norm
                out[f"{spec.name}_contrib"] = contrib
                contrib_by_factor[spec.name] = contrib
                valid_by_factor[spec.name] = pd.Series(False, index=work.index, dtype=bool)
                weight_by_factor[spec.name] = float(spec.weight)
                continue

            raw = self._as_numeric(work[resolved_col])
            raw = self._apply_control_toggles(raw=raw, permno_index=permno_idx, spec=spec)
            norm = self._normalize(values=raw, date_index=date_idx, method=spec.normalization)
            sign = 1.0 if spec.direction == "positive" else -1.0
            contrib = sign * float(spec.weight) * norm

            out[f"{spec.name}_source"] = resolved_col
            out[f"{spec.name}_normalized"] = norm
            out[f"{spec.name}_contrib"] = contrib
            contrib_by_factor[spec.name] = contrib
            valid_by_factor[spec.name] = norm.notna()
            weight_by_factor[spec.name] = float(spec.weight)

        contrib_df = pd.DataFrame(contrib_by_factor, index=work.index)
        valid_df = pd.DataFrame(valid_by_factor, index=work.index)
        weight_series = pd.Series(weight_by_factor, dtype=float)

        # Strict regime veto: block all score computation rows for vetoed regimes.
        if self.strict_red_veto:
            veto_mask = regime_veto(
                date_index=date_idx,
                regime_by_date=self.regime_by_date,
                blocked_regimes=self.veto_regimes,
            )
            if bool(veto_mask.any()):
                valid_df.loc[veto_mask, :] = False
                contrib_df.loc[veto_mask, :] = np.nan

        if self.scoring_method == "complete_case":
            row_valid = valid_df.all(axis=1)
            score = contrib_df.sum(axis=1, min_count=len(self.factor_specs)).where(row_valid, np.nan)
            for name in contrib_df.columns:
                out[f"{name}_contrib"] = contrib_df[name].where(row_valid, np.nan)
        elif self.scoring_method == "partial":
            row_valid = valid_df.any(axis=1)
            weighted_sum = contrib_df.fillna(0.0).sum(axis=1)
            available_weight = valid_df.mul(weight_series, axis=1).sum(axis=1).replace(0.0, np.nan)
            score = (weighted_sum / available_weight).where(row_valid, np.nan)
            scaled_contrib = contrib_df.div(available_weight, axis=0)
            for name in contrib_df.columns:
                out[f"{name}_contrib"] = scaled_contrib[name].where(row_valid, np.nan)
        else:
            # Impute-neutral keeps fixed weights and treats missing factors as zero contribution.
            row_valid = valid_df.any(axis=1)
            score = contrib_df.fillna(0.0).sum(axis=1).where(row_valid, np.nan)
            for name in contrib_df.columns:
                out[f"{name}_contrib"] = contrib_df[name].where(row_valid, np.nan)

        out["score_valid"] = row_valid.astype(bool)
        out["score"] = score
        coverage = float(row_valid.mean()) if len(out) else 0.0
        summary = ScorecardRunSummary(
            n_rows=int(len(out)),
            n_dates=int(out[self.date_col].nunique()),
            coverage=coverage,
            missing_factor_columns=tuple(sorted(set(missing_cols))),
            scoring_method=self.scoring_method,
        )
        return out, summary


def build_phase20_conviction_frame(
    scores_df: pd.DataFrame,
    features_df: pd.DataFrame,
    regime_by_date: pd.Series | None = None,
    *,
    support_sma_window: int = 200,
    momentum_lookback: int = 60,
    support_buffer: float = -0.05,
    dictatorship_mode: bool = True,
    ticker_pool_config: TickerPoolConfig | None = None,
) -> pd.DataFrame:
    """
    Build Phase 20 conviction features on top of score outputs.

    This helper is intentionally deterministic and PIT-safe:
    all tactical features are lagged by one bar before they influence
    conviction or entry decisions.
    """

    required_score = {"date", "permno", "score", "score_valid"}
    missing_score = sorted(required_score - set(scores_df.columns))
    if missing_score:
        raise ValueError(f"scores_df missing required columns: {missing_score}")

    required_feat = {"date", "permno", "ticker", "adj_close", "dist_sma20", "sma200"}
    missing_feat = sorted(required_feat - set(features_df.columns))
    if missing_feat:
        raise ValueError(f"features_df missing required columns: {missing_feat}")

    score_cols = ["date", "permno", "score", "score_valid"]
    feat_cols = [
        "date",
        "permno",
        "ticker",
        "adj_close",
        "dist_sma20",
        "sma200",
        "yz_vol_20d",
        "atr_14d",
        "revenue_growth_q",
        "revenue_growth_yoy",
        "resid_mom_60d",
        "z_inventory_quality_proxy",
        "capital_cycle_score",
        "amihud_20d",
        "ebitda_ttm",
        "roic",
        "gm_accel_q",
        "operating_margin_delta_q",
        "z_discipline_cond",
        "z_moat",
        "z_demand",
        # SDM manifold columns (Action 2)
        "rev_accel",
        "inv_vel_traj",
        "gm_traj",
        "op_lev",
        "intang_intensity",
        "q_tot",
        "rmw",
        "cma",
        "yield_slope_10y2y",
        "CycleSetup",
        "cycle_setup",
        "ind_rev_accel",
        "ind_inv_vel_traj",
        "ind_gm_traj",
        "ind_op_lev",
    ]
    work_feat = features_df.copy()
    for col in feat_cols:
        if col not in work_feat.columns:
            work_feat[col] = np.nan

    merged = (
        scores_df[score_cols]
        .merge(work_feat[feat_cols], on=["date", "permno"], how="left")
        .copy()
    )
    merged["date"] = pd.to_datetime(merged["date"], errors="coerce")
    merged["permno"] = pd.to_numeric(merged["permno"], errors="coerce")
    for col in [
        "score",
        "adj_close",
        "dist_sma20",
        "sma200",
        "yz_vol_20d",
        "atr_14d",
        "revenue_growth_q",
        "revenue_growth_yoy",
        "resid_mom_60d",
        "z_inventory_quality_proxy",
        "capital_cycle_score",
        "amihud_20d",
        "ebitda_ttm",
        "roic",
        "gm_accel_q",
        "operating_margin_delta_q",
        "z_discipline_cond",
        "z_moat",
        "z_demand",
        "rev_accel",
        "inv_vel_traj",
        "gm_traj",
        "op_lev",
        "intang_intensity",
        "q_tot",
        "rmw",
        "cma",
        "yield_slope_10y2y",
        "CycleSetup",
        "cycle_setup",
        "ind_rev_accel",
        "ind_inv_vel_traj",
        "ind_gm_traj",
        "ind_op_lev",
    ]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")
    merged["CycleSetup"] = merged["CycleSetup"].combine_first(merged["cycle_setup"])
    merged["score_valid"] = pd.to_numeric(merged["score_valid"], errors="coerce").fillna(False).astype(bool)
    merged = merged.dropna(subset=["date", "permno"]).sort_values(["permno", "date"]).reset_index(drop=True)
    merged = _attach_sector_industry_context(merged)

    # Restore bounded continuity for off-cycle names without leaking stale fundamentals.
    core_fundamental_cols = ["q_tot", "inv_vel_traj", "op_lev", "rev_accel", "CycleSetup"]
    for col in core_fundamental_cols:
        merged[col] = pd.to_numeric(
            merged.get(col, pd.Series(np.nan, index=merged.index, dtype=float)),
            errors="coerce",
        )
    merged.loc[:, core_fundamental_cols] = (
        merged.groupby("permno", sort=False)[core_fundamental_cols].ffill(limit=120)
    )
    merged["cycle_setup"] = pd.to_numeric(
        merged.get("cycle_setup", pd.Series(np.nan, index=merged.index, dtype=float)),
        errors="coerce",
    ).combine_first(merged["CycleSetup"])

    price_g = merged.groupby("permno", sort=False)["adj_close"]
    sma200_g = merged.groupby("permno", sort=False)["sma200"]
    dist_sma20_g = merged.groupby("permno", sort=False)["dist_sma20"]
    mom_g = merged.groupby("permno", sort=False)["resid_mom_60d"]
    yzvol_g = merged.groupby("permno", sort=False)["yz_vol_20d"]
    atr_g = merged.groupby("permno", sort=False)["atr_14d"]
    rev_g = merged.groupby("permno", sort=False)["revenue_growth_q"]
    invq_g = merged.groupby("permno", sort=False)["z_inventory_quality_proxy"]
    ccycle_g = merged.groupby("permno", sort=False)["capital_cycle_score"]
    amihud_g = merged.groupby("permno", sort=False)["amihud_20d"]
    ebitda_g = merged.groupby("permno", sort=False)["ebitda_ttm"]
    roic_g = merged.groupby("permno", sort=False)["roic"]
    om_delta_g = merged.groupby("permno", sort=False)["operating_margin_delta_q"]
    zdisc_g = merged.groupby("permno", sort=False)["z_discipline_cond"]
    zmoat_g = merged.groupby("permno", sort=False)["z_moat"]
    zdemand_g = merged.groupby("permno", sort=False)["z_demand"]
    rev_accel_sdm_g = merged.groupby("permno", sort=False)["rev_accel"]
    inv_vel_traj_g = merged.groupby("permno", sort=False)["inv_vel_traj"]
    gm_traj_sdm_g = merged.groupby("permno", sort=False)["gm_traj"]
    op_lev_sdm_g = merged.groupby("permno", sort=False)["op_lev"]
    intang_intensity_g = merged.groupby("permno", sort=False)["intang_intensity"]
    q_tot_g = merged.groupby("permno", sort=False)["q_tot"]
    rmw_g = merged.groupby("permno", sort=False)["rmw"]
    cma_g = merged.groupby("permno", sort=False)["cma"]
    slope_g = merged.groupby("permno", sort=False)["yield_slope_10y2y"]
    cycle_setup_g = merged.groupby("permno", sort=False)["CycleSetup"]
    ind_rev_accel_g = merged.groupby("permno", sort=False)["ind_rev_accel"]
    ind_inv_vel_traj_g = merged.groupby("permno", sort=False)["ind_inv_vel_traj"]
    ind_gm_traj_g = merged.groupby("permno", sort=False)["ind_gm_traj"]
    ind_op_lev_g = merged.groupby("permno", sort=False)["ind_op_lev"]

    momentum_window = int(max(2, momentum_lookback))
    support_floor = float(support_buffer)

    momentum_signal = price_g.transform(
        lambda s: s.pct_change(periods=momentum_window, fill_method=None)
    )

    # Golden-Master gate contract: keep strict lagging but use canonical feature gates.
    support_proximity = (price_g.shift(1) > sma200_g.shift(1)) & (dist_sma20_g.shift(1) > support_floor)
    mom_ok = mom_g.shift(1) > 0.0
    quality_lag = invq_g.shift(1)
    capital_cycle_lag = ccycle_g.shift(1)
    resid_mom_lag = momentum_signal.shift(1)
    revenue_growth_lag = rev_g.shift(1).fillna(zdemand_g.shift(1))
    realized_vol_lag = yzvol_g.shift(1).fillna(atr_g.shift(1))
    liquidity_lag = amihud_g.shift(1)

    quality_med = quality_lag.groupby(merged["date"], sort=False).transform("median")
    liquidity_med = liquidity_lag.groupby(merged["date"], sort=False).transform("median")
    quality_above_median = quality_lag >= quality_med
    liquidity_above_median = liquidity_lag <= liquidity_med

    quality_ok = (quality_lag > 0.0) | (capital_cycle_lag > 0.0)
    illiquid_flag = liquidity_lag > liquidity_lag.groupby(merged["date"], sort=False).transform("quantile", q=0.80)

    # EBITDA/ROIC acceleration: use quarterly-ish lag delta, then fallback to proxies.
    ebitda_accel = ebitda_g.diff(63).shift(1)
    roic_accel = roic_g.diff(63).shift(1)
    ebitda_proxy = om_delta_g.shift(1)
    roic_proxy = zmoat_g.shift(1).where(zmoat_g.shift(1).notna(), zdemand_g.shift(1))
    ebitda_accel = ebitda_accel.fillna(ebitda_proxy).fillna(zdisc_g.shift(1))
    roic_accel = roic_accel.fillna(roic_proxy)
    sdm_rev_accel_lag = rev_accel_sdm_g.shift(1)
    sdm_inv_vel_traj_lag = inv_vel_traj_g.shift(1)
    sdm_gm_traj_lag = gm_traj_sdm_g.shift(1)
    sdm_op_lev_lag = op_lev_sdm_g.shift(1)
    sdm_intang_lag = intang_intensity_g.shift(1)
    sdm_q_tot_lag = q_tot_g.shift(1)
    sdm_rmw_lag = rmw_g.shift(1)
    sdm_cma_lag = cma_g.shift(1)
    sdm_slope_lag = slope_g.shift(1)
    sdm_cycle_setup_lag = cycle_setup_g.shift(1)
    ind_rev_accel_lag = ind_rev_accel_g.shift(1)
    ind_inv_vel_traj_lag = ind_inv_vel_traj_g.shift(1)
    ind_gm_traj_lag = ind_gm_traj_g.shift(1)
    ind_op_lev_lag = ind_op_lev_g.shift(1)

    style_compounder_gate = (
        (capital_cycle_lag > 0.5)
        & (ebitda_accel > 0.0)
        & (roic_accel > 0.0)
        & quality_above_median.fillna(False)
        & liquidity_above_median.fillna(False)
        & mom_ok.fillna(False)
    )
    weak_quality_liquidity = (~quality_above_median.fillna(False)) | (~liquidity_above_median.fillna(False))

    merged["score_pct"] = merged.groupby("date", sort=False)["score"].rank(pct=True, method="average")
    raw_conviction = (
        5.0 * merged["score_pct"].fillna(0.0)
        + 2.0 * mom_ok.astype(float)
        + 2.0 * support_proximity.astype(float)
        + 1.0 * quality_ok.astype(float)
    )
    merged["conviction_score"] = raw_conviction.clip(lower=0.0, upper=10.0)
    merged["support_proximity"] = support_proximity.fillna(False).astype(bool)
    merged["mom_ok"] = mom_ok.fillna(False).astype(bool)
    merged["quality_ok"] = quality_ok.fillna(False).astype(bool)
    merged["illiquid_flag"] = illiquid_flag.fillna(False).astype(bool)
    merged["capital_cycle_lag"] = capital_cycle_lag
    merged["resid_mom_lag"] = resid_mom_lag
    merged["revenue_growth_lag"] = revenue_growth_lag
    merged["realized_vol_lag"] = realized_vol_lag
    merged["quality_lag"] = quality_lag
    merged["liquidity_score"] = -np.log1p(liquidity_lag.clip(lower=0.0))
    merged["ebitda_accel"] = ebitda_accel
    merged["roic_accel"] = roic_accel
    # Action 2 manifold routing: keep these lagged and PIT-safe for ticker-pool geometry.
    merged["rev_accel"] = sdm_rev_accel_lag
    merged["inv_vel_traj"] = sdm_inv_vel_traj_lag
    merged["gm_traj"] = sdm_gm_traj_lag
    merged["op_lev"] = sdm_op_lev_lag
    merged["intang_intensity"] = sdm_intang_lag
    merged["q_tot"] = sdm_q_tot_lag
    merged["rmw"] = sdm_rmw_lag
    merged["cma"] = sdm_cma_lag
    merged["yield_slope_10y2y"] = sdm_slope_lag
    merged["CycleSetup"] = sdm_cycle_setup_lag
    merged["cycle_setup"] = sdm_cycle_setup_lag
    merged["ind_rev_accel"] = ind_rev_accel_lag
    merged["ind_inv_vel_traj"] = ind_inv_vel_traj_lag
    merged["ind_gm_traj"] = ind_gm_traj_lag
    merged["ind_op_lev"] = ind_op_lev_lag
    merged["style_compounder_gate"] = style_compounder_gate.fillna(False).astype(bool)
    merged["weak_quality_liquidity"] = weak_quality_liquidity.fillna(False).astype(bool)

    if regime_by_date is None:
        merged["regime"] = "AMBER"
    else:
        reg = pd.Series(regime_by_date).copy()
        reg.index = pd.to_datetime(reg.index, errors="coerce")
        reg = reg[~reg.index.isna()]
        merged["regime"] = merged["date"].map(reg).fillna("AMBER").astype(str).str.upper()

    pool_cfg = ticker_pool_config or TickerPoolConfig(dictatorship_mode=bool(dictatorship_mode))

    pool = rank_ticker_pool(
        merged,
        date_col="date",
        permno_col="permno",
        ticker_col="ticker",
        sector_col="sector",
        score_col="score",
        style_gate_col="style_compounder_gate",
        weak_ql_col="weak_quality_liquidity",
        config=pool_cfg,
    )
    merged["mahalanobis_distance"] = pd.to_numeric(pool["mahalanobis_distance"], errors="coerce")
    merged["mahalanobis_k_cyc"] = pd.to_numeric(pool.get("mahalanobis_k_cyc"), errors="coerce")
    merged["compounder_prob"] = pd.to_numeric(pool["compounder_prob"], errors="coerce")
    merged["pool_long_candidate"] = pd.to_numeric(pool["pool_long_candidate"], errors="coerce").fillna(False).astype(bool)
    merged["pool_short_candidate"] = pd.to_numeric(pool["pool_short_candidate"], errors="coerce").fillna(False).astype(bool)
    merged["pool_action"] = pool["pool_action"].astype(str)
    merged["posterior_cyclical"] = pd.to_numeric(pool.get("posterior_cyclical"), errors="coerce")
    merged["posterior_defensive"] = pd.to_numeric(pool.get("posterior_defensive"), errors="coerce")
    merged["posterior_junk"] = pd.to_numeric(pool.get("posterior_junk"), errors="coerce")
    merged["posterior_negative"] = pd.to_numeric(pool.get("posterior_negative"), errors="coerce")
    merged["odds_ratio"] = pd.to_numeric(pool.get("odds_ratio"), errors="coerce")
    merged["odds_score"] = pd.to_numeric(pool.get("odds_score"), errors="coerce")
    merged["defensive_cluster_id"] = pd.to_numeric(pool.get("defensive_cluster_id"), errors="coerce").fillna(-1).astype(int)
    merged["junk_cluster_id"] = pd.to_numeric(pool.get("junk_cluster_id"), errors="coerce").fillna(-1).astype(int)
    merged["shrinkage_method"] = pool["shrinkage_method"].astype(str)
    merged["shrinkage_coeff"] = pd.to_numeric(pool["shrinkage_coeff"], errors="coerce")
    merged["centroid_source"] = pool["centroid_source"].astype(str)
    merged["centroid_quarter"] = pool["centroid_quarter"].astype(str)
    merged["centroid_knn_count"] = pd.to_numeric(pool["centroid_knn_count"], errors="coerce").fillna(0).astype(int)
    merged["centroid_seed_used"] = pool["centroid_seed_used"].astype(str)
    merged["centroid_seed_missing"] = pool["centroid_seed_missing"].astype(str)
    merged["dictatorship_mode"] = pd.to_numeric(pool.get("dictatorship_mode"), errors="coerce").fillna(False).astype(bool)
    merged["path1_feature_allow"] = pool.get("path1_feature_allow", pd.Series("", index=pool.index)).astype(str)
    merged["path1_feature_deny"] = pool.get("path1_feature_deny", pd.Series("", index=pool.index)).astype(str)
    merged["path1_residualization"] = pool.get("path1_residualization", pd.Series("not_run", index=pool.index)).astype(str)
    merged["path1_sector_count"] = pd.to_numeric(pool.get("path1_sector_count"), errors="coerce").fillna(0).astype(int)
    merged["path1_cov_resample"] = pool.get("path1_cov_resample", pd.Series("not_run", index=pool.index)).astype(str)
    merged["path1_cov_resample_n"] = pd.to_numeric(pool.get("path1_cov_resample_n"), errors="coerce").fillna(0).astype(int)
    merged["path1_cov_resample_per_sector"] = pd.to_numeric(
        pool.get("path1_cov_resample_per_sector"), errors="coerce"
    ).fillna(0).astype(int)
    merged["path1_cov_resample_seed"] = pd.to_numeric(pool.get("path1_cov_resample_seed"), errors="coerce").fillna(-1).astype(int)

    # Lift conviction when the Mahalanobis profile is close to compounder centroid.
    pool_boost = (merged["compounder_prob"].fillna(0.5) - 0.5) * 2.0
    merged["conviction_score"] = (merged["conviction_score"] + (1.5 * pool_boost)).clip(lower=0.0, upper=10.0)

    merged["entry_gate"] = (
        merged["score_valid"]
        & (merged["conviction_score"] >= 7.0)
        & merged["pool_long_candidate"]
        & merged["mom_ok"]
        & merged["support_proximity"]
    )

    # Final leverage slice: pure target-vol sizing + sigmoid jump veto + EMA smoothing,
    # then linear portfolio beta cap with strict net/gross and borrow-cost accounting.
    target_vol = 0.15
    leverage_min = 1.0
    leverage_max = 1.5
    jump_sigmoid_k = 30.0
    jump_sigmoid_x0 = 0.15
    leverage_ema_span = 10
    beta_cap_abs = 1.0
    borrow_rate_annual = 0.03
    annualization = np.sqrt(252.0)

    raw_ret = price_g.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    sigma_cont_raw = (
        raw_ret.groupby(merged["permno"], sort=False)
        .transform(lambda s: s.rolling(20, min_periods=5).std())
        * annualization
    )
    sigma_continuous = (
        sigma_cont_raw.groupby(merged["permno"], sort=False).shift(1)
        .replace([np.inf, -np.inf], np.nan)
        .fillna(realized_vol_lag.abs())
        .clip(lower=1e-6)
    )
    merged["sigma_continuous"] = sigma_continuous

    target_vol_ratio = (float(target_vol) / sigma_continuous).replace([np.inf, -np.inf], np.nan)
    leverage_target_raw = target_vol_ratio.clip(lower=leverage_min, upper=leverage_max).fillna(leverage_min)

    jump_proxy = (
        raw_ret.abs()
        .groupby(merged["permno"], sort=False)
        .shift(1)
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
    )
    jump_veto = 1.0 / (1.0 + np.exp((-float(jump_sigmoid_k)) * (jump_proxy - float(jump_sigmoid_x0))))
    merged["jump_veto_score"] = pd.to_numeric(jump_veto, errors="coerce").fillna(0.0).clip(lower=0.0, upper=1.0)

    leverage_eligible = merged["entry_gate"] & merged["mom_ok"] & merged["regime"].eq("GREEN")
    leverage_candidate = pd.Series(
        np.where(leverage_eligible, leverage_target_raw, leverage_min),
        index=merged.index,
        dtype=float,
    )
    leverage_post_veto = leverage_min + (leverage_candidate - leverage_min) * (1.0 - merged["jump_veto_score"])
    leverage_post_veto = leverage_post_veto.clip(lower=leverage_min, upper=leverage_max)

    leverage_smoothed = leverage_post_veto.groupby(merged["permno"], sort=False).transform(
        lambda s: s.ewm(span=int(leverage_ema_span), adjust=False, min_periods=1).mean()
    )
    leverage_smoothed = leverage_smoothed.clip(lower=leverage_min, upper=leverage_max)

    market_ret = raw_ret.groupby(merged["date"], sort=False).transform("mean").replace([np.inf, -np.inf], np.nan)
    beta_frame = pd.DataFrame(
        {
            "permno": merged["permno"],
            "asset_ret": raw_ret,
            "market_ret": market_ret,
        },
        index=merged.index,
    )
    beta_frame["asset_x_market"] = beta_frame["asset_ret"] * beta_frame["market_ret"]
    grp_beta = beta_frame.groupby("permno", sort=False)
    mean_asset = grp_beta["asset_ret"].rolling(60, min_periods=20).mean().reset_index(level=0, drop=True)
    mean_market = grp_beta["market_ret"].rolling(60, min_periods=20).mean().reset_index(level=0, drop=True)
    mean_asset_x_market = grp_beta["asset_x_market"].rolling(60, min_periods=20).mean().reset_index(level=0, drop=True)
    cov_asset_market = mean_asset_x_market - (mean_asset * mean_market)
    var_market = grp_beta["market_ret"].rolling(60, min_periods=20).var().reset_index(level=0, drop=True)
    beta_raw = cov_asset_market / var_market
    beta_lag = (
        pd.to_numeric(beta_raw, errors="coerce")
        .groupby(merged["permno"], sort=False)
        .shift(1)
        .replace([np.inf, -np.inf], np.nan)
        .fillna(1.0)
        .clip(lower=-3.0, upper=3.0)
    )
    merged["asset_beta_lag"] = beta_lag

    regime_u = merged["regime"].astype(str).str.upper()
    cash_pct = regime_u.map({"GREEN": 0.0, "AMBER": 0.25, "RED": 0.50}).fillna(0.25).astype(float)
    short_budget = regime_u.map({"GREEN": 0.20, "AMBER": 0.10, "RED": 0.00}).fillna(0.10).astype(float)
    long_budget = (1.0 - cash_pct).clip(lower=0.0)

    short_selected = merged["pool_short_candidate"] & merged["score_valid"] & (~merged["entry_gate"])
    n_long = merged["entry_gate"].groupby(merged["date"], sort=False).transform("sum").replace(0, np.nan)
    n_short = short_selected.groupby(merged["date"], sort=False).transform("sum").replace(0, np.nan)
    long_w_base = pd.Series(np.where(merged["entry_gate"], long_budget / n_long, 0.0), index=merged.index, dtype=float)
    short_w_base = pd.Series(np.where(short_selected, short_budget / n_short, 0.0), index=merged.index, dtype=float)
    long_w_lev = long_w_base * leverage_smoothed
    signed_w_pre = long_w_lev - short_w_base

    portfolio_beta_pre = (signed_w_pre * beta_lag).groupby(merged["date"], sort=False).transform("sum")
    beta_scale_pre = pd.Series(
        np.where(
            np.abs(portfolio_beta_pre) > float(beta_cap_abs),
            float(beta_cap_abs) / np.abs(portfolio_beta_pre),
            1.0,
        ),
        index=merged.index,
        dtype=float,
    ).clip(lower=0.0, upper=1.0)
    signed_w_mid = signed_w_pre * beta_scale_pre

    portfolio_beta_mid = (signed_w_mid * beta_lag).groupby(merged["date"], sort=False).transform("sum")
    beta_scale_post = pd.Series(
        np.where(
            np.abs(portfolio_beta_mid) > float(beta_cap_abs),
            float(beta_cap_abs) / np.abs(portfolio_beta_mid),
            1.0,
        ),
        index=merged.index,
        dtype=float,
    ).clip(lower=0.0, upper=1.0)
    signed_w_final = signed_w_mid * beta_scale_post
    portfolio_beta_final = (signed_w_final * beta_lag).groupby(merged["date"], sort=False).transform("sum")

    with np.errstate(divide="ignore", invalid="ignore"):
        leverage_final = np.where(
            merged["entry_gate"] & (long_w_base > 0.0),
            np.abs(signed_w_final) / long_w_base,
            leverage_min,
        )
    leverage_final = pd.Series(leverage_final, index=merged.index, dtype=float).replace([np.inf, -np.inf], np.nan).fillna(leverage_min)
    leverage_final = leverage_final.clip(lower=leverage_min, upper=leverage_max)

    gross_exposure = np.abs(signed_w_final).groupby(merged["date"], sort=False).transform("sum")
    net_exposure = signed_w_final.groupby(merged["date"], sort=False).transform("sum")
    short_borrow_balance = pd.Series(
        np.where(signed_w_final < 0.0, -signed_w_final, 0.0),
        index=merged.index,
        dtype=float,
    ).groupby(merged["date"], sort=False).transform("sum")
    borrow_cost_daily = short_borrow_balance * (float(borrow_rate_annual) / 252.0)

    merged["cash_pct"] = cash_pct
    merged["short_budget"] = short_budget
    merged["position_weight_long_base"] = long_w_base
    merged["position_weight_short_base"] = short_w_base
    merged["position_weight_final"] = signed_w_final
    merged["beta_scale_pre"] = beta_scale_pre
    merged["beta_scale_post"] = beta_scale_post
    merged["portfolio_beta_pre"] = portfolio_beta_pre
    merged["portfolio_beta"] = portfolio_beta_final
    merged["gross_exposure"] = gross_exposure
    merged["net_exposure"] = net_exposure
    merged["short_borrow_balance"] = short_borrow_balance
    merged["borrow_cost_daily"] = borrow_cost_daily
    merged["leverage_mult"] = leverage_final
    merged["leverage_multiplier"] = leverage_final

    merged["avoid_or_short_flag"] = (
        merged["score_valid"]
        & (merged["score_pct"] <= 0.10)
        & (~merged["quality_ok"] | merged["illiquid_flag"])
    ) | merged["pool_short_candidate"]
    merged.sort_values(["date", "conviction_score", "score"], ascending=[True, False, False], inplace=True)
    return merged
