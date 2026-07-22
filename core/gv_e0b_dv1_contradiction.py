"""GV-E0B-DV1 Contradiction Case (G08): observed within-case decision comparison.

Capture authority (PR #5 repair):
- Append-only sequence-numbered event journal (tamper-evident under process custody).
- Arm opens are sealed chain events; closes reference exact open-event hashes.
- Equal 60-minute *budget cap* (early submit allowed; late submit rejected).
- Mechanical reviewer blinding via sealed REVIEW_PACKAGE (ARM_A/ARM_B).
- Two humans only: operator (baseline+post) + different blinded reviewer (rubric).
- Local hashes do not prove wall-clock history or personhood against a privileged
  repository operator; SAW/repo review remains external accountability.

Endpoint authority: docs/architecture/godview_e0/e0_acceptance_tests.md G08.
Score 39 frozen; observed-comparison count stays 0 until real eligible close.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import tempfile
from types import MappingProxyType
from typing import Any, Protocol

from core.gv_fs0_book import (
    DecisionEnvelope as _DecisionEnvelope,
    OpenBookBuild as _OpenBookBuild,
    _build_book,
    _build_decision,
    build_no_position_source_fixture as _build_no_position_source_fixture,
)
from core.gv_fs0_canonical import (
    CANONICAL_TIMESTAMP_RE,
    SHA256_RE,
    canonical_document_bytes,
    domain_hash,
)
from core.gv_fs0_certify import (
    build_certified_result_from_book as _build_certified_result_from_book,
    run_isolated_verifier,
)
from core.gv_fs0_publish import (
    DEFAULT_CURRENT_DECISION_LOCK,
    DEFAULT_CURRENT_DECISION_TARGET,
    publish_current_decision as _publish_current_decision,
)

VerifierRunner = Callable[[Mapping[str, Any]], dict[str, Any]]

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE_DIR = ROOT / "data" / "gv_e0b" / "dv1_g08"
DEFAULT_RESULT_JSON = DEFAULT_CASE_DIR / "result.json"
DEFAULT_DECISION_PACKET_MD = DEFAULT_CASE_DIR / "decision_packet.md"
DEFAULT_BASELINE_PATH = DEFAULT_CASE_DIR / "captures" / "baseline_seal.json"
DEFAULT_PACKET_PATH = DEFAULT_CASE_DIR / "captures" / "packet.json"
DEFAULT_POST_PATH = DEFAULT_CASE_DIR / "captures" / "post_packet_seal.json"
DEFAULT_RUBRIC_PATH = DEFAULT_CASE_DIR / "captures" / "rubric_scores.json"
DEFAULT_SESSION_PATH = DEFAULT_CASE_DIR / "captures" / "session.json"
DEFAULT_EVENTS_DIR = DEFAULT_CASE_DIR / "captures" / "events"
DEFAULT_REVIEWER_EXPORT_DIR = DEFAULT_CASE_DIR / "captures" / "reviewer_export"
DEFAULT_REVIEW_PACKAGE_PATH = DEFAULT_REVIEWER_EXPORT_DIR / "review_package.json"
DEFAULT_RUBRIC_AUTHORING_PATH = DEFAULT_REVIEWER_EXPORT_DIR / "rubric_authoring.json"
DEFAULT_OPERATOR_CUSTODY_DIR = DEFAULT_CASE_DIR / "captures" / "operator_custody"
DEFAULT_REVIEW_MAPPING_PATH = (
    DEFAULT_OPERATOR_CUSTODY_DIR / "review_mapping.private.json"
)
DEFAULT_AUTHORING_TEMPLATES_DIR = DEFAULT_CASE_DIR / "captures" / "authoring"
DEFAULT_SESSION_MANIFEST_PATH = DEFAULT_CASE_DIR / "captures" / "session_manifest.json"
DEFAULT_CHECKPOINTS_DIR = DEFAULT_CASE_DIR / "captures" / "checkpoints"

CASE_ID = "E0B_DV1_G08_CONTRADICTION_1"
PROTOCOL_ID = "GODVIEW-E0-P0-V1"
MODULE = "G_supply"
SUBJECT = "SYNTH_MU_SUPPLY"
BLOCK_REASON = "CONTRADICTORY_INDISPENSABLE_EVIDENCE"
RUN_STATE_BLOCKED = "BLOCKED"
RUN_CLASS_SYNTHETIC = "SYNTHETIC_DEV_RUN"
RESEARCH_ACTION_HOLD = "HOLD_FOR_EVIDENCE"
PORTFOLIO_ACTION_NO_POSITION = "NO_POSITION"
E0B_DECISION_ID = "DECISION_E0B_DV1_G08_1"
RATIONALE_REF_PREFIX = "E0B:CMP:"

DOMAIN_BUNDLE = "GV-E0B:DV1:BUNDLE:V1"
DOMAIN_BASELINE = "GV-E0B:DV1:BASELINE:V1"
DOMAIN_PACKET = "GV-E0B:DV1:PACKET:V1"
DOMAIN_POST = "GV-E0B:DV1:POST_PACKET:V1"
DOMAIN_RUBRIC = "GV-E0B:DV1:RUBRIC:V1"
DOMAIN_COMPARISON = "GV-E0B:DV1:COMPARISON:V1"
DOMAIN_RESULT = "GV-E0B:DV1:RESULT:V1"
DOMAIN_SESSION = "GV-E0B:DV1:SESSION:V1"
DOMAIN_CHAIN = "GV-E0B:DV1:CHAIN:V1"
DOMAIN_ARM_OPEN = "GV-E0B:DV1:ARM_OPEN:V1"
DOMAIN_REVIEW_PACKAGE = "GV-E0B:DV1:REVIEW_PACKAGE:V1"
DOMAIN_REVIEW_MAPPING = "GV-E0B:DV1:REVIEW_MAPPING:V1"
DOMAIN_SESSION_MANIFEST = "GV-E0B:DV1:SESSION_MANIFEST:V1"
DOMAIN_CHECKPOINT = "GV-E0B:DV1:CHECKPOINT:V1"
DOMAIN_ONESHOT_AUTH = "GV-E0B:DV1:ONESHOT_AUTH:V1"
DOMAIN_GITHUB_RECEIPT = "GV-E0B:DV1:GITHUB_RECEIPT:V1"

# One-shot Attempt-1 authorization (production G08 only; not personhood proof).
ONESHOT_CASE_ID = "GV_E0B_DV1_G08"
ONESHOT_ATTEMPT = 1
ONESHOT_AUTH_SCHEMA = "gv_e0b_g08_oneshot_authorization_v1"
GITHUB_RECEIPT_SCHEMA = "gv_e0b_g08_github_rubric_receipt_v1"
# v2 requires provider-authenticated GitHub login fields (author/committer).
GITHUB_RECEIPT_SCHEMA_V2 = "gv_e0b_g08_github_rubric_receipt_v2"
INVALIDATION_CLASS_REVIEWER_INDEPENDENCE = (
    "INVALID_REVIEWER_INDEPENDENCE_NOT_ESTABLISHED"
)
DEFAULT_ATTEMPT1_INVALIDATION_PATH = (
    DEFAULT_CASE_DIR / "invalidation" / "ATTEMPT_1_INVALIDATION.json"
)
RECEIPT_PROVIDER_GITHUB = "GITHUB"
FIXTURE_SOURCE_COMMIT = "0" * 40
FIXTURE_SOURCE_TREE = "1" * 40
PREREGISTRATION_RELATIVE_PATH = (
    "docs/phase_brief/gv-e0b-dv1-contradiction-brief.md"
)

AUTH_FIXTURE = "ENGINE_TEST_FIXTURE"
AUTH_REAL_OPERATOR = "REAL_HUMAN_OPERATOR"
AUTH_REAL_REVIEWER = "REAL_HUMAN_REVIEWER"

# Canonical blinded review-arm schema: identical keys on every arm (no provenance leaks).
REVIEW_ARM_FIELDS: tuple[str, ...] = (
    "action",
    "rationale",
    "missing_evidence",
    "falsifiers",
    "contradictions_recognized",
    "bundle_hash",
    "alpha_claim",
    "case_id",
)
REVIEWER_EXPORT_EXACT_NAMES: frozenset[str] = frozenset(
    {"review_package.json", "rubric_authoring.json"}
)
DOMAIN_RNG = "GV-E0B:DV1:RNG:V1"

BUDGET_MINUTES = 60
ZERO_CHAIN_HASH = "0" * 64
ARM_BASELINE = "BASELINE"
ARM_POST = "POST"
LABEL_ARM_A = "ARM_A"
LABEL_ARM_B = "ARM_B"
REVIEW_INPUT_MODE_BLINDED = "BLINDED_ARM_LABELS"
BLINDING_CUSTODY_MODEL = "ARM_LABEL_BLINDING_SEPARATED_EXPORT_CUSTODY"
AUTHORING_ONLY = "AUTHORING_ONLY"
BASELINE_TEMPLATE_ID = "GV_E0B_G08_BASELINE_AUTHORING_V1"
POST_TEMPLATE_ID = "GV_E0B_G08_POST_AUTHORING_V1"
RUBRIC_TEMPLATE_ID = "GV_E0B_G08_RUBRIC_AUTHORING_V1"
SESSION_MANIFEST_SCHEMA = "gv_e0b_g08_session_manifest_v1"
CHECKPOINT_SCHEMA = "gv_e0b_g08_checkpoint_v1"
CAPTURE_STATE_ACTIVE = "ACTIVE"
CAPTURE_STATE_RESUMABLE = "RESUMABLE"
CAPTURE_STATE_ABORTED = "ABORTED"
CAPTURE_STATE_COMPLETE = "COMPLETE"
CAPTURE_STATES = frozenset(
    {
        CAPTURE_STATE_ACTIVE,
        CAPTURE_STATE_RESUMABLE,
        CAPTURE_STATE_ABORTED,
        CAPTURE_STATE_COMPLETE,
    }
)

STAGE_SESSION_OPEN = "SESSION_OPEN"
STAGE_BASELINE_OPEN = "BASELINE_OPEN"
STAGE_BASELINE_CLOSE = "BASELINE_CLOSE"
STAGE_PACKET = "PACKET"
STAGE_POST_OPEN = "POST_OPEN"
STAGE_POST_CLOSE = "POST_CLOSE"
STAGE_REVIEW_PACKAGE = "REVIEW_PACKAGE"
STAGE_RUBRIC_CLOSE = "RUBRIC_CLOSE"

CANONICAL_STAGE_ORDER: tuple[str, ...] = (
    STAGE_SESSION_OPEN,
    STAGE_BASELINE_OPEN,
    STAGE_BASELINE_CLOSE,
    STAGE_PACKET,
    STAGE_POST_OPEN,
    STAGE_POST_CLOSE,
    STAGE_REVIEW_PACKAGE,
    STAGE_RUBRIC_CLOSE,
)

RUBRIC_ITEMS: tuple[str, ...] = (
    "selected_action_defensibility",
    "indispensable_missing_evidence_identification",
    "falsifier_and_contradiction_recognition",
    "supply_demand_business_shareholder_valuation_claim_separation",
    "avoidance_of_claims_beyond_evidence",
    "rationale_traceability",
)

DECISION_VALUE_IMPROVED = "IMPROVED"
DECISION_VALUE_NOT_IMPROVED = "NOT_IMPROVED"
TARGETED_VALUE_DIMENSIONS: tuple[str, ...] = (
    "indispensable_missing_evidence_identification",
    "falsifier_and_contradiction_recognition",
)
CORE_SAFETY_DIMENSIONS: tuple[str, ...] = (
    "selected_action_defensibility",
    "avoidance_of_claims_beyond_evidence",
)

ALLOWED_ACTIONS = frozenset(
    {
        "ADVANCE_TO_FULL_RESEARCH",
        "HOLD_FOR_EVIDENCE",
        "REJECT_THESIS",
    }
)

# Provenance / timing / identity fields never projected into blinded review arms.
_BLIND_FORBIDDEN_KEYS = frozenset(
    {
        "arm",
        "arm_started_at",
        "arm_ended_at",
        "sealed_at",
        "session_nonce",
        "prev_chain_hash",
        "human_analysis_time_minutes",
        "elapsed_seconds",
        "allowed_budget_minutes",
        "arm_opened_event_hash",
        "equal_budget_attestation",
        "baseline_hash",
        "post_packet_hash",
        "packet_hash",
        "sealed_before_packet",
        "authorship_kind",
        "operator_id",
        "portfolio_action",
        "baseline",
        "post",
        "BASELINE",
        "POST",
        "HUMAN_BASELINE",
        "HUMAN_POST_PACKET",
    }
)


class GvE0bDv1Error(RuntimeError):
    """Fail-closed E0B-DV1 contradiction-case error."""


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _paths_alias(left: Path, right: Path) -> bool:
    left_path = Path(left)
    right_path = Path(right)
    try:
        left_identity = os.path.normcase(str(left_path.resolve(strict=False)))
        right_identity = os.path.normcase(str(right_path.resolve(strict=False)))
        if left_identity == right_identity:
            return True
        try:
            left_stat = left_path.stat()
        except FileNotFoundError:
            left_stat = None
        try:
            right_stat = right_path.stat()
        except FileNotFoundError:
            right_stat = None
        return (
            left_stat is not None
            and right_stat is not None
            and os.path.samestat(left_stat, right_stat)
        )
    except OSError as exc:
        raise GvE0bDv1Error("E0B_CASE_PATH_IDENTITY_UNCERTAIN") from exc


def _require_distinct_case_paths(
    named_paths: Sequence[tuple[str, Path | None]],
) -> None:
    active = [(name, Path(path)) for name, path in named_paths if path is not None]
    for index, (left_name, left_path) in enumerate(active):
        for right_name, right_path in active[index + 1 :]:
            if _paths_alias(left_path, right_path):
                raise GvE0bDv1Error(
                    f"E0B_CASE_PATH_ALIAS:{left_name}:{right_name}"
                )


def _require_mapping(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise GvE0bDv1Error(code)
    return {str(k): v for k, v in value.items()}


def _is_placeholder_text(value: Any) -> bool:
    """True for template sentinels / unedited REPLACE_WITH_* authoring values."""

    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    upper = text.upper()
    if "REPLACE_WITH_" in upper:
        return True
    if upper.startswith("REPLACE_WITH"):
        return True
    return False


def _reject_placeholder_identity(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GvE0bDv1Error(code)
    if _is_placeholder_text(value):
        raise GvE0bDv1Error(code)
    return value


def _require_str(record: Mapping[str, Any], key: str, code: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise GvE0bDv1Error(code)
    if _is_placeholder_text(value):
        raise GvE0bDv1Error(code)
    return value


def _require_bool(record: Mapping[str, Any], key: str, expected: bool, code: str) -> bool:
    value = record.get(key)
    if value is not expected:
        raise GvE0bDv1Error(code)
    return bool(value)


def _require_timestamp(record: Mapping[str, Any], key: str, code: str) -> str:
    value = _require_str(record, key, code)
    if not CANONICAL_TIMESTAMP_RE.fullmatch(value):
        raise GvE0bDv1Error(code)
    return value


def _require_sha256(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise GvE0bDv1Error(code)
    return value


def _utc_now_canonical() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _require_generated_at(value: Any) -> str:
    if not isinstance(value, str) or not CANONICAL_TIMESTAMP_RE.fullmatch(value):
        raise GvE0bDv1Error("E0B_PACKET_GENERATED_AT_INVALID")
    return value


class CaptureClock(Protocol):
    def now(self) -> str: ...


class WallClock:
    """Production capture clock: actual UTC wall time only."""

    def now(self) -> str:
        return _utc_now_canonical()


class AdvanceableClock:
    """Test-only clock. Production stages must use WallClock."""

    def __init__(self, start: str) -> None:
        if not CANONICAL_TIMESTAMP_RE.fullmatch(start):
            raise GvE0bDv1Error("E0B_CLOCK_START_INVALID")
        self._current = datetime.fromisoformat(start.replace("Z", "+00:00"))

    def now(self) -> str:
        return self._current.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def advance_minutes(self, minutes: int) -> str:
        if minutes < 0:
            raise GvE0bDv1Error("E0B_CLOCK_ADVANCE_NEGATIVE")
        self._current = self._current + timedelta(minutes=int(minutes))
        return self.now()

    def advance_seconds(self, seconds: int) -> str:
        if seconds < 0:
            raise GvE0bDv1Error("E0B_CLOCK_ADVANCE_NEGATIVE")
        self._current = self._current + timedelta(seconds=int(seconds))
        return self.now()


def _parse_ts(value: str) -> datetime:
    if not CANONICAL_TIMESTAMP_RE.fullmatch(value):
        raise GvE0bDv1Error("E0B_TIMESTAMP_INVALID")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _add_minutes(ts: str, minutes: int) -> str:
    return (_parse_ts(ts) + timedelta(minutes=int(minutes))).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


def _elapsed_seconds(start: str, end: str) -> int:
    s = _parse_ts(start)
    e = _parse_ts(end)
    if e <= s:
        raise GvE0bDv1Error("E0B_ARM_END_BEFORE_START")
    return int((e - s).total_seconds())


def _without_keys(record: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    banned = set(keys)
    return {k: _plain(v) for k, v in record.items() if k not in banned}


def _reject_caller_timing_fields(record: Mapping[str, Any]) -> None:
    banned = (
        "sealed_at",
        "arm_started_at",
        "arm_ended_at",
        "session_nonce",
        "prev_chain_hash",
        "human_analysis_time_minutes",
        "elapsed_seconds",
        "allowed_budget_minutes",
        "arm_opened_event_hash",
        "deadline_at",
        "scored_at",
        "generated_at",
        "opened_at",
    )
    for key in banned:
        if key in record:
            raise GvE0bDv1Error(f"E0B_CALLER_TIMING_FORBIDDEN:{key}")


def _best_effort_fsync_directory(directory: Path) -> None:
    """Fsync directory metadata where the host exposes a portable handle.

    File payloads are fsynced before atomic replacement. Windows does not expose
    a portable directory-fsync handle, so directory durability remains an honest
    best-effort boundary matching the canonical GV-FS0 publisher.
    """

    flags = getattr(os, "O_RDONLY", 0)
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        return
    finally:
        os.close(descriptor)


def _stage_temp_bytes(target: Path, payload: bytes) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target.parent),
    )
    temp_path = Path(raw_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return temp_path


def _atomic_write_bytes(target: Path, payload: bytes) -> None:
    temp_path = _stage_temp_bytes(target, payload)
    try:
        os.replace(temp_path, target)
        _best_effort_fsync_directory(target.parent)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _read_optional_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _restore_path_bytes(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
        _best_effort_fsync_directory(path.parent)
        return
    _atomic_write_bytes(path, previous)


def _atomic_write_pair(
    first_path: Path,
    first_payload: bytes,
    second_path: Path,
    second_payload: bytes,
) -> None:
    _require_distinct_case_paths(
        [("canonical_result", first_path), ("canonical_packet", second_path)]
    )
    first_previous = _read_optional_bytes(first_path)
    second_previous = _read_optional_bytes(second_path)
    first_temp = _stage_temp_bytes(first_path, first_payload)
    try:
        second_temp = _stage_temp_bytes(second_path, second_payload)
    except Exception:
        first_temp.unlink(missing_ok=True)
        raise

    first_replaced = False
    second_replaced = False
    try:
        os.replace(first_temp, first_path)
        first_temp = None
        first_replaced = True
        _best_effort_fsync_directory(first_path.parent)
        os.replace(second_temp, second_path)
        second_temp = None
        second_replaced = True
        _best_effort_fsync_directory(second_path.parent)
    except Exception as exc:
        for temp_path in (first_temp, second_temp):
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
        rollback_errors: list[Exception] = []
        if second_replaced:
            try:
                _restore_path_bytes(second_path, second_previous)
            except Exception as rollback_exc:
                rollback_errors.append(rollback_exc)
        if first_replaced:
            try:
                _restore_path_bytes(first_path, first_previous)
            except Exception as rollback_exc:
                rollback_errors.append(rollback_exc)
        if rollback_errors:
            raise GvE0bDv1Error(
                "E0B_CANONICAL_ARTIFACT_ROLLBACK_FAILED"
            ) from exc
        raise


def _persist_sealed_json(path: Path, record: Mapping[str, Any]) -> None:
    payload = canonical_document_bytes(_plain(record))
    _atomic_write_bytes(path, payload)


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GvE0bDv1Error(f"E0B_PATH_MISSING:{path.name}")
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GvE0bDv1Error(f"E0B_PATH_INVALID_JSON:{path.name}") from exc
    return _require_mapping(data, f"E0B_PATH_NOT_OBJECT:{path.name}")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _session_manifest_path(session_path: Path) -> Path:
    return session_path.parent / "session_manifest.json"


def _checkpoints_dir_for(session_path: Path) -> Path:
    return session_path.parent / "checkpoints"


def _require_git_object_id(value: Any, code: str) -> str:
    if not isinstance(value, str) or len(value) not in {40, 64}:
        raise GvE0bDv1Error(code)
    if any(char not in "0123456789abcdef" for char in value):
        raise GvE0bDv1Error(code)
    return value


def _require_principal_id(value: Any, code: str) -> str:
    principal = _reject_placeholder_identity(value, code).strip()
    if len(principal) > 128:
        raise GvE0bDv1Error(code)
    if any(char.isspace() or char in "/\\" for char in principal):
        raise GvE0bDv1Error(code)
    return principal


def _authoring_template_specs() -> dict[str, tuple[str, str, Callable[[], dict[str, Any]]]]:
    return {
        "baseline": ("baseline_authoring.json", BASELINE_TEMPLATE_ID, blank_baseline_authoring_template),
        "post": ("post_authoring.json", POST_TEMPLATE_ID, blank_post_authoring_template),
        "rubric": ("rubric_authoring.json", RUBRIC_TEMPLATE_ID, blank_rubric_authoring_template),
    }


def _authoring_template_descriptor(
    role: str,
    path: Path,
) -> dict[str, Any]:
    specs = _authoring_template_specs()
    if role not in specs:
        raise GvE0bDv1Error("E0B_AUTHORING_TEMPLATE_ROLE_INVALID")
    expected_name, template_id, builder = specs[role]
    path = Path(path)
    if path.name != expected_name or not path.is_file() or path.is_symlink():
        raise GvE0bDv1Error(f"E0B_AUTHORING_TEMPLATE_PATH_INVALID:{role}")
    raw = path.read_bytes()
    expected = canonical_document_bytes(builder())
    if raw != expected:
        raise GvE0bDv1Error(f"E0B_AUTHORING_TEMPLATE_NOT_BLANK:{role}")
    return {
        "role": role,
        "file_name": expected_name,
        "artifact_role": AUTHORING_ONLY,
        "template_id": template_id,
        "sha256": _sha256_bytes(raw),
        "byte_length": len(raw),
    }


def _in_memory_authoring_template_descriptors() -> list[dict[str, Any]]:
    descriptors: list[dict[str, Any]] = []
    for role, (file_name, template_id, builder) in _authoring_template_specs().items():
        payload = canonical_document_bytes(builder())
        descriptors.append(
            {
                "role": role,
                "file_name": file_name,
                "artifact_role": AUTHORING_ONLY,
                "template_id": template_id,
                "sha256": _sha256_bytes(payload),
                "byte_length": len(payload),
            }
        )
    return descriptors


def _build_session_manifest(
    *,
    session_id: str,
    source_commit: str,
    source_tree: str,
    protocol_freeze_manifest_sha256: str,
    operator_principal_id: str,
    reviewer_principal_id: str,
    budget_started_at: str,
    authoring_templates: Sequence[Mapping[str, Any]],
    oneshot_authorization: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    operator_id = _require_principal_id(operator_principal_id, "E0B_OPERATOR_REQUIRED")
    reviewer_id = _require_principal_id(reviewer_principal_id, "E0B_REVIEWER_REQUIRED")
    if reviewer_id == operator_id:
        raise GvE0bDv1Error("E0B_REVIEWER_MUST_DIFFER_FROM_OPERATOR")
    body: dict[str, Any] = {
        "schema_version": SESSION_MANIFEST_SCHEMA,
        "case_id": CASE_ID,
        "session_id": _require_str(
            {"session_id": session_id}, "session_id", "E0B_SESSION_NONCE_REQUIRED"
        ),
        "source_commit": _require_git_object_id(
            source_commit, "E0B_SOURCE_COMMIT_INVALID"
        ),
        "source_tree": _require_git_object_id(source_tree, "E0B_SOURCE_TREE_INVALID"),
        "protocol_id": PROTOCOL_ID,
        "protocol_freeze_manifest_sha256": _require_sha256(
            protocol_freeze_manifest_sha256,
            "E0B_PROTOCOL_FREEZE_MANIFEST_HASH_INVALID",
        ),
        "operator_principal_id": operator_id,
        "reviewer_principal_id": reviewer_id,
        "budget_started_at": _require_timestamp(
            {"budget_started_at": budget_started_at},
            "budget_started_at",
            "E0B_BUDGET_START_INVALID",
        ),
        "budget_cap_minutes": BUDGET_MINUTES,
        "authoring_templates": [_plain(item) for item in authoring_templates],
        "authoring_boundary": {
            "artifact_role": AUTHORING_ONLY,
            "templates_are_evidence": False,
            "template_descriptors_permitted_in_session_manifest": True,
            "template_documents_permitted_in_session_or_result": False,
            "authoring_fields_permitted_in_sealed_records": False,
        },
    }
    if oneshot_authorization is not None:
        body["oneshot_authorization"] = _plain(oneshot_authorization)
        body["oneshot_case_id"] = ONESHOT_CASE_ID
        body["oneshot_attempt"] = ONESHOT_ATTEMPT
    roles = [item.get("role") for item in body["authoring_templates"]]
    if roles != ["baseline", "post", "rubric"]:
        raise GvE0bDv1Error("E0B_AUTHORING_TEMPLATE_SET_INVALID")
    out = dict(body)
    out["session_manifest_hash"] = domain_hash(DOMAIN_SESSION_MANIFEST, body)
    return out


def verify_session_manifest(manifest: Mapping[str, Any]) -> str:
    plain = _plain(manifest)
    claimed = _require_sha256(
        plain.get("session_manifest_hash"), "E0B_SESSION_MANIFEST_HASH_INVALID"
    )
    body = _without_keys(plain, "session_manifest_hash")
    if body.get("schema_version") != SESSION_MANIFEST_SCHEMA:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_SCHEMA_INVALID")
    if body.get("case_id") != CASE_ID or body.get("protocol_id") != PROTOCOL_ID:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_AUTHORITY_INVALID")
    _require_git_object_id(body.get("source_commit"), "E0B_SOURCE_COMMIT_INVALID")
    _require_git_object_id(body.get("source_tree"), "E0B_SOURCE_TREE_INVALID")
    _require_sha256(
        body.get("protocol_freeze_manifest_sha256"),
        "E0B_PROTOCOL_FREEZE_MANIFEST_HASH_INVALID",
    )
    operator_id = _require_principal_id(
        body.get("operator_principal_id"), "E0B_OPERATOR_REQUIRED"
    )
    reviewer_id = _require_principal_id(
        body.get("reviewer_principal_id"), "E0B_REVIEWER_REQUIRED"
    )
    if operator_id == reviewer_id:
        raise GvE0bDv1Error("E0B_REVIEWER_MUST_DIFFER_FROM_OPERATOR")
    templates = body.get("authoring_templates")
    if not isinstance(templates, list) or [item.get("role") for item in templates] != [
        "baseline",
        "post",
        "rubric",
    ]:
        raise GvE0bDv1Error("E0B_AUTHORING_TEMPLATE_SET_INVALID")
    expected_specs = {
        role: {
            "file_name": file_name,
            "template_id": template_id,
            "sha256": _sha256_bytes(canonical_document_bytes(builder())),
            "byte_length": len(canonical_document_bytes(builder())),
        }
        for role, (file_name, template_id, builder) in _authoring_template_specs().items()
    }
    for descriptor in templates:
        role = descriptor.get("role")
        expected = expected_specs.get(role)
        if expected is None:
            raise GvE0bDv1Error("E0B_AUTHORING_TEMPLATE_ROLE_INVALID")
        if descriptor.get("artifact_role") != AUTHORING_ONLY:
            raise GvE0bDv1Error("E0B_AUTHORING_ROLE_INVALID")
        for field in ("file_name", "template_id", "sha256", "byte_length"):
            if descriptor.get(field) != expected[field]:
                raise GvE0bDv1Error(f"E0B_AUTHORING_TEMPLATE_DESCRIPTOR_INVALID:{field}")
    boundary = _require_mapping(
        body.get("authoring_boundary"),
        "E0B_AUTHORING_BOUNDARY_REQUIRED",
    )
    if boundary != {
        "artifact_role": AUTHORING_ONLY,
        "templates_are_evidence": False,
        "template_descriptors_permitted_in_session_manifest": True,
        "template_documents_permitted_in_session_or_result": False,
        "authoring_fields_permitted_in_sealed_records": False,
    }:
        raise GvE0bDv1Error("E0B_AUTHORING_BOUNDARY_INVALID")
    if domain_hash(DOMAIN_SESSION_MANIFEST, body) != claimed:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_SEAL_MISMATCH")
    return claimed


def load_session_manifest(path: Path) -> dict[str, Any]:
    manifest = _load_json_object(path)
    verify_session_manifest(manifest)
    return manifest


def _sanitize_authoring_submission(
    authoring: Mapping[str, Any],
    *,
    expected_template_id: str,
) -> dict[str, Any]:
    plain = _plain(authoring)
    auth = plain.get("authorship_kind")
    if auth in {AUTH_REAL_OPERATOR, AUTH_REAL_REVIEWER}:
        if plain.get("artifact_role") != AUTHORING_ONLY:
            raise GvE0bDv1Error("E0B_AUTHORING_ROLE_REQUIRED")
        if plain.get("template_id") != expected_template_id:
            raise GvE0bDv1Error("E0B_AUTHORING_TEMPLATE_ID_INVALID")
    return {
        key: value
        for key, value in plain.items()
        if key not in {"artifact_role", "template_id", "notes"}
    }


def _reject_authoring_metadata_in_evidence(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in {"artifact_role", "template_id"}:
                raise GvE0bDv1Error("E0B_AUTHORING_METADATA_IN_EVIDENCE")
            _reject_authoring_metadata_in_evidence(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_authoring_metadata_in_evidence(item)


def _create_sealed_json(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_document_bytes(_plain(record))
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise GvE0bDv1Error(f"E0B_APPEND_ONLY_FILE_EXISTS:{path.name}") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _best_effort_fsync_directory(path.parent)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _checkpoint_path(checkpoints_dir: Path, seq: int) -> Path:
    return checkpoints_dir / f"{seq:04d}.json"


def load_capture_checkpoints(
    session_path: Path = DEFAULT_SESSION_PATH,
) -> list[dict[str, Any]]:
    session = load_capture_session(session_path)
    directory = _checkpoints_dir_for(session_path)
    if not directory.is_dir():
        return []
    files = sorted(directory.glob("*.json"))
    checkpoints: list[dict[str, Any]] = []
    previous = ZERO_CHAIN_HASH
    for index, path in enumerate(files):
        checkpoint = _load_json_object(path)
        if checkpoint.get("schema_version") != CHECKPOINT_SCHEMA:
            raise GvE0bDv1Error("E0B_CHECKPOINT_SCHEMA_INVALID")
        if checkpoint.get("sequence") != index:
            raise GvE0bDv1Error("E0B_CHECKPOINT_SEQUENCE_INVALID")
        if checkpoint.get("prev_checkpoint_hash") != previous:
            raise GvE0bDv1Error("E0B_CHECKPOINT_CHAIN_BREAK")
        if checkpoint.get("session_id") != session["session_nonce"]:
            raise GvE0bDv1Error("E0B_CHECKPOINT_SESSION_MISMATCH")
        if checkpoint.get("session_manifest_hash") != session["session_manifest_hash"]:
            raise GvE0bDv1Error("E0B_CHECKPOINT_MANIFEST_MISMATCH")
        state = checkpoint.get("state")
        if state not in CAPTURE_STATES:
            raise GvE0bDv1Error("E0B_CHECKPOINT_STATE_INVALID")
        claimed = _require_sha256(
            checkpoint.get("checkpoint_hash"), "E0B_CHECKPOINT_HASH_INVALID"
        )
        body = _without_keys(checkpoint, "checkpoint_hash")
        if domain_hash(DOMAIN_CHECKPOINT, body) != claimed:
            raise GvE0bDv1Error("E0B_CHECKPOINT_SEAL_MISMATCH")
        checkpoints.append(checkpoint)
        previous = claimed
    return checkpoints


def append_capture_checkpoint(
    *,
    session_path: Path = DEFAULT_SESSION_PATH,
    operation: str,
    state: str,
    detail: str,
    clock: CaptureClock | None = None,
) -> Mapping[str, Any]:
    if state not in CAPTURE_STATES:
        raise GvE0bDv1Error("E0B_CHECKPOINT_STATE_INVALID")
    session = load_capture_session(session_path)
    existing = load_capture_checkpoints(session_path)
    if existing and existing[-1]["state"] in {CAPTURE_STATE_ABORTED, CAPTURE_STATE_COMPLETE}:
        raise GvE0bDv1Error("E0B_CAPTURE_STATE_TERMINAL")
    sequence = len(existing)
    previous = existing[-1]["checkpoint_hash"] if existing else ZERO_CHAIN_HASH
    body = {
        "schema_version": CHECKPOINT_SCHEMA,
        "case_id": CASE_ID,
        "session_id": session["session_nonce"],
        "session_manifest_hash": session["session_manifest_hash"],
        "sequence": sequence,
        "operation": _require_str(
            {"operation": operation}, "operation", "E0B_CHECKPOINT_OPERATION_INVALID"
        ),
        "state": state,
        "detail": str(detail),
        "created_at": (clock or WallClock()).now(),
        "event_count": len(session["chain"]),
        "tip_chain_hash": _session_tip_from_chain(session["chain"]),
        "prev_checkpoint_hash": previous,
    }
    checkpoint = {**body, "checkpoint_hash": domain_hash(DOMAIN_CHECKPOINT, body)}
    _create_sealed_json(_checkpoint_path(_checkpoints_dir_for(session_path), sequence), checkpoint)
    return _freeze(checkpoint)


def capture_lifecycle_state(session_path: Path = DEFAULT_SESSION_PATH) -> str:
    checkpoints = load_capture_checkpoints(session_path)
    if not checkpoints:
        return CAPTURE_STATE_RESUMABLE
    return str(checkpoints[-1]["state"])


def require_capture_resumable(session_path: Path = DEFAULT_SESSION_PATH) -> None:
    state = capture_lifecycle_state(session_path)
    if state == CAPTURE_STATE_ACTIVE:
        raise GvE0bDv1Error("E0B_CAPTURE_RECOVERY_REQUIRED")
    if state == CAPTURE_STATE_ABORTED:
        raise GvE0bDv1Error("E0B_CAPTURE_ABORTED")
    if state == CAPTURE_STATE_COMPLETE:
        raise GvE0bDv1Error("E0B_CAPTURE_COMPLETE")


def _require_active_checkpoint_for_authoritative_stage(
    session_path: Path,
    operation: str,
) -> None:
    manifest = load_session_manifest(_session_manifest_path(session_path))
    if (
        manifest["source_commit"] == "0" * 40
        and manifest["source_tree"] == "1" * 40
    ):
        return
    checkpoints = load_capture_checkpoints(session_path)
    if not checkpoints:
        raise GvE0bDv1Error("E0B_CAPTURE_CHECKPOINT_MISSING")
    latest = checkpoints[-1]
    if latest["state"] != CAPTURE_STATE_ACTIVE:
        raise GvE0bDv1Error("E0B_CAPTURE_ACTIVE_CHECKPOINT_REQUIRED")
    if latest["operation"] != operation:
        raise GvE0bDv1Error("E0B_CAPTURE_OPERATION_MISMATCH")


def recover_capture_checkpoint(
    *,
    session_path: Path = DEFAULT_SESSION_PATH,
    operation: str,
    expected_stage: str | None,
    expected_artifacts: Sequence[Path],
    clock: CaptureClock | None = None,
) -> Mapping[str, Any]:
    checkpoints = load_capture_checkpoints(session_path)
    if not checkpoints or checkpoints[-1]["state"] != CAPTURE_STATE_ACTIVE:
        raise GvE0bDv1Error("E0B_CAPTURE_NOT_ACTIVE")
    active = checkpoints[-1]
    if active["operation"] != operation:
        raise GvE0bDv1Error("E0B_CAPTURE_OPERATION_MISMATCH")
    session = load_capture_session(session_path)
    current_count = len(session["chain"])
    start_count = int(active["event_count"])
    current_stage = session["chain"][-1]["stage"] if session["chain"] else None
    artifacts_ready = all(Path(path).is_file() for path in expected_artifacts)
    if current_count == start_count:
        state = CAPTURE_STATE_RESUMABLE
        detail = "no_authoritative_event_mutation_detected"
    elif (
        current_count == start_count + 1
        and expected_stage is not None
        and current_stage == expected_stage
        and artifacts_ready
    ):
        state = CAPTURE_STATE_RESUMABLE
        detail = "authoritative_stage_committed_before_checkpoint"
    else:
        state = CAPTURE_STATE_ABORTED
        detail = "partial_or_ambiguous_authoritative_mutation"
    return append_capture_checkpoint(
        session_path=session_path,
        operation=operation,
        state=state,
        detail=detail,
        clock=clock,
    )


def abort_capture_session(
    *,
    session_path: Path = DEFAULT_SESSION_PATH,
    reason: str,
    clock: CaptureClock | None = None,
) -> Mapping[str, Any]:
    if not isinstance(reason, str) or not reason.strip():
        raise GvE0bDv1Error("E0B_ABORT_REASON_REQUIRED")
    return append_capture_checkpoint(
        session_path=session_path,
        operation="ABORT_SESSION",
        state=CAPTURE_STATE_ABORTED,
        detail=reason.strip(),
        clock=clock,
    )


def _events_dir_for(session_path: Path) -> Path:
    return session_path.parent / "events"


def _event_path(events_dir: Path, seq: int) -> Path:
    return events_dir / f"{seq:04d}.json"


def _list_event_files(events_dir: Path) -> list[Path]:
    if not events_dir.is_dir():
        return []
    files = sorted(events_dir.glob("*.json"))
    return [p for p in files if p.name[:4].isdigit()]


def _chain_link(
    *,
    session_nonce: str,
    stage: str,
    record_hash: str,
    prev_chain_hash: str,
    seq: int,
) -> dict[str, Any]:
    body = {
        "session_nonce": session_nonce,
        "stage": stage,
        "seq": int(seq),
        "record_hash": _require_sha256(record_hash, "E0B_CHAIN_RECORD_HASH_INVALID"),
        "prev_chain_hash": _require_sha256(prev_chain_hash, "E0B_CHAIN_PREV_INVALID"),
    }
    out = dict(body)
    out["chain_hash"] = domain_hash(DOMAIN_CHAIN, body)
    return out


def _session_tip_from_chain(chain: Sequence[Mapping[str, Any]]) -> str:
    if not chain:
        return ZERO_CHAIN_HASH
    tip = chain[-1].get("chain_hash")
    return _require_sha256(tip, "E0B_SESSION_TIP_INVALID")


def _rebuild_session_from_events(events_dir: Path) -> dict[str, Any]:
    files = _list_event_files(events_dir)
    if not files:
        raise GvE0bDv1Error("E0B_SESSION_CHAIN_EMPTY")
    chain: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    case_id: str | None = None
    session_nonce: str | None = None
    bundle_hash: str | None = None
    created_at: str | None = None
    session_manifest_hash: str | None = None
    expected_prev = ZERO_CHAIN_HASH
    for idx, path in enumerate(files):
        event = _load_json_object(path)
        seq = int(event.get("seq", -1))
        if seq != idx:
            raise GvE0bDv1Error(f"E0B_EVENT_SEQ_GAP:{idx}")
        link = _require_mapping(event.get("link"), f"E0B_EVENT_LINK_MISSING:{idx}")
        body = _without_keys(link, "chain_hash")
        recomputed = domain_hash(DOMAIN_CHAIN, body)
        claimed = _require_sha256(link.get("chain_hash"), "E0B_CHAIN_HASH_INVALID")
        if recomputed != claimed:
            raise GvE0bDv1Error(f"E0B_SESSION_CHAIN_SEAL_MISMATCH:{idx}")
        if body.get("prev_chain_hash") != expected_prev:
            raise GvE0bDv1Error(f"E0B_SESSION_CHAIN_BREAK:{idx}")
        if body.get("seq") != idx:
            raise GvE0bDv1Error(f"E0B_EVENT_SEQ_MISMATCH:{idx}")
        expected_prev = claimed
        if case_id is None:
            case_id = _require_str(event, "case_id", "E0B_CASE_ID_MISMATCH")
            session_nonce = _require_str(event, "session_nonce", "E0B_SESSION_NONCE_REQUIRED")
            bundle_hash = _require_sha256(event.get("bundle_hash"), "E0B_BUNDLE_HASH_INVALID")
            created_at = _require_timestamp(event, "created_at", "E0B_CREATED_AT_INVALID")
            session_manifest_hash = _require_sha256(
                event.get("session_manifest_hash"),
                "E0B_SESSION_MANIFEST_HASH_INVALID",
            )
        else:
            if event.get("case_id") != case_id:
                raise GvE0bDv1Error("E0B_CASE_ID_MISMATCH")
            if event.get("session_nonce") != session_nonce:
                raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
            if event.get("bundle_hash") != bundle_hash:
                raise GvE0bDv1Error("E0B_SESSION_BUNDLE_MISMATCH")
            if event.get("session_manifest_hash") != session_manifest_hash:
                raise GvE0bDv1Error("E0B_SESSION_MANIFEST_MISMATCH")
        if link.get("session_nonce") != session_nonce:
            raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
        chain.append(_plain(link))
        events.append(_plain(event))
    assert case_id and session_nonce and bundle_hash and created_at and session_manifest_hash
    session_body = {
        "case_id": case_id,
        "session_nonce": session_nonce,
        "bundle_hash": bundle_hash,
        "created_at": created_at,
        "session_manifest_hash": session_manifest_hash,
        "chain": chain,
    }
    session_hash = domain_hash(DOMAIN_SESSION, session_body)
    return {
        **session_body,
        "session_hash": session_hash,
        "events": events,
        "events_dir": str(events_dir),
        "ledger_custody_note": (
            "Tamper-evident under capture-process custody. Local hashes do not "
            "independently prove wall-clock history or human identity against a "
            "privileged repository operator."
        ),
    }


def verify_session_chain(session: Mapping[str, Any]) -> str:
    plain = _plain(session)
    claimed = _require_sha256(plain.get("session_hash"), "E0B_SESSION_HASH_INVALID")
    chain = list(plain.get("chain") or [])
    if not chain:
        raise GvE0bDv1Error("E0B_SESSION_CHAIN_EMPTY")
    expected_prev = ZERO_CHAIN_HASH
    nonce = _require_str(plain, "session_nonce", "E0B_SESSION_NONCE_REQUIRED")
    for idx, entry in enumerate(chain):
        if not isinstance(entry, Mapping):
            raise GvE0bDv1Error(f"E0B_SESSION_ENTRY_INVALID:{idx}")
        body = _without_keys(entry, "chain_hash")
        if body.get("session_nonce") != nonce:
            raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
        if body.get("prev_chain_hash") != expected_prev:
            raise GvE0bDv1Error(f"E0B_SESSION_CHAIN_BREAK:{idx}")
        if int(body.get("seq", -1)) != idx:
            raise GvE0bDv1Error(f"E0B_EVENT_SEQ_MISMATCH:{idx}")
        recomputed = domain_hash(DOMAIN_CHAIN, body)
        claimed_link = _require_sha256(entry.get("chain_hash"), "E0B_CHAIN_HASH_INVALID")
        if recomputed != claimed_link:
            raise GvE0bDv1Error(f"E0B_SESSION_CHAIN_SEAL_MISMATCH:{idx}")
        expected_prev = claimed_link
    body = {
        "case_id": plain["case_id"],
        "session_nonce": nonce,
        "bundle_hash": plain["bundle_hash"],
        "created_at": plain["created_at"],
        "session_manifest_hash": _require_sha256(
            plain.get("session_manifest_hash"),
            "E0B_SESSION_MANIFEST_HASH_INVALID",
        ),
        "chain": [_plain(e) for e in chain],
    }
    if domain_hash(DOMAIN_SESSION, body) != claimed:
        raise GvE0bDv1Error("E0B_SESSION_SEAL_MISMATCH")
    return claimed


def verify_session_bound_to_records(
    session: Mapping[str, Any],
    seals: Mapping[str, Any],
) -> None:
    """Enforce exact canonical chain and bind each close/link to embedded records."""

    plain = _plain(session)
    verify_session_chain(plain)
    manifest = _require_mapping(
        seals.get("session_manifest"),
        "E0B_SESSION_MANIFEST_REQUIRED",
    )
    verify_session_manifest(manifest)
    if plain.get("session_manifest_hash") != manifest["session_manifest_hash"]:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_MISMATCH")
    if plain.get("session_nonce") != manifest["session_id"]:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_SESSION_MISMATCH")
    chain = list(plain.get("chain") or [])
    stages = [str(e.get("stage")) for e in chain]
    if stages != list(CANONICAL_STAGE_ORDER):
        raise GvE0bDv1Error("E0B_CHAIN_STAGE_ORDER")
    by_stage = {str(e["stage"]): e for e in chain}
    if by_stage[STAGE_BASELINE_CLOSE]["record_hash"] != seals["baseline"]["baseline_hash"]:
        raise GvE0bDv1Error("E0B_CHAIN_RECORD_UNBOUND:BASELINE")
    if by_stage[STAGE_PACKET]["record_hash"] != seals["packet"]["packet_hash"]:
        raise GvE0bDv1Error("E0B_CHAIN_RECORD_UNBOUND:PACKET")
    if by_stage[STAGE_POST_CLOSE]["record_hash"] != seals["post"]["post_packet_hash"]:
        raise GvE0bDv1Error("E0B_CHAIN_RECORD_UNBOUND:POST")
    if by_stage[STAGE_REVIEW_PACKAGE]["record_hash"] != seals["review_package"][
        "review_package_hash"
    ]:
        raise GvE0bDv1Error("E0B_CHAIN_RECORD_UNBOUND:REVIEW_PACKAGE")
    if by_stage[STAGE_RUBRIC_CLOSE]["record_hash"] != seals["rubric"]["rubric_hash"]:
        raise GvE0bDv1Error("E0B_CHAIN_RECORD_UNBOUND:RUBRIC")

    # Open-event hashes must match decision close records.
    events = list(plain.get("events") or [])
    if len(events) != len(chain):
        # Rebuild open hashes from event payloads when available.
        events_dir = plain.get("events_dir")
        if isinstance(events_dir, str) and Path(events_dir).is_dir():
            rebuilt = _rebuild_session_from_events(Path(events_dir))
            events = list(rebuilt.get("events") or [])
    open_by_stage: dict[str, dict[str, Any]] = {}
    for event in events:
        stage = str(event.get("stage") or event.get("link", {}).get("stage"))
        if stage in {STAGE_BASELINE_OPEN, STAGE_POST_OPEN}:
            payload = _require_mapping(event.get("payload"), "E0B_OPEN_PAYLOAD_REQUIRED")
            open_by_stage[stage] = payload
    if STAGE_BASELINE_OPEN not in open_by_stage or STAGE_POST_OPEN not in open_by_stage:
        raise GvE0bDv1Error("E0B_CHAIN_OPEN_MISSING")
    b_open = open_by_stage[STAGE_BASELINE_OPEN]
    p_open = open_by_stage[STAGE_POST_OPEN]
    if seals["baseline"]["arm_opened_event_hash"] != b_open["open_event_hash"]:
        raise GvE0bDv1Error("E0B_CHAIN_OPEN_REF_MISMATCH:BASELINE")
    if seals["post"]["arm_opened_event_hash"] != p_open["open_event_hash"]:
        raise GvE0bDv1Error("E0B_CHAIN_OPEN_REF_MISMATCH:POST")
    if seals["baseline"]["arm_started_at"] != b_open["opened_at"]:
        raise GvE0bDv1Error("E0B_CHAIN_OPEN_TIME_MISMATCH:BASELINE")
    if seals["post"]["arm_started_at"] != p_open["opened_at"]:
        raise GvE0bDv1Error("E0B_CHAIN_OPEN_TIME_MISMATCH:POST")
    # Equal configured budgets (not equal elapsed).
    if (
        int(seals["baseline"]["allowed_budget_minutes"]) != BUDGET_MINUTES
        or int(seals["post"]["allowed_budget_minutes"]) != BUDGET_MINUTES
    ):
        raise GvE0bDv1Error("E0B_BUDGET_CONFIG_MISMATCH")
    if seals["baseline"]["allowed_budget_minutes"] != seals["post"]["allowed_budget_minutes"]:
        raise GvE0bDv1Error("E0B_UNEQUAL_CONFIGURED_BUDGETS")
    # Mapping bind.
    mapping = seals.get("review_mapping")
    if not isinstance(mapping, Mapping):
        raise GvE0bDv1Error("E0B_REVIEW_MAPPING_REQUIRED")
    if mapping.get("review_package_hash") != seals["review_package"]["review_package_hash"]:
        raise GvE0bDv1Error("E0B_MAPPING_PACKAGE_MISMATCH")
    if seals["rubric"].get("review_package_hash") != seals["review_package"][
        "review_package_hash"
    ]:
        raise GvE0bDv1Error("E0B_RUBRIC_PACKAGE_MISMATCH")
    if seals["rubric"].get("mapping_commitment") != mapping.get("mapping_commitment"):
        raise GvE0bDv1Error("E0B_RUBRIC_MAPPING_MISMATCH")
    if seals["baseline"].get("operator_id") != manifest["operator_principal_id"]:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_OPERATOR_MISMATCH")
    if seals["post"].get("operator_id") != manifest["operator_principal_id"]:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_OPERATOR_MISMATCH")
    if seals["rubric"].get("reviewer_id") != manifest["reviewer_principal_id"]:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_REVIEWER_MISMATCH")
    if seals["review_package"].get("session_manifest_hash") != manifest[
        "session_manifest_hash"
    ]:
        raise GvE0bDv1Error("E0B_REVIEW_PACKAGE_MANIFEST_MISMATCH")
    if seals["rubric"].get("session_manifest_hash") != manifest[
        "session_manifest_hash"
    ]:
        raise GvE0bDv1Error("E0B_RUBRIC_MANIFEST_MISMATCH")
    for evidence_record in (
        seals["baseline"],
        seals["packet"],
        seals["post"],
        seals["rubric"],
    ):
        _reject_authoring_metadata_in_evidence(evidence_record)
    # Canonical ledger holds only the mapping commitment (hash), not plaintext mapping.
    # Chain links are hashes only; commitment lives on the append-only event payload.
    events = list(plain.get("events") or [])
    if not events and isinstance(plain.get("events_dir"), str):
        events_dir = Path(plain["events_dir"])
        if events_dir.is_dir():
            events = list(_rebuild_session_from_events(events_dir).get("events") or [])
    rp_payload = None
    for event in events:
        if event.get("stage") == STAGE_REVIEW_PACKAGE:
            rp_payload = _require_mapping(
                event.get("payload"), "E0B_REVIEW_PACKAGE_PAYLOAD_REQUIRED"
            )
    if not isinstance(rp_payload, Mapping):
        raise GvE0bDv1Error("E0B_REVIEW_PACKAGE_PAYLOAD_REQUIRED")
    commitment = rp_payload.get("mapping_commitment")
    if commitment != mapping.get("mapping_commitment"):
        raise GvE0bDv1Error("E0B_MAPPING_COMMITMENT_MISMATCH")
    if seals["rubric"].get("review_input_mode") != REVIEW_INPUT_MODE_BLINDED:
        raise GvE0bDv1Error("E0B_REVIEW_INPUT_MODE_REQUIRED")
    verify_mapping_randomization(mapping)
    pkg = seals["review_package"]
    if set(pkg.get("arm_a") or {}) != set(pkg.get("arm_b") or {}):
        raise GvE0bDv1Error("E0B_REVIEW_ARM_SCHEMA_MISMATCH")
    if set(pkg.get("arm_a") or {}) != set(REVIEW_ARM_FIELDS):
        raise GvE0bDv1Error("E0B_REVIEW_ARM_SCHEMA_INVALID")


def _append_event(
    *,
    session_path: Path,
    stage: str,
    record_hash: str,
    payload: Mapping[str, Any],
    case_id: str,
    session_nonce: str,
    bundle_hash: str,
    created_at: str,
) -> dict[str, Any]:
    manifest = load_session_manifest(_session_manifest_path(session_path))
    if manifest["session_id"] != session_nonce:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_SESSION_MISMATCH")
    events_dir = _events_dir_for(session_path)
    events_dir.mkdir(parents=True, exist_ok=True)
    existing = _list_event_files(events_dir)
    seq = len(existing)
    if existing:
        session = _rebuild_session_from_events(events_dir)
        prev = _session_tip_from_chain(session["chain"])
        if session["session_nonce"] != session_nonce:
            raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
    else:
        prev = ZERO_CHAIN_HASH
    link = _chain_link(
        session_nonce=session_nonce,
        stage=stage,
        record_hash=record_hash,
        prev_chain_hash=prev,
        seq=seq,
    )
    event = {
        "case_id": case_id,
        "session_nonce": session_nonce,
        "bundle_hash": bundle_hash,
        "created_at": created_at,
        "session_manifest_hash": manifest["session_manifest_hash"],
        "seq": seq,
        "stage": stage,
        "payload": _plain(payload),
        "link": link,
    }
    path = _event_path(events_dir, seq)
    if path.exists():
        raise GvE0bDv1Error(f"E0B_EVENT_ALREADY_EXISTS:{seq}")
    _persist_sealed_json(path, event)
    session = _rebuild_session_from_events(events_dir)
    # Tip index only (reconstructible from events; not the sealed authority).
    index = {
        "case_id": session["case_id"],
        "session_nonce": session["session_nonce"],
        "bundle_hash": session["bundle_hash"],
        "created_at": session["created_at"],
        "session_manifest_hash": session["session_manifest_hash"],
        "session_hash": session["session_hash"],
        "tip_chain_hash": session["chain"][-1]["chain_hash"],
        "event_count": len(session["chain"]),
        "events_dir": str(events_dir),
        "ledger_custody_note": session["ledger_custody_note"],
    }
    _persist_sealed_json(session_path, index)
    return session



def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_fixture_git_identity(source_commit: str, source_tree: str) -> bool:
    return (
        str(source_commit) == FIXTURE_SOURCE_COMMIT
        and str(source_tree) == FIXTURE_SOURCE_TREE
    )


def build_oneshot_authorization(
    *,
    authorization_tag_object: str,
    candidate_commit: str,
    candidate_tree: str,
    preregistration_sha256: str,
    case_id: str = ONESHOT_CASE_ID,
    attempt: int = ONESHOT_ATTEMPT,
) -> dict[str, Any]:
    """Build a deterministic one-shot Attempt-1 authorization body (fixture helper)."""

    tag_object = _require_git_object_id(
        authorization_tag_object, "E0B_ONESHOT_TAG_OBJECT_INVALID"
    )
    auth_commit = _require_git_object_id(
        candidate_commit, "E0B_ONESHOT_CANDIDATE_COMMIT_INVALID"
    )
    auth_tree = _require_git_object_id(
        candidate_tree, "E0B_ONESHOT_CANDIDATE_TREE_INVALID"
    )
    auth_prereg = _require_sha256(
        preregistration_sha256, "E0B_ONESHOT_PREREGISTRATION_HASH_INVALID"
    )
    if case_id != ONESHOT_CASE_ID:
        raise GvE0bDv1Error("E0B_ONESHOT_CASE_MISMATCH")
    if int(attempt) != ONESHOT_ATTEMPT:
        raise GvE0bDv1Error("E0B_ONESHOT_ATTEMPT_NOT_FIRST")
    artifact_hash = domain_hash(
        DOMAIN_ONESHOT_AUTH,
        {
            "authorization_tag_object": tag_object,
            "case_id": ONESHOT_CASE_ID,
            "attempt": ONESHOT_ATTEMPT,
            "candidate_commit": auth_commit,
            "candidate_tree": auth_tree,
            "preregistration_sha256": auth_prereg,
        },
    )
    body = {
        "schema_version": ONESHOT_AUTH_SCHEMA,
        "case_id": ONESHOT_CASE_ID,
        "attempt": ONESHOT_ATTEMPT,
        "authorization_tag_object": tag_object,
        "authorization_artifact_sha256": artifact_hash,
        "candidate_commit": auth_commit,
        "candidate_tree": auth_tree,
        "preregistration_sha256": auth_prereg,
        "claim_boundary": {
            "natural_personhood_proven": False,
            "causal_superiority_proven": False,
            "operational_separation_only": True,
        },
    }
    out = dict(body)
    out["authorization_body_hash"] = domain_hash(DOMAIN_ONESHOT_AUTH, body)
    return out


def verify_oneshot_authorization(
    authorization: Mapping[str, Any] | None,
    *,
    candidate_commit: str,
    candidate_tree: str,
    preregistration_sha256: str,
    expected_case_id: str = ONESHOT_CASE_ID,
    expected_attempt: int = ONESHOT_ATTEMPT,
) -> dict[str, Any]:
    """Fail-closed verification of remotely retained one-shot Attempt-1 auth."""

    if authorization is None:
        raise GvE0bDv1Error("E0B_ONESHOT_AUTHORIZATION_MISSING")
    plain = _require_mapping(authorization, "E0B_ONESHOT_AUTHORIZATION_INVALID")
    if plain.get("schema_version") != ONESHOT_AUTH_SCHEMA:
        raise GvE0bDv1Error("E0B_ONESHOT_SCHEMA_INVALID")
    if plain.get("case_id") != expected_case_id:
        raise GvE0bDv1Error("E0B_ONESHOT_CASE_MISMATCH")
    attempt = plain.get("attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool):
        raise GvE0bDv1Error("E0B_ONESHOT_ATTEMPT_INVALID")
    if attempt != expected_attempt or attempt != ONESHOT_ATTEMPT:
        raise GvE0bDv1Error("E0B_ONESHOT_ATTEMPT_NOT_FIRST")
    tag_object = _require_git_object_id(
        plain.get("authorization_tag_object"), "E0B_ONESHOT_TAG_OBJECT_INVALID"
    )
    artifact_hash = _require_sha256(
        plain.get("authorization_artifact_sha256"),
        "E0B_ONESHOT_ARTIFACT_HASH_INVALID",
    )
    auth_commit = _require_git_object_id(
        plain.get("candidate_commit"), "E0B_ONESHOT_CANDIDATE_COMMIT_INVALID"
    )
    auth_tree = _require_git_object_id(
        plain.get("candidate_tree"), "E0B_ONESHOT_CANDIDATE_TREE_INVALID"
    )
    auth_prereg = _require_sha256(
        plain.get("preregistration_sha256"),
        "E0B_ONESHOT_PREREGISTRATION_HASH_INVALID",
    )
    expected_commit = _require_git_object_id(
        candidate_commit, "E0B_ONESHOT_CANDIDATE_COMMIT_INVALID"
    )
    expected_tree = _require_git_object_id(
        candidate_tree, "E0B_ONESHOT_CANDIDATE_TREE_INVALID"
    )
    expected_prereg = _require_sha256(
        preregistration_sha256, "E0B_ONESHOT_PREREGISTRATION_HASH_INVALID"
    )
    if auth_commit != expected_commit:
        raise GvE0bDv1Error("E0B_ONESHOT_CANDIDATE_COMMIT_MISMATCH")
    if auth_tree != expected_tree:
        raise GvE0bDv1Error("E0B_ONESHOT_CANDIDATE_TREE_MISMATCH")
    if auth_prereg != expected_prereg:
        raise GvE0bDv1Error("E0B_ONESHOT_PREREGISTRATION_MISMATCH")
    # Reconstruct body hash without claimed self hash / envelope fields.
    body = {
        "schema_version": ONESHOT_AUTH_SCHEMA,
        "case_id": expected_case_id,
        "attempt": ONESHOT_ATTEMPT,
        "authorization_tag_object": tag_object,
        "authorization_artifact_sha256": artifact_hash,
        "candidate_commit": auth_commit,
        "candidate_tree": auth_tree,
        "preregistration_sha256": auth_prereg,
        "claim_boundary": {
            "natural_personhood_proven": False,
            "causal_superiority_proven": False,
            "operational_separation_only": True,
        },
    }
    expected_body_hash = domain_hash(DOMAIN_ONESHOT_AUTH, body)
    claimed_body_hash = plain.get("authorization_body_hash")
    if claimed_body_hash is not None:
        claimed = _require_sha256(
            claimed_body_hash, "E0B_ONESHOT_BODY_HASH_INVALID"
        )
        if claimed != expected_body_hash:
            raise GvE0bDv1Error("E0B_ONESHOT_BODY_HASH_MISMATCH")
    # Artifact hash must equal domain hash of the authorization identity envelope
    # excluding mutable free text. Tag object identity is required and non-empty.
    if tag_object == FIXTURE_SOURCE_COMMIT:
        raise GvE0bDv1Error("E0B_ONESHOT_TAG_OBJECT_MUTABLE_OR_UNVERIFIABLE")
    recomputed_artifact = domain_hash(
        DOMAIN_ONESHOT_AUTH,
        {
            "authorization_tag_object": tag_object,
            "case_id": expected_case_id,
            "attempt": ONESHOT_ATTEMPT,
            "candidate_commit": auth_commit,
            "candidate_tree": auth_tree,
            "preregistration_sha256": auth_prereg,
        },
    )
    if artifact_hash != recomputed_artifact:
        raise GvE0bDv1Error("E0B_ONESHOT_ARTIFACT_HASH_MISMATCH")
    out = dict(body)
    out["authorization_body_hash"] = expected_body_hash
    out["authorization_artifact_sha256"] = artifact_hash
    return _freeze(out)


def build_github_rubric_receipt(
    *,
    repository: str,
    authenticated_submitter_id: str,
    submission_commit_sha: str,
    rubric_path: str,
    rubric_blob_oid: str | None,
    rubric_sha256: str,
    receipt_url: str,
    submitted_at: str,
    review_package_hash: str,
    candidate_commit: str,
    candidate_tree: str,
    case_id: str = ONESHOT_CASE_ID,
    attempt: int = ONESHOT_ATTEMPT,
    github_author_login: str | None = None,
    github_committer_login: str | None = None,
) -> dict[str, Any]:
    """Build a machine-readable GitHub external rubric receipt (fixture helper).

    Production eligibility requires v2 fields: provider-authenticated
    ``github_author_login`` / ``github_committer_login``. Submitter id must equal
    the author login (not free-text Git metadata alone).
    """

    submitter = _require_principal_id(
        authenticated_submitter_id, "E0B_RECEIPT_SUBMITTER_REQUIRED"
    )
    author_login = (
        _require_principal_id(github_author_login, "E0B_RECEIPT_GITHUB_AUTHOR_LOGIN_REQUIRED")
        if github_author_login is not None
        else None
    )
    committer_login = (
        _require_principal_id(
            github_committer_login, "E0B_RECEIPT_GITHUB_COMMITTER_LOGIN_REQUIRED"
        )
        if github_committer_login is not None
        else None
    )
    if author_login is None or committer_login is None:
        raise GvE0bDv1Error("E0B_RECEIPT_GITHUB_LOGIN_REQUIRED")
    if author_login != submitter:
        raise GvE0bDv1Error("E0B_RECEIPT_SUBMITTER_NOT_GITHUB_AUTHOR")
    body = {
        "schema_version": GITHUB_RECEIPT_SCHEMA_V2,
        "provider": RECEIPT_PROVIDER_GITHUB,
        "repository": _require_str(
            {"repository": repository}, "repository", "E0B_RECEIPT_REPOSITORY_REQUIRED"
        ),
        "authenticated_submitter_id": submitter,
        "github_author_login": author_login,
        "github_committer_login": committer_login,
        "submission_commit_sha": _require_git_object_id(
            submission_commit_sha, "E0B_RECEIPT_SUBMISSION_COMMIT_INVALID"
        ),
        "rubric_path": _require_str(
            {"rubric_path": rubric_path}, "rubric_path", "E0B_RECEIPT_RUBRIC_PATH_REQUIRED"
        ),
        "rubric_blob_oid": (
            _require_git_object_id(rubric_blob_oid, "E0B_RECEIPT_RUBRIC_BLOB_INVALID")
            if rubric_blob_oid
            else None
        ),
        "rubric_sha256": _require_sha256(
            rubric_sha256, "E0B_RECEIPT_RUBRIC_SHA256_INVALID"
        ),
        "receipt_url": _require_str(
            {"receipt_url": receipt_url}, "receipt_url", "E0B_RECEIPT_URL_REQUIRED"
        ),
        "submitted_at": _require_timestamp(
            {"submitted_at": submitted_at}, "submitted_at", "E0B_RECEIPT_TIMESTAMP_INVALID"
        ),
        "review_package_hash": _require_sha256(
            review_package_hash, "E0B_RECEIPT_REVIEW_PACKAGE_HASH_INVALID"
        ),
        "candidate_commit": _require_git_object_id(
            candidate_commit, "E0B_RECEIPT_CANDIDATE_COMMIT_INVALID"
        ),
        "candidate_tree": _require_git_object_id(
            candidate_tree, "E0B_RECEIPT_CANDIDATE_TREE_INVALID"
        ),
        "case_id": case_id,
        "attempt": int(attempt),
        "claim_boundary": {
            "natural_personhood_proven": False,
            "github_account_is_not_natural_person_proof": True,
            "operational_separation_only": True,
            "provider_authenticated_login_required": True,
        },
    }
    out = dict(body)
    out["receipt_hash"] = domain_hash(DOMAIN_GITHUB_RECEIPT, body)
    return out


def verify_github_rubric_receipt(
    receipt: Mapping[str, Any] | None,
    *,
    rubric_bytes: bytes,
    expected_submitter_id: str,
    expected_candidate_commit: str,
    expected_candidate_tree: str,
    expected_review_package_hash: str,
    expected_case_id: str = ONESHOT_CASE_ID,
    expected_attempt: int = ONESHOT_ATTEMPT,
) -> dict[str, Any]:
    """Verify external GitHub receipt against exact imported rubric bytes."""

    if receipt is None:
        raise GvE0bDv1Error("E0B_EXTERNAL_RECEIPT_MISSING")
    plain = _require_mapping(receipt, "E0B_EXTERNAL_RECEIPT_INVALID")
    schema = plain.get("schema_version")
    if schema not in {GITHUB_RECEIPT_SCHEMA, GITHUB_RECEIPT_SCHEMA_V2}:
        raise GvE0bDv1Error("E0B_RECEIPT_SCHEMA_INVALID")
    # v1 free-text submitter receipts are no longer production-eligible.
    if schema != GITHUB_RECEIPT_SCHEMA_V2:
        raise GvE0bDv1Error("E0B_RECEIPT_SCHEMA_V2_REQUIRED")
    if plain.get("provider") != RECEIPT_PROVIDER_GITHUB:
        raise GvE0bDv1Error("E0B_RECEIPT_PROVIDER_INVALID")
    for field in (
        "repository",
        "authenticated_submitter_id",
        "github_author_login",
        "github_committer_login",
        "submission_commit_sha",
        "rubric_path",
        "rubric_sha256",
        "receipt_url",
        "submitted_at",
        "review_package_hash",
        "candidate_commit",
        "candidate_tree",
        "case_id",
        "attempt",
    ):
        if plain.get(field) in (None, ""):
            raise GvE0bDv1Error(f"E0B_RECEIPT_FIELD_MISSING:{field}")
    submitter = _require_principal_id(
        plain.get("authenticated_submitter_id"), "E0B_RECEIPT_SUBMITTER_REQUIRED"
    )
    author_login = _require_principal_id(
        plain.get("github_author_login"), "E0B_RECEIPT_GITHUB_AUTHOR_LOGIN_REQUIRED"
    )
    committer_login = _require_principal_id(
        plain.get("github_committer_login"),
        "E0B_RECEIPT_GITHUB_COMMITTER_LOGIN_REQUIRED",
    )
    expected_submitter = _require_principal_id(
        expected_submitter_id, "E0B_RECEIPT_SUBMITTER_REQUIRED"
    )
    if submitter != expected_submitter:
        raise GvE0bDv1Error("E0B_RECEIPT_SUBMITTER_MISMATCH")
    if author_login != submitter:
        raise GvE0bDv1Error("E0B_RECEIPT_SUBMITTER_NOT_GITHUB_AUTHOR")
    if plain.get("case_id") != expected_case_id:
        raise GvE0bDv1Error("E0B_RECEIPT_CASE_MISMATCH")
    attempt = plain.get("attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool):
        raise GvE0bDv1Error("E0B_RECEIPT_ATTEMPT_INVALID")
    if attempt != expected_attempt:
        raise GvE0bDv1Error("E0B_RECEIPT_ATTEMPT_MISMATCH")
    receipt_commit = _require_git_object_id(
        plain.get("candidate_commit"), "E0B_RECEIPT_CANDIDATE_COMMIT_INVALID"
    )
    receipt_tree = _require_git_object_id(
        plain.get("candidate_tree"), "E0B_RECEIPT_CANDIDATE_TREE_INVALID"
    )
    expected_commit = _require_git_object_id(
        expected_candidate_commit, "E0B_RECEIPT_CANDIDATE_COMMIT_INVALID"
    )
    expected_tree = _require_git_object_id(
        expected_candidate_tree, "E0B_RECEIPT_CANDIDATE_TREE_INVALID"
    )
    if receipt_commit != expected_commit:
        raise GvE0bDv1Error("E0B_RECEIPT_CANDIDATE_COMMIT_MISMATCH")
    if receipt_tree != expected_tree:
        raise GvE0bDv1Error("E0B_RECEIPT_CANDIDATE_TREE_MISMATCH")
    pkg_hash = _require_sha256(
        plain.get("review_package_hash"), "E0B_RECEIPT_REVIEW_PACKAGE_HASH_INVALID"
    )
    expected_pkg = _require_sha256(
        expected_review_package_hash, "E0B_RECEIPT_REVIEW_PACKAGE_HASH_INVALID"
    )
    if pkg_hash != expected_pkg:
        raise GvE0bDv1Error("E0B_RECEIPT_REVIEW_PACKAGE_HASH_MISMATCH")
    claimed_rubric_sha = _require_sha256(
        plain.get("rubric_sha256"), "E0B_RECEIPT_RUBRIC_SHA256_INVALID"
    )
    actual_rubric_sha = _sha256_hex(rubric_bytes)
    if claimed_rubric_sha != actual_rubric_sha:
        raise GvE0bDv1Error("E0B_RECEIPT_RUBRIC_BYTE_MISMATCH")
    _require_git_object_id(
        plain.get("submission_commit_sha"), "E0B_RECEIPT_SUBMISSION_COMMIT_INVALID"
    )
    _require_str(plain, "repository", "E0B_RECEIPT_REPOSITORY_REQUIRED")
    _require_str(plain, "rubric_path", "E0B_RECEIPT_RUBRIC_PATH_REQUIRED")
    _require_str(plain, "receipt_url", "E0B_RECEIPT_URL_REQUIRED")
    _require_timestamp(plain, "submitted_at", "E0B_RECEIPT_TIMESTAMP_INVALID")
    blob_oid = plain.get("rubric_blob_oid")
    if blob_oid is not None:
        _require_git_object_id(blob_oid, "E0B_RECEIPT_RUBRIC_BLOB_INVALID")
    body = {
        "schema_version": GITHUB_RECEIPT_SCHEMA_V2,
        "provider": RECEIPT_PROVIDER_GITHUB,
        "repository": plain["repository"],
        "authenticated_submitter_id": submitter,
        "github_author_login": author_login,
        "github_committer_login": committer_login,
        "submission_commit_sha": plain["submission_commit_sha"],
        "rubric_path": plain["rubric_path"],
        "rubric_blob_oid": blob_oid,
        "rubric_sha256": claimed_rubric_sha,
        "receipt_url": plain["receipt_url"],
        "submitted_at": plain["submitted_at"],
        "review_package_hash": pkg_hash,
        "candidate_commit": receipt_commit,
        "candidate_tree": receipt_tree,
        "case_id": expected_case_id,
        "attempt": expected_attempt,
        "claim_boundary": {
            "natural_personhood_proven": False,
            "github_account_is_not_natural_person_proof": True,
            "operational_separation_only": True,
            "provider_authenticated_login_required": True,
        },
    }
    expected_receipt_hash = domain_hash(DOMAIN_GITHUB_RECEIPT, body)
    claimed_receipt_hash = plain.get("receipt_hash")
    if claimed_receipt_hash is not None:
        claimed = _require_sha256(
            claimed_receipt_hash, "E0B_RECEIPT_HASH_INVALID"
        )
        if claimed != expected_receipt_hash:
            raise GvE0bDv1Error("E0B_RECEIPT_HASH_MISMATCH")
    out = dict(body)
    out["receipt_hash"] = expected_receipt_hash
    return _freeze(out)


def import_external_rubric_submission(
    *,
    receipt: Mapping[str, Any],
    rubric_path: Path,
    expected_submitter_id: str,
    expected_candidate_commit: str,
    expected_candidate_tree: str,
    expected_review_package_hash: str,
    expected_case_id: str = ONESHOT_CASE_ID,
    expected_attempt: int = ONESHOT_ATTEMPT,
) -> dict[str, Any]:
    """Load exact external rubric bytes and bind a verified GitHub receipt.

    Rejects operator-authored replacement bytes that do not match the receipt.
    Does not prove natural-person identity; only authenticated-account separation.
    """

    path = Path(rubric_path)
    if not path.is_file():
        raise GvE0bDv1Error("E0B_EXTERNAL_RUBRIC_PATH_MISSING")
    rubric_bytes = path.read_bytes()
    verified_receipt = verify_github_rubric_receipt(
        receipt,
        rubric_bytes=rubric_bytes,
        expected_submitter_id=expected_submitter_id,
        expected_candidate_commit=expected_candidate_commit,
        expected_candidate_tree=expected_candidate_tree,
        expected_review_package_hash=expected_review_package_hash,
        expected_case_id=expected_case_id,
        expected_attempt=expected_attempt,
    )
    try:
        authoring = json.loads(rubric_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GvE0bDv1Error("E0B_EXTERNAL_RUBRIC_JSON_INVALID") from exc
    if not isinstance(authoring, dict):
        raise GvE0bDv1Error("E0B_EXTERNAL_RUBRIC_JSON_INVALID")
    # Fail closed if operator tries to override scores after external seal.
    return {
        "authoring": authoring,
        "rubric_bytes_sha256": _sha256_hex(rubric_bytes),
        "receipt": _plain(verified_receipt),
    }


def assert_mapping_reveal_allowed(
    *,
    rubric: Mapping[str, Any],
    revealed_exists: bool,
) -> None:
    """Mapping reveal is allowed only after receipt-bound rubric seal (real path)."""

    plain = _plain(rubric)
    auth = plain.get("authorship_kind")
    if auth == AUTH_REAL_REVIEWER:
        receipt = plain.get("external_submission_receipt")
        if not isinstance(receipt, Mapping) or not receipt.get("receipt_hash"):
            raise GvE0bDv1Error("E0B_MAPPING_REVEAL_BEFORE_RECEIPT_BOUND_RUBRIC")
        if revealed_exists is False:
            # caller is about to reveal; receipt bound is enough
            return
    return


def open_capture_session(
    *,
    bundle: Mapping[str, Any] | None = None,
    session_path: Path = DEFAULT_SESSION_PATH,
    clock: CaptureClock | None = None,
    source_commit: str = "0" * 40,
    source_tree: str = "1" * 40,
    protocol_freeze_manifest_sha256: str = "4" * 64,
    operator_principal_id: str = "OP_FIXTURE_1",
    reviewer_principal_id: str = "REV_FIXTURE_1",
    authoring_template_paths: Mapping[str, Path] | None = None,
    oneshot_authorization: Mapping[str, Any] | None = None,
    preregistration_sha256: str | None = None,
) -> Mapping[str, Any]:
    """Open one manifest-bound append-only capture session.

    Production callers must supply the exact Git commit/tree, the reserved
    operator/reviewer principal IDs, the three pristine authoring templates,
    and a remotely retained one-shot Attempt-1 authorization identity.
    Fixture defaults exist only for deterministic engine tests.
    """

    clk = clock or WallClock()
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    events_dir = _events_dir_for(session_path)
    if _list_event_files(events_dir):
        raise GvE0bDv1Error("E0B_SESSION_ALREADY_OPEN")
    fixture_git = _is_fixture_git_identity(source_commit, source_tree)
    oneshot_bound: dict[str, Any] | None = None
    if not fixture_git:
        if preregistration_sha256 is None:
            raise GvE0bDv1Error("E0B_ONESHOT_PREREGISTRATION_HASH_INVALID")
        oneshot_bound = _plain(
            verify_oneshot_authorization(
                oneshot_authorization,
                candidate_commit=source_commit,
                candidate_tree=source_tree,
                preregistration_sha256=preregistration_sha256,
            )
        )
    elif oneshot_authorization is not None:
        # Explicit fixture-supplied authorization still validated when provided.
        if preregistration_sha256 is None:
            raise GvE0bDv1Error("E0B_ONESHOT_PREREGISTRATION_HASH_INVALID")
        oneshot_bound = _plain(
            verify_oneshot_authorization(
                oneshot_authorization,
                candidate_commit=source_commit,
                candidate_tree=source_tree,
                preregistration_sha256=preregistration_sha256,
            )
        )
    manifest_path = _session_manifest_path(session_path)
    if manifest_path.exists():
        manifest = load_session_manifest(manifest_path)
        session_nonce = str(manifest["session_id"])
        created_at = str(manifest["budget_started_at"])
        if manifest["source_commit"] != source_commit or manifest["source_tree"] != source_tree:
            raise GvE0bDv1Error("E0B_SESSION_MANIFEST_GIT_MISMATCH")
        if manifest["protocol_freeze_manifest_sha256"] != protocol_freeze_manifest_sha256:
            raise GvE0bDv1Error("E0B_SESSION_MANIFEST_PROTOCOL_FREEZE_MISMATCH")
        if manifest["operator_principal_id"] != operator_principal_id:
            raise GvE0bDv1Error("E0B_SESSION_MANIFEST_OPERATOR_MISMATCH")
        if manifest["reviewer_principal_id"] != reviewer_principal_id:
            raise GvE0bDv1Error("E0B_SESSION_MANIFEST_REVIEWER_MISMATCH")
        if oneshot_bound is not None:
            bound = manifest.get("oneshot_authorization")
            if not isinstance(bound, Mapping):
                raise GvE0bDv1Error("E0B_ONESHOT_AUTHORIZATION_MISSING")
            if bound.get("authorization_body_hash") != oneshot_bound.get(
                "authorization_body_hash"
            ):
                raise GvE0bDv1Error("E0B_ONESHOT_BODY_HASH_MISMATCH")
    else:
        created_at = clk.now()
        session_nonce = secrets.token_hex(32)
        if authoring_template_paths is None:
            descriptors = _in_memory_authoring_template_descriptors()
        else:
            if set(authoring_template_paths) != {"baseline", "post", "rubric"}:
                raise GvE0bDv1Error("E0B_AUTHORING_TEMPLATE_SET_INVALID")
            descriptors = [
                _authoring_template_descriptor(role, authoring_template_paths[role])
                for role in ("baseline", "post", "rubric")
            ]
        manifest = _build_session_manifest(
            session_id=session_nonce,
            source_commit=source_commit,
            source_tree=source_tree,
            protocol_freeze_manifest_sha256=protocol_freeze_manifest_sha256,
            operator_principal_id=operator_principal_id,
            reviewer_principal_id=reviewer_principal_id,
            budget_started_at=created_at,
            authoring_templates=descriptors,
            oneshot_authorization=oneshot_bound,
        )
        _create_sealed_json(manifest_path, manifest)
    open_body = {
        "case_id": CASE_ID,
        "session_nonce": session_nonce,
        "bundle_hash": bndl["bundle_hash"],
        "created_at": created_at,
        "session_manifest_hash": manifest["session_manifest_hash"],
    }
    open_hash = domain_hash(DOMAIN_SESSION, open_body)
    session = _append_event(
        session_path=session_path,
        stage=STAGE_SESSION_OPEN,
        record_hash=open_hash,
        payload=open_body,
        case_id=CASE_ID,
        session_nonce=session_nonce,
        bundle_hash=bndl["bundle_hash"],
        created_at=created_at,
    )
    append_capture_checkpoint(
        session_path=session_path,
        operation="OPEN_SESSION",
        state=CAPTURE_STATE_RESUMABLE,
        detail="session_manifest_and_session_open_committed",
        clock=clk,
    )
    return _freeze(session)


def load_capture_session(session_path: Path = DEFAULT_SESSION_PATH) -> dict[str, Any]:
    manifest = load_session_manifest(_session_manifest_path(session_path))
    events_dir = _events_dir_for(session_path)
    session = _rebuild_session_from_events(events_dir)
    verify_session_chain(session)
    if session["session_nonce"] != manifest["session_id"]:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_SESSION_MISMATCH")
    if session["session_manifest_hash"] != manifest["session_manifest_hash"]:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_MISMATCH")
    session["session_manifest"] = manifest
    return session


def _find_open_payload(session: Mapping[str, Any], open_stage: str) -> dict[str, Any]:
    for event in session.get("events") or []:
        if event.get("stage") == open_stage:
            return _require_mapping(event.get("payload"), "E0B_OPEN_PAYLOAD_REQUIRED")
    raise GvE0bDv1Error(f"E0B_ARM_NOT_OPEN:{open_stage}")


def stage_open_arm(
    arm: str,
    *,
    session_path: Path = DEFAULT_SESSION_PATH,
    clock: CaptureClock | None = None,
    allowed_budget_minutes: int = BUDGET_MINUTES,
) -> Mapping[str, Any]:
    """System-stamp arm open as a sealed chain event (no mutable open_arms map)."""

    if arm not in {ARM_BASELINE, ARM_POST}:
        raise GvE0bDv1Error("E0B_ARM_UNKNOWN")
    if int(allowed_budget_minutes) != BUDGET_MINUTES:
        raise GvE0bDv1Error("E0B_BUDGET_CONFIG_INVALID")
    operation = "OPEN_BASELINE" if arm == ARM_BASELINE else "OPEN_POST"
    _require_active_checkpoint_for_authoritative_stage(session_path, operation)
    clk = clock or WallClock()
    session = load_capture_session(session_path)
    stages = [e["stage"] for e in session["chain"]]
    open_stage = STAGE_BASELINE_OPEN if arm == ARM_BASELINE else STAGE_POST_OPEN
    if open_stage in stages:
        raise GvE0bDv1Error(f"E0B_ARM_ALREADY_OPEN:{arm}")
    if arm == ARM_BASELINE and stages != [STAGE_SESSION_OPEN]:
        raise GvE0bDv1Error("E0B_CHAIN_STAGE_ORDER")
    if arm == ARM_POST and stages != [
        STAGE_SESSION_OPEN,
        STAGE_BASELINE_OPEN,
        STAGE_BASELINE_CLOSE,
        STAGE_PACKET,
    ]:
        raise GvE0bDv1Error("E0B_CHAIN_STAGE_ORDER")
    opened_at = clk.now()
    deadline_at = _add_minutes(opened_at, BUDGET_MINUTES)
    payload = {
        "arm": arm,
        "opened_at": opened_at,
        "deadline_at": deadline_at,
        "allowed_budget_minutes": BUDGET_MINUTES,
        "session_nonce": session["session_nonce"],
        "prev_chain_hash": _session_tip_from_chain(session["chain"]),
    }
    open_event_hash = domain_hash(DOMAIN_ARM_OPEN, payload)
    payload = {**payload, "open_event_hash": open_event_hash}
    session = _append_event(
        session_path=session_path,
        stage=open_stage,
        record_hash=open_event_hash,
        payload=payload,
        case_id=session["case_id"],
        session_nonce=session["session_nonce"],
        bundle_hash=session["bundle_hash"],
        created_at=session["created_at"],
    )
    return _freeze(payload)


def sealed_adversarial_bundle() -> Mapping[str, Any]:
    """Synthetic G08 fixture: two indispensable sources contradict on one fact."""

    body = {
        "case_id": CASE_ID,
        "protocol_id": PROTOCOL_ID,
        "subject": SUBJECT,
        "module": MODULE,
        "decision_timestamp": "2026-07-19T12:00:00.000000Z",
        "information_cutoff": "2026-07-19T12:00:00.000000Z",
        "run_class": RUN_CLASS_SYNTHETIC,
        "indispensable_claims": [
            {
                "source_id": "SRC_A_FAB_UTIL_SYNTH",
                "indispensable": True,
                "claim_family": "C1_PHYSICAL_RELIEF_SLOWER",
                "fact_key": "qualified_sellable_supply_relief_quarters",
                "value": 8,
                "direction": "SLOWER_RELIEF",
                "statement": (
                    "Synthetic fab-utilization note: qualified sellable supply "
                    "relief requires eight quarters."
                ),
            },
            {
                "source_id": "SRC_B_CAPEX_RAMP_SYNTH",
                "indispensable": True,
                "claim_family": "C1_PHYSICAL_RELIEF_SLOWER",
                "fact_key": "qualified_sellable_supply_relief_quarters",
                "value": 2,
                "direction": "FASTER_RELIEF",
                "statement": (
                    "Synthetic capex-ramp note: qualified sellable supply relief "
                    "completes in two quarters."
                ),
            },
        ],
        "engine_prohibitions": [
            "average_contradictory_indispensable_values",
            "majority_vote_contradictory_indispensable_values",
            "provider_or_network_access",
            "full_valuation_lattice",
            "hardcoded_human_baseline_or_rubric",
        ],
    }
    digest = domain_hash(DOMAIN_BUNDLE, body)
    out = dict(body)
    out["bundle_hash"] = digest
    return _freeze(out)


def verify_bundle_seal(bundle: Mapping[str, Any]) -> str:
    plain = _plain(bundle)
    claimed = _require_sha256(plain.get("bundle_hash"), "E0B_BUNDLE_HASH_INVALID")
    body = _without_keys(plain, "bundle_hash")
    recomputed = domain_hash(DOMAIN_BUNDLE, body)
    if recomputed != claimed:
        raise GvE0bDv1Error("E0B_BUNDLE_SEAL_MISMATCH")
    return recomputed


def _find_indispensable_contradictions(
    claims: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_key: dict[str, list[Mapping[str, Any]]] = {}
    for claim in claims:
        if not claim.get("indispensable"):
            continue
        key = str(claim.get("fact_key") or "")
        by_key.setdefault(key, []).append(claim)
    contradictions: list[dict[str, Any]] = []
    for fact_key, group in sorted(by_key.items()):
        values = {item.get("value") for item in group}
        directions = {item.get("direction") for item in group}
        if len(values) > 1 or len(directions) > 1:
            contradictions.append(
                {
                    "fact_key": fact_key,
                    "source_ids": [str(item.get("source_id")) for item in group],
                    "values": sorted(values, key=lambda v: str(v)),
                    "directions": sorted(str(d) for d in directions),
                    "resolution": "BLOCK_NO_AVERAGE_NO_MAJORITY",
                }
            )
    return contradictions


def build_godview_packet(
    *,
    bundle: Mapping[str, Any] | None = None,
    generated_at: str,
    session_nonce: str,
    prev_chain_hash: str,
) -> Mapping[str, Any]:
    b_plain = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(b_plain)
    claims = list(b_plain.get("indispensable_claims") or [])
    if not claims:
        raise GvE0bDv1Error("E0B_BUNDLE_CLAIMS_REQUIRED")
    contradictions = _find_indispensable_contradictions(claims)
    if not contradictions:
        raise GvE0bDv1Error("E0B_G08_EXPECTS_CONTRADICTION")
    ts = _require_generated_at(generated_at)
    body = {
        "case_id": CASE_ID,
        "arm": "GODVIEW_PACKET",
        "bundle_hash": b_plain["bundle_hash"],
        "generated_at": ts,
        "session_nonce": _require_str(
            {"session_nonce": session_nonce}, "session_nonce", "E0B_SESSION_NONCE_REQUIRED"
        ),
        "prev_chain_hash": _require_sha256(prev_chain_hash, "E0B_CHAIN_PREV_INVALID"),
        "run_state": RUN_STATE_BLOCKED,
        "block_reason": BLOCK_REASON,
        "acceptance_case": "G08",
        "run_class": RUN_CLASS_SYNTHETIC,
        "research_action": RESEARCH_ACTION_HOLD,
        "portfolio_action": PORTFOLIO_ACTION_NO_POSITION,
        "candidate": "NONE",
        "contradictions": contradictions,
        "engine_may_not_average": True,
        "engine_may_not_majority_vote": True,
        "missing_evidence": [],
        "falsifiers": [
            {
                "falsifier_id": "F_G08_INDISPENSABLE_CONTRADICTION",
                "fact_key": item["fact_key"],
                "source_ids": item["source_ids"],
            }
            for item in contradictions
        ],
        "alpha_claim": False,
        "rationale": (
            "Indispensable sources contradict on qualified sellable supply relief "
            "quarters (8 vs 2). Engine blocks without averaging or majority vote."
        ),
    }
    digest = domain_hash(DOMAIN_PACKET, body)
    out = dict(body)
    out["packet_hash"] = digest
    return _freeze(out)


def verify_packet_seal(packet: Mapping[str, Any]) -> str:
    plain = _plain(packet)
    claimed = _require_sha256(plain.get("packet_hash"), "E0B_PACKET_HASH_INVALID")
    body = _without_keys(plain, "packet_hash")
    recomputed = domain_hash(DOMAIN_PACKET, body)
    if recomputed != claimed:
        raise GvE0bDv1Error("E0B_PACKET_SEAL_MISMATCH")
    return recomputed


def load_packet_seal(path: Path) -> Mapping[str, Any]:
    raw = _load_json_object(path)
    if "packet_hash" not in raw:
        raise GvE0bDv1Error("E0B_PACKET_UNSEALED")
    verify_packet_seal(raw)
    return _freeze(_plain(raw))


def _stamp_decision_timing(
    *,
    open_payload: Mapping[str, Any],
    ended_at: str,
) -> dict[str, Any]:
    opened_at = _require_timestamp(open_payload, "opened_at", "E0B_ARM_STARTED_REQUIRED")
    deadline_at = _require_timestamp(open_payload, "deadline_at", "E0B_DEADLINE_REQUIRED")
    open_event_hash = _require_sha256(
        open_payload.get("open_event_hash"), "E0B_OPEN_EVENT_HASH_INVALID"
    )
    allowed = int(open_payload.get("allowed_budget_minutes", -1))
    if allowed != BUDGET_MINUTES:
        raise GvE0bDv1Error("E0B_BUDGET_CONFIG_MISMATCH")
    if ended_at > deadline_at:
        raise GvE0bDv1Error("E0B_BUDGET_EXCEEDED")
    elapsed = _elapsed_seconds(opened_at, ended_at)
    max_seconds = BUDGET_MINUTES * 60
    if elapsed > max_seconds:
        raise GvE0bDv1Error("E0B_BUDGET_EXCEEDED")
    return {
        "arm_started_at": opened_at,
        "arm_ended_at": ended_at,
        "sealed_at": ended_at,
        "arm_opened_event_hash": open_event_hash,
        "allowed_budget_minutes": BUDGET_MINUTES,
        "elapsed_seconds": elapsed,
        "human_analysis_time_minutes": elapsed // 60,
        "equal_budget_attestation": True,
    }


def _validate_decision_arm(
    record: Mapping[str, Any],
    *,
    expected_arm: str,
    allowed_auth: frozenset[str],
) -> dict[str, Any]:
    plain = _require_mapping(record, "E0B_DECISION_RECORD_INVALID")
    if plain.get("case_id") != CASE_ID:
        raise GvE0bDv1Error("E0B_CASE_ID_MISMATCH")
    if plain.get("arm") != expected_arm:
        raise GvE0bDv1Error("E0B_ARM_MISMATCH")
    auth = _require_str(plain, "authorship_kind", "E0B_AUTHORSHIP_REQUIRED")
    if auth not in allowed_auth:
        raise GvE0bDv1Error("E0B_AUTHORSHIP_INVALID")
    # Reject null/unselected and template sentinels before any seal.
    if plain.get("operator_id") is None:
        raise GvE0bDv1Error("E0B_OPERATOR_REQUIRED")
    if plain.get("action") is None:
        raise GvE0bDv1Error("E0B_ACTION_REQUIRED")
    if plain.get("rationale") is None or plain.get("rationale") == "":
        raise GvE0bDv1Error("E0B_RATIONALE_REQUIRED")
    operator_id = _reject_placeholder_identity(
        plain.get("operator_id"), "E0B_OPERATOR_REQUIRED"
    )
    arm_started_at = _require_timestamp(plain, "arm_started_at", "E0B_ARM_STARTED_REQUIRED")
    arm_ended_at = _require_timestamp(plain, "arm_ended_at", "E0B_ARM_ENDED_REQUIRED")
    elapsed = int(plain.get("elapsed_seconds", -1))
    if elapsed < 0:
        elapsed = _elapsed_seconds(arm_started_at, arm_ended_at)
    allowed = int(plain.get("allowed_budget_minutes", -1))
    if allowed != BUDGET_MINUTES:
        raise GvE0bDv1Error("E0B_BUDGET_CONFIG_MISMATCH")
    if elapsed > allowed * 60:
        raise GvE0bDv1Error("E0B_BUDGET_EXCEEDED")
    if arm_ended_at <= arm_started_at:
        raise GvE0bDv1Error("E0B_ARM_END_BEFORE_START")
    open_hash = _require_sha256(
        plain.get("arm_opened_event_hash"), "E0B_OPEN_EVENT_HASH_INVALID"
    )
    session_nonce = _require_str(plain, "session_nonce", "E0B_SESSION_NONCE_REQUIRED")
    prev_chain_hash = _require_sha256(
        plain.get("prev_chain_hash"), "E0B_CHAIN_PREV_INVALID"
    )
    sealed_at = arm_ended_at
    if "sealed_at" in plain and plain["sealed_at"] != sealed_at:
        raise GvE0bDv1Error("E0B_SEALED_AT_MUST_MATCH_ARM_END")
    bundle_hash = _require_sha256(plain.get("bundle_hash"), "E0B_BUNDLE_HASH_INVALID")
    _require_bool(plain, "equal_budget_attestation", True, "E0B_EQUAL_BUDGET_REQUIRED")
    _require_bool(
        plain, "outside_research_attestation", False, "E0B_OUTSIDE_RESEARCH_FORBIDDEN"
    )
    _require_bool(
        plain,
        "post_cutoff_information_attestation",
        False,
        "E0B_POST_CUTOFF_FORBIDDEN",
    )
    action = _require_str(plain, "action", "E0B_ACTION_REQUIRED")
    if action not in ALLOWED_ACTIONS:
        raise GvE0bDv1Error("E0B_ACTION_INVALID")
    rationale = _require_str(plain, "rationale", "E0B_RATIONALE_REQUIRED")
    if plain.get("alpha_claim") is not False:
        raise GvE0bDv1Error("E0B_ALPHA_CLAIM_FORBIDDEN")
    for key in ("missing_evidence", "falsifiers", "contradictions_recognized"):
        if not isinstance(plain.get(key), list):
            raise GvE0bDv1Error(f"E0B_{key.upper()}_REQUIRED")
    return {
        "case_id": CASE_ID,
        "arm": expected_arm,
        "authorship_kind": auth,
        "operator_id": operator_id,
        "arm_started_at": arm_started_at,
        "arm_ended_at": arm_ended_at,
        "sealed_at": sealed_at,
        "arm_opened_event_hash": open_hash,
        "session_nonce": session_nonce,
        "prev_chain_hash": prev_chain_hash,
        "bundle_hash": bundle_hash,
        "allowed_budget_minutes": BUDGET_MINUTES,
        "elapsed_seconds": elapsed,
        "human_analysis_time_minutes": elapsed // 60,
        "equal_budget_attestation": True,
        "outside_research_attestation": False,
        "post_cutoff_information_attestation": False,
        "action": action,
        "rationale": rationale,
        "missing_evidence": list(plain["missing_evidence"]),
        "falsifiers": list(plain["falsifiers"]),
        "contradictions_recognized": list(plain["contradictions_recognized"]),
        "alpha_claim": False,
    }


def seal_baseline_record(record: Mapping[str, Any]) -> Mapping[str, Any]:
    body = _validate_decision_arm(
        record,
        expected_arm="HUMAN_BASELINE",
        allowed_auth=frozenset({AUTH_FIXTURE, AUTH_REAL_OPERATOR}),
    )
    if "sealed_before_packet" in record and record["sealed_before_packet"] is not True:
        raise GvE0bDv1Error("E0B_BASELINE_MUST_PREDATE_PACKET_FLAG")
    body["sealed_before_packet"] = True
    # Human custody attestation (not personhood proof). REAL operators must
    # actively set true at capture time; fixtures may be false for tests.
    fresh = record.get("operator_had_not_seen_packet_or_expected_outcome")
    if body["authorship_kind"] == AUTH_REAL_OPERATOR:
        if fresh is not True:
            raise GvE0bDv1Error("E0B_OPERATOR_FRESHNESS_REQUIRED")
        body["operator_had_not_seen_packet_or_expected_outcome"] = True
    else:
        body["operator_had_not_seen_packet_or_expected_outcome"] = fresh is True
    digest = domain_hash(DOMAIN_BASELINE, body)
    out = dict(body)
    out["baseline_hash"] = digest
    return _freeze(out)


def verify_baseline_seal(baseline: Mapping[str, Any]) -> str:
    plain = _plain(baseline)
    claimed = _require_sha256(plain.get("baseline_hash"), "E0B_BASELINE_HASH_INVALID")
    body = _without_keys(plain, "baseline_hash")
    sealed = seal_baseline_record(body)
    if sealed["baseline_hash"] != claimed:
        raise GvE0bDv1Error("E0B_BASELINE_SEAL_MISMATCH")
    return claimed


def load_baseline_seal(
    path: Path,
    *,
    expected_bundle_hash: str,
) -> Mapping[str, Any]:
    raw = _load_json_object(path)
    if "baseline_hash" not in raw:
        raise GvE0bDv1Error("E0B_BASELINE_UNSEALED")
    verify_baseline_seal(raw)
    sealed = _freeze(_plain(raw))
    if sealed["bundle_hash"] != expected_bundle_hash:
        raise GvE0bDv1Error("E0B_BASELINE_BUNDLE_MISMATCH")
    return sealed


def seal_post_packet_record(
    record: Mapping[str, Any],
    *,
    packet: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> Mapping[str, Any]:
    p = _plain(packet)
    b = _plain(baseline)
    verify_packet_seal(p)
    verify_baseline_seal(b)
    body = _validate_decision_arm(
        record,
        expected_arm="HUMAN_POST_PACKET",
        allowed_auth=frozenset({AUTH_FIXTURE, AUTH_REAL_OPERATOR}),
    )
    packet_hash = _require_sha256(p.get("packet_hash"), "E0B_PACKET_HASH_INVALID")
    claimed_packet = record.get("packet_hash")
    if claimed_packet is not None and claimed_packet != packet_hash:
        raise GvE0bDv1Error("E0B_POST_PACKET_HASH_MISMATCH")
    claimed_baseline = record.get("baseline_hash")
    if claimed_baseline is not None and claimed_baseline != b["baseline_hash"]:
        raise GvE0bDv1Error("E0B_POST_BASELINE_HASH_MISMATCH")
    if body["bundle_hash"] != b["bundle_hash"] or body["bundle_hash"] != p["bundle_hash"]:
        raise GvE0bDv1Error("E0B_POST_BUNDLE_MISMATCH")
    if body["operator_id"] != b["operator_id"]:
        raise GvE0bDv1Error("E0B_POST_OPERATOR_MUST_MATCH_BASELINE")
    if body["authorship_kind"] != b["authorship_kind"]:
        raise GvE0bDv1Error("E0B_POST_AUTHORSHIP_KIND_MISMATCH")
    if body["session_nonce"] != b["session_nonce"]:
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
    if body["session_nonce"] != p.get("session_nonce"):
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
    if int(body["allowed_budget_minutes"]) != int(b["allowed_budget_minutes"]):
        raise GvE0bDv1Error("E0B_UNEQUAL_CONFIGURED_BUDGETS")
    if not (b["sealed_at"] < p["generated_at"] <= body["sealed_at"]):
        raise GvE0bDv1Error("E0B_INVALID_BASELINE_SEAL_ORDERING")
    portfolio_action = record.get("portfolio_action", PORTFOLIO_ACTION_NO_POSITION)
    if portfolio_action != PORTFOLIO_ACTION_NO_POSITION:
        raise GvE0bDv1Error("E0B_PORTFOLIO_ACTION_MUST_BE_NO_POSITION")
    body["packet_hash"] = packet_hash
    body["baseline_hash"] = b["baseline_hash"]
    body["portfolio_action"] = PORTFOLIO_ACTION_NO_POSITION
    digest = domain_hash(DOMAIN_POST, body)
    out = dict(body)
    out["post_packet_hash"] = digest
    return _freeze(out)


def verify_post_packet_seal(
    post: Mapping[str, Any],
    *,
    packet: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> str:
    plain = _plain(post)
    claimed = _require_sha256(plain.get("post_packet_hash"), "E0B_POST_HASH_INVALID")
    body = _without_keys(plain, "post_packet_hash")
    sealed = seal_post_packet_record(body, packet=packet, baseline=baseline)
    if sealed["post_packet_hash"] != claimed:
        raise GvE0bDv1Error("E0B_POST_SEAL_MISMATCH")
    return claimed


def load_post_packet_seal(
    path: Path,
    *,
    packet: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> Mapping[str, Any]:
    raw = _load_json_object(path)
    if "post_packet_hash" not in raw:
        raise GvE0bDv1Error("E0B_POST_UNSEALED")
    verify_post_packet_seal(raw, packet=packet, baseline=baseline)
    return _freeze(_plain(raw))


def _validate_rubric_arm_scores(scores: Any, code: str) -> dict[str, dict[str, Any]]:
    mapping = _require_mapping(scores, code)
    if set(mapping) != set(RUBRIC_ITEMS):
        raise GvE0bDv1Error("E0B_RUBRIC_ITEMS_INVALID")
    out: dict[str, dict[str, Any]] = {}
    for item in RUBRIC_ITEMS:
        entry = _require_mapping(mapping[item], f"E0B_RUBRIC_ITEM_INVALID:{item}")
        score = entry.get("score")
        if score not in (0, 1, 2):
            raise GvE0bDv1Error(f"E0B_RUBRIC_SCORE_INVALID:{item}")
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise GvE0bDv1Error(f"E0B_RUBRIC_REASON_REQUIRED:{item}")
        out[item] = {"score": int(score), "reason": reason.strip()}
    return out


def _project_decision_for_blind(decision: Mapping[str, Any]) -> dict[str, Any]:
    """Project a decision into the canonical review-arm schema (identical keys always)."""

    plain = _plain(decision)
    if plain.get("alpha_claim") is not False:
        raise GvE0bDv1Error("E0B_ALPHA_CLAIM_FORBIDDEN")
    projected = {
        "action": _require_str(plain, "action", "E0B_ACTION_REQUIRED"),
        "rationale": _require_str(plain, "rationale", "E0B_RATIONALE_REQUIRED"),
        "missing_evidence": list(plain.get("missing_evidence") or []),
        "falsifiers": list(plain.get("falsifiers") or []),
        "contradictions_recognized": list(plain.get("contradictions_recognized") or []),
        "bundle_hash": _require_sha256(plain.get("bundle_hash"), "E0B_BUNDLE_HASH_INVALID"),
        "alpha_claim": False,
        "case_id": _require_str(plain, "case_id", "E0B_CASE_ID_MISMATCH"),
    }
    if set(projected) != set(REVIEW_ARM_FIELDS):
        raise GvE0bDv1Error("E0B_REVIEW_ARM_SCHEMA_INVALID")
    if any(key in projected for key in _BLIND_FORBIDDEN_KEYS):
        raise GvE0bDv1Error("E0B_REVIEW_ARM_LEAKS_PROVENANCE")
    return projected


def _arm_assignment_from_rng(raw: bytes) -> tuple[str, str]:
    if not raw:
        raise GvE0bDv1Error("E0B_RNG_PREIMAGE_REQUIRED")
    if raw[0] % 2 == 0:
        return ARM_BASELINE, ARM_POST
    return ARM_POST, ARM_BASELINE


def verify_mapping_randomization(mapping: Mapping[str, Any]) -> None:
    """Verify rng preimage, commitment, and arm assignment parity (final replay)."""

    plain = _plain(mapping)
    preimage_hex = plain.get("rng_bytes_hex")
    if not isinstance(preimage_hex, str) or not preimage_hex:
        raise GvE0bDv1Error("E0B_RNG_PREIMAGE_REQUIRED")
    try:
        raw = bytes.fromhex(preimage_hex)
    except ValueError as exc:
        raise GvE0bDv1Error("E0B_RNG_PREIMAGE_INVALID") from exc
    # Production capture always uses secrets.token_bytes(16); reject other lengths.
    if len(raw) != 16:
        raise GvE0bDv1Error("E0B_RNG_PREIMAGE_LENGTH")
    expected_commitment = domain_hash(DOMAIN_RNG, {"bytes_hex": preimage_hex})
    if plain.get("rng_commitment") != expected_commitment:
        raise GvE0bDv1Error("E0B_RNG_COMMITMENT_MISMATCH")
    arm_a, arm_b = _arm_assignment_from_rng(raw)
    if plain.get("arm_a_source") != arm_a or plain.get("arm_b_source") != arm_b:
        raise GvE0bDv1Error("E0B_RNG_ASSIGNMENT_MISMATCH")


def seal_review_package(
    *,
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    packet: Mapping[str, Any],
    bundle: Mapping[str, Any],
    session_nonce: str,
    prev_chain_hash: str,
    session_manifest_hash: str = "2" * 64,
    rng_bytes: bytes | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build blinded review package + sealed mapping (mapping withheld from export).

    ``rng_bytes`` is fixture/test injection only. Production stages must call
    without it so entropy comes from ``secrets.token_bytes(16)``.
    """

    b = _plain(baseline)
    p = _plain(post)
    pkt = _plain(packet)
    bndl = _plain(bundle)
    verify_baseline_seal(b)
    verify_post_packet_seal(p, packet=pkt, baseline=b)
    verify_packet_seal(pkt)
    verify_bundle_seal(bndl)
    # Random assignment: first byte even => ARM_A=BASELINE, else ARM_A=POST.
    if rng_bytes is None:
        raw = secrets.token_bytes(16)
    else:
        if not isinstance(rng_bytes, (bytes, bytearray)) or len(rng_bytes) != 16:
            raise GvE0bDv1Error("E0B_RNG_PREIMAGE_LENGTH")
        raw = bytes(rng_bytes)
    arm_a_source, arm_b_source = _arm_assignment_from_rng(raw)
    if arm_a_source == ARM_BASELINE:
        arm_a_decision, arm_b_decision = b, p
    else:
        arm_a_decision, arm_b_decision = p, b
    arm_a = _project_decision_for_blind(arm_a_decision)
    arm_b = _project_decision_for_blind(arm_b_decision)
    if set(arm_a) != set(arm_b) or set(arm_a) != set(REVIEW_ARM_FIELDS):
        raise GvE0bDv1Error("E0B_REVIEW_ARM_SCHEMA_MISMATCH")
    package_body = {
        "case_id": CASE_ID,
        "session_nonce": session_nonce,
        "prev_chain_hash": _require_sha256(prev_chain_hash, "E0B_CHAIN_PREV_INVALID"),
        "bundle": bndl,
        "packet_run_state": pkt["run_state"],
        "packet_block_reason": pkt["block_reason"],
        "packet_rationale": pkt["rationale"],
        "packet_contradictions": pkt["contradictions"],
        "instructions": (
            "Score ARM_A and ARM_B independently with the frozen six-item rubric. "
            "Arms are randomly labeled; do not infer baseline vs post order. "
            "Identical evidence bundle, schema, and instructions for both arms."
        ),
        "rubric_items": list(RUBRIC_ITEMS),
        "score_scale": {"min": 0, "max": 2},
        "arm_a": arm_a,
        "arm_b": arm_b,
        "blinding": "MECHANICAL_RANDOM_ARM_LABELS",
        "blinding_custody_model": BLINDING_CUSTODY_MODEL,
        "mapping_withheld": True,
        "review_input_mode_required": REVIEW_INPUT_MODE_BLINDED,
        "session_manifest_hash": _require_sha256(
            session_manifest_hash,
            "E0B_SESSION_MANIFEST_HASH_INVALID",
        ),
        "reviewer_export_boundary": {
            "exact_file_names": sorted(REVIEWER_EXPORT_EXACT_NAMES),
            "private_mapping_excluded": True,
            "session_scoped_directory": True,
            "rubric_template": {
                "artifact_role": AUTHORING_ONLY,
                "template_id": RUBRIC_TEMPLATE_ID,
                "sha256": _sha256_bytes(
                    canonical_document_bytes(blank_rubric_authoring_template())
                ),
            },
        },
    }
    package_hash = domain_hash(DOMAIN_REVIEW_PACKAGE, package_body)
    package = {**package_body, "review_package_hash": package_hash}
    mapping_body = {
        "case_id": CASE_ID,
        "session_nonce": session_nonce,
        "review_package_hash": package_hash,
        "arm_a_source": arm_a_source,
        "arm_b_source": arm_b_source,
        "baseline_hash": b["baseline_hash"],
        "post_packet_hash": p["post_packet_hash"],
        "rng_commitment": domain_hash(DOMAIN_RNG, {"bytes_hex": raw.hex()}),
        "revealed": False,
    }
    mapping_commitment = domain_hash(DOMAIN_REVIEW_MAPPING, mapping_body)
    # Commitment is ledger/export-visible; preimage stays operator-custody only.
    mapping = {
        **mapping_body,
        "mapping_commitment": mapping_commitment,
        "rng_bytes_hex": raw.hex(),
    }
    return package, mapping


