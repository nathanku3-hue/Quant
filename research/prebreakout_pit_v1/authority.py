"""Fail-closed PIT source authority for PREBREAKOUT_DISCOVERY_v1.

W3 owns source/identity/availability/corporate-action truth only. It does not
own the breakout algorithm, labels, outcomes, scoring, search, or capital.

The authority is deliberately date-local. Historical capture must prove a
provider-bound historical as-of query; prospective capture must use only bytes
available by the decision cutoff. Current-survivor projection, current-primary
projection, ticker/entity/PERMNO identity fallback, and alternate-listing
substitution are all forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from research.alpha_pit_v1.contracts import validate_source_receipt_binding
from research.prebreakout_discovery_v1.preregistration import CONTRACT_SHA256 as W2_CONTRACT_SHA256


FAMILY_ID = "PREBREAKOUT_DISCOVERY_v1"
PIT_AUTHORITY_SCHEMA = "prebreakout_pit_authority_v1"
SOURCE_AUTHORITY_SCHEMA = "prebreakout_pit_source_authority_v1"
CANDIDATE_ROW_SCHEMA = "prebreakout_pit_candidate_row_v1"
CORPORATE_ACTION_ROW_SCHEMA = "prebreakout_pit_corporate_action_row_v1"
SMOKE_PROOF_SCHEMA = "prebreakout_bminus1_eligibility_proof_v1"
RISK_SET_SPEC_ID = "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1"
CORPORATE_ACTION_POLICY_ID = "PREBREAKOUT_DATE_LOCAL_CORPORATE_ACTION_V1"

HISTORICAL_CAPTURE_MODE = "HISTORICAL_PIT_DATE_LOCAL"
PROSPECTIVE_CAPTURE_MODE = "PROSPECTIVE_SAME_DAY"
_CAPTURE_MODES = frozenset({HISTORICAL_CAPTURE_MODE, PROSPECTIVE_CAPTURE_MODE})

PRIMARY_DATE_LOCAL = "PRIMARY_DATE_LOCAL"
NON_PRIMARY_DATE_LOCAL = "NON_PRIMARY_DATE_LOCAL"
AMBIGUOUS_DATE_LOCAL = "AMBIGUOUS_DATE_LOCAL"
_PRIMARY_STATES = frozenset(
    {PRIMARY_DATE_LOCAL, NON_PRIMARY_DATE_LOCAL, AMBIGUOUS_DATE_LOCAL}
)
PRIMARY_PROOF_PROVIDER = "DATE_LOCAL_PROVIDER_PRIMARY"
PRIMARY_PROOF_UNIQUE = "UNIQUE_DATE_LOCAL_QUALIFYING_LISTING"
PRIMARY_PROOF_NON_PRIMARY = "DATE_LOCAL_PROVIDER_NON_PRIMARY"
PRIMARY_PROOF_AMBIGUOUS = "DATE_LOCAL_AMBIGUOUS_MULTIPLE"
_PRIMARY_PROOFS = frozenset(
    {
        PRIMARY_PROOF_PROVIDER,
        PRIMARY_PROOF_UNIQUE,
        PRIMARY_PROOF_NON_PRIMARY,
        PRIMARY_PROOF_AMBIGUOUS,
    }
)

ACTION_CLEAR = "CLEAR"
ACTION_PENDING_TERMINAL = "PENDING_TERMINAL"
ACTION_EFFECTIVE_TERMINAL = "EFFECTIVE_TERMINAL"
ACTION_UNRESOLVED = "UNRESOLVED"
_ACTION_STATES = frozenset(
    {
        ACTION_CLEAR,
        ACTION_PENDING_TERMINAL,
        ACTION_EFFECTIVE_TERMINAL,
        ACTION_UNRESOLVED,
    }
)

ELIGIBLE = "ELIGIBLE"
EXCLUSION_NON_US = "NON_US_LISTING"
EXCLUSION_NON_COMMON = "NON_COMMON_EQUITY"
EXCLUSION_NON_PRIMARY = "NON_PRIMARY_LISTING"
EXCLUSION_AMBIGUOUS_PRIMARY = "AMBIGUOUS_PRIMARY_LISTING"
EXCLUSION_NOT_ACTIVE = "NOT_ACTIVE_TRADABLE"
EXCLUSION_CA_UNRESOLVED = "CORPORATE_ACTION_UNRESOLVED"
EXCLUSION_CA_EFFECTIVE = "CORPORATE_ACTION_TERMINAL_EFFECTIVE"
EXCLUSION_NOT_IN_SOURCE = "NOT_IN_DATE_LOCAL_SOURCE_POPULATION"
EXCLUSION_IDENTITY_UNBOUND = "IDENTITY_UNBOUND"
B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE = "B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE"

_SOURCE_AUTHORITY_FIELDS = frozenset(
    {
        "schema_version",
        "family_id",
        "risk_set_spec_id",
        "capture_mode",
        "decision_session_date",
        "provider",
        "date_local_membership_query",
        "source_population_complete",
        "historical_as_of_mechanically_bound",
        "corporate_action_coverage_complete",
        "current_survivor_back_projection_used",
        "current_primary_back_projection_used",
        "alternate_listing_backfill_used",
        "ticker_fallback_used",
        "company_entity_fallback_used",
        "permno_fallback_used",
        "primary_listing_resolution",
        "ambiguous_listing_policy",
        "source_receipt_sha256s",
    }
)

_CANDIDATE_FIELDS = frozenset(
    {
        "schema_version",
        "security_id",
        "company_id",
        "trading_item_id",
        "spt_instrument_item_id",
        "membership_as_of_date",
        "listing_country",
        "security_class",
        "primary_listing_state",
        "primary_listing_proof_kind",
        "active_tradable",
        "observed_at",
        "available_at",
        "source_id",
        "source_receipt_sha256",
        "identity_receipt_sha256",
    }
)

_CORPORATE_ACTION_FIELDS = frozenset(
    {
        "schema_version",
        "security_id",
        "trading_item_id",
        "action_state",
        "effective_session_date",
        "event_type",
        "observed_at",
        "available_at",
        "source_id",
        "source_receipt_sha256",
    }
)

_CIQ_SECURITY_RE = re.compile(r"^CIQSEC:IQ\d+$")
_TRADING_ITEM_RE = re.compile(r"^\d+$")
_SPT_RE = re.compile(r"^SPT\d+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class PrebreakoutPITAuthorityError(ValueError):
    """Fail-closed W3 PIT authority violation."""


@dataclass(frozen=True)
class PrebreakoutPITAuthority:
    """One immutable date-local W3 authority packet."""

    body: Mapping[str, Any]
    packet_sha256: str

    @property
    def decision_session_date(self) -> str:
        return str(self.body["decision_session_date"])

    @property
    def eligible_rows(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(self.body["eligible_rows"])

    @property
    def exclusion_rows(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(self.body["exclusion_rows"])

    def as_dict(self) -> dict[str, Any]:
        return {**dict(self.body), "packet_sha256": self.packet_sha256}


@dataclass(frozen=True)
class BMinusOneEligibilityProof:
    """Zero-statistical-weight trace for one named or generic smoke case."""

    body: Mapping[str, Any]
    proof_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {**dict(self.body), "proof_sha256": self.proof_sha256}


def build_prebreakout_pit_authority(
    *,
    as_of: datetime,
    decision_session_date: date | str,
    source_authority: Mapping[str, Any],
    candidate_rows: Sequence[Mapping[str, Any]],
    corporate_action_rows: Sequence[Mapping[str, Any]],
    source_receipts: Sequence[Mapping[str, Any]],
    fixture: bool = False,
) -> PrebreakoutPITAuthority:
    """Compile one date-local PIT risk set from source-bound candidate facts.

    Every candidate must have an exact CIQ Security ID + Trading Item identity
    and exactly one corporate-action state row. Exclusions are deterministic;
    no excluded/ambiguous/current-survivor row can be repaired by fallback.
    """

    cutoff = _utc_datetime(as_of, field="as_of")
    decision_day = _date_value(decision_session_date, field="decision_session_date")
    receipts = _validate_source_receipts(source_receipts)
    receipt_hashes = {str(row["raw_receipt_sha256"]) for row in receipts}
    authority = _validate_source_authority(
        source_authority,
        decision_day=decision_day,
        receipt_hashes=receipt_hashes,
        fixture=fixture,
    )
    _validate_source_receipt_timing(
        receipts,
        capture_mode=str(authority["capture_mode"]),
        decision_day=decision_day,
        cutoff=cutoff,
    )
    candidates = _validate_candidate_rows(
        candidate_rows,
        decision_day=decision_day,
        cutoff=cutoff,
        receipt_hashes=receipt_hashes,
    )
    actions = _validate_corporate_action_rows(
        corporate_action_rows,
        candidates=candidates,
        decision_day=decision_day,
        cutoff=cutoff,
        receipt_hashes=receipt_hashes,
    )

    action_by_key = {
        (str(row["security_id"]), str(row["trading_item_id"])): row
        for row in actions
    }
    eligible_rows: list[dict[str, Any]] = []
    exclusion_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        key = (str(candidate["security_id"]), str(candidate["trading_item_id"]))
        action = action_by_key[key]
        reason = _eligibility_reason(candidate, action)
        compiled = {
            **candidate,
            "corporate_action_state": action["action_state"],
            "corporate_action_effective_session_date": action["effective_session_date"],
            "corporate_action_event_type": action["event_type"],
            "corporate_action_source_receipt_sha256": action["source_receipt_sha256"],
            "eligibility_status": ELIGIBLE if reason is None else "EXCLUDED",
            "exclusion_reason": reason,
        }
        if reason is None:
            eligible_rows.append(compiled)
        else:
            exclusion_rows.append(compiled)

    _require_unique_eligible_authority(eligible_rows)
    body = _canonical(
        {
            "schema_version": PIT_AUTHORITY_SCHEMA,
            "family_id": FAMILY_ID,
            "risk_set_spec_id": RISK_SET_SPEC_ID,
            "corporate_action_policy_id": CORPORATE_ACTION_POLICY_ID,
            "decision_session_date": decision_day.isoformat(),
            "as_of": _timestamp_text(cutoff),
            "source_authority": authority,
            "source_receipt_sha256s": sorted(receipt_hashes),
            "candidate_count": len(candidates),
            "eligible_count": len(eligible_rows),
            "exclusion_count": len(exclusion_rows),
            "eligible_rows": sorted(
                eligible_rows,
                key=lambda row: (str(row["security_id"]), str(row["trading_item_id"])),
            ),
            "exclusion_rows": sorted(
                exclusion_rows,
                key=lambda row: (str(row["security_id"]), str(row["trading_item_id"])),
            ),
            "current_survivor_fallback_used": False,
            "alternate_listing_fallback_used": False,
            "ticker_entity_permno_fallback_used": False,
            "outcome_access_performed": False,
            "statistical_evidence_weight": 0,
            "financial_alpha_evidence": 0,
            "capital_authority": "NONE",
            "authority_class": "MECHANICAL_FIXTURE_ZERO_EVIDENCE" if fixture else "PIT_SOURCE_AUTHORITY_ZERO_ALPHA",
        }
    )
    return PrebreakoutPITAuthority(
        body=body,
        packet_sha256=_hash("PREBREAKOUT_PIT_AUTHORITY_V1", body),
    )


def verify_prebreakout_pit_authority(packet: PrebreakoutPITAuthority | Mapping[str, Any]) -> None:
    """Recompute packet closure and reject authority drift."""

    if isinstance(packet, PrebreakoutPITAuthority):
        body = dict(packet.body)
        sealed = packet.packet_sha256
    elif isinstance(packet, Mapping):
        body = {key: value for key, value in packet.items() if key != "packet_sha256"}
        sealed = str(packet.get("packet_sha256") or "")
    else:
        raise TypeError("prebreakout_pit_authority_packet_required")
    if body.get("schema_version") != PIT_AUTHORITY_SCHEMA:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_authority_schema_invalid")
    if body.get("family_id") != FAMILY_ID or body.get("risk_set_spec_id") != RISK_SET_SPEC_ID:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_authority_contract_invalid")
    if body.get("corporate_action_policy_id") != CORPORATE_ACTION_POLICY_ID:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_policy_invalid")
    if body.get("outcome_access_performed") is not False:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_outcome_access_forbidden")
    if body.get("financial_alpha_evidence") != 0 or body.get("statistical_evidence_weight") != 0:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_evidence_authority_forbidden")
    if body.get("capital_authority") != "NONE":
        raise PrebreakoutPITAuthorityError("prebreakout_pit_capital_authority_forbidden")
    source = body.get("source_authority")
    if not isinstance(source, Mapping):
        raise PrebreakoutPITAuthorityError("prebreakout_pit_source_authority_required")
    if source.get("date_local_membership_query") is not True or source.get("source_population_complete") is not True:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_source_completeness_invalid")
    if source.get("corporate_action_coverage_complete") is not True:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_coverage_incomplete")
    for field in (
        "current_survivor_back_projection_used",
        "current_primary_back_projection_used",
        "alternate_listing_backfill_used",
        "ticker_fallback_used",
        "company_entity_fallback_used",
        "permno_fallback_used",
    ):
        if source.get(field) is not False:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_forbidden_source_flag:" + field)
    if body.get("current_survivor_fallback_used") is not False:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_survivor_fallback_forbidden")
    if body.get("alternate_listing_fallback_used") is not False:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_alternate_listing_fallback_forbidden")
    if body.get("ticker_entity_permno_fallback_used") is not False:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_identity_fallback_forbidden")
    receipt_hashes = body.get("source_receipt_sha256s")
    if not isinstance(receipt_hashes, list) or any(not _SHA256_RE.fullmatch(str(value)) for value in receipt_hashes):
        raise PrebreakoutPITAuthorityError("prebreakout_pit_source_receipt_hashes_invalid")
    if source.get("source_receipt_sha256s") != receipt_hashes:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_source_receipt_binding_drift")
    eligible = body.get("eligible_rows")
    excluded = body.get("exclusion_rows")
    if not isinstance(eligible, list) or not isinstance(excluded, list):
        raise PrebreakoutPITAuthorityError("prebreakout_pit_compiled_rows_required")
    if int(body.get("eligible_count", -1)) != len(eligible) or int(body.get("exclusion_count", -1)) != len(excluded):
        raise PrebreakoutPITAuthorityError("prebreakout_pit_compiled_row_count_invalid")
    if int(body.get("candidate_count", -1)) != len(eligible) + len(excluded):
        raise PrebreakoutPITAuthorityError("prebreakout_pit_candidate_count_invalid")
    _verify_compiled_rows(
        eligible_rows=eligible,
        exclusion_rows=excluded,
        decision_session_date=str(body.get("decision_session_date") or ""),
        as_of=str(body.get("as_of") or ""),
    )
    expected = _hash("PREBREAKOUT_PIT_AUTHORITY_V1", _canonical(body))
    if sealed != expected:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_authority_hash_mismatch")


def build_b_minus_one_eligibility_proof(
    *,
    authority: PrebreakoutPITAuthority | None,
    case_id: str,
    display_symbol: str,
    breakout_contract_sha256: str | None,
    breakout_session: date | str | None,
    b_minus_1_session: date | str | None,
    expected_security_id: str | None = None,
    expected_trading_item_id: str | None = None,
) -> BMinusOneEligibilityProof:
    """Trace B-1 PIT eligibility without giving named cases statistical weight.

    The display symbol is trace metadata only. The algorithm never branches on
    symbol literals. If W2 has not frozen/bound the breakout contract, the proof
    is deterministically unavailable and no source result is inspected.
    """

    case = _nonempty_text(case_id, field="case_id")
    symbol = _nonempty_text(display_symbol, field="display_symbol")

    if not breakout_contract_sha256:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_w2_contract_hash_required")
    breakout_hash = _sha256(breakout_contract_sha256, field="breakout_contract_sha256")
    if breakout_hash != W2_CONTRACT_SHA256:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_w2_contract_hash_mismatch")
    if breakout_session is None or b_minus_1_session is None:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_breakout_sessions_required")
    breakout_day = _date_value(breakout_session, field="breakout_session")
    b1_day = _date_value(b_minus_1_session, field="b_minus_1_session")
    if b1_day >= breakout_day:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_bminus1_not_before_breakout")
    if authority is None:
        return _smoke_proof(
            case_id=case,
            display_symbol=symbol,
            breakout_contract_sha256=breakout_hash,
            breakout_session=breakout_day,
            b_minus_1_session=b1_day,
            security_id=expected_security_id,
            trading_item_id=expected_trading_item_id,
            status="DETERMINISTIC_UNAVAILABLE",
            reason=B_MINUS_1_PIT_AUTHORITY_UNAVAILABLE,
            authority_sha256=None,
        )

    verify_prebreakout_pit_authority(authority)
    if authority.decision_session_date != b1_day.isoformat():
        raise PrebreakoutPITAuthorityError("prebreakout_pit_authority_not_bminus1_session")
    if expected_security_id is None or expected_trading_item_id is None:
        return _smoke_proof(
            case_id=case,
            display_symbol=symbol,
            breakout_contract_sha256=breakout_hash,
            breakout_session=breakout_day,
            b_minus_1_session=b1_day,
            security_id=expected_security_id,
            trading_item_id=expected_trading_item_id,
            status="DETERMINISTIC_UNAVAILABLE",
            reason=EXCLUSION_IDENTITY_UNBOUND,
            authority_sha256=authority.packet_sha256,
        )

    security_id = _security_id(expected_security_id)
    trading_item_id = _trading_item_id(expected_trading_item_id)
    matches = [
        row
        for row in (*authority.eligible_rows, *authority.exclusion_rows)
        if row.get("security_id") == security_id
        and row.get("trading_item_id") == trading_item_id
    ]
    if len(matches) > 1:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_smoke_identity_duplicate")
    if not matches:
        return _smoke_proof(
            case_id=case,
            display_symbol=symbol,
            breakout_contract_sha256=breakout_hash,
            breakout_session=breakout_day,
            b_minus_1_session=b1_day,
            security_id=security_id,
            trading_item_id=trading_item_id,
            status="DETERMINISTIC_EXCLUSION",
            reason=EXCLUSION_NOT_IN_SOURCE,
            authority_sha256=authority.packet_sha256,
        )

    row = matches[0]
    eligible = row.get("eligibility_status") == ELIGIBLE
    return _smoke_proof(
        case_id=case,
        display_symbol=symbol,
        breakout_contract_sha256=breakout_hash,
        breakout_session=breakout_day,
        b_minus_1_session=b1_day,
        security_id=security_id,
        trading_item_id=trading_item_id,
        status="PIT_ELIGIBLE_B_MINUS_1" if eligible else "DETERMINISTIC_EXCLUSION",
        reason=None if eligible else str(row.get("exclusion_reason") or "UNKNOWN_EXCLUSION"),
        authority_sha256=authority.packet_sha256,
        row_available_at=str(row.get("available_at") or ""),
        row_corporate_action_state=str(row.get("corporate_action_state") or ""),
    )


def _validate_source_authority(
    raw: Mapping[str, Any],
    *,
    decision_day: date,
    receipt_hashes: set[str],
    fixture: bool,
) -> dict[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != _SOURCE_AUTHORITY_FIELDS:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_source_authority_fields_invalid")
    authority = dict(raw)
    if authority.get("schema_version") != SOURCE_AUTHORITY_SCHEMA:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_source_authority_schema_invalid")
    if authority.get("family_id") != FAMILY_ID or authority.get("risk_set_spec_id") != RISK_SET_SPEC_ID:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_source_authority_contract_invalid")
    mode = str(authority.get("capture_mode") or "")
    if mode not in _CAPTURE_MODES:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_capture_mode_invalid")
    if _date_value(authority.get("decision_session_date"), field="source_decision_session_date") != decision_day:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_source_decision_date_mismatch")
    provider = str(authority.get("provider") or "").upper()
    if fixture:
        if provider != "DETERMINISTIC_FIXTURE_ONLY":
            raise PrebreakoutPITAuthorityError("prebreakout_pit_fixture_provider_invalid")
    elif provider not in {"S&P CAPITAL IQ PRO", "S&P CAPITAL IQ", "SPCIQPRO"}:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_provider_invalid")
    if authority.get("date_local_membership_query") is not True:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_date_local_membership_required")
    if authority.get("source_population_complete") is not True:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_source_population_incomplete")
    if authority.get("corporate_action_coverage_complete") is not True:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_coverage_incomplete")
    if mode == HISTORICAL_CAPTURE_MODE and authority.get("historical_as_of_mechanically_bound") is not True:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_historical_asof_not_bound")
    if mode == PROSPECTIVE_CAPTURE_MODE and authority.get("historical_as_of_mechanically_bound") is not False:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_prospective_historical_asof_flag_invalid")
    for field in (
        "current_survivor_back_projection_used",
        "current_primary_back_projection_used",
        "alternate_listing_backfill_used",
        "ticker_fallback_used",
        "company_entity_fallback_used",
        "permno_fallback_used",
    ):
        if authority.get(field) is not False:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_forbidden_source_flag:" + field)
    if authority.get("primary_listing_resolution") != "DATE_LOCAL_PROVIDER_OR_UNIQUE_QUALIFYING_LISTING":
        raise PrebreakoutPITAuthorityError("prebreakout_pit_primary_listing_resolution_invalid")
    if authority.get("ambiguous_listing_policy") != "DETERMINISTIC_EXCLUDE_NO_FALLBACK":
        raise PrebreakoutPITAuthorityError("prebreakout_pit_ambiguous_listing_policy_invalid")
    bound = authority.get("source_receipt_sha256s")
    if not isinstance(bound, list) or set(map(str, bound)) != receipt_hashes:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_source_receipt_set_not_exact")
    authority["source_receipt_sha256s"] = sorted(receipt_hashes)
    return _canonical(authority)


def _validate_source_receipts(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_source_receipts_required")
    output: list[dict[str, Any]] = []
    hashes: set[str] = set()
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise PrebreakoutPITAuthorityError("prebreakout_pit_source_receipt_mapping_required")
        try:
            validate_source_receipt_binding(raw)
        except ValueError as exc:
            raise PrebreakoutPITAuthorityError(str(exc)) from exc
        digest = _sha256(str(raw.get("raw_receipt_sha256") or ""), field="source_receipt_sha256")
        if digest in hashes:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_source_receipt_duplicate")
        hashes.add(digest)
        output.append(_canonical(dict(raw)))
    return sorted(output, key=lambda row: str(row["raw_receipt_sha256"]))


def _validate_source_receipt_timing(
    receipts: Sequence[Mapping[str, Any]],
    *,
    capture_mode: str,
    decision_day: date,
    cutoff: datetime,
) -> None:
    for receipt in receipts:
        observed_start = _date_value(receipt.get("observed_range_start"), field="source_observed_range_start")
        observed_end = _date_value(receipt.get("observed_range_end"), field="source_observed_range_end")
        if observed_start > observed_end or observed_end > decision_day:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_source_observed_range_after_decision")
        retrieved = _utc_datetime(receipt.get("retrieved_at"), field="source_retrieved_at")
        if capture_mode == PROSPECTIVE_CAPTURE_MODE and retrieved > cutoff:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_prospective_source_receipt_after_asof")


def _validate_candidate_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    decision_day: date,
    cutoff: datetime,
    receipt_hashes: set[str],
) -> list[dict[str, Any]]:
    if not rows:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_candidate_rows_required")
    output: list[dict[str, Any]] = []
    seen_security: set[str] = set()
    seen_trading: set[str] = set()
    for raw in rows:
        if not isinstance(raw, Mapping) or set(raw) != _CANDIDATE_FIELDS:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_candidate_row_fields_invalid")
        if raw.get("schema_version") != CANDIDATE_ROW_SCHEMA:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_candidate_row_schema_invalid")
        security_id = _security_id(raw.get("security_id"))
        company_id = _company_id(raw.get("company_id"))
        trading_item_id = _trading_item_id(raw.get("trading_item_id"))
        spt = _spt_id(raw.get("spt_instrument_item_id"))
        if spt != f"SPT{trading_item_id}":
            raise PrebreakoutPITAuthorityError("prebreakout_pit_trading_item_alias_mismatch")
        if security_id in seen_security:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_candidate_security_duplicate")
        if trading_item_id in seen_trading:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_candidate_trading_item_duplicate")
        seen_security.add(security_id)
        seen_trading.add(trading_item_id)
        if _date_value(raw.get("membership_as_of_date"), field="membership_as_of_date") != decision_day:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_candidate_not_date_local")
        primary_state = str(raw.get("primary_listing_state") or "")
        if primary_state not in _PRIMARY_STATES:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_primary_listing_state_invalid")
        primary_proof = str(raw.get("primary_listing_proof_kind") or "")
        if primary_proof not in _PRIMARY_PROOFS:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_primary_listing_proof_invalid")
        allowed_proofs = {
            PRIMARY_DATE_LOCAL: {PRIMARY_PROOF_PROVIDER, PRIMARY_PROOF_UNIQUE},
            NON_PRIMARY_DATE_LOCAL: {PRIMARY_PROOF_NON_PRIMARY},
            AMBIGUOUS_DATE_LOCAL: {PRIMARY_PROOF_AMBIGUOUS},
        }
        if primary_proof not in allowed_proofs[primary_state]:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_primary_listing_state_proof_mismatch")
        if not isinstance(raw.get("active_tradable"), bool):
            raise PrebreakoutPITAuthorityError("prebreakout_pit_active_tradable_boolean_required")
        observed = _utc_datetime(raw.get("observed_at"), field="candidate_observed_at")
        available = _utc_datetime(raw.get("available_at"), field="candidate_available_at")
        if observed > available or available > cutoff:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_candidate_availability_order_invalid")
        source_receipt = _sha256(raw.get("source_receipt_sha256"), field="candidate_source_receipt_sha256")
        identity_receipt = _sha256(raw.get("identity_receipt_sha256"), field="candidate_identity_receipt_sha256")
        if source_receipt not in receipt_hashes or identity_receipt not in receipt_hashes:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_candidate_receipt_unbound")
        output.append(
            _canonical(
                {
                    "security_id": security_id,
                    "company_id": company_id,
                    "trading_item_id": trading_item_id,
                    "spt_instrument_item_id": spt,
                    "membership_as_of_date": decision_day.isoformat(),
                    "listing_country": _nonempty_text(raw.get("listing_country"), field="listing_country").upper(),
                    "security_class": _nonempty_text(raw.get("security_class"), field="security_class").upper(),
                    "primary_listing_state": primary_state,
                    "primary_listing_proof_kind": primary_proof,
                    "active_tradable": bool(raw["active_tradable"]),
                    "observed_at": _timestamp_text(observed),
                    "available_at": _timestamp_text(available),
                    "source_id": _nonempty_text(raw.get("source_id"), field="candidate_source_id"),
                    "source_receipt_sha256": source_receipt,
                    "identity_receipt_sha256": identity_receipt,
                }
            )
        )
    return sorted(output, key=lambda row: (str(row["security_id"]), str(row["trading_item_id"])))


def _validate_corporate_action_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    candidates: Sequence[Mapping[str, Any]],
    decision_day: date,
    cutoff: datetime,
    receipt_hashes: set[str],
) -> list[dict[str, Any]]:
    if not rows:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_rows_required")
    candidate_keys = {
        (str(row["security_id"]), str(row["trading_item_id"])) for row in candidates
    }
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for raw in rows:
        if not isinstance(raw, Mapping) or set(raw) != _CORPORATE_ACTION_FIELDS:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_row_fields_invalid")
        if raw.get("schema_version") != CORPORATE_ACTION_ROW_SCHEMA:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_row_schema_invalid")
        security_id = _security_id(raw.get("security_id"))
        trading_item_id = _trading_item_id(raw.get("trading_item_id"))
        key = (security_id, trading_item_id)
        if key not in candidate_keys:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_outside_candidates")
        if key in seen:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_duplicate_identity")
        seen.add(key)
        state = str(raw.get("action_state") or "")
        if state not in _ACTION_STATES:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_state_invalid")
        effective_raw = raw.get("effective_session_date")
        event_type = str(raw.get("event_type") or "").strip()
        if state == ACTION_CLEAR:
            if effective_raw not in (None, "") or event_type not in ("", "NONE"):
                raise PrebreakoutPITAuthorityError("prebreakout_pit_clear_action_fields_invalid")
            effective_text = None
            event_type = "NONE"
        elif state == ACTION_PENDING_TERMINAL:
            effective = _date_value(effective_raw, field="corporate_action_effective_session_date")
            if effective <= decision_day or not event_type:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_pending_terminal_semantics_invalid")
            effective_text = effective.isoformat()
        elif state == ACTION_EFFECTIVE_TERMINAL:
            effective = _date_value(effective_raw, field="corporate_action_effective_session_date")
            if effective > decision_day or not event_type:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_effective_terminal_semantics_invalid")
            effective_text = effective.isoformat()
        else:
            if not event_type:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_unresolved_action_event_type_required")
            effective_text = None if effective_raw in (None, "") else _date_value(
                effective_raw,
                field="corporate_action_effective_session_date",
            ).isoformat()
        observed = _utc_datetime(raw.get("observed_at"), field="corporate_action_observed_at")
        available = _utc_datetime(raw.get("available_at"), field="corporate_action_available_at")
        if observed > available or available > cutoff:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_availability_order_invalid")
        receipt = _sha256(raw.get("source_receipt_sha256"), field="corporate_action_source_receipt_sha256")
        if receipt not in receipt_hashes:
            raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_receipt_unbound")
        output.append(
            _canonical(
                {
                    "security_id": security_id,
                    "trading_item_id": trading_item_id,
                    "action_state": state,
                    "effective_session_date": effective_text,
                    "event_type": event_type,
                    "observed_at": _timestamp_text(observed),
                    "available_at": _timestamp_text(available),
                    "source_id": _nonempty_text(raw.get("source_id"), field="corporate_action_source_id"),
                    "source_receipt_sha256": receipt,
                }
            )
        )
    if seen != candidate_keys:
        raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_coverage_not_exact")
    return sorted(output, key=lambda row: (str(row["security_id"]), str(row["trading_item_id"])))


def _eligibility_reason(candidate: Mapping[str, Any], action: Mapping[str, Any]) -> str | None:
    if candidate.get("listing_country") != "US":
        return EXCLUSION_NON_US
    if candidate.get("security_class") != "COMMON_EQUITY":
        return EXCLUSION_NON_COMMON
    primary = candidate.get("primary_listing_state")
    if primary == AMBIGUOUS_DATE_LOCAL:
        return EXCLUSION_AMBIGUOUS_PRIMARY
    if primary != PRIMARY_DATE_LOCAL:
        return EXCLUSION_NON_PRIMARY
    if candidate.get("active_tradable") is not True:
        return EXCLUSION_NOT_ACTIVE
    action_state = action.get("action_state")
    if action_state == ACTION_UNRESOLVED:
        return EXCLUSION_CA_UNRESOLVED
    if action_state == ACTION_EFFECTIVE_TERMINAL:
        return EXCLUSION_CA_EFFECTIVE
    return None


def _require_unique_eligible_authority(rows: Sequence[Mapping[str, Any]]) -> None:
    for field in ("security_id", "trading_item_id", "company_id"):
        values = [str(row[field]) for row in rows]
        if len(values) != len(set(values)):
            raise PrebreakoutPITAuthorityError(f"prebreakout_pit_eligible_{field}_not_unique")


def _verify_compiled_rows(
    *,
    eligible_rows: Sequence[Mapping[str, Any]],
    exclusion_rows: Sequence[Mapping[str, Any]],
    decision_session_date: str,
    as_of: str,
) -> None:
    decision_day = _date_value(decision_session_date, field="decision_session_date")
    cutoff = _utc_datetime(as_of, field="as_of")
    seen: set[tuple[str, str]] = set()
    for expected_status, rows in ((ELIGIBLE, eligible_rows), ("EXCLUDED", exclusion_rows)):
        for row in rows:
            if not isinstance(row, Mapping):
                raise PrebreakoutPITAuthorityError("prebreakout_pit_compiled_row_mapping_required")
            security_id = _security_id(row.get("security_id"))
            company_id = _company_id(row.get("company_id"))
            trading_item_id = _trading_item_id(row.get("trading_item_id"))
            if _spt_id(row.get("spt_instrument_item_id")) != f"SPT{trading_item_id}":
                raise PrebreakoutPITAuthorityError("prebreakout_pit_trading_item_alias_mismatch")
            key = (security_id, trading_item_id)
            if key in seen:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_compiled_identity_duplicate")
            seen.add(key)
            if _date_value(row.get("membership_as_of_date"), field="membership_as_of_date") != decision_day:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_compiled_row_not_date_local")
            available = _utc_datetime(row.get("available_at"), field="compiled_available_at")
            if available > cutoff:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_compiled_available_after_asof")
            if row.get("eligibility_status") != expected_status:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_compiled_eligibility_status_invalid")
            if expected_status == ELIGIBLE and row.get("exclusion_reason") is not None:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_eligible_exclusion_reason_forbidden")
            if expected_status == "EXCLUDED" and not str(row.get("exclusion_reason") or "").strip():
                raise PrebreakoutPITAuthorityError("prebreakout_pit_exclusion_reason_required")
            if row.get("primary_listing_state") not in _PRIMARY_STATES:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_primary_listing_state_invalid")
            if row.get("primary_listing_proof_kind") not in _PRIMARY_PROOFS:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_primary_listing_proof_invalid")
            if row.get("corporate_action_state") not in _ACTION_STATES:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_corporate_action_state_invalid")
            # Touch company_id so malformed-but-unused company identity cannot hide behind a valid hash.
            if not company_id:
                raise PrebreakoutPITAuthorityError("prebreakout_pit_company_id_invalid")
    _require_unique_eligible_authority(eligible_rows)


def _smoke_proof(
    *,
    case_id: str,
    display_symbol: str,
    breakout_contract_sha256: str | None,
    breakout_session: date | None,
    b_minus_1_session: date | None,
    security_id: str | None,
    trading_item_id: str | None,
    status: str,
    reason: str | None,
    authority_sha256: str | None,
    row_available_at: str | None = None,
    row_corporate_action_state: str | None = None,
) -> BMinusOneEligibilityProof:
    body = _canonical(
        {
            "schema_version": SMOKE_PROOF_SCHEMA,
            "family_id": FAMILY_ID,
            "case_id": case_id,
            "display_symbol": display_symbol,
            "display_symbol_used_for_logic": False,
            "breakout_contract_sha256": breakout_contract_sha256,
            "breakout_session": None if breakout_session is None else breakout_session.isoformat(),
            "b_minus_1_session": None if b_minus_1_session is None else b_minus_1_session.isoformat(),
            "security_id": security_id,
            "trading_item_id": trading_item_id,
            "status": status,
            "reason": reason,
            "pit_authority_sha256": authority_sha256,
            "row_available_at": row_available_at,
            "row_corporate_action_state": row_corporate_action_state,
            "statistical_weight": 0,
            "promotion_denominator_weight": 0,
            "outcome_access_performed": False,
            "financial_alpha_evidence": 0,
            "capital_authority": "NONE",
        }
    )
    return BMinusOneEligibilityProof(
        body=body,
        proof_sha256=_hash("PREBREAKOUT_BMINUS1_SMOKE_PROOF_V1", body),
    )


def _security_id(value: Any) -> str:
    text = str(value or "").strip()
    if not _CIQ_SECURITY_RE.fullmatch(text):
        raise PrebreakoutPITAuthorityError("prebreakout_pit_ciq_security_id_required")
    return text


def _company_id(value: Any) -> str:
    text = str(value or "").strip()
    if not text.isdigit():
        raise PrebreakoutPITAuthorityError("prebreakout_pit_company_id_invalid")
    return text


def _trading_item_id(value: Any) -> str:
    text = str(value or "").strip()
    if not _TRADING_ITEM_RE.fullmatch(text):
        raise PrebreakoutPITAuthorityError("prebreakout_pit_trading_item_id_required")
    return text


def _spt_id(value: Any) -> str:
    text = str(value or "").strip()
    if not _SPT_RE.fullmatch(text):
        raise PrebreakoutPITAuthorityError("prebreakout_pit_spt_instrument_item_id_required")
    return text


def _sha256(value: Any, *, field: str) -> str:
    text = str(value or "").strip().lower()
    if not _SHA256_RE.fullmatch(text):
        raise PrebreakoutPITAuthorityError(f"prebreakout_pit_{field}_invalid")
    return text


def _nonempty_text(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise PrebreakoutPITAuthorityError(f"prebreakout_pit_{field}_required")
    return text


def _date_value(value: date | str | Any, *, field: str) -> date:
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    else:
        try:
            parsed = date.fromisoformat(str(value or ""))
        except ValueError as exc:
            raise PrebreakoutPITAuthorityError(f"prebreakout_pit_{field}_invalid") from exc
    return parsed


def _utc_datetime(value: datetime | Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        except ValueError as exc:
            raise PrebreakoutPITAuthorityError(f"prebreakout_pit_{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PrebreakoutPITAuthorityError(f"prebreakout_pit_{field}_timezone_required")
    return parsed.astimezone(timezone.utc)


def _timestamp_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _canonical(value: Any) -> Any:
    if isinstance(value, datetime):
        return _timestamp_text(_utc_datetime(value, field="canonical_datetime"))
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, float):
        return format(value, ".17g")
    return value


def _hash(domain: str, value: Any) -> str:
    raw = json.dumps(
        {"domain": domain, "value": _canonical(value)},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
