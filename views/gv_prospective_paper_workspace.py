"""Streamlit surface for operator-supplied prospective paper observations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gv_portfolio_v0.operated_scenarios import PROSPECTIVE_25_SCENARIO_ID
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
        st.header("GV Prospective Paper Baseline 25")
        st.caption(
            "Accepted 25-security certified baseline · operator-supplied observations · "
            "mutation-free preview · explicit confirmation · no provider, broker, or live capital."
        )
        st.success(
            "Certified initial portfolio ready for runtime observation."
        )
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

        symbols = [row["symbol"] for row in workspace["reviews"]]
        selected_symbol = st.selectbox(
            "Observed instrument",
            symbols,
            key="gv_prospective_instrument_symbol",
        )
        selected_review = _review_for_symbol(workspace, selected_symbol)
        instrument_id = selected_review["instrument_id"]

        content = st.text_area(
            "Observation content",
            key=f"gv_prospective_content_{selected_symbol}",
            placeholder="Enter the new observation exactly as reviewed by the operator.",
        )
        locator = st.text_input(
            "Source locator",
            key=f"gv_prospective_locator_{selected_symbol}",
            placeholder="operator://date/source-reference",
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
        return workspace
    except ProspectiveOperationError as exc:
        st.error("Prospective paper operation refused invalid authority.")
        st.caption(f"Authority refused: {exc}")
        raise
