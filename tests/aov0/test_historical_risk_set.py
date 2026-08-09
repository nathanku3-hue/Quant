from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from research.aov0.historical_screen_reconstruction import entity_membership_hash
from research.aov0.historical_risk_set import (
    AOV_HIGH_GROWTH_SCREEN_CRITERIA,
    AOV_HIGH_GROWTH_SCREEN_LAW_HASH,
    HISTORICAL_SCREEN_CAPTURE_MODE,
    HISTORICAL_SCREEN_FREEZE_MODE,
    HISTORICAL_SCREEN_RECEIPT_SCHEMA,
    HISTORICAL_SCREEN_RECON_CAPTURE_MODE,
    HISTORICAL_SCREEN_RECON_LOGIC,
    HISTORICAL_SCREEN_RECON_RECEIPT_SCHEMA,
    HISTORICAL_SCREEN_RECON_SOURCE_ID,
    HISTORICAL_SCREEN_SOURCE_ID,
    load_historical_start_risk_set,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_fixture(tmp_path: Path) -> tuple[Path, Path]:
    membership = tmp_path / "historical_screen_20250516.csv"
    pd.DataFrame(
        {
            "SP_ENTITY_ID": ["4913905", "107089758", "4972296"],
            "CompanyName": ["A", "B", "C"],
        }
    ).to_csv(membership, index=False)
    receipt = {
        "schema_version": HISTORICAL_SCREEN_RECEIPT_SCHEMA,
        "source_id": HISTORICAL_SCREEN_SOURCE_ID,
        "capture_mode": HISTORICAL_SCREEN_CAPTURE_MODE,
        "universe_freeze_mode": HISTORICAL_SCREEN_FREEZE_MODE,
        "historical_as_of_mechanically_bound": True,
        "current_screen_conditioned": False,
        "requested_cutoff_date": "2025-05-16",
        "provider_effective_as_of_date": "2025-05-16",
        "criteria": list(AOV_HIGH_GROWTH_SCREEN_CRITERIA),
        "screen_law_hash": AOV_HIGH_GROWTH_SCREEN_LAW_HASH,
        "raw_object_name": membership.name,
        "raw_object_sha256": _sha256(membership),
        "raw_object_bytes": membership.stat().st_size,
        "result_count": 3,
        "observed_identity_columns": ["SP_ENTITY_ID"],
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
    receipt_path = tmp_path / "historical_screen_20250516.receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    return membership, receipt_path


def _write_component_receipt(
    tmp_path: Path,
    name: str,
    payload: dict[str, object],
    *,
    frame: pd.DataFrame | None = None,
    csv_role: str = "normalized",
) -> Path:
    payload = {
        **payload,
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
    if frame is not None:
        csv = tmp_path / f"{name}.csv"
        frame.to_csv(csv, index=False)
        payload[f"{csv_role}_csv_name"] = csv.name
        payload[f"{csv_role}_csv_sha256"] = _sha256(csv)
        payload[f"{csv_role}_csv_bytes"] = csv.stat().st_size
    path = tmp_path / f"{name}.receipt.json"
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def _binding(path: Path, role: str) -> dict[str, str]:
    return {"role": role, "receipt_path": str(path), "receipt_sha256": _sha256(path)}


def _write_reconstruction_fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, Path]]:
    membership = tmp_path / "historical_screen_reconstructed_20250516.csv"
    pd.DataFrame(
        {
            "SP_ENTITY_ID": ["4913905", "107089758", "4972296"],
            "CompanyName": ["A", "B", "C"],
        }
    ).to_csv(membership, index=False)
    candidate_ids = ("4913905", "107089758", "4972296")
    market = _write_component_receipt(
        tmp_path,
        "market_candidates",
        {
            "schema_version": "aov0_xpressapi_historical_screen_market_candidate_merged_receipt_v1",
            "source_id": "SPGLOBAL_XPRESSAPI:SCREENER",
            "capture_scope": "HISTORICAL_MARKET_CANDIDATES_ONLY",
            "as_of_date": "2025-05-16",
            "country_code_count": 3,
            "part_count": 1,
            "country_code_universe_source": {"source_id": "LOOKUP", "sha256": "a" * 64},
            "primary_exchange_source": {"source_id": "EXCHANGES", "sha256": "b" * 64},
            "historical_market_date_mechanically_bound": True,
            "current_company_state_filters_used": False,
            "historical_risk_set_admission_authority": "NONE",
        },
        frame=pd.DataFrame(
            {
                "SP_ENTITY_ID": list(candidate_ids),
                "CompanyName": ["A", "B", "C"],
            }
        ),
        csv_role="merged",
    )
    company = _write_component_receipt(
        tmp_path,
        "company_state",
        {
            "schema_version": "aov0_historical_company_state_receipt_v1",
            "source_id": "FIXTURE:HISTORICAL_COMPANY_STATE",
            "as_of_date": "2025-05-16",
            "historical_as_of_mechanically_bound": True,
            "current_conditioned": False,
            "historical_company_type_reconstructed": True,
            "historical_company_status_reconstructed": True,
            "requested_entity_count": 3,
            "requested_entity_membership_sha256": entity_membership_hash(candidate_ids),
            "requested_entity_coverage_complete": True,
        },
        frame=pd.DataFrame(
            {
                "SP_ENTITY_ID": list(candidate_ids),
                "CompanyType": ["Public Company"] * 3,
                "CompanyStatus": ["Operating", "Operating Subsidiary", "Operating"],
            }
        ),
    )
    revenue = _write_component_receipt(
        tmp_path,
        "annual_revenue",
        {
            "schema_version": "aov0_historical_annual_revenue_receipt_v1",
            "source_id": "FIXTURE:HISTORICAL_ANNUAL_REVENUE",
            "as_of_date": "2025-05-16",
            "historical_as_of_mechanically_bound": True,
            "current_conditioned": False,
            "filing_version": "Original",
            "relative_periods": ["LFY", "FY-1", "FY-2", "FY-3"],
            "requested_entity_count": 3,
            "requested_entity_membership_sha256": entity_membership_hash(candidate_ids),
            "requested_entity_coverage_complete": True,
        },
        frame=pd.DataFrame(
            {
                "SP_ENTITY_ID": list(candidate_ids),
                "LFY": [220.0, 260.0, 300.0],
                "FY-1": [160.0, 190.0, 220.0],
                "FY-2": [120.0, 140.0, 160.0],
                "FY-3": [90.0, 100.0, 120.0],
            }
        ),
    )
    receipt = {
        "schema_version": HISTORICAL_SCREEN_RECON_RECEIPT_SCHEMA,
        "source_id": HISTORICAL_SCREEN_RECON_SOURCE_ID,
        "capture_mode": HISTORICAL_SCREEN_RECON_CAPTURE_MODE,
        "universe_freeze_mode": HISTORICAL_SCREEN_FREEZE_MODE,
        "historical_as_of_mechanically_bound": True,
        "current_screen_conditioned": False,
        "requested_cutoff_date": "2025-05-16",
        "provider_effective_as_of_date": "2025-05-16",
        "criteria": list(AOV_HIGH_GROWTH_SCREEN_CRITERIA),
        "screen_law_hash": AOV_HIGH_GROWTH_SCREEN_LAW_HASH,
        "reconstruction_logic": HISTORICAL_SCREEN_RECON_LOGIC,
        "growth_multiplier": 1.3,
        "revenue_periods": ["LFY", "FY-1", "FY-2", "FY-3"],
        "component_receipts": [
            _binding(market, "market_candidates"),
            _binding(company, "historical_company_state"),
            _binding(revenue, "historical_annual_revenue"),
        ],
        "current_screen_parity": {
            "pass": True,
            "exact_membership_match": True,
            "screen_law_hash": AOV_HIGH_GROWTH_SCREEN_LAW_HASH,
            "reference_membership_sha256": "c" * 64,
            "reconstructed_membership_sha256": "d" * 64,
        },
        "raw_object_name": membership.name,
        "raw_object_sha256": _sha256(membership),
        "raw_object_bytes": membership.stat().st_size,
        "result_count": 3,
        "observed_identity_columns": ["SP_ENTITY_ID"],
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
    receipt_path = tmp_path / "historical_screen_reconstructed_20250516.receipt.json"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    return membership, receipt_path, {"market": market, "company": company, "revenue": revenue}


def test_historical_start_risk_set_admits_exact_hash_bound_screen(tmp_path: Path) -> None:
    membership, receipt = _write_fixture(tmp_path)
    admitted = load_historical_start_risk_set(
        membership,
        receipt,
        expected_as_of_date="2025-05-16",
    )
    assert admitted.entity_ids == ("107089758", "4913905", "4972296")
    assert admitted.metadata["historical_screen_membership_reconstructed"] is True
    assert admitted.metadata["current_screen_conditioned"] is False
    assert admitted.metadata["financial_alpha_evidence"] == 0


def test_historical_start_risk_set_rejects_current_conditioning_or_criteria_drift(tmp_path: Path) -> None:
    membership, receipt_path = _write_fixture(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["current_screen_conditioned"] = True
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="current_conditioning_forbidden"):
        load_historical_start_risk_set(membership, receipt_path, expected_as_of_date="2025-05-16")

    membership, receipt_path = _write_fixture(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["criteria"][3] = "Total Revenue[Latest Fiscal Year] >= Total Revenue[FY-1] * 1.2"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="criteria_drift"):
        load_historical_start_risk_set(membership, receipt_path, expected_as_of_date="2025-05-16")


def test_historical_start_risk_set_rejects_tampered_membership_or_asof(tmp_path: Path) -> None:
    membership, receipt = _write_fixture(tmp_path)
    with membership.open("a", encoding="utf-8") as handle:
        handle.write("9999999,D\n")
    with pytest.raises(ValueError, match="membership_hash_mismatch"):
        load_historical_start_risk_set(membership, receipt, expected_as_of_date="2025-05-16")

    membership, receipt = _write_fixture(tmp_path)
    with pytest.raises(ValueError, match="requested_cutoff_date_mismatch"):
        load_historical_start_risk_set(membership, receipt, expected_as_of_date="2025-05-23")


def test_historical_start_risk_set_admits_fully_bound_reconstruction(tmp_path: Path) -> None:
    membership, receipt, _ = _write_reconstruction_fixture(tmp_path)
    admitted = load_historical_start_risk_set(
        membership,
        receipt,
        expected_as_of_date="2025-05-16",
    )
    assert admitted.entity_ids == ("107089758", "4913905", "4972296")
    assert admitted.metadata["screen_reconstruction"] is True
    assert admitted.metadata["source_id"] == HISTORICAL_SCREEN_RECON_SOURCE_ID
    assert admitted.metadata["current_screen_conditioned"] is False
    assert admitted.metadata["financial_alpha_evidence"] == 0


def test_historical_screen_reconstruction_rejects_current_company_state_or_bad_vintage(tmp_path: Path) -> None:
    membership, receipt_path, components = _write_reconstruction_fixture(tmp_path)
    company = json.loads(components["company"].read_text(encoding="utf-8"))
    company["current_conditioned"] = True
    components["company"].write_text(json.dumps(company, sort_keys=True), encoding="utf-8")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    for binding in receipt["component_receipts"]:
        if binding["role"] == "historical_company_state":
            binding["receipt_sha256"] = _sha256(components["company"])
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="company_state_current_conditioning_forbidden"):
        load_historical_start_risk_set(membership, receipt_path, expected_as_of_date="2025-05-16")

    membership, receipt_path, components = _write_reconstruction_fixture(tmp_path)
    revenue = json.loads(components["revenue"].read_text(encoding="utf-8"))
    revenue["filing_version"] = "Current/Restated"
    components["revenue"].write_text(json.dumps(revenue, sort_keys=True), encoding="utf-8")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    for binding in receipt["component_receipts"]:
        if binding["role"] == "historical_annual_revenue":
            binding["receipt_sha256"] = _sha256(components["revenue"])
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="revenue_vintage_invalid"):
        load_historical_start_risk_set(membership, receipt_path, expected_as_of_date="2025-05-16")


def test_historical_screen_reconstruction_rejects_failed_parity_or_component_tamper(tmp_path: Path) -> None:
    membership, receipt_path, _ = _write_reconstruction_fixture(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["current_screen_parity"]["pass"] = False
    receipt["current_screen_parity"]["exact_membership_match"] = False
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="current_parity_failed"):
        load_historical_start_risk_set(membership, receipt_path, expected_as_of_date="2025-05-16")

    membership, receipt_path, components = _write_reconstruction_fixture(tmp_path)
    with components["market"].open("a", encoding="utf-8") as handle:
        handle.write("\n")
    with pytest.raises(ValueError, match="component_hash_mismatch:market_candidates"):
        load_historical_start_risk_set(membership, receipt_path, expected_as_of_date="2025-05-16")
