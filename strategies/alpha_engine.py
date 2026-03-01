"""
FR-070 Alpha Engine

Selector + Sizer + Executor layer that bridges:
  - Regime Governor (capital budget)
  - Feature Store (asset-level alpha features)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

ROBUST_SIGMA_SCALE: float = 1.4826
SEMANTIC_EPSILON_FLOOR_DEFAULT: float = 1e-6
SEMANTIC_MIN_WINDOW_SIZE_DEFAULT: int = 20


@dataclass(frozen=True)
class AlphaEngineConfig:
    top_n: int = 5
    min_price: float = 1.0
    min_adv20: float = 10_000_000.0
    target_risk: float = 0.02
    conviction_threshold: float = 2.0
    conviction_boost: float = 1.2
    static_rsi_threshold: float = 30.0
    use_adaptive_rsi: bool = True
    adaptive_rsi_percentile: float = 0.15
    adaptive_rsi_window: int = 252
    adaptive_rsi_min_periods: int = 63
    entry_dist_sma20_max: float = 0.0
    entry_logic: str = "combined"
    atr_mult_low_vol: float = 3.0
    atr_mult_mid_vol: float = 4.0
    atr_mult_high_vol: float = 5.0
    low_vol_cutoff: float = 20.0
    high_vol_cutoff: float = 30.0
    max_position_weight: float = 0.35
    semantic_epsilon_floor: float = SEMANTIC_EPSILON_FLOOR_DEFAULT
    semantic_min_window_size: int = SEMANTIC_MIN_WINDOW_SIZE_DEFAULT


@dataclass(frozen=True)
class AlphaPlanResult:
    asof_date: pd.Timestamp
    regime_state: str
    regime_budget: float
    budget_utilization: float
    universe_rows: int
    selected: pd.DataFrame
    weights: pd.Series

    @property
    def empty(self) -> bool:
        return self.selected.empty


class AlphaEngine:
    """
    Deterministic FR-070 alpha allocator.

    Structural-fixed rules:
      - Trend eligibility gate: close > SMA200 (or trend_veto == False).
      - Regime budgets: GREEN=1.0, AMBER=0.5, RED=0.0.
      - Long-only and hard exposure cap.

    Adaptive knobs:
      - RSI entry threshold via rolling percentile.
      - ATR stop multiplier via volatility regime.
      - Selection depth via top-N.
    """

    BUDGET_MAP = {
        "GREEN": 1.0,
        "AMBER": 0.5,
        "RED": 0.0,
    }
    ENTRY_LOGIC_DIP = "dip"
    ENTRY_LOGIC_BREAKOUT = "breakout"
    ENTRY_LOGIC_COMBINED = "combined"
    ENTRY_LOGIC_SET = {ENTRY_LOGIC_DIP, ENTRY_LOGIC_BREAKOUT, ENTRY_LOGIC_COMBINED}
    BOOLEAN_TRUE_TOKENS = frozenset({"1", "true", "t", "yes", "y", "on"})
    BOOLEAN_FALSE_TOKENS = frozenset({"0", "false", "f", "no", "n", "off"})
    SNAPSHOT_PRECOMPUTED_COLUMNS = (
        "adv20",
        "rsi_threshold",
        "prev_rsi",
        "prior_50d_high",
    )

    REQUIRED_COLUMNS = {
        "date",
        "permno",
        "adj_close",
        "volume",
        "sma200",
        "dist_sma20",
        "rsi_14d",
        "atr_14d",
        "yz_vol_20d",
        "composite_score",
        "trend_veto",
    }

    def __init__(self, config: AlphaEngineConfig | None = None):
        self.config = config or AlphaEngineConfig()
        self._normalize_entry_logic(self.config.entry_logic)

    @classmethod
    def _normalize_regime_state(cls, regime_state: str | None) -> str:
        state = str(regime_state).strip().upper()
        if state in cls.BUDGET_MAP:
            return state
        # Fail-safe unknown/invalid states to RED budget behavior.
        return "RED"

    @classmethod
    def _normalize_entry_logic(cls, entry_logic: str | None) -> str:
        logic = str(entry_logic or "").strip().lower()
        if logic in cls.ENTRY_LOGIC_SET:
            return logic
        raise ValueError(f"Unsupported entry_logic: {entry_logic}")

    @classmethod
    def regime_budget(cls, regime_state: str) -> float:
        return float(cls.BUDGET_MAP[cls._normalize_regime_state(regime_state)])

    def _validate_features(self, features: pd.DataFrame):
        if not isinstance(features, pd.DataFrame):
            raise TypeError("features must be a pandas DataFrame")
        missing = sorted(self.REQUIRED_COLUMNS.difference(set(features.columns)))
        if missing:
            raise ValueError(f"Missing required feature columns: {missing}")

    def _compute_adv20_and_threshold(self, hist: pd.DataFrame) -> pd.DataFrame:
        cfg = self.config
        out = hist.copy()
        out["dollar_volume"] = pd.to_numeric(out["adj_close"], errors="coerce") * pd.to_numeric(
            out["volume"], errors="coerce"
        )
        out = out.sort_values(["permno", "date"])

        if "adv20" not in out.columns:
            out["adv20"] = (
                out.groupby("permno", sort=False)["dollar_volume"]
                .rolling(window=20, min_periods=20)
                .mean()
                .reset_index(level=0, drop=True)
            )
        else:
            out["adv20"] = pd.to_numeric(out["adv20"], errors="coerce")

        if cfg.use_adaptive_rsi:
            if "rsi_threshold" in out.columns:
                out["rsi_threshold"] = pd.to_numeric(out["rsi_threshold"], errors="coerce")
            else:
                # PIT-safe threshold: use lagged rolling percentile so today's threshold
                # is computed from historical RSI values only (excludes today's RSI).
                out["rsi_threshold"] = (
                    out.groupby("permno", sort=False)["rsi_14d"]
                    .rolling(
                        window=cfg.adaptive_rsi_window,
                        min_periods=cfg.adaptive_rsi_min_periods,
                    )
                    .quantile(cfg.adaptive_rsi_percentile)
                    .reset_index(level=0, drop=True)
                )
                out["rsi_threshold"] = out.groupby("permno", sort=False)["rsi_threshold"].shift(1)
        else:
            out["rsi_threshold"] = float(cfg.static_rsi_threshold)

        if "prev_rsi" not in out.columns:
            out["prev_rsi"] = out.groupby("permno", sort=False)["rsi_14d"].shift(1)
        else:
            out["prev_rsi"] = pd.to_numeric(out["prev_rsi"], errors="coerce")
        if "prior_50d_high" not in out.columns:
            close = pd.to_numeric(out["adj_close"], errors="coerce")
            out["prior_50d_high"] = (
                close.groupby(out["permno"], sort=False)
                .rolling(window=50, min_periods=50)
                .max()
                .reset_index(level=0, drop=True)
            )
            out["prior_50d_high"] = out.groupby("permno", sort=False)["prior_50d_high"].shift(1)
        else:
            out["prior_50d_high"] = pd.to_numeric(out["prior_50d_high"], errors="coerce")
        return out

    def _atr_multiplier(self, market_vol: float | None, regime_state: str) -> float:
        cfg = self.config
        if market_vol is None or not np.isfinite(market_vol):
            regime = self._normalize_regime_state(regime_state)
            if regime == "RED":
                return float(cfg.atr_mult_high_vol)
            if regime == "AMBER":
                return float(cfg.atr_mult_mid_vol)
            return float((cfg.atr_mult_low_vol + cfg.atr_mult_mid_vol) / 2.0)

        if market_vol < cfg.low_vol_cutoff:
            return float(cfg.atr_mult_low_vol)
        if market_vol > cfg.high_vol_cutoff:
            return float(cfg.atr_mult_high_vol)
        return float(cfg.atr_mult_mid_vol)

    @staticmethod
    def _safe_numeric(df: pd.DataFrame, col: str) -> pd.Series:
        return pd.to_numeric(df[col], errors="coerce")

    @classmethod
    def _parse_boolean_series(cls, values: pd.Series, *, default: bool) -> pd.Series:
        parsed = pd.Series(pd.NA, index=values.index, dtype="boolean")

        bool_mask = values.map(lambda v: isinstance(v, (bool, np.bool_)))
        if bool_mask.any():
            parsed.loc[bool_mask] = values.loc[bool_mask].astype(bool).to_numpy()

        numeric = pd.to_numeric(values, errors="coerce")
        parsed.loc[numeric.eq(1.0)] = True
        parsed.loc[numeric.eq(0.0)] = False

        text = values.astype("string").str.strip().str.lower()
        parsed.loc[text.isin(cls.BOOLEAN_TRUE_TOKENS)] = True
        parsed.loc[text.isin(cls.BOOLEAN_FALSE_TOKENS)] = False

        return parsed.fillna(bool(default)).astype(bool)

    @staticmethod
    def _percentile_fallback_scale(series: pd.Series) -> pd.Series:
        ranked = series.rank(method="average", pct=True, na_option="keep")
        return ((ranked - 0.5) * 2.0).astype(float)

    @classmethod
    def _semantic_scale_with_fallback(
        cls,
        series: pd.Series,
        *,
        epsilon_floor: float = SEMANTIC_EPSILON_FLOOR_DEFAULT,
        min_window_size: int = SEMANTIC_MIN_WINDOW_SIZE_DEFAULT,
    ) -> tuple[pd.Series, dict[str, float | int]]:
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
                scaled = cls._percentile_fallback_scale(s)
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
        return scaled.astype(float), telemetry

    def _empty_result(self, dt: pd.Timestamp, regime: str, budget: float, universe_rows: int) -> AlphaPlanResult:
        return AlphaPlanResult(
            asof_date=dt,
            regime_state=regime,
            regime_budget=budget,
            budget_utilization=0.0,
            universe_rows=int(universe_rows),
            selected=pd.DataFrame(
                columns=[
                    "date",
                    "permno",
                    "entry",
                    "stop_price",
                    "reason_code",
                    "weight",
                ]
            ),
            weights=pd.Series(dtype=float),
        )

    def prepare_feature_history(self, features: pd.DataFrame) -> pd.DataFrame:
        self._validate_features(features)
        f = features.copy()
        f["date"] = pd.to_datetime(f["date"], errors="coerce")
        f = f.dropna(subset=["date", "permno"]).sort_values(["date", "permno"])
        if f.empty:
            return f
        return self._compute_adv20_and_threshold(f)

    def _build_from_today(
        self,
        today: pd.DataFrame,
        regime_state: str,
        asof_date: pd.Timestamp,
        market_vol: float | None,
    ) -> AlphaPlanResult:
        regime = self._normalize_regime_state(regime_state)
        budget = self.regime_budget(regime)
        if today.empty or budget <= 0.0:
            return self._empty_result(
                dt=pd.Timestamp(asof_date),
                regime=regime,
                budget=budget,
                universe_rows=len(today),
            )

        cfg = self.config
        close = self._safe_numeric(today, "adj_close")
        sma200 = self._safe_numeric(today, "sma200")
        dist_sma20 = self._safe_numeric(today, "dist_sma20")
        rsi = self._safe_numeric(today, "rsi_14d")
        rsi_thr = self._safe_numeric(today, "rsi_threshold")
        prev_rsi = self._safe_numeric(today, "prev_rsi")
        prior_50d_high = self._safe_numeric(today, "prior_50d_high")
        atr = self._safe_numeric(today, "atr_14d")
        yz_vol = self._safe_numeric(today, "yz_vol_20d")
        score = self._safe_numeric(today, "composite_score")
        adv20 = self._safe_numeric(today, "adv20")
        trend_veto = self._parse_boolean_series(today["trend_veto"], default=True)

        liquidity_ok = adv20 >= cfg.min_adv20
        price_floor = float(cfg.min_price)
        if price_floor > 0.0:
            price_ok = close >= price_floor
        else:
            price_ok = pd.Series(True, index=today.index, dtype=bool)
        tradable = liquidity_ok & price_ok
        trend_ok = (close > sma200) & (~trend_veto)
        rsi_gate = rsi <= rsi_thr
        rsi_cross = (prev_rsi > rsi_thr) & rsi_gate
        pullback_gate = dist_sma20 <= cfg.entry_dist_sma20_max
        dip_entry = rsi_gate & (pullback_gate | rsi_cross)
        breakout_entry_green = (regime == "GREEN") & (close > prior_50d_high)
        entry_logic = self._normalize_entry_logic(cfg.entry_logic)
        if entry_logic == self.ENTRY_LOGIC_DIP:
            entry_signal = dip_entry
        elif entry_logic == self.ENTRY_LOGIC_BREAKOUT:
            entry_signal = breakout_entry_green
        else:
            entry_signal = dip_entry | breakout_entry_green
        entry = tradable & trend_ok & entry_signal

        candidates = today.loc[entry].copy()
        if candidates.empty:
            return self._empty_result(
                dt=pd.Timestamp(asof_date),
                regime=regime,
                budget=budget,
                universe_rows=len(today),
            )

        score_rank = pd.to_numeric(candidates["composite_score"], errors="coerce")
        permno_tiebreak = pd.to_numeric(candidates["permno"], errors="coerce")
        candidates = (
            candidates.assign(
                _composite_score_numeric=score_rank,
                _permno_tiebreak=permno_tiebreak,
            )
            .sort_values(
                ["_composite_score_numeric", "_permno_tiebreak"],
                ascending=[False, True],
                na_position="last",
                kind="mergesort",
            )
            .head(int(cfg.top_n))
            .drop(columns=["_composite_score_numeric", "_permno_tiebreak"])
        )
        atr_mult = self._atr_multiplier(market_vol=market_vol, regime_state=regime)

        score_cand = pd.to_numeric(candidates["composite_score"], errors="coerce")
        score_semantic, score_semantic_stats = self._semantic_scale_with_fallback(
            score_cand,
            epsilon_floor=cfg.semantic_epsilon_floor,
            min_window_size=cfg.semantic_min_window_size,
        )
        yz_cand = pd.to_numeric(candidates["yz_vol_20d"], errors="coerce")
        close_cand = pd.to_numeric(candidates["adj_close"], errors="coerce")
        atr_cand = pd.to_numeric(candidates["atr_14d"], errors="coerce")

        base_size = cfg.target_risk / yz_cand.clip(lower=1e-6)
        conviction = np.where(score_cand > cfg.conviction_threshold, cfg.conviction_boost, 1.0)
        raw = pd.Series(base_size.to_numpy() * conviction, index=candidates.index, dtype=float).clip(lower=0.0)
        raw = raw.where(np.isfinite(raw), 0.0)

        if raw.sum() <= 0.0:
            weights = pd.Series(0.0, index=candidates.index, dtype=float)
        else:
            weights = raw / raw.sum()
            weights = weights * budget

        # Single-position concentration guardrail + hard budget renormalization.
        max_w = float(cfg.max_position_weight) * float(budget)
        if max_w > 0.0:
            weights = weights.clip(upper=max_w)
            total = float(weights.sum())
            if total > budget and total > 0:
                weights = weights * (budget / total)

        dip_reason = f"MOM_DIP_{regime}_{'ADAPT' if cfg.use_adaptive_rsi else 'FIXED'}"
        breakout_reason = f"MOM_BREAKOUT_GREEN_{'ADAPT' if cfg.use_adaptive_rsi else 'FIXED'}"
        if entry_logic == self.ENTRY_LOGIC_DIP:
            reason = np.full(len(candidates), dip_reason, dtype=object)
        elif entry_logic == self.ENTRY_LOGIC_BREAKOUT:
            reason = np.full(len(candidates), breakout_reason, dtype=object)
        else:
            dip_selected = dip_entry.loc[candidates.index].fillna(False)
            reason = np.where(dip_selected.to_numpy(), dip_reason, breakout_reason)
        stop_price = (close_cand - (atr_mult * atr_cand)).clip(lower=0.0)

        candidates = candidates.assign(
            entry=True,
            stop_price=stop_price.values,
            reason_code=reason,
            weight=weights.values,
            semantic_score=score_semantic.values,
            semantic_fallback_rows=int(score_semantic_stats.get("fallback_rows", 0)),
            semantic_row_total=int(score_semantic_stats.get("row_total", 0)),
            semantic_fallback_rate=float(score_semantic_stats.get("fallback_rate", 0.0)),
        )
        budget_use = float(weights.sum())

        weight_series = pd.Series(
            data=weights.values,
            index=candidates["permno"].astype("int64"),
            dtype=float,
            name="weight",
        )
        weight_series.index.name = "permno"

        return AlphaPlanResult(
            asof_date=pd.Timestamp(asof_date),
            regime_state=regime,
            regime_budget=float(budget),
            budget_utilization=budget_use,
            universe_rows=len(today),
            selected=candidates.reset_index(drop=True),
            weights=weight_series,
        )

    def build_daily_plan_from_snapshot(
        self,
        snapshot: pd.DataFrame,
        regime_state: str,
        asof_date: pd.Timestamp | None = None,
        market_vol: float | None = None,
    ) -> AlphaPlanResult:
        if not isinstance(snapshot, pd.DataFrame):
            raise TypeError("snapshot must be a pandas DataFrame")
        if snapshot.empty:
            dt = pd.Timestamp(asof_date) if asof_date is not None else pd.Timestamp.utcnow().normalize()
            regime = self._normalize_regime_state(regime_state)
            return self._empty_result(dt=dt, regime=regime, budget=self.regime_budget(regime), universe_rows=0)

        snap = snapshot.copy()
        self._validate_features(snap)
        snap["date"] = pd.to_datetime(snap["date"], errors="coerce")
        bad_dates = int(snap["date"].isna().sum())
        if bad_dates > 0:
            raise ValueError(f"snapshot contains {bad_dates} rows with non-coercible date values")

        dt = pd.Timestamp(asof_date) if asof_date is not None else pd.Timestamp(snap["date"].max())
        single_day_snapshot = int(snap["date"].nunique(dropna=True)) <= 1
        if single_day_snapshot:
            missing_precomputed = [c for c in self.SNAPSHOT_PRECOMPUTED_COLUMNS if c not in snap.columns]
            for col in self.SNAPSHOT_PRECOMPUTED_COLUMNS:
                if col in snap.columns:
                    snap[col] = pd.to_numeric(snap[col], errors="coerce")

            target_day = snap.loc[snap["date"] == dt]
            missing_precomputed_rows = (
                int(target_day[list(self.SNAPSHOT_PRECOMPUTED_COLUMNS)].isna().any(axis=1).sum())
                if set(self.SNAPSHOT_PRECOMPUTED_COLUMNS).issubset(set(target_day.columns))
                else int(len(target_day))
            )
            if (not target_day.empty) and (missing_precomputed or missing_precomputed_rows > 0):
                raise ValueError(
                    "Single-day snapshot requires precomputed columns "
                    f"{list(self.SNAPSHOT_PRECOMPUTED_COLUMNS)} with non-null values for asof_date={dt.date()}. "
                    f"missing_columns={missing_precomputed}, rows_missing_precomputed={missing_precomputed_rows}. "
                    "Provide multi-day history or precompute these fields before calling build_daily_plan_from_snapshot."
                )
        else:
            drop_cols = [c for c in self.SNAPSHOT_PRECOMPUTED_COLUMNS if c in snap.columns]
            if drop_cols:
                snap = snap.drop(columns=drop_cols)
            snap = self._compute_adv20_and_threshold(snap.sort_values(["date", "permno"]))

        snap = snap[snap["date"] == dt].copy()
        if snap.empty:
            regime = self._normalize_regime_state(regime_state)
            return self._empty_result(dt=dt, regime=regime, budget=self.regime_budget(regime), universe_rows=0)

        return self._build_from_today(snap, regime_state=regime_state, asof_date=dt, market_vol=market_vol)

    def build_daily_plan(
        self,
        features: pd.DataFrame,
        regime_state: str,
        asof_date: pd.Timestamp | None = None,
        market_vol: float | None = None,
    ) -> AlphaPlanResult:
        f = self.prepare_feature_history(features)
        if f.empty:
            dt = pd.Timestamp(asof_date) if asof_date is not None else pd.Timestamp.utcnow().normalize()
            regime = self._normalize_regime_state(regime_state)
            return self._empty_result(dt=dt, regime=regime, budget=self.regime_budget(regime), universe_rows=0)

        dt = pd.Timestamp(asof_date) if asof_date is not None else pd.Timestamp(f["date"].max())
        hist = f[f["date"] <= dt].copy()
        if hist.empty:
            regime = self._normalize_regime_state(regime_state)
            return self._empty_result(dt=dt, regime=regime, budget=self.regime_budget(regime), universe_rows=0)

        today = hist[hist["date"] == dt].copy()
        return self._build_from_today(
            today=today,
            regime_state=regime_state,
            asof_date=dt,
            market_vol=market_vol,
        )
