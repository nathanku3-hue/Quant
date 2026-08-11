"""OK-SBI-0 S0 pre-open freeze writer — lands machine freeze + claim schema.

Does not open outcomes, call providers, rank composites, or issue carve-outs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from research.asymmetric_opportunity_v1.claim_schema import schema_document  # noqa: E402
from research.asymmetric_opportunity_v1.preopen_freeze import (  # noqa: E402
    build_machine_freeze,
    write_machine_freeze,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_ROOT,
        help="K0A lineage repo root",
    )
    parser.add_argument(
        "--freeze-out",
        type=Path,
        default=None,
        help="Machine freeze JSON path",
    )
    parser.add_argument(
        "--claim-schema-out",
        type=Path,
        default=None,
        help="Claim schema JSON path",
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()

    freeze_path = args.freeze_out or (
        root / "docs" / "context" / "e2e_evidence" / "ok_sbi_0_machine_freeze_v1_2.json"
    )
    schema_path = args.claim_schema_out or (
        root
        / "docs"
        / "context"
        / "e2e_evidence"
        / "ok_sbi_0_claim_receipt_schema_v1_2.json"
    )

    freeze = write_machine_freeze(freeze_path, repo_root=root)
    schema = schema_document()
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(
        json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    summary = {
        "slice_id": freeze["slice_id"],
        "STATE": freeze["STATE"],
        "runnable_evaluation": freeze["runnable_evaluation"],
        "blocked_field_count": freeze["blocked_field_count"],
        "Q_feasibility": freeze["Q_feasibility"],
        "q_amendment_cycles_used": freeze["q_amendment_cycles_used"],
        "outcome_open_authorized": freeze["outcome_open_authorized"],
        "financial_alpha_evidence": 0,
        "artifacts": {
            "machine_freeze": {
                "path": freeze_path.as_posix(),
                "sha256": _sha256_file(freeze_path),
            },
            "claim_schema": {
                "path": schema_path.as_posix(),
                "sha256": _sha256_file(schema_path),
            },
        },
        "constitution": freeze["constitution"],
    }
    sys.stdout.write(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
