"""Streamlit operator workspace for the GV Portfolio V0 vertical."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Protocol

from gv_portfolio_v0.storage import (
    admit_later_watch_observation,
    confirm_and_certify,
    ensure_workspace,
)
from gv_portfolio_v0.vertical import PortfolioV0Error


class WorkspaceRenderer(Protocol):
    def header(self, body: str) -> Any: ...
    def subheader(self, body: str) -> Any: ...
    def caption(self, body: str) -> Any: ...
    def markdown(self, body: str) -> Any: ...
    def table(self, data: Any) -> Any: ...
    def info(self, body: str) -> Any: ...
    def warning(self, body: str) -> Any: ...
    def error(self, body: str) -> Any: ...
    def success(self, body: str) -> Any: ...
    def button(self, label: str, key: str | None = None) -> bool: ...


def build_review_rows(workspace: Mapping[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for review in workspace["reviews"]:
        thesis = review["living_thesis_lite"]
        scenario = thesis["scenario_range"]
        rows.append(
            {
                "symbol": review["symbol"],
                "relationship": review["relationship"],
                "outcome": review["outcome"],
                "bear/base/bull": (
                    f"{scenario['bear_value']} / {scenario['base_value']} / "
                    f"{scenario['bull_value']}"
                ),
                "thesis": thesis["principal_claim"],
                "state": "WATCH" if thesis["watch_conditions"] else "NO_WATCH_RULE",
            }
        )
    rows.append(
        {
            "symbol": "CASH",
            "relationship": "COMPETING_ALLOCATION",
            "outcome": "CASH",
            "bear/base/bull": "1 / 1 / 1",
            "thesis": "Retain classified liquidity when no admitted security beats cash.",
            "state": "AVAILABLE",
        }
    )
    return rows


def build_book_rows(workspace: Mapping[str, Any]) -> list[dict[str, str]]:
    symbols = {
        row["instrument_id"]: row["symbol"]
        for row in [*workspace["instruments"], workspace["benchmark"]]
    }
    return [
        {
            "symbol": symbols.get(row["instrument_id"], row["instrument_id"][:12]),
            "quantity": row["quantity"],
            "valuation_price": row["valuation_price"] or "PENDING",
            "market_value": row["market_value"] or "PENDING",
        }
        for row in workspace["book"]["positions"]
    ]


def build_cash_rows(workspace: Mapping[str, Any]) -> list[dict[str, str]]:
    return [dict(row) for row in workspace["book"]["classified_cash"]]


def _render_status(st: WorkspaceRenderer, workspace: Mapping[str, Any]) -> None:
    status = workspace["status"]
    if status == "DRAFT_REVIEW":
        st.warning("Review complete; portfolio aim awaits operator confirmation.")
    elif status == "CERTIFIED":
        st.success(
            "Certified paper book persisted and reopened. One deterministic order and fill are complete."
        )
    else:
        st.success(
            "Later WATCH observation admitted. Evidence changed; portfolio aim remained unchanged."
        )
    st.caption(
        f"status=`{status}` · NAV={workspace['book']['nav']} · "
        f"valuation={workspace['book']['valuation_status']} · "
        f"certification={(workspace.get('certification') or {}).get('certification_id', 'NOT_YET')}"
    )
    st.info(workspace["explanation"])


def render_portfolio_workspace(
    st: WorkspaceRenderer, *, root: Path | None = None
) -> dict[str, Any]:
    st.header("GV Micro-Portfolio Workspace")
    st.caption(
        "Four reviewed securities · benchmark · classified cash · deterministic paper execution. "
        "No provider, broker, alpha, score-uplift, or live-capital claim."
    )
    try:
        workspace = ensure_workspace(root=root)
        st.subheader("Review and Living Thesis Lite")
        st.table(build_review_rows(workspace))
        st.caption(
            f"Benchmark: `{workspace['benchmark']['symbol']}` · "
            f"Aim: `{workspace['portfolio_aim']['portfolio_aim_id']}` · "
            f"Original decision snapshot: `{workspace['decision_snapshot']['decision_snapshot_id']}`"
        )

        if workspace["status"] == "DRAFT_REVIEW":
            if st.button(
                "Confirm portfolio aim and execute paper order",
                key="gv_portfolio_confirm",
            ):
                workspace = confirm_and_certify(root=root)
        elif workspace["status"] == "CERTIFIED":
            if st.button(
                "Admit later WATCH observation",
                key="gv_portfolio_watch_observation",
            ):
                workspace = admit_later_watch_observation(root=root)

        _render_status(st, workspace)
        st.subheader("Certified book")
        st.table(build_book_rows(workspace))
        st.subheader("Classified cash")
        st.table(build_cash_rows(workspace))
        st.caption(
            f"Position value={workspace['book']['position_value']} · "
            f"Cash={workspace['book']['total_cash']} · NAV={workspace['book']['nav']} · "
            f"Split residual={workspace['book']['split_value_residual']}"
        )

        competition = workspace["decision_snapshot"]["capital_competition"]
        st.subheader("Capital competition")
        st.table(competition["candidates"])
        st.caption(
            f"Winner: `{competition['selected_candidate']}` by "
            f"`{competition['method']}` at {competition['selected_net_score_bps']} bps."
        )
        if workspace.get("order"):
            st.subheader("Paper execution")
            st.table(
                [
                    {
                        "order_id": workspace["order"]["order_id"],
                        "fill_id": workspace["fill"]["fill_id"],
                        "side": workspace["fill"]["side"],
                        "quantity": workspace["fill"]["quantity"],
                        "price": workspace["fill"]["price"],
                        "fee": workspace["fill"]["fee"],
                    }
                ]
            )
        if workspace.get("later_observation"):
            st.subheader("Later observation")
            st.table([workspace["later_observation"]])
            st.caption(
                "Aim comparison: unchanged because hard_falsifier_fired=False and classification=WATCH."
            )
        return workspace
    except PortfolioV0Error as exc:
        st.error("GV Portfolio V0 refused to present unverified state")
        st.caption(f"Authority refused: {exc}")
        raise
