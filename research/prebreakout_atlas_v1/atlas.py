"""W4 discovery-only Atlas for PREBREAKOUT_DISCOVERY_v1.

This package is intentionally separate from W2/W5 implementation modules. W4
consumes an explicit hash-bound W2 methodology binding and verified W3 PIT
packets, then constructs a full discovery census. It does not open outcomes,
fit/retune models, compute untouched promotion metrics, or grant capital.

Winner evidence is counted by effective episode at the exact B-1 anchor so
repeated daily rows cannot manufacture extra winners. False-winner and ordinary
control populations remain full date-local decision rows. Named smoke cases are
accepted only through W3 proof objects and always receive zero statistical and
promotion-denominator weight.
"""

from __future__ import annotations

from dataclasses import dataclass
import gzip
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from core.gv_fs0_canonical import domain_hash
from research.prebreakout_pit_v1 import authority as w3


FAMILY_ID = "PREBREAKOUT_DISCOVERY_v1"
ATLAS_SCHEMA = "prebreakout_discovery_atlas_v1"
METHODOLOGY_BINDING_SCHEMA = "prebreakout_atlas_methodology_binding_v1"
MATCH_CONTRACT_SCHEMA = "prebreakout_atlas_matched_control_contract_v1"
RESEARCH_MODE = "DISCOVERY_ONLY"
MATURED_OUTCOME_STATUS = "MATURED_OPEN"
INCOMPLETE_OUTCOME_STATUS = "INCOMPLETE_HORIZON"
FIXTURE_AUTHORITY_CLASS = "MECHANICAL_FIXTURE_ZERO_EVIDENCE"
DISCOVERY_AUTHORITY_CLASS = "DISCOVERY_ONLY_ZERO_FINANCIAL_AUTHORITY"

TRUE_WINNER = "TRUE_WINNER"
FALSE_WINNER = "FALSE_WINNER"
MISSED_WINNER = "MISSED_WINNER"
MATCHED_CONTROL = "MATCHED_CONTROL"
ORDINARY_CONTROL_POOL = "ORDINARY_CONTROL_POOL"
EXCLUDED_WINNER = "EXCLUDED_WINNER"
EXCLUDED_NONWINNER = "EXCLUDED_NONWINNER"
INCOMPLETE_OUTCOME = "INCOMPLETE_OUTCOME"
WINNER_CASE_CLASSES = (TRUE_WINNER, MISSED_WINNER)

