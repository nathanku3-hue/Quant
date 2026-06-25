from __future__ import annotations

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from strategies.optimizer import OPTIMIZATION_METHOD_OPTIONS, OptimizationMethod
from strategies.strategy_replay import (
    REPLAY_COLUMNS,
    SELECTED_METHOD_REPLAY_ARTIFACT_TYPE,
    StrategyReplayBundle,
    StrategyReplayRunMetadata,
    _attach_replay_performance,
    build_selected_method_replay,
    build_strategy_replay,
    selected_method_replay_bundle_to_frame,
    write_selected_method_replay_artifact_atomic,
)
from core.data_orchestrator import StrategyReplayInputs


def _prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            101: [100.0, 101.0, 102.0, 104.0, 105.0, 107.0],
            102: [100.0, 99.0, 100.0, 102.0, 103.0, 106.0],
            103: [50.0, 50.5, 51.0, 51.7, 52.1, 52.5],
            104: [80.0, 80.2, 80.5, 80.9, 81.4, 81.8],
        },
        index=pd.date_range("2026-01-01", periods=6, freq="D"),
    )


def _prices_with_late_bbb() -> pd.DataFrame:
    prices = _prices()
    prices.loc[prices.index < pd.Timestamp("2026-01-05"), 102] = pd.NA
    return prices


def _ticker_map() -> dict[int, str]:
    return {101: "AAA", 102: "BBB", 103: "CCC", 104: "DDD"}


def _controls(max_weight: float = 0.35, rule100_candidate_frame: pd.DataFrame | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        max_weight=max_weight,
        risk_free_rate=0.01,
        rule100_candidate_frame=rule100_candidate_frame,
    )


def _rule100_candidates(date: str = "2026-01-06") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": date,
                "ticker": "AAA",
                "permno": 101,
                "factor_positive_count": 20,
                "technical_quality": 1.0,
                "sizing_eligible": True,
                "eligibility_reason": "eligible_buy_or_hold",
            },
            {
                "date": date,
                "ticker": "BBB",
                "permno": 102,
                "factor_positive_count": 3,
                "technical_quality": 0.8,
                "sizing_eligible": True,
                "eligibility_reason": "eligible_buy_or_hold",
            },
            {
                "date": date,
                "ticker": "CCC",
                "permno": 103,
                "factor_positive_count": 3,
                "technical_quality": 0.6,
                "sizing_eligible": True,
                "eligibility_reason": "eligible_buy_or_hold",
            },
            {
                "date": date,
                "ticker": "DDD",
                "permno": 104,
                "factor_positive_count": 3,
                "technical_quality": 0.4,
                "sizing_eligible": True,
                "eligibility_reason": "eligible_buy_or_hold",
            },
        ]
    )


def _successful_result(weights: pd.Series) -> SimpleNamespace:
    return SimpleNamespace(
        weights=weights,
        diagnostics=SimpleNamespace(
            result_is_optimized=True,
            solver_success=True,
            fallback_used=False,
            solver_message="synthetic optimizer success",
            messages=("synthetic optimizer success",),
        ),
    )


def _failed_result(weights: pd.Series) -> SimpleNamespace:
    return SimpleNamespace(
        weights=weights,
        diagnostics=SimpleNamespace(
            result_is_optimized=False,
            solver_success=False,
            fallback_used=True,
            fallback_reason="forced fallback",
            solver_message="forced fallback",
            messages=("forced fallback",),
        ),
    )


def test_every_exposed_method_returns_asset_rows_plus_cash() -> None:
    prices = _prices()
    dates = pd.to_datetime(["2026-01-05", "2026-01-06"])
    controls = _controls(rule100_candidate_frame=_rule100_candidates("2026-01-05"))

    for method in OPTIMIZATION_METHOD_OPTIONS:
        replay = build_strategy_replay(
            method=method,
            controls=controls,
            prices=prices,
            ticker_map=_ticker_map(),
            sector_map={},
            as_of_range=dates,
        )

        assert set(replay["method"]) == {method.value}
        for date in dates:
            day = replay[replay["date"] == date.date().isoformat()]
            assert len(day) == prices.shape[1] + 1
            assert set(day["ticker"]) == {"AAA", "BBB", "CCC", "DDD", "CASH"}


