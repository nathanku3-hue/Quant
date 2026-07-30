"""GV-DETERMINISTIC-REPLAY-0 — exact reconstruction and custody reports.

Replay owns reconstruction orchestration, idempotence proofs, correction lineage,
partial-fill residual reporting, valuation-pending honesty, and byte-stable prior
certification under append-only reopen. Product vertical fixtures remain read-only
consumers of Slice 0 events; this module does not mutate Slice 0 product code.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.book import (
    PortfolioBookError,
    build_portfolio_book,
    certification_eligible,
)

ID_DOMAIN = "GV-PORTFOLIO-V0"
REPLAY_SCHEMA = "gv_portfolio_v0_replay_report_v1"
REPLAY_CLAIM_BOUNDARY = (
    "Deterministic replay certification only; no alpha or live-capital claim."
)

# Branch pins (implementation starts from promotion tip; custody base is immutable).
PROMOTION_TIP_SHA = "9bee4396502174cfd791809e53de183e1a93bb75"
CUSTODY_BASE_SHA = "03a5c922d250d615380bbd0d60e8fd636e4ec1c6"
SLICE0_TERMINAL_SHA = "85e6601742710f03e6cced7377b4be426cd4892f"


class ReplayError(ValueError):
    """Fail-closed deterministic replay error."""


def branch_pins() -> dict[str, str]:
    return {
        "promotion_tip_sha": PROMOTION_TIP_SHA,
        "custody_base_sha": CUSTODY_BASE_SHA,
        "slice0_terminal_sha": SLICE0_TERMINAL_SHA,
        "active_implementation_base": PROMOTION_TIP_SHA,
    }


def _ordered_event_rows(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(row) for row in events]
    if not rows:
        raise ReplayError("EVENT_STREAM_REQUIRED")
    sequences: list[int] = []
    event_ids: list[str] = []
    for row in rows:
        sequence = row.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise ReplayError("EVENT_SEQUENCE_INVALID")
        sequences.append(sequence)
        event_id = row.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ReplayError("EVENT_ID_REQUIRED")
        event_ids.append(event_id)
        if not isinstance(row.get("payload"), Mapping):
            raise ReplayError("EVENT_PAYLOAD_MAPPING_REQUIRED")
    if len(sequences) != len(set(sequences)):
        raise ReplayError("DUPLICATE_EVENT_SEQUENCE")
    if sequences != list(range(len(rows))):
        raise ReplayError("DECLARED_EVENT_ORDER_INVALID")
    if len(event_ids) != len(set(event_ids)):
        raise ReplayError("DUPLICATE_EVENT_ID")
    return rows


def subject_events(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Economic + decision subject stream excludes certification record markers."""

    return [
        dict(row)
        for row in _ordered_event_rows(events)
        if row.get("event_type") != "CERTIFICATION_RECORDED"
    ]


def event_ledger_hash(events: Iterable[Mapping[str, Any]]) -> str:
    return domain_hash(f"{ID_DOMAIN}:EVENT_LEDGER:V1", subject_events(events))


