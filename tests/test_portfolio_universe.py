from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from strategies.optimizer import DEFAULT_OPTIMIZATION_METHOD, OPTIMIZATION_METHOD_OPTIONS, OptimizationMethod
from strategies.portfolio_universe import (
    OptimizerUniversePolicy,
    build_optimizer_universe,
    diagnose_max_weight_feasibility,
    load_current_position_memory,
    map_permno_weights_to_ticker_weights,
    optimizer_universe_health_summary,
    save_position_memory,
    split_history_readiness,
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


def test_open_lifecycle_hold_stays_in_universe_when_today_scan_says_exit() -> None:
    scan = pd.DataFrame(
        [{"Ticker": "AAA", "Rating": "EXIT / TRAIL TIGHT", "Action": "KILL"}]
    )
    result = build_optimizer_universe(
        scan,
        {1: "AAA"},
        _prices(),
        position_memory={
            "AAA": {
                "last_weight": 0.25,
                "source": "lifecycle_replay",
                "entry_date": "2026-01-01",
            }
        },
    )

    assert result.included_tickers == ["AAA"]
    assert result.included[0].status == "included_current_hold"
    assert result.included[0].reason == "open_lifecycle_position"


def test_lifecycle_replay_sell_all_overrides_stale_position_memory(tmp_path: Path) -> None:
    from data.portfolio_lifecycle_log import append_lifecycle_event

    mem_path = tmp_path / "positions.json"
    log_path = tmp_path / "lifecycle.jsonl"
    save_position_memory({"AAA": {"permno": 1, "last_weight": 0.25}}, mem_path)
    append_lifecycle_event("AAA", "ENTER", "2026-01-01", 0.25, permno=1, path=log_path)
    append_lifecycle_event("AAA", "EXIT", "2026-01-05", 0.00, permno=1, path=log_path)

    memory = load_current_position_memory(
        as_of="2026-01-10",
        position_path=mem_path,
        lifecycle_path=log_path,
    )

    assert memory == {}


def test_ticker_weight_mapping_preserves_residual_cash() -> None:
    weights = pd.Series({1: 0.25, 2: 0.25})
    mapped = map_permno_weights_to_ticker_weights(weights, {1: "AAA", 2: "BBB"})

    assert mapped.to_dict() == {"AAA": 0.25, "BBB": 0.25}
    assert float(mapped.sum()) == pytest.approx(0.50)


def test_ticker_weight_mapping_normalizes_only_above_one() -> None:
    weights = pd.Series({1: 0.80, 2: 0.80})
    mapped = map_permno_weights_to_ticker_weights(weights, {1: "AAA", 2: "BBB"})

    assert mapped.to_dict() == {"AAA": 0.5, "BBB": 0.5}
    assert float(mapped.sum()) == pytest.approx(1.0)


def test_missing_ticker_resolution_is_reported() -> None:
    result = build_optimizer_universe(_scan_frame(), _ticker_map(), _prices())

    assert [record.ticker for record in result.missing_mappings] == ["DDD"]
    assert "DDD" not in result.included_tickers


def test_insufficient_price_history_is_reported() -> None:
    result = build_optimizer_universe(_scan_frame(), _ticker_map(), _prices())

    assert [record.ticker for record in result.insufficient_history] == ["EEE"]
    assert result.insufficient_history[0].history_obs == 1


def test_stale_price_endpoint_is_reported_even_with_enough_history() -> None:
    from core.data_orchestrator import build_price_endpoint_freshness

    scan = pd.DataFrame(
        [
            {"Ticker": "AAA", "Rating": "ENTER: BUY", "Action": "BUY AGGRESSIVE"},
            {"Ticker": "BBB", "Rating": "ENTER: BUY", "Action": "BUY AGGRESSIVE"},
        ]
    )
    prices = pd.DataFrame(
        {
            1: [10.0, 11.0, 12.0, None, None],
            2: [20.0, 21.0, 22.0, 23.0, 24.0],
        },
        index=pd.to_datetime(["2026-02-24", "2026-02-25", "2026-02-27", "2026-05-10", "2026-05-11"]),
    )
    freshness = build_price_endpoint_freshness(prices)

    result = build_optimizer_universe(
        scan,
        {1: "AAA", 2: "BBB"},
        prices,
        price_freshness=freshness,
    )

    assert result.included_tickers == ["BBB"]
    stale = {record.ticker: record for record in result.insufficient_history}
    assert stale["AAA"].reason == "stale_price_endpoint"
    assert stale["AAA"].history_obs == 3
    assert stale["AAA"].latest_price_date == "2026-02-27"


def test_history_readiness_splits_missing_history_from_stale_endpoint() -> None:
    from strategies.portfolio_universe import UniverseRecord

    missing = UniverseRecord(
        ticker="RBRK",
        permno=90001,
        rating="ENTER: BUY",
        action="BUY AGGRESSIVE",
        status="insufficient_history",
        reason="local_price_history_unavailable",
        history_obs=0,
        latest_price_date="",
    )
    stale = UniverseRecord(
        ticker="GOOGL",
        permno=90319,
        rating="ENTER: BUY",
        action="BUY AGGRESSIVE",
        status="insufficient_history",
        reason="stale_price_endpoint",
        history_obs=2516,
        latest_price_date="2024-12-31",
    )

    result = build_optimizer_universe(
        pd.DataFrame(columns=["Ticker", "Rating", "Action"]),
        {},
        pd.DataFrame(),
    )
    result = type(result)(
        included=(),
        excluded=(missing, stale),
        missing_mappings=(),
        insufficient_history=(missing, stale),
        policy_summary={},
    )

    split = split_history_readiness(result.insufficient_history)
    summary = optimizer_universe_health_summary(result)

    assert [record.ticker for record in split["missing_history"]] == ["RBRK"]
    assert [record.ticker for record in split["stale_endpoint"]] == ["GOOGL"]
    assert summary["insufficient_history"] == 2
    assert summary["missing_history"] == 1
    assert summary["stale_endpoint"] == 1
    assert summary["missing_history_tickers"] == ["RBRK"]
    assert summary["stale_endpoint_tickers"] == ["GOOGL"]


def test_optimizer_universe_reuses_supplied_freshness_snapshot(monkeypatch) -> None:
    from core.data_orchestrator import build_price_endpoint_freshness
    import strategies.portfolio_universe as portfolio_universe

    scan = pd.DataFrame(
        [
            {"Ticker": "AAA", "Rating": "ENTER: BUY", "Action": "BUY AGGRESSIVE"},
            {"Ticker": "BBB", "Rating": "ENTER: BUY", "Action": "BUY AGGRESSIVE"},
        ]
    )
    prices = pd.DataFrame(
        {
            1: [10.0, 11.0, 12.0],
            2: [20.0, 21.0, 22.0],
        },
        index=pd.to_datetime(["2026-05-01", "2026-05-02", "2026-05-03"]),
    )
    freshness = build_price_endpoint_freshness(prices)
    monkeypatch.setattr(
        portfolio_universe,
        "build_price_endpoint_freshness",
        lambda *_args, **_kwargs: pytest.fail("dashboard-supplied freshness should be reused"),
    )

    result = build_optimizer_universe(
        scan,
        {1: "AAA", 2: "BBB"},
        prices,
        price_freshness=freshness,
    )

    assert result.included_tickers == ["AAA", "BBB"]


def test_endpoint_freshness_uses_universe_policy_tolerance() -> None:
    scan = pd.DataFrame(
        [
            {"Ticker": "AAA", "Rating": "ENTER: BUY", "Action": "BUY AGGRESSIVE"},
            {"Ticker": "BBB", "Rating": "ENTER: BUY", "Action": "BUY AGGRESSIVE"},
        ]
    )
    prices = pd.DataFrame(
        {
            1: [10.0, 11.0, 12.0, None],
            2: [20.0, 21.0, 22.0, 23.0],
        },
        index=pd.to_datetime(["2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04"]),
    )

    strict_policy = OptimizerUniversePolicy(max_endpoint_staleness_days=0)
    tolerant_policy = OptimizerUniversePolicy(max_endpoint_staleness_days=1)

    strict = build_optimizer_universe(scan, {1: "AAA", 2: "BBB"}, prices, policy=strict_policy)
    tolerant = build_optimizer_universe(scan, {1: "AAA", 2: "BBB"}, prices, policy=tolerant_policy)

    assert strict.included_tickers == ["BBB"]
    assert {record.ticker: record.reason for record in strict.insufficient_history}["AAA"] == "stale_price_endpoint"
    assert tolerant.included_tickers == ["AAA", "BBB"]


def test_portfolio_universe_uses_shared_endpoint_freshness_contract() -> None:
    source = Path("strategies/portfolio_universe.py").read_text(encoding="utf-8")

    assert "from core.data_orchestrator import build_price_endpoint_freshness" in source
    assert "from core.data_orchestrator import price_column_latest_date" in source
    assert "from core.data_orchestrator import price_endpoint_is_fresh" in source
    assert "from core.data_orchestrator import price_frame_latest_date" in source
    assert "def _price_endpoint_date(" not in source
    assert "def _latest_endpoint_date(" not in source
    assert "def _price_endpoint_is_fresh(" not in source


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
    assert "Rule of 100" in method_values
    assert DEFAULT_OPTIMIZATION_METHOD is OptimizationMethod.RULE_OF_100
    assert "Thesis-Neutral Max Sharpe" in method_values
    assert OptimizationMethod.RULE_OF_100.is_mean_variance is False
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


def test_allocation_table_returns_cash_only_for_zero_holdings() -> None:
    from views.optimizer_view import _build_allocation_table

    prices = pd.DataFrame(
        {1: [10.0, 11.0], 2: [20.0, 21.0]},
        index=pd.date_range("2026-01-01", periods=2),
    )
    weights = pd.Series({1: 0.0, 2: 0.0})

    table = _build_allocation_table(
        prices_selected=prices,
        weights=weights,
        ticker_map={1: "AAA", 2: "BBB"},
        sector_map={1: "Tech", 2: "Health"},
        portfolio_value=1_000.0,
    )

    assert table.shape[0] == 1
    assert table["ticker"].iloc[0] == "CASH"
    assert float(table["weight"].iloc[0]) == 1.0
    assert abs(float(table["allocation_usd"].iloc[0]) - 1_000.0) < 1e-9


def test_optimizer_failure_paths_clear_session_weights() -> None:
    from views.optimizer_view import _clear_optimizer_session_weights
    import views.optimizer_view as optimizer_view

    optimizer_view.st.session_state["optimizer_weights"] = {1: 0.5}
    optimizer_view.st.session_state["optimizer_price_latest_date"] = "2026-01-02"
    optimizer_view.st.session_state["optimizer_cash_only"] = True

    _clear_optimizer_session_weights()

    assert optimizer_view.st.session_state["optimizer_weights"] == {}
    assert optimizer_view.st.session_state["optimizer_price_latest_date"] == ""
    assert optimizer_view.st.session_state["optimizer_cash_only"] is False


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
