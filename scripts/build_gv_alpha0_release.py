"""Build a deterministic, broker-free GV-ALPHA0 release archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gv_alpha0_ship_runtime import build_seed_manifest
VERSION = "0.1.0"
PRODUCT_NAME = "gv-alpha0-paper-decision"
ARCHIVE_PREFIX = f"{PRODUCT_NAME}-{VERSION}"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)

PACKAGE_FILE_MAP: tuple[tuple[Path, Path], ...] = (
    (Path("alpha_app.py"), Path("alpha_app.py")),
    (Path("launch_alpha.py"), Path("launch_alpha.py")),
    (Path("requirements-release.txt"), Path("requirements-release.txt")),
    (Path("core/__init__.py"), Path("core/__init__.py")),
    (Path("core/gv_alpha0_ship_runtime.py"), Path("core/gv_alpha0_ship_runtime.py")),
    (Path("core/gv_fs0_book.py"), Path("core/gv_fs0_book.py")),
    (Path("core/gv_fs0_bundle.py"), Path("core/gv_fs0_bundle.py")),
    (Path("core/gv_fs0_canonical.py"), Path("core/gv_fs0_canonical.py")),
    (Path("core/gv_fs0_certify.py"), Path("core/gv_fs0_certify.py")),
    (Path("core/gv_fs0_current_decision.py"), Path("core/gv_fs0_current_decision.py")),
    (Path("core/gv_fs0_publish.py"), Path("core/gv_fs0_publish.py")),
    (Path("core/gv_v2_alpha0_case_close.py"), Path("core/gv_v2_alpha0_case_close.py")),
    (
        Path("core/gv_v2_alpha0_source_family_two.py"),
        Path("core/gv_v2_alpha0_source_family_two.py"),
    ),
    (
        Path("core/gv_v2_b0b_official_source_intake.py"),
        Path("core/gv_v2_b0b_official_source_intake.py"),
    ),
    (Path("validation/__init__.py"), Path("validation/__init__.py")),
    (
        Path("validation/gv_fs0_reconstruction.py"),
        Path("validation/gv_fs0_reconstruction.py"),
    ),
    (Path("views/__init__.py"), Path("views/__init__.py")),
    (Path("views/gv_alpha0_case_workspace.py"), Path("views/gv_alpha0_case_workspace.py")),
    (
        Path("scripts/smoke_gv_alpha0_release.py"),
        Path("scripts/smoke_gv_alpha0_release.py"),
    ),
    (Path("release/gv-alpha0/README.md"), Path("README.md")),
    (Path("release/gv-alpha0/ROLLBACK.md"), Path("ROLLBACK.md")),
    (Path("release/gv-alpha0/run-windows.cmd"), Path("run-windows.cmd")),
    (Path("release/gv-alpha0/run-linux.sh"), Path("run-linux.sh")),
)


class ReleaseBuildError(RuntimeError):
    pass


def _canonical_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseBuildError("GV_ALPHA0_RELEASE_GIT_IDENTITY_UNAVAILABLE") from exc


def _source_identity(
    *, allow_dirty: bool, source_commit: str | None = None
) -> tuple[str, str]:
    if source_commit is not None:
        commit = source_commit.strip().lower()
        if len(commit) != 40 or any(ch not in "0123456789abcdef" for ch in commit):
            raise ReleaseBuildError("GV_ALPHA0_RELEASE_SOURCE_COMMIT_INVALID")
        if not allow_dirty:
            raise ReleaseBuildError(
                "GV_ALPHA0_RELEASE_SOURCE_COMMIT_OVERRIDE_REQUIRES_ALLOW_DIRTY"
            )
        return commit, "dirty-candidate"

    commit = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain", "--untracked-files=all")
    if status and not allow_dirty:
        raise ReleaseBuildError("GV_ALPHA0_RELEASE_DIRTY_WORKTREE_REFUSED")
    return commit, "dirty-candidate" if status else "clean"


def _read_required(path: Path) -> bytes:
    absolute = ROOT / path
    if not absolute.is_file():
        raise ReleaseBuildError(f"GV_ALPHA0_RELEASE_FILE_MISSING:{path.as_posix()}")
    return absolute.read_bytes()


def _read_packaged_text(source: Path, target: Path) -> bytes:
    raw = _read_required(source)
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if target.suffix.lower() == ".cmd":
        return normalized.replace(b"\n", b"\r\n")
    return normalized


def _package_payloads(
    *, allow_dirty: bool, source_commit: str | None = None
) -> tuple[dict[str, bytes], dict[str, Any]]:
    commit, tree_state = _source_identity(
        allow_dirty=allow_dirty, source_commit=source_commit
    )
    seed = build_seed_manifest(bundle_root=ROOT)
    payloads: dict[str, bytes] = {}

    for source, target in PACKAGE_FILE_MAP:
        payloads[target.as_posix()] = _read_packaged_text(source, target)
    contract_root = ROOT / "contracts/gv_fs0/v1"
    contract_files = [
        *sorted(
            (contract_root / "schemas").glob("*.schema.json"),
            key=lambda item: item.as_posix(),
        ),
        contract_root / "tables/gv_fs0_event_ranks_v1.json",
        contract_root / "tables/gv_fs0_generated_event_slots_v1.json",
        contract_root / "tables/gv_fs0_transition_ownership_v1.json",
        contract_root
        / "registries/gv_fs0_certification_failure_registry_v1.json",
    ]
    for source in contract_files:
        if not source.is_file():
            raise ReleaseBuildError(
                f"GV_ALPHA0_RELEASE_CONTRACT_MISSING:{source.relative_to(ROOT).as_posix()}"
            )
        relative = source.relative_to(ROOT)
        payloads[relative.as_posix()] = source.read_bytes()
    for relative_text in seed["files"]:
        relative = Path(relative_text)
        payloads[relative.as_posix()] = _read_required(relative)

    files = {
        name: {"bytes": len(raw), "sha256": _sha256(raw)}
        for name, raw in sorted(payloads.items())
    }
    release_manifest = {
        "schema": "gv_alpha0_release_manifest_v1",
        "product": PRODUCT_NAME,
        "version": VERSION,
        "source_commit": commit,
        "source_tree_state": tree_state,
        "seed_digest": seed["seed_digest"],
        "claim": "usable certified paper-decision product; no decision-improvement or alpha claim",
        "files": files,
    }
    payloads["RELEASE_MANIFEST.json"] = _canonical_json_bytes(release_manifest)
    return payloads, release_manifest


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(f"{ARCHIVE_PREFIX}/{name}", date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    mode = 0o755 if name == "run-linux.sh" else 0o644
    info.external_attr = (mode & 0xFFFF) << 16
    return info


def build_release(
    *,
    output_dir: Path,
    allow_dirty: bool = False,
    source_commit: str | None = None,
) -> dict[str, Any]:
    payloads, manifest = _package_payloads(
        allow_dirty=allow_dirty, source_commit=source_commit
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{ARCHIVE_PREFIX}.zip"

    with zipfile.ZipFile(archive, mode="w", allowZip64=True) as handle:
        for name in sorted(payloads):
            handle.writestr(_zip_info(name), payloads[name])

    archive_bytes = archive.read_bytes()
    archive_hash = _sha256(archive_bytes)
    sha_path = archive.with_suffix(".zip.sha256")
    sha_path.write_text(f"{archive_hash}  {archive.name}\n", encoding="utf-8", newline="\n")

    record = {
        "schema": "gv_alpha0_release_record_v1",
        "product": PRODUCT_NAME,
        "version": VERSION,
        "source_commit": manifest["source_commit"],
        "source_tree_state": manifest["source_tree_state"],
        "seed_digest": manifest["seed_digest"],
        "artifact": archive.name,
        "artifact_bytes": len(archive_bytes),
        "artifact_sha256": archive_hash,
    }
    record_path = output_dir / f"{ARCHIVE_PREFIX}.release.json"
    record_path.write_bytes(_canonical_json_bytes(record))
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--source-commit")
    args = parser.parse_args(argv)
    try:
        record = build_release(
            output_dir=args.output_dir,
            allow_dirty=bool(args.allow_dirty),
            source_commit=args.source_commit,
        )
    except ReleaseBuildError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(record, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
