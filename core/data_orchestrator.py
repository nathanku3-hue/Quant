"""
Data Orchestrator: Unified Data Loading Abstraction Layer

Provides a unified interface for loading dashboard data, supporting both:
- Live mode: yfinance fetching (dashboard.py legacy path)
- Historical mode: processed parquet files (app.py institutional-grade path)

Enables gradual migration from yfinance to parquet-based data pipeline.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import pandas as pd

from data.dashboard_data_loader import load_dashboard_data


@dataclass
class UnifiedDataPackage:
    """
    Unified data structure for dashboard consumption.

    All dashboards consume this standardized format regardless of underlying source.
    """
    prices: pd.DataFrame  # Wide format: date index, ticker columns
    returns: pd.DataFrame  # Wide format: date index, ticker columns
    macro: pd.DataFrame  # Date index with macro/liquidity/regime features
    ticker_map: dict[int, str]  # permno → ticker mapping
    sector_map: dict[int, str] | None  # permno → sector mapping (optional)
    fundamentals: dict[str, Any] | None  # Fundamentals dict (optional)
    metadata: dict[str, Any]  # Metadata about data source, staleness, etc.


def load_unified_data(
    mode: str = "historical",
    top_n: int = 2000,
    start_year: int = 2000,
    universe_mode: str = "top_liquid",
    asof_date: Any = None,
    *,
    processed_dir: str = "./data/processed",
    static_dir: str = "./data/static",
) -> UnifiedDataPackage:
    """
    Load dashboard data with unified interface.

    Args:
        mode: "historical" (parquet, institutional-grade) or "live" (yfinance, legacy)
        top_n: Number of top liquid tickers
        start_year: Start year for historical data
        universe_mode: "top_liquid" or "r3000_pit"
        asof_date: Optional as-of date for point-in-time universe
        processed_dir: Path to processed data directory
        static_dir: Path to static data directory

    Returns:
        UnifiedDataPackage with standardized data structure
    """
    if mode == "historical":
        return _load_historical_data(
            top_n=top_n,
            start_year=start_year,
            universe_mode=universe_mode,
            asof_date=asof_date,
            processed_dir=processed_dir,
            static_dir=static_dir,
        )
    elif mode == "live":
        return _load_live_data(
            top_n=top_n,
            start_year=start_year,
            processed_dir=processed_dir,
            static_dir=static_dir,
        )
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'historical' or 'live'")


def _load_historical_data(
    top_n: int,
    start_year: int,
    universe_mode: str,
    asof_date: Any,
    processed_dir: str,
    static_dir: str,
) -> UnifiedDataPackage:
    """
    Load data from processed parquet files (institutional-grade path).

    This is the preferred mode for production use with app.py's data pipeline.
    """
    # Use app.py's dashboard_data_loader
    prices_wide, returns_wide, macro, ticker_map, fundamentals_wide = load_dashboard_data(
        top_n=top_n,
        start_year=start_year,
        universe_mode=universe_mode,
        asof_date=asof_date,
        processed_dir=processed_dir,
        static_dir=static_dir,
    )

    # Extract sector_map if available
    sector_map = None
    if isinstance(fundamentals_wide, dict) and "sector_map" in fundamentals_wide:
        sector_map = fundamentals_wide["sector_map"]

    # Build metadata
    metadata = {
        "mode": "historical",
        "source": "parquet",
        "universe_mode": universe_mode,
        "top_n": top_n,
        "start_year": start_year,
        "prices_shape": prices_wide.shape,
        "returns_shape": returns_wide.shape,
        "macro_shape": macro.shape,
        "data_quality": "institutional_grade",
    }

    return UnifiedDataPackage(
        prices=prices_wide,
        returns=returns_wide,
        macro=macro,
        ticker_map=ticker_map,
        sector_map=sector_map,
        fundamentals=fundamentals_wide,
        metadata=metadata,
    )


def _load_live_data(
    top_n: int,
    start_year: int,
    processed_dir: str,
    static_dir: str,
) -> UnifiedDataPackage:
    """
    Load data from live yfinance fetching (dashboard.py legacy path).

    This mode is a fallback for when parquet files are unavailable.
    Provides compatibility with dashboard.py's original data fetching.
    """
    # Check if macro features exist (required for regime manager)
    macro_features_tri_path = f"{processed_dir}/macro_features_tri.parquet"
    macro_features_path = f"{processed_dir}/macro_features.parquet"

    macro = None
    if os.path.exists(macro_features_tri_path):
        macro = pd.read_parquet(macro_features_tri_path)
    elif os.path.exists(macro_features_path):
        macro = pd.read_parquet(macro_features_path)
    else:
        # Fallback: create minimal macro DataFrame
        # This allows dashboard to function without regime manager
        import datetime
        date_range = pd.date_range(
            start=f"{start_year}-01-01",
            end=datetime.datetime.now(),
            freq="D",
        )
        macro = pd.DataFrame(index=date_range)
        macro.index.name = "date"

    # Load sector_map if available
    sector_map_path = f"{static_dir}/sector_map.parquet"
    sector_map = None
    if os.path.exists(sector_map_path):
        sector_map_df = pd.read_parquet(sector_map_path)
        if "permno" in sector_map_df.columns and "sector" in sector_map_df.columns:
            sector_map = dict(zip(sector_map_df["permno"], sector_map_df["sector"]))

    # Build metadata
    metadata = {
        "mode": "live",
        "source": "yfinance",
        "universe_mode": "yfinance_live",
        "top_n": top_n,
        "start_year": start_year,
        "data_quality": "live_fetch",
        "warning": "Live mode is legacy path. Migrate to historical mode for institutional-grade data.",
    }

    # Return minimal package (dashboard.py will populate via its own fetching)
    # This allows dashboard.py to use orchestrator without breaking existing code
    return UnifiedDataPackage(
        prices=pd.DataFrame(),  # Empty - dashboard.py fetches via yfinance
        returns=pd.DataFrame(),  # Empty - dashboard.py computes
        macro=macro,
        ticker_map={},  # Empty - dashboard.py builds dynamically
        sector_map=sector_map,
        fundamentals=None,
        metadata=metadata,
    )


def get_macro_features(
    processed_dir: str = "./data/processed",
    prefer_tri: bool = True,
) -> pd.DataFrame:
    """
    Load macro features for regime manager.

    Args:
        processed_dir: Path to processed data directory
        prefer_tri: If True, prefer macro_features_tri.parquet over macro_features.parquet

    Returns:
        Macro features DataFrame with date index
    """
    macro_features_tri_path = f"{processed_dir}/macro_features_tri.parquet"
    macro_features_path = f"{processed_dir}/macro_features.parquet"

    if prefer_tri and os.path.exists(macro_features_tri_path):
        return pd.read_parquet(macro_features_tri_path)
    elif os.path.exists(macro_features_path):
        return pd.read_parquet(macro_features_path)
    else:
        raise FileNotFoundError(
            f"Macro features not found. Expected at:\n"
            f"  - {macro_features_tri_path} OR\n"
            f"  - {macro_features_path}\n"
            f"Run macro feature builder first."
        )


def derive_data_health(package: UnifiedDataPackage) -> dict[str, Any]:
    """
    Assess data health and return status dict.

    Returns dict with:
        - status: "HEALTHY" | "DEGRADED" | "FAILED"
        - issues: List of issues found
        - metrics: Dict of health metrics
    """
    issues = []
    metrics = {}

    # Check prices coverage
    if package.prices.empty:
        issues.append("Prices DataFrame is empty")
    else:
        null_pct = package.prices.isnull().sum().sum() / (package.prices.shape[0] * package.prices.shape[1])
        metrics["prices_null_pct"] = f"{null_pct * 100:.2f}%"
        if null_pct > 0.10:
            issues.append(f"Prices have {null_pct*100:.1f}% null values (threshold: 10%)")

    # Check returns coverage
    if package.returns.empty:
        issues.append("Returns DataFrame is empty")
    else:
        null_pct = package.returns.isnull().sum().sum() / (package.returns.shape[0] * package.returns.shape[1])
        metrics["returns_null_pct"] = f"{null_pct * 100:.2f}%"

    # Check macro features
    if package.macro.empty:
        issues.append("Macro DataFrame is empty")
    else:
        metrics["macro_rows"] = len(package.macro)
        metrics["macro_cols"] = len(package.macro.columns)

    # Check ticker map
    if not package.ticker_map:
        issues.append("Ticker map is empty")
    else:
        metrics["ticker_count"] = len(package.ticker_map)

    # Determine overall status
    if len(issues) == 0:
        status = "HEALTHY"
    elif len(issues) <= 2:
        status = "DEGRADED"
    else:
        status = "FAILED"

    return {
        "status": status,
        "issues": issues,
        "metrics": metrics,
        "data_mode": package.metadata.get("mode", "unknown"),
        "data_quality": package.metadata.get("data_quality", "unknown"),
    }
