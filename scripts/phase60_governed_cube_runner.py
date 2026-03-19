from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.day5_ablation_report import _atomic_csv_write  # noqa: E402
from scripts.day5_ablation_report import _atomic_json_write  # noqa: E402
from scripts.phase56_pead_runner import PeadConfig  # noqa: E402
from scripts.phase56_pead_runner import build_pead_target_weights  # noqa: E402
from scripts.phase56_pead_runner import load_pead_feature_frame  # noqa: E402
from scripts.phase56_pead_runner import select_pead_candidates  # noqa: E402
from scripts.phase57_corporate_actions_runner import CorporateActionsConfig  # noqa: E402
from scripts.phase57_corporate_actions_runner import build_corporate_action_target_weights  # noqa: E402
from scripts.phase57_corporate_actions_runner import load_corporate_action_frame  # noqa: E402
from scripts.phase57_corporate_actions_runner import load_trading_dates  # noqa: E402
from scripts.phase57_corporate_actions_runner import select_corporate_action_candidates  # noqa: E402


RESEARCH_MAX_DATE = pd.Timestamp("2022-12-31")
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
BOOK_ID = "PHASE60_GOVERNED_BOOK_V1"
PACKET_ID = "PHASE60_GOVERNED_CUBE_V1"
SLEEVE_PHASE56 = "phase56_event_pead"
SLEEVE_PHASE57 = "phase57_event_corporate_actions"

DEFAULT_CUBE_PATH = PROCESSED_DIR / "phase60_governed_cube.csv"
DEFAULT_DAILY_PATH = PROCESSED_DIR / "phase60_governed_cube_daily.csv"
DEFAULT_SUMMARY_PATH = PROCESSED_DIR / "phase60_governed_cube_summary.json"
DEFAULT_PHASE55_SUMMARY_PATH = PROCESSED_DIR / "phase55_allocator_cpcv_summary.json"
DEFAULT_PHASE59_SUMMARY_PATH = PROCESSED_DIR / "phase59_shadow_summary.json"
DEFAULT_PHASE54_SUMMARY_PATH = PROCESSED_DIR / "phase54_core_sleeve_summary.json"
DEFAULT_PHASE56_SUMMARY_PATH = PROCESSED_DIR / "phase56_pead_summary.json"
DEFAULT_PHASE57_SUMMARY_PATH = PROCESSED_DIR / "phase57_corporate_actions_summary.json"


@dataclass(frozen=True)
class GovernedCubeConfig:
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    max_date: pd.Timestamp
    cost_bps: float
    cube_path: Path = DEFAULT_CUBE_PATH
    daily_path: Path = DEFAULT_DAILY_PATH
    summary_path: Path = DEFAULT_SUMMARY_PATH
    phase55_summary_path: Path = DEFAULT_PHASE55_SUMMARY_PATH
    phase59_summary_path: Path = DEFAULT_PHASE59_SUMMARY_PATH
    phase54_summary_path: Path = DEFAULT_PHASE54_SUMMARY_PATH
    phase56_summary_path: Path = DEFAULT_PHASE56_SUMMARY_PATH
    phase57_summary_path: Path = DEFAULT_PHASE57_SUMMARY_PATH


def validate_config(cfg: GovernedCubeConfig) -> None:
    if cfg.max_date > RESEARCH_MAX_DATE:
        raise ValueError(f"max_date must be <= {RESEARCH_MAX_DATE.date()}, got {cfg.max_date.date()}")
    if cfg.end_date > cfg.max_date:
        raise ValueError("end_date must be <= max_date")
    if cfg.start_date > cfg.end_date:
        raise ValueError("start_date must be <= end_date")
    if abs(float(cfg.cost_bps) - 5.0) > 1e-9:
        raise ValueError("Phase 60 governed cube is locked to a 5.0 bps gating cost basis")


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_locked_summary(
    summary_path: Path,
    *,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    max_date: pd.Timestamp,
    cost_bps: float,
    require_exact_start: bool = True,
) -> dict[str, Any]:
    payload = _load_json(summary_path)
    if require_exact_start and "start_date" in payload and pd.Timestamp(payload["start_date"]) != start_date:
        raise ValueError(f"{summary_path} start_date mismatch")
    if "end_date" in payload and pd.Timestamp(payload["end_date"]) != end_date:
        raise ValueError(f"{summary_path} end_date mismatch")
    if "max_date" in payload and pd.Timestamp(payload["max_date"]) != max_date:
        raise ValueError(f"{summary_path} max_date mismatch")
    if "cost_bps" in payload and abs(float(payload["cost_bps"]) - float(cost_bps)) > 1e-9:
        raise ValueError(f"{summary_path} cost_bps mismatch")
    return payload


