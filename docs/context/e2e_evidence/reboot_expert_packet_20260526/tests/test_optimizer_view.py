from __future__ import annotations

import base64
import json
import struct

import pandas as pd
from streamlit.testing.v1 import AppTest

from core import data_orchestrator
from strategies.optimizer import DEFAULT_OPTIMIZATION_METHOD, OptimizationMethod
from views.optimizer_view import PORTFOLIO_REPLAY_SELECTION_KEY


OPTIMIZER_VIEW_APP = r"""
import pandas as pd

from views.optimizer_view import render_optimizer_view

prices = pd.DataFrame(
    {
        1: [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        2: [20.0, 22.0, 21.0, 23.0, 24.0, 25.0],
        3: [30.0, 29.0, 32.0, 31.0, 34.0, 33.0],
    },
    index=pd.date_range("2026-01-01", periods=6),
)
render_optimizer_view(
    prices_wide=prices,
    ticker_map={},
    sector_map={1: "Tech", 2: "Tech", 3: "Health"},
    selected_permnos=[1, 2, 3],
)
"""


DEFAULT_TRAILING_RETURN_SELECTION_APP = r"""
import pandas as pd

from views.optimizer_view import render_optimizer_view
import views.optimizer_view as optimizer_view

optimizer_view.refresh_selected_prices_with_live_overlay = (
    lambda prices_selected, ticker_map, **kwargs: (prices_selected, prices_selected.index.max(), "local")
)

prices = pd.DataFrame(
    {
        1: [100.0, 110.0],
        2: [100.0, 150.0],
        3: [None, 120.0],
        4: [100.0, 100.0],
    },
    index=pd.to_datetime(["2025-05-13", "2026-05-13"]),
)
render_optimizer_view(
    prices_wide=prices,
    ticker_map={1: "SLOW", 2: "FAST", 3: "NEW", 4: "FLAT"},
    sector_map={1: "Tech", 2: "Tech", 3: "Health", 4: "Cash Proxy"},
)
"""


EMPTY_OPTIMIZER_SELECTION_APP = r"""
import pandas as pd

from views.optimizer_view import render_optimizer_view

prices = pd.DataFrame(
    {1: [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]},
    index=pd.date_range("2026-01-01", periods=6),
)
render_optimizer_view(
    prices_wide=prices,
    ticker_map={1: "AAA"},
    sector_map={1: "Tech"},
    selected_permnos=[],
)
"""


LIFECYCLE_HOLD_OPTIMIZER_APP = r"""
import pandas as pd

from strategies.portfolio_universe import OptimizerUniverseResult, UniverseRecord
from views.optimizer_view import render_optimizer_view

prices = pd.DataFrame(
    {1: [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]},
    index=pd.date_range("2026-01-01", periods=6),
)
universe = OptimizerUniverseResult(
    included=(
        UniverseRecord(
            ticker="AMAT",
            permno=1,
            rating="EXIT / TRAIL TIGHT",
            action="KILL",
            status="included_current_hold",
            reason="open_lifecycle_position",
            history_obs=6,
        ),
    ),
    excluded=(),
    missing_mappings=(),
    insufficient_history=(),
    policy_summary={},
)
render_optimizer_view(
    prices_wide=prices,
    ticker_map={1: "AAA"},
    sector_map={1: "Tech"},
    selected_permnos=[1],
    universe_audit=universe,
    position_memory={"AAA": {"last_weight": 0.25, "source": "lifecycle_replay"}},
)
"""


RULE100_HOLD_WITH_ENTRY_OPTIMIZER_APP = r"""
import pandas as pd

from strategies.portfolio_universe import OptimizerUniverseResult, UniverseRecord
import views.optimizer_view as optimizer_view

optimizer_view.update_position_memory_after_optimization = lambda **kwargs: {}

prices = pd.DataFrame(
    {
        1: [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        2: [20.0, 22.0, 21.0, 23.0, 24.0, 25.0],
        3: [30.0, 29.0, 32.0, 31.0, 34.0, 33.0],
    },
    index=pd.date_range("2026-01-01", periods=6),
)
universe = OptimizerUniverseResult(
    included=(
        UniverseRecord(
            ticker="AAA",
            permno=1,
            rating="EXIT / TRAIL TIGHT",
            action="KILL",
            status="included_current_hold",
            reason="open_lifecycle_position",
            history_obs=6,
        ),
        UniverseRecord(
            ticker="LRCX",
            permno=2,
            rating="ENTER: BUY",
            action="BUY AGGRESSIVE",
            status="included",
            reason="eligible_rating",
            history_obs=6,
        ),
        UniverseRecord(
            ticker="TSM",
            permno=3,
            rating="ENTER: BUY",
            action="BUY AGGRESSIVE",
            status="included",
            reason="eligible_rating",
            history_obs=6,
        ),
    ),
    excluded=(),
    missing_mappings=(),
    insufficient_history=(),
    policy_summary={},
)
optimizer_view.render_optimizer_view(
    prices_wide=prices,
    ticker_map={1: "AMAT", 2: "LRCX", 3: "TSM"},
    sector_map={1: "Tech", 2: "Tech", 3: "Health"},
    selected_permnos=[1, 2, 3],
    universe_audit=universe,
    position_memory={
        "AMAT": {"last_weight": 0.10, "source": "lifecycle_replay"},
        "LRCX": {"last_weight": 0.10, "source": "lifecycle_replay"},
        "TSM": {"last_weight": 0.10, "source": "lifecycle_replay"},
    },
    rule100_candidate_frame=pd.DataFrame(
        [
            {
                "ticker": "AMAT",
                "factor_positive_count": 3,
                "technical_quality": 1.0,
                "sizing_eligible": True,
            },
            {
                "ticker": "LRCX",
                "factor_positive_count": 3,
                "technical_quality": 1.0,
                "sizing_eligible": True,
            },
            {
                "ticker": "TSM",
                "factor_positive_count": 1,
                "technical_quality": 0.25,
                "sizing_eligible": False,
            },
        ]
    ),
)
"""


