"""Focused tests for M7F5-ID0 dated-identifier authority."""
from __future__ import annotations

import inspect
import json
import os
import subprocess
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


def _provenance(
    path: Path,
    source: Path,
    *,
    gvkey_column: str = "gvkey",
    identifier_column: str = "cusip",
    identifier_type: str = "CUSIP",
    effective_start_column: str = "effective_start",
    effective_end_column: str = "effective_end",
    interval_meaning: str = "IDENTIFIER_VALIDITY",
    source_sha256: str | None = None,
) -> Path:
    payload = {
        "schema_version": id0.PROVENANCE_SCHEMA_VERSION,
        "declaration_type": id0.PROVENANCE_DECLARATION_TYPE,
        "dataset": {"name": "synthetic_compustat_identity", "version": "v1"},
        "source_sha256": source_sha256 or id0._sha256_file(source),
        "binding": {
            "gvkey_column": gvkey_column,
            "identifier_column": identifier_column,
            "identifier_type": identifier_type,
            "effective_start_column": effective_start_column,
            "effective_end_column": effective_end_column,
            "effective_interval_semantics": {
                "meaning": interval_meaning,
                "start_inclusive": True,
                "end_inclusive": True,
                "null_end_means_open_ended": True,
            },
        },
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _approval_payload(
    source: Path,
    envelope: Path,
    *,
    approval_scope: str = id0.APPROVAL_SCOPE,
    decision: str = id0.APPROVAL_DECISION,
    owner_identity: str = "Synthetic Data Owner",
    owner_role: str = id0.APPROVAL_DATA_OWNER_ROLE,
    approval_ref: str = "TEST-DATA-OWNER-APPROVAL-001",
    source_sha256: str | None = None,
    envelope_sha256: str | None = None,
    gvkey_column: str = "gvkey",
    identifier_column: str = "cusip",
    identifier_type: str = "CUSIP",
    effective_start_column: str = "effective_start",
    effective_end_column: str = "effective_end",
    interval_meaning: str = "IDENTIFIER_VALIDITY",
) -> dict[str, object]:
    return {
        "schema_version": id0.APPROVAL_SCHEMA_VERSION,
        "authority_type": id0.APPROVAL_AUTHORITY_TYPE,
        "approval_scope": approval_scope,
        "decision": decision,
        "owner": {"identity": owner_identity, "role": owner_role},
        "approval_ref": approval_ref,
        "provenance_envelope_sha256": envelope_sha256 or id0._sha256_file(envelope),
        "source_sha256": source_sha256 or id0._sha256_file(source),
        "dataset": {"name": "synthetic_compustat_identity", "version": "v1"},
        "binding": {
            "gvkey_column": gvkey_column,
            "identifier_column": identifier_column,
            "identifier_type": identifier_type,
            "effective_start_column": effective_start_column,
            "effective_end_column": effective_end_column,
            "effective_interval_semantics": {
                "meaning": interval_meaning,
                "start_inclusive": True,
                "end_inclusive": True,
                "null_end_means_open_ended": True,
            },
        },
    }


def _commit_approval(
    repository: Path,
    payload: dict[str, object],
    *,
    relative_path: str = "docs/authorization/m7f5/id0-test-approval.json",
) -> tuple[Path, str, str]:
    repository.mkdir(parents=True, exist_ok=True)
    _git(repository, "init", "-q")
    _git(repository, "config", "user.name", "M7F5 Test Owner")
    _git(repository, "config", "user.email", "m7f5-test@example.invalid")
    approval_file = repository / Path(relative_path)
    approval_file.parent.mkdir(parents=True, exist_ok=True)
    approval_file.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    _git(repository, "add", relative_path)
    _git(repository, "commit", "-q", "-m", "approve identifier source semantics")
    return repository, _git(repository, "rev-parse", "HEAD"), relative_path


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
    with_authority: bool = True,
    envelope_path: Path | None = None,
    approval_payload: dict[str, object] | None = None,
    approval_repository: Path | None = None,
    approval_commit: str | None = None,
    approval_path: str | None = None,
) -> dict[str, object]:
    if not with_authority:
        return id0.evaluate_authority(
            d1_path=d1,
            identifier_source_path=source,
            **_lock(d1),
        )
    if envelope_path is None:
        envelope_path = _provenance(source.with_suffix(".provenance.json"), source)
    if approval_repository is None:
        approval_repository = source.parent / f"{source.stem}-approval-repo"
    if approval_commit is None or approval_path is None:
        approval_repository, approval_commit, approval_path = _commit_approval(
            approval_repository,
            approval_payload or _approval_payload(source, envelope_path),
        )
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(id0, "APPROVAL_REPOSITORY_ROOT", approval_repository)
        return id0.evaluate_authority(
            d1_path=d1,
            identifier_source_path=source,
            provenance_envelope_path=envelope_path,
            approval_commit=approval_commit,
            approval_path=approval_path,
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
    evidence = _evaluate(d1, source, with_authority=False)
    report = evidence["dated_identifier_source"]
    assert evidence["status"] == id0.STATUS_BLOCKED_PROVENANCE
    assert report["effective_date_columns"] is None
    assert report["updated_at_profile"]["unique_non_null_values"] == 1
    assert report["updated_at_profile"]["authoritative_effective_date"] is False
    assert evidence["strict_pit_identifier_authority"] is False


def test_complete_unique_dated_source_passes(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [
            {"gvkey": "001004", "cusip": "11111111", "effective_start": "2018-01-01", "effective_end": "2019-05-31"},
            {"gvkey": "001004", "cusip": "22222222", "effective_start": "2019-06-01", "effective_end": None},
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
        [{"gvkey": "001004", "cusip": "11111111", "effective_start": "2018-01-01", "effective_end": "2019-05-31"}],
    )
    evidence = _evaluate(d1, source)
    assert evidence["status"] == id0.STATUS_BLOCKED_COVERAGE
    assert evidence["dated_identifier_source"]["coverage"]["missing_events"] == 1


def test_overlapping_rows_block_ambiguity(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [
            {"gvkey": "001004", "cusip": "11111111", "effective_start": "2018-01-01", "effective_end": None},
            {"gvkey": "001004", "cusip": "11111111", "effective_start": "2019-01-01", "effective_end": None},
        ],
    )
    evidence = _evaluate(d1, source)
    assert evidence["status"] == id0.STATUS_BLOCKED_AMBIGUITY
    assert evidence["dated_identifier_source"]["coverage"]["overlapping_interval_events"] == 2


def test_invalid_interval_order_blocks_before_coverage(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [{"gvkey": "001004", "cusip": "11111111", "effective_start": "2020-01-01", "effective_end": "2019-01-01"}],
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


def test_legacy_direct_column_authority_flags_are_removed() -> None:
    parser = id0._build_parser()
    option_strings = {
        option
        for action in parser._actions
        for option in action.option_strings
    }
    assert "--identifier-column" not in option_strings
    assert "--effective-start-column" not in option_strings
    assert "--effective-end-column" not in option_strings
    assert "--provenance-envelope" in option_strings
    assert "--approval-commit" in option_strings
    assert "--approval-path" in option_strings
    assert "--approval-file" not in option_strings
    assert "--approval-repository" not in option_strings
    assert "approval_repository_root" not in inspect.signature(
        id0.evaluate_authority
    ).parameters


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
            "cusip": "11111111",
            "start_date": "2018-01-01",
            "end_date": None,
        }],
    )
    evidence = _evaluate(d1, source, with_authority=False)
    report = evidence["dated_identifier_source"]
    assert evidence["status"] == id0.STATUS_BLOCKED_PROVENANCE
    assert report["reason_codes"] == [
        "committed_git_blob_data_owner_approval_required"
    ]
    assert report["strict_pit_identifier_authority"] is False


