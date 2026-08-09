from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.aov0.historical_checkpoint import (
    build_historical_aov_decision_checkpoint,
    split_historical_market_custody,
)
from research.aov0.historical_outcome import (
    OUTCOME_AUTHORITY,
    evaluate_historical_aov_outcome,
    verify_historical_aov_outcome,
)


TARGET_DATE = "2025-06-30"
EVALUATION_START = "2025-07-01T20:00:00Z"
MATURITY = "2025-07-31T20:00:00Z"
BINDINGS = {
    "historical_fundamentals": "a" * 64,
    "primary_security_master": "b" * 64,
    "decision_market": "c" * 64,
}


def _fundamentals() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_entity_id": ["1", "2", "3", "4"],
            "factor_present_count": [4, 3, 2, 4],
            "factor_positive_count": [4, 2, 2, 1],
            "known_at": ["2025-06-30T12:00:00Z"] * 4,
            "pit_mode": ["CIQ_VENDOR_HISTORICAL_ASOF_DATE_CONSERVATIVE_BOUNDARY"] * 4,
        }
    )


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


def _full_market() -> pd.DataFrame:
    history = pd.bdate_range(end=TARGET_DATE, periods=210)
    future = pd.bdate_range(start="2025-07-01", end="2025-08-01")
    dates = history.append(future)
    frames = []
    for entity, security, trading, slope, future_bias in (
        ("1", "101", "SPT101", 0.12, 0.40),
        ("2", "202", "SPT202", 0.08, -0.20),
        ("3", "303", "SPT303", 0.10, 0.05),
        ("4", "404", "SPT404", 0.09, 0.10),
    ):
        x = np.arange(len(dates), dtype=float)
        returns = 0.20 + 0.05 * np.sin(x / 5.0)
        returns[len(history) :] += future_bias
        frames.append(
            pd.DataFrame(
                {
                    "SPT_DATE": dates,
                    "SP_SECURITY_ID": security,
                    "SPT_INSTRUMENT_ITEM_ID": trading,
                    "SPT_CLOSE": 50.0 + slope * x + 0.15 * np.sin(x / 3.0),
                    "SPT_VOLUME": 1_000_000.0 + 10_000.0 * (x % 13),
                    "SPT_TOTAL_RETURN": returns,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def _economic_cash() -> pd.Series:
    dates = pd.bdate_range(start="2025-07-01", end="2025-07-31")
    return pd.Series(0.0001, index=dates, name="economic_cash_return")


def _checkpoint_and_outcome_frame():
    decision, outcome = split_historical_market_custody(_full_market(), target_date=TARGET_DATE)
    checkpoint = build_historical_aov_decision_checkpoint(
        security_master_raw=_master(),
        decision_market_raw=decision,
        fundamental_state=_fundamentals(),
        frozen_entity_ids={"1", "2", "3", "4"},
        target_date=TARGET_DATE,
        decision_cut_time="2025-06-30T20:05:00Z",
        source_bindings=BINDINGS,
    )
    return checkpoint, outcome


def test_historical_outcome_uses_canonical_engine_and_starts_after_evaluation_close() -> None:
    checkpoint, outcome_market = _checkpoint_and_outcome_frame()
    outcome = evaluate_historical_aov_outcome(
        checkpoint=checkpoint,
        outcome_market_raw=outcome_market,
        evaluation_start=EVALUATION_START,
        outcome_open_not_before=MATURITY,
        turnover_cost_rate=0.001,
        outcome_source_sha256="d" * 64,
        economic_cash_returns=_economic_cash(),
        economic_cash_source_sha256="f" * 64,
    )
    verify_historical_aov_outcome(outcome)

    assert outcome.payload["outcome_authority"] == OUTCOME_AUTHORITY
    assert outcome.payload["canonical_engine"] == "core.engine.run_simulation"
    assert outcome.payload["financial_alpha_evidence"] == 0
    assert outcome.payload["required_arms"] == [
        "rule100",
        "parent",
        "child",
        "pit_equal_weight",
        "economic_cash",
    ]
    assert outcome.payload["parent_child_mutation_authority"] == "NONE"
    assert outcome.payload["prospective_clock_authority"] == "NONE"
    for arm, simulation in outcome.simulations.items():
        evaluation_date = pd.Timestamp("2025-07-01")
        assert simulation.loc[evaluation_date, "gross_ret"] == pytest.approx(0.0)
        assert simulation.loc[evaluation_date, "turnover"] == pytest.approx(0.0)
        first_execution = simulation.index[simulation["turnover"].gt(0.0)][0]
        assert first_execution == pd.Timestamp("2025-07-02")
        assert outcome.payload["arm_metrics"][arm]["first_attributed_return_date"] == "2025-07-02"


def test_outcome_bytes_change_outcome_identity_but_cannot_change_decision_identity() -> None:
    checkpoint, outcome_market = _checkpoint_and_outcome_frame()
    original_checkpoint_id = checkpoint.checkpoint_id
    first = evaluate_historical_aov_outcome(
        checkpoint=checkpoint,
        outcome_market_raw=outcome_market,
        evaluation_start=EVALUATION_START,
        outcome_open_not_before=MATURITY,
        turnover_cost_rate=0.001,
        outcome_source_sha256="d" * 64,
        economic_cash_returns=_economic_cash(),
        economic_cash_source_sha256="f" * 64,
    )
    mutated_market = outcome_market.copy()
    mutated_market.loc[mutated_market.index[0], "SPT_TOTAL_RETURN"] = 50.0
    second = evaluate_historical_aov_outcome(
        checkpoint=checkpoint,
        outcome_market_raw=mutated_market,
        evaluation_start=EVALUATION_START,
        outcome_open_not_before=MATURITY,
        turnover_cost_rate=0.001,
        outcome_source_sha256="e" * 64,
        economic_cash_returns=_economic_cash(),
        economic_cash_source_sha256="f" * 64,
    )
    assert checkpoint.checkpoint_id == original_checkpoint_id
    assert first.outcome_id != second.outcome_id


def test_historical_outcome_rejects_pre_target_or_wrong_maturity() -> None:
    checkpoint, outcome_market = _checkpoint_and_outcome_frame()
    contaminated = pd.concat(
        [outcome_market, _full_market().loc[lambda frame: pd.to_datetime(frame["SPT_DATE"]).eq(pd.Timestamp(TARGET_DATE))].head(1)],
        ignore_index=True,
    )
    with pytest.raises(ValueError, match="pre_or_target_market_forbidden"):
        evaluate_historical_aov_outcome(
            checkpoint=checkpoint,
            outcome_market_raw=contaminated,
            evaluation_start=EVALUATION_START,
            outcome_open_not_before=MATURITY,
            turnover_cost_rate=0.001,
            outcome_source_sha256="d" * 64,
            economic_cash_returns=_economic_cash(),
            economic_cash_source_sha256="f" * 64,
        )

    with pytest.raises(ValueError, match="maturity_contract_mismatch"):
        evaluate_historical_aov_outcome(
            checkpoint=checkpoint,
            outcome_market_raw=outcome_market,
            evaluation_start=EVALUATION_START,
            outcome_open_not_before="2025-08-01T20:00:00Z",
            turnover_cost_rate=0.001,
            outcome_source_sha256="d" * 64,
            economic_cash_returns=_economic_cash(),
            economic_cash_source_sha256="f" * 64,
        )


def test_historical_outcome_fails_closed_on_missing_executed_return() -> None:
    checkpoint, outcome_market = _checkpoint_and_outcome_frame()
    active = checkpoint.dag.parent.iloc[0]
    active_security = str(active[active.gt(0.0)].index[0])
    security_raw = active_security.split(":", 1)[1]
    mask = (
        outcome_market["SP_SECURITY_ID"].astype(str).eq(security_raw)
        & pd.to_datetime(outcome_market["SPT_DATE"]).eq(pd.Timestamp("2025-07-02"))
    )
    outcome_market = outcome_market.copy()
    outcome_market.loc[mask, "SPT_TOTAL_RETURN"] = np.nan
    with pytest.raises(RuntimeError, match="Missing .* return cells"):
        evaluate_historical_aov_outcome(
            checkpoint=checkpoint,
            outcome_market_raw=outcome_market,
            evaluation_start=EVALUATION_START,
            outcome_open_not_before=MATURITY,
            turnover_cost_rate=0.001,
            outcome_source_sha256="d" * 64,
            economic_cash_returns=_economic_cash(),
            economic_cash_source_sha256="f" * 64,
        )
