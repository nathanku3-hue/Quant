from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from scripts.phase56_pead_runner import PeadConfig
from scripts.phase56_pead_runner import RESEARCH_MAX_DATE
from scripts.phase56_pead_runner import build_pead_target_weights
from scripts.phase56_pead_runner import select_pead_candidates
from scripts.phase56_pead_runner import summarize_simulation
from scripts.phase56_pead_runner import validate_config


def _cfg() -> PeadConfig:
    return PeadConfig(
        start_date=pd.Timestamp("2000-01-01"),
        end_date=pd.Timestamp("2000-01-31"),
        max_date=pd.Timestamp("2022-12-31"),
        cost_bps=5.0,
        adv_window_days=20,
        adv_usd_min=5_000_000.0,
        max_days_since_earnings=63,
        value_rank_threshold=0.60,
        summary_path=Path("data/processed/phase56_pead_summary.json"),
        evidence_path=Path("data/processed/phase56_pead_evidence.csv"),
    )


def test_validate_config_rejects_post_2022_end_date():
    cfg = _cfg()
    bad = PeadConfig(
        **{
            **cfg.__dict__,
            "end_date": pd.Timestamp("2023-01-03"),
            "max_date": RESEARCH_MAX_DATE,
        }
    )
    with pytest.raises(ValueError, match="end_date must be <="):
        validate_config(bad)


def test_select_pead_candidates_applies_quality_adv_days_and_rank_gates():
    cfg = _cfg()
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2000-01-03",
                    "2000-01-03",
                    "2000-01-03",
                    "2000-01-03",
                    "2000-01-03",
                ]
            ),
            "permno": [1, 2, 3, 4, 5],
            "ticker": ["A", "B", "C", "D", "E"],
            "capital_cycle_score": [1.0, 2.0, 3.0, 4.0, 5.0],
            "z_inventory_quality_proxy": [0.1] * 5,
            "adv_usd": [6_000_000, 6_000_000, 6_000_000, 1_000_000, 6_000_000],
            "days_since_earnings": [10, 10, 10, 10, 100],
            "quality_pass": [1, 1, 1, 1, 0],
            "release_date": pd.to_datetime(["1999-12-31"] * 5),
        }
    )

    out = select_pead_candidates(frame, cfg)

    assert list(out["permno"]) == [2, 3]
    assert out["value_rank_pct"].tolist() == pytest.approx([2 / 3, 1.0])


def test_build_pead_target_weights_equal_weights_per_day():
    selected = pd.DataFrame(
        {
            "date": pd.to_datetime(["2000-01-03", "2000-01-03", "2000-01-04"]),
            "permno": [1, 2, 3],
            "score_valid": [True, True, True],
        }
    )

    weights = build_pead_target_weights(selected)

    assert float(weights.loc[pd.Timestamp("2000-01-03"), 1]) == pytest.approx(0.5)
    assert float(weights.loc[pd.Timestamp("2000-01-03"), 2]) == pytest.approx(0.5)
    assert float(weights.loc[pd.Timestamp("2000-01-04"), 3]) == pytest.approx(1.0)


def test_summarize_simulation_reports_expected_fields():
    cfg = _cfg()
    idx = pd.date_range("2000-01-03", periods=3, freq="B")
    sim = pd.DataFrame(
        {
            "gross_ret": [0.0, 0.01, -0.02],
            "net_ret": [0.0, 0.0095, -0.0205],
            "turnover": [0.0, 1.0, 0.5],
            "cost": [0.0, 0.0005, 0.0005],
        },
        index=idx,
    )
    weights = pd.DataFrame({1: [0.0, 1.0, 1.0]}, index=idx)
    selected = pd.DataFrame({"date": idx, "permno": [1, 1, 1]})

    summary = summarize_simulation(sim=sim, weights=weights, selected=selected, cfg=cfg)

    assert summary["strategy_id"] == "PHASE56_PEAD_CAPITAL_CYCLE_V1"
    assert summary["candidate_rows"] == 3
    assert summary["candidate_permnos"] == 1
    assert summary["avg_positions"] == pytest.approx(2 / 3)
    assert "sharpe" in summary
