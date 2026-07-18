from __future__ import annotations

import ast
import copy
import os
from pathlib import Path
from typing import Any

import pytest

import core.gv_fs0_publish as publication
from core.gv_fs0_bundle import (
    GvFs0BundleError,
    build_certified_bundle,
    certified_bundle_bytes,
    parse_certified_bundle_bytes,
    read_certified_bundle,
    validate_certified_bundle,
)
from core.gv_fs0_canonical import canonical_document_bytes, sha256_bytes
from core.gv_fs0_certify import (
    build_no_position_certified_result,
    build_open_certified_result,
)
from core.gv_fs0_publish import (
    GvFs0PublicationError,
    PUBLICATION_LOCKED,
    PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
    PUBLICATION_RECOVERY_RECORD_FAILED,
    PUBLICATION_TARGET_CHANGED,
    build_default_certified_bundle,
    publish_default_certified_bundle,
)
from views.gv_fs0_portfolio_adapter import (
    GvFs0PresentationError,
    render_gv_fs0_certified_bundle,
)

ROOT = Path(__file__).resolve().parents[2]
PERMANENT_BUNDLE = ROOT / "data" / "gv_fs0" / "gv_fs0_certified_bundle.json"
EXPECTED_BUNDLE_HASH = "527c86b9e50386bf9e5847037642910b47b81697dbf089df3038099feab6282c"
EXPECTED_BUNDLE_ID = "BUNDLE_" + EXPECTED_BUNDLE_HASH
EXPECTED_FILE_SHA256 = "a9dda224da21ab4abfe1f27afdb2875bb34f240d469caf20a90b7e635adb96e5"
EXPECTED_BYTE_LENGTH = 55_774


class FakeRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def subheader(self, body: str) -> None:
        self.calls.append(("subheader", body))

    def table(self, data: Any) -> None:
        self.calls.append(("table", data))

    def caption(self, body: str) -> None:
        self.calls.append(("caption", body))


def _paths(tmp_path: Path) -> tuple[Path, Path]:
    target = tmp_path / "data" / "gv_fs0" / "gv_fs0_certified_bundle.json"
    lock = target.parent / ".gv_fs0_certified_bundle.lock"
    return target, lock


def test_complete_bundle_identity_is_exact_and_deterministic() -> None:
    first = build_default_certified_bundle()
    second = build_default_certified_bundle()
    first_bytes = certified_bundle_bytes(first)
    second_bytes = certified_bundle_bytes(second)

    assert first == second
    assert first_bytes == second_bytes
    assert [row["role"] for row in first["components"]] == ["OPEN", "NO_POSITION"]
    assert first["bundle_hash"] == EXPECTED_BUNDLE_HASH
    assert first["bundle_id"] == EXPECTED_BUNDLE_ID
    assert sha256_bytes(first_bytes) == EXPECTED_FILE_SHA256
    assert len(first_bytes) == EXPECTED_BYTE_LENGTH
    assert parse_certified_bundle_bytes(first_bytes) == first


def test_partial_wrong_order_or_tampered_bundle_fails_closed() -> None:
    opened = build_open_certified_result()
    abstained = build_no_position_certified_result()
    with pytest.raises(GvFs0BundleError, match="BUNDLE_REQUIRES_TWO_COMPONENTS"):
        build_certified_bundle([opened])
    with pytest.raises(GvFs0BundleError, match="COMPONENT_ROLE_INVALID"):
        build_certified_bundle([abstained, opened])

    bundle = build_certified_bundle([opened, abstained])
    tampered_component = copy.deepcopy(bundle)
    tampered_component["components"][0]["snapshots"][-1]["nav"] = "9999"
    with pytest.raises(GvFs0BundleError, match="COMPONENT_HASH_INVALID"):
        validate_certified_bundle(tampered_component)

    tampered_presentation = copy.deepcopy(bundle)
    tampered_presentation["components"][1]["presentation"]["rows"][6]["value"] = "1"
    with pytest.raises(GvFs0BundleError, match="PRESENTATION_HASH_INVALID"):
        validate_certified_bundle(tampered_presentation)

    tampered_bundle = copy.deepcopy(bundle)
    tampered_bundle["bundle_hash"] = "0" * 64
    tampered_bundle["bundle_id"] = "BUNDLE_" + "0" * 64
    with pytest.raises(GvFs0BundleError, match="BUNDLE_HASH_INVALID"):
        validate_certified_bundle(tampered_bundle)


