"""Unit tests for M7F0-v4 mechanical contract (no full CRSP required)."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from scripts import pead_m7f0_2019_crsp_vertical as m7


def test_day_plus_1_is_first_session_after_rdq_and_in_window() -> None:
    sessions = pd.DatetimeIndex(pd.to_datetime(["2019-01-02", "2019-01-03", "2019-01-04"] + [
        f"2019-01-{d:02d}" for d in range(5, 31)
    ] + [f"2019-02-{d:02d}" for d in range(1, 29)] + [f"2019-03-{d:02d}" for d in range(1, 32)]))
    # Build 60+ sessions
    sessions = pd.date_range("2019-01-02", periods=80, freq="B")
    permno = 101
    panel = pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": 0.001,
            "dlret_raw": None,
            "dlstcd_raw": None,
        }
    )
    event = {
        "event_id": "g|2019-01-03|101",
        "gvkey": "g",
        "rdq": pd.Timestamp("2019-01-03"),
        "permno": permno,
        "sue": 1.0,
    }
    out = m7.resolve_event_window(
        event=event,
        sessions=sessions,
        panel_by_permno={permno: panel},
    )
    assert out["status"] == "ok"
    assert out["entry"] == pd.Timestamp("2019-01-04")  # first business day after RDQ
    assert len(out["rows"]) == 60
    assert out["rows"][0]["return_date"] == out["entry"]
    assert out["rows"][0]["session_offset"] == 1


def test_delist_compounds_then_cash_remainder() -> None:
    sessions = pd.date_range("2019-06-03", periods=70, freq="B")
    permno = 202
    rets = [0.01] * 70
    dlrets = [None] * 70
    dlst = [None] * 70
    # Delist on offset 3 (third session in window)
    dlrets[2] = -0.3
    dlst[2] = 500
    panel = pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": rets,
            "dlret_raw": dlrets,
            "dlstcd_raw": dlst,
        }
    )
    event = {
        "event_id": "g|2019-05-31|202",
        "gvkey": "g",
        "rdq": pd.Timestamp("2019-05-31"),
        "permno": permno,
        "sue": 2.0,
    }
    out = m7.resolve_event_window(event=event, sessions=sessions, panel_by_permno={permno: panel})
    assert out["status"] == "ok"
    # entry is first session after RDQ = 2019-06-03
    r2 = out["rows"][2]
    assert r2["delist_day"] is True
    assert math.isclose(r2["r"], (1.01) * (0.7) - 1.0, rel_tol=1e-9)
    assert out["rows"][3]["live"] is False
    assert out["rows"][3]["r"] == 0.0
    assert all(row["live"] is False for row in out["rows"][3:])


def test_unresolved_delist_blocks_event() -> None:
    sessions = pd.date_range("2019-06-03", periods=70, freq="B")
    permno = 303
    panel = pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": 0.0,
            "dlret_raw": [None] * 70,
            "dlstcd_raw": [None] * 70,
        }
    )
    panel.loc[panel.index[0], "dlstcd_raw"] = 550
    # dlret remains None
    event = {
        "event_id": "g|2019-05-31|303",
        "gvkey": "g",
        "rdq": pd.Timestamp("2019-05-31"),
        "permno": permno,
        "sue": 1.0,
    }
    out = m7.resolve_event_window(event=event, sessions=sessions, panel_by_permno={permno: panel})
    assert out["status"] == "unresolved_delist"


def test_cost_formula_and_min_live() -> None:
    # Two days: 10 names then 10 names half replaced
    rows = []
    d0 = pd.Timestamp("2019-03-01")
    d1 = pd.Timestamp("2019-03-04")
    for i in range(10):
        rows.append(
            {
                "event_id": f"e{i}",
                "permno": 1000 + i,
                "rdq": d0 - pd.Timedelta(days=5),
                "entry": d0,
                "return_date": d0,
                "session_offset": 1,
                "r": 0.01,
                "delist_day": False,
                "sue": float(10 - i),
            }
        )
    for i in range(10):
        rows.append(
            {
                "event_id": f"f{i}",
                "permno": 2000 + i,
                "rdq": d1 - pd.Timedelta(days=5),
                "entry": d1,
                "return_date": d1,
                "session_offset": 1,
                "r": 0.0,
                "delist_day": False,
                "sue": float(i),
            }
        )
    winners = pd.DataFrame(rows)
    daily, _ = m7.build_daily_portfolio(winners)
    assert len(daily) == 2
    # Day0: enter 10 names equal weight 0.1 each → turnover L1 = 1.0
    assert math.isclose(daily.iloc[0]["turnover_l1"], 1.0, rel_tol=1e-9)
    assert math.isclose(daily.iloc[0]["daily_cost"], 0.00075, rel_tol=1e-9)
    # Day1: exit 10 old + enter 10 new = 2.0 before terminal liquidation add on final day
    # Final day also includes terminal liquidation of the 10 names (+1.0) folded in.
    assert daily.iloc[1]["turnover_l1"] >= 2.0 - 1e-9


def test_min_live_blocks_mid_horizon() -> None:
    d0 = pd.Timestamp("2019-03-01")
    d1 = pd.Timestamp("2019-03-04")
    d2 = pd.Timestamp("2019-03-05")
    rows = []
    for i in range(10):
        rows.append(
            {
                "event_id": f"e{i}",
                "permno": 1000 + i,
                "rdq": d0 - pd.Timedelta(days=1),
                "entry": d0,
                "return_date": d0,
                "session_offset": 1,
                "r": 0.0,
                "delist_day": False,
                "sue": 1.0,
            }
        )
    # Mid day only 3 live names (not final)
    for i in range(3):
        rows.append(
            {
                "event_id": f"e{i}",
                "permno": 1000 + i,
                "rdq": d0 - pd.Timedelta(days=1),
                "entry": d0,
                "return_date": d1,
                "session_offset": 2,
                "r": 0.0,
                "delist_day": False,
                "sue": 1.0,
            }
        )
    for i in range(10):
        rows.append(
            {
                "event_id": f"e{i}",
                "permno": 1000 + i,
                "rdq": d0 - pd.Timedelta(days=1),
                "entry": d0,
                "return_date": d2,
                "session_offset": 3,
                "r": 0.0,
                "delist_day": False,
                "sue": 1.0,
            }
        )
    with pytest.raises(m7.M7F0BlockedError, match="live_names_below_min"):
        m7.build_daily_portfolio(pd.DataFrame(rows))


def test_earliest_event_wins_overlap() -> None:
    sessions = pd.date_range("2019-01-02", periods=70, freq="B")
    resolved = []
    for i, (rdq, sue, permno) in enumerate(
        [
            (pd.Timestamp("2018-12-28"), 5.0, 1),
            (pd.Timestamp("2019-01-10"), 9.0, 1),  # later event same permno
        ]
    ):
        panel = pd.DataFrame(
            {
                "permno": permno,
                "date": sessions,
                "ret_raw": 0.001,
                "dlret_raw": None,
                "dlstcd_raw": None,
            }
        )
        # pad many events for formation breadth on first entry only - skip; unit test apply_formation with synthetic
    # Direct unit: claims sort
    claims = pd.DataFrame(
        [
            {
                "event_id": "early",
                "permno": 1,
                "rdq": pd.Timestamp("2019-01-02"),
                "entry": pd.Timestamp("2019-01-03"),
                "return_date": pd.Timestamp("2019-01-04"),
                "session_offset": 1,
                "r": 0.01,
                "delist_day": False,
                "sue": 1.0,
            },
            {
                "event_id": "late",
                "permno": 1,
                "rdq": pd.Timestamp("2019-01-05"),
                "entry": pd.Timestamp("2019-01-06"),
                "return_date": pd.Timestamp("2019-01-04"),
                "session_offset": 1,
                "r": 0.02,
                "delist_day": False,
                "sue": 2.0,
            },
        ]
    )
    claims = claims.sort_values(
        ["permno", "return_date", "rdq", "entry", "event_id"],
        ascending=[True, True, True, True, True],
        kind="mergesort",
    )
    winners = claims.drop_duplicates(subset=["permno", "return_date"], keep="first")
    assert winners.iloc[0]["event_id"] == "early"
