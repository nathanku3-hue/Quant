"""GV-E0A operable cutover: custody → research HOLD_FOR_EVIDENCE → paper NO_POSITION.

One active certified decision path for the default product UI. F1C dual-role
bundle remains an evidence substrate only. This module performs no provider
access, real-price lookup, broker paths, or Streamlit rendering.

Authority rules (post code-quality A/A/A/A):
- Production publication always re-verifies exact E0 custody bytes from disk.
- A canonical, hash-addressed research-decision artifact binds subject, module,
  research action, claim boundary, and custody hashes.
- DecisionEnvelope.rationale_ref is exactly ``E0A:RD:<research_decision_hash>``.
- Callers cannot inject custody hashes or a pre-built certified result.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any

from core.gv_fs0_book import (
    DecisionEnvelope,
    OpenBookBuild,
    _build_book,
    _build_decision,
    build_no_position_source_fixture,
)
from core.gv_fs0_canonical import domain_hash
from core.gv_fs0_certify import (
    build_certified_result_from_book,
    run_isolated_verifier,
)
from core.gv_fs0_publish import (
    CurrentDecisionPublicationResult,
    DEFAULT_CURRENT_DECISION_LOCK,
    DEFAULT_CURRENT_DECISION_TARGET,
    publish_current_decision,
)

VerifierRunner = Callable[[Mapping[str, Any]], dict[str, Any]]

ROOT = Path(__file__).resolve().parents[1]
E0_CUSTODY_DIR = ROOT / "docs" / "architecture" / "godview_e0"

E0A_DECISION_ID = "DECISION_E0A_HOLD_FOR_EVIDENCE_1"
E0A_RESEARCH_ACTION = "HOLD_FOR_EVIDENCE"
E0A_PORTFOLIO_ACTION = "NO_POSITION"
E0A_SUBJECT = "MU"
E0A_MODULE = "G_supply"
RESEARCH_DECISION_DOMAIN = "GV-E0A:RESEARCH_DECISION:V1"
RESEARCH_DECISION_SCHEMA = "gv_e0a_research_decision_v1"
RATIONALE_REF_PREFIX = "E0A:RD:"

CLAIM_BOUNDARY = (
    "No established market mispricing, financial alpha, investability, "
    "tradability, trade recommendation, or portfolio readiness claim. "
    "Research HOLD_FOR_EVIDENCE maps only to paper NO_POSITION."
)

# Exact frozen custody bytes; fail closed on any mismatch.
E0_CUSTODY_SHA256: Mapping[str, str] = MappingProxyType(
    {
        "e0_preregistration.yaml": (
            "0a6dc18a44d7532610a73f90b92477fc7bd36644c1a052d81a48162097176618"
        ),
        "evidence_authority_matrix.csv": (
            "3306adbed26d27732a0a53d3819a09044e418e183ecc58ebebf82c6f9fe0dcb0"
        ),
        "e0_model_spec.md": (
            "28a0ea062777d9364008480266ce933bd6a34348ce0defcac7185398068a38f0"
        ),
        "e0_acceptance_tests.md": (
            "9d9a7f195bd8db2caea82859d6a73d951c862f229fc9d72e5302c58ba7b8d55c"
        ),
    }
)


class GvE0aOperableError(RuntimeError):
    """Fail-closed E0A operable cutover error."""


def _freeze(value: Any) -> Any:
    """Deep-freeze mappings/sequences so nested custody maps are immutable."""

    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def verify_e0_custody(root: Path | None = None) -> Mapping[str, str]:
    """Verify frozen E0 custody files at exact SHA-256; return frozen basename→sha map."""

    base = Path(root) if root is not None else ROOT
    custody_dir = base / "docs" / "architecture" / "godview_e0"
    verified: dict[str, str] = {}
    for name, expected in E0_CUSTODY_SHA256.items():
        path = custody_dir / name
        if not path.is_file():
            raise GvE0aOperableError(f"E0_CUSTODY_MISSING:{name}")
        digest = sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            raise GvE0aOperableError(f"E0_CUSTODY_HASH_MISMATCH:{name}")
        verified[name] = digest
    # Deterministic key order for operators and hash preimages.
    ordered = {name: verified[name] for name in sorted(verified)}
    return MappingProxyType(ordered)


def _research_decision_preimage(custody_hashes: Mapping[str, str]) -> dict[str, Any]:
    """Authoritative fields hashed into research_decision_hash (no circular ref)."""

    ordered_custody = {name: custody_hashes[name] for name in sorted(custody_hashes)}
    if set(ordered_custody) != set(E0_CUSTODY_SHA256):
        raise GvE0aOperableError("E0_CUSTODY_SET_INVALID")
    for name, expected in E0_CUSTODY_SHA256.items():
        if ordered_custody[name] != expected:
            raise GvE0aOperableError(f"E0_CUSTODY_HASH_MISMATCH:{name}")
    return {
        "schema_version": RESEARCH_DECISION_SCHEMA,
        "research_action": E0A_RESEARCH_ACTION,
        "portfolio_action": E0A_PORTFOLIO_ACTION,
        "subject": E0A_SUBJECT,
        "module": E0A_MODULE,
        "decision_id": E0A_DECISION_ID,
        "custody_hashes": ordered_custody,
        "alpha_claim": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def build_e0a_research_decision(*, root: Path | None = None) -> Mapping[str, Any]:
    """Canonical hash-addressed research decision bound to verified custody bytes.

    Always re-reads and re-verifies exact custody files. Callers cannot supply
    custody hashes. Nested structures are deep-frozen.
    """

    custody = verify_e0_custody(root)
    preimage = _research_decision_preimage(custody)
    research_decision_hash = domain_hash(RESEARCH_DECISION_DOMAIN, preimage)
    rationale_ref = f"{RATIONALE_REF_PREFIX}{research_decision_hash}"
    if len(rationale_ref) > 128:
        raise GvE0aOperableError("E0A_RATIONALE_REF_TOO_LONG")
    payload = {
        **preimage,
        "research_decision_hash": research_decision_hash,
        "rationale_ref": rationale_ref,
    }
    return _freeze(payload)


def e0a_rationale_ref(*, root: Path | None = None) -> str:
    """Return the DecisionEnvelope.rationale_ref that binds the research decision."""

    return str(build_e0a_research_decision(root=root)["rationale_ref"])


def build_e0a_decision(
    fixture_hash: str,
    fixture_id: str,
    *,
    rationale_ref: str,
) -> DecisionEnvelope:
    """Portfolio DecisionEnvelope for E0A: NO_POSITION economics, bound rationale."""

    if not rationale_ref.startswith(RATIONALE_REF_PREFIX):
        raise GvE0aOperableError("E0A_RATIONALE_REF_PREFIX_INVALID")
    return _build_decision(
        fixture_hash=fixture_hash,
        fixture_id=fixture_id,
        decision_id=E0A_DECISION_ID,
        action=E0A_PORTFOLIO_ACTION,
        requested_quantity=None,
        rationale_ref=rationale_ref,
    )


def build_e0a_book(*, root: Path | None = None) -> OpenBookBuild:
    """NO_POSITION fixture economics with DecisionEnvelope bound to E0 research hash."""

    research = build_e0a_research_decision(root=root)
    rationale_ref = str(research["rationale_ref"])

    def decision_builder(fixture_hash: str, fixture_id: str) -> DecisionEnvelope:
        return build_e0a_decision(
            fixture_hash,
            fixture_id,
            rationale_ref=rationale_ref,
        )

    return _build_book(
        fixture=build_no_position_source_fixture(),
        decision_builder=decision_builder,
    )


def _assert_certified_binds_research(
    certified: Mapping[str, Any],
    research: Mapping[str, Any],
) -> None:
    decision = certified.get("decision")
    if not isinstance(decision, Mapping):
        raise GvE0aOperableError("E0A_DECISION_REQUIRED")
    if decision.get("decision_id") != E0A_DECISION_ID:
        raise GvE0aOperableError("E0A_DECISION_ID_REQUIRED")
    if decision.get("action") != E0A_PORTFOLIO_ACTION:
        raise GvE0aOperableError("E0A_PORTFOLIO_ACTION_REQUIRED")
    expected_rationale = str(research["rationale_ref"])
    if decision.get("rationale_ref") != expected_rationale:
        raise GvE0aOperableError("E0A_RATIONALE_BINDING_INVALID")
    expected_hash = str(research["research_decision_hash"])
    if expected_rationale != f"{RATIONALE_REF_PREFIX}{expected_hash}":
        raise GvE0aOperableError("E0A_RESEARCH_HASH_BINDING_INVALID")
    if certified.get("certification", {}).get("certification_status") != "CERTIFIED":
        raise GvE0aOperableError("E0A_CERTIFIED_STATUS_REQUIRED")
    if certified.get("role") != E0A_PORTFOLIO_ACTION:
        raise GvE0aOperableError("E0A_ROLE_REQUIRED")


def build_e0a_certified_result(
    verifier_runner: VerifierRunner = run_isolated_verifier,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Always re-verify custody, bind research hash, then certify the paper decision."""

    research = build_e0a_research_decision(root=root)
    certified = build_certified_result_from_book(
        build_e0a_book(root=root),
        verifier_runner,
    )
    _assert_certified_binds_research(certified, research)
    return certified


