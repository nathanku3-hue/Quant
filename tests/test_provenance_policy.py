from __future__ import annotations

import json

import pytest

from data.provenance import ManifestInput
from data.provenance import ProvenanceError
from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import SOURCE_QUALITY_OPERATIONAL
from data.provenance import assert_can_promote
from data.provenance import assert_can_validate_artifact
from data.provenance import build_manifest
from data.provenance import validate_alert_record
from data.provenance import validate_quote_snapshot
from data.provenance import write_manifest


def _artifact(tmp_path):
    path = tmp_path / "returns.csv"
    path.write_text("date,net_ret\n2026-01-01,0.01\n", encoding="utf-8")
    return path


def test_validation_requires_manifest(tmp_path):
    artifact = _artifact(tmp_path)

    with pytest.raises(ProvenanceError, match="Missing provenance manifest"):
        assert_can_validate_artifact(artifact)


def test_canonical_manifest_allows_promotion_validation(tmp_path):
    artifact = _artifact(tmp_path)
    manifest = build_manifest(
        ManifestInput(
            artifact_path=artifact,
            source_quality=SOURCE_QUALITY_CANONICAL,
            provider="wrds",
            provider_feed="crsp_daily",
            license_scope="canonical_research",
            row_count=1,
            date_range={"start": "2026-01-01", "end": "2026-01-01"},
        )
    )
    write_manifest(manifest, artifact_path=artifact)

    loaded = assert_can_validate_artifact(artifact, promotion_intent=True)

    assert loaded["source_quality"] == SOURCE_QUALITY_CANONICAL


def test_tier2_manifest_blocks_promotion(tmp_path):
    artifact = _artifact(tmp_path)
    manifest = build_manifest(
        ManifestInput(
            artifact_path=artifact,
            source_quality=SOURCE_QUALITY_NON_CANONICAL,
            provider="yahoo",
            provider_feed="yahoo_public_api",
            license_scope="research_education_convenience_only",
            row_count=1,
            date_range=("2026-01-01", "2026-01-01"),
        )
    )
    write_manifest(manifest, artifact_path=artifact)

    with pytest.raises(ProvenanceError, match="V1 promotion validation"):
        assert_can_validate_artifact(artifact, promotion_intent=True)
    with pytest.raises(ProvenanceError, match="V1 promotion packet"):
        assert_can_promote({"manifest": manifest})


def test_alert_requires_source_quality():
    with pytest.raises(ProvenanceError, match="source_quality is required"):
        validate_alert_record({"symbol": "AAPL", "provider": "alpaca", "provider_feed": "iex"})


def test_alpaca_iex_quote_requires_iex_only_tag():
    quote = {
        "symbol": "AAPL",
        "provider": "alpaca",
        "provider_feed": "iex",
        "source_quality": SOURCE_QUALITY_OPERATIONAL,
        "quote_quality": "sip_quality",
    }

    with pytest.raises(ProvenanceError, match="quote_quality=iex_only"):
        validate_quote_snapshot(quote)

    quote["quote_quality"] = "iex_only"
    validate_quote_snapshot(quote)

