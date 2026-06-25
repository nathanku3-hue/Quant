from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from strategies.rule100_softmax import (
    Rule100SoftmaxConfig,
    cap_and_redistribute,
    compare_softmax_and_kelly,
    gross_budget_for_count,
    kelly_ablation_weights,
    rule100_config_from_max_weight,
    score_rule100_candidates,
    softmax_v1_weights,
    stable_softmax,
)


def _candidate_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ticker": "AAA", "permno": 1, "factor_positive_count": 3, "technical_quality": 0.2},
            {"ticker": "BBB", "permno": 2, "factor_positive_count": 3, "technical_quality": 1.0},
            {"ticker": "CCC", "permno": 3, "factor_positive_count": 4, "technical_quality": 0.4},
            {"ticker": "DDD", "permno": 4, "factor_positive_count": 4, "technical_quality": 1.0},
        ]
    )


def test_rule100_softmax_score_uses_v1_formula() -> None:
    scored = score_rule100_candidates(_candidate_frame())

    by_ticker = scored.set_index("ticker")
    assert by_ticker.loc["AAA", "score"] == pytest.approx(0.05)
    assert by_ticker.loc["BBB", "score"] == pytest.approx(0.25)
    assert by_ticker.loc["CCC", "score"] == pytest.approx(0.85)
    assert by_ticker.loc["DDD", "score"] == pytest.approx(1.00)


def test_rule100_softmax_requires_explicit_inputs() -> None:
    with pytest.raises(ValueError, match="factor_positive_count"):
        score_rule100_candidates(pd.DataFrame({"technical_quality": [1.0]}))

    with pytest.raises(ValueError, match="technical_quality"):
        score_rule100_candidates(pd.DataFrame({"factor_positive_count": [4]}))


def test_stable_softmax_handles_non_finite_values() -> None:
    probs = stable_softmax([float("nan"), float("inf"), -float("inf")], temperature=1.0)

    assert probs.tolist() == pytest.approx([1 / 3, 1 / 3, 1 / 3])


def test_stable_softmax_rejects_non_positive_temperature() -> None:
    with pytest.raises(ValueError, match="temperature"):
        stable_softmax([1.0, 2.0], temperature=0.0)


def test_cap_and_redistribute_preserves_budget_when_feasible() -> None:
    raw = pd.Series({"AAA": 0.37, "BBB": 0.01, "CCC": 0.01, "DDD": 0.01})

    capped = cap_and_redistribute(raw, cap=0.15)

    assert float(capped.sum()) == pytest.approx(0.40)
    assert float(capped.max()) <= 0.15 + 1e-12
    assert capped["AAA"] == pytest.approx(0.15)


def test_softmax_v1_weights_sum_to_budget_and_reserve_cash() -> None:
    weights = softmax_v1_weights(_candidate_frame())

    assert float(weights.sum()) == pytest.approx(0.40)
    assert float(weights.max()) <= 0.15 + 1e-12
    assert gross_budget_for_count(4) == pytest.approx(0.40)


def test_rule100_ui_replay_config_allows_single_name_to_reach_max_weight() -> None:
    frame = pd.DataFrame(
        [{"ticker": "AAA", "permno": 1, "factor_positive_count": 3, "technical_quality": 1.0}]
    )

    weights = softmax_v1_weights(frame, rule100_config_from_max_weight(0.35))

    assert float(weights.sum()) == pytest.approx(0.35)
    assert float(weights.iloc[0]) == pytest.approx(0.35)


def test_rule100_ui_replay_config_equal_names_use_cap_budget_and_cash() -> None:
    frame = pd.DataFrame(
        [
            {"ticker": "AAA", "permno": 1, "factor_positive_count": 3, "technical_quality": 1.0},
            {"ticker": "BBB", "permno": 2, "factor_positive_count": 3, "technical_quality": 1.0},
        ]
    )

    weights = softmax_v1_weights(frame, rule100_config_from_max_weight(0.35))

    assert weights.tolist() == pytest.approx([0.35, 0.35])
    assert float(1.0 - weights.sum()) == pytest.approx(0.30)


def test_rule100_audit_default_budget_stays_frozen_at_ten_percent_per_name() -> None:
    frame = pd.DataFrame(
        [
            {"ticker": "AAA", "permno": 1, "factor_positive_count": 3, "technical_quality": 1.0},
            {"ticker": "BBB", "permno": 2, "factor_positive_count": 3, "technical_quality": 1.0},
        ]
    )

    weights = softmax_v1_weights(frame)

    assert weights.tolist() == pytest.approx([0.10, 0.10])
    assert float(1.0 - weights.sum()) == pytest.approx(0.80)


