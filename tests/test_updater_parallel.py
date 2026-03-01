from __future__ import annotations

import os
import time

import pandas as pd

from data import updater


def test_chunk_list_splits_expected_sizes():
    chunks = updater._chunk_list(["A", "B", "C", "D", "E"], chunk_size=2)
    assert chunks == [["A", "B"], ["C", "D"], ["E"]]


def test_parallel_batch_download_deduplicates_ticker_date(monkeypatch):
    def fake_batch_download(tickers_list, start_date, threads=True):
        rows = []
        for t in tickers_list:
            rows.append(
                {
                    "date": pd.Timestamp("2025-01-02"),
                    "ticker": str(t).upper(),
                    "raw_close": 100.0,
                    "adj_close": 101.0,
                    "total_ret": 0.01,
                    "volume": 1_000_000,
                }
            )
        return pd.DataFrame(rows)

    monkeypatch.setattr(updater, "batch_download_yahoo", fake_batch_download)
    out = updater.parallel_batch_download_yahoo(
        tickers_list=["aapl", "AAPL", "msft"],
        start_date="2025-01-01",
        chunk_size=1,
        max_workers=4,
    )
    assert set(out["ticker"].tolist()) == {"AAPL", "MSFT"}
    assert len(out) == 2
    assert out.attrs.get("all_chunks_failed") is False


def test_parallel_batch_download_returns_empty_when_all_chunks_fail(monkeypatch):
    def fail_batch_download(tickers_list, start_date, threads=True):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(updater, "batch_download_yahoo", fail_batch_download)
    out = updater.parallel_batch_download_yahoo(
        tickers_list=["AAPL", "MSFT"],
        start_date="2025-01-01",
        chunk_size=1,
        max_workers=2,
    )
    assert out.empty
    assert out.attrs.get("all_chunks_failed") is True


def test_parallel_batch_download_marks_chunk_failed_on_yf_transport_exception(monkeypatch):
    def fail_yf_download(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(updater.yf, "download", fail_yf_download)

    out = updater.parallel_batch_download_yahoo(
        tickers_list=["AAPL", "MSFT"],
        start_date="2025-01-01",
        chunk_size=1,
        max_workers=2,
    )
    assert out.empty
    assert int(out.attrs.get("failed_chunks", 0)) == 2
    assert int(out.attrs.get("total_chunks", 0)) == 2
    assert out.attrs.get("all_chunks_failed") is True


def test_publish_patch_rows_uses_lock_and_atomic_write(tmp_path, monkeypatch):
    patch_path = tmp_path / "patch.parquet"
    rows = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-03"]),
            "permno": [10001],
            "raw_close": [101.0],
            "adj_close": [101.0],
            "total_ret": [0.01],
            "volume": [1_200_000.0],
        }
    )

    events: list[str] = []

    def fake_acquire(timeout_sec=updater.UPDATE_LOCK_TIMEOUT_SEC):
        events.append("acquire")

    def fake_release(expected_token=None):
        events.append("release")

    def tracking_atomic_write(df, filename, index=False):
        events.append(f"atomic:{filename}")
        df.to_parquet(filename, index=index)

    monkeypatch.setattr(updater, "_acquire_update_lock", fake_acquire)
    monkeypatch.setattr(updater, "_release_update_lock", fake_release)
    monkeypatch.setattr(updater, "atomic_parquet_write", tracking_atomic_write)

    combined, previous_rows = updater.publish_patch_rows(rows, patch_path=str(patch_path))
    assert previous_rows == 0
    assert len(combined) == 1
    assert events == ["acquire", f"atomic:{patch_path}", "release"]


