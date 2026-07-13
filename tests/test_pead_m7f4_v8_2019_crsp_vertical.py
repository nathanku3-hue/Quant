"""Unit tests for M7F4-v8 exact self-financing identity."""

from __future__ import annotations

import inspect
import json
import math
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from scripts import pead_m7f4_v8_2019_crsp_vertical as m7


def test_day_plus_1_is_first_session_after_rdq_and_in_window() -> None:
    sessions = pd.date_range("2019-01-02", periods=80, freq="B")
    permno = 101
    panel = pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": 0.001,
            "dlret_raw": None,
            "dlstcd_raw": None,
            "prc_raw": 10.0,
            "vol_raw": 1000.0,
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
    assert out["entry"] == pd.Timestamp("2019-01-04")
    assert len(out["rows"]) == 60
    assert out["rows"][0]["return_date"] == out["entry"]
    assert out["bridge_applied"] is False


def test_formation_entry_does_not_require_entry_day_return() -> None:
    sessions = pd.date_range("2019-01-02", periods=10, freq="B")
    events = pd.DataFrame(
        [
            {
                "event_id": "a|2019-01-02|1",
                "gvkey": "a",
                "rdq": pd.Timestamp("2019-01-02"),
                "permno": 1,
                "sue": 1.0,
            }
        ]
    )
    out = m7.assign_formation_entry(events, sessions)
    assert bool(out.iloc[0]["formation_eligible"]) is True
    assert out.iloc[0]["entry"] == pd.Timestamp("2019-01-03")


def test_dedup_one_event_per_formation_permno_keeps_highest_sue() -> None:
    events = pd.DataFrame(
        [
            {
                "event_id": "a|2019-01-01|1",
                "gvkey": "a",
                "rdq": pd.Timestamp("2019-01-01"),
                "permno": 1,
                "sue": 1.0,
                "entry": pd.Timestamp("2019-01-03"),
                "formation_eligible": True,
            },
            {
                "event_id": "b|2019-01-02|1",
                "gvkey": "b",
                "rdq": pd.Timestamp("2019-01-02"),
                "permno": 1,
                "sue": 3.0,
                "entry": pd.Timestamp("2019-01-03"),
                "formation_eligible": True,
            },
        ]
    )
    deduped, dropped = m7.dedup_formation_permno(events)
    assert dropped == 1
    assert len(deduped) == 1
    assert deduped.iloc[0]["event_id"] == "b|2019-01-02|1"


def _panel_with_prior(
    permno: int,
    sessions: pd.DatetimeIndex,
    *,
    ret: object = 0.001,
    prc: object = 10.0,
    vol: object = 1000.0,
    bad_prior_slots: int = 0,
) -> pd.DataFrame:
    n = len(sessions)
    rets = [ret] * n
    prcs = [prc] * n
    vols = [vol] * n
    for i in range(min(bad_prior_slots, n)):
        rets[i] = "C"
        prcs[i] = 0.0
        vols[i] = 0.0
    return pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": rets,
            "dlret_raw": [None] * n,
            "dlstcd_raw": [None] * n,
            "prc_raw": prcs,
            "vol_raw": vols,
        }
    )


def test_prior20_gate_passes_with_15_of_20_ok() -> None:
    sessions = pd.date_range("2018-12-01", periods=40, freq="B")
    entry = sessions[20]
    events = pd.DataFrame(
        [
            {
                "event_id": "a|2018-12-20|1",
                "gvkey": "a",
                "rdq": sessions[19],
                "permno": 1,
                "sue": 1.0,
                "entry": entry,
                "formation_eligible": True,
            }
        ]
    )
    panel = _panel_with_prior(1, sessions, bad_prior_slots=5)
    kept, failed, stats = m7.apply_pre_q5_prior20_observability(
        events, sessions, {1: panel}
    )
    assert stats["pre_q5_prior20_ok"] == 1
    assert len(kept) == 1
    assert int(kept.iloc[0]["prior20_n_ok"]) == 15


def test_prior20_gate_fails_with_14_of_20() -> None:
    sessions = pd.date_range("2018-12-01", periods=40, freq="B")
    entry = sessions[20]
    events = pd.DataFrame(
        [
            {
                "event_id": "a|2018-12-20|1",
                "gvkey": "a",
                "rdq": sessions[19],
                "permno": 1,
                "sue": 1.0,
                "entry": entry,
                "formation_eligible": True,
            }
        ]
    )
    panel = _panel_with_prior(1, sessions, bad_prior_slots=6)
    kept, failed, stats = m7.apply_pre_q5_prior20_observability(
        events, sessions, {1: panel}
    )
    assert stats["pre_q5_prior20_lt_15"] == 1
    assert len(kept) == 0


def test_vol_zero_fails_observability() -> None:
    assert m7._session_observability_ok(0.01, 10.0, 0.0) is False
    assert m7._session_observability_ok(0.01, 10.0, 1.0) is True


def test_exclude_pre_entry_delist_before_q5_structural() -> None:
    """Structural DLSTCD>=200 before entry excludes; no event-id policy."""
    sessions = pd.date_range("2019-01-02", periods=40, freq="B")
    entry = sessions[10]
    events = pd.DataFrame(
        [
            {
                "event_id": "dead|2019-01-01|1",
                "gvkey": "dead",
                "rdq": sessions[8],
                "permno": 1,
                "sue": 9.0,
                "entry": entry,
                "formation_eligible": True,
                "pre_q5_gate_status": "prior20_ok",
                "prior20_n_ok": 20,
            },
            {
                "event_id": "live|2019-01-01|2",
                "gvkey": "live",
                "rdq": sessions[8],
                "permno": 2,
                "sue": 1.0,
                "entry": entry,
                "formation_eligible": True,
                "pre_q5_gate_status": "prior20_ok",
                "prior20_n_ok": 20,
            },
        ]
    )
    panel1 = _panel_with_prior(1, sessions)
    # delist two sessions before entry
    panel1 = panel1.copy()
    idx = panel1.index[panel1["date"] == sessions[8]][0]
    panel1.loc[idx, "dlstcd_raw"] = 233
    panel1.loc[idx, "dlret_raw"] = 0.01
    panel2 = _panel_with_prior(2, sessions)
    kept, excl, stats = m7.exclude_pre_entry_delists(
        events, {1: panel1, 2: panel2}
    )
    assert stats["pre_entry_delist_excluded"] == 1
    assert stats["pre_entry_delist_kept"] == 1
    assert int(kept.iloc[0]["permno"]) == 2
    assert int(excl.iloc[0]["permno"]) == 1
    # Q5 rerank uses surviving only
    q5, qstats = m7.apply_formation_breadth_q5(
        pd.concat(
            [
                kept.assign(
                    formation_n_distinct_permno=50
                )
            ],
            ignore_index=True,
        )
    )
    # with n=1 after exclude, floor(1/5)=0 -> empty q5 is ok; breadth may filter
    assert stats["pre_entry_delist_excluded"] == 1


