import inspect
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts import pead_m6_pit_walk_forward_equity_curve as m6


def _strict_d1_manifest(*, current_vintage: bool = True) -> dict:
    limitations = []
    if current_vintage:
        limitations.append(
            "Input fundamentals are a current-vintage Compustat extract that may include later restatements; strict point-in-time filing-vintage behavior and freedom from restatement hindsight are not established."
        )
    return {
        "schema_version": "1.0",
        "builder": "scripts/pead_d1_sue_builder.py",
        "row_count": 10,
        "columns": ["gvkey", "rdq", "datadate", "sue"],
        "limitations": limitations,
        "methodology": {"eps_basis": "raw numeric epspxq"},
    }


def _d2a_manifest(*, crsp: bool = False, price_fallback: int = 3) -> dict:
    return {
        "schema_version": "2.0",
        "label": "full_universe_security_level",
        "row_count": 100,
        "data_sources": ["crsp.dsf"] if crsp else ["prices_daily_compustat"],
        "return_type_dist": {"total_return": 97, "price_return_fallback": price_fallback},
        "warnings": ["price_return_fallback excludes dividends when either total-return level is unavailable"]
        if price_fallback
        else [],
    }


def _d2b_manifest(*, delisting: bool = False) -> dict:
    return {
        "schema_version": "1.0",
        "builder": "scripts/pead_d2b_event_window_contract.py",
        "counts": {"rows": 100, "events": 10},
        "policy": {
            "lookback_market_sessions": 20,
            "liquidity_score": "arithmetic mean of finite dollar_volume",
        },
        "declarations": {
            "delisting_imputation": delisting,
            "delisting_label": delisting,
        },
    }


def test_m6_input_contract_blocks_current_vintage_and_missing_return_contracts() -> None:
    status = m6.validate_input_contract(
        d1_manifest=_strict_d1_manifest(current_vintage=True),
        d2a_manifest=_d2a_manifest(crsp=False, price_fallback=3),
        d2b_manifest=_d2b_manifest(delisting=False),
    )

    assert status["blocked"] is True
    assert status["flags"]["timing_pit_release_date_or_rdq_aligned"] is True
    assert status["flags"]["strict_pit_eps_vintage"] is False
    assert status["flags"]["eps_vintage"] == "release_date_aligned_but_restated"
    assert status["flags"]["current_vintage_compustat_eps_detected"] is True
    assert "pit_vintage_blocked" in status["failure_reasons"]
    assert "delisting_missing" in status["failure_reasons"]
    assert "tradable_return_missing" in status["failure_reasons"]


def test_m6_input_contract_keeps_vintage_boundary_when_best_available_is_allowed() -> None:
    status = m6.validate_input_contract(
        d1_manifest=_strict_d1_manifest(current_vintage=True),
        d2a_manifest=_d2a_manifest(crsp=True, price_fallback=0),
        d2b_manifest=_d2b_manifest(delisting=True),
        allow_release_date_aligned_but_restated=True,
    )

    assert status["flags"]["eps_vintage"] == "release_date_aligned_but_restated"
    assert "pit_vintage_blocked" not in status["failure_reasons"]
    assert "tradability_liquidity_screen_missing" in status["failure_reasons"]


def test_m6_cost_model_must_be_nonzero_explicit() -> None:
    with pytest.raises(ValueError, match="nonzero and explicit"):
        m6.CostModel(entry_cost_bps=0.0, exit_cost_bps=0.0, slippage_bps=0.0, daily_short_borrow_bps=0.0).validate()

    model = m6.CostModel(entry_cost_bps=5.0, exit_cost_bps=5.0, slippage_bps=1.0, daily_short_borrow_bps=0.5)
    evidence = model.to_evidence()
    assert evidence["nonzero_explicit_costs"] is True
    assert evidence["one_way_turnover_cost_bps"] == pytest.approx(6.0)


def test_m6_walk_forward_folds_are_time_ordered_by_decision_date() -> None:
    dates = pd.to_datetime(["2016-01-05", "2017-03-01", "2018-06-01", "2019-02-01", "2020-05-01"])

    folds = m6.build_walk_forward_folds(dates, m6.WalkForwardConfig(initial_train_years=3))

    assert [fold["fold_id"] for fold in folds] == ["fold_01_2019", "fold_02_2020"]
    assert folds[0]["train_start"] == "2016-01-01"
    assert folds[0]["train_end"] == "2018-12-31"
    assert folds[0]["test_start"] == "2019-01-01"
    assert folds[0]["split_key"] == "decision_date"
    assert pd.Timestamp(folds[1]["train_end"]) < pd.Timestamp(folds[1]["test_start"])