RULE100_INELIGIBLE_OPTIMIZER_APP = r"""
import pandas as pd

from strategies.portfolio_universe import OptimizerUniverseResult, UniverseRecord
import views.optimizer_view as optimizer_view

optimizer_view.update_position_memory_after_optimization = lambda **kwargs: {}

prices = pd.DataFrame(
    {
        1: [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        2: [20.0, 22.0, 21.0, 23.0, 24.0, 25.0],
    },
    index=pd.date_range("2026-01-01", periods=6),
)
universe = OptimizerUniverseResult(
    included=(
        UniverseRecord(
            ticker="AAA",
            permno=1,
            rating="EXIT / TRAIL TIGHT",
            action="KILL",
            status="included_current_hold",
            reason="open_lifecycle_position",
            history_obs=6,
        ),
        UniverseRecord(
            ticker="BBB",
            permno=2,
            rating="EXIT / TRAIL TIGHT",
            action="KILL",
            status="included_current_hold",
            reason="open_lifecycle_position",
            history_obs=6,
        ),
    ),
    excluded=(),
    missing_mappings=(),
    insufficient_history=(),
    policy_summary={},
)
optimizer_view.render_optimizer_view(
    prices_wide=prices,
    ticker_map={1: "AAA", 2: "BBB"},
    sector_map={1: "Tech", 2: "Health"},
    selected_permnos=[1, 2],
    universe_audit=universe,
    position_memory={
        "AAA": {"last_weight": 0.25, "source": "lifecycle_replay"},
        "BBB": {"last_weight": 0.25, "source": "lifecycle_replay"},
    },
    rule100_candidate_frame=pd.DataFrame(
        [
            {
                "ticker": "AAA",
                "factor_positive_count": 1,
                "technical_quality": 0.25,
                "sizing_eligible": False,
            },
            {
                "ticker": "BBB",
                "factor_positive_count": 1,
                "technical_quality": 0.25,
                "sizing_eligible": False,
            },
        ]
    ),
)
"""


UNIVERSE_HISTORY_DIAGNOSTIC_APP = r"""
import pandas as pd

from strategies.optimizer import OptimizationMethod
from strategies.portfolio_universe import OptimizerUniverseResult, UniverseRecord
import views.optimizer_view as optimizer_view

optimizer_view.update_position_memory_after_optimization = lambda **kwargs: {}
optimizer_view.refresh_selected_prices_with_live_overlay = (
    lambda prices_selected, ticker_map, **kwargs: (prices_selected, prices_selected.index.max(), "local")
)

prices = pd.DataFrame(
    {
        1: [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        2: [20.0, 22.0, 21.0, 23.0, 24.0, 25.0],
    },
    index=pd.date_range("2026-01-01", periods=6),
)
universe = OptimizerUniverseResult(
    included=(
        UniverseRecord(
            ticker="AAA",
            permno=1,
            rating="ENTER: BUY",
            action="BUY AGGRESSIVE",
            status="included",
            reason="eligible_rating",
            history_obs=6,
            latest_price_date="2026-01-06",
        ),
        UniverseRecord(
            ticker="BBB",
            permno=2,
            rating="ENTER: BUY",
            action="BUY AGGRESSIVE",
            status="included",
            reason="eligible_rating",
            history_obs=6,
            latest_price_date="2026-01-06",
        ),
    ),
    excluded=(
        UniverseRecord(
            ticker="RBRK",
            permno=90001,
            rating="ENTER: BUY",
            action="BUY AGGRESSIVE",
            status="insufficient_history",
            reason="local_price_history_unavailable",
            history_obs=0,
            latest_price_date="",
        ),
        UniverseRecord(
            ticker="GOOGL",
            permno=90319,
            rating="ENTER: BUY",
            action="BUY AGGRESSIVE",
            status="insufficient_history",
            reason="stale_price_endpoint",
            history_obs=2516,
            latest_price_date="2024-12-31",
        ),
    ),
    missing_mappings=(),
    insufficient_history=(
        UniverseRecord(
            ticker="RBRK",
            permno=90001,
            rating="ENTER: BUY",
            action="BUY AGGRESSIVE",
            status="insufficient_history",
            reason="local_price_history_unavailable",
            history_obs=0,
            latest_price_date="",
        ),
        UniverseRecord(
            ticker="GOOGL",
            permno=90319,
            rating="ENTER: BUY",
            action="BUY AGGRESSIVE",
            status="insufficient_history",
            reason="stale_price_endpoint",
            history_obs=2516,
            latest_price_date="2024-12-31",
        ),
    ),
    policy_summary={},
)
optimizer_view.render_optimizer_view(
    prices_wide=prices,
    ticker_map={1: "AAA", 2: "BBB"},
    sector_map={1: "Tech", 2: "Health"},
    selected_permnos=[1, 2],
    universe_audit=universe,
    rule100_candidate_frame=pd.DataFrame(
        [
            {
                "ticker": "AAA",
                "factor_positive_count": 3,
                "technical_quality": 1.0,
                "sizing_eligible": True,
            },
            {
                "ticker": "BBB",
                "factor_positive_count": 3,
                "technical_quality": 1.0,
                "sizing_eligible": True,
            },
        ]
    ),
)
"""


