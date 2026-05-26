from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.boot_status import BootStatus
from core import data_readiness_gate as gate


def test_write_boot_status_allows_only_boot_status_path(tmp_path: Path) -> None:
    status = {"schema_version": gate.SCHEMA_VERSION, "overall_status": "PASS"}

    with pytest.raises(ValueError):
        gate.write_boot_status("docs/context/not_boot_status.json", status, repo_root=tmp_path)

    assert not (tmp_path / "docs/context/not_boot_status.json").exists()


def test_write_boot_status_uses_atomic_target_and_leaves_no_temp_file(tmp_path: Path) -> None:
    status = {"schema_version": gate.SCHEMA_VERSION, "overall_status": "PASS"}

    outcome = gate.write_boot_status(gate.DEFAULT_STATUS_PATH, status, repo_root=tmp_path)

    status_path = tmp_path / gate.DEFAULT_STATUS_PATH
    assert outcome == "written"
    assert status_path.exists()
    boot_status = BootStatus.from_json_dict(json.loads(status_path.read_text(encoding="utf-8")))
    assert boot_status.schema_version == "boot-status/v1"
    assert boot_status.metadata["data_readiness"]["schema_version"] == gate.SCHEMA_VERSION
    assert list(status_path.parent.glob("*.tmp")) == []


def test_boot_write_snapshot_allows_only_status_json_delta(tmp_path: Path) -> None:
    before = gate.capture_boot_write_snapshot(tmp_path)
    gate.write_boot_status(
        gate.DEFAULT_STATUS_PATH,
        {"schema_version": gate.SCHEMA_VERSION, "overall_status": "PASS"},
        repo_root=tmp_path,
    )
    after = gate.capture_boot_write_snapshot(tmp_path)

    diff = gate.diff_boot_write_snapshot(before, after)

    assert diff["status"] == "PASS"
    assert diff["allowed_changed"] == [gate.DEFAULT_STATUS_PATH.as_posix()]
    assert diff["disallowed_changed"] == []
    assert diff["post_boot_only_allowed_delta"] is True


def test_boot_write_snapshot_rejects_disallowed_context_delta(tmp_path: Path) -> None:
    docs_context = tmp_path / "docs/context"
    docs_context.mkdir(parents=True)
    current = docs_context / "current_context.json"
    current.write_text('{"old": true}\n', encoding="utf-8")

    before = gate.capture_boot_write_snapshot(tmp_path)
    current.write_text('{"mutated": true}\n', encoding="utf-8")
    after = gate.capture_boot_write_snapshot(tmp_path)

    diff = gate.diff_boot_write_snapshot(before, after)

    assert diff["status"] == "FAIL"
    assert diff["disallowed_changed"] == ["docs/context/current_context.json"]


def test_boot_write_snapshot_rejects_temp_residue_in_guarded_data_roots(tmp_path: Path) -> None:
    before = gate.capture_boot_write_snapshot(tmp_path)
    residue_paths = [
        tmp_path / "data/runtime_cache/strategy_replay/.artifact.parquet.123.tmp",
        tmp_path / "data/candidate_cards/.card.json.123.tmp",
        tmp_path / "data/processed/.prices.parquet.123.tmp",
    ]
    for path in residue_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("partial", encoding="utf-8")
    after = gate.capture_boot_write_snapshot(tmp_path)

    diff = gate.diff_boot_write_snapshot(before, after)

    assert diff["status"] == "FAIL"
    assert diff["disallowed_changed"] == [
        "data/candidate_cards/.card.json.123.tmp",
        "data/processed/.prices.parquet.123.tmp",
        "data/runtime_cache/strategy_replay/.artifact.parquet.123.tmp",
    ]


def test_noncanonical_runtime_boot_status_path_is_not_an_allowed_write() -> None:
    before = gate.capture_boot_write_snapshot(Path("."))
    after = dict(before)
    forbidden_path = "docs/context/" + gate.DEFAULT_STATUS_PATH.name
    after[forbidden_path] = (17, 123, False)

    diff = gate.diff_boot_write_snapshot(before, after)

    assert diff["status"] == "FAIL"
    assert diff["allowed_changed"] == []
    assert diff["disallowed_changed"] == [forbidden_path]


def test_runtime_boot_status_path_is_allowed_only_when_schema_valid() -> None:
    before = gate.capture_boot_write_snapshot(Path("."))
    after = dict(before)
    canonical_path = gate.DEFAULT_STATUS_PATH.as_posix()
    after[canonical_path] = (17, 123, False)

    diff = gate.diff_boot_write_snapshot(before, after)

    assert diff["status"] == "FAIL"
    assert diff["allowed_changed"] == []
    assert diff["invalid_allowed_writes"] == [canonical_path]
    assert diff["disallowed_changed"] == [canonical_path]
