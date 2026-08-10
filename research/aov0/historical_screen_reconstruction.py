"""Deterministic reconstruction of the frozen AOV high-growth source screen.

This module does not acquire provider data.  It compiles three independently
admitted historical components:

1. historical market candidates (historical pricing date + primary exchange),
2. historical company type/status state, and
3. historical Original-filing annual revenue values for LFY..FY-3.

All company-state/revenue captures must prove that they requested the *exact*
market-candidate cohort.  This prevents incomplete provider capture from being
silently interpreted as a failed screen criterion.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from research.aov0.historical_risk_set import (
    AOV_HIGH_GROWTH_SCREEN_CRITERIA,
    AOV_HIGH_GROWTH_SCREEN_LAW_HASH,
    HISTORICAL_SCREEN_FREEZE_MODE,
    HISTORICAL_SCREEN_RECON_CAPTURE_MODE,
    HISTORICAL_SCREEN_RECON_LOGIC,
    HISTORICAL_SCREEN_RECON_RECEIPT_SCHEMA,
    HISTORICAL_SCREEN_RECON_SOURCE_ID,
)


HISTORICAL_COMPANY_STATE_RECEIPT_SCHEMA = "aov0_historical_company_state_receipt_v1"
HISTORICAL_ANNUAL_REVENUE_RECEIPT_SCHEMA = "aov0_historical_annual_revenue_receipt_v1"
HISTORICAL_SCREEN_PARITY_RECEIPT_SCHEMA = "aov0_historical_screen_current_parity_receipt_v1"
XPRESSAPI_MARKET_CANDIDATE_MERGED_SCHEMA = (
    "aov0_xpressapi_historical_screen_market_candidate_merged_receipt_v1"
)
CIQ_SECURITIES_MARKET_CANDIDATE_RECEIPT_SCHEMA = (
    "aov0_ciq_securities_historical_market_candidate_receipt_v1"
)
CIQ_MARKET_ORIGINAL_REVENUE_CANDIDATE_RECEIPT_SCHEMA = (
    "aov0_ciq_historical_market_original_revenue_candidate_receipt_v1"
)
CIQ_MARKET_ORIGINAL_REVENUE_CANDIDATE_SOURCE_ID = (
    "SPCIQPRO:SECURITIES_PRODUCTQUERY+COMPANIES_PRODUCTQUERY"
)
CIQ_SECURITIES_MARKET_CANDIDATE_SOURCE_ID = "SPCIQPRO:SECURITIES_PRODUCTQUERY"
CIQ_SECURITIES_MARKET_PERSPECTIVE = "321247"
CIQ_SECURITIES_PRICE_FIELD_KEY = "324251"
CIQ_SECURITIES_PRICE_DATE_SECONDARY_KEY = "sk_557"
CIQ_SECURITIES_EXCHANGE_GROUP_FIELD_KEY = "406718"
CIQ_SECURITIES_MAJOR_US_EXCHANGE_GROUP_VALUE = "-1,-4"
CIQ_SECURITIES_FUNDING_TYPE_FIELD_KEY = "321268"
CIQ_SECURITIES_FUNDING_TYPE_VALUES = ("1", "16")
CIQ_SECURITIES_MAJOR_US_EXCHANGE_CODES = {
    "NYSE": "0",
    "NYSEAM": "1",
    "NASDAQGM": "2",
    "NASDAQCM": "211",
    "NASDAQGS": "212",
}
CIQ_SECURITIES_EXCLUDED_ARCA_CODE = "33"
REVENUE_PERIODS = ("LFY", "FY-1", "FY-2", "FY-3")
GROWTH_MULTIPLIER = 1.3
ALLOWED_COMPANY_TYPES = ("Public Company",)
ALLOWED_COMPANY_STATUSES = ("Operating", "Operating Subsidiary")
CIQ_RECONSTRUCTED_COMPANY_STATE_SOURCE_ID = (
    "SPCIQPRO:SECURITIES_PRODUCTQUERY+KEY_DEVELOPMENTS_PRODUCTQUERY"
)
CIQ_RECONSTRUCTED_COMPANY_STATE_LAW = (
    "DATED_MAJOR_US_COMMON_OR_DR_LISTING_WITH_TERMINAL_TRANSITION_CHECK_V1"
)
CIQ_RECONSTRUCTED_COMPANY_STATUS_OUTPUT = "ELIGIBLE_OPERATING_BUCKET_NOT_SUBSIDIARY_CLASSIFICATION"
CIQ_KEY_DEVELOPMENTS_PERSPECTIVE = "311682"
CIQ_KEY_DEVELOPMENTS_ENTITY_FIELD_KEY = "398876"
CIQ_KEY_DEVELOPMENTS_DATE_FIELD_KEY = "311764"
CIQ_HISTORICAL_REVENUE_SOURCE_ID = "SPCIQPRO:COMPANIES_PRODUCTQUERY"
CIQ_HISTORICAL_REVENUE_FIELD_KEY = "329288"
CIQ_HISTORICAL_REVENUE_PERIOD_SECONDARY_KEY = "sk_854"
CIQ_HISTORICAL_REVENUE_REPORTING_BASIS_SECONDARY_KEY = "sk_858"
CIQ_HISTORICAL_REVENUE_ASOF_SECONDARY_KEY = "sk_860"


class HistoricalScreenReconstructionError(ValueError):
    """Fail-closed screen reconstruction/parity error."""


@dataclass(frozen=True)
class ReconstructedHistoricalScreen:
    membership: pd.DataFrame
    audit: pd.DataFrame
    metadata: dict[str, Any]


def _sha256_file(path: str | Path) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_entity_ids(values: Iterable[object]) -> tuple[str, ...]:
    normalized = tuple(sorted(str(value).strip() for value in values if str(value).strip()))
    if not normalized:
        raise HistoricalScreenReconstructionError("historical_screen_entity_membership_empty")
    if len(normalized) != len(set(normalized)):
        raise HistoricalScreenReconstructionError("historical_screen_entity_membership_duplicate")
    if any(not value.isdigit() for value in normalized):
        raise HistoricalScreenReconstructionError("historical_screen_entity_membership_invalid")
    return normalized


def entity_membership_hash(values: Iterable[object]) -> str:
    ids = _canonical_entity_ids(values)
    raw = json.dumps(ids, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _read_receipt(path: Path, *, schema: str, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        receipt = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise HistoricalScreenReconstructionError(f"historical_screen_{label}_receipt_json_invalid") from exc
    if receipt.get("schema_version") != schema:
        raise HistoricalScreenReconstructionError(f"historical_screen_{label}_receipt_schema_invalid")
    if receipt.get("financial_alpha_evidence") != 0:
        raise HistoricalScreenReconstructionError(f"historical_screen_{label}_financial_authority_invalid")
    if receipt.get("prospective_clock_authority") != "NONE":
        raise HistoricalScreenReconstructionError(f"historical_screen_{label}_prospective_authority_invalid")
    if receipt.get("parent_child_mutation_authority") != "NONE":
        raise HistoricalScreenReconstructionError(f"historical_screen_{label}_mutation_authority_invalid")
    return receipt


def _bound_csv(
    receipt_path: Path,
    receipt: Mapping[str, Any],
    *,
    label: str,
    name_field: str = "normalized_csv_name",
    hash_field: str = "normalized_csv_sha256",
    bytes_field: str = "normalized_csv_bytes",
) -> Path:
    name = str(receipt.get(name_field) or "").strip()
    if not name:
        raise HistoricalScreenReconstructionError(f"historical_screen_{label}_csv_name_missing")
    path = receipt_path.parent / name
    if not path.is_file():
        raise HistoricalScreenReconstructionError(f"historical_screen_{label}_csv_missing")
    if receipt.get(hash_field) != _sha256_file(path):
        raise HistoricalScreenReconstructionError(f"historical_screen_{label}_csv_hash_mismatch")
    if int(receipt.get(bytes_field, -1)) != path.stat().st_size:
        raise HistoricalScreenReconstructionError(f"historical_screen_{label}_csv_size_mismatch")
    return path


def _validate_ciq_securities_market_receipt(
    receipt: Mapping[str, Any], *, expected_date: pd.Timestamp
) -> None:
    if receipt.get("source_id") != CIQ_SECURITIES_MARKET_CANDIDATE_SOURCE_ID:
        raise HistoricalScreenReconstructionError("historical_screen_market_source_invalid")
    if receipt.get("capture_scope") != "HISTORICAL_MARKET_CANDIDATES_ONLY":
        raise HistoricalScreenReconstructionError("historical_screen_market_scope_invalid")
    if str(receipt.get("market_perspective") or "") != CIQ_SECURITIES_MARKET_PERSPECTIVE:
        raise HistoricalScreenReconstructionError("historical_screen_market_perspective_invalid")
    if str(receipt.get("price_field_key") or "") != CIQ_SECURITIES_PRICE_FIELD_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_market_price_field_invalid")
    if str(receipt.get("price_date_secondary_key") or "") != CIQ_SECURITIES_PRICE_DATE_SECONDARY_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_market_price_date_key_invalid")
    if str(receipt.get("exchange_group_field_key") or "") != CIQ_SECURITIES_EXCHANGE_GROUP_FIELD_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_market_exchange_field_invalid")
    if str(receipt.get("exchange_group_value") or "") != CIQ_SECURITIES_MAJOR_US_EXCHANGE_GROUP_VALUE:
        raise HistoricalScreenReconstructionError("historical_screen_market_exchange_group_invalid")
    if str(receipt.get("funding_type_field_key") or "") != CIQ_SECURITIES_FUNDING_TYPE_FIELD_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_market_funding_field_invalid")
    funding_values = tuple(str(value) for value in receipt.get("funding_type_values") or ())
    if funding_values != CIQ_SECURITIES_FUNDING_TYPE_VALUES:
        raise HistoricalScreenReconstructionError("historical_screen_market_funding_values_invalid")

    parity = receipt.get("major_us_exchange_group_parity")
    if not isinstance(parity, Mapping):
        raise HistoricalScreenReconstructionError("historical_screen_market_exchange_parity_missing")
    if parity.get("exact_match") is not True:
        raise HistoricalScreenReconstructionError("historical_screen_market_exchange_parity_failed")
    try:
        parity_date = pd.Timestamp(parity.get("as_of_date")).normalize()
    except Exception as exc:  # pragma: no cover - pandas exception is version-specific.
        raise HistoricalScreenReconstructionError("historical_screen_market_exchange_parity_date_invalid") from exc
    if parity_date != expected_date:
        raise HistoricalScreenReconstructionError("historical_screen_market_exchange_parity_date_mismatch")
    expected_codes = CIQ_SECURITIES_MAJOR_US_EXCHANGE_CODES
    observed_codes = {
        str(key): str(value) for key, value in (parity.get("explicit_exchange_codes") or {}).items()
    }
    if observed_codes != expected_codes:
        raise HistoricalScreenReconstructionError("historical_screen_market_exchange_codes_invalid")
    if str(parity.get("excluded_arca_code") or "") != CIQ_SECURITIES_EXCLUDED_ARCA_CODE:
        raise HistoricalScreenReconstructionError("historical_screen_market_arca_exclusion_invalid")
    try:
        group_rows = int(parity.get("group_security_row_count", -1))
        explicit_rows = int(parity.get("explicit_union_security_row_count", -1))
        group_only = int(parity.get("group_only_count", -1))
        explicit_only = int(parity.get("explicit_only_count", -1))
    except (TypeError, ValueError) as exc:
        raise HistoricalScreenReconstructionError("historical_screen_market_exchange_parity_counts_invalid") from exc
    if group_rows < 1 or group_rows != explicit_rows or group_only != 0 or explicit_only != 0:
        raise HistoricalScreenReconstructionError("historical_screen_market_exchange_parity_counts_mismatch")
    try:
        source_rows = int(receipt.get("source_security_row_count", -1))
        result_entities = int(receipt.get("result_entity_count", -1))
    except (TypeError, ValueError) as exc:
        raise HistoricalScreenReconstructionError("historical_screen_market_result_counts_invalid") from exc
    if source_rows != group_rows or result_entities < 1 or result_entities > source_rows:
        raise HistoricalScreenReconstructionError("historical_screen_market_result_counts_mismatch")


def _validate_ciq_market_original_revenue_candidate_receipt(
    receipt: Mapping[str, Any], *, expected_date: pd.Timestamp
) -> dict[str, Any]:
    if receipt.get("source_id") != CIQ_MARKET_ORIGINAL_REVENUE_CANDIDATE_SOURCE_ID:
        raise HistoricalScreenReconstructionError("historical_screen_market_source_invalid")
    if receipt.get("capture_scope") != "HISTORICAL_MARKET_ORIGINAL_REVENUE_CANDIDATES_ONLY_NOT_A1_RISK_SET":
        raise HistoricalScreenReconstructionError("historical_screen_market_scope_invalid")
    market = receipt.get("market_component")
    revenue = receipt.get("revenue_component")
    intersection = receipt.get("intersection")
    if not isinstance(market, Mapping) or not isinstance(revenue, Mapping) or not isinstance(intersection, Mapping):
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_component_missing")
    projected_market = {
        **receipt,
        **market,
        "source_id": market.get("source_id"),
        "capture_scope": "HISTORICAL_MARKET_CANDIDATES_ONLY",
        "result_entity_count": market.get("source_entity_count"),
    }
    _validate_ciq_securities_market_receipt(projected_market, expected_date=expected_date)
    if revenue.get("source_id") != CIQ_HISTORICAL_REVENUE_SOURCE_ID:
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_revenue_source_invalid")
    if str(revenue.get("companies_perspective") or "") != "266637":
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_revenue_perspective_invalid")
    if str(revenue.get("field_key") or "") != CIQ_HISTORICAL_REVENUE_FIELD_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_revenue_field_invalid")
    if revenue.get("filing_version") != "Original" or revenue.get("reporting_basis") != "Originally Reported":
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_revenue_vintage_invalid")
    if revenue.get("historical_as_of_mechanically_bound") is not True:
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_revenue_asof_not_bound")
    if str(revenue.get("as_of_secondary_key") or "") != CIQ_HISTORICAL_REVENUE_ASOF_SECONDARY_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_revenue_asof_key_invalid")
    if str(revenue.get("period_secondary_key") or "") != CIQ_HISTORICAL_REVENUE_PERIOD_SECONDARY_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_revenue_period_key_invalid")
    if tuple(str(value) for value in revenue.get("periods") or ()) != ("FY0", "FY-1", "FY-2", "FY-3"):
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_revenue_periods_invalid")
    if revenue.get("provider_formula_validation_passed") is not True:
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_formula_validation_missing")
    if float(revenue.get("growth_multiplier", 0)) != GROWTH_MULTIPLIER:
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_growth_multiplier_invalid")
    if int(intersection.get("candidate_count", -1)) < 1:
        raise HistoricalScreenReconstructionError("historical_screen_market_partial_candidate_count_invalid")
    return dict(intersection)


def _read_market_receipt(
    path: Path, *, expected_date: pd.Timestamp
) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        probe = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise HistoricalScreenReconstructionError("historical_screen_market_receipt_json_invalid") from exc
    schema = str(probe.get("schema_version") or "")
    if schema == XPRESSAPI_MARKET_CANDIDATE_MERGED_SCHEMA:
        receipt = _read_receipt(path, schema=schema, label="market")
        if receipt.get("source_id") != "SPGLOBAL_XPRESSAPI:SCREENER":
            raise HistoricalScreenReconstructionError("historical_screen_market_source_invalid")
        csv_role = "merged"
    elif schema == CIQ_SECURITIES_MARKET_CANDIDATE_RECEIPT_SCHEMA:
        receipt = _read_receipt(path, schema=schema, label="market")
        _validate_ciq_securities_market_receipt(receipt, expected_date=expected_date)
        csv_role = "merged"
    elif schema == CIQ_MARKET_ORIGINAL_REVENUE_CANDIDATE_RECEIPT_SCHEMA:
        receipt = _read_receipt(path, schema=schema, label="market")
        intersection = _validate_ciq_market_original_revenue_candidate_receipt(
            receipt, expected_date=expected_date
        )
        receipt = dict(receipt)
        market_component = receipt.get("market_component") or {}
        receipt["historical_market_date_mechanically_bound"] = market_component.get(
            "historical_market_date_mechanically_bound"
        )
        receipt["current_company_state_filters_used"] = market_component.get(
            "current_company_state_filters_used"
        )
        receipt["intersection_csv_name"] = intersection.get("candidate_csv_name")
        receipt["intersection_csv_sha256"] = intersection.get("candidate_csv_sha256")
        receipt["intersection_csv_bytes"] = intersection.get("candidate_csv_bytes")
        csv_role = "intersection"
    else:
        raise HistoricalScreenReconstructionError("historical_screen_market_receipt_schema_invalid")
    return receipt, csv_role


def _normalize_market_candidates(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    required = {"SP_ENTITY_ID", "CompanyName"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise HistoricalScreenReconstructionError(
            "historical_screen_market_columns_missing:" + ",".join(missing)
        )
    out = frame.loc[:, ["SP_ENTITY_ID", "CompanyName"]].copy()
    out["SP_ENTITY_ID"] = out["SP_ENTITY_ID"].astype(str).str.strip()
    out["CompanyName"] = out["CompanyName"].astype(str).str.strip()
    ids = _canonical_entity_ids(out["SP_ENTITY_ID"])
    if len(ids) != len(out):
        raise HistoricalScreenReconstructionError("historical_screen_market_entity_duplicate")
    if out["CompanyName"].eq("").any():
        raise HistoricalScreenReconstructionError("historical_screen_market_company_name_blank")
    return out.sort_values("SP_ENTITY_ID", key=lambda s: s.astype(int)).reset_index(drop=True)


def _normalize_company_state(path: Path, *, expected_ids: tuple[str, ...]) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    required = {"SP_ENTITY_ID", "CompanyType", "CompanyStatus"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise HistoricalScreenReconstructionError(
            "historical_screen_company_state_columns_missing:" + ",".join(missing)
        )
    out = frame.loc[:, ["SP_ENTITY_ID", "CompanyType", "CompanyStatus"]].copy()
    for column in out.columns:
        out[column] = out[column].astype(str).str.strip()
    observed = _canonical_entity_ids(out["SP_ENTITY_ID"])
    if observed != expected_ids:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_membership_mismatch")
    return out.sort_values("SP_ENTITY_ID", key=lambda s: s.astype(int)).reset_index(drop=True)


def _normalize_revenue(path: Path, *, expected_ids: tuple[str, ...]) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    required = {"SP_ENTITY_ID", *REVENUE_PERIODS}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise HistoricalScreenReconstructionError(
            "historical_screen_revenue_columns_missing:" + ",".join(missing)
        )
    out = frame.loc[:, ["SP_ENTITY_ID", *REVENUE_PERIODS]].copy()
    out["SP_ENTITY_ID"] = out["SP_ENTITY_ID"].astype(str).str.strip()
    observed = _canonical_entity_ids(out["SP_ENTITY_ID"])
    if observed != expected_ids:
        raise HistoricalScreenReconstructionError("historical_screen_revenue_membership_mismatch")
    for column in REVENUE_PERIODS:
        text = out[column].astype(str).str.strip()
        numeric = pd.to_numeric(text.where(text.ne("")), errors="coerce")
        invalid = text.ne("") & numeric.isna()
        if invalid.any():
            raise HistoricalScreenReconstructionError(
                f"historical_screen_revenue_numeric_invalid:{column}"
            )
        out[column] = numeric.astype(float)
    return out.sort_values("SP_ENTITY_ID", key=lambda s: s.astype(int)).reset_index(drop=True)


def _validate_component_cohort(
    receipt: Mapping[str, Any],
    *,
    label: str,
    expected_ids: tuple[str, ...],
) -> None:
    expected_hash = entity_membership_hash(expected_ids)
    if int(receipt.get("requested_entity_count", -1)) != len(expected_ids):
        raise HistoricalScreenReconstructionError(
            f"historical_screen_{label}_requested_entity_count_mismatch"
        )
    if receipt.get("requested_entity_membership_sha256") != expected_hash:
        raise HistoricalScreenReconstructionError(
            f"historical_screen_{label}_requested_entity_hash_mismatch"
        )
    if receipt.get("requested_entity_coverage_complete") is not True:
        raise HistoricalScreenReconstructionError(
            f"historical_screen_{label}_requested_entity_coverage_incomplete"
        )


def reconstruct_historical_screen(
    *,
    market_receipt_path: str | Path,
    company_state_receipt_path: str | Path,
    revenue_receipt_path: str | Path,
    expected_as_of_date: str | pd.Timestamp,
) -> ReconstructedHistoricalScreen:
    """Compile the exact screen law from three historical, cohort-bound components."""

    expected_date = pd.Timestamp(expected_as_of_date).normalize()
    market_receipt_path = Path(market_receipt_path)
    company_state_receipt_path = Path(company_state_receipt_path)
    revenue_receipt_path = Path(revenue_receipt_path)

    market_receipt, market_csv_role = _read_market_receipt(
        market_receipt_path, expected_date=expected_date
    )
    if market_receipt.get("historical_market_date_mechanically_bound") is not True:
        raise HistoricalScreenReconstructionError("historical_screen_market_asof_not_bound")
    if market_receipt.get("current_company_state_filters_used") is not False:
        raise HistoricalScreenReconstructionError("historical_screen_market_current_state_forbidden")
    if market_receipt.get("historical_risk_set_admission_authority") != "NONE":
        raise HistoricalScreenReconstructionError("historical_screen_market_authority_invalid")
    if pd.Timestamp(market_receipt.get("as_of_date")).normalize() != expected_date:
        raise HistoricalScreenReconstructionError("historical_screen_market_asof_mismatch")
    market_path = _bound_csv(
        market_receipt_path,
        market_receipt,
        label="market",
        name_field=f"{market_csv_role}_csv_name",
        hash_field=f"{market_csv_role}_csv_sha256",
        bytes_field=f"{market_csv_role}_csv_bytes",
    )
    market = _normalize_market_candidates(market_path)
    candidate_ids = _canonical_entity_ids(market["SP_ENTITY_ID"])

    company_receipt = _read_receipt(
        company_state_receipt_path,
        schema=HISTORICAL_COMPANY_STATE_RECEIPT_SCHEMA,
        label="company_state",
    )
    if pd.Timestamp(company_receipt.get("as_of_date")).normalize() != expected_date:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_asof_mismatch")
    if company_receipt.get("historical_as_of_mechanically_bound") is not True:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_asof_not_bound")
    if company_receipt.get("current_conditioned") is not False:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_current_conditioning_forbidden")
    if company_receipt.get("historical_company_type_reconstructed") is not True:
        raise HistoricalScreenReconstructionError("historical_screen_company_type_missing")
    if company_receipt.get("historical_company_status_reconstructed") is not True:
        raise HistoricalScreenReconstructionError("historical_screen_company_status_missing")
    if company_receipt.get("source_id") != CIQ_RECONSTRUCTED_COMPANY_STATE_SOURCE_ID:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_source_invalid")
    if company_receipt.get("reconstruction_law") != CIQ_RECONSTRUCTED_COMPANY_STATE_LAW:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_law_invalid")
    if company_receipt.get("status_output_semantics") != CIQ_RECONSTRUCTED_COMPANY_STATUS_OUTPUT:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_output_semantics_invalid")
    if str(company_receipt.get("market_perspective") or "") != CIQ_SECURITIES_MARKET_PERSPECTIVE:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_market_perspective_invalid")
    if str(company_receipt.get("price_field_key") or "") != CIQ_SECURITIES_PRICE_FIELD_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_price_field_invalid")
    if str(company_receipt.get("price_date_secondary_key") or "") != CIQ_SECURITIES_PRICE_DATE_SECONDARY_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_price_date_key_invalid")
    if str(company_receipt.get("exchange_group_field_key") or "") != CIQ_SECURITIES_EXCHANGE_GROUP_FIELD_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_exchange_field_invalid")
    if str(company_receipt.get("exchange_group_value") or "") != CIQ_SECURITIES_MAJOR_US_EXCHANGE_GROUP_VALUE:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_exchange_group_invalid")
    if str(company_receipt.get("funding_type_field_key") or "") != CIQ_SECURITIES_FUNDING_TYPE_FIELD_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_funding_field_invalid")
    if tuple(str(v) for v in company_receipt.get("funding_type_values") or ()) != CIQ_SECURITIES_FUNDING_TYPE_VALUES:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_funding_values_invalid")
    if str(company_receipt.get("key_developments_perspective") or "") != CIQ_KEY_DEVELOPMENTS_PERSPECTIVE:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_keydev_perspective_invalid")
    if str(company_receipt.get("key_developments_entity_field_key") or "") != CIQ_KEY_DEVELOPMENTS_ENTITY_FIELD_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_keydev_entity_field_invalid")
    if str(company_receipt.get("key_developments_date_field_key") or "") != CIQ_KEY_DEVELOPMENTS_DATE_FIELD_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_keydev_date_field_invalid")
    if company_receipt.get("current_company_type_status_values_used") is not False:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_current_values_forbidden")
    if int(company_receipt.get("key_developments_entity_coverage_count", -1)) != len(candidate_ids):
        raise HistoricalScreenReconstructionError("historical_screen_company_state_keydev_coverage_invalid")
    if int(company_receipt.get("key_developments_provider_row_count", -1)) < len(candidate_ids):
        raise HistoricalScreenReconstructionError("historical_screen_company_state_keydev_rows_invalid")
    if company_receipt.get("key_developments_response_exception") is not None:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_keydev_provider_exception")
    if int(company_receipt.get("unresolved_terminal_state_count", -1)) != 0:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_terminal_state_unresolved")
    _validate_component_cohort(company_receipt, label="company_state", expected_ids=candidate_ids)
    audit_path = _bound_csv(
        company_state_receipt_path,
        company_receipt,
        label="company_state_keydev_audit",
        name_field="key_developments_audit_csv_name",
        hash_field="key_developments_audit_csv_sha256",
        bytes_field="key_developments_audit_csv_bytes",
    )
    audit = pd.read_csv(audit_path, dtype=str, encoding="utf-8-sig").fillna("")
    audit_required = {"SP_ENTITY_ID", "EventCount", "UnresolvedTerminalAtCutoff"}
    if not audit_required.issubset(audit.columns):
        raise HistoricalScreenReconstructionError("historical_screen_company_state_keydev_audit_columns_missing")
    audit["SP_ENTITY_ID"] = audit["SP_ENTITY_ID"].astype(str).str.strip()
    if _canonical_entity_ids(audit["SP_ENTITY_ID"]) != candidate_ids:
        raise HistoricalScreenReconstructionError("historical_screen_company_state_keydev_audit_membership_mismatch")
    event_counts = pd.to_numeric(audit["EventCount"], errors="coerce")
    if event_counts.isna().any() or event_counts.lt(1).any():
        raise HistoricalScreenReconstructionError("historical_screen_company_state_keydev_audit_coverage_invalid")
    unresolved = audit["UnresolvedTerminalAtCutoff"].astype(str).str.strip().str.lower()
    if not unresolved.isin({"false"}).all():
        raise HistoricalScreenReconstructionError("historical_screen_company_state_keydev_audit_unresolved")
    company_path = _bound_csv(company_state_receipt_path, company_receipt, label="company_state")
    company = _normalize_company_state(company_path, expected_ids=candidate_ids)

    revenue_receipt = _read_receipt(
        revenue_receipt_path,
        schema=HISTORICAL_ANNUAL_REVENUE_RECEIPT_SCHEMA,
        label="revenue",
    )
    if pd.Timestamp(revenue_receipt.get("as_of_date")).normalize() != expected_date:
        raise HistoricalScreenReconstructionError("historical_screen_revenue_asof_mismatch")
    if revenue_receipt.get("historical_as_of_mechanically_bound") is not True:
        raise HistoricalScreenReconstructionError("historical_screen_revenue_asof_not_bound")
    if revenue_receipt.get("current_conditioned") is not False:
        raise HistoricalScreenReconstructionError("historical_screen_revenue_current_conditioning_forbidden")
    if revenue_receipt.get("filing_version") != "Original":
        raise HistoricalScreenReconstructionError("historical_screen_revenue_vintage_invalid")
    if tuple(revenue_receipt.get("relative_periods") or ()) != REVENUE_PERIODS:
        raise HistoricalScreenReconstructionError("historical_screen_revenue_periods_invalid")
    if revenue_receipt.get("source_id") != CIQ_HISTORICAL_REVENUE_SOURCE_ID:
        raise HistoricalScreenReconstructionError("historical_screen_revenue_source_invalid")
    if str(revenue_receipt.get("companies_perspective") or "") != "266637":
        raise HistoricalScreenReconstructionError("historical_screen_revenue_perspective_invalid")
    if str(revenue_receipt.get("field_key") or "") != CIQ_HISTORICAL_REVENUE_FIELD_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_revenue_field_invalid")
    if revenue_receipt.get("reporting_basis") != "Originally Reported":
        raise HistoricalScreenReconstructionError("historical_screen_revenue_reporting_basis_invalid")
    if str(revenue_receipt.get("period_secondary_key") or "") != CIQ_HISTORICAL_REVENUE_PERIOD_SECONDARY_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_revenue_period_key_invalid")
    if str(revenue_receipt.get("reporting_basis_secondary_key") or "") != CIQ_HISTORICAL_REVENUE_REPORTING_BASIS_SECONDARY_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_revenue_reporting_basis_key_invalid")
    if str(revenue_receipt.get("as_of_secondary_key") or "") != CIQ_HISTORICAL_REVENUE_ASOF_SECONDARY_KEY:
        raise HistoricalScreenReconstructionError("historical_screen_revenue_asof_key_invalid")
    if revenue_receipt.get("provider_numeric_values_returned") is not True:
        raise HistoricalScreenReconstructionError("historical_screen_revenue_numeric_provider_proof_missing")
    _validate_component_cohort(revenue_receipt, label="revenue", expected_ids=candidate_ids)
    revenue_path = _bound_csv(revenue_receipt_path, revenue_receipt, label="revenue")
    revenue = _normalize_revenue(revenue_path, expected_ids=candidate_ids)

    joined = market.merge(company, on="SP_ENTITY_ID", how="inner", validate="one_to_one")
    joined = joined.merge(revenue, on="SP_ENTITY_ID", how="inner", validate="one_to_one")
    joined["company_type_pass"] = joined["CompanyType"].isin(ALLOWED_COMPANY_TYPES)
    joined["company_status_pass"] = joined["CompanyStatus"].isin(ALLOWED_COMPANY_STATUSES)
    joined["growth_lfy_fy1_pass"] = (
        joined["LFY"].notna()
        & joined["FY-1"].notna()
        & joined["LFY"].ge(joined["FY-1"] * GROWTH_MULTIPLIER)
    )
    joined["growth_fy1_fy2_pass"] = (
        joined["FY-1"].notna()
        & joined["FY-2"].notna()
        & joined["FY-1"].ge(joined["FY-2"] * GROWTH_MULTIPLIER)
    )
    joined["growth_fy2_fy3_pass"] = (
        joined["FY-2"].notna()
        & joined["FY-3"].notna()
        & joined["FY-2"].ge(joined["FY-3"] * GROWTH_MULTIPLIER)
    )
    pass_columns = [
        "company_type_pass",
        "company_status_pass",
        "growth_lfy_fy1_pass",
        "growth_fy1_fy2_pass",
        "growth_fy2_fy3_pass",
    ]
    joined["screen_pass"] = joined[pass_columns].all(axis=1)
    membership = joined.loc[joined["screen_pass"], ["SP_ENTITY_ID", "CompanyName"]].copy()
    membership = membership.sort_values("SP_ENTITY_ID", key=lambda s: s.astype(int)).reset_index(drop=True)
    if membership.empty:
        raise HistoricalScreenReconstructionError("historical_screen_reconstructed_membership_empty")

    metadata = {
        "as_of_date": expected_date.date().isoformat(),
        "candidate_count": len(candidate_ids),
        "candidate_membership_sha256": entity_membership_hash(candidate_ids),
        "result_count": len(membership),
        "reconstructed_membership_sha256": entity_membership_hash(membership["SP_ENTITY_ID"]),
        "screen_law_hash": AOV_HIGH_GROWTH_SCREEN_LAW_HASH,
        "growth_multiplier": GROWTH_MULTIPLIER,
        "revenue_periods": list(REVENUE_PERIODS),
        "criteria": list(AOV_HIGH_GROWTH_SCREEN_CRITERIA),
        "current_screen_conditioned": False,
        "financial_alpha_evidence": 0,
    }
    return ReconstructedHistoricalScreen(
        membership=membership,
        audit=joined.sort_values("SP_ENTITY_ID", key=lambda s: s.astype(int)).reset_index(drop=True),
        metadata=metadata,
    )


def build_current_screen_parity_receipt(
    *,
    reference_membership_path: str | Path,
    reconstructed_membership_path: str | Path,
    reference_source_id: str,
    parity_as_of_date: str | pd.Timestamp,
    provider_proof_path: str | Path | None = None,
) -> dict[str, Any]:
    """Prove exact current-date membership parity for the reconstruction law."""

    reference_membership_path = Path(reference_membership_path)
    reconstructed_membership_path = Path(reconstructed_membership_path)
    if not reference_membership_path.is_file() or not reconstructed_membership_path.is_file():
        raise FileNotFoundError("historical_screen_parity_membership_missing")
    reference = pd.read_csv(reference_membership_path, dtype=str, encoding="utf-8-sig").fillna("")
    reconstructed = pd.read_csv(
        reconstructed_membership_path, dtype=str, encoding="utf-8-sig"
    ).fillna("")
    if "SP_ENTITY_ID" not in reference or "SP_ENTITY_ID" not in reconstructed:
        raise HistoricalScreenReconstructionError("historical_screen_parity_entity_id_missing")
    reference_ids = _canonical_entity_ids(reference["SP_ENTITY_ID"])
    reconstructed_ids = _canonical_entity_ids(reconstructed["SP_ENTITY_ID"])
    exact = reference_ids == reconstructed_ids
    provider_proof: dict[str, Any] | None = None
    provider_proof_manifest: dict[str, Any] | None = None
    if provider_proof_path is not None:
        proof_path = Path(provider_proof_path)
        if not proof_path.is_file():
            raise FileNotFoundError(proof_path)
        try:
            provider_proof = json.loads(proof_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise HistoricalScreenReconstructionError(
                "historical_screen_parity_provider_proof_json_invalid"
            ) from exc
        if provider_proof.get("schema_version") != "aov0_ciq_current_screen_decomposed_parity_provider_proof_v1":
            raise HistoricalScreenReconstructionError(
                "historical_screen_parity_provider_proof_schema_invalid"
            )
        if provider_proof.get("exact_membership_parity") is not True:
            raise HistoricalScreenReconstructionError(
                "historical_screen_parity_provider_proof_failed"
            )
        if any(
            provider_proof.get(field) is not None
            for field in (
                "direct_response_exception",
                "state_response_exception",
                "revenue_response_exception",
            )
        ):
            raise HistoricalScreenReconstructionError(
                "historical_screen_parity_provider_response_exception"
            )
        if int(provider_proof.get("direct_count", -1)) != len(reference_ids):
            raise HistoricalScreenReconstructionError(
                "historical_screen_parity_provider_direct_count_mismatch"
            )
        if int(provider_proof.get("reconstructed_count", -1)) != len(reconstructed_ids):
            raise HistoricalScreenReconstructionError(
                "historical_screen_parity_provider_reconstructed_count_mismatch"
            )
        validations = provider_proof.get("formula_validations") or []
        if len(validations) != 3 or not all(
            isinstance(item, Mapping)
            and item.get("ok") is True
            and item.get("isValid") is True
            for item in validations
        ):
            raise HistoricalScreenReconstructionError(
                "historical_screen_parity_provider_formula_validation_invalid"
            )
        provider_proof_manifest = {
            "path": proof_path.resolve().as_posix(),
            "sha256": _sha256_file(proof_path),
            "bytes": proof_path.stat().st_size,
            "schema_version": provider_proof["schema_version"],
            "captured_at_utc": provider_proof.get("captured_at_utc"),
        }
    return {
        "schema_version": HISTORICAL_SCREEN_PARITY_RECEIPT_SCHEMA,
        "source_id": "AOV0:HISTORICAL_SCREEN_RECONSTRUCTION_PARITY",
        "parity_as_of_date": pd.Timestamp(parity_as_of_date).normalize().date().isoformat(),
        "reference_source_id": str(reference_source_id).strip(),
        "screen_law_hash": AOV_HIGH_GROWTH_SCREEN_LAW_HASH,
        "reference_membership_name": reference_membership_path.name,
        "reference_membership_sha256": _sha256_file(reference_membership_path),
        "reference_entity_membership_sha256": entity_membership_hash(reference_ids),
        "reference_result_count": len(reference_ids),
        "reconstructed_membership_name": reconstructed_membership_path.name,
        "reconstructed_membership_sha256": _sha256_file(reconstructed_membership_path),
        "reconstructed_entity_membership_sha256": entity_membership_hash(reconstructed_ids),
        "reconstructed_result_count": len(reconstructed_ids),
        "exact_membership_match": exact,
        "pass": exact,
        "provider_proof": provider_proof_manifest,
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }


def build_reconstruction_receipt(
    *,
    membership_path: str | Path,
    market_receipt_path: str | Path,
    company_state_receipt_path: str | Path,
    revenue_receipt_path: str | Path,
    parity_receipt_path: str | Path,
    as_of_date: str | pd.Timestamp,
) -> dict[str, Any]:
    """Build the only reconstruction receipt shape admitted by historical_risk_set."""

    membership_path = Path(membership_path)
    market_receipt_path = Path(market_receipt_path)
    company_state_receipt_path = Path(company_state_receipt_path)
    revenue_receipt_path = Path(revenue_receipt_path)
    parity_receipt_path = Path(parity_receipt_path)
    if not membership_path.is_file():
        raise FileNotFoundError(membership_path)
    membership = pd.read_csv(membership_path, dtype=str, encoding="utf-8-sig").fillna("")
    if "SP_ENTITY_ID" not in membership:
        raise HistoricalScreenReconstructionError("historical_screen_membership_entity_id_missing")
    ids = _canonical_entity_ids(membership["SP_ENTITY_ID"])

    parity = _read_receipt(
        parity_receipt_path,
        schema=HISTORICAL_SCREEN_PARITY_RECEIPT_SCHEMA,
        label="parity",
    )
    if parity.get("screen_law_hash") != AOV_HIGH_GROWTH_SCREEN_LAW_HASH:
        raise HistoricalScreenReconstructionError("historical_screen_parity_law_hash_invalid")
    if parity.get("pass") is not True or parity.get("exact_membership_match") is not True:
        raise HistoricalScreenReconstructionError("historical_screen_parity_not_passed")

    as_of = pd.Timestamp(as_of_date).normalize().date().isoformat()
    components = []
    for role, path in (
        ("market_candidates", market_receipt_path),
        ("historical_company_state", company_state_receipt_path),
        ("historical_annual_revenue", revenue_receipt_path),
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
        components.append(
            {
                "role": role,
                "receipt_path": path.resolve().as_posix(),
                "receipt_sha256": _sha256_file(path),
            }
        )
    return {
        "schema_version": HISTORICAL_SCREEN_RECON_RECEIPT_SCHEMA,
        "source_id": HISTORICAL_SCREEN_RECON_SOURCE_ID,
        "capture_mode": HISTORICAL_SCREEN_RECON_CAPTURE_MODE,
        "universe_freeze_mode": HISTORICAL_SCREEN_FREEZE_MODE,
        "historical_as_of_mechanically_bound": True,
        "current_screen_conditioned": False,
        "requested_cutoff_date": as_of,
        "provider_effective_as_of_date": as_of,
        "criteria": list(AOV_HIGH_GROWTH_SCREEN_CRITERIA),
        "screen_law_hash": AOV_HIGH_GROWTH_SCREEN_LAW_HASH,
        "reconstruction_logic": HISTORICAL_SCREEN_RECON_LOGIC,
        "growth_multiplier": GROWTH_MULTIPLIER,
        "revenue_periods": list(REVENUE_PERIODS),
        "component_receipts": components,
        "current_screen_parity": {
            "pass": True,
            "exact_membership_match": True,
            "screen_law_hash": AOV_HIGH_GROWTH_SCREEN_LAW_HASH,
            "reference_membership_sha256": str(parity["reference_membership_sha256"]),
            "reconstructed_membership_sha256": str(parity["reconstructed_membership_sha256"]),
            "parity_receipt_path": parity_receipt_path.resolve().as_posix(),
            "parity_receipt_sha256": _sha256_file(parity_receipt_path),
        },
        "raw_object_name": membership_path.name,
        "raw_object_sha256": _sha256_file(membership_path),
        "raw_object_bytes": membership_path.stat().st_size,
        "result_count": len(ids),
        "observed_identity_columns": ["SP_ENTITY_ID"],
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
