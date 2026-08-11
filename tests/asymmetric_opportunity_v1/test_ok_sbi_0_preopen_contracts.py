from __future__ import annotations

import json
from pathlib import Path

from research.asymmetric_opportunity_v1.preopen_freeze import (
    CONSTITUTION,
    SLICE_ID,
    build_machine_freeze,
)
from research.asymmetric_opportunity_v1.q_source_contract import Q_SOURCE_BLOCKED


REPO = Path(__file__).resolve().parents[2]


def test_build_machine_freeze_honest_blockers() -> None:
    freeze = build_machine_freeze(repo_root=REPO)
    assert freeze["slice_id"] == SLICE_ID
    assert freeze["spec_version"] == "v1.2"
    assert freeze["runnable_evaluation"] is False
    assert freeze["blocked_field_count"] > 0
    assert freeze["outcome_open_authorized"] is False
    assert freeze["Q_feasibility"] == Q_SOURCE_BLOCKED
    assert freeze["q_amendment_cycles_used"] == 0
    assert freeze["authorization"]["OK_SBI_0_DEV_OPEN_1"] == "NOT_ISSUED"
    assert freeze["authorization"]["financial_alpha_evidence"] == 0
    assert freeze["constitution"] == CONSTITUTION
    assert "outcome_join" in freeze["forbidden_this_turn"]
    assert freeze["step5_label_packs"]["join_forbidden"] is True
    assert freeze["step6_contracts"]["arms"]["constraints"]["composite_trophy"] == "FORBIDDEN"
    # Upstream K0A hashes bound when files present.
    assert freeze["step4_numeric_gates"]["denominator_hash"] != "BLOCKED_UNSET"
    assert "K_t_schedule" in freeze["blocked_fields"]


def test_authority_docs_landed() -> None:
    paths = [
        REPO / "docs" / "architecture" / "ok_sbi_0_sparse_basis_identification_v1_2.md",
        REPO / "docs" / "architecture" / "ok_sbi_0_release_hardening_v1_2.md",
        REPO / "docs" / "architecture" / "orthogonalization_contract_v1.md",
        REPO
        / "docs"
        / "context"
        / "e2e_evidence"
        / "ao_k0a_orthogonal_basis_preflight_20260811.json",
    ]
    for path in paths:
        assert path.is_file(), path


def test_freeze_script_roundtrip(tmp_path: Path) -> None:
    from scripts.ok_sbi_0_preopen_freeze import main as freeze_main
    import sys

    freeze_out = tmp_path / "ok_sbi_0_machine_freeze_v1_2.json"
    schema_out = tmp_path / "ok_sbi_0_claim_receipt_schema_v1_2.json"
    argv = sys.argv
    try:
        sys.argv = [
            "ok_sbi_0_preopen_freeze.py",
            "--repo-root",
            str(REPO),
            "--freeze-out",
            str(freeze_out),
            "--claim-schema-out",
            str(schema_out),
        ]
        assert freeze_main() == 0
    finally:
        sys.argv = argv

    freeze = json.loads(freeze_out.read_text(encoding="utf-8"))
    schema = json.loads(schema_out.read_text(encoding="utf-8"))
    assert freeze["blocked_field_count"] == len(freeze["blocked_fields"])
    assert freeze["runnable_evaluation"] is False
    assert "ledger_id" in schema["required_fields"]
    assert schema["schema_id"] == "OkSbi0ClaimReceiptSchemaV1"
