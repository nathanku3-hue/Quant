from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from data import fundamentals_updater


def _make_quarter_row(ticker: str, permno: int, release_date: str) -> pd.DataFrame:
    ts = pd.Timestamp(release_date)
    return pd.DataFrame(
        {
            "permno": [permno],
            "ticker": [ticker],
            "fiscal_period_end": [ts - pd.Timedelta(days=45)],
            "release_date": [ts],
            "filing_date": [ts],
            "published_at": [ts],
            "ingested_at": [pd.Timestamp("2026-01-01")],
            "roic": [0.12],
            "revenue_growth_yoy": [0.08],
            "quality_pass_mvq": [True],
            "source": ["unit-test"],
        }
    )


def _configure_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    tickers_path = processed_dir / "tickers.parquet"
    fundamentals_path = processed_dir / "fundamentals.parquet"
    snapshot_path = processed_dir / "fundamentals_snapshot.parquet"
    checkpoint_meta_path = processed_dir / "fundamentals_ingest.checkpoint.json"
    checkpoint_rows_path = processed_dir / "fundamentals_ingest.partial.parquet"

    pd.DataFrame(
        {
            "ticker": ["AAPL", "MSFT", "GOOG"],
            "permno": [10001, 10002, 10003],
        }
    ).to_parquet(tickers_path, index=False)

    monkeypatch.setattr(fundamentals_updater, "PROCESSED_DIR", str(processed_dir))
    monkeypatch.setattr(fundamentals_updater, "TICKERS_PATH", str(tickers_path))
    monkeypatch.setattr(fundamentals_updater, "FUNDAMENTALS_PATH", str(fundamentals_path))
    monkeypatch.setattr(fundamentals_updater, "FUNDAMENTALS_SNAPSHOT_PATH", str(snapshot_path))
    monkeypatch.setattr(
        fundamentals_updater,
        "FUNDAMENTALS_INGEST_CHECKPOINT_META_PATH",
        str(checkpoint_meta_path),
    )
    monkeypatch.setattr(
        fundamentals_updater,
        "FUNDAMENTALS_INGEST_CHECKPOINT_ROWS_PATH",
        str(checkpoint_rows_path),
    )

    monkeypatch.setattr(fundamentals_updater, "_phase17_writer_gate", lambda: (True, None))
    monkeypatch.setattr(fundamentals_updater.updater, "_acquire_update_lock", lambda: "test-token")
    monkeypatch.setattr(fundamentals_updater.updater, "_release_update_lock", lambda expected_token=None: None)

    return {
        "processed_dir": processed_dir,
        "tickers_path": tickers_path,
        "fundamentals_path": fundamentals_path,
        "snapshot_path": snapshot_path,
        "checkpoint_meta_path": checkpoint_meta_path,
        "checkpoint_rows_path": checkpoint_rows_path,
    }


