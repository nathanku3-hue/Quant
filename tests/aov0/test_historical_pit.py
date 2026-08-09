from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.aov0.ciq_market import (
    _derive_market_features,
    _parse_market_raw,
    build_ciq_market_slice,
    normalize_primary_security_master,
)
from research.aov0.cube import build_vertical_cube
from research.aov0.experiment import run_five_arm_experiment
from research.aov0.historical_pit import (
    HISTORICAL_PIT_MODE,
    REQUIRED_RELATIVE_PERIODS,
    HistoricalFactorStates,
    activate_decision_targets,
    build_factor_transition_plan,
    build_historical_factor_states,
    build_historical_market_panel,
    build_historical_replay_inputs,
    completed_week_decision_dates,
    expand_transition_fundamentals,
    historical_cash_from_official_sofr_rows,
    normalize_historical_pit_fundamentals,
    validate_historical_session_continuity,
)


def _provider_snapshot(as_of: pd.Timestamp, entities: tuple[str, ...] = ("1", "2", "3", "4")) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    quarter_ends = list(reversed(pd.date_range(end=as_of, periods=5, freq="QE-DEC")))
    for entity_index, entity in enumerate(entities):
        scale = 1.0 + 0.15 * entity_index
        for relative_period, period_end in zip(REQUIRED_RELATIVE_PERIODS, quarter_ends, strict=True):
            q = int(relative_period.replace("FQ", "") or "0")
            age = abs(q)
            revenue = (100.0 + 7.0 * (4 - age) + 5.0 * entity_index) * scale
            assets = (300.0 + 4.0 * age + 10.0 * entity_index) * scale
            inventory = (30.0 + age + entity_index) * scale
            records.append(
                {
                    "as_of_date": as_of,
                    "source_entity_id": entity,
                    "relative_period": relative_period,
                    "period_end": period_end,
                    "IQ_TOTAL_REV": revenue,
                    "IQ_TOTAL_ASSETS": assets,
                    "IQ_INVENTORY": inventory,
                    "IQ_DA_SUPPL_CF": 3.0 * scale,
                    "IQ_TOTAL_EQUITY": 160.0 * scale,
                    "IQ_TOTAL_DEBT": 60.0 * scale,
                    "IQ_CASH_ST_INVEST": 20.0 * scale,
                    "IQ_OPER_INC": (12.0 + 1.5 * (4 - age) + entity_index) * scale,
                    "IQ_CAPEX_BNK": 6.0 * scale,
                    "filing_version": "Original",
                    "provider_function": "SPG",
                }
            )
    return pd.DataFrame(records)


def _master() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "SP_ENTITY_ID": ["1", "2", "3", "4"],
            "SP_SECURITY_ID": ["101", "202", "303", "404"],
            "SPT_INSTRUMENT_ITEM_ID": ["SPT101", "SPT202", "SPT303", "SPT404"],
            "Primary Security Flag": ["Yes"] * 4,
            "Ticker": ["AAA", "BBB", "CCC", "DDD"],
            "Exchange": ["NASDAQ", "NYSE", "NYSE", "NASDAQ"],
            "Description": ["Common Stock"] * 4,
        }
    )


def _market() -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    dates = pd.bdate_range("2024-01-02", periods=285)
    frames: list[pd.DataFrame] = []
    for entity_index, (security, trading) in enumerate(
        (("101", "SPT101"), ("202", "SPT202"), ("303", "SPT303"), ("404", "SPT404"))
    ):
        x = np.arange(len(dates), dtype=float)
        close = 40.0 + (0.06 + 0.01 * entity_index) * x + 0.05 * np.sin(x / 7.0 + entity_index)
        total_return_pct = 0.08 + 0.04 * np.sin(x / 11.0 + entity_index)
        volume = 900_000.0 + 25_000.0 * entity_index + 1_000.0 * (x % 13)
        frames.append(
            pd.DataFrame(
                {
                    "SPT_DATE": dates,
                    "SP_SECURITY_ID": security,
                    "SPT_INSTRUMENT_ITEM_ID": trading,
                    "SPT_CLOSE": close,
                    "SPT_VOLUME": volume,
                    "SPT_TOTAL_RETURN": total_return_pct,
                }
            )
        )
    return pd.concat(frames, ignore_index=True), dates


