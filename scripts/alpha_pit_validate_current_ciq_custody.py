"""Read-only validation of landed current CIQ custody through Alpha PIT v1.

This does not create a CRV1 risk set, input packet, seal, outcome, or evidence
claim.  It proves only that the already-landed AOV current-cut CIQ structured
bytes can be consumed by the frozen Alpha PIT interface without fallback.
The AOV growth-screen 109 is never passed to ``risk_set``; absence of an
independent ``CRV1_US_PRIMARY_COMMON_V1`` source must remain fail-closed.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.alpha_pit_v1.adapters import (  # noqa: E402
    CiqCycleV1Adapter,
    CycleResonancePITBackendV1,
    SecAlphaClaimsV1Adapter,
)
from research.alpha_pit_v1.contracts import FAMILY_ID, OBSERVATION_FIELDS, ResearchMode  # noqa: E402
from research.alpha_pit_v1.session import open_alpha_pit_session  # noqa: E402
from research.aov0.contracts import normalize_security_id  # noqa: E402


DEFAULT_AS_OF = "2026-08-08T20:00:00Z"
EXPECTED_RISK_SET_BLOCK = "alpha_pit_crv1_risk_set_source_not_landed"


def _parse_aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("as_of_timezone_required")
    return parsed


def _security_ids(master_path: Path) -> tuple[str, ...]:
    frame = pd.read_csv(master_path, dtype=str)
    if "SP_CIQ_ID" not in frame.columns:
        raise ValueError("security_master_missing_SP_CIQ_ID")
    ids = tuple(
        sorted(normalize_security_id(f"CIQSEC:{str(value).strip()}") for value in frame["SP_CIQ_ID"])
    )
    if len(set(ids)) != len(ids):
        raise ValueError("security_master_duplicate_ciq_security_id")
    return ids


def _observation_summary(rows: list[dict]) -> dict:
    by_field: dict[str, Counter] = defaultdict(Counter)
    missing_reasons: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        field_id = str(row["field_id"])
        status = str(row["coverage_status"])
        by_field[field_id][status] += 1
        if status != "PRESENT":
            missing_reasons[field_id][str(row["missingness_reason"])] += 1
    return {
        "row_count": len(rows),
        "coverage_by_field": {
            field: dict(sorted(counter.items()))
            for field, counter in sorted(by_field.items())
        },
        "missingness_by_field": {
            field: dict(sorted(counter.items()))
            for field, counter in sorted(missing_reasons.items())
        },
    }


def validate_current_custody(*, root: Path, as_of: datetime) -> dict:
    master_path = root / "data/aov0/raw/ciq_primary_security_master_20260808T162322Z.csv"
    ciq = CiqCycleV1Adapter(
        security_master_path=master_path,
        security_master_receipt_path=root / "data/aov0/source_receipts/ciq_primary_security_master_current.json",
        market_history_path=root / "data/aov0/raw/ciq_primary_security_market_history_20260808T193921Z.csv",
        market_receipt_path=root / "data/aov0/source_receipts/ciq_primary_security_market_data_current.json",
        fundamental_panel_path=root / "data/aov0/intermediate/ciq_entity_quarterly_panel.parquet",
        fundamental_receipt_path=root / "data/aov0/source_receipts/ciq_quarterly_fundamentals_run_4_20260807.json",
    )
    backend = CycleResonancePITBackendV1(
        ciq=ciq,
        sec_claims=SecAlphaClaimsV1Adapter(custody_verified_at=ciq.custody_verified_at),
    )
    api = open_alpha_pit_session(
        mode=ResearchMode.CONFIRMATORY,
        family_id=FAMILY_ID,
        decision_context_id="CLOCK1_CURRENT_CIQ_CUSTODY_MECHANICAL_VALIDATION",
        backend=backend,
    )
    ids = _security_ids(master_path)

    observations = api.observations(ids=ids, fields=OBSERVATION_FIELDS, as_of=as_of)
    expectations = api.expectations(ids=ids, as_of=as_of)
    claims = api.source_claims(ids=ids, as_of=as_of)

    risk_set_status = "UNEXPECTEDLY_AVAILABLE"
    try:
        api.risk_set(as_of=as_of)
    except ValueError as exc:
        if EXPECTED_RISK_SET_BLOCK not in str(exc):
            raise
        risk_set_status = "BLOCKED_INDEPENDENT_CRV1_RISK_SET_NOT_LANDED"
    if risk_set_status != "BLOCKED_INDEPENDENT_CRV1_RISK_SET_NOT_LANDED":
        raise AssertionError("current_AOV_109_must_not_become_CRV1_risk_set")

    expectation_statuses = Counter(str(row["coverage_status"]) for row in expectations.payload["rows"])
    if set(expectation_statuses) != {"MISSING_SOURCE"}:
        raise AssertionError("current_custody_expectations_must_remain_explicitly_missing")
    if claims.payload["rows"]:
        raise AssertionError("current_custody_SEC_claims_must_remain_empty_until_landed")

    return {
        "schema_version": "alpha_pit_current_ciq_custody_validation_v1",
        "status": "CURRENT_CIQ_STRUCTURED_PRODUCER_VERIFIED_RISK_SET_BLOCKED",
        "as_of": as_of.isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "security_count": len(ids),
        "observation_fields": list(OBSERVATION_FIELDS),
        "observations": _observation_summary(observations.payload["rows"]),
        "expectations": {
            "row_count": len(expectations.payload["rows"]),
            "coverage_status_counts": dict(sorted(expectation_statuses.items())),
            "missingness_by_reason": expectations.manifest["coverage_summary"]["missingness_by_reason"],
        },
        "source_claims": {
            "row_count": len(claims.payload["rows"]),
            "missingness_by_reason": claims.manifest["coverage_summary"]["missingness_by_reason"],
        },
        "risk_set_status": risk_set_status,
        "growth_screen_used_for_crv1_risk_set": False,
        "financial_alpha_evidence": 0,
        "authority": "MECHANICAL_CURRENT_CUSTODY_VALIDATION_ONLY",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--as-of", default=DEFAULT_AS_OF)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = validate_current_custody(root=args.root.resolve(), as_of=_parse_aware(args.as_of))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
