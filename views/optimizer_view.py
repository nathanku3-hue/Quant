"""Phase 6 portfolio optimizer view."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from strategies.optimizer import PortfolioOptimizer

DEFAULT_PORTFOLIO_VALUE = 10_000.0
MIN_REQUIRED_OBS = 3


def _resolve_permnos(
    prices_wide: pd.DataFrame,
    ticker_map: dict,
    selected_permnos=None,
    selected_tickers=None,
) -> list:
    """Resolve selected permnos/tickers against available columns."""
    available = list(prices_wide.columns)
    lookup = {}
    for permno in available:
        lookup[permno] = permno
        lookup[str(permno)] = permno
        if isinstance(permno, (int, np.integer)):
            lookup[str(int(permno))] = permno

    selected = []
    if selected_permnos is not None:
        for raw in selected_permnos:
            resolved = lookup.get(raw, lookup.get(str(raw)))
            if resolved is not None and resolved not in selected:
                selected.append(resolved)

    ticker_to_permno = {}
    for permno, ticker in (ticker_map or {}).items():
        if permno in available:
            ticker_to_permno[str(ticker).upper()] = permno

    if selected_tickers is not None:
        for ticker in selected_tickers:
            resolved = ticker_to_permno.get(str(ticker).upper())
            if resolved is not None and resolved not in selected:
                selected.append(resolved)

    return selected


def _ticker_label(permno, ticker_map: dict) -> str:
    ticker_lookup = ticker_map or {}
    ticker = ticker_lookup.get(permno)
    return f"{ticker} ({permno})" if ticker else str(permno)


def _build_allocation_table(
    prices_selected: pd.DataFrame,
    weights: pd.Series,
    ticker_map: dict,
    sector_map: dict | None,
    portfolio_value: float,
) -> pd.DataFrame:
    """Build a table with weights, dollars, and estimated shares."""
    latest_prices = prices_selected.ffill().iloc[-1].replace([np.inf, -np.inf], np.nan)
    weights = weights.reindex(prices_selected.columns).fillna(0.0)

    alloc_value = weights * float(portfolio_value)
    px = latest_prices.reindex(weights.index)
    shares = np.where((px > 0) & px.notna(), alloc_value / px, np.nan)

    ticker_lookup = ticker_map or {}
    table = pd.DataFrame(
        {
            "permno": weights.index,
            "ticker": [ticker_lookup.get(p, str(p)) for p in weights.index],
            "sector": [str((sector_map or {}).get(p, "Unknown")) for p in weights.index],
            "weight": weights.values,
            "allocation_usd": alloc_value.values,
            "latest_price": px.values,
            "est_shares": shares,
        }
    )
    table = table.replace([np.inf, -np.inf], np.nan)
    table = table[table["weight"] > 0].sort_values("weight", ascending=False)
    return table


def render_optimizer_view(
    prices_wide: pd.DataFrame,
    ticker_map: dict,
    sector_map: dict | None = None,
    selected_permnos=None,
    selected_tickers=None,
):
    """Render portfolio optimization controls and allocations."""
    st.header("📦 Portfolio Optimizer")

    if not isinstance(prices_wide, pd.DataFrame) or prices_wide.empty:
        st.warning("No price data available for optimization.")
        return

    default_selection = _resolve_permnos(
        prices_wide=prices_wide,
        ticker_map=ticker_map,
        selected_permnos=selected_permnos,
        selected_tickers=selected_tickers,
    )
    if not default_selection:
        default_selection = list(prices_wide.columns[: min(10, prices_wide.shape[1])])

    selected_assets = st.multiselect(
        "Select assets",
        options=list(prices_wide.columns),
        default=default_selection,
        format_func=lambda p: _ticker_label(p, ticker_map),
    )
    if not selected_assets:
        st.info("Select at least one asset to run optimization.")
        return

    prices_selected = prices_wide.reindex(columns=selected_assets)
    prices_selected = prices_selected.apply(pd.to_numeric, errors="coerce")
    prices_selected = prices_selected.replace([np.inf, -np.inf], np.nan)
    prices_selected = prices_selected.dropna(how="all")
    prices_selected = prices_selected.dropna(axis=1, how="all")

    if prices_selected.empty or prices_selected.shape[1] == 0:
        st.warning("Selected assets have no usable price data.")
        return

    sufficient_cols = prices_selected.columns[prices_selected.notna().sum() >= MIN_REQUIRED_OBS]
    dropped_cols = [c for c in prices_selected.columns if c not in sufficient_cols]
    if dropped_cols:
        dropped_names = ", ".join([_ticker_label(c, ticker_map) for c in dropped_cols])
        st.caption(f"Skipped assets with insufficient history: {dropped_names}")

    prices_selected = prices_selected.reindex(columns=sufficient_cols)
    if prices_selected.shape[1] == 0:
        st.warning("Not enough history to optimize the selected assets.")
        return

    ctl1, ctl2, ctl3 = st.columns([1.5, 1, 1])
    with ctl1:
        method = st.selectbox(
            "Method",
            [
                "Inverse Volatility",
                "Mean-Variance (Max Sharpe)",
                "Mean-Variance (Min Volatility)",
                "Mean-Variance (Max Return)",
            ],
            index=0,
        )
    with ctl2:
        max_weight = st.slider("Max weight", min_value=0.05, max_value=1.0, value=0.2, step=0.05)
    with ctl3:
        portfolio_value = st.number_input(
            "Portfolio value ($)",
            min_value=1_000.0,
            value=float(DEFAULT_PORTFOLIO_VALUE),
            step=500.0,
        )

    cap_col1, cap_col2 = st.columns([1.2, 1.2])
    with cap_col1:
        enable_sector_cap = st.checkbox("Enable Sector Constraint", value=False)
    with cap_col2:
        max_sector_weight = st.slider(
            "Max sector weight",
            min_value=0.10,
            max_value=1.0,
            value=0.30,
            step=0.05,
            disabled=not enable_sector_cap,
        )

    risk_free_rate = 0.0
    if method.startswith("Mean-Variance"):
        risk_free_rate = st.number_input(
            "Risk-free rate (annual)",
            min_value=-0.1,
            max_value=0.2,
            value=0.0,
            step=0.005,
            format="%.3f",
        )

    min_feasible = 1.0 / prices_selected.shape[1]
    effective_max_weight = float(max_weight)
    if effective_max_weight < min_feasible:
        effective_max_weight = min_feasible
        st.caption(
            f"Adjusted max weight to {effective_max_weight:.2f} for feasibility "
            f"({prices_selected.shape[1]} assets)."
        )

    optimizer = PortfolioOptimizer()
    if method.startswith("Mean-Variance"):
        if optimizer.has_slsqp():
            st.caption("Optimization Method: Mean-Variance (SLSQP)")
        else:
            st.warning("Optimization Method: Fallback (Equal Weight) — SciPy unavailable")

    if method == "Inverse Volatility":
        weights = optimizer.optimize_inverse_volatility(
            prices_selected,
            max_weight=effective_max_weight,
        )
    elif method == "Mean-Variance (Min Volatility)":
        weights = optimizer.optimize_mean_variance(
            prices_selected,
            objective="min_volatility",
            max_weight=effective_max_weight,
            risk_free_rate=risk_free_rate,
        )
    elif method == "Mean-Variance (Max Return)":
        weights = optimizer.optimize_mean_variance(
            prices_selected,
            objective="max_return",
            max_weight=effective_max_weight,
            risk_free_rate=risk_free_rate,
        )
    else:
        weights = optimizer.optimize_mean_variance(
            prices_selected,
            objective="max_sharpe",
            max_weight=effective_max_weight,
            risk_free_rate=risk_free_rate,
        )

    if not isinstance(weights, pd.Series) or weights.empty:
        st.warning("Unable to compute weights with current inputs.")
        return

    weights = weights.reindex(prices_selected.columns).fillna(0.0)
    if float(weights.sum()) <= 0:
        st.warning("No positive allocation produced by optimizer.")
        return
    weights = weights / float(weights.sum())

    if enable_sector_cap:
        if isinstance(sector_map, dict) and len(sector_map) > 0:
            selected_sector_map = {p: sector_map.get(p, "Unknown") for p in weights.index}
            weights = optimizer.apply_sector_cap(
                weights=weights,
                sector_map=selected_sector_map,
                max_sector_weight=float(max_sector_weight),
            )
            st.caption(f"Sector cap applied: max {float(max_sector_weight):.0%} per sector.")
        else:
            st.warning("Sector map unavailable; skipped sector constraint.")

    allocation_df = _build_allocation_table(
        prices_selected=prices_selected,
        weights=weights,
        ticker_map=ticker_map,
        sector_map=sector_map,
        portfolio_value=float(portfolio_value),
    )
    if allocation_df.empty:
        st.warning("Optimization produced no investable allocation.")
        return

    sector_exposure = (
        allocation_df.groupby("sector", dropna=False)["weight"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"weight": "sector_weight"})
    )
    if enable_sector_cap and not sector_exposure.empty:
        realized_max = float(sector_exposure["sector_weight"].max())
        if realized_max > float(max_sector_weight) + 1e-6:
            st.warning(
                f"Sector cap target {float(max_sector_weight):.0%} is infeasible with current selection "
                f"(realized max {realized_max:.0%})."
            )

    chart_col, table_col = st.columns([1.2, 1.4])
    with chart_col:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=allocation_df["ticker"],
                    values=allocation_df["weight"],
                    hole=0.35,
                    sort=False,
                    textinfo="label+percent",
                    hovertemplate="%{label}<br>Weight: %{value:.2%}<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            title=f"Allocation ({method})",
            margin=dict(l=20, r=20, t=50, b=20),
            height=420,
        )
        st.plotly_chart(fig, width="stretch")

        st.subheader("Sector Exposure")
        st.dataframe(
            sector_exposure.rename(
                columns={
                    "sector": "Sector",
                    "sector_weight": "Weight",
                }
            ).style.format({"Weight": "{:.2%}"}),
            width="stretch",
            height=240,
        )

    with table_col:
        st.subheader("Allocation Table")
        st.dataframe(
            allocation_df.rename(
                columns={
                    "permno": "Permno",
                    "ticker": "Ticker",
                    "sector": "Sector",
                    "weight": "Weight",
                    "allocation_usd": "Allocation ($)",
                    "latest_price": "Latest Price ($)",
                    "est_shares": "Estimated Shares",
                }
            ).style.format(
                {
                    "Weight": "{:.2%}",
                    "Allocation ($)": "${:,.2f}",
                    "Latest Price ($)": "${:,.2f}",
                    "Estimated Shares": "{:,.2f}",
                }
            ),
            width="stretch",
            height=420,
        )