def test_replay_slices_optimizer_prices_at_or_before_each_date(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: list[tuple[str, pd.Timestamp, float]] = []

    def _inverse(self, prices_df: pd.DataFrame, max_weight: float):
        observed.append(("inverse", prices_df.index.max(), max_weight))
        return _successful_result(pd.Series({101: 0.25, 102: 0.25, 103: 0.25, 104: 0.25}))

    def _mean(self, prices_df: pd.DataFrame, objective: str, max_weight: float, risk_free_rate: float):
        observed.append((objective, prices_df.index.max(), max_weight))
        return _successful_result(pd.Series({101: 0.25, 102: 0.25, 103: 0.25, 104: 0.25}))

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _inverse,
    )
    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_mean_variance_with_diagnostics",
        _mean,
    )

    dates = pd.to_datetime(["2026-01-04", "2026-01-06"])
    replayed_methods = [m for m in OPTIMIZATION_METHOD_OPTIONS if m != OptimizationMethod.RULE_OF_100]
    for method in replayed_methods:
        build_strategy_replay(
            method=method,
            controls=_controls(max_weight=0.35),
            prices=_prices(),
            ticker_map=_ticker_map(),
            sector_map={},
            as_of_range=dates,
        )

    assert observed
    assert [max_seen_date for _objective, max_seen_date, _max_weight in observed] == list(dates) * len(replayed_methods)
    for _objective, max_seen_date, max_weight in observed:
        assert max_weight == pytest.approx(0.35)


def test_rule100_replay_does_not_use_future_candidate_rows() -> None:
    candidates = pd.DataFrame(
        [
            {
                "date": "2026-01-04",
                "ticker": "AAA",
                "permno": 101,
                "factor_positive_count": 4,
                "technical_quality": 1.0,
                "sizing_eligible": True,
                "eligibility_reason": "eligible_buy_or_hold",
            },
            {
                "date": "2026-01-05",
                "ticker": "BBB",
                "permno": 102,
                "factor_positive_count": 20,
                "technical_quality": 1.0,
                "sizing_eligible": True,
                "eligibility_reason": "eligible_buy_or_hold",
            },
        ]
    )

    replay = build_strategy_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls=_controls(rule100_candidate_frame=candidates),
        prices=_prices(),
        ticker_map=_ticker_map(),
        sector_map={},
        as_of_range=pd.to_datetime(["2026-01-04"]),
    )

    day = replay.set_index("ticker")
    assert day.loc["AAA", "target_weight"] > 0
    assert day.loc["BBB", "target_weight"] == pytest.approx(0.0)
    assert day.loc["BBB", "reason"] == "no_rule100_candidate_as_of_date"


def test_rule100_replay_requires_dated_candidate_frame_to_prevent_snapshot_leak() -> None:
    candidates = pd.DataFrame(
        [
            {
                "ticker": "AAA",
                "permno": 101,
                "factor_positive_count": 20,
                "technical_quality": 1.0,
                "sizing_eligible": True,
                "eligibility_reason": "eligible_buy_or_hold",
            },
        ]
    )

    replay = build_strategy_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls=_controls(rule100_candidate_frame=candidates),
        prices=_prices(),
        ticker_map=_ticker_map(),
        sector_map={},
        as_of_range=pd.to_datetime(["2026-01-04"]),
    )

    assert float(replay[replay["ticker"] != "CASH"]["target_weight"].sum()) == pytest.approx(0.0)
    assert replay[replay["ticker"] == "CASH"]["target_weight"].iloc[0] == pytest.approx(1.0)
    assert set(replay["status"]) == {"cash_closed"}
    assert set(replay["reason"]) == {"rule100_candidate_frame_missing_required_columns"}


def test_rule100_replay_requires_price_available_as_of_date() -> None:
    candidates = pd.DataFrame(
        [
            {
                "date": "2026-01-04",
                "ticker": "BBB",
                "permno": 102,
                "factor_positive_count": 20,
                "technical_quality": 1.0,
                "sizing_eligible": True,
                "eligibility_reason": "eligible_buy_or_hold",
            },
        ]
    )

    replay = build_strategy_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls=_controls(rule100_candidate_frame=candidates),
        prices=_prices_with_late_bbb(),
        ticker_map=_ticker_map(),
        sector_map={},
        as_of_range=pd.to_datetime(["2026-01-04"]),
    )

    day = replay.set_index("ticker")
    assert day.loc["BBB", "target_weight"] == pytest.approx(0.0)
    assert day.loc["BBB", "reason"] == "no_price_available_as_of_date"
    assert day.loc["CASH", "target_weight"] == pytest.approx(1.0)


