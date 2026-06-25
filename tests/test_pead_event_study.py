from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from strategies.pead_event_study import PeadEventStudyConfig
from strategies.pead_event_study import PeadCalendarTimeInferenceConfig
from strategies.pead_event_study import build_calendar_time_inference
from strategies.pead_event_study import build_event_windows
from strategies.pead_event_study import run_pead_event_study
from strategies.pead_event_study import summarize_event_windows
from strategies.pead_event_study import summarize_quantile_performance


def _event(event_id: str = "E1", event_date: str = "2024-01-02", sue: float = 1.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_id": [event_id],
            "issuer_id": ["1001"],
            "security_id": ["1001-01"],
            "event_date": [event_date],
            "sue": [sue],
            "is_primary_security": [True],
        }
    )


def test_event_window_starts_next_trading_day_and_requires_all_sixty_observations():
    dates = pd.bdate_range("2024-01-02", periods=61)
    returns = pd.DataFrame(
        {
            "security_id": "1001-01",
            "date": dates,
            "total_return": np.full(len(dates), 0.001),
        }
    )

    windows = build_event_windows(_event(), returns, dates)

    assert len(windows) == 60
    assert windows.iloc[0]["event_day"] == 1
    assert windows.iloc[0]["return_date"] == pd.Timestamp("2024-01-03")
    assert pd.Timestamp("2024-01-02") not in set(windows["return_date"])
    assert windows.iloc[-1]["event_day"] == 60
    assert windows["window_complete"].all()
    assert windows["return_observations"].eq(60).all()


def test_incomplete_window_is_visible_and_excluded_from_analysis():
    sessions = pd.bdate_range("2024-01-03", periods=60)
    returns = pd.DataFrame(
        {
            "security_id": ["1001-01", "1001-01"],
            "date": pd.to_datetime(["2024-01-03", "2024-01-04"]),
            "total_return": [0.01, np.nan],
        }
    )

    windows = build_event_windows(_event(), returns, sessions)
    outcomes = summarize_event_windows(windows)

    assert len(windows) == 60
    assert not windows["window_complete"].any()
    assert outcomes.loc[0, "coverage_reason"] == "missing_asset_return"
    assert not outcomes.loc[0, "eligible_for_analysis"]
    assert np.isnan(outcomes.loc[0, "cumulative_total_return"])


def test_missing_middle_security_return_does_not_compress_event_time():
    sessions = pd.bdate_range("2024-01-03", periods=60)
    observed = sessions.delete(1)
    returns = pd.DataFrame(
        {
            "security_id": "1001-01",
            "date": observed,
            "total_return": np.full(len(observed), 0.001),
        }
    )

    windows = build_event_windows(_event(), returns, sessions)
    missing_row = windows.loc[windows["return_date"] == sessions[1]].iloc[0]

    assert len(windows) == 60
    assert missing_row["event_day"] == 2
    assert np.isnan(missing_row["asset_return"])
    assert not windows["window_complete"].any()


def test_car_and_bhar_use_explicit_benchmark_formulas():
    config = PeadEventStudyConfig(
        start_day=1,
        end_day=2,
        benchmark_return_column="benchmark_return",
        quantiles=2,
    )
    returns = pd.DataFrame(
        {
            "security_id": ["1001-01", "1001-01", "1001-01"],
            "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
            "total_return": [0.99, 0.10, -0.05],
            "benchmark_return": [0.99, 0.02, 0.01],
        }
    )

    result = run_pead_event_study(_event(), returns, pd.to_datetime(["2024-01-03", "2024-01-04"]), config)
    outcome = result.event_outcomes.iloc[0]

    assert result.outcome_column == "car"
    assert outcome["cumulative_total_return"] == pytest.approx((1.10 * 0.95) - 1.0)
    assert outcome["cumulative_benchmark_return"] == pytest.approx((1.02 * 1.01) - 1.0)
    assert outcome["car"] == pytest.approx((0.10 - 0.02) + (-0.05 - 0.01))
    assert outcome["bhar"] == pytest.approx(((1.10 * 0.95) - 1.0) - ((1.02 * 1.01) - 1.0))


