from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MANIFEST_SCHEMA_VERSION = "1.0.0"

SOURCE_QUALITY_CANONICAL = "canonical"
SOURCE_QUALITY_OPERATIONAL = "operational"
SOURCE_QUALITY_NON_CANONICAL = "non_canonical"
SOURCE_QUALITY_REJECTED = "rejected"

SOURCE_QUALITIES = frozenset(
    {
        SOURCE_QUALITY_CANONICAL,
        SOURCE_QUALITY_OPERATIONAL,
        SOURCE_QUALITY_NON_CANONICAL,
        SOURCE_QUALITY_REJECTED,
    }
)
PROMOTION_ALLOWED_SOURCE_QUALITIES = frozenset({SOURCE_QUALITY_CANONICAL})

REQUIRED_MANIFEST_FIELDS = (
    "manifest_schema_version",
    "schema_version",
    "source_quality",
    "provider",
    "provider_feed",
    "asof_ts",
    "license_scope",
    "row_count",
    "date_range",
    "sha256",
)


class ProvenanceError(RuntimeError):
    """Raised when an artifact cannot pass provenance policy."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "null", "nan"}:
        return ""
    return text


def _normalize_quality(value: Any) -> str:
    quality = _clean_text(value).lower()
    if quality not in SOURCE_QUALITIES:
        raise ProvenanceError(f"Invalid source_quality: {value!r}")
    return quality


def _normalize_date_range(value: Any) -> dict[str, str | None]:
    if isinstance(value, dict):
        start = value.get("start") or value.get("min") or value.get("from")
        end = value.get("end") or value.get("max") or value.get("to")
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        start, end = value
    elif value is None:
        start, end = None, None
    else:
        raise ProvenanceError("date_range must be a dict, a two-item sequence, or None")
    return {
        "start": _clean_text(start) or None,
        "end": _clean_text(end) or None,
    }


def compute_sha256(path: str | os.PathLike[str]) -> str:
    target = Path(path)
    if target.is_dir():
        file_paths = sorted(p for p in target.rglob("*") if p.is_file())
        digest = hashlib.sha256()
        for file_path in file_paths:
            rel = file_path.relative_to(target).as_posix().encode("utf-8")
            digest.update(rel)
            digest.update(b"\0")
            with file_path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        return digest.hexdigest()
    if not target.exists():
        raise FileNotFoundError(f"Cannot hash missing artifact: {target}")

    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_path_for(artifact_path: str | os.PathLike[str]) -> Path:
    return Path(f"{Path(artifact_path)}.manifest.json")


def write_json_atomic(payload: dict[str, Any], path: str | os.PathLike[str]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


@dataclass(frozen=True)
class ManifestInput:
    artifact_path: str | os.PathLike[str]
    source_quality: str
    provider: str
    provider_feed: str
    license_scope: str
    row_count: int
    date_range: dict[str, str | None] | tuple[Any, Any] | list[Any] | None
    schema_version: str = "1.0.0"
    asof_ts: str | None = None
    extra: dict[str, Any] | None = None


def build_manifest(config: ManifestInput) -> dict[str, Any]:
    artifact_path = Path(config.artifact_path)
    quality = _normalize_quality(config.source_quality)
    row_count = int(config.row_count)
    if row_count < 0:
        raise ProvenanceError("row_count must be >= 0")

    provider = _clean_text(config.provider)
    provider_feed = _clean_text(config.provider_feed)
    license_scope = _clean_text(config.license_scope)
    schema_version = _clean_text(config.schema_version)
    if not provider:
        raise ProvenanceError("provider is required")
    if not provider_feed:
        raise ProvenanceError("provider_feed is required")
    if not license_scope:
        raise ProvenanceError("license_scope is required")
    if not schema_version:
        raise ProvenanceError("schema_version is required")

    manifest: dict[str, Any] = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "schema_version": schema_version,
        "artifact_path": str(artifact_path),
        "source_quality": quality,
        "provider": provider,
        "provider_feed": provider_feed,
        "asof_ts": _clean_text(config.asof_ts) or utc_now_iso(),
        "license_scope": license_scope,
        "row_count": row_count,
        "date_range": _normalize_date_range(config.date_range),
        "sha256": compute_sha256(artifact_path),
        "manifest_created_at_utc": utc_now_iso(),
    }
    if config.extra:
        manifest["extra"] = dict(config.extra)
    validate_manifest(manifest)
    return manifest


def write_manifest(
    manifest: dict[str, Any],
    manifest_path: str | os.PathLike[str] | None = None,
    *,
    artifact_path: str | os.PathLike[str] | None = None,
) -> Path:
    validate_manifest(manifest)
    target = Path(manifest_path) if manifest_path is not None else manifest_path_for(
        artifact_path or manifest["artifact_path"]
    )
    write_json_atomic(manifest, target)
    return target


def load_manifest(path: str | os.PathLike[str]) -> dict[str, Any]:
    target = Path(path)
    with target.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ProvenanceError(f"Manifest must be a JSON object: {target}")
    validate_manifest(payload)
    return payload


def load_manifest_for_artifact(
    artifact_path: str | os.PathLike[str],
    manifest_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    target = Path(manifest_path) if manifest_path is not None else manifest_path_for(artifact_path)
    if not target.exists():
        raise ProvenanceError(f"Missing provenance manifest for artifact: {artifact_path}")
    manifest = load_manifest(target)
    declared = _clean_text(manifest.get("artifact_path"))
    if declared and Path(declared) != Path(artifact_path):
        raise ProvenanceError(
            f"Manifest artifact_path mismatch: manifest={declared} artifact={artifact_path}"
        )
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise ProvenanceError("manifest must be a dictionary")
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        raise ProvenanceError("Manifest missing required field(s): " + ", ".join(missing))

    _normalize_quality(manifest.get("source_quality"))
    for field in ("provider", "provider_feed", "asof_ts", "license_scope", "schema_version", "sha256"):
        if not _clean_text(manifest.get(field)):
            raise ProvenanceError(f"Manifest field {field} is required")
    try:
        row_count = int(manifest.get("row_count"))
    except (TypeError, ValueError):
        raise ProvenanceError("Manifest row_count must be an integer") from None
    if row_count < 0:
        raise ProvenanceError("Manifest row_count must be >= 0")
    _normalize_date_range(manifest.get("date_range"))


def require_source_quality(
    manifest: dict[str, Any],
    allowed: Iterable[str],
    *,
    context: str,
) -> None:
    validate_manifest(manifest)
    quality = _normalize_quality(manifest.get("source_quality"))
    allowed_set = {_normalize_quality(item) for item in allowed}
    if quality not in allowed_set:
        allowed_str = ", ".join(sorted(allowed_set))
        raise ProvenanceError(
            f"{context} requires source_quality in {{{allowed_str}}}; got {quality}"
        )


def assert_can_validate_artifact(
    artifact_path: str | os.PathLike[str],
    *,
    manifest_path: str | os.PathLike[str] | None = None,
    promotion_intent: bool = False,
) -> dict[str, Any]:
    manifest = load_manifest_for_artifact(artifact_path, manifest_path=manifest_path)
    if promotion_intent:
        require_source_quality(
            manifest,
            PROMOTION_ALLOWED_SOURCE_QUALITIES,
            context="V1 promotion validation",
        )
    return manifest


def assert_can_promote(packet: dict[str, Any]) -> None:
    if not isinstance(packet, dict):
        raise ProvenanceError("promotion packet must be a dictionary")

    manifests = packet.get("manifests")
    if manifests is None and "manifest" in packet:
        manifests = [packet["manifest"]]
    if manifests is None and "source_quality" in packet:
        quality = _normalize_quality(packet.get("source_quality"))
        if quality not in PROMOTION_ALLOWED_SOURCE_QUALITIES:
            raise ProvenanceError(f"Cannot promote packet from source_quality={quality}")
        return
    if not isinstance(manifests, list) or not manifests:
        raise ProvenanceError("promotion packet requires at least one source manifest")
    for manifest in manifests:
        if not isinstance(manifest, dict):
            raise ProvenanceError("promotion packet manifest entries must be objects")
        require_source_quality(
            manifest,
            PROMOTION_ALLOWED_SOURCE_QUALITIES,
            context="V1 promotion packet",
        )


def validate_alert_record(record: dict[str, Any]) -> None:
    if not isinstance(record, dict):
        raise ProvenanceError("alert record must be a dictionary")
    quality = _clean_text(record.get("source_quality")).lower()
    if not quality:
        raise ProvenanceError("Alert blocked: source_quality is required")
    _normalize_quality(quality)
    provider = _clean_text(record.get("provider"))
    provider_feed = _clean_text(record.get("provider_feed"))
    if not provider or not provider_feed:
        raise ProvenanceError("Alert blocked: provider and provider_feed are required")
    if quality == SOURCE_QUALITY_REJECTED:
        raise ProvenanceError("Alert blocked: rejected sources cannot emit alerts")


def validate_quote_snapshot(snapshot: dict[str, Any]) -> None:
    validate_alert_record(snapshot)
    if _clean_text(snapshot.get("provider")).lower() == "alpaca":
        feed = _clean_text(snapshot.get("provider_feed")).lower()
        quote_quality = _clean_text(snapshot.get("quote_quality")).lower()
        if feed == "iex" and quote_quality != "iex_only":
            raise ProvenanceError("Alpaca IEX quotes must be tagged quote_quality=iex_only")
        if feed in {"sip", "delayed_sip"} and quote_quality not in {
            "sip_quality",
            "delayed_sip_quality",
        }:
            raise ProvenanceError("Alpaca SIP/delayed SIP quotes must carry SIP-quality tags")

