from __future__ import annotations

import csv
import json
import math
from datetime import date
from pathlib import Path

import pytest

from data.provenance import compute_sha256


FRED_FIXTURE = Path("data/fixtures/fred/fred_macro_tiny.csv")
FRED_MANIFEST = Path("data/fixtures/fred/fred_macro_tiny.manifest.json")
KEN_FRENCH_FIXTURE = Path("data/fixtures/ken_french/ken_french_factor_tiny.csv")
KEN_FRENCH_MANIFEST = Path("data/fixtures/ken_french/ken_french_factor_tiny.manifest.json")

FRED_REQUIRED_MANIFEST_FIELDS = {
    "source_name",
    "source_quality",
    "provider",
    "provider_feed",
    "dataset_type",
    "observed_estimated_or_inferred",
    "series_id",
    "date_range",
    "row_count",
    "sha256",
    "schema_version",
    "official_source_url",
    "terms_note",
    "api_key_required",
    "retrieved_at_or_static_fixture_created_at",
    "asof_ts",
    "allowed_use",
    "forbidden_use",
}

KEN_FRENCH_REQUIRED_MANIFEST_FIELDS = {
    "source_name",
    "source_quality",
    "provider",
    "provider_feed",
    "dataset_type",
    "observed_estimated_or_inferred",
    "dataset_id",
    "date_range",
    "row_count",
    "sha256",
    "schema_version",
    "official_source_url",
    "terms_note",
    "retrieved_at_or_static_fixture_created_at",
    "asof_ts",
    "allowed_use",
    "forbidden_use",
}

FORBIDDEN_SCORE_COLUMNS = {
    "macro_regime_score",
    "factor_regime_score",
    "signal_rank",
    "candidate_rank",
    "alert",
    "state_machine_state",
}


class MacroFactorTinyFixtureError(RuntimeError):
    pass


def _manifest_path(fixture_path: Path) -> Path:
    if fixture_path == FRED_FIXTURE:
        return FRED_MANIFEST
    if fixture_path == KEN_FRENCH_FIXTURE:
        return KEN_FRENCH_MANIFEST
    return fixture_path.with_name(f"{fixture_path.stem}.manifest.json")