def test_kelly_ablation_is_thin_comparator_on_same_harness() -> None:
    frame = _candidate_frame()
    softmax = softmax_v1_weights(frame)
    kelly = kelly_ablation_weights(frame)

    assert float(kelly.sum()) < float(softmax.sum())
    assert int((kelly > 0).sum()) < int((softmax > 0).sum())
    assert float(kelly.max()) >= float(softmax.max())


def test_compare_softmax_and_kelly_is_deterministic_and_auditable() -> None:
    shuffled = _candidate_frame().sample(frac=1.0, random_state=7).reset_index(drop=True)

    comparison, summary = compare_softmax_and_kelly(shuffled)

    assert comparison["ticker"].tolist() == ["DDD", "CCC", "BBB", "AAA"]
    assert "softmax_weight" in comparison.columns
    assert "kelly_weight" in comparison.columns
    assert summary["kelly_comparator_only"] is True
    assert summary["eligible_count"] == 4
    assert summary["gross_budget"] == pytest.approx(0.40)
    assert summary["softmax"]["cash_residual"] == pytest.approx(0.60)
    assert summary["kelly_ablation"]["nonzero_names"] == 2
    assert summary["kelly_ablation"]["cash_residual"] == pytest.approx(0.70)


def test_optional_penalty_columns_are_configurable_not_standalone_stack() -> None:
    frame = pd.DataFrame(
        [
            {
                "ticker": "AAA",
                "factor_positive_count": 4,
                "technical_quality": 1.0,
                "hold_intact": 1.0,
                "age_penalty": 0.5,
                "trim_penalty": 1.0,
            }
        ]
    )
    cfg = Rule100SoftmaxConfig(hold_weight=0.10, age_penalty_weight=0.20, trim_penalty_weight=0.30)

    scored = score_rule100_candidates(frame, cfg)

    assert scored["score"].iloc[0] == pytest.approx(1.0 + 0.10 - 0.10 - 0.30)


def test_rule100_softmax_v1_audit_writes_single_shared_harness_artifacts(tmp_path) -> None:
    from data.portfolio_lifecycle_log import append_lifecycle_event
    from scripts.rule100_softmax_v1_audit import run_rule100_softmax_v1_audit

    lifecycle_path = tmp_path / "lifecycle.jsonl"
    features_path = tmp_path / "features.parquet"
    output_prefix = tmp_path / "rule100_softmax_v1"

    append_lifecycle_event("AAA", "ENTER", "2026-01-01", 0.10, permno=1, path=lifecycle_path)
    append_lifecycle_event("BBB", "ENTER", "2026-01-01", 0.10, permno=2, path=lifecycle_path)

    pd.DataFrame(
        [
            {
                "date": "2026-01-05",
                "ticker": "AAA",
                "permno": 1,
                "z_demand": 0.5,
                "z_moat": 0.2,
                "z_inventory_quality_proxy": 0.1,
                "z_discipline_cond": -0.3,
                "dist_sma20": 0.01,
                "trend_veto": False,
            },
            {
                "date": "2026-01-05",
                "ticker": "BBB",
                "permno": 2,
                "z_demand": 0.5,
                "z_moat": 0.2,
                "z_inventory_quality_proxy": 0.1,
                "z_discipline_cond": 0.3,
                "dist_sma20": 0.02,
                "trend_veto": False,
            },
        ]
    ).to_parquet(features_path)

    summary = run_rule100_softmax_v1_audit(
        as_of="2026-01-05",
        features_path=features_path,
        lifecycle_path=lifecycle_path,
        output_prefix=output_prefix,
    )

    artifacts = summary["artifacts"]
    assert summary["boundary"]["softmax_v1_primary"] is True
    assert summary["boundary"]["kelly_comparator_only"] is True
    assert summary["boundary"]["mutates_lifecycle_log"] is False
    assert all(Path(path).exists() for path in artifacts.values())

    comparison = pd.read_csv(artifacts["comparison_csv"])
    assert comparison["ticker"].tolist() == ["BBB", "AAA"]
    assert {"softmax_weight", "kelly_weight", "softmax_delta_from_current"}.issubset(comparison.columns)
    assert float(comparison["softmax_weight"].sum()) == pytest.approx(0.20)
    assert int((comparison["kelly_weight"] > 0).sum()) <= int((comparison["softmax_weight"] > 0).sum())

    history = pd.read_csv(artifacts["history_csv"])
    assert {
        "event_weight",
        "softmax_v1_target_weight",
        "softmax_v1_cash_residual",
        "source",
    }.issubset(history.columns)
    assert set(history["source"].unique()) == {"rule100_softmax_v1_history"}


