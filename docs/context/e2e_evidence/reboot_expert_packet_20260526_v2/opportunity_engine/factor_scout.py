from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from opportunity_engine.factor_scout_schema import (
    EXPECTED_SOURCE_ARTIFACT,
    FactorScoutValidationError,
    FactorScoutValidationResult,
    assert_valid_factor_scout_baseline,
    assert_valid_factor_scout_output,
    validate_factor_scout_baseline,
    validate_factor_scout_output,
)


def load_factor_scout_baseline(path: str | Path) -> dict[str, Any]:
    return _load_json(path)


def load_factor_scout_output(path: str | Path) -> dict[str, Any]:
    return _load_json(path)


def load_factor_scout_manifest(path: str | Path) -> dict[str, Any]:
    return _load_json(path)


def validate_factor_scout_baseline_bundle(
    baseline_path: str | Path,
    manifest_path: str | Path,
) -> FactorScoutValidationResult:
    baseline = load_factor_scout_baseline(baseline_path)
    manifest = load_factor_scout_manifest(manifest_path)
    result = validate_factor_scout_baseline(baseline, manifest=manifest)
    hash_error = _validate_manifest_hash(Path(baseline_path), manifest)
    if hash_error is None:
        return result
    return FactorScoutValidationResult(valid=False, errors=(*result.errors, hash_error))


def validate_factor_scout_output_bundle(
    output_path: str | Path,
    manifest_path: str | Path,
    *,
    baseline_path: str | Path | None = None,
) -> FactorScoutValidationResult:
    output = load_factor_scout_output(output_path)
    manifest = load_factor_scout_manifest(manifest_path)
    baseline = load_factor_scout_baseline(baseline_path) if baseline_path is not None else None
    result = validate_factor_scout_output(output, manifest=manifest, baseline=baseline)
    hash_error = _validate_manifest_hash(Path(output_path), manifest)
    if hash_error is None:
        return result
    return FactorScoutValidationResult(valid=False, errors=(*result.errors, hash_error))


def assert_valid_factor_scout_baseline_bundle(
    baseline_path: str | Path,
    manifest_path: str | Path,
) -> None:
    result = validate_factor_scout_baseline_bundle(baseline_path, manifest_path)
    if not result.valid:
        raise FactorScoutValidationError("; ".join(result.errors))

    baseline = load_factor_scout_baseline(baseline_path)
    manifest = load_factor_scout_manifest(manifest_path)
    assert_valid_factor_scout_baseline(baseline, manifest=manifest)


def assert_valid_factor_scout_output_bundle(
    output_path: str | Path,
    manifest_path: str | Path,
    *,
    baseline_path: str | Path | None = None,
) -> None:
    result = validate_factor_scout_output_bundle(
        output_path,
        manifest_path,
        baseline_path=baseline_path,
    )
    if not result.valid:
        raise FactorScoutValidationError("; ".join(result.errors))

    output = load_factor_scout_output(output_path)
    manifest = load_factor_scout_manifest(manifest_path)
    baseline = load_factor_scout_baseline(baseline_path) if baseline_path is not None else None
    assert_valid_factor_scout_output(output, manifest=manifest, baseline=baseline)


def source_artifact_metadata(source_path: str | Path = EXPECTED_SOURCE_ARTIFACT) -> dict[str, Any]:
    import duckdb

    path = str(source_path)
    con = duckdb.connect(database=":memory:")
    try:
        row = con.execute(
            """
            SELECT
                COUNT(*)::BIGINT AS row_count,
                MIN(date)::DATE::VARCHAR AS start_date,
                MAX(date)::DATE::VARCHAR AS end_date,
                COUNT(DISTINCT permno)::BIGINT AS universe_count
            FROM read_parquet(?)
            """,
            [path],
        ).fetchone()
    finally:
        con.close()

    if row is None:
        raise ValueError(f"source artifact has no readable metadata: {source_path}")
    row_count, start_date, end_date, universe_count = row
    return {
        "source_artifact": path,
        "source_artifact_row_count": int(row_count),
        "source_artifact_date_range": {"start": start_date, "end": end_date},
        "source_artifact_universe_count": int(universe_count),
        "source_artifact_sha256": artifact_sha256(source_path),
    }


def select_first_eligible_fixture_row(
    source_path: str | Path = EXPECTED_SOURCE_ARTIFACT,
    *,
    ticker_map_path: str | Path = "data/processed/tickers.parquet",
    company_master_path: str | Path = "data/processed/security_master_compustat.parquet",
) -> dict[str, Any]:
    import duckdb

    con = duckdb.connect(database=":memory:")
    try:
        row = con.execute(
            """
            WITH latest AS (
                SELECT MAX(date) AS asof_date
                FROM read_parquet(?)
            ),
            factor_rows AS (
                SELECT f.date::DATE::VARCHAR AS asof_date, CAST(f.permno AS BIGINT) AS permno
                FROM read_parquet(?) f, latest l
                WHERE f.date = l.asof_date
                  AND f.score_valid = true
                  AND f.momentum_normalized IS NOT NULL
                  AND f.quality_normalized IS NOT NULL
                  AND f.volatility_normalized IS NOT NULL
                  AND f.illiquidity_normalized IS NOT NULL
            ),
            tickers AS (
                SELECT CAST(permno AS BIGINT) AS permno, ticker
                FROM read_parquet(?)
                WHERE ticker IS NOT NULL AND ticker <> ''
            ),
            names AS (
                SELECT ticker, any_value(company_name) AS company_name
                FROM read_parquet(?)
                WHERE ticker IS NOT NULL
                  AND ticker <> ''
                  AND company_name IS NOT NULL
                  AND company_name <> ''
                GROUP BY ticker
            )
            SELECT r.asof_date, r.permno, t.ticker, n.company_name
            FROM factor_rows r
            JOIN tickers t USING (permno)
            JOIN names n ON upper(n.ticker) = upper(t.ticker)
            ORDER BY r.asof_date DESC, r.permno ASC
            LIMIT 1
            """,
            [str(source_path), str(source_path), str(ticker_map_path), str(company_master_path)],
        ).fetchone()
    finally:
        con.close()

    if row is None:
        raise ValueError("no eligible local factor scout fixture row found")
    asof_date, permno, ticker, company_name = row
    return {
        "asof_date": str(asof_date),
        "permno": int(permno),
        "ticker": str(ticker),
        "company_name": str(company_name),
        "selection_basis": "latest_date_then_lowest_permno_after_local_metadata_filters",
        "uses_score_ordering": False,
    }


def artifact_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_manifest_hash(artifact_path: Path, manifest: Mapping[str, Any]) -> str | None:
    expected = manifest.get("artifact_sha256")
    if not expected:
        return "manifest artifact_sha256 is required"
    observed = artifact_sha256(artifact_path)
    if expected != observed:
        return "manifest artifact_sha256 does not match artifact bytes"
    return None


def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data
