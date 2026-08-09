"""Fail-closed S&P XpressAPI historical Screener market-candidate capture.

This module deliberately solves only the provider-historical *market candidate*
part of the Lane-2 high-growth risk-set problem.  XpressAPI Screener supports a
historical ``pricingDate`` and ``primaryExchange`` filter, but its company type
and company status filters are separate Company Intelligence fields with no
historical-as-of parameter in the published request contract.  Likewise, the
API's numeric revenue filters cannot express the frozen screen's cross-period
30% growth comparisons.

Consequently, output from this module is never an A1 historical risk set.  It is
an immutable, hash-bound candidate object that can later be joined to separately
admitted historical company-state and Original-filing revenue evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd


XPRESSAPI_SCREENER_SOURCE_ID = "SPGLOBAL_XPRESSAPI:SCREENER"
XPRESSAPI_SCREENER_ENDPOINT = "https://xpressapi.marketplace.spglobal.com/screener/api/v1/screener"
XPRESSAPI_SCREEN_PLAN_SCHEMA = "aov0_xpressapi_historical_screen_market_candidate_plan_v1"
XPRESSAPI_SCREEN_PART_RECEIPT_SCHEMA = "aov0_xpressapi_historical_screen_market_candidate_part_receipt_v1"
XPRESSAPI_SCREEN_MERGED_RECEIPT_SCHEMA = "aov0_xpressapi_historical_screen_market_candidate_merged_receipt_v1"
XPRESSAPI_COUNTRY_CODES_PER_REQUEST = 50
XPRESSAPI_RESULT_HARD_CAP = 20_000


class XpressApiHistoricalScreenError(ValueError):
    """Fail-closed XpressAPI historical screen capture/merge error."""


@dataclass(frozen=True)
class XpressScreenPlan:
    payload: dict[str, Any]
    plan_hash: str


@dataclass(frozen=True)
class XpressScreenPart:
    frame: pd.DataFrame
    metadata: dict[str, Any]


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: str | Path) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def request_hash(request_payload: Mapping[str, Any]) -> str:
    return _sha256_bytes(_canonical_json_bytes(request_payload))


def _normalize_unique(values: Iterable[object], *, label: str) -> tuple[str, ...]:
    normalized = tuple(sorted({str(value).strip().upper() for value in values if str(value).strip()}))
    if not normalized:
        raise XpressApiHistoricalScreenError(f"xpressapi_{label}_required")
    return normalized


def build_market_candidate_request(
    *,
    as_of_date: str | pd.Timestamp,
    country_codes: Sequence[object],
    primary_exchanges: Sequence[object],
    max_results: int = XPRESSAPI_RESULT_HARD_CAP,
) -> dict[str, Any]:
    """Build one documented historical Market Data screen request.

    The request intentionally excludes ``companyType`` and ``companyStatus``.
    Their published Screener contract does not bind them to ``pricingDate``;
    using them here would silently reintroduce current-state conditioning.
    """

    as_of = pd.Timestamp(as_of_date).normalize()
    countries = _normalize_unique(country_codes, label="country_codes")
    exchanges = _normalize_unique(primary_exchanges, label="primary_exchanges")
    if len(countries) > XPRESSAPI_COUNTRY_CODES_PER_REQUEST:
        raise XpressApiHistoricalScreenError("xpressapi_country_code_filter_limit_exceeded")
    if len(exchanges) > XPRESSAPI_COUNTRY_CODES_PER_REQUEST:
        raise XpressApiHistoricalScreenError("xpressapi_exchange_filter_limit_exceeded")
    if not 1 <= int(max_results) <= XPRESSAPI_RESULT_HARD_CAP:
        raise XpressApiHistoricalScreenError("xpressapi_max_results_invalid")
    return {
        "maxResults": int(max_results),
        "filters": [
            {"filter": "countryCode", "filterValues": list(countries)},
            {"filter": "pricingDate", "filterValues": [as_of.date().isoformat()]},
            {"filter": "primaryExchange", "filterValues": list(exchanges)},
        ],
    }


def build_market_candidate_plan(
    *,
    as_of_date: str | pd.Timestamp,
    country_codes: Sequence[object],
    primary_exchanges: Sequence[object],
    country_code_universe_source: Mapping[str, Any],
    primary_exchange_source: Mapping[str, Any],
    chunk_size: int = XPRESSAPI_COUNTRY_CODES_PER_REQUEST,
) -> XpressScreenPlan:
    """Partition the provider country-code universe into deterministic requests."""

    as_of = pd.Timestamp(as_of_date).normalize()
    countries = _normalize_unique(country_codes, label="country_codes")
    exchanges = _normalize_unique(primary_exchanges, label="primary_exchanges")
    if not 1 <= int(chunk_size) <= XPRESSAPI_COUNTRY_CODES_PER_REQUEST:
        raise XpressApiHistoricalScreenError("xpressapi_country_chunk_size_invalid")
    for label, source in (
        ("country_code_universe", country_code_universe_source),
        ("primary_exchange", primary_exchange_source),
    ):
        if not isinstance(source, Mapping) or not source.get("source_id") or not source.get("sha256"):
            raise XpressApiHistoricalScreenError(f"xpressapi_{label}_source_binding_invalid")
        if not str(source["sha256"]).strip() or len(str(source["sha256"]).strip()) != 64:
            raise XpressApiHistoricalScreenError(f"xpressapi_{label}_source_hash_invalid")

    requests: list[dict[str, Any]] = []
    for index in range(0, len(countries), int(chunk_size)):
        batch = countries[index : index + int(chunk_size)]
        payload = build_market_candidate_request(
            as_of_date=as_of,
            country_codes=batch,
            primary_exchanges=exchanges,
        )
        requests.append(
            {
                "chunk_index": len(requests),
                "country_codes": list(batch),
                "request": payload,
                "request_sha256": request_hash(payload),
            }
        )

    plan = {
        "schema_version": XPRESSAPI_SCREEN_PLAN_SCHEMA,
        "source_id": XPRESSAPI_SCREENER_SOURCE_ID,
        "endpoint": XPRESSAPI_SCREENER_ENDPOINT,
        "as_of_date": as_of.date().isoformat(),
        "capture_scope": "HISTORICAL_MARKET_CANDIDATES_ONLY",
        "historical_market_date_mechanically_bound": True,
        "historical_company_type_reconstructed": False,
        "historical_company_status_reconstructed": False,
        "historical_growth_screen_reconstructed": False,
        "historical_risk_set_admission_authority": "NONE",
        "current_company_state_filters_used": False,
        "primary_exchanges": list(exchanges),
        "country_codes": list(countries),
        "country_code_count": len(countries),
        "country_code_universe_source": dict(country_code_universe_source),
        "primary_exchange_source": dict(primary_exchange_source),
        "requests": requests,
        "request_count": len(requests),
        "result_hard_cap_per_request": XPRESSAPI_RESULT_HARD_CAP,
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
    return XpressScreenPlan(payload=plan, plan_hash=_sha256_bytes(_canonical_json_bytes(plan)))


def validate_result_set(
    response_payload: Mapping[str, Any],
    *,
    request_payload: Mapping[str, Any],
) -> XpressScreenPart:
    """Validate one XpressAPI Screener result set without granting A1 authority."""

    if not isinstance(response_payload, Mapping):
        raise XpressApiHistoricalScreenError("xpressapi_response_not_object")
    required = {"currentPage", "currentPageSize", "totalPages", "totalResults", "results"}
    missing = sorted(required - set(response_payload))
    if missing:
        raise XpressApiHistoricalScreenError(
            "xpressapi_response_fields_missing:" + ",".join(missing)
        )
    try:
        current_page = int(response_payload["currentPage"])
        current_page_size = int(response_payload["currentPageSize"])
        total_pages = int(response_payload["totalPages"])
        total_results = int(response_payload["totalResults"])
    except (TypeError, ValueError) as exc:
        raise XpressApiHistoricalScreenError("xpressapi_response_pagination_invalid") from exc
    if current_page < 0 or current_page_size < 0 or total_pages < 0 or total_results < 0:
        raise XpressApiHistoricalScreenError("xpressapi_response_pagination_negative")
    if total_results >= XPRESSAPI_RESULT_HARD_CAP:
        raise XpressApiHistoricalScreenError("xpressapi_response_result_cap_saturated_refine_request")

    rows = response_payload["results"]
    if not isinstance(rows, list):
        raise XpressApiHistoricalScreenError("xpressapi_results_not_array")
    if len(rows) != current_page_size:
        raise XpressApiHistoricalScreenError("xpressapi_current_page_size_mismatch")
    if total_pages not in {0, 1}:
        # The published request schema exposes maxResults but no page input.
        # Refuse to silently assume pagination semantics that are not bound in
        # the contract used to create this acquisition implementation.
        raise XpressApiHistoricalScreenError("xpressapi_unimplemented_pagination_contract")
    if total_results != len(rows):
        raise XpressApiHistoricalScreenError("xpressapi_total_results_mismatch")

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise XpressApiHistoricalScreenError("xpressapi_company_row_not_object")
        company_id = str(row.get("companyId") or "").strip()
        company_name = str(row.get("companyName") or "").strip()
        if not company_id.isdigit():
            raise XpressApiHistoricalScreenError("xpressapi_company_id_invalid")
        if not company_name:
            raise XpressApiHistoricalScreenError("xpressapi_company_name_blank")
        if company_id in seen:
            raise XpressApiHistoricalScreenError("xpressapi_company_id_duplicate")
        seen.add(company_id)
        normalized.append({"SP_ENTITY_ID": company_id, "CompanyName": company_name})

    frame = pd.DataFrame(normalized, columns=["SP_ENTITY_ID", "CompanyName"])
    if not frame.empty:
        frame = frame.sort_values("SP_ENTITY_ID", key=lambda s: s.astype(int)).reset_index(drop=True)
    metadata = {
        "source_id": XPRESSAPI_SCREENER_SOURCE_ID,
        "endpoint": XPRESSAPI_SCREENER_ENDPOINT,
        "request_sha256": request_hash(request_payload),
        "result_count": len(frame),
        "current_page": current_page,
        "current_page_size": current_page_size,
        "total_pages": total_pages,
        "total_results": total_results,
        "historical_risk_set_admission_authority": "NONE",
        "financial_alpha_evidence": 0,
    }
    return XpressScreenPart(frame=frame, metadata=metadata)


def build_part_receipt(
    *,
    plan_path: str | Path,
    plan: Mapping[str, Any],
    chunk_index: int,
    raw_response_path: str | Path,
    normalized_csv_path: str | Path,
    retrieved_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build a token-free immutable receipt for one completed plan chunk."""

    plan_path = Path(plan_path)
    raw_response_path = Path(raw_response_path)
    normalized_csv_path = Path(normalized_csv_path)
    if plan.get("schema_version") != XPRESSAPI_SCREEN_PLAN_SCHEMA:
        raise XpressApiHistoricalScreenError("xpressapi_plan_schema_invalid")
    requests = plan.get("requests") or []
    if not 0 <= int(chunk_index) < len(requests):
        raise XpressApiHistoricalScreenError("xpressapi_plan_chunk_index_invalid")
    request_binding = requests[int(chunk_index)]
    if request_hash(request_binding["request"]) != request_binding.get("request_sha256"):
        raise XpressApiHistoricalScreenError("xpressapi_plan_request_hash_invalid")
    if not raw_response_path.is_file() or not normalized_csv_path.is_file():
        raise FileNotFoundError("xpressapi_part_output_missing")
    response = json.loads(raw_response_path.read_text(encoding="utf-8-sig"))
    validated = validate_result_set(response, request_payload=request_binding["request"])
    observed = pd.read_csv(normalized_csv_path, dtype=str, encoding="utf-8-sig").fillna("")
    expected = validated.frame.fillna("")
    if observed.to_dict(orient="records") != expected.to_dict(orient="records"):
        raise XpressApiHistoricalScreenError("xpressapi_part_normalized_csv_drift")

    retrieved = retrieved_at_utc or datetime.now(timezone.utc).isoformat()
    receipt = {
        "schema_version": XPRESSAPI_SCREEN_PART_RECEIPT_SCHEMA,
        "source_id": XPRESSAPI_SCREENER_SOURCE_ID,
        "endpoint": XPRESSAPI_SCREENER_ENDPOINT,
        "capture_scope": "HISTORICAL_MARKET_CANDIDATES_ONLY",
        "chunk_index": int(chunk_index),
        "as_of_date": str(plan["as_of_date"]),
        "country_codes": list(request_binding["country_codes"]),
        "primary_exchanges": list(plan["primary_exchanges"]),
        "request_sha256": str(request_binding["request_sha256"]),
        "plan_path": plan_path.resolve().as_posix(),
        "plan_sha256": sha256_file(plan_path),
        "raw_response_name": raw_response_path.name,
        "raw_response_sha256": sha256_file(raw_response_path),
        "raw_response_bytes": raw_response_path.stat().st_size,
        "normalized_csv_name": normalized_csv_path.name,
        "normalized_csv_sha256": sha256_file(normalized_csv_path),
        "normalized_csv_bytes": normalized_csv_path.stat().st_size,
        "result_count": len(expected),
        "retrieved_at_utc": retrieved,
        "authorization_material_persisted": False,
        "historical_market_date_mechanically_bound": True,
        "historical_company_type_reconstructed": False,
        "historical_company_status_reconstructed": False,
        "historical_growth_screen_reconstructed": False,
        "historical_risk_set_admission_authority": "NONE",
        "current_company_state_filters_used": False,
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
    return receipt


def merge_market_candidate_parts(
    *,
    plan_path: str | Path,
    part_receipt_paths: Sequence[str | Path],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Verify every planned country partition and merge unique candidates."""

    plan_path = Path(plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    if plan.get("schema_version") != XPRESSAPI_SCREEN_PLAN_SCHEMA:
        raise XpressApiHistoricalScreenError("xpressapi_plan_schema_invalid")
    expected_requests = plan.get("requests") or []
    if len(part_receipt_paths) != len(expected_requests):
        raise XpressApiHistoricalScreenError("xpressapi_part_receipt_count_mismatch")

    frames: list[pd.DataFrame] = []
    bindings: list[dict[str, Any]] = []
    observed_chunks: set[int] = set()
    for raw_path in part_receipt_paths:
        receipt_path = Path(raw_path)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        if receipt.get("schema_version") != XPRESSAPI_SCREEN_PART_RECEIPT_SCHEMA:
            raise XpressApiHistoricalScreenError("xpressapi_part_receipt_schema_invalid")
        if receipt.get("source_id") != XPRESSAPI_SCREENER_SOURCE_ID:
            raise XpressApiHistoricalScreenError("xpressapi_part_receipt_source_invalid")
        if receipt.get("historical_risk_set_admission_authority") != "NONE":
            raise XpressApiHistoricalScreenError("xpressapi_part_authority_escalation_forbidden")
        if receipt.get("authorization_material_persisted") is not False:
            raise XpressApiHistoricalScreenError("xpressapi_part_authorization_persistence_invalid")
        if receipt.get("plan_sha256") != sha256_file(plan_path):
            raise XpressApiHistoricalScreenError("xpressapi_part_plan_hash_mismatch")
        chunk = int(receipt.get("chunk_index", -1))
        if chunk in observed_chunks or not 0 <= chunk < len(expected_requests):
            raise XpressApiHistoricalScreenError("xpressapi_part_chunk_invalid_or_duplicate")
        observed_chunks.add(chunk)
        request_binding = expected_requests[chunk]
        if receipt.get("request_sha256") != request_binding.get("request_sha256"):
            raise XpressApiHistoricalScreenError("xpressapi_part_request_hash_mismatch")

        csv_path = receipt_path.parent / str(receipt.get("normalized_csv_name") or "")
        if not csv_path.is_file():
            raise XpressApiHistoricalScreenError("xpressapi_part_csv_missing")
        if receipt.get("normalized_csv_sha256") != sha256_file(csv_path):
            raise XpressApiHistoricalScreenError("xpressapi_part_csv_hash_mismatch")
        if int(receipt.get("normalized_csv_bytes", -1)) != csv_path.stat().st_size:
            raise XpressApiHistoricalScreenError("xpressapi_part_csv_size_mismatch")
        frame = pd.read_csv(csv_path, dtype=str, encoding="utf-8-sig").fillna("")
        if set(frame.columns) != {"SP_ENTITY_ID", "CompanyName"}:
            raise XpressApiHistoricalScreenError("xpressapi_part_csv_columns_invalid")
        if len(frame) != int(receipt.get("result_count", -1)):
            raise XpressApiHistoricalScreenError("xpressapi_part_result_count_mismatch")
        frames.append(frame)
        bindings.append(
            {
                "chunk_index": chunk,
                "receipt_name": receipt_path.name,
                "receipt_sha256": sha256_file(receipt_path),
                "normalized_csv_name": csv_path.name,
                "normalized_csv_sha256": sha256_file(csv_path),
            }
        )

    if observed_chunks != set(range(len(expected_requests))):
        raise XpressApiHistoricalScreenError("xpressapi_plan_partition_incomplete")
    merged = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame(
        columns=["SP_ENTITY_ID", "CompanyName"]
    )
    if not merged.empty:
        name_counts = merged.groupby("SP_ENTITY_ID")["CompanyName"].nunique(dropna=False)
        if (name_counts > 1).any():
            raise XpressApiHistoricalScreenError("xpressapi_candidate_company_name_conflict")
        merged = merged.drop_duplicates("SP_ENTITY_ID", keep="first")
        merged = merged.sort_values("SP_ENTITY_ID", key=lambda s: s.astype(int)).reset_index(drop=True)

    metadata = {
        "schema_version": XPRESSAPI_SCREEN_MERGED_RECEIPT_SCHEMA,
        "source_id": XPRESSAPI_SCREENER_SOURCE_ID,
        "endpoint": XPRESSAPI_SCREENER_ENDPOINT,
        "capture_scope": "HISTORICAL_MARKET_CANDIDATES_ONLY",
        "as_of_date": str(plan["as_of_date"]),
        "primary_exchanges": list(plan["primary_exchanges"]),
        "country_code_count": int(plan["country_code_count"]),
        "country_code_universe_source": dict(plan["country_code_universe_source"]),
        "primary_exchange_source": dict(plan["primary_exchange_source"]),
        "plan_name": plan_path.name,
        "plan_sha256": sha256_file(plan_path),
        "part_count": len(bindings),
        "parts": sorted(bindings, key=lambda value: int(value["chunk_index"])),
        "result_count": len(merged),
        "historical_market_date_mechanically_bound": True,
        "historical_company_type_reconstructed": False,
        "historical_company_status_reconstructed": False,
        "historical_growth_screen_reconstructed": False,
        "historical_risk_set_admission_authority": "NONE",
        "current_company_state_filters_used": False,
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
    return merged, metadata
