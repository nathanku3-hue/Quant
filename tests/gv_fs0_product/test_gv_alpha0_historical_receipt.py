from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "release/gv-alpha0/RECEIPT.json"
EXPECTED = {
    "release_tag": "gv-alpha0-paper-decision-v0.1.0",
    "source_commit": "a88ed05bbd360d8cc053f9ed835992c48958e7f5",
    "release_proof_tip": "93e7a55",
    "artifact_bytes": 18666047,
    "artifact_sha256": "67f5b154182be5d9cecf050934a81b107a8d38e9ea072f0df565dd6b24fe2d57",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_alpha0_release_is_historical_receipt_not_current_root_rebuild_contract() -> None:
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "gv_alpha0_historical_release_receipt_v1"
    assert payload["status"] == "FROZEN_HISTORICAL_RECEIPT_NO_CURRENT_ROOT_REBUILD_CONTRACT"
    for key, value in EXPECTED.items():
        assert payload[key] == value
    assert "current root source is not required to rebuild" in payload["claim_boundary"]

    for removed in ("alpha_app.py", "launch_alpha.py", "portfolio_app.py", "launch_portfolio.py"):
        assert not (ROOT / removed).exists()
    assert not (ROOT / "scripts/build_gv_alpha0_release.py").exists()
    assert not (ROOT / "scripts/smoke_gv_alpha0_release.py").exists()


def test_alpha0_tracked_receipt_files_match_frozen_hashes() -> None:
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    for relative, expected_hash in payload["tracked_receipt_files"].items():
        path = ROOT / "release/gv-alpha0" / relative
        assert path.is_file()
        assert _sha256(path) == expected_hash