@pytest.mark.parametrize(
    ("events", "returns", "match"),
    [
        (
            pd.DataFrame(
                {
                    "event_id": ["E1", "E1"],
                    "issuer_id": ["A", "B"],
                    "security_id": ["A", "B"],
                    "event_date": ["2024-01-02", "2024-01-02"],
                    "sue": [1.0, 2.0],
                    "is_primary_security": [True, True],
                }
            ),
            pd.DataFrame(columns=["security_id", "date", "total_return"]),
            "event_id must be unique",
        ),
        (
            _event(),
            pd.DataFrame(
                {
                    "security_id": ["1001-01", "1001-01"],
                    "date": ["2024-01-03", "2024-01-03"],
                    "total_return": [0.01, 0.02],
                }
            ),
            "unique by security_id,date",
        ),
        (
            _event(),
            pd.DataFrame(
                {
                    "security_id": ["1001-01"],
                    "date": ["2024-01-03"],
                    "total_return": [-1.01],
                }
            ),
            "below -100%",
        ),
    ],
)
def test_schema_contract_fails_closed(events: pd.DataFrame, returns: pd.DataFrame, match: str):
    with pytest.raises(ValueError, match=match):
        build_event_windows(events, returns, pd.bdate_range("2024-01-03", periods=60))


def test_date_and_config_validation_fail_closed():
    returns = pd.DataFrame(
        {"security_id": ["1001-01"], "date": [20240103], "total_return": [0.01]}
    )
    with pytest.raises(ValueError, match="not numeric epoch"):
        build_event_windows(_event(), returns, pd.bdate_range("2024-01-03", periods=60))
    with pytest.raises(ValueError, match="timezone"):
        build_event_windows(_event(event_date="2024-01-02T23:00:00Z"), pd.DataFrame(columns=["security_id", "date", "total_return"]), pd.bdate_range("2024-01-03", periods=60))
    with pytest.raises(ValueError, match="reserved column"):
        build_event_windows(
            _event(),
            pd.DataFrame(columns=["security_id", "date", "total_return"]),
            pd.bdate_range("2024-01-03", periods=60),
            PeadEventStudyConfig(benchmark_return_column="total_return"),
        )
    with pytest.raises(TypeError, match="start_day"):
        build_event_windows(
            _event(),
            pd.DataFrame(columns=["security_id", "date", "total_return"]),
            pd.bdate_range("2024-01-03", periods=60),
            PeadEventStudyConfig(start_day=1.5),  # type: ignore[arg-type]
        )


def test_malformed_window_complete_is_rejected_before_quantiles():
    outcomes = pd.DataFrame(
        {
            "event_id": ["E1", "E2", "E3", "E4", "E5"],
            "event_date": pd.to_datetime(["2024-01-15"] * 5),
            "sue": [1.0, 2.0, 3.0, 4.0, 5.0],
            "window_complete": ["False", True, True, True, True],
            "cumulative_total_return": [0.01, 0.02, 0.03, 0.04, 0.05],
        }
    )

    with pytest.raises(ValueError, match="strict boolean"):
        summarize_quantile_performance(outcomes, "cumulative_total_return", PeadEventStudyConfig())


def test_quantile_spread_is_cohort_based_and_hac_is_reported():
    rows: list[dict[str, object]] = []
    for cohort_index, quarter_start in enumerate(pd.to_datetime(["2023-01-15", "2023-04-15", "2023-07-15", "2023-10-15"])):
        cohort_scale = [0.8, 1.1, 0.9, 1.3][cohort_index]
        for rank in range(1, 11):
            rows.append(
                {
                    "event_id": f"{cohort_index}-{rank}",
                    "event_date": quarter_start,
                    "sue": float(rank),
                    "window_complete": True,
                    "car": cohort_scale * rank / 100.0,
                }
            )
    outcomes = pd.DataFrame(rows)
    config = PeadEventStudyConfig(
        benchmark_return_column="benchmark_return",
        quantiles=5,
        cohort_frequency="Q",
        allow_ex_post_cohorts=True,
        hac_maxlags=1,
    )

    result = summarize_quantile_performance(outcomes, "car", config)

    assert result.assignments["quantile_eligible"].all()
    assert set(result.quantile_summary["signal_quantile"].astype(int)) == {1, 2, 3, 4, 5}
    assert len(result.cohort_spreads) == 4
    assert (result.cohort_spreads["high_minus_low"] > 0.0).all()
    assert result.spread_statistics["n_cohorts"] == 4
    assert np.isfinite(result.spread_statistics["hac_standard_error"])
    assert np.isfinite(result.spread_statistics["hac_t_stat"])


