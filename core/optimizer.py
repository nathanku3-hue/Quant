"""
Terminal Zero — Parameter Optimizer (Phase 4)

Automated Grid Search over (k, z) parameter space.
Finds the "Golden Parameters" that maximize Return per unit of Pain.

Metric: Ulcer Performance Index (UPI) = CAGR / Ulcer Index
  - Ulcer Index = sqrt(mean(drawdown^2)) — captures depth AND duration.
  - Higher UPI = more return for less suffering.
"""

import numpy as np
import pandas as pd
from . import engine
from strategies.investor_cockpit import InvestorCockpitStrategy


def run_parameter_sweep(
    prices_wide: pd.DataFrame,
    returns_wide: pd.DataFrame,
    macro: pd.DataFrame,
    k_range: np.ndarray = np.arange(2.0, 5.0, 0.5),
    z_range: np.ndarray = np.arange(-1.5, -4.5, -0.5),
    cost_bps: float = 0.001,
) -> pd.DataFrame:
    """
    Grid Search for Optimal (k, z).

    Args:
        prices_wide:  Wide DataFrame of adj_close (Index=Date, Cols=Permno)
        returns_wide: Wide DataFrame of total_ret (Index=Date, Cols=Permno)
        macro:        DataFrame with spy_close, vix_proxy
        k_range:      Array of k (stop multiplier) values to test
        z_range:      Array of z (entry threshold) values to test
        cost_bps:     Transaction cost in basis points

    Returns:
        DataFrame with columns: k, z, total_return, cagr, max_dd, sharpe,
                                ulcer_index, upi
    """
    results = []
    total_combos = len(k_range) * len(z_range)
    combo_idx = 0

    for k in k_range:
        for z in z_range:
            combo_idx += 1
            print(f"  [{combo_idx}/{total_combos}] k={k:.1f}, z={z:.1f} ...", end="")

            try:
                # Instantiate strategy with these specific parameters
                strat = InvestorCockpitStrategy(k_stop=float(k), z_entry=float(z))

                # Generate weights
                weights, _, _ = strat.generate_weights(prices_wide, None, macro)

                # Run simulation through the Engine
                sim = engine.run_simulation(weights, returns_wide, cost_bps=cost_bps)

                # ── Calculate Metrics ───────────────────────────────────────
                net_curve = (1 + sim["net_ret"]).cumprod()
                total_ret = net_curve.iloc[-1] - 1

                # CAGR
                n_years = len(net_curve) / 252
                cagr = (net_curve.iloc[-1] ** (1 / n_years) - 1) if n_years > 0 else 0.0

                # Drawdown
                peak = net_curve.cummax()
                dd = (net_curve - peak) / peak
                max_dd = dd.min()

                # Ulcer Index (quadratic mean of drawdowns)
                ulcer_index = np.sqrt((dd ** 2).mean())

                # Sharpe Ratio
                daily_ret = sim["net_ret"]
                sharpe = (
                    daily_ret.mean() / daily_ret.std() * np.sqrt(252)
                    if daily_ret.std() > 0
                    else 0.0
                )

                # Ulcer Performance Index (UPI)
                upi = cagr / (ulcer_index + 1e-6)

                # Avg Daily Turnover
                avg_turnover = sim["turnover"].mean()

                results.append(
                    {
                        "k": round(float(k), 2),
                        "z": round(float(z), 2),
                        "total_return": round(total_ret, 4),
                        "cagr": round(cagr, 4),
                        "max_dd": round(max_dd, 4),
                        "sharpe": round(sharpe, 4),
                        "ulcer_index": round(ulcer_index, 4),
                        "upi": round(upi, 4),
                        "avg_turnover": round(avg_turnover, 4),
                    }
                )
                print(f" CAGR={cagr:.2%}, DD={max_dd:.1%}, UPI={upi:.2f}")

            except Exception as e:
                print(f" ERROR: {e}")
                results.append(
                    {
                        "k": round(float(k), 2),
                        "z": round(float(z), 2),
                        "total_return": np.nan,
                        "cagr": np.nan,
                        "max_dd": np.nan,
                        "sharpe": np.nan,
                        "ulcer_index": np.nan,
                        "upi": np.nan,
                        "avg_turnover": np.nan,
                    }
                )

    return pd.DataFrame(results)


def run_adaptive_benchmark(
    prices_wide: pd.DataFrame,
    returns_wide: pd.DataFrame,
    macro: pd.DataFrame,
    cost_bps: float = 0.001,
) -> dict:
    """
    Run a single simulation using Dynamic Volatility Mapping (Adaptive mode).
    Returns the same metrics as the grid search for direct comparison.
    """
    print("  [ADAPTIVE] Running Dynamic Volatility Mapping benchmark...")

    strat = InvestorCockpitStrategy(use_dynamic_params=True, green_candle=True)
    weights, _, _ = strat.generate_weights(prices_wide, None, macro)
    sim = engine.run_simulation(weights, returns_wide, cost_bps=cost_bps)

    net_curve = (1 + sim["net_ret"]).cumprod()
    total_ret = net_curve.iloc[-1] - 1
    n_years = len(net_curve) / 252
    cagr = (net_curve.iloc[-1] ** (1 / n_years) - 1) if n_years > 0 else 0.0

    peak = net_curve.cummax()
    dd = (net_curve - peak) / peak
    max_dd = dd.min()
    ulcer_index = np.sqrt((dd ** 2).mean())

    daily_ret = sim["net_ret"]
    sharpe = daily_ret.mean() / daily_ret.std() * np.sqrt(252) if daily_ret.std() > 0 else 0.0
    upi = cagr / (ulcer_index + 1e-6)
    avg_turnover = sim["turnover"].mean()

    result = {
        "k": "adaptive",
        "z": "adaptive",
        "total_return": round(total_ret, 4),
        "cagr": round(cagr, 4),
        "max_dd": round(max_dd, 4),
        "sharpe": round(sharpe, 4),
        "ulcer_index": round(ulcer_index, 4),
        "upi": round(upi, 4),
        "avg_turnover": round(avg_turnover, 4),
    }
    print(f"  [ADAPTIVE] CAGR={cagr:.2%}, DD={max_dd:.1%}, UPI={upi:.2f}")
    return result

