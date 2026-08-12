"""One-budget append-only Trial/Search custody for SECTOR_ROTATION_ALPHA_v1 M0."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from core.gv_fs0_canonical import assert_sha256, domain_hash
from research.alpha_pit_v1.manifests import canonical_value
from research.sector_rotation_alpha_v1.contracts import (
    FAMILY_ID,
    IMPLEMENTATION_ID,
    MECHANISM_FALSIFIERS,
    SEARCH_FAMILY_ID,
    TRIAL_BUDGET_MAX,
    TRIAL_LEDGER_SCOPE,
    TRIAL_RECEIPT_SCHEMA,
    validate_sector_rotation_contract,
)


CODE_MANIFEST_SCHEMA = "sra_m0_executable_code_manifest_v1"
CODE_MANIFEST_PATHS = (
    "core/gv_fs0_canonical.py",
    "research/aov0/contracts.py",
    "research/alpha_pit_v1/contracts.py",
    "research/alpha_pit_v1/manifests.py",
    "research/alpha_pit_v1/session.py",
    "research/sector_rotation_alpha_v1/contracts.py",
    "research/sector_rotation_alpha_v1/features.py",
    "research/sector_rotation_alpha_v1/ledger.py",
    "research/sector_rotation_alpha_v1/model.py",
    "research/sector_rotation_alpha_v1/pit_packet.py",
    "research/sector_rotation_alpha_v1/runner.py",
    "research/sector_rotation_alpha_v1/source.py",
    "research/sector_rotation_alpha_v1/trial_ledger.py",
)


def build_code_manifest(repo_root: str | Path) -> dict[str, Any]:
    """Hash the exact W8 executable surface and its narrow shared PIT dependencies."""

    root = Path(repo_root)
    file_sha256s: dict[str, str] = {}
    for relative in CODE_MANIFEST_PATHS:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError("sra_code_manifest_file_missing:" + relative)
        file_sha256s[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    body = {
        "schema_version": CODE_MANIFEST_SCHEMA,
        "family_id": FAMILY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "file_sha256s": file_sha256s,
    }
    return {
        **body,
        "code_manifest_sha256": domain_hash(
            "SECTOR_ROTATION_ALPHA_V1:CODE_MANIFEST",
            canonical_value(body),
        ),
    }


def verify_code_manifest(manifest: Mapping[str, Any], *, repo_root: str | Path | None = None) -> None:
    if not isinstance(manifest, Mapping):
        raise ValueError("sra_code_manifest_mapping_required")
    if manifest.get("schema_version") != CODE_MANIFEST_SCHEMA:
        raise ValueError("sra_code_manifest_schema_invalid")
    if manifest.get("family_id") != FAMILY_ID or manifest.get("implementation_id") != IMPLEMENTATION_ID:
        raise ValueError("sra_code_manifest_identity_invalid")
    file_sha256s = manifest.get("file_sha256s")
    if not isinstance(file_sha256s, Mapping) or tuple(sorted(map(str, file_sha256s))) != tuple(sorted(CODE_MANIFEST_PATHS)):
        raise ValueError("sra_code_manifest_path_set_invalid")
    for relative in CODE_MANIFEST_PATHS:
        assert_sha256(str(file_sha256s.get(relative) or ""))
    sealed = str(manifest.get("code_manifest_sha256") or "")
    body = {key: value for key, value in manifest.items() if key != "code_manifest_sha256"}
    expected = domain_hash("SECTOR_ROTATION_ALPHA_V1:CODE_MANIFEST", canonical_value(body))
    if sealed != expected:
        raise ValueError("sra_code_manifest_hash_mismatch")
    if repo_root is not None:
        current = build_code_manifest(repo_root)
        if canonical_value(current) != canonical_value(manifest):
            raise ValueError("sra_code_manifest_current_bytes_mismatch")


def build_trial_receipt(*, code_manifest: Mapping[str, Any], created_at: datetime) -> dict[str, Any]:
    """Freeze the sole material M0 trial before any result-bearing evaluation."""

    validate_sector_rotation_contract()
    verify_code_manifest(code_manifest)
    stamp = _timestamp(created_at, "created_at")
    body = {
        "schema_version": TRIAL_RECEIPT_SCHEMA,
        "family_id": FAMILY_ID,
        "search_family_id": SEARCH_FAMILY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "trial_ledger_scope": TRIAL_LEDGER_SCOPE,
        "trial_number": 1,
        "trial_budget_max": TRIAL_BUDGET_MAX,
        "material_trials_consumed": 1,
        "code_manifest_sha256": str(code_manifest["code_manifest_sha256"]),
        "code_manifest": canonical_value(code_manifest),
        "falsifiers": list(MECHANISM_FALSIFIERS),
        "outcome_accessed": False,
        "status": "PREREGISTERED_NOT_EVALUATED",
        "created_at": _timestamp_text(stamp),
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    return {
        **body,
        "trial_receipt_sha256": domain_hash(
            "SECTOR_ROTATION_ALPHA_V1:TRIAL_RECEIPT",
            canonical_value(body),
        ),
    }


def verify_trial_receipt(receipt: Mapping[str, Any]) -> None:
    if not isinstance(receipt, Mapping):
        raise ValueError("sra_trial_receipt_mapping_required")
    if receipt.get("schema_version") != TRIAL_RECEIPT_SCHEMA:
        raise ValueError("sra_trial_receipt_schema_invalid")
    if receipt.get("family_id") != FAMILY_ID:
        raise ValueError("sra_trial_receipt_family_invalid")
    if receipt.get("search_family_id") != SEARCH_FAMILY_ID or receipt.get("implementation_id") != IMPLEMENTATION_ID:
        raise ValueError("sra_trial_receipt_search_identity_invalid")
    if receipt.get("trial_ledger_scope") != TRIAL_LEDGER_SCOPE:
        raise ValueError("sra_trial_receipt_scope_invalid")
    if int(receipt.get("trial_number", -1)) != 1:
        raise ValueError("sra_trial_receipt_number_invalid")
    if int(receipt.get("trial_budget_max", -1)) != 1 or int(receipt.get("material_trials_consumed", -1)) != 1:
        raise ValueError("sra_trial_receipt_budget_invalid")
    if receipt.get("outcome_accessed") is not False or receipt.get("status") != "PREREGISTERED_NOT_EVALUATED":
        raise ValueError("sra_trial_receipt_outcome_state_invalid")
    if receipt.get("falsifiers") != list(MECHANISM_FALSIFIERS):
        raise ValueError("sra_trial_receipt_falsifier_drift")
    if receipt.get("financial_alpha_evidence") != 0 or receipt.get("capital_authority") != "NONE":
        raise ValueError("sra_trial_receipt_authority_invalid")
    assert_sha256(str(receipt.get("code_manifest_sha256") or ""))
    code_manifest = receipt.get("code_manifest")
    if not isinstance(code_manifest, Mapping):
        raise ValueError("sra_trial_receipt_code_manifest_required")
    verify_code_manifest(code_manifest)
    if str(code_manifest["code_manifest_sha256"]) != str(receipt.get("code_manifest_sha256")):
        raise ValueError("sra_trial_receipt_code_manifest_hash_mismatch")
    _timestamp(receipt.get("created_at"), "created_at")
    sealed = str(receipt.get("trial_receipt_sha256") or "")
    body = {key: value for key, value in receipt.items() if key != "trial_receipt_sha256"}
    expected = domain_hash("SECTOR_ROTATION_ALPHA_V1:TRIAL_RECEIPT", canonical_value(body))
    if sealed != expected:
        raise ValueError("sra_trial_receipt_hash_mismatch")


def append_trial_receipt(ledger_path: str | Path, receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Append the sole M0 material trial. A second material trial fails closed."""

    verify_trial_receipt(receipt)
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
            raise FileExistsError("sra_trial_ledger_writer_lock_exists") from exc
        os.write(lock_fd, (str(receipt["trial_receipt_sha256"]) + "\n").encode("utf-8"))
        os.fsync(lock_fd)

        existing = load_trial_ledger(path)
        if existing:
            raise RuntimeError("sra_material_trial_budget_exhausted")
        line = json.dumps(canonical_value(receipt), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8") + b"\n"
        fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
        try:
            if os.write(fd, line) != len(line):
                raise OSError("sra_trial_ledger_partial_append")
            os.fsync(fd)
        finally:
            os.close(fd)
        verified = load_trial_ledger(path)
        if verified != [canonical_value(receipt)]:
            raise ValueError("sra_trial_ledger_post_append_verification_failed")
        return verified[0]
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        if lock_created and lock_path.exists():
            try:
                lock_path.unlink()
            except OSError:
                pass


def load_trial_ledger(ledger_path: str | Path) -> list[dict[str, Any]]:
    path = Path(ledger_path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    if not raw:
        return []
    if not raw.endswith(b"\n"):
        raise ValueError("sra_trial_ledger_partial_final_line")
    lines = raw.splitlines()
    if len(lines) > 1:
        raise ValueError("sra_trial_ledger_budget_exceeded")
    try:
        parsed = json.loads(lines[0].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("sra_trial_ledger_invalid_json") from exc
    if not isinstance(parsed, dict):
        raise ValueError("sra_trial_ledger_entry_mapping_required")
    verify_trial_receipt(parsed)
    return [parsed]


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
