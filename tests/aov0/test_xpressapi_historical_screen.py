from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from research.aov0.xpressapi_historical_screen import (
    XPRESSAPI_RESULT_HARD_CAP,
    XpressApiHistoricalScreenError,
    build_market_candidate_plan,
    build_market_candidate_request,
    build_part_receipt,
    merge_market_candidate_parts,
    request_hash,
    validate_result_set,
)


def _source(source_id: str, seed: str) -> dict[str, object]:
    return {"source_id": source_id, "sha256": seed * 64}


def _response(*pairs: tuple[int, str]) -> dict[str, object]:
    rows = [{"companyId": company_id, "companyName": name} for company_id, name in pairs]
    return {
        "currentPage": 0,
        "currentPageSize": len(rows),
        "totalPages": 1 if rows else 0,
        "totalResults": len(rows),
        "results": rows,
    }


def test_market_candidate_request_binds_historical_date_without_current_company_state() -> None:
    payload = build_market_candidate_request(
        as_of_date="2025-05-16",
        country_codes=["USA", "CAN"],
        primary_exchanges=["NYSE", "NASDAQGS"],
    )
    filters = {item["filter"]: item for item in payload["filters"]}
    assert filters["pricingDate"]["filterValues"] == ["2025-05-16"]
    assert filters["countryCode"]["filterValues"] == ["CAN", "USA"]
    assert filters["primaryExchange"]["filterValues"] == ["NASDAQGS", "NYSE"]
    assert "companyType" not in filters
    assert "companyStatus" not in filters
    assert payload["maxResults"] == XPRESSAPI_RESULT_HARD_CAP


def test_market_candidate_plan_partitions_country_universe_and_has_no_a1_authority() -> None:
    plan = build_market_candidate_plan(
        as_of_date="2025-05-16",
        country_codes=[f"C{i:02d}" for i in range(7)],
        primary_exchanges=["NYSE", "NASDAQGS"],
        country_code_universe_source=_source("PROVIDER_COUNTRY_LOOKUP", "a"),
        primary_exchange_source=_source("FROZEN_MAJOR_US_EXCHANGES", "b"),
        chunk_size=3,
    ).payload
    assert plan["request_count"] == 3
    assert [len(item["country_codes"]) for item in plan["requests"]] == [3, 3, 1]
    assert plan["historical_market_date_mechanically_bound"] is True
    assert plan["historical_company_type_reconstructed"] is False
    assert plan["historical_company_status_reconstructed"] is False
    assert plan["historical_growth_screen_reconstructed"] is False
    assert plan["historical_risk_set_admission_authority"] == "NONE"
    assert plan["current_company_state_filters_used"] is False
    assert plan["financial_alpha_evidence"] == 0
    for item in plan["requests"]:
        assert item["request_sha256"] == request_hash(item["request"])


def test_result_set_rejects_saturation_pagination_and_duplicate_ids() -> None:
    request = build_market_candidate_request(
        as_of_date="2025-05-16",
        country_codes=["USA"],
        primary_exchanges=["NYSE"],
    )
    saturated = _response((1, "A"))
    saturated["totalResults"] = XPRESSAPI_RESULT_HARD_CAP
    with pytest.raises(XpressApiHistoricalScreenError, match="result_cap_saturated"):
        validate_result_set(saturated, request_payload=request)

    paged = _response((1, "A"))
    paged["totalPages"] = 2
    with pytest.raises(XpressApiHistoricalScreenError, match="unimplemented_pagination"):
        validate_result_set(paged, request_payload=request)

    duplicated = _response((1, "A"), (1, "A"))
    with pytest.raises(XpressApiHistoricalScreenError, match="company_id_duplicate"):
        validate_result_set(duplicated, request_payload=request)


