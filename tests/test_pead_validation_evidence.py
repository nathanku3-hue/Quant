from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from views import pead_validation_evidence as view_mod
from views import strategy_view


class _MetricColumn:
    def __init__(self, captured: dict[str, list]) -> None:
        self._captured = captured

    def metric(self, label: str, value: str, *_args, **_kwargs) -> None:
        self._captured["metrics"].append((str(label), str(value)))


class _Expander:
    def __enter__(self) -> "_Expander":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


@pytest.fixture
def streamlit_stub(monkeypatch: pytest.MonkeyPatch) -> dict[str, list]:
    captured: dict[str, list] = {
        "subheader": [],
        "warning": [],
        "caption": [],
        "error": [],
        "markdown": [],
        "code": [],
        "success": [],
        "table": [],
        "metrics": [],
        "expander": [],
    }

    def _capture(name: str):
        return lambda value="", *_args, **_kwargs: captured[name].append(str(value))

    monkeypatch.setattr(view_mod.st, "subheader", _capture("subheader"))
    monkeypatch.setattr(view_mod.st, "warning", _capture("warning"))
    monkeypatch.setattr(view_mod.st, "caption", _capture("caption"))
    monkeypatch.setattr(view_mod.st, "error", _capture("error"))
    monkeypatch.setattr(view_mod.st, "markdown", _capture("markdown"))
    monkeypatch.setattr(view_mod.st, "code", _capture("code"))
    monkeypatch.setattr(view_mod.st, "success", _capture("success"))
    monkeypatch.setattr(
        view_mod.st,
        "table",
        lambda value, *_args, **_kwargs: captured["table"].append(value),
    )
    monkeypatch.setattr(
        view_mod.st,
        "columns",
        lambda count: [_MetricColumn(captured) for _ in range(count)],
    )

    def _expander(label: str, *_args, **_kwargs) -> _Expander:
        captured["expander"].append(str(label))
        return _Expander()

    monkeypatch.setattr(view_mod.st, "expander", _expander)
    return captured


def _valid_validation_payload(*, full_universe: bool = True) -> dict:
    return {
        "artifact_name": "pead_real_data_validation",
        "round_id": "ROUND-TEST-FULL" if full_universe else "ROUND-TEST-LEGACY",
        "mode": "EXECUTION_PACKET",
        "evidence_policy": {
            "interpretation_performed": False,
            "forbidden_use": [
                "alpha claims",
                "strategy promotion",
                "ranking/scoring",
                "alerts",
                "broker/order paths",
            ],
        },
        "counts": {
            "rows": 14015160 if full_universe else 754920,
            "events": 233586 if full_universe else 12582,
            "issuers": 9969 if full_universe else 362,
            "eligible_events": 196638 if full_universe else 11450,
            "ineligible_events": 36948 if full_universe else 1132,
        },
        "lineage": {
            "d1": {
                "manifest_path": "data/processed/d1.manifest.json",
                "manifest_sha256": "1" * 64,
                "parquet_path": "data/processed/d1.parquet",
                "parquet_sha256": "2" * 64,
                "row_count": 14015160 if full_universe else 346511,
            },
            "d2b": {
                "manifest_path": "data/processed/d2b.manifest.json",
                "manifest_sha256": "3" * 64,
                "parquet_path": "data/processed/d2b.parquet",
                "parquet_sha256": "4" * 64,
                "row_count": 14015160 if full_universe else 754920,
            },
            "d3": {
                "manifest_path": "data/processed/d3.manifest.json",
                "manifest_sha256": "5" * 64,
                "parquet_path": "data/processed/d3.parquet",
                "parquet_sha256": "6" * 64,
                "row_count": 2810,
            },
        },
        "outputs": {
            "event_date": {
                "ex_post_descriptive_only": False,
                "metrics": {
                    "car": {
                        "hac": {
                            "observed_cohort_gap_count": 2777,
                            "standard_error": None,
                            "t_stat": None,
                        }
                    },
                    "bhar": {
                        "hac": {
                            "observed_cohort_gap_count": 2777,
                            "standard_error": None,
                            "t_stat": None,
                        }
                    },
                },
            },
            "quarterly": {
                "ex_post_descriptive_only": True,
                "metrics": {},
            },
        },
        "limitations": list(
            view_mod.EXPECTED_FULL_UNIVERSE_LIMITATIONS
            if full_universe
            else view_mod.EXPECTED_LEGACY_LIMITATIONS
        ),
    }


