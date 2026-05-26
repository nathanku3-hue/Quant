from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "boot-status/v1"
DEFAULT_BOOT_STATUS_PATH = Path("runtime/boot_status_current.json")
BOOT_STATUS_CURRENT_PATH = DEFAULT_BOOT_STATUS_PATH
LEGACY_BOOT_STATUS_PATH = Path("docs/context/boot_status_current.json")

PRIMARY_VERDICTS = ("ready", "degraded", "blocked")
CHECK_STATUSES = ("pass", "warn", "fail", "not_applicable", "deferred")
CHECK_SEVERITIES = ("ready", "degraded", "blocked")
NEXT_SAFE_ACTION_VERBS = ("Inspect", "Review", "Open")
ACTION_SHAPED_TERMS = (
    "buy",
    "sell",
    "hold",
    "rank",
    "score",
    "alert",
    "order",
    "recommendation",
    "conviction",
    "act",
    "trade",
)


class BootStatusValidationError(ValueError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_choice(value: Any, *, allowed: Sequence[str], field_name: str) -> str:
    normalized = str(value).strip().lower()
    if normalized not in allowed:
        raise BootStatusValidationError(f"{field_name} must be one of {allowed}; got {value!r}")
    return normalized


def _require_bool(payload: Mapping[str, Any], field_name: str, default: bool = False) -> bool:
    value = payload.get(field_name, default)
    if not isinstance(value, bool):
        raise BootStatusValidationError(f"BootContextFlags.{field_name} must be a boolean")
    return value


def _dangerous_terms(text: str) -> tuple[str, ...]:
    found: list[str] = []
    for term in ACTION_SHAPED_TERMS:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", text, re.IGNORECASE):
            found.append(term)
    return tuple(found)


@dataclass(frozen=True)
class BootContextFlags:
    safe_boot: bool
    boot_candidate: bool = False
    local_planning: bool = False

    def to_json_dict(self) -> dict[str, bool]:
        return {
            "safe_boot": bool(self.safe_boot),
            "boot_candidate": bool(self.boot_candidate),
            "local_planning": bool(self.local_planning),
        }

    @classmethod
    def from_json_dict(cls, payload: Mapping[str, Any]) -> "BootContextFlags":
        return cls(
            safe_boot=_require_bool(payload, "safe_boot"),
            boot_candidate=_require_bool(payload, "boot_candidate"),
            local_planning=_require_bool(payload, "local_planning"),
        )


@dataclass(frozen=True)
class ReadinessCheck:
    id: str
    label: str
    status: str
    severity: str
    summary: str
    evidence_ref: str | None = None
    destination: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise BootStatusValidationError("ReadinessCheck.id is required")
        if not self.label.strip():
            raise BootStatusValidationError("ReadinessCheck.label is required")
        if not self.summary.strip():
            raise BootStatusValidationError("ReadinessCheck.summary is required")
        object.__setattr__(
            self,
            "status",
            _normalize_choice(self.status, allowed=CHECK_STATUSES, field_name="ReadinessCheck.status"),
        )
        object.__setattr__(
            self,
            "severity",
            _normalize_choice(self.severity, allowed=CHECK_SEVERITIES, field_name="ReadinessCheck.severity"),
        )

    def to_json_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "status": self.status,
            "severity": self.severity,
            "summary": self.summary,
        }
        if self.evidence_ref is not None:
            payload["evidence_ref"] = self.evidence_ref
        if self.destination is not None:
            payload["destination"] = self.destination
        if self.details:
            payload["details"] = dict(self.details)
        return payload

    @classmethod
    def from_json_dict(cls, payload: Mapping[str, Any]) -> "ReadinessCheck":
        return cls(
            id=str(payload.get("id", "")),
            label=str(payload.get("label", "")),
            status=str(payload.get("status", "")),
            severity=str(payload.get("severity", "")),
            summary=str(payload.get("summary", "")),
            evidence_ref=payload.get("evidence_ref"),
            destination=payload.get("destination"),
            details=dict(payload.get("details") or {}),
        )


