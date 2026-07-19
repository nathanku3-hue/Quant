"""GV-E0A operable cutover: custody → HOLD_FOR_EVIDENCE → paper NO_POSITION."""

from __future__ import annotations

import ast
import hashlib
import inspect
import re
from pathlib import Path
from typing import Any

import pytest

from core.gv_e0a_operable import (
    E0A_DECISION_ID,
    E0A_PORTFOLIO_ACTION,
    E0A_RESEARCH_ACTION,
    E0_CUSTODY_SHA256,
    RATIONALE_REF_PREFIX,
    GvE0aOperableError,
    build_e0a_book,
    build_e0a_certified_result,
    build_e0a_research_decision,
    e0a_rationale_ref,
    publish_e0a_current_decision,
    verify_e0_custody,
)
from core.gv_fs0_canonical import canonical_document_bytes
from core.gv_fs0_current_decision import parse_current_decision_bytes
from core.gv_fs0_publish import (
    DEFAULT_CURRENT_DECISION_TARGET,
    publish_current_decision,
)
from views.gv_fs0_portfolio_adapter import (
    GvFs0PresentationError,
    load_current_certified_decision,
    render_gv_fs0_current_decision,
)

ROOT = Path(__file__).resolve().parents[2]

# Mandatory tracked current-decision identities (hosted parity pins these).
EXPECTED_RESEARCH_DECISION_HASH = (
    "b4694a69bd1bc35a0d97a839ad47b66b517da1bd0f4abccd56bacca22d9e8e38"
)
EXPECTED_CERTIFIED_RESULT_HASH = (
    "627c136926ecf947f2ea00f24de85291d44ef5594016f022fac7f2217093d6e6"
)
EXPECTED_CURRENT_FILE_SHA256 = (
    "7ba9c7c48dfc89ceae2a5a88aba8bfebbe6d5032272b0d254f4139478699b5c9"
)
EXPECTED_CURRENT_BYTE_LENGTH = 23_696
EXPECTED_RATIONALE_REF = f"{RATIONALE_REF_PREFIX}{EXPECTED_RESEARCH_DECISION_HASH}"


class FakeRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def subheader(self, body: str) -> None:
        self.calls.append(("subheader", body))

    def table(self, data: Any) -> None:
        self.calls.append(("table", data))

    def caption(self, body: str) -> None:
        self.calls.append(("caption", body))


def _current_paths(tmp_path: Path) -> tuple[Path, Path]:
    target = tmp_path / "data" / "gv_fs0" / "gv_fs0_current_decision.json"
    lock = target.parent / ".gv_fs0_current_decision.lock"
    return target, lock


def test_preregistered_authority_sources_exist_in_committed_tree() -> None:
    """Every authority_sources path in frozen preregistration must exist on disk."""
    prereg = ROOT / "docs" / "architecture" / "godview_e0" / "e0_preregistration.yaml"
    text = prereg.read_text(encoding="utf-8")
    # Minimal parse: list items under the authority_sources key only.
    lines = text.splitlines()
    in_block = False
    sources: list[str] = []
    for line in lines:
        if re.match(r"^  authority_sources:\s*$", line):
            in_block = True
            continue
        if in_block:
            m = re.match(r"^    - (.+)$", line)
            if m:
                sources.append(m.group(1).strip())
                continue
            if line.startswith("  ") and not line.startswith("    "):
                break
            if not line.startswith(" "):
                break
    assert sources, "authority_sources must be non-empty in frozen preregistration"
    missing = [rel for rel in sources if not (ROOT / rel).is_file()]
    assert missing == [], f"preregistered authority_sources missing from tree: {missing}"


def test_no_e0a_rationale_ref_compatibility_alias() -> None:
    import core.gv_e0a_operable as mod

    assert not hasattr(mod, "E0A_RATIONALE_REF")
    with pytest.raises(AttributeError):
        getattr(mod, "E0A_RATIONALE_REF")