def _valid_m1b_payload(
    *,
    schema_version: str = "2.0",
    parent_sha256: str = "1" * 64,
    full_universe: bool = True,
) -> dict:
    payload = {
        "schema_version": schema_version,
        "round_id": "ROUND-TEST-M1B-FULL" if full_universe else "ROUND-TEST-M1B-LEGACY",
        "scope_id": "V2_PEAD_CALENDAR_TIME_INFERENCE_IMPLEMENTATION",
        "method_id": "calendar_time_q5_q1_single_factor_hac59_v1",
        "evidence_policy": {
            "allowed_use": "bounded_methodology_review_only",
            "forbidden_use": list(view_mod.EXPECTED_M1B_FORBIDDEN_USE),
            "interpretation_performed": False,
            "strategy_promotion_authorized": False,
            "ranking_or_scoring_authorized": False,
            "alerts_or_recommendations_authorized": False,
            "broker_or_order_path_authorized": False,
        },
        "formation": {
            "minimum_finite_per_leg": 10,
        },
        "lineage": {},
        "limitations": {
            "sample_universe": "full_universe" if full_universe else "fixed_500_gvkey_current_vintage_sample",
            "eps_vintage": "current_vintage_compustat_eps",
            "return_source": "compustat_total_return_proxy",
            "delisting_adjustment": "none",
            "factor_model": "single_factor_gross_equal_weight_q5_minus_q1".replace(
                "single_factor", "single_factor_mktrf"
            ),
        },
        "session_coverage": {
            "authoritative_sessions": 2810,
            "retained_sessions": 2552 if full_universe else 2539,
            "retained_date_min": "2016-01-12" if full_universe else "2016-02-01",
            "retained_date_max": "2026-03-06",
            "extreme_expected_rows": 5159218 if full_universe else 226772,
            "extreme_missing_rows": 65230 if full_universe else 1519,
            "null_return_date_rows_excluded": 227362 if full_universe else 19812,
            "internal_gap_count": 0,
        },
        "primary_inference": {
            "status": "valid",
            "observations": 2552 if full_universe else 2539,
            "hac_maxlags_used": 59,
            "use_correction": True,
        },
    }
    if schema_version == "2.0":
        payload["artifact_name"] = "pead_calendar_time_inference_m1b"
        payload["parent_sha256"] = parent_sha256
        payload["publishable"] = True
    return payload


def _write_payload(path: Path, payload: object) -> str:
    data = json.dumps(payload, sort_keys=True).encode("utf-8")
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _write_status_bundle(tmp_path: Path) -> tuple[Path, str, Path, str, Path, str, Path, str]:
    validation_path = tmp_path / "validation-full.json"
    validation_sha = _write_payload(validation_path, _valid_validation_payload(full_universe=True))
    m1b_path = tmp_path / "m1b-full.json"
    m1b_sha = _write_payload(
        m1b_path,
        _valid_m1b_payload(schema_version="2.0", parent_sha256=validation_sha, full_universe=True),
    )
    legacy_validation_path = tmp_path / "validation-legacy.json"
    legacy_validation_sha = _write_payload(
        legacy_validation_path,
        _valid_validation_payload(full_universe=False),
    )
    legacy_m1b_path = tmp_path / "m1b-legacy.json"
    legacy_m1b_sha = _write_payload(
        legacy_m1b_path,
        _valid_m1b_payload(schema_version="1.0", full_universe=False),
    )
    return (
        validation_path,
        validation_sha,
        m1b_path,
        m1b_sha,
        legacy_validation_path,
        legacy_validation_sha,
        legacy_m1b_path,
        legacy_m1b_sha,
    )


def _rendered_text(captured: dict[str, list]) -> str:
    return "\n".join(
        str(value)
        for key, values in captured.items()
        if key != "table"
        for value in values
    )


def test_missing_json_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(
        view_mod.PeadValidationEvidenceError,
        match="evidence JSON missing",
    ):
        view_mod.load_pead_validation_evidence(
            tmp_path / "missing.json",
            expected_sha256="0" * 64,
        )


