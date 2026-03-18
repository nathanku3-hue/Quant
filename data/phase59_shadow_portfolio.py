from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from data.research_connector import PROJECT_ROOT
from data.research_connector import connect_research
from utils.metrics import compute_cagr
from utils.metrics import compute_max_drawdown
from utils.metrics import compute_ulcer_index
from utils.statistics import safe_sharpe


DEFAULT_BASELINE_SUMMARY_PATH = (
    PROJECT_ROOT / "data" / "processed" / "phase54_core_sleeve_summary.json"
)
DEFAULT_PHASE54_TOP20_EXPOSURE_PATH = (
    PROJECT_ROOT / "data" / "processed" / "phase54_core_sleeve_top20_exposure.csv"
)
DEFAULT_PHASE54_SAMPLE_OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "phase54_core_sleeve_sample_output.csv"
)
DEFAULT_PHASE55_EVIDENCE_PATH = (
    PROJECT_ROOT / "data" / "processed" / "phase55_allocator_cpcv_evidence.json"
)
DEFAULT_PHASE50_ROOT = PROJECT_ROOT / "data" / "processed" / "phase50_shadow_ship"
DEFAULT_PHASE50_CURVE_PATH = DEFAULT_PHASE50_ROOT / "phase50_curve_full_20260410.csv"
DEFAULT_PHASE50_TELEMETRY_PATH = (
    DEFAULT_PHASE50_ROOT / "phase50_aggregated_telemetry_20260410.json"
)
DEFAULT_PHASE50_GATE_PATH = DEFAULT_PHASE50_ROOT / "gate_recommendation.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "data" / "processed" / "phase59_shadow_summary.json"
DEFAULT_EVIDENCE_PATH = PROJECT_ROOT / "data" / "processed" / "phase59_shadow_evidence.csv"
DEFAULT_DELTA_PATH = PROJECT_ROOT / "data" / "processed" / "phase59_shadow_delta_vs_c3.csv"
RESEARCH_MAX_DATE = pd.Timestamp("2022-12-31")
SHADOW_PACKET_ID = "PHASE59_SHADOW_MONITOR_V1"
_POSITIONS_RE = re.compile(r"paper_curve_positions_day(\d+)\.csv$", re.IGNORECASE)
_SEVERITY_RANK = {"GREEN": 0, "YELLOW": 1, "RED": 2}


@dataclass(frozen=True)
class ShadowPortfolioConfig:
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    max_date: pd.Timestamp
    cost_bps: float
    summary_path: Path = DEFAULT_SUMMARY_PATH
    evidence_path: Path = DEFAULT_EVIDENCE_PATH
    delta_path: Path = DEFAULT_DELTA_PATH
    baseline_summary_path: Path = DEFAULT_BASELINE_SUMMARY_PATH
    phase54_top20_exposure_path: Path = DEFAULT_PHASE54_TOP20_EXPOSURE_PATH
    phase54_sample_output_path: Path = DEFAULT_PHASE54_SAMPLE_OUTPUT_PATH
    phase55_evidence_path: Path = DEFAULT_PHASE55_EVIDENCE_PATH
    phase50_curve_path: Path = DEFAULT_PHASE50_CURVE_PATH
    phase50_telemetry_path: Path = DEFAULT_PHASE50_TELEMETRY_PATH
    phase50_gate_path: Path = DEFAULT_PHASE50_GATE_PATH
    phase50_root: Path = DEFAULT_PHASE50_ROOT
    starting_notional_equity: float = 100_000.0


def validate_config(cfg: ShadowPortfolioConfig) -> None:
    if cfg.max_date > RESEARCH_MAX_DATE:
        raise ValueError(
            f"max_date must be <= {RESEARCH_MAX_DATE.date()}, got {cfg.max_date.date()}"
        )
    if cfg.end_date > cfg.max_date:
        raise ValueError(
            f"end_date must be <= max_date ({cfg.max_date.date()}), got {cfg.end_date.date()}"
        )
    if cfg.start_date > cfg.end_date:
        raise ValueError("start_date must be <= end_date")
    if float(cfg.cost_bps) <= 0.0:
        raise ValueError("cost_bps must be > 0")


