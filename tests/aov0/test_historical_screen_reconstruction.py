from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from research.aov0.historical_risk_set import load_historical_start_risk_set
from research.aov0.historical_screen_reconstruction import (
    HISTORICAL_ANNUAL_REVENUE_RECEIPT_SCHEMA,
    HISTORICAL_COMPANY_STATE_RECEIPT_SCHEMA,
    HistoricalScreenReconstructionError,
    build_current_screen_parity_receipt,
    build_reconstruction_receipt,
    entity_membership_hash,
    reconstruct_historical_screen,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_receipt_with_csv(
    root: Path,
    *,
    name: str,
    frame: pd.DataFrame,
    payload: dict[str, object],
    csv_role: str = "normalized",
) -> Path:
    csv = root / f"{name}.csv"
    frame.to_csv(csv, index=False)
    receipt = {
        **payload,
        f"{csv_role}_csv_name": csv.name,
        f"{csv_role}_csv_sha256": _sha(csv),
        f"{csv_role}_csv_bytes": csv.stat().st_size,
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
    path = root / f"{name}.receipt.json"
    path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    return path


def _convert_market_receipt_to_ciq_securities(market: Path) -> Path:
    receipt = json.loads(market.read_text(encoding="utf-8"))
    receipt.update(
        {
            "schema_version": "aov0_ciq_securities_historical_market_candidate_receipt_v1",
            "source_id": "SPCIQPRO:SECURITIES_PRODUCTQUERY",
            "market_perspective": "321247",
            "price_field_key": "324251",
            "price_date_secondary_key": "sk_557",
            "exchange_group_field_key": "406718",
            "exchange_group_value": "-1,-4",
            "funding_type_field_key": "321268",
            "funding_type_values": ["1", "16"],
            "source_security_row_count": 6,
            "result_entity_count": 4,
            "major_us_exchange_group_parity": {
                "as_of_date": "2025-05-16",
                "exact_match": True,
                "group_security_row_count": 6,
                "explicit_union_security_row_count": 6,
                "group_only_count": 0,
                "explicit_only_count": 0,
                "explicit_exchange_codes": {
                    "NYSE": "0",
                    "NYSEAM": "1",
                    "NASDAQGM": "2",
                    "NASDAQCM": "211",
                    "NASDAQGS": "212",
                },
                "excluded_arca_code": "33",
            },
        }
    )
    for field in (
        "country_code_count",
        "part_count",
        "country_code_universe_source",
        "primary_exchange_source",
    ):
        receipt.pop(field, None)
    market.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    return market


def _components(tmp_path: Path) -> tuple[Path, Path, Path]:
    ids = ("1", "2", "3", "4")
    cohort_hash = entity_membership_hash(ids)
    market = _write_receipt_with_csv(
        tmp_path,
        name="market",
        frame=pd.DataFrame(
            {"SP_ENTITY_ID": ids, "CompanyName": ["A", "B", "C", "D"]}
        ),
        csv_role="merged",
        payload={
            "schema_version": "aov0_xpressapi_historical_screen_market_candidate_merged_receipt_v1",
            "source_id": "SPGLOBAL_XPRESSAPI:SCREENER",
            "capture_scope": "HISTORICAL_MARKET_CANDIDATES_ONLY",
            "as_of_date": "2025-05-16",
            "historical_market_date_mechanically_bound": True,
            "current_company_state_filters_used": False,
            "historical_risk_set_admission_authority": "NONE",
            "country_code_count": 2,
            "part_count": 1,
            "country_code_universe_source": {"source_id": "COUNTRIES", "sha256": "a" * 64},
            "primary_exchange_source": {"source_id": "EXCHANGES", "sha256": "b" * 64},
        },
    )
    company = _write_receipt_with_csv(
        tmp_path,
        name="company",
        frame=pd.DataFrame(
            {
                "SP_ENTITY_ID": ids,
                "CompanyType": ["Public Company", "Public Company", "Private Company", "Public Company"],
                "CompanyStatus": ["Operating", "Operating Subsidiary", "Operating", "Operating"],
            }
        ),
        payload={
            "schema_version": HISTORICAL_COMPANY_STATE_RECEIPT_SCHEMA,
            "source_id": "FIXTURE:HISTORICAL_COMPANY_STATE",
            "as_of_date": "2025-05-16",
            "historical_as_of_mechanically_bound": True,
            "current_conditioned": False,
            "historical_company_type_reconstructed": True,
            "historical_company_status_reconstructed": True,
            "requested_entity_count": 4,
            "requested_entity_membership_sha256": cohort_hash,
            "requested_entity_coverage_complete": True,
        },
    )
    revenue = _write_receipt_with_csv(
        tmp_path,
        name="revenue",
        frame=pd.DataFrame(
            {
                "SP_ENTITY_ID": ids,
                # 1 passes. 2 fails final growth leg. 3 would pass growth but
                # fails company type. 4 has genuine missing LFY and fails.
                "LFY": [220.0, 220.0, 220.0, ""],
                "FY-1": [160.0, 160.0, 160.0, 160.0],
                "FY-2": [120.0, 120.0, 120.0, 120.0],
                "FY-3": [90.0, 100.0, 90.0, 90.0],
            }
        ),
        payload={
            "schema_version": HISTORICAL_ANNUAL_REVENUE_RECEIPT_SCHEMA,
            "source_id": "SPCIQPRO:HISTORICAL_ANNUAL_REVENUE",
            "as_of_date": "2025-05-16",
            "historical_as_of_mechanically_bound": True,
            "current_conditioned": False,
            "filing_version": "Original",
            "relative_periods": ["LFY", "FY-1", "FY-2", "FY-3"],
            "requested_entity_count": 4,
            "requested_entity_membership_sha256": cohort_hash,
            "requested_entity_coverage_complete": True,
        },
    )
    return market, company, revenue


def test_reconstruct_historical_screen_applies_exact_law_and_missing_is_nonpass(tmp_path: Path) -> None:
    market, company, revenue = _components(tmp_path)
    rebuilt = reconstruct_historical_screen(
        market_receipt_path=market,
        company_state_receipt_path=company,
        revenue_receipt_path=revenue,
        expected_as_of_date="2025-05-16",
    )
    assert rebuilt.membership["SP_ENTITY_ID"].tolist() == ["1"]
    audit = rebuilt.audit.set_index("SP_ENTITY_ID")
    assert bool(audit.loc["1", "screen_pass"]) is True
    assert bool(audit.loc["2", "growth_fy2_fy3_pass"]) is False
    assert bool(audit.loc["3", "company_type_pass"]) is False
    assert bool(audit.loc["4", "growth_lfy_fy1_pass"]) is False
    assert rebuilt.metadata["current_screen_conditioned"] is False
    assert rebuilt.metadata["financial_alpha_evidence"] == 0


def test_reconstruct_accepts_ciq_securities_productquery_market_component(tmp_path: Path) -> None:
    market, company, revenue = _components(tmp_path)
    _convert_market_receipt_to_ciq_securities(market)
    rebuilt = reconstruct_historical_screen(
        market_receipt_path=market,
        company_state_receipt_path=company,
        revenue_receipt_path=revenue,
        expected_as_of_date="2025-05-16",
    )
    assert rebuilt.membership["SP_ENTITY_ID"].tolist() == ["1"]
    assert rebuilt.metadata["candidate_count"] == 4
    assert rebuilt.metadata["current_screen_conditioned"] is False


@pytest.mark.parametrize(
    ("mutator", "error"),
    [
        (lambda r: r.__setitem__("exchange_group_value", "0,1,2,211,212"), "exchange_group_invalid"),
        (
            lambda r: r["major_us_exchange_group_parity"].__setitem__("exact_match", False),
            "exchange_parity_failed",
        ),
        (
            lambda r: r["major_us_exchange_group_parity"]["explicit_exchange_codes"].__setitem__(
                "ARCA", "33"
            ),
            "exchange_codes_invalid",
        ),
        (
            lambda r: r.__setitem__("current_company_state_filters_used", True),
            "current_state_forbidden",
        ),
    ],
)
def test_ciq_securities_market_component_tamper_fails_closed(
    tmp_path: Path, mutator, error: str
) -> None:
    market, company, revenue = _components(tmp_path)
    _convert_market_receipt_to_ciq_securities(market)
    receipt = json.loads(market.read_text(encoding="utf-8"))
    mutator(receipt)
    market.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(HistoricalScreenReconstructionError, match=error):
        reconstruct_historical_screen(
            market_receipt_path=market,
            company_state_receipt_path=company,
            revenue_receipt_path=revenue,
            expected_as_of_date="2025-05-16",
        )


def test_reconstruct_rejects_incomplete_requested_cohort_even_if_csv_shape_looks_valid(tmp_path: Path) -> None:
    market, company, revenue = _components(tmp_path)
    receipt = json.loads(company.read_text(encoding="utf-8"))
    receipt["requested_entity_count"] = 3
    company.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(HistoricalScreenReconstructionError, match="requested_entity_count_mismatch"):
        reconstruct_historical_screen(
            market_receipt_path=market,
            company_state_receipt_path=company,
            revenue_receipt_path=revenue,
            expected_as_of_date="2025-05-16",
        )


def test_current_screen_parity_is_exact_and_no_tolerance_exists(tmp_path: Path) -> None:
    reference = tmp_path / "reference.csv"
    reconstructed = tmp_path / "reconstructed.csv"
    pd.DataFrame({"SP_ENTITY_ID": ["1", "2"]}).to_csv(reference, index=False)
    pd.DataFrame({"SP_ENTITY_ID": ["2", "1"]}).to_csv(reconstructed, index=False)
    passed = build_current_screen_parity_receipt(
        reference_membership_path=reference,
        reconstructed_membership_path=reconstructed,
        reference_source_id="SPCIQPRO:COMPANIES_SCREENER_RESULT",
        parity_as_of_date="2026-08-07",
    )
    assert passed["pass"] is True
    pd.DataFrame({"SP_ENTITY_ID": ["1", "3"]}).to_csv(reconstructed, index=False)
    failed = build_current_screen_parity_receipt(
        reference_membership_path=reference,
        reconstructed_membership_path=reconstructed,
        reference_source_id="SPCIQPRO:COMPANIES_SCREENER_RESULT",
        parity_as_of_date="2026-08-07",
    )
    assert failed["pass"] is False
    assert failed["exact_membership_match"] is False


def test_ciq_securities_market_component_is_accepted_by_final_loader(tmp_path: Path) -> None:
    market, company, revenue = _components(tmp_path)
    _convert_market_receipt_to_ciq_securities(market)
    rebuilt = reconstruct_historical_screen(
        market_receipt_path=market,
        company_state_receipt_path=company,
        revenue_receipt_path=revenue,
        expected_as_of_date="2025-05-16",
    )
    membership = tmp_path / "historical_membership_ciq.csv"
    rebuilt.membership.to_csv(membership, index=False)
    current_reference = tmp_path / "current_reference_ciq.csv"
    current_reconstructed = tmp_path / "current_reconstructed_ciq.csv"
    pd.DataFrame({"SP_ENTITY_ID": ["10", "20"]}).to_csv(current_reference, index=False)
    pd.DataFrame({"SP_ENTITY_ID": ["10", "20"]}).to_csv(current_reconstructed, index=False)
    parity_payload = build_current_screen_parity_receipt(
        reference_membership_path=current_reference,
        reconstructed_membership_path=current_reconstructed,
        reference_source_id="SPCIQPRO:COMPANIES_SCREENER_RESULT",
        parity_as_of_date="2026-08-07",
    )
    parity = tmp_path / "parity_ciq.receipt.json"
    parity.write_text(json.dumps(parity_payload), encoding="utf-8")
    final_payload = build_reconstruction_receipt(
        membership_path=membership,
        market_receipt_path=market,
        company_state_receipt_path=company,
        revenue_receipt_path=revenue,
        parity_receipt_path=parity,
        as_of_date="2025-05-16",
    )
    final = tmp_path / "historical_membership_ciq.receipt.json"
    final.write_text(json.dumps(final_payload), encoding="utf-8")
    admitted = load_historical_start_risk_set(
        membership, final, expected_as_of_date="2025-05-16"
    )
    assert admitted.entity_ids == ("1",)
    assert admitted.metadata["screen_reconstruction"] is True


def test_final_receipt_is_recompiled_by_formal_loader(tmp_path: Path) -> None:
    market, company, revenue = _components(tmp_path)
    rebuilt = reconstruct_historical_screen(
        market_receipt_path=market,
        company_state_receipt_path=company,
        revenue_receipt_path=revenue,
        expected_as_of_date="2025-05-16",
    )
    membership = tmp_path / "historical_membership.csv"
    rebuilt.membership.to_csv(membership, index=False)

    current_reference = tmp_path / "current_reference.csv"
    current_reconstructed = tmp_path / "current_reconstructed.csv"
    pd.DataFrame({"SP_ENTITY_ID": ["10", "20"]}).to_csv(current_reference, index=False)
    pd.DataFrame({"SP_ENTITY_ID": ["10", "20"]}).to_csv(current_reconstructed, index=False)
    parity_payload = build_current_screen_parity_receipt(
        reference_membership_path=current_reference,
        reconstructed_membership_path=current_reconstructed,
        reference_source_id="SPCIQPRO:COMPANIES_SCREENER_RESULT",
        parity_as_of_date="2026-08-07",
    )
    parity = tmp_path / "parity.receipt.json"
    parity.write_text(json.dumps(parity_payload), encoding="utf-8")

    final_payload = build_reconstruction_receipt(
        membership_path=membership,
        market_receipt_path=market,
        company_state_receipt_path=company,
        revenue_receipt_path=revenue,
        parity_receipt_path=parity,
        as_of_date="2025-05-16",
    )
    final = tmp_path / "historical_membership.receipt.json"
    final.write_text(json.dumps(final_payload), encoding="utf-8")
    admitted = load_historical_start_risk_set(
        membership, final, expected_as_of_date="2025-05-16"
    )
    assert admitted.entity_ids == ("1",)
    assert admitted.metadata["screen_reconstruction"] is True

    # A claimed extra member cannot be admitted even if the outer receipt's
    # raw-object hash/count are updated to match the tampered file.
    pd.DataFrame({"SP_ENTITY_ID": ["1", "2"], "CompanyName": ["A", "B"]}).to_csv(
        membership, index=False
    )
    tampered = json.loads(final.read_text(encoding="utf-8"))
    tampered["raw_object_sha256"] = _sha(membership)
    tampered["raw_object_bytes"] = membership.stat().st_size
    tampered["result_count"] = 2
    final.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="compiler_membership_mismatch"):
        load_historical_start_risk_set(
            membership, final, expected_as_of_date="2025-05-16"
        )
