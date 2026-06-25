"""
Contract tests for Phase 33A Step 1: Baseline Identity

Validates:
1. Deterministic ID generation (same content → same ID)
2. Immutability (frozen dataclass, content-derived ID)
3. Split storage (metadata.json + expected_allocation.parquet)
4. Atomic writes (no partial writes)
5. Integrity checks (ID matches content)
"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.baseline_registry import BacktestBaseline, BaselineRegistry


@pytest.fixture
def temp_registry(tmp_path):
    """Create temporary baseline registry for testing."""
    registry_dir = tmp_path / "test_baselines"
    registry = BaselineRegistry(baselines_dir=registry_dir)
    yield registry
    # Cleanup
    if registry_dir.exists():
        shutil.rmtree(registry_dir)


@pytest.fixture
def sample_baseline():
    """Create sample baseline for testing."""
    config = {
        "momentum_lookback": 20,
        "entry_threshold": 0.5,
        "exit_threshold": -0.3,
    }
    config_hash = BacktestBaseline.compute_config_hash(config)
    data_hash = "abc123def456"  # Mock data snapshot hash
    calendar = "NYSE_2026"
    version = "1.0.0"

    baseline_id = BacktestBaseline.compute_baseline_id(
        config_hash, data_hash, calendar, version
    )

    # Create sample allocation DataFrame
    dates = pd.date_range("2025-01-01", periods=10, freq="D")
    tickers = [14593, 14551, 14543]  # AAPL, MSFT, GOOGL permnos
    allocation = pd.DataFrame(
        np.random.rand(10, 3) * 0.3,  # Random weights summing to ~0.9
        index=dates,
        columns=tickers,
    )

    rebalance_schedule = [dates[0], dates[5], dates[9]]

    return BacktestBaseline(
        baseline_id=baseline_id,
        strategy_name="momentum_quality",
        strategy_version=version,
        config_hash=config_hash,
        data_snapshot_hash=data_hash,
        calendar_version=calendar,
        execution_timestamp=datetime(2026, 3, 3, 10, 30, 0),
        run_environment="dev",
        expected_allocation=allocation,
        rebalance_schedule=rebalance_schedule,
        full_config=config,
    )


def test_baseline_identity_deterministic():
    """
    Contract: Same content produces same baseline_id across multiple calls.

    Critical: Timestamp is NOT in hash (excluded for determinism).
    """
    config = {"momentum_lookback": 20, "entry_threshold": 0.5}
    config_hash = BacktestBaseline.compute_config_hash(config)
    data_hash = "test_data_v1"
    calendar = "NYSE_2026"
    version = "1.0.0"

    # Generate ID multiple times with same inputs
    id1 = BacktestBaseline.compute_baseline_id(config_hash, data_hash, calendar, version)
    id2 = BacktestBaseline.compute_baseline_id(config_hash, data_hash, calendar, version)
    id3 = BacktestBaseline.compute_baseline_id(config_hash, data_hash, calendar, version)

    assert id1 == id2 == id3, "Baseline ID must be deterministic"
    assert len(id1) == 16, "Baseline ID should be 16-char hex string"


def test_baseline_id_excludes_timestamp():
    """
    Contract: Timestamp change does NOT affect baseline_id.

    Critical: Ensures re-runs with same config produce same ID.
    """
    config = {"entry": 0.5}
    config_hash = BacktestBaseline.compute_config_hash(config)
    data_hash = "data_v1"
    calendar = "NYSE_2026"
    version = "1.0.0"

    dates = pd.date_range("2025-01-01", periods=5, freq="D")
    allocation = pd.DataFrame(np.random.rand(5, 2), index=dates, columns=[14593, 14551])

    # Create two baselines with different timestamps but identical content
    baseline_t1 = BacktestBaseline(
        baseline_id=BacktestBaseline.compute_baseline_id(config_hash, data_hash, calendar, version),
        strategy_name="test_strategy",
        strategy_version=version,
        config_hash=config_hash,
        data_snapshot_hash=data_hash,
        calendar_version=calendar,
        execution_timestamp=datetime(2026, 3, 1, 10, 0, 0),  # Different timestamp
        run_environment="dev",
        expected_allocation=allocation,
        rebalance_schedule=[dates[0]],
        full_config=config,
    )

    baseline_t2 = BacktestBaseline(
        baseline_id=BacktestBaseline.compute_baseline_id(config_hash, data_hash, calendar, version),
        strategy_name="test_strategy",
        strategy_version=version,
        config_hash=config_hash,
        data_snapshot_hash=data_hash,
        calendar_version=calendar,
        execution_timestamp=datetime(2026, 3, 3, 15, 30, 0),  # Different timestamp
        run_environment="dev",
        expected_allocation=allocation,
        rebalance_schedule=[dates[0]],
        full_config=config,
    )

    # Baseline IDs must be identical despite different timestamps
    assert baseline_t1.baseline_id == baseline_t2.baseline_id, \
        "Baseline ID must NOT include timestamp (determinism requirement)"


def test_baseline_id_changes_with_config():
    """
    Contract: Different config produces different baseline_id.
    """
    config1 = {"entry": 0.5, "exit": -0.3}
    config2 = {"entry": 0.6, "exit": -0.3}  # Different entry threshold

    hash1 = BacktestBaseline.compute_config_hash(config1)
    hash2 = BacktestBaseline.compute_config_hash(config2)

    id1 = BacktestBaseline.compute_baseline_id(hash1, "data_v1", "NYSE_2026", "1.0.0")
    id2 = BacktestBaseline.compute_baseline_id(hash2, "data_v1", "NYSE_2026", "1.0.0")

    assert id1 != id2, "Different config must produce different baseline_id"


def test_baseline_id_changes_with_data_snapshot():
    """
    Contract: Different data snapshot produces different baseline_id.
    """
    config = {"entry": 0.5}
    config_hash = BacktestBaseline.compute_config_hash(config)

    id1 = BacktestBaseline.compute_baseline_id(config_hash, "data_v1", "NYSE_2026", "1.0.0")
    id2 = BacktestBaseline.compute_baseline_id(config_hash, "data_v2", "NYSE_2026", "1.0.0")

    assert id1 != id2, "Different data snapshot must produce different baseline_id"


def test_config_hash_deterministic():
    """
    Contract: Config hash is deterministic (sorted keys).
    """
    config1 = {"b": 2, "a": 1, "c": 3}
    config2 = {"a": 1, "c": 3, "b": 2}  # Same content, different order

    hash1 = BacktestBaseline.compute_config_hash(config1)
    hash2 = BacktestBaseline.compute_config_hash(config2)

    assert hash1 == hash2, "Config hash must be deterministic (key order independent)"


def test_split_storage_save_load(temp_registry, sample_baseline):
    """
    Contract: Split storage preserves all baseline data.

    Validates:
    - metadata.json created with correct fields
    - expected_allocation.parquet preserves float64 precision
    - Round-trip save/load produces identical baseline
    """
    # Save baseline
    temp_registry.save_baseline(sample_baseline)

    # Verify split storage exists
    baseline_dir = temp_registry.baselines_dir / sample_baseline.baseline_id
    assert baseline_dir.exists(), "Baseline directory should exist"

    metadata_path = baseline_dir / "metadata.json"
    allocation_path = baseline_dir / "expected_allocation.parquet"
    assert metadata_path.exists(), "metadata.json should exist"
    assert allocation_path.exists(), "expected_allocation.parquet should exist"

    # Verify metadata structure
    metadata = json.loads(metadata_path.read_text())
    assert metadata["baseline_id"] == sample_baseline.baseline_id
    assert metadata["strategy_name"] == sample_baseline.strategy_name
    assert metadata["config_hash"] == sample_baseline.config_hash
    assert "rebalance_schedule" in metadata
    assert "full_config" in metadata

    # Load baseline
    loaded = temp_registry.load_baseline(sample_baseline.baseline_id)

    # Verify identity fields match
    assert loaded.baseline_id == sample_baseline.baseline_id
    assert loaded.strategy_name == sample_baseline.strategy_name
    assert loaded.config_hash == sample_baseline.config_hash
    assert loaded.data_snapshot_hash == sample_baseline.data_snapshot_hash

    # Verify allocation DataFrame preserved (float64 precision)
    # Note: Parquet may not preserve DatetimeIndex.freq, so check_freq=False
    pd.testing.assert_frame_equal(
        loaded.expected_allocation,
        sample_baseline.expected_allocation,
        check_freq=False
    )

    # Verify rebalance schedule preserved
    assert loaded.rebalance_schedule == sample_baseline.rebalance_schedule

    # Verify config preserved
    assert loaded.full_config == sample_baseline.full_config


def test_atomic_write_no_partial_files(temp_registry, sample_baseline):
    """
    Contract: Atomic writes prevent partial baseline artifacts.

    Validates: .tmp files are cleaned up after successful write.
    """
    temp_registry.save_baseline(sample_baseline)

    baseline_dir = temp_registry.baselines_dir / sample_baseline.baseline_id

    # Verify no .tmp files remain
    tmp_files = list(baseline_dir.glob("*.tmp"))
    assert len(tmp_files) == 0, "No .tmp files should remain after successful write"


def test_integrity_check_on_save(temp_registry):
    """
    Contract: save_baseline() rejects baselines with mismatched baseline_id.
    """
    config = {"entry": 0.5}
    config_hash = BacktestBaseline.compute_config_hash(config)
    correct_id = BacktestBaseline.compute_baseline_id(config_hash, "data_v1", "NYSE_2026", "1.0.0")

    dates = pd.date_range("2025-01-01", periods=5, freq="D")
    allocation = pd.DataFrame(np.random.rand(5, 2), index=dates, columns=[14593, 14551])

    # Create baseline with WRONG baseline_id
    bad_baseline = BacktestBaseline(
        baseline_id="wrong_id_12345",  # Manually set wrong ID
        strategy_name="test",
        strategy_version="1.0.0",
        config_hash=config_hash,
        data_snapshot_hash="data_v1",
        calendar_version="NYSE_2026",
        execution_timestamp=datetime.now(),
        run_environment="dev",
        expected_allocation=allocation,
        rebalance_schedule=[dates[0]],
        full_config=config,
    )

    # Should raise ValueError due to ID mismatch
    with pytest.raises(ValueError, match="Baseline ID mismatch"):
        temp_registry.save_baseline(bad_baseline)


def test_integrity_check_on_load(temp_registry, sample_baseline):
    """
    Contract: load_baseline() validates ID matches content hashes.
    """
    # Save valid baseline
    temp_registry.save_baseline(sample_baseline)

    # Corrupt metadata.json by changing config_hash
    baseline_dir = temp_registry.baselines_dir / sample_baseline.baseline_id
    metadata_path = baseline_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["config_hash"] = "corrupted_hash_abc123"  # Corrupt hash
    metadata_path.write_text(json.dumps(metadata, indent=2))

    # Load should fail integrity check
    with pytest.raises(ValueError, match="integrity check failed"):
        temp_registry.load_baseline(sample_baseline.baseline_id)


def test_list_baselines(temp_registry, sample_baseline):
    """
    Contract: list_baselines() returns all baseline IDs.
    """
    # Initially empty
    assert temp_registry.list_baselines() == []

    # Save baseline
    temp_registry.save_baseline(sample_baseline)

    # Should appear in list
    baselines = temp_registry.list_baselines()
    assert sample_baseline.baseline_id in baselines


def test_baseline_exists(temp_registry, sample_baseline):
    """
    Contract: baseline_exists() correctly checks presence.
    """
    assert not temp_registry.baseline_exists(sample_baseline.baseline_id)

    temp_registry.save_baseline(sample_baseline)

    assert temp_registry.baseline_exists(sample_baseline.baseline_id)


def test_load_nonexistent_baseline(temp_registry):
    """
    Contract: load_baseline() raises FileNotFoundError for missing baseline.
    """
    with pytest.raises(FileNotFoundError, match="Baseline .* not found"):
        temp_registry.load_baseline("nonexistent_id")


def test_float_precision_preserved(temp_registry):
    """
    Contract: Parquet preserves full float64 precision (no JSON float loss).
    """
    config = {"entry": 0.5}
    config_hash = BacktestBaseline.compute_config_hash(config)
    baseline_id = BacktestBaseline.compute_baseline_id(config_hash, "data_v1", "NYSE_2026", "1.0.0")

    # Create allocation with high-precision floats
    dates = pd.date_range("2025-01-01", periods=3, freq="D")
    allocation = pd.DataFrame({
        14593: [0.123456789012345, 0.987654321098765, 0.555555555555555],
        14551: [0.111111111111111, 0.222222222222222, 0.333333333333333],
    }, index=dates)

    baseline = BacktestBaseline(
        baseline_id=baseline_id,
        strategy_name="precision_test",
        strategy_version="1.0.0",
        config_hash=config_hash,
        data_snapshot_hash="data_v1",
        calendar_version="NYSE_2026",
        execution_timestamp=datetime.now(),
        run_environment="dev",
        expected_allocation=allocation,
        rebalance_schedule=[dates[0]],
        full_config=config,
    )

    temp_registry.save_baseline(baseline)
    loaded = temp_registry.load_baseline(baseline_id)

    # Verify float64 precision preserved (should match exactly)
    # Note: Parquet may not preserve DatetimeIndex.freq, so check_freq=False
    pd.testing.assert_frame_equal(loaded.expected_allocation, allocation, check_freq=False)
    np.testing.assert_array_almost_equal(
        loaded.expected_allocation.values,
        allocation.values,
        decimal=15,  # Full float64 precision
    )


def test_update_latest_pointer(temp_registry, sample_baseline):
    """
    Phase 33A Step 7: Test latest pointer creation and update.

    Contract: save_baseline() automatically updates latest.json pointer.
    """
    temp_registry.save_baseline(sample_baseline)

    latest_path = temp_registry.baselines_dir / "latest.json"
    assert latest_path.exists(), "latest.json should be created after save"

    pointer = json.loads(latest_path.read_text())
    assert pointer["baseline_id"] == sample_baseline.baseline_id
    assert pointer["strategy_name"] == sample_baseline.strategy_name
    assert pointer["strategy_version"] == sample_baseline.strategy_version
    assert "created_at" in pointer
    assert "path" in pointer
    assert pointer["path"] == f"data/backtest_baselines/{sample_baseline.baseline_id}"


def test_latest_pointer_atomic_update(temp_registry):
    """
    Phase 33A Step 7: Test that latest pointer updates are atomic.

    Contract: Last write wins, no partial updates.
    """
    # Create two different baselines
    config1 = {"entry": 0.5}
    config_hash1 = BacktestBaseline.compute_config_hash(config1)
    baseline_id1 = BacktestBaseline.compute_baseline_id(config_hash1, "data_v1", "NYSE_2026", "1.0.0")

    dates = pd.date_range("2025-01-01", periods=5, freq="D")
    allocation = pd.DataFrame(np.random.rand(5, 2), index=dates, columns=[14593, 14551])

    baseline1 = BacktestBaseline(
        baseline_id=baseline_id1,
        strategy_name="strategy_v1",
        strategy_version="1.0.0",
        config_hash=config_hash1,
        data_snapshot_hash="data_v1",
        calendar_version="NYSE_2026",
        execution_timestamp=datetime(2026, 3, 1, 10, 0, 0),
        run_environment="dev",
        expected_allocation=allocation,
        rebalance_schedule=[dates[0]],
        full_config=config1,
    )

    config2 = {"entry": 0.6}
    config_hash2 = BacktestBaseline.compute_config_hash(config2)
    baseline_id2 = BacktestBaseline.compute_baseline_id(config_hash2, "data_v1", "NYSE_2026", "1.0.0")

    baseline2 = BacktestBaseline(
        baseline_id=baseline_id2,
        strategy_name="strategy_v2",
        strategy_version="1.0.0",
        config_hash=config_hash2,
        data_snapshot_hash="data_v1",
        calendar_version="NYSE_2026",
        execution_timestamp=datetime(2026, 3, 3, 15, 30, 0),
        run_environment="dev",
        expected_allocation=allocation,
        rebalance_schedule=[dates[0]],
        full_config=config2,
    )

    # Save first baseline
    temp_registry.save_baseline(baseline1)
    latest = json.loads((temp_registry.baselines_dir / "latest.json").read_text())
    assert latest["strategy_name"] == "strategy_v1"

    # Save second baseline (should update pointer)
    temp_registry.save_baseline(baseline2)
    latest = json.loads((temp_registry.baselines_dir / "latest.json").read_text())
    assert latest["strategy_name"] == "strategy_v2"
    assert latest["baseline_id"] == baseline_id2


def test_latest_pointer_no_tmp_files(temp_registry, sample_baseline):
    """
    Phase 33A Step 7: Test atomic write cleanup for latest pointer.

    Contract: No .tmp files remain after successful pointer update.
    """
    temp_registry.save_baseline(sample_baseline)

    # Verify no .tmp files in baselines_dir root
    tmp_files = list(temp_registry.baselines_dir.glob("*.tmp"))
    assert len(tmp_files) == 0, "No .tmp files should remain after pointer update"
