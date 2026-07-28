"""Broker-free Alpha product entrypoint (GV-ALPHA0-CLOSE Case Workspace).

No dashboard, no broker client, no trading-SDK import path.
Launch via: python launch_alpha.py
"""

from __future__ import annotations

import streamlit as st

from core.gv_alpha0_ship_runtime import (
    GvAlpha0ShipRuntimeError,
    prepare_runtime_workspace,
)
from views.gv_alpha0_case_workspace import (
    GvAlpha0CaseWorkspaceError,
    render_case_workspace,
)

st.set_page_config(
    page_title="GV-ALPHA0 Case Workspace",
    page_icon="α",
    layout="wide",
)

st.sidebar.markdown("**GV-ALPHA0**")
st.sidebar.caption(
    "Broker-free paper-decision product. No APCA/ALPACA env required. "
    "No provider or network access required."
)

try:
    runtime = prepare_runtime_workspace()
    st.sidebar.caption(f"Workspace: `{runtime.root}`")
    if runtime.initialized:
        st.sidebar.success("Deterministic sample workspace initialized.")
    # Product path always verifies the seeded case from raw before confirmation.
    render_case_workspace(st, root=runtime.root, verify=True)
except GvAlpha0ShipRuntimeError as exc:
    st.error("GV-ALPHA0 startup diagnostics failed")
    st.caption(f"Startup refused: {exc}")
except GvAlpha0CaseWorkspaceError:
    # Error already rendered inside workspace; keep page alive.
    pass