def verify_review_package(package: Mapping[str, Any]) -> str:
    plain = _plain(package)
    claimed = _require_sha256(
        plain.get("review_package_hash"), "E0B_REVIEW_PACKAGE_HASH_INVALID"
    )
    body = _without_keys(plain, "review_package_hash")
    if domain_hash(DOMAIN_REVIEW_PACKAGE, body) != claimed:
        raise GvE0bDv1Error("E0B_REVIEW_PACKAGE_SEAL_MISMATCH")
    if plain.get("mapping_withheld") is not True:
        raise GvE0bDv1Error("E0B_REVIEW_PACKAGE_MUST_WITHHOLD_MAPPING")
    if "arm_a_source" in plain or "arm_b_source" in plain:
        raise GvE0bDv1Error("E0B_REVIEW_PACKAGE_LEAKS_MAPPING")
    if plain.get("review_input_mode_required") != REVIEW_INPUT_MODE_BLINDED:
        raise GvE0bDv1Error("E0B_REVIEW_PACKAGE_BLINDING_MODE_REQUIRED")
    _require_sha256(
        plain.get("session_manifest_hash"),
        "E0B_SESSION_MANIFEST_HASH_INVALID",
    )
    boundary = _require_mapping(
        plain.get("reviewer_export_boundary"),
        "E0B_REVIEWER_EXPORT_BOUNDARY_REQUIRED",
    )
    if boundary.get("exact_file_names") != sorted(REVIEWER_EXPORT_EXACT_NAMES):
        raise GvE0bDv1Error("E0B_REVIEWER_EXPORT_BOUNDARY_INVALID")
    if boundary.get("private_mapping_excluded") is not True:
        raise GvE0bDv1Error("E0B_REVIEWER_EXPORT_BOUNDARY_INVALID")
    if boundary.get("session_scoped_directory") is not True:
        raise GvE0bDv1Error("E0B_REVIEWER_EXPORT_BOUNDARY_INVALID")
    template = _require_mapping(
        boundary.get("rubric_template"),
        "E0B_REVIEWER_EXPORT_TEMPLATE_REQUIRED",
    )
    if template.get("artifact_role") != AUTHORING_ONLY:
        raise GvE0bDv1Error("E0B_AUTHORING_ROLE_INVALID")
    if template.get("template_id") != RUBRIC_TEMPLATE_ID:
        raise GvE0bDv1Error("E0B_AUTHORING_TEMPLATE_ID_INVALID")
    expected_template_hash = _sha256_bytes(
        canonical_document_bytes(blank_rubric_authoring_template())
    )
    if template.get("sha256") != expected_template_hash:
        raise GvE0bDv1Error("E0B_AUTHORING_TEMPLATE_HASH_INVALID")
    arm_a = _require_mapping(plain.get("arm_a"), "E0B_REVIEW_ARM_A_REQUIRED")
    arm_b = _require_mapping(plain.get("arm_b"), "E0B_REVIEW_ARM_B_REQUIRED")
    if set(arm_a) != set(arm_b) or set(arm_a) != set(REVIEW_ARM_FIELDS):
        raise GvE0bDv1Error("E0B_REVIEW_ARM_SCHEMA_MISMATCH")
    for forbidden in _BLIND_FORBIDDEN_KEYS:
        if forbidden in arm_a or forbidden in arm_b:
            raise GvE0bDv1Error("E0B_REVIEW_ARM_LEAKS_PROVENANCE")
    return claimed


