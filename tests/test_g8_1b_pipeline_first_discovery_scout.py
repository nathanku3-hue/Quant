from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from opportunity_engine.factor_scout import (
    load_factor_scout_baseline,
    load_factor_scout_manifest,
    load_factor_scout_output,
    select_first_eligible_fixture_row,
    source_artifact_metadata,
    validate_factor_scout_baseline_bundle,
    validate_factor_scout_output_bundle,
)
from opportunity_engine.factor_scout_schema import (
    SCOUT_DISCOVERY_ORIGIN,
    SCOUT_MODEL_ID,
    validate_factor_scout_baseline,
    validate_factor_scout_output,
)


BASELINE_PATH = Path("data/discovery/local_factor_scout_baseline_v0.json")
BASELINE_MANIFEST_PATH = Path("data/discovery/local_factor_scout_baseline_v0.manifest.json")
OUTPUT_PATH = Path("data/discovery/local_factor_scout_output_tiny_v0.json")
OUTPUT_MANIFEST_PATH = Path("data/discovery/local_factor_scout_output_tiny_v0.manifest.json")


def _baseline() -> dict:
    return load_factor_scout_baseline(BASELINE_PATH)


def _baseline_manifest() -> dict:
    return load_factor_scout_manifest(BASELINE_MANIFEST_PATH)


def _output() -> dict:
    return load_factor_scout_output(OUTPUT_PATH)


def _output_manifest() -> dict:
    return load_factor_scout_manifest(OUTPUT_MANIFEST_PATH)


def _baseline_errors(baseline: dict, manifest: dict | None = None) -> tuple[str, ...]:
    return validate_factor_scout_baseline(baseline, manifest=manifest or _baseline_manifest()).errors


def _output_errors(output: dict, manifest: dict | None = None, baseline: dict | None = None) -> tuple[str, ...]:
    return validate_factor_scout_output(
        output,
        manifest=manifest or _output_manifest(),
        baseline=baseline or _baseline(),
    ).errors


def _item(output: dict) -> dict:
    return output["items"][0]


def test_factor_scout_baseline_and_output_bundles_validate():
    baseline_result = validate_factor_scout_baseline_bundle(BASELINE_PATH, BASELINE_MANIFEST_PATH)
    output_result = validate_factor_scout_output_bundle(
        OUTPUT_PATH,
        OUTPUT_MANIFEST_PATH,
        baseline_path=BASELINE_PATH,
    )

    assert baseline_result.valid, baseline_result.errors
    assert output_result.valid, output_result.errors


def test_factor_scout_requires_model_id():
    baseline = _baseline()
    baseline["scout_model_id"] = "LOCAL_FACTOR_ALPHA_MODEL"

    assert any(f"scout_model_id must be {SCOUT_MODEL_ID}" in error for error in _baseline_errors(baseline))


def test_factor_scout_requires_model_version():
    baseline = _baseline()
    baseline["scout_model_version"] = ""

    assert any("scout_model_version is required" in error for error in _baseline_errors(baseline))


def test_factor_scout_requires_factor_names_and_weights():
    baseline = _baseline()
    baseline["factor_names"] = []
    baseline["factor_weights"] = {}

    errors = _baseline_errors(baseline)
    assert any("factor_names must be a non-empty list" in error for error in errors)
    assert any("factor_weights must be a non-empty object" in error for error in errors)


def test_factor_scout_weights_sum_to_one():
    baseline = _baseline()
    baseline["factor_weights"]["momentum_normalized"] = 0.50

    assert any("factor_weights must sum to 1.0" in error for error in _baseline_errors(baseline))


def test_factor_scout_requires_source_artifact_metadata():
    baseline = _baseline()
    baseline.pop("source_artifact_row_count")
    baseline["source_artifact_date_range"] = {"start": "", "end": ""}
    baseline["source_artifact_universe_count"] = 0

    errors = _baseline_errors(baseline)
    assert any("source_artifact_row_count" in error for error in errors)
    assert any("source_artifact_date_range.start is required" in error for error in errors)
    assert any("source_artifact_date_range.end is required" in error for error in errors)
    assert any("source_artifact_universe_count must be a positive integer" in error for error in errors)


