"""Unit tests for M7F1-v5.2-final formation-first + prior-20 tradability gate."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from scripts import pead_m7f1_v5_2019_crsp_vertical as m7


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
    # Poison earliest prior slots if requested
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
    # 40 sessions so entry has 20 priors
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
    # 5 bad + 15 good in prior window → still ok
    panel = _panel_with_prior(1, sessions, bad_prior_slots=5)
    kept, failed, stats = m7.apply_pre_q5_prior20_observability(
        events, sessions, {1: panel}
    )
    assert stats["pre_q5_prior20_ok"] == 1
    assert stats["pre_q5_prior20_fail"] == 0
    assert len(kept) == 1
    assert int(kept.iloc[0]["prior20_n_ok"]) == 15
    assert failed.empty


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
    assert failed.iloc[0]["pre_q5_gate_status"] == "prior20_lt_15"
    assert int(failed.iloc[0]["prior20_n_ok"]) == 14


def test_vol_zero_fails_observability() -> None:
    assert m7._session_observability_ok(0.01, 10.0, 0.0) is False
    assert m7._session_observability_ok(0.01, 10.0, 1.0) is True
    assert m7._session_observability_ok(0.01, 0.0, 1.0) is False
    assert m7._session_observability_ok(0.01, -5.0, 1.0) is True  # abs(PRC)>0
    assert m7._session_observability_ok("C", 10.0, 1.0) is False


def test_prior20_gate_does_not_inspect_entry_or_future_returns() -> None:
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
    panel = _panel_with_prior(1, sessions)
    # Corrupt entry day and all post-entry sessions
    panel = panel.copy()
    for i in range(20, 40):
        panel.loc[panel.index[i], "ret_raw"] = "C"
        panel.loc[panel.index[i], "prc_raw"] = 0.0
        panel.loc[panel.index[i], "vol_raw"] = 0.0
    kept, failed, stats = m7.apply_pre_q5_prior20_observability(
        events, sessions, {1: panel}
    )
    assert stats["pre_q5_prior20_ok"] == 1
    assert len(kept) == 1
    assert failed.empty


def test_panel_load_window_requires_20_pre_2019_sessions() -> None:
    sessions = pd.date_range("2018-11-01", periods=80, freq="B")
    start, end, meta = m7.panel_load_window(sessions)
    assert meta["n_pre_cohort_sessions_loaded"] == 20
    assert pd.Timestamp(start) < pd.Timestamp("2019-01-01")
    assert end == "2020-12-31"
    short = pd.date_range("2019-01-02", periods=30, freq="B")
    with pytest.raises(m7.M7F1BlockedError, match="source_spine_lacks_prior20"):
        m7.panel_load_window(short)


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
    assert stats["suppressed_entry_overlap"] == 1
    assert kept.iloc[0]["event_id"] == "early"
    assert suppressed.iloc[0]["event_id"] == "late"


def test_delist_cash_slot_retains_weight_not_reallocated() -> None:
    d0 = pd.Timestamp("2019-03-01")
    d1 = pd.Timestamp("2019-03-04")
    rows = [
        {
            "event_id": "e0",
            "permno": 1000,
            "rdq": d0 - pd.Timedelta(days=5),
            "entry": d0,
            "return_date": d0,
            "session_offset": 1,
            "r": 0.10,
            "live_equity": True,
            "cash_slot": False,
            "delist_day": False,
            "active_slot": True,
            "sue": 1.0,
        },
        {
            "event_id": "e1",
            "permno": 1001,
            "rdq": d0 - pd.Timedelta(days=5),
            "entry": d0,
            "return_date": d0,
            "session_offset": 1,
            "r": 0.00,
            "live_equity": True,
            "cash_slot": False,
            "delist_day": False,
            "active_slot": True,
            "sue": 1.0,
        },
        {
            "event_id": "e0",
            "permno": 1000,
            "rdq": d0 - pd.Timedelta(days=5),
            "entry": d0,
            "return_date": d1,
            "session_offset": 2,
            "r": 0.0,
            "live_equity": False,
            "cash_slot": True,
            "delist_day": False,
            "active_slot": True,
            "sue": 1.0,
        },
        {
            "event_id": "e1",
            "permno": 1001,
            "rdq": d0 - pd.Timedelta(days=5),
            "entry": d0,
            "return_date": d1,
            "session_offset": 2,
            "r": 0.20,
            "live_equity": True,
            "cash_slot": False,
            "delist_day": False,
            "active_slot": True,
            "sue": 1.0,
        },
    ]
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
    assert int(daily.iloc[1]["n_active_slots"]) == 10


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
    event = {
        "event_id": "g|2019-05-31|202",
        "gvkey": "g",
        "rdq": pd.Timestamp("2019-05-31"),
        "permno": permno,
        "sue": 2.0,
        "q5_rank": 3,
        "formation_n_distinct_permno": 55,
    }
    out = m7.resolve_event_window(event=event, sessions=sessions, panel_by_permno={permno: panel})
    assert out["status"] == "ok"
    assert out["q5_rank"] == 3
    r2 = out["rows"][2]
    assert r2["delist_day"] is True
    assert math.isclose(r2["r"], (1.01) * (0.7) - 1.0, rel_tol=1e-9)
    assert out["rows"][3]["cash_slot"] is True
    assert out["rows"][3]["r"] == 0.0


def test_invalid_window_preserves_q5_rank_and_failure_detail() -> None:
    sessions = pd.date_range("2019-06-03", periods=70, freq="B")
    permno = 404
    panel = pd.DataFrame(
        {
            "permno": permno,
            "date": sessions,
            "ret_raw": ["C"] * 70,
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
    assert out["q5_rank"] == 7
    assert out["formation_n_distinct_permno"] == 60
    assert out["failure_detail"] is not None
    assert "ret_raw" in out["failure_detail"]
    ledger = m7._ledger_row_from_resolved(out)
    assert ledger["q5_rank"] == 7
    assert ledger["failure_detail"] is not None


def test_stale_curve_invalidation(tmp_path: Path) -> None:
    path = tmp_path / "pead_m7f1_v5_2019_daily_returns.parquet"
    pd.DataFrame({"return_date": ["2019-01-02"], "daily_net_return": [0.01]}).to_parquet(
        path, index=False
    )
    assert path.is_file()
    out = m7._invalidate_stale_curve(path)
    assert out["invalidated"] is True
    assert out["prior_sha256"] is not None
    assert not path.is_file()
    out2 = m7._invalidate_stale_curve(path)
    assert out2["invalidated"] is False


def test_atomic_write_parquet(tmp_path: Path) -> None:
    path = tmp_path / "t.parquet"
    df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
    sha = m7._atomic_write_parquet(df, path)
    assert path.is_file()
    assert len(sha) == 64
    assert m7._sha256_file(path) == sha


def test_detached_head_requires_proof_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_git(repo_root: Path, *args: str) -> str:
        if args[:2] == ("rev-parse", "HEAD"):
            return "a" * 40
        if args[:2] == ("rev-parse", "HEAD^{tree}"):
            return "b" * 40
        raise m7.M7F1BlockedError("unexpected")

    monkeypatch.setattr(m7, "_git_cmd", fake_git)

    import subprocess as sp

    class R:
        def __init__(self, code: int, out: str = ""):
            self.returncode = code
            self.stdout = out
            self.stderr = ""

    def fake_run(*a, **k):
        return R(1, "")

    monkeypatch.setattr(sp, "run", fake_run)
    with pytest.raises(m7.M7F1BlockedError, match="detached_head_requires_explicit"):
        m7.resolve_run_identity(tmp_path, detached_proof_mode=False)


def test_cost_and_min_active_slots() -> None:
    d0 = pd.Timestamp("2019-03-01")
    d1 = pd.Timestamp("2019-03-04")
    rows = []
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
                "live_equity": True,
                "cash_slot": False,
                "delist_day": False,
                "active_slot": True,
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
                "live_equity": True,
                "cash_slot": False,
                "delist_day": False,
                "active_slot": True,
                "sue": float(i),
            }
        )
    daily, _ = m7.build_daily_portfolio(pd.DataFrame(rows))
    assert math.isclose(daily.iloc[0]["turnover_l1"], 1.0, rel_tol=1e-9)
    assert math.isclose(daily.iloc[0]["daily_cost"], 0.00075, rel_tol=1e-9)
    assert daily.iloc[1]["turnover_l1"] >= 2.0 - 1e-9


def test_link_model_and_version_constants() -> None:
    assert m7.LINK_MODEL == "cross_vintage_snapshot_cusip8_non_pit"
    assert m7.IMPLEMENTATION_VERSION == "m7f1-v5.2-final"
    assert "prior20_formation_tradability" in m7.ROADMAP_DEVIATION
    assert m7.MIN_PRIOR_OK == 15
    assert m7.PRIOR_SESSIONS == 20
