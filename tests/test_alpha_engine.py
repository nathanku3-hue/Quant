import numpy as np
import pandas as pd
import pytest

from strategies.alpha_engine import AlphaEngine, AlphaEngineConfig


def _make_features(
    n_days: int = 280,
    perm2_volume: float = 2_000_000.0,
    perm2_base_price: float = 50.0,
    perm2_slope: float = 0.15,
) -> pd.DataFrame:
    idx = pd.date_range("2024-01-02", periods=n_days, freq="B")
    records: list[dict] = []

    def _add_asset(permno: int, base_price: float, slope: float, yz: float, atr: float, score: float):
        for i, d in enumerate(idx):
            close = base_price + (slope * i)
            rsi = 60.0 + 2.0 * np.sin(i / 12.0) if permno == 101 else (20.0 if permno == 202 else 50.0)
            if i == len(idx) - 1 and permno == 101:
                rsi = 40.0  # above static 30, but below adaptive percentile from its own history

            dist = -0.02 if (i == len(idx) - 1 and permno in (101, 202)) else 0.01
            vol = perm2_volume if permno == 202 else 2_000_000.0

            records.append(
                {
                    "date": d,
                    "permno": permno,
                    "adj_close": close,
                    "volume": vol,
                    "sma200": close - 8.0,
                    "dist_sma20": dist,
                    "rsi_14d": rsi,
                    "atr_14d": atr,
                    "yz_vol_20d": yz,
                    "composite_score": score,
                    "trend_veto": False,
                }
            )

    _add_asset(101, base_price=100.0, slope=0.25, yz=0.20, atr=2.0, score=3.1)
    _add_asset(202, base_price=perm2_base_price, slope=perm2_slope, yz=0.35, atr=1.5, score=2.4)
    _add_asset(303, base_price=30.0, slope=0.10, yz=0.40, atr=1.2, score=0.8)
    return pd.DataFrame.from_records(records)


def _make_breakout_only_features() -> pd.DataFrame:
    features = _make_features(perm2_volume=1_000.0)
    asof = pd.Timestamp(features["date"].max())
    today = pd.to_datetime(features["date"]) == asof
    # Block dip gate on the as-of bar while preserving trend/tradability for breakout checks.
    features.loc[today, "rsi_14d"] = 80.0
    features.loc[today, "dist_sma20"] = 0.05
    return features


def test_default_min_price_floor_is_one_dollar():
    assert AlphaEngineConfig().min_price == 1.0


def test_regime_normalization_fails_safe_to_red_budget():
    assert AlphaEngine.regime_budget(" GREEN ") == 1.0
    assert AlphaEngine.regime_budget(" red ") == 0.0
    assert AlphaEngine.regime_budget("unknown-state") == 0.0


def test_low_price_but_liquid_name_is_tradable_at_one_dollar_floor():
    features = _make_features(
        perm2_volume=15_000_000.0,
        perm2_base_price=1.2,
        perm2_slope=0.0,
    )
    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=50.0,
        top_n=3,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="GREEN")

    assert not plan.selected.empty
    selected_202 = plan.selected[plan.selected["permno"].astype(int) == 202]
    assert not selected_202.empty
    row = selected_202.iloc[0]
    assert float(row["adj_close"]) >= cfg.min_price
    assert float(row["adv20"]) >= cfg.min_adv20


def test_red_regime_forces_zero_budget():
    features = _make_features()
    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=50.0,
        top_n=2,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="RED")

    assert plan.regime_budget == 0.0
    assert plan.budget_utilization == 0.0
    assert plan.weights.empty
    assert plan.selected.empty


def test_green_plan_respects_budget_and_stop_formula():
    features = _make_features()
    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=50.0,
        top_n=2,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="GREEN", market_vol=35.0)

    assert not plan.selected.empty
    assert 0.0 < plan.budget_utilization <= 1.0 + 1e-12
    assert float(plan.weights.sum()) <= 1.0 + 1e-12
    assert plan.selected["reason_code"].str.contains("MOM_DIP_GREEN_FIXED").all()

    # High vol regime => atr multiplier should be 5.0
    row = plan.selected.iloc[0]
    expected_stop = float(row["adj_close"]) - (5.0 * float(row["atr_14d"]))
    np.testing.assert_allclose(float(row["stop_price"]), expected_stop, rtol=1e-12, atol=1e-12)