_CIQSEC_RE = re.compile(r"^CIQSEC:IQ\d+$")
_TRADING_ITEM_RE = re.compile(r"^\d+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

PREHISTORY_REQUIRED_COLUMNS = (
    "decision_session_date",
    "decision_session_ordinal",
    "decision_listing_session_ordinal",
    "security_id",
    "trading_item_id",
    "pit_authority_sha256",
    "pit_risk_set_spec_id",
    "eligibility_status",
    "exclusion_reason",
    "flagged",
)

REQUIRED_COLUMNS = (
    "decision_session_date",
    "decision_session_ordinal",
    "decision_listing_session_ordinal",
    "security_id",
    "trading_item_id",
    "pit_authority_sha256",
    "pit_risk_set_spec_id",
    "eligibility_status",
    "exclusion_reason",
    "flagged",
    "winner_label",
    "outcome_status",
    "effective_episode_id",
    "breakout_session_date",
    "breakout_session_ordinal",
    "breakout_listing_session_ordinal",
    "b_minus_1_session_date",
    "b_minus_1_session_ordinal",
    "b_minus_1_listing_session_ordinal",
)


class AtlasError(ValueError):
    """Fail-closed W4 Atlas contract violation."""


@dataclass(frozen=True)
class PrebreakoutMethodologyBinding:
    """Minimal W2 authority W4 is permitted to consume.

    Values are supplied from W2's frozen preregistration. W4 deliberately does
    not import W2 implementation modules, preventing W4 from silently acquiring
    ownership of breakout, TTFLD, horizon, or search semantics.
    """

    family_id: str
    methodology_contract_sha256: str
    breakout_contract_sha256: str
    risk_set_spec_id: str
    primary_label_spec_id: str
    breakout_spec_id: str
    ttfld_spec_id: str
    primary_horizon_sessions: int
    lead_lookback_sessions: int
    min_legitimate_lead_sessions: int
    search_family_id: str
    trial_budget_max: int

    def __post_init__(self) -> None:
        if self.family_id != FAMILY_ID:
            raise AtlasError("prebreakout_atlas_methodology_family_id_invalid")
        _sha256(self.methodology_contract_sha256, field="methodology_contract_sha256")
        _sha256(self.breakout_contract_sha256, field="breakout_contract_sha256")
        for field_name in (
            "risk_set_spec_id",
            "primary_label_spec_id",
            "breakout_spec_id",
            "ttfld_spec_id",
            "search_family_id",
        ):
            if not str(getattr(self, field_name) or "").strip():
                raise AtlasError(f"prebreakout_atlas_methodology_{field_name}_required")
        for field_name in (
            "primary_horizon_sessions",
            "lead_lookback_sessions",
            "min_legitimate_lead_sessions",
            "trial_budget_max",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise AtlasError(f"prebreakout_atlas_methodology_{field_name}_positive_int_required")
        if self.min_legitimate_lead_sessions > self.lead_lookback_sessions:
            raise AtlasError("prebreakout_atlas_methodology_min_lead_exceeds_lookback")

    @classmethod
    def from_preregistration_snapshot(
        cls,
        snapshot: Mapping[str, Any],
        *,
        methodology_contract_sha256: str,
        breakout_contract_sha256: str | None = None,
    ) -> "PrebreakoutMethodologyBinding":
        """Bind W4 to a caller-supplied frozen W2 snapshot without importing W2."""

        if not isinstance(snapshot, Mapping):
            raise AtlasError("prebreakout_atlas_methodology_snapshot_mapping_required")
        breakout = snapshot.get("breakout")
        horizons = snapshot.get("horizons")
        ttfld = snapshot.get("ttfld")
        search = snapshot.get("search")
        if not all(isinstance(value, Mapping) for value in (breakout, horizons, ttfld, search)):
            raise AtlasError("prebreakout_atlas_methodology_snapshot_sections_required")
        supplied_methodology_hash = _sha256(
            methodology_contract_sha256,
            field="methodology_contract_sha256",
        )
        expected_methodology_hash = _domain_hash(
            "PREBREAKOUT_DISCOVERY_V1:W2_CONTRACT",
            snapshot,
        )
        if supplied_methodology_hash != expected_methodology_hash:
            raise AtlasError("prebreakout_atlas_methodology_snapshot_hash_mismatch")
        supplied_breakout_hash = _sha256(
            breakout_contract_sha256 or methodology_contract_sha256,
            field="breakout_contract_sha256",
        )
        if supplied_breakout_hash != supplied_methodology_hash:
            raise AtlasError("prebreakout_atlas_breakout_contract_must_equal_w2_methodology_contract")
        return cls(
            family_id=str(snapshot.get("family_id") or ""),
            methodology_contract_sha256=supplied_methodology_hash,
            breakout_contract_sha256=supplied_breakout_hash,
            risk_set_spec_id=str(snapshot.get("risk_set_spec_id") or ""),
            primary_label_spec_id=str(snapshot.get("primary_label_spec_id") or ""),
            breakout_spec_id=str(breakout.get("spec_id") or ""),
            ttfld_spec_id=str(ttfld.get("spec_id") or ""),
            primary_horizon_sessions=_positive_int(
                horizons.get("primary_sessions"),
                field="primary_horizon_sessions",
            ),
            lead_lookback_sessions=_positive_int(
                ttfld.get("lead_lookback_sessions"),
                field="lead_lookback_sessions",
            ),
            min_legitimate_lead_sessions=_positive_int(
                ttfld.get("minimum_legitimate_lead_sessions"),
                field="min_legitimate_lead_sessions",
            ),
            search_family_id=str(search.get("search_family_id") or ""),
            trial_budget_max=_positive_int(
                search.get("trial_budget_max"),
                field="trial_budget_max",
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        body = {
            "schema_version": METHODOLOGY_BINDING_SCHEMA,
            "family_id": self.family_id,
            "methodology_contract_sha256": self.methodology_contract_sha256,
            "breakout_contract_sha256": self.breakout_contract_sha256,
            "risk_set_spec_id": self.risk_set_spec_id,
            "primary_label_spec_id": self.primary_label_spec_id,
            "breakout_spec_id": self.breakout_spec_id,
            "ttfld_spec_id": self.ttfld_spec_id,
            "primary_horizon_sessions": self.primary_horizon_sessions,
            "lead_lookback_sessions": self.lead_lookback_sessions,
            "min_legitimate_lead_sessions": self.min_legitimate_lead_sessions,
            "search_family_id": self.search_family_id,
            "trial_budget_max": self.trial_budget_max,
        }
        return {
            **body,
            "binding_sha256": _domain_hash(
                "PREBREAKOUT_ATLAS_V1:METHODOLOGY_BINDING",
                body,
            ),
        }


@dataclass(frozen=True)
class MatchedControlContract:
    """Charged/preregistered control definition consumed by W4."""

    methodology_contract_sha256: str
    control_definition_id: str
    match_columns: tuple[str, ...]
    search_charge_receipt_sha256: str | None
    trial_ledger_snapshot_sha256: str | None

    def __post_init__(self) -> None:
        _sha256(self.methodology_contract_sha256, field="control_methodology_contract_sha256")
        definition = str(self.control_definition_id or "").strip()
        if not definition:
            raise AtlasError("prebreakout_atlas_control_definition_id_required")
        columns = tuple(str(value).strip() for value in self.match_columns)
        if not columns or any(not value for value in columns):
            raise AtlasError("prebreakout_atlas_match_columns_required")
        if len(columns) != len(set(columns)):
            raise AtlasError("prebreakout_atlas_match_columns_duplicate")
        if any(not value.isidentifier() for value in columns):
            raise AtlasError("prebreakout_atlas_match_column_identifier_invalid")
        reserved = set(REQUIRED_COLUMNS) | {
            "atlas_row_id",
            "census_class",
            "statistical_weight",
            "first_legitimate_flag_session_date",
            "first_legitimate_flag_session_ordinal",
        }
        if any(value in reserved for value in columns):
            raise AtlasError("prebreakout_atlas_match_column_reserved")
        charge = self.search_charge_receipt_sha256
        ledger = self.trial_ledger_snapshot_sha256
        if (charge is None) != (ledger is None):
            raise AtlasError("prebreakout_atlas_control_charge_and_ledger_must_bind_together")
        if charge is not None:
            _sha256(charge, field="control_definition_charge_sha256")
            _sha256(ledger, field="trial_ledger_snapshot_sha256")
        object.__setattr__(self, "control_definition_id", definition)
        object.__setattr__(self, "match_columns", columns)

    def as_dict(self, *, methodology: PrebreakoutMethodologyBinding) -> dict[str, Any]:
        if self.methodology_contract_sha256 != methodology.methodology_contract_sha256:
            raise AtlasError("prebreakout_atlas_control_methodology_binding_mismatch")
        body = {
            "schema_version": MATCH_CONTRACT_SCHEMA,
            "family_id": FAMILY_ID,
            "methodology_contract_sha256": self.methodology_contract_sha256,
            "search_family_id": methodology.search_family_id,
            "charged_field": "control_definition",
            "control_definition_id": self.control_definition_id,
            "match_columns": list(self.match_columns),
            "search_charge_receipt_sha256": self.search_charge_receipt_sha256,
            "trial_ledger_snapshot_sha256": self.trial_ledger_snapshot_sha256,
        }
        return {
            **body,
            "matched_control_contract_sha256": _domain_hash(
                "PREBREAKOUT_ATLAS_V1:MATCHED_CONTROL_CONTRACT",
                body,
            ),
        }


def upstream_contract_status(methodology: PrebreakoutMethodologyBinding) -> dict[str, Any]:
    """Return W2-binding↔W3 integration status without mutating either surface."""

    aligned = methodology.risk_set_spec_id == w3.RISK_SET_SPEC_ID
    return {
        "methodology_family_id": methodology.family_id,
        "w3_family_id": w3.FAMILY_ID,
        "methodology_risk_set_spec_id": methodology.risk_set_spec_id,
        "w3_risk_set_spec_id": w3.RISK_SET_SPEC_ID,
        "risk_set_spec_aligned": aligned,
        "methodology_contract_sha256": methodology.methodology_contract_sha256,
    }


def assert_upstream_contract_alignment(methodology: PrebreakoutMethodologyBinding) -> None:
    status = upstream_contract_status(methodology)
    if status["methodology_family_id"] != status["w3_family_id"]:
        raise AtlasError("prebreakout_atlas_w2_w3_family_id_mismatch")
    if not status["risk_set_spec_aligned"]:
        raise AtlasError(
            "prebreakout_atlas_w2_w3_risk_set_spec_mismatch:"
            f"{status['methodology_risk_set_spec_id']}!={status['w3_risk_set_spec_id']}"
        )


def build_discovery_atlas(
    grid: pd.DataFrame,
    *,
    methodology: PrebreakoutMethodologyBinding,
    matched_control_contract: MatchedControlContract,
    pit_authorities_by_date: Mapping[str, w3.PrebreakoutPITAuthority | Mapping[str, Any]] | None = None,
    prehistory_flags: pd.DataFrame | None = None,
    prehistory_pit_authorities_by_date: Mapping[str, w3.PrebreakoutPITAuthority | Mapping[str, Any]] | None = None,
    smoke_proofs: Sequence[w3.BMinusOneEligibilityProof | Mapping[str, Any]] = (),
    fixture: bool = False,
) -> dict[str, Any]:
    """Build the full W4 census from already-open discovery labels.

    Real mode requires exact W2/W3 risk-set alignment, verified date-local W3
    PIT packets for every row, and a charged control definition. Fixture mode
    is mechanical scaffolding only and explicitly carries zero evidence.
    """

    assert_upstream_contract_alignment(methodology)
    if matched_control_contract.methodology_contract_sha256 != methodology.methodology_contract_sha256:
        raise AtlasError("prebreakout_atlas_control_methodology_binding_mismatch")
    if fixture:
        if pit_authorities_by_date or prehistory_pit_authorities_by_date:
            raise AtlasError("prebreakout_atlas_fixture_pit_authority_forbidden")
    else:
        if (
            matched_control_contract.search_charge_receipt_sha256 is None
            or matched_control_contract.trial_ledger_snapshot_sha256 is None
        ):
            raise AtlasError("prebreakout_atlas_real_control_definition_charge_required")
        if not pit_authorities_by_date:
            raise AtlasError("prebreakout_atlas_real_pit_authorities_required")

    frame = _normalize_grid(
        grid,
        methodology=methodology,
        matched_control_contract=matched_control_contract,
    )
    prehistory = _normalize_prehistory_flags(
        prehistory_flags,
        methodology=methodology,
    )
    if not prehistory.empty:
        first_grid_date = frame["decision_session_date"].min()
        if prehistory["decision_session_date"].max() >= first_grid_date:
            raise AtlasError("prebreakout_atlas_prehistory_must_precede_census_grid")
    smoke = _normalize_smoke_proofs(smoke_proofs, methodology=methodology)
    zero_weight_identity_keys = {
        _identity_key(row["security_id"], row["trading_item_id"])
        for row in smoke
        if row.get("security_id") and row.get("trading_item_id")
    }

    if not fixture:
        _verify_pit_bindings(
            frame,
            pit_authorities_by_date or {},
            methodology=methodology,
        )
        if not prehistory.empty:
            if not prehistory_pit_authorities_by_date:
                raise AtlasError("prebreakout_atlas_real_prehistory_pit_authorities_required")
            _verify_pit_bindings(
                prehistory,
                prehistory_pit_authorities_by_date,
                methodology=methodology,
            )

    frame["identity_key"] = [
        _identity_key(security, trading)
        for security, trading in zip(frame["security_id"], frame["trading_item_id"], strict=True)
    ]
    frame["is_smoke_trace"] = frame["identity_key"].isin(zero_weight_identity_keys)
    frame["statistical_weight"] = np.where(
        frame["eligibility_status"].eq(w3.ELIGIBLE) & ~frame["is_smoke_trace"],
        1,
        0,
    ).astype(int)
    frame["atlas_row_id"] = [
        _domain_hash(
            "PREBREAKOUT_ATLAS_V1:INPUT_ROW",
            {
                "decision_session_date": _date_text(row.decision_session_date),
                "decision_session_ordinal": int(row.decision_session_ordinal),
                "security_id": row.security_id,
                "trading_item_id": row.trading_item_id,
                "effective_episode_id": row.effective_episode_id,
            },
        )
        for row in frame.itertuples(index=False)
    ]

    match_columns = matched_control_contract.match_columns
    winner_census = _build_winner_episode_census(
        frame,
        prehistory_flags=prehistory,
        methodology=methodology,
        match_columns=match_columns,
    )
    false_winners = _build_false_winner_census(frame, match_columns=match_columns)
    ordinary_pool = _build_ordinary_control_pool(frame, match_columns=match_columns)
    ordinary_control_groups = _compress_ordinary_control_pool(
        ordinary_pool,
        match_columns=match_columns,
    )
    exclusions = _build_exclusion_census(frame, match_columns=match_columns)
    incomplete_outcomes = _build_incomplete_outcome_census(frame, match_columns=match_columns)
    matched_controls, unmatched = _build_matched_control_census(
        winner_census=winner_census,
        false_winners=false_winners,
        ordinary_pool=ordinary_pool,
        contract=matched_control_contract,
    )
    smoke_traces = _build_smoke_traces(frame, smoke)

    statistical_winners = winner_census[winner_census["statistical_weight"].eq(1)]
    statistical_false = false_winners[false_winners["statistical_weight"].eq(1)]
    body = {
        "schema_version": ATLAS_SCHEMA,
        "family_id": FAMILY_ID,
        "research_mode": RESEARCH_MODE,
        "fixture": bool(fixture),
        "authority_class": FIXTURE_AUTHORITY_CLASS if fixture else DISCOVERY_AUTHORITY_CLASS,
        "methodology_binding": methodology.as_dict(),
        "w3_risk_set_spec_id": w3.RISK_SET_SPEC_ID,
        "matched_control_contract": matched_control_contract.as_dict(methodology=methodology),
        "authority_boundary": {
            "provider_access": "FORBIDDEN",
            "label_open_performed_by_atlas": False,
            "model_fit_or_retune": "FORBIDDEN",
            "walk_forward_development": "OUT_OF_SCOPE_W5",
            "promotion_metrics": "OUT_OF_SCOPE_W6",
            "financial_alpha_evidence": 0,
            "capital_authority": "NONE",
            "parent_child_mutation": "FORBIDDEN",
            "ticker_entity_permno_identity_fallback": "FORBIDDEN",
        },
        "summary": {
            "input_date_security_row_count": int(len(frame)),
            "prehistory_flag_row_count": int(len(prehistory)),
            "winner_episode_count_all_traces": int(len(winner_census)),
            "true_winner_count_statistical": int(
                statistical_winners["census_class"].eq(TRUE_WINNER).sum()
            ),
            "missed_winner_count_statistical": int(
                statistical_winners["census_class"].eq(MISSED_WINNER).sum()
            ),
            "false_winner_decision_count_statistical": int(len(statistical_false)),
            "ordinary_control_pool_row_count_statistical": int(
                ordinary_pool["statistical_weight"].eq(1).sum()
            ),
            "deterministic_exclusion_row_count": int(len(exclusions)),
            "incomplete_outcome_row_count": int(len(incomplete_outcomes)),
            "matched_control_group_count": int(len(matched_controls)),
            "matched_control_pair_count": int(
                matched_controls["matched_control_count"].sum()
            ) if not matched_controls.empty else 0,
            "case_without_exact_matched_control_count": int(len(unmatched)),
            "smoke_trace_count": int(len(smoke_traces)),
        },
        "winner_episode_census": _records(winner_census),
        "false_winner_census": _records(false_winners),
        "ordinary_control_pool": _records(ordinary_control_groups),
        "deterministic_exclusion_census": _records(exclusions),
        "incomplete_outcome_census": _records(incomplete_outcomes),
        "matched_controls": _records(matched_controls),
        "cases_without_exact_matched_control": unmatched,
        "smoke_traces": smoke_traces,
    }
    return {
        **body,
        "atlas_sha256": _domain_hash("PREBREAKOUT_ATLAS_V1:REPORT", body),
    }


def verify_discovery_atlas(report: Mapping[str, Any]) -> None:
    if not isinstance(report, Mapping):
        raise AtlasError("prebreakout_atlas_report_mapping_required")
    if report.get("schema_version") != ATLAS_SCHEMA or report.get("family_id") != FAMILY_ID:
        raise AtlasError("prebreakout_atlas_report_identity_invalid")
    if report.get("research_mode") != RESEARCH_MODE:
        raise AtlasError("prebreakout_atlas_report_mode_invalid")
    authority = report.get("authority_boundary")
    if not isinstance(authority, Mapping):
        raise AtlasError("prebreakout_atlas_authority_boundary_required")
    if (
        authority.get("financial_alpha_evidence") != 0
        or authority.get("capital_authority") != "NONE"
        or authority.get("label_open_performed_by_atlas") is not False
    ):
        raise AtlasError("prebreakout_atlas_financial_or_label_authority_invalid")
    methodology = report.get("methodology_binding")
    if not isinstance(methodology, Mapping):
        raise AtlasError("prebreakout_atlas_methodology_binding_required")
    sealed_binding = str(methodology.get("binding_sha256") or "")
    binding_body = {key: value for key, value in methodology.items() if key != "binding_sha256"}
    if sealed_binding != _domain_hash("PREBREAKOUT_ATLAS_V1:METHODOLOGY_BINDING", binding_body):
        raise AtlasError("prebreakout_atlas_methodology_binding_hash_mismatch")
    sealed = str(report.get("atlas_sha256") or "")
    body = {key: value for key, value in report.items() if key != "atlas_sha256"}
    if sealed != _domain_hash("PREBREAKOUT_ATLAS_V1:REPORT", body):
        raise AtlasError("prebreakout_atlas_hash_mismatch")


def _normalize_prehistory_flags(
    prehistory: pd.DataFrame | None,
    *,
    methodology: PrebreakoutMethodologyBinding,
) -> pd.DataFrame:
    if prehistory is None:
        return pd.DataFrame(columns=PREHISTORY_REQUIRED_COLUMNS)
    if not isinstance(prehistory, pd.DataFrame):
        raise AtlasError("prebreakout_atlas_prehistory_frame_required")
    if prehistory.empty:
        return pd.DataFrame(columns=PREHISTORY_REQUIRED_COLUMNS)
    if set(prehistory.columns) != set(PREHISTORY_REQUIRED_COLUMNS):
        raise AtlasError("prebreakout_atlas_prehistory_columns_invalid")
    frame = prehistory.copy()
    frame["decision_session_date"] = pd.to_datetime(
        frame["decision_session_date"], errors="coerce"
    ).dt.normalize()
    if frame["decision_session_date"].isna().any():
        raise AtlasError("prebreakout_atlas_prehistory_decision_date_required")
    for column in ("decision_session_ordinal", "decision_listing_session_ordinal"):
        numeric = pd.to_numeric(frame[column], errors="coerce")
        if numeric.isna().any() or ((numeric < 0) | (numeric % 1 != 0)).any():
            raise AtlasError(f"prebreakout_atlas_prehistory_{column}_nonnegative_integer_required")
        frame[column] = numeric.astype("Int64")
    frame["security_id"] = frame["security_id"].astype(str).str.strip()
    frame["trading_item_id"] = frame["trading_item_id"].astype(str).str.strip()
    if (~frame["security_id"].map(lambda value: bool(_CIQSEC_RE.fullmatch(value)))).any():
        raise AtlasError("prebreakout_atlas_prehistory_canonical_ciqsec_required")
    if (~frame["trading_item_id"].map(lambda value: bool(_TRADING_ITEM_RE.fullmatch(value)))).any():
        raise AtlasError("prebreakout_atlas_prehistory_canonical_trading_item_required")
    if frame.duplicated(["decision_session_date", "security_id", "trading_item_id"]).any():
        raise AtlasError("prebreakout_atlas_prehistory_duplicate_date_identity")
    frame["pit_authority_sha256"] = frame["pit_authority_sha256"].astype(str).str.lower().str.strip()
    if (~frame["pit_authority_sha256"].map(lambda value: bool(_SHA256_RE.fullmatch(value)))).any():
        raise AtlasError("prebreakout_atlas_prehistory_pit_authority_sha256_invalid")
    frame["pit_risk_set_spec_id"] = frame["pit_risk_set_spec_id"].astype(str).str.strip()
    if frame["pit_risk_set_spec_id"].ne(methodology.risk_set_spec_id).any():
        raise AtlasError("prebreakout_atlas_prehistory_risk_set_spec_invalid")
    frame["eligibility_status"] = frame["eligibility_status"].astype(str).str.strip()
    if (~frame["eligibility_status"].isin({w3.ELIGIBLE, "EXCLUDED"})).any():
        raise AtlasError("prebreakout_atlas_prehistory_eligibility_status_invalid")
    frame["exclusion_reason"] = frame["exclusion_reason"].fillna("").astype(str).str.strip()
    if frame.loc[frame["eligibility_status"].eq(w3.ELIGIBLE), "exclusion_reason"].ne("").any():
        raise AtlasError("prebreakout_atlas_prehistory_eligible_exclusion_reason_forbidden")
    if frame.loc[frame["eligibility_status"].eq("EXCLUDED"), "exclusion_reason"].eq("").any():
        raise AtlasError("prebreakout_atlas_prehistory_excluded_reason_required")
    invalid = ~frame["flagged"].map(lambda value: type(value) is bool or isinstance(value, np.bool_))
    if invalid.any():
        raise AtlasError("prebreakout_atlas_prehistory_flagged_boolean_required")
    frame["flagged"] = frame["flagged"].astype(bool)
    if frame.loc[frame["eligibility_status"].eq("EXCLUDED"), "flagged"].any():
        raise AtlasError("prebreakout_atlas_prehistory_excluded_row_cannot_be_flagged")
    frame["identity_key"] = [
        _identity_key(security, trading)
        for security, trading in zip(frame["security_id"], frame["trading_item_id"], strict=True)
    ]
    return frame.sort_values(
        ["decision_session_ordinal", "security_id", "trading_item_id"],
        kind="mergesort",
    ).reset_index(drop=True)


def _normalize_grid(
    grid: pd.DataFrame,
    *,
    methodology: PrebreakoutMethodologyBinding,
    matched_control_contract: MatchedControlContract,
) -> pd.DataFrame:
    if not isinstance(grid, pd.DataFrame) or grid.empty:
        raise AtlasError("prebreakout_atlas_grid_required")
    required = (*REQUIRED_COLUMNS, *matched_control_contract.match_columns)
    missing = [column for column in required if column not in grid.columns]
    if missing:
        raise AtlasError("prebreakout_atlas_grid_column_missing:" + missing[0])
    frame = grid.copy()

    for column in (
        "decision_session_date",
        "breakout_session_date",
        "b_minus_1_session_date",
    ):
        frame[column] = pd.to_datetime(frame[column], errors="coerce").dt.normalize()
    if frame["decision_session_date"].isna().any():
        raise AtlasError("prebreakout_atlas_decision_session_date_required")

    for column in (
        "decision_session_ordinal",
        "decision_listing_session_ordinal",
        "breakout_session_ordinal",
        "breakout_listing_session_ordinal",
        "b_minus_1_session_ordinal",
        "b_minus_1_listing_session_ordinal",
    ):
        numeric = pd.to_numeric(frame[column], errors="coerce")
        present = numeric.notna()
        if ((numeric[present] < 0) | (numeric[present] % 1 != 0)).any():
            raise AtlasError(f"prebreakout_atlas_{column}_nonnegative_integer_required")
        frame[column] = numeric.astype("Int64")
    if frame["decision_session_ordinal"].isna().any():
        raise AtlasError("prebreakout_atlas_decision_session_ordinal_required")

    frame["security_id"] = frame["security_id"].astype(str).str.strip()
    frame["trading_item_id"] = frame["trading_item_id"].astype(str).str.strip()
    if (~frame["security_id"].map(lambda value: bool(_CIQSEC_RE.fullmatch(value)))).any():
        raise AtlasError("prebreakout_atlas_canonical_ciqsec_required")
    if (~frame["trading_item_id"].map(lambda value: bool(_TRADING_ITEM_RE.fullmatch(value)))).any():
        raise AtlasError("prebreakout_atlas_canonical_trading_item_required")
    if frame.duplicated(["decision_session_date", "security_id", "trading_item_id"]).any():
        raise AtlasError("prebreakout_atlas_duplicate_date_identity")

    frame["pit_authority_sha256"] = frame["pit_authority_sha256"].astype(str).str.lower().str.strip()
    if (~frame["pit_authority_sha256"].map(lambda value: bool(_SHA256_RE.fullmatch(value)))).any():
        raise AtlasError("prebreakout_atlas_pit_authority_sha256_invalid")
    frame["pit_risk_set_spec_id"] = frame["pit_risk_set_spec_id"].astype(str).str.strip()
    if frame["pit_risk_set_spec_id"].ne(methodology.risk_set_spec_id).any():
        raise AtlasError("prebreakout_atlas_grid_risk_set_spec_invalid")

    frame["eligibility_status"] = frame["eligibility_status"].astype(str).str.strip()
    if (~frame["eligibility_status"].isin({w3.ELIGIBLE, "EXCLUDED"})).any():
        raise AtlasError("prebreakout_atlas_eligibility_status_invalid")
    frame["exclusion_reason"] = frame["exclusion_reason"].fillna("").astype(str).str.strip()
    if frame.loc[frame["eligibility_status"].eq(w3.ELIGIBLE), "exclusion_reason"].ne("").any():
        raise AtlasError("prebreakout_atlas_eligible_exclusion_reason_forbidden")
    if frame.loc[frame["eligibility_status"].eq("EXCLUDED"), "exclusion_reason"].eq("").any():
        raise AtlasError("prebreakout_atlas_excluded_reason_required")

    invalid_flagged = ~frame["flagged"].map(
        lambda value: type(value) is bool or isinstance(value, np.bool_)
    )
    if invalid_flagged.any():
        raise AtlasError("prebreakout_atlas_flagged_boolean_required")
    frame["flagged"] = frame["flagged"].astype(bool)
    if frame.loc[frame["eligibility_status"].eq("EXCLUDED"), "flagged"].any():
        raise AtlasError("prebreakout_atlas_excluded_row_cannot_be_flagged")

    frame["outcome_status"] = frame["outcome_status"].astype(str).str.strip()
    if not frame["outcome_status"].isin({MATURED_OUTCOME_STATUS, INCOMPLETE_OUTCOME_STATUS}).all():
        raise AtlasError("prebreakout_atlas_outcome_status_invalid")
    matured = frame["outcome_status"].eq(MATURED_OUTCOME_STATUS)
    incomplete = frame["outcome_status"].eq(INCOMPLETE_OUTCOME_STATUS)
    winner_values: list[bool | None] = []
    for status_is_matured, status_is_incomplete, value in zip(
        matured,
        incomplete,
        frame["winner_label"],
        strict=True,
    ):
        is_boolean = type(value) is bool or isinstance(value, np.bool_)
        is_missing = value is None or bool(pd.isna(value))
        if status_is_matured:
            if not is_boolean:
                raise AtlasError("prebreakout_atlas_matured_winner_label_boolean_required")
            winner_values.append(bool(value))
        elif status_is_incomplete:
            if not is_missing:
                raise AtlasError("prebreakout_atlas_incomplete_winner_label_must_be_null")
            winner_values.append(None)
        else:  # pragma: no cover - status domain closed above.
            raise AtlasError("prebreakout_atlas_outcome_status_invalid")
    frame["winner_label"] = pd.Series(winner_values, dtype="boolean")
    frame["effective_episode_id"] = frame["effective_episode_id"].astype(str).str.strip()
    if frame["effective_episode_id"].eq("").any():
        raise AtlasError("prebreakout_atlas_effective_episode_id_required")

    winners = frame["outcome_status"].eq(MATURED_OUTCOME_STATUS) & frame["winner_label"].eq(True)
    breakout_columns = (
        "breakout_session_date",
        "breakout_session_ordinal",
        "breakout_listing_session_ordinal",
        "b_minus_1_session_date",
        "b_minus_1_session_ordinal",
        "b_minus_1_listing_session_ordinal",
    )
    for column in breakout_columns:
        if frame.loc[winners, column].isna().any():
            raise AtlasError(f"prebreakout_atlas_winner_{column}_required")
    if frame.loc[~winners, list(breakout_columns)].notna().any().any():
        raise AtlasError("prebreakout_atlas_nonwinner_or_incomplete_breakout_fields_forbidden")
    if (
        frame.loc[winners, "b_minus_1_session_ordinal"].astype(int)
        >= frame.loc[winners, "breakout_session_ordinal"].astype(int)
    ).any():
        raise AtlasError("prebreakout_atlas_b_minus_1_must_precede_breakout")
    if (
        frame.loc[winners, "b_minus_1_session_date"].to_numpy(dtype="datetime64[ns]")
        >= frame.loc[winners, "breakout_session_date"].to_numpy(dtype="datetime64[ns]")
    ).any():
        raise AtlasError("prebreakout_atlas_b_minus_1_date_must_precede_breakout")

    for column in matched_control_contract.match_columns:
        if frame[column].isna().any():
            raise AtlasError("prebreakout_atlas_match_value_missing:" + column)

    return frame.sort_values(
        ["decision_session_ordinal", "security_id", "trading_item_id"],
        kind="mergesort",
    ).reset_index(drop=True)


def _verify_pit_bindings(
    frame: pd.DataFrame,
    authorities_by_date: Mapping[str, w3.PrebreakoutPITAuthority | Mapping[str, Any]],
    *,
    methodology: PrebreakoutMethodologyBinding,
) -> None:
    required_dates = sorted({_date_text(value) for value in frame["decision_session_date"]})
    supplied_dates = {_date_text(pd.Timestamp(raw_date)) for raw_date in authorities_by_date}
    if set(required_dates) != supplied_dates:
        raise AtlasError("prebreakout_atlas_pit_authority_date_coverage_not_exact")

    by_date = {
        _date_text(pd.Timestamp(raw_date)): packet
        for raw_date, packet in authorities_by_date.items()
    }
    date_keys = frame["decision_session_date"].map(_date_text)
    for date_text, group in frame.groupby(date_keys, sort=True):
        packet = _load_pit_authority_packet(
            by_date[str(date_text)],
            expected_date=str(date_text),
            methodology=methodology,
        )
        if group["pit_authority_sha256"].nunique() != 1:
            raise AtlasError("prebreakout_atlas_date_has_multiple_pit_authority_hashes")
        if group["pit_authority_sha256"].iloc[0] != str(packet.get("packet_sha256")):
            raise AtlasError("prebreakout_atlas_pit_authority_hash_binding_mismatch")
        authority_rows: dict[str, Mapping[str, Any]] = {}
        for raw in (*packet.get("eligible_rows", []), *packet.get("exclusion_rows", [])):
            key = _identity_key(str(raw["security_id"]), str(raw["trading_item_id"]))
            if key in authority_rows:
                raise AtlasError("prebreakout_atlas_pit_authority_duplicate_identity")
            authority_rows[key] = raw
        grid_rows: dict[str, Any] = {}
        for row in group.itertuples(index=False):
            key = _identity_key(row.security_id, row.trading_item_id)
            grid_rows[key] = row
            authority_row = authority_rows.get(key)
            if authority_row is None:
                raise AtlasError("prebreakout_atlas_grid_identity_absent_from_pit_authority")
            status = str(authority_row.get("eligibility_status"))
            reason = str(authority_row.get("exclusion_reason") or "")
            if row.eligibility_status != status or row.exclusion_reason != reason:
                raise AtlasError("prebreakout_atlas_grid_pit_status_drift")
        if set(grid_rows) != set(authority_rows):
            raise AtlasError("prebreakout_atlas_grid_not_full_date_local_pit_census")


def _load_pit_authority_packet(
    packet_or_entry: w3.PrebreakoutPITAuthority | Mapping[str, Any],
    *,
    expected_date: str,
    methodology: PrebreakoutMethodologyBinding,
) -> dict[str, Any]:
    if isinstance(packet_or_entry, w3.PrebreakoutPITAuthority):
        w3.verify_prebreakout_pit_authority(packet_or_entry)
        data = packet_or_entry.as_dict()
    elif isinstance(packet_or_entry, Mapping) and packet_or_entry.get("schema_version") == w3.PIT_AUTHORITY_SCHEMA:
        w3.verify_prebreakout_pit_authority(packet_or_entry)
        data = dict(packet_or_entry)
    elif isinstance(packet_or_entry, Mapping):
        entry = dict(packet_or_entry)
        path_text = str(entry.get("authority_path") or "").strip()
        file_hash = str(entry.get("authority_file_sha256") or "").lower().strip()
        packet_hash = str(entry.get("authority_packet_sha256") or "").lower().strip()
        entry_date = str(entry.get("decision_session_date") or "").strip()
        if not path_text or not _SHA256_RE.fullmatch(file_hash) or not _SHA256_RE.fullmatch(packet_hash):
            raise AtlasError("prebreakout_atlas_pit_authority_manifest_entry_invalid")
        if entry_date != expected_date:
            raise AtlasError("prebreakout_atlas_pit_authority_date_key_mismatch")
        path = Path(path_text)
        if not path.is_file():
            raise AtlasError("prebreakout_atlas_pit_authority_file_missing")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != file_hash:
            raise AtlasError("prebreakout_atlas_pit_authority_file_hash_mismatch")
        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise AtlasError("prebreakout_atlas_pit_authority_file_invalid") from exc
        if str(data.get("packet_sha256") or "") != packet_hash:
            raise AtlasError("prebreakout_atlas_pit_authority_manifest_packet_hash_mismatch")
        w3.verify_prebreakout_pit_authority(data)
    else:
        raise AtlasError("prebreakout_atlas_pit_authority_packet_or_manifest_entry_required")
    if str(data.get("decision_session_date")) != expected_date:
        raise AtlasError("prebreakout_atlas_pit_authority_date_key_mismatch")
    if str(data.get("risk_set_spec_id")) != methodology.risk_set_spec_id:
        raise AtlasError("prebreakout_atlas_pit_authority_not_bound_to_methodology_risk_set")
    return data


def _build_winner_episode_census(
    frame: pd.DataFrame,
    *,
    prehistory_flags: pd.DataFrame,
    methodology: PrebreakoutMethodologyBinding,
    match_columns: Sequence[str],
) -> pd.DataFrame:
    winners = frame[
        frame["outcome_status"].eq(MATURED_OUTCOME_STATUS)
        & frame["winner_label"].eq(True)
    ].copy()
    if winners.empty:
        return pd.DataFrame(columns=_winner_columns(match_columns))

    rows: list[dict[str, Any]] = []
    grouped = winners.groupby(
        ["effective_episode_id", "security_id", "trading_item_id"],
        sort=True,
        dropna=False,
    )
    for (episode_id, security_id, trading_item_id), group in grouped:
        breakout_dates = group["breakout_session_date"].drop_duplicates()
        breakout_ordinals = group["breakout_session_ordinal"].drop_duplicates()
        breakout_listing_ordinals = group["breakout_listing_session_ordinal"].drop_duplicates()
        b1_dates = group["b_minus_1_session_date"].drop_duplicates()
        b1_ordinals = group["b_minus_1_session_ordinal"].drop_duplicates()
        b1_listing_ordinals = group["b_minus_1_listing_session_ordinal"].drop_duplicates()
        if any(
            len(values) != 1
            for values in (
                breakout_dates,
                breakout_ordinals,
                breakout_listing_ordinals,
                b1_dates,
                b1_ordinals,
                b1_listing_ordinals,
            )
        ):
            raise AtlasError("prebreakout_atlas_winner_episode_breakout_binding_inconsistent")
        breakout_date = pd.Timestamp(breakout_dates.iloc[0])
        breakout_ordinal = int(breakout_ordinals.iloc[0])
        breakout_listing_ordinal = int(breakout_listing_ordinals.iloc[0])
        b1_date = pd.Timestamp(b1_dates.iloc[0])
        b1_ordinal = int(b1_ordinals.iloc[0])
        b1_listing_ordinal = int(b1_listing_ordinals.iloc[0])
        expected_latest_listing = breakout_listing_ordinal - methodology.min_legitimate_lead_sessions
        if b1_listing_ordinal != expected_latest_listing:
            raise AtlasError("prebreakout_atlas_bminus1_listing_ordinal_not_methodology_min_lead")
        anchor = group[
            group["decision_session_ordinal"].astype(int).eq(b1_ordinal)
            & group["decision_listing_session_ordinal"].astype(int).eq(b1_listing_ordinal)
            & group["decision_session_date"].eq(b1_date)
        ]
        if len(anchor) != 1:
            raise AtlasError("prebreakout_atlas_winner_episode_exact_bminus1_row_required")
        anchor_row = anchor.iloc[0]
        lower_listing_ordinal = breakout_listing_ordinal - methodology.lead_lookback_sessions
        prehistory_identity = prehistory_flags[
            prehistory_flags["security_id"].eq(str(security_id))
            & prehistory_flags["trading_item_id"].eq(str(trading_item_id))
        ]
        history_columns = [
            "decision_session_date",
            "decision_session_ordinal",
            "decision_listing_session_ordinal",
            "eligibility_status",
            "flagged",
        ]
        lead_history = (
            group[history_columns].copy()
            if prehistory_identity.empty
            else pd.concat(
                [prehistory_identity[history_columns], group[history_columns]],
                ignore_index=True,
            )
        )
        eligible_window = lead_history[
            lead_history["eligibility_status"].eq(w3.ELIGIBLE)
            & lead_history["decision_listing_session_ordinal"].astype(int).between(
                lower_listing_ordinal,
                expected_latest_listing,
            )
        ]
        flagged = eligible_window[eligible_window["flagged"]].sort_values(
            ["decision_listing_session_ordinal", "decision_session_ordinal", "decision_session_date"],
            kind="mergesort",
        )
        first_flag = None if flagged.empty else flagged.iloc[0]

        if anchor_row["eligibility_status"] != w3.ELIGIBLE:
            census_class = EXCLUDED_WINNER
            statistical_weight = 0
            miss_reason = "DETERMINISTIC_B_MINUS_1_PIT_EXCLUSION"
        elif first_flag is None:
            census_class = MISSED_WINNER
            statistical_weight = int(anchor_row["statistical_weight"])
            miss_reason = "NO_LEGITIMATE_FLAG_AT_OR_BEFORE_B_MINUS_1"
        else:
            census_class = TRUE_WINNER
            statistical_weight = int(anchor_row["statistical_weight"])
            miss_reason = None

        output = {
            "census_class": census_class,
            "effective_episode_id": str(episode_id),
            "security_id": str(security_id),
            "trading_item_id": str(trading_item_id),
            "identity_key": _identity_key(str(security_id), str(trading_item_id)),
            "breakout_session_date": _date_text(breakout_date),
            "breakout_session_ordinal": breakout_ordinal,
            "breakout_listing_session_ordinal": breakout_listing_ordinal,
            "b_minus_1_session_date": _date_text(b1_date),
            "b_minus_1_session_ordinal": b1_ordinal,
            "b_minus_1_listing_session_ordinal": b1_listing_ordinal,
            "b_minus_1_pit_authority_sha256": str(anchor_row["pit_authority_sha256"]),
            "b_minus_1_eligibility_status": str(anchor_row["eligibility_status"]),
            "b_minus_1_exclusion_reason": str(anchor_row["exclusion_reason"]) or None,
            "first_legitimate_flag_session_date": (
                None if first_flag is None else _date_text(first_flag["decision_session_date"])
            ),
            "first_legitimate_flag_session_ordinal": (
                None if first_flag is None else int(first_flag["decision_session_ordinal"])
            ),
            "first_legitimate_flag_listing_session_ordinal": (
                None
                if first_flag is None
                else int(first_flag["decision_listing_session_ordinal"])
            ),
            "prebreakout_flag_present": first_flag is not None,
            "miss_or_exclusion_reason": miss_reason,
            "statistical_weight": statistical_weight,
            "is_smoke_trace": bool(anchor_row["is_smoke_trace"]),
            "matched_control_count": 0,
        }
        for column in match_columns:
            output[column] = _jsonable(anchor_row[column])
        rows.append(output)

    return pd.DataFrame(rows).sort_values(
        ["b_minus_1_session_ordinal", "security_id", "effective_episode_id"],
        kind="mergesort",
    ).reset_index(drop=True)


def _build_false_winner_census(
    frame: pd.DataFrame,
    *,
    match_columns: Sequence[str],
) -> pd.DataFrame:
    rows = frame[
        frame["outcome_status"].eq(MATURED_OUTCOME_STATUS)
        & frame["winner_label"].eq(False)
        & frame["eligibility_status"].eq(w3.ELIGIBLE)
        & frame["flagged"]
    ].copy()
    if rows.empty:
        return pd.DataFrame(columns=_false_winner_columns(match_columns))
    rows["census_class"] = FALSE_WINNER
    rows["matched_control_count"] = 0
    keep = [
        "census_class",
        "atlas_row_id",
        "effective_episode_id",
        "decision_session_date",
        "decision_session_ordinal",
        "security_id",
        "trading_item_id",
        "identity_key",
        "pit_authority_sha256",
        "statistical_weight",
        "is_smoke_trace",
        "matched_control_count",
        *match_columns,
    ]
    return rows[keep].sort_values(
        ["decision_session_ordinal", "security_id"], kind="mergesort"
    ).reset_index(drop=True)


def _build_ordinary_control_pool(
    frame: pd.DataFrame,
    *,
    match_columns: Sequence[str],
) -> pd.DataFrame:
    rows = frame[
        frame["outcome_status"].eq(MATURED_OUTCOME_STATUS)
        & frame["winner_label"].eq(False)
        & frame["eligibility_status"].eq(w3.ELIGIBLE)
        & ~frame["flagged"]
    ].copy()
    if rows.empty:
        return pd.DataFrame(columns=_ordinary_control_columns(match_columns))
    rows["census_class"] = ORDINARY_CONTROL_POOL
    keep = [
        "census_class",
        "atlas_row_id",
        "effective_episode_id",
        "decision_session_date",
        "decision_session_ordinal",
        "security_id",
        "trading_item_id",
        "identity_key",
        "pit_authority_sha256",
        "statistical_weight",
        "is_smoke_trace",
        *match_columns,
    ]
    return rows[keep].sort_values(
        ["decision_session_ordinal", "security_id"], kind="mergesort"
    ).reset_index(drop=True)


def _compress_ordinary_control_pool(
    ordinary_pool: pd.DataFrame,
    *,
    match_columns: Sequence[str],
) -> pd.DataFrame:
    columns = [
        "census_class",
        "decision_session_date",
        "decision_session_ordinal",
        "match_group_id",
        "ordinary_control_count",
        "ordinary_control_identity_set_sha256",
        "statistical_weight",
        *match_columns,
    ]
    if ordinary_pool.empty:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, Any]] = []
    group_columns = ["decision_session_date", "decision_session_ordinal", *match_columns]
    for keys, group in ordinary_pool.groupby(group_columns, sort=True, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        decision_date = _date_text(keys[0])
        decision_ordinal = int(keys[1])
        match_values = {
            column: _jsonable(keys[index + 2])
            for index, column in enumerate(match_columns)
        }
        identities = [
            {
                "atlas_row_id": str(item["atlas_row_id"]),
                "security_id": str(item["security_id"]),
                "trading_item_id": str(item["trading_item_id"]),
            }
            for item in group.sort_values(
                ["security_id", "trading_item_id"],
                kind="mergesort",
            ).to_dict(orient="records")
        ]
        match_group_id = _domain_hash(
            "PREBREAKOUT_ATLAS_V1:ORDINARY_CONTROL_GROUP",
            {
                "decision_session_ordinal": decision_ordinal,
                "match_values": match_values,
            },
        )
        rows.append(
            {
                "census_class": ORDINARY_CONTROL_POOL,
                "decision_session_date": decision_date,
                "decision_session_ordinal": decision_ordinal,
                "match_group_id": match_group_id,
                "ordinary_control_count": len(identities),
                "ordinary_control_identity_set_sha256": _domain_hash(
                    "PREBREAKOUT_ATLAS_V1:ORDINARY_CONTROL_IDENTITY_SET",
                    {
                        "match_group_id": match_group_id,
                        "controls": identities,
                    },
                ),
                "statistical_weight": 1,
                **match_values,
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["decision_session_ordinal", *match_columns],
        kind="mergesort",
    ).reset_index(drop=True)


def _build_exclusion_census(
    frame: pd.DataFrame,
    *,
    match_columns: Sequence[str],
) -> pd.DataFrame:
    rows = frame[
        frame["outcome_status"].eq(MATURED_OUTCOME_STATUS)
        & frame["eligibility_status"].eq("EXCLUDED")
    ].copy()
    if rows.empty:
        return pd.DataFrame(columns=_exclusion_columns(match_columns))
    rows["census_class"] = np.where(rows["winner_label"], EXCLUDED_WINNER, EXCLUDED_NONWINNER)
    keep = [
        "census_class",
        "atlas_row_id",
        "effective_episode_id",
        "decision_session_date",
        "decision_session_ordinal",
        "security_id",
        "trading_item_id",
        "identity_key",
        "pit_authority_sha256",
        "exclusion_reason",
        "winner_label",
        "statistical_weight",
        "is_smoke_trace",
        *match_columns,
    ]
    return rows[keep].sort_values(
        ["decision_session_ordinal", "security_id"], kind="mergesort"
    ).reset_index(drop=True)


def _build_incomplete_outcome_census(
    frame: pd.DataFrame,
    *,
    match_columns: Sequence[str],
) -> pd.DataFrame:
    rows = frame[frame["outcome_status"].eq(INCOMPLETE_OUTCOME_STATUS)].copy()
    if rows.empty:
        return pd.DataFrame(columns=_incomplete_outcome_columns(match_columns))
    rows["census_class"] = INCOMPLETE_OUTCOME
    keep = _incomplete_outcome_columns(match_columns)
    return rows[keep].sort_values(
        ["decision_session_ordinal", "security_id", "trading_item_id"],
        kind="mergesort",
    ).reset_index(drop=True)


def _build_matched_control_census(
    *,
    winner_census: pd.DataFrame,
    false_winners: pd.DataFrame,
    ordinary_pool: pd.DataFrame,
    contract: MatchedControlContract,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    cases: list[dict[str, Any]] = []
    for row in winner_census.to_dict(orient="records"):
        if int(row["statistical_weight"]) != 1 or row["census_class"] not in WINNER_CASE_CLASSES:
            continue
        cases.append(
            {
                "case_id": _domain_hash(
                    "PREBREAKOUT_ATLAS_V1:WINNER_CASE",
                    {
                        "effective_episode_id": row["effective_episode_id"],
                        "security_id": row["security_id"],
                        "b_minus_1_session_ordinal": row["b_minus_1_session_ordinal"],
                    },
                ),
                "case_class": row["census_class"],
                "security_id": row["security_id"],
                "decision_session_date": row["b_minus_1_session_date"],
                "decision_session_ordinal": int(row["b_minus_1_session_ordinal"]),
                **{column: row[column] for column in contract.match_columns},
            }
        )
    for row in false_winners.to_dict(orient="records"):
        if int(row["statistical_weight"]) != 1:
            continue
        cases.append(
            {
                "case_id": str(row["atlas_row_id"]),
                "case_class": FALSE_WINNER,
                "security_id": row["security_id"],
                "decision_session_date": _date_text(row["decision_session_date"]),
                "decision_session_ordinal": int(row["decision_session_ordinal"]),
                **{column: row[column] for column in contract.match_columns},
            }
        )

    groups: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for case in sorted(
        cases,
        key=lambda row: (row["decision_session_ordinal"], row["security_id"], row["case_id"]),
    ):
        mask = ordinary_pool["decision_session_ordinal"].astype(int).eq(
            int(case["decision_session_ordinal"])
        )
        for column in contract.match_columns:
            mask &= ordinary_pool[column].eq(case[column])
        controls = ordinary_pool.loc[mask & ordinary_pool["statistical_weight"].eq(1)].sort_values(
            ["security_id", "trading_item_id"], kind="mergesort"
        )
        if controls.empty:
            unmatched.append(
                {
                    "case_id": case["case_id"],
                    "case_class": case["case_class"],
                    "security_id": case["security_id"],
                    "decision_session_date": case["decision_session_date"],
                    "reason": "NO_EXACT_PREREGISTERED_MATCHED_CONTROL",
                }
            )
            continue
        match_values = {column: _jsonable(case[column]) for column in contract.match_columns}
        group_id = _domain_hash(
            "PREBREAKOUT_ATLAS_V1:MATCH_GROUP",
            {
                "decision_session_ordinal": int(case["decision_session_ordinal"]),
                "match_values": match_values,
            },
        )
        control_identities = [
            {
                "atlas_row_id": str(control["atlas_row_id"]),
                "security_id": str(control["security_id"]),
                "trading_item_id": str(control["trading_item_id"]),
            }
            for control in controls.to_dict(orient="records")
        ]
        groups.append(
            {
                "census_class": MATCHED_CONTROL,
                "case_id": case["case_id"],
                "case_class": case["case_class"],
                "case_security_id": case["security_id"],
                "decision_session_date": case["decision_session_date"],
                "decision_session_ordinal": int(case["decision_session_ordinal"]),
                "match_group_id": group_id,
                "matched_control_count": len(control_identities),
                "matched_control_identity_set_sha256": _domain_hash(
                    "PREBREAKOUT_ATLAS_V1:MATCHED_CONTROL_IDENTITY_SET",
                    {
                        "match_group_id": group_id,
                        "controls": control_identities,
                    },
                ),
                "statistical_weight": 1,
                **match_values,
            }
        )

    columns = [
        "census_class",
        "case_id",
        "case_class",
        "case_security_id",
        "decision_session_date",
        "decision_session_ordinal",
        "match_group_id",
        "matched_control_count",
        "matched_control_identity_set_sha256",
        "statistical_weight",
        *contract.match_columns,
    ]
    output = pd.DataFrame(groups, columns=columns)
    if not output.empty:
        output = output.sort_values(
            ["decision_session_ordinal", "case_security_id", "case_id"],
            kind="mergesort",
        ).reset_index(drop=True)

    if not winner_census.empty:
        counts = {
            (str(group["case_security_id"]), str(group["decision_session_date"])): int(
                group["matched_control_count"]
            )
            for group in groups
            if group["case_class"] in WINNER_CASE_CLASSES
        }
        for index, row in winner_census.iterrows():
            key = (str(row["security_id"]), str(row["b_minus_1_session_date"]))
            winner_census.at[index, "matched_control_count"] = int(counts.get(key, 0))
    if not false_winners.empty:
        counts_by_case = {
            str(group["case_id"]): int(group["matched_control_count"])
            for group in groups
            if group["case_class"] == FALSE_WINNER
        }
        for index, row in false_winners.iterrows():
            false_winners.at[index, "matched_control_count"] = int(
                counts_by_case.get(str(row["atlas_row_id"]), 0)
            )
    return output, unmatched


def _normalize_smoke_proofs(
    proofs: Sequence[w3.BMinusOneEligibilityProof | Mapping[str, Any]],
    *,
    methodology: PrebreakoutMethodologyBinding,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()
    for proof in proofs:
        if isinstance(proof, w3.BMinusOneEligibilityProof):
            row = proof.as_dict()
        elif isinstance(proof, Mapping):
            row = dict(proof)
        else:
            raise AtlasError("prebreakout_atlas_smoke_proof_mapping_required")
        if row.get("schema_version") != w3.SMOKE_PROOF_SCHEMA or row.get("family_id") != FAMILY_ID:
            raise AtlasError("prebreakout_atlas_smoke_proof_identity_invalid")
        if row.get("display_symbol_used_for_logic") is not False:
            raise AtlasError("prebreakout_atlas_smoke_symbol_logic_forbidden")
        if row.get("statistical_weight") != 0 or row.get("promotion_denominator_weight") != 0:
            raise AtlasError("prebreakout_atlas_smoke_weight_must_be_zero")
        if row.get("financial_alpha_evidence") != 0 or row.get("capital_authority") != "NONE":
            raise AtlasError("prebreakout_atlas_smoke_authority_invalid")
        proof_breakout_hash = row.get("breakout_contract_sha256")
        if proof_breakout_hash is not None and proof_breakout_hash != methodology.breakout_contract_sha256:
            raise AtlasError("prebreakout_atlas_smoke_breakout_contract_binding_mismatch")
        case_id = str(row.get("case_id") or "").strip()
        if not case_id or case_id in seen_case_ids:
            raise AtlasError("prebreakout_atlas_smoke_case_id_invalid_or_duplicate")
        seen_case_ids.add(case_id)
        if row.get("security_id") is not None:
            _security_id(row["security_id"])
        if row.get("trading_item_id") is not None:
            _trading_item_id(row["trading_item_id"])
        sealed = _sha256(row.get("proof_sha256"), field="smoke_proof_sha256")
        body = {key: value for key, value in row.items() if key != "proof_sha256"}
        if sealed != _w3_proof_hash(body):
            raise AtlasError("prebreakout_atlas_smoke_proof_hash_mismatch")
        output.append(row)
    return sorted(output, key=lambda row: str(row["case_id"]))


def _build_smoke_traces(frame: pd.DataFrame, proofs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    for proof in proofs:
        security_id = proof.get("security_id")
        trading_item_id = proof.get("trading_item_id")
        identity = (
            None
            if security_id is None or trading_item_id is None
            else _identity_key(str(security_id), str(trading_item_id))
        )
        rows = frame.iloc[0:0] if identity is None else frame[frame["identity_key"].eq(identity)]
        b1_text = proof.get("b_minus_1_session")
        if b1_text and not rows.empty:
            eligible_pre_b1 = rows[
                rows["decision_session_date"].le(pd.Timestamp(str(b1_text)).normalize())
                & rows["eligibility_status"].eq(w3.ELIGIBLE)
            ]
            any_early = bool(eligible_pre_b1["flagged"].any())
        else:
            any_early = False
        traces.append(
            {
                "case_id": proof["case_id"],
                "display_symbol": proof.get("display_symbol"),
                "display_symbol_used_for_logic": False,
                "security_id": security_id,
                "trading_item_id": trading_item_id,
                "b_minus_1_proof_status": proof.get("status"),
                "b_minus_1_proof_reason": proof.get("reason"),
                "b_minus_1_session": proof.get("b_minus_1_session"),
                "breakout_session": proof.get("breakout_session"),
                "proof_sha256": proof.get("proof_sha256"),
                "atlas_input_row_count": int(len(rows)),
                "any_legitimate_prebreakout_flag": any_early,
                "statistical_weight": 0,
                "promotion_denominator_weight": 0,
            }
        )
    return traces


def _winner_columns(match_columns: Sequence[str]) -> list[str]:
    return [
        "census_class",
        "effective_episode_id",
        "security_id",
        "trading_item_id",
        "identity_key",
        "breakout_session_date",
        "breakout_session_ordinal",
        "breakout_listing_session_ordinal",
        "b_minus_1_session_date",
        "b_minus_1_session_ordinal",
        "b_minus_1_listing_session_ordinal",
        "b_minus_1_pit_authority_sha256",
        "b_minus_1_eligibility_status",
        "b_minus_1_exclusion_reason",
        "first_legitimate_flag_session_date",
        "first_legitimate_flag_session_ordinal",
        "first_legitimate_flag_listing_session_ordinal",
        "prebreakout_flag_present",
        "miss_or_exclusion_reason",
        "statistical_weight",
        "is_smoke_trace",
        "matched_control_count",
        *match_columns,
    ]


def _false_winner_columns(match_columns: Sequence[str]) -> list[str]:
    return [
        "census_class",
        "atlas_row_id",
        "effective_episode_id",
        "decision_session_date",
        "decision_session_ordinal",
        "security_id",
        "trading_item_id",
        "identity_key",
        "pit_authority_sha256",
        "statistical_weight",
        "is_smoke_trace",
        "matched_control_count",
        *match_columns,
    ]


def _ordinary_control_columns(match_columns: Sequence[str]) -> list[str]:
    return [
        "census_class",
        "atlas_row_id",
        "effective_episode_id",
        "decision_session_date",
        "decision_session_ordinal",
        "security_id",
        "trading_item_id",
        "identity_key",
        "pit_authority_sha256",
        "statistical_weight",
        "is_smoke_trace",
        *match_columns,
    ]


def _exclusion_columns(match_columns: Sequence[str]) -> list[str]:
    return [
        "census_class",
        "atlas_row_id",
        "effective_episode_id",
        "decision_session_date",
        "decision_session_ordinal",
        "security_id",
        "trading_item_id",
        "identity_key",
        "pit_authority_sha256",
        "exclusion_reason",
        "winner_label",
        "statistical_weight",
        "is_smoke_trace",
        *match_columns,
    ]


def _incomplete_outcome_columns(match_columns: Sequence[str]) -> list[str]:
    return [
        "census_class",
        "atlas_row_id",
        "effective_episode_id",
        "decision_session_date",
        "decision_session_ordinal",
        "security_id",
        "trading_item_id",
        "identity_key",
        "pit_authority_sha256",
        "eligibility_status",
        "exclusion_reason",
        "statistical_weight",
        "is_smoke_trace",
        *match_columns,
    ]


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return [
        {str(key): _jsonable(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def _identity_key(security_id: str, trading_item_id: str) -> str:
    return f"{_security_id(security_id)}|{_trading_item_id(trading_item_id)}"


def _security_id(value: Any) -> str:
    text = str(value or "").strip()
    if not _CIQSEC_RE.fullmatch(text):
        raise AtlasError("prebreakout_atlas_canonical_ciqsec_required")
    return text


def _trading_item_id(value: Any) -> str:
    text = str(value or "").strip()
    if not _TRADING_ITEM_RE.fullmatch(text):
        raise AtlasError("prebreakout_atlas_canonical_trading_item_required")
    return text


def _positive_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool):
        raise AtlasError(f"prebreakout_atlas_{field}_positive_int_required")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise AtlasError(f"prebreakout_atlas_{field}_positive_int_required") from exc
    if parsed < 1 or str(parsed) != str(value).strip():
        raise AtlasError(f"prebreakout_atlas_{field}_positive_int_required")
    return parsed


def _sha256(value: Any, *, field: str) -> str:
    text = str(value or "").strip().lower()
    if not _SHA256_RE.fullmatch(text):
        raise AtlasError(f"prebreakout_atlas_{field}_invalid")
    return text


def _date_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    return pd.Timestamp(value).date().isoformat()


def _jsonable(value: Any) -> Any:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, pd.Timestamp):
        return _date_text(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, float) and np.isnan(value):
        return None
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _hash_safe(value: Any) -> Any:
    value = _jsonable(value)
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
    raise AtlasError(f"prebreakout_atlas_hash_value_type_unsupported:{type(value).__name__}")


def _domain_hash(domain: str, value: Any) -> str:
    return domain_hash(domain, _hash_safe(value))


def _w3_proof_hash(body: Mapping[str, Any]) -> str:
    raw = json.dumps(
        {"domain": "PREBREAKOUT_BMINUS1_SMOKE_PROOF_V1", "value": body},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
