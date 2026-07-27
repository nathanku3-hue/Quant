from __future__ import annotations

from pathlib import Path

from core.gv_fs0_canonical import parse_canonical_document_bytes
from core.gv_one_case_delta import ROOT, verify_hosted_proof


RECEIPT_DIR = ROOT / "data/gv_one_case_delta/hosted_receipts/14b3773"
CANDIDATE_SHA = "14b37734b4ea0d5b4cb61f6bcea56accbd52ff87"
CANDIDATE_TREE = "54d24cf15a7f27f5399e2ac07ea603e4accf4738"


def _load(path: Path) -> dict:
    value = parse_canonical_document_bytes(path.read_bytes())
    assert isinstance(value, dict)
    return value


def test_hosted_receipt_is_signed_and_binds_exact_candidate() -> None:
    receipt = _load(RECEIPT_DIR / "hosted_proof.json")
    trusted = _load(RECEIPT_DIR / "trusted_proof_issuers.json")

    digest = verify_hosted_proof(
        receipt,
        candidate_sha=CANDIDATE_SHA,
        candidate_tree=CANDIDATE_TREE,
        trusted_proof_issuers=trusted,
    )

    assert digest == "246357afc2848f71d1252b79987ea8ba980c323a3be5e25751d3a9a8b78b283a"
    assert receipt["hosted_proof_hash"] == digest


def test_hosted_receipt_records_product_protocol_and_parity_green() -> None:
    receipt = _load(RECEIPT_DIR / "hosted_proof.json")
    payload = receipt["payload"]

    assert payload["product_workflow_run_id"] == "30285531998"
    assert payload["windows_run_id"] == "90042256003"
    assert payload["windows_conclusion"] == "SUCCESS"
    assert payload["linux_run_id"] == "90042256059"
    assert payload["linux_conclusion"] == "SUCCESS"
    assert payload["product_parity_job_id"] == "90043281214"
    assert payload["product_parity_conclusion"] == "SUCCESS"

    assert payload["protocol_workflow_run_id"] == "30285532512"
    assert payload["protocol_windows_job_id"] == "90042257227"
    assert payload["protocol_windows_conclusion"] == "SUCCESS"
    assert payload["protocol_linux_job_id"] == "90042257211"
    assert payload["protocol_linux_conclusion"] == "SUCCESS"
    assert payload["protocol_parity_job_id"] == "90042562009"
    assert payload["protocol_parity_conclusion"] == "SUCCESS"
