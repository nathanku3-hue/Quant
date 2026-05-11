from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from strategies.scanner import build_price_technicals
from strategies.scanner import calculate_price_technical
from strategies.scanner import calculate_leverage
from strategies.scanner import calculate_macro_score
from strategies.scanner import calculate_sovereign_entry_price
from strategies.scanner import calculate_support_distance
from strategies.scanner import calculate_tactics
from strategies.scanner import classify_breadth_status
from strategies.scanner import classify_cluster
from strategies.scanner import enrich_scan_frame
from strategies.scanner import generate_proxy_signal
from strategies.scanner import generate_rating


def _macro_close_frame(days: int = 250) -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=days, freq="B")
    return pd.DataFrame(
        {
            "^TNX": np.full(days, 4.0),
            "VWEHX": np.full(days, 100.0),
            "VFISX": np.full(days, 100.0),
        },
        index=idx,
    )


def _ohlc(days: int = 60) -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=days, freq="B")
    close = pd.Series(np.linspace(100.0, 130.0, days), index=idx)
    return pd.DataFrame(
        {
            "Close": close,
            "High": close + 1.5,
            "Low": close - 1.0,
            "Open": close - 0.25,
        },
        index=idx,
    )


def test_macro_score_rewards_falling_rates_and_strong_credit() -> None:
    frame = _macro_close_frame()
    frame.loc[frame.index[-1], "VWEHX"] = 110.0

    score = calculate_macro_score(frame)

    assert score == {"score": 100, "rate_score": 50, "credit_score": 50}


def test_macro_score_handles_short_input_as_unknown() -> None:
    assert calculate_macro_score(_macro_close_frame(days=40)) is None


def test_macro_score_fails_closed_on_invalid_credit_denominator() -> None:
    frame = _macro_close_frame()
    frame["VFISX"] = 0.0

    assert calculate_macro_score(frame) is None


@pytest.mark.parametrize("bad_value", [0.0, np.nan, np.inf])
def test_macro_score_fails_closed_on_latest_invalid_credit_denominator(bad_value: float) -> None:
    frame = _macro_close_frame()
    frame.loc[frame.index[-1], "VFISX"] = bad_value

    assert calculate_macro_score(frame) is None


def test_macro_score_locks_rate_and_credit_threshold_edges() -> None:
    frame = _macro_close_frame()
    frame.loc[frame.index[-63], "^TNX"] = 4.0
    frame.loc[frame.index[-1], "^TNX"] = 4.5
    frame.loc[frame.index[-1], "VWEHX"] = 110.0

    assert calculate_macro_score(frame) == {"score": 50, "rate_score": 0, "credit_score": 50}

    frame = _macro_close_frame()
    frame.loc[frame.index[-1], "VWEHX"] = 80.0

    assert calculate_macro_score(frame) == {"score": 50, "rate_score": 50, "credit_score": 0}


@pytest.mark.parametrize(
    ("spy", "rsp", "expected_label", "expected_color"),
    [
        (np.linspace(100.0, 110.0, 60), np.linspace(90.0, 105.0, 60), "HEALTHY (Broad)", "#00FFAA"),
        (np.linspace(100.0, 112.0, 60), np.linspace(110.0, 95.0, 60), "DIVERGENCE (Thinning)", "#FFD700"),
        (np.linspace(110.0, 95.0, 60), np.linspace(105.0, 90.0, 60), "WEAK (Correction)", "#ff4444"),
    ],
)
def test_breadth_status_thresholds(
    spy: np.ndarray,
    rsp: np.ndarray,
    expected_label: str,
    expected_color: str,
) -> None:
    idx = pd.date_range("2025-01-01", periods=60, freq="B")
    frame = pd.DataFrame({"SPY": spy, "RSP": rsp}, index=idx)

    assert classify_breadth_status(frame) == (expected_label, expected_color)