def test_cash_row_residual_matches_one_minus_gross_target_weight_for_all_methods() -> None:
    controls = _controls(rule100_candidate_frame=_rule100_candidates("2026-01-06"))

    for method in OPTIMIZATION_METHOD_OPTIONS:
        replay = build_strategy_replay(
            method=method,
            controls=controls,
            prices=_prices(),
            ticker_map=_ticker_map(),
            sector_map={},
            as_of_range=pd.to_datetime(["2026-01-06"]),
        )
        asset_rows = replay[replay["ticker"] != "CASH"]
        cash_row = replay[replay["ticker"] == "CASH"].iloc[0]
        gross = float(asset_rows["target_weight"].sum())

        assert cash_row["target_weight"] == pytest.approx(1.0 - gross)
        assert cash_row["cash_residual"] == pytest.approx(1.0 - gross)
        assert replay["cash_residual"].nunique() == 1


def test_max_weight_control_flows_to_supported_methods_and_rule100_replay_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[float] = []

    def _inverse(self, prices_df: pd.DataFrame, max_weight: float):
        observed.append(max_weight)
        return _successful_result(pd.Series({101: 0.25, 102: 0.25, 103: 0.25, 104: 0.25}))

    def _mean(self, prices_df: pd.DataFrame, objective: str, max_weight: float, risk_free_rate: float):
        observed.append(max_weight)
        return _successful_result(pd.Series({101: 0.25, 102: 0.25, 103: 0.25, 104: 0.25}))

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _inverse,
    )
    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_mean_variance_with_diagnostics",
        _mean,
    )

    for method in [m for m in OPTIMIZATION_METHOD_OPTIONS if m != OptimizationMethod.RULE_OF_100]:
        replay = build_strategy_replay(
            method=method,
            controls=_controls(max_weight=0.35),
            prices=_prices(),
            ticker_map=_ticker_map(),
            sector_map={},
            as_of_range=pd.to_datetime(["2026-01-06"]),
        )
        assert set(replay["cap_used"]) == {0.35}

    rule100 = build_strategy_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls=_controls(max_weight=0.35, rule100_candidate_frame=_rule100_candidates("2026-01-06")),
        prices=_prices(),
        ticker_map=_ticker_map(),
        sector_map={},
        as_of_range=pd.to_datetime(["2026-01-06"]),
    )

    assert observed
    assert all(value == pytest.approx(0.35) for value in observed)
    assert set(rule100["cap_used"]) == {0.35}
    assert float(rule100[rule100["ticker"] != "CASH"]["target_weight"].max()) == pytest.approx(0.35)


def test_optimizer_failure_fails_closed_without_reusing_stale_or_fallback_weights(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}

    def _inverse(self, prices_df: pd.DataFrame, max_weight: float):
        calls["count"] += 1
        if calls["count"] == 1:
            return _successful_result(pd.Series({101: 0.25, 102: 0.25, 103: 0.25, 104: 0.25}))
        return _failed_result(pd.Series({101: 0.25, 102: 0.25, 103: 0.25, 104: 0.25}))

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _inverse,
    )

    replay = build_strategy_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=0.35),
        prices=_prices(),
        ticker_map=_ticker_map(),
        sector_map={},
        as_of_range=pd.to_datetime(["2026-01-05", "2026-01-06"]),
    )

    first_day = replay[replay["date"] == "2026-01-05"]
    second_day = replay[replay["date"] == "2026-01-06"]

    assert float(first_day[first_day["ticker"] != "CASH"]["target_weight"].sum()) == pytest.approx(1.0)
    assert float(second_day[second_day["ticker"] != "CASH"]["target_weight"].sum()) == pytest.approx(0.0)
    assert second_day[second_day["ticker"] == "CASH"]["target_weight"].iloc[0] == pytest.approx(1.0)
    assert set(second_day["status"]) == {"cash_closed"}


