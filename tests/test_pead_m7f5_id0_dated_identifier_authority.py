"""Focused tests for M7F5-ID0 dated-identifier authority."""
from __future__ import annotations

import os
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


def _evaluate(
    d1: Path,
    source: Path,
    *,
    bind_columns: bool = True,
) -> dict[str, object]:
    column_args = (
        {
            "identifier_column": "cusip",
            "effective_start_column": "effective_start",
            "effective_end_column": "effective_end",
        }
        if bind_columns
        else {}
    )
    return id0.evaluate_authority(
        d1_path=d1,
        identifier_source_path=source,
        **column_args,
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
    evidence = _evaluate(d1, source, bind_columns=False)
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


def test_detected_date_names_are_not_semantic_authority(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "relationship.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111A",
            "start_date": "2018-01-01",
            "end_date": None,
        }],
    )
    evidence = _evaluate(d1, source, bind_columns=False)
    report = evidence["dated_identifier_source"]
    assert evidence["status"] == id0.STATUS_BLOCKED_SCHEMA
    assert report["reason_codes"] == [
        "identifier_validity_columns_must_be_explicitly_bound"
    ]
    assert report["strict_pit_identifier_authority"] is False


@pytest.mark.parametrize("malformed_end", ["", "   ", "not-a-date"])
def test_malformed_non_null_end_never_becomes_open_ended(
    tmp_path: Path, malformed_end: str
) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111A",
            "effective_start": "2018-01-01",
            "effective_end": malformed_end,
        }],
    )
    evidence = _evaluate(d1, source)
    assert evidence["status"] == id0.STATUS_BLOCKED_INTERVALS
    assert evidence["dated_identifier_source"]["invalid_relevant_rows"] == 1


def test_overlong_identifier_is_rejected_instead_of_truncated(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": "1234567890",
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    evidence = _evaluate(d1, source)
    assert evidence["status"] == id0.STATUS_BLOCKED_INTERVALS


def test_mixed_missing_and_overlap_preserves_both_blockers(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [
            {
                "gvkey": "001004",
                "cusip": "11111111A",
                "effective_start": "2018-01-01",
                "effective_end": "2019-05-31",
            },
            {
                "gvkey": "001004",
                "cusip": "11111111A",
                "effective_start": "2019-01-01",
                "effective_end": "2019-05-31",
            },
        ],
    )
    evidence = _evaluate(d1, source)
    reasons = evidence["dated_identifier_source"]["reason_codes"]
    assert evidence["status"] == id0.STATUS_BLOCKED_AMBIGUITY
    assert "one_or_more_events_have_no_effective_identifier" in reasons
    assert "one_or_more_events_have_multiple_active_identifier_rows" in reasons


def test_non_finite_sue_is_ineligible_and_json_safe(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    frame = pd.read_parquet(d1)
    frame.loc[len(frame)] = {
        "gvkey": "009999",
        "rdq": "2019-08-01",
        "sue_price_scaled_clipped": float("inf"),
        "valid_sue": True,
    }
    events, contract = id0.build_pre_identity_events(frame)
    assert "009999|2019-08-01" not in set(events["event_id"])
    assert contract["unique_pre_identity_events"] == 2
    id0._serialize_evidence(contract)


def test_read_hash_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    hashes = iter(["before", "after"])
    monkeypatch.setattr(id0, "_sha256_file", lambda _path: next(hashes))
    with pytest.raises(id0.M7F5ID0InputError, match="d1_changed_during_read"):
        id0.inspect_d1_lock(d1)


@pytest.mark.parametrize("target", ["d1", "source"])
def test_output_cannot_alias_an_input(tmp_path: Path, target: str) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "source.parquet",
        [{"gvkey": "001004", "cusip": "11111111A"}],
    )
    output = d1 if target == "d1" else source
    before = output.read_bytes()
    exit_code = id0.main([
        "--d1", str(d1),
        "--identifier-source", str(source),
        "--output", str(output),
    ])
    assert exit_code == 2
    assert output.read_bytes() == before


def test_output_hardlink_alias_is_rejected(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "source.parquet",
        [{"gvkey": "001004", "cusip": "11111111A"}],
    )
    alias = tmp_path / "d1-alias.parquet"
    try:
        os.link(d1, alias)
    except OSError as exc:
        pytest.skip(f"hardlinks unavailable: {exc}")
    before = d1.read_bytes()
    assert id0.main([
        "--d1", str(d1),
        "--identifier-source", str(source),
        "--output", str(alias),
    ]) == 2
    assert d1.read_bytes() == before


def test_atomic_write_cleans_partial_when_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "evidence.json"

    def fail_replace(_self: Path, _target: Path) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        id0._atomic_write_text(output, "{}\n")
    assert not output.exists()
    assert not list(tmp_path.glob(f".{output.name}.*.tmp"))
