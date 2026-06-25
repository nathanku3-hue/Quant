from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from scripts import phase60_d341_blocked_audit_review as mod


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "phase60_d341_blocked_audit_review.py"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _make_fixture(tmp_path: Path) -> mod.ReviewConfig:
    preflight_path = tmp_path / "phase60_d340_preflight_20260319_summary.json"
    audit_summary_path = tmp_path / "phase60_governed_audit_summary.json"
    audit_evidence_path = tmp_path / "phase60_governed_audit_evidence.csv"
    audit_delta_path = tmp_path / "phase60_governed_audit_delta.csv"
    output_summary_path = tmp_path / "phase60_d341_review_20260319_summary.json"
    output_findings_path = tmp_path / "phase60_d341_review_20260319_findings.csv"
    output_status_path = tmp_path / "phase60_d341_review_20260319.status.txt"

    _write_json(
        preflight_path,
        {
            "packet_id": mod.EXPECTED_PREFLIGHT_PACKET_ID,
            "passed": True,
            "checks": {
                "PF-01": True,
                "PF-02": True,
                "PF-03": True,
                "PF-04": True,
                "PF-05": True,
                "PF-06": True,
                "SEMANTIC": True,
            },
        },
    )
    _write_json(
        audit_summary_path,
        {
            "packet_id": mod.EXPECTED_AUDIT_PACKET_ID,
            "book_id": mod.EXPECTED_BOOK_ID,
            "status": "blocked",
            "start_date": "2023-01-01",
            "end_date": "2024-12-31",
            "allocator_overlay_applied": False,
            "core_sleeve_included": False,
            "kill_switches_triggered": [mod.EXPECTED_KILL_SWITCH],
            "comparator_error": "Missing 274 return cells on executed exposures.",
            "same_period_c3_5bps": {"baseline_config_id": "", "metrics_c3": {}},
            "same_period_c3_10bps": {"baseline_config_id": "", "metrics_c3": {}},
        },
    )
    _write_csv(
        audit_evidence_path,
        pd.DataFrame(
            [
                {
                    "date": "2023-01-03",
                    "book_id": mod.EXPECTED_BOOK_ID,
                    "gross_exposure": 1.0,
                    "turnover_total": 1.0,
                    "n_active_permnos": 22,
                    "net_ret_5bps": 0.0,
                    "net_ret_10bps": 0.0,
                }
            ]
        ),
    )
    _write_csv(
        audit_delta_path,
        pd.DataFrame(
            [
                {
                    "lane": "5bps_gate",
                    "window_start": "2023-01-01",
                    "window_end": "2024-12-31",
                    "cost_bps": 5.0,
                    "comparator_available": False,
                },
                {
                    "lane": "10bps_sensitivity",
                    "window_start": "2023-01-01",
                    "window_end": "2024-12-31",
                    "cost_bps": 10.0,
                    "comparator_available": False,
                },
            ]
        ),
    )
    return mod.ReviewConfig(
        preflight_path=preflight_path,
        audit_summary_path=audit_summary_path,
        audit_evidence_path=audit_evidence_path,
        audit_delta_path=audit_delta_path,
        output_summary_path=output_summary_path,
        output_findings_path=output_findings_path,
        output_status_path=output_status_path,
    )


def test_run_blocked_audit_review_happy_path(tmp_path: Path) -> None:
    cfg = _make_fixture(tmp_path)

    out = mod.run_blocked_audit_review(cfg)

    assert out["active_phase"] == 60
    assert out["review_status"] == "blocked_confirmed"
    assert out["disposition"] == "evidence_only_hold"
    assert out["missing_executed_exposure_return_cells"] == 274
    assert out["comparator_available"] is False
    assert out["promotion_authorized"] is False
    assert out["remediation_authorized"] is False
    assert out["widening_authorized"] is False
    assert out["allocator_carry_forward_authorized"] is False
    assert out["core_sleeve_inclusion_authorized"] is False
    assert out["research_data_mutation_authorized"] is False
    assert out["kernel_mutation_authorized"] is False

    findings = pd.read_csv(cfg.output_findings_path)
    assert set(findings["status"].tolist()) == {"PASS"}
    assert cfg.output_status_path.read_text(encoding="utf-8").startswith("PASS:")


