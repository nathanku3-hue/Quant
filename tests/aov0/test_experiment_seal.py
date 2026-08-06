from __future__ import annotations

import json
from pathlib import Path

from research.aov0.cube import build_vertical_cube
from research.aov0.experiment import (
    reopen_prospective_seal,
    run_five_arm_experiment,
    seal_prospective_experiment,
)


COMPUTED_AT = "2026-08-06T18:00:00Z"


def test_five_arm_experiment_emits_hash_bound_evidence_and_seals_exactly(
    tmp_path: Path,
    aov_primitives,
    rule100_weights,
    aov_returns,
    economic_cash_returns,
    development_contract,
) -> None:
    cube = build_vertical_cube(aov_primitives, computed_at=COMPUTED_AT)
    result = run_five_arm_experiment(
        rule100_weights=rule100_weights,
        returns_df=aov_returns,
        economic_cash_returns=economic_cash_returns,
        cube=cube,
        pit_eligibility_provider=lambda _date: (101, 202),
        output_root=tmp_path / "evidence",
        contract=development_contract,
    )
    assert set(result.arm_metrics) == {
        "rule100",
        "parent",
        "child",
        "pit_equal_weight",
        "economic_cash",
    }
    assert result.runs["rule100"].status.value == "diagnostic_only"
    assert result.runs["parent"].status.value == "exploratory"
    assert result.runs["child"].status.value == "exploratory"
    for run in result.runs.values():
        manifest = Path(run.artifacts["evidence_manifest.json"])
        assert manifest.is_file()
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        assert payload["schema_version"] == "research_evidence_manifest_v1"
        assert "evidence_packet.json" in payload["files"]

    experiment = json.loads(result.experiment_manifest.read_text(encoding="utf-8"))
    assert experiment["evidence_level"] == "A1_EXPLORATORY_MECHANICAL_ONLY"
    assert experiment["alpha_evidence"] == 0
    assert experiment["dag"]["cache_misses"] == 3

    seal = seal_prospective_experiment(
        result,
        cube=cube,
        decision_cut_id="AOV0_LOCAL_CUT_20260806",
        sealed_at="2026-08-06T18:30:00Z",
        output_dir=tmp_path / "seals",
        contract=development_contract,
    )
    reopened = reopen_prospective_seal(seal.path)
    assert reopened == seal.payload
    assert reopened["outcome_status"] == "SEALED_NOT_OPENED"
    assert reopened["outcome_data_loaded"] is False
    assert reopened["outcome_open_not_before"] == "2026-09-05T18:30:00Z"
    assert reopened["alpha_evidence"] == 0
    assert len(reopened["seal_id"]) == 64


def test_seal_hash_tamper_fails_closed(
    tmp_path: Path,
    aov_primitives,
    rule100_weights,
    aov_returns,
    economic_cash_returns,
    development_contract,
) -> None:
    cube = build_vertical_cube(aov_primitives, computed_at=COMPUTED_AT)
    result = run_five_arm_experiment(
        rule100_weights=rule100_weights,
        returns_df=aov_returns,
        economic_cash_returns=economic_cash_returns,
        cube=cube,
        pit_eligibility_provider=lambda _date: (101, 202),
        output_root=tmp_path / "evidence",
        contract=development_contract,
    )
    seal = seal_prospective_experiment(
        result,
        cube=cube,
        decision_cut_id="AOV0_LOCAL_CUT_TAMPER",
        sealed_at="2026-08-06T18:30:00Z",
        output_dir=tmp_path / "seals",
        contract=development_contract,
    )
    payload = json.loads(seal.path.read_text(encoding="utf-8"))
    payload["decision_cut_id"] = "TAMPERED"
    seal.path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    try:
        import pytest
        with pytest.raises(ValueError, match="aov0_prospective_seal_hash_mismatch"):
            reopen_prospective_seal(seal.path)
    finally:
        pass
