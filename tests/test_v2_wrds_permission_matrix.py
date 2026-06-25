from __future__ import annotations

import json

import pytest

from v2_discovery.data_lab.permission_matrix import PermissionMatrixError
from v2_discovery.data_lab.permission_matrix import DENIED_ACTIONS
from v2_discovery.data_lab.permission_matrix import WrdsPermissionEntry
from v2_discovery.data_lab.permission_matrix import build_default_wrds_permission_matrix
from v2_discovery.data_lab.permission_matrix import validate_permission_matrix_payload
from v2_discovery.data_lab.schema_registry import validate_permission_matrix_schema
from v2_discovery.data_lab.wrds_probe import build_wrds_permission_probe_contract
from v2_discovery.data_lab.wrds_probe import validate_wrds_permission_probe_contract


def test_v2_d0_default_permission_matrix_is_offline_contract_only():
    matrix = build_default_wrds_permission_matrix(created_at_utc="2026-06-01T00:00:00Z")
    payload = matrix.to_dict()

    validate_permission_matrix_payload(payload)
    validate_permission_matrix_schema(payload)

    assert payload["authority"] == "offline_contract_only"
    assert payload["provider"] == "wrds"
    assert payload["provider_access_allowed"] is False
    assert payload["snapshot_generation_allowed"] is False
    assert payload["data_output_allowed"] is False
    assert payload["v1_canonical_write_allowed"] is False
    assert {entry["dataset_id"] for entry in payload["entries"]} >= {
        "crsp_daily_stock_file",
        "crsp_stocknames",
        "compustat_fundamentals_quarterly",
        "ibes_detail_eps_us",
    }
    assert payload["denied_actions"] == list(DENIED_ACTIONS)
    assert "candidate_promotion" in payload["denied_actions"]
    assert "recommendations" in payload["denied_actions"]
    assert "sqlite_storage" in payload["denied_actions"]
    assert "safe_boot_claim" in payload["denied_actions"]
    assert "boot_ready_claim" in payload["denied_actions"]


def test_v2_d0_permission_matrix_rejects_provider_access_or_snapshot_generation():
    for value in (True, 0, None, ""):
        with pytest.raises(PermissionMatrixError, match="provider_access_allowed"):
            WrdsPermissionEntry(
                dataset_id="crsp_daily_stock_file",
                wrds_library="crsp",
                wrds_table="dsf",
                dataset_name="CRSP Daily Stock File",
                provider_access_allowed=value,
            )

    with pytest.raises(PermissionMatrixError, match="snapshot_generation_allowed"):
        WrdsPermissionEntry(
            dataset_id="crsp_daily_stock_file",
            wrds_library="crsp",
            wrds_table="dsf",
            dataset_name="CRSP Daily Stock File",
            snapshot_generation_allowed=True,
        )


def test_v2_d0_permission_matrix_requires_approval_ref_for_approved_status():
    with pytest.raises(PermissionMatrixError, match="approval_ref"):
        WrdsPermissionEntry(
            dataset_id="crsp_daily_stock_file",
            wrds_library="crsp",
            wrds_table="dsf",
            dataset_name="CRSP Daily Stock File",
            permission_status="approved",
        )


def test_v2_d0_permission_matrix_rejects_duplicate_dataset_ids():
    entry = WrdsPermissionEntry(
        dataset_id="crsp_daily_stock_file",
        wrds_library="crsp",
        wrds_table="dsf",
        dataset_name="CRSP Daily Stock File",
    )
    with pytest.raises(PermissionMatrixError, match="unique"):
        build_default_wrds_permission_matrix([entry, entry])


def test_v2_d0_schema_contract_rejects_widened_root_flags():
    payload = build_default_wrds_permission_matrix(
        created_at_utc="2026-06-01T00:00:00Z"
    ).to_dict()
    payload["provider_access_allowed"] = True

    with pytest.raises(Exception, match="provider_access_allowed|False"):
        validate_permission_matrix_schema(payload)
    with pytest.raises(PermissionMatrixError, match="provider_access_allowed"):
        validate_permission_matrix_payload(payload)


def test_v2_d0_schema_contract_rejects_missing_approval_ref_and_denied_action_drift():
    payload = build_default_wrds_permission_matrix(
        created_at_utc="2026-06-01T00:00:00Z"
    ).to_dict()
    payload["entries"][0]["permission_status"] = "approved"
    payload["entries"][0]["approval_ref"] = None

    with pytest.raises(Exception, match="approval_ref"):
        validate_permission_matrix_schema(payload)
    with pytest.raises(PermissionMatrixError, match="approval_ref"):
        validate_permission_matrix_payload(payload)

    payload = build_default_wrds_permission_matrix(
        created_at_utc="2026-06-01T00:00:00Z"
    ).to_dict()
    payload["denied_actions"] = payload["denied_actions"][:-1]

    with pytest.raises(Exception, match="denied_actions"):
        validate_permission_matrix_schema(payload)
    with pytest.raises(PermissionMatrixError, match="denied_actions"):
        validate_permission_matrix_payload(payload)


