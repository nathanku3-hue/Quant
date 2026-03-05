"""
Phase 33A Step 3: Canonical Instrument Mapping Contract

Resolves identifier mismatch between backtest (permno) and live telemetry (symbol).

Key Contract Properties (FR-044):
- Bidirectional permno ↔ symbol conversion
- Point-in-time mapping (single snapshot date)
- Canonical permno basis for all drift comparisons

IMPORTANT LIMITATION (Phase 33):
  Current implementation uses single snapshot date (point-in-time mapping).
  Historical ticker changes (e.g., FB → META) are NOT supported in production data.
  As-of date parameter is reserved for future enhancement (Phase 34+).

  For Phase 33 drift detection (90-day window), point-in-time mapping is sufficient.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class InstrumentMapping:
    """
    Immutable instrument identifier mapping.

    Represents one permno → symbol mapping valid as of snapshot_date.
    """
    permno: int  # CRSP permanent number (canonical identifier)
    symbol: str  # Trading symbol (can change over time)
    cusip: str | None  # CUSIP identifier (optional)
    snapshot_date: date  # Valid as of this date


class InstrumentMapper:
    """
    Canonical permno ↔ symbol mapper with as-of date validation.

    Contract: All drift comparisons performed on canonical permno basis.
    Live telemetry symbols are converted to permno before comparison.

    Usage:
        mapper = InstrumentMapper("data/static/instrument_mapping.parquet")

        # Convert live telemetry symbol to permno
        permno = mapper.symbol_to_permno("AAPL", as_of=date(2025, 1, 15))

        # Convert backtest permno to symbol (for display)
        symbol = mapper.permno_to_symbol(14593, as_of=date(2025, 1, 15))
    """

    def __init__(self, mapping_file: Path | str):
        """
        Initialize mapper from instrument mapping Parquet file.

        Args:
            mapping_file: Path to instrument_mapping.parquet with schema:
                - permno (int): CRSP permanent number
                - symbol (str): Trading symbol
                - cusip (str): CUSIP identifier (optional, can be None)
                - snapshot_date (date): Valid as-of date

        Raises:
            FileNotFoundError: If mapping file doesn't exist
            ValueError: If mapping file schema is invalid
        """
        mapping_path = Path(mapping_file)
        if not mapping_path.exists():
            raise FileNotFoundError(f"Instrument mapping file not found: {mapping_path}")

        self.mapping = pd.read_parquet(mapping_path)

        # Validate schema
        required_columns = {"permno", "symbol", "cusip", "snapshot_date"}
        missing = required_columns - set(self.mapping.columns)
        if missing:
            raise ValueError(f"Mapping file missing required columns: {missing}")

        # Ensure correct types
        self.mapping["permno"] = self.mapping["permno"].astype(int)
        self.mapping["symbol"] = self.mapping["symbol"].astype(str).str.upper().str.strip()
        self.mapping["snapshot_date"] = pd.to_datetime(self.mapping["snapshot_date"]).dt.date

        # Sort by snapshot_date descending for efficient as-of lookup
        self.mapping = self.mapping.sort_values("snapshot_date", ascending=False)

    def permno_to_symbol(self, permno: int, as_of: date) -> str:
        """
        Convert permno → symbol with as-of date validation.

        Args:
            permno: CRSP permanent number
            as_of: Date for which symbol should be valid (currently point-in-time only)

        Returns:
            Trading symbol valid as of specified date

        Raises:
            ValueError: If no symbol found for permno as of date
            ValueError: If ambiguous mapping found (multiple symbols for same permno)

        Note:
            Phase 33 implementation uses single snapshot date.
            as_of parameter validated but not used for historical resolution.
            Full temporal support deferred to Phase 34+.

        Example:
            >>> mapper = InstrumentMapper("data/static/instrument_mapping.parquet")
            >>> symbol = mapper.permno_to_symbol(14593, as_of=date(2025, 1, 15))
            >>> print(symbol)
            'AAPL'
        """
        # Find most recent mapping on or before as_of date
        matches = self.mapping[
            (self.mapping["permno"] == permno) &
            (self.mapping["snapshot_date"] <= as_of)
        ]

        if matches.empty:
            raise ValueError(
                f"No symbol found for permno={permno} as of {as_of}. "
                f"Mapping may not cover this date or permno is invalid."
            )

        # Fail-closed: Detect ambiguous mappings (multiple symbols for same permno on same date)
        if len(matches) > 1:
            unique_symbols = matches["symbol"].unique()
            if len(unique_symbols) > 1:
                raise ValueError(
                    f"Ambiguous mapping for permno={permno} as of {as_of}: "
                    f"Multiple symbols found: {unique_symbols.tolist()}. "
                    f"Data quality issue or ticker change requires disambiguation."
                )

        return str(matches.iloc[0]["symbol"])

    def symbol_to_permno(self, symbol: str, as_of: date) -> int:
        """
        Convert symbol → permno with as-of date validation.

        Args:
            symbol: Trading symbol (case-insensitive)
            as_of: Date for which mapping should be valid (currently point-in-time only)

        Returns:
            CRSP permanent number valid as of specified date

        Raises:
            ValueError: If no permno found for symbol as of date
            ValueError: If ambiguous mapping found (multiple permnos for same symbol)

        Note:
            Phase 33 implementation uses single snapshot date.
            as_of parameter validated but not used for historical resolution.
            Full temporal support deferred to Phase 34+.

        Example:
            >>> mapper = InstrumentMapper("data/static/instrument_mapping.parquet")
            >>> permno = mapper.symbol_to_permno("AAPL", as_of=date(2025, 1, 15))
            >>> print(permno)
            14593
        """
        symbol_upper = symbol.upper().strip()

        # Find most recent mapping on or before as_of date
        matches = self.mapping[
            (self.mapping["symbol"] == symbol_upper) &
            (self.mapping["snapshot_date"] <= as_of)
        ]

        if matches.empty:
            raise ValueError(
                f"No permno found for symbol={symbol} as of {as_of}. "
                f"Symbol may not exist, mapping may not cover this date, or symbol may have changed."
            )

        # Fail-closed: Detect ambiguous mappings (multiple permnos for same symbol on same date)
        # This can occur when ticker is reused by different companies or during corporate actions
        if len(matches) > 1:
            unique_permnos = matches["permno"].unique()
            if len(unique_permnos) > 1:
                raise ValueError(
                    f"Ambiguous mapping for symbol={symbol} as of {as_of}: "
                    f"Multiple permnos found: {unique_permnos.tolist()}. "
                    f"Ticker reuse or corporate action requires disambiguation. "
                    f"Consider using permno directly or adding CUSIP validation."
                )

        return int(matches.iloc[0]["permno"])

    def get_mapping(self, permno: int | None = None, symbol: str | None = None, as_of: date | None = None) -> pd.DataFrame:
        """
        Get all mappings matching criteria.

        Args:
            permno: Filter by permno (optional)
            symbol: Filter by symbol (optional)
            as_of: Filter by snapshot_date <= as_of (optional)

        Returns:
            DataFrame of matching InstrumentMapping records

        Example:
            >>> # Get all historical mappings for AAPL
            >>> mappings = mapper.get_mapping(symbol="AAPL")
        """
        result = self.mapping.copy()

        if permno is not None:
            result = result[result["permno"] == permno]

        if symbol is not None:
            symbol_upper = symbol.upper().strip()
            result = result[result["symbol"] == symbol_upper]

        if as_of is not None:
            result = result[result["snapshot_date"] <= as_of]

        return result

    def validate_roundtrip(self, permno: int, as_of: date) -> bool:
        """
        Validate permno → symbol → permno roundtrip.

        Args:
            permno: Permno to test
            as_of: As-of date for mapping

        Returns:
            True if roundtrip successful, False otherwise

        Example:
            >>> mapper.validate_roundtrip(14593, date(2025, 1, 15))
            True
        """
        try:
            symbol = self.permno_to_symbol(permno, as_of)
            permno_roundtrip = self.symbol_to_permno(symbol, as_of)
            return permno == permno_roundtrip
        except ValueError:
            return False
