from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from rendered_governance import assert_rendered_governance_safe
from rendered_governance import collect_rendered_text
from rendered_governance import scan_rendered_governance


DASHBOARD_WIDE_FORBIDDEN_APP = r"""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Synthetic Dashboard Governance")

st.title("Strong Buy")
st.header("Latest Buys/Sells")
st.subheader("Buy/Sell Decision Log")

buy_tab, sell_tab = st.tabs(["BUY", "SELL"])
with buy_tab:
    st.markdown("Entry/Exit Strategy")
    st.caption("Estimated Shares")
    st.metric("Action Status", "blocked")
    st.button("rebalance now")

with sell_tab:
    with st.expander("Portfolio Optimizer"):
        st.download_button("submit_order", data="blocked", file_name="blocked.txt")
        st.caption("broker_call")
        st.markdown("buy_alert")
        st.info("sell_alert")

st.dataframe(
    pd.DataFrame(
        {
            "rank": ["score"],
            "recommendation": ["allocation alert"],
        }
    ),
    hide_index=True,
)
st.table(pd.DataFrame({"surface": ["Strong Buy"]}))
"""


DASHBOARD_WIDE_FORBIDDEN_INDEX_APP = r"""
import pandas as pd
import streamlit as st

st.dataframe(
    pd.DataFrame(
        {"Research Bucket": ["Rows Passing Research Filter"]},
        index=pd.Index(["Strong Buy"], name="Rank"),
    )
)
st.table(
    pd.DataFrame(
        {"Research Bucket": ["Rows Passing Research Filter"]},
        index=pd.Index(["BUY"], name="Synthetic Index"),
    )
)
st.table(
    pd.Series(
        ["Rows Passing Research Filter"],
        index=pd.Index(["SELL"], name="Synthetic Series Index"),
        name="Research Bucket",
    )
)
"""


DASHBOARD_WIDE_ALLOWED_APP = r"""
import pandas as pd
import streamlit as st

PAGES = {
    "Research Optimizer - Simulation Only": "research_optimizer",
    "Replay Decision-Code Audit Log": "replay_audit",
}

st.title("Research Optimizer - Simulation Only")
st.sidebar.radio("Research Bucket", list(PAGES), index=0)

weights_tab, replay_tab = st.tabs(
    ["Simulation Weight Table", "Replay Decision-Code Audit Log"]
)
with weights_tab:
    st.caption("Historical Replay Lifecycle Events")
    st.markdown("Open replay lifecycle rows")
    st.metric("Rows Passing Research Filter", "8")
    st.button("Simulation notional")
    st.download_button(
        "Simulation Weight Table",
        data="ticker,weight\nAAA,0.25\n",
        file_name="simulation_weights.csv",
    )
    st.dataframe(
        pd.DataFrame(
            {
                "Research Bucket": ["Rows Passing Research Filter"],
                "Simulation notional": ["Research Optimizer - Simulation Only"],
                "Open replay lifecycle rows": [
                    "Historical Replay Lifecycle Events"
                ],
            }
        ),
        hide_index=True,
    )

with replay_tab:
    with st.expander("Replay Decision-Code Audit Log"):
        st.table(
            pd.DataFrame(
                {
                    "Simulation Weight Table": ["Research Bucket"],
                    "Historical Replay Lifecycle Events": [
                        "Open replay lifecycle rows"
                    ],
                }
            )
        )
        st.caption("Simulation notional")
"""


DASHBOARD_WIDE_ALLOWED_VARIANT_VIOLATION_APP = r"""
import pandas as pd
import streamlit as st

st.markdown("Research Optimizer - Simulation Only buy panel")
st.caption("Simulation Weight Table score panel")
variant_tab = st.tabs(["Replay Decision-Code Audit Log broker panel"])[0]
with variant_tab:
    with st.expander("Historical Replay Lifecycle Events alert panel"):
        st.metric("Research Bucket rank panel", "blocked")
        st.button("Rows Passing Research Filter recommendation panel")
        st.download_button(
            "Open replay lifecycle rows sell panel",
            data="blocked",
            file_name="blocked.txt",
        )
        st.table(pd.DataFrame({"Simulation notional order panel": ["blocked"]}))
"""


def test_dashboard_wide_rendered_governance_fails_action_labels() -> None:
    app = AppTest.from_string(DASHBOARD_WIDE_FORBIDDEN_APP).run(timeout=15)

    assert not app.exception
    findings = scan_rendered_governance(app)
    patterns = {finding.pattern for finding in findings}

    assert {
        "Strong Buy",
        "Latest Buys/Sells",
        "Buy/Sell Decision Log",
        "BUY",
        "SELL",
        "Entry/Exit Strategy",
        "Estimated Shares",
        "Action Status",
        "rebalance now",
        "Portfolio Optimizer",
        "submit_order",
        "broker_call",
        "buy_alert",
        "sell_alert",
        "Rank",
        "Score",
        "recommendation",
        "allocation alert",
    }.issubset(patterns)
    with pytest.raises(AssertionError, match="Rendered governance scan found forbidden labels"):
        assert_rendered_governance_safe(app)


def test_dashboard_wide_rendered_governance_fails_dataframe_table_indexes() -> None:
    app = AppTest.from_string(DASHBOARD_WIDE_FORBIDDEN_INDEX_APP).run(timeout=15)

    assert not app.exception
    rendered_text = {item.text for item in collect_rendered_text(app)}
    findings = scan_rendered_governance(app)
    patterns = {finding.pattern for finding in findings}

    assert {"Rank", "Strong Buy", "BUY", "SELL"}.issubset(rendered_text)
    assert {"Rank", "Strong Buy", "BUY", "SELL"}.issubset(patterns)
    with pytest.raises(AssertionError, match="Rendered governance scan found forbidden labels"):
        assert_rendered_governance_safe(app)


def test_dashboard_wide_rendered_governance_allows_research_only_shell() -> None:
    app = AppTest.from_string(DASHBOARD_WIDE_ALLOWED_APP).run(timeout=15)

    assert not app.exception
    assert_rendered_governance_safe(app)
    rendered_text = {item.text for item in collect_rendered_text(app)}

    assert {
        "Research Optimizer - Simulation Only",
        "Simulation Weight Table",
        "Replay Decision-Code Audit Log",
        "Historical Replay Lifecycle Events",
        "Research Bucket",
        "Rows Passing Research Filter",
        "Open replay lifecycle rows",
        "Simulation notional",
    }.issubset(rendered_text)


def test_dashboard_wide_allowed_labels_are_exact_only() -> None:
    app = AppTest.from_string(DASHBOARD_WIDE_ALLOWED_VARIANT_VIOLATION_APP).run(
        timeout=15
    )

    assert not app.exception
    findings = scan_rendered_governance(app)
    patterns = {finding.pattern for finding in findings}

    assert {
        "Research Optimizer - Simulation Only variant with buy",
        "Simulation Weight Table variant with score",
        "Replay Decision-Code Audit Log variant with broker",
        "Historical Replay Lifecycle Events variant with alert",
        "Research Bucket variant with rank",
        "Rows Passing Research Filter variant with recommendation",
        "Open replay lifecycle rows variant with sell",
        "Simulation notional variant with order",
    }.issubset(patterns)
    with pytest.raises(AssertionError, match="Rendered governance scan found forbidden labels"):
        assert_rendered_governance_safe(app)