def test_v2_d0_permission_matrix_direct_validator_rejects_entry_extra_fields():
    payload = build_default_wrds_permission_matrix(
        created_at_utc="2026-06-01T00:00:00Z"
    ).to_dict()
    payload["entries"][0]["wrds_password"] = "not-for-repo"

    with pytest.raises(Exception, match="wrds_password"):
        validate_permission_matrix_schema(payload)
    with pytest.raises(PermissionMatrixError, match="wrds_password"):
        validate_permission_matrix_payload(payload)


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (lambda payload: payload.update({"provider": "WRDS"}), "provider"),
        (lambda payload: payload.update({"created_at_utc": 123}), "created_at_utc"),
        (lambda payload: payload["entries"][0].update({"dataset_id": 123}), "dataset_id"),
        (lambda payload: payload["entries"][0].update({"pit_required": "false"}), "pit_required"),
        (
            lambda payload: payload["entries"][0].update(
                {"allowed_uses": ["PROVENANCE_CONTRACT"]}
            ),
            "allowed_uses",
        ),
        (lambda payload: payload["entries"][0].update({"notes": [7]}), "notes"),
    ),
)
def test_v2_d0_permission_matrix_direct_validator_rejects_raw_payload_coercion(
    mutate,
    message,
):
    payload = build_default_wrds_permission_matrix(
        created_at_utc="2026-06-01T00:00:00Z"
    ).to_dict()
    mutate(payload)

    with pytest.raises(Exception, match=message):
        validate_permission_matrix_schema(payload)
    with pytest.raises(PermissionMatrixError, match=message):
        validate_permission_matrix_payload(payload)


def test_v2_d0_permission_matrix_rejects_constant_drift():
    payload = build_default_wrds_permission_matrix(
        created_at_utc="2026-06-01T00:00:00Z"
    ).to_dict()
    payload["matrix_id"] = "MUTATED"

    with pytest.raises(Exception, match="matrix_id"):
        validate_permission_matrix_schema(payload)
    with pytest.raises(PermissionMatrixError, match="matrix_id"):
        validate_permission_matrix_payload(payload)


def test_v2_d0_wrds_probe_contract_never_connects_or_outputs_data():
    matrix = build_default_wrds_permission_matrix(created_at_utc="2026-06-01T00:00:00Z")
    probe = build_wrds_permission_probe_contract(
        matrix,
        created_at_utc="2026-06-01T00:00:00Z",
    )

    validated = validate_wrds_permission_probe_contract(probe)
    text = json.dumps(validated, sort_keys=True).lower()

    assert validated["execution_mode"] == "offline_contract_only"
    assert validated["provider_access_allowed"] is False
    assert validated["wrds_connection_attempted"] is False
    assert validated["snapshot_generation_allowed"] is False
    assert validated["data_output_allowed"] is False
    assert validated["v1_canonical_write_allowed"] is False
    assert "record_permission_decision_only" == validated["next_allowed_action"]
    assert "score" not in text
    assert "rank" in text  # only as a denied action, never as output.
    assert "candidate_ranking" in validated["denied_actions"]


def test_v2_d0_wrds_probe_contract_rejects_root_drift():
    probe = build_wrds_permission_probe_contract(
        created_at_utc="2026-06-01T00:00:00Z",
    )

    for field, value, message in (
        ("next_allowed_action", "connect_to_wrds", "next_allowed_action"),
        ("denied_actions", probe["denied_actions"][:-1], "denied_actions"),
        ("code_ref", "v2_discovery/data_lab/wrds_probe.py@mutated", "code_ref"),
    ):
        payload = dict(probe)
        payload[field] = value
        with pytest.raises(PermissionMatrixError, match=message):
            validate_wrds_permission_probe_contract(payload)

    payload = dict(probe)
    payload["wrds_password"] = "not-for-repo"
    with pytest.raises(PermissionMatrixError, match="credential|unexpected"):
        validate_wrds_permission_probe_contract(payload)


def test_v2_d0_wrds_probe_contract_rejects_dataset_row_drift():
    probe = build_wrds_permission_probe_contract(
        created_at_utc="2026-06-01T00:00:00Z",
    )

    payload = dict(probe)
    payload["datasets"] = [dict(probe["datasets"][0], output_path="tmp/probe.json")]
    with pytest.raises(PermissionMatrixError, match="output|unexpected"):
        validate_wrds_permission_probe_contract(payload)

    payload = dict(probe)
    payload["datasets"] = [dict(probe["datasets"][0], wrds_table="")]
    with pytest.raises(PermissionMatrixError, match="wrds_table"):
        validate_wrds_permission_probe_contract(payload)

    payload = dict(probe)
    payload["datasets"] = [
        dict(
            probe["datasets"][0],
            permission_status="approved",
            approval_ref=None,
        )
    ]
    with pytest.raises(PermissionMatrixError, match="approval_ref"):
        validate_wrds_permission_probe_contract(payload)