def test_small_or_incomplete_cohorts_do_not_receive_quantiles():
    outcomes = pd.DataFrame(
        {
            "event_id": ["E1", "E2", "E3", "E4"],
            "event_date": pd.to_datetime(["2024-01-15"] * 4),
            "sue": [1.0, 2.0, 3.0, 4.0],
            "window_complete": [True, True, True, True],
            "cumulative_total_return": [0.01, 0.02, 0.03, 0.04],
        }
    )

    result = summarize_quantile_performance(
        outcomes,
        "cumulative_total_return",
        PeadEventStudyConfig(quantiles=5),
    )

    assert not result.assignments["quantile_eligible"].any()
    assert result.quantile_summary.empty
    assert result.cohort_spreads.empty
    assert result.spread_statistics["n_cohorts"] == 0


def test_outcome_completeness_does_not_drive_signal_bucket_membership():
    outcomes = pd.DataFrame(
        {
            "event_id": ["E1", "E2", "E3", "E4", "E5"],
            "event_date": pd.to_datetime(["2024-01-15"] * 5),
            "sue": [1.0, 2.0, 3.0, 4.0, 5.0],
            "window_complete": [True, True, True, True, False],
            "cumulative_total_return": [0.01, 0.02, 0.03, 0.04, np.nan],
        }
    )

    result = summarize_quantile_performance(
        outcomes,
        "cumulative_total_return",
        PeadEventStudyConfig(quantiles=5),
    )

    assert result.assignments["signal_bucket_eligible"].all()
    assert result.assignments["signal_quantile"].notna().all()
    assert not result.assignments.loc[result.assignments["event_id"].eq("E5"), "quantile_eligible"].iloc[0]


def test_hac_inference_fails_closed_when_cohort_periods_have_gaps():
    rows: list[dict[str, object]] = []
    for quarter_start in pd.to_datetime(["2023-01-15", "2023-07-15"]):
        for rank in range(1, 11):
            rows.append(
                {
                    "event_id": f"{quarter_start.date()}-{rank}",
                    "event_date": quarter_start,
                    "sue": float(rank),
                    "window_complete": True,
                    "car": rank / 100.0,
                }
            )
    result = summarize_quantile_performance(
        pd.DataFrame(rows),
        "car",
        PeadEventStudyConfig(
            benchmark_return_column="benchmark_return",
            quantiles=5,
            cohort_frequency="Q",
            allow_ex_post_cohorts=True,
        ),
    )

    assert result.spread_statistics["hac_gap_count"] == 1
    assert np.isnan(result.spread_statistics["hac_t_stat"])


def _calendar_row(
    event_id: str,
    event_date: str,
    sue: float,
    security_id: object,
    return_date: str,
    asset_return: float,
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "issuer_id": event_id,
        "security_id": security_id,
        "event_date": pd.Timestamp(event_date),
        "event_day": 1,
        "sue": sue,
        "asset_return": asset_return,
        "return_date": pd.Timestamp(return_date),
        "window_complete": True,
    }


