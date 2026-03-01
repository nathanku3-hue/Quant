from __future__ import annotations

import json
import os
import time
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from execution import microstructure as microstructure_module
from execution.microstructure import _shutdown_execution_microstructure_spoolers
from execution.microstructure import append_execution_microstructure
from execution.microstructure import build_execution_telemetry_rows
from execution.microstructure import get_execution_microstructure_spool_status
from execution.microstructure import wait_for_execution_microstructure_flush


@pytest.fixture(autouse=True)
def _cleanup_spoolers() -> None:
    _shutdown_execution_microstructure_spoolers()
    yield
    _shutdown_execution_microstructure_spoolers()


def _sample_execute_results() -> list[dict]:
    return [
        {
            "order": {
                "client_order_id": "cid-aapl-1",
                "symbol": "AAPL",
                "side": "buy",
                "qty": 10,
                "order_type": "limit",
                "limit_price": 100.25,
                "arrival_ts": "2026-03-01T15:30:00.100Z",
                "arrival_quote_ts": "2026-03-01T15:30:00.099Z",
                "arrival_bid_price": 100.00,
                "arrival_ask_price": 100.20,
                "arrival_price": 100.10,
            },
            "result": {
                "ok": True,
                "order_id": "ord-aapl-1",
                "status": "filled",
                "submit_sent_ts": "2026-03-01T15:30:00.150Z",
                "broker_ack_ts": "2026-03-01T15:30:00.250Z",
                "filled_at": "2026-03-01T15:30:00.900Z",
                "partial_fills": [
                    {
                        "fill_index": 1,
                        "fill_qty": 4.0,
                        "fill_price": 100.20,
                        "fill_ts": "2026-03-01T15:30:00.700Z",
                        "fill_venue": "XNAS",
                        "source": "broker_activity",
                    },
                    {
                        "fill_index": 2,
                        "fill_qty": 6.0,
                        "fill_price": 100.40,
                        "fill_ts": "2026-03-01T15:30:00.900Z",
                        "fill_venue": "XNAS",
                        "source": "broker_activity",
                    },
                ],
                "fill_summary": {
                    "fill_count": 2,
                    "fill_qty": 10.0,
                    "fill_notional": 1004.0,
                    "fill_vwap": 100.4,
                    "first_fill_ts": "2026-03-01T15:30:00.700Z",
                    "last_fill_ts": "2026-03-01T15:30:00.900Z",
                },
            },
        }
    ]