def test_review_fails_if_audit_not_blocked(tmp_path: Path) -> None:
    cfg = _make_fixture(tmp_path)
    payload = json.loads(cfg.audit_summary_path.read_text(encoding="utf-8"))
    payload["status"] = "ok"
    _write_json(cfg.audit_summary_path, payload)

    with pytest.raises(RuntimeError, match="status must remain blocked"):
        mod.run_blocked_audit_review(cfg)


def test_review_fails_if_ks03_missing(tmp_path: Path) -> None:
    cfg = _make_fixture(tmp_path)
    payload = json.loads(cfg.audit_summary_path.read_text(encoding="utf-8"))
    payload["kill_switches_triggered"] = []
    _write_json(cfg.audit_summary_path, payload)

    with pytest.raises(RuntimeError, match="missing KS-03_same_period_c3_unavailable"):
        mod.run_blocked_audit_review(cfg)


def test_review_fails_if_gap_count_drifted(tmp_path: Path) -> None:
    cfg = _make_fixture(tmp_path)
    payload = json.loads(cfg.audit_summary_path.read_text(encoding="utf-8"))
    payload["comparator_error"] = "Missing 273 return cells on executed exposures."
    _write_json(cfg.audit_summary_path, payload)

    with pytest.raises(RuntimeError, match="exact 274"):
        mod.run_blocked_audit_review(cfg)


def test_review_fails_if_delta_schema_drifted(tmp_path: Path) -> None:
    cfg = _make_fixture(tmp_path)
    _write_csv(
        cfg.audit_delta_path,
        pd.DataFrame(
            [
                {
                    "lane": "5bps_gate",
                    "window_start": "2023-01-01",
                    "window_end": "2024-12-31",
                    "cost_bps": 5.0,
                    "comparator_available": False,
                }
            ]
        ),
    )

    with pytest.raises(RuntimeError, match="must contain exactly the 5bps and 10bps lanes"):
        mod.run_blocked_audit_review(cfg)


def test_review_fails_if_comparator_available(tmp_path: Path) -> None:
    cfg = _make_fixture(tmp_path)
    _write_csv(
        cfg.audit_delta_path,
        pd.DataFrame(
            [
                {
                    "lane": "5bps_gate",
                    "window_start": "2023-01-01",
                    "window_end": "2024-12-31",
                    "cost_bps": 5.0,
                    "comparator_available": False,
                },
                {
                    "lane": "10bps_sensitivity",
                    "window_start": "2023-01-01",
                    "window_end": "2024-12-31",
                    "cost_bps": 10.0,
                    "comparator_available": True,
                },
            ]
        ),
    )

    with pytest.raises(RuntimeError, match="comparator_available false in both lanes"):
        mod.run_blocked_audit_review(cfg)


def test_review_fails_if_evidence_empty(tmp_path: Path) -> None:
    cfg = _make_fixture(tmp_path)
    _write_csv(cfg.audit_evidence_path, pd.DataFrame(columns=mod.EXPECTED_EVIDENCE_COLUMNS))

    with pytest.raises(RuntimeError, match="evidence CSV is empty"):
        mod.run_blocked_audit_review(cfg)


def test_cli_runs_successfully(tmp_path: Path) -> None:
    cfg = _make_fixture(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--preflight-path",
            str(cfg.preflight_path),
            "--audit-summary-path",
            str(cfg.audit_summary_path),
            "--audit-evidence-path",
            str(cfg.audit_evidence_path),
            "--audit-delta-path",
            str(cfg.audit_delta_path),
            "--output-summary-path",
            str(cfg.output_summary_path),
            "--output-findings-path",
            str(cfg.output_findings_path),
            "--output-status-path",
            str(cfg.output_status_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["missing_executed_exposure_return_cells"] == 274