def test_checkpoint_resume_uses_frozen_targets_and_partial_rows(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    paths["checkpoint_rows_path"].parent.mkdir(parents=True, exist_ok=True)
    _make_quarter_row("AAPL", 10001, "2025-03-01").to_parquet(paths["checkpoint_rows_path"], index=False)
    paths["checkpoint_meta_path"].write_text(
        json.dumps(
            {
                "version": 1,
                "scope": "Custom",
                "custom_list": "AAPL,MSFT",
                "targets": ["AAPL", "MSFT"],
                "processed_tickers": ["AAPL"],
                "tickers_with_data": 1,
                "rows_in_partial": 1,
                "stage": "fetch",
                "created_at": "2026-02-01T00:00:00",
                "updated_at": "2026-02-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )

    fetch_calls: list[str] = []

    def fake_extract(ticker: str, permno: int) -> pd.DataFrame:
        fetch_calls.append(ticker)
        return _make_quarter_row(ticker, permno, "2025-06-01")

    monkeypatch.setattr(fundamentals_updater, "_extract_ticker_fundamentals", fake_extract)

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL,MSFT",
        checkpoint_enabled=True,
    )
    assert result["success"] is True
    assert fetch_calls == ["MSFT"]

    written = pd.read_parquet(paths["fundamentals_path"])
    assert set(written["ticker"].astype(str)) == {"AAPL", "MSFT"}
    assert not paths["checkpoint_meta_path"].exists()
    assert not paths["checkpoint_rows_path"].exists()


def test_checkpoint_init_removes_orphan_partial_rows(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    _make_quarter_row("MSFT", 10002, "2025-03-01").to_parquet(paths["checkpoint_rows_path"], index=False)
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: _make_quarter_row(ticker, permno, "2025-06-01"),
    )

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL",
        checkpoint_enabled=True,
    )
    assert result["success"] is True

    written = pd.read_parquet(paths["fundamentals_path"])
    assert set(written["ticker"].astype(str)) == {"AAPL"}


@pytest.mark.parametrize(
    ("checkpoint_keep", "checkpoint_exists_after_success"),
    [
        (False, False),
        (True, True),
    ],
)
def test_checkpoint_success_cleanup_policy(tmp_path, monkeypatch, checkpoint_keep, checkpoint_exists_after_success):
    paths = _configure_paths(tmp_path, monkeypatch)
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: _make_quarter_row(ticker, permno, "2025-03-01"),
    )

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL",
        checkpoint_enabled=True,
        checkpoint_keep=checkpoint_keep,
    )
    assert result["success"] is True
    assert paths["checkpoint_meta_path"].exists() is checkpoint_exists_after_success
    assert paths["checkpoint_rows_path"].exists() is checkpoint_exists_after_success

    if checkpoint_exists_after_success:
        payload = json.loads(paths["checkpoint_meta_path"].read_text(encoding="utf-8"))
        assert payload["stage"] == fundamentals_updater.CHECKPOINT_STAGE_DONE
        assert payload["processed_tickers"] == ["AAPL"]


