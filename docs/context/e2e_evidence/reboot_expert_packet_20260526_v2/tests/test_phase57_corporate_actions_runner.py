from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.phase57_corporate_actions_runner import CorporateActionsConfig
from scripts.phase57_corporate_actions_runner import build_corporate_action_target_weights
from scripts.phase57_corporate_actions_runner import load_baseline_summary
from scripts.phase57_corporate_actions_runner import select_corporate_action_candidates
from scripts.phase57_corporate_actions_runner import validate_config


def _make_config(tmp_path: Path, **overrides: object) -> CorporateActionsConfig:
    base = CorporateActionsConfig(
        start_date=pd.Timestamp("2015-01-01"),
        end_date=pd.Timestamp("2022-12-31"),
        max_date=pd.Timestamp("2022-12-31"),
        cost_bps=5.0,
        adv_window_days=20,
        adv_usd_min=5_000_000.0,
        event_yield_min=0.005,
        event_yield_max=0.25,
        value_rank_threshold=0.60,
        summary_path=tmp_path / "summary.json",
        evidence_path=tmp_path / "evidence.csv",
        delta_path=tmp_path / "delta.csv",
        baseline_summary_path=tmp_path / "baseline.json",
        features_path=tmp_path / "features.parquet",
        panel_path=tmp_path / "panel.parquet",
        prices_path=tmp_path / "prices.parquet",
    )
    return CorporateActionsConfig(**{**base.__dict__, **overrides})


def test_validate_config_rejects_event_band_order(tmp_path: Path):
    cfg = _make_config(tmp_path, event_yield_min=0.05, event_yield_max=0.01)
    with pytest.raises(ValueError, match="event_yield_max must be > event_yield_min"):
        validate_config(cfg)


def test_select_corporate_action_candidates_applies_band_quality_and_rank(tmp_path: Path):
    cfg = _make_config(tmp_path)
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2020-01-02",
                    "2020-01-02",
                    "2020-01-02",
                    "2020-01-03",
                    "2020-01-03",
                ]
            ),
            "permno": [1, 2, 3, 4, 5],
            "ticker": ["AAA", "BBB", "CCC", "DDD", "EEE"],
            "capital_cycle_score": [0.1, 0.2, 0.3, 0.4, 0.5],
            "quality_pass": [1, 1, 0, 1, 1],
            "adv_usd": [10_000_000.0, 9_000_000.0, 12_000_000.0, 2_000_000.0, 7_000_000.0],
            "corp_action_yield": [0.01, 0.015, 0.02, 0.01, 0.30],
        }
    )

    selected = select_corporate_action_candidates(frame, cfg)

    assert list(selected["permno"]) == [2]
    assert selected.iloc[0]["value_rank_pct"] >= cfg.value_rank_threshold


def test_build_target_weights_reindexes_full_calendar_and_sets_zero_off_event_days():
    selected = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-02", "2020-01-02", "2020-01-06"]),
            "permno": [10, 20, 20],
            "score_valid": [True, True, True],
        }
    )
    calendar = pd.DatetimeIndex(
        pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"]),
        name="date",
    )

    weights = build_corporate_action_target_weights(selected, calendar)

    assert list(weights.index) == list(calendar)
    assert weights.loc[pd.Timestamp("2020-01-02")].sum() == pytest.approx(1.0)
    assert weights.loc[pd.Timestamp("2020-01-03")].sum() == pytest.approx(0.0)
    assert weights.loc[pd.Timestamp("2020-01-06")].sum() == pytest.approx(1.0)
    assert set(weights.columns) == {10, 20}


def test_load_baseline_summary_rejects_window_mismatch(tmp_path: Path):
    cfg = _make_config(tmp_path)
    payload = {
        "window": {"start_date": "2020-01-01", "end_date": "2022-12-31"},
        "cost_bps": 5.0,
        "baseline_config_id": "C3_LEAKY_INTEGRATOR_V1",
        "metrics": {
            "c3": {
                "sharpe": 0.1,
                "cagr": 0.2,
                "max_dd": -0.3,
                "ulcer": 1.0,
                "turnover_annual": 2.0,
                "turnover_total": 3.0,
            }
        },
    }
    cfg.baseline_summary_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.baseline_summary_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="Baseline window mismatch"):
        load_baseline_summary(cfg)
