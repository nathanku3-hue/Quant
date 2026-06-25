"""Tests for Rule100 softmax v1.1 scoring (approved expert contract)."""

from __future__ import annotations

import pandas as pd
import pytest

from strategies.rule100_softmax_v1_1 import (
    Rule100SoftmaxV1_1Config,
    V1_1_FACTOR_GROUPS,
    compute_factor_group_counts,
    compute_factor_strength_continuous,
    compute_staleness_penalty,
    compute_technical_quality_continuous,
    lifecycle_state_multiplier,
    score_v1_1_candidates,
    softmax_v1_1_weights,
)


def _candidate_frame() -> pd.DataFrame:
    return pd.DataFrame([
        {"ticker": "AAA", "factor_strength_continuous": 0.8, "technical_quality_continuous": 0.6,
         "hold_intact": 1.0, "staleness_penalty": 0.2, "lifecycle_state": "HOLD"},
        {"ticker": "BBB", "factor_strength_continuous": 0.5, "technical_quality_continuous": 0.4,
         "hold_intact": 1.0, "staleness_penalty": 0.8, "lifecycle_state": "HOLD"},
        {"ticker": "CCC", "factor_strength_continuous": 0.3, "technical_quality_continuous": 0.2,
         "hold_intact": 0.0, "staleness_penalty": 1.0, "lifecycle_state": "TIGHTEN"},
    ])


def test_v1_1_score_formula_matches_contract() -> None:
    scored = score_v1_1_candidates(_candidate_frame())
    by_ticker = scored.set_index("ticker")
    # AAA: 0.50*0.8 + 0.35*0.6 + 0.15*1.0 - 0.10*0.2 = 0.40+0.21+0.15-0.02 = 0.74
    assert by_ticker.loc["AAA", "score_v1_1"] == pytest.approx(0.74)
    # BBB: 0.50*0.5 + 0.35*0.4 + 0.15*1.0 - 0.10*0.8 = 0.25+0.14+0.15-0.08 = 0.46
    assert by_ticker.loc["BBB", "score_v1_1"] == pytest.approx(0.46)
    # CCC: 0.50*0.3 + 0.35*0.2 + 0.15*0.0 - 0.10*1.0 = 0.15+0.07+0-0.10 = 0.12
    assert by_ticker.loc["CCC", "score_v1_1"] == pytest.approx(0.12)


def test_v1_1_no_trim_tighten_in_score() -> None:
    """trim_tighten_penalty is NOT in the score formula (removed per contract)."""
    cfg = Rule100SoftmaxV1_1Config()
    assert not hasattr(cfg, "trim_tighten_penalty_weight")


def test_lifecycle_multiplier_values() -> None:
    actions = pd.Series(["BUY", "HOLD", "TRIM", "TIGHTEN", "EXIT", "unknown"])
    result = lifecycle_state_multiplier(actions)
    assert result.iloc[0] == pytest.approx(1.0)   # BUY
    assert result.iloc[1] == pytest.approx(1.0)   # HOLD
    assert result.iloc[2] == pytest.approx(0.75)  # TRIM
    assert result.iloc[3] == pytest.approx(0.50)  # TIGHTEN
    assert result.iloc[4] == pytest.approx(0.0)   # EXIT
    assert result.iloc[5] == pytest.approx(0.0)   # unknown -> 0


def test_lifecycle_multiplier_applied_post_softmax() -> None:
    """TRIM/TIGHTEN reduce weight; freed capital becomes cash (no redistribution)."""
    frame = pd.DataFrame([
        {"ticker": "AAA", "factor_strength_continuous": 0.8, "technical_quality_continuous": 0.6,
         "hold_intact": 1.0, "staleness_penalty": 0.0, "lifecycle_state": "HOLD"},
        {"ticker": "BBB", "factor_strength_continuous": 0.8, "technical_quality_continuous": 0.6,
         "hold_intact": 1.0, "staleness_penalty": 0.0, "lifecycle_state": "TRIM"},
    ])
    weights = softmax_v1_1_weights(frame)
    # Both have same score, so softmax gives equal raw weights
    # AAA: raw * 1.0, BBB: raw * 0.75
    assert weights.iloc[0] > weights.iloc[1]
    # Total should be less than budget (freed capital = cash)
    assert float(weights.sum()) < 0.20  # budget = 0.10 * 2 = 0.20


def test_lifecycle_exit_zeroes_weight() -> None:
    frame = pd.DataFrame([
        {"ticker": "AAA", "factor_strength_continuous": 0.9, "technical_quality_continuous": 0.9,
         "hold_intact": 1.0, "staleness_penalty": 0.0, "lifecycle_state": "EXIT"},
    ])
    weights = softmax_v1_1_weights(frame)
    assert float(weights.sum()) == pytest.approx(0.0)


def test_weights_respect_budget_and_cap() -> None:
    weights = softmax_v1_1_weights(_candidate_frame())
    # Budget = min(1.0, 0.10 * 3) = 0.30 before lifecycle multiplier
    assert float(weights.sum()) <= 0.30
    assert float(weights.max()) <= 0.15 + 1e-12


