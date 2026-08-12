"""Admit independent broad current CIQ identity/market custody for CRV1.

No provider/network acquisition is performed here.  The command requires fresh,
hash-bound CRV1 capture receipts and writes only derived Alpha-PIT source
artifacts.  AOV-109, growth-screen, survivor-backprojection, and legacy-identity
inputs fail closed in the admission library before any output is written.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.alpha_pit_v1.adapters.ciq_crv1_source_v1 import (  # noqa: E402
    build_crv1_structured_source_admission,
    canonical_json_bytes,
)


def _aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("alpha_pit_crv1_as_of_timezone_required")
    return parsed


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            raise FileExistsError(f"alpha_pit_crv1_admission_output_exists:{path.as_posix()}")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True, help="Timezone-aware decision cut, e.g. 2026-08-10T21:00:00Z")
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--identity-capture-receipt", type=Path, required=True)
    parser.add_argument("--market", type=Path, required=True)
    parser.add_argument("--market-capture-receipt", type=Path, required=True)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data/alpha_pit_v1/crv1/current",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir.resolve()
    identity_receipt_path = out_dir / "ciq_crv1_primary_security_master.receipt.json"
    market_receipt_path = out_dir / "ciq_crv1_primary_security_market.receipt.json"
    risk_source_path = out_dir / "crv1_us_primary_common_risk_set.source.json"
    risk_receipt_path = out_dir / "crv1_us_primary_common_risk_set.receipt.json"
    outputs = (identity_receipt_path, market_receipt_path, risk_source_path, risk_receipt_path)
    existing = [path.as_posix() for path in outputs if path.exists()]
    if existing:
        raise FileExistsError("alpha_pit_crv1_admission_outputs_exist:" + ",".join(existing))

    admission = build_crv1_structured_source_admission(
        as_of=_aware(args.as_of),
        identity_path=args.identity.resolve(),
        identity_capture_receipt_path=args.identity_capture_receipt.resolve(),
        market_path=args.market.resolve(),
        market_capture_receipt_path=args.market_capture_receipt.resolve(),
        identity_receipt_path_for_binding=identity_receipt_path.name,
    )

    _atomic_bytes(identity_receipt_path, canonical_json_bytes(admission.identity_receipt))
    _atomic_bytes(market_receipt_path, canonical_json_bytes(admission.market_receipt))
    _atomic_bytes(risk_source_path, canonical_json_bytes(admission.risk_set_source))
    _atomic_bytes(risk_receipt_path, canonical_json_bytes(admission.risk_set_receipt))

    summary = {
        "schema_version": "alpha_pit_crv1_current_source_admission_summary_v1",
        "status": "CRV1_INDEPENDENT_NON_GROWTH_RISK_SET_ADMITTED",
        "eligible_security_count": admission.eligible_security_count,
        "exclusion_counts": admission.risk_set_source["exclusion_counts"],
        "identity_receipt": identity_receipt_path.as_posix(),
        "market_receipt": market_receipt_path.as_posix(),
        "risk_set_source": risk_source_path.as_posix(),
        "risk_set_receipt": risk_receipt_path.as_posix(),
        "aov_109_reused": False,
        "financial_alpha_evidence": 0,
        "outcomes_accessed": False,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