def load_baseline_summary(cfg: ShadowPortfolioConfig) -> dict[str, Any]:
    payload = json.loads(cfg.baseline_summary_path.read_text(encoding="utf-8"))
    try:
        window = payload["window"]
        baseline_start = pd.Timestamp(window["start_date"])
        baseline_end = pd.Timestamp(window["end_date"])
        baseline_cost_bps = float(payload["cost_bps"])
        baseline_config_id = str(payload["baseline_config_id"])
        baseline_metrics = payload["metrics"]["c3"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"Baseline summary missing required Phase 54 C3 fields: {cfg.baseline_summary_path}"
        ) from exc

    if baseline_start != cfg.start_date or baseline_end != cfg.end_date:
        raise ValueError(
            "Baseline window mismatch: "
            f"expected {cfg.start_date.date()} -> {cfg.end_date.date()}, "
            f"got {baseline_start.date()} -> {baseline_end.date()}"
        )
    if abs(baseline_cost_bps - float(cfg.cost_bps)) > 1e-9:
        raise ValueError(
            f"Baseline cost_bps mismatch: expected {cfg.cost_bps}, got {baseline_cost_bps}"
        )

    return {
        "baseline_config_id": baseline_config_id,
        "baseline_cost_bps": baseline_cost_bps,
        "baseline_metrics_c3": {
            "sharpe": float(baseline_metrics["sharpe"]),
            "cagr": float(baseline_metrics["cagr"]),
            "max_dd": float(baseline_metrics["max_dd"]),
            "ulcer": float(baseline_metrics["ulcer"]),
            "turnover_annual": float(baseline_metrics["turnover_annual"]),
            "turnover_total": float(baseline_metrics["turnover_total"]),
        },
    }


def select_phase55_variant(cfg: ShadowPortfolioConfig) -> dict[str, Any]:
    payload = json.loads(cfg.phase55_evidence_path.read_text(encoding="utf-8"))
    fold_results = payload.get("fold_results")
    if not isinstance(fold_results, list) or not fold_results:
        raise ValueError("Phase 55 evidence does not contain fold_results")

    frame = pd.DataFrame(fold_results)
    required_cols = {"selected_variant", "outer_test_sharpe", "positive_outer_fold"}
    missing = required_cols.difference(frame.columns)
    if missing:
        raise ValueError(f"Phase 55 evidence missing required columns: {sorted(missing)}")

    grouped = (
        frame.groupby("selected_variant", as_index=False)
        .agg(
            selection_count=("selected_variant", "size"),
            median_outer_test_sharpe=("outer_test_sharpe", "median"),
            mean_outer_test_sharpe=("outer_test_sharpe", "mean"),
            positive_outer_fold_share=("positive_outer_fold", "mean"),
        )
        .sort_values(
            by=["selection_count", "median_outer_test_sharpe", "selected_variant"],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)
    )
    winner = grouped.iloc[0]
    return {
        "variant_id": str(winner["selected_variant"]),
        "selection_count": int(winner["selection_count"]),
        "median_outer_test_sharpe": float(winner["median_outer_test_sharpe"]),
        "mean_outer_test_sharpe": float(winner["mean_outer_test_sharpe"]),
        "positive_outer_fold_share": float(winner["positive_outer_fold_share"]),
        "selection_policy": (
            "selected_variant = argmax(selection_count, median_outer_test_sharpe, "
            "variant_id_ascending)"
        ),
        "source_path": str(cfg.phase55_evidence_path),
    }


