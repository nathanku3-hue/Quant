"""Frozen retained-byte winner-capture diagnostics for AOV historical evidence.

This module is deliberately provider-blind.  It accepts already-captured replay
matrices and reports where extreme future winners fall out of the frozen AOV
support path.  It does not rebuild Rule100, Parent, Child, or any provider query.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
from typing import Any

import numpy as np
import pandas as pd


WINNER_CAPTURE_SCHEMA = "aov0_winner_capture_diagnostic_v0"
WINNER_FRACTION = 0.05
PRIMARY_HORIZON = 10
SECONDARY_HORIZON = 20
WEIGHT_EPSILON = 1e-12
REGIME_EPSILON = 1e-12


class WinnerCaptureError(ValueError):
    """Fail-closed diagnostic contract violation."""


def _require_matrix(frame: pd.DataFrame, *, label: str) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise WinnerCaptureError(f"winner_capture_{label}_required")
    out = frame.copy()
    if not isinstance(out.index, pd.DatetimeIndex):
        try:
            out.index = pd.to_datetime(out.index, errors="raise")
        except (TypeError, ValueError) as exc:
            raise WinnerCaptureError(f"winner_capture_{label}_date_index_required") from exc
    out.index = pd.DatetimeIndex(out.index).normalize()
    if out.index.has_duplicates:
        raise WinnerCaptureError(f"winner_capture_{label}_duplicate_date")
    if not out.index.is_monotonic_increasing:
        raise WinnerCaptureError(f"winner_capture_{label}_date_order_invalid")
    if out.columns.has_duplicates:
        raise WinnerCaptureError(f"winner_capture_{label}_duplicate_security")
    numeric = out.apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise WinnerCaptureError(f"winner_capture_{label}_non_finite")
    return numeric.astype(float)


def _assert_same_surface(
    reference: pd.DataFrame,
    candidate: pd.DataFrame,
    *,
    label: str,
) -> None:
    if not reference.index.equals(candidate.index):
        raise WinnerCaptureError(f"winner_capture_{label}_date_surface_mismatch")
    if list(reference.columns) != list(candidate.columns):
        raise WinnerCaptureError(f"winner_capture_{label}_security_surface_mismatch")


def state_change_anchors(
    target_weights: pd.DataFrame,
    *,
    epsilon: float = WEIGHT_EPSILON,
) -> pd.DatetimeIndex:
    """Return dates where the live target state changes, including the first row."""

    targets = _require_matrix(target_weights, label="target_weights")
    if epsilon < 0:
        raise WinnerCaptureError("winner_capture_weight_epsilon_invalid")
    changed = targets.diff().abs().gt(float(epsilon)).any(axis=1)
    changed.iloc[0] = True
    return pd.DatetimeIndex(targets.index[changed]).normalize()


def forward_total_returns(
    total_returns: pd.DataFrame,
    *,
    anchor: pd.Timestamp,
    horizon: int,
) -> tuple[pd.Timestamp, pd.Series]:
    """Compound the next ``horizon`` observed sessions, excluding the anchor."""

    returns = _require_matrix(total_returns, label="total_returns")
    if int(horizon) != horizon or int(horizon) <= 0:
        raise WinnerCaptureError("winner_capture_horizon_invalid")
    day = pd.Timestamp(anchor).normalize()
    if day not in returns.index:
        raise WinnerCaptureError("winner_capture_anchor_not_in_return_calendar")
    position = int(returns.index.get_loc(day))
    end = position + int(horizon)
    if end >= len(returns.index):
        raise WinnerCaptureError("winner_capture_incomplete_forward_horizon")
    window = returns.iloc[position + 1 : end + 1]
    values = np.prod(1.0 + window.to_numpy(dtype=float), axis=0) - 1.0
    return pd.Timestamp(window.index[-1]).normalize(), pd.Series(values, index=returns.columns, dtype=float)


def deterministic_top_fraction(
    values: pd.Series,
    *,
    fraction: float = WINNER_FRACTION,
) -> tuple[str, ...]:
    """Select the highest fraction with security-id ascending tie break."""

    if not isinstance(values, pd.Series) or values.empty:
        raise WinnerCaptureError("winner_capture_values_required")
    if not 0.0 < float(fraction) <= 1.0:
        raise WinnerCaptureError("winner_capture_fraction_invalid")
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.isna().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise WinnerCaptureError("winner_capture_values_non_finite")
    rows = pd.DataFrame(
        {
            "security_id": [str(value) for value in numeric.index],
            "value": numeric.to_numpy(dtype=float),
        }
    ).sort_values(["value", "security_id"], ascending=[False, True], kind="mergesort")
    count = max(1, int(math.ceil(float(fraction) * len(rows))))
    return tuple(rows.head(count)["security_id"].tolist())


def build_regime_series(
    close_history: pd.DataFrame,
    *,
    active_security_ids: Sequence[str],
    terminal_effective_dates: Mapping[str, object] | None = None,
    sma_window: int = 200,
) -> pd.Series:
    """Reproduce the AOV slow-trend breadth regime from retained close history."""

    if not isinstance(close_history, pd.DataFrame) or close_history.empty:
        raise WinnerCaptureError("winner_capture_close_history_required")
    closes = close_history.copy()
    if not isinstance(closes.index, pd.DatetimeIndex):
        closes.index = pd.to_datetime(closes.index, errors="raise")
    closes.index = pd.DatetimeIndex(closes.index).normalize()
    if closes.index.has_duplicates or not closes.index.is_monotonic_increasing:
        raise WinnerCaptureError("winner_capture_close_history_date_surface_invalid")
    if closes.columns.has_duplicates:
        raise WinnerCaptureError("winner_capture_close_history_duplicate_security")
    closes = closes.apply(pd.to_numeric, errors="coerce")
    finite_or_missing = np.isfinite(closes.fillna(0.0).to_numpy(dtype=float))
    if not finite_or_missing.all():
        raise WinnerCaptureError("winner_capture_close_history_non_finite")
    ids = tuple(str(value) for value in active_security_ids)
    if not ids or len(set(ids)) != len(ids):
        raise WinnerCaptureError("winner_capture_active_security_ids_invalid")
    missing = sorted(set(ids) - set(closes.columns.astype(str)))
    if missing:
        raise WinnerCaptureError("winner_capture_regime_security_missing:" + missing[0])
    if int(sma_window) != sma_window or int(sma_window) <= 1:
        raise WinnerCaptureError("winner_capture_regime_sma_window_invalid")

    selected = closes.loc[:, list(ids)].copy()
    # CIQ market features roll within each security's observed rows after query-
    # grid placeholders are removed.  Rolling the wide union calendar would
    # incorrectly count provider NA holiday placeholders against min_periods.
    trend = pd.DataFrame(np.nan, index=selected.index, columns=selected.columns, dtype=float)
    for security_id in selected.columns:
        observed = selected[security_id].dropna()
        sma = observed.rolling(window=int(sma_window), min_periods=int(sma_window)).mean()
        values = pd.Series(
            np.where(observed.ge(sma), 1.0, -1.0),
            index=observed.index,
            dtype=float,
        ).where(sma.notna())
        trend.loc[values.index, security_id] = values

    for security_id, effective in dict(terminal_effective_dates or {}).items():
        sid = str(security_id)
        if sid not in trend.columns:
            continue
        effective_date = pd.Timestamp(effective).normalize()
        trend.loc[trend.index >= effective_date, sid] = np.nan

    regime = trend.mean(axis=1, skipna=True)
    regime.name = "regime"
    return regime


def regime_bucket(value: float | int | np.floating | None) -> str:
    if value is None or not np.isfinite(float(value)):
        return "UNAVAILABLE"
    numeric = float(value)
    if numeric > REGIME_EPSILON:
        return "POSITIVE_BREADTH"
    if numeric < -REGIME_EPSILON:
        return "NEGATIVE_BREADTH"
    return "NEUTRAL_BREADTH"


def _support_age_sessions(
    targets: pd.DataFrame,
    *,
    anchor: pd.Timestamp,
    security_id: str,
    epsilon: float,
) -> int:
    position = int(targets.index.get_loc(pd.Timestamp(anchor).normalize()))
    values = targets[security_id].iloc[: position + 1].to_numpy(dtype=float)
    age = 0
    for value in values[::-1]:
        if value <= epsilon:
            break
        age += 1
    return age


def _aggregate_episodes(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    if not episodes:
        return {
            "episode_count": 0,
            "winner_observation_count": 0,
            "selection_breadth_mean": None,
            "winner_recall": None,
            "winner_recall_lift_vs_breadth": None,
            "funnel": {},
            "capital": {},
            "contribution": {},
            "child_clipping": {},
            "false_positive_downside_avoided": {},
        }

    winner_total = int(sum(int(item["winner_count"]) for item in episodes))
    funnel_keys = (
        "risk_set_access",
        "sizing_eligible",
        "nonzero_forecast_support",
        "entry_lead",
        "capital_allocated",
        "contribution_captured",
    )
    funnel: dict[str, Any] = {}
    for key in funnel_keys:
        count = int(sum(int(item["funnel_counts"][key]) for item in episodes))
        funnel[key] = {
            "count": count,
            "recall": float(count / winner_total) if winner_total else None,
        }

    breadth = float(np.mean([float(item["selection_breadth"]) for item in episodes]))
    recall = float(funnel["sizing_eligible"]["recall"]) if winner_total else None
    lead_values = [
        int(winner["entry_lead_sessions_before_anchor"])
        for episode in episodes
        for winner in episode["winners"]
        if winner["entry_lead_sessions_before_anchor"] is not None
    ]
    clipping_count = int(sum(int(item["child_clipped_winner_count"]) for item in episodes))
    late_capture_count = int(sum(int(item["late_entry_capture_count"]) for item in episodes))
    false_positive_count = int(sum(int(item["false_positive_count"]) for item in episodes))
    downside_count = int(sum(int(item["downside_false_positive_count"]) for item in episodes))
    downside_avoided_count = int(sum(int(item["downside_avoided_count"]) for item in episodes))

    return {
        "episode_count": len(episodes),
        "winner_observation_count": winner_total,
        "selection_breadth_mean": breadth,
        "winner_recall": recall,
        "winner_recall_lift_vs_breadth": (
            float(recall / breadth) if recall is not None and breadth > 0.0 else None
        ),
        "funnel": funnel,
        "capital": {
            "winner_capital_share_of_risky_gross_first_session_mean": float(
                np.mean([float(item["winner_capital_share_first_session"]) for item in episodes])
            ),
            "entry_lead_sessions_before_anchor_mean": (
                float(np.mean(lead_values)) if lead_values else None
            ),
        },
        "contribution": {
            "parent_winner_contribution_sum": float(
                sum(float(item["parent_winner_contribution"]) for item in episodes)
            ),
            "child_winner_contribution_sum": float(
                sum(float(item["child_winner_contribution"]) for item in episodes)
            ),
            "late_entry_capture_count": late_capture_count,
            "episode_overlap_sensitive": True,
        },
        "child_clipping": {
            "clipped_winner_count": clipping_count,
            "clipped_winner_rate": float(clipping_count / winner_total) if winner_total else None,
            "winner_gross_giveup_sum": float(
                sum(float(item["child_winner_gross_giveup"]) for item in episodes)
            ),
            "episode_overlap_sensitive": True,
        },
        "false_positive_downside_avoided": {
            "parent_supported_nonwinner_count": false_positive_count,
            "negative_forward_return_count": downside_count,
            "child_avoided_loss_count": downside_avoided_count,
            "child_avoided_loss_sum": float(
                sum(float(item["child_avoided_loss_sum"]) for item in episodes)
            ),
            "episode_overlap_sensitive": True,
        },
    }


def diagnose_stage(
    *,
    stage: str,
    total_returns: pd.DataFrame,
    rule100_targets: pd.DataFrame,
    parent_targets: pd.DataFrame,
    child_targets: pd.DataFrame,
    parent_executed: pd.DataFrame,
    child_executed: pd.DataFrame,
    regime: pd.Series,
    horizons: Sequence[int] = (PRIMARY_HORIZON, SECONDARY_HORIZON),
    identity_by_security: Mapping[str, Mapping[str, Any]] | None = None,
    winner_fraction: float = WINNER_FRACTION,
    epsilon: float = WEIGHT_EPSILON,
) -> dict[str, Any]:
    """Diagnose winner access and Parent/Child capture on one retained replay stage."""

    if not str(stage).strip():
        raise WinnerCaptureError("winner_capture_stage_required")
    returns = _require_matrix(total_returns, label="total_returns")
    rule = _require_matrix(rule100_targets, label="rule100_targets")
    parent = _require_matrix(parent_targets, label="parent_targets")
    child = _require_matrix(child_targets, label="child_targets")
    parent_exec = _require_matrix(parent_executed, label="parent_executed")
    child_exec = _require_matrix(child_executed, label="child_executed")
    for label, frame in (
        ("rule100_targets", rule),
        ("parent_targets", parent),
        ("child_targets", child),
        ("parent_executed", parent_exec),
        ("child_executed", child_exec),
    ):
        _assert_same_surface(returns, frame, label=label)

    if (child.to_numpy(dtype=float) - parent.to_numpy(dtype=float) > epsilon).any():
        raise WinnerCaptureError("winner_capture_child_target_exceeds_parent")
    if (child_exec.to_numpy(dtype=float) - parent_exec.to_numpy(dtype=float) > epsilon).any():
        raise WinnerCaptureError("winner_capture_child_executed_exceeds_parent")

    regime_series = pd.Series(regime).copy()
    if not isinstance(regime_series.index, pd.DatetimeIndex):
        regime_series.index = pd.to_datetime(regime_series.index, errors="raise")
    regime_series.index = pd.DatetimeIndex(regime_series.index).normalize()
    anchors = state_change_anchors(rule, epsilon=epsilon)
    identities = {str(key): dict(value) for key, value in dict(identity_by_security or {}).items()}

    horizon_reports: dict[str, Any] = {}
    for raw_horizon in horizons:
        horizon = int(raw_horizon)
        episodes: list[dict[str, Any]] = []
        for anchor in anchors:
            position = int(returns.index.get_loc(anchor))
            if position + horizon >= len(returns.index):
                continue
            maturity, forward = forward_total_returns(returns, anchor=anchor, horizon=horizon)
            winners = deterministic_top_fraction(forward, fraction=winner_fraction)
            window_dates = returns.index[position + 1 : position + horizon + 1]
            first_session = pd.Timestamp(window_dates[0]).normalize()

            rule_row = rule.loc[anchor]
            parent_row = parent.loc[anchor]
            first_parent_exec = parent_exec.loc[first_session]
            winner_set = set(winners)
            rule_support = {str(sid) for sid in rule.columns[rule_row.gt(epsilon)]}
            parent_support = {str(sid) for sid in parent.columns[parent_row.gt(epsilon)]}
            entry_support = {str(sid) for sid in parent_exec.columns[first_parent_exec.gt(epsilon)]}

            parent_contribution = (
                parent_exec.loc[window_dates] * returns.loc[window_dates]
            ).sum(axis=0)
            child_contribution = (
                child_exec.loc[window_dates] * returns.loc[window_dates]
            ).sum(axis=0)

            winner_rows: list[dict[str, Any]] = []
            captured_count = 0
            late_capture_count = 0
            clipped_count = 0
            for security_id in winners:
                parent_value = float(parent_contribution[security_id])
                child_value = float(child_contribution[security_id])
                entered_on_first_session = security_id in entry_support
                captured = entered_on_first_session and parent_value > epsilon
                late_captured = (not entered_on_first_session) and parent_value > epsilon
                clipped = (parent_value - child_value) > epsilon
                captured_count += int(captured)
                late_capture_count += int(late_captured)
                clipped_count += int(clipped)
                age = _support_age_sessions(parent, anchor=anchor, security_id=security_id, epsilon=epsilon)
                identity = identities.get(security_id, {})
                winner_rows.append(
                    {
                        "security_id": security_id,
                        "ticker": identity.get("ticker"),
                        "company_name": identity.get("company_name"),
                        "forward_total_return": float(forward[security_id]),
                        "sizing_eligible": security_id in rule_support,
                        "nonzero_forecast_support": security_id in parent_support,
                        "entry_lead": entered_on_first_session,
                        "entry_lead_sessions_before_anchor": max(age - 1, 0) if age else None,
                        "late_entry_captured": late_captured,
                        "parent_capital_first_session": float(first_parent_exec[security_id]),
                        "parent_contribution": parent_value,
                        "child_contribution": child_value,
                        "child_gross_giveup": float(parent_value - child_value),
                    }
                )

            risky_gross = float(first_parent_exec.clip(lower=0.0).sum())
            winner_capital = float(first_parent_exec.loc[list(winners)].clip(lower=0.0).sum())
            nonwinner_support = sorted(parent_support - winner_set)
            downside_ids = [sid for sid in nonwinner_support if float(forward[sid]) < 0.0]
            avoided = {
                sid: float(child_contribution[sid] - parent_contribution[sid])
                for sid in downside_ids
            }
            raw_regime = float(regime_series.get(anchor, np.nan))
            episodes.append(
                {
                    "anchor_date": anchor.date().isoformat(),
                    "first_outcome_session": first_session.date().isoformat(),
                    "maturity_date": maturity.date().isoformat(),
                    "regime": raw_regime if np.isfinite(raw_regime) else None,
                    "regime_bucket": regime_bucket(raw_regime),
                    "risk_set_count": len(rule.columns),
                    "winner_count": len(winners),
                    "selection_breadth": float(len(rule_support) / len(rule.columns)),
                    "winner_capital_share_first_session": (
                        float(winner_capital / risky_gross) if risky_gross > epsilon else 0.0
                    ),
                    "funnel_counts": {
                        "risk_set_access": len(winners),
                        "sizing_eligible": len(winner_set & rule_support),
                        "nonzero_forecast_support": len(winner_set & parent_support),
                        "entry_lead": len(winner_set & entry_support),
                        "capital_allocated": len(
                            [sid for sid in winners if float(first_parent_exec[sid]) > epsilon]
                        ),
                        "contribution_captured": captured_count,
                    },
                    "parent_winner_contribution": float(parent_contribution.loc[list(winners)].sum()),
                    "child_winner_contribution": float(child_contribution.loc[list(winners)].sum()),
                    "child_winner_gross_giveup": float(
                        (parent_contribution.loc[list(winners)] - child_contribution.loc[list(winners)]).sum()
                    ),
                    "child_clipped_winner_count": clipped_count,
                    "late_entry_capture_count": late_capture_count,
                    "false_positive_count": len(nonwinner_support),
                    "downside_false_positive_count": len(downside_ids),
                    "downside_avoided_count": len([value for value in avoided.values() if value > epsilon]),
                    "child_avoided_loss_sum": float(sum(max(value, 0.0) for value in avoided.values())),
                    "winners": winner_rows,
                }
            )

        by_regime: dict[str, Any] = {}
        for bucket in ("NEGATIVE_BREADTH", "NEUTRAL_BREADTH", "POSITIVE_BREADTH", "UNAVAILABLE"):
            subset = [item for item in episodes if item["regime_bucket"] == bucket]
            if subset:
                by_regime[bucket] = _aggregate_episodes(subset)
        horizon_reports[str(horizon)] = {
            "horizon_sessions": horizon,
            "eligible_anchor_count": len(episodes),
            "aggregate": _aggregate_episodes(episodes),
            "by_regime": by_regime,
            "episodes": episodes,
        }

    stage_forward = pd.Series(
        np.prod(1.0 + returns.to_numpy(dtype=float), axis=0) - 1.0,
        index=returns.columns,
        dtype=float,
    )
    stage_winners = deterministic_top_fraction(stage_forward, fraction=winner_fraction)
    contribution_gap = ((parent_exec - child_exec) * returns).sum(axis=0)
    total_gap = float(contribution_gap.sum())
    top_winner_gap = float(contribution_gap.loc[list(stage_winners)].sum())
    stage_winner_rows = []
    for sid in stage_winners:
        identity = identities.get(sid, {})
        stage_winner_rows.append(
            {
                "security_id": sid,
                "ticker": identity.get("ticker"),
                "company_name": identity.get("company_name"),
                "stage_total_return": float(stage_forward[sid]),
                "opening_parent_executed_weight": float(parent_exec.iloc[1][sid]) if len(parent_exec) > 1 else 0.0,
                "ever_parent_exposed": bool(parent_exec[sid].gt(epsilon).any()),
                "parent_contribution": float((parent_exec[sid] * returns[sid]).sum()),
                "child_contribution": float((child_exec[sid] * returns[sid]).sum()),
                "parent_minus_child_contribution": float(contribution_gap[sid]),
            }
        )

    return {
        "stage": str(stage),
        "risk_set_count": len(rule.columns),
        "anchor_law": "RULE100_TARGET_STATE_CHANGE_DATES_FIRST_ROW_INCLUDED",
        "anchor_count": len(anchors),
        "anchor_dates": [value.date().isoformat() for value in anchors],
        "label_law": "DATE_LOCAL_TOP5PCT_NEXT_H_OBSERVED_SESSION_TOTAL_RETURN_EXCLUDING_ANCHOR",
        "winner_fraction": float(winner_fraction),
        "horizons": horizon_reports,
        "whole_stage_parent_child_attribution": {
            "daily_non_overlapping": True,
            "parent_minus_child_gross_contribution_gap": total_gap,
            "largest_realized_winner_count": len(stage_winners),
            "largest_realized_winners": stage_winner_rows,
            "largest_realized_winner_gap_contribution": top_winner_gap,
            "largest_realized_winner_gap_share": (
                float(top_winner_gap / total_gap) if abs(total_gap) > epsilon else None
            ),
        },
    }
