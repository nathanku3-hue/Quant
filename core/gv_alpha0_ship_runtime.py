"""Release workspace bootstrap for the broker-free GV-ALPHA0 product.

The shipped application treats repository/package data as an immutable sample seed
and writes operator state only to a user-writable runtime root. Startup verifies
all seeded bytes and fails closed instead of silently repairing tampered state.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

RUNTIME_HOME_ENV = "GV_ALPHA0_HOME"
WORKSPACE_SCHEMA = "gv_alpha0_release_workspace_v1"
WORKSPACE_MARKER = ".gv-alpha0-workspace.json"
RELEASE_MANIFEST_NAME = "RELEASE_MANIFEST.json"
RELEASE_MANIFEST_SCHEMA = "gv_alpha0_release_manifest_v1"
RELEASE_PRODUCT = "gv-alpha0-paper-decision"

CASE_RELATIVE_DIR = Path("data/gv_v2_alpha0/case_mu_g_supply_close_1")
SOURCE_FILES: tuple[Path, ...] = (
    Path("data/gv_v2_b0b/mu_0000723125-26-000015/access_authorization.json"),
    Path("data/gv_v2_b0b/mu_0000723125-26-000015/raw/0000723125-26-000015-index.htm"),
    Path("data/gv_v2_b0b/mu_0000723125-26-000015/raw/0000723125-26-000015.txt"),
    Path("data/gv_v2_b0b/mu_0000723125-26-000015/raw/mu-20260528.htm"),
    Path(
        "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/access_authorization.json"
    ),
    Path(
        "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/raw/0001045810-26-000052-index.htm"
    ),
    Path(
        "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/raw/0001045810-26-000052.txt"
    ),
    Path(
        "data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/raw/nvda-20260426.htm"
    ),
)
SEALED_CASE_FILES: tuple[str, ...] = (
    "case_manifest.json",
    "coverage.json",
    "case_claim.json",
    "evidence_panel.json",
    "pre_adjudication_seal.json",
)


class GvAlpha0ShipRuntimeError(RuntimeError):
    """Release workspace startup refused."""


@dataclass(frozen=True)
class RuntimeWorkspace:
    root: Path
    case_dir: Path
    initialized: bool
    seed_digest: str
    diagnostics: tuple[str, ...]


def _canonical_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _same_or_within(path: Path, root: Path) -> bool:
    try:
        path_text = os.path.normcase(os.path.abspath(os.fspath(path)))
        root_text = os.path.normcase(os.path.abspath(os.fspath(root)))
        return os.path.commonpath((path_text, root_text)) == root_text
    except ValueError:
        return False


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(callable(is_junction) and is_junction())


def _canonical_existing_directory(path: Path, *, code: str) -> Path:
    try:
        canonical = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise GvAlpha0ShipRuntimeError(code) from exc
    if not canonical.is_dir():
        raise GvAlpha0ShipRuntimeError(code)
    return canonical


def _canonical_candidate(path: Path) -> Path:
    """Resolve every existing ancestor, including Windows junctions."""

    lexical = _absolute_lexical(path)
    cursor = lexical
    missing: list[str] = []
    while not cursor.exists():
        if cursor.is_symlink():
            raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RUNTIME_BROKEN_LINK_REFUSED")
        parent = cursor.parent
        if parent == cursor:
            raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RUNTIME_PATH_UNRESOLVABLE")
        missing.append(cursor.name)
        cursor = parent
    try:
        canonical = cursor.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RUNTIME_PATH_UNRESOLVABLE") from exc
    for name in reversed(missing):
        canonical = canonical / name
    return canonical


def _safe_relative_path(value: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_MANIFEST_PATH_INVALID")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_MANIFEST_PATH_INVALID")
    if pure.as_posix() != value:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_MANIFEST_PATH_INVALID")
    return Path(*pure.parts)


def _confined_existing_file(
    *, root: Path, relative: Path, escape_code: str, missing_code: str
) -> Path:
    candidate = root / relative
    if _is_link_like(candidate):
        raise GvAlpha0ShipRuntimeError(escape_code)
    try:
        canonical = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise GvAlpha0ShipRuntimeError(missing_code) from exc
    if not _same_or_within(canonical, root):
        raise GvAlpha0ShipRuntimeError(escape_code)
    if not canonical.is_file():
        raise GvAlpha0ShipRuntimeError(missing_code)
    return canonical


def _expected_seed_relative_files() -> tuple[Path, ...]:
    return (*SOURCE_FILES, *(CASE_RELATIVE_DIR / name for name in SEALED_CASE_FILES))


def _is_ignored_package_extra(relative: Path) -> bool:
    return (
        any(part in {".venv", "venv", "__pycache__"} for part in relative.parts)
        or relative.suffix.lower() in {".pyc", ".pyo"}
    )


def _is_exact_git_checkout(bundle_root: Path) -> bool:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(bundle_root), "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        top_level = Path(output).resolve(strict=True)
    except (OSError, subprocess.CalledProcessError, RuntimeError):
        return False
    return top_level == bundle_root


def _validate_release_manifest(bundle_root: Path) -> dict[str, Any] | None:
    """Validate every packaged byte before seed initialization.

    A Git checkout may run without a release manifest for development. A copied or
    extracted product has no ``.git`` marker and must carry a complete manifest.
    """

    manifest_candidate = bundle_root / RELEASE_MANIFEST_NAME
    if not manifest_candidate.is_file():
        if _is_exact_git_checkout(bundle_root):
            return None
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_MANIFEST_MISSING")

    manifest_path = _confined_existing_file(
        root=bundle_root,
        relative=Path(RELEASE_MANIFEST_NAME),
        escape_code="ALPHA0_SHIP_RELEASE_MANIFEST_PATH_ESCAPE",
        missing_code="ALPHA0_SHIP_RELEASE_MANIFEST_MISSING",
    )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_MANIFEST_INVALID") from exc
    if not isinstance(payload, dict):
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_MANIFEST_INVALID")
    if payload.get("schema") != RELEASE_MANIFEST_SCHEMA:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_MANIFEST_SCHEMA_MISMATCH")
    if payload.get("product") != RELEASE_PRODUCT:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_PRODUCT_MISMATCH")
    files = payload.get("files")
    if not isinstance(files, dict) or not files:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_MANIFEST_INVALID")

    manifest_names: set[str] = set()
    for relative_text, metadata in files.items():
        relative = _safe_relative_path(relative_text)
        if relative_text == RELEASE_MANIFEST_NAME:
            raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_MANIFEST_SELF_ENTRY")
        if not isinstance(metadata, dict) or set(metadata) != {"bytes", "sha256"}:
            raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_MANIFEST_INVALID")
        expected_bytes = metadata.get("bytes")
        expected_hash = metadata.get("sha256")
        if (
            not isinstance(expected_bytes, int)
            or isinstance(expected_bytes, bool)
            or expected_bytes < 0
            or not isinstance(expected_hash, str)
            or len(expected_hash) != 64
            or any(ch not in "0123456789abcdef" for ch in expected_hash)
        ):
            raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_MANIFEST_INVALID")
        source = _confined_existing_file(
            root=bundle_root,
            relative=relative,
            escape_code=f"ALPHA0_SHIP_RELEASE_FILE_PATH_ESCAPE:{relative_text}",
            missing_code=f"ALPHA0_SHIP_RELEASE_FILE_MISSING:{relative_text}",
        )
        if source.stat().st_size != expected_bytes or _sha256_file(source) != expected_hash:
            raise GvAlpha0ShipRuntimeError(
                f"ALPHA0_SHIP_RELEASE_FILE_TAMPERED:{relative_text}"
            )
        manifest_names.add(relative_text)

    required_seed_names = {
        relative.as_posix() for relative in _expected_seed_relative_files()
    }
    if not required_seed_names.issubset(manifest_names):
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_SEED_MANIFEST_INCOMPLETE")

    actual_names: set[str] = set()
    for directory, dirnames, filenames in os.walk(bundle_root, topdown=True, followlinks=False):
        directory_path = Path(directory)
        kept_dirs: list[str] = []
        for dirname in dirnames:
            child = directory_path / dirname
            relative = child.relative_to(bundle_root)
            if _is_ignored_package_extra(relative):
                continue
            if _is_link_like(child):
                raise GvAlpha0ShipRuntimeError(
                    f"ALPHA0_SHIP_RELEASE_DIRECTORY_LINK_REFUSED:{relative.as_posix()}"
                )
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs
        for filename in filenames:
            child = directory_path / filename
            relative = child.relative_to(bundle_root)
            if relative.as_posix() == RELEASE_MANIFEST_NAME or _is_ignored_package_extra(relative):
                continue
            _confined_existing_file(
                root=bundle_root,
                relative=relative,
                escape_code=f"ALPHA0_SHIP_RELEASE_FILE_PATH_ESCAPE:{relative.as_posix()}",
                missing_code=f"ALPHA0_SHIP_RELEASE_FILE_MISSING:{relative.as_posix()}",
            )
            actual_names.add(relative.as_posix())
    if actual_names != manifest_names:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_FILE_SET_MISMATCH")
    return payload


def default_runtime_root(*, env: dict[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    explicit = values.get(RUNTIME_HOME_ENV, "").strip()
    if explicit:
        return Path(explicit).expanduser()

    if os.name == "nt":
        local_app_data = values.get("LOCALAPPDATA", "").strip()
        base = Path(local_app_data).expanduser() if local_app_data else Path.home() / "AppData" / "Local"
        return base / "GV-ALPHA0"

    xdg_data_home = values.get("XDG_DATA_HOME", "").strip()
    base = Path(xdg_data_home).expanduser() if xdg_data_home else Path.home() / ".local" / "share"
    return base / "gv-alpha0"


def _seed_relative_files(bundle_root: Path) -> tuple[Path, ...]:
    relative = _expected_seed_relative_files()
    for source_file in relative:
        _confined_existing_file(
            root=bundle_root,
            relative=source_file,
            escape_code=f"ALPHA0_SHIP_SEED_PATH_ESCAPE:{source_file.as_posix()}",
            missing_code=f"ALPHA0_SHIP_SEED_FILE_MISSING:{source_file.as_posix()}",
        )
    return relative


def build_seed_manifest(*, bundle_root: Path | None = None) -> dict[str, Any]:
    lexical = _absolute_lexical(Path(bundle_root) if bundle_root is not None else ROOT)
    base = _canonical_existing_directory(
        lexical, code="ALPHA0_SHIP_BUNDLE_ROOT_INVALID"
    )
    files: dict[str, dict[str, Any]] = {}
    for relative in _seed_relative_files(base):
        source = _confined_existing_file(
            root=base,
            relative=relative,
            escape_code=f"ALPHA0_SHIP_SEED_PATH_ESCAPE:{relative.as_posix()}",
            missing_code=f"ALPHA0_SHIP_SEED_FILE_MISSING:{relative.as_posix()}",
        )
        files[relative.as_posix()] = {
            "bytes": source.stat().st_size,
            "sha256": _sha256_file(source),
        }

    digest = _sha256_bytes(_canonical_json_bytes(files))
    return {
        "schema": WORKSPACE_SCHEMA,
        "seed_digest": digest,
        "files": files,
    }


def _read_marker(runtime_root: Path) -> dict[str, Any]:
    marker = _confined_existing_file(
        root=runtime_root,
        relative=Path(WORKSPACE_MARKER),
        escape_code="ALPHA0_SHIP_WORKSPACE_MARKER_PATH_ESCAPE",
        missing_code="ALPHA0_SHIP_WORKSPACE_MARKER_MISSING",
    )
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_WORKSPACE_MARKER_INVALID") from exc
    if not isinstance(payload, dict):
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_WORKSPACE_MARKER_INVALID")
    return payload


def _verify_runtime_seed(
    runtime_root: Path, expected: dict[str, Any], *, bundle_root: Path
) -> None:
    runtime = _canonical_existing_directory(
        runtime_root, code="ALPHA0_SHIP_RUNTIME_ROOT_UNREADABLE"
    )
    marker = _read_marker(runtime)
    if marker.get("schema") != WORKSPACE_SCHEMA:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_WORKSPACE_SCHEMA_MISMATCH")
    if marker.get("seed_digest") != expected["seed_digest"]:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_SEED_VERSION_MISMATCH")
    if marker.get("files") != expected["files"]:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_WORKSPACE_MANIFEST_MISMATCH")

    for relative_text, metadata in expected["files"].items():
        relative = Path(relative_text)
        target = _confined_existing_file(
            root=runtime,
            relative=relative,
            escape_code=f"ALPHA0_SHIP_RUNTIME_SEED_PATH_ESCAPE:{relative.as_posix()}",
            missing_code=f"ALPHA0_SHIP_RUNTIME_SEED_MISSING:{relative.as_posix()}",
        )
        if _same_or_within(target, bundle_root):
            raise GvAlpha0ShipRuntimeError(
                f"ALPHA0_SHIP_RUNTIME_SEED_ENTERED_BUNDLE:{relative.as_posix()}"
            )
        if target.stat().st_size != metadata["bytes"] or _sha256_file(target) != metadata["sha256"]:
            raise GvAlpha0ShipRuntimeError(
                f"ALPHA0_SHIP_RUNTIME_SEED_TAMPERED:{relative.as_posix()}"
            )


def _assert_parent_writable(parent: Path) -> None:
    parent.mkdir(parents=True, exist_ok=True)
    probe = parent / f".gv-alpha0-write-probe-{uuid.uuid4().hex}"
    try:
        probe.write_bytes(b"ok\n")
        if probe.read_bytes() != b"ok\n":
            raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RUNTIME_WRITE_VERIFY_FAILED")
    except OSError as exc:
        raise GvAlpha0ShipRuntimeError(
            f"ALPHA0_SHIP_RUNTIME_PARENT_NOT_WRITABLE:{parent}"
        ) from exc
    finally:
        probe.unlink(missing_ok=True)


def _initialize_runtime(
    *, bundle_root: Path, runtime_root: Path, manifest: dict[str, Any]
) -> None:
    if runtime_root.exists():
        if runtime_root.is_symlink():
            raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RUNTIME_ROOT_SYMLINK_REFUSED")
        try:
            has_entries = any(runtime_root.iterdir())
        except OSError as exc:
            raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RUNTIME_ROOT_UNREADABLE") from exc
        if has_entries:
            raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_UNMANAGED_RUNTIME_ROOT_NOT_EMPTY")
        runtime_root.rmdir()

    _assert_parent_writable(runtime_root.parent)
    staging = runtime_root.parent / f".{runtime_root.name}.seed-{uuid.uuid4().hex}"
    try:
        staging.mkdir(parents=False, exist_ok=False)
        for relative_text in manifest["files"]:
            relative = Path(relative_text)
            source = _confined_existing_file(
                root=bundle_root,
                relative=relative,
                escape_code=f"ALPHA0_SHIP_SEED_PATH_ESCAPE:{relative.as_posix()}",
                missing_code=f"ALPHA0_SHIP_SEED_FILE_MISSING:{relative.as_posix()}",
            )
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        (staging / WORKSPACE_MARKER).write_bytes(_canonical_json_bytes(manifest))
        _verify_runtime_seed(staging, manifest, bundle_root=bundle_root)
        staging.replace(runtime_root)
    except GvAlpha0ShipRuntimeError:
        raise
    except OSError as exc:
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RUNTIME_INITIALIZATION_FAILED") from exc
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def prepare_runtime_workspace(
    *,
    bundle_root: Path | None = None,
    runtime_root: Path | None = None,
) -> RuntimeWorkspace:
    bundle_lexical = _absolute_lexical(
        Path(bundle_root) if bundle_root is not None else ROOT
    )
    bundle = _canonical_existing_directory(
        bundle_lexical, code="ALPHA0_SHIP_BUNDLE_ROOT_INVALID"
    )
    release_manifest = _validate_release_manifest(bundle)

    runtime_lexical = _absolute_lexical(
        Path(runtime_root) if runtime_root is not None else default_runtime_root()
    )
    if _is_link_like(runtime_lexical):
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RUNTIME_ROOT_LINK_REFUSED")
    runtime = _canonical_candidate(runtime_lexical)

    if _same_or_within(runtime_lexical, bundle_lexical) or _same_or_within(
        runtime, bundle
    ):
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RUNTIME_INSIDE_BUNDLE_REFUSED")

    manifest = build_seed_manifest(bundle_root=bundle)
    if (
        release_manifest is not None
        and release_manifest.get("seed_digest") != manifest["seed_digest"]
    ):
        raise GvAlpha0ShipRuntimeError("ALPHA0_SHIP_RELEASE_SEED_DIGEST_MISMATCH")

    marker = runtime / WORKSPACE_MARKER
    initialized = False
    if not marker.is_file():
        _initialize_runtime(bundle_root=bundle, runtime_root=runtime, manifest=manifest)
        initialized = True

    _verify_runtime_seed(runtime, manifest, bundle_root=bundle)
    case_dir = runtime / CASE_RELATIVE_DIR
    diagnostics = (
        f"bundle={bundle}",
        f"runtime={runtime}",
        f"seed={manifest['seed_digest']}",
        "network=not-required",
        "broker=not-required",
    )
    return RuntimeWorkspace(
        root=runtime,
        case_dir=case_dir,
        initialized=initialized,
        seed_digest=str(manifest["seed_digest"]),
        diagnostics=diagnostics,
    )
