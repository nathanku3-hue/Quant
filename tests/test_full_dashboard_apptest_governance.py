from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from streamlit.util import calc_md5

from rendered_governance import assert_rendered_governance_safe
from rendered_governance import collect_rendered_text
from views.page_registry import APPROVED_PAGE_SLUGS
from views.page_registry import APPROVED_PAGE_TITLES


DASHBOARD_PATH = Path("dashboard.py")
SIDE_EFFECT_SENTINELS = (
    Path("runtime/boot_status_current.json"),
    Path("data/last_scan_state.json"),
    Path("data/.backtest_pid"),
)


def _snapshot(paths: tuple[Path, ...]) -> dict[Path, bytes | None]:
    out: dict[Path, bytes | None] = {}
    for path in paths:
        out[path] = path.read_bytes() if path.exists() else None
    return out


def _assert_snapshot_unchanged(before: dict[Path, bytes | None]) -> None:
    after = _snapshot(tuple(before))
    assert after == before


def test_dashboard_import_has_no_top_level_runtime_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = _snapshot(SIDE_EFFECT_SENTINELS)
    calls: list[str] = []

    monkeypatch.delenv("T0_DASHBOARD_APPTEST_SAFE", raising=False)
    monkeypatch.setattr("streamlit.set_page_config", lambda *args, **kwargs: calls.append("page_config"))
    monkeypatch.setattr("streamlit.navigation", lambda *args, **kwargs: calls.append("navigation"))
    monkeypatch.setattr("streamlit.stop", lambda: (_ for _ in ()).throw(AssertionError("st.stop called")))
    monkeypatch.setattr("yfinance.download", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("provider refresh called")))

    import dashboard

    importlib.reload(dashboard)

    assert calls == []
    _assert_snapshot_unchanged(before)


def test_actual_dashboard_shell_renders_with_app_test_and_no_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = _snapshot(SIDE_EFFECT_SENTINELS)

    monkeypatch.setenv("T0_DASHBOARD_APPTEST_SAFE", "1")
    app = AppTest.from_file(str(DASHBOARD_PATH)).run(timeout=30)

    assert not app.exception
    assert_rendered_governance_safe(app)
    rendered_text = {item.text for item in collect_rendered_text(app)}

    assert "Terminal Zero GodView" in rendered_text
    assert "Portfolio & Allocation" in rendered_text
    assert "Research-only dashboard shell rendered with provider refresh disabled." in rendered_text
    assert "Command Center" not in rendered_text
    assert "Research Lab" not in rendered_text
    assert "Settings & Ops" not in rendered_text
    _assert_snapshot_unchanged(before)


def test_actual_dashboard_safe_mode_blocks_refresh_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = _snapshot(SIDE_EFFECT_SENTINELS)

    monkeypatch.setenv("T0_DASHBOARD_APPTEST_SAFE", "1")
    import dashboard

    importlib.reload(dashboard)

    with pytest.raises(RuntimeError, match="scan refresh is disabled"):
        dashboard.run_and_save_scan()

    assert dashboard.fetch_macro_score() is None
    assert dashboard.get_breadth_status()[0] == "UNKNOWN (AppTest safe)"
    assert dashboard._download_ytd_close_prices(("SPY",), "2026-01-01").empty
    _assert_snapshot_unchanged(before)


def test_actual_dashboard_portfolio_page_body_safe_mode_blocks_yfinance() -> None:
    before = _snapshot(SIDE_EFFECT_SENTINELS)
    app_source = r'''
import os

import streamlit as st
import yfinance as yf

os.environ["T0_DASHBOARD_APPTEST_SAFE"] = "1"

def _fail_download(*args, **kwargs):
    raise AssertionError("provider refresh called")

yf.download = _fail_download

import dashboard

st.set_page_config(page_title="Portfolio Safe Mode Probe")
dashboard._initialize_dashboard_state()
dashboard._render_portfolio_allocation_page()
'''

    app = AppTest.from_string(app_source).run(timeout=30)

    assert not app.exception
    assert_rendered_governance_safe(app)
    rendered_text = {item.text for item in collect_rendered_text(app)}
    assert "Portfolio & Allocation" in rendered_text
    assert "YTD Performance" in rendered_text
    _assert_snapshot_unchanged(before)


@pytest.mark.parametrize(
    ("slug", "title"),
    tuple(zip(APPROVED_PAGE_SLUGS, APPROVED_PAGE_TITLES)),
)
def test_actual_dashboard_approved_routes_render_with_governance(
    monkeypatch: pytest.MonkeyPatch,
    slug: str,
    title: str,
) -> None:
    before = _snapshot(SIDE_EFFECT_SENTINELS)

    monkeypatch.setenv("T0_DASHBOARD_APPTEST_SAFE", "1")
    app = AppTest.from_file(str(DASHBOARD_PATH))
    app._page_hash = calc_md5(slug)
    app.run(timeout=30)

    assert not app.exception
    assert_rendered_governance_safe(app)
    rendered_text = {item.text for item in collect_rendered_text(app)}
    assert title in rendered_text
    _assert_snapshot_unchanged(before)