def test_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    _write_payload(path, _valid_validation_payload())

    with pytest.raises(
        view_mod.PeadValidationEvidenceError,
        match="SHA256 mismatch",
    ):
        view_mod.load_pead_validation_evidence(
            path,
            expected_sha256="0" * 64,
        )


def test_schema_mismatch_fails_closed(tmp_path: Path) -> None:
    payload = _valid_validation_payload()
    del payload["counts"]["events"]
    path = tmp_path / "evidence.json"
    sha256 = _write_payload(path, payload)

    with pytest.raises(
        view_mod.PeadValidationEvidenceError,
        match="required integer field missing: events",
    ):
        view_mod.load_pead_validation_evidence(
            path,
            expected_sha256=sha256,
        )


def test_non_object_json_root_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    sha256 = _write_payload(path, ["not", "an", "object"])

    with pytest.raises(
        view_mod.PeadValidationEvidenceError,
        match="evidence JSON root must be an object",
    ):
        view_mod.load_pead_validation_evidence(
            path,
            expected_sha256=sha256,
        )


def test_unrenderable_limitations_fail_closed(tmp_path: Path) -> None:
    payload = _valid_validation_payload()
    payload["limitations"] = ["full universe (9,969 issuers)", None]
    path = tmp_path / "evidence.json"
    sha256 = _write_payload(path, payload)

    with pytest.raises(
        view_mod.PeadValidationEvidenceError,
        match="limitations contain an unreadable item",
    ):
        view_mod.load_pead_validation_evidence(
            path,
            expected_sha256=sha256,
        )


def test_v2_pair_parent_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    (
        validation_path,
        validation_sha,
        m1b_path,
        m1b_sha,
        legacy_validation_path,
        legacy_validation_sha,
        legacy_m1b_path,
        legacy_m1b_sha,
    ) = _write_status_bundle(tmp_path)
    bad_payload = _valid_m1b_payload(
        schema_version="2.0",
        parent_sha256="0" * 64,
        full_universe=True,
    )
    m1b_sha = _write_payload(m1b_path, bad_payload)

    with pytest.raises(
        view_mod.PeadValidationEvidenceError,
        match="parent hash linkage mismatch",
    ):
        view_mod.load_pead_evidence_status(
            validation_path,
            m1b_path,
            expected_validation_sha256=validation_sha,
            expected_m1b_sha256=m1b_sha,
            legacy_validation_path=legacy_validation_path,
            legacy_m1b_path=legacy_m1b_path,
            expected_legacy_validation_sha256=legacy_validation_sha,
            expected_legacy_m1b_sha256=legacy_m1b_sha,
        )


def test_v2_pair_requires_publishable_child(tmp_path: Path) -> None:
    path = tmp_path / "m1b.json"
    payload = _valid_m1b_payload(schema_version="2.0", parent_sha256="1" * 64)
    payload["publishable"] = False
    sha256 = _write_payload(path, payload)

    with pytest.raises(
        view_mod.PeadValidationEvidenceError,
        match="publishable flag is not true",
    ):
        view_mod.load_pead_m1b_evidence(path, expected_sha256=sha256)


def test_m1b_action_authority_fails_closed(tmp_path: Path) -> None:
    payload = _valid_m1b_payload()
    payload["evidence_policy"]["strategy_promotion_authorized"] = True
    path = tmp_path / "m1b.json"
    sha256 = _write_payload(path, payload)

    with pytest.raises(
        view_mod.PeadValidationEvidenceError,
        match="strategy_promotion_authorized = true",
    ):
        view_mod.load_pead_m1b_evidence(path, expected_sha256=sha256)


