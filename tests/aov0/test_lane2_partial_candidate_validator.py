from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.aov0_validate_lane2_partial_candidate import (
    PartialCandidateValidationError,
    validate_partial_candidate,
)


def _artifacts(tmp_path: Path) -> tuple[Path, Path]:
    candidate = tmp_path / "candidate.csv"
    candidate.write_text("SP_ENTITY_ID,CompanyName\n1,Alpha\n2,Beta\n", encoding="utf-8")
    raw = candidate.read_bytes()
    receipt = {
        "schema_version": "aov0_ciq_historical_market_original_revenue_candidate_receipt_v1",
        "capture_scope": "HISTORICAL_MARKET_ORIGINAL_REVENUE_CANDIDATES_ONLY_NOT_A1_RISK_SET",
        "as_of_date": "2025-05-16",
        "historical_risk_set_admission_authority": "NONE",
        "intersection": {
            "candidate_csv_sha256": hashlib.sha256(raw).hexdigest(),
            "candidate_csv_bytes": len(raw),
            "candidate_count": 2,
        },
        "market_component": {
            "current_company_state_filters_used": False,
            "major_us_exchange_group_parity": {
                "as_of_date": "2025-05-16",
                "exact_match": True,
            },
        },
        "revenue_component": {
            "provider_formula_validation_passed": True,
            "filing_version": "Original",
            "historical_as_of_mechanically_bound": True,
        },
        "historical_company_state": {"applied_to_candidate_membership": False},
        "historical_primary_identity": {"authority": "OPEN"},
    }
    receipt_path = tmp_path / "candidate.receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    return candidate, receipt_path


def test_validate_partial_candidate_accepts_non_authoritative_freeze(tmp_path: Path) -> None:
    candidate, receipt = _artifacts(tmp_path)
    result = validate_partial_candidate(candidate, receipt, expected_as_of_date="2025-05-16")
    assert result["entity_count"] == 2
    assert result["historical_risk_set_admission_authority"] == "NONE"


@pytest.mark.parametrize(
    ("path", "value", "error"),
    [
        (("historical_risk_set_admission_authority",), "ADMITTED", "ciq_partial_authority_invalid"),
        (
            ("market_component", "major_us_exchange_group_parity", "exact_match"),
            False,
            "ciq_partial_exchange_parity_invalid",
        ),
        (("market_component", "current_company_state_filters_used"), True, "ciq_partial_current_state_conditioning_invalid"),
        (("revenue_component", "filing_version"), "Current", "ciq_partial_revenue_vintage_invalid"),
        (
            ("historical_company_state", "applied_to_candidate_membership"),
            True,
            "ciq_partial_company_state_authority_invalid",
        ),
        (("historical_primary_identity", "authority"), "ADMITTED", "ciq_partial_primary_authority_invalid"),
    ],
)
def test_validate_partial_candidate_rejects_authority_or_source_tamper(
    tmp_path: Path, path: tuple[str, ...], value, error: str
) -> None:
    candidate, receipt = _artifacts(tmp_path)
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    cursor = payload
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(PartialCandidateValidationError, match=error):
        validate_partial_candidate(candidate, receipt, expected_as_of_date="2025-05-16")


def test_validate_partial_candidate_rejects_candidate_byte_tamper(tmp_path: Path) -> None:
    candidate, receipt = _artifacts(tmp_path)
    candidate.write_text(candidate.read_text(encoding="utf-8") + "3,Gamma\n", encoding="utf-8")
    with pytest.raises(PartialCandidateValidationError, match="ciq_partial_csv_hash_mismatch"):
        validate_partial_candidate(candidate, receipt, expected_as_of_date="2025-05-16")
