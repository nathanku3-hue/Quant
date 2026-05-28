from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from rendered_governance import assert_rendered_governance_safe
from rendered_governance import collect_rendered_text
from rendered_governance import scan_rendered_governance


SCANNER_DISPLAY_APP = r"""
import pandas as pd
import streamlit as st

from views.scanner_display import build_scanner_research_display_frame

source = pd.DataFrame(
    [
        {
            "Ticker": "AAA",
            "Rating": "ENTER: STRONG BUY",
            "Score": 100.0,
            "Entry_Price": 10.0,
            "Stop_Loss": 9.0,
            "Target_Price": 14.0,
            "Leverage": 1.5,
            "Cluster": "Compute",
            "Current_Price": 11.0,
            "Tactical_Warning": "N/A",
            "Proxy_Type": "Sector Only",
            "P_Value": "p=82%",
            "Proxy_Content": "Research note",
            "Proxy_Signal": "CORRELATED",
        }
    ]
)

display = build_scanner_research_display_frame(source, time_label="just now")
st.dataframe(display, hide_index=True)
"""

FORBIDDEN_RENDERED_APP = r"""
import pandas as pd
import streamlit as st

st.header("Strong Buy")
st.caption("Latest Buys/Sells")
st.markdown("BUY")
st.metric("Action Status", "research-only fixture")
st.download_button("Generate Option Yield", data="not-used", file_name="fixture.txt")
st.dataframe(
    pd.DataFrame(
        {
            "Score": [99],
            "Research Bucket": ["Rows Passing Research Filter"],
            "safe_cell": ["broker_call"],
            "safe_cell_2": ["SELL"],
        }
    ),
    hide_index=True,
)
st.table(pd.DataFrame({"safe_column": ["investment recommendation"]}))
st.caption("Entry/Exit Strategy")
st.caption("Portfolio Optimizer")
"""


ALLOWED_RENDERED_APP = r"""
import pandas as pd
import streamlit as st

st.header("Research Optimizer - Simulation Only")
st.caption("Replay Decision-Code Audit Log")
st.metric("Rows Passing Research Filter", "3")
st.download_button("Simulation Weight Table", data="not-used", file_name="fixture.txt")
st.dataframe(
    pd.DataFrame(
        {
            "Research Bucket": ["Rows Passing Research Filter"],
            "Simulation Weight Table": ["Research Optimizer - Simulation Only"],
        }
    ),
    hide_index=True,
)
st.table(pd.DataFrame({"Replay Decision-Code Audit Log": ["Research Bucket"]}))
"""

ALLOWED_VARIANT_RENDERED_APP = r"""
import streamlit as st

st.header("Portfolio & Allocation")
st.caption("Historical Replay Lifecycle Events")
st.metric("Research Optimizer - Simulation Only", "ready")
"""

DANGEROUS_ALLOWED_VARIANT_RENDERED_APP = r"""
import streamlit as st

st.caption("Portfolio & Allocation action panel")
st.metric("Research Optimizer - Simulation Only action panel", "blocked")
st.markdown("Simulation Weight Table score panel")
"""


@pytest.mark.parametrize(
    ("app_source", "expected_patterns"),
    [
        (
            FORBIDDEN_RENDERED_APP,
            {
                "Strong Buy",
                "Latest Buys/Sells",
                "BUY",
                "Action Status",
                "Generate Option Yield",
                "Score",
                "broker_call",
                "SELL",
                "investment recommendation",
                "Entry/Exit Strategy",
                "Portfolio Optimizer",
            },
        )
    ],
)
def test_rendered_governance_scan_fails_for_forbidden_visible_text(
    app_source: str,
    expected_patterns: set[str],
) -> None:
    app = AppTest.from_string(app_source).run(timeout=15)

    assert not app.exception
    findings = scan_rendered_governance(app)

    assert expected_patterns.issubset({finding.pattern for finding in findings})
    with pytest.raises(AssertionError, match="Rendered governance scan found forbidden labels"):
        assert_rendered_governance_safe(app)


def test_rendered_governance_scan_allows_research_only_labels() -> None:
    app = AppTest.from_string(ALLOWED_RENDERED_APP).run(timeout=15)

    assert not app.exception
    assert_rendered_governance_safe(app)


def test_rendered_governance_allows_exact_labels_but_blocks_action_variants() -> None:
    allowed_app = AppTest.from_string(ALLOWED_VARIANT_RENDERED_APP).run(timeout=15)
    variant_app = AppTest.from_string(DANGEROUS_ALLOWED_VARIANT_RENDERED_APP).run(
        timeout=15
    )

    assert not allowed_app.exception
    assert not variant_app.exception
    assert_rendered_governance_safe(allowed_app)

    findings = scan_rendered_governance(variant_app)
    assert {
        "Portfolio & Allocation variant with action panel",
        "Research Optimizer - Simulation Only variant with action panel",
        "Simulation Weight Table variant with score",
    }.issubset({finding.pattern for finding in findings})
    with pytest.raises(AssertionError, match="Rendered governance scan found forbidden labels"):
        assert_rendered_governance_safe(variant_app)


def test_rendered_governance_collects_download_and_dataframe_text() -> None:
    app = AppTest.from_string(ALLOWED_RENDERED_APP).run(timeout=15)

    rendered_text = {item.text for item in collect_rendered_text(app)}

    assert "Simulation Weight Table" in rendered_text
    assert "Research Bucket" in rendered_text
    assert "Rows Passing Research Filter" in rendered_text
    assert "Research Optimizer - Simulation Only" in rendered_text


def test_scanner_display_dataframe_render_remains_quarantined() -> None:
    app = AppTest.from_string(SCANNER_DISPLAY_APP).run(timeout=15)

    assert not app.exception
    assert_rendered_governance_safe(app)
    rendered_text = {item.text for item in collect_rendered_text(app)}
    assert "Setup evidence review" in rendered_text
    assert "Support Reference" in rendered_text
    assert "$10.00 (support ref; flush -0%; premium +0%)" in rendered_text
    assert "Score" not in rendered_text
    assert "Rating" not in rendered_text
    assert "Entry_Price" not in rendered_text
