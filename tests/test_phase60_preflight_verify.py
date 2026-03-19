from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts import phase60_preflight_verify as mod


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def test_preflight_passes_on_valid_cube(tmp_path: Path):
    cube_path = tmp_path / "cube.csv"
    daily_path = tmp_path / "daily.csv"
    summary_path = tmp_path / "summary.json"
    output_path = tmp_path / "out.json"

    _write_csv(
        cube_path,
        pd.DataFrame(
            {
                "date": ["2022-12-30"],
                "book_id": [mod.EXPECTED_BOOK_ID],
                "sleeve_id": ["phase56_event_pead"],
                "permno": [1],
                "ticker": ["AAA"],
                "eligibility_state": ["governed_active__allocator_blocked"],
                "sleeve_weight_pre_allocator": [1.0],
                "allocator_overlay_weight": [0.0],
                "book_weight_final": [1.0],
                "gross_exposure": [1.0],
                "turnover_component": [1.0],
                "source_artifact": ["phase56.json"],
            }
        ),
    )
    _write_csv(
        daily_path,
        pd.DataFrame(
            {
                "date": ["2022-12-30"],
                "book_id": [mod.EXPECTED_BOOK_ID],
                "gross_exposure": [1.0],
                "turnover_total": [1.0],
                "n_active_permnos": [1],
                "allocator_overlay_applied": [False],
            }
        ),
    )
    summary_path.write_text(
        json.dumps(
            {
                "packet_id": mod.EXPECTED_PACKET_ID,
                "cost_bps_gate": 5.0,
                "start_date": "2015-01-01",
                "end_date": "2022-12-31",
                "max_date": "2022-12-31",
                "cube_path": str(cube_path),
                "daily_path": str(daily_path),
                "summary_path": str(summary_path),
                "core_sleeve_included": False,
                "allocator_overlay_applied": False,
            }
        ),
        encoding="utf-8",
    )

    out = mod.run_preflight(
        mod.PreflightConfig(
            cube_path=cube_path,
            daily_path=daily_path,
            summary_path=summary_path,
            output_path=output_path,
        )
    )
    assert out["passed"] is True


def test_preflight_blocks_phase50_fill(tmp_path: Path):
    cube_path = tmp_path / "cube.csv"
    daily_path = tmp_path / "daily.csv"
    summary_path = tmp_path / "summary.json"
    output_path = tmp_path / "out.json"

    _write_csv(
        cube_path,
        pd.DataFrame(
            {
                "date": ["2022-12-30"],
                "book_id": [mod.EXPECTED_BOOK_ID],
                "sleeve_id": ["phase56_event_pead"],
                "permno": [1],
                "ticker": ["AAA"],
                "eligibility_state": ["governed_active__allocator_blocked"],
                "sleeve_weight_pre_allocator": [1.0],
                "allocator_overlay_weight": [0.0],
                "book_weight_final": [1.0],
                "gross_exposure": [1.0],
                "turnover_component": [1.0],
                "source_artifact": ["phase50_shadow_ship"],
            }
        ),
    )
    _write_csv(
        daily_path,
        pd.DataFrame(
            {
                "date": ["2022-12-30"],
                "book_id": [mod.EXPECTED_BOOK_ID],
                "gross_exposure": [1.0],
                "turnover_total": [1.0],
                "n_active_permnos": [1],
                "allocator_overlay_applied": [False],
            }
        ),
    )
    summary_path.write_text(
        json.dumps(
            {
                "packet_id": mod.EXPECTED_PACKET_ID,
                "cost_bps_gate": 5.0,
                "start_date": "2015-01-01",
                "end_date": "2022-12-31",
                "max_date": "2022-12-31",
                "cube_path": str(cube_path),
                "daily_path": str(daily_path),
                "summary_path": str(summary_path),
                "core_sleeve_included": False,
                "allocator_overlay_applied": False,
            }
        ),
        encoding="utf-8",
    )

    out = mod.run_preflight(
        mod.PreflightConfig(
            cube_path=cube_path,
            daily_path=daily_path,
            summary_path=summary_path,
            output_path=output_path,
        )
    )
    assert out["passed"] is False