def _fetch_catalog_meta() -> dict[str, Any]:
    conn = connect_research()
    try:
        meta = conn.execute(
            """
            SELECT
                COUNT(*) AS rows,
                COUNT(DISTINCT variant_id) AS distinct_variants,
                MIN(snapshot_date) AS min_snapshot_date,
                MAX(snapshot_date) AS max_snapshot_date
            FROM allocator_state
            """
        ).fetchone()
    finally:
        conn.close()

    if meta is None:
        raise ValueError("allocator_state catalog metadata query returned no rows")

    rows, distinct_variants, min_snapshot_date, max_snapshot_date = meta
    return {
        "rows": int(rows),
        "distinct_variants": int(distinct_variants),
        "min_snapshot_date": pd.Timestamp(min_snapshot_date).date().isoformat(),
        "max_snapshot_date": pd.Timestamp(max_snapshot_date).date().isoformat(),
    }


def _query_variant_returns(
    cfg: ShadowPortfolioConfig,
    variant_id: str,
) -> pd.DataFrame:
    conn = connect_research()
    try:
        frame = conn.execute(
            """
            SELECT snapshot_date, period_return
            FROM allocator_state
            WHERE variant_id = ?
              AND snapshot_date >= ?
              AND snapshot_date <= ?
            ORDER BY snapshot_date ASC
            """,
            [variant_id, cfg.start_date.date(), cfg.max_date.date()],
        ).fetchdf()
    finally:
        conn.close()

    if frame.empty:
        raise ValueError(f"allocator_state contains no rows for variant_id={variant_id}")
    frame["snapshot_date"] = pd.to_datetime(frame["snapshot_date"], errors="coerce").dt.normalize()
    frame["period_return"] = pd.to_numeric(frame["period_return"], errors="coerce").fillna(0.0)
    frame = frame.dropna(subset=["snapshot_date"]).reset_index(drop=True)
    return frame