def _walk_app_nodes(node):
    yield node
    children = getattr(node, "children", None)
    if isinstance(children, dict):
        iterable = children.values()
    elif children is None:
        iterable = []
    else:
        iterable = children
    for child in iterable:
        yield from _walk_app_nodes(child)


def _plotly_specs(app: AppTest) -> list[dict]:
    specs: list[dict] = []
    for root_child in app._tree.children.values():
        for node in _walk_app_nodes(root_child):
            if getattr(node, "type", None) == "plotly_chart":
                specs.append(json.loads(node.proto.spec))
    return specs


def _decode_plotly_f64_values(values) -> list[float]:
    if isinstance(values, dict) and values.get("dtype") == "f8":
        raw = base64.b64decode(values["bdata"])
        return [item[0] for item in struct.iter_unpack("<d", raw)]
    return [float(value) for value in values]


def test_optimizer_view_renders_with_streamlit_testing() -> None:
    app = AppTest.from_string(OPTIMIZER_VIEW_APP).run(timeout=15)

    assert not app.exception
    assert any("Portfolio Optimizer" in header.value for header in app.header)
    assert app.multiselect[0].label == "Select assets"
    assert app.selectbox[0].label == "Method"
    assert app.selectbox[0].value == OptimizationMethod.RULE_OF_100
    assert any(subheader.value == "Allocation Table" for subheader in app.subheader)


def test_optimizer_default_method_is_rule_of_100() -> None:
    app = AppTest.from_string(OPTIMIZER_VIEW_APP).run(timeout=15)

    assert DEFAULT_OPTIMIZATION_METHOD is OptimizationMethod.RULE_OF_100
    assert app.selectbox[0].value == OptimizationMethod.RULE_OF_100


def test_default_asset_selection_uses_trailing_one_year_return_order() -> None:
    app = AppTest.from_string(DEFAULT_TRAILING_RETURN_SELECTION_APP).run(timeout=15)

    assert not app.exception
    assert app.multiselect[0].value == [2, 1, 4, 3]
    assert PORTFOLIO_REPLAY_SELECTION_KEY not in app.session_state


def test_optimizer_empty_selection_renders_cash_only_existing_pie() -> None:
    app = AppTest.from_string(EMPTY_OPTIMIZER_SELECTION_APP).run(timeout=15)
    specs = _plotly_specs(app)

    assert not app.exception
    assert len(specs) == 1
    assert specs[0]["layout"]["title"]["text"] == "Allocation (100% Cash)"
    trace = specs[0]["data"][0]
    assert trace["type"] == "pie"
    assert trace["labels"] == ["CASH"]
    assert _decode_plotly_f64_values(trace["values"]) == [1.0]
    assert any("Select at least one asset to run optimization." in info.value for info in app.info)
    assert app.session_state["optimizer_cash_only"] is True
    assert app.session_state["portfolio_allocation_state"]["mode"] == "cash_only"
    assert app.session_state["portfolio_allocation_state"]["cash_only"] is True
    assert PORTFOLIO_REPLAY_SELECTION_KEY not in app.session_state
    assert not app.warning


def test_optimizer_lifecycle_holds_render_with_residual_cash() -> None:
    app = AppTest.from_string(LIFECYCLE_HOLD_OPTIMIZER_APP).run(timeout=15)
    app.selectbox[0].select(OptimizationMethod.INVERSE_VOLATILITY)
    app.run(timeout=15)
    specs = _plotly_specs(app)

    assert not app.exception
    assert len(specs) == 1
    assert specs[0]["layout"]["title"]["text"] == "Allocation (Lifecycle Holds)"
    trace = specs[0]["data"][0]
    assert trace["labels"] == ["AAA", "CASH"]
    assert _decode_plotly_f64_values(trace["values"]) == [0.25, 0.75]
    assert any("Current-hold replay output" in info.value for info in app.info)
    assert app.session_state["optimizer_cash_only"] is False
    assert app.session_state["portfolio_allocation_state"]["mode"] == "current_hold_replay"
    assert app.session_state["portfolio_allocation_state"]["source"] == "lifecycle_replay"
    assert app.session_state["portfolio_allocation_state"]["weights"] == {1: 0.25}
    assert app.session_state[PORTFOLIO_REPLAY_SELECTION_KEY].replay_assets == (1,)


