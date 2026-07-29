"""Deterministic replay and fail-closed certification for GV Portfolio V0.

This module is intentionally separate from the Slice 0 product reducer. It
rebuilds book, execution, decision, and certification projections from the
persisted immutable records without provider, broker, network, or live-capital
work. Terminal replay certification is gated by an exact independent Slice 0
audit receipt; local shadow evidence never self-authorizes that gate.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Iterable, Mapping, Sequence

from contracts.gv_portfolio.v0 import (
    CustodyContractError,
    identifier as custody_identifier,
    verify_record_id,
)
from core.gv_fs0_canonical import (
    CanonicalizationError,
    assert_sha256,
    canonical_document_bytes,
    canonical_timestamp,
    domain_hash,
    sha256_bytes,
)
from core.gv_portfolio_v0 import (
    CustodyEventError,
    portfolio_book_event,
    verify_portfolio_book_event,
)
from gv_portfolio_v0.vertical import (
    DECLARED_PRECISION,
    ID_DOMAIN,
    SCHEMA_VERSION,
    PortfolioV0Error,
    certify_workspace,
    reduce_events,
)

REPLAY_INPUT_SCHEMA = "gv_portfolio_v0_replay_input_v1"
REPLAY_EVIDENCE_SCHEMA = "gv_portfolio_v0_replay_evidence_v1"
REPLAY_CERTIFICATION_SCHEMA = "gv_portfolio_v0_replay_certification_v1"
AUDIT_RECEIPT_SCHEMA = "gv_portfolio_v0_slice0_audit_receipt_v2"
EXTERNAL_REVIEW_RECEIPT_SCHEMA = "gv_portfolio_v0_external_review_receipt_v2"
REVIEW_REPORT_SCHEMA = "gv_portfolio_v0_slice0_reviewer_report_v1"
REPLAY_DOMAIN = "GV-PORTFOLIO-V0:REPLAY"
REVIEW_DOMAINS = ("A", "B", "C")
GITHUB_PROVIDER = "GITHUB"
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_GITHUB_LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")




class ReplayV0Error(PortfolioV0Error):
    """Fail-closed replay or replay-certification error."""


def _decimal(value: str | int | Decimal) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ReplayV0Error(f"DECIMAL_INVALID:{value}") from exc
    if not parsed.is_finite():
        raise ReplayV0Error("DECIMAL_FINITE_REQUIRED")
    return parsed


def _decimal_text(value: str | int | Decimal) -> str:
    parsed = _decimal(value)
    if parsed == 0:
        return "0"
    text = format(parsed.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _portfolio_identifier(kind: str, payload: Mapping[str, Any]) -> str:
    return custody_identifier(kind, payload)


def _replay_identifier(kind: str, payload: Mapping[str, Any]) -> str:
    return f"{kind}_" + domain_hash(f"{REPLAY_DOMAIN}:{kind}:V1", dict(payload))


def _verify_record_id(
    record: Mapping[str, Any], *, kind: str, id_key: str
) -> None:
    try:
        verify_record_id(record, kind=kind, id_key=id_key)
    except CustodyContractError as exc:
        raise ReplayV0Error(str(exc)) from exc


def _verify_event(event: Mapping[str, Any]) -> dict[str, Any]:
    row = deepcopy(dict(event))
    try:
        verify_portfolio_book_event(row)
    except (CustodyContractError, CustodyEventError) as exc:
        raise ReplayV0Error(str(exc)) from exc
    return row


def event_with_updates(
    event: Mapping[str, Any],
    *,
    payload_updates: Mapping[str, Any] | None = None,
    **field_updates: Any,
) -> dict[str, Any]:
    """Return a new content-addressed event without mutating the source event."""

    source = _verify_event(event)
    body = {key: deepcopy(value) for key, value in source.items() if key != "event_id"}
    if payload_updates:
        body["payload"] = {**body["payload"], **deepcopy(dict(payload_updates))}
    for key, value in field_updates.items():
        if key not in body:
            raise ReplayV0Error(f"EVENT_UPDATE_FIELD_INVALID:{key}")
        body[key] = deepcopy(value)
    try:
        return portfolio_book_event(
            body["sequence"],
            body["event_type"],
            body["effective_at"],
            body["source_identity"],
            instrument_id=body["instrument_id"],
            cash_bucket=body["cash_bucket"],
            payload=body["payload"],
        )
    except (CustodyContractError, CustodyEventError) as exc:
        raise ReplayV0Error(str(exc)) from exc


def build_event_correction(
    *,
    target_event: Mapping[str, Any],
    replacement_event: Mapping[str, Any],
    reason: str,
    recorded_at: str,
) -> dict[str, Any]:
    """Build one immutable correction overlay for an existing event sequence slot."""

    target = _verify_event(target_event)
    replacement = _verify_event(replacement_event)
    if replacement["sequence"] != target["sequence"]:
        raise ReplayV0Error("CORRECTION_SEQUENCE_MISMATCH")
    if replacement["event_id"] == target["event_id"]:
        raise ReplayV0Error("CORRECTION_REPLACEMENT_UNCHANGED")
    payload = {
        "target_event_id": target["event_id"],
        "target_event_sha256": sha256_bytes(canonical_document_bytes(target)),
        "replacement_event": replacement,
        "reason": reason,
        "recorded_at": recorded_at,
    }
    return {"correction_id": _replay_identifier("COR", payload), **payload}


def _deduplicate_events(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, bytes] = {}
    unique: list[dict[str, Any]] = []
    for event in events:
        row = _verify_event(event)
        raw = canonical_document_bytes(row)
        event_id = row["event_id"]
        if event_id in by_id:
            if by_id[event_id] != raw:
                raise ReplayV0Error("DUPLICATE_EVENT_CONFLICT")
            continue
        by_id[event_id] = raw
        unique.append(row)
    unique.sort(key=lambda row: (row["sequence"], row["event_id"]))
    sequences = [row["sequence"] for row in unique]
    if not sequences or sequences != list(range(len(unique))):
        raise ReplayV0Error("EVENT_SEQUENCE_NOT_CONTIGUOUS")
    return unique


def normalize_event_stream(
    events: Iterable[Mapping[str, Any]],
    *,
    corrections: Sequence[Mapping[str, Any]] = (),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Deduplicate exact delivery retries and apply explicit correction overlays."""

    normalized = _deduplicate_events(events)
    index_by_id = {row["event_id"]: index for index, row in enumerate(normalized)}
    corrected_targets: set[str] = set()
    lineage: list[dict[str, Any]] = []

    prepared_corrections = sorted(
        (deepcopy(dict(item)) for item in corrections),
        key=lambda item: item.get("correction_id", ""),
    )
    for correction in prepared_corrections:
        correction_id = correction.get("correction_id")
        body = {key: value for key, value in correction.items() if key != "correction_id"}
        if correction_id != _replay_identifier("COR", body):
            raise ReplayV0Error("CORRECTION_ID_MISMATCH")
        target_id = correction.get("target_event_id")
        if target_id not in index_by_id:
            raise ReplayV0Error("CORRECTION_TARGET_MISSING")
        if target_id in corrected_targets:
            raise ReplayV0Error("MULTIPLE_CORRECTIONS_PER_TARGET_PROHIBITED")
        target_index = index_by_id[target_id]
        target = normalized[target_index]
        if correction.get("target_event_sha256") != sha256_bytes(
            canonical_document_bytes(target)
        ):
            raise ReplayV0Error("CORRECTION_TARGET_HASH_MISMATCH")
        replacement = _verify_event(correction.get("replacement_event") or {})
        if replacement["sequence"] != target["sequence"]:
            raise ReplayV0Error("CORRECTION_SEQUENCE_MISMATCH")
        if replacement["event_id"] in index_by_id and replacement["event_id"] != target_id:
            raise ReplayV0Error("CORRECTION_REPLACEMENT_ID_COLLISION")
        normalized[target_index] = replacement
        corrected_targets.add(target_id)
        lineage.append(
            {
                "correction_id": correction_id,
                "target_event_id": target_id,
                "replacement_event_id": replacement["event_id"],
                "sequence": replacement["sequence"],
                "reason": correction["reason"],
                "recorded_at": correction["recorded_at"],
            }
        )

    normalized.sort(key=lambda row: (row["sequence"], row["event_id"]))
    sequences = [row["sequence"] for row in normalized]
    if sequences != list(range(len(normalized))):
        raise ReplayV0Error("CORRECTED_EVENT_SEQUENCE_INVALID")
    event_ids = [row["event_id"] for row in normalized]
    if len(event_ids) != len(set(event_ids)):
        raise ReplayV0Error("CORRECTED_EVENT_ID_DUPLICATE")
    return normalized, lineage


