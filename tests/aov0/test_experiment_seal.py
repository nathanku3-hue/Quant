from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import json
from pathlib import Path

import pandas as pd
import pytest

from core.gv_fs0_canonical import domain_hash
from research.aov0.cube import build_vertical_cube
from research.aov0.experiment import (
    RETURN_INTERVAL_POLICY,
    reopen_prospective_seal,
    run_five_arm_experiment,
    seal_prospective_experiment,
    validate_attributed_return_intervals,
)


COMPUTED_AT = "2026-08-06T18:00:00Z"
SEAL_TIME = datetime(2026, 8, 6, 18, 30, tzinfo=UTC)
EVALUATION_START = "2026-08-06T20:00:00Z"


def _decision_cut_binding(result, *, cut_id: str) -> dict[str, object]:
    return {
        "schema_version": "aov0_ciq_decision_cut_v3",
        "decision_cut_id": cut_id,
        "knowledge_cutoff": "2026-08-06T18:00:00Z",
        "cut_built_at": "2026-08-06T18:20:00Z",
        "decision_target_date": result.current_target_date,
        "evaluation_start": EVALUATION_START,
        "execution_calendar_id": "NYSE_2026_CORE_CLOSE_1600_ET",
        "inputs": {
            name: {"path": f"{name}.parquet", "bytes": 1, "sha256": "0" * 64}
            for name in ("rule100_targets", "vertical_primitives", "total_returns", "official_sofr")
        },
        "decision_cut_artifact": {"path": "decision_cut.json", "bytes": 1, "sha256": "1" * 64},
    }


def _executable_manifest(tmp_path: Path) -> Path:
    path = tmp_path / "executable_manifest.json"
    path.write_text("{}\n", encoding="utf-8")
    return path


def _experiment(
    tmp_path: Path,
    *,
    aov_primitives,
    rule100_weights,
    aov_returns,
    economic_cash_returns,
    development_contract,
):
    cube = build_vertical_cube(aov_primitives, computed_at=COMPUTED_AT)
    result = run_five_arm_experiment(
        rule100_weights=rule100_weights,
        returns_df=aov_returns,
        economic_cash_returns=economic_cash_returns,
        cube=cube,
        pit_eligibility_provider=lambda _date: ("CIQSEC:101", "CIQSEC:202"),
        output_root=tmp_path / "evidence",
        contract=development_contract,
    )
    return cube, result


def test_five_arm_experiment_emits_hash_bound_evidence_and_v3_seal_candidate(
    tmp_path: Path,
    aov_primitives,
    rule100_weights,
    aov_returns,
    economic_cash_returns,
    development_contract,
) -> None:
    cube, result = _experiment(
        tmp_path,
        aov_primitives=aov_primitives,
        rule100_weights=rule100_weights,
        aov_returns=aov_returns,
        economic_cash_returns=economic_cash_returns,
        development_contract=development_contract,
    )
    assert set(result.arm_metrics) == {
        "rule100",
        "parent",
        "child",
        "pit_equal_weight",
        "economic_cash",
    }
    for run in result.runs.values():
        manifest = Path(run.artifacts["evidence_manifest.json"])
        assert manifest.is_file()
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        assert payload["schema_version"] == "research_evidence_manifest_v1"
        assert "evidence_packet.json" in payload["files"]

    experiment = json.loads(result.experiment_manifest.read_text(encoding="utf-8"))
    assert experiment["financial_alpha_evidence"] == 0
    assert set(experiment["current_decision_targets"]["arm_target_vectors"]) == {
        "rule100",
        "parent",
        "child",
        "pit_equal_weight",
        "economic_cash",
    }

    seal = seal_prospective_experiment(
        result,
        cube=cube,
        decision_cut_binding=_decision_cut_binding(result, cut_id="AOV0_LOCAL_CUT_20260806"),
        executable_manifest=_executable_manifest(tmp_path),
        output_dir=tmp_path / "seals",
        contract=development_contract,
        sealed_at=SEAL_TIME,
    )
    reopened = reopen_prospective_seal(seal.path)
    assert reopened == seal.payload
    assert reopened["schema_version"] == "aov0_prospective_seal_v3"
    assert reopened["sealed_at"] == "2026-08-06T18:30:00Z"
    assert reopened["evaluation_start"] == EVALUATION_START
    assert reopened["return_interval_policy"] == RETURN_INTERVAL_POLICY
    assert reopened["outcome_status"] == "SEALED_NOT_OPENED"
    assert reopened["outcome_data_loaded"] is False
    assert reopened["outcome_open_not_before"] == "2026-09-05T20:00:00Z"
    assert reopened["evidence_level"] == "PROSPECTIVE_SEAL_CANDIDATE_FINANCIAL_ALPHA_EVIDENCE_0"
    assert reopened["financial_alpha_evidence"] == 0
    assert "prospective_clock_started" not in reopened
    assert reopened["current_decision_target_hashes"] == result.current_target_hashes
    assert len(reopened["seal_id"]) == 64


def test_seal_rejects_actual_write_time_at_or_after_evaluation_start(
    tmp_path: Path,
    aov_primitives,
    rule100_weights,
    aov_returns,
    economic_cash_returns,
    development_contract,
) -> None:
    cube, result = _experiment(
        tmp_path,
        aov_primitives=aov_primitives,
        rule100_weights=rule100_weights,
        aov_returns=aov_returns,
        economic_cash_returns=economic_cash_returns,
        development_contract=development_contract,
    )
    with pytest.raises(ValueError, match="aov0_prospective_seal_timing_invalid"):
        seal_prospective_experiment(
            result,
            cube=cube,
            decision_cut_binding=_decision_cut_binding(result, cut_id="AOV0_LOCAL_CUT_LATE"),
            executable_manifest=_executable_manifest(tmp_path),
            output_dir=tmp_path / "seals",
            contract=development_contract,
            sealed_at=datetime(2026, 8, 6, 20, 0, tzinfo=UTC),
        )


