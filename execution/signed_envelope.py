from __future__ import annotations

from contextlib import contextmanager
import errno
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Mapping

from core.security_policy import require_hmac_rotation_compliance

if os.name == "nt":  # pragma: no cover
    import msvcrt
else:  # pragma: no cover
    import fcntl

SIGNED_EXECUTION_ENVELOPE_FIELD = "signed_execution_envelope"
EXECUTION_ENVELOPE_SECRET_ENV = "TZ_EXECUTION_ENVELOPE_SECRET"
EXECUTION_ENVELOPE_KID_ENV = "TZ_EXECUTION_ENVELOPE_KID"
EXECUTION_ENVELOPE_TTL_SECONDS_ENV = "TZ_EXECUTION_ENVELOPE_TTL_SECONDS"
EXECUTION_REPLAY_LEDGER_PATH_ENV = "TZ_EXECUTION_REPLAY_LEDGER_PATH"
EXECUTION_REPLAY_LOCK_TIMEOUT_MS_ENV = "TZ_EXECUTION_REPLAY_LOCK_TIMEOUT_MS"
EXECUTION_REPLAY_LEDGER_MAX_ROWS_ENV = "TZ_EXECUTION_REPLAY_LEDGER_MAX_ROWS"
DEFAULT_EXECUTION_ENVELOPE_TTL_SECONDS = 300
DEFAULT_EXECUTION_REPLAY_LOCK_TIMEOUT_MS = 25
DEFAULT_EXECUTION_REPLAY_LEDGER_MAX_ROWS = 50_000
_DEFAULT_REPLAY_LEDGER_FILENAME = "execution_replay_ledger.jsonl"
_REPLAY_LEDGER_LOCK_SUFFIX = ".lock"
_REPLAY_LEDGER_MALFORMED_SUFFIX = ".malformed.jsonl"
QUALITY_DEBT_EVENT_KEY_REPLAY_LOCK_TIMEOUT = "execution.replay_ledger.lock_timeout"
QUALITY_DEBT_EVENT_KEY_REPLAY_LOCK_FAILURE = "execution.replay_ledger.lock_failure"
QUALITY_DEBT_EVENT_KEY_REPLAY_LEDGER_MALFORMED = "execution.replay_ledger.malformed_detected"
QUALITY_DEBT_EVENT_KEY_REPLAY_LEDGER_TRIMMED = "execution.replay_ledger.trimmed"
_REPLAY_LOCK_RETRY_SLEEP_SECONDS = 0.001
LOGGER = logging.getLogger(__name__)


def _utc_now(now_utc: datetime | None = None) -> datetime:
    if isinstance(now_utc, datetime):
        if now_utc.tzinfo is None:
            return now_utc.replace(tzinfo=timezone.utc)
        return now_utc.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def _required_text(raw: Mapping[str, Any], field: str) -> str:
    value = str(raw.get(field, "")).strip()
    if not value:
        raise ValueError(f"execution envelope missing required field: {field}")
    return value


def _required_int(raw: Mapping[str, Any], field: str) -> int:
    try:
        value = int(raw.get(field))
    except (TypeError, ValueError):
        raise ValueError(f"execution envelope field {field} must be an integer") from None
    if value <= 0:
        raise ValueError(f"execution envelope field {field} must be > 0")
    return value


def _canonical_payload_bytes(payload: Mapping[str, Any]) -> bytes:
    material = {k: v for (k, v) in payload.items() if k != SIGNED_EXECUTION_ENVELOPE_FIELD}
    serialized = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return serialized.encode("utf-8")


def _payload_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_payload_bytes(payload)).hexdigest()


def _resolve_envelope_ttl_seconds() -> int:
    raw = str(os.environ.get(EXECUTION_ENVELOPE_TTL_SECONDS_ENV, "")).strip()
    if raw == "":
        return DEFAULT_EXECUTION_ENVELOPE_TTL_SECONDS
    try:
        ttl = int(raw)
    except ValueError:
        raise ValueError(f"{EXECUTION_ENVELOPE_TTL_SECONDS_ENV} must be a positive integer") from None
    if ttl <= 0:
        raise ValueError(f"{EXECUTION_ENVELOPE_TTL_SECONDS_ENV} must be a positive integer")
    return ttl


