from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.boot_status import (
    BOOT_STATUS_CURRENT_PATH,
    BootContextFlags,
    BootStatus,
    BootStatusValidationError,
    NextSafeAction,
    ReadinessCheck,
    deferred_check,
    load_boot_status_fail_closed,
    make_boot_status,
    write_boot_status_file,
)


def _ready_check() -> ReadinessCheck:
    return ReadinessCheck(
        id="boot_core",
        label="Boot core",
        status="pass",
        severity="ready",
        summary="Boot core passed.",
    )


def test_ready_requires_safe_boot_flag() -> None:
    degraded = make_boot_status(
        source="test",
        flags=BootContextFlags(safe_boot=False, boot_candidate=True),
        checks=(_ready_check(),),
        generated_at="2026-05-26T00:00:00Z",
    )
    ready = make_boot_status(
        source="test",
        flags=BootContextFlags(safe_boot=True, boot_candidate=True),
        checks=(_ready_check(),),
        generated_at="2026-05-26T00:00:00Z",
    )

    assert degraded.primary_verdict == "degraded"
    assert ready.primary_verdict == "ready"


def test_deferred_check_degrades_boot_status() -> None:
    status = make_boot_status(
        source="test",
        flags=BootContextFlags(safe_boot=True, boot_candidate=True),
        checks=(
            _ready_check(),
            deferred_check("data_readiness_gate", "Data readiness gate", "Deferred from boot-core v0."),
        ),
        generated_at="2026-05-26T00:00:00Z",
    )

    assert status.primary_verdict == "degraded"
    assert status.flags.safe_boot is True


def test_boot_status_round_trips_json() -> None:
    status = make_boot_status(
        source="test",
        flags=BootContextFlags(safe_boot=False, boot_candidate=True),
        checks=(_ready_check(),),
        generated_at="2026-05-26T00:00:00Z",
    )

    parsed = BootStatus.from_json_dict(json.loads(status.to_json_text()))

    assert parsed == status


def test_next_safe_action_rejects_action_shaped_copy() -> None:
    with pytest.raises(BootStatusValidationError):
        NextSafeAction(
            label="Review buy signal",
            destination="Boot Status",
            reason="Unsafe label.",
        )


def test_write_boot_status_file_is_path_confined(tmp_path: Path) -> None:
    status = make_boot_status(
        source="test",
        flags=BootContextFlags(safe_boot=False, boot_candidate=True),
        checks=(_ready_check(),),
        generated_at="2026-05-26T00:00:00Z",
    )
    result = write_boot_status_file(status, BOOT_STATUS_CURRENT_PATH, repo_root=tmp_path)

    assert result == "written"
    assert (tmp_path / BOOT_STATUS_CURRENT_PATH).exists()

    with pytest.raises(BootStatusValidationError):
        write_boot_status_file(status, tmp_path.parent / "boot_status_current.json", repo_root=tmp_path)


def test_load_boot_status_fail_closed_for_missing_artifact(tmp_path: Path) -> None:
    status = load_boot_status_fail_closed(tmp_path / "missing.json")

    assert status.primary_verdict == "blocked"
    assert status.checks[0].id == "boot_status_artifact"


def test_schema_file_declares_boot_status_contract() -> None:
    schema = json.loads(Path("docs/context/boot_status_current.schema.json").read_text(encoding="utf-8"))
    check_statuses = schema["properties"]["checks"]["items"]["properties"]["status"]["enum"]

    assert schema["properties"]["schema_version"]["const"] == "boot-status/v1"
    assert {"pass", "warn", "fail", "not_applicable", "deferred"}.issubset(set(check_statuses))