def test_historical_pit_fundamentals_require_original_spg_and_fq0() -> None:
    raw = _provider_snapshot(pd.Timestamp("2025-05-23"))
    normalized = normalize_historical_pit_fundamentals(raw)
    assert normalized["pit_mode"].eq(HISTORICAL_PIT_MODE).all()
    assert normalized["known_at"].dt.tz is not None

    bad = raw.copy()
    bad.loc[0, "filing_version"] = "Current/Restated"
    with pytest.raises(ValueError, match="filing_version_not_original"):
        normalize_historical_pit_fundamentals(bad)

    missing_fq0 = raw.loc[~((raw["source_entity_id"] == "1") & (raw["relative_period"] == "FQ0"))]
    with pytest.raises(ValueError, match="fq0_missing"):
        normalize_historical_pit_fundamentals(missing_fq0)


def test_factor_state_recomputed_per_historical_asof() -> None:
    dates = [pd.Timestamp("2025-05-23"), pd.Timestamp("2025-05-30")]
    raw = pd.concat([_provider_snapshot(date) for date in dates], ignore_index=True)
    built = build_historical_factor_states(raw, frozen_entity_ids={"1", "2", "3", "4"})
    assert list(built.snapshot_dates) == dates
    assert len(built.frame) == 8
    assert built.frame.groupby("as_of_date")["source_entity_id"].nunique().eq(4).all()
    assert built.frame["factor_present_count"].between(0, 4).all()
    assert built.frame["factor_positive_count"].between(0, 4).all()


def test_transition_plan_is_sparse_and_forward_fill_never_uses_future_snapshot() -> None:
    first_date = pd.Timestamp("2025-05-23")
    middle_date = pd.Timestamp("2025-05-30")
    change_date = pd.Timestamp("2025-09-05")
    first = normalize_historical_pit_fundamentals(_provider_snapshot(first_date))
    changed = normalize_historical_pit_fundamentals(_provider_snapshot(change_date))
    first_fq0 = first.loc[first["relative_period"].eq("FQ0")].set_index("source_entity_id")["period_end"]
    changed_fq0 = changed.loc[changed["relative_period"].eq("FQ0")].set_index("source_entity_id")["period_end"]

    period_rows = []
    for entity in ("1", "2", "3", "4"):
        for as_of, period_end in (
            (first_date, first_fq0.loc[entity]),
            (middle_date, first_fq0.loc[entity]),
            (change_date, changed_fq0.loc[entity]),
        ):
            period_rows.append(
                {
                    "as_of_date": as_of,
                    "source_entity_id": entity,
                    "fq0_period_end": period_end,
                }
            )
    matrix = pd.DataFrame(period_rows)
    plan = build_factor_transition_plan(matrix)
    assert len(plan) == 8
    assert set(plan["transition_reason"]) == {"INITIAL", "FQ0_PERIOD_CHANGE"}

    transition_raw = pd.concat(
        [_provider_snapshot(first_date), _provider_snapshot(change_date)],
        ignore_index=True,
    )
    expanded = expand_transition_fundamentals(matrix, transition_raw)
    assert expanded.groupby(["as_of_date", "source_entity_id"]).size().eq(5).all()
    middle = expanded.loc[expanded["as_of_date"].eq(middle_date)]
    assert middle["source_transition_as_of_date"].eq(first_date).all()
    changed_rows = expanded.loc[expanded["as_of_date"].eq(change_date)]
    assert changed_rows["source_transition_as_of_date"].eq(change_date).all()

    missing = matrix.copy()
    missing.loc[0, "fq0_period_end"] = pd.NaT
    with pytest.raises(ValueError, match="period_matrix_fq0_missing"):
        build_factor_transition_plan(missing)


