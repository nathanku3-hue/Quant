"""Build Winner Capture Diagnostic v0 from sealed A1/A2 bytes only.

This command performs no provider acquisition and never invokes the historical
A2 evaluator.  It verifies retained source hashes, reads the already-created
A1/A2 reports and arm matrices, and writes a historical diagnostic artifact with
``financial_alpha_evidence = 0``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.aov0.winner_capture import (  # noqa: E402
    PRIMARY_HORIZON,
    SECONDARY_HORIZON,
    WINNER_CAPTURE_SCHEMA,
    build_regime_series,
    diagnose_stage,
)


A1_CLASSIFICATION = "A1_ADMITTED_HISTORICAL_PIT"
A2_CLASSIFICATION = "A2_UNTOUCHED_HISTORICAL_PIT"
REPORT_AUTHORITY = "HISTORICAL_DIAGNOSTIC_ONLY_FINANCIAL_ALPHA_EVIDENCE_ZERO"

DEFAULT_A1_REPORT = Path("data/aov0/historical/evidence/current_stream/a1_report.json")
DEFAULT_A1_RUN_PREFIX = Path(
    "data/aov0/historical/evidence/current_stream/a1_runs/canonical_five_arm/runs/4fbd699f7934eebd"
)
DEFAULT_A2_REPORT = Path("data/aov0/historical/evidence/current_stream/a2/a2_result.json")
DEFAULT_A2_RUN_PREFIX = Path(
    "data/aov0/historical/evidence/current_stream/a2/evidence/canonical_five_arm/runs/723725475b02fc1e"
)
DEFAULT_HISTORICAL_SCREEN = Path(
    "data/aov0/historical/source_authority/20250516/final/historical_screen_20250516.csv"
)
DEFAULT_HISTORICAL_SECURITY_MASTER = Path(
    "data/aov0/historical/source_authority/20250516/ciq_productquery/historical_screen_security_identity_20250516.csv"
)
DEFAULT_CURRENT_PRIMARY_MASTER = Path("data/aov0/raw/ciq_primary_security_master_20260808T162322Z.csv")
DEFAULT_LEGACY_SMOKE_TRACE = Path(
    "docs/context/e2e_evidence/replay_selected_price_loading_mu_sndk_trace_20260515.json"
)
DEFAULT_OUT = Path("docs/context/e2e_evidence/winner_capture_diagnostic_v0_20260810.json")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _atomic_json(payload: dict[str, Any], path: Path, *, refuse_existing: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if refuse_existing and path.exists():
        raise FileExistsError(f"winner_capture_artifact_exists:{path.as_posix()}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        if refuse_existing and path.exists():
            raise FileExistsError(f"winner_capture_artifact_exists:{path.as_posix()}")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"winner_capture_json_object_required:{path.as_posix()}")
    return value


def _validate_report(report: dict[str, Any], *, stage: str) -> None:
    expected = A1_CLASSIFICATION if stage == "A1" else A2_CLASSIFICATION
    if report.get("stage") != stage:
        raise ValueError(f"winner_capture_{stage.lower()}_stage_mismatch")
    if report.get("evidence_classification") != expected:
        raise ValueError(f"winner_capture_{stage.lower()}_classification_invalid")
    if report.get("financial_alpha_evidence") != 0:
        raise ValueError(f"winner_capture_{stage.lower()}_financial_alpha_evidence_nonzero")
    ids = report.get("security_ids")
    if not isinstance(ids, list) or not ids or len(ids) != len(set(map(str, ids))):
        raise ValueError(f"winner_capture_{stage.lower()}_security_ids_invalid")
    if int(report.get("security_count", -1)) != len(ids):
        raise ValueError(f"winner_capture_{stage.lower()}_security_count_invalid")
    if stage == "A2":
        meter = report.get("a2_query_meter")
        if not isinstance(meter, dict):
            raise ValueError("winner_capture_a2_query_meter_required")
        if int(meter.get("evaluation_query_count", -1)) != 1:
            raise ValueError("winner_capture_a2_query_count_not_one")
        if meter.get("second_evaluation_forbidden") is not True:
            raise ValueError("winner_capture_a2_second_evaluation_not_forbidden")


def _verified_market_paths(report: dict[str, Any], *, stage: str) -> tuple[list[Path], list[dict[str, Any]]]:
    sources = report.get("input_sources", {}).get("market")
    if not isinstance(sources, list) or not sources:
        raise ValueError(f"winner_capture_{stage.lower()}_market_sources_required")
    paths: list[Path] = []
    manifest: list[dict[str, Any]] = []
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError(f"winner_capture_{stage.lower()}_market_source_invalid")
        path = Path(str(source.get("path") or ""))
        expected = str(source.get("sha256") or "")
        if not path.is_file():
            raise FileNotFoundError(f"winner_capture_retained_market_missing:{path.as_posix()}")
        actual = _sha256_file(path)
        if actual != expected:
            raise ValueError(f"winner_capture_retained_market_hash_mismatch:{path.name}")
        paths.append(path)
        manifest.append(
            {
                "path": path.as_posix(),
                "sha256": actual,
                "bytes": int(path.stat().st_size),
            }
        )
    return paths, manifest


def _load_market(
    report: dict[str, Any],
    paths: list[Path],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = [
        pd.read_csv(
            path,
            usecols=["SPT_DATE", "SP_CIQ_ID", "SPT_TOTAL_RETURN", "SPT_CLOSE"],
        )
        for path in paths
    ]
    raw = pd.concat(frames, ignore_index=True, sort=False)
    raw["date"] = pd.to_datetime(raw["SPT_DATE"], errors="raise").dt.normalize()
    raw["security_id"] = "CIQSEC:" + raw["SP_CIQ_ID"].astype(str)
    raw["total_return"] = pd.to_numeric(raw["SPT_TOTAL_RETURN"], errors="coerce") / 100.0
    raw["close"] = pd.to_numeric(raw["SPT_CLOSE"], errors="coerce")
    ids = [str(value) for value in report["security_ids"]]
    raw = raw.loc[raw["security_id"].isin(ids)].copy()
    if raw.duplicated(["date", "security_id"]).any():
        raise ValueError("winner_capture_market_duplicate_date_security")
    bad_return = raw["total_return"].notna() & ~np.isfinite(raw["total_return"].fillna(0.0))
    bad_close = raw["close"].notna() & ~np.isfinite(raw["close"].fillna(0.0))
    if bad_return.any() or bad_close.any():
        raise ValueError("winner_capture_market_non_finite")

    for event in report.get("replay_metadata", {}).get("terminal_events", []):
        security_id = str(event["security_id"])
        effective = pd.Timestamp(event["effective_date"]).normalize()
        last_trade = pd.Timestamp(event["last_trading_date"]).normalize()
        last_rows = raw.loc[
            raw["security_id"].eq(security_id) & raw["date"].eq(last_trade), "close"
        ].dropna()
        if len(last_rows):
            terminal_return = float(event["cash_consideration"]) / float(last_rows.iloc[0]) - 1.0
        else:
            terminal_return = event.get("terminal_return")
            if terminal_return is None:
                raise ValueError(f"winner_capture_terminal_return_unavailable:{security_id}")
            terminal_return = float(terminal_return)
        event_rows = raw["security_id"].eq(security_id) & raw["date"].ge(effective)
        raw.loc[event_rows, "total_return"] = 0.0
        raw.loc[raw["security_id"].eq(security_id) & raw["date"].eq(effective), "total_return"] = terminal_return

    returns = raw.pivot(index="date", columns="security_id", values="total_return").sort_index()
    closes = raw.pivot(index="date", columns="security_id", values="close").sort_index()
    returns = returns.reindex(columns=ids)
    closes = closes.reindex(columns=ids)
    return returns, closes


def _arm_directory(run_prefix: Path, arm: str) -> Path:
    return Path(f"{run_prefix.as_posix()}_{arm}")


def _load_arm(
    run_prefix: Path,
    *,
    arm: str,
    security_ids: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    directory = _arm_directory(run_prefix, arm)
    target_path = directory / "target_weights.csv"
    executed_path = directory / "executed_weights.csv"
    target = pd.read_csv(target_path, parse_dates=["date"]).set_index("date")
    executed = pd.read_csv(executed_path, parse_dates=["date"]).set_index("date")
    if list(target.columns) != security_ids or list(executed.columns) != security_ids:
        raise ValueError(f"winner_capture_{arm}_security_surface_mismatch")
    target.index = pd.DatetimeIndex(target.index).normalize()
    executed.index = pd.DatetimeIndex(executed.index).normalize()
    if not target.index.equals(executed.index):
        raise ValueError(f"winner_capture_{arm}_date_surface_mismatch")
    expected = target.shift(1).fillna(0.0)
    if not np.allclose(
        expected.to_numpy(dtype=float),
        executed.to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-15,
    ):
        raise ValueError(f"winner_capture_{arm}_execution_lag_mismatch")
    return target, executed, {
        "target_weights": {
            "path": target_path.as_posix(),
            "sha256": _sha256_file(target_path),
            "bytes": int(target_path.stat().st_size),
        },
        "executed_weights": {
            "path": executed_path.as_posix(),
            "sha256": _sha256_file(executed_path),
            "bytes": int(executed_path.stat().st_size),
        },
    }


def _parse_ticker(company_name: object) -> str | None:
    match = re.search(r":([^:()]+)\)\s*$", str(company_name or ""))
    return match.group(1).strip().upper() if match else None


def _identity_map(
    *,
    screen_path: Path,
    security_master_path: Path,
    security_ids: list[str],
) -> dict[str, dict[str, Any]]:
    screen = pd.read_csv(screen_path)
    security = pd.read_csv(security_master_path)
    required_security = {"SP_ENTITY_ID", "SP_CIQ_ID"}
    if not required_security.issubset(security.columns) or not {"SP_ENTITY_ID", "CompanyName"}.issubset(screen.columns):
        raise ValueError("winner_capture_identity_source_schema_invalid")
    security = security.copy()
    security["security_id"] = "CIQSEC:" + security["SP_CIQ_ID"].astype(str)
    merged = security[["security_id", "SP_ENTITY_ID"]].merge(
        screen[["SP_ENTITY_ID", "CompanyName"]],
        on="SP_ENTITY_ID",
        how="left",
        validate="many_to_one",
    )
    merged = merged.loc[merged["security_id"].isin(security_ids)].copy()
    result: dict[str, dict[str, Any]] = {}
    for row in merged.itertuples(index=False):
        result[str(row.security_id)] = {
            "source_entity_id": str(row.SP_ENTITY_ID),
            "ticker": _parse_ticker(row.CompanyName),
            "company_name": None if pd.isna(row.CompanyName) else str(row.CompanyName),
        }
    return result


def _stage_payload(
    *,
    stage: str,
    report_path: Path,
    run_prefix: Path,
    identity: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    report = _load_json(report_path)
    _validate_report(report, stage=stage)
    security_ids = [str(value) for value in report["security_ids"]]
    if sorted(identity) != sorted(security_ids):
        missing = sorted(set(security_ids) - set(identity))
        if missing:
            raise ValueError("winner_capture_identity_missing:" + missing[0])

    market_paths, market_manifest = _verified_market_paths(report, stage=stage)
    returns_full, closes_full = _load_market(report, market_paths)
    rule_target, rule_exec, rule_manifest = _load_arm(
        run_prefix, arm="rule100", security_ids=security_ids
    )
    parent_target, parent_exec, parent_manifest = _load_arm(
        run_prefix, arm="parent", security_ids=security_ids
    )
    child_target, child_exec, child_manifest = _load_arm(
        run_prefix, arm="child", security_ids=security_ids
    )
    if not rule_target.index.equals(parent_target.index) or not rule_target.index.equals(child_target.index):
        raise ValueError(f"winner_capture_{stage.lower()}_arm_calendar_mismatch")

    returns = returns_full.reindex(index=rule_target.index, columns=security_ids)
    if returns.isna().any().any() or not np.isfinite(returns.to_numpy(dtype=float)).all():
        raise ValueError(f"winner_capture_{stage.lower()}_return_surface_incomplete")
    terminal_dates = {
        str(event["security_id"]): str(event["effective_date"])
        for event in report.get("replay_metadata", {}).get("terminal_events", [])
    }
    regime = build_regime_series(
        closes_full,
        active_security_ids=security_ids,
        terminal_effective_dates=terminal_dates,
    )
    diagnostic = diagnose_stage(
        stage=stage,
        total_returns=returns,
        rule100_targets=rule_target,
        parent_targets=parent_target,
        child_targets=child_target,
        parent_executed=parent_exec,
        child_executed=child_exec,
        regime=regime,
        horizons=(PRIMARY_HORIZON, SECONDARY_HORIZON),
        identity_by_security=identity,
    )
    metrics = report["metrics"]
    diagnostic["reported_stage_economics"] = {
        "parent_gross_return_sum": float(metrics["parent"]["gross_return_sum"]),
        "child_gross_return_sum": float(metrics["child"]["gross_return_sum"]),
        "parent_minus_child_gross_gap": float(
            metrics["parent"]["gross_return_sum"] - metrics["child"]["gross_return_sum"]
        ),
        "parent_total_cost_drag": float(metrics["parent"]["total_cost_drag"]),
        "child_total_cost_drag": float(metrics["child"]["total_cost_drag"]),
        "child_cost_savings_vs_parent": float(
            metrics["parent"]["total_cost_drag"] - metrics["child"]["total_cost_drag"]
        ),
    }
    recomputed = diagnostic["whole_stage_parent_child_attribution"][
        "parent_minus_child_gross_contribution_gap"
    ]
    reported = diagnostic["reported_stage_economics"]["parent_minus_child_gross_gap"]
    if not np.isclose(float(recomputed), float(reported), rtol=0.0, atol=1e-12):
        raise ValueError(f"winner_capture_{stage.lower()}_gross_gap_reconciliation_failed")

    custody = {
        "stage_report": {
            "path": report_path.as_posix(),
            "sha256": _sha256_file(report_path),
            "report_content_hash": report.get("report_content_hash"),
            "evidence_classification": report.get("evidence_classification"),
        },
        "market_sources": market_manifest,
        "arm_sources": {
            "rule100": rule_manifest,
            "parent": parent_manifest,
            "child": child_manifest,
        },
    }
    return diagnostic, custody


def _screen_tickers(screen_path: Path, *, allowed_entity_ids: set[str]) -> set[str]:
    screen = pd.read_csv(screen_path)
    tickers: set[str] = set()
    for row in screen.itertuples(index=False):
        if str(row.SP_ENTITY_ID) not in allowed_entity_ids:
            continue
        ticker = _parse_ticker(row.CompanyName)
        if ticker:
            tickers.add(ticker)
    return tickers


def _smoke_probes(
    symbols: list[str],
    *,
    a2_report: dict[str, Any],
    historical_screen_path: Path,
    current_primary_master_path: Path,
    legacy_trace_path: Path,
) -> list[dict[str, Any]]:
    if not symbols:
        return []
    allowed_entities = {str(value) for value in a2_report.get("source_entity_ids", [])}
    lane2_tickers = _screen_tickers(historical_screen_path, allowed_entity_ids=allowed_entities)
    current = pd.read_csv(current_primary_master_path)
    current_tickers = {str(value).strip().upper() for value in current.get("Ticker", pd.Series(dtype=str)).dropna()}
    legacy_payload = _load_json(legacy_trace_path)
    legacy_by_ticker = {
        str(row.get("ticker") or "").strip().upper(): row
        for row in legacy_payload.get("trace", [])
        if isinstance(row, dict)
    }

    probes: list[dict[str, Any]] = []
    for raw_symbol in symbols:
        symbol = str(raw_symbol).strip().upper()
        if not symbol:
            raise ValueError("winner_capture_smoke_symbol_empty")
        in_lane2 = symbol in lane2_tickers
        in_current = symbol in current_tickers
        if not in_lane2:
            deterministic_status = "NOT_IN_RETAINED_LANE2_COHORT"
        elif not in_current:
            deterministic_status = "NOT_IN_CURRENT_CIQ_PRIMARY_MASTER"
        else:
            deterministic_status = "IN_CIQ_MASTER_AND_RETAINED_LANE2_COHORT"
        legacy = legacy_by_ticker.get(symbol)
        probes.append(
            {
                "symbol": symbol,
                "acceptance_weight": 0,
                "special_case_code_authorized": False,
                "in_retained_lane2_cohort": in_lane2,
                "in_current_ciq_primary_master": in_current,
                "deterministic_status": deterministic_status,
                "legacy_diagnostic_only": (
                    None
                    if legacy is None
                    else {
                        "latest_sizing_eligible": legacy.get("latest_sizing_eligible"),
                        "rule100_history_dates": legacy.get("rule100_history_dates"),
                        "eligible_feature_dates": legacy.get("eligible_feature_dates"),
                        "latest_exclusion_gate": legacy.get("latest_exclusion_gate"),
                        "latest_exclusion_detail": legacy.get("latest_exclusion_detail"),
                        "source_path": legacy_trace_path.as_posix(),
                        "source_sha256": _sha256_file(legacy_trace_path),
                    }
                ),
            }
        )
    return probes


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    a1_report = _load_json(args.a1_report)
    a2_report = _load_json(args.a2_report)
    _validate_report(a1_report, stage="A1")
    _validate_report(a2_report, stage="A2")
    if list(map(str, a1_report["security_ids"])) != list(map(str, a2_report["security_ids"])):
        raise ValueError("winner_capture_a1_a2_frozen_security_set_mismatch")
    security_ids = [str(value) for value in a2_report["security_ids"]]
    identity = _identity_map(
        screen_path=args.historical_screen,
        security_master_path=args.historical_security_master,
        security_ids=security_ids,
    )
    a1, a1_custody = _stage_payload(
        stage="A1",
        report_path=args.a1_report,
        run_prefix=args.a1_run_prefix,
        identity=identity,
    )
    a2, a2_custody = _stage_payload(
        stage="A2",
        report_path=args.a2_report,
        run_prefix=args.a2_run_prefix,
        identity=identity,
    )
    smoke = _smoke_probes(
        args.smoke_symbol,
        a2_report=a2_report,
        historical_screen_path=args.historical_screen,
        current_primary_master_path=args.current_primary_master,
        legacy_trace_path=args.legacy_smoke_trace,
    )
    payload: dict[str, Any] = {
        "schema_version": WINNER_CAPTURE_SCHEMA,
        "status": "FROZEN_RETAINED_BYTE_DIAGNOSTIC",
        "evidence_authority": REPORT_AUTHORITY,
        "financial_alpha_evidence": 0,
        "a2_requery_count": 0,
        "a2_second_evaluation_performed": False,
        "provider_calls_performed": 0,
        "parent_child_mutated": False,
        "clock_1_outcome_accessed": False,
        "frozen_as_of_utc": a2_report.get("created_at_utc"),
        "primary_label": {
            "label_spec_id": "AOV_WINNER_CAPTURE_NEXT10D_TOP5_V0",
            "horizon_sessions": PRIMARY_HORIZON,
            "winner_fraction": 0.05,
        },
        "secondary_label": {
            "label_spec_id": "AOV_WINNER_CAPTURE_NEXT20D_TOP5_V0",
            "horizon_sessions": SECONDARY_HORIZON,
            "winner_fraction": 0.05,
        },
        "risk_set_law": {
            "label_universe": "FROZEN_LANE2_94_PRIMARY_SECURITY_COHORT",
            "out_of_cohort_winner_recall_inference_authorized": False,
            "limitation": "The retained A1/A2 label universe measures access conditional on the frozen Lane-2 cohort; it cannot estimate winner recall for names absent from that cohort.",
        },
        "stage_diagnostics": {"A1": a1, "A2": a2},
        "smoke_probes": smoke,
        "acceptance_boundary": {
            "a1_a2_are_acceptance_evidence_for_new_family": False,
            "new_family_acceptance_requires": "NEW_UNTOUCHED_OR_PROSPECTIVE_FREEZE_WITH_CROSS_SECTIONAL_WINNER_RECALL_LIFT",
            "named_smoke_probes_are_pass_fail_gate": False,
        },
        "custody": {
            "A1": a1_custody,
            "A2": a2_custody,
            "historical_screen": {
                "path": args.historical_screen.as_posix(),
                "sha256": _sha256_file(args.historical_screen),
            },
            "historical_security_master": {
                "path": args.historical_security_master.as_posix(),
                "sha256": _sha256_file(args.historical_security_master),
            },
            "current_primary_master_smoke_only": {
                "path": args.current_primary_master.as_posix(),
                "sha256": _sha256_file(args.current_primary_master),
            },
        },
    }
    payload["report_content_hash"] = _canonical_json_hash(payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a1-report", type=Path, default=DEFAULT_A1_REPORT)
    parser.add_argument("--a1-run-prefix", type=Path, default=DEFAULT_A1_RUN_PREFIX)
    parser.add_argument("--a2-report", type=Path, default=DEFAULT_A2_REPORT)
    parser.add_argument("--a2-run-prefix", type=Path, default=DEFAULT_A2_RUN_PREFIX)
    parser.add_argument("--historical-screen", type=Path, default=DEFAULT_HISTORICAL_SCREEN)
    parser.add_argument(
        "--historical-security-master", type=Path, default=DEFAULT_HISTORICAL_SECURITY_MASTER
    )
    parser.add_argument("--current-primary-master", type=Path, default=DEFAULT_CURRENT_PRIMARY_MASTER)
    parser.add_argument("--legacy-smoke-trace", type=Path, default=DEFAULT_LEGACY_SMOKE_TRACE)
    parser.add_argument("--smoke-symbol", action="append", default=[])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--refuse-existing", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    _atomic_json(report, args.out, refuse_existing=args.refuse_existing)
    primary_a1 = report["stage_diagnostics"]["A1"]["horizons"][str(PRIMARY_HORIZON)]["aggregate"]
    primary_a2 = report["stage_diagnostics"]["A2"]["horizons"][str(PRIMARY_HORIZON)]["aggregate"]
    secondary_a2 = report["stage_diagnostics"]["A2"]["horizons"][str(SECONDARY_HORIZON)]["aggregate"]
    print(
        json.dumps(
            {
                "out": args.out.as_posix(),
                "report_content_hash": report["report_content_hash"],
                "A1_10d_recall": primary_a1["winner_recall"],
                "A1_10d_breadth": primary_a1["selection_breadth_mean"],
                "A2_10d_recall": primary_a2["winner_recall"],
                "A2_10d_breadth": primary_a2["selection_breadth_mean"],
                "A2_20d_recall": secondary_a2["winner_recall"],
                "A2_top5_realized_winner_gap_share": report["stage_diagnostics"]["A2"]
                ["whole_stage_parent_child_attribution"]["largest_realized_winner_gap_share"],
                "financial_alpha_evidence": report["financial_alpha_evidence"],
                "a2_requery_count": report["a2_requery_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
