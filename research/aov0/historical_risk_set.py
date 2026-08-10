"""Fail-closed admission for the historical-start AOV source cohort.

A formal A1 replay must not borrow the current 2026 frozen 109 as its historical
universe.  The historical analogue of the prospective AOV launch is one exact
high-growth Companies screen evaluated at the A1 start date and then frozen for
the A1/A2 lineage.  This module admits only a hash-bound provider snapshot that
proves those semantics; everything else remains diagnostic-only.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


HISTORICAL_SCREEN_SOURCE_ID = "SPCIQPRO:COMPANIES_SCREENER_RESULT"
HISTORICAL_SCREEN_RECEIPT_SCHEMA = "aov0_ciq_historical_screen_capture_receipt_v1"
HISTORICAL_SCREEN_CAPTURE_MODE = "HISTORICAL_PIT_SCREEN_SNAPSHOT"
HISTORICAL_SCREEN_RECON_SOURCE_ID = "AOV0:HISTORICAL_SCREEN_RECONSTRUCTION"
HISTORICAL_SCREEN_RECON_RECEIPT_SCHEMA = "aov0_historical_screen_reconstruction_receipt_v1"
HISTORICAL_SCREEN_RECON_CAPTURE_MODE = "HISTORICAL_PIT_SCREEN_RECONSTRUCTION"
HISTORICAL_SCREEN_RECON_LOGIC = "AOV0_HIGH_GROWTH_SCREEN_RECONSTRUCTION_V1"
HISTORICAL_SCREEN_FREEZE_MODE = "HISTORICAL_START_SCREEN_FROZEN"

AOV_HIGH_GROWTH_SCREEN_CRITERIA = (
    "Exchange[Current] in Major US Exchanges",
    "Company Type in Public Company",
    "Company Status in Operating,Operating Subsidiary",
    "Total Revenue[Latest Fiscal Year] >= Total Revenue[FY-1] * 1.3",
    "Total Revenue[FY-1] >= Total Revenue[FY-2] * 1.3",
    "Total Revenue[FY-2] >= Total Revenue[FY-3] * 1.3",
)


def _canonical_json_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


AOV_HIGH_GROWTH_SCREEN_LAW_HASH = _canonical_json_hash(list(AOV_HIGH_GROWTH_SCREEN_CRITERIA))


class HistoricalRiskSetError(ValueError):
    """Fail-closed historical risk-set admission error."""


@dataclass(frozen=True)
class HistoricalRiskSet:
    entity_ids: tuple[str, ...]
    as_of_date: pd.Timestamp
    membership_path: Path
    receipt_path: Path
    metadata: dict[str, Any]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_bound_component_receipt(
    binding: Any,
    *,
    role: str,
    expected_as_of_date: pd.Timestamp | None = None,
) -> dict[str, Any]:
    if not isinstance(binding, dict):
        raise HistoricalRiskSetError(f"historical_screen_recon_component_binding_invalid:{role}")
    if binding.get("role") != role:
        raise HistoricalRiskSetError(f"historical_screen_recon_component_role_invalid:{role}")
    path_text = str(binding.get("receipt_path") or "").strip()
    if not path_text:
        raise HistoricalRiskSetError(f"historical_screen_recon_component_path_missing:{role}")
    path = Path(path_text)
    if not path.is_file():
        raise HistoricalRiskSetError(f"historical_screen_recon_component_file_missing:{role}")
    observed_hash = _sha256_file(path)
    if binding.get("receipt_sha256") != observed_hash:
        raise HistoricalRiskSetError(f"historical_screen_recon_component_hash_mismatch:{role}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise HistoricalRiskSetError(f"historical_screen_recon_component_json_invalid:{role}") from exc
    if payload.get("financial_alpha_evidence") != 0:
        raise HistoricalRiskSetError(f"historical_screen_recon_component_financial_authority_invalid:{role}")
    if payload.get("prospective_clock_authority") != "NONE":
        raise HistoricalRiskSetError(f"historical_screen_recon_component_prospective_authority_invalid:{role}")
    if payload.get("parent_child_mutation_authority") != "NONE":
        raise HistoricalRiskSetError(f"historical_screen_recon_component_mutation_authority_invalid:{role}")
    if expected_as_of_date is not None:
        date_value = payload.get("as_of_date") or payload.get("provider_effective_as_of_date")
        try:
            observed_date = pd.Timestamp(date_value).normalize()
        except Exception as exc:  # pragma: no cover - pandas exception is version-specific.
            raise HistoricalRiskSetError(f"historical_screen_recon_component_asof_invalid:{role}") from exc
        if observed_date != expected_as_of_date:
            raise HistoricalRiskSetError(f"historical_screen_recon_component_asof_mismatch:{role}")
    return payload


def _validate_reconstruction_receipt(
    receipt: dict[str, Any],
    *,
    expected_as_of_date: pd.Timestamp,
) -> tuple[str, ...]:
    if receipt.get("reconstruction_logic") != HISTORICAL_SCREEN_RECON_LOGIC:
        raise HistoricalRiskSetError("historical_screen_recon_logic_invalid")
    if receipt.get("growth_multiplier") != 1.3:
        raise HistoricalRiskSetError("historical_screen_recon_growth_multiplier_invalid")
    if tuple(receipt.get("revenue_periods") or ()) != ("LFY", "FY-1", "FY-2", "FY-3"):
        raise HistoricalRiskSetError("historical_screen_recon_revenue_periods_invalid")

    bindings = receipt.get("component_receipts") or []
    if not isinstance(bindings, list):
        raise HistoricalRiskSetError("historical_screen_recon_components_invalid")
    by_role = {str(binding.get("role")): binding for binding in bindings if isinstance(binding, dict)}
    required_roles = {"market_candidates", "historical_company_state", "historical_annual_revenue"}
    if set(by_role) != required_roles:
        raise HistoricalRiskSetError("historical_screen_recon_component_roles_invalid")

    market = _load_bound_component_receipt(
        by_role["market_candidates"], role="market_candidates", expected_as_of_date=expected_as_of_date
    )
    market_schema = market.get("schema_version")
    market_state = market
    expected_market_scope = "HISTORICAL_MARKET_CANDIDATES_ONLY"
    if market_schema == "aov0_xpressapi_historical_screen_market_candidate_merged_receipt_v1":
        if market.get("source_id") != "SPGLOBAL_XPRESSAPI:SCREENER":
            raise HistoricalRiskSetError("historical_screen_recon_market_source_invalid")
        if int(market.get("country_code_count", 0)) < 1 or int(market.get("part_count", 0)) < 1:
            raise HistoricalRiskSetError("historical_screen_recon_market_partition_invalid")
        if not isinstance(market.get("country_code_universe_source"), dict):
            raise HistoricalRiskSetError("historical_screen_recon_country_universe_source_missing")
        if not isinstance(market.get("primary_exchange_source"), dict):
            raise HistoricalRiskSetError("historical_screen_recon_exchange_source_missing")
    elif market_schema == "aov0_ciq_securities_historical_market_candidate_receipt_v1":
        if market.get("source_id") != "SPCIQPRO:SECURITIES_PRODUCTQUERY":
            raise HistoricalRiskSetError("historical_screen_recon_market_source_invalid")
        if str(market.get("market_perspective") or "") != "321247":
            raise HistoricalRiskSetError("historical_screen_recon_market_perspective_invalid")
        if str(market.get("price_field_key") or "") != "324251":
            raise HistoricalRiskSetError("historical_screen_recon_market_price_field_invalid")
        if str(market.get("price_date_secondary_key") or "") != "sk_557":
            raise HistoricalRiskSetError("historical_screen_recon_market_price_date_key_invalid")
        if str(market.get("exchange_group_field_key") or "") != "406718":
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_field_invalid")
        if str(market.get("exchange_group_value") or "") != "-1,-4":
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_group_invalid")
        if str(market.get("funding_type_field_key") or "") != "321268":
            raise HistoricalRiskSetError("historical_screen_recon_market_funding_field_invalid")
        if tuple(str(value) for value in market.get("funding_type_values") or ()) != ("1", "16"):
            raise HistoricalRiskSetError("historical_screen_recon_market_funding_values_invalid")
        parity = market.get("major_us_exchange_group_parity")
        if not isinstance(parity, dict) or parity.get("exact_match") is not True:
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_parity_invalid")
        if {str(k): str(v) for k, v in (parity.get("explicit_exchange_codes") or {}).items()} != {
            "NYSE": "0",
            "NYSEAM": "1",
            "NASDAQGM": "2",
            "NASDAQCM": "211",
            "NASDAQGS": "212",
        }:
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_codes_invalid")
        if str(parity.get("excluded_arca_code") or "") != "33":
            raise HistoricalRiskSetError("historical_screen_recon_market_arca_exclusion_invalid")
        try:
            parity_date = pd.Timestamp(parity.get("as_of_date")).normalize()
            group_rows = int(parity.get("group_security_row_count", -1))
            explicit_rows = int(parity.get("explicit_union_security_row_count", -1))
            group_only = int(parity.get("group_only_count", -1))
            explicit_only = int(parity.get("explicit_only_count", -1))
            source_rows = int(market.get("source_security_row_count", -1))
            result_entities = int(market.get("result_entity_count", -1))
        except Exception as exc:  # pragma: no cover - exact parser exception is version-specific.
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_parity_counts_invalid") from exc
        if parity_date != expected_as_of_date:
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_parity_date_mismatch")
        if group_rows < 1 or group_rows != explicit_rows or group_only != 0 or explicit_only != 0:
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_parity_counts_mismatch")
        if source_rows != group_rows or result_entities < 1 or result_entities > source_rows:
            raise HistoricalRiskSetError("historical_screen_recon_market_result_counts_mismatch")
    elif market_schema == "aov0_ciq_historical_market_original_revenue_candidate_receipt_v1":
        if market.get("source_id") != "SPCIQPRO:SECURITIES_PRODUCTQUERY+COMPANIES_PRODUCTQUERY":
            raise HistoricalRiskSetError("historical_screen_recon_market_source_invalid")
        market_component = market.get("market_component")
        revenue_component = market.get("revenue_component")
        intersection = market.get("intersection")
        if not isinstance(market_component, dict) or not isinstance(revenue_component, dict) or not isinstance(intersection, dict):
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_component_missing")
        market_state = market_component
        expected_market_scope = "HISTORICAL_MARKET_ORIGINAL_REVENUE_CANDIDATES_ONLY_NOT_A1_RISK_SET"
        if market_component.get("source_id") != "SPCIQPRO:SECURITIES_PRODUCTQUERY":
            raise HistoricalRiskSetError("historical_screen_recon_market_source_invalid")
        if str(market_component.get("market_perspective") or "") != "321247":
            raise HistoricalRiskSetError("historical_screen_recon_market_perspective_invalid")
        if str(market_component.get("price_field_key") or "") != "324251":
            raise HistoricalRiskSetError("historical_screen_recon_market_price_field_invalid")
        if str(market_component.get("price_date_secondary_key") or "") != "sk_557":
            raise HistoricalRiskSetError("historical_screen_recon_market_price_date_key_invalid")
        if str(market_component.get("exchange_group_field_key") or "") != "406718":
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_field_invalid")
        if str(market_component.get("exchange_group_value") or "") != "-1,-4":
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_group_invalid")
        if str(market_component.get("funding_type_field_key") or "") != "321268":
            raise HistoricalRiskSetError("historical_screen_recon_market_funding_field_invalid")
        if tuple(str(value) for value in market_component.get("funding_type_values") or ()) != ("1", "16"):
            raise HistoricalRiskSetError("historical_screen_recon_market_funding_values_invalid")
        parity = market_component.get("major_us_exchange_group_parity")
        if not isinstance(parity, dict) or parity.get("exact_match") is not True:
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_parity_invalid")
        if {str(k): str(v) for k, v in (parity.get("explicit_exchange_codes") or {}).items()} != {
            "NYSE": "0",
            "NYSEAM": "1",
            "NASDAQGM": "2",
            "NASDAQCM": "211",
            "NASDAQGS": "212",
        }:
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_codes_invalid")
        if str(parity.get("excluded_arca_code") or "") != "33":
            raise HistoricalRiskSetError("historical_screen_recon_market_arca_exclusion_invalid")
        try:
            parity_date = pd.Timestamp(parity.get("as_of_date")).normalize()
            group_rows = int(parity.get("group_security_row_count", -1))
            explicit_rows = int(parity.get("explicit_union_security_row_count", -1))
            group_only = int(parity.get("group_only_count", -1))
            explicit_only = int(parity.get("explicit_only_count", -1))
            source_rows = int(market_component.get("source_security_row_count", -1))
            result_entities = int(market_component.get("source_entity_count", -1))
        except Exception as exc:  # pragma: no cover - exact parser exception is version-specific.
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_parity_counts_invalid") from exc
        if parity_date != expected_as_of_date:
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_parity_date_mismatch")
        if group_rows < 1 or group_rows != explicit_rows or group_only != 0 or explicit_only != 0:
            raise HistoricalRiskSetError("historical_screen_recon_market_exchange_parity_counts_mismatch")
        if source_rows != group_rows or result_entities < 1 or result_entities > source_rows:
            raise HistoricalRiskSetError("historical_screen_recon_market_result_counts_mismatch")
        if revenue_component.get("source_id") != "SPCIQPRO:COMPANIES_PRODUCTQUERY":
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_revenue_source_invalid")
        if str(revenue_component.get("companies_perspective") or "") != "266637":
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_revenue_perspective_invalid")
        if str(revenue_component.get("field_key") or "") != "329288":
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_revenue_field_invalid")
        if revenue_component.get("filing_version") != "Original" or revenue_component.get("reporting_basis") != "Originally Reported":
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_revenue_vintage_invalid")
        if revenue_component.get("historical_as_of_mechanically_bound") is not True:
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_revenue_asof_not_bound")
        if str(revenue_component.get("as_of_secondary_key") or "") != "sk_860":
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_revenue_asof_key_invalid")
        if str(revenue_component.get("period_secondary_key") or "") != "sk_854":
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_revenue_period_key_invalid")
        if tuple(str(value) for value in revenue_component.get("periods") or ()) != ("FY0", "FY-1", "FY-2", "FY-3"):
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_revenue_periods_invalid")
        if revenue_component.get("provider_formula_validation_passed") is not True:
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_formula_validation_missing")
        if float(revenue_component.get("growth_multiplier", 0)) != 1.3:
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_growth_multiplier_invalid")
        if int(intersection.get("candidate_count", -1)) < 1:
            raise HistoricalRiskSetError("historical_screen_recon_market_partial_candidate_count_invalid")
    else:
        raise HistoricalRiskSetError("historical_screen_recon_market_schema_invalid")
    if market.get("capture_scope") != expected_market_scope:
        raise HistoricalRiskSetError("historical_screen_recon_market_scope_invalid")
    if market_state.get("historical_market_date_mechanically_bound") is not True:
        raise HistoricalRiskSetError("historical_screen_recon_market_date_not_bound")
    if market_state.get("current_company_state_filters_used") is not False:
        raise HistoricalRiskSetError("historical_screen_recon_market_current_state_forbidden")
    if market.get("historical_risk_set_admission_authority") != "NONE":
        raise HistoricalRiskSetError("historical_screen_recon_market_authority_invalid")

    company = _load_bound_component_receipt(
        by_role["historical_company_state"],
        role="historical_company_state",
        expected_as_of_date=expected_as_of_date,
    )
    if company.get("historical_as_of_mechanically_bound") is not True:
        raise HistoricalRiskSetError("historical_screen_recon_company_state_asof_not_bound")
    if company.get("current_conditioned") is not False:
        raise HistoricalRiskSetError("historical_screen_recon_company_state_current_conditioning_forbidden")
    if company.get("historical_company_type_reconstructed") is not True:
        raise HistoricalRiskSetError("historical_screen_recon_company_type_missing")
    if company.get("historical_company_status_reconstructed") is not True:
        raise HistoricalRiskSetError("historical_screen_recon_company_status_missing")

    revenue = _load_bound_component_receipt(
        by_role["historical_annual_revenue"],
        role="historical_annual_revenue",
        expected_as_of_date=expected_as_of_date,
    )
    if revenue.get("historical_as_of_mechanically_bound") is not True:
        raise HistoricalRiskSetError("historical_screen_recon_revenue_asof_not_bound")
    if revenue.get("current_conditioned") is not False:
        raise HistoricalRiskSetError("historical_screen_recon_revenue_current_conditioning_forbidden")
    if revenue.get("filing_version") != "Original":
        raise HistoricalRiskSetError("historical_screen_recon_revenue_vintage_invalid")
    if tuple(revenue.get("relative_periods") or ()) != ("LFY", "FY-1", "FY-2", "FY-3"):
        raise HistoricalRiskSetError("historical_screen_recon_revenue_periods_invalid")

    parity = receipt.get("current_screen_parity")
    if not isinstance(parity, dict):
        raise HistoricalRiskSetError("historical_screen_recon_current_parity_missing")
    if parity.get("exact_membership_match") is not True or parity.get("pass") is not True:
        raise HistoricalRiskSetError("historical_screen_recon_current_parity_failed")
    if parity.get("screen_law_hash") != AOV_HIGH_GROWTH_SCREEN_LAW_HASH:
        raise HistoricalRiskSetError("historical_screen_recon_current_parity_law_hash_invalid")
    for field in ("reference_membership_sha256", "reconstructed_membership_sha256"):
        value = str(parity.get(field) or "")
        if len(value) != 64:
            raise HistoricalRiskSetError(f"historical_screen_recon_current_parity_hash_invalid:{field}")

    # Re-run the deterministic compiler from the hash-bound component receipts.
    # A reconstruction receipt cannot self-certify an arbitrary membership.
    from research.aov0.historical_screen_reconstruction import (  # local import avoids module cycle
        reconstruct_historical_screen,
    )

    rebuilt = reconstruct_historical_screen(
        market_receipt_path=Path(str(by_role["market_candidates"]["receipt_path"])),
        company_state_receipt_path=Path(str(by_role["historical_company_state"]["receipt_path"])),
        revenue_receipt_path=Path(str(by_role["historical_annual_revenue"]["receipt_path"])),
        expected_as_of_date=expected_as_of_date,
    )
    rebuilt_ids = tuple(sorted(rebuilt.membership["SP_ENTITY_ID"].astype(str).tolist()))
    if not rebuilt_ids:
        raise HistoricalRiskSetError("historical_screen_recon_compiler_membership_empty")
    return rebuilt_ids


def load_historical_start_risk_set(
    membership_path: str | Path,
    receipt_path: str | Path,
    *,
    expected_as_of_date: str | pd.Timestamp,
) -> HistoricalRiskSet:
    membership_path = Path(membership_path)
    receipt_path = Path(receipt_path)
    if not membership_path.is_file():
        raise FileNotFoundError(membership_path)
    if not receipt_path.is_file():
        raise FileNotFoundError(receipt_path)

    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise HistoricalRiskSetError("historical_screen_receipt_json_invalid") from exc

    schema_version = receipt.get("schema_version")
    if schema_version == HISTORICAL_SCREEN_RECEIPT_SCHEMA:
        expected_source_id = HISTORICAL_SCREEN_SOURCE_ID
        expected_capture_mode = HISTORICAL_SCREEN_CAPTURE_MODE
    elif schema_version == HISTORICAL_SCREEN_RECON_RECEIPT_SCHEMA:
        expected_source_id = HISTORICAL_SCREEN_RECON_SOURCE_ID
        expected_capture_mode = HISTORICAL_SCREEN_RECON_CAPTURE_MODE
    else:
        raise HistoricalRiskSetError("historical_screen_receipt_schema_invalid")
    if receipt.get("source_id") != expected_source_id:
        raise HistoricalRiskSetError("historical_screen_source_invalid")
    if receipt.get("capture_mode") != expected_capture_mode:
        raise HistoricalRiskSetError("historical_screen_capture_mode_invalid")
    if receipt.get("universe_freeze_mode") != HISTORICAL_SCREEN_FREEZE_MODE:
        raise HistoricalRiskSetError("historical_screen_freeze_mode_invalid")
    if receipt.get("historical_as_of_mechanically_bound") is not True:
        raise HistoricalRiskSetError("historical_screen_asof_not_mechanically_bound")
    if receipt.get("current_screen_conditioned") is not False:
        raise HistoricalRiskSetError("historical_screen_current_conditioning_forbidden")
    if receipt.get("financial_alpha_evidence") != 0:
        raise HistoricalRiskSetError("historical_screen_financial_alpha_evidence_invalid")
    if receipt.get("prospective_clock_authority") != "NONE":
        raise HistoricalRiskSetError("historical_screen_prospective_authority_invalid")
    if receipt.get("parent_child_mutation_authority") != "NONE":
        raise HistoricalRiskSetError("historical_screen_mutation_authority_invalid")

    expected_date = pd.Timestamp(expected_as_of_date).normalize()
    for field in ("requested_cutoff_date", "provider_effective_as_of_date"):
        try:
            observed = pd.Timestamp(receipt.get(field)).normalize()
        except Exception as exc:  # pragma: no cover - exact pandas exception is version-specific.
            raise HistoricalRiskSetError(f"historical_screen_{field}_invalid") from exc
        if observed != expected_date:
            raise HistoricalRiskSetError(f"historical_screen_{field}_mismatch")

    reconstructed_entity_ids: tuple[str, ...] | None = None
    if schema_version == HISTORICAL_SCREEN_RECON_RECEIPT_SCHEMA:
        reconstructed_entity_ids = _validate_reconstruction_receipt(
            receipt, expected_as_of_date=expected_date
        )

    criteria = tuple(str(value) for value in receipt.get("criteria") or ())
    if criteria != AOV_HIGH_GROWTH_SCREEN_CRITERIA:
        raise HistoricalRiskSetError("historical_screen_criteria_drift")
    if receipt.get("screen_law_hash") != AOV_HIGH_GROWTH_SCREEN_LAW_HASH:
        raise HistoricalRiskSetError("historical_screen_law_hash_invalid")

    raw_hash = _sha256_file(membership_path)
    if receipt.get("raw_object_sha256") != raw_hash:
        raise HistoricalRiskSetError("historical_screen_membership_hash_mismatch")
    if receipt.get("raw_object_name") != membership_path.name:
        raise HistoricalRiskSetError("historical_screen_membership_name_mismatch")
    if int(receipt.get("raw_object_bytes", -1)) != membership_path.stat().st_size:
        raise HistoricalRiskSetError("historical_screen_membership_size_mismatch")

    frame = pd.read_csv(membership_path, dtype=str, encoding="utf-8-sig")
    if "SP_ENTITY_ID" not in frame.columns:
        raise HistoricalRiskSetError("historical_screen_entity_id_missing")
    entity = frame["SP_ENTITY_ID"].fillna("").astype(str).str.strip()
    if entity.eq("").any():
        raise HistoricalRiskSetError("historical_screen_entity_id_blank")
    if entity.duplicated().any():
        raise HistoricalRiskSetError("historical_screen_entity_id_duplicate")
    if not entity.str.fullmatch(r"\d+").all():
        raise HistoricalRiskSetError("historical_screen_entity_id_invalid")
    entity_ids = tuple(sorted(entity.tolist()))
    if not entity_ids:
        raise HistoricalRiskSetError("historical_screen_membership_empty")
    if int(receipt.get("result_count", -1)) != len(entity_ids):
        raise HistoricalRiskSetError("historical_screen_result_count_mismatch")
    if reconstructed_entity_ids is not None and reconstructed_entity_ids != entity_ids:
        raise HistoricalRiskSetError("historical_screen_recon_compiler_membership_mismatch")
    observed_identity = tuple(str(value) for value in receipt.get("observed_identity_columns") or ())
    if "SP_ENTITY_ID" not in observed_identity:
        raise HistoricalRiskSetError("historical_screen_identity_authority_missing")

    metadata = {
        "source_id": expected_source_id,
        "capture_mode": expected_capture_mode,
        "receipt_schema_version": schema_version,
        "screen_reconstruction": schema_version == HISTORICAL_SCREEN_RECON_RECEIPT_SCHEMA,
        "universe_freeze_mode": HISTORICAL_SCREEN_FREEZE_MODE,
        "historical_screen_membership_reconstructed": True,
        "as_of_date": expected_date.date().isoformat(),
        "entity_count": len(entity_ids),
        "screen_law_hash": AOV_HIGH_GROWTH_SCREEN_LAW_HASH,
        "membership_path": membership_path.resolve().as_posix(),
        "membership_sha256": raw_hash,
        "receipt_path": receipt_path.resolve().as_posix(),
        "receipt_sha256": _sha256_file(receipt_path),
        "current_screen_conditioned": False,
        "financial_alpha_evidence": 0,
    }
    return HistoricalRiskSet(
        entity_ids=entity_ids,
        as_of_date=expected_date,
        membership_path=membership_path,
        receipt_path=receipt_path,
        metadata=metadata,
    )
