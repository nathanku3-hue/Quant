from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from data.phase59_shadow_portfolio import ShadowPortfolioConfig
from data.phase59_shadow_portfolio import build_phase59_packet
from data.phase59_shadow_portfolio import select_phase55_variant


def test_select_phase55_variant_ranks_deterministically(tmp_path: Path):
    evidence_path = tmp_path / "phase55_evidence.json"
    evidence_path.write_text(
        json.dumps(
            {
                "fold_results": [
                    {"selected_variant": "B", "outer_test_sharpe": 0.2, "positive_outer_fold": True},
                    {"selected_variant": "A", "outer_test_sharpe": 0.5, "positive_outer_fold": True},
                    {"selected_variant": "B", "outer_test_sharpe": 0.3, "positive_outer_fold": False},
                    {"selected_variant": "A", "outer_test_sharpe": 0.4, "positive_outer_fold": False},
                    {"selected_variant": "A", "outer_test_sharpe": 0.3, "positive_outer_fold": True},
                ]
            }
        ),
        encoding="utf-8",
    )
    cfg = ShadowPortfolioConfig(
        start_date=pd.Timestamp("2015-01-01"),
        end_date=pd.Timestamp("2022-12-31"),
        max_date=pd.Timestamp("2022-12-31"),
        cost_bps=5.0,
        phase55_evidence_path=evidence_path,
    )

    winner = select_phase55_variant(cfg)

    assert winner["variant_id"] == "A"
    assert winner["selection_count"] == 3


def test_build_phase59_packet_on_repo_surface(tmp_path: Path):
    cfg = ShadowPortfolioConfig(
        start_date=pd.Timestamp("2015-01-01"),
        end_date=pd.Timestamp("2022-12-31"),
        max_date=pd.Timestamp("2022-12-31"),
        cost_bps=5.0,
        summary_path=tmp_path / "summary.json",
        evidence_path=tmp_path / "evidence.csv",
        delta_path=tmp_path / "delta.csv",
    )

    summary, evidence_frame, delta_frame = build_phase59_packet(cfg)

    assert summary["packet_id"] == "PHASE59_SHADOW_MONITOR_V1"
    assert summary["same_window_same_cost_same_engine"] is True
    assert summary["catalog_rows"] >= 100_000
    assert summary["selected_variant"]["variant_id"].startswith("v_")
    assert summary["shadow_reference"]["reference_only"] is True
    assert 0.0 <= summary["shadow_reference"]["holdings_overlap"] <= 1.0
    assert set(evidence_frame["surface_id"]) == {
        "phase59_shadow_research",
        "phase50_shadow_reference",
    }
    assert set(delta_frame["surface_id"]) == {
        "phase59_shadow_research",
        "phase50_shadow_reference_alerts",
    }
    assert bool(summary["review_hold"]) is True
