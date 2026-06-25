"""Tests for the strategy adapter contract, Rule100 adapter, and coverage metadata."""

from __future__ import annotations

import pandas as pd
import pytest

from strategies.adapter import StrategyAdapter, ValidationResult
from strategies.adapter_registry import STRATEGY_ADAPTERS, get_adapter
from strategies.optimizer import OptimizationMethod
from strategies.rule100_adapter import Rule100Adapter


# ── Contract tests ──────────────────────────────────────────────────────────


class TestAdapterContract:
    """Verify the ABC contract is correctly implemented."""

    def test_rule100_adapter_is_strategy_adapter(self) -> None:
        adapter = Rule100Adapter()
        assert isinstance(adapter, StrategyAdapter)

    def test_rule100_adapter_identity_fields(self) -> None:
        adapter = Rule100Adapter()
        assert adapter.strategy_id == "rule_of_100_softmax_v1"
        assert adapter.display_name == "Rule of 100"
        assert adapter.method == OptimizationMethod.RULE_OF_100
        assert "factor_positive_count" in adapter.required_inputs
        assert "technical_quality" in adapter.required_inputs

    def test_registry_contains_rule100(self) -> None:
        assert OptimizationMethod.RULE_OF_100 in STRATEGY_ADAPTERS
        assert isinstance(STRATEGY_ADAPTERS[OptimizationMethod.RULE_OF_100], Rule100Adapter)

    def test_get_adapter_by_string(self) -> None:
        adapter = get_adapter("Rule of 100")
        assert adapter is not None
        assert adapter.strategy_id == "rule_of_100_softmax_v1"

    def test_get_adapter_unknown_returns_none(self) -> None:
        assert get_adapter("Nonexistent Strategy") is None


# ── Coverage tests ──────────────────────────────────────────────────────────


class TestCoverageValidation:
    """Verify coverage boundary enforcement."""

    def test_rejects_date_before_coverage_start(self) -> None:
        adapter = Rule100Adapter()
        inputs = pd.DataFrame(
            {"factor_positive_count": [3], "technical_quality": [0.8], "sizing_eligible": [True]}
        )
        result = adapter.validate_inputs("2024-06-01", inputs)
        assert isinstance(result, ValidationResult)
        assert result.ok is False
        assert "no_pit_candidate_data_before_coverage_start" in result.reason
        assert len(result.warnings) > 0
        assert "2024-06-01" in result.warnings[0]

    def test_accepts_date_at_coverage_start(self) -> None:
        adapter = Rule100Adapter()
        inputs = pd.DataFrame(
            {"factor_positive_count": [4], "technical_quality": [0.9], "sizing_eligible": [True]}
        )
        result = adapter.validate_inputs("2025-01-06", inputs)
        assert result.ok is True

    def test_accepts_date_after_coverage_start(self) -> None:
        adapter = Rule100Adapter()
        inputs = pd.DataFrame(
            {"factor_positive_count": [4], "technical_quality": [0.9], "sizing_eligible": [True]}
        )
        result = adapter.validate_inputs("2026-01-15", inputs)
        assert result.ok is True

    def test_rejects_empty_inputs(self) -> None:
        adapter = Rule100Adapter()
        result = adapter.validate_inputs("2025-06-01", pd.DataFrame())
        assert result.ok is False
        assert "empty_pit_inputs" in result.reason

    def test_rejects_missing_required_columns(self) -> None:
        adapter = Rule100Adapter()
        inputs = pd.DataFrame({"ticker": ["MSFT"], "score": [1.0]})
        result = adapter.validate_inputs("2025-06-01", inputs)
        assert result.ok is False
        assert "missing_required_columns" in result.reason

    def test_warns_no_eligible_candidates(self) -> None:
        adapter = Rule100Adapter()
        inputs = pd.DataFrame(
            {"factor_positive_count": [1], "technical_quality": [0.2], "sizing_eligible": [False]}
        )
        result = adapter.validate_inputs("2025-06-01", inputs)
        assert result.ok is True
        assert any("no_sizing_eligible" in w for w in result.warnings)


# ── Leakage tests ───────────────────────────────────────────────────────────


