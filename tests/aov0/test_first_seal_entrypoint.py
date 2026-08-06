from __future__ import annotations

from pathlib import Path

from scripts.aov0_first_seal import run_first_seal


def test_first_real_seal_blocks_on_missing_admitted_inputs(tmp_path: Path) -> None:
    result = run_first_seal(input_root=tmp_path / "missing", output_root=tmp_path / "out")
    assert result == {
        "status": "BLOCKED_OWNER_DECISION_AND_ADMITTED_INPUTS",
        "alpha_evidence": 0,
        "prospective_clock_started": False,
        "owner_decisions_required": [
            "insurance_materiality_floor_ratio",
            "insurance_premium_ceiling_annual_return",
        ],
        "missing": [
            "rule100_targets",
            "vertical_primitives",
            "total_returns",
            "official_sofr",
            "decision_cut",
        ],
        "required_paths": {
            "rule100_targets": (tmp_path / "missing/rule100_targets.parquet").as_posix(),
            "vertical_primitives": (tmp_path / "missing/vertical_primitives.parquet").as_posix(),
            "total_returns": (tmp_path / "missing/total_returns.parquet").as_posix(),
            "official_sofr": (tmp_path / "missing/official_sofr.parquet").as_posix(),
            "decision_cut": (tmp_path / "missing/decision_cut.json").as_posix(),
        },
    }
    assert not (tmp_path / "out").exists()
