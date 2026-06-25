from __future__ import annotations

import csv
import json
import math
from datetime import date
from pathlib import Path

import pytest

from data.provenance import compute_sha256


FIXTURE = Path("data/fixtures/cftc/cftc_tff_tiny.csv")
MANIFEST = Path("data/fixtures/cftc/cftc_tff_tiny.manifest.json")

REQUIRED_MANIFEST_FIELDS = {
    "source_name",
    "source_quality",
    "provider",
    "provider_feed",
    "dataset_type",
    "observed_estimated_or_inferred",
    "report_date",
    "asof_position_date",
    "publication_or_retrieved_at",
    "market_name",
    "contract_market_code",
    "trader_category",
    "long_positions",
    "short_positions",
    "spreading_positions",
    "open_interest",
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

ALLOWED_TRADER_CATEGORIES = {
    "Dealer/Intermediary",
    "Asset Manager/Institutional",
    "Leveraged Funds",
    "Other Reportables",
}

FORBIDDEN_SINGLE_NAME_COLUMNS = {
    "ticker",
    "symbol",
    "issuer",
    "cusip",
    "sedol",
    "isin",
    "single_name_inference",
    "cta_buying_signal",
}


class CftcTffTinyFixtureError(RuntimeError):
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
        raise CftcTffTinyFixtureError(f"{field} must parse as ISO date: {value!r}") from exc


def _finite_non_negative(value: str, *, field: str, allow_blank: bool = False) -> None:
    if allow_blank and value == "":
        return
    try:
        parsed = float(value)
    except ValueError as exc:
        raise CftcTffTinyFixtureError(f"{field} must be numeric: {value!r}") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise CftcTffTinyFixtureError(f"{field} must be finite and non-negative")


def _validate_manifest(manifest: dict, fixture_path: Path, rows: list[dict[str, str]]) -> None:
    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    if missing:
        raise CftcTffTinyFixtureError("manifest missing required fields: " + ", ".join(missing))

    if manifest["source_name"] != "CFTC Commitments of Traders / TFF":
        raise CftcTffTinyFixtureError("source_name must identify CFTC Commitments of Traders / TFF")
    if manifest["source_quality"] != "public_official_observed":
        raise CftcTffTinyFixtureError("source_quality must be public_official_observed")
    if manifest["provider"] != "cftc":
        raise CftcTffTinyFixtureError("provider must be cftc")
    if manifest["provider_feed"] != "cot_tff":
        raise CftcTffTinyFixtureError("provider_feed must be cot_tff")
    if manifest["dataset_type"] != "futures_positioning":
        raise CftcTffTinyFixtureError("dataset_type must be futures_positioning")
    if manifest["observed_estimated_or_inferred"] != "observed":
        raise CftcTffTinyFixtureError("observed_estimated_or_inferred must be observed")
    if manifest["freshness_policy"] != "weekly / Friday release / Tuesday positions":
        raise CftcTffTinyFixtureError("freshness_policy must be weekly / Friday release / Tuesday positions")
    if not manifest["allowed_use"] or not manifest["forbidden_use"]:
        raise CftcTffTinyFixtureError("allowed_use and forbidden_use are required")
    if "single_name_inference" not in set(manifest["forbidden_use"]):
        raise CftcTffTinyFixtureError("single_name_inference must be forbidden")
    if not str(manifest["official_source_url"]).startswith("https://www.cftc.gov/"):
        raise CftcTffTinyFixtureError("official_source_url must point to CFTC")
    if manifest["row_count"] != len(rows):
        raise CftcTffTinyFixtureError("row_count mismatch")
    if manifest["sha256"] != compute_sha256(fixture_path):
        raise CftcTffTinyFixtureError("sha256 mismatch")

    _parse_iso_date(manifest["report_date"], field="report_date")
    _parse_iso_date(manifest["asof_position_date"], field="asof_position_date")
    _parse_iso_date(manifest["publication_or_retrieved_at"], field="publication_or_retrieved_at")
    for bound in ("start", "end"):
        _parse_iso_date(manifest["date_range"][bound], field=f"date_range.{bound}")


def _validate_rows(manifest: dict, rows: list[dict[str, str]]) -> None:
    expected_columns = manifest["schema_columns"]
    seen: set[tuple[str, str, str, str]] = set()

    for row in rows:
        if list(row.keys()) != expected_columns:
            raise CftcTffTinyFixtureError("schema column mismatch")
        if FORBIDDEN_SINGLE_NAME_COLUMNS.intersection(row):
            raise CftcTffTinyFixtureError("single-name inference fields must not appear")

        report_date = row["report_date"]
        asof_position_date = row["asof_position_date"]
        market_name = row["market_name"].strip()
        contract_market_code = row["contract_market_code"].strip()
        trader_category = row["trader_category"].strip()

        _parse_iso_date(report_date, field="report_date")
        _parse_iso_date(asof_position_date, field="asof_position_date")
        if not market_name:
            raise CftcTffTinyFixtureError("market_name is required")
        if not contract_market_code:
            raise CftcTffTinyFixtureError("contract_market_code is required")
        if trader_category not in ALLOWED_TRADER_CATEGORIES:
            raise CftcTffTinyFixtureError("trader_category is not allowed")

        primary_key = (report_date, market_name, contract_market_code, trader_category)
        if primary_key in seen:
            raise CftcTffTinyFixtureError("duplicate primary key")
        seen.add(primary_key)

        _finite_non_negative(row["long_positions"], field="long_positions")
        _finite_non_negative(row["short_positions"], field="short_positions")
        _finite_non_negative(row["spreading_positions"], field="spreading_positions", allow_blank=True)
        _finite_non_negative(row["open_interest"], field="open_interest")


def _validate_fixture(fixture_path: Path = FIXTURE) -> None:
    manifest_path = _manifest_path(fixture_path)
    if not manifest_path.exists():
        raise CftcTffTinyFixtureError("manifest is required")

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


def test_g7_1f_cftc_tff_fixture_and_manifest_validate():
    _validate_fixture()


def test_g7_1f_manifest_exists():
    assert MANIFEST.exists()


def test_g7_1f_rejects_manifest_hash_mismatch(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_manifest(manifest_path)
    manifest["sha256"] = "0" * 64
    _write_manifest(manifest_path, manifest)

    with pytest.raises(CftcTffTinyFixtureError, match="sha256 mismatch"):
        _validate_fixture(fixture_path)


def test_g7_1f_rejects_row_count_mismatch(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_manifest(manifest_path)
    manifest["row_count"] = manifest["row_count"] + 1
    _write_manifest(manifest_path, manifest)

    with pytest.raises(CftcTffTinyFixtureError, match="row_count mismatch"):
        _validate_fixture(fixture_path)


def test_g7_1f_rejects_duplicate_primary_key(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows.append(dict(rows[0]))
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(CftcTffTinyFixtureError, match="duplicate primary key"):
        _validate_fixture(fixture_path)


def test_g7_1f_rejects_non_finite_or_negative_values(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows[0]["long_positions"] = "nan"
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(CftcTffTinyFixtureError, match="long_positions"):
        _validate_fixture(fixture_path)

    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows[0]["long_positions"] = "1"
    rows[0]["open_interest"] = "-1"
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(CftcTffTinyFixtureError, match="open_interest"):
        _validate_fixture(fixture_path)


def test_g7_1f_requires_source_quality_allowed_use_observed_label_and_single_name_block(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    manifest_path = _manifest_path(fixture_path)
    manifest = _read_manifest(manifest_path)

    manifest["source_quality"] = ""
    _write_manifest(manifest_path, manifest)
    with pytest.raises(CftcTffTinyFixtureError, match="source_quality"):
        _validate_fixture(fixture_path)

    manifest = _read_manifest(manifest_path)
    manifest["source_quality"] = "public_official_observed"
    manifest["allowed_use"] = []
    _write_manifest(manifest_path, manifest)
    with pytest.raises(CftcTffTinyFixtureError, match="allowed_use"):
        _validate_fixture(fixture_path)

    manifest = _read_manifest(manifest_path)
    manifest["allowed_use"] = ["broad futures-positioning context"]
    manifest["observed_estimated_or_inferred"] = "estimated"
    _write_manifest(manifest_path, manifest)
    with pytest.raises(CftcTffTinyFixtureError, match="must be observed"):
        _validate_fixture(fixture_path)

    manifest = _read_manifest(manifest_path)
    manifest["observed_estimated_or_inferred"] = "observed"
    manifest["forbidden_use"] = ["buy/sell signal"]
    _write_manifest(manifest_path, manifest)
    with pytest.raises(CftcTffTinyFixtureError, match="single_name_inference"):
        _validate_fixture(fixture_path)


def test_g7_1f_rejects_single_name_columns_and_unknown_trader_category(tmp_path):
    fixture_path = _copy_pair(tmp_path)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    for row in rows:
        row["ticker"] = "AAPL"
    manifest["schema_columns"].append("ticker")
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(CftcTffTinyFixtureError, match="single-name inference"):
        _validate_fixture(fixture_path)

    fixture_path = _copy_pair(tmp_path)
    rows = _read_rows(fixture_path)
    manifest = _read_manifest(_manifest_path(fixture_path))
    rows[0]["trader_category"] = "CTA"
    _rewrite_pair(fixture_path, rows, manifest)

    with pytest.raises(CftcTffTinyFixtureError, match="trader_category"):
        _validate_fixture(fixture_path)
