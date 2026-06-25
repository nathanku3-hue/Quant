from __future__ import annotations

import json
import math
import re
from datetime import date
from pathlib import Path

import pytest

from data.provenance import compute_sha256


FIXTURE_DIR = Path("data/fixtures/sec")
COMPANYFACTS_FIXTURE = FIXTURE_DIR / "sec_companyfacts_tiny.json"
SUBMISSIONS_FIXTURE = FIXTURE_DIR / "sec_submissions_tiny.json"
SEC_FIXTURES = (COMPANYFACTS_FIXTURE, SUBMISSIONS_FIXTURE)

REQUIRED_MANIFEST_FIELDS = {
    "source_name",
    "source_quality",
    "provider",
    "provider_feed",
    "api_endpoint",
    "retrieved_at",
    "asof_ts",
    "entity_key_type",
    "cik",
    "ticker_if_known",
    "form_types",
    "row_count",
    "date_range",
    "sha256",
    "schema_version",
    "license_or_terms_note",
    "rate_limit_policy",
    "allowed_use",
    "forbidden_use",
    "observed_estimated_or_inferred",
}


class SecTinyFixtureError(RuntimeError):
    pass


def _manifest_path(fixture_path: Path) -> Path:
    return Path(f"{fixture_path}.manifest.json")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _records(payload: dict) -> list[dict]:
    fixture_type = payload.get("fixture_type")
    if fixture_type == "sec_companyfacts_tiny":
        return payload.get("facts", [])
    if fixture_type == "sec_submissions_tiny":
        return payload.get("filings", [])
    raise SecTinyFixtureError(f"unknown fixture_type: {fixture_type!r}")


def _parse_iso_date(value: str, *, field: str, allow_blank: bool = False) -> None:
    if value == "" and allow_blank:
        return
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise SecTinyFixtureError(f"{field} must parse as ISO date: {value!r}") from exc


def _validate_manifest(manifest: dict, fixture_path: Path, records: list[dict]) -> None:
    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    if missing:
        raise SecTinyFixtureError("manifest missing required fields: " + ", ".join(missing))

    if manifest["source_name"] != "SEC EDGAR / data.sec.gov":
        raise SecTinyFixtureError("source_name must identify SEC data.sec.gov")
    if manifest["source_quality"] != "public_official_observed":
        raise SecTinyFixtureError("source_quality must be public_official_observed")
    if manifest["provider"] != "sec":
        raise SecTinyFixtureError("provider must be sec")
    if manifest["provider_feed"] != "data.sec.gov":
        raise SecTinyFixtureError("provider_feed must be data.sec.gov")
    if manifest["entity_key_type"] != "CIK":
        raise SecTinyFixtureError("entity_key_type must be CIK")
    if manifest["observed_estimated_or_inferred"] != "observed":
        raise SecTinyFixtureError("observed_estimated_or_inferred must be observed")
    if not manifest["allowed_use"] or not manifest["forbidden_use"]:
        raise SecTinyFixtureError("allowed_use and forbidden_use are required")
    if not manifest["api_endpoint"].startswith("https://data.sec.gov/"):
        raise SecTinyFixtureError("api_endpoint must point to data.sec.gov")
    if manifest["row_count"] != len(records):
        raise SecTinyFixtureError("row_count mismatch")
    if manifest["sha256"] != compute_sha256(fixture_path):
        raise SecTinyFixtureError("sha256 mismatch")

    cik = manifest["cik"]
    if not re.fullmatch(r"\d{10}", cik):
        raise SecTinyFixtureError("CIK must be zero-padded 10 digits")
    for bound in ("start", "end"):
        _parse_iso_date(manifest["date_range"][bound], field=f"date_range.{bound}")


def _validate_records(payload: dict, manifest: dict, records: list[dict]) -> None:
    seen: set[str] = set()
    expected_cik = manifest["cik"]
    expected_columns = manifest["schema_columns"]

    for record in records:
        if list(record.keys()) != expected_columns:
            raise SecTinyFixtureError("schema column mismatch")
        if record["cik"] != expected_cik or not re.fullmatch(r"\d{10}", record["cik"]):
            raise SecTinyFixtureError("record CIK format invalid")
        primary_key = record.get("primary_key")
        if not primary_key:
            raise SecTinyFixtureError("primary_key is required")
        if primary_key in seen:
            raise SecTinyFixtureError("duplicate primary key")
        seen.add(primary_key)

        if payload["fixture_type"] == "sec_companyfacts_tiny":
            _parse_iso_date(record["filed"], field="filed")
            _parse_iso_date(record["end"], field="end")
            if not isinstance(record["value"], (int, float)) or not math.isfinite(record["value"]):
                raise SecTinyFixtureError("numeric facts must be finite")
        else:
            _parse_iso_date(record["filing_date"], field="filing_date")
            _parse_iso_date(record["report_date"], field="report_date", allow_blank=True)


