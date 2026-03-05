"""
Regime Manager View Component

Provides simplified FR-041 Governor banner with progressive disclosure:
- Primary display: State (RED/AMBER/GREEN) + Target Exposure + BOCPD
- Secondary display: Matrix Exposure, Throttle Score, Composite Z (expandable)

Implements institutional best practice: show 2-3 key metrics, hide advanced in expandable section.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np

from strategies.regime_manager import RegimeManager, GovernorState


# Lazy initialization to avoid import-time dependency
_REGIME_MANAGER: RegimeManager | None = None


def _get_regime_manager() -> RegimeManager:
    """Get or create singleton RegimeManager instance."""
    global _REGIME_MANAGER
    if _REGIME_MANAGER is None:
        _REGIME_MANAGER = RegimeManager()
    return _REGIME_MANAGER


def get_regime_snapshot(macro: pd.DataFrame, index: pd.Index) -> dict:
    """
    Evaluate current regime state and return snapshot dict.

    Returns dict with keys:
        - governor_state: RED | AMBER | GREEN
        - reason: Explainability string
        - target_exposure: 0.0-2.0
        - matrix_exposure: Current calculated exposure
        - throttle_score: 0.0-1.0
        - composite_z: Composite macro z-score
        - bocpd_prob: Bayesian changepoint probability
    """
    try:
        manager = _get_regime_manager()
        result = manager.evaluate(macro, index).latest()
    except Exception as e:
        # Fallback state if RegimeManager unavailable
        result = {
            "governor_state": GovernorState.AMBER.value,
            "reason": f"Fallback: FR-041 unavailable ({type(e).__name__})",
            "target_exposure": 0.5,
            "matrix_exposure": 0.5,
            "throttle_score": 1.0,
            "composite_z": 0.0,
            "bocpd_prob": float("nan"),
        }

    # Normalize state to valid enum values
    state = str(result.get("governor_state", GovernorState.AMBER.value)).upper()
    if state not in {GovernorState.RED.value, GovernorState.AMBER.value, GovernorState.GREEN.value}:
        state = GovernorState.AMBER.value
    result["governor_state"] = state
    return result


def render_regime_banner(
    snapshot: dict,
    title: str = "FR-041 Governor",
    simplified: bool = True,
) -> None:
    """
    Render FR-041 Governor regime state banner.

    Args:
        snapshot: Regime snapshot dict from get_regime_snapshot()
        title: Banner title (default: "FR-041 Governor")
        simplified: If True, show only 3 key metrics (State/Exposure/BOCPD)
                   If False, show all 6 metrics (for Settings/Admin page)
    """
    state = str(snapshot.get("governor_state", GovernorState.AMBER.value))
    reason = str(snapshot.get("reason", "No explainability available"))
    target = float(snapshot.get("target_exposure", 0.5))
    bocpd = pd.to_numeric(snapshot.get("bocpd_prob", np.nan), errors="coerce")

    # Advanced metrics (hidden by default in simplified mode)
    throttle = float(snapshot.get("throttle_score", 1.0))
    matrix_exp = float(snapshot.get("matrix_exposure", target))
    composite_z = float(snapshot.get("composite_z", 0.0))

    # State-based styling
    if state == GovernorState.RED.value:
        icon, color, label = "🔴", "#ff4444", "RED"
    elif state == GovernorState.GREEN.value:
        icon, color, label = "🟢", "#00c57a", "GREEN"
    else:
        icon, color, label = "🟠", "#ffb020", "AMBER"

    bocpd_label = f"{float(bocpd):.2f}" if pd.notna(bocpd) else "N/A"

    if simplified:
        # Simplified view: 3 key metrics only (institutional best practice)
        st.markdown(
            f"""
            <div style='border: 1px solid {color}; border-left: 6px solid {color};
                        border-radius: 10px; padding: 14px 16px; margin: 8px 0 14px 0;
                        background: linear-gradient(135deg, rgba(15,22,35,0.95), rgba(20,30,45,0.75));'>
                <div style='display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap;'>
                    <div>
                        <div style='font-size:0.75rem; color:#9aa4b2; letter-spacing:0.08em;'>{title}</div>
                        <div style='font-size:1.25rem; font-weight:700; color:{color};'>{icon} {label}</div>
                        <div style='font-size:0.92rem; color:#d8dee9; margin-top:4px;'>{reason}</div>
                    </div>
                    <div style='display:flex; gap:18px;'>
                        <div>
                            <div style='font-size:0.72rem; color:#9aa4b2;'>Target Exposure</div>
                            <div style='font-size:1.10rem; color:#ffffff; font-weight:700;'>{target:.2f}x</div>
                        </div>
                        <div>
                            <div style='font-size:0.72rem; color:#9aa4b2;'>BOCPD</div>
                            <div style='font-size:1.10rem; color:#ffffff; font-weight:700;'>{bocpd_label}</div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Progressive disclosure: expandable section for advanced metrics
        with st.expander("🔧 Advanced Regime Metrics"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Matrix Exposure", f"{matrix_exp:.2f}x")
            with col2:
                st.metric("Throttle Score", f"{throttle:.2f}")
            with col3:
                st.metric("Composite Z", f"{composite_z:.2f}")

    else:
        # Full view: all 6 metrics (for Settings/Admin page)
        st.markdown(
            f"""
            <div style='border: 1px solid {color}; border-left: 6px solid {color};
                        border-radius: 10px; padding: 14px 16px; margin: 8px 0 14px 0;
                        background: linear-gradient(135deg, rgba(15,22,35,0.95), rgba(20,30,45,0.75));'>
                <div style='display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap;'>
                    <div>
                        <div style='font-size:0.75rem; color:#9aa4b2; letter-spacing:0.08em;'>{title}</div>
                        <div style='font-size:1.25rem; font-weight:700; color:{color};'>{icon} {label}</div>
                        <div style='font-size:0.92rem; color:#d8dee9; margin-top:4px;'>{reason}</div>
                    </div>
                    <div style='display:flex; gap:18px;'>
                        <div>
                            <div style='font-size:0.72rem; color:#9aa4b2;'>Target Exposure</div>
                            <div style='font-size:1.10rem; color:#ffffff; font-weight:700;'>{target:.2f}x</div>
                        </div>
                        <div>
                            <div style='font-size:0.72rem; color:#9aa4b2;'>Matrix</div>
                            <div style='font-size:1.10rem; color:#ffffff; font-weight:700;'>{matrix_exp:.2f}x</div>
                        </div>
                        <div>
                            <div style='font-size:0.72rem; color:#9aa4b2;'>Throttle</div>
                            <div style='font-size:1.10rem; color:#ffffff; font-weight:700;'>{throttle:.2f}</div>
                        </div>
                        <div>
                            <div style='font-size:0.72rem; color:#9aa4b2;'>Composite Z</div>
                            <div style='font-size:1.10rem; color:#ffffff; font-weight:700;'>{composite_z:.2f}</div>
                        </div>
                        <div>
                            <div style='font-size:0.72rem; color:#9aa4b2;'>BOCPD</div>
                            <div style='font-size:1.10rem; color:#ffffff; font-weight:700;'>{bocpd_label}</div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_regime_banner_from_macro(
    macro: pd.DataFrame,
    index: pd.Index,
    title: str = "FR-041 Governor",
    simplified: bool = True,
) -> None:
    """
    Convenience function: evaluate regime and render banner in one call.

    Args:
        macro: Macro features DataFrame with regime columns
        index: Date index for evaluation
        title: Banner title
        simplified: Show simplified (3 metrics) or full (6 metrics) view
    """
    snapshot = get_regime_snapshot(macro, index)
    render_regime_banner(snapshot, title=title, simplified=simplified)
