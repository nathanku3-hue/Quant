from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from scripts.phase58_governance_runner import GovernanceConfig
from scripts.phase58_governance_runner import build_event_return_matrix
from scripts.phase58_governance_runner import build_review_hold_reasons
from scripts.phase58_governance_runner import validate_config


def _make_config(tmp_path: Path, **overrides: object) -> GovernanceConfig:
    base = GovernanceConfig(
        start_date=pd.Timestamp("2015-01-01"),
        end_date=pd.Timestamp("2022-12-31"),
        max_date=pd.Timestamp("2022-12-31"),
        cost_bps=5.0,
        summary_path=tmp_path / "summary.json",
        evidence_path=tmp_path / "evidence.csv",
        delta_path=tmp_path / "delta.csv",
        baseline_summary_path=tmp_path / "baseline.json",
        phase55_summary_path=tmp_path / "phase55.json",
    )
    return GovernanceConfig(**{**base.__dict__, **overrides})


def test_validate_config_rejects_guard_breach(tmp_path: Path):
    cfg = _make_config(tmp_path, max_date=pd.Timestamp("2023-01-01"))
    with pytest.raises(ValueError, match="max_date must be <="):
        validate_config(cfg)


def test_build_event_return_matrix_aligns_on_union_and_zero_fills(tmp_path: Path):
    pead = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-02", "2020-01-03"]),
            "net_ret": [0.01, -0.02],
        }
    )
    corp = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-03", "2020-01-06"]),
            "net_ret": [0.03, 0.04],
        }
    )
    pead_path = tmp_path / "pead.csv"
    corp_path = tmp_path / "corp.csv"
    pead.to_csv(pead_path, index=False)
    corp.to_csv(corp_path, index=False)

    matrix = build_event_return_matrix(pead_path, corp_path)

    assert list(matrix.index) == list(pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]))
    assert matrix.loc[pd.Timestamp("2020-01-02"), "phase57_corporate_actions"] == pytest.approx(0.0)
    assert matrix.loc[pd.Timestamp("2020-01-06"), "phase56_pead"] == pytest.approx(0.0)


def test_build_review_hold_reasons_collects_family_and_sleeve_failures():
    delta = pd.DataFrame(
        [
            {
                "sleeve_id": "phase56_event_pead",
                "sharpe_delta": 0.1,
                "cagr_delta": 0.2,
            },
            {
                "sleeve_id": "phase57_event_corporate_actions",
                "sharpe_delta": -0.1,
                "cagr_delta": -0.2,
            },
        ]
    )

    reasons = build_review_hold_reasons(delta, family_spa_p=0.06, family_wrc_p=0.07)

    assert "event_family_spa_p >= 0.05" in reasons
    assert "event_family_wrc_p >= 0.05" in reasons
    assert "phase57_event_corporate_actions_sharpe_delta < 0" in reasons
    assert "phase57_event_corporate_actions_cagr_delta < 0" in reasons