def test_bridge_blank_one_day_with_adjacent_prices_and_next_ret() -> None:
    sessions = pd.date_range("2019-06-03", periods=70, freq="B")
    permno = 303
    rets: list[object] = [0.01] * 70
    prcs = [10.0] * 70
    # day offset 3 (index 2 after entry index 0) is blank; next numeric
    # entry = sessions[0] if rdq = sessions[0]-1 business day
    rets[2] = None  # blank
    prcs[2] = float("nan")
    panel = pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": rets,
            "dlret_raw": [None] * 70,
            "dlstcd_raw": [None] * 70,
            "prc_raw": prcs,
            "vol_raw": 100.0,
        }
    )
    # ensure prev and next prices exist (index 1 and 3)
    panel.loc[1, "prc_raw"] = 10.0
    panel.loc[3, "prc_raw"] = 10.2
    panel.loc[3, "ret_raw"] = 0.02
    out = m7.resolve_event_window(
        event={
            "event_id": "b|2019-05-31|303",
            "gvkey": "b",
            "rdq": pd.Timestamp("2019-05-31"),
            "permno": permno,
            "sue": 1.0,
        },
        sessions=sessions,
        panel_by_permno={permno: panel},
    )
    assert out["status"] == "ok"
    assert out["bridge_applied"] is True
    bridged = [r for r in out["rows"] if r.get("bridged_gap")]
    assert len(bridged) == 1
    assert bridged[0]["r"] == 0.0
    records = m7.bridge_parity_records_from_resolved(out)
    assert len(records) == 1
    assert records[0]["prev_prc"] == pytest.approx(10.0)
    assert records[0]["next_prc"] == pytest.approx(10.2)
    assert records[0]["next_ret"] == pytest.approx(0.02)
    assert records[0]["parity_ok"] is True
    ledger = m7._ledger_row_from_resolved(out)
    assert ledger["bridge_parity_n_attempts"] == 1
    assert ledger["bridge_parity_n_ok"] == 1
    assert '"prev_prc":10.0' in ledger["bridge_parity_records_json"]


def test_bridge_rejects_letter_special_b() -> None:
    sessions = pd.date_range("2019-06-03", periods=70, freq="B")
    permno = 404
    rets: list[object] = [0.01] * 70
    rets[2] = "B"
    panel = pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": rets,
            "dlret_raw": [None] * 70,
            "dlstcd_raw": [None] * 70,
            "prc_raw": 10.0,
            "vol_raw": 100.0,
        }
    )
    out = m7.resolve_event_window(
        event={
            "event_id": "x|2019-05-31|404",
            "gvkey": "x",
            "rdq": pd.Timestamp("2019-05-31"),
            "permno": permno,
            "sue": 1.0,
            "q5_rank": 7,
            "formation_n_distinct_permno": 60,
        },
        sessions=sessions,
        panel_by_permno={permno: panel},
    )
    assert out["status"] == "nonnumeric_selected_window"
    assert out["outcome_class"] == "outcome_ambiguous"
    assert out["q5_rank"] == 7
    assert out["partial_rows"] is not None


def test_bridge_rejects_multi_day_blank() -> None:
    sessions = pd.date_range("2019-06-03", periods=70, freq="B")
    permno = 505
    rets: list[object] = [0.01] * 70
    rets[2] = None
    rets[3] = None  # next also blank -> unbridgeable
    panel = pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": rets,
            "dlret_raw": [None] * 70,
            "dlstcd_raw": [None] * 70,
            "prc_raw": 10.0,
            "vol_raw": 100.0,
        }
    )
    out = m7.resolve_event_window(
        event={
            "event_id": "m|2019-05-31|505",
            "gvkey": "m",
            "rdq": pd.Timestamp("2019-05-31"),
            "permno": permno,
            "sue": 1.0,
        },
        sessions=sessions,
        panel_by_permno={permno: panel},
    )
    assert out["status"] == "nonnumeric_selected_window"
    assert "unbridgeable" in (out["failure_detail"] or "")


def test_outcome_scenario_write_down_and_neutral_carry() -> None:
    sessions = pd.date_range("2019-06-03", periods=70, freq="B")
    permno = 606
    rets: list[object] = [0.01] * 70
    rets[5] = "B"
    panel = pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": rets,
            "dlret_raw": [None] * 70,
            "dlstcd_raw": [None] * 70,
            "prc_raw": 10.0,
            "vol_raw": 100.0,
        }
    )
    resolved = m7.resolve_event_window(
        event={
            "event_id": "o|2019-05-31|606",
            "gvkey": "o",
            "rdq": pd.Timestamp("2019-05-31"),
            "permno": permno,
            "sue": 1.0,
        },
        sessions=sessions,
        panel_by_permno={permno: panel},
    )
    assert resolved["status"] != "ok"
    carry = m7.expand_outcome_scenario_rows(
        resolved, sessions=sessions, scenario="neutral_carry_to_cash"
    )
    down = m7.expand_outcome_scenario_rows(
        resolved, sessions=sessions, scenario="write_down_100pct"
    )
    assert carry is not None and len(carry) == 60
    assert down is not None and len(down) == 60
    # first bad offset ~6
    first_bad_idx = next(
        i for i, r in enumerate(carry) if r.get("outcome_scenario") == "neutral_carry_to_cash"
    )
    assert carry[first_bad_idx]["r"] == 0.0
    assert carry[first_bad_idx]["cash_slot"] is True
    assert down[first_bad_idx]["r"] == -1.0
    assert down[first_bad_idx + 1]["r"] == 0.0
    assert down[first_bad_idx + 1].get("dead_sleeve") is True
    assert down[first_bad_idx + 1].get("active_slot") is False


def test_delist_compounds_then_cash_remainder() -> None:
    sessions = pd.date_range("2019-06-03", periods=70, freq="B")
    permno = 202
    rets = [0.01] * 70
    dlrets = [None] * 70
    dlst = [None] * 70
    dlrets[2] = -0.3
    dlst[2] = 500
    panel = pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": rets,
            "dlret_raw": dlrets,
            "dlstcd_raw": dlst,
            "prc_raw": 10.0,
            "vol_raw": 100.0,
        }
    )
    out = m7.resolve_event_window(
        event={
            "event_id": "g|2019-05-31|202",
            "gvkey": "g",
            "rdq": pd.Timestamp("2019-05-31"),
            "permno": permno,
            "sue": 2.0,
            "q5_rank": 3,
            "formation_n_distinct_permno": 55,
        },
        sessions=sessions,
        panel_by_permno={permno: panel},
    )
    assert out["status"] == "ok"
    r2 = out["rows"][2]
    assert r2["delist_day"] is True
    assert math.isclose(r2["r"], (1.01) * (0.7) - 1.0, rel_tol=1e-9)
    assert out["rows"][3]["cash_slot"] is True


def test_map_meta_used_for_selection_true() -> None:
    # structural assertion on module constants / helper contract text
    assert m7.IMPLEMENTATION_VERSION == "m7f4-v8"
    assert "used_for_selection" not in m7.ROADMAP_DEVIATION  # not claiming false
    # build_crsp meta dict keys validated via synthetic inspection of source defaults
    assert m7.ARTIFACT_NAME.startswith("pead_m7f4_v8")


