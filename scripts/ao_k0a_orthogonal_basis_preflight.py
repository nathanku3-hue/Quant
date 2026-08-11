"""AO-K0A immutable W3 basis-status preflight.

This command is intentionally read-only: it prints a content-addressed summary
of the basis-status matrix and never writes a feature store.  Inputs are only
immutable W3 authority/market custody plus the admitted ECONPHYSICS S0 corpus.
No winner/outcome/W6/provider surface is opened.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import date
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

from research.asymmetric_opportunity_v1.orthogonalization import (
    ELIGIBLE_COMPLETE,
    M_MISSING_HISTORY,
    M_OBSERVED,
    M_WARMUP,
    Q_AND_M_MISSING,
    Q_UNOBSERVED,
    assign_basis_status,
    contract_semantics,
)
from research.econphysics_prebreakout_v1 import build_structured_snapshots
import scripts.econphysics_prebreakout_s0_shootout as s0_admission


SCHEMA_VERSION = "ao_k0a_orthogonal_basis_preflight_receipt_v1"
MATRIX_SCHEMA = "ao_k0a_basis_status_matrix_v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _weekly_last_sessions(session_dates: list[str]) -> list[str]:
    by_week: dict[tuple[int, int], str] = {}
    for raw in session_dates:
        parsed = date.fromisoformat(raw)
        iso = parsed.isocalendar()
        key = (iso.year, iso.week)
        by_week[key] = max(raw, by_week.get(key, raw))
    return [by_week[key] for key in sorted(by_week)]


def _load_admitted_s0_state_events(
    *,
    raw_path: Path,
    master_path: Path,
    transition_plan_path: Path,
) -> tuple[dict[str, list[tuple[str, bool]]], dict[str, Any]]:
    receipt_path = raw_path.with_suffix(".receipt.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    s0_admission._validate_receipt(raw_path, master_path, transition_plan_path, receipt)
    master_rows = s0_admission._read_csv(master_path)
    transition_plan_rows = s0_admission._read_csv(transition_plan_path)
    raw_rows = s0_admission._read_csv(raw_path)
    entity_to_security = s0_admission._master_map(master_rows)
    expected_fq0, _ = s0_admission._transition_plan_maps(
        transition_plan_rows,
        entity_to_security=entity_to_security,
    )
    admitted_rows, admission = s0_admission._admit_rows(
        raw_rows,
        entity_to_security=entity_to_security,
        receipt_sha256=_sha256(receipt_path),
        expected_fq0_by_snapshot=expected_fq0,
    )
    snapshots = build_structured_snapshots(admitted_rows)
    admitted_keys = {
        (snapshot.security_id, snapshot.as_of_date.isoformat()) for snapshot in snapshots
    }

    events: dict[str, list[tuple[str, bool]]] = defaultdict(list)
    for row in transition_plan_rows:
        entity = str(row["source_entity_id"]).strip()
        security_id = entity_to_security[entity]
        as_of_date = str(row["as_of_date"]).strip()
        # No bridge: an invalid/quarantined expected transition flips the Q
        # source state to unobserved until a later admitted transition arrives.
        events[security_id].append(
            (as_of_date, (security_id, as_of_date) in admitted_keys)
        )
    for security_id in events:
        events[security_id].sort()

    return dict(events), {
        "raw_path": raw_path.as_posix(),
        "raw_sha256": _sha256(raw_path),
        "receipt_path": receipt_path.as_posix(),
        "receipt_sha256": _sha256(receipt_path),
        "master_path": master_path.as_posix(),
        "master_sha256": _sha256(master_path),
        "transition_plan_path": transition_plan_path.as_posix(),
        "transition_plan_sha256": _sha256(transition_plan_path),
        "admitted_snapshot_count": len(snapshots),
        "admitted_security_count": len({snapshot.security_id for snapshot in snapshots}),
        "quarantined_transition_snapshot_count": int(
            admission["fq0_plan_capture_mismatch_snapshot_count"]
        ),
        "winner_or_equity_outcome_access_performed": receipt.get(
            "winner_or_equity_outcome_access_performed"
        ),
        "w6_access_performed": receipt.get("w6_access_performed"),
        "selection_performed": receipt.get("selection_performed"),
    }


def _q_observed(events: dict[str, list[tuple[str, bool]]], security_id: str, decision_date: str) -> bool:
    state = False
    for as_of_date, observed in events.get(security_id, ()):  # chronological
        if as_of_date > decision_date:
            break
        state = observed
    return state


def build_preflight(args: argparse.Namespace) -> dict[str, Any]:
    w3_root = Path(args.w3_root)
    authority_manifest_path = w3_root / "authority.manifest.json"
    source_manifest_path = w3_root / "source_manifest.json"
    partition_path = w3_root / "session_partition.json"
    authority_manifest = json.loads(authority_manifest_path.read_text(encoding="utf-8"))
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    partition = json.loads(partition_path.read_text(encoding="utf-8"))

    if source_manifest.get("risk_set_spec_id") != "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1":
        raise ValueError("ao_k0a_w3_risk_set_drift")
    if authority_manifest.get("outcome_access_performed") is not False:
        raise ValueError("ao_k0a_w3_outcome_access_already_performed")
    if authority_manifest.get("w6_labels_opened") is not False:
        raise ValueError("ao_k0a_w3_w6_labels_opened")
    if partition.get("outcome_access_performed") is not False or partition.get("w6_labels_opened") is not False:
        raise ValueError("ao_k0a_partition_outcome_firewall_invalid")

    s0_events, s0_receipt = _load_admitted_s0_state_events(
        raw_path=Path(args.s0_raw),
        master_path=Path(args.s0_master),
        transition_plan_path=Path(args.s0_transition_plan),
    )
    if (
        s0_receipt["winner_or_equity_outcome_access_performed"] is not False
        or s0_receipt["w6_access_performed"] is not False
        or s0_receipt["selection_performed"] is not False
    ):
        raise ValueError("ao_k0a_s0_outcome_firewall_invalid")

    pre_w6_sessions = (
        list(partition["feature_warmup"])
        + list(partition["w5_development"])
        + list(partition["post_development_embargo"])
    )
    if set(pre_w6_sessions) & set(partition["w6_lockbox_decisions"]):
        raise ValueError("ao_k0a_pre_w6_partition_overlap")
    decision_dates = _weekly_last_sessions(pre_w6_sessions)
    session_position = {session_date: i for i, session_date in enumerate(pre_w6_sessions)}

    entries = {
        entry["decision_session_date"]: entry
        for entry in authority_manifest["entries"]
    }
    market_parts = {
        part["session_date"]: part for part in source_manifest["market"]["parts"]
    }

    eligible_by_date: dict[str, list[tuple[str, str]]] = {}
    eligible_sets: dict[str, set[tuple[str, str]]] = {}
    for session_date in pre_w6_sessions:
        entry = entries[session_date]
        with gzip.open(Path(entry["authority_path"]), "rt", encoding="utf-8") as handle:
            body = json.load(handle)
        if body.get("outcome_access_performed") is not False:
            raise ValueError(f"ao_k0a_authority_outcome_surface:{session_date}")
        rows = sorted(
            (str(row["security_id"]), str(row["trading_item_id"]))
            for row in body["eligible_rows"]
        )
        if len(rows) != int(entry["eligible_count"]):
            raise ValueError(f"ao_k0a_w3_eligible_count_drift:{session_date}")
        if len(rows) != len(set(rows)):
            raise ValueError(f"ao_k0a_w3_duplicate_listing:{session_date}")
        eligible_by_date[session_date] = rows
        eligible_sets[session_date] = set(rows)

    finite_return_dates: dict[tuple[str, str], set[str]] = defaultdict(set)
    for session_date in pre_w6_sessions:
        part = market_parts[session_date]
        with Path(part["csv_path"]).open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                raw_return = str(row.get("SP_TOTAL_RETURN") or "").strip()
                if not raw_return:
                    continue
                try:
                    float(raw_return)
                except ValueError:
                    continue
                key = (
                    "CIQSEC:" + str(row["SP_CIQ_ID"]).strip(),
                    str(row["SP_TRADING_ITEM_ID"]).strip(),
                )
                # Exact W3 date-local listing only: no alternate-listing bridge.
                if key in eligible_sets[session_date]:
                    finite_return_dates[key].add(session_date)

    matrix_digest = hashlib.sha256()
    status_counts: Counter[str] = Counter()
    q_observed_count = 0
    m_observed_count = 0
    matrix_row_count = 0
    date_summaries: list[dict[str, Any]] = []
    post_warmup_rows = 0
    post_warmup_complete = 0

    for decision_date in decision_dates:
        position = session_position[decision_date]
        if position < 59:
            trailing_window: set[str] | None = None
        else:
            trailing_window = set(pre_w6_sessions[position - 59 : position + 1])

        date_counts: Counter[str] = Counter()
        for security_id, trading_item_id in eligible_by_date[decision_date]:
            q_observed = _q_observed(s0_events, security_id, decision_date)
            if trailing_window is None:
                m_state = M_WARMUP
            else:
                key = (security_id, trading_item_id)
                history_dates = finite_return_dates.get(key, set())
                # Both W3 eligibility and finite exact-listing return custody
                # must be continuous across the 60-session window.
                w3_continuous = all(
                    key in eligible_sets[session_date] for session_date in trailing_window
                )
                m_state = (
                    M_OBSERVED
                    if w3_continuous and trailing_window.issubset(history_dates)
                    else M_MISSING_HISTORY
                )
            status = assign_basis_status(q_observed=q_observed, m_state=m_state)
            canonical_row = {
                "basis_status": status,
                "decision_date": decision_date,
                "security_id": security_id,
                "trading_item_id": trading_item_id,
            }
            matrix_digest.update(_canonical_bytes(canonical_row))
            matrix_digest.update(b"\n")
            matrix_row_count += 1
            status_counts[status] += 1
            date_counts[status] += 1
            q_observed_count += int(q_observed)
            m_observed_count += int(m_state == M_OBSERVED)
            if trailing_window is not None:
                post_warmup_rows += 1
                post_warmup_complete += int(status == ELIGIBLE_COMPLETE)

        date_summaries.append(
            {
                "decision_date": decision_date,
                "w3_eligible_count": len(eligible_by_date[decision_date]),
                "status_counts": dict(sorted(date_counts.items())),
            }
        )

    all_eligible_counts = [int(entry["eligible_count"]) for entry in authority_manifest["entries"]]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "matrix_schema": MATRIX_SCHEMA,
        "status": "FROZEN_SOURCE_PREFLIGHT_NO_EMPIRICAL_RESULT",
        "orthogonalization_contract": contract_semantics(),
        "basis_status_semantics": "SOURCE_OBSERVABILITY_PREFLIGHT_NOT_Q_M_RESULT",
        "q_source_observability_law": (
            "latest planned S0 fundamental transition at/before decision date must be an admitted "
            "snapshot; quarantined planned transitions set Q source state UNOBSERVED until a later "
            "admitted snapshot; no feature-store bridge or missing fill"
        ),
        "m_observability_law": (
            "exact W3 security+trading-item must have 60 continuous pre-W6 W3-eligible sessions "
            "with finite SP_TOTAL_RETURN in exact W3 market custody; otherwise M_WARMUP or "
            "M_MISSING_HISTORY; no alternate-listing bridge"
        ),
        "q_numeric_kernel_status": (
            "NOT_REDERIVED_IN_AO_K0A; old Rule100 z-factor artifacts are not used to define "
            "observability or denominator boundaries"
        ),
        "w3": {
            "risk_set_spec_id": source_manifest["risk_set_spec_id"],
            "authority_manifest_path": authority_manifest_path.as_posix(),
            "authority_manifest_sha256": _sha256(authority_manifest_path),
            "source_manifest_path": source_manifest_path.as_posix(),
            "source_manifest_sha256": _sha256(source_manifest_path),
            "session_partition_path": partition_path.as_posix(),
            "session_partition_sha256": _sha256(partition_path),
            "all_session_count": len(all_eligible_counts),
            "all_session_mean_eligible_count": sum(all_eligible_counts) / len(all_eligible_counts),
            "all_session_min_eligible_count": min(all_eligible_counts),
            "all_session_max_eligible_count": max(all_eligible_counts),
        },
        "s0": s0_receipt,
        "pre_w6": {
            "session_count": len(pre_w6_sessions),
            "weekly_decision_count": len(decision_dates),
            "first_weekly_decision": decision_dates[0],
            "last_weekly_decision": decision_dates[-1],
            "w6_dates_consumed": 0,
        },
        "matrix": {
            "row_count": matrix_row_count,
            "sha256": matrix_digest.hexdigest(),
            "status_counts": dict(sorted(status_counts.items())),
            "q_source_observed_rate_all_rows": q_observed_count / matrix_row_count,
            "m_observed_rate_all_rows": m_observed_count / matrix_row_count,
            "complete_rate_post_m_warmup": (
                post_warmup_complete / post_warmup_rows if post_warmup_rows else None
            ),
            "coverage_pass_fail_gate": "ABSENT_BY_CONTRACT",
            "rows_removed_for_missingness": 0,
        },
        "date_summaries": date_summaries,
        "forbidden_actions": {
            "winner_or_future_outcome_read": False,
            "w6_read": False,
            "new_provider_request": False,
            "security_level_return_imputation": False,
            "complete_case_denominator": False,
            "observed_subset_renormalization": False,
            "portfolio_optimization": False,
        },
    }
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--w3-root",
        default="data/prebreakout/compiled/w3_real_authority_20250324_20260807",
    )
    parser.add_argument(
        "--s0-raw",
        default="data/prebreakout/raw/econphysics_s0_structured_v1/structured_transitions.csv",
    )
    parser.add_argument(
        "--s0-master",
        default="data/prebreakout/compiled/econphysics_s0_request_20260810/s0_ciqsec_company_master.csv",
    )
    parser.add_argument(
        "--s0-transition-plan",
        default="data/prebreakout/compiled/econphysics_s0_request_20260810/s0_period_change_plan.csv",
    )
    return parser


def main() -> int:
    payload = build_preflight(_parser().parse_args())
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
