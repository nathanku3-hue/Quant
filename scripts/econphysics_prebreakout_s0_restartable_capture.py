"""Restartable transport for the frozen ECONPHYSICS S0 CIQ request set.

The scientific/provider request semantics remain owned by
``aov0_capture_ciq_historical_pit_productquery.py``.  This wrapper changes only
transport custody: every completed provider batch is atomically landed with a
hash-bound receipt, and later invocations validate and skip completed batches
instead of re-querying them.

It intentionally has no winner/equity-outcome/W6/selection surface.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import UTC, datetime
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.aov0_capture_ciq_historical_pit_productquery import (
    Cdp,
    ENDPOINT,
    FILING_VERSION,
    OPTIONS,
    PERIODS,
    PERIOD_METRIC,
    PROVIDER_FUNCTION,
    SOURCE_ID,
    _extract_data,
    _fetch_expression,
    _load_master,
    _numeric_text,
    _period_end,
    _period_probe_pairs,
    _request_body,
    _requested_transition_metrics,
    _scalar_request,
)


TRANSPORT_SCHEMA = "econphysics_s0_restartable_transport_v1"
SHARD_RECEIPT_SCHEMA = "econphysics_s0_restartable_provider_batch_receipt_v1"
PERIOD_FINAL_RECEIPT_SCHEMA = "econphysics_s0_restartable_period_matrix_receipt_v1"
TRANSITION_FINAL_RECEIPT_SCHEMA = "econphysics_s0_restartable_transition_receipt_v1"
FROZEN_CAPTURE_SCRIPT = Path("scripts/aov0_capture_ciq_historical_pit_productquery.py")


class RestartableCaptureError(ValueError):
    """Fail-closed transport/custody error."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            raise FileExistsError(f"econphysics_s0_restartable_output_exists:{path}")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def _atomic_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise RestartableCaptureError("econphysics_s0_restartable_rows_empty")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            raise FileExistsError(f"econphysics_s0_restartable_output_exists:{path}")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _stable_manifest(
    *,
    mode: str,
    plan_path: Path,
    master_path: Path,
    batch_requests: int,
    total_units: int,
    total_provider_requests: int,
    total_batches: int,
    metrics: Sequence[str],
) -> dict[str, object]:
    return {
        "schema_version": TRANSPORT_SCHEMA,
        "mode": mode,
        "source_id": SOURCE_ID,
        "provider_endpoint": ENDPOINT,
        "provider_function": PROVIDER_FUNCTION,
        "options": OPTIONS,
        "filing_version": FILING_VERSION,
        "plan_path": plan_path.as_posix(),
        "plan_sha256": _sha256(plan_path),
        "master_path": master_path.as_posix(),
        "master_sha256": _sha256(master_path),
        "batch_requests": int(batch_requests),
        "total_units": int(total_units),
        "total_provider_requests": int(total_provider_requests),
        "total_batches": int(total_batches),
        "metrics": list(metrics),
        "relative_periods": ["FQ0"] if mode == "PERIOD_MATRIX" else list(PERIODS),
        "frozen_capture_script_sha256": _sha256(FROZEN_CAPTURE_SCRIPT),
        "transport_script_sha256": _sha256(Path(__file__)),
        "restart_law": "VALIDATE_AND_SKIP_COMPLETE_SHARDS; NEVER_REQUERY_VALID_COMPLETE_SHARD",
    }


def _ensure_manifest(transport_dir: Path, expected: Mapping[str, object]) -> Path:
    path = transport_dir / "transport_manifest.json"
    if path.exists():
        actual = json.loads(path.read_text(encoding="utf-8"))
        if actual != dict(expected):
            raise RestartableCaptureError("econphysics_s0_restartable_transport_manifest_drift")
        return path
    transport_dir.mkdir(parents=True, exist_ok=True)
    _atomic_text(path, json.dumps(dict(expected), indent=2, sort_keys=True) + "\n")
    return path