def _write_part(
    root: Path,
    *,
    plan_path: Path,
    plan: dict[str, object],
    chunk: int,
    rows: tuple[tuple[int, str], ...],
) -> Path:
    stem = f"part_{chunk:03d}"
    raw = root / f"{stem}.raw.json"
    csv = root / f"{stem}.csv"
    receipt = root / f"{stem}.receipt.json"
    response = _response(*rows)
    raw.write_text(json.dumps(response), encoding="utf-8")
    validated = validate_result_set(
        response, request_payload=plan["requests"][chunk]["request"]  # type: ignore[index]
    )
    validated.frame.to_csv(csv, index=False)
    payload = build_part_receipt(
        plan_path=plan_path,
        plan=plan,
        chunk_index=chunk,
        raw_response_path=raw,
        normalized_csv_path=csv,
        retrieved_at_utc="2026-08-09T12:00:00+00:00",
    )
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    return receipt


def test_part_receipt_and_merge_are_hash_bound_token_free_and_non_authoritative(tmp_path: Path) -> None:
    plan_obj = build_market_candidate_plan(
        as_of_date="2025-05-16",
        country_codes=["CAN", "USA"],
        primary_exchanges=["NYSE"],
        country_code_universe_source=_source("PROVIDER_COUNTRY_LOOKUP", "a"),
        primary_exchange_source=_source("FROZEN_MAJOR_US_EXCHANGES", "b"),
        chunk_size=1,
    )
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan_obj.payload), encoding="utf-8")
    r0 = _write_part(
        tmp_path,
        plan_path=plan_path,
        plan=plan_obj.payload,
        chunk=0,
        rows=((1, "Alpha"), (2, "Beta")),
    )
    r1 = _write_part(
        tmp_path,
        plan_path=plan_path,
        plan=plan_obj.payload,
        chunk=1,
        rows=((2, "Beta"), (3, "Gamma")),
    )
    receipt = json.loads(r0.read_text(encoding="utf-8"))
    serialized = json.dumps(receipt)
    assert "Bearer" not in serialized
    assert receipt["authorization_material_persisted"] is False
    assert receipt["historical_risk_set_admission_authority"] == "NONE"

    merged, metadata = merge_market_candidate_parts(
        plan_path=plan_path,
        part_receipt_paths=[r1, r0],
    )
    assert merged["SP_ENTITY_ID"].tolist() == ["1", "2", "3"]
    assert metadata["part_count"] == 2
    assert metadata["historical_company_status_reconstructed"] is False
    assert metadata["historical_growth_screen_reconstructed"] is False
    assert metadata["historical_risk_set_admission_authority"] == "NONE"
    assert metadata["financial_alpha_evidence"] == 0


def test_merge_rejects_plan_tamper_and_conflicting_company_names(tmp_path: Path) -> None:
    plan_obj = build_market_candidate_plan(
        as_of_date="2025-05-16",
        country_codes=["CAN", "USA"],
        primary_exchanges=["NYSE"],
        country_code_universe_source=_source("PROVIDER_COUNTRY_LOOKUP", "a"),
        primary_exchange_source=_source("FROZEN_MAJOR_US_EXCHANGES", "b"),
        chunk_size=1,
    )
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan_obj.payload), encoding="utf-8")
    r0 = _write_part(
        tmp_path,
        plan_path=plan_path,
        plan=plan_obj.payload,
        chunk=0,
        rows=((2, "Beta"),),
    )
    r1 = _write_part(
        tmp_path,
        plan_path=plan_path,
        plan=plan_obj.payload,
        chunk=1,
        rows=((2, "Different Beta"),),
    )
    with pytest.raises(XpressApiHistoricalScreenError, match="company_name_conflict"):
        merge_market_candidate_parts(plan_path=plan_path, part_receipt_paths=[r0, r1])

    tampered = json.loads(plan_path.read_text(encoding="utf-8"))
    tampered["as_of_date"] = "2025-05-17"
    plan_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(XpressApiHistoricalScreenError, match="plan_hash_mismatch"):
        merge_market_candidate_parts(plan_path=plan_path, part_receipt_paths=[r0, r1])