def test_optimizer_exception_fails_closed_to_cash(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(self, prices_df: pd.DataFrame, max_weight: float):
        raise RuntimeError("synthetic optimizer exception")

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _raise,
    )

    replay = build_strategy_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=0.35),
        prices=_prices(),
        ticker_map=_ticker_map(),
        sector_map={},
        as_of_range=pd.to_datetime(["2026-01-06"]),
    )

    assert float(replay[replay["ticker"] != "CASH"]["target_weight"].sum()) == pytest.approx(0.0)
    assert replay[replay["ticker"] == "CASH"]["target_weight"].iloc[0] == pytest.approx(1.0)
    assert set(replay["status"]) == {"cash_closed"}
    assert set(replay["reason"]) == {"optimizer_exception:RuntimeError"}


def test_malformed_as_of_range_fails_closed_to_empty_replay() -> None:
    replay = build_strategy_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=0.35),
        prices=_prices(),
        ticker_map=_ticker_map(),
        sector_map={},
        as_of_range=("bad", "2026-01-06"),
    )

    assert replay.empty
    assert list(replay.columns) == REPLAY_COLUMNS


def test_single_string_as_of_range_is_one_replay_date() -> None:
    replay = build_strategy_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls=_controls(rule100_candidate_frame=_rule100_candidates("2026-01-06")),
        prices=_prices(),
        ticker_map=_ticker_map(),
        sector_map={},
        as_of_range="2026-01-06",
    )

    assert set(replay["date"]) == {"2026-01-06"}
    assert len(replay) == _prices().shape[1] + 1


def test_build_strategy_replay_accepts_pit_input_object(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: list[pd.Timestamp] = []

    def _inverse(self, prices_df: pd.DataFrame, max_weight: float):
        observed.append(prices_df.index.max())
        return _successful_result(pd.Series({101: 0.50, 102: 0.50}))

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _inverse,
    )
    idx = pd.to_datetime(["2026-01-01", "2026-01-02"])
    replay_inputs = StrategyReplayInputs(
        as_of_date=pd.Timestamp("2026-01-02"),
        prices=pd.DataFrame({101: [100.0, 101.0], 102: [50.0, 51.0]}, index=idx),
        returns=pd.DataFrame({101: [0.0, 0.01], 102: [0.0, 0.02]}, index=idx),
        ticker_map={101: "AAA", 102: "BBB"},
        cache_signature={"universe_mode": "r3000_pit"},
        cache_key="unit",
        metadata={"future_rows_excluded": True},
    )

    replay = build_strategy_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=0.60),
        prices=replay_inputs,
        ticker_map=None,
        sector_map={},
        as_of_range=None,
    )

    assert observed == [pd.Timestamp("2026-01-02")]
    assert set(replay["date"]) == {"2026-01-02"}
    assert set(replay["ticker"]) == {"AAA", "BBB", "CASH"}


def test_build_strategy_replay_empty_pit_input_object_emits_cash_closed_row() -> None:
    replay_inputs = StrategyReplayInputs(
        as_of_date=pd.Timestamp("2026-01-02"),
        prices=pd.DataFrame(index=pd.to_datetime(["2026-01-02"])),
        returns=pd.DataFrame(index=pd.to_datetime(["2026-01-02"])),
        ticker_map={101: "AAA"},
        cache_signature={"universe_mode": "r3000_pit"},
        cache_key="empty",
        metadata={"future_rows_excluded": True},
    )

    replay = build_strategy_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=0.35),
        prices=replay_inputs,
        ticker_map=None,
        sector_map={},
        as_of_range=None,
    )

    assert list(replay["date"]) == ["2026-01-02"]
    assert list(replay["ticker"]) == ["CASH"]
    assert float(replay["target_weight"].iloc[0]) == pytest.approx(1.0)
    assert replay["status"].iloc[0] == "cash_closed"
    assert replay["reason"].iloc[0] == "no_selected_assets_in_pit_universe_as_of_date"


def test_near_overallocated_optimizer_output_does_not_emit_negative_cash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _inverse(self, prices_df: pd.DataFrame, max_weight: float):
        return _successful_result(pd.Series({101: 0.25000015, 102: 0.25000015, 103: 0.25000015, 104: 0.25000015}))

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _inverse,
    )

    replay = build_strategy_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=0.35),
        prices=_prices(),
        ticker_map=_ticker_map(),
        sector_map={},
        as_of_range=pd.to_datetime(["2026-01-06"]),
    )

    cash = replay[replay["ticker"] == "CASH"].iloc[0]
    assert cash["target_weight"] == pytest.approx(0.0)
    assert cash["cash_residual"] == pytest.approx(0.0)
    assert float(replay["target_weight"].min()) >= 0.0


