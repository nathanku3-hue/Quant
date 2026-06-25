import numpy as np
import pandas as pd

from strategies.regime_manager import GovernorState, MarketState, RegimeManager


def test_matrix_mapping_enforces_red_long_only_safety():
    mgr = RegimeManager()

    assert mgr.matrix_exposure(GovernorState.RED.value, MarketState.NEG.value) == 0.0
    assert mgr.matrix_exposure(GovernorState.RED.value, MarketState.NEUT.value) == 0.0
    assert mgr.matrix_exposure(GovernorState.RED.value, MarketState.POS.value) == 0.20
    assert mgr.matrix_exposure(GovernorState.GREEN.value, MarketState.POS.value) == 1.3


def test_red_floor_behavior_and_red_pos_cap():
    idx = pd.date_range("2025-01-01", periods=120, freq="B")
    momentum = pd.Series(np.linspace(-2.0, 2.0, len(idx)), index=idx)
    liq_imp = pd.Series(np.linspace(-1.5, 2.0, len(idx)), index=idx)
    vrp = pd.Series(np.linspace(-1.0, 1.5, len(idx)), index=idx)
    vix = pd.Series(np.linspace(35.0, 15.0, len(idx)), index=idx)

    macro = pd.DataFrame(
        {
            "repo_spread_bps": 12.0,  # explicit RED trigger
            "credit_freeze": False,
            "liquidity_impulse": liq_imp.values,
            "vix_level": vix.values,
            "us_net_liquidity_mm": 1_000_000.0,
            "vrp": vrp.values,
            "momentum_proxy": momentum.values,
        },
        index=idx,
    )

    mgr = RegimeManager()
    result = mgr.evaluate(macro, idx)

    # RED + NEG/NEUT must floor at zero.
    red_neg_neut = (result.governor_state == GovernorState.RED.value) & (
        result.market_state.isin([MarketState.NEG.value, MarketState.NEUT.value])
    )
    assert (result.target_exposure.loc[red_neg_neut] == 0.0).all()

    # RED + POS must never exceed 0.20.
    red_pos = (result.governor_state == GovernorState.RED.value) & (
        result.market_state == MarketState.POS.value
    )
    assert red_pos.any()
    assert (result.target_exposure.loc[red_pos] <= 0.20).all()


def test_missing_data_fallback_uses_legacy_scalar_and_neutral_default():
    idx = pd.date_range("2025-06-01", periods=3, freq="B")
    mgr = RegimeManager()

    macro_scalar = pd.DataFrame({"regime_scalar": [0.80, 0.65, 0.40]}, index=idx)
    result_scalar = mgr.evaluate(macro_scalar, idx)
    np.testing.assert_allclose(result_scalar.target_exposure.values, [0.80, 0.65, 0.40], rtol=1e-12, atol=1e-12)
    assert result_scalar.governor_state.tolist() == [
        GovernorState.GREEN.value,
        GovernorState.AMBER.value,
        GovernorState.RED.value,
    ]
    assert result_scalar.reason.str.contains("Fallback: FR-041 inputs missing; using legacy regime_scalar=").all()

    macro_missing = pd.DataFrame(index=idx)
    result_missing = mgr.evaluate(macro_missing, idx)
    np.testing.assert_allclose(result_missing.target_exposure.values, [0.5, 0.5, 0.5], rtol=1e-12, atol=1e-12)
    assert (result_missing.governor_state == GovernorState.AMBER.value).all()
