"""Run the narrow ECONPHYSICS S0 economic-dynamics diagnostic on the real PIT corpus.

This runner reuses the exact S0 structured-corpus admission law from the M0/M1
shootout.  It performs no provider call and has no market, winner, W6, selector,
or capital surface.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.econphysics_prebreakout_v1.contracts import build_structured_snapshots
from research.econphysics_prebreakout_v1.dynamics_diagnostic import (
    DYNAMICS_DIAGNOSTIC_SCHEMA,
    evaluate_economic_dynamics_diagnostic,
)
from research.econphysics_prebreakout_v1.shootout_evaluator import (
    DEFAULT_MINIMUM_FOLD_COVERAGE,
    DEFAULT_MINIMUM_FOLD_N,
)
from scripts.econphysics_prebreakout_s0_shootout import (
    _admit_rows,
    _atomic_json,
    _master_map,
    _read_csv,
    _sha256,
    _transition_plan_maps,
    _validate_receipt,
)


REPORT_SCHEMA = "econphysics_prebreakout_s0_economic_dynamics_real_corpus_report_v2"


def run(args: argparse.Namespace) -> dict[str, Any]:
    raw_path = Path(args.structured_transitions)
    master_path = Path(args.master)
    transition_plan_path = Path(args.transition_plan)
    out_path = Path(args.out)
    receipt_path = raw_path.with_suffix(".receipt.json")
    if not receipt_path.exists():
        raise ValueError("econphysics_dynamics_diagnostic_receipt_required")

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    _validate_receipt(raw_path, master_path, transition_plan_path, receipt)
    master_rows = _read_csv(master_path)
    transition_plan_rows = _read_csv(transition_plan_path)
    raw_rows = _read_csv(raw_path)
    if len(raw_rows) != int(receipt.get("raw_grid_rows") or -1):
        raise ValueError("econphysics_dynamics_diagnostic_raw_row_count_receipt_mismatch")

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
    diagnostic = evaluate_economic_dynamics_diagnostic(
        snapshots,
        predecessor_period_end_by_snapshot=predecessor_period_end_by_snapshot,
        minimum_fold_n=args.minimum_fold_n,
        minimum_fold_coverage=args.minimum_fold_coverage,
    )
    payload = {
        "schema_version": REPORT_SCHEMA,
        "diagnostic_schema_version": DYNAMICS_DIAGNOSTIC_SCHEMA,
        "source_corpus": {
            "raw_path": raw_path.as_posix(),
            "raw_sha256": _sha256(raw_path),
            "receipt_path": receipt_path.as_posix(),
            "receipt_sha256": receipt_sha,
            "master_path": master_path.as_posix(),
            "master_sha256": _sha256(master_path),
            "transition_plan_path": transition_plan_path.as_posix(),
            "transition_plan_sha256": _sha256(transition_plan_path),
            "source_plan_sha256": receipt.get("source_plan_sha256"),
            "transport_mode": receipt.get("transport_mode"),
            "provider_request_count_already_in_custody": receipt.get("provider_request_count"),
            "provider_access_performed_by_this_diagnostic": False,
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
        "diagnostic": diagnostic,
        "routing_contract": {
            "DYNAMICS_SIGNAL_PRESENT": "retain this node for a separately frozen causal continuation; do not classify the node as observable-insufficient",
            "NO_LOW_FREEDOM_DYNAMICS_SIGNAL": "only after primitive persistence/reversal/level/delta2 plus fixed M0/M1 representation-conditioned reversal all fail with adequate fold coverage may this node route toward observable insufficiency",
            "UNOBSERVED": "coverage is insufficient for the low-freedom operator family; do not infer observable insufficiency",
            "NODE_SPECIFIC_DYNAMICS_SURVIVORS": "retain surviving nodes independently; an integrated failure may not discard the whole structured surface",
            "OBSERVABLE_INSUFFICIENCY_CANDIDATE": "all core nodes had adequate coverage and no fixed low-freedom operator survived; upstream causal observables may be warranted",
        },
        "expectation_layer_boundary": {
            "upstream_causal_observables": [
                "orders_backlog",
                "pricing_mix",
                "utilization_capacity",
                "channel_inventory",
            ],
            "downstream_expectation_observables": [
                "revisions",
                "guidance",
                "consensus",
            ],
            "mixed_in_this_diagnostic": False,
        },
        "diagnostic_only": True,
        "financial_alpha_evidence": 0,
        "promotion_authority": "NONE",
        "capital_authority": "NONE",
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
    diagnostic = payload["diagnostic"]
    print(
        "S0_DYNAMICS_DIAGNOSTIC_COMPLETE"
        f"\tPAIRS={diagnostic['adjacent_transition_pair_count']}"
        f"\tROUTING={diagnostic['routing']}"
        f"\tSURVIVORS={','.join(diagnostic['surviving_target_ids']) or 'NONE'}"
        f"\tOUT={args.out}"
    )
    for target_id, target in diagnostic["targets"].items():
        print(
            "S0_DYNAMICS_TARGET"
            f"\tTARGET={target_id}"
            f"\tROUTING={target['node_routing']}"
            f"\tOPERATORS={','.join(target['surviving_operator_ids']) or 'NONE'}"
            f"\tREVERSAL={target['lag1_transition']['overall_development']['reversal_rate']}"
        )


if __name__ == "__main__":
    main()
