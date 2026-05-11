"""Pinned strategy universe loader.

Reads data/universe/pinned_thesis_universe.yml and resolves tickers to permnos
via tickers.parquet. Returns pinned permnos for union into feature generation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

DEFAULT_MANIFEST_PATH = Path("data/universe/pinned_thesis_universe.yml")
TICKERS_PATH = Path("data/processed/tickers.parquet")


@dataclass(frozen=True)
class PinnedTicker:
    ticker: str
    start: str  # ISO date or "first_available_trade_date"
    source: str
    notes: str = ""
    permno: int | None = None
    status: str = "OK"  # OK | DATA_BLOCKED | MISSING_MAP


def load_pinned_manifest(path: Path | str | None = None) -> list[dict]:
    """Load raw manifest entries from YAML. Raises on missing/broken/invalid file."""
    path = Path(path) if path else DEFAULT_MANIFEST_PATH
    if not path.exists():
        raise FileNotFoundError(f"Pinned universe manifest not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data or not isinstance(data, dict):
        raise ValueError(f"Pinned universe manifest is empty or malformed: {path}")
    entries = []
    for group_name, tickers in data.items():
        if not isinstance(tickers, list) or len(tickers) == 0:
            raise ValueError(f"Pinned universe group '{group_name}' is empty or not a list")
        for i, entry in enumerate(tickers):
            if not isinstance(entry, dict):
                raise ValueError(f"Pinned universe entry {i} in '{group_name}' is not a dict: {entry!r}")
            ticker = entry.get("ticker", "")
            if not ticker or not str(ticker).strip():
                raise ValueError(f"Pinned universe entry {i} in '{group_name}' has blank ticker")
            entries.append(entry)
    # Reject duplicates
    seen: set[str] = set()
    for entry in entries:
        tk = str(entry["ticker"]).strip().upper()
        if tk in seen:
            raise ValueError(f"Duplicate ticker in pinned universe manifest: {tk}")
        seen.add(tk)
    return entries


def resolve_pinned_universe(
    manifest_path: Path | str | None = None,
    tickers_path: Path | str | None = None,
) -> list[PinnedTicker]:
    """Resolve manifest tickers to permnos. Flag missing mappings."""
    entries = load_pinned_manifest(manifest_path)
    if not entries:
        return []

    tickers_path = Path(tickers_path) if tickers_path else TICKERS_PATH
    if tickers_path.exists():
        tdf = pd.read_parquet(tickers_path)
        t2p = dict(zip(tdf["ticker"], tdf["permno"]))
    else:
        t2p = {}

    result = []
    for entry in entries:
        ticker = str(entry.get("ticker", "")).strip().upper()
        start = str(entry.get("start", "2025-01-02"))
        source = str(entry.get("source", "yahoo"))
        notes = str(entry.get("notes", ""))
        permno = t2p.get(ticker)

        if permno is None:
            status = "MISSING_MAP"
        else:
            status = "OK"

        result.append(PinnedTicker(
            ticker=ticker,
            start=start,
            source=source,
            notes=notes,
            permno=int(permno) if permno is not None else None,
            status=status,
        ))
    return result


def get_pinned_permnos(manifest_path: Path | str | None = None) -> list[int]:
    """Return list of permnos for all pinned tickers. Raises if any ticker is unresolved."""
    resolved = resolve_pinned_universe(manifest_path)
    missing = [p.ticker for p in resolved if p.status == "MISSING_MAP"]
    if missing:
        raise ValueError(f"Pinned tickers have no permno mapping (MISSING_MAP): {missing}. Fix tickers.parquet or remove from manifest.")
    return [p.permno for p in resolved if p.permno is not None]


def get_pinned_tickers(manifest_path: Path | str | None = None) -> list[str]:
    """Return list of ticker symbols from the manifest (normalized: stripped + uppercased)."""
    entries = load_pinned_manifest(manifest_path)
    return [str(e.get("ticker", "")).strip().upper() for e in entries]