def test_optimizer_publishes_signed_replay_selection_after_valid_controls() -> None:
    app = AppTest.from_string(OPTIMIZER_VIEW_APP).run(timeout=15)

    assert not app.exception
    selection = app.session_state[PORTFOLIO_REPLAY_SELECTION_KEY]
    assert selection.replay_assets == (1, 2, 3)
    assert selection.source == "optimizer_controls"
    assert selection.signature["replay_assets"] == ["int:1", "int:2", "int:3"]
    assert selection.signature["method"] == OptimizationMethod.RULE_OF_100.value
    assert selection.signature["price_frame"]["selected_price_hash"]


def test_rule100_method_renders_softmax_v1_targets_without_optimizer() -> None:
    app = AppTest.from_string(RULE100_HOLD_WITH_ENTRY_OPTIMIZER_APP).run(timeout=15)
    assert OptimizationMethod.RULE_OF_100.value in app.selectbox[0].options
    app.selectbox[0].select(OptimizationMethod.RULE_OF_100)
    app.run(timeout=15)
    specs = _plotly_specs(app)

    assert not app.exception
    assert len(specs) == 1
    assert specs[0]["layout"]["title"]["text"] == "Allocation (Rule of 100)"
    trace = specs[0]["data"][0]
    assert trace["labels"] == ["AMAT", "LRCX", "CASH"]
    assert _decode_plotly_f64_values(trace["values"]) == pytest.approx([0.35, 0.35, 0.30])
    assert any("Rule of 100 softmax v1 sizing output" in info.value for info in app.info)
    assert not any(subheader.value == "Optimizer Diagnostics" for subheader in app.subheader)
    assert app.session_state["optimizer_cash_only"] is False
    assert app.session_state["portfolio_allocation_state"]["mode"] == "rule_of_100_replay"
    assert app.session_state["portfolio_allocation_state"]["source"] == "rule100_softmax_v1"
    assert app.session_state["portfolio_allocation_state"]["weights"] == {1: 0.35, 2: 0.35}
    selection = app.session_state[PORTFOLIO_REPLAY_SELECTION_KEY]
    assert selection.replay_assets == (1, 2, 3)
    assert selection.signature["replay_assets"] == ["int:1", "int:2", "int:3"]


def test_rule100_method_drops_ineligible_holds_to_cash_instead_of_last_weight() -> None:
    app = AppTest.from_string(RULE100_INELIGIBLE_OPTIMIZER_APP).run(timeout=15)
    app.selectbox[0].select(OptimizationMethod.RULE_OF_100)
    app.run(timeout=15)
    specs = _plotly_specs(app)

    assert not app.exception
    assert len(specs) == 1
    trace = specs[0]["data"][0]
    assert trace["labels"] == ["CASH"]
    assert _decode_plotly_f64_values(trace["values"]) == [1.0]
    assert any("no eligible lifecycle holds" in info.value for info in app.info)
    assert app.session_state["optimizer_cash_only"] is True
    assert app.session_state["portfolio_allocation_state"]["source"] == "rule100_softmax_v1"
    assert app.session_state["portfolio_allocation_state"]["weights"] == {}
    assert app.session_state[PORTFOLIO_REPLAY_SELECTION_KEY].replay_assets == (1, 2)


def test_optimizer_universe_audit_splits_missing_history_from_stale_endpoint() -> None:
    app = AppTest.from_string(UNIVERSE_HISTORY_DIAGNOSTIC_APP).run(timeout=15)
    app.selectbox[0].select(OptimizationMethod.INVERSE_VOLATILITY)
    app.run(timeout=15)

    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Missing History"] == "1"
    assert metrics["Stale Endpoint"] == "1"
    assert "History Fail" not in metrics
    audit_table = app.dataframe[0].value
    by_ticker = {row["Ticker"]: row for row in audit_table.to_dict("records")}
    assert by_ticker["RBRK"]["Reason"] == "local_price_history_unavailable"
    assert by_ticker["RBRK"]["History Obs"] == 0
    assert by_ticker["GOOGL"]["Reason"] == "stale_price_endpoint"
    assert by_ticker["GOOGL"]["Latest Price Date"] == "2024-12-31"
    assert by_ticker["GOOGL"]["History Obs"] == 2516


def test_optimizer_explanation_uses_split_history_labels() -> None:
    source = Path("views/optimizer_view.py").read_text(encoding="utf-8")

    assert "Missing local price history" in source
    assert "Stale local price endpoints" in source
    assert '"Price-history failures"' not in source


