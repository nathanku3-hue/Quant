import numpy as np
import pandas as pd
import pytest

from strategies.stop_loss import ATRCalculator
from strategies.stop_loss import PortfolioDrawdownMonitor
from strategies.stop_loss import PositionStop
from strategies.stop_loss import StopLossConfig
from strategies.stop_loss import StopLossManager
from strategies.stop_loss import create_stop_loss_system


@pytest.fixture
def sample_prices() -> pd.Series:
    dates = pd.date_range("2020-01-01", periods=120, freq="D")
    up = 100.0 + 0.5 * np.arange(60)
    down = up[-1] - 0.3 * np.arange(60)
    prices = np.concatenate([up, down])
    return pd.Series(prices, index=dates, name="close")


def test_atr_calculator_initialization() -> None:
    cfg = StopLossConfig()
    calc = ATRCalculator(cfg)
    assert calc.config.atr_mode == "proxy_close_only"
    assert calc.config.atr_window == 20


def test_atr_computation_close_only(sample_prices: pd.Series) -> None:
    calc = ATRCalculator(StopLossConfig(atr_window=20))
    atr = calc.compute_atr(sample_prices)
    assert isinstance(atr, pd.Series)
    assert len(atr) == len(sample_prices)
    assert atr.iloc[:20].isna().all()
    assert atr.iloc[20:].notna().all()
    assert (atr.iloc[20:] >= 0.0).all()


def test_atr_at_specific_date(sample_prices: pd.Series) -> None:
    calc = ATRCalculator(StopLossConfig())
    date = sample_prices.index[40]
    value = calc.compute_atr_at_date(sample_prices, date)
    series_value = calc.compute_atr(sample_prices).loc[date]
    assert isinstance(value, float)
    assert np.isclose(value, float(series_value))


def test_atr_insufficient_history_raises(sample_prices: pd.Series) -> None:
    calc = ATRCalculator(StopLossConfig(atr_window=20))
    with pytest.raises(ValueError, match="insufficient history"):
        calc.compute_atr_at_date(sample_prices, sample_prices.index[10])


def test_stop_loss_manager_initialization() -> None:
    mgr = StopLossManager(StopLossConfig())
    assert mgr.positions == {}


def test_enter_position_sets_initial_stop(sample_prices: pd.Series) -> None:
    cfg = StopLossConfig()
    mgr = StopLossManager(cfg)
    entry_date = sample_prices.index[30]
    entry_price = float(sample_prices.loc[entry_date])
    pos = mgr.enter_position("TEST", entry_date, entry_price, sample_prices)
    assert "TEST" in mgr.positions
    expected = entry_price - (cfg.initial_stop_atr_multiple * pos.atr_at_entry)
    assert np.isclose(pos.current_stop, expected)
    assert pos.is_trailing is False


def test_d57_ratchet_constraint_enforced(sample_prices: pd.Series) -> None:
    mgr = StopLossManager(StopLossConfig())
    entry_date = sample_prices.index[30]
    entry_price = float(sample_prices.loc[entry_date])
    mgr.enter_position("TEST", entry_date, entry_price, sample_prices)

    stop_1, _ = mgr.update_stop(
        "TEST",
        current_date=sample_prices.index[40],
        current_price=float(sample_prices.loc[sample_prices.index[40]]),
        close_prices=sample_prices,
    )
    assert mgr.positions["TEST"].is_trailing is True

    stop_2, _ = mgr.update_stop(
        "TEST",
        current_date=sample_prices.index[85],
        current_price=float(sample_prices.loc[sample_prices.index[85]]),
        close_prices=sample_prices,
    )
    assert stop_2 >= stop_1

    stop_3, _ = mgr.update_stop(
        "TEST",
        current_date=sample_prices.index[100],
        current_price=float(sample_prices.loc[sample_prices.index[100]]),
        close_prices=sample_prices,
    )
    assert stop_3 >= stop_2


def test_trailing_stop_activates_only_after_profit(sample_prices: pd.Series) -> None:
    mgr = StopLossManager(StopLossConfig())
    entry_date = sample_prices.index[40]
    entry_price = float(sample_prices.loc[entry_date])
    mgr.enter_position("TEST", entry_date, entry_price, sample_prices)

    # Underwater update: trailing should remain disabled.
    mgr.update_stop(
        "TEST",
        current_date=sample_prices.index[41],
        current_price=float(entry_price - 1.0),
        close_prices=sample_prices,
    )
    assert mgr.positions["TEST"].is_trailing is False

    # Profitable update: trailing should activate.
    mgr.update_stop(
        "TEST",
        current_date=sample_prices.index[42],
        current_price=float(entry_price + 1.0),
        close_prices=sample_prices,
    )
    assert mgr.positions["TEST"].is_trailing is True


