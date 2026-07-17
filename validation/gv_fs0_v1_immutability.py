#!/usr/bin/env python3
"""Reject unversioned changes to an already-frozen GV-FS0 V1 surface."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gv_fs0.protocol.definitions import (
    CONTRACT_PATH,
    FREEZE_MANIFEST_PATH,
    PHASE_BRIEF_PATH,
    expected_documents,
    assert_documents_match,
)

FROZEN_V1_PATHS = frozenset(
    {
        CONTRACT_PATH,
        PHASE_BRIEF_PATH,
        *expected_documents().keys(),
        "gv_fs0/protocol/canonical.py",
        "gv_fs0/protocol/definitions.py",
        "gv_fs0/protocol/ordering.py",
        "gv_fs0/protocol/publication.py",
        "gv_fs0/protocol/supervision.py",
        "gv_fs0/protocol/validation.py",
        "validation/gv_fs0_canonical_reference.py",
        "validation/gv_fs0_protocol_freeze.py",
        "validation/gv_fs0_v1_immutability.py",
    }
)


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _base_contains_manifest(base_ref: str) -> bool:
    result = _git("cat-file", "-e", f"{base_ref}:{FREEZE_MANIFEST_PATH}", check=False)
    return result.returncode == 0


def _changed_paths(base_ref: str) -> set[str]:
    result = _git("diff", "--name-only", f"{base_ref}...HEAD")
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def validate(base_ref: str | None) -> None:
    assert_documents_match(ROOT)
    if base_ref is None or not _base_contains_manifest(base_ref):
        return
    changed_frozen = sorted(_changed_paths(base_ref).intersection(FROZEN_V1_PATHS))
    if changed_frozen:
        rendered = "\n".join(f"  - {path}" for path in changed_frozen)
        raise RuntimeError(
            "GV-FS0 V1 is already frozen on the comparison base. "
            "Change the protocol/schema/domain version and re-audit instead of mutating V1:\n"
            + rendered
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", help="Git base ref used for same-version change detection")
    args = parser.parse_args()
    try:
        validate(args.base_ref)
    except Exception as exc:
        print(f"GV_FS0_V1_IMMUTABILITY: FAIL: {exc}", file=sys.stderr)
        return 1
    print("GV_FS0_V1_IMMUTABILITY: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
