from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
BACKFILL_SCRIPT_PATH = ROOT / "scripts" / "backfill_execution_latency.py"
SLIPPAGE_SCRIPT_PATH = ROOT / "scripts" / "evaluate_execution_slippage_baseline.py"


def _load_script_module(module_name: str, script_path: Path):
    assert script_path.exists(), f"Missing script: {script_path}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_backfill_latency_script_adds_heartbeat_annotations() -> None:
    mod = _load_script_module("backfill_execution_latency", BACKFILL_SCRIPT_PATH)
    source = pd.DataFrame(
        {
            "captured_at_utc": [
                "2026-03-01T15:30:00.100Z",
                "2026-03-01T15:30:00.200Z",
                "2026-03-01T15:30:00.300Z",
                "2026-03-01T15:30:00.400Z",
            ],
            "client_order_id": ["cid-1", "cid-2", "cid-3", "cid-4"],
            "latency_ms_submit_to_ack": [70.0, 75.0, 80.0, 520.0],
        }
    )

    out = mod.backfill_heartbeat_latency_columns(source, history_ms=[72.0] * 20)
    summary = mod.build_backfill_summary(out)

    assert len(out) == 4
    assert "heartbeat_decision" in out.columns
    assert "heartbeat_hard_ceiling_ms" in out.columns
    assert str(out.iloc[-1]["heartbeat_reason"]) == "hard_ceiling_exceeded"
    assert bool(out.iloc[-1]["heartbeat_is_hard_block"]) is True
    assert int(summary["rows"]) == 4
    assert int(summary["heartbeat_hard_block_rows"]) >= 1


def test_backfill_latency_script_sorts_by_event_time_for_history_bootstrap() -> None:
    mod = _load_script_module("backfill_execution_latency", BACKFILL_SCRIPT_PATH)
    source = pd.DataFrame(
        {
            "client_order_id": ["cid-late-arrival", "cid-early-arrival", "cid-mid-arrival"],
            "arrival_ts": [
                "2026-03-01T15:30:00.300Z",
                "2026-03-01T15:30:00.100Z",
                "2026-03-01T15:30:00.200Z",
            ],
            "execution_ts": [
                "2026-03-01T15:30:00.310Z",
                "2026-03-01T15:30:00.900Z",
                "2026-03-01T15:30:00.210Z",
            ],
            "captured_at_utc": [
                "2026-03-01T15:30:00.050Z",
                "2026-03-01T15:30:00.400Z",
                "2026-03-01T15:30:00.250Z",
            ],
            "latency_ms_submit_to_ack": [90.0, 70.0, 80.0],
        }
    )

    out = mod.backfill_heartbeat_latency_columns(source, history_ms=[72.0] * 20)

    assert out["client_order_id"].tolist() == [
        "cid-early-arrival",
        "cid-mid-arrival",
        "cid-late-arrival",
    ]


def test_backfill_loader_fails_loud_without_duckdb_even_when_parquet_exists(tmp_path: Path) -> None:
    mod = _load_script_module("backfill_execution_latency", BACKFILL_SCRIPT_PATH)
    duckdb_path = tmp_path / "missing.duckdb"
    parquet_path = tmp_path / "fallback.parquet"
    pd.DataFrame([{"latency_ms_submit_to_ack": 75.0}]).to_parquet(parquet_path, index=False)

    with pytest.raises(mod.PrimarySinkUnavailableError):
        mod._load_source_rows(
            duckdb_path=duckdb_path,
            parquet_path=parquet_path,
            table_name="execution_microstructure",
            source_mode=mod.SOURCE_MODE_DUCKDB_STRICT,
        )


