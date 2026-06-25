"""Regression tests for pinned strategy universe behavior.

Validates:
- Manifest loads and resolves all thesis tickers to permnos
- Loader raises on missing/broken manifest (fail-closed)
- PIT replay default tickers include all pinned tickers
- Shared eligibility function matches expected gate logic
- diagnose_pinned_exclusions reports concrete reasons
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml


# ── Manifest Loading ──────────────────────────────────────────────────────


def test_pinned_manifest_loads_all_thesis_tickers() -> None:
    from data.universe.loader import load_pinned_manifest

    entries = load_pinned_manifest()
    tickers = [e["ticker"] for e in entries]
    assert "MU" in tickers
    assert "SNDK" in tickers
    assert "WDC" in tickers
    assert len(tickers) >= 10


def test_pinned_manifest_resolves_permnos() -> None:
    from data.universe.loader import resolve_pinned_universe

    resolved = resolve_pinned_universe()
    ok_tickers = [p.ticker for p in resolved if p.status == "OK"]
    assert "MU" in ok_tickers
    assert "WDC" in ok_tickers
    assert "SNDK" in ok_tickers


def test_pinned_loader_raises_on_missing_manifest(tmp_path: Path) -> None:
    from data.universe.loader import load_pinned_manifest

    with pytest.raises(FileNotFoundError):
        load_pinned_manifest(tmp_path / "nonexistent.yml")


def test_pinned_loader_raises_on_empty_manifest(tmp_path: Path) -> None:
    from data.universe.loader import load_pinned_manifest

    empty = tmp_path / "empty.yml"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError):
        load_pinned_manifest(empty)


def test_pinned_get_permnos_returns_ints() -> None:
    from data.universe.loader import get_pinned_permnos

    permnos = get_pinned_permnos()
    assert len(permnos) >= 10
    assert all(isinstance(p, int) for p in permnos)


# ── PIT Replay Default Tickers ───────────────────────────────────────────


def test_replay_default_tickers_include_pinned() -> None:
    from scripts.pit_lifecycle_replay import _default_replay_tickers

    defaults = _default_replay_tickers()
    for ticker in ["MU", "SNDK", "WDC", "AMAT", "LRCX"]:
        assert ticker in defaults, f"Pinned ticker {ticker} missing from replay defaults"


def test_replay_default_tickers_include_scanner() -> None:
    from scripts.pit_lifecycle_replay import SCANNER_TICKERS, _default_replay_tickers

    defaults = _default_replay_tickers()
    for ticker in SCANNER_TICKERS:
        assert ticker in defaults


# ── Shared Eligibility Function ──────────────────────────────────────────


def test_eligibility_enter_when_all_gates_pass() -> None:
    from scripts.pit_lifecycle_replay import is_pit_eligible

    assert is_pit_eligible(z_demand=0.5, capital_cycle_score=0.1, dist_sma20=0.03, trend_veto=False)


def test_eligibility_reject_negative_demand() -> None:
    from scripts.pit_lifecycle_replay import is_pit_eligible

    assert not is_pit_eligible(z_demand=-0.1, capital_cycle_score=0.1, dist_sma20=0.03, trend_veto=False)


def test_eligibility_reject_negative_cycle() -> None:
    from scripts.pit_lifecycle_replay import is_pit_eligible

    assert not is_pit_eligible(z_demand=0.5, capital_cycle_score=-0.1, dist_sma20=0.03, trend_veto=False)


def test_eligibility_reject_stretched() -> None:
    from scripts.pit_lifecycle_replay import is_pit_eligible

    assert not is_pit_eligible(z_demand=0.5, capital_cycle_score=0.1, dist_sma20=0.08, trend_veto=False)


def test_eligibility_reject_trend_veto() -> None:
    from scripts.pit_lifecycle_replay import is_pit_eligible

    assert not is_pit_eligible(z_demand=0.5, capital_cycle_score=0.1, dist_sma20=0.03, trend_veto=True)


def test_parabolic_zone_is_trim_not_exit() -> None:
    from scripts.pit_lifecycle_replay import is_pit_exit, is_pit_trim

    assert not is_pit_exit(dist_sma20=0.15, trend_veto=False)
    assert is_pit_trim(dist_sma20=0.15)


def test_hard_stop_is_exit() -> None:
    from scripts.pit_lifecycle_replay import is_pit_exit

    assert is_pit_exit(dist_sma20=0.21, trend_veto=False)


def test_exit_on_trend_veto() -> None:
    from scripts.pit_lifecycle_replay import is_pit_exit

    assert is_pit_exit(dist_sma20=0.03, trend_veto=True)


def test_no_exit_when_normal() -> None:
    from scripts.pit_lifecycle_replay import is_pit_exit

    assert not is_pit_exit(dist_sma20=0.08, trend_veto=False)


def test_replay_entry_weight_uses_max_positions_not_universe_size() -> None:
    from scripts.pit_lifecycle_replay import replay_entry_weight, rule100_target_weight, build_rule100_state

    assert replay_entry_weight() == pytest.approx(0.10)
    assert replay_entry_weight(max_positions=20) == pytest.approx(0.05)
    three_factor_state = build_rule100_state(
        pd.Series(
            {
                "z_demand": 0.4,
                "z_moat": 0.2,
                "z_inventory_quality_proxy": 0.1,
                "z_discipline_cond": -0.3,
            }
        )
    )
    four_factor_state = build_rule100_state(
        pd.Series(
            {
                "z_demand": 0.4,
                "z_moat": 0.2,
                "z_inventory_quality_proxy": 0.1,
                "z_discipline_cond": 0.3,
            }
        )
    )
    assert rule100_target_weight(three_factor_state) == pytest.approx(0.10)
    assert rule100_target_weight(four_factor_state) == pytest.approx(0.125)


def test_rule100_state_exposes_proxy_provenance() -> None:
    from scripts.pit_lifecycle_replay import build_rule100_state

    state = build_rule100_state(
        pd.Series(
            {
                "z_demand": 0.4,
                "z_moat": 0.2,
                "z_inventory_quality_proxy": 0.1,
                "z_discipline_cond": -0.3,
            }
        )
    )

    assert state.to_record()["rule100_provenance"] == {
        "demand": "z_demand",
        "supply": "z_inventory_quality_proxy",
        "pricing": "z_moat",
        "margin": "z_discipline_cond",
    }
    assert state.confirmed
    assert state.hold_intact


def test_lifecycle_factor_confirmation_requires_three_positive_vectors() -> None:
    from scripts.pit_lifecycle_replay import lifecycle_factor_confirmation

    confirmed, coverage, positives = lifecycle_factor_confirmation(
        pd.Series(
            {
                "z_demand": 0.4,
                "z_moat": 0.2,
                "z_inventory_quality_proxy": 0.1,
                "z_discipline_cond": -0.3,
            }
        )
    )
    assert confirmed
    assert coverage == 4
    assert positives == 3

    rejected, coverage, positives = lifecycle_factor_confirmation(
        pd.Series(
            {
                "z_demand": 0.4,
                "z_moat": None,
                "z_inventory_quality_proxy": 0.1,
                "z_discipline_cond": -0.3,
            }
        )
    )
    assert not rejected
    assert coverage == 3
    assert positives == 2


def test_exit_guard_requires_hard_exit_or_confirmed_trend_veto() -> None:
    from scripts.pit_lifecycle_replay import MIN_HOLD_DAYS, should_emit_exit

    assert not should_emit_exit(
        entry_date="2026-01-01",
        dt="2026-01-02",
        dist_sma20=0.13,
        trend_veto=False,
        exit_streak=2,
    )
    assert not should_emit_exit(
        entry_date="2026-01-01",
        dt=pd.Timestamp("2026-01-01") + pd.Timedelta(days=MIN_HOLD_DAYS),
        dist_sma20=0.13,
        trend_veto=False,
        exit_streak=2,
    )
    assert not should_emit_exit(
        entry_date="2026-01-01",
        dt=pd.Timestamp("2026-01-01") + pd.Timedelta(days=MIN_HOLD_DAYS),
        dist_sma20=0.13,
        trend_veto=False,
        exit_streak=1,
    )
    assert should_emit_exit(
        entry_date="2026-01-01",
        dt=pd.Timestamp("2026-01-01") + pd.Timedelta(days=MIN_HOLD_DAYS),
        dist_sma20=0.03,
        trend_veto=True,
        exit_streak=2,
    )


def test_drop_in_exit_guard_allows_hard_stretch_override() -> None:
    from scripts.pit_lifecycle_replay import should_emit_exit

    assert should_emit_exit(
        entry_date="2026-01-01",
        dt="2026-01-02",
        dist_sma20=0.21,
        trend_veto=False,
        exit_streak=1,
    )


def test_reentry_cooldown_blocks_until_expiry() -> None:
    from scripts.pit_lifecycle_replay import is_reentry_blocked

    cooldown_until = pd.Timestamp("2026-01-11")
    assert is_reentry_blocked(pd.Timestamp("2026-01-10"), cooldown_until)
    assert not is_reentry_blocked(pd.Timestamp("2026-01-11"), cooldown_until)


# ── Diagnostics ──────────────────────────────────────────────────────────


def test_diagnose_pinned_exclusions_returns_all_pinned() -> None:
    from scripts.pit_lifecycle_replay import diagnose_pinned_exclusions

    diag = diagnose_pinned_exclusions()
    assert not diag.empty
    assert "MU" in diag["ticker"].values
    assert "SNDK" in diag["ticker"].values
    assert "WDC" in diag["ticker"].values


def test_diagnose_reports_data_blocked_or_ok_or_failed_gate() -> None:
    from scripts.pit_lifecycle_replay import diagnose_pinned_exclusions

    diag = diagnose_pinned_exclusions()
    valid_statuses = {"OK", "DATA_BLOCKED", "FAILED_GATE"}
    assert set(diag["status"].unique()).issubset(valid_statuses)


def test_diagnose_no_silent_exclusions() -> None:
    """Every pinned ticker must appear in diagnostics — none silently dropped."""
    from data.universe.loader import get_pinned_tickers
    from scripts.pit_lifecycle_replay import diagnose_pinned_exclusions

    pinned = get_pinned_tickers()
    diag = diagnose_pinned_exclusions()
    diagnosed_tickers = set(diag["ticker"].values)
    for ticker in pinned:
        assert ticker in diagnosed_tickers, f"Pinned ticker {ticker} silently excluded from diagnostics"


def test_trace_thesis_ticker_eligibility_answers_mu_sndk_gates(tmp_path: Path) -> None:
    from scripts.pit_lifecycle_replay import trace_thesis_ticker_eligibility

    manifest = tmp_path / "pinned.yml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "supercycle_thesis": [
                    {"ticker": "MU", "start": "2025-01-02", "source": "fixture"},
                    {"ticker": "SNDK", "start": "2025-01-02", "source": "fixture"},
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    tickers = pd.DataFrame({"permno": [101, 202], "ticker": ["MU", "SNDK"]})
    universe = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-02", "2026-01-02", "2026-01-03", "2026-01-03"]),
            "permno": [101, 202, 101, 202],
            "ticker": ["MU", "SNDK", "MU", "SNDK"],
        }
    )
    prices = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-02", "2026-01-02", "2026-01-03", "2026-01-03"]),
            "permno": [101, 202, 101, 202],
            "ticker": ["MU", "SNDK", "MU", "SNDK"],
            "tri": [10.0, 20.0, 11.0, 21.0],
            "total_ret": [0.0, 0.0, 0.1, 0.05],
        }
    )
    features = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-02", "2026-01-02", "2026-01-03", "2026-01-03"]),
            "permno": [101, 202, 101, 202],
            "ticker": ["MU", "SNDK", "MU", "SNDK"],
            "adj_close": [10.0, 20.0, 11.0, 21.0],
            "dist_sma20": [0.01, 0.01, 0.08, 0.01],
            "trend_veto": [False, False, False, False],
            "z_demand": [0.4, -0.2, 0.5, -0.1],
            "capital_cycle_score": [0.3, 0.2, 0.4, 0.2],
            "z_moat": [0.2, 0.1, 0.2, 0.1],
            "z_inventory_quality_proxy": [0.2, 0.1, 0.2, 0.1],
            "z_discipline_cond": [0.2, -0.1, 0.2, -0.1],
        }
    )
    history = pd.DataFrame(
        {
            "date": ["2026-01-02"],
            "ticker": ["MU"],
            "permno": [101],
            "sizing_eligible": [True],
            "eligibility_reason": ["eligible_buy_or_hold"],
        }
    )
    decisions = pd.DataFrame(
        {
            "date": ["2026-01-03", "2026-01-03"],
            "ticker": ["MU", "SNDK"],
            "position_state_after": ["FLAT", "FLAT"],
        }
    )

    tickers_path = tmp_path / "tickers.parquet"
    universe_path = tmp_path / "universe.parquet"
    prices_path = tmp_path / "prices.parquet"
    features_path = tmp_path / "features.parquet"
    history_path = tmp_path / "history.csv"
    decisions_path = tmp_path / "decisions.jsonl"
    tickers.to_parquet(tickers_path, index=False)
    universe.to_parquet(universe_path, index=False)
    prices.to_parquet(prices_path, index=False)
    features.to_parquet(features_path, index=False)
    history.to_csv(history_path, index=False)
    decisions.to_json(decisions_path, orient="records", lines=True)

    trace = trace_thesis_ticker_eligibility(
        ("MU", "SNDK"),
        start_date="2026-01-02",
        end_date="2026-01-03",
        replay_dates=["2026-01-02", "2026-01-03"],
        manifest_path=manifest,
        tickers_path=tickers_path,
        universe_path=universe_path,
        prices_path=prices_path,
        features_path=features_path,
        rule100_history_path=history_path,
        decision_log_path=decisions_path,
    ).set_index("ticker")

    assert bool(trace.loc["MU", "pinned_thesis_universe"]) is True
    assert int(trace.loc["MU", "permno"]) == 101
    assert trace.loc["MU", "ticker_map_status"] == "OK"
    assert bool(trace.loc["MU", "latest_pit_member"]) is True
    assert bool(trace.loc["MU", "latest_local_price_return"]) is True
    assert int(trace.loc["MU", "rule100_history_dates"]) == 1
    assert trace.loc["MU", "latest_exclusion_gate"] == "technical quality"

    assert bool(trace.loc["SNDK", "pinned_thesis_universe"]) is True
    assert int(trace.loc["SNDK", "permno"]) == 202
    assert bool(trace.loc["SNDK", "latest_pit_member"]) is True
    assert bool(trace.loc["SNDK", "latest_local_price_return"]) is True
    assert int(trace.loc["SNDK", "rule100_history_dates"]) == 0
    assert trace.loc["SNDK", "latest_exclusion_gate"] == "factor threshold"


def test_trace_thesis_ticker_eligibility_reports_pit_membership_gate(tmp_path: Path) -> None:
    from scripts.pit_lifecycle_replay import trace_thesis_ticker_eligibility

    manifest = tmp_path / "pinned.yml"
    manifest.write_text(
        yaml.safe_dump({"supercycle_thesis": [{"ticker": "SNDK", "start": "2025-01-02", "source": "fixture"}]}),
        encoding="utf-8",
    )
    tickers_path = tmp_path / "tickers.parquet"
    universe_path = tmp_path / "universe.parquet"
    prices_path = tmp_path / "prices.parquet"
    features_path = tmp_path / "features.parquet"
    pd.DataFrame({"permno": [202], "ticker": ["SNDK"]}).to_parquet(tickers_path, index=False)
    pd.DataFrame({"date": pd.to_datetime(["2026-01-02"]), "permno": [202], "ticker": ["SNDK"]}).to_parquet(universe_path, index=False)
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-02", "2026-01-03"]),
            "permno": [202, 202],
            "ticker": ["SNDK", "SNDK"],
            "tri": [20.0, 21.0],
            "total_ret": [0.0, 0.05],
        }
    ).to_parquet(prices_path, index=False)
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-03"]),
            "permno": [202],
            "ticker": ["SNDK"],
            "dist_sma20": [0.01],
            "trend_veto": [False],
            "z_demand": [0.5],
            "capital_cycle_score": [0.2],
            "z_moat": [0.1],
            "z_inventory_quality_proxy": [0.1],
            "z_discipline_cond": [0.1],
        }
    ).to_parquet(features_path, index=False)

    trace = trace_thesis_ticker_eligibility(
        ("SNDK",),
        start_date="2026-01-02",
        end_date="2026-01-03",
        replay_dates=["2026-01-03"],
        manifest_path=manifest,
        tickers_path=tickers_path,
        universe_path=universe_path,
        prices_path=prices_path,
        features_path=features_path,
        rule100_history_path=tmp_path / "missing_history.csv",
        decision_log_path=tmp_path / "missing_decisions.jsonl",
    )

    assert bool(trace.loc[0, "latest_pit_member"]) is False
    assert trace.loc[0, "latest_exclusion_gate"] == "PIT membership"


def test_trace_thesis_ticker_eligibility_rejects_non_finite_return_rows(tmp_path: Path) -> None:
    from scripts.pit_lifecycle_replay import trace_thesis_ticker_eligibility

    manifest = tmp_path / "pinned.yml"
    manifest.write_text(
        yaml.safe_dump({"supercycle_thesis": [{"ticker": "MU", "start": "2025-01-02", "source": "fixture"}]}),
        encoding="utf-8",
    )
    tickers_path = tmp_path / "tickers.parquet"
    universe_path = tmp_path / "universe.parquet"
    prices_path = tmp_path / "prices.parquet"
    features_path = tmp_path / "features.parquet"
    pd.DataFrame({"permno": [101], "ticker": ["MU"]}).to_parquet(tickers_path, index=False)
    pd.DataFrame({"date": pd.to_datetime(["2026-01-03"]), "permno": [101], "ticker": ["MU"]}).to_parquet(universe_path, index=False)
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-03"]),
            "permno": [101],
            "ticker": ["MU"],
            "tri": [11.0],
            "total_ret": [float("inf")],
        }
    ).to_parquet(prices_path, index=False)
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-03"]),
            "permno": [101],
            "ticker": ["MU"],
            "dist_sma20": [0.01],
            "trend_veto": [False],
            "z_demand": [0.5],
            "capital_cycle_score": [0.2],
            "z_moat": [0.1],
            "z_inventory_quality_proxy": [0.1],
            "z_discipline_cond": [0.1],
        }
    ).to_parquet(features_path, index=False)

    trace = trace_thesis_ticker_eligibility(
        ("MU",),
        start_date="2026-01-03",
        end_date="2026-01-03",
        replay_dates=["2026-01-03"],
        manifest_path=manifest,
        tickers_path=tickers_path,
        universe_path=universe_path,
        prices_path=prices_path,
        features_path=features_path,
        rule100_history_path=tmp_path / "missing_history.csv",
        decision_log_path=tmp_path / "missing_decisions.jsonl",
    )

    assert bool(trace.loc[0, "latest_pit_member"]) is True
    assert bool(trace.loc[0, "latest_local_price_return"]) is False
    assert trace.loc[0, "latest_exclusion_gate"] == "data unavailable"
    assert trace.loc[0, "latest_exclusion_detail"] == "no local price/return row on latest replay date"


def test_export_lifecycle_decision_log_writes_buy_sell_and_reasons(tmp_path: Path) -> None:
    from scripts.pit_lifecycle_replay import export_lifecycle_decision_log

    decision_path = tmp_path / "decision_log.jsonl"
    buy_sell_path = tmp_path / "buy_sell_log.jsonl"
    audit_path = tmp_path / "audit.json"

    df = export_lifecycle_decision_log(
        start_date="2025-01-02",
        end_date="2025-03-31",
        output_path=decision_path,
        buy_sell_path=buy_sell_path,
        audit_summary_path=audit_path,
        tickers=["TSM"],
    )

    assert decision_path.exists()
    assert buy_sell_path.exists()
    assert audit_path.exists()
    assert not df.empty
    assert {"BUY", "SELL"}.issubset(set(df["buy_sell"].dropna()))
    assert "primary_reason" in df.columns
    assert "reason_codes" in df.columns
    assert "rule100_confirmed" in df.columns
    assert "target_weight" in df.columns
    assert "suggested_weight_delta" in df.columns
    assert "rule100_provenance" in df.columns

    buy_sell_rows = [json.loads(line) for line in buy_sell_path.read_text(encoding="utf-8").splitlines()]
    assert buy_sell_rows
    assert all(row["buy_sell"] in {"BUY", "SELL"} for row in buy_sell_rows)
    assert all(row["primary_reason"] for row in buy_sell_rows)
    assert all(row["reason_codes"] for row in buy_sell_rows)
    assert all(row["target_weight"] >= 0 for row in buy_sell_rows)

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["buy_sell_rows"] == len(buy_sell_rows)
    assert "rule100_proxy_sources" in audit
    assert "baseline_comparison" in audit


def test_export_lifecycle_decision_log_matches_replay_events(tmp_path: Path) -> None:
    from scripts.pit_lifecycle_replay import export_lifecycle_decision_log, run_pit_replay

    events = run_pit_replay(
        start_date="2026-01-01",
        end_date="2026-05-11",
        log_path=tmp_path / "events.jsonl",
    )
    decisions = export_lifecycle_decision_log(
        start_date="2026-01-01",
        end_date="2026-05-11",
    )
    trades = decisions[decisions["buy_sell"].isin(["BUY", "SELL"])].copy()
    trades["event_action"] = trades["buy_sell"].map({"BUY": "ENTER", "SELL": "EXIT"})

    event_keys = list(zip(events["date"], events["ticker"], events["action"]))
    trade_keys = list(zip(trades["date"], trades["ticker"], trades["event_action"]))
    assert trade_keys == event_keys



# ── Feature Store Union Behavior ─────────────────────────────────────────


def test_feature_store_run_build_unions_pinned_permnos(tmp_path: Path, monkeypatch) -> None:
    """run_build unions pinned permnos into the selected universe."""
    from data import feature_store as fs

    captured_permnos = []

    # Stub _select_universe_permnos to return a small set
    monkeypatch.setattr(fs, "_select_universe_permnos", lambda **kw: [1, 2, 3])

    # Stub get_pinned_permnos to return thesis permnos
    import data.universe.loader as loader_mod
    monkeypatch.setattr(loader_mod, "get_pinned_permnos", lambda **kw: [100, 200, 300])

    # Stub _load_prices_long to capture what permnos were requested
    original_load = fs._load_prices_long

    def _capture_load(permnos, **kwargs):
        captured_permnos.extend(permnos)
        raise RuntimeError("Intentional abort after permno capture")

    monkeypatch.setattr(fs, "_load_prices_long", _capture_load)

    # Stub lock
    monkeypatch.setattr(fs.updater, "_acquire_update_lock", lambda: "test_token")
    monkeypatch.setattr(fs.updater, "_release_update_lock", lambda **kw: None)
    monkeypatch.setattr(fs, "_ensure_partitioned_feature_store", lambda *a, **kw: None)
    monkeypatch.setattr(fs, "_read_feature_date_bounds", lambda *a: (None, None))

    result = fs.run_build(start_year=2024, yearly_top_n=3)

    # The build will fail at _load_prices_long, but we captured the permnos
    assert 100 in captured_permnos
    assert 200 in captured_permnos
    assert 300 in captured_permnos
    assert 1 in captured_permnos


def test_feature_store_run_build_aborts_on_loader_failure(tmp_path: Path, monkeypatch) -> None:
    """run_build aborts when pinned loader fails and allow_missing=False."""
    from data import feature_store as fs

    monkeypatch.setattr(fs, "_select_universe_permnos", lambda **kw: [1, 2, 3])

    # Make loader raise
    import data.universe.loader as loader_mod
    monkeypatch.setattr(loader_mod, "get_pinned_permnos", lambda **kw: (_ for _ in ()).throw(FileNotFoundError("test")))

    monkeypatch.setattr(fs.updater, "_acquire_update_lock", lambda: "test_token")
    monkeypatch.setattr(fs.updater, "_release_update_lock", lambda **kw: None)
    monkeypatch.setattr(fs, "_ensure_partitioned_feature_store", lambda *a, **kw: None)
    monkeypatch.setattr(fs, "_read_feature_date_bounds", lambda *a: (None, None))

    result = fs.run_build(start_year=2024, yearly_top_n=3, allow_missing_pinned_universe=False)
    assert result["success"] is False


def test_feature_store_run_build_proceeds_with_override(tmp_path: Path, monkeypatch) -> None:
    """run_build proceeds when loader fails but allow_missing=True."""
    from data import feature_store as fs

    import data.universe.loader as loader_mod
    monkeypatch.setattr(loader_mod, "get_pinned_permnos", lambda **kw: (_ for _ in ()).throw(FileNotFoundError("test")))

    monkeypatch.setattr(fs, "_select_universe_permnos", lambda **kw: [1, 2, 3])
    monkeypatch.setattr(fs.updater, "_acquire_update_lock", lambda: "test_token")
    monkeypatch.setattr(fs.updater, "_release_update_lock", lambda **kw: None)
    monkeypatch.setattr(fs, "_ensure_partitioned_feature_store", lambda *a, **kw: None)
    monkeypatch.setattr(fs, "_read_feature_date_bounds", lambda *a: (None, None))

    # Will fail later (no real data) but should NOT abort at pinned loader
    result = fs.run_build(start_year=2024, yearly_top_n=3, allow_missing_pinned_universe=True)
    # Check it got past the pinned loader (failed somewhere else, not at pinned check)
    log_text = " ".join(result.get("log", []))
    assert "Proceeding with override" in log_text


# ── P1/P2 Hardening Edge Cases ───────────────────────────────────────────


def test_pinned_loader_rejects_duplicate_tickers(tmp_path: Path) -> None:
    manifest = tmp_path / "dup.yml"
    manifest.write_text("group:\n  - ticker: MU\n    start: '2025-01-02'\n    source: yahoo\n  - ticker: MU\n    start: '2025-01-02'\n    source: yahoo\n", encoding="utf-8")
    from data.universe.loader import load_pinned_manifest
    with pytest.raises(ValueError, match="Duplicate ticker"):
        load_pinned_manifest(manifest)


def test_pinned_loader_rejects_blank_ticker(tmp_path: Path) -> None:
    manifest = tmp_path / "blank.yml"
    manifest.write_text("group:\n  - ticker: '  '\n    start: '2025-01-02'\n    source: yahoo\n", encoding="utf-8")
    from data.universe.loader import load_pinned_manifest
    with pytest.raises(ValueError, match="blank ticker"):
        load_pinned_manifest(manifest)


def test_pinned_loader_rejects_empty_group(tmp_path: Path) -> None:
    manifest = tmp_path / "empty_group.yml"
    manifest.write_text("group: []\n", encoding="utf-8")
    from data.universe.loader import load_pinned_manifest
    with pytest.raises(ValueError, match="empty or not a list"):
        load_pinned_manifest(manifest)


def test_pinned_loader_strips_whitespace(tmp_path: Path) -> None:
    manifest = tmp_path / "ws.yml"
    manifest.write_text("group:\n  - ticker: ' MU '\n    start: '2025-01-02'\n    source: yahoo\n  - ticker: AMD\n    start: '2025-01-02'\n    source: yahoo\n", encoding="utf-8")
    from data.universe.loader import resolve_pinned_universe
    resolved = resolve_pinned_universe(manifest)
    tickers = [p.ticker for p in resolved]
    assert "MU" in tickers  # stripped


def test_get_pinned_permnos_raises_on_unresolved(tmp_path: Path, monkeypatch) -> None:
    """get_pinned_permnos must fail if any ticker has no permno mapping."""
    import data.universe.loader as loader_mod

    def _fake_resolve(manifest_path=None, tickers_path=None):
        from data.universe.loader import PinnedTicker
        return [
            PinnedTicker(ticker="MU", start="2025-01-02", source="yahoo", permno=53613, status="OK"),
            PinnedTicker(ticker="FAKE", start="2025-01-02", source="yahoo", permno=None, status="MISSING_MAP"),
        ]

    monkeypatch.setattr(loader_mod, "resolve_pinned_universe", _fake_resolve)
    with pytest.raises(ValueError, match="MISSING_MAP"):
        loader_mod.get_pinned_permnos()


def test_incremental_noop_blocked_when_pinned_permnos_missing(tmp_path: Path, monkeypatch) -> None:
    """Default (allow_missing=False): incremental no-op is blocked when pinned permnos are missing from feature store."""
    from data import feature_store as fs

    import data.universe.loader as loader_mod
    monkeypatch.setattr(loader_mod, "get_pinned_permnos", lambda **kw: [99999])  # permno not in fixture

    monkeypatch.setattr(fs.updater, "_acquire_update_lock", lambda: "test_token")
    monkeypatch.setattr(fs.updater, "_release_update_lock", lambda **kw: None)
    monkeypatch.setattr(fs, "_ensure_partitioned_feature_store", lambda *a, **kw: None)

    # Simulate: features already up to date (max date >= today)
    import pandas as pd
    now = pd.Timestamp.utcnow().tz_localize(None).normalize()
    monkeypatch.setattr(fs, "_read_feature_date_bounds", lambda *a: (pd.Timestamp("2024-01-01"), now))
    monkeypatch.setattr(fs, "_load_existing_feature_permnos", lambda *a: [1, 2, 3])  # pinned 99999 NOT here

    # Stop immediately after the guard fires by raising in _select_universe_permnos
    class _GuardPassed(Exception):
        pass

    monkeypatch.setattr(fs, "_select_universe_permnos", lambda **kw: (_ for _ in ()).throw(_GuardPassed()))

    result = fs.run_build(start_year=2024, yearly_top_n=3, allow_missing_pinned_universe=False)
    log_text = " ".join(result.get("log", []))
    assert "Incremental no-op blocked" in log_text
    # The build proceeded past the no-op guard (forced rebuild attempt)
    assert "already up to date (no incremental rows pending)" not in log_text
