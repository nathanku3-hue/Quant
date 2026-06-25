"""
Tests for Phase 33A Step 2: Baseline Export Wiring

Validates:
1. Rebalance date extraction from target weights
2. Data snapshot hash determinism
3. End-to-end baseline export during backtest
4. Baseline artifact linkage (results → baseline_id → registry)
5. Atomic persistence of baseline artifacts
"""

import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.baseline_registry import BaselineRegistry
from core.engine import (
    compute_data_snapshot_hash,
    extract_rebalance_dates,
    run_backtest_with_baseline_export,
    run_simulation,
)


@pytest.fixture
def temp_registry(tmp_path):
    """Create temporary baseline registry for testing."""
    registry_dir = tmp_path / "test_baselines"
    registry = BaselineRegistry(baselines_dir=registry_dir)

    # Monkey-patch default registry location for duration of test
    import core.engine
    original_init = BaselineRegistry.__init__

    def patched_init(self, baselines_dir=None):
        if baselines_dir is None:
            baselines_dir = registry_dir
        original_init(self, baselines_dir)

    BaselineRegistry.__init__ = patched_init

    yield registry

    # Restore original
    BaselineRegistry.__init__ = original_init

    # Cleanup
    if registry_dir.exists():
        shutil.rmtree(registry_dir)


@pytest.fixture
def sample_returns():
    """Create sample returns DataFrame for testing."""
    dates = pd.date_range("2025-01-01", periods=20, freq="D")
    permnos = [14593, 14551, 14543]  # AAPL, MSFT, GOOGL

    # Simulate realistic daily returns (-3% to +3%)
    np.random.seed(42)
    returns = pd.DataFrame(
        np.random.randn(20, 3) * 0.015,  # ~1.5% daily vol
        index=dates,
        columns=permnos,
    )
    return returns


@pytest.fixture
def sample_weights():
    """Create sample target weights DataFrame for testing."""
    dates = pd.date_range("2025-01-01", periods=20, freq="D")
    permnos = [14593, 14551, 14543]

    # Static allocation for first 10 days
    weights = pd.DataFrame(
        [[0.4, 0.3, 0.2]] * 10 + [[0.3, 0.4, 0.2]] * 10,  # Rebalance at day 10
        index=dates,
        columns=permnos,
    )
    return weights


def test_extract_rebalance_dates_single_rebalance(sample_weights):
    """
    Contract: Extract dates where allocation changed.

    Expected: First date (initial allocation) + date where weights changed.
    """
    rebalance_dates = extract_rebalance_dates(sample_weights)

    # Should have 2 rebalances: initial + day 10 change
    assert len(rebalance_dates) == 2, "Expected 2 rebalance dates"

    # First rebalance is initial allocation
    assert rebalance_dates[0] == sample_weights.index[0].to_pydatetime()

    # Second rebalance is day 10 (where allocation changed)
    assert rebalance_dates[1] == sample_weights.index[10].to_pydatetime()


def test_extract_rebalance_dates_no_changes():
    """
    Contract: Static allocation should only have 1 rebalance (initial).
    """
    dates = pd.date_range("2025-01-01", periods=10, freq="D")
    static_weights = pd.DataFrame(
        [[0.5, 0.3, 0.2]] * 10,  # No changes
        index=dates,
        columns=[14593, 14551, 14543],
    )

    rebalance_dates = extract_rebalance_dates(static_weights)

    # Only initial allocation
    assert len(rebalance_dates) == 1
    assert rebalance_dates[0] == dates[0].to_pydatetime()


def test_extract_rebalance_dates_daily_rebalance():
    """
    Contract: Daily changes should produce N rebalance dates.
    """
    dates = pd.date_range("2025-01-01", periods=5, freq="D")

    # Different weights each day
    daily_weights = pd.DataFrame(
        [[0.5 + i*0.05, 0.3, 0.2] for i in range(5)],
        index=dates,
        columns=[14593, 14551, 14543],
    )

    rebalance_dates = extract_rebalance_dates(daily_weights)

    # Should have 5 rebalances (every day)
    assert len(rebalance_dates) == 5


def test_extract_rebalance_dates_empty_dataframe():
    """
    Contract: Empty DataFrame should return empty list.
    """
    empty_df = pd.DataFrame()
    rebalance_dates = extract_rebalance_dates(empty_df)

    assert rebalance_dates == []


