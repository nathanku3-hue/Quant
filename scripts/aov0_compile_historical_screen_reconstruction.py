#!/usr/bin/env python
"""Compile and seal a reconstructed historical AOV high-growth risk set.

Stages are deliberately separate:

``reconstruct``
    Compile historical membership from three independently admitted components.

``parity``
    Compare a current-date reconstruction against the frozen direct CIQ screen.
    Exact membership equality is required; no tolerance is supported.

``finalize``
    Bind the historical membership, its three component receipts, and a passing
    current-date parity receipt into the reconstruction receipt admitted by
    ``research.aov0.historical_risk_set``.  The loader will still re-run the
    compiler before admission.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.aov0.historical_risk_set import load_historical_start_risk_set  # noqa: E402
from research.aov0.historical_screen_reconstruction import (  # noqa: E402
    build_current_screen_parity_receipt,
    build_reconstruction_receipt,
    reconstruct_historical_screen,
)


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as handle:
        tmp = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    _atomic_write_bytes(
        path,
        (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode(
            "utf-8"
        ),
    )


def _write_csv(path: Path, frame) -> None:
    _atomic_write_bytes(path, frame.to_csv(index=False, lineterminator="\n").encode("utf-8"))


def _refuse_existing(*paths: Path) -> None:
    existing = [path.as_posix() for path in paths if path.exists()]
    if existing:
        raise FileExistsError("refuse_existing:" + ",".join(existing))


def command_reconstruct(args: argparse.Namespace) -> int:
    out_membership = args.out_membership.resolve()
    out_audit = args.out_audit.resolve()
    out_metadata = args.out_metadata.resolve()
    _refuse_existing(out_membership, out_audit, out_metadata)
    rebuilt = reconstruct_historical_screen(
        market_receipt_path=args.market_receipt.resolve(),
        company_state_receipt_path=args.company_state_receipt.resolve(),
        revenue_receipt_path=args.revenue_receipt.resolve(),
        expected_as_of_date=args.as_of_date,
    )
    _write_csv(out_membership, rebuilt.membership)
    _write_csv(out_audit, rebuilt.audit)
    metadata = dict(rebuilt.metadata)
    metadata["membership_name"] = out_membership.name
    metadata["audit_name"] = out_audit.name
    _write_json(out_metadata, metadata)
    print(
        f"HISTORICAL_SCREEN_RECONSTRUCT_OK\tASOF={metadata['as_of_date']}\t"
        f"CANDIDATES={metadata['candidate_count']}\tPASS={metadata['result_count']}\t"
        f"PATH={out_membership}"
    )
    return 0


def command_parity(args: argparse.Namespace) -> int:
    out = args.out.resolve()
    _refuse_existing(out)
    payload = build_current_screen_parity_receipt(
        reference_membership_path=args.reference_membership.resolve(),
        reconstructed_membership_path=args.reconstructed_membership.resolve(),
        reference_source_id=args.reference_source_id,
        parity_as_of_date=args.as_of_date,
    )
    _write_json(out, payload)
    print(
        f"HISTORICAL_SCREEN_PARITY_{'PASS' if payload['pass'] else 'FAIL'}\t"
        f"REFERENCE={payload['reference_result_count']}\t"
        f"RECONSTRUCTED={payload['reconstructed_result_count']}\tPATH={out}"
    )
    return 0 if payload["pass"] else 2


def command_finalize(args: argparse.Namespace) -> int:
    out = args.out.resolve()
    _refuse_existing(out)
    payload = build_reconstruction_receipt(
        membership_path=args.membership.resolve(),
        market_receipt_path=args.market_receipt.resolve(),
        company_state_receipt_path=args.company_state_receipt.resolve(),
        revenue_receipt_path=args.revenue_receipt.resolve(),
        parity_receipt_path=args.parity_receipt.resolve(),
        as_of_date=args.as_of_date,
    )
    _write_json(out, payload)
    # Prove the exact artifact we just wrote is accepted and recompiles to the
    # same membership; the admission loader remains the final authority.
    admitted = load_historical_start_risk_set(
        args.membership.resolve(), out, expected_as_of_date=args.as_of_date
    )
    print(
        f"HISTORICAL_SCREEN_FINALIZE_OK\tASOF={admitted.as_of_date.date().isoformat()}\t"
        f"ENTITIES={len(admitted.entity_ids)}\tPATH={out}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    reconstruct = sub.add_parser("reconstruct")
    reconstruct.add_argument("--as-of-date", required=True)
    reconstruct.add_argument("--market-receipt", type=Path, required=True)
    reconstruct.add_argument("--company-state-receipt", type=Path, required=True)
    reconstruct.add_argument("--revenue-receipt", type=Path, required=True)
    reconstruct.add_argument("--out-membership", type=Path, required=True)
    reconstruct.add_argument("--out-audit", type=Path, required=True)
    reconstruct.add_argument("--out-metadata", type=Path, required=True)
    reconstruct.set_defaults(func=command_reconstruct)

    parity = sub.add_parser("parity")
    parity.add_argument("--as-of-date", required=True)
    parity.add_argument("--reference-membership", type=Path, required=True)
    parity.add_argument("--reconstructed-membership", type=Path, required=True)
    parity.add_argument("--reference-source-id", required=True)
    parity.add_argument("--out", type=Path, required=True)
    parity.set_defaults(func=command_parity)

    finalize = sub.add_parser("finalize")
    finalize.add_argument("--as-of-date", required=True)
    finalize.add_argument("--membership", type=Path, required=True)
    finalize.add_argument("--market-receipt", type=Path, required=True)
    finalize.add_argument("--company-state-receipt", type=Path, required=True)
    finalize.add_argument("--revenue-receipt", type=Path, required=True)
    finalize.add_argument("--parity-receipt", type=Path, required=True)
    finalize.add_argument("--out", type=Path, required=True)
    finalize.set_defaults(func=command_finalize)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
