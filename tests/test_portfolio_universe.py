from __future__ import annotations

from pathlib import Path

import pandas as pd

from strategies.optimizer import OPTIMIZATION_METHOD_OPTIONS, OptimizationMethod
from strategies.portfolio_universe import (
    build_optimizer_universe,
    diagnose_max_weight_feasibility,
)


def _scan_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Ticker": "AAA", "Rating": "EXIT / TRAIL TIGHT", "Action": "BUY AGGRESSIVE"},
            {"Ticker": "BBB", "Rating": "WATCH / HOLD", "Action": "BUY AGGRESSIVE"},
            {"Ticker": "CCC", "Rating": "ENTER: STRONG BUY (Coiled)", "Action": "BUY AGGRESSIVE"},
            {"Ticker": "DDD", "Rating": "ENTER: BUY", "Action": "BUY AGGRESSIVE"},
            {"Ticker": "EEE", "Rating": "ENTER: BUY", "Action": "BUY AGGRESSIVE"},
            {"Ticker": "FFF", "Rating": "IGNORE", "Action": "IGNORE (Opportunity Cost)"},
            {"Ticker": "MU", "Rating": "ENTER: BUY", "Action": "BUY AGGRESSIVE"},
        ]
    )


def _prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            1: [10.0, 10.5, 10.8, 11.0],
            2: [20.0, 20.5, 21.0, 21.5],
            3: [30.0, 30.5, 31.0, 32.0],
            5: [50.0, None, None, None],
            6: [60.0, 61.0, 62.0, 63.0],
            7: [70.0, 71.0, 72.0, 73.0],
        },
        index=pd.date_range("2026-01-01", periods=4),
    )


def _ticker_map() -> dict[int, str]:
    return {1: "AAA", 2: "BBB", 3: "CCC", 5: "EEE", 6: "MU", 7: "FFF"}


def test_display_sort_does_not_define_optimizer_universe() -> None:
    result = build_optimizer_universe(_scan_frame(), _ticker_map(), _prices())

    assert result.included_tickers == ["CCC", "MU"]
    assert "AAA" not in result.included_tickers
    assert "BBB" not in result.included_tickers


def test_optimizer_universe_excludes_exit_and_kill_by_default() -> None:
    result = build_optimizer_universe(_scan_frame(), _ticker_map(), _prices())
    excluded = {record.ticker: record.reason for record in result.excluded}

    assert excluded["AAA"] == "exit_or_kill"
    assert excluded["FFF"] == "ignore"


def test_watch_is_research_only_by_default() -> None:
    result = build_optimizer_universe(_scan_frame(), _ticker_map(), _prices())
    records = {record.ticker: record for record in result.excluded}

    assert records["BBB"].status == "research_only"
    assert records["BBB"].reason == "watch_research_only"


def test_missing_ticker_resolution_is_reported() -> None:
    result = build_optimizer_universe(_scan_frame(), _ticker_map(), _prices())

    assert [record.ticker for record in result.missing_mappings] == ["DDD"]
    assert "DDD" not in result.included_tickers


def test_insufficient_price_history_is_reported() -> None:
    result = build_optimizer_universe(_scan_frame(), _ticker_map(), _prices())

    assert [record.ticker for record in result.insufficient_history] == ["EEE"]
    assert result.insufficient_history[0].history_obs == 1


def test_cap_at_one_over_n_flags_forced_equal_weight() -> None:
    boundary = diagnose_max_weight_feasibility(n_assets=19, max_weight=1 / 19)
    infeasible = diagnose_max_weight_feasibility(n_assets=19, max_weight=0.05)
    open_room = diagnose_max_weight_feasibility(n_assets=3, max_weight=0.35)

    assert boundary["is_feasible"] is True
    assert boundary["is_boundary_forced"] is True
    assert "forced toward equal weight" in str(boundary["message"])
    assert infeasible["is_feasible"] is False
    assert open_room["is_feasible"] is True
    assert open_room["is_boundary_forced"] is False


def test_optimizer_method_dropdown_uses_strategy_registry() -> None:
    source = Path("views/optimizer_view.py").read_text(encoding="utf-8")
    method_values = [method.value for method in OPTIMIZATION_METHOD_OPTIONS]

    assert "Auto (Best Sharpe)" not in source
    assert "MEAN_VARIANCE_METHODS =" not in source
    assert "OPTIMIZATION_METHOD_OPTIONS" in source
    assert "Historical Max Sharpe Strategy" in method_values
    assert "Thesis-Neutral Max Sharpe" in method_values
    assert OptimizationMethod.THESIS_NEUTRAL_MAX_SHARPE.is_mean_variance is True


def test_optimizer_view_uses_universe_result_contract() -> None:
    source = Path("views/optimizer_view.py").read_text(encoding="utf-8")

    assert "OptimizerUniverseResult | None" in source
    assert "universe_audit.to_frame()" in source
    assert 'hasattr(universe_audit, "to_frame")' not in source
    assert "isinstance(universe_audit, dict)" not in source


def test_allocation_table_adds_cash_inside_helper() -> None:
    from views.optimizer_view import _build_allocation_table

    prices = pd.DataFrame(
        {1: [10.0, 11.0], 2: [20.0, 21.0]},
        index=pd.date_range("2026-01-01", periods=2),
    )
    weights = pd.Series({1: 0.6, 2: 0.3})

    table = _build_allocation_table(
        prices_selected=prices,
        weights=weights,
        ticker_map={1: "AAA", 2: "BBB"},
        sector_map={1: "Tech", 2: "Health"},
        portfolio_value=1_000.0,
    )
    cash = table.loc[table["ticker"] == "CASH"]

    assert cash.shape[0] == 1
    assert abs(float(cash["weight"].iloc[0]) - 0.1) < 1e-12
    assert abs(float(cash["allocation_usd"].iloc[0]) - 100.0) < 1e-9


def test_optimizer_failure_paths_clear_session_weights() -> None:
    from views.optimizer_view import _clear_optimizer_session_weights
    import views.optimizer_view as optimizer_view

    optimizer_view.st.session_state["optimizer_weights"] = {1: 0.5}
    optimizer_view.st.session_state["optimizer_price_latest_date"] = "2026-01-02"

    _clear_optimizer_session_weights()

    assert optimizer_view.st.session_state["optimizer_weights"] == {}
    assert optimizer_view.st.session_state["optimizer_price_latest_date"] == ""


def test_mu_not_hard_forced() -> None:
    source = (
        Path("views/optimizer_view.py").read_text(encoding="utf-8")
        + "\n"
        + Path("strategies/portfolio_universe.py").read_text(encoding="utf-8")
    )

    assert '"MU minimum"' not in source
    assert "DEFAULT_MICRON_MIN_WEIGHT" not in source
    assert 'min_weight["MU"]' not in source
    assert "MU = 0.20" not in source


def test_no_conviction_mode_added() -> None:
    runtime_source = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in [
            "dashboard.py",
            "views/optimizer_view.py",
            "strategies/portfolio_universe.py",
            "strategies/optimizer.py",
        ]
    )

    assert "Endgame / Conviction" not in runtime_source
    assert "Black-Litterman" not in runtime_source
    assert "MU anchor slider" not in runtime_source