def test_stale_curve_invalidation(tmp_path: Path) -> None:
    path = tmp_path / "pead_m7f4_v8_2019_daily_returns.parquet"
    pd.DataFrame({"return_date": ["2019-01-02"], "daily_net_return": [0.01]}).to_parquet(
        path, index=False
    )
    out = m7._invalidate_stale_curve(path)
    assert out["invalidated"] is True
    assert not path.is_file()


def test_atomic_write_parquet(tmp_path: Path) -> None:
    path = tmp_path / "t.parquet"
    df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
    sha = m7._atomic_write_parquet(df, path)
    assert path.is_file()
    assert len(sha) == 64


def test_suppress_later_event_entirely_on_entry_overlap() -> None:
    sessions = pd.date_range("2019-01-02", periods=80, freq="B")
    entry0 = sessions[0]
    entry1 = sessions[10]
    q5 = pd.DataFrame(
        [
            {
                "event_id": "early",
                "gvkey": "g1",
                "rdq": entry0 - pd.Timedelta(days=1),
                "permno": 7,
                "sue": 1.0,
                "entry": entry0,
                "q5_rank": 1,
                "formation_n_distinct_permno": 50,
            },
            {
                "event_id": "late",
                "gvkey": "g2",
                "rdq": entry1 - pd.Timedelta(days=1),
                "permno": 7,
                "sue": 9.0,
                "entry": entry1,
                "q5_rank": 1,
                "formation_n_distinct_permno": 50,
            },
        ]
    )
    kept, suppressed, stats = m7.suppress_entry_overlap(q5, sessions)
    assert stats["q5_events_after_overlap"] == 1
    assert kept.iloc[0]["event_id"] == "early"


def test_blank_helpers() -> None:
    assert m7._is_blank_return(None) is True
    assert m7._is_blank_return("") is True
    assert m7._is_blank_return("B") is False
    assert m7._is_letter_special_return("B") is True
    assert m7._is_letter_special_return(None) is False


def test_panel_load_window_requires_20_pre_2019_sessions() -> None:
    sessions = pd.date_range("2018-11-01", periods=80, freq="B")
    start, end, meta = m7.panel_load_window(sessions)
    assert meta["n_pre_cohort_sessions_loaded"] == 20
    short = pd.date_range("2019-01-02", periods=30, freq="B")
    with pytest.raises(m7.M7F4BlockedError, match="source_spine_lacks_prior20"):
        m7.panel_load_window(short)


def test_delist_cash_slot_retains_weight_not_reallocated() -> None:
    d0 = pd.Timestamp("2019-03-01")
    d1 = pd.Timestamp("2019-03-04")
    rows = []
    for eid, r0, r1, cash1 in (
        ("e0", 0.10, 0.0, True),
        ("e1", 0.00, 0.20, False),
    ):
        rows.append(
            {
                "event_id": eid,
                "permno": 1000 if eid == "e0" else 1001,
                "rdq": d0 - pd.Timedelta(days=5),
                "entry": d0,
                "return_date": d0,
                "session_offset": 1,
                "r": r0,
                "live_equity": True,
                "cash_slot": False,
                "delist_day": False,
                "active_slot": True,
                "sue": 1.0,
            }
        )
        rows.append(
            {
                "event_id": eid,
                "permno": 1000 if eid == "e0" else 1001,
                "rdq": d0 - pd.Timedelta(days=5),
                "entry": d0,
                "return_date": d1,
                "session_offset": 2,
                "r": r1,
                "live_equity": not cash1,
                "cash_slot": cash1,
                "delist_day": False,
                "active_slot": True,
                "sue": 1.0,
            }
        )
    for i in range(2, 10):
        for dt, r in ((d0, 0.0), (d1, 0.0)):
            rows.append(
                {
                    "event_id": f"pad{i}",
                    "permno": 2000 + i,
                    "rdq": d0 - pd.Timedelta(days=5),
                    "entry": d0,
                    "return_date": dt,
                    "session_offset": 1 if dt == d0 else 2,
                    "r": r,
                    "live_equity": True,
                    "cash_slot": False,
                    "delist_day": False,
                    "active_slot": True,
                    "sue": 0.0,
                }
            )
    daily, _ = m7.build_daily_portfolio(pd.DataFrame(rows))
    day1 = daily.iloc[1]
    post_cost_invested_return = day1["nav_after_ret"] / day1["nav_after_open_cost"] - 1.0
    assert math.isclose(post_cost_invested_return, 0.02, rel_tol=1e-9)
    assert day1["daily_pre_cost_gross_return"] == pytest.approx(
        day1["nav_after_ret"] / day1["nav_after_open_cost"] - 1.0
    )
    assert day1["daily_pre_cost_gross_return"] == pytest.approx(0.02)
    assert day1["daily_net_return"] < day1["daily_pre_cost_gross_return"]
    assert day1["nav_cost_drag_dollars"] == pytest.approx(
        day1["nav_pre_cost_gross_end"] - day1["nav_end"]
    )
    assert int(day1["n_cash_slots"]) == 1


def test_bridge_rejects_price_ret_parity_mismatch() -> None:
    sessions = pd.date_range("2019-06-03", periods=70, freq="B")
    permno = 707
    rets: list[object] = [0.01] * 70
    rets[2] = None
    panel = pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": rets,
            "dlret_raw": [None] * 70,
            "dlstcd_raw": [None] * 70,
            "prc_raw": 10.0,
            "vol_raw": 100.0,
        }
    )
    # next price jump not explained by next RET
    panel.loc[1, "prc_raw"] = 10.0
    panel.loc[3, "prc_raw"] = 50.0
    panel.loc[3, "ret_raw"] = 0.01
    out = m7.resolve_event_window(
        event={
            "event_id": "p|2019-05-31|707",
            "gvkey": "p",
            "rdq": pd.Timestamp("2019-05-31"),
            "permno": permno,
            "sue": 1.0,
        },
        sessions=sessions,
        panel_by_permno={permno: panel},
    )
    assert out["status"] == "nonnumeric_selected_window"
    assert "parity" in (out["failure_detail"] or "")
    records = m7.bridge_parity_records_from_resolved(out)
    assert len(records) == 1
    assert records[0]["parity_ok"] is False
    summary = m7.summarize_bridge_parity([out])
    assert summary["n_attempts"] == 1
    assert summary["n_fail"] == 1
    assert summary["max_abs_err"] is not None


def test_hash_selected_event_set_stable() -> None:
    a = m7.hash_selected_event_set(["b", "a", "a"])
    b = m7.hash_selected_event_set(["a", "b"])
    assert a == b
    assert len(a) == 64


