from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
ATTRIBUTION_SCRIPT = SCRIPTS_DIR / "attribution_report.py"


def _create_mock_data(tmp_path: Path, start_date: str, end_date: str):
    """Create mock data files in the expected format for attribution_report.py."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    n_dates = len(dates)

    # Create mock assets (using permno IDs)
    permnos = [10001, 10002, 10003, 10004, 10005]
    n_assets = len(permnos)

    # Create mock factor scores (long format: date x permno with factor columns)
    np.random.seed(42)
    factor_scores_data = []
    for date in dates:
        for permno in permnos:
            factor_scores_data.append({
                "date": date,
                "permno": permno,
                "momentum_normalized": np.random.randn(),
                "quality_normalized": np.random.randn(),
                "volatility_normalized": np.random.randn(),
                "value_normalized": np.random.randn(),
            })
    factor_scores = pd.DataFrame(factor_scores_data)
    factor_scores.to_parquet(data_dir / "phase34_factor_scores.parquet", index=False)

    # Create mock prices TRI (long format: date x permno with tri/total_ret columns)
    base_prices = {permno: price for permno, price in zip(permnos, [100, 150, 200, 120, 80])}
    prices_tri_data = []
    for i, date in enumerate(dates):
        for permno in permnos:
            # Generate cumulative price movement
            price = base_prices[permno] * (1 + 0.001 * i + 0.02 * np.random.randn())
            price = max(price, 1.0)  # Ensure positive prices
            prices_tri_data.append({
                "date": date,
                "permno": permno,
                "tri": price,
                "total_ret": price,
            })
    prices_tri = pd.DataFrame(prices_tri_data)
    prices_tri.to_parquet(data_dir / "prices_tri.parquet", index=False)

    # Create mock target weights (wide format: dates x permnos)
    # Weights sum to 1.0 for each date
    raw_weights = np.random.rand(n_dates, n_assets)
    target_weights = pd.DataFrame(
        raw_weights / raw_weights.sum(axis=1, keepdims=True),
        index=dates,
        columns=permnos,
    )
    target_weights.index.name = "date"
    target_weights.reset_index(inplace=True)
    target_weights.to_parquet(data_dir / "phase34_target_weights.parquet", index=False)

    # Create mock regime history
    regimes = ["NORMAL", "VOLATILE", "TRENDING"]
    regime_history = pd.DataFrame(
        {
            "date": dates,
            "governor_state": np.random.choice(regimes, size=n_dates),
        }
    )
    regime_history.to_csv(data_dir / "regime_history.csv", index=False)

    return data_dir


def test_attribution_report_end_to_end_integration(tmp_path: Path):
    """
    True end-to-end integration test for attribution_report.py.

    Tests:
    1. Run scripts/attribution_report.py on bounded date range (2023-01-01 to 2023-12-31)
    2. Assert all 5 artifacts are generated with proper content
    3. Validate artifact schemas match expected format
    4. Verify IC values are bounded [-1, 1]
    5. Verify accounting identity: sum(contributions) + residual ≈ portfolio_return
    """
    # Arrange: Set up test parameters
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    output_dir = tmp_path / "attribution_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create mock data files
    data_dir = _create_mock_data(tmp_path, start_date, end_date)

    # Act: Run the attribution report script with mock data paths
    cmd = [
        sys.executable,
        str(ATTRIBUTION_SCRIPT),
        "--start-date", start_date,
        "--end-date", end_date,
        "--output-dir", str(output_dir),
        "--factor-scores-path", str(data_dir / "phase34_factor_scores.parquet"),
        "--prices-tri-path", str(data_dir / "prices_tri.parquet"),
        "--target-weights-path", str(data_dir / "phase34_target_weights.parquet"),
        "--regime-history-path", str(data_dir / "regime_history.csv"),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )

    # Assert: Script executed successfully
    assert result.returncode == 0, (
        f"Attribution script failed with return code {result.returncode}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Assert: All 5 artifacts are generated
    expected_artifacts = [
        "phase34_factor_ic.csv",
        "phase34_regime_ic.csv",
        "phase34_attribution.csv",
        "phase34_behavior_ledger.csv",
        "phase34_summary.json",
    ]

    for artifact in expected_artifacts:
        artifact_path = output_dir / artifact
        assert artifact_path.exists(), f"Missing artifact: {artifact}"

    # Test 1: Validate phase34_factor_ic.csv
    factor_ic_path = output_dir / "phase34_factor_ic.csv"
    factor_ic = pd.read_csv(factor_ic_path)

    # Assert non-empty
    assert not factor_ic.empty, "phase34_factor_ic.csv is empty"

    # Assert has required columns for long-format schema
    required_ic_cols = ["date", "factor", "ic", "p_value", "n_assets"]
    for col in required_ic_cols:
        assert col in factor_ic.columns, f"Missing column in factor_ic: {col}"

    # Assert IC values are bounded [-1, 1]
    ic_values = factor_ic["ic"].values
    ic_values_clean = ic_values[~np.isnan(ic_values)]
    assert np.all(ic_values_clean >= -1.0), f"IC values below -1: {ic_values_clean[ic_values_clean < -1.0]}"
    assert np.all(ic_values_clean <= 1.0), f"IC values above 1: {ic_values_clean[ic_values_clean > 1.0]}"

    # Test 2: Validate phase34_regime_ic.csv
    regime_ic_path = output_dir / "phase34_regime_ic.csv"
    regime_ic = pd.read_csv(regime_ic_path)

    # Assert non-empty
    assert not regime_ic.empty, "phase34_regime_ic.csv is empty"

    # Assert no unnamed index columns
    unnamed_cols = [col for col in regime_ic.columns if col.startswith("Unnamed:")]
    assert len(unnamed_cols) == 0, f"Found unnamed index columns in regime_ic: {unnamed_cols}"

    # Assert required columns
    required_regime_cols = ["regime", "factor", "mean_ic", "std_ic", "n_obs"]
    for col in required_regime_cols:
        assert col in regime_ic.columns, f"Missing column in regime_ic: {col}"

    # Assert IC values are bounded [-1, 1]
    mean_ic_values = regime_ic["mean_ic"].values
    mean_ic_clean = mean_ic_values[~np.isnan(mean_ic_values)]
    assert np.all(mean_ic_clean >= -1.0), f"Mean IC values below -1: {mean_ic_clean[mean_ic_clean < -1.0]}"
    assert np.all(mean_ic_clean <= 1.0), f"Mean IC values above 1: {mean_ic_clean[mean_ic_clean > 1.0]}"

    # Test 3: Validate phase34_attribution.csv
    attribution_path = output_dir / "phase34_attribution.csv"
    attribution = pd.read_csv(attribution_path, index_col=0)  # Date index intentional

    # Assert non-empty
    assert not attribution.empty, "phase34_attribution.csv is empty"

    # Assert required columns including residual
    assert "portfolio_return" in attribution.columns, "Missing portfolio_return column"
    assert "residual" in attribution.columns, "Missing residual column"

    # Assert has contribution columns
    contribution_cols = [col for col in attribution.columns if col.endswith("_contribution")]
    assert len(contribution_cols) > 0, "No contribution columns found"

    # Test 4: Verify accounting identity: sum(contributions) + residual ≈ portfolio_return
    for idx in attribution.index:
        row = attribution.loc[idx]
        portfolio_return = row["portfolio_return"]
        residual = row["residual"]

        # Sum all contribution columns
        contributions_sum = sum(row[col] for col in contribution_cols if not pd.isna(row[col]))

        # Accounting identity: contributions + residual should equal portfolio_return
        # Note: residual is already the difference, so contributions_sum should equal portfolio_return
        # because residual = portfolio_return - contributions_sum
        reconstructed_return = contributions_sum + residual

        # Allow small numerical tolerance
        assert np.isclose(reconstructed_return, portfolio_return, atol=1e-10), (
            f"Accounting identity violated at {idx}: "
            f"contributions_sum={contributions_sum:.10f}, "
            f"residual={residual:.10f}, "
            f"reconstructed={reconstructed_return:.10f}, "
            f"portfolio_return={portfolio_return:.10f}"
        )

    # Test 5: Validate phase34_behavior_ledger.csv
    behavior_ledger_path = output_dir / "phase34_behavior_ledger.csv"
    behavior_ledger = pd.read_csv(behavior_ledger_path)

    # Assert non-empty
    assert not behavior_ledger.empty, "phase34_behavior_ledger.csv is empty"

    # Assert no unnamed index columns
    unnamed_cols = [col for col in behavior_ledger.columns if col.startswith("Unnamed:")]
    assert len(unnamed_cols) == 0, f"Found unnamed index columns in behavior_ledger: {unnamed_cols}"

    # Assert required columns
    required_behavior_cols = ["date", "regime", "regime_changed", "total_weight_change", "n_positions"]
    for col in required_behavior_cols:
        assert col in behavior_ledger.columns, f"Missing column in behavior_ledger: {col}"

    # Test 6: Validate phase34_summary.json
    summary_path = output_dir / "phase34_summary.json"
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    # Assert valid JSON structure
    assert isinstance(summary, dict), "summary.json is not a dictionary"

    # Assert required keys
    required_summary_keys = ["ic_stability", "regime_hit_rate", "contribution_r_squared", "ic_consistency_by_factor"]
    for key in required_summary_keys:
        assert key in summary, f"Missing key in summary.json: {key}"

    # Validate ic_stability structure
    assert "mean_ic" in summary["ic_stability"], "Missing mean_ic in ic_stability"
    assert "std_ic" in summary["ic_stability"], "Missing std_ic in ic_stability"
    assert "ic_consistency" in summary["ic_stability"], "Missing ic_consistency in ic_stability"

    # Validate regime_hit_rate structure
    assert isinstance(summary["regime_hit_rate"], dict), "regime_hit_rate should be a dictionary"

    # Validate contribution_r_squared
    assert isinstance(summary["contribution_r_squared"], (int, float)), "contribution_r_squared should be numeric"

    # Validate ic_consistency_by_factor structure
    assert isinstance(summary["ic_consistency_by_factor"], dict), "ic_consistency_by_factor should be a dictionary"

    print(f"\n✓ All 5 artifacts generated successfully")
    print(f"✓ Schema validation passed")
    print(f"✓ IC values bounded [-1, 1]")
    print(f"✓ Accounting identity verified for {len(attribution)} dates")
    print(f"✓ Summary statistics validated")