def test_market_overlap_must_reconcile_and_replay_is_weekly_one_bar_ready() -> None:
    raw_market, dates = _market()
    midpoint = pd.Timestamp(dates[230])
    part_a = raw_market.loc[pd.to_datetime(raw_market["SPT_DATE"]).le(midpoint)].copy()
    part_b = raw_market.loc[pd.to_datetime(raw_market["SPT_DATE"]).ge(midpoint)].copy()
    market = build_historical_market_panel(
        security_master_raw=_master(),
        market_parts=[part_a, part_b],
        frozen_entity_ids={"1", "2", "3", "4"},
    )
    assert market.frame.duplicated(["date", "security_id"]).sum() == 0

    eligible_calendar = pd.DatetimeIndex(dates[210:281])
    decisions = completed_week_decision_dates(eligible_calendar)
    start = decisions[0]
    end = eligible_calendar[-1]
    replay_calendar = eligible_calendar[(eligible_calendar >= start) & (eligible_calendar <= end)]
    decisions = completed_week_decision_dates(replay_calendar)
    raw_fundamentals = pd.concat([_provider_snapshot(date) for date in decisions], ignore_index=True)
    states = build_historical_factor_states(raw_fundamentals, frozen_entity_ids={"1", "2", "3", "4"})

    replay = build_historical_replay_inputs(
        market_panel=market,
        factor_states=states,
        evaluation_start=start,
        evaluation_end=end,
    )
    assert replay.rule100_weights.index.equals(replay.total_returns.index)
    assert replay.decision_rule100_weights.index.equals(replay.decision_dates)
    first_activation = eligible_calendar[eligible_calendar.get_loc(start) + 1]
    assert replay.rule100_weights.index.min() == first_activation
    assert replay.activation_dates[0] == first_activation
    assert replay.decision_to_activation[start] == first_activation
    assert replay.rule100_weights.shape[1] == 4
    assert replay.primitives.groupby("date")["security_id"].nunique().eq(4).all()
    changed = replay.rule100_weights.ne(replay.rule100_weights.shift(1)).any(axis=1)
    changed.iloc[0] = True
    assert set(replay.rule100_weights.index[changed]).issubset(set(replay.activation_dates))
    assert replay.metadata["decision_start"] == start.date().isoformat()
    assert replay.metadata["evaluation_start"] == first_activation.date().isoformat()
    assert replay.metadata["financial_alpha_evidence"] == 0

    parent_like = replay.decision_rule100_weights * 0.5
    activated_parent = activate_decision_targets(parent_like, replay)
    assert activated_parent.index.equals(replay.total_returns.index)
    assert activated_parent.loc[first_activation].equals(parent_like.loc[start])

    conflicting = part_b.copy()
    overlap_mask = pd.to_datetime(conflicting["SPT_DATE"]).eq(midpoint) & conflicting["SP_SECURITY_ID"].eq("101")
    conflicting.loc[overlap_mask, "SPT_CLOSE"] = conflicting.loc[overlap_mask, "SPT_CLOSE"] + 1.0
    with pytest.raises(ValueError, match="overlap_value_conflict:close"):
        build_historical_market_panel(
            security_master_raw=_master(),
            market_parts=[part_a, conflicting],
            frozen_entity_ids={"1", "2", "3", "4"},
        )