def test_backfill_loader_allows_explicit_parquet_override_flag(tmp_path: Path) -> None:
    mod = _load_script_module("backfill_execution_latency", BACKFILL_SCRIPT_PATH)
    duckdb_path = tmp_path / "missing.duckdb"
    parquet_path = tmp_path / "override.parquet"
    expected = pd.DataFrame(
        [
            {"latency_ms_submit_to_ack": 71.0, "client_order_id": "cid-1"},
            {"latency_ms_submit_to_ack": 72.0, "client_order_id": "cid-2"},
        ]
    )
    expected.to_parquet(parquet_path, index=False)

    loaded = mod._load_source_rows(
        duckdb_path=duckdb_path,
        parquet_path=parquet_path,
        table_name="execution_microstructure",
        source_mode=mod.SOURCE_MODE_PARQUET_OVERRIDE,
    )

    assert loaded["client_order_id"].tolist() == ["cid-1", "cid-2"]


def test_backfill_loader_allows_explicit_parquet_override_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = _load_script_module("backfill_execution_latency", BACKFILL_SCRIPT_PATH)
    duckdb_path = tmp_path / "missing.duckdb"
    parquet_path = tmp_path / "override-env.parquet"
    pd.DataFrame([{"latency_ms_submit_to_ack": 73.0, "client_order_id": "cid-env"}]).to_parquet(
        parquet_path,
        index=False,
    )
    monkeypatch.setenv(mod.SOURCE_MODE_ENV, mod.SOURCE_MODE_PARQUET_OVERRIDE)

    loaded = mod._load_source_rows(
        duckdb_path=duckdb_path,
        parquet_path=parquet_path,
        table_name="execution_microstructure",
        source_mode=None,
    )

    assert loaded["client_order_id"].tolist() == ["cid-env"]


def test_backfill_summary_handles_missing_latency_column_without_crashing() -> None:
    mod = _load_script_module("backfill_execution_latency", BACKFILL_SCRIPT_PATH)
    frame = pd.DataFrame(
        [
            {"client_order_id": "cid-1", "heartbeat_decision": "PASS"},
            {"client_order_id": "cid-2", "heartbeat_decision": "BLOCK"},
        ]
    )

    summary = mod.build_backfill_summary(frame)

    assert int(summary["rows"]) == 2
    assert int(summary["latency_observed_rows"]) == 0
    assert summary["decision_counts"] == {"PASS": 1, "BLOCK": 1}


def test_slippage_baseline_script_preserves_signed_asymmetry() -> None:
    mod = _load_script_module("evaluate_execution_slippage_baseline", SLIPPAGE_SCRIPT_PATH)
    frame = pd.DataFrame(
        [
            {"side": "buy", "symbol": "AAPL", "slippage_bps": -12.0, "implementation_shortfall_dollars": -1.2},
            {"side": "buy", "symbol": "AAPL", "slippage_bps": 8.0, "implementation_shortfall_dollars": 0.8},
            {"side": "sell", "symbol": "MSFT", "slippage_bps": 5.0, "implementation_shortfall_dollars": 0.5},
            {"side": "sell", "symbol": "MSFT", "slippage_bps": 0.0, "implementation_shortfall_dollars": 0.0},
            {"side": "buy", "symbol": "NVDA", "slippage_bps": None, "implementation_shortfall_dollars": 0.1},
        ]
    )

    summary, by_side, by_symbol = mod.compute_slippage_baseline(frame)

    assert int(summary["rows"]) == 5
    assert int(summary["cohort_rows"]) == 5
    assert int(summary["observed_rows"]) == 4
    assert int(summary["zero_imputed_rows"]) == 1
    assert int(summary["favorable_rows"]) == 1
    assert int(summary["adverse_rows"]) == 2
    assert int(summary["neutral_rows"]) == 2
    assert float(summary["mean_slippage_bps"]) == pytest.approx(0.2, abs=1e-12)
    assert float(summary["total_implementation_shortfall_dollars"]) == pytest.approx(0.2, abs=1e-12)

    assert set(by_side["side"].astype(str)) == {"buy", "sell"}
    buy_row = by_side.loc[by_side["side"] == "buy"].iloc[0]
    sell_row = by_side.loc[by_side["side"] == "sell"].iloc[0]
    assert int(buy_row["rows"]) == 3
    assert int(buy_row["observed_rows"]) == 2
    assert int(buy_row["favorable_rows"]) == 1
    assert int(sell_row["adverse_rows"]) == 1
    assert set(by_symbol["symbol"].astype(str)) == {"AAPL", "MSFT", "NVDA"}
    nvda_row = by_symbol.loc[by_symbol["symbol"] == "NVDA"].iloc[0]
    assert int(nvda_row["rows"]) == 1
    assert int(nvda_row["observed_rows"]) == 0
    assert float(nvda_row["mean_slippage_bps"]) == pytest.approx(0.0, abs=1e-12)