def test_build_execution_telemetry_rows_computes_buy_is_slippage_and_latency() -> None:
    order_rows, fill_rows = build_execution_telemetry_rows(
        _sample_execute_results(),
        batch_id="20260301-batch-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )

    assert len(order_rows) == 1
    assert len(fill_rows) == 2

    row = order_rows[0]
    assert row["client_order_id"] == "cid-aapl-1"
    assert row["arrival_price"] == 100.10
    assert row["fill_vwap"] == 100.4
    assert row["fill_qty"] == 10.0

    # IS (buy) = (VWAP_fill - Arrival) * Qty
    assert float(row["implementation_shortfall_dollars"]) == pytest.approx(3.0, abs=1e-12)
    assert float(row["slippage_bps"]) == pytest.approx(29.97002997002999, abs=1e-9)

    assert row["latency_ms_command_to_submit"] == 50.0
    assert row["latency_ms_submit_to_ack"] == 100.0
    assert row["latency_ms_ack_to_first_fill"] == 450.0
    assert row["latency_ms_command_to_first_fill"] == 600.0


def test_build_execution_telemetry_rows_computes_sell_is_slippage_with_arrival_normalization() -> None:
    execute_results = [
        {
            "order": {
                "client_order_id": "cid-msft-sell-1",
                "symbol": "MSFT",
                "side": "sell",
                "qty": 8,
                "order_type": "market",
                "arrival_ts": "2026-03-01T15:35:00.100Z",
                "arrival_price": 100.0,
            },
            "result": {
                "ok": True,
                "order_id": "ord-msft-sell-1",
                "status": "filled",
                "submit_sent_ts": "2026-03-01T15:35:00.150Z",
                "broker_ack_ts": "2026-03-01T15:35:00.250Z",
                "filled_at": "2026-03-01T15:35:00.900Z",
                "partial_fills": [
                    {
                        "fill_index": 1,
                        "fill_qty": 8.0,
                        "fill_price": 99.5,
                        "fill_ts": "2026-03-01T15:35:00.900Z",
                        "fill_venue": "XNAS",
                        "source": "broker_activity",
                    }
                ],
                "fill_summary": {
                    "fill_count": 1,
                    "fill_qty": 8.0,
                    "fill_notional": 796.0,
                    "fill_vwap": 99.5,
                    "first_fill_ts": "2026-03-01T15:35:00.900Z",
                    "last_fill_ts": "2026-03-01T15:35:00.900Z",
                },
            },
        }
    ]

    order_rows, fill_rows = build_execution_telemetry_rows(
        execute_results,
        batch_id="20260301-batch-sell-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )

    assert len(order_rows) == 1
    assert len(fill_rows) == 1

    row = order_rows[0]
    assert row["side"] == "sell"
    assert row["arrival_price"] == 100.0
    assert row["fill_vwap"] == 99.5
    assert row["fill_qty"] == 8.0

    # IS (sell) = (Arrival - VWAP_fill) * Qty, normalized in bps by Arrival.
    assert float(row["implementation_shortfall_dollars"]) == pytest.approx(4.0, abs=1e-12)
    assert float(row["slippage_bps"]) == pytest.approx(50.0, abs=1e-12)


def test_build_execution_telemetry_rows_preserves_negative_slippage_for_favorable_buy() -> None:
    execute_results = [
        {
            "order": {
                "client_order_id": "cid-aapl-favorable-buy-1",
                "symbol": "AAPL",
                "side": "buy",
                "qty": 5,
                "order_type": "market",
                "arrival_ts": "2026-03-01T15:40:00.100Z",
                "arrival_price": 100.0,
            },
            "result": {
                "ok": True,
                "order_id": "ord-aapl-favorable-buy-1",
                "status": "filled",
                "submit_sent_ts": "2026-03-01T15:40:00.120Z",
                "broker_ack_ts": "2026-03-01T15:40:00.150Z",
                "filled_at": "2026-03-01T15:40:00.300Z",
                "fill_summary": {
                    "fill_count": 1,
                    "fill_qty": 5.0,
                    "fill_notional": 495.0,
                    "fill_vwap": 99.0,
                    "first_fill_ts": "2026-03-01T15:40:00.300Z",
                    "last_fill_ts": "2026-03-01T15:40:00.300Z",
                },
            },
        }
    ]

    order_rows, _ = build_execution_telemetry_rows(
        execute_results,
        batch_id="20260301-batch-favorable-buy-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )

    assert len(order_rows) == 1
    row = order_rows[0]
    assert float(row["implementation_shortfall_dollars"]) == pytest.approx(-5.0, abs=1e-12)
    assert float(row["slippage_bps"]) == pytest.approx(-100.0, abs=1e-12)


def test_build_execution_telemetry_rows_preserves_zero_slippage_without_abs_coercion() -> None:
    execute_results = [
        {
            "order": {
                "client_order_id": "cid-msft-zero-slippage-1",
                "symbol": "MSFT",
                "side": "sell",
                "qty": 4,
                "order_type": "market",
                "arrival_ts": "2026-03-01T15:42:00.100Z",
                "arrival_price": 250.0,
            },
            "result": {
                "ok": True,
                "order_id": "ord-msft-zero-slippage-1",
                "status": "filled",
                "submit_sent_ts": "2026-03-01T15:42:00.130Z",
                "broker_ack_ts": "2026-03-01T15:42:00.180Z",
                "filled_at": "2026-03-01T15:42:00.350Z",
                "fill_summary": {
                    "fill_count": 1,
                    "fill_qty": 4.0,
                    "fill_notional": 1000.0,
                    "fill_vwap": 250.0,
                    "first_fill_ts": "2026-03-01T15:42:00.350Z",
                    "last_fill_ts": "2026-03-01T15:42:00.350Z",
                },
            },
        }
    ]

    order_rows, _ = build_execution_telemetry_rows(
        execute_results,
        batch_id="20260301-batch-zero-slippage-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )

    assert len(order_rows) == 1
    row = order_rows[0]
    assert float(row["implementation_shortfall_dollars"]) == pytest.approx(0.0, abs=1e-12)
    assert float(row["slippage_bps"]) == pytest.approx(0.0, abs=1e-12)


def test_to_positive_float_or_none_rejects_non_finite_values() -> None:
    assert microstructure_module._to_positive_float_or_none(float("inf")) is None
    assert microstructure_module._to_positive_float_or_none(float("-inf")) is None
    assert microstructure_module._to_positive_float_or_none(float("nan")) is None


def test_evaluate_heartbeat_freshness_blocks_when_hard_ceiling_exceeded() -> None:
    metrics = microstructure_module.evaluate_heartbeat_freshness(
        submit_to_ack_latency_ms=610.0,
        latency_history_ms=[80.0, 90.0, 85.0, 95.0, 88.0, 92.0, 86.0, 89.0, 91.0, 87.0, 90.0, 88.0],
        hard_ceiling_ms=500.0,
    )

    assert metrics["heartbeat_decision"] == "BLOCK"
    assert metrics["heartbeat_reason"] == "hard_ceiling_exceeded"
    assert metrics["heartbeat_is_blocked"] is True
    assert metrics["heartbeat_is_hard_block"] is True
    assert float(metrics["heartbeat_hard_ceiling_ms"]) == pytest.approx(500.0, abs=1e-12)


def test_evaluate_heartbeat_freshness_adapts_threshold_under_open_spike_regime() -> None:
    normal_metrics = microstructure_module.evaluate_heartbeat_freshness(
        submit_to_ack_latency_ms=260.0,
        latency_history_ms=[62.0, 65.0, 64.0, 66.0, 63.0, 65.0, 67.0, 66.0, 64.0, 65.0, 66.0, 64.0],
        hard_ceiling_ms=500.0,
    )
    open_metrics = microstructure_module.evaluate_heartbeat_freshness(
        submit_to_ack_latency_ms=260.0,
        latency_history_ms=[180.0, 220.0, 260.0, 300.0, 340.0, 380.0, 420.0, 360.0, 320.0, 280.0, 240.0, 200.0],
        hard_ceiling_ms=500.0,
    )

    assert normal_metrics["heartbeat_decision"] == "BLOCK"
    assert normal_metrics["heartbeat_reason"] == "adaptive_limit_exceeded"
    assert open_metrics["heartbeat_decision"] == "PASS"
    assert open_metrics["heartbeat_reason"] == "within_limit"
    assert float(open_metrics["heartbeat_adaptive_limit_ms"]) > float(normal_metrics["heartbeat_adaptive_limit_ms"])


def test_load_recent_submit_to_ack_history_ms_enforces_event_time_ordering(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    table_name = "execution_microstructure"

    with duckdb.connect(str(duckdb_path)) as conn:
        conn.execute(
            f"""
            CREATE TABLE {table_name} (
                client_order_id VARCHAR,
                latency_ms_submit_to_ack DOUBLE,
                arrival_ts VARCHAR,
                execution_ts VARCHAR,
                captured_at_utc VARCHAR
            )
            """
        )
        conn.executemany(
            f"INSERT INTO {table_name} (client_order_id, latency_ms_submit_to_ack, arrival_ts, execution_ts, captured_at_utc) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    "cid-arrival-100",
                    100.0,
                    "2026-03-01T15:30:00.100Z",
                    "2026-03-01T15:30:00.700Z",
                    "2026-03-01T15:30:00.900Z",
                ),
                (
                    "cid-arrival-200",
                    200.0,
                    "2026-03-01T15:30:00.200Z",
                    "2026-03-01T15:30:00.210Z",
                    "2026-03-01T15:30:00.100Z",
                ),
                (
                    "cid-arrival-300",
                    300.0,
                    "2026-03-01T15:30:00.300Z",
                    "2026-03-01T15:30:00.305Z",
                    "2026-03-01T15:30:00.050Z",
                ),
                (
                    "cid-old-event-new-capture",
                    50.0,
                    "2026-03-01T15:29:59.900Z",
                    "2026-03-01T15:30:00.000Z",
                    "2026-03-01T15:31:00.000Z",
                ),
            ],
        )

    history = microstructure_module._load_recent_submit_to_ack_history_ms(
        duckdb_path=duckdb_path,
        table_name=table_name,
        window_size=3,
    )

    assert history == [100.0, 200.0, 300.0]


def test_build_execution_telemetry_rows_emits_heartbeat_fields_with_rolling_history() -> None:
    order_rows, _ = build_execution_telemetry_rows(
        _sample_execute_results(),
        batch_id="20260301-batch-heartbeat-1",
        strategy="ALPHA_SOVEREIGN_V1",
        submit_to_ack_history_ms=[85.0] * 20,
    )

    assert len(order_rows) == 1
    row = order_rows[0]
    assert row["heartbeat_mode"] == "adaptive_mad"
    assert row["heartbeat_window_count"] == 20
    assert float(row["heartbeat_latency_ms"]) == pytest.approx(100.0, abs=1e-12)
    assert row["heartbeat_decision"] in {"PASS", "BLOCK"}
    assert "heartbeat_adaptive_limit_ms" in row
    assert "heartbeat_hard_ceiling_ms" in row


def test_build_execution_telemetry_rows_backfills_recovery_anchors_and_clamps_clock_drift_latency() -> None:
    execute_results = [
        {
            "order": {
                "client_order_id": "cid-aapl-recovery-anchors-1",
                "symbol": "AAPL",
                "side": "buy",
                "qty": 1,
                "order_type": "market",
                "arrival_ts": "2026-03-01T15:45:00.500Z",
                "arrival_price": 100.0,
            },
            "result": {
                "ok": True,
                "order_id": "ord-aapl-recovery-anchors-1",
                "status": "filled",
                "recovered": True,
                "created_at": "2026-03-01T15:45:00.150Z",
                "submitted_at": "2026-03-01T15:45:00.300Z",
                "updated_at": "2026-03-01T15:45:00.200Z",
                "filled_at": "2026-03-01T15:45:00.100Z",
                "fill_summary": {
                    "fill_count": 1,
                    "fill_qty": 1.0,
                    "fill_notional": 100.0,
                    "fill_vwap": 100.0,
                    "first_fill_ts": "2026-03-01T15:45:00.100Z",
                    "last_fill_ts": "2026-03-01T15:45:00.100Z",
                },
            },
        }
    ]

    order_rows, _ = build_execution_telemetry_rows(
        execute_results,
        batch_id="20260301-batch-recovery-anchors-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )

    assert len(order_rows) == 1
    row = order_rows[0]
    assert row["submit_sent_ts"] == "2026-03-01T15:45:00.300Z"
    assert row["broker_ack_ts"] == "2026-03-01T15:45:00.200Z"
    assert row["latency_ms_command_to_submit"] == 0.0
    assert row["latency_ms_submit_to_ack"] == 0.0
    assert row["latency_ms_ack_to_first_fill"] == 0.0
    assert row["latency_ms_command_to_first_fill"] == 0.0


def test_build_execution_telemetry_rows_missing_broker_ack_blocks_heartbeat() -> None:
    execute_results = [
        {
            "order": {
                "client_order_id": "cid-aapl-missing-ack-1",
                "symbol": "AAPL",
                "side": "buy",
                "qty": 1,
                "order_type": "market",
                "arrival_ts": "2026-03-01T15:46:00.500Z",
                "arrival_price": 100.0,
            },
            "result": {
                "ok": True,
                "order_id": "ord-aapl-missing-ack-1",
                "status": "accepted",
                "submit_sent_ts": "2026-03-01T15:46:00.550Z",
                "submitted_at": "2026-03-01T15:46:00.550Z",
                # no broker_ack_ts / ack_ts / updated_at
            },
        }
    ]

    order_rows, _ = build_execution_telemetry_rows(
        execute_results,
        batch_id="20260301-batch-missing-ack-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )

    assert len(order_rows) == 1
    row = order_rows[0]
    assert row["submit_sent_ts"] == "2026-03-01T15:46:00.550Z"
    assert row["broker_ack_ts"] is None
    assert row["latency_ms_submit_to_ack"] is None
    assert row["heartbeat_decision"] == "BLOCK"
    assert row["heartbeat_reason"] == "latency_missing"


def test_build_execution_telemetry_rows_reconstructs_order_summary_from_partial_fills_when_fill_summary_missing() -> None:
    execute_results = [
        {
            "order": {
                "client_order_id": "cid-aapl-partial-summary-fallback-1",
                "symbol": "AAPL",
                "side": "buy",
                "qty": 3,
                "order_type": "limit",
                "limit_price": 101.0,
                "arrival_ts": "2026-03-01T15:50:00.100Z",
                "arrival_price": 100.0,
            },
            "result": {
                "ok": True,
                "order_id": "ord-aapl-partial-summary-fallback-1",
                "status": "partially_filled",
                "submit_sent_ts": "2026-03-01T15:50:00.150Z",
                "broker_ack_ts": "2026-03-01T15:50:00.200Z",
                "partial_fills": [
                    {
                        "fill_index": 1,
                        "fill_qty": 1.0,
                        "fill_price": 100.0,
                        "fill_ts": "2026-03-01T15:50:00.400Z",
                        "fill_venue": "XNAS",
                        "source": "broker_activity",
                    },
                    {
                        "fill_index": 2,
                        "fill_qty": 2.0,
                        "fill_price": 101.0,
                        "fill_ts": "2026-03-01T15:50:00.900Z",
                        "fill_venue": "XNAS",
                        "source": "broker_activity",
                    },
                ],
            },
        }
    ]

    order_rows, fill_rows = build_execution_telemetry_rows(
        execute_results,
        batch_id="20260301-batch-partial-summary-fallback-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )

    assert len(order_rows) == 1
    assert len(fill_rows) == 2
    row = order_rows[0]
    assert row["fill_count"] == 2
    assert row["fill_qty"] == pytest.approx(3.0, abs=1e-12)
    assert row["fill_notional"] == pytest.approx(302.0, abs=1e-12)
    assert row["fill_vwap"] == pytest.approx((100.0 + 2.0 * 101.0) / 3.0, abs=1e-12)
    assert row["first_fill_ts"] == "2026-03-01T15:50:00.400Z"
    assert row["last_fill_ts"] == "2026-03-01T15:50:00.900Z"
    assert float(row["implementation_shortfall_dollars"]) == pytest.approx(2.0, abs=1e-12)
    assert float(row["slippage_bps"]) == pytest.approx(66.66666666666667, abs=1e-12)


def test_build_execution_telemetry_rows_synthesizes_fill_row_when_only_fill_summary_present() -> None:
    execute_results = [
        {
            "order": {
                "client_order_id": "cid-aapl-summary-only-1",
                "symbol": "AAPL",
                "side": "buy",
                "qty": 2,
                "order_type": "market",
                "arrival_ts": "2026-03-01T16:00:00.100Z",
                "arrival_price": 100.0,
            },
            "result": {
                "ok": True,
                "order_id": "ord-aapl-summary-only-1",
                "status": "filled",
                "submit_sent_ts": "2026-03-01T16:00:00.150Z",
                "broker_ack_ts": "2026-03-01T16:00:00.180Z",
                "filled_at": "2026-03-01T16:00:00.300Z",
                "fill_summary": {
                    "fill_count": 1,
                    "fill_qty": 2.0,
                    "fill_notional": 201.0,
                    "fill_vwap": 100.5,
                    "first_fill_ts": "2026-03-01T16:00:00.300Z",
                    "last_fill_ts": "2026-03-01T16:00:00.300Z",
                },
            },
        }
    ]

    order_rows, fill_rows = build_execution_telemetry_rows(
        execute_results,
        batch_id="20260301-batch-summary-only-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )

    assert len(order_rows) == 1
    assert len(fill_rows) == 1
    fill = fill_rows[0]
    assert fill["fill_qty"] == pytest.approx(2.0, abs=1e-12)
    assert fill["fill_price"] == pytest.approx(100.5, abs=1e-12)
    assert fill["fill_source"] == "summary_fallback"


def test_append_execution_microstructure_appends_spool_jsonl(tmp_path: Path) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"

    summary = append_execution_microstructure(
        _sample_execute_results(),
        batch_id="20260301-batch-1",
        strategy="ALPHA_SOVEREIGN_V1",
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        spool_path=spool_path,
    )

    assert summary["orders_prepared"] == 1
    assert summary["fills_prepared"] == 2
    assert summary["orders_written"] == 1
    assert summary["fills_written"] == 2
    assert summary["spool_records_appended"] == 3
    assert spool_path.exists()

    lines = [line for line in spool_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 3
    records = [json.loads(line) for line in lines]

    order_records = [record for record in records if record.get("record_type") == "order"]
    fill_records = [record for record in records if record.get("record_type") == "fill"]
    assert len(order_records) == 1
    assert len(fill_records) == 2
    assert str(order_records[0]["row"]["client_order_id"]) == "cid-aapl-1"


def test_append_execution_microstructure_async_flush_writes_parquet_and_duckdb(tmp_path: Path) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"

    summary = append_execution_microstructure(
        _sample_execute_results(),
        batch_id="20260301-batch-1",
        strategy="ALPHA_SOVEREIGN_V1",
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        spool_path=spool_path,
    )

    assert summary["orders_prepared"] == 1
    assert summary["fills_prepared"] == 2
    assert summary["orders_written"] == 1
    assert summary["fills_written"] == 2

    drained = wait_for_execution_microstructure_flush(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        timeout_seconds=5.0,
    )
    assert drained is True
    assert parquet_path.exists()
    assert fills_parquet_path.exists()
    assert duckdb_path.exists()

    order_df = pd.read_parquet(parquet_path)
    fill_df = pd.read_parquet(fills_parquet_path)
    assert int(len(order_df)) == 1
    assert int(len(fill_df)) == 2
    assert str(order_df.loc[0, "client_order_id"]) == "cid-aapl-1"
    assert "heartbeat_decision" in order_df.columns
    assert "heartbeat_adaptive_limit_ms" in order_df.columns
    assert str(order_df.loc[0, "heartbeat_decision"]) in {"PASS", "BLOCK"}

    with duckdb.connect(str(duckdb_path)) as conn:
        order_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure").fetchone()[0]
        fill_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure_fills").fetchone()[0]

    assert int(order_count) == 1
    assert int(fill_count) == 2


def test_append_execution_microstructure_flush_failure_is_non_blocking_and_preserves_spool(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"

    def _raise_sink_failure(*, rows_df: pd.DataFrame, fills_df: pd.DataFrame, duckdb_path: Path, table_name: str) -> tuple[int, int]:
        raise RuntimeError("forced sink failure for async flush")

    monkeypatch.setattr("execution.microstructure._append_duckdb_rows", _raise_sink_failure)

    started = time.perf_counter()
    summary = append_execution_microstructure(
        _sample_execute_results(),
        batch_id="20260301-batch-1",
        strategy="ALPHA_SOVEREIGN_V1",
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        spool_path=spool_path,
    )
    elapsed_seconds = time.perf_counter() - started

    assert summary["orders_prepared"] == 1
    assert summary["fills_prepared"] == 2
    assert summary["orders_written"] == 1
    assert summary["fills_written"] == 2
    assert summary["spool_records_appended"] == 3
    assert elapsed_seconds < 0.5

    last_status: dict | None = None
    deadline = time.monotonic() + 3.0
    while time.monotonic() <= deadline:
        last_status = get_execution_microstructure_spool_status(
            spool_path=spool_path,
            parquet_path=parquet_path,
            fills_parquet_path=fills_parquet_path,
            duckdb_path=duckdb_path,
        )
        if _clean_status_error(last_status):
            break
        time.sleep(0.05)

    assert last_status is not None
    assert int(last_status["pending_bytes"]) > 0
    assert "forced sink failure for async flush" in _clean_status_error(last_status)

    lines = [line for line in spool_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 3


def test_flush_quarantines_malformed_spool_lines_and_continues_valid_records(tmp_path: Path) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"
    bad_path = spool_path.with_suffix(f"{spool_path.suffix}.bad")

    order_rows, _ = build_execution_telemetry_rows(
        _sample_execute_results(),
        batch_id="20260301-batch-malformed-line-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )
    good_record = {"record_type": "order", "row": order_rows[0]}
    malformed_line = '{"record_type":"order","row":{"broken":true}'
    payload = "\n".join([json.dumps(good_record), malformed_line]) + "\n"
    spool_path.write_text(payload, encoding="utf-8")

    drained = wait_for_execution_microstructure_flush(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        timeout_seconds=5.0,
    )
    assert drained is True

    assert bad_path.exists()
    bad_entries = [json.loads(line) for line in bad_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(bad_entries) == 1
    assert str(bad_entries[0].get("reason")) == "json_decode_error"

    with duckdb.connect(str(duckdb_path)) as conn:
        order_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure").fetchone()[0]
    assert int(order_count) == 1


def test_read_spool_quarantines_schema_invalid_json_with_cursor_advance(tmp_path: Path) -> None:
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"
    bad_path = spool_path.with_suffix(f"{spool_path.suffix}.bad")
    invalid_record = {"record_type": "order", "row": "not-an-object"}
    payload = f"{json.dumps(invalid_record)}\n"
    spool_path.write_text(payload, encoding="utf-8")

    records, cursor, quarantined_lines = microstructure_module._read_spool_records_since(
        spool_path=spool_path,
        start_offset=0,
        generation=0,
        bad_path=bad_path,
    )

    assert records == []
    assert quarantined_lines == 1
    assert cursor == int(spool_path.stat().st_size)
    bad_entries = [json.loads(line) for line in bad_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(bad_entries) == 1
    assert str(bad_entries[0].get("reason")) == "schema_row_not_object"


def test_flush_quarantines_stale_trailing_partial_line_and_drains_spool(tmp_path: Path) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"
    bad_path = spool_path.with_suffix(f"{spool_path.suffix}.bad")
    offset_path = spool_path.with_suffix(f"{spool_path.suffix}.offset")
    generation_path = spool_path.with_suffix(f"{spool_path.suffix}.gen")

    order_rows, _ = build_execution_telemetry_rows(
        _sample_execute_results(),
        batch_id="20260301-batch-partial-line-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )
    good_record = {"record_type": "order", "row": order_rows[0]}
    trailing_partial = '{"record_type":"order","row":{"incomplete":true}'
    spool_path.write_text(f"{json.dumps(good_record)}\n{trailing_partial}", encoding="utf-8")
    stale_ts = time.time() - 60.0
    os.utime(spool_path, (stale_ts, stale_ts))

    summary = microstructure_module._flush_spool_to_sinks(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        table_name="execution_microstructure",
    )

    assert int(summary["records_flushed"]) == 1
    assert int(summary["quarantined_lines"]) == 1
    assert int(summary["spool_compacted"]) == 1

    bad_entries = [json.loads(line) for line in bad_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    reasons = {str(row.get("reason")) for row in bad_entries}
    assert "trailing_partial_line_stale" in reasons
    assert int(offset_path.read_text(encoding="utf-8").strip()) == 0
    assert int(generation_path.read_text(encoding="utf-8").strip()) >= 1

    with duckdb.connect(str(duckdb_path)) as conn:
        order_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure").fetchone()[0]
    assert int(order_count) == 1


def test_legacy_single_file_parquet_export_is_idempotent_after_cursor_reset(tmp_path: Path) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"
    cursor_path = parquet_path.with_suffix(f"{parquet_path.suffix}.cursor")

    append_execution_microstructure(
        _sample_execute_results(),
        batch_id="20260301-batch-legacy-idempotent-1",
        strategy="ALPHA_SOVEREIGN_V1",
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        spool_path=spool_path,
    )
    drained = wait_for_execution_microstructure_flush(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        timeout_seconds=5.0,
    )
    assert drained is True
    assert int(len(pd.read_parquet(parquet_path))) == 1

    cursor_path.write_text("0\n", encoding="utf-8")
    wrote = microstructure_module._export_duckdb_table_to_parquet(
        duckdb_path=duckdb_path,
        table_name="execution_microstructure",
        parquet_path=parquet_path,
    )

    assert wrote >= 0
    assert int(len(pd.read_parquet(parquet_path))) == 1
    assert int(cursor_path.read_text(encoding="utf-8").strip()) == 1


def test_append_duckdb_table_rows_handles_schema_drift_without_flush_failure(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "execution_microstructure.duckdb"

    with duckdb.connect(str(duckdb_path)) as conn:
        first = pd.DataFrame(
            [
                {
                    "client_order_id": "cid-a",
                    "value": 1.0,
                    "_spool_record_uid": "uid-a",
                }
            ]
        )
        second = pd.DataFrame(
            [
                {
                    "client_order_id": "cid-b",
                    "value": 2.0,
                    "new_metric": 99.0,
                    "_spool_record_uid": "uid-b",
                }
            ]
        )

        wrote_first = microstructure_module._append_duckdb_table_rows(
            conn=conn,
            table="execution_microstructure",
            frame=first,
            register_name="reg_first",
        )
        wrote_second = microstructure_module._append_duckdb_table_rows(
            conn=conn,
            table="execution_microstructure",
            frame=second,
            register_name="reg_second",
        )

        columns = conn.execute("PRAGMA table_info(execution_microstructure)").fetchall()
        col_names = {str(row[1]) for row in columns}
        row_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure").fetchone()[0]

    assert wrote_first == 1
    assert wrote_second == 1
    assert "new_metric" in col_names
    assert int(row_count) == 2


def test_export_duckdb_table_to_parquet_uses_deterministic_append_order(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    parquet_path = tmp_path / "execution_microstructure.parquet"

    with duckdb.connect(str(duckdb_path)) as conn:
        conn.execute(
            """
            CREATE TABLE execution_microstructure AS
            SELECT * FROM (
                VALUES
                    ('uid-c', 'cid-c'),
                    ('uid-a', 'cid-a'),
                    ('uid-b', 'cid-b')
            ) AS t(_spool_record_uid, client_order_id)
            """
        )

    pd.DataFrame(columns=["_spool_record_uid", "client_order_id"]).to_parquet(parquet_path, index=False)
    wrote_first = microstructure_module._export_duckdb_table_to_parquet(
        duckdb_path=duckdb_path,
        table_name="execution_microstructure",
        parquet_path=parquet_path,
        batch_rows=2,
    )
    wrote_second = microstructure_module._export_duckdb_table_to_parquet(
        duckdb_path=duckdb_path,
        table_name="execution_microstructure",
        parquet_path=parquet_path,
        batch_rows=2,
    )

    out = pd.read_parquet(parquet_path)
    assert wrote_first >= 0
    assert wrote_second >= 0
    assert out["_spool_record_uid"].astype(str).tolist() == ["uid-c", "uid-a", "uid-b"]


def test_export_duckdb_table_to_parquet_does_not_skip_rows_when_appends_happen_between_batches(
    tmp_path: Path,
) -> None:
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    parquet_path = tmp_path / "execution_microstructure.parquet"

    with duckdb.connect(str(duckdb_path)) as conn:
        conn.execute(
            """
            CREATE TABLE execution_microstructure AS
            SELECT * FROM (
                VALUES
                    ('uid-a', 'cid-a'),
                    ('uid-b', 'cid-b'),
                    ('uid-c', 'cid-c')
            ) AS t(_spool_record_uid, client_order_id)
            """
        )

    pd.DataFrame(columns=["_spool_record_uid", "client_order_id"]).to_parquet(parquet_path, index=False)
    first_write = microstructure_module._export_duckdb_table_to_parquet(
        duckdb_path=duckdb_path,
        table_name="execution_microstructure",
        parquet_path=parquet_path,
        batch_rows=2,
    )

    with duckdb.connect(str(duckdb_path)) as conn:
        conn.execute(
            """
            INSERT INTO execution_microstructure (_spool_record_uid, client_order_id)
            VALUES ('uid-d', 'cid-d')
            """
        )

    second_write = microstructure_module._export_duckdb_table_to_parquet(
        duckdb_path=duckdb_path,
        table_name="execution_microstructure",
        parquet_path=parquet_path,
        batch_rows=2,
    )

    out = pd.read_parquet(parquet_path)
    exported_uids = out["_spool_record_uid"].astype(str).tolist()
    assert first_write >= 0
    assert second_write >= 0
    assert exported_uids == ["uid-a", "uid-b", "uid-c", "uid-d"]


def test_append_parquet_legacy_file_preserves_rows_without_spool_uid(tmp_path: Path) -> None:
    from execution import microstructure as microstructure_module

    parquet_path = tmp_path / "legacy_without_uid.parquet"
    existing_df = pd.DataFrame(
        [
            {"client_order_id": "cid-legacy-1", "symbol": "AAPL"},
            {"client_order_id": "cid-legacy-2", "symbol": "MSFT"},
        ]
    )
    existing_df.to_parquet(parquet_path, index=False)

    new_rows_df = pd.DataFrame(
        [
            {
                "client_order_id": "cid-new-1",
                "symbol": "NVDA",
                "_spool_record_uid": "uid-new-1",
            }
        ]
    )

    wrote = microstructure_module._append_parquet_legacy_file(parquet_path, new_rows_df)
    merged_df = pd.read_parquet(parquet_path)

    assert wrote == 1
    assert int(len(merged_df)) == 3
    assert set(merged_df["client_order_id"].astype(str)) == {"cid-legacy-1", "cid-legacy-2", "cid-new-1"}


def test_append_parquet_legacy_file_preserves_rows_with_null_record_id(tmp_path: Path) -> None:
    from execution import microstructure as microstructure_module

    parquet_path = tmp_path / "legacy_null_record_id.parquet"
    existing_df = pd.DataFrame(
        [
            {"client_order_id": "cid-legacy-1", "record_id": None, "symbol": "AAPL"},
            {"client_order_id": "cid-legacy-2", "record_id": None, "symbol": "MSFT"},
        ]
    )
    existing_df.to_parquet(parquet_path, index=False)

    new_rows_df = pd.DataFrame(
        [
            {
                "client_order_id": "cid-new-1",
                "record_id": "rec-new-1",
                "symbol": "NVDA",
            }
        ]
    )

    wrote = microstructure_module._append_parquet_legacy_file(parquet_path, new_rows_df)
    merged_df = pd.read_parquet(parquet_path)

    assert wrote == 1
    assert int(len(merged_df)) == 3
    assert set(merged_df["client_order_id"].astype(str)) == {"cid-legacy-1", "cid-legacy-2", "cid-new-1"}


def test_append_parquet_legacy_file_preserves_rows_with_null_uid(tmp_path: Path) -> None:
    from execution import microstructure as microstructure_module

    parquet_path = tmp_path / "legacy_null_uid.parquet"
    existing_df = pd.DataFrame(
        [
            {"client_order_id": "cid-legacy-1", "uid": None, "symbol": "AAPL"},
            {"client_order_id": "cid-legacy-2", "uid": None, "symbol": "MSFT"},
        ]
    )
    existing_df.to_parquet(parquet_path, index=False)

    new_rows_df = pd.DataFrame(
        [
            {
                "client_order_id": "cid-new-1",
                "uid": "uid-new-1",
                "symbol": "NVDA",
            }
        ]
    )

    wrote = microstructure_module._append_parquet_legacy_file(parquet_path, new_rows_df)
    merged_df = pd.read_parquet(parquet_path)

    assert wrote == 1
    assert int(len(merged_df)) == 3
    assert set(merged_df["client_order_id"].astype(str)) == {"cid-legacy-1", "cid-legacy-2", "cid-new-1"}


def test_spool_append_and_atomic_write_paths_call_fsync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"
    offset_path = spool_path.with_suffix(f"{spool_path.suffix}.offset")
    parquet_path = tmp_path / "atomic.parquet"
    fsync_calls: list[int] = []

    monkeypatch.setattr(microstructure_module.os, "fsync", lambda fd: fsync_calls.append(int(fd)))

    appended = microstructure_module._append_spool_records(
        spool_path=spool_path,
        order_rows=[{"client_order_id": "cid-a"}],
        fill_rows=[],
    )
    microstructure_module._write_spool_offset(offset_path, 17)
    microstructure_module._atomic_write_parquet(pd.DataFrame([{"v": 1}]), parquet_path)

    assert appended == 1
    assert int(offset_path.read_text(encoding="utf-8").strip()) == 17
    assert parquet_path.exists()
    assert len(fsync_calls) >= 3


def test_append_post_write_error_buffers_retry_and_prevents_duckdb_duplicates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"

    original_append_prebuilt = microstructure_module._append_prebuilt_spool_records
    state = {"failed_once": False}

    def _raise_after_successful_append(
        *,
        spool_path: Path,
        records: list[dict[str, object]],
        lock_timeout_seconds: float,
    ) -> int:
        wrote = original_append_prebuilt(
            spool_path=spool_path,
            records=records,
            lock_timeout_seconds=lock_timeout_seconds,
        )
        if not state["failed_once"]:
            state["failed_once"] = True
            raise OSError("synthetic post-write append failure")
        return wrote

    monkeypatch.setattr(
        microstructure_module,
        "_append_prebuilt_spool_records",
        _raise_after_successful_append,
    )

    summary = append_execution_microstructure(
        _sample_execute_results(),
        batch_id="20260301-batch-post-write-error-1",
        strategy="ALPHA_SOVEREIGN_V1",
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        spool_path=spool_path,
    )
    assert state["failed_once"] is True
    assert int(summary["spool_records_total"]) == 3
    assert int(summary["spool_records_appended"]) == 0
    assert int(summary["spool_records_buffered"]) == 3
    assert int(summary["spool_records_dropped"]) == 0
    assert int(summary["spool_append_lock_contended"]) == 0
    assert "synthetic post-write append failure" in str(summary.get("spool_append_error"))

    drained = wait_for_execution_microstructure_flush(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        timeout_seconds=5.0,
    )
    assert drained is True

    with duckdb.connect(str(duckdb_path)) as conn:
        order_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure").fetchone()[0]
        fill_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure_fills").fetchone()[0]
    assert int(order_count) == 1
    assert int(fill_count) == 2


def test_flush_recovers_when_stale_offset_exceeds_spool_size(tmp_path: Path) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"
    offset_path = spool_path.with_suffix(f"{spool_path.suffix}.offset")

    order_rows, _ = build_execution_telemetry_rows(
        _sample_execute_results(),
        batch_id="20260301-batch-stale-offset-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )
    spool_path.write_text(f'{json.dumps({"record_type": "order", "row": order_rows[0]})}\n', encoding="utf-8")
    offset_path.write_text("999999\n", encoding="utf-8")

    drained = wait_for_execution_microstructure_flush(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        timeout_seconds=5.0,
    )
    assert drained is True

    with duckdb.connect(str(duckdb_path)) as conn:
        order_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure").fetchone()[0]
    assert int(order_count) == 1


def test_flush_replay_after_partial_failure_does_not_duplicate_duckdb_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"
    expected_offset_path = spool_path.with_suffix(f"{spool_path.suffix}.offset")

    from execution import microstructure as microstructure_module

    original_write_offset = microstructure_module._write_spool_offset
    state = {"failed_once": False}

    def _fail_once_for_spool_offset(offset_path: Path, offset: int) -> None:
        if Path(offset_path) == expected_offset_path and not state["failed_once"]:
            state["failed_once"] = True
            raise RuntimeError("forced offset write failure after duckdb insert")
        original_write_offset(offset_path, offset)

    monkeypatch.setattr("execution.microstructure._write_spool_offset", _fail_once_for_spool_offset)

    append_execution_microstructure(
        _sample_execute_results(),
        batch_id="20260301-batch-replay-dedupe-1",
        strategy="ALPHA_SOVEREIGN_V1",
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        spool_path=spool_path,
    )

    deadline = time.monotonic() + 3.0
    saw_error = False
    while time.monotonic() <= deadline:
        status = get_execution_microstructure_spool_status(
            spool_path=spool_path,
            parquet_path=parquet_path,
            fills_parquet_path=fills_parquet_path,
            duckdb_path=duckdb_path,
        )
        if "forced offset write failure after duckdb insert" in _clean_status_error(status):
            saw_error = True
            break
        time.sleep(0.05)
    assert saw_error is True
    assert state["failed_once"] is True

    monkeypatch.setattr("execution.microstructure._write_spool_offset", original_write_offset)

    drained = wait_for_execution_microstructure_flush(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        timeout_seconds=5.0,
    )
    assert drained is True

    with duckdb.connect(str(duckdb_path)) as conn:
        order_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure").fetchone()[0]
        fill_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure_fills").fetchone()[0]
    assert int(order_count) == 1
    assert int(fill_count) == 2


def test_flush_compacts_spool_after_reaching_eof(tmp_path: Path) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"
    offset_path = spool_path.with_suffix(f"{spool_path.suffix}.offset")

    append_execution_microstructure(
        _sample_execute_results(),
        batch_id="20260301-batch-compaction-1",
        strategy="ALPHA_SOVEREIGN_V1",
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        spool_path=spool_path,
    )

    drained = wait_for_execution_microstructure_flush(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        timeout_seconds=5.0,
    )
    assert drained is True

    assert spool_path.exists()
    assert int(spool_path.stat().st_size) == 0
    assert offset_path.exists()
    assert int(offset_path.read_text(encoding="utf-8").strip()) == 0


def test_append_execution_microstructure_lock_contention_buffers_without_blocking(
    tmp_path: Path,
) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"

    with microstructure_module._acquire_spool_cross_process_lock(
        spool_path=spool_path,
        timeout_seconds=0.100,
    ) as lock_acquired:
        assert lock_acquired is True
        started = time.perf_counter()
        summary = append_execution_microstructure(
            _sample_execute_results(),
            batch_id="20260301-batch-lock-contention-append-1",
            strategy="ALPHA_SOVEREIGN_V1",
            parquet_path=parquet_path,
            fills_parquet_path=fills_parquet_path,
            duckdb_path=duckdb_path,
            spool_path=spool_path,
        )
        elapsed_seconds = time.perf_counter() - started

        assert elapsed_seconds < 0.5
        assert int(summary["spool_records_total"]) == 3
        assert int(summary["spool_records_appended"]) == 0
        assert int(summary["spool_records_buffered"]) == 3
        assert int(summary["spool_records_dropped"]) == 0
        assert int(summary["spool_append_lock_contended"]) == 1

        status = get_execution_microstructure_spool_status(
            spool_path=spool_path,
            parquet_path=parquet_path,
            fills_parquet_path=fills_parquet_path,
            duckdb_path=duckdb_path,
        )
        assert int(status.get("buffered_records_pending", 0)) >= 3
        assert int(status.get("append_lock_contention_count", 0)) >= 1
        assert int(status["pending_bytes"]) > 0

    drained = wait_for_execution_microstructure_flush(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        timeout_seconds=5.0,
    )
    assert drained is True

    status_after = get_execution_microstructure_spool_status(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
    )
    assert int(status_after.get("buffered_records_pending", 0)) == 0

    with duckdb.connect(str(duckdb_path)) as conn:
        order_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure").fetchone()[0]
        fill_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure_fills").fetchone()[0]
    assert int(order_count) == 1
    assert int(fill_count) == 2


def test_append_execution_microstructure_buffer_capacity_overflow_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"

    monkeypatch.setattr(microstructure_module, "SPOOL_BUFFER_MAX_RECORDS", 1)
    monkeypatch.setattr(microstructure_module, "SPOOL_BUFFER_MAX_BYTES", 10_000_000)

    with microstructure_module._acquire_spool_cross_process_lock(
        spool_path=spool_path,
        timeout_seconds=0.100,
    ) as lock_acquired:
        assert lock_acquired is True
        with pytest.raises(RuntimeError, match="telemetry spool retry buffer overflow"):
            append_execution_microstructure(
                _sample_execute_results(),
                batch_id="20260301-batch-buffer-overflow-1",
                strategy="ALPHA_SOVEREIGN_V1",
                parquet_path=parquet_path,
                fills_parquet_path=fills_parquet_path,
                duckdb_path=duckdb_path,
                spool_path=spool_path,
            )

        status = get_execution_microstructure_spool_status(
            spool_path=spool_path,
            parquet_path=parquet_path,
            fills_parquet_path=fills_parquet_path,
            duckdb_path=duckdb_path,
        )
        assert int(status.get("buffered_records_pending", 0)) == 0
        assert int(status.get("buffer_drop_count", 0)) >= 3


def test_append_execution_microstructure_same_payload_is_idempotent_across_append_retries(
    tmp_path: Path,
) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"

    kwargs = {
        "batch_id": "20260301-batch-idempotent-retry-1",
        "strategy": "ALPHA_SOVEREIGN_V1",
        "parquet_path": parquet_path,
        "fills_parquet_path": fills_parquet_path,
        "duckdb_path": duckdb_path,
        "spool_path": spool_path,
    }
    append_execution_microstructure(_sample_execute_results(), **kwargs)
    append_execution_microstructure(_sample_execute_results(), **kwargs)

    drained = wait_for_execution_microstructure_flush(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        timeout_seconds=5.0,
    )
    assert drained is True

    with duckdb.connect(str(duckdb_path)) as conn:
        order_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure").fetchone()[0]
        fill_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure_fills").fetchone()[0]
    assert int(order_count) == 1
    assert int(fill_count) == 2


def test_shutdown_execution_microstructure_spoolers_fails_closed_when_buffered_records_remain(
    tmp_path: Path,
) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"

    with microstructure_module._acquire_spool_cross_process_lock(
        spool_path=spool_path,
        timeout_seconds=0.100,
    ) as lock_acquired:
        assert lock_acquired is True
        summary = append_execution_microstructure(
            _sample_execute_results(),
            batch_id="20260301-batch-shutdown-fail-closed-1",
            strategy="ALPHA_SOVEREIGN_V1",
            parquet_path=parquet_path,
            fills_parquet_path=fills_parquet_path,
            duckdb_path=duckdb_path,
            spool_path=spool_path,
        )
        assert int(summary["spool_records_buffered"]) == 3
        with pytest.raises(RuntimeError, match="telemetry spool shutdown fail-closed"):
            microstructure_module._shutdown_execution_microstructure_spoolers()


def test_flush_spool_returns_fast_when_cross_process_lock_is_contended(tmp_path: Path) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"

    order_rows, _ = build_execution_telemetry_rows(
        _sample_execute_results(),
        batch_id="20260301-batch-lock-contention-flush-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )
    spool_path.write_text(
        f'{json.dumps({"record_type": "order", "row": order_rows[0]})}\n',
        encoding="utf-8",
    )

    with microstructure_module._acquire_spool_cross_process_lock(
        spool_path=spool_path,
        timeout_seconds=0.100,
    ) as lock_acquired:
        assert lock_acquired is True
        started = time.perf_counter()
        summary = microstructure_module._flush_spool_to_sinks(
            spool_path=spool_path,
            parquet_path=parquet_path,
            fills_parquet_path=fills_parquet_path,
            duckdb_path=duckdb_path,
            table_name="execution_microstructure",
        )
        elapsed_seconds = time.perf_counter() - started

    assert elapsed_seconds < 0.5
    assert int(summary["spool_lock_contended"]) == 1
    assert int(summary["records_flushed"]) == 0

    summary_after_release = microstructure_module._flush_spool_to_sinks(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        table_name="execution_microstructure",
    )
    assert int(summary_after_release["spool_lock_contended"]) == 0
    assert int(summary_after_release["records_flushed"]) == 1


def test_flush_invokes_duckdb_wal_checkpoint_management_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parquet_path = tmp_path / "execution_microstructure.parquet"
    fills_parquet_path = tmp_path / "execution_microstructure_fills.parquet"
    duckdb_path = tmp_path / "execution_microstructure.duckdb"
    spool_path = tmp_path / "execution_microstructure_spool.jsonl"
    calls: list[Path] = []

    def _track_duckdb_maintenance(*, duckdb_path: Path) -> dict[str, object]:
        calls.append(Path(duckdb_path))
        return {
            "wal_autocheckpoint_set": 1,
            "checkpoint_attempted": 1,
            "checkpoint_completed": 1,
            "maintenance_error": None,
        }

    monkeypatch.setattr(
        microstructure_module,
        "_manage_duckdb_wal_checkpoint",
        _track_duckdb_maintenance,
    )

    order_rows, _ = build_execution_telemetry_rows(
        _sample_execute_results(),
        batch_id="20260301-batch-duckdb-maintenance-1",
        strategy="ALPHA_SOVEREIGN_V1",
    )
    spool_path.write_text(
        f'{json.dumps({"record_type": "order", "row": order_rows[0]})}\n',
        encoding="utf-8",
    )

    summary = microstructure_module._flush_spool_to_sinks(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        table_name="execution_microstructure",
    )

    assert int(summary["records_flushed"]) == 1
    assert int(summary["wal_autocheckpoint_set"]) == 1
    assert int(summary["duckdb_checkpoint_attempted"]) == 1
    assert int(summary["duckdb_checkpoint_completed"]) == 1
    assert calls == [duckdb_path]

    with duckdb.connect(str(duckdb_path)) as conn:
        order_count = conn.execute("SELECT COUNT(*) FROM execution_microstructure").fetchone()[0]
    assert int(order_count) == 1


def test_wait_for_execution_microstructure_flush_fails_closed_when_last_flush_error_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _StatusSequenceSpooler:
        def __init__(self, statuses: list[dict[str, object]]) -> None:
            self._statuses = statuses
            self._cursor = 0

        def request_flush(self) -> None:
            return None

        def status(self) -> dict[str, object]:
            idx = min(self._cursor, len(self._statuses) - 1)
            value = self._statuses[idx]
            self._cursor += 1
            return value

    statuses = [
        {"pending_bytes": 1, "last_flush_ts_utc": "2026-03-01T16:10:00.000Z", "last_flush_error": None, "buffer_drop_count": 0},
        {"pending_bytes": 0, "last_flush_ts_utc": "2026-03-01T16:10:00.100Z", "last_flush_error": "forced sink error", "buffer_drop_count": 0},
    ]
    stub = _StatusSequenceSpooler(statuses)
    monkeypatch.setattr(microstructure_module, "_get_or_create_spooler", lambda **_kwargs: stub)

    drained = microstructure_module.wait_for_execution_microstructure_flush(
        timeout_seconds=0.2,
        poll_interval_seconds=0.01,
    )
    assert drained is False


def test_wait_for_execution_microstructure_flush_fails_closed_when_buffer_drop_detected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _StatusSequenceSpooler:
        def __init__(self, statuses: list[dict[str, object]]) -> None:
            self._statuses = statuses
            self._cursor = 0

        def request_flush(self) -> None:
            return None

        def status(self) -> dict[str, object]:
            idx = min(self._cursor, len(self._statuses) - 1)
            value = self._statuses[idx]
            self._cursor += 1
            return value

    statuses = [
        {"pending_bytes": 2, "last_flush_ts_utc": "2026-03-01T16:12:00.000Z", "last_flush_error": None, "buffer_drop_count": 0},
        {"pending_bytes": 0, "last_flush_ts_utc": "2026-03-01T16:12:00.100Z", "last_flush_error": None, "buffer_drop_count": 3},
    ]
    stub = _StatusSequenceSpooler(statuses)
    monkeypatch.setattr(microstructure_module, "_get_or_create_spooler", lambda **_kwargs: stub)

    drained = microstructure_module.wait_for_execution_microstructure_flush(
        timeout_seconds=0.2,
        poll_interval_seconds=0.01,
    )
    assert drained is False


def _clean_status_error(status: dict[str, object]) -> str:
    raw = status.get("last_flush_error")
    if raw is None:
        return ""
    return str(raw)