class TestNoFutureLeakage:
    """Verify allocation_fn cannot produce weights from future data."""

    def test_allocation_uses_only_provided_pit_inputs(self) -> None:
        """allocation_fn receives a pre-sliced PIT frame; it cannot reach beyond it."""
        adapter = Rule100Adapter()
        # Simulate a PIT frame as of 2025-03-01 with 2 candidates
        inputs = pd.DataFrame({
            "factor_positive_count": [4, 3],
            "technical_quality": [0.9, 0.7],
            "sizing_eligible": [True, True],
            "ticker": ["MSFT", "AVGO"],
        })
        weights = adapter.allocation_fn("2025-03-01", inputs, {"max_weight": 0.35})
        assert isinstance(weights, pd.Series)
        assert len(weights) == 2
        assert float(weights.sum()) <= 1.0 + 1e-9
        assert all(w >= 0.0 for w in weights)

    def test_allocation_does_not_access_external_state(self) -> None:
        """allocation_fn is pure — same inputs produce same outputs."""
        adapter = Rule100Adapter()
        inputs = pd.DataFrame({
            "factor_positive_count": [5],
            "technical_quality": [1.0],
            "sizing_eligible": [True],
        })
        w1 = adapter.allocation_fn("2025-06-01", inputs, {"max_weight": 0.20})
        w2 = adapter.allocation_fn("2025-06-01", inputs, {"max_weight": 0.20})
        pd.testing.assert_series_equal(w1, w2)


# ── Stale carry-forward tests ───────────────────────────────────────────────


class TestNoStaleCarryForward:
    """Verify that missing/empty inputs produce zero weights, not carry-forward."""

    def test_empty_inputs_produce_empty_weights(self) -> None:
        adapter = Rule100Adapter()
        weights = adapter.allocation_fn("2025-06-01", pd.DataFrame(), {"max_weight": 0.35})
        assert weights.empty or float(weights.sum()) == 0.0

    def test_no_eligible_produces_zero_weights(self) -> None:
        adapter = Rule100Adapter()
        inputs = pd.DataFrame({
            "factor_positive_count": [1, 2],
            "technical_quality": [0.1, 0.2],
            "sizing_eligible": [False, False],
        })
        weights = adapter.allocation_fn("2025-06-01", inputs, {"max_weight": 0.35})
        assert float(weights.sum()) == 0.0


# ── Metadata tests ──────────────────────────────────────────────────────────


class TestReplayMetadataCoverage:
    """Verify StrategyReplayRunMetadata coverage fields are populated."""

    def test_metadata_has_coverage_fields(self) -> None:
        from strategies.strategy_replay import StrategyReplayRunMetadata

        m = StrategyReplayRunMetadata(
            run_id="test",
            method_id="Rule of 100",
            source_id="test_source",
            input_signatures=(),
            date_window={"requested_start": "2024-01-01", "requested_end": "2025-12-31",
                         "replay_start": "2025-01-06", "replay_end": "2025-12-31"},
            row_counts={"daily_portfolio": 0, "event_annotations": 0,
                        "buy_sell_decisions": 0, "total": 0},
            status_counts={},
            timing={},
            input_coverage_start="2025-01-06",
            effective_start="2025-01-06",
            coverage_warnings=(
                "requested_start 2024-01-01 < input_coverage_start 2025-01-06; "
                "dates before 2025-01-06 are cash_closed",
            ),
        )
        assert m.input_coverage_start == "2025-01-06"
        assert m.effective_start == "2025-01-06"
        assert len(m.coverage_warnings) == 1
        assert "cash_closed" in m.coverage_warnings[0]

    def test_empty_metadata_has_none_defaults(self) -> None:
        from strategies.strategy_replay import _empty_run_metadata

        m = _empty_run_metadata()
        assert m.input_coverage_start is None
        assert m.effective_start is None
        assert m.coverage_warnings == ()


# ── Integration tests ───────────────────────────────────────────────────────


