from __future__ import annotations

import csv
import json
import math
from datetime import date
from pathlib import Path

import pytest

from data.provenance import compute_sha256


FIXTURE = Path("data/fixtures/finra/finra_short_interest_tiny.csv")
MANIFEST = Path("data/fixtures/finra/finra_short_interest_tiny.manifest.json")

REQUIRED_MANIFEST_FIELDS = {
    "source_name",
    "source_quality",
    "provider",
    "provider_feed",
    "dataset_type",
    "observed_estimated_or_inferred",
    "settlement_date",
    "publication_or_retrieved_at",
    "asof_ts",
    "ticker",
    "issue_name",
    "short_interest",
    "average_daily_volume",
    "days_to_cover",
    "row_count",
    "date_range",
    "sha256",
    "schema_version",
    "official_source_url",
    "license_or_terms_note",
    "freshness_policy",
    "allowed_use",
    "forbidden_use",
}

REG_SHO_ONLY_COLUMNS = {
    "short_sale_volume",
    "short_exempt_volume",
    "total_volume",
    "market_center",
    "trade_date",
}


class FinraTinyFixtureError(RuntimeError):
    pass


def _manifest_path(fixture_path: Path) -> Path:
    if fixture_path == FIXTURE:
        return MANIFEST
    return fixture_path.with_name(f"{fixture_path.stem}.manifest.json")