def test_unrelated_employment_intervals_cannot_self_authorize(
    tmp_path: Path,
) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "employment.parquet",
        [
            {
                "gvkey": "001004",
                "cusip": "11111111",
                "employment_start": "2018-01-01",
                "employment_end": "2019-05-31",
            },
            {
                "gvkey": "001004",
                "cusip": "22222222",
                "employment_start": "2019-06-01",
                "employment_end": None,
            },
        ],
    )
    evidence = _evaluate(d1, source, with_authority=False)
    assert evidence["status"] == id0.STATUS_BLOCKED_PROVENANCE
    assert evidence["strict_pit_identifier_authority"] is False
    assert evidence["dated_identifier_source"]["coverage"] is None


def test_provenance_source_hash_mismatch_blocks_before_coverage(
    tmp_path: Path,
) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111",
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    envelope = _provenance(
        tmp_path / "source.provenance.json",
        source,
        source_sha256="0" * 64,
    )
    evidence = _evaluate(d1, source, envelope_path=envelope)
    report = evidence["dated_identifier_source"]
    assert evidence["status"] == id0.STATUS_BLOCKED_PROVENANCE
    assert "provenance_source_sha256_mismatch" in report["reason_codes"]
    assert report["coverage"] is None
    assert report["provenance_envelope"]["verified"] is False


