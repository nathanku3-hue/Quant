from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.day5_ablation_report import _atomic_csv_write  # noqa: E402
from scripts.day5_ablation_report import _atomic_json_write  # noqa: E402


EVIDENCE_DIR = PROJECT_ROOT / "docs" / "context" / "e2e_evidence"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_PREFLIGHT_PATH = EVIDENCE_DIR / "phase60_d340_preflight_20260319_summary.json"
DEFAULT_AUDIT_SUMMARY_PATH = PROCESSED_DIR / "phase60_governed_audit_summary.json"
DEFAULT_AUDIT_EVIDENCE_PATH = PROCESSED_DIR / "phase60_governed_audit_evidence.csv"
DEFAULT_AUDIT_DELTA_PATH = PROCESSED_DIR / "phase60_governed_audit_delta.csv"
DEFAULT_OUTPUT_SUMMARY_PATH = EVIDENCE_DIR / "phase60_d341_review_20260319_summary.json"
DEFAULT_OUTPUT_FINDINGS_PATH = EVIDENCE_DIR / "phase60_d341_review_20260319_findings.csv"
DEFAULT_OUTPUT_STATUS_PATH = EVIDENCE_DIR / "phase60_d341_review_20260319.status.txt"
EXPECTED_PREFLIGHT_PACKET_ID = "PHASE60_D340_PREFLIGHT_V1"
EXPECTED_AUDIT_PACKET_ID = "PHASE60_GOVERNED_AUDIT_V1"
EXPECTED_BOOK_ID = "PHASE60_GOVERNED_BOOK_V1"
EXPECTED_KILL_SWITCH = "KS-03_same_period_c3_unavailable"
EXPECTED_MISSING_RETURN_CELLS = 274
EXPECTED_DELTA_LANES = ["5bps_gate", "10bps_sensitivity"]
EXPECTED_EVIDENCE_COLUMNS = [
    "date",
    "book_id",
    "gross_exposure",
    "turnover_total",
    "n_active_permnos",
    "net_ret_5bps",
    "net_ret_10bps",
]


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


@dataclass(frozen=True)
class ReviewConfig:
    preflight_path: Path = DEFAULT_PREFLIGHT_PATH
    audit_summary_path: Path = DEFAULT_AUDIT_SUMMARY_PATH
    audit_evidence_path: Path = DEFAULT_AUDIT_EVIDENCE_PATH
    audit_delta_path: Path = DEFAULT_AUDIT_DELTA_PATH
    output_summary_path: Path = DEFAULT_OUTPUT_SUMMARY_PATH
    output_findings_path: Path = DEFAULT_OUTPUT_FINDINGS_PATH
    output_status_path: Path = DEFAULT_OUTPUT_STATUS_PATH


@dataclass(frozen=True)
class ReviewArtifacts:
    preflight: dict[str, Any]
    audit_summary: dict[str, Any]
    audit_evidence: pd.DataFrame
    audit_delta: pd.DataFrame


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_inputs(cfg: ReviewConfig) -> ReviewArtifacts:
    return ReviewArtifacts(
        preflight=_load_json(cfg.preflight_path),
        audit_summary=_load_json(cfg.audit_summary_path),
        audit_evidence=pd.read_csv(cfg.audit_evidence_path),
        audit_delta=pd.read_csv(cfg.audit_delta_path),
    )


