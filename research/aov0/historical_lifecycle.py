"""Source-bound terminal-security lifecycle events for historical AOV replay.

Terminal events are execution/corporate-action facts, not alpha signals.  They
may change realized return and tradability only on or after the event effective
date.  The loader requires a hash-bound receipt and exact permanent CIQ/SPT
identity so a delisting can never be repaired by substituting another listing.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


TERMINAL_EVENTS_SCHEMA = "aov0_historical_terminal_events_v1"
TERMINAL_EVENTS_RECEIPT_SCHEMA = "aov0_historical_terminal_events_receipt_v1"
CASH_MERGER_EVENT = "CASH_MERGER_PREOPEN_TRADING_SUSPENSION"
DEFAULT_CASH_ELECTION_EVENT = "DEFAULT_CASH_ELECTION_MERGER_TRADING_SUSPENSION"
_ALLOWED_EVENT_TYPES = frozenset({CASH_MERGER_EVENT, DEFAULT_CASH_ELECTION_EVENT})
_REQUIRED_COLUMNS = (
    "source_entity_id",
    "security_id",
    "source_spt_item",
    "last_trading_date",
    "effective_date",
    "cash_consideration",
    "currency",
    "event_type",
    "source_authority",
    "source_locator",
)


@dataclass(frozen=True)
class HistoricalTerminalEvents:
    frame: pd.DataFrame
    events_path: Path
    receipt_path: Path
    metadata: dict[str, object]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_historical_terminal_events(
    events_path: Path,
    receipt_path: Path,
) -> HistoricalTerminalEvents:
    """Load a hash-bound terminal-event authority packet and fail closed."""

    events_path = Path(events_path).resolve()
    receipt_path = Path(receipt_path).resolve()
    if not events_path.is_file():
        raise FileNotFoundError(events_path)
    if not receipt_path.is_file():
        raise FileNotFoundError(receipt_path)

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema_version") != TERMINAL_EVENTS_RECEIPT_SCHEMA:
        raise ValueError("aov0_historical_terminal_event_receipt_schema_invalid")
    if str(receipt.get("events_sha256") or "") != _sha256_file(events_path):
        raise ValueError("aov0_historical_terminal_event_hash_mismatch")
    if receipt.get("current_screen_conditioned") is not False:
        raise ValueError("aov0_historical_terminal_event_current_screen_conditioned")
    if receipt.get("current_primary_security_conditioned") is not False:
        raise ValueError("aov0_historical_terminal_event_current_primary_conditioned")
    if int(receipt.get("financial_alpha_evidence", -1)) != 0:
        raise ValueError("aov0_historical_terminal_event_alpha_evidence_invalid")

    raw = pd.read_csv(events_path, dtype=str)
    missing = [column for column in _REQUIRED_COLUMNS if column not in raw.columns]
    if missing:
        raise ValueError("aov0_historical_terminal_event_columns_missing:" + ",".join(missing))
    frame = raw.loc[:, _REQUIRED_COLUMNS].copy()
    if len(frame) != int(receipt.get("event_count", -1)) or frame.empty:
        raise ValueError("aov0_historical_terminal_event_count_invalid")

    for column in ("source_entity_id", "security_id", "source_spt_item", "source_authority", "source_locator"):
        frame[column] = frame[column].fillna("").astype(str).str.strip()
        if frame[column].eq("").any():
            raise ValueError(f"aov0_historical_terminal_event_blank:{column}")
    if frame["security_id"].duplicated().any():
        raise ValueError("aov0_historical_terminal_event_duplicate_security")
    if not frame["security_id"].str.startswith("CIQSEC:").all():
        raise ValueError("aov0_historical_terminal_event_ciq_security_required")
    if not frame["source_spt_item"].str.startswith("SPT").all():
        raise ValueError("aov0_historical_terminal_event_spt_required")

    frame["last_trading_date"] = pd.to_datetime(frame["last_trading_date"], errors="raise").dt.normalize()
    frame["effective_date"] = pd.to_datetime(frame["effective_date"], errors="raise").dt.normalize()
    if (frame["effective_date"] <= frame["last_trading_date"]).any():
        raise ValueError("aov0_historical_terminal_event_date_order_invalid")
    frame["cash_consideration"] = pd.to_numeric(frame["cash_consideration"], errors="coerce")
    if frame["cash_consideration"].isna().any() or not np.isfinite(frame["cash_consideration"].to_numpy(float)).all():
        raise ValueError("aov0_historical_terminal_event_cash_nonfinite")
    if (frame["cash_consideration"] <= 0.0).any():
        raise ValueError("aov0_historical_terminal_event_cash_nonpositive")
    frame["currency"] = frame["currency"].fillna("").astype(str).str.upper().str.strip()
    if not frame["currency"].eq("USD").all():
        raise ValueError("aov0_historical_terminal_event_currency_not_usd")
    frame["event_type"] = frame["event_type"].fillna("").astype(str).str.strip()
    if not frame["event_type"].isin(_ALLOWED_EVENT_TYPES).all():
        raise ValueError("aov0_historical_terminal_event_type_invalid")

    bindings = receipt.get("event_bindings")
    if not isinstance(bindings, list) or len(bindings) != len(frame):
        raise ValueError("aov0_historical_terminal_event_receipt_bindings_invalid")
    expected_bindings = [
        {
            "source_entity_id": str(row.source_entity_id),
            "security_id": str(row.security_id),
            "source_spt_item": str(row.source_spt_item),
            "last_trading_date": pd.Timestamp(row.last_trading_date).date().isoformat(),
            "effective_date": pd.Timestamp(row.effective_date).date().isoformat(),
            "cash_consideration": format(Decimal(str(float(row.cash_consideration))).normalize(), "f"),
            "currency": str(row.currency),
            "event_type": str(row.event_type),
            "source_authority": str(row.source_authority),
            "source_locator": str(row.source_locator),
        }
        for row in frame.itertuples(index=False)
    ]
    if bindings != expected_bindings:
        raise ValueError("aov0_historical_terminal_event_receipt_binding_drift")

    return HistoricalTerminalEvents(
        frame=frame.sort_values(["effective_date", "security_id"]).reset_index(drop=True),
        events_path=events_path,
        receipt_path=receipt_path,
        metadata=dict(receipt),
    )