def test_publish_replaces_absent_target_and_loads_exact_bytes(tmp_path: Path) -> None:
    target, lock = _paths(tmp_path)
    result = publish_default_certified_bundle(target=target, lock_path=lock)

    assert result.status == "REPLACED"
    assert result.bundle_hash == EXPECTED_BUNDLE_HASH
    assert result.bundle_id == EXPECTED_BUNDLE_ID
    assert result.target_file_sha256 == EXPECTED_FILE_SHA256
    assert target.read_bytes() == certified_bundle_bytes(build_default_certified_bundle())
    assert read_certified_bundle(target)["bundle_id"] == EXPECTED_BUNDLE_ID
    assert not lock.exists()
    assert not list(target.parent.glob("*.tmp"))


def test_identical_candidate_is_idempotent_without_mtime_change(tmp_path: Path) -> None:
    target, lock = _paths(tmp_path)
    publish_default_certified_bundle(target=target, lock_path=lock)
    before = target.stat().st_mtime_ns
    result = publish_default_certified_bundle(target=target, lock_path=lock)

    assert result.status == "IDEMPOTENT"
    assert target.stat().st_mtime_ns == before
    assert not lock.exists()


def test_existing_lock_blocks_without_age_or_pid_recovery(tmp_path: Path) -> None:
    target, lock = _paths(tmp_path)
    target.parent.mkdir(parents=True)
    lock.write_bytes(
        b'{"record_version":"GV-FS0-PUBLICATION-RECOVERY-V1",'
        b'"state":"RECOVERY_REQUIRED","target_token":"GV_FS0_CERTIFIED_BUNDLE"}\n'
    )
    os.utime(lock, (1, 1))
    original = lock.read_bytes()

    with pytest.raises(GvFs0PublicationError, match=PUBLICATION_LOCKED) as caught:
        publish_default_certified_bundle(target=target, lock_path=lock)
    assert caught.value.code == PUBLICATION_LOCKED
    assert lock.read_bytes() == original


def test_target_changed_after_observation_is_not_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, lock = _paths(tmp_path)
    target.parent.mkdir(parents=True)
    prior = b'{"state":"prior"}\n'
    concurrent = b'{"state":"concurrent"}\n'
    target.write_bytes(prior)
    real_acquire = publication._acquire_lock

    def mutate_then_lock(path: Path) -> None:
        target.write_bytes(concurrent)
        real_acquire(path)

    monkeypatch.setattr(publication, "_acquire_lock", mutate_then_lock)
    with pytest.raises(GvFs0PublicationError, match=PUBLICATION_TARGET_CHANGED):
        publish_default_certified_bundle(target=target, lock_path=lock)
    assert target.read_bytes() == concurrent
    assert not lock.exists()


def test_pre_replace_failure_preserves_prior_target_and_releases_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, lock = _paths(tmp_path)
    target.parent.mkdir(parents=True)
    prior = b'{"state":"prior"}\n'
    target.write_bytes(prior)

    def fail_replace(_source: Path, _target: Path) -> None:
        raise OSError("injected pre-replace failure")

    monkeypatch.setattr(publication, "_replace_file", fail_replace)
    with pytest.raises(OSError, match="injected pre-replace failure"):
        publish_default_certified_bundle(target=target, lock_path=lock)
    assert target.read_bytes() == prior
    assert not lock.exists()
    assert not list(target.parent.glob("*.tmp"))


def test_post_replace_failure_creates_durable_recovery_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, lock = _paths(tmp_path)
    target.parent.mkdir(parents=True)
    prior = b'{"state":"prior"}\n'
    target.write_bytes(prior)

    def fail_verify(_target: Path, _candidate: bytes) -> str:
        raise GvFs0PublicationError(
            PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
            "injected_post_replace",
        )

    monkeypatch.setattr(publication, "_verify_published_target", fail_verify)
    with pytest.raises(
        GvFs0PublicationError, match=PUBLICATION_POST_REPLACE_VERIFICATION_FAILED
    ):
        publish_default_certified_bundle(target=target, lock_path=lock)

    assert target.read_bytes() != prior
    recovery = canonical_document_bytes(
        publication._recovery_record(
            observed_prebuild_target_hash=sha256_bytes(prior),
            candidate_hash=EXPECTED_FILE_SHA256,
            observed_post_replace_target_hash=EXPECTED_FILE_SHA256,
            failure_stage="injected_post_replace",
        )
    )
    assert lock.read_bytes() == recovery
    assert b'"state":"RECOVERY_REQUIRED"' in recovery


