import numpy as np
import pandas as pd

from strategies.investor_cockpit import InvestorCockpitStrategy


def _make_feature_history(prices: pd.DataFrame, score_map: dict[tuple[pd.Timestamp, int], float]) -> pd.DataFrame:
    rows = []
    for dt in prices.index:
        for permno in prices.columns:
            px = float(prices.loc[dt, permno])
            rows.append(
                {
                    "date": dt,
                    "permno": int(permno),
                    "adj_close": px,
                    "volume": 2_000_000.0,
                    "sma200": px * 0.95,
                    "dist_sma20": -0.02,
                    "rsi_14d": 20.0,
                    "atr_14d": 1.0,
                    "yz_vol_20d": 0.25 + (0.02 * (int(permno) % 3)),
                    "composite_score": float(score_map.get((pd.Timestamp(dt), int(permno)), 0.0)),
                    "trend_veto": False,
                    # Precomputed fields to bypass rolling-window warmup in tiny synthetic fixtures.
                    "adv20": 20_000_000.0,
                    "rsi_threshold": 30.0,
                    "prev_rsi": 35.0,
                    "prior_50d_high": px * 1.10,
                }
            )
    return pd.DataFrame(rows)


def test_phase15_weights_respect_regime_cap():
    idx = pd.date_range("2026-01-01", periods=8, freq="B")
    prices = pd.DataFrame(
        {
            101: np.linspace(100.0, 108.0, len(idx)),
            202: np.linspace(50.0, 55.0, len(idx)),
        },
        index=idx,
    )
    scores = {(dt, 101): 3.0 for dt in idx}
    scores.update({(dt, 202): 2.5 for dt in idx})
    features = _make_feature_history(prices, scores)
    macro = pd.DataFrame({"regime_scalar": 0.5, "vix_level": 20.0}, index=idx)

    strat = InvestorCockpitStrategy(
        use_alpha_engine=True,
        alpha_top_n=1,
        hysteresis_exit_rank=2,
        ratchet_stops=True,
    )
    weights, regime, details = strat.generate_weights(
        prices=prices,
        fundamentals={"feature_history": features},
        macro=macro,
    )

    assert isinstance(details.get("alpha_telemetry"), pd.DataFrame)
    assert (weights.sum(axis=1) <= 0.5 + 1e-12).all()
    assert (regime <= 0.5 + 1e-12).all()


def test_phase15_history_with_partial_missing_precomputed_does_not_crash_and_respects_cap():
    idx = pd.date_range("2026-01-01", periods=8, freq="B")
    prices = pd.DataFrame(
        {
            101: np.linspace(100.0, 108.0, len(idx)),
            202: np.linspace(50.0, 55.0, len(idx)),
        },
        index=idx,
    )
    scores = {(dt, 101): 3.0 for dt in idx}
    scores.update({(dt, 202): 2.5 for dt in idx})
    features = _make_feature_history(prices, scores)
    missing_day = idx[3]
    missing_mask = (pd.to_datetime(features["date"]) == missing_day) & (features["permno"] == 101)
    features.loc[missing_mask, "rsi_threshold"] = np.nan

    macro = pd.DataFrame({"regime_scalar": 0.5, "vix_level": 20.0}, index=idx)
    strat = InvestorCockpitStrategy(
        use_alpha_engine=True,
        alpha_top_n=1,
        hysteresis_exit_rank=2,
        ratchet_stops=True,
    )
    weights, regime, details = strat.generate_weights(
        prices=prices,
        fundamentals={"feature_history": features},
        macro=macro,
    )

    assert isinstance(details.get("alpha_telemetry"), pd.DataFrame)
    assert (weights.sum(axis=1) <= 0.5 + 1e-12).all()
    assert (regime <= 0.5 + 1e-12).all()


def test_hysteresis_rank_buffer_hold_then_exit():
    idx = pd.to_datetime(["2026-01-05", "2026-01-06", "2026-01-07"])
    prices = pd.DataFrame(
        {
            101: [100.0, 101.0, 102.0],
            202: [90.0, 92.0, 93.0],
            303: [80.0, 81.0, 85.0],
        },
        index=idx,
    )
    scores = {
        (idx[0], 101): 10.0,
        (idx[0], 202): 8.0,
        (idx[0], 303): 7.0,
        (idx[1], 101): 8.5,   # rank 2 -> should be held via hysteresis
        (idx[1], 202): 9.5,   # rank 1 -> new entry
        (idx[1], 303): 7.0,
        (idx[2], 101): 6.0,   # rank 3 -> should exit when hysteresis rank=2
        (idx[2], 202): 9.2,
        (idx[2], 303): 8.9,
    }
    features = _make_feature_history(prices, scores)
    macro = pd.DataFrame({"regime_scalar": 1.0, "vix_level": 20.0}, index=idx)

    strat = InvestorCockpitStrategy(
        use_alpha_engine=True,
        alpha_top_n=1,
        hysteresis_exit_rank=2,
        ratchet_stops=True,
    )
    weights, _, _ = strat.generate_weights(
        prices=prices,
        fundamentals={"feature_history": features},
        macro=macro,
    )

    assert weights.loc[idx[1], 101] > 0.0
    assert weights.loc[idx[2], 101] == 0.0


def test_ratchet_stop_is_non_decreasing():
    idx = pd.date_range("2026-02-01", periods=6, freq="B")
    prices = pd.DataFrame({101: np.linspace(100.0, 110.0, len(idx))}, index=idx)
    scores = {(dt, 101): 9.0 for dt in idx}
    features = _make_feature_history(prices, scores)
    macro = pd.DataFrame({"regime_scalar": 1.0, "vix_level": 35.0}, index=idx)

    strat = InvestorCockpitStrategy(
        use_alpha_engine=True,
        alpha_top_n=1,
        hysteresis_exit_rank=2,
        ratchet_stops=True,
    )
    _, _, details = strat.generate_weights(
        prices=prices,
        fundamentals={"feature_history": features},
        macro=macro,
    )

    hist = details.get("ratchet_history")
    assert isinstance(hist, pd.DataFrame)
    p_hist = hist[hist["permno"] == 101].sort_values("date")
    diffs = p_hist["stop_loss_level"].diff().fillna(0.0)
    assert (diffs >= -1e-12).all()
