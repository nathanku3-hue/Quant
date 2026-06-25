"""Build Rule100 softmax v1.1 sizing audit artifacts (approved expert contract).

Writes separate artifacts from v1:
- rule100_softmax_v1_1_comparison.csv
- rule100_softmax_v1_1_summary.json

Does NOT mutate v1 artifacts, lifecycle log, position memory, or UI routing.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.portfolio_lifecycle_log import DEFAULT_LIFECYCLE_LOG_PATH  # noqa: E402
from data.portfolio_lifecycle_log import get_open_lifecycle_positions  # noqa: E402
from scripts.pit_lifecycle_replay import RULE_OF_100_FACTOR_SOURCES  # noqa: E402
from strategies.rule100_softmax import summarize_weights  # noqa: E402
from strategies.rule100_softmax_v1_1 import (  # noqa: E402
    Rule100SoftmaxV1_1Config,
    V1_1_FACTOR_GROUPS,
    compute_factor_group_counts,
    compute_factor_strength_continuous,
    compute_staleness_penalty,
    compute_technical_quality_continuous,
    lifecycle_state_multiplier,
    score_v1_1_candidates,
    softmax_v1_1_weights,
)

DEFAULT_FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "features.parquet"
DEFAULT_DECISION_LOG_PATH = PROJECT_ROOT / "data" / "portfolio_lifecycle_decision_log.jsonl"
DEFAULT_OUTPUT_PREFIX = PROJECT_ROOT / "data" / "processed" / "rule100_softmax_v1_1"


def _resolve_path(path: Path | str | None, default: Path) -> Path:
    resolved = Path(path) if path is not None else default
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved


def _atomic_write(content: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _retire_stale_history_artifact(prefix: Path) -> dict[str, Any]:
    """Move the removed v1.1 history artifact out of the active contract."""
    legacy_path = prefix.with_name(prefix.name + "_history.csv")
    retired_path = legacy_path.with_name(f"{legacy_path.stem}.retired{legacy_path.suffix}")
    if not legacy_path.exists():
        return {
            "legacy_history_csv": str(legacy_path),
            "status": "absent",
            "current_contract": "comparison_csv_and_summary_json_only",
        }
    os.replace(legacy_path, retired_path)
    return {
        "legacy_history_csv": str(legacy_path),
        "retired_csv": str(retired_path),
        "status": "retired",
        "current_contract": "comparison_csv_and_summary_json_only",
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def _read_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return pd.DataFrame(records)


def _latest_lifecycle_state(
    decisions: pd.DataFrame,
    tickers: list[str],
    as_of: pd.Timestamp,
) -> dict[str, str]:
    """Get latest lifecycle_action per ticker as of date."""
    if decisions.empty:
        return {t: "HOLD" for t in tickers}
    df = decisions.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df[df["date"].notna() & (df["date"] <= as_of) & df["ticker"].isin(tickers)]
    if df.empty:
        return {t: "HOLD" for t in tickers}
    latest = df.sort_values("date").drop_duplicates("ticker", keep="last")
    return {
        row["ticker"]: str(row.get("lifecycle_action", "HOLD")).upper()
        for _, row in latest.iterrows()
    }


def _days_since_factor_change(
    decisions: pd.DataFrame,
    ticker: str,
    as_of: pd.Timestamp,
) -> float:
    """Days since factor_positive_count last changed for a ticker."""
    if decisions.empty or "ticker" not in decisions.columns:
        return 0.0
    tf = decisions[decisions["ticker"] == ticker].copy()
    if tf.empty:
        return 0.0
    tf["date"] = pd.to_datetime(tf["date"], errors="coerce")
    tf = tf[tf["date"].notna() & (tf["date"] <= as_of)].sort_values("date")
    fpc = pd.to_numeric(tf.get("factor_positive_count"), errors="coerce")
    if fpc.notna().sum() < 2:
        return 0.0
    changes = fpc.diff().ne(0) & fpc.notna()
    change_dates = tf.loc[changes.values, "date"]
    if change_dates.empty:
        return 0.0
    return max(0.0, (as_of - change_dates.max()).days)


def build_v1_1_candidate_frame(
    *,
    as_of: str | pd.Timestamp | None = None,
    features_path: Path | str | None = None,
    lifecycle_path: Path | str | None = None,
    decision_log_path: Path | str | None = None,
    config: Rule100SoftmaxV1_1Config | None = None,
) -> pd.DataFrame:
    """Build PIT-safe v1.1 candidate frame from current open holds."""
    cfg = config or Rule100SoftmaxV1_1Config()
    cutoff = pd.Timestamp(as_of) if as_of else pd.Timestamp.now().normalize()
    if cutoff.tzinfo:
        cutoff = cutoff.tz_convert(None)
    cutoff = cutoff.normalize()

    features_file = _resolve_path(features_path, DEFAULT_FEATURES_PATH)
    lifecycle_file = _resolve_path(lifecycle_path, PROJECT_ROOT / DEFAULT_LIFECYCLE_LOG_PATH)
    decision_file = _resolve_path(decision_log_path, DEFAULT_DECISION_LOG_PATH)

    open_positions = get_open_lifecycle_positions(as_of=cutoff, path=lifecycle_file)
    if not open_positions:
        return pd.DataFrame()

    tickers = sorted(open_positions.keys())

    # Full cross-section for percentile ranking
    features = pd.read_parquet(features_file)
    features["date"] = pd.to_datetime(features["date"], errors="coerce")
    features["ticker"] = features["ticker"].astype(str).str.upper().str.strip()
    all_latest = (
        features[features["date"].notna() & (features["date"] <= cutoff)]
        .sort_values(["ticker", "date"])
        .drop_duplicates(subset=["ticker"], keep="last")
        .reset_index(drop=True)
    )

    # Factor strength: ranked over full cross-section
    all_latest["factor_strength_continuous"] = compute_factor_strength_continuous(all_latest)

    # Technical quality: computed over full cross-section
    all_latest["technical_quality_continuous"] = compute_technical_quality_continuous(all_latest)

    # Narrow to held tickers
    latest = all_latest[all_latest["ticker"].isin(tickers)].copy().reset_index(drop=True)

    # Hold intact (using one signal per approved factor group)
    factor_counts = compute_factor_group_counts(latest, V1_1_FACTOR_GROUPS)
    latest["factor_present_count"] = factor_counts["factor_present_count"].astype(int)
    latest["factor_positive_count"] = factor_counts["factor_positive_count"].astype(int)
    latest["hold_intact"] = (
        (latest["factor_present_count"] >= 3) & (latest["factor_positive_count"] >= 2)
    ).astype(float)

    # Staleness penalty
    decisions = _read_jsonl(decision_file)
    latest["days_since_factor_change"] = latest["ticker"].apply(
        lambda t: _days_since_factor_change(decisions, t, cutoff)
    )
    latest["staleness_penalty"] = compute_staleness_penalty(
        latest["days_since_factor_change"], saturation_days=cfg.staleness_saturation_days
    )

    # Lifecycle state from decision log
    state_map = _latest_lifecycle_state(decisions, tickers, cutoff)
    latest["lifecycle_state"] = latest["ticker"].map(state_map).fillna("HOLD")

    # Entry metadata
    for ticker in tickers:
        pos = open_positions[ticker]
        mask = latest["ticker"] == ticker
        latest.loc[mask, "entry_date"] = pos.get("entry_date", "")
        latest.loc[mask, "current_weight"] = pos.get("last_weight", 0.0)

    entry_dates = pd.to_datetime(latest["entry_date"], errors="coerce")
    latest["hold_days"] = (cutoff - entry_dates).dt.days.fillna(0).clip(lower=0).astype(int)
    latest["source"] = "rule100_softmax_v1_1"
    return latest.sort_values("ticker").reset_index(drop=True)


def run_v1_1_audit(
    *,
    as_of: str | pd.Timestamp | None = None,
    features_path: Path | str | None = None,
    lifecycle_path: Path | str | None = None,
    decision_log_path: Path | str | None = None,
    output_prefix: Path | str | None = None,
    config: Rule100SoftmaxV1_1Config | None = None,
) -> dict[str, Any]:
    """Run v1.1 audit and write artifacts."""
    cfg = config or Rule100SoftmaxV1_1Config()
    prefix = _resolve_path(output_prefix, DEFAULT_OUTPUT_PREFIX)
    comparison_path = prefix.with_name(prefix.name + "_comparison.csv")
    summary_path = prefix.with_name(prefix.name + "_summary.json")
    retired_artifacts = _retire_stale_history_artifact(prefix)

    candidates = build_v1_1_candidate_frame(
        as_of=as_of,
        features_path=features_path,
        lifecycle_path=lifecycle_path,
        decision_log_path=decision_log_path,
        config=cfg,
    )

    if candidates.empty:
        empty_summary = {
            "status": "cash_only",
            "scope": "rule100_softmax_v1_1_audit",
            "eligible_count": 0,
            "config": asdict(cfg),
            "artifacts": {"comparison_csv": str(comparison_path), "summary_json": str(summary_path)},
            "retired_artifacts": retired_artifacts,
            "boundary": {"mutates_v1": False, "research_only": True},
        }
        _atomic_write(json.dumps(_json_safe(empty_summary), indent=2) + "\n", summary_path)
        _atomic_write(pd.DataFrame().to_csv(index=False), comparison_path)
        return empty_summary

    # Score and size
    scored = score_v1_1_candidates(candidates, cfg)
    scored["sizing_eligible"] = scored["hold_intact"] >= 1.0

    # Weights (lifecycle multiplier applied inside softmax_v1_1_weights)
    scored["v1_1_target_weight"] = 0.0
    eligible = scored[scored["sizing_eligible"]].copy()
    if not eligible.empty:
        weights = softmax_v1_1_weights(eligible, cfg)
        scored.loc[weights.index, "v1_1_target_weight"] = weights.values

    # Lifecycle multiplier column for audit
    scored["lifecycle_multiplier"] = lifecycle_state_multiplier(scored["lifecycle_state"])

    weight_summary = summarize_weights(scored["v1_1_target_weight"])

    # Write comparison
    comparison_cols = [
        "ticker", "lifecycle_state", "lifecycle_multiplier",
        "factor_strength_continuous", "technical_quality_continuous",
        "hold_intact", "staleness_penalty", "score_v1_1",
        "sizing_eligible", "v1_1_target_weight",
        "current_weight", "hold_days", "days_since_factor_change",
        "factor_present_count", "factor_positive_count", "source",
    ]
    comparison = scored[[c for c in comparison_cols if c in scored.columns]].copy()
    comparison["delta_from_current"] = comparison["v1_1_target_weight"] - pd.to_numeric(
        comparison.get("current_weight", 0.0), errors="coerce"
    ).fillna(0.0)
    _atomic_write(comparison.to_csv(index=False), comparison_path)

    cutoff_str = (pd.Timestamp(as_of) if as_of else pd.Timestamp.now()).normalize().date().isoformat()
    summary: dict[str, Any] = {
        "status": "ok",
        "scope": "rule100_softmax_v1_1_audit",
        "as_of_date": cutoff_str,
        "eligible_count": int(scored["sizing_eligible"].sum()),
        "total_candidates": len(scored),
        "config": asdict(cfg),
        "weight_summary": weight_summary,
        "artifacts": {"comparison_csv": str(comparison_path), "summary_json": str(summary_path)},
        "retired_artifacts": retired_artifacts,
        "boundary": {
            "mutates_v1": False,
            "mutates_lifecycle_log": False,
            "mutates_position_memory": False,
            "research_only": True,
        },
    }
    _atomic_write(json.dumps(_json_safe(summary), indent=2, sort_keys=True) + "\n", summary_path)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rule100 softmax v1.1 research audit.")
    parser.add_argument("--as-of-date", default=None)
    parser.add_argument("--features-path", default=str(DEFAULT_FEATURES_PATH))
    parser.add_argument("--lifecycle-path", default=str(PROJECT_ROOT / DEFAULT_LIFECYCLE_LOG_PATH))
    parser.add_argument("--decision-log-path", default=str(DEFAULT_DECISION_LOG_PATH))
    parser.add_argument("--output-prefix", default=str(DEFAULT_OUTPUT_PREFIX))
    parser.add_argument("--temperature", type=float, default=1.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_v1_1_audit(
        as_of=args.as_of_date,
        features_path=args.features_path,
        lifecycle_path=args.lifecycle_path,
        decision_log_path=args.decision_log_path,
        output_prefix=args.output_prefix,
        config=Rule100SoftmaxV1_1Config(temperature=args.temperature),
    )
    print(f"v1.1 audit complete - status: {summary['status']}")
    for k, v in summary.get("artifacts", {}).items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