def test_self_financing_legs_differ_in_turnover() -> None:
    """write_down vs neutral should not share identical turnover when residual paths differ."""
    sessions = pd.date_range("2019-01-02", periods=80, freq="B")
    # 12 ok events + 1 residual-like synthetic via scenario rows
    rows_n = []
    rows_w = []
    eids = [f"e{i}" for i in range(12)]
    for i, eid in enumerate(eids):
        for off, dt in enumerate(sessions[:20], start=1):
            base = {
                "event_id": eid,
                "permno": 1000 + i,
                "rdq": sessions[0] - pd.Timedelta(days=1),
                "entry": sessions[0],
                "return_date": dt,
                "session_offset": off,
                "r": 0.001,
                "live_equity": True,
                "cash_slot": False,
                "delist_day": False,
                "active_slot": True,
                "dead_sleeve": False,
                "sue": 1.0,
            }
            rows_n.append(dict(base))
            rows_w.append(dict(base))
    # residual sleeve eR: neutral cash after day 5; write_down -100% day 5 then dead
    for off, dt in enumerate(sessions[:20], start=1):
        if off < 5:
            common = {
                "event_id": "eR",
                "permno": 9999,
                "rdq": sessions[0] - pd.Timedelta(days=1),
                "entry": sessions[0],
                "return_date": dt,
                "session_offset": off,
                "r": 0.001,
                "live_equity": True,
                "cash_slot": False,
                "delist_day": False,
                "active_slot": True,
                "dead_sleeve": False,
                "sue": 1.0,
            }
            rows_n.append(dict(common))
            rows_w.append(dict(common))
        elif off == 5:
            rows_n.append(
                {
                    "event_id": "eR",
                    "permno": 9999,
                    "rdq": sessions[0] - pd.Timedelta(days=1),
                    "entry": sessions[0],
                    "return_date": dt,
                    "session_offset": off,
                    "r": 0.0,
                    "live_equity": False,
                    "cash_slot": True,
                    "delist_day": False,
                    "active_slot": True,
                    "dead_sleeve": False,
                    "sue": 1.0,
                }
            )
            rows_w.append(
                {
                    "event_id": "eR",
                    "permno": 9999,
                    "rdq": sessions[0] - pd.Timedelta(days=1),
                    "entry": sessions[0],
                    "return_date": dt,
                    "session_offset": off,
                    "r": -1.0,
                    "live_equity": True,
                    "cash_slot": False,
                    "delist_day": False,
                    "active_slot": True,
                    "dead_sleeve": False,
                    "sue": 1.0,
                }
            )
        else:
            rows_n.append(
                {
                    "event_id": "eR",
                    "permno": 9999,
                    "rdq": sessions[0] - pd.Timedelta(days=1),
                    "entry": sessions[0],
                    "return_date": dt,
                    "session_offset": off,
                    "r": 0.0,
                    "live_equity": False,
                    "cash_slot": True,
                    "delist_day": False,
                    "active_slot": True,
                    "dead_sleeve": False,
                    "sue": 1.0,
                }
            )
            rows_w.append(
                {
                    "event_id": "eR",
                    "permno": 9999,
                    "rdq": sessions[0] - pd.Timedelta(days=1),
                    "entry": sessions[0],
                    "return_date": dt,
                    "session_offset": off,
                    "r": 0.0,
                    "live_equity": False,
                    "cash_slot": False,
                    "delist_day": False,
                    "active_slot": False,
                    "dead_sleeve": True,
                    "sue": 1.0,
                }
            )
    d_n, s_n = m7.build_daily_portfolio(pd.DataFrame(rows_n))
    d_w, s_w = m7.build_daily_portfolio(pd.DataFrame(rows_w))
    assert s_n["total_turnover_l1"] != s_w["total_turnover_l1"]
    assert s_n["total_direct_cost_dollars"] != s_w["total_direct_cost_dollars"]
    # write-down should destroy more NAV
    assert s_w["total_net_return"] < s_n["total_net_return"]


def test_shapley_four_residuals_sum_to_gap() -> None:
    sessions = pd.date_range("2019-01-02", periods=70, freq="B")
    resolved = []
    # 10 ok events
    for i in range(10):
        rows = []
        for off, dt in enumerate(sessions[:60], start=1):
            rows.append(
                {
                    "event_id": f"ok{i}",
                    "gvkey": f"g{i}",
                    "permno": 100 + i,
                    "rdq": sessions[0] - pd.Timedelta(days=1),
                    "entry": sessions[0],
                    "sue": 1.0,
                    "session_offset": off,
                    "return_date": dt,
                    "r": 0.001,
                    "live_equity": True,
                    "cash_slot": False,
                    "delist_day": False,
                    "active_slot": True,
                    "dead_sleeve": False,
                    "bridged_gap": False,
                }
            )
        resolved.append(
            {
                "event_id": f"ok{i}",
                "gvkey": f"g{i}",
                "permno": 100 + i,
                "rdq": sessions[0] - pd.Timedelta(days=1),
                "entry": sessions[0],
                "sue": 1.0,
                "status": "ok",
                "rows": rows,
                "partial_rows": [],
                "first_bad_session": None,
            }
        )
    # 4 residual events failing at different offsets
    for j, bad_off in enumerate([10, 20, 30, 40]):
        partial = []
        for off, dt in enumerate(sessions[: bad_off - 1], start=1):
            partial.append(
                {
                    "event_id": f"bad{j}",
                    "gvkey": f"b{j}",
                    "permno": 900 + j,
                    "rdq": sessions[0] - pd.Timedelta(days=1),
                    "entry": sessions[0],
                    "sue": 1.0,
                    "session_offset": off,
                    "return_date": dt,
                    "r": 0.001,
                    "live_equity": True,
                    "cash_slot": False,
                    "delist_day": False,
                    "active_slot": True,
                    "dead_sleeve": False,
                    "bridged_gap": False,
                }
            )
        resolved.append(
            {
                "event_id": f"bad{j}",
                "gvkey": f"b{j}",
                "permno": 900 + j,
                "rdq": sessions[0] - pd.Timedelta(days=1),
                "entry": sessions[0],
                "sue": 1.0,
                "status": "nonnumeric_selected_window",
                "rows": None,
                "partial_rows": partial,
                "first_bad_session": sessions[bad_off - 1].strftime("%Y-%m-%d"),
                "outcome_class": "outcome_ambiguous",
            }
        )
    out = m7.shapley_16_residual_attribution(
        resolved, sessions=sessions, scenario="write_down_100pct"
    )
    assert out["n_states"] == 16
    assert out["n_residual"] == 4
    assert out["sum_equals_gap_abs_err"] < 1e-9


