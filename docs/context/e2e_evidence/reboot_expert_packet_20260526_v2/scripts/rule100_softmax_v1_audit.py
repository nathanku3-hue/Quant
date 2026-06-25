"""Build Rule100 softmax v1 sizing audit artifacts.

The script is intentionally additive: it does not mutate the v0 lifecycle log,
position memory, UI method routing, provider data, or broker paths.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.portfolio_lifecycle_log import DEFAULT_LIFECYCLE_LOG_PATH  # noqa: E402
from data.portfolio_lifecycle_log import get_open_lifecycle_positions  # noqa: E402
from scripts.pit_lifecycle_replay import ACCUMULATION_DIST_MAX  # noqa: E402
from scripts.pit_lifecycle_replay import HARD_EXIT_DIST_SMA20  # noqa: E402
from scripts.pit_lifecycle_replay import PARABOLIC_DIST_SMA20  # noqa: E402
from scripts.pit_lifecycle_replay import RULE_OF_100_FACTOR_SOURCES  # noqa: E402
from strategies.rule100_softmax import KellyAblationConfig  # noqa: E402
from strategies.rule100_softmax import Rule100SoftmaxConfig  # noqa: E402
from strategies.rule100_softmax import compare_softmax_and_kelly  # noqa: E402
from strategies.rule100_softmax import score_rule100_candidates  # noqa: E402
from strategies.rule100_softmax import softmax_v1_weights  # noqa: E402
from strategies.rule100_softmax import summarize_weights  # noqa: E402


DEFAULT_FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "features.parquet"
DEFAULT_OUTPUT_PREFIX = PROJECT_ROOT / "data" / "processed" / "rule100_softmax_v1"
DEFAULT_DECISION_LOG_PATH = PROJECT_ROOT / "data" / "portfolio_lifecycle_decision_log.jsonl"
DEFAULT_HISTORY_PATH = DEFAULT_OUTPUT_PREFIX.with_name(DEFAULT_OUTPUT_PREFIX.name + "_history.csv")
HISTORY_COLUMNS = [
    "date",
    "ticker",
    "permno",
    "lifecycle_action",
    "buy_sell",
    "event_weight",
    "event_target_weight",
    "softmax_v1_target_weight",
    "softmax_v1_cash_residual",
    "softmax_v1_gross_weight",
    "sizing_eligible",
    "eligibility_reason",
    "factor_positive_count",
    "factor_present_count",
    "technical_quality",
    "score",
    "hold_days",
    "source",
]


def _resolve_path(path: Path | str | None, default: Path) -> Path:
    resolved = Path(path) if path is not None else default
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def _atomic_json_write(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(_json_safe(payload), handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _atomic_csv_write(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    os.close(fd)
    try:
        frame.to_csv(tmp, index=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _read_jsonl_frame(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()

    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSONL row {line_no} in {path}") from exc
    return pd.DataFrame(records)


def _coerce_as_of(as_of: str | pd.Timestamp | None) -> pd.Timestamp:
    if as_of is None:
        return pd.Timestamp.now().normalize()
    ts = pd.Timestamp(as_of)
    if ts.tzinfo is not None:
        ts = ts.tz_convert(None)
    return ts.normalize()


def _open_positions_frame(open_positions: dict[str, dict]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for ticker, payload in sorted((open_positions or {}).items()):
        rows.append(
            {
                "ticker": str(ticker).upper().strip(),
                "permno": payload.get("permno"),
                "entry_date": payload.get("entry_date", ""),
                "current_weight": payload.get("last_weight", 0.0),
                "position_source": payload.get("source", "lifecycle_replay"),
            }
        )
    return pd.DataFrame(rows)


def _latest_feature_rows(
    *,
    tickers: list[str],
    as_of: pd.Timestamp,
    features_path: Path,
) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame(columns=["ticker"])
    if not features_path.exists():
        raise FileNotFoundError(f"Missing features parquet: {features_path}")

    features = pd.read_parquet(features_path)
    if features.empty or "ticker" not in features.columns or "date" not in features.columns:
        return pd.DataFrame(columns=["ticker"])

    work = features.copy()
    work["ticker"] = work["ticker"].astype(str).str.upper().str.strip()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work[work["ticker"].isin(set(tickers)) & work["date"].notna() & (work["date"] <= as_of)].copy()
    if work.empty:
        return pd.DataFrame(columns=["ticker"])
    return (
        work.sort_values(["ticker", "date"], ascending=[True, True])
        .drop_duplicates(subset=["ticker"], keep="last")
        .reset_index(drop=True)
    )


def _boolean_series(values: pd.Series, default: bool = False) -> pd.Series:
    return values.astype("boolean").fillna(default).astype(bool)


def _coerce_decision_candidates(day: pd.DataFrame) -> pd.DataFrame:
    held = day[
        day.get("position_state_after", pd.Series("", index=day.index))
        .astype(str)
        .str.upper()
        .eq("HELD")
    ].copy()
    if held.empty:
        return pd.DataFrame(columns=HISTORY_COLUMNS)

    held["factor_present_count"] = (
        pd.to_numeric(held.get("factor_present_count"), errors="coerce")
        .fillna(0)
        .clip(lower=0)
        .astype(int)
    )
    held["factor_positive_count"] = (
        pd.to_numeric(held.get("factor_positive_count"), errors="coerce")
        .fillna(0)
        .clip(lower=0)
        .astype(int)
    )

    dist = (
        pd.to_numeric(held.get("dist_sma20"), errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .astype(float)
    )
    if "trend_veto" in held.columns:
        trend_veto = _boolean_series(held["trend_veto"], default=False)
    else:
        trend_veto = pd.Series(False, index=held.index, dtype=bool)

    hold_intact = (held["factor_present_count"] >= 3) & (held["factor_positive_count"] >= 2)
    hard_exit_candidate = trend_veto | (dist > float(HARD_EXIT_DIST_SMA20))
    proximity = (1.0 - (dist.clip(lower=0.0) / float(ACCUMULATION_DIST_MAX))).clip(lower=0.0, upper=1.0)
    hold_confirmed = hold_intact & ~hard_exit_candidate

    held["hold_intact"] = hold_intact.astype(float)
    held["technical_quality"] = np.where(
        hold_confirmed,
        1.0,
        proximity.where(~trend_veto & dist.notna(), 0.0),
    ).astype(float)
    held["trim_penalty"] = (
        (dist > float(PARABOLIC_DIST_SMA20)) & (dist <= float(HARD_EXIT_DIST_SMA20))
    ).astype(float)
    held["sizing_eligible"] = hold_confirmed.astype(bool)
    held["eligibility_reason"] = np.select(
        [
            hard_exit_candidate.to_numpy(dtype=bool),
            (~hold_intact).to_numpy(dtype=bool),
        ],
        [
            "exit_or_trend_veto_block",
            "tighten_below_hold_threshold",
        ],
        default="eligible_buy_or_hold",
    )
    held["current_weight"] = (
        pd.to_numeric(held.get("weight"), errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .clip(lower=0.0)
    )
    held["age_penalty"] = (
        pd.to_numeric(held.get("hold_days"), errors="coerce")
        .fillna(0)
        .clip(lower=0)
        .astype(float)
        / 90.0
    ).clip(lower=0.0, upper=1.0)
    return held


def build_rule100_softmax_v1_history(
    *,
    decision_log_path: Path | str | None = None,
    softmax_config: Rule100SoftmaxConfig | None = None,
) -> pd.DataFrame:
    """Build PIT daily Rule100 softmax v1 target-weight history.

    The returned frame is a derived sizing audit table. It preserves the
    lifecycle event weight as `event_weight` and writes the v1 sizing output
    into separate softmax columns.
    """

    decision_file = _resolve_path(decision_log_path, DEFAULT_DECISION_LOG_PATH)
    cfg = softmax_config or Rule100SoftmaxConfig()
    decisions = _read_jsonl_frame(decision_file)
    if decisions.empty:
        return pd.DataFrame(columns=HISTORY_COLUMNS)

    decisions = decisions.copy()
    decisions["date"] = pd.to_datetime(decisions.get("date"), errors="coerce")
    decisions = decisions[decisions["date"].notna()].sort_values(["date", "ticker"], kind="mergesort")
    if decisions.empty:
        return pd.DataFrame(columns=HISTORY_COLUMNS)

    rows: list[pd.DataFrame] = []
    for date_value, day in decisions.groupby(decisions["date"].dt.normalize(), sort=True):
        candidates = _coerce_decision_candidates(day)
        if candidates.empty:
            event_day = day[day.get("buy_sell", pd.Series(index=day.index, dtype=object)).isin(["SELL"])].copy()
            if event_day.empty:
                continue
            event_day["softmax_v1_target_weight"] = 0.0
            event_day["softmax_v1_cash_residual"] = 1.0
            event_day["softmax_v1_gross_weight"] = 0.0
            event_day["sizing_eligible"] = False
            event_day["eligibility_reason"] = "flat_after_event"
            event_day["technical_quality"] = 0.0
            event_day["score"] = np.nan
            rows.append(event_day)
            continue

        scored = score_rule100_candidates(candidates, cfg)
        scored["softmax_v1_target_weight"] = 0.0
        eligible = scored[scored["sizing_eligible"].astype(bool)].copy()
        if not eligible.empty:
            weights = softmax_v1_weights(eligible, cfg)
            scored.loc[weights.index, "softmax_v1_target_weight"] = weights.astype(float)
        summary = summarize_weights(scored["softmax_v1_target_weight"])
        scored["softmax_v1_cash_residual"] = float(summary["cash_residual"])
        scored["softmax_v1_gross_weight"] = float(summary["gross_weight"])
        rows.append(scored)

        sell_rows = day[
            day.get("buy_sell", pd.Series(index=day.index, dtype=object)).astype(str).str.upper().eq("SELL")
        ].copy()
        if not sell_rows.empty:
            sell_rows["softmax_v1_target_weight"] = 0.0
            sell_rows["softmax_v1_cash_residual"] = float(summary["cash_residual"])
            sell_rows["softmax_v1_gross_weight"] = float(summary["gross_weight"])
            sell_rows["sizing_eligible"] = False
            sell_rows["eligibility_reason"] = "flat_after_sell"
            sell_rows["technical_quality"] = 0.0
            sell_rows["score"] = np.nan
            rows.append(sell_rows)

    if not rows:
        return pd.DataFrame(columns=HISTORY_COLUMNS)

    history = pd.concat(rows, ignore_index=True, sort=False)
    history["date"] = pd.to_datetime(history["date"], errors="coerce").dt.date.astype(str)
    history["ticker"] = history.get("ticker", "").astype(str).str.upper().str.strip()
    history["event_weight"] = (
        pd.to_numeric(history.get("weight"), errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .clip(lower=0.0)
    )
    history["event_target_weight"] = (
        pd.to_numeric(history.get("target_weight"), errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(history["event_weight"])
        .clip(lower=0.0)
    )
    history["source"] = "rule100_softmax_v1_history"

    for col in ("softmax_v1_target_weight", "softmax_v1_cash_residual", "softmax_v1_gross_weight"):
        history[col] = (
            pd.to_numeric(history.get(col), errors="coerce")
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0.0)
            .clip(lower=0.0)
        )

    for col in ("factor_positive_count", "factor_present_count", "hold_days"):
        history[col] = pd.to_numeric(history.get(col), errors="coerce").fillna(0).astype(int)
    history["technical_quality"] = pd.to_numeric(history.get("technical_quality"), errors="coerce").fillna(0.0)
    history["score"] = pd.to_numeric(history.get("score"), errors="coerce")
    history["sizing_eligible"] = history.get("sizing_eligible", False).astype(bool)

    for col in HISTORY_COLUMNS:
        if col not in history.columns:
            history[col] = np.nan

    return (
        history[HISTORY_COLUMNS]
        .sort_values(["date", "ticker", "buy_sell"], ascending=[True, True, True], kind="mergesort")
        .reset_index(drop=True)
    )


def write_rule100_softmax_v1_history(
    *,
    output_path: Path | str | None = None,
    decision_log_path: Path | str | None = None,
    softmax_config: Rule100SoftmaxConfig | None = None,
) -> pd.DataFrame:
    """Build and atomically write the PIT softmax v1 history artifact."""

    output_file = _resolve_path(output_path, DEFAULT_HISTORY_PATH)
    history = build_rule100_softmax_v1_history(
        decision_log_path=decision_log_path,
        softmax_config=softmax_config,
    )
    _atomic_csv_write(history, output_file)
    return history


def build_current_rule100_candidate_frame(
    *,
    as_of: str | pd.Timestamp | None = None,
    features_path: Path | str | None = None,
    lifecycle_path: Path | str | None = None,
) -> pd.DataFrame:
    """Build a PIT-safe candidate frame from current open lifecycle holds."""

    cutoff = _coerce_as_of(as_of)
    features_file = _resolve_path(features_path, DEFAULT_FEATURES_PATH)
    lifecycle_file = _resolve_path(lifecycle_path, PROJECT_ROOT / DEFAULT_LIFECYCLE_LOG_PATH)
    open_positions = get_open_lifecycle_positions(as_of=cutoff, path=lifecycle_file)
    positions = _open_positions_frame(open_positions)
    if positions.empty:
        return pd.DataFrame(
            columns=[
                "ticker",
                "permno",
                "entry_date",
                "current_weight",
                "feature_date",
                "factor_present_count",
                "factor_positive_count",
                "technical_quality",
                "hold_intact",
                "age_penalty",
                "trim_penalty",
            ]
        )

    latest = _latest_feature_rows(
        tickers=positions["ticker"].astype(str).tolist(),
        as_of=cutoff,
        features_path=features_file,
    )
    merged = positions.merge(latest, on="ticker", how="left", suffixes=("", "_feature"))
    if "permno_feature" in merged.columns:
        merged["permno"] = merged["permno"].where(merged["permno"].notna(), merged["permno_feature"])
        merged.drop(columns=["permno_feature"], inplace=True)

    factor_cols = tuple(dict.fromkeys(RULE_OF_100_FACTOR_SOURCES.values()))
    for col in factor_cols:
        if col not in merged.columns:
            merged[col] = np.nan
    factors = merged.loc[:, factor_cols].apply(pd.to_numeric, errors="coerce")
    merged["factor_present_count"] = factors.notna().sum(axis=1).astype(int)
    merged["factor_positive_count"] = (factors > 0.0).sum(axis=1).astype(int)
    merged["factor_strength"] = np.where(
        merged["factor_present_count"] > 0,
        merged["factor_positive_count"] / merged["factor_present_count"],
        0.0,
    )

    if "dist_sma20" not in merged.columns:
        merged["dist_sma20"] = np.nan
    dist = (
        pd.to_numeric(merged["dist_sma20"], errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .astype(float)
    )
    if "trend_veto" in merged.columns:
        trend_veto = _boolean_series(merged["trend_veto"], default=False)
    else:
        trend_veto = pd.Series(False, index=merged.index, dtype=bool)
    merged["hold_intact"] = (
        (merged["factor_present_count"] >= 3) & (merged["factor_positive_count"] >= 2)
    ).astype(float)
    hard_exit_candidate = trend_veto | (dist > float(HARD_EXIT_DIST_SMA20))
    proximity = (1.0 - (dist.clip(lower=0.0) / float(ACCUMULATION_DIST_MAX))).clip(lower=0.0, upper=1.0)
    hold_confirmed = (merged["hold_intact"] > 0.0) & ~hard_exit_candidate
    merged["technical_quality"] = np.where(
        hold_confirmed,
        1.0,
        proximity.where(~trend_veto & dist.notna(), 0.0),
    ).astype(float)
    merged["trim_penalty"] = (
        (dist > float(PARABOLIC_DIST_SMA20)) & (dist <= float(HARD_EXIT_DIST_SMA20))
    ).astype(float)
    merged["sizing_eligible"] = hold_confirmed.astype(bool)
    merged["eligibility_reason"] = np.select(
        [
            hard_exit_candidate.to_numpy(dtype=bool),
            (merged["hold_intact"] <= 0.0).to_numpy(dtype=bool),
        ],
        [
            "exit_or_trend_veto_block",
            "tighten_below_hold_threshold",
        ],
        default="eligible_buy_or_hold",
    )

    entry_dates = pd.to_datetime(merged["entry_date"], errors="coerce")
    hold_days = (cutoff - entry_dates).dt.days
    merged["hold_days"] = pd.to_numeric(hold_days, errors="coerce").fillna(0).clip(lower=0).astype(int)
    merged["age_penalty"] = (merged["hold_days"] / 90.0).clip(lower=0.0, upper=1.0)
    merged["feature_date"] = pd.to_datetime(merged.get("date"), errors="coerce")
    merged["current_weight"] = (
        pd.to_numeric(merged["current_weight"], errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .clip(lower=0.0)
    )
    return merged.sort_values(["ticker"], kind="mergesort").reset_index(drop=True)


def run_rule100_softmax_v1_audit(
    *,
    as_of: str | pd.Timestamp | None = None,
    features_path: Path | str | None = None,
    lifecycle_path: Path | str | None = None,
    decision_log_path: Path | str | None = None,
    output_prefix: Path | str | None = None,
    softmax_config: Rule100SoftmaxConfig | None = None,
    kelly_config: KellyAblationConfig | None = None,
) -> dict[str, Any]:
    """Run the shared softmax/Kelly audit harness and write artifacts."""

    cutoff = _coerce_as_of(as_of)
    prefix = _resolve_path(output_prefix, DEFAULT_OUTPUT_PREFIX)
    comparison_path = prefix.with_name(prefix.name + "_comparison.csv")
    sample_path = prefix.with_name(prefix.name + "_sample_output.csv")
    cash_path = prefix.with_name(prefix.name + "_cash_allocation.csv")
    history_path = prefix.with_name(prefix.name + "_history.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")

    cfg = softmax_config or Rule100SoftmaxConfig()
    kcfg = kelly_config or KellyAblationConfig(
        max_single_name_weight=cfg.max_single_name_weight,
        gross_budget_per_name=cfg.gross_budget_per_name,
        gross_budget_cap=cfg.gross_budget_cap,
    )

    candidates = build_current_rule100_candidate_frame(
        as_of=cutoff,
        features_path=features_path,
        lifecycle_path=lifecycle_path,
    )
    eligible_mask = candidates.get(
        "sizing_eligible",
        pd.Series(False, index=candidates.index, dtype=bool),
    ).astype(bool)
    eligible_candidates = candidates.loc[eligible_mask].copy()
    eligible_comparison, sizing_summary = compare_softmax_and_kelly(
        eligible_candidates,
        softmax_config=cfg,
        kelly_config=kcfg,
    )
    comparison = score_rule100_candidates(candidates, cfg)
    comparison["softmax_weight"] = 0.0
    comparison["kelly_weight"] = 0.0
    if not eligible_comparison.empty and "ticker" in eligible_comparison.columns:
        weights = eligible_comparison.set_index("ticker")
        for col in ("softmax_weight", "kelly_weight"):
            mapped = comparison["ticker"].map(weights[col])
            comparison[col] = mapped.fillna(comparison[col]).astype(float)
    comparison["weight_delta_softmax_minus_kelly"] = comparison["softmax_weight"] - comparison["kelly_weight"]
    sort_cols = [col for col in ("sizing_eligible", "score", "ticker") if col in comparison.columns]
    if sort_cols:
        ascending = [False if col in {"sizing_eligible", "score"} else True for col in sort_cols]
        comparison = comparison.sort_values(
            sort_cols,
            ascending=ascending,
            kind="mergesort",
        ).reset_index(drop=True)

    if not comparison.empty and "current_weight" in comparison.columns:
        current = pd.to_numeric(comparison["current_weight"], errors="coerce").fillna(0.0)
        comparison["softmax_delta_from_current"] = comparison["softmax_weight"] - current
        comparison["kelly_delta_from_current"] = comparison["kelly_weight"] - current
    elif not comparison.empty:
        comparison["softmax_delta_from_current"] = comparison["softmax_weight"]
        comparison["kelly_delta_from_current"] = comparison["kelly_weight"]

    current_summary = summarize_weights(comparison["current_weight"]) if "current_weight" in comparison.columns else summarize_weights(pd.Series(dtype=float))
    cash_rows = [
        {"policy": "current_v0_last_weight", **current_summary},
        {"policy": "softmax_v1_primary", **sizing_summary["softmax"]},
        {"policy": "kelly_ablation_comparator", **sizing_summary["kelly_ablation"]},
    ]
    cash = pd.DataFrame(cash_rows)

    sample_cols = [
        "ticker",
        "permno",
        "sizing_eligible",
        "eligibility_reason",
        "current_weight",
        "factor_positive_count",
        "technical_quality",
        "score",
        "softmax_weight",
        "kelly_weight",
        "softmax_delta_from_current",
        "kelly_delta_from_current",
    ]
    sample = comparison[[col for col in sample_cols if col in comparison.columns]].copy()

    _atomic_csv_write(comparison, comparison_path)
    _atomic_csv_write(sample, sample_path)
    _atomic_csv_write(cash, cash_path)
    history = build_rule100_softmax_v1_history(
        decision_log_path=decision_log_path,
        softmax_config=cfg,
    )
    _atomic_csv_write(history, history_path)

    feature_dates = []
    if "feature_date" in comparison.columns:
        feature_dates = [
            pd.Timestamp(v).date().isoformat()
            for v in pd.to_datetime(comparison["feature_date"], errors="coerce").dropna().unique()
        ]
    summary: dict[str, Any] = {
        "status": "ok" if len(comparison) else "cash_only",
        "scope": "rule100_softmax_v1_audit",
        "as_of_date": cutoff.date().isoformat(),
        "feature_dates_used": sorted(feature_dates),
        "softmax_config": asdict(cfg),
        "kelly_config": asdict(kcfg),
        "sizing_summary": sizing_summary,
        "current_v0_summary": current_summary,
        "boundary": {
            "softmax_v1_primary": True,
            "kelly_comparator_only": True,
            "mutates_lifecycle_log": False,
            "mutates_position_memory": False,
            "runtime_ui_wiring_changed": False,
            "broker_or_alert_behavior": False,
        },
        "artifacts": {
            "comparison_csv": str(comparison_path),
            "sample_csv": str(sample_path),
            "cash_csv": str(cash_path),
            "history_csv": str(history_path),
            "summary_json": str(summary_path),
        },
    }
    _atomic_json_write(summary, summary_path)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Rule100 softmax v1 sizing audit artifacts.")
    parser.add_argument("--as-of-date", default=None)
    parser.add_argument("--features-path", default=str(DEFAULT_FEATURES_PATH))
    parser.add_argument("--lifecycle-path", default=str(PROJECT_ROOT / DEFAULT_LIFECYCLE_LOG_PATH))
    parser.add_argument("--decision-log-path", default=str(DEFAULT_DECISION_LOG_PATH))
    parser.add_argument("--output-prefix", default=str(DEFAULT_OUTPUT_PREFIX))
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--max-single-name-weight", type=float, default=0.15)
    parser.add_argument("--kelly-odds", type=float, default=1.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_rule100_softmax_v1_audit(
        as_of=args.as_of_date,
        features_path=args.features_path,
        lifecycle_path=args.lifecycle_path,
        decision_log_path=args.decision_log_path,
        output_prefix=args.output_prefix,
        softmax_config=Rule100SoftmaxConfig(
            temperature=float(args.temperature),
            max_single_name_weight=float(args.max_single_name_weight),
        ),
        kelly_config=KellyAblationConfig(
            odds=float(args.kelly_odds),
            max_single_name_weight=float(args.max_single_name_weight),
        ),
    )
    artifacts = summary.get("artifacts", {})
    print("Rule100 softmax v1 audit complete")
    print(f"Status: {summary.get('status')}")
    print(f"Summary: {artifacts.get('summary_json')}")
    print(f"Comparison: {artifacts.get('comparison_csv')}")
    print(f"History: {artifacts.get('history_csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
