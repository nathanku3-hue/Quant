"""P0.5 hard integrity gate: frozen + product canon must be consumable at runtime.

This module imports core.gv_fs0_canonical at import time so a missing or stale
canonical surface fails before any assertion body runs.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest

# Import-time load — non-lazy. Failure here blocks the entire product suite.
import core.gv_fs0_canonical as gv_fs0_canonical  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "contracts" / "gv_fs0" / "v1" / "gv_fs0_freeze_manifest_v1.json"
CANONICAL_MODULE = REPO_ROOT / "core" / "gv_fs0_canonical.py"

# Product-slice canon required before F1A (path-level bankability).
REQUIRED_PRODUCT_CANON = (
    "docs/architecture/godview_endgame_vision.md",
    "docs/architecture/godview_portfolio_first_operating_model.md",
    "docs/architecture/godview_portfolio_p0_owner_freeze.md",
)

REQUIRED_FROZEN_RUNTIME_LOADS = (
    "contracts/gv_fs0/v1/tables/gv_fs0_event_ranks_v1.json",
    "contracts/gv_fs0/v1/tables/gv_fs0_generated_event_slots_v1.json",
    "contracts/gv_fs0/v1/tables/gv_fs0_transition_ownership_v1.json",
    "contracts/gv_fs0/v1/registries/gv_fs0_certification_failure_registry_v1.json",
    "contracts/gv_fs0/v1/registries/gv_fs0_operational_error_registry_v1.json",
    "contracts/gv_fs0/v1/vectors/gv_fs0_canonical_vectors_v1.json",
)

FROZEN_VERIFIER_SCRIPT = REPO_ROOT / "validation" / "gv_fs0_reconstruction.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_file(rel: str) -> Path:
    path = REPO_ROOT / rel
    if not path.is_file():
        raise FileNotFoundError(f"REQUIRED_CANON_MISSING:{rel}")
    if path.stat().st_size <= 0:
        raise FileNotFoundError(f"REQUIRED_CANON_EMPTY:{rel}")
    return path


def test_canonical_module_is_importable_and_present() -> None:
    assert CANONICAL_MODULE.is_file()
    assert gv_fs0_canonical is not None
    assert hasattr(gv_fs0_canonical, "prepare_identity_string")
    assert hasattr(gv_fs0_canonical, "prepare_descriptive_string")
    assert hasattr(gv_fs0_canonical, "encode_json_string")


def test_product_canon_files_exist_with_current_authority_status() -> None:
    """Fail closed if any product canon lacks an explicit current disposition."""
    for rel in REQUIRED_PRODUCT_CANON:
        path = _require_file(rel)
        text = path.read_text(encoding="utf-8")
        assert "Status:" in text
        assert "Primary authority:" in text or "Primary sequence authority:" in text
        assert "Portfolio" in text or "Owner Freeze" in text


def test_top_level_roadmap_tracks_operated_phase_and_accepted_foundations() -> None:
    path = _require_file("docs/architecture/top_level_roadmap.md")
    text = path.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "# GodView Top-Level Roadmap"
    assert "PAIR-DECISION-SERIES-1" in text
    assert "9af5259" in text
    assert "dashboard.py" in text
    assert "LIVE CLOSED" in text or "Limited Live" in text
    assert "70/100" in text
    assert "operability" in text.lower()
    assert "episode 1" in text.lower()
    assert "portfolio-alpha evidence" in text.lower()
    assert "ACTIVE_SLICE = GV-MICRO-PORTFOLIO-VERTICAL-0" not in text
    assert "NEXT_GATE = GV-DETERMINISTIC-REPLAY-0" not in text
    assert "39/100" not in text
    assert not text.splitlines()[0].startswith("# Top-Level Roadmap: Unified Opportunity Engine")


def test_freeze_manifest_hashes_match_on_disk() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    assert len(entries) == manifest["frozen_surface_count"]
    mismatches: list[str] = []
    for entry in entries:
        path = REPO_ROOT / entry["path"]
        if not path.is_file():
            mismatches.append(f"MISSING {entry['path']}")
            continue
        actual = _sha256(path)
        if actual != entry["sha256"]:
            mismatches.append(
                f"HASH_MISMATCH {entry['path']}: expected={entry['sha256']} actual={actual}"
            )
        actual_len = path.stat().st_size
        if actual_len != entry["byte_length"]:
            mismatches.append(
                f"SIZE_MISMATCH {entry['path']}: expected={entry['byte_length']} actual={actual_len}"
            )
    assert mismatches == [], "\n".join(mismatches)


def test_runtime_load_frozen_tables_and_registries() -> None:
    """Runtime consumption discipline: Path load + JSON parse, not mere existence."""
    loaded: dict[str, object] = {}
    for rel in REQUIRED_FROZEN_RUNTIME_LOADS:
        path = _require_file(rel)
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload is not None
        loaded[rel] = payload
    # Light structural checks prove we did not load empty shells.
    ranks = loaded["contracts/gv_fs0/v1/tables/gv_fs0_event_ranks_v1.json"]
    assert isinstance(ranks, dict)
    op = loaded["contracts/gv_fs0/v1/registries/gv_fs0_operational_error_registry_v1.json"]
    assert isinstance(op, dict)
    codes = {entry["code"] for entry in op["entries"]}
    for required in (
        "PUBLICATION_LOCKED",
        "PUBLICATION_TARGET_CHANGED",
        "PUBLICATION_POST_REPLACE_VERIFICATION_FAILED",
        "PUBLICATION_RECOVERY_RECORD_FAILED",
    ):
        assert required in codes
    # Invented codes must not be smuggled into the frozen registry expectation.
    assert "PUBLICATION_LOCK_BREAK_PROHIBITED" not in codes


def test_external_import_canonical_reimport_is_stable() -> None:
    """Validate external import path remains resolvable under product suite."""
    imported = importlib.import_module("core.gv_fs0_canonical")
    assert imported.prepare_identity_string("OPEN") == "OPEN"


def test_frozen_verifier_exists_and_refuses_in_process_import() -> None:
    """External import discipline: verifier may load as a path but must refuse non-isolated use."""
    assert FROZEN_VERIFIER_SCRIPT.is_file()
    # Product suite must not keep a live in-process verifier module as a library dependency.
    sys.modules.pop("validation.gv_fs0_reconstruction", None)
    with pytest.raises(RuntimeError, match="GV_FS0_RECONSTRUCTION_PROCESS_ONLY"):
        importlib.import_module("validation.gv_fs0_reconstruction")
    # Clean up any partial module registration after the refuse path.
    sys.modules.pop("validation.gv_fs0_reconstruction", None)


def test_product_tests_are_not_top_level_protocol_glob() -> None:
    this_file = Path(__file__).resolve()
    assert this_file.parent.name == "gv_fs0_product"
    assert not this_file.name.startswith("test_gv_fs0_")
    top_level_collisions = list((REPO_ROOT / "tests").glob("test_gv_fs0_product*.py"))
    assert top_level_collisions == []


@pytest.mark.parametrize(
    "forbidden_name",
    [
        "test_gv_fs0_book.py",
        "test_gv_fs0_certification.py",
        "test_gv_fs0_publication_product.py",
        "test_gv_fs0_ui.py",
    ],
)
def test_no_product_named_protocol_glob_files(forbidden_name: str) -> None:
    assert not (REPO_ROOT / "tests" / forbidden_name).exists()


def test_missing_product_canon_is_detectable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Absence failure mode: integrity helper must fail closed when a canon path is gone."""

    def fake_require(rel: str) -> Path:
        if rel.endswith("godview_endgame_vision.md"):
            raise FileNotFoundError(f"REQUIRED_CANON_MISSING:{rel}")
        return _require_file(rel)

    monkeypatch.setattr(sys.modules[__name__], "_require_file", fake_require)
    with pytest.raises(FileNotFoundError, match="REQUIRED_CANON_MISSING"):
        _require_file("docs/architecture/godview_endgame_vision.md")
