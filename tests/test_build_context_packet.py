from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path

from scripts.build_context_packet import PACKET_KEYS
from scripts.build_context_packet import build_context_packet
from scripts.build_context_packet import render_context_markdown


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_context_packet.py"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_repo_fixture(root: Path, *, include_locked: bool) -> Path:
    repo = root / "repo"
    _write(
        repo / "docs/phase_brief/phase7-brief.md",
        "\n".join(
            [
                "# Phase 7 Brief",
                "",
                "## Status",
                "- Active",
            ]
        ),
    )

    handover_lines = [
        "# Phase 7 Handover",
        "",
        "## New Context Packet",
        "- What was done:",
        "  - Implemented context bootstrap.",
    ]
    if include_locked:
        handover_lines.extend(
            [
                "- What is locked:",
                "  - Schema key order is fixed.",
            ]
        )
    handover_lines.extend(
        [
            "- What remains:",
            "  - Add CI smoke command.",
            "- Immediate first step: .venv\\Scripts\\python scripts/build_context_packet.py",
            "- Next-phase roadmap summary:",
            "  - Add context packet smoke check in CI.",
            "",
            "ConfirmationRequired: YES",
        ]
    )
    _write(repo / "docs/handover/phase7_handover.md", "\n".join(handover_lines))
    _write(repo / "docs/decision log.md", "Decision Log\n")
    _write(repo / "docs/lessonss.md", "Lessons\n")
    return repo


