"""W5 mechanical contracts for PREBREAKOUT_DISCOVERY_v1 development walk-forward.

W2 owns the scientific contract and persistent Trial/Search Ledger. W5 binds to
that authority rather than defining a second budget, horizon, risk set, or
label identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from core.gv_fs0_canonical import assert_sha256, domain_hash
from research.prebreakout_discovery_v1 import preregistration as w2


FAMILY_ID = w2.FAMILY_ID
WALK_FORWARD_SCHEMA = "prebreakout_development_walk_forward_v1"
DEVELOPMENT_AUTHORITY_CLASS = "DEVELOPMENT_ONLY_ZERO_FINANCIAL_AUTHORITY"
LABEL_SCOPE = "DEVELOPMENT_ONLY"

_RESERVED_FEATURE_COLUMNS = {
    "decision_date",
    "security_id",
    "trading_item_id",
    "statistical_weight",
    "source_manifest_sha256",
    "pit_authority_sha256",
    "pit_risk_set_spec_id",
    "label_available_date",
    "forecast_score",
    "target_label",
}


class PrebreakoutWalkForwardError(ValueError):
    """Fail-closed W5 contract violation."""


class WalkForwardMode(str, Enum):
    EXPANDING = "EXPANDING"
    ROLLING = "ROLLING"


@dataclass(frozen=True)
class WalkForwardSpec:
    """Explicit W5 split declaration bound to the frozen W2 contract."""

    walk_forward_plan_id: str
    training_window_spec_id: str
    cross_sectional_holdout_spec_id: str
    development_objective_id: str
    family_id: str
    risk_set_spec_id: str
    primary_label_spec_id: str
    primary_horizon_sessions: int
    search_family_id: str
    trial_ledger_scope: str
    trial_budget_max: int
    mode: WalkForwardMode
    fold_count: int
    minimum_training_sessions: int
    rolling_training_sessions: int | None
    embargo_sessions: int
    oos_sessions_per_fold: int
    feature_columns: tuple[str, ...]
    holdout_seed: str
    holdout_modulus: int
    holdout_remainders: tuple[int, ...]
    label_scope: str = LABEL_SCOPE

    def __post_init__(self) -> None:
        w2.validate_contract()
        for field_name in (
            "walk_forward_plan_id",
            "training_window_spec_id",
            "cross_sectional_holdout_spec_id",
            "development_objective_id",
            "holdout_seed",
        ):
            if not str(getattr(self, field_name) or "").strip():
                raise PrebreakoutWalkForwardError(f"prebreakout_{field_name}_required")
        if self.family_id != w2.FAMILY_ID:
            raise PrebreakoutWalkForwardError("prebreakout_w5_w2_family_id_mismatch")
        if self.risk_set_spec_id != w2.RISK_SET_SPEC_ID:
            raise PrebreakoutWalkForwardError("prebreakout_w5_w2_risk_set_spec_mismatch")
        if self.primary_label_spec_id != w2.PRIMARY_LABEL_SPEC_ID:
            raise PrebreakoutWalkForwardError("prebreakout_w5_w2_primary_label_spec_mismatch")
        if self.primary_horizon_sessions != w2.PRIMARY_HORIZON_SESSIONS:
            raise PrebreakoutWalkForwardError("prebreakout_w5_w2_primary_horizon_mismatch")
        if self.search_family_id != w2.SEARCH_FAMILY_ID:
            raise PrebreakoutWalkForwardError("prebreakout_w5_w2_search_family_mismatch")
        if self.trial_ledger_scope != w2.TRIAL_LEDGER_SCOPE:
            raise PrebreakoutWalkForwardError("prebreakout_w5_w2_trial_ledger_scope_mismatch")
        if self.trial_budget_max != w2.TRIAL_BUDGET_MAX:
            raise PrebreakoutWalkForwardError("prebreakout_w5_w2_trial_budget_mismatch")
        if self.label_scope != LABEL_SCOPE:
            raise PrebreakoutWalkForwardError("prebreakout_label_scope_must_be_development_only")

        objective_upper = self.development_objective_id.upper()
        if "SHARPE" in objective_upper or "CAGR" in objective_upper:
            raise PrebreakoutWalkForwardError("prebreakout_economic_primary_search_objective_forbidden")

        mode = WalkForwardMode(self.mode)
        if isinstance(self.fold_count, bool) or not isinstance(self.fold_count, int) or self.fold_count < 1:
            raise PrebreakoutWalkForwardError("prebreakout_fold_count_positive_int_required")
        for field_name in (
            "minimum_training_sessions",
            "primary_horizon_sessions",
            "oos_sessions_per_fold",
            "holdout_modulus",
            "trial_budget_max",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise PrebreakoutWalkForwardError(f"prebreakout_{field_name}_positive_int_required")
        if isinstance(self.embargo_sessions, bool) or not isinstance(self.embargo_sessions, int):
            raise PrebreakoutWalkForwardError("prebreakout_embargo_sessions_nonnegative_int_required")
        if self.embargo_sessions < self.primary_horizon_sessions:
            raise PrebreakoutWalkForwardError("prebreakout_embargo_shorter_than_primary_horizon")

        if mode is WalkForwardMode.ROLLING:
            rolling = self.rolling_training_sessions
            if isinstance(rolling, bool) or not isinstance(rolling, int) or rolling < self.minimum_training_sessions:
                raise PrebreakoutWalkForwardError(
                    "prebreakout_rolling_training_sessions_must_cover_minimum_training_sessions"
                )
        elif self.rolling_training_sessions is not None:
            raise PrebreakoutWalkForwardError(
                "prebreakout_expanding_mode_rolling_training_sessions_must_be_none"
            )

        columns = tuple(str(value).strip() for value in self.feature_columns)
        if not columns or any(not value for value in columns):
            raise PrebreakoutWalkForwardError("prebreakout_feature_columns_required")
        if columns != self.feature_columns:
            raise PrebreakoutWalkForwardError("prebreakout_feature_columns_must_be_canonical_text")
        if len(columns) != len(set(columns)):
            raise PrebreakoutWalkForwardError("prebreakout_feature_columns_duplicate")
        reserved = sorted(set(columns) & _RESERVED_FEATURE_COLUMNS)
        if reserved:
            raise PrebreakoutWalkForwardError("prebreakout_feature_column_reserved:" + reserved[0])

        if self.holdout_modulus < 2:
            raise PrebreakoutWalkForwardError("prebreakout_holdout_modulus_must_exceed_one")
        remainders = tuple(self.holdout_remainders)
        if not remainders:
            raise PrebreakoutWalkForwardError("prebreakout_holdout_remainders_required")
        if len(remainders) != len(set(remainders)):
            raise PrebreakoutWalkForwardError("prebreakout_holdout_remainders_duplicate")
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or value >= self.holdout_modulus
            for value in remainders
        ):
            raise PrebreakoutWalkForwardError("prebreakout_holdout_remainder_invalid")
        if len(remainders) >= self.holdout_modulus:
            raise PrebreakoutWalkForwardError("prebreakout_holdout_cannot_consume_full_cross_section")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": WALK_FORWARD_SCHEMA,
            "walk_forward_plan_id": self.walk_forward_plan_id,
            "training_window_spec_id": self.training_window_spec_id,
            "cross_sectional_holdout_spec_id": self.cross_sectional_holdout_spec_id,
            "development_objective_id": self.development_objective_id,
            "family_id": self.family_id,
            "w2_contract_sha256": w2.CONTRACT_SHA256,
            "risk_set_spec_id": self.risk_set_spec_id,
            "primary_label_spec_id": self.primary_label_spec_id,
            "primary_horizon_sessions": self.primary_horizon_sessions,
            "search_family_id": self.search_family_id,
            "trial_ledger_scope": self.trial_ledger_scope,
            "trial_budget_max": self.trial_budget_max,
            "mode": WalkForwardMode(self.mode).value,
            "fold_count": self.fold_count,
            "minimum_training_sessions": self.minimum_training_sessions,
            "rolling_training_sessions": self.rolling_training_sessions,
            "embargo_sessions": self.embargo_sessions,
            "oos_sessions_per_fold": self.oos_sessions_per_fold,
            "feature_columns": list(self.feature_columns),
            "holdout_seed": self.holdout_seed,
            "holdout_modulus": self.holdout_modulus,
            "holdout_remainders": list(self.holdout_remainders),
            "label_scope": self.label_scope,
            "authority_class": DEVELOPMENT_AUTHORITY_CLASS,
            "financial_alpha_evidence": 0,
            "capital_authority": "NONE",
        }

    @property
    def spec_sha256(self) -> str:
        return domain_hash("PREBREAKOUT_DISCOVERY_V1:WALK_FORWARD_SPEC", _hash_safe(self.as_dict()))


@dataclass(frozen=True)
class DevelopmentCandidate:
    trial_id: str
    implementation_id: str
    variant_sha256: str

    def __post_init__(self) -> None:
        if not str(self.trial_id or "").strip():
            raise PrebreakoutWalkForwardError("prebreakout_trial_id_required")
        if not str(self.implementation_id or "").strip():
            raise PrebreakoutWalkForwardError("prebreakout_implementation_id_required")
        try:
            assert_sha256(self.variant_sha256)
        except ValueError as exc:
            raise PrebreakoutWalkForwardError("prebreakout_variant_sha256_invalid") from exc


@dataclass(frozen=True)
class TemporalFold:
    fold_index: int
    fold_id: str
    train_start_date: str
    train_end_date: str
    embargo_start_date: str
    embargo_end_date: str
    oos_start_date: str
    oos_end_date: str
    train_session_count: int
    embargo_session_count: int
    oos_session_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "fold_index": self.fold_index,
            "fold_id": self.fold_id,
            "train_start_date": self.train_start_date,
            "train_end_date": self.train_end_date,
            "embargo_start_date": self.embargo_start_date,
            "embargo_end_date": self.embargo_end_date,
            "oos_start_date": self.oos_start_date,
            "oos_end_date": self.oos_end_date,
            "train_session_count": self.train_session_count,
            "embargo_session_count": self.embargo_session_count,
            "oos_session_count": self.oos_session_count,
        }


def _hash_safe(value: Any) -> Any:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, Mapping):
        return {str(key): _hash_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_hash_safe(item) for item in value]
    raise PrebreakoutWalkForwardError(
        f"prebreakout_hash_value_type_unsupported:{type(value).__name__}"
    )
