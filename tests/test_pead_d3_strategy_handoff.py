from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from strategies.pead_event_study import PeadEventStudyConfig
from strategies.pead_event_study import build_event_windows
from strategies.pead_event_study import summarize_event_windows


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
D3_MANIFEST_PATH = (
    DATA_DIR / "pead_d3_ken_french_daily_benchmark.parquet.manifest.json"
)
if D3_MANIFEST_PATH.is_file():
    try:
        d3_manifest = json.loads(D3_MANIFEST_PATH.read_text(encoding="utf-8"))
        d2b_manifest_name = Path(d3_manifest["d2b_input"]["manifest_path"]).name
        D2B_MANIFEST_PATH = DATA_DIR / d2b_manifest_name
    except Exception:
        D2B_MANIFEST_PATH = DATA_DIR / "pead_d2b_event_windows_sample.parquet.manifest.json"
else:
    D2B_MANIFEST_PATH = DATA_DIR / "pead_d2b_event_windows_sample.parquet.manifest.json"
D2B_HANDOFF_COLUMNS = [
    "event_id",
    "issuer_id",
    "security_id",
    "event_date",
    "sue",
    "is_primary_security",
    "event_day",
    "return_date",
    "asset_return",
    "window_complete",
]


def _read_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@pytest.fixture(scope="module")
def published_handoff() -> tuple[
    dict[str, Any],
    dict[str, Any],
    Path,
    pd.DataFrame,
    pd.DataFrame,
]:
    manifest_paths = (D2B_MANIFEST_PATH, D3_MANIFEST_PATH)
    missing_manifests = [path for path in manifest_paths if not path.is_file()]
    if len(missing_manifests) == len(manifest_paths):
        pytest.skip("requires locally published D2B and D3 artifact bundles")
    assert not missing_manifests, f"incomplete local handoff bundle: {missing_manifests}"

    d2b_manifest = _read_manifest(D2B_MANIFEST_PATH)
    d3_manifest = _read_manifest(D3_MANIFEST_PATH)
    d2b_path = DATA_DIR / d2b_manifest["output"]["parquet_file"]
    d3_path = DATA_DIR / d3_manifest["parquet_file"]
    assert d2b_path.is_file(), f"D2B manifest target is missing: {d2b_path}"
    assert d3_path.is_file(), f"D3 manifest target is missing: {d3_path}"
    return (
        d2b_manifest,
        d3_manifest,
        d3_path,
        pd.read_parquet(d2b_path, columns=D2B_HANDOFF_COLUMNS),
        pd.read_parquet(d3_path, columns=["return_date", "benchmark_return"]),
    )


@pytest.fixture(scope="module")
def joined_handoff(
    published_handoff: tuple[
        dict[str, Any],
        dict[str, Any],
        Path,
        pd.DataFrame,
        pd.DataFrame,
    ],
) -> pd.DataFrame:
    _, _, _, d2b, d3 = published_handoff
    return d2b.merge(
        d3[["return_date", "benchmark_return"]],
        on="return_date",
        how="left",
        validate="many_to_one",
    )


def _complete_event_ids(joined: pd.DataFrame, count: int = 3) -> list[str]:
    complete = joined.groupby("event_id", sort=False)["window_complete"].all()
    return sorted(complete.index[complete].astype(str))[:count]


def _strategy_inputs(
    joined: pd.DataFrame,
    d3: pd.DataFrame,
    event_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DatetimeIndex]:
    event_window = joined.loc[joined["event_id"].eq(event_id)].sort_values("event_day")
    event_columns = [
        "event_id",
        "issuer_id",
        "security_id",
        "event_date",
        "sue",
        "is_primary_security",
    ]
    events = event_window.loc[event_window["event_day"].eq(1), event_columns].copy()
    returns = event_window[
        ["security_id", "return_date", "asset_return", "benchmark_return"]
    ].rename(columns={"return_date": "date", "asset_return": "total_return"})
    
    target_dtype = d3["return_date"].dtype
    events["event_date"] = events["event_date"].astype(target_dtype)
    returns["date"] = returns["date"].astype(target_dtype)
    sessions = pd.DatetimeIndex(d3["return_date"].astype(target_dtype))
    
    return events, returns, sessions


