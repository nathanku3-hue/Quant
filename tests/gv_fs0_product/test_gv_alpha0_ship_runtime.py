"""Shipment-runtime tests for one complete GV-ALPHA0 user workflow."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from core.gv_alpha0_ship_runtime import (
    CASE_RELATIVE_DIR,
    GvAlpha0ShipRuntimeError,
    RUNTIME_HOME_ENV,
    SEALED_CASE_FILES,
    WORKSPACE_MARKER,
    default_runtime_root,
    prepare_runtime_workspace,
)
from core.gv_v2_alpha0_case_close import (
    FUNCTIONAL_STAGE_OPERABLE,
    FUNCTIONAL_STAGE_PRE_ADJUDICATION,
    OPERATOR_CONFIRMATION_PHRASE,
)
from views.gv_alpha0_case_workspace import (
    apply_operator_confirmation,
    load_workspace_model,
)

ROOT = Path(__file__).resolve().parents[2]


def test_fresh_workspace_seeds_only_verified_pre_adjudication_state(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime"
    workspace = prepare_runtime_workspace(
        bundle_root=ROOT, runtime_root=runtime_root
    )

    assert workspace.initialized is True
    assert workspace.root == runtime_root.absolute()
    assert (runtime_root / WORKSPACE_MARKER).is_file()
    for filename in SEALED_CASE_FILES:
        assert (runtime_root / CASE_RELATIVE_DIR / filename).is_file()
    assert not (runtime_root / CASE_RELATIVE_DIR / "operator_confirmation.json").exists()
    assert not (runtime_root / CASE_RELATIVE_DIR / "result.json").exists()
    assert not (
        runtime_root
        / "data/gv_v2_b0b/mu_0000723125-26-000015/research_decision.json"
    ).exists()
    assert not (
        runtime_root
        / "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/operator_decision_capture.json"
    ).exists()

    model = load_workspace_model(root=runtime_root, verify=True)
    assert model["functional_stage"] == FUNCTIONAL_STAGE_PRE_ADJUDICATION
    assert model["seal_verified_on_load"] is True
    assert model["awaiting_operator_confirmation"] is True


def test_confirm_persists_and_reopens_without_reset(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    first = prepare_runtime_workspace(bundle_root=ROOT, runtime_root=runtime_root)

    confirmed = apply_operator_confirmation(
        root=runtime_root,
        adjudicator_label="PILOT_OPERATOR",
        confirmation_phrase=OPERATOR_CONFIRMATION_PHRASE,
        confirmed_at="2026-07-28T04:00:00.000000Z",
    )
    result_path = runtime_root / CASE_RELATIVE_DIR / "result.json"
    result_bytes = result_path.read_bytes()
    assert confirmed["functional_stage"] == FUNCTIONAL_STAGE_OPERABLE

    second = prepare_runtime_workspace(bundle_root=ROOT, runtime_root=runtime_root)
    reopened = load_workspace_model(root=runtime_root, verify=True)

    assert first.seed_digest == second.seed_digest
    assert second.initialized is False
    assert result_path.read_bytes() == result_bytes
    assert reopened["functional_stage"] == FUNCTIONAL_STAGE_OPERABLE
    assert reopened["operator_confirmation_present"] is True
    assert reopened["seal_verified_on_load"] is True


def test_startup_fails_closed_on_seed_tamper(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    prepare_runtime_workspace(bundle_root=ROOT, runtime_root=runtime_root)
    auth = (
        runtime_root
        / "data/gv_v2_b0b/mu_0000723125-26-000015/access_authorization.json"
    )
    auth.write_text(auth.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(GvAlpha0ShipRuntimeError, match="SEED_TAMPERED"):
        prepare_runtime_workspace(bundle_root=ROOT, runtime_root=runtime_root)


def test_startup_refuses_unmanaged_nonempty_root(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    (runtime_root / "unrelated.txt").write_text("do not overwrite", encoding="utf-8")

    with pytest.raises(GvAlpha0ShipRuntimeError, match="UNMANAGED_RUNTIME_ROOT_NOT_EMPTY"):
        prepare_runtime_workspace(bundle_root=ROOT, runtime_root=runtime_root)
    assert (runtime_root / "unrelated.txt").read_text(encoding="utf-8") == "do not overwrite"


@pytest.mark.skipif(os.name != "nt", reason="Windows junction regression")
def test_runtime_parent_junction_into_bundle_is_refused(tmp_path: Path) -> None:
    junction = tmp_path / "bundle-route"
    runtime_name = f"runtime-{tmp_path.name}"
    routed_target = ROOT / runtime_name
    assert not routed_target.exists()
    command = [
        os.environ.get("COMSPEC", "cmd.exe"),
        "/d",
        "/c",
        "mklink",
        "/J",
        str(junction),
        str(ROOT),
    ]
    created = subprocess.run(command, capture_output=True, text=True, check=False)
    if created.returncode != 0:
        pytest.skip(f"junction creation unavailable: {created.stderr or created.stdout}")
    try:
        with pytest.raises(GvAlpha0ShipRuntimeError, match="RUNTIME_INSIDE_BUNDLE"):
            prepare_runtime_workspace(
                bundle_root=ROOT, runtime_root=junction / runtime_name
            )
        assert not routed_target.exists()
    finally:
        junction.rmdir()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction regression")
def test_runtime_seed_junction_escape_is_refused(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    prepare_runtime_workspace(bundle_root=ROOT, runtime_root=runtime_root)

    source_dir = runtime_root / "data/gv_v2_b0b"
    outside_dir = tmp_path / "outside-b0b"
    shutil.copytree(source_dir, outside_dir)
    shutil.rmtree(source_dir)
    command = [
        os.environ.get("COMSPEC", "cmd.exe"),
        "/d",
        "/c",
        "mklink",
        "/J",
        str(source_dir),
        str(outside_dir),
    ]
    created = subprocess.run(command, capture_output=True, text=True, check=False)
    if created.returncode != 0:
        pytest.skip(f"junction creation unavailable: {created.stderr or created.stdout}")
    try:
        with pytest.raises(GvAlpha0ShipRuntimeError, match="RUNTIME_SEED_PATH_ESCAPE"):
            prepare_runtime_workspace(bundle_root=ROOT, runtime_root=runtime_root)
    finally:
        source_dir.rmdir()


def test_runtime_home_environment_override(tmp_path: Path) -> None:
    selected = tmp_path / "selected"
    resolved = default_runtime_root(env={RUNTIME_HOME_ENV: str(selected)})
    assert resolved == selected