def test_publish_patch_rows_skips_lock_when_already_held(tmp_path, monkeypatch):
    patch_path = tmp_path / "patch.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-03"]),
            "permno": [10001],
            "raw_close": [100.0],
            "adj_close": [100.0],
            "total_ret": [0.0],
            "volume": [1_000_000.0],
        }
    ).to_parquet(patch_path, index=False)

    rows = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-03"]),
            "permno": [10001],
            "raw_close": [102.0],
            "adj_close": [102.0],
            "total_ret": [0.02],
            "volume": [1_400_000.0],
        }
    )

    lock_calls: list[str] = []

    def fake_acquire(timeout_sec=updater.UPDATE_LOCK_TIMEOUT_SEC):
        lock_calls.append("acquire")

    def fake_release(expected_token=None):
        lock_calls.append("release")

    monkeypatch.setattr(updater, "_acquire_update_lock", fake_acquire)
    monkeypatch.setattr(updater, "_release_update_lock", fake_release)

    combined, previous_rows = updater.publish_patch_rows(
        rows,
        patch_path=str(patch_path),
        lock_already_held=True,
    )
    assert previous_rows == 1
    assert lock_calls == []
    assert len(combined) == 1

    written = pd.read_parquet(patch_path)
    assert len(written) == 1
    assert float(written.iloc[0]["adj_close"]) == 102.0


def test_release_update_lock_skips_on_token_mismatch(tmp_path, monkeypatch):
    lock_path = tmp_path / ".update.lock"
    lock_path.write_text("pid=123 ts=1 token=owner-a", encoding="utf-8")
    monkeypatch.setattr(updater, "UPDATE_LOCK_PATH", str(lock_path))

    updater._release_update_lock(expected_token="owner-b")
    assert lock_path.exists()


def test_release_update_lock_noop_without_token(tmp_path, monkeypatch):
    lock_path = tmp_path / ".update.lock"
    lock_path.write_text("pid=123 ts=1 token=owner-a", encoding="utf-8")
    monkeypatch.setattr(updater, "UPDATE_LOCK_PATH", str(lock_path))
    monkeypatch.setattr(updater, "_OWNED_UPDATE_LOCK_TOKEN", None)

    updater._release_update_lock()
    assert lock_path.exists()


def test_acquire_update_lock_recovers_stale_dead_owner_with_pid_probe(tmp_path, monkeypatch):
    lock_path = tmp_path / ".update.lock"
    stale_ts = int(time.time()) - 10_000
    lock_path.write_text(f"pid=4444 ts={stale_ts} token=stale", encoding="utf-8")

    monkeypatch.setattr(updater, "UPDATE_LOCK_PATH", str(lock_path))
    monkeypatch.setattr(updater, "UPDATE_LOCK_STALE_SEC", 60)
    monkeypatch.setattr(updater, "_pid_is_running", lambda _pid: False)

    token = updater._acquire_update_lock(timeout_sec=1)
    assert isinstance(token, str)
    assert token

    payload = lock_path.read_text(encoding="utf-8")
    assert f"token={token}" in payload

    updater._release_update_lock(expected_token=token)
    assert not lock_path.exists()


def test_read_partition_rows_recovers_missing_live_partition_from_backup(tmp_path, monkeypatch):
    patch_root = tmp_path / "patch.parquet"
    lock_path = tmp_path / ".update.lock"
    monkeypatch.setattr(updater, "UPDATE_LOCK_PATH", str(lock_path))
    lock_path.write_text(
        f"pid={os.getpid()} ts={int(time.time())} token=self-owner",
        encoding="utf-8",
    )

    backup_dir = patch_root / "year=2025" / "month=01.bak.crash"
    os.makedirs(backup_dir, exist_ok=True)
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-03"]),
            "permno": [10001],
            "raw_close": [101.0],
            "adj_close": [101.0],
            "total_ret": [0.01],
            "volume": [1_200_000.0],
        }
    ).to_parquet(backup_dir / updater.PATCH_PART_FILE, index=False)

    out = updater._read_partition_rows(str(patch_root), year=2025, month=1)
    live_dir = patch_root / "year=2025" / "month=01"
    assert live_dir.exists()
    assert not backup_dir.exists()
    assert len(out) == 1
    assert float(out.iloc[0]["adj_close"]) == 101.0


def test_publish_patch_rows_migrates_empty_legacy_patch_file(tmp_path, monkeypatch):
    patch_path = tmp_path / "patch.parquet"
    lock_path = tmp_path / ".update.lock"
    monkeypatch.setattr(updater, "UPDATE_LOCK_PATH", str(lock_path))

    pd.DataFrame(columns=updater.PATCH_COLUMNS).to_parquet(patch_path, index=False)
    rows = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-03"]),
            "permno": [10001],
            "raw_close": [102.0],
            "adj_close": [102.0],
            "total_ret": [0.02],
            "volume": [1_300_000.0],
        }
    )

    combined, previous_rows = updater.publish_patch_rows(rows, patch_path=str(patch_path))
    assert previous_rows == 0
    assert patch_path.is_dir()
    assert len(combined) == 1
    assert float(combined.iloc[0]["adj_close"]) == 102.0