def _atomic_text_write(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    tries = 8
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        for i in range(tries):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if i >= tries - 1:
                    raise
                time.sleep(0.15 * (i + 1))
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _extract_missing_return_cells(message: str | None) -> int | None:
    if not message:
        return None
    match = re.search(r"Missing\s+([\d,]+)\s+return cells on executed exposures", str(message), flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _build_finding(
    *,
    finding_id: str,
    source_artifact: Path,
    check_name: str,
    expected: Any,
    observed: Any,
    status: bool,
    notes: str,
) -> dict[str, Any]:
    return {
        "finding_id": finding_id,
        "source_artifact": _display_path(source_artifact),
        "check_name": check_name,
        "expected": json.dumps(expected, sort_keys=True) if isinstance(expected, (dict, list)) else str(expected),
        "observed": json.dumps(observed, sort_keys=True) if isinstance(observed, (dict, list)) else str(observed),
        "status": "PASS" if status else "FAIL",
        "notes": notes,
    }


def _require(status: bool, message: str) -> None:
    if not status:
        raise RuntimeError(message)


def run_blocked_audit_review(cfg: ReviewConfig) -> dict[str, Any]:
    artifacts = _load_inputs(cfg)

    findings: list[dict[str, Any]] = []

    preflight_packet_id = str(artifacts.preflight.get("packet_id", ""))
    preflight_passed = bool(artifacts.preflight.get("passed", False))
    preflight_checks = artifacts.preflight.get("checks", {})
    findings.append(
        _build_finding(
            finding_id="RV-01",
            source_artifact=cfg.preflight_path,
            check_name="d340_preflight_passed",
            expected={"packet_id": EXPECTED_PREFLIGHT_PACKET_ID, "passed": True},
            observed={"packet_id": preflight_packet_id, "passed": preflight_passed},
            status=preflight_packet_id == EXPECTED_PREFLIGHT_PACKET_ID and preflight_passed,
            notes="D-341 review remains bounded to the published D-340 preflight packet.",
        )
    )
    _require(preflight_packet_id == EXPECTED_PREFLIGHT_PACKET_ID, "D-340 preflight packet_id mismatch")
    _require(preflight_passed, "D-340 preflight did not pass")
    _require(all(bool(v) for v in preflight_checks.values()), "D-340 preflight checks are not all PASS")

    audit_packet_id = str(artifacts.audit_summary.get("packet_id", ""))
    audit_status = str(artifacts.audit_summary.get("status", ""))
    findings.append(
        _build_finding(
            finding_id="RV-02",
            source_artifact=cfg.audit_summary_path,
            check_name="d340_audit_blocked",
            expected={"packet_id": EXPECTED_AUDIT_PACKET_ID, "status": "blocked"},
            observed={"packet_id": audit_packet_id, "status": audit_status},
            status=audit_packet_id == EXPECTED_AUDIT_PACKET_ID and audit_status == "blocked",
            notes="D-341 is an evidence-only review of the already blocked D-340 audit packet.",
        )
    )
    _require(audit_packet_id == EXPECTED_AUDIT_PACKET_ID, "D-340 audit packet_id mismatch")
    _require(audit_status == "blocked", "D-340 audit status must remain blocked")

    kill_switches = [str(item) for item in artifacts.audit_summary.get("kill_switches_triggered", [])]
    findings.append(
        _build_finding(
            finding_id="RV-03",
            source_artifact=cfg.audit_summary_path,
            check_name="ks03_present",
            expected=[EXPECTED_KILL_SWITCH],
            observed=kill_switches,
            status=EXPECTED_KILL_SWITCH in kill_switches,
            notes="The same-period comparator block must remain explicit and machine-readable.",
        )
    )
    _require(EXPECTED_KILL_SWITCH in kill_switches, "D-340 audit summary is missing KS-03_same_period_c3_unavailable")

    comparator_error = str(artifacts.audit_summary.get("comparator_error", ""))
    missing_cells = _extract_missing_return_cells(comparator_error)
    findings.append(
        _build_finding(
            finding_id="RV-04",
            source_artifact=cfg.audit_summary_path,
            check_name="missing_executed_exposure_return_cells",
            expected=EXPECTED_MISSING_RETURN_CELLS,
            observed=missing_cells,
            status=missing_cells == EXPECTED_MISSING_RETURN_CELLS,
            notes="The exact 274-cell executed-exposure return gap is part of the D-341 review contract.",
        )
    )
    _require(
        missing_cells == EXPECTED_MISSING_RETURN_CELLS,
        "D-340 comparator_error must preserve the exact 274 executed-exposure missing-return cells",
    )

    summary_comparator_empty = bool(not artifacts.audit_summary.get("same_period_c3_5bps", {}).get("metrics_c3")) and bool(
        not artifacts.audit_summary.get("same_period_c3_10bps", {}).get("metrics_c3")
    )
    findings.append(
        _build_finding(
            finding_id="RV-05",
            source_artifact=cfg.audit_summary_path,
            check_name="comparator_metrics_absent_in_blocked_packet",
            expected=True,
            observed=summary_comparator_empty,
            status=summary_comparator_empty,
            notes="Blocked D-340 comparator fields must remain empty rather than fabricated.",
        )
    )
    _require(summary_comparator_empty, "Blocked D-340 comparator metrics must remain empty")

    evidence = artifacts.audit_evidence.copy()
    findings.append(
        _build_finding(
            finding_id="RV-06",
            source_artifact=cfg.audit_evidence_path,
            check_name="audit_evidence_shape",
            expected={"non_empty": True, "columns": EXPECTED_EVIDENCE_COLUMNS},
            observed={"non_empty": not evidence.empty, "columns": list(evidence.columns)},
            status=(not evidence.empty and list(evidence.columns) == EXPECTED_EVIDENCE_COLUMNS),
            notes="Daily governed evidence must be present for the evidence-only hold packet.",
        )
    )
    _require(not evidence.empty, "D-340 audit evidence CSV is empty")
    _require(list(evidence.columns) == EXPECTED_EVIDENCE_COLUMNS, "D-340 audit evidence schema drifted")
    _require(evidence["book_id"].astype(str).eq(EXPECTED_BOOK_ID).all(), "D-340 audit evidence contains unexpected book_id values")

    delta = artifacts.audit_delta.copy()
    observed_lanes = delta["lane"].astype(str).tolist() if "lane" in delta.columns else []
    comparator_available = [str(value).strip().lower() == "true" for value in delta.get("comparator_available", pd.Series(dtype=object))]
    findings.append(
        _build_finding(
            finding_id="RV-07",
            source_artifact=cfg.audit_delta_path,
            check_name="delta_lanes_and_comparator_availability",
            expected={"lanes": EXPECTED_DELTA_LANES, "comparator_available": [False, False]},
            observed={"lanes": observed_lanes, "comparator_available": comparator_available},
            status=(observed_lanes == EXPECTED_DELTA_LANES and comparator_available == [False, False]),
            notes="The bounded D-340 delta packet must remain two-lane and comparator-unavailable in both lanes.",
        )
    )
    _require(observed_lanes == EXPECTED_DELTA_LANES, "D-340 audit delta must contain exactly the 5bps and 10bps lanes")
    _require(comparator_available == [False, False], "D-340 audit delta must keep comparator_available false in both lanes")

    allocator_block = not bool(artifacts.audit_summary.get("allocator_overlay_applied", True))
    core_block = not bool(artifacts.audit_summary.get("core_sleeve_included", True))
    findings.append(
        _build_finding(
            finding_id="RV-08",
            source_artifact=cfg.audit_summary_path,
            check_name="allocator_and_core_blocks_preserved",
            expected={"allocator_overlay_applied": False, "core_sleeve_included": False},
            observed={
                "allocator_overlay_applied": bool(artifacts.audit_summary.get("allocator_overlay_applied", True)),
                "core_sleeve_included": bool(artifacts.audit_summary.get("core_sleeve_included", True)),
            },
            status=allocator_block and core_block,
            notes="D-341 must preserve the allocator/core governance hold with no promotion path.",
        )
    )
    _require(allocator_block, "Allocator overlay must remain blocked in D-340 SSOT artifacts")
    _require(core_block, "Core sleeve must remain excluded in D-340 SSOT artifacts")

    findings_df = pd.DataFrame(findings)
    review_status = "blocked_confirmed"
    summary = {
        "packet_id": "PHASE60_D341_BLOCKED_AUDIT_REVIEW_V1",
        "source_packet_id": EXPECTED_AUDIT_PACKET_ID,
        "active_phase": 60,
        "review_scope": "blocked_audit_review_evidence_only",
        "review_status": review_status,
        "disposition": "evidence_only_hold",
        "hold_reason": "same_period_c3_comparator_unavailable_under_strict_missing_return_rules",
        "start_date": str(artifacts.audit_summary.get("start_date", "")),
        "end_date": str(artifacts.audit_summary.get("end_date", "")),
        "preflight_passed": preflight_passed,
        "audit_status": audit_status,
        "kill_switches_triggered": kill_switches,
        "comparator_error": comparator_error,
        "missing_executed_exposure_return_cells": EXPECTED_MISSING_RETURN_CELLS,
        "comparator_available": False,
        "reviewed_delta_lanes": EXPECTED_DELTA_LANES,
        "evidence_rows_reviewed": int(len(evidence)),
        "delta_rows_reviewed": int(len(delta)),
        "book_id": EXPECTED_BOOK_ID,
        "promotion_authorized": False,
        "remediation_authorized": False,
        "widening_authorized": False,
        "allocator_carry_forward_authorized": False,
        "core_sleeve_inclusion_authorized": False,
        "research_data_mutation_authorized": False,
        "kernel_mutation_authorized": False,
        "input_artifacts": {
            "preflight_path": _display_path(cfg.preflight_path),
            "audit_summary_path": _display_path(cfg.audit_summary_path),
            "audit_evidence_path": _display_path(cfg.audit_evidence_path),
            "audit_delta_path": _display_path(cfg.audit_delta_path),
        },
        "output_artifacts": {
            "summary_path": _display_path(cfg.output_summary_path),
            "findings_path": _display_path(cfg.output_findings_path),
            "status_path": _display_path(cfg.output_status_path),
        },
    }

    cfg.output_summary_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_write(summary, cfg.output_summary_path)
    _atomic_csv_write(findings_df, cfg.output_findings_path)
    _atomic_text_write(
        "PASS: D-341 blocked audit review confirmed evidence-only hold; D-340 SSOT remains blocked with KS-03 and 274 missing executed-exposure return cells.\n",
        cfg.output_status_path,
    )
    return summary


def parse_args() -> ReviewConfig:
    parser = argparse.ArgumentParser(description="Review the immutable D-340 blocked audit packet and publish D-341 evidence-only hold artifacts.")
    parser.add_argument("--preflight-path", default=str(DEFAULT_PREFLIGHT_PATH))
    parser.add_argument("--audit-summary-path", default=str(DEFAULT_AUDIT_SUMMARY_PATH))
    parser.add_argument("--audit-evidence-path", default=str(DEFAULT_AUDIT_EVIDENCE_PATH))
    parser.add_argument("--audit-delta-path", default=str(DEFAULT_AUDIT_DELTA_PATH))
    parser.add_argument("--output-summary-path", default=str(DEFAULT_OUTPUT_SUMMARY_PATH))
    parser.add_argument("--output-findings-path", default=str(DEFAULT_OUTPUT_FINDINGS_PATH))
    parser.add_argument("--output-status-path", default=str(DEFAULT_OUTPUT_STATUS_PATH))
    args = parser.parse_args()
    return ReviewConfig(
        preflight_path=Path(args.preflight_path),
        audit_summary_path=Path(args.audit_summary_path),
        audit_evidence_path=Path(args.audit_evidence_path),
        audit_delta_path=Path(args.audit_delta_path),
        output_summary_path=Path(args.output_summary_path),
        output_findings_path=Path(args.output_findings_path),
        output_status_path=Path(args.output_status_path),
    )


def main() -> int:
    summary = run_blocked_audit_review(parse_args())
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
