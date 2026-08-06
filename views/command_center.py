"""Sole Command Center for source-bound pair decision series."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from core.gv_fs0_canonical import canonical_document_bytes
from core.gv_pit.adapters import build_real_pit_source_bundle
from core.gv_pit.governance import govern_real_pit_bundle
from core.gv_pit.read_models import DecisionEpisodeReadModel, project_decision_episode
from gv_portfolio_v0.market_source_adapter import (
    load_source_derived_market_packets,
    load_verified_episode_contract,
    max_registered_episode_number,
    next_open_episode_number,
    verified_pair_summary,
)
from gv_portfolio_v0.operated_scenarios import (
    PAIR_DECISION_SERIES_SCENARIO_ID,
    get_scenario,
)
from gv_portfolio_v0.operated_storage import (
    confirm_prospective_observation_and_persist,
    ensure_prospective_workspace,
    reject_prospective_observation_and_persist,
    workspace_path,
)
from gv_portfolio_v0.prospective import (
    build_pair_episode_request,
    preview_runtime_observation,
)
from views.gv_operated_portfolio_workspace import build_book_rows, build_trade_rows

_ACTIVE_PREVIEW_KEY = "gv_command_center_pair_episode_preview"
_ACTIVE_PREVIEW_REQUEST_KEY = "gv_command_center_pair_episode_preview_request"
_ACTIVE_PREVIEW_WORKSPACE_KEY = "gv_command_center_pair_episode_preview_workspace"


def build_command_center_read_model() -> DecisionEpisodeReadModel:
    """Compose the immutable banked PIT comparison without durable mutation."""

    return project_decision_episode(
        govern_real_pit_bundle(build_real_pit_source_bundle()).read()
    )


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


def build_active_command_center_workspace(
    *, root: Path | None = None
) -> dict[str, Any]:
    return ensure_prospective_workspace(
        root=root,
        scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID,
    )


def _active_book_rows(workspace: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = build_book_rows(workspace)
    return rows or [
        {
            "symbol": "CASH_ONLY",
            "quantity": "0",
            "valuation_price": "N/A",
            "market_value": "0",
        }
    ]


def _active_cost_rows(workspace: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = [dict(row) for row in workspace["book"]["classified_costs"]]
    return rows or [
        {
            "classification": "NONE",
            "fill_id": "",
            "order_id": "",
            "cash_bucket": "",
            "amount": "0",
        }
    ]


def _clear_preview(session: Any) -> None:
    session.pop(_ACTIVE_PREVIEW_KEY, None)
    session.pop(_ACTIVE_PREVIEW_REQUEST_KEY, None)
    session.pop(_ACTIVE_PREVIEW_WORKSPACE_KEY, None)


def _render_pair_preview_flow(
    st: Any,
    *,
    workspace: dict[str, Any],
    root: Path | None,
    request: dict[str, Any],
) -> None:
    session = st.session_state
    series = request["decision_series_contract"]
    episode_number = int(series["episode_number"])
    if st.button(
        f"Preview pair episode {episode_number}",
        key="gv_command_center_preview",
    ):
        try:
            session[_ACTIVE_PREVIEW_KEY] = preview_runtime_observation(
                workspace, request
            )
            session[_ACTIVE_PREVIEW_REQUEST_KEY] = dict(request)
            session[_ACTIVE_PREVIEW_WORKSPACE_KEY] = str(
                workspace_path(
                    root, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
                ).absolute()
            )
        except Exception as exc:
            _clear_preview(session)
            st.error(f"Preview rejected: {type(exc).__name__}: {exc}")

    preview = session.get(_ACTIVE_PREVIEW_KEY)
    current_path = str(
        workspace_path(
            root, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
        ).absolute()
    )
    prior_request = session.get(_ACTIVE_PREVIEW_REQUEST_KEY)
    try:
        request_changed = not isinstance(prior_request, Mapping) or (
            canonical_document_bytes(dict(prior_request))
            != canonical_document_bytes(request)
        )
    except (TypeError, ValueError):
        request_changed = True
    stale = isinstance(preview, dict) and (
        preview.get("prior_book_hash") != workspace["book"]["book_hash"]
        or preview.get("prior_certification_id")
        != workspace["certification"]["certification_id"]
        or preview.get("prior_event_count") != len(workspace["events"])
        or preview.get("prior_decision_snapshot_id")
        != workspace["current_decision_snapshot"]["decision_snapshot_id"]
        or session.get(_ACTIVE_PREVIEW_WORKSPACE_KEY) != current_path
        or request_changed
    )
    if stale:
        _clear_preview(session)
        preview = None
        st.warning("The prior preview was stale and has been discarded.")
    if not isinstance(preview, dict):
        return

    series = preview["request"]["decision_series_contract"]
    packets = preview["request"]["source_derived_market_packets"]
    st.subheader(
        f"Mutation-free PAIR-DECISION-SERIES-1 episode {series['episode_number']} preview"
    )
    st.table(
        [
            {
                "proposal_id": preview["proposal_id"],
                "decision_series_id": series["decision_series_id"],
                "episode_number": series["episode_number"],
                "decision_cut_id": series["decision_cut_id"],
                "selected_disposition": preview["request"]["selected_disposition"],
                "economics_changed": preview["economics_changed"],
                "outcome_status": series["outcome_status"],
                "outcome_open_not_before": series["outcome_open_not_before"],
                "authoritative": False,
            }
        ]
    )
    st.table(
        [
            {
                "instrument_id": packet["instrument_id"],
                "permanent_identity": packet["permanent_instrument_identity"],
                "value": packet["value"],
                "valid_effective_at": packet["valid_effective_at"],
                "retrieval_knowledge_at": packet["retrieval_knowledge_at"],
                "row_locator": packet["row_locator"],
                "row_sha256": packet["row_sha256"],
                "packet_sha256": packet["content_sha256"],
            }
            for packet in packets
        ]
    )
    st.subheader("Resulting book preview")
    st.table(_active_book_rows(workspace))
    st.table(workspace["book"]["classified_cash"])
    st.table(_active_cost_rows(workspace))
    st.caption(
        f"book_hash_after=`{workspace['book']['book_hash']}` · "
        f"cash_after={workspace['book']['total_cash']} · "
        f"costs_after={workspace['book']['total_costs']} · "
        f"residual={workspace['book']['unexplained_residual']} · authoritative=false"
    )

    if st.button("Confirm cash / abstention", key="gv_command_center_confirm"):
        try:
            confirm_prospective_observation_and_persist(
                preview,
                root=root,
                scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID,
            )
        except Exception as exc:
            st.error(f"Confirmation rejected: {type(exc).__name__}: {exc}")
        else:
            _clear_preview(session)
            st.rerun()

    rejection_reason = st.text_area(
        "Reject-all rationale",
        key="gv_command_center_rejection_reason",
        placeholder="Explain why the verified A/B/cash proposal must be rejected.",
    )
    if st.button("Reject all", key="gv_command_center_reject"):
        try:
            reject_prospective_observation_and_persist(
                preview,
                rejection_reason,
                root=root,
                scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID,
            )
        except Exception as exc:
            st.error(f"Rejection failed: {type(exc).__name__}: {exc}")
        else:
            _clear_preview(session)
            st.rerun()


def _render_pair_episode_action(
    st: Any,
    *,
    workspace: dict[str, Any],
    root: Path | None,
    episode_number: int,
) -> None:
    st.subheader(f"Seal real MU / NVDA / cash episode {episode_number}")
    st.caption(
        "Market authority is derived from one pinned Cboe BZX source capture, one "
        "permission manifest, one parser, and one common PIT cut for this episode. "
        "The operator cannot edit price, source identity, parser, permission, or timestamps."
    )
    try:
        source = verified_pair_summary(episode_number)
        contract = load_verified_episode_contract(episode_number)
        packets = load_source_derived_market_packets(
            workspace["instruments"], episode_number=episode_number
        )
    except Exception as exc:
        st.error(f"Pair source authority unavailable: {type(exc).__name__}: {exc}")
        return

    reviews = {row["instrument_id"]: row for row in workspace["reviews"]}
    st.table(
        [
            {
                "symbol": instrument["symbol"],
                "instrument_id": instrument["instrument_id"],
                "permanent_identity": instrument["permanent_key"],
                "subject_outcome": reviews[instrument["instrument_id"]]["outcome"],
                "target_quantity": reviews[instrument["instrument_id"]][
                    "target_quantity"
                ],
                "source_value": packet["value"],
                "packet_sha256": packet["content_sha256"],
                "row_locator": packet["row_locator"],
            }
            for instrument, packet in zip(workspace["instruments"], packets, strict=True)
        ]
    )
    st.table(
        [
            {
                "decision_series_id": contract["decision_series_id"],
                "episode_number": contract["episode_number"],
                "decision_cut_id": contract["decision_cut_id"],
                "outcome_horizon": contract["outcome_horizon_spec"]["kind"],
                "outcome_open_not_before": contract["outcome_open_not_before"],
                "comparator": contract["comparator_spec"]["primary"],
                "cost_model_id": contract["cost_model_id"],
                "decision_policy_version": contract["decision_policy_version"],
                "source_contract_version": contract["source_contract_version"],
                "outcome_data_loaded": contract["outcome_data_loaded"],
            }
        ]
    )
    st.caption(
        f"Source object `{source['source_object_sha256']}` · permission "
        f"`{source['permission_manifest_sha256']}` · attribution: {source['attribution']}."
    )
    st.info(
        "Banked evidence does not authorize a position in either security. Cash / "
        f"abstention is the only confirmable episode-{episode_number} disposition; "
        "reject-all remains available."
    )
    rationale = st.text_area(
        "Operator rationale",
        value=(
            "The common market cut is verified, but banked MU and NVDA evidence does "
            "not establish a cost-aware expected-return edge. Retain certified cash."
        ),
        key="gv_command_center_operator_rationale",
    )
    try:
        request = build_pair_episode_request(
            workspace, operator_rationale=rationale
        )
    except Exception as exc:
        st.error(f"Episode request unavailable: {type(exc).__name__}: {exc}")
        return
    _render_pair_preview_flow(
        st,
        workspace=workspace,
        root=root,
        request=request,
    )


def render_command_center(
    st: Any,
    *,
    root: Path | None = None,
) -> DecisionEpisodeReadModel | None:
    try:
        model = build_command_center_read_model()
        workspace = build_active_command_center_workspace(root=root)
    except Exception as exc:
        _render_fail_closed(st, title="Command Center", error=exc)
        return None
    identity = model.pit_identity
    market_context = identity.market_snapshot_id
    scenario = get_scenario(PAIR_DECISION_SERIES_SCENARIO_ID)

    st.header("Command Center")
    st.caption(
        "Active source-bound pair series first; immutable historical no-market PIT "
        "comparison second. One product path owns preview, disposition, atomic "
        "persistence, certification, and exact replay."
    )

    st.subheader("Active certified pair-series workspace")
    st.caption(scenario["claim_boundary"])
    nav_col, cash_col, position_col, cost_col = st.columns(4)
    nav_col.metric("Active NAV", workspace["book"]["nav"])
    cash_col.metric("Active cash", workspace["book"]["total_cash"])
    position_col.metric(
        "Active positions",
        sum(int(row["quantity"]) > 0 for row in workspace["book"]["positions"]),
    )
    cost_col.metric("Active costs", workspace["book"]["total_costs"])
    st.table(_active_book_rows(workspace))
    st.table(workspace["book"]["classified_cash"])
    st.table(_active_cost_rows(workspace))
    st.table(
        [
            {
                "scenario_id": workspace["scenario_id"],
                "status": workspace["status"],
                "book_hash": workspace["book"]["book_hash"],
                "certification_id": workspace["certification"]["certification_id"],
                "prior_certification_id": workspace["certification"].get(
                    "prior_certification_id"
                )
                or "GENESIS",
                "event_count": len(workspace["events"]),
                "certification_lineage_depth": len(
                    workspace["certification_history"]
                ),
                "sealed_series_episode_count": workspace[
                    "sealed_series_episode_count"
                ],
                "opened_outcome_episode_count": workspace[
                    "opened_outcome_episode_count"
                ],
                "unexplained_residual": workspace["book"][
                    "unexplained_residual"
                ],
            }
        ]
    )
    if workspace["prospective_episode_history"]:
        st.subheader("Sealed episode lineage")
        st.table(workspace["prospective_episode_history"])
    if workspace["fills"]:
        st.subheader("Certified paper fills")
        st.table(build_trade_rows(workspace))

    next_episode = next_open_episode_number(
        int(workspace["prospective_episode_count"])
    )
    if next_episode is not None:
        if workspace["prospective_episode_count"] > 0:
            st.success(
                "PAIR-DECISION-SERIES-1 has "
                f"{workspace['prospective_episode_count']} sealed episode(s) "
                "persisted, certified, and reopened exactly. Outcome data remains "
                f"closed; episode {next_episode} is open."
            )
        _render_pair_episode_action(
            st,
            workspace=workspace,
            root=root,
            episode_number=next_episode,
        )
    else:
        st.success(
            "PAIR-DECISION-SERIES-1 has sealed all registered episodes "
            f"(1–{max_registered_episode_number()}), persisted, certified, and "
            "reopened exactly. Outcome data remains closed until each "
            "preregistered open rule permits."
        )

    st.subheader("Banked no-market comparison baseline")
    st.caption(
        "This historical PIT comparison remains immutable evidence and is not the "
        "current source-bound market episode."
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
    baseline_capital_col, baseline_cash_col, proposal_col = st.columns(3)
    baseline_capital_col.metric("Baseline NAV", format(model.certified_nav, "f"))
    baseline_cash_col.metric(
        "Baseline classified cash",
        format(sum((row.amount for row in model.classified_cash), start=0), "f"),
    )
    proposal_col.metric("Proposal rows", len(model.proposal_records))
    st.subheader("Capital proposals")
    st.table(_proposal_rows(model))
    st.subheader("Disagreement and evidence gaps")
    st.info(model.disagreement_summary)
    st.table(
        [{"missing_discriminator": value} for value in model.evidence_gap_summary]
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
                "selected_rows": len(model.selected_record_ids),
                "durable_governance_persistence": "NONE_FOR_BANKED_BASELINE",
            }
        ]
    )
    return model


def render_decisions_and_thesis(st: Any) -> DecisionEpisodeReadModel | None:
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
    try:
        model = build_command_center_read_model()
    except Exception as exc:
        _render_fail_closed(st, title="Operations & Replay", error=exc)
        return None
    st.header("Operations & Replay")
    st.caption(
        "Read-only governance lineage reconstructed from the bounded digest-chained "
        "stream. No durable governance mutation occurs on this historical page."
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