def test_status_surface_renders_v2_primary_readiness_and_folded_legacy(
    tmp_path: Path,
    streamlit_stub: dict[str, list],
) -> None:
    (
        validation_path,
        validation_sha,
        m1b_path,
        m1b_sha,
        legacy_validation_path,
        legacy_validation_sha,
        legacy_m1b_path,
        legacy_m1b_sha,
    ) = _write_status_bundle(tmp_path)

    status = view_mod.render_pead_validation_evidence(
        validation_path,
        expected_sha256=validation_sha,
        m1b_path=m1b_path,
        expected_m1b_sha256=m1b_sha,
        legacy_validation_path=legacy_validation_path,
        legacy_m1b_path=legacy_m1b_path,
        expected_legacy_validation_sha256=legacy_validation_sha,
        expected_legacy_m1b_sha256=legacy_m1b_sha,
    )

    assert status is not None
    assert status.validation.counts["events"] == 233586
    assert status.validation.counts["issuers"] == 9969
    assert status.m1b.retained_sessions == 2552
    assert status.legacy_validation is not None
    assert status.legacy_validation.counts["events"] == 12582
    assert streamlit_stub["subheader"] == [view_mod.REVIEW_ONLY_TITLE]
    assert streamlit_stub["caption"] == ["Primary v2 evidence pair"]
    assert streamlit_stub["error"] == []
    assert streamlit_stub["code"] == []
    assert streamlit_stub["success"] == []
    assert streamlit_stub["expander"] == ["Legacy sample comparison"]
    assert ("Events", "233,586") in streamlit_stub["metrics"]
    assert ("Eligible", "196,638") in streamlit_stub["metrics"]
    assert ("Issuers", "9,969") in streamlit_stub["metrics"]
    assert ("Retained Sessions", "2,552") in streamlit_stub["metrics"]
    assert ("Internal Gaps", "0") in streamlit_stub["metrics"]

    readiness_rows = streamlit_stub["table"][0]
    assert readiness_rows == [
        {
            "Item": "Primary v2 evidence pair",
            "State": "Pass",
            "Meaning": "Full-universe validation and M1B child are hash-linked and read-only.",
        },
        {
            "Item": "Dashboard readiness",
            "State": "Ready",
            "Meaning": "Use as minimal evidence/readiness status only.",
        },
        {
            "Item": "Legacy sample comparison",
            "State": "Folded",
            "Meaning": "Available only as secondary context.",
        },
        {
            "Item": "Alpha / product actions",
            "State": "Blocked",
            "Meaning": "Separate Alpha Interpretation Gate required.",
        },
    ]
    legacy_rows = streamlit_stub["table"][1]
    assert legacy_rows[0] == {
        "Item": "Legacy events",
        "Primary v2": "233,586",
        "Legacy sample": "12,582",
    }
    assert any("Primary full-universe evidence pair passes" in text for text in streamlit_stub["markdown"])
    assert any("not an alpha verdict" in text for text in streamlit_stub["markdown"])
    assert any("Strategy promotion, ranking" in text for text in streamlit_stub["markdown"])

    rendered = _rendered_text(streamlit_stub)
    assert "SHA256" not in rendered
    assert "manifest" not in rendered.lower()
    assert "docs/context" not in rendered
    assert ".json" not in rendered
    assert re.search(r"\b[0-9a-f]{64}\b", rendered.lower()) is None


def test_renderer_returns_none_and_shows_sanitized_fail_closed_error(
    tmp_path: Path,
    streamlit_stub: dict[str, list],
) -> None:
    result = view_mod.render_pead_validation_evidence(
        tmp_path / "missing.json",
        expected_sha256="0" * 64,
        m1b_path=tmp_path / "missing-m1b.json",
        expected_m1b_sha256="0" * 64,
        legacy_validation_path=tmp_path / "missing-legacy.json",
        legacy_m1b_path=tmp_path / "missing-legacy-m1b.json",
        expected_legacy_validation_sha256="0" * 64,
        expected_legacy_m1b_sha256="0" * 64,
    )

    assert result is None
    assert len(streamlit_stub["error"]) == 1
    assert "failed closed" in streamlit_stub["error"][0]
    assert "missing.json" not in streamlit_stub["error"][0]
    assert streamlit_stub["table"] == []
    assert streamlit_stub["metrics"] == []
    assert streamlit_stub["warning"] == []
    assert streamlit_stub["caption"] == []


