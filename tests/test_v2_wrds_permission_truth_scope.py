from __future__ import annotations

import json

import pytest

from v2_discovery.data_lab.permission_matrix import ALLOWED_USE_PROVENANCE_CONTRACT
from v2_discovery.data_lab.permission_truth import ENTITLEMENT_STATUS_APPROVED
from v2_discovery.data_lab.permission_truth import ENTITLEMENT_STATUS_PENDING
from v2_discovery.data_lab.permission_truth import PEAD_STARTER_SCOPE_NOT_REQUESTED
from v2_discovery.data_lab.permission_truth import PEAD_STARTER_SCOPE_REQUESTED
from v2_discovery.data_lab.permission_truth import PermissionTruthError
from v2_discovery.data_lab.permission_truth import V2D01PermissionTruthRow
from v2_discovery.data_lab.permission_truth import V2D01PermissionTruthScope
from v2_discovery.data_lab.permission_truth import build_v2_d0_1_permission_truth_scope
from v2_discovery.data_lab.permission_truth import validate_v2_d0_1_permission_truth_payload


EXPECTED_TABLES = (
    "crsp.dsf",
    "crsp.stocknames",
    "crsp.ccmxpf_linktable",
    "comp.fundq",
    "ibes.det_epsus",
)


def _payload() -> dict:
    return build_v2_d0_1_permission_truth_scope(
        created_at_utc="2026-06-02T00:00:00Z",
    ).to_dict()


def test_v2_d0_1_permission_truth_default_rows_split_entitlement_from_pead_scope():
    payload = _payload()
    validated = validate_v2_d0_1_permission_truth_payload(payload)

    assert validated.stable_hash()
    assert payload["authority"] == "offline_contract_only"
    assert payload["provider"] == "wrds"
    assert payload["provider_access_allowed"] is False
    assert payload["snapshot_generation_allowed"] is False
    assert payload["data_output_allowed"] is False
    assert payload["v1_canonical_write_allowed"] is False
    assert [f"{row['wrds_library']}.{row['wrds_table']}" for row in payload["rows"]] == list(
        EXPECTED_TABLES
    )
    assert len(payload["rows"]) == 5

    rows_by_table = {f"{row['wrds_library']}.{row['wrds_table']}": row for row in payload["rows"]}
    for table in EXPECTED_TABLES:
        row = rows_by_table[table]
        assert row["allowed_uses"] == [ALLOWED_USE_PROVENANCE_CONTRACT]
        assert row["v2_d0_1_entitlement_status"] == ENTITLEMENT_STATUS_PENDING
        assert row["approval_ref"] is None
        assert row["provider_access_allowed"] is False
        assert row["snapshot_generation_allowed"] is False
        assert row["data_output_allowed"] is False
        assert row["v1_canonical_write_allowed"] is False

    assert rows_by_table["ibes.det_epsus"]["v2_d0_1_entitlement_status"] == ENTITLEMENT_STATUS_PENDING
    assert rows_by_table["ibes.det_epsus"]["pead_v2_001_starter_scope"] == (
        PEAD_STARTER_SCOPE_NOT_REQUESTED
    )
    assert {
        table
        for table, row in rows_by_table.items()
        if row["pead_v2_001_starter_scope"] == PEAD_STARTER_SCOPE_REQUESTED
    } == {
        "crsp.dsf",
        "crsp.stocknames",
        "crsp.ccmxpf_linktable",
        "comp.fundq",
    }
    assert "read_only_permission_probe" not in json.dumps(payload, sort_keys=True)
    assert "schema_discovery" not in json.dumps(payload, sort_keys=True)
    assert "pit_snapshot_design" not in json.dumps(payload, sort_keys=True)


def test_v2_d0_1_permission_truth_approves_only_rows_with_table_specific_ref():
    payload = build_v2_d0_1_permission_truth_scope(
        approval_refs={
            "crsp.dsf": "APPROVAL-CRSP-DSF-20260602",
            "ibes_detail_eps_us": "APPROVAL-IBES-DET-EPSUS-20260602",
        },
        created_at_utc="2026-06-02T00:00:00Z",
    ).to_dict()

    validated = validate_v2_d0_1_permission_truth_payload(payload).to_dict()
    rows_by_table = {f"{row['wrds_library']}.{row['wrds_table']}": row for row in validated["rows"]}

    assert rows_by_table["crsp.dsf"]["v2_d0_1_entitlement_status"] == ENTITLEMENT_STATUS_APPROVED
    assert rows_by_table["crsp.dsf"]["approval_ref"] == "APPROVAL-CRSP-DSF-20260602"
    assert rows_by_table["ibes.det_epsus"]["v2_d0_1_entitlement_status"] == (
        ENTITLEMENT_STATUS_APPROVED
    )
    assert rows_by_table["ibes.det_epsus"]["approval_ref"] == "APPROVAL-IBES-DET-EPSUS-20260602"
    assert rows_by_table["ibes.det_epsus"]["pead_v2_001_starter_scope"] == (
        PEAD_STARTER_SCOPE_NOT_REQUESTED
    )
    assert rows_by_table["comp.fundq"]["v2_d0_1_entitlement_status"] == ENTITLEMENT_STATUS_PENDING