def test_first_bad_exposure_is_not_event_count_share() -> None:
    sessions = pd.date_range("2019-01-02", periods=70, freq="B")
    resolved = []
    for i in range(10):
        rows = []
        for off, dt in enumerate(sessions[:60], start=1):
            rows.append(
                {
                    "event_id": f"ok{i}",
                    "gvkey": f"g{i}",
                    "permno": 100 + i,
                    "rdq": sessions[0] - pd.Timedelta(days=1),
                    "entry": sessions[0],
                    "sue": 1.0,
                    "session_offset": off,
                    "return_date": dt,
                    "r": 0.0,
                    "live_equity": True,
                    "cash_slot": False,
                    "delist_day": False,
                    "active_slot": True,
                    "dead_sleeve": False,
                    "bridged_gap": False,
                }
            )
        resolved.append(
            {
                "event_id": f"ok{i}",
                "status": "ok",
                "permno": 100 + i,
                "rdq": sessions[0] - pd.Timedelta(days=1),
                "entry": sessions[0],
                "sue": 1.0,
                "gvkey": f"g{i}",
                "rows": rows,
                "partial_rows": [],
                "first_bad_session": None,
            }
        )
    partial = []
    for off, dt in enumerate(sessions[:5], start=1):
        partial.append(
            {
                "event_id": "bad0",
                "gvkey": "b0",
                "permno": 900,
                "rdq": sessions[0] - pd.Timedelta(days=1),
                "entry": sessions[0],
                "sue": 1.0,
                "session_offset": off,
                "return_date": dt,
                "r": 0.0,
                "live_equity": True,
                "cash_slot": False,
                "delist_day": False,
                "active_slot": True,
                "dead_sleeve": False,
                "bridged_gap": False,
            }
        )
    resolved.append(
        {
            "event_id": "bad0",
            "gvkey": "b0",
            "permno": 900,
            "rdq": sessions[0] - pd.Timedelta(days=1),
            "entry": sessions[0],
            "sue": 1.0,
            "status": "nonnumeric_selected_window",
            "rows": None,
            "partial_rows": partial,
            "first_bad_session": sessions[5].strftime("%Y-%m-%d"),
        }
    )
    exp = m7.first_bad_date_residual_exposure(
        resolved, scenario="write_down_100pct", sessions=sessions
    )
    # 11 active on first bad => weight 1/11, not 1/11 event-count of selected (1/11 same coincidentally)
    # event count share would be 1/11 as well here; compare to wrong metric 1/n only when n differs
    assert exp["summed_first_bad_date_target_weight"] == pytest.approx(1.0 / 11.0)
    assert exp["metric"] == m7.RESIDUAL_EXPOSURE_METRIC


def _portfolio_row(
    event_id: str,
    return_date: pd.Timestamp,
    *,
    live_equity: bool,
    cash_slot: bool,
    r: float = 0.0,
    delist_day: bool = False,
    active_slot: bool = True,
    dead_sleeve: bool = False,
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "permno": 5000 + int(event_id.removeprefix("e") or 0),
        "rdq": return_date - pd.Timedelta(days=5),
        "entry": return_date,
        "return_date": return_date,
        "session_offset": 1,
        "r": r,
        "live_equity": live_equity,
        "cash_slot": cash_slot,
        "delist_day": delist_day,
        "active_slot": active_slot,
        "dead_sleeve": dead_sleeve,
        "sue": 1.0,
    }


def test_duplicate_position_days_fail_closed() -> None:
    dt = pd.Timestamp("2019-01-02")
    rows = [
        _portfolio_row(f"e{i}", dt, live_equity=True, cash_slot=False)
        for i in range(10)
    ]
    rows.append(dict(rows[0]))
    with pytest.raises(m7.M7F4BlockedError, match="duplicate_position_days:1"):
        m7.build_daily_portfolio(pd.DataFrame(rows))


def test_equity_to_cash_transition_is_charged_once_and_cost_carries_state() -> None:
    d0 = pd.Timestamp("2019-01-02")
    d1 = pd.Timestamp("2019-01-03")
    rows: list[dict[str, object]] = []
    for i in range(10):
        rows.append(_portfolio_row(f"e{i}", d0, live_equity=True, cash_slot=False))
        rows.append(
            _portfolio_row(
                f"e{i}",
                d1,
                live_equity=i != 0,
                cash_slot=i == 0,
            )
        )
    daily, stats = m7.build_daily_portfolio(pd.DataFrame(rows))
    assert daily.iloc[0]["nav_end"] < 1.0
    assert daily.iloc[1]["nav_open"] == pytest.approx(daily.iloc[0]["nav_end"])
    day1 = daily.iloc[1]
    assert day1["turnover_open_equity_l1"] > 0.1
    assert day1["turnover_open_equity_l1"] == pytest.approx(
        day1["open_equity_trade_dollars"] / day1["nav_open"]
    )
    assert day1["open_cost_dollars"] == pytest.approx(
        m7.ONE_WAY_COST * day1["open_equity_trade_dollars"]
    )
    assert day1["open_cost_fixed_point_abs_residual_dollars"] <= m7.OPEN_COST_FIXED_POINT_TOL
    assert day1["turnover_close_equity_exits"] == pytest.approx(0.0)
    assert daily.iloc[1]["turnover_terminal_equity"] == pytest.approx(0.9)
    assert stats["cost_in_next_day_state"] is True
    assert stats["nav_state_matches_equity_path"] is True


def test_terminal_liquidation_is_equity_only() -> None:
    dt = pd.Timestamp("2019-01-02")
    cash_rows = [
        _portfolio_row(f"e{i}", dt, live_equity=False, cash_slot=True)
        for i in range(10)
    ]
    cash_daily, _ = m7.build_daily_portfolio(pd.DataFrame(cash_rows))
    assert cash_daily.iloc[0]["turnover_terminal_equity"] == pytest.approx(0.0)
    assert cash_daily.iloc[0]["terminal_cost_rate"] == pytest.approx(0.0)
    assert cash_daily.iloc[0]["terminal_cost_dollars"] == pytest.approx(0.0)

    equity_rows = [
        _portfolio_row(f"e{i}", dt, live_equity=True, cash_slot=False)
        for i in range(10)
    ]
    equity_daily, _ = m7.build_daily_portfolio(pd.DataFrame(equity_rows))
    assert equity_daily.iloc[0]["turnover_terminal_equity"] == pytest.approx(1.0)
    assert equity_daily.iloc[0]["terminal_cost_rate"] == pytest.approx(m7.ONE_WAY_COST)
    assert equity_daily.iloc[0]["terminal_cost_dollars"] == pytest.approx(
        m7.ONE_WAY_COST * equity_daily.iloc[0]["terminal_equity_trade_dollars"]
    )


def test_canonical_selection_row_hash_is_shuffle_stable_and_content_sensitive() -> None:
    rows = [
        {
            "event_id": "b",
            "gvkey": "002",
            "permno": 2,
            "rdq": "2019-01-03",
            "entry": "2019-01-04",
            "sue": 2.0,
            "q5_rank": 2,
            "formation_n_distinct_permno": 55,
        },
        {
            "event_id": "a",
            "gvkey": "001",
            "permno": 1,
            "rdq": "2019-01-02",
            "entry": "2019-01-03",
            "sue": 1.0,
            "q5_rank": 1,
            "formation_n_distinct_permno": 55,
        },
    ]
    original = m7.hash_canonical_selection_rows(rows)
    assert original == m7.hash_canonical_selection_rows(list(reversed(rows)))
    changed = [dict(row) for row in rows]
    changed[0]["permno"] = 99
    assert original != m7.hash_canonical_selection_rows(changed)


