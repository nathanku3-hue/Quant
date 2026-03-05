from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

import pandas as pd
import pytest

from core.drift_alert_manager import AlertLevel, AlertRecord, AlertState
from core.drift_detector import DriftTaxonomy
from views import drift_monitor_view as view_mod


class _DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def streamlit_stub(monkeypatch: pytest.MonkeyPatch):
    captured = {
        "error": [],
        "warning": [],
        "info": [],
        "success": [],
        "markdown": [],
        "caption": [],
        "subheader": [],
    }
    clicked_keys: set[str] = set()

    def _capture(name):
        return lambda msg="", *args, **kwargs: captured[name].append(str(msg))

    def _button(label, *args, **kwargs):
        key = str(kwargs.get("key", label))
        return key in clicked_keys

    monkeypatch.setattr(view_mod.st, "error", _capture("error"))
    monkeypatch.setattr(view_mod.st, "warning", _capture("warning"))
    monkeypatch.setattr(view_mod.st, "info", _capture("info"))
    monkeypatch.setattr(view_mod.st, "success", _capture("success"))
    monkeypatch.setattr(view_mod.st, "markdown", _capture("markdown"))
    monkeypatch.setattr(view_mod.st, "caption", _capture("caption"))
    monkeypatch.setattr(view_mod.st, "subheader", _capture("subheader"))
    monkeypatch.setattr(view_mod.st, "button", _button)
    monkeypatch.setattr(view_mod.st, "plotly_chart", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod.st, "dataframe", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod.st, "json", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod.st, "expander", lambda *_args, **_kwargs: _DummyContext())

    return captured, clicked_keys


@pytest.fixture
def mock_alert_manager():
    manager = Mock()
    manager.get_active_alerts = Mock(return_value=[])
    manager.acknowledge_alert = Mock(return_value=1)
    manager.resolve_alert = Mock(return_value=True)
    manager.process_drift_result = Mock(return_value=None)
    return manager


@pytest.fixture
def mock_drift_detector():
    detector = Mock()
    detector.detect_allocation_drift = Mock()
    return detector


@pytest.fixture
def red_alert():
    now = datetime.now(timezone.utc)
    return AlertRecord(
        alert_id="alert_red_1",
        drift_uid="uid_red_1",
        taxonomy=DriftTaxonomy.ALLOCATION_DRIFT.value,
        drift_score=4.0,
        normalized_score=10.0,
        alert_level=AlertLevel.RED.value,
        state=AlertState.ACTIVE.value,
        created_at=now,
        updated_at=now,
        details={"path": "test"},
    )


def test_empty_state_rendering(streamlit_stub, mock_alert_manager, mock_drift_detector):
    captured, _ = streamlit_stub

    view_mod.render_drift_monitor_view(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_weights=None,
        baseline_metadata=None,
        live_weights=None,
        macro=pd.DataFrame(),
    )

    assert any("No active drift alerts" in msg for msg in captured["info"])


def test_red_alert_display_path(streamlit_stub, mock_alert_manager, mock_drift_detector, red_alert):
    captured, _ = streamlit_stub
    mock_alert_manager.get_active_alerts.return_value = [red_alert]

    view_mod.render_drift_monitor_view(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_weights=None,
        baseline_metadata=None,
        live_weights=None,
        macro=pd.DataFrame(),
    )

    assert any("Current level: RED" in msg for msg in captured["error"])


def test_acknowledge_button_calls_manager(
    streamlit_stub,
    mock_alert_manager,
    mock_drift_detector,
    red_alert,
):
    _, clicked_keys = streamlit_stub
    mock_alert_manager.get_active_alerts.return_value = [red_alert]
    clicked_keys.add(f"ack_{red_alert.alert_id}")

    view_mod.render_drift_monitor_view(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_weights=None,
        baseline_metadata=None,
        live_weights=None,
        macro=pd.DataFrame(),
    )

    mock_alert_manager.acknowledge_alert.assert_called_once_with(red_alert.taxonomy)


def test_force_check_without_baseline_shows_error(
    streamlit_stub,
    mock_alert_manager,
    mock_drift_detector,
):
    captured, clicked_keys = streamlit_stub
    clicked_keys.add("force_drift_check")

    view_mod.render_drift_monitor_view(
        alert_manager=mock_alert_manager,
        drift_detector=mock_drift_detector,
        baseline_weights=None,
        baseline_metadata=None,
        live_weights=pd.Series({"AAPL": 1.0}),
        macro=pd.DataFrame(),
    )

    assert any("baseline weights unavailable" in msg.lower() for msg in captured["error"])
    mock_drift_detector.detect_allocation_drift.assert_not_called()
