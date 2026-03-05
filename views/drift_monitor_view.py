"""Phase 33A Step 6: Drift monitor view."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from core.drift_alert_manager import AlertRecord, DriftAlertManager
from core.drift_detector import DriftDetector

try:
    # Preferred path if a class-based normalizer exists.
    from core.drift_score_normalizer import DriftScoreNormalizer  # type: ignore[attr-defined]
except Exception:
    # Compatibility shim for the current function-based normalizer contract.
    from core.drift_score_normalizer import normalize_drift_result

    class DriftScoreNormalizer:  # type: ignore[override]
        """Compatibility adapter exposing normalize() for view-level workflow."""

        def normalize(
            self,
            drift_score: float,
            taxonomy: Any,
            details: dict[str, Any] | None = None,
        ) -> float:
            taxonomy_name = taxonomy.value if hasattr(taxonomy, "value") else str(taxonomy)
            return float(normalize_drift_result(str(taxonomy_name), float(drift_score), details))


_LAST_FORCE_CHECK_TS_UTC: datetime | None = None


def render_drift_monitor_view(
    alert_manager: DriftAlertManager,
    drift_detector: DriftDetector,
    baseline_weights: pd.Series | None,
    baseline_metadata: dict | None,
    live_weights: pd.Series | None,
    macro: pd.DataFrame,
) -> None:
    """Render drift monitor dashboard content for Tab 6."""
    # Reserved for future macro-driven drift context.
    _ = macro

    active_alerts = alert_manager.get_active_alerts()
    history_df = _load_alert_history(alert_manager)
    current_level = _derive_current_level(active_alerts)
    last_check_text = _resolve_last_check_text(history_df)

    # Show baseline info if available
    if baseline_metadata:
        st.caption(
            f"**Baseline:** {baseline_metadata.get('strategy_name', 'Unknown')} "
            f"(ID: {baseline_metadata.get('baseline_id', 'N/A')[:8]}...) | "
            f"Created: {baseline_metadata.get('created_at', 'Unknown')}"
        )

    status_line = (
        f"Current level: {current_level} | "
        f"Active alerts: {len(active_alerts)} | "
        f"Last check: {last_check_text}"
    )
    if current_level == "RED":
        st.error(status_line)
    elif current_level == "YELLOW":
        st.warning(status_line)
    else:
        st.success(status_line)

    if st.button("Force Drift Check", key="force_drift_check", type="primary"):
        _run_force_drift_check(
            alert_manager=alert_manager,
            drift_detector=drift_detector,
            baseline_weights=baseline_weights,
            live_weights=live_weights,
        )

    st.markdown("---")
    _render_active_alerts(alert_manager, active_alerts)

    st.markdown("---")
    _render_allocation_comparison_heatmap(baseline_weights, live_weights)

    st.markdown("---")
    _render_history_timeline(history_df)


def _derive_current_level(active_alerts: list[AlertRecord]) -> str:
    if not active_alerts:
        return "GREEN"
    level_rank = {"GREEN": 0, "YELLOW": 1, "RED": 2}
    max_level = max((str(alert.alert_level).upper() for alert in active_alerts), key=level_rank.get)
    return max_level


def _resolve_last_check_text(history_df: pd.DataFrame) -> str:
    latest_ts: datetime | None = _LAST_FORCE_CHECK_TS_UTC
    if not history_df.empty and "timestamp" in history_df.columns:
        try:
            history_ts = pd.to_datetime(history_df["timestamp"], utc=True).max().to_pydatetime()
            if latest_ts is None or history_ts > latest_ts:
                latest_ts = history_ts
        except Exception:
            pass

    if latest_ts is None:
        return "Never"

    if latest_ts.tzinfo is None:
        latest_ts = latest_ts.replace(tzinfo=timezone.utc)
    return latest_ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def _render_active_alerts(alert_manager: DriftAlertManager, active_alerts: list[AlertRecord]) -> None:
    st.subheader("Active Alerts")
    if not active_alerts:
        st.info("No active drift alerts.")
        return

    for alert in active_alerts:
        level = str(alert.alert_level).upper()
        prefix = "🔴" if level == "RED" else "🟡" if level == "YELLOW" else "🟢"
        st.markdown(
            f"{prefix} **{alert.taxonomy}** | Level: **{level}** | "
            f"Normalized: **{float(alert.normalized_score):.2f}**"
        )
        st.caption(
            f"Alert ID: {alert.alert_id} | "
            f"Created: {_format_ts(alert.created_at)} | State: {alert.state}"
        )

        if st.button("Acknowledge", key=f"ack_{alert.alert_id}", type="secondary"):
            acknowledged = alert_manager.acknowledge_alert(alert.taxonomy)
            st.success(f"Acknowledged {acknowledged} alert(s) for {alert.taxonomy}.")

        if st.button("Resolve", key=f"resolve_{alert.alert_id}", type="secondary"):
            resolved = alert_manager.resolve_alert(alert.alert_id)
            if resolved:
                st.success(f"Resolved alert {alert.alert_id}.")
            else:
                st.error(f"Unable to resolve alert {alert.alert_id}.")

        if alert.details:
            with st.expander(f"Details: {alert.alert_id}", expanded=False):
                st.json(alert.details)


def _run_force_drift_check(
    alert_manager: DriftAlertManager,
    drift_detector: DriftDetector,
    baseline_weights: pd.Series | None,
    live_weights: pd.Series | None,
) -> None:
    if baseline_weights is None:
        st.error("Cannot run drift check: baseline weights unavailable.")
        return
    if live_weights is None:
        st.error("Cannot run drift check: live weights unavailable.")
        return

    baseline = _normalize_weight_series(baseline_weights)
    live = _normalize_weight_series(live_weights)
    if baseline is None:
        st.error("Cannot run drift check: baseline weights are empty or invalid.")
        return
    if live is None:
        st.error("Cannot run drift check: live weights are empty or invalid.")
        return

    try:
        drift_result = drift_detector.detect_allocation_drift(
            expected_weights=baseline,
            actual_weights=live,
        )
        normalizer = DriftScoreNormalizer()
        normalized_score = _normalize_score(normalizer, drift_result)
        alert = alert_manager.process_drift_result(drift_result, normalized_score)

        global _LAST_FORCE_CHECK_TS_UTC
        _LAST_FORCE_CHECK_TS_UTC = datetime.now(timezone.utc)

        if alert is None:
            st.info(
                f"Drift check complete. Normalized score: {normalized_score:.2f}. "
                "No alert created."
            )
            return

        level = str(alert.alert_level).upper()
        msg = (
            f"Drift check complete. Alert {alert.alert_id} created "
            f"({level}, score={alert.normalized_score:.2f})."
        )
        if level == "RED":
            st.error(msg)
        elif level == "YELLOW":
            st.warning(msg)
        else:
            st.success(msg)
    except Exception as exc:
        logging.exception("Force drift check failed: %s", exc)
        st.error(f"Force drift check failed: {exc}")


def _normalize_score(normalizer: DriftScoreNormalizer, drift_result: Any) -> float:
    try:
        return float(
            normalizer.normalize(
                drift_result.drift_score,
                drift_result.taxonomy,
                drift_result.details,
            )
        )
    except TypeError:
        return float(normalizer.normalize(drift_result.drift_score, drift_result.taxonomy))


def _normalize_weight_series(weights: pd.Series) -> pd.Series | None:
    if not isinstance(weights, pd.Series) or weights.empty:
        return None
    cleaned = pd.to_numeric(weights, errors="coerce").dropna()
    if cleaned.empty:
        return None
    total = float(cleaned.sum())
    if abs(total) < 1e-12:
        return None
    return (cleaned / total).sort_index()


def _render_allocation_comparison_heatmap(
    baseline_weights: pd.Series | None,
    live_weights: pd.Series | None,
) -> None:
    st.subheader("Allocation Comparison")
    if baseline_weights is None:
        st.warning("Baseline weights unavailable. Allocation comparison disabled.")
        return
    if live_weights is None:
        st.warning("Live weights unavailable. Allocation comparison disabled.")
        return

    baseline = _normalize_weight_series(baseline_weights)
    live = _normalize_weight_series(live_weights)
    if baseline is None or live is None:
        st.warning("Allocation comparison skipped: invalid baseline/live weight vectors.")
        return

    compare_df = _build_allocation_comparison_frame(baseline, live)
    if compare_df.empty:
        st.info("No overlapping allocation data to compare.")
        return

    heatmap_frame = compare_df[["Baseline", "Live", "Delta"]].T
    fig = px.imshow(
        heatmap_frame,
        aspect="auto",
        color_continuous_scale="RdBu",
        origin="lower",
        labels={"x": "Asset", "y": "Series", "color": "Weight"},
        title="Baseline vs Live Allocation",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        compare_df.style.format({"Baseline": "{:.2%}", "Live": "{:.2%}", "Delta": "{:+.2%}"}),
        use_container_width=True,
    )


def _build_allocation_comparison_frame(
    baseline: pd.Series,
    live: pd.Series,
) -> pd.DataFrame:
    all_assets = baseline.index.union(live.index)
    frame = pd.DataFrame(index=all_assets)
    frame["Baseline"] = baseline.reindex(all_assets).fillna(0.0)
    frame["Live"] = live.reindex(all_assets).fillna(0.0)
    frame["Delta"] = frame["Live"] - frame["Baseline"]
    frame = frame.sort_values("Delta", key=lambda s: s.abs(), ascending=False)
    return frame


def _render_history_timeline(history_df: pd.DataFrame) -> None:
    st.subheader("Historical Timeline")
    if history_df.empty:
        st.info("No alert history available yet.")
        return

    plot_df = history_df.copy()
    plot_df["timestamp"] = pd.to_datetime(plot_df["timestamp"], errors="coerce", utc=True)
    plot_df = plot_df.dropna(subset=["timestamp", "normalized_score"])
    if plot_df.empty:
        st.info("No valid timeline points to plot.")
        return

    fig = px.line(
        plot_df,
        x="timestamp",
        y="normalized_score",
        color="taxonomy",
        markers=True,
        title="Alert History (ACTIVE transitions)",
    )
    fig.add_hline(y=5.0, line_dash="dot", line_color="#ffcc00")
    fig.add_hline(y=10.0, line_dash="dot", line_color="#ff4444")
    st.plotly_chart(fig, use_container_width=True)


def _load_alert_history(alert_manager: DriftAlertManager) -> pd.DataFrame:
    db_path = getattr(alert_manager, "db_path", None)
    if db_path is None:
        return pd.DataFrame()

    resolved_path = Path(str(db_path))
    if not resolved_path.exists():
        return pd.DataFrame()

    try:
        with duckdb.connect(str(resolved_path)) as conn:
            return conn.execute(
                """
                SELECT
                    h.transition_at AS timestamp,
                    a.taxonomy AS taxonomy,
                    a.normalized_score AS normalized_score,
                    a.alert_level AS alert_level
                FROM alert_history h
                INNER JOIN alerts a ON a.alert_id = h.alert_id
                WHERE h.to_state = 'ACTIVE'
                ORDER BY h.transition_at ASC
                """
            ).fetchdf()
    except Exception as exc:
        logging.warning("Unable to load alert history: %s", exc)
        return pd.DataFrame()


def _format_ts(ts: datetime | None) -> str:
    if ts is None:
        return "n/a"
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
