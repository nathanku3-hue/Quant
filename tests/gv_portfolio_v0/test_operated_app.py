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


def test_operated_entrypoints_have_no_provider_or_broker_imports() -> None:
    forbidden = {"alpaca", "yfinance", "dashboard", "broker_api"}
    for path in (
        ROOT / "operated_portfolio_app.py",
        ROOT / "launch_operated_portfolio.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] not in forbidden for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden


def test_operated_portfolio_black_box_operator_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    def _denied(*_args: object, **_kwargs: object) -> None:
        raise OSError("GV_OPERATED_PORTFOLIO_NETWORK_DENIED")

    monkeypatch.setattr(socket, "create_connection", _denied)
    monkeypatch.setenv("GV_OPERATED_PORTFOLIO_HOME", str(tmp_path / "workspace"))
    monkeypatch.chdir(ROOT)

    app = AppTest.from_file(str(ROOT / "operated_portfolio_app.py")).run(timeout=90)
    assert not app.exception, app.exception
    initial = _page_blob(app)
    assert "GV Operated Portfolio 10" in initial
    assert "instruments=10" in initial
    assert "portfolio_count=1" in initial
    assert "DIGITAL_INFRASTRUCTURE" in initial
    assert "REAL_ECONOMY" in initial
    assert "DRAFT_REVIEW" in initial
    assert "NAV=5000" in initial

    confirm = next(
        button
        for button in app.button
        if getattr(button, "key", None) == "gv_operated_confirm"
    )
    confirm.click()
    app = app.run(timeout=90)
    assert not app.exception, app.exception
    funded = _page_blob(app)
    assert "FUNDED_CERTIFIED" in funded
    assert "NAV=4992" in funded
    assert "NSTAR" in funded
    assert "HARBOR" in funded
    assert "ATLAS" in funded
    assert "VITAL" in funded

    app = app.run(timeout=90)
    no_change = next(
        button
        for button in app.button
        if getattr(button, "key", None) == "gv_operated_no_change"
    )
    no_change.click()
    app = app.run(timeout=90)
    assert not app.exception, app.exception
    unchanged = _page_blob(app)
    assert "OBSERVED_NO_CHANGE_CERTIFIED" in unchanged
    assert "NO_CHANGE" in unchanged
    assert "orders_created" in unchanged
    assert "NAV=4992" in unchanged

    app = app.run(timeout=90)
    transition = next(
        button
        for button in app.button
        if getattr(button, "key", None) == "gv_operated_transition"
    )
    transition.click()
    app = app.run(timeout=90)
    assert not app.exception, app.exception
    transitioned = _page_blob(app)
    assert "TRANSITION_CERTIFIED" in transitioned
    assert "AUTHORIZED_TRANSITION" in transitioned
    assert "SELL" in transitioned
    assert "BUY" in transitioned
    assert "MERID" in transitioned
    assert "NAV=4988" in transitioned
    assert "residual=0" in transitioned

    app = app.run(timeout=90)
    correction = next(
        button
        for button in app.button
        if getattr(button, "key", None) == "gv_operated_correction"
    )
    correction.click()
    app = app.run(timeout=90)
    assert not app.exception, app.exception
    corrected = _page_blob(app)
    assert "CORRECTED_CERTIFIED" in corrected
    assert "NAV=4988" in corrected
    assert "lineage_depth=3" in corrected

    fresh = AppTest.from_file(str(ROOT / "operated_portfolio_app.py")).run(timeout=90)
    assert not fresh.exception, fresh.exception
    reopened = _page_blob(fresh)
    assert "CORRECTED_CERTIFIED" in reopened
    assert "NAV=4988" in reopened
    assert "lineage_depth=3" in reopened
    assert not any(
        getattr(button, "key", None) in {
            "gv_operated_confirm",
            "gv_operated_no_change",
            "gv_operated_transition",
            "gv_operated_correction",
        }
        for button in fresh.button
    )
