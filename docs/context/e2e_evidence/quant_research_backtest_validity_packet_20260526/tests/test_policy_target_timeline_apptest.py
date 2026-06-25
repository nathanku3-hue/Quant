"""AppTest-level regressions for real dashboard Strategy Replay rendering."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest


HISTORY_PATH = Path("data/processed/rule100_softmax_v1_history.csv")


@pytest.fixture(scope="module")
def dashboard_app():
    if not HISTORY_PATH.exists():
        pytest.skip("rule100_softmax_v1_history.csv not built yet")

    app = AppTest.from_file("dashboard.py")
    app.query_params["page"] = "portfolio-and-allocation"
    app = app.run(timeout=120)

    assert not app.exception, f"Dashboard AppTest raised: {app.exception}"
    return app


def _dataframe_values(app) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    for df_element in app.dataframe:
        value = df_element.value
        if isinstance(value, pd.DataFrame):
            frames.append(value)
    return frames


class TestRealDashboardPolicyTarget:
    """P2: dashboard.py must render Strategy Replay with PIT build_strategy_replay output."""

    def test_portfolio_route_renders_real_dashboard(self, dashboard_app):
        assert any(header.value == "Portfolio & Allocation" for header in dashboard_app.header)
        assert any(
            "Strategy Replay" in subheader.value
            for subheader in dashboard_app.subheader
        )

    def test_replay_snapshot_rendered_with_ticker_and_replay_weight(self, dashboard_app):
        """Strategy Replay Latest Snapshot must render replay-specific weight labels."""
        found_snapshot = False
        for df in _dataframe_values(dashboard_app):
            if not {"Ticker", "Replay Weight"}.issubset(df.columns):
                continue
            # Must include CASH or at least have weight data
            if df["Replay Weight"].dtype == object:
                continue
            found_snapshot = True
            break

        assert found_snapshot, "Strategy Replay Latest Snapshot dataframe not rendered"

    def test_replay_snapshot_includes_cash(self, dashboard_app):
        """CASH must appear in replay output."""
        found_cash = False
        for df in _dataframe_values(dashboard_app):
            if "Ticker" not in df.columns:
                continue
            tickers = df["Ticker"].astype(str).str.upper().str.strip()
            if "CASH" in tickers.values:
                found_cash = True
                break

        assert found_cash, "CASH not found in any replay dataframe"


class TestRealDashboardReplaySource:
    """P2: Strategy Replay source label must include method and max_weight."""

    def test_replay_source_label_rendered(self, dashboard_app):
        """Replaying caption with method and max_weight must be rendered."""
        found_source = False
        for caption in dashboard_app.caption:
            if "Replaying:" in caption.value and "max_weight=" in caption.value:
                found_source = True
                break
        assert found_source, "Strategy Replay source label not rendered"


def test_dashboard_replay_source_uses_pit_loader_not_raw_price_frame():
    """Regression: replay integration must consume per-date StrategyReplayInputs via input_loader."""
    source = Path("dashboard.py").read_text(encoding="utf-8")
    start = source.index("def _build_dashboard_strategy_replay_context(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "_load_dashboard_strategy_replay_inputs_cached(" in fn_source
    assert "input_loader=_dashboard_input_loader" in fn_source
    request_start = source.index("def _build_dashboard_replay_request(")
    request_next = source.index("\ndef _valid_cached_ytd_replay_context", request_start + 1)
    request_source = source[request_start:request_next]
    assert 'if "pytest" in sys.modules:' in request_source
    assert "prices=replay_prices" not in fn_source
    assert "if replay_inputs.prices.empty:" not in fn_source
    assert "_read_dashboard_saved_replay_artifact(request)" in fn_source


def test_dashboard_replay_surface_uses_shared_context_for_annotations_and_decisions():
    """Replay render path must not read lifecycle/buy-sell sources directly."""
    source = Path("dashboard.py").read_text(encoding="utf-8")
    start = source.index("def _render_strategy_replay_section(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "full_context" in fn_source
    assert "read_lifecycle_log(" not in fn_source
    assert "portfolio_lifecycle_buy_sell_log.jsonl" not in fn_source
    # Annotation fallback surfaces must not exist (UI unification)
    assert "_render_buy_sell_decision_log(" not in fn_source
    assert "annotation overlay" not in fn_source


class TestV11NotPromoted:
    """P2: v1.1 must not appear as promoted runtime policy."""

    def test_dashboard_lifecycle_section_does_not_source_v1_1(self):
        source = Path("dashboard.py").read_text(encoding="utf-8")
        start = source.index("def _render_strategy_replay_section(")
        ledger_start = source.index("def _render_event_ledger_chart(", start)
        next_def = source.index("\ndef ", ledger_start + 1)
        section_source = source[start:next_def]

        assert "v1_1_history" not in section_source
        assert "softmax_v1_1" not in section_source
