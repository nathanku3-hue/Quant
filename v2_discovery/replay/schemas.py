from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from v2_discovery.fast_sim.schemas import PROXY_ENGINE_NAME
from v2_discovery.fast_sim.schemas import V1_CANONICAL_ENGINE_NAME
from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.simulator import SYNTHETIC_PROXY_ENGINE_VERSION


G3_SCHEMA_VERSION = "1.0.0"
G3_V1_REPLAY_ID = "PH65_G3_V1_CANONICAL_REPLAY_001"
G3_V1_ENGINE_VERSION = "phase65-g3-core-engine-current"
G3_BOUNDARY_VERDICT = "v2_blocked_from_promotion"
G3_REPORT_SCHEMA_VERSION = "1.0.0"


class G3ReplayError(ProxyBoundaryError):
    """Raised when the G3 canonical replay boundary is violated."""


@dataclass(frozen=True)
class G3MechanicalOutput:
    candidate_id: str
    manifest_uri: str
    source_quality: str
    positions: pd.DataFrame
    ledger: pd.DataFrame

    def to_allowed_fields(self) -> dict[str, Any]:
        date_values = self.ledger["date"].astype(str).tolist()
        return {
            "positions": _position_records(self.positions),
            "cash": _series_records(self.ledger, "cash"),
            "turnover": _series_records(self.ledger, "turnover"),
            "transaction_cost": _series_records(self.ledger, "transaction_cost"),
            "gross_exposure": _series_records(self.ledger, "gross_exposure"),
            "net_exposure": _series_records(self.ledger, "net_exposure"),
            "row_count": int(len(self.ledger)),
            "date_range": {
                "start": date_values[0] if date_values else None,
                "end": date_values[-1] if date_values else None,
            },
            "manifest_uri": self.manifest_uri,
            "source_quality": self.source_quality,
            "candidate_id": self.candidate_id,
        }


@dataclass(frozen=True)
class G3V1Replay:
    replay_id: str
    engine_name: str
    engine_version: str
    output: G3MechanicalOutput
    engine_rows: int

    def __post_init__(self) -> None:
        if self.engine_name != V1_CANONICAL_ENGINE_NAME:
            raise G3ReplayError("G3 V1 replay must use core.engine.run_simulation")
        if self.engine_rows <= 0:
            raise G3ReplayError("G3 V1 replay requires non-empty canonical engine output")


@dataclass(frozen=True)
class G3V2ProxyReplay:
    proxy_run_id: str
    engine_name: str
    engine_version: str
    registry_note_event_id: str
    output: G3MechanicalOutput
    promotion_ready: bool
    canonical_engine_required: bool

    def __post_init__(self) -> None:
        if self.engine_name != PROXY_ENGINE_NAME:
            raise G3ReplayError("G3 V2 replay must use v2_proxy output")
        if self.engine_version != SYNTHETIC_PROXY_ENGINE_VERSION:
            raise G3ReplayError("G3 V2 replay engine_version mismatch")
        if self.promotion_ready:
            raise G3ReplayError("G3 V2 output cannot be promotion_ready")
        if not self.canonical_engine_required:
            raise G3ReplayError("G3 V2 output must require canonical engine evidence")


@dataclass(frozen=True)
class G3ReplayRun:
    report: dict[str, Any]
    v1_replay: G3V1Replay
    v2_replay: G3V2ProxyReplay
    report_path: Path | None = None
    report_manifest_path: Path | None = None


def _position_records(positions: pd.DataFrame) -> list[dict[str, Any]]:
    ordered = positions.sort_values(["date", "symbol"], kind="mergesort")
    return [
        {
            "date": str(row.date),
            "symbol": str(row.symbol),
            "quantity": _round_float(row.quantity),
            "market_value": _round_float(row.market_value),
        }
        for row in ordered[["date", "symbol", "quantity", "market_value"]].itertuples(index=False)
    ]


def _series_records(ledger: pd.DataFrame, column: str) -> list[dict[str, Any]]:
    return [
        {"date": str(row.date), "value": _round_float(getattr(row, column))}
        for row in ledger[["date", column]].itertuples(index=False)
    ]


def _round_float(value: Any) -> float:
    return round(float(value), 6)
