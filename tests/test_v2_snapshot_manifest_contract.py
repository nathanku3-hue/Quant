from __future__ import annotations

import pytest

from v2_discovery.data_lab.permission_matrix import build_default_wrds_permission_matrix
from v2_discovery.data_lab.schema_registry import validate_snapshot_manifest_schema
from v2_discovery.data_lab.snapshot_manifest import SnapshotManifestError
from v2_discovery.data_lab.snapshot_manifest import build_wrds_snapshot_manifest
from v2_discovery.data_lab.snapshot_manifest import validate_snapshot_manifest_payload


def test_v2_d0_snapshot_manifest_is_contract_only_and_schema_valid():
    matrix = build_default_wrds_permission_matrix(created_at_utc="2026-06-01T00:00:00Z")
    manifest = build_wrds_snapshot_manifest(
        matrix,
        created_at_utc="2026-06-01T00:00:00Z",
    )
    payload = manifest.to_dict()

    validate_snapshot_manifest_payload(payload)
    validate_snapshot_manifest_schema(payload)

    assert payload["manifest_status"] == "contract_only"
    assert payload["provider"] == "wrds"
    assert payload["provider_access_allowed"] is False
    assert payload["snapshot_generation_allowed"] is False
    assert payload["committed_wrds_output_allowed"] is False
    assert payload["data_output_allowed"] is False
    assert payload["v1_canonical_write_allowed"] is False
    assert payload["planned_storage_uri"].startswith("data/runtime_cache/v2_data_lab/")
    assert payload["permission_matrix_sha256"] == matrix.stable_hash()
    assert payload["pit_policy"]["no_future_leakage"] is True
    assert payload["pit_policy"]["release_date_required"] is True
    assert payload["pit_policy"]["manifest_hash_required"] is True


def test_v2_d0_snapshot_manifest_blocks_v1_canonical_or_boot_paths():
    matrix = build_default_wrds_permission_matrix(created_at_utc="2026-06-01T00:00:00Z")

    for bad_uri in (
        "data/processed/wrds_snapshot.parquet",
        "data/registry/wrds_snapshot.parquet",
        "runtime/boot_status_current.json",
        "docs/context/boot_status_current.json",
        "/tmp/wrds_snapshot.parquet",
        "/data/processed/wrds_snapshot.parquet",
        "C:/tmp/wrds_snapshot.parquet",
        "E:\\Code\\Quant\\data\\processed\\wrds_snapshot.parquet",
        "\\\\server\\share\\data\\processed\\wrds_snapshot.parquet",
        "file:///tmp/wrds_snapshot.parquet",
    ):
        with pytest.raises(SnapshotManifestError, match="planned_storage_uri"):
            build_wrds_snapshot_manifest(matrix, planned_storage_uri=bad_uri)


def test_v2_d0_snapshot_manifest_storage_uri_matches_schema_contract():
    matrix = build_default_wrds_permission_matrix(created_at_utc="2026-06-01T00:00:00Z")

    for good_uri in (
        "data/runtime_cache/v2_data_lab/wrds_snapshots/v2_d0_contract_only/",
        "data/runtime_cache/v2_data_lab/probe_contract_only",
    ):
        payload = build_wrds_snapshot_manifest(
            matrix,
            planned_storage_uri=good_uri,
            created_at_utc="2026-06-01T00:00:00Z",
        ).to_dict()

        validate_snapshot_manifest_payload(payload)
        validate_snapshot_manifest_schema(payload)

    with pytest.raises(SnapshotManifestError, match="planned_storage_uri"):
        build_wrds_snapshot_manifest(
            matrix,
            planned_storage_uri="data/runtime_cache/v2_data_lab",
            created_at_utc="2026-06-01T00:00:00Z",
        )


def test_v2_d0_snapshot_manifest_rejects_snapshot_generation_flag():
    payload = build_wrds_snapshot_manifest(
        created_at_utc="2026-06-01T00:00:00Z",
    ).to_dict()
    payload["snapshot_generation_allowed"] = True

    with pytest.raises(Exception, match="snapshot_generation_allowed|False"):
        validate_snapshot_manifest_schema(payload)
    with pytest.raises(SnapshotManifestError, match="snapshot_generation_allowed"):
        validate_snapshot_manifest_payload(payload)

    payload = build_wrds_snapshot_manifest(
        created_at_utc="2026-06-01T00:00:00Z",
    ).to_dict()
    payload["snapshot_generation_allowed"] = 0
    with pytest.raises(SnapshotManifestError, match="snapshot_generation_allowed"):
        validate_snapshot_manifest_payload(payload)


