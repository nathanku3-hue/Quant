"""Fresh-process full-chain verifier for an AOV-0 prospective seal candidate."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gv_fs0_canonical import domain_hash
from research.aov0.experiment import reopen_prospective_seal_full_chain


FRESH_VERIFICATION_SCHEMA = "aov0_fresh_process_verification_v1"


def _artifact_identity(path: Path) -> dict[str, object]:
    path = Path(path).resolve()
    raw = path.read_bytes()
    try:
        display = path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        display = path.as_posix()
    return {"path": display, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _atomic_new_json(path: Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"aov0_fresh_verification_proof_exists:{path}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seal", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--verification-proof", type=Path)
    parser.add_argument("--expected-parent-pid", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if (args.verification_proof is None) != (args.expected_parent_pid is None):
        print(
            json.dumps(
                {
                    "status": "BLOCKED_FULL_CHAIN_REOPEN",
                    "reason": "aov0_fresh_verification_proof_requires_expected_parent_pid",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    if args.expected_parent_pid is not None and os.getpid() == args.expected_parent_pid:
        print(
            json.dumps(
                {
                    "status": "BLOCKED_FULL_CHAIN_REOPEN",
                    "reason": "aov0_fresh_verification_separate_process_required",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    try:
        result = reopen_prospective_seal_full_chain(
            args.seal,
            repo_root=args.repo_root,
        )
        if args.verification_proof is not None:
            body = {
                "schema_version": FRESH_VERIFICATION_SCHEMA,
                "status": "FULL_CHAIN_REOPEN_VERIFIED",
                "verified_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "parent_pid": int(args.expected_parent_pid),
                "verifier_pid": os.getpid(),
                "fresh_process": os.getpid() != int(args.expected_parent_pid),
                "seal_id": result["seal_id"],
                "seal_artifact": _artifact_identity(args.seal),
                "verifier_executable": _artifact_identity(Path(__file__)),
                "evaluation_start": result["evaluation_start"],
                "outcome_open_not_before": result["outcome_open_not_before"],
            }
            proof = {
                **body,
                "verification_id": domain_hash("AOV0:FRESH_PROCESS_VERIFICATION:V1", body),
            }
            _atomic_new_json(args.verification_proof, proof)
            result = {
                **result,
                "verification_id": proof["verification_id"],
                "verification_proof": _artifact_identity(args.verification_proof),
            }
    except (FileExistsError, FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "status": "BLOCKED_FULL_CHAIN_REOPEN",
                    "reason": str(exc),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