def test_e0_custody_hash_gate_passes_on_frozen_bytes() -> None:
    verified = verify_e0_custody(ROOT)
    assert len(verified) == 4
    for name, expected in E0_CUSTODY_SHA256.items():
        assert verified[name] == expected
        path = ROOT / "docs" / "architecture" / "godview_e0" / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_e0_custody_hash_gate_fails_closed_on_tamper(tmp_path: Path) -> None:
    custody = tmp_path / "docs" / "architecture" / "godview_e0"
    custody.mkdir(parents=True)
    for name, expected in E0_CUSTODY_SHA256.items():
        src = ROOT / "docs" / "architecture" / "godview_e0" / name
        dest = custody / name
        if name == "e0_model_spec.md":
            dest.write_bytes(src.read_bytes() + b"\n# tamper\n")
        else:
            dest.write_bytes(src.read_bytes())
            assert hashlib.sha256(dest.read_bytes()).hexdigest() == expected
    with pytest.raises(GvE0aOperableError, match="E0_CUSTODY_HASH_MISMATCH"):
        verify_e0_custody(tmp_path)


def test_research_decision_is_hash_addressed_and_deep_frozen() -> None:
    research = build_e0a_research_decision(root=ROOT)
    assert research["research_action"] == E0A_RESEARCH_ACTION
    assert research["portfolio_action"] == E0A_PORTFOLIO_ACTION
    assert research["subject"] == "MU"
    assert research["module"] == "G_supply"
    assert research["decision_id"] == E0A_DECISION_ID
    assert research["alpha_claim"] is False
    assert "claim_boundary" in research
    assert set(research["custody_hashes"]) == set(E0_CUSTODY_SHA256)
    for name, digest in E0_CUSTODY_SHA256.items():
        assert research["custody_hashes"][name] == digest

    rd_hash = research["research_decision_hash"]
    assert isinstance(rd_hash, str) and len(rd_hash) == 64
    assert research["rationale_ref"] == f"{RATIONALE_REF_PREFIX}{rd_hash}"
    assert research["rationale_ref"] == e0a_rationale_ref(root=ROOT)

    # Deep freeze: top-level and nested custody map reject mutation.
    with pytest.raises(TypeError):
        research["research_action"] = "ADVANCE_TO_FULL_RESEARCH"  # type: ignore[index]
    with pytest.raises(TypeError):
        research["custody_hashes"]["e0_model_spec.md"] = "0" * 64  # type: ignore[index]


def test_research_hold_for_evidence_maps_to_portfolio_no_position() -> None:
    research = build_e0a_research_decision(root=ROOT)
    book = build_e0a_book(root=ROOT)
    assert book.decision.action == E0A_PORTFOLIO_ACTION
    assert book.decision.decision_id == E0A_DECISION_ID
    assert book.decision.rationale_ref == research["rationale_ref"]
    assert book.decision.requested_quantity is None
    assert all(row["shares"] == 0 for row in book.book.snapshots)
    assert all(row["nav"] == "1000" for row in book.book.snapshots)


def test_e0a_certification_binds_research_custody_hash() -> None:
    research = build_e0a_research_decision(root=ROOT)
    result = build_e0a_certified_result(root=ROOT)
    assert result["role"] == "NO_POSITION"
    assert result["decision"]["decision_id"] == E0A_DECISION_ID
    assert result["decision"]["action"] == "NO_POSITION"
    assert result["decision"]["rationale_ref"] == research["rationale_ref"]
    assert result["decision"]["rationale_ref"].startswith(RATIONALE_REF_PREFIX)
    assert (
        result["decision"]["rationale_ref"]
        == f"{RATIONALE_REF_PREFIX}{research['research_decision_hash']}"
    )
    assert result["certification"]["certification_status"] == "CERTIFIED"
    assert all(value == "TRUE" for value in result["certification"]["checks"].values())
    rows = {row["label"]: row["value"] for row in result["presentation"]["rows"]}
    assert rows["Action"] == "NO_POSITION"
    assert rows["Shares"] == "0"
    assert rows["NAV"] == "1000"
    assert rows["Rationale"] == research["rationale_ref"]