def _synthetic_events_and_returns() -> tuple[pd.DataFrame, pd.DataFrame]:
    decision_dates = pd.to_datetime(["2020-01-02", "2021-01-04", "2022-01-03", "2023-01-03"])
    events = []
    returns = []
    for date_index, decision_date in enumerate(decision_dates):
        for security_index in range(10):
            security_id = f"S{date_index}_{security_index}"
            events.append(
                {
                    "event_id": f"E{date_index}_{security_index}",
                    "security_id": security_id,
                    "decision_date": decision_date,
                    "signal": float(security_index),
                    "tradable": True,
                    "liquidity_pass": True,
                }
            )
            for return_date in pd.bdate_range(decision_date + pd.Timedelta(days=1), periods=5):
                # High-signal names rise; low-signal names fall.  Short leg contribution is therefore positive.
                ret = 0.004 if security_index >= 8 else (-0.004 if security_index <= 1 else 0.0)
                returns.append(
                    {
                        "security_id": security_id,
                        "return_date": return_date,
                        "tradable_total_return": ret,
                    }
                )
    return pd.DataFrame(events), pd.DataFrame(returns)


def test_m6_portfolio_engine_emits_reproducible_net_equity_curve_after_costs() -> None:
    events, returns = _synthetic_events_and_returns()
    cfg = m6.PortfolioConfig(holding_period_sessions=5, min_leg_count=2)
    costs = m6.CostModel(entry_cost_bps=5.0, exit_cost_bps=5.0, slippage_bps=1.0, daily_short_borrow_bps=0.5)

    daily = m6.build_daily_portfolio_returns(events, returns, portfolio_config=cfg, cost_model=costs)
    metrics = m6.compute_equity_curve_metrics(daily)
    folds = m6.build_walk_forward_folds(events["decision_date"], m6.WalkForwardConfig(initial_train_years=2))
    fold_results = m6.compute_fold_results(daily, folds)

    assert not daily.empty
    assert set(["daily_gross_return", "daily_net_return", "turnover", "turnover_cost", "short_borrow_cost"]).issubset(daily.columns)
    assert daily["turnover_cost"].sum() > 0.0
    assert daily["short_borrow_cost"].sum() > 0.0
    assert daily["daily_net_return"].sum() < daily["daily_gross_return"].sum()
    assert metrics["equity_curve_summary"]["status"] == "valid"
    assert metrics["equity_curve_summary"]["equity_reproducible_from_daily_net_returns"] is True
    assert metrics["equity_curve_summary"]["net_CAGR"] is not None
    assert len(fold_results) == 2
    assert all(result["test_days"] > 0 for result in fold_results)


def test_m6_validate_inputs_evidence_writes_fail_closed_artifact(tmp_path: Path) -> None:
    d1 = tmp_path / "d1.json"
    d2a = tmp_path / "d2a.json"
    d2b = tmp_path / "d2b.json"
    m5a = tmp_path / "m5a.json"
    out = tmp_path / "m6.json"
    d1.write_text(json.dumps(_strict_d1_manifest(current_vintage=True)), encoding="utf-8")
    d2a.write_text(json.dumps(_d2a_manifest(crsp=False, price_fallback=5)), encoding="utf-8")
    d2b.write_text(json.dumps(_d2b_manifest(delisting=False)), encoding="utf-8")
    m5a.write_text(json.dumps({"artifact_name": "pead_m5a_net_multifactor_alpha_test", "scope_id": "M5A", "data_validity_flags": {"diagnostic_only": True}}), encoding="utf-8")

    rc = m6.main([
        "--validate-inputs",
        "--d1-manifest",
        str(d1),
        "--d2a-manifest",
        str(d2a),
        "--d2b-manifest",
        str(d2b),
        "--m5a-evidence",
        str(m5a),
        "--output",
        str(out),
    ])

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["workflow_status"] == "blocked_fail_closed"
    assert payload["daily_return_summary"]["status"] == "not_emitted"
    assert payload["data_validity_flags"]["daily_returns_emitted"] is False
    assert payload["data_validity_flags"]["m6a_scale_engine_ready"] is True
    assert payload["data_validity_flags"]["m6b_real_run_wiring_allowed"] is True
    assert payload["data_validity_flags"]["m6b_data_contract_ready"] is False
    assert payload["engine_runtime"]["dense_return_date_by_security_matrix_materialized"] is False
    assert payload["engine_runtime"]["duckdb_memory_limit"] == "1024MB"
    assert payload["claim_boundary"]["eps_vintage_status"] == "release_date_aligned_but_restated"


