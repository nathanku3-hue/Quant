"""Real Streamlit AppTests for the default E0A current-decision portfolio route."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.gv_e0a_operable import publish_e0a_current_decision
from core.gv_fs0_publish import (
    DEFAULT_CURRENT_DECISION_LOCK,
    DEFAULT_CURRENT_DECISION_TARGET,
)
from views.page_registry import PORTFOLIO_PAGE_ROUTE, PORTFOLIO_PAGE_TITLE

ROOT = Path(__file__).resolve().parents[2]


def _app_status_text(app: AppTest) -> str:
    values: list[str] = []
    for group_name in ("info", "warning", "error"):
        for element in getattr(app, group_name):
            value = getattr(element, "value", "")
            if value:
                values.append(str(value))
    return "\n".join(values)


def _run_portfolio_app() -> AppTest:
    app = AppTest.from_file(str(ROOT / "dashboard.py"))
    app.query_params["page"] = PORTFOLIO_PAGE_ROUTE
    return app.run(timeout=90)


@pytest.fixture
def isolated_current_decision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point default current-decision paths at a temp location for fail-path tests."""

    target = tmp_path / "gv_fs0_current_decision.json"
    lock = tmp_path / ".gv_fs0_current_decision.lock"
    monkeypatch.setattr(
        "core.gv_fs0_publish.DEFAULT_CURRENT_DECISION_TARGET", target
    )
    monkeypatch.setattr(
        "core.gv_fs0_publish.DEFAULT_CURRENT_DECISION_LOCK", lock
    )
    monkeypatch.setattr(
        "views.gv_fs0_portfolio_adapter.DEFAULT_CURRENT_DECISION_PATH", target
    )
    monkeypatch.setattr(
        "core.gv_fs0_current_decision.DEFAULT_CURRENT_DECISION_PATH", target
    )
    return target, lock


def test_apptest_success_one_table_for_current_decision() -> None:
    """Success path: one certified portfolio table, no dual-bundle headers."""

    prior_target = (
        DEFAULT_CURRENT_DECISION_TARGET.read_bytes()
        if DEFAULT_CURRENT_DECISION_TARGET.exists()
        else None
    )
    prior_lock = (
        DEFAULT_CURRENT_DECISION_LOCK.read_bytes()
        if DEFAULT_CURRENT_DECISION_LOCK.exists()
        else None
    )
    try:
        if DEFAULT_CURRENT_DECISION_LOCK.exists():
            DEFAULT_CURRENT_DECISION_LOCK.unlink()
        publish_e0a_current_decision()
        app = _run_portfolio_app()
        assert not app.exception
        assert any(header.value == PORTFOLIO_PAGE_TITLE for header in app.header)
        assert [element.value for element in app.subheader] == [
            "GV-FS0 Certified Paper Portfolio — NO_POSITION",
        ]
        assert len(app.table) == 1
        caption_text = "\n".join(element.value for element in app.caption)
        assert "CERTIFIED" in caption_text
        assert "Certified decision unavailable" not in _app_status_text(app)
    finally:
        if prior_target is None:
            DEFAULT_CURRENT_DECISION_TARGET.unlink(missing_ok=True)
        else:
            DEFAULT_CURRENT_DECISION_TARGET.write_bytes(prior_target)
        if prior_lock is None:
            DEFAULT_CURRENT_DECISION_LOCK.unlink(missing_ok=True)
        else:
            DEFAULT_CURRENT_DECISION_LOCK.write_bytes(prior_lock)


def test_apptest_missing_current_decision_shows_unavailable(
    isolated_current_decision: tuple[Path, Path],
) -> None:
    target, _lock = isolated_current_decision
    assert not target.exists()
    app = _run_portfolio_app()
    assert not app.exception
    status = _app_status_text(app)
    assert "Certified decision unavailable" in status
    assert len(app.table) == 0
    assert not any(
        "OPEN" in str(getattr(element, "value", ""))
        for element in app.subheader
    )


def test_apptest_invalid_current_decision_shows_unavailable(
    isolated_current_decision: tuple[Path, Path],
) -> None:
    target, _lock = isolated_current_decision
    # Non-canonical / non-certified bytes must refuse authority.
    target.write_bytes(b'{"not":"a certified decision"}\n')
    app = _run_portfolio_app()
    assert not app.exception
    status = _app_status_text(app)
    assert "Certified decision unavailable" in status
    assert len(app.table) == 0
