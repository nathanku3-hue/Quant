"""Phase 6 research optimizer simulation view."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data_orchestrator import load_strategy_metrics_from_results
from core.data_orchestrator import PriceEndpointFreshness
from core.data_orchestrator import build_price_endpoint_freshness
from core.data_orchestrator import price_frame_latest_date
from core.data_orchestrator import refresh_selected_prices_with_live_overlay
from strategies.optimizer import (
    DEFAULT_OPTIMIZATION_METHOD,
    OPTIMIZATION_METHOD_OPTIONS,
    OptimizationMethod,
    PortfolioOptimizer,
)
from strategies.portfolio_universe import (
    OptimizerUniverseResult,
    diagnose_max_weight_feasibility,
    get_maintain_weight_caps,
    optimizer_universe_health_summary,
    update_position_memory_after_optimization,
)
from strategies.rule100_softmax import rule100_config_from_max_weight, softmax_v1_weights

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


@dataclass(frozen=True)
class PortfolioReplaySelection:
    """Explicit dashboard replay selection published by optimizer controls."""

    method: str
    max_weight: float
    risk_free_rate: float
    replay_assets: tuple[object, ...]
    latest_price_date: str
    source: str
    signature: dict


PORTFOLIO_REPLAY_SELECTION_KEY = "portfolio_replay_selection"
PORTFOLIO_REPLAY_SELECTION_VERSION = "portfolio_replay_selection_v1"
PORTFOLIO_ALLOCATION_STATE_KEY = "portfolio_allocation_state"
PORTFOLIO_ALLOCATION_MODE_KEY = "portfolio_allocation_mode"
PORTFOLIO_ALLOCATION_SOURCE_KEY = "portfolio_allocation_source"
PORTFOLIO_ALLOCATION_WEIGHTS_KEY = "portfolio_allocation_weights"
PORTFOLIO_ALLOCATION_CASH_ONLY_KEY = "portfolio_allocation_cash_only"
PORTFOLIO_ALLOCATION_PRICE_DATE_KEY = "portfolio_allocation_price_latest_date"
PORTFOLIO_CURRENT_HOLD_REPLAY_KEY = "portfolio_current_hold_replay"
RULE100_SOFTMAX_V1_SOURCE = "rule100_softmax_v1"


def _stable_hash(values: list[str]) -> str:
    payload = json.dumps(values, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def portfolio_replay_asset_identity(asset: object) -> str:
    return f"{type(asset).__name__}:{asset}"


def _selected_price_content_hash(
    prices_wide: pd.DataFrame,
    replay_assets: tuple[object, ...],
) -> str:
    if not isinstance(prices_wide, pd.DataFrame) or prices_wide.empty or not replay_assets:
        return ""
    selected = prices_wide.reindex(columns=list(replay_assets))
    row_hash = pd.util.hash_pandas_object(selected, index=True).to_numpy(dtype="uint64", copy=False)
    digest = hashlib.sha256()
    digest.update(row_hash.tobytes())
    digest.update(json.dumps([portfolio_replay_asset_identity(asset) for asset in replay_assets], separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()


def _price_frame_identity(
    prices_wide: pd.DataFrame,
    replay_assets: tuple[object, ...],
) -> dict[str, object]:
    if not isinstance(prices_wide, pd.DataFrame) or prices_wide.empty:
        return {
            "rows": 0,
            "columns": 0,
            "index_start": "",
            "index_end": "",
            "columns_hash": "",
            "selected_price_hash": "",
        }
    index = pd.to_datetime(pd.Index(prices_wide.index), errors="coerce")
    valid_index = index[pd.notna(index)]
    index_start = valid_index.min().date().isoformat() if len(valid_index) else ""
    index_end = valid_index.max().date().isoformat() if len(valid_index) else ""
    return {
        "rows": int(prices_wide.shape[0]),
        "columns": int(prices_wide.shape[1]),
        "index_start": index_start,
        "index_end": index_end,
        "columns_hash": _stable_hash([portfolio_replay_asset_identity(col) for col in prices_wide.columns]),
        "selected_price_hash": _selected_price_content_hash(prices_wide, replay_assets),
    }


def build_portfolio_replay_selection_signature(
    *,
    prices_wide: pd.DataFrame,
    replay_assets: tuple[object, ...],
    method: str,
    max_weight: float,
    risk_free_rate: float,
) -> dict[str, object]:
    """Return the signature that binds a replay selection to current controls and prices."""

    return {
        "version": PORTFOLIO_REPLAY_SELECTION_VERSION,
        "method": str(method),
        "max_weight": float(max_weight),
        "risk_free_rate": float(risk_free_rate),
        "replay_assets": [portfolio_replay_asset_identity(asset) for asset in replay_assets],
        "price_frame": _price_frame_identity(prices_wide, replay_assets),
    }


def _clear_portfolio_replay_selection() -> None:
    st.session_state.pop(PORTFOLIO_REPLAY_SELECTION_KEY, None)


def _store_portfolio_replay_selection(
    *,
    prices_wide: pd.DataFrame,
    prices_selected: pd.DataFrame,
    method: str,
    max_weight: float,
    risk_free_rate: float,
    latest_price_date: pd.Timestamp | None,
) -> None:
    replay_assets = tuple(prices_selected.columns)
    latest_value = latest_price_date.date().isoformat() if latest_price_date is not None else ""
    st.session_state[PORTFOLIO_REPLAY_SELECTION_KEY] = PortfolioReplaySelection(
        method=str(method),
        max_weight=float(max_weight),
        risk_free_rate=float(risk_free_rate),
        replay_assets=replay_assets,
        latest_price_date=latest_value,
        source="optimizer_controls",
        signature=build_portfolio_replay_selection_signature(
            prices_wide=prices_wide,
            replay_assets=replay_assets,
            method=str(method),
            max_weight=float(max_weight),
            risk_free_rate=float(risk_free_rate),
        ),
    )


def _coerce_session_weights(raw_weights) -> dict[object, float]:
    if raw_weights is None:
        return {}
    if isinstance(raw_weights, pd.Series):
        series = raw_weights.copy()
    elif isinstance(raw_weights, dict):
        series = pd.Series(raw_weights, dtype="float64")
    else:
        return {}

    series = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
    series = series.dropna()
    series = series[series > 0]
    return {asset: float(weight) for asset, weight in series.items()}


def _write_portfolio_allocation_state(
    *,
    mode: str,
    source: str,
    weights: pd.Series | dict | None,
    latest_price_date: pd.Timestamp | None,
    cash_only: bool,
) -> None:
    latest_value = latest_price_date.date().isoformat() if latest_price_date is not None else ""
    weight_payload = {} if cash_only else _coerce_session_weights(weights)
    state = {
        "mode": mode,
        "source": source,
        "weights": weight_payload,
        "cash_only": bool(cash_only),
        "latest_price_date": latest_value,
    }

    st.session_state[PORTFOLIO_ALLOCATION_STATE_KEY] = state
    st.session_state[PORTFOLIO_ALLOCATION_MODE_KEY] = mode
    st.session_state[PORTFOLIO_ALLOCATION_SOURCE_KEY] = source
    st.session_state[PORTFOLIO_ALLOCATION_WEIGHTS_KEY] = weight_payload
    st.session_state[PORTFOLIO_ALLOCATION_CASH_ONLY_KEY] = bool(cash_only)
    st.session_state[PORTFOLIO_ALLOCATION_PRICE_DATE_KEY] = latest_value
    st.session_state["optimizer_weights"] = weight_payload
    st.session_state["optimizer_price_latest_date"] = latest_value
    st.session_state["optimizer_cash_only"] = bool(cash_only)

    if mode in {"current_hold_replay", "rule_of_100_replay"}:
        st.session_state[PORTFOLIO_CURRENT_HOLD_REPLAY_KEY] = {
            "mode": mode,
            "source": source,
            "weights": weight_payload,
            "cash_only": bool(cash_only),
            "latest_price_date": latest_value,
        }
    else:
        st.session_state.pop(PORTFOLIO_CURRENT_HOLD_REPLAY_KEY, None)


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
    """Build a complete simulation weight table with weights, dollars, shares, and cash."""
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
        return _build_cash_allocation_table(portfolio_value)

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


def _build_cash_allocation_table(portfolio_value: float) -> pd.DataFrame:
    try:
        cash_allocation = float(portfolio_value)
    except (TypeError, ValueError):
        cash_allocation = float(DEFAULT_PORTFOLIO_VALUE)
    if not np.isfinite(cash_allocation):
        cash_allocation = float(DEFAULT_PORTFOLIO_VALUE)

    return pd.DataFrame(
        [
            {
                "permno": "CASH",
                "ticker": "CASH",
                "sector": "Cash",
                "weight": 1.0,
                "allocation_usd": cash_allocation,
                "latest_price": np.nan,
                "est_shares": np.nan,
            }
        ]
    )


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


def _universe_health_count(universe_audit: OptimizerUniverseResult | None, key: str) -> int:
    value = optimizer_universe_health_summary(universe_audit).get(key, 0)
    try:
        return int(value)
    except (TypeError, ValueError):
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


def _order_assets_by_trailing_one_year_return(
    asset_options: list,
    prices_wide: pd.DataFrame,
    price_freshness: PriceEndpointFreshness | None = None,
) -> list:
    """Order default asset choices by local trailing 1-year return with stable fallback."""
    if not isinstance(prices_wide, pd.DataFrame) or prices_wide.empty:
        return list(asset_options)

    prices = prices_wide.reindex(columns=list(asset_options)).copy()
    prices.index = pd.to_datetime(prices.index, errors="coerce")
    prices = prices.loc[prices.index.notna()].sort_index()
    prices = prices.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    prices = prices.dropna(axis=1, how="all")
    if prices.empty:
        return list(asset_options)
    if price_freshness is None:
        price_freshness = build_price_endpoint_freshness(prices, list(asset_options))

    latest_date = price_frame_latest_date(
        prices,
        freshness=price_freshness,
        columns=list(asset_options),
    )
    if latest_date is None:
        return list(asset_options)
    anchor_date = latest_date - pd.DateOffset(years=1)
    latest_by_asset = price_freshness.latest_by_column
    ranked: list[tuple[int, float, int, object]] = []
    original_position = {asset: idx for idx, asset in enumerate(asset_options)}

    for asset in asset_options:
        if asset not in prices.columns:
            ranked.append((1, 0.0, original_position[asset], asset))
            continue
        asset_latest = latest_by_asset.get(asset)
        if asset_latest is None or pd.Timestamp(asset_latest).normalize() < pd.Timestamp(latest_date).normalize():
            ranked.append((1, 0.0, original_position[asset], asset))
            continue
        series = prices[asset].dropna()
        series = series[series.index <= latest_date]
        if series.empty:
            ranked.append((1, 0.0, original_position[asset], asset))
            continue

        ending = series.iloc[-1]
        history = series[series.index <= anchor_date]
        if history.empty:
            ranked.append((1, 0.0, original_position[asset], asset))
            continue
        starting = history.iloc[-1]
        if not np.isfinite(starting) or not np.isfinite(ending) or float(starting) <= 0:
            ranked.append((1, 0.0, original_position[asset], asset))
            continue

        trailing_return = float(ending) / float(starting) - 1.0
        if not np.isfinite(trailing_return):
            ranked.append((1, 0.0, original_position[asset], asset))
            continue
        ranked.append((0, -trailing_return, original_position[asset], asset))

    return [asset for _fallback, _neg_return, _position, asset in sorted(ranked)]


def _render_universe_audit(universe_audit: OptimizerUniverseResult | None) -> None:
    audit_df = _universe_audit_frame(universe_audit)
    if audit_df.empty:
        return

    st.subheader("Universe Audit")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Included", _universe_count(universe_audit, "included"))
    with c2:
        st.metric("Excluded", _universe_count(universe_audit, "excluded"))
    with c3:
        st.metric("Missing Map", _universe_count(universe_audit, "missing_mappings"))
    with c4:
        st.metric("Missing History", _universe_health_count(universe_audit, "missing_history"))
    with c5:
        st.metric("Stale Endpoint", _universe_health_count(universe_audit, "stale_endpoint"))

    display = audit_df.rename(
        columns={
            "ticker": "Ticker",
            "permno": "Permno",
            "rating": "Rating",
            "action": "Action",
            "status": "Status",
            "reason": "Reason",
            "history_obs": "History Obs",
            "latest_price_date": "Latest Price Date",
        }
    )
    preferred_cols = ["Ticker", "Permno", "Status", "Reason", "Latest Price Date", "Rating", "Action", "History Obs"]
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
    st.subheader("Why This Optimizer Allocation?")
    rows = [
        {"Item": "Universe source", "Status": "Explicit optimizer universe builder"},
        {"Item": "Thesis mode", "Status": "Thesis-neutral; no MU hard floor or conviction tilt"},
        {"Item": "Optimizer method", "Status": method.value},
        {"Item": "Eligible assets", "Status": str(_universe_count(universe_audit, "included"))},
        {"Item": "Excluded by policy", "Status": str(_universe_count(universe_audit, "excluded"))},
        {"Item": "Missing ticker mappings", "Status": str(_universe_count(universe_audit, "missing_mappings"))},
        {"Item": "Missing local price history", "Status": str(_universe_health_count(universe_audit, "missing_history"))},
        {"Item": "Stale local price endpoints", "Status": str(_universe_health_count(universe_audit, "stale_endpoint"))},
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
    price_freshness: PriceEndpointFreshness | None = None,
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
    explicit_user_selection = selected_permnos is not None or selected_tickers is not None
    if not default_selection and not explicit_user_selection and candidate_options is not None:
        default_selection = _order_assets_by_trailing_one_year_return(
            list(candidate_options),
            prices_wide,
            price_freshness=price_freshness,
        )
    elif not default_selection and not explicit_user_selection:
        default_selection = _order_assets_by_trailing_one_year_return(
            list(prices_wide.columns),
            prices_wide,
            price_freshness=price_freshness,
        )[: min(10, prices_wide.shape[1])]

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
    price_freshness: PriceEndpointFreshness | None = None,
) -> tuple[pd.DataFrame, pd.Timestamp | None, str] | None:
    prices_selected = prices_wide.reindex(columns=selected_assets)
    required_latest = price_frame_latest_date(prices_wide, freshness=price_freshness)
    prices_selected, latest_price_date, refresh_source = refresh_selected_prices_with_live_overlay(
        prices_selected=prices_selected,
        ticker_map=ticker_map,
        required_latest=required_latest,
    )
    prices_selected = prices_selected.dropna(axis=1, how="all")

    if prices_selected.empty or prices_selected.shape[1] == 0:
        _clear_optimizer_session_weights()
        st.warning("Selected assets have no usable price data.")
        return None

    if latest_price_date is not None:
        if refresh_source == "live":
            source_label = "live refresh"
        elif refresh_source == "live_stale_dropped":
            source_label = "live refresh; stale assets dropped"
        elif refresh_source == "local_stale_dropped":
            source_label = "local TRI; stale assets dropped"
        else:
            source_label = "local TRI"
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


def _is_rule100_method(method: OptimizationMethod) -> bool:
    return method == OptimizationMethod.RULE_OF_100


def _render_optimizer_controls() -> OptimizerControls:
    ctl1, ctl2, ctl3 = st.columns([1.5, 1, 1])
    with ctl1:
        selected_method = st.selectbox(
            "Method",
            list(OPTIMIZATION_METHOD_OPTIONS),
            index=list(OPTIMIZATION_METHOD_OPTIONS).index(DEFAULT_OPTIMIZATION_METHOD),
            format_func=lambda method: method.value,
        )
    # Store raw selection before resolution (replay needs the original choice)
    st.session_state["optimizer_selected_method"] = OptimizationMethod(selected_method).value
    method = _resolve_historical_method(OptimizationMethod(selected_method))
    is_rule100 = _is_rule100_method(method)

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
            "Simulation notional ($)",
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


def _render_rule100_lifecycle_allocation(
    prices_selected: pd.DataFrame,
    selected_assets: list,
    ticker_map: dict,
    sector_map: dict | None,
    controls: OptimizerControls,
    latest_price_date: pd.Timestamp | None,
    rule100_candidate_frame: pd.DataFrame | None = None,
    show_allocation_outputs: bool = True,
) -> None:
    target_weights = _rule100_softmax_weights_for_ui(
        selected_assets=selected_assets,
        ticker_map=ticker_map,
        as_of=latest_price_date,
        candidate_frame=rule100_candidate_frame,
        max_weight=controls.max_weight,
    )
    if not target_weights.empty and float(target_weights.sum()) > 0:
        st.info("Rule of 100 softmax v1 sizing output: showing PIT softmax targets for eligible lifecycle holds with residual cash.")
        _write_portfolio_allocation_state(
            mode="rule_of_100_replay",
            source=RULE100_SOFTMAX_V1_SOURCE,
            weights=target_weights,
            latest_price_date=latest_price_date,
            cash_only=False,
        )
        allocation_df = _build_allocation_table(
            prices_selected=prices_selected,
            weights=target_weights,
            ticker_map=ticker_map,
            sector_map=sector_map,
            portfolio_value=controls.portfolio_value,
        )
    else:
        st.info("Rule of 100 softmax v1 sizing output has no eligible lifecycle holds as of the current PIT state. Showing cash only.")
        _write_portfolio_allocation_state(
            mode="rule_of_100_replay",
            source=RULE100_SOFTMAX_V1_SOURCE,
            weights={},
            latest_price_date=latest_price_date,
            cash_only=True,
        )
        allocation_df = _build_cash_allocation_table(controls.portfolio_value)

    if show_allocation_outputs:
        _render_allocation_outputs(
            allocation_df,
            controls.method,
            controls,
            title_override="Allocation (Rule of 100)",
        )


def _render_optimizer_method_status(optimizer: PortfolioOptimizer, method: OptimizationMethod) -> None:
    if not method.is_mean_variance:
        return
    if optimizer.has_slsqp():
        st.caption("Optimization Method: Mean-Variance (SLSQP)")
    else:
        st.warning("Optimization Method: Fallback (Equal Weight) — SciPy unavailable")


def _clear_optimizer_session_weights() -> None:
    _clear_portfolio_replay_selection()
    _write_portfolio_allocation_state(
        mode="unavailable",
        source="optimizer",
        weights={},
        latest_price_date=None,
        cash_only=False,
    )


def _set_optimizer_cash_only_session() -> None:
    _clear_portfolio_replay_selection()
    _write_portfolio_allocation_state(
        mode="cash_only",
        source="optimizer",
        weights={},
        latest_price_date=None,
        cash_only=True,
    )


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
    _write_portfolio_allocation_state(
        mode="optimizer",
        source="optimizer",
        weights=weights,
        latest_price_date=latest_price_date,
        cash_only=False,
    )


def _store_current_hold_replay_session(weights: pd.Series, latest_price_date: pd.Timestamp | None) -> None:
    _write_portfolio_allocation_state(
        mode="current_hold_replay",
        source="lifecycle_replay",
        weights=weights,
        latest_price_date=latest_price_date,
        cash_only=False,
    )


def _has_new_entry_candidates(universe_audit: OptimizerUniverseResult | None) -> bool:
    if universe_audit is None:
        return False
    return any(record.status == "included" and record.reason == "eligible_rating" for record in universe_audit.included)


def _has_current_hold_candidates(universe_audit: OptimizerUniverseResult | None) -> bool:
    if universe_audit is None:
        return False
    return any(record.status == "included_current_hold" for record in universe_audit.included)


def _current_hold_weights_from_memory(
    selected_assets: list,
    ticker_map: dict,
    position_memory: dict[str, dict] | None,
) -> pd.Series:
    if not position_memory:
        return pd.Series(dtype="float64")

    ticker_to_permno = {str(ticker).upper(): permno for permno, ticker in (ticker_map or {}).items()}
    selected = set(selected_assets)
    weights: dict[object, float] = {}
    for ticker, entry in position_memory.items():
        permno = ticker_to_permno.get(str(ticker).upper())
        if permno not in selected:
            continue
        try:
            weight = float(entry.get("last_weight", 0.0))
        except (TypeError, ValueError):
            weight = 0.0
        if np.isfinite(weight) and weight > 0:
            weights[permno] = weight

    series = pd.Series(weights, dtype="float64")
    total = float(series.sum()) if not series.empty else 0.0
    if total > 1.0:
        series = series / total
    return series


def _load_rule100_candidate_frame_for_ui(as_of: pd.Timestamp | None) -> pd.DataFrame:
    from scripts.rule100_softmax_v1_audit import build_current_rule100_candidate_frame

    return build_current_rule100_candidate_frame(as_of=as_of)


def _rule100_softmax_weights_for_ui(
    *,
    selected_assets: list,
    ticker_map: dict,
    as_of: pd.Timestamp | None,
    candidate_frame: pd.DataFrame | None = None,
    max_weight: float = DEFAULT_MAX_WEIGHT,
) -> pd.Series:
    candidates = candidate_frame
    if candidates is None:
        try:
            candidates = _load_rule100_candidate_frame_for_ui(as_of)
        except Exception:
            return pd.Series(dtype="float64")
    if not isinstance(candidates, pd.DataFrame) or candidates.empty:
        return pd.Series(dtype="float64")

    required = {"ticker", "factor_positive_count", "technical_quality"}
    if not required.issubset(candidates.columns):
        return pd.Series(dtype="float64")

    selected = set(selected_assets)
    ticker_to_permno = {
        str(ticker).upper(): permno
        for permno, ticker in (ticker_map or {}).items()
        if permno in selected
    }
    if not ticker_to_permno:
        return pd.Series(dtype="float64")

    eligible_mask = candidates.get(
        "sizing_eligible",
        pd.Series(False, index=candidates.index, dtype=bool),
    ).astype(bool)
    eligible = candidates.loc[eligible_mask].copy()
    if eligible.empty:
        return pd.Series(dtype="float64")

    try:
        ticker_weights = softmax_v1_weights(
            eligible,
            rule100_config_from_max_weight(max_weight),
        )
    except ValueError:
        return pd.Series(dtype="float64")

    weights: dict[object, float] = {}
    for idx, weight in ticker_weights.items():
        ticker = str(eligible.loc[idx, "ticker"]).upper().strip()
        permno = ticker_to_permno.get(ticker)
        if permno is None:
            continue
        try:
            w = float(weight)
        except (TypeError, ValueError):
            continue
        if np.isfinite(w) and w > 0:
            weights[permno] = weights.get(permno, 0.0) + w

    series = pd.Series(weights, dtype="float64")
    total = float(series.sum()) if not series.empty else 0.0
    if total > 1.0:
        series = series / total
    return series


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
    if _is_cash_only_sector_exposure(sector_exposure):
        return
    realized_max = float(sector_exposure["sector_weight"].max())
    if realized_max > controls.max_sector_weight + 1e-6:
        st.warning(
            f"Sector cap target {controls.max_sector_weight:.0%} is infeasible with current selection "
            f"(realized max {realized_max:.0%})."
        )


def _render_allocation_chart(
    allocation_df: pd.DataFrame,
    method: OptimizationMethod,
    title_override: str | None = None,
) -> None:
    if title_override is not None:
        title = title_override
    else:
        title = "Allocation (100% Cash)" if _is_cash_only_allocation(allocation_df) else f"Allocation ({method.value})"
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
        title=title,
        margin=dict(l=20, r=20, t=50, b=20),
        height=420,
    )
    st.plotly_chart(fig, width="stretch")


def _is_cash_only_allocation(allocation_df: pd.DataFrame) -> bool:
    if not isinstance(allocation_df, pd.DataFrame) or allocation_df.empty:
        return False
    if not {"ticker", "weight"}.issubset(allocation_df.columns):
        return False
    tickers = allocation_df["ticker"].astype(str).str.upper()
    weights = pd.to_numeric(allocation_df["weight"], errors="coerce").fillna(0.0)
    return bool((tickers == "CASH").all() and abs(float(weights.sum()) - 1.0) <= 1e-9)


def _is_cash_only_sector_exposure(sector_exposure: pd.DataFrame) -> bool:
    if not isinstance(sector_exposure, pd.DataFrame) or sector_exposure.empty:
        return False
    if not {"sector", "sector_weight"}.issubset(sector_exposure.columns):
        return False
    sectors = sector_exposure["sector"].astype(str).str.lower()
    weights = pd.to_numeric(sector_exposure["sector_weight"], errors="coerce").fillna(0.0)
    return bool((sectors == "cash").all() and abs(float(weights.sum()) - 1.0) <= 1e-9)


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
    st.subheader("Simulation Weight Table")
    st.dataframe(
        allocation_df.rename(
            columns={
                "permno": "Permno",
                "ticker": "Ticker",
                "sector": "Sector",
                "weight": "Weight",
                "allocation_usd": "Allocation ($)",
                "latest_price": "Latest Price ($)",
                "est_shares": "Simulated Shares at Notional",
            }
        ).style.format(
            {
                "Weight": "{:.2%}",
                "Allocation ($)": "${:,.2f}",
                "Latest Price ($)": "${:,.2f}",
                "Simulated Shares at Notional": "{:,.2f}",
            }
        ),
        width="stretch",
        height=420,
    )


def _render_allocation_outputs(
    allocation_df: pd.DataFrame,
    method: OptimizationMethod,
    controls: OptimizerControls,
    title_override: str | None = None,
) -> None:
    sector_exposure = _build_sector_exposure(allocation_df)
    _render_sector_cap_warning(sector_exposure, controls)

    chart_col, table_col = st.columns([1.2, 1.4])
    with chart_col:
        _render_allocation_chart(allocation_df, method, title_override=title_override)
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
    position_memory: dict[str, dict] | None = None,
    rule100_candidate_frame: pd.DataFrame | None = None,
    price_freshness: PriceEndpointFreshness | None = None,
    show_allocation_outputs: bool = True,
):
    """Render portfolio optimization controls and allocations."""
    st.header("Research Optimizer - Simulation Only")

    if not isinstance(prices_wide, pd.DataFrame) or prices_wide.empty:
        _clear_optimizer_session_weights()
        st.warning("No price data available for optimization.")
        return
    if price_freshness is None:
        price_freshness = build_price_endpoint_freshness(prices_wide)

    selected_assets = _render_asset_selector(
        prices_wide=prices_wide,
        ticker_map=ticker_map,
        selected_permnos=selected_permnos,
        selected_tickers=selected_tickers,
        universe_audit=universe_audit,
        price_freshness=price_freshness,
    )
    if selected_assets is None:
        _set_optimizer_cash_only_session()
        controls = OptimizerControls(
            method=DEFAULT_OPTIMIZATION_METHOD,
            max_weight=DEFAULT_MAX_WEIGHT,
            portfolio_value=DEFAULT_PORTFOLIO_VALUE,
            enable_sector_cap=False,
            max_sector_weight=1.0,
            risk_free_rate=0.0,
        )
        if show_allocation_outputs:
            _render_allocation_outputs(
                _build_cash_allocation_table(controls.portfolio_value),
                controls.method,
                controls,
            )
        return

    prepared_prices = _prepare_selected_prices(
        prices_wide=prices_wide,
        selected_assets=selected_assets,
        ticker_map=ticker_map,
        price_freshness=price_freshness,
    )
    if prepared_prices is None:
        _clear_portfolio_replay_selection()
        return
    prices_selected, latest_price_date, _refresh_source = prepared_prices

    controls = _render_optimizer_controls()
    st.session_state["optimizer_method"] = st.session_state.get("optimizer_selected_method", controls.method.value)
    st.session_state["optimizer_max_weight"] = controls.max_weight
    st.session_state["optimizer_risk_free_rate"] = controls.risk_free_rate
    selection_method = st.session_state["optimizer_method"]
    try:
        _store_portfolio_replay_selection(
            prices_wide=prices_wide,
            prices_selected=prices_selected,
            method=selection_method,
            max_weight=controls.max_weight,
            risk_free_rate=controls.risk_free_rate,
            latest_price_date=latest_price_date,
        )
    except Exception:
        _clear_portfolio_replay_selection()
        st.error("Replay selection unavailable: selected assets could not be signed for replay.")
        return
    if not show_allocation_outputs:
        st.caption("Controls-only: allocation evidence is rendered from the latest daily replay snapshot below.")
        return
    if _is_rule100_method(controls.method):
        _render_rule100_lifecycle_allocation(
            prices_selected=prices_selected,
            selected_assets=list(prices_selected.columns),
            ticker_map=ticker_map,
            sector_map=sector_map,
            controls=controls,
            latest_price_date=latest_price_date,
            rule100_candidate_frame=rule100_candidate_frame,
            show_allocation_outputs=show_allocation_outputs,
        )
        return

    if (
        _has_current_hold_candidates(universe_audit)
        and not _has_new_entry_candidates(universe_audit)
    ):
        hold_weights = _current_hold_weights_from_memory(
            selected_assets=list(prices_selected.columns),
            ticker_map=ticker_map,
            position_memory=position_memory,
        )
        if not hold_weights.empty and float(hold_weights.sum()) > 0:
            st.info("Open replay lifecycle output: no new PIT ENTER candidates today, so the page is showing open lifecycle holdings with residual cash instead of optimizer output.")
            _store_current_hold_replay_session(hold_weights, latest_price_date)
            allocation_df = _build_allocation_table(
                prices_selected=prices_selected,
                weights=hold_weights,
                ticker_map=ticker_map,
                sector_map=sector_map,
                portfolio_value=controls.portfolio_value,
            )
            if show_allocation_outputs:
                _render_allocation_outputs(
                    allocation_df,
                    controls.method,
                    controls,
                    title_override="Allocation (Lifecycle Holds)",
                )
            return

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

    # Enforce maintain-tier weight caps: positions can't grow beyond last allocation
    if position_memory and universe_audit is not None:
        maintain_caps = get_maintain_weight_caps(universe_audit, position_memory, ticker_map)
        if maintain_caps:
            for permno, cap in maintain_caps.items():
                if permno in weights.index and float(weights[permno]) > cap:
                    weights[permno] = cap
            total = float(weights.sum())
            if total > 1.0:
                weights = weights / total

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

    # Persist position memory after successful optimization
    if universe_audit is not None:
        update_position_memory_after_optimization(
            weights=weights,
            ticker_map=ticker_map,
            universe=universe_audit,
        )

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

    if show_allocation_outputs:
        _render_allocation_outputs(allocation_df, controls.method, controls)
