"""Focused tests for Position Lifecycle Replay.

Validates:
- JSONL append/read round-trip
- ENTER/EXIT event emission from optimizer lifecycle
- Dashboard renderer exists and handles empty state
- No forbidden action/signal vocabulary
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest


DASHBOARD = Path("dashboard.py")


# ── JSONL Log Tests ───────────────────────────────────────────────────────


def test_lifecycle_log_append_and_read(tmp_path: Path) -> None:
    from data.portfolio_lifecycle_log import append_lifecycle_event, read_lifecycle_log

    log_path = tmp_path / "test_log.jsonl"

    append_lifecycle_event("MU", "ENTER", "2026-01-15", 0.25, rating="", reason="optimizer_allocation", path=log_path)
    append_lifecycle_event("MU", "EXIT", "2026-03-10", 0.0, rating="EXIT / TRAIL TIGHT", reason="exit_or_kill", path=log_path)

    df = read_lifecycle_log(log_path)
    assert len(df) == 2
    assert list(df["ticker"]) == ["MU", "MU"]
    assert list(df["action"]) == ["ENTER", "EXIT"]
    assert df["weight"].iloc[0] == pytest.approx(0.25)
    assert df["weight"].iloc[1] == pytest.approx(0.0)


def test_lifecycle_log_empty_file_returns_empty_df(tmp_path: Path) -> None:
    from data.portfolio_lifecycle_log import read_lifecycle_log

    df = read_lifecycle_log(tmp_path / "nonexistent.jsonl")
    assert df.empty
    assert "ticker" in df.columns
    assert "action" in df.columns


def test_lifecycle_log_rejects_invalid_action(tmp_path: Path) -> None:
    from data.portfolio_lifecycle_log import append_lifecycle_event

    with pytest.raises(ValueError, match="action must be one of"):
        append_lifecycle_event("MU", "BUY", "2026-01-01", 0.1, path=tmp_path / "x.jsonl")


def test_lifecycle_log_atomic_append_preserves_existing(tmp_path: Path) -> None:
    from data.portfolio_lifecycle_log import append_lifecycle_event, read_lifecycle_log

    log_path = tmp_path / "test_log.jsonl"
    append_lifecycle_event("AMD", "ENTER", "2026-02-01", 0.15, path=log_path)
    append_lifecycle_event("LRCX", "ENTER", "2026-02-05", 0.10, path=log_path)

    df = read_lifecycle_log(log_path)
    assert len(df) == 2
    assert set(df["ticker"]) == {"AMD", "LRCX"}
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_lifecycle_log_malformed_json_fails_closed(tmp_path: Path) -> None:
    from data.portfolio_lifecycle_log import read_lifecycle_log

    log_path = tmp_path / "bad_log.jsonl"
    log_path.write_text(
        json.dumps({"ticker": "AAA", "action": "ENTER", "date": "2026-01-01", "weight": 0.2})
        + "\n"
        + "{bad-json\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Malformed lifecycle JSONL row 2"):
        read_lifecycle_log(log_path)


def test_open_lifecycle_positions_are_pit_safe(tmp_path: Path) -> None:
    from data.portfolio_lifecycle_log import append_lifecycle_event, get_open_lifecycle_positions

    log_path = tmp_path / "lifecycle.jsonl"
    append_lifecycle_event("AAA", "ENTER", "2026-01-01", 0.20, permno=1, path=log_path)
    append_lifecycle_event("AAA", "EXIT", "2026-01-05", 0.00, permno=1, path=log_path)
    append_lifecycle_event("BBB", "ENTER", "2026-01-03", 0.15, permno=2, path=log_path)
    append_lifecycle_event("CCC", "ENTER", "2026-02-01", 0.10, permno=3, path=log_path)

    open_positions = get_open_lifecycle_positions(as_of="2026-01-15", path=log_path)

    assert set(open_positions) == {"BBB"}
    assert open_positions["BBB"]["last_weight"] == pytest.approx(0.15)
    assert open_positions["BBB"]["source"] == "lifecycle_replay"


# ── Optimizer Lifecycle Hook Tests ────────────────────────────────────────


def test_lifecycle_enter_emitted_on_new_position(tmp_path: Path) -> None:
    from data.portfolio_lifecycle_log import read_lifecycle_log
    from strategies.portfolio_universe import (
        OptimizerUniverseResult,
        update_position_memory_after_optimization,
    )

    mem_path = tmp_path / "positions.json"
    log_path = tmp_path / "lifecycle.jsonl"

    # Monkey-patch the log path for this test
    import data.portfolio_lifecycle_log as log_mod
    original = log_mod.DEFAULT_LIFECYCLE_LOG_PATH
    log_mod.DEFAULT_LIFECYCLE_LOG_PATH = log_path

    try:
        weights = pd.Series({"10": 0.30, "20": 0.20})
        ticker_map = {"10": "MU", "20": "AMD"}
        universe = OptimizerUniverseResult(included=[], excluded=[], missing_mappings=[], insufficient_history=[], policy_summary={})

        update_position_memory_after_optimization(weights, ticker_map, universe, path=mem_path)

        df = read_lifecycle_log(log_path)
        assert len(df) == 2
        assert set(df["action"]) == {"ENTER"}
        assert set(df["ticker"]) == {"MU", "AMD"}
    finally:
        log_mod.DEFAULT_LIFECYCLE_LOG_PATH = original


def test_lifecycle_exit_emitted_on_kill(tmp_path: Path) -> None:
    from data.portfolio_lifecycle_log import read_lifecycle_log
    from strategies.portfolio_universe import (
        OptimizerUniverseResult,
        UniverseRecord,
        save_position_memory,
        update_position_memory_after_optimization,
    )

    mem_path = tmp_path / "positions.json"
    log_path = tmp_path / "lifecycle.jsonl"

    # Pre-seed position memory with MU
    save_position_memory({"MU": {"permno": 10, "last_weight": 0.25, "entry_date": "2026-01-01"}}, mem_path)

    import data.portfolio_lifecycle_log as log_mod
    original = log_mod.DEFAULT_LIFECYCLE_LOG_PATH
    log_mod.DEFAULT_LIFECYCLE_LOG_PATH = log_path

    try:
        weights = pd.Series(dtype=float)
        ticker_map = {}
        excluded_record = UniverseRecord(
            ticker="MU", permno=10, status="excluded", reason="exit_or_kill",
            rating="EXIT / TRAIL TIGHT (Mania Top)", action="BUY AGGRESSIVE", history_obs=2516,
        )
        universe = OptimizerUniverseResult(included=[], excluded=[excluded_record], missing_mappings=[], insufficient_history=[], policy_summary={})

        update_position_memory_after_optimization(weights, ticker_map, universe, path=mem_path)

        df = read_lifecycle_log(log_path)
        assert len(df) == 1
        assert df["action"].iloc[0] == "EXIT"
        assert df["ticker"].iloc[0] == "MU"
        assert df["reason"].iloc[0] == "exit_or_kill"
    finally:
        log_mod.DEFAULT_LIFECYCLE_LOG_PATH = original


def test_existing_open_lifecycle_position_does_not_emit_duplicate_enter(tmp_path: Path) -> None:
    from data.portfolio_lifecycle_log import append_lifecycle_event, read_lifecycle_log
    from strategies.portfolio_universe import (
        OptimizerUniverseResult,
        update_position_memory_after_optimization,
    )

    mem_path = tmp_path / "positions.json"
    log_path = tmp_path / "lifecycle.jsonl"
    append_lifecycle_event("AMD", "ENTER", "2026-01-01", 0.25, permno=10, path=log_path)

    weights = pd.Series({10: 0.25})
    ticker_map = {10: "AMD"}
    universe = OptimizerUniverseResult(included=[], excluded=[], missing_mappings=[], insufficient_history=[], policy_summary={})

    update_position_memory_after_optimization(
        weights,
        ticker_map,
        universe,
        path=mem_path,
        lifecycle_path=log_path,
    )

    df = read_lifecycle_log(log_path)
    assert len(df) == 1
    assert df["action"].iloc[0] == "ENTER"


# ── Dashboard Renderer Checks ─────────────────────────────────────────────


def test_lifecycle_renderer_exists_in_dashboard() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    assert "def _render_strategy_replay_section(" in source


def test_lifecycle_renderer_is_not_default_certified_portfolio_authority() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_allocation_page()")
    next_def = source.index("\ndef ", start + 1)
    page_source = source[start:next_def]

    assert "render_gv_fs0_current_decision(st)" in page_source
    assert "render_gv_fs0_certified_bundle(st)" not in page_source
    assert "_render_strategy_replay_section(" not in page_source
    assert "_render_portfolio_builder_section(" not in page_source
    assert "_render_shadow_portfolio_section()" not in page_source


def test_lifecycle_renderer_shows_truthful_empty_state() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_strategy_replay_section(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "No strategy replay data produced" in fn_source


def test_lifecycle_renderer_uses_enter_exit_not_buy_sell() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_event_ledger_chart(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    # Must use ENTER/EXIT vocabulary
    assert '"ENTER"' in fn_source
    assert '"EXIT"' in fn_source
    # Must NOT use BUY/SELL as marker labels
    assert 'name="BUY"' not in fn_source
    assert 'name="SELL"' not in fn_source


def test_lifecycle_transaction_log_shows_softmax_v1_target_separate_from_event_weight() -> None:
    """Verify ENTER hover shows Policy Target and Lifecycle Event Wt as separate fields."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_event_ledger_chart(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    # Hover template must show both fields separately, policy target first
    assert "Policy Target:" in fn_source
    assert "Lifecycle Event Wt:" in fn_source


