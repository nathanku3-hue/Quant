from __future__ import annotations

import copy
from pathlib import Path
import shutil
import subprocess

import pytest

import core.gv_one_case_delta as delta
from core.gv_fs0_canonical import canonical_document_bytes


def _copy_allowlist(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for relative in delta.ALLOWED_INPUT_HASHES:
        source = delta.ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for relative in delta.FORBIDDEN_SOURCE_PATHS:
        source = delta.ROOT / relative
        if source.is_file():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return root


def test_canonical_case_artifacts_are_lf_pinned_in_git() -> None:
    paths = [
        delta.DEFAULT_BINDING_PATH,
        delta.DEFAULT_BUNDLE_PATH,
        delta.DEFAULT_PROJECTION_PATH,
        delta.DEFAULT_PROJECTION_MANIFEST_PATH,
    ]
    for path in paths:
        relative = path.relative_to(delta.ROOT).as_posix()
        output = subprocess.check_output(
            ["git", "check-attr", "eol", "--", relative],
            cwd=delta.ROOT,
            text=True,
        )
        assert output.rstrip().endswith(": eol: lf")
        assert b"\r\n" not in path.read_bytes()


def test_tracked_projection_is_exact_deterministic_answer_free_build() -> None:
    bundle, projection, manifest = delta.build_pre_human_artifacts()
    assert delta.DEFAULT_BUNDLE_PATH.read_bytes() == canonical_document_bytes(bundle)
    assert delta.DEFAULT_PROJECTION_PATH.read_bytes() == canonical_document_bytes(projection)
    assert delta.DEFAULT_PROJECTION_MANIFEST_PATH.read_bytes() == canonical_document_bytes(manifest)
    assert projection["claim_state"] == "CLAIM_INSUFFICIENT"
    assert projection["dimension_states"] == {
        "physical_supply_telemetry": "FAIL",
        "industry_economics": "NOT_EVALUATED",
        "business_capture": "NOT_EVALUATED",
        "shareholder_capture": "NOT_EVALUATED",
        "decision_time_price_envelope": "NOT_EVALUATED",
    }
    assert manifest["source_read_set_complete"] is True
    assert {item["path"] for item in manifest["source_read_set"]} == set(delta.ALLOWED_INPUT_HASHES)
    assert manifest["human_result_present"] is False
    assert manifest["publication_authority"] is False


def test_static_binding_has_no_self_referential_candidate_identity() -> None:
    binding = delta.load_experiment_binding()
    assert "candidate_sha" not in binding
    assert "candidate_tree" not in binding
    assert binding["identity_adapter"] == "OPENSSH_SSHSIG_V1"
    assert binding["maximum_budget_seconds_per_arm"] == 3600
    assert binding["early_submission_allowed"] is True
    assert binding["latency_endpoint"] == "NONE"


def test_forbidden_source_path_is_rejected_before_read() -> None:
    reader = delta.AllowlistedSourceReader(delta.ROOT, delta.ALLOWED_INPUT_HASHES)
    with pytest.raises(delta.OneCaseDeltaError, match="SOURCE_PATH_NOT_ALLOWLISTED"):
        reader.read_bytes("data/gv_v2_alpha0/case_mu_g_supply_close_1/export_bundle.json")
    assert reader.read_set == []


def test_mutated_allowlisted_source_fails_hash_custody(tmp_path: Path) -> None:
    root = _copy_allowlist(tmp_path)
    relative = next(iter(delta.ALLOWED_INPUT_HASHES))
    path = root / relative
    path.write_bytes(path.read_bytes() + b"mutation")
    reader = delta.AllowlistedSourceReader(root, delta.ALLOWED_INPUT_HASHES)
    with pytest.raises(delta.OneCaseDeltaError, match="SOURCE_HASH_MISMATCH"):
        reader.read_bytes(relative)


def test_symlink_and_junction_components_fail_before_resolution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_allowlist(tmp_path)
    relative = next(iter(delta.ALLOWED_INPUT_HASHES))
    target = root / relative
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda self: self == target or original(self))
    with pytest.raises(delta.OneCaseDeltaError, match="SOURCE_SYMLINK_PROHIBITED"):
        delta._validate_source_path(root, relative)

    monkeypatch.setattr(Path, "is_symlink", original)
    monkeypatch.setattr(delta, "_is_junction", lambda path: path == target)
    with pytest.raises(delta.OneCaseDeltaError, match="SOURCE_JUNCTION_PROHIBITED"):
        delta._validate_source_path(root, relative)


def test_hardlink_alias_to_forbidden_path_fails(tmp_path: Path) -> None:
    root = _copy_allowlist(tmp_path)
    relative = next(iter(delta.ALLOWED_INPUT_HASHES))
    target = root / relative
    alias = root / "data/gv_v2_alpha0/case_mu_g_supply_close_1/export_bundle.json"
    alias.unlink()
    try:
        alias.hardlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("hard links unavailable")
    with pytest.raises(delta.OneCaseDeltaError, match="SOURCE_HARDLINK_PROHIBITED|SOURCE_ALIASES_FORBIDDEN_PATH"):
        delta._validate_source_path(root, relative)


def test_forbidden_projection_fields_and_values_fail_closed() -> None:
    with pytest.raises(delta.OneCaseDeltaError, match="FORBIDDEN_KEY"):
        delta._scan_forbidden({"adjudication": {}})
    with pytest.raises(delta.OneCaseDeltaError, match="FORBIDDEN_VALUE"):
        delta._scan_forbidden({"note": "NO_POSITION"})
    projection = copy.deepcopy(delta.build_pre_human_artifacts()[1])
    projection.pop("projection_hash")
    delta._scan_forbidden(projection)
