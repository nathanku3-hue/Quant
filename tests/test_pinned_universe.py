"""Regression tests for pinned strategy universe behavior.

Validates:
- Manifest loads and resolves all thesis tickers to permnos
- Loader raises on missing/broken manifest (fail-closed)
- PIT replay default tickers include all pinned tickers
- Shared eligibility function matches expected gate logic
- diagnose_pinned_exclusions reports concrete reasons
"""
from __future__ import annotations

from pathlib import Path

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


def test_exit_on_parabolic() -> None:
    from scripts.pit_lifecycle_replay import is_pit_exit

    assert is_pit_exit(dist_sma20=0.15, trend_veto=False)


def test_exit_on_trend_veto() -> None:
    from scripts.pit_lifecycle_replay import is_pit_exit

    assert is_pit_exit(dist_sma20=0.03, trend_veto=True)


def test_no_exit_when_normal() -> None:
    from scripts.pit_lifecycle_replay import is_pit_exit

    assert not is_pit_exit(dist_sma20=0.08, trend_veto=False)


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