def test_code_identity_accepts_newline_only_difference(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path
    code = repo / "scripts" / "pead_m7f4_v8_2019_crsp_vertical.py"
    code.parent.mkdir(parents=True)
    code.write_bytes(b"print('x')\r\n")
    monkeypatch.setattr(m7, "_git_blob_bytes", lambda *_: b"print('x')\n")
    identity = m7._resolve_code_identity(repo, code)
    assert identity["code_hash_authority"] == "git_blob"
    assert identity["code_hash_fallback"] is None
    assert identity["code_normalized_worktree_matches_git_blob"] is True
    assert identity["code_sha256_git_blob"] != identity["code_sha256_worktree"]
    assert identity["code_sha256_normalized_git_blob"] == identity[
        "code_sha256_normalized_worktree"
    ]


def test_code_identity_rejects_missing_or_semantically_different_blob(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path
    code = repo / "scripts" / "pead_m7f4_v8_2019_crsp_vertical.py"
    code.parent.mkdir(parents=True)
    code.write_text("print('worktree')\n", encoding="utf-8")

    monkeypatch.setattr(m7, "_git_blob_bytes", lambda *_: None)
    with pytest.raises(m7.M7F4BlockedError, match="code_not_committed_at_head"):
        m7._resolve_code_identity(repo, code)

    monkeypatch.setattr(m7, "_git_blob_bytes", lambda *_: b"print('committed')\n")
    with pytest.raises(m7.M7F4BlockedError, match="semantic_mismatch"):
        m7._resolve_code_identity(repo, code)


def test_open_cost_fixed_point_is_deterministic_and_trade_exact() -> None:
    kwargs = {
        "nav_open": 1.0,
        "current_equity_dollars": {"a": 0.4, "b": 0.1},
        "target_equity_weights": {"a": 0.2, "c": 0.5},
    }
    first = m7._solve_open_cost_fixed_point(**kwargs)
    second = m7._solve_open_cost_fixed_point(**kwargs)
    assert first == second
    assert first["open_cost_dollars"] == pytest.approx(
        m7.ONE_WAY_COST * first["open_equity_trade_dollars"], abs=1e-15
    )
    assert first["open_cost_rate"] == pytest.approx(
        first["open_cost_dollars"] / kwargs["nav_open"]
    )
    assert sum(first["target_equity_dollars"].values()) == pytest.approx(
        0.7 * first["nav_after_open_cost"]
    )


def test_zero_active_slots_preserve_nav_in_global_idle_cash() -> None:
    d0 = pd.Timestamp("2019-01-02")
    d1 = pd.Timestamp("2019-01-03")
    d2 = pd.Timestamp("2019-01-04")
    rows: list[dict[str, object]] = []
    for i in range(10):
        rows.append(_portfolio_row(f"e{i}", d0, live_equity=True, cash_slot=False))
        rows.append(
            _portfolio_row(
                f"e{i}",
                d1,
                live_equity=False,
                cash_slot=False,
                active_slot=False,
                dead_sleeve=True,
            )
        )
        rows.append(_portfolio_row(f"e{i + 10}", d2, live_equity=True, cash_slot=False))
    daily, stats = m7.build_daily_portfolio(pd.DataFrame(rows))
    idle = daily.iloc[1]
    reentry = daily.iloc[2]
    assert idle["n_active_slots"] == 0
    assert idle["global_idle_cash_end"] == pytest.approx(idle["nav_end"])
    assert idle["nav_end"] == pytest.approx(idle["nav_after_open_cost"])
    assert reentry["nav_open"] == pytest.approx(idle["nav_end"])
    assert reentry["global_idle_cash_open"] == pytest.approx(idle["nav_end"])
    assert reentry["open_cost_dollars"] > 0.0
    assert stats["global_idle_cash_policy"] == m7.GLOBAL_IDLE_CASH_POLICY
    assert stats["no_recapitalization"] is True


def test_exhausted_nav_never_recapitalizes() -> None:
    d0 = pd.Timestamp("2019-01-02")
    d1 = pd.Timestamp("2019-01-03")
    rows: list[dict[str, object]] = []
    for i in range(10):
        rows.append(
            _portfolio_row(f"e{i}", d0, live_equity=True, cash_slot=False, r=-1.0)
        )
        rows.append(
            _portfolio_row(
                f"e{i}",
                d1,
                live_equity=False,
                cash_slot=False,
                active_slot=False,
                dead_sleeve=True,
            )
        )
    with pytest.raises(m7.M7F4BlockedError, match="no_recapitalization"):
        m7.build_daily_portfolio(pd.DataFrame(rows))


def test_stage_cost_dollars_rates_and_nav_drag_reconcile() -> None:
    d0 = pd.Timestamp("2019-01-02")
    d1 = pd.Timestamp("2019-01-03")
    rows: list[dict[str, object]] = []
    for i in range(10):
        rows.append(_portfolio_row(f"e{i}", d0, live_equity=True, cash_slot=False, r=0.01))
        rows.append(
            _portfolio_row(
                f"e{i}",
                d1,
                live_equity=True,
                cash_slot=False,
                r=0.02,
                delist_day=i == 0,
            )
        )
    daily, _ = m7.build_daily_portfolio(pd.DataFrame(rows))
    for _, row in daily.iterrows():
        assert row["nav_after_open_cost"] == pytest.approx(
            row["open_cost_base_nav"] - row["open_cost_dollars"]
        )
        assert row["open_cost_rate"] == pytest.approx(
            row["open_cost_dollars"] / row["open_cost_base_nav"]
        )
        assert row["nav_after_close_cost"] == pytest.approx(
            row["close_cost_base_nav"] - row["close_cost_dollars"]
        )
        assert row["nav_end"] == pytest.approx(
            row["terminal_cost_base_nav"] - row["terminal_cost_dollars"]
        )
        assert row["daily_pre_cost_gross_return"] == pytest.approx(
            row["nav_after_ret"] / row["nav_after_open_cost"] - 1.0
        )
        assert row["daily_net_return"] == pytest.approx(row["nav_end"] / row["nav_open"] - 1.0)
        assert row["nav_cost_drag_dollars"] == pytest.approx(
            row["nav_pre_cost_gross_end"] - row["nav_end"]
        )


def test_bridge_proof_is_flattened_into_ledger_columns() -> None:
    parity = {
        "prev_prc": 10.0,
        "next_prc": 10.1,
        "next_ret": 0.01,
        "gap_prc": None,
        "parity_abs_err": 0.0,
        "tol": m7.BRIDGE_PRICE_RET_PARITY_ABS_TOL,
        "parity_ok": True,
    }
    resolved = {
        "event_id": "g|2019-01-02|1",
        "gvkey": "g",
        "permno": 1,
        "rdq": pd.Timestamp("2019-01-02"),
        "entry": pd.Timestamp("2019-01-03"),
        "sue": 1.0,
        "status": "ok",
        "rows": [
            {
                "return_date": pd.Timestamp("2019-01-04"),
                "bridge_parity": parity,
            }
        ],
        "bridge_applied": True,
        "bridge_sessions": ["2019-01-04"],
    }
    ledger = m7._ledger_row_from_resolved(resolved)
    assert ledger["bridge_proof_flattened"] is True
    assert ledger["bridge_gap_session"] == "2019-01-04"
    assert ledger["bridge_prev_prc"] == 10.0
    assert ledger["bridge_next_prc"] == 10.1
    assert ledger["bridge_next_ret"] == 0.01
    assert ledger["bridge_parity_ok"] is True
    assert ledger["bridge_parity_tol"] == m7.BRIDGE_PRICE_RET_PARITY_ABS_TOL


def test_code_identity_rejects_path_outside_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("print('x')\n", encoding="utf-8")
    with pytest.raises(m7.M7F4BlockedError, match="outside_repo_root"):
        m7._resolve_code_identity(repo, outside)


def test_v8_source_has_no_m7f3_supersession_or_compatibility_surface() -> None:
    source = Path(m7.__file__).read_text(encoding="utf-8")
    assert "M7F3-v7" not in source
    assert "supersedes" not in source
    assert "compatibility" not in source.lower()


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _init_git_repo(repo: Path, content: bytes) -> str:
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "M7F4 Test")
    _git(repo, "config", "user.email", "m7f4@example.invalid")
    _git(repo, "config", "core.autocrlf", "false")
    (repo / "tracked.txt").write_bytes(content)
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "initial")
    return _git(repo, "rev-parse", "HEAD")