def _resolve_replay_lock_timeout_ms() -> int:
    raw = str(os.environ.get(EXECUTION_REPLAY_LOCK_TIMEOUT_MS_ENV, "")).strip()
    if raw == "":
        return DEFAULT_EXECUTION_REPLAY_LOCK_TIMEOUT_MS
    try:
        timeout_ms = int(raw)
    except ValueError:
        raise ValueError(f"{EXECUTION_REPLAY_LOCK_TIMEOUT_MS_ENV} must be a positive integer") from None
    if timeout_ms <= 0:
        raise ValueError(f"{EXECUTION_REPLAY_LOCK_TIMEOUT_MS_ENV} must be a positive integer")
    return timeout_ms


def _resolve_replay_ledger_max_rows() -> int:
    raw = str(os.environ.get(EXECUTION_REPLAY_LEDGER_MAX_ROWS_ENV, "")).strip()
    if raw == "":
        return DEFAULT_EXECUTION_REPLAY_LEDGER_MAX_ROWS
    try:
        max_rows = int(raw)
    except ValueError:
        raise ValueError(f"{EXECUTION_REPLAY_LEDGER_MAX_ROWS_ENV} must be a positive integer") from None
    if max_rows <= 0:
        raise ValueError(f"{EXECUTION_REPLAY_LEDGER_MAX_ROWS_ENV} must be a positive integer")
    return max_rows


def _fsync_parent_dir_if_possible(path: Path) -> None:
    if os.name == "nt":
        return
    fd: int | None = None
    try:
        fd = os.open(str(path), os.O_RDONLY)
        os.fsync(fd)
    except OSError:
        return
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