def test_seal_hash_tamper_fails_closed(
    tmp_path: Path,
    aov_primitives,
    rule100_weights,
    aov_returns,
    economic_cash_returns,
    development_contract,
) -> None:
    cube, result = _experiment(
        tmp_path,
        aov_primitives=aov_primitives,
        rule100_weights=rule100_weights,
        aov_returns=aov_returns,
        economic_cash_returns=economic_cash_returns,
        development_contract=development_contract,
    )
    seal = seal_prospective_experiment(
        result,
        cube=cube,
        decision_cut_binding=_decision_cut_binding(result, cut_id="AOV0_LOCAL_CUT_TAMPER"),
        executable_manifest=_executable_manifest(tmp_path),
        output_dir=tmp_path / "seals",
        contract=development_contract,
        sealed_at=SEAL_TIME,
    )
    payload = json.loads(seal.path.read_text(encoding="utf-8"))
    payload["decision_cut_id"] = "TAMPERED"
    seal.path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="aov0_prospective_seal_hash_mismatch"):
        reopen_prospective_seal(seal.path)


def test_self_consistent_early_maturity_is_rejected_semantically(
    tmp_path: Path,
    aov_primitives,
    rule100_weights,
    aov_returns,
    economic_cash_returns,
    development_contract,
) -> None:
    cube, result = _experiment(
        tmp_path,
        aov_primitives=aov_primitives,
        rule100_weights=rule100_weights,
        aov_returns=aov_returns,
        economic_cash_returns=economic_cash_returns,
        development_contract=development_contract,
    )
    seal = seal_prospective_experiment(
        result,
        cube=cube,
        decision_cut_binding=_decision_cut_binding(result, cut_id="AOV0_LOCAL_CUT_EARLY_MATURITY"),
        executable_manifest=_executable_manifest(tmp_path),
        output_dir=tmp_path / "seals",
        contract=development_contract,
        sealed_at=SEAL_TIME,
    )
    payload = json.loads(seal.path.read_text(encoding="utf-8"))
    payload["outcome_open_not_before"] = "2026-09-04T20:00:00Z"
    body = {key: value for key, value in payload.items() if key != "seal_id"}
    payload["seal_id"] = domain_hash("AOV0:PROSPECTIVE_SEAL:V3", body)
    seal.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="aov0_prospective_outcome_maturity_invalid"):
        reopen_prospective_seal(seal.path)


def test_attributed_return_interval_before_evaluation_start_is_rejected() -> None:
    intervals = pd.DataFrame(
        {
            "interval_start": ["2026-08-06T19:59:59Z"],
            "interval_end": ["2026-08-07T20:00:00Z"],
        }
    )
    with pytest.raises(ValueError, match="begins_before_evaluation_start"):
        validate_attributed_return_intervals(intervals, evaluation_start=EVALUATION_START)


def test_attributed_return_interval_at_evaluation_start_is_admitted() -> None:
    intervals = pd.DataFrame(
        {
            "interval_start": [EVALUATION_START],
            "interval_end": ["2026-08-07T20:00:00Z"],
        }
    )
    validate_attributed_return_intervals(intervals, evaluation_start=EVALUATION_START)


def test_proxy_cash_authority_is_rejected_before_seal(
    tmp_path: Path,
    aov_primitives,
    rule100_weights,
    aov_returns,
    economic_cash_returns,
    development_contract,
) -> None:
    cube, result = _experiment(
        tmp_path,
        aov_primitives=aov_primitives,
        rule100_weights=rule100_weights,
        aov_returns=aov_returns,
        economic_cash_returns=economic_cash_returns,
        development_contract=development_contract,
    )
    bad_contract = replace(development_contract, economic_cash_source="ETF_PROXY")
    with pytest.raises(ValueError, match="aov0_economic_cash_source_invalid"):
        seal_prospective_experiment(
            result,
            cube=cube,
            decision_cut_binding=_decision_cut_binding(result, cut_id="AOV0_BAD_CASH"),
            executable_manifest=_executable_manifest(tmp_path),
            output_dir=tmp_path / "seals",
            contract=bad_contract,
            sealed_at=SEAL_TIME,
        )


def test_v2_seal_schema_has_no_active_reopen_compatibility(
    tmp_path: Path,
    aov_primitives,
    rule100_weights,
    aov_returns,
    economic_cash_returns,
    development_contract,
) -> None:
    cube, result = _experiment(
        tmp_path,
        aov_primitives=aov_primitives,
        rule100_weights=rule100_weights,
        aov_returns=aov_returns,
        economic_cash_returns=economic_cash_returns,
        development_contract=development_contract,
    )
    seal = seal_prospective_experiment(
        result,
        cube=cube,
        decision_cut_binding=_decision_cut_binding(result, cut_id="AOV0_NO_V2_COMPAT"),
        executable_manifest=_executable_manifest(tmp_path),
        output_dir=tmp_path / "seals",
        contract=development_contract,
        sealed_at=SEAL_TIME,
    )
    payload = json.loads(seal.path.read_text(encoding="utf-8"))
    payload["schema_version"] = "aov0_prospective_seal_v2"
    seal.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="aov0_prospective_seal_schema_invalid"):
        reopen_prospective_seal(seal.path)
