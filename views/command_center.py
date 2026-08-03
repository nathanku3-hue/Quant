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


def render_command_center(st: Any) -> DecisionEpisodeReadModel:
    """Render the default read-only all-capital operator surface."""

    model = build_command_center_read_model()
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
                "governance_events": model.event_count,
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


def render_decisions_and_thesis(st: Any) -> DecisionEpisodeReadModel:
    """Render read-only proposal claims and evidence custody."""

    model = build_command_center_read_model()
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
                "supporting_evidence": ", ".join(row.supporting_evidence_ids),
                "contradicting_evidence": (
                    ", ".join(row.contradicting_evidence_ids) or "NONE"
                ),
                "missing_discriminator": row.missing_discriminator,
            }
            for row in model.proposal_records
        ]
    )
    return model
