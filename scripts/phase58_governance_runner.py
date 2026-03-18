from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.day5_ablation_report import _atomic_csv_write  # noqa: E402
from scripts.day5_ablation_report import _atomic_json_write  # noqa: E402
from scripts.phase56_pead_runner import PeadConfig  # noqa: E402
from scripts.phase56_pead_runner import RESEARCH_MAX_DATE  # noqa: E402
from scripts.phase56_pead_runner import run_pead  # noqa: E402
from scripts.phase57_corporate_actions_runner import CorporateActionsConfig  # noqa: E402
from scripts.phase57_corporate_actions_runner import run_corporate_actions  # noqa: E402
from utils.spa import spa_wrc_pvalues  # noqa: E402
from utils.statistics import deflated_sharpe_ratio  # noqa: E402
from utils.statistics import effective_number_of_trials  # noqa: E402
from utils.statistics import safe_sharpe  # noqa: E402


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_BASELINE_SUMMARY_PATH = PROCESSED_DIR / "phase54_core_sleeve_summary.json"
DEFAULT_PHASE55_SUMMARY_PATH = PROCESSED_DIR / "phase55_allocator_cpcv_summary.json"
DEFAULT_SUMMARY_PATH = PROCESSED_DIR / "phase58_governance_summary.json"
DEFAULT_EVIDENCE_PATH = PROCESSED_DIR / "phase58_governance_evidence.csv"
DEFAULT_DELTA_PATH = PROCESSED_DIR / "phase58_governance_delta_vs_c3.csv"


@dataclass(frozen=True)
class GovernanceConfig:
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    max_date: pd.Timestamp
    cost_bps: float
    summary_path: Path
    evidence_path: Path
    delta_path: Path
    baseline_summary_path: Path = DEFAULT_BASELINE_SUMMARY_PATH
    phase55_summary_path: Path = DEFAULT_PHASE55_SUMMARY_PATH
    adv_window_days: int = 20
    adv_usd_min: float = 5_000_000.0
    max_days_since_earnings: int = 63
    value_rank_threshold: float = 0.60
    event_yield_min: float = 0.005
    event_yield_max: float = 0.25


def validate_config(cfg: GovernanceConfig) -> None:
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