def test_promotional_or_action_language_is_absent_in_positive_form(
    tmp_path: Path,
    streamlit_stub: dict[str, list],
) -> None:
    (
        validation_path,
        validation_sha,
        m1b_path,
        m1b_sha,
        legacy_validation_path,
        legacy_validation_sha,
        legacy_m1b_path,
        legacy_m1b_sha,
    ) = _write_status_bundle(tmp_path)

    view_mod.render_pead_validation_evidence(
        validation_path,
        expected_sha256=validation_sha,
        m1b_path=m1b_path,
        expected_m1b_sha256=m1b_sha,
        legacy_validation_path=legacy_validation_path,
        legacy_m1b_path=legacy_m1b_path,
        expected_legacy_validation_sha256=legacy_validation_sha,
        expected_legacy_m1b_sha256=legacy_m1b_sha,
    )

    rendered = _rendered_text(streamlit_stub).replace(view_mod.REVIEW_ONLY_WARNING, "")
    forbidden_positive_phrases = (
        "alpha proven",
        "statistically significant",
        "buy signal",
        "sell signal",
        "trade recommendation",
        "recommended action",
        "approved promotion",
        "broker order",
    )
    lowered = rendered.lower()
    for phrase in forbidden_positive_phrases:
        assert phrase not in lowered
    assert view_mod.REVIEW_ONLY_WARNING in _rendered_text(streamlit_stub)


def test_strategy_page_routes_pead_evidence_status_tab(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        strategy_view.st,
        "radio",
        lambda *_args, **_kwargs: strategy_view.PEAD_EVIDENCE_STATUS_TAB,
    )

    strategy_view.render_strategy_page(
        render_modular_strategies=lambda: calls.append("matrix"),
        render_backtest_lab=lambda: calls.append("backtest"),
        render_pead_validation_evidence=lambda: calls.append("evidence"),
    )

    assert calls == ["evidence"]


@pytest.mark.parametrize(
    ("selection", "expected_call"),
    (
        ("Strategy Matrix", "matrix"),
        ("Backtest Lab", "backtest"),
    ),
)
def test_strategy_page_preserves_legacy_routes(
    monkeypatch: pytest.MonkeyPatch,
    selection: str,
    expected_call: str,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        strategy_view.st,
        "radio",
        lambda *_args, **_kwargs: selection,
    )

    strategy_view.render_strategy_page(
        render_modular_strategies=lambda: calls.append("matrix"),
        render_backtest_lab=lambda: calls.append("backtest"),
        render_pead_validation_evidence=lambda: calls.append("evidence"),
    )

    assert calls == [expected_call]


def test_dashboard_wires_read_only_evidence_renderer() -> None:
    source = Path("dashboard.py").read_text(encoding="utf-8")
    assert (
        "from views.pead_validation_evidence import "
        "render_pead_validation_evidence"
    ) in source
    assert (
        "render_pead_validation_evidence=render_pead_validation_evidence"
    ) in source


def test_strategy_surface_renders_pead_evidence_status_with_streamlit() -> None:
    app = AppTest.from_string(
        """
from views.pead_validation_evidence import render_pead_validation_evidence
from views.strategy_view import PEAD_EVIDENCE_STATUS_TAB, render_strategy_page

render_strategy_page(
    lambda: None,
    lambda: None,
    render_pead_validation_evidence,
)
"""
    ).run(timeout=90)

    assert not app.exception
    evidence_selector = next(
        radio for radio in app.radio if strategy_view.PEAD_EVIDENCE_STATUS_TAB in radio.options
    )
    evidence_selector.set_value(strategy_view.PEAD_EVIDENCE_STATUS_TAB)
    app = app.run(timeout=90)

    assert not app.exception
    assert any(
        subheader.value == view_mod.REVIEW_ONLY_TITLE for subheader in app.subheader
    )
    assert any(
        warning.value == view_mod.REVIEW_ONLY_WARNING for warning in app.warning
    )
    assert any(metric.label == "Events" and metric.value == "233,586" for metric in app.metric)
    assert any(metric.label == "Issuers" and metric.value == "9,969" for metric in app.metric)
    assert any(
        metric.label == "Retained Sessions" and metric.value == "2,552"
        for metric in app.metric
    )
    assert any(
        "not an alpha verdict" in markdown.value
        for markdown in app.markdown
    )


def test_reader_has_no_provider_parquet_or_pead_recomputation_path() -> None:
    source = Path("views/pead_validation_evidence.py").read_text(encoding="utf-8")
    forbidden_tokens = (
        "yfinance",
        "requests",
        "urlopen",
        "read_parquet",
        "duckdb",
        "polars",
        "pandas",
        "scripts.pead",
        "strategies.pead",
    )
    for token in forbidden_tokens:
        assert token not in source
