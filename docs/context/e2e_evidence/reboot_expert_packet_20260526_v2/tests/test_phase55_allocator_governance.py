from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from scripts.phase55_allocator_governance import (
    NestedCPCVConfig,
    compute_nested_cpcv,
)
from utils.spa import BootstrapConfig


def _build_rows(
    fold: int,
    dates: pd.DatetimeIndex,
    variant: object,
    returns: list[float],
) -> list[dict]:
    return [
        {
            "fold": fold,
            "snapshot_date": date,
            "variant_id": variant,
            "period_return": ret,
        }
        for date, ret in zip(dates, returns)
    ]


def test_nested_cpcv_uses_combinatorial_outer_splits_and_outer_train_only_selection():
    fold_dates = {
        0: pd.date_range("2020-01-01", periods=4, freq="D"),
        1: pd.date_range("2020-01-05", periods=4, freq="D"),
        2: pd.date_range("2020-01-09", periods=4, freq="D"),
        3: pd.date_range("2020-01-13", periods=4, freq="D"),
    }
    rows: list[dict] = []
    rows += _build_rows(0, fold_dates[0], "A", [0.030, 0.025, 0.028, 0.031])
    rows += _build_rows(0, fold_dates[0], "B", [-0.010, -0.015, -0.012, -0.008])
    rows += _build_rows(1, fold_dates[1], "A", [0.035, 0.030, 0.032, 0.027])
    rows += _build_rows(1, fold_dates[1], "B", [-0.020, -0.010, -0.015, -0.012])
    rows += _build_rows(2, fold_dates[2], "A", [-0.030, -0.025, -0.028, -0.022])
    rows += _build_rows(2, fold_dates[2], "B", [0.020, 0.025, 0.021, 0.027])
    rows += _build_rows(3, fold_dates[3], "A", [-0.020, -0.015, -0.018, -0.014])
    rows += _build_rows(3, fold_dates[3], "B", [0.030, 0.035, 0.028, 0.032])

    frame = pd.DataFrame(rows)
    config = NestedCPCVConfig(
        n_blocks=2,
        periods_per_year=252.0,
        spa_min_obs=2,
        spa_bootstrap=BootstrapConfig(n_boot=50, seed=7),
    )

    summary, evidence = compute_nested_cpcv(frame=frame, config=config, max_date="2022-12-31")

    assert summary["aggregation"] == {
        "pbo": "mean",
        "dsr": "median",
        "spa_p": "median",
        "wrc_p": "median",
    }
    assert summary["n_outer_folds"] == 4
    assert summary["n_outer_splits"] == 6

    split_map = {
        item["outer_test_blocks"]: item
        for item in evidence["fold_results"]
    }
    assert split_map["2,3"]["selected_variant"] == "A"
    assert split_map["0,1"]["selected_variant"] == "B"


def test_guard_rejects_post_2022_rows():
    frame = pd.DataFrame(
        [
            {
                "fold": 0,
                "snapshot_date": pd.Timestamp("2023-01-01"),
                "variant_id": "A",
                "period_return": 0.01,
            },
            {
                "fold": 1,
                "snapshot_date": pd.Timestamp("2023-01-02"),
                "variant_id": "A",
                "period_return": 0.02,
            },
        ]
    )
    config = NestedCPCVConfig(
        n_blocks=2,
        periods_per_year=252.0,
        spa_min_obs=2,
        spa_bootstrap=BootstrapConfig(n_boot=10, seed=1),
    )

    with pytest.raises(ValueError, match="snapshot_date exceeds max_date guard"):
        compute_nested_cpcv(frame=frame, config=config, max_date="2022-12-31")


def test_max_date_argument_is_clamped_to_research_max_date():
    frame = pd.DataFrame(
        [
            {
                "fold": 0,
                "snapshot_date": pd.Timestamp("2022-12-01"),
                "variant_id": "A",
                "period_return": 0.01,
            },
            {
                "fold": 1,
                "snapshot_date": pd.Timestamp("2022-12-02"),
                "variant_id": "A",
                "period_return": 0.02,
            },
        ]
    )
    config = NestedCPCVConfig(
        n_blocks=2,
        periods_per_year=252.0,
        spa_min_obs=2,
        spa_bootstrap=BootstrapConfig(n_boot=10, seed=1),
    )

    with pytest.raises(ValueError, match="max_date must be <="):
        compute_nested_cpcv(frame=frame, config=config, max_date="2023-01-01")


def test_duplicate_rows_across_folds_raise_leakage_error():
    frame = pd.DataFrame(
        [
            {
                "fold": 0,
                "snapshot_date": pd.Timestamp("2022-12-01"),
                "variant_id": "A",
                "period_return": 0.01,
            },
            {
                "fold": 1,
                "snapshot_date": pd.Timestamp("2022-12-01"),
                "variant_id": "A",
                "period_return": 0.02,
            },
        ]
    )
    config = NestedCPCVConfig(
        n_blocks=2,
        periods_per_year=252.0,
        spa_min_obs=2,
        spa_bootstrap=BootstrapConfig(n_boot=10, seed=1),
    )

    with pytest.raises(ValueError, match="duplicate \\(snapshot_date, variant_id\\) rows across multiple folds"):
        compute_nested_cpcv(frame=frame, config=config, max_date="2022-12-31")


