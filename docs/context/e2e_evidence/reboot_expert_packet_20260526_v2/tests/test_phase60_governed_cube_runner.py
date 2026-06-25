from __future__ import annotations

import pandas as pd
import pytest

from scripts import phase60_governed_cube_runner as mod


def test_validate_config_rejects_non_gating_cost():
    cfg = mod.GovernedCubeConfig(
        start_date=pd.Timestamp("2015-01-01"),
        end_date=pd.Timestamp("2022-12-31"),
        max_date=pd.Timestamp("2022-12-31"),
        cost_bps=10.0,
    )
    with pytest.raises(ValueError, match="5.0 bps"):
        mod.validate_config(cfg)


def test_build_cube_rows_zero_overlay_and_exit_turnover():
    calendar = pd.DatetimeIndex(pd.to_datetime(["2022-01-03", "2022-01-04", "2022-01-05"]), name="date")
    pead_weights = pd.DataFrame({101: [0.5, 0.0, 0.0]}, index=calendar)
    corp_weights = pd.DataFrame({101: [0.0, 0.25, 0.0], 202: [0.5, 0.5, 0.0]}, index=calendar)
    meta = pd.DataFrame(
        {
            "date": pd.to_datetime(["2022-01-03", "2022-01-04", "2022-01-03"]),
            "permno": [101, 101, 202],
            "ticker": ["AAA", "AAA", "BBB"],
            "sleeve_id": [mod.SLEEVE_PHASE56, mod.SLEEVE_PHASE57, mod.SLEEVE_PHASE57],
            "source_artifact": ["p56", "p57", "p57"],
        }
    )

    cube, daily = mod._build_cube_rows(
        calendar=calendar,
        pead_weights=pead_weights,
        corp_weights=corp_weights,
        meta=meta,
    )

    assert cube["allocator_overlay_weight"].abs().sum() == pytest.approx(0.0)
    first_101 = cube[(cube["date"] == pd.Timestamp("2022-01-03")) & (cube["permno"] == 101)].iloc[0]
    second_101 = cube[(cube["date"] == pd.Timestamp("2022-01-04")) & (cube["permno"] == 101)].iloc[0]
    exit_202 = cube[(cube["date"] == pd.Timestamp("2022-01-05")) & (cube["permno"] == 202)].iloc[0]

    assert first_101["book_weight_final"] == pytest.approx(0.5)
    assert first_101["turnover_component"] == pytest.approx(0.5)
    assert second_101["book_weight_final"] == pytest.approx(0.25)
    assert second_101["turnover_component"] == pytest.approx(0.25)
    assert exit_202["book_weight_final"] == pytest.approx(0.0)
    assert exit_202["turnover_component"] == pytest.approx(0.5)
    assert exit_202["eligibility_state"] == "turnover_exit__allocator_blocked"
    assert daily.loc[daily["date"] == pd.Timestamp("2022-01-03"), "gross_exposure"].iloc[0] == pytest.approx(1.0)


def test_selected_metadata_normalizes_and_deduplicates():
    selected = pd.DataFrame(
        {
            "date": pd.to_datetime(["2022-01-03", "2022-01-03"]),
            "permno": [101, 101],
            "ticker": ["aaa", "AAA"],
        }
    )
    out = mod._selected_metadata(selected, sleeve_id="phase56_event_pead", source_artifact="artifact.json")
    assert len(out) == 1
    assert out.iloc[0]["ticker"] == "AAA"
    assert out.iloc[0]["permno"] == 101