def test_run_update_fails_closed_on_partial_chunk_failures(tmp_path, monkeypatch):
    prices_path = tmp_path / "prices.parquet"
    tickers_path = tmp_path / "tickers.parquet"
    patch_path = tmp_path / "patch.parquet"
    macro_path = tmp_path / "macro.parquet"
    lock_path = tmp_path / ".update.lock"

    prices = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-02", "2025-01-02"]),
            "permno": [10001, 84398],
            "raw_close": [100.0, 500.0],
            "adj_close": [100.0, 500.0],
            "total_ret": [0.0, 0.0],
            "volume": [1_000_000.0, 2_000_000.0],
        }
    )
    prices.to_parquet(prices_path, index=False)
    tickers = pd.DataFrame({"permno": [10001, 84398], "ticker": ["AAPL", "SPY"]})
    tickers.to_parquet(tickers_path, index=False)

    monkeypatch.setattr(updater, "PRICES_PATH", str(prices_path))
    monkeypatch.setattr(updater, "TICKERS_PATH", str(tickers_path))
    monkeypatch.setattr(updater, "PATCH_PATH", str(patch_path))
    monkeypatch.setattr(updater, "MACRO_PATH", str(macro_path))
    monkeypatch.setattr(updater, "UPDATE_LOCK_PATH", str(lock_path))
    monkeypatch.setattr(updater, "get_top_liquid_tickers", lambda n=50: ["AAPL"])

    def fake_parallel_download(tickers_list, start_date, chunk_size=64, max_workers=8):
        out = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-03", "2025-01-03"]),
                "ticker": ["AAPL", "SPY"],
                "raw_close": [101.0, 501.0],
                "adj_close": [101.0, 501.0],
                "total_ret": [0.01, 0.002],
                "volume": [1_200_000.0, 2_200_000.0],
            }
        )
        out.attrs["all_chunks_failed"] = False
        out.attrs["failed_chunks"] = 1
        out.attrs["total_chunks"] = 2
        return out

    monkeypatch.setattr(updater, "parallel_batch_download_yahoo", fake_parallel_download)

    events: list[str] = []

    def tracking_atomic_write(df, filename, index=False):
        events.append(f"atomic:{filename}")
        df.to_parquet(filename, index=index)

    def tracking_publish_patch_rows(*args, **kwargs):
        events.append("publish")
        return pd.DataFrame(), 0

    monkeypatch.setattr(updater, "atomic_parquet_write", tracking_atomic_write)
    monkeypatch.setattr(updater, "publish_patch_rows", tracking_publish_patch_rows)

    result = updater.run_update(scope="Top 50")
    assert result["success"] is False
    assert result.get("tickers_updated", 0) == 0
    assert "publish" not in events
    assert not patch_path.exists()