def verify_review_package_bound_to_records(
    package: Mapping[str, Any],
    mapping: Mapping[str, Any],
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    packet: Mapping[str, Any],
    bundle: Mapping[str, Any],
) -> None:
    """Prove package arms/bundle/packet equal canonical projections under mapping.

    Existing package/mapping seals alone only prove self-consistency of a package
    preimage. This verifier reprojects sealed baseline/post through REVIEW_ARM_FIELDS
    under the verified random assignment and requires exact equality with package
    arm content plus embedded bundle/packet fields.
    """

    b = _plain(baseline)
    p = _plain(post)
    pkt = _plain(packet)
    bndl = _plain(bundle)
    pkg = _plain(package)
    mp = _plain(mapping)
    verify_bundle_seal(bndl)
    verify_baseline_seal(b)
    verify_packet_seal(pkt)
    verify_post_packet_seal(p, packet=pkt, baseline=b)
    verify_review_package(pkg)
    verify_review_mapping(mp, review_package_hash=pkg["review_package_hash"])
    verify_mapping_randomization(mp)
    if mp.get("baseline_hash") != b["baseline_hash"]:
        raise GvE0bDv1Error("E0B_MAPPING_BASELINE_HASH_MISMATCH")
    if mp.get("post_packet_hash") != p["post_packet_hash"]:
        raise GvE0bDv1Error("E0B_MAPPING_POST_HASH_MISMATCH")
    expected_baseline = _project_decision_for_blind(b)
    expected_post = _project_decision_for_blind(p)
    if mp["arm_a_source"] == ARM_BASELINE:
        expected_a, expected_b = expected_baseline, expected_post
    else:
        expected_a, expected_b = expected_post, expected_baseline
    if _plain(pkg.get("arm_a")) != expected_a:
        raise GvE0bDv1Error("E0B_PACKAGE_ARM_A_NOT_CANONICAL")
    if _plain(pkg.get("arm_b")) != expected_b:
        raise GvE0bDv1Error("E0B_PACKAGE_ARM_B_NOT_CANONICAL")
    if _plain(pkg.get("bundle")) != bndl:
        raise GvE0bDv1Error("E0B_PACKAGE_BUNDLE_NOT_CANONICAL")
    if pkg.get("packet_run_state") != pkt.get("run_state"):
        raise GvE0bDv1Error("E0B_PACKAGE_PACKET_STATE_MISMATCH")
    if pkg.get("packet_block_reason") != pkt.get("block_reason"):
        raise GvE0bDv1Error("E0B_PACKAGE_PACKET_REASON_MISMATCH")
    if pkg.get("packet_rationale") != pkt.get("rationale"):
        raise GvE0bDv1Error("E0B_PACKAGE_PACKET_RATIONALE_MISMATCH")
    if _plain(pkg.get("packet_contradictions")) != _plain(pkt.get("contradictions")):
        raise GvE0bDv1Error("E0B_PACKAGE_PACKET_CONTRADICTIONS_MISMATCH")


