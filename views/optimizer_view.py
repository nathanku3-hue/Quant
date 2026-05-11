"""Phase 6 portfolio optimizer view."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data_orchestrator import load_strategy_metrics_from_results
from core.data_orchestrator import refresh_selected_prices_with_live_overlay
from strategies.optimizer import (
    DEFAULT_OPTIMIZATION_METHOD,
    OPTIMIZATION_METHOD_OPTIONS,
    OptimizationMethod,
    PortfolioOptimizer,
)
from strategies.portfolio_universe import OptimizerUniverseResult, diagnose_max_weight_feasibility

DEFAULT_PORTFOLIO_VALUE = 10_000.0
DEFAULT_MAX_WEIGHT = 0.35
MIN_REQUIRED_OBS = 3


@dataclass(frozen=True)
class OptimizerControls:
    method: OptimizationMethod
    max_weight: float
    portfolio_value: float
    enable_sector_cap: bool
    max_sector_weight: float
    risk_free_rate: float


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
    """Build a complete allocation table with weights, dollars, shares, and cash."""
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
    table["permno"] = table["permno"].astype(str)
    if table.empty:
        return table

    cash_weight = 1.0 - float(weights.sum())
    cash_allocation = float(portfolio_value) * cash_weight
    cash_row = pd.DataFrame(
        [
            {
                "permno": "CASH",
                "ticker": "CASH",
                "sector": "Cash",
                "weight": float(cash_weight),
                "allocation_usd": float(cash_allocation),
                "latest_price": np.nan,
                "est_shares": np.nan,
            }
        ]
    )
    return pd.concat([table, cash_row], ignore_index=True)


def _universe_audit_frame(universe_audit: OptimizerUniverseResult | None) -> pd.DataFrame:
    if universe_audit is None:
        return pd.DataFrame()
    frame = universe_audit.to_frame()
    return frame if isinstance(frame, pd.DataFrame) else pd.DataFrame()


def _universe_count(universe_audit: OptimizerUniverseResult | None, attr: str) -> int:
    value = getattr(universe_audit, attr, None)
    if value is None:
        return 0
    try:
        return len(value)
    except TypeError:
        return 0


def _candidate_options_from_audit(
    universe_audit: OptimizerUniverseResult | None,
    prices_wide: pd.DataFrame,
) -> list | None:
    if universe_audit is None:
        return None
    permnos = list(universe_audit.included_permnos)
    available = set(prices_wide.columns) if isinstance(prices_wide, pd.DataFrame) else set()
    return [permno for permno in permnos if permno in available]


def _render_universe_audit(universe_audit: OptimizerUniverseResult | None) -> None:
    audit_df = _universe_audit_frame(universe_audit)
    if audit_df.empty:
        return

    st.subheader("Universe Audit")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Included", _universe_count(universe_audit, "included"))
    with c2:
        st.metric("Excluded", _universe_count(universe_audit, "excluded"))
    with c3:
        st.metric("Missing Map", _universe_count(universe_audit, "missing_mappings"))
    with c4:
        st.metric("History Fail", _universe_count(universe_audit, "insufficient_history"))

    display = audit_df.rename(
        columns={
            "ticker": "Ticker",
            "permno": "Permno",
            "rating": "Rating",
            "action": "Action",
            "status": "Status",
            "reason": "Reason",
            "history_obs": "History Obs",
        }
    )
    preferred_cols = ["Ticker", "Permno", "Status", "Reason", "Rating", "Action", "History Obs"]
    display_cols = [col for col in preferred_cols if col in display.columns]
    st.dataframe(display[display_cols], width="stretch", height=260)


def _render_allocation_explanation(
    method: OptimizationMethod,
    feasibility: dict[str, object],
    universe_audit: OptimizerUniverseResult | None,
    enable_sector_cap: bool,
    max_sector_weight: float,
    fallback_used: bool,
) -> None:
    st.subheader("Why This Allocation?")
    rows = [
        {"Item": "Universe source", "Status": "Explicit optimizer universe builder"},
        {"Item": "Thesis mode", "Status": "Thesis-neutral; no MU hard floor or conviction tilt"},
        {"Item": "Optimizer method", "Status": method.value},
        {"Item": "Eligible assets", "Status": str(_universe_count(universe_audit, "included"))},
        {"Item": "Excluded by policy", "Status": str(_universe_count(universe_audit, "excluded"))},
        {"Item": "Missing ticker mappings", "Status": str(_universe_count(universe_audit, "missing_mappings"))},
        {"Item": "Price-history failures", "Status": str(_universe_count(universe_audit, "insufficient_history"))},
        {"Item": "Max-weight diagnostic", "Status": str(feasibility.get("message", ""))},
        {
            "Item": "Sector constraint",
            "Status": f"Enabled at {float(max_sector_weight):.0%}" if enable_sector_cap else "Disabled",
        },
        {"Item": "Fallback status", "Status": "Equal-weight fallback" if fallback_used else "Optimizer produced weights"},
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True, height=360)


def _render_optimizer_diagnostics(diagnostics) -> None:
    """Render UI-safe optimizer diagnostics without changing policy controls."""
    if diagnostics is None:
        return

    feasibility = diagnostics.feasibility_report
    bounds = diagnostics.bound_diagnostics
    constraints = diagnostics.constraint_diagnostics

    if not feasibility.is_feasible:
        st.error("Optimization status: infeasible.")
    elif diagnostics.fallback_used:
        reason = diagnostics.fallback_reason or diagnostics.solver_message or "optimizer did not produce usable weights"
        st.warning(
            "Fallback allocation used: equal weight. "
            f"Reason: {reason}. This is not an optimized result."
        )
    elif feasibility.is_equal_weight_forced:
        st.warning(
            "The optimizer has effectively no allocation freedom. "
            "The max-weight cap is at the minimum feasible boundary, so the result is forced toward equal weight."
        )
    elif diagnostics.result_is_optimized:
        st.success("Optimization status: optimized result.")
    else:
        st.warning("Optimization status: not optimized.")

    active_constraints = ", ".join(diagnostics.active_constraints) or "None"
    max_cap_assets = ", ".join(bounds.assets_at_upper_bound) or "None"
    lower_bound_assets = ", ".join(bounds.assets_at_lower_bound) or "None"
    feasibility_messages = " | ".join(feasibility.messages)

    rows = [
        {"Item": "Optimization status", "Status": "Optimized" if diagnostics.result_is_optimized else "Not optimized"},
        {"Item": "Feasibility status", "Status": feasibility.status},
        {"Item": "Active constraints", "Status": active_constraints},
        {"Item": "Assets at max cap", "Status": f"{bounds.upper_bound_count}: {max_cap_assets}"},
        {"Item": "Assets at lower bound", "Status": f"{bounds.lower_bound_count}: {lower_bound_assets}"},
        {"Item": "Equal weight forced", "Status": "Yes" if feasibility.is_equal_weight_forced else "No"},
        {"Item": "Result type", "Status": "Fallback" if diagnostics.fallback_used else "Optimizer"},
        {"Item": "Solver success", "Status": str(bool(diagnostics.solver_success))},
        {"Item": "Solver status", "Status": str(diagnostics.solver_status)},
        {"Item": "Solver message", "Status": diagnostics.solver_message or "None"},
        {"Item": "Objective", "Status": diagnostics.objective_name},
        {"Item": "Bounds", "Status": diagnostics.bounds_summary},
        {"Item": "Constraints", "Status": diagnostics.constraints_summary},
        {"Item": "Cash residual", "Status": f"{constraints.cash_residual:.6f}"},
        {"Item": "Constraint residual", "Status": f"{constraints.constraint_residuals.get('fully_invested', 0.0):.6f}"},
        {"Item": "Feasibility message", "Status": feasibility_messages},
    ]
    st.subheader("Optimizer Diagnostics")
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True, height=420)


def _render_asset_selector(
    prices_wide: pd.DataFrame,
    ticker_map: dict,
    selected_permnos,
    selected_tickers,
    universe_audit: OptimizerUniverseResult | None,
) -> list | None:
    _render_universe_audit(universe_audit)
    candidate_options = _candidate_options_from_audit(universe_audit, prices_wide)
    if candidate_options is not None and not candidate_options:
        _clear_optimizer_session_weights()
        st.info("No optimizer-eligible assets under the current portfolio universe policy.")
        return None

    asset_options = candidate_options if candidate_options is not None else list(prices_wide.columns)
    default_selection = _resolve_permnos(
        prices_wide=prices_wide,
        ticker_map=ticker_map,
        selected_permnos=selected_permnos,
        selected_tickers=selected_tickers,
    )
    if candidate_options is not None:
        default_selection = [permno for permno in default_selection if permno in candidate_options]
    explicit_default = selected_permnos is not None or selected_tickers is not None or universe_audit is not None
    if not default_selection and not explicit_default:
        default_selection = list(prices_wide.columns[: min(10, prices_wide.shape[1])])

    selected_assets = st.multiselect(
        "Select assets",
        options=asset_options,
        default=default_selection,
        format_func=lambda p: _ticker_label(p, ticker_map),
    )
    if not selected_assets:
        _clear_optimizer_session_weights()
        st.info("Select at least one asset to run optimization.")
        return None
    return list(selected_assets)


def _prepare_selected_prices(
    prices_wide: pd.DataFrame,
    selected_assets: list,
    ticker_map: dict,
) -> tuple[pd.DataFrame, pd.Timestamp | None, str] | None:
    prices_selected = prices_wide.reindex(columns=selected_assets)
    prices_selected, latest_price_date, refresh_source = refresh_selected_prices_with_live_overlay(
        prices_selected=prices_selected,
        ticker_map=ticker_map,
    )
    prices_selected = prices_selected.dropna(axis=1, how="all")

    if prices_selected.empty or prices_selected.shape[1] == 0:
        _clear_optimizer_session_weights()
        st.warning("Selected assets have no usable price data.")
        return None

    if latest_price_date is not None:
        source_label = "live refresh" if refresh_source == "live" else "local TRI"
        st.caption(f"Price data through {latest_price_date.date()} ({source_label}).")

    sufficient_cols = prices_selected.columns[prices_selected.notna().sum() >= MIN_REQUIRED_OBS]
    dropped_cols = [c for c in prices_selected.columns if c not in sufficient_cols]
    if dropped_cols:
        dropped_names = ", ".join([_ticker_label(c, ticker_map) for c in dropped_cols])
        st.caption(f"Skipped assets with insufficient history: {dropped_names}")

    prices_selected = prices_selected.reindex(columns=sufficient_cols)
    if prices_selected.shape[1] == 0:
        _clear_optimizer_session_weights()
        st.warning("Not enough history to optimize the selected assets.")
        return None
    return prices_selected, latest_price_date, refresh_source


def _resolve_historical_method(method: OptimizationMethod) -> OptimizationMethod:
    if method == OptimizationMethod.HISTORICAL_BEST_CAGR:
        metrics = load_strategy_metrics_from_results()
        if not metrics:
            st.warning(f"No backtest results found. Using {OptimizationMethod.INVERSE_VOLATILITY.value}.")
            return OptimizationMethod.INVERSE_VOLATILITY

        name, data = max(metrics.items(), key=lambda x: x[1]["cagr"])
        st.info(
            f"Using: {name} "
            f"(CAGR: {data['cagr']*100:.1f}%, "
            f"Sharpe: {data['sharpe']:.2f}, "
            f"updated: {data['timestamp'][:10]})"
        )
        return OptimizationMethod.INVERSE_VOLATILITY

    if method == OptimizationMethod.HISTORICAL_MAX_SHARPE:
        metrics = load_strategy_metrics_from_results()
        if not metrics:
            st.warning(f"No backtest results found. Using {OptimizationMethod.THESIS_NEUTRAL_MAX_SHARPE.value}.")
            return OptimizationMethod.THESIS_NEUTRAL_MAX_SHARPE

        name, data = max(metrics.items(), key=lambda x: x[1]["sharpe"])
        st.info(
            f"Using: {name} "
            f"(Sharpe: {data['sharpe']:.2f}, "
            f"CAGR: {data['cagr']*100:.1f}%, "
            f"updated: {data['timestamp'][:10]})"
        )
        return OptimizationMethod.THESIS_NEUTRAL_MAX_SHARPE

    return method


def _render_optimizer_controls() -> OptimizerControls:
    ctl1, ctl2, ctl3 = st.columns([1.5, 1, 1])
    with ctl1:
        selected_method = st.selectbox(
            "Method",
            list(OPTIMIZATION_METHOD_OPTIONS),
            index=list(OPTIMIZATION_METHOD_OPTIONS).index(DEFAULT_OPTIMIZATION_METHOD),
            format_func=lambda method: method.value,
        )
    method = _resolve_historical_method(OptimizationMethod(selected_method))

    with ctl2:
        max_weight = st.slider(
            "Max weight",
            min_value=0.05,
            max_value=1.0,
            value=DEFAULT_MAX_WEIGHT,
            step=0.01,
            help="Default is 35%; 33% is the intended operating target.",
        )
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
    if method.is_mean_variance:
        risk_free_rate = st.number_input(
            "Risk-free rate (annual)",
            min_value=-0.1,
            max_value=0.2,
            value=0.0,
            step=0.005,
            format="%.3f",
        )

    return OptimizerControls(
        method=method,
        max_weight=float(max_weight),
        portfolio_value=float(portfolio_value),
        enable_sector_cap=bool(enable_sector_cap),
        max_sector_weight=float(max_sector_weight),
        risk_free_rate=float(risk_free_rate),
    )


def _render_optimizer_method_status(optimizer: PortfolioOptimizer, method: OptimizationMethod) -> None:
    if not method.is_mean_variance:
        return
    if optimizer.has_slsqp():
        st.caption("Optimization Method: Mean-Variance (SLSQP)")
    else:
        st.warning("Optimization Method: Fallback (Equal Weight) — SciPy unavailable")


def _clear_optimizer_session_weights() -> None:
    st.session_state["optimizer_weights"] = {}
    st.session_state["optimizer_price_latest_date"] = ""


def _run_optimizer(
    optimizer: PortfolioOptimizer,
    method: OptimizationMethod,
    prices_selected: pd.DataFrame,
    max_weight: float,
    risk_free_rate: float,
):
    if method == OptimizationMethod.INVERSE_VOLATILITY:
        return optimizer.optimize_inverse_volatility_with_diagnostics(
            prices_selected,
            max_weight=max_weight,
        )
    if method == OptimizationMethod.MEAN_VARIANCE_MIN_VOLATILITY:
        return optimizer.optimize_mean_variance_with_diagnostics(
            prices_selected,
            objective="min_volatility",
            max_weight=max_weight,
            risk_free_rate=risk_free_rate,
        )
    if method == OptimizationMethod.MEAN_VARIANCE_MAX_RETURN:
        return optimizer.optimize_mean_variance_with_diagnostics(
            prices_selected,
            objective="max_return",
            max_weight=max_weight,
            risk_free_rate=risk_free_rate,
        )
    return optimizer.optimize_mean_variance_with_diagnostics(
        prices_selected,
        objective="max_sharpe",
        max_weight=max_weight,
        risk_free_rate=risk_free_rate,
    )


@st.cache_data(ttl=300, show_spinner=False)
def _run_optimizer_cached(
    method_value: str,
    prices_selected: pd.DataFrame,
    max_weight: float,
    risk_free_rate: float,
):
    method = OptimizationMethod(method_value)
    optimizer = PortfolioOptimizer()
    return _run_optimizer(
        optimizer=optimizer,
        method=method,
        prices_selected=prices_selected,
        max_weight=float(max_weight),
        risk_free_rate=float(risk_free_rate),
    )


def _apply_sector_constraint(
    optimizer: PortfolioOptimizer,
    weights: pd.Series,
    sector_map: dict | None,
    controls: OptimizerControls,
) -> pd.Series:
    if not controls.enable_sector_cap:
        return weights
    if isinstance(sector_map, dict) and len(sector_map) > 0:
        selected_sector_map = {p: sector_map.get(p, "Unknown") for p in weights.index}
        capped_weights = optimizer.apply_sector_cap(
            weights=weights,
            sector_map=selected_sector_map,
            max_sector_weight=controls.max_sector_weight,
        )
        st.caption(f"Sector cap applied: max {controls.max_sector_weight:.0%} per sector.")
        return capped_weights

    st.warning("Sector map unavailable; skipped sector constraint.")
    return weights


def _store_optimizer_session_weights(weights: pd.Series, latest_price_date: pd.Timestamp | None) -> None:
    st.session_state["optimizer_weights"] = {
        p: float(w) for p, w in weights.items() if float(w) > 0
    }
    st.session_state["optimizer_price_latest_date"] = (
        latest_price_date.date().isoformat() if latest_price_date is not None else ""
    )


def _build_sector_exposure(allocation_df: pd.DataFrame) -> pd.DataFrame:
    return (
        allocation_df.groupby("sector", dropna=False)["weight"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"weight": "sector_weight"})
    )


def _render_sector_cap_warning(
    sector_exposure: pd.DataFrame,
    controls: OptimizerControls,
) -> None:
    if not controls.enable_sector_cap or sector_exposure.empty:
        return
    realized_max = float(sector_exposure["sector_weight"].max())
    if realized_max > controls.max_sector_weight + 1e-6:
        st.warning(
            f"Sector cap target {controls.max_sector_weight:.0%} is infeasible with current selection "
            f"(realized max {realized_max:.0%})."
        )


def _render_allocation_chart(allocation_df: pd.DataFrame, method: OptimizationMethod) -> None:
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
        title=f"Allocation ({method.value})",
        margin=dict(l=20, r=20, t=50, b=20),
        height=420,
    )
    st.plotly_chart(fig, width="stretch")


def _render_sector_exposure(sector_exposure: pd.DataFrame) -> None:
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


def _render_allocation_table(allocation_df: pd.DataFrame) -> None:
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


def _render_allocation_outputs(
    allocation_df: pd.DataFrame,
    method: OptimizationMethod,
    controls: OptimizerControls,
) -> None:
    sector_exposure = _build_sector_exposure(allocation_df)
    _render_sector_cap_warning(sector_exposure, controls)

    chart_col, table_col = st.columns([1.2, 1.4])
    with chart_col:
        _render_allocation_chart(allocation_df, method)
        _render_sector_exposure(sector_exposure)

    with table_col:
        _render_allocation_table(allocation_df)


def render_optimizer_view(
    prices_wide: pd.DataFrame,
    ticker_map: dict,
    sector_map: dict | None = None,
    selected_permnos=None,
    selected_tickers=None,
    universe_audit: OptimizerUniverseResult | None = None,
):
    """Render portfolio optimization controls and allocations."""
    st.header("📦 Portfolio Optimizer")

    if not isinstance(prices_wide, pd.DataFrame) or prices_wide.empty:
        _clear_optimizer_session_weights()
        st.warning("No price data available for optimization.")
        return

    selected_assets = _render_asset_selector(
        prices_wide=prices_wide,
        ticker_map=ticker_map,
        selected_permnos=selected_permnos,
        selected_tickers=selected_tickers,
        universe_audit=universe_audit,
    )
    if selected_assets is None:
        return

    prepared_prices = _prepare_selected_prices(
        prices_wide=prices_wide,
        selected_assets=selected_assets,
        ticker_map=ticker_map,
    )
    if prepared_prices is None:
        return
    prices_selected, latest_price_date, _refresh_source = prepared_prices

    controls = _render_optimizer_controls()
    feasibility = diagnose_max_weight_feasibility(
        n_assets=prices_selected.shape[1],
        max_weight=controls.max_weight,
    )
    if not bool(feasibility.get("is_feasible")):
        st.error(str(feasibility.get("message", "Max-weight cap is infeasible.")))
    elif bool(feasibility.get("is_boundary_forced")):
        st.warning(str(feasibility.get("message", "")))

    optimizer = PortfolioOptimizer()
    _render_optimizer_method_status(optimizer, controls.method)
    optimizer_result = _run_optimizer_cached(
        method_value=controls.method.value,
        prices_selected=prices_selected,
        max_weight=controls.max_weight,
        risk_free_rate=controls.risk_free_rate,
    )
    weights = optimizer_result.weights
    optimizer_diagnostics = optimizer_result.diagnostics
    _render_optimizer_diagnostics(optimizer_diagnostics)

    if not isinstance(weights, pd.Series) or weights.empty:
        _clear_optimizer_session_weights()
        st.warning("Unable to compute weights with current inputs.")
        return

    weights = weights.reindex(prices_selected.columns).fillna(0.0)
    if float(weights.sum()) <= 0:
        _clear_optimizer_session_weights()
        st.warning("No positive allocation produced by optimizer.")
        return
    weights = weights / float(weights.sum())
    weights = _apply_sector_constraint(optimizer, weights, sector_map, controls)

    fallback_used = bool(getattr(optimizer_diagnostics, "fallback_used", False))
    _render_allocation_explanation(
        method=controls.method,
        feasibility=feasibility,
        universe_audit=universe_audit,
        enable_sector_cap=controls.enable_sector_cap,
        max_sector_weight=controls.max_sector_weight,
        fallback_used=fallback_used,
    )
    _store_optimizer_session_weights(weights, latest_price_date)

    allocation_df = _build_allocation_table(
        prices_selected=prices_selected,
        weights=weights,
        ticker_map=ticker_map,
        sector_map=sector_map,
        portfolio_value=controls.portfolio_value,
    )
    if allocation_df.empty:
        _clear_optimizer_session_weights()
        st.warning("Optimization produced no investable allocation.")
        return

    _render_allocation_outputs(allocation_df, controls.method, controls)
