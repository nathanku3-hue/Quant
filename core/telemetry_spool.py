"""
Telemetry Spool Writer - Phase 33B Slice 2

Append-only JSONL writer for telemetry events with performance-optimized durability.

Durability Contract:
- Event writes use append mode (open(..., 'a')) for performance
- Each write is flushed to OS buffer (not fsync'd to disk)
- Accepts crash-window event loss (events in OS buffer may be lost on crash)
- Rotation uses atomic replace pattern (no partial rotations)
- Thread-safe with lock for concurrent writes

Trade-offs:
- Performance: ~1000x faster than fsync per event
- Durability: Events may be lost in crash window (typically <1 second)
- Use case: Observability telemetry where occasional event loss is acceptable

For critical audit trails requiring strict durability, use DuckDB-backed
alert persistence (DriftAlertManager) instead.

Design:
- JSONL format (one JSON object per line)
- Automatic rotation when file exceeds size threshold
- Cleanup of old rotated files (keeps N most recent)

Usage:
    spool = TelemetrySpool(spool_path="data/telemetry/drift_events.jsonl")
    spool.write_event(event)
    spool.rotate_if_needed()
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.telemetry_events import TelemetryEvent

logger = logging.getLogger(__name__)


class TelemetrySpool:
    """
    Thread-safe append-only telemetry event writer.

    Phase 33B Slice 2: Observability foundation with performance-optimized durability.

    Features:
    - JSONL format for easy parsing
    - Buffered append writes (flush to OS, no fsync)
    - Atomic rotation on size threshold
    - Thread-safe with lock
    """

    def __init__(
        self,
        spool_path: Path | str,
        *,
        max_size_mb: float = 10.0,
        rotation_keep: int = 5,
    ):
        """
        Initialize telemetry spool writer.

        Args:
            spool_path: Path to JSONL spool file
            max_size_mb: Max file size before rotation (default: 10 MB)
            rotation_keep: Number of rotated files to keep (default: 5)
        """
        self.spool_path = Path(spool_path)
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.rotation_keep = rotation_keep
        self._write_lock = threading.Lock()

        # Ensure parent directory exists
        self.spool_path.parent.mkdir(parents=True, exist_ok=True)

    def write_event(self, event: TelemetryEvent) -> None:
        """
        Write telemetry event to spool (thread-safe, buffered I/O).

        Durability: Uses append mode with flush to OS buffer (not fsync).
        Events in OS buffer may be lost on crash/power failure.
        This trade-off provides ~1000x better performance for observability use case.

        Args:
            event: TelemetryEvent to persist

        Raises:
            OSError: If write fails
        """
        with self._write_lock:
            try:
                # Serialize event to JSON line
                event_dict = event.to_dict()
                json_line = json.dumps(event_dict, separators=(',', ':')) + '\n'

                # Buffered append: write + flush to OS buffer (no fsync for performance)
                with open(self.spool_path, 'a', encoding='utf-8') as f:
                    f.write(json_line)
                    f.flush()  # Ensure write to OS buffer

            except Exception as e:
                logger.error(f"Failed to write telemetry event: {e}", exc_info=True)
                raise

    def rotate_if_needed(self) -> bool:
        """
        Rotate spool file if size exceeds threshold (atomic operation).

        Rotation strategy:
        - Rename current file to {name}.{timestamp}.jsonl (atomic replace)
        - Create new empty spool file
        - Delete oldest rotated files beyond rotation_keep limit

        Durability: Rotation uses atomic replace, no partial rotations possible.

        Returns:
            True if rotation occurred, False otherwise

        Raises:
            OSError: If rotation fails
        """
        with self._write_lock:
            if not self.spool_path.exists():
                return False

            file_size = self.spool_path.stat().st_size
            if file_size < self.max_size_bytes:
                return False

            try:
                # Generate rotation filename with timestamp and microseconds for uniqueness
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
                rotated_name = f"{self.spool_path.stem}.{timestamp}.jsonl"
                rotated_path = self.spool_path.parent / rotated_name

                # Rename current file (use replace to overwrite if exists on Windows)
                self.spool_path.replace(rotated_path)
                logger.info(f"Rotated telemetry spool: {rotated_path}")

                # Clean up old rotated files
                self._cleanup_old_rotations()

                return True

            except Exception as e:
                logger.error(f"Failed to rotate telemetry spool: {e}", exc_info=True)
                raise

    def _cleanup_old_rotations(self) -> None:
        """
        Delete oldest rotated files beyond rotation_keep limit.

        Keeps only the N most recent rotated files.
        """
        try:
            # Find all rotated files matching pattern
            pattern = f"{self.spool_path.stem}.*.jsonl"
            rotated_files = sorted(
                self.spool_path.parent.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True,  # Newest first
            )

            # Delete files beyond keep limit
            for old_file in rotated_files[self.rotation_keep:]:
                old_file.unlink()
                logger.info(f"Deleted old telemetry spool: {old_file}")

        except Exception as e:
            logger.warning(f"Failed to cleanup old telemetry spools: {e}")

    def read_events(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Read events from spool file (for testing/debugging).

        Args:
            limit: Max number of events to read (None = all)

        Returns:
            List of event dicts (parsed JSON)
        """
        if not self.spool_path.exists():
            return []

        events = []
        try:
            with open(self.spool_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if limit and len(events) >= limit:
                        break
                    if line.strip():
                        events.append(json.loads(line))
            return events

        except Exception as e:
            logger.error(f"Failed to read telemetry events: {e}", exc_info=True)
            return []

    def clear(self) -> None:
        """
        Clear spool file (for testing).

        WARNING: Deletes all events in current spool file.
        """
        with self._write_lock:
            if self.spool_path.exists():
                self.spool_path.unlink()
                logger.info(f"Cleared telemetry spool: {self.spool_path}")
