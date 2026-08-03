"""Streamlit surface for operator-supplied prospective paper observations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from core.gv_fs0_canonical import canonical_document_bytes
from core.gv_v2_mu_nvda_reconciliation import (
    MuNvdaReconciliationError,
    load_verified_mu_nvda_reconciliation,
)
from core.gv_v2_mu_nvda_shadow_decision import (
    MuNvdaShadowDecisionError,
    load_mu_nvda_shadow_decision,
    verify_mu_nvda_shadow_decision,
)
from gv_portfolio_v0.operated_scenarios import (
    PROSPECTIVE_25_SCENARIO_ID,
    REAL_MU_PROSPECTIVE_SCENARIO_ID,
    get_scenario,
)
from gv_portfolio_v0.operated_storage import (
    confirm_prospective_observation_and_persist,
    ensure_prospective_workspace,
    reject_prospective_observation_and_persist,
)
from gv_portfolio_v0.prospective import (
    ProspectiveOperationError,
    preview_runtime_observation,
)
from views.gv_operated_portfolio_workspace import (
    build_book_rows,
    build_review_rows,
)

_PREVIEW_KEY = "gv_prospective_pending_preview"


def _decision_free_evidence_identity(
    reconciliation: Mapping[str, Any],
) -> dict[str, Any]:
    """Project only the immutable source evidence shared by both decisions."""

    corroboration = reconciliation.get("corroboration") or []
    mu_statement_ids = sorted(
        {
            str(statement_id)
            for row in corroboration
            for statement_id in row.get("mu_statement_ids", [])
        }
    )
    nvda_fact_ids = sorted(
        {
            str(fact_id)
            for row in corroboration
            for fact_id in row.get("nvda_fact_ids", [])
        }
    )
    bindings = reconciliation.get("source_bindings") or {}
    return {
        "source_families": list(reconciliation.get("source_families") or []),
        "source_bindings": {
            "mu_claim_evaluation_hash": bindings.get("mu_claim_evaluation_hash"),
            "nvda_fact_set_hash": bindings.get("nvda_fact_set_hash"),
        },
        "mu_statement_ids": mu_statement_ids,
        "nvda_fact_ids": nvda_fact_ids,
    }


def _real_mu_shadow_context() -> dict[str, Any]:
    """Load and bind the independent shadow to the exact operated evidence."""

    reconciliation = load_verified_mu_nvda_reconciliation()
    shadow = load_mu_nvda_shadow_decision()
    verify_mu_nvda_shadow_decision(shadow)
    operated_identity = _decision_free_evidence_identity(reconciliation)
    if canonical_document_bytes(operated_identity) != canonical_document_bytes(
        shadow["evidence_identity"]
    ):
        raise ProspectiveOperationError("SHADOW_OPERATED_EVIDENCE_MISMATCH")
    return {
        "reconciliation": reconciliation,
        "shadow": shadow,
        "evidence_identity": operated_identity,
    }


def _comparison_reason(operated_outcome: str, shadow_outcome: str) -> str:
    if operated_outcome == shadow_outcome:
        return (
            "No material disagreement: both treat missing Micron-specific physical "
            "supply persistence evidence as insufficient for a position."
        )
    if operated_outcome == "ADMIT" and shadow_outcome == "ABSTAIN":
        return (
            "The operated proposal admits MU despite the unresolved physical-supply "
            "discriminator; the shadow treats that gap as decision-limiting."
        )
    if operated_outcome == "REJECT" and shadow_outcome == "ABSTAIN":
        return (
            "The operated proposal treats the evidence as disqualifying; the shadow sees "
            "insufficient proof, not adverse evidence."
        )
    return (
        f"The operated proposal returns {operated_outcome}, while the independent shadow "
        f"returns {shadow_outcome} from the same immutable evidence."
    )


def _real_mu_comparison_row(
    *,
    workspace: Mapping[str, Any],
    shadow_context: Mapping[str, Any],
    proposal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    current_review = workspace["reviews"][0]
    operated_review = current_review
    operator_final_decision = "NOT_YET_RECORDED"
    if proposal is not None:
        operated_review = proposal["review_changes"][0]["after"]
        operator_final_decision = "PENDING_CONFIRM_OR_REJECT"
    elif workspace["prospective_episode_history"]:
        last_episode = workspace["prospective_episode_history"][-1]
        if last_episode["disposition"] == "CONFIRMED":
            operator_final_decision = f"CONFIRMED_{current_review['outcome']}"
            operated_review = workspace["prospective_proposals"][-1]["review_changes"][
                0
            ]["after"]
        else:
            rejected = workspace["rejected_proposals"][-1]["prospective_proposal"]
            operated_review = rejected["review_changes"][0]["after"]
            operator_final_decision = (
                f"REJECTED_PROPOSAL_RETAINED_{current_review['outcome']}"
            )

    shadow = shadow_context["shadow"]
    operated_outcome = str(operated_review["outcome"])
    shadow_outcome = str(shadow["outcome"])
    return {
        "operated_decision": operated_outcome,
        "operated_principal_claim": operated_review["living_thesis_lite"][
            "principal_claim"
        ],
        "shadow_decision": shadow_outcome,
        "shadow_principal_claim": shadow["principal_claim"],
        "agreement": operated_outcome == shadow_outcome,
        "reason_for_disagreement": _comparison_reason(
            operated_outcome, shadow_outcome
        ),
        "shadow_missing_discriminator": shadow["missing_discriminator"],
        "shadow_falsifier": shadow["falsifier"],
        "operator_final_decision": operator_final_decision,
        "same_immutable_evidence": True,
    }


def _render_real_mu_evidence_and_comparison(
    st: Any,
    *,
    workspace: Mapping[str, Any],
    shadow_context: Mapping[str, Any],
    proposal: Mapping[str, Any] | None = None,
) -> None:
    reconciliation = shadow_context["reconciliation"]
    identity = shadow_context["evidence_identity"]
    instrument = workspace["instruments"][0]

    st.subheader("Immutable source evidence")
    st.table(
        [
            {
                "subject": reconciliation["subject"],
                "source_families": len(identity["source_families"]),
                "mu_statements": len(identity["mu_statement_ids"]),
                "nvda_facts": len(identity["nvda_fact_ids"]),
                "corroboration": reconciliation["corroboration_status"],
                "contradiction": reconciliation["contradiction_status"],
                "reconciliation_hash": reconciliation["reconciliation_hash"],
            }
        ]
    )
    st.table(
        [
            {
                "claim": row["claim"],
                "support": row["support"],
                "mu_statement_ids": ", ".join(row["mu_statement_ids"]),
                "nvda_fact_ids": ", ".join(row["nvda_fact_ids"]),
            }
            for row in reconciliation["corroboration"]
        ]
    )
    st.caption(f"missing_discriminator={reconciliation['missing_discriminator']}")
    st.subheader("Instrument identity")
    st.table(
        [
            {
                "symbol": instrument["symbol"],
                "name": instrument["name"],
                "namespace": instrument["namespace"],
                "permanent_key": instrument["permanent_key"],
                "security_class": instrument["security_class"],
            }
        ]
    )
    st.subheader("Same-evidence decision comparison")
    comparison = _real_mu_comparison_row(
        workspace=workspace,
        shadow_context=shadow_context,
        proposal=proposal,
    )
    st.table([comparison])
    st.caption(
        f"operator_final_decision={comparison['operator_final_decision']} · "
        f"same_immutable_evidence=true · shadow_reads_portfolio_decision=false · "
        f"shadow_mutation_authorized=false · "
        f"shadow_decision_hash=`{shadow_context['shadow']['shadow_decision_hash']}`"
    )


def _review_for_symbol(workspace: dict[str, Any], symbol: str) -> dict[str, Any]:
    for review in workspace["reviews"]:
        if review["symbol"] == symbol:
            return review
    raise ProspectiveOperationError("OBSERVATION_INSTRUMENT_UNKNOWN")


def _review_update_inputs(
    st: Any,
    review: dict[str, Any],
    *,
    key_prefix: str,
    label_prefix: str,
) -> dict[str, Any]:
    symbol = review["symbol"]
    key_base = f"gv_prospective_{key_prefix}" if key_prefix else "gv_prospective"
    outcome = st.selectbox(
        f"{label_prefix}Instrument review outcome",
        ["ADMIT", "REJECT", "ABSTAIN"],
        index=["ADMIT", "REJECT", "ABSTAIN"].index(review["outcome"]),
        key=f"{key_base}_outcome_{symbol}",
    )
    score = st.number_input(
        f"{label_prefix}Proposed net score (bps)",
        value=int(review["net_score_bps"]),
        step=1,
        key=f"{key_base}_score_{symbol}",
    )
    quantity = st.number_input(
        f"{label_prefix}Proposed target quantity",
        value=int(review["target_quantity"]),
        min_value=0,
        step=1,
        key=f"{key_base}_quantity_{symbol}",
    )
    principal_claim = st.text_area(
        f"{label_prefix}Updated principal claim",
        value=review["living_thesis_lite"]["principal_claim"],
        key=f"{key_base}_claim_{symbol}",
    )
    return {
        "instrument_id": review["instrument_id"],
        "outcome": outcome,
        "net_score_bps": int(score),
        "target_quantity": str(int(quantity)),
        "principal_claim": principal_claim,
    }


def _preview_rows(proposal: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "symbol": change["before"]["symbol"],
            "outcome_before": change["before"]["outcome"],
            "outcome_after": change["after"]["outcome"],
            "score_before_bps": change["before"]["net_score_bps"],
            "score_after_bps": change["after"]["net_score_bps"],
            "quantity_before": change["before"]["target_quantity"],
            "quantity_after": change["after"]["target_quantity"],
            "economics_changed": proposal["economics_changed"],
            "content_sha256": proposal["evidence"]["content_sha256"],
        }
        for change in proposal["review_changes"]
    ]


def render_prospective_paper_workspace(
    st: Any,
    *,
    root: Path | None = None,
    scenario_id: str = PROSPECTIVE_25_SCENARIO_ID,
) -> dict[str, Any]:
    """Render the two-action preview/confirm Slice A operator flow."""

    try:
        workspace = ensure_prospective_workspace(
            root=root, scenario_id=scenario_id
        )
        scenario = get_scenario(scenario_id)
        st.header(scenario["title"])
        st.caption(
            f"{scenario['claim_boundary']} · operator-supplied observations · "
            "mutation-free preview · explicit confirmation."
        )
        st.success("Certified paper decision ready for runtime observation.")
        st.caption(
            f"status=`{workspace['status']}` · instruments={len(workspace['instruments'])} · "
            f"episodes={workspace['prospective_episode_count']} · "
            f"operator_actions={workspace['operator_action_count']} · "
            f"NAV={workspace['book']['nav']} · residual={workspace['book']['unexplained_residual']}"
        )

        st.subheader("Current portfolio book")
        st.table(build_book_rows(workspace))
        st.caption(f"book_hash=`{workspace['book']['book_hash']}`")

        st.subheader("Current instrument reviews")
        st.table(build_review_rows(workspace))

        shadow_context: dict[str, Any] | None = None
        if scenario_id == REAL_MU_PROSPECTIVE_SCENARIO_ID:
            shadow_context = _real_mu_shadow_context()
            _render_real_mu_evidence_and_comparison(
                st,
                workspace=workspace,
                shadow_context=shadow_context,
            )

        symbols = [row["symbol"] for row in workspace["reviews"]]
        selected_symbol = st.selectbox(
            "Observed instrument",
            symbols,
            key="gv_prospective_instrument_symbol",
        )
        selected_review = _review_for_symbol(workspace, selected_symbol)
        instrument_id = selected_review["instrument_id"]

        exact_source_evidence = (
            workspace["evidence_references"][0]
            if scenario_id == REAL_MU_PROSPECTIVE_SCENARIO_ID
            else None
        )
        content = st.text_area(
            "Observation content",
            value=(
                exact_source_evidence["content"]
                if exact_source_evidence is not None
                else ""
            ),
            key=f"gv_prospective_content_{selected_symbol}",
            placeholder="Enter the new observation exactly as reviewed by the operator.",
            disabled=exact_source_evidence is not None,
        )
        locator = st.text_input(
            "Source locator",
            value=(
                exact_source_evidence["locator"]
                if exact_source_evidence is not None
                else ""
            ),
            key=f"gv_prospective_locator_{selected_symbol}",
            placeholder="operator://date/source-reference",
            disabled=exact_source_evidence is not None,
        )
        if exact_source_evidence is not None:
            st.caption(
                "Exact banked evidence is locked for the same-evidence comparison; "
                "the operator controls only the review, rationale, and final disposition."
            )
        observed_at = st.text_input(
            "Observed at UTC",
            key=f"gv_prospective_observed_at_{selected_symbol}",
            placeholder="2026-10-01T12:00:00.000000Z",
        )
        review_updates = [
            _review_update_inputs(
                st,
                selected_review,
                key_prefix="",
                label_prefix="",
            )
        ]
        include_second = st.checkbox(
            "Add second instrument review proposal",
            key="gv_prospective_add_second_review",
        )
        if include_second:
            companion_symbols = [
                symbol for symbol in symbols if symbol != selected_symbol
            ]
            companion_symbol = st.selectbox(
                "Second observed instrument",
                companion_symbols,
                key="gv_prospective_second_instrument_symbol",
            )
            companion_review = _review_for_symbol(workspace, companion_symbol)
            review_updates.append(
                _review_update_inputs(
                    st,
                    companion_review,
                    key_prefix="secondary",
                    label_prefix="Second instrument — ",
                )
            )
        rationale = st.text_area(
            "Operator rationale",
            key=f"gv_prospective_rationale_{selected_symbol}",
            placeholder="Explain why the proposed review preserves portfolio economics.",
        )

        if st.button(
            "Preview prospective observation",
            key="gv_prospective_preview",
        ):
            request = {
                "content": content,
                "locator": locator,
                "observed_at": observed_at,
                "review_updates": review_updates,
                "operator_rationale": rationale,
            }
            st.session_state[_PREVIEW_KEY] = preview_runtime_observation(
                workspace, request
            )

        preview = st.session_state.get(_PREVIEW_KEY)
        if isinstance(preview, dict):
            st.subheader("Mutation-free preview")
            st.table(_preview_rows(preview))
            st.info(preview["changed_why"]["reason"])
            if shadow_context is not None:
                _render_real_mu_evidence_and_comparison(
                    st,
                    workspace=workspace,
                    shadow_context=shadow_context,
                    proposal=preview,
                )
            st.caption(
                f"proposal_id=`{preview['proposal_id']}` · "
                f"prior_event_count={preview['prior_event_count']} · "
                f"change_type={preview['changed_why']['change_type']} · "
                f"orders_created={preview['changed_why']['orders_created']} · "
                "authoritative=false"
            )
            if preview.get("transition"):
                st.subheader("Proposed transition legs")
                st.table(preview["transition"]["legs"])
                st.caption(
                    "transition_sides="
                    + ",".join(
                        row["side"] for row in preview["transition"]["legs"]
                    )
                )
            if st.button(
                "Confirm prospective observation",
                key="gv_prospective_confirm",
            ):
                workspace = confirm_prospective_observation_and_persist(
                    preview,
                    root=root,
                    scenario_id=scenario_id,
                )
                st.session_state.pop(_PREVIEW_KEY, None)
                st.success("Prospective observation confirmed and certified append-only.")
            rejection_reason = st.text_area(
                "Rejection rationale",
                key="gv_prospective_rejection_reason",
                placeholder=(
                    "Explain why this validated proposal must not become decision authority."
                ),
            )
            if st.button(
                "Reject prospective observation",
                key="gv_prospective_reject",
            ):
                workspace = reject_prospective_observation_and_persist(
                    preview,
                    rejection_reason,
                    root=root,
                    scenario_id=scenario_id,
                )
                st.session_state.pop(_PREVIEW_KEY, None)
                st.success("Prospective proposal rejected and certified without authority change.")

        if workspace["prospective_episode_count"]:
            st.subheader("Prospective episode history")
            st.table(workspace["prospective_episode_history"])
            if workspace["observations"]:
                st.subheader("Confirmed prospective episodes")
                st.table(workspace["observations"])
            if workspace["rejected_proposals"]:
                st.subheader("Rejected prospective proposals")
                st.table(
                    [
                        {
                            "proposal_id": row["proposal_id"],
                            "rejected_at": row["rejected_at"],
                            "rejection_reason": row["rejection_reason"],
                        }
                        for row in workspace["rejected_proposals"]
                    ]
                )
            last_episode = workspace["prospective_episode_history"][-1]
            st.caption(
                f"episodes={workspace['prospective_episode_count']} · "
                f"operator_actions={workspace['operator_action_count']} · "
                f"last_disposition={last_episode['disposition']} · "
                f"certification=`{workspace['certification']['certification_id']}` · "
                f"lineage_depth={len(workspace['certification_history'])} · "
                f"book_hash=`{workspace['book']['book_hash']}`"
            )
            if last_episode["disposition"] == "REJECTED":
                st.caption(
                    f"rejection_reason={last_episode['rejection_reason']} · "
                    "authority_changed=False · holdings_changed=False · "
                    "cash_changed=False · orders_created=0"
                )
            elif workspace.get("changed_why"):
                st.subheader("Changed why")
                st.table([workspace["changed_why"]])
                if workspace["changed_why"].get("transition_legs"):
                    st.subheader("Confirmed transition legs")
                    st.table(workspace["changed_why"]["transition_legs"])
                    st.caption(
                        "transition_sides="
                        + ",".join(
                            row["side"]
                            for row in workspace["changed_why"]["transition_legs"]
                        )
                    )
                st.caption(
                    f"change_type={workspace['changed_why']['change_type']} · "
                    f"holdings_changed={workspace['changed_why']['holdings_changed']} · "
                    f"cash_changed={workspace['changed_why']['cash_changed']} · "
                    f"orders_created={workspace['changed_why']['orders_created']}"
                )
            if shadow_context is not None:
                _render_real_mu_evidence_and_comparison(
                    st,
                    workspace=workspace,
                    shadow_context=shadow_context,
                )
        return workspace
    except (ProspectiveOperationError, MuNvdaReconciliationError, MuNvdaShadowDecisionError) as exc:
        st.error("Prospective paper operation refused invalid authority.")
        st.caption(f"Authority refused: {exc}")
        raise