def test_publish_e0a_rejects_result_injection_parameter() -> None:
    """Production publish must not accept a caller-supplied certified result."""
    params = inspect.signature(publish_e0a_current_decision).parameters
    assert "result" not in params
    assert "custody_hashes" not in params
    assert "require_custody" not in params


def test_atomic_publish_current_decision_and_idempotent(tmp_path: Path) -> None:
    target, lock = _current_paths(tmp_path)
    result = build_e0a_certified_result(root=ROOT)
    first = publish_current_decision(result, target=target, lock_path=lock)
    assert first.status == "REPLACED"
    assert target.is_file()
    assert not lock.exists()
    loaded = parse_current_decision_bytes(target.read_bytes())
    assert loaded["decision"]["decision_id"] == E0A_DECISION_ID
    assert loaded["certified_decision_result_hash"] == first.certified_decision_result_hash

    before = target.stat().st_mtime_ns
    second = publish_current_decision(result, target=target, lock_path=lock)
    assert second.status == "IDEMPOTENT"
    assert target.stat().st_mtime_ns == before
    assert not lock.exists()


def test_publish_e0a_operator_path_always_rechecks_custody(tmp_path: Path) -> None:
    target, lock = _current_paths(tmp_path)
    research = build_e0a_research_decision(root=ROOT)
    publication = publish_e0a_current_decision(
        target=target,
        lock_path=lock,
        root=ROOT,
    )
    assert publication.status == "REPLACED"
    component = load_current_certified_decision(target)
    assert component["decision"]["decision_id"] == E0A_DECISION_ID
    assert component["decision"]["rationale_ref"] == research["rationale_ref"]


def test_publish_e0a_fails_when_custody_tampered(tmp_path: Path) -> None:
    """Even with a valid target, tampered custody under root blocks publication."""
    # Plant valid-looking E0 files under a fake root, then tamper one.
    custody = tmp_path / "docs" / "architecture" / "godview_e0"
    custody.mkdir(parents=True)
    for name in E0_CUSTODY_SHA256:
        src = ROOT / "docs" / "architecture" / "godview_e0" / name
        (custody / name).write_bytes(src.read_bytes())
    (custody / "e0_preregistration.yaml").write_bytes(b"tampered\n")

    target, lock = _current_paths(tmp_path)
    with pytest.raises(GvE0aOperableError, match="E0_CUSTODY_HASH_MISMATCH"):
        publish_e0a_current_decision(target=target, lock_path=lock, root=tmp_path)
    assert not target.exists()


def test_adapter_renders_exactly_one_title_and_table(tmp_path: Path) -> None:
    target, lock = _current_paths(tmp_path)
    research = build_e0a_research_decision(root=ROOT)
    publish_e0a_current_decision(target=target, lock_path=lock, root=ROOT)
    renderer = FakeRenderer()
    model = render_gv_fs0_current_decision(renderer, decision_path=target)
    assert model["title"] == "GV-FS0 Certified Paper Portfolio — NO_POSITION"
    assert [name for name, _ in renderer.calls] == ["subheader", "table", "caption"]
    assert sum(1 for name, _ in renderer.calls if name == "subheader") == 1
    assert sum(1 for name, _ in renderer.calls if name == "table") == 1
    rows = {row["label"]: row["value"] for row in model["rows"]}
    assert rows["Action"] == "NO_POSITION"
    assert rows["Rationale"] == research["rationale_ref"]