def test_run_update_fails_closed_when_all_chunks_fail(tmp_path, monkeypatch):
    prices_path = tmp_path / "prices.parquet"
    tickers_path = tmp_path / "tickers.parquet"
    patch_path = tmp_path / "patch.parquet"
    macro_path = tmp_path / "macro.parquet"
    lock_path = tmp_path / ".update.lock"

    prices = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-02", "2025-01-02"]),
            "permno": [10001, 84398],
            "raw_close": [100.0, 500.0],
            "adj_close": [100.0, 500.0],
            "total_ret": [0.0, 0.0],
            "volume": [1_000_000.0, 2_000_000.0],
        }
    )
    prices.to_parquet(prices_path, index=False)
    tickers = pd.DataFrame({"permno": [10001, 84398], "ticker": ["AAPL", "SPY"]})
    tickers.to_parquet(tickers_path, index=False)

    monkeypatch.setattr(updater, "PRICES_PATH", str(prices_path))
    monkeypatch.setattr(updater, "TICKERS_PATH", str(tickers_path))
    monkeypatch.setattr(updater, "PATCH_PATH", str(patch_path))
    monkeypatch.setattr(updater, "MACRO_PATH", str(macro_path))
    monkeypatch.setattr(updater, "UPDATE_LOCK_PATH", str(lock_path))
    monkeypatch.setattr(updater, "get_top_liquid_tickers", lambda n=50: ["AAPL"])

    def fake_parallel_download(tickers_list, start_date, chunk_size=64, max_workers=8):
        out = pd.DataFrame()
        out.attrs["all_chunks_failed"] = True
        out.attrs["failed_chunks"] = 2
        out.attrs["total_chunks"] = 2
        return out

    monkeypatch.setattr(updater, "parallel_batch_download_yahoo", fake_parallel_download)

    events: list[str] = []

    def tracking_atomic_write(df, filename, index=False):
        events.append(f"atomic:{filename}")
        df.to_parquet(filename, index=index)

    def tracking_publish_patch_rows(*args, **kwargs):
        events.append("publish")
        return pd.DataFrame(), 0

    monkeypatch.setattr(updater, "atomic_parquet_write", tracking_atomic_write)
    monkeypatch.setattr(updater, "publish_patch_rows", tracking_publish_patch_rows)

    result = updater.run_update(scope="Top 50")
    assert result["success"] is False
    assert result.get("tickers_updated", 0) == 0
    assert "publish" not in events
    assert not patch_path.exists()


def test_run_update_commits_ticker_map_before_patch(tmp_path, monkeypatch):
    prices_path = tmp_path / "prices.parquet"
    tickers_path = tmp_path / "tickers.parquet"
    patch_path = tmp_path / "patch.parquet"
    macro_path = tmp_path / "macro.parquet"
    lock_path = tmp_path / ".update.lock"

    prices = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-02", "2025-01-02"]),
            "permno": [10001, 84398],
            "raw_close": [100.0, 500.0],
            "adj_close": [100.0, 500.0],
            "total_ret": [0.0, 0.0],
            "volume": [1_000_000.0, 2_000_000.0],
        }
    )
    prices.to_parquet(prices_path, index=False)
    tickers = pd.DataFrame({"permno": [10001, 84398], "ticker": ["AAPL", "SPY"]})
    tickers.to_parquet(tickers_path, index=False)

    monkeypatch.setattr(updater, "PRICES_PATH", str(prices_path))
    monkeypatch.setattr(updater, "TICKERS_PATH", str(tickers_path))
    monkeypatch.setattr(updater, "PATCH_PATH", str(patch_path))
    monkeypatch.setattr(updater, "MACRO_PATH", str(macro_path))
    monkeypatch.setattr(updater, "UPDATE_LOCK_PATH", str(lock_path))
    monkeypatch.setattr(updater, "get_top_liquid_tickers", lambda n=50: ["AAPL"])

    def fake_parallel_download(tickers_list, start_date, chunk_size=64, max_workers=8):
        return pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-03", "2025-01-03"]),
                "ticker": ["AAPL", "SPY"],
                "raw_close": [101.0, 501.0],
                "adj_close": [101.0, 501.0],
                "total_ret": [0.01, 0.002],
                "volume": [1_200_000.0, 2_200_000.0],
            }
        )

    monkeypatch.setattr(updater, "parallel_batch_download_yahoo", fake_parallel_download)

    events: list[str] = []
    original_atomic_write = updater.atomic_parquet_write
    original_publish_patch_rows = updater.publish_patch_rows

    def tracking_atomic_write(df, filename, index=False):
        events.append(str(filename))
        return original_atomic_write(df, filename, index=index)

    def tracking_publish_patch_rows(patch_rows, **kwargs):
        events.append("publish_patch_rows")
        return original_publish_patch_rows(patch_rows, **kwargs)

    monkeypatch.setattr(updater, "atomic_parquet_write", tracking_atomic_write)
    monkeypatch.setattr(updater, "publish_patch_rows", tracking_publish_patch_rows)

    result = updater.run_update(scope="Top 50")
    assert result["success"] is True
    assert "publish_patch_rows" in events
    assert str(tickers_path) in events
    assert str(patch_path) in events
    assert events.index(str(tickers_path)) < events.index("publish_patch_rows")
    assert events.index("publish_patch_rows") < events.index(str(patch_path))