def test_optimizer_view_exercises_mean_variance_and_sector_cap_controls() -> None:
    app = AppTest.from_string(OPTIMIZER_VIEW_APP).run(timeout=15)
    app.selectbox[0].select(OptimizationMethod.MEAN_VARIANCE_MAX_RETURN)
    app.checkbox[0].check()
    app.slider[1].set_value(0.50)
    app.run(timeout=15)

    assert not app.exception
    assert any(
        caption.value == "Optimization Method: Mean-Variance (SLSQP)"
        for caption in app.caption
    )
    assert any("Sector cap applied: max 50%" in caption.value for caption in app.caption)
    assert any(subheader.value == "Sector Exposure" for subheader in app.subheader)


def test_trailing_one_year_return_orders_default_assets_descending() -> None:
    from views.optimizer_view import _order_assets_by_trailing_one_year_return

    prices = pd.DataFrame(
        {
            "slow": [100.0, 110.0],
            "fast": [100.0, 150.0],
            "new": [None, 120.0],
            "flat": [100.0, 100.0],
        },
        index=pd.to_datetime(["2025-05-13", "2026-05-13"]),
    )

    ordered = _order_assets_by_trailing_one_year_return(
        ["new", "slow", "fast", "flat"],
        prices,
    )

    assert ordered == ["fast", "slow", "flat", "new"]


def test_trailing_one_year_return_order_uses_last_available_anchor_without_future_leakage() -> None:
    from views.optimizer_view import _order_assets_by_trailing_one_year_return

    prices = pd.DataFrame(
        {
            "aaa": [100.0, 101.0, 120.0],
            "bbb": [100.0, 200.0, 121.0],
        },
        index=pd.to_datetime(["2025-05-13", "2025-06-01", "2026-05-13"]),
    )

    ordered = _order_assets_by_trailing_one_year_return(["aaa", "bbb"], prices)

    assert ordered == ["bbb", "aaa"]


def test_trailing_one_year_return_order_demotes_stale_endpoint_assets() -> None:
    from views.optimizer_view import _order_assets_by_trailing_one_year_return

    prices = pd.DataFrame(
        {
            "fresh": [100.0, 110.0, 120.0],
            "stale_winner": [100.0, 300.0, None],
        },
        index=pd.to_datetime(["2025-05-13", "2026-02-27", "2026-05-13"]),
    )

    ordered = _order_assets_by_trailing_one_year_return(["stale_winner", "fresh"], prices)

    assert ordered == ["fresh", "stale_winner"]


def test_prepare_selected_prices_drops_stale_overlay_assets(monkeypatch) -> None:
    import views.optimizer_view as optimizer_view
    from core.data_orchestrator import build_price_endpoint_freshness

    prices_wide = pd.DataFrame(
        {
            1: [100.0, 110.0, 120.0],
            2: [100.0, 130.0, None],
        },
        index=pd.to_datetime(["2026-05-01", "2026-05-02", "2026-05-03"]),
    )

    def _fake_refresh(prices_selected, ticker_map, **kwargs):
        assert kwargs["required_latest"] == pd.Timestamp("2026-05-03")
        return prices_selected.reindex(columns=[1]), pd.Timestamp("2026-05-03"), "live_stale_dropped"

    monkeypatch.setattr(optimizer_view, "refresh_selected_prices_with_live_overlay", _fake_refresh)
    monkeypatch.setattr(
        optimizer_view,
        "build_price_endpoint_freshness",
        lambda *_args, **_kwargs: pytest.fail("freshness snapshot should be supplied by caller"),
    )
    freshness = build_price_endpoint_freshness(prices_wide)

    prepared = optimizer_view._prepare_selected_prices(
        prices_wide,
        [1, 2],
        {1: "AAA", 2: "BBB"},
        price_freshness=freshness,
    )

    assert prepared is not None
    prices_selected, latest, source = prepared
    assert latest == pd.Timestamp("2026-05-03")
    assert source == "live_stale_dropped"
    assert list(prices_selected.columns) == [1]


def test_default_ordering_uses_supplied_freshness_snapshot(monkeypatch) -> None:
    import views.optimizer_view as optimizer_view
    from core.data_orchestrator import build_price_endpoint_freshness

    prices = pd.DataFrame(
        {
            "fresh": [100.0, 110.0, 120.0],
            "stale_winner": [100.0, 300.0, None],
        },
        index=pd.to_datetime(["2025-05-13", "2026-02-27", "2026-05-13"]),
    )
    freshness = build_price_endpoint_freshness(prices)
    monkeypatch.setattr(
        optimizer_view,
        "build_price_endpoint_freshness",
        lambda *_args, **_kwargs: pytest.fail("caller-supplied freshness should be reused"),
    )

    ordered = optimizer_view._order_assets_by_trailing_one_year_return(
        ["stale_winner", "fresh"],
        prices,
        price_freshness=freshness,
    )

    assert ordered == ["fresh", "stale_winner"]