def test_non_identifier_interval_attestation_blocks(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "employment.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111",
            "employment_start": "2018-01-01",
            "employment_end": None,
        }],
    )
    envelope = _provenance(
        tmp_path / "source.provenance.json",
        source,
        effective_start_column="employment_start",
        effective_end_column="employment_end",
        interval_meaning="EMPLOYMENT_VALIDITY",
    )
    evidence = _evaluate(d1, source, envelope_path=envelope)
    assert evidence["status"] == id0.STATUS_BLOCKED_PROVENANCE
    assert (
        "effective_interval_semantics_are_not_identifier_validity"
        in evidence["dated_identifier_source"]["reason_codes"]
    )


def test_duplicate_provenance_keys_are_rejected(tmp_path: Path) -> None:
    envelope = tmp_path / "duplicate.json"
    envelope.write_text(
        '{"schema_version":"x","source_sha256":"%s",'
        '"source_sha256":"%s"}' % ("0" * 64, "1" * 64),
        encoding="utf-8",
    )
    with pytest.raises(id0.M7F5ID0InputError, match="duplicate_key"):
        id0._read_json_file(envelope, label="provenance_envelope")


def test_caller_attestation_inside_envelope_is_rejected(tmp_path: Path) -> None:
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111",
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    envelope = _provenance(tmp_path / "source.provenance.json", source)
    payload = json.loads(envelope.read_text(encoding="utf-8"))
    payload["attestation"] = {
        "data_owner": "Caller Invented Owner",
        "approval_ref": "CALLER-INVENTED-APPROVAL",
    }
    envelope.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    with pytest.raises(id0.M7F5ID0InputError, match="unexpected_keys"):
        id0._parse_provenance_envelope(envelope)


def test_envelope_without_committed_approval_is_input_error(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111",
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    envelope = _provenance(tmp_path / "source.provenance.json", source)
    with pytest.raises(id0.M7F5ID0InputError, match="required_together"):
        id0.evaluate_authority(
            d1_path=d1,
            identifier_source_path=source,
            provenance_envelope_path=envelope,
            **_lock(d1),
        )


@pytest.mark.parametrize(
    ("approval_overrides", "expected_reason"),
    [
        ({"approval_scope": "OTHER_SCOPE"}, "approval_scope_mismatch"),
        ({"owner_role": "CALLER"}, "approval_owner_role_is_not_data_owner"),
        ({"source_sha256": "0" * 64}, "approval_source_sha256_mismatch"),
        (
            {"envelope_sha256": "0" * 64},
            "approval_provenance_envelope_sha256_mismatch",
        ),
        (
            {"interval_meaning": "EMPLOYMENT_VALIDITY"},
            "approval_binding_mismatch:interval_meaning",
        ),
    ],
)
def test_committed_approval_binding_mismatch_blocks(
    tmp_path: Path,
    approval_overrides: dict[str, object],
    expected_reason: str,
) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [
            {
                "gvkey": "001004",
                "cusip": "11111111",
                "effective_start": "2018-01-01",
                "effective_end": "2019-05-31",
            },
            {
                "gvkey": "001004",
                "cusip": "22222222",
                "effective_start": "2019-06-01",
                "effective_end": None,
            },
        ],
    )
    envelope = _provenance(tmp_path / "source.provenance.json", source)
    approval = _approval_payload(source, envelope, **approval_overrides)
    evidence = _evaluate(
        d1,
        source,
        envelope_path=envelope,
        approval_payload=approval,
    )
    assert evidence["status"] == id0.STATUS_BLOCKED_PROVENANCE
    assert expected_reason in evidence["dated_identifier_source"]["reason_codes"]
    assert evidence["dated_identifier_source"]["coverage"] is None