def _read_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _read_rows(path: Path = FIXTURE) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _parse_iso_date(value: str, *, field: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise FinraTinyFixtureError(f"{field} must parse as ISO date: {value!r}") from exc


def _finite_non_negative(value: str, *, field: str, allow_blank: bool = False) -> None:
    if allow_blank and value == "":
        return
    try:
        parsed = float(value)
    except ValueError as exc:
        raise FinraTinyFixtureError(f"{field} must be numeric: {value!r}") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise FinraTinyFixtureError(f"{field} must be finite and non-negative")


def _validate_manifest(manifest: dict, fixture_path: Path, rows: list[dict[str, str]]) -> None:
    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    if missing:
        raise FinraTinyFixtureError("manifest missing required fields: " + ", ".join(missing))

    if manifest["source_name"] != "FINRA Equity Short Interest":
        raise FinraTinyFixtureError("source_name must identify FINRA Equity Short Interest")
    if manifest["source_quality"] != "public_official_observed":
        raise FinraTinyFixtureError("source_quality must be public_official_observed")
    if manifest["provider"] != "finra":
        raise FinraTinyFixtureError("provider must be finra")
    if manifest["provider_feed"] != "equity_short_interest":
        raise FinraTinyFixtureError("provider_feed must be equity_short_interest")
    if manifest["dataset_type"] != "short_interest":
        raise FinraTinyFixtureError("dataset_type must be short_interest")
    if manifest["observed_estimated_or_inferred"] != "observed":
        raise FinraTinyFixtureError("observed_estimated_or_inferred must be observed")
    if manifest["freshness_policy"] != "twice_monthly / delayed":
        raise FinraTinyFixtureError("freshness_policy must be twice_monthly / delayed")
    if not manifest["allowed_use"] or not manifest["forbidden_use"]:
        raise FinraTinyFixtureError("allowed_use and forbidden_use are required")
    if not str(manifest["official_source_url"]).startswith("https://cdn.finra.org/"):
        raise FinraTinyFixtureError("official_source_url must point to FINRA CDN")
    if manifest["row_count"] != len(rows):
        raise FinraTinyFixtureError("row_count mismatch")
    if manifest["sha256"] != compute_sha256(fixture_path):
        raise FinraTinyFixtureError("sha256 mismatch")

    _parse_iso_date(manifest["settlement_date"], field="settlement_date")
    _parse_iso_date(manifest["asof_ts"], field="asof_ts")
    _parse_iso_date(manifest["publication_or_retrieved_at"], field="publication_or_retrieved_at")
    for bound in ("start", "end"):
        _parse_iso_date(manifest["date_range"][bound], field=f"date_range.{bound}")


def _validate_rows(manifest: dict, rows: list[dict[str, str]]) -> None:
    expected_columns = manifest["schema_columns"]
    seen: set[tuple[str, str]] = set()

    for row in rows:
        if list(row.keys()) != expected_columns:
            raise FinraTinyFixtureError("schema column mismatch")
        if REG_SHO_ONLY_COLUMNS.intersection(row):
            raise FinraTinyFixtureError("Reg SHO fields must not appear in short-interest fixture")

        settlement_date = row["settlement_date"]
        ticker = row["ticker"].strip()
        _parse_iso_date(settlement_date, field="settlement_date")
        if not ticker:
            raise FinraTinyFixtureError("ticker is required")

        primary_key = (settlement_date, ticker)
        if primary_key in seen:
            raise FinraTinyFixtureError("duplicate primary key")
        seen.add(primary_key)

        _finite_non_negative(row["short_interest"], field="short_interest")
        _finite_non_negative(row["average_daily_volume"], field="average_daily_volume")
        _finite_non_negative(row["days_to_cover"], field="days_to_cover", allow_blank=True)


def _validate_fixture(fixture_path: Path = FIXTURE) -> None:
    manifest_path = _manifest_path(fixture_path)
    if not manifest_path.exists():
        raise FinraTinyFixtureError("manifest is required")

    rows = _read_rows(fixture_path)
    manifest = _read_manifest(manifest_path)
    _validate_manifest(manifest, fixture_path, rows)
    _validate_rows(manifest, rows)


def _copy_pair(tmp_path: Path) -> Path:
    target = tmp_path / FIXTURE.name
    target.write_bytes(FIXTURE.read_bytes())
    manifest_target = _manifest_path(target)
    manifest_target.write_text(MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _rewrite_pair(fixture_path: Path, rows: list[dict[str, object]], manifest: dict) -> None:
    _write_rows(fixture_path, rows, list(rows[0].keys()))
    manifest["sha256"] = compute_sha256(fixture_path)
    manifest["row_count"] = len(rows)
    _write_manifest(_manifest_path(fixture_path), manifest)


def test_g7_1e_finra_short_interest_fixture_and_manifest_validate():
    _validate_fixture()


def test_g7_1e_manifest_exists():
    assert MANIFEST.exists()


def test_g7_1e_rejects_manifest_hash_mismatch(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_manifest(manifest_path)
    manifest["sha256"] = "0" * 64
    _write_manifest(manifest_path, manifest)

    with pytest.raises(FinraTinyFixtureError, match="sha256 mismatch"):
        _validate_fixture(fixture_path)


def test_g7_1e_rejects_row_count_mismatch(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_manifest(manifest_path)
    manifest["row_count"] = manifest["row_count"] + 1
    _write_manifest(manifest_path, manifest)

    with pytest.raises(FinraTinyFixtureError, match="row_count mismatch"):
        _validate_fixture(fixture_path)


def test_g7_1e_rejects_duplicate_primary_key(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows.append(dict(rows[0]))
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(FinraTinyFixtureError, match="duplicate primary key"):
        _validate_fixture(fixture_path)


def test_g7_1e_rejects_non_finite_or_negative_values(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows[0]["short_interest"] = "nan"
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(FinraTinyFixtureError, match="short_interest"):
        _validate_fixture(fixture_path)

    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows[0]["short_interest"] = "1"
    rows[0]["average_daily_volume"] = "-1"
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(FinraTinyFixtureError, match="average_daily_volume"):
        _validate_fixture(fixture_path)


def test_g7_1e_requires_source_quality_allowed_use_and_observed_label(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_manifest(manifest_path)

    manifest["source_quality"] = ""
    _write_manifest(manifest_path, manifest)
    with pytest.raises(FinraTinyFixtureError, match="source_quality"):
        _validate_fixture(fixture_path)

    manifest = _read_manifest(manifest_path)
    manifest["source_quality"] = "public_official_observed"
    manifest["allowed_use"] = []
    _write_manifest(manifest_path, manifest)
    with pytest.raises(FinraTinyFixtureError, match="allowed_use"):
        _validate_fixture(fixture_path)

    manifest = _read_manifest(manifest_path)
    manifest["allowed_use"] = ["fixture validation only"]
    manifest["observed_estimated_or_inferred"] = "estimated"
    _write_manifest(manifest_path, manifest)
    with pytest.raises(FinraTinyFixtureError, match="must be observed"):
        _validate_fixture(fixture_path)


def test_g7_1e_rejects_reg_sho_fields_in_short_interest_fixture(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    for row in rows:
        row["short_sale_volume"] = "100"
    manifest["schema_columns"].append("short_sale_volume")
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(FinraTinyFixtureError, match="Reg SHO fields"):
        _validate_fixture(fixture_path)
