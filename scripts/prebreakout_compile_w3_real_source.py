#!/usr/bin/env python3
"""Compile landed PREBREAKOUT Capital IQ custody into real W3 authority.

This is a local deterministic compiler only.  It performs no provider access,
outcome access, trial-ledger mutation, W6 label read, broker order, or capital
action.  Output is restartable by date-index range and written atomically.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.prebreakout_discovery_v1.breakout import algorithmic_breakout_events
from research.prebreakout_discovery_v1.preregistration import CONTRACT_SHA256 as W2_CONTRACT_SHA256
from research.prebreakout_pit_v1.authority import (
    PrebreakoutPITAuthority,
    build_b_minus_one_eligibility_proof,
    build_prebreakout_pit_authority,
    verify_prebreakout_pit_authority,
)
from research.prebreakout_pit_v1.real_source import (
    LIFECYCLE_STATE_RECEIPT_SCHEMA,
    REAL_SOURCE_COMPILER_ID,
    LifecycleState,
    apply_lifecycle_transition,
    build_lifecycle_transitions,
    candidate_rows_from_market,
    canonical_json_bytes,
    canonical_sha256,
    collect_entity_tickers,
    corporate_action_rows_for_candidates,
    freeze_session_partition,
    lifecycle_state_receipt_body,
    load_lifecycle_rows,
    normalized_lifecycle_receipt_binding,
    normalized_market_receipt_binding,
    sha256_file,
    source_authority_for_session,
    verify_and_build_custody_manifest,
)


DEFAULT_MARKET_DIRS = (
    Path("data/prebreakout/raw/historical_corpus_20250324_20260807"),
    Path("data/prebreakout/raw/historical_corpus_20250401_20260807"),
)
DEFAULT_LIFECYCLE_DIR = Path("data/prebreakout/raw/key_developments_lifecycle_20250324_20260807")
DEFAULT_OUTPUT_DIR = Path("data/prebreakout/compiled/w3_real_authority_20250324_20260807")
AUTHORITY_MANIFEST_SCHEMA = "prebreakout_w3_authority_bundle_manifest_v1"
SMOKE_PROOF_BUNDLE_SCHEMA = "prebreakout_w3_mu_sndk_bminus1_proof_bundle_v1"
CLASSIFICATION_SUMMARY_SCHEMA = "prebreakout_w3_lifecycle_classification_summary_v1"

SMOKE_IDENTITIES = (
    {
        "case_prefix": "MU",
        "display_symbol": "MU",
        "security_id": "CIQSEC:IQ289030",
        "ciq_id": "IQ289030",
        "trading_item_id": "2630498",
    },
    {
        "case_prefix": "SNDK",
        "display_symbol": "SNDK",
        "security_id": "CIQSEC:IQ1860586153",
        "ciq_id": "IQ1860586153",
        "trading_item_id": "1929119896",
    },
)


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".tmp.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _atomic_json(path: Path, value: Any) -> str:
    payload = canonical_json_bytes(value)
    _atomic_bytes(path, payload)
    return hashlib.sha256(payload).hexdigest()


def _atomic_gzip_json(path: Path, value: Any) -> str:
    payload = canonical_json_bytes(value)
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    _atomic_bytes(path, compressed)
    return hashlib.sha256(compressed).hexdigest()


def _load_gzip_json(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def _packet_from_mapping(raw: Mapping[str, Any]) -> PrebreakoutPITAuthority:
    body = dict(raw)
    sealed = str(body.pop("packet_sha256"))
    packet = PrebreakoutPITAuthority(body=body, packet_sha256=sealed)
    verify_prebreakout_pit_authority(packet)
    return packet


def _as_of_from_candidates(candidates: list[dict[str, Any]]) -> datetime:
    values = {str(row["available_at"]) for row in candidates}
    if len(values) != 1:
        raise ValueError("prebreakout_w3_real_candidate_asof_not_unique")
    return datetime.fromisoformat(next(iter(values)).replace("Z", "+00:00"))


def _classification_summary(transitions: Mapping[str, list[Any]]) -> dict[str, Any]:
    flat = [transition for values in transitions.values() for transition in values]
    transition_kind = Counter(value.transition_kind for value in flat)
    state_event_type = Counter(value.state_event_type for value in flat)
    role_resolution = Counter(value.role_resolution for value in flat)
    raw_event_type = Counter(value.raw_event_type for value in flat)
    body = {
        "schema_version": CLASSIFICATION_SUMMARY_SCHEMA,
        "compiler_id": REAL_SOURCE_COMPILER_ID,
        "w2_contract_sha256": W2_CONTRACT_SHA256,
        "transition_count": len(flat),
        "affected_entity_count": len({value.entity_id for value in flat}),
        "activation_session_count": len(transitions),
        "transition_kind_counts": dict(sorted(transition_kind.items())),
        "state_event_type_counts": dict(sorted(state_event_type.items())),
        "role_resolution_counts": dict(sorted(role_resolution.items())),
        "raw_event_type_counts": dict(sorted(raw_event_type.items())),
        "ambiguous_mna_transition_count": sum(
            count for key, count in state_event_type.items() if "ROLE_UNRESOLVED" in key
        ),
        "same_day_event_use": False,
        "pre_corpus_event_override_used": False,
        "ticker_identity_fallback_used": False,
        "outcome_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    return {**body, "summary_sha256": canonical_sha256(body)}


def _compile_selected_dates(
    *,
    custody: Mapping[str, Any],
    output_dir: Path,
    start_index: int,
    end_index: int,
    compiler_sha256: str,
) -> None:
    sessions = list(custody["session_spine"])
    if start_index < 0 or end_index >= len(sessions) or start_index > end_index:
        raise ValueError("prebreakout_w3_compile_index_range_invalid")

    market_parts = {str(part["session_date"]): dict(part) for part in custody["market"]["parts"]}
    entity_tickers = collect_entity_tickers(custody["market"]["parts"])
    lifecycle_rows = load_lifecycle_rows(custody["lifecycle"]["parts"])
    transitions = build_lifecycle_transitions(
        lifecycle_rows=lifecycle_rows,
        entity_tickers=entity_tickers,
        session_spine=sessions,
    )
    _atomic_json(output_dir / "lifecycle_classification_summary.json", _classification_summary(transitions))

    lifecycle_observed_start = min(row["EVENT_DATE"] for row in lifecycle_rows)
    lifecycle_retrieved_at = str(custody["lifecycle"]["max_retrieved_at"])
    states: dict[str, LifecycleState] = {}

    for index, session in enumerate(sessions):
        applied = transitions.get(session, [])
        for transition in applied:
            prior = states.get(transition.entity_id, LifecycleState())
            next_state = apply_lifecycle_transition(prior, transition)
            if next_state == LifecycleState():
                states.pop(transition.entity_id, None)
            else:
                states[transition.entity_id] = next_state

        if index < start_index or index > end_index:
            continue

        part = market_parts[session]
        market_binding = normalized_market_receipt_binding(
            market_part=part,
            compiler_sha256=compiler_sha256,
        )
        candidates = candidate_rows_from_market(
            part["csv_path"],
            market_receipt_sha256=market_binding["raw_receipt_sha256"],
        )
        as_of = _as_of_from_candidates(candidates)

        lifecycle_receipt_body = lifecycle_state_receipt_body(
            decision_session_date=session,
            custody_manifest_sha256=str(custody["manifest_sha256"]),
            active_states=states,
            applied_transitions=applied,
            compiler_sha256=compiler_sha256,
            raw_lifecycle_retrieved_at=lifecycle_retrieved_at,
        )
        lifecycle_receipt_path = output_dir / "receipts" / f"lifecycle_state_{session.replace('-', '')}.receipt.json"
        lifecycle_receipt_sha256 = _atomic_json(lifecycle_receipt_path, lifecycle_receipt_body)
        observed_end = (date.fromisoformat(session) - timedelta(days=1)).isoformat()
        lifecycle_binding = normalized_lifecycle_receipt_binding(
            receipt_path=lifecycle_receipt_path,
            receipt_sha256=lifecycle_receipt_sha256,
            observed_range_start=lifecycle_observed_start,
            observed_range_end=observed_end,
            compiler_sha256=compiler_sha256,
            raw_lifecycle_retrieved_at=lifecycle_retrieved_at,
        )
        actions = corporate_action_rows_for_candidates(
            candidates,
            states=states,
            lifecycle_receipt_sha256=lifecycle_receipt_sha256,
            as_of=as_of.isoformat().replace("+00:00", "Z"),
        )
        source_receipts = [market_binding, lifecycle_binding]
        source_authority = source_authority_for_session(
            decision_session_date=session,
            source_receipt_sha256s=[row["raw_receipt_sha256"] for row in source_receipts],
        )
        packet = build_prebreakout_pit_authority(
            as_of=as_of,
            decision_session_date=session,
            source_authority=source_authority,
            candidate_rows=candidates,
            corporate_action_rows=actions,
            source_receipts=source_receipts,
            fixture=False,
        )
        authority_path = output_dir / "authority" / f"date_{session.replace('-', '')}.json.gz"
        compressed_sha = _atomic_gzip_json(authority_path, packet.as_dict())
        marker = {
            "schema_version": "prebreakout_w3_authority_date_compile_receipt_v1",
            "decision_session_date": session,
            "source_custody_manifest_sha256": custody["manifest_sha256"],
            "market_csv_sha256": part["csv_sha256"],
            "market_receipt_sha256": market_binding["raw_receipt_sha256"],
            "lifecycle_state_receipt_sha256": lifecycle_receipt_sha256,
            "authority_packet_sha256": packet.packet_sha256,
            "authority_file_sha256": compressed_sha,
            "candidate_count": int(packet.body["candidate_count"]),
            "eligible_count": int(packet.body["eligible_count"]),
            "exclusion_count": int(packet.body["exclusion_count"]),
            "w6_labels_opened": False,
            "outcome_access_performed": False,
            "financial_alpha_evidence": 0,
            "capital_authority": "NONE",
        }
        _atomic_json(output_dir / "date_receipts" / f"date_{session.replace('-', '')}.compile.json", marker)
        if (index - start_index) % 20 == 0 or index == end_index:
            print(
                json.dumps(
                    {
                        "compiled_index": index,
                        "session": session,
                        "candidate_count": marker["candidate_count"],
                        "eligible_count": marker["eligible_count"],
                        "exclusion_count": marker["exclusion_count"],
                        "nonclear_entity_state_count": lifecycle_receipt_body["nonclear_entity_state_count"],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )


def _load_listing_closes(custody: Mapping[str, Any], *, ciq_id: str, trading_item_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for part in custody["market"]["parts"]:
        path = Path(str(part["csv_path"]))
        import csv

        with path.open(encoding="utf-8", newline="") as handle:
            for raw in csv.DictReader(handle):
                if raw.get("SP_CIQ_ID") == ciq_id and raw.get("SP_TRADING_ITEM_ID") == trading_item_id:
                    rows.append(
                        {
                            "security_id": "CIQSEC:" + ciq_id,
                            "trading_item_id": trading_item_id,
                            "session_date": str(raw["MEMBERSHIP_AS_OF_DATE"]),
                            "close": float(raw["SP_PRICE_CLOSE"]),
                        }
                    )
    rows.sort(key=lambda row: row["session_date"])
    return rows


def _finalize(custody: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    sessions = list(custody["session_spine"])
    entries: list[dict[str, Any]] = []
    for session in sessions:
        date_key = session.replace("-", "")
        authority_path = output_dir / "authority" / f"date_{date_key}.json.gz"
        marker_path = output_dir / "date_receipts" / f"date_{date_key}.compile.json"
        lifecycle_receipt_path = output_dir / "receipts" / f"lifecycle_state_{date_key}.receipt.json"
        if not authority_path.is_file() or not marker_path.is_file() or not lifecycle_receipt_path.is_file():
            raise FileNotFoundError(f"prebreakout_w3_authority_date_missing:{session}")
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if marker["authority_file_sha256"] != sha256_file(authority_path):
            raise ValueError("prebreakout_w3_authority_file_hash_mismatch")
        if marker["lifecycle_state_receipt_sha256"] != sha256_file(lifecycle_receipt_path):
            raise ValueError("prebreakout_w3_lifecycle_receipt_hash_mismatch")
        packet = _packet_from_mapping(_load_gzip_json(authority_path))
        if packet.packet_sha256 != marker["authority_packet_sha256"]:
            raise ValueError("prebreakout_w3_authority_packet_marker_mismatch")
        entries.append(
            {
                "decision_session_date": session,
                "authority_path": authority_path.as_posix(),
                "authority_file_sha256": marker["authority_file_sha256"],
                "authority_packet_sha256": packet.packet_sha256,
                "lifecycle_state_receipt_sha256": marker["lifecycle_state_receipt_sha256"],
                "candidate_count": marker["candidate_count"],
                "eligible_count": marker["eligible_count"],
                "exclusion_count": marker["exclusion_count"],
            }
        )

    packet_binding = [
        {"decision_session_date": row["decision_session_date"], "authority_packet_sha256": row["authority_packet_sha256"]}
        for row in entries
    ]
    receipt_binding = [
        {
            "decision_session_date": row["decision_session_date"],
            "lifecycle_state_receipt_sha256": row["lifecycle_state_receipt_sha256"],
        }
        for row in entries
    ]
    body = {
        "schema_version": AUTHORITY_MANIFEST_SCHEMA,
        "compiler_id": REAL_SOURCE_COMPILER_ID,
        "family_id": "PREBREAKOUT_DISCOVERY_v1",
        "w2_contract_sha256": W2_CONTRACT_SHA256,
        "source_custody_manifest_sha256": custody["manifest_sha256"],
        "session_partition_sha256": custody["session_partition_sha256"],
        "session_count": len(entries),
        "authority_bundle_sha256": canonical_sha256(packet_binding),
        "lifecycle_state_receipt_bundle_sha256": canonical_sha256(receipt_binding),
        "market_payload_sha256": canonical_sha256(
            [
                {"session_date": part["session_date"], "csv_sha256": part["csv_sha256"]}
                for part in custody["market"]["parts"]
            ]
        ),
        "lifecycle_payload_sha256": canonical_sha256(
            [{"csv_path": part["csv_path"], "csv_sha256": part["csv_sha256"]} for part in custody["lifecycle"]["parts"]]
        ),
        "entries": entries,
        "current_survivor_back_projection_used": False,
        "current_primary_back_projection_used": False,
        "alternate_listing_fallback_used": False,
        "ticker_identity_fallback_used": False,
        "w6_labels_opened": False,
        "outcome_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    manifest = {**body, "manifest_sha256": canonical_sha256(body)}
    _atomic_json(output_dir / "authority.manifest.json", manifest)

    proofs: list[dict[str, Any]] = []
    smoke_summary: dict[str, Any] = {}
    for identity in SMOKE_IDENTITIES:
        closes = _load_listing_closes(
            custody,
            ciq_id=str(identity["ciq_id"]),
            trading_item_id=str(identity["trading_item_id"]),
        )
        if len(closes) != len(sessions):
            raise ValueError("prebreakout_w3_smoke_listing_session_count_invalid")
        events = algorithmic_breakout_events(closes)
        status_counts: Counter[str] = Counter()
        for episode_index, event in enumerate(events, start=1):
            b_index = sessions.index(event.session_date)
            if b_index < 1:
                raise ValueError("prebreakout_w3_smoke_breakout_without_bminus1")
            b1 = sessions[b_index - 1]
            authority_path = output_dir / "authority" / f"date_{b1.replace('-', '')}.json.gz"
            packet = _packet_from_mapping(_load_gzip_json(authority_path))
            proof = build_b_minus_one_eligibility_proof(
                authority=packet,
                case_id=f"{identity['case_prefix']}_EPISODE_{episode_index:02d}",
                display_symbol=str(identity["display_symbol"]),
                breakout_contract_sha256=W2_CONTRACT_SHA256,
                breakout_session=event.session_date,
                b_minus_1_session=b1,
                expected_security_id=str(identity["security_id"]),
                expected_trading_item_id=str(identity["trading_item_id"]),
            )
            proof_dict = proof.as_dict()
            proofs.append(proof_dict)
            status_counts[str(proof_dict["status"])] += 1
        smoke_summary[str(identity["display_symbol"])] = {
            "exact_listing_session_count": len(closes),
            "accepted_w2_breakout_episode_count": len(events),
            "pit_proof_status_counts": dict(sorted(status_counts.items())),
        }

    proof_body = {
        "schema_version": SMOKE_PROOF_BUNDLE_SCHEMA,
        "family_id": "PREBREAKOUT_DISCOVERY_v1",
        "w2_contract_sha256": W2_CONTRACT_SHA256,
        "authority_bundle_sha256": manifest["authority_bundle_sha256"],
        "statistical_weight": 0,
        "promotion_denominator_weight": 0,
        "display_symbol_used_for_logic": False,
        "summary": smoke_summary,
        "proofs": proofs,
        "outcome_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    proof_bundle = {**proof_body, "proof_bundle_sha256": canonical_sha256(proof_body)}
    _atomic_json(output_dir / "mu_sndk_bminus1_proofs.json", proof_bundle)
    return {"authority_manifest": manifest, "smoke_proofs": proof_bundle}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int, default=345)
    parser.add_argument("--no-finalize", action="store_true")
    args = parser.parse_args()

    compiler_module = Path(__file__).resolve().parents[1] / "research" / "prebreakout_pit_v1" / "real_source.py"
    compiler_sha256 = sha256_file(compiler_module)
    custody = verify_and_build_custody_manifest(
        market_dirs=DEFAULT_MARKET_DIRS,
        lifecycle_dir=DEFAULT_LIFECYCLE_DIR,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _atomic_json(args.output_dir / "source_manifest.json", custody)
    partition = freeze_session_partition(custody["session_spine"])
    _atomic_json(args.output_dir / "session_partition.json", partition)

    _compile_selected_dates(
        custody=custody,
        output_dir=args.output_dir,
        start_index=args.start_index,
        end_index=args.end_index,
        compiler_sha256=compiler_sha256,
    )

    result: dict[str, Any] = {
        "source_manifest_sha256": custody["manifest_sha256"],
        "session_partition_sha256": partition["partition_sha256"],
        "compiled_range": [args.start_index, args.end_index],
        "trial_open_appended": False,
        "w6_labels_opened": False,
        "outcome_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    if not args.no_finalize:
        finalized = _finalize(custody, args.output_dir)
        result.update(
            {
                "authority_manifest_sha256": finalized["authority_manifest"]["manifest_sha256"],
                "authority_bundle_sha256": finalized["authority_manifest"]["authority_bundle_sha256"],
                "smoke_proof_bundle_sha256": finalized["smoke_proofs"]["proof_bundle_sha256"],
                "smoke_summary": finalized["smoke_proofs"]["summary"],
            }
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
