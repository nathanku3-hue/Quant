from __future__ import annotations

import ast
from pathlib import Path
import socket

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _page_blob(app: object) -> str:
    parts: list[str] = []
    for collection_name in (
        "header",
        "subheader",
        "caption",
        "info",
        "warning",
        "success",
        "table",
    ):
        for element in getattr(app, collection_name):
            parts.append(str(getattr(element, "value", element)))
    return "\n".join(parts)


def test_portfolio_entrypoints_have_no_provider_or_broker_imports() -> None:
    forbidden = {"alpaca", "yfinance", "dashboard", "broker_api", "execution"}
    for path in (ROOT / "portfolio_app.py", ROOT / "launch_portfolio.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] not in forbidden for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden


def test_portfolio_app_full_operator_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    def _denied(*_args: object, **_kwargs: object) -> None:
        raise OSError("GV_PORTFOLIO_V0_NETWORK_DENIED")

    monkeypatch.setattr(socket, "create_connection", _denied)
    monkeypatch.setenv("GV_PORTFOLIO_V0_HOME", str(tmp_path / "workspace"))
    monkeypatch.chdir(ROOT)

    app = AppTest.from_file(str(ROOT / "portfolio_app.py")).run(timeout=90)
    assert not app.exception, app.exception
    initial = _page_blob(app)
    assert "GV Micro-Portfolio Workspace" in initial
    assert "NSTAR" in initial
    assert "HARBOR" in initial
    assert "RIVAL" in initial
    assert "ORBIT" in initial
    assert "BENCH100" in initial
    assert "DRAFT_REVIEW" in initial
    assert "NAV=1500" in initial

    confirm = next(
        button
        for button in app.button
        if getattr(button, "key", None) == "gv_portfolio_confirm"
    )
    confirm.click()
    app = app.run(timeout=90)
    assert not app.exception, app.exception
    certified = _page_blob(app)
    assert "CERTIFIED" in certified
    assert "NAV=1499" in certified
    assert "Paper execution" in certified
    assert "Split residual=0" in certified
    assert "HARBOR" in certified

    # A fresh render exposes the next valid operation after confirmation.
    app = app.run(timeout=90)
    assert not app.exception, app.exception
    watch = next(
        button
        for button in app.button
        if getattr(button, "key", None) == "gv_portfolio_watch_observation"
    )
    watch.click()
    app = app.run(timeout=90)
    assert not app.exception, app.exception
    observed = _page_blob(app)
    assert "OBSERVED_WATCH_AIM_UNCHANGED" in observed
    assert "Later observation" in observed
    assert "Aim comparison: unchanged" in observed
    assert "no hard falsifier fired" in observed

    fresh = AppTest.from_file(str(ROOT / "portfolio_app.py")).run(timeout=90)
    assert not fresh.exception, fresh.exception
    reopened = _page_blob(fresh)
    assert "OBSERVED_WATCH_AIM_UNCHANGED" in reopened
    assert "NAV=1499" in reopened
    assert not any(
        getattr(button, "key", None) in {
            "gv_portfolio_confirm",
            "gv_portfolio_watch_observation",
        }
        for button in fresh.button
    )