def load_baseline_summary(cfg: GovernanceConfig) -> dict[str, Any]:
    if not cfg.baseline_summary_path.exists():
        raise FileNotFoundError(f"Missing required baseline summary: {cfg.baseline_summary_path}")

    with open(cfg.baseline_summary_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

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


def load_phase55_reference(cfg: GovernanceConfig) -> dict[str, Any]:
    if not cfg.phase55_summary_path.exists():
        raise FileNotFoundError(f"Missing required Phase 55 summary: {cfg.phase55_summary_path}")
    with open(cfg.phase55_summary_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return {
        "reference_only": True,
        "allocator_gate_pass": bool(payload.get("allocator_gate_pass", False)),
        "pbo": float(payload.get("pbo", float("nan"))),
        "dsr": float(payload.get("dsr", float("nan"))),
        "spa_p": float(payload.get("spa_p", float("nan"))),
        "wrc_p": float(payload.get("wrc_p", float("nan"))),
        "positive_outer_fold_share": float(payload.get("positive_outer_fold_share", float("nan"))),
        "max_date": str(payload.get("max_date", "")),
        "source_summary_path": str(cfg.phase55_summary_path),
    }


def load_evidence_returns(evidence_path: Path, column_name: str) -> pd.DataFrame:
    frame = pd.read_csv(evidence_path)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame[column_name] = pd.to_numeric(frame["net_ret"], errors="coerce").fillna(0.0)
    frame = frame.dropna(subset=["date"])[["date", column_name]].copy()
    return frame.sort_values("date").reset_index(drop=True)


def build_event_return_matrix(pead_evidence_path: Path, corp_evidence_path: Path) -> pd.DataFrame:
    pead = load_evidence_returns(pead_evidence_path, "phase56_pead")
    corp = load_evidence_returns(corp_evidence_path, "phase57_corporate_actions")
    merged = pead.merge(corp, on="date", how="outer").sort_values("date").fillna(0.0)
    return merged.set_index("date")


def build_delta_row(
    *,
    sleeve_id: str,
    strategy_id: str,
    summary: dict[str, Any],
    baseline: dict[str, Any],
    dsr: float,
    family_spa_p: float,
    family_wrc_p: float,
) -> dict[str, Any]:
    c3 = baseline["baseline_metrics_c3"]
    turnover_ratio = (
        float(summary["turnover_annual"]) / float(c3["turnover_annual"])
        if abs(float(c3["turnover_annual"])) > 1e-12
        else 0.0
    )
    return {
        "sleeve_id": sleeve_id,
        "strategy_id": strategy_id,
        "window_start": str(summary["start_date"]),
        "window_end": str(summary["end_date"]),
        "cost_bps": float(summary["cost_bps"]),
        "baseline_config_id": baseline["baseline_config_id"],
        "same_window_same_cost_same_engine": True,
        "sharpe_c3": float(c3["sharpe"]),
        "sharpe_sleeve": float(summary["sharpe"]),
        "sharpe_delta": float(summary["sharpe"] - c3["sharpe"]),
        "cagr_c3": float(c3["cagr"]),
        "cagr_sleeve": float(summary["cagr"]),
        "cagr_delta": float(summary["cagr"] - c3["cagr"]),
        "turnover_annual_c3": float(c3["turnover_annual"]),
        "turnover_annual_sleeve": float(summary["turnover_annual"]),
        "turnover_ratio_sleeve_vs_c3": float(turnover_ratio),
        "max_dd_c3": float(c3["max_dd"]),
        "max_dd_sleeve": float(summary["max_dd"]),
        "max_dd_delta": float(summary["max_dd"] - c3["max_dd"]),
        "ulcer_c3": float(c3["ulcer"]),
        "ulcer_sleeve": float(summary["ulcer"]),
        "ulcer_delta": float(summary["ulcer"] - c3["ulcer"]),
        "net_return_total_sleeve": float(summary["net_return_total"]),
        "dsr": float(dsr),
        "family_spa_p": float(family_spa_p),
        "family_wrc_p": float(family_wrc_p),
        "pbo": float("nan"),
        "pbo_applicable": False,
    }


def build_review_hold_reasons(delta_frame: pd.DataFrame, family_spa_p: float, family_wrc_p: float) -> list[str]:
    reasons: list[str] = []
    if not pd.isna(family_spa_p) and family_spa_p >= 0.05:
        reasons.append("event_family_spa_p >= 0.05")
    if not pd.isna(family_wrc_p) and family_wrc_p >= 0.05:
        reasons.append("event_family_wrc_p >= 0.05")
    for _, row in delta_frame.iterrows():
        sleeve_id = str(row["sleeve_id"])
        if float(row["sharpe_delta"]) < 0.0:
            reasons.append(f"{sleeve_id}_sharpe_delta < 0")
        if float(row["cagr_delta"]) < 0.0:
            reasons.append(f"{sleeve_id}_cagr_delta < 0")
    return reasons


def build_evidence_frame(
    pead_summary: dict[str, Any],
    corp_summary: dict[str, Any],
    delta_frame: pd.DataFrame,
    phase55_reference: dict[str, Any],
) -> pd.DataFrame:
    delta_map = {str(row["sleeve_id"]): row for _, row in delta_frame.iterrows()}
    records = [
        {
            "sleeve_id": "phase56_event_pead",
            "strategy_id": str(pead_summary["strategy_id"]),
            "source_family": "event_sleeve",
            "start_date": str(pead_summary["start_date"]),
            "end_date": str(pead_summary["end_date"]),
            "max_date": str(pead_summary["max_date"]),
            "cost_bps": float(pead_summary["cost_bps"]),
            "same_engine": bool(pead_summary["same_engine"]),
            "same_window_same_cost_same_engine": True,
            "candidate_rows": int(pead_summary["candidate_rows"]),
            "candidate_dates": int(pead_summary["candidate_dates"]),
            "sharpe": float(pead_summary["sharpe"]),
            "cagr": float(pead_summary["cagr"]),
            "max_dd": float(pead_summary["max_dd"]),
            "ulcer": float(pead_summary["ulcer"]),
            "turnover_annual": float(pead_summary["turnover_annual"]),
            "net_return_total": float(pead_summary["net_return_total"]),
            "dsr": float(delta_map["phase56_event_pead"]["dsr"]),
            "family_spa_p": float(delta_map["phase56_event_pead"]["family_spa_p"]),
            "family_wrc_p": float(delta_map["phase56_event_pead"]["family_wrc_p"]),
            "pbo": float("nan"),
            "pbo_applicable": False,
        },
        {
            "sleeve_id": "phase57_event_corporate_actions",
            "strategy_id": str(corp_summary["strategy_id"]),
            "source_family": "event_sleeve",
            "start_date": str(corp_summary["start_date"]),
            "end_date": str(corp_summary["end_date"]),
            "max_date": str(corp_summary["max_date"]),
            "cost_bps": float(corp_summary["cost_bps"]),
            "same_engine": bool(corp_summary["same_engine"]),
            "same_window_same_cost_same_engine": True,
            "candidate_rows": int(corp_summary["candidate_rows"]),
            "candidate_dates": int(corp_summary["candidate_dates"]),
            "sharpe": float(corp_summary["sharpe"]),
            "cagr": float(corp_summary["cagr"]),
            "max_dd": float(corp_summary["max_dd"]),
            "ulcer": float(corp_summary["ulcer"]),
            "turnover_annual": float(corp_summary["turnover_annual"]),
            "net_return_total": float(corp_summary["net_return_total"]),
            "dsr": float(delta_map["phase57_event_corporate_actions"]["dsr"]),
            "family_spa_p": float(delta_map["phase57_event_corporate_actions"]["family_spa_p"]),
            "family_wrc_p": float(delta_map["phase57_event_corporate_actions"]["family_wrc_p"]),
            "pbo": float("nan"),
            "pbo_applicable": False,
        },
        {
            "sleeve_id": "phase55_allocator_reference",
            "strategy_id": "PHASE55_ALLOCATOR_GOVERNANCE_REFERENCE",
            "source_family": "allocator_reference",
            "start_date": "",
            "end_date": "",
            "max_date": str(phase55_reference["max_date"]),
            "cost_bps": float("nan"),
            "same_engine": False,
            "same_window_same_cost_same_engine": False,
            "candidate_rows": 0,
            "candidate_dates": 0,
            "sharpe": float("nan"),
            "cagr": float("nan"),
            "max_dd": float("nan"),
            "ulcer": float("nan"),
            "turnover_annual": float("nan"),
            "net_return_total": float("nan"),
            "dsr": float(phase55_reference["dsr"]),
            "family_spa_p": float(phase55_reference["spa_p"]),
            "family_wrc_p": float(phase55_reference["wrc_p"]),
            "pbo": float(phase55_reference["pbo"]),
            "pbo_applicable": True,
        },
    ]
    return pd.DataFrame(records)


def run_governance_packet(cfg: GovernanceConfig) -> dict[str, Any]:
    validate_config(cfg)
    baseline = load_baseline_summary(cfg)
    phase55_reference = load_phase55_reference(cfg)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        pead_summary = run_pead(
            PeadConfig(
                start_date=cfg.start_date,
                end_date=cfg.end_date,
                max_date=cfg.max_date,
                cost_bps=float(cfg.cost_bps),
                adv_window_days=int(cfg.adv_window_days),
                adv_usd_min=float(cfg.adv_usd_min),
                max_days_since_earnings=int(cfg.max_days_since_earnings),
                value_rank_threshold=float(cfg.value_rank_threshold),
                summary_path=tmp / "phase56_summary.json",
                evidence_path=tmp / "phase56_evidence.csv",
            )
        )
        corp_summary = run_corporate_actions(
            CorporateActionsConfig(
                start_date=cfg.start_date,
                end_date=cfg.end_date,
                max_date=cfg.max_date,
                cost_bps=float(cfg.cost_bps),
                adv_window_days=int(cfg.adv_window_days),
                adv_usd_min=float(cfg.adv_usd_min),
                event_yield_min=float(cfg.event_yield_min),
                event_yield_max=float(cfg.event_yield_max),
                value_rank_threshold=float(cfg.value_rank_threshold),
                summary_path=tmp / "phase57_summary.json",
                evidence_path=tmp / "phase57_evidence.csv",
                delta_path=tmp / "phase57_delta.csv",
                baseline_summary_path=cfg.baseline_summary_path,
            )
        )

        event_matrix = build_event_return_matrix(
            pead_evidence_path=tmp / "phase56_evidence.csv",
            corp_evidence_path=tmp / "phase57_evidence.csv",
        )
        event_n_trials_eff = float(effective_number_of_trials(event_matrix))
        sr_estimates = event_matrix.apply(lambda col: safe_sharpe(col)).astype(float)
        family_spa_wrc = spa_wrc_pvalues(event_matrix)
        family_spa_p = float(family_spa_wrc["spa_p"])
        family_wrc_p = float(family_spa_wrc["wrc_p"])

        pead_dsr = float(
            deflated_sharpe_ratio(
                returns=event_matrix["phase56_pead"],
                sr_estimates=sr_estimates,
                n_trials_eff=event_n_trials_eff,
            )["dsr"]
        )
        corp_dsr = float(
            deflated_sharpe_ratio(
                returns=event_matrix["phase57_corporate_actions"],
                sr_estimates=sr_estimates,
                n_trials_eff=event_n_trials_eff,
            )["dsr"]
        )

        delta_rows = [
            build_delta_row(
                sleeve_id="phase56_event_pead",
                strategy_id=str(pead_summary["strategy_id"]),
                summary=pead_summary,
                baseline=baseline,
                dsr=pead_dsr,
                family_spa_p=family_spa_p,
                family_wrc_p=family_wrc_p,
            ),
            build_delta_row(
                sleeve_id="phase57_event_corporate_actions",
                strategy_id=str(corp_summary["strategy_id"]),
                summary=corp_summary,
                baseline=baseline,
                dsr=corp_dsr,
                family_spa_p=family_spa_p,
                family_wrc_p=family_wrc_p,
            ),
        ]
        delta_frame = pd.DataFrame(delta_rows)
        evidence_frame = build_evidence_frame(
            pead_summary=pead_summary,
            corp_summary=corp_summary,
            delta_frame=delta_frame,
            phase55_reference=phase55_reference,
        )

    review_hold_reasons = build_review_hold_reasons(
        delta_frame=delta_frame,
        family_spa_p=family_spa_p,
        family_wrc_p=family_wrc_p,
    )

    summary = {
        "packet_id": "PHASE58_GOVERNANCE_EVENT_LAYER_V1",
        "start_date": cfg.start_date.strftime("%Y-%m-%d"),
        "end_date": cfg.end_date.strftime("%Y-%m-%d"),
        "max_date": cfg.max_date.strftime("%Y-%m-%d"),
        "cost_bps": float(cfg.cost_bps),
        "same_window_same_cost_same_engine": True,
        "family_scope": ["phase56_event_pead", "phase57_event_corporate_actions"],
        "sleeve_count": 2,
        "event_family_effective_n_trials": event_n_trials_eff,
        "event_family_spa_p": family_spa_p,
        "event_family_wrc_p": family_wrc_p,
        "pbo_applicable_event_family": False,
        "pbo_reason": "single-packet event sleeves do not expose a CSCV search lattice in this bounded packet",
        "review_hold": True,
        "review_hold_reasons": review_hold_reasons,
        "allocator_reference": phase55_reference,
        "phase56_event_pead": {
            "strategy_id": pead_summary["strategy_id"],
            "rows": int(pead_summary["rows"]),
            "candidate_rows": int(pead_summary["candidate_rows"]),
            "candidate_dates": int(pead_summary["candidate_dates"]),
            "sharpe": float(pead_summary["sharpe"]),
            "cagr": float(pead_summary["cagr"]),
            "max_dd": float(pead_summary["max_dd"]),
            "ulcer": float(pead_summary["ulcer"]),
            "turnover_annual": float(pead_summary["turnover_annual"]),
            "dsr": pead_dsr,
        },
        "phase57_event_corporate_actions": {
            "strategy_id": corp_summary["strategy_id"],
            "rows": int(corp_summary["rows"]),
            "candidate_rows": int(corp_summary["candidate_rows"]),
            "candidate_dates": int(corp_summary["candidate_dates"]),
            "sharpe": float(corp_summary["sharpe"]),
            "cagr": float(corp_summary["cagr"]),
            "max_dd": float(corp_summary["max_dd"]),
            "ulcer": float(corp_summary["ulcer"]),
            "turnover_annual": float(corp_summary["turnover_annual"]),
            "dsr": corp_dsr,
        },
        "baseline_config_id": baseline["baseline_config_id"],
        "baseline_metrics_c3": baseline["baseline_metrics_c3"],
        "source_paths": {
            "baseline_summary_path": str(cfg.baseline_summary_path),
            "phase55_summary_path": str(cfg.phase55_summary_path),
            "phase56_runner_path": str(PROJECT_ROOT / "scripts" / "phase56_pead_runner.py"),
            "phase57_runner_path": str(PROJECT_ROOT / "scripts" / "phase57_corporate_actions_runner.py"),
            "statistics_path": str(PROJECT_ROOT / "utils" / "statistics.py"),
            "spa_path": str(PROJECT_ROOT / "utils" / "spa.py"),
            "engine_path": str(PROJECT_ROOT / "core" / "engine.py"),
        },
        "summary_path": str(cfg.summary_path),
        "evidence_path": str(cfg.evidence_path),
        "delta_path": str(cfg.delta_path),
    }

    cfg.summary_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_write(summary, cfg.summary_path)
    _atomic_csv_write(evidence_frame, cfg.evidence_path)
    _atomic_csv_write(delta_frame, cfg.delta_path)
    return summary


def parse_args() -> GovernanceConfig:
    parser = argparse.ArgumentParser(description="Phase 58 bounded governance runner.")
    parser.add_argument("--start-date", default="2015-01-01")
    parser.add_argument("--end-date", default="2022-12-31")
    parser.add_argument("--max-date", default="2022-12-31")
    parser.add_argument("--cost-bps", type=float, default=5.0)
    parser.add_argument("--summary-path", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--evidence-path", default=str(DEFAULT_EVIDENCE_PATH))
    parser.add_argument("--delta-path", default=str(DEFAULT_DELTA_PATH))
    parser.add_argument("--baseline-summary-path", default=str(DEFAULT_BASELINE_SUMMARY_PATH))
    parser.add_argument("--phase55-summary-path", default=str(DEFAULT_PHASE55_SUMMARY_PATH))
    args = parser.parse_args()
    return GovernanceConfig(
        start_date=pd.Timestamp(args.start_date),
        end_date=pd.Timestamp(args.end_date),
        max_date=pd.Timestamp(args.max_date),
        cost_bps=float(args.cost_bps),
        summary_path=Path(args.summary_path),
        evidence_path=Path(args.evidence_path),
        delta_path=Path(args.delta_path),
        baseline_summary_path=Path(args.baseline_summary_path),
        phase55_summary_path=Path(args.phase55_summary_path),
    )


def main() -> None:
    cfg = parse_args()
    summary = run_governance_packet(cfg)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