def _shard_paths(transport_dir: Path, *, mode: str, batch_index: int) -> tuple[Path, Path]:
    stem = ("period" if mode == "PERIOD_MATRIX" else "transition") + f"_batch_{batch_index:06d}"
    data_path = transport_dir / "shards" / f"{stem}.csv"
    receipt_path = transport_dir / "shards" / f"{stem}.receipt.json"
    return data_path, receipt_path


def _request_key_period(date: pd.Timestamp, entity: str) -> str:
    return f"{date.date().isoformat()}|{entity}|{PERIOD_METRIC}|FQ0"


def _request_key_transition(entity: str, date: pd.Timestamp, period: str, metric: str) -> str:
    return f"{date.date().isoformat()}|{entity}|{metric}|{period}"


def _validate_shard_receipt(
    *,
    receipt: Mapping[str, object],
    data_path: Path,
    manifest: Mapping[str, object],
    batch_index: int,
    unit_start: int,
    unit_end: int,
    provider_request_count: int,
    first_request_key: str,
    last_request_key: str,
) -> None:
    expected = {
        "schema_version": SHARD_RECEIPT_SCHEMA,
        "mode": manifest["mode"],
        "batch_index": batch_index,
        "unit_start_offset": unit_start,
        "unit_end_offset_exclusive": unit_end,
        "provider_request_count": provider_request_count,
        "first_request_key": first_request_key,
        "last_request_key": last_request_key,
        "plan_sha256": manifest["plan_sha256"],
        "master_sha256": manifest["master_sha256"],
        "frozen_capture_script_sha256": manifest["frozen_capture_script_sha256"],
        "transport_script_sha256": manifest["transport_script_sha256"],
        "filing_version": FILING_VERSION,
        "options": OPTIONS,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise RestartableCaptureError(f"econphysics_s0_restartable_shard_receipt_drift:{batch_index}:{key}")
    if receipt.get("raw_object_sha256") != _sha256(data_path):
        raise RestartableCaptureError(f"econphysics_s0_restartable_shard_hash_mismatch:{batch_index}")
    if int(receipt.get("raw_object_rows") or -1) <= 0:
        raise RestartableCaptureError(f"econphysics_s0_restartable_shard_rows_invalid:{batch_index}")


async def _fetch_provider_batch(cdp: Cdp, payloads: list[dict[str, object]]) -> dict[int, object]:
    value = await cdp.evaluate(_fetch_expression(_request_body(payloads)))
    if not isinstance(value, dict):
        raise RestartableCaptureError("econphysics_s0_restartable_transport_result_invalid")
    if int(value.get("status", -1)) != 200:
        raise RestartableCaptureError(
            f"econphysics_s0_restartable_http:{value.get('status')}:{str(value.get('body'))[:1000]}"
        )
    body = value.get("body")
    if not isinstance(body, dict):
        raise RestartableCaptureError("econphysics_s0_restartable_body_invalid")
    responses = body.get("responses")
    if not isinstance(responses, list) or len(responses) != len(payloads):
        raise RestartableCaptureError(
            f"econphysics_s0_restartable_response_count_invalid:{len(responses or [])}/{len(payloads)}"
        )
    output: dict[int, object] = {}
    for response in responses:
        if not isinstance(response, dict):
            raise RestartableCaptureError("econphysics_s0_restartable_response_invalid")
        response_id = int(response.get("id"))
        if response_id in output:
            raise RestartableCaptureError(f"econphysics_s0_restartable_duplicate_response_id:{response_id}")
        output[response_id] = _extract_data(response)
    if len(output) != len(payloads):
        raise RestartableCaptureError("econphysics_s0_restartable_batch_incomplete")
    return output


def _existing_pair_state(data_path: Path, receipt_path: Path) -> bool:
    if data_path.exists() != receipt_path.exists():
        raise RestartableCaptureError(f"econphysics_s0_restartable_partial_shard:{data_path.name}")
    return data_path.exists()


def _period_batch_spec(
    pairs: Sequence[tuple[pd.Timestamp, str]], batch_requests: int, batch_index: int
) -> tuple[int, int, list[tuple[pd.Timestamp, str]]]:
    start = batch_index * batch_requests
    end = min(len(pairs), start + batch_requests)
    return start, end, list(pairs[start:end])


def _transition_batch_spec(
    pairs: Sequence[tuple[str, pd.Timestamp]], metrics: Sequence[str], batch_requests: int, batch_index: int
) -> tuple[int, int, list[tuple[str, pd.Timestamp]], int]:
    requests_per_transition = len(PERIODS) * len(metrics)
    units_per_batch = max(1, batch_requests // requests_per_transition)
    start = batch_index * units_per_batch
    end = min(len(pairs), start + units_per_batch)
    batch = list(pairs[start:end])
    return start, end, batch, len(batch) * requests_per_transition


def _period_shard_rows(
    batch: Sequence[tuple[pd.Timestamp, str]], values: Mapping[int, object], *, request_id_start: int, retrieved_at: str
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for offset, (date, entity) in enumerate(batch):
        request_id = request_id_start + offset
        rows.append(
            {
                "as_of_date": date.date().isoformat(),
                "source_entity_id": entity,
                "fq0_period_end": _period_end(values[request_id]),
                "retrieved_at_utc": retrieved_at,
                "provider_function": PROVIDER_FUNCTION,
                "provider_metric": PERIOD_METRIC,
                "relative_period": "FQ0",
                "filing_version": FILING_VERSION,
            }
        )
    return rows


def _transition_shard_rows(
    batch: Sequence[tuple[str, pd.Timestamp]],
    metrics: Sequence[str],
    values: Mapping[int, object],
    *,
    request_id_start: int,
    retrieved_at: str,
) -> list[dict[str, object]]:
    request_id = request_id_start
    rows: list[dict[str, object]] = []
    for entity, date in batch:
        for period in PERIODS:
            row: dict[str, object] = {
                "as_of_date": date.date().isoformat(),
                "source_entity_id": entity,
                "relative_period": period,
                "period_end": "",
                **{metric: "" for metric in metrics if metric != PERIOD_METRIC},
                "retrieved_at_utc": retrieved_at,
                "provider_function": PROVIDER_FUNCTION,
                "filing_version": FILING_VERSION,
            }
            for metric in metrics:
                raw = values[request_id]
                if metric == PERIOD_METRIC:
                    row["period_end"] = _period_end(raw)
                else:
                    row[metric] = _numeric_text(raw)
                request_id += 1
            rows.append(row)
    return rows


def _write_shard(
    *,
    data_path: Path,
    receipt_path: Path,
    rows: Sequence[Mapping[str, object]],
    manifest: Mapping[str, object],
    batch_index: int,
    unit_start: int,
    unit_end: int,
    provider_request_count: int,
    first_request_key: str,
    last_request_key: str,
    retrieved_at: str,
) -> None:
    _atomic_csv(data_path, rows)
    receipt = {
        "schema_version": SHARD_RECEIPT_SCHEMA,
        "mode": manifest["mode"],
        "batch_index": batch_index,
        "unit_start_offset": unit_start,
        "unit_end_offset_exclusive": unit_end,
        "provider_request_count": provider_request_count,
        "first_request_key": first_request_key,
        "last_request_key": last_request_key,
        "plan_sha256": manifest["plan_sha256"],
        "master_sha256": manifest["master_sha256"],
        "frozen_capture_script_sha256": manifest["frozen_capture_script_sha256"],
        "transport_script_sha256": manifest["transport_script_sha256"],
        "filing_version": FILING_VERSION,
        "options": OPTIONS,
        "captured_at_utc": retrieved_at,
        "raw_object_name": data_path.name,
        "raw_object_sha256": _sha256(data_path),
        "raw_object_rows": len(rows),
        "financial_alpha_evidence": 0,
        "winner_or_equity_outcome_access_performed": False,
        "w6_access_performed": False,
        "selection_performed": False,
    }
    _atomic_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")


def _verify_period_shard(
    *,
    data_path: Path,
    receipt_path: Path,
    manifest: Mapping[str, object],
    batch_index: int,
    unit_start: int,
    unit_end: int,
    batch: Sequence[tuple[pd.Timestamp, str]],
) -> list[dict[str, str]]:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    _validate_shard_receipt(
        receipt=receipt,
        data_path=data_path,
        manifest=manifest,
        batch_index=batch_index,
        unit_start=unit_start,
        unit_end=unit_end,
        provider_request_count=len(batch),
        first_request_key=_request_key_period(*batch[0]),
        last_request_key=_request_key_period(*batch[-1]),
    )
    rows = _load_csv(data_path)
    if len(rows) != len(batch):
        raise RestartableCaptureError(f"econphysics_s0_restartable_period_shard_row_count:{batch_index}")
    for row, (date, entity) in zip(rows, batch):
        if row.get("as_of_date") != date.date().isoformat() or row.get("source_entity_id") != entity:
            raise RestartableCaptureError(f"econphysics_s0_restartable_period_shard_membership:{batch_index}")
        if (
            row.get("provider_function") != PROVIDER_FUNCTION
            or row.get("provider_metric") != PERIOD_METRIC
            or row.get("relative_period") != "FQ0"
            or row.get("filing_version") != FILING_VERSION
        ):
            raise RestartableCaptureError(f"econphysics_s0_restartable_period_shard_semantics:{batch_index}")
    return rows


def _verify_transition_shard(
    *,
    data_path: Path,
    receipt_path: Path,
    manifest: Mapping[str, object],
    batch_index: int,
    unit_start: int,
    unit_end: int,
    batch: Sequence[tuple[str, pd.Timestamp]],
    metrics: Sequence[str],
) -> list[dict[str, str]]:
    request_count = len(batch) * len(PERIODS) * len(metrics)
    first = _request_key_transition(batch[0][0], batch[0][1], PERIODS[0], metrics[0])
    last = _request_key_transition(batch[-1][0], batch[-1][1], PERIODS[-1], metrics[-1])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    _validate_shard_receipt(
        receipt=receipt,
        data_path=data_path,
        manifest=manifest,
        batch_index=batch_index,
        unit_start=unit_start,
        unit_end=unit_end,
        provider_request_count=request_count,
        first_request_key=first,
        last_request_key=last,
    )
    rows = _load_csv(data_path)
    expected_rows = len(batch) * len(PERIODS)
    if len(rows) != expected_rows:
        raise RestartableCaptureError(f"econphysics_s0_restartable_transition_shard_row_count:{batch_index}")
    cursor = 0
    for entity, date in batch:
        for period in PERIODS:
            row = rows[cursor]
            cursor += 1
            if (
                row.get("as_of_date") != date.date().isoformat()
                or row.get("source_entity_id") != entity
                or row.get("relative_period") != period
                or row.get("provider_function") != PROVIDER_FUNCTION
                or row.get("filing_version") != FILING_VERSION
            ):
                raise RestartableCaptureError(f"econphysics_s0_restartable_transition_shard_membership:{batch_index}")
            for metric in metrics:
                if metric != PERIOD_METRIC and metric not in row:
                    raise RestartableCaptureError(
                        f"econphysics_s0_restartable_transition_shard_metric_missing:{batch_index}:{metric}"
                    )
    return rows


def _final_receipt(
    *,
    schema: str,
    out: Path,
    manifest: Mapping[str, object],
    transport_manifest_path: Path,
    raw_rows: int,
    extra: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": schema,
        "source_id": SOURCE_ID,
        "provider": "S&P Capital IQ Pro authenticated existing web session",
        "capture_mode": manifest["mode"],
        "transport_mode": "RESTARTABLE_ATOMIC_PROVIDER_BATCH_SHARDS_V1",
        "provider_endpoint": ENDPOINT,
        "provider_function": PROVIDER_FUNCTION,
        "filing_version": FILING_VERSION,
        "options": OPTIONS,
        "raw_object_name": out.name,
        "raw_object_sha256": _sha256(out),
        "raw_object_bytes": out.stat().st_size,
        "raw_grid_rows": raw_rows,
        "source_plan_name": Path(str(manifest["plan_path"])).name,
        "source_plan_sha256": manifest["plan_sha256"],
        "master_name": Path(str(manifest["master_path"])).name,
        "master_sha256": manifest["master_sha256"],
        "transport_manifest_sha256": _sha256(transport_manifest_path),
        "transport_batch_count": manifest["total_batches"],
        "provider_request_count": manifest["total_provider_requests"],
        "existing_session_reused": True,
        "sign_in_performed": False,
        "sign_out_performed": False,
        "financial_alpha_evidence": 0,
        "winner_or_equity_outcome_access_performed": False,
        "w6_access_performed": False,
        "selection_performed": False,
        **dict(extra),
    }


def _ensure_final_pair(out: Path) -> tuple[bool, Path]:
    receipt = out.with_suffix(".receipt.json")
    if out.exists() != receipt.exists():
        raise RestartableCaptureError("econphysics_s0_restartable_partial_final_output")
    return out.exists(), receipt


async def capture_period_matrix(args: argparse.Namespace) -> None:
    plan_path = Path(args.plan)
    master_path = Path(args.master)
    out = Path(args.out)
    transport_dir = Path(args.transport_dir)
    plan = pd.read_csv(plan_path, dtype=str).fillna("")
    master = _load_master(master_path)
    pairs, plan_mode = _period_probe_pairs(plan, master)
    if not pairs:
        raise RestartableCaptureError("econphysics_s0_restartable_period_plan_empty")
    total_batches = math.ceil(len(pairs) / args.batch_requests)
    manifest = _stable_manifest(
        mode="PERIOD_MATRIX",
        plan_path=plan_path,
        master_path=master_path,
        batch_requests=args.batch_requests,
        total_units=len(pairs),
        total_provider_requests=len(pairs),
        total_batches=total_batches,
        metrics=[PERIOD_METRIC],
    )
    manifest_path = _ensure_manifest(transport_dir, manifest)
    final_exists, final_receipt_path = _ensure_final_pair(out)
    if final_exists:
        final_receipt = json.loads(final_receipt_path.read_text(encoding="utf-8"))
        if final_receipt.get("raw_object_sha256") != _sha256(out):
            raise RestartableCaptureError("econphysics_s0_restartable_final_hash_mismatch")
        print(f"PERIOD_MATRIX_RESTARTABLE_ALREADY_COMPLETE\tPAIRS={len(pairs)}\tPATH={out}", flush=True)
        return

    fetched = 0
    complete = 0
    cdp: Cdp | None = None
    try:
        for batch_index in range(total_batches):
            start, end, batch = _period_batch_spec(pairs, args.batch_requests, batch_index)
            data_path, receipt_path = _shard_paths(transport_dir, mode="PERIOD_MATRIX", batch_index=batch_index)
            if _existing_pair_state(data_path, receipt_path):
                _verify_period_shard(
                    data_path=data_path,
                    receipt_path=receipt_path,
                    manifest=manifest,
                    batch_index=batch_index,
                    unit_start=start,
                    unit_end=end,
                    batch=batch,
                )
                complete += 1
                continue
            if args.max_batches is not None and fetched >= args.max_batches:
                continue
            if cdp is None:
                cdp = await Cdp(args.port).__aenter__()
            request_id_start = start + 1
            payloads = [
                _scalar_request(
                    request_id_start + offset,
                    entity=entity,
                    metric=PERIOD_METRIC,
                    period="FQ0",
                    as_of=date.date().isoformat(),
                )
                for offset, (date, entity) in enumerate(batch)
            ]
            values = await _fetch_provider_batch(cdp, payloads)
            retrieved_at = datetime.now(UTC).isoformat()
            rows = _period_shard_rows(batch, values, request_id_start=request_id_start, retrieved_at=retrieved_at)
            missing = sum(not str(row["fq0_period_end"]) for row in rows)
            if missing and not args.allow_missing_period_end:
                raise RestartableCaptureError(
                    f"econphysics_s0_restartable_period_missing_not_allowed:batch={batch_index}:count={missing}"
                )
            _write_shard(
                data_path=data_path,
                receipt_path=receipt_path,
                rows=rows,
                manifest=manifest,
                batch_index=batch_index,
                unit_start=start,
                unit_end=end,
                provider_request_count=len(batch),
                first_request_key=_request_key_period(*batch[0]),
                last_request_key=_request_key_period(*batch[-1]),
                retrieved_at=retrieved_at,
            )
            fetched += 1
            complete += 1
            print(
                f"S0_PERIOD_SHARD_OK\tBATCH={batch_index}\tPAIRS={len(batch)}\tMISSING_FQ0={missing}"
                f"\tCOMPLETE={complete}/{total_batches}",
                flush=True,
            )
    finally:
        if cdp is not None:
            await cdp.__aexit__(None, None, None)

    all_rows: list[dict[str, str]] = []
    missing_total = 0
    for batch_index in range(total_batches):
        start, end, batch = _period_batch_spec(pairs, args.batch_requests, batch_index)
        data_path, receipt_path = _shard_paths(transport_dir, mode="PERIOD_MATRIX", batch_index=batch_index)
        if not _existing_pair_state(data_path, receipt_path):
            continue
        rows = _verify_period_shard(
            data_path=data_path,
            receipt_path=receipt_path,
            manifest=manifest,
            batch_index=batch_index,
            unit_start=start,
            unit_end=end,
            batch=batch,
        )
        all_rows.extend(rows)
        missing_total += sum(not row.get("fq0_period_end") for row in rows)
    completed_batches = sum(
        1
        for batch_index in range(total_batches)
        if _shard_paths(transport_dir, mode="PERIOD_MATRIX", batch_index=batch_index)[0].exists()
        and _shard_paths(transport_dir, mode="PERIOD_MATRIX", batch_index=batch_index)[1].exists()
    )
    if completed_batches != total_batches:
        print(
            f"PERIOD_MATRIX_RESTARTABLE_PARTIAL\tCOMPLETE_BATCHES={completed_batches}/{total_batches}"
            f"\tPAIRS_LANDED={len(all_rows)}/{len(pairs)}\tNEW_BATCHES={fetched}",
            flush=True,
        )
        return
    if len(all_rows) != len(pairs):
        raise RestartableCaptureError("econphysics_s0_restartable_period_merge_count_mismatch")
    _atomic_csv(out, all_rows)
    receipt = _final_receipt(
        schema=PERIOD_FINAL_RECEIPT_SCHEMA,
        out=out,
        manifest=manifest,
        transport_manifest_path=manifest_path,
        raw_rows=len(all_rows),
        extra={
            "period_probe_plan_mode": plan_mode,
            "probe_pair_count": len(pairs),
            "weekly_date_count": len({date for date, _ in pairs}),
            "entity_count": len({entity for _, entity in pairs}),
            "provider_metric": PERIOD_METRIC,
            "relative_period": "FQ0",
            "missing_fq0_period_end_count": missing_total,
            "missing_fq0_period_end_allowed": bool(args.allow_missing_period_end),
            "restart_duplicate_prevention": "COMPLETE_SHARD_HASH_AND_MEMBERSHIP_VALIDATION_BEFORE_PROVIDER_ACCESS",
        },
    )
    _atomic_text(final_receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        f"PERIOD_MATRIX_RESTARTABLE_COMPLETE\tPAIRS={len(pairs)}\tMISSING_FQ0={missing_total}"
        f"\tSHA256={_sha256(out)}\tPATH={out}",
        flush=True,
    )


async def capture_transitions(args: argparse.Namespace) -> None:
    plan_path = Path(args.plan)
    master_path = Path(args.master)
    out = Path(args.out)
    transport_dir = Path(args.transport_dir)
    plan = pd.read_csv(plan_path, dtype=str).fillna("")
    master = _load_master(master_path)
    required = {"source_entity_id", "as_of_date"}
    if plan.empty or not required.issubset(plan.columns):
        raise RestartableCaptureError("econphysics_s0_restartable_transition_plan_invalid")
    valid_entities = set(master["SP_ENTITY_ID"].tolist())
    pairs: list[tuple[str, pd.Timestamp]] = []
    seen: set[tuple[str, pd.Timestamp]] = set()
    for row in plan.itertuples(index=False):
        entity = str(row.source_entity_id).strip()
        date = pd.Timestamp(row.as_of_date).normalize()
        if entity not in valid_entities:
            raise RestartableCaptureError(f"econphysics_s0_restartable_transition_entity_outside_master:{entity}")
        key = (entity, date)
        if key in seen:
            raise RestartableCaptureError(f"econphysics_s0_restartable_transition_duplicate:{entity}:{date.date()}")
        seen.add(key)
        pairs.append(key)
    pairs.sort(key=lambda item: (item[1], int(item[0])))
    metrics = _requested_transition_metrics(args)
    requests_per_transition = len(PERIODS) * len(metrics)
    if args.batch_requests < requests_per_transition:
        raise RestartableCaptureError(
            f"econphysics_s0_restartable_batch_too_small_for_transition:{args.batch_requests}<{requests_per_transition}"
        )
    units_per_batch = max(1, args.batch_requests // requests_per_transition)
    total_batches = math.ceil(len(pairs) / units_per_batch)
    total_provider_requests = len(pairs) * requests_per_transition
    manifest = _stable_manifest(
        mode="TRANSITIONS",
        plan_path=plan_path,
        master_path=master_path,
        batch_requests=args.batch_requests,
        total_units=len(pairs),
        total_provider_requests=total_provider_requests,
        total_batches=total_batches,
        metrics=metrics,
    )
    manifest_path = _ensure_manifest(transport_dir, manifest)
    final_exists, final_receipt_path = _ensure_final_pair(out)
    if final_exists:
        final_receipt = json.loads(final_receipt_path.read_text(encoding="utf-8"))
        if final_receipt.get("raw_object_sha256") != _sha256(out):
            raise RestartableCaptureError("econphysics_s0_restartable_transition_final_hash_mismatch")
        print(f"TRANSITIONS_RESTARTABLE_ALREADY_COMPLETE\tTRANSITIONS={len(pairs)}\tPATH={out}", flush=True)
        return

    fetched = 0
    cdp: Cdp | None = None
    try:
        for batch_index in range(total_batches):
            start, end, batch, request_count = _transition_batch_spec(pairs, metrics, args.batch_requests, batch_index)
            data_path, receipt_path = _shard_paths(transport_dir, mode="TRANSITIONS", batch_index=batch_index)
            if _existing_pair_state(data_path, receipt_path):
                _verify_transition_shard(
                    data_path=data_path,
                    receipt_path=receipt_path,
                    manifest=manifest,
                    batch_index=batch_index,
                    unit_start=start,
                    unit_end=end,
                    batch=batch,
                    metrics=metrics,
                )
                continue
            if args.max_batches is not None and fetched >= args.max_batches:
                continue
            if cdp is None:
                cdp = await Cdp(args.port).__aenter__()
            request_id_start = start * requests_per_transition + 1
            request_id = request_id_start
            payloads: list[dict[str, object]] = []
            for entity, date in batch:
                for period in PERIODS:
                    for metric in metrics:
                        payloads.append(
                            _scalar_request(
                                request_id,
                                entity=entity,
                                metric=metric,
                                period=period,
                                as_of=date.date().isoformat(),
                            )
                        )
                        request_id += 1
            if len(payloads) != request_count or len(payloads) > args.batch_requests:
                raise RestartableCaptureError("econphysics_s0_restartable_transition_batch_shape_invalid")
            values = await _fetch_provider_batch(cdp, payloads)
            retrieved_at = datetime.now(UTC).isoformat()
            rows = _transition_shard_rows(
                batch,
                metrics,
                values,
                request_id_start=request_id_start,
                retrieved_at=retrieved_at,
            )
            fq0_missing = [row for row in rows if row["relative_period"] == "FQ0" and not row["period_end"]]
            if fq0_missing:
                first = fq0_missing[0]
                raise RestartableCaptureError(
                    "econphysics_s0_restartable_transition_fq0_missing:"
                    f"{first['source_entity_id']}:{first['as_of_date']}:count={len(fq0_missing)}"
                )
            first_key = _request_key_transition(batch[0][0], batch[0][1], PERIODS[0], metrics[0])
            last_key = _request_key_transition(batch[-1][0], batch[-1][1], PERIODS[-1], metrics[-1])
            _write_shard(
                data_path=data_path,
                receipt_path=receipt_path,
                rows=rows,
                manifest=manifest,
                batch_index=batch_index,
                unit_start=start,
                unit_end=end,
                provider_request_count=request_count,
                first_request_key=first_key,
                last_request_key=last_key,
                retrieved_at=retrieved_at,
            )
            fetched += 1
            print(
                f"S0_TRANSITION_SHARD_OK\tBATCH={batch_index}\tTRANSITIONS={len(batch)}"
                f"\tREQUESTS={request_count}\tCOMPLETE_HINT={batch_index + 1}/{total_batches}",
                flush=True,
            )
    finally:
        if cdp is not None:
            await cdp.__aexit__(None, None, None)

    completed_batches = 0
    all_rows: list[dict[str, str]] = []
    for batch_index in range(total_batches):
        start, end, batch, _ = _transition_batch_spec(pairs, metrics, args.batch_requests, batch_index)
        data_path, receipt_path = _shard_paths(transport_dir, mode="TRANSITIONS", batch_index=batch_index)
        if not _existing_pair_state(data_path, receipt_path):
            continue
        rows = _verify_transition_shard(
            data_path=data_path,
            receipt_path=receipt_path,
            manifest=manifest,
            batch_index=batch_index,
            unit_start=start,
            unit_end=end,
            batch=batch,
            metrics=metrics,
        )
        completed_batches += 1
        all_rows.extend(rows)
    if completed_batches != total_batches:
        print(
            f"TRANSITIONS_RESTARTABLE_PARTIAL\tCOMPLETE_BATCHES={completed_batches}/{total_batches}"
            f"\tTRANSITIONS_LANDED={len(all_rows)//len(PERIODS)}/{len(pairs)}\tNEW_BATCHES={fetched}",
            flush=True,
        )
        return
    expected_rows = len(pairs) * len(PERIODS)
    if len(all_rows) != expected_rows:
        raise RestartableCaptureError("econphysics_s0_restartable_transition_merge_count_mismatch")
    _atomic_csv(out, all_rows)
    receipt = _final_receipt(
        schema=TRANSITION_FINAL_RECEIPT_SCHEMA,
        out=out,
        manifest=manifest,
        transport_manifest_path=manifest_path,
        raw_rows=len(all_rows),
        extra={
            "transition_count": len(pairs),
            "relative_periods": list(PERIODS),
            "metrics": list(metrics),
            "restart_duplicate_prevention": "COMPLETE_SHARD_HASH_AND_MEMBERSHIP_VALIDATION_BEFORE_PROVIDER_ACCESS",
        },
    )
    _atomic_text(final_receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        f"TRANSITIONS_RESTARTABLE_COMPLETE\tTRANSITIONS={len(pairs)}\tROWS={len(all_rows)}"
        f"\tSHA256={_sha256(out)}\tPATH={out}",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=9230)
    parser.add_argument("--batch-requests", type=int, default=200)
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
        help="Fetch at most this many missing provider batches in this invocation; completed shards are always validated/skipped.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    period = sub.add_parser("period-matrix")
    period.add_argument("--plan", required=True)
    period.add_argument("--master", required=True)
    period.add_argument("--out", required=True)
    period.add_argument("--transport-dir", required=True)
    period.add_argument("--allow-missing-period-end", action="store_true")

    transitions = sub.add_parser("transitions")
    transitions.add_argument("--plan", required=True)
    transitions.add_argument("--master", required=True)
    transitions.add_argument("--out", required=True)
    transitions.add_argument("--transport-dir", required=True)
    transitions.add_argument(
        "--metric",
        action="append",
        help="Repeat to restrict capture to the same allowed metric subset as the frozen provider request script.",
    )

    args = parser.parse_args()
    if args.batch_requests < 1 or args.batch_requests > 500:
        raise RestartableCaptureError("econphysics_s0_restartable_batch_requests_out_of_range:1..500")
    if args.max_batches is not None and args.max_batches < 1:
        raise RestartableCaptureError("econphysics_s0_restartable_max_batches_positive")
    if args.command == "period-matrix":
        asyncio.run(capture_period_matrix(args))
    else:
        asyncio.run(capture_transitions(args))


if __name__ == "__main__":
    main()
