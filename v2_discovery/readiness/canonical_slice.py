from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import compute_sha256
from data.provenance import load_manifest
from v2_discovery.readiness.schemas import G4_DEFAULT_DATASET_NAME
from v2_discovery.readiness.schemas import G4_NUMERIC_COLUMNS
from v2_discovery.readiness.schemas import G4_PRICE_COLUMNS
from v2_discovery.readiness.schemas import G4_PRIMARY_KEY
from v2_discovery.readiness.schemas import G4_REQUIRED_COLUMNS
from v2_discovery.readiness.schemas import G4_RETURN_COLUMNS
from v2_discovery.readiness.schemas import G4_RETURN_MAX_INCLUSIVE
from v2_discovery.readiness.schemas import G4_RETURN_MIN_EXCLUSIVE
from v2_discovery.readiness.schemas import G4_SCHEMA_VERSION
from v2_discovery.readiness.schemas import G4_SOURCE_TIER
from v2_discovery.readiness.schemas import G4CanonicalSlice
from v2_discovery.readiness.schemas import G4ReadinessError


G4_DEFAULT_ARTIFACT_URI = Path("data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet")
G4_DEFAULT_MANIFEST_URI = Path(f"{G4_DEFAULT_ARTIFACT_URI}.manifest.json")
G4_FRESHNESS_CUTOFF_DATE = pd.Timestamp("2024-01-01")

_FORBIDDEN_PROVIDER_TOKENS = frozenset(
    {
        "al" "paca",
        "iex",
        "openbb",
        "public_web",
        "web_scrape",
        "yahoo",
        "yfinance",
    }
)


def load_g4_canonical_slice(
    *,
    artifact_uri: str | Path = G4_DEFAULT_ARTIFACT_URI,
    manifest_uri: str | Path = G4_DEFAULT_MANIFEST_URI,
    dataset_name: str = G4_DEFAULT_DATASET_NAME,
    repo_root: str | Path | None = None,
    freshness_cutoff_date: str | pd.Timestamp | None = G4_FRESHNESS_CUTOFF_DATE,
) -> G4CanonicalSlice:
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    artifact_path = _resolve_path(root, artifact_uri)
    manifest_path = _resolve_path(root, manifest_uri)
    if not manifest_path.exists():
        raise G4ReadinessError("G4 requires a manifest")
    if not artifact_path.exists():
        raise G4ReadinessError(f"G4 artifact does not exist: {artifact_uri}")

    try:
        manifest = load_manifest(manifest_path)
    except Exception as exc:
        raise G4ReadinessError(f"G4 manifest failed validation: {exc}") from exc
    _validate_manifest_contract(
        manifest,
        artifact_path=artifact_path,
        manifest_uri=manifest_uri,
        dataset_name=dataset_name,
    )
    try:
        data = pd.read_parquet(artifact_path)
    except Exception as exc:
        raise G4ReadinessError(f"G4 cannot read canonical parquet slice: {exc}") from exc
    _validate_slice_data(
        data,
        manifest,
        freshness_cutoff_date=freshness_cutoff_date,
    )
    return G4CanonicalSlice(
        dataset_name=dataset_name,
        artifact_uri=_relative_or_absolute(root, artifact_path),
        manifest_uri=_relative_or_absolute(root, manifest_path),
        artifact_path=artifact_path,
        manifest_path=manifest_path,
        manifest=dict(manifest),
        data=data.copy(),
    )


