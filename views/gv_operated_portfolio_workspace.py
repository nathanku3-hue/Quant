"""Shared summary-first Streamlit surface for operated-portfolio scenarios."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Protocol

from gv_portfolio_v0.operated import (
    OperatedPortfolioError,
    STATUS_DRAFT,
    STATUS_FUNDED,
    STATUS_NO_CHANGE,
    STATUS_TRANSITION,
)
from gv_portfolio_v0.operated_scenarios import DEFAULT_SCENARIO_ID, get_scenario
from gv_portfolio_v0.operated_storage import (
    admit_no_change_and_persist,
    append_correction_and_persist,
    authorize_transition_and_persist,
    confirm_and_persist,
    ensure_workspace,
)


class WorkspaceRenderer(Protocol):
    def header(self, body: str) -> Any: ...
    def subheader(self, body: str) -> Any: ...
    def caption(self, body: str) -> Any: ...
    def table(self, data: Any) -> Any: ...
    def info(self, body: str) -> Any: ...
    def warning(self, body: str) -> Any: ...
    def success(self, body: str) -> Any: ...
    def error(self, body: str) -> Any: ...
    def button(self, label: str, key: str | None = None) -> bool: ...


def build_review_rows(workspace: Mapping[str, Any]) -> list[dict[str, Any]]:
    funded = {
        row["instrument_id"]
        for row in workspace["book"]["positions"]
        if int(row["quantity"]) > 0
    }
    return [
        {
            "symbol": row["symbol"],
            "cluster": row["economic_cluster"],
            "outcome": row["outcome"],
            "net_score_bps": row["net_score_bps"],
            "target_quantity": row["target_quantity"],
            "funded_now": row["instrument_id"] in funded,
            "thesis": row["living_thesis_lite"]["principal_claim"],
            "evidence_count": len(
                row["living_thesis_lite"]["evidence_reference_ids"]
            ),
        }
        for row in workspace["reviews"]
    ]


def build_cluster_rows(workspace: Mapping[str, Any]) -> list[dict[str, Any]]:
    reviews = build_review_rows(workspace)
    clusters = sorted({row["cluster"] for row in reviews})
    return [
        {
            "cluster": cluster,
            "security_count": sum(row["cluster"] == cluster for row in reviews),
            "admit_count": sum(
                row["cluster"] == cluster and row["outcome"] == "ADMIT"
                for row in reviews
            ),
            "funded_count": sum(
                row["cluster"] == cluster and row["funded_now"] for row in reviews
            ),
            "highest_score_bps": max(
                row["net_score_bps"]
                for row in reviews
                if row["cluster"] == cluster
            ),
        }
        for cluster in clusters
    ]


def build_exception_rows(workspace: Mapping[str, Any]) -> list[dict[str, Any]]:
    changed_symbols: set[str] = set()
    changed_why = workspace.get("changed_why") or {}
    for key in ("reduced", "funded_or_increased"):
        row = changed_why.get(key)
        if isinstance(row, Mapping) and isinstance(row.get("symbol"), str):
            changed_symbols.add(row["symbol"])
    rows = build_review_rows(workspace)
    return [
        row
        for row in rows
        if row["funded_now"]
        or row["symbol"] in changed_symbols
        or row["outcome"] == "REJECT"
    ]


def build_book_rows(workspace: Mapping[str, Any]) -> list[dict[str, str]]:
    symbols = {
        row["instrument_id"]: row["symbol"] for row in workspace["instruments"]
    }
    return [
        {
            "symbol": symbols[row["instrument_id"]],
            "quantity": row["quantity"],
            "valuation_price": row["valuation_price"] or "PENDING",
            "market_value": row["market_value"] or "PENDING",
        }
        for row in workspace["book"]["positions"]
        if int(row["quantity"]) > 0
    ]


def build_trade_rows(workspace: Mapping[str, Any]) -> list[dict[str, str]]:
    symbols = {
        row["instrument_id"]: row["symbol"] for row in workspace["instruments"]
    }
    return [
        {
            "symbol": symbols[row["instrument_id"]],
            "side": row["side"],
            "quantity": row["quantity"],
            "price": row["price"],
            "fee": row["fee"],
            "fill_id": row["fill_id"],
        }
        for row in workspace["fills"]
    ]


def _render_status(st: WorkspaceRenderer, workspace: Mapping[str, Any]) -> None:
    status = workspace["status"]
    instrument_count = len(workspace["instruments"])
    if status == STATUS_DRAFT:
        st.warning(
            f"Review complete; one {instrument_count}-security portfolio awaits confirmation."
        )
    else:
        st.success(f"Persisted and replay-certified: {status}")
    st.caption(
        f"status=`{status}` · instruments={instrument_count} · portfolio_count=1 · "
        f"NAV={workspace['book']['nav']} · cash={workspace['book']['total_cash']} · "
        f"costs={workspace['book']['total_costs']} · residual={workspace['book']['unexplained_residual']}"
    )
    st.info(workspace["explanation"])


def render_operated_portfolio_workspace(
    st: WorkspaceRenderer,
    *,
    root: Path | None = None,
    scenario_id: str = DEFAULT_SCENARIO_ID,
) -> dict[str, Any]:
    scenario = get_scenario(scenario_id)
    st.header(scenario["title"])
    st.caption(
        "One portfolio · permanent instrument identities · individually owned evidence and theses · "
        "BUY and SELL/REDUCE paper execution · exact replay. No provider, broker, alpha, or live-capital claim."
    )
    try:
        workspace = ensure_workspace(root=root, scenario_id=scenario_id)
        st.subheader("Portfolio and cluster summary")
        cluster_rows = build_cluster_rows(workspace)
        st.table(cluster_rows)
        st.caption(
            f"clusters={len(cluster_rows)} · securities={len(workspace['instruments'])} · "
            f"required_operator_actions<=4 · per_security_confirmations=0"
        )

        st.subheader("Exceptions and funded priorities")
        exception_rows = build_exception_rows(workspace)
        st.table(exception_rows)
        outcome_counts = Counter(row["outcome"] for row in workspace["reviews"])
        st.caption(
            "outcomes="
            + ",".join(
                f"{key}:{outcome_counts[key]}" for key in sorted(outcome_counts)
            )
        )

        st.subheader("Full instrument-specific review")
        review_rows = build_review_rows(workspace)
        st.table(review_rows)
        st.caption(
            "clusters="
            + ",".join(sorted({row["cluster"] for row in review_rows}))
            + " · symbols="
            + ",".join(row["symbol"] for row in review_rows)
        )
        competition = workspace["current_decision_snapshot"]["capital_competition"]
        st.caption(
            f"Competition method: `{competition['method']}` across "
            f"{len(competition['candidates'])} instruments; cash score={competition['cash_score_bps']} bps."
        )

        if workspace["status"] == STATUS_DRAFT:
            if st.button(
                "Confirm and fund one portfolio",
                key="gv_operated_confirm",
            ):
                workspace = confirm_and_persist(
                    root=root, scenario_id=scenario_id
                )
        elif workspace["status"] == STATUS_FUNDED:
            if st.button(
                "Admit justified no-change observation",
                key="gv_operated_no_change",
            ):
                workspace = admit_no_change_and_persist(
                    root=root, scenario_id=scenario_id
                )
        elif workspace["status"] == STATUS_NO_CHANGE:
            reduced = scenario["transition"]["primary_reduced_symbol"]
            funded = scenario["transition"]["primary_funded_symbol"]
            if st.button(
                f"Authorize {reduced} reduction and {funded} funding",
                key="gv_operated_transition",
            ):
                workspace = authorize_transition_and_persist(
                    root=root, scenario_id=scenario_id
                )
        elif workspace["status"] == STATUS_TRANSITION:
            if st.button(
                "Record non-economic correction",
                key="gv_operated_correction",
            ):
                workspace = append_correction_and_persist(
                    root=root, scenario_id=scenario_id
                )

        _render_status(st, workspace)
        st.subheader("One reconciled portfolio book")
        book_rows = build_book_rows(workspace)
        st.table(book_rows)
        st.caption(
            "funded_symbols="
            + (",".join(row["symbol"] for row in book_rows) if book_rows else "NONE")
        )
        st.subheader("Classified residual cash")
        st.table(workspace["book"]["classified_cash"])

        if workspace["fills"]:
            st.subheader("Deterministic paper trades")
            trade_rows = build_trade_rows(workspace)
            st.table(trade_rows)
            st.caption(
                "trade_sides="
                + ",".join(row["side"] for row in trade_rows)
                + " · trade_symbols="
                + ",".join(row["symbol"] for row in trade_rows)
            )
        if workspace.get("changed_why"):
            st.subheader("Changed why")
            st.table([workspace["changed_why"]])
            st.caption(
                f"change_type={workspace['changed_why']['change_type']} · "
                f"changed_why={workspace['changed_why']}"
            )
        if workspace.get("observations"):
            st.subheader("Later observations")
            st.table(workspace["observations"])
        st.caption(
            f"Certification: `{(workspace.get('certification') or {}).get('certification_id', 'NOT_YET')}` · "
            f"lineage_depth={len(workspace.get('certification_history') or [])} · "
            f"book_hash=`{workspace['book']['book_hash']}`"
        )
        return workspace
    except OperatedPortfolioError as exc:
        st.error(f"{scenario['title']} refused unverified state")
        st.caption(f"Authority refused: {exc}")
        raise