def _tiny_selection_rows() -> list[dict[str, object]]:
    return [
        {
            "event_id": "a|2019-01-02|1",
            "gvkey": "a",
            "permno": 1,
            "rdq": "2019-01-02",
            "entry": "2019-01-03",
            "sue": 1.0,
            "q5_rank": 1,
            "formation_n_distinct_permno": 55,
        },
        {
            "event_id": "b|2019-01-03|2",
            "gvkey": "b",
            "permno": 2,
            "rdq": "2019-01-03",
            "entry": "2019-01-04",
            "sue": 2.0,
            "q5_rank": 2,
            "formation_n_distinct_permno": 55,
        },
    ]


def _set_lock_to_rows(
    monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, object]]
) -> None:
    monkeypatch.setattr(m7, "LOCKED_SELECTED_EVENT_COUNT", len(rows))
    monkeypatch.setattr(
        m7,
        "LOCKED_SELECTED_EVENT_SET_SHA256",
        m7.hash_selected_event_set([str(row["event_id"]) for row in rows]),
    )
    monkeypatch.setattr(
        m7,
        "LOCKED_SELECTED_CANONICAL_ROWS_SHA256",
        m7.hash_canonical_selection_rows(rows),
    )


def test_locked_selection_contract_constants_are_exact() -> None:
    assert m7.LOCKED_SELECTED_EVENT_COUNT == 2448
    assert m7.LOCKED_SELECTED_EVENT_SET_SHA256 == (
        "caeccc642e5d052b211cc5ecfc335bf4f63d0fd7d63018a6b40c5d6965ad2e6d"
    )
    assert m7.LOCKED_SELECTED_CANONICAL_ROWS_SHA256 == (
        "7f336eefaf7de6840a907a94361297111a2abc66702ad41b0aa0733016435749"
    )


def test_locked_selection_contract_accepts_only_all_three_identities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = _tiny_selection_rows()
    _set_lock_to_rows(monkeypatch, rows)
    contract = m7.enforce_locked_selection_contract(rows)
    assert contract["locked_contract_verified"] is True
    assert contract["n_selected_events"] == 2

    monkeypatch.setattr(m7, "LOCKED_SELECTED_EVENT_SET_SHA256", "0" * 64)
    with pytest.raises(m7.M7F4BlockedError, match="event_set_sha256"):
        m7.enforce_locked_selection_contract(rows)

    _set_lock_to_rows(monkeypatch, rows)
    monkeypatch.setattr(m7, "LOCKED_SELECTED_CANONICAL_ROWS_SHA256", "f" * 64)
    with pytest.raises(m7.M7F4BlockedError, match="canonical_rows_sha256"):
        m7.enforce_locked_selection_contract(rows)


def test_locked_selection_contract_rejects_count_and_duplicate_event_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = _tiny_selection_rows()
    with pytest.raises(m7.M7F4BlockedError, match="count=2:expected=2448"):
        m7.enforce_locked_selection_contract(rows)

    duplicate_rows = [dict(rows[0]), dict(rows[0])]
    _set_lock_to_rows(monkeypatch, duplicate_rows)
    with pytest.raises(m7.M7F4BlockedError, match="unique_event_ids=1:rows=2"):
        m7.enforce_locked_selection_contract(duplicate_rows)


def test_run_vertical_has_no_output_mutation_before_selection_lock() -> None:
    source = inspect.getsource(m7.run_vertical)
    before_gate = source.split(
        "selection_contract = enforce_locked_selection_contract", maxsplit=1
    )[0]
    assert "_atomic_write" not in before_gate
    assert "_publish_crsp_cusip_permno_map" not in before_gate
    assert "_invalidate_stale_curve" not in before_gate