def test_approval_blob_change_at_head_revokes_authority(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111",
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    envelope = _provenance(tmp_path / "source.provenance.json", source)
    repository, commit, approval_path = _commit_approval(
        tmp_path / "approval-repo",
        _approval_payload(source, envelope),
    )
    approval_file = repository / Path(approval_path)
    changed = json.loads(approval_file.read_text(encoding="utf-8"))
    changed["decision"] = "REVOKED"
    approval_file.write_text(json.dumps(changed, sort_keys=True), encoding="utf-8")
    _git(repository, "add", approval_path)
    _git(repository, "commit", "-q", "-m", "revoke approval")
    with pytest.raises(id0.M7F5ID0InputError, match="changed_or_revoked"):
        _evaluate(
            d1,
            source,
            envelope_path=envelope,
            approval_repository=repository,
            approval_commit=commit,
            approval_path=approval_path,
        )


def test_approval_path_must_be_under_docs_authorization(tmp_path: Path) -> None:
    repository = tmp_path / "approval-repo"
    repository.mkdir()
    _git(repository, "init", "-q")
    _git(repository, "config", "user.name", "M7F5 Test Owner")
    _git(repository, "config", "user.email", "m7f5-test@example.invalid")
    outside = repository / "approval.json"
    outside.write_text("{}", encoding="utf-8")
    _git(repository, "add", "approval.json")
    _git(repository, "commit", "-q", "-m", "invalid approval location")
    with pytest.raises(id0.M7F5ID0InputError, match="docs_authorization"):
        id0._read_git_blob_approval(
            repository,
            approval_commit=_git(repository, "rev-parse", "HEAD"),
            approval_path="approval.json",
        )


def test_duplicate_keys_in_committed_approval_are_rejected(tmp_path: Path) -> None:
    repository = tmp_path / "approval-repo"
    repository.mkdir()
    _git(repository, "init", "-q")
    _git(repository, "config", "user.name", "M7F5 Test Owner")
    _git(repository, "config", "user.email", "m7f5-test@example.invalid")
    approval_path = "docs/authorization/m7f5/duplicate.json"
    approval_file = repository / Path(approval_path)
    approval_file.parent.mkdir(parents=True)
    approval_file.write_text(
        '{"schema_version":"x","schema_version":"y"}',
        encoding="utf-8",
    )
    _git(repository, "add", approval_path)
    _git(repository, "commit", "-q", "-m", "duplicate approval keys")
    with pytest.raises(id0.M7F5ID0InputError, match="authority_approval_duplicate_key"):
        id0._read_git_blob_approval(
            repository,
            approval_commit=_git(repository, "rev-parse", "HEAD"),
            approval_path=approval_path,
        )


def test_approval_commit_must_be_reachable_from_head(tmp_path: Path) -> None:
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111",
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    envelope = _provenance(tmp_path / "source.provenance.json", source)
    repository, approval_commit, approval_path = _commit_approval(
        tmp_path / "approval-repo",
        _approval_payload(source, envelope),
    )
    approval_bytes = (repository / Path(approval_path)).read_bytes()
    _git(repository, "checkout", "-q", "--orphan", "unrelated")
    _git(repository, "rm", "-q", "-rf", ".")
    approval_file = repository / Path(approval_path)
    approval_file.parent.mkdir(parents=True, exist_ok=True)
    approval_file.write_bytes(approval_bytes)
    _git(repository, "add", approval_path)
    _git(repository, "commit", "-q", "-m", "unrelated approval history")
    with pytest.raises(id0.M7F5ID0InputError, match="not_reachable_from_head"):
        id0._read_git_blob_approval(
            repository,
            approval_commit=approval_commit,
            approval_path=approval_path,
        )


def test_ambient_git_dir_cannot_redirect_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111",
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    envelope = _provenance(tmp_path / "source.provenance.json", source)
    repository, commit, approval_path = _commit_approval(
        tmp_path / "approval-repo",
        _approval_payload(source, envelope),
    )
    redirect = tmp_path / "redirect-repo"
    redirect.mkdir()
    _git(redirect, "init", "-q")
    monkeypatch.setenv("GIT_DIR", str(redirect / ".git"))
    approval, report = id0._read_git_blob_approval(
        repository,
        approval_commit=commit,
        approval_path=approval_path,
    )
    assert approval["approval_ref"] == "TEST-DATA-OWNER-APPROVAL-001"
    assert report["commit"] == commit


def test_missing_provenance_bound_column_blocks_schema(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111",
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    envelope = _provenance(
        tmp_path / "source.provenance.json",
        source,
        effective_start_column="employment_start",
    )
    evidence = _evaluate(
        d1,
        source,
        envelope_path=envelope,
        approval_payload=_approval_payload(
            source,
            envelope,
            effective_start_column="employment_start",
        ),
    )
    assert evidence["status"] == id0.STATUS_BLOCKED_SCHEMA
    assert evidence["dated_identifier_source"]["reason_codes"] == [
        "provenance_bound_effective_start_column_missing"
    ]


@pytest.mark.parametrize("malformed_end", ["", "   ", "not-a-date"])
def test_malformed_non_null_end_never_becomes_open_ended(
    tmp_path: Path, malformed_end: str
) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111",
            "effective_start": "2018-01-01",
            "effective_end": malformed_end,
        }],
    )
    evidence = _evaluate(d1, source)
    assert evidence["status"] == id0.STATUS_BLOCKED_INTERVALS
    assert evidence["dated_identifier_source"]["invalid_relevant_rows"] == 1