def test_selected_method_replay_bundle_exposes_shared_schema_for_rule100_and_optimizer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _inverse(self, prices_df: pd.DataFrame, max_weight: float):
        return _successful_result(pd.Series({101: 0.25, 102: 0.25, 103: 0.25, 104: 0.25}))

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _inverse,
    )

    rule100_bundle = build_selected_method_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls=_controls(rule100_candidate_frame=_rule100_candidates("2026-01-06")),
        prices=_prices(),
        ticker_map=_ticker_map(),
        as_of_range=["2026-01-06"],
    )
    optimizer_bundle = build_selected_method_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=0.35),
        prices=_prices(),
        ticker_map=_ticker_map(),
        as_of_range=["2026-01-06"],
    )

    assert isinstance(rule100_bundle, StrategyReplayBundle)
    assert list(rule100_bundle.replay.columns) == list(optimizer_bundle.replay.columns) == REPLAY_COLUMNS
    assert set(rule100_bundle.replay["ticker"]) == {"AAA", "BBB", "CCC", "DDD", "CASH"}
    assert set(optimizer_bundle.replay["ticker"]) == {"AAA", "BBB", "CCC", "DDD", "CASH"}
    assert rule100_bundle.decision_context.status == "empty"
    assert optimizer_bundle.event_context.reason == "no_event_annotations_context_provided"


def test_selected_method_replay_attaches_pit_filtered_event_and_decision_context() -> None:
    event_context = pd.DataFrame(
        [
            {"date": "2026-01-04", "ticker": "AAA", "action": "ENTER", "weight": 0.25, "reason": "in_window"},
            {"date": "2026-01-07", "ticker": "AAA", "action": "EXIT", "weight": 0.0, "reason": "future"},
            {"date": "2026-01-04", "ticker": "ZZZ", "action": "ENTER", "weight": 0.10, "reason": "not_in_replay"},
        ]
    )
    decision_context = pd.DataFrame(
        [
            {
                "date": "2026-01-04",
                "ticker": "AAA",
                "method": OptimizationMethod.RULE_OF_100.value,
                "buy_sell": "BUY",
                "target_weight": 0.25,
                "primary_reason": "eligible_buy",
            },
            {
                "date": "2026-01-04",
                "ticker": "BBB",
                "method": OptimizationMethod.INVERSE_VOLATILITY.value,
                "buy_sell": "BUY",
                "target_weight": 0.25,
                "primary_reason": "wrong_method",
            },
        ]
    )

    bundle = build_selected_method_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls=_controls(rule100_candidate_frame=_rule100_candidates("2026-01-04")),
        prices=_prices(),
        ticker_map=_ticker_map(),
        as_of_range=["2026-01-04"],
        event_context=event_context,
        decision_context=decision_context,
    )

    assert bundle.event_context.status == "ok"
    assert bundle.decision_context.status == "ok"
    assert bundle.event_context.frame[["date", "ticker", "action", "reason"]].to_dict("records") == [
        {"date": "2026-01-04", "ticker": "AAA", "action": "ENTER", "reason": "in_window"}
    ]
    assert bundle.decision_context.frame[["date", "ticker", "buy_sell", "reason"]].to_dict("records") == [
        {"date": "2026-01-04", "ticker": "AAA", "buy_sell": "BUY", "reason": "eligible_buy"}
    ]