def test_v2_d0_snapshot_manifest_requires_pit_no_future_leakage_policy():
    payload = build_wrds_snapshot_manifest(
        created_at_utc="2026-06-01T00:00:00Z",
    ).to_dict()
    payload["pit_policy"]["no_future_leakage"] = False

    with pytest.raises(Exception, match="no_future_leakage|True"):
        validate_snapshot_manifest_schema(payload)
    with pytest.raises(SnapshotManifestError, match="no_future_leakage"):
        validate_snapshot_manifest_payload(payload)

    payload = build_wrds_snapshot_manifest(
        created_at_utc="2026-06-01T00:00:00Z",
    ).to_dict()
    payload["pit_policy"]["unexpected"] = True
    with pytest.raises(Exception, match="pit_policy|unexpected"):
        validate_snapshot_manifest_schema(payload)
    with pytest.raises(SnapshotManifestError, match="unexpected"):
        validate_snapshot_manifest_payload(payload)


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (lambda row: row.update({"output_path": "tmp/probe.json"}), "output_path"),
        (lambda row: row.pop("effective_date_field"), "effective_date_field"),
    ),
)
def test_v2_d0_snapshot_manifest_direct_validator_rejects_dataset_row_key_drift(
    mutate,
    message,
):
    payload = build_wrds_snapshot_manifest(
        created_at_utc="2026-06-01T00:00:00Z",
    ).to_dict()
    mutate(payload["datasets"][0])

    with pytest.raises(Exception, match=message):
        validate_snapshot_manifest_schema(payload)
    with pytest.raises(SnapshotManifestError, match=message):
        validate_snapshot_manifest_payload(payload)


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (lambda payload: payload.update({"provider": "WRDS"}), "provider"),
        (
            lambda payload: payload.update(
                {"permission_matrix_sha256": payload["permission_matrix_sha256"].upper()}
            ),
            "permission_matrix_sha256",
        ),
        (
            lambda payload: payload.update(
                {"schema_registry_uri": "contracts\\data_snapshot\\wrds_snapshot_manifest.schema.json"}
            ),
            "schema_registry_uri",
        ),
        (lambda payload: payload.update({"created_at_utc": 123}), "created_at_utc"),
        (lambda payload: payload["datasets"][0].update({"permission_status": "bogus"}), "permission_status"),
        (lambda payload: payload["datasets"][0].update({"dataset_id": 123}), "dataset_id"),
        (lambda payload: payload["datasets"][0].update({"primary_key": [123]}), "primary_key"),
        (lambda payload: payload["datasets"][0].update({"release_date_field": 123}), "release_date_field"),
    ),
)
def test_v2_d0_snapshot_manifest_direct_validator_rejects_raw_payload_coercion(
    mutate,
    message,
):
    payload = build_wrds_snapshot_manifest(
        created_at_utc="2026-06-01T00:00:00Z",
    ).to_dict()
    mutate(payload)

    with pytest.raises(Exception, match=message):
        validate_snapshot_manifest_schema(payload)
    with pytest.raises(SnapshotManifestError, match=message):
        validate_snapshot_manifest_payload(payload)


def test_v2_d0_snapshot_manifest_rejects_constant_and_denied_action_drift():
    payload = build_wrds_snapshot_manifest(
        created_at_utc="2026-06-01T00:00:00Z",
    ).to_dict()
    payload["schema_version"] = "2.0.0"

    with pytest.raises(Exception, match="schema_version"):
        validate_snapshot_manifest_schema(payload)
    with pytest.raises(SnapshotManifestError, match="schema_version"):
        validate_snapshot_manifest_payload(payload)

    payload = build_wrds_snapshot_manifest(
        created_at_utc="2026-06-01T00:00:00Z",
    ).to_dict()
    payload["denied_actions"] = payload["denied_actions"][:-1]

    with pytest.raises(Exception, match="denied_actions"):
        validate_snapshot_manifest_schema(payload)
    with pytest.raises(SnapshotManifestError, match="denied_actions"):
        validate_snapshot_manifest_payload(payload)


def test_v2_d0_snapshot_manifest_records_release_date_fields_for_fundamental_sources():
    payload = build_wrds_snapshot_manifest(
        created_at_utc="2026-06-01T00:00:00Z",
    ).to_dict()
    rows = {row["dataset_id"]: row for row in payload["datasets"]}

    assert rows["compustat_fundamentals_quarterly"]["release_date_field"] == "rdq"
    assert "rdq" in rows["compustat_fundamentals_quarterly"]["point_in_time_fields"]
    assert rows["ibes_detail_eps_us"]["release_date_field"] == "anndats"
    assert "revdats" in rows["ibes_detail_eps_us"]["point_in_time_fields"]
