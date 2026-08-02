from __future__ import annotations

from pathlib import Path
import socket

import pytest

from gv_portfolio_v0.operated_scenarios import PROSPECTIVE_25_SCENARIO_ID

ROOT = Path(__file__).resolve().parents[2]


def _blob(app: object) -> str:
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


def _element_by_key(collection: object, key: str) -> object:
    return next(
        element
        for element in collection
        if getattr(element, "key", None) == key
    )


def test_prospective_app_accepts_runtime_observation_preview_confirm_and_reopen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    def _denied(*_args: object, **_kwargs: object) -> None:
        raise OSError("GV_PROSPECTIVE_NETWORK_DENIED")

    monkeypatch.setattr(socket, "create_connection", _denied)
    monkeypatch.setenv("GV_OPERATED_SCENARIO_ID", PROSPECTIVE_25_SCENARIO_ID)
    monkeypatch.setenv("GV_OPERATED_PORTFOLIO_HOME", str(tmp_path / "workspace"))
    monkeypatch.chdir(ROOT)

    app = AppTest.from_file(str(ROOT / "operated_portfolio_app.py")).run(timeout=120)
    assert not app.exception, app.exception
    initial = _blob(app)
    assert "GV Prospective Paper Baseline 25" in initial
    assert "episodes=0" in initial
    assert "operator_actions=0" in initial
    assert "instruments=25" in initial
    assert "residual=0" in initial

    _element_by_key(
        app.text_area, "gv_prospective_content_NSTAR"
    ).set_value(
        "Northstar operator-supplied renewal evidence remained inside the watch band."
    )
    _element_by_key(
        app.text_input, "gv_prospective_locator_NSTAR"
    ).set_value("operator://2026-10-01/nstar-renewal-review")
    _element_by_key(
        app.text_input, "gv_prospective_observed_at_NSTAR"
    ).set_value("2026-10-01T12:00:00.000000Z")
    _element_by_key(
        app.text_area, "gv_prospective_claim_NSTAR"
    ).set_value(
        "Renewal durability remains intact after the operator-supplied runtime observation."
    )
    _element_by_key(
        app.text_area, "gv_prospective_rationale_NSTAR"
    ).set_value(
        "The new source remains inside the watch band; preserve capital and cash."
    )
    _element_by_key(app.button, "gv_prospective_preview").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    preview = _blob(app)
    assert "Mutation-free preview" in preview
    assert "authoritative=false" in preview
    preview_tables = [
        getattr(table, "value", None)
        for table in app.table
        if hasattr(getattr(table, "value", None), "columns")
        and "economics_changed" in getattr(table, "value").columns
    ]
    assert preview_tables
    assert bool(preview_tables[-1].iloc[0]["economics_changed"]) is False
    assert any(
        getattr(button, "key", None) == "gv_prospective_confirm"
        for button in app.button
    )

    _element_by_key(app.button, "gv_prospective_confirm").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    confirmed = _blob(app)
    assert "Prospective observation confirmed and certified append-only." in confirmed
    assert "episodes=1" in confirmed
    assert "operator_actions=2" in confirmed
    assert "PROSPECTIVE_NO_CHANGE" in confirmed
    assert "orders_created" in confirmed
    assert "residual=0" in confirmed

    fresh = AppTest.from_file(str(ROOT / "operated_portfolio_app.py")).run(timeout=120)
    assert not fresh.exception, fresh.exception
    reopened = _blob(fresh)
    assert "episodes=1" in reopened
    assert "operator_actions=2" in reopened
    assert "PROSPECTIVE_NO_CHANGE" in reopened
    assert "lineage_depth=1" in reopened
    assert "residual=0" in reopened