def test_selected_method_aux_context_targets_replay_weights_not_legacy_aux_weights() -> None:
    """Aux rows keep legacy weight as audit metadata but display replay target_weight semantics."""
    event_context = pd.DataFrame(
        [
            {
                "date": "2026-01-04",
                "ticker": "AAA",
                "action": "ENTER",
                "weight": 0.99,
                "reason": "legacy_event_weight",
            },
        ]
    )
    decision_context = pd.DataFrame(
        [
            {
                "date": "2026-01-04",
                "ticker": "AAA",
                "method": OptimizationMethod.RULE_OF_100.value,
                "buy_sell": "BUY",
                "target_weight": 0.88,
                "primary_reason": "legacy_decision_target",
            },
        ]
    )

    bundle = build_selected_method_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls=_controls(rule100_candidate_frame=_rule100_candidates("2026-01-04")),
        prices=_prices(),
        ticker_map=_ticker_map(),
        as_of_range=["2026-01-04"],
        event_context=event_context,
        decision_context=decision_context,
    )

    replay_target = float(
        bundle.replay[
            (bundle.replay["ticker"] == "AAA")
            & (pd.to_datetime(bundle.replay["date"]).dt.date.astype(str) == "2026-01-04")
        ]["target_weight"].iloc[0]
    )
    assert replay_target != pytest.approx(0.99)
    assert replay_target != pytest.approx(0.88)
    assert float(bundle.event_context.frame["target_weight"].iloc[0]) == pytest.approx(replay_target)
    assert float(bundle.event_context.frame["weight"].iloc[0]) == pytest.approx(0.99)
    assert bundle.event_context.frame["row_role"].iloc[0] == "event_annotations"
    assert bundle.event_context.frame["context_role"].iloc[0] == "current_holding"
    assert float(bundle.decision_context.frame["target_weight"].iloc[0]) == pytest.approx(replay_target)
    assert float(bundle.decision_context.frame["weight"].iloc[0]) == pytest.approx(0.88)
    assert bundle.decision_context.frame["row_role"].iloc[0] == "decision_context"
    assert bundle.decision_context.frame["context_role"].iloc[0] == "current_holding"


def test_selected_method_aux_context_out_of_replay_universe_is_filtered_not_zero_weighted() -> None:
    decision_context = pd.DataFrame(
        [
            {
                "date": "2026-01-04",
                "ticker": "ZZZ",
                "method": OptimizationMethod.RULE_OF_100.value,
                "buy_sell": "BUY",
                "weight": 0.10,
                "primary_reason": "not_in_replay_universe",
            },
        ]
    )

    bundle = build_selected_method_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls=_controls(rule100_candidate_frame=_rule100_candidates("2026-01-04")),
        prices=_prices(),
        ticker_map=_ticker_map(),
        as_of_range=["2026-01-04"],
        decision_context=decision_context,
    )

    assert bundle.decision_context.status == "empty"
    assert bundle.decision_context.frame.empty


def test_replay_frame_contains_performance_path_without_optimizer_weights(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _inverse(self, prices_df: pd.DataFrame, max_weight: float):
        return _successful_result(pd.Series({101: 0.50, 102: 0.50, 103: 0.0, 104: 0.0}))

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _inverse,
    )

    replay = build_strategy_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=0.60),
        prices=_prices(),
        ticker_map=_ticker_map(),
        as_of_range=["2026-01-05", "2026-01-06"],
    )

    assert {"asset_return", "return_contribution", "portfolio_return", "portfolio_equity"}.issubset(replay.columns)
    day = replay[replay["date"] == "2026-01-05"].set_index("ticker")
    expected_return = 0.50 * (107.0 / 105.0 - 1.0) + 0.50 * (106.0 / 103.0 - 1.0)
    assert day.loc["AAA", "asset_return"] == pytest.approx(107.0 / 105.0 - 1.0)
    assert day.loc["BBB", "asset_return"] == pytest.approx(106.0 / 103.0 - 1.0)
    assert day.loc["CASH", "asset_return"] == pytest.approx(0.0)
    assert day.loc["AAA", "portfolio_return"] == pytest.approx(expected_return)
    assert float(replay.groupby("date")["portfolio_return"].first().iloc[0]) == pytest.approx(expected_return)
    assert float(replay[replay["date"] == "2026-01-06"]["portfolio_return"].iloc[0]) == pytest.approx(0.0)


def test_replay_performance_does_not_use_same_date_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _inverse(self, prices_df: pd.DataFrame, max_weight: float):
        return _successful_result(pd.Series({101: 1.0, 102: 0.0, 103: 0.0, 104: 0.0}))

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _inverse,
    )

    replay = build_strategy_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=1.0),
        prices=_prices(),
        ticker_map=_ticker_map(),
        as_of_range=["2026-01-06"],
    )

    day = replay[replay["date"] == "2026-01-06"].set_index("ticker")
    assert day.loc["AAA", "asset_return"] == pytest.approx(0.0)
    assert day.loc["AAA", "portfolio_return"] == pytest.approx(0.0)