def test_factor_scout_requires_input_or_source_manifest_reference():
    baseline = _baseline()
    baseline.pop("input_data_manifest")
    baseline.pop("source_artifact_manifest", None)

    assert any(
        "input_data_manifest or source_artifact_manifest is required" in error
        for error in _baseline_errors(baseline)
    )


def test_factor_scout_output_requires_manifest():
    output = _output()

    assert any(
        "output manifest is required" in error
        for error in validate_factor_scout_output(output, baseline=_baseline()).errors
    )


def test_factor_scout_output_is_intake_only():
    output = _output()
    result = validate_factor_scout_output(output, manifest=_output_manifest(), baseline=_baseline())

    assert result.valid, result.errors
    assert len(output["items"]) == 1
    assert _item(output)["status"] == "intake_only"

    bad_output = deepcopy(output)
    _item(bad_output)["status"] = "candidate_card_exists"

    assert any("status must be intake_only" in error for error in _output_errors(bad_output))


def test_factor_scout_output_uses_local_factor_scout_origin():
    output = _output()

    assert _item(output)["discovery_origin"] == SCOUT_DISCOVERY_ORIGIN

    _item(output)["discovery_origin"] = "SYSTEM_SCOUTED"

    assert any(
        f"discovery_origin must be {SCOUT_DISCOVERY_ORIGIN}" in error
        for error in _output_errors(output)
    )


def test_factor_scout_output_is_system_scouted_but_not_validated():
    output = _output()
    item = _item(output)

    assert item["is_user_seeded"] is False
    assert item["is_system_scouted"] is True
    assert item["is_validated"] is False
    assert item["is_actionable"] is False

    item["is_validated"] = True

    assert any("is_validated must be false" in error for error in _output_errors(output))


def test_factor_scout_output_cannot_expose_score():
    output = _output()
    _item(output)["factor_score"] = 0.99

    assert any("factor_score" in error for error in _output_errors(output))


def test_factor_scout_output_cannot_expose_rank():
    output = _output()
    _item(output)["rank"] = 1

    assert any("rank" in error for error in _output_errors(output))


def test_factor_scout_output_cannot_emit_buy_sell_hold():
    output = _output()
    _item(output)["decision_call"] = "buy"

    assert any("forbidden action call" in error for error in _output_errors(output))


def test_factor_scout_output_cannot_mark_actionable():
    output = _output()
    _item(output)["is_actionable"] = True

    assert any("is_actionable must be false" in error for error in _output_errors(output))


def test_factor_scout_output_cannot_create_candidate_card():
    output = _output()
    _item(output)["candidate_card_created"] = True

    assert any("candidate_card_created" in error for error in _output_errors(output))


def test_yfinance_not_canonical_in_factor_scout():
    manifest = _output_manifest()
    manifest["source_policy"]["canonical_sources"].append({"source_id": "yfinance", "canonical": True})

    assert any("yfinance cannot be canonical" in error for error in _output_errors(_output(), manifest=manifest))


def test_factor_scout_metadata_reader_matches_fixture_metadata():
    metadata = source_artifact_metadata()
    baseline = _baseline()

    assert metadata["source_artifact_row_count"] == baseline["source_artifact_row_count"]
    assert metadata["source_artifact_date_range"] == baseline["source_artifact_date_range"]
    assert metadata["source_artifact_universe_count"] == baseline["source_artifact_universe_count"]


def test_factor_scout_selection_is_deterministic_without_score_ordering():
    row = select_first_eligible_fixture_row()
    output = _output()
    baseline = _baseline()

    assert row["ticker"] == _item(output)["ticker"]
    assert row["company_name"] == _item(output)["company_name"]
    assert row["asof_date"] == output["asof_date"]
    assert row["uses_score_ordering"] is False
    assert baseline["selection_policy"]["uses_score_ordering"] is False