def _subject_events(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        deepcopy(dict(row))
        for row in events
        if row.get("event_type") != "CERTIFICATION_RECORDED"
    ]


def _reconstruct_execution(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    orders: dict[str, dict[str, Any]] = {}
    fills_by_order: dict[str, list[dict[str, Any]]] = {}

    for event in events:
        event_type = event["event_type"]
        payload = event["payload"]
        if event_type == "ORDER_CREATED":
            order = deepcopy(dict(payload.get("order") or {}))
            _verify_record_id(order, kind="ORD", id_key="order_id")
            order_id = order["order_id"]
            if order_id in orders:
                raise ReplayV0Error("DUPLICATE_ORDER_ID")
            orders[order_id] = order
        elif event_type == "FILL_COMPLETED":
            fill = deepcopy(dict(payload.get("fill") or {}))
            _verify_record_id(fill, kind="FIL", id_key="fill_id")
            fills_by_order.setdefault(fill["order_id"], []).append(fill)

    for order_id in fills_by_order:
        if order_id not in orders:
            raise ReplayV0Error("ORPHAN_FILL")

    order_states: list[dict[str, Any]] = []
    total_gross_notional = Decimal("0")
    total_fees = Decimal("0")
    for order_id, order in sorted(orders.items()):
        order_quantity = _decimal(order["quantity"])
        fills = sorted(fills_by_order.get(order_id, []), key=lambda row: row["fill_id"])
        filled_quantity = Decimal("0")
        gross_notional = Decimal("0")
        fees = Decimal("0")
        fill_ids: list[str] = []
        for fill in fills:
            if fill["instrument_id"] != order["instrument_id"]:
                raise ReplayV0Error("FILL_INSTRUMENT_MISMATCH")
            if fill["side"] != order["side"]:
                raise ReplayV0Error("FILL_SIDE_MISMATCH")
            quantity = _decimal(fill["quantity"])
            if quantity <= 0:
                raise ReplayV0Error("FILL_QUANTITY_POSITIVE_REQUIRED")
            price = _decimal(fill["price"])
            fee = _decimal(fill["fee"])
            if price < 0 or fee < 0:
                raise ReplayV0Error("FILL_COST_NONNEGATIVE_REQUIRED")
            filled_quantity += quantity
            gross_notional += quantity * price
            fees += fee
            fill_ids.append(fill["fill_id"])
        remaining = order_quantity - filled_quantity
        if remaining < 0:
            raise ReplayV0Error("ORDER_OVERFILLED")
        status = "OPEN" if filled_quantity == 0 else "FILLED" if remaining == 0 else "PARTIAL"
        order_states.append(
            {
                "order_id": order_id,
                "decision_snapshot_id": order["decision_snapshot_id"],
                "portfolio_aim_id": order["portfolio_aim_id"],
                "instrument_id": order["instrument_id"],
                "side": order["side"],
                "ordered_quantity": _decimal_text(order_quantity),
                "filled_quantity": _decimal_text(filled_quantity),
                "remaining_quantity": _decimal_text(remaining),
                "gross_notional": _decimal_text(gross_notional),
                "fees": _decimal_text(fees),
                "cash_cost": _decimal_text(gross_notional + fees),
                "status": status,
                "fill_ids": fill_ids,
            }
        )
        total_gross_notional += gross_notional
        total_fees += fees

    execution = {
        "orders": order_states,
        "order_count": len(order_states),
        "fill_count": sum(len(rows) for rows in fills_by_order.values()),
        "gross_notional": _decimal_text(total_gross_notional),
        "fees": _decimal_text(total_fees),
        "cash_cost": _decimal_text(total_gross_notional + total_fees),
    }
    execution["execution_hash"] = domain_hash(
        f"{REPLAY_DOMAIN}:EXECUTION:V1", execution
    )
    return execution


def _reconstruct_decision(
    workspace: Mapping[str, Any], events: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    aim = deepcopy(dict(workspace.get("portfolio_aim") or {}))
    snapshot = deepcopy(dict(workspace.get("decision_snapshot") or {}))
    _verify_record_id(aim, kind="AIM", id_key="portfolio_aim_id")
    _verify_record_id(snapshot, kind="DSN", id_key="decision_snapshot_id")

    aim_id = aim["portfolio_aim_id"]
    snapshot_id = snapshot["decision_snapshot_id"]
    if snapshot.get("portfolio_aim_id") != aim_id:
        raise ReplayV0Error("SNAPSHOT_AIM_REFERENCE_MISMATCH")

    thesis_states: list[dict[str, Any]] = []
    for review in snapshot.get("reviews") or []:
        thesis = review.get("living_thesis_lite") or {}
        thesis_states.append(
            {
                "instrument_id": review["instrument_id"],
                "relationship": review["relationship"],
                "outcome": review["outcome"],
                "principal_claim": thesis["principal_claim"],
                "scenario_range": deepcopy(dict(thesis["scenario_range"])),
                "evidence_reference_ids": list(thesis["evidence_reference_ids"]),
                "hard_falsifiers": list(thesis["hard_falsifiers"]),
                "watch_conditions": list(thesis["watch_conditions"]),
                "state": thesis["state"],
            }
        )
    thesis_states.sort(key=lambda row: row["instrument_id"])

    aim_confirmed = False
    later_observations: list[dict[str, Any]] = []
    for event in events:
        if event["event_type"] == "PORTFOLIO_AIM_CONFIRMED":
            if event["payload"].get("portfolio_aim_id") != aim_id:
                raise ReplayV0Error("AIM_CONFIRMATION_REFERENCE_MISMATCH")
            aim_confirmed = True
        elif event["event_type"] == "ORDER_CREATED":
            order = event["payload"].get("order") or {}
            if order.get("decision_snapshot_id") != snapshot_id:
                raise ReplayV0Error("ORDER_SNAPSHOT_REFERENCE_MISMATCH")
            if order.get("portfolio_aim_id") != aim_id:
                raise ReplayV0Error("ORDER_AIM_REFERENCE_MISMATCH")
        elif event["event_type"] == "LATER_OBSERVATION_ADMITTED":
            payload = event["payload"]
            before = payload.get("portfolio_aim_id_before")
            after = payload.get("portfolio_aim_id_after")
            later_observations.append(
                {
                    "event_id": event["event_id"],
                    "evidence_reference_id": payload["evidence_reference_id"],
                    "classification": payload["classification"],
                    "hard_falsifier_fired": bool(payload["hard_falsifier_fired"]),
                    "portfolio_aim_id_before": before,
                    "portfolio_aim_id_after": after,
                    "aim_changed": before != after,
                }
            )

    decision = {
        "portfolio_aim_id": aim_id,
        "decision_snapshot_id": snapshot_id,
        "aim_confirmed": aim_confirmed,
        "selected_action": snapshot["selected_action"],
        "selected_instrument_id": snapshot["selected_instrument_id"],
        "selected_quantity": snapshot["selected_quantity"],
        "thesis_states": thesis_states,
        "later_observations": later_observations,
    }
    decision["decision_state_hash"] = domain_hash(
        f"{REPLAY_DOMAIN}:DECISION:V1", decision
    )
    return decision


def _replay_product_certification_chain(
    workspace: Mapping[str, Any], events: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    records = [
        *[deepcopy(dict(row)) for row in workspace.get("certification_history") or []],
        *(
            [deepcopy(dict(workspace["certification"]))]
            if isinstance(workspace.get("certification"), Mapping)
            else []
        ),
    ]
    by_id = {row["certification_id"]: row for row in records}
    if len(by_id) != len(records):
        raise ReplayV0Error("CERTIFICATION_HISTORY_ID_DUPLICATE")

    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, event in enumerate(events):
        if event["event_type"] != "CERTIFICATION_RECORDED":
            continue
        certification_id = event["payload"].get("certification_id")
        record = by_id.get(certification_id)
        if record is None:
            raise ReplayV0Error("CERTIFICATION_RECORD_MISSING")
        prefix_workspace = deepcopy(dict(workspace))
        prefix_workspace["events"] = [deepcopy(dict(row)) for row in events[:index]]
        expected = certify_workspace(
            prefix_workspace,
            prior_certification_id=record.get("prior_certification_id"),
        )
        byte_stable = canonical_document_bytes(expected) == canonical_document_bytes(record)
        if not byte_stable:
            raise ReplayV0Error("PRIOR_CERTIFICATION_BYTE_DRIFT")
        chain.append(
            {
                "sequence": event["sequence"],
                "certification_id": certification_id,
                "subject_event_ledger_hash": record["subject_event_ledger_hash"],
                "terminal_book_hash": record["terminal_book_hash"],
                "prior_certification_id": record.get("prior_certification_id"),
                "byte_stable": True,
            }
        )
        seen.add(certification_id)
    if seen != set(by_id):
        raise ReplayV0Error("CERTIFICATION_HISTORY_LEDGER_MISMATCH")
    return chain


def replay_workspace(
    workspace: Mapping[str, Any],
    *,
    corrections: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Reconstruct deterministic state from one persisted Slice 0 workspace."""

    if workspace.get("schema_version") != SCHEMA_VERSION:
        raise ReplayV0Error("WORKSPACE_SCHEMA_INVALID")
    normalized_events, correction_lineage = normalize_event_stream(
        workspace.get("events") or [], corrections=corrections
    )
    subject_events = _subject_events(normalized_events)
    book = reduce_events(normalized_events)
    execution = _reconstruct_execution(normalized_events)
    decision = _reconstruct_decision(workspace, normalized_events)
    certification_chain = (
        []
        if correction_lineage
        else _replay_product_certification_chain(workspace, normalized_events)
    )
    replay = {
        "schema_version": REPLAY_INPUT_SCHEMA,
        "fixture_id": workspace.get("fixture_id"),
        "source_event_ledger_hash": domain_hash(
            f"{ID_DOMAIN}:EVENT_LEDGER:V1", subject_events
        ),
        "normalized_event_stream_hash": domain_hash(
            f"{REPLAY_DOMAIN}:NORMALIZED_EVENTS:V1", normalized_events
        ),
        "event_count": len(normalized_events),
        "correction_lineage": correction_lineage,
        "book": book,
        "execution": execution,
        "decision": decision,
        "product_certification_status": (
            "INVALIDATED_BY_CORRECTION"
            if correction_lineage
            else "BYTE_STABLE"
        ),
        "product_certification_chain": certification_chain,
    }
    replay["replay_state_hash"] = domain_hash(
        f"{REPLAY_DOMAIN}:STATE:V1", replay
    )
    return replay


def _fill_correction_fixture(
    workspace: Mapping[str, Any],
    *,
    quantity: str,
    fee: str,
    reason: str,
) -> dict[str, Any]:
    fill_event = next(
        (
            event
            for event in workspace.get("events") or []
            if event.get("event_type") == "FILL_COMPLETED"
        ),
        None,
    )
    if fill_event is None:
        raise ReplayV0Error("FILL_EVENT_REQUIRED_FOR_FIXTURE")
    source_fill = deepcopy(dict(fill_event["payload"].get("fill") or {}))
    _verify_record_id(source_fill, kind="FIL", id_key="fill_id")
    fill_payload = {
        key: value for key, value in source_fill.items() if key != "fill_id"
    }
    fill_payload["quantity"] = quantity
    fill_payload["fee"] = fee
    replacement_fill = {
        "fill_id": _portfolio_identifier("FIL", fill_payload),
        **fill_payload,
    }
    replacement_event = event_with_updates(
        fill_event,
        payload_updates={"fill": replacement_fill},
        source_identity=replacement_fill["fill_id"],
    )
    return build_event_correction(
        target_event=fill_event,
        replacement_event=replacement_event,
        reason=reason,
        recorded_at="2026-07-22T00:00:00.000000Z",
    )


def build_replay_fixture_matrix(workspace: Mapping[str, Any]) -> dict[str, Any]:
    """Exercise the bounded adversarial fixtures included in Stream 6."""

    baseline = replay_workspace(workspace)

    source_events = list(workspace.get("events") or [])
    if len(source_events) < 3:
        raise ReplayV0Error("FIXTURE_EVENT_STREAM_INCOMPLETE")
    duplicate_delivery = deepcopy(dict(workspace))
    duplicate_delivery["events"] = [
        *[deepcopy(dict(row)) for row in source_events],
        deepcopy(dict(source_events[2])),
    ]
    duplicate = replay_workspace(duplicate_delivery)

    partial = replay_workspace(
        workspace,
        corrections=[
            _fill_correction_fixture(
                workspace,
                quantity="2",
                fee="1",
                reason="Exercise deterministic partial-fill residual state.",
            )
        ],
    )
    corrected = replay_workspace(
        workspace,
        corrections=[
            _fill_correction_fixture(
                workspace,
                quantity="3",
                fee="2",
                reason="Exercise explicit fee and quantity correction lineage.",
            )
        ],
    )

    opening = next(
        (
            event
            for event in workspace.get("events") or []
            if event.get("event_type") == "POSITION_OPENING"
        ),
        None,
    )
    if opening is None:
        raise ReplayV0Error("POSITION_OPENING_REQUIRED_FOR_FIXTURE")
    pending_event = event_with_updates(
        opening,
        sequence=0,
        payload_updates={"valuation_price": None},
    )
    pending_workspace = deepcopy(dict(workspace))
    pending_workspace["events"] = [pending_event]
    pending_workspace["certification"] = None
    pending_workspace["certification_history"] = []
    pending = replay_workspace(pending_workspace)

    partial_order = partial["execution"]["orders"][0]
    corrected_order = corrected["execution"]["orders"][0]
    checks = {
        "duplicate_delivery_idempotent": canonical_document_bytes(duplicate)
        == canonical_document_bytes(baseline),
        "partial_fill_residual_exact": partial_order["status"] == "PARTIAL"
        and partial_order["filled_quantity"] == "2"
        and partial_order["remaining_quantity"] == "3"
        and partial_order["cash_cost"] == "81",
        "partial_fill_nav_exact": partial["book"]["nav"] == "1499",
        "correction_lineage_explicit": len(corrected["correction_lineage"]) == 1
        and corrected["product_certification_status"]
        == "INVALIDATED_BY_CORRECTION",
        "correction_economics_exact": corrected_order["remaining_quantity"] == "2"
        and corrected_order["cash_cost"] == "122"
        and corrected["book"]["nav"] == "1498",
        "valuation_pending_no_invention": pending["book"]["valuation_status"]
        == "VALUATION_PENDING"
        and pending["book"]["nav"] is None
        and pending["book"]["position_value"] is None,
        "zero_split_residual_preserved": partial["book"]["split_value_residual"]
        == "0"
        and corrected["book"]["split_value_residual"] == "0",
    }
    matrix = {
        "idempotence": {
            "baseline_replay_state_hash": baseline["replay_state_hash"],
            "duplicate_delivery_replay_state_hash": duplicate["replay_state_hash"],
        },
        "partial_fill": {
            "order_status": partial_order["status"],
            "filled_quantity": partial_order["filled_quantity"],
            "remaining_quantity": partial_order["remaining_quantity"],
            "cash_cost": partial_order["cash_cost"],
            "terminal_nav": partial["book"]["nav"],
        },
        "correction_lineage": {
            "correction_id": corrected["correction_lineage"][0]["correction_id"],
            "target_event_id": corrected["correction_lineage"][0][
                "target_event_id"
            ],
            "replacement_event_id": corrected["correction_lineage"][0][
                "replacement_event_id"
            ],
            "remaining_quantity": corrected_order["remaining_quantity"],
            "cash_cost": corrected_order["cash_cost"],
            "terminal_nav": corrected["book"]["nav"],
            "product_certification_status": corrected[
                "product_certification_status"
            ],
        },
        "valuation_pending": {
            "valuation_status": pending["book"]["valuation_status"],
            "position_value": pending["book"]["position_value"],
            "nav": pending["book"]["nav"],
        },
        "checks": checks,
    }
    matrix["fixture_matrix_hash"] = domain_hash(
        f"{REPLAY_DOMAIN}:FIXTURE_MATRIX:V1", matrix
    )
    return matrix


def _required_text(value: Any, *, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReplayV0Error(code)
    return value


def _git_object_id(value: Any, *, code: str) -> str:
    text = _required_text(value, code=code)
    if not _SHA1_RE.fullmatch(text):
        raise ReplayV0Error(code)
    return text


def _sha256_text(value: Any, *, code: str) -> str:
    try:
        return assert_sha256(value)
    except CanonicalizationError as exc:
        raise ReplayV0Error(code) from exc


def _canonical_receipt_timestamp(value: Any, *, code: str) -> str:
    if not isinstance(value, str):
        raise ReplayV0Error(code)
    try:
        normalized = canonical_timestamp(value)
    except CanonicalizationError as exc:
        raise ReplayV0Error(code) from exc
    if normalized != value:
        raise ReplayV0Error(code)
    return normalized


def _github_login(value: Any, *, code: str) -> str:
    text = _required_text(value, code=code)
    if not _GITHUB_LOGIN_RE.fullmatch(text):
        raise ReplayV0Error(code)
    return text


def _audit_package_hash(
    *,
    candidate_commit: str,
    candidate_tree: str,
    subject_event_ledger_hash: str,
) -> str:
    return domain_hash(
        f"{REPLAY_DOMAIN}:SLICE0_AUDIT_PACKAGE:V2",
        {
            "candidate_commit": candidate_commit,
            "candidate_tree": candidate_tree,
            "subject_event_ledger_hash": subject_event_ledger_hash,
            "locked_environment": {
                "python": "3.12.10",
                "pytest": "9.0.2",
                "streamlit": "1.54.0",
                "jsonschema": "4.26.0",
            },
        },
    )


def _validate_reviewer_report(
    report: Mapping[str, Any],
    *,
    expected_domain: str,
    expected_candidate_commit: str,
    expected_candidate_tree: str,
    expected_subject_event_ledger_hash: str,
) -> dict[str, Any]:
    row = deepcopy(dict(report))
    required = {
        "schema_version",
        "domain",
        "verdict",
        "candidate_commit",
        "candidate_tree",
        "subject_event_ledger_hash",
        "checks",
        "findings",
        "reviewer_summary",
    }
    if set(row) != required:
        raise ReplayV0Error("REVIEW_REPORT_FIELDS_INVALID")
    if row["schema_version"] != REVIEW_REPORT_SCHEMA:
        raise ReplayV0Error("REVIEW_REPORT_SCHEMA_INVALID")
    if row["domain"] != expected_domain or row["verdict"] != "PASS":
        raise ReplayV0Error("REVIEW_REPORT_VERDICT_INVALID")
    if row["candidate_commit"] != expected_candidate_commit:
        raise ReplayV0Error("REVIEW_REPORT_CANDIDATE_COMMIT_MISMATCH")
    if row["candidate_tree"] != expected_candidate_tree:
        raise ReplayV0Error("REVIEW_REPORT_CANDIDATE_TREE_MISMATCH")
    if row["subject_event_ledger_hash"] != expected_subject_event_ledger_hash:
        raise ReplayV0Error("REVIEW_REPORT_SUBJECT_MISMATCH")
    checks = row["checks"]
    if not isinstance(checks, Mapping) or not checks:
        raise ReplayV0Error("REVIEW_REPORT_CHECKS_REQUIRED")
    if any(value is not True for value in checks.values()):
        raise ReplayV0Error("REVIEW_REPORT_CHECK_FAILED")
    findings = row["findings"]
    if not isinstance(findings, list):
        raise ReplayV0Error("REVIEW_REPORT_FINDINGS_LIST_REQUIRED")
    for finding in findings:
        if not isinstance(finding, Mapping):
            raise ReplayV0Error("REVIEW_REPORT_FINDING_INVALID")
        severity = str(finding.get("severity", "")).upper()
        status = str(finding.get("status", "")).upper()
        if severity in {"CRITICAL", "HIGH"} and status not in {"CLOSED", "RESOLVED"}:
            raise ReplayV0Error("REVIEW_REPORT_HIGH_FINDING_OPEN")
    _required_text(row["reviewer_summary"], code="REVIEW_REPORT_SUMMARY_REQUIRED")
    return row


def _validate_external_review_receipt(
    receipt: Mapping[str, Any],
    *,
    expected_domain: str,
    expected_candidate_commit: str,
    expected_candidate_tree: str,
    expected_subject_event_ledger_hash: str,
    expected_review_package_hash: str,
    expected_implementer_login: str,
) -> tuple[dict[str, Any], str]:
    row = deepcopy(dict(receipt))
    required = {
        "schema_version",
        "domain",
        "verdict",
        "provider",
        "repository",
        "authenticated_submitter_id",
        "github_author_login",
        "github_committer_login",
        "submission_commit_sha",
        "report_path",
        "report_sha256",
        "report",
        "receipt_url",
        "submitted_at",
        "candidate_commit",
        "candidate_tree",
        "review_package_hash",
        "claim_boundary",
        "receipt_hash",
    }
    if set(row) != required:
        raise ReplayV0Error("EXTERNAL_REVIEW_RECEIPT_FIELDS_INVALID")
    if row["schema_version"] != EXTERNAL_REVIEW_RECEIPT_SCHEMA:
        raise ReplayV0Error("EXTERNAL_REVIEW_RECEIPT_SCHEMA_INVALID")
    if row["domain"] != expected_domain or row["verdict"] != "PASS":
        raise ReplayV0Error("EXTERNAL_REVIEW_RECEIPT_VERDICT_INVALID")
    if row["provider"] != GITHUB_PROVIDER:
        raise ReplayV0Error("EXTERNAL_REVIEW_PROVIDER_INVALID")
    repository = _required_text(
        row["repository"], code="EXTERNAL_REVIEW_REPOSITORY_REQUIRED"
    )
    repository_parts = repository.split("/")
    if len(repository_parts) != 2 or any(not part for part in repository_parts):
        raise ReplayV0Error("EXTERNAL_REVIEW_REPOSITORY_INVALID")
    submitter = _github_login(
        row["authenticated_submitter_id"], code="EXTERNAL_REVIEW_SUBMITTER_INVALID"
    )
    author = _github_login(
        row["github_author_login"], code="EXTERNAL_REVIEW_AUTHOR_INVALID"
    )
    _github_login(
        row["github_committer_login"], code="EXTERNAL_REVIEW_COMMITTER_INVALID"
    )
    if author != submitter:
        raise ReplayV0Error("EXTERNAL_REVIEW_SUBMITTER_NOT_AUTHOR")
    if submitter == expected_implementer_login:
        raise ReplayV0Error("EXTERNAL_REVIEWER_EQUALS_IMPLEMENTER")
    _git_object_id(
        row["submission_commit_sha"], code="EXTERNAL_REVIEW_SUBMISSION_COMMIT_INVALID"
    )
    if row["candidate_commit"] != expected_candidate_commit:
        raise ReplayV0Error("EXTERNAL_REVIEW_CANDIDATE_COMMIT_MISMATCH")
    if row["candidate_tree"] != expected_candidate_tree:
        raise ReplayV0Error("EXTERNAL_REVIEW_CANDIDATE_TREE_MISMATCH")
    if row["review_package_hash"] != expected_review_package_hash:
        raise ReplayV0Error("EXTERNAL_REVIEW_PACKAGE_HASH_MISMATCH")
    report = row["report"]
    if not isinstance(report, Mapping):
        raise ReplayV0Error("EXTERNAL_REVIEW_REPORT_OBJECT_REQUIRED")
    verified_report = _validate_reviewer_report(
        report,
        expected_domain=expected_domain,
        expected_candidate_commit=expected_candidate_commit,
        expected_candidate_tree=expected_candidate_tree,
        expected_subject_event_ledger_hash=expected_subject_event_ledger_hash,
    )
    expected_report_sha = sha256_bytes(canonical_document_bytes(verified_report))
    if _sha256_text(
        row["report_sha256"], code="EXTERNAL_REVIEW_REPORT_SHA256_INVALID"
    ) != expected_report_sha:
        raise ReplayV0Error("EXTERNAL_REVIEW_REPORT_BYTE_MISMATCH")
    _required_text(row["report_path"], code="EXTERNAL_REVIEW_REPORT_PATH_REQUIRED")
    receipt_url = _required_text(
        row["receipt_url"], code="EXTERNAL_REVIEW_RECEIPT_URL_REQUIRED"
    )
    if not receipt_url.startswith("https://github.com/"):
        raise ReplayV0Error("EXTERNAL_REVIEW_RECEIPT_URL_INVALID")
    _canonical_receipt_timestamp(
        row["submitted_at"], code="EXTERNAL_REVIEW_TIMESTAMP_INVALID"
    )
    expected_boundary = {
        "provider_authenticated_account_separation_required": True,
        "natural_personhood_proven": False,
        "operational_separation_only": True,
    }
    if row["claim_boundary"] != expected_boundary:
        raise ReplayV0Error("EXTERNAL_REVIEW_CLAIM_BOUNDARY_INVALID")
    body = {key: value for key, value in row.items() if key != "receipt_hash"}
    expected_receipt_hash = domain_hash(
        f"{REPLAY_DOMAIN}:EXTERNAL_REVIEW_RECEIPT:V2", body
    )
    if _sha256_text(
        row["receipt_hash"], code="EXTERNAL_REVIEW_RECEIPT_HASH_INVALID"
    ) != expected_receipt_hash:
        raise ReplayV0Error("EXTERNAL_REVIEW_RECEIPT_HASH_MISMATCH")
    return row, submitter


def evaluate_audit_receipt(
    audit_receipt: Mapping[str, Any] | None,
    *,
    subject_event_ledger_hash: str,
    expected_candidate_commit: str | None = None,
    expected_candidate_tree: str | None = None,
    expected_implementer_github_login: str | None = None,
) -> dict[str, Any]:
    """Validate receipt structure without granting locally self-authored audit authority.

    A JSON payload can bind bytes and declared identities, but it cannot prove that
    GitHub authenticated those identities. Until a separate provider-verification
    boundary exists, every locally supplied receipt remains non-authorizing.
    """

    if audit_receipt is None:
        return {
            "status": "BLOCKED",
            "reason": "SLICE0_AUDIT_PASS_REQUIRED",
            "audit_receipt_hash": None,
        }
    try:
        candidate_commit = _git_object_id(
            expected_candidate_commit,
            code="EXPECTED_CANDIDATE_COMMIT_REQUIRED",
        )
        candidate_tree = _git_object_id(
            expected_candidate_tree,
            code="EXPECTED_CANDIDATE_TREE_REQUIRED",
        )
        implementer_login = _github_login(
            expected_implementer_github_login,
            code="EXPECTED_IMPLEMENTER_GITHUB_LOGIN_REQUIRED",
        )
        subject_hash = _sha256_text(
            subject_event_ledger_hash,
            code="SUBJECT_EVENT_LEDGER_HASH_INVALID",
        )
        row = deepcopy(dict(audit_receipt))
        required = {
            "schema_version",
            "verdict",
            "independent",
            "candidate_commit",
            "candidate_tree",
            "subject_event_ledger_hash",
            "locked_environment",
            "implementer_github_login",
            "review_package_hash",
            "reviewers",
            "claim_boundary",
            "audit_receipt_hash",
        }
        if set(row) != required:
            raise ReplayV0Error("AUDIT_RECEIPT_FIELDS_INVALID")
        if row["schema_version"] != AUDIT_RECEIPT_SCHEMA:
            raise ReplayV0Error("AUDIT_RECEIPT_SCHEMA_V2_REQUIRED")
        if row["verdict"] != "PASS" or row["independent"] is not True:
            raise ReplayV0Error("AUDIT_RECEIPT_VERDICT_INVALID")
        if row["candidate_commit"] != candidate_commit:
            raise ReplayV0Error("AUDIT_RECEIPT_CANDIDATE_COMMIT_MISMATCH")
        if row["candidate_tree"] != candidate_tree:
            raise ReplayV0Error("AUDIT_RECEIPT_CANDIDATE_TREE_MISMATCH")
        if row["subject_event_ledger_hash"] != subject_hash:
            raise ReplayV0Error("AUDIT_RECEIPT_SUBJECT_MISMATCH")
        if row["implementer_github_login"] != implementer_login:
            raise ReplayV0Error("AUDIT_RECEIPT_IMPLEMENTER_MISMATCH")
        expected_environment = {
            "python": "3.12.10",
            "pytest": "9.0.2",
            "streamlit": "1.54.0",
            "jsonschema": "4.26.0",
        }
        if row["locked_environment"] != expected_environment:
            raise ReplayV0Error("AUDIT_RECEIPT_ENVIRONMENT_MISMATCH")
        expected_package_hash = _audit_package_hash(
            candidate_commit=candidate_commit,
            candidate_tree=candidate_tree,
            subject_event_ledger_hash=subject_hash,
        )
        if row["review_package_hash"] != expected_package_hash:
            raise ReplayV0Error("AUDIT_RECEIPT_PACKAGE_HASH_MISMATCH")
        reviewers = row["reviewers"]
        if not isinstance(reviewers, list) or len(reviewers) != 3:
            raise ReplayV0Error("AUDIT_RECEIPT_THREE_REVIEWERS_REQUIRED")
        by_domain: dict[str, Mapping[str, Any]] = {}
        for receipt in reviewers:
            if not isinstance(receipt, Mapping):
                raise ReplayV0Error("AUDIT_RECEIPT_REVIEWER_OBJECT_REQUIRED")
            domain = receipt.get("domain")
            if domain in by_domain:
                raise ReplayV0Error("AUDIT_RECEIPT_REVIEWER_DOMAIN_DUPLICATE")
            by_domain[str(domain)] = receipt
        if set(by_domain) != set(REVIEW_DOMAINS):
            raise ReplayV0Error("AUDIT_RECEIPT_REVIEWER_DOMAINS_INVALID")
        reviewer_logins: list[str] = []
        verified_reviewers: list[dict[str, Any]] = []
        for domain in REVIEW_DOMAINS:
            verified, login = _validate_external_review_receipt(
                by_domain[domain],
                expected_domain=domain,
                expected_candidate_commit=candidate_commit,
                expected_candidate_tree=candidate_tree,
                expected_subject_event_ledger_hash=subject_hash,
                expected_review_package_hash=expected_package_hash,
                expected_implementer_login=implementer_login,
            )
            verified_reviewers.append(verified)
            reviewer_logins.append(login)
        if len(set(reviewer_logins)) != 3:
            raise ReplayV0Error("AUDIT_RECEIPT_REVIEWER_LOGINS_NOT_DISTINCT")
        expected_boundary = {
            "provider_account_separation_proven": True,
            "natural_personhood_proven": False,
            "terminal_acceptance_requires_exact_git_and_report_bytes": True,
        }
        if row["claim_boundary"] != expected_boundary:
            raise ReplayV0Error("AUDIT_RECEIPT_CLAIM_BOUNDARY_INVALID")
        body = {
            **{key: value for key, value in row.items() if key not in {"reviewers", "audit_receipt_hash"}},
            "reviewers": verified_reviewers,
        }
        expected_audit_hash = domain_hash(
            f"{REPLAY_DOMAIN}:AUDIT_RECEIPT:V2", body
        )
        if _sha256_text(
            row["audit_receipt_hash"], code="AUDIT_RECEIPT_HASH_INVALID"
        ) != expected_audit_hash:
            raise ReplayV0Error("AUDIT_RECEIPT_HASH_MISMATCH")
        return {
            "status": "BLOCKED",
            "reason": "EXTERNAL_PROVIDER_VERIFICATION_REQUIRED",
            "audit_receipt_hash": expected_audit_hash,
            "reviewer_github_logins": reviewer_logins,
        }
    except ReplayV0Error as exc:
        return {
            "status": "BLOCKED",
            "reason": f"SLICE0_AUDIT_RECEIPT_INVALID:{exc}",
            "audit_receipt_hash": None,
        }


def build_replay_evidence(
    workspace: Mapping[str, Any],
    *,
    audit_receipt: Mapping[str, Any] | None = None,
    expected_candidate_commit: str | None = None,
    expected_candidate_tree: str | None = None,
    expected_implementer_github_login: str | None = None,
) -> dict[str, Any]:
    """Build byte-stable shadow replay evidence; terminal certification is external."""

    first = replay_workspace(workspace)
    second = replay_workspace(deepcopy(dict(workspace)))
    fixture_matrix = build_replay_fixture_matrix(workspace)
    stored_book = workspace.get("book")
    if not isinstance(stored_book, Mapping):
        raise ReplayV0Error("STORED_BOOK_OBJECT_REQUIRED")
    current_certification = workspace.get("certification")
    if not isinstance(current_certification, Mapping):
        raise ReplayV0Error("CURRENT_CERTIFICATION_OBJECT_REQUIRED")
    orders = first["execution"]["orders"]
    checks = {
        "idempotent_replay_bytes": canonical_document_bytes(first)
        == canonical_document_bytes(second),
        "stored_book_exact": canonical_document_bytes(first["book"])
        == canonical_document_bytes(stored_book),
        "classified_cash_exact": first["book"].get("classified_cash")
        == stored_book.get("classified_cash"),
        "positions_exact": first["book"].get("positions") == stored_book.get("positions"),
        "costs_exact": first["execution"].get("cash_cost") == "201",
        "nav_exact": first["book"].get("nav") == "1499",
        "thesis_state_reconstructed": len(first["decision"].get("thesis_states") or []) == 4,
        "aim_reference_exact": first["decision"].get("portfolio_aim_id")
        == workspace["portfolio_aim"]["portfolio_aim_id"],
        "decision_snapshot_reference_exact": first["decision"].get(
            "decision_snapshot_id"
        )
        == workspace["decision_snapshot"]["decision_snapshot_id"],
        "execution_fully_filled": len(orders) == 1
        and orders[0].get("status") == "FILLED"
        and orders[0].get("remaining_quantity") == "0",
        "prior_certifications_byte_stable": bool(
            first["product_certification_chain"]
        )
        and all(
            row["byte_stable"] for row in first["product_certification_chain"]
        ),
        "current_certification_subject_exact": first[
            "source_event_ledger_hash"
        ]
        == current_certification.get("subject_event_ledger_hash"),
        "zero_unexplained_residual": first["book"].get("split_value_residual")
        == "0",
        "valuation_complete_without_invention": first["book"].get(
            "valuation_status"
        )
        == "COMPLETE",
        "adversarial_fixture_matrix_passed": all(
            fixture_matrix["checks"].values()
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise ReplayV0Error(f"REPLAY_CHECK_FAILED:{','.join(failed)}")

    audit_gate = evaluate_audit_receipt(
        audit_receipt,
        subject_event_ledger_hash=first["source_event_ledger_hash"],
        expected_candidate_commit=expected_candidate_commit,
        expected_candidate_tree=expected_candidate_tree,
        expected_implementer_github_login=expected_implementer_github_login,
    )
    evidence = {
        "schema_version": REPLAY_EVIDENCE_SCHEMA,
        "fixture_id": first["fixture_id"],
        "source_event_ledger_hash": first["source_event_ledger_hash"],
        "normalized_event_stream_hash": first["normalized_event_stream_hash"],
        "replay_state_hash": first["replay_state_hash"],
        "terminal_book_hash": first["book"]["book_hash"],
        "decision_state_hash": first["decision"]["decision_state_hash"],
        "execution_hash": first["execution"]["execution_hash"],
        "fixture_matrix_hash": fixture_matrix["fixture_matrix_hash"],
        "fixture_matrix": fixture_matrix,
        "product_certification_ids": [
            row["certification_id"]
            for row in first["product_certification_chain"]
        ],
        "checks": checks,
        "declared_precision": DECLARED_PRECISION,
        "audit_gate": audit_gate,
        "claim_boundary": (
            "Deterministic local replay evidence only until an exact independent "
            "Slice 0 audit receipt passes the gate."
        ),
        "replay_certification": None,
    }
    if audit_gate["status"] == "PASS":
        certification_payload = {
            "schema_version": REPLAY_CERTIFICATION_SCHEMA,
            "source_event_ledger_hash": evidence["source_event_ledger_hash"],
            "normalized_event_stream_hash": evidence[
                "normalized_event_stream_hash"
            ],
            "replay_state_hash": evidence["replay_state_hash"],
            "terminal_book_hash": evidence["terminal_book_hash"],
            "decision_state_hash": evidence["decision_state_hash"],
            "execution_hash": evidence["execution_hash"],
            "fixture_matrix_hash": evidence["fixture_matrix_hash"],
            "product_certification_ids": evidence["product_certification_ids"],
            "audit_receipt_hash": audit_gate["audit_receipt_hash"],
            "checks": checks,
            "declared_precision": DECLARED_PRECISION,
        }
        evidence["replay_certification"] = {
            "certification_id": _portfolio_identifier("CRT", certification_payload),
            **certification_payload,
        }
    evidence["evidence_hash"] = domain_hash(
        f"{REPLAY_DOMAIN}:EVIDENCE:V1", evidence
    )
    return evidence