class TestAdapterIntegrationInReplay:
    """Prove adapter is consumed by the central replay path, not just tested in isolation."""

    def test_pre_coverage_dates_are_cash_closed_in_build_strategy_replay(self) -> None:
        """build_strategy_replay with pre-2025 dates produces cash_closed rows when candidates exist."""
        from strategies.strategy_replay import build_strategy_replay

        # Create a price frame spanning 2024-06-01 to 2025-02-01
        dates = pd.date_range("2024-06-01", "2025-02-01", freq="B")
        prices = pd.DataFrame(
            {"MSFT": range(100, 100 + len(dates)), "AVGO": range(200, 200 + len(dates))},
            index=dates,
        )
        # Provide candidates with dates BEFORE coverage start — adapter must block these
        candidates = pd.DataFrame({
            "date": ["2024-07-01", "2024-07-01", "2025-01-10", "2025-01-10"],
            "ticker": ["MSFT", "AVGO", "MSFT", "AVGO"],
            "factor_positive_count": [4, 3, 4, 3],
            "technical_quality": [0.9, 0.7, 0.9, 0.7],
            "sizing_eligible": [True, True, True, True],
        })
        controls = {"max_weight": 0.35, "rule100_candidate_frame": candidates}

        replay = build_strategy_replay(
            method="Rule of 100",
            controls=controls,
            prices=prices,
            as_of_range=[pd.Timestamp("2024-07-01"), pd.Timestamp("2025-01-15")],
        )

        assert not replay.empty
        # Pre-coverage date (2024-07-01) has candidates but adapter must block them
        pre_coverage = replay[pd.to_datetime(replay["date"]) == pd.Timestamp("2024-07-01")]
        assert not pre_coverage.empty, "Expected pre-coverage rows in replay"
        assert all(pre_coverage["status"] == "cash_closed"), (
            f"Pre-coverage rows should be cash_closed, got: {pre_coverage['status'].unique()}"
        )
        assert all("adapter_validation_failed" in str(r) for r in pre_coverage["reason"]), (
            f"Pre-coverage reason should mention adapter_validation_failed, got: {pre_coverage['reason'].unique()}"
        )
        # Post-coverage date (2025-01-15) should produce weights
        post_coverage = replay[pd.to_datetime(replay["date"]) == pd.Timestamp("2025-01-15")]
        assert not post_coverage.empty
        non_cash_post = post_coverage[post_coverage["ticker"] != "CASH"]
        assert any(non_cash_post["status"] == "ok")

    def test_post_coverage_dates_are_not_blocked(self) -> None:
        """Dates after input_coverage_start are not rejected by adapter."""
        from strategies.strategy_replay import build_strategy_replay

        dates = pd.date_range("2025-01-02", "2025-02-01", freq="B")
        prices = pd.DataFrame(
            {"MSFT": range(100, 100 + len(dates))},
            index=dates,
        )
        candidates = pd.DataFrame({
            "date": ["2025-01-10"],
            "ticker": ["MSFT"],
            "factor_positive_count": [4],
            "technical_quality": [0.9],
            "sizing_eligible": [True],
        })
        controls = {"max_weight": 0.35, "rule100_candidate_frame": candidates}

        replay = build_strategy_replay(
            method="Rule of 100",
            controls=controls,
            prices=prices,
            as_of_range=[pd.Timestamp("2025-01-15")],
        )

        assert not replay.empty
        # Post-coverage date should NOT be cash_closed due to adapter
        non_cash = replay[replay["ticker"] != "CASH"]
        assert not all(non_cash["status"] == "cash_closed"), (
            "Post-coverage dates should not all be cash_closed by adapter"
        )

    def test_build_selected_method_replay_coverage_metadata(self) -> None:
        """build_selected_method_replay populates coverage_warnings for pre-2025 start."""
        from strategies.strategy_replay import build_selected_method_replay

        dates = pd.date_range("2024-01-01", "2025-02-01", freq="B")
        prices = pd.DataFrame(
            {"MSFT": range(100, 100 + len(dates))},
            index=dates,
        )
        # Include pre-coverage candidates so adapter blocks them
        candidates = pd.DataFrame({
            "date": ["2024-06-01", "2025-01-10"],
            "ticker": ["MSFT", "MSFT"],
            "factor_positive_count": [4, 4],
            "technical_quality": [0.9, 0.9],
            "sizing_eligible": [True, True],
        })
        controls = {"max_weight": 0.35, "rule100_candidate_frame": candidates}

        bundle = build_selected_method_replay(
            method="Rule of 100",
            controls=controls,
            prices=prices,
            start_date="2024-01-01",
            end_date="2025-02-01",
            as_of_range=[pd.Timestamp("2024-06-01"), pd.Timestamp("2025-01-15")],
        )

        # Metadata should report coverage gap
        assert bundle.run_metadata.input_coverage_start == "2025-01-06"
        assert len(bundle.run_metadata.coverage_warnings) > 0
        assert "2024-01-01" in bundle.run_metadata.coverage_warnings[0]
        assert "cash_closed" in bundle.run_metadata.coverage_warnings[0]

        # Pre-coverage replay date with candidates should be cash_closed
        pre_coverage = bundle.replay[pd.to_datetime(bundle.replay["date"]) == pd.Timestamp("2024-06-01")]
        if not pre_coverage.empty:
            assert all(pre_coverage["status"] == "cash_closed")




    def test_allocation_fn_is_called_by_build_strategy_replay(self, monkeypatch) -> None:
        """Spy proves adapter.allocation_fn is called in the production replay path."""
        from strategies.strategy_replay import build_strategy_replay
        from strategies import adapter_registry
        from strategies.rule100_adapter import Rule100Adapter

        calls: list[tuple[str, int]] = []
        original_allocation_fn = Rule100Adapter.allocation_fn

        def spy_allocation_fn(self, as_of_date, pit_inputs, controls):
            calls.append((as_of_date, len(pit_inputs)))
            return original_allocation_fn(self, as_of_date, pit_inputs, controls)

        monkeypatch.setattr(Rule100Adapter, "allocation_fn", spy_allocation_fn)

        dates = pd.date_range("2025-01-02", "2025-02-01", freq="B")
        prices = pd.DataFrame(
            {"MSFT": range(100, 100 + len(dates)), "AVGO": range(200, 200 + len(dates))},
            index=dates,
        )
        candidates = pd.DataFrame({
            "date": ["2025-01-10", "2025-01-10"],
            "ticker": ["MSFT", "AVGO"],
            "factor_positive_count": [4, 3],
            "technical_quality": [0.9, 0.7],
            "sizing_eligible": [True, True],
        })
        controls = {"max_weight": 0.35, "rule100_candidate_frame": candidates}

        replay = build_strategy_replay(
            method="Rule of 100",
            controls=controls,
            prices=prices,
            as_of_range=[pd.Timestamp("2025-01-15")],
        )

        assert not replay.empty
        assert len(calls) > 0, "allocation_fn was never called by build_strategy_replay"
        assert calls[0][0] == "2025-01-15"
        assert calls[0][1] == 2  # 2 eligible candidates

    def test_validate_inputs_is_called_with_pit_sliced_frame(self, monkeypatch) -> None:
        """Spy proves validate_inputs receives PIT-sliced frame, not full candidates."""
        from strategies.strategy_replay import build_strategy_replay
        from strategies.rule100_adapter import Rule100Adapter
        from strategies.adapter import ValidationResult

        validation_calls: list[tuple[str, int]] = []
        original_validate = Rule100Adapter.validate_inputs

        def spy_validate(self, as_of_date, pit_inputs):
            validation_calls.append((as_of_date, len(pit_inputs)))
            return original_validate(self, as_of_date, pit_inputs)

        monkeypatch.setattr(Rule100Adapter, "validate_inputs", spy_validate)

        dates = pd.date_range("2025-01-02", "2025-02-01", freq="B")
        prices = pd.DataFrame({"MSFT": range(100, 100 + len(dates))}, index=dates)
        # Two candidate dates — only one should be visible at as_of 2025-01-10
        candidates = pd.DataFrame({
            "date": ["2025-01-08", "2025-01-20"],
            "ticker": ["MSFT", "MSFT"],
            "factor_positive_count": [4, 5],
            "technical_quality": [0.9, 1.0],
            "sizing_eligible": [True, True],
        })
        controls = {"max_weight": 0.35, "rule100_candidate_frame": candidates}

        build_strategy_replay(
            method="Rule of 100",
            controls=controls,
            prices=prices,
            as_of_range=[pd.Timestamp("2025-01-10")],
        )

        assert len(validation_calls) > 0
        # PIT slice at 2025-01-10 should only see the 2025-01-08 row (1 row)
        assert validation_calls[0][0] == "2025-01-10"
        assert validation_calls[0][1] == 1, (
            f"validate_inputs should receive PIT-sliced frame (1 row), got {validation_calls[0][1]}"
        )