@dataclass(frozen=True)
class NextSafeAction:
    label: str
    destination: str
    reason: str
    allowed_use: str = "research review"
    forbidden_use: str = "recommendation, ranking, alert, order, or trade action"

    def __post_init__(self) -> None:
        validate_next_safe_action(self)

    def to_json_dict(self) -> dict[str, str]:
        return {
            "label": self.label,
            "destination": self.destination,
            "reason": self.reason,
            "allowed_use": self.allowed_use,
            "forbidden_use": self.forbidden_use,
        }

    @classmethod
    def from_json_dict(cls, payload: Mapping[str, Any]) -> "NextSafeAction":
        return cls(
            label=str(payload.get("label", "")),
            destination=str(payload.get("destination", "")),
            reason=str(payload.get("reason", "")),
            allowed_use=str(payload.get("allowed_use", "research review")),
            forbidden_use=str(
                payload.get("forbidden_use", "recommendation, ranking, alert, order, or trade action")
            ),
        )


@dataclass(frozen=True)
class BootStatus:
    schema_version: str
    generated_at: str
    source: str
    primary_verdict: str
    flags: BootContextFlags
    checks: tuple[ReadinessCheck, ...]
    next_safe_action: NextSafeAction
    artifact_id: str | None = None
    git_commit: str | None = None
    local_context_id: str | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise BootStatusValidationError(
                f"schema_version must be {SCHEMA_VERSION!r}; got {self.schema_version!r}"
            )
        if not self.generated_at.strip():
            raise BootStatusValidationError("BootStatus.generated_at is required")
        if not self.source.strip():
            raise BootStatusValidationError("BootStatus.source is required")
        object.__setattr__(
            self,
            "primary_verdict",
            _normalize_choice(
                self.primary_verdict,
                allowed=PRIMARY_VERDICTS,
                field_name="BootStatus.primary_verdict",
            ),
        )
        object.__setattr__(self, "checks", tuple(self.checks))
        object.__setattr__(self, "warnings", tuple(str(item) for item in self.warnings))
        if not self.checks:
            raise BootStatusValidationError("BootStatus.checks must contain at least one check")
        derived = primary_verdict_from_checks(self.checks, self.flags)
        if self.primary_verdict != derived:
            raise BootStatusValidationError(
                f"primary_verdict {self.primary_verdict!r} does not match derived verdict {derived!r}"
            )
        validate_next_safe_action(self.next_safe_action)

    def to_json_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source": self.source,
            "primary_verdict": self.primary_verdict,
            "flags": self.flags.to_json_dict(),
            "checks": [check.to_json_dict() for check in self.checks],
            "next_safe_action": self.next_safe_action.to_json_dict(),
            "warnings": list(self.warnings),
        }
        if self.artifact_id is not None:
            payload["artifact_id"] = self.artifact_id
        if self.git_commit is not None:
            payload["git_commit"] = self.git_commit
        if self.local_context_id is not None:
            payload["local_context_id"] = self.local_context_id
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload

    @classmethod
    def from_json_dict(cls, payload: Mapping[str, Any]) -> "BootStatus":
        flags_payload = payload.get("flags")
        if not isinstance(flags_payload, Mapping):
            raise BootStatusValidationError("BootStatus.flags must be an object")
        checks_payload = payload.get("checks")
        if not isinstance(checks_payload, list):
            raise BootStatusValidationError("BootStatus.checks must be a list")
        action_payload = payload.get("next_safe_action")
        if not isinstance(action_payload, Mapping):
            raise BootStatusValidationError("BootStatus.next_safe_action must be an object")
        return cls(
            schema_version=str(payload.get("schema_version", "")),
            generated_at=str(payload.get("generated_at", "")),
            source=str(payload.get("source", "")),
            primary_verdict=str(payload.get("primary_verdict", "")),
            flags=BootContextFlags.from_json_dict(flags_payload),
            checks=tuple(ReadinessCheck.from_json_dict(item) for item in checks_payload),
            next_safe_action=NextSafeAction.from_json_dict(action_payload),
            artifact_id=payload.get("artifact_id"),
            git_commit=payload.get("git_commit"),
            local_context_id=payload.get("local_context_id"),
            warnings=tuple(str(item) for item in payload.get("warnings", [])),
            metadata=dict(payload.get("metadata") or {}),
        )

    def to_json_text(self) -> str:
        return json.dumps(self.to_json_dict(), indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def primary_verdict_from_checks(checks: Sequence[ReadinessCheck], flags: BootContextFlags) -> str:
    if not checks:
        return "blocked"
    severities = {check.severity for check in checks}
    statuses = {check.status for check in checks}
    if "blocked" in severities or "fail" in statuses:
        return "blocked"
    if "degraded" in severities or "warn" in statuses or "deferred" in statuses:
        return "degraded"
    return "ready" if flags.safe_boot else "degraded"


def validate_next_safe_action(action: NextSafeAction) -> None:
    if not action.label.strip():
        raise BootStatusValidationError("NextSafeAction.label is required")
    if not action.destination.strip():
        raise BootStatusValidationError("NextSafeAction.destination is required")
    if not action.reason.strip():
        raise BootStatusValidationError("NextSafeAction.reason is required")
    if not action.label.startswith(NEXT_SAFE_ACTION_VERBS):
        raise BootStatusValidationError("NextSafeAction.label must start with Inspect, Review, or Open")
    fields = {
        "label": action.label,
        "destination": action.destination,
        "reason": action.reason,
        "allowed_use": action.allowed_use,
    }
    failures = {
        field_name: terms
        for field_name, value in fields.items()
        if (terms := _dangerous_terms(str(value)))
    }
    if failures:
        rendered = "; ".join(f"{field_name}:{','.join(terms)}" for field_name, terms in failures.items())
        raise BootStatusValidationError(f"NextSafeAction contains action-shaped copy: {rendered}")


def next_safe_action_for_verdict(primary_verdict: str) -> NextSafeAction:
    verdict = _normalize_choice(primary_verdict, allowed=PRIMARY_VERDICTS, field_name="primary_verdict")
    if verdict == "ready":
        return NextSafeAction(
            label="Review readiness summary",
            destination="Boot Status",
            reason="Preflight checks report a usable research-review state.",
        )
    if verdict == "degraded":
        return NextSafeAction(
            label="Inspect readiness diagnostics",
            destination="Boot Status",
            reason="One or more checks are advisory, deferred, or limited.",
        )
    return NextSafeAction(
        label="Open boot diagnostics",
        destination="Boot Status",
        reason="One or more checks block normal research review.",
    )


def make_boot_status(
    *,
    source: str,
    flags: BootContextFlags,
    checks: Sequence[ReadinessCheck],
    generated_at: str | None = None,
    next_safe_action: NextSafeAction | None = None,
    artifact_id: str | None = None,
    git_commit: str | None = None,
    local_context_id: str | None = None,
    warnings: Sequence[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> BootStatus:
    check_tuple = tuple(checks) or (
        ReadinessCheck(
            id="boot_status.no_checks",
            label="Boot status checks unavailable",
            status="fail",
            severity="blocked",
            summary="No trusted readiness checks were produced.",
            destination="Boot Status",
        ),
    )
    primary = primary_verdict_from_checks(check_tuple, flags)
    return BootStatus(
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at or _utc_now(),
        source=source,
        primary_verdict=primary,
        flags=flags,
        checks=check_tuple,
        next_safe_action=next_safe_action or next_safe_action_for_verdict(primary),
        artifact_id=artifact_id,
        git_commit=git_commit,
        local_context_id=local_context_id,
        warnings=tuple(warnings),
        metadata=metadata or {},
    )


def deferred_check(check_id: str, label: str, summary: str, *, destination: str = "Boot Status") -> ReadinessCheck:
    return ReadinessCheck(
        id=check_id,
        label=label,
        status="deferred",
        severity="degraded",
        summary=summary,
        destination=destination,
    )


def status_json_text(status: BootStatus | Mapping[str, Any]) -> str:
    parsed = status if isinstance(status, BootStatus) else BootStatus.from_json_dict(status)
    return parsed.to_json_text()


def _resolve_boot_status_target(path: str | Path, repo_root: str | Path | None) -> Path:
    target = Path(path)
    allowed_paths = {DEFAULT_BOOT_STATUS_PATH.as_posix(), LEGACY_BOOT_STATUS_PATH.as_posix()}
    if repo_root is None:
        if target.is_absolute() or target.as_posix() not in allowed_paths:
            raise BootStatusValidationError(
                f"boot status output must be {DEFAULT_BOOT_STATUS_PATH.as_posix()}"
            )
        return target
    repo = Path(repo_root).resolve()
    resolved = target if target.is_absolute() else repo / target
    try:
        relative = resolved.resolve().relative_to(repo).as_posix()
    except ValueError as exc:
        raise BootStatusValidationError("boot status output must stay inside repository") from exc
    if relative not in allowed_paths:
        raise BootStatusValidationError(
            f"boot status output must be {DEFAULT_BOOT_STATUS_PATH.as_posix()}; got {relative}"
        )
    return resolved


def write_boot_status_file(
    status: BootStatus | Mapping[str, Any],
    path: str | Path = DEFAULT_BOOT_STATUS_PATH,
    *,
    repo_root: str | Path | None = None,
) -> str:
    target = _resolve_boot_status_target(path, repo_root)
    parsed = status if isinstance(status, BootStatus) else BootStatus.from_json_dict(status)
    text = parsed.to_json_text()
    existing = target.read_text(encoding="utf-8") if target.exists() else None
    if existing == text:
        return "unchanged"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp_path, target)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return "written"


def blocked_boot_status(reason: str, *, path: Path | None = None) -> BootStatus:
    path_detail = path.as_posix() if path is not None else DEFAULT_BOOT_STATUS_PATH.as_posix()
    return make_boot_status(
        source="core.boot_status.load_boot_status_fail_closed",
        flags=BootContextFlags(safe_boot=False),
        checks=(
            ReadinessCheck(
                id="boot_status_artifact",
                label="Boot status artifact",
                status="fail",
                severity="blocked",
                summary=reason,
                evidence_ref=path_detail,
                destination="Boot Status",
            ),
        ),
        metadata={"path": path_detail},
    )


def _load_boot_status_path(path: Path, *, source_role: str) -> BootStatus:
    target = path
    if not target.exists():
        return blocked_boot_status("Boot status artifact is missing.", path=target)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise BootStatusValidationError("Boot status artifact must be a JSON object")
        status = BootStatus.from_json_dict(payload)
    except Exception as exc:
        return blocked_boot_status(f"Boot status artifact is invalid: {exc}", path=target)
    metadata = dict(status.metadata)
    metadata["loaded_from"] = target.as_posix()
    metadata["source_role"] = source_role
    return BootStatus(
        schema_version=status.schema_version,
        generated_at=status.generated_at,
        source=status.source,
        primary_verdict=status.primary_verdict,
        flags=status.flags,
        checks=status.checks,
        next_safe_action=status.next_safe_action,
        artifact_id=status.artifact_id,
        git_commit=status.git_commit,
        local_context_id=status.local_context_id,
        warnings=status.warnings,
        metadata=metadata,
    )


def load_boot_status_fail_closed(path: str | Path | None = None) -> BootStatus:
    if path is not None:
        return _load_boot_status_path(Path(path), source_role="explicit")
    if DEFAULT_BOOT_STATUS_PATH.exists():
        return _load_boot_status_path(DEFAULT_BOOT_STATUS_PATH, source_role="canonical")
    if LEGACY_BOOT_STATUS_PATH.exists():
        return _load_boot_status_path(LEGACY_BOOT_STATUS_PATH, source_role="legacy")
    return blocked_boot_status("Boot status artifact is missing.", path=DEFAULT_BOOT_STATUS_PATH)