def test_duplicate_rows_within_same_fold_fail_closed():
    frame = pd.DataFrame(
        [
            {
                "fold": 0,
                "snapshot_date": pd.Timestamp("2022-12-01"),
                "variant_id": "A",
                "period_return": 0.01,
            },
            {
                "fold": 0,
                "snapshot_date": pd.Timestamp("2022-12-01"),
                "variant_id": "A",
                "period_return": 0.02,
            },
            {
                "fold": 1,
                "snapshot_date": pd.Timestamp("2022-12-02"),
                "variant_id": "A",
                "period_return": 0.03,
            },
        ]
    )
    config = NestedCPCVConfig(
        n_blocks=2,
        periods_per_year=252.0,
        spa_min_obs=2,
        spa_bootstrap=BootstrapConfig(n_boot=10, seed=1),
    )

    with pytest.raises(ValueError, match="duplicate \\(fold, snapshot_date, variant_id\\) rows"):
        compute_nested_cpcv(frame=frame, config=config, max_date="2022-12-31")


def test_snapshot_date_must_map_to_one_fold_globally():
    frame = pd.DataFrame(
        [
            {
                "fold": 0,
                "snapshot_date": pd.Timestamp("2022-12-01"),
                "variant_id": "A",
                "period_return": 0.01,
            },
            {
                "fold": 1,
                "snapshot_date": pd.Timestamp("2022-12-01"),
                "variant_id": "B",
                "period_return": 0.02,
            },
        ]
    )
    config = NestedCPCVConfig(
        n_blocks=2,
        periods_per_year=252.0,
        spa_min_obs=2,
        spa_bootstrap=BootstrapConfig(n_boot=10, seed=1),
    )

    with pytest.raises(ValueError, match="snapshot_date -> single fold contract"):
        compute_nested_cpcv(frame=frame, config=config, max_date="2022-12-31")


@pytest.mark.parametrize(
    ("bad_field", "bad_value", "match"),
    [
        ("snapshot_date", "not-a-date", "malformed snapshot_date"),
        ("period_return", "not-a-number", "malformed period_return"),
    ],
)
def test_malformed_source_rows_fail_closed(bad_field: str, bad_value: object, match: str):
    frame = pd.DataFrame(
        [
            {
                "fold": 0,
                "snapshot_date": pd.Timestamp("2022-12-01"),
                "variant_id": "A",
                "period_return": 0.01,
            },
            {
                "fold": 1,
                "snapshot_date": pd.Timestamp("2022-12-02"),
                "variant_id": "A",
                "period_return": 0.02,
            },
        ]
    )
    frame[bad_field] = frame[bad_field].astype(object)
    frame.loc[0, bad_field] = bad_value
    config = NestedCPCVConfig(
        n_blocks=2,
        periods_per_year=252.0,
        spa_min_obs=2,
        spa_bootstrap=BootstrapConfig(n_boot=10, seed=1),
    )

    with pytest.raises(ValueError, match=match):
        compute_nested_cpcv(frame=frame, config=config, max_date="2022-12-31")


def test_numeric_variant_ids_are_normalized_to_string_contract():
    fold_dates = {
        0: pd.date_range("2020-01-01", periods=4, freq="D"),
        1: pd.date_range("2020-01-05", periods=4, freq="D"),
        2: pd.date_range("2020-01-09", periods=4, freq="D"),
        3: pd.date_range("2020-01-13", periods=4, freq="D"),
    }
    rows: list[dict] = []
    rows += _build_rows(0, fold_dates[0], 1, [0.030, 0.025, 0.028, 0.031])
    rows += _build_rows(0, fold_dates[0], 2, [-0.010, -0.015, -0.012, -0.008])
    rows += _build_rows(1, fold_dates[1], 1, [0.035, 0.030, 0.032, 0.027])
    rows += _build_rows(1, fold_dates[1], 2, [-0.020, -0.010, -0.015, -0.012])
    rows += _build_rows(2, fold_dates[2], 1, [-0.030, -0.025, -0.028, -0.022])
    rows += _build_rows(2, fold_dates[2], 2, [0.020, 0.025, 0.021, 0.027])
    rows += _build_rows(3, fold_dates[3], 1, [-0.020, -0.015, -0.018, -0.014])
    rows += _build_rows(3, fold_dates[3], 2, [0.030, 0.035, 0.028, 0.032])

    config = NestedCPCVConfig(
        n_blocks=2,
        periods_per_year=252.0,
        spa_min_obs=2,
        spa_bootstrap=BootstrapConfig(n_boot=50, seed=7),
    )
    _, evidence = compute_nested_cpcv(
        frame=pd.DataFrame(rows),
        config=config,
        max_date="2022-12-31",
    )

    assert all(isinstance(item["selected_variant"], str) for item in evidence["fold_results"])
    assert {item["selected_variant"] for item in evidence["fold_results"]} <= {"1", "2"}


def test_direct_script_cli_help_runs_by_path():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "phase55_allocator_governance.py"

    completed = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Phase 55 nested CPCV allocator governance runner" in completed.stdout
