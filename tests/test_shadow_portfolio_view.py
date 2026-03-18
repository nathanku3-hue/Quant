from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from views import shadow_portfolio_view as view_mod


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
        "caption": [],
        "markdown": [],
        "metric": [],
    }

    def _capture(name):
        return lambda msg="", *args, **kwargs: captured[name].append(str(msg))

    monkeypatch.setattr(view_mod.st, "error", _capture("error"))
    monkeypatch.setattr(view_mod.st, "warning", _capture("warning"))
    monkeypatch.setattr(view_mod.st, "info", _capture("info"))
    monkeypatch.setattr(view_mod.st, "success", _capture("success"))
    monkeypatch.setattr(view_mod.st, "caption", _capture("caption"))
    monkeypatch.setattr(view_mod.st, "markdown", _capture("markdown"))
    monkeypatch.setattr(view_mod.st, "subheader", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        view_mod.st,
        "metric",
        lambda label, value, *args, **kwargs: captured["metric"].append(f"{label}:{value}"),
    )
    monkeypatch.setattr(view_mod.st, "plotly_chart", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod.st, "dataframe", lambda *_args, **_kwargs: None)
    return captured


def test_render_shadow_portfolio_view_handles_missing_artifacts(streamlit_stub, tmp_path: Path):
    view_mod.render_shadow_portfolio_view(
        summary_path=tmp_path / "summary.json",
        evidence_path=tmp_path / "evidence.csv",
        delta_path=tmp_path / "delta.csv",
    )

    assert any("No Phase 59 shadow monitor artifacts available yet." in msg for msg in streamlit_stub["info"])


def test_render_shadow_portfolio_view_renders_red_status(streamlit_stub, tmp_path: Path):
    summary_path = tmp_path / "summary.json"
    evidence_path = tmp_path / "evidence.csv"
    delta_path = tmp_path / "delta.csv"
    summary_path.write_text(
        json.dumps(
            {
                "review_hold": True,
                "selected_variant": {"variant_id": "v_test", "sharpe": -0.1, "cagr": -0.02},
                "shadow_reference": {
                    "alert_level": "RED",
                    "holdings_overlap": 0.0,
                    "gross_exposure_delta": 1.0,
                    "turnover_delta_rel": 0.02,
                    "alert_rows": [
                        {
                            "metric_name": "holdings_overlap",
                            "metric_value": 0.0,
                            "metric_level": "RED",
                            "reason": "test",
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "date": "2022-12-30",
                "surface_id": "phase59_shadow_research",
                "reference_only": False,
                "variant_id": "v_test",
                "net_ret": 0.0,
                "equity": 1.0,
                "notional_equity": 100000.0,
                "turnover": None,
                "gross_exposure": None,
                "positions_count": None,
                "is_observed_day": True,
                "source_path": "research",
            },
            {
                "date": "2026-04-10",
                "surface_id": "phase50_shadow_reference",
                "reference_only": True,
                "variant_id": None,
                "net_ret": 0.001,
                "equity": 1.02,
                "notional_equity": 102000.0,
                "turnover": 1.0,
                "gross_exposure": 1.0,
                "positions_count": 5,
                "is_observed_day": True,
                "source_path": "phase50",
            },
        ]
    ).to_csv(evidence_path, index=False)
    pd.DataFrame(
        [
            {"surface_id": "phase59_shadow_research", "reference_only": False},
            {"surface_id": "phase50_shadow_reference_alerts", "reference_only": True},
        ]
    ).to_csv(delta_path, index=False)

    view_mod.render_shadow_portfolio_view(
        summary_path=summary_path,
        evidence_path=evidence_path,
        delta_path=delta_path,
    )

    assert any("Reference alert: RED" in msg for msg in streamlit_stub["error"])
    assert any(item.startswith("Holdings Overlap:0.00%") for item in streamlit_stub["metric"])
