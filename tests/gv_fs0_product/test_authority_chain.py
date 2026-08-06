"""Authority-chain machine proof for GV-FS0-F1 product boundaries.

Lands in P0.5 before any F1A product module. When product modules appear, the
same tests AST-enforce the import graph. Until then, they prove the frozen
authority surfaces and forbidden legacy paths.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORITY_CHAIN = (
    "InstrumentId",
    "PortfolioBookEvent",
    "DecisionSnapshotId",
    "PortfolioAimId",
    "CertificationId",
)

REQUIRED_PRODUCT_CANON = (
    "docs/architecture/godview_endgame_vision.md",
    "docs/architecture/godview_portfolio_first_operating_model.md",
    "docs/architecture/godview_portfolio_p0_owner_freeze.md",
)

PRODUCT_MODULE_GLOBS = (
    "core/gv_fs0_*.py",
    "views/gv_fs0_*.py",
)

# Protocol primitive is allowed; product modules must not reverse authority.
ALLOWED_PRODUCT_IMPORT_PREFIXES = (
    "core.gv_fs0_canonical",
    "json",
    "pathlib",
    "dataclasses",
    "decimal",
    "datetime",
    "hashlib",
    "typing",
    "collections",
    "enum",
    "re",
    "sys",
    "os",
    "io",
    "copy",
    "functools",
    "itertools",
    "unicodedata",
)

FORBIDDEN_PRODUCT_IMPORT_PREFIXES = (
    "strategies",
    "validation.gv_fs0_reconstruction",
    "dashboard",
    "yfinance",
    "wrds",
)

FINAL_ADAPTER_REL = "views/gv_fs0_portfolio_adapter.py"
BRIEF_REL = "docs/phase_brief/gv-fs0-f1-product-slice-brief.md"
ROADMAP_REL = "docs/architecture/top_level_roadmap.md"
UOE_REL = "docs/architecture/unified_opportunity_engine.md"
VERIFIER_REL = "validation/gv_fs0_reconstruction.py"
LEGACY_REPLAY_REL = "strategies/strategy_replay.py"


def _read(rel: str) -> str:
    path = REPO_ROOT / rel
    assert path.is_file(), f"missing required path {rel}"
    return path.read_text(encoding="utf-8")


def _product_module_paths() -> list[Path]:
    paths: list[Path] = []
    for pattern in PRODUCT_MODULE_GLOBS:
        for path in REPO_ROOT.glob(pattern):
            if path.name == "gv_fs0_canonical.py":
                # Frozen protocol primitive, not a product module under F1 ownership.
                continue
            paths.append(path)
    return sorted(paths)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
    return names


def test_required_product_canons_declare_current_authority_disposition() -> None:
    for rel in REQUIRED_PRODUCT_CANON:
        text = _read(rel)
        assert "Status:" in text
        assert "Primary authority:" in text or "Primary sequence authority:" in text
    owner_freeze = _read("docs/architecture/godview_portfolio_p0_owner_freeze.md")
    assert "not the active Slice 0 fixture mandate" in owner_freeze


def test_roadmap_distinguishes_accepted_foundation_from_active_operated_phase() -> None:
    text = _read(ROADMAP_REL)
    assert text.splitlines()[0] == "# GodView Top-Level Roadmap"
    assert "PIT-SOURCE-AUTHORITY-1" in text
    assert "PIT-ALPHA-AUTHORITY-CUT-1" in text or "pit-alpha-authority-cut-1-terminal" in text
    assert "9af5259" in text
    assert "dashboard.py" in text
    assert "LIVE CLOSED" in text or "Limited Live" in text
    assert "70/100" in text
    assert "operability" in text.lower() and "custody" in text.lower() and "replay" in text.lower()
    assert "not an alpha" in text.lower() or "not alpha" in text.lower()
    assert "ACTIVE_SLICE = GV-MICRO-PORTFOLIO-VERTICAL-0" not in text
    assert "NEXT_GATE = GV-DETERMINISTIC-REPLAY-0" not in text
    assert "39/100" not in text
    assert "immutable" in text.lower()
    assert "market packet" in text.lower()


def test_e0_preregistration_authority_sources_exist_and_are_tracked() -> None:
    """Merge-safety: every frozen authority_sources path exists and is git-tracked.

    Provenance: paths are named by frozen e0_preregistration.yaml. Missing paths
    must be dispositioned (track with proven provenance OR amend the reference).
    Untracked dirty-root bytes alone do not satisfy this check.
    """

    import subprocess

    prereg = _read("docs/architecture/godview_e0/e0_preregistration.yaml")
    sources: list[str] = []
    for line in prereg.splitlines():
        stripped = line.strip()
        if stripped.startswith("- docs/"):
            sources.append(stripped[2:].strip())
    assert sources, "preregistration must declare authority_sources"
    tracked = subprocess.check_output(
        ["git", "ls-files", "--", *sources],
        cwd=REPO_ROOT,
        text=True,
    ).splitlines()
    tracked_set = {path.replace("\\", "/") for path in tracked}
    for rel in sources:
        path = REPO_ROOT / rel
        assert path.is_file(), f"missing preregistered authority source: {rel}"
        assert rel.replace("\\", "/") in tracked_set, (
            f"preregistered authority source is not git-tracked: {rel}"
        )


def test_uoe_engine_is_superseded_not_active_gate() -> None:
    text = _read(UOE_REL)
    head = "\n".join(text.splitlines()[:12])
    assert "SUPERSEDED" in head
    assert "historical" in head.lower()


def test_brief_uses_final_adapter_injection_not_throwaway_temp_route() -> None:
    text = _read(BRIEF_REL)
    assert "views/gv_fs0_portfolio_adapter.py" in text
    assert "inject" in text.lower()
    # Require explicit final-adapter contract; reject planned throwaway temp architecture.
    assert "Final adapter injection contract" in text or "final adapter" in text.lower()
    assert "throwaway" in text.lower() or "FORBIDDEN" in text
    # Must not schedule a disposable temp architecture as the F1A plan of record.
    assert "TEMP_UI_ID" not in text
    assert "temporary visible UI" not in text.lower() or "final adapter" in text.lower()


def test_brief_does_not_invent_unregistered_publication_codes() -> None:
    text = _read(BRIEF_REL)
    for code in (
        "PUBLICATION_LOCKED",
        "PUBLICATION_TARGET_CHANGED",
        "PUBLICATION_POST_REPLACE_VERIFICATION_FAILED",
        "PUBLICATION_RECOVERY_RECORD_FAILED",
    ):
        assert code in text
    # Only the four frozen publication codes may appear as PUBLICATION_* tokens.
    found = set(re.findall(r"PUBLICATION_[A-Z0-9_]+", text))
    allowed = {
        "PUBLICATION_LOCKED",
        "PUBLICATION_TARGET_CHANGED",
        "PUBLICATION_POST_REPLACE_VERIFICATION_FAILED",
        "PUBLICATION_RECOVERY_RECORD_FAILED",
    }
    assert found <= allowed, f"unregistered publication codes in brief: {sorted(found - allowed)}"


def test_frozen_verifier_remains_process_only_script() -> None:
    text = _read(VERIFIER_REL)
    assert "standard-library-only" in text or "stdlib" in text.lower() or "ISOLATED" in text
    tree = ast.parse(text, filename=VERIFIER_REL)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    # No repository package imports in the frozen verifier.
    for forbidden in ("core", "strategies", "views", "dashboard", "data"):
        assert forbidden not in imports


def test_legacy_strategy_replay_is_not_fs0_product_entry() -> None:
    """Legacy replay may exist, but product modules must not import it."""
    assert (REPO_ROOT / LEGACY_REPLAY_REL).is_file()
    legacy_text = _read(LEGACY_REPLAY_REL)
    assert '__authority__ = "REVOKED_BY_GV_FS0_20260716"' in legacy_text
    for path in _product_module_paths():
        imported = _imported_modules(path)
        for name in imported:
            assert not name.startswith("strategies.strategy_replay")
            assert name != "strategies"


def test_product_modules_respect_forbidden_import_prefixes() -> None:
    violations: list[str] = []
    for path in _product_module_paths():
        for name in _imported_modules(path):
            if any(name == p or name.startswith(p + ".") for p in FORBIDDEN_PRODUCT_IMPORT_PREFIXES):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {name}")
    assert violations == []


def test_final_adapter_when_present_is_injection_shaped() -> None:
    """If the final adapter file exists, require injection-friendly API surface."""
    adapter = REPO_ROOT / FINAL_ADAPTER_REL
    if not adapter.is_file():
        pytest.skip("final adapter not landed yet (allowed until F1A)")
    text = adapter.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(adapter))
    func_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    # Accept either explicit inject/render naming; reject temp-route naming.
    assert not any("temp" in name.lower() for name in func_names)
    assert any(
        key in text.lower()
        for key in ("inject", "presentation", "snapshot", "certification", "render")
    )
    imports = _imported_modules(adapter)
    for name in imports:
        assert not name.startswith("strategies")
        assert name != "validation.gv_fs0_reconstruction"


def test_no_throwaway_temp_adapter_files() -> None:
    forbidden_globs = (
        "views/gv_fs0*temp*",
        "views/*temp*fs0*",
        "views/gv_fs0_temp_*.py",
    )
    found: list[str] = []
    for pattern in forbidden_globs:
        found.extend(str(p.relative_to(REPO_ROOT)) for p in REPO_ROOT.glob(pattern))
    assert found == []