def verify_review_mapping(
    mapping: Mapping[str, Any],
    *,
    review_package_hash: str,
) -> str:
    plain = _plain(mapping)
    claimed = _require_sha256(
        plain.get("mapping_commitment"), "E0B_MAPPING_COMMITMENT_INVALID"
    )
    # Operator-custody preimage is outside the sealed mapping body.
    body = _without_keys(plain, "mapping_commitment", "rng_bytes_hex")
    if domain_hash(DOMAIN_REVIEW_MAPPING, body) != claimed:
        raise GvE0bDv1Error("E0B_MAPPING_SEAL_MISMATCH")
    if plain.get("review_package_hash") != review_package_hash:
        raise GvE0bDv1Error("E0B_MAPPING_PACKAGE_MISMATCH")
    if set({plain.get("arm_a_source"), plain.get("arm_b_source")}) != {
        ARM_BASELINE,
        ARM_POST,
    }:
        raise GvE0bDv1Error("E0B_MAPPING_ARMS_INVALID")
    return claimed


def seal_rubric_record(
    record: Mapping[str, Any],
    *,
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    packet: Mapping[str, Any],
    review_package: Mapping[str, Any],
    review_mapping: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Seal rubric from blinded ARM_A/ARM_B only; map to baseline/post after input seal.

    No compatibility path for already-mapped baseline_scores/post_scores.
    """

    b = _plain(baseline)
    p = _plain(post)
    pkt = _plain(packet)
    pkg = _plain(review_package)
    mp = _plain(review_mapping)
    verify_baseline_seal(b)
    verify_post_packet_seal(p, packet=pkt, baseline=b)
    verify_review_package(pkg)
    verify_review_mapping(mp, review_package_hash=pkg["review_package_hash"])
    plain = _require_mapping(record, "E0B_RUBRIC_RECORD_INVALID")
    if plain.get("case_id") != CASE_ID:
        raise GvE0bDv1Error("E0B_CASE_ID_MISMATCH")
    has_a = "arm_a_scores" in plain
    has_b = "arm_b_scores" in plain
    has_mapped_labels = "baseline_scores" in plain or "post_scores" in plain
    # Authoring may not supply already-mapped baseline/post scores as the input path.
    # Sealed records may *contain* mapped scores as derived outputs after ARM sealing;
    # re-verify still requires both ARM score blocks and recomputes the mapping.
    if has_mapped_labels and not (has_a and has_b):
        raise GvE0bDv1Error("E0B_RUBRIC_UNBLINDED_SCORES_FORBIDDEN")
    for key in ("baseline", "post", "BASELINE", "POST"):
        if key in plain:
            raise GvE0bDv1Error("E0B_RUBRIC_BASELINE_POST_LABEL_FORBIDDEN")
    if not has_a or not has_b:
        raise GvE0bDv1Error("E0B_RUBRIC_REQUIRES_BOTH_ARM_SCORES")
    arm_a_scores = _validate_rubric_arm_scores(
        plain.get("arm_a_scores"), "E0B_ARM_A_SCORES_REQUIRED"
    )
    arm_b_scores = _validate_rubric_arm_scores(
        plain.get("arm_b_scores"), "E0B_ARM_B_SCORES_REQUIRED"
    )
    # Map blinded arms to baseline/post only after ARM scores are validated.
    if mp["arm_a_source"] == ARM_BASELINE:
        baseline_scores, post_scores = arm_a_scores, arm_b_scores
    else:
        baseline_scores, post_scores = arm_b_scores, arm_a_scores
    auth = _require_str(plain, "authorship_kind", "E0B_RUBRIC_AUTHORSHIP_REQUIRED")
    if auth not in {AUTH_FIXTURE, AUTH_REAL_REVIEWER}:
        raise GvE0bDv1Error("E0B_RUBRIC_AUTHORSHIP_INVALID")
    if plain.get("reviewer_id") is None:
        raise GvE0bDv1Error("E0B_REVIEWER_REQUIRED")
    reviewer_id = _reject_placeholder_identity(
        plain.get("reviewer_id"), "E0B_REVIEWER_REQUIRED"
    )
    if reviewer_id == b["operator_id"]:
        raise GvE0bDv1Error("E0B_REVIEWER_MUST_DIFFER_FROM_OPERATOR")
    if b["authorship_kind"] == AUTH_REAL_OPERATOR and auth != AUTH_REAL_REVIEWER:
        raise GvE0bDv1Error("E0B_REAL_OPERATOR_REQUIRES_REAL_REVIEWER")
    if b["authorship_kind"] == AUTH_FIXTURE and auth != AUTH_FIXTURE:
        raise GvE0bDv1Error("E0B_FIXTURE_OPERATOR_REQUIRES_FIXTURE_REVIEWER")
    scored_at = _require_timestamp(plain, "scored_at", "E0B_SCORED_AT_REQUIRED")
    if scored_at < p["sealed_at"]:
        raise GvE0bDv1Error("E0B_RUBRIC_BEFORE_POST_FORBIDDEN")
    session_nonce = _require_str(plain, "session_nonce", "E0B_SESSION_NONCE_REQUIRED")
    prev_chain_hash = _require_sha256(
        plain.get("prev_chain_hash"), "E0B_CHAIN_PREV_INVALID"
    )
    if session_nonce != b["session_nonce"] or session_nonce != p["session_nonce"]:
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
    if session_nonce != pkt.get("session_nonce") or session_nonce != pkg.get("session_nonce"):
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
    # Reviewer custody attestation (human assertion; not cryptographic personhood).
    existing_custody = plain.get("custody_attestation")
    if isinstance(existing_custody, Mapping):
        custody_src = existing_custody
    else:
        custody_src = plain
    receipt = custody_src.get("reviewer_received_only_blinded_review_package")
    package_attested = custody_src.get("review_package_hash_attested")
    manifest_attested = custody_src.get("session_manifest_hash_attested")
    export_boundary_attested = custody_src.get("reviewer_export_boundary_attested")
    external_receipt_bound: dict[str, Any] | None = None
    if auth == AUTH_REAL_REVIEWER:
        if receipt is not True:
            raise GvE0bDv1Error("E0B_REVIEWER_BLINDED_RECEIPT_REQUIRED")
        if package_attested != pkg["review_package_hash"]:
            raise GvE0bDv1Error("E0B_REVIEWER_PACKAGE_ATTESTATION_MISMATCH")
        if manifest_attested != pkg["session_manifest_hash"]:
            raise GvE0bDv1Error("E0B_REVIEWER_MANIFEST_ATTESTATION_MISMATCH")
        if export_boundary_attested is not True:
            raise GvE0bDv1Error("E0B_REVIEWER_EXPORT_ATTESTATION_REQUIRED")
        raw_ext = plain.get("external_submission_receipt")
        rubric_bytes_sha = plain.get("external_rubric_bytes_sha256")
        if raw_ext is None:
            raise GvE0bDv1Error("E0B_EXTERNAL_RECEIPT_MISSING")
        if not isinstance(rubric_bytes_sha, str) or not SHA256_RE.fullmatch(
            rubric_bytes_sha
        ):
            raise GvE0bDv1Error("E0B_RECEIPT_RUBRIC_SHA256_INVALID")
        # Receipt must already be verified by import_external_rubric_submission;
        # re-check identity fields and hash binding fail-closed.
        ext = _require_mapping(raw_ext, "E0B_EXTERNAL_RECEIPT_INVALID")
        if ext.get("provider") != RECEIPT_PROVIDER_GITHUB:
            raise GvE0bDv1Error("E0B_RECEIPT_PROVIDER_INVALID")
        if ext.get("schema_version") != GITHUB_RECEIPT_SCHEMA_V2:
            raise GvE0bDv1Error("E0B_RECEIPT_SCHEMA_V2_REQUIRED")
        if ext.get("authenticated_submitter_id") != reviewer_id:
            raise GvE0bDv1Error("E0B_RECEIPT_SUBMITTER_MISMATCH")
        author_login = ext.get("github_author_login")
        committer_login = ext.get("github_committer_login")
        if not isinstance(author_login, str) or not author_login.strip():
            raise GvE0bDv1Error("E0B_RECEIPT_GITHUB_AUTHOR_LOGIN_REQUIRED")
        if not isinstance(committer_login, str) or not committer_login.strip():
            raise GvE0bDv1Error("E0B_RECEIPT_GITHUB_COMMITTER_LOGIN_REQUIRED")
        if author_login != reviewer_id:
            raise GvE0bDv1Error("E0B_RECEIPT_SUBMITTER_NOT_GITHUB_AUTHOR")
        if author_login == b.get("operator_id") or author_login == p.get("operator_id"):
            raise GvE0bDv1Error("E0B_RECEIPT_REVIEWER_EQUALS_OPERATOR")
        if ext.get("rubric_sha256") != rubric_bytes_sha:
            raise GvE0bDv1Error("E0B_RECEIPT_RUBRIC_BYTE_MISMATCH")
        if ext.get("review_package_hash") != pkg["review_package_hash"]:
            raise GvE0bDv1Error("E0B_RECEIPT_REVIEW_PACKAGE_HASH_MISMATCH")
        if ext.get("case_id") != ONESHOT_CASE_ID:
            raise GvE0bDv1Error("E0B_RECEIPT_CASE_MISMATCH")
        if ext.get("attempt") != ONESHOT_ATTEMPT:
            raise GvE0bDv1Error("E0B_RECEIPT_ATTEMPT_MISMATCH")
        body_for_hash = {
            "schema_version": GITHUB_RECEIPT_SCHEMA_V2,
            "provider": RECEIPT_PROVIDER_GITHUB,
            "repository": ext.get("repository"),
            "authenticated_submitter_id": ext.get("authenticated_submitter_id"),
            "github_author_login": author_login,
            "github_committer_login": committer_login,
            "submission_commit_sha": ext.get("submission_commit_sha"),
            "rubric_path": ext.get("rubric_path"),
            "rubric_blob_oid": ext.get("rubric_blob_oid"),
            "rubric_sha256": ext.get("rubric_sha256"),
            "receipt_url": ext.get("receipt_url"),
            "submitted_at": ext.get("submitted_at"),
            "review_package_hash": ext.get("review_package_hash"),
            "candidate_commit": ext.get("candidate_commit"),
            "candidate_tree": ext.get("candidate_tree"),
            "case_id": ext.get("case_id"),
            "attempt": ext.get("attempt"),
            "claim_boundary": {
                "natural_personhood_proven": False,
                "github_account_is_not_natural_person_proof": True,
                "operational_separation_only": True,
                "provider_authenticated_login_required": True,
            },
        }
        expected_receipt_hash = domain_hash(DOMAIN_GITHUB_RECEIPT, body_for_hash)
        claimed_rh = ext.get("receipt_hash")
        if claimed_rh != expected_receipt_hash:
            raise GvE0bDv1Error("E0B_RECEIPT_HASH_MISMATCH")
        external_receipt_bound = dict(body_for_hash)
        external_receipt_bound["receipt_hash"] = expected_receipt_hash
    custody = {
        "fresh_operator_attested": custody_src.get("fresh_operator_attested") is True,
        "blinded_review_conditions_attested": (
            custody_src.get("blinded_review_conditions_attested") is True
        ),
        "reviewer_received_only_blinded_review_package": receipt is True,
        "review_package_hash_attested": (
            package_attested
            if auth == AUTH_REAL_REVIEWER
            else pkg["review_package_hash"]
        ),
        "session_manifest_hash_attested": (
            manifest_attested
            if auth == AUTH_REAL_REVIEWER
            else pkg["session_manifest_hash"]
        ),
        "reviewer_export_boundary_attested": (
            export_boundary_attested is True
            if auth == AUTH_REAL_REVIEWER
            else True
        ),
    }
    body = {
        "case_id": CASE_ID,
        "authorship_kind": auth,
        "reviewer_id": reviewer_id,
        "scored_at": scored_at,
        "session_nonce": session_nonce,
        "prev_chain_hash": prev_chain_hash,
        "bundle_hash": b["bundle_hash"],
        "baseline_hash": b["baseline_hash"],
        "packet_hash": pkt["packet_hash"],
        "post_packet_hash": p["post_packet_hash"],
        "review_package_hash": pkg["review_package_hash"],
        "session_manifest_hash": pkg["session_manifest_hash"],
        "mapping_commitment": mp["mapping_commitment"],
        "review_input_mode": REVIEW_INPUT_MODE_BLINDED,
        "arm_a_scores": arm_a_scores,
        "arm_b_scores": arm_b_scores,
        # Mapped after blinded input validation for comparison/replay only.
        "baseline_scores": baseline_scores,
        "post_scores": post_scores,
        "custody_attestation": custody,
        "alpha_claim": False,
        "general_effectiveness_claim": False,
        "causal_superiority_claim": False,
    }
    if external_receipt_bound is not None:
        body["external_submission_receipt"] = external_receipt_bound
        body["external_rubric_bytes_sha256"] = plain["external_rubric_bytes_sha256"]
        body["mapping_reveal_gate"] = "RECEIPT_BOUND_RUBRIC_SEALED"
    digest = domain_hash(DOMAIN_RUBRIC, body)
    out = dict(body)
    out["rubric_hash"] = digest
    return _freeze(out)


def verify_rubric_seal(
    rubric: Mapping[str, Any],
    *,
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    packet: Mapping[str, Any],
    review_package: Mapping[str, Any],
    review_mapping: Mapping[str, Any],
) -> str:
    plain = _plain(rubric)
    claimed = _require_sha256(plain.get("rubric_hash"), "E0B_RUBRIC_HASH_INVALID")
    body = _without_keys(plain, "rubric_hash")
    sealed = seal_rubric_record(
        body,
        baseline=baseline,
        post=post,
        packet=packet,
        review_package=review_package,
        review_mapping=review_mapping,
    )
    if sealed["rubric_hash"] != claimed:
        raise GvE0bDv1Error("E0B_RUBRIC_SEAL_MISMATCH")
    return claimed


def load_rubric_scores(
    path: Path,
    *,
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    packet: Mapping[str, Any],
    review_package: Mapping[str, Any],
    review_mapping: Mapping[str, Any],
) -> Mapping[str, Any]:
    raw = _load_json_object(path)
    if "rubric_hash" not in raw:
        raise GvE0bDv1Error("E0B_RUBRIC_UNSEALED")
    verify_rubric_seal(
        raw,
        baseline=baseline,
        post=post,
        packet=packet,
        review_package=review_package,
        review_mapping=review_mapping,
    )
    return _freeze(_plain(raw))


def score_totals(arm_scores: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    items = {item: int(arm_scores[item]["score"]) for item in RUBRIC_ITEMS}
    return {
        "items": items,
        "total": sum(items.values()),
        "max_total": 2 * len(RUBRIC_ITEMS),
    }


def _verified_delta_value(entry: Any, code: str) -> int:
    delta = _require_mapping(entry, code)
    raw = delta.get("value_string")
    if not isinstance(raw, str):
        raise GvE0bDv1Error(code)
    try:
        value = int(raw)
    except ValueError as exc:
        raise GvE0bDv1Error(code) from exc
    magnitude = delta.get("magnitude")
    if type(magnitude) is not int or magnitude != abs(value):
        raise GvE0bDv1Error(code)
    if delta.get("is_negative") is not (value < 0):
        raise GvE0bDv1Error(code)
    return value


def decision_value_disposition_from_comparison(
    comparison: Mapping[str, Any],
) -> str:
    """Classify one observed G08 result without making a general causal claim.

    IMPROVED requires a positive total blinded-rubric delta, improvement in at
    least one GodView-targeted dimension, and no regression in either core safety
    dimension. Every other valid observed comparison is NOT_IMPROVED.
    """

    plain = _plain(comparison)
    delta = _require_mapping(plain.get("delta"), "E0B_VALUE_DELTA_REQUIRED")
    item_deltas = _require_mapping(
        delta.get("item_score_differences"), "E0B_VALUE_ITEM_DELTAS_REQUIRED"
    )
    if set(item_deltas) != set(RUBRIC_ITEMS):
        raise GvE0bDv1Error("E0B_VALUE_ITEM_DELTAS_INVALID")
    total_delta = _verified_delta_value(
        delta.get("total_score_difference"), "E0B_VALUE_TOTAL_DELTA_INVALID"
    )
    values = {
        item: _verified_delta_value(
            item_deltas[item], f"E0B_VALUE_ITEM_DELTA_INVALID:{item}"
        )
        for item in RUBRIC_ITEMS
    }
    if total_delta != sum(values.values()):
        raise GvE0bDv1Error("E0B_VALUE_TOTAL_DELTA_MISMATCH")
    targeted_improved = any(values[item] > 0 for item in TARGETED_VALUE_DIMENSIONS)
    safety_not_worse = all(values[item] >= 0 for item in CORE_SAFETY_DIMENSIONS)
    if total_delta > 0 and targeted_improved and safety_not_worse:
        return DECISION_VALUE_IMPROVED
    return DECISION_VALUE_NOT_IMPROVED


def is_attribution_structure_valid(
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    rubric: Mapping[str, Any],
) -> bool:
    """Two-human structure: same real operator for both arms; different real reviewer."""

    return (
        baseline.get("authorship_kind") == AUTH_REAL_OPERATOR
        and post.get("authorship_kind") == AUTH_REAL_OPERATOR
        and baseline.get("operator_id") == post.get("operator_id")
        and rubric.get("authorship_kind") == AUTH_REAL_REVIEWER
        and rubric.get("reviewer_id") != baseline.get("operator_id")
    )


def is_observed_comparison_eligible(
    baseline: Mapping[str, Any],
    post: Mapping[str, Any],
    rubric: Mapping[str, Any],
) -> bool:
    """True only when methodological + two-human boundaries are sealed.

    Requires:
    - real operator (both arms) + different real reviewer;
    - blinded ARM input mode on the sealed rubric;
    - baseline operator custody assertion (not seen packet/outcome before baseline);
    - reviewer custody assertion (received only blinded review package);
    - external GitHub receipt v2 with provider-authenticated author login
      equal to reviewer_id and unequal to operator_id.

    These remain human attestations plus provider-login binding, not personhood proof.
    """

    if not is_attribution_structure_valid(baseline, post, rubric):
        return False
    if rubric.get("review_input_mode") != REVIEW_INPUT_MODE_BLINDED:
        return False
    if baseline.get("operator_had_not_seen_packet_or_expected_outcome") is not True:
        return False
    custody = rubric.get("custody_attestation")
    if not isinstance(custody, Mapping):
        return False
    if custody.get("reviewer_received_only_blinded_review_package") is not True:
        return False
    if custody.get("reviewer_export_boundary_attested") is not True:
        return False
    if not isinstance(custody.get("review_package_hash_attested"), str):
        return False
    if not isinstance(custody.get("session_manifest_hash_attested"), str):
        return False
    # Provider-authenticated reviewer independence (not free-text git name).
    ext = rubric.get("external_submission_receipt")
    if not isinstance(ext, Mapping):
        return False
    if ext.get("schema_version") != GITHUB_RECEIPT_SCHEMA_V2:
        return False
    author_login = ext.get("github_author_login")
    committer_login = ext.get("github_committer_login")
    submitter = ext.get("authenticated_submitter_id")
    reviewer_id = rubric.get("reviewer_id")
    operator_id = baseline.get("operator_id")
    if not isinstance(author_login, str) or not author_login.strip():
        return False
    if not isinstance(committer_login, str) or not committer_login.strip():
        return False
    if author_login != submitter or author_login != reviewer_id:
        return False
    if author_login == operator_id:
        return False
    return True


def stage_capture_baseline(
    authoring: Mapping[str, Any],
    *,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    session_path: Path = DEFAULT_SESSION_PATH,
    bundle: Mapping[str, Any] | None = None,
    clock: CaptureClock | None = None,
) -> Mapping[str, Any]:
    clk = clock or WallClock()
    _reject_caller_timing_fields(authoring)
    clean_authoring = _sanitize_authoring_submission(
        authoring,
        expected_template_id=BASELINE_TEMPLATE_ID,
    )
    _require_active_checkpoint_for_authoritative_stage(
        session_path, "SUBMIT_BASELINE"
    )
    session = load_capture_session(session_path)
    open_payload = _find_open_payload(session, STAGE_BASELINE_OPEN)
    ended = clk.now()
    timing = _stamp_decision_timing(open_payload=open_payload, ended_at=ended)
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    if session["bundle_hash"] != bndl["bundle_hash"]:
        raise GvE0bDv1Error("E0B_SESSION_BUNDLE_MISMATCH")
    record = {
        **clean_authoring,
        **timing,
        "session_nonce": session["session_nonce"],
        "prev_chain_hash": _session_tip_from_chain(session["chain"]),
        "bundle_hash": bndl["bundle_hash"],
    }
    sealed = seal_baseline_record(record)
    if sealed["operator_id"] != session["session_manifest"]["operator_principal_id"]:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_OPERATOR_MISMATCH")
    _append_event(
        session_path=session_path,
        stage=STAGE_BASELINE_CLOSE,
        record_hash=sealed["baseline_hash"],
        payload={"baseline_hash": sealed["baseline_hash"]},
        case_id=session["case_id"],
        session_nonce=session["session_nonce"],
        bundle_hash=session["bundle_hash"],
        created_at=session["created_at"],
    )
    _persist_sealed_json(baseline_path, sealed)
    return sealed


def stage_generate_packet(
    *,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    packet_path: Path = DEFAULT_PACKET_PATH,
    session_path: Path = DEFAULT_SESSION_PATH,
    bundle: Mapping[str, Any] | None = None,
    clock: CaptureClock | None = None,
) -> Mapping[str, Any]:
    clk = clock or WallClock()
    _require_active_checkpoint_for_authoritative_stage(
        session_path, "GENERATE_PACKET"
    )
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    session = load_capture_session(session_path)
    baseline = load_baseline_seal(
        baseline_path, expected_bundle_hash=bndl["bundle_hash"]
    )
    if baseline["session_nonce"] != session["session_nonce"]:
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
    stages = [e["stage"] for e in session["chain"]]
    if stages != [
        STAGE_SESSION_OPEN,
        STAGE_BASELINE_OPEN,
        STAGE_BASELINE_CLOSE,
    ]:
        raise GvE0bDv1Error("E0B_CHAIN_STAGE_ORDER")
    ts = clk.now()
    if not (baseline["sealed_at"] < ts):
        raise GvE0bDv1Error("E0B_PACKET_MUST_FOLLOW_BASELINE")
    packet = build_godview_packet(
        bundle=bndl,
        generated_at=ts,
        session_nonce=session["session_nonce"],
        prev_chain_hash=_session_tip_from_chain(session["chain"]),
    )
    _append_event(
        session_path=session_path,
        stage=STAGE_PACKET,
        record_hash=packet["packet_hash"],
        payload={"packet_hash": packet["packet_hash"]},
        case_id=session["case_id"],
        session_nonce=session["session_nonce"],
        bundle_hash=session["bundle_hash"],
        created_at=session["created_at"],
    )
    _persist_sealed_json(packet_path, packet)
    return packet


def stage_capture_post(
    authoring: Mapping[str, Any],
    *,
    post_path: Path = DEFAULT_POST_PATH,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    packet_path: Path = DEFAULT_PACKET_PATH,
    session_path: Path = DEFAULT_SESSION_PATH,
    bundle: Mapping[str, Any] | None = None,
    clock: CaptureClock | None = None,
) -> Mapping[str, Any]:
    clk = clock or WallClock()
    _reject_caller_timing_fields(authoring)
    clean_authoring = _sanitize_authoring_submission(
        authoring,
        expected_template_id=POST_TEMPLATE_ID,
    )
    _require_active_checkpoint_for_authoritative_stage(session_path, "SUBMIT_POST")
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    session = load_capture_session(session_path)
    open_payload = _find_open_payload(session, STAGE_POST_OPEN)
    ended = clk.now()
    timing = _stamp_decision_timing(open_payload=open_payload, ended_at=ended)
    baseline = load_baseline_seal(
        baseline_path, expected_bundle_hash=bndl["bundle_hash"]
    )
    packet = load_packet_seal(packet_path)
    record = {
        **clean_authoring,
        **timing,
        "session_nonce": session["session_nonce"],
        "prev_chain_hash": _session_tip_from_chain(session["chain"]),
        "bundle_hash": bndl["bundle_hash"],
    }
    sealed = seal_post_packet_record(record, packet=packet, baseline=baseline)
    if sealed["operator_id"] != session["session_manifest"]["operator_principal_id"]:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_OPERATOR_MISMATCH")
    _append_event(
        session_path=session_path,
        stage=STAGE_POST_CLOSE,
        record_hash=sealed["post_packet_hash"],
        payload={"post_packet_hash": sealed["post_packet_hash"]},
        case_id=session["case_id"],
        session_nonce=session["session_nonce"],
        bundle_hash=session["bundle_hash"],
        created_at=session["created_at"],
    )
    _persist_sealed_json(post_path, sealed)
    return sealed


def blank_rubric_authoring_template() -> dict[str, Any]:
    """Schema-shaped blank blinded rubric form (ARM_A/ARM_B only).

    Decision fields stay null/empty so an unedited template fails seal immediately.
    """

    blank_arm = {
        item: {"score": None, "reason": ""}
        for item in RUBRIC_ITEMS
    }
    return {
        "artifact_role": AUTHORING_ONLY,
        "template_id": RUBRIC_TEMPLATE_ID,
        "case_id": CASE_ID,
        "authorship_kind": AUTH_REAL_REVIEWER,
        "reviewer_id": None,
        "arm_a_scores": blank_arm,
        "arm_b_scores": {
            item: {"score": None, "reason": ""}
            for item in RUBRIC_ITEMS
        },
        "alpha_claim": False,
        "general_effectiveness_claim": False,
        "causal_superiority_claim": False,
        "fresh_operator_attested": None,
        "blinded_review_conditions_attested": None,
        "reviewer_received_only_blinded_review_package": None,
        "review_package_hash_attested": None,
        "session_manifest_hash_attested": None,
        "reviewer_export_boundary_attested": None,
        "notes": (
            "Score ARM_A and ARM_B only. Do not write baseline/post labels. "
            "Fill score 0|1|2 and non-empty reason per item. "
            "Set reviewer_id to a real reviewer identity. "
            "Set reviewer_received_only_blinded_review_package to true only after "
            "you confirm you received only the blinded export package."
        ),
    }


def blank_baseline_authoring_template() -> dict[str, Any]:
    """Blank baseline form: no preselected action and no placeholder identity."""

    return {
        "artifact_role": AUTHORING_ONLY,
        "template_id": BASELINE_TEMPLATE_ID,
        "case_id": CASE_ID,
        "arm": "HUMAN_BASELINE",
        "authorship_kind": AUTH_REAL_OPERATOR,
        "operator_id": None,
        "equal_budget_attestation": True,
        "outside_research_attestation": False,
        "post_cutoff_information_attestation": False,
        "operator_had_not_seen_packet_or_expected_outcome": None,
        "sealed_before_packet": True,
        "action": None,
        "rationale": None,
        "missing_evidence": [],
        "falsifiers": [],
        "contradictions_recognized": [],
        "alpha_claim": False,
        "notes": (
            "Fill operator_id, action (one of ADVANCE_TO_FULL_RESEARCH | "
            "HOLD_FOR_EVIDENCE | REJECT_THESIS), and rationale. "
            "Set operator_had_not_seen_packet_or_expected_outcome to true only if "
            "you had not seen the GodView packet or expected outcome before baseline."
        ),
    }


def blank_post_authoring_template() -> dict[str, Any]:
    """Blank post form: no preselected action/portfolio and no placeholder identity."""

    return {
        "artifact_role": AUTHORING_ONLY,
        "template_id": POST_TEMPLATE_ID,
        "case_id": CASE_ID,
        "arm": "HUMAN_POST_PACKET",
        "authorship_kind": AUTH_REAL_OPERATOR,
        "operator_id": None,
        "equal_budget_attestation": True,
        "outside_research_attestation": False,
        "post_cutoff_information_attestation": False,
        "action": None,
        "portfolio_action": None,
        "rationale": None,
        "missing_evidence": [],
        "falsifiers": [],
        "contradictions_recognized": [],
        "alpha_claim": False,
        "notes": (
            "Fill operator_id (must match baseline), action, rationale. "
            "portfolio_action must be set to NO_POSITION at submission."
        ),
    }


def write_authoring_templates(authoring_dir: Path) -> dict[str, Path]:
    """Create-only blank baseline/post/rubric authoring JSON (narrow G08 handoff)."""

    authoring_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "baseline": authoring_dir / "baseline_authoring.json",
        "post": authoring_dir / "post_authoring.json",
        "rubric": authoring_dir / "rubric_authoring.json",
    }
    for path in paths.values():
        if path.exists():
            raise GvE0bDv1Error(f"E0B_AUTHORING_TEMPLATE_EXISTS:{path.name}")
    _persist_sealed_json(paths["baseline"], blank_baseline_authoring_template())
    _persist_sealed_json(paths["post"], blank_post_authoring_template())
    _persist_sealed_json(paths["rubric"], blank_rubric_authoring_template())
    return paths


def _assert_reviewer_export_ready(export_dir: Path) -> None:
    if export_dir.exists():
        if not export_dir.is_dir():
            raise GvE0bDv1Error("E0B_REVIEWER_EXPORT_NOT_DIR")
        entries = list(export_dir.iterdir())
        if entries:
            raise GvE0bDv1Error("E0B_REVIEWER_EXPORT_NOT_EMPTY")
    else:
        export_dir.mkdir(parents=True, exist_ok=True)


def _assert_reviewer_export_exact(export_dir: Path) -> None:
    if not export_dir.is_dir():
        raise GvE0bDv1Error("E0B_REVIEWER_EXPORT_NOT_DIR")
    names = {path.name for path in export_dir.iterdir()}
    if names != set(REVIEWER_EXPORT_EXACT_NAMES):
        raise GvE0bDv1Error("E0B_REVIEWER_EXPORT_CONTENTS_INVALID")
    for path in export_dir.iterdir():
        if path.is_dir() or path.is_symlink():
            raise GvE0bDv1Error("E0B_REVIEWER_EXPORT_CONTENTS_INVALID")


def stage_build_review_package(
    *,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    post_path: Path = DEFAULT_POST_PATH,
    packet_path: Path = DEFAULT_PACKET_PATH,
    session_path: Path = DEFAULT_SESSION_PATH,
    package_path: Path = DEFAULT_REVIEW_PACKAGE_PATH,
    mapping_path: Path = DEFAULT_REVIEW_MAPPING_PATH,
    rubric_authoring_path: Path | None = None,
    bundle: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Seal blinded REVIEW_PACKAGE under separated export custody.

    Production always draws 16-byte entropy via secrets.token_bytes(16).
    Deterministic RNG injection is test-only via mock of secrets.token_bytes
    or the pure seal_review_package(..., rng_bytes=...) helper.

    Reviewer export directory receives only:
      - review_package.json
      - blank rubric_authoring.json (ARM_A/ARM_B)

    Private mapping is written under operator custody (not in export dir).
    Canonical ledger stores mapping_commitment only.
    """

    _require_active_checkpoint_for_authoritative_stage(
        session_path, "EXPORT_REVIEW_PACKAGE"
    )
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    session = load_capture_session(session_path)
    stages = [e["stage"] for e in session["chain"]]
    if stages != list(CANONICAL_STAGE_ORDER[:6]):
        raise GvE0bDv1Error("E0B_CHAIN_STAGE_ORDER")
    baseline = load_baseline_seal(baseline_path, expected_bundle_hash=bndl["bundle_hash"])
    packet = load_packet_seal(packet_path)
    post = load_post_packet_seal(post_path, packet=packet, baseline=baseline)
    package, mapping = seal_review_package(
        baseline=baseline,
        post=post,
        packet=packet,
        bundle=bndl,
        session_nonce=session["session_nonce"],
        prev_chain_hash=_session_tip_from_chain(session["chain"]),
        session_manifest_hash=session["session_manifest_hash"],
    )
    verify_review_package_bound_to_records(
        package=package,
        mapping=mapping,
        baseline=baseline,
        post=post,
        packet=packet,
        bundle=bndl,
    )
    export = _plain(package)
    package_path = Path(package_path)
    mapping_path = Path(mapping_path)
    # Prefer session-nonce-specific export dir; require clean exact contents.
    export_dir = package_path.parent.resolve()
    if mapping_path.resolve().is_relative_to(export_dir):
        raise GvE0bDv1Error("E0B_MAPPING_MUST_LEAVE_REVIEWER_EXPORT")
    _assert_reviewer_export_ready(export_dir)
    blank_path = (
        Path(rubric_authoring_path)
        if rubric_authoring_path is not None
        else export_dir / "rubric_authoring.json"
    )
    if blank_path.resolve().parent != export_dir:
        raise GvE0bDv1Error("E0B_RUBRIC_TEMPLATE_MUST_LIVE_IN_EXPORT")
    if package_path.name != "review_package.json":
        raise GvE0bDv1Error("E0B_REVIEW_PACKAGE_NAME_INVALID")
    if blank_path.name != "rubric_authoring.json":
        raise GvE0bDv1Error("E0B_RUBRIC_TEMPLATE_NAME_INVALID")
    _persist_sealed_json(package_path, export)
    _persist_sealed_json(blank_path, blank_rubric_authoring_template())
    _assert_reviewer_export_exact(export_dir)
    # Private mapping under operator custody only (not exported to reviewer).
    _persist_sealed_json(mapping_path, mapping)
    _append_event(
        session_path=session_path,
        stage=STAGE_REVIEW_PACKAGE,
        record_hash=package["review_package_hash"],
        payload={
            "review_package_hash": package["review_package_hash"],
            "mapping_commitment": mapping["mapping_commitment"],
        },
        case_id=session["case_id"],
        session_nonce=session["session_nonce"],
        bundle_hash=session["bundle_hash"],
        created_at=session["created_at"],
    )
    return _freeze(export)


def stage_capture_rubric(
    authoring: Mapping[str, Any],
    *,
    rubric_path: Path = DEFAULT_RUBRIC_PATH,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    post_path: Path = DEFAULT_POST_PATH,
    packet_path: Path = DEFAULT_PACKET_PATH,
    session_path: Path = DEFAULT_SESSION_PATH,
    package_path: Path = DEFAULT_REVIEW_PACKAGE_PATH,
    mapping_path: Path = DEFAULT_REVIEW_MAPPING_PATH,
    bundle: Mapping[str, Any] | None = None,
    clock: CaptureClock | None = None,
    external_receipt: Mapping[str, Any] | None = None,
    external_rubric_path: Path | None = None,
) -> Mapping[str, Any]:
    """Rubric close: no 60-minute timer; scores against blinded package.

    Real-reviewer path requires an externally submitted GitHub receipt and the
    exact imported rubric bytes. Mapping reveal occurs only after the
    receipt-bound rubric is durably sealed.
    """

    clk = clock or WallClock()
    working_authoring = _plain(authoring)
    # Real-reviewer submissions must come from external receipt-bound bytes.
    auth_kind = working_authoring.get("authorship_kind")
    if auth_kind == AUTH_REAL_REVIEWER:
        if external_receipt is None or external_rubric_path is None:
            raise GvE0bDv1Error("E0B_EXTERNAL_RECEIPT_MISSING")
        session_preview = load_capture_session(session_path)
        package_preview = _load_json_object(package_path)
        verify_review_package(package_preview)
        imported = import_external_rubric_submission(
            receipt=external_receipt,
            rubric_path=Path(external_rubric_path),
            expected_submitter_id=str(
                session_preview["session_manifest"]["reviewer_principal_id"]
            ),
            expected_candidate_commit=str(
                session_preview["session_manifest"]["source_commit"]
            ),
            expected_candidate_tree=str(
                session_preview["session_manifest"]["source_tree"]
            ),
            expected_review_package_hash=str(package_preview["review_package_hash"]),
        )
        # Reject operator-authored replacement: only imported bytes may score.
        working_authoring = dict(imported["authoring"])
        working_authoring["external_submission_receipt"] = imported["receipt"]
        working_authoring["external_rubric_bytes_sha256"] = imported[
            "rubric_bytes_sha256"
        ]
        # Preserve custody attestations if present on the external payload;
        # otherwise require them via seal_rubric_record fail-closed checks.
    _reject_caller_timing_fields(working_authoring)
    clean_authoring = _sanitize_authoring_submission(
        working_authoring,
        expected_template_id=RUBRIC_TEMPLATE_ID,
    )
    # Re-attach receipt fields stripped by authoring sanitizer if needed.
    if auth_kind == AUTH_REAL_REVIEWER:
        clean_authoring = dict(clean_authoring)
        clean_authoring["external_submission_receipt"] = working_authoring[
            "external_submission_receipt"
        ]
        clean_authoring["external_rubric_bytes_sha256"] = working_authoring[
            "external_rubric_bytes_sha256"
        ]
        for key in (
            "fresh_operator_attested",
            "blinded_review_conditions_attested",
            "reviewer_received_only_blinded_review_package",
            "review_package_hash_attested",
            "session_manifest_hash_attested",
            "reviewer_export_boundary_attested",
        ):
            if key in working_authoring and key not in clean_authoring:
                clean_authoring[key] = working_authoring[key]
    _require_active_checkpoint_for_authoritative_stage(
        session_path, "SUBMIT_RUBRIC"
    )
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    session = load_capture_session(session_path)
    stages = [e["stage"] for e in session["chain"]]
    if stages != list(CANONICAL_STAGE_ORDER[:7]):
        raise GvE0bDv1Error("E0B_CHAIN_STAGE_ORDER")
    baseline = load_baseline_seal(baseline_path, expected_bundle_hash=bndl["bundle_hash"])
    packet = load_packet_seal(packet_path)
    post = load_post_packet_seal(post_path, packet=packet, baseline=baseline)
    package = _load_json_object(package_path)
    verify_review_package(package)
    mapping = _load_json_object(mapping_path)
    verify_review_mapping(mapping, review_package_hash=package["review_package_hash"])
    scored_at = clk.now()
    record = {
        **clean_authoring,
        "scored_at": scored_at,
        "session_nonce": session["session_nonce"],
        "prev_chain_hash": _session_tip_from_chain(session["chain"]),
    }
    # Private mapping must match ledger commitment before scores are sealed.
    rp_events = [
        e for e in (session.get("events") or []) if e.get("stage") == STAGE_REVIEW_PACKAGE
    ]
    if not rp_events:
        raise GvE0bDv1Error("E0B_REVIEW_PACKAGE_EVENT_MISSING")
    rp_payload = _require_mapping(
        rp_events[-1].get("payload"), "E0B_REVIEW_PACKAGE_PAYLOAD_REQUIRED"
    )
    commitment = rp_payload.get("mapping_commitment")
    if commitment != mapping.get("mapping_commitment"):
        raise GvE0bDv1Error("E0B_MAPPING_COMMITMENT_MISMATCH")
    verify_mapping_randomization(mapping)
    sealed = seal_rubric_record(
        record,
        baseline=baseline,
        post=post,
        packet=packet,
        review_package=package,
        review_mapping=mapping,
    )
    if sealed["reviewer_id"] != session["session_manifest"]["reviewer_principal_id"]:
        raise GvE0bDv1Error("E0B_SESSION_MANIFEST_REVIEWER_MISMATCH")
    # Durable order: compute seal → persist rubric → RUBRIC_CLOSE → reload/verify
    # complete chain → only then materialize revealed mapping + RNG preimage.
    _persist_sealed_json(rubric_path, sealed)
    _append_event(
        session_path=session_path,
        stage=STAGE_RUBRIC_CLOSE,
        record_hash=sealed["rubric_hash"],
        payload={"rubric_hash": sealed["rubric_hash"]},
        case_id=session["case_id"],
        session_nonce=session["session_nonce"],
        bundle_hash=session["bundle_hash"],
        created_at=session["created_at"],
    )
    reloaded_session = load_capture_session(session_path)
    stages_after = [e["stage"] for e in reloaded_session["chain"]]
    if stages_after != list(CANONICAL_STAGE_ORDER):
        raise GvE0bDv1Error("E0B_CHAIN_STAGE_ORDER")
    reloaded_rubric = load_rubric_scores(
        rubric_path,
        baseline=baseline,
        post=post,
        packet=packet,
        review_package=package,
        review_mapping=mapping,
    )
    if reloaded_rubric["rubric_hash"] != sealed["rubric_hash"]:
        raise GvE0bDv1Error("E0B_RUBRIC_SEAL_MISMATCH")
    seals_for_bind = {
        "baseline": _plain(baseline),
        "packet": _plain(packet),
        "post": _plain(post),
        "review_package": _plain(package),
        "review_mapping": _plain(mapping),
        "rubric": _plain(reloaded_rubric),
        "session_manifest": reloaded_session["session_manifest"],
        "session": reloaded_session,
    }
    verify_session_bound_to_records(reloaded_session, seals_for_bind)
    verify_review_package_bound_to_records(
        package=package,
        mapping=mapping,
        baseline=baseline,
        post=post,
        packet=packet,
        bundle=bndl,
    )
    reveal_path = mapping_path.with_name(
        mapping_path.name.replace(".private.json", ".revealed.json")
        if mapping_path.name.endswith(".private.json")
        else mapping_path.name + ".revealed.json"
    )
    assert_mapping_reveal_allowed(rubric=reloaded_rubric, revealed_exists=False)
    reveal_payload = {
        "mapping_commitment": mapping["mapping_commitment"],
        "review_package_hash": mapping["review_package_hash"],
        "arm_a_source": mapping["arm_a_source"],
        "arm_b_source": mapping["arm_b_source"],
        "baseline_hash": mapping["baseline_hash"],
        "post_packet_hash": mapping["post_packet_hash"],
        "rng_commitment": mapping["rng_commitment"],
        "rng_bytes_hex": mapping["rng_bytes_hex"],
        "revealed_at": scored_at,
        "revealed_after": "RUBRIC_CLOSE",
        "blinding_custody_model": BLINDING_CUSTODY_MODEL,
        "rubric_hash": sealed["rubric_hash"],
        "note": (
            "Arm-label blinding under separated export custody. "
            "RNG preimage revealed only after durable RUBRIC_CLOSE and "
            "complete chain verification."
        ),
    }
    if reloaded_rubric.get("authorship_kind") == AUTH_REAL_REVIEWER:
        receipt = reloaded_rubric.get("external_submission_receipt")
        if not isinstance(receipt, Mapping):
            raise GvE0bDv1Error("E0B_MAPPING_REVEAL_BEFORE_RECEIPT_BOUND_RUBRIC")
        reveal_payload["external_receipt_hash"] = receipt.get("receipt_hash")
        reveal_payload["revealed_after"] = "RECEIPT_BOUND_RUBRIC_SEAL"
        reveal_payload["note"] = (
            "Arm-label blinding under separated export custody. "
            "Mapping reveal only after receipt-bound rubric seal. "
            "GitHub account separation is operational only; not natural-person proof."
        )
    _persist_sealed_json(reveal_path, reveal_payload)
    return sealed


def _collect_sealed_records(
    *,
    baseline_path: Path,
    post_path: Path,
    rubric_path: Path,
    packet_path: Path,
    session_path: Path,
    package_path: Path,
    mapping_path: Path,
    bundle: Mapping[str, Any] | None,
) -> dict[str, Any]:
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    baseline = load_baseline_seal(baseline_path, expected_bundle_hash=bndl["bundle_hash"])
    packet = load_packet_seal(packet_path)
    post = load_post_packet_seal(post_path, packet=packet, baseline=baseline)
    package = _load_json_object(package_path)
    verify_review_package(package)
    mapping = _load_json_object(mapping_path)
    verify_review_mapping(mapping, review_package_hash=package["review_package_hash"])
    verify_review_package_bound_to_records(
        package=package,
        mapping=mapping,
        baseline=baseline,
        post=post,
        packet=packet,
        bundle=bndl,
    )
    rubric = load_rubric_scores(
        rubric_path,
        baseline=baseline,
        post=post,
        packet=packet,
        review_package=package,
        review_mapping=mapping,
    )
    session = load_capture_session(session_path)
    manifest = load_session_manifest(_session_manifest_path(session_path))
    return {
        "bundle": bndl,
        "baseline": _plain(baseline),
        "packet": _plain(packet),
        "post": _plain(post),
        "review_package": _plain(package),
        "review_mapping": _plain(mapping),
        "rubric": _plain(rubric),
        "session_manifest": manifest,
        "session": session,
    }


def _build_comparison_from_verified_records(
    *,
    bundle: Mapping[str, Any],
    packet: Mapping[str, Any],
    seals: Mapping[str, Any],
) -> Mapping[str, Any]:
    bndl = _plain(bundle)
    pkt = _plain(packet)
    verify_session_bound_to_records(seals["session"], seals)
    baseline = seals["baseline"]
    post = seals["post"]
    rubric = seals["rubric"]
    if baseline.get("session_nonce") != seals["session"]["session_nonce"]:
        raise GvE0bDv1Error("E0B_SESSION_NONCE_MISMATCH")
    if not (baseline["sealed_at"] < pkt["generated_at"]):
        raise GvE0bDv1Error("E0B_INVALID_BASELINE_SEAL")
    baseline_totals = score_totals(rubric["baseline_scores"])
    post_totals = score_totals(rubric["post_scores"])
    item_deltas: dict[str, dict[str, Any]] = {}
    for item in RUBRIC_ITEMS:
        raw = int(post_totals["items"][item]) - int(baseline_totals["items"][item])
        item_deltas[item] = {
            "magnitude": abs(raw),
            "is_negative": raw < 0,
            "value_string": str(raw),
        }
    total_raw = int(post_totals["total"]) - int(baseline_totals["total"])
    total_delta = {
        "magnitude": abs(total_raw),
        "is_negative": total_raw < 0,
        "value_string": str(total_raw),
    }
    attribution_ok = is_attribution_structure_valid(baseline, post, rubric)
    comparison = _plain(
        {
            "case_id": CASE_ID,
            "acceptance_case": "G08",
            "run_class": RUN_CLASS_SYNTHETIC,
            "session_nonce": baseline["session_nonce"],
            "stage_claim": {
                "shipped_product_score": 39,
                "score_frozen": True,
                "functional_stage": "CERTIFIED_SINGLE_DECISION_OPERABLE",
                "target_stage": "ONE_CASE_DECISION_DELTA_OBSERVED",
                "observed_comparison_count": 0,
                "comparison_observed_eligible": False,
                "decision_value_disposition": None,
                "attribution_structure_valid": attribution_ok,
                "alpha_claim": False,
            },
            "bundle_hash": bndl["bundle_hash"],
            "baseline_hash": baseline["baseline_hash"],
            "packet_hash": pkt["packet_hash"],
            "post_packet_hash": post["post_packet_hash"],
            "review_package_hash": seals["review_package"]["review_package_hash"],
            "rubric_hash": rubric["rubric_hash"],
            "session_hash": seals["session"]["session_hash"],
            "session_manifest_hash": seals["session_manifest"][
                "session_manifest_hash"
            ],
            "source_commit": seals["session_manifest"]["source_commit"],
            "source_tree": seals["session_manifest"]["source_tree"],
            "protocol_freeze_manifest_sha256": seals["session_manifest"][
                "protocol_freeze_manifest_sha256"
            ],
            "baseline": {
                "authorship_kind": baseline["authorship_kind"],
                "operator_id": baseline["operator_id"],
                "sealed_at": baseline["sealed_at"],
                "action": baseline["action"],
                "rationale": baseline["rationale"],
                "allowed_budget_minutes": baseline["allowed_budget_minutes"],
                "elapsed_seconds": baseline["elapsed_seconds"],
                "operator_had_not_seen_packet_or_expected_outcome": bool(
                    baseline.get("operator_had_not_seen_packet_or_expected_outcome")
                ),
            },
            "godview_packet": {
                "run_state": pkt["run_state"],
                "block_reason": pkt["block_reason"],
                "generated_at": pkt["generated_at"],
                "rationale": pkt["rationale"],
            },
            "post_packet": {
                "authorship_kind": post["authorship_kind"],
                "operator_id": post["operator_id"],
                "sealed_at": post["sealed_at"],
                "action": post["action"],
                "rationale": post["rationale"],
                "allowed_budget_minutes": post["allowed_budget_minutes"],
                "elapsed_seconds": post["elapsed_seconds"],
            },
            "rubric": {
                "authorship_kind": rubric["authorship_kind"],
                "reviewer_id": rubric["reviewer_id"],
                "scored_at": rubric["scored_at"],
                "review_input_mode": rubric.get("review_input_mode"),
                "custody_attestation": _plain(rubric.get("custody_attestation") or {}),
                "external_submission_receipt": (
                    _plain(rubric.get("external_submission_receipt"))
                    if isinstance(rubric.get("external_submission_receipt"), Mapping)
                    else None
                ),
                "baseline": baseline_totals,
                "post_packet": post_totals,
            },
            "delta": {
                "item_score_differences": item_deltas,
                "total_score_difference": total_delta,
                "action_change": baseline["action"] != post["action"],
            },
            "claim_boundary": (
                "Observed within-case difference only. No causal superiority, "
                "general decision-quality improvement, research-efficiency, alpha, "
                "or score uplift claim."
            ),
        }
    )
    comparison["comparison_hash"] = domain_hash(DOMAIN_COMPARISON, comparison)
    return _freeze(comparison)


def build_comparison(
    *,
    baseline_path: Path,
    post_path: Path,
    rubric_path: Path,
    bundle: Mapping[str, Any] | None = None,
    packet: Mapping[str, Any] | None = None,
    packet_path: Path | None = None,
    session_path: Path | None = None,
    package_path: Path | None = None,
    mapping_path: Path | None = None,
) -> Mapping[str, Any]:
    bndl = _plain(bundle) if bundle is not None else _plain(sealed_adversarial_bundle())
    verify_bundle_seal(bndl)
    if packet is not None:
        pkt = _plain(packet)
        verify_packet_seal(pkt)
    elif packet_path is not None:
        pkt = _plain(load_packet_seal(packet_path))
    else:
        raise GvE0bDv1Error("E0B_PACKET_REQUIRED")
    if pkt["bundle_hash"] != bndl["bundle_hash"]:
        raise GvE0bDv1Error("E0B_PACKET_BUNDLE_MISMATCH")
    if session_path is None or package_path is None or mapping_path is None:
        raise GvE0bDv1Error("E0B_SESSION_PACKAGE_REQUIRED")
    seals = _collect_sealed_records(
        baseline_path=baseline_path,
        post_path=post_path,
        rubric_path=rubric_path,
        packet_path=packet_path or DEFAULT_PACKET_PATH,
        session_path=session_path,
        package_path=package_path,
        mapping_path=mapping_path,
        bundle=bndl,
    )
    if seals["packet"]["packet_hash"] != pkt["packet_hash"]:
        raise GvE0bDv1Error("E0B_PACKET_SOURCE_MISMATCH")
    return _build_comparison_from_verified_records(
        bundle=bndl,
        packet=pkt,
        seals=seals,
    )


def build_result_document(
    comparison: Mapping[str, Any],
    *,
    sealed_records: Mapping[str, Any],
) -> Mapping[str, Any]:
    plain = _plain(comparison)
    claimed = _require_sha256(plain.get("comparison_hash"), "E0B_COMPARISON_HASH_INVALID")
    body = _without_keys(plain, "comparison_hash")
    recomputed = domain_hash(DOMAIN_COMPARISON, body)
    if recomputed != claimed:
        raise GvE0bDv1Error("E0B_COMPARISON_SEAL_MISMATCH")
    seals = _require_mapping(sealed_records, "E0B_SEALED_RECORDS_REQUIRED")
    for key in (
        "bundle",
        "baseline",
        "packet",
        "post",
        "review_package",
        "review_mapping",
        "rubric",
        "session_manifest",
        "session",
    ):
        if key not in seals:
            raise GvE0bDv1Error(f"E0B_SEALED_RECORD_MISSING:{key}")
    verify_bundle_seal(seals["bundle"])
    verify_baseline_seal(seals["baseline"])
    verify_packet_seal(seals["packet"])
    verify_post_packet_seal(
        seals["post"], packet=seals["packet"], baseline=seals["baseline"]
    )
    verify_review_package(seals["review_package"])
    verify_review_mapping(
        seals["review_mapping"],
        review_package_hash=seals["review_package"]["review_package_hash"],
    )
    verify_review_package_bound_to_records(
        package=seals["review_package"],
        mapping=seals["review_mapping"],
        baseline=seals["baseline"],
        post=seals["post"],
        packet=seals["packet"],
        bundle=seals["bundle"],
    )
    verify_rubric_seal(
        seals["rubric"],
        baseline=seals["baseline"],
        post=seals["post"],
        packet=seals["packet"],
        review_package=seals["review_package"],
        review_mapping=seals["review_mapping"],
    )
    verify_session_bound_to_records(seals["session"], seals)
    if seals["baseline"]["baseline_hash"] != plain["baseline_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_BASELINE_HASH_MISMATCH")
    if seals["packet"]["packet_hash"] != plain["packet_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_PACKET_HASH_MISMATCH")
    if seals["post"]["post_packet_hash"] != plain["post_packet_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_POST_HASH_MISMATCH")
    if seals["rubric"]["rubric_hash"] != plain["rubric_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_RUBRIC_HASH_MISMATCH")
    observed_eligible = is_observed_comparison_eligible(
        seals["baseline"], seals["post"], seals["rubric"]
    )
    disposition = (
        decision_value_disposition_from_comparison(plain)
        if observed_eligible
        else None
    )
    observation_claim = {
        "comparison_observed_eligible": observed_eligible,
        "observed_comparison_count": 1 if observed_eligible else 0,
        "human_ids_are_attribution_only": True,
        "external_attestation_required": False,
        "third_attestor_required": False,
        "mechanical_blinding_required": True,
        "budget_model": "EQUAL_MAX_MINUTES_EARLY_SUBMIT_ALLOWED",
        "ledger_custody_note": seals["session"].get("ledger_custody_note"),
    }
    value_claim = {
        "decision_value_disposition": disposition,
        "rule_version": "G08_ONE_CASE_VALUE_V1",
        "improved_requires_positive_total_delta": True,
        "improved_requires_targeted_dimension_gain": list(TARGETED_VALUE_DIMENSIONS),
        "improved_forbids_core_safety_regression": list(CORE_SAFETY_DIMENSIONS),
        "general_causal_superiority_claim": False,
    }
    result_body = {
        "schema_version": "gv_e0b_dv1_result_v4",
        "case_id": CASE_ID,
        "run_class": RUN_CLASS_SYNTHETIC,
        "comparison": plain,
        "sealed_records": {
            "bundle": _plain(seals["bundle"]),
            "baseline": _plain(seals["baseline"]),
            "packet": _plain(seals["packet"]),
            "post": _plain(seals["post"]),
            "review_package": _plain(seals["review_package"]),
            "review_mapping": _plain(seals["review_mapping"]),
            "rubric": _plain(seals["rubric"]),
            "session_manifest": _plain(seals["session_manifest"]),
            "session": {
                k: _plain(v)
                for k, v in seals["session"].items()
                if k not in {"events_dir", "session_manifest"}
            },
        },
        "observation_claim": observation_claim,
        "value_claim": value_claim,
        "claim_boundary": (
            "Observed within-case difference only. A methodologically valid "
            "comparison does not itself demonstrate decision value. IMPROVED is "
            "a bounded one-case disposition under the frozen rubric, not general "
            "causal superiority, population effectiveness, research-efficiency, "
            "alpha, or score uplift. REAL_HUMAN labels are attribution only. "
            "Observation eligibility requires two-human structure, blinded ARM "
            "input mode, operator/reviewer custody attestations, and bound chain replay. "
            "Blinding is arm-label blinding under separated export custody, not "
            "absolute cryptographic proof of reviewer ignorance. Engine fixtures "
            "do not count as observed comparisons. Ledger is tamper-evident under "
            "capture-process custody only."
        ),
    }
    result_hash = domain_hash(DOMAIN_RESULT, result_body)
    out = dict(result_body)
    out["result_hash"] = result_hash
    return _freeze(out)


def verify_comparison_document(comparison: Mapping[str, Any]) -> Mapping[str, Any]:
    plain = _plain(comparison)
    claimed = _require_sha256(
        plain.get("comparison_hash"), "E0B_COMPARISON_HASH_INVALID"
    )
    body = _without_keys(plain, "comparison_hash")
    if domain_hash(DOMAIN_COMPARISON, body) != claimed:
        raise GvE0bDv1Error("E0B_COMPARISON_SEAL_MISMATCH")
    stage = body.get("stage_claim")
    if not isinstance(stage, Mapping):
        raise GvE0bDv1Error("E0B_STAGE_CLAIM_REQUIRED")
    comparison_count = stage.get("observed_comparison_count")
    if type(comparison_count) is not int or comparison_count != 0:
        raise GvE0bDv1Error("E0B_COMPARISON_COUNT_MUST_BE_ZERO")
    if stage.get("comparison_observed_eligible") is not False:
        raise GvE0bDv1Error("E0B_COMPARISON_OBSERVED_MUST_BE_FALSE")
    if stage.get("decision_value_disposition") is not None:
        raise GvE0bDv1Error("E0B_COMPARISON_VALUE_MUST_BE_UNEVALUATED")
    if stage.get("shipped_product_score") != 39 or stage.get("score_frozen") is not True:
        raise GvE0bDv1Error("E0B_SCORE_FREEZE_VIOLATION")
    if stage.get("functional_stage") != "CERTIFIED_SINGLE_DECISION_OPERABLE":
        raise GvE0bDv1Error("E0B_STAGE_FREEZE_VIOLATION")
    if stage.get("alpha_claim") is not False:
        raise GvE0bDv1Error("E0B_ALPHA_CLAIM_FORBIDDEN")
    return _freeze(plain)


def verify_result_document(result: Mapping[str, Any]) -> Mapping[str, Any]:
    plain = _plain(result)
    claimed = _require_sha256(plain.get("result_hash"), "E0B_RESULT_HASH_INVALID")
    body = _without_keys(plain, "result_hash")
    if domain_hash(DOMAIN_RESULT, body) != claimed:
        raise GvE0bDv1Error("E0B_RESULT_SEAL_MISMATCH")
    if body.get("schema_version") != "gv_e0b_dv1_result_v4":
        raise GvE0bDv1Error("E0B_RESULT_SCHEMA_INVALID")
    if body.get("case_id") != CASE_ID:
        raise GvE0bDv1Error("E0B_RESULT_CASE_ID_MISMATCH")
    if body.get("run_class") != RUN_CLASS_SYNTHETIC:
        raise GvE0bDv1Error("E0B_RESULT_RUN_CLASS_MISMATCH")
    comparison = body.get("comparison")
    if not isinstance(comparison, Mapping):
        raise GvE0bDv1Error("E0B_RESULT_COMPARISON_MISSING")
    verify_comparison_document(comparison)
    seals = body.get("sealed_records")
    if not isinstance(seals, Mapping):
        raise GvE0bDv1Error("E0B_SEALED_RECORDS_REQUIRED")
    for key in (
        "bundle",
        "baseline",
        "packet",
        "post",
        "review_package",
        "review_mapping",
        "rubric",
        "session_manifest",
        "session",
    ):
        if key not in seals:
            raise GvE0bDv1Error(f"E0B_SEALED_RECORD_MISSING:{key}")
    verify_session_manifest(seals["session_manifest"])
    verify_bundle_seal(seals["bundle"])
    verify_baseline_seal(seals["baseline"])
    verify_packet_seal(seals["packet"])
    verify_post_packet_seal(
        seals["post"], packet=seals["packet"], baseline=seals["baseline"]
    )
    verify_review_package(seals["review_package"])
    verify_review_mapping(
        seals["review_mapping"],
        review_package_hash=seals["review_package"]["review_package_hash"],
    )
    verify_review_package_bound_to_records(
        package=seals["review_package"],
        mapping=seals["review_mapping"],
        baseline=seals["baseline"],
        post=seals["post"],
        packet=seals["packet"],
        bundle=seals["bundle"],
    )
    verify_rubric_seal(
        seals["rubric"],
        baseline=seals["baseline"],
        post=seals["post"],
        packet=seals["packet"],
        review_package=seals["review_package"],
        review_mapping=seals["review_mapping"],
    )
    verify_session_bound_to_records(seals["session"], seals)
    expected_comparison = _build_comparison_from_verified_records(
        bundle=seals["bundle"],
        packet=seals["packet"],
        seals=seals,
    )
    if _plain(comparison) != _plain(expected_comparison):
        raise GvE0bDv1Error("E0B_RESULT_COMPARISON_BINDING_MISMATCH")
    if seals["baseline"]["baseline_hash"] != comparison["baseline_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_BASELINE_HASH_MISMATCH")
    if seals["packet"]["packet_hash"] != comparison["packet_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_PACKET_HASH_MISMATCH")
    if seals["post"]["post_packet_hash"] != comparison["post_packet_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_POST_HASH_MISMATCH")
    if seals["rubric"]["rubric_hash"] != comparison["rubric_hash"]:
        raise GvE0bDv1Error("E0B_RESULT_RUBRIC_HASH_MISMATCH")
    observed_eligible = is_observed_comparison_eligible(
        seals["baseline"], seals["post"], seals["rubric"]
    )
    observation_claim = _require_mapping(
        body.get("observation_claim"), "E0B_OBSERVATION_CLAIM_REQUIRED"
    )
    if observation_claim.get("comparison_observed_eligible") is not observed_eligible:
        raise GvE0bDv1Error("E0B_OBSERVATION_ELIGIBILITY_MISMATCH")
    expected_count = 1 if observed_eligible else 0
    observed_count = observation_claim.get("observed_comparison_count")
    if type(observed_count) is not int or observed_count != expected_count:
        raise GvE0bDv1Error("E0B_OBSERVED_COUNT_MISMATCH")
    value_claim = _require_mapping(
        body.get("value_claim"), "E0B_VALUE_CLAIM_REQUIRED"
    )
    expected_disposition = (
        decision_value_disposition_from_comparison(comparison)
        if observed_eligible
        else None
    )
    if value_claim.get("decision_value_disposition") != expected_disposition:
        raise GvE0bDv1Error("E0B_VALUE_DISPOSITION_MISMATCH")
    if value_claim.get("rule_version") != "G08_ONE_CASE_VALUE_V1":
        raise GvE0bDv1Error("E0B_VALUE_RULE_VERSION_INVALID")
    if value_claim.get("improved_requires_positive_total_delta") is not True:
        raise GvE0bDv1Error("E0B_VALUE_RULE_TOTAL_INVALID")
    if value_claim.get("improved_requires_targeted_dimension_gain") != list(
        TARGETED_VALUE_DIMENSIONS
    ):
        raise GvE0bDv1Error("E0B_VALUE_RULE_TARGETED_INVALID")
    if value_claim.get("improved_forbids_core_safety_regression") != list(
        CORE_SAFETY_DIMENSIONS
    ):
        raise GvE0bDv1Error("E0B_VALUE_RULE_SAFETY_INVALID")
    if value_claim.get("general_causal_superiority_claim") is not False:
        raise GvE0bDv1Error("E0B_VALUE_CAUSAL_CLAIM_FORBIDDEN")
    return _freeze(plain)


def load_verified_result(path: Path) -> Mapping[str, Any]:
    raw = _load_json_object(path)
    return verify_result_document(raw)


def stage_compare(
    *,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    post_path: Path = DEFAULT_POST_PATH,
    rubric_path: Path = DEFAULT_RUBRIC_PATH,
    packet_path: Path = DEFAULT_PACKET_PATH,
    session_path: Path = DEFAULT_SESSION_PATH,
    package_path: Path = DEFAULT_REVIEW_PACKAGE_PATH,
    mapping_path: Path = DEFAULT_REVIEW_MAPPING_PATH,
    result_json_path: Path = DEFAULT_RESULT_JSON,
    decision_packet_path: Path = DEFAULT_DECISION_PACKET_MD,
    bundle: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    return run_e0b_dv1_case(
        baseline_path=baseline_path,
        post_path=post_path,
        rubric_path=rubric_path,
        packet_path=packet_path,
        session_path=session_path,
        package_path=package_path,
        mapping_path=mapping_path,
        result_json_path=result_json_path,
        decision_packet_path=decision_packet_path,
        bundle=bundle,
    )


def build_decision_packet_markdown(result: Mapping[str, Any]) -> str:
    verified = verify_result_document(result)
    c = _plain(verified["comparison"])
    observation = _plain(verified["observation_claim"])
    value = _plain(verified["value_claim"])
    lines = [
        "# GV-E0B-DV1 Decision Packet — G08 Contradiction Case",
        "",
        f"- case_id: `{c['case_id']}`",
        f"- run_class: `{c['run_class']}`",
        f"- acceptance_case: `{c['acceptance_case']}`",
        f"- comparison_hash: `{c['comparison_hash']}`",
        f"- bundle_hash: `{c['bundle_hash']}`",
        f"- baseline_hash: `{c['baseline_hash']}`",
        f"- packet_hash: `{c['packet_hash']}`",
        f"- post_packet_hash: `{c['post_packet_hash']}`",
        f"- review_package_hash: `{c.get('review_package_hash', '')}`",
        f"- rubric_hash: `{c['rubric_hash']}`",
        f"- observed_comparison_count: `{observation['observed_comparison_count']}`",
        f"- comparison_observed_eligible: `{observation['comparison_observed_eligible']}`",
        f"- decision_value_disposition: `{value['decision_value_disposition']}`",
        f"- shipped_product_score: `39` (frozen)",
        f"- functional_stage: `{c['stage_claim']['functional_stage']}`",
        "",
        "## Baseline",
        f"- authorship: `{c['baseline']['authorship_kind']}` / `{c['baseline']['operator_id']}`",
        f"- sealed_at: `{c['baseline']['sealed_at']}`",
        f"- elapsed_seconds: `{c['baseline'].get('elapsed_seconds')}` / budget `{c['baseline'].get('allowed_budget_minutes')}m`",
        f"- action: `{c['baseline']['action']}`",
        f"- rationale: {c['baseline']['rationale']}",
        "",
        "## GodView packet",
        f"- run_state: `{c['godview_packet']['run_state']}`",
        f"- block_reason: `{c['godview_packet']['block_reason']}`",
        f"- rationale: {c['godview_packet']['rationale']}",
        "",
        "## Post-packet",
        f"- authorship: `{c['post_packet']['authorship_kind']}` / `{c['post_packet']['operator_id']}`",
        f"- sealed_at: `{c['post_packet']['sealed_at']}`",
        f"- elapsed_seconds: `{c['post_packet'].get('elapsed_seconds')}` / budget `{c['post_packet'].get('allowed_budget_minutes')}m`",
        f"- action: `{c['post_packet']['action']}`",
        f"- rationale: {c['post_packet']['rationale']}",
        "",
        "## Rubric delta (observed within-case only)",
        f"- reviewer: `{c['rubric']['reviewer_id']}` ({c['rubric']['authorship_kind']})",
        f"- baseline_total: `{c['rubric']['baseline']['total']}`",
        f"- post_total: `{c['rubric']['post_packet']['total']}`",
        f"- total_score_difference: `{c['delta']['total_score_difference']['value_string']}`",
        f"- action_change: `{c['delta']['action_change']}`",
        "",
        "Interpretation: observed within-case difference only. Observation "
        "eligibility and decision-value disposition are separate. No general "
        "causal or population-effectiveness claim.",
        "",
    ]
    return "\n".join(lines)


def write_canonical_artifacts(
    comparison: Mapping[str, Any],
    *,
    sealed_records: Mapping[str, Any],
    result_json_path: Path = DEFAULT_RESULT_JSON,
    decision_packet_path: Path = DEFAULT_DECISION_PACKET_MD,
) -> Mapping[str, Any]:
    result = build_result_document(comparison, sealed_records=sealed_records)
    result_bytes = canonical_document_bytes(_plain(result))
    packet_md = build_decision_packet_markdown(result).encode("utf-8")
    _atomic_write_pair(
        result_json_path,
        result_bytes,
        decision_packet_path,
        packet_md,
    )
    if result_json_path.read_bytes() != result_bytes:
        raise GvE0bDv1Error("E0B_RESULT_JSON_VERIFY_FAILED")
    if decision_packet_path.read_bytes() != packet_md:
        raise GvE0bDv1Error("E0B_DECISION_PACKET_VERIFY_FAILED")
    return result


def e0b_rationale_ref(comparison_hash: str) -> str:
    digest = _require_sha256(comparison_hash, "E0B_COMPARISON_HASH_INVALID")
    ref = f"{RATIONALE_REF_PREFIX}{digest}"
    if len(ref) > 128:
        raise GvE0bDv1Error("E0B_RATIONALE_REF_TOO_LONG")
    return ref


def _build_e0b_decision(
    fixture_hash: str,
    fixture_id: str,
    *,
    rationale_ref: str,
) -> _DecisionEnvelope:
    if not rationale_ref.startswith(RATIONALE_REF_PREFIX):
        raise GvE0bDv1Error("E0B_RATIONALE_REF_PREFIX_INVALID")
    return _build_decision(
        fixture_hash=fixture_hash,
        fixture_id=fixture_id,
        decision_id=E0B_DECISION_ID,
        action=PORTFOLIO_ACTION_NO_POSITION,
        requested_quantity=None,
        rationale_ref=rationale_ref,
    )


def _build_e0b_book(*, comparison_hash: str) -> _OpenBookBuild:
    rationale_ref = e0b_rationale_ref(comparison_hash)

    def decision_builder(fixture_hash: str, fixture_id: str) -> _DecisionEnvelope:
        return _build_e0b_decision(
            fixture_hash,
            fixture_id,
            rationale_ref=rationale_ref,
        )

    return _build_book(
        fixture=_build_no_position_source_fixture(),
        decision_builder=decision_builder,
    )


def _build_e0b_certified_result_from_verified_result(
    verified_result: Mapping[str, Any],
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    """Build the private E0B certificate from one verified result only.

    This closes the official E0B comparison-only authority route. It does not
    claim to stop a privileged repository operator from manually invoking lower-
    level certification or publication infrastructure outside this module.
    """

    candidate = _plain(verified_result)
    observation = _require_mapping(
        candidate.get("observation_claim"), "E0B_OBSERVATION_CLAIM_REQUIRED"
    )
    if observation.get("comparison_observed_eligible") is not True:
        raise GvE0bDv1Error("E0B_PUBLISH_REQUIRES_OBSERVED_ELIGIBLE")
    count = observation.get("observed_comparison_count")
    if type(count) is not int or count != 1:
        raise GvE0bDv1Error("E0B_PUBLISH_REQUIRES_COUNT_ONE")

    verified = verify_result_document(candidate)
    comparison = _require_mapping(
        verified.get("comparison"), "E0B_RESULT_COMPARISON_MISSING"
    )
    comparison_hash = _require_sha256(
        comparison.get("comparison_hash"), "E0B_COMPARISON_HASH_INVALID"
    )
    certified = _build_certified_result_from_book(
        _build_e0b_book(comparison_hash=comparison_hash),
        verifier_runner,
    )
    decision = certified.get("decision") or {}
    expected_ref = e0b_rationale_ref(comparison_hash)
    if decision.get("decision_id") != E0B_DECISION_ID:
        raise GvE0bDv1Error("E0B_CERT_DECISION_ID_MISMATCH")
    if decision.get("rationale_ref") != expected_ref:
        raise GvE0bDv1Error("E0B_CERT_RATIONALE_BINDING_INVALID")
    if decision.get("action") != PORTFOLIO_ACTION_NO_POSITION:
        raise GvE0bDv1Error("E0B_CERT_ACTION_MISMATCH")
    if certified.get("certification", {}).get("certification_status") != "CERTIFIED":
        raise GvE0bDv1Error("E0B_CERT_STATUS_REQUIRED")
    return certified


def run_e0b_dv1_case(
    *,
    baseline_path: Path,
    post_path: Path,
    rubric_path: Path,
    packet_path: Path | None = None,
    session_path: Path | None = None,
    package_path: Path | None = None,
    mapping_path: Path | None = None,
    packet: Mapping[str, Any] | None = None,
    bundle: Mapping[str, Any] | None = None,
    result_json_path: Path = DEFAULT_RESULT_JSON,
    decision_packet_path: Path = DEFAULT_DECISION_PACKET_MD,
    publish: bool = False,
    current_target: Path = DEFAULT_CURRENT_DECISION_TARGET,
    current_lock: Path = DEFAULT_CURRENT_DECISION_LOCK,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> Mapping[str, Any]:
    if packet_path is None and packet is None:
        raise GvE0bDv1Error("E0B_PACKET_REQUIRED")
    if session_path is None or package_path is None or mapping_path is None:
        raise GvE0bDv1Error("E0B_SESSION_PACKAGE_REQUIRED")
    _require_active_checkpoint_for_authoritative_stage(session_path, "FINALIZE")
    case_paths: list[tuple[str, Path | None]] = [
        ("baseline", baseline_path),
        ("post", post_path),
        ("rubric", rubric_path),
        ("packet", packet_path or DEFAULT_PACKET_PATH),
        ("session", session_path),
        ("review_package", package_path),
        ("review_mapping", mapping_path),
        ("result", result_json_path),
        ("decision_packet", decision_packet_path),
    ]
    if publish:
        case_paths.extend(
            [
                ("current_target", current_target),
                ("current_lock", current_lock),
            ]
        )
    _require_distinct_case_paths(case_paths)
    comparison = build_comparison(
        baseline_path=baseline_path,
        post_path=post_path,
        rubric_path=rubric_path,
        packet_path=packet_path,
        packet=packet,
        bundle=bundle,
        session_path=session_path,
        package_path=package_path,
        mapping_path=mapping_path,
    )
    sealed_records = _collect_sealed_records(
        baseline_path=baseline_path,
        post_path=post_path,
        rubric_path=rubric_path,
        packet_path=packet_path or DEFAULT_PACKET_PATH,
        session_path=session_path,
        package_path=package_path,
        mapping_path=mapping_path,
        bundle=bundle,
    )
    if publish:
        preflight_result = verify_result_document(
            build_result_document(comparison, sealed_records=sealed_records)
        )
        preflight_observation = preflight_result["observation_claim"]
        if preflight_observation.get("comparison_observed_eligible") is not True:
            raise GvE0bDv1Error("E0B_PUBLISH_REQUIRES_OBSERVED_ELIGIBLE")
        preflight_count = preflight_observation.get("observed_comparison_count")
        if type(preflight_count) is not int or preflight_count != 1:
            raise GvE0bDv1Error("E0B_PUBLISH_REQUIRES_COUNT_ONE")
    result = write_canonical_artifacts(
        comparison,
        sealed_records=sealed_records,
        result_json_path=result_json_path,
        decision_packet_path=decision_packet_path,
    )
    verified_result = load_verified_result(result_json_path)
    observation = verified_result["observation_claim"]
    value_claim = verified_result["value_claim"]
    published = None
    if publish:
        if observation["comparison_observed_eligible"] is not True:
            raise GvE0bDv1Error("E0B_PUBLISH_REQUIRES_OBSERVED_ELIGIBLE")
        observed_count = observation.get("observed_comparison_count")
        if type(observed_count) is not int or observed_count != 1:
            raise GvE0bDv1Error("E0B_PUBLISH_REQUIRES_COUNT_ONE")
        certified = _build_e0b_certified_result_from_verified_result(
            verified_result,
            verifier_runner,
        )
        comparison_hash = verified_result["comparison"]["comparison_hash"]
        decision = certified.get("decision") or {}
        if decision.get("rationale_ref") != e0b_rationale_ref(comparison_hash):
            raise GvE0bDv1Error("E0B_CERT_RATIONALE_BINDING_INVALID")
        published = _publish_current_decision(
            certified,
            target=current_target,
            lock_path=current_lock,
        )
    return _freeze(
        {
            "comparison": comparison,
            "result": verified_result,
            "published": None
            if published is None
            else {
                "status": published.status,
                "target_path": published.target_path,
                "certified_decision_result_hash": published.certified_decision_result_hash,
            },
            "observed_comparison_count": observation["observed_comparison_count"],
            "comparison_observed_eligible": observation[
                "comparison_observed_eligible"
            ],
            "decision_value_disposition": value_claim[
                "decision_value_disposition"
            ],
            "run_class": RUN_CLASS_SYNTHETIC,
        }
    )


def build_comparison_presentation(
    comparison: Mapping[str, Any],
    *,
    observation_claim: Mapping[str, Any] | None = None,
    value_claim: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    c = _plain(comparison)
    observation = (
        _plain(observation_claim)
        if observation_claim is not None
        else {
            "observed_comparison_count": c["stage_claim"][
                "observed_comparison_count"
            ],
            "comparison_observed_eligible": c["stage_claim"][
                "comparison_observed_eligible"
            ],
        }
    )
    value = (
        _plain(value_claim)
        if value_claim is not None
        else {
            "decision_value_disposition": c["stage_claim"][
                "decision_value_disposition"
            ]
        }
    )
    rows = [
        {"label": "Case", "value": str(c["case_id"])},
        {"label": "AcceptanceCase", "value": "G08"},
        {"label": "RunClass", "value": RUN_CLASS_SYNTHETIC},
        {
            "label": "GodViewRunState",
            "value": str(c["godview_packet"]["run_state"]),
        },
        {
            "label": "BlockReason",
            "value": str(c["godview_packet"]["block_reason"]),
        },
        {
            "label": "BaselineAuthorship",
            "value": str(c["baseline"]["authorship_kind"]),
        },
        {
            "label": "BaselineAction",
            "value": str(c["baseline"]["action"]),
        },
        {
            "label": "PostPacketAuthorship",
            "value": str(c["post_packet"]["authorship_kind"]),
        },
        {
            "label": "PostPacketAction",
            "value": str(c["post_packet"]["action"]),
        },
        {
            "label": "ActionChange",
            "value": "TRUE" if c["delta"]["action_change"] else "FALSE",
        },
        {
            "label": "RubricTotalDelta",
            "value": str(c["delta"]["total_score_difference"]["value_string"]),
        },
        {
            "label": "Reviewer",
            "value": f"{c['rubric']['reviewer_id']} ({c['rubric']['authorship_kind']})",
        },
        {
            "label": "ObservedComparisonCount",
            "value": str(observation["observed_comparison_count"]),
        },
        {
            "label": "ComparisonObservedEligible",
            "value": (
                "TRUE"
                if observation["comparison_observed_eligible"]
                else "FALSE"
            ),
        },
        {
            "label": "DecisionValueDisposition",
            "value": str(value["decision_value_disposition"] or "NOT_EVALUATED"),
        },
        {
            "label": "ComparisonHash",
            "value": str(c["comparison_hash"]),
        },
        {"label": "AlphaClaim", "value": "FALSE"},
        {"label": "ShippedProductScore", "value": "39"},
        {
            "label": "FunctionalStage",
            "value": "CERTIFIED_SINGLE_DECISION_OPERABLE",
        },
    ]
    return _freeze(
        {
            "title": "GV-E0B-DV1 Decision Delta — G08 Contradiction Case",
            "rows": rows,
        }
    )


def render_e0b_dv1_comparison(
    renderer: Any,
    *,
    comparison: Mapping[str, Any] | None = None,
    result_json_path: Path | None = None,
) -> Mapping[str, Any]:
    obs = 0
    observed_eligible = False
    disposition: str | None = None
    observation_claim: Mapping[str, Any] | None = None
    value_claim: Mapping[str, Any] | None = None
    inv_note = ""
    if comparison is None:
        path = result_json_path or DEFAULT_RESULT_JSON
        if not path.is_file():
            raise GvE0bDv1Error("E0B_RESULT_MISSING")
        result = load_verified_result(path)
        comparison = result["comparison"]
        authority = observation_authority_from_disk(path)
        obs = int(authority["observed_comparison_count"])
        observed_eligible = bool(authority["comparison_observed_eligible"])
        disposition = authority.get("decision_value_disposition")
        if authority.get("invalidation") is not None:
            inv = authority["invalidation"]
            inv_note = (
                f" · INVALIDATED:{inv.get('classification')} "
                "(Attempt-1 observation authority superseded; sealed evidence preserved)"
            )
            observation_claim = {
                "comparison_observed_eligible": False,
                "observed_comparison_count": 0,
            }
            value_claim = {"decision_value_disposition": None}
        else:
            observation_claim = result["observation_claim"]
            value_claim = result["value_claim"]
    else:
        comparison = verify_comparison_document(comparison)
    presentation = build_comparison_presentation(
        comparison,
        observation_claim=observation_claim,
        value_claim=value_claim,
    )
    renderer.subheader(presentation["title"])
    renderer.table(list(presentation["rows"]))
    renderer.caption(
        "E0B-DV1 · G08 · SYNTHETIC_DEV_RUN · score 39 frozen · "
        f"observed-comparison count = {obs} · "
        f"observed_eligible={observed_eligible} · "
        f"value_disposition={disposition or 'NOT_EVALUATED'} · "
        "within-case difference only · no general causal/alpha claim"
        f"{inv_note}"
    )
    return presentation


def load_attempt1_invalidation(
    path: Path = DEFAULT_ATTEMPT1_INVALIDATION_PATH,
) -> dict[str, Any] | None:
    """Load append-only Attempt-1 invalidation authority if present."""

    inv_path = Path(path)
    if not inv_path.is_file():
        return None
    try:
        raw = json.loads(inv_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    if raw.get("attempt") != 1:
        return None
    if raw.get("classification") != INVALIDATION_CLASS_REVIEWER_INDEPENDENCE:
        return None
    if raw.get("observation_authority_superseded") is not True:
        return None
    return raw


def observation_authority_from_disk(
    result_json_path: Path = DEFAULT_RESULT_JSON,
    *,
    invalidation_path: Path = DEFAULT_ATTEMPT1_INVALIDATION_PATH,
) -> dict[str, Any]:
    """Authoritative observation status after optional invalidation supersession.

    Preserved sealed Attempt-1 result bytes are never rewritten. An append-only
    invalidation packet supersedes observation eligibility / count only for the
    canonical case result path (not isolated fixture temp results).
    """

    result_path = Path(result_json_path)
    # Invalidation binds only the production case result, not test fixtures.
    apply_invalidation = False
    try:
        apply_invalidation = result_path.resolve() == DEFAULT_RESULT_JSON.resolve()
    except OSError:
        apply_invalidation = str(result_path).replace("\\", "/").endswith(
            "data/gv_e0b/dv1_g08/result.json"
        )
    inv = load_attempt1_invalidation(invalidation_path) if apply_invalidation else None
    if inv is not None:
        return {
            "comparison_observed_eligible": False,
            "observed_comparison_count": 0,
            "decision_value_disposition": None,
            "functional_stage": "CERTIFIED_SINGLE_DECISION_OPERABLE",
            "shipped_product_score": 39,
            "invalidation": inv,
            "authority": "INVALIDATION_SUPERSEDES_SEALED_RESULT",
        }
    if not result_path.is_file():
        return {
            "comparison_observed_eligible": False,
            "observed_comparison_count": 0,
            "decision_value_disposition": None,
            "functional_stage": "CERTIFIED_SINGLE_DECISION_OPERABLE",
            "shipped_product_score": 39,
            "invalidation": None,
            "authority": "NO_RESULT",
        }
    try:
        result = load_verified_result(result_path)
        observation = result["observation_claim"]
        value = result["value_claim"]
        eligible = observation.get("comparison_observed_eligible") is True
        return {
            "comparison_observed_eligible": eligible,
            "observed_comparison_count": (
                int(observation["observed_comparison_count"]) if eligible else 0
            ),
            "decision_value_disposition": (
                value.get("decision_value_disposition") if eligible else None
            ),
            "functional_stage": "CERTIFIED_SINGLE_DECISION_OPERABLE",
            "shipped_product_score": 39,
            "invalidation": None,
            "authority": "SEALED_RESULT",
        }
    except GvE0bDv1Error:
        return {
            "comparison_observed_eligible": False,
            "observed_comparison_count": 0,
            "decision_value_disposition": None,
            "functional_stage": "CERTIFIED_SINGLE_DECISION_OPERABLE",
            "shipped_product_score": 39,
            "invalidation": None,
            "authority": "RESULT_UNVERIFIED",
        }


def observed_comparison_count_from_disk(
    result_json_path: Path = DEFAULT_RESULT_JSON,
) -> int:
    auth = observation_authority_from_disk(result_json_path)
    return int(auth["observed_comparison_count"])


__all__ = [
    "AUTH_FIXTURE",
    "AUTH_REAL_OPERATOR",
    "AUTH_REAL_REVIEWER",
    "AUTHORING_ONLY",
    "AdvanceableClock",
    "BASELINE_TEMPLATE_ID",
    "BUDGET_MINUTES",
    "BLOCK_REASON",
    "BLINDING_CUSTODY_MODEL",
    "CANONICAL_STAGE_ORDER",
    "CAPTURE_STATE_ABORTED",
    "CAPTURE_STATE_ACTIVE",
    "CAPTURE_STATE_COMPLETE",
    "CAPTURE_STATE_RESUMABLE",
    "CASE_ID",
    "CORE_SAFETY_DIMENSIONS",
    "DECISION_VALUE_IMPROVED",
    "DECISION_VALUE_NOT_IMPROVED",
    "DEFAULT_AUTHORING_TEMPLATES_DIR",
    "DEFAULT_CHECKPOINTS_DIR",
    "DEFAULT_SESSION_MANIFEST_PATH",
    "POST_TEMPLATE_ID",
    "REVIEW_ARM_FIELDS",
    "REVIEWER_EXPORT_EXACT_NAMES",
    "DEFAULT_BASELINE_PATH",
    "DEFAULT_DECISION_PACKET_MD",
    "DEFAULT_EVENTS_DIR",
    "DEFAULT_OPERATOR_CUSTODY_DIR",
    "DEFAULT_PACKET_PATH",
    "DEFAULT_POST_PATH",
    "DEFAULT_RESULT_JSON",
    "DEFAULT_REVIEWER_EXPORT_DIR",
    "DEFAULT_REVIEW_MAPPING_PATH",
    "DEFAULT_REVIEW_PACKAGE_PATH",
    "DEFAULT_RUBRIC_AUTHORING_PATH",
    "DEFAULT_RUBRIC_PATH",
    "DEFAULT_SESSION_PATH",
    "E0B_DECISION_ID",
    "RATIONALE_REF_PREFIX",
    "REVIEW_INPUT_MODE_BLINDED",
    "RUBRIC_ITEMS",
    "RUBRIC_TEMPLATE_ID",
    "RUN_CLASS_SYNTHETIC",
    "TARGETED_VALUE_DIMENSIONS",
    "WallClock",
    "GvE0bDv1Error",
    "abort_capture_session",
    "append_capture_checkpoint",
    "blank_baseline_authoring_template",
    "blank_post_authoring_template",
    "blank_rubric_authoring_template",
    "build_comparison",
    "build_comparison_presentation",
    "build_decision_packet_markdown",
    "build_godview_packet",
    "build_result_document",
    "capture_lifecycle_state",
    "decision_value_disposition_from_comparison",
    "e0b_rationale_ref",
    "is_attribution_structure_valid",
    "is_observed_comparison_eligible",
    "load_baseline_seal",
    "load_capture_checkpoints",
    "load_capture_session",
    "load_session_manifest",
    "load_packet_seal",
    "load_post_packet_seal",
    "load_rubric_scores",
    "load_verified_result",
    "observed_comparison_count_from_disk",
    "open_capture_session",
    "recover_capture_checkpoint",
    "render_e0b_dv1_comparison",
    "require_capture_resumable",
    "run_e0b_dv1_case",
    "seal_baseline_record",
    "seal_post_packet_record",
    "seal_review_package",
    "seal_rubric_record",
    "sealed_adversarial_bundle",
    "stage_build_review_package",
    "stage_capture_baseline",
    "stage_capture_post",
    "stage_capture_rubric",
    "stage_compare",
    "stage_generate_packet",
    "stage_open_arm",
    "verify_bundle_seal",
    "verify_comparison_document",
    "verify_mapping_randomization",
    "verify_review_mapping",
    "verify_review_package",
    "verify_review_package_bound_to_records",
    "verify_result_document",
    "verify_session_manifest",
    "write_authoring_templates",
    "write_canonical_artifacts",
    "ONESHOT_CASE_ID",
    "ONESHOT_ATTEMPT",
    "ONESHOT_AUTH_SCHEMA",
    "GITHUB_RECEIPT_SCHEMA",
    "GITHUB_RECEIPT_SCHEMA_V2",
    "INVALIDATION_CLASS_REVIEWER_INDEPENDENCE",
    "DEFAULT_ATTEMPT1_INVALIDATION_PATH",
    "load_attempt1_invalidation",
    "observation_authority_from_disk",
    "RECEIPT_PROVIDER_GITHUB",
    "PREREGISTRATION_RELATIVE_PATH",
    "assert_mapping_reveal_allowed",
    "build_github_rubric_receipt",
    "build_oneshot_authorization",
    "import_external_rubric_submission",
    "verify_github_rubric_receipt",
    "verify_oneshot_authorization",
]
