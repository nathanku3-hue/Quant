"""Read-only Command Center over real PIT adapters and projected governance facts."""

from __future__ import annotations

from typing import Any

from core.gv_pit.adapters import build_real_pit_source_bundle
from core.gv_pit.governance import govern_real_pit_bundle
from core.gv_pit.read_models import (
    DecisionEpisodeReadModel,
    project_decision_episode,
)


def build_command_center_read_model() -> DecisionEpisodeReadModel:
    """Compose the current real episode without persistence or portfolio mutation."""

    bundle = build_real_pit_source_bundle()
    stream = govern_real_pit_bundle(bundle)
    return project_decision_episode(stream.read())


def _evidence_provenance(rows: tuple[object, ...]) -> str:
    if not rows:
        return "NONE"
    return "; ".join(
        f"{row.evidence_id} | sha256={row.sha256_digest} | source={row.source_identity}"
        for row in rows
    )


def _proposal_rows(model: DecisionEpisodeReadModel) -> list[dict[str, object]]:
    return [
        {
            "module": row.module_id,
            "outcome": row.outcome,
            "identity_status": row.status,
            "sleeve": row.sleeve_id,
            "target": "; ".join(row.target_summary) or "NO_INSTRUMENT_TARGET",
            "reason_not_to_act": row.reason_not_to_act,
            "missing_discriminator": row.missing_discriminator,
        }
        for row in model.proposal_records
    ]


def _render_fail_closed(st: Any, *, title: str, error: Exception) -> None:
    st.header(title)
    st.error("PIT authority unavailable — no proposal state was rendered.")
    st.caption(f"Fail-closed reason: {type(error).__name__}: {error}")
    st.table(
        [
            {
                "episode_status": "UNAVAILABLE",
                "replay_status": "FAILED_CLOSED",
                "selection_available": False,
                "portfolio_mutation_available": False,
            }
        ]
    )


def render_command_center(st: Any) -> DecisionEpisodeReadModel | None:
    """Render the default read-only all-capital operator surface."""

    try:
        model = build_command_center_read_model()
    except Exception as exc:
        _render_fail_closed(st, title="Command Center", error=exc)
        return None
    identity = model.pit_identity
    market_context = identity.market_snapshot_id

    st.header("Command Center")
    st.caption(
        "One certified book, one exact point-in-time identity, and every real "
        "eligible capital proposal. Read-only Slice 1: no selection, preview, "
        "authorization, persistence, or portfolio mutation."
    )

    st.subheader("Point-in-time identity")
    st.table(
        [
            {
                "certified_book_id": identity.certified_book_id,
                "certified_book_head_event_id": identity.certified_book_head_event_id,
                "evidence_set_id": identity.evidence_set_id,
                "market_context": market_context.kind,
                "as_of_utc": identity.as_of_utc,
            }
        ]
    )
    st.caption(
        "The certified head is the final authoritative event in the certified "
        "prefix. The later certification marker is not the book head."
    )

    capital_col, cash_col, proposal_col = st.columns(3)
    capital_col.metric("Certified NAV", format(model.certified_nav, "f"))
    cash_col.metric(
        "Classified cash",
        format(sum((row.amount for row in model.classified_cash), start=0), "f"),
    )
    proposal_col.metric("Proposal rows", len(model.proposal_records))

    st.subheader("Capital proposals")
    st.table(_proposal_rows(model))
    st.caption(
        "MU operated and MU shadow consume the same decision-free evidence. "
        "The cash baseline carries no fabricated yield or market-return claim."
    )

    st.subheader("Disagreement and evidence gaps")
    st.info(model.disagreement_summary)
    st.table(
        [
            {"missing_discriminator": value}
            for value in model.evidence_gap_summary
        ]
    )

    st.subheader("Compact system health")
    st.table(
        [
            {
                "episode_status": model.status,
                "replay_status": model.replay_status,
                "governance_stream": model.stream_id,
                "governance_events": model.event_count,
                "head_sequence": model.head_sequence_number,
                "eligible_rows": sum(
                    row.status == "ELIGIBLE" for row in model.proposal_records
                ),
                "rejected_identity_rows": sum(
                    row.status == "REJECTED_IDENTITY_MISMATCH"
                    for row in model.proposal_records
                ),
                "selected_rows": len(model.selected_record_ids),
                "durable_governance_persistence": "NONE",
            }
        ]
    )
    return model


def render_decisions_and_thesis(st: Any) -> DecisionEpisodeReadModel | None:
    """Render read-only proposal claims and evidence custody."""

    try:
        model = build_command_center_read_model()
    except Exception as exc:
        _render_fail_closed(st, title="Decisions & Thesis", error=exc)
        return None
    st.header("Decisions & Thesis")
    st.caption(
        "Immutable proposal evidence and thesis detail. This page owns no signal "
        "calculation, identity admission, lifecycle transition, or portfolio mutation."
    )
    st.table(
        [
            {
                "module": row.module_id,
                "outcome": row.outcome,
                "status": row.status,
                "principal_claim": row.principal_claim,
                "supporting_evidence": _evidence_provenance(
                    row.supporting_evidence
                ),
                "contradicting_evidence": _evidence_provenance(
                    row.contradicting_evidence
                ),
                "missing_discriminator": row.missing_discriminator,
            }
            for row in model.proposal_records
        ]
    )
    return model


def render_operations_and_replay(st: Any) -> DecisionEpisodeReadModel | None:
    """Render full Slice 1 source, event-lineage, and projection diagnostics."""

    try:
        model = build_command_center_read_model()
    except Exception as exc:
        _render_fail_closed(st, title="Operations & Replay", error=exc)
        return None

    st.header("Operations & Replay")
    st.caption(
        "Read-only governance lineage. Every row is reconstructed from the bounded "
        "digest-chained stream; no durable governance write occurs in Slice 1."
    )
    st.subheader("Replay identity")
    st.table(
        [
            {
                "stream_id": model.stream_id,
                "event_count": model.event_count,
                "head_sequence": model.head_sequence_number,
                "terminal_event_digest": model.terminal_event_digest,
                "replay_status": model.replay_status,
            }
        ]
    )
    st.subheader("Governance event lineage")
    st.table(
        [
            {
                "sequence": event.sequence_number,
                "type": event.event_type,
                "event_id": event.event_id,
                "timestamp_utc": event.timestamp_utc,
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "previous_digest": event.previous_event_digest,
                "event_digest": event.event_digest,
                "record_id": event.record_id or "",
                "proposal_id": event.proposal_id or "",
            }
            for event in model.governance_events
        ]
    )
    st.subheader("Authority boundary")
    st.table(
        [
            {
                "durable_governance_persistence": "NONE",
                "proposal_selection": "UNAVAILABLE",
                "optimizer_or_risk_math": "UNAVAILABLE",
                "transition_preview": "UNAVAILABLE",
                "authorization": "UNAVAILABLE",
                "book_mutation": "UNAVAILABLE",
                "certification_change": "UNAVAILABLE",
            }
        ]
    )
    return model
