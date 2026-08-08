"""Frozen executable contract for ALPHA-ORGANISM-VERTICAL-0.

The contract intentionally chooses one engineering configuration. V0 has no
result-driven calibration and no compatibility aliases.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash


CONTRACT_SCHEMA = "aov0_ciq_executable_contract_v1"
SECURITY_ID_PREFIX = "CIQSEC:"
ACTIVE_PERMANENT_ID_TYPE = "ciq_security_id"
ACTIVE_IDENTITY_COLUMN = "security_id"
ACTIVE_TOTAL_RETURN_AUTHORITY = "SPCIQPRO_PRIMARY_SECURITY_TOTAL_RETURN_MATRIX_ONLY"
ACTIVE_EQUITY_DATA_AUTHORITY = "SPCIQPRO"
ACTIVE_FUNDAMENTAL_SOURCE = "SPCIQPRO_QUARTERLY_FUNDAMENTALS"
ACTIVE_SECURITY_MASTER_SOURCE = "SPCIQPRO_PRIMARY_SECURITY_MASTER"
ACTIVE_MARKET_DATA_SOURCE = "SPCIQPRO_PRIMARY_SECURITY_MARKET_DATA"
ACTIVE_ECONOMIC_CASH_SOURCE = "OFFICIAL_SOFR"
ACTIVE_ECONOMIC_CASH_QUOTE_CONVENTION = "SOFR_PERCENT_MINUS_25BP_ACT_360_SIMPLE_ACCRUAL"
ACTIVE_ECONOMIC_CASH_ROLL_POLICY = "OVERNIGHT_ACCRUAL_NO_PROXY_SUBSTITUTION"
ACTIVE_ECONOMIC_CASH_KNOWN_AT_RULE = "USE_ONLY_OFFICIAL_RATE_AFTER_PUBLICATION"


@dataclass(frozen=True)
class AOV0Contract:
    schema_version: str = CONTRACT_SCHEMA
    permanent_id_type: str = ACTIVE_PERMANENT_ID_TYPE
    identity_column: str = ACTIVE_IDENTITY_COLUMN
    security_id_namespace: str = "CIQSEC"
    universe_rule: str = "RULE100_DATE_LOCAL_ELIGIBLE_UNIVERSE"
    equity_data_authority: str = ACTIVE_EQUITY_DATA_AUTHORITY
    fundamental_source: str = ACTIVE_FUNDAMENTAL_SOURCE
    security_master_source: str = ACTIVE_SECURITY_MASTER_SOURCE
    market_data_source: str = ACTIVE_MARKET_DATA_SOURCE
    total_return_authority: str = ACTIVE_TOTAL_RETURN_AUTHORITY
    corporate_action_role: str = "RECONCILIATION_ONLY_NO_SECOND_PNL_PATH"
    execution_lag: str = "one_bar"
    sleeve_horizon_calendar_days: int = 30
    attempt_frequency: str = "weekly"
    rule100_equivalence_tolerance: float = 1e-12
    single_name_cap: float = 0.35
    parent_strength: float = 0.35
    child_eta: float = 0.50
    child_hazard_cap: float = 0.50
    cvar_level: float = 0.95
    insurance_materiality_floor_ratio: float | None = 0.05
    insurance_premium_ceiling_annual_return: float | None = 0.0015
    economic_cash_source: str = ACTIVE_ECONOMIC_CASH_SOURCE
    economic_cash_quote_convention: str = ACTIVE_ECONOMIC_CASH_QUOTE_CONVENTION
    economic_cash_roll_policy: str = ACTIVE_ECONOMIC_CASH_ROLL_POLICY
    economic_cash_known_at_rule: str = ACTIVE_ECONOMIC_CASH_KNOWN_AT_RULE
    inference_primary_endpoint: str = "PAIRED_CHILD_MINUS_PARENT_NET_RETURN"
    inference_hac_lag_weekly: int = 4
    inference_block_bootstrap_expected_weeks: int = 5
    f_proxy_formula: str = "robust_z(sign(total_return)*min(abs(total_return)/realized_vol,3)*dollar_volume/adv20)"
    c_proxy_formula: str = "ewma20(abs(F_proxy))"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {
            key: (format(value, ".17g") if isinstance(value, float) else value)
            for key, value in payload.items()
        }

    @property
    def contract_hash(self) -> str:
        return domain_hash("AOV0:CIQ_EXECUTABLE_CONTRACT:V1", self.to_dict())

    def canonical_bytes(self) -> bytes:
        return canonical_document_bytes(self.to_dict())


DEFAULT_CONTRACT = AOV0Contract()


def normalize_security_id(value: object) -> str:
    """Return the canonical Capital IQ security identity or fail closed.

    Active AOV authority deliberately requires an explicit CIQSEC namespace so
    legacy PERMNO integers, tickers, and company-level entity IDs cannot enter
    the current contract by accident.
    """

    text = str(value or "").strip()
    if not text.startswith(SECURITY_ID_PREFIX):
        raise ValueError("aov0_ciq_security_id_namespace_required")
    raw = text[len(SECURITY_ID_PREFIX) :].strip()
    if not raw or any(character.isspace() for character in raw):
        raise ValueError("aov0_ciq_security_id_invalid")
    return f"{SECURITY_ID_PREFIX}{raw}"


OWNER_INSURANCE_DECISION_FIELDS = (
    "insurance_materiality_floor_ratio",
    "insurance_premium_ceiling_annual_return",
)


def validate_contract(contract: AOV0Contract) -> None:
    if contract.schema_version != CONTRACT_SCHEMA:
        raise ValueError("aov0_contract_schema_invalid")
    if contract.permanent_id_type != ACTIVE_PERMANENT_ID_TYPE:
        raise ValueError("aov0_permanent_id_contract_invalid")
    if contract.identity_column != ACTIVE_IDENTITY_COLUMN or contract.security_id_namespace != "CIQSEC":
        raise ValueError("aov0_identity_column_contract_invalid")
    if contract.equity_data_authority != ACTIVE_EQUITY_DATA_AUTHORITY:
        raise ValueError("aov0_equity_data_authority_invalid")
    if contract.fundamental_source != ACTIVE_FUNDAMENTAL_SOURCE:
        raise ValueError("aov0_fundamental_source_invalid")
    if contract.security_master_source != ACTIVE_SECURITY_MASTER_SOURCE:
        raise ValueError("aov0_security_master_source_invalid")
    if contract.market_data_source != ACTIVE_MARKET_DATA_SOURCE:
        raise ValueError("aov0_market_data_source_invalid")
    if contract.total_return_authority != ACTIVE_TOTAL_RETURN_AUTHORITY:
        raise ValueError("aov0_total_return_authority_invalid")
    if contract.economic_cash_source != ACTIVE_ECONOMIC_CASH_SOURCE:
        raise ValueError("aov0_economic_cash_source_invalid")
    if contract.economic_cash_quote_convention != ACTIVE_ECONOMIC_CASH_QUOTE_CONVENTION:
        raise ValueError("aov0_economic_cash_quote_convention_invalid")
    if contract.economic_cash_roll_policy != ACTIVE_ECONOMIC_CASH_ROLL_POLICY:
        raise ValueError("aov0_economic_cash_roll_policy_invalid")
    if contract.economic_cash_known_at_rule != ACTIVE_ECONOMIC_CASH_KNOWN_AT_RULE:
        raise ValueError("aov0_economic_cash_known_at_rule_invalid")
    if not (0 < contract.single_name_cap <= 1):
        raise ValueError("aov0_single_name_cap_invalid")
    if not (0 <= contract.child_hazard_cap <= 1):
        raise ValueError("aov0_child_hazard_cap_invalid")
    if not (0.5 < contract.cvar_level < 1.0):
        raise ValueError("aov0_cvar_level_invalid")
    if contract.sleeve_horizon_calendar_days <= 0:
        raise ValueError("aov0_horizon_invalid")
    if contract.inference_hac_lag_weekly < 0:
        raise ValueError("aov0_hac_lag_invalid")
    if (
        contract.insurance_materiality_floor_ratio is not None
        and not (0.0 <= contract.insurance_materiality_floor_ratio <= 1.0)
    ):
        raise ValueError("aov0_insurance_materiality_invalid")
    if (
        contract.insurance_premium_ceiling_annual_return is not None
        and contract.insurance_premium_ceiling_annual_return < 0.0
    ):
        raise ValueError("aov0_insurance_premium_invalid")


def validate_prospective_contract(contract: AOV0Contract) -> None:
    validate_contract(contract)
    unresolved = [
        field
        for field in OWNER_INSURANCE_DECISION_FIELDS
        if getattr(contract, field) is None
    ]
    if unresolved:
        raise ValueError(
            "aov0_owner_insurance_decisions_required:" + ",".join(unresolved)
        )
