"""Read-only Command Center over real PIT adapters and projected governance facts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from core.gv_fs0_canonical import canonical_document_bytes
from core.gv_pit.adapters import (
    REAL_MU_OPERATED_MODULE_ID,
    build_real_pit_source_bundle,
)
from core.gv_pit.contracts import canonical_value
from core.gv_pit.governance import govern_real_pit_bundle
from core.gv_pit.read_models import (
    DecisionEpisodeReadModel,
    project_decision_episode,
)
from gv_portfolio_v0.operated_scenarios import (
    OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    get_scenario,
)
from gv_portfolio_v0.operated_storage import (
    confirm_prospective_observation_and_persist,
    ensure_prospective_workspace,
    reject_prospective_observation_and_persist,
    workspace_path,
)
from gv_portfolio_v0.market_packet import build_immutable_market_packet
from gv_portfolio_v0.prospective import (
    operated_rotation_companion,
    preview_runtime_observation,
)
from views.gv_operated_portfolio_workspace import build_book_rows, build_trade_rows


_ACTIVE_PREVIEW_KEY = "gv_command_center_operated_paper_capital_preview"
_ACTIVE_PREVIEW_REQUEST_KEY = (
    "gv_command_center_operated_paper_capital_preview_request"
)
_ACTIVE_PREVIEW_WORKSPACE_KEY = (
    "gv_command_center_operated_paper_capital_preview_workspace"
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


def build_active_command_center_workspace(
    *, root: Path | None = None
) -> dict[str, Any]:
    """Load or bootstrap the single persisted forward-operated paper workspace."""

    return ensure_prospective_workspace(
        root=root,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
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


def _displayed_operated_proposal_binding(
    model: DecisionEpisodeReadModel,
    workspace: Mapping[str, Any],
) -> dict[str, Any]:
    matching = [
        row
        for row in model.proposal_records
        if row.module_id == REAL_MU_OPERATED_MODULE_ID and row.status == "ELIGIBLE"
    ]
    if len(matching) != 1:
        raise ValueError("DISPLAYED_ELIGIBLE_OPERATED_PROPOSAL_REQUIRED")
    row = matching[0]
    return {
        "episode_id": model.episode_id,
        "record_id": row.record_id,
        "proposal_id": row.proposal_id,
        "module_id": row.module_id,
        "module_version": row.module_version,
        "sleeve_id": row.sleeve_id,
        "status": row.status,
        "pit_identity": canonical_value(model.pit_identity),
        "active_book_hash": workspace["book"]["book_hash"],
        "active_certification_id": workspace["certification"]["certification_id"],
        "active_event_count": len(workspace["events"]),
    }


def _render_operated_preview_flow(
    st: Any,
    *,
    workspace: dict[str, Any],
    root: Path | None,
    request: dict[str, Any],
) -> None:
    session = st.session_state
    if st.button("Preview paper-capital decision", key="gv_command_center_preview"):
        try:
            session[_ACTIVE_PREVIEW_KEY] = preview_runtime_observation(
                workspace, request
            )
            session[_ACTIVE_PREVIEW_REQUEST_KEY] = dict(request)
            session[_ACTIVE_PREVIEW_WORKSPACE_KEY] = str(
                workspace_path(
                    root, scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID
                ).absolute()
            )
        except Exception as exc:
            session.pop(_ACTIVE_PREVIEW_KEY, None)
            session.pop(_ACTIVE_PREVIEW_REQUEST_KEY, None)
            session.pop(_ACTIVE_PREVIEW_WORKSPACE_KEY, None)
            st.error(f"Preview rejected: {type(exc).__name__}: {exc}")

    preview = session.get(_ACTIVE_PREVIEW_KEY)
    current_workspace_path = str(
        workspace_path(
            root, scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID
        ).absolute()
    )
    preview_request = session.get(_ACTIVE_PREVIEW_REQUEST_KEY)
    try:
        request_changed = not isinstance(preview_request, Mapping) or (
            canonical_document_bytes(dict(preview_request))
            != canonical_document_bytes(request)
        )
    except (TypeError, ValueError):
        request_changed = True
    preview_is_stale = isinstance(preview, dict) and (
        preview.get("prior_book_hash") != workspace["book"]["book_hash"]
        or preview.get("prior_certification_id")
        != workspace["certification"]["certification_id"]
        or preview.get("prior_event_count") != len(workspace["events"])
        or preview.get("prior_decision_snapshot_id")
        != workspace["current_decision_snapshot"]["decision_snapshot_id"]
        or session.get(_ACTIVE_PREVIEW_WORKSPACE_KEY)
        != current_workspace_path
        or request_changed
    )
    if preview_is_stale:
        session.pop(_ACTIVE_PREVIEW_KEY, None)
        session.pop(_ACTIVE_PREVIEW_REQUEST_KEY, None)
        session.pop(_ACTIVE_PREVIEW_WORKSPACE_KEY, None)
        preview = None
        st.warning("The prior preview is stale and was discarded.")
    if not isinstance(preview, dict):
        return

    transition = preview["transition"]
    st.subheader("Mutation-free paper-capital preview")
    forward_packet = preview["request"].get("forward_operated_packet")
    if isinstance(forward_packet, Mapping):
        market_packet = forward_packet.get("market_packet", {})
        st.table(
            [
                {
                    "proposal_id": preview["proposal_id"],
                    "transition_kind": transition["transition_kind"],
                    "instrument_id": forward_packet["instrument_id"],
                    "target_quantity": forward_packet["target_quantity"],
                    "market_value": market_packet.get("value"),
                    "valid_effective_at": market_packet.get("valid_effective_at"),
                    "content_sha256": market_packet.get("content_sha256"),
                    "source_permission_identity": market_packet.get(
                        "source_permission_identity"
                    ),
                    "authoritative": False,
                }
            ]
        )
    else:
        binding = preview["request"]["displayed_proposal_binding"]
        st.table(
            [
                {
                    "proposal_id": preview["proposal_id"],
                    "transition_kind": transition["transition_kind"],
                    "displayed_record_id": binding["record_id"],
                    "displayed_proposal_id": binding["proposal_id"],
                    "displayed_module": binding["module_id"],
                    "active_book_hash": binding["active_book_hash"],
                    "authoritative": False,
                }
            ]
        )
        st.table(preview["request"]["forward_operated_market_packets"])
    st.table(transition["legs"])
    st.subheader("Resulting book preview")
    st.table(transition["positions_after"])
    st.table(transition["classified_cash_after"])
    st.table(transition["classified_costs_after"])
    st.caption(
        f"book_hash_after=`{transition['book_hash_after']}` · "
        f"cash_after={transition['cash_after']} · costs_after={transition['costs_after']} · "
        f"residual={transition['unexplained_residual']} · authoritative=false"
    )

    if st.button("Confirm paper-capital decision", key="gv_command_center_confirm"):
        try:
            confirm_prospective_observation_and_persist(
                preview,
                root=root,
                scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
            )
        except Exception as exc:
            st.error(f"Confirmation rejected: {type(exc).__name__}: {exc}")
        else:
            session.pop(_ACTIVE_PREVIEW_KEY, None)
            session.pop(_ACTIVE_PREVIEW_REQUEST_KEY, None)
            session.pop(_ACTIVE_PREVIEW_WORKSPACE_KEY, None)
            st.rerun()

    rejection_reason = st.text_area(
        "Rejection rationale",
        key="gv_command_center_rejection_reason",
        placeholder="Explain why this validated proposal must not receive capital authority.",
    )
    if st.button("Reject paper-capital decision", key="gv_command_center_reject"):
        try:
            reject_prospective_observation_and_persist(
                preview,
                rejection_reason,
                root=root,
                scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
            )
        except Exception as exc:
            st.error(f"Rejection failed: {type(exc).__name__}: {exc}")
        else:
            session.pop(_ACTIVE_PREVIEW_KEY, None)
            session.pop(_ACTIVE_PREVIEW_REQUEST_KEY, None)
            session.pop(_ACTIVE_PREVIEW_WORKSPACE_KEY, None)
            st.rerun()


def _render_operated_paper_action(
    st: Any,
    *,
    workspace: dict[str, Any],
    root: Path | None,
    pit_identity: Mapping[str, Any],
) -> None:
    st.subheader("Operate one paper-capital decision")
    st.caption(
        "Owner assertions are content-addressed and bound to the preview. They are not "
        "provider-verified evidence, investment advice, broker authority, or live capital."
    )
    review = workspace["reviews"][0]
    instrument = workspace["instruments"][0]
    st.table(
        [
            {
                "instrument_id": instrument["instrument_id"],
                "symbol": instrument["symbol"],
                "permanent_key": instrument["permanent_key"],
                "current_outcome": review["outcome"],
                "current_target_quantity": review["target_quantity"],
            }
        ]
    )

    evidence_content = st.text_area(
        "Owner evidence content",
        key="gv_command_center_evidence_content",
        placeholder="Enter the evidence exactly as reviewed by the owner.",
    )
    source_locator = st.text_input(
        "Evidence source locator",
        key="gv_command_center_source_locator",
        placeholder="operator://date/source-reference",
    )
    evidence_observed_at = st.text_input(
        "Evidence observed at UTC",
        key="gv_command_center_evidence_observed_at",
        placeholder="2026-08-04T12:01:00.000000Z",
    )
    market_value = st.text_input(
        "Market packet value",
        key="gv_command_center_market_price",
        placeholder="100.00",
    )
    market_valid_at = st.text_input(
        "Market valid/effective at UTC",
        key="gv_command_center_market_observed_at",
        placeholder="2026-08-04T12:00:00.000000Z",
    )
    market_knowledge_at = st.text_input(
        "Market retrieval/knowledge at UTC",
        key="gv_command_center_market_knowledge_at",
        placeholder="2026-08-04T12:00:30.000000Z",
    )
    market_source_permission = st.text_input(
        "Market source/permission identity",
        key="gv_command_center_market_source_identity",
        placeholder="owner-local/permission/manual-v1",
    )
    market_receipt = st.text_area(
        "Market raw bytes or receipt",
        key="gv_command_center_market_receipt",
        placeholder="Immutable receipt or raw observation bytes for this market packet.",
    )
    market_unit = st.text_input(
        "Market unit",
        key="gv_command_center_market_unit",
        value="price",
    )
    market_currency = st.text_input(
        "Market currency",
        key="gv_command_center_market_currency",
        value="USD",
    )
    target_quantity = st.number_input(
        "Paper target quantity",
        min_value=1,
        step=1,
        value=1,
        key="gv_command_center_target_quantity",
    )
    net_score_bps = st.number_input(
        "Owner net score (bps)",
        step=1,
        value=0,
        key="gv_command_center_net_score_bps",
    )
    principal_claim = st.text_area(
        "Principal claim",
        key="gv_command_center_principal_claim",
        placeholder="State the bounded claim supporting this paper target.",
    )
    operator_rationale = st.text_area(
        "Operator rationale",
        key="gv_command_center_operator_rationale",
        placeholder="Explain why this exact target should be previewed.",
    )

    try:
        market_packet = build_immutable_market_packet(
            source_permission_identity=market_source_permission,
            raw_bytes_or_receipt=market_receipt,
            valid_effective_at=market_valid_at,
            retrieval_knowledge_at=market_knowledge_at,
            permanent_instrument_identity=str(instrument["permanent_key"]),
            instrument_id=str(review["instrument_id"]),
            value=market_value,
            unit=market_unit,
            currency=market_currency,
        )
    except Exception:
        market_packet = {
            "instrument_id": review["instrument_id"],
            "permanent_instrument_identity": instrument["permanent_key"],
            "value": market_value,
            "valid_effective_at": market_valid_at,
            "retrieval_knowledge_at": market_knowledge_at,
            "source_permission_identity": market_source_permission,
            "raw_bytes_or_receipt": market_receipt,
            "unit": market_unit,
            "currency": market_currency,
        }

    request = {
        "content": evidence_content,
        "locator": source_locator,
        "observed_at": evidence_observed_at,
        "pit_identity": dict(pit_identity),
        "market_instrument_id": review["instrument_id"],
        "market_packet": market_packet,
        "review_updates": [
            {
                "instrument_id": review["instrument_id"],
                "outcome": "ADMIT",
                "net_score_bps": int(net_score_bps),
                "target_quantity": str(int(target_quantity)),
                "principal_claim": principal_claim,
            }
        ],
        "operator_rationale": operator_rationale,
    }
    _render_operated_preview_flow(
        st,
        workspace=workspace,
        root=root,
        request=request,
    )


def _render_operated_rotation_action(
    st: Any,
    *,
    workspace: dict[str, Any],
    root: Path | None,
    model: DecisionEpisodeReadModel,
) -> None:
    funded_positions = [
        row for row in workspace["book"]["positions"] if int(row["quantity"]) > 0
    ]
    if len(funded_positions) != 1:
        st.error("Rotation requires exactly one certified funded source position.")
        return
    source_position = funded_positions[0]
    source_review = next(
        row
        for row in workspace["reviews"]
        if row["instrument_id"] == source_position["instrument_id"]
    )
    source_instrument = next(
        row
        for row in workspace["instruments"]
        if row["instrument_id"] == source_position["instrument_id"]
    )
    companion = operated_rotation_companion(workspace)
    companion_review = companion["review"]
    companion_instrument = companion["instrument"]
    binding = _displayed_operated_proposal_binding(model, workspace)

    st.subheader("Operate one proposal-bound SELL+BUY rotation")
    st.caption(
        "This repeatability action uses one displayed eligible proposal, the certified "
        "active book, and two owner-identified market observations. It proves operation "
        "and replay only; it does not prove provider quality, alpha, or realized value."
    )
    st.table(
        [
            {
                "displayed_record_id": binding["record_id"],
                "displayed_proposal_id": binding["proposal_id"],
                "module": binding["module_id"],
                "status": binding["status"],
                "active_book_hash": binding["active_book_hash"],
            }
        ]
    )
    st.table(
        [
            {
                "role": "REDUCE",
                "symbol": source_instrument["symbol"],
                "instrument_id": source_instrument["instrument_id"],
                "current_quantity": source_position["quantity"],
                "current_price": source_position["valuation_price"],
            },
            {
                "role": "FUND",
                "symbol": companion_instrument["symbol"],
                "instrument_id": companion_instrument["instrument_id"],
                "current_quantity": "0",
                "current_price": companion_review["reference_price"],
            },
        ]
    )

    evidence_content = st.text_area(
        "Rotation evidence content",
        key="gv_command_center_rotation_evidence_content",
        placeholder="State the owner-reviewed evidence for this bounded rotation.",
    )
    source_locator = st.text_input(
        "Rotation evidence source locator",
        key="gv_command_center_rotation_source_locator",
        placeholder="operator://date/mu-merid/rotation",
    )
    evidence_observed_at = st.text_input(
        "Rotation evidence observed at UTC",
        key="gv_command_center_rotation_evidence_observed_at",
        placeholder="2026-08-04T13:01:00.000000Z",
    )

    source_market_price = st.text_input(
        f"{source_instrument['symbol']} market packet value",
        key="gv_command_center_rotation_source_market_price",
        value=str(source_position["valuation_price"]),
    )
    source_market_observed_at = st.text_input(
        f"{source_instrument['symbol']} market valid/effective at UTC",
        key="gv_command_center_rotation_source_market_observed_at",
        placeholder="2026-08-04T13:00:00.000000Z",
    )
    source_market_knowledge_at = st.text_input(
        f"{source_instrument['symbol']} market retrieval/knowledge at UTC",
        key="gv_command_center_rotation_source_market_knowledge_at",
        placeholder="2026-08-04T13:00:30.000000Z",
    )
    source_market_source_identity = st.text_input(
        f"{source_instrument['symbol']} market source/permission identity",
        key="gv_command_center_rotation_source_market_source_identity",
        placeholder="owner-local/permission/manual-v1",
    )
    source_market_receipt = st.text_area(
        f"{source_instrument['symbol']} market raw bytes or receipt",
        key="gv_command_center_rotation_source_market_receipt",
        placeholder="Immutable receipt for the source market packet.",
    )
    source_target_quantity = st.number_input(
        f"{source_instrument['symbol']} reduced target quantity",
        min_value=0,
        max_value=max(int(source_position["quantity"]) - 1, 0),
        value=max(int(source_position["quantity"]) - 1, 0),
        step=1,
        key="gv_command_center_rotation_source_target_quantity",
    )
    source_net_score_bps = st.number_input(
        f"{source_instrument['symbol']} owner net score (bps)",
        step=1,
        value=int(source_review["net_score_bps"]),
        key="gv_command_center_rotation_source_net_score_bps",
    )
    source_principal_claim = st.text_area(
        f"{source_instrument['symbol']} principal claim",
        key="gv_command_center_rotation_source_principal_claim",
        placeholder="State why the certified source position should be reduced.",
    )

    companion_market_price = st.text_input(
        f"{companion_instrument['symbol']} market packet value",
        key="gv_command_center_rotation_companion_market_price",
        value=str(companion_review["reference_price"]),
    )
    companion_market_observed_at = st.text_input(
        f"{companion_instrument['symbol']} market valid/effective at UTC",
        key="gv_command_center_rotation_companion_market_observed_at",
        placeholder="2026-08-04T13:00:00.000000Z",
    )
    companion_market_knowledge_at = st.text_input(
        f"{companion_instrument['symbol']} market retrieval/knowledge at UTC",
        key="gv_command_center_rotation_companion_market_knowledge_at",
        placeholder="2026-08-04T13:00:30.000000Z",
    )
    companion_market_source_identity = st.text_input(
        f"{companion_instrument['symbol']} market source/permission identity",
        key="gv_command_center_rotation_companion_market_source_identity",
        placeholder="owner-local/permission/manual-v1",
    )
    companion_market_receipt = st.text_area(
        f"{companion_instrument['symbol']} market raw bytes or receipt",
        key="gv_command_center_rotation_companion_market_receipt",
        placeholder="Immutable receipt for the companion market packet.",
    )
    companion_target_quantity = st.number_input(
        f"{companion_instrument['symbol']} funded target quantity",
        min_value=1,
        value=1,
        step=1,
        key="gv_command_center_rotation_companion_target_quantity",
    )
    companion_net_score_bps = st.number_input(
        f"{companion_instrument['symbol']} owner net score (bps)",
        step=1,
        value=int(companion_review["net_score_bps"]),
        key="gv_command_center_rotation_companion_net_score_bps",
    )
    companion_principal_claim = st.text_area(
        f"{companion_instrument['symbol']} principal claim",
        key="gv_command_center_rotation_companion_principal_claim",
        placeholder="State why the governed companion should receive bounded funding.",
    )
    operator_rationale = st.text_area(
        "Rotation operator rationale",
        key="gv_command_center_rotation_operator_rationale",
        placeholder="Explain why this exact SELL+BUY transition should be previewed.",
    )

    def _rotation_packet(
        *,
        instrument: Mapping[str, Any],
        value: str,
        valid_at: str,
        knowledge_at: str,
        source_permission: str,
        receipt: str,
    ) -> dict[str, str]:
        try:
            return build_immutable_market_packet(
                source_permission_identity=source_permission,
                raw_bytes_or_receipt=receipt,
                valid_effective_at=valid_at,
                retrieval_knowledge_at=knowledge_at,
                permanent_instrument_identity=str(instrument["permanent_key"]),
                instrument_id=str(instrument["instrument_id"]),
                value=value,
            )
        except Exception:
            return {
                "instrument_id": str(instrument["instrument_id"]),
                "permanent_instrument_identity": str(instrument["permanent_key"]),
                "value": value,
                "valid_effective_at": valid_at,
                "retrieval_knowledge_at": knowledge_at,
                "source_permission_identity": source_permission,
                "raw_bytes_or_receipt": receipt,
                "unit": "price",
                "currency": "USD",
            }

    request = {
        "content": evidence_content,
        "locator": source_locator,
        "observed_at": evidence_observed_at,
        "pit_identity": dict(binding["pit_identity"]),
        "displayed_proposal_binding": dict(binding),
        "forward_operated_market_packets": [
            _rotation_packet(
                instrument=source_instrument,
                value=source_market_price,
                valid_at=source_market_observed_at,
                knowledge_at=source_market_knowledge_at,
                source_permission=source_market_source_identity,
                receipt=source_market_receipt,
            ),
            _rotation_packet(
                instrument=companion_instrument,
                value=companion_market_price,
                valid_at=companion_market_observed_at,
                knowledge_at=companion_market_knowledge_at,
                source_permission=companion_market_source_identity,
                receipt=companion_market_receipt,
            ),
        ],
        "review_updates": [
            {
                "instrument_id": source_review["instrument_id"],
                "outcome": "ADMIT",
                "net_score_bps": int(source_net_score_bps),
                "target_quantity": str(int(source_target_quantity)),
                "principal_claim": source_principal_claim,
            },
            {
                "instrument_id": companion_review["instrument_id"],
                "outcome": "ADMIT",
                "net_score_bps": int(companion_net_score_bps),
                "target_quantity": str(int(companion_target_quantity)),
                "principal_claim": companion_principal_claim,
            },
        ],
        "operator_rationale": operator_rationale,
    }
    _render_operated_preview_flow(
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
    """Render persisted paper authority plus the banked read-only PIT comparison."""

    try:
        model = build_command_center_read_model()
        workspace = build_active_command_center_workspace(root=root)
    except Exception as exc:
        _render_fail_closed(st, title="Command Center", error=exc)
        return None
    identity = model.pit_identity
    market_context = identity.market_snapshot_id
    scenario = get_scenario(OPERATED_PAPER_CAPITAL_SCENARIO_ID)

    st.header("Command Center")
    st.caption(
        "Active persisted paper authority first; banked no-market comparison second. "
        "The bounded entry and one proposal-bound SELL+BUY rotation reuse the existing "
        "preview, disposition, atomic persistence, certification, and exact replay path."
    )

    st.subheader("Active certified paper workspace")
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
                "prospective_episode_count": workspace[
                    "prospective_episode_count"
                ],
                "unexplained_residual": workspace["book"][
                    "unexplained_residual"
                ],
            }
        ]
    )
    if workspace["prospective_episode_history"]:
        st.subheader("Operated episode lineage")
        st.table(workspace["prospective_episode_history"])
    if workspace["fills"]:
        st.subheader("Certified paper fills")
        st.table(build_trade_rows(workspace))

    funded_positions = [
        row for row in workspace["book"]["positions"] if int(row["quantity"]) > 0
    ]
    if not funded_positions:
        _render_operated_paper_action(
            st,
            workspace=workspace,
            root=root,
            pit_identity=canonical_value(identity),
        )
    elif len(funded_positions) == 1 and workspace["prospective_episode_count"] == 1:
        st.success(
            "The bounded cash-funded entry has been operated, persisted, certified, "
            "and reopened from active authority."
        )
        _render_operated_rotation_action(
            st,
            workspace=workspace,
            root=root,
            model=model,
        )
    else:
        st.success(
            "The proposal-bound SELL+BUY rotation has been operated, persisted, "
            "certified, and reopened from active authority."
        )

    st.subheader("Banked no-market comparison baseline")
    st.caption(
        "This closed Slice 1 comparison remains immutable historical evidence. It is "
        "not projected as the current market-aware active book."
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

    baseline_capital_col, baseline_cash_col, proposal_col = st.columns(3)
    baseline_capital_col.metric("Baseline NAV", format(model.certified_nav, "f"))
    baseline_cash_col.metric(
        "Baseline classified cash",
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
                "durable_governance_persistence": "NONE_FOR_BANKED_BASELINE",
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
