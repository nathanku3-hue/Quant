from __future__ import annotations

import math

import pandas as pd
import pytest

from data.provenance import ManifestInput
from data.provenance import ProvenanceError
from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import build_manifest
from validation.schemas import run_minimal_validation_lab
from validation.schemas import validate_validation_report


def _returns_frame() -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=140, freq="B")
    values = [0.002 + 0.0005 * math.sin(i / 5.0) for i in range(len(dates))]
    return pd.DataFrame(
        {
            "date": dates,
            "net_ret": values,
            "regime": ["low_vol" if i % 2 == 0 else "high_vol" for i in range(len(dates))],
        }
    )


def _manifest(tmp_path, quality=SOURCE_QUALITY_CANONICAL):
    artifact = tmp_path / "returns.csv"
    _returns_frame().to_csv(artifact, index=False)
    return build_manifest(
        ManifestInput(
            artifact_path=artifact,
            source_quality=quality,
            provider="wrds" if quality == SOURCE_QUALITY_CANONICAL else "yahoo",
            provider_feed="crsp_daily" if quality == SOURCE_QUALITY_CANONICAL else "yahoo_public_api",
            license_scope="canonical_research" if quality == SOURCE_QUALITY_CANONICAL else "research_education",
            row_count=140,
            date_range={"start": "2020-01-01", "end": "2020-07-14"},
        )
    )


def test_minimal_validation_lab_returns_full_report(tmp_path):
    report = run_minimal_validation_lab(
        _returns_frame(),
        source_manifest=_manifest(tmp_path),
        strategy_id="SYNTHETIC_PASS",
        promotion_intent=True,
    ).to_dict()

    validate_validation_report(report)
    assert report["strategy_id"] == "SYNTHETIC_PASS"
    assert report["source_manifest"]["source_quality"] == SOURCE_QUALITY_CANONICAL
    assert set(["oos", "walk_forward", "regime", "permutation", "bootstrap"]).issubset(report)


def test_minimal_validation_lab_blocks_tier2_promotion(tmp_path):
    with pytest.raises(ProvenanceError, match="V1 promotion validation lab"):
        run_minimal_validation_lab(
            _returns_frame(),
            source_manifest=_manifest(tmp_path, quality=SOURCE_QUALITY_NON_CANONICAL),
            strategy_id="TIER2_BLOCKED",
            promotion_intent=True,
        )