def validate_sidecar_manifest_if_required(
    *,
    primary_date_end: str,
    sidecar_required: bool,
    sidecar_manifest_uri: str | Path | None,
    repo_root: str | Path | None = None,
) -> str:
    if not sidecar_required:
        return "pass"
    if sidecar_manifest_uri is None:
        raise G4ReadinessError("G4 sidecar_required=true requires a sidecar manifest")
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    sidecar_manifest_path = _resolve_path(root, sidecar_manifest_uri)
    if not sidecar_manifest_path.exists():
        raise G4ReadinessError("G4 required sidecar manifest does not exist")
    try:
        sidecar_manifest = load_manifest(sidecar_manifest_path)
    except Exception as exc:
        raise G4ReadinessError(f"G4 sidecar manifest failed validation: {exc}") from exc
    _validate_source_is_tier0(sidecar_manifest)
    sidecar_end = _date_range(sidecar_manifest).get("end")
    if sidecar_end is None:
        raise G4ReadinessError("G4 required sidecar has ambiguous date_range.end")
    if pd.Timestamp(sidecar_end) < pd.Timestamp(primary_date_end):
        raise G4ReadinessError("G4 required sidecar is stale")
    return "pass"


def _validate_manifest_contract(
    manifest: Mapping[str, Any],
    *,
    artifact_path: Path,
    manifest_uri: str | Path,
    dataset_name: str,
) -> None:
    _validate_source_is_tier0(manifest)
    declared_path = str(manifest.get("artifact_path") or "").strip()
    if declared_path and Path(declared_path) != artifact_path:
        raise G4ReadinessError("G4 manifest artifact_path mismatch")
    if str(manifest.get("schema_version") or "").strip() != G4_SCHEMA_VERSION:
        raise G4ReadinessError("G4 schema_version mismatch")
    if str(_extra(manifest).get("dataset_name") or "").strip() != dataset_name:
        raise G4ReadinessError("G4 manifest dataset_name mismatch")
    if tuple(_extra(manifest).get("primary_key") or ()) != G4_PRIMARY_KEY:
        raise G4ReadinessError("G4 manifest primary_key mismatch")
    expected_schema = _schema_columns(manifest)
    if expected_schema is None:
        raise G4ReadinessError("G4 manifest schema is required")
    if tuple(expected_schema) != G4_REQUIRED_COLUMNS:
        raise G4ReadinessError("G4 manifest schema mismatch")
    expected_hash = str(manifest.get("sha256") or "").strip()
    if expected_hash != compute_sha256(artifact_path):
        raise G4ReadinessError("G4 manifest hash mismatch")
    if not str(manifest_uri).strip():
        raise G4ReadinessError("G4 manifest_uri is required")


def _validate_source_is_tier0(manifest: Mapping[str, Any]) -> None:
    if manifest.get("source_quality") != SOURCE_QUALITY_CANONICAL:
        raise G4ReadinessError("G4 requires Tier 0 canonical source_quality")
    tier = str(_extra(manifest).get("source_tier") or "").strip().lower()
    if tier != G4_SOURCE_TIER:
        raise G4ReadinessError("G4 requires source_tier=tier0")
    provider = str(manifest.get("provider") or "").strip().lower()
    provider_feed = str(manifest.get("provider_feed") or "").strip().lower()
    joined = f"{provider} {provider_feed}"
    if any(token in joined for token in _FORBIDDEN_PROVIDER_TOKENS):
        raise G4ReadinessError("G4 rejects non-canonical provider artifacts")


def _validate_slice_data(
    data: pd.DataFrame,
    manifest: Mapping[str, Any],
    *,
    freshness_cutoff_date: str | pd.Timestamp | None,
) -> None:
    if data.empty:
        raise G4ReadinessError("G4 canonical slice must be non-empty")
    _validate_required_columns(data)
    _validate_manifest_row_count(data, manifest)
    _validate_manifest_schema(data, manifest)
    _validate_dates(data, manifest, freshness_cutoff_date=freshness_cutoff_date)
    _validate_finite_numeric(data)
    _validate_duplicate_primary_keys(data)
    _validate_date_monotonicity(data)
    _validate_price_domain(data)
    _validate_return_domain(data)


