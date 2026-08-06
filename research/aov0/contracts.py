"""Frozen executable contract for ALPHA-ORGANISM-VERTICAL-0.

The contract intentionally chooses one engineering configuration. V0 has no
result-driven calibration and no compatibility aliases.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash


CONTRACT_SCHEMA = "aov0_executable_contract_v1"


@dataclass(frozen=True)
class AOV0Contract:
    schema_version: str = CONTRACT_SCHEMA
    permanent_id_type: str = "permno"
    universe_rule: str = "RULE100_DATE_LOCAL_ELIGIBLE_UNIVERSE"
    total_return_authority: str = "PIT_TOTAL_RETURN_MATRIX_ONLY"
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
    insurance_materiality_floor_ratio: float = 0.05
    insurance_premium_ceiling_annual_return: float = 0.0050
    economic_cash_source: str = "OFFICIAL_SOFR"
    economic_cash_quote_convention: str = "SOFR_PERCENT_MINUS_25BP_ACT_360_SIMPLE_ACCRUAL"
    economic_cash_roll_policy: str = "OVERNIGHT_ACCRUAL_NO_PROXY_SUBSTITUTION"
    economic_cash_known_at_rule: str = "USE_ONLY_OFFICIAL_RATE_AFTER_PUBLICATION"
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
        return domain_hash("AOV0:EXECUTABLE_CONTRACT:V1", self.to_dict())

    def canonical_bytes(self) -> bytes:
        return canonical_document_bytes(self.to_dict())


DEFAULT_CONTRACT = AOV0Contract()


def validate_contract(contract: AOV0Contract) -> None:
    if contract.schema_version != CONTRACT_SCHEMA:
        raise ValueError("aov0_contract_schema_invalid")
    if contract.permanent_id_type != "permno":
        raise ValueError("aov0_permanent_id_contract_invalid")
    if contract.total_return_authority != "PIT_TOTAL_RETURN_MATRIX_ONLY":
        raise ValueError("aov0_total_return_authority_invalid")
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