def test_small_frame_performance_prefers_real_zero_permno_return_over_ticker_fallback() -> None:
    replay = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01"],
            "method": [OptimizationMethod.INVERSE_VOLATILITY.value] * 2,
            "ticker": ["AAA", "CASH"],
            "permno": [101, "CASH"],
            "target_weight": [1.0, 0.0],
            "cash_residual": [0.0, 0.0],
            "cap_used": [1.0, 1.0],
            "cap_source": ["controls.max_weight"] * 2,
            "source": ["test"] * 2,
            "status": ["ok"] * 2,
            "reason": ["test"] * 2,
        }
    )
    returns = pd.DataFrame(
        {
            101: [0.0, 0.0],
            "AAA": [0.0, 0.25],
        },
        index=pd.to_datetime(["2026-01-01", "2026-01-02"]),
    )

    out = _attach_replay_performance(replay, returns).set_index("ticker")

    assert out.loc["AAA", "asset_return"] == pytest.approx(0.0)
    assert out.loc["AAA", "portfolio_return"] == pytest.approx(0.0)



def test_start_date_changes_replay_construction_not_just_filtering(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """start_date/end_date on the raw-DataFrame path must limit which dates are
    replayed (constructed), not just filter a full-range replay after the fact."""

    call_dates: list[pd.Timestamp] = []

    def _inverse(self, prices_df: pd.DataFrame, max_weight: float):
        call_dates.append(prices_df.index.max())
        return _successful_result(pd.Series({101: 0.25, 102: 0.25, 103: 0.25, 104: 0.25}))

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _inverse,
    )

    prices = _prices()  # 2026-01-01 through 2026-01-06

    # Full range — no start_date/end_date, no as_of_range → uses entire price index
    full_bundle = build_selected_method_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=0.35),
        prices=prices,
        ticker_map=_ticker_map(),
    )
    full_dates = set(full_bundle.replay["date"].unique())

    call_dates.clear()

    # Restricted range via start_date/end_date
    narrow_bundle = build_selected_method_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=0.35),
        prices=prices,
        ticker_map=_ticker_map(),
        start_date="2026-01-04",
        end_date="2026-01-06",
    )
    narrow_dates = set(narrow_bundle.replay["date"].unique())

    # The narrow bundle must have fewer replay dates than the full bundle
    assert narrow_dates < full_dates
    assert "2026-01-04" in narrow_dates
    assert "2026-01-06" in narrow_dates
    assert "2026-01-01" not in narrow_dates

    # Optimizer was only called for dates in the narrow range
    for dt in call_dates:
        assert dt >= pd.Timestamp("2026-01-04")
        assert dt <= pd.Timestamp("2026-01-06")


def test_latest_snapshot_derivable_from_bundle_last_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The latest target-weight snapshot is the last date in bundle.daily_portfolio."""

    def _inverse(self, prices_df: pd.DataFrame, max_weight: float):
        return _successful_result(pd.Series({101: 0.30, 102: 0.30, 103: 0.20, 104: 0.20}))

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _inverse,
    )

    bundle = build_selected_method_replay(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls=_controls(max_weight=0.35),
        prices=_prices(),
        ticker_map=_ticker_map(),
        start_date="2026-01-04",
        end_date="2026-01-06",
    )

    # Derive latest snapshot from the bundle's last date
    portfolio = bundle.daily_portfolio
    last_date = portfolio["date"].max()
    snapshot = portfolio[portfolio["date"] == last_date].set_index("ticker")

    assert last_date == "2026-01-06"
    assert snapshot.loc["AAA", "target_weight"] == pytest.approx(0.30)
    assert snapshot.loc["BBB", "target_weight"] == pytest.approx(0.30)
    assert snapshot.loc["CCC", "target_weight"] == pytest.approx(0.20)
    assert snapshot.loc["DDD", "target_weight"] == pytest.approx(0.20)
    assert snapshot.loc["CASH", "target_weight"] == pytest.approx(0.0)

    # run_metadata.date_window reflects the requested range
    assert bundle.run_metadata.date_window["requested_start"] == "2026-01-04"
    assert bundle.run_metadata.date_window["requested_end"] == "2026-01-06"