def _build_research_surface(
    cfg: ShadowPortfolioConfig,
    selected_variant: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    observed = _query_variant_returns(cfg, selected_variant["variant_id"])
    observed = observed.rename(columns={"snapshot_date": "date", "period_return": "net_ret"})
    calendar = pd.DataFrame(index=pd.bdate_range(cfg.start_date, cfg.end_date, freq="B"))
    calendar.index.name = "date"
    daily = calendar.join(observed.set_index("date"), how="left")
    daily["is_observed_day"] = daily["net_ret"].notna()
    daily["net_ret"] = daily["net_ret"].fillna(0.0).astype(float)
    daily["equity"] = (1.0 + daily["net_ret"]).cumprod()
    daily["notional_equity"] = float(cfg.starting_notional_equity) * daily["equity"]
    daily["surface_id"] = "phase59_shadow_research"
    daily["reference_only"] = False
    daily["variant_id"] = str(selected_variant["variant_id"])
    daily["turnover"] = math.nan
    daily["gross_exposure"] = math.nan
    daily["positions_count"] = math.nan
    daily["source_path"] = "research_data/catalog.duckdb::allocator_state"
    daily = daily.reset_index()

    summary = {
        "variant_id": str(selected_variant["variant_id"]),
        "selection_count": int(selected_variant["selection_count"]),
        "median_outer_test_sharpe": float(selected_variant["median_outer_test_sharpe"]),
        "mean_outer_test_sharpe": float(selected_variant["mean_outer_test_sharpe"]),
        "positive_outer_fold_share": float(selected_variant["positive_outer_fold_share"]),
        "selection_policy": str(selected_variant["selection_policy"]),
        "observed_rows": int(len(observed)),
        "calendar_rows": int(len(daily)),
        "observed_days": int(daily["is_observed_day"].sum()),
        "first_observed_date": observed["date"].min().date().isoformat(),
        "last_observed_date": observed["date"].max().date().isoformat(),
        "same_window_same_cost_same_engine": True,
        "same_engine_source": (
            "allocator_state_source_{i,t} = melt(phase17_3_parameter_sweep_return_streams)"
        ),
        "sharpe": float(safe_sharpe(daily["net_ret"])),
        "cagr": float(compute_cagr(daily["equity"])),
        "max_dd": float(compute_max_drawdown(daily["equity"])),
        "ulcer": float(compute_ulcer_index(daily["equity"])),
        "net_return_total": float(daily["equity"].iloc[-1] - 1.0),
        "turnover_annual": float("nan"),
        "turnover_metric_available": False,
    }
    return summary, daily


def _extract_shadow_positions(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "ticker" not in frame.columns or "target_weight" not in frame.columns:
        raise ValueError(f"Shadow positions file missing required columns: {path}")
    frame["ticker"] = frame["ticker"].astype(str).str.upper()
    frame["target_weight"] = pd.to_numeric(frame["target_weight"], errors="coerce").fillna(0.0)
    return frame


def _load_phase50_positions(cfg: ShadowPortfolioConfig) -> tuple[Path, pd.DataFrame, Path, pd.DataFrame]:
    candidates: list[tuple[int, Path]] = []
    for path in cfg.phase50_root.glob("paper_curve_positions_day*.csv"):
        match = _POSITIONS_RE.search(path.name)
        if match:
            candidates.append((int(match.group(1)), path))
    if not candidates:
        raise FileNotFoundError(f"No phase50 positions files found under {cfg.phase50_root}")

    candidates.sort(key=lambda item: item[0])
    first_path = candidates[0][1]
    last_path = candidates[-1][1]
    return first_path, _extract_shadow_positions(first_path), last_path, _extract_shadow_positions(last_path)


def _metric_level(metric_name: str, value: float) -> str:
    if metric_name == "holdings_overlap":
        if value < 0.10:
            return "RED"
        if value < 0.30:
            return "YELLOW"
        return "GREEN"
    if metric_name == "gross_exposure_delta":
        if value > 0.75:
            return "RED"
        if value > 0.25:
            return "YELLOW"
        return "GREEN"
    if metric_name == "turnover_delta_rel":
        if value > 0.50:
            return "RED"
        if value > 0.10:
            return "YELLOW"
        return "GREEN"
    raise ValueError(f"Unknown metric_name: {metric_name}")


def _build_shadow_reference_surface(
    cfg: ShadowPortfolioConfig,
) -> tuple[dict[str, Any], pd.DataFrame]:
    curve = pd.read_csv(cfg.phase50_curve_path)
    curve["date"] = pd.to_datetime(curve["date"], errors="coerce").dt.normalize()
    curve = curve.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    telemetry = json.loads(cfg.phase50_telemetry_path.read_text(encoding="utf-8"))
    gate = json.loads(cfg.phase50_gate_path.read_text(encoding="utf-8"))
    first_path, first_positions, last_path, last_positions = _load_phase50_positions(cfg)
    core_sample = pd.read_csv(cfg.phase54_sample_output_path)
    core_sample["selected"] = core_sample["selected"].astype(bool)
    core_selected_tickers = set(
        core_sample.loc[core_sample["selected"], "ticker"].astype(str).str.upper().tolist()
    )
    shadow_first_tickers = set(first_positions["ticker"].tolist())
    shadow_last_tickers = set(last_positions["ticker"].tolist())
    core_exposure = pd.read_csv(cfg.phase54_top20_exposure_path).sort_values("date").iloc[-1]
    shadow_gross_exposure = float(last_positions["target_weight"].abs().sum())
    holdings_overlap = float(
        len(shadow_last_tickers.intersection(core_selected_tickers))
        / max(1, len(shadow_last_tickers))
    )
    holdings_overlap_window = float(
        len(shadow_last_tickers.intersection(shadow_first_tickers))
        / max(1, len(shadow_last_tickers))
    )
    gross_exposure_delta = float(abs(float(core_exposure["gross_exposure"]) - shadow_gross_exposure))
    turnover_avg = float(telemetry["averages"]["turnover"])
    turnover_delta_abs = float(abs(telemetry["averages"]["turnover_delta_vs_c3"]))
    turnover_delta_rel = float(turnover_delta_abs / max(abs(turnover_avg), 1e-12))

    alert_rows = [
        {
            "metric_name": "holdings_overlap",
            "metric_value": holdings_overlap,
            "metric_level": _metric_level("holdings_overlap", holdings_overlap),
            "reason": "shadow latest basket vs locked C3 sample output",
        },
        {
            "metric_name": "gross_exposure_delta",
            "metric_value": gross_exposure_delta,
            "metric_level": _metric_level("gross_exposure_delta", gross_exposure_delta),
            "reason": "shadow latest gross exposure vs locked C3 top20 exposure latest row",
        },
        {
            "metric_name": "turnover_delta_rel",
            "metric_value": turnover_delta_rel,
            "metric_level": _metric_level("turnover_delta_rel", turnover_delta_rel),
            "reason": "shadow average turnover delta vs C3 from phase50 aggregated telemetry",
        },
    ]
    overall_alert_level = max(
        (row["metric_level"] for row in alert_rows),
        key=lambda level: _SEVERITY_RANK[level],
    )
    alert_reasons = [row["reason"] for row in alert_rows if row["metric_level"] != "GREEN"]

    curve["surface_id"] = "phase50_shadow_reference"
    curve["reference_only"] = True
    curve["variant_id"] = None
    curve["gross_exposure"] = shadow_gross_exposure
    curve["positions_count"] = int(last_positions["ticker"].nunique())
    curve["is_observed_day"] = True
    curve["source_path"] = str(cfg.phase50_curve_path)
    curve = curve.rename(columns={"equity": "equity", "notional_equity": "notional_equity"})

    summary = {
        "reference_only": True,
        "curve_rows": int(len(curve)),
        "curve_start_date": curve["date"].min().date().isoformat(),
        "curve_end_date": curve["date"].max().date().isoformat(),
        "curve_day_completed": int(telemetry["curve_day_completed"]),
        "curve_horizon_days": int(telemetry["curve_horizon_days"]),
        "cumulative_return_pct": float(telemetry["cumulative_return_pct"]),
        "latest_notional_equity": float(curve["notional_equity"].iloc[-1]),
        "average_turnover": turnover_avg,
        "average_slippage_bps": float(telemetry["averages"]["slippage_bps"]),
        "holdings_overlap": holdings_overlap,
        "holdings_overlap_window": holdings_overlap_window,
        "gross_exposure_shadow": shadow_gross_exposure,
        "gross_exposure_core_latest": float(core_exposure["gross_exposure"]),
        "gross_exposure_delta": gross_exposure_delta,
        "turnover_delta_abs": turnover_delta_abs,
        "turnover_delta_rel": turnover_delta_rel,
        "alert_level": overall_alert_level,
        "alert_reasons": alert_reasons,
        "alert_rows": alert_rows,
        "production_default_selector": str(gate.get("production_default_selector", "")),
        "baseline_evidence_mode": str(telemetry.get("baseline_evidence_mode", "")),
        "broker_calls_detected_total": int(telemetry.get("broker_calls_detected_total", 0)),
        "all_intents_simulated": bool(telemetry.get("all_intents_simulated", False)),
        "positions_first_path": str(first_path),
        "positions_latest_path": str(last_path),
        "phase54_core_sample_path": str(cfg.phase54_sample_output_path),
        "phase54_top20_exposure_path": str(cfg.phase54_top20_exposure_path),
        "phase50_gate_path": str(cfg.phase50_gate_path),
    }
    return summary, curve


def _build_research_delta_row(
    research_summary: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    c3 = baseline["baseline_metrics_c3"]
    return {
        "surface_id": "phase59_shadow_research",
        "reference_only": False,
        "variant_id": str(research_summary["variant_id"]),
        "window_start": None,
        "window_end": None,
        "cost_bps": float(baseline["baseline_cost_bps"]),
        "baseline_config_id": baseline["baseline_config_id"],
        "same_window_same_cost_same_engine": True,
        "sharpe_c3": float(c3["sharpe"]),
        "sharpe_surface": float(research_summary["sharpe"]),
        "sharpe_delta": float(research_summary["sharpe"] - c3["sharpe"]),
        "cagr_c3": float(c3["cagr"]),
        "cagr_surface": float(research_summary["cagr"]),
        "cagr_delta": float(research_summary["cagr"] - c3["cagr"]),
        "max_dd_c3": float(c3["max_dd"]),
        "max_dd_surface": float(research_summary["max_dd"]),
        "max_dd_delta": float(research_summary["max_dd"] - c3["max_dd"]),
        "ulcer_c3": float(c3["ulcer"]),
        "ulcer_surface": float(research_summary["ulcer"]),
        "ulcer_delta": float(research_summary["ulcer"] - c3["ulcer"]),
        "turnover_annual_c3": float(c3["turnover_annual"]),
        "turnover_annual_surface": float("nan"),
        "turnover_metric_available": False,
        "holdings_overlap": float("nan"),
        "gross_exposure_delta": float("nan"),
        "turnover_delta_abs": float("nan"),
        "turnover_delta_rel": float("nan"),
        "alert_level": "",
        "alert_reasons": "",
    }


def _build_reference_delta_row(
    reference_summary: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    return {
        "surface_id": "phase50_shadow_reference_alerts",
        "reference_only": True,
        "variant_id": "",
        "window_start": reference_summary["curve_start_date"],
        "window_end": reference_summary["curve_end_date"],
        "cost_bps": float("nan"),
        "baseline_config_id": baseline["baseline_config_id"],
        "same_window_same_cost_same_engine": False,
        "sharpe_c3": float("nan"),
        "sharpe_surface": float("nan"),
        "sharpe_delta": float("nan"),
        "cagr_c3": float("nan"),
        "cagr_surface": float("nan"),
        "cagr_delta": float("nan"),
        "max_dd_c3": float("nan"),
        "max_dd_surface": float("nan"),
        "max_dd_delta": float("nan"),
        "ulcer_c3": float("nan"),
        "ulcer_surface": float("nan"),
        "ulcer_delta": float("nan"),
        "turnover_annual_c3": float(baseline["baseline_metrics_c3"]["turnover_annual"]),
        "turnover_annual_surface": float("nan"),
        "turnover_metric_available": True,
        "holdings_overlap": float(reference_summary["holdings_overlap"]),
        "gross_exposure_delta": float(reference_summary["gross_exposure_delta"]),
        "turnover_delta_abs": float(reference_summary["turnover_delta_abs"]),
        "turnover_delta_rel": float(reference_summary["turnover_delta_rel"]),
        "alert_level": str(reference_summary["alert_level"]),
        "alert_reasons": " | ".join(reference_summary["alert_reasons"]),
    }


def build_phase59_packet(
    cfg: ShadowPortfolioConfig,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    validate_config(cfg)
    baseline = load_baseline_summary(cfg)
    selected_variant = select_phase55_variant(cfg)
    catalog_meta = _fetch_catalog_meta()
    research_summary, research_evidence = _build_research_surface(cfg, selected_variant)
    reference_summary, reference_evidence = _build_shadow_reference_surface(cfg)

    delta_frame = pd.DataFrame(
        [
            _build_research_delta_row(research_summary, baseline),
            _build_reference_delta_row(reference_summary, baseline),
        ]
    )
    review_hold_reasons: list[str] = []
    research_delta = delta_frame.loc[delta_frame["surface_id"] == "phase59_shadow_research"].iloc[0]
    if float(research_delta["sharpe_delta"]) < 0.0:
        review_hold_reasons.append("phase59_shadow_research_sharpe_delta < 0")
    if float(research_delta["cagr_delta"]) < 0.0:
        review_hold_reasons.append("phase59_shadow_research_cagr_delta < 0")
    if str(reference_summary["alert_level"]).upper() != "GREEN":
        review_hold_reasons.append(
            f"phase50_shadow_reference_alert_level = {reference_summary['alert_level']}"
        )

    evidence_frame = pd.concat(
        [
            research_evidence[
                [
                    "date",
                    "surface_id",
                    "reference_only",
                    "variant_id",
                    "net_ret",
                    "equity",
                    "notional_equity",
                    "turnover",
                    "gross_exposure",
                    "positions_count",
                    "is_observed_day",
                    "source_path",
                ]
            ],
            reference_evidence[
                [
                    "date",
                    "surface_id",
                    "reference_only",
                    "variant_id",
                    "net_ret",
                    "equity",
                    "notional_equity",
                    "turnover",
                    "gross_exposure",
                    "positions_count",
                    "is_observed_day",
                    "source_path",
                ]
            ],
        ],
        ignore_index=True,
    ).sort_values(["surface_id", "date"]).reset_index(drop=True)

    summary = {
        "packet_id": SHADOW_PACKET_ID,
        "strategy_id": SHADOW_PACKET_ID,
        "start_date": cfg.start_date.date().isoformat(),
        "end_date": cfg.end_date.date().isoformat(),
        "max_date": cfg.max_date.date().isoformat(),
        "cost_bps": float(cfg.cost_bps),
        "baseline_config_id": baseline["baseline_config_id"],
        "same_window_same_cost_same_engine": True,
        "summary_path": str(cfg.summary_path),
        "evidence_path": str(cfg.evidence_path),
        "delta_path": str(cfg.delta_path),
        "catalog_rows": int(catalog_meta["rows"]),
        "catalog_distinct_variants": int(catalog_meta["distinct_variants"]),
        "catalog_min_snapshot_date": str(catalog_meta["min_snapshot_date"]),
        "catalog_max_snapshot_date": str(catalog_meta["max_snapshot_date"]),
        "selected_variant": research_summary,
        "shadow_reference": reference_summary,
        "review_hold": bool(review_hold_reasons),
        "review_hold_reasons": review_hold_reasons,
        "source_paths": {
            "baseline_summary_path": str(cfg.baseline_summary_path),
            "phase55_evidence_path": str(cfg.phase55_evidence_path),
            "phase50_curve_path": str(cfg.phase50_curve_path),
            "phase50_telemetry_path": str(cfg.phase50_telemetry_path),
            "phase50_gate_path": str(cfg.phase50_gate_path),
            "phase54_top20_exposure_path": str(cfg.phase54_top20_exposure_path),
            "phase54_sample_output_path": str(cfg.phase54_sample_output_path),
            "research_catalog_path": str(PROJECT_ROOT / "research_data" / "catalog.duckdb"),
            "research_connector_path": str(PROJECT_ROOT / "data" / "research_connector.py"),
        },
    }
    return summary, evidence_frame, delta_frame


def load_shadow_monitor_artifacts(
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    evidence_path: Path = DEFAULT_EVIDENCE_PATH,
    delta_path: Path = DEFAULT_DELTA_PATH,
) -> tuple[dict[str, Any] | None, pd.DataFrame, pd.DataFrame]:
    summary: dict[str, Any] | None = None
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

    evidence = pd.read_csv(evidence_path) if evidence_path.exists() else pd.DataFrame()
    delta = pd.read_csv(delta_path) if delta_path.exists() else pd.DataFrame()
    if not evidence.empty and "date" in evidence.columns:
        evidence["date"] = pd.to_datetime(evidence["date"], errors="coerce")
    return summary, evidence, delta