def test_successful_generation_in_temp_repo_fixture(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    json_out = repo / "docs/context/current_context.json"
    md_out = repo / "docs/context/current_context.md"
    assert json_out.exists()
    assert md_out.exists()

    packet = json.loads(json_out.read_text(encoding="utf-8"))
    assert packet["active_phase"] == 7
    assert packet["what_was_done"] == ["Implemented context bootstrap."]

    markdown = md_out.read_text(encoding="utf-8")
    headers = [line.strip() for line in markdown.splitlines() if line.startswith("## ")]
    assert headers == [
        "## What Was Done",
        "## What Is Locked",
        "## What Is Next",
        "## First Command",
    ]


def test_missing_required_section_returns_non_zero(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=False)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "missing required sections" in result.stderr.lower()


def test_schema_keys_present_and_first_command_non_empty(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )

    assert tuple(packet.keys()) == PACKET_KEYS
    assert str(packet["first_command"]).strip()


def test_active_phase_prefers_selected_context_source(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    _write(
        repo / "docs/phase_brief/phase99-brief.md",
        "\n".join(
            [
                "# Phase 99 Brief",
                "",
                "## Status",
                "- Placeholder high-number brief.",
            ]
        ),
    )
    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert int(packet["active_phase"]) == 7


def test_active_phase_promotes_newer_brief_when_context_packet_exists(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    _write(
        repo / "docs/phase_brief/phase99-brief.md",
        "\n".join(
            [
                "# Phase 99 Brief",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Landed newer brief context.",
                "## What Is Locked",
                "- Older handover is superseded.",
                "## What Is Next",
                "- Refresh current context.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python scripts/build_context_packet.py",
                "```",
            ]
        ),
    )
    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert int(packet["active_phase"]) == 99
    assert packet["what_was_done"] == ["Landed newer brief context."]


def test_same_phase_handover_prefers_latest_g_suffix(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    _write(
        repo / "docs/handover/phase7_g1_handover.md",
        "\n".join(
            [
                "# Phase 7 G1 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G1 context.",
                "## What Is Locked",
                "- G1 lock.",
                "## What Is Next",
                "- Start G2.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g1.py -q",
                "```",
            ]
        ),
    )
    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )

    assert int(packet["active_phase"]) == 7
    assert packet["what_was_done"] == ["Completed G1 context."]
    assert str(packet["first_command"]).endswith("tests/test_g1.py -q")


def test_same_phase_handover_sorts_g8_after_g74(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    _write(
        repo / "docs/handover/phase65_g74_dashboard_wireframe_handover.md",
        "\n".join(
            [
                "# Phase 65 G7.4 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G7.4 dashboard context.",
                "## What Is Locked",
                "- Dashboard runtime remains held.",
                "## What Is Next",
                "- Approve G8.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g7_4_dashboard_state_spec.py -q",
                "```",
            ]
        ),
    )
    _write(
        repo / "docs/handover/phase65_g8_supercycle_candidate_card_handover.md",
        "\n".join(
            [
                "# Phase 65 G8 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G8 candidate-card context.",
                "## What Is Locked",
                "- G8 remains card-only.",
                "## What Is Next",
                "- Approve G9.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g8_supercycle_candidate_card.py -q",
                "```",
            ]
        ),
    )
    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )

    assert int(packet["active_phase"]) == 65
    assert packet["what_was_done"] == ["Completed G8 candidate-card context."]
    assert str(packet["first_command"]).endswith("tests/test_g8_supercycle_candidate_card.py -q")


def test_same_phase_handover_sorts_g81_after_g8_but_before_g9(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    _write(
        repo / "docs/handover/phase65_g8_supercycle_candidate_card_handover.md",
        "\n".join(
            [
                "# Phase 65 G8 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G8 context.",
                "## What Is Locked",
                "- G8 lock.",
                "## What Is Next",
                "- Approve G8.1.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g8.py -q",
                "```",
            ]
        ),
    )
    _write(
        repo / "docs/handover/phase65_g81_supercycle_discovery_intake_handover.md",
        "\n".join(
            [
                "# Phase 65 G8.1 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G8.1 intake context.",
                "## What Is Locked",
                "- G8.1 lock.",
                "## What Is Next",
                "- Approve G9.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g8_1.py -q",
                "```",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed G8.1 intake context."]

    _write(
        repo / "docs/handover/phase65_g9_market_behavior_signal_card_handover.md",
        "\n".join(
            [
                "# Phase 65 G9 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G9 signal-card context.",
                "## What Is Locked",
                "- G9 lock.",
                "## What Is Next",
                "- Hold.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g9.py -q",
                "```",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed G9 signal-card context."]


def test_dashboard_ia_handover_can_select_without_phase_prefix(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    _write(
        repo / "docs/handover/phase65_g81a_discovery_drift_handover.md",
        "\n".join(
            [
                "# Phase 65 G8.1A Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G8.1A context.",
                "## What Is Locked",
                "- G8.1A lock.",
                "## What Is Next",
                "- Approve DASH-0.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g8_1a.py -q",
                "```",
            ]
        ),
    )
    _write(
        repo / "docs/handover/dashboard_ia_handover_20260510.md",
        "\n".join(
            [
                "# DASH-0 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed DASH-0 context.",
                "## What Is Locked",
                "- DASH-0 lock.",
                "## What Is Next",
                "- Approve DASH-1.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_build_context_packet.py -q",
                "```",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )

    assert int(packet["active_phase"]) == 65
    assert packet["what_was_done"] == ["Completed DASH-0 context."]


def test_dashboard_ia_handover_sorts_after_g81b_but_before_g9(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    _write(
        repo / "docs/handover/phase65_g81b_pipeline_first_scout_handover.md",
        "\n".join(
            [
                "# Phase 65 G8.1B Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G8.1B context.",
                "## What Is Locked",
                "- G8.1B lock.",
                "## What Is Next",
                "- Approve DASH-0.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g8_1b.py -q",
                "```",
            ]
        ),
    )
    _write(
        repo / "docs/handover/dashboard_ia_handover_20260510.md",
        "\n".join(
            [
                "# DASH-0 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed DASH-0 context.",
                "## What Is Locked",
                "- DASH-0 lock.",
                "## What Is Next",
                "- Approve DASH-1.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_build_context_packet.py -q",
                "```",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed DASH-0 context."]

    _write(
        repo / "docs/handover/phase65_g9_market_behavior_signal_card_handover.md",
        "\n".join(
            [
                "# Phase 65 G9 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G9 context.",
                "## What Is Locked",
                "- G9 lock.",
                "## What Is Next",
                "- Hold.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g9.py -q",
                "```",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed G9 context."]


def test_dash_1_handover_sorts_after_dashboard_ia_but_before_g9(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    _write(
        repo / "docs/handover/dashboard_ia_handover_20260510.md",
        "\n".join(
            [
                "# DASH-0 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed DASH-0 context.",
                "## What Is Locked",
                "- DASH-0 lock.",
                "## What Is Next",
                "- Approve DASH-1.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_build_context_packet.py -q",
                "```",
            ]
        ),
    )
    _write(
        repo / "docs/handover/dash_1_page_registry_shell_handover_20260510.md",
        "\n".join(
            [
                "# DASH-1 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed DASH-1 context.",
                "## What Is Locked",
                "- DASH-1 lock.",
                "## What Is Next",
                "- Approve DASH-2.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_dash_1_page_registry_shell.py -q",
                "```",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed DASH-1 context."]

    _write(
        repo / "docs/handover/phase65_g9_market_behavior_signal_card_handover.md",
        "\n".join(
            [
                "# Phase 65 G9 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G9 context.",
                "## What Is Locked",
                "- G9 lock.",
                "## What Is Next",
                "- Hold.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g9.py -q",
                "```",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed G9 context."]


def test_g82_handover_sorts_after_dash_1_but_before_g9(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    _write(
        repo / "docs/handover/dash_1_page_registry_shell_handover_20260510.md",
        "\n".join(
            [
                "# DASH-1 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed DASH-1 context.",
                "## What Is Locked",
                "- DASH-1 lock.",
                "## What Is Next",
                "- Approve G8.2.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_dash_1_page_registry_shell.py -q",
                "```",
            ]
        ),
    )
    _write(
        repo / "docs/handover/phase65_g82_system_scouted_candidate_card_handover.md",
        "\n".join(
            [
                "# Phase 65 G8.2 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G8.2 context.",
                "## What Is Locked",
                "- G8.2 lock.",
                "## What Is Next",
                "- Approve G9 or G8.3.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g8_2_system_scouted_candidate_card.py -q",
                "```",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed G8.2 context."]

    _write(
        repo / "docs/handover/phase65_g9_market_behavior_signal_card_handover.md",
        "\n".join(
            [
                "# Phase 65 G9 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G9 context.",
                "## What Is Locked",
                "- G9 lock.",
                "## What Is Next",
                "- Hold.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g9.py -q",
                "```",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed G9 context."]


def test_optimizer_diagnostics_handover_sorts_after_g82_but_before_g9(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    _write(
        repo / "docs/handover/phase65_g82_system_scouted_candidate_card_handover.md",
        "\n".join(
            [
                "# Phase 65 G8.2 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G8.2 context.",
                "## What Is Locked",
                "- G8.2 lock.",
                "## What Is Next",
                "- Approve optimizer diagnostics.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g8_2_system_scouted_candidate_card.py -q",
                "```",
            ]
        ),
    )
    _write(
        repo / "docs/handover/phase65_optimizer_core_structured_diagnostics_handover.md",
        "\n".join(
            [
                "# Phase 65 Optimizer Diagnostics Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed optimizer diagnostics context.",
                "## What Is Locked",
                "- Diagnostics-only lock.",
                "## What Is Next",
                "- Hold or plan thesis anchor policy.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_optimizer_core_policy.py -q",
                "```",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed optimizer diagnostics context."]

    _write(
        repo / "docs/handover/phase65_g9_market_behavior_signal_card_handover.md",
        "\n".join(
            [
                "# Phase 65 G9 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed G9 context.",
                "## What Is Locked",
                "- G9 lock.",
                "## What Is Next",
                "- Hold.",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python -m pytest tests/test_g9.py -q",
                "```",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed G9 context."]


def test_markdown_first_command_uses_fenced_block_when_backticks_present() -> None:
    packet = {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_files": ["docs/handover/phase20_handover.md"],
        "active_phase": 20,
        "what_was_done": ["Done"],
        "what_is_locked": ["Locked"],
        "what_is_next": ["Next"],
        "first_command": "Fix in `tests/test_x.py` then rerun.",
        "next_todos": ["Todo"],
    }
    markdown = render_context_markdown(packet)
    assert "## First Command" in markdown
    assert "```text" in markdown


def test_validate_mode_passes_after_build_and_fails_when_missing(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    build = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr

    validate = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo), "--validate"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate.returncode == 0, validate.stderr

    (repo / "docs/context/current_context.md").unlink()
    validate_missing = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo), "--validate"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate_missing.returncode != 0
    assert "missing context markdown artifact" in validate_missing.stderr.lower()


def test_parser_accepts_markdown_style_new_context_packet(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "docs/phase_brief/phase8-brief.md", "# Phase 8 Brief\n")
    _write(
        repo / "docs/handover/phase8_handover.md",
        "\n".join(
            [
                "# Phase 8 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed A",
                "## What Is Locked",
                "- Locked B",
                "## What Is Next",
                "- Do C",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python scripts/build_context_packet.py",
                "```",
                "## Confirmation",
                "ConfirmationRequired: YES",
            ]
        ),
    )
    _write(repo / "docs/decision log.md", "Decision Log\n")
    _write(repo / "docs/lessonss.md", "Lessons\n")

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed A"]
    assert packet["what_is_locked"] == ["Locked B"]
    assert packet["what_is_next"] == ["Do C"]
    assert str(packet["first_command"]).strip() == ".venv\\Scripts\\python scripts/build_context_packet.py"


def test_validate_mode_fails_on_markdown_json_drift(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    build = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr

    md_path = repo / "docs/context/current_context.md"
    drifted = md_path.read_text(encoding="utf-8").replace("Implemented context bootstrap.", "Drifted text.")
    md_path.write_text(drifted, encoding="utf-8")

    validate = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo), "--validate"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate.returncode != 0
    assert "markdown artifact drifted" in validate.stderr.lower()