def _read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _parse_iso_date(value: str, *, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise MacroFactorTinyFixtureError(f"{field} must parse as ISO date: {value!r}") from exc


def _finite_numeric(value: str, *, field: str) -> None:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise MacroFactorTinyFixtureError(f"{field} must be numeric: {value!r}") from exc
    if not math.isfinite(parsed):
        raise MacroFactorTinyFixtureError(f"{field} must be finite")


def _require_date_range_reconciles(manifest: dict, rows: list[dict[str, str]]) -> None:
    row_dates = sorted(_parse_iso_date(row["date"], field="date") for row in rows)
    expected_start = row_dates[0].isoformat()
    expected_end = row_dates[-1].isoformat()
    if manifest["date_range"]["start"] != expected_start:
        raise MacroFactorTinyFixtureError("date_range start mismatch")
    if manifest["date_range"]["end"] != expected_end:
        raise MacroFactorTinyFixtureError("date_range end mismatch")


def _require_common_manifest_fields(
    *,
    manifest: dict,
    fixture_path: Path,
    rows: list[dict[str, str]],
    required_fields: set[str],
) -> None:
    missing = sorted(required_fields - set(manifest))
    if missing:
        raise MacroFactorTinyFixtureError("manifest missing required fields: " + ", ".join(missing))
    if manifest["row_count"] != len(rows):
        raise MacroFactorTinyFixtureError("row_count mismatch")
    if manifest["sha256"] != compute_sha256(fixture_path):
        raise MacroFactorTinyFixtureError("sha256 mismatch")
    if manifest["observed_estimated_or_inferred"] != "observed":
        raise MacroFactorTinyFixtureError("observed_estimated_or_inferred must be observed")
    if not manifest["source_quality"]:
        raise MacroFactorTinyFixtureError("source_quality is required")
    if not manifest["allowed_use"] or not manifest["forbidden_use"]:
        raise MacroFactorTinyFixtureError("allowed_use and forbidden_use are required")
    _parse_iso_date(manifest["retrieved_at_or_static_fixture_created_at"], field="retrieved_at_or_static_fixture_created_at")
    _parse_iso_date(manifest["asof_ts"], field="asof_ts")
    _parse_iso_date(manifest["date_range"]["start"], field="date_range.start")
    _parse_iso_date(manifest["date_range"]["end"], field="date_range.end")
    _require_date_range_reconciles(manifest, rows)


def _validate_fred_manifest(manifest: dict, fixture_path: Path, rows: list[dict[str, str]]) -> None:
    _require_common_manifest_fields(
        manifest=manifest,
        fixture_path=fixture_path,
        rows=rows,
        required_fields=FRED_REQUIRED_MANIFEST_FIELDS,
    )
    if manifest["source_name"] != "FRED / ALFRED":
        raise MacroFactorTinyFixtureError("source_name must identify FRED / ALFRED")
    if manifest["source_quality"] != "public_official_observed":
        raise MacroFactorTinyFixtureError("source_quality must be public_official_observed")
    if manifest["provider"] != "fred":
        raise MacroFactorTinyFixtureError("provider must be fred")
    if manifest["provider_feed"] != "fred_or_alfred":
        raise MacroFactorTinyFixtureError("provider_feed must be fred_or_alfred")
    if manifest["dataset_type"] != "macro_series":
        raise MacroFactorTinyFixtureError("dataset_type must be macro_series")
    if manifest["api_key_required"] != "true_for_live_api":
        raise MacroFactorTinyFixtureError("api_key_required must be true_for_live_api")
    if not str(manifest["official_source_url"]).startswith("https://fred.stlouisfed.org/"):
        raise MacroFactorTinyFixtureError("official_source_url must point to FRED")


def _validate_ken_french_manifest(
    manifest: dict, fixture_path: Path, rows: list[dict[str, str]]
) -> None:
    _require_common_manifest_fields(
        manifest=manifest,
        fixture_path=fixture_path,
        rows=rows,
        required_fields=KEN_FRENCH_REQUIRED_MANIFEST_FIELDS,
    )
    if manifest["source_name"] != "Kenneth French Data Library":
        raise MacroFactorTinyFixtureError("source_name must identify Kenneth French Data Library")
    if manifest["source_quality"] != "public_research_observed":
        raise MacroFactorTinyFixtureError("source_quality must be public_research_observed")
    if manifest["provider"] != "ken_french":
        raise MacroFactorTinyFixtureError("provider must be ken_french")
    if manifest["provider_feed"] != "data_library":
        raise MacroFactorTinyFixtureError("provider_feed must be data_library")
    if manifest["dataset_type"] != "factor_returns":
        raise MacroFactorTinyFixtureError("dataset_type must be factor_returns")
    if not str(manifest["official_source_url"]).startswith(
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/"
    ):
        raise MacroFactorTinyFixtureError("official_source_url must point to Ken French Data Library")


def _validate_fred_rows(manifest: dict, rows: list[dict[str, str]]) -> None:
    expected_columns = manifest["schema_columns"]
    seen: set[tuple[str, str, str, str]] = set()

    for row in rows:
        if list(row.keys()) != expected_columns:
            raise MacroFactorTinyFixtureError("schema column mismatch")
        if FORBIDDEN_SCORE_COLUMNS.intersection(row):
            raise MacroFactorTinyFixtureError("score/runtime fields must not appear")
        series_id = row["series_id"].strip()
        if not series_id:
            raise MacroFactorTinyFixtureError("series_id is required")
        _parse_iso_date(row["date"], field="date")
        _parse_iso_date(row["realtime_start"], field="realtime_start")
        _parse_iso_date(row["realtime_end"], field="realtime_end")
        _parse_iso_date(row["asof_ts"], field="asof_ts")
        primary_key = (series_id, row["date"], row["realtime_start"], row["realtime_end"])
        if primary_key in seen:
            raise MacroFactorTinyFixtureError("duplicate primary key")
        seen.add(primary_key)
        _finite_numeric(row["value"], field="value")


def _validate_ken_french_rows(manifest: dict, rows: list[dict[str, str]]) -> None:
    expected_columns = manifest["schema_columns"]
    seen: set[tuple[str, str, str]] = set()

    for row in rows:
        if list(row.keys()) != expected_columns:
            raise MacroFactorTinyFixtureError("schema column mismatch")
        if FORBIDDEN_SCORE_COLUMNS.intersection(row):
            raise MacroFactorTinyFixtureError("score/runtime fields must not appear")
        dataset_id = row["dataset_id"].strip()
        factor_name = row["factor_name"].strip()
        if not dataset_id:
            raise MacroFactorTinyFixtureError("dataset_id is required")
        if not factor_name:
            raise MacroFactorTinyFixtureError("factor_name is required")
        if row["frequency"] != "monthly":
            raise MacroFactorTinyFixtureError("frequency must be monthly")
        _parse_iso_date(row["date"], field="date")
        _parse_iso_date(row["asof_ts"], field="asof_ts")
        primary_key = (dataset_id, row["date"], factor_name)
        if primary_key in seen:
            raise MacroFactorTinyFixtureError("duplicate primary key")
        seen.add(primary_key)
        _finite_numeric(row["factor_return"], field="factor_return")


def _validate_fred_fixture(fixture_path: Path = FRED_FIXTURE) -> None:
    manifest_path = _manifest_path(fixture_path)
    if not manifest_path.exists():
        raise MacroFactorTinyFixtureError("manifest is required")
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(manifest_path)
    _validate_fred_manifest(manifest, fixture_path, rows)
    _validate_fred_rows(manifest, rows)


def _validate_ken_french_fixture(fixture_path: Path = KEN_FRENCH_FIXTURE) -> None:
    manifest_path = _manifest_path(fixture_path)
    if not manifest_path.exists():
        raise MacroFactorTinyFixtureError("manifest is required")
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(manifest_path)
    _validate_ken_french_manifest(manifest, fixture_path, rows)
    _validate_ken_french_rows(manifest, rows)


def _copy_pair(tmp_path: Path, fixture_path: Path) -> Path:
    target = tmp_path / fixture_path.name
    target.write_bytes(fixture_path.read_bytes())
    manifest_target = _manifest_path(target)
    manifest_target.write_text(_manifest_path(fixture_path).read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _rewrite_pair(fixture_path: Path, rows: list[dict[str, object]], manifest: dict) -> None:
    _write_rows(fixture_path, rows, list(rows[0].keys()))
    manifest["sha256"] = compute_sha256(fixture_path)
    manifest["row_count"] = len(rows)
    _write_manifest(_manifest_path(fixture_path), manifest)


def test_g7_1g_fred_and_ken_french_fixtures_validate():
    _validate_fred_fixture()
    _validate_ken_french_fixture()


def test_g7_1g_manifests_exist():
    assert FRED_MANIFEST.exists()
    assert KEN_FRENCH_MANIFEST.exists()


def test_g7_1g_rejects_manifest_hash_mismatch(tmp_path):
    fixture_path = _copy_pair(tmp_path, FRED_FIXTURE)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_manifest(manifest_path)
    manifest["sha256"] = "0" * 64
    _write_manifest(manifest_path, manifest)

    with pytest.raises(MacroFactorTinyFixtureError, match="sha256 mismatch"):
        _validate_fred_fixture(fixture_path)


def test_g7_1g_rejects_row_count_and_date_range_mismatch(tmp_path):
    fixture_path = _copy_pair(tmp_path, KEN_FRENCH_FIXTURE)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_manifest(manifest_path)
    manifest["row_count"] = manifest["row_count"] + 1
    _write_manifest(manifest_path, manifest)

    with pytest.raises(MacroFactorTinyFixtureError, match="row_count mismatch"):
        _validate_ken_french_fixture(fixture_path)

    manifest = _read_manifest(manifest_path)
    manifest["row_count"] = 12
    manifest["date_range"]["start"] = "1926-01-31"
    _write_manifest(manifest_path, manifest)

    with pytest.raises(MacroFactorTinyFixtureError, match="date_range start mismatch"):
        _validate_ken_french_fixture(fixture_path)


def test_g7_1g_rejects_duplicate_primary_keys(tmp_path):
    fixture_path = _copy_pair(tmp_path, FRED_FIXTURE)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows.append(dict(rows[0]))
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(MacroFactorTinyFixtureError, match="duplicate primary key"):
        _validate_fred_fixture(fixture_path)

    fixture_path = _copy_pair(tmp_path, KEN_FRENCH_FIXTURE)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows.append(dict(rows[0]))
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(MacroFactorTinyFixtureError, match="duplicate primary key"):
        _validate_ken_french_fixture(fixture_path)


def test_g7_1g_rejects_non_finite_numeric_values(tmp_path):
    fixture_path = _copy_pair(tmp_path, FRED_FIXTURE)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows[0]["value"] = "nan"
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(MacroFactorTinyFixtureError, match="value"):
        _validate_fred_fixture(fixture_path)

    fixture_path = _copy_pair(tmp_path, KEN_FRENCH_FIXTURE)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows[0]["factor_return"] = "inf"
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(MacroFactorTinyFixtureError, match="factor_return"):
        _validate_ken_french_fixture(fixture_path)


def test_g7_1g_requires_source_quality_allowed_use_observed_label_and_key_policy(tmp_path):
    fixture_path = _copy_pair(tmp_path, FRED_FIXTURE)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_manifest(manifest_path)

    manifest["source_quality"] = ""
    _write_manifest(manifest_path, manifest)
    with pytest.raises(MacroFactorTinyFixtureError, match="source_quality"):
        _validate_fred_fixture(fixture_path)

    manifest = _read_manifest(manifest_path)
    manifest["source_quality"] = "public_official_observed"
    manifest["allowed_use"] = []
    _write_manifest(manifest_path, manifest)
    with pytest.raises(MacroFactorTinyFixtureError, match="allowed_use"):
        _validate_fred_fixture(fixture_path)

    manifest = _read_manifest(manifest_path)
    manifest["allowed_use"] = ["macro context"]
    manifest["observed_estimated_or_inferred"] = "estimated"
    _write_manifest(manifest_path, manifest)
    with pytest.raises(MacroFactorTinyFixtureError, match="must be observed"):
        _validate_fred_fixture(fixture_path)

    manifest = _read_manifest(manifest_path)
    manifest["observed_estimated_or_inferred"] = "observed"
    manifest["api_key_required"] = "false"
    _write_manifest(manifest_path, manifest)
    with pytest.raises(MacroFactorTinyFixtureError, match="api_key_required"):
        _validate_fred_fixture(fixture_path)


def test_g7_1g_rejects_score_runtime_columns_and_missing_ids(tmp_path):
    fixture_path = _copy_pair(tmp_path, FRED_FIXTURE)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    for row in rows:
        row["macro_regime_score"] = "1"
    manifest["schema_columns"].append("macro_regime_score")
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(MacroFactorTinyFixtureError, match="score/runtime fields"):
        _validate_fred_fixture(fixture_path)

    fixture_path = _copy_pair(tmp_path, KEN_FRENCH_FIXTURE)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows[0]["dataset_id"] = ""
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(MacroFactorTinyFixtureError, match="dataset_id"):
        _validate_ken_french_fixture(fixture_path)
