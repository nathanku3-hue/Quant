"""Deterministic package and fresh-extraction smoke for GV-ALPHA0."""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

from scripts.build_gv_alpha0_release import ARCHIVE_PREFIX, build_release

ROOT = Path(__file__).resolve().parents[2]


def test_ci_custody_evidence_stays_outside_checkout() -> None:
    workflow = (ROOT / ".github/workflows/gv-fs0-product.yml").read_text(
        encoding="utf-8"
    )
    assert 'Path(os.environ["RUNNER_TEMP"])' in workflow
    assert '/ "gv-fs0-environment-custody.json"' in workflow
    assert 'path: ${{ runner.temp }}/gv-fs0-environment-custody.json' in workflow
    assert 'Path("gv-fs0-environment-custody.json").write_text' not in workflow


def test_release_archive_is_reproducible_and_narrow(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first = build_release(output_dir=first_dir, allow_dirty=True)
    second = build_release(output_dir=second_dir, allow_dirty=True)

    first_zip = first_dir / str(first["artifact"])
    second_zip = second_dir / str(second["artifact"])
    assert first["artifact_sha256"] == second["artifact_sha256"]
    assert first_zip.read_bytes() == second_zip.read_bytes()

    with zipfile.ZipFile(first_zip) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert all(name.startswith(f"{ARCHIVE_PREFIX}/") for name in names)
        relative = [name.removeprefix(f"{ARCHIVE_PREFIX}/") for name in names]
        assert "RELEASE_MANIFEST.json" in relative
        assert "launch_alpha.py" in relative
        assert "scripts/smoke_gv_alpha0_release.py" in relative
        assert "contracts/gv_fs0/v1/gv_fs0_freeze_manifest_v1.json" not in relative
        assert "contracts/gv_fs0/v1/vectors/gv_fs0_canonical_vectors_v1.json" not in relative
        assert (
            "contracts/gv_fs0/v1/registries/gv_fs0_operational_error_registry_v1.json"
            not in relative
        )
        assert not any(
            name.startswith(
                (
                    "research/",
                    "strategies/",
                    "execution/",
                    "dashboard",
                    "tests/",
                    "docs/saw_reports/",
                )
            )
            for name in relative
        )
        assert b"\r\n" not in archive.read(f"{ARCHIVE_PREFIX}/alpha_app.py")
        windows_wrapper = archive.read(f"{ARCHIVE_PREFIX}/run-windows.cmd")
        assert b"\r\n" in windows_wrapper
        assert b"\n" not in windows_wrapper.replace(b"\r\n", b"")
        manifest = json.loads(
            archive.read(f"{ARCHIVE_PREFIX}/RELEASE_MANIFEST.json")
        )
        assert manifest["version"] == "0.1.0"
        assert manifest["source_commit"]
        assert manifest["seed_digest"]
        assert manifest["claim"].startswith("usable certified paper-decision")


def _extract_release(tmp_path: Path) -> Path:
    output_dir = tmp_path / "dist"
    record = build_release(output_dir=output_dir, allow_dirty=True)
    archive_path = output_dir / str(record["artifact"])
    extract_dir = tmp_path / "extract"
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(extract_dir)
    return extract_dir / ARCHIVE_PREFIX


def test_extracted_release_refuses_tampered_seed_before_initialization(
    tmp_path: Path,
) -> None:
    product_root = _extract_release(tmp_path)
    seed = (
        product_root
        / "data/gv_v2_b0b/mu_0000723125-26-000015/access_authorization.json"
    )
    seed.write_bytes(seed.read_bytes() + b"\n")
    runtime_root = tmp_path / "runtime"
    code = (
        "import sys; from pathlib import Path; "
        "from core.gv_alpha0_ship_runtime import prepare_runtime_workspace; "
        "prepare_runtime_workspace(bundle_root=Path.cwd(), runtime_root=Path(sys.argv[1]))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code, str(runtime_root)],
        cwd=product_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert completed.returncode != 0
    assert "ALPHA0_SHIP_RELEASE_FILE_TAMPERED" in completed.stderr
    assert not runtime_root.exists()


def test_extracted_release_refuses_missing_manifest_before_initialization(
    tmp_path: Path,
) -> None:
    product_root = _extract_release(tmp_path)
    (product_root / "RELEASE_MANIFEST.json").unlink()
    (product_root / ".git").write_text("gitdir: missing-gitdir\n", encoding="utf-8")
    runtime_root = tmp_path / "runtime"
    code = (
        "import sys; from pathlib import Path; "
        "from core.gv_alpha0_ship_runtime import prepare_runtime_workspace; "
        "prepare_runtime_workspace(bundle_root=Path.cwd(), runtime_root=Path(sys.argv[1]))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code, str(runtime_root)],
        cwd=product_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert completed.returncode != 0
    assert "ALPHA0_SHIP_RELEASE_MANIFEST_MISSING" in completed.stderr
    assert not runtime_root.exists()


def test_extracted_release_completes_fresh_machine_smoke(tmp_path: Path) -> None:
    product_root = _extract_release(tmp_path)
    completed = subprocess.run(
        [sys.executable, "scripts/smoke_gv_alpha0_release.py"],
        cwd=product_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    assert result["status"] == "PASS"
    assert result["functional_stage"] == "CERTIFIED_MULTI_SOURCE_CASE_OPERABLE"
    assert result["portfolio_action"] == "NO_POSITION"