@pytest.mark.parametrize(
    "malformed_identifier",
    [
        "1234567890",
        "12345678!",
        "1234-5678A",
        "1234 5678A",
        "037833101",
        "03783310A",
        "1234567ſ",
        "1234567ı",
        "123456ß",
    ],
)
def test_malformed_identifier_is_rejected_instead_of_rewritten(
    tmp_path: Path, malformed_identifier: str
) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": malformed_identifier,
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    evidence = _evaluate(d1, source)
    assert evidence["status"] == id0.STATUS_BLOCKED_INTERVALS


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        ("03783310", "03783310"),
        ("037833100", "03783310"),
        ("037833101", None),
        ("03783310A", None),
    ],
)
def test_cusip9_requires_numeric_computed_check_digit(
    identifier: str, expected: str | None
) -> None:
    normalized = id0._normalize_identifier8(
        pd.Series([identifier]), identifier_type="CUSIP"
    ).iloc[0]
    if expected is None:
        assert pd.isna(normalized)
    else:
        assert normalized == expected


def test_numeric_identifier_dtype_cannot_gain_lexical_authority(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "numeric-identifier.parquet",
        [{
            "gvkey": "001004",
            "cusip": 12345678,
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    evidence = _evaluate(d1, source)
    assert evidence["status"] == id0.STATUS_BLOCKED_INTERVALS
    assert evidence["strict_pit_identifier_authority"] is False
    assert evidence["dated_identifier_source"]["invalid_relevant_rows"] == 1


def test_categorical_identifier_dtype_is_not_implicitly_lexical() -> None:
    normalized = id0._normalize_identifier8(
        pd.Series(pd.Categorical(["037833100"])),
        identifier_type="CUSIP",
    )
    assert normalized.isna().all()


def test_list_typed_identifier_blocks_without_crashing_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    events, contract = id0.build_pre_identity_events(pd.read_parquet(d1))
    source = _source(
        tmp_path / "list-identifier.parquet",
        [{
            "gvkey": "001004",
            "cusip": ["037833100", "594918104"],
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    d1_report = {
        "verified": True,
        "mismatches": [],
        **contract,
    }
    monkeypatch.setattr(
        id0,
        "inspect_d1_lock",
        lambda *_args, **_kwargs: (events, d1_report),
    )
    envelope = _provenance(tmp_path / "source.provenance.json", source)
    approval_repository, approval_commit, approval_path = _commit_approval(
        tmp_path / "approval-repo",
        _approval_payload(source, envelope),
    )
    monkeypatch.setattr(id0, "APPROVAL_REPOSITORY_ROOT", approval_repository)
    exit_code = id0.main([
        "--d1", str(d1),
        "--identifier-source", str(source),
        "--provenance-envelope", str(envelope),
        "--approval-commit", approval_commit,
        "--approval-path", approval_path,
    ])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert id0.STATUS_BLOCKED_INTERVALS in captured.out
    assert "Traceback" not in captured.out


def test_mixed_missing_and_overlap_preserves_both_blockers(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "dated.parquet",
        [
            {
                "gvkey": "001004",
                "cusip": "11111111",
                "effective_start": "2018-01-01",
                "effective_end": "2019-05-31",
            },
            {
                "gvkey": "001004",
                "cusip": "11111111",
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


def test_read_and_hash_use_same_private_snapshot_under_aba_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    original_frame = pd.read_parquet(d1)
    original_bytes = d1.read_bytes()
    replacement = _d1(tmp_path / "replacement.parquet")
    replacement_frame = pd.read_parquet(replacement)
    replacement_frame.loc[0, "gvkey"] = "999999"
    replacement_frame.to_parquet(replacement, index=False)
    replacement_bytes = replacement.read_bytes()
    real_read_parquet = pd.read_parquet

    def aba_read(snapshot_path: Path) -> pd.DataFrame:
        d1.write_bytes(replacement_bytes)
        parsed = real_read_parquet(snapshot_path)
        d1.write_bytes(original_bytes)
        return parsed

    monkeypatch.setattr(pd, "read_parquet", aba_read)
    parsed, reported_sha = id0._read_parquet_with_stable_sha256(d1, label="d1")
    pd.testing.assert_frame_equal(parsed, original_frame)
    assert reported_sha == id0._sha256_file(d1)


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_envelope_bindings_cannot_gain_authority(
    tmp_path: Path, blank: str
) -> None:
    source = _source(
        tmp_path / "dated.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111A",
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    envelope = _provenance(
        tmp_path / "source.provenance.json",
        source,
        effective_start_column=blank,
    )
    with pytest.raises(id0.M7F5ID0InputError, match="must_be_non_empty_string"):
        id0._parse_provenance_envelope(envelope)


def test_provenance_envelope_must_be_detached_from_source(
    tmp_path: Path,
) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "source.parquet",
        [{"gvkey": "001004", "cusip": "11111111A"}],
    )
    with pytest.raises(id0.M7F5ID0InputError, match="must_be_detached"):
        id0.evaluate_authority(
            d1_path=d1,
            identifier_source_path=source,
            provenance_envelope_path=source,
            **_lock(d1),
        )


def test_output_cannot_alias_provenance_envelope(tmp_path: Path) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "source.parquet",
        [{
            "gvkey": "001004",
            "cusip": "11111111",
            "effective_start": "2018-01-01",
            "effective_end": None,
        }],
    )
    envelope = _provenance(tmp_path / "source.provenance.json", source)
    before = envelope.read_bytes()
    assert id0.main([
        "--d1", str(d1),
        "--identifier-source", str(source),
        "--provenance-envelope", str(envelope),
        "--output", str(envelope),
    ]) == 2
    assert envelope.read_bytes() == before


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


def test_output_write_failure_is_controlled(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    d1 = _d1(tmp_path / "d1.parquet")
    source = _source(
        tmp_path / "source.parquet",
        [{"gvkey": "001004", "cusip": "11111111A"}],
    )
    output_directory = tmp_path / "existing-directory"
    output_directory.mkdir()
    exit_code = id0.main([
        "--d1", str(d1),
        "--identifier-source", str(source),
        "--output", str(output_directory),
    ])
    captured = capsys.readouterr()
    assert exit_code == 3
    assert captured.out == ""
    assert captured.err.startswith("M7F5_ID0_OUTPUT_ERROR:")
    assert "Traceback" not in captured.err
