"""Freeze exact Trial-1 source/code custody without opening Trial #1.

The script consumes the already-compiled real W3 authority and the captured
market corpus. It computes development label and breakout-episode payloads to
content hashes only; no label values or winner summaries are written or
printed. W6 decision sessions and the lockbox label tail are not read into the
pre-charge market table.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping

import duckdb

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from research.prebreakout_discovery_v1 import preregistration as w2
from research.prebreakout_discovery_v1 import trial1_m0
from research.prebreakout_discovery_v1.precharge_custody import (
    PRECHARGE_SCHEMA,
    build_code_bundle_manifest,
    build_trial1_source_manifest,
    compute_development_label_hash,
    compute_episode_anchor_hash,
    create_market_table,
    decision_spine_hash,
    development_market_payload_hash,
    development_w3_bundle_hash,
    source_receipt_bundle_hash,
)
from research.prebreakout_pit_v1.real_source import canonical_sha256, sha256_file


W3_ROOT = Path("data/prebreakout/compiled/w3_real_authority_20250324_20260807")
DEFAULT_OUTPUT = Path("data/prebreakout/compiled/trial1_precharge_20260810")


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return sha256_file(path)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"precharge_json_object_required:{path}")
    return data


def _verify_canonical_manifest(payload: Mapping[str, Any], *, seal_field: str = "manifest_sha256") -> None:
    sealed = str(payload.get(seal_field) or "")
    body = {key: value for key, value in payload.items() if key != seal_field}
    if sealed != canonical_sha256(body):
        raise ValueError(f"precharge_manifest_hash_mismatch:{seal_field}")


def _select_by_dates(rows: list[dict[str, Any]], dates: list[str], *, date_field: str) -> list[dict[str, Any]]:
    index = {str(row[date_field]): row for row in rows}
    if len(index) != len(rows):
        raise ValueError(f"precharge_duplicate_date_field:{date_field}")
    try:
        selected = [index[date_value] for date_value in dates]
    except KeyError as exc:
        raise ValueError(f"precharge_missing_required_date:{date_field}:{exc.args[0]}") from exc
    return selected


def freeze(output_dir: Path) -> dict[str, Any]:
    source = _load_json(W3_ROOT / "source_manifest.json")
    authority = _load_json(W3_ROOT / "authority.manifest.json")
    partition = _load_json(W3_ROOT / "session_partition.json")
    _verify_canonical_manifest(source)
    _verify_canonical_manifest(authority)

    if source.get("w2_contract_sha256") != w2.CONTRACT_SHA256:
        raise ValueError("precharge_w3_source_w2_hash_mismatch")
    if authority.get("w2_contract_sha256") != w2.CONTRACT_SHA256:
        raise ValueError("precharge_w3_authority_w2_hash_mismatch")
    if authority.get("session_count") != 346 or partition.get("total_session_count") != 346:
        raise ValueError("precharge_exact_346_session_corpus_required")
    if source.get("session_partition_sha256") != partition.get("partition_sha256"):
        raise ValueError("precharge_partition_hash_binding_mismatch")
    for field in (
        "current_survivor_back_projection_used",
        "current_primary_back_projection_used",
        "alternate_listing_fallback_used",
        "ticker_identity_fallback_used",
    ):
        if authority.get(field) is not False:
            raise ValueError("precharge_forbidden_w3_fallback:" + field)
    if authority.get("w6_labels_opened") is not False or authority.get("outcome_access_performed") is not False:
        raise ValueError("precharge_w3_authority_label_or_outcome_state_invalid")

    warmup = [str(value) for value in partition["feature_warmup"]]
    development = [str(value) for value in partition["w5_development"]]
    embargo = [str(value) for value in partition["post_development_embargo"]]
    lockbox = [str(value) for value in partition["w6_lockbox_decisions"]]
    label_tail = [str(value) for value in partition["lockbox_label_maturity_tail"]]
    if list(map(len, (warmup, development, embargo, lockbox, label_tail))) != [60, 226, 20, 20, 20]:
        raise ValueError("precharge_partition_counts_invalid")
    if set(warmup + development + embargo) & set(lockbox + label_tail):
        raise ValueError("precharge_development_source_overlaps_w6")

    source_market_parts = list(source["market"]["parts"])
    authority_entries = list(authority["entries"])
    precharge_market_dates = warmup + development + embargo
    precharge_authority_dates = warmup + development
    market_parts = _select_by_dates(source_market_parts, precharge_market_dates, date_field="session_date")
    w3_entries = _select_by_dates(authority_entries, precharge_authority_dates, date_field="decision_session_date")
    dev_entries = _select_by_dates(authority_entries, development, date_field="decision_session_date")
    if len(market_parts) != 306 or len(w3_entries) != 286 or len(dev_entries) != 226:
        raise ValueError("precharge_selected_source_counts_invalid")
    if any(str(part["session_date"]) in set(lockbox + label_tail) for part in market_parts):
        raise ValueError("precharge_w6_market_part_selected")

    for part in market_parts:
        path = Path(str(part["csv_path"]))
        receipt = Path(str(part["receipt_path"]))
        if sha256_file(path) != str(part["csv_sha256"]):
            raise ValueError("precharge_market_csv_hash_drift:" + str(part["session_date"]))
        if sha256_file(receipt) != str(part["receipt_sha256"]):
            raise ValueError("precharge_market_receipt_hash_drift:" + str(part["session_date"]))
    for entry in w3_entries:
        path = Path(str(entry["authority_path"]))
        if sha256_file(path) != str(entry["authority_file_sha256"]):
            raise ValueError("precharge_w3_authority_file_hash_drift:" + str(entry["decision_session_date"]))

    candidate_counts = {
        str(entry["decision_session_date"]): int(entry["candidate_count"])
        for entry in dev_entries
    }

    connection = duckdb.connect(database=":memory:")
    try:
        market_row_count = create_market_table(
            connection,
            csv_paths=[str(part["csv_path"]) for part in market_parts],
            maximum_session_date=embargo[-1],
        )
        label_custody = compute_development_label_hash(
            connection,
            decision_dates=development,
            candidate_counts=candidate_counts,
        )
        episode_custody = compute_episode_anchor_hash(
            connection,
            session_spine=source["session_spine"],
            development_decision_dates=development,
        )
    finally:
        connection.close()

    market_payload_sha256 = development_market_payload_hash(market_parts)
    w3_bundle_sha256 = development_w3_bundle_hash(w3_entries)
    decision_sha256 = decision_spine_hash(development)
    receipts_sha256 = source_receipt_bundle_hash(
        market_parts=market_parts,
        authority_entries=w3_entries,
    )
    code_bundle = build_code_bundle_manifest(_REPO_ROOT)
    source_manifest = build_trial1_source_manifest(
        market_history_payload_sha256=market_payload_sha256,
        w3_pit_authority_bundle_sha256=w3_bundle_sha256,
        development_label_custody_sha256=label_custody.payload_sha256,
        episode_custody_sha256=episode_custody.payload_sha256,
        decision_spine_sha256=decision_sha256,
        source_receipt_bundle_sha256=receipts_sha256,
    )
    prepared = trial1_m0.prepare_trial1_m0_for_trial_open(
        source_manifest=source_manifest,
        code_sha256=str(code_bundle["code_bundle_sha256"]),
    )
    if prepared.trial_open_appended:
        raise ValueError("precharge_prepare_must_not_append_trial_open")

    output_dir.mkdir(parents=True, exist_ok=True)
    code_path = output_dir / "trial1_code_bundle.json"
    source_path = output_dir / "trial1_source_manifest.json"
    label_path = output_dir / "w4_development_label_hash_custody.json"
    episode_path = output_dir / "w4_episode_anchor_hash_custody.json"
    prepared_path = output_dir / "trial1_prepared_uncharged.json"

    label_receipt = {
        **label_custody.as_dict(),
        "family_id": w2.FAMILY_ID,
        "label_spec_id": w2.PRIMARY_LABEL_SPEC_ID,
        "decision_spine_sha256": decision_sha256,
        "development_label_visibility": "HASHED_NOT_INSPECTED",
        "result_summary_emitted": False,
        "w6_lockbox_included": False,
    }
    episode_receipt = {
        **episode_custody.as_dict(),
        "family_id": w2.FAMILY_ID,
        "breakout_contract_sha256": w2.CONTRACT_SHA256,
        "decision_spine_sha256": decision_sha256,
        "winner_label_join_performed": False,
        "result_summary_emitted": False,
        "w6_lockbox_included": False,
    }
    prepared_payload = prepared.as_dict()

    code_file_sha = _atomic_json(code_path, code_bundle)
    source_file_sha = _atomic_json(source_path, source_manifest)
    label_file_sha = _atomic_json(label_path, label_receipt)
    episode_file_sha = _atomic_json(episode_path, episode_receipt)
    prepared_file_sha = _atomic_json(prepared_path, prepared_payload)

    receipt_body = {
        "schema_version": PRECHARGE_SCHEMA,
        "family_id": w2.FAMILY_ID,
        "trial_id": trial1_m0.TRIAL_ID,
        "implementation_id": trial1_m0.IMPLEMENTATION_ID,
        "w2_contract_sha256": w2.CONTRACT_SHA256,
        "w3_full_authority_manifest_sha256": str(authority["manifest_sha256"]),
        "w3_full_authority_bundle_sha256": str(authority["authority_bundle_sha256"]),
        "w3_precharge_authority_bundle_sha256": w3_bundle_sha256,
        "precharge_market_payload_sha256": market_payload_sha256,
        "source_receipt_bundle_sha256": receipts_sha256,
        "decision_spine_sha256": decision_sha256,
        "development_label_custody_sha256": label_custody.payload_sha256,
        "episode_anchor_custody_sha256": episode_custody.payload_sha256,
        "source_manifest_sha256": str(source_manifest["manifest_sha256"]),
        "code_bundle_sha256": str(code_bundle["code_bundle_sha256"]),
        "prepared_variant_sha256": prepared.variant_sha256,
        "precharge_market_session_count": len(market_parts),
        "precharge_w3_authority_session_count": len(w3_entries),
        "development_decision_session_count": len(development),
        "market_row_count_loaded": market_row_count,
        "development_label_visibility": "HASHED_NOT_INSPECTED",
        "development_label_payload_persisted": False,
        "development_label_values_printed": False,
        "development_label_result_summary_emitted": False,
        "episode_payload_persisted": False,
        "episode_winner_join_performed": False,
        "w6_lockbox_market_rows_read": False,
        "w6_lockbox_included": False,
        "w6_labels_opened": False,
        "trial_open_appended": False,
        "material_trials_consumed": 0,
        "development_run_performed": False,
        "result_inspection_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
        "frozen_at_utc": datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "artifacts": {
            "trial1_code_bundle.json": code_file_sha,
            "trial1_source_manifest.json": source_file_sha,
            "w4_development_label_hash_custody.json": label_file_sha,
            "w4_episode_anchor_hash_custody.json": episode_file_sha,
            "trial1_prepared_uncharged.json": prepared_file_sha,
        },
    }
    receipt = {**receipt_body, "receipt_sha256": canonical_sha256(receipt_body)}
    receipt_file_sha = _atomic_json(output_dir / "precharge.receipt.json", receipt)

    return {
        "precharge_receipt_sha256": receipt["receipt_sha256"],
        "precharge_receipt_file_sha256": receipt_file_sha,
        "source_manifest_sha256": source_manifest["manifest_sha256"],
        "code_bundle_sha256": code_bundle["code_bundle_sha256"],
        "prepared_variant_sha256": prepared.variant_sha256,
        "trial_open_appended": False,
        "material_trials_consumed": 0,
        "development_label_visibility": "HASHED_NOT_INSPECTED",
        "w6_lockbox_included": False,
        "w6_labels_opened": False,
        "result_inspection_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = freeze(args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