def test_rule100_softmax_v1_audit_writes_cash_only_artifacts_when_no_open_positions(tmp_path) -> None:
    from scripts.rule100_softmax_v1_audit import run_rule100_softmax_v1_audit

    lifecycle_path = tmp_path / "empty_lifecycle.jsonl"
    features_path = tmp_path / "features.parquet"
    output_prefix = tmp_path / "rule100_softmax_v1"
    pd.DataFrame([{"date": "2026-01-05", "ticker": "AAA"}]).to_parquet(features_path)

    summary = run_rule100_softmax_v1_audit(
        as_of="2026-01-05",
        features_path=features_path,
        lifecycle_path=lifecycle_path,
        output_prefix=output_prefix,
    )

    artifacts = summary["artifacts"]
    assert summary["status"] == "cash_only"
    assert summary["sizing_summary"]["eligible_count"] == 0
    assert all(Path(path).exists() for path in artifacts.values())
    comparison = pd.read_csv(artifacts["comparison_csv"])
    assert comparison.empty
    cash = pd.read_csv(artifacts["cash_csv"])
    assert cash["policy"].tolist() == [
        "current_v0_last_weight",
        "softmax_v1_primary",
        "kelly_ablation_comparator",
    ]


def test_rule100_softmax_v1_history_keeps_event_weight_but_drops_ineligible_target(tmp_path) -> None:
    from scripts.rule100_softmax_v1_audit import build_rule100_softmax_v1_history

    decision_log = tmp_path / "decision_log.jsonl"
    rows = [
        {
            "date": "2026-01-05",
            "ticker": "AAA",
            "permno": 1,
            "position_state_after": "HELD",
            "lifecycle_action": "HOLD",
            "buy_sell": None,
            "weight": 0.10,
            "target_weight": 0.10,
            "hold_days": 10,
            "factor_present_count": 4,
            "factor_positive_count": 3,
            "dist_sma20": 0.02,
            "trend_veto": False,
        },
        {
            "date": "2026-01-05",
            "ticker": "TSM",
            "permno": 2,
            "position_state_after": "HELD",
            "lifecycle_action": "TIGHTEN",
            "buy_sell": None,
            "weight": 0.10,
            "target_weight": 0.10,
            "hold_days": 30,
            "factor_present_count": 4,
            "factor_positive_count": 1,
            "dist_sma20": 0.04,
            "trend_veto": False,
        },
    ]
    decision_log.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    history = build_rule100_softmax_v1_history(decision_log_path=decision_log)
    by_ticker = history.set_index("ticker")

    assert by_ticker.loc["TSM", "event_weight"] == pytest.approx(0.10)
    assert by_ticker.loc["TSM", "softmax_v1_target_weight"] == pytest.approx(0.0)
    assert by_ticker.loc["TSM", "softmax_v1_cash_residual"] == pytest.approx(0.90)
    assert by_ticker.loc["TSM", "eligibility_reason"] == "tighten_below_hold_threshold"
    assert by_ticker.loc["AAA", "softmax_v1_target_weight"] == pytest.approx(0.10)


def test_rule100_softmax_v1_current_history_drops_tsm_to_cash() -> None:
    from scripts.rule100_softmax_v1_audit import build_rule100_softmax_v1_history

    history = build_rule100_softmax_v1_history()
    current = history[history["date"] == "2026-05-11"].set_index("ticker")

    assert current.loc["TSM", "event_weight"] == pytest.approx(0.10)
    assert current.loc["TSM", "softmax_v1_target_weight"] == pytest.approx(0.0)
    assert current.loc["TSM", "softmax_v1_cash_residual"] == pytest.approx(0.80)
    assert current.loc["TSM", "eligibility_reason"] == "tighten_below_hold_threshold"
    assert current.loc["AMAT", "softmax_v1_target_weight"] == pytest.approx(0.10)
    assert current.loc["LRCX", "softmax_v1_target_weight"] == pytest.approx(0.10)