def test_adaptive_rsi_can_select_when_static_is_blocked():
    # Make permno 202 non-tradable so only permno 101 can qualify in adaptive mode.
    # Clamp last-bar closes to prior highs for tradable names so this test isolates RSI gating,
    # not GREEN breakout entries.
    features = _make_features(perm2_volume=1_000.0)
    asof = pd.Timestamp(features["date"].max())
    today = pd.to_datetime(features["date"]) == asof
    for permno in (101, 303):
        asset_mask = features["permno"] == permno
        prev_close = float(features.loc[asset_mask, "adj_close"].iloc[-2])
        features.loc[today & asset_mask, "adj_close"] = prev_close

    static_cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=30.0,
        top_n=2,
        max_position_weight=1.0,
    )
    static_engine = AlphaEngine(static_cfg)
    static_plan = static_engine.build_daily_plan(features=features, regime_state="GREEN")
    assert static_plan.selected.empty

    adaptive_cfg = AlphaEngineConfig(
        use_adaptive_rsi=True,
        adaptive_rsi_percentile=0.05,
        adaptive_rsi_window=252,
        adaptive_rsi_min_periods=63,
        top_n=2,
        max_position_weight=1.0,
    )
    adaptive_engine = AlphaEngine(adaptive_cfg)
    adaptive_plan = adaptive_engine.build_daily_plan(features=features, regime_state="GREEN")

    assert not adaptive_plan.selected.empty
    assert 101 in set(adaptive_plan.selected["permno"].astype(int).tolist())
    assert adaptive_plan.selected["reason_code"].str.contains("ADAPT").all()


def test_adaptive_threshold_is_lagged_prior_only():
    features = _make_features(perm2_volume=1_000.0)
    cfg = AlphaEngineConfig(
        use_adaptive_rsi=True,
        adaptive_rsi_percentile=0.05,
        adaptive_rsi_window=252,
        adaptive_rsi_min_periods=63,
        top_n=2,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="GREEN")

    assert not plan.selected.empty
    row = plan.selected[plan.selected["permno"].astype(int) == 101].iloc[0]
    asof = pd.Timestamp(plan.asof_date)
    hist = features[(features["permno"] == 101) & (pd.to_datetime(features["date"]) < asof)]["rsi_14d"]
    expected = float(hist.tail(252).quantile(0.05))
    np.testing.assert_allclose(float(row["rsi_threshold"]), expected, rtol=1e-12, atol=1e-12)
    assert float(row["rsi_14d"]) <= float(row["rsi_threshold"])


def test_amber_budget_hard_cap():
    features = _make_features()
    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=50.0,
        top_n=3,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="AMBER")

    assert plan.regime_budget == 0.5
    assert float(plan.weights.sum()) <= 0.5 + 1e-12
    assert plan.budget_utilization <= 0.5 + 1e-12


def test_candidate_ranking_uses_numeric_composite_score_ordering():
    features = _make_features()
    features["composite_score"] = features["composite_score"].astype(object)
    asof = pd.Timestamp(features["date"].max())
    today = pd.to_datetime(features["date"]) == asof
    features.loc[today & (features["permno"] == 101), "composite_score"] = "9"
    features.loc[today & (features["permno"] == 202), "composite_score"] = "10"
    features.loc[today & (features["permno"] == 303), "composite_score"] = "2"

    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=30.0,
        entry_logic="breakout",
        top_n=2,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="GREEN", asof_date=asof)

    assert not plan.selected.empty
    selected_permnos = plan.selected["permno"].astype(int).tolist()
    assert selected_permnos == [202, 101]
    assert 303 not in selected_permnos


def test_missing_required_columns_raise_contract_error():
    features = _make_features().drop(columns=["trend_veto"])
    engine = AlphaEngine(AlphaEngineConfig())
    try:
        engine.build_daily_plan(features=features, regime_state="GREEN")
        raise AssertionError("Expected ValueError for missing required columns")
    except ValueError as exc:
        assert "Missing required feature columns" in str(exc)


def test_build_daily_plan_from_snapshot_computes_history_fields_before_day_filter():
    features = _make_features()
    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=50.0,
        top_n=2,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    asof = pd.Timestamp(features["date"].max())

    baseline = engine.build_daily_plan(
        features=features,
        regime_state="GREEN",
        asof_date=asof,
    )
    from_snapshot = engine.build_daily_plan_from_snapshot(
        snapshot=features,
        regime_state="GREEN",
        asof_date=asof,
    )

    assert not from_snapshot.selected.empty
    assert from_snapshot.selected["permno"].astype(int).tolist() == baseline.selected["permno"].astype(int).tolist()
    lhs = from_snapshot.weights.sort_index()
    rhs = baseline.weights.sort_index().reindex(lhs.index)
    np.testing.assert_allclose(lhs.to_numpy(dtype=float), rhs.to_numpy(dtype=float), rtol=0.0, atol=1e-12)


def test_build_daily_plan_from_snapshot_single_day_requires_precomputed_fields():
    features = _make_features()
    asof = pd.Timestamp(features["date"].max())
    one_day_snapshot = features.loc[pd.to_datetime(features["date"]) == asof].copy()
    engine = AlphaEngine(AlphaEngineConfig())

    with pytest.raises(ValueError, match="Single-day snapshot requires precomputed columns"):
        engine.build_daily_plan_from_snapshot(
            snapshot=one_day_snapshot,
            regime_state="GREEN",
            asof_date=asof,
        )


def test_build_daily_plan_from_snapshot_missing_required_columns_raises_contract_error():
    snapshot = _make_features().drop(columns=["trend_veto"])
    engine = AlphaEngine(AlphaEngineConfig())
    with pytest.raises(ValueError, match="Missing required feature columns"):
        engine.build_daily_plan_from_snapshot(snapshot=snapshot, regime_state="GREEN")