def publish_e0a_current_decision(
    *,
    target: Path = DEFAULT_CURRENT_DECISION_TARGET,
    lock_path: Path = DEFAULT_CURRENT_DECISION_LOCK,
    verifier_runner: VerifierRunner = run_isolated_verifier,
    root: Path | None = None,
) -> CurrentDecisionPublicationResult:
    """Always verify custody bytes, build bound research decision, certify, publish.

    No caller-supplied certified result or custody hashes are accepted. Production
    publication cannot bypass the custody gate.
    """

    research = build_e0a_research_decision(root=root)
    certified = build_e0a_certified_result(verifier_runner, root=root)
    _assert_certified_binds_research(certified, research)
    return publish_current_decision(certified, target=target, lock_path=lock_path)


__all__ = [
    "CLAIM_BOUNDARY",
    "E0A_DECISION_ID",
    "E0A_MODULE",
    "E0A_PORTFOLIO_ACTION",
    "E0A_RESEARCH_ACTION",
    "E0A_SUBJECT",
    "E0_CUSTODY_SHA256",
    "RATIONALE_REF_PREFIX",
    "RESEARCH_DECISION_DOMAIN",
    "RESEARCH_DECISION_SCHEMA",
    "GvE0aOperableError",
    "build_e0a_book",
    "build_e0a_certified_result",
    "build_e0a_decision",
    "build_e0a_research_decision",
    "e0a_rationale_ref",
    "publish_e0a_current_decision",
    "verify_e0_custody",
]