def test_time_based_exit_after_max_underwater_days() -> None:
    dates = pd.date_range("2020-01-01", periods=80, freq="D")
    prices = pd.Series(np.linspace(100.0, 60.0, len(dates)), index=dates, name="close")
    cfg = StopLossConfig(max_underwater_days=3)
    mgr = StopLossManager(cfg)

    entry_date = dates[25]
    entry_price = float(prices.loc[entry_date])
    mgr.enter_position("TEST", entry_date, entry_price, prices)

    should_exit = False
    for idx in [26, 27, 28, 29]:
        _, should_exit = mgr.update_stop(
            "TEST",
            current_date=dates[idx],
            current_price=float(prices.iloc[idx]),
            close_prices=prices,
        )
    assert should_exit is True


def test_stop_hit_detection(sample_prices: pd.Series) -> None:
    mgr = StopLossManager(StopLossConfig())
    entry_date = sample_prices.index[30]
    pos = mgr.enter_position("TEST", entry_date, float(sample_prices.loc[entry_date]), sample_prices)
    assert mgr.check_stop_hit("TEST", pos.current_stop + 1.0) is False
    assert mgr.check_stop_hit("TEST", pos.current_stop) is True
    assert mgr.check_stop_hit("TEST", pos.current_stop - 0.01) is True


def test_drawdown_monitor_tiers_activate_correctly() -> None:
    mon = PortfolioDrawdownMonitor(StopLossConfig())
    assert mon.update_equity(100_000.0) == (0, 1.0)
    assert mon.update_equity(92_000.0) == (1, 0.75)
    assert mon.update_equity(88_000.0) == (2, 0.50)
    assert mon.update_equity(85_000.0) == (3, 0.0)


def test_drawdown_recovery_resets_tier() -> None:
    mon = PortfolioDrawdownMonitor(StopLossConfig())
    mon.update_equity(100_000.0)
    tier_1, _ = mon.update_equity(90_000.0)
    assert tier_1 == 1
    tier_rec, scale_rec = mon.update_equity(97_000.0)
    assert tier_rec == 0
    assert scale_rec == 1.0


def test_factory_creates_both_components() -> None:
    mgr, mon = create_stop_loss_system()
    assert isinstance(mgr, StopLossManager)
    assert isinstance(mon, PortfolioDrawdownMonitor)
    assert mgr.config == mon.config


def test_full_lifecycle_stop_hit(sample_prices: pd.Series) -> None:
    mgr, _ = create_stop_loss_system()
    entry_date = sample_prices.index[30]
    mgr.enter_position("TEST", entry_date, float(sample_prices.loc[entry_date]), sample_prices)

    stop_1, should_exit_1 = mgr.update_stop(
        "TEST",
        current_date=sample_prices.index[40],
        current_price=float(sample_prices.loc[sample_prices.index[40]]),
        close_prices=sample_prices,
    )
    assert should_exit_1 is False

    _, should_exit_2 = mgr.update_stop(
        "TEST",
        current_date=sample_prices.index[100],
        current_price=float(stop_1 - 0.5),
        close_prices=sample_prices,
    )
    assert should_exit_2 is True
    mgr.remove_position("TEST")
    assert "TEST" not in mgr.positions


def test_multiple_positions_tracked_independently(sample_prices: pd.Series) -> None:
    mgr, _ = create_stop_loss_system()
    p1 = mgr.enter_position("AAPL", sample_prices.index[30], 150.0, sample_prices)
    p2 = mgr.enter_position("MSFT", sample_prices.index[35], 300.0, sample_prices)
    assert len(mgr.positions) == 2
    assert p1.current_stop != p2.current_stop


def test_atr_with_zero_volatility() -> None:
    dates = pd.date_range("2020-01-01", periods=50, freq="D")
    prices = pd.Series([100.0] * 50, index=dates)
    atr = ATRCalculator(StopLossConfig()).compute_atr(prices)
    assert (atr.iloc[20:] == 0.0).all()


def test_min_stop_distance_floor_for_zero_volatility() -> None:
    dates = pd.date_range("2020-01-01", periods=50, freq="D")
    prices = pd.Series([100.0] * 50, index=dates)
    cfg = StopLossConfig(min_stop_distance_abs=0.01)
    mgr = StopLossManager(cfg)
    pos = mgr.enter_position("TEST", dates[30], 100.0, prices)
    assert np.isclose(pos.current_stop, 99.99)


def test_remove_position_and_missing_position_stop_hit() -> None:
    mgr, _ = create_stop_loss_system()
    mgr.positions["TEST"] = PositionStop(
        ticker="TEST",
        entry_date=pd.Timestamp("2020-01-01"),
        entry_price=100.0,
        atr_at_entry=2.0,
        current_stop=96.0,
    )
    mgr.remove_position("TEST")
    assert mgr.check_stop_hit("TEST", 95.0) is False