def test_recovery_record_failure_retains_existing_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, lock = _paths(tmp_path)

    def fail_verify(_target: Path, _candidate: bytes) -> str:
        raise GvFs0PublicationError(
            PUBLICATION_POST_REPLACE_VERIFICATION_FAILED,
            "injected_post_replace",
        )

    def fail_recovery(_lock: Path, _record: dict[str, str]) -> None:
        raise OSError("injected recovery failure")

    monkeypatch.setattr(publication, "_verify_published_target", fail_verify)
    monkeypatch.setattr(publication, "_write_recovery_record", fail_recovery)
    with pytest.raises(GvFs0PublicationError, match=PUBLICATION_RECOVERY_RECORD_FAILED):
        publish_default_certified_bundle(target=target, lock_path=lock)
    assert target.exists()
    assert lock.exists()


def test_headless_default_render_reads_published_bytes_for_both_roles(
    tmp_path: Path,
) -> None:
    target, lock = _paths(tmp_path)
    publish_default_certified_bundle(target=target, lock_path=lock)
    renderer = FakeRenderer()
    models = render_gv_fs0_certified_bundle(renderer, bundle_path=target)

    assert [model["title"].rsplit("— ", 1)[-1] for model in models] == [
        "OPEN",
        "NO_POSITION",
    ]
    open_rows = {row["label"]: row["value"] for row in models[0]["rows"]}
    no_position_rows = {
        row["label"]: row["value"] for row in models[1]["rows"]
    }
    assert open_rows["NAV"] == "1044"
    assert open_rows["Shares"] == "10"
    assert no_position_rows["NAV"] == "1000"
    assert no_position_rows["Shares"] == "0"
    assert [name for name, _ in renderer.calls] == [
        "subheader",
        "table",
        "caption",
        "subheader",
        "table",
        "caption",
    ]


def test_default_render_fails_closed_without_valid_bundle(tmp_path: Path) -> None:
    renderer = FakeRenderer()
    missing = tmp_path / "missing.json"
    with pytest.raises(GvFs0PresentationError, match="CERTIFIED_BUNDLE_INVALID"):
        render_gv_fs0_certified_bundle(renderer, bundle_path=missing)

    invalid = tmp_path / "invalid.json"
    invalid.write_bytes(b'{"not":"a bundle"}\n')
    with pytest.raises(GvFs0PresentationError, match="CERTIFIED_BUNDLE_INVALID"):
        render_gv_fs0_certified_bundle(renderer, bundle_path=invalid)


def test_default_dashboard_authority_is_current_decision_only() -> None:
    dashboard_path = ROOT / "dashboard.py"
    tree = ast.parse(dashboard_path.read_text(encoding="utf-8"), filename=str(dashboard_path))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_render_portfolio_allocation_page"
    )
    body = ast.unparse(function)
    assert "render_gv_fs0_current_decision(st)" in body
    assert "render_gv_fs0_certified_bundle(st)" not in body
    for forbidden in (
        "_render_portfolio_builder_section",
        "_ensure_daily_portfolio_replay_context",
        "_render_replay_allocation_snapshot",
        "_render_portfolio_ytd_chart",
        "_render_strategy_replay_section",
        "render_optimizer_view",
    ):
        assert forbidden not in body

    adapter_source = (ROOT / "views" / "gv_fs0_portfolio_adapter.py").read_text(
        encoding="utf-8"
    )
    adapter_tree = ast.parse(adapter_source)
    imports: set[str] = set()
    for node in ast.walk(adapter_tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    assert "core.gv_fs0_bundle" in imports
    assert "core.gv_fs0_current_decision" in imports  # shared canonical reader only
    assert not any(
        name in imports
        for name in (
            "core.gv_fs0_book",
            "core.gv_fs0_certify",
            "core.gv_fs0_publish",
            "core.gv_e0a_operable",
            "strategies.strategy_replay",
        )
    )


def test_tracked_permanent_bundle_matches_current_build() -> None:
    assert PERMANENT_BUNDLE.is_file()
    raw = PERMANENT_BUNDLE.read_bytes()
    assert len(raw) == EXPECTED_BYTE_LENGTH
    assert sha256_bytes(raw) == EXPECTED_FILE_SHA256
    assert raw == certified_bundle_bytes(build_default_certified_bundle())
    assert read_certified_bundle(PERMANENT_BUNDLE)["bundle_id"] == EXPECTED_BUNDLE_ID