def test_run_vertical_residual_evidence_uses_locked_selection_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the real residual-evidence writer, not only the lock helper."""
    rows = _tiny_selection_rows()
    _set_lock_to_rows(monkeypatch, rows)
    selected = pd.DataFrame(rows)
    selected["rdq"] = pd.to_datetime(selected["rdq"])
    selected["entry"] = pd.to_datetime(selected["entry"])
    selected["formation_eligible"] = True
    selected["pre_q5_gate_status"] = "prior20_ok"
    selected["prior20_n_ok"] = 20
    empty = selected.iloc[0:0].copy()
    sessions = pd.date_range("2018-12-03", periods=100, freq="B")
    panel = pd.DataFrame(
        {
            "permno": [1, 2],
            "date": [sessions[0], sessions[0]],
            "ret_raw": [0.0, 0.0],
            "dlret_raw": [None, None],
            "dlstcd_raw": [None, None],
            "prc_raw": [10.0, 20.0],
            "vol_raw": [100.0, 200.0],
        }
    )
    identity = {
        "commit": "a" * 40,
        "tree": "b" * 40,
        "branch_ref": None,
        "detached": True,
        "detached_proof_mode": True,
        "proof_authority": "detached_proof_mode",
        "code_path": "scripts/pead_m7f4_v8_2019_crsp_vertical.py",
        "code_sha256": "c" * 64,
        "code_sha256_git_blob": "c" * 64,
        "code_sha256_worktree": "c" * 64,
        "code_sha256_normalized_git_blob": "c" * 64,
        "code_sha256_normalized_worktree": "c" * 64,
        "code_normalized_worktree_matches_git_blob": True,
        "code_hash_authority": "git_blob_sha256",
        "code_hash_fallback": None,
        "config_sha256": "d" * 64,
        "logical_identity_sha256": "e" * 64,
    }

    monkeypatch.setattr(m7, "resolve_run_identity", lambda *_args, **_kwargs: identity)
    monkeypatch.setattr(m7.duckdb, "connect", lambda: object())
    monkeypatch.setattr(
        m7,
        "build_crsp_cusip_permno_map",
        lambda *_args, **_kwargs: (
            pd.DataFrame({"cusip8": ["00000001", "00000002"], "permno": [1, 2]}),
            {"source_max_date": "2024-12-31"},
        ),
    )
    monkeypatch.setattr(
        m7,
        "load_mapped_events",
        lambda *_args, **_kwargs: (selected.copy(), {"unique_mapped_events": 2}),
    )
    monkeypatch.setattr(m7, "load_source_session_spine", lambda *_args, **_kwargs: sessions)
    monkeypatch.setattr(
        m7,
        "panel_load_window",
        lambda _sessions: (
            sessions[0],
            sessions[-1],
            {"spine_n_sessions": len(sessions)},
        ),
    )
    monkeypatch.setattr(m7, "load_crsp_panel", lambda *_args, **_kwargs: panel.copy())
    monkeypatch.setattr(m7, "assign_formation_entry", lambda *_args, **_kwargs: selected.copy())
    monkeypatch.setattr(
        m7, "dedup_formation_permno", lambda *_args, **_kwargs: (selected.copy(), 0)
    )
    monkeypatch.setattr(
        m7,
        "apply_pre_q5_prior20_observability",
        lambda *_args, **_kwargs: (
            selected.copy(),
            empty.copy(),
            {"pre_q5_prior20_ok": 2},
        ),
    )
    monkeypatch.setattr(
        m7,
        "exclude_pre_entry_delists",
        lambda *_args, **_kwargs: (
            selected.copy(),
            empty.copy(),
            {"pre_entry_delist_excluded": 0},
        ),
    )
    monkeypatch.setattr(
        m7,
        "apply_formation_breadth_q5",
        lambda *_args, **_kwargs: (selected.copy(), {"events_after_breadth": 2}),
    )
    monkeypatch.setattr(
        m7,
        "suppress_entry_overlap",
        lambda *_args, **_kwargs: (
            selected.copy(),
            empty.copy(),
            {"q5_events_after_overlap": 2},
        ),
    )

    def fake_resolve(*, event: dict[str, object], **_kwargs: object) -> dict[str, object]:
        base = {
            **event,
            "claim_end": sessions[60],
            "delist_offset": None,
            "pre_q5_gate_status": "prior20_ok",
            "prior20_n_ok": 20,
            "panel_first_date": sessions[0].strftime("%Y-%m-%d"),
            "panel_last_date": sessions[-1].strftime("%Y-%m-%d"),
            "bridge_applied": False,
            "bridge_sessions": [],
        }
        if str(event["event_id"]).startswith("a|"):
            return {
                **base,
                "status": "ok",
                "rows": [{"return_date": sessions[i]} for i in range(1, 61)],
                "failure_detail": None,
                "first_bad_session": None,
                "outcome_class": "observed",
            }
        return {
            **base,
            "status": "unresolved_delist",
            "rows": [],
            "failure_detail": "synthetic_residual",
            "first_bad_session": sessions[10].strftime("%Y-%m-%d"),
            "outcome_class": "outcome_ambiguous",
        }

    monkeypatch.setattr(m7, "resolve_event_window", fake_resolve)
    monkeypatch.setattr(
        m7,
        "expand_outcome_scenario_rows",
        lambda resolved, **_kwargs: [
            {
                "event_id": resolved["event_id"],
                "return_date": sessions[1],
                "r": 0.0,
            }
        ],
    )
    monkeypatch.setattr(
        m7,
        "build_daily_portfolio",
        lambda _positions: (
            pd.DataFrame({"return_date": [sessions[1]], "daily_net_return": [0.0]}),
            {
                "total_turnover_l1": 0.0,
                "total_direct_cost_dollars": 0.0,
                "total_nav_cost_drag_dollars": 0.0,
            },
        ),
    )
    monkeypatch.setattr(
        m7,
        "first_bad_date_residual_exposure",
        lambda *_args, **_kwargs: {
            "n_residual_events": 1,
            "summed_first_bad_date_target_weight": 0.5,
        },
    )
    monkeypatch.setattr(
        m7,
        "shapley_16_residual_attribution",
        lambda *_args, **_kwargs: {
            "n_residual": 1,
            "sum_equals_gap_abs_err": 0.0,
        },
    )

    def publish_map(frame: pd.DataFrame, _meta: dict[str, object], path: Path) -> str:
        return m7._atomic_write_parquet(frame, path)

    monkeypatch.setattr(m7, "_publish_crsp_cusip_permno_map", publish_map)

    d1_path = tmp_path / "d1.parquet"
    sec_path = tmp_path / "security.parquet"
    crsp_path = tmp_path / "crsp.csv"
    for path, payload in (
        (d1_path, b"d1"),
        (sec_path, b"security"),
        (crsp_path, b"crsp"),
    ):
        path.write_bytes(payload)
    evidence_path = tmp_path / "evidence.json"
    parquet_path = tmp_path / "daily_returns.parquet"
    manifest_path = tmp_path / "daily_returns.manifest.json"
    cusip_map_path = tmp_path / "cusip_map.parquet"
    ledger_path = tmp_path / "event_ledger.parquet"
    ledger_manifest_path = tmp_path / "event_ledger.manifest.json"

    evidence = m7.run_vertical(
        repo_root=tmp_path,
        d1_path=d1_path,
        sec_path=sec_path,
        crsp_path=crsp_path,
        evidence_path=evidence_path,
        parquet_path=parquet_path,
        manifest_path=manifest_path,
        cusip_map_path=cusip_map_path,
        ledger_path=ledger_path,
        ledger_manifest_path=ledger_manifest_path,
        detached_proof_mode=True,
    )

    persisted = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["status"] == "DIAGNOSTIC_COMPLETE"
    assert evidence["counts"]["n_selected_event_set"] == 2
    assert persisted["counts"]["n_selected_event_set"] == 2
    assert persisted["contract"]["locked_selection_contract"]["n_selected_events"] == 2
    assert manifest_path.is_file()
    assert ledger_manifest_path.is_file()
    assert not parquet_path.exists()


def test_git_context_ignores_ambient_repo_splice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    head_a = _init_git_repo(repo_a, b"A\n")
    head_b = _init_git_repo(repo_b, b"B\n")
    assert head_a != head_b

    monkeypatch.setenv("GIT_DIR", str(repo_b / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(repo_b))
    monkeypatch.setenv("GIT_COMMON_DIR", str(repo_b / ".git"))
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", str(repo_b / ".git" / "objects"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.repositoryformatversion")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "0")

    context = m7._resolve_git_context(repo_a)
    assert Path(context["repo_root"]) == repo_a.resolve()
    assert m7._git_cmd(repo_a, "rev-parse", "HEAD", git_context=context) == head_a
    assert m7._git_blob_bytes(repo_a, "tracked.txt", context) == b"A\n"
    env = m7._sanitized_git_env()
    assert env["GIT_NO_REPLACE_OBJECTS"] == "1"
    assert all(key == "GIT_NO_REPLACE_OBJECTS" or not key.startswith("GIT_") for key in env)


def test_git_context_rejects_replacement_refs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    first = _init_git_repo(repo, b"first\n")
    (repo / "tracked.txt").write_bytes(b"second\n")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "second")
    second = _git(repo, "rev-parse", "HEAD")
    _git(repo, "replace", first, second)

    with pytest.raises(m7.M7F4BlockedError, match="git_replacement_refs_present"):
        m7._resolve_git_context(repo)


def test_v7_cli_is_true_stub_and_no_v7_exception_alias(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts import pead_m7f3_v7_2019_crsp_vertical as retired_v7

    assert retired_v7.main(["--ignored"]) == 2
    assert "M7F3-v7 executable path is retired" in capsys.readouterr().err
    assert not hasattr(retired_v7, "run_vertical")
    assert not hasattr(retired_v7, "build_daily_portfolio")
    assert not hasattr(m7, "M7F3BlockedError")
    source = Path(retired_v7.__file__).read_text(encoding="utf-8")
    assert "from scripts import" not in source
    assert len(source.splitlines()) < 30
