from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LATEST_POINTER = PROCESSED_DIR / "phase23_freeze_latest.json"
RESTORE_BACKUP_ROOT = PROCESSED_DIR / "phase23_restore_backups"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"JSON object expected: {path}")
    return obj


def _resolve_manifest(path_arg: str | None) -> Path:
    if path_arg:
        p = Path(path_arg)
        if not p.is_absolute():
            p = (PROJECT_ROOT / p).resolve()
        return p
    if not LATEST_POINTER.exists():
        raise FileNotFoundError(f"Missing freeze pointer: {LATEST_POINTER}")
    pointer = _load_json(LATEST_POINTER)
    manifest_path = pointer.get("manifest_path")
    if not isinstance(manifest_path, str) or manifest_path.strip() == "":
        raise ValueError(f"Invalid manifest_path in pointer: {LATEST_POINTER}")
    return Path(manifest_path).resolve()


def restore_snapshot(*, manifest_path: Path, dry_run: bool, code_only: bool) -> None:
    manifest = _load_json(manifest_path)
    entries = manifest.get("entries")
    code_files = set(str(x) for x in manifest.get("code_files", []))
    if not isinstance(entries, list):
        raise ValueError(f"Invalid entries list in {manifest_path}")

    backup_dir = RESTORE_BACKUP_ROOT / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    restored = 0
    skipped = 0

    for e in entries:
        if not isinstance(e, dict):
            continue
        repo_rel = e.get("repo_rel")
        snapshot_rel = e.get("snapshot_rel")
        expected_hash = e.get("sha256")
        if not isinstance(repo_rel, str) or not isinstance(snapshot_rel, str):
            continue
        if code_only and repo_rel not in code_files:
            skipped += 1
            continue

        src = manifest_path.parent / snapshot_rel
        dst = (PROJECT_ROOT / repo_rel).resolve()
        if not src.is_file():
            raise FileNotFoundError(f"Snapshot file missing: {src}")
        try:
            dst.relative_to(PROJECT_ROOT)
        except ValueError as exc:
            raise ValueError(f"Refusing to restore outside project root: {dst}") from exc

        if dry_run:
            print(f"[DRY-RUN] restore {src} -> {dst}")
            restored += 1
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and dst.is_file():
            backup_target = backup_dir / repo_rel
            backup_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, backup_target)

        tmp = dst.with_suffix(dst.suffix + ".restore_tmp")
        shutil.copy2(src, tmp)
        tmp.replace(dst)

        if isinstance(expected_hash, str) and expected_hash.strip() != "":
            actual_hash = _sha256_file(dst)
            if actual_hash != expected_hash:
                raise RuntimeError(
                    f"Hash mismatch after restore for {repo_rel}: expected={expected_hash} actual={actual_hash}"
                )
        restored += 1

    print(f"[RESTORE] Manifest: {manifest_path}")
    print(f"[RESTORE] Restored entries: {restored}")
    print(f"[RESTORE] Skipped entries: {skipped}")
    if dry_run:
        print("[RESTORE] Mode: dry-run (no files modified)")
    else:
        print(f"[RESTORE] Backup dir: {backup_dir}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Restore repository files from a Phase 23 freeze snapshot.")
    p.add_argument("--manifest", default=None, help="Path to freeze manifest.json. Defaults to latest pointer.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--code-only", action="store_true", help="Restore only files listed under code_files.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = _resolve_manifest(args.manifest)
    restore_snapshot(
        manifest_path=manifest_path,
        dry_run=bool(args.dry_run),
        code_only=bool(args.code_only),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