def test_factor_strength_uses_cross_sectional_percentile() -> None:
    features = pd.DataFrame({
        "z_demand": [1.0, 2.0, 3.0],
        "z_inventory_quality_proxy": [3.0, 2.0, 1.0],
        "z_moat": [1.0, 3.0, 2.0],
        "capital_cycle_score": [0.5, 1.0, 0.2],
    })
    result = compute_factor_strength_continuous(features)
    # Each column ranked, then averaged
    assert len(result) == 3
    assert all(0.0 <= v <= 1.0 for v in result)


def test_factor_strength_shrinks_missing_groups_toward_neutral() -> None:
    features = pd.DataFrame({
        "z_demand": [1.0],
    })

    result = compute_factor_strength_continuous(features)

    assert result.iloc[0] == pytest.approx(0.625)

    all_missing = compute_factor_strength_continuous(pd.DataFrame(index=[0]))
    assert all_missing.iloc[0] == pytest.approx(0.50)


def test_factor_group_counts_do_not_double_count_alternate_columns() -> None:
    features = pd.DataFrame({
        "z_demand": [1.0],
        "z_inventory_quality_proxy": [1.0],
        "z_moat": [1.0],
        "capital_cycle_score": [1.0],
        "quality_composite": [1.0],
    })

    counts = compute_factor_group_counts(features)

    assert len(V1_1_FACTOR_GROUPS) == 4
    assert counts.loc[0, "factor_present_count"] == 4
    assert counts.loc[0, "factor_positive_count"] == 4


def test_technical_quality_four_subgroups() -> None:
    features = pd.DataFrame({
        "resid_mom_60d": [0.1, 0.2, -0.1],
        "rel_strength_60d": [0.3, 0.1, 0.2],
        "dist_sma20": [0.02, 0.05, 0.15],
        "trend_veto": [False, False, True],
        "rsi_14d": [55.0, 30.0, 80.0],
        "yz_vol_20d": [0.15, 0.30, 0.10],
        "realized_vol_21d": [0.15, 0.30, 0.10],
    })
    result = compute_technical_quality_continuous(features)
    assert len(result) == 3
    assert all(0.0 <= v <= 1.0 for v in result)
    # First row: good momentum, close to SMA, ideal RSI, low vol -> highest
    assert result.iloc[0] > result.iloc[2]


def test_staleness_penalty_saturates_at_config() -> None:
    days = pd.Series([0, 60, 120, 200])
    result = compute_staleness_penalty(days, saturation_days=120.0)
    assert result.iloc[0] == pytest.approx(0.0)
    assert result.iloc[1] == pytest.approx(0.5)
    assert result.iloc[2] == pytest.approx(1.0)
    assert result.iloc[3] == pytest.approx(1.0)  # capped


def test_v1_1_audit_retires_history_and_counts_factor_groups(tmp_path) -> None:
    from data.portfolio_lifecycle_log import append_lifecycle_event
    from scripts.rule100_softmax_v1_1_audit import run_v1_1_audit

    lifecycle_path = tmp_path / "lifecycle.jsonl"
    features_path = tmp_path / "features.parquet"
    decision_log_path = tmp_path / "missing_decisions.jsonl"
    output_prefix = tmp_path / "rule100_softmax_v1_1"
    stale_history = output_prefix.with_name(output_prefix.name + "_history.csv")
    retired_history = stale_history.with_name(f"{stale_history.stem}.retired{stale_history.suffix}")

    append_lifecycle_event("AAA", "ENTER", "2026-01-01", 0.10, permno=1, path=lifecycle_path)
    stale_history.write_text("stale,history\n1,2\n", encoding="utf-8")

    pd.DataFrame(
        [
            {
                "date": "2026-01-05",
                "ticker": "AAA",
                "permno": 1,
                "z_demand": 0.5,
                "z_inventory_quality_proxy": 0.2,
                "z_moat": 0.3,
                "capital_cycle_score": 0.4,
                "quality_composite": 0.9,
                "resid_mom_60d": 0.1,
                "rel_strength_60d": 0.2,
                "dist_sma20": 0.01,
                "trend_veto": False,
                "rsi_14d": 55.0,
                "yz_vol_20d": 0.2,
                "realized_vol_21d": 0.2,
            },
        ]
    ).to_parquet(features_path)

    summary = run_v1_1_audit(
        as_of="2026-01-05",
        features_path=features_path,
        lifecycle_path=lifecycle_path,
        decision_log_path=decision_log_path,
        output_prefix=output_prefix,
    )

    assert set(summary["artifacts"]) == {"comparison_csv", "summary_json"}
    assert "history_csv" not in summary["artifacts"]
    assert not stale_history.exists()
    assert retired_history.exists()
    assert summary["retired_artifacts"]["status"] == "retired"

    comparison = pd.read_csv(summary["artifacts"]["comparison_csv"])
    assert comparison.loc[0, "factor_present_count"] == 4
    assert comparison.loc[0, "factor_positive_count"] == 4