def test_compute_data_snapshot_hash_deterministic(sample_returns):
    """
    Contract: Same DataFrame produces same hash across multiple calls.
    """
    hash1 = compute_data_snapshot_hash(sample_returns)
    hash2 = compute_data_snapshot_hash(sample_returns)
    hash3 = compute_data_snapshot_hash(sample_returns)

    assert hash1 == hash2 == hash3, "Data snapshot hash must be deterministic"
    assert len(hash1) == 64, "Should be full SHA256 (64 hex chars)"


def test_compute_data_snapshot_hash_changes_with_data():
    """
    Contract: Different data produces different hash.
    """
    dates = pd.date_range("2025-01-01", periods=10, freq="D")
    permnos = [14593, 14551]

    df1 = pd.DataFrame(np.random.randn(10, 2) * 0.01, index=dates, columns=permnos)
    df2 = pd.DataFrame(np.random.randn(10, 2) * 0.01, index=dates, columns=permnos)

    hash1 = compute_data_snapshot_hash(df1)
    hash2 = compute_data_snapshot_hash(df2)

    assert hash1 != hash2, "Different data must produce different hash"


def test_compute_data_snapshot_hash_changes_with_shape():
    """
    Contract: Different DataFrame shape produces different hash.
    """
    dates1 = pd.date_range("2025-01-01", periods=10, freq="D")
    dates2 = pd.date_range("2025-01-01", periods=15, freq="D")  # More rows
    permnos = [14593, 14551]

    df1 = pd.DataFrame(np.zeros((10, 2)), index=dates1, columns=permnos)
    df2 = pd.DataFrame(np.zeros((15, 2)), index=dates2, columns=permnos)

    hash1 = compute_data_snapshot_hash(df1)
    hash2 = compute_data_snapshot_hash(df2)

    assert hash1 != hash2, "Different shape must produce different hash"


def test_run_backtest_with_baseline_export_integration(temp_registry, sample_weights, sample_returns):
    """
    Contract: End-to-end baseline export creates valid baseline in registry.

    Validates:
    - Simulation results returned correctly
    - Baseline created with deterministic ID
    - Baseline saved to registry
    - Baseline can be loaded from registry
    """
    strategy_config = {
        "momentum_lookback": 20,
        "entry_threshold": 0.5,
        "exit_threshold": -0.3,
    }

    results, baseline = run_backtest_with_baseline_export(
        target_weights=sample_weights,
        returns_df=sample_returns,
        strategy_config=strategy_config,
        strategy_name="test_momentum",
        strategy_version="1.0.0",
        cost_bps=0.0010,
        save_baseline=True,
    )

    # Verify simulation results
    assert isinstance(results, pd.DataFrame)
    assert "gross_ret" in results.columns
    assert "net_ret" in results.columns
    assert "turnover" in results.columns
    assert "cost" in results.columns
    assert len(results) == len(sample_weights)

    # Verify baseline created
    assert baseline.strategy_name == "test_momentum"
    assert baseline.strategy_version == "1.0.0"
    assert baseline.full_config == strategy_config
    assert baseline.expected_allocation.equals(sample_weights)
    assert len(baseline.rebalance_schedule) == 2  # Initial + 1 rebalance

    # Verify baseline saved to registry
    assert temp_registry.baseline_exists(baseline.baseline_id)

    # Verify baseline can be loaded
    loaded_baseline = temp_registry.load_baseline(baseline.baseline_id)
    assert loaded_baseline.baseline_id == baseline.baseline_id
    assert loaded_baseline.strategy_name == baseline.strategy_name
    pd.testing.assert_frame_equal(
        loaded_baseline.expected_allocation,
        baseline.expected_allocation,
        check_freq=False
    )


def test_baseline_id_determinism_across_runs(temp_registry, sample_weights, sample_returns):
    """
    Contract: Same config + data produces same baseline_id across runs.

    Critical: Ensures drift detector can map live run → exact backtest baseline.
    """
    strategy_config = {"momentum": 20, "entry": 0.5}

    # Run backtest twice with identical inputs
    _, baseline1 = run_backtest_with_baseline_export(
        target_weights=sample_weights,
        returns_df=sample_returns,
        strategy_config=strategy_config,
        strategy_name="test",
        strategy_version="1.0.0",
        save_baseline=False,  # Don't save to avoid collision
    )

    _, baseline2 = run_backtest_with_baseline_export(
        target_weights=sample_weights,
        returns_df=sample_returns,
        strategy_config=strategy_config,
        strategy_name="test",
        strategy_version="1.0.0",
        save_baseline=False,
    )

    # Baseline IDs must be identical
    assert baseline1.baseline_id == baseline2.baseline_id, \
        "Same config + data must produce same baseline_id (determinism requirement)"