def test_m6_run_returns_nonzero_when_inputs_are_blocked(tmp_path: Path) -> None:
    d1 = tmp_path / "d1.json"
    d2a = tmp_path / "d2a.json"
    d2b = tmp_path / "d2b.json"
    m5a = tmp_path / "m5a.json"
    out = tmp_path / "m6.json"
    d1.write_text(json.dumps(_strict_d1_manifest(current_vintage=True)), encoding="utf-8")
    d2a.write_text(json.dumps(_d2a_manifest(crsp=False, price_fallback=5)), encoding="utf-8")
    d2b.write_text(json.dumps(_d2b_manifest(delisting=False)), encoding="utf-8")
    m5a.write_text(json.dumps({}), encoding="utf-8")

    rc = m6.main([
        "--run",
        "--d1-manifest",
        str(d1),
        "--d2a-manifest",
        str(d2a),
        "--d2b-manifest",
        str(d2b),
        "--m5a-evidence",
        str(m5a),
        "--output",
        str(out),
    ])

    assert rc == 2
    assert json.loads(out.read_text(encoding="utf-8"))["workflow_status"] == "blocked_fail_closed"


def test_m6_sparse_turnover_matches_entry_exit_and_overlapping_cohort_parity() -> None:
    events = pd.DataFrame(
        [
            {"event_id": "A_short", "security_id": "S_A", "decision_date": "2024-01-01", "signal": 0.0, "tradable": True, "liquidity_pass": True},
            {"event_id": "A_long", "security_id": "L_A", "decision_date": "2024-01-01", "signal": 1.0, "tradable": True, "liquidity_pass": True},
            {"event_id": "B_short", "security_id": "S_B", "decision_date": "2024-01-02", "signal": 0.0, "tradable": True, "liquidity_pass": True},
            {"event_id": "B_long", "security_id": "L_B", "decision_date": "2024-01-02", "signal": 1.0, "tradable": True, "liquidity_pass": True},
        ]
    )
    returns = pd.DataFrame(
        [
            {"security_id": security_id, "return_date": date, "tradable_total_return": 0.0}
            for security_id in ["S_A", "L_A", "S_B", "L_B"]
            for date in pd.bdate_range("2024-01-02", periods=3)
        ]
    )

    daily = m6.build_daily_portfolio_returns(
        events,
        returns,
        portfolio_config=m6.PortfolioConfig(holding_period_sessions=2, quantiles=2, long_quantile=2, short_quantile=1, min_leg_count=1),
        cost_model=m6.CostModel(entry_cost_bps=5.0, exit_cost_bps=5.0, slippage_bps=1.0, daily_short_borrow_bps=0.5),
    )

    assert daily["return_date"].dt.strftime("%Y-%m-%d").tolist() == ["2024-01-02", "2024-01-03", "2024-01-04"]
    assert daily["turnover"].tolist() == pytest.approx([1.0, 1.0, 2.0])
    assert daily["average_gross_exposure"].tolist() == pytest.approx([1.0, 1.0, 1.0])
    assert daily["daily_gross_return"].tolist() == pytest.approx([0.0, 0.0, 0.0])
    assert daily.iloc[-1]["turnover"] == pytest.approx(2.0)  # 1.0 rebalance plus 1.0 final trade-to-zero exit.


def test_m6_sparse_engine_has_calendar_index_projection_and_no_dense_weight_pivot() -> None:
    source = inspect.getsource(m6.build_daily_portfolio_returns)
    runtime = m6.engine_runtime_contract(m6.PortfolioConfig())

    for forbidden in ("itertuples", "position_rows", "pivot_table", "ASOF JOIN"):
        assert forbidden not in source
    assert "ret.return_idx BETWEEN event.entry_idx AND event.exit_idx" in source
    assert runtime["engine_architecture"] == "duckdb_sparse_interval_window_join_direct_daily_aggregate_v2"
    assert runtime["calendar_index"]["index_name"] == "return_idx"
    assert runtime["calendar_index"]["index_dtype"] == "int32"
    assert runtime["calendar_index"]["entry_exit_predicate"] == "entry_idx <= return_idx <= exit_idx"
    assert runtime["input_projection"]["duckdb_identifier_dtype"] == "int32"
    assert runtime["input_projection"]["duckdb_object_dtype_relations_forbidden"] is True
    assert runtime["determinism"]["compensated_fsum_aggregates"] is True
    assert runtime["determinism"]["single_duckdb_thread"] is True
    assert runtime["determinism"]["canonical_daily_output_sha256"] is True
    assert runtime["python_event_row_loop"] is False
    assert runtime["dense_return_date_by_security_matrix_materialized"] is False
    assert runtime["turnover_rule"].endswith("final trade-to-zero exit")


