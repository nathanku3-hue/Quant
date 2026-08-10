"""Run the single charged PREBREAKOUT Trial #1 development sequence.

Strict ordering:
1. verify the frozen uncharged source/code/precharge custody;
2. append or reuse the exact Trial-1 TRIAL_OPEN (cost 1/8);
3. freeze deterministic W3-aligned Trial-1 flags before any label materialization;
4. materialize development labels/episode anchors only after the charge and
   require exact equality with the pre-charge hash-only custody;
5. run W5 temporal-OOS development and W4 discovery census;
6. close Trial #1 PASS/FAIL/NULL from the frozen development survival law.

This script never reads W6 decision/tail market rows, never opens W6 labels,
never creates broker orders, and never changes the Trial-1 scientific rule.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Iterable, Mapping

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from research.prebreakout_atlas_v1.atlas import (
    EXCLUDED_WINNER,
    MISSED_WINNER,
    TRUE_WINNER,
    MatchedControlContract,
    PrebreakoutMethodologyBinding,
    build_discovery_atlas,
    verify_discovery_atlas,
)
from research.prebreakout_discovery_v1 import preregistration as w2
from research.prebreakout_discovery_v1.breakout import enforce_b_minus_one_pit_proof
from research.prebreakout_discovery_v1.ledger import (
    EVENT_CLOSE,
    EVENT_OPEN,
    append_trial_close,
    append_trial_open,
    load_trial_ledger,
    verify_trial_ledger,
)
from research.prebreakout_discovery_v1.precharge_custody import (
    EPISODE_HASH_DOMAIN,
    LABEL_HASH_DOMAIN,
    canonical_json_bytes,
    create_market_table,
    iter_development_label_records,
    iter_episode_anchor_records,
)
from research.prebreakout_discovery_v1.trial1_m0 import (
    CONTROL_SPEC_ID,
    FEATURE_COLUMNS,
    IMPLEMENTATION_ID,
    TRIAL_ID,
    as_development_candidate,
    compute_trial1_m0_features,
    prepare_trial1_m0_for_trial_open,
    summarize_trial1_recall_lift,
    trial1_m0_fold_recall_lift_objective,
    trial1_m0_scorer,
    verify_trial1_source_manifest,
)
from research.prebreakout_discovery_v1.walk_forward import run_charged_development_candidate
from research.prebreakout_pit_v1.authority import ELIGIBLE, RISK_SET_SPEC_ID
from research.prebreakout_pit_v1.real_source import canonical_sha256, sha256_file


W3_ROOT = Path("data/prebreakout/compiled/w3_real_authority_20250324_20260807")
PRECHARGE_ROOT = Path("data/prebreakout/compiled/trial1_precharge_20260810")
DEFAULT_OUTPUT = Path("data/prebreakout/compiled/trial1_real_20260810")
DEFAULT_LEDGER = Path("data/prebreakout/ledger/trial_ledger.jsonl")
MU_IDENTITY = ("CIQSEC:IQ289030", "2630498")
SNDK_IDENTITY = ("CIQSEC:IQ1860586153", "1929119896")
SMOKE_IDENTITIES = frozenset({MU_IDENTITY, SNDK_IDENTITY})


class Trial1RealRunError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise Trial1RealRunError(f"trial1_json_object_required:{path}")
    return value


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


def _atomic_gzip_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with gzip.open(temp, "wt", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            handle.write("\n")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return sha256_file(path)


def _atomic_duckdb_copy(connection: duckdb.DuckDBPyConnection, query: str, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".parquet.tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    temp.unlink(missing_ok=True)
    try:
        escaped = temp.as_posix().replace("'", "''")
        connection.execute(f"COPY ({query}) TO '{escaped}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return sha256_file(path)


def _stream_records_to_parquet(
    *,
    records: Iterable[Mapping[str, Any]],
    domain: str,
    path: Path,
    schema: pa.Schema,
    expected_payload_sha256: str,
    expected_record_count: int,
) -> tuple[str, int, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".parquet.tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    temp.unlink(missing_ok=True)
    digest = hashlib.sha256()
    digest.update(domain.encode("utf-8"))
    digest.update(b"\n")
    count = 0
    writer: pq.ParquetWriter | None = None
    batch: list[dict[str, Any]] = []
    try:
        writer = pq.ParquetWriter(temp, schema=schema, compression="zstd", use_dictionary=True)
        for raw in records:
            record = dict(raw)
            digest.update(canonical_json_bytes(record))
            digest.update(b"\n")
            batch.append(record)
            count += 1
            if len(batch) >= 10_000:
                writer.write_table(pa.Table.from_pylist(batch, schema=schema))
                batch.clear()
        if batch:
            writer.write_table(pa.Table.from_pylist(batch, schema=schema))
        writer.close()
        writer = None
        payload_sha = digest.hexdigest()
        if payload_sha != expected_payload_sha256:
            raise Trial1RealRunError("trial1_postcharge_payload_hash_mismatch")
        if count != expected_record_count:
            raise Trial1RealRunError("trial1_postcharge_payload_record_count_mismatch")
        temp.replace(path)
    finally:
        if writer is not None:
            writer.close()
        temp.unlink(missing_ok=True)
    return payload_sha, count, sha256_file(path)


def _verify_precharge() -> dict[str, Any]:
    receipt = _load_json(PRECHARGE_ROOT / "precharge.receipt.json")
    source_manifest = _load_json(PRECHARGE_ROOT / "trial1_source_manifest.json")
    code_bundle = _load_json(PRECHARGE_ROOT / "trial1_code_bundle.json")
    prepared = _load_json(PRECHARGE_ROOT / "trial1_prepared_uncharged.json")
    label_custody = _load_json(PRECHARGE_ROOT / "w4_development_label_hash_custody.json")
    episode_custody = _load_json(PRECHARGE_ROOT / "w4_episode_anchor_hash_custody.json")

    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise Trial1RealRunError("trial1_precharge_artifact_map_required")
    for name, expected in artifacts.items():
        path = PRECHARGE_ROOT / str(name)
        if sha256_file(path) != str(expected):
            raise Trial1RealRunError("trial1_precharge_artifact_hash_drift:" + str(name))
    if receipt.get("trial_open_appended") is not False or int(receipt.get("material_trials_consumed", -1)) != 0:
        raise Trial1RealRunError("trial1_precharge_state_not_uncharged")
    if receipt.get("development_label_visibility") != "HASHED_NOT_INSPECTED":
        raise Trial1RealRunError("trial1_precharge_label_visibility_invalid")
    if receipt.get("w6_lockbox_included") is not False or receipt.get("w6_labels_opened") is not False:
        raise Trial1RealRunError("trial1_precharge_w6_forbidden")
    if verify_trial1_source_manifest(source_manifest) != source_manifest["manifest_sha256"]:
        raise Trial1RealRunError("trial1_source_manifest_reopen_failed")
    if source_manifest["manifest_sha256"] != receipt["source_manifest_sha256"]:
        raise Trial1RealRunError("trial1_source_manifest_receipt_drift")
    if code_bundle["code_bundle_sha256"] != receipt["code_bundle_sha256"]:
        raise Trial1RealRunError("trial1_code_bundle_receipt_drift")
    for item in code_bundle["files"]:
        path = _REPO_ROOT / str(item["path"])
        if sha256_file(path) != str(item["sha256"]):
            raise Trial1RealRunError("trial1_code_file_hash_drift:" + str(item["path"]))
    re_prepared = prepare_trial1_m0_for_trial_open(
        source_manifest=source_manifest,
        code_sha256=str(code_bundle["code_bundle_sha256"]),
    )
    if re_prepared.variant_sha256 != prepared["variant_sha256"]:
        raise Trial1RealRunError("trial1_prepared_variant_hash_drift")
    if re_prepared.variant_sha256 != receipt["prepared_variant_sha256"]:
        raise Trial1RealRunError("trial1_prepared_variant_receipt_drift")
    return {
        "receipt": receipt,
        "source_manifest": source_manifest,
        "code_bundle": code_bundle,
        "prepared": re_prepared,
        "label_custody": label_custody,
        "episode_custody": episode_custody,
    }


def _open_or_reuse_trial(ledger_path: Path, prepared: Any) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    entries = load_trial_ledger(ledger_path)
    verify_trial_ledger(entries)
    opens = [entry for entry in entries if entry["event_type"] == EVENT_OPEN and entry["payload"]["trial_id"] == TRIAL_ID]
    if len(opens) > 1:
        raise Trial1RealRunError("trial1_multiple_open_entries")
    if opens:
        opened = opens[0]
        if opened["payload"]["variant"] != dict(prepared.variant):
            raise Trial1RealRunError("trial1_existing_open_variant_mismatch")
        if opened["payload"]["variant_sha256"] != prepared.variant_sha256:
            raise Trial1RealRunError("trial1_existing_open_variant_hash_mismatch")
    else:
        if any(entry["event_type"] == EVENT_OPEN for entry in entries):
            raise Trial1RealRunError("trial1_real_ledger_contains_other_material_trial")
        opened = append_trial_open(
            ledger_path,
            trial_id=TRIAL_ID,
            variant=prepared.variant,
        )
        entries = load_trial_ledger(ledger_path)
        verify_trial_ledger(entries)
    closes = [entry for entry in entries if entry["event_type"] == EVENT_CLOSE and entry["payload"]["trial_id"] == TRIAL_ID]
    if closes:
        raise Trial1RealRunError("trial1_already_closed")
    if int(entries[-1]["cumulative_material_trials"]) != 1:
        raise Trial1RealRunError("trial1_material_trial_count_not_one")
    return opened, entries, sha256_file(ledger_path)


def _load_w3() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = _load_json(W3_ROOT / "source_manifest.json")
    authority = _load_json(W3_ROOT / "authority.manifest.json")
    partition = _load_json(W3_ROOT / "session_partition.json")
    if source.get("w2_contract_sha256") != w2.CONTRACT_SHA256:
        raise Trial1RealRunError("trial1_w3_source_w2_hash_mismatch")
    if authority.get("w2_contract_sha256") != w2.CONTRACT_SHA256:
        raise Trial1RealRunError("trial1_w3_authority_w2_hash_mismatch")
    if authority.get("w6_labels_opened") is not False or authority.get("outcome_access_performed") is not False:
        raise Trial1RealRunError("trial1_w3_w6_or_outcome_state_invalid")
    return source, authority, partition


def _market_parts_by_date(source: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    parts = list(source["market"]["parts"])
    result = {str(item["session_date"]): dict(item) for item in parts}
    if len(result) != len(parts):
        raise Trial1RealRunError("trial1_market_part_date_duplicate")
    return result


def _authority_entries_by_date(authority: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    entries = list(authority["entries"])
    result = {str(item["decision_session_date"]): dict(item) for item in entries}
    if len(result) != len(entries):
        raise Trial1RealRunError("trial1_w3_authority_date_duplicate")
    return result


def _read_pre_w6_market(parts: list[dict[str, Any]]) -> pd.DataFrame:
    paths = [str(item["csv_path"]) for item in parts]
    connection = duckdb.connect(database=":memory:")
    try:
        frame = connection.execute(
            """
            SELECT
                'CIQSEC:' || TRIM(SP_CIQ_ID) AS security_id,
                TRIM(SP_TRADING_ITEM_ID) AS trading_item_id,
                MEMBERSHIP_AS_OF_DATE AS session_date,
                CAST(SP_PRICE_CLOSE AS DOUBLE) AS close,
                TRY_CAST(NULLIF(TRIM(SP_TOTAL_RETURN), '') AS DOUBLE) / 100.0 AS total_return_1d,
                CAST(SP_VOLUME AS DOUBLE) AS volume
            FROM read_csv_auto(?, all_varchar=true, union_by_name=true)
            ORDER BY security_id, trading_item_id, session_date
            """,
            [paths],
        ).df()
    finally:
        connection.close()
    return frame


def _write_w3_projection(entries: list[dict[str, Any]], path: Path, global_ordinal: Mapping[str, int]) -> str:
    schema = pa.schema(
        [
            ("decision_session_date", pa.string()),
            ("decision_session_ordinal", pa.int64()),
            ("security_id", pa.string()),
            ("trading_item_id", pa.string()),
            ("pit_authority_sha256", pa.string()),
            ("pit_risk_set_spec_id", pa.string()),
            ("eligibility_status", pa.string()),
            ("exclusion_reason", pa.string()),
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    temp.unlink(missing_ok=True)
    writer = pq.ParquetWriter(temp, schema=schema, compression="zstd", use_dictionary=True)
    try:
        for entry in entries:
            authority_path = Path(str(entry["authority_path"]))
            if sha256_file(authority_path) != str(entry["authority_file_sha256"]):
                raise Trial1RealRunError("trial1_w3_authority_file_hash_drift")
            with gzip.open(authority_path, "rt", encoding="utf-8") as handle:
                packet = json.load(handle)
            if packet.get("packet_sha256") != entry["authority_packet_sha256"]:
                raise Trial1RealRunError("trial1_w3_authority_packet_hash_drift")
            date_text = str(entry["decision_session_date"])
            records: list[dict[str, Any]] = []
            for row in (*packet["eligible_rows"], *packet["exclusion_rows"]):
                records.append(
                    {
                        "decision_session_date": date_text,
                        "decision_session_ordinal": int(global_ordinal[date_text]),
                        "security_id": str(row["security_id"]),
                        "trading_item_id": str(row["trading_item_id"]),
                        "pit_authority_sha256": str(packet["packet_sha256"]),
                        "pit_risk_set_spec_id": str(packet["risk_set_spec_id"]),
                        "eligibility_status": str(row["eligibility_status"]),
                        "exclusion_reason": str(row.get("exclusion_reason") or ""),
                    }
                )
            if len(records) != int(entry["candidate_count"]):
                raise Trial1RealRunError("trial1_w3_projection_candidate_count_drift")
            writer.write_table(pa.Table.from_pylist(records, schema=schema))
        writer.close()
        writer = None
        temp.replace(path)
    finally:
        if writer is not None:
            writer.close()
        temp.unlink(missing_ok=True)
    return sha256_file(path)


def _freeze_flags(
    *,
    output_dir: Path,
    source: Mapping[str, Any],
    authority: Mapping[str, Any],
    partition: Mapping[str, Any],
    prepared: Any,
    code_bundle_sha256: str,
    source_manifest_sha256: str,
    trial_open_chain_hash: str,
) -> dict[str, Any]:
    warmup = list(map(str, partition["feature_warmup"]))
    development = list(map(str, partition["w5_development"]))
    embargo = list(map(str, partition["post_development_embargo"]))
    lockbox = set(map(str, partition["w6_lockbox_decisions"]))
    tail = set(map(str, partition["lockbox_label_maturity_tail"]))
    market_by_date = _market_parts_by_date(source)
    pre_w6_dates = warmup + development + embargo
    if set(pre_w6_dates) & (lockbox | tail):
        raise Trial1RealRunError("trial1_flag_source_overlaps_w6")
    market_parts = [market_by_date[value] for value in pre_w6_dates]
    market = _read_pre_w6_market(market_parts)
    features = compute_trial1_m0_features(market)
    del market
    features["decision_listing_session_ordinal"] = features.groupby(
        ["security_id", "trading_item_id"], sort=False
    ).cumcount().astype(np.int64)
    census_dates = set(warmup + development)
    features = features[features["session_date"].isin(census_dates)].copy()

    global_ordinal = {str(value): index for index, value in enumerate(source["session_spine"])}
    authority_by_date = _authority_entries_by_date(authority)
    entries = [authority_by_date[value] for value in warmup + development]
    w3_projection = output_dir / "w3_warmup_development_projection.parquet"
    w3_projection_sha = _write_w3_projection(entries, w3_projection, global_ordinal)

    connection = duckdb.connect(database=":memory:")
    connection.register("trial_features", features)
    try:
        flag_path = output_dir / "trial1_flag_projection.parquet"
        w3_path = w3_projection.as_posix().replace("'", "''")
        query = f"""
        SELECT
            w.decision_session_date,
            w.decision_session_ordinal,
            CAST(f.decision_listing_session_ordinal AS BIGINT) AS decision_listing_session_ordinal,
            w.security_id,
            w.trading_item_id,
            w.pit_authority_sha256,
            w.pit_risk_set_spec_id,
            w.eligibility_status,
            w.exclusion_reason,
            f.feature_status,
            CAST(f.near_high_component AS DOUBLE) AS near_high_component,
            CAST(f.vol_compression_component AS DOUBLE) AS vol_compression_component,
            CAST(f.volume_pressure_component AS DOUBLE) AS volume_pressure_component,
            CASE WHEN w.eligibility_status = '{ELIGIBLE}' THEN CAST(f.prebreakout_trigger AS BOOLEAN) ELSE FALSE END AS flagged,
            CASE WHEN w.eligibility_status = '{ELIGIBLE}' THEN CAST(f.forecast_score AS DOUBLE) ELSE 0.0 END AS forecast_score,
            'ALL_W3_ELIGIBLE' AS trial1_control_stratum
        FROM read_parquet('{w3_path}') w
        JOIN trial_features f
          ON f.session_date = w.decision_session_date
         AND f.security_id = w.security_id
         AND f.trading_item_id = w.trading_item_id
        ORDER BY w.decision_session_ordinal, w.security_id, w.trading_item_id
        """
        flag_sha = _atomic_duckdb_copy(connection, query, flag_path)
        row_count = int(connection.execute(f"SELECT COUNT(*) FROM read_parquet('{flag_path.as_posix()}')").fetchone()[0])
        expected = sum(int(entry["candidate_count"]) for entry in entries)
        if row_count != expected:
            raise Trial1RealRunError("trial1_flag_projection_row_count_not_full_w3_census")
        excluded_flagged = int(
            connection.execute(
                f"SELECT COUNT(*) FROM read_parquet('{flag_path.as_posix()}') WHERE eligibility_status != '{ELIGIBLE}' AND flagged"
            ).fetchone()[0]
        )
        if excluded_flagged:
            raise Trial1RealRunError("trial1_excluded_row_flagged")
    finally:
        connection.unregister("trial_features")
        connection.close()
        del features

    receipt_body = {
        "schema_version": "prebreakout_trial1_flag_freeze_v1",
        "family_id": w2.FAMILY_ID,
        "trial_id": TRIAL_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "variant_sha256": prepared.variant_sha256,
        "source_manifest_sha256": source_manifest_sha256,
        "code_bundle_sha256": code_bundle_sha256,
        "trial_open_chain_hash": trial_open_chain_hash,
        "w3_full_authority_bundle_sha256": authority["authority_bundle_sha256"],
        "flag_projection_path": flag_path.as_posix(),
        "flag_projection_sha256": flag_sha,
        "flag_projection_row_count": row_count,
        "w3_projection_path": w3_projection.as_posix(),
        "w3_projection_sha256": w3_projection_sha,
        "warmup_session_count": len(warmup),
        "development_session_count": len(development),
        "w6_market_rows_read": False,
        "development_labels_materialized": False,
        "development_label_values_inspected": False,
        "outcome_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
        "frozen_at_utc": datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    }
    receipt = {**receipt_body, "receipt_sha256": canonical_sha256(receipt_body)}
    _atomic_json(output_dir / "trial1_flag_freeze.receipt.json", receipt)
    return receipt


def _materialize_postcharge_custody(
    *,
    output_dir: Path,
    source: Mapping[str, Any],
    authority: Mapping[str, Any],
    partition: Mapping[str, Any],
    label_custody: Mapping[str, Any],
    episode_custody: Mapping[str, Any],
    flag_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    warmup = list(map(str, partition["feature_warmup"]))
    development = list(map(str, partition["w5_development"]))
    embargo = list(map(str, partition["post_development_embargo"]))
    market_by_date = _market_parts_by_date(source)
    market_parts = [market_by_date[value] for value in warmup + development + embargo]
    authority_by_date = _authority_entries_by_date(authority)
    candidate_counts = {
        value: int(authority_by_date[value]["candidate_count"])
        for value in development
    }

    connection = duckdb.connect(database=":memory:")
    try:
        create_market_table(
            connection,
            csv_paths=[str(item["csv_path"]) for item in market_parts],
            maximum_session_date=embargo[-1],
        )
        label_schema = pa.schema(
            [
                ("schema_version", pa.string()),
                ("family_id", pa.string()),
                ("label_spec_id", pa.string()),
                ("decision_session_date", pa.string()),
                ("security_id", pa.string()),
                ("trading_item_id", pa.string()),
                ("listing_session_ordinal", pa.int64()),
                ("candidate_count", pa.int64()),
                ("required_winner_count", pa.int64()),
                ("label_available_date", pa.string()),
                ("horizon_status", pa.string()),
                ("forward_total_return", pa.string()),
                ("winner_label", pa.bool_()),
            ]
        )
        label_path = output_dir / "development_labels.parquet"
        label_payload_sha, label_count, label_file_sha = _stream_records_to_parquet(
            records=iter_development_label_records(
                connection,
                decision_dates=development,
                candidate_counts=candidate_counts,
            ),
            domain=LABEL_HASH_DOMAIN,
            path=label_path,
            schema=label_schema,
            expected_payload_sha256=str(label_custody["payload_sha256"]),
            expected_record_count=int(label_custody["record_count"]),
        )

        episode_schema = pa.schema(
            [
                ("schema_version", pa.string()),
                ("family_id", pa.string()),
                ("breakout_contract_sha256", pa.string()),
                ("effective_episode_id", pa.string()),
                ("security_id", pa.string()),
                ("trading_item_id", pa.string()),
                ("breakout_session_date", pa.string()),
                ("breakout_session_ordinal", pa.int64()),
                ("breakout_listing_session_ordinal", pa.int64()),
                ("b_minus_1_session_date", pa.string()),
                ("b_minus_1_session_ordinal", pa.int64()),
                ("b_minus_1_listing_session_ordinal", pa.int64()),
                ("lead_window_start_session_date", pa.string()),
                ("lead_window_start_session_ordinal", pa.int64()),
                ("lead_window_start_listing_session_ordinal", pa.int64()),
            ]
        )
        episode_path = output_dir / "development_episode_anchors.parquet"
        episode_payload_sha, episode_count, episode_file_sha = _stream_records_to_parquet(
            records=iter_episode_anchor_records(
                connection,
                session_spine=source["session_spine"],
                development_decision_dates=development,
            ),
            domain=EPISODE_HASH_DOMAIN,
            path=episode_path,
            schema=episode_schema,
            expected_payload_sha256=str(episode_custody["payload_sha256"]),
            expected_record_count=int(episode_custody["record_count"]),
        )
    finally:
        connection.close()

    receipt_body = {
        "schema_version": "prebreakout_trial1_postcharge_label_open_v1",
        "family_id": w2.FAMILY_ID,
        "trial_id": TRIAL_ID,
        "trial_open_chain_hash": flag_receipt["trial_open_chain_hash"],
        "flag_freeze_receipt_sha256": flag_receipt["receipt_sha256"],
        "prediction_before_label_materialization": True,
        "development_label_payload_sha256": label_payload_sha,
        "development_label_record_count": label_count,
        "development_label_path": label_path.as_posix(),
        "development_label_file_sha256": label_file_sha,
        "episode_anchor_payload_sha256": episode_payload_sha,
        "episode_anchor_record_count": episode_count,
        "episode_anchor_path": episode_path.as_posix(),
        "episode_anchor_file_sha256": episode_file_sha,
        "precharge_label_hash_reproduced": True,
        "precharge_episode_hash_reproduced": True,
        "w6_lockbox_included": False,
        "w6_labels_opened": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
        "opened_at_utc": datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    }
    receipt = {**receipt_body, "receipt_sha256": canonical_sha256(receipt_body)}
    _atomic_json(output_dir / "development_label_open.receipt.json", receipt)
    return receipt


def _w5_run(
    *,
    output_dir: Path,
    flag_receipt: Mapping[str, Any],
    label_open: Mapping[str, Any],
    partition: Mapping[str, Any],
    source_manifest: Mapping[str, Any],
    code_bundle: Mapping[str, Any],
    prepared: Any,
    ledger_entries: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    development = set(map(str, partition["w5_development"]))
    flags = Path(str(flag_receipt["flag_projection_path"]))
    labels = Path(str(label_open["development_label_path"]))
    if sha256_file(flags) != flag_receipt["flag_projection_sha256"]:
        raise Trial1RealRunError("trial1_flag_file_hash_drift_before_w5")
    if sha256_file(labels) != label_open["development_label_file_sha256"]:
        raise Trial1RealRunError("trial1_label_file_hash_drift_before_w5")

    connection = duckdb.connect(database=":memory:")
    try:
        flag_path = flags.as_posix().replace("'", "''")
        label_path = labels.as_posix().replace("'", "''")
        development_list = sorted(development)
        connection.execute("CREATE TEMP TABLE dev_dates(decision_date VARCHAR)")
        connection.executemany("INSERT INTO dev_dates VALUES (?)", [(value,) for value in development_list])
        feature_frame = connection.execute(
            f"""
            SELECT
                f.decision_session_date AS decision_date,
                f.security_id,
                f.trading_item_id,
                CASE
                    WHEN (f.security_id = '{MU_IDENTITY[0]}' AND f.trading_item_id = '{MU_IDENTITY[1]}')
                      OR (f.security_id = '{SNDK_IDENTITY[0]}' AND f.trading_item_id = '{SNDK_IDENTITY[1]}')
                    THEN 0.0 ELSE 1.0
                END AS statistical_weight,
                '{source_manifest['manifest_sha256']}' AS source_manifest_sha256,
                f.pit_authority_sha256,
                f.pit_risk_set_spec_id,
                f.near_high_component,
                f.vol_compression_component,
                f.volume_pressure_component,
                f.flagged AS prebreakout_trigger
            FROM read_parquet('{flag_path}') f
            JOIN dev_dates d ON d.decision_date = f.decision_session_date
            WHERE f.eligibility_status = '{ELIGIBLE}'
            ORDER BY f.decision_session_date, f.security_id
            """
        ).df()
        connection.register("w5_features", feature_frame)
        label_frame = connection.execute(
            f"""
            SELECT
                l.decision_session_date AS decision_date,
                l.security_id,
                CASE WHEN l.winner_label IS NULL THEN NULL ELSE CAST(l.winner_label AS INTEGER) END AS target_label,
                l.label_available_date,
                CASE WHEN l.horizon_status = 'INCOMPLETE_HORIZON' THEN 'INCOMPLETE_HORIZON' ELSE 'MATURED' END AS label_status
            FROM read_parquet('{label_path}') l
            JOIN w5_features f
              ON f.decision_date = l.decision_session_date
             AND f.security_id = l.security_id
             AND f.trading_item_id = l.trading_item_id
            ORDER BY l.decision_session_date, l.security_id
            """
        ).df()
    finally:
        try:
            connection.unregister("w5_features")
        except Exception:
            pass
        connection.close()

    candidate = as_development_candidate(prepared)
    run = run_charged_development_candidate(
        feature_frame=feature_frame,
        label_frame=label_frame,
        spec=prepared_walk_forward_spec(),
        candidate=candidate,
        trial_ledger_entries=ledger_entries,
        scorer=trial1_m0_scorer,
        objective=trial1_m0_fold_recall_lift_objective,
    )
    summary = summarize_trial1_recall_lift(run)
    _atomic_gzip_json(output_dir / "w5_development_run.json.gz", run)
    _atomic_json(output_dir / "w5_recall_lift_summary.json", summary)
    return run, summary


def prepared_walk_forward_spec():
    from research.prebreakout_discovery_v1.trial1_m0 import build_trial1_walk_forward_spec

    return build_trial1_walk_forward_spec()


def _build_w4_grid(
    *,
    flag_path: Path,
    label_path: Path,
    episode_path: Path,
    partition: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    development = list(map(str, partition["w5_development"]))
    warmup = list(map(str, partition["feature_warmup"]))
    connection = duckdb.connect(database=":memory:")
    try:
        fpath = flag_path.as_posix().replace("'", "''")
        lpath = label_path.as_posix().replace("'", "''")
        epath = episode_path.as_posix().replace("'", "''")
        connection.execute("CREATE TEMP TABLE dev_dates(decision_date VARCHAR)")
        connection.executemany("INSERT INTO dev_dates VALUES (?)", [(value,) for value in development])
        connection.execute("CREATE TEMP TABLE warmup_dates(decision_date VARCHAR)")
        connection.executemany("INSERT INTO warmup_dates VALUES (?)", [(value,) for value in warmup])
        connection.execute(
            f"""
            CREATE TEMP TABLE episode_status AS
            SELECT
                e.*,
                l.horizon_status AS b1_horizon_status,
                l.winner_label AS b1_winner_label
            FROM read_parquet('{epath}') e
            JOIN read_parquet('{lpath}') l
              ON l.decision_session_date = e.b_minus_1_session_date
             AND l.security_id = e.security_id
             AND l.trading_item_id = e.trading_item_id
            """
        )
        overlap = int(
            connection.execute(
                """
                SELECT COUNT(*) FROM (
                    SELECT f.decision_session_date, f.security_id, f.trading_item_id, COUNT(*) AS n
                    FROM read_parquet(?) f
                    JOIN episode_status e
                      ON e.security_id = f.security_id
                     AND e.trading_item_id = f.trading_item_id
                     AND f.decision_listing_session_ordinal BETWEEN
                         e.breakout_listing_session_ordinal - ? AND e.b_minus_1_listing_session_ordinal
                    WHERE e.b1_winner_label IS TRUE OR e.b1_horizon_status = 'INCOMPLETE_HORIZON'
                    GROUP BY 1,2,3 HAVING COUNT(*) > 1
                )
                """,
                [str(flag_path), int(w2.LEAD_LOOKBACK_SESSIONS)],
            ).fetchone()[0]
        )
        if overlap:
            raise Trial1RealRunError("trial1_w4_episode_lead_intervals_overlap")
        grid = connection.execute(
            f"""
            SELECT
                f.decision_session_date,
                f.decision_session_ordinal,
                f.decision_listing_session_ordinal,
                f.security_id,
                f.trading_item_id,
                f.pit_authority_sha256,
                f.pit_risk_set_spec_id,
                f.eligibility_status,
                f.exclusion_reason,
                f.flagged,
                CASE
                    WHEN e.b1_horizon_status = 'INCOMPLETE_HORIZON' THEN NULL
                    WHEN e.b1_winner_label IS TRUE THEN TRUE
                    ELSE FALSE
                END AS winner_label,
                CASE
                    WHEN e.b1_horizon_status = 'INCOMPLETE_HORIZON' THEN 'INCOMPLETE_HORIZON'
                    ELSE 'MATURED_OPEN'
                END AS outcome_status,
                COALESCE(
                    e.effective_episode_id,
                    'ROW|' || f.decision_session_date || '|' || f.security_id || '|' || f.trading_item_id
                ) AS effective_episode_id,
                CASE WHEN e.b1_winner_label IS TRUE THEN e.breakout_session_date ELSE NULL END AS breakout_session_date,
                CASE WHEN e.b1_winner_label IS TRUE THEN e.breakout_session_ordinal ELSE NULL END AS breakout_session_ordinal,
                CASE WHEN e.b1_winner_label IS TRUE THEN e.breakout_listing_session_ordinal ELSE NULL END AS breakout_listing_session_ordinal,
                CASE WHEN e.b1_winner_label IS TRUE THEN e.b_minus_1_session_date ELSE NULL END AS b_minus_1_session_date,
                CASE WHEN e.b1_winner_label IS TRUE THEN e.b_minus_1_session_ordinal ELSE NULL END AS b_minus_1_session_ordinal,
                CASE WHEN e.b1_winner_label IS TRUE THEN e.b_minus_1_listing_session_ordinal ELSE NULL END AS b_minus_1_listing_session_ordinal,
                f.trial1_control_stratum
            FROM read_parquet('{fpath}') f
            JOIN dev_dates d ON d.decision_date = f.decision_session_date
            LEFT JOIN episode_status e
              ON e.security_id = f.security_id
             AND e.trading_item_id = f.trading_item_id
             AND (e.b1_winner_label IS TRUE OR e.b1_horizon_status = 'INCOMPLETE_HORIZON')
             AND f.decision_listing_session_ordinal BETWEEN
                 e.breakout_listing_session_ordinal - {int(w2.LEAD_LOOKBACK_SESSIONS)}
                 AND e.b_minus_1_listing_session_ordinal
            ORDER BY f.decision_session_ordinal, f.security_id, f.trading_item_id
            """
        ).df()
        prehistory = connection.execute(
            f"""
            SELECT
                f.decision_session_date,
                f.decision_session_ordinal,
                f.decision_listing_session_ordinal,
                f.security_id,
                f.trading_item_id,
                f.pit_authority_sha256,
                f.pit_risk_set_spec_id,
                f.eligibility_status,
                f.exclusion_reason,
                f.flagged
            FROM read_parquet('{fpath}') f
            JOIN warmup_dates d ON d.decision_date = f.decision_session_date
            ORDER BY f.decision_session_ordinal, f.security_id, f.trading_item_id
            """
        ).df()
    finally:
        connection.close()
    return grid, prehistory


def _w4_run(
    *,
    output_dir: Path,
    flag_receipt: Mapping[str, Any],
    label_open: Mapping[str, Any],
    partition: Mapping[str, Any],
    authority: Mapping[str, Any],
    trial_open: Mapping[str, Any],
    ledger_snapshot_sha256: str,
) -> dict[str, Any]:
    flag_path = Path(str(flag_receipt["flag_projection_path"]))
    label_path = Path(str(label_open["development_label_path"]))
    episode_path = Path(str(label_open["episode_anchor_path"]))
    grid, prehistory = _build_w4_grid(
        flag_path=flag_path,
        label_path=label_path,
        episode_path=episode_path,
        partition=partition,
    )
    methodology = PrebreakoutMethodologyBinding.from_preregistration_snapshot(
        w2.contract_snapshot(),
        methodology_contract_sha256=w2.CONTRACT_SHA256,
    )
    control = MatchedControlContract(
        methodology_contract_sha256=w2.CONTRACT_SHA256,
        control_definition_id=CONTROL_SPEC_ID,
        match_columns=("trial1_control_stratum",),
        search_charge_receipt_sha256=str(trial_open["chain_hash"]),
        trial_ledger_snapshot_sha256=ledger_snapshot_sha256,
    )
    entries = _authority_entries_by_date(authority)
    dev_entries = {value: entries[value] for value in map(str, partition["w5_development"])}
    warmup_entries = {value: entries[value] for value in map(str, partition["feature_warmup"])}
    smoke_bundle = _load_json(W3_ROOT / "mu_sndk_bminus1_proofs.json")
    smoke_proofs = list(smoke_bundle["proofs"])
    report = build_discovery_atlas(
        grid,
        methodology=methodology,
        matched_control_contract=control,
        pit_authorities_by_date=dev_entries,
        prehistory_flags=prehistory,
        prehistory_pit_authorities_by_date=warmup_entries,
        smoke_proofs=smoke_proofs,
        fixture=False,
    )
    verify_discovery_atlas(report)
    _atomic_gzip_json(output_dir / "w4_discovery_atlas.json.gz", report)
    return report


def _smoke_development_checks(
    *,
    flag_path: Path,
    source: Mapping[str, Any],
    partition: Mapping[str, Any],
) -> dict[str, Any]:
    development_end = str(partition["w5_development"][-1])
    pre_w6_end = str(partition["post_development_embargo"][-1])
    proof_bundle = _load_json(W3_ROOT / "mu_sndk_bminus1_proofs.json")
    proofs = list(proof_bundle["proofs"])
    market_by_date = _market_parts_by_date(source)
    pre_w6_dates = [value for value in source["session_spine"] if str(value) <= pre_w6_end]
    paths = [str(market_by_date[str(value)]["csv_path"]) for value in pre_w6_dates]
    connection = duckdb.connect(database=":memory:")
    try:
        ordered = connection.execute(
            """
            SELECT 'CIQSEC:' || SP_CIQ_ID AS security_id, SP_TRADING_ITEM_ID AS trading_item_id,
                   LIST(MEMBERSHIP_AS_OF_DATE ORDER BY MEMBERSHIP_AS_OF_DATE) AS sessions
            FROM read_csv_auto(?, all_varchar=true, union_by_name=true)
            WHERE ('CIQSEC:' || SP_CIQ_ID, SP_TRADING_ITEM_ID) IN ((?, ?), (?, ?))
            GROUP BY 1,2
            """,
            [paths, MU_IDENTITY[0], MU_IDENTITY[1], SNDK_IDENTITY[0], SNDK_IDENTITY[1]],
        ).fetchall()
        ordered_by_identity = {(str(row[0]), str(row[1])): list(map(str, row[2])) for row in ordered}
        flagged = connection.execute(
            """
            SELECT security_id, trading_item_id,
                   LIST(decision_session_date ORDER BY decision_listing_session_ordinal) FILTER (WHERE flagged) AS flag_sessions
            FROM read_parquet(?)
            WHERE (security_id, trading_item_id) IN ((?, ?), (?, ?))
            GROUP BY 1,2
            """,
            [str(flag_path), MU_IDENTITY[0], MU_IDENTITY[1], SNDK_IDENTITY[0], SNDK_IDENTITY[1]],
        ).fetchall()
        flags_by_identity = {
            (str(row[0]), str(row[1])): ([] if row[2] is None else list(map(str, row[2])))
            for row in flagged
        }
    finally:
        connection.close()

    checked = 0
    deferred = 0
    failures: list[dict[str, Any]] = []
    for proof in proofs:
        b1 = str(proof["b_minus_1_session"])
        breakout = str(proof["breakout_session"])
        identity = (str(proof["security_id"]), str(proof["trading_item_id"]))
        if b1 > development_end or breakout > pre_w6_end:
            deferred += 1
            continue
        checked += 1
        try:
            enforce_b_minus_one_pit_proof(
                pit_proof=proof,
                ordered_sessions=ordered_by_identity[identity],
                flag_sessions=flags_by_identity.get(identity, []),
            )
        except ValueError as exc:
            failures.append(
                {
                    "case_id": proof["case_id"],
                    "breakout_session": breakout,
                    "b_minus_1_session": b1,
                    "reason": str(exc),
                }
            )
    return {
        "checked_development_smoke_episode_count": checked,
        "deferred_postdevelopment_smoke_episode_count": deferred,
        "failure_count": len(failures),
        "failures": failures,
        "all_checked_pass": len(failures) == 0,
    }


def _development_survival(
    *,
    w5_summary: Mapping[str, Any],
    atlas: Mapping[str, Any],
    smoke: Mapping[str, Any],
) -> dict[str, Any]:
    winner_rows = [
        row
        for row in atlas["winner_episode_census"]
        if int(row["statistical_weight"]) == 1 and row["census_class"] in {TRUE_WINNER, MISSED_WINNER}
    ]
    effective_leads: list[int] = []
    for row in winner_rows:
        first = row.get("first_legitimate_flag_listing_session_ordinal")
        if first is None:
            effective_leads.append(0)
        else:
            effective_leads.append(int(row["breakout_listing_session_ordinal"]) - int(first))
    median_ttfld = None if not effective_leads else float(np.median(np.asarray(effective_leads, dtype=float)))
    lift_value = w5_summary.get("median_temporal_oos_recall_lift")
    lift = None if lift_value is None else float(lift_value)
    if w5_summary.get("status") == "NULL" or not winner_rows:
        status = "NULL"
    elif lift is None or lift <= 1.0 or median_ttfld is None or median_ttfld <= 0.0 or not smoke["all_checked_pass"]:
        status = "FAIL"
    else:
        status = "PASS"
    return {
        "development_survival_status": status,
        "w5_recall_lift_status": w5_summary.get("status"),
        "informative_fold_count": int(w5_summary.get("informative_fold_count", 0)),
        "median_temporal_oos_recall_lift": lift,
        "statistical_winner_episode_count": len(winner_rows),
        "median_effective_ttfld_sessions_miss_zero": median_ttfld,
        "smoke_checked_count": smoke["checked_development_smoke_episode_count"],
        "smoke_deferred_count": smoke["deferred_postdevelopment_smoke_episode_count"],
        "smoke_failure_count": smoke["failure_count"],
        "pit_or_custody_violation_count": 0,
        "w6_access_performed": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }


def run(output_dir: Path, ledger_path: Path) -> dict[str, Any]:
    precharge = _verify_precharge()
    source, authority, partition = _load_w3()
    prepared = precharge["prepared"]

    opened, ledger_entries, ledger_snapshot_sha = _open_or_reuse_trial(ledger_path, prepared)
    flag_receipt = _freeze_flags(
        output_dir=output_dir,
        source=source,
        authority=authority,
        partition=partition,
        prepared=prepared,
        code_bundle_sha256=str(precharge["code_bundle"]["code_bundle_sha256"]),
        source_manifest_sha256=str(precharge["source_manifest"]["manifest_sha256"]),
        trial_open_chain_hash=str(opened["chain_hash"]),
    )
    label_open = _materialize_postcharge_custody(
        output_dir=output_dir,
        source=source,
        authority=authority,
        partition=partition,
        label_custody=precharge["label_custody"],
        episode_custody=precharge["episode_custody"],
        flag_receipt=flag_receipt,
    )
    w5_run, w5_summary = _w5_run(
        output_dir=output_dir,
        flag_receipt=flag_receipt,
        label_open=label_open,
        partition=partition,
        source_manifest=precharge["source_manifest"],
        code_bundle=precharge["code_bundle"],
        prepared=prepared,
        ledger_entries=ledger_entries,
    )
    atlas = _w4_run(
        output_dir=output_dir,
        flag_receipt=flag_receipt,
        label_open=label_open,
        partition=partition,
        authority=authority,
        trial_open=opened,
        ledger_snapshot_sha256=ledger_snapshot_sha,
    )
    smoke = _smoke_development_checks(
        flag_path=Path(str(flag_receipt["flag_projection_path"])),
        source=source,
        partition=partition,
    )
    survival = _development_survival(w5_summary=w5_summary, atlas=atlas, smoke=smoke)

    result_body = {
        "schema_version": "prebreakout_trial1_m0_real_development_result_v1",
        "family_id": w2.FAMILY_ID,
        "trial_id": TRIAL_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "w2_contract_sha256": w2.CONTRACT_SHA256,
        "trial_open_chain_hash": opened["chain_hash"],
        "ledger_snapshot_sha256_after_open": ledger_snapshot_sha,
        "source_manifest_sha256": precharge["source_manifest"]["manifest_sha256"],
        "code_bundle_sha256": precharge["code_bundle"]["code_bundle_sha256"],
        "variant_sha256": prepared.variant_sha256,
        "flag_freeze_receipt_sha256": flag_receipt["receipt_sha256"],
        "label_open_receipt_sha256": label_open["receipt_sha256"],
        "w5_run_sha256": w5_run["run_sha256"],
        "w4_atlas_sha256": atlas["atlas_sha256"],
        "w5_summary": dict(w5_summary),
        "smoke_development": smoke,
        "survival": survival,
        "w6_lockbox_opened": False,
        "w6_labels_opened": False,
        "prospective_prediction_written": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
        "completed_at_utc": datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    }
    result = {**result_body, "result_sha256": canonical_sha256(result_body)}
    result_path = output_dir / "trial1_development_result.json"
    result_file_sha = _atomic_json(result_path, result)

    close_status = str(survival["development_survival_status"])
    if close_status not in {"PASS", "FAIL", "NULL"}:
        raise Trial1RealRunError("trial1_survival_status_invalid_for_close")
    latest_entries = load_trial_ledger(ledger_path)
    if not any(entry["event_type"] == EVENT_CLOSE and entry["payload"]["trial_id"] == TRIAL_ID for entry in latest_entries):
        append_trial_close(
            ledger_path,
            trial_id=TRIAL_ID,
            result_status=close_status,
            result_artifact_sha256=result_file_sha,
            result_summary={
                "development_survival_status": close_status,
                "median_temporal_oos_recall_lift": survival["median_temporal_oos_recall_lift"],
                "median_effective_ttfld_sessions_miss_zero": survival["median_effective_ttfld_sessions_miss_zero"],
                "statistical_winner_episode_count": survival["statistical_winner_episode_count"],
                "w6_access_performed": False,
            },
        )
    final_entries = load_trial_ledger(ledger_path)
    verify_trial_ledger(final_entries)
    if int(final_entries[-1]["cumulative_material_trials"]) != 1:
        raise Trial1RealRunError("trial1_final_material_trial_count_not_one")

    final = {
        "development_survival_status": close_status,
        "material_trials_consumed": 1,
        "trial_budget_max": w2.TRIAL_BUDGET_MAX,
        "result_sha256": result["result_sha256"],
        "result_file_sha256": result_file_sha,
        "w5_run_sha256": w5_run["run_sha256"],
        "w4_atlas_sha256": atlas["atlas_sha256"],
        "median_temporal_oos_recall_lift": survival["median_temporal_oos_recall_lift"],
        "median_effective_ttfld_sessions_miss_zero": survival["median_effective_ttfld_sessions_miss_zero"],
        "statistical_winner_episode_count": survival["statistical_winner_episode_count"],
        "smoke_failure_count": survival["smoke_failure_count"],
        "w6_lockbox_opened": False,
        "w6_labels_opened": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    _atomic_json(output_dir / "trial1_run_summary.json", final)
    return final


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--ledger-path", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verified = _verify_precharge()
        result = {
            "precharge_verified": True,
            "source_manifest_sha256": verified["source_manifest"]["manifest_sha256"],
            "code_bundle_sha256": verified["code_bundle"]["code_bundle_sha256"],
            "variant_sha256": verified["prepared"].variant_sha256,
            "trial_open_appended": False,
            "material_trials_consumed": 0,
            "w6_access_performed": False,
        }
    else:
        result = run(args.output_dir, args.ledger_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