def test_prospective_app_previews_and_confirms_runtime_transition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    def _denied(*_args: object, **_kwargs: object) -> None:
        raise OSError("GV_PROSPECTIVE_NETWORK_DENIED")

    monkeypatch.setattr(socket, "create_connection", _denied)
    monkeypatch.setenv("GV_OPERATED_SCENARIO_ID", PROSPECTIVE_25_SCENARIO_ID)
    monkeypatch.setenv("GV_OPERATED_PORTFOLIO_HOME", str(tmp_path / "workspace"))
    monkeypatch.chdir(ROOT)

    app = AppTest.from_file(str(ROOT / "operated_portfolio_app.py")).run(timeout=120)
    assert not app.exception, app.exception
    _element_by_key(
        app.selectbox, "gv_prospective_instrument_symbol"
    ).select("HARBOR")
    app = app.run(timeout=120)
    assert not app.exception, app.exception

    _element_by_key(
        app.checkbox, "gv_prospective_add_second_review"
    ).set_value(True)
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    _element_by_key(
        app.selectbox, "gv_prospective_second_instrument_symbol"
    ).select("MERID")
    app = app.run(timeout=120)
    assert not app.exception, app.exception

    _element_by_key(
        app.text_area, "gv_prospective_content_HARBOR"
    ).set_value(
        "Harbor backlog quality weakened while Meridian converted qualification into a firm order."
    )
    _element_by_key(
        app.text_input, "gv_prospective_locator_HARBOR"
    ).set_value("operator://2026-10-15/harbor-meridian-review")
    _element_by_key(
        app.text_input, "gv_prospective_observed_at_HARBOR"
    ).set_value("2026-10-15T12:00:00.000000Z")
    _element_by_key(
        app.number_input, "gv_prospective_score_HARBOR"
    ).set_value(260)
    _element_by_key(
        app.number_input, "gv_prospective_quantity_HARBOR"
    ).set_value(6)
    _element_by_key(
        app.text_area, "gv_prospective_claim_HARBOR"
    ).set_value(
        "Backlog quality weakened; retain only a reduced monitoring position."
    )
    _element_by_key(
        app.number_input, "gv_prospective_secondary_score_MERID"
    ).set_value(590)
    _element_by_key(
        app.number_input, "gv_prospective_secondary_quantity_MERID"
    ).set_value(5)
    _element_by_key(
        app.text_area, "gv_prospective_secondary_claim_MERID"
    ).set_value(
        "A firm qualification order now supports bounded prospective funding."
    )
    _element_by_key(
        app.text_area, "gv_prospective_rationale_HARBOR"
    ).set_value(
        "Reduce Harbor and fund Meridian because the runtime evidence reverses their capital priority."
    )
    _element_by_key(app.button, "gv_prospective_preview").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    preview = _blob(app)
    assert "change_type=PROSPECTIVE_TRANSITION" in preview
    assert "orders_created=2" in preview
    assert "Proposed transition legs" in preview
    assert "transition_sides=SELL,BUY" in preview
    assert "authoritative=false" in preview

    _element_by_key(app.button, "gv_prospective_confirm").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    confirmed = _blob(app)
    assert "episodes=1" in confirmed
    assert "operator_actions=2" in confirmed
    assert "change_type=PROSPECTIVE_TRANSITION" in confirmed
    assert "holdings_changed=True" in confirmed
    assert "cash_changed=True" in confirmed
    assert "orders_created=2" in confirmed
    assert "Confirmed transition legs" in confirmed
    assert "transition_sides=SELL,BUY" in confirmed
    assert "residual=0" in confirmed

    fresh = AppTest.from_file(str(ROOT / "operated_portfolio_app.py")).run(timeout=120)
    assert not fresh.exception, fresh.exception
    reopened = _blob(fresh)
    assert "episodes=1" in reopened
    assert "change_type=PROSPECTIVE_TRANSITION" in reopened
    assert "orders_created=2" in reopened
    assert "transition_sides=SELL,BUY" in reopened
    assert "residual=0" in reopened


def test_prospective_app_rejects_validated_proposal_without_authority_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    def _denied(*_args: object, **_kwargs: object) -> None:
        raise OSError("GV_PROSPECTIVE_NETWORK_DENIED")

    monkeypatch.setattr(socket, "create_connection", _denied)
    monkeypatch.setenv("GV_OPERATED_SCENARIO_ID", PROSPECTIVE_25_SCENARIO_ID)
    monkeypatch.setenv("GV_OPERATED_PORTFOLIO_HOME", str(tmp_path / "workspace"))
    monkeypatch.chdir(ROOT)

    app = AppTest.from_file(str(ROOT / "operated_portfolio_app.py")).run(timeout=120)
    assert not app.exception, app.exception
    initial = _blob(app)
    initial_book_hash = next(
        line for line in initial.splitlines() if "book_hash=`" in line
    )

    _element_by_key(
        app.text_area, "gv_prospective_content_NSTAR"
    ).set_value(
        "Northstar renewal evidence is coherent, but the operator rejects its source quality."
    )
    _element_by_key(
        app.text_input, "gv_prospective_locator_NSTAR"
    ).set_value("operator://2026-11-01/nstar-rejected-source")
    _element_by_key(
        app.text_input, "gv_prospective_observed_at_NSTAR"
    ).set_value("2026-11-01T12:00:00.000000Z")
    _element_by_key(
        app.text_area, "gv_prospective_claim_NSTAR"
    ).set_value(
        "Renewal durability appears intact, but this source is not accepted as authority."
    )
    _element_by_key(
        app.text_area, "gv_prospective_rationale_NSTAR"
    ).set_value(
        "The proposal is internally valid but should not alter portfolio authority."
    )
    _element_by_key(app.button, "gv_prospective_preview").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    assert "authoritative=false" in _blob(app)

    _element_by_key(
        app.text_area, "gv_prospective_rejection_reason"
    ).set_value(
        "Source quality is insufficient for decision authority; retain only the rejection record."
    )
    _element_by_key(app.button, "gv_prospective_reject").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    rejected = _blob(app)
    assert "Prospective proposal rejected and certified without authority change." in rejected
    assert "episodes=1" in rejected
    assert "operator_actions=2" in rejected
    assert "last_disposition=REJECTED" in rejected
    assert "Rejected prospective proposals" in rejected
    assert "authority_changed=False" in rejected
    assert "holdings_changed=False" in rejected
    assert "cash_changed=False" in rejected
    assert "orders_created=0" in rejected
    assert initial_book_hash in rejected

    fresh = AppTest.from_file(str(ROOT / "operated_portfolio_app.py")).run(timeout=120)
    assert not fresh.exception, fresh.exception
    reopened = _blob(fresh)
    assert "episodes=1" in reopened
    assert "last_disposition=REJECTED" in reopened
    assert "Rejected prospective proposals" in reopened
    assert "authority_changed=False" in reopened
    assert initial_book_hash in reopened