def test_m6_calendar_index_relations_are_int32_and_bound_sparse_intervals() -> None:
    events = pd.DataFrame(
        [
            {"event_id": "short", "security_id": "S", "decision_date": "2024-01-05", "signal": 0.0, "tradable": True, "liquidity_pass": True},
            {"event_id": "long", "security_id": "L", "decision_date": "2024-01-05", "signal": 1.0, "tradable": True, "liquidity_pass": True},
        ]
    )
    returns = pd.DataFrame(
        [
            {"security_id": security_id, "return_date": return_date, "tradable_total_return": 0.001}
            for security_id in ["S", "L"]
            for return_date in pd.bdate_range("2024-01-08", periods=3)
        ]
    )
    config = m6.PortfolioConfig(holding_period_sessions=2, quantiles=2, long_quantile=2, short_quantile=1, min_leg_count=1)

    selected_events, input_returns, trading_calendar = m6._prepare_sparse_engine_relations(events, returns, config)

    assert selected_events["entry_idx"].tolist() == [0, 0]
    assert selected_events["exit_idx"].tolist() == [1, 1]
    assert input_returns["return_idx"].tolist() == [0, 1, 2, 0, 1, 2]
    assert trading_calendar["return_idx"].tolist() == [0, 1, 2]
    for relation in (selected_events, input_returns, trading_calendar):
        assert not any(dtype == object for dtype in relation.dtypes)
    assert str(selected_events["event_idx"].dtype) == "int32"
    assert str(selected_events["security_idx"].dtype) == "int32"
    assert str(input_returns["return_idx"].dtype) == "int32"


def test_m6_daily_output_hash_is_deterministic_across_input_order() -> None:
    events, returns = _synthetic_events_and_returns()
    config = m6.PortfolioConfig(holding_period_sessions=5, min_leg_count=2)

    baseline = m6.build_daily_portfolio_returns(events, returns, portfolio_config=config)
    shuffled = m6.build_daily_portfolio_returns(
        events.sample(frac=1.0, random_state=19).reset_index(drop=True),
        returns.sample(frac=1.0, random_state=23).reset_index(drop=True),
        portfolio_config=config,
    )

    assert m6.daily_portfolio_output_hash(baseline) == m6.daily_portfolio_output_hash(shuffled)
    pd.testing.assert_frame_equal(baseline, shuffled, check_exact=True)


def test_m6_sparse_engine_full_universe_smoke_stays_under_memory_cap_and_latency_budget() -> None:
    event_count = 196_638
    security_count = 1_024
    holding_period_sessions = 60
    event_ids = np.arange(event_count, dtype=np.int64)
    events = pd.DataFrame(
        {
            "event_id": event_ids,
            "security_id": event_ids % security_count,
            "decision_date": pd.Timestamp("2024-01-01"),
            "signal": event_ids.astype(float),
            "tradable": True,
            "liquidity_pass": True,
        }
    )
    returns = pd.DataFrame(
        {
            "security_id": np.repeat(np.arange(security_count, dtype=np.int64), holding_period_sessions),
            "return_date": np.tile(pd.bdate_range("2024-01-02", periods=holding_period_sessions), security_count),
            "tradable_total_return": 0.001,
        }
    )
    config = m6.PortfolioConfig(
        holding_period_sessions=holding_period_sessions,
        quantiles=2,
        long_quantile=2,
        short_quantile=1,
        min_leg_count=1,
    )

    started = time.perf_counter()
    daily = m6.build_daily_portfolio_returns(events, returns, portfolio_config=config)
    elapsed_seconds = time.perf_counter() - started

    assert event_count * holding_period_sessions == 11_798_280
    assert len(daily) == holding_period_sessions
    assert daily["return_date"].nunique() == holding_period_sessions
    assert daily["turnover"].notna().all()
    assert m6.engine_runtime_contract(config)["duckdb_memory_limit"] == "1024MB"
    assert elapsed_seconds < 60.0