def reconstruct_book(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Exact economic reconstruction from the declared event order."""

    try:
        return build_portfolio_book(_ordered_event_rows(events))
    except PortfolioBookError as exc:
        raise ReplayError(str(exc)) from exc


def exact_match(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return canonical_document_bytes(dict(left)) == canonical_document_bytes(dict(right))


def reconstruct_exact(
    events: Iterable[Mapping[str, Any]],
    *,
    expected_book: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail closed unless reconstruction matches the expected book bytes."""

    book = reconstruct_book(events)
    # Compare certification-stable core (exclude replay-only residual projection).
    expected_core = {
        key: value
        for key, value in expected_book.items()
        if key != "partial_fill_residuals"
    }
    actual_core = {
        key: value for key, value in book.items() if key != "partial_fill_residuals"
    }
    if not exact_match(actual_core, expected_core):
        raise ReplayError("RECONSTRUCTION_MISMATCH")
    return book


def replay_idempotent(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Replay the same event prefix twice; require identical book and ledger hashes."""

    rows = _ordered_event_rows(events)
    first = reconstruct_book(rows)
    second = reconstruct_book(deepcopy(rows))
    if first["book_hash"] != second["book_hash"]:
        raise ReplayError("IDEMPOTENCE_BOOK_HASH_MISMATCH")
    if event_ledger_hash(rows) != event_ledger_hash(deepcopy(rows)):
        raise ReplayError("IDEMPOTENCE_LEDGER_HASH_MISMATCH")
    if not exact_match(first, second):
        raise ReplayError("IDEMPOTENCE_BOOK_BYTES_MISMATCH")
    return first


def partial_fill_residuals(events: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    book = reconstruct_book(events)
    residuals = list(book.get("partial_fill_residuals") or [])
    return residuals


def valuation_pending_book(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Reconstruct with missing prices; never invent a valuation."""

    book = reconstruct_book(events)
    if book.get("valuation_status") != "VALUATION_PENDING":
        raise ReplayError("VALUATION_PENDING_REQUIRED")
    if book.get("nav") is not None or book.get("position_value") is not None:
        raise ReplayError("FABRICATED_VALUATION_FORBIDDEN")
    if certification_eligible(book):
        raise ReplayError("PENDING_BOOK_MUST_NOT_CERTIFY")
    for row in book.get("positions") or []:
        if row.get("valuation_price") is None and row.get("market_value") is not None:
            raise ReplayError("FABRICATED_MARKET_VALUE_FORBIDDEN")
    return book


def _certification_record(
    *,
    events: list[dict[str, Any]],
    book: Mapping[str, Any],
    prior_certification_id: str | None,
    decision_snapshot_id: str,
    portfolio_aim_id: str,
) -> dict[str, Any]:
    if book.get("valuation_status") != "COMPLETE":
        raise ReplayError("CERTIFICATION_REQUIRES_COMPLETE_VALUATION")
    if not certification_eligible(book):
        raise ReplayError("CERTIFICATION_BOOK_INELIGIBLE")
    subject = subject_events(events)
    payload = {
        "subject_event_ledger_hash": domain_hash(
            f"{ID_DOMAIN}:EVENT_LEDGER:V1", subject
        ),
        "terminal_book_hash": book["book_hash"],
        "decision_snapshot_id": decision_snapshot_id,
        "portfolio_aim_id": portfolio_aim_id,
        "declared_precision": book.get("declared_precision"),
        "prior_certification_id": prior_certification_id,
        "replay_schema": REPLAY_SCHEMA,
    }
    certification_id = "CRT_" + domain_hash(f"{ID_DOMAIN}:CRT:V1", payload)
    return {"certification_id": certification_id, **payload}


def certify_replay_prefix(
    events: Iterable[Mapping[str, Any]],
    *,
    decision_snapshot_id: str,
    portfolio_aim_id: str,
    prior_certification: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    rows = _ordered_event_rows(events)
    book = reconstruct_book(rows)
    prior_id = None
    if prior_certification is not None:
        prior_id = prior_certification.get("certification_id")
        if not isinstance(prior_id, str) or not prior_id:
            raise ReplayError("PRIOR_CERTIFICATION_ID_REQUIRED")
    return _certification_record(
        events=rows,
        book=book,
        prior_certification_id=prior_id,
        decision_snapshot_id=decision_snapshot_id,
        portfolio_aim_id=portfolio_aim_id,
    )


def append_correction_and_recertify(
    events: Iterable[Mapping[str, Any]],
    *,
    prior_certification: Mapping[str, Any],
    correction_payload: Mapping[str, Any],
    decision_snapshot_id: str,
    portfolio_aim_id: str,
    effective_at: str,
    source_identity: str,
) -> dict[str, Any]:
    """Append-only correction lineage; prior certification bytes stay frozen."""

    prior_bytes = canonical_document_bytes(dict(prior_certification))
    rows = _ordered_event_rows(events)
    # Recompute prior from the frozen pre-correction prefix; require byte match.
    if prior_certification.get("prior_certification_id") is None:
        recomputed_prior = certify_replay_prefix(
            rows,
            decision_snapshot_id=decision_snapshot_id,
            portfolio_aim_id=portfolio_aim_id,
            prior_certification=None,
        )
    else:
        recomputed_prior = certify_replay_prefix(
            rows,
            decision_snapshot_id=decision_snapshot_id,
            portfolio_aim_id=portfolio_aim_id,
            prior_certification={
                "certification_id": prior_certification["prior_certification_id"]
            },
        )
    if canonical_document_bytes(recomputed_prior) != prior_bytes:
        raise ReplayError("PRIOR_CERTIFICATION_NOT_BYTE_STABLE")

    correction_body = {
        "correction_kind": str(correction_payload.get("correction_kind") or "ANNOTATION"),
        "reason": str(correction_payload.get("reason") or ""),
        "prior_certification_id": prior_certification["certification_id"],
        "details": dict(correction_payload.get("details") or {}),
    }
    # Non-economic annotation: book ignores CORRECTION_RECORDED; lineage is the proof.
    correction_event = {
        "sequence": len(rows),
        "event_type": "CORRECTION_RECORDED",
        "effective_at": effective_at,
        "source_identity": source_identity,
        "instrument_id": None,
        "cash_bucket": None,
        "payload": correction_body,
    }
    # event_id is content-addressed for custody of the correction itself
    event_identity = {
        key: value for key, value in correction_event.items() if key != "event_id"
    }
    correction_event["event_id"] = "EVT_" + domain_hash(
        f"{ID_DOMAIN}:EVT:V1", event_identity
    )

    extended = [*rows, correction_event]
    # Book reduction must tolerate non-economic correction markers.
    book = reconstruct_book_with_corrections(extended)
    new_cert = _certification_record(
        events=extended,
        book=book,
        prior_certification_id=prior_certification["certification_id"],
        decision_snapshot_id=decision_snapshot_id,
        portfolio_aim_id=portfolio_aim_id,
    )
    if canonical_document_bytes(dict(prior_certification)) != prior_bytes:
        raise ReplayError("PRIOR_CERTIFICATION_MUTATED")
    return {
        "events": extended,
        "book": book,
        "prior_certification": dict(prior_certification),
        "certification": new_cert,
        "prior_certification_bytes_sha256": domain_hash(
            f"{ID_DOMAIN}:CERT_BYTES:V1",
            {"bytes": prior_bytes.decode("utf-8")},
        ),
    }


def reconstruct_book_with_corrections(
    events: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Reduce events; non-economic correction markers are ignored by accounting."""

    return reconstruct_book(events)


def reopen_with_stable_prior(
    *,
    pre_observation_events: Iterable[Mapping[str, Any]],
    full_events: Iterable[Mapping[str, Any]],
    prior_certification: Mapping[str, Any],
    decision_snapshot_id: str,
    portfolio_aim_id: str,
) -> dict[str, Any]:
    """Reopen after later events; prior Replay cert must recompute byte-identically."""

    prior_bytes = canonical_document_bytes(dict(prior_certification))
    recomputed = certify_replay_prefix(
        pre_observation_events,
        decision_snapshot_id=decision_snapshot_id,
        portfolio_aim_id=portfolio_aim_id,
        prior_certification=None,
    )
    if canonical_document_bytes(recomputed) != prior_bytes:
        raise ReplayError("REOPEN_PRIOR_CERTIFICATION_MISMATCH")
    current = certify_replay_prefix(
        full_events,
        decision_snapshot_id=decision_snapshot_id,
        portfolio_aim_id=portfolio_aim_id,
        prior_certification=prior_certification,
    )
    if current.get("prior_certification_id") != prior_certification.get(
        "certification_id"
    ):
        raise ReplayError("REOPEN_PRIOR_LINK_MISMATCH")
    if canonical_document_bytes(dict(prior_certification)) != prior_bytes:
        raise ReplayError("REOPEN_PRIOR_CERTIFICATION_MUTATED")
    return {
        "prior_certification": dict(prior_certification),
        "certification": current,
        "book": reconstruct_book(full_events),
    }


def reopen_slice0_workspace_stable(
    certified_workspace: Mapping[str, Any],
    observed_workspace: Mapping[str, Any],
) -> dict[str, Any]:
    """Product-cert reopen: recompute prior via product certifier; require byte match."""

    from gv_portfolio_v0.vertical import certify_workspace

    prior = dict(certified_workspace["certification"])
    prior_bytes = canonical_document_bytes(prior)
    prefix = deepcopy(dict(certified_workspace))
    recomputed = certify_workspace(prefix)
    if canonical_document_bytes(recomputed) != prior_bytes:
        raise ReplayError("REOPEN_PRIOR_CERTIFICATION_MISMATCH")
    observed_prior = observed_workspace.get("certification_history") or []
    if not observed_prior:
        raise ReplayError("OBSERVED_PRIOR_HISTORY_REQUIRED")
    stored_prior = observed_prior[0]
    if canonical_document_bytes(dict(stored_prior)) != prior_bytes:
        raise ReplayError("OBSERVED_PRIOR_HISTORY_MISMATCH")
    current = observed_workspace.get("certification")
    if not isinstance(current, Mapping):
        raise ReplayError("OBSERVED_CERTIFICATION_REQUIRED")
    if current.get("prior_certification_id") != prior.get("certification_id"):
        raise ReplayError("REOPEN_PRIOR_LINK_MISMATCH")
    if canonical_document_bytes(prior) != prior_bytes:
        raise ReplayError("REOPEN_PRIOR_CERTIFICATION_MUTATED")
    # Exact book reconstruction of the observed event log.
    book = reconstruct_exact(
        observed_workspace["events"], expected_book=observed_workspace["book"]
    )
    return {
        "prior_certification": prior,
        "certification": dict(current),
        "book": book,
    }


def build_replay_report(
    events: Iterable[Mapping[str, Any]],
    *,
    expected_book: Mapping[str, Any] | None = None,
    decision_snapshot_id: str = "DSN_REPLAY_FIXTURE",
    portfolio_aim_id: str = "AIM_REPLAY_FIXTURE",
) -> dict[str, Any]:
    """Assemble the Replay 0 acceptance report for a frozen event log."""

    rows = _ordered_event_rows(events)
    if expected_book is not None:
        book = reconstruct_exact(rows, expected_book=expected_book)
    else:
        book = reconstruct_book(rows)
    idempotent_book = replay_idempotent(rows)
    residuals = list(book.get("partial_fill_residuals") or [])
    report = {
        "schema_version": REPLAY_SCHEMA,
        "claim_boundary": REPLAY_CLAIM_BOUNDARY,
        "branch_pins": branch_pins(),
        "event_count": len(rows),
        "event_ledger_hash": event_ledger_hash(rows),
        "book_hash": book["book_hash"],
        "book": book,
        "idempotent_book_hash": idempotent_book["book_hash"],
        "partial_fill_residuals": residuals,
        "valuation_status": book.get("valuation_status"),
        "unexplained_residual": book.get("unexplained_residual"),
        "split_value_residual": book.get("split_value_residual"),
        "decision_snapshot_id": decision_snapshot_id,
        "portfolio_aim_id": portfolio_aim_id,
    }
    report["report_hash"] = domain_hash(f"{ID_DOMAIN}:REPLAY_REPORT:V1", report)
    return report


def slice0_workspace_replay_report() -> dict[str, Any]:
    """Exact reconstruction of the banked Slice 0 vertical acceptance fixture."""

    # Import locally so Product modules remain consumers, not Replay dependents at import.
    from gv_portfolio_v0.vertical import (
        admit_watch_observation,
        build_draft_workspace,
        confirm_draft_workspace,
    )

    draft = build_draft_workspace()
    certified = confirm_draft_workspace(draft)
    observed = admit_watch_observation(certified)
    events = observed["events"]
    expected_book = observed["book"]
    report = build_replay_report(
        events,
        expected_book=expected_book,
        decision_snapshot_id=observed["decision_snapshot"]["decision_snapshot_id"],
        portfolio_aim_id=observed["portfolio_aim"]["portfolio_aim_id"],
    )
    prior = certified["certification"]
    reopen = reopen_slice0_workspace_stable(certified, observed)
    report["prior_certification_id"] = prior["certification_id"]
    report["reopen_certification_id"] = reopen["certification"]["certification_id"]
    report["prior_certification_byte_stable"] = True
    report["report_hash"] = domain_hash(f"{ID_DOMAIN}:REPLAY_REPORT:V1", report)
    return report