def test_baseline_id_changes_with_config(temp_registry, sample_weights, sample_returns):
    """
    Contract: Different config produces different baseline_id.
    """
    config1 = {"momentum": 20}
    config2 = {"momentum": 30}  # Different parameter

    _, baseline1 = run_backtest_with_baseline_export(
        target_weights=sample_weights,
        returns_df=sample_returns,
        strategy_config=config1,
        save_baseline=False,
    )

    _, baseline2 = run_backtest_with_baseline_export(
        target_weights=sample_weights,
        returns_df=sample_returns,
        strategy_config=config2,
        save_baseline=False,
    )

    assert baseline1.baseline_id != baseline2.baseline_id


def test_baseline_timestamp_excluded_from_id(temp_registry, sample_weights, sample_returns):
    """
    Contract: Execution timestamp does NOT affect baseline_id.

    Critical: Ensures re-runs produce same ID for drift comparison.
    """
    import time

    strategy_config = {"entry": 0.5}

    _, baseline1 = run_backtest_with_baseline_export(
        target_weights=sample_weights,
        returns_df=sample_returns,
        strategy_config=strategy_config,
        save_baseline=False,
    )

    time.sleep(0.1)  # Ensure different timestamp

    _, baseline2 = run_backtest_with_baseline_export(
        target_weights=sample_weights,
        returns_df=sample_returns,
        strategy_config=strategy_config,
        save_baseline=False,
    )

    # Timestamps differ
    assert baseline1.execution_timestamp != baseline2.execution_timestamp

    # But baseline_id is identical (timestamp excluded from hash)
    assert baseline1.baseline_id == baseline2.baseline_id


def test_baseline_save_atomicity(temp_registry, sample_weights, sample_returns):
    """
    Contract: Baseline save is atomic (no partial artifacts on error).
    """
    strategy_config = {"test": 1}

    _, baseline = run_backtest_with_baseline_export(
        target_weights=sample_weights,
        returns_df=sample_returns,
        strategy_config=strategy_config,
        save_baseline=True,
    )

    baseline_dir = temp_registry.baselines_dir / baseline.baseline_id

    # Verify no .tmp files remain
    tmp_files = list(baseline_dir.glob("*.tmp"))
    assert len(tmp_files) == 0, "No .tmp files should remain after save"

    # Verify both files exist
    assert (baseline_dir / "metadata.json").exists()
    assert (baseline_dir / "expected_allocation.parquet").exists()


def test_baseline_export_preserves_simulation_results(sample_weights, sample_returns):
    """
    Contract: Baseline export does NOT alter simulation results.

    Ensures run_backtest_with_baseline_export() produces identical
    results to run_simulation() for same inputs.
    """
    # Run without baseline export
    results_direct = run_simulation(
        target_weights=sample_weights,
        returns_df=sample_returns,
        cost_bps=0.0010,
    )

    # Run with baseline export
    results_with_baseline, _ = run_backtest_with_baseline_export(
        target_weights=sample_weights,
        returns_df=sample_returns,
        strategy_config={"test": 1},
        cost_bps=0.0010,
        save_baseline=False,
    )

    # Results must be identical
    pd.testing.assert_frame_equal(results_direct, results_with_baseline)


def test_baseline_config_deep_copy(temp_registry, sample_weights, sample_returns):
    """
    Contract: Baseline stores deep copy of config (immutability).

    Ensures mutations to original config don't affect stored baseline.
    """
    strategy_config = {"param": [1, 2, 3]}  # Mutable list

    _, baseline = run_backtest_with_baseline_export(
        target_weights=sample_weights,
        returns_df=sample_returns,
        strategy_config=strategy_config,
        save_baseline=False,
    )

    # Mutate original config
    strategy_config["param"].append(4)

    # Baseline should still have original values
    assert baseline.full_config["param"] == [1, 2, 3], \
        "Baseline must store deep copy (immutability requirement)"


def test_baseline_allocation_deep_copy(temp_registry, sample_weights, sample_returns):
    """
    Contract: Baseline stores deep copy of allocation (immutability).
    """
    _, baseline = run_backtest_with_baseline_export(
        target_weights=sample_weights,
        returns_df=sample_returns,
        strategy_config={"test": 1},
        save_baseline=False,
    )

    # Mutate original weights
    sample_weights.iloc[0, 0] = 999.0

    # Baseline should have original values
    assert baseline.expected_allocation.iloc[0, 0] != 999.0, \
        "Baseline must store deep copy of allocation"