def test_v2_d0_1_permission_truth_rejects_approved_without_approval_ref():
    with pytest.raises(PermissionTruthError, match="approval_ref"):
        V2D01PermissionTruthRow(
            dataset_id="crsp_daily_stock_file",
            wrds_library="crsp",
            wrds_table="dsf",
            dataset_name="CRSP Daily Stock File",
            pead_v2_001_starter_scope=PEAD_STARTER_SCOPE_REQUESTED,
            v2_d0_1_entitlement_status=ENTITLEMENT_STATUS_APPROVED,
        )

    payload = _payload()
    payload["rows"][0]["v2_d0_1_entitlement_status"] = ENTITLEMENT_STATUS_APPROVED
    payload["rows"][0]["approval_ref"] = None

    with pytest.raises(PermissionTruthError, match="approval_ref"):
        validate_v2_d0_1_permission_truth_payload(payload)


def test_v2_d0_1_permission_truth_rejects_non_exact_rows_and_duplicates():
    payload = _payload()
    payload["rows"] = payload["rows"][:-1]

    with pytest.raises(PermissionTruthError, match="exactly five"):
        validate_v2_d0_1_permission_truth_payload(payload)

    payload = _payload()
    payload["rows"][1]["dataset_id"] = payload["rows"][0]["dataset_id"]
    with pytest.raises(PermissionTruthError, match="unique"):
        validate_v2_d0_1_permission_truth_payload(payload)

    payload = _payload()
    payload["rows"][1]["wrds_library"] = payload["rows"][0]["wrds_library"]
    payload["rows"][1]["wrds_table"] = payload["rows"][0]["wrds_table"]
    with pytest.raises(PermissionTruthError, match="unique"):
        validate_v2_d0_1_permission_truth_payload(payload)


def test_v2_d0_1_permission_truth_rejects_status_scope_and_allowed_use_drift():
    payload = _payload()
    payload["rows"][4]["pead_v2_001_starter_scope"] = PEAD_STARTER_SCOPE_REQUESTED
    with pytest.raises(PermissionTruthError, match="ibes_detail_eps_us|pead_v2_001"):
        validate_v2_d0_1_permission_truth_payload(payload)

    payload = _payload()
    payload["rows"][0]["v2_d0_1_entitlement_status"] = "unknown"
    with pytest.raises(PermissionTruthError, match="entitlement_status"):
        validate_v2_d0_1_permission_truth_payload(payload)

    payload = _payload()
    payload["rows"][0]["allowed_uses"] = [
        "read_only_permission_probe",
        ALLOWED_USE_PROVENANCE_CONTRACT,
    ]
    with pytest.raises(PermissionTruthError, match="allowed_uses"):
        validate_v2_d0_1_permission_truth_payload(payload)


def test_v2_d0_1_permission_truth_rejects_root_and_row_shape_drift():
    payload = _payload()
    payload["query"] = "select * from crsp.dsf"
    with pytest.raises(PermissionTruthError, match="query|unexpected"):
        validate_v2_d0_1_permission_truth_payload(payload)

    payload = _payload()
    payload["provider"] = "WRDS"
    with pytest.raises(PermissionTruthError, match="provider"):
        validate_v2_d0_1_permission_truth_payload(payload)

    payload = _payload()
    payload["provider_access_allowed"] = True
    with pytest.raises(PermissionTruthError, match="provider_access_allowed"):
        validate_v2_d0_1_permission_truth_payload(payload)

    payload = _payload()
    payload["rows"][0]["credential_ref"] = "not-allowed"
    with pytest.raises(PermissionTruthError, match="credential|unexpected"):
        validate_v2_d0_1_permission_truth_payload(payload)

    payload = _payload()
    payload["rows"][0]["output_path"] = "data/processed/wrds.parquet"
    with pytest.raises(PermissionTruthError, match="output|unexpected"):
        validate_v2_d0_1_permission_truth_payload(payload)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("schema_version", "2.0.0", "schema_version"),
        ("artifact_id", "MUTATED", "artifact_id"),
        ("scope_id", "MUTATED", "scope_id"),
        ("authority", "provider_probe", "authority"),
        ("code_ref", "v2_discovery/data_lab/permission_truth.py@mutated", "code_ref"),
        ("denied_actions", [], "denied_actions"),
    ),
)
def test_v2_d0_1_permission_truth_rejects_root_constant_drift(field, value, message):
    payload = _payload()
    payload[field] = value

    with pytest.raises(PermissionTruthError, match=message):
        validate_v2_d0_1_permission_truth_payload(payload)


def test_v2_d0_1_permission_truth_builder_rejects_unknown_approval_refs():
    with pytest.raises(PermissionTruthError, match="unknown"):
        build_v2_d0_1_permission_truth_scope(
            approval_refs={"crsp.msf": "APPROVAL-NOT-IN-SCOPE-20260602"},
        )

    with pytest.raises(PermissionTruthError, match="non-empty string"):
        build_v2_d0_1_permission_truth_scope(
            approval_refs={"crsp.dsf": 123},
        )


def test_v2_d0_1_permission_truth_dataclass_rejects_manual_row_scope_widening():
    rows = tuple(
        V2D01PermissionTruthRow.from_dict(row)
        for row in build_v2_d0_1_permission_truth_scope().to_dict()["rows"]
    )
    widened = rows[:-1] + (
        V2D01PermissionTruthRow(
            dataset_id="ibes_detail_eps_us",
            wrds_library="ibes",
            wrds_table="det_epsus",
            dataset_name="IBES Detail EPS US",
            pead_v2_001_starter_scope=PEAD_STARTER_SCOPE_REQUESTED,
        ),
    )

    with pytest.raises(PermissionTruthError, match="ibes_detail_eps_us|pead_v2_001"):
        V2D01PermissionTruthScope(rows=widened)