def test_published_d3_manifest_hash_and_allowed_use(
    published_handoff: tuple[
        dict[str, Any],
        dict[str, Any],
        Path,
        pd.DataFrame,
        pd.DataFrame,
    ],
) -> None:
    d2b_manifest, d3_manifest, d3_path, _, d3 = published_handoff
    d2b_path = DATA_DIR / d2b_manifest["output"]["parquet_file"]

    assert d3_path.is_file()
    assert _sha256(d3_path) == d3_manifest["sha256"]
    assert d3_manifest["sha256"] in d3_path.name
    assert d3_manifest["allowed_use"] == "benchmark_input_for_pead_d3_only"
    assert d3_manifest["row_count"] == len(d3) == 2_810
    assert _sha256(D2B_MANIFEST_PATH) == d3_manifest["d2b_input"]["manifest_sha256"]
    assert d2b_manifest["output"]["sha256"] == d3_manifest["d2b_input"][
        "parquet_sha256"
    ]
    assert _sha256(d2b_path) == d3_manifest["d2b_input"]["parquet_sha256"]


def test_d2b_to_d3_join_preserves_rows_and_covers_return_dates(
    published_handoff: tuple[
        dict[str, Any],
        dict[str, Any],
        Path,
        pd.DataFrame,
        pd.DataFrame,
    ],
    joined_handoff: pd.DataFrame,
) -> None:
    d2b_manifest, _, _, d2b, d3 = published_handoff

    assert d3["return_date"].is_unique
    assert len(joined_handoff) == len(d2b) == d2b_manifest["output"]["rows"]
    assert d2b_manifest["counts"]["events"] == d2b_manifest["counts"]["selection_status"]["selected"] + d2b_manifest["counts"]["selection_status"]["no_eligible_candidate"]

    d2b_return_dates = pd.DatetimeIndex(d2b["return_date"].dropna().unique())
    d3_return_dates = pd.DatetimeIndex(d3["return_date"])
    assert len(d3_return_dates) == 2_810
    assert d2b_return_dates.isin(d3_return_dates).all()
    assert joined_handoff.loc[
        joined_handoff["return_date"].notna(), "benchmark_return"
    ].notna().all()


def test_complete_windows_have_sixty_benchmark_observations(
    published_handoff: tuple[
        dict[str, Any],
        dict[str, Any],
        Path,
        pd.DataFrame,
        pd.DataFrame,
    ],
    joined_handoff: pd.DataFrame,
) -> None:
    d2b_manifest, _, _, _, _ = published_handoff
    grouped = joined_handoff.groupby("event_id", sort=False)
    complete = grouped["window_complete"].all()
    benchmark_observations = grouped["benchmark_return"].count()

    assert complete.sum() == d2b_manifest["counts"]["coverage_reason"]["complete"]
    assert benchmark_observations.loc[complete].eq(60).all()


def test_published_handoff_matches_strategy_car_and_bhar_formulas(
    published_handoff: tuple[
        dict[str, Any],
        dict[str, Any],
        Path,
        pd.DataFrame,
        pd.DataFrame,
    ],
    joined_handoff: pd.DataFrame,
) -> None:
    _, _, _, _, d3 = published_handoff
    event_id = _complete_event_ids(joined_handoff, count=1)[0]
    events, returns, sessions = _strategy_inputs(joined_handoff, d3, event_id)
    config = PeadEventStudyConfig(benchmark_return_column="benchmark_return")
    windows = build_event_windows(events, returns, sessions, config)

    outcome = summarize_event_windows(windows, config).iloc[0]
    expected_asset = (1.0 + windows["asset_return"]).prod() - 1.0
    expected_benchmark = (1.0 + windows["benchmark_return"]).prod() - 1.0
    expected_car = windows["abnormal_return"].sum()
    expected_bhar = expected_asset - expected_benchmark

    assert outcome["car"] == pytest.approx(expected_car)
    assert outcome["bhar"] == pytest.approx(expected_bhar)


def test_missing_benchmark_masks_car_and_bhar_but_preserves_raw_cumulative_return(
    published_handoff: tuple[
        dict[str, Any],
        dict[str, Any],
        Path,
        pd.DataFrame,
        pd.DataFrame,
    ],
    joined_handoff: pd.DataFrame,
) -> None:
    _, _, _, _, d3 = published_handoff
    event_id = _complete_event_ids(joined_handoff, count=1)[0]
    events, returns, sessions = _strategy_inputs(joined_handoff, d3, event_id)
    expected_raw_return = (1.0 + returns["total_return"]).prod() - 1.0
    returns.loc[returns.index.min(), "benchmark_return"] = np.nan
    config = PeadEventStudyConfig(benchmark_return_column="benchmark_return")
    windows = build_event_windows(events, returns, sessions, config)

    outcome = summarize_event_windows(windows, config).iloc[0]

    assert outcome["benchmark_observations"] == 59
    assert not windows["window_complete"].any()
    assert not outcome["window_complete"]
    assert not outcome["eligible_for_analysis"]
    assert outcome["coverage_reason"] == "missing_benchmark_return"
    assert np.isnan(outcome["car"])
    assert np.isnan(outcome["bhar"])
    assert outcome["cumulative_total_return"] == pytest.approx(expected_raw_return)
