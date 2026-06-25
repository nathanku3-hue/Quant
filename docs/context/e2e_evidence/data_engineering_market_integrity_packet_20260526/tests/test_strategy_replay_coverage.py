"""Tests for strategy replay coverage plan, input_unavailable emission, and CLI args."""
from __future__ import annotations

from pathlib import Path
import time
from unittest.mock import MagicMock

import pandas as pd
import pytest

from core.data_orchestrator import (
    BatchedPITReplayData,
    StrategyReplayInputs,
    build_batched_pit_input_loader,
    pit_members_for_date,
)
from strategies.optimizer import OptimizationMethod
from strategies.strategy_replay import (
    ReplayDateCoverage,
    _build_replay_from_input_loader,
    _build_run_metadata,
    _compute_coverage_plan,
    _strategy_inputs_signature,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_batched(
    permnos: list[int],
    price_dates: list[str],
    membership: dict[str, set[int]],
) -> BatchedPITReplayData:
    idx = pd.to_datetime(price_dates)
    prices = pd.DataFrame(
        {p: [float(i + 1) for i in range(len(price_dates))] for p in permnos},
        index=idx,
    )
    returns = prices.pct_change(fill_method=None).fillna(0.0)
    return BatchedPITReplayData(
        raw_prices=prices,
        raw_returns=returns,
        membership_dates=sorted(membership.keys()),
        membership_index=membership,
        ticker_map={p: f"T{p}" for p in permnos},
        trading_dates=[pd.Timestamp(d) for d in price_dates],
        metadata={},
    )


def _make_inputs(as_of: str, permnos: list[int]) -> StrategyReplayInputs:
    idx = pd.to_datetime(["2024-01-02", "2024-01-03"])
    prices = pd.DataFrame({p: [1.0, 1.1] for p in permnos}, index=idx)
    returns = prices.pct_change(fill_method=None).fillna(0.0)
    return StrategyReplayInputs(
        as_of_date=pd.Timestamp(as_of),
        prices=prices,
        returns=returns,
        ticker_map={p: f"T{p}" for p in permnos},
        cache_signature={"universe_mode": "r3000_pit"},
        cache_key=f"test_{as_of}",
        metadata={"source": "test"},
    )


# ---------------------------------------------------------------------------
# Test 1: Non-monotonic membership gap → correct segments
# ---------------------------------------------------------------------------

def test_coverage_plan_non_monotonic_gap():
    """Dates with gap > threshold are uncovered; dates within threshold are covered."""
    membership = {
        "2024-01-02": {1, 2},
        "2024-02-01": {1, 2},  # big gap after Jan 02
    }
    batched = _make_batched(
        permnos=[1, 2],
        price_dates=["2024-01-02", "2024-01-15", "2024-02-01"],
        membership=membership,
    )
    replay_dates = [
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-15"),  # 13 days after Jan 02 → within 30-day gap
        pd.Timestamp("2024-02-01"),
    ]
    plan = _compute_coverage_plan(
        OptimizationMethod.INVERSE_VOLATILITY,
        {},
        replay_dates,
        batched=batched,
        max_membership_gap_days=30,
    )
    assert len(plan) == 3
    assert plan[0].covered is True
    assert plan[1].covered is True   # 13 days gap → ok
    assert plan[2].covered is True


def test_coverage_plan_gap_exceeded():
    """Date more than max_gap_days after last membership date → uncovered."""
    membership = {"2024-01-02": {1, 2}}
    batched = _make_batched(
        permnos=[1, 2],
        price_dates=["2024-01-02", "2024-03-01"],
        membership=membership,
    )
    replay_dates = [pd.Timestamp("2024-03-01")]  # ~59 days after Jan 02
    plan = _compute_coverage_plan(
        OptimizationMethod.INVERSE_VOLATILITY,
        {},
        replay_dates,
        batched=batched,
        max_membership_gap_days=30,
    )
    assert len(plan) == 1
    assert plan[0].covered is False
    assert plan[0].reason == "membership_gap_exceeded"


# ---------------------------------------------------------------------------
# Test 2: Unavailable dates preserve expected member rows (not just CASH)
# ---------------------------------------------------------------------------

def test_input_unavailable_preserves_expected_members():
    """input_unavailable dates emit rows for expected_members, not just CASH."""
    membership = {"2024-01-02": {10, 20, 30}}
    batched = _make_batched(
        permnos=[10, 20, 30],
        price_dates=["2024-01-02"],
        membership=membership,
    )
    # Force gap exceeded for the replay date
    replay_dates = [pd.Timestamp("2024-03-15")]  # far beyond 30-day gap
    plan = _compute_coverage_plan(
        OptimizationMethod.INVERSE_VOLATILITY,
        {},
        replay_dates,
        batched=batched,
        max_membership_gap_days=30,
    )
    assert plan[0].covered is False

    def _loader(**kwargs):
        return _make_inputs(kwargs["as_of_date"], [10, 20, 30])

    replay, sigs = _build_replay_from_input_loader(
        selected_method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        input_loader=_loader,
        replay_dates=replay_dates,
        replay_start="2024-01-01",
        ticker_map=None,
        sector_map=None,
        max_weight=0.35,
        coverage_plan=plan,
    )
    # Should have a CASH row (input_unavailable emits cash_closed)
    assert not replay.empty
    cash_rows = replay[replay["ticker"] == "CASH"]
    assert len(cash_rows) >= 1
    # Reason must carry the specific cause, not just "input_unavailable"
    assert cash_rows["reason"].str.startswith("input_unavailable:").all()


# ---------------------------------------------------------------------------
# Test 3: Membership gap exceeded → CASH-only row
# ---------------------------------------------------------------------------

def test_membership_gap_exceeded_cash_only():
    """When gap exceeded, loader is not called; output is a single CASH row."""
    membership = {"2024-01-02": {1}}
    batched = _make_batched(
        permnos=[1],
        price_dates=["2024-01-02"],
        membership=membership,
    )
    replay_dates = [pd.Timestamp("2024-04-01")]  # ~90 days gap
    plan = _compute_coverage_plan(
        OptimizationMethod.INVERSE_VOLATILITY,
        {},
        replay_dates,
        batched=batched,
        max_membership_gap_days=30,
    )

    loader_called = []

    def _loader(**kwargs):
        loader_called.append(True)
        return _make_inputs(kwargs["as_of_date"], [1])

    replay, _ = _build_replay_from_input_loader(
        selected_method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        input_loader=_loader,
        replay_dates=replay_dates,
        replay_start="2024-01-01",
        ticker_map=None,
        sector_map=None,
        max_weight=0.35,
        coverage_plan=plan,
    )
    assert not loader_called, "loader must not be called for uncovered dates"
    assert set(replay["ticker"].unique()) == {"CASH"}
    # Reason must carry specific cause
    assert replay["reason"].str.startswith("input_unavailable:").all()


# ---------------------------------------------------------------------------
# Test 4: Rule100 with candidates starting 2025 → pre-2025 dates are uncovered
# ---------------------------------------------------------------------------

def test_rule100_pre_candidate_dates_uncovered():
    """Dates before earliest candidate date are classified as candidate_coverage_not_started."""
    membership = {
        "2024-06-01": {1, 2},
        "2025-01-02": {1, 2},
    }
    batched = _make_batched(
        permnos=[1, 2],
        price_dates=["2024-06-01", "2025-01-02"],
        membership=membership,
    )
    candidates = pd.DataFrame({
        "date": ["2025-01-02"],
        "ticker": ["T1"],
        "permno": [1],
        "factor_positive_count": [3],
        "technical_quality": [0.8],
        "sizing_eligible": [True],
        "eligibility_reason": ["ok"],
    })
    controls = {"rule100_candidate_frame": candidates, "max_weight": 0.35}

    replay_dates = [pd.Timestamp("2024-06-01"), pd.Timestamp("2025-01-02")]
    plan = _compute_coverage_plan(
        OptimizationMethod.RULE_OF_100,
        controls,
        replay_dates,
        batched=batched,
        max_membership_gap_days=30,
    )
    pre_2025 = [e for e in plan if e.date < pd.Timestamp("2025-01-01")]
    post_2025 = [e for e in plan if e.date >= pd.Timestamp("2025-01-01")]
    assert all(not e.covered for e in pre_2025)
    assert all(e.reason == "candidate_coverage_not_started" for e in pre_2025)
    assert all(e.covered for e in post_2025)


# ---------------------------------------------------------------------------
# Test 5: Coverage metadata in manifest (input_coverage_start from source)
# ---------------------------------------------------------------------------

def test_build_run_metadata_coverage_start_from_plan():
    """input_coverage_start in date_window reflects first covered date, not requested start."""
    covered_date = pd.Timestamp("2025-01-02")
    uncovered_date = pd.Timestamp("2024-06-01")
    plan = [
        ReplayDateCoverage(
            date=uncovered_date, covered=False, reason="candidate_coverage_not_started",
            membership_date="2024-06-01", priced_member_count=2, expected_members=[1, 2],
        ),
        ReplayDateCoverage(
            date=covered_date, covered=True, reason="ok",
            membership_date="2025-01-02", priced_member_count=2, expected_members=[1, 2],
        ),
    ]
    replay = pd.DataFrame({
        "date": [covered_date.date().isoformat()],
        "ticker": ["T1"],
        "status": ["ok"],
    })
    empty_ctx = MagicMock()
    empty_ctx.frame = pd.DataFrame(columns=["status"])

    meta = _build_run_metadata(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        replay=replay,
        event_context=empty_ctx,
        decision_context=empty_ctx,
        input_signatures=[],
        requested_start="2024-01-01",
        requested_end="2025-06-01",
        started_at_utc="2026-01-01T00:00:00Z",
        completed_at_utc="2026-01-01T00:00:01Z",
        elapsed_ms=1000.0,
        run_id=None,
        source_id=None,
        coverage_plan=plan,
    )
    assert meta.input_coverage_start == "2025-01-02"
    assert meta.date_window["input_coverage_start"] == "2025-01-02"
    # requested_start is earlier than coverage start
    assert meta.date_window["requested_start"] == "2024-01-01"


# ---------------------------------------------------------------------------
# Test 6: Performance budget — synthetic 4-asset 5Y < 5s
# ---------------------------------------------------------------------------

def test_performance_budget_4asset_5year():
    """Coverage plan + input_loader loop for 4 assets over ~5Y of monthly dates < 5s."""
    permnos = [1, 2, 3, 4]
    # Monthly dates over 5 years ≈ 60 dates
    date_range = pd.date_range("2020-01-01", "2024-12-31", freq="MS")
    price_dates = [d.strftime("%Y-%m-%d") for d in date_range]
    membership = {d: set(permnos) for d in price_dates}

    batched = _make_batched(permnos=permnos, price_dates=price_dates, membership=membership)
    replay_dates = [pd.Timestamp(d) for d in price_dates]

    t0 = time.perf_counter()
    plan = _compute_coverage_plan(
        OptimizationMethod.INVERSE_VOLATILITY,
        {},
        replay_dates,
        batched=batched,
        max_membership_gap_days=35,
    )

    def _loader(**kwargs):
        return _make_inputs(kwargs["as_of_date"], permnos)

    _build_replay_from_input_loader(
        selected_method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        input_loader=_loader,
        replay_dates=replay_dates,
        replay_start=price_dates[0],
        ticker_map=None,
        sector_map=None,
        max_weight=0.35,
        coverage_plan=plan,
    )
    elapsed = time.perf_counter() - t0
    assert elapsed < 5.0, f"Performance budget exceeded: {elapsed:.2f}s"


# ---------------------------------------------------------------------------
# Test 7: CLI parser has new args
# ---------------------------------------------------------------------------

def test_cli_parser_new_args():
    """build_parser exposes replay horizon, candidate, budget, and membership args."""
    from scripts.build_strategy_replay_artifact import build_parser

    parser = build_parser()
    args = parser.parse_args([
        "--as-of-date", "2025-01-01",
        "--lookback-years", "3",
        "--rule100-candidate-path", "/tmp/candidates.parquet",
        "--budget-max-seconds", "120",
        "--budget-max-rows", "1000",
        "--budget-max-dates", "250",
        "--budget-max-elapsed-ms", "10000",
        "--max-membership-gap-days", "45",
    ])
    assert args.lookback_years == 3
    assert args.rule100_candidate_path == "/tmp/candidates.parquet"
    assert args.budget_max_seconds == 120
    assert args.budget_max_rows == 1000
    assert args.budget_max_dates == 250
    assert args.budget_max_elapsed_ms == 10000
    assert args.max_membership_gap_days == 45


def test_selected_output_cli_removes_written_bundle_when_post_write_budget_exceeded(
    tmp_path,
    monkeypatch,
):
    """The selected-output CLI budget covers artifact write/promotion too."""
    from scripts import build_strategy_replay_artifact as builder
    from strategies.strategy_replay import (
        StrategyReplayBundle,
        StrategyReplayContext,
        StrategyReplayRunMetadata,
    )

    artifact_path = tmp_path / "selected_cli.parquet"
    clock = {"value": 0.0}

    def _fake_time():
        return clock["value"]

    def _advance_after_write(bundle, *, artifact_path=None, cache_dir=None):
        path = Path(artifact_path) if artifact_path is not None else (tmp_path / "selected_cli.parquet")
        manifest_path = path.with_suffix(path.suffix + ".manifest.json")
        path.write_bytes(b"parquet-placeholder")
        manifest_path.write_text("{}", encoding="utf-8")
        clock["value"] = 2.0
        return {
            "artifact_path": path,
            "manifest_path": manifest_path,
            "run_id": bundle.run_id,
            "source_id": bundle.run_metadata.source_id,
        }

    metadata = StrategyReplayRunMetadata(
        run_id="cli_budget_test",
        method_id=OptimizationMethod.INVERSE_VOLATILITY.value,
        source_id="selected_method_replay:cli_budget_test",
        input_signatures=(),
        date_window={
            "requested_start": "2026-01-02",
            "requested_end": "2026-01-02",
            "replay_start": "2026-01-02",
            "replay_end": "2026-01-02",
        },
        row_counts={"daily_portfolio": 0, "event_annotations": 0, "buy_sell_decisions": 0, "total": 0},
        status_counts={"daily_portfolio": {"empty": 0}, "event_annotations": {"empty": 0}, "buy_sell_decisions": {"empty": 0}},
        timing={"started_at_utc": "2026-01-02T00:00:00Z", "completed_at_utc": "2026-01-02T00:00:00Z", "elapsed_ms": 0.0},
        controls_signature={"max_weight": 0.35},
    )
    empty_ctx = StrategyReplayContext(
        context_type="event_annotations",
        frame=pd.DataFrame(),
        status="empty",
        reason="test",
        source="test",
    )
    bundle = StrategyReplayBundle(
        replay=pd.DataFrame(),
        event_context=empty_ctx,
        decision_context=StrategyReplayContext(
            context_type="decision_context",
            frame=pd.DataFrame(),
            status="empty",
            reason="test",
            source="test",
        ),
        run_metadata=metadata,
    )

    monkeypatch.setattr(builder.time, "time", _fake_time)
    monkeypatch.setattr(builder, "load_replay_date_index", lambda **kwargs: [pd.Timestamp("2026-01-02")])
    monkeypatch.setattr(builder, "load_batched_pit_replay_data", lambda **kwargs: object())
    monkeypatch.setattr(builder, "build_batched_pit_input_loader", lambda *args, **kwargs: (lambda **kw: None))
    monkeypatch.setattr(builder, "_compute_coverage_plan", lambda **kwargs: [])
    monkeypatch.setattr(
        builder,
        "build_selected_method_replay_with_budget",
        lambda *args, **kwargs: type("Result", (), {"available": True, "bundle": bundle})(),
    )
    monkeypatch.setattr(builder, "write_selected_method_replay_artifact_atomic", _advance_after_write)

    exit_code = builder.main([
        "--as-of-date", "2026-01-02",
        "--method", OptimizationMethod.INVERSE_VOLATILITY.value,
        "--artifact-kind", "selected-method-output",
        "--output-path", str(artifact_path),
        "--budget-max-seconds", "1",
    ])

    assert exit_code == 1
    assert not artifact_path.exists()
    assert not artifact_path.with_suffix(artifact_path.suffix + ".manifest.json").exists()

# ---------------------------------------------------------------------------
# Test 8: coverage_segments captures covered → uncovered → covered intervals
# ---------------------------------------------------------------------------

def test_coverage_segments_non_continuous():
    """A covered/uncovered/covered window produces 3 segments in date_window."""
    plan = [
        ReplayDateCoverage(date=pd.Timestamp("2024-01-02"), covered=True, reason="ok",
                           membership_date="2024-01-02", priced_member_count=2, expected_members=[1, 2]),
        ReplayDateCoverage(date=pd.Timestamp("2024-02-01"), covered=True, reason="ok",
                           membership_date="2024-01-02", priced_member_count=2, expected_members=[1, 2]),
        ReplayDateCoverage(date=pd.Timestamp("2024-03-01"), covered=False, reason="membership_gap_exceeded",
                           membership_date=None, priced_member_count=0, expected_members=[]),
        ReplayDateCoverage(date=pd.Timestamp("2024-04-01"), covered=False, reason="membership_gap_exceeded",
                           membership_date=None, priced_member_count=0, expected_members=[]),
        ReplayDateCoverage(date=pd.Timestamp("2024-05-01"), covered=True, reason="ok",
                           membership_date="2024-05-01", priced_member_count=2, expected_members=[1, 2]),
    ]
    replay = pd.DataFrame({
        "date": ["2024-01-02", "2024-02-01", "2024-05-01"],
        "ticker": ["T1", "T1", "T1"],
        "status": ["ok", "ok", "ok"],
    })
    empty_ctx = MagicMock()
    empty_ctx.frame = pd.DataFrame(columns=["status"])

    meta = _build_run_metadata(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        replay=replay,
        event_context=empty_ctx,
        decision_context=empty_ctx,
        input_signatures=[],
        requested_start="2024-01-01",
        requested_end="2024-06-01",
        started_at_utc="2026-01-01T00:00:00Z",
        completed_at_utc="2026-01-01T00:00:01Z",
        elapsed_ms=1.0,
        run_id=None,
        source_id=None,
        coverage_plan=plan,
    )
    segs = meta.date_window["coverage_segments"]
    assert segs is not None
    assert len(segs) == 3
    assert segs[0] == {"start": "2024-01-02", "end": "2024-02-01", "covered": True}
    assert segs[1] == {"start": "2024-03-01", "end": "2024-04-01", "covered": False}
    assert segs[2] == {"start": "2024-05-01", "end": "2024-05-01", "covered": True}


# ---------------------------------------------------------------------------
# Test 9: Daily-scale perf — 50 assets × 5Y business days < 10s
# ---------------------------------------------------------------------------

def test_performance_budget_daily_scale():
    """CASH-only gap routing for 50 assets over 5Y of daily dates < 10s.

    Uses all-uncovered dates (gap exceeded) so the optimizer is never invoked.
    This isolates the coverage scan + CASH-only input_unavailable emission overhead.
    """
    permnos = list(range(1, 51))
    date_range = pd.date_range("2020-01-01", "2024-12-31", freq="B")  # ~1305 days
    price_dates = [d.strftime("%Y-%m-%d") for d in date_range]

    # Single membership snapshot at start; all replay dates exceed 35-day gap
    membership = {price_dates[0]: set(permnos)}
    batched = _make_batched(permnos=permnos, price_dates=price_dates, membership=membership)

    # Replay dates start 60 days after the only membership date → all gap-exceeded
    gap_start = pd.Timestamp(price_dates[0]) + pd.Timedelta(days=60)
    replay_dates = [pd.Timestamp(d) for d in price_dates if pd.Timestamp(d) >= gap_start]
    assert len(replay_dates) > 1200, "Need enough dates to stress the routing loop"

    loader_called = [0]

    def _loader(**kwargs):
        loader_called[0] += 1
        return _make_inputs(kwargs["as_of_date"], permnos)

    t0 = time.perf_counter()
    plan = _compute_coverage_plan(
        OptimizationMethod.INVERSE_VOLATILITY,
        {},
        replay_dates,
        batched=batched,
        max_membership_gap_days=35,
    )
    _build_replay_from_input_loader(
        selected_method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        input_loader=_loader,
        replay_dates=replay_dates,
        replay_start=price_dates[0],
        ticker_map=None,
        sector_map=None,
        max_weight=0.35,
        coverage_plan=plan,
    )
    elapsed = time.perf_counter() - t0

    assert elapsed < 10.0, f"Daily-scale routing budget exceeded: {elapsed:.2f}s"
    assert loader_called[0] == 0, "Loader must not be called for gap-exceeded dates"
    assert all(not e.covered for e in plan)


def test_performance_budget_daily_scale_no_priced_members_row_heavy():
    """Row-heavy unavailable routing for 50 assets over 5Y of daily dates < 10s."""
    permnos = list(range(1, 51))
    date_range = pd.date_range("2020-01-01", "2024-12-31", freq="B")
    price_dates = [d.strftime("%Y-%m-%d") for d in date_range]
    idx = pd.to_datetime(price_dates)
    prices = pd.DataFrame({p: [float("nan")] * len(price_dates) for p in permnos}, index=idx)
    returns = pd.DataFrame({p: [float("nan")] * len(price_dates) for p in permnos}, index=idx)
    batched = BatchedPITReplayData(
        raw_prices=prices,
        raw_returns=returns,
        membership_dates=price_dates,
        membership_index={d: set(permnos) for d in price_dates},
        ticker_map={p: f"T{p}" for p in permnos},
        trading_dates=[pd.Timestamp(d) for d in price_dates],
        metadata={},
    )
    replay_dates = [pd.Timestamp(d) for d in price_dates]

    loader_called = [0]

    def _loader(**kwargs):
        loader_called[0] += 1
        return _make_inputs(kwargs["as_of_date"], permnos)

    t0 = time.perf_counter()
    plan = _compute_coverage_plan(
        OptimizationMethod.INVERSE_VOLATILITY,
        {},
        replay_dates,
        batched=batched,
        max_membership_gap_days=35,
    )
    replay, _signatures = _build_replay_from_input_loader(
        selected_method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        input_loader=_loader,
        replay_dates=replay_dates,
        replay_start=price_dates[0],
        ticker_map=batched.ticker_map,
        sector_map=None,
        max_weight=0.35,
        coverage_plan=plan,
    )
    elapsed = time.perf_counter() - t0

    assert elapsed < 10.0, f"Row-heavy daily-scale routing budget exceeded: {elapsed:.2f}s"
    assert loader_called[0] == 0, "Loader must not be called for no-priced-member dates"
    assert all(e.reason == "no_priced_members" for e in plan)
    assert len(replay) == len(replay_dates) * (len(permnos) + 1)
    assert set(replay["status"]) == {"cash_closed"}
    assert set(replay["reason"]) == {"input_unavailable:no_priced_members"}
    assert replay["portfolio_return"].eq(0.0).all()
    assert replay["portfolio_equity"].eq(1.0).all()
