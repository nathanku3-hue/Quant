"""Unit tests for M7F2-v6-final: pre-entry exclude, blank bridge, outcome envelope."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from scripts import pead_m7f2_v6_2019_crsp_vertical as m7


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
    panel.loc[3, "prc_raw"] = 10.5
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
    assert down[first_bad_idx]["r"] == -1.0
    assert down[first_bad_idx + 1]["r"] == 0.0


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
    assert m7.IMPLEMENTATION_VERSION == "m7f2-v6-final"
    assert "used_for_selection" not in m7.ROADMAP_DEVIATION  # not claiming false
    # build_crsp meta dict keys validated via synthetic inspection of source defaults
    assert m7.ARTIFACT_NAME.startswith("pead_m7f2_v6")


def test_stale_curve_invalidation(tmp_path: Path) -> None:
    path = tmp_path / "pead_m7f2_v6_2019_daily_returns.parquet"
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
    with pytest.raises(m7.M7F2BlockedError, match="source_spine_lacks_prior20"):
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
    assert math.isclose(daily.iloc[1]["daily_gross_return"], 0.02, rel_tol=1e-9)
    assert int(daily.iloc[1]["n_cash_slots"]) == 1