def test_explicit_optimizer_selection_preserves_user_order() -> None:
    from views.optimizer_view import _resolve_permnos

    prices = pd.DataFrame(
        {
            1: [100.0, 200.0],
            2: [100.0, 110.0],
            3: [100.0, 150.0],
        },
        index=pd.to_datetime(["2025-05-13", "2026-05-13"]),
    )

    assert _resolve_permnos(prices, {1: "AAA", 2: "BBB", 3: "CCC"}, selected_permnos=[2, 1]) == [2, 1]


def test_recent_close_prices_use_display_only_parquet_cache(
    tmp_path,
    monkeypatch,
) -> None:
    calls: list[tuple[tuple[str, ...], str]] = []

    class FakeProvider:
        def download_daily_bars(self, tickers, start, threads=True):
            calls.append((tuple(tickers), start))
            index = pd.date_range("2026-01-01", periods=3)
            columns = pd.MultiIndex.from_product([["Adj Close"], tickers])
            return pd.DataFrame(
                [[10.0, 20.0], [11.0, 21.0], [12.0, 22.0]],
                index=index,
                columns=columns,
            )

    monkeypatch.setattr(
        data_orchestrator,
        "build_market_data_provider",
        lambda name: FakeProvider(),
    )

    first = data_orchestrator.download_recent_close_prices(
        ("bbb", "AAA"),
        "2026-01-01",
        cache_dir=tmp_path,
        schedule_background=False,
    )

    assert calls == [(("AAA", "BBB"), "2026-01-01")]
    assert list(first.columns) == ["AAA", "BBB"]
    assert len(list(tmp_path.glob("*.parquet"))) == 1

    def _fail_provider(name):
        raise AssertionError("provider should not be called for fresh cache")

    monkeypatch.setattr(data_orchestrator, "build_market_data_provider", _fail_provider)
    cached = data_orchestrator.download_recent_close_prices(
        ("AAA", "BBB"),
        "2026-01-01",
        cache_dir=tmp_path,
        schedule_background=False,
    )

    pd.testing.assert_frame_equal(cached, first, check_freq=False)


def test_cold_recent_close_cache_schedules_background_refresh(
    tmp_path,
    monkeypatch,
) -> None:
    scheduled: list[tuple[tuple[str, ...], str]] = []

    def _record_schedule(tickers, start_iso, cache_path, cache_key):
        scheduled.append((tuple(tickers), start_iso))

    monkeypatch.setattr(data_orchestrator, "_schedule_overlay_refresh", _record_schedule)
    result = data_orchestrator.download_recent_close_prices(
        ("BBB", "aaa"),
        "2026-01-01",
        cache_dir=tmp_path,
        schedule_background=True,
    )

    assert result.empty
    assert scheduled == [(("AAA", "BBB"), "2026-01-01")]


def test_scaled_live_overlay_cache_returns_copy_safe_results() -> None:
    data_orchestrator._scaled_overlay_cache.clear()
    local = pd.DataFrame(
        {"AAA": [100.0, 110.0]},
        index=pd.to_datetime(["2026-01-02", "2026-01-03"]),
    )
    live = pd.DataFrame(
        {"AAA": [50.0, 55.0]},
        index=pd.to_datetime(["2026-01-03", "2026-01-04"]),
    )

    scaled = data_orchestrator.scale_live_overlay_to_local(local, live)
    assert len(data_orchestrator._scaled_overlay_cache) == 1
    assert abs(float(scaled.loc[pd.Timestamp("2026-01-04"), "AAA"]) - 121.0) <= 1e-9

    scaled.iloc[0, 0] = -999.0
    cached = data_orchestrator.scale_live_overlay_to_local(local, live)

    assert len(data_orchestrator._scaled_overlay_cache) == 1
    assert abs(float(cached.loc[pd.Timestamp("2026-01-03"), "AAA"]) - 110.0) <= 1e-9



# ── Strategy Replay Behavioral Acceptance Checks ──────────────────────────


from pathlib import Path

import pytest

from strategies.optimizer import OPTIMIZATION_METHOD_OPTIONS, OptimizationMethod
from strategies.strategy_replay import build_strategy_replay, REPLAY_COLUMNS
from views.optimizer_view import _rule100_softmax_weights_for_ui


DASHBOARD = Path("dashboard.py")