def test_calendar_time_overlap_resolves_all_quantiles_before_extreme_filtering():
    rows = [
        _calendar_row("O1", "2024-01-01", 1.0, "A", "2024-01-03", 0.01),
        _calendar_row("O2", "2024-01-01", 2.0, "O2", "2024-01-03", 0.02),
        _calendar_row("O3", "2024-01-01", 3.0, "O3", "2024-01-03", 0.03),
        _calendar_row("O4", "2024-01-01", 4.0, "O4", "2024-01-03", 0.04),
        _calendar_row("O5", "2024-01-01", 5.0, "B", "2024-01-03", 0.05),
        _calendar_row("N1", "2024-01-02", 1.0, "A", "2024-01-03", np.nan),
        _calendar_row("N2", "2024-01-02", 2.0, "N2", "2024-01-03", 0.02),
        _calendar_row("N3", "2024-01-02", 3.0, "B", "2024-01-03", 0.00),
        _calendar_row("N4", "2024-01-02", 4.0, "N4", "2024-01-03", 0.04),
        _calendar_row("N5", "2024-01-02", 5.0, "C", "2024-01-03", 0.07),
    ]
    factors = pd.DataFrame({"return_date": [pd.Timestamp("2024-01-03")], "mktrf": [0.001]})

    result = build_calendar_time_inference(
        pd.DataFrame(rows),
        factors,
        PeadCalendarTimeInferenceConfig(minimum_finite_per_leg=1, bootstrap_replications=4),
    )

    retained_ids = set(result.exposures["event_id"].astype(str))
    assert {"N1", "N5"}.issubset(retained_ids)
    assert "O1" not in retained_ids
    assert "O5" not in retained_ids
    assert "N3" not in retained_ids
    assert result.session_coverage["q1"]["expected"] == 1
    assert result.session_coverage["q1"]["missing"] == 1
    assert result.session_coverage["q5"]["finite"] == 1


def test_calendar_time_counts_no_security_extreme_as_expected_missing():
    rows = [
        _calendar_row("E1", "2024-01-01", 1.0, "S1", "2024-01-02", 0.01),
        _calendar_row("E2", "2024-01-01", 2.0, "S2", "2024-01-02", 0.02),
        _calendar_row("E3", "2024-01-01", 3.0, "S3", "2024-01-02", 0.03),
        _calendar_row("E4", "2024-01-01", 4.0, "S4", "2024-01-02", 0.04),
        _calendar_row("E5", "2024-01-01", 5.0, pd.NA, "2024-01-02", np.nan),
    ]
    factors = pd.DataFrame({"return_date": [pd.Timestamp("2024-01-02")], "mktrf": [0.001]})

    result = build_calendar_time_inference(
        pd.DataFrame(rows),
        factors,
        PeadCalendarTimeInferenceConfig(minimum_finite_per_leg=1, bootstrap_replications=4),
    )

    assert result.session_coverage["extreme_expected_rows"] == 2
    assert result.session_coverage["extreme_missing_rows"] == 1
    assert result.session_coverage["q5"]["expected"] == 1
    assert result.session_coverage["q5"]["finite"] == 0
    assert result.session_coverage["q5"]["missing"] == 1


def test_calendar_time_primary_inference_uses_hac59_and_robustness_only_bootstrap():
    sessions = pd.bdate_range("2024-01-02", periods=60)
    factors = pd.DataFrame({"return_date": sessions, "mktrf": np.linspace(-0.001, 0.001, len(sessions))})
    rows: list[dict[str, object]] = []
    for rank in range(1, 51):
        security_id = f"S{rank:02d}"
        for event_day, (return_date, mktrf) in enumerate(zip(sessions, factors["mktrf"]), start=1):
            if rank <= 10:
                asset_return = 0.001 + (0.2 * float(mktrf))
            elif rank > 40:
                asset_return = 0.003 + (0.7 * float(mktrf))
            else:
                asset_return = 0.002 + (0.4 * float(mktrf))
            rows.append(
                {
                    "event_id": f"E{rank:02d}",
                    "issuer_id": f"E{rank:02d}",
                    "security_id": security_id,
                    "event_date": pd.Timestamp("2024-01-01"),
                    "event_day": event_day,
                    "sue": float(rank),
                    "asset_return": asset_return,
                    "return_date": return_date,
                    "window_complete": True,
                }
            )

    result = build_calendar_time_inference(
        pd.DataFrame(rows),
        factors,
        PeadCalendarTimeInferenceConfig(bootstrap_replications=32, bootstrap_max_batch_size=8),
    )

    assert result.session_coverage["retained_sessions"] == 60
    assert result.session_coverage["internal_gap_count"] == 0
    assert result.primary_inference["status"] == "valid"
    assert result.primary_inference["hac_maxlags_used"] == 59
    assert result.primary_inference["alpha_ct"] == pytest.approx(0.002)
    assert result.primary_inference["beta_m"] == pytest.approx(0.5)
    assert result.robustness["status"] == "valid"
    assert result.robustness["replications"] == 32
