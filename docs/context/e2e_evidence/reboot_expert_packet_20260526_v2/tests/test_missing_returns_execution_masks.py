from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_phase20_simulate_missing_entry_bar_is_not_counted():
    mod = _load_module(ROOT / "scripts" / "phase20_full_backtest.py", "phase20_full_backtest_missing_returns")
    d1 = pd.Timestamp("2024-01-02")
    d2 = pd.Timestamp("2024-01-03")
    weights = pd.DataFrame({101: [1.0, 1.0]}, index=pd.DatetimeIndex([d1, d2]))
    returns_wide = pd.DataFrame({101: [0.01]}, index=pd.DatetimeIndex([d2]))

    sim, missing = mod._simulate(
        weights=weights,
        returns_wide=returns_wide,
        cost_bps=0.0,
        allow_missing_returns=False,
    )
    assert len(sim) == 2
    assert int(missing) == 0


def test_phase20_simulate_missing_exit_bar_raises_in_strict_mode():
    mod = _load_module(ROOT / "scripts" / "phase20_full_backtest.py", "phase20_full_backtest_missing_returns_exit")
    d1 = pd.Timestamp("2024-01-02")
    d2 = pd.Timestamp("2024-01-03")
    weights = pd.DataFrame({101: [1.0, 0.0]}, index=pd.DatetimeIndex([d1, d2]))
    returns_wide = pd.DataFrame({101: [0.01]}, index=pd.DatetimeIndex([d1]))

    with pytest.raises(RuntimeError, match="executed-exposure return cells"):
        mod._simulate(
            weights=weights,
            returns_wide=returns_wide,
            cost_bps=0.0,
            allow_missing_returns=False,
        )


def test_phase20_simulate_allow_missing_returns_proceeds_with_missing_count():
    mod = _load_module(ROOT / "scripts" / "phase20_full_backtest.py", "phase20_full_backtest_missing_returns_permissive")
    d1 = pd.Timestamp("2024-01-02")
    d2 = pd.Timestamp("2024-01-03")
    weights = pd.DataFrame({101: [1.0, 0.0]}, index=pd.DatetimeIndex([d1, d2]))
    returns_wide = pd.DataFrame({101: [0.01]}, index=pd.DatetimeIndex([d1]))

    sim, missing = mod._simulate(
        weights=weights,
        returns_wide=returns_wide,
        cost_bps=0.0,
        allow_missing_returns=True,
    )
    assert len(sim) == 2
    assert int(missing) == 1


def test_regime_fidelity_missing_exit_bar_raises_in_strict_mode():
    mod = _load_module(ROOT / "scripts" / "regime_fidelity_sprint.py", "regime_fidelity_sprint_missing_returns")
    d1 = pd.Timestamp("2024-01-02")
    d2 = pd.Timestamp("2024-01-03")
    target = pd.DataFrame({101: [1.0, 0.0]}, index=pd.DatetimeIndex([d1, d2]))
    returns_long = pd.DataFrame({"date": [d1], "permno": [101], "ret": [0.01]})

    with pytest.raises(RuntimeError, match="executed-exposure return cells"):
        mod._simulate_from_target_weights(
            target_weights=target,
            returns_long=returns_long,
            cost_bps=0.0,
            allow_missing_returns=False,
            max_matrix_cells=1_000,
        )


def test_regime_fidelity_allow_missing_returns_proceeds_with_missing_count():
    mod = _load_module(ROOT / "scripts" / "regime_fidelity_sprint.py", "regime_fidelity_sprint_missing_returns_permissive")
    d1 = pd.Timestamp("2024-01-02")
    d2 = pd.Timestamp("2024-01-03")
    target = pd.DataFrame({101: [1.0, 0.0]}, index=pd.DatetimeIndex([d1, d2]))
    returns_long = pd.DataFrame({"date": [d1], "permno": [101], "ret": [0.01]})

    sim, missing = mod._simulate_from_target_weights(
        target_weights=target,
        returns_long=returns_long,
        cost_bps=0.0,
        allow_missing_returns=True,
        max_matrix_cells=1_000,
    )
    assert len(sim) == 2
    assert int(missing) == 1


def test_regime_fidelity_missing_entry_bar_is_not_counted():
    mod = _load_module(ROOT / "scripts" / "regime_fidelity_sprint.py", "regime_fidelity_sprint_missing_returns_entry")
    d1 = pd.Timestamp("2024-01-02")
    d2 = pd.Timestamp("2024-01-03")
    target = pd.DataFrame({101: [1.0, 1.0]}, index=pd.DatetimeIndex([d1, d2]))
    returns_long = pd.DataFrame({"date": [d2], "permno": [101], "ret": [0.01]})

    sim, missing = mod._simulate_from_target_weights(
        target_weights=target,
        returns_long=returns_long,
        cost_bps=0.0,
        allow_missing_returns=False,
        max_matrix_cells=1_000,
    )
    assert len(sim) == 2
    assert int(missing) == 0


def test_phase21_stop_impact_missing_exit_bar_raises_in_strict_mode():
    mod = _load_module(ROOT / "scripts" / "phase21_day1_stop_impact.py", "phase21_day1_stop_missing_returns")
    d1 = pd.Timestamp("2024-01-02")
    d2 = pd.Timestamp("2024-01-03")
    target = pd.DataFrame({101: [1.0, 0.0]}, index=pd.DatetimeIndex([d1, d2]))
    returns_long = pd.DataFrame({"date": [d1], "permno": [101], "ret": [0.01]})

    with pytest.raises(RuntimeError, match="executed-exposure return cells"):
        mod._simulate_from_target_weights(
            target_weights=target,
            returns_long=returns_long,
            cost_bps=0.0,
            allow_missing_returns=False,
            max_matrix_cells=1_000,
        )


def test_phase21_stop_impact_missing_entry_bar_is_not_counted():
    mod = _load_module(ROOT / "scripts" / "phase21_day1_stop_impact.py", "phase21_day1_stop_missing_returns_entry")
    d1 = pd.Timestamp("2024-01-02")
    d2 = pd.Timestamp("2024-01-03")
    target = pd.DataFrame({101: [1.0, 1.0]}, index=pd.DatetimeIndex([d1, d2]))
    returns_long = pd.DataFrame({"date": [d2], "permno": [101], "ret": [0.01]})

    sim, missing = mod._simulate_from_target_weights(
        target_weights=target,
        returns_long=returns_long,
        cost_bps=0.0,
        allow_missing_returns=False,
        max_matrix_cells=1_000,
    )
    assert len(sim) == 2
    assert int(missing) == 0


def test_phase21_stop_impact_allow_missing_returns_proceeds_with_missing_count():
    mod = _load_module(ROOT / "scripts" / "phase21_day1_stop_impact.py", "phase21_day1_stop_missing_returns_permissive")
    d1 = pd.Timestamp("2024-01-02")
    d2 = pd.Timestamp("2024-01-03")
    target = pd.DataFrame({101: [1.0, 0.0]}, index=pd.DatetimeIndex([d1, d2]))
    returns_long = pd.DataFrame({"date": [d1], "permno": [101], "ret": [0.01]})

    sim, missing = mod._simulate_from_target_weights(
        target_weights=target,
        returns_long=returns_long,
        cost_bps=0.0,
        allow_missing_returns=True,
        max_matrix_cells=1_000,
    )
    assert len(sim) == 2
    assert int(missing) == 1
