"""Freeze the ECONPHYSICS S0 structured-fundamental request from W3 authority.

This script is local-only request preparation.  It never opens a provider,
market series, equity outcome, or W6 label surface.  A separate explicit
capture authorization is required before the emitted ProductQuery commands may
be executed.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.aov0.contracts import normalize_security_id
from research.econphysics_prebreakout_v1.contracts import (
    FILING_VERSION,
    REQUEST_METRICS,
    VALUE_UNIT,
)


REQUEST_SCHEMA = "econphysics_prebreakout_s0_structured_request_v1"
TRANSITION_PLAN_SCHEMA = "econphysics_prebreakout_s0_period_change_plan_v1"
DEFAULT_W3_ROOT = Path("data/prebreakout/compiled/w3_real_authority_20250324_20260807")
DEFAULT_OUT_DIR = Path("data/prebreakout/compiled/econphysics_s0_request_20260810")
DEFAULT_MANIFEST = Path("docs/architecture/econphysics_prebreakout_s0_structured_request_v1.json")
CAPTURE_SCRIPT = Path("scripts/aov0_capture_ciq_historical_pit_productquery.py")
CAUSAL_CONTRACT = Path("docs/architecture/econphysics_prebreakout_v1_causal_contract.md")
OBSERVABLE_MANIFEST = Path("docs/architecture/econphysics_prebreakout_v1_pit_observable_manifest.json")


class S0RequestError(ValueError):
    """Fail-closed request-freeze error."""


def compile_w3_request_rows(w3_root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    partition_path = w3_root / "session_partition.json"
    partition = json.loads(partition_path.read_text(encoding="utf-8"))
    if partition.get("family_id") != "PREBREAKOUT_DISCOVERY_v1":
        raise S0RequestError("econphysics_s0_w3_family_invalid")
    if bool(partition.get("w6_labels_opened")) or bool(partition.get("development_labels_overlap_w6_lockbox")):
        raise S0RequestError("econphysics_s0_w6_custody_not_sealed")
    pre_w6 = [
        *partition.get("feature_warmup", []),
        *partition.get("w5_development", []),
        *partition.get("post_development_embargo", []),
    ]
    if not pre_w6 or pre_w6 != sorted(set(pre_w6)):
        raise S0RequestError("econphysics_s0_pre_w6_sessions_invalid")
    forbidden = set(partition.get("w6_lockbox_decisions", [])) | set(partition.get("lockbox_label_maturity_tail", []))
    if set(pre_w6) & forbidden:
        raise S0RequestError("econphysics_s0_pre_w6_spine_overlaps_forbidden_dates")
    first_forbidden = min(forbidden) if forbidden else None
    if first_forbidden is not None and max(pre_w6) >= first_forbidden:
        raise S0RequestError("econphysics_s0_pre_w6_spine_not_strictly_pre_w6")

    weekly_dates = _weekly_last_sessions(pre_w6)
    weekly_set = set(weekly_dates)
    identity: dict[tuple[str, str], dict[str, Any]] = {}
    security_to_entity: dict[str, str] = {}
    entity_to_security: dict[str, str] = {}
    probe_rows: list[dict[str, str]] = []
    eligible_row_count = 0

    for session in pre_w6:
        packet_path = w3_root / "authority" / f"date_{session.replace('-', '')}.json.gz"
        if not packet_path.exists():
            raise S0RequestError(f"econphysics_s0_w3_authority_packet_missing:{session}")
        with gzip.open(packet_path, "rt", encoding="utf-8") as handle:
            packet = json.load(handle)
        if packet.get("decision_session_date") != session or packet.get("financial_alpha_evidence") != 0:
            raise S0RequestError(f"econphysics_s0_w3_authority_packet_invalid:{session}")
        source = packet.get("source_authority") or {}
        if (
            not source.get("historical_as_of_mechanically_bound")
            or source.get("ticker_fallback_used")
            or source.get("permno_fallback_used")
            or source.get("company_entity_fallback_used")
            or source.get("current_primary_back_projection_used")
            or source.get("current_survivor_back_projection_used")
        ):
            raise S0RequestError(f"econphysics_s0_w3_source_authority_invalid:{session}")
        for row in packet.get("eligible_rows") or []:
            security_id = normalize_security_id(str(row.get("security_id") or ""))
            entity = str(row.get("company_id") or "").strip()
            if not entity.isdigit():
                raise S0RequestError("econphysics_s0_company_entity_invalid")
            prior_entity = security_to_entity.setdefault(security_id, entity)
            prior_security = entity_to_security.setdefault(entity, security_id)
            if prior_entity != entity or prior_security != security_id:
                raise S0RequestError("econphysics_s0_security_entity_mapping_not_one_to_one")
            key = (security_id, entity)
            state = identity.setdefault(
                key,
                {"first": session, "last": session, "count": 0},
            )
            state["last"] = session
            state["count"] += 1
            eligible_row_count += 1
            if session in weekly_set:
                probe_rows.append(
                    {
                        "source_entity_id": entity,
                        "security_id": security_id,
                        "as_of_date": session,
                    }
                )

    master_rows = [
        {
            "SP_ENTITY_ID": entity,
            "security_id": security_id,
            "first_w3_eligible_as_of": str(state["first"]),
            "last_w3_eligible_as_of": str(state["last"]),
            "w3_eligible_session_count": str(state["count"]),
        }
        for (security_id, entity), state in identity.items()
    ]
    master_rows.sort(key=lambda row: int(row["SP_ENTITY_ID"]))
    probe_rows.sort(key=lambda row: (row["as_of_date"], int(row["source_entity_id"])))
    if len(probe_rows) != len({(row["source_entity_id"], row["as_of_date"]) for row in probe_rows}):
        raise S0RequestError("econphysics_s0_period_probe_plan_duplicate_pair")
    spine_rows = [{"as_of_date": session} for session in weekly_dates]
    metadata = {
        "pre_w6_session_count": len(pre_w6),
        "pre_w6_first_session": pre_w6[0],
        "pre_w6_last_session": pre_w6[-1],
        "weekly_as_of_count": len(weekly_dates),
        "weekly_as_of_first": weekly_dates[0],
        "weekly_as_of_last": weekly_dates[-1],
        "master_pair_count": len(master_rows),
        "eligible_row_count": eligible_row_count,
        "period_probe_pair_count": len(probe_rows),
        "w6_decision_count_excluded": len(partition.get("w6_lockbox_decisions", [])),
        "maturity_tail_count_excluded": len(partition.get("lockbox_label_maturity_tail", [])),
        "partition_sha256": _sha256(partition_path),
        "partition_declared_sha256": str(partition.get("partition_sha256") or ""),
    }
    return master_rows, spine_rows, probe_rows, metadata


def compile_period_change_plan(period_rows: Sequence[Mapping[str, Any]], master_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    entity_to_security = {
        str(row["SP_ENTITY_ID"]).strip(): normalize_security_id(str(row["security_id"]))
        for row in master_rows
    }
    grouped: dict[str, list[tuple[date, date | None]]] = {}
    seen: set[tuple[str, date]] = set()
    for row in period_rows:
        entity = str(row.get("source_entity_id") or "").strip()
        if entity not in entity_to_security:
            raise S0RequestError(f"econphysics_s0_period_matrix_entity_outside_master:{entity}")
        as_of = date.fromisoformat(str(row.get("as_of_date") or ""))
        key = (entity, as_of)
        if key in seen:
            raise S0RequestError("econphysics_s0_period_matrix_duplicate_pair")
        seen.add(key)
        raw_period = str(row.get("fq0_period_end") or "").strip()
        period_end = date.fromisoformat(raw_period) if raw_period else None
        if period_end is not None and period_end > as_of:
            raise S0RequestError("econphysics_s0_period_matrix_future_period_end")
        grouped.setdefault(entity, []).append((as_of, period_end))

    plan: list[dict[str, str]] = []
    for entity, values in grouped.items():
        ordered = sorted(values)
        prior_as_of: date | None = None
        prior_period: date | None = None
        for as_of, period_end in ordered:
            if period_end is None:
                # Missing observations terminate adjacency.  The next observed
                # probe is a new baseline; never bridge across missing PIT data.
                prior_as_of = None
                prior_period = None
                continue
            if prior_period is None or prior_as_of is None:
                prior_as_of = as_of
                prior_period = period_end
                continue
            if period_end < prior_period:
                # A backward FQ0 period is an internally inconsistent provider
                # observation, not an economic transition.  Quarantine it as
                # UNOBSERVED and terminate adjacency exactly like missingness.
                prior_as_of = None
                prior_period = None
                continue
            if period_end > prior_period:
                plan.append(
                    {
                        "source_entity_id": entity,
                        "security_id": entity_to_security[entity],
                        "as_of_date": as_of.isoformat(),
                        "fq0_period_end": period_end.isoformat(),
                        "prior_probe_as_of_date": prior_as_of.isoformat(),
                        "prior_fq0_period_end": prior_period.isoformat(),
                        "transition_reason": "FQ0_PERIOD_CHANGE",
                    }
                )
            prior_as_of = as_of
            prior_period = period_end
    return sorted(plan, key=lambda row: (row["as_of_date"], int(row["source_entity_id"])))


def freeze_request(*, w3_root: Path, out_dir: Path, manifest_path: Path) -> dict[str, Any]:
    master_rows, spine_rows, probe_rows, metadata = compile_w3_request_rows(w3_root)
    master_path = out_dir / "s0_ciqsec_company_master.csv"
    spine_path = out_dir / "s0_pre_w6_weekly_asof_spine.csv"
    probe_path = out_dir / "s0_period_probe_plan.csv"
    for path in (master_path, spine_path, probe_path, manifest_path):
        if path.exists():
            raise FileExistsError(f"econphysics_s0_request_output_exists:{path}")
    _atomic_csv(master_path, master_rows)
    _atomic_csv(spine_path, spine_rows)
    _atomic_csv(probe_path, probe_rows)
    manifest = _request_manifest(
        w3_root=w3_root,
        master_path=master_path,
        spine_path=spine_path,
        probe_path=probe_path,
        metadata=metadata,
    )
    _atomic_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def _request_manifest(
    *,
    w3_root: Path,
    master_path: Path,
    spine_path: Path,
    probe_path: Path,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    period_out = Path("data/prebreakout/raw/econphysics_s0_structured_v1/fq0_period_matrix.csv")
    transition_plan = Path("data/prebreakout/compiled/econphysics_s0_request_20260810/s0_period_change_plan.csv")
    transition_out = Path("data/prebreakout/raw/econphysics_s0_structured_v1/structured_transitions.csv")
    metric_args = [item for metric in REQUEST_METRICS for item in ("--metric", metric)]
    return {
        "schema_version": REQUEST_SCHEMA,
        "family_id": "ECONPHYSICS_PREBREAKOUT_v1",
        "slice_id": "ECONPHYSICS_S0_STRUCTURED_STATE_TRANSITION_PROOF_v1",
        "status": "FROZEN_REQUEST_ONLY_CAPTURE_NOT_EXECUTED",
        "source_authority": {
            "w3_root": w3_root.as_posix(),
            "authority_manifest_sha256": _sha256(w3_root / "authority.manifest.json"),
            "session_partition_sha256": _sha256(w3_root / "session_partition.json"),
            **dict(metadata),
        },
        "frozen_inputs": {
            "ciqsec_company_master": master_path.as_posix(),
            "ciqsec_company_master_sha256": _sha256(master_path),
            "pre_w6_weekly_asof_spine": spine_path.as_posix(),
            "pre_w6_weekly_asof_spine_sha256": _sha256(spine_path),
            "period_probe_plan": probe_path.as_posix(),
            "period_probe_plan_sha256": _sha256(probe_path),
            "causal_contract_sha256": _sha256(CAUSAL_CONTRACT),
            "pit_observable_manifest_sha256": _sha256(OBSERVABLE_MANIFEST),
            "capture_script_sha256": _sha256(CAPTURE_SCRIPT),
        },
        "request": {
            "provider": "S&P Capital IQ Pro authenticated existing web session",
            "provider_function": "SPG",
            "options": "Options:Curr=USD,Mag=Thousands,ConvMethod=R,FilingVer=Original",
            "filing_version": FILING_VERSION,
            "value_unit": VALUE_UNIT,
            "stage_1_period_probe": {
                "metric": "IQ_PERIOD_END",
                "relative_period": "FQ0",
                "plan_mode": "EXACT_W3_ELIGIBLE_ENTITY_DATE_PAIRS",
                "allow_missing_period_end": True,
                "output": period_out.as_posix(),
                "argv_after_python": [
                    CAPTURE_SCRIPT.as_posix(),
                    "--batch-requests", "200",
                    "period-matrix",
                    "--plan", probe_path.as_posix(),
                    "--master", master_path.as_posix(),
                    "--out", period_out.as_posix(),
                    "--allow-missing-period-end",
                ],
            },
            "stage_2_transition_plan": {
                "rule": "CAPTURE_ONLY_ADJACENT_NONMISSING_FQ0_PERIOD_CHANGES; FIRST_OBSERVATION_IS_BASELINE_ONLY; NO_INITIAL_FULL_PULL; NO_BRIDGE_ACROSS_MISSING_PROBES",
                "output": transition_plan.as_posix(),
            },
            "stage_3_sparse_fundamentals": {
                "relative_periods": ["FQ0", "FQ-1", "FQ-2", "FQ-3", "FQ-4"],
                "metrics": list(REQUEST_METRICS),
                "output": transition_out.as_posix(),
                "argv_after_python": [
                    CAPTURE_SCRIPT.as_posix(),
                    "--batch-requests", "200",
                    "transitions",
                    "--plan", transition_plan.as_posix(),
                    "--master", master_path.as_posix(),
                    "--out", transition_out.as_posix(),
                    *metric_args,
                ],
            },
        },
        "admission": {
            "available_at_rule": "CONSERVATIVE_END_OF_REQUESTED_AS_OF_DATE_UTC",
            "ratio_law": "SAME_RELATIVE_PERIOD_AND_PERIOD_END; SAME_USD_THOUSANDS_UNIT; REVENUE_MUST_BE_POSITIVE",
            "operating_margin_formula": "IQ_OPER_INC / IQ_TOTAL_REV",
            "inventory_to_revenue_formula": "IQ_INVENTORY / IQ_TOTAL_REV",
            "capex_semantics": "SUPPLY_CAPITAL_CYCLE_EVIDENCE_ONLY_NOT_CAPACITY_STATE",
            "missingness": "PRESERVE_AS_UNOBSERVED; NO_IMPUTATION",
        },
        "forbidden_surfaces": [
            "MARKET_FEATURES",
            "EQUITY_OUTCOMES",
            "SELECTION_LABELS",
            "W6_DECISIONS",
            "W6_MATURITY_TAIL",
            "VSB_OUTCOMES",
            "A2_OUTCOMES_OR_REQUERY",
            "CRV1_OUTCOMES",
        ],
        "provider_capture_authority": "NONE_UNTIL_EXPLICIT_CAPTURE_GO",
        "successor_empirical_authority": "NONE_UNTIL_PROVIDER_CAPTURE_GO_AND_S0_EVIDENCE_EXISTS",
        "financial_alpha_evidence": 0,
        "promotion_authority": "NONE",
        "capital_authority": "NONE",
    }


def _weekly_last_sessions(sessions: Sequence[str]) -> list[str]:
    by_week: dict[tuple[int, int], str] = {}
    for value in sessions:
        day = date.fromisoformat(value)
        iso = day.isocalendar()
        key = (iso.year, iso.week)
        by_week[key] = max(value, by_week.get(key, value))
    return sorted(by_week.values())


def _csv_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    if not rows:
        raise S0RequestError("econphysics_s0_csv_rows_required")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _atomic_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    _atomic_bytes(path, _csv_bytes(rows))


def _atomic_text(path: Path, text: str) -> None:
    _atomic_bytes(path, text.encode("utf-8"))


def _atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            raise FileExistsError(f"econphysics_s0_request_output_exists:{path}")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _derive_transition_plan_cli(args: argparse.Namespace) -> None:
    matrix_path = Path(args.period_matrix)
    master_path = Path(args.master)
    out = Path(args.out)
    receipt_path = matrix_path.with_suffix(".receipt.json")
    if not receipt_path.exists():
        raise S0RequestError("econphysics_s0_period_matrix_receipt_required")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("raw_object_sha256") != _sha256(matrix_path):
        raise S0RequestError("econphysics_s0_period_matrix_receipt_hash_mismatch")
    if receipt.get("filing_version") != FILING_VERSION or receipt.get("provider_metric") != "IQ_PERIOD_END":
        raise S0RequestError("econphysics_s0_period_matrix_receipt_semantics_invalid")
    rows = compile_period_change_plan(_load_csv(matrix_path), _load_csv(master_path))
    if not rows:
        raise S0RequestError("econphysics_s0_no_period_changes_observed")
    _atomic_csv(out, rows)
    print(f"S0_TRANSITION_PLAN_OK\tROWS={len(rows)}\tSHA256={_sha256(out)}\tPATH={out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    freeze = sub.add_parser("freeze-request")
    freeze.add_argument("--w3-root", default=str(DEFAULT_W3_ROOT))
    freeze.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    freeze.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    derive = sub.add_parser("derive-transition-plan")
    derive.add_argument("--period-matrix", required=True)
    derive.add_argument("--master", required=True)
    derive.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "freeze-request":
        manifest = freeze_request(
            w3_root=Path(args.w3_root),
            out_dir=Path(args.out_dir),
            manifest_path=Path(args.manifest),
        )
        print(
            "S0_REQUEST_FROZEN"
            f"\tMASTER={manifest['source_authority']['master_pair_count']}"
            f"\tWEEKLY_DATES={manifest['source_authority']['weekly_as_of_count']}"
            f"\tPROBE_PAIRS={manifest['source_authority']['period_probe_pair_count']}"
            f"\tMANIFEST={args.manifest}"
        )
    else:
        _derive_transition_plan_cli(args)


if __name__ == "__main__":
    main()