def test_slippage_baseline_script_sanitizes_non_finite_rows() -> None:
    mod = _load_script_module("evaluate_execution_slippage_baseline", SLIPPAGE_SCRIPT_PATH)
    frame = pd.DataFrame(
        [
            {"side": "buy", "symbol": "AAPL", "slippage_bps": float("inf"), "implementation_shortfall_dollars": 1.0},
            {"side": "sell", "symbol": "MSFT", "slippage_bps": float("-inf"), "implementation_shortfall_dollars": float("inf")},
            {"side": "buy", "symbol": "NVDA", "slippage_bps": 10.0, "implementation_shortfall_dollars": 2.0},
        ]
    )

    summary, by_side, by_symbol = mod.compute_slippage_baseline(frame)

    assert int(summary["rows"]) == 3
    assert int(summary["observed_rows"]) == 1
    assert int(summary["zero_imputed_rows"]) == 2
    assert int(summary["adverse_rows"]) == 1
    assert int(summary["neutral_rows"]) == 2
    assert float(summary["mean_slippage_bps"]) == pytest.approx(10.0 / 3.0, abs=1e-12)
    assert float(summary["total_implementation_shortfall_dollars"]) == pytest.approx(3.0, abs=1e-12)

    assert set(by_side["side"].astype(str)) == {"buy", "sell"}
    sell_row = by_side.loc[by_side["side"] == "sell"].iloc[0]
    assert int(sell_row["observed_rows"]) == 0
    assert float(sell_row["implementation_shortfall_dollars_sum"]) == pytest.approx(0.0, abs=1e-12)
    assert set(by_symbol["symbol"].astype(str)) == {"AAPL", "MSFT", "NVDA"}


def test_slippage_loader_fails_loud_on_duckdb_query_error_without_fallback(tmp_path: Path) -> None:
    mod = _load_script_module("evaluate_execution_slippage_baseline", SLIPPAGE_SCRIPT_PATH)
    duckdb_path = tmp_path / "primary.duckdb"
    parquet_path = tmp_path / "fallback.parquet"
    pd.DataFrame([{"slippage_bps": 3.0, "side": "buy", "symbol": "AAPL"}]).to_parquet(parquet_path, index=False)
    with duckdb.connect(str(duckdb_path)) as conn:
        conn.execute("CREATE TABLE some_other_table(x INTEGER)")
        conn.execute("INSERT INTO some_other_table VALUES (1)")

    with pytest.raises(mod.PrimarySinkUnavailableError):
        mod._load_source_rows(
            duckdb_path=duckdb_path,
            parquet_path=parquet_path,
            table_name="execution_microstructure",
            source_mode=mod.SOURCE_MODE_DUCKDB_STRICT,
        )


def test_slippage_loader_allows_explicit_parquet_override(tmp_path: Path) -> None:
    mod = _load_script_module("evaluate_execution_slippage_baseline", SLIPPAGE_SCRIPT_PATH)
    duckdb_path = tmp_path / "missing.duckdb"
    parquet_path = tmp_path / "override.parquet"
    expected = pd.DataFrame(
        [
            {"slippage_bps": 1.0, "side": "buy", "symbol": "AAPL"},
            {"slippage_bps": -1.0, "side": "sell", "symbol": "MSFT"},
        ]
    )
    expected.to_parquet(parquet_path, index=False)

    loaded = mod._load_source_rows(
        duckdb_path=duckdb_path,
        parquet_path=parquet_path,
        table_name="execution_microstructure",
        source_mode=mod.SOURCE_MODE_PARQUET_OVERRIDE,
    )

    assert loaded["symbol"].tolist() == ["AAPL", "MSFT"]
