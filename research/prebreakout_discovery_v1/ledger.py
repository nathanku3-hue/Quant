"""Append-only charged Trial/Search Ledger for PREBREAKOUT_DISCOVERY_v1.

A material development variant is charged when TRIAL_OPEN is appended, before
its result is inspected.  TRIAL_CLOSE is a zero-cost immutable follow-up.  The
ledger is intentionally separate from the future Prediction Ledger.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import domain_hash
from research.prebreakout_discovery_v1.preregistration import (
    FAMILY_ID,
    SEARCH_FAMILY_ID,
    TRIAL_BUDGET_MAX,
    TRIAL_COST_PER_MATERIAL_VARIANT,
    TRIAL_LEDGER_SCOPE,
    hash_safe,
)


LEDGER_LINK_SCHEMA = "prebreakout_trial_ledger_link_v1"
GENESIS_CHAIN_HASH = "0" * 64
EVENT_OPEN = "TRIAL_OPEN"
EVENT_CLOSE = "TRIAL_CLOSE"
CLOSE_STATUSES = frozenset({"COMPLETE", "FAILED", "NULL", "ABORTED", "REJECTED", "SELECTED"})

_REQUIRED_VARIANT_FIELDS = (
    "implementation_id",
    "feature_spec_id",
    "transform_spec_id",
    "model_spec_id",
    "training_window_spec_id",
    "calibration_spec_id",
    "ranking_spec_id",
    "control_spec_id",
    "cross_sectional_holdout_spec_id",
    "temporal_fold_plan_id",
    "source_manifest_sha256",
    "code_sha256",
)


def append_trial_open(
    ledger_path: str | Path,
    *,
    trial_id: str,
    variant: Mapping[str, Any],
    recorded_at: datetime | str | None = None,
) -> dict[str, Any]:
    """Charge exactly one material variant before outcome-bearing inspection."""

    trial_id = _nonempty(trial_id, "trial_id")
    normalized_variant = _normalize_variant(variant)
    variant_sha256 = domain_hash("PREBREAKOUT_DISCOVERY_V1:TRIAL_VARIANT", hash_safe(normalized_variant))
    payload = {
        "trial_id": trial_id,
        "material_trial_cost": TRIAL_COST_PER_MATERIAL_VARIANT,
        "variant_sha256": variant_sha256,
        "variant": normalized_variant,
        "outcome_access_class": "DISCOVERY_DEVELOPMENT_ONLY",
        "untouched_lockbox_access": "FORBIDDEN",
        "prospective_outcome_access": "FORBIDDEN",
    }
    return _append_event(ledger_path, event_type=EVENT_OPEN, payload=payload, recorded_at=recorded_at)


def append_trial_close(
    ledger_path: str | Path,
    *,
    trial_id: str,
    result_status: str,
    result_artifact_sha256: str,
    result_summary: Mapping[str, Any] | None = None,
    recorded_at: datetime | str | None = None,
) -> dict[str, Any]:
    """Close one already charged trial without refunding or adding search budget."""

    trial_id = _nonempty(trial_id, "trial_id")
    status = str(result_status or "").strip().upper()
    if status not in CLOSE_STATUSES:
        raise ValueError("prebreakout_trial_close_status_invalid")
    result_hash = _sha256_text(result_artifact_sha256, "result_artifact_sha256")
    summary = dict(result_summary or {})
    payload = {
        "trial_id": trial_id,
        "material_trial_cost": 0,
        "result_status": status,
        "result_artifact_sha256": result_hash,
        "result_summary": summary,
    }
    return _append_event(ledger_path, event_type=EVENT_CLOSE, payload=payload, recorded_at=recorded_at)


def load_trial_ledger(ledger_path: str | Path) -> list[dict[str, Any]]:
    path = Path(ledger_path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    if not raw:
        return []
    if not raw.endswith(b"\n"):
        raise ValueError("prebreakout_trial_ledger_partial_final_line")
    entries: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(raw.splitlines(), start=1):
        if not raw_line:
            raise ValueError(f"prebreakout_trial_ledger_blank_line:{line_number}")
        try:
            parsed = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"prebreakout_trial_ledger_invalid_json:{line_number}") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"prebreakout_trial_ledger_entry_mapping_required:{line_number}")
        entries.append(parsed)
    verify_trial_ledger(entries)
    return entries


def verify_trial_ledger(entries: Sequence[Mapping[str, Any]]) -> None:
    previous_hash = GENESIS_CHAIN_HASH
    previous_recorded: datetime | None = None
    cumulative = 0
    opened: dict[str, str] = {}
    closed: set[str] = set()

    for sequence, raw in enumerate(entries):
        if not isinstance(raw, Mapping):
            raise ValueError("prebreakout_trial_ledger_entry_mapping_required")
        entry = dict(raw)
        chain_hash = str(entry.pop("chain_hash", ""))
        expected = domain_hash("PREBREAKOUT_DISCOVERY_V1:TRIAL_LEDGER_LINK", hash_safe(entry))
        if chain_hash != expected:
            raise ValueError("prebreakout_trial_ledger_chain_hash_mismatch")
        if entry.get("schema_version") != LEDGER_LINK_SCHEMA:
            raise ValueError("prebreakout_trial_ledger_schema_invalid")
        if int(entry.get("sequence", -1)) != sequence:
            raise ValueError("prebreakout_trial_ledger_sequence_invalid")
        if entry.get("previous_chain_hash") != previous_hash:
            raise ValueError("prebreakout_trial_ledger_previous_hash_invalid")
        if entry.get("family_id") != FAMILY_ID or entry.get("search_family_id") != SEARCH_FAMILY_ID:
            raise ValueError("prebreakout_trial_ledger_identity_invalid")
        if entry.get("trial_ledger_scope") != TRIAL_LEDGER_SCOPE:
            raise ValueError("prebreakout_trial_ledger_scope_invalid")
        if int(entry.get("trial_budget_max", -1)) != TRIAL_BUDGET_MAX:
            raise ValueError("prebreakout_trial_ledger_budget_identity_invalid")

        event_type = entry.get("event_type")
        payload = entry.get("payload")
        if not isinstance(payload, Mapping):
            raise ValueError("prebreakout_trial_ledger_payload_mapping_required")
        trial_id = _nonempty(payload.get("trial_id"), "trial_id")
        event_cost = int(payload.get("material_trial_cost", -1))

        if event_type == EVENT_OPEN:
            if event_cost != TRIAL_COST_PER_MATERIAL_VARIANT:
                raise ValueError("prebreakout_trial_open_cost_invalid")
            if trial_id in opened:
                raise ValueError("prebreakout_trial_duplicate_open")
            variant = payload.get("variant")
            if not isinstance(variant, Mapping):
                raise ValueError("prebreakout_trial_variant_mapping_required")
            normalized_variant = _normalize_variant(variant)
            variant_sha = domain_hash("PREBREAKOUT_DISCOVERY_V1:TRIAL_VARIANT", hash_safe(normalized_variant))
            if str(payload.get("variant_sha256") or "") != variant_sha:
                raise ValueError("prebreakout_trial_variant_hash_mismatch")
            if payload.get("outcome_access_class") != "DISCOVERY_DEVELOPMENT_ONLY":
                raise ValueError("prebreakout_trial_outcome_access_class_invalid")
            if payload.get("untouched_lockbox_access") != "FORBIDDEN" or payload.get("prospective_outcome_access") != "FORBIDDEN":
                raise ValueError("prebreakout_trial_forbidden_outcome_access_invalid")
            opened[trial_id] = variant_sha
            cumulative += event_cost
        elif event_type == EVENT_CLOSE:
            if event_cost != 0:
                raise ValueError("prebreakout_trial_close_cost_invalid")
            if trial_id not in opened:
                raise ValueError("prebreakout_trial_close_without_open")
            if trial_id in closed:
                raise ValueError("prebreakout_trial_duplicate_close")
            status = str(payload.get("result_status") or "").upper()
            if status not in CLOSE_STATUSES:
                raise ValueError("prebreakout_trial_close_status_invalid")
            _sha256_text(payload.get("result_artifact_sha256"), "result_artifact_sha256")
            if not isinstance(payload.get("result_summary"), Mapping):
                raise ValueError("prebreakout_trial_result_summary_mapping_required")
            closed.add(trial_id)
        else:
            raise ValueError("prebreakout_trial_ledger_event_type_invalid")

        if cumulative > TRIAL_BUDGET_MAX:
            raise ValueError("prebreakout_trial_budget_exceeded")
        if int(entry.get("cumulative_material_trials", -1)) != cumulative:
            raise ValueError("prebreakout_trial_ledger_cumulative_count_invalid")

        recorded = _timestamp(entry.get("recorded_at"), "recorded_at")
        if previous_recorded is not None and recorded < previous_recorded:
            raise ValueError("prebreakout_trial_ledger_recorded_at_not_monotonic")
        previous_recorded = recorded
        previous_hash = chain_hash


def _append_event(
    ledger_path: str | Path,
    *,
    event_type: str,
    payload: Mapping[str, Any],
    recorded_at: datetime | str | None,
) -> dict[str, Any]:
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
            raise FileExistsError("prebreakout_trial_ledger_writer_lock_exists") from exc
        os.write(lock_fd, (str(payload.get("trial_id")) + "\n").encode("utf-8"))
        os.fsync(lock_fd)

        existing = load_trial_ledger(path)
        trial_id = str(payload.get("trial_id"))
        if event_type == EVENT_OPEN:
            if any(entry["event_type"] == EVENT_OPEN and entry["payload"]["trial_id"] == trial_id for entry in existing):
                raise FileExistsError("prebreakout_trial_already_opened")
            current_count = _material_trial_count(existing)
            if current_count + TRIAL_COST_PER_MATERIAL_VARIANT > TRIAL_BUDGET_MAX:
                raise ValueError("prebreakout_trial_budget_exceeded")
        elif event_type == EVENT_CLOSE:
            if not any(entry["event_type"] == EVENT_OPEN and entry["payload"]["trial_id"] == trial_id for entry in existing):
                raise ValueError("prebreakout_trial_close_without_open")
            if any(entry["event_type"] == EVENT_CLOSE and entry["payload"]["trial_id"] == trial_id for entry in existing):
                raise FileExistsError("prebreakout_trial_already_closed")
        else:  # pragma: no cover - internal guard
            raise ValueError("prebreakout_trial_ledger_event_type_invalid")

        recorded = _timestamp(recorded_at or datetime.now(timezone.utc), "recorded_at")
        if existing:
            prior_recorded = _timestamp(existing[-1]["recorded_at"], "previous_recorded_at")
            if recorded < prior_recorded:
                raise ValueError("prebreakout_trial_ledger_recorded_at_not_monotonic")
        previous_hash = str(existing[-1]["chain_hash"]) if existing else GENESIS_CHAIN_HASH
        cumulative = _material_trial_count(existing) + (TRIAL_COST_PER_MATERIAL_VARIANT if event_type == EVENT_OPEN else 0)
        body = {
            "schema_version": LEDGER_LINK_SCHEMA,
            "sequence": len(existing),
            "previous_chain_hash": previous_hash,
            "family_id": FAMILY_ID,
            "search_family_id": SEARCH_FAMILY_ID,
            "trial_ledger_scope": TRIAL_LEDGER_SCOPE,
            "trial_budget_max": TRIAL_BUDGET_MAX,
            "cumulative_material_trials": cumulative,
            "event_type": event_type,
            "recorded_at": _timestamp_text(recorded),
            "payload": dict(payload),
        }
        chain_hash = domain_hash("PREBREAKOUT_DISCOVERY_V1:TRIAL_LEDGER_LINK", hash_safe(body))
        entry = {**body, "chain_hash": chain_hash}
        line = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8") + b"\n"
        fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
        try:
            if os.write(fd, line) != len(line):
                raise OSError("prebreakout_trial_ledger_partial_append")
            os.fsync(fd)
        finally:
            os.close(fd)

        verified = load_trial_ledger(path)
        if not verified or verified[-1] != entry:
            raise ValueError("prebreakout_trial_ledger_post_append_verification_failed")
        return entry
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        if lock_created and lock_path.exists():
            try:
                lock_path.unlink()
            except OSError:
                pass


def _material_trial_count(entries: Sequence[Mapping[str, Any]]) -> int:
    return sum(1 for entry in entries if entry.get("event_type") == EVENT_OPEN)


def _normalize_variant(variant: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(variant, Mapping):
        raise ValueError("prebreakout_trial_variant_mapping_required")
    normalized = dict(variant)
    for field in _REQUIRED_VARIANT_FIELDS:
        value = _nonempty(normalized.get(field), field)
        normalized[field] = value
    normalized["source_manifest_sha256"] = _sha256_text(normalized["source_manifest_sha256"], "source_manifest_sha256")
    normalized["code_sha256"] = _sha256_text(normalized["code_sha256"], "code_sha256")
    return normalized


def _nonempty(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"prebreakout_{field}_required")
    return text


def _sha256_text(value: Any, field: str) -> str:
    text = _nonempty(value, field).lower()
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise ValueError(f"prebreakout_{field}_invalid")
    return text


def _timestamp(value: Any, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"prebreakout_{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"prebreakout_{field}_timezone_required")
    return parsed.astimezone(timezone.utc)


def _timestamp_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