def test_trend_veto_string_false_is_parsed_as_false():
    features = _make_features()
    asof = pd.Timestamp(features["date"].max())
    today = pd.to_datetime(features["date"]) == asof
    features.loc[today, "trend_veto"] = "False"

    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=50.0,
        top_n=3,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="GREEN", asof_date=asof)
    assert not plan.selected.empty


def test_trend_veto_unknown_tokens_default_to_veto_true():
    features = _make_features()
    asof = pd.Timestamp(features["date"].max())
    today = pd.to_datetime(features["date"]) == asof
    features.loc[today, "trend_veto"] = "MAYBE"

    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=50.0,
        top_n=3,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="GREEN", asof_date=asof)
    assert plan.selected.empty


def test_green_breakout_entry_triggers_when_dip_path_is_blocked():
    features = _make_breakout_only_features()
    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=30.0,
        top_n=3,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="GREEN")

    assert not plan.selected.empty
    assert (plan.selected["reason_code"] == "MOM_BREAKOUT_GREEN_FIXED").all()
    assert (
        pd.to_numeric(plan.selected["rsi_14d"], errors="coerce")
        > pd.to_numeric(plan.selected["rsi_threshold"], errors="coerce")
    ).all()
    assert (pd.to_numeric(plan.selected["adj_close"], errors="coerce") > plan.selected["prior_50d_high"]).all()


def test_dip_entry_logic_disables_breakout_path_when_dip_is_blocked():
    features = _make_breakout_only_features()
    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=30.0,
        entry_logic="dip",
        top_n=3,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="GREEN")

    assert plan.selected.empty


def test_breakout_entry_logic_selects_breakout_only_reason():
    features = _make_breakout_only_features()
    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=30.0,
        entry_logic="breakout",
        top_n=3,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="GREEN")

    assert not plan.selected.empty
    assert (plan.selected["reason_code"] == "MOM_BREAKOUT_GREEN_FIXED").all()


def test_invalid_entry_logic_raises_value_error():
    with pytest.raises(ValueError):
        AlphaEngine(AlphaEngineConfig(entry_logic="not_supported"))


def test_breakout_entry_is_disabled_in_amber_and_red():
    features = _make_breakout_only_features()
    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=30.0,
        top_n=3,
        max_position_weight=1.0,
    )
    engine = AlphaEngine(cfg)
    amber = engine.build_daily_plan(features=features, regime_state="AMBER")
    red = engine.build_daily_plan(features=features, regime_state="RED")

    assert amber.selected.empty
    assert red.selected.empty


def test_semantic_scale_uses_locked_sigma_formula():
    values = pd.Series([1.0, 2.0, 4.0, 7.0], dtype=float)
    scaled, telemetry = AlphaEngine._semantic_scale_with_fallback(
        values,
        epsilon_floor=1e-6,
        min_window_size=2,
    )

    median = float(values.median())
    mad = float((values - median).abs().median())
    robust_sigma = max(1.4826 * mad, 1e-6)
    expected = (values - median) / robust_sigma
    np.testing.assert_allclose(scaled.to_numpy(dtype=float), expected.to_numpy(dtype=float), rtol=0.0, atol=1e-12)
    assert telemetry["fallback_rows"] == 0
    assert telemetry["row_total"] == 1
    assert telemetry["fallback_rate"] == 0.0


def test_semantic_scale_routes_to_percentile_fallback_when_window_is_small():
    values = pd.Series([5.0, 15.0, 25.0], dtype=float)
    scaled, telemetry = AlphaEngine._semantic_scale_with_fallback(
        values,
        epsilon_floor=1e-6,
        min_window_size=5,
    )

    expected = ((values.rank(method="average", pct=True) - 0.5) * 2.0).astype(float)
    np.testing.assert_allclose(scaled.to_numpy(dtype=float), expected.to_numpy(dtype=float), rtol=0.0, atol=1e-12)
    assert telemetry["fallback_rows"] == 1
    assert telemetry["row_total"] == 1
    assert telemetry["fallback_rate"] == 1.0


def test_plan_records_semantic_fallback_rate_arithmetic():
    features = _make_features()
    cfg = AlphaEngineConfig(
        use_adaptive_rsi=False,
        static_rsi_threshold=50.0,
        top_n=2,
        max_position_weight=1.0,
        semantic_min_window_size=5,
    )
    engine = AlphaEngine(cfg)
    plan = engine.build_daily_plan(features=features, regime_state="GREEN")
    assert not plan.selected.empty

    row = plan.selected.iloc[0]
    fallback_rows = int(row["semantic_fallback_rows"])
    row_total = int(row["semantic_row_total"])
    fallback_rate = float(row["semantic_fallback_rate"])
    expected_rate = float(fallback_rows) / float(row_total) if row_total > 0 else 0.0
    np.testing.assert_allclose(fallback_rate, expected_rate, rtol=0.0, atol=1e-12)