def _normalize_weights(weights: pd.DataFrame, calendar: pd.DatetimeIndex, permnos: list[int]) -> pd.DataFrame:
    if weights.empty:
        out = pd.DataFrame(0.0, index=calendar, columns=permnos)
        out.index.name = "date"
        out.columns.name = "permno"
        return out
    out = weights.copy()
    out.index = pd.to_datetime(out.index, errors="coerce")
    out = out.reindex(index=calendar, columns=permnos, fill_value=0.0)
    out = out.fillna(0.0).astype(float)
    out.index.name = "date"
    out.columns.name = "permno"
    return out


def _selected_metadata(selected: pd.DataFrame, *, sleeve_id: str, source_artifact: str) -> pd.DataFrame:
    out = selected[["date", "permno", "ticker"]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["permno"] = pd.to_numeric(out["permno"], errors="coerce")
    out["ticker"] = out["ticker"].astype(str).str.upper().str.strip()
    out = out.dropna(subset=["date", "permno"]).drop_duplicates(subset=["date", "permno"])
    out["permno"] = out["permno"].astype(int)
    out["sleeve_id"] = sleeve_id
    out["source_artifact"] = source_artifact
    return out


def _phase56_surface(cfg: GovernedCubeConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    run_cfg = PeadConfig(
        start_date=cfg.start_date,
        end_date=cfg.end_date,
        max_date=cfg.max_date,
        cost_bps=cfg.cost_bps,
        adv_window_days=20,
        adv_usd_min=5_000_000.0,
        max_days_since_earnings=63,
        value_rank_threshold=0.60,
        summary_path=PROCESSED_DIR / "_phase60_tmp_phase56_summary.json",
        evidence_path=PROCESSED_DIR / "_phase60_tmp_phase56_evidence.csv",
    )
    frame = load_pead_feature_frame(run_cfg)
    selected = select_pead_candidates(frame, run_cfg)
    weights = build_pead_target_weights(selected)
    meta = _selected_metadata(
        selected,
        sleeve_id=SLEEVE_PHASE56,
        source_artifact=str(cfg.phase56_summary_path),
    )
    return weights, meta


def _phase57_surface(cfg: GovernedCubeConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DatetimeIndex]:
    run_cfg = CorporateActionsConfig(
        start_date=cfg.start_date,
        end_date=cfg.end_date,
        max_date=cfg.max_date,
        cost_bps=cfg.cost_bps,
        adv_window_days=20,
        adv_usd_min=5_000_000.0,
        event_yield_min=0.005,
        event_yield_max=0.25,
        value_rank_threshold=0.60,
        summary_path=PROCESSED_DIR / "_phase60_tmp_phase57_summary.json",
        evidence_path=PROCESSED_DIR / "_phase60_tmp_phase57_evidence.csv",
        delta_path=PROCESSED_DIR / "_phase60_tmp_phase57_delta.csv",
        baseline_summary_path=cfg.phase54_summary_path,
    )
    trading_dates = load_trading_dates(run_cfg)
    frame = load_corporate_action_frame(run_cfg)
    selected = select_corporate_action_candidates(frame, run_cfg)
    weights = build_corporate_action_target_weights(selected, trading_dates)
    meta = _selected_metadata(
        selected,
        sleeve_id=SLEEVE_PHASE57,
        source_artifact=str(cfg.phase57_summary_path),
    )
    return weights, meta, trading_dates


def _forward_fill_metadata(meta: pd.DataFrame, calendar: pd.DatetimeIndex, permnos: list[int]) -> pd.DataFrame:
    grouped = (
        meta.groupby(["date", "permno"], as_index=True)
        .agg(
            ticker=("ticker", "first"),
            sleeve_id=("sleeve_id", lambda s: "|".join(sorted(set(map(str, s))))),
            source_artifact=("source_artifact", lambda s: "|".join(sorted(set(map(str, s))))),
        )
    )
    full_index = pd.MultiIndex.from_product([calendar, permnos], names=["date", "permno"])
    dense = grouped.reindex(full_index)
    dense[["ticker", "sleeve_id", "source_artifact"]] = dense.groupby(level="permno")[
        ["ticker", "sleeve_id", "source_artifact"]
    ].ffill()
    return dense


def _build_cube_rows(
    *,
    calendar: pd.DatetimeIndex,
    pead_weights: pd.DataFrame,
    corp_weights: pd.DataFrame,
    meta: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    permnos = sorted(set(map(int, pead_weights.columns.tolist() + corp_weights.columns.tolist())))
    pead_full = _normalize_weights(pead_weights, calendar, permnos)
    corp_full = _normalize_weights(corp_weights, calendar, permnos)

    book_pre = pead_full.add(corp_full, fill_value=0.0)
    book_final = book_pre.copy()
    allocator_overlay = book_final * 0.0
    gross_exposure = book_final.abs().sum(axis=1)
    turnover = book_final.diff().abs()
    if not turnover.empty:
        turnover.iloc[0] = book_final.iloc[0].abs()
    turnover = turnover.fillna(0.0)

    keep_mask = (book_final.abs() > 0.0) | (turnover > 0.0)
    final_long = book_final.where(keep_mask).stack().rename("book_weight_final")
    pre_long = book_pre.where(keep_mask).stack().rename("sleeve_weight_pre_allocator")
    overlay_long = allocator_overlay.where(keep_mask).stack().rename("allocator_overlay_weight")
    turn_long = turnover.where(keep_mask).stack().rename("turnover_component")

    dense_meta = _forward_fill_metadata(meta, calendar, permnos)
    cube = pd.concat([pre_long, overlay_long, final_long, turn_long], axis=1).reset_index()
    cube = cube.merge(
        dense_meta.reset_index(),
        on=["date", "permno"],
        how="left",
        validate="many_to_one",
    )
    cube["book_id"] = BOOK_ID
    cube["eligibility_state"] = np.where(
        cube["book_weight_final"].abs() > 0.0,
        "governed_active__allocator_blocked",
        "turnover_exit__allocator_blocked",
    )
    cube["gross_exposure"] = cube["date"].map(gross_exposure.to_dict()).astype(float)
    cube = cube[
        [
            "date",
            "book_id",
            "sleeve_id",
            "permno",
            "ticker",
            "eligibility_state",
            "sleeve_weight_pre_allocator",
            "allocator_overlay_weight",
            "book_weight_final",
            "gross_exposure",
            "turnover_component",
            "source_artifact",
        ]
    ].sort_values(["date", "permno", "sleeve_id"], kind="stable")

    daily = pd.DataFrame(
        {
            "date": calendar,
            "book_id": BOOK_ID,
            "gross_exposure": gross_exposure.values,
            "turnover_total": turnover.sum(axis=1).values,
            "n_active_permnos": (book_final.abs() > 0.0).sum(axis=1).astype(int).values,
            "allocator_overlay_applied": False,
        }
    )
    return cube.reset_index(drop=True), daily.reset_index(drop=True)


def build_governed_cube(cfg: GovernedCubeConfig) -> dict[str, Any]:
    validate_config(cfg)
    phase56_summary = _validate_locked_summary(
        cfg.phase56_summary_path,
        start_date=cfg.start_date,
        end_date=cfg.end_date,
        max_date=cfg.max_date,
        cost_bps=cfg.cost_bps,
        require_exact_start=False,
    )
    phase57_summary = _validate_locked_summary(
        cfg.phase57_summary_path,
        start_date=cfg.start_date,
        end_date=cfg.end_date,
        max_date=cfg.max_date,
        cost_bps=cfg.cost_bps,
    )
    phase54_summary = _load_json(cfg.phase54_summary_path)
    phase55_summary = _load_json(cfg.phase55_summary_path)
    phase59_summary = _load_json(cfg.phase59_summary_path)

    phase56_weights, phase56_meta = _phase56_surface(cfg)
    phase57_weights, phase57_meta, trading_dates = _phase57_surface(cfg)
    cube, daily = _build_cube_rows(
        calendar=trading_dates,
        pead_weights=phase56_weights,
        corp_weights=phase57_weights,
        meta=pd.concat([phase56_meta, phase57_meta], ignore_index=True),
    )

    summary = {
        "packet_id": PACKET_ID,
        "book_id": BOOK_ID,
        "start_date": cfg.start_date.strftime("%Y-%m-%d"),
        "end_date": cfg.end_date.strftime("%Y-%m-%d"),
        "max_date": cfg.max_date.strftime("%Y-%m-%d"),
        "cost_bps_gate": float(cfg.cost_bps),
        "engine_run_applied": False,
        "governed_input_surfaces_same_window_same_cost": True,
        "included_sleeves": [SLEEVE_PHASE56, SLEEVE_PHASE57],
        "core_sleeve_included": False,
        "core_sleeve_block_reason": (
            "phase54 core sleeve remains blocked (`ABORT_PIVOT`, `gates_passed = 4/6`, "
            "`rule100_pass_rate = 0.10132320319432121`)"
        ),
        "allocator_variant_id": phase59_summary["selected_variant"]["variant_id"],
        "allocator_gate_pass": bool(phase55_summary["allocator_gate_pass"]),
        "allocator_overlay_applied": False,
        "allocator_block_reason": (
            "allocator carry-forward excluded until research eligibility clears; overlay forced to zero"
        ),
        "phase50_reference_only_excluded": True,
        "cube_rows": int(len(cube)),
        "daily_rows": int(len(daily)),
        "active_dates": int(daily["n_active_permnos"].gt(0).sum()),
        "active_permnos": int(cube.loc[cube["book_weight_final"].abs() > 0.0, "permno"].nunique()),
        "gross_exposure_mean": float(daily["gross_exposure"].mean()),
        "gross_exposure_max": float(daily["gross_exposure"].max()),
        "turnover_total": float(daily["turnover_total"].sum()),
        "turnover_mean": float(daily["turnover_total"].mean()),
        "summary_path": str(cfg.summary_path),
        "cube_path": str(cfg.cube_path),
        "daily_path": str(cfg.daily_path),
        "source_paths": {
            "phase56_summary_path": str(cfg.phase56_summary_path),
            "phase57_summary_path": str(cfg.phase57_summary_path),
            "phase55_summary_path": str(cfg.phase55_summary_path),
            "phase54_summary_path": str(cfg.phase54_summary_path),
            "phase59_summary_path": str(cfg.phase59_summary_path),
        },
        "source_metrics": {
            "phase56_candidate_rows_same_window": int(len(phase56_meta)),
            "phase57_candidate_rows_same_window": int(len(phase57_meta)),
            "phase54_gates_passed": int(phase54_summary["gates_passed"]),
            "phase54_gates_total": int(phase54_summary["gates_total"]),
        },
    }

    cfg.summary_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_write(summary, cfg.summary_path)
    _atomic_csv_write(cube, cfg.cube_path)
    _atomic_csv_write(daily, cfg.daily_path)
    return summary


def parse_args() -> GovernedCubeConfig:
    parser = argparse.ArgumentParser(description="Build the bounded Phase 60 governed daily holdings cube.")
    parser.add_argument("--start-date", default="2015-01-01")
    parser.add_argument("--end-date", default="2022-12-31")
    parser.add_argument("--max-date", default="2022-12-31")
    parser.add_argument("--cost-bps", type=float, default=5.0)
    parser.add_argument("--cube-path", default=str(DEFAULT_CUBE_PATH))
    parser.add_argument("--daily-path", default=str(DEFAULT_DAILY_PATH))
    parser.add_argument("--summary-path", default=str(DEFAULT_SUMMARY_PATH))
    args = parser.parse_args()
    return GovernedCubeConfig(
        start_date=pd.Timestamp(args.start_date),
        end_date=pd.Timestamp(args.end_date),
        max_date=pd.Timestamp(args.max_date),
        cost_bps=float(args.cost_bps),
        cube_path=Path(args.cube_path),
        daily_path=Path(args.daily_path),
        summary_path=Path(args.summary_path),
    )


def main() -> None:
    cfg = parse_args()
    summary = build_governed_cube(cfg)
    print("=" * 72)
    print("Phase 60 Governed Cube")
    print("=" * 72)
    print(f"Window            : {summary['start_date']} .. {summary['end_date']}")
    print(f"Max Date          : {summary['max_date']}")
    print(f"Cost Gate (bps)   : {summary['cost_bps_gate']:.2f}")
    print(f"Included Sleeves  : {', '.join(summary['included_sleeves'])}")
    print(f"Allocator Overlay : {summary['allocator_overlay_applied']}")
    print(f"Cube Rows         : {summary['cube_rows']:,}")
    print(f"Daily Rows        : {summary['daily_rows']:,}")
    print(f"Active Dates      : {summary['active_dates']:,}")
    print(f"Active Permnos    : {summary['active_permnos']:,}")
    print(f"Gross Exp Mean    : {summary['gross_exposure_mean']:.4f}")
    print(f"Gross Exp Max     : {summary['gross_exposure_max']:.4f}")
    print(f"Turnover Total    : {summary['turnover_total']:.4f}")


if __name__ == "__main__":
    main()
