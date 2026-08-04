"""Append-only prospective paper operation for certified portfolio profiles.

Runtime observations and review changes are operator proposals until deterministic
preview validation and explicit confirmation. Confirmed episodes are reconstructed
from one canonical event log; scenario-authored later observations are prohibited.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, DecimalException, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from core.gv_fs0_canonical import assert_sha256, canonical_document_bytes, domain_hash
from core.gv_v2_mu_nvda_reconciliation import (
    MuNvdaReconciliationError,
    load_verified_mu_nvda_reconciliation,
)
from gv_portfolio_v0.execution import ExecutionError, portfolio_book_event
from gv_portfolio_v0.operated import (
    OperatedPortfolioError,
    STATUS_FUNDED,
    _append_trade,
    _append_transition_event,
    _decision_snapshot,
    _evidence,
    _record,
    _thesis,
    _transition_legs_from_reviews,
    build_draft_workspace,
    confirm_initial_portfolio,
)
from gv_portfolio_v0.operated_scenarios import (
    OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    PROSPECTIVE_25_SCENARIO_ID,
    REAL_MU_PROSPECTIVE_SCENARIO_ID,
    get_scenario,
)
from gv_portfolio_v0.replay import (
    ReplayError,
    certify_replay_prefix,
    reconstruct_book,
    reconstruct_exact,
    replay_idempotent,
)

PROSPECTIVE_SCHEMA = "gv_prospective_paper_workspace_v1"
PROPOSAL_SCHEMA = "gv_prospective_observation_proposal_v2"
EPISODE_SCHEMA = "gv_prospective_confirmed_episode_v1"
REJECTED_EPISODE_SCHEMA = "gv_prospective_rejected_episode_v1"
INSTRUMENT_OUTCOMES = frozenset({"ADMIT", "REJECT", "ABSTAIN"})
MAX_PROSPECTIVE_TEXT_LENGTH = 4096
MAX_PROSPECTIVE_REVIEW_UPDATES = 64
MAX_PROSPECTIVE_EVENT_COUNT = 4096
MAX_PROSPECTIVE_EPISODE_COUNT = 512
MAX_PROSPECTIVE_REQUEST_BYTES = 256_000
MAX_PROSPECTIVE_DECIMAL_INTEGER_DIGITS = 18
MAX_PROSPECTIVE_DECIMAL_FRACTION_DIGITS = 18
MAX_PROSPECTIVE_QUANTITY_DIGITS = 18


class ProspectiveOperationError(OperatedPortfolioError):
    """Fail-closed prospective paper operation error."""


@dataclass(frozen=True, slots=True)
class ForwardOperatedDecisionPacket:
    """Typed owner assertion admitted only by the bounded forward-operated profile."""

    instrument_id: str
    evidence_content: str
    source_locator: str
    evidence_observed_at: str
    market_price: str
    market_observed_at: str
    market_source_identity: str
    target_quantity: str
    principal_claim: str
    operator_rationale: str
    pit_identity: dict[str, Any]


def _utc_datetime(value: str, *, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ProspectiveOperationError(f"{field.upper()}_REQUIRED")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProspectiveOperationError(f"{field.upper()}_INVALID") from exc
    if parsed.tzinfo is None:
        raise ProspectiveOperationError(f"{field.upper()}_UTC_REQUIRED")
    return parsed.astimezone(timezone.utc)


def _utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _required_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProspectiveOperationError(f"{field.upper()}_REQUIRED")
    text = value.strip()
    if len(text) > MAX_PROSPECTIVE_TEXT_LENGTH:
        raise ProspectiveOperationError(f"{field.upper()}_TOO_LONG")
    return text


def _whole_quantity(value: Any) -> str:
    if isinstance(value, bool):
        raise ProspectiveOperationError("TARGET_QUANTITY_INVALID")
    text = str(value).strip()
    if len(text) > MAX_PROSPECTIVE_QUANTITY_DIGITS:
        raise ProspectiveOperationError("TARGET_QUANTITY_OUT_OF_BOUNDS")
    try:
        quantity = int(text)
    except (TypeError, ValueError) as exc:
        raise ProspectiveOperationError("TARGET_QUANTITY_INVALID") from exc
    if quantity < 0 or str(quantity) != text:
        raise ProspectiveOperationError("TARGET_QUANTITY_INVALID")
    return text


def _score(value: Any) -> int:
    if isinstance(value, bool):
        raise ProspectiveOperationError("NET_SCORE_BPS_INVALID")
    try:
        score = int(value)
    except (TypeError, ValueError) as exc:
        raise ProspectiveOperationError("NET_SCORE_BPS_INVALID") from exc
    if score < -100000 or score > 100000:
        raise ProspectiveOperationError("NET_SCORE_BPS_OUT_OF_RANGE")
    return score


def _positive_decimal_text(value: Any, *, field: str) -> str:
    if isinstance(value, bool) or isinstance(value, float):
        raise ProspectiveOperationError(f"{field.upper()}_DECIMAL_TYPE_INVALID")
    raw_text = str(value).strip()
    if len(raw_text) > MAX_PROSPECTIVE_TEXT_LENGTH:
        raise ProspectiveOperationError(f"{field.upper()}_TOO_LONG")
    try:
        parsed = Decimal(raw_text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ProspectiveOperationError(f"{field.upper()}_DECIMAL_INVALID") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ProspectiveOperationError(f"{field.upper()}_MUST_BE_POSITIVE")
    sign, digits, exponent = parsed.as_tuple()
    digits = list(digits)
    while len(digits) > 1 and digits[-1] == 0:
        digits.pop()
        exponent += 1
    integer_digits = len(digits) + max(exponent, 0)
    fraction_digits = max(-exponent, 0)
    if (
        integer_digits > MAX_PROSPECTIVE_DECIMAL_INTEGER_DIGITS
        or fraction_digits > MAX_PROSPECTIVE_DECIMAL_FRACTION_DIGITS
    ):
        raise ProspectiveOperationError(f"{field.upper()}_OUT_OF_BOUNDS")
    coefficient = "".join(str(digit) for digit in digits)
    if exponent >= 0:
        text = coefficient + ("0" * exponent)
    else:
        split = len(coefficient) + exponent
        if split <= 0:
            text = "0." + ("0" * -split) + coefficient
        else:
            text = coefficient[:split] + "." + coefficient[split:]
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if sign and text != "0":
        text = "-" + text
    return text


def _sha256_text(value: Any, *, field: str) -> str:
    text = _required_text(value, field=field)
    try:
        assert_sha256(text)
    except ValueError as exc:
        raise ProspectiveOperationError(f"{field.upper()}_INVALID") from exc
    return text


def _normalize_pit_identity(value: Any) -> dict[str, Any]:
    """Normalize the typed PIT identity tuple into persisted canonical primitives."""

    if not isinstance(value, Mapping):
        raise ProspectiveOperationError("FORWARD_OPERATED_PIT_IDENTITY_REQUIRED")
    certified_book_id = _sha256_text(
        value.get("certified_book_id"), field="pit_certified_book_id"
    )
    certified_book_head_event_id = _required_text(
        value.get("certified_book_head_event_id"),
        field="pit_certified_book_head_event_id",
    )
    evidence_set_id = _sha256_text(
        value.get("evidence_set_id"), field="pit_evidence_set_id"
    )
    as_of_raw = _required_text(value.get("as_of_utc"), field="pit_as_of_utc")
    as_of = _utc_datetime(as_of_raw, field="pit_as_of_utc")
    as_of_utc = _utc_timestamp(as_of)
    if as_of_raw != as_of_utc:
        raise ProspectiveOperationError("PIT_AS_OF_UTC_NOT_CANONICAL")

    market = value.get("market_snapshot_id")
    if not isinstance(market, Mapping):
        raise ProspectiveOperationError("PIT_MARKET_SNAPSHOT_REQUIRED")
    market_kind = _required_text(
        market.get("kind"), field="pit_market_snapshot_kind"
    )
    if market_kind != "NO_MARKET_DEPENDENCY_CASH_ONLY_V1":
        raise ProspectiveOperationError("PIT_MARKET_SNAPSHOT_KIND_INVALID")
    market_book_id = _sha256_text(
        market.get("certified_book_id"), field="pit_market_certified_book_id"
    )
    market_head_event_id = _required_text(
        market.get("certified_book_head_event_id"),
        field="pit_market_certified_book_head_event_id",
    )
    market_book_hash = _sha256_text(
        market.get("certified_book_hash"), field="pit_market_certified_book_hash"
    )
    validation_digest = _sha256_text(
        market.get("validation_digest"), field="pit_market_validation_digest"
    )
    if market_book_id != certified_book_id:
        raise ProspectiveOperationError("PIT_MARKET_BOOK_ID_MISMATCH")
    if market_head_event_id != certified_book_head_event_id:
        raise ProspectiveOperationError("PIT_MARKET_HEAD_EVENT_MISMATCH")
    return {
        "certified_book_id": certified_book_id,
        "certified_book_head_event_id": certified_book_head_event_id,
        "evidence_set_id": evidence_set_id,
        "market_snapshot_id": {
            "kind": market_kind,
            "certified_book_id": market_book_id,
            "certified_book_head_event_id": market_head_event_id,
            "certified_book_hash": market_book_hash,
            "validation_digest": validation_digest,
        },
        "as_of_utc": as_of_utc,
    }


@lru_cache(maxsize=1)
def _validated_forward_pit_identity() -> dict[str, Any]:
    """Load the current validated banked PIT identity without an import cycle."""

    try:
        from core.gv_pit.adapters import build_real_pit_source_bundle
        from core.gv_pit.contracts import canonical_value

        return _normalize_pit_identity(
            canonical_value(build_real_pit_source_bundle().pit_identity)
        )
    except ProspectiveOperationError:
        raise
    except Exception as exc:
        raise ProspectiveOperationError(
            "FORWARD_OPERATED_PIT_IDENTITY_UNAVAILABLE"
        ) from exc


def _verify_source_authority(scenario: Mapping[str, Any]) -> None:
    authority = scenario.get("source_authority")
    if authority is None:
        return
    if not isinstance(authority, Mapping):
        raise ProspectiveOperationError("PROSPECTIVE_SOURCE_AUTHORITY_INVALID")
    if authority.get("verification_mode") != "REBUILD_FROM_BANKED_SOURCES":
        raise ProspectiveOperationError("PROSPECTIVE_SOURCE_VERIFICATION_MODE_INVALID")
    result_path_text = _required_text(
        authority.get("result_path"), field="source_result_path"
    )
    relative_path = Path(result_path_text)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ProspectiveOperationError("PROSPECTIVE_SOURCE_PATH_INVALID")
    repository_root = Path(__file__).resolve().parents[1]
    result_path = (repository_root / relative_path).resolve()
    if not result_path.is_relative_to(repository_root.resolve()):
        raise ProspectiveOperationError("PROSPECTIVE_SOURCE_PATH_ESCAPE")
    try:
        result = load_verified_mu_nvda_reconciliation(result_path=result_path)
    except MuNvdaReconciliationError as exc:
        raise ProspectiveOperationError(
            f"PROSPECTIVE_SOURCE_AUTHORITY_INVALID:{exc}"
        ) from exc
    required = {
        "schema_version": authority.get("schema_version"),
        "case_id": authority.get("case_id"),
        "reconciliation_hash": authority.get("reconciliation_hash"),
        "research_action": "HOLD_FOR_EVIDENCE",
        "portfolio_action": "NO_POSITION",
        "portfolio_mutation_authorized": False,
    }
    for key, expected in required.items():
        if result.get(key) != expected:
            raise ProspectiveOperationError(
                f"PROSPECTIVE_SOURCE_AUTHORITY_MISMATCH:{key}"
            )


def _baseline_workspace(
    scenario_id: str = PROSPECTIVE_25_SCENARIO_ID,
) -> dict[str, Any]:
    scenario = get_scenario(scenario_id)
    _verify_source_authority(scenario)
    if scenario.get("runtime_observation_mode") is not True:
        raise ProspectiveOperationError("PROSPECTIVE_RUNTIME_MODE_REQUIRED")
    if not isinstance(scenario.get("source_scenario_id"), str):
        raise ProspectiveOperationError("PROSPECTIVE_SOURCE_SCENARIO_INVALID")
    if "no_change" in scenario or "transition" in scenario:
        raise ProspectiveOperationError("SCENARIO_AUTHORED_EPISODE_PROHIBITED")
    workspace = confirm_initial_portfolio(build_draft_workspace(scenario_id))
    if workspace["status"] != STATUS_FUNDED:
        raise ProspectiveOperationError("CERTIFIED_FUNDED_BASELINE_REQUIRED")
    if scenario_id == OPERATED_PAPER_CAPITAL_SCENARIO_ID:
        workspace["baseline_book_hash"] = workspace["book"]["book_hash"]
        workspace["pit_identity"] = _validated_forward_pit_identity()
    return workspace


def _decorate(
    workspace: Mapping[str, Any],
    *,
    baseline_hash: str,
    baseline_event_count: int,
    proposals: list[dict[str, Any]],
    rejected_proposals: list[dict[str, Any]],
    episode_history: list[dict[str, Any]],
) -> dict[str, Any]:
    result = deepcopy(dict(workspace))
    result["operation_schema_version"] = PROSPECTIVE_SCHEMA
    result["operation_mode"] = "PROSPECTIVE_PAPER"
    scenario = get_scenario(str(result["scenario_id"]))
    result["source_scenario_id"] = scenario["source_scenario_id"]
    if "source_authority" in scenario:
        result["source_authority"] = deepcopy(scenario["source_authority"])
    if result["scenario_id"] == OPERATED_PAPER_CAPITAL_SCENARIO_ID:
        expected_pit_identity = _validated_forward_pit_identity()
        if result.get("baseline_book_hash") != expected_pit_identity["certified_book_id"]:
            raise ProspectiveOperationError(
                "FORWARD_OPERATED_PIT_BASELINE_BOOK_MISMATCH"
            )
        result["pit_identity"] = deepcopy(expected_pit_identity)
    result["baseline_workspace_hash"] = baseline_hash
    result["baseline_event_count"] = baseline_event_count
    result["prospective_episode_count"] = len(episode_history)
    result["operator_action_count"] = len(episode_history) * 2
    result["prospective_proposals"] = deepcopy(proposals)
    result["rejected_proposals"] = deepcopy(rejected_proposals)
    result["prospective_episode_history"] = deepcopy(episode_history)
    return result


def build_prospective_workspace(
    scenario_id: str = PROSPECTIVE_25_SCENARIO_ID,
) -> dict[str, Any]:
    """Bootstrap one certified runtime-observation portfolio profile."""

    baseline = _baseline_workspace(scenario_id)
    baseline_hash = domain_hash("GV-PROSPECTIVE-PAPER:BASELINE:V1", baseline)
    return _decorate(
        baseline,
        baseline_hash=baseline_hash,
        baseline_event_count=len(baseline["events"]),
        proposals=[],
        rejected_proposals=[],
        episode_history=[],
    )


def _normalize_review_update(
    workspace: Mapping[str, Any], update: Mapping[str, Any]
) -> dict[str, Any]:
    if not isinstance(update, Mapping):
        raise ProspectiveOperationError("REVIEW_UPDATE_MAPPING_REQUIRED")
    instrument_id = _required_text(update.get("instrument_id"), field="instrument_id")
    known_ids = {row["instrument_id"] for row in workspace["instruments"]}
    if instrument_id not in known_ids:
        raise ProspectiveOperationError("OBSERVATION_INSTRUMENT_UNKNOWN")
    outcome = _required_text(update.get("outcome"), field="outcome").upper()
    if outcome == "CASH":
        raise ProspectiveOperationError("CASH_IS_PORTFOLIO_CANDIDATE")
    if outcome not in INSTRUMENT_OUTCOMES:
        raise ProspectiveOperationError("INSTRUMENT_OUTCOME_INVALID")
    target_quantity = _whole_quantity(update.get("target_quantity"))
    if outcome != "ADMIT" and target_quantity != "0":
        raise ProspectiveOperationError("NON_ADMIT_TARGET_QUANTITY_MUST_BE_ZERO")
    return {
        "instrument_id": instrument_id,
        "outcome": outcome,
        "net_score_bps": _score(update.get("net_score_bps")),
        "target_quantity": target_quantity,
        "principal_claim": _required_text(
            update.get("principal_claim"), field="principal_claim"
        ),
    }


def _normalize_request(
    workspace: Mapping[str, Any], request: Mapping[str, Any]
) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise ProspectiveOperationError("OBSERVATION_REQUEST_MAPPING_REQUIRED")
    try:
        request_size = len(canonical_document_bytes(dict(request)))
    except (TypeError, ValueError) as exc:
        raise ProspectiveOperationError("OBSERVATION_REQUEST_CANONICAL_INVALID") from exc
    if request_size > MAX_PROSPECTIVE_REQUEST_BYTES:
        raise ProspectiveOperationError("OBSERVATION_REQUEST_BYTES_OUT_OF_BOUNDS")
    observed_at = _required_text(request.get("observed_at"), field="observed_at")
    observed_time = _utc_datetime(observed_at, field="observed_at")
    latest_time = max(
        _utc_datetime(row["effective_at"], field="effective_at")
        for row in workspace["events"]
    )
    if observed_time <= latest_time:
        raise ProspectiveOperationError("OBSERVATION_TIMESTAMP_NOT_AFTER_AUTHORITY")
    content = _required_text(request.get("content"), field="content")
    locator = _required_text(request.get("locator"), field="locator")
    if workspace.get("scenario_id") == REAL_MU_PROSPECTIVE_SCENARIO_ID:
        initial_evidence = workspace.get("evidence_references", [None])[0]
        if not isinstance(initial_evidence, Mapping):
            raise ProspectiveOperationError("REAL_MU_SOURCE_EVIDENCE_REQUIRED")
        if content != initial_evidence.get("content"):
            raise ProspectiveOperationError("REAL_MU_EXACT_EVIDENCE_CONTENT_REQUIRED")
        if locator != initial_evidence.get("locator"):
            raise ProspectiveOperationError("REAL_MU_EXACT_EVIDENCE_LOCATOR_REQUIRED")

    raw_updates = request.get("review_updates")
    if not isinstance(raw_updates, list) or not raw_updates:
        raise ProspectiveOperationError("REVIEW_UPDATES_REQUIRED")
    if len(raw_updates) > MAX_PROSPECTIVE_REVIEW_UPDATES:
        raise ProspectiveOperationError("REVIEW_UPDATES_TOO_MANY")
    updates = [_normalize_review_update(workspace, row) for row in raw_updates]
    ids = [row["instrument_id"] for row in updates]
    if len(ids) != len(set(ids)):
        raise ProspectiveOperationError("REVIEW_UPDATE_INSTRUMENT_DUPLICATE")
    operator_rationale = _required_text(
        request.get("operator_rationale"), field="operator_rationale"
    )
    normalized: dict[str, Any] = {
        "content": content,
        "locator": locator,
        "observed_at": _utc_timestamp(observed_time),
        "review_updates": updates,
        "operator_rationale": operator_rationale,
    }

    if workspace.get("scenario_id") == OPERATED_PAPER_CAPITAL_SCENARIO_ID:
        if len(updates) != 1:
            raise ProspectiveOperationError("FORWARD_OPERATED_SINGLE_INSTRUMENT_REQUIRED")
        update = updates[0]
        if update["outcome"] != "ADMIT" or update["target_quantity"] == "0":
            raise ProspectiveOperationError("FORWARD_OPERATED_NONZERO_ADMIT_REQUIRED")
        if (
            "forward_operated_packet" in request
            and request.get("forward_operated_packet") is not None
            and not isinstance(request.get("forward_operated_packet"), Mapping)
        ):
            raise ProspectiveOperationError(
                "FORWARD_OPERATED_PACKET_MAPPING_REQUIRED"
            )
        stored_packet = request.get("forward_operated_packet")
        packet_source = stored_packet if isinstance(stored_packet, Mapping) else request
        requested_pit_identity = _normalize_pit_identity(request.get("pit_identity"))
        workspace_pit_identity = _normalize_pit_identity(
            workspace.get("pit_identity")
        )
        if requested_pit_identity != workspace_pit_identity:
            raise ProspectiveOperationError(
                "FORWARD_OPERATED_PIT_IDENTITY_WORKSPACE_MISMATCH"
            )
        pit_identity = workspace_pit_identity
        if pit_identity != _validated_forward_pit_identity():
            raise ProspectiveOperationError("FORWARD_OPERATED_PIT_IDENTITY_MISMATCH")
        instrument_id = _required_text(
            (
                packet_source.get("instrument_id")
                if isinstance(stored_packet, Mapping)
                else packet_source.get("market_instrument_id")
            ),
            field="market_instrument_id",
        )
        if instrument_id != update["instrument_id"]:
            raise ProspectiveOperationError("FORWARD_OPERATED_MARKET_INSTRUMENT_MISMATCH")
        market_observed_at = _required_text(
            packet_source.get("market_observed_at"), field="market_observed_at"
        )
        market_observed_time = _utc_datetime(
            market_observed_at, field="market_observed_at"
        )
        if market_observed_time <= latest_time:
            raise ProspectiveOperationError(
                "MARKET_OBSERVATION_TIMESTAMP_NOT_AFTER_AUTHORITY"
            )
        if market_observed_time > observed_time:
            raise ProspectiveOperationError("MARKET_OBSERVATION_AFTER_EVIDENCE_DECISION")
        if isinstance(stored_packet, Mapping):
            expected_packet_bindings = {
                "instrument_id": update["instrument_id"],
                "evidence_content": content,
                "source_locator": locator,
                "evidence_observed_at": _utc_timestamp(observed_time),
                "target_quantity": update["target_quantity"],
                "principal_claim": update["principal_claim"],
                "operator_rationale": operator_rationale,
                "pit_identity": pit_identity,
            }
            for field, expected_value in expected_packet_bindings.items():
                if stored_packet.get(field) != expected_value:
                    raise ProspectiveOperationError(
                        "FORWARD_OPERATED_PACKET_BINDING_MISMATCH"
                    )
        packet = ForwardOperatedDecisionPacket(
            instrument_id=instrument_id,
            evidence_content=content,
            source_locator=locator,
            evidence_observed_at=_utc_timestamp(observed_time),
            market_price=_positive_decimal_text(
                packet_source.get("market_price"), field="market_price"
            ),
            market_observed_at=_utc_timestamp(market_observed_time),
            market_source_identity=_required_text(
                packet_source.get("market_source_identity"),
                field="market_source_identity",
            ),
            target_quantity=update["target_quantity"],
            principal_claim=update["principal_claim"],
            operator_rationale=operator_rationale,
            pit_identity=pit_identity,
        )
        normalized["forward_operated_packet"] = {
            "instrument_id": packet.instrument_id,
            "evidence_content": packet.evidence_content,
            "source_locator": packet.source_locator,
            "evidence_observed_at": packet.evidence_observed_at,
            "market_price": packet.market_price,
            "market_observed_at": packet.market_observed_at,
            "market_source_identity": packet.market_source_identity,
            "target_quantity": packet.target_quantity,
            "principal_claim": packet.principal_claim,
            "operator_rationale": packet.operator_rationale,
            "pit_identity": deepcopy(packet.pit_identity),
        }
        normalized["pit_identity"] = deepcopy(pit_identity)
    return normalized


def _review_by_id(workspace: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["instrument_id"]: deepcopy(row) for row in workspace["reviews"]}


def _reconstruct_book_or_fail_closed(
    events: list[Mapping[str, Any]], *, code: str
) -> dict[str, Any]:
    try:
        return reconstruct_book(events)
    except (DecimalException, ExecutionError, ReplayError, ValueError) as exc:
        raise ProspectiveOperationError(f"{code}:{exc}") from exc


def _transition_preview(
    workspace: Mapping[str, Any],
    *,
    decision_snapshot: Mapping[str, Any],
    legs: list[dict[str, str]],
    observed_at: str,
    observation_id: str,
    transition_kind: str,
) -> dict[str, Any]:
    result = deepcopy(dict(workspace))
    result["current_decision_snapshot"] = deepcopy(dict(decision_snapshot))
    result["events"] = [
        *deepcopy(workspace["events"]),
        portfolio_book_event(
            len(workspace["events"]),
            "LATER_OBSERVATION_ADMITTED",
            observed_at,
            observation_id,
            payload={"preview_only": True},
        ),
    ]
    transition_at = _utc_timestamp(
        _utc_datetime(observed_at, field="observed_at") + timedelta(seconds=2)
    )
    transition = _append_transition_event(
        result,
        transition_kind=transition_kind,
        effective_at=transition_at,
        legs=legs,
    )
    anchor = _utc_datetime(observed_at, field="observed_at")
    for index, leg in enumerate(legs):
        created_at = _utc_timestamp(anchor + timedelta(seconds=3 + (index * 2)))
        filled_at = _utc_timestamp(anchor + timedelta(seconds=4 + (index * 2)))
        _append_trade(
            result,
            transition_event_id=transition["event_id"],
            instrument_id=leg["instrument_id"],
            side=leg["side"],
            quantity=leg["quantity"],
            price=leg["reference_price"],
            fee="2",
            order_created_at=created_at,
            filled_at=filled_at,
        )
    result["book"] = _reconstruct_book_or_fail_closed(
        result["events"], code="PROSPECTIVE_TRANSITION_REPLAY_FAILED"
    )
    if result["book"]["unexplained_residual"] != "0":
        raise ProspectiveOperationError("PROSPECTIVE_TRANSITION_RESIDUAL_NONZERO")
    if any(Decimal(row["amount"]) < 0 for row in result["book"]["classified_cash"]):
        raise ProspectiveOperationError("PROSPECTIVE_TRANSITION_NEGATIVE_CASH")
    return {
        "transition_kind": transition_kind,
        "legs": deepcopy(legs),
        "order_count": len(legs),
        "book_hash_after": result["book"]["book_hash"],
        "nav_after": result["book"]["nav"],
        "cash_after": result["book"]["total_cash"],
        "classified_cash_after": deepcopy(result["book"]["classified_cash"]),
        "positions_after": deepcopy(result["book"]["positions"]),
        "costs_after": result["book"]["total_costs"],
        "classified_costs_after": deepcopy(result["book"]["classified_costs"]),
        "unexplained_residual": result["book"]["unexplained_residual"],
    }


def _build_proposal(
    workspace: Mapping[str, Any], request: Mapping[str, Any]
) -> dict[str, Any]:
    normalized = _normalize_request(workspace, request)
    scenario = get_scenario(str(workspace["scenario_id"]))
    reviews_by_id = _review_by_id(workspace)
    before_reviews = deepcopy(workspace["reviews"])
    owned_ids = [row["instrument_id"] for row in normalized["review_updates"]]
    evidence = _evidence(
        scenario,
        content=normalized["content"],
        locator=normalized["locator"],
        observed_at=normalized["observed_at"],
        owned_instrument_ids=owned_ids,
    )

    review_changes: list[dict[str, Any]] = []
    for update in normalized["review_updates"]:
        before = reviews_by_id[update["instrument_id"]]
        prior_thesis = before["living_thesis_lite"]
        after = deepcopy(before)
        after["outcome"] = update["outcome"]
        after["net_score_bps"] = update["net_score_bps"]
        after["target_quantity"] = update["target_quantity"]
        forward_packet = normalized.get("forward_operated_packet")
        if (
            isinstance(forward_packet, Mapping)
            and forward_packet.get("instrument_id") == update["instrument_id"]
        ):
            after["reference_price"] = forward_packet["market_price"]
        after["living_thesis_lite"] = _thesis(
            scenario,
            instrument_id=update["instrument_id"],
            principal_claim=update["principal_claim"],
            evidence_reference_ids=[
                *prior_thesis["evidence_reference_ids"],
                evidence["evidence_reference_id"],
            ],
            hard_falsifiers=list(prior_thesis["hard_falsifiers"]),
            watch_conditions=list(prior_thesis["watch_conditions"]),
        )
        reviews_by_id[update["instrument_id"]] = after
        review_changes.append({"before": before, "after": after})

    ordered_reviews = [reviews_by_id[row["instrument_id"]] for row in workspace["reviews"]]
    decision_created_at = _utc_timestamp(
        _utc_datetime(normalized["observed_at"], field="observed_at")
        + timedelta(seconds=1)
    )
    decision_snapshot = _decision_snapshot(
        scenario,
        aim_id=workspace["portfolio_aim"]["portfolio_aim_id"],
        reviews=ordered_reviews,
        created_at=decision_created_at,
        reason="OPERATOR_PROPOSED_PROSPECTIVE_CAPITAL_DECISION",
    )
    legs = _transition_legs_from_reviews(
        workspace["instruments"], before_reviews, ordered_reviews
    )
    economics_changed = bool(legs)
    transition_kind = "PROSPECTIVE_REBALANCE"
    if economics_changed:
        sides = {row["side"] for row in legs}
        funded_positions = [
            row
            for row in workspace["book"]["positions"]
            if int(row["quantity"]) > 0
        ]
        cash_funded_entry = (
            scenario.get("forward_operated_market_packet") is True
            and not funded_positions
            and sides == {"BUY"}
        )
        if cash_funded_entry:
            packet = normalized.get("forward_operated_packet")
            if not isinstance(packet, Mapping):
                raise ProspectiveOperationError("FORWARD_OPERATED_PACKET_REQUIRED")
            if len(legs) != 1:
                raise ProspectiveOperationError("CASH_FUNDED_ENTRY_SINGLE_LEG_REQUIRED")
            leg = legs[0]
            if leg["instrument_id"] != packet.get("instrument_id"):
                raise ProspectiveOperationError("CASH_FUNDED_ENTRY_INSTRUMENT_MISMATCH")
            if leg["reference_price"] != packet.get("market_price"):
                raise ProspectiveOperationError("CASH_FUNDED_ENTRY_PRICE_MISMATCH")
            if int(leg["quantity"]) <= 0:
                raise ProspectiveOperationError("CASH_FUNDED_ENTRY_QUANTITY_REQUIRED")
            if "BUY" not in scenario["portfolio_aim"]["allowed_actions"]:
                raise ProspectiveOperationError("CASH_FUNDED_ENTRY_BUY_NOT_ALLOWED")
            transition_kind = "PROSPECTIVE_CASH_FUNDED_ENTRY"
        else:
            if "SELL" not in sides:
                raise ProspectiveOperationError("PROSPECTIVE_TRANSITION_SELL_REQUIRED")
            if "BUY" not in sides:
                raise ProspectiveOperationError("PROSPECTIVE_TRANSITION_BUY_REQUIRED")

    observation = _record(
        scenario,
        "OBS",
        "observation_id",
        {
            "evidence_reference_id": evidence["evidence_reference_id"],
            "disposition": (
                "PROPOSED_PROSPECTIVE_TRANSITION"
                if economics_changed
                else "PROPOSED_PROSPECTIVE_NO_CHANGE"
            ),
            "instrument_ids": sorted(owned_ids),
            "threshold_crossed": economics_changed,
            "observed_at": normalized["observed_at"],
            "decision_snapshot_id": decision_snapshot["decision_snapshot_id"],
            "operator_rationale": normalized["operator_rationale"],
        },
    )
    transition = (
        _transition_preview(
            workspace,
            decision_snapshot=decision_snapshot,
            legs=legs,
            observed_at=normalized["observed_at"],
            observation_id=observation["observation_id"],
            transition_kind=transition_kind,
        )
        if economics_changed
        else None
    )
    changed_why = {
        "change_type": (
            transition_kind
            if transition_kind == "PROSPECTIVE_CASH_FUNDED_ENTRY"
            else "PROSPECTIVE_TRANSITION"
            if economics_changed
            else "PROSPECTIVE_NO_CHANGE"
        ),
        "reason": normalized["operator_rationale"],
        "review_changes": [
            {
                "symbol": row["before"]["symbol"],
                "outcome_before": row["before"]["outcome"],
                "outcome_after": row["after"]["outcome"],
                "score_before_bps": int(row["before"]["net_score_bps"]),
                "score_after_bps": int(row["after"]["net_score_bps"]),
                "quantity_before": str(row["before"]["target_quantity"]),
                "quantity_after": str(row["after"]["target_quantity"]),
                "reference_price_before": str(row["before"]["reference_price"]),
                "reference_price_after": str(row["after"]["reference_price"]),
                "thesis_changed": canonical_document_bytes(
                    row["before"]["living_thesis_lite"]
                )
                != canonical_document_bytes(row["after"]["living_thesis_lite"]),
            }
            for row in review_changes
        ],
        "holdings_changed": economics_changed,
        "cash_changed": economics_changed,
        "orders_created": len(legs),
        "transition_legs": deepcopy(legs),
        "book_hash_before": workspace["book"]["book_hash"],
        "book_hash_after": (
            transition["book_hash_after"]
            if transition is not None
            else workspace["book"]["book_hash"]
        ),
    }
    body = {
        "schema_version": PROPOSAL_SCHEMA,
        "request": normalized,
        "evidence": evidence,
        "review_changes": review_changes,
        "decision_snapshot": decision_snapshot,
        "observation": observation,
        "changed_why": changed_why,
        "economics_changed": economics_changed,
        "transition": transition,
        "prior_decision_snapshot_id": workspace["current_decision_snapshot"][
            "decision_snapshot_id"
        ],
        "prior_certification_id": workspace["certification"]["certification_id"],
        "prior_book_hash": workspace["book"]["book_hash"],
        "prior_event_count": len(workspace["events"]),
    }
    return {
        "proposal_id": "PRP_"
        + domain_hash(f"{scenario['id_domain']}:PROSPECTIVE_PROPOSAL:V2", body),
        **body,
    }


def preview_runtime_observation(
    workspace: Mapping[str, Any], request: Mapping[str, Any]
) -> dict[str, Any]:
    """Return a deterministic proposal without mutating memory or persistence."""

    validate_prospective_workspace(workspace)
    before = canonical_document_bytes(dict(workspace))
    proposal = _build_proposal(workspace, request)
    if canonical_document_bytes(dict(workspace)) != before:
        raise ProspectiveOperationError("PREVIEW_MUTATED_WORKSPACE")
    return proposal


def _validate_event(event: Mapping[str, Any]) -> None:
    try:
        expected = portfolio_book_event(
            event["sequence"],
            event["event_type"],
            event["effective_at"],
            event["source_identity"],
            instrument_id=event.get("instrument_id"),
            cash_bucket=event.get("cash_bucket"),
            payload=event.get("payload") or {},
        )
    except (KeyError, ExecutionError) as exc:
        raise ProspectiveOperationError("PROSPECTIVE_EVENT_INVALID") from exc
    if canonical_document_bytes(expected) != canonical_document_bytes(dict(event)):
        raise ProspectiveOperationError("PROSPECTIVE_EVENT_ID_MISMATCH")


def _apply_proposal_projection(
    workspace: Mapping[str, Any], proposal: Mapping[str, Any]
) -> dict[str, Any]:
    result = deepcopy(dict(workspace))
    result["evidence_references"] = [
        *result["evidence_references"],
        deepcopy(proposal["evidence"]),
    ]
    after_by_id = {
        row["after"]["instrument_id"]: deepcopy(row["after"])
        for row in proposal["review_changes"]
    }
    result["reviews"] = [
        after_by_id.get(row["instrument_id"], deepcopy(row))
        for row in result["reviews"]
    ]
    result["decision_snapshots"] = [
        *result["decision_snapshots"],
        deepcopy(proposal["decision_snapshot"]),
    ]
    result["current_decision_snapshot"] = deepcopy(proposal["decision_snapshot"])
    result["observations"] = [
        *result["observations"],
        deepcopy(proposal["observation"]),
    ]
    result["changed_why"] = deepcopy(proposal["changed_why"])
    return result


def _episode_workspace(
    workspace: Mapping[str, Any], proposal: Mapping[str, Any]
) -> dict[str, Any]:
    result = _apply_proposal_projection(workspace, proposal)
    observation = proposal["observation"]
    try:
        observation_event = portfolio_book_event(
            len(workspace["events"]),
            "LATER_OBSERVATION_ADMITTED",
            observation["observed_at"],
            observation["observation_id"],
            instrument_id=(
                observation["instrument_ids"][0]
                if len(observation["instrument_ids"]) == 1
                else None
            ),
            payload={
                "schema_version": EPISODE_SCHEMA,
                "prospective_proposal": deepcopy(dict(proposal)),
            },
        )
    except ExecutionError as exc:
        raise ProspectiveOperationError(str(exc)) from exc
    result["events"] = [*deepcopy(workspace["events"]), observation_event]

    if proposal["economics_changed"]:
        legs = deepcopy(proposal["transition"]["legs"])
        anchor = _utc_datetime(observation["observed_at"], field="observed_at")
        transition = _append_transition_event(
            result,
            transition_kind=proposal["transition"]["transition_kind"],
            effective_at=_utc_timestamp(anchor + timedelta(seconds=2)),
            legs=legs,
        )
        for index, leg in enumerate(legs):
            _append_trade(
                result,
                transition_event_id=transition["event_id"],
                instrument_id=leg["instrument_id"],
                side=leg["side"],
                quantity=leg["quantity"],
                price=leg["reference_price"],
                fee="2",
                order_created_at=_utc_timestamp(
                    anchor + timedelta(seconds=3 + (index * 2))
                ),
                filled_at=_utc_timestamp(
                    anchor + timedelta(seconds=4 + (index * 2))
                ),
            )
        result["book"] = _reconstruct_book_or_fail_closed(
            result["events"], code="PROSPECTIVE_EPISODE_REPLAY_FAILED"
        )
        if result["book"]["book_hash"] != proposal["transition"]["book_hash_after"]:
            raise ProspectiveOperationError("TRANSITION_PREVIEW_BOOK_MISMATCH")
        result["changed_why"]["book_hash_after"] = result["book"]["book_hash"]
        result["changed_why"]["cash_after"] = result["book"]["total_cash"]
        result["changed_why"]["costs_after"] = result["book"]["total_costs"]
        result["changed_why"]["unexplained_residual"] = result["book"][
            "unexplained_residual"
        ]
    else:
        result["book"] = _reconstruct_book_or_fail_closed(
            result["events"], code="PROSPECTIVE_NO_CHANGE_REPLAY_FAILED"
        )
        if canonical_document_bytes(result["book"]) != canonical_document_bytes(
            workspace["book"]
        ):
            raise ProspectiveOperationError("PROSPECTIVE_NO_CHANGE_BOOK_DRIFT")

    try:
        certification = certify_replay_prefix(
            result["events"],
            decision_snapshot_id=result["current_decision_snapshot"][
                "decision_snapshot_id"
            ],
            portfolio_aim_id=result["portfolio_aim"]["portfolio_aim_id"],
            prior_certification=workspace["certification"],
        )
    except ReplayError as exc:
        raise ProspectiveOperationError(
            f"PROSPECTIVE_CERTIFICATION_FAILED:{exc}"
        ) from exc
    last_time = max(
        _utc_datetime(row["effective_at"], field="effective_at")
        for row in result["events"]
    )
    try:
        certification_event = portfolio_book_event(
            len(result["events"]),
            "CERTIFICATION_RECORDED",
            _utc_timestamp(last_time + timedelta(seconds=1)),
            certification["certification_id"],
            payload={"certification_id": certification["certification_id"]},
        )
    except ExecutionError as exc:
        raise ProspectiveOperationError(str(exc)) from exc
    result["events"].append(certification_event)
    result["book"] = _reconstruct_book_or_fail_closed(
        result["events"], code="PROSPECTIVE_CERTIFICATION_REPLAY_FAILED"
    )
    result["certification_history"] = [
        *result["certification_history"],
        deepcopy(workspace["certification"]),
    ]
    result["certification"] = certification
    return result


def _rejected_episode_workspace(
    workspace: Mapping[str, Any],
    proposal: Mapping[str, Any],
    rejection_reason: str,
) -> dict[str, Any]:
    """Append a rejected proposal without granting evidence, review, or capital authority."""

    reason = _required_text(rejection_reason, field="rejection_reason")
    result = deepcopy(dict(workspace))
    observed_at = proposal["request"]["observed_at"]
    rejection_record = {
        "proposal_id": proposal["proposal_id"],
        "rejection_reason": reason,
        "rejected_at": observed_at,
        "prospective_proposal": deepcopy(dict(proposal)),
    }
    try:
        rejection_event = portfolio_book_event(
            len(workspace["events"]),
            "PROSPECTIVE_PROPOSAL_REJECTED",
            observed_at,
            proposal["proposal_id"],
            payload={
                "schema_version": REJECTED_EPISODE_SCHEMA,
                **deepcopy(rejection_record),
            },
        )
    except ExecutionError as exc:
        raise ProspectiveOperationError(str(exc)) from exc
    result["events"] = [*deepcopy(workspace["events"]), rejection_event]
    result["book"] = _reconstruct_book_or_fail_closed(
        result["events"], code="PROSPECTIVE_REJECTION_REPLAY_FAILED"
    )
    if canonical_document_bytes(result["book"]) != canonical_document_bytes(
        workspace["book"]
    ):
        raise ProspectiveOperationError("REJECTED_PROPOSAL_CHANGED_BOOK")
    try:
        certification = certify_replay_prefix(
            result["events"],
            decision_snapshot_id=workspace["current_decision_snapshot"][
                "decision_snapshot_id"
            ],
            portfolio_aim_id=workspace["portfolio_aim"]["portfolio_aim_id"],
            prior_certification=workspace["certification"],
        )
    except ReplayError as exc:
        raise ProspectiveOperationError(
            f"PROSPECTIVE_REJECTION_CERTIFICATION_FAILED:{exc}"
        ) from exc
    try:
        certification_event = portfolio_book_event(
            len(result["events"]),
            "CERTIFICATION_RECORDED",
            _utc_timestamp(
                _utc_datetime(observed_at, field="observed_at")
                + timedelta(seconds=1)
            ),
            certification["certification_id"],
            payload={"certification_id": certification["certification_id"]},
        )
    except ExecutionError as exc:
        raise ProspectiveOperationError(str(exc)) from exc
    result["events"].append(certification_event)
    result["book"] = _reconstruct_book_or_fail_closed(
        result["events"], code="PROSPECTIVE_REJECTION_CERTIFICATION_REPLAY_FAILED"
    )
    result["certification_history"] = [
        *result["certification_history"],
        deepcopy(workspace["certification"]),
    ]
    result["certification"] = certification
    return result


def _reconstruct_prospective_workspace(
    events: list[Mapping[str, Any]],
    *,
    scenario_id: str = PROSPECTIVE_25_SCENARIO_ID,
) -> dict[str, Any]:
    """Project full decision and economic state from the append-only event log."""

    baseline = _baseline_workspace(scenario_id)
    baseline_hash = domain_hash("GV-PROSPECTIVE-PAPER:BASELINE:V1", baseline)
    if not isinstance(events, list):
        raise ProspectiveOperationError("PROSPECTIVE_EVENTS_REQUIRED")
    if len(events) > MAX_PROSPECTIVE_EVENT_COUNT:
        raise ProspectiveOperationError("PROSPECTIVE_EVENT_LIMIT_EXCEEDED")
    try:
        rows: list[dict[str, Any]] = []
        for row in events:
            if not isinstance(row, Mapping):
                raise ProspectiveOperationError("PROSPECTIVE_EVENT_MAPPING_REQUIRED")
            rows.append(deepcopy(dict(row)))
    except ProspectiveOperationError:
        raise
    except Exception as exc:
        raise ProspectiveOperationError("PROSPECTIVE_EVENT_INVALID") from exc
    baseline_count = len(baseline["events"])
    if len(rows) < baseline_count:
        raise ProspectiveOperationError("BASELINE_EVENT_PREFIX_MISSING")
    if canonical_document_bytes(rows[:baseline_count]) != canonical_document_bytes(
        baseline["events"]
    ):
        raise ProspectiveOperationError("BASELINE_EVENT_PREFIX_MISMATCH")

    result = deepcopy(baseline)
    proposals: list[dict[str, Any]] = []
    rejected_proposals: list[dict[str, Any]] = []
    episode_history: list[dict[str, Any]] = []
    cursor = baseline_count
    while cursor < len(rows):
        if len(episode_history) >= MAX_PROSPECTIVE_EPISODE_COUNT:
            raise ProspectiveOperationError("PROSPECTIVE_EPISODE_LIMIT_EXCEEDED")
        episode_event = rows[cursor]
        _validate_event(episode_event)
        payload = episode_event.get("payload") or {}

        if episode_event["event_type"] == "LATER_OBSERVATION_ADMITTED":
            if payload.get("schema_version") != EPISODE_SCHEMA:
                raise ProspectiveOperationError("PROSPECTIVE_EPISODE_SCHEMA_INVALID")
            stored = payload.get("prospective_proposal")
            if not isinstance(stored, Mapping):
                raise ProspectiveOperationError("PROSPECTIVE_PROPOSAL_REQUIRED")
            expected_proposal = _build_proposal(result, stored.get("request") or {})
            if canonical_document_bytes(dict(stored)) != canonical_document_bytes(
                expected_proposal
            ):
                raise ProspectiveOperationError(
                    "PROSPECTIVE_PROPOSAL_PROJECTION_MISMATCH"
                )
            expected_workspace = _episode_workspace(result, expected_proposal)
            disposition = "CONFIRMED"
            proposals.append(deepcopy(expected_proposal))
            episode_history.append(
                {
                    "disposition": disposition,
                    "proposal_id": expected_proposal["proposal_id"],
                    "observed_at": expected_proposal["request"]["observed_at"],
                    "economics_changed": expected_proposal["economics_changed"],
                }
            )
        elif episode_event["event_type"] == "PROSPECTIVE_PROPOSAL_REJECTED":
            if payload.get("schema_version") != REJECTED_EPISODE_SCHEMA:
                raise ProspectiveOperationError(
                    "PROSPECTIVE_REJECTED_EPISODE_SCHEMA_INVALID"
                )
            stored = payload.get("prospective_proposal")
            if not isinstance(stored, Mapping):
                raise ProspectiveOperationError("PROSPECTIVE_PROPOSAL_REQUIRED")
            expected_proposal = _build_proposal(result, stored.get("request") or {})
            if canonical_document_bytes(dict(stored)) != canonical_document_bytes(
                expected_proposal
            ):
                raise ProspectiveOperationError(
                    "PROSPECTIVE_PROPOSAL_PROJECTION_MISMATCH"
                )
            rejection_reason = _required_text(
                payload.get("rejection_reason"), field="rejection_reason"
            )
            expected_workspace = _rejected_episode_workspace(
                result, expected_proposal, rejection_reason
            )
            rejection_record = {
                "proposal_id": expected_proposal["proposal_id"],
                "rejection_reason": rejection_reason,
                "rejected_at": expected_proposal["request"]["observed_at"],
                "prospective_proposal": deepcopy(expected_proposal),
            }
            rejected_proposals.append(rejection_record)
            episode_history.append(
                {
                    "disposition": "REJECTED",
                    "proposal_id": expected_proposal["proposal_id"],
                    "observed_at": expected_proposal["request"]["observed_at"],
                    "economics_changed": False,
                    "rejection_reason": rejection_reason,
                }
            )
        else:
            raise ProspectiveOperationError("PROSPECTIVE_EPISODE_EVENT_REQUIRED")

        expected_tail = expected_workspace["events"][len(result["events"]):]
        actual_tail = rows[cursor : cursor + len(expected_tail)]
        if len(actual_tail) != len(expected_tail):
            raise ProspectiveOperationError("PROSPECTIVE_EPISODE_EVENT_TAIL_MISSING")
        for row in actual_tail:
            _validate_event(row)
        if canonical_document_bytes(actual_tail) != canonical_document_bytes(
            expected_tail
        ):
            raise ProspectiveOperationError("PROSPECTIVE_EPISODE_EVENT_TAIL_MISMATCH")
        expected_workspace["events"] = rows[: cursor + len(expected_tail)]
        result = expected_workspace
        cursor += len(expected_tail)

    try:
        reconstructed = reconstruct_exact(rows, expected_book=result["book"])
        replayed = replay_idempotent(rows)
    except ReplayError as exc:
        raise ProspectiveOperationError(f"PROSPECTIVE_REPLAY_FAILED:{exc}") from exc
    if reconstructed["book_hash"] != result["book"]["book_hash"]:
        raise ProspectiveOperationError("PROSPECTIVE_BOOK_RECONSTRUCTION_MISMATCH")
    if replayed["book_hash"] != result["book"]["book_hash"]:
        raise ProspectiveOperationError("PROSPECTIVE_BOOK_IDEMPOTENCE_MISMATCH")
    return _decorate(
        result,
        baseline_hash=baseline_hash,
        baseline_event_count=baseline_count,
        proposals=proposals,
        rejected_proposals=rejected_proposals,
        episode_history=episode_history,
    )


def reconstruct_prospective_workspace(
    events: list[Mapping[str, Any]],
    *,
    scenario_id: str = PROSPECTIVE_25_SCENARIO_ID,
) -> dict[str, Any]:
    """Project an event log and convert malformed input to a closed error."""

    try:
        return _reconstruct_prospective_workspace(events, scenario_id=scenario_id)
    except ProspectiveOperationError:
        raise
    except Exception as exc:
        raise ProspectiveOperationError("PROSPECTIVE_RECONSTRUCTION_FAILED") from exc


def validate_prospective_workspace(workspace: Mapping[str, Any]) -> None:
    scenario_id = workspace.get("scenario_id")
    if not isinstance(scenario_id, str):
        raise ProspectiveOperationError("PROSPECTIVE_SCENARIO_REQUIRED")
    try:
        scenario = get_scenario(scenario_id)
    except ValueError as exc:
        raise ProspectiveOperationError("PROSPECTIVE_SCENARIO_REQUIRED") from exc
    if scenario.get("runtime_observation_mode") is not True:
        raise ProspectiveOperationError("PROSPECTIVE_RUNTIME_MODE_REQUIRED")
    if workspace.get("operation_schema_version") != PROSPECTIVE_SCHEMA:
        raise ProspectiveOperationError("PROSPECTIVE_SCHEMA_INVALID")
    events = workspace.get("events")
    if not isinstance(events, list):
        raise ProspectiveOperationError("PROSPECTIVE_EVENTS_REQUIRED")
    projected = reconstruct_prospective_workspace(events, scenario_id=scenario_id)
    if canonical_document_bytes(dict(workspace)) != canonical_document_bytes(projected):
        raise ProspectiveOperationError("PROSPECTIVE_WORKSPACE_PROJECTION_MISMATCH")


def confirm_runtime_observation(
    workspace: Mapping[str, Any], proposal: Mapping[str, Any]
) -> dict[str, Any]:
    """Append one confirmed episode and its replay certification."""

    validate_prospective_workspace(workspace)
    if not isinstance(proposal, Mapping):
        raise ProspectiveOperationError("PROSPECTIVE_PROPOSAL_MAPPING_REQUIRED")
    expected = _build_proposal(workspace, proposal.get("request") or {})
    if canonical_document_bytes(dict(proposal)) != canonical_document_bytes(expected):
        raise ProspectiveOperationError("STALE_OR_MUTATED_PROPOSAL")
    episode = _episode_workspace(workspace, expected)
    result = reconstruct_prospective_workspace(
        episode["events"], scenario_id=str(workspace["scenario_id"])
    )
    validate_prospective_workspace(result)
    return result


def reject_runtime_observation(
    workspace: Mapping[str, Any],
    proposal: Mapping[str, Any],
    rejection_reason: str,
) -> dict[str, Any]:
    """Append a certified rejection while preserving all current decision authority."""

    validate_prospective_workspace(workspace)
    if not isinstance(proposal, Mapping):
        raise ProspectiveOperationError("PROSPECTIVE_PROPOSAL_MAPPING_REQUIRED")
    expected = _build_proposal(workspace, proposal.get("request") or {})
    if canonical_document_bytes(dict(proposal)) != canonical_document_bytes(expected):
        raise ProspectiveOperationError("STALE_OR_MUTATED_PROPOSAL")
    episode = _rejected_episode_workspace(workspace, expected, rejection_reason)
    result = reconstruct_prospective_workspace(
        episode["events"], scenario_id=str(workspace["scenario_id"])
    )
    validate_prospective_workspace(result)
    return result