def test_lifecycle_no_forbidden_tokens() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    # Check across all lifecycle-related functions
    start = source.index("def _render_strategy_replay_section(")
    # Find the end after _render_event_ledger_chart
    ledger_start = source.index("def _render_event_ledger_chart(", start)
    next_def = source.index("\ndef ", ledger_start + 1)
    fn_source = source[start:next_def].lower()

    forbidden = ["submit_order", "buy_sell_hold", "recommendation", "alert", "broker"]
    for token in forbidden:
        assert token not in fn_source, f"Forbidden token '{token}' in lifecycle renderer"



# ── Regression: Replay Chart Hover Weight Source ──────────────────────────


def test_replay_chart_hover_does_not_use_enters_weight_reason_directly() -> None:
    """Regression: ENTER hover must NOT use enters[['weight', 'reason']] as customdata.

    Rule of 100 v1 requires Softmax v1 Target as primary, Event Weight as audit.
    """
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_event_ledger_chart(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    # Must NOT use the old pattern
    assert 'enters[["weight", "reason"]]' not in fn_source
    assert "enters[['weight', 'reason']]" not in fn_source

    # Must show Policy Target first, then Lifecycle Event Wt
    assert "Policy Target:" in fn_source
    assert "Lifecycle Event Wt:" in fn_source
    target_pos = fn_source.index("Policy Target:")
    event_pos = fn_source.index("Lifecycle Event Wt:")
    assert target_pos < event_pos, "Policy Target must appear before Lifecycle Event Wt in hover"


def test_current_tsm_softmax_v1_history_values() -> None:
    """Regression: TSM appears as Event Weight=10%, Softmax v1 Target=0%, cash 80%.

    Validates the derived history artifact matches the expected policy output.
    """
    import pandas as pd
    from pathlib import Path

    history_path = Path("data/processed/rule100_softmax_v1_history.csv")
    if not history_path.exists():
        pytest.skip("rule100_softmax_v1_history.csv not built yet")

    history = pd.read_csv(history_path)
    tsm = history[history["ticker"].str.upper() == "TSM"].copy()
    assert not tsm.empty, "TSM must appear in softmax v1 history"

    latest = tsm.iloc[-1]
    assert latest["event_weight"] == pytest.approx(0.10, abs=0.001)
    assert latest["softmax_v1_target_weight"] == pytest.approx(0.0, abs=0.001)
    assert latest["softmax_v1_cash_residual"] == pytest.approx(0.80, abs=0.01)


# ── Regression: Policy Target Timeline UI Rendering ───────────────────────


def test_policy_target_timeline_sourced_from_csv_not_jsonl() -> None:
    """Regression: Strategy Replay must use build_strategy_replay engine."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_strategy_replay_section(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    # Must consume the shared context, not load CSV directly
    assert "full_context" in fn_source
    # Must not use the old CSV-only path
    assert "_ensure_rule100_softmax_v1_history()" not in fn_source


def test_policy_target_timeline_renders_daily_target_chart() -> None:
    """Regression: Policy Target Timeline renders a line chart of daily targets."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_policy_target_timeline(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    # Must plot softmax_v1_target_weight as a line
    assert "softmax_v1_target_weight" in fn_source
    assert "Policy Target Weight" in fn_source
    assert 'mode="lines+markers"' in fn_source


def test_policy_target_table_has_required_columns() -> None:
    """Regression: Policy Target History table must show all required columns."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_policy_target_timeline(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    required_columns = [
        "Policy Target Weight",
        "Lifecycle Event Wt",
        "Target - Event",
        "Cash Residual",
        "Eligibility Reason",
    ]
    for col in required_columns:
        assert col in fn_source, f"Required column '{col}' missing from policy target table"


def test_event_ledger_replay_labeled_separately() -> None:
    """Regression: Strategy Replay section uses build_selected_method_replay and shows timeline."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _build_dashboard_strategy_replay_context(")
    next_def = source.index("\ndef ", start + 1)
    context_source = source[start:next_def]
    render_start = source.index("def _render_strategy_replay_section(")
    render_next = source.index("\ndef ", render_start + 1)
    render_source = source[render_start:render_next]

    assert "Strategy Replay Timeline" in render_source
    assert "build_selected_method_replay(" in context_source
    assert "_dashboard_input_loader" in context_source
    assert "_dashboard_context_from_backend_bundle(" in context_source