def test_breadth_status_fails_closed_on_nonfinite_recent_inputs() -> None:
    idx = pd.date_range("2025-01-01", periods=60, freq="B")
    frame = pd.DataFrame(
        {
            "SPY": np.linspace(100.0, 112.0, 60),
            "RSP": np.linspace(90.0, 105.0, 60),
        },
        index=idx,
    )
    frame.loc[idx[-1], "RSP"] = np.nan

    assert classify_breadth_status(frame) == ("UNKNOWN (No Data)", "#888")


def test_build_price_technicals_extracts_multi_ticker_history() -> None:
    hist = pd.concat({"AAA": _ohlc(), "BBB": _ohlc() * 2.0}, axis=1).swaplevel(axis=1)

    result = build_price_technicals(hist, ["AAA", "BBB"])

    assert result["AAA"]["price"] == pytest.approx(130.0)
    assert result["BBB"]["price"] == pytest.approx(260.0)
    assert result["AAA"]["atr"] > 0.0
    assert result["AAA"]["convexity"] > 0.0


def test_price_technical_invalid_history_returns_safe_defaults() -> None:
    result = calculate_price_technical(pd.DataFrame())

    assert result == {
        "price": 0.0,
        "ema21": 0.0,
        "sma50": 0.0,
        "sma200": 0.0,
        "atr": 0.0,
        "convexity": 1.0,
    }


@pytest.mark.parametrize(
    ("price", "atr", "cluster"),
    [(100.0, 2.0, "I. Heavy"), (100.0, 3.0, "II. Sprinter"), (100.0, 5.0, "III. Scout"), (0.0, 1.0, "Unknown")],
)
def test_cluster_classification(price: float, atr: float, cluster: str) -> None:
    assert classify_cluster(price, atr) == cluster


def test_sovereign_entry_price_applies_god_mode_premium_and_scout_flush() -> None:
    row = {
        "Current_Price": 100.0,
        "EMA21": 95.0,
        "SMA50": 90.0,
        "SMA200": 75.0,
        "Score": 95.0,
        "Convexity": 1.2,
        "Cluster_Type": "III. Scout",
    }

    entry, label, max_flush, premium, base_support = calculate_sovereign_entry_price(row, macro_score=85)

    assert entry == pytest.approx(95.0 * 0.89)
    assert label == "21-EMA (God Mode)"
    assert max_flush == pytest.approx(0.16)
    assert premium == pytest.approx(0.05)
    assert base_support == pytest.approx(95.0)


@pytest.mark.parametrize(
    ("score", "expected_premium", "expected_entry"),
    [(89.0, 0.00, 90.0 * 0.95), (90.0, 0.03, 90.0 * 0.98), (95.0, 0.05, 90.0)],
)
def test_sovereign_entry_price_locks_quality_premium_edges(
    score: float,
    expected_premium: float,
    expected_entry: float,
) -> None:
    row = {
        "Current_Price": 100.0,
        "EMA21": 95.0,
        "SMA50": 90.0,
        "SMA200": 75.0,
        "Score": score,
        "Convexity": 2.0,
        "Cluster_Type": "I. Heavy",
    }

    entry, _label, max_flush, premium, _base_support = calculate_sovereign_entry_price(row, macro_score=85)

    assert entry == pytest.approx(expected_entry)
    assert max_flush == pytest.approx(0.05)
    assert premium == pytest.approx(expected_premium)


def test_support_distance_and_tactics_parabolic_macro_risk() -> None:
    row = {
        "Current_Price": 120.0,
        "Entry_Price": 100.0,
        "ATR": 2.0,
        "Score": 95.0,
        "Convexity": 1.8,
        "Cluster_Type": "I. Heavy",
    }
    row["Tech_Support_Dist"] = calculate_support_distance(row)

    stop, warning, cluster, multiplier = calculate_tactics(row, macro_risk=True)

    assert row["Tech_Support_Dist"] == pytest.approx(20.0)
    assert "PARABOLIC MANIA" in warning
    assert stop == pytest.approx(120.0 - (multiplier * 2.0))
    assert cluster == "I. Heavy"
    assert 1.5 <= multiplier < 2.5