def test_historical_market_technicals_match_current_cut_kernel_same_input() -> None:
    raw_market, _dates = _market()
    security_map, _ = normalize_primary_security_master(
        _master(), frozen_entity_ids={"1", "2", "3", "4"}
    )
    parsed = _parse_market_raw(raw_market, security_map)
    fundamentals = pd.DataFrame(
        {
            "source_entity_id": ["1", "2", "3", "4"],
            "factor_present_count": [4, 4, 4, 4],
            "factor_positive_count": [4, 3, 2, 4],
        }
    )
    current = _derive_market_features(
        parsed,
        fundamentals,
        admission_time=pd.Timestamp("2026-01-01T00:00:00Z").to_pydatetime(),
    )
    historical = build_historical_market_panel(
        security_master_raw=_master(),
        market_parts=[raw_market],
        frozen_entity_ids={"1", "2", "3", "4"},
    ).frame

    columns = [
        "dollar_volume",
        "adv20",
        "realized_vol",
        "sma20",
        "sma200",
        "dist_sma20",
        "trend_fast",
        "trend_slow",
    ]
    left = current.sort_values(["date", "security_id"]).reset_index(drop=True)
    right = historical.sort_values(["date", "security_id"]).reset_index(drop=True)
    assert left[["date", "security_id", "trading_item_id"]].equals(
        right[["date", "security_id", "trading_item_id"]]
    )
    for column in columns:
        np.testing.assert_allclose(
            pd.to_numeric(left[column], errors="coerce").to_numpy(dtype=float),
            pd.to_numeric(right[column], errors="coerce").to_numpy(dtype=float),
            rtol=0.0,
            atol=1e-12,
            equal_nan=True,
        )
    assert left["trend_veto"].astype("boolean").equals(
        right["trend_veto"].astype("boolean")
    )