def test_event_ledger_chart_handles_missing_softmax_overlay_columns() -> None:
    """Regression: ENTER annotations must not crash before v1 overlay columns exist."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_event_ledger_chart(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert '"rule100_softmax_v1_target_weight" in enters.columns' in fn_source
    assert "pd.Series(0.0, index=enters.index" in fn_source
    assert 'enters.get("rule100_softmax_v1_target_weight")' not in fn_source


def test_tsm_latest_target_visible_in_policy_timeline() -> None:
    """Regression: TSM 2026-05-11 target=0% must be visible via policy target timeline.

    The policy target timeline sources from rule100_softmax_v1_history.csv directly,
    so daily TIGHTEN rows (which have no ENTER/EXIT event) are visible.
    """
    from pathlib import Path

    history_path = Path("data/processed/rule100_softmax_v1_history.csv")
    if not history_path.exists():
        pytest.skip("rule100_softmax_v1_history.csv not built yet")

    history = pd.read_csv(history_path)
    history["date"] = pd.to_datetime(history["date"], errors="coerce")
    tsm = history[history["ticker"].str.upper() == "TSM"].copy()

    # TSM 2026-05-11 must exist in the CSV (this is what the timeline renders)
    tsm_may11 = tsm[tsm["date"] == "2026-05-11"]
    assert not tsm_may11.empty, "TSM 2026-05-11 must exist in v1 history CSV"
    assert tsm_may11.iloc[0]["softmax_v1_target_weight"] == pytest.approx(0.0, abs=0.001)
    assert tsm_may11.iloc[0]["eligibility_reason"] == "tighten_below_hold_threshold"

    # Confirm this row has NO corresponding ENTER/EXIT event (proving timeline is needed)
    from data.portfolio_lifecycle_log import read_lifecycle_log
    events = read_lifecycle_log()
    if not events.empty:
        events["date"] = pd.to_datetime(events["date"], errors="coerce")
        tsm_events_may11 = events[
            (events["ticker"].str.upper() == "TSM") &
            (events["date"].dt.date == pd.Timestamp("2026-05-11").date())
        ]
        assert tsm_events_may11.empty, (
            "TSM 2026-05-11 should NOT have an ENTER/EXIT event; "
            "it is only visible via the policy target timeline"
        )


def test_event_ledger_chart_unchanged_enter_exit_markers() -> None:
    """Regression: Event Ledger chart still uses ENTER/EXIT markers, not daily rows."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_event_ledger_chart(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert '"ENTER"' in fn_source
    assert '"EXIT"' in fn_source
    assert 'name="ENTER"' in fn_source
    assert 'name="EXIT"' in fn_source
    # Must NOT plot daily HOLD/TIGHTEN rows
    assert 'name="HOLD"' not in fn_source
    assert 'name="TIGHTEN"' not in fn_source
