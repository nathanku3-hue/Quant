"""Streamlit AppTest for E0B-DV1 comparison surface on Certified Portfolio."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.gv_e0b_dv1_contradiction import (
    build_comparison,
    write_canonical_artifacts,
)
from core.gv_e0b_dv1_contradiction import _collect_sealed_records
from tests.gv_fs0_product.test_e0b_dv1_contradiction import _fixture_paths
from views.page_registry import PORTFOLIO_PAGE_ROUTE, PORTFOLIO_PAGE_TITLE

ROOT = Path(__file__).resolve().parents[2]


def _run_portfolio_app() -> AppTest:
    app = AppTest.from_file(str(ROOT / "dashboard.py"))
    app.query_params["page"] = PORTFOLIO_PAGE_ROUTE
    return app.run(timeout=90)


def test_apptest_e0b_missing_artifact_shows_observed_count_zero(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing_result.json"
    monkeypatch.setattr(
        "core.gv_e0b_dv1_contradiction.DEFAULT_RESULT_JSON",
        missing,
    )
    app = _run_portfolio_app()
    assert not app.exception
    assert any(header.value == PORTFOLIO_PAGE_TITLE for header in app.header)
    caption_text = "\n".join(element.value for element in app.caption)
    assert "observed-comparison count = 0" in caption_text


def test_apptest_e0b_fixture_result_renders_comparison_not_close(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    b, pkt, p, r, sess, bundle, _packet = _fixture_paths(tmp_path / "caps")
    comparison = build_comparison(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
    )
    result_path = tmp_path / "result.json"
    packet_path = tmp_path / "decision_packet.md"
    seals = _collect_sealed_records(
        baseline_path=b,
        post_path=p,
        rubric_path=r,
        packet_path=pkt,
        session_path=sess,
        bundle=bundle,
    )
    write_canonical_artifacts(
        comparison,
        sealed_records=seals,
        result_json_path=result_path,
        decision_packet_path=packet_path,
    )
    monkeypatch.setattr(
        "core.gv_e0b_dv1_contradiction.DEFAULT_RESULT_JSON",
        result_path,
    )
    app = _run_portfolio_app()
    assert not app.exception
    subheaders = [element.value for element in app.subheader]
    assert any("GV-E0B-DV1 Decision Delta" in value for value in subheaders)
    caption_text = "\n".join(element.value for element in app.caption)
    assert "observed-comparison count = 0" in caption_text
    assert "SYNTHETIC_DEV_RUN" in caption_text or "score 39 frozen" in caption_text
