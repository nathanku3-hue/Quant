"""
Phase 33A Step 1: Baseline Identity Contract

Deterministic baseline registry for drift detection with immutable identity binding.

Key Contract Properties (FR-043):
- Baseline ID is content-derived (config + data + calendar + version)
- Timestamp is metadata only (NOT in ID hash for determinism)
- Split storage: metadata.json (small) + expected_allocation.parquet (large)
- Atomic writes with temp + replace pattern
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class BacktestBaseline:
    """
    Immutable baseline identity for drift comparison.

    Contract: baseline_id = SHA256(config_hash|data_hash|calendar|version)[:16]
    Guarantees: Same content → same ID across reruns (deterministic)
    """

    # Identity fields (content-derived, deterministic)
    baseline_id: str  # Computed from content hashes (16-char hex)
    strategy_name: str  # e.g., "momentum_quality_blend"
    strategy_version: str  # Semantic versioning: "1.2.0"
    config_hash: str  # SHA256 of sorted config parameters
    data_snapshot_hash: str  # Parquet file hash or git SHA
    calendar_version: str  # e.g., "NYSE_2026"

    # Metadata (NOT in identity hash)
    execution_timestamp: datetime
    run_environment: str  # "dev" | "staging" | "prod"

    # Drift comparison artifacts
    expected_allocation: pd.DataFrame  # Date index × permno columns with target weights
    rebalance_schedule: list[datetime]  # Planned rebalance dates
    full_config: dict[str, Any]  # Complete strategy parameters (sorted)

    @staticmethod
    def compute_baseline_id(
        config_hash: str,
        data_snapshot_hash: str,
        calendar_version: str,
        strategy_version: str,
    ) -> str:
        """
        Deterministic ID from content hashes.

        Critical: Timestamp NOT included (breaks determinism).
        Formula: SHA256(config_hash|data_hash|calendar|version)[:16]
        """
        material = f"{config_hash}|{data_snapshot_hash}|{calendar_version}|{strategy_version}"
        return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def compute_config_hash(config: dict[str, Any]) -> str:
        """
        Deterministic hash of strategy configuration.

        Sorted keys ensure determinism across dict iteration orders.
        """
        sorted_config = json.dumps(config, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(sorted_config.encode("utf-8")).hexdigest()


class BaselineRegistry:
    """
    Baseline storage manager with split layout and atomic writes.

    Storage Layout:
        data/backtest_baselines/{baseline_id}/
        ├── metadata.json              # Small, human-readable
        └── expected_allocation.parquet  # Large, columnar

    Contract: All writes are atomic (temp file + rename).
    """

    def __init__(self, baselines_dir: Path | str = "data/backtest_baselines"):
        self.baselines_dir = Path(baselines_dir)
        self.baselines_dir.mkdir(parents=True, exist_ok=True)

    def save_baseline(self, baseline: BacktestBaseline) -> None:
        """
        Save baseline with split storage and atomic writes.

        Raises:
            ValueError: If baseline_id doesn't match computed ID (integrity check)
            OSError: If write fails
        """
        # Integrity check: Verify baseline_id matches content
        computed_id = BacktestBaseline.compute_baseline_id(
            baseline.config_hash,
            baseline.data_snapshot_hash,
            baseline.calendar_version,
            baseline.strategy_version,
        )
        if baseline.baseline_id != computed_id:
            raise ValueError(
                f"Baseline ID mismatch: expected {computed_id}, got {baseline.baseline_id}"
            )

        baseline_dir = self.baselines_dir / baseline.baseline_id
        baseline_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata as JSON (small, human-readable)
        metadata = {
            "baseline_id": baseline.baseline_id,
            "strategy_name": baseline.strategy_name,
            "strategy_version": baseline.strategy_version,
            "config_hash": baseline.config_hash,
            "data_snapshot_hash": baseline.data_snapshot_hash,
            "calendar_version": baseline.calendar_version,
            "execution_timestamp": baseline.execution_timestamp.isoformat(),
            "run_environment": baseline.run_environment,
            "rebalance_schedule": [dt.isoformat() for dt in baseline.rebalance_schedule],
            "full_config": baseline.full_config,
        }

        # Atomic write: temp file + rename
        metadata_path = baseline_dir / "metadata.json"
        metadata_tmp = baseline_dir / "metadata.json.tmp"
        metadata_tmp.write_text(json.dumps(metadata, indent=2))
        metadata_tmp.replace(metadata_path)

        # Save allocation as Parquet (large, columnar, preserves float64 precision)
        allocation_path = baseline_dir / "expected_allocation.parquet"
        allocation_tmp = baseline_dir / "expected_allocation.parquet.tmp"
        baseline.expected_allocation.to_parquet(allocation_tmp, compression="snappy")
        allocation_tmp.replace(allocation_path)

        # Update latest pointer (Phase 33A Step 7)
        self.update_latest_pointer(baseline)

    def update_latest_pointer(self, baseline: BacktestBaseline) -> None:
        """
        Update latest.json pointer to most recent baseline.

        Phase 33A Step 7: Creates/updates data/backtest_baselines/latest.json with:
        - baseline_id: For loading full baseline
        - strategy_name: For display
        - created_at: For staleness check
        - path: Relative path to baseline directory

        Atomic write with temp + replace pattern for cross-platform safety.
        """
        pointer = {
            "baseline_id": baseline.baseline_id,
            "strategy_name": baseline.strategy_name,
            "strategy_version": baseline.strategy_version,
            "created_at": baseline.execution_timestamp.isoformat(),
            "path": f"data/backtest_baselines/{baseline.baseline_id}",
        }

        latest_path = self.baselines_dir / "latest.json"
        temp_path = latest_path.with_suffix(".json.tmp")

        temp_path.write_text(json.dumps(pointer, indent=2))
        temp_path.replace(latest_path)  # Atomic on POSIX and Windows

    def load_baseline(self, baseline_id: str) -> BacktestBaseline:
        """
        Load baseline from split storage.

        Raises:
            FileNotFoundError: If baseline_id doesn't exist
            ValueError: If baseline_id integrity check fails
        """
        baseline_dir = self.baselines_dir / baseline_id
        if not baseline_dir.exists():
            raise FileNotFoundError(f"Baseline {baseline_id} not found at {baseline_dir}")

        # Load metadata
        metadata_path = baseline_dir / "metadata.json"
        metadata = json.loads(metadata_path.read_text())

        # Load allocation
        allocation_path = baseline_dir / "expected_allocation.parquet"
        expected_allocation = pd.read_parquet(allocation_path)

        baseline = BacktestBaseline(
            baseline_id=metadata["baseline_id"],
            strategy_name=metadata["strategy_name"],
            strategy_version=metadata["strategy_version"],
            config_hash=metadata["config_hash"],
            data_snapshot_hash=metadata["data_snapshot_hash"],
            calendar_version=metadata["calendar_version"],
            execution_timestamp=datetime.fromisoformat(metadata["execution_timestamp"]),
            run_environment=metadata["run_environment"],
            expected_allocation=expected_allocation,
            rebalance_schedule=[datetime.fromisoformat(dt) for dt in metadata["rebalance_schedule"]],
            full_config=metadata["full_config"],
        )

        # Integrity check: Verify loaded baseline_id matches content
        computed_id = BacktestBaseline.compute_baseline_id(
            baseline.config_hash,
            baseline.data_snapshot_hash,
            baseline.calendar_version,
            baseline.strategy_version,
        )
        if baseline.baseline_id != computed_id:
            raise ValueError(
                f"Baseline {baseline_id} integrity check failed: "
                f"stored ID {baseline.baseline_id} != computed ID {computed_id}"
            )

        return baseline

    def list_baselines(self) -> list[str]:
        """List all baseline IDs in registry."""
        if not self.baselines_dir.exists():
            return []
        return [d.name for d in self.baselines_dir.iterdir() if d.is_dir()]

    def baseline_exists(self, baseline_id: str) -> bool:
        """Check if baseline exists in registry."""
        return (self.baselines_dir / baseline_id).exists()