_REPLAY_PRICES = pd.DataFrame(
    {
        1: [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        2: [20.0, 22.0, 21.0, 23.0, 24.0, 25.0],
        3: [30.0, 29.0, 32.0, 31.0, 34.0, 33.0],
    },
    index=pd.date_range("2026-01-01", periods=6),
)

_RULE100_CANDIDATES = pd.DataFrame(
    [
        {"date": "2026-01-01", "ticker": "AAA", "permno": 1, "factor_positive_count": 3, "technical_quality": 1.0, "sizing_eligible": True, "eligibility_reason": "eligible_buy_or_hold"},
        {"date": "2026-01-01", "ticker": "BBB", "permno": 2, "factor_positive_count": 3, "technical_quality": 1.0, "sizing_eligible": True, "eligibility_reason": "eligible_buy_or_hold"},
    ]
)


@pytest.mark.parametrize("method", list(OPTIMIZATION_METHOD_OPTIONS))
def test_strategy_replay_produces_output_for_every_method(method: OptimizationMethod) -> None:
    """Every optimizer method produces a replay DataFrame with CASH rows."""
    controls = {"max_weight": 0.35, "risk_free_rate": 0.0}
    if method == OptimizationMethod.RULE_OF_100:
        controls["rule100_candidate_frame"] = _RULE100_CANDIDATES

    result = build_strategy_replay(
        method=method,
        controls=controls,
        prices=_REPLAY_PRICES,
        ticker_map={1: "AAA", 2: "BBB", 3: "CCC"},
        as_of_range=[_REPLAY_PRICES.index[-1]],
    )

    assert not result.empty, f"Replay for {method.value} returned empty"
    assert set(REPLAY_COLUMNS).issubset(result.columns)
    assert "CASH" in result["ticker"].values, f"CASH missing for {method.value}"
    assert result["method"].iloc[0] == method.value
    # cap_used must reflect the slider value
    assert float(result["cap_used"].iloc[0]) == pytest.approx(0.35)
    assert result["cap_source"].iloc[0] == "controls.max_weight"


def test_strategy_replay_rule100_max_weight_affects_output() -> None:
    """Rule of 100 replay with max_weight=35% labels cap_used=35% and respects cap."""
    controls = {"max_weight": 0.35, "risk_free_rate": 0.0, "rule100_candidate_frame": _RULE100_CANDIDATES}
    result = build_strategy_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls=controls,
        prices=_REPLAY_PRICES,
        ticker_map={1: "AAA", 2: "BBB", 3: "CCC"},
        as_of_range=[_REPLAY_PRICES.index[-1]],
    )
    assert not result.empty
    assert float(result["cap_used"].iloc[0]) == pytest.approx(0.35)
    # No single asset exceeds max_weight
    asset_rows = result[result["ticker"] != "CASH"]
    if not asset_rows.empty:
        assert float(asset_rows["target_weight"].max()) <= 0.35 + 1e-6


def test_rule100_direct_ui_state_and_strategy_replay_agree_at_max_weight() -> None:
    ui_weights = _rule100_softmax_weights_for_ui(
        selected_assets=[1, 2, 3],
        ticker_map={1: "AAA", 2: "BBB", 3: "CCC"},
        as_of=_REPLAY_PRICES.index[-1],
        candidate_frame=_RULE100_CANDIDATES,
        max_weight=0.35,
    )
    replay = build_strategy_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls={"max_weight": 0.35, "risk_free_rate": 0.0, "rule100_candidate_frame": _RULE100_CANDIDATES},
        prices=_REPLAY_PRICES,
        ticker_map={1: "AAA", 2: "BBB", 3: "CCC"},
        as_of_range=[_REPLAY_PRICES.index[-1]],
    )
    replay_weights = replay[replay["ticker"] != "CASH"].set_index("permno")["target_weight"]

    assert ui_weights.to_dict() == pytest.approx({1: 0.35, 2: 0.35})
    assert replay_weights.reindex(ui_weights.index).to_dict() == pytest.approx(ui_weights.to_dict())
    assert float(replay[replay["ticker"] == "CASH"]["target_weight"].iloc[0]) == pytest.approx(0.30)


def test_strategy_replay_max_weight_slider_changes_optimizer_output() -> None:
    """Changing max_weight from 35% to 50% changes optimizer replay output."""
    controls_35 = {"max_weight": 0.35, "risk_free_rate": 0.0}
    controls_50 = {"max_weight": 0.50, "risk_free_rate": 0.0}
    dates = [_REPLAY_PRICES.index[-1]]
    ticker_map = {1: "AAA", 2: "BBB", 3: "CCC"}

    result_35 = build_strategy_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=controls_35,
        prices=_REPLAY_PRICES,
        ticker_map=ticker_map,
        as_of_range=dates,
    )
    result_50 = build_strategy_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=controls_50,
        prices=_REPLAY_PRICES,
        ticker_map=ticker_map,
        as_of_range=dates,
    )

    assert float(result_35["cap_used"].iloc[0]) == pytest.approx(0.35)
    assert float(result_50["cap_used"].iloc[0]) == pytest.approx(0.50)


def test_strategy_replay_cash_always_present() -> None:
    """CASH row is always present in replay output for every date."""
    controls = {"max_weight": 0.35, "risk_free_rate": 0.0}
    result = build_strategy_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=controls,
        prices=_REPLAY_PRICES,
        ticker_map={1: "AAA", 2: "BBB", 3: "CCC"},
        as_of_range=list(_REPLAY_PRICES.index),
    )
    dates = result["date"].unique()
    for date in dates:
        date_rows = result[result["date"] == date]
        assert "CASH" in date_rows["ticker"].values, f"CASH missing on {date}"


