from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


G4_SCHEMA_VERSION = "1.0.0"
G4_REPORT_SCHEMA_VERSION = "1.0.0"
G4_READINESS_RUN_ID = "PH65_G4_REAL_CANONICAL_READINESS_001"
G4_CODE_REF = "v2_discovery/readiness/canonical_readiness.py@phase65-g4"
G4_DEFAULT_DATASET_NAME = "prices_tri_real_canonical_tiny_slice"
G4_REPORT_PROVIDER_FEED = "g4_real_canonical_readiness_report"

G4_PRIMARY_KEY = ("date", "permno")
G4_PRICE_COLUMNS = ("tri", "legacy_adj_close", "raw_close")
G4_RETURN_COLUMNS = ("total_ret",)
G4_NUMERIC_COLUMNS = (
    "permno",
    "tri",
    "total_ret",
    "legacy_adj_close",
    "raw_close",
    "volume",
)
G4_REQUIRED_COLUMNS = (
    "date",
    "permno",
    "ticker",
    "tri",
    "total_ret",
    "legacy_adj_close",
    "raw_close",
    "volume",
)

G4_SOURCE_TIER = "tier0"
G4_RETURN_MIN_EXCLUSIVE = -1.0
G4_RETURN_MAX_INCLUSIVE = 10.0


class G4ReadinessError(RuntimeError):
    """Raised when a G4 canonical readiness gate is violated."""


@dataclass(frozen=True)
class G4CanonicalSlice:
    dataset_name: str
    artifact_uri: str
    manifest_uri: str
    artifact_path: Path
    manifest_path: Path
    manifest: dict[str, Any]
    data: Any


@dataclass(frozen=True)
class G4ReadinessRun:
    report: dict[str, Any]
    slice: G4CanonicalSlice
    report_path: Path | None = None
    report_manifest_path: Path | None = None