def _validate_fixture(fixture_path: Path) -> None:
    manifest_path = _manifest_path(fixture_path)
    if not manifest_path.exists():
        raise SecTinyFixtureError("manifest is required")

    payload = _read_json(fixture_path)
    manifest = _read_json(manifest_path)
    records = _records(payload)

    _validate_manifest(manifest, fixture_path, records)
    _validate_records(payload, manifest, records)


def _copy_pair(tmp_path: Path, fixture_path: Path) -> Path:
    target = tmp_path / fixture_path.name
    target.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")
    manifest_target = _manifest_path(target)
    manifest_target.write_text(_manifest_path(fixture_path).read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _rewrite_pair(fixture_path: Path, payload: dict, manifest: dict) -> None:
    _write_json(fixture_path, payload)
    manifest["sha256"] = compute_sha256(fixture_path)
    manifest["row_count"] = len(_records(payload))
    _write_json(_manifest_path(fixture_path), manifest)


def test_g7_1d_sec_tiny_fixtures_and_manifests_validate():
    for fixture_path in SEC_FIXTURES:
        _validate_fixture(fixture_path)


def test_g7_1d_manifest_exists_for_each_fixture():
    for fixture_path in SEC_FIXTURES:
        assert _manifest_path(fixture_path).exists()


def test_g7_1d_rejects_manifest_hash_mismatch(tmp_path):
    fixture_path = _copy_pair(tmp_path, COMPANYFACTS_FIXTURE)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_json(manifest_path)
    manifest["sha256"] = "0" * 64
    _write_json(manifest_path, manifest)

    with pytest.raises(SecTinyFixtureError, match="sha256 mismatch"):
        _validate_fixture(fixture_path)


def test_g7_1d_rejects_row_count_mismatch(tmp_path):
    fixture_path = _copy_pair(tmp_path, SUBMISSIONS_FIXTURE)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_json(manifest_path)
    manifest["row_count"] = manifest["row_count"] + 1
    _write_json(manifest_path, manifest)

    with pytest.raises(SecTinyFixtureError, match="row_count mismatch"):
        _validate_fixture(fixture_path)


def test_g7_1d_rejects_duplicate_primary_key(tmp_path):
    fixture_path = _copy_pair(tmp_path, SUBMISSIONS_FIXTURE)
    payload = _read_json(fixture_path)
    manifest = _read_json(_manifest_path(fixture_path))
    payload["filings"].append(dict(payload["filings"][0]))
    _rewrite_pair(fixture_path, payload, manifest)

    with pytest.raises(SecTinyFixtureError, match="duplicate primary key"):
        _validate_fixture(fixture_path)


def test_g7_1d_rejects_non_finite_numeric_fact(tmp_path):
    fixture_path = _copy_pair(tmp_path, COMPANYFACTS_FIXTURE)
    payload = _read_json(fixture_path)
    manifest = _read_json(_manifest_path(fixture_path))
    payload["facts"][0]["value"] = float("inf")
    _rewrite_pair(fixture_path, payload, manifest)

    with pytest.raises(SecTinyFixtureError, match="numeric facts must be finite"):
        _validate_fixture(fixture_path)


def test_g7_1d_rejects_bad_cik_format(tmp_path):
    fixture_path = _copy_pair(tmp_path, COMPANYFACTS_FIXTURE)
    payload = _read_json(fixture_path)
    manifest = _read_json(_manifest_path(fixture_path))
    manifest["cik"] = "320193"
    payload["entity"]["cik"] = "320193"
    payload["facts"][0]["cik"] = "320193"
    _rewrite_pair(fixture_path, payload, manifest)

    with pytest.raises(SecTinyFixtureError, match="CIK must be zero-padded"):
        _validate_fixture(fixture_path)


def test_g7_1d_requires_source_quality_allowed_use_and_observed_label(tmp_path):
    fixture_path = _copy_pair(tmp_path, SUBMISSIONS_FIXTURE)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_json(manifest_path)

    manifest["source_quality"] = ""
    _write_json(manifest_path, manifest)
    with pytest.raises(SecTinyFixtureError, match="source_quality"):
        _validate_fixture(fixture_path)

    manifest = _read_json(manifest_path)
    manifest["source_quality"] = "public_official_observed"
    manifest["allowed_use"] = ""
    _write_json(manifest_path, manifest)
    with pytest.raises(SecTinyFixtureError, match="allowed_use"):
        _validate_fixture(fixture_path)

    manifest = _read_json(manifest_path)
    manifest["allowed_use"] = "fixture validation only"
    manifest["observed_estimated_or_inferred"] = "estimated"
    _write_json(manifest_path, manifest)
    with pytest.raises(SecTinyFixtureError, match="must be observed"):
        _validate_fixture(fixture_path)