def test_adapter_fails_closed_without_current_decision(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(GvFs0PresentationError, match="CURRENT_DECISION_UNAVAILABLE"):
        render_gv_fs0_current_decision(FakeRenderer(), decision_path=missing)


def test_adapter_rejects_non_canonical_bytes(tmp_path: Path) -> None:
    """Publisher identity requires canonical bytes; adapter must share that gate."""
    target, lock = _current_paths(tmp_path)
    publish_e0a_current_decision(target=target, lock_path=lock, root=ROOT)
    # Pretty-printed object may schema-validate but is not canonical identity.
    pretty = (
        b'{\n  "schema_version": "gv_fs0_certified_decision_result_v1"\n}\n'
    )
    target.write_bytes(pretty)
    with pytest.raises(GvFs0PresentationError, match="CURRENT_DECISION_INVALID"):
        load_current_certified_decision(target)

    # Also reject: object re-encoded with extra whitespace after valid publish
    # by rewriting valid content with non-canonical JSON dumps.
    publish_e0a_current_decision(target=target, lock_path=lock, root=ROOT)
    validated = parse_current_decision_bytes(target.read_bytes())
    import json

    non_canonical = (
        json.dumps(validated, indent=2, sort_keys=False).encode("utf-8") + b"\n"
    )
    assert non_canonical != canonical_document_bytes(validated)
    target.write_bytes(non_canonical)
    with pytest.raises(GvFs0PresentationError, match="CURRENT_DECISION_INVALID"):
        load_current_certified_decision(target)


def test_dashboard_default_path_is_single_current_not_dual_bundle() -> None:
    dashboard_path = ROOT / "dashboard.py"
    source = dashboard_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(dashboard_path))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_render_portfolio_allocation_page"
    )
    body = ast.unparse(function)
    assert "render_gv_fs0_current_decision(st)" in body
    assert "render_gv_fs0_certified_bundle" not in body
    assert "Certified decision unavailable" in body
    assert "GvFs0PresentationError" in body
    assert "HOLD_FOR_EVIDENCE" in body or "HOLD_FOR_EVIDENCE" in source
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "views.gv_fs0_portfolio_adapter":
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    assert "render_gv_fs0_current_decision" in imports
    assert "GvFs0PresentationError" in imports
    assert "render_gv_fs0_certified_bundle" not in imports


def test_tracked_current_decision_artifact_is_mandatory_e0a_identity() -> None:
    """Tracked default product authority must exist and match fixed hashes (no skip)."""

    path = DEFAULT_CURRENT_DECISION_TARGET
    assert path.is_file(), "tracked current-decision artifact is mandatory"
    raw = path.read_bytes()
    assert len(raw) == EXPECTED_CURRENT_BYTE_LENGTH
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_CURRENT_FILE_SHA256

    research = build_e0a_research_decision(root=ROOT)
    assert research["research_decision_hash"] == EXPECTED_RESEARCH_DECISION_HASH
    assert research["rationale_ref"] == EXPECTED_RATIONALE_REF

    component = load_current_certified_decision(path)
    assert component["decision"]["decision_id"] == E0A_DECISION_ID
    assert component["decision"]["action"] == "NO_POSITION"
    assert component["decision"]["rationale_ref"] == EXPECTED_RATIONALE_REF
    assert component["certified_decision_result_hash"] == EXPECTED_CERTIFIED_RESULT_HASH
    assert component["certification"]["certification_status"] == "CERTIFIED"

    # Double publish determinism vs tracked bytes.
    rebuilt = build_e0a_certified_result(root=ROOT)
    from core.gv_fs0_current_decision import certified_decision_result_bytes

    first = certified_decision_result_bytes(rebuilt)
    second = certified_decision_result_bytes(build_e0a_certified_result(root=ROOT))
    assert first == second == raw


def test_publish_e0a_twice_matches_tracked_bytes(tmp_path: Path) -> None:
    target, lock = _current_paths(tmp_path)
    first = publish_e0a_current_decision(target=target, lock_path=lock, root=ROOT)
    second = publish_e0a_current_decision(target=target, lock_path=lock, root=ROOT)
    assert first.status == "REPLACED"
    assert second.status == "IDEMPOTENT"
    assert first.certified_decision_result_hash == EXPECTED_CERTIFIED_RESULT_HASH
    assert target.read_bytes() == DEFAULT_CURRENT_DECISION_TARGET.read_bytes()
    assert hashlib.sha256(target.read_bytes()).hexdigest() == EXPECTED_CURRENT_FILE_SHA256