def _emit_quality_debt_event(*, event_key: str, detail: Mapping[str, Any]) -> None:
    payload = {
        "detail": dict(detail),
        "event_key": str(event_key).strip(),
        "timestamp_utc": _utc_now().isoformat(timespec="milliseconds").replace("+00:00", "Z"),
    }
    LOGGER.warning(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _require_envelope_secret() -> str:
    secret = str(os.environ.get(EXECUTION_ENVELOPE_SECRET_ENV, "")).strip()
    if not secret:
        raise EnvironmentError(f"Missing required environment variable: {EXECUTION_ENVELOPE_SECRET_ENV}")
    return secret


def _resolve_kid(key_version: str) -> str:
    configured = str(os.environ.get(EXECUTION_ENVELOPE_KID_ENV, "")).strip()
    return configured if configured else str(key_version).strip()


def _signature_material(
    *,
    kid: str,
    exp: int,
    key_version: str,
    payload_hash: str,
    intent_id: str,
    nonce: str,
) -> bytes:
    material = {
        "exp": int(exp),
        "intent_id": str(intent_id),
        "key_version": str(key_version),
        "kid": str(kid),
        "nonce": str(nonce),
        "payload_hash": str(payload_hash),
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return encoded.encode("utf-8")


def _compute_signature(
    *,
    kid: str,
    exp: int,
    key_version: str,
    payload_hash: str,
    intent_id: str,
    nonce: str,
    secret: str,
) -> str:
    message = _signature_material(
        kid=kid,
        exp=exp,
        key_version=key_version,
        payload_hash=payload_hash,
        intent_id=intent_id,
        nonce=nonce,
    )
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _derive_intent_id(payload: Mapping[str, Any], payload_hash: str) -> str:
    batch_id = str(payload.get("batch_id", "")).strip()
    if batch_id:
        return batch_id
    return hashlib.sha256(payload_hash.encode("utf-8")).hexdigest()[:24]


def _resolve_replay_ledger_path() -> Path:
    configured = str(os.environ.get(EXECUTION_REPLAY_LEDGER_PATH_ENV, "")).strip()
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parent / _DEFAULT_REPLAY_LEDGER_FILENAME


def _is_lock_contention_error(exc: OSError) -> bool:
    if isinstance(exc, BlockingIOError):
        return True
    if exc.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
        return True
    return getattr(exc, "winerror", None) in {33, 36}


def _try_acquire_exclusive_lock(handle: Any) -> bool:
    if os.name == "nt":  # pragma: no cover
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError as exc:
            if _is_lock_contention_error(exc):
                return False
            raise
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError as exc:
        if _is_lock_contention_error(exc):
            return False
        raise


def _acquire_exclusive_lock(handle: Any, *, timeout_ms: int) -> None:
    deadline = time.monotonic() + (float(timeout_ms) / 1000.0)
    while True:
        if _try_acquire_exclusive_lock(handle):
            return
        now = time.monotonic()
        if now >= deadline:
            raise TimeoutError(f"replay ledger lock acquisition timed out after {int(timeout_ms)}ms")
        time.sleep(min(_REPLAY_LOCK_RETRY_SLEEP_SECONDS, max(deadline - now, 0.0)))


def _release_exclusive_lock(handle: Any) -> None:
    if os.name == "nt":  # pragma: no cover
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def _exclusive_file_lock(lock_path: Path, *, timeout_ms: int | None = None):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    timeout_budget_ms = int(timeout_ms) if timeout_ms is not None else _resolve_replay_lock_timeout_ms()
    if timeout_budget_ms <= 0:
        raise ValueError("timeout_ms must be a positive integer")
    with lock_path.open("a+b") as handle:
        acquired = False
        try:
            _acquire_exclusive_lock(handle, timeout_ms=timeout_budget_ms)
            acquired = True
        except Exception as exc:
            _emit_quality_debt_event(
                event_key=(
                    QUALITY_DEBT_EVENT_KEY_REPLAY_LOCK_TIMEOUT
                    if isinstance(exc, TimeoutError)
                    else QUALITY_DEBT_EVENT_KEY_REPLAY_LOCK_FAILURE
                ),
                detail={
                    "error": str(exc),
                    "lock_path": str(lock_path),
                    "timeout_ms": timeout_budget_ms,
                },
            )
            raise
        try:
            yield
        finally:
            if acquired:
                _release_exclusive_lock(handle)


@dataclass(frozen=True, slots=True)
class SignedExecutionEnvelope:
    kid: str
    exp: int
    key_version: str
    payload_hash: str
    signature: str
    intent_id: str
    nonce: str

    @property
    def replay_key(self) -> str:
        return f"{self.intent_id}:{self.nonce}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kid": self.kid,
            "exp": self.exp,
            "key_version": self.key_version,
            "payload_hash": self.payload_hash,
            "signature": self.signature,
            "intent_id": self.intent_id,
            "nonce": self.nonce,
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> SignedExecutionEnvelope:
        return cls(
            kid=_required_text(raw, "kid"),
            exp=_required_int(raw, "exp"),
            key_version=_required_text(raw, "key_version"),
            payload_hash=_required_text(raw, "payload_hash"),
            signature=_required_text(raw, "signature"),
            intent_id=_required_text(raw, "intent_id"),
            nonce=_required_text(raw, "nonce"),
        )


@dataclass(slots=True)
class ReplayLedger:
    path: Path
    seen: set[str]

    @staticmethod
    def _lock_path(path: Path) -> Path:
        return path.with_name(f"{path.name}{_REPLAY_LEDGER_LOCK_SUFFIX}")

    @staticmethod
    def _quarantine_path(path: Path) -> Path:
        return path.with_name(f"{path.name}{_REPLAY_LEDGER_MALFORMED_SUFFIX}")

    @classmethod
    def load(cls, path: Path) -> ReplayLedger:
        ledger = cls(path=path, seen=set())
        seen, _, _ = ledger._read_state()
        ledger.seen = seen
        return ledger

    @staticmethod
    def _serialize_record(envelope: SignedExecutionEnvelope, *, recorded_at: str) -> str:
        record = {
            "recorded_at": str(recorded_at),
            "replay_key": envelope.replay_key,
            "intent_id": envelope.intent_id,
            "nonce": envelope.nonce,
            "kid": envelope.kid,
            "key_version": envelope.key_version,
            "exp": envelope.exp,
        }
        return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def _read_state(self) -> tuple[set[str], list[str], list[dict[str, Any]]]:
        seen: set[str] = set()
        valid_lines: list[str] = []
        malformed_rows: list[dict[str, Any]] = []
        if not self.path.exists():
            return seen, valid_lines, malformed_rows

        with self.path.open("r", encoding="utf-8") as handle:
            for line_no, raw_line in enumerate(handle, start=1):
                text = raw_line.strip()
                if text == "":
                    continue
                try:
                    row = json.loads(text)
                except json.JSONDecodeError:
                    malformed_rows.append(
                        {
                            "line_no": line_no,
                            "reason": "json_decode_error",
                            "raw_line": raw_line.rstrip("\r\n"),
                        }
                    )
                    continue
                if not isinstance(row, Mapping):
                    malformed_rows.append(
                        {
                            "line_no": line_no,
                            "reason": "row_not_object",
                            "raw_line": raw_line.rstrip("\r\n"),
                        }
                    )
                    continue
                replay_key = str(row.get("replay_key", "")).strip()
                if replay_key == "":
                    malformed_rows.append(
                        {
                            "line_no": line_no,
                            "reason": "missing_replay_key",
                            "raw_line": raw_line.rstrip("\r\n"),
                        }
                    )
                    continue
                seen.add(replay_key)
                valid_lines.append(text)
        return seen, valid_lines, malformed_rows

    @staticmethod
    def _trim_valid_lines(valid_lines: list[str], *, max_rows: int) -> tuple[list[str], bool]:
        if max_rows <= 0:
            return valid_lines, False
        if len(valid_lines) <= int(max_rows):
            return valid_lines, False
        return valid_lines[-int(max_rows) :], True

    def _quarantine_malformed_rows(self, malformed_rows: list[dict[str, Any]]) -> None:
        if not malformed_rows:
            return
        quarantine_path = self._quarantine_path(self.path)
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        quarantined_at = _utc_now().isoformat(timespec="seconds").replace("+00:00", "Z")
        with quarantine_path.open("a", encoding="utf-8") as handle:
            for row in malformed_rows:
                payload = {
                    "quarantined_at": quarantined_at,
                    "ledger_path": str(self.path),
                    "line_no": int(row.get("line_no", 0)),
                    "reason": str(row.get("reason", "")),
                    "raw_line": str(row.get("raw_line", "")),
                }
                handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _rewrite_with_valid_lines(self, valid_lines: list[str]) -> None:
        temp_path = self.path.with_name(f"{self.path.name}.tmp.{uuid.uuid4().hex}")
        try:
            with temp_path.open("w", encoding="utf-8") as handle:
                for line in valid_lines:
                    handle.write(line)
                    handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
            _fsync_parent_dir_if_possible(self.path.parent)
        finally:
            temp_path.unlink(missing_ok=True)

    def assert_not_replayed(self, replay_key: str) -> None:
        if replay_key in self.seen:
            raise ValueError(f"replay detected for intent_id={replay_key.split(':', 1)[0]}")

    def append(self, envelope: SignedExecutionEnvelope, *, recorded_at: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record_line = self._serialize_record(envelope, recorded_at=recorded_at)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(record_line)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.seen.add(envelope.replay_key)

    def assert_not_replayed_and_append_atomic(
        self,
        envelope: SignedExecutionEnvelope,
        *,
        recorded_at: str,
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self._lock_path(self.path)
        with _exclusive_file_lock(lock_path):
            seen, valid_lines, malformed_rows = self._read_state()
            max_rows = _resolve_replay_ledger_max_rows()
            valid_lines, was_trimmed = self._trim_valid_lines(valid_lines, max_rows=max_rows)
            seen = set()
            for line in valid_lines:
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(payload, Mapping):
                    continue
                replay_key = str(payload.get("replay_key", "")).strip()
                if replay_key:
                    seen.add(replay_key)
            self.seen = seen
            if malformed_rows:
                self._quarantine_malformed_rows(malformed_rows)
                self._rewrite_with_valid_lines(valid_lines)
                _emit_quality_debt_event(
                    event_key=QUALITY_DEBT_EVENT_KEY_REPLAY_LEDGER_MALFORMED,
                    detail={
                        "ledger_path": str(self.path),
                        "malformed_rows": int(len(malformed_rows)),
                    },
                )
                raise ValueError("replay ledger malformed rows detected; submit rejected fail-closed")
            if was_trimmed:
                self._rewrite_with_valid_lines(valid_lines)
                _emit_quality_debt_event(
                    event_key=QUALITY_DEBT_EVENT_KEY_REPLAY_LEDGER_TRIMMED,
                    detail={
                        "ledger_path": str(self.path),
                        "max_rows": int(max_rows),
                    },
                )
            self.assert_not_replayed(envelope.replay_key)
            self.append(envelope, recorded_at=recorded_at)


def sign_execution_payload(
    payload: Mapping[str, Any],
    *,
    now_utc: datetime | None = None,
    key_version: str | None = None,
    ttl_seconds: int | None = None,
) -> SignedExecutionEnvelope:
    now_val = _utc_now(now_utc)
    resolved_key_version = str(key_version).strip() if key_version is not None else ""
    if resolved_key_version == "":
        status = require_hmac_rotation_compliance(now_utc=now_val)
        resolved_key_version = str(status.get("hmac_key_version", "")).strip()
    if resolved_key_version == "":
        raise ValueError("resolved key_version cannot be empty")
    ttl = int(ttl_seconds) if ttl_seconds is not None else _resolve_envelope_ttl_seconds()
    if ttl <= 0:
        raise ValueError("ttl_seconds must be a positive integer")
    payload_hash = _payload_hash(payload)
    intent_id = _derive_intent_id(payload, payload_hash)
    nonce = uuid.uuid4().hex
    exp = int(now_val.timestamp()) + int(ttl)
    kid = _resolve_kid(resolved_key_version)
    secret = _require_envelope_secret()
    signature = _compute_signature(
        kid=kid,
        exp=exp,
        key_version=resolved_key_version,
        payload_hash=payload_hash,
        intent_id=intent_id,
        nonce=nonce,
        secret=secret,
    )
    return SignedExecutionEnvelope(
        kid=kid,
        exp=exp,
        key_version=resolved_key_version,
        payload_hash=payload_hash,
        signature=signature,
        intent_id=intent_id,
        nonce=nonce,
    )


def attach_signed_execution_envelope(
    payload: dict[str, Any],
    *,
    now_utc: datetime | None = None,
    key_version: str | None = None,
    ttl_seconds: int | None = None,
) -> dict[str, Any]:
    envelope = sign_execution_payload(
        payload,
        now_utc=now_utc,
        key_version=key_version,
        ttl_seconds=ttl_seconds,
    )
    payload[SIGNED_EXECUTION_ENVELOPE_FIELD] = envelope.to_dict()
    return payload


def verify_signed_execution_envelope(
    payload: Mapping[str, Any],
    *,
    now_utc: datetime | None = None,
) -> SignedExecutionEnvelope:
    now_val = _utc_now(now_utc)
    envelope_raw = payload.get(SIGNED_EXECUTION_ENVELOPE_FIELD)
    if not isinstance(envelope_raw, Mapping):
        raise ValueError(f"payload missing {SIGNED_EXECUTION_ENVELOPE_FIELD}")
    envelope = SignedExecutionEnvelope.from_mapping(envelope_raw)
    if int(envelope.exp) <= int(now_val.timestamp()):
        raise ValueError("execution envelope expired")

    status = require_hmac_rotation_compliance(now_utc=now_val)
    expected_key_version = str(status.get("hmac_key_version", "")).strip()
    if envelope.key_version != expected_key_version:
        raise ValueError("execution envelope key_version mismatch")
    expected_kid = _resolve_kid(expected_key_version)
    if envelope.kid != expected_kid:
        raise ValueError("execution envelope kid mismatch")

    expected_hash = _payload_hash(payload)
    if not hmac.compare_digest(envelope.payload_hash, expected_hash):
        raise ValueError("execution envelope payload hash mismatch")

    expected_signature = _compute_signature(
        kid=envelope.kid,
        exp=envelope.exp,
        key_version=envelope.key_version,
        payload_hash=envelope.payload_hash,
        intent_id=envelope.intent_id,
        nonce=envelope.nonce,
        secret=_require_envelope_secret(),
    )
    if not hmac.compare_digest(envelope.signature, expected_signature):
        raise ValueError("execution envelope signature mismatch")
    return envelope


def verify_local_submit_envelope_and_replay(
    payload: Mapping[str, Any],
    *,
    now_utc: datetime | None = None,
) -> SignedExecutionEnvelope:
    now_val = _utc_now(now_utc)
    envelope = verify_signed_execution_envelope(payload, now_utc=now_val)
    ledger = ReplayLedger(path=_resolve_replay_ledger_path(), seen=set())
    ledger.assert_not_replayed_and_append_atomic(
        envelope,
        recorded_at=now_val.isoformat(timespec="seconds").replace("+00:00", "Z"),
    )
    return envelope
