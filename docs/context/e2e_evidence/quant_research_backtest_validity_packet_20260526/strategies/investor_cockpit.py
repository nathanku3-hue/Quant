"""
Terminal Zero — Investor Cockpit Strategy (Phase 4.1: Dynamic Volatility Mapping)

Per-stock adaptive parameters based on cross-sectional volatility rank.
  [FR-019] Dynamic k/z Mapping:
    k_i = 2.5 + (1.5 × VolRank_i)    High Vol → loose stop, Low Vol → tight stop
    z_i = -3.0 + (2.0 × VolRank_i)   High Vol → shallow dip, Low Vol → deep dip
  [FR-017] Green Candle Confirmation: Entry only if Price(T) > Price(T-1)
  [D-19]   Quantile Mapping formula documented in Decision Log.
"""

import os

import duckdb
import numpy as np
import pandas as pd
from strategies.base import BaseStrategy
from strategies.alpha_engine import AlphaEngine, AlphaEngineConfig
from strategies.regime_manager import RegimeManager


class InvestorCockpitStrategy(BaseStrategy):
    """
    Signal generation with per-stock Volatility-Ranked Adaptive Parameters.
    Supports Fixed mode (for grid search) and Adaptive mode (for live Cockpit).
    """
    SKIP_QUALITY_CHECK = {"SPY", "QQQ", "IWM", "DIA", "GLD", "TLT"}
    FEATURES_PATH = "./data/processed/features.parquet"
    ALPHA_FEATURE_COLUMNS = [
        "date",
        "permno",
        "adj_close",
        "tri",
        "volume",
        "sma200",
        "dist_sma20",
        "rsi_14d",
        "atr_14d",
        "yz_vol_20d",
        "composite_score",
        "trend_veto",
    ]
    ALPHA_OPTIONAL_COLUMNS = ["adv20", "rsi_threshold", "prev_rsi", "prior_50d_high"]

    def __init__(
        self,
        k_stop: float = 3.5,        # Fixed k (used when use_dynamic_params=False)
        z_entry: float = -2.5,      # Fixed z (used when use_dynamic_params=False)
        atr_period: int = 22,
        lookback: int = 20,
        vol_rank_window: int = 60,   # Window for volatility ranking
        use_dynamic_params: bool = False,
        green_candle: bool = True,
        use_alpha_engine: bool = False,
        alpha_top_n: int = 5,
        hysteresis_exit_rank: int = 20,
        alpha_entry_logic: str = "combined",
        ratchet_stops: bool = True,
    ):
        self.k_stop = k_stop
        self.z_entry = z_entry
        self.atr_period = atr_period
        self.lookback = lookback
        self.vol_rank_window = vol_rank_window
        self.use_dynamic_params = use_dynamic_params
        self.green_candle = green_candle
        self.use_alpha_engine = bool(use_alpha_engine)
        self.alpha_top_n = int(max(1, alpha_top_n))
        self.hysteresis_exit_rank = int(max(self.alpha_top_n, hysteresis_exit_rank))
        self.alpha_entry_logic = str(alpha_entry_logic).strip().lower()
        self.ratchet_stops = bool(ratchet_stops)
        self.alpha_engine = AlphaEngine(
            AlphaEngineConfig(
                top_n=self.hysteresis_exit_rank,
                use_adaptive_rsi=True,
                entry_logic=self.alpha_entry_logic,
            )
        )
        self.regime_manager = RegimeManager()

    # ── Core Math: Dynamic Parameter Mapping [D-19] ─────────────────────────

    def _compute_dynamic_params(self, prices: pd.DataFrame):
        """
        [FR-019] Per-stock, per-day k and z based on cross-sectional volatility rank.

        Returns:
            k_matrix: DataFrame (same shape as prices) of per-stock k values.
            z_matrix: DataFrame (same shape as prices) of per-stock z values.
            vol_rank: DataFrame of percentile ranks (0.0=lowest vol, 1.0=highest vol).
        """
        # 1. Calculate rolling annualized volatility
        daily_ret = prices.pct_change(fill_method=None)
        vol = daily_ret.rolling(self.vol_rank_window).std() * np.sqrt(252)

        # 2. Cross-sectional rank (axis=1: rank stocks against each other per day)
        vol_rank = vol.rank(axis=1, pct=True)

        # 3. Linear mapping
        #    High Vol (Rank=1.0) → k=4.0, z=-1.0 (loose stop, shallow dip)
        #    Low Vol  (Rank=0.0) → k=2.5, z=-3.0 (tight stop, deep dip)
        k_matrix = 2.5 + (1.5 * vol_rank)
        z_matrix = -3.0 + (2.0 * vol_rank)

        return k_matrix, z_matrix, vol_rank

    # ── Advanced Alpha: Efficiency Ratio [D-26] ─────────────────────────────

    def _calculate_efficiency_ratio(self, prices: pd.DataFrame, window: int = 10):
        """
        Kaufman Efficiency Ratio (Fractal Efficiency).
        ER = |Direction| / TotalPath.
        ER → 1.0 = clean trend, ER → 0.0 = random walk.
        """
        direction = prices.diff(window).abs()
        volatility = prices.diff().abs().rolling(window).sum()
        er = direction / volatility.replace(0, 1)
        return er

    # ── Advanced Alpha: Robust Z-Score [D-26] ────────────────────────────────

    def _calculate_robust_z(self, prices: pd.DataFrame, window: int = 20):
        """
        Robust Z-Score using Median & MAD.
        Resistant to fat-tail crashes where StdDev blows up.
        1.4826 scaling makes MAD comparable to StdDev under normality.
        """
        median = prices.rolling(window).median()
        deviation = (prices - median).abs()
        mad = deviation.rolling(window).median()
        robust_z = (prices - median) / (mad * 1.4826).replace(0, 1)
        return robust_z

    @staticmethod
    def _latest_quality_status(
        fundamentals: dict | None,
        index: pd.Index,
        columns: pd.Index,
    ) -> pd.Series:
        """
        Return latest per-ticker quality status as 1/0 vector.
        If fundamentals are missing or malformed, default to 0 (fail-safe).
        """
        status = pd.Series(0, index=columns, dtype=int)
        if not isinstance(fundamentals, dict):
            return status

        q_df = fundamentals.get("quality_pass")
        if isinstance(q_df, pd.DataFrame) and not q_df.empty:
            q_aligned = q_df.reindex(index=index, columns=columns).ffill()
            if not q_aligned.empty:
                status = q_aligned.iloc[-1].fillna(False).astype(int)

        # ETF/index bypass: these instruments do not have corporate quarterly fundamentals.
        ticker_map = fundamentals.get("ticker_map", {})
        if isinstance(ticker_map, dict):
            for col in status.index:
                ticker = ticker_map.get(col)
                if ticker is None and isinstance(col, (int, np.integer)):
                    ticker = ticker_map.get(int(col))
                if ticker is None:
                    ticker = ticker_map.get(str(col))
                if isinstance(ticker, str) and ticker.upper() in InvestorCockpitStrategy.SKIP_QUALITY_CHECK:
                    status.loc[col] = 1

        return status

    @staticmethod
    def _latest_earnings_dates(
        fundamentals: dict | None,
        columns: pd.Index,
    ) -> tuple[pd.Series, pd.Series]:
        """
        Return per-ticker next/last earnings dates aligned to columns.
        Missing data stays NaT.
        """
        next_dt = pd.Series(pd.NaT, index=columns, dtype="datetime64[ns]")
        last_dt = pd.Series(pd.NaT, index=columns, dtype="datetime64[ns]")
        if not isinstance(fundamentals, dict):
            return next_dt, last_dt

        cal_df = fundamentals.get("earnings_calendar")
        if isinstance(cal_df, pd.DataFrame) and not cal_df.empty:
            keyed = cal_df.copy()
            if "permno" in keyed.columns:
                keyed["permno"] = pd.to_numeric(keyed["permno"], errors="coerce")
                keyed = keyed.dropna(subset=["permno"]).drop_duplicates(subset=["permno"], keep="last")
                keyed["permno"] = keyed["permno"].astype("int64")
                keyed = keyed.set_index("permno")
            else:
                idx_num = pd.to_numeric(keyed.index, errors="coerce")
                keyed = keyed.assign(_permno_idx=idx_num).dropna(subset=["_permno_idx"])
                keyed["_permno_idx"] = keyed["_permno_idx"].astype("int64")
                keyed = keyed.drop_duplicates(subset=["_permno_idx"], keep="last").set_index("_permno_idx")

            target = pd.to_numeric(pd.Index(columns), errors="coerce")
            target_idx = pd.Index(target).where(pd.notna(target), -1).astype("int64")
            aligned = keyed.reindex(target_idx)
            aligned.index = columns
            if "next_earnings_date" in aligned.columns:
                next_dt = pd.to_datetime(aligned["next_earnings_date"], errors="coerce")
            if "last_earnings_date" in aligned.columns:
                last_dt = pd.to_datetime(aligned["last_earnings_date"], errors="coerce")
        return next_dt, last_dt

    @staticmethod
    def _macro_score(macro: pd.DataFrame, idx: pd.Index) -> int:
        """
        Macro score in [0,2].
        Priority:
          1) Use FR-041 target exposure mapping when available.
          2) Use FR-035/FR-040 fallback logic.
          3) Fallback to legacy VIX + VIX trend heuristic.
        """
        if not isinstance(macro, pd.DataFrame) or macro.empty:
            return 1

        # FR-041 first: map target exposure to conviction macro points.
        try:
            regime_latest = RegimeManager().evaluate(macro, idx).latest()
            exp_now = float(regime_latest.get("target_exposure", np.nan))
            if np.isfinite(exp_now):
                if exp_now <= 0.20:
                    return 0
                if exp_now <= 0.75:
                    return 1
                return 2
        except Exception:
            pass

        if "regime_scalar" in macro.columns:
            rs = pd.to_numeric(macro["regime_scalar"], errors="coerce").reindex(idx).ffill()
            if rs.notna().any():
                now = float(rs.iloc[-1])
                if now <= 0.5:
                    return 0
                if now <= 0.7:
                    return 1
                return 2

        # FR-040 overlay: downgrade macro score under flow/plumbing stress.
        liq_cols = {"liquidity_impulse", "repo_stress", "global_dollar_stress", "lrp_index"}
        if liq_cols.issubset(macro.columns):
            liq_imp = pd.to_numeric(macro["liquidity_impulse"], errors="coerce").reindex(idx).ffill()
            repo_stress = macro["repo_stress"].reindex(idx).ffill().fillna(False).astype(bool)
            dollar_stress = macro["global_dollar_stress"].reindex(idx).ffill().fillna(False).astype(bool)
            lrp = pd.to_numeric(macro["lrp_index"], errors="coerce").reindex(idx).ffill()

            liq_now = float(liq_imp.iloc[-1]) if liq_imp.notna().any() else 0.0
            repo_now = bool(repo_stress.iloc[-1]) if len(repo_stress) else False
            dollar_now = bool(dollar_stress.iloc[-1]) if len(dollar_stress) else False
            lrp_now = float(lrp.iloc[-1]) if lrp.notna().any() else 0.0

            stress_hits = 0
            stress_hits += int(repo_now)
            stress_hits += int(dollar_now)
            stress_hits += int(liq_now < -1.0)
            stress_hits += int(lrp_now > 1.0)

            if stress_hits >= 2:
                return 0
            if stress_hits == 1 or liq_now < 0:
                return 1
            return 2

        if "vix_proxy" not in macro.columns:
            return 1

        vix_series = macro["vix_proxy"].reindex(idx).ffill().fillna(15.0)
        vix_ma_20 = vix_series.rolling(20).mean()
        vix_now = float(vix_series.iloc[-1])
        vix_trend_now = float(vix_ma_20.iloc[-1])
        if vix_now < 20:
            return 2 if vix_now < vix_trend_now else 1
        return 1 if vix_now < vix_trend_now else 0

    @staticmethod
    def _legacy_regime_series(index: pd.Index, macro: pd.DataFrame) -> pd.Series:
        vix = (
            macro["vix_proxy"].reindex(index).ffill().fillna(15.0)
            if isinstance(macro, pd.DataFrame) and "vix_proxy" in macro.columns
            else pd.Series(30.0, index=index)
        )
        vix_regime = pd.Series(1.0, index=index, dtype=float)
        vix_regime[vix > 30] = 0.5
        vix_regime[(vix >= 20) & (vix <= 30)] = 0.7

        if isinstance(macro, pd.DataFrame) and "regime_scalar" in macro.columns:
            rs = pd.to_numeric(macro["regime_scalar"], errors="coerce").reindex(index).ffill()
            return rs.clip(lower=0.0, upper=1.0).where(rs.notna(), vix_regime).fillna(0.5)
        return vix_regime

    @staticmethod
    def _sql_escape_path(path: str) -> str:
        return str(path).replace("\\", "/").replace("'", "''")

    def _load_alpha_features_from_store(self, prices: pd.DataFrame) -> pd.DataFrame:
        if not os.path.exists(self.FEATURES_PATH):
            return pd.DataFrame(columns=self.ALPHA_FEATURE_COLUMNS)
        if prices.empty or len(prices.columns) == 0:
            return pd.DataFrame(columns=self.ALPHA_FEATURE_COLUMNS)

        idx = pd.DatetimeIndex(prices.index).sort_values()
        start = pd.Timestamp(idx.min()).strftime("%Y-%m-%d")
        end = pd.Timestamp(idx.max()).strftime("%Y-%m-%d")
        permnos = [int(p) for p in prices.columns]
        permno_list = ",".join(str(p) for p in permnos)
        cols = ", ".join(self.ALPHA_FEATURE_COLUMNS)

        con = duckdb.connect()
        try:
            available = con.execute(
                f"DESCRIBE SELECT * FROM '{self._sql_escape_path(self.FEATURES_PATH)}'"
            ).df()
            available_cols = {str(c) for c in available.get("column_name", pd.Series(dtype=str)).tolist()}
            select_cols = [c for c in self.ALPHA_FEATURE_COLUMNS if c in available_cols]
            if "date" not in select_cols:
                select_cols.append("date")
            if "permno" not in select_cols:
                select_cols.append("permno")
            cols = ", ".join(select_cols)
            q = f"""
                SELECT {cols}
                FROM '{self._sql_escape_path(self.FEATURES_PATH)}'
                WHERE CAST(date AS DATE) >= DATE '{start}'
                  AND CAST(date AS DATE) <= DATE '{end}'
                  AND CAST(permno AS BIGINT) IN ({permno_list})
                ORDER BY date, permno
            """
            df = con.execute(q).df()
        finally:
            con.close()

        if df.empty:
            return pd.DataFrame(columns=self.ALPHA_FEATURE_COLUMNS)
        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.tz_convert(None).dt.normalize()
        df = df.dropna(subset=["date", "permno"]).copy()
        df["permno"] = pd.to_numeric(df["permno"], errors="coerce").astype("Int64")
        for col in self.ALPHA_FEATURE_COLUMNS:
            if col not in df.columns:
                df[col] = np.nan
        df["adj_close"] = pd.to_numeric(df["adj_close"], errors="coerce")
        df["tri"] = pd.to_numeric(df["tri"], errors="coerce")
        df["tri"] = df["tri"].where(df["tri"].notna(), df["adj_close"])
        df["adj_close"] = df["adj_close"].where(df["adj_close"].notna(), df["tri"])
        return df[self.ALPHA_FEATURE_COLUMNS]

    @staticmethod
    def _cross_z(wide: pd.DataFrame) -> pd.DataFrame:
        mu = wide.mean(axis=1, skipna=True)
        sigma = wide.std(axis=1, skipna=True).replace(0.0, np.nan)
        return wide.sub(mu, axis=0).div(sigma, axis=0)

    def _build_alpha_features_fallback(self, prices: pd.DataFrame) -> pd.DataFrame:
        if prices.empty:
            return pd.DataFrame(columns=self.ALPHA_FEATURE_COLUMNS)
        px = prices.sort_index().astype(float)
        ret = px.pct_change(fill_method=None)
        sma20 = px.rolling(20, min_periods=20).mean()
        sma200 = px.rolling(200, min_periods=200).mean()
        dist_sma20 = (px - sma20) / sma20.replace(0.0, np.nan)
        atr14 = px.diff().abs().rolling(14, min_periods=14).mean()
        yz20 = ret.rolling(20, min_periods=20).std() * np.sqrt(252.0)

        delta = px.diff()
        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)
        avg_gain = gain.ewm(alpha=1.0 / 14.0, adjust=False, min_periods=14).mean()
        avg_loss = loss.ewm(alpha=1.0 / 14.0, adjust=False, min_periods=14).mean()
        rs = avg_gain / avg_loss.replace(0.0, np.nan)
        rsi14 = (100.0 - (100.0 / (1.0 + rs))).clip(lower=0.0, upper=100.0)

        mom = px / px.shift(60) - 1.0
        z_mom = self._cross_z(mom)
        z_vol = self._cross_z(yz20)
        score = z_mom - z_vol

        vol = pd.DataFrame(20_000_000.0, index=px.index, columns=px.columns)
        trend_veto = px.lt(sma200)

        def _stack(w: pd.DataFrame, name: str) -> pd.Series:
            try:
                return w.stack(future_stack=True).rename(name)
            except TypeError:
                return w.stack(dropna=False).rename(name)

        out = pd.concat(
            [
                _stack(px, "adj_close"),
                _stack(px, "tri"),
                _stack(vol, "volume"),
                _stack(sma200, "sma200"),
                _stack(dist_sma20, "dist_sma20"),
                _stack(rsi14, "rsi_14d"),
                _stack(atr14, "atr_14d"),
                _stack(yz20, "yz_vol_20d"),
                _stack(score, "composite_score"),
                _stack(trend_veto.astype(float), "trend_veto"),
            ],
            axis=1,
        ).reset_index().rename(columns={"level_0": "date", "level_1": "permno"})
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        out["permno"] = pd.to_numeric(out["permno"], errors="coerce").astype("Int64")
        out["trend_veto"] = out["trend_veto"].fillna(1.0).astype(bool)
        return out[self.ALPHA_FEATURE_COLUMNS]

    def _resolve_alpha_feature_history(self, prices: pd.DataFrame, fundamentals: dict | None) -> pd.DataFrame:
        if isinstance(fundamentals, dict):
            fh = fundamentals.get("feature_history")
            if isinstance(fh, pd.DataFrame) and not fh.empty:
                out = fh.copy()
                if "tri" not in out.columns and "adj_close" in out.columns:
                    out["tri"] = out["adj_close"]
                if "adj_close" not in out.columns and "tri" in out.columns:
                    out["adj_close"] = out["tri"]
                for col in self.ALPHA_FEATURE_COLUMNS:
                    if col not in out.columns:
                        out[col] = np.nan
                keep_cols = self.ALPHA_FEATURE_COLUMNS + [c for c in self.ALPHA_OPTIONAL_COLUMNS if c in out.columns]
                out["date"] = pd.to_datetime(out["date"], errors="coerce", utc=True).dt.tz_convert(None).dt.normalize()
                out = out.dropna(subset=["date", "permno"])
                perm_set = {int(p) for p in prices.columns}
                out["permno"] = pd.to_numeric(out["permno"], errors="coerce").astype("Int64")
                out = out[out["permno"].isin(perm_set)]
                pidx = pd.DatetimeIndex(pd.to_datetime(prices.index, errors="coerce", utc=True)).tz_convert(None).normalize()
                out = out[(out["date"] >= pidx.min()) & (out["date"] <= pidx.max())]
                if not out.empty:
                    return out[keep_cols]

        from_store = self._load_alpha_features_from_store(prices)
        if not from_store.empty:
            return from_store
        return self._build_alpha_features_fallback(prices)

    @staticmethod
    def _market_vol_series(macro: pd.DataFrame, index: pd.Index) -> pd.Series:
        if not isinstance(macro, pd.DataFrame) or macro.empty:
            return pd.Series(np.nan, index=index, dtype=float)
        if "vix_level" in macro.columns:
            s = pd.to_numeric(macro["vix_level"], errors="coerce").reindex(index).ffill()
            if s.notna().sum() > 0:
                return s
        if "vix_proxy" in macro.columns:
            return pd.to_numeric(macro["vix_proxy"], errors="coerce").reindex(index).ffill()
        return pd.Series(np.nan, index=index, dtype=float)

    def _generate_weights_alpha_engine(
        self,
        prices: pd.DataFrame,
        fundamentals: dict | None,
        macro: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.Series, dict] | None:
        if prices.empty:
            return None

        prices = prices.copy()
        prices.index = pd.DatetimeIndex(pd.to_datetime(prices.index, errors="coerce", utc=True)).tz_convert(None).normalize()
        feature_history = self._resolve_alpha_feature_history(prices=prices, fundamentals=fundamentals)
        if feature_history.empty:
            return None

        feature_history = feature_history.copy()
        feature_history["date"] = pd.to_datetime(feature_history["date"], errors="coerce", utc=True).dt.tz_convert(None).dt.normalize()
        feature_history = feature_history.dropna(subset=["date", "permno"])
        feature_history["permno"] = pd.to_numeric(feature_history["permno"], errors="coerce").astype("Int64")
        feature_history = feature_history.sort_values(["date", "permno"])

        idx = prices.index
        cols = pd.Index([int(c) for c in prices.columns])
        weights = pd.DataFrame(0.0, index=idx, columns=cols, dtype=float)

        try:
            regime_result = self.regime_manager.evaluate(macro, idx)
            regime = regime_result.target_exposure.reindex(idx).ffill().fillna(0.5)
            governor = regime_result.governor_state.reindex(idx).ffill().fillna("AMBER")
            governor_reason = regime_result.reason.reindex(idx).ffill().fillna("Fallback")
            market_state = regime_result.market_state.reindex(idx).ffill().fillna("NEUT")
        except Exception:
            regime = self._legacy_regime_series(idx, macro)
            governor = pd.Series("AMBER", index=idx, dtype=object)
            governor_reason = pd.Series("Fallback: legacy regime", index=idx, dtype=object)
            market_state = pd.Series("NEUT", index=idx, dtype=object)

        market_vol = self._market_vol_series(macro, idx)
        prepared = self.alpha_engine.prepare_feature_history(feature_history)
        if prepared.empty:
            return None

        held: set[int] = set()
        ratchet: dict[int, float] = {}
        stop_records: list[dict] = []
        telemetry_rows: list[dict] = []
        by_date = {d: g for d, g in prepared.groupby("date", sort=True)}
        latest_selected = pd.DataFrame()
        latest_candidate_scores: list[dict] = []
        prev_row_w = pd.Series(0.0, index=cols, dtype=float)

        for dt in idx:
            dt_key = pd.Timestamp(dt).normalize()
            budget_t = float(regime.loc[dt]) if dt in regime.index else 0.0
            today = by_date.get(dt_key)
            if today is None or today.empty:
                row_w = prev_row_w.copy()
                total = float(row_w.sum())
                if total > 0 and budget_t >= 0:
                    row_w = row_w * min(1.0, budget_t / total)
                weights.loc[dt] = row_w.values
                prev_row_w = row_w.copy()
                telemetry_rows.append(
                    {
                        "date": dt,
                        "alpha_score": np.nan,
                        "entry_trigger": 0,
                        "num_positions": int((row_w > 0).sum()),
                        "stop_loss_level": np.nan,
                        "turnover": np.nan,
                        "governor_state": str(governor.loc[dt]),
                        "regime_cap": budget_t,
                        "exit_rank": 0,
                        "exit_stop": 0,
                    }
                )
                continue

            plan = self.alpha_engine.build_daily_plan_from_snapshot(
                snapshot=today,
                regime_state=str(governor.loc[dt]),
                asof_date=dt,
                market_vol=float(market_vol.loc[dt]) if pd.notna(market_vol.loc[dt]) else None,
            )

            selected = plan.selected.copy()
            if not selected.empty:
                selected["permno"] = pd.to_numeric(selected["permno"], errors="coerce").astype("Int64")
                selected = selected.dropna(subset=["permno"])
                selected["permno"] = selected["permno"].astype(int)
                selected = selected.sort_values("composite_score", ascending=False).head(self.hysteresis_exit_rank)
            rank_map = {int(p): (i + 1) for i, p in enumerate(selected["permno"].tolist())} if not selected.empty else {}

            if selected.empty:
                row_w = prev_row_w.copy()
                total = float(row_w.sum())
                if total > 0 and budget_t >= 0:
                    row_w = row_w * min(1.0, budget_t / total)
                weights.loc[dt] = row_w.values
                prev_row_w = row_w.copy()
                latest_selected = selected.copy()
                latest_candidate_scores = []
                latest_stops = [ratchet[p] for p in held if p in ratchet]
                telemetry_rows.append(
                    {
                        "date": dt,
                        "alpha_score": np.nan,
                        "entry_trigger": 0,
                        "num_positions": int((row_w > 0).sum()),
                        "stop_loss_level": float(np.nanmean(latest_stops)) if latest_stops else np.nan,
                        "turnover": np.nan,
                        "governor_state": str(governor.loc[dt]),
                        "regime_cap": budget_t,
                        "exit_rank": 0,
                        "exit_stop": 0,
                    }
                )
                continue

            prev_held = set(held)
            held = {p for p in held if rank_map.get(p, self.hysteresis_exit_rank + 1) <= self.hysteresis_exit_rank}
            top_entries = [p for p, rk in rank_map.items() if rk <= self.alpha_top_n]
            held.update(top_entries)
            exit_rank = len(prev_held - held)

            selected_idx = selected.set_index("permno") if not selected.empty else pd.DataFrame()
            active = [p for p in held if p in selected_idx.index]
            stop_hits = 0
            final_active: list[int] = []
            for p in active:
                px = np.nan
                if "tri" in selected_idx.columns:
                    px = float(pd.to_numeric(selected_idx.at[p, "tri"], errors="coerce"))
                if not np.isfinite(px):
                    px = float(pd.to_numeric(selected_idx.at[p, "adj_close"], errors="coerce"))
                raw_stop = float(pd.to_numeric(selected_idx.at[p, "stop_price"], errors="coerce"))
                prev_stop = ratchet.get(p, raw_stop)
                stop_now = max(prev_stop, raw_stop) if self.ratchet_stops else raw_stop
                ratchet[p] = stop_now
                stop_records.append({"date": dt, "permno": int(p), "stop_loss_level": float(stop_now)})
                if np.isfinite(px) and np.isfinite(stop_now) and px <= stop_now:
                    stop_hits += 1
                    held.discard(p)
                    ratchet.pop(p, None)
                else:
                    final_active.append(p)

            for p in list(ratchet.keys()):
                if p not in held:
                    ratchet.pop(p, None)

            row_w = pd.Series(0.0, index=cols, dtype=float)
            if final_active and not selected_idx.empty:
                raw = pd.to_numeric(selected_idx.loc[final_active, "weight"], errors="coerce").fillna(0.0)
                total = float(raw.sum())
                budget = budget_t
                if total > 0 and budget > 0:
                    w = (raw / total) * budget
                    row_w.loc[w.index.astype(int)] = w.values
            weights.loc[dt] = row_w
            prev_row_w = row_w.copy()

            latest_selected = selected.copy()
            if (
                not selected.empty
                and {"permno", "composite_score", "stop_price"}.issubset(set(selected.columns))
            ):
                price_col = "tri" if "tri" in selected.columns else "adj_close"
                if price_col not in selected.columns:
                    price_col = "adj_close"
                latest_candidate_scores = (
                    selected.head(self.alpha_top_n)[["permno", "composite_score", price_col, "stop_price"]]
                    .rename(columns={price_col: "price", "composite_score": "alpha_score"})
                    .to_dict("records")
                )
            else:
                latest_candidate_scores = []
            latest_stops = [ratchet[p] for p in final_active if p in ratchet]
            telemetry_rows.append(
                {
                    "date": dt,
                    "alpha_score": float(pd.to_numeric(selected["composite_score"], errors="coerce").head(self.alpha_top_n).mean())
                    if not selected.empty
                    else np.nan,
                    "entry_trigger": max(0, len(held - prev_held)),
                    "num_positions": int(len(final_active)),
                    "stop_loss_level": float(np.nanmean(latest_stops)) if latest_stops else np.nan,
                    "turnover": np.nan,
                    "governor_state": str(governor.loc[dt]),
                    "regime_cap": float(regime.loc[dt]),
                    "exit_rank": int(exit_rank),
                    "exit_stop": int(stop_hits),
                }
            )

        turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
        telemetry = pd.DataFrame(telemetry_rows).set_index("date")
        telemetry["turnover"] = turnover.reindex(telemetry.index).astype(float)
        stop_history = pd.DataFrame(stop_records)

        # Build UI-compatible details.
        latest_dt = idx[-1]
        latest_px = prices.ffill().iloc[-1]
        stop_prices = {int(p): float(s) for p, s in ratchet.items() if p in cols}
        active_set = set(stop_prices.keys())
        states = {}
        for c in cols:
            p = int(c)
            px = float(pd.to_numeric(latest_px.get(c, np.nan), errors="coerce"))
            stp = stop_prices.get(p, np.nan)
            if p in active_set:
                state = "HOLD" if (np.isfinite(px) and np.isfinite(stp) and px > stp) else "AVOID"
                desc = "🧠 Alpha Hold" if state == "HOLD" else "⛔ Hit Ratchet Stop"
                color = "#00ff88" if state == "HOLD" else "#ff4444"
                support = stp if np.isfinite(stp) else px
            else:
                state, desc, color, support = "WAIT", "⏳ Not in Alpha Basket", "#888888", px
            states[p] = {"state": state, "desc": desc, "color": color, "support": round(float(support), 2)}

        latest_sel_idx = latest_selected.set_index("permno") if not latest_selected.empty else pd.DataFrame()
        score_map = {}
        if not latest_selected.empty:
            raw_score = pd.to_numeric(latest_selected["composite_score"], errors="coerce")
            score_norm = ((raw_score - raw_score.min()) / (raw_score.max() - raw_score.min() + 1e-9)) * 10.0
            for p, s in zip(latest_selected["permno"], score_norm):
                score_map[int(p)] = int(np.clip(round(float(s)), 0, 10))

        details = {
            "status": "🧠 ALPHA ENGINE",
            "mode": "alpha_engine",
            "k_values": {int(c): float(self.k_stop) for c in cols},
            "z_values": {int(c): float(self.z_entry) for c in cols},
            "vol_rank": {},
            "stop_prices": stop_prices,
            "buy_thresholds": {},
            "states": states,
            "conviction": {int(c): score_map.get(int(c), 0) for c in cols},
            "cv_trend": {int(c): 0 for c in cols},
            "cv_value": {int(c): 0 for c in cols},
            "cv_macro": 0,
            "cv_mom": {int(c): 0 for c in cols},
            "metrics": {"rz_score": {int(c): np.nan for c in cols}, "er_score": {int(c): np.nan for c in cols}},
            "quality_pass": {int(c): 1 for c in cols},
            "quality_cap_applied": {int(c): False for c in cols},
            "governor_state": str(governor.loc[latest_dt]),
            "governor_reason": str(governor_reason.loc[latest_dt]),
            "market_state": str(market_state.loc[latest_dt]),
            "target_exposure": float(regime.loc[latest_dt]),
            "matrix_exposure": float(regime.loc[latest_dt]),
            "throttle_score": float("nan"),
            "composite_z": float("nan"),
            "bocpd_prob": float("nan"),
            "alpha_telemetry": telemetry,
            "ratchet_history": stop_history,
            "top_alpha_candidates": latest_candidate_scores,
            "active_stop_losses": [{"permno": int(p), "stop_loss_level": float(v)} for p, v in stop_prices.items()],
            "hysteresis_exit_rank": int(self.hysteresis_exit_rank),
            "alpha_top_n": int(self.alpha_top_n),
            "alpha_entry_logic": str(self.alpha_entry_logic),
            "ratchet_enabled": bool(self.ratchet_stops),
        }
        return weights.astype(float), regime.astype(float), details

    # ── Weight Generation ───────────────────────────────────────────────────

    def generate_weights(
        self, prices, fundamentals, macro
    ) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
        """
        Full pipeline: Dynamic/Fixed params → Signals → Macro Defense → Weights.
        """
        if not isinstance(prices, pd.DataFrame):
            raise TypeError("prices must be a pandas DataFrame")

        if prices.empty or prices.shape[1] == 0:
            empty_idx = prices.index if isinstance(prices.index, pd.Index) else pd.Index([])
            empty_cols = prices.columns if isinstance(prices.columns, pd.Index) else pd.Index([])
            empty_weights = pd.DataFrame(0.0, index=empty_idx, columns=empty_cols, dtype=float)
            empty_regime = pd.Series(1.0, index=empty_idx, dtype=float)
            details = {
                "status": "⚪ NO DATA",
                "mode": "fixed" if not self.use_dynamic_params else "dynamic",
                "k_values": {},
                "z_values": {},
                "vol_rank": {},
                "stop_prices": {},
                "buy_thresholds": {},
                "states": {},
                "conviction": {},
                "cv_trend": {},
                "cv_value": {},
                "cv_macro": 0,
                "cv_mom": {},
                "metrics": {"rz_score": {}, "er_score": {}},
                "quality_pass": {},
                "quality_cap_applied": {},
                "governor_state": "AMBER",
                "governor_reason": "Fallback: empty input",
                "market_state": "NEUT",
                "target_exposure": 0.5,
                "matrix_exposure": 0.5,
                "throttle_score": 1.0,
                "composite_z": 0.0,
                "bocpd_prob": 0.0,
            }
            return empty_weights, empty_regime, details

        if self.use_alpha_engine and len(prices.index) >= 2:
            alpha_result = self._generate_weights_alpha_engine(
                prices=prices,
                fundamentals=fundamentals if isinstance(fundamentals, dict) else None,
                macro=macro,
            )
            if alpha_result is not None:
                return alpha_result

        # Guardrail for fresh/new tickers with <2 bars: emit neutral HOLD states.
        if len(prices.index) < 2:
            idx = prices.index
            cols = prices.columns
            try:
                regime_result = self.regime_manager.evaluate(macro, idx)
                regime = regime_result.target_exposure
                regime_latest = regime_result.latest()
            except Exception:
                regime = self._legacy_regime_series(idx, macro)
                regime_latest = {
                    "governor_state": "AMBER",
                    "reason": "Fallback: legacy regime series due to FR-041 evaluation error",
                    "market_state": "NEUT",
                    "target_exposure": float(regime.iloc[-1]) if len(regime) else 0.5,
                    "matrix_exposure": float(regime.iloc[-1]) if len(regime) else 0.5,
                    "throttle_score": 1.0,
                    "composite_z": 0.0,
                    "bocpd_prob": 0.0,
                }

            weights = pd.DataFrame(0.0, index=idx, columns=cols, dtype=float)
            last_price = prices.iloc[-1].fillna(0.0)
            states = {
                c: {
                    "state": "HOLD",
                    "desc": "🛡️ Insufficient history (Neutral)",
                    "color": "#888888",
                    "support": round(float(last_price.get(c, 0.0)), 2),
                }
                for c in cols
            }
            quality_status = pd.Series(1, index=cols, dtype=int)
            details = {
                "status": "⚪ NEUTRAL (<2 bars)",
                "mode": "fixed" if not self.use_dynamic_params else "dynamic",
                "k_values": {c: float(self.k_stop) for c in cols},
                "z_values": {c: float(self.z_entry) for c in cols},
                "vol_rank": {},
                "stop_prices": {c: float(last_price.get(c, 0.0)) for c in cols},
                "buy_thresholds": {c: float(last_price.get(c, 0.0)) for c in cols},
                "states": states,
                "conviction": {c: 0 for c in cols},
                "cv_trend": {c: 0 for c in cols},
                "cv_value": {c: 0 for c in cols},
                "cv_macro": 0,
                "cv_mom": {c: 0 for c in cols},
                "metrics": {
                    "rz_score": {c: float("nan") for c in cols},
                    "er_score": {c: float("nan") for c in cols},
                },
                "quality_pass": quality_status.to_dict(),
                "quality_cap_applied": {c: False for c in cols},
                "governor_state": regime_latest["governor_state"],
                "governor_reason": regime_latest["reason"],
                "market_state": regime_latest["market_state"],
                "target_exposure": float(regime_latest["target_exposure"]),
                "matrix_exposure": float(regime_latest["matrix_exposure"]),
                "throttle_score": float(regime_latest["throttle_score"]),
                "composite_z": float(regime_latest["composite_z"]),
                "bocpd_prob": float(regime_latest["bocpd_prob"]),
            }
            return weights, regime, details

        # ── 1. Get k/z (Adaptive or Fixed) ──────────────────────────────────
        if self.use_dynamic_params:
            k_matrix, z_matrix, vol_rank = self._compute_dynamic_params(prices)
        else:
            k_matrix = self.k_stop   # scalar broadcasts across DataFrame ops
            z_matrix = self.z_entry
            vol_rank = pd.DataFrame(0.5, index=prices.index, columns=prices.columns)

        # ── 2. Chandelier Exit (uses k_matrix) ──────────────────────────────
        tr = prices.diff().abs()
        atr = tr.rolling(self.atr_period).mean()
        highest_close = prices.rolling(self.atr_period).max()

        if isinstance(k_matrix, (int, float)):
            stop_level = highest_close - (k_matrix * atr)
        else:
            stop_level = highest_close - (k_matrix * atr)

        is_above_stop = (prices > stop_level).astype(float)

        # ── 3. Dip Hunter (uses z_matrix) ───────────────────────────────────
        ma = prices.rolling(self.lookback).mean()
        std = prices.rolling(self.lookback).std()

        if isinstance(z_matrix, (int, float)):
            buy_zone = ma + (z_matrix * std)
        else:
            buy_zone = ma + (z_matrix * std)

        dip_signal = prices < buy_zone

        # [FR-017] Green Candle Confirmation
        if self.green_candle:
            bounce = prices.diff() > 0
            dip_signal = dip_signal & bounce

        # ── 4. Combine: Hold if above stop OR buying the confirmed dip ──────
        raw_signal = (is_above_stop == 1) | dip_signal
        raw_signal = raw_signal.astype(float)

        # ── 5. Equal Weight Normalization ───────────────────────────────────
        row_sum = raw_signal.sum(axis=1).replace(0, np.nan)
        weights = raw_signal.div(row_sum, axis=0).fillna(0.0)

        # ── 6. Macro Defense (FR-041 Governor+Throttle+Matrix) ─────────────
        try:
            regime_result = self.regime_manager.evaluate(macro, prices.index)
            regime = regime_result.target_exposure
            regime_latest = regime_result.latest()
        except Exception:
            regime = self._legacy_regime_series(prices.index, macro)
            regime_latest = {
                "governor_state": "AMBER",
                "reason": "Fallback: legacy regime series due to FR-041 evaluation error",
                "market_state": "NEUT",
                "target_exposure": float(regime.iloc[-1]) if len(regime) else 0.5,
                "matrix_exposure": float(regime.iloc[-1]) if len(regime) else 0.5,
                "throttle_score": 1.0,
                "composite_z": 0.0,
                "bocpd_prob": 0.0,
            }

        weights = weights.mul(regime, axis=0)

        # ── 7. 5-State Classifier [FR-023] ─────────────────────────────────────
        #   HOLD  — Price > Stop, above buy zone. Trend healthy.
        #   BUY   — Price > Stop, in buy zone, green candle confirmed.
        #   WATCH — Price > Stop, in buy zone, waiting for green candle.
        #   AVOID — Price < Stop, above buy zone. Trend broken, wait for support.
        #   WAIT  — Price < Stop, below buy zone. Capitulation, watch for reversal.

        current_price = prices.iloc[-1]
        current_stop = stop_level.iloc[-1]
        current_buy = buy_zone.iloc[-1]
        if len(prices.index) >= 2:
            is_green = prices.iloc[-1] > prices.iloc[-2]
        else:
            is_green = pd.Series(False, index=current_price.index, dtype=bool)

        # For support price calculation: get MA and Std for deeper Z
        current_ma = ma.iloc[-1]
        current_std = std.iloc[-1]

        states = {}
        for ticker in current_price.index:
            p = current_price[ticker]
            s = current_stop[ticker]
            b = current_buy[ticker]
            g = is_green[ticker]

            # Skip NaN tickers
            if pd.isna(p) or pd.isna(s) or pd.isna(b):
                continue

            if p > s:
                # ── UPTREND (Price above Stop) ──
                if p > b:
                    state, desc, color = "HOLD", "🛡️ Trend Healthy", "#00ff88"
                    support = s  # Stop is the floor
                else:
                    if g:
                        state, desc, color = "BUY", "💎 Dip Confirmed (Green Candle)", "#00ff88"
                        support = s
                    else:
                        state, desc, color = "WATCH", "👀 Dip Detected (Wait for Green)", "#FFD700"
                        support = s
            else:
                # ── DOWNTREND (Price below Stop) ──
                if p > b:
                    state, desc, color = "AVOID", "⛔ Trend Broken (Wait for Support)", "#ff4444"
                    support = b  # Buy zone is the next support
                else:
                    state, desc, color = "WAIT", "⏳ Capitulation (Watch for Reversal)", "#888888"
                    # Deep support: one more std dev below buy zone
                    m = current_ma[ticker]
                    sd = current_std[ticker]
                    if not pd.isna(m) and not pd.isna(sd) and sd > 0:
                        # z_deep = current_z - 1.5 standard deviations
                        if self.use_dynamic_params:
                            z_now = z_matrix.iloc[-1][ticker] if ticker in z_matrix.columns else self.z_entry
                        else:
                            z_now = self.z_entry
                        z_deep = z_now - 1.5
                        support = m + (z_deep * sd)
                    else:
                        support = b * 0.95

            states[ticker] = {
                "state": state,
                "desc": desc,
                "color": color,
                "support": round(support, 2),
            }

        # ── 8. Conviction Scorecard [FR-024 v2 — L5 Alpha] ─────────────────────
        #   Vectorized, deterministic scoring (0-10). No LLM.
        #   A. Trend     (3pts): Price > MA200
        #   B. Value     (3pts): Robust Z-Score (MAD-based, crash-resistant)
        #   C. Macro     (2pts): VIX level + VIX trend direction
        #   D. Momentum  (2pts): Efficiency Ratio (fractal trend quality)

        # Advanced feature engineering
        er = self._calculate_efficiency_ratio(prices, window=10)
        rz_score = self._calculate_robust_z(prices, window=20)
        ma_20 = prices.rolling(20).mean()

        # A. Trend (3 pts) — unchanged, already solid
        ma_200 = prices.rolling(200).mean()
        score_trend = (prices > ma_200).astype(int) * 3

        # B. Value (3 pts) — ROBUST UPGRADE
        #    RZ < -3.0 → 3pts (massive outlier, deep value)
        #    RZ < -2.0 → 1pt  (significant dip)
        score_value = (rz_score < -3.0).astype(int) * 3
        score_value = score_value + ((rz_score >= -3.0) & (rz_score < -2.0)).astype(int) * 1

        # C. Macro (2 pts) — REGIME UPGRADE (absolute + trend)
        score_macro = self._macro_score(macro, prices.index)

        # D. Momentum (2 pts) — FRACTAL UPGRADE
        #    Price > MA20 AND ER > 0.4 → 2pts (clean efficient trend)
        #    Price > MA20 AND ER ≤ 0.4 → 1pt  (uptrend but choppy)
        #    Otherwise → 0pts (downtrend or random walk)
        is_uptrending = prices > ma_20
        is_efficient = er > 0.4
        score_mom = (is_uptrending & is_efficient).astype(int) * 2
        score_mom = score_mom + (is_uptrending & (~is_efficient)).astype(int) * 1

        # Total (0-10)
        total_conviction = score_trend + score_value + score_macro + score_mom

        # ── 9. Quality Penalty [FR-027] ────────────────────────────────────
        # Hybrid behavior:
        #   - Scanner uses hard filter (scan_universe).
        #   - Watchlist/detail keep visibility but cap conviction at 5 if quality fails.
        quality_status = pd.Series(1, index=prices.columns, dtype=int)
        raw_last_conviction = total_conviction.iloc[-1]
        capped_last_conviction = raw_last_conviction.copy()
        quality_cap_applied = pd.Series(False, index=prices.columns, dtype=bool)

        if isinstance(fundamentals, dict) and "quality_pass" in fundamentals:
            quality_status = self._latest_quality_status(fundamentals, prices.index, prices.columns)
            cap_vector = quality_status.replace({1: 10, 0: 5})
            capped_last_conviction = raw_last_conviction.clip(upper=cap_vector)
            quality_cap_applied = (quality_status == 0) & (raw_last_conviction >= 5)

        # Extract last row for details
        conviction_dict = capped_last_conviction.to_dict()
        trend_dict = score_trend.iloc[-1].to_dict()
        value_dict = score_value.iloc[-1].to_dict()
        mom_dict = score_mom.iloc[-1].to_dict()
        metrics = {
            "rz_score": rz_score.iloc[-1].to_dict(),
            "er_score": er.iloc[-1].to_dict(),
        }

        if self.use_dynamic_params:
            details = {
                "status": "🧬 ADAPTIVE",
                "mode": "dynamic",
                "k_values": k_matrix.iloc[-1].to_dict(),
                "z_values": z_matrix.iloc[-1].to_dict(),
                "vol_rank": vol_rank.iloc[-1].to_dict(),
                "stop_prices": stop_level.iloc[-1].to_dict(),
                "buy_thresholds": buy_zone.iloc[-1].to_dict(),
                "states": states,
                "conviction": conviction_dict,
                "cv_trend": trend_dict,
                "cv_value": value_dict,
                "cv_macro": score_macro,
                "cv_mom": mom_dict,
                "metrics": metrics,
                "quality_pass": quality_status.to_dict(),
                "quality_cap_applied": quality_cap_applied.to_dict(),
                "governor_state": regime_latest["governor_state"],
                "governor_reason": regime_latest["reason"],
                "market_state": regime_latest["market_state"],
                "target_exposure": float(regime_latest["target_exposure"]),
                "matrix_exposure": float(regime_latest["matrix_exposure"]),
                "throttle_score": float(regime_latest["throttle_score"]),
                "composite_z": float(regime_latest["composite_z"]),
                "bocpd_prob": float(regime_latest["bocpd_prob"]),
            }
        else:
            details = {
                "status": f"📌 FIXED (k={self.k_stop}, z={self.z_entry})",
                "mode": "fixed",
                "k_values": {c: self.k_stop for c in prices.columns},
                "z_values": {c: self.z_entry for c in prices.columns},
                "vol_rank": {},
                "stop_prices": stop_level.iloc[-1].to_dict(),
                "buy_thresholds": buy_zone.iloc[-1].to_dict(),
                "states": states,
                "conviction": conviction_dict,
                "cv_trend": trend_dict,
                "cv_value": value_dict,
                "cv_macro": score_macro,
                "cv_mom": mom_dict,
                "metrics": metrics,
                "quality_pass": quality_status.to_dict(),
                "quality_cap_applied": quality_cap_applied.to_dict(),
                "governor_state": regime_latest["governor_state"],
                "governor_reason": regime_latest["reason"],
                "market_state": regime_latest["market_state"],
                "target_exposure": float(regime_latest["target_exposure"]),
                "matrix_exposure": float(regime_latest["matrix_exposure"]),
                "throttle_score": float(regime_latest["throttle_score"]),
                "composite_z": float(regime_latest["composite_z"]),
                "bocpd_prob": float(regime_latest["bocpd_prob"]),
            }

        return weights, regime, details

    # ── Public API: Universe Scanner [FR-026] ──────────────────────────────────

    def scan_universe(
        self,
        prices_wide: pd.DataFrame,
        macro: pd.DataFrame,
        fundamentals_wide: dict | None = None,
        top_n: int = 5,
        mode: str = "default",
        earnings_blackout_days: int = 5,
        catalyst_lookback_days: int = 7,
        return_metrics: bool = False,
    ) -> pd.DataFrame | tuple[pd.DataFrame, dict]:
        """
        [FR-026] Trend + Quality + L5 scanner.
        Memory-safe: operates on tail(250) slice (~4MB).
        Returns DataFrame of top opportunities (best available market candidates).
        """
        gate_metrics = {
            "universe_size": int(prices_wide.shape[1]),
            "trend_pass": 0,
            "quality_pass": 0,
            "catalyst_pass": 0,
            "final_survivors": 0,
            "earnings_risk": 0,
            "shown": 0,
        }

        # ── PRE-SCAN: slice to last 250 days (enough for MA200) ──
        p = prices_wide.tail(250)
        if p.empty or len(p) < 200:
            empty = pd.DataFrame()
            return (empty, gate_metrics) if return_metrics else empty

        # ── PASS 1: CHEAP GATE — Trend Filter ──
        ma200 = p.rolling(200).mean()
        trend_mask = (p.iloc[-1] > ma200.iloc[-1]).fillna(False)
        gate_metrics["trend_pass"] = int(trend_mask.sum())

        # ── PASS 1.5: QUALITY GATE [FR-027] ──
        # Hard filter in scanner: only investable names pass.
        qual_status = self._latest_quality_status(fundamentals_wide, p.index, trend_mask.index)
        qual_mask = qual_status.astype(bool)
        gate_metrics["quality_pass"] = int(qual_mask.sum())
        final_mask = trend_mask & qual_mask

        # [FR-034] Optional catalyst mode: keep only recent earnings names.
        mode_norm = str(mode).strip().lower()
        next_earnings_dt, last_earnings_dt = self._latest_earnings_dates(
            fundamentals_wide,
            trend_mask.index,
        )
        asof_date = pd.Timestamp(p.index[-1]).normalize()
        if mode_norm == "fresh_catalysts":
            days_since_earnings = (asof_date - last_earnings_dt).dt.days
            catalyst_mask = days_since_earnings.between(0, max(0, int(catalyst_lookback_days)), inclusive="both")
            final_mask = final_mask & catalyst_mask.fillna(False)
            gate_metrics["catalyst_pass"] = int((trend_mask & qual_mask & catalyst_mask.fillna(False)).sum())
        else:
            gate_metrics["catalyst_pass"] = int((trend_mask & qual_mask).sum())

        candidates = final_mask[final_mask].index.tolist()
        gate_metrics["final_survivors"] = len(candidates)

        if not candidates:
            empty = pd.DataFrame()  # Bear market, nothing passed
            return (empty, gate_metrics) if return_metrics else empty

        # ── PASS 2: FULL L5 ALPHA on candidates only ──
        p_scan = p[candidates]
        prices_now = p_scan.iloc[-1]

        # Robust Z (Value)
        rz = self._calculate_robust_z(p_scan, window=20).iloc[-1]

        # Efficiency Ratio (Momentum Quality)
        er = self._calculate_efficiency_ratio(p_scan, window=10).iloc[-1]

        # MA20 (short-term trend baseline)
        ma20 = p_scan.rolling(20).mean().iloc[-1]

        # Macro (scalar — same for all)
        score_macro = self._macro_score(macro, p.index)

        # ── SCORING (vectorized) ──
        score_trend = 3  # All passed gate 1

        score_value = (rz < -3.0).astype(int) * 3
        score_value = score_value + ((rz >= -3.0) & (rz < -2.0)).astype(int) * 1

        is_up = prices_now > ma20
        score_mom = (is_up & (er > 0.4)).astype(int) * 2
        score_mom = score_mom + (is_up & (er <= 0.4)).astype(int) * 1

        total = score_trend + score_value + score_macro + score_mom

        # ── BUILD RESULTS ──
        # 1-day price change
        prev_close = p_scan.iloc[-2]
        pct_1d = ((prices_now - prev_close) / prev_close)

        results = pd.DataFrame({
            "permno": candidates,
            "score": total.values,
            "price": prices_now.values,
            "pct_1d": pct_1d.values,
            "rz": rz.values,
            "er": er.values,
            "trend_pts": score_trend,
            "value_pts": score_value.values,
            "macro_pts": score_macro,
            "mom_pts": score_mom.values,
        })

        # [FR-034] Earnings event overlays for scanner explainability.
        next_aligned = pd.to_datetime(next_earnings_dt.reindex(candidates), errors="coerce")
        last_aligned = pd.to_datetime(last_earnings_dt.reindex(candidates), errors="coerce")
        days_to = (next_aligned - asof_date).dt.days.astype("float32")
        days_since = (asof_date - last_aligned).dt.days.astype("float32")
        risk_days = max(0, int(earnings_blackout_days) - 1)
        earnings_risk = days_to.between(0, risk_days, inclusive="both").fillna(False)

        results["days_to_earnings"] = days_to.to_numpy()
        results["days_since_earnings"] = days_since.to_numpy()
        results["earnings_risk"] = earnings_risk.to_numpy()

        # Sort desc, top N (no hard cutoff — frontend handles visual tiers)
        results = results.dropna(subset=["score"])
        results = results.sort_values("score", ascending=False).head(top_n)
        gate_metrics["earnings_risk"] = int(results["earnings_risk"].sum()) if "earnings_risk" in results.columns else 0
        gate_metrics["shown"] = len(results)

        return (results, gate_metrics) if return_metrics else results

    # ── Public API for Dashboard ────────────────────────────────────────────

    def get_signals(self, prices: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """
        Returns raw signal levels for the UI to visualize.
        Uses FIXED parameters (self.k_stop, self.z_entry) for simple charting.
        """
        tr = prices.diff().abs()
        atr = tr.rolling(self.atr_period).mean()
        highest_close = prices.rolling(self.atr_period).max()
        stop_level = highest_close - (self.k_stop * atr)

        ma = prices.rolling(self.lookback).mean()
        std = prices.rolling(self.lookback).std()
        buy_zone = ma + (self.z_entry * std)

        log_px = np.log(prices.clip(lower=0.01))
        log_ma = log_px.rolling(self.lookback).mean()
        log_std = log_px.rolling(self.lookback).std()
        z_score = (log_px - log_ma) / log_std

        bounce = prices.diff() > 0

        return {
            "z_score": z_score,
            "atr": atr,
            "stop_level": stop_level,
            "buy_zone": buy_zone,
            "ma": ma,
            "std": std,
            "bounce": bounce,
        }
