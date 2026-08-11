"""Admit the completed S0 structured corpus and run the M0-vs-M1 shootout.

This runner reads only the frozen structured economic capture plus its exact
identity master.  It does not read market data, winner labels, W6, or any
selection outcome.  The default evaluator hardening is intentionally minimal:
minimum fold N, minimum fold coverage, and PARTIAL_SUPPORT.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.econphysics_prebreakout_v1.contracts import (
    FILING_VERSION,
    RELATIVE_PERIODS,
    REQUEST_METRICS,
    VALUE_UNIT,
    build_structured_snapshots,
    conservative_available_at,
)
from research.econphysics_prebreakout_v1.shootout_evaluator import (
    DEFAULT_MINIMUM_FOLD_COVERAGE,
    DEFAULT_MINIMUM_FOLD_N,
    evaluate_m0_m1_shootout,
)


REPORT_SCHEMA = "econphysics_prebreakout_s0_m0_m1_real_corpus_report_v2"
EXPECTED_PROVIDER_FUNCTION = "SPG"


class ShootoutAdmissionError(ValueError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            raise FileExistsError(f"econphysics_s0_shootout_output_exists:{path}")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def _master_map(master_rows: Sequence[Mapping[str, str]]) -> dict[str, str]:
    output: dict[str, str] = {}
    reverse: dict[str, str] = {}
    for row in master_rows:
        entity = str(row.get("SP_ENTITY_ID") or "").strip()
        security = str(row.get("security_id") or "").strip().upper()
        if not entity.isdigit() or not security.startswith("CIQSEC:IQ"):
            raise ShootoutAdmissionError("econphysics_s0_shootout_master_identity_invalid")
        prior = output.setdefault(entity, security)
        if prior != security:
            raise ShootoutAdmissionError("econphysics_s0_shootout_entity_security_drift")
        prior_entity = reverse.setdefault(security, entity)
        if prior_entity != entity:
            raise ShootoutAdmissionError("econphysics_s0_shootout_security_entity_drift")
    if not output:
        raise ShootoutAdmissionError("econphysics_s0_shootout_master_empty")
    return output


def _validate_receipt(
    raw_path: Path,
    master_path: Path,
    transition_plan_path: Path,
    receipt: Mapping[str, Any],
) -> None:
    if receipt.get("raw_object_sha256") != _sha256(raw_path):
        raise ShootoutAdmissionError("econphysics_s0_shootout_raw_receipt_hash_mismatch")
    if receipt.get("master_sha256") != _sha256(master_path):
        raise ShootoutAdmissionError("econphysics_s0_shootout_master_receipt_hash_mismatch")
    if receipt.get("source_plan_sha256") != _sha256(transition_plan_path):
        raise ShootoutAdmissionError("econphysics_s0_shootout_transition_plan_receipt_hash_mismatch")
    if receipt.get("filing_version") != FILING_VERSION:
        raise ShootoutAdmissionError("econphysics_s0_shootout_filing_version_invalid")
    if receipt.get("provider_function") != EXPECTED_PROVIDER_FUNCTION:
        raise ShootoutAdmissionError("econphysics_s0_shootout_provider_function_invalid")
    if list(receipt.get("relative_periods") or []) != list(RELATIVE_PERIODS):
        raise ShootoutAdmissionError("econphysics_s0_shootout_relative_periods_invalid")
    if list(receipt.get("metrics") or []) != list(REQUEST_METRICS):
        raise ShootoutAdmissionError("econphysics_s0_shootout_metrics_invalid")
    if receipt.get("winner_or_equity_outcome_access_performed") is not False:
        raise ShootoutAdmissionError("econphysics_s0_shootout_outcome_firewall_receipt_invalid")
    if receipt.get("w6_access_performed") is not False or receipt.get("selection_performed") is not False:
        raise ShootoutAdmissionError("econphysics_s0_shootout_forbidden_surface_receipt_invalid")


def _transition_plan_maps(
    plan_rows: Sequence[Mapping[str, str]],
    *,
    entity_to_security: Mapping[str, str],
) -> tuple[dict[tuple[str, str], str], dict[tuple[str, str, str], str]]:
    expected_fq0: dict[tuple[str, str], str] = {}
    predecessor: dict[tuple[str, str, str], str] = {}
    for row in plan_rows:
        entity = str(row.get("source_entity_id") or "").strip()
        security = str(row.get("security_id") or "").strip().upper()
        if entity_to_security.get(entity) != security:
            raise ShootoutAdmissionError("econphysics_s0_shootout_transition_plan_identity_drift")
        as_of = str(row.get("as_of_date") or "").strip()
        fq0_period_end = str(row.get("fq0_period_end") or "").strip()
        prior_period_end = str(row.get("prior_fq0_period_end") or "").strip()
        if not as_of or not fq0_period_end or not prior_period_end:
            raise ShootoutAdmissionError("econphysics_s0_shootout_transition_plan_period_identity_missing")
        if str(row.get("transition_reason") or "").strip() != "FQ0_PERIOD_CHANGE":
            raise ShootoutAdmissionError("econphysics_s0_shootout_transition_plan_reason_invalid")
        group_key = (entity, as_of)
        snapshot_key = (security, entity, as_of)
        if group_key in expected_fq0 or snapshot_key in predecessor:
            raise ShootoutAdmissionError("econphysics_s0_shootout_transition_plan_duplicate")
        expected_fq0[group_key] = fq0_period_end
        predecessor[snapshot_key] = prior_period_end
    if not expected_fq0:
        raise ShootoutAdmissionError("econphysics_s0_shootout_transition_plan_empty")
    return expected_fq0, predecessor


def _admit_rows(
    raw_rows: Sequence[Mapping[str, str]],
    *,
    entity_to_security: Mapping[str, str],
    receipt_sha256: str,
    expected_fq0_by_snapshot: Mapping[tuple[str, str], str],
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    metric_fields = ("IQ_TOTAL_REV", "IQ_INVENTORY", "IQ_OPER_INC", "IQ_CAPEX_BNK")
    raw_missing = {"period_end": 0, **{field: 0 for field in metric_fields}}
    admitted_missing = {"period_end": 0, **{field: 0 for field in metric_fields}}
    provider_functions: set[str] = set()
    filing_versions: set[str] = set()
    grouped_rows: dict[tuple[str, str], dict[str, Mapping[str, str]]] = {}

    for row in raw_rows:
        entity = str(row.get("source_entity_id") or "").strip()
        if entity not in entity_to_security:
            raise ShootoutAdmissionError(f"econphysics_s0_shootout_entity_outside_master:{entity}")
        as_of = str(row.get("as_of_date") or "").strip()
        relative_period = str(row.get("relative_period") or "").strip().upper()
        if relative_period not in RELATIVE_PERIODS:
            raise ShootoutAdmissionError("econphysics_s0_shootout_relative_period_invalid")
        provider_functions.add(str(row.get("provider_function") or "").strip())
        filing_versions.add(str(row.get("filing_version") or "").strip())
        group = grouped_rows.setdefault((entity, as_of), {})
        if relative_period in group:
            raise ShootoutAdmissionError("econphysics_s0_shootout_duplicate_entity_asof_relative_period")
        group[relative_period] = row
        for field in raw_missing:
            if not str(row.get(field) or "").strip():
                raw_missing[field] += 1

    if provider_functions != {EXPECTED_PROVIDER_FUNCTION}:
        raise ShootoutAdmissionError("econphysics_s0_shootout_row_provider_function_drift")
    if filing_versions != {FILING_VERSION}:
        raise ShootoutAdmissionError("econphysics_s0_shootout_row_filing_version_drift")
    bad_grids = sum(set(group) != set(RELATIVE_PERIODS) for group in grouped_rows.values())
    if bad_grids:
        raise ShootoutAdmissionError(f"econphysics_s0_shootout_raw_five_quarter_grid_invalid:{bad_grids}")
    if set(grouped_rows) != set(expected_fq0_by_snapshot):
        raise ShootoutAdmissionError("econphysics_s0_shootout_transition_plan_capture_membership_drift")

    fq0_plan_capture_mismatch_keys = {
        key
        for key, group in grouped_rows.items()
        if str(group["FQ0"].get("period_end") or "").strip() != expected_fq0_by_snapshot[key]
    }
    duplicate_alias_keys: set[tuple[str, str, str]] = set()
    duplicate_period_end_snapshot_count = 0
    for (entity, as_of), group in grouped_rows.items():
        seen_period_ends: set[str] = set()
        snapshot_has_alias = False
        for relative_period in RELATIVE_PERIODS:
            period_end = str(group[relative_period].get("period_end") or "").strip()
            if not period_end:
                continue
            if period_end in seen_period_ends:
                # RELATIVE_PERIODS is newest-to-oldest.  Preserve the first
                # (newer) occurrence and quarantine the older alias row.
                duplicate_alias_keys.add((entity, as_of, relative_period))
                snapshot_has_alias = True
            else:
                seen_period_ends.add(period_end)
        duplicate_period_end_snapshot_count += int(snapshot_has_alias)

    admitted: list[dict[str, object]] = []
    cleared_missing_period_metric_cells = 0
    cleared_duplicate_alias_metric_cells = 0
    for (entity, as_of), group in sorted(
        grouped_rows.items(), key=lambda item: (item[0][1], int(item[0][0]))
    ):
        if (entity, as_of) in fq0_plan_capture_mismatch_keys:
            # Stage 1 and Stage 3 disagree on whether the quarter transition had
            # occurred at this exact PIT cut.  The sparse fundamental snapshot
            # is therefore not a lawful transition state and is excluded as an
            # explicit UNOBSERVED boundary.  The evaluator's predecessor gate
            # prevents any later valid snapshot from bridging across it.
            continue
        security = entity_to_security[entity]
        available_at = conservative_available_at(as_of).isoformat().replace("+00:00", "Z")
        for relative_period in RELATIVE_PERIODS:
            row = group[relative_period]
            raw_period_end = str(row.get("period_end") or "").strip()
            duplicate_alias = (entity, as_of, relative_period) in duplicate_alias_keys
            missing_period_end = not raw_period_end
            quarantine_row = missing_period_end or duplicate_alias
            admitted_period_end = "" if quarantine_row else raw_period_end
            admitted_metrics: dict[str, str] = {}
            for field in metric_fields:
                raw_value = str(row.get(field) or "").strip()
                if quarantine_row:
                    admitted_metrics[field] = ""
                    if raw_value:
                        if duplicate_alias:
                            cleared_duplicate_alias_metric_cells += 1
                        else:
                            cleared_missing_period_metric_cells += 1
                else:
                    admitted_metrics[field] = raw_value
            admitted_row = {
                "security_id": security,
                "source_entity_id": entity,
                "as_of_date": as_of,
                "available_at": available_at,
                "relative_period": relative_period,
                "period_end": admitted_period_end,
                **admitted_metrics,
                "filing_version": str(row.get("filing_version") or "").strip(),
                "value_unit": VALUE_UNIT,
                "source_receipt_sha256": receipt_sha256,
            }
            admitted.append(admitted_row)
            for field in admitted_missing:
                if not str(admitted_row.get(field) or "").strip():
                    admitted_missing[field] += 1

    return admitted, {
        "raw_row_count": len(raw_rows),
        "raw_snapshot_group_count": len(grouped_rows),
        "raw_missing_cell_counts": raw_missing,
        "admitted_missing_cell_counts": admitted_missing,
        "raw_five_quarter_grid_violation_count": bad_grids,
        "duplicate_period_end_snapshot_count": duplicate_period_end_snapshot_count,
        "duplicate_alias_row_count": len(duplicate_alias_keys),
        "fq0_plan_capture_mismatch_snapshot_count": len(fq0_plan_capture_mismatch_keys),
        "fq0_plan_capture_mismatch_rows_quarantined": len(fq0_plan_capture_mismatch_keys) * len(RELATIVE_PERIODS),
        "missing_period_end_rows_quarantined": raw_missing["period_end"],
        "measurement_cells_cleared_due_missing_period_end": cleared_missing_period_metric_cells,
        "measurement_cells_cleared_due_duplicate_period_end": cleared_duplicate_alias_metric_cells,
        "quarantine_law": "FQ0_PLAN_CAPTURE_MISMATCH=>WHOLE_SNAPSHOT_UNOBSERVED; MISSING_PERIOD_END_OR_OLDER_DUPLICATE_PERIOD_ALIAS=>PERIOD_END_AND_ALL_METRICS_UNOBSERVED",
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    raw_path = Path(args.structured_transitions)
    master_path = Path(args.master)
    transition_plan_path = Path(args.transition_plan)
    out_path = Path(args.out)
    receipt_path = raw_path.with_suffix(".receipt.json")
    if not receipt_path.exists():
        raise ShootoutAdmissionError("econphysics_s0_shootout_receipt_required")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    _validate_receipt(raw_path, master_path, transition_plan_path, receipt)
    master_rows = _read_csv(master_path)
    transition_plan_rows = _read_csv(transition_plan_path)
    raw_rows = _read_csv(raw_path)
    if len(raw_rows) != int(receipt.get("raw_grid_rows") or -1):
        raise ShootoutAdmissionError("econphysics_s0_shootout_raw_row_count_receipt_mismatch")
    entity_to_security = _master_map(master_rows)
    expected_fq0_by_snapshot, predecessor_period_end_by_snapshot = _transition_plan_maps(
        transition_plan_rows,
        entity_to_security=entity_to_security,
    )
    receipt_sha = _sha256(receipt_path)
    admitted_rows, admission = _admit_rows(
        raw_rows,
        entity_to_security=entity_to_security,
        receipt_sha256=receipt_sha,
        expected_fq0_by_snapshot=expected_fq0_by_snapshot,
    )
    snapshots = build_structured_snapshots(admitted_rows)
    report = evaluate_m0_m1_shootout(
        snapshots,
        minimum_fold_n=args.minimum_fold_n,
        minimum_fold_coverage=args.minimum_fold_coverage,
        predecessor_period_end_by_snapshot=predecessor_period_end_by_snapshot,
    )
    payload = {
        "schema_version": REPORT_SCHEMA,
        "source_corpus": {
            "raw_path": raw_path.as_posix(),
            "raw_sha256": _sha256(raw_path),
            "receipt_path": receipt_path.as_posix(),
            "receipt_sha256": receipt_sha,
            "master_path": master_path.as_posix(),
            "master_sha256": _sha256(master_path),
            "transition_plan_path": transition_plan_path.as_posix(),
            "source_plan_sha256": receipt.get("source_plan_sha256"),
            "transition_count": receipt.get("transition_count"),
            "provider_request_count": receipt.get("provider_request_count"),
            "transport_mode": receipt.get("transport_mode"),
        },
        "admission": {
            **admission,
            "admitted_snapshot_count": len(snapshots),
            "admitted_security_count": len({snapshot.security_id for snapshot in snapshots}),
            "pit_violation_count": 0,
            "imputation_performed": False,
            "market_data_access_performed": False,
            "winner_or_equity_outcome_access_performed": False,
            "w6_access_performed": False,
        },
        "shootout": report,
        "interpretation_contract": {
            "M1_STABLE_EXTRACTION_LIFT": "continuous low-SNR extraction has stable economic-transition lift over M0; proceed to expectation-gap/winner-selection shootout",
            "NO_EXTRACTION_LIFT": "under the frozen persistence semantics M1 does not establish stable extraction lift over M0; do not infer structured-information insufficiency until a fixed low-freedom dynamics-operator diagnostic has tested persistence, mean reversion and inflection node by node",
            "PARTIAL_SUPPORT": "some economic mechanism improves but integrated extraction is not yet stable; inspect target-specific result before winner selection",
            "ECONOMIC_SIGNAL_WITHOUT_WINNER_LIFT": "reserved for the later sealed winner-selection shootout; not adjudicated here",
        },
        "peer_reference_universe": "CONTEMPORANEOUS_S0_FQ0_TRANSITION_SNAPSHOTS_ONLY; NO_SECTOR_REDESIGN",
        "promotion_authority": "NONE",
        "capital_authority": "NONE",
        "financial_alpha_evidence": 0,
    }
    _atomic_json(out_path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structured-transitions", required=True)
    parser.add_argument("--master", required=True)
    parser.add_argument("--transition-plan", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--minimum-fold-n", type=int, default=DEFAULT_MINIMUM_FOLD_N)
    parser.add_argument("--minimum-fold-coverage", type=float, default=DEFAULT_MINIMUM_FOLD_COVERAGE)
    args = parser.parse_args()
    payload = run(args)
    shootout = payload["shootout"]
    print(
        "S0_M0_M1_SHOOTOUT_COMPLETE"
        f"\tSNAPSHOTS={shootout['snapshot_count']}"
        f"\tPAIRS={shootout['adjacent_transition_pair_count']}"
        f"\tSTATUS={shootout['integrated_state_transition_status']}"
        f"\tOUT={args.out}"
    )
    for target_id, target in shootout["targets"].items():
        comparison = target["comparison"]
        print(
            "S0_TARGET"
            f"\tTARGET={target_id}"
            f"\tSTATUS={comparison['status']}"
            f"\tM1_BETTER_FOLDS={comparison['m1_better_fold_count']}"
            f"\tM0_BETTER_FOLDS={comparison['m0_better_fold_count']}"
            f"\tMEDIAN_LIFT_DELTA={comparison['median_lift_delta_m1_minus_m0']}"
        )


if __name__ == "__main__":
    main()
