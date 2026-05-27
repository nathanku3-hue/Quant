from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.governance_preflight import REQUIRED_CANDIDATE_FLAGS, run_governance_preflight


PYTHON = Path(r"E:\Code\Quant\.venv\Scripts\python.exe")


def _write_candidate(
    root: Path,
    card: dict,
    *,
    manifest_uri: str | None = None,
    manifest_artifact_uri: str | None = None,
) -> tuple[Path, Path]:
    card_dir = root / "data" / "candidate_cards"
    card_dir.mkdir(parents=True, exist_ok=True)
    card_path = card_dir / "TEST_candidate_card_v0.json"
    manifest_path = card_dir / "TEST_candidate_card_v0.manifest.json"
    card["manifest_uri"] = manifest_uri or manifest_path.relative_to(root).as_posix()
    card_path.write_text(json.dumps(card, indent=2, sort_keys=True), encoding="utf-8")
    manifest = {
        "artifact_uri": manifest_artifact_uri
        if manifest_artifact_uri is not None
        else card_path.relative_to(root).as_posix(),
        "artifact_sha256": hashlib.sha256(card_path.read_bytes()).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return card_path, manifest_path


def _base_card() -> dict:
    return {
        "candidate_id": "TEST",
        "ticker": "TST",
        "company_name": "Test Research Object",
        "theme": "test-research-theme",
        "supercycle_family_id": "TEST_RESEARCH_FAMILY",
        "candidate_status": "candidate_card_only",
        "created_at": "2026-05-26T00:00:00+08:00",
        "created_by": "governance_preflight_test",
        "source_quality_summary": {
            "observed": [],
            "estimated": [],
            "inferred": [],
            "research_only": ["test fixture"],
            "not_canonical": [],
            "missing": [],
            "stale": [],
            "forbidden": [],
            "canonical_sources": [],
        },
        "state_machine_version": "test_state_machine_v0",
        "primary_alpha": {
            "thesis_summary": "Research-only fixture.",
            "evidence_present": [],
            "evidence_missing": [],
            "thesis_breakers": [],
        },
        "secondary_alpha": {
            "observed_signals_available": [],
            "blocked_signals_due_to_provider_gap": [
                {"signal_family": "IV_VOL_INTELLIGENCE"},
                {"signal_family": "OPTIONS_WHALE_RADAR"},
                {"signal_family": "GAMMA_DEALER_MAP"},
            ],
        },
        "state_mapping": {
            "initial_state": "THESIS_CANDIDATE",
            "allowed_next_states": ["EVIDENCE_BUILDING"],
            "forbidden_jumps": [
                "THESIS_CANDIDATE -> BUYING_RANGE",
                "THESIS_CANDIDATE -> ADD_ON_SETUP",
                "THESIS_CANDIDATE -> LET_WINNER_RUN",
                "THESIS_CANDIDATE -> TRIM_OPTIONAL",
            ],
        },
        "risk_discipline": {},
        "governance": dict(REQUIRED_CANDIDATE_FLAGS),
        "forbidden_outputs": {
            "no_score": True,
            "no_rank": True,
            "no_buy_sell_signal": True,
            "no_buying_range": True,
            "no_alert": True,
            "no_broker_action": True,
        },
        "forbidden_use": ["buy/sell/hold output is prohibited"],
    }


def test_scanner_does_not_import_boot_preflight_module() -> None:
    source = Path("scripts/governance_preflight.py").read_text(encoding="utf-8")
    test_source = Path("tests/test_boot_preflight_governance.py").read_text(encoding="utf-8")
    boot_import = "from scripts import " + "boot_preflight"

    assert "scripts.boot_preflight" not in source
    assert boot_import not in test_source


def test_artifact_drift_requires_integrated_governance_files(tmp_path: Path) -> None:
    (tmp_path / "governance_gate_v0.patch").write_text("reference patch only\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs" / "architecture").mkdir(parents=True)
    (tmp_path / "opportunity_engine").mkdir()
    (tmp_path / "scripts" / "governance_preflight.py").write_text("# scanner\n", encoding="utf-8")
    (tmp_path / "scripts" / "boot_preflight.py").write_text(
        "run_governance_preflight\nchecks['governance']\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "architecture" / "governance_boundary_policy.md").write_text("# policy\n", encoding="utf-8")
    (tmp_path / "opportunity_engine" / "candidate_card_schema.py").write_text(
        '"governance"\n"no_buying_range"\n',
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_boot_preflight_governance.py").write_text("# tests\n", encoding="utf-8")

    result = run_governance_preflight(tmp_path)

    assert result.passed, [finding.format() for finding in result.findings]


def test_artifact_drift_fails_when_patch_exists_without_standalone_files(tmp_path: Path) -> None:
    (tmp_path / "governance_gate_v0.patch").write_text("reference patch only\n", encoding="utf-8")

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert any(
        finding.code == "GOV-000" and "GOVERNANCE_ARTIFACT_NOT_APPLIED" in finding.message
        for finding in result.findings
    )


def test_exact_neutral_research_console_labels_are_allowed(tmp_path: Path) -> None:
    (tmp_path / "views").mkdir()
    (tmp_path / "views" / "optimizer_view.py").write_text(
        'REPLAY = "Replay allocation snapshot"\n'
        'CURRENT = "Current allocation snapshot"\n'
        'LIFECYCLE = "Historical Replay Lifecycle Events"\n',
        encoding="utf-8",
    )
    (tmp_path / "views" / "page_registry.py").write_text(
        'PAGES = ["Research Portfolio / Replay Allocation", "Strategy Research Replay"]\n',
        encoding="utf-8",
    )
    (tmp_path / "dashboard.py").write_text(
        'TITLE = "Research Portfolio / Replay Allocation"\n'
        'PAGE_TITLE = "Strategy Research Replay"\n'
        'EVENTS = "Historical Replay Lifecycle Events"\n',
        encoding="utf-8",
    )

    result = run_governance_preflight(tmp_path)

    assert result.passed, [finding.format() for finding in result.findings]
    assert result.status == "PASS"
    assert not result.findings


@pytest.mark.parametrize(
    "phrase",
    [
        "Strong Buy",
        "BUY AGGRESSIVE",
        "Action Status: Buy",
        "investment recommendation",
        "trade alert",
        "broker order",
        "Generate Option Yield",
        "Buy Zone confirmed.",
        "Action Report",
    ],
)
def test_advisory_or_action_ui_terms_fail_closed(tmp_path: Path, phrase: str) -> None:
    (tmp_path / "dashboard.py").write_text(
        f'import streamlit as st\nst.markdown("{phrase}")\n',
        encoding="utf-8",
    )

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert result.status == "FAIL"
    assert any(finding.code == "GOV-002" and phrase.lower() in finding.message.lower() for finding in result.findings)


@pytest.mark.parametrize("phrase", ["Strong\nBuy", "BUY   AGGRESSIVE", "Action\nStatus: Buy"])
def test_action_ui_terms_fail_closed_with_whitespace_variants(tmp_path: Path, phrase: str) -> None:
    (tmp_path / "dashboard.py").write_text(
        f'import streamlit as st\nst.markdown({phrase!r})\n',
        encoding="utf-8",
    )

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert result.status == "FAIL"
    assert any(finding.code == "GOV-002" for finding in result.findings)


@pytest.mark.parametrize(
    "phrase",
    [
        "Portfolio & Allocation",
        "Entry/Exit Strategy",
        "Entry/Exit Events",
        "ENTER/EXIT Events",
        "ENTER event",
        "EXIT event",
        "Strategy Research Replay",
        "Historical Replay Lifecycle Events",
        "Replay allocation snapshot",
        "Current allocation snapshot",
    ],
)
def test_exact_research_console_labels_are_allowed(tmp_path: Path, phrase: str) -> None:
    (tmp_path / "dashboard.py").write_text(
        f'import streamlit as st\nst.markdown("{phrase}")\n',
        encoding="utf-8",
    )

    result = run_governance_preflight(tmp_path)

    assert result.passed, [finding.format() for finding in result.findings]
    assert result.status == "PASS"


@pytest.mark.parametrize(
    "phrase",
    [
        "Portfolio & Allocation action panel",
        "Entry/Exit Strategy action panel",
        "Entry/Exit Events action panel",
        "ENTER/EXIT Events action panel",
        "ENTER event action panel",
        "EXIT event action panel",
    ],
)
def test_research_console_labels_are_exact_only(tmp_path: Path, phrase: str) -> None:
    (tmp_path / "dashboard.py").write_text(
        f'import streamlit as st\nst.markdown("{phrase}")\n',
        encoding="utf-8",
    )

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert result.status == "FAIL"
    assert any(finding.code == "GOV-002" for finding in result.findings)


def test_internal_replay_codes_are_allowed_when_not_display_phrases(tmp_path: Path) -> None:
    (tmp_path / "dashboard.py").write_text(
        'actions = {"BUY", "SELL", "ENTER", "EXIT"}\n'
        'allowed = "BUY" in actions and "SELL" in actions\n',
        encoding="utf-8",
    )

    result = run_governance_preflight(tmp_path)

    assert result.passed, [finding.format() for finding in result.findings]


def test_dynamic_display_action_states_fail_closed(tmp_path: Path) -> None:
    (tmp_path / "views").mkdir()
    (tmp_path / "views" / "detail_view.py").write_text(
        'state = {"state": "BUY", "desc": "Research candidate"}\n',
        encoding="utf-8",
    )

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert any(finding.code == "GOV-002" and "dynamic display value" in finding.message for finding in result.findings)


def test_candidate_card_requires_governance_block(tmp_path: Path) -> None:
    card = _base_card()
    card.pop("governance")
    _write_candidate(tmp_path, card)

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert any(finding.code == "GOV-003" and "governance object" in finding.message for finding in result.findings)


def test_candidate_card_requires_no_buying_range_flag(tmp_path: Path) -> None:
    card = _base_card()
    card["governance"].pop("no_buying_range")
    _write_candidate(tmp_path, card)

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert any("governance.no_buying_range" in finding.message for finding in result.findings)


def test_candidate_card_forbidden_fields_fail_closed(tmp_path: Path) -> None:
    card = _base_card()
    card["primary_alpha"] = {"factor_score": 0.91}
    _write_candidate(tmp_path, card)

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert any(finding.code == "GOV-004" and "factor_score" in finding.message for finding in result.findings)


def test_candidate_card_manifest_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    card_path, manifest_path = _write_candidate(tmp_path, _base_card())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifact_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert any(finding.code == "GOV-008" and "sha256" in finding.message for finding in result.findings)
    assert card_path.exists()


def test_candidate_card_malformed_schema_rejected_by_canonical_validator(tmp_path: Path) -> None:
    card = _base_card()
    card.pop("company_name")
    _write_candidate(tmp_path, card)

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert any(
        finding.code == "GOV-003"
        and "canonical candidate-card schema rejected card" in finding.message
        and "company_name" in finding.message
        for finding in result.findings
    )


def test_candidate_card_rejects_off_sibling_manifest_uri(tmp_path: Path) -> None:
    _write_candidate(
        tmp_path,
        _base_card(),
        manifest_uri="data/candidate_cards/nested/TEST_candidate_card_v0.manifest.json",
    )

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert any(finding.code == "GOV-008" and "manifest_uri must equal sibling manifest path" in finding.message for finding in result.findings)


def test_candidate_card_rejects_wrong_sibling_manifest_uri(tmp_path: Path) -> None:
    _write_candidate(
        tmp_path,
        _base_card(),
        manifest_uri="data/candidate_cards/OTHER_candidate_card_v0.manifest.json",
    )

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert any(
        finding.code == "GOV-008" and "manifest_uri must equal sibling manifest path" in finding.message
        for finding in result.findings
    )


def test_candidate_card_manifest_requires_artifact_uri(tmp_path: Path) -> None:
    _card_path, manifest_path = _write_candidate(tmp_path, _base_card())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("artifact_uri")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert any(finding.code == "GOV-008" and "artifact_uri is required" in finding.message for finding in result.findings)


def test_runtime_order_flags_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("T0_ORDERS_ENABLED", "true")

    result = run_governance_preflight(tmp_path)

    assert not result.passed
    assert any(finding.code == "GOV-001" and "T0_ORDERS_ENABLED" in finding.message for finding in result.findings)


def test_negated_governance_text_can_mention_prohibited_words(tmp_path: Path) -> None:
    _write_candidate(tmp_path, _base_card())

    result = run_governance_preflight(tmp_path)

    assert result.passed, [finding.format() for finding in result.findings]


def test_json_cli_is_read_only_and_does_not_generate_runtime_status(tmp_path: Path) -> None:
    script_path = Path("scripts/governance_preflight.py").resolve()
    completed = subprocess.run(
        [str(PYTHON), str(script_path), "--repo-root", str(tmp_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["status"] == "PASS"
    assert not (tmp_path / "runtime" / "boot_status_current.json").exists()


def test_json_cli_reports_findings_without_boot_blocking_exit(tmp_path: Path) -> None:
    script_path = Path("scripts/governance_preflight.py").resolve()
    (tmp_path / "dashboard.py").write_text('TITLE = "Strong Buy"\n', encoding="utf-8")

    completed = subprocess.run(
        [str(PYTHON), str(script_path), "--repo-root", str(tmp_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["status"] == "FAIL"
    assert payload["passed"] is False