def test_proxy_signal_and_rating_allow_coiled_strong_buy() -> None:
    proxy_db = {
        "Compute": {"type": "Sector Only", "conf": "p=82%", "name": "TSMC", "span": "YoY", "key": "tsmc"},
        "Software": {"type": "None", "conf": "NA", "name": "[NO PROXY]", "span": "", "key": None},
    }
    row = {"Sector": "Compute", "Score": 100.0, "Tech_Support_Dist": 3.0}
    proxy_type, p_value, content, signal = generate_proxy_signal(
        row,
        proxy_data={"tsmc": {"val": 0.08, "span": "YoY"}},
        proxy_db=proxy_db,
    )

    rating = generate_rating(
        {
            "Action": "BUY",
            "Score": 100.0,
            "Tech_Support_Dist": 3.0,
            "Support_Price": 95.0,
            "Support_Label": "50-SMA (Standard)",
            "Proxy_Type": proxy_type,
            "Tactical_Warning": "",
            "Proxy_Signal": signal,
        }
    )

    assert proxy_type == "Sector Only"
    assert p_value == "p=82%"
    assert content == "TSMC (YoY): +8.0%"
    assert signal == "COILED SPRING"
    assert rating == "ENTER: STRONG BUY (Coiled)"


def test_rating_exit_precedence_and_leverage_gate() -> None:
    assert generate_rating({"Action": "KILL", "Score": 100}) == "EXIT (Macro/Sector Rot)"
    assert generate_rating({"Action": "BUY", "Score": 100, "Proxy_Type": "[NO PROXY]"}) == "WATCH (Miss Proxy Cap)"
    assert calculate_leverage({"Rating": "ENTER: STRONG BUY (Coiled)", "Convexity": 1.2}, 85) == "LEAPs"
    assert calculate_leverage({"Rating": "ENTER: STRONG BUY (Coiled)", "Convexity": 1.2}, 79) == "Avoid"
    assert calculate_leverage({"Rating": "ENTER: STRONG BUY (Coiled)", "Convexity": 1.8}, 85) == "Avoid"
    assert calculate_leverage({"Rating": "WATCH / HOLD", "Convexity": 1.0}, 85) == ""


def test_enrich_scan_frame_adds_scanner_outputs(sample_ticker_map: dict[int, str]) -> None:
    df_scan = pd.DataFrame(
        [
            {"Ticker": sample_ticker_map[101], "Score": 100.0, "Action": "BUY"},
            {"Ticker": sample_ticker_map[202], "Score": 80.0, "Action": "KILL"},
        ]
    )
    technicals = {
        "AAA": {"price": 97.0, "ema21": 95.0, "sma50": 90.0, "sma200": 80.0, "atr": 2.0, "convexity": 1.0},
        "BBB": {"price": 50.0, "ema21": 48.0, "sma50": 47.0, "sma200": 45.0, "atr": 3.0, "convexity": 1.2},
    }
    proxy_db = {
        "Compute": {"type": "Sector Only", "conf": "p=82%", "name": "TSMC", "span": "YoY", "key": "tsmc"},
        "Software": {"type": "None", "conf": "NA", "name": "[NO PROXY]", "span": "", "key": None},
    }

    enriched = enrich_scan_frame(
        df_scan,
        technicals=technicals,
        sector_map={"AAA": "Compute", "BBB": "Software"},
        proxy_db=proxy_db,
        proxy_data={"tsmc": {"val": 0.08, "span": "YoY"}},
        macro={"score": 85},
    )

    assert {"Entry_Price", "Stop_Loss", "Target_Price", "Proxy_Signal", "Rating", "Leverage"}.issubset(enriched.columns)
    assert enriched.loc[0, "Proxy_Signal"] == "COILED SPRING"
    assert enriched.loc[0, "Rating"] == "ENTER: STRONG BUY (Coiled)"
    assert enriched.loc[0, "Leverage"] == "LEAPs"
    assert enriched.loc[1, "Rating"] == "EXIT (Macro/Sector Rot)"