def test_checkpoint_target_mismatch_fails_by_default(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    paths["checkpoint_meta_path"].write_text(
        json.dumps(
            {
                "version": 1,
                "scope": "Custom",
                "custom_list": "AAPL,MSFT",
                "targets": ["AAPL", "MSFT"],
                "processed_tickers": [],
                "tickers_with_data": 0,
                "rows_in_partial": 0,
                "stage": "fetch",
                "created_at": "2026-02-01T00:00:00",
                "updated_at": "2026-02-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )

    fetch_calls: list[str] = []
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: fetch_calls.append(ticker) or _make_quarter_row(ticker, permno, "2025-03-01"),
    )

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL,GOOG",
        checkpoint_enabled=True,
    )
    assert result["success"] is False
    assert fetch_calls == []
    assert any("Checkpoint mismatch" in line for line in result["log"])
    assert paths["checkpoint_meta_path"].exists()


def test_checkpoint_fetch_stage_with_processed_tickers_but_no_rows_fails(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    paths["checkpoint_meta_path"].write_text(
        json.dumps(
            {
                "version": 1,
                "scope": "Custom",
                "custom_list": "AAPL,MSFT",
                "targets": ["AAPL", "MSFT"],
                "processed_tickers": ["AAPL"],
                "tickers_with_data": 1,
                "rows_in_partial": 1,
                "stage": "fetch",
                "created_at": "2026-02-01T00:00:00",
                "updated_at": "2026-02-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )

    fetch_calls: list[str] = []
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: fetch_calls.append(ticker) or _make_quarter_row(ticker, permno, "2025-03-01"),
    )

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL,MSFT",
        checkpoint_enabled=True,
    )
    assert result["success"] is False
    assert fetch_calls == []
    assert any("processed_tickers but checkpoint rows are missing/empty" in line for line in result["log"])


def test_run_update_default_path_remains_checkpoint_free(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: _make_quarter_row(ticker, permno, "2025-03-01"),
    )

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL",
    )
    assert result["success"] is True
    assert not paths["checkpoint_meta_path"].exists()
    assert not paths["checkpoint_rows_path"].exists()


def test_checkpoint_target_mismatch_reset_restarts(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    paths["checkpoint_meta_path"].write_text(
        json.dumps(
            {
                "version": 1,
                "scope": "Custom",
                "custom_list": "AAPL,MSFT",
                "targets": ["AAPL", "MSFT"],
                "processed_tickers": ["AAPL"],
                "tickers_with_data": 1,
                "rows_in_partial": 1,
                "stage": "fetch",
                "created_at": "2026-02-01T00:00:00",
                "updated_at": "2026-02-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )
    _make_quarter_row("AAPL", 10001, "2025-03-01").to_parquet(paths["checkpoint_rows_path"], index=False)

    fetch_calls: list[str] = []

    def fake_extract(ticker: str, permno: int) -> pd.DataFrame:
        fetch_calls.append(ticker)
        return _make_quarter_row(ticker, permno, "2025-06-01")

    monkeypatch.setattr(fundamentals_updater, "_extract_ticker_fundamentals", fake_extract)

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL,GOOG",
        checkpoint_enabled=True,
        checkpoint_mismatch_policy=fundamentals_updater.CHECKPOINT_MISMATCH_RESET,
    )
    assert result["success"] is True
    assert fetch_calls == ["AAPL", "GOOG"]
    written = pd.read_parquet(paths["fundamentals_path"])
    assert set(written["ticker"].astype(str)) == {"AAPL", "GOOG"}


def test_checkpoint_corrupt_rows_reset_policy_recovers(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    paths["checkpoint_meta_path"].write_text(
        json.dumps(
            {
                "version": 1,
                "scope": "Custom",
                "custom_list": "AAPL",
                "targets": ["AAPL"],
                "processed_tickers": [],
                "tickers_with_data": 0,
                "rows_in_partial": 0,
                "stage": "fetch",
                "created_at": "2026-02-01T00:00:00",
                "updated_at": "2026-02-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )
    paths["checkpoint_rows_path"].write_bytes(b"not-a-parquet")
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: _make_quarter_row(ticker, permno, "2025-03-01"),
    )

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL",
        checkpoint_enabled=True,
        checkpoint_mismatch_policy=fundamentals_updater.CHECKPOINT_MISMATCH_RESET,
    )
    assert result["success"] is True
    written = pd.read_parquet(paths["fundamentals_path"])
    assert set(written["ticker"].astype(str)) == {"AAPL"}


def test_checkpoint_persists_final_write_stage_on_failure(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: _make_quarter_row(ticker, permno, "2025-03-01"),
    )

    def fail_snapshot(_df: pd.DataFrame, _status: dict) -> int:
        raise RuntimeError("snapshot failure for checkpoint test")

    monkeypatch.setattr(fundamentals_updater, "_save_scanner_snapshot", fail_snapshot)

    with pytest.raises(RuntimeError, match="snapshot failure for checkpoint test"):
        fundamentals_updater.run_update(
            scope="Custom",
            custom_list="AAPL",
            checkpoint_enabled=True,
        )

    assert paths["checkpoint_meta_path"].exists()
    assert paths["checkpoint_rows_path"].exists()
    payload = json.loads(paths["checkpoint_meta_path"].read_text(encoding="utf-8"))
    assert payload["stage"] == fundamentals_updater.CHECKPOINT_STAGE_FINAL_WRITE
    assert payload["processed_tickers"] == ["AAPL"]
    checkpoint_rows = pd.read_parquet(paths["checkpoint_rows_path"])
    assert set(checkpoint_rows["ticker"].astype(str)) == {"AAPL"}


def test_checkpoint_final_write_resume_preserves_frozen_permno_map(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    _make_quarter_row("AAPL", 10001, "2025-03-01").to_parquet(paths["checkpoint_rows_path"], index=False)
    paths["checkpoint_meta_path"].write_text(
        json.dumps(
            {
                "version": 1,
                "scope": "Custom",
                "custom_list": "AAPL",
                "targets": ["AAPL"],
                "processed_tickers": ["AAPL"],
                "permno_map": {"AAPL": 10001},
                "tickers_with_data": 1,
                "rows_in_partial": 1,
                "stage": "final_write",
                "created_at": "2026-02-01T00:00:00",
                "updated_at": "2026-02-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame({"ticker": ["AAPL"], "permno": [999999]}).to_parquet(paths["tickers_path"], index=False)
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: (_ for _ in ()).throw(AssertionError("fetch stage should be skipped")),
    )

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL",
        checkpoint_enabled=True,
    )
    assert result["success"] is True
    written = pd.read_parquet(paths["fundamentals_path"])
    assert set(pd.to_numeric(written["permno"], errors="coerce").dropna().astype(int)) == {10001}

    ticker_map = pd.read_parquet(paths["tickers_path"])
    aapl_permno = int(ticker_map.loc[ticker_map["ticker"].astype(str) == "AAPL", "permno"].iloc[0])
    assert aapl_permno == 10001


def test_checkpoint_corrupt_metadata_fails_by_default(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    paths["checkpoint_meta_path"].write_text("{not-json", encoding="utf-8")

    fetch_calls: list[str] = []
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: fetch_calls.append(ticker) or _make_quarter_row(ticker, permno, "2025-03-01"),
    )

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL",
        checkpoint_enabled=True,
    )
    assert result["success"] is False
    assert fetch_calls == []
    assert any("Checkpoint mismatch" in line for line in result["log"])
    assert paths["checkpoint_meta_path"].exists()


def test_checkpoint_corrupt_metadata_reset_policy_recovers(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    paths["checkpoint_meta_path"].write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: _make_quarter_row(ticker, permno, "2025-03-01"),
    )

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL",
        checkpoint_enabled=True,
        checkpoint_mismatch_policy=fundamentals_updater.CHECKPOINT_MISMATCH_RESET,
    )
    assert result["success"] is True
    written = pd.read_parquet(paths["fundamentals_path"])
    assert set(written["ticker"].astype(str)) == {"AAPL"}


def test_checkpoint_semantic_metadata_corruption_fails_by_default(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    paths["checkpoint_meta_path"].write_text(
        json.dumps(
            {
                "version": 1,
                "scope": "Custom",
                "custom_list": "AAPL",
                "targets": ["AAPL"],
                "processed_tickers": [],
                "permno_map": {"AAPL": 10001},
                "tickers_with_data": 0,
                "rows_in_partial": "bad-int",
                "stage": "fetch",
                "created_at": "2026-02-01T00:00:00",
                "updated_at": "2026-02-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )
    fetch_calls: list[str] = []
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: fetch_calls.append(ticker) or _make_quarter_row(ticker, permno, "2025-03-01"),
    )

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL",
        checkpoint_enabled=True,
    )
    assert result["success"] is False
    assert fetch_calls == []
    assert any("Checkpoint mismatch" in line for line in result["log"])


def test_checkpoint_final_write_with_invalid_permno_fails_by_default(tmp_path, monkeypatch):
    paths = _configure_paths(tmp_path, monkeypatch)
    bad_rows = _make_quarter_row("AAPL", 10001, "2025-03-01")
    bad_rows["permno"] = pd.Series([pd.NA], dtype="Int64")
    bad_rows.to_parquet(paths["checkpoint_rows_path"], index=False)
    paths["checkpoint_meta_path"].write_text(
        json.dumps(
            {
                "version": 1,
                "scope": "Custom",
                "custom_list": "AAPL",
                "targets": ["AAPL"],
                "processed_tickers": ["AAPL"],
                "permno_map": {"AAPL": 10001},
                "tickers_with_data": 1,
                "rows_in_partial": 1,
                "stage": "final_write",
                "created_at": "2026-02-01T00:00:00",
                "updated_at": "2026-02-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        fundamentals_updater,
        "_extract_ticker_fundamentals",
        lambda ticker, permno: (_ for _ in ()).throw(AssertionError("fetch stage should be skipped")),
    )

    result = fundamentals_updater.run_update(
        scope="Custom",
        custom_list="AAPL",
        checkpoint_enabled=True,
    )
    assert result["success"] is False
    assert any("Checkpoint mismatch" in line for line in result["log"])
    assert not paths["fundamentals_path"].exists()
