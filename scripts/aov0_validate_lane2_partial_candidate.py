from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "aov0_ciq_historical_market_original_revenue_candidate_receipt_v1"
CAPTURE_SCOPE = "HISTORICAL_MARKET_ORIGINAL_REVENUE_CANDIDATES_ONLY_NOT_A1_RISK_SET"


class PartialCandidateValidationError(ValueError):
    """Raised when a Lane-2 partial candidate freeze fails custody validation."""


def _require_mapping(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PartialCandidateValidationError(f"{label}_missing")
    return value


def validate_partial_candidate(
    candidate_csv: str | Path,
    receipt_path: str | Path,
    *,
    expected_as_of_date: str,
) -> dict[str, Any]:
    csv_path = Path(candidate_csv)
    receipt_file = Path(receipt_path)
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))

    if receipt.get("schema_version") != SCHEMA_VERSION:
        raise PartialCandidateValidationError("ciq_partial_schema_invalid")
    if receipt.get("capture_scope") != CAPTURE_SCOPE:
        raise PartialCandidateValidationError("ciq_partial_scope_invalid")
    if receipt.get("as_of_date") != expected_as_of_date:
        raise PartialCandidateValidationError("ciq_partial_asof_mismatch")
    if receipt.get("historical_risk_set_admission_authority") != "NONE":
        raise PartialCandidateValidationError("ciq_partial_authority_invalid")

    primary = _require_mapping(receipt.get("historical_primary_identity"), label="ciq_partial_primary")
    if primary.get("authority") != "OPEN":
        raise PartialCandidateValidationError("ciq_partial_primary_authority_invalid")

    raw = csv_path.read_bytes()
    intersection = _require_mapping(receipt.get("intersection"), label="ciq_partial_intersection")
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    if observed_sha256 != intersection.get("candidate_csv_sha256"):
        raise PartialCandidateValidationError("ciq_partial_csv_hash_mismatch")
    if len(raw) != int(intersection.get("candidate_csv_bytes", -1)):
        raise PartialCandidateValidationError("ciq_partial_csv_bytes_mismatch")

    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    ids = [str(row.get("SP_ENTITY_ID") or "").strip() for row in rows]
    if any(not entity_id for entity_id in ids):
        raise PartialCandidateValidationError("ciq_partial_entity_id_missing")
    if len(rows) != int(intersection.get("candidate_count", -1)) or len(set(ids)) != len(ids):
        raise PartialCandidateValidationError("ciq_partial_candidate_count_mismatch")

    market = _require_mapping(receipt.get("market_component"), label="ciq_partial_market")
    parity = _require_mapping(market.get("major_us_exchange_group_parity"), label="ciq_partial_exchange_parity")
    if parity.get("exact_match") is not True:
        raise PartialCandidateValidationError("ciq_partial_exchange_parity_invalid")
    if parity.get("as_of_date") != expected_as_of_date:
        raise PartialCandidateValidationError("ciq_partial_exchange_parity_date_mismatch")
    if market.get("current_company_state_filters_used") is not False:
        raise PartialCandidateValidationError("ciq_partial_current_state_conditioning_invalid")

    revenue = _require_mapping(receipt.get("revenue_component"), label="ciq_partial_revenue")
    if revenue.get("provider_formula_validation_passed") is not True:
        raise PartialCandidateValidationError("ciq_partial_revenue_validation_invalid")
    if revenue.get("filing_version") != "Original":
        raise PartialCandidateValidationError("ciq_partial_revenue_vintage_invalid")
    if revenue.get("historical_as_of_mechanically_bound") is not True:
        raise PartialCandidateValidationError("ciq_partial_revenue_asof_binding_invalid")

    company_state = _require_mapping(receipt.get("historical_company_state"), label="ciq_partial_company_state")
    if company_state.get("applied_to_candidate_membership") is not False:
        raise PartialCandidateValidationError("ciq_partial_company_state_authority_invalid")

    return {
        "as_of_date": expected_as_of_date,
        "entity_count": len(ids),
        "candidate_csv_sha256": observed_sha256,
        "historical_risk_set_admission_authority": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the non-authoritative Lane-2 CIQ partial candidate freeze.")
    parser.add_argument("candidate_csv")
    parser.add_argument("receipt")
    parser.add_argument("--as-of-date", required=True)
    args = parser.parse_args()
    result = validate_partial_candidate(
        args.candidate_csv,
        args.receipt,
        expected_as_of_date=args.as_of_date,
    )
    print(
        "CIQ_PARTIAL_VALID"
        f"\tASOF={result['as_of_date']}"
        f"\tENTITIES={result['entity_count']}"
        f"\tSHA256={result['candidate_csv_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