def _validate_required_columns(data: pd.DataFrame) -> None:
    missing = [column for column in G4_REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise G4ReadinessError("G4 slice missing required column(s): " + ", ".join(missing))


def _validate_manifest_row_count(data: pd.DataFrame, manifest: Mapping[str, Any]) -> None:
    if int(manifest.get("row_count")) != int(len(data)):
        raise G4ReadinessError("G4 manifest row_count mismatch")


def _validate_manifest_schema(data: pd.DataFrame, manifest: Mapping[str, Any]) -> None:
    expected = _schema_columns(manifest)
    if expected != list(data.columns):
        raise G4ReadinessError("G4 manifest schema mismatch")


def _validate_dates(
    data: pd.DataFrame,
    manifest: Mapping[str, Any],
    *,
    freshness_cutoff_date: str | pd.Timestamp | None,
) -> None:
    dates = pd.to_datetime(data["date"], errors="coerce")
    if dates.isna().any():
        raise G4ReadinessError("G4 date column contains invalid dates")
    actual = {
        "start": dates.min().strftime("%Y-%m-%d"),
        "end": dates.max().strftime("%Y-%m-%d"),
    }
    expected = _date_range(manifest)
    if expected != actual:
        raise G4ReadinessError("G4 manifest date_range mismatch")
    if freshness_cutoff_date is not None and pd.Timestamp(actual["end"]) < pd.Timestamp(freshness_cutoff_date):
        raise G4ReadinessError("G4 freshness_check failed")


def _validate_finite_numeric(data: pd.DataFrame) -> None:
    for column in G4_NUMERIC_COLUMNS:
        values = pd.to_numeric(data[column], errors="coerce").to_numpy(dtype="float64", na_value=np.nan)
        if not np.isfinite(values).all():
            raise G4ReadinessError("G4 finite_numeric_check failed")


def _validate_duplicate_primary_keys(data: pd.DataFrame) -> None:
    if data.duplicated(list(G4_PRIMARY_KEY)).any():
        raise G4ReadinessError("G4 duplicate_key_check failed")


def _validate_date_monotonicity(data: pd.DataFrame) -> None:
    framed = data.assign(_g4_date=pd.to_datetime(data["date"], errors="coerce"))
    for _, group in framed.groupby("permno", sort=False):
        if not group["_g4_date"].is_monotonic_increasing:
            raise G4ReadinessError("G4 date_monotonicity_check failed")


def _validate_price_domain(data: pd.DataFrame) -> None:
    for column in G4_PRICE_COLUMNS:
        values = pd.to_numeric(data[column], errors="coerce")
        if (values <= 0).any():
            raise G4ReadinessError("G4 price_domain_check failed")
    volume = pd.to_numeric(data["volume"], errors="coerce")
    if (volume < 0).any():
        raise G4ReadinessError("G4 price_domain_check failed")


def _validate_return_domain(data: pd.DataFrame) -> None:
    for column in G4_RETURN_COLUMNS:
        values = pd.to_numeric(data[column], errors="coerce")
        bad = (values <= G4_RETURN_MIN_EXCLUSIVE) | (values > G4_RETURN_MAX_INCLUSIVE)
        if bad.any():
            raise G4ReadinessError("G4 return_domain_check failed")


def _schema_columns(manifest: Mapping[str, Any]) -> list[str] | None:
    schema = manifest.get("schema")
    if isinstance(schema, Mapping) and isinstance(schema.get("columns"), list):
        return [str(column) for column in schema["columns"]]
    schema_columns = manifest.get("schema_columns")
    if isinstance(schema_columns, list):
        return [str(column) for column in schema_columns]
    return None


def _date_range(manifest: Mapping[str, Any]) -> dict[str, str | None]:
    value = manifest.get("date_range")
    if not isinstance(value, Mapping):
        raise G4ReadinessError("G4 manifest date_range is required")
    start = value.get("start")
    end = value.get("end")
    return {
        "start": str(start) if start is not None else None,
        "end": str(end) if end is not None else None,
    }


def _extra(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    extra = manifest.get("extra")
    if not isinstance(extra, Mapping):
        raise G4ReadinessError("G4 manifest extra metadata is required")
    return extra


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _relative_or_absolute(root: Path, value: Path) -> str:
    try:
        return value.relative_to(root).as_posix()
    except ValueError:
        return str(value)
