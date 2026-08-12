"""Hash-chained append-only prediction tape for SECTOR_ROTATION_ALPHA_v1."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.manifests import canonical_value
from research.sector_rotation_alpha_v1.contracts import FAMILY_ID, IMPLEMENTATION_ID, PREDICTION_LEDGER_SCOPE
from research.sector_rotation_alpha_v1.runner import verify_prediction_batch


LEDGER_LINK_SCHEMA = "sector_rotation_prediction_ledger_link_v1"
GENESIS_CHAIN_HASH = "0" * 64


def append_prediction_batch(
    ledger_path: str | Path,
    batch: Mapping[str, Any],
    *,
    recorded_at: datetime | str | None = None,
) -> dict[str, Any]:
    """Append one sealed ETF decision-date batch under exclusive fail-closed custody."""

    verify_prediction_batch(batch)
    path = Path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = Path(str(path) + ".lock")
    lock_fd: int | None = None
    lock_created = False
    try:
        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            lock_created = True
        except FileExistsError as exc:
            raise FileExistsError("sra_prediction_ledger_writer_lock_exists") from exc
        os.write(lock_fd, (str(batch["prediction_batch_sha256"]) + "\n").encode("utf-8"))
        os.fsync(lock_fd)

        existing = load_prediction_tape(path)
        batch_sha = str(batch["prediction_batch_sha256"])
        decision_date = str(batch["decision_session_date"])
        if any(str(entry["prediction_batch_sha256"]) == batch_sha for entry in existing):
            raise FileExistsError("sra_prediction_batch_already_in_ledger")
        if any(str(entry["decision_session_date"]) == decision_date for entry in existing):
            raise FileExistsError("sra_prediction_decision_date_already_in_ledger")

        made_at = _timestamp(batch.get("prediction_made_at"), "prediction_made_at")
        recorded = _timestamp(recorded_at or datetime.now(timezone.utc), "recorded_at")
        if recorded < made_at:
            raise ValueError("sra_prediction_ledger_recorded_before_prediction")
        if existing:
            previous_recorded = _timestamp(existing[-1]["recorded_at"], "previous_recorded_at")
            if recorded < previous_recorded:
                raise ValueError("sra_prediction_ledger_recorded_at_not_monotonic")

        previous_hash = str(existing[-1]["chain_hash"]) if existing else GENESIS_CHAIN_HASH
        prediction_ids = [str(row["prediction_id"]) for row in batch["rows"]]
        body = {
            "schema_version": LEDGER_LINK_SCHEMA,
            "sequence": len(existing),
            "previous_chain_hash": previous_hash,
            "family_id": FAMILY_ID,
            "implementation_id": IMPLEMENTATION_ID,
            "prediction_ledger_scope": PREDICTION_LEDGER_SCOPE,
            "prediction_batch_sha256": batch_sha,
            "prediction_ids": prediction_ids,
            "trial_receipt_sha256": str(batch["trial_receipt_sha256"]),
            "decision_context_id": str(batch["decision_context_id"]),
            "decision_session_date": decision_date,
            "knowledge_cutoff": str(batch["knowledge_cutoff"]),
            "prediction_made_at": str(batch["prediction_made_at"]),
            "recorded_at": _timestamp_text(recorded),
            "risk_set_count": int(batch["risk_set_count"]),
            "support_count": int(batch["support_count"]),
            "support_breadth": str(batch["support_breadth"]),
            "incumbent_support_count": int(batch["incumbent_support_count"]),
            "incumbent_support_breadth": str(batch["incumbent_support_breadth"]),
            "evaluation_status": "UNMATURED_NOT_EVALUATED",
            "batch": canonical_value(batch),
        }
        chain_hash = domain_hash(
            "SECTOR_ROTATION_ALPHA_V1:PREDICTION_LEDGER_LINK",
            canonical_value(body),
        )
        entry = {**body, "chain_hash": chain_hash}
        line = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8") + b"\n"
        fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
        try:
            if os.write(fd, line) != len(line):
                raise OSError("sra_prediction_ledger_partial_append")
            os.fsync(fd)
        finally:
            os.close(fd)

        verified = load_prediction_tape(path)
        if not verified or verified[-1] != entry:
            raise ValueError("sra_prediction_ledger_post_append_verification_failed")
        return entry
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        if lock_created and lock_path.exists():
            try:
                lock_path.unlink()
            except OSError:
                pass


def load_prediction_tape(ledger_path: str | Path) -> list[dict[str, Any]]:
    path = Path(ledger_path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    if not raw:
        return []
    if not raw.endswith(b"\n"):
        raise ValueError("sra_prediction_ledger_partial_final_line")
    entries: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(raw.splitlines(), start=1):
        if not raw_line:
            raise ValueError(f"sra_prediction_ledger_blank_line:{line_number}")
        try:
            parsed = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"sra_prediction_ledger_invalid_json:{line_number}") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"sra_prediction_ledger_entry_mapping_required:{line_number}")
        entries.append(parsed)
    verify_prediction_tape(entries)
    return entries


def verify_prediction_tape(entries: Sequence[Mapping[str, Any]]) -> None:
    previous_hash = GENESIS_CHAIN_HASH
    previous_recorded: datetime | None = None
    batch_hashes: set[str] = set()
    decision_dates: set[str] = set()
    prediction_ids_seen: set[str] = set()
    for sequence, raw in enumerate(entries):
        if not isinstance(raw, Mapping):
            raise ValueError("sra_prediction_ledger_entry_mapping_required")
        entry = dict(raw)
        chain_hash = str(entry.pop("chain_hash", ""))
        expected = domain_hash(
            "SECTOR_ROTATION_ALPHA_V1:PREDICTION_LEDGER_LINK",
            canonical_value(entry),
        )
        if chain_hash != expected:
            raise ValueError("sra_prediction_ledger_chain_hash_mismatch")
        if entry.get("schema_version") != LEDGER_LINK_SCHEMA:
            raise ValueError("sra_prediction_ledger_schema_invalid")
        if int(entry.get("sequence", -1)) != sequence:
            raise ValueError("sra_prediction_ledger_sequence_invalid")
        if entry.get("previous_chain_hash") != previous_hash:
            raise ValueError("sra_prediction_ledger_previous_hash_invalid")
        if entry.get("family_id") != FAMILY_ID or entry.get("implementation_id") != IMPLEMENTATION_ID:
            raise ValueError("sra_prediction_ledger_identity_invalid")
        if entry.get("prediction_ledger_scope") != PREDICTION_LEDGER_SCOPE:
            raise ValueError("sra_prediction_ledger_scope_invalid")
        if entry.get("evaluation_status") != "UNMATURED_NOT_EVALUATED":
            raise ValueError("sra_prediction_ledger_evaluation_status_invalid")

        batch = entry.get("batch")
        if not isinstance(batch, Mapping):
            raise ValueError("sra_prediction_ledger_batch_mapping_required")
        verify_prediction_batch(batch)
        batch_sha = str(batch["prediction_batch_sha256"])
        decision_date = str(batch["decision_session_date"])
        prediction_ids = [str(row["prediction_id"]) for row in batch["rows"]]
        for field in (
            "trial_receipt_sha256",
            "decision_context_id",
            "decision_session_date",
            "knowledge_cutoff",
            "prediction_made_at",
            "support_breadth",
            "incumbent_support_breadth",
        ):
            if str(batch[field]) != str(entry.get(field)):
                raise ValueError("sra_prediction_ledger_batch_field_mismatch:" + field)
        for field in ("risk_set_count", "support_count", "incumbent_support_count"):
            if int(batch[field]) != int(entry.get(field, -1)):
                raise ValueError("sra_prediction_ledger_batch_count_mismatch:" + field)
        if batch_sha != str(entry.get("prediction_batch_sha256")):
            raise ValueError("sra_prediction_ledger_batch_sha_mismatch")
        if prediction_ids != list(entry.get("prediction_ids") or []):
            raise ValueError("sra_prediction_ledger_prediction_ids_mismatch")
        if batch_sha in batch_hashes:
            raise ValueError("sra_prediction_ledger_duplicate_batch")
        if decision_date in decision_dates:
            raise ValueError("sra_prediction_ledger_duplicate_decision_date")
        if any(prediction_id in prediction_ids_seen for prediction_id in prediction_ids):
            raise ValueError("sra_prediction_ledger_duplicate_prediction_id")
        batch_hashes.add(batch_sha)
        decision_dates.add(decision_date)
        prediction_ids_seen.update(prediction_ids)

        made_at = _timestamp(entry.get("prediction_made_at"), "prediction_made_at")
        recorded = _timestamp(entry.get("recorded_at"), "recorded_at")
        if recorded < made_at:
            raise ValueError("sra_prediction_ledger_recorded_before_prediction")
        if previous_recorded is not None and recorded < previous_recorded:
            raise ValueError("sra_prediction_ledger_recorded_at_not_monotonic")
        previous_recorded = recorded
        previous_hash = chain_hash


def _timestamp(value: Any, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"sra_{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"sra_{field}_timezone_required")
    return parsed.astimezone(timezone.utc)


def _timestamp_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