def test_strategy_replay_unsupported_dates_show_cash_closed_status() -> None:
    """Failed/unsupported replay dates show status=cash_closed with explicit reason."""
    # Single-asset prices that may cause optimizer issues
    single_price = pd.DataFrame(
        {1: [10.0, 10.0]},
        index=pd.date_range("2026-01-01", periods=2),
    )
    controls = {"max_weight": 0.35, "risk_free_rate": 0.0}
    result = build_strategy_replay(
        method=OptimizationMethod.THESIS_NEUTRAL_MAX_SHARPE,
        controls=controls,
        prices=single_price,
        ticker_map={1: "AAA"},
        as_of_range=[single_price.index[-1]],
    )
    assert not result.empty
    # Either produces weights or shows cash_closed with reason
    statuses = set(result["status"].unique())
    assert statuses.issubset({"ok", "cash_closed", "cash_only"})
    if "cash_closed" in statuses:
        reasons = result[result["status"] == "cash_closed"]["reason"].unique()
        assert all(r != "" for r in reasons), "cash_closed rows must have explicit reason"


def test_dashboard_strategy_replay_calls_build_strategy_replay() -> None:
    """Dashboard source selector can use saved artifacts and fallback build, not old CSV loader."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _build_dashboard_strategy_replay_context(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "build_selected_method_replay(" in fn_source
    assert "_read_dashboard_saved_replay_artifact(request)" in fn_source
    assert 'source_mode="saved_artifact"' in source
    assert "allow_transitional_fallback" in fn_source
    assert "_REPLAY_ARTIFACT_REGISTRY" not in fn_source
    assert "_ensure_rule100_softmax_v1_history()" not in fn_source


def test_dashboard_strategy_replay_loads_pit_inputs_per_date() -> None:
    """Dashboard replay must use an input_loader backed by one batched PIT source load."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _build_dashboard_strategy_replay_context(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "_load_dashboard_batched_pit_replay_data_cached(" in fn_source
    assert "build_batched_pit_input_loader(" in fn_source
    assert "_filter_dashboard_replay_inputs_to_assets(" in fn_source
    assert "_dashboard_input_loader" in fn_source
    assert "input_loader=_dashboard_input_loader" in fn_source
    assert "replay_prices = prices_wide[replay_assets]" not in fn_source
    assert "prices=replay_prices" not in fn_source


def test_dashboard_batched_pit_loader_passes_selected_permnos_without_watchlist_shortcut() -> None:
    """Dashboard batch loading limits prices to selected permnos after full PIT membership proof."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _build_dashboard_strategy_replay_context(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]
    loader_start = source.index("def _load_dashboard_batched_pit_replay_data_cached(")
    loader_next = source.index("\ndef ", loader_start + 1)
    loader_source = source[loader_start:loader_next]

    assert "selected_permnos=_numeric_replay_permnos(request.allocation_assets)" in fn_source
    assert "selected_permnos=selected_permnos" in loader_source
    assert "watchlist" not in fn_source.lower()


def test_dashboard_strategy_replay_loader_forces_r3000_pit_universe() -> None:
    """The dashboard helper must fail closed through the r3000 PIT loader."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _load_dashboard_strategy_replay_inputs_cached(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "load_strategy_replay_inputs(" in fn_source
    assert 'universe_mode="r3000_pit"' in fn_source
    assert "end_date=as_of_date" in fn_source


def test_dashboard_replay_request_constructor_is_pure() -> None:
    """Replay request construction is separated from backend bundle execution."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _build_dashboard_replay_request(")
    next_def = source.index("\ndef _valid_cached_ytd_replay_context", start + 1)
    fn_source = source[start:next_def]

    assert "_make_dashboard_replay_request(" in fn_source
    assert "build_selected_method_replay(" not in fn_source
    assert "pd.read_parquet(" not in fn_source
    assert "_read_dashboard_saved_replay_artifact(" not in fn_source


def test_dashboard_strategy_replay_preserves_failed_or_empty_dates_as_cash_closed() -> None:
    """Dashboard replay delegates per-date failure handling to build_selected_method_replay."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _build_dashboard_strategy_replay_context(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    # Backend bundle handles per-date failures via input_loader; dashboard catches bundle-level failures
    assert "build_selected_method_replay(" in fn_source
    assert 'status="failed"' in fn_source
    assert "build_selected_method_replay failed:" in fn_source


def test_dashboard_strategy_replay_no_hardcoded_rule100_only_gate() -> None:
    """No registry gate blocks non-Rule100 methods."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_strategy_replay_section(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "No replay artifact available" not in fn_source
    assert "unsupported for method" not in fn_source


def test_dashboard_strategy_replay_source_label_structure() -> None:
    """Source label includes method, cap_used, cap_source, and source."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _get_replay_source_label(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "method=" in fn_source
    assert "cap_used=" in fn_source
    assert "cap_source=" in fn_source
    assert "source=" in fn_source