def test_historical_decision_cut_matches_current_rule100_and_activated_cube(tmp_path) -> None:
    raw_market, dates = _market()
    market = build_historical_market_panel(
        security_master_raw=_master(),
        market_parts=[raw_market],
        frozen_entity_ids={"1", "2", "3", "4"},
    )
    start = next(pd.Timestamp(day) for day in dates[210:] if pd.Timestamp(day).weekday() == 4)
    end = pd.Timestamp(dates[dates.get_loc(start) + 4])

    built = build_historical_factor_states(
        _provider_snapshot(start), frozen_entity_ids={"1", "2", "3", "4"}
    )
    factor = built.frame.copy()
    factor.loc[factor["source_entity_id"].eq("4"), "factor_present_count"] = 2
    factor.loc[factor["source_entity_id"].eq("4"), "factor_positive_count"] = 2
    states = HistoricalFactorStates(
        frame=factor,
        snapshot_dates=pd.DatetimeIndex([start]),
        frozen_entity_ids=built.frozen_entity_ids,
    )
    replay = build_historical_replay_inputs(
        market_panel=market,
        factor_states=states,
        evaluation_start=start,
        evaluation_end=end,
    )
    first_activation = pd.Timestamp(replay.activation_dates[0])

    gate_state = factor.copy()
    gate_state["known_at"] = start.tz_localize("UTC") + pd.Timedelta(
        hours=23, minutes=59, seconds=59
    )
    actual_known = pd.to_datetime(factor["known_at"], utc=True).max()
    current = build_ciq_market_slice(
        security_master_raw=_master(),
        market_raw=raw_market.loc[pd.to_datetime(raw_market["SPT_DATE"]).le(start)].copy(),
        fundamental_state=gate_state,
        admission_time=actual_known.to_pydatetime(),
        target_date=start,
    )

    current_active = tuple(sorted(current.rule100_targets.columns.astype(str)))
    assert current_active == replay.eligible_by_date[first_activation]
    assert "CIQSEC:404" not in current_active
    assert replay.decision_rule100_weights.loc[start, "CIQSEC:404"] == 0.0

    expected_weights = pd.Series(0.0, index=replay.decision_rule100_weights.columns, dtype=float)
    expected_weights.loc[current.rule100_targets.columns] = current.rule100_targets.loc[start]
    np.testing.assert_allclose(
        replay.decision_rule100_weights.loc[start].to_numpy(dtype=float),
        expected_weights.to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-12,
    )

    current_target = current.market_features.loc[
        pd.to_datetime(current.market_features["date"]).dt.normalize().eq(start)
    ].sort_values("security_id").reset_index(drop=True)
    replay_target = replay.primitives.loc[
        pd.to_datetime(replay.primitives["date"]).dt.normalize().eq(start)
    ].sort_values("security_id").reset_index(drop=True)
    assert current_target[["security_id", "trading_item_id"]].equals(
        replay_target[["security_id", "trading_item_id"]]
    )
    parity_columns = [
        "total_return",
        "realized_vol",
        "dollar_volume",
        "adv20",
        "quality",
        "trend_fast",
        "trend_slow",
        "exit_capacity",
        "regime",
        "uncertainty",
        "dist_sma20",
        "technical_quality",
        "factor_present_count",
        "factor_positive_count",
    ]
    for column in parity_columns:
        np.testing.assert_allclose(
            pd.to_numeric(current_target[column], errors="coerce").to_numpy(dtype=float),
            pd.to_numeric(replay_target[column], errors="coerce").to_numpy(dtype=float),
            rtol=0.0,
            atol=1e-12,
            equal_nan=True,
        )
    assert current_target["trend_veto"].astype(bool).equals(
        replay_target["trend_veto"].astype(bool)
    )
    assert current_target["sizing_eligible"].astype(bool).equals(
        replay_target["sizing_eligible"].astype(bool)
    )

    current_cube = build_vertical_cube(
        current.market_features,
        computed_at=pd.to_datetime(current.market_features["known_at"], utc=True).max().isoformat(),
    )
    current_state = current_cube.frame.loc[
        pd.to_datetime(current_cube.frame["date"]).dt.normalize().eq(start)
    ].set_index("security_id")
    replay_state = replay.cube.frame.loc[
        pd.to_datetime(replay.cube.frame["date"]).dt.normalize().eq(first_activation)
    ].set_index("security_id")
    np.testing.assert_allclose(
        replay_state.loc[list(current_active), ["Q", "M", "F_proxy", "C_proxy", "L", "R", "U"]].to_numpy(dtype=float),
        current_state.loc[list(current_active), ["Q", "M", "F_proxy", "C_proxy", "L", "R", "U"]].to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-12,
    )
    neutral = replay_state.loc["CIQSEC:404"]
    assert neutral[["Q", "M", "F_proxy", "C_proxy", "R"]].astype(float).eq(0.0).all()
    assert float(neutral["L"]) == 0.5
    assert float(neutral["U"]) == 1.0
    assert replay.cube.frame.groupby("date")["security_id"].nunique().eq(4).all()
    assert set(pd.DatetimeIndex(replay.cube.frame["date"]).normalize()) == set(replay.rule100_weights.index)

    experiment = run_five_arm_experiment(
        rule100_weights=replay.rule100_weights,
        returns_df=replay.total_returns,
        economic_cash_returns=pd.Series(
            0.0, index=replay.rule100_weights.index, name="economic_cash", dtype=float
        ),
        cube=replay.cube,
        pit_eligibility_provider=lambda date: replay.eligible_by_date[
            pd.Timestamp(date).normalize()
        ],
        output_root=tmp_path / "historical_parity_five_arm",
    )
    assert set(experiment.arm_metrics) == {
        "rule100",
        "parent",
        "child",
        "pit_equal_weight",
        "economic_cash",
    }
    assert all(run.status.value != "blocked" for run in experiment.runs.values())


def test_historical_session_continuity_rejects_missing_market_week() -> None:
    valid = pd.DatetimeIndex(["2025-05-22", "2025-05-23", "2025-05-27"])
    assert validate_historical_session_continuity(valid).equals(valid)
    with pytest.raises(ValueError, match="historical_market_calendar_gap"):
        validate_historical_session_continuity(
            pd.DatetimeIndex(["2025-05-23", "2025-06-02"])
        )


def test_historical_cash_uses_only_strictly_prior_official_effective_date() -> None:
    dates = pd.DatetimeIndex(["2025-05-23", "2025-05-27", "2025-05-28"])
    sofr = pd.DataFrame(
        {
            "effectiveDate": ["2025-05-22", "2025-05-23", "2025-05-27"],
            "percentRate": [4.30, 4.31, 4.32],
        }
    )
    cash = historical_cash_from_official_sofr_rows(dates, sofr)
    assert cash.iloc[0] == 0.0
    expected_first = (0.0430 - 0.0025) * 4.0 / 360.0
    expected_second = (0.0431 - 0.0025) * 1.0 / 360.0
    assert cash.iloc[1] == pytest.approx(expected_first)
    assert cash.iloc[2] == pytest.approx(expected_second)
