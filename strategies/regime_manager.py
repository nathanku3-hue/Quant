"""
FR-041 Regime Manager

Deterministic Governor + Throttle + Matrix exposure control with a lightweight
online BOCPD-style changepoint probability on net liquidity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd


class GovernorState(str, Enum):
    RED = "RED"
    AMBER = "AMBER"
    GREEN = "GREEN"


class MarketState(str, Enum):
    NEG = "NEG"
    NEUT = "NEUT"
    POS = "POS"


@dataclass(frozen=True)
class RegimeManagerResult:
    target_exposure: pd.Series
    governor_state: pd.Series
    market_state: pd.Series
    matrix_exposure: pd.Series
    throttle_score: pd.Series
    composite_z: pd.Series
    bocpd_prob: pd.Series
    reason: pd.Series

    def latest(self) -> dict:
        if self.target_exposure.empty:
            return {
                "target_exposure": 0.5,
                "governor_state": GovernorState.AMBER.value,
                "market_state": MarketState.NEUT.value,
                "matrix_exposure": 0.5,
                "throttle_score": 1.0,
                "composite_z": 0.0,
                "bocpd_prob": 0.0,
                "reason": "Fallback: empty index",
            }

        return {
            "target_exposure": float(self.target_exposure.iloc[-1]),
            "governor_state": str(self.governor_state.iloc[-1]),
            "market_state": str(self.market_state.iloc[-1]),
            "matrix_exposure": float(self.matrix_exposure.iloc[-1]),
            "throttle_score": float(self.throttle_score.iloc[-1]),
            "composite_z": float(self.composite_z.iloc[-1]),
            "bocpd_prob": float(self.bocpd_prob.iloc[-1]),
            "reason": str(self.reason.iloc[-1]),
        }


class RegimeManager:
    """
    FR-041 governor and exposure manager.

    BOCPD note:
      This implementation uses a lightweight Bayesian-surprise approximation:
        - Estimate standardized one-step surprise on net liquidity.
        - Use hazard prior h and Gaussian no-change likelihood.
        - Posterior cp probability: h / (h + (1-h)*L_no_change).
      This is mathematically grounded as a hazard-updated online changepoint
      posterior approximation and is deterministic.
    """

    # FR-041 approved matrix (Governor x ThrottleBin -> target exposure)
    DEFAULT_MATRIX = {
        (GovernorState.RED.value, MarketState.NEG.value): 0.00,
        (GovernorState.RED.value, MarketState.NEUT.value): 0.00,
        (GovernorState.RED.value, MarketState.POS.value): 0.20,
        (GovernorState.AMBER.value, MarketState.NEG.value): 0.25,
        (GovernorState.AMBER.value, MarketState.NEUT.value): 0.50,
        (GovernorState.AMBER.value, MarketState.POS.value): 0.75,
        (GovernorState.GREEN.value, MarketState.NEG.value): 0.70,
        (GovernorState.GREEN.value, MarketState.NEUT.value): 1.00,
        (GovernorState.GREEN.value, MarketState.POS.value): 1.30,
    }

    def __init__(
        self,
        matrix: dict[tuple[str, str], float] | None = None,
        bocpd_window: int = 63,
        bocpd_min_periods: int = 20,
        bocpd_hazard: float = 1.0 / 126.0,
        bocpd_smoothing: float = 0.25,
        throttle_clip: tuple[float, float] = (-2.0, 2.0),
        max_exposure: float = 1.5,
    ):
        self.matrix = dict(self.DEFAULT_MATRIX)
        if matrix:
            self.matrix.update(
                {(str(k[0]).upper(), str(k[1]).upper()): float(v) for k, v in matrix.items()}
            )
        self.bocpd_window = int(bocpd_window)
        self.bocpd_min_periods = int(bocpd_min_periods)
        self.bocpd_hazard = float(np.clip(bocpd_hazard, 1e-6, 0.5))
        self.bocpd_smoothing = float(np.clip(bocpd_smoothing, 0.0, 1.0))
        self.throttle_clip = (float(throttle_clip[0]), float(throttle_clip[1]))
        self.max_exposure = float(max(0.2, max_exposure))

    def matrix_exposure(self, governor_state: str, market_state: str) -> float:
        key = (str(governor_state).upper(), str(market_state).upper())
        val = float(self.matrix.get(key, 0.5))
        return float(np.clip(val, 0.0, self.max_exposure))

    @staticmethod
    def _numeric_col(macro: pd.DataFrame | None, idx: pd.Index, col: str) -> pd.Series:
        if not isinstance(macro, pd.DataFrame) or col not in macro.columns:
            return pd.Series(np.nan, index=idx, dtype=float)
        s = pd.to_numeric(macro[col], errors="coerce").reindex(idx)
        return s.ffill()

    @staticmethod
    def _raw_col(macro: pd.DataFrame | None, idx: pd.Index, col: str) -> pd.Series:
        if not isinstance(macro, pd.DataFrame) or col not in macro.columns:
            return pd.Series(np.nan, index=idx, dtype=float)
        return macro[col].reindex(idx)

    @staticmethod
    def _bool_col(macro: pd.DataFrame | None, idx: pd.Index, col: str, default: bool = False) -> pd.Series:
        if not isinstance(macro, pd.DataFrame) or col not in macro.columns:
            return pd.Series(bool(default), index=idx, dtype=bool)
        return macro[col].reindex(idx).astype("boolean").ffill().fillna(default).astype(bool)

    @staticmethod
    def _rolling_z(series: pd.Series, window: int = 63, min_periods: int = 20) -> pd.Series:
        s = pd.to_numeric(series, errors="coerce")
        mu = s.rolling(window=window, min_periods=min_periods).mean()
        sigma = s.rolling(window=window, min_periods=min_periods).std()
        z = (s - mu) / sigma.replace(0.0, np.nan)
        return z.replace([np.inf, -np.inf], np.nan)

    def bocpd_probability(self, net_liquidity: pd.Series) -> pd.Series:
        s = pd.to_numeric(net_liquidity, errors="coerce")
        mean_prev = s.rolling(self.bocpd_window, min_periods=self.bocpd_min_periods).mean().shift(1)
        std_prev = s.rolling(self.bocpd_window, min_periods=self.bocpd_min_periods).std().shift(1)
        z = ((s - mean_prev) / std_prev.replace(0.0, np.nan)).abs()

        # Under no change, large surprise has low likelihood.
        no_change_like = np.exp(-0.5 * (z ** 2))
        no_change_like = no_change_like.where(z.notna(), 1.0)

        h = self.bocpd_hazard
        posterior_cp = h / (h + (1.0 - h) * no_change_like)
        posterior_cp = posterior_cp.clip(lower=0.0, upper=1.0).fillna(h)
        if self.bocpd_smoothing > 0.0:
            posterior_cp = posterior_cp.ewm(alpha=self.bocpd_smoothing, adjust=False).mean()
        return posterior_cp.astype(float)

    @staticmethod
    def _momentum_proxy(macro: pd.DataFrame | None, idx: pd.Index) -> pd.Series:
        if not isinstance(macro, pd.DataFrame):
            return pd.Series(np.nan, index=idx, dtype=float)

        if "momentum_proxy" in macro.columns:
            return pd.to_numeric(macro["momentum_proxy"], errors="coerce").reindex(idx).ffill()

        if "spy_close" in macro.columns:
            spy = pd.to_numeric(macro["spy_close"], errors="coerce").reindex(idx).ffill()
            return spy.pct_change(periods=20, fill_method=None)

        if "mtum_spy_corr_60d" in macro.columns:
            return pd.to_numeric(macro["mtum_spy_corr_60d"], errors="coerce").reindex(idx).ffill()

        return pd.Series(np.nan, index=idx, dtype=float)

    def evaluate(self, macro: pd.DataFrame | None, idx: pd.Index) -> RegimeManagerResult:
        if not isinstance(idx, pd.Index):
            idx = pd.Index([])
        if len(idx) == 0:
            empty = pd.Series(dtype=float, index=idx)
            return RegimeManagerResult(
                target_exposure=empty,
                governor_state=pd.Series(dtype=object, index=idx),
                market_state=pd.Series(dtype=object, index=idx),
                matrix_exposure=empty,
                throttle_score=empty,
                composite_z=empty,
                bocpd_prob=empty,
                reason=pd.Series(dtype=object, index=idx),
            )

        us_net_liquidity = self._numeric_col(macro, idx, "us_net_liquidity_mm")
        liquidity_impulse = self._numeric_col(macro, idx, "liquidity_impulse")
        repo_spread_bps = self._numeric_col(macro, idx, "repo_spread_bps")
        vix_level = self._numeric_col(macro, idx, "vix_level")
        if vix_level.notna().sum() == 0:
            vix_level = self._numeric_col(macro, idx, "vix_proxy")
        vrp = self._numeric_col(macro, idx, "vrp")

        credit_raw = self._raw_col(macro, idx, "credit_freeze")
        credit_freeze = credit_raw.astype("boolean").fillna(False).astype(bool)
        momentum_proxy = self._momentum_proxy(macro, idx)

        bocpd_prob = self.bocpd_probability(us_net_liquidity)
        us_net_liq_ma20 = us_net_liquidity.rolling(20, min_periods=5).mean()

        # FR-042 calibration: suppress low-vol false positives while preserving crisis capture.
        red_repo = repo_spread_bps > 10.0
        red_credit = credit_freeze & (vix_level > 15.0)
        red_liq = (liquidity_impulse < -1.90) & (vix_level > 20.0)
        red_vix = vix_level > 40.0
        red_mask = red_repo | red_credit | red_liq | red_vix

        amber_liq = (us_net_liquidity < (us_net_liq_ma20 * 0.997)) & (liquidity_impulse < 0.0)
        amber_vix = vix_level > 25.0
        amber_bocpd = bocpd_prob > 0.80
        amber_mask = (~red_mask) & (amber_liq | amber_vix | amber_bocpd)

        governor_state = pd.Series(GovernorState.GREEN.value, index=idx, dtype=object)
        governor_state.loc[amber_mask] = GovernorState.AMBER.value
        governor_state.loc[red_mask] = GovernorState.RED.value

        # Throttle score S in [-2, 2], built from standardized components.
        liq_z = self._rolling_z(liquidity_impulse, window=63, min_periods=20)
        vrp_z = self._rolling_z(vrp, window=63, min_periods=20)
        vix_z = self._rolling_z(vix_level, window=63, min_periods=20)
        mom_z = self._rolling_z(momentum_proxy, window=63, min_periods=20)
        parts = pd.concat([liq_z, vrp_z, -vix_z, mom_z], axis=1)
        composite_z = parts.mean(axis=1, skipna=True).clip(
            lower=self.throttle_clip[0], upper=self.throttle_clip[1]
        )
        composite_z = composite_z.fillna(0.0).astype(float)
        throttle_score = composite_z.copy()

        # Discretize throttle score to NEG / NEUT / POS bins for matrix lookup.
        market_state = pd.Series(MarketState.NEUT.value, index=idx, dtype=object)
        market_state.loc[throttle_score > 0.5] = MarketState.POS.value
        market_state.loc[throttle_score < -0.5] = MarketState.NEG.value

        key = governor_state.astype(str) + "|" + market_state.astype(str)
        mapping = {f"{g}|{m}": float(np.clip(v, 0.0, self.max_exposure)) for (g, m), v in self.matrix.items()}
        matrix_exposure = key.map(mapping).fillna(0.5).astype(float)
        target_exposure = matrix_exposure.copy()
        red_pos = (governor_state == GovernorState.RED.value) & (market_state == MarketState.POS.value)
        red_not_pos = (governor_state == GovernorState.RED.value) & (market_state != MarketState.POS.value)
        target_exposure.loc[red_not_pos] = 0.0
        target_exposure.loc[red_pos] = np.minimum(target_exposure.loc[red_pos], 0.20)

        feature_count = pd.concat(
            [
                repo_spread_bps.notna(),
                credit_raw.notna(),
                liquidity_impulse.notna(),
                us_net_liquidity.notna(),
                vrp.notna(),
                vix_level.notna(),
            ],
            axis=1,
        ).sum(axis=1)
        fallback_mask = feature_count < 2
        regime_scalar = self._numeric_col(macro, idx, "regime_scalar").clip(0.0, 1.0)
        legacy_vix_scalar = pd.Series(np.nan, index=idx, dtype=float)
        legacy_vix_scalar.loc[vix_level.notna()] = 1.0
        legacy_vix_scalar.loc[vix_level > 30.0] = 0.5
        legacy_vix_scalar.loc[(vix_level >= 20.0) & (vix_level <= 30.0)] = 0.7
        legacy_scalar = regime_scalar.where(regime_scalar.notna(), legacy_vix_scalar)

        fallback_with_legacy = fallback_mask & legacy_scalar.notna()
        fallback_no_scalar = fallback_mask & (~fallback_with_legacy)

        market_state.loc[fallback_mask] = MarketState.NEUT.value
        throttle_score.loc[fallback_mask] = 0.0
        composite_z.loc[fallback_mask] = 0.0
        matrix_exposure.loc[fallback_with_legacy] = legacy_scalar.loc[fallback_with_legacy]
        target_exposure.loc[fallback_with_legacy] = legacy_scalar.loc[fallback_with_legacy]

        governor_state.loc[fallback_with_legacy] = GovernorState.GREEN.value
        governor_state.loc[fallback_with_legacy & (legacy_scalar <= 0.7)] = GovernorState.AMBER.value
        governor_state.loc[fallback_with_legacy & (legacy_scalar <= 0.5)] = GovernorState.RED.value

        governor_state.loc[fallback_no_scalar] = GovernorState.AMBER.value
        matrix_exposure.loc[fallback_no_scalar] = 0.5
        target_exposure.loc[fallback_no_scalar] = 0.5

        reasons: list[str] = []
        for t in idx:
            if bool(fallback_no_scalar.loc[t]):
                reasons.append("Fallback: FR-041 inputs missing; using neutral 0.50 exposure")
                continue

            if bool(fallback_with_legacy.loc[t]):
                rs = float(legacy_scalar.loc[t])
                reasons.append(f"Fallback: FR-041 inputs missing; using legacy regime_scalar={rs:.2f}")
                continue

            if bool(red_repo.loc[t]):
                reasons.append(f"RED: repo_spread_bps={float(repo_spread_bps.loc[t]):.2f} > 10.0")
            elif bool(red_credit.loc[t]):
                reasons.append("RED: credit_freeze=True with vix_level>15")
            elif bool(red_liq.loc[t]):
                reasons.append(
                    f"RED: liquidity_impulse={float(liquidity_impulse.loc[t]):.2f} < -1.90 with vix_level>20"
                )
            elif bool(red_vix.loc[t]):
                reasons.append(f"RED: vix_level={float(vix_level.loc[t]):.2f} > 40")
            elif bool(amber_liq.loc[t]):
                reasons.append("AMBER: us_net_liquidity_mm < 99.7% MA20 and liquidity_impulse < 0")
            elif bool(amber_vix.loc[t]):
                reasons.append(f"AMBER: vix_level={float(vix_level.loc[t]):.2f} > 25")
            elif bool(amber_bocpd.loc[t]):
                reasons.append(f"AMBER: bocpd_prob={float(bocpd_prob.loc[t]):.2f} > 0.80")
            else:
                reasons.append("GREEN: no RED/AMBER trigger")

        return RegimeManagerResult(
            target_exposure=target_exposure.astype(float),
            governor_state=governor_state.astype(str),
            market_state=market_state.astype(str),
            matrix_exposure=matrix_exposure.astype(float),
            throttle_score=throttle_score.astype(float),
            composite_z=composite_z.astype(float),
            bocpd_prob=bocpd_prob.astype(float),
            reason=pd.Series(reasons, index=idx, dtype=object),
        )
