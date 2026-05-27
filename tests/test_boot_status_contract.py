from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.boot_status import (
    BOOT_STATUS_CONTEXT_SNAPSHOT_PATH,
    BOOT_STATUS_CURRENT_PATH,
    BootContextFlags,
    BootStatus,
    BootStatusValidationError,
    DEFAULT_BOOT_STATUS_PATH,
    NextSafeAction,
    ReadinessCheck,
    checks_allow_safe_boot,
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


def _boot_status(*, safe_boot: bool, source: str = "test") -> BootStatus:
    return make_boot_status(
        source=source,
        flags=BootContextFlags(safe_boot=safe_boot, boot_candidate=True),
        checks=(_ready_check(),),
        generated_at="2026-05-26T00:00:00Z",
    )


def test_boot_status_path_is_runtime_contract() -> None:
    assert BOOT_STATUS_CURRENT_PATH == Path("runtime/boot_status_current.json")
    assert DEFAULT_BOOT_STATUS_PATH == BOOT_STATUS_CURRENT_PATH
    assert BOOT_STATUS_CONTEXT_SNAPSHOT_PATH == Path("docs/context/boot_status_current.json")


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
    assert status.flags.safe_boot is False


def test_safe_boot_flag_is_earned_only_when_all_checks_pass() -> None:
    warn_status = make_boot_status(
        source="test",
        flags=BootContextFlags(safe_boot=True, boot_candidate=True),
        checks=(
            _ready_check(),
            ReadinessCheck(
                id="context_packet_validation",
                label="Context packet validation",
                status="warn",
                severity="degraded",
                summary="Context packet is stale.",
            ),
        ),
        generated_at="2026-05-26T00:00:00Z",
    )
    ready_status = _boot_status(safe_boot=True)

    assert checks_allow_safe_boot(ready_status.checks) is True
    assert checks_allow_safe_boot(warn_status.checks) is False
    assert warn_status.primary_verdict == "degraded"
    assert warn_status.flags.safe_boot is False


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


def test_write_boot_status_file_rejects_docs_context_snapshot_path(tmp_path: Path) -> None:
    status = _boot_status(safe_boot=True)

    with pytest.raises(BootStatusValidationError):
        write_boot_status_file(status, BOOT_STATUS_CONTEXT_SNAPSHOT_PATH, repo_root=tmp_path)

    assert not (tmp_path / BOOT_STATUS_CONTEXT_SNAPSHOT_PATH).exists()


def test_load_boot_status_fail_closed_for_missing_artifact(tmp_path: Path) -> None:
    status = load_boot_status_fail_closed(tmp_path / "missing.json")

    assert status.primary_verdict == "blocked"
    assert status.checks[0].id == "boot_status_artifact"


def test_load_boot_status_without_explicit_path_uses_runtime_canonical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical_path = tmp_path / BOOT_STATUS_CURRENT_PATH
    canonical_path.parent.mkdir(parents=True)
    canonical_path.write_text(_boot_status(safe_boot=True, source="runtime").to_json_text(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    status = load_boot_status_fail_closed()

    assert status.metadata["loaded_from"] == BOOT_STATUS_CURRENT_PATH.as_posix()
    assert status.metadata["source_role"] == "canonical"
    assert status.flags.safe_boot is True
    assert status.primary_verdict == "ready"


def test_docs_context_snapshot_cannot_override_runtime_canonical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical_path = tmp_path / DEFAULT_BOOT_STATUS_PATH
    canonical_path.parent.mkdir(parents=True)
    canonical_path.write_text(_boot_status(safe_boot=True, source="runtime").to_json_text(), encoding="utf-8")
    snapshot_path = tmp_path / BOOT_STATUS_CONTEXT_SNAPSHOT_PATH
    snapshot_path.parent.mkdir(parents=True)
    snapshot_path.write_text(_boot_status(safe_boot=False, source="docs-context").to_json_text(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    status = load_boot_status_fail_closed()

    assert status.metadata["loaded_from"] == DEFAULT_BOOT_STATUS_PATH.as_posix()
    assert status.metadata["source_role"] == "canonical"
    assert status.flags.safe_boot is True
    assert status.primary_verdict == "ready"


def test_missing_runtime_canonical_does_not_fallback_to_docs_context_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_path = tmp_path / BOOT_STATUS_CONTEXT_SNAPSHOT_PATH
    snapshot_path.parent.mkdir(parents=True)
    snapshot_path.write_text(_boot_status(safe_boot=True, source="docs-context").to_json_text(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    status = load_boot_status_fail_closed()

    assert status.primary_verdict == "blocked"
    assert status.flags.safe_boot is False
    assert status.checks[0].id == "boot_status_artifact"
    assert DEFAULT_BOOT_STATUS_PATH.as_posix() in str(status.checks[0].evidence_ref)


def test_docs_context_snapshot_path_is_not_loaded_by_default_source_text() -> None:
    source = Path("core/boot_status.py").read_text(encoding="utf-8")

    assert "LEGACY_BOOT_STATUS_PATH" not in source
    assert "BOOT_STATUS_CONTEXT_SNAPSHOT_PATH.exists()" not in source


def test_schema_file_declares_boot_status_contract() -> None:
    schema = json.loads(Path("docs/context/boot_status_current.schema.json").read_text(encoding="utf-8"))
    check_statuses = schema["properties"]["checks"]["items"]["properties"]["status"]["enum"]

    assert schema["properties"]["schema_version"]["const"] == "boot-status/v1"
    assert {"pass", "warn", "fail", "not_applicable", "deferred"}.issubset(set(check_statuses))
