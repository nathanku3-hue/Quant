"""Focused tests for M7F5-ID0 dated-identifier authority."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from scripts import pead_m7f5_id0_dated_identifier_authority as id0


def _d1(path: Path) -> Path:
    pd.DataFrame(
        [
            {"gvkey": "001004", "rdq": "2019-03-19", "sue_price_scaled_clipped": -0.0027, "valid_sue": True},
            {"gvkey": "001004", "rdq": "2019-07-10", "sue_price_scaled_clipped": 0.0065, "valid_sue": True},
            {"gvkey": "002000", "rdq": "2018-12-31", "sue_price_scaled_clipped": 1.0, "valid_sue": True},
            {"gvkey": "003000", "rdq": "2019-05-01", "sue_price_scaled_clipped": 1.0, "valid_sue": False},
        ]
    ).to_parquet(path, index=False)
    return path


def _source(path: Path, rows: list[dict[str, object]]) -> Path:
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def _lock(path: Path) -> dict[str, object]:
    _, contract = id0.build_pre_identity_events(pd.read_parquet(path))
    return {
        "expected_d1_sha256": id0._sha256_file(path),
        "expected_event_count": contract["unique_pre_identity_events"],
        "expected_event_set_sha256": contract["pre_identity_event_set_sha256"],
        "expected_canonical_rows_sha256": contract["pre_identity_canonical_rows_sha256"],
    }


def _evaluate(d1: Path, source: Path) -> dict[str, object]:
    return id0.evaluate_authority(
        d1_path=d1,
        identifier_source_path=source,
        **_lock(d1),
    )


def test_locked_real_d1_contract_constants_are_exact() -> None:
    assert id0.LOCKED_D1_SHA256 == "81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855"
    assert id0.LOCKED_PRE_IDENTITY_EVENT_COUNT == 21_882
    assert id0.LOCKED_PRE_IDENTITY_EVENT_SET_SHA256 == "2922192aba299a7ab741e2ff1183f033291312614fbb4b3dce60f760fe7e06a5"
    assert id0.LOCKED_PRE_IDENTITY_CANONICAL_ROWS_SHA256 == "3592137066ad74290e988ac06f4b6e29ccce64fc29ce8be4e864a3d0b7a882bd"


def test_pre_identity_filter_and_hash_are_shuffle_stable(tmp_path: Path) -> None:
    frame = pd.read_parquet(_d1(tmp_path / "d1.parquet"))
    events, contract = id0.build_pre_identity_events(frame)
    shuffled, shuffled_contract = id0.build_pre_identity_events(frame.sample(frac=1, random_state=7))
    assert events["event_id"].tolist() == ["001004|2019-03-19", "001004|2019-07-10"]
    assert contract["unique_pre_identity_events"] == 2
    assert contract == shuffled_contract
    pd.testing.assert_frame_equal(events, shuffled)


def test_snapshot_only_master_returns_required_blocker(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "master.parquet",
        [{"gvkey": "001004", "cusip": "12345678A", "updated_at": "2026-03-07T11:03:59Z"}],
    )
    evidence = _evaluate(d1, source)
    report = evidence["dated_identifier_source"]
    assert evidence["status"] == "BLOCKED_DATED_COMPUSTAT_IDENTIFIER_SOURCE_ABSENT"
    assert report["effective_date_columns"] is None
    assert report["updated_at_profile"]["unique_non_null_values"] == 1
    assert report["updated_at_profile"]["authoritative_effective_date"] is False
    assert evidence["strict_pit_identifier_authority"] is False


def test_complete_unique_dated_source_passes(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [
            {"gvkey": "001004", "cusip": "11111111A", "effective_start": "2018-01-01", "effective_end": "2019-05-31"},
            {"gvkey": "001004", "cusip": "22222222B", "effective_start": "2019-06-01", "effective_end": None},
        ],
    )
    evidence = _evaluate(d1, source)
    coverage = evidence["dated_identifier_source"]["coverage"]
    assert evidence["status"] == id0.STATUS_PASS
    assert coverage["uniquely_covered_events"] == 2
    assert coverage["missing_events"] == 0
    assert coverage["canonical_event_identifier_mapping_sha256"]


def test_missing_interval_blocks_coverage(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [{"gvkey": "001004", "cusip": "11111111A", "effective_start": "2018-01-01", "effective_end": "2019-05-31"}],
    )
    evidence = _evaluate(d1, source)
    assert evidence["status"] == id0.STATUS_BLOCKED_COVERAGE
    assert evidence["dated_identifier_source"]["coverage"]["missing_events"] == 1


def test_overlapping_rows_block_ambiguity(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [
            {"gvkey": "001004", "cusip": "11111111A", "effective_start": "2018-01-01", "effective_end": None},
            {"gvkey": "001004", "cusip": "11111111A", "effective_start": "2019-01-01", "effective_end": None},
        ],
    )
    evidence = _evaluate(d1, source)
    assert evidence["status"] == id0.STATUS_BLOCKED_AMBIGUITY
    assert evidence["dated_identifier_source"]["coverage"]["overlapping_interval_events"] == 2


def test_invalid_interval_order_blocks_before_coverage(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [{"gvkey": "001004", "cusip": "11111111A", "effective_start": "2020-01-01", "effective_end": "2019-01-01"}],
    )
    evidence = _evaluate(d1, source)
    assert evidence["status"] == id0.STATUS_BLOCKED_INTERVALS
    assert evidence["dated_identifier_source"]["coverage"] is None


def test_d1_lock_mismatch_skips_source_evaluation(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(tmp_path / "master.parquet", [{"gvkey": "001004", "cusip": "11111111A"}])
    evidence = id0.evaluate_authority(
        d1_path=d1,
        identifier_source_path=source,
        expected_d1_sha256="0" * 64,
        expected_event_count=2,
        expected_event_set_sha256="0" * 64,
        expected_canonical_rows_sha256="0" * 64,
    )
    assert evidence["status"] == id0.STATUS_BLOCKED_D1_LOCK
    assert evidence["dated_identifier_source"]["evaluation_skipped"] is True


def test_explicit_effective_columns_require_a_pair(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    events, _ = id0.build_pre_identity_events(pd.read_parquet(d1))
    source = _source(tmp_path / "dated.parquet", [{"gvkey": "001004", "cusip": "11111111A", "valid_from": "2018-01-01"}])
    with pytest.raises(id0.M7F5ID0InputError, match="must_be_supplied_together"):
        id0.inspect_identifier_source(source, events, effective_start_column="valid_from")


def test_atomic_evidence_write_is_deterministic(tmp_path: Path) -> None:
    payload = id0._serialize_evidence({"status": id0.STATUS_BLOCKED_SOURCE_ABSENT})
    output = tmp_path / "evidence.json"
    id0._atomic_write_text(output, payload)
    first = output.read_bytes()
    id0._atomic_write_text(output, payload)
    assert output.read_bytes() == first
    assert not list(tmp_path.glob(f".{output.name}.*.tmp"))
